---
title: Knowledge Graph Enrichment Implementation
status: draft
type: proposal
created: 2025-12-27
updated: 2025-12-28
tags: [knowledge-graph, entities, neo4j, extraction]
parent: null
children: []
related:
  - ./advanced_rag_enhancements_proposal.md
  - ./adaptive_entity_intelligence_proposal.md
---

# Knowledge Graph Enrichment Implementation Proposal

**Date**: December 27, 2024  
**Status**: Draft  
**Source**: Category 2 from Advanced RAG Enhancements Proposal

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Entity Extraction from Text](#21-entity-extraction-from-text) | ⬜ Pending | — | — |
| [Relationship Discovery](#22-relationship-discovery) | ⬜ Pending | — | — |
| [Entity Resolution](#23-entity-resolution-deduplication) | ⬜ Pending | — | — |
| [Graph Summarization](#24-knowledge-graph-summarization) | 🔘 Deferred | — | — |

> **Depends on**: [Knowledge Graph Master](../../Implemented/Masters/knowledge_graph_master.md), [Ingestion Pipeline](../../Implemented/Masters/ingestion_pipeline_master.md)  
> **Affects**: [Adaptive Entity Intelligence](./adaptive_entity_intelligence_proposal.md), [Advanced RAG Enhancements](./advanced_rag_enhancements_proposal.md)

---

## Executive Summary

This proposal outlines how to implement **entity extraction from unstructured text** (PDFs, documents) while staying true to Davlon's core principles. Currently, entities are only extracted from structured CSVs via schema learning. The goal is to extend this to narrative text.

---

## Alignment with Core Philosophies

| Principle | How This Proposal Aligns |
|-----------|-------------------------|
| **Preemptive AI** | System suggests entity links for human approval—never auto-merges |
| **Zero-Hallucination** | Entities extracted with source provenance; questionable extractions flagged |
| **True GraphRAG** | All entities stored in Neo4j alongside chunks—no split stack |
| **Self-Adapting** | Uses learned schemas to guide extraction, not hardcoded types |

---

## Proposed Features

### 2.1 Entity Extraction from Text

**Current**: Entities created only from CSV columns.  
**Proposed**: Extract People, Organizations, Dates, Monetary values from PDF/DOCX text.

**Implementation Approach**:

```
Document Text → Gemini Extraction → Confidence Check → Graph Storage
                     ↓
              Low Confidence?
                     ↓
              Inbox: "I found 'Acme Corp' in this contract. 
                      Is this a client? [Yes] [No] [Ignore]"
```

**Why Gemini (not spaCy)?**
- Already in stack (no new dependencies)
- Better at domain-specific entities (company names, legal terms)
- Can be guided by learned Company Profile

**Schema-Guided Prompts**:
```python
prompt = f"""
The user's company is in {company_profile.industry}.
Extract entities from this text. Types to look for:
{company_profile.learned_entity_types}

Format: JSON array of {{type, name, confidence, source_quote}}
"""
```

**Confidence Threshold**:
- ≥0.8: Auto-create entity
- 0.5-0.8: Create but flag for review
- <0.5: Send to Inbox for approval

---

### 2.2 Relationship Discovery

**Current**: Relationships inferred from CSV column names (e.g., `doctor_id` → `HAS_DOCTOR`).  
**Proposed**: Extract relationships from narrative text patterns.

**Triggering Patterns** (via Gemini):
| Text Pattern | Relationship |
|--------------|--------------|
| "X reports to Y" | `(X)-[:REPORTS_TO]->(Y)` |
| "X signed with Y" | `(X)-[:SIGNED]->(Contract)-[:WITH]->(Y)` |
| "X is located in Y" | `(X)-[:LOCATED_IN]->(Y)` |

**Implementation**: Part of the same extraction pass as 2.1—no separate pipeline.

---

### 2.3 Entity Resolution (Deduplication)

**Current**: "John" and "John Smith" create separate nodes.  
**Proposed**: Embed entity names and find duplicates via cosine similarity.

**Algorithm**:
```cypher
// Find similar entities daily (scheduled job)
MATCH (a:Person), (b:Person)
WHERE a <> b 
  AND a.name_embedding IS NOT NULL 
  AND b.name_embedding IS NOT NULL
WITH a, b, gds.similarity.cosine(a.name_embedding, b.name_embedding) AS sim
WHERE sim > 0.85
RETURN a.name, b.name, sim
```

**Merge Policy**: 
- Never auto-merge
- Send to Inbox: *"Is 'J. Smith' the same as 'John Smith'?"*
- If confirmed, merge nodes with provenance trail

---

### 2.4 Knowledge Graph Summarization

**Status**: Deferred  
**Rationale**: Current graph size is manageable. Revisit when:
- Graph exceeds 100K nodes
- Query latency degrades
- Storage costs become significant

---

## Implementation Order

| Phase | Feature | Effort | Dependencies |
|-------|---------|--------|--------------|
| 1 | Entity Extraction (2.1) | 3 days | None |
| 2 | Relationship Discovery (2.2) | 2 days | Phase 1 |
| 3 | Entity Resolution (2.3) | 3 days | Phase 1 |
| 4 | Summarization (2.4) | Deferred | - |

---

## Technical Design

### New Files
- `backend/entity_extractor.py` — Gemini-based extraction with confidence scoring

### Modified Files
- `ingestion.py` — Call extraction after chunking
- `database.py` — Entity deduplication query
- `main.py` — Daily job for resolution

### Neo4j Schema Additions
```cypher
// Entity nodes with embeddings for resolution
CREATE CONSTRAINT entity_id IF NOT EXISTS 
  FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// Index for similarity search
CREATE VECTOR INDEX entity_embeddings IF NOT EXISTS
  FOR (e:Entity) ON e.name_embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
```

---

## Verification Plan

1. **Unit Test**: Extract entities from sample contract PDF
2. **Integration Test**: Verify entity appears in graph and links to source chunk
3. **Inbox Test**: Low-confidence extraction triggers notification
4. **Deduplication Test**: Similar names flagged for merge

---

## Decision Points

> [!IMPORTANT]  
> Before implementation, confirm:
> 1. Which entity types matter most for your use case? (People, Organizations, Dates, Money?)
> 2. Should low-confidence entities be created with a "pending" status, or only created after approval?
> 3. Is the daily deduplication job sufficient, or should it run on every upload?

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/ingestion.py` | Extraction trigger after chunking |
| `backend/database.py` | Deduplication queries |
| `backend/graph_service.py` | Entity node creation |
