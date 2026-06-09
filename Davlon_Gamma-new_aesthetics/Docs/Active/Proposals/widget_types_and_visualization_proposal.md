---
title: Widget Types & Visualization Standards
status: draft
type: proposal
created: 2025-12-18
updated: 2025-12-28
tags: [widgets, visualization, design-system]
parent: null
children: []
related:
  - ./widget_generation_proposal.md
  - ./widget_customization_implementation.md
  - ./widget_implementation_checklist.md
---

# Proposal: Widget Types & Visualization Standards

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Widget Taxonomy](#1-widget-taxonomy--visualization-matrix) | ✅ Complete | 2025-12-18 | `widget_templates.js` |
| [Size Immutability](#a-size-immutability) | ✅ Complete | 2025-12-18 | `style.css` |
| [Title Truncation](#b-title-safety--truncation) | ✅ Complete | 2025-12-18 | `style.css` |
| [Color Palette CSS Vars](#c-color-palette-restrictions) | 🔄 In Progress | — | `style.css` |
| [Data Reactivity](#3-data-freshness--reactivity) | ⬜ Pending | — | — |

> **Depends on**: [Widget System Master](../../Implemented/Masters/widget_system_master.md), [UI System Master](../../Implemented/Masters/ui_system_master.md)  
> **Affects**: [Widget Generation](./widget_generation_proposal.md), [Widget Checklist](./widget_implementation_checklist.md)

---

## Objective
To simplify the widget generation process by defining a standard set of data types and their corresponding optimal visualizations and dimensions. This standardization ensures consistency and predictable UI behavior while leveraging AI for complex or edge cases.

## 1. Widget Taxonomy & Visualization Matrix

We classify user requests into distinct "Media Types" based on the data structure.

| Media Type | Description | Optimal Visualization | Default Dimension |
| :--- | :--- | :--- | :--- |
| **KPI (Metric)** | Single numeric value, potentially with a trend or comparison. | **Big Number Card**<br>With optional trend indicator (↑/↓) and sparkline. | **1x1** (Small Square) |
| **Time Series** | Quantitative data points plotted over a continuous time interval. | **Line Chart** (for trends)<br>**Bar Chart** (for discrete periods). | **2x1** (Wide Rectangle) |
| **Categorical** | Comparison of values across distinct categories (e.g., Revenue by City). | **Horizontal Bar Chart** (best for readability)<br>**Doughnut Chart** (for < 5 items). | **1x2** (Tall) or **2x2** |
| **List / Records** | A set of individual items with metadata (e.g., Recent Transactions, Top Agents). | **Simple Table** or **List View**<br>With status badges or avatars. | **2x2** (Large Square) |
| **Progress** | A value relative to a defined target or capacity. | **Radial Gauge** or **Linear Progress Bar**. | **1x1** (Small Square) |
| **Comparison** | Two specific values being compared directly (e.g., This Year vs Last Year). | **Dual Stat Card** or **Butterfly Chart**. | **2x1** (Wide Rectangle) |

## 2. Immutable Rules (The "Iron Laws")

> [!IMPORTANT]
> The AI is FORBIDDEN from altering these constraints.

### A. Size Immutability
Widget dimensions are **CONSTANTS**. They never change based on content volume.
-   **1x1**: `160px x 160px`
-   **2x1**: `344px x 160px`
-   **1x2**: `160px x 344px`
-   **2x2**: `344px x 344px`

**Overflow Behavior**: If content exceeds the fixed box, it must:
1.  **Text**: Truncate with ellipsis (`...`).
2.  **Lists**: Activate an internal scrollbar `overflow-y: auto`.
3.  **Charts**: Simplify labels or reduce density.

### B. Title Safety & Truncation
-   **Max Length**: Titles are capped at 1 line.
-   **CSS Enforcement**: `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;`
-   **AI Instruction**: "Generate short, punchy titles (max 25 chars preferred). If the title is 'Total Revenue for the Fiscal Year 2024', rename it to 'FY24 Revenue'."

### C. Color Palette Restrictions
The AI may ONLY use the following CSS variables defined in the project. Hex codes are **forbidden**.

-   **Backgrounds**: `var(--bg-body)`, `var(--bg-surface)`
-   **Text**: `var(--text-primary)`, `var(--text-secondary)`
-   **Brand Primary**: `var(--accent)` (Blue)
-   **Functional**: `var(--accent-warning)` (Yellow/Orange - *implied*)
-   **Borders**: `var(--dock-border)`

*Constraint*: If a chart needs multiple colors (e.g., a pie chart), use opacity variations of `var(--accent)` or strictly defined secondary palette variables (to be added to CSS if missing).

## 3. Data Freshness & Reactivity

Widgets are **Live Views**, not static screenshots.

-   **Trigger**: A widget subscribes to a specific data source or "Topic" (e.g., `ingestion/documents`, `sales/Q3`).
-   **Update Flow**:
    1.  User adds a new PDF document.
    2.  `IngestionPipeline` emits a `data_updated` event for the `documents` topic.
    3.  All widgets subscribed to `documents` re-fetch their JSON payload.
    4.  The Frontend re-renders the widget with new values without layout shifts.

## 4. The AI "Wildcard" Strategy

For any request that does not cleanly fit into the above categories, or involves complex, multi-dimensional analysis (e.g., "Show me the correlation between rain and sales over 5 years overlaid with marketing spend"), we default to **AI Autonomy**.

**Rule:**
> "If the data structure is ambiguous or complex, the AI is authorized to construct a custom visualization payload, selecting the dimensions and chart type it deems most effective."

This ensures the rigid standards handle 90% of cases efficiently, while not blocking the 10% of creative/complex user requests.

## 5. Open Questions & Decisions

> [!QUESTION]
> **Chart Color Palette**: We currently only have one primary accent color (`--accent`). To support multi-category charts (like Pie/Doughnut), do we want to:
> A. Add more semantic colors (Red, Green, Purple) to the global CSS?
> B. Use monochromatic shades of the single Blue accent?

> [!QUESTION]
> **Refresh Rate**: For "Live" sources that don't have push events, what is the acceptable polling interval? (e.g., Every 30s? Every 5 mins?)

> [!QUESTION]
> **Mobile Layout**: The 160px grid is optimized for desktop. On mobile, do we reflow to a single column (100% width) or keep the grid scaling down?

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| 🔗 Related | [Widget Generation Proposal](./widget_generation_proposal.md) | AI-powered widget generation concept |
| 🔗 Related | [Widget Customization Implementation](./widget_customization_implementation.md) | Technical implementation details |
| 🔗 Related | [Widget Implementation Checklist](./widget_implementation_checklist.md) | Consolidated implementation tasks |

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `public/style.css` | Size constraints, color palette, CSS vars |
| `public/widget_templates.js` | Template taxonomy, dimensions |
