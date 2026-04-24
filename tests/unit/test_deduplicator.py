"""Unit tests for IncidentDeduplicator — embedding-based dedup logic.

Marked @pytest.mark.slow because they load the sentence-transformer model.
"""

import pytest
from datetime import datetime, timedelta

from smart_dispatch.agents.triage.deduplicator import IncidentDeduplicator
from smart_dispatch.core.embeddings.sentence_transformer_provider import (
    SentenceTransformerProvider,
)
from smart_dispatch.data.schemas import IncidentType


@pytest.fixture(scope="module")
def embedder():
    return SentenceTransformerProvider()


@pytest.fixture
def dedup(city_graph, embedder):
    return IncidentDeduplicator(
        embedder=embedder,
        city_graph=city_graph,
        similarity_threshold=0.75,
        time_window_minutes=15,
    )


NOW = datetime(2024, 1, 1, 12, 0, 0)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_empty_index_returns_none(dedup):
    result = await dedup.check_duplicate(
        incident_type=IncidentType.FIRE,
        summary="fire at market",
        location_text="Connaught Place",
        node_id="N01",
        timestamp=NOW,
    )
    assert result is None


@pytest.mark.slow
@pytest.mark.asyncio
async def test_same_type_same_location_similar_text_is_duplicate(dedup):
    await dedup.add_incident(
        incident_id="INC_001",
        call_id="call_001",
        incident_type=IncidentType.FIRE,
        summary="large fire at the market, flames spreading",
        location_text="Connaught Place",
        node_id="N01",
        timestamp=NOW,
    )

    result = await dedup.check_duplicate(
        incident_type=IncidentType.FIRE,
        summary="big fire at the market, fire spreading",
        location_text="Connaught Place",
        node_id="N01",
        timestamp=NOW + timedelta(minutes=2),
    )
    assert result is not None
    record, similarity = result
    assert record.incident_id == "INC_001"
    assert similarity >= 0.75


@pytest.mark.slow
@pytest.mark.asyncio
async def test_different_incident_types_no_match(dedup):
    await dedup.add_incident(
        incident_id="INC_med",
        call_id="call_med",
        incident_type=IncidentType.MEDICAL,
        summary="person collapsed at the market",
        location_text="Connaught Place",
        node_id="N01",
        timestamp=NOW,
    )

    result = await dedup.check_duplicate(
        incident_type=IncidentType.FIRE,  # Different type
        summary="fire at the market",
        location_text="Connaught Place",
        node_id="N01",
        timestamp=NOW + timedelta(minutes=2),
    )
    assert result is None


@pytest.mark.slow
@pytest.mark.asyncio
async def test_outside_time_window_no_match(dedup):
    await dedup.add_incident(
        incident_id="INC_old",
        call_id="call_old",
        incident_type=IncidentType.FIRE,
        summary="fire at the station",
        location_text="Saket",
        node_id="N08",
        timestamp=NOW - timedelta(minutes=20),  # outside 15-min window
    )

    result = await dedup.check_duplicate(
        incident_type=IncidentType.FIRE,
        summary="fire at the station again",
        location_text="Saket",
        node_id="N08",
        timestamp=NOW,
    )
    assert result is None


@pytest.mark.slow
@pytest.mark.asyncio
async def test_prune_old_removes_expired_records(dedup):
    await dedup.add_incident(
        incident_id="INC_prune",
        call_id="call_prune",
        incident_type=IncidentType.ACCIDENT,
        summary="accident on the highway",
        location_text="NH8",
        node_id="N15",
        timestamp=NOW - timedelta(minutes=20),
    )

    pruned = dedup.prune_old(now=NOW)
    assert pruned >= 1
    stats = dedup.stats()
    # After pruning, no old records
    for r in dedup._records:
        assert r.created_at >= NOW - timedelta(minutes=15)
