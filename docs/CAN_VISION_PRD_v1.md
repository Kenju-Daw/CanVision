# CAN Vision — Product Requirements Document
**Version:** 1.0  
**Status:** Draft — Pending Architectural Review  
**Author:** Systems Architect (AI-assisted)  
**Last Updated:** 2026-06-07  
**Audience:** Embedded engineers, frontend developers, systems integrators

---

## 0. Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-07 | Initial PRD — full scope definition |

---

## 1. Executive Summary

**CAN Vision** is an open-source, OS-agnostic CAN bus analysis and J1939 instrument cluster platform targeting automotive and heavy-duty vehicle systems engineers.

It solves a real gap: existing tools (Vector CANalyzer, PEAK PCAN-View, SavvyCAN) are either OS-locked, expensive, closed-source, or require native driver installation. CAN Vision runs entirely in a browser — no installs, no OS dependency, no license fees.

The system has two primary modes:
- **Live Mode:** An ESP32 microcontroller acts as a CAN-to-WiFi bridge in Access Point mode, streaming raw CAN frames over WebSocket to any browser on the local network.
- **Offline Mode:** A local Python server parses recorded log files (`.trc`, `.log`, `.asc`, `.mf4`, `.blf`) and streams decoded signals to the same browser dashboard.

Both modes share a single React frontend featuring a configurable instrument cluster, J1939-aware signal decoder, DBC management, and an editable signal database.

---

## 2. Problem Statement

### 2.1 Current Pain Points
1. **OS Lock-in:** PEAK PCAN-View and Vector CANalyzer are Windows-only. Engineers switching to Linux/macOS lose tooling.
2. **Driver Friction:** Every CAN USB adapter requires OS-level driver installation — blocking on restricted corporate machines.
3. **License Cost:** Professional CAN analysis suites cost €1,000–€5,000+. J1939 add-on modules are separate licenses.
4. **No Live Dashboard:** Existing tools show raw frame tables, not instrument-cluster-style visualizations for engineers on the floor.
5. **J1939 Complexity:** J1939 multi-frame reassembly (BAM/CMDT), PGN masking, and SPN scaling are not trivially handled by generic CAN tools.
6. **Log Format Fragmentation:** Engineers work with `.trc` (PEAK), `.log` (candump), `.asc` (Vector), `.mf4` (ASAM/CANedge) — rarely does one tool handle all.

### 2.2 Target User
- **Primary:** Mechatronics / Systems Engineer working with J1939 vehicles (trucks, buses, agricultural, construction equipment).
- **Secondary:** Automotive embedded developer needing a portable CAN debugging tool.
- **Environment:** Lab bench, vehicle floor, or field — laptop + browser only.

---

## 3. Goals & Non-Goals

### 3.1 Goals (Phase 1)
- [G1] OS-agnostic — runs in any modern browser (Chrome, Firefox, Safari, Edge)
- [G2] Live J1939 CAN streaming via ESP32 in WiFi AP mode
- [G3] Offline analysis of `.trc`, `.log`, `.asc`, `.mf4`, `.blf` files
- [G4] DBC file upload with J1939 standard auto-assignment
- [G5] Editable signal definitions (scale, offset, unit, range, label)
- [G6] Configurable instrument cluster (gauges, dials, bars, numeric)
- [G7] J1939 Transport Protocol support (BAM / CMDT multi-frame reassembly)
- [G8] Signal verification against J1939 standard PGN/SPN database
- [G9] Fully open source — no license dependencies

### 3.2 Non-Goals (Phase 1)
- [ ] Cloud telemetry or fleet management
- [ ] CAN bus transmission / frame injection
- [ ] Mobile native app (iOS/Android)
- [ ] Multi-user collaboration or shared sessions
- [ ] AI signal inference (deferred to Phase 2 review)
- [ ] OBD2 passenger-car protocol (separate effort)
- [ ] CAN FD (future — ESP32-S3 variant supports it)
- [ ] Proprietary OEM PGN reverse engineering

---

## 4. Users & Use Cases

### UC-01: Live Vehicle Inspection
> *An engineer connects the ESP32 to a truck's J1939 (Deutsch 9-pin) port. The ESP32 creates a WiFi hotspot. The engineer connects their laptop, opens Chrome to `192.168.4.1`, uploads a DBC file, and watches real-time engine speed, coolant temperature, and vehicle speed on an instrument cluster dashboard.*

### UC-02: Offline Log Analysis
> *An engineer has a `.trc` file recorded earlier with PEAK PCAN-Explorer. They launch the Python server locally (`python main.py`), open the browser dashboard, upload the `.trc` file, and replay/analyze the decoded J1939 signals at any speed.*

### UC-03: Signal Database Editing
> *An auto-decoded J1939 signal has incorrect scaling from the open-source DBC. The engineer clicks the signal in the table, edits the scale factor and offset, and the gauge immediately reflects the corrected value. The edit is saved locally.*

### UC-04: Custom Cluster Layout
> *A test engineer defines a cluster showing 6 gauges: RPM tachometer, speed dial, coolant temp thermometer, fuel rate bar, oil pressure dial, and DTC fault count. They save this layout as a profile named "Engine Test".*

### UC-05: DM1 Fault Code Reading
> *During a drive cycle, the engine ECU broadcasts DM1 fault codes via J1939-73 multi-frame messages. CAN Vision reassembles the BAM transport protocol frames and decodes active DTCs, showing fault lamp status and SPN/FMI pairs in a fault panel.*

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CAN Vision System                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    SHARED FRONTEND (React)                   │  │
│  │   ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │  │
│  │   │  Instrument │  │ Signal Table │  │  DBC / J1939      │  │  │
│  │   │  Cluster    │  │ + Statistics │  │  Signal Editor    │  │  │
│  │   └─────────────┘  └──────────────┘  └───────────────────┘  │  │
│  │   ┌────────────────────────────────────────────────────────┐ │  │
│  │   │              WebSocket Client (browser native)         │ │  │
│  │   └────────────────────────┬───────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────  │
│                               │                                     │
│          ┌────────────────────┴────────────────────┐               │
│          │                                          │               │
│   ┌──────┴──────────────┐            ┌─────────────┴─────────────┐ │
│   │   LIVE MODE          │            │   OFFLINE MODE             │ │
│   │                      │            │                            │ │
│   │  ESP32 (AP Mode)     │            │  Python FastAPI            │ │
│   │  192.168.4.1:80      │            │  localhost:8000            │ │
│   │  ws://192.168.4.1:81 │            │  ws://localhost:8000/ws   │ │
│   │                      │            │                            │ │
│   │  ┌────────────────┐  │            │  ┌──────────────────────┐ │ │
│   │  │ TWAI Peripheral│  │            │  │ File Parsers          │ │ │
│   │  │ 250K / 500K    │  │            │  │ .trc .log .asc       │ │ │
│   │  └───────┬────────┘  │            │  │ .mf4 .blf .csv       │ │ │
│   │          │           │            │  └──────────────────────┘ │ │
│   │  ┌───────┴────────┐  │            │  ┌──────────────────────┐ │ │
│   │  │ SN65HVD230     │  │            │  │ DBC Decoder          │ │ │
│   │  │ CAN Transceiver│  │            │  │ cantools 41.4.1      │ │ │
│   │  └───────┬────────┘  │            │  └──────────────────────┘ │ │
│   │          │           │            │  ┌──────────────────────┐ │ │
│   │   [J1939 Deutsch]    │            │  │ J1939 TP Assembler   │ │ │
│   │    Vehicle Bus       │            │  │ BAM / CMDT           │ │ │
│   └──────────────────────┘            │  └──────────────────────┘ │ │
│                                       └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.1 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend tech | React (browser) | OS agnostic, no install, rich ecosystem |
| Live bridge | ESP32 TWAI + WiFi AP | No laptop drivers, OS-independent, cheap hardware |
| CAN decode location | Client-side JS (live) + Python (offline) | Browser handles live; Python handles binary formats |
| DBC decode library | cantools (Python), custom JS parser (live) | cantools is gold standard; JS needed for browser |
| J1939 TP | Server-side (offline) + ESP32 partial (live) | Multi-frame reassembly is stateful — managed server-side |
| Data streaming | WebSocket (native browser API) | Low overhead, bidirectional, real-time |
| Storage | SQLite + local filesystem | No cloud dependency, laptop-only |
| Packaging | Python venv + npm | Minimal dependency on system-level installs |

---

## 6. Hardware Specification — ESP32 Firmware

### 6.1 Bill of Materials (Minimum Viable)

| Component | Part | Notes |
|-----------|------|-------|
| Microcontroller | ESP32-WROOM-32 or ESP32-DevKit | 240 MHz dual-core, 520 KB SRAM, built-in WiFi |
| CAN Transceiver | SN65HVD230 (TI) | 3.3V compatible, 1 Mbit/s, ±12V bus fault tolerance |
| Connector | DB9 female + J1939 Deutsch 9-pin adapter | Or OBD2 splitter for lighter trucks |
| Power | 7–32V via DB9 pin 9 (VBatt) → 3.3V LDO | Powered from vehicle, no USB needed in field |
| Termination | Optional 120Ω switch | External when bus doesn't have termination |

### 6.2 TWAI Peripheral Configuration

```
CAN bit rate: 250 kbps (default) / 500 kbps (configurable)
Mode: Listen-only (default) → Active (optional, for address claim)
RX pin: GPIO 22
TX pin: GPIO 21
Filter: Accept all (PGN filtering done on frontend)
RX Queue: 64 frames (FIFO)
```

### 6.3 WiFi Access Point Configuration

```
SSID: CANVision_XXXXXX (last 6 of MAC)
Password: canvision (configurable in firmware)
IP: 192.168.4.1
HTTP: Port 80 (serves configuration page)
WebSocket: Port 81
Max clients: 4 simultaneous WebSocket connections
```

### 6.4 WebSocket Frame Format (ESP32 → Browser)

```json
{
  "ts": 1234567890.123,
  "id": "0x0CF00401",
  "ext": true,
  "dlc": 8,
  "data": [17, 98, 235, 240, 255, 255, 255, 255],
  "ch": 0
}
```

### 6.5 ESP32 Firmware Library Stack

| Library | Version | Purpose |
|---------|---------|---------|
| ESP-IDF TWAI driver | ESP-IDF 5.x | CAN hardware peripheral |
| ESPAsyncWebServer | 3.x | HTTP + WebSocket server |
| ArduinoJson | 7.x | JSON serialization |
| WiFi (built-in) | — | AP mode |
| Preferences | — | Config persistence in NVS |

### 6.6 Throughput Budget

| Parameter | Value |
|-----------|-------|
| J1939 typical frame rate | 500–1500 frames/s |
| Frame size (JSON) | ~120 bytes avg |
| Peak WebSocket throughput | ~180 KB/s (1500 × 120B) |
| ESP32 WiFi bandwidth | ~2–5 MB/s (more than sufficient) |
| Client throttle (dashboard) | 20 Hz update cycle (downsample in browser) |

---

## 7. Feature Specifications

### 7.1 Live Mode — ESP32 WiFi Bridge

**Description:** Engineer connects laptop to ESP32 AP, browser opens `http://192.168.4.1`, selects Live mode. Real-time raw CAN frames stream via WebSocket. DBC decode and J1939 lookup happen client-side in JavaScript.

**Acceptance Criteria:**
- [ ] Browser receives WebSocket frames within 100ms of CAN frame arrival
- [ ] Dashboard updates at ≥ 10 Hz for active signals
- [ ] Supports simultaneous connection of up to 4 browser clients
- [ ] AP SSID visible within 5 seconds of power-on
- [ ] Listen-only mode default (no frames transmitted to vehicle bus)

**Configuration Page (`192.168.4.1`):**
- Bit rate selector (250K / 500K / 1M)
- Listen-only / Active toggle
- SSID/password change
- Filter PGN list (whitelist)

---

### 7.2 Offline Analysis Mode

**Description:** Python FastAPI server runs locally. Engineer uploads a log file. Backend parses, DBC-decodes, and streams signals via WebSocket to the dashboard. Supports replay at variable speed.

**Supported Formats:**

| Format | Library | Notes |
|--------|---------|-------|
| `.trc` | python-can TRCReader | PEAK PCAN-Explorer v1.1 and v2.0 |
| `.log` | python-can CanutilsLogReader | Linux candump format |
| `.asc` | python-can ASCReader | Vector CANalyzer ASCII |
| `.blf` | python-can BLFReader | Vector Binary Logging Format |
| `.mf4` | asammdf MDF() | ASAM MDF4; CSS CANedge native |
| `.csv` | pandas | Generic timestamp + ID + data |

**Acceptance Criteria:**
- [ ] File upload via drag-and-drop or file picker (React)
- [ ] Parse completion notification within 5s for files < 50MB
- [ ] Replay speed: 0.1x, 0.5x, 1x, 2x, 5x, 10x, max
- [ ] Scrubber bar for timeline navigation
- [ ] Signal filter: show only selected PGNs/SPNs during replay

---

### 7.3 DBC Management & J1939 Auto-Assignment

**Description:** User uploads a DBC file. CAN Vision merges it with a built-in J1939 open-source signal database. Known PGNs are auto-labelled. Unknown PGNs are flagged.

**Signal Resolution Priority:**
1. User-uploaded DBC (highest priority — always wins)
2. Built-in open J1939 database (arthithadee/J1939-DBC-Database + nberlette/canbus)
3. Raw hex (unresolved — displayed as `Unknown PGN 0xXXXX`)

**DBC Merge Logic:**
- On DBC upload, parse with cantools
- For each message in DBC: check if PGN already in J1939 base → if yes, user DBC signals override
- J1939 base fills gaps for PGNs not in user DBC
- All resolved signals go into unified `SignalStore`

**Acceptance Criteria:**
- [ ] DBC upload via drag-and-drop; parse within 2s for files < 10MB
- [ ] Auto-assign J1939 PGN names, SPN names, units, scale, offset from built-in DB
- [ ] Visual indicator: `[DBC]` / `[J1939 Standard]` / `[Unknown]` badge per signal
- [ ] Persisted across browser sessions (localStorage)

---

### 7.4 Signal Editor

**Description:** Any signal in the decoded database can be edited by the user. Changes take effect immediately on the live dashboard.

**Editable Fields per Signal:**

| Field | Type | Notes |
|-------|------|-------|
| Display Name | string | Overrides DBC/J1939 default |
| Scale (Factor) | float | e.g. `0.125` for Engine Speed |
| Offset | float | e.g. `-40` for temperature |
| Unit | string | e.g. `rpm`, `°C`, `km/h` |
| Min Display | float | Gauge range minimum |
| Max Display | float | Gauge range maximum |
| Warning Threshold | float | Yellow zone start |
| Critical Threshold | float | Red zone start |
| Enabled | bool | Toggle signal on/off |
| Gauge Type | enum | speedometer/tachometer/thermometer/bar/numeric |

**Acceptance Criteria:**
- [ ] Inline editing in signal table row (click to edit)
- [ ] Changes propagate to gauges within 100ms
- [ ] Export edited signal DB as modified DBC file
- [ ] Reset to standard button per signal and global

---

### 7.5 Instrument Cluster

**Description:** Configurable visual dashboard showing real-time signal values as automotive-style gauges and indicators.

**Gauge Types:**

| Type | Use Case | Example Signal |
|------|----------|----------------|
| Tachometer (arc) | RPM | Engine Speed (SPN 190) |
| Speedometer (arc) | km/h | Vehicle Speed (SPN 84) |
| Thermometer (arc) | °C | Coolant Temp (SPN 110) |
| Pressure gauge | bar/kPa | Oil Pressure |
| Fuel gauge (bar) | % | Fuel Level |
| Numeric display | any | Hours, DTC count |
| Status LED | boolean | Fault lamp, brake status |
| Bar graph | % scale | Engine Load |

**Layout:**
- Grid-based drag-and-drop layout (react-grid-layout)
- Predefined templates: "J1939 Engine", "J1939 Driveline", "Custom"
- Save/load layout profiles as JSON
- Fullscreen mode

**Acceptance Criteria:**
- [ ] Add/remove gauges from signal table drag-to-cluster
- [ ] Gauge assignment persists across sessions
- [ ] Needle animation ≥ 30 fps (requestAnimationFrame)
- [ ] Color zones (green/yellow/red) follow signal thresholds
- [ ] At least 5 simultaneous gauges with no frame drop on modern laptop

---

### 7.6 Signal Table & Statistics

**Description:** Tabular view of all active signals with live values, statistics, and filtering.

**Columns:**

| Column | Description |
|--------|-------------|
| PGN | Hex + decimal |
| SPN | Numeric ID |
| Signal Name | DBC / J1939 standard |
| Source Address | ECU SA (hex) |
| Value | Live decoded value + unit |
| Raw | Hex raw bytes |
| Min | Session minimum |
| Max | Session maximum |
| Avg | Rolling average |
| Rate | Frames/second |
| Source | `[DBC]` / `[J1939]` / `[Unknown]` |

**Acceptance Criteria:**
- [ ] Filter by PGN, SPN, SA, signal name
- [ ] Sort by any column
- [ ] Export to CSV
- [ ] Highlight signals exceeding thresholds in red

---

### 7.7 J1939 Transport Protocol (BAM / CMDT)

**Description:** J1939 multi-frame messages (>8 bytes) are reassembled from TP.CM (PGN 60416) and TP.DT (PGN 60160) frames before DBC decode.

**Supported:**
- BAM (Broadcast Announce Message) — up to 1785 bytes
- CMDT (Connection Mode Data Transfer) — RTS/CTS peer-to-peer
- DM1 active DTC list (J1939-73, PGN 65226)
- DM11 clear all faults (J1939-73)

**Acceptance Criteria:**
- [ ] BAM messages reassembled and decoded correctly
- [ ] DM1 DTC panel: active fault count, SPN, FMI, occurrence count per fault
- [ ] Fault lamp status (amber/red) from DM1 lamp status byte

---

## 8. Technical Stack

### 8.1 Firmware (ESP32)

```
Language:     C / Arduino Framework (ESP-IDF compat)
Libraries:    ESPAsyncWebServer, ArduinoJson 7.x, ESP-IDF TWAI
Build:        PlatformIO (VSCode extension)
Target:       ESP32-WROOM-32 / ESP32-DevKit
Flash:        4MB (firmware ~400KB, 3.6MB free for config NVS)
```

### 8.2 Backend (Offline Mode)

```
Language:     Python 3.9+
Framework:    FastAPI 0.115+ + uvicorn
Libraries:
  - python-can 4.6.1       (log file readers: TRC/ASC/BLF/LOG)
  - cantools 41.4.1         (DBC parse + J1939 decode)
  - asammdf 8.8.11          (MF4/MDF4 file parsing)
  - can-j1939               (TP reassembly + address claim)
  - pandas                  (data manipulation)
  - fastapi-cors            (CORS for localhost)
Packaging:    requirements.txt + optional PyInstaller bundle
```

### 8.3 Frontend (Shared Dashboard)

```
Framework:    React 18 + Vite
Styling:      TailwindCSS 3.x
State:        Zustand (signal store)
Charts:       D3.js (custom gauges) + Recharts (sparklines)
Layout:       react-grid-layout (drag-drop cluster)
WebSocket:    Native browser WebSocket API
DBC parse:    Custom JS DBC parser (for live mode client-side decode)
Routing:      React Router (Live / Offline / Settings views)
Build:        Vite (fast HMR, small bundle)
```

---

## 9. API Specification

### 9.1 ESP32 WebSocket (Live Mode)

**Endpoint:** `ws://192.168.4.1:81`

**Inbound (browser → ESP32):**
```json
{ "cmd": "set_bitrate", "value": 250000 }
{ "cmd": "set_filter", "pgns": ["0xF004", "0xFEF1"] }
{ "cmd": "ping" }
```

**Outbound (ESP32 → browser):**
```json
{
  "ts": 1234567890.123,
  "id": "0x0CF00401",
  "ext": true,
  "dlc": 8,
  "data": [17, 98, 235, 240, 255, 255, 255, 255],
  "ch": 0
}
```

**Heartbeat:** ESP32 sends `{"type":"hb","uptime":1234}` every 5s.

---

### 9.2 Python FastAPI (Offline Mode)

**Base URL:** `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload log file (multipart/form-data) |
| `GET` | `/api/files` | List uploaded files |
| `DELETE` | `/api/files/{id}` | Delete uploaded file |
| `POST` | `/api/dbc` | Upload DBC file |
| `GET` | `/api/dbc/signals` | List all resolved signals |
| `PUT` | `/api/dbc/signals/{spn}` | Edit signal definition |
| `POST` | `/api/replay/start` | Start replay (speed, start_ts, end_ts) |
| `POST` | `/api/replay/pause` | Pause replay |
| `POST` | `/api/replay/stop` | Stop replay |
| `GET` | `/api/replay/status` | Current replay position |
| `GET` | `/api/signals/export` | Export signal DB as DBC |
| `WS` | `/ws` | WebSocket — decoded signal stream |

**WebSocket Signal Frame (Python → Browser):**
```json
{
  "type": "signal",
  "ts": 1234567890.123,
  "pgn": 61444,
  "pgn_name": "EEC1",
  "spn": 190,
  "spn_name": "Engine Speed",
  "value": 621.5,
  "unit": "rpm",
  "raw": "0x6813",
  "sa": "0x00",
  "source": "j1939_standard"
}
```

---

## 10. Data Models

### 10.1 Signal Definition

```typescript
interface SignalDefinition {
  pgn: number;
  pgn_name: string;
  spn: number;
  spn_name: string;
  start_bit: number;
  length: number;
  scale: number;
  offset: number;
  unit: string;
  min_value: number;
  max_value: number;
  display_min: number;
  display_max: number;
  warn_threshold: number | null;
  crit_threshold: number | null;
  gauge_type: 'tachometer' | 'speedometer' | 'thermometer' | 'bar' | 'numeric' | 'led';
  source: 'user_dbc' | 'j1939_standard' | 'unknown';
  enabled: boolean;
  user_overrides: Partial<SignalDefinition>;
}
```

### 10.2 Live Signal Value

```typescript
interface SignalValue {
  spn: number;
  pgn: number;
  value: number;
  raw_hex: string;
  source_address: number;
  timestamp: number;
  session_min: number;
  session_max: number;
  session_avg: number;
  rate_hz: number;
}
```

### 10.3 Cluster Layout

```typescript
interface ClusterLayout {
  id: string;
  name: string;
  created_at: string;
  gauges: GaugeConfig[];
}

interface GaugeConfig {
  id: string;
  spn: number;
  gauge_type: string;
  grid_x: number;
  grid_y: number;
  grid_w: number;
  grid_h: number;
}
```

---

## 11. File & Project Structure

```
can-vision/
│
├── firmware/                        ← ESP32 PlatformIO project
│   ├── platformio.ini
│   └── src/
│       ├── main.cpp
│       ├── can_reader.h / .cpp      ← TWAI init, frame reading
│       ├── ws_server.h / .cpp       ← ESPAsyncWebServer + WebSocket
│       ├── config.h / .cpp          ← NVS config (bitrate, SSID)
│       └── j1939_filter.h           ← Optional PGN whitelist
│
├── backend/                         ← Python FastAPI (offline mode)
│   ├── requirements.txt
│   ├── main.py                      ← FastAPI app entry point
│   └── app/
│       ├── api/
│       │   ├── upload.py            ← File upload routes
│       │   ├── replay.py            ← Replay control routes
│       │   ├── signals.py           ← Signal DB routes
│       │   └── websocket.py         ← WS broadcast manager
│       ├── parsers/
│       │   ├── base_parser.py       ← Abstract parser interface
│       │   ├── trc_parser.py        ← PEAK .trc
│       │   ├── log_parser.py        ← candump .log
│       │   ├── asc_parser.py        ← Vector .asc
│       │   ├── blf_parser.py        ← Vector .blf
│       │   └── mf4_parser.py        ← ASAM MF4 (asammdf)
│       ├── decoders/
│       │   ├── dbc_loader.py        ← cantools DBC load + merge
│       │   ├── j1939_decoder.py     ← PGN masking, SPN decode
│       │   └── tp_reassembler.py    ← BAM/CMDT multi-frame
│       ├── db/
│       │   ├── signal_store.py      ← In-memory + SQLite signal DB
│       │   └── j1939_base.json      ← Open-source J1939 PGN/SPN DB
│       └── models/
│           ├── signal.py            ← Pydantic models
│           └── config.py
│
├── dashboard/                       ← React frontend (shared)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── router.tsx               ← Live / Offline / Settings routes
│       ├── components/
│       │   ├── cluster/
│       │   │   ├── Cluster.tsx      ← Main drag-drop grid
│       │   │   ├── Gauge.tsx        ← Base gauge component
│       │   │   ├── Tachometer.tsx
│       │   │   ├── Speedometer.tsx
│       │   │   ├── Thermometer.tsx
│       │   │   ├── BarGauge.tsx
│       │   │   ├── NumericDisplay.tsx
│       │   │   └── StatusLED.tsx
│       │   ├── SignalTable.tsx
│       │   ├── DBCEditor.tsx
│       │   ├── J1939Browser.tsx     ← Browse PGN/SPN DB
│       │   ├── FaultPanel.tsx       ← DM1 DTC list
│       │   ├── FileUpload.tsx
│       │   └── ReplayControls.tsx
│       ├── hooks/
│       │   ├── useWebSocket.ts      ← WS connection + reconnect
│       │   ├── useSignalStore.ts
│       │   └── useDBC.ts
│       ├── stores/
│       │   ├── signalStore.ts       ← Zustand: live signal values
│       │   ├── dbcStore.ts          ← Signal definitions + edits
│       │   └── clusterStore.ts      ← Layout profiles
│       ├── parsers/
│       │   └── dbc_parser.ts        ← JS DBC parser (live mode)
│       └── utils/
│           ├── j1939.ts             ← PGN extract, SPN decode helpers
│           └── units.ts             ← Unit conversion helpers
│
├── docs/
│   ├── PRD.md                       ← This document
│   ├── ARCHITECTURE.md
│   ├── ESP32_SETUP.md
│   ├── BACKEND_SETUP.md
│   └── CONTRIBUTING.md
│
├── data/
│   └── j1939_base.json              ← Open J1939 PGN/SPN database
│
├── .gitignore
├── README.md
└── Makefile                         ← `make backend` / `make dashboard` / `make firmware`
```

---

## 12. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Dashboard update latency (live) | < 100ms end-to-end |
| NFR-02 | File parse time (offline) | < 5s for 50MB files |
| NFR-03 | Gauge render frame rate | ≥ 30 fps |
| NFR-04 | Max simultaneous WebSocket clients | 4 (ESP32 limit) |
| NFR-05 | Browser compatibility | Chrome 90+, Firefox 90+, Safari 15+ |
| NFR-06 | Python version | 3.9+ |
| NFR-07 | ESP32 SRAM headroom | ≥ 50KB free during operation |
| NFR-08 | Backend startup time | < 3s |
| NFR-09 | DBC file size limit | 50MB |
| NFR-10 | Log file size limit | 2GB (streamed, not loaded fully) |
| NFR-11 | Bus safety | Listen-only mode default on ESP32 |

---

## 13. Phased Build Plan

### Phase 1 — Foundation (Now)
**Goal:** Working offline parser with signal table in browser.

| Task | Owner | Notes |
|------|-------|-------|
| Project scaffold (folders, README, Makefile) | Dev | |
| Python backend skeleton (FastAPI + uvicorn) | Dev | |
| `.trc` parser + WebSocket stream | Dev | Test with PEAK sample files |
| `.log` (candump) parser | Dev | |
| `.asc` (Vector) parser | Dev | |
| `.mf4` parser (asammdf) | Dev | CSS Electronics demo data |
| DBC loader (cantools) + J1939 base merge | Dev | |
| J1939 TP reassembler (BAM) | Dev | |
| React scaffold (Vite + Tailwind + Zustand) | Dev | |
| Signal table component (basic) | Dev | |
| WebSocket hook + reconnect logic | Dev | |

**Exit criteria:** Upload a `.trc` file → see decoded J1939 signals in table in browser.

---

### Phase 2 — Instrument Cluster
**Goal:** Visual gauge dashboard with DBC editor.

| Task | Notes |
|------|-------|
| D3.js gauge components (tachometer, speedometer, thermometer) | |
| Cluster grid layout (react-grid-layout) | |
| Signal → gauge assignment (drag-and-drop) | |
| DBC upload + signal editor UI | |
| J1939 standard DB browser | |
| Replay controls + scrubber | |
| Layout save/load profiles | |

**Exit criteria:** Upload CSS Electronics J1939 demo MF4 → configure cluster → see engine RPM on tachometer gauge, vehicle speed on speedometer.

---

### Phase 3 — Live Mode (ESP32)
**Goal:** Real-time J1939 data from vehicle to browser dashboard.

| Task | Notes |
|------|-------|
| ESP32 firmware: TWAI init + listen-only | PlatformIO |
| ESP32 firmware: WiFi AP mode | SSID: CANVision_XXXXXX |
| ESP32 firmware: AsyncWebSocket server | Port 81 |
| ESP32 firmware: JSON frame serialization | ArduinoJson 7 |
| ESP32 firmware: Config page (port 80) | Bit rate, filter |
| JS DBC parser for live client-side decode | Custom or port cantools |
| Frontend: Live mode WebSocket client | |
| Frontend: J1939 PGN masking in JS | |
| J1939 BAM reassembly in browser (JS) | Stateful, per SA |

**Exit criteria:** ESP32 connected to J1939 bus → laptop joins AP → browser shows live engine RPM on tachometer.

---

### Phase 4 — Polish & Hardening
| Task | Notes |
|------|-------|
| DM1 DTC decoder + fault panel | J1939-73 DBC |
| CMDT transport protocol support | Peer-to-peer |
| `.blf` (Vector Binary) parser | |
| Export: session CSV, modified DBC | |
| PyInstaller bundle (Windows + Linux .exe / bin) | |
| ESP32-S3 CAN FD variant | |
| AI signal inference (optional) | Phase 2 decision — 0.6B model |

---

## 14. Open Questions

| # | Question | Decision Needed By | Notes |
|---|----------|--------------------|-------|
| OQ-1 | Full SAE J1939 Digital Annex DBC — purchase or use open-source only? | Phase 2 | CSS Electronics DBC = ~€X. Open DBCs cover ~50–70% of common signals. |
| OQ-2 | ESP32-S3 for CAN FD support? | Phase 3 | S3 TWAI supports CAN FD. Newer trucks use CAN FD. |
| OQ-3 | Is CMDT (peer-to-peer TP) required for Phase 1? | Phase 1 exit | BAM covers most use cases. CMDT mainly for diagnostics. |
| OQ-4 | AI signal inference (0.6B model) — when to add? | Phase 4 | For unknown PGN identification. Phi-3 mini / Qwen2-0.5B. |
| OQ-5 | PyInstaller bundle — required before testing? | Phase 1 | Or just `python main.py` is acceptable for now. |
| OQ-6 | J1939 address claiming — active mode required? | Phase 3 | Needed only if ESP32 needs to transmit (e.g., request PGN). |

---

## 15. References

| Resource | URL | Type |
|----------|-----|------|
| CSS Electronics J1939 Guide | csselectronics.com/pages/j1939-explained-simple-intro-tutorial | Tutorial |
| CSS Electronics J1939 Data Pack | csselectronics.com/pages/j1939-data-pack-heavy-duty | Sample Data |
| python-can | github.com/hardbyte/python-can | Library |
| cantools | github.com/cantools/cantools | Library |
| asammdf | github.com/danielhrisca/asammdf | Library |
| can-j1939 | github.com/juergenH87/python-can-j1939 | Library |
| J1939 DBC Database | github.com/arthithadee/J1939-DBC-Database | Open DB |
| pretty_j1939 | github.com/nmfta-repo/pretty_j1939 | Tool |
| PEAK PCAN-USB FD | peak-system.com | Hardware |
| SN65HVD230 Datasheet | ti.com | Hardware |
| ESPAsyncWebServer | github.com/me-no-dev/ESPAsyncWebServer | Firmware |
| ArduinoJson | arduinojson.org | Firmware |

---

*End of CAN Vision PRD v1.0*
