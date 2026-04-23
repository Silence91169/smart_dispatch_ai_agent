"""Core Pydantic models for the 911 call data layer."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class IncidentType(str, Enum):
    FIRE = "FIRE"
    MEDICAL = "MEDICAL"
    ACCIDENT = "ACCIDENT"
    CRIME = "CRIME"
    HAZARD = "HAZARD"
    OTHER = "OTHER"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ResourceType(str, Enum):
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE_CAR = "police_car"
    HAZMAT_UNIT = "hazmat_unit"


class Location(BaseModel):
    """A geographic point. node_id refers to the city graph (built in Phase 3)."""

    node_id: Optional[str] = None
    raw_text: str
    landmark: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class MockCall(BaseModel):
    """A single raw 911 call as it arrives at the system.

    Note: ``event_id`` is ground-truth bookkeeping for evaluation only.
    Agents must never read or act on this field — they should derive
    duplicate detection purely from transcript content.
    """

    call_id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:8]}")
    transcript: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    caller_phone: Optional[str] = None
    event_id: Optional[str] = None

    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat()}}


class ExpectedTriage(BaseModel):
    """Ground-truth answer for a call in the golden dataset."""

    incident_type: IncidentType
    severity: Severity
    resources_needed: list[ResourceType]
    location_keywords: list[str]
    is_duplicate_of: Optional[str] = None


class GoldenCase(BaseModel):
    """A single labeled test case for evaluating the Triage Agent."""

    call: MockCall
    expected: ExpectedTriage
    notes: Optional[str] = None
