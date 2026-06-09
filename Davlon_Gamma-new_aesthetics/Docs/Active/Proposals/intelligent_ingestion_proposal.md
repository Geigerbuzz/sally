---
title: Intelligent Ingestion & Deep Entity Extraction
status: draft
type: proposal
created: 2025-12-18
updated: 2025-12-28
tags: [ingestion, entities, extraction, cortex]
parent: null
children: []
related:
  - ./knowledge_graph_enrichment_proposal.md
  - ../../Implemented/Proposals/self_adapting_rag_proposal.md
---

# Proposal: Intelligent Ingestion & Deep Entity Extraction

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Universal Loader](#31-step-1-universal-loader) | ✅ Complete | 2025-12-20 | `ingestion.py:extract_text` |
| [Classifier Agent](#32-step-2-the-classifier-agent-the-gatekeeper) | ⬜ Pending | — | — |
| [Deep Entity Extraction](#33-step-3-deep-entity-extraction-the-miner) | ⬜ Pending | — | — |
| [Graph Reconciliation](#34-step-4-graph-reconciliation-the-merger) | ⬜ Pending | — | — |
| [Schema-First Learning (A)](#strategy-a-schema-first-ai-fallback-the-hybrid---recommended) | ✅ Complete | 2025-12-21 | `schema_learner.py` |

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md)  
> **Affects**: [Knowledge Graph Enrichment](./knowledge_graph_enrichment_proposal.md), [Adaptive Entity Intelligence](./adaptive_entity_intelligence_proposal.md)

---

## 1. Objective
To upgrade the Davlon ingestion pipeline from a simple format-based router (CSV=Listing, PDF=RAG) to a **Semantic, Content-Aware Intelligence System**. The system must ingest **any** file format (PDF, DOCX, XLSX, TXT, CSV), automatically classify its intent, and extract high-precision relationships (Graph Data) even from unstructured narrative text.

## 2. The Problem
Current logic is brittle:
- "If CSV -> Make Listing". (False Positive Risk: A CSV of lunch orders creates a listing).
- "If PDF -> Vectorize". (False Negative Risk: A PDF rent roll contains critical entity data that gets buried in vector chunks).
- "Memos are ignored". (Critical Missing Data: "Marta is retiring" is lost).

## 3. Proposed Architecture: The "Cortex" Pipeline

Input -> **[Universal Loader]** -> **[Classifier Agent]** -> **[Extraction Agent]** -> **[Graph Reconciliation]**

### 3.1 Step 1: Universal Loader
Regardless of extension, text is extracted.
- **Tools**: `pdfplumber` (PDF), `pandas` (Excel/CSV), `python-docx` (Word).
- **Output**: Pure Text + Metadata (Author, Date).

### 3.2 Step 2: The Classifier Agent (The "Gatekeeper")
**Goal**: Determine *what* this document is.
- **Input**: First 4k tokens of document.
- **Prompt**: "Classify this document into: [LISTING_DATA, CLIENT_DATA, INTERNAL_MEMO, IRRELEVANT]. Confidence Score required."
- **Logic**:
    - If `IRRELEVANT` (e.g., Brand Guidelines): Index for RAG only (Vector), do NOT attempt Graph Extraction.
    - If `LISTING_DATA`: Trigger Listing Extraction.
    - If `MEMO`: Trigger Relationship Extraction.

### 3.3 Step 3: Deep Entity Extraction (The "Miner")
This is the core requirement. We use a **Schema-Guided Extraction** approach.

**Scenario: The Memo**
> *Text*: "Tom is assigned to all properties on the coast."
**Extraction Prompt**:
> "Extract all entities and relationships fitting the schema: `(Person)-[ASSIGNED_TO]->(Region/Property)` or `(Person)-[STATUS_CHANGE]->(Role)`."
**Output (JSON)**:
```json
[
  {
    "source": "Tom",
    "type": "Person",
    "relationship": "MANAGES",
    "target": "Coastal Properties",
    "target_type": "Region"
  }
]
```

### 3.4 Step 4: Graph Reconciliation (The "Merger")
**Challenge**: The node "Tom" might already exist as "Tom H." or `tom@davlon.com`.
**Solution**: **Vector-Based Node Resolution**.
1.  System looks up "Tom" in the Graph Index.
2.  Finds candidate: `Tom Henderson (Agent)`.
3.  AI Confirmation: "Is 'Tom' in this context likely 'Tom Henderson'?" -> YES.
4.  **Action**: Create edge `(Tom Henderson)-[:MANAGES]->(Coastal Region Node)`.

## 4. Technical Stack

1.  **LLM**: Gemini 1.5 Pro (Large context window is key for full-doc analysis).
2.  **Graph**: Neo4j (already present).
3.  **Orchestration**: Python `backend/ingestion.py` (needs major refactor to be "Agentic" rather than procedural).
4.  **Parsers**:
    - `openpyxl` / `pandas` (Excel)
    - `python-docx` (Word)

## 5. Failure Modes & Reliability
- **Low Confidence**: If the Classifier is unsure (e.g., 40% Listing), it flags the document as `Needs Review` in the Inbox rather than polluting the database.
- **Conflict**: If extraction contradicts existing data (e.g., "Marta is retiring" vs Graph "Marta is Active"), it creates a `Contradiction Alert` in the Inbox.


## 6. Special Case: Barcelona Government Data (Hybrid & Adaptive Learning)
Since we must assume official documents are valid but anticipate hundreds of format variations, a rigid "Zero-Tolerance" system is too brittle. We need a system that *learns* new formats as they appear.

I propose a **Hybrid Strategy** that combines the speed of code with the flexibility of AI.

### Strategy A: "Schema-First, AI-Fallback" (The Hybrid - Recommended)
This approach prioritizes reliability but fails gracefully into "Learning Mode".

1.  **Phase 1: Deterministic Check (The Fast Path)**
    *   System checks if the CSV matches a known "Fingerprint" (e.g., rigid Pydantic models for `Carrec_tipus_propietari`).
    *   **If Match**: Fast, code-based ingestion.

2.  **Phase 2: AI-Driven "Header Harmonization" (The Learning Path)**
    *   **Trigger**: If the file *fails* the rigid check (e.g., "District_ID" instead of "Codi_districte").
    *   **Action**: The system sends the *new* headers + a **Representative Sample** (e.g., first 5-10 rows) to Gemini. (Sending the full file is unnecessary for schema inference and wastes tokens).
    *   **Prompt**: "These are the headers and sample data for a Barcelona Legal Doc. Map them to our Canonical Schema..."
    *   **Result**: Gemini returns a JSON Mapping (e.g., `{"District_ID": "district_code"}`).
    *   **Ingestion**: The system uses this inferred map to process the **Entire File** locally.

3.  **Phase 3: The Stickiness (Learning)**
    *   The system **saves this new mapping** to a database.
    *   Next time this simplified/altered format appears, it hits **Phase 1** (fingerprint match) and skips the AI cost.

### Strategy B: "The Universal Mapper" (Pure AI)
We treat *every* CSV as a unique entity.
*   **Logic**: Every single upload is passed to Gemini to extract a specific JSON structure, ignoring the original column names entirely.
*   **Pros**: Ultimate flexibility. Handles completely changed layouts.
*   **Cons**: Slower, higher cost per file.

### Strategy C: "Constraint Learning" (Trust but Verify)
We accept all data but ask Gemini to generate *Validation Rules* on the fly.
*   **Logic**: When a new file type arrives, Gemini analyzes it and writes a minimal Python validation script (e.g., "Column C must be numeric").
*   **Pros**: Ensures validity without rigid pre-coding.
*   **Cons**: Generating code at runtime adds security complexity.

**Recommendation**: **Strategy A**. It balances the rigidity you need for trusted data with the flexibility to handle "Official but Outlier" documents without manual code updates.

## 7. Implementation Stages
1.  **Universal Parser**: Build the `Loader` class for DOCX/XLSX.
2.  **Classification Prompts**: Test prompts to reliably distinguish a "Menu" from a "Client List".
3.  **Extraction Logic**: Build the JSON-structured extraction chain.
4.  **Legal Module**: Implement the "Similiar Contract" retrieval step.

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/ingestion.py` | Universal loader, classifier integration |
| `backend/graph_service.py` | Graph reconciliation, entity merging |
| `backend/schema_learner.py` | Schema-first learning |
