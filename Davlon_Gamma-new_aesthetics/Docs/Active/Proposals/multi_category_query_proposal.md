---
title: Multi-Category Query Classification
status: draft
type: proposal
created: 2025-12-21
updated: 2025-12-28
tags: [rag, query, classification, categories]
parent: null
children: []
related:
  - ./unified_document_labeling_proposal.md
  - ./adaptive_learning_system_proposal.md
---

# Multi-Category Query Classification Proposal

**Date**: December 21, 2025  
**Status**: Draft - Awaiting Review

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Multi-Category Detection](#multi-category-detection) | ✅ Complete | 2025-12-25 | `rag.py:classify_query_multi` |
| [Special Category Boost](#feature-1-special-category-context-boost) | ✅ Complete | 2025-12-25 | `rag.py:QueryClassification.has_special` |
| [Unknown Topic Logging](#feature-2-unknown-topic-logging) | ✅ Complete | 2025-12-25 | `database.py:log_unknown_topic` |
| [Alias/Synonym Detection](#aliassynonym-detection) | ✅ Complete | 2025-12-25 | `database.py:_normalize_topic` |
| [Knowledge Gap Alerts](#feature-3-knowledge-gap-detection--alerts) | ⬜ Pending | — | — |
| [Category Suggestions](#feature-4-category-suggestion-from-gaps) | ⬜ Pending | — | — |

> **Depends on**: [RAG System Master](../../Implemented/Masters/rag_system_master.md), [Unified Labeling](./unified_document_labeling_proposal.md)  
> **Affects**: [Adaptive Learning](./adaptive_learning_system_proposal.md), [Confidence Calibrated Retrieval](./confidence_calibrated_retrieval_proposal.md)

---

## Executive Summary

Enhance query processing to:

1. **Detect ALL relevant categories** in a question (not just one)
2. **Boost context for special categories** when detected
3. **Log missing categories** when users ask about topics we don't have
4. **Alert admins** when recurring knowledge gaps are detected

---

## Current State

```python
# Current: Returns ONE category
async def _classify_query(self, user_query: str) -> str:
    prompt = """Which document category is MOST relevant?
    Respond with ONLY the category name."""
    # Returns: "contracts" (single string)
```

**Problems:**
- "What are the contract terms for the Johnson property?" involves BOTH `contracts` AND `real_estate`
- If user asks about something we don't have, we just fail silently
- No tracking of knowledge gaps

---

## Proposed Solution

### Multi-Category Detection

```python
async def classify_query_multi(self, query: str) -> QueryClassification:
    """
    Detect ALL relevant categories in a query.
    
    Returns:
        QueryClassification with:
        - detected_categories: List of categories found in query
        - has_special: Whether any detected category is special
        - unknown_topics: Topics mentioned that don't match any category
    """
    available_categories = await db.get_unique_categories()
    special_categories = await db.get_special_categories()  # ["legal", ...]
    
    prompt = f"""Analyze this user question and identify:
    
    1. ALL document categories that are relevant (from the available list)
    2. Any topics mentioned that DON'T match available categories
    
    Available categories: {', '.join(available_categories)}
    
    User question: "{query}"
    
    Respond in JSON:
    {{
        "categories": ["category1", "category2"],
        "unknown_topics": ["topic_not_in_categories"]
    }}
    """
    
    response = await model.generate_content_async(prompt)
    result = parse_json(response.text)
    
    detected = [c for c in result['categories'] if c in available_categories]
    unknown = result.get('unknown_topics', [])
    has_special = any(c in special_categories for c in detected)
    
    return QueryClassification(
        detected_categories=detected,
        has_special=has_special,
        unknown_topics=unknown
    )
```

---

## Feature 1: Special Category Context Boost

When a special category (like `legal`) is detected in the query, allocate more context to documents from that category.

```python
async def retrieve_with_category_awareness(query: str) -> List[dict]:
    classification = await classify_query_multi(query)
    
    # Standard retrieval
    all_chunks = await vector_search(query, k=30)
    
    if classification.has_special:
        # Sort: special category chunks first (at same relevance level)
        def sort_key(chunk):
            is_special = any(
                cat in classification.detected_categories 
                for cat in chunk['categories'] 
                if cat in special_categories
            )
            return (-chunk['score'], -int(is_special))
        
        all_chunks = sorted(all_chunks, key=sort_key)
    
    return all_chunks[:15]
```

**Example:**
```
Query: "What are the contract terms for the Johnson property?"
Detected: ["contracts", "real_estate"]
Has special: Yes (contracts → legal)
Result: Contract clauses get priority in context window
```

---

## Feature 2: Unknown Topic Logging

Unknown topics are logged on **every query** where they're detected.

```python
async def log_unknown_topic(topic: str, query: str):
    """Log when a user asks about something we don't have."""
    
    # First, check if this topic is an alias of an existing unknown topic
    canonical_topic = await normalize_topic(topic)
    
    await db.run_query("""
        MERGE (t:UnknownTopic {name: $topic})
        ON CREATE SET t.first_seen = datetime(), t.count = 1
        ON MATCH SET t.count = t.count + 1, t.last_seen = datetime()
        
        CREATE (q:QueryLog {text: $query, timestamp: datetime()})
        MERGE (q)-[:MENTIONED]->(t)
    """, topic=canonical_topic, query=query)
```

### Alias/Synonym Detection

Before logging, the system checks if the topic is a known synonym of an existing unknown topic.

```python
async def normalize_topic(topic: str) -> str:
    """
    Check if this topic is an alias of an existing unknown topic.
    
    Examples:
      - "MVP" → "minimum_viable_product" (if that exists)
      - "Minimum Viable Product" → "minimum_viable_product" (normalization)
      - "ROI" → "return_on_investment"
    """
    # Get existing unknown topics
    existing_topics = await db.run_query("""
        MATCH (t:UnknownTopic)
        RETURN t.name as name, t.aliases as aliases
    """)
    
    # Check for semantic similarity with existing topics
    for existing in existing_topics:
        if is_semantic_match(topic, existing['name']):
            return existing['name']
        if existing['aliases'] and topic.lower() in [a.lower() for a in existing['aliases']]:
            return existing['name']
    
    # Use LLM to check for acronym/synonym match
    prompt = f"""Is "{topic}" an acronym or synonym for any of these existing topics?
    
    Existing topics: {[t['name'] for t in existing_topics]}
    
    If yes, respond with the matching topic name.
    If no, respond with "NEW".
    """
    
    response = await model.generate_content_async(prompt)
    result = response.text.strip()
    
    if result != "NEW" and result in [t['name'] for t in existing_topics]:
        # Also store this as an alias for future quick lookup
        await db.run_query("""
            MATCH (t:UnknownTopic {name: $existing})
            SET t.aliases = COALESCE(t.aliases, []) + $new_alias
        """, existing=result, new_alias=topic)
        return result
    
    # Normalize the new topic (lowercase, underscores)
    return topic.lower().replace(" ", "_").replace("-", "_")
```

**Example:**
```
Query 1: "What's our MVP timeline?" → logs "minimum_viable_product"
Query 2: "When do we launch the minimum viable product?" → matches existing, increments count
Query 3: "What about the Minimum Viable Product?" → matches existing, increments count
```

**Data Model:**
```cypher
(:UnknownTopic {
    name: "minimum_viable_product",
    aliases: ["MVP", "min viable product"],  // ← NEW: Tracked aliases
    count: 12,
    first_seen: datetime(),
    last_seen: datetime()
})

(:QueryLog)-[:MENTIONED]->(:UnknownTopic)
```
```

---

## Feature 3: Knowledge Gap Detection & Alerts

When unknown topics are mentioned repeatedly, notify admins.

### Detection Logic

```python
async def check_knowledge_gaps():
    """Periodic check for recurring knowledge gaps."""
    gaps = await db.run_query("""
        MATCH (t:UnknownTopic)
        WHERE t.count >= 3 
        AND t.last_seen > datetime() - duration('P7D')
        AND NOT t.notified
        RETURN t.name as topic, t.count as mentions
        ORDER BY t.count DESC
        LIMIT 5
    """)
    
    for gap in gaps:
        await send_knowledge_gap_alert(gap['topic'], gap['mentions'])
        await mark_as_notified(gap['topic'])
```

### Inbox Message Format

```
┌────────────────────────────────────────────────────────────────┐
│ 📬 INBOX                                                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📊 I noticed a knowledge gap                                   │
│                                                                 │
│ Users have asked about "market analysis" 5 times in the        │
│ past week, but I don't have any documents about this            │
│ topic.                                                          │
│                                                                 │
│ Example questions I couldn't fully answer:                      │
│ • "What does the market analysis say about Q4?"                │
│ • "Can you summarize our market research?"                     │
│                                                                 │
│ Is this relevant to your company? If so, uploading documents   │
│ about market analysis would help me answer these questions     │
│ better.                                                         │
│                                                                 │
│          [Yes, remind me later]  [Not relevant, ignore]        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Feature 4: Category Suggestion from Gaps

When a gap is acknowledged, offer to create the category proactively.

```
┌────────────────────────────────────────────────────────────────┐
│ 📬 INBOX                                                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📁 Ready to help                                               │
│                                                                 │
│ You mentioned "market analysis" is relevant. Would you like    │
│ me to create a category for it now?                            │
│                                                                 │
│ Once you upload documents about market analysis, I'll          │
│ automatically organize them and be ready to answer questions.  │
│                                                                 │
│              [Create "market_analysis" category]               │
│              [I'll upload documents first]                     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## How Multi-Category Detection Helps Context Allocation

With multi-category detection, we can make smarter decisions:

```python
async def allocate_context_smart(query: str, chunks: List[dict], budget: int):
    classification = await classify_query_multi(query)
    
    # If query explicitly mentions special category, boost it
    if classification.has_special:
        # Use Approach 2: Relevance-first with special tiebreaker
        return allocate_with_special_tiebreaker(
            chunks, 
            budget, 
            priority_categories=classification.detected_categories
        )
    else:
        # Pure relevance-based
        return allocate_by_relevance(chunks, budget)
```

This solves the Context Window Allocation problem we discussed earlier:
- **Query about contracts** → Boost legal/contract chunks ✅
- **Query about team lunch** → Don't boost irrelevant legal chunks ✅

---

## Complete Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Query: "What are the contract terms for the Johnson       │
│             property we discussed last week?"                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Multi-Category Classification                                   │
├─────────────────────────────────────────────────────────────────┤
│ detected_categories: ["contracts", "real_estate"]               │
│ has_special: true (contracts → legal-like)                      │
│ unknown_topics: []                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Smart Retrieval                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. Vector search → 30 candidates                                │
│ 2. Rerank by relevance                                          │
│ 3. Tiebreaker: Prefer chunks from ["contracts", "real_estate"] │
│ 4. Special category boost for context allocation               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Context Assembly                                                │
├─────────────────────────────────────────────────────────────────┤
│ Contract clauses: 60% of budget                                 │
│ Property details: 30% of budget                                 │
│ Meeting notes: 10% of budget                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Answer Generation (with careful tone for legal content)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Unknown Topic Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Query: "What does our market analysis say about           │
│             the downtown area?"                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Multi-Category Classification                                   │
├─────────────────────────────────────────────────────────────────┤
│ detected_categories: ["real_estate"]                            │
│ has_special: false                                              │
│ unknown_topics: ["market_analysis"]  ← NOT in our categories   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Log Unknown Topic                                               │
├─────────────────────────────────────────────────────────────────┤
│ topic: "market_analysis"                                        │
│ count: 5 (previously asked 4 times)                             │
│ → Threshold reached! Queue inbox message.                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Best-Effort Answer                                              │
├─────────────────────────────────────────────────────────────────┤
│ "I found some information about the downtown area in your      │
│ real estate documents, but I don't have dedicated market       │
│ analysis documents. Here's what I found: ..."                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Benefits Summary

| Feature | Benefit |
|---------|---------|
| **Multi-category detection** | Better retrieval for complex queries |
| **Special category boost** | Query-aware context allocation (solves our earlier problem) |
| **Unknown topic logging** | Visibility into knowledge gaps |
| **Admin alerts** | Proactive improvement of the knowledge base |
| **Category suggestions** | Lower friction to add new categories |

---

## Implementation Priority

### Phase 1: Multi-Category Detection
- Update `_classify_query()` to return multiple categories
- Update retrieval to use all detected categories

### Phase 2: Special Category Context Boost
- Implement query-aware context allocation
- Use Approach 2 (relevance + tiebreaker) when special detected

### Phase 3: Unknown Topic System
- Add `UnknownTopic` nodes to Neo4j
- Implement logging on every query
- Periodic gap detection job

### Phase 4: Admin Alerts
- Inbox integration for knowledge gap alerts
- Category creation workflow

---

## Decisions Made

| Question | Decision |
|----------|----------|
| Log on every query or only incomplete? | **Every query** |
| Threshold for alerting | **3 mentions in 7 days** |
| Auto-create empty categories? | *Deferred — see reminders doc* |

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/rag.py` | Query classification, multi-category detection |
| `backend/database.py` | Category queries, UnknownTopic storage |
| `backend/main.py` | Knowledge gap detection job |
