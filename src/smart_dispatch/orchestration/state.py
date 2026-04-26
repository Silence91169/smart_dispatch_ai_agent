"""LangGraph state schema for the dispatch pipeline."""

from typing import Optional, TypedDict

from smart_dispatch.agents.dispatch.schemas import DispatchDecision
from smart_dispatch.agents.triage.schemas import TriageResult
from smart_dispatch.data.schemas import MockCall


class DispatchGraphState(TypedDict, total=False):
    """State flowing through the LangGraph pipeline for a single 112 call.

    triage_results holds one TriageResult per distinct location extracted from
    the transcript. Single-location calls produce a list of one element.
    dispatch_decisions mirrors that list — one DispatchDecision per TriageResult.
    """

    # Input
    call: MockCall

    # Filled by triage node — one entry per resolved location
    triage_results: list[TriageResult]
    triage_error: Optional[str]

    # Filled by dispatch node — parallel list to triage_results
    dispatch_decisions: list[Optional[DispatchDecision]]
    dispatch_skipped: bool
    dispatch_skip_reason: Optional[str]

    # Timing
    started_at: Optional[float]
    total_latency_ms: Optional[float]
