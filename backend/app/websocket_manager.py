"""WebSocket connection manager for ChainShieldAI.

Manages active WebSocket connections and broadcasts updated
graph snapshots to all connected clients.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections for real-time graph updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, data: dict[str, Any]) -> None:
        """Broadcast JSON data to all connected clients.

        Handles disconnected clients gracefully by removing them
        from the active connections list.
        """
        disconnected: list[WebSocket] = []
        message = json.dumps(data)

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            try:
                self.active_connections.remove(conn)
            except ValueError:
                pass

    @property
    def connection_count(self) -> int:
        """Return the number of active connections."""
        return len(self.active_connections)
