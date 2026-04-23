"""DispatchAgent — priority queue, vehicle selection, re-routing, LLM reasoning."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from smart_dispatch.agents.base import BaseAgent
from smart_dispatch.agents.triage.schemas import TriageResult
from smart_dispatch.core.llm.base import LLMProvider
from smart_dispatch.core.llm.factory import get_default_provider
from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.data.resource_db import (
    DispatchLog,
    Incident,
    ResourceDB,
    ResourceStatus,
)
from smart_dispatch.data.schemas import ResourceType, Severity

from .priority_queue import IncidentPriorityQueue
from .reasoning import DispatchReasoner
from .rerouter import Rerouter
from .router import VehicleCandidate, VehicleRouter
from .schemas import (
    DispatchDecision,
    DispatchStatus,
    ReassignmentEvent,
    ResourceAssignment,
)


class DispatchAgent(BaseAgent):
    """Consumes TriageResults, manages a priority queue, dispatches vehicles,
    handles re-routing, and generates LLM reasoning for every decision."""

    DISPATCH_TICK_SEC = 2.0
    UNFULFILLED_RETRY_SEC = 10.0

    def __init__(
        self,
        db: ResourceDB,
        city_graph: Optional[CityGraph] = None,
        llm: Optional[LLMProvider] = None,
        enable_rerouting: bool = True,
        enable_llm_reasoning: bool = True,
    ) -> None:
        super().__init__(name="dispatch")
        self.db = db
        self.city_graph = city_graph or CityGraph()
        self.llm = llm or get_default_provider()
        self.queue = IncidentPriorityQueue()
        self.router = VehicleRouter(self.city_graph, self.db)
        self.rerouter = Rerouter(self.db)
        self.reasoner = DispatchReasoner(self.llm)
        self.enable_rerouting = enable_rerouting
        self.enable_llm_reasoning = enable_llm_reasoning

        self._decisions: list[DispatchDecision] = []
        self._reassignment_events: list[ReassignmentEvent] = []

        # severity + full triage cache for re-queue reconstruction
        self._incident_severity: dict[str, Severity] = {}
        self._triage_cache: dict[str, TriageResult] = {}

        self._loop_task: Optional[asyncio.Task] = None
        self._running = False

    # -------- Lifecycle --------

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._dispatch_loop())
        self.logger.info("DispatchAgent started.")

    async def stop(self) -> None:
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        self.logger.info("DispatchAgent stopped.")

    # -------- Main intake --------

    async def process(self, triage: TriageResult) -> Optional[DispatchDecision]:
        """Intake a TriageResult. Duplicates are counted, not re-dispatched.
        Returns the dispatch decision if made immediately, else None."""
        self._call_count += 1

        if triage.is_duplicate:
            await self.db.increment_duplicate_count(triage.incident_id)
            self.logger.info(
                f"Duplicate call {triage.call_id} for incident {triage.incident_id} — counted."
            )
            return None

        if triage.location_node_id is None:
            self.logger.warning(
                f"Incident {triage.incident_id} has no resolved location; skipping dispatch."
            )
            return None

        existing = await self.db.get_incident(triage.incident_id)
        if existing is None:
            now = datetime.now(timezone.utc)
            incident = Incident(
                id=triage.incident_id,
                incident_type=triage.incident_type.value,
                severity=triage.severity.value,
                location_node_id=triage.location_node_id,
                location_raw=triage.location_raw,
                status="pending",
                duplicate_call_count=1,
                created_at=now,
                updated_at=now,
            )
            await self.db.create_incident(incident)

        self._incident_severity[triage.incident_id] = triage.severity
        self._triage_cache[triage.incident_id] = triage

        await self.queue.push(triage)
        self.logger.info(
            f"Enqueued {triage.incident_id} | {triage.severity.value} "
            f"{triage.incident_type.value} @ {triage.location_node_id} "
            f"| queue_size={await self.queue.size()}"
        )

        return await self._try_dispatch_next()

    # -------- Background loop --------

    async def _dispatch_loop(self) -> None:
        while self._running:
            try:
                await self._try_dispatch_next()
            except Exception as e:
                self.logger.exception(f"Dispatch loop error: {e}")
            await asyncio.sleep(self.DISPATCH_TICK_SEC)

    # -------- Core dispatch logic --------

    async def _try_dispatch_next(self) -> Optional[DispatchDecision]:
        triage = await self.queue.pop()
        if triage is None:
            return None
        decision = await self._dispatch_incident(triage)
        self._decisions.append(decision)
        return decision

    async def _dispatch_incident(self, triage: TriageResult) -> DispatchDecision:
        if not triage.resources_needed:
            # Re-queued bumped incident with no remaining resource requests — nothing to do.
            return DispatchDecision(
                decision_id=f"DEC_{uuid4().hex[:8]}",
                incident_id=triage.incident_id,
                severity=triage.severity,
                incident_type=triage.incident_type,
                location_node_id=triage.location_node_id or "UNKNOWN",
                status=DispatchStatus.DISPATCHED,
                decision_reasoning="(bumped incident re-queued; no additional resources needed)",
                fallback_reasoning="",
            )

        start = time.perf_counter()
        decision_id = f"DEC_{uuid4().hex[:8]}"

        assignments: list[ResourceAssignment] = []
        unfulfilled: list[ResourceType] = []
        alternatives: list[dict] = []

        for resource_type in triage.resources_needed:
            assignment, alt_log = await self._assign_one_resource(resource_type, triage)
            if assignment:
                assignments.append(assignment)
            else:
                unfulfilled.append(resource_type)
            alternatives.extend(alt_log)

        if not assignments and unfulfilled:
            status = DispatchStatus.UNFULFILLABLE
            await self._requeue_after_delay(triage, self.UNFULFILLED_RETRY_SEC)
        elif assignments and unfulfilled:
            status = DispatchStatus.PARTIALLY_DISPATCHED
            await self.db.update_incident_status(triage.incident_id, "partially_dispatched")
        else:
            status = DispatchStatus.DISPATCHED
            await self.db.update_incident_status(triage.incident_id, "dispatched")

        decision = DispatchDecision(
            decision_id=decision_id,
            incident_id=triage.incident_id,
            severity=triage.severity,
            incident_type=triage.incident_type,
            location_node_id=triage.location_node_id or "UNKNOWN",
            status=status,
            assignments=assignments,
            unfulfilled_resources=unfulfilled,
            considered_alternatives=alternatives,
            processing_time_ms=(time.perf_counter() - start) * 1000,
        )

        if self.enable_llm_reasoning and (assignments or unfulfilled):
            decision.decision_reasoning = await self.reasoner.explain(decision, triage.summary)
        else:
            decision.decision_reasoning = self.reasoner._deterministic_fallback(decision)
        decision.fallback_reasoning = self.reasoner._deterministic_fallback(decision)

        self.logger.info(
            f"Decision {decision_id} | {decision.status.value} | "
            f"assigned={len(assignments)} unfulfilled={len(unfulfilled)} | "
            f"{decision.processing_time_ms:.0f}ms"
        )
        return decision

    async def _assign_one_resource(
        self,
        resource_type: ResourceType,
        incident: TriageResult,
    ) -> tuple[Optional[ResourceAssignment], list[dict]]:
        alt_log: list[dict] = []

        best_available = await self.router.find_best_available(
            resource_type=resource_type,
            destination_node=incident.location_node_id,
        )

        if best_available:
            alt_log.append({
                "resource_id": best_available.resource.id,
                "call_sign": best_available.resource.call_sign,
                "eta_sec": best_available.travel_time_sec,
                "status": "available",
                "chosen": True,
            })
            try:
                assignment = await self._commit_dispatch(best_available, incident, reassigned_from=None)
                return assignment, alt_log
            except Exception as e:
                self.logger.warning(f"Dispatch commit failed for {best_available.resource.id}: {e}")
                return None, alt_log

        if not self.enable_rerouting:
            return None, alt_log

        all_candidates = await self.router.find_all_candidates(
            resource_type=resource_type,
            destination_node=incident.location_node_id,
            include_busy=True,
        )

        for cand in all_candidates:
            if cand.is_available:
                continue

            current_sev = None
            if cand.currently_assigned_to:
                current_sev = self._incident_severity.get(cand.currently_assigned_to)

            should_reassign, reason = self.rerouter.evaluate_reassignment(
                candidate=cand,
                new_incident_severity=incident.severity,
                current_incident_severity=current_sev,
                new_incident_eta_sec=cand.travel_time_sec,
            )

            alt_log.append({
                "resource_id": cand.resource.id,
                "call_sign": cand.resource.call_sign,
                "eta_sec": cand.travel_time_sec,
                "status": cand.resource.status.value,
                "current_incident": cand.currently_assigned_to,
                "reassign_considered": True,
                "reassign_decision": should_reassign,
                "reassign_reason": reason,
            })

            if should_reassign:
                reassigned_from = cand.currently_assigned_to
                if reassigned_from:
                    self._reassignment_events.append(ReassignmentEvent(
                        resource_id=cand.resource.id,
                        from_incident_id=reassigned_from,
                        to_incident_id=incident.incident_id,
                        reason=reason,
                    ))
                    prior_triage = self._triage_cache.get(reassigned_from)
                    if prior_triage:
                        bumped = TriageResult(
                            **{
                                **prior_triage.model_dump(),
                                "call_id": f"requeue_{uuid4().hex[:6]}",
                                "resources_needed": [],
                                "summary": "(re-queued after reassignment)",
                                "reasoning": "",
                                "is_duplicate": False,
                            }
                        )
                        await self.queue.push(bumped)

                try:
                    assignment = await self._commit_dispatch(cand, incident, reassigned_from=reassigned_from)
                    return assignment, alt_log
                except Exception as e:
                    self.logger.warning(f"Reassignment commit failed for {cand.resource.id}: {e}")

        return None, alt_log

    async def _commit_dispatch(
        self,
        candidate: VehicleCandidate,
        incident: TriageResult,
        reassigned_from: Optional[str],
    ) -> ResourceAssignment:
        now = datetime.now(timezone.utc)
        eta = now + timedelta(seconds=candidate.travel_time_sec)

        if candidate.is_available:
            await self.db.dispatch_resource(
                resource_id=candidate.resource.id,
                incident_id=incident.incident_id,
                destination_node=incident.location_node_id,
                eta_sec=candidate.travel_time_sec,
            )
        else:
            await self.db.update_resource_status(
                resource_id=candidate.resource.id,
                new_status=ResourceStatus.EN_ROUTE,
                current_node=incident.location_node_id,
                new_incident_id=incident.incident_id,
                eta_sec=candidate.travel_time_sec,
            )

        log = DispatchLog(
            id=uuid4().hex,
            incident_id=incident.incident_id,
            resource_id=candidate.resource.id,
            dispatched_at=now,
            travel_time_sec=candidate.travel_time_sec,
            reassigned=reassigned_from is not None,
        )
        await self.db.log_dispatch(log)

        return ResourceAssignment(
            resource_id=candidate.resource.id,
            resource_type=ResourceType(candidate.resource.resource_type),
            call_sign=candidate.resource.call_sign,
            from_node_id=candidate.resource.current_node_id,
            to_node_id=incident.location_node_id,
            path=candidate.path,
            travel_time_sec=candidate.travel_time_sec,
            dispatched_at=now,
            estimated_arrival=eta,
            was_reassigned_from=reassigned_from,
        )

    async def _requeue_after_delay(self, triage: TriageResult, delay_sec: float) -> None:
        async def _delayed() -> None:
            await asyncio.sleep(delay_sec)
            await self.queue.push(triage)
        asyncio.create_task(_delayed())

    # -------- Stats / inspection --------

    def stats(self) -> dict:
        total = len(self._decisions)
        by_status: dict[str, int] = {}
        for d in self._decisions:
            by_status[d.status.value] = by_status.get(d.status.value, 0) + 1
        reassigns = sum(
            1 for d in self._decisions for a in d.assignments if a.was_reassigned_from
        )
        avg_ms = sum(d.processing_time_ms for d in self._decisions) / total if total else 0
        return {
            "total_decisions": total,
            "by_status": by_status,
            "reassignments": reassigns,
            "avg_processing_ms": round(avg_ms, 1),
            "reasoning_enabled": self.enable_llm_reasoning,
            "rerouting_enabled": self.enable_rerouting,
        }

    def recent_decisions(self, n: int = 10) -> list[DispatchDecision]:
        return self._decisions[-n:]

    def reassignment_events(self) -> list[ReassignmentEvent]:
        return list(self._reassignment_events)
