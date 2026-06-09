---
title: Confidence-Calibrated Retrieval
status: draft
type: proposal
created: 2025-12-21
updated: 2025-12-28
tags: [rag, retrieval, confidence, calibration]
parent: null
children: []
related:
  - ./advanced_rag_enhancements_proposal.md
  - ./rag_retrieval_improvements_proposal.md
  - ../../Implemented/Proposals/self_adapting_rag_proposal.md
---

# Confidence-Calibrated Retrieval: Technical Proposal

**Date**: December 21, 2025  
**Status**: Draft — Awaiting Review  
**Risk Level**: 🟠 Medium-High (affects answer quality directly)

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Score Thresholds (Approach A)](#approach-a-score-thresholds-simple) | ⬜ Pending | — | — |
| [Cumulative Confidence (Approach B)](#approach-b-cumulative-confidence-theoretical) | ⬜ Pending | — | — |
| [Query-Aware Retrieval (Approach C)](#approach-c-query-aware-retrieval-recommended) | ✅ Complete | 2025-12-21 | `rag.py:get_retrieval_strategy` |
| [LLM Validation (Approach D)](#approach-d-llm-validated-retrieval-most-reliable-most-expensive) | ⬜ Pending | — | — |
| [Hard Limits & Safeguards](#safeguards--guardrails) | ⬜ Pending | — | — |
| [No Good Answer Detection](#3-no-good-answer-detection) | ⬜ Pending | — | — |
| [Shadow Mode Logging](#phase-1-shadow-mode-1-week) | ⬜ Pending | — | — |

> **Depends on**: [RAG Retrieval Improvements](./rag_retrieval_improvements_proposal.md#layer-3-retrieval)  
> **Affects**: [Advanced RAG Enhancements](./advanced_rag_enhancements_proposal.md), [RAG System Master](../../Implemented/Masters/rag_system_master.md)

---

## Executive Summary

This proposal outlines the implementation of **Confidence-Calibrated Retrieval** — a dynamic approach to document retrieval that adjusts the number of chunks retrieved based on confidence thresholds rather than using a fixed top-K approach.

> [!CAUTION]
> **Getting this wrong can cause:**
> - **Under-retrieval**: Missing critical information → incomplete/wrong answers
> - **Over-retrieval**: Including irrelevant context → confused AI, slower responses
> - **Inconsistent behavior**: Same question returns different depths of information
> - **Confidence miscalibration**: System thinks it's confident when it shouldn't be

---

## Current State

```
User Query → Vector Search → Top 5 Chunks → LLM → Response
                    ↓
            (Always exactly 5,
             regardless of query
             complexity or match quality)
```

**Problems with fixed top-K:**

| Scenario | What Happens | Ideal Behavior |
|----------|--------------|----------------|
| Simple factual question | Returns 5 chunks, 4 are noise | Should return 1-2 high-relevance chunks |
| Complex analytical question | Returns 5 chunks, misses context | Should retrieve 10-15 chunks |
| Ambiguous question | Returns 5 semi-relevant chunks | Should either clarify OR retrieve broadly |
| No good matches exist | Returns 5 low-quality chunks | Should indicate low confidence / ask for clarification |

---

## Proposed Enhancement

Replace fixed top-K with **adaptive retrieval** that adjusts based on confidence signals.

```
User Query → Vector Search → Confidence Analysis → Dynamic K → LLM → Response
                                    ↓
                          "How confident are we in these results?"
                                    ↓
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              High Match      Medium Match      Low Match
              (score > 0.8)   (0.5-0.8)        (< 0.5)
                    ↓               ↓               ↓
              Return 2-3      Return 5-7       Return 10+
              chunks          chunks           OR ask user
```

---

## Risk Analysis

### Risk 1: Stopping Too Early (Under-Retrieval)

**Scenario**: First chunk scores 0.85 (high), so system returns only 2 chunks. But the full answer requires information from chunk #7.

**Example**:
```
Q: "What are all the warranty terms in our contracts?"
Top 1 chunk: "Standard warranty is 12 months" (score: 0.87)
Chunks 5-8: Additional warranty terms for different product lines (scores: 0.5-0.6)
```

**If we stop early**: User gets incomplete answer, missing 60% of warranty terms.

**Mitigation Options**:
- [ ] Option A: Never return fewer than 5 chunks (floor)
- [ ] Option B: Detect "comprehensive" queries ("all", "every", "list") → force broad retrieval
- [ ] Option C: Check if top chunk fully answers query before stopping

---

### Risk 2: Expanding Too Much (Over-Retrieval)

**Scenario**: Low initial scores trigger expansion to 15+ chunks, but most are truly irrelevant.

**Example**:
```
Q: "What is the interest rate?"
Top 1 chunk: Score 0.45 (talks about "interesting" results, not interest rates)
System: "Low confidence, expand search!"
Returns 15 chunks, all about "interesting" things, zero about interest rates
```

**If we over-expand**: LLM gets confused, may hallucinate, response time increases.

**Mitigation Options**:
- [ ] Option A: Set maximum expansion limit (e.g., never more than 15)
- [ ] Option B: Validate expanded results still match query semantically
- [ ] Option C: If all scores low after expansion, return "I don't have information about this"

---

### Risk 3: Confidence Miscalibration

**Scenario**: Vector similarity scores don't accurately reflect answer quality.

**Example**:
```
Q: "How much did we pay for the Smith property?"
Top chunk: "The Smith family has been clients for 10 years" (score: 0.82)
```

High score because "Smith" matches, but chunk doesn't answer the question at all.

**Mitigation Options**:
- [ ] Option A: Use LLM to validate "does this chunk answer the question?" before returning
- [ ] Option B: Combine vector score with keyword matching
- [ ] Option C: Track historical accuracy per score range

---

### Risk 4: Inconsistent User Experience

**Scenario**: Same question returns different amounts of information on different runs.

**Example**:
```
Day 1: "Tell me about Project Alpha" → Returns 3 chunks (high-confidence match found)
Day 2: "Tell me about Project Alpha" → Returns 12 chunks (new documents uploaded, scores distributed differently)
```

**User perception**: "Why did I get more detail yesterday?"

**Mitigation Options**:
- [ ] Option A: Cache retrieval patterns per query signature
- [ ] Option B: Use consistent K but apply confidence for filtering
- [ ] Option C: Always show "confidence level" to user so they understand variability

---

## Implementation Approaches

### Approach A: Score Thresholds (Simple)

**How it works**: Define score bands that determine how many chunks to return.

```python
def calculate_dynamic_k(scores: List[float]) -> int:
    top_score = scores[0]
    
    if top_score >= 0.85:
        return 3  # Very confident, minimal context needed
    elif top_score >= 0.70:
        return 5  # Standard confidence
    elif top_score >= 0.50:
        return 8  # Lower confidence, need more context
    else:
        return 12  # Low confidence, retrieve broadly
```

| Pros | Cons |
|------|------|
| Simple to implement | Arbitrary thresholds |
| Predictable behavior | Doesn't consider score distribution |
| Easy to tune | Ignores query complexity |

**Risk Level**: 🟡 Medium

---

### Approach B: Cumulative Confidence (Theoretical)

**How it works**: Keep retrieving until cumulative confidence exceeds threshold.

```python
def retrieve_until_confident(scores: List[float], threshold: float = 0.95) -> int:
    cumulative = 0.0
    for i, score in enumerate(scores):
        cumulative += score / sum(scores)  # Normalize
        if cumulative >= threshold:
            return i + 1
    return len(scores)
```

| Pros | Cons |
|------|------|
| Theoretically elegant | Math doesn't map to real confidence |
| Adapts to score distribution | Can still stop too early |
| Based on relative scores | Hard to explain to users |

**Risk Level**: 🟠 Medium-High

---

### Approach C: Query-Aware Retrieval (Recommended)

**How it works**: Analyze query intent FIRST, then adjust retrieval strategy.

```python
def get_retrieval_strategy(query: str) -> dict:
    """Determine retrieval strategy based on query analysis."""
    
    # Step 1: Classify query type
    query_lower = query.lower()
    
    # Comprehensive queries need broad retrieval
    if any(word in query_lower for word in ["all", "every", "list", "compare", "summarize"]):
        return {"min_k": 8, "max_k": 20, "score_floor": 0.3}
    
    # Factual queries need precision
    if any(word in query_lower for word in ["what is", "how much", "when did", "who is"]):
        return {"min_k": 3, "max_k": 8, "score_floor": 0.5}
    
    # Analytical queries need depth
    if any(word in query_lower for word in ["why", "analyze", "explain", "how does"]):
        return {"min_k": 5, "max_k": 12, "score_floor": 0.4}
    
    # Default: balanced
    return {"min_k": 5, "max_k": 10, "score_floor": 0.4}


def dynamic_retrieve(query: str, all_results: List[dict]) -> List[dict]:
    strategy = get_retrieval_strategy(query)
    
    # Filter by score floor
    valid_results = [r for r in all_results if r['score'] >= strategy['score_floor']]
    
    # Apply bounds
    k = max(strategy['min_k'], min(len(valid_results), strategy['max_k']))
    
    return valid_results[:k]
```

| Pros | Cons |
|------|------|
| Query-aware, not just score-aware | More complex logic |
| Explicit bounds prevent extremes | Keyword matching isn't perfect |
| Explainable strategy | Needs tuning over time |

**Risk Level**: 🟢 Lower

---

### Approach D: LLM-Validated Retrieval (Most Reliable, Most Expensive)

**How it works**: Use LLM to validate each chunk's relevance before including.

```python
async def validated_retrieve(query: str, candidates: List[dict], max_k: int = 10) -> List[dict]:
    validated = []
    
    for chunk in candidates[:max_k * 2]:  # Check more than needed
        # Quick LLM validation
        is_relevant = await llm_check_relevance(query, chunk['text'])
        
        if is_relevant:
            validated.append(chunk)
            if len(validated) >= max_k:
                break
    
    return validated

async def llm_check_relevance(query: str, chunk_text: str) -> bool:
    prompt = f"""
    Query: {query}
    Document chunk: {chunk_text[:500]}
    
    Does this chunk contain information that helps answer the query? 
    Reply ONLY 'yes' or 'no'.
    """
    response = await model.generate_content_async(prompt)
    return 'yes' in response.text.lower()
```

| Pros | Cons |
|------|------|
| Most accurate | Expensive (extra API calls) |
| Catches semantic mismatches | Adds latency |
| LLM understands query intent | May reject relevant chunks |

**Risk Level**: 🟢 Lowest (but highest cost)

---

## Recommended Approach: Hybrid C + D

Use **Approach C (Query-Aware)** as the primary method, with **Approach D (LLM Validation)** as a fallback for low-confidence scenarios.

```python
async def confidence_calibrated_retrieve(query: str, all_results: List[dict]) -> List[dict]:
    # Step 1: Query-aware strategy
    strategy = get_retrieval_strategy(query)
    
    # Step 2: Initial filtering
    valid_results = [r for r in all_results if r['score'] >= strategy['score_floor']]
    
    # Step 3: Check if we're in a low-confidence scenario
    top_score = valid_results[0]['score'] if valid_results else 0
    
    if top_score < 0.5:
        # Low confidence: validate with LLM
        return await validated_retrieve(query, all_results, strategy['max_k'])
    else:
        # Standard: use query-aware bounds
        k = max(strategy['min_k'], min(len(valid_results), strategy['max_k']))
        return valid_results[:k]
```

---

## Safeguards & Guardrails

### 1. Hard Limits
```python
MIN_CHUNKS = 3   # Never return fewer (prevents under-retrieval)
MAX_CHUNKS = 15  # Never return more (prevents context overload)
```

### 2. Score Floor Protection
```python
ABSOLUTE_SCORE_FLOOR = 0.25  # Below this = definitely irrelevant
```

### 3. "No Good Answer" Detection
```python
if all(r['score'] < 0.4 for r in top_results):
    return {
        "answer": "I don't have confident information about this topic.",
        "confidence": "low",
        "suggestion": "Try rephrasing or check if relevant documents are uploaded."
    }
```

### 4. Logging & Monitoring
```python
# Log retrieval decisions for analysis
logger.info(f"Query: {query}")
logger.info(f"Strategy: {strategy}")
logger.info(f"Top score: {top_score}, Returned K: {len(results)}")
```

---

## Testing Strategy

### Unit Tests
- [ ] Query classification correctly identifies comprehensive/factual/analytical queries
- [ ] Score filtering respects floor thresholds
- [ ] Bounds (min_k, max_k) are always respected

### Integration Tests
- [ ] Simple factual query → returns 3-5 chunks
- [ ] "List all X" query → returns 8-15 chunks
- [ ] No-match scenario → returns low-confidence message

### Regression Tests
- [ ] Compare answers before/after on 50 sample queries
- [ ] Ensure no degradation in answer quality
- [ ] Measure response time impact

### Edge Cases
- [ ] Empty database → graceful handling
- [ ] Single chunk available → returns it
- [ ] All chunks have same score → uses min_k

---

## Rollout Plan

### Phase 1: Shadow Mode (1 week)
- Implement logic but don't change actual retrieval
- Log "what we would have done" vs current fixed-K
- Analyze differences

### Phase 2: A/B Test (1 week)
- 50% of queries use new system
- Compare user satisfaction, answer quality
- Monitor for issues

### Phase 3: Full Rollout
- Switch all queries to dynamic retrieval
- Keep fixed-K as fallback option
- Monitor and tune thresholds

---

## Decision Points

> [!IMPORTANT]
> **Decisions needed before implementation:**

1. **Which approach?**
   - [ ] A: Simple score thresholds (fastest to implement)
   - [ ] B: Cumulative confidence (theoretical elegance)
   - [ ] C: Query-aware retrieval (recommended balance)
   - [ ] D: LLM validation (most reliable, most expensive)
   - [ ] C+D Hybrid (recommended)

2. **Hard limits:**
   - Min chunks: 3? 5?
   - Max chunks: 10? 15? 20?
   - Score floor: 0.25? 0.3? 0.4?

3. **Low-confidence behavior:**
   - [ ] Return best available with warning
   - [ ] Ask user for clarification
   - [ ] Expand search silently
   - [ ] Refuse to answer

4. **Rollout strategy:**
   - [ ] Direct deployment (faster)
   - [ ] Shadow mode first (safer)
   - [ ] A/B test (data-driven)

---

## Summary

| Aspect | Recommendation |
|--------|----------------|
| **Approach** | Hybrid C+D (Query-aware + LLM validation fallback) |
| **Risk** | 🟡 Medium with proper safeguards |
| **Effort** | 3-5 days |
| **Testing Required** | Extensive regression testing |
| **Rollout** | Shadow mode → A/B test → Full |

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/rag.py` | Retrieval strategy, confidence scoring |
| `backend/database.py` | Vector search, score handling |
