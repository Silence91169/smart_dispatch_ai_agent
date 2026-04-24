"""GET/POST /eval/golden — live accuracy check on the 50 golden cases."""

from fastapi import APIRouter, Depends, Query

from smart_dispatch.api.dependencies import AppState, get_state

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/golden")
async def run_golden_eval(
    limit: int | None = Query(default=None, ge=1, le=50),
    state: AppState = Depends(get_state),
):
    """Run the full golden dataset evaluation and return live accuracy metrics.

    Takes 30–90 seconds depending on limit and LLM provider speed.
    Reuses the already-loaded triage agent — no model reload on each request.
    """
    # Import here to keep the evaluation module out of the FastAPI import graph
    # until the endpoint is actually hit.
    from evaluation.evaluator import run_evaluation

    report = await run_evaluation(agent=state.triage_agent, limit=limit)

    return {
        "triage": {
            "total": report.triage.total,
            "type_accuracy": round(report.triage.type_accuracy, 4),
            "severity_accuracy": round(report.triage.severity_accuracy, 4),
            "severity_within_one_accuracy": round(report.triage.severity_tolerance_accuracy, 4),
            "location_accuracy": round(report.triage.location_accuracy, 4),
            "resources_exact_rate": round(report.triage.resources_exact_rate, 4),
            "avg_confidence": round(report.triage.avg_confidence, 4),
        },
        "dedup": {
            "precision": round(report.dedup.precision, 4),
            "recall": round(report.dedup.recall, 4),
            "f1": round(report.dedup.f1, 4),
        },
        "total_time_sec": round(report.total_time_sec, 2),
        "llm": f"{report.llm_provider}:{report.llm_model}",
        "per_case": report.per_case,
    }
