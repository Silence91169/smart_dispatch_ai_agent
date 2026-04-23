"""Shared application singletons accessed via FastAPI's Depends()."""

from dataclasses import dataclass, field
from typing import Optional

from smart_dispatch.data.resource_db import ResourceDB
from smart_dispatch.agents.dispatch.agent import DispatchAgent
from smart_dispatch.agents.triage.agent import TriageAgent
from smart_dispatch.orchestration.event_bus import EventBus
from smart_dispatch.orchestration.graph import DispatchOrchestrator
from smart_dispatch.api.simulation import SimulationRunner


@dataclass
class AppState:
    db: Optional[ResourceDB] = None
    triage_agent: Optional[TriageAgent] = None
    dispatch_agent: Optional[DispatchAgent] = None
    event_bus: Optional[EventBus] = None
    orchestrator: Optional[DispatchOrchestrator] = None
    simulation: Optional[SimulationRunner] = None
    dispatch_decisions: list = field(default_factory=list)


app_state = AppState()


def get_state() -> AppState:
    return app_state
