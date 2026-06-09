---
title: Advanced RAG & Data Pipeline Enhancements
status: draft
type: proposal
created: 2025-12-21
updated: 2025-12-28
tags: [rag, pipeline, neo4j, retrieval]
parent: null
children: []
related:
  - ./rag_retrieval_improvements_proposal.md
  - ./confidence_calibrated_retrieval_proposal.md
  - ../../Implemented/Proposals/self_adapting_rag_proposal.md
  - ./knowledge_graph_enrichment_proposal.md
  - ../Specs/Master_Data_Pipeline.md
---

# Advanced RAG & Data Pipeline Enhancements

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Hybrid Search with Graph](#11-hybrid-search-with-graph-traversal) | ✅ Complete | 2025-12-21 | `database.py:hybrid_graph_search` |
| [Temporal-Aware Retrieval](#13-temporal-aware-retrieval) | ✅ Complete | 2025-12-21 | `database.py:TEMPORAL_DECAY` |
| [Confidence-Calibrated Retrieval](#14-confidence-calibrated-retrieval) | ⬜ Pending | — | — |
| [Entity Extraction (NER)](#21-automatic-entity-extraction-ner) | ⬜ Pending | — | — |
| [Relationship Discovery](#22-relationship-discovery-from-text) | ⬜ Pending | — | — |
| [Entity Resolution](#23-entity-resolution--deduplication) | ⬜ Pending | — | — |
| [Delta Ingestion](#31-incremental-updates-delta-ingestion) | ⬜ Pending | — | — |
| [Streaming Ingestion](#32-streaming-ingestion) | ⬜ Pending | — | — |
| [Multi-Modal Ingestion](#33-multi-modal-ingestion) | ⬜ Pending | — | — |
| [Query Decomposition](#41-agentic-query-decomposition) | ⬜ Pending | — | — |
| [Conversational Memory](#42-conversational-memory) | ⬜ Pending | — | — |
| [Proactive Insights](#43-proactive-insights) | ⬜ Pending | — | — |
| [Citation Enhancement](#44-citation-enhancement) | ✅ Complete | 2025-12-21 | `rag.py:format_citations` |
| [Document Access Control](#71-document-level-access-control) | ⬜ Pending | — | — |

> **Depends on**: [RAG Retrieval Improvements](./rag_retrieval_improvements_proposal.md), [Knowledge Graph Master](../../Implemented/Masters/knowledge_graph_master.md)  
> **Affects**: [Self-Adapting RAG](../../Implemented/Proposals/self_adapting_rag_proposal.md), [Entity Intelligence](./adaptive_entity_intelligence_proposal.md)

---

## Overview

This document outlines potential upgrades and optional features that can be added to the self-adapting RAG system and data pipeline. All proposals are designed to work with **Neo4j Aura** as the storage backend.

---

## Category 1: Advanced Retrieval Enhancements

### 1.1 Hybrid Search with Graph Traversal

**Current State**: Vector search finds semantically similar chunks.

**Proposed Enhancement**: Combine vector similarity with graph relationships for more precise retrieval.

**How It Works**:
1. Vector search returns top 20 candidate chunks
2. Graph traversal expands to neighboring nodes (entities, documents, categories)
3. Re-ranking based on structural relevance

**Example**:
> User asks: "What contracts does John manage?"
> - Vector finds chunks mentioning "contracts" and "management"
> - Graph traverses: `(John:Person)-[:MANAGES]->(Contract)` relationships
> - Result combines semantic + structural relevance

**Neo4j Aura Compatibility**: ✅ Uses native vector index + Cypher traversal

**Effort**: Medium (2-3 days)

---

### ~~1.2 Multi-Hop Reasoning~~ → [DISCARDED](discarded_features.md)

---

### 1.3 Temporal-Aware Retrieval

**Current State**: All chunks treated equally regardless of document age.

**Proposed Enhancement**: Time-weighted retrieval that prioritizes recent data while still allowing historical queries.

**Features**:
- Automatic `uploadedAt` timestamp indexing
- Query modifiers: "latest", "from Q3 2024", "historical trend"
- Decay factor for older documents in default searches
- "Legacy" vs "Active" document classification

**Example Queries**:
- "What is the current policy?" → Prioritizes recent documents
- "How has the policy changed over time?" → Chronological retrieval

**Neo4j Aura Compatibility**: ✅ Datetime functions + sorted queries

**Effort**: Low (1-2 days)

---

### 1.4 Confidence-Calibrated Retrieval

**Current State**: Fixed top-K retrieval (always returns 5 chunks).

**Proposed Enhancement**: Dynamic retrieval based on confidence thresholds.

**How It Works**:
- Retrieve until cumulative confidence exceeds threshold
- Stop early if first chunk is extremely relevant
- Expand search if initial results are borderline

**Benefits**:
- Faster responses for easy questions
- More thorough retrieval for ambiguous queries
- Reduced hallucination risk

**Effort**: Low (1-2 days)

---

## Category 2: Knowledge Graph Enrichment

### 2.1 Automatic Entity Extraction (NER)

**Current State**: Entities created only from structured CSV data.

**Proposed Enhancement**: Extract entities from unstructured text (PDFs, documents).

**How It Works**:
1. Run Named Entity Recognition on ingested text
2. Extract: People, Organizations, Locations, Dates, Monetary values
3. Create graph nodes and relationships automatically

**Example**:
> Document text: "Alice signed a $500K contract with Acme Corp on March 15."
> Creates:
> - `(:Person {name: "Alice"})`
> - `(:Organization {name: "Acme Corp"})`  
> - `(:Contract {value: 500000, date: "2024-03-15"})`
> - Relationships: `(Alice)-[:SIGNED]->(Contract)-[:WITH]->(Acme Corp)`

**Implementation Options**:
- Gemini-based extraction (current stack)
- spaCy NER (cost-effective)
- Hybrid: spaCy base + Gemini refinement

**Neo4j Aura Compatibility**: ✅ Standard node/relationship creation

**Effort**: Medium (3-4 days)

---

### 2.2 Relationship Discovery from Text

**Current State**: Relationships inferred from CSV column hints only.

**Proposed Enhancement**: Extract relationships from narrative text.

**Example Patterns**:
- "X reports to Y" → `(X)-[:REPORTS_TO]->(Y)`
- "X purchased Y" → `(X)-[:PURCHASED]->(Y)`
- "X is located in Y" → `(X)-[:LOCATED_IN]->(Y)`

**Implementation**:
```
Prompt: "Extract all relationships from this text. Format: (Entity1, RELATIONSHIP, Entity2)"
```

**Effort**: Medium (2-3 days)

---

### 2.3 Entity Resolution & Deduplication

**Current State**: "John" and "John Smith" and "J. Smith" create separate nodes.

**Proposed Enhancement**: Intelligent entity merging.

**How It Works**:
1. Embed entity names/descriptions
2. Find similar entities via vector similarity
3. AI confirmation: "Is 'John' the same as 'John Smith'?"
4. Merge nodes if confirmed

**Neo4j Aura Query**:
```cypher
MATCH (a:Person), (b:Person)
WHERE a <> b AND a.embedding IS NOT NULL AND b.embedding IS NOT NULL
WITH a, b, gds.similarity.cosine(a.embedding, b.embedding) AS sim
WHERE sim > 0.85
RETURN a.name, b.name, sim
ORDER BY sim DESC
```

**Effort**: Medium (3-4 days)

---

### 2.4 Knowledge Graph Summarization

**Current State**: Graph grows indefinitely.

**Proposed Enhancement**: Periodic summarization/consolidation.

**Features**:
- Compress old nodes into summary nodes
- Archive detailed data while preserving queryable summaries
- "Q1 2024 Sales Summary" node instead of 10,000 individual transactions

**Benefits**:
- Faster queries
- Reduced storage costs
- Maintains historical insights

**Effort**: High (1 week)

---

## Category 3: Ingestion Pipeline Upgrades

### 3.1 Incremental Updates (Delta Ingestion)

**Current State**: Full document re-ingestion on updates.

**Proposed Enhancement**: Only process changed sections.

**How It Works**:
1. Hash each chunk on ingestion
2. On re-upload, compare hashes
3. Only re-embed and update changed chunks

**Benefits**:
- 10x faster re-ingestion
- Lower Gemini API costs
- Preserves chunk IDs for citation stability

**Effort**: Medium (2-3 days)

---

### 3.2 Streaming Ingestion

**Current State**: Synchronous, blocking ingestion.

**Proposed Enhancement**: Background processing with progress tracking.

**Features**:
- Upload returns immediately with job ID
- WebSocket updates for progress
- Retry logic for failed chunks
- Batch processing for large uploads

**Architecture**:
```
Upload → Queue (Redis/In-Memory) → Workers → Neo4j
           ↓
      WebSocket: "35% complete..."
```

**Effort**: Medium (3-4 days)

---

### 3.3 Multi-Modal Ingestion

**Current State**: Text extraction from documents.

**Proposed Enhancement**: Full vision-first processing.

**Capabilities**:
- **Charts/Graphs**: Describe trends, extract data points
- **Tables**: Convert to structured data (not just markdown)
- **Diagrams/Flowcharts**: Extract relationships
- **Images**: Generate searchable descriptions
- **Handwritten Notes**: OCR + interpretation

**Implementation**:
Use Gemini 2.5 Flash vision capabilities for each page/image.

**Effort**: High (1 week)

---

### 3.4 Real-Time Data Connectors

**Current State**: Manual file uploads only.

**Proposed Enhancement**: Live data source integrations.

**Connectors**:
| Source | Type | Use Case |
|--------|------|----------|
| Google Drive | Sync | Automatic ingestion of new docs |
| Salesforce | API | CRM data as graph entities |
| Notion | API | Internal docs and wikis |
| Slack | Webhook | Important messages/decisions |
| Email (IMAP) | Polling | Customer communications |
| Databases | CDC | Real-time data changes |

**Architecture**:
```
External Source → Connector → Normalize → Ingestion Pipeline → Neo4j
```

**Effort**: High per connector (3-5 days each)

---

## Category 4: Query & Response Enhancements

### 4.1 Agentic Query Decomposition

**Current State**: Single-shot query processing.

**Proposed Enhancement**: Agent that breaks down complex queries.

**Capabilities**:
- Identify query type (factual, comparative, analytical)
- Route to appropriate handler
- Chain multiple operations

**Example**:
> "Create a summary of all Q4 contracts and email it to the team"
> - Agent Step 1: Retrieve Q4 contracts
> - Agent Step 2: Generate summary
> - Agent Step 3: Format as email
> - Agent Step 4: (With integration) Send email

**Effort**: High (1 week)

---

### 4.2 Conversational Memory

**Current State**: Each query is independent.

**Proposed Enhancement**: Session-aware conversations.

**Features**:
- Remember previous questions in session
- Resolve pronouns: "What about their revenue?" → knows "their" = previous entity
- Store conversation history in Neo4j

**Schema**:
```cypher
(:Session)-[:HAS_MESSAGE]->(:Message {role, content, timestamp})
(:Message)-[:REFERENCES]->(:Entity)
```

**Effort**: Medium (2-3 days)

---

### 4.3 Proactive Insights

**Current State**: Passive Q&A only.

**Proposed Enhancement**: System generates unsolicited insights.

**Triggers**:
- New document uploaded → "This contract mentions a deadline in 3 days"
- Pattern detected → "Revenue has declined for 3 consecutive months"
- Entity changes → "John's role changed from 'Agent' to 'Manager'"

**Implementation**:
Background analysis jobs that query the graph for anomalies/patterns.

**Effort**: High (1 week)

---

### 4.4 Citation Enhancement

**Current State**: Basic [[Source: filename]] citations.

**Proposed Enhancement**: Rich, interactive citations.

**Features**:
- Page/section numbers
- Highlight relevant passages
- "View in context" links
- Confidence scores per citation
- Citation clustering: "3 sources agree on this"

**Effort**: Medium (2-3 days)

---

## Category 5: Analytics & Observability

### 5.1 Query Analytics Dashboard

**Current State**: No visibility into usage patterns.

**Proposed Enhancement**: Analytics for query patterns.

**Metrics**:
- Most common query topics
- Average response time
- Confidence score distribution
- Failed query analysis
- Document utilization (which docs are queried most)

**Storage**: Neo4j nodes for query logs

**Effort**: Medium (3-4 days)

---

### 5.2 RAG Quality Monitoring

**Current State**: No automated quality checks.

**Proposed Enhancement**: Continuous quality monitoring.

**Checks**:
- Retrieval relevance scores over time
- Hallucination detection rate
- Citation accuracy audits
- User feedback integration (thumbs up/down)

**Alerts**:
- "Relevance scores dropped 20% this week"
- "Document X has high hallucination rate"

**Effort**: Medium (3-4 days)

---

### 5.3 Knowledge Graph Visualization

**Current State**: Graph exists but isn't visible to users.

**Proposed Enhancement**: Interactive graph explorer.

**Features**:
- Visual representation of entities and relationships
- Filter by entity type, time range, source
- Click-to-query: Click entity → "Tell me about this"
- Export subgraphs

**Tools**: Neo4j Bloom (paid) or custom D3.js visualization

**Effort**: High (1-2 weeks)

---

## Category 6: Neo4j Aura-Specific Optimizations

### 6.1 Vector Index Tuning

**Current State**: Default vector index configuration.

**Proposed Enhancement**: Optimized index settings.

**Tuning Options**:
- Dimension reduction (768 → 256) for speed vs accuracy tradeoff
- HNSW parameters: `m` (connections), `efConstruction` (build quality)
- Similarity function: cosine vs euclidean

**Effort**: Low (1 day)

---

### 6.2 Query Caching

**Current State**: Every query hits Neo4j.

**Proposed Enhancement**: Intelligent caching layer.

**Strategies**:
- Exact query match cache
- Semantic similarity cache (similar questions → same answer)
- Entity-based cache invalidation

**Implementation**: Redis or in-memory cache with TTL

**Effort**: Medium (2-3 days)

---

### 6.3 Batch Operations

**Current State**: Individual Cypher queries.

**Proposed Enhancement**: Batched writes for performance.

**Optimization**:
```cypher
// Instead of N individual creates:
UNWIND $batch AS row
CREATE (n:Entity {id: row.id, name: row.name, ...})
```

**Benefits**: 10-50x faster bulk ingestion

**Effort**: Low (1 day)

---

## Category 7: Security & Governance

### 7.1 Document-Level Access Control

**Current State**: All users see all documents.

**Proposed Enhancement**: Role-based document access.

**Features**:
- Tag documents with access levels
- Filter retrieval based on user role
- Audit log for sensitive document access

**Schema**:
```cypher
(:User)-[:HAS_ROLE]->(:Role)-[:CAN_ACCESS]->(:Document)
```

**Effort**: Medium (3-4 days)

---

### 7.2 PII Detection & Redaction

**Current State**: All content stored as-is.

**Proposed Enhancement**: Automatic PII handling.

**Capabilities**:
- Detect: SSN, credit cards, email, phone numbers
- Options: Redact, encrypt, or flag for review
- Audit trail for PII access

**Effort**: Medium (2-3 days)

---

### 7.3 Data Lineage Tracking

**Current State**: Basic source file tracking.

**Proposed Enhancement**: Full data provenance.

**Tracks**:
- Original source
- Transformation history
- Which chunks derived from which pages
- Who uploaded, when, why

**Query**: "Where did this fact come from?" → Full lineage graph

**Effort**: Medium (2-3 days)

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Temporal-Aware Retrieval | High | Low | 🟢 Quick Win |
| Batch Operations | Medium | Low | 🟢 Quick Win |
| Conversational Memory | High | Medium | 🟡 High Value |
| Entity Extraction (NER) | High | Medium | 🟡 High Value |
| Incremental Updates | High | Medium | 🟡 High Value |
| Multi-Hop Reasoning | High | High | 🟠 Strategic |
| Multi-Modal Ingestion | High | High | 🟠 Strategic |
| Knowledge Graph Viz | Medium | High | 🔵 Nice to Have |
| Real-Time Connectors | Medium | High | 🔵 Nice to Have |

---

## Recommended Roadmap

### Phase 1: Quick Wins (1-2 weeks)
- Temporal-aware retrieval
- Batch operations optimization
- Confidence-calibrated retrieval
- Citation enhancement

### Phase 2: Core Upgrades (2-4 weeks)
- Conversational memory
- Entity extraction from text
- Incremental updates (delta ingestion)
- Query analytics dashboard

### Phase 3: Advanced Features (4-8 weeks)
- Multi-hop reasoning
- Multi-modal ingestion
- Proactive insights
- Knowledge graph visualization

### Phase 4: Enterprise Features (Ongoing)
- Real-time data connectors
- Access control
- PII detection
- Data lineage

---

## Questions for Prioritization

1. Which use cases are most important to your target customers?
2. Is real-time data integration a priority, or is batch upload sufficient?
3. How important is the visual knowledge graph explorer?
4. Do you need multi-tenant isolation (separate data per company)?
5. What's the budget for additional infrastructure (Redis, workers, etc.)?

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/rag.py` | Retrieval enhancements, confidence scoring |
| `backend/database.py` | Graph queries, vector search, caching |
| `backend/ingestion.py` | Delta ingestion, streaming, multi-modal |
| `backend/graph_service.py` | Entity extraction, relationship discovery |
