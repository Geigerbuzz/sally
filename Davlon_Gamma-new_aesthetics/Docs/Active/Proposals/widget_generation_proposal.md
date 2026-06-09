---
title: Reliable AI Widget Generation
status: draft
type: proposal
created: 2025-12-18
updated: 2025-12-28
tags: [widgets, ai, generation]
parent: null
children:
  - ./widget_customization_implementation.md
related:
  - ./widget_types_and_visualization_proposal.md
  - ./widget_implementation_checklist.md
  - ./b2b_widget_expansion.md
  - ./shock_ideas.md
---

# Proposal: Reliable AI Widget Generation

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [JSON Schema Contract](#4-templated-generation-the-golden-path) | ✅ Complete | 2025-12-18 | `widget_templates.js` |
| [Validation Loop](#2-the-validation--self-healing-loop-the-black-box) | ⬜ Pending | — | — |
| [Pre-Flight Simulation](#3-pre-flight-simulation-the-test-drive) | ⬜ Pending | — | — |
| [Template Library](#how-it-works) | ✅ Complete | 2025-12-20 | `widget_templates.js` |

> **Depends on**: [Widget System Master](../../Implemented/Masters/widget_system_master.md)  
> **Affects**: [Widget Customization](./widget_customization_implementation.md), [Widget Checklist](./widget_implementation_checklist.md)

---

## Objective
Enable users to generate fully functional, Davlon-compatible widgets using natural language prompts. 
**Prime Directive**: The widgets MUST work on the first try. Speed and cost are irrelevant variables. Reliability is the only metric.

## Core Philosophy: "Zero Tolerance for Failure"
Because the end-user is not tech-savvy, they cannot debug "hallucinated" code. The system must guarantee execution correctness before the user ever sees the widget.

## Technology Stack (High-Fidelity)
- **AI Model**: Google Gemini 1.5 Pro / Ultra or GPT-4o. (Highest reasoning tiers only).
- **Validation**: Recursive Self-Correction Loop with Zod Schemas.
- **Simulation Environment**: Headless Browser Sandboxing for Pre-Flight Checks.

## Architecture Pipeline: The "Ironclad" Workflow

### 1. The Prompt Engineering Layer (Strict Schema)
We will not request loose code. We request a rigid JSON contract.
**System Prompt:**
> "You are a mission-critical code generator. You must adhere to the Davlon Design System strictly. If you are unsure, do not guess."

### 2. The Validation & Self-Healing Loop (The "Black Box")
Before the user sees anything, the backend performs a robust verification cycle:
1.  **Schema Check**: Does the JSON match the strict `WidgetPayload` interface?
2.  **Linting**: Run a linter on the generated inner HTML/CSS to catch syntax errors.
3.  **Self-Correction**: If any check fails, feed the error *back* into the AI: *"You made a syntax error on line 4. Fix it."*
    *   *Repeat this loop up to 5 times if necessary.*
4.  **Dependency Check**: Verify that no uninstalled libraries or fonts are referenced.

### 3. Pre-Flight Simulation (The "Test Drive")
*Optional but recommended for 100% reliability:*
Spin up a headless browser instance on the server, inject the widget, and check for:
- Console Errors.
- Layout Shifts (CLS).
- Rendering Failures.
Only if the widget renders cleanly in the sandbox is it sent to the frontend.

## 4. Templated Generation (The "Golden Path")
*Proposal Update (Dec 2025)*: Instead of asking the AI to write raw HTML/CSS from scratch (risky), we should provide a library of **Rigid Templates**.

### How it works
1.  **Template Library**: We pre-code robust, responsive widgets for common patterns:
    -   `BarChartTuple`: X-Axis, Y-Axis, Title.
    -   `KPICard`: Label, Value, Trend, Icon.
    -   `ListTable`: Columns, Rows.
2.  **AI Task**: To generate a "Sales Widget", the AI **selects a template** and **fills the JSON data**.
    -   *Input*: "Show me sales by region."
    -   *AI Output*: `{"template": "BarChart", "data": { "labels": ["North", "South"], "values": [120, 90] }}`.
3.  **Frontend Render**: The frontend takes this JSON and renders it using the pre-tested `BarChart` component.

### Benefits
-   **Zero Hallucination Risk**: The AI cannot break the CSS layout because it doesn't touch the CSS.
-   **Consistency**: All widgets look like they belong to the Davlon Design System.
-   **Speed**: Generating JSON is faster and cheaper than generating entire DOM structures.

## 5. Next Steps
1.  Define the `WidgetJSON` Schema (Zod).
2.  Build the Template Library (HTML/CSS components).
3.  Implement the JSON-filling Agent.

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| ⬇️ Child | [Widget Customization Implementation](./widget_customization_implementation.md) | Technical implementation details |
| 🔗 Related | [Widget Types & Visualization](./widget_types_and_visualization_proposal.md) | Widget taxonomy and standards |
| 🔗 Related | [Widget Implementation Checklist](./widget_implementation_checklist.md) | Consolidated implementation tasks |
| 🔗 Related | [B2B Widget Expansion](./b2b_widget_expansion.md) | Enterprise widget features |
| 🔗 Related | [Shock Ideas](./shock_ideas.md) | Wow-factor features |

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `public/widget_templates.js` | Template library, schema |
| `backend/main.py` | `/api/generate-widget` endpoint |
