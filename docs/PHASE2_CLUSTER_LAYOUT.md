# Phase 2: Cluster Layout (Person B)

## Deliverable
Build drag-drop gauge grid with save/load profiles.

## Components

### Cluster.tsx
Main container using react-grid-layout.

**Props:**
```typescript
interface ClusterProps {
  signals: SignalValue[];
  layout?: GridLayout[];
  onLayoutChange?: (layout: GridLayout[]) => void;
}
```

**Features:**
- 12-column grid
- Drag gauges, resize
- Snap to grid (20px)
- CompactType: "vertical"

### ClusterLayoutPanel.tsx
Sidebar UI for add/remove/profiles.

**Features:**
- Button: "Add Gauge" → select PGN/SPN from dropdown
- Button: "Remove" → click gauge to delete
- Dropdown: "Preset Layouts" (Engine, Driveline, Custom)
- Button: "Save as Preset"
- Persist to localStorage

---

## Implementation

```typescript
import GridLayout from "react-grid-layout";

export function Cluster({ signals, layout, onLayoutChange }: ClusterProps) {
  const [items, setItems] = useState(layout || defaultLayout);
  
  return (
    <GridLayout
      className="layout"
      layout={items}
      onLayoutChange={onLayoutChange}
      cols={12}
      rowHeight={30}
      width={1200}
      isResizable
      isDraggable
    >
      {items.map(item => (
        <div key={item.i} className="grid-item">
          <Gauge pgn={...} spn={...} value={...} />
        </div>
      ))}
    </GridLayout>
  );
}
```

---

## Files to Create

```
dashboard/src/components/
├── cluster/
│   └── Cluster.tsx
└── ClusterLayoutPanel.tsx
```

---

## Exit Criteria

- [ ] Gauges render in grid
- [ ] Drag-drop works
- [ ] Resize works
- [ ] Save/load presets to localStorage
- [ ] Can add/remove gauges

---

Depends on: **feat/gauges** merged (Person A)
