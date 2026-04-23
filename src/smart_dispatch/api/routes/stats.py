"""GET /stats — live dashboard summary."""

from fastapi import APIRouter, Depends

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import StatsResponse
from smart_dispatch.data.resource_db import ResourceStatus

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/", response_model=StatsResponse)
async def get_stats(state: AppState = Depends(get_state)) -> StatsResponse:
    all_incidents = await state.db.list_incidents(limit=500)
    active = [i for i in all_incidents if i.status == "active"]
    resolved = [i for i in all_incidents if i.status == "resolved"]

    all_resources = await state.db.list_resources()
    available = [r for r in all_resources if r.status == ResourceStatus.AVAILABLE.value]
    dispatched = [r for r in all_resources if r.status == ResourceStatus.DISPATCHED.value]

    return StatsResponse(
        incidents_total=len(all_incidents),
        incidents_active=len(active),
        incidents_resolved=len(resolved),
        resources_total=len(all_resources),
        resources_available=len(available),
        resources_dispatched=len(dispatched),
        simulation=state.simulation.stats() if state.simulation else {},
        events_buffered=len(state.event_bus.history(limit=500)),
    )
