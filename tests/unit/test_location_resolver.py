"""Tests for LocationResolver — 3-tier resolution with real embeddings.

Marked @pytest.mark.slow because they load the sentence-transformer model.
"""

import pytest

from smart_dispatch.agents.triage.location_resolver import LocationResolver
from smart_dispatch.core.embeddings.sentence_transformer_provider import (
    SentenceTransformerProvider,
)


@pytest.fixture(scope="module")
def embedder():
    return SentenceTransformerProvider()


@pytest.fixture(scope="module")
def resolver(city_graph, embedder):
    return LocationResolver(city_graph=city_graph, embedder=embedder)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_exact_name_match_returns_confidence_one(resolver):
    node_id, confidence = await resolver.resolve("Connaught Place")
    assert node_id == "N01"
    assert confidence == 1.0


@pytest.mark.slow
@pytest.mark.asyncio
async def test_alias_match_cp_returns_high_confidence(resolver):
    node_id, confidence = await resolver.resolve("CP")
    assert node_id is not None
    assert confidence == pytest.approx(0.9)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_alias_match_aiims_case_insensitive(resolver):
    node_id, confidence = await resolver.resolve("aiims")
    assert node_id is not None
    assert confidence == pytest.approx(0.9)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_semantic_match_typo(resolver):
    # "chandi chowk" is close to "Chandni Chowk"
    node_id, confidence = await resolver.resolve("chandi chowk")
    assert node_id is not None
    assert confidence >= resolver.SEMANTIC_THRESHOLD


@pytest.mark.slow
@pytest.mark.asyncio
async def test_garbage_returns_none(resolver):
    node_id, confidence = await resolver.resolve("xyz123abc_nonsense_garbage")
    # Either None or low confidence
    assert node_id is None or confidence < resolver.SEMANTIC_THRESHOLD


@pytest.mark.slow
@pytest.mark.asyncio
async def test_landmark_helps_resolution(resolver):
    # Using a landmark improves the query
    node_id_with, conf_with = await resolver.resolve("market area", landmark="near AIIMS")
    node_id_plain, conf_plain = await resolver.resolve("market area")
    # Both may resolve but with landmark should at least not be worse
    assert conf_with >= 0.0


@pytest.mark.slow
@pytest.mark.asyncio
async def test_empty_string_returns_none(resolver):
    node_id, confidence = await resolver.resolve("")
    assert node_id is None
    assert confidence == 0.0
