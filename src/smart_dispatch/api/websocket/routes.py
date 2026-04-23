"""WebSocket endpoint — /ws/live."""

import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.websocket.manager import ConnectionManager

logger = logging.getLogger("websocket.routes")
router = APIRouter()

_manager = ConnectionManager()


@router.websocket("/ws/live")
async def ws_live(ws: WebSocket, state: AppState = Depends(get_state)) -> None:
    await _manager.connect(ws, state.event_bus)
    try:
        while True:
            # Keep the connection open; we only push, never pull.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WebSocket closed unexpectedly: %s", exc)
    finally:
        await _manager.disconnect(ws, state.event_bus)
