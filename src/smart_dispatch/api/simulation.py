"""SimulationRunner — drives a CallStream through the orchestrator as a background task."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.call_stream import CallStream
from smart_dispatch.data.schemas import MockCall
from smart_dispatch.orchestration.event_bus import Event, EventBus, EventType
from smart_dispatch.orchestration.graph import DispatchOrchestrator


class SimulationRunner:
    """Runs a scenario or live stream through the orchestrator as a background asyncio task."""

    def __init__(self, orchestrator: DispatchOrchestrator, event_bus: EventBus) -> None:
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._stats: dict = {
            "started_at": None,
            "calls_processed": 0,
            "incidents_created": 0,
            "duplicates_detected": 0,
            "scenario_name": None,
        }
        self.logger = logging.getLogger("simulation")

    @property
    def is_running(self) -> bool:
        return self._running

    def stats(self) -> dict:
        return dict(self._stats)

    async def start_scenario(
        self,
        scenario_name: str,
        calls: list[MockCall],
        speed_multiplier: float = 1.0,
    ) -> None:
        if self._running:
            raise RuntimeError("Simulation already running — stop it first.")
        self._stats = {
            "started_at": datetime.utcnow().isoformat(),
            "calls_processed": 0,
            "incidents_created": 0,
            "duplicates_detected": 0,
            "scenario_name": scenario_name,
        }
        self._running = True
        await self.event_bus.publish(Event(
            type=EventType.SIMULATION_STARTED,
            payload={"scenario": scenario_name, "total_calls": len(calls)},
        ))
        self._task = asyncio.create_task(self._run_batch(calls, speed_multiplier))

    async def start_live(
        self,
        calls_per_minute: float = 20.0,
        seed: Optional[int] = None,
        max_calls: Optional[int] = None,
        duplicate_ratio: float = 0.3,
    ) -> None:
        if self._running:
            raise RuntimeError("Simulation already running — stop it first.")
        self._stats = {
            "started_at": datetime.utcnow().isoformat(),
            "calls_processed": 0,
            "incidents_created": 0,
            "duplicates_detected": 0,
            "scenario_name": f"live({calls_per_minute}cpm)",
        }
        self._running = True
        await self.event_bus.publish(Event(
            type=EventType.SIMULATION_STARTED,
            payload={"mode": "live", "rate_per_min": calls_per_minute},
        ))
        gen = MockCallGenerator(seed=seed)
        stream = CallStream(
            gen,
            calls_per_minute=calls_per_minute,
            max_calls=max_calls,
            duplicate_ratio=duplicate_ratio,
        )
        self._task = asyncio.create_task(self._run_stream(stream))

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.event_bus.publish(Event(
            type=EventType.SIMULATION_STOPPED,
            payload=self._stats,
        ))

    # -------- Internal runners --------

    async def _run_batch(self, calls: list[MockCall], speed_multiplier: float) -> None:
        try:
            if not calls:
                return
            t0 = calls[0].timestamp
            started = asyncio.get_event_loop().time()
            for call in calls:
                if not self._running:
                    break
                delta = (call.timestamp - t0).total_seconds() / max(speed_multiplier, 0.01)
                target = started + delta
                wait = target - asyncio.get_event_loop().time()
                if wait > 0:
                    await asyncio.sleep(wait)
                await self._process_call(call)
        except asyncio.CancelledError:
            self.logger.info("Simulation batch cancelled.")
            raise
        finally:
            self._running = False

    async def _run_stream(self, stream: CallStream) -> None:
        try:
            async for call in stream:
                if not self._running:
                    break
                await self._process_call(call)
        except asyncio.CancelledError:
            raise
        finally:
            self._running = False

    async def _process_call(self, call: MockCall) -> None:
        await self.event_bus.publish(Event(
            type=EventType.CALL_RECEIVED,
            call_id=call.call_id,
            payload={
                "transcript": call.transcript,
                "timestamp": call.timestamp.isoformat(),
            },
        ))
        try:
            result = await self.orchestrator.run(call)
        except Exception as exc:
            self.logger.exception("Call %s failed in orchestrator", call.call_id)
            await self.event_bus.publish(Event(
                type=EventType.SYSTEM_ERROR,
                call_id=call.call_id,
                payload={"error": str(exc)},
            ))
            return

        self._stats["calls_processed"] += 1
        for triage in result.get("triage_results", []):
            if triage.is_duplicate:
                self._stats["duplicates_detected"] += 1
            else:
                self._stats["incidents_created"] += 1

        if self._stats["calls_processed"] % 5 == 0:
            await self.event_bus.publish(Event(
                type=EventType.SIMULATION_PROGRESS,
                payload=dict(self._stats),
            ))
