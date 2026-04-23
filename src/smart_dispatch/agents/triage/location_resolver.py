"""Tiered resolver: raw location text → city graph node_id."""

from __future__ import annotations

from typing import Optional

import numpy as np

from smart_dispatch.core.embeddings.base import EmbeddingProvider
from smart_dispatch.data.city_fixtures import CITY_LOCATIONS
from smart_dispatch.data.city_graph import CityGraph


class LocationResolver:
    """Resolves raw location text to a node_id using three tiers.

    Tier 1: exact canonical name match (confidence 1.0)
    Tier 2: alias substring match — longest alias wins (confidence 0.9)
    Tier 3: semantic embedding match (confidence = cosine similarity if >= threshold)
    """

    EXACT_MATCH_CONFIDENCE = 1.0
    ALIAS_MATCH_CONFIDENCE = 0.9
    SEMANTIC_THRESHOLD = 0.6

    def __init__(self, city_graph: CityGraph, embedder: EmbeddingProvider) -> None:
        self.graph = city_graph
        self.embedder = embedder
        self._node_embeddings: Optional[np.ndarray] = None
        self._node_ids: list[str] = []
        self._loaded = False

    async def load(self) -> None:
        """Pre-compute embeddings for all node descriptions."""
        if self._loaded:
            return
        descriptions: list[str] = []
        for loc in CITY_LOCATIONS:
            text = f"{loc['name']} {' '.join(loc.get('aliases', []))}"
            descriptions.append(text)
            self._node_ids.append(loc["node_id"])
        self._node_embeddings = await self.embedder.embed_batch(descriptions)
        self._loaded = True

    async def resolve(
        self, raw_text: str, landmark: Optional[str] = None
    ) -> tuple[Optional[str], float]:
        """Return (node_id, confidence). Returns (None, 0.0) if unresolvable."""
        if not raw_text:
            return None, 0.0

        await self.load()
        query = raw_text.lower().strip()
        if landmark:
            query = f"{query} {landmark.lower().strip()}"

        # Tier 1: exact canonical name
        for loc in CITY_LOCATIONS:
            if loc["name"].lower() == query:
                return loc["node_id"], self.EXACT_MATCH_CONFIDENCE

        # Tier 2: alias substring — pick longest matching alias
        best_node: Optional[str] = None
        best_len = 0
        for loc in CITY_LOCATIONS:
            for alias in loc.get("aliases", []):
                alias_lower = alias.lower()
                if alias_lower in query or query in alias_lower:
                    if len(alias_lower) > best_len:
                        best_len = len(alias_lower)
                        best_node = loc["node_id"]
        if best_node:
            return best_node, self.ALIAS_MATCH_CONFIDENCE

        # Tier 3: semantic embedding
        query_emb = await self.embedder.embed(query)
        assert self._node_embeddings is not None
        similarities = self._node_embeddings @ query_emb
        best_idx = int(np.argmax(similarities))
        best_sim = float(similarities[best_idx])

        if best_sim >= self.SEMANTIC_THRESHOLD:
            return self._node_ids[best_idx], best_sim

        return None, best_sim
