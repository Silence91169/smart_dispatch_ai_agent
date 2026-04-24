"""Core evaluation harness — runs golden cases through a single TriageAgent."""

import time
from dataclasses import dataclass

from smart_dispatch.data.golden_dataset import load_golden_dataset, GoldenCase
from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.agents.triage.agent import TriageAgent
from smart_dispatch.agents.triage.schemas import TriageResult

from .metrics import aggregate_triage, evaluate_dedup, TriageMetrics, DedupMetrics


@dataclass
class EvalReport:
    triage: TriageMetrics
    dedup: DedupMetrics
    per_case: list[dict]
    total_time_sec: float
    llm_provider: str
    llm_model: str


async def run_evaluation(
    agent: TriageAgent | None = None,
    golden_cases: list[GoldenCase] | None = None,
    limit: int | None = None,
) -> EvalReport:
    t0 = time.perf_counter()

    if golden_cases is None:
        golden_cases = load_golden_dataset()
    if limit:
        golden_cases = golden_cases[:limit]

    if agent is None:
        agent = TriageAgent(city_graph=CityGraph())
        await agent.initialize()

    pairs: list[tuple[GoldenCase, TriageResult]] = []
    per_case_details = []

    # Process chronologically so dedup index sees calls in order
    sorted_cases = sorted(golden_cases, key=lambda c: c.call.timestamp)

    for case in sorted_cases:
        try:
            result = await agent.process(case.call)
            pairs.append((case, result))
            per_case_details.append({
                "call_id": case.call.call_id,
                "transcript": case.call.transcript[:120],
                "expected_type": case.expected.incident_type.value,
                "actual_type": result.incident_type.value,
                "expected_severity": case.expected.severity.value,
                "actual_severity": result.severity.value,
                "is_duplicate_expected": case.expected.is_duplicate_of is not None,
                "is_duplicate_actual": result.is_duplicate,
                "confidence": result.llm_confidence,
                "latency_ms": result.processing_time_ms,
            })
        except Exception as e:
            per_case_details.append({
                "call_id": case.call.call_id,
                "error": str(e),
            })

    triage_metrics = aggregate_triage(pairs)
    dedup_metrics = evaluate_dedup(pairs)

    return EvalReport(
        triage=triage_metrics,
        dedup=dedup_metrics,
        per_case=per_case_details,
        total_time_sec=time.perf_counter() - t0,
        llm_provider=getattr(agent.llm, "provider_name", "unknown"),
        llm_model=getattr(agent.llm, "model", "unknown"),
    )
