"""Async-safe min-heap priority queue for incidents."""

from __future__ import annotations

import asyncio
import heapq
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from smart_dispatch.agents.triage.schemas import TriageResult

from .schemas import SEVERITY_PRIORITY


@dataclass(order=True)
class QueuedIncident:
    """Wrapper for heapq ordering. Sort by (priority, timestamp, seq)."""

    priority: int
    enqueued_at: datetime
    seq: int
    triage: TriageResult = field(compare=False)
    invalidated: bool = field(default=False, compare=False)


class IncidentPriorityQueue:
    """Async-safe min-heap of pending incidents.

    CRITICAL (priority=0) always comes before HIGH (priority=1), even if HIGH arrived first.
    Invalidated entries are skipped lazily on pop/peek — no costly heap removal needed.
    """

    def __init__(self) -> None:
        self._heap: list[QueuedIncident] = []
        self._lock = asyncio.Lock()
        self._seq = 0
        self._by_incident: dict[str, QueuedIncident] = {}

    async def push(self, triage: TriageResult) -> None:
        async with self._lock:
            existing = self._by_incident.get(triage.incident_id)
            if existing is not None:
                existing.invalidated = True
            self._seq += 1
            item = QueuedIncident(
                priority=SEVERITY_PRIORITY[triage.severity],
                enqueued_at=triage.triaged_at,
                seq=self._seq,
                triage=triage,
            )
            heapq.heappush(self._heap, item)
            self._by_incident[triage.incident_id] = item

    async def pop(self) -> Optional[TriageResult]:
        async with self._lock:
            while self._heap:
                item = heapq.heappop(self._heap)
                if item.invalidated:
                    continue
                if self._by_incident.get(item.triage.incident_id) is item:
                    del self._by_incident[item.triage.incident_id]
                return item.triage
            return None

    async def peek(self) -> Optional[TriageResult]:
        async with self._lock:
            while self._heap and self._heap[0].invalidated:
                heapq.heappop(self._heap)
            return self._heap[0].triage if self._heap else None

    async def remove(self, incident_id: str) -> bool:
        async with self._lock:
            item = self._by_incident.pop(incident_id, None)
            if item is None:
                return False
            item.invalidated = True
            return True

    async def size(self) -> int:
        async with self._lock:
            return sum(1 for i in self._heap if not i.invalidated)

    async def snapshot(self) -> list[TriageResult]:
        async with self._lock:
            items = sorted(
                (i for i in self._heap if not i.invalidated),
                key=lambda i: (i.priority, i.enqueued_at, i.seq),
            )
            return [i.triage for i in items]
