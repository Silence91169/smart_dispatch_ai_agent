"""LangGraph dispatch pipeline — Triage → Dispatch with event publishing."""

import logging
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph

from smart_dispatch.agents.dispatch.agent import DispatchAgent
from smart_dispatch.agents.triage.agent import TriageAgent

from .event_bus import Event, EventBus, EventType
from .state import DispatchGraphState

logger = logging.getLogger("orchestration.graph")


class DispatchOrchestrator:
    """Wraps a compiled LangGraph over TriageAgent and DispatchAgent.

    Publishes events at each stage so the WebSocket layer can broadcast them.
    """

    def __init__(
        self,
        triage_agent: TriageAgent,
        dispatch_agent: DispatchAgent,
        event_bus: EventBus,
    ) -> None:
        self.triage_agent = triage_agent
        self.dispatch_agent = dispatch_agent
        self.event_bus = event_bus
        self._graph = self._build_graph()

    # -------- Graph construction --------

    def _build_graph(self):
        g: StateGraph = StateGraph(DispatchGraphState)
        g.add_node("triage", self._triage_node)
        g.add_node("dispatch", self._dispatch_node)
        g.add_node("skip_dispatch", self._skip_dispatch_node)

        g.add_edge(START, "triage")
        g.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {"dispatch": "dispatch", "skip": "skip_dispatch"},
        )
        g.add_edge("dispatch", END)
        g.add_edge("skip_dispatch", END)
        return g.compile()

    # -------- Nodes --------

    async def _triage_node(self, state: DispatchGraphState) -> DispatchGraphState:
        call = state["call"]
        await self.event_bus.publish(Event(
            type=EventType.TRIAGE_STARTED,
            call_id=call.call_id,
            payload={"transcript_preview": call.transcript[:120]},
        ))
        try:
            # Returns list[TriageResult] — one per distinct location in the transcript.
            results = await self.triage_agent.process(call)
        except Exception as exc:
            logger.exception("Triage failed for %s", call.call_id)
            await self.event_bus.publish(Event(
                type=EventType.TRIAGE_FAILED,
                call_id=call.call_id,
                payload={"error": str(exc)},
            ))
            return {**state, "triage_error": str(exc), "triage_results": []}

        # Publish one event per location result
        for result in results:
            await self.event_bus.publish(Event(
                type=EventType.TRIAGE_COMPLETED,
                call_id=call.call_id,
                incident_id=result.incident_id,
                payload={
                    "incident_type": result.incident_type.value,
                    "severity": result.severity.value,
                    "location_node_id": result.location_node_id,
                    "location_index": result.location_index,
                    "is_duplicate": result.is_duplicate,
                    "duplicate_of_call_id": result.duplicate_of_call_id,
                    "summary": result.summary,
                    "processing_time_ms": result.processing_time_ms,
                },
            ))

            if result.is_duplicate:
                await self.event_bus.publish(Event(
                    type=EventType.DUPLICATE_DETECTED,
                    call_id=call.call_id,
                    incident_id=result.incident_id,
                    payload={
                        "duplicate_of_call_id": result.duplicate_of_call_id,
                        "similarity": result.dedup_similarity,
                    },
                ))
            else:
                await self.event_bus.publish(Event(
                    type=EventType.INCIDENT_CREATED,
                    incident_id=result.incident_id,
                    payload=result.model_dump(mode="json"),
                ))

        return {**state, "triage_results": results}

    async def _dispatch_node(self, state: DispatchGraphState) -> DispatchGraphState:
        triage_results = state.get("triage_results", [])
        decisions: list = []

        for triage_result in triage_results:
            # Skip duplicates and unresolved locations — dispatch_agent handles
            # duplicate counting internally; unresolved locations have no target node.
            if triage_result.is_duplicate or triage_result.location_node_id is None:
                decisions.append(None)
                continue

            decision = await self.dispatch_agent.process(triage_result)
            decisions.append(decision)

            if decision is None:
                continue

            await self.event_bus.publish(Event(
                type=EventType.DISPATCH_DECIDED,
                incident_id=decision.incident_id,
                payload=decision.model_dump(mode="json"),
            ))

            for assignment in decision.assignments:
                await self.event_bus.publish(Event(
                    type=EventType.RESOURCE_DISPATCHED,
                    incident_id=decision.incident_id,
                    resource_id=assignment.resource_id,
                    payload={
                        "call_sign": assignment.call_sign,
                        "from_node_id": assignment.from_node_id,
                        "to_node_id": assignment.to_node_id,
                        "path": assignment.path,
                        "travel_time_sec": assignment.travel_time_sec,
                        "was_reassigned_from": assignment.was_reassigned_from,
                    },
                ))
                if assignment.was_reassigned_from:
                    await self.event_bus.publish(Event(
                        type=EventType.RESOURCE_REASSIGNED,
                        incident_id=decision.incident_id,
                        resource_id=assignment.resource_id,
                        payload={"from_incident_id": assignment.was_reassigned_from},
                    ))

            if decision.unfulfilled_resources:
                await self.event_bus.publish(Event(
                    type=EventType.UNFULFILLED_INCIDENT,
                    incident_id=decision.incident_id,
                    payload={"unfulfilled": [r.value for r in decision.unfulfilled_resources]},
                ))

        return {**state, "dispatch_decisions": decisions}

    async def _skip_dispatch_node(self, state: DispatchGraphState) -> DispatchGraphState:
        reason = ""
        if state.get("triage_error"):
            reason = f"triage_error: {state['triage_error']}"
        else:
            # All results were duplicates or had unresolved locations.
            # Forward duplicates to dispatch_agent so it increments the DB counter.
            for result in state.get("triage_results", []):
                if result.is_duplicate:
                    await self.dispatch_agent.process(result)
                    reason = reason or "duplicate"
                elif result.location_node_id is None:
                    reason = reason or "unresolved_location"
        return {**state, "dispatch_skipped": True, "dispatch_skip_reason": reason, "dispatch_decisions": []}

    # -------- Routing --------

    def _route_after_triage(self, state: DispatchGraphState) -> Literal["dispatch", "skip"]:
        if state.get("triage_error"):
            return "skip"
        results = state.get("triage_results")
        if not results:
            return "skip"
        # Route to dispatch if at least one result is a new, resolved incident.
        for result in results:
            if not result.is_duplicate and result.location_node_id is not None:
                return "dispatch"
        return "skip"

    # -------- Public API --------

    async def run(self, call) -> DispatchGraphState:
        """Process a single 112 call through the full pipeline."""
        start = time.perf_counter()
        initial_state: DispatchGraphState = {
            "call": call,
            "started_at": start,
            "dispatch_skipped": False,
        }
        final_state = await self._graph.ainvoke(initial_state)
        final_state["total_latency_ms"] = (time.perf_counter() - start) * 1000
        return final_state
