# CAN Vision

Open-source, OS-agnostic CAN bus / J1939 instrument cluster platform. Runs entirely in a browser — no installs, no OS dependency, no license fees.

## Features

- **Live Mode** (Phase 3): ESP32 WiFi bridge streams raw CAN frames to browser
- **Offline Mode** (Phase 1 ✅): Parse `.trc` `.log` `.asc` `.blf` `.mf4` files
- **J1939 Decoder** (Phase 1 ✅): PGN/SPN auto-decode + BAM/CMDT reassembly
- **DBC Manager** (Phase 2): Upload custom DBC → merge with open J1939 base
- **Instrument Cluster** (Phase 2): Configurable gauges (tachometer, speedometer, thermometer, bars)
- **Signal Editor** (Phase 2): Edit scale, offset, unit, thresholds per signal

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+

### Installation & Run

```bash
# Clone & install
git clone https://github.com/Kenju-Daw/CanVision.git
cd CanVision
make install

# Start both backend and frontend
make dev
```

Opens:
- **Dashboard**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

### Or separately:

```bash
# Terminal 1: Backend (FastAPI)
make backend

# Terminal 2: Frontend (React)
make dashboard
```

## Test with Sample Data

```bash
# Backend is running:
# 1. Open http://localhost:5173
# 2. Drop data/test_j1939.log (or any .trc/.log/.asc/.blf/.mf4)
# 3. Click "Start Replay"
# 4. Watch 9 J1939 signals decode live in the Signal Table
```

---

## Project Status

### Phase 1 ✅ Complete
- [x] Log file parsers (5 formats)
- [x] J1939 PGN/SPN decoder
- [x] BAM/CMDT transport protocol
- [x] Signal table with live values + stats
- [x] Backend API + WebSocket
- [x] React frontend scaffold

### Phase 2 🚧 In Progress
- [ ] **feat/gauges** — D3.js gauge components (Person A)
- [ ] **feat/cluster-layout** — Drag-drop grid + profiles (Person B)
- [ ] **feat/dbc-editor** — DBC upload + signal editor (Person C)
- [ ] **feat/j1939-browser** — PGN/SPN lookup widget (Person D)

### Phase 3 📋 Planned
- [ ] **feat/esp32-firmware** — TWAI + WiFi AP bridge (Person E)
- [ ] CAN FD support (ESP32-S3)
- [ ] DTC/fault panel
- [ ] Optional: AI signal inference (0.6B model)

---

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design, data flow, key decisions
- **[PHASE1_COMPLETE.md](docs/PHASE1_COMPLETE.md)** — What's built, what works, test results
- **[API.md](docs/API.md)** — Backend endpoints, WebSocket protocol, data models
- **[PHASE2_GAUGES.md](docs/PHASE2_GAUGES.md)** — Gauge component specs
- **[PHASE2_DBC.md](docs/PHASE2_DBC.md)** — DBC merge logic, signal editor UX
- **[PHASE2_CLUSTER_LAYOUT.md](docs/PHASE2_CLUSTER_LAYOUT.md)** — Grid layout, drag-drop, profiles
- **[PHASE2_J1939_BROWSER.md](docs/PHASE2_J1939_BROWSER.md)** — PGN/SPN lookup widget
- **[ESP32_SETUP.md](docs/ESP32_SETUP.md)** — Hardware BOM, firmware build, AP mode config
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Git workflow, code style, PR process

---

## Tech Stack

### Backend
- **Framework**: FastAPI + uvicorn
- **Parsers**: python-can 4.6.1, asammdf 8.8.11
- **Decoders**: cantools 41.4.1, custom J1939 logic
- **State**: Thread-safe in-memory signal store

### Frontend
- **Framework**: React 18 + Vite
- **State**: Zustand
- **Charts**: D3.js (Phase 2), Recharts
- **Layout**: react-grid-layout (Phase 2)
- **Styling**: Tailwind CSS

### Hardware (Phase 3)
- **Microcontroller**: ESP32-WROOM-32
- **CAN Transceiver**: SN65HVD230 (3.3V)
- **Firmware**: ESP-IDF + ArduinoJson + ESPAsyncWebServer

---

## File Structure

```
CanVision/
├── backend/                    # Python FastAPI
│   ├── main.py                 # Entry point
│   ├── requirements.txt
│   └── app/
│       ├── parsers/            # .trc .log .asc .blf .mf4 readers
│       ├── decoders/           # J1939 PGN/SPN, DBC, TP reassembly
│       ├── api/                # Routes, WebSocket
│       ├── db/                 # Signal store
│       └── models/             # Pydantic schemas
│
├── dashboard/                  # React frontend (Vite)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/         # SignalTable, FileUpload, (Gauges Phase 2)
│   │   ├── hooks/              # useWebSocket
│   │   └── stores/             # Zustand (signals, definitions)
│   ├── package.json
│   └── vite.config.ts
│
├── firmware/                   # ESP32 (Phase 3)
│   └── src/
│       ├── main.cpp            # TWAI + WebSocket
│       ├── can_reader.h
│       └── ws_server.h
│
├── data/
│   ├── j1939_base.json        # 9 PGNs × 14 SPNs (EEC1, CCVS1, ET1...)
│   └── test_j1939.log         # Synthetic test data (13 frames)
│
├── docs/                       # Full documentation
├── Makefile                    # Quick commands
├── .gitignore
└── CONTRIBUTING.md
```

---

## API Endpoints

### Files
- `POST /api/upload` — Upload log file
- `GET /api/files` — List uploaded files
- `DELETE /api/files/{file_id}` — Delete file

### DBC
- `POST /api/dbc` — Upload DBC
- `GET /api/dbc/signals` — List all signal definitions

### Replay
- `POST /api/replay/start` — Start replaying log
- `POST /api/replay/stop` — Stop replay
- `GET /api/status` — System status

### WebSocket
- `WS /ws` — Live signal frames (JSON)
  - Signal: `{type:"signal", ts, pgn, spn_name, value, unit, ...}`
  - Status: `{type:"status", event, detail}`
  - Heartbeat: `{type:"heartbeat", ts, clients}`

---

## Development

### Code Style
- **Python**: PEP 8 (black, flake8)
- **TypeScript**: ESLint + Prettier
- **Git**: Conventional commits (`feat:`, `fix:`, `docs:`)

### Testing
```bash
# Backend
cd backend && python -m pytest

# Frontend
cd dashboard && npm test
```

### Git Workflow
1. Create feature branch: `git checkout -b feat/your-feature main`
2. Make commits: `git commit -m "feat: description"`
3. Push: `git push origin feat/your-feature`
4. Open PR on GitHub
5. Code review → merge to `main`

---

## Troubleshooting

### Backend won't start
```bash
# Reinstall deps
pip install -r backend/requirements.txt

# Check Python version
python --version  # 3.9+
```

### Dashboard can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/

# Check proxy in vite.config.ts
# Should have: proxy: { '/api': { target: 'http://localhost:8000' } }
```

### No signals in table after replay
1. Check `/api/status` → should show `signals_active > 0`
2. Check browser console for WebSocket errors
3. Try `data/test_j1939.log` first (known good)

---

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for:
- How to claim a task
- Branch naming
- PR checklist
- Code review process

---

## License

MIT (or specify your choice)

---

## Contact

- GitHub Issues: Bug reports, feature requests
- Discussions: Architecture questions, design feedback

---

## Acknowledgments

- **J1939 Data**: CSS Electronics (open-source data pack)
- **Libraries**: python-can, cantools, asammdf, FastAPI, React, D3.js

---

**Ready to build?** Pick a Phase 2 feature, create your branch, and start coding!
