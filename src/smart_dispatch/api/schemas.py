"""Request / response Pydantic models for the FastAPI layer."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity


# -------- Simulation --------

class StartScenarioRequest(BaseModel):
    scenario_name: str
    speed_multiplier: float = 1.0


class StartLiveRequest(BaseModel):
    calls_per_minute: float = 20.0
    seed: Optional[int] = None
    max_calls: Optional[int] = None
    duplicate_ratio: float = 0.3


class SimulationStatusResponse(BaseModel):
    is_running: bool
    stats: dict


# -------- Incidents --------

class IncidentSummary(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    location_node_id: Optional[str]
    location_raw: str
    status: str
    duplicate_call_count: int
    created_at: datetime
    updated_at: datetime


# -------- Resources --------

class ResourceSummary(BaseModel):
    id: str
    call_sign: str
    resource_type: str
    status: str
    current_node_id: str
    current_incident_id: Optional[str]


# -------- Calls --------

class SingleCallRequest(BaseModel):
    transcript: str
    call_id: Optional[str] = None


class CallResultResponse(BaseModel):
    call_id: str
    triage: Optional[dict] = None
    dispatch: Optional[dict] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
    latency_ms: Optional[float] = None


# -------- Decisions --------

class DecisionSummary(BaseModel):
    incident_id: str
    assignments: list[dict]
    unfulfilled_resources: list[str]
    decided_at: datetime


# -------- Graph --------

class GraphStateResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]
    resources: list[dict]


# -------- Stats --------

class StatsResponse(BaseModel):
    incidents_total: int
    incidents_active: int
    incidents_resolved: int
    resources_total: int
    resources_available: int
    resources_dispatched: int
    simulation: dict
    events_buffered: int


# -------- Events --------

class EventMessage(BaseModel):
    type: str
    timestamp: str
    payload: dict
    incident_id: Optional[str] = None
    call_id: Optional[str] = None
    resource_id: Optional[str] = None
