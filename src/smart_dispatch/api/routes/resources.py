"""GET /resources — list and detail endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import ResourceSummary
from smart_dispatch.data.resource_db import ResourceStatus
from smart_dispatch.data.schemas import ResourceType

router = APIRouter(prefix="/resources", tags=["resources"])


def _to_summary(resource) -> ResourceSummary:
    return ResourceSummary(
        id=resource.id,
        call_sign=resource.call_sign,
        resource_type=resource.resource_type,
        status=resource.status,
        current_node_id=resource.current_node_id,
        current_incident_id=resource.current_incident_id,
    )


@router.get("/", response_model=list[ResourceSummary])
async def list_resources(
    status: str | None = Query(None),
    resource_type: str | None = Query(None, alias="type"),
    state: AppState = Depends(get_state),
) -> list[ResourceSummary]:
    status_enum = ResourceStatus(status) if status else None
    type_enum = ResourceType(resource_type) if resource_type else None
    resources = await state.db.list_resources(status=status_enum, resource_type=type_enum)
    return [_to_summary(r) for r in resources]


@router.get("/{resource_id}", response_model=ResourceSummary)
async def get_resource(
    resource_id: str,
    state: AppState = Depends(get_state),
) -> ResourceSummary:
    resource = await state.db.get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _to_summary(resource)
