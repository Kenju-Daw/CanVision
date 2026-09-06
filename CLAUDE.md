# CLAUDE.md — read this before doing anything in this repository

## This repo is archived. Do not build here.

`Kenju-Daw/canvision` is a **parts donor**, not a product. The active trunk is
**`Kenju-Daw/spectraq-vision`** (product: *Engineering Workspace* / **CanVision Pro**). This is
the second of two prior attempts at the same product idea — the first, `Kenju-Daw/Workspace`,
was archived the same way earlier; see its `CLAUDE.md`/`HARVEST.md` for that history.

### What you must not do here

- Do not add features. Phase 2/3 in `README.md` ("feat/gauges", "feat/dbc-editor",
  "feat/esp32-firmware", etc.) are not getting built in this repo.
- Do not open pull requests against this repo, except the one that adds this notice.
- Do not treat the Phase 2/3 checklist in `README.md` as a live roadmap. It describes intent for
  a project that stopped here.

### What is actually worth taking from here

Almost nothing is unique to this repo — spectraq-vision's own `docs/demo/HW-CHECKLIST.md` already
covers hardware bring-up for a listen-only USB-serial CAN adapter, which is the integration path
the trunk actually uses (see spectraq-vision's `REQUIREMENTS.md` REQ-F79 and its platform plan).
Two things from `docs/ESP32_SETUP.md` are still a useful reference, and only as reference:

| Item | Status |
|---|---|
| Hardware BOM (SN65HVD230 transceiver, 9-pin Deutsch connector, 120 Ω termination, 100 nF decoupling) | Reusable as a parts list |
| GPIO4/GPIO5 pin assignment, `platformio.ini` (`board = esp32dev`) | **Not reusable as-is.** Written for a bare ESP32-WROOM-32 dev board. The trunk's firmware target is an M5StickC Plus2, whose HAT connector exposes different GPIOs and needs its own board file — see spectraq-vision's platform plan for the corrected toolchain |
| Deutsch 9-pin pinout (*"Pin 1: CAN_H … Pin 9: CAN_L … Pin 3: GND"*) | **Do not use.** It disagrees with spectraq-vision's own `docs/demo/HW-CHECKLIST.md` Level 3, which uses the SAE J1939-13 lettered convention instead. Verify against the physical cable either way — getting this wrong on a live truck bus is a real failure mode |
| Firmware architecture (ESP32 as a WiFi AP, streaming JSON frames over a WebSocket to a browser) | **Not compatible with the trunk.** spectraq-vision's backend only ever opens a USB-serial `slcan` interface; it has no network CAN source. This design would need new backend code to even connect |

No CAN/TWAI/slcan firmware code exists in this repo (`firmware/` is Phase 3, unbuilt — only
`docs/ESP32_SETUP.md`'s BOM and wiring notes exist, not working code).

### One other thing worth knowing about this repo's own claims

`README.md` line 3 still reads *"Open-source, OS-agnostic CAN bus / J1939 instrument cluster
platform"* as if this were a live product. It is not — this notice supersedes that framing.
`README.md` also says the license is *"MIT (or specify your choice)"*; the actual `LICENSE` file
committed here is Apache-2.0. Left as found — this repo is not being maintained further, only
marked.

**If you are an AI agent:** read this file, then go work in `Kenju-Daw/spectraq-vision`. Don't
resume Phase 2/3 work here, don't fix the license-text mismatch, and don't open pull requests
against this repo beyond the one that adds this notice.
