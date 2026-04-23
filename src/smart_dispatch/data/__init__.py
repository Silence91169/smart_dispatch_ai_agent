"""Data simulation layer — 112 call generation, city graph, and resource database."""

from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.call_stream import CallStream
from smart_dispatch.data.city_graph import CityGraph, get_city_graph
from smart_dispatch.data.golden_dataset import get_duplicates_map, load_golden_dataset
from smart_dispatch.data.resource_db import Resource, ResourceDB, ResourceNotAvailableError, ResourceStatus
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
    "CityGraph",
    "get_city_graph",
    "load_golden_dataset",
    "get_duplicates_map",
    "Resource",
    "ResourceDB",
    "ResourceNotAvailableError",
    "ResourceStatus",
    "MockCall",
    "ExpectedTriage",
    "GoldenCase",
    "IncidentType",
    "Location",
    "ResourceType",
    "Severity",
]
