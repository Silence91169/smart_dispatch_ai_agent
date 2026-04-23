"""GET /decisions — in-memory dispatch decision log."""

from datetime import datetime

from fastapi import APIRouter, Depends

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import DecisionSummary

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("/", response_model=list[DecisionSummary])
async def list_decisions(
    state: AppState = Depends(get_state),
) -> list[DecisionSummary]:
    results = []
    for d in state.dispatch_decisions:
        # d is already a dict from model_dump(mode="json") captured by event bus.
        results.append(
            DecisionSummary(
                incident_id=d["incident_id"],
                assignments=d.get("assignments", []),
                unfulfilled_resources=[
                    r if isinstance(r, str) else r.get("value", str(r))
                    for r in d.get("unfulfilled_resources", [])
                ],
                decided_at=datetime.utcnow(),
            )
        )
    return results
