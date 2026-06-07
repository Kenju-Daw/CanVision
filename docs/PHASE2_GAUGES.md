# Phase 2: Gauge Components (Person A)

## Deliverable
Build 6 reusable gauge components using D3.js + React.

## Components to Build

### 1. Tachometer
Arc gauge, 0–8000 RPM (J1939 engine speed).

**Props:**
```typescript
interface TachometerProps {
  value: number;           // Current RPM (0-8000)
  min?: number;            // Min (default 0)
  max?: number;            // Max (default 8000)
  warn?: number;           // Warn threshold (e.g. 7000)
  crit?: number;           // Critical threshold (e.g. 7500)
  unit?: string;           // "rpm" (display label)
}
```

**Visual:**
- Arc from 0° (bottom-left) to 270° (bottom-right)
- Color zones: green (0-6500), yellow (6500-7000), red (7000+)
- Needle rotates to value
- Center circle with large font: "5500 RPM"
- Labels at 0, 2000, 4000, 6000, 8000

---

### 2. Speedometer
Arc gauge, 0–250 km/h (J1939 vehicle speed).

**Props:**
```typescript
interface SpeedometerProps {
  value: number;           // Current speed (0-250)
  min?: number;            // Default 0
  max?: number;            // Default 250
  unit?: string;           // "km/h" or "mph"
}
```

**Visual:**
- Similar to tachometer but wider range
- Color: green (0-120), yellow (120-180), red (180+)
- Labels: 0, 50, 100, 150, 200, 250

---

### 3. Thermometer
Vertical or arc gauge, –40 to +120°C (engine coolant temp).

**Props:**
```typescript
interface ThermometerProps {
  value: number;           // Current temp (–40 to +120)
  unit?: string;           // "°C" or "°F"
  warn?: number;           // e.g. 100
  crit?: number;           // e.g. 110
}
```

**Visual:**
- Vertical arc from bottom (cold) to top (hot)
- Color: blue (–40 to 40), green (40-90), yellow (90-100), red (100+)
- Center: large font temperature value

---

### 4. BarGauge
Horizontal bar, 0–100% (fuel level, oil pressure % of max).

**Props:**
```typescript
interface BarGaugeProps {
  value: number;           // 0-100
  label?: string;          // "Fuel", "Brake Pressure"
  warn?: number;           // e.g. 20 (low fuel warning)
  crit?: number;           // e.g. 10 (critical)
}
```

**Visual:**
- Horizontal bar, left to right
- Background: light gray
- Fill: green (value > warn), yellow (value 10-20), red (value < crit)
- Percentage text inside: "75%"

---

### 5. NumericDisplay
Large number with unit (generic).

**Props:**
```typescript
interface NumericDisplayProps {
  value: number | null;    // -9999 to +9999
  unit: string;            // "L/h", "kPa", "h", etc
  label?: string;          // "Fuel Rate", "Oil Pressure"
  warn?: number;
  crit?: number;
  decimals?: number;       // Default 2
}
```

**Visual:**
- Large font (48px+)
- Value: bold, color changes with thresholds (green > yellow > red)
- Unit: smaller font (16px) below value
- Label: tiny font (12px) above

---

### 6. StatusLED
Simple on/off indicator (fault lamp, brake status).

**Props:**
```typescript
interface StatusLEDProps {
  active: boolean;         // true = on (red), false = off (gray)
  label?: string;          // "MIL", "Brake Applied"
  size?: "sm" | "md" | "lg";
}
```

**Visual:**
- Circle (sm: 20px, md: 40px, lg: 60px diameter)
- Off: dark gray (#6b7280)
- On: bright red (#ef4444) + optional blink animation

---

## Implementation Notes

### D3.js for Gauges
```typescript
// Use D3 v7.9
import * as d3 from 'd3';

// Arc generator for tachometer
const arc = d3.arc()
  .innerRadius(80)
  .outerRadius(100)
  .startAngle(angle1)
  .endAngle(angle2);

// Scale value to angle
const angleScale = d3.scaleLinear()
  .domain([0, 8000])  // RPM
  .range([0, 270 * Math.PI / 180]);  // 0-270°
```

### React Integration
```typescript
export function Tachometer({ value, warn, crit }: TachometerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 200, height: 200 });

  useEffect(() => {
    if (!svgRef.current) return;
    // Render D3 chart on svgRef.current
    // Update when `value` changes
  }, [value, warn, crit]);

  return <svg ref={svgRef} {...dimensions} />;
}
```

### Styling
- Tailwind CSS OK for borders, spacing
- D3 for SVG paths (arcs, needles)
- Inline styles for dynamic colors

---

## Test with Sample Data

```typescript
<Tachometer value={3500} min={0} max={8000} warn={7000} crit={7500} />
<Speedometer value={120} unit="km/h" />
<Thermometer value={85} warn={100} crit={110} />
<BarGauge value={75} label="Fuel" warn={20} />
<NumericDisplay value={11.2} unit="L/h" label="Fuel Rate" />
<StatusLED active={false} label="MIL" />
```

---

## Files to Create

```
dashboard/src/components/cluster/
├── Tachometer.tsx
├── Speedometer.tsx
├── Thermometer.tsx
├── BarGauge.tsx
├── NumericDisplay.tsx
├── StatusLED.tsx
└── index.ts  (export all)
```

---

## Exit Criteria

- [ ] All 6 components render without errors
- [ ] Can pass mock data and see responsive updates
- [ ] Colors match thresholds (warn/crit)
- [ ] Works in 200×200 and 400×400 viewports
- [ ] No console errors
- [ ] Unit tests (optional): value updates trigger re-render

---

## Dependencies

```json
{
  "d3": "^7.9.0",
  "react": "^18.3.1"
}
```

---

## Phase 2 Sequence

1. ✅ **Person A (you)** builds these 6 components (feat/gauges)
2. **Person B** waits for merge, then builds Cluster.tsx (feat/cluster-layout)
3. **Person C** builds DBC editor (feat/dbc-editor) — can work in parallel

---

Merge to `main` when done. Person B will use these in the Cluster grid!
