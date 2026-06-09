---
title: Multimodal Vision-First Ingestion
status: draft
type: proposal
created: 2025-12-18
updated: 2025-12-28
tags: [ingestion, vision, multimodal, pdf]
parent: null
children: []
related:
  - ./intelligent_ingestion_proposal.md
  - ./advanced_rag_enhancements_proposal.md
---

# Proposal: Multimodal "Vision-First" Ingestion (Zero Data Loss)

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Page Rendering](#the-new-pipeline) | ⬜ Pending | — | — |
| [Vision Extraction](#the-new-pipeline) | ⬜ Pending | — | — |
| [Chart/Table → Markdown](#3-why-this-wins) | ⬜ Pending | — | — |

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md)  
> **Affects**: [Advanced RAG Enhancements](./advanced_rag_enhancements_proposal.md#33-multi-modal-ingestion)

---

## 1. The Problem: "Text Blindness"
You correctly pointed out that `pypdf` (and standard OCR) is "blind" to:
*   **Charts**: It sees "Figure 1" but not the upward trend line.
*   **Tables**: It sees a jumble of words, losing the row/column logic.
*   **Images**: It ignores diagrams entirely.

If your "No Compromise" goal is true reliability, `pypdf` is insufficient.

## 2. The Solution: Vision-First Ingestion
Instead of trying to "scrape" text code from the file, we treat the document **as an image**—exactly how a human reads it.

### The New Pipeline
1.  **Render ("The Screenshot")**:
    *   Convert every page of the PDF into a high-resolution Image (PNG).
2.  **Vision Extraction ("The Describer")**:
    *   Send each page image to **Gemini 2.5 Flash (Vision)**.
    *   *Prompt*: "Transcribe this page into detailed Markdown. If there is a chart, describe the data points and trends. If there is a table, convert it to a Markdown table."
3.  **Embedding ("The Index")**:
    *   Embed this *rich textual description* using `gemini-embedding-001`.
4.  **Storage**:
    *   Save the Vector in Neo4j.
    *   Save the *Original Page Image* reference (so we can show it to the user later).

## 3. Why This Wins
*   **Charts become Searchable**: "Revenue trend" matches the *description* of the blue line going up.
*   **Tables become Structural**: The AI converts visual grids into readable Markdown tables.
*   **Context**: Layout headers and sidebars are understood correctly.

## 4. Implementation Cost
*   **Slower Ingestion**: Processing a 50-page PDF takes ~20 seconds (vs 1s with `pypdf`).
*   **Higher Cost**: We pay for Vision tokens for every page.
*   **Verdict**: Worth it for "True RAG".

## 5. Alternative: "Unstructured.io" or "LlamaParse"
There are paid tools (LlamaParse) that do this "complex extraction".
*   **Pros**: Pre-built.
*   **Cons**: Another vendor, data privacy risk, cost.
*   **My Recommendation**: Build our own "Vision-First" pipeline using Gemini. We already have the best Vision model (Flash) in our stack. Why pay someone else?

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/ingestion.py` | Page rendering, vision extraction |
| `backend/rag.py` | Embedding rich descriptions |
