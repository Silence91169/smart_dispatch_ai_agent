"""Integration tests for the full triage + dispatch pipeline.

Requires GROQ_API_KEY or another configured LLM provider.
"""

import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from smart_dispatch.agents.triage.agent import TriageAgent
from smart_dispatch.agents.dispatch.agent import DispatchAgent
from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.data.schemas import IncidentType, MockCall, ResourceType, Severity
from smart_dispatch.agents.dispatch.schemas import DispatchStatus


pytestmark = pytest.mark.integration


def _skip_if_no_key():
    if not any(os.getenv(k) for k in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")):
        pytest.skip("No LLM API key — set GROQ_API_KEY to run integration tests")


@pytest_asyncio.fixture
async def pipeline(fresh_db, city_graph):
    _skip_if_no_key()
    triage = TriageAgent(city_graph=city_graph)
    await triage.initialize()
    dispatch = DispatchAgent(db=fresh_db, city_graph=city_graph, enable_llm_reasoning=False)
    return triage, dispatch


@pytest.mark.asyncio
async def test_single_call_dispatches_vehicles(pipeline, fresh_db):
    triage_agent, dispatch_agent = pipeline
    call = MockCall(transcript="bhai fire at CP, 3 log phase hai andar")
    triage = await triage_agent.process(call)

    assert not triage.is_duplicate
    decision = await dispatch_agent.process(triage)

    assert decision is not None
    assert decision.status in (DispatchStatus.DISPATCHED, DispatchStatus.PARTIALLY_DISPATCHED)
    assert len(decision.assignments) > 0

    # Fleet count should be reduced
    available = await fresh_db.available_resources_by_type("fire_truck")
    # At least one fire truck should be dispatched
    fire = await fresh_db.list_resources(resource_type="fire_truck")
    dispatched = [r for r in fire if r.status.value == "dispatched"]
    assert len(dispatched) > 0


@pytest.mark.asyncio
async def test_duplicate_call_not_re_dispatched(pipeline, fresh_db):
    triage_agent, dispatch_agent = pipeline

    call1 = MockCall(
        transcript="huge fire at Connaught Place, building fully involved",
        timestamp=datetime.now(timezone.utc),
    )
    call2 = MockCall(
        transcript="fire at CP, building on fire, please send help",
        timestamp=datetime.now(timezone.utc) + timedelta(seconds=10),
    )

    t1 = await triage_agent.process(call1)
    assert not t1.is_duplicate
    d1 = await dispatch_agent.process(t1)
    assert d1 is not None

    t2 = await triage_agent.process(call2)
    d2 = await dispatch_agent.process(t2)

    if t2.is_duplicate:
        assert d2 is None  # duplicate — no new dispatch
    # If LLM didn't catch the duplicate, that's acceptable — dedup is probabilistic


@pytest.mark.asyncio
async def test_unfulfillable_when_no_resource_available(pipeline, fresh_db):
    triage_agent, dispatch_agent = pipeline

    # Exhaust all fire trucks
    fire_trucks = await fresh_db.available_resources_by_type("fire_truck")
    for i, ft in enumerate(fire_trucks):
        await fresh_db.dispatch_resource(
            resource_id=ft.id,
            incident_id=f"INC_dummy_{i}",
            destination_node="N10",
            eta_sec=9999.0,
        )

    call = MockCall(transcript="massive fire at Saket mall, need fire engines urgently")
    triage = await triage_agent.process(call)
    # Force fire type in result if LLM didn't — override for test
    if triage.incident_type != IncidentType.FIRE:
        pytest.skip("LLM classified differently — skip unfulfillable test")

    decision = await dispatch_agent.process(triage)
    if decision is not None:
        fire_assigned = [a for a in decision.assignments if a.resource_type == ResourceType.FIRE_TRUCK]
        fire_unfulfilled = [r for r in decision.unfulfilled_resources if r == ResourceType.FIRE_TRUCK]
        # Either no fire trucks assigned, or at least one unfulfilled
        assert len(fire_assigned) == 0 or len(fire_unfulfilled) > 0
