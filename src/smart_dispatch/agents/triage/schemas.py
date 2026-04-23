"""Triage Agent output schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity


class LLMTriageExtraction(BaseModel):
    """Raw LLM output — extracted before post-processing."""

    incident_type: IncidentType
    severity: Severity
    resources_needed: list[ResourceType] = Field(min_length=1)
    location_text: str = Field(..., description="Location as mentioned by caller, normalized")
    location_landmark: Optional[str] = Field(
        None, description="Nearby landmark if mentioned"
    )
    summary: str = Field(..., description="One-sentence summary of the incident")
    reasoning: str = Field(..., description="Brief reasoning for severity and resource choices")
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("resources_needed")
    @classmethod
    def dedupe_resources(cls, v: list[ResourceType]) -> list[ResourceType]:
        seen: set = set()
        return [r for r in v if not (r in seen or seen.add(r))]


class TriageResult(BaseModel):
    """Final triage output — LLM extraction + location resolution + dedup."""

    # Core incident data
    incident_id: str
    call_id: str
    incident_type: IncidentType
    severity: Severity
    resources_needed: list[ResourceType]

    # Location
    location_raw: str
    location_landmark: Optional[str] = None
    location_node_id: Optional[str] = None
    location_confidence: float = 0.0

    # Summary
    summary: str
    reasoning: str
    llm_confidence: float

    # Deduplication
    is_duplicate: bool = False
    duplicate_of_call_id: Optional[str] = None
    dedup_similarity: Optional[float] = None

    # Tracing
    triaged_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    llm_provider: str = ""
    llm_model: str = ""
    original_transcript: str = ""
