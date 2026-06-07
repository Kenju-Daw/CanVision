# CAN Vision API Reference

## Base URL
- **Production**: (TBD)
- **Development**: `http://localhost:8000`

## REST Endpoints

### Files

#### POST /api/upload
Upload a CAN log file for offline analysis.

**Request:**
```bash
curl -F "file=@test_j1939.log" http://localhost:8000/api/upload
```

**Response:**
```json
{
  "file_id": "a1b2c3d4",
  "filename": "test_j1939.log",
  "size_bytes": 1024,
  "format": "log"
}
```

---

#### GET /api/files
List all uploaded files.

**Response:**
```json
{
  "files": [
    {
      "file_id": "a1b2c3d4",
      "filename": "test_j1939.log",
      "format": "log",
      "size_bytes": 1024,
      "uploaded_at": 1717000000.5
    }
  ]
}
```

---

#### DELETE /api/files/{file_id}
Delete an uploaded file.

**Response:**
```json
{
  "deleted": "a1b2c3d4"
}
```

---

### DBC Management

#### POST /api/dbc
Upload a DBC file. Merges with built-in J1939 base database.

**Request:**
```bash
curl -F "file=@custom.dbc" http://localhost:8000/api/dbc
```

**Response:**
```json
{
  "filename": "custom.dbc",
  "messages_loaded": 42
}
```

---

#### GET /api/dbc/signals
Get all signal definitions (merged DBC + J1939 base).

**Response:**
```json
{
  "count": 56,
  "signals": [
    {
      "pgn": 61444,
      "pgn_name": "EEC1",
      "spn": 190,
      "spn_name": "EngineSpeed",
      "scale": 0.125,
      "offset": 0.0,
      "unit": "rpm",
      "min_value": 0.0,
      "max_value": 8031.875,
      "display_min": 0.0,
      "display_max": 8000.0,
      "byte_start": 3,
      "byte_len": 2,
      "gauge_type": "tachometer",
      "source": "j1939_standard",
      "warn_threshold": 7000.0,
      "crit_threshold": 7500.0,
      "enabled": true
    }
  ]
}
```

---

### Replay

#### POST /api/replay/start
Start replaying a log file.

**Request:**
```json
{
  "file_id": "a1b2c3d4",
  "speed": 1.0,
  "start_ts": null,
  "end_ts": null
}
```

**Response:**
```json
{
  "started": true,
  "file_id": "a1b2c3d4",
  "speed": 1.0
}
```

**Errors:**
```json
{
  "detail": "File not found. Upload it first."
}
```

---

#### POST /api/replay/stop
Stop an active replay.

**Response:**
```json
{
  "stopped": true
}
```

---

### System

#### GET /api/status
Get backend status.

**Response:**
```json
{
  "status": "ok",
  "ws_clients": 2,
  "signals_active": 42,
  "dbc_loaded": false,
  "dbc_signals": 0,
  "replay_running": true,
  "uploaded_files": 3,
  "supported_formats": [".asc", ".blf", ".log", ".mdf", ".mdf4", ".mf4", ".trc"]
}
```

---

#### GET /
Health check.

**Response:**
```json
{
  "service": "CAN Vision Backend",
  "version": "1.0.0",
  "ws": "ws://localhost:8000/ws",
  "docs": "http://localhost:8000/docs"
}
```

---

## WebSocket (ws://localhost:8000/ws)

### Message Types

#### Signal (Server → Client)
```json
{
  "type": "signal",
  "ts": 1717000000.020,
  "pgn": 61444,
  "pgn_name": "EEC1",
  "spn": 190,
  "spn_name": "EngineSpeed",
  "value": 1200.5,
  "unit": "rpm",
  "raw_hex": "11 62 EB F0 FF FF FF FF",
  "source_address": 0,
  "source": "j1939_standard",
  "channel": 0,
  "session_min": 0.0,
  "session_max": 2400.0,
  "session_avg": 1200.5,
  "rate_hz": 50.0
}
```

---

#### Unknown (Server → Client)
Raw frame that couldn't be decoded.

```json
{
  "type": "unknown",
  "ts": 1717000000.020,
  "arbitration_id": 123456,
  "arbitration_id_hex": "0x0001E240",
  "pgn": 7744,
  "pgn_hex": "0x1E40",
  "source_address": 64,
  "dlc": 8,
  "data_hex": "12 34 56 78 9A BC DE F0"
}
```

---

#### Status (Server → Client)
Status event (replay start, stop, error, etc).

```json
{
  "type": "status",
  "event": "replay_start",
  "detail": "test_j1939.log at 1.0x"
}
```

---

#### Heartbeat (Server → Client)
Periodic keep-alive.

```json
{
  "type": "heartbeat",
  "ts": 1717000000.100,
  "clients": 3
}
```

---

#### Ping (Client → Server), Pong (Server → Client)
```json
{ "type": "ping" }
{ "type": "pong" }
```

---

## Data Types

### RawFrame (Internal)
```typescript
interface RawFrame {
  ts: number;                    // Unix timestamp or relative seconds
  arbitration_id: number;        // 29-bit extended CAN ID
  is_extended_id: boolean;
  dlc: number;                   // 0-8 bytes
  data: number[];                // [0x11, 0x62, ...]
  channel: number;               // 0 = main CAN bus
  is_error_frame?: boolean;
}
```

### SignalDefinition (Metadata)
```typescript
interface SignalDefinition {
  pgn: number;
  pgn_name: string;
  spn: number;
  spn_name: string;
  scale: number;                 // raw * scale + offset = physical
  offset: number;
  unit: string;                  // "rpm", "km/h", "%", etc
  min_value: number;
  max_value: number;
  display_min: number;
  display_max: number;
  byte_start: number;            // Physical byte in payload
  byte_len: number;              // 1-8 bytes
  gauge_type: "tachometer" | "speedometer" | "thermometer" | "bar" | "numeric" | "led";
  source: "user_dbc" | "j1939_standard" | "unknown";
  warn_threshold?: number;
  crit_threshold?: number;
  enabled: boolean;
}
```

### ReplayConfig
```typescript
interface ReplayConfig {
  file_id: string;
  speed: number;                 // 0.1 - 10.0 (default 1.0)
  start_ts?: number;             // Optional: start from this timestamp
  end_ts?: number;               // Optional: stop at this timestamp
}
```

---

## Error Handling

All errors return JSON with HTTP status + detail:

```json
{
  "detail": "Unsupported file format: '.xyz'"
}
```

| Status | Meaning |
|--------|---------|
| 200 | OK |
| 400 | Bad request (invalid file, bad format) |
| 404 | Not found (file_id doesn't exist) |
| 409 | Conflict (replay already running) |
| 500 | Server error (parser crash, disk full, etc) |

---

## Authentication

Currently: **None**

Phase 2+: Add API key or JWT if deploying to shared server.

---

## Rate Limits

None (phase 1). Future:
- 10 file uploads per hour per IP
- 100 API calls per minute per IP
- WebSocket: 100 messages/sec per client

---

## Versioning

API is versioned as `/api/v1/...` (future). Currently unversioned paths.

Breaking changes will increment major version.

---

## Example: Full Replay Flow

```javascript
// 1. Upload file
const uploadRes = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData  // file input
});
const { file_id } = await uploadRes.json();

// 2. Connect WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === 'signal') {
    console.log(`${data.spn_name}: ${data.value} ${data.unit}`);
  }
};

// 3. Start replay
const replayRes = await fetch('http://localhost:8000/api/replay/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ file_id, speed: 1.0 })
});
console.log(await replayRes.json());  // { "started": true, ... }

// 4. Stop replay (later)
await fetch('http://localhost:8000/api/replay/stop', { method: 'POST' });
```
