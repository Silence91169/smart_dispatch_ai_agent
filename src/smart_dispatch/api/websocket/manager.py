"""WebSocket connection manager — fan-out EventBus events to all connected clients."""

import asyncio
import logging
from typing import Optional

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from smart_dispatch.orchestration.event_bus import Event, EventBus

logger = logging.getLogger("websocket.manager")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
        self._subscribed = False

    async def connect(self, ws: WebSocket, event_bus: EventBus, history_limit: int = 100) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.append(ws)

        # Replay recent history so the client catches up immediately.
        for event in event_bus.history(limit=history_limit):
            await self._send_one(ws, event)

        # Subscribe once — EventBus deduplicates, but we track it so we never
        # unsubscribe while other connections are still alive (React StrictMode
        # causes a brief double-connect/disconnect cycle in dev).
        if not self._subscribed:
            await event_bus.subscribe(self._broadcast)
            self._subscribed = True

    async def disconnect(self, ws: WebSocket, event_bus: EventBus) -> None:
        async with self._lock:
            if ws in self._connections:
                self._connections.remove(ws)
            remaining = len(self._connections)
        # Only unsubscribe when the last connection leaves.
        if remaining == 0 and self._subscribed:
            await event_bus.unsubscribe(self._broadcast)
            self._subscribed = False

    async def _broadcast(self, event: Event) -> None:
        dead: list[WebSocket] = []
        async with self._lock:
            connections = list(self._connections)

        for ws in connections:
            await self._send_one(ws, event, dead=dead)

        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self._connections:
                        self._connections.remove(ws)

    async def _send_one(
        self, ws: WebSocket, event: Event, dead: Optional[list] = None
    ) -> None:
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_text(event.model_dump_json())
        except Exception as exc:
            logger.debug("WebSocket send failed: %s", exc)
            if dead is not None:
                dead.append(ws)
