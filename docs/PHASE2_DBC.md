# Phase 2: DBC Editor (Person C)

## Deliverable
DBC upload + signal definition editor.

## Components

### DBCUpload.tsx
Upload custom DBC, merge with J1939 base.

### SignalDefinitionEditor.tsx
Edit per-signal: scale, offset, unit, thresholds, gauge type.

---

## Files to Create

```
dashboard/src/components/
├── DBCUpload.tsx
├── SignalDefinitionEditor.tsx
└── ...

backend/app/api/
└── signal_editor.py  (PUT /api/signals/{spn} endpoint)
```

---

## Exit Criteria

- [ ] Upload DBC → merged into signal definitions
- [ ] Edit scale, offset, unit per signal
- [ ] Changes persist (localStorage or backend)
- [ ] Source badge shows [DBC] vs [J1939]

---

Can work in parallel with Person A & B
