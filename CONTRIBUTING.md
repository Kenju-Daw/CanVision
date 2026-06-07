# Contributing to CAN Vision

Thanks for contributing! This guide explains how to work on CAN Vision in parallel across Phase 2 features.

## Getting Started

1. **Fork & clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/CanVision.git
   cd CanVision
   ```

2. **Create a feature branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```

3. **Make commits** (Conventional Commits)
   ```bash
   git commit -m "feat: add tachometer gauge component"
   git commit -m "fix: correct PGN extraction for PDU1 frames"
   git commit -m "docs: update ESP32 setup instructions"
   ```

4. **Push & open PR**
   ```bash
   git push origin feat/your-feature-name
   ```
   Then open a PR on GitHub — CI runs tests, code review, merge to `main`

---

## Phase 2 Task Assignment

### Person A: Gauges (D3.js Components)
**Branch**: `feat/gauges`  
**Files to create**:
- `dashboard/src/components/cluster/Tachometer.tsx`
- `dashboard/src/components/cluster/Speedometer.tsx`
- `dashboard/src/components/cluster/Thermometer.tsx`
- `dashboard/src/components/cluster/BarGauge.tsx`
- `dashboard/src/components/cluster/NumericDisplay.tsx`
- `dashboard/src/components/cluster/StatusLED.tsx`

**Spec**: See [PHASE2_GAUGES.md](docs/PHASE2_GAUGES.md)

### Person B: Cluster Layout (Grid + Profiles)
**Branch**: `feat/cluster-layout`  
**Files to create**:
- `dashboard/src/components/cluster/Cluster.tsx` (react-grid-layout wrapper)
- `dashboard/src/components/ClusterLayoutPanel.tsx` (UI for add/remove, profiles)

**Depends on**: `feat/gauges` merged  
**Spec**: See [PHASE2_CLUSTER_LAYOUT.md](docs/PHASE2_CLUSTER_LAYOUT.md)

### Person C: DBC Editor (Upload + Signal Editor)
**Branch**: `feat/dbc-editor`  
**Files to create**:
- `dashboard/src/components/DBCUpload.tsx`
- `dashboard/src/components/SignalDefinitionEditor.tsx`
- `backend/app/api/signal_editor.py` (update endpoint for signal overrides)

**Spec**: See [PHASE2_DBC.md](docs/PHASE2_DBC.md)

### Person D: J1939 Browser (PGN/SPN Lookup)
**Branch**: `feat/j1939-browser`  
**Files to create**:
- `dashboard/src/components/J1939Browser.tsx` (searchable tree view)
- `dashboard/src/components/J1939BrowserPanel.tsx` (side panel)

**Spec**: See [PHASE2_J1939_BROWSER.md](docs/PHASE2_J1939_BROWSER.md)

### Person E: ESP32 Firmware (CAN-to-WiFi Bridge)
**Branch**: `feat/esp32-firmware` (start now, but Phase 3)  
**Files to create**:
- `firmware/src/main.cpp`
- `firmware/src/can_reader.h`
- `firmware/src/ws_server.h`
- `firmware/platformio.ini`

**Spec**: See [ESP32_SETUP.md](docs/ESP32_SETUP.md)

---

## Code Style

### Python
```bash
# Format
black backend/

# Lint
flake8 backend/

# Type check (optional)
mypy backend/app/
```

### TypeScript / React
```bash
# Format
cd dashboard && npx prettier --write src/

# Lint
npm run lint

# No console.log in production code
# Use React DevTools for debugging
```

### Commit Messages
```
feat: add tachometer gauge component
fix: correct byte extraction in J1939 decoder
docs: add API documentation
refactor: simplify signal store logic
test: add unit tests for PGN extraction
chore: update dependencies
```

---

## Code Review Checklist

Before opening a PR, make sure:

- [ ] Branch is based on latest `main`
- [ ] Code follows style guide (black, prettier)
- [ ] No console.log or debug code
- [ ] No breaking changes to existing APIs
- [ ] Tests pass: `npm test` (frontend) or `pytest` (backend)
- [ ] Documentation updated (docstrings, README)
- [ ] Commit messages are conventional
- [ ] PR description explains what & why

**PR Template:**
```markdown
## Description
Brief summary of changes

## Why
Problem this solves / feature it adds

## Testing
How to test this change

## Checklist
- [ ] Code style (black/prettier)
- [ ] Tests passing
- [ ] Docs updated
- [ ] No breaking changes
```

---

## Avoiding Conflicts

**Golden Rule:** Minimize file overlap.

| Task | Primary Files | Don't Touch |
|------|---------------|------------|
| Person A (Gauges) | `components/cluster/*.tsx` | Person B's layout |
| Person B (Layout) | `components/Cluster*.tsx` | Person A's gauge innards |
| Person C (DBC Editor) | `components/DBC*.tsx` | API routes (coordinate) |
| Person D (J1939) | `components/J1939*.tsx` | Everything else |
| Person E (Firmware) | `firmware/` | Backend/frontend |

**API Changes?** Post in Slack/discussion first, then coordinate with Person C + E.

---

## Testing

### Frontend
```bash
cd dashboard
npm test
```

### Backend
```bash
cd backend
pip install pytest pytest-asyncio
pytest
```

### Manual Testing
```bash
# Terminal 1
make backend

# Terminal 2
make dashboard

# Browser
curl http://localhost:8000/docs
open http://localhost:5173
```

---

## Common Issues

### "Merge conflict"
```bash
git fetch origin
git rebase origin/main
# Resolve conflicts in editor
git add .
git rebase --continue
```

### "Main moved forward while I was working"
```bash
git rebase origin/main
# or
git merge origin/main
```

### "Need to update from Person X's branch"
```bash
git fetch origin
git rebase origin/feat/their-feature
```

### "Accidentally committed to main"
```bash
git reset --soft HEAD~1  # Undo last commit, keep changes
git checkout -b feat/new-branch
git commit -m "feat: message"
```

---

## Documentation

When adding a feature, update:

1. **Docstrings** (Python functions)
   ```python
   def extract_pgn(arbitration_id: int) -> tuple[int, int]:
       """
       Extract (pgn, source_address) from a 29-bit J1939 arbitration ID.
       
       Args:
           arbitration_id: 29-bit extended CAN ID
       
       Returns:
           (pgn, source_address) tuple
       
       Example:
           >>> extract_pgn(0x0CF00400)
           (61444, 0)  # EEC1, Engine #1
       """
   ```

2. **JSDoc** (TypeScript/React)
   ```typescript
   /**
    * Tachometer gauge component
    * @param value - RPM (0-8000)
    * @param unit - "rpm"
    */
   export function Tachometer({ value, unit }: Props) { ... }
   ```

3. **README or docs/** (user-facing)
   - Phase 2 doc updated
   - Feature added to project status

---

## Questions?

- **Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API**: See [API.md](docs/API.md)
- **Phase 1 details**: See [PHASE1_COMPLETE.md](docs/PHASE1_COMPLETE.md)
- **Your feature spec**: See `docs/PHASE2_*.md`

Open a discussion on GitHub if something is unclear!

---

## Code of Conduct

- Be respectful
- Help each other (no gatekeeping)
- Ask questions — no dumb questions
- Review others' PRs kindly
- Celebrate merged PRs! 🎉

Happy coding!
