"""GET /incidents — list and detail endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import IncidentSummary

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_summary(incident) -> IncidentSummary:
    return IncidentSummary(
        incident_id=incident.id,
        incident_type=incident.incident_type,
        severity=incident.severity,
        location_node_id=incident.location_node_id,
        location_raw=incident.location_raw,
        status=incident.status,
        duplicate_call_count=incident.duplicate_call_count,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


@router.get("/", response_model=list[IncidentSummary])
async def list_incidents(
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    state: AppState = Depends(get_state),
) -> list[IncidentSummary]:
    incidents = await state.db.list_incidents(status=status, limit=limit)
    return [_to_summary(i) for i in incidents]


@router.get("/{incident_id}", response_model=IncidentSummary)
async def get_incident(
    incident_id: str,
    state: AppState = Depends(get_state),
) -> IncidentSummary:
    incident = await state.db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _to_summary(incident)
