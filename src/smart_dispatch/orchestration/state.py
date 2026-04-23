"""LangGraph state schema for the dispatch pipeline."""

from typing import Optional, TypedDict

from smart_dispatch.agents.dispatch.schemas import DispatchDecision
from smart_dispatch.agents.triage.schemas import TriageResult
from smart_dispatch.data.schemas import MockCall


class DispatchGraphState(TypedDict, total=False):
    """State flowing through the LangGraph pipeline for a single 112 call."""

    # Input
    call: MockCall

    # Filled by triage node
    triage_result: Optional[TriageResult]
    triage_error: Optional[str]

    # Filled by dispatch node
    dispatch_decision: Optional[DispatchDecision]
    dispatch_skipped: bool
    dispatch_skip_reason: Optional[str]

    # Timing
    started_at: Optional[float]
    total_latency_ms: Optional[float]
