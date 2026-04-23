"""Embedding + FAISS deduplication for incident detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from smart_dispatch.core.embeddings.base import EmbeddingProvider
from smart_dispatch.data.schemas import IncidentType


@dataclass
class IncidentRecord:
    """Lightweight record stored in the dedup index."""

    incident_id: str
    call_id: str
    node_id: Optional[str]
    incident_type: IncidentType
    created_at: datetime
    dedup_text: str
    embedding: np.ndarray
    duplicate_call_ids: list[str] = field(default_factory=list)


class IncidentDeduplicator:
    """Detects duplicate incidents using FAISS similarity search.

    All four criteria must pass to declare a duplicate:
    1. Same incident_type
    2. Within time window (default 15 min)
    3. Location compatible (same node, or adjacent in graph, or either unresolved)
    4. Embedding cosine similarity >= threshold (default 0.75)
    """

    DEFAULT_SIMILARITY_THRESHOLD = 0.75
    DEFAULT_TIME_WINDOW_MINUTES = 15

    def __init__(
        self,
        embedder: EmbeddingProvider,
        city_graph,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        time_window_minutes: int = DEFAULT_TIME_WINDOW_MINUTES,
    ) -> None:
        self.embedder = embedder
        self.city_graph = city_graph
        self.similarity_threshold = similarity_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
        self._records: list[IncidentRecord] = []
        self._index = None
        self._dim: Optional[int] = None

    async def _ensure_index(self) -> None:
        if self._index is None:
            import faiss

            await self.embedder.load()
            self._dim = self.embedder.dimension
            self._index = faiss.IndexFlatIP(self._dim)

    def _build_dedup_text(
        self, incident_type: IncidentType, summary: str, location_text: str
    ) -> str:
        return f"{incident_type.value} at {location_text}. {summary}"

    async def check_duplicate(
        self,
        incident_type: IncidentType,
        summary: str,
        location_text: str,
        node_id: Optional[str],
        timestamp: datetime,
    ) -> Optional[tuple[IncidentRecord, float]]:
        """Return (record, similarity) if duplicate found, else None."""
        await self._ensure_index()
        if self._index.ntotal == 0:
            return None

        query_text = self._build_dedup_text(incident_type, summary, location_text)
        query_emb = await self.embedder.embed(query_text)
        query_vec = query_emb.reshape(1, -1).astype("float32")

        k = min(10, self._index.ntotal)
        similarities, indices = self._index.search(query_vec, k)

        for sim, idx in zip(similarities[0], indices[0]):
            if idx < 0 or idx >= len(self._records):
                continue
            record = self._records[idx]

            if record.incident_type != incident_type:
                continue
            if timestamp - record.created_at > self.time_window:
                continue
            if node_id and record.node_id:
                if node_id != record.node_id and not self._are_adjacent(node_id, record.node_id):
                    continue
            if sim < self.similarity_threshold:
                continue

            return record, float(sim)

        return None

    def _are_adjacent(self, node_a: str, node_b: str) -> bool:
        try:
            return self.city_graph.graph.has_edge(node_a, node_b)
        except Exception:
            return False

    async def add_incident(
        self,
        incident_id: str,
        call_id: str,
        incident_type: IncidentType,
        summary: str,
        location_text: str,
        node_id: Optional[str],
        timestamp: datetime,
    ) -> IncidentRecord:
        """Register a new (non-duplicate) incident in the index."""
        await self._ensure_index()
        dedup_text = self._build_dedup_text(incident_type, summary, location_text)
        embedding = await self.embedder.embed(dedup_text)

        record = IncidentRecord(
            incident_id=incident_id,
            call_id=call_id,
            node_id=node_id,
            incident_type=incident_type,
            created_at=timestamp,
            dedup_text=dedup_text,
            embedding=embedding,
        )
        self._records.append(record)
        self._index.add(embedding.reshape(1, -1).astype("float32"))
        return record

    async def register_duplicate(self, primary_call_id: str, duplicate_call_id: str) -> None:
        for r in self._records:
            if r.call_id == primary_call_id:
                r.duplicate_call_ids.append(duplicate_call_id)
                return

    def prune_old(self, now: datetime) -> int:
        """Remove records older than the time window. Rebuilds the FAISS index."""
        import faiss

        cutoff = now - self.time_window
        kept = [r for r in self._records if r.created_at >= cutoff]
        pruned = len(self._records) - len(kept)
        if pruned > 0:
            self._records = kept
            self._index = faiss.IndexFlatIP(self._dim)
            if kept:
                vecs = np.vstack([r.embedding.reshape(1, -1) for r in kept]).astype("float32")
                self._index.add(vecs)
        return pruned

    def stats(self) -> dict:
        return {
            "total_incidents": len(self._records),
            "index_size": self._index.ntotal if self._index else 0,
            "similarity_threshold": self.similarity_threshold,
            "time_window_minutes": int(self.time_window.total_seconds() / 60),
        }
