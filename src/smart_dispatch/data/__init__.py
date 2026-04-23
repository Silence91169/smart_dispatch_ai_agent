"""Data simulation layer — 911 call generation and golden dataset."""

from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.call_stream import CallStream
from smart_dispatch.data.golden_dataset import get_duplicates_map, load_golden_dataset
from smart_dispatch.data.schemas import (
    ExpectedTriage,
    GoldenCase,
    IncidentType,
    Location,
    MockCall,
    ResourceType,
    Severity,
)

__all__ = [
    "MockCallGenerator",
    "CallStream",
    "load_golden_dataset",
    "get_duplicates_map",
    "MockCall",
    "ExpectedTriage",
    "GoldenCase",
    "IncidentType",
    "Location",
    "ResourceType",
    "Severity",
]
