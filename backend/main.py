"""
CAN Vision — Backend Entry Point
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router
from app.api.upload import init as init_upload
from app.api.websocket import manager
from app.decoders.dbc_loader import DBCLoader
from app.db.signal_store import SignalStore


# ── Shared state ────────────────────────────────────────────────────────────
dbc_loader = DBCLoader()
signal_store = SignalStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup / shutdown."""
    # Wire shared state into upload router
    init_upload(dbc_loader, signal_store)

    # Start WebSocket heartbeat background task
    heartbeat_task = asyncio.create_task(manager.heartbeat_loop(interval=5.0))

    print("✅ CAN Vision backend started")
    print("   WebSocket : ws://localhost:8000/ws")
    print("   API docs  : http://localhost:8000/docs")
    print()

    yield

    heartbeat_task.cancel()
    print("CAN Vision backend stopped")


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CAN Vision Backend",
    description="CAN bus / J1939 log file parser and signal decoder",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)


# ── WebSocket endpoint ───────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.broadcast_status("client_connected", f"Clients: {manager.client_count}")
    try:
        while True:
            # Keep connection alive; handle any client messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle client commands (future: filter, seek, etc.)
                import json
                cmd = json.loads(data)
                if cmd.get("cmd") == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text('{"type":"ping"}')
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
        await manager.broadcast_status("client_disconnected", f"Clients: {manager.client_count}")


# ── Root health check ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "CAN Vision Backend",
        "version": "1.0.0",
        "ws": "ws://localhost:8000/ws",
        "docs": "http://localhost:8000/docs",
    }
