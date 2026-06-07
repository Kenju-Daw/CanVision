"""
Upload and replay API routes.
POST /api/upload    — upload a CAN log file
POST /api/dbc       — upload a DBC file
POST /api/replay/start — start replay
POST /api/replay/stop  — stop replay
GET  /api/files     — list uploaded files
GET  /api/status    — system status
"""

import asyncio
import os
import shutil
import time
import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..parsers import get_parser, supported_extensions
from ..decoders.dbc_loader import DBCLoader
from ..decoders.j1939_decoder import J1939Decoder
from ..decoders.tp_reassembler import TPReassembler
from ..db.signal_store import SignalStore
from ..api.websocket import manager
from ..models.signal import ReplayConfig, SignalFrame, UnknownFrame

router = APIRouter(prefix="/api")

# Upload directory
UPLOAD_DIR = "/tmp/can_vision_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Shared state (injected via app.state in main.py)
_dbc_loader: DBCLoader | None = None
_signal_store: SignalStore | None = None
_replay_task: asyncio.Task | None = None
_replay_running = False
_uploaded_files: dict[str, dict] = {}   # file_id -> metadata


def init(dbc_loader: DBCLoader, signal_store: SignalStore):
    global _dbc_loader, _signal_store
    _dbc_loader = dbc_loader
    _signal_store = signal_store


@router.get("/status")
async def get_status():
    return {
        "status": "ok",
        "ws_clients": manager.client_count,
        "signals_active": _signal_store.signal_count() if _signal_store else 0,
        "dbc_loaded": _dbc_loader.has_user_dbc() if _dbc_loader else False,
        "dbc_signals": _dbc_loader.signal_count() if _dbc_loader else 0,
        "replay_running": _replay_running,
        "uploaded_files": len(_uploaded_files),
        "supported_formats": supported_extensions(),
    }


@router.get("/files")
async def list_files():
    return {"files": list(_uploaded_files.values())}


@router.post("/upload")
async def upload_log_file(file: UploadFile = File(...)):
    """Upload a CAN log file (.trc, .log, .asc, .blf, .mf4)."""
    filename = file.filename or "unknown"
    file_id = str(uuid.uuid4())[:8]
    dest = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")

    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    # Validate we have a parser for this format
    try:
        get_parser(filename)
    except ValueError as e:
        os.remove(dest)
        raise HTTPException(status_code=400, detail=str(e))

    size = os.path.getsize(dest)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

    _uploaded_files[file_id] = {
        "file_id": file_id,
        "filename": filename,
        "format": ext,
        "size_bytes": size,
        "path": dest,
        "uploaded_at": time.time(),
    }

    return {"file_id": file_id, "filename": filename, "size_bytes": size, "format": ext}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    info = _uploaded_files.pop(file_id, None)
    if info is None:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        os.remove(info["path"])
    except OSError:
        pass
    return {"deleted": file_id}


@router.post("/dbc")
async def upload_dbc(file: UploadFile = File(...)):
    """Upload a DBC file. Merges with built-in J1939 base DB."""
    if _dbc_loader is None:
        raise HTTPException(status_code=500, detail="DBC loader not initialised")

    filename = file.filename or "upload.dbc"
    dest = os.path.join(UPLOAD_DIR, f"user_{filename}")

    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        count = _dbc_loader.load_dbc(dest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DBC load failed: {e}")

    return {"filename": filename, "messages_loaded": count}


@router.get("/dbc/signals")
async def get_signals():
    """List all resolved signal definitions."""
    if _dbc_loader is None:
        return {"signals": []}
    defs = _dbc_loader.get_all_signal_defs()
    return {"signals": [d.model_dump() for d in defs], "count": len(defs)}


@router.post("/replay/start")
async def start_replay(config: ReplayConfig):
    """Start replaying a previously uploaded log file."""
    global _replay_task, _replay_running

    if config.file_id not in _uploaded_files:
        raise HTTPException(status_code=404, detail="File not found. Upload it first.")

    if _replay_running:
        raise HTTPException(status_code=409, detail="Replay already running. Stop it first.")

    file_info = _uploaded_files[config.file_id]
    _replay_task = asyncio.create_task(
        _run_replay(file_info["path"], file_info["filename"], config)
    )

    return {"started": True, "file_id": config.file_id, "speed": config.speed}


@router.post("/replay/stop")
async def stop_replay():
    global _replay_running, _replay_task
    _replay_running = False
    if _replay_task and not _replay_task.done():
        _replay_task.cancel()
    return {"stopped": True}


async def _run_replay(filepath: str, filename: str, config: ReplayConfig):
    """
    Async replay loop.
    Reads frames from file, decodes them, and streams via WebSocket.
    Throttled to config.speed × real time.
    """
    global _replay_running

    if _dbc_loader is None or _signal_store is None:
        await manager.broadcast_status("error", "Backend not initialised")
        return

    _replay_running = True
    _signal_store.reset_session()

    parser = get_parser(filename)
    decoder = J1939Decoder(_dbc_loader)
    tp = TPReassembler()

    await manager.broadcast_status("replay_start", f"Replaying {filename} at {config.speed}x")

    try:
        prev_frame_ts: Optional[float] = None
        prev_wall_ts = time.monotonic()
        frame_count = 0

        for raw_frame in parser.parse(filepath):
            if not _replay_running:
                break

            # Speed-adjusted sleep between frames
            if prev_frame_ts is not None:
                frame_gap = raw_frame.ts - prev_frame_ts
                if frame_gap > 0:
                    target_sleep = frame_gap / config.speed
                    elapsed = time.monotonic() - prev_wall_ts
                    sleep_time = max(0.0, target_sleep - elapsed)
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)

            prev_frame_ts = raw_frame.ts
            prev_wall_ts = time.monotonic()
            frame_count += 1

            # J1939 TP reassembly
            for processed_frame in tp.process(raw_frame):
                # Decode
                decoded_list = decoder.decode(processed_frame)

                for decoded in decoded_list:
                    if isinstance(decoded, SignalFrame):
                        _signal_store.update(decoded)
                        await manager.broadcast_signal(decoded)
                    elif isinstance(decoded, UnknownFrame):
                        # Only broadcast unknowns occasionally to avoid flooding
                        if frame_count % 100 == 0:
                            await manager.broadcast_unknown(decoded)

        await manager.broadcast_status("replay_complete", f"{frame_count} frames processed")

    except asyncio.CancelledError:
        await manager.broadcast_status("replay_stopped", "Replay cancelled by user")
    except Exception as e:
        await manager.broadcast_status("replay_error", str(e))
    finally:
        _replay_running = False
        tp.clear()
