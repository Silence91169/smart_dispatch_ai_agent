"""Integration tests for TriageAgent — 5 canonical transcripts with real LLM.

Requires GROQ_API_KEY (or another configured provider) in environment.
Skipped automatically when running without API keys (mark: integration).
"""

import os
import pytest

from smart_dispatch.agents.triage.agent import TriageAgent
from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity, MockCall


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def triage_agent(city_graph):
    """Single agent shared across tests — dedup index carries state."""
    if not os.getenv("GROQ_API_KEY") and not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No LLM API key configured — set GROQ_API_KEY to run integration tests")
    return TriageAgent(city_graph=city_graph)


@pytest.mark.asyncio
async def test_triage_agent_initializes(triage_agent):
    await triage_agent.initialize()
    healthy = await triage_agent.health_check()
    assert healthy


@pytest.mark.asyncio
async def test_fire_at_cp(triage_agent):
    await triage_agent.initialize()
    call = MockCall(transcript="bhai fire at CP, 3 log phase hai andar, log phanse hain")
    result = await triage_agent.process(call)

    assert result.incident_type == IncidentType.FIRE
    assert result.severity in (Severity.CRITICAL, Severity.HIGH)
    assert any(r == ResourceType.FIRE_TRUCK for r in result.resources_needed)
    assert not result.is_duplicate


@pytest.mark.asyncio
async def test_medical_at_aiims(triage_agent):
    await triage_agent.initialize()
    call = MockCall(transcript="aunty ji collapse ho gayi AIIMS ke paas, heart attack lag raha hai")
    result = await triage_agent.process(call)

    assert result.incident_type == IncidentType.MEDICAL
    assert result.severity in (Severity.CRITICAL, Severity.HIGH)
    assert any(r == ResourceType.AMBULANCE for r in result.resources_needed)


@pytest.mark.asyncio
async def test_accident_at_nehru_place(triage_agent):
    await triage_agent.initialize()
    call = MockCall(transcript="accident at Nehru Place, 2 cars crashed, one person injured")
    result = await triage_agent.process(call)

    assert result.incident_type == IncidentType.ACCIDENT
    assert result.severity in (Severity.HIGH, Severity.MEDIUM, Severity.CRITICAL)


@pytest.mark.asyncio
async def test_crime_at_karol_bagh(triage_agent):
    await triage_agent.initialize()
    call = MockCall(transcript="robbery happening at Karol Bagh market, 3 men with weapons")
    result = await triage_agent.process(call)

    assert result.incident_type == IncidentType.CRIME
    assert any(r == ResourceType.POLICE_CAR for r in result.resources_needed)


@pytest.mark.asyncio
async def test_hazard_gas_leak_dwarka(triage_agent):
    await triage_agent.initialize()
    call = MockCall(transcript="gas leak at Dwarka sector 10, smell very strong, people evacuating")
    result = await triage_agent.process(call)

    assert result.incident_type == IncidentType.HAZARD
    assert result.severity in (Severity.HIGH, Severity.CRITICAL, Severity.MEDIUM)
