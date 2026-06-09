---
title: RAG System Master
status: implemented
type: master
created: 2025-12-28
updated: 2025-12-28
tags: [rag, retrieval, ai, search, core]
consolidates:
  - Active/Proposals/advanced_rag_enhancements_proposal.md
  - Active/Proposals/rag_retrieval_improvements_proposal.md
  - Active/Proposals/confidence_calibrated_retrieval_proposal.md
  - Active/Proposals/self_adapting_rag_proposal.md
---

# RAG System Master

The core intelligence layer of Davlon. Implements retrieval-augmented generation with hybrid search, adaptive retrieval, and sentence-level verification.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          RAG PIPELINE                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. QUERY ANALYSIS                                                    │
│     ├── Intent Classification (FACTUAL, SUMMARY, ANALYTICAL...)      │
│     ├── Multi-Category Detection (AI classifies to learned cats)     │
│     └── Query Expansion (synonyms from cache or LLM)                  │
│                                                                       │
│  2. RETRIEVAL                                                         │
│     ├── Adaptive K Selection (scales with corpus size)               │
│     ├── Model Selection (lite/flash/pro based on complexity)         │
│     ├── Hybrid Search (vector + graph traversal)                     │
│     └── Score Floor Filtering (0.35 minimum)                         │
│                                                                       │
│  3. GENERATION                                                        │
│     ├── Context Injection (ranked chunks + company profile)          │
│     ├── Gemini 2.5 Flash (default) or Pro (complex queries)          │
│     └── Inline Citation Enforcement                                  │
│                                                                       │
│  4. VERIFICATION                                                      │
│     ├── Sentence-Level Splitting                                     │
│     ├── Vector Similarity Scoring (answer vs context)                │
│     └── Confidence Thresholds (90% text, 75% images)                 │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Key Files

| File | Size | Purpose |
|------|------|---------|
| [rag.py](file:///Users/dora/Documents/Davlon_Gamma/backend/rag.py) | 48KB | Main RAG client, GeminiClient class |
| [database.py](file:///Users/dora/Documents/Davlon_Gamma/backend/database.py) | 46KB | Neo4j driver, hybrid_graph_search |
| [company_profile.py](file:///Users/dora/Documents/Davlon_Gamma/backend/company_profile.py) | 13KB | Dynamic company context |

---

## Implemented Features

### 1. Query Intent Classification
**Status**: ✅ Complete  
**Code**: `rag.py:classify_query_intent()`

Rule-based (no AI call) classification into 7 intent types:

| Intent | Trigger Phrases | Base K | Score Floor |
|--------|-----------------|--------|-------------|
| FACTUAL | "what is", "who is" | 5 | 0.50 |
| COMPREHENSIVE | "list all", "show all" | 15 | 0.35 |
| ANALYTICAL | "why", "explain" | 10 | 0.40 |
| COMPARATIVE | "compare", "vs" | 12 | 0.40 |
| TEMPORAL | "when", "latest" | 8 | 0.40 |
| DEFINITION | "define", "meaning" | 3 | 0.55 |
| SUMMARY | "summarize", "overview" | 18 | 0.30 |

---

### 2. Adaptive K Selection
**Status**: ✅ Complete  
**Code**: `rag.py:calculate_adaptive_k()`

Scales retrieval count with corpus size:

| Corpus Size | Scale Factor | Example (base K=5) |
|-------------|--------------|-------------------|
| < 500 chunks | 1.0x | 5 chunks |
| 500-2000 | 1.5x | 7 chunks |
| 2000-10000 | 2.0x | 10 chunks |
| 10000+ | 3.0x | 15 chunks |

Special categories get additional 1.5x boost.

---

### 3. Model Auto-Selection
**Status**: ✅ Complete (Pro defined but not yet activated)  
**Code**: `rag.py:select_model_for_corpus()`

| Model | Corpus Size | Query Type | Cost/1M tokens |
|-------|-------------|------------|----------------|
| gemini-2.5-flash-lite | < 500 | Simple | $0.075 |
| gemini-2.5-flash | 500+ | Any | $0.15 |
| ~~gemini-2.5-pro~~ | — | (Configured, not selected) | $1.25 |

> **Note**: Pro model is defined in `GEMINI_MODELS` but `select_model_for_corpus()` currently only returns lite or flash.

---

### 4. Query Expansion with Caching
**Status**: ✅ Complete  
**Code**: `rag.py:expand_query_for_retrieval()`

- Cache-first lookup in Neo4j
- LLM fallback for cache misses
- Generates 3-5 synonyms/related terms
- Tracks hit rates for pruning low-performers

---

### 5. Hybrid Graph+Vector Search
**Status**: ✅ Complete  
**Code**: `database.py:hybrid_graph_search()`

Combines two search strategies:
1. **Vector similarity** — Semantic matching via embeddings
2. **Graph traversal** — Follows entity relationships in Neo4j

Also includes:
- Temporal boost (prioritize recent documents)
- Score floor filtering (remove < 0.35)
- Source diversity (prevent single-source domination)

---

### 6. Multi-Category Detection
**Status**: ✅ Complete  
**Code**: `rag.py:classify_query_multi()`

- Detects ALL relevant categories (not just one)
- Identifies unknown topics → logs for admin review
- Returns `QueryClassification` dataclass

---

### 7. Sentence-Level Verification
**Status**: ✅ Complete  
**Code**: `rag.py:_verify_mathematically()`

"Vector Judge" — calculates cosine similarity between answer and context:
- Embeds the answer
- Embeds each context chunk
- Returns max similarity score

Thresholds:
- Text: 90% confidence required
- Images: 75% (more ambiguous)
- Tables/Graphs: 90%

---

### 8. Special Category Handling
**Status**: ✅ Complete  
**Code**: `rag.py:_apply_special_category_tiebreaker()`

Categories marked "special" (e.g., legal) get:
- Tiebreaker priority at similar scores
- Audit logging for compliance
- 50% chunk overlap during ingestion(*)

---

## Configuration

```python
# Score floor for filtering
SCORE_FLOOR = 0.35

# Confidence thresholds
CONFIDENCE_THRESHOLD_TEXT = 0.90
CONFIDENCE_THRESHOLD_IMAGE = 0.75

# Temporal decay
TEMPORAL_DECAY_DAYS = 365
TEMPORAL_DECAY_FACTOR = 0.3
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/query` | POST | Main RAG query |
| `/api/query-documents` | POST | Document-constrained query |
| `/api/expansion-metrics` | GET | Query expansion quality stats |
| `/api/prune-expansions` | POST | Admin: prune low-performing terms |

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| 📋 Proposal | [Advanced RAG Enhancements](../../Active/Proposals/advanced_rag_enhancements_proposal.md) | Future roadmap |
| 📋 Proposal | [Retrieval Improvements](../../Active/Proposals/rag_retrieval_improvements_proposal.md) | Detailed chunking/reranking plans |
| 📋 Proposal | [Confidence Calibrated Retrieval](../../Active/Proposals/confidence_calibrated_retrieval_proposal.md) | Dynamic K theory |
| 📋 Proposal | [Self-Adapting RAG](../../Active/Proposals/self_adapting_rag_proposal.md) | Company-agnostic architecture |
| 🔧 Master | [Ingestion Pipeline](./ingestion_pipeline_master.md) | How documents enter the system |
| 🔧 Master | [Knowledge Graph](./knowledge_graph_master.md) | Neo4j schema and entities |
