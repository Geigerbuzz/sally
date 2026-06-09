---
title: Widget System Master
status: implemented
type: master
created: 2025-12-28
updated: 2025-12-28
tags: [widgets, dashboard, frontend, ui]
consolidates:
  - Active/Proposals/widget_generation_proposal.md
  - Active/Proposals/widget_customization_implementation.md
  - Active/Proposals/widget_types_and_visualization_proposal.md
---

# Widget System Master

The visual dashboard layer of Davlon. Implements drag-and-drop widgets with AI-powered generation, template enforcement, and rich visual effects.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        WIDGET SYSTEM                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  FRONTEND (public/)                                                   │
│  ├── widgets.js         # Drag-drop engine, collision detection      │
│  ├── widget_templates.js # Template renderer (KPI, Chart, Table)     │
│  └── index.html         # Dashboard canvas with grid                 │
│                                                                       │
│  BACKEND (backend/)                                                   │
│  ├── main.py            # /api/generate-widget endpoint              │
│  └── rag.py             # RAG context for data-driven widgets        │
│                                                                       │
│  RENDERING                                                            │
│  ├── Template Selection   # AI picks kpi-card, bar-chart, etc.       │
│  ├── JSON Payload         # Strict schema, no raw HTML               │
│  └── Chart.js             # Charts rendered via retained library     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Key Files

| File | Size | Purpose |
|------|------|---------|
| [widgets.js](file:///Users/dora/Documents/Davlon_Gamma/public/widgets.js) | 50KB | Drag-drop, collision, persistence |
| [widget_templates.js](file:///Users/dora/Documents/Davlon_Gamma/public/widget_templates.js) | 8KB | Template renderer class |
| [index.html](file:///Users/dora/Documents/Davlon_Gamma/public/index.html) | 9KB | Dashboard canvas |
| [main.py](file:///Users/dora/Documents/Davlon_Gamma/backend/main.py) | 29KB | `/api/generate-widget` endpoint |

---

## Implemented Features

### 1. Template Library
**Status**: ✅ Complete  
**Code**: `widget_templates.js:WidgetRenderer`

| Template | Size | Use Case |
|----------|------|----------|
| `kpi-card` | 1x1 | Single metric with trend |
| `bar-chart` | 2x1 | Categorical comparisons |
| `line-chart` | 2x1 | Time series data |
| `data-table` | 2x2 | Tabular records |

---

### 2. Drag and Drop
**Status**: ✅ Complete  
**Code**: `widgets.js` (lines 360-500)

- Unified mouse + touch support
- Ghost preview showing drop target
- Smooth FLIP animations
- Grid snapping to columns

---

### 3. Collision Detection
**Status**: ✅ Complete  
**Code**: `widgets.js:finalizeDrop()`

When widgets overlap:
1. Detect occupied cells
2. Push conflicting widgets down
3. Re-arrange grid without overlap

---

### 4. AI Widget Generation
**Status**: ✅ Complete  
**Code**: `main.py:/api/generate-widget`

Flow:
1. User provides natural language prompt
2. Backend queries RAG for relevant data
3. AI generates JSON payload (template + data)
4. Frontend renders via WidgetRenderer

---

### 5. Widget Persistence
**Status**: ✅ Complete  
**Code**: `widgets.js:saveUserWidget()`

- Widgets saved to `localStorage` under `davlon_user_widgets`
- Restored on page load
- Per-tab state (Team/Personal/Environment)

---

### 6. Visual Effects
**Status**: ✅ Complete

| Effect | Code | Description |
|--------|------|-------------|
| Confetti | `triggerConfetti()` | On new widget creation |
| Shine | `initShineEffect()` | Mouse-following border glow |
| FLIP Animation | `animateGridChange()` | Smooth position transitions |
| Grid Pegs | `drawPegs()` | Visual snap guides |

---

### 7. Tab System
**Status**: ✅ Complete  
**Code**: `widgets.js:switchTab()`

Three dashboard tabs:
- **Team** — Shared widgets
- **Personal** — User's private widgets
- **Environment** — ESG metrics widgets

---

## Widget Payload Schema

```typescript
interface WidgetPayload {
  id: string;           // Unique identifier
  title: string;        // Display title
  template: 'kpi-card' | 'bar-chart' | 'line-chart' | 'data-table';
  dimension?: '1x1' | '2x1' | '1x2' | '2x2';  // Grid size
  data: KPIData | ChartData | TableData;
}

interface KPIData {
  value: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: string;  // Remix Icon class
}

interface ChartData {
  labels: string[];
  datasets: { label: string; values: number[]; color?: string; }[];
}

interface TableData {
  headers: string[];
  rows: string[][];
}
```

---

## CSS Classes

| Class | Size | Pixels |
|-------|------|--------|
| `w-1x1` | Small square | 160×160 |
| `w-2x1` | Wide rectangle | 344×160 |
| `w-1x2` | Tall rectangle | 160×344 |
| `w-2x2` | Large square | 344×344 |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/generate-widget` | POST | AI widget generation |
| `/api/widget-data` | GET | Live data for widgets |

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| 📋 Proposal | [Widget Generation](../../Active/Proposals/widget_generation_proposal.md) | Original concept |
| 📋 Proposal | [Widget Customization](../../Active/Proposals/widget_customization_implementation.md) | Technical implementation |
| 📋 Proposal | [Widget Types](../../Active/Proposals/widget_types_and_visualization_proposal.md) | Taxonomy and standards |
| 📋 Proposal | [B2B Widget Expansion](../../Active/Proposals/b2b_widget_expansion.md) | Enterprise features |
| 📋 Checklist | [Widget Implementation Checklist](../../Active/Proposals/widget_implementation_checklist.md) | Remaining work |
