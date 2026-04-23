"""In-process async pub-sub event bus."""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Awaitable, Callable

from pydantic import BaseModel, Field


class EventType(str, Enum):
    CALL_RECEIVED = "call_received"
    TRIAGE_STARTED = "triage_started"
    TRIAGE_COMPLETED = "triage_completed"
    TRIAGE_FAILED = "triage_failed"
    DUPLICATE_DETECTED = "duplicate_detected"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    DISPATCH_DECIDED = "dispatch_decided"
    RESOURCE_DISPATCHED = "resource_dispatched"
    RESOURCE_STATUS_CHANGED = "resource_status_changed"
    RESOURCE_REASSIGNED = "resource_reassigned"
    UNFULFILLED_INCIDENT = "unfulfilled_incident"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_STOPPED = "simulation_stopped"
    SIMULATION_PROGRESS = "simulation_progress"
    SYSTEM_ERROR = "system_error"


class Event(BaseModel):
    """Envelope for all system events."""

    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)
    incident_id: str | None = None
    call_id: str | None = None
    resource_id: str | None = None


Subscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    """Thread-safe in-process async pub-sub with a rolling history buffer."""

    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []
        self._lock = asyncio.Lock()
        self._history: list[Event] = []
        self._history_limit = 500
        self.logger = logging.getLogger("event_bus")

    async def subscribe(self, callback: Subscriber) -> None:
        async with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    async def unsubscribe(self, callback: Subscriber) -> None:
        async with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    async def publish(self, event: Event) -> None:
        async with self._lock:
            subs = list(self._subscribers)
            self._history.append(event)
            if len(self._history) > self._history_limit:
                self._history = self._history[-self._history_limit :]

        for sub in subs:
            try:
                await sub(event)
            except Exception as exc:
                self.logger.exception("Subscriber error on %s: %s", event.type, exc)

    def history(self, limit: int = 100) -> list[Event]:
        return self._history[-limit:]
