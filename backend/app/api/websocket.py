"""
WebSocket connection manager.
Handles multiple simultaneous clients, broadcast, and heartbeat.
"""

import asyncio
import json
import time
from fastapi import WebSocket, WebSocketDisconnect
from ..models.signal import SignalFrame, UnknownFrame, StatusMessage


class ConnectionManager:
    """Manages all active WebSocket connections and broadcasts."""

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.append(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            if ws in self._connections:
                self._connections.remove(ws)

    async def broadcast(self, data: dict):
        """Send a JSON message to all connected clients."""
        if not self._connections:
            return
        msg = json.dumps(data)
        dead = []
        async with self._lock:
            clients = list(self._connections)
        for ws in clients:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    async def broadcast_signal(self, frame: SignalFrame):
        await self.broadcast(frame.model_dump())

    async def broadcast_unknown(self, frame: UnknownFrame):
        await self.broadcast(frame.model_dump())

    async def broadcast_status(self, event: str, detail: str = ""):
        msg = StatusMessage(event=event, detail=detail)
        await self.broadcast(msg.model_dump())

    async def heartbeat_loop(self, interval: float = 5.0):
        """Send periodic heartbeat to keep connections alive."""
        while True:
            await asyncio.sleep(interval)
            if self._connections:
                await self.broadcast({
                    "type": "heartbeat",
                    "ts": time.time(),
                    "clients": len(self._connections),
                })

    @property
    def client_count(self) -> int:
        return len(self._connections)


# Singleton instance shared across the app
manager = ConnectionManager()
