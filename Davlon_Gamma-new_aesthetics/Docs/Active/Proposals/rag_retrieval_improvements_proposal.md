---
title: RAG Retrieval Pipeline Improvement Proposal
status: draft
type: proposal
created: 2025-12-21
updated: 2025-12-28
tags: [rag, retrieval, pipeline, search]
parent: null
children: []
related:
  - ./advanced_rag_enhancements_proposal.md
  - ./confidence_calibrated_retrieval_proposal.md
  - ../../Implemented/Proposals/self_adapting_rag_proposal.md
  - ../../Implemented/Proposals/inline_citations_proposal.md
---

# RAG Retrieval Pipeline: Comprehensive Improvement Proposal

**Date**: December 21, 2025  
**Status**: Draft — Awaiting Review  
**Scope**: Full retrieval pipeline from query to context delivery

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Semantic Chunking](#11-semantic-chunking) | ✅ Complete | 2025-12-21 | `semantic_chunker.py` |
| [Overlapping Chunks](#12-overlapping-chunks) | ⬜ Pending | — | — |
| [Parent-Child Links](#13-parent-child-chunk-relationships) | ✅ Complete | 2025-12-21 | `database.py:insert_chunk` |
| [Chunk Metadata](#14-chunk-metadata-enrichment) | ⬜ Pending | — | — |
| [Query Intent Classification](#21-query-intent-classification) | ✅ Complete | 2025-12-21 | `rag.py:classify_query` |
| [Query Expansion](#22-query-expansion) | ✅ Complete | 2025-12-21 | `rag.py:expand_query` |
| [HyDE Embeddings](#23-hyde-hypothetical-document-embeddings) | ⬜ Pending | — | — |
| [Multi-Stage Retrieval](#31-multi-stage-retrieval) | ⬜ Pending | — | — |
| [Reranking](#32-reranking-options) | ⬜ Pending | — | — |
| [Graph-Enhanced Retrieval](#33-graph-enhanced-retrieval) | ✅ Complete | 2025-12-21 | `database.py:hybrid_graph_search` |
| [Confidence Scoring](#41-confidence-scoring) | ⬜ Pending | — | — |
| [Adaptive K Selection](#42-adaptive-k-selection) | ⬜ Pending | — | — |
| [Parent Context Assembly](#43-parent-context-assembly) | ⬜ Pending | — | — |

---

## Executive Summary

This document proposes a systematic overhaul of the retrieval pipeline to address the fundamental limitations of vector-only search. The improvements span four layers:

1. **Upstream** — Better chunking and indexing
2. **Query** — Smarter query understanding and expansion
3. **Retrieval** — Multi-stage search with reranking  
4. **Delivery** — Confidence calibration and context assembly

Each layer independently improves accuracy; together they compound into a significantly more reliable system.

---

## Current Pipeline Assessment

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Document → Fixed Chunking → Embedding → Neo4j                          │
│                    ↓                                                     │
│  Query → Embedding → Vector Search (Top 5) → LLM Response               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Known Limitations

| Stage | Problem | Impact |
|-------|---------|--------|
| **Chunking** | Fixed size breaks mid-sentence | Context loss, orphan references |
| **Chunking** | No overlap between chunks | "This" and "it" without antecedent |
| **Query** | Raw query embedded directly | Vocabulary mismatch |
| **Retrieval** | Vector-only scoring | Topic match ≠ answer relevance |
| **Retrieval** | Fixed top-K (always 5) | Over/under retrieval |
| **Delivery** | No reranking | Low-quality chunks reach LLM |

---

## Proposed Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROPOSED PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INDEXING (Upstream):                                                    │
│  Document → Semantic Chunking → Overlap → Embedding → Neo4j             │
│                           ↓               ↓                              │
│                    Parent Links     Chunk Metadata                       │
│                                                                          │
│  RETRIEVAL:                                                              │
│  Query → Analysis → Expansion → Multi-Vector Search → Rerank → Filter   │
│              ↓           ↓              ↓                ↓               │
│         Intent      Synonyms      Graph+Vector      Score+Diversity     │
│                                                                          │
│  DELIVERY:                                                               │
│  Ranked Chunks → Context Assembly → Confidence Check → LLM Response     │
│                       ↓                   ↓                              │
│               Parent Context      Low? → Expand/Clarify                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# Layer 1: Upstream Improvements (Indexing) {#layer-1-upstream}

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md)  
> **Affects**: [Layer 3 Retrieval](#layer-3-retrieval), [RAG System](../../Implemented/Masters/rag_system_master.md)

## 1.1 Semantic Chunking {#11-semantic-chunking}

**Current**: Fixed character-based chunking (e.g., 500 chars)

**Problem**: Breaks mid-sentence, separates related content

**Proposed**: Semantic-aware chunking

```python
def semantic_chunk(text: str) -> List[str]:
    """Chunk by semantic boundaries, not character count."""
    chunks = []
    
    # 1. Split by major boundaries (headers, paragraphs)
    sections = split_by_headers(text)
    
    for section in sections:
        # 2. Split long sections by paragraph
        paragraphs = section.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            # 3. Keep related paragraphs together
            if len(current_chunk) + len(para) < 800:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
    
    return chunks
```

**Benefits**:
- Complete thoughts in each chunk
- Headers stay with their content
- Natural paragraph groupings preserved

**Effort**: Low (1-2 days)

---

## 1.2 Overlapping Chunks

**Current**: Chunks are disjoint (chunk 1 ends where chunk 2 begins)

**Problem**: References like "this agreement" or "the above terms" lose context

**Proposed**: 20% overlap between consecutive chunks

```python
def chunk_with_overlap(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Find natural break point (sentence end)
        last_period = chunk.rfind('. ')
        if last_period > chunk_size * 0.5:
            chunk = chunk[:last_period + 1]
            end = start + last_period + 1
        
        chunks.append(chunk)
        start = end - overlap  # Overlap with previous
    
    return chunks
```

**Benefits**:
- "This" and "it" have antecedents in same chunk
- Sentence boundaries preserved
- Context continuity

**Effort**: Low (1 day)

---

## 1.3 Parent-Child Chunk Relationships

**Current**: Chunks are independent nodes

**Problem**: Can't retrieve surrounding context when needed

**Proposed**: Link chunks to their neighbors and parent sections

```cypher
// Schema
(:Chunk)-[:NEXT]->(:Chunk)
(:Chunk)-[:PREV]->(:Chunk)
(:Section)-[:CONTAINS]->(:Chunk)
(:Document)-[:HAS_SECTION]->(:Section)
```

```python
# During ingestion
for i, chunk in enumerate(chunks):
    await db.run_query("""
        CREATE (c:Chunk {id: $id, text: $text, position: $pos})
        WITH c
        MATCH (prev:Chunk {id: $prev_id})
        CREATE (prev)-[:NEXT]->(c)
        CREATE (c)-[:PREV]->(prev)
    """, id=chunk_id, prev_id=prev_chunk_id, pos=i)
```

**Retrieval benefit**:
```python
# When a chunk is retrieved, optionally fetch neighbors
async def get_with_context(chunk_id: str, context_window: int = 1):
    query = """
    MATCH (c:Chunk {id: $id})
    OPTIONAL MATCH (prev:Chunk)-[:NEXT*1..$window]->(c)
    OPTIONAL MATCH (c)-[:NEXT*1..$window]->(next:Chunk)
    RETURN prev.text, c.text, next.text
    """
    return await db.run_query(query, id=chunk_id, window=context_window)
```

**Benefits**:
- Can fetch "Appendix C" when chunk says "see Appendix C"
- Can get full context around a matched fragment
- Enables parent-document summarization

**Effort**: Medium (2-3 days)

---

## 1.4 Chunk Metadata Enrichment

**Current**: Chunks have text + source + category

**Problem**: No structured information for filtering/boosting

**Proposed**: Extract and store metadata during ingestion

```python
class ChunkMetadata(BaseModel):
    chunk_id: str
    text: str
    source: str
    
    # New fields
    section_title: Optional[str]      # "Payment Terms", "Appendix A"
    page_number: Optional[int]        # From PDF extraction
    content_type: str                 # "prose", "table", "list", "legal"
    entities_mentioned: List[str]     # ["John Smith", "Acme Corp", "$500K"]
    has_numbers: bool                 # Useful for financial queries
    is_definition: bool               # "X means...", "X is defined as..."
    temporal_references: List[str]    # ["March 2024", "Q1", "fiscal year"]
```

**Query-time benefit**:
```python
# User asks: "What is the total amount?"
# Boost chunks where has_numbers=True
# Filter to content_type="table" for numerical queries
```

**Effort**: Medium (2-3 days)

---

# Layer 2: Query Understanding {#layer-2-query}

> **Depends on**: None (standalone preprocessing)  
> **Affects**: [Layer 3 Retrieval](#layer-3-retrieval), [Adaptive Learning](./adaptive_learning_system_proposal.md)

## 2.1 Query Intent Classification {#21-query-intent-classification}

**Current**: All queries treated identically

**Problem**: Factual, analytical, and comprehensive queries need different strategies

**Proposed**: Classify query before retrieval

```python
class QueryIntent(Enum):
    FACTUAL = "factual"           # "What is X?" → Need 1-3 precise chunks
    COMPREHENSIVE = "comprehensive" # "List all X" → Need many chunks
    ANALYTICAL = "analytical"     # "Why did X?" → Need context + reasoning
    COMPARATIVE = "comparative"   # "Compare X and Y" → Need multiple topics
    TEMPORAL = "temporal"         # "When did X?" → Need time-aware search
    DEFINITION = "definition"     # "What does X mean?" → Need definition chunks

async def classify_query(query: str) -> QueryIntent:
    # Rule-based first (fast)
    query_lower = query.lower()
    
    if any(w in query_lower for w in ["list all", "what are all", "every", "show me all"]):
        return QueryIntent.COMPREHENSIVE
    if any(w in query_lower for w in ["compare", "difference between", "vs", "versus"]):
        return QueryIntent.COMPARATIVE
    if any(w in query_lower for w in ["why", "explain", "how does", "reason"]):
        return QueryIntent.ANALYTICAL
    if any(w in query_lower for w in ["when", "what date", "what time", "timeline"]):
        return QueryIntent.TEMPORAL
    if any(w in query_lower for w in ["what is", "define", "meaning of", "what does"]):
        return QueryIntent.DEFINITION
    
    return QueryIntent.FACTUAL

# Different retrieval strategies per intent
INTENT_STRATEGIES = {
    QueryIntent.FACTUAL:       {"k": 5,  "score_floor": 0.5, "expand": False},
    QueryIntent.COMPREHENSIVE: {"k": 20, "score_floor": 0.3, "expand": True},
    QueryIntent.ANALYTICAL:    {"k": 10, "score_floor": 0.4, "expand": True},
    QueryIntent.COMPARATIVE:   {"k": 15, "score_floor": 0.4, "expand": True},
    QueryIntent.TEMPORAL:      {"k": 8,  "score_floor": 0.4, "time_sort": True},
    QueryIntent.DEFINITION:    {"k": 3,  "score_floor": 0.6, "prefer_definitions": True},
}
```

**Benefits**:
- "List all payment terms" retrieves 20 chunks, not 5
- "What is APR?" retrieves 3 focused chunks
- Reduces over/under retrieval

**Effort**: Low (1-2 days)

---

## 2.2 Query Expansion

**Current**: Raw query embedded directly

**Problem**: "interest rate" doesn't match "APR"

**Proposed**: Expand query with synonyms and related terms

### Option A: LLM-Based Expansion (Accurate, Slower)

```python
async def expand_query_llm(query: str) -> str:
    prompt = f"""
    Original query: {query}
    
    Generate 3-5 alternative phrasings or related terms that might appear in documents.
    Return as comma-separated list.
    
    Example:
    Query: "What is the interest rate?"
    Expansion: "APR, annual percentage rate, lending rate, finance charge"
    """
    response = await model.generate_content_async(prompt)
    return f"{query} {response.text}"
```

### Option B: Embedding-Based Expansion (Fast, Less Accurate)

```python
async def expand_query_embedding(query: str) -> List[str]:
    # Find similar queries from historical data
    query_embedding = await embed(query)
    similar_queries = await db.run_query("""
        CALL db.index.vector.queryNodes('query_log', 5, $embedding)
        YIELD node, score
        WHERE score > 0.8
        RETURN node.text as similar_query
    """, embedding=query_embedding)
    
    return [query] + [q['similar_query'] for q in similar_queries]
```

### Option C: Hybrid (Recommended)

```python
async def expand_query_hybrid(query: str) -> str:
    # Fast keyword expansion
    synonyms = get_synonyms(query)  # From local thesaurus
    
    # Only use LLM for complex queries
    if needs_deep_expansion(query):
        llm_expansion = await expand_query_llm(query)
        return f"{query} {synonyms} {llm_expansion}"
    
    return f"{query} {synonyms}"
```

**Benefits**:
- "interest rate" query matches "APR", "finance charge" chunks
- Covers vocabulary gaps
- Reduces zero-result queries

**Effort**: Low-Medium (1-3 days)

---

## 2.3 HyDE (Hypothetical Document Embeddings)

**Current**: Embed the question

**Problem**: Questions and answers have different semantic structure

**Example**:
```
Question: "What is the late fee?"
Answer style: "Late payments incur a $50 penalty."
```

These embed differently — question words vs statement words.

**Proposed**: Generate a hypothetical answer, embed THAT

```python
async def hyde_embed(query: str) -> List[float]:
    # Step 1: Generate hypothetical answer
    prompt = f"""
    Imagine a document that answers this question:
    Question: {query}
    
    Write a 1-2 sentence passage that would contain the answer.
    Be specific and factual-sounding.
    """
    hypothetical = await model.generate_content_async(prompt)
    
    # Step 2: Embed the hypothetical answer
    embedding = await embed(hypothetical.text)
    
    return embedding
```

**Example transformation**:
```
Query: "What is the late fee?"
HyDE: "Late payments are subject to a penalty fee of $50 per occurrence."
→ Embedding of this hypothetical matches actual answer chunks better
```

**Benefits**:
- 10-20% improvement in retrieval accuracy (per research)
- Matches answer-shaped text, not question-shaped
- Especially helps for factual queries

**Caution**:
- Adds one LLM call per query
- Hypothetical might bias toward wrong answers

**Effort**: Low (1 day)

---

# Layer 3: Retrieval Improvements {#layer-3-retrieval}

> **Depends on**: [Layer 1 Upstream](#layer-1-upstream), [Layer 2 Query](#layer-2-query), [Knowledge Graph](../../Implemented/Masters/knowledge_graph_master.md)  
> **Affects**: [Layer 4 Delivery](#layer-4-delivery), [RAG System](../../Implemented/Masters/rag_system_master.md)

## 3.1 Multi-Stage Retrieval {#31-multi-stage-retrieval}

**Current**: Single vector search → Top K → Done

**Proposed**: Three-stage funnel

```
Stage 1: Broad Recall (Vector Search)
├── Retrieve 50 candidates
├── Prioritize recall over precision
└── Fast, cheap

Stage 2: Reranking
├── Score 50 candidates with cross-encoder or reranker
├── Sort by true relevance
└── Medium speed, low cost

Stage 3: Filtering & Assembly
├── Apply score floor
├── Ensure diversity
├── Add parent context if needed
└── Return 5-15 high-quality chunks
```

```python
async def multi_stage_retrieve(query: str) -> List[dict]:
    # Stage 1: Broad vector search
    candidates = await vector_search(query, k=50)
    
    # Stage 2: Rerank
    reranked = await rerank(query, candidates)
    
    # Stage 3: Filter and assemble
    results = []
    sources_seen = set()
    
    for chunk in reranked:
        if chunk['score'] < 0.35:
            break  # Score floor
        
        # Diversity: don't over-represent one source
        if chunk['source'] in sources_seen and len(results) >= 5:
            continue
        
        results.append(chunk)
        sources_seen.add(chunk['source'])
        
        if len(results) >= 15:
            break
    
    return results
```

**Benefits**:
- High recall in stage 1 (don't miss anything)
- High precision in stage 2 (reranker catches what vector missed)
- Controlled output in stage 3 (diversity, quality floor)

**Effort**: Medium (2-3 days)

---

## 3.2 Reranking Options

### Option A: Cohere Rerank API (Easiest)

```python
import cohere

co = cohere.Client(api_key)

async def rerank_cohere(query: str, chunks: List[dict]) -> List[dict]:
    response = co.rerank(
        query=query,
        documents=[c['text'] for c in chunks],
        top_n=20,
        model='rerank-english-v2.0'
    )
    
    reranked = []
    for result in response.results:
        chunk = chunks[result.index]
        chunk['rerank_score'] = result.relevance_score
        reranked.append(chunk)
    
    return sorted(reranked, key=lambda x: x['rerank_score'], reverse=True)
```

**Cost**: ~$0.001 per query (1000 chunks = $1)

### Option B: Cross-Encoder (Local, Free)

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_local(query: str, chunks: List[dict]) -> List[dict]:
    pairs = [(query, c['text']) for c in chunks]
    scores = model.predict(pairs)
    
    for i, chunk in enumerate(chunks):
        chunk['rerank_score'] = float(scores[i])
    
    return sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
```

**Cost**: Free (runs locally)
**Speed**: ~100ms for 50 chunks
**Accuracy**: Slightly lower than Cohere

### Option C: LLM-Based Reranking (Most Accurate, Most Expensive)

```python
async def rerank_llm(query: str, chunks: List[dict]) -> List[dict]:
    # Batch chunks for efficiency
    prompt = f"""
    Query: {query}
    
    Rank these passages by relevance to the query. 
    Return the indices in order from most to least relevant.
    
    Passages:
    {chr(10).join(f"[{i}] {c['text'][:200]}..." for i, c in enumerate(chunks[:20]))}
    
    Ranking (just the numbers): 
    """
    
    response = await model.generate_content_async(prompt)
    order = parse_ranking(response.text)
    
    return [chunks[i] for i in order]
```

**Cost**: ~$0.01 per query
**Accuracy**: Highest

### Recommendation: Cohere or Local Cross-Encoder

For most use cases, Cohere Rerank or a local cross-encoder provides the best balance. Reserve LLM reranking for the most critical applications.

---

## 3.3 Graph-Enhanced Retrieval

**Current**: Only vector similarity

**Proposed**: Combine vector + graph traversal

```python
async def hybrid_graph_vector_search(query: str, k: int = 15) -> List[dict]:
    # Vector candidates
    vector_results = await vector_search(query, k=30)
    
    # Entity extraction from query
    entities = await extract_entities(query)  # ["John", "Project Alpha"]
    
    # Graph traversal for entity-related chunks
    graph_results = []
    for entity in entities:
        related = await db.run_query("""
            MATCH (e:Entity {name: $entity})-[:MENTIONED_IN]->(c:Chunk)
            RETURN c.text, c.source, 0.7 as score
            LIMIT 10
        """, entity=entity)
        graph_results.extend(related)
    
    # Merge and deduplicate
    all_results = merge_results(vector_results, graph_results)
    
    # Rerank combined results
    return await rerank(query, all_results)[:k]
```

**Benefits**:
- Query mentions "John" → Get all chunks about John
- Graph relationships surface indirect connections
- Catches what vector search misses

**Effort**: Medium (already partially implemented)

---

# Layer 4: Delivery & Confidence {#layer-4-delivery}

> **Depends on**: [Layer 3 Retrieval](#layer-3-retrieval)  
> **Affects**: [Chat Interface](../../Implemented/Masters/ui_system_master.md), [Entity Intelligence](./adaptive_entity_intelligence_proposal.md)

## 4.1 Confidence Scoring {#41-confidence-scoring}

**Current**: No confidence indication

**Proposed**: Calculate and return confidence with each response

```python
def calculate_confidence(reranked_results: List[dict]) -> dict:
    if not reranked_results:
        return {"level": "none", "score": 0.0, "action": "refuse"}
    
    top_score = reranked_results[0]['rerank_score']
    avg_top_3 = mean([r['rerank_score'] for r in reranked_results[:3]])
    score_spread = top_score - reranked_results[-1]['rerank_score']
    
    if top_score > 0.8 and avg_top_3 > 0.7:
        return {"level": "high", "score": 0.9, "action": "answer"}
    elif top_score > 0.6 and avg_top_3 > 0.5:
        return {"level": "medium", "score": 0.6, "action": "answer_with_caveat"}
    elif top_score > 0.4:
        return {"level": "low", "score": 0.4, "action": "expand_or_clarify"}
    else:
        return {"level": "none", "score": 0.2, "action": "refuse_or_clarify"}
```

**Actions**:
- `answer`: Proceed normally
- `answer_with_caveat`: "Based on available information..."
- `expand_or_clarify`: Fetch more chunks or ask user
- `refuse_or_clarify`: "I don't have confident information about this"

---

## 4.2 Adaptive K Selection

**Current**: Always retrieve 5 chunks

**Proposed**: Dynamic K based on confidence and query type

```python
async def adaptive_retrieve(query: str) -> List[dict]:
    intent = await classify_query(query)
    strategy = INTENT_STRATEGIES[intent]
    
    # Initial retrieval
    candidates = await vector_search(query, k=strategy['k'] * 3)
    reranked = await rerank(query, candidates)
    
    # Calculate confidence
    confidence = calculate_confidence(reranked)
    
    # Adjust K based on confidence
    if confidence['level'] == 'high':
        k = min(strategy['k'], 5)  # Less context needed
    elif confidence['level'] == 'low':
        k = strategy['k'] * 2  # More context needed
    else:
        k = strategy['k']
    
    # Apply score floor
    results = [r for r in reranked if r['rerank_score'] > strategy['score_floor']][:k]
    
    return results, confidence
```

---

## 4.3 Parent Context Assembly

**Current**: Return only matched chunks

**Proposed**: Optionally include surrounding context

```python
async def assemble_context(chunks: List[dict], include_parents: bool = False) -> str:
    context_parts = []
    
    for chunk in chunks:
        if include_parents:
            # Get surrounding chunks
            full_context = await get_with_context(chunk['id'], window=1)
            context_parts.append(full_context)
        else:
            context_parts.append(chunk['text'])
    
    # Deduplicate overlapping content
    deduplicated = deduplicate_text(context_parts)
    
    return "\n\n---\n\n".join(deduplicated)
```

**When to include parents**:
- Low confidence (need more context)
- Analytical queries (need reasoning chain)
- Chunks contain references ("as mentioned above")

---

# Implementation Roadmap

## Phase 1: Quick Wins (Week 1-2)

| Improvement | Effort | Impact |
|-------------|--------|--------|
| Query intent classification | 1 day | High |
| Overlapping chunks | 1 day | Medium |
| Score-based adaptive K | 1 day | Medium |
| Confidence scoring | 1 day | Medium |

## Phase 2: Core Upgrades (Week 3-4)

| Improvement | Effort | Impact |
|-------------|--------|--------|
| Reranking (Cohere or local) | 2 days | High |
| Semantic chunking | 2 days | Medium |
| Query expansion (hybrid) | 2 days | High |
| Parent-child links | 2 days | Medium |

## Phase 3: Advanced (Week 5-6)

| Improvement | Effort | Impact |
|-------------|--------|--------|
| HyDE embeddings | 1 day | Medium |
| Chunk metadata enrichment | 3 days | Medium |
| Full graph-enhanced retrieval | 3 days | High |
| LLM validation fallback | 2 days | Medium |

---

# Testing & Validation

## Retrieval Quality Metrics

```python
# Precision@K: Of top K results, how many are relevant?
# Recall@K: Of all relevant docs, how many are in top K?
# NDCG: Ranked quality (penalizes relevant docs ranked low)
# MRR: Mean Reciprocal Rank (where does first relevant result appear?)

async def evaluate_retrieval(test_queries: List[dict]) -> dict:
    results = {
        'precision_at_5': [],
        'recall_at_5': [],
        'ndcg_at_10': [],
        'mrr': []
    }
    
    for test in test_queries:
        retrieved = await retrieve(test['query'])
        relevant_set = set(test['relevant_chunk_ids'])
        
        # Calculate metrics...
    
    return {k: mean(v) for k, v in results.items()}
```

## A/B Testing Framework

```python
async def retrieve_ab_test(query: str) -> List[dict]:
    if random.random() < 0.5:
        # Control: current pipeline
        return await current_retrieve(query), "control"
    else:
        # Treatment: new pipeline
        return await new_retrieve(query), "treatment"
```

---

# Decision Points

> [!IMPORTANT]
> **Decisions needed before implementation:**

## Reranking

- [ ] Cohere API ($0.001/query)
- [ ] Local cross-encoder (free, slightly less accurate)
- [ ] LLM-based (expensive, most accurate)

## Query Expansion

- [ ] LLM-based (accurate, adds latency)
- [ ] Synonym-based (fast, limited)
- [ ] Hybrid (recommended)

## HyDE

- [ ] Implement (adds one LLM call per query)
- [ ] Skip (save latency/cost)

## Chunking Changes

- [ ] Migrate existing chunks (requires re-embedding)
- [ ] Apply only to new documents
- [ ] Full re-ingestion

## Confidence Actions

- [ ] Low confidence → Refuse to answer
- [ ] Low confidence → Answer with strong caveat
- [ ] Low confidence → Ask user for clarification

---

# Summary

| Layer | Key Improvement | Expected Impact |
|-------|-----------------|-----------------|
| **Upstream** | Semantic chunking + overlap | -30% context loss |
| **Query** | Intent classification + expansion | -40% vocabulary mismatch |
| **Retrieval** | Reranking + adaptive K | +25% precision |
| **Delivery** | Confidence calibration | -50% confident wrong answers |

**Combined expected improvement: 30-50% reduction in retrieval failures**

---

# Appendix: Cost Analysis

| Feature | Per-Query Cost | Monthly (10K queries) |
|---------|----------------|----------------------|
| Current (vector only) | $0.00 | $0.00 |
| + Reranking (Cohere) | $0.001 | $10 |
| + Query expansion (LLM) | $0.002 | $20 |
| + HyDE | $0.002 | $20 |
| + LLM validation | $0.01 | $100 |
| **Full pipeline** | **~$0.015** | **~$150** |

Most value comes from reranking + query expansion for ~$30/month at 10K queries.

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/rag.py` | Query classification, expansion, retrieval |
| `backend/database.py` | Vector search, graph traversal |
| `backend/semantic_chunker.py` | Chunking strategies |
| `backend/ingestion.py` | Chunk overlap, metadata enrichment |
