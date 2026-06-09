---
title: Templated AI Widget Generation - Technical Implementation
status: draft
type: proposal
created: 2025-12-18
updated: 2025-12-28
tags: [widgets, ai, implementation, technical]
parent: ./widget_generation_proposal.md
children: []
related:
  - ./widget_types_and_visualization_proposal.md
  - ./widget_implementation_checklist.md
---

# Technical Proposal: Templated AI Widget Generation

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [WidgetPayload Schema](#2-data-models-the-contract) | ✅ Complete | 2025-12-18 | `main.py` |
| [Backend Validation](#3-backend-implementation-pythonfastapi) | ✅ Complete | 2025-12-18 | `main.py:generate_widget` |
| [WidgetRenderer Component](#4-frontend-implementation) | ✅ Complete | 2025-12-18 | `widget_templates.js` |
| [Theme-Aware Templates](#template-library) | ⬜ Pending | — | — |

> **Depends on**: [Widget Generation Proposal](./widget_generation_proposal.md)  
> **Affects**: [Widget Checklist](./widget_implementation_checklist.md)

---

## Executive Summary
This document outlines the technical implementation for a reliable AI widget generation system as proposed in [widget_generation_proposal.md](./widget_generation_proposal.md). The core strategy shifts from generating raw code to a **Template-Based Data Injection** model. The AI selects a pre-built, robust UI template and populates it with structured JSON data.

## 1. System Architecture

### High-Level Flow
1.  **User Prompt**: "Show me sales by region for Q3."
2.  **Backend Agent**:
    -   Analyzes prompt.
    -   Selects best template (e.g., `BarChart`).
    -   Extracts data and formats it into `WidgetPayload` JSON.
    -   Validates JSON against strict Zod schema.
3.  **Frontend**:
    -   Receives `WidgetPayload`.
    -   `WidgetRenderer` component dynamically loads the correct template.
    -   Injects data into the safe, pre-styled component.

## 2. Data Models (The Contract)

We will use strict TypeScript/Zod definitions to ensure the AI cannot break the frontend.

### Core Types

```typescript
type TemplateType = 'kpi-card' | 'bar-chart' | 'line-chart' | 'data-table';

interface BaseWidget {
  id: string;
  title: string;
  template: TemplateType;
}

// Specific Payload Schemas
interface KPIPayload extends BaseWidget {
  template: 'kpi-card';
  data: {
    value: string; // e.g., "$120k"
    trend?: 'up' | 'down' | 'neutral';
    trendValue?: string; // e.g., "+12%"
    subtitle?: string;
  };
}

interface ChartPayload extends BaseWidget {
  template: 'bar-chart' | 'line-chart';
  data: {
    labels: string[]; // X-Axis
    datasets: {
      label: string;
      values: number[]; // Y-Axis
      color?: string; // Optional hex override
    }[];
  };
}

export type WidgetPayload = KPIPayload | ChartPayload; // Union type
```

## 3. Backend Implementation (Python/FastAPI)

The backend's primary job is **Schema Enforcement**.

### AI Prompt Strategy
We will not ask for code. We will ask for JSON.
**System Prompt:**
> You are a data extraction engine. You have access to the following schemas: [Schema Definitions].
> Analyze the user request.
> 1. Select the most appropriate template.
> 2. Transform the data into the matching JSON structure.
> 3. Return ONLY the JSON.

### Validation Layer
We can use a library like `instructor` (for Pydantic) or manual schema validation to guarantee the AI output is valid before sending it to the client.

## 4. Frontend Implementation

### The `WidgetRenderer` Component
A central dispatcher that takes the JSON and renders the correct component.

```javascript
// Pseudo-code
function WidgetRenderer({ widget }) {
  switch (widget.template) {
    case 'kpi-card':
      return <KPICard data={widget.data} title={widget.title} />;
    case 'bar-chart':
      return <BarChart data={widget.data} title={widget.title} />;
    default:
      return <ErrorWidget message="Unknown template" />;
  }
}
```

### Template Library
We currently need to build these "Gold Standard" templates in `public/components`. They must be:
-   **Responsive**: Work on mobile/desktop.
-   **Theme-Aware**: Support Light/Dark mode automatically.
-   **Error-Proof**: Handle missing optional data gracefully.

## 5. Development Roadmap

1.  **Phase 1: Template Library**: Build the HTML/CSS/JS for `KPICard`, `Chart`, and `Table` using Chart.js or similar for the graphs.
2.  **Phase 2: Backend Agent**: Create the endpoint `/api/generate-widget` that accepts a prompt and returns the `WidgetPayload`.
3.  **Phase 3: Integration**: specific "Add Widget" button that connects the two.

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| ⬆️ Parent | [Widget Generation Proposal](./widget_generation_proposal.md) | Original concept and philosophy |
| 🔗 Related | [Widget Types & Visualization](./widget_types_and_visualization_proposal.md) | Widget taxonomy and standards |
| 🔗 Related | [Widget Implementation Checklist](./widget_implementation_checklist.md) | Consolidated implementation tasks |

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `public/widget_templates.js` | WidgetRenderer, template components |
| `backend/main.py` | Backend validation, schema enforcement |
