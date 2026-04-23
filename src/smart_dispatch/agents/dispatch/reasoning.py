"""LLM-based dispatch decision explainer with deterministic fallback."""

from __future__ import annotations

import logging

from smart_dispatch.core.llm.base import LLMProvider
from smart_dispatch.data.city_fixtures import get_location_by_node_id

from .schemas import DispatchDecision
from .prompts import DISPATCH_REASONING_SYSTEM_PROMPT, REASONING_USER_TEMPLATE


class DispatchReasoner:
    """Generates human-readable reasoning for dispatch decisions."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm
        self.logger = logging.getLogger("dispatch.reasoner")

    async def explain(self, decision: DispatchDecision, incident_summary: str) -> str:
        """Generate reasoning text. Returns deterministic fallback on LLM failure."""
        try:
            prompt = self._build_prompt(decision, incident_summary)
            response = await self.llm.complete(
                prompt=prompt,
                system=DISPATCH_REASONING_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=300,
            )
            return response.content.strip()
        except Exception as e:
            self.logger.warning(f"LLM reasoning failed: {e}; using fallback.")
            return self._deterministic_fallback(decision)

    def _build_prompt(self, decision: DispatchDecision, summary: str) -> str:
        loc = get_location_by_node_id(decision.location_node_id) or {}
        loc_name = loc.get("name", decision.location_node_id)

        if decision.assignments:
            lines = []
            for a in decision.assignments:
                from_loc = get_location_by_node_id(a.from_node_id) or {}
                from_name = from_loc.get("name", a.from_node_id)
                line = (
                    f"  - {a.call_sign} ({a.resource_type.value}) from {from_name} "
                    f"→ ETA {a.travel_time_sec / 60:.1f} min"
                )
                if a.was_reassigned_from:
                    line += f" [REASSIGNED from incident {a.was_reassigned_from}]"
                lines.append(line)
            assignments_block = "\n".join(lines)
        else:
            assignments_block = "  (none)"

        if decision.considered_alternatives:
            alt_lines = [f"  - {alt}" for alt in decision.considered_alternatives[:5]]
            alternatives_block = "\n".join(alt_lines)
        else:
            alternatives_block = "  (none)"

        reassignments = [a for a in decision.assignments if a.was_reassigned_from]
        if reassignments:
            reassignments_block = "\n".join(
                f"  - {a.call_sign} pulled from incident {a.was_reassigned_from}"
                for a in reassignments
            )
        else:
            reassignments_block = "  (none)"

        if decision.unfulfilled_resources:
            unfulfilled_block = ", ".join(r.value for r in decision.unfulfilled_resources)
        else:
            unfulfilled_block = "  (none)"

        return REASONING_USER_TEMPLATE.format(
            incident_type=decision.incident_type.value,
            severity=decision.severity.value,
            location_name=loc_name,
            location_node=decision.location_node_id,
            summary=summary,
            assignments_block=assignments_block,
            alternatives_block=alternatives_block,
            reassignments_block=reassignments_block,
            unfulfilled_block=unfulfilled_block,
        )

    def _deterministic_fallback(self, decision: DispatchDecision) -> str:
        if not decision.assignments:
            return (
                f"No resources available for {decision.severity.value} "
                f"{decision.incident_type.value} at {decision.location_node_id}. "
                f"Incident queued for retry."
            )
        parts = []
        for a in decision.assignments:
            note = " (reassigned)" if a.was_reassigned_from else ""
            parts.append(f"{a.call_sign} dispatched (ETA {a.travel_time_sec / 60:.1f} min){note}")
        result = "; ".join(parts) + f" for {decision.severity.value} {decision.incident_type.value}."
        if decision.unfulfilled_resources:
            result += f" Unfulfilled: {', '.join(r.value for r in decision.unfulfilled_resources)}."
        return result
