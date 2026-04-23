"""Dispatch Agent data models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity

SEVERITY_PRIORITY: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


class DispatchStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    PARTIALLY_DISPATCHED = "partially_dispatched"
    UNFULFILLABLE = "unfulfillable"
    RESOLVED = "resolved"
    REASSIGNED = "reassigned"


class ResourceAssignment(BaseModel):
    resource_id: str
    resource_type: ResourceType
    call_sign: str
    from_node_id: str
    to_node_id: str
    path: list[str]
    travel_time_sec: float
    dispatched_at: datetime
    estimated_arrival: datetime
    was_reassigned_from: Optional[str] = None


class DispatchDecision(BaseModel):
    decision_id: str
    incident_id: str
    severity: Severity
    incident_type: IncidentType
    location_node_id: str
    status: DispatchStatus

    assignments: list[ResourceAssignment] = Field(default_factory=list)
    unfulfilled_resources: list[ResourceType] = Field(default_factory=list)

    decision_reasoning: str = ""
    fallback_reasoning: str = ""
    considered_alternatives: list[dict] = Field(default_factory=list)

    decided_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0


class ReassignmentEvent(BaseModel):
    resource_id: str
    from_incident_id: str
    to_incident_id: str
    reason: str
    reassigned_at: datetime = Field(default_factory=datetime.utcnow)
