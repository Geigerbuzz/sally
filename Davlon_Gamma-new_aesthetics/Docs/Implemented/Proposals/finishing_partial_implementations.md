# Finishing Partial RAG Implementations

**Date**: December 27, 2025  
**Status**: Draft - Gap Analysis

This document details what remains to fully complete three partially implemented features from the Advanced RAG Enhancements proposal.

---

## 1. Query Expansion

### Current State
- `expand_query_for_retrieval()` exists in `rag.py` (lines 324-359)
- It **IS** called during RAG queries (line 756)
- Uses Gemini to generate synonyms/acronyms

### Gaps

| Gap | Description |
|-----|-------------|
| **No Caching** | Every query triggers an LLM call for expansion, adding latency and cost |
| **No Quality Metrics** | No measurement of whether expansions improve retrieval accuracy |

### Remaining Work

1. **Cache Layer**: Store common term expansions in Neo4j or Redis
   - Key: normalized query term
   - Value: expansion list
   - TTL: 7 days
2. **Quality Metrics**: Track expansion effectiveness (hit rate, relevance improvement)

---

## 2. Semantic Chunking ✅ COMPLETE

### Current State
- `semantic_chunker.py` is **fully implemented** (557 lines)
- Uses sentence embeddings to detect topic boundaries
- Adaptive thresholds based on document similarity distribution
- Lookahead window for confirming topic breaks
- Overlap support for context continuity
- **Now wired into ingestion pipeline as default**
- **`SEMANTIC_CHUNKING_ENABLED` config toggle added**

### Implementation
- `config.py`: Added `SEMANTIC_CHUNKING_ENABLED` (default: `true`)
- `ingestion.py`: Semantic chunking is default, character-based fallback if disabled or on error

---

## 3. Document Lifecycle

### Current State
- `document_lifecycle.py` is **comprehensive** (483 lines)
- AI permanence analysis with rule-based confidence scoring
- Version supersession detection (`v1` → `v2`)
- Recovery learning (boosts category when user un-archives)

### Gaps

| Gap | Description |
|-----|-------------|
| **No Scheduled Jobs** | `analyze_permanence()` is called at ingestion only; no periodic re-evaluation |
| **No UI Surfaces** | Legacy tab API exists but frontend "Legacy" tab not implemented |
| **Inbox Notifications** | `should_notify_for_legacy()` returns bool but no integration with Inbox |
| **APOC Dependency** | `_boost_category_permanence()` requires APOC plugin which may not be installed |

### Remaining Work

1. **Legacy Tab UI**: Create `/api/documents/legacy` endpoint and frontend tab in `sources.html`
2. **Scheduled Re-evaluation**: Add daily background job to check `status = 'active'` documents where `createdAt < 90 days ago` and `permanence_score < 0.5`
3. **Inbox Integration**: When `should_notify_for_legacy()` returns true, create an Inbox message:
   ```json
   {
     "type": "lifecycle_decision",
     "message": "I've marked 'contract_draft_v1.pdf' as legacy. Was this correct?",
     "actions": ["Confirm", "Restore"]
   }
   ```
4. **Remove APOC Dependency**: Rewrite `_boost_category_permanence()` to use standard JSON string manipulation instead of APOC functions

---

## Summary Table

| Feature | Core Logic | Pipeline Integration | UI | Caching/Metrics |
|---------|-----------|---------------------|-----|----------------|
| Query Expansion | ✅ | ✅ | N/A | ✅ Done |
| Semantic Chunking | ✅ | ✅ Done | N/A | N/A |
| Document Lifecycle | ✅ | ✅ | ✅ | ✅ |

---

## ✅ IMPLEMENTATION COMPLETE

**Completed: December 27, 2024**

All features from this proposal have been implemented:
- Query Expansion with Neo4j caching and learning signals
- Semantic Chunking as default pipeline
- Document Lifecycle with scheduled jobs, Legacy UI, and Inbox notifications
- APOC dependency confirmed available on Neo4j Aura
