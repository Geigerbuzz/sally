---
title: Adaptive Document Categorization System
status: review
type: proposal
created: 2025-12-21
updated: 2025-12-28
tags: [documents, categories, rag, dynamic]
parent: null
children: []
related:
  - ./adaptive_learning_system_proposal.md
  - ../../Implemented/Proposals/self_adapting_rag_proposal.md
  - ../../Implemented/Proposals/legacy_document_management_proposal.md
  - ../../Implemented/Masters/document_lifecycle_master.md
---

# Adaptive Document Categorization System

**Date**: December 21, 2025  
**Status**: Draft — Awaiting Review

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Multi-Category Tagging](#multi-category-tagging) | ⬜ Pending | — | — |
| [Special Category Behavior](#special-category-behavior) | ⬜ Pending | — | — |
| [Positive Signal Detection](#positive-signals-proactive-detection) | ⬜ Pending | — | — |
| [Negative Signal Detection](#negative-signals-problem-detection) | ⬜ Pending | — | — |
| [Admin Inbox Communication](#admin-communication-inbox-only) | ✅ Complete | 2025-12-25 | `database.py:create_inbox_message` |
| [Chunk Overlap](#1-chunk-overlap) | ⬜ Pending | — | — |
| [Citation Confidence Threshold](#2-citation-confidence-threshold) | ⬜ Pending | — | — |
| [Legacy Warning Behavior](#3-legacy-warning-behavior) | ⬜ Pending | — | — |
| [Answer Generation Tone](#5-answer-generation-tone) | ⬜ Pending | — | — |
| [Audit Trail](#6-audit-trail) | ⬜ Pending | — | — |

> **Depends on**: [Adaptive Learning System](./adaptive_learning_system_proposal.md), [Document Lifecycle Master](../../Implemented/Masters/document_lifecycle_master.md)  
> **Affects**: [RAG System](../../Implemented/Masters/rag_system_master.md), [Self-Adapting RAG](../../Implemented/Proposals/self_adapting_rag_proposal.md)

---

## Executive Summary

A **self-learning categorization system** that:

1. Uses dynamic AI-discovered categories
2. Treats `legal` as the only hardcoded special category
3. Learns from **both positive and negative** user signals
4. Communicates with admins via simple **inbox messages** (no dashboard)
5. When a category becomes "special," it affects **multiple system behaviors** — not just overlap

---

## Core Design

### Multi-Category Tagging

Documents can belong to **multiple categories**. This is stored as an array:

```
Document: "property_deed_123_main_st.pdf"
Categories: ["real_estate", "legal"]
```

```
Document: "q4_financial_report.xlsx"
Categories: ["financial", "quarterly_reports"]
```

```
Document: "compliance_policy_v3.pdf"
Categories: ["policies", "compliance", "legal"]
```

### Special Category Behavior

If a document has **ANY special category** in its list, the entire document gets special treatment.

```python
def is_special_document(categories: List[str]) -> bool:
    special_categories = get_special_categories()  # ["legal", ...]
    return any(cat in special_categories for cat in categories)
```

Examples:

| Document | Categories | Has Special? | Overlap |
|----------|------------|--------------|---------|
| property_deed.pdf | `["real_estate", "legal"]` | ✅ Yes (`legal`) | 50% |
| q4_report.xlsx | `["financial"]` | ❌ No | 30% |
| nda_draft.pdf | `["contracts", "legal", "drafts"]` | ✅ Yes (`legal`) | 50% |
| meeting_notes.md | `["internal", "meeting_notes"]` | ❌ No | 30% |

### Default Special Category

`legal` is the only hardcoded special category. Others can be promoted by the system (with admin approval) based on learned patterns.

---

## How the System Learns

### Positive Signals (Proactive Detection)

The system doesn't just wait for problems. It watches for signs that a category is **important to the company**.

#### Signal: High Query Frequency

```
"Users ask about 'compliance' documents 3x more than other categories."
→ This might be a core business function worth special treatment.
```

#### Signal: Citation Trust

```
"When 'financial' documents are cited in answers, users rarely ask follow-ups."
→ Users trust these documents. They're reliable sources.
```

#### Signal: Document Velocity

```
"The 'contracts' category receives 15 new documents per week."
→ This is an active, important area of the business.
```

#### Signal: Cross-Category References

```
"Documents in 'properties' frequently reference documents in 'legal'."
→ These categories are closely linked. Maybe 'properties' needs legal-tier treatment.
```

#### Signal: Query Complexity

```
"Questions about 'technical_specs' tend to be longer and more detailed."
→ Users need comprehensive answers. This category might need more context.
```

### Negative Signals (Problem Detection)

#### Signal: Incomplete Answers
Users get partial information; system couldn't find everything.

#### Signal: Query Refinement
Users immediately rephrase the same question.

#### Signal: Context Expansion
Users frequently click to see more surrounding text.

#### Signal: Document Recovery
Users keep un-archiving documents from this category.

---

## Admin Communication (Inbox Only)

**No dashboards. No technical metrics.** Just simple, friendly messages in the admin's inbox.

### Example Messages

#### Positive Pattern Detected

```
┌────────────────────────────────────────────────────────────────┐
│ 📬 INBOX                                                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 💡 Observation about your documents                            │
│                                                                 │
│ I've noticed that your team asks about "compliance" documents  │
│ more than any other category. This seems to be important to    │
│ your operations.                                                │
│                                                                 │
│ Would you like me to treat compliance documents with extra     │
│ care? This means I'll:                                         │
│   • Keep more context when reading them                        │
│   • Prioritize them in search results                          │
│   • Be more careful about their accuracy                       │
│                                                                 │
│                     [Yes, sounds good]  [No thanks]            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

#### Problem Pattern Detected

```
┌────────────────────────────────────────────────────────────────┐
│ 📬 INBOX                                                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🔧 I might be able to do better                                │
│                                                                 │
│ When answering questions about "technical specifications,"     │
│ I've noticed I sometimes miss important details that are in    │
│ your documents.                                                 │
│                                                                 │
│ I think this is because technical specs often reference other  │
│ sections, and I'm not capturing those connections well.        │
│                                                                 │
│ Would you like me to be more thorough with technical specs?    │
│ This will make my answers more complete, but might take        │
│ slightly longer.                                                │
│                                                                 │
│                     [Yes, be more thorough]  [Keep as is]      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

#### Link Discovery

```
┌────────────────────────────────────────────────────────────────┐
│ 📬 INBOX                                                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🔗 I noticed a connection                                      │
│                                                                 │
│ Your "properties" documents frequently mention things from     │
│ your "legal" documents. They seem closely related.             │
│                                                                 │
│ Right now, I treat "properties" as regular documents. Would    │
│ you like me to treat them with the same care as legal          │
│ documents?                                                      │
│                                                                 │
│                     [Yes, they're related]  [No, keep separate]│
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## What "Special" Status Actually Means

When a category becomes special (either `legal` by default, or promoted by admin), it affects the system in specific ways:

### 1. Chunk Overlap

| Status | Overlap |
|--------|---------|
| Regular | 30% |
| Special | 50% |

More overlap = more context preserved between chunks = better handling of cross-references in legal/important documents.

---

### 2. Citation Confidence Threshold

The system requires **higher confidence** before citing special documents.

```python
def should_cite(chunk: dict, confidence: float) -> bool:
    if is_special_document(chunk['categories']):
        return confidence >= 0.95  # Higher bar for special
    else:
        return confidence >= 0.90  # Normal threshold
```

**Why?** You don't want to cite a legal document unless you're very confident it's relevant. Misattributing legal content is worse than misattributing meeting notes.

---

### 3. Legacy Warning Behavior

When citing a special document that's marked as legacy, the system adds **stronger warnings**.

```python
def format_legacy_warning(source: str, categories: List[str]) -> str:
    if is_special_document(categories):
        return f"⚠️ IMPORTANT: '{source}' may be outdated. Please verify this information is current before relying on it."
    else:
        return f"Note: '{source}' is from an older document."
```

**Why?** Outdated legal/special documents are more dangerous than outdated meeting notes.

---

### 4. Context Window Allocation (Extensive Analysis)

> [!IMPORTANT]
> **This feature has significant potential but also significant risks. The following is a deep analysis.**

#### The Core Idea

When assembling context for the LLM, we have a limited token budget (e.g., 8,000 tokens for context). If retrieved chunks exceed this, we must truncate. The question: **should special-category chunks get priority in that budget?**

#### Scenarios Where This Helps

**Scenario A: Mixed Query with Legal Relevance**
```
Query: "What are the terms for the Johnson property?"
Retrieved:
  - Chunk 1: Contract clause (legal) - 2000 tokens
  - Chunk 2: Meeting notes about Johnson - 1500 tokens  
  - Chunk 3: Email thread about property - 1500 tokens
  - Chunk 4: Another contract clause (legal) - 2000 tokens
Total: 7000 tokens (fits)
```
No truncation needed. Feature doesn't matter.

**Scenario B: Overflow with Legal Content**
```
Query: "Summarize all terms in our contracts"
Retrieved:
  - 5 contract chunks (legal) - 10,000 tokens
  - 3 email threads referencing contracts - 3,000 tokens
Total: 13,000 tokens (must truncate 5,000)
```
Without priority: Might keep emails, truncate contract text.
With priority: Keeps all contract text, truncates emails.
**This is good.** The query is about contracts; emails are secondary.

**Scenario C: Legal Content Irrelevant to Query**
```
Query: "When is the team lunch next week?"
Retrieved:
  - Chunk 1: Email about lunch - 500 tokens
  - Chunk 2: Old contract mentioning lunch expenses (legal) - 2000 tokens
  - Chunk 3: Meeting notes about lunch - 500 tokens
Total: 3000 tokens (fits, but context is polluted)
```
With priority: Legal chunk about "lunch expenses" takes 60% budget.
**This is bad.** The legal chunk is irrelevant noise.

#### Scenarios Where This Hurts

**Scenario D: False Positive Legal Content**
```
Query: "What color should we paint the office?"
Retrieved:
  - Chunk 1: Design discussion - 1000 tokens
  - Chunk 2: Building lease mentioning "alterations" (legal) - 2000 tokens
  - Chunk 3: Paint vendor quote - 500 tokens
Total: 3500 tokens (fits)
```
With priority: Lease clause gets 60% weight in answer.
**Result:** AI might over-emphasize "check your lease before painting" instead of just answering the color question.

**Scenario E: All Regular Content Query**
```
Query: "What did we discuss in last week's standup?"
Retrieved:
  - 4 meeting notes chunks - 4000 tokens
Total: 4000 tokens (fits, no legal content)
```
With priority: No special chunks exist. Feature does nothing.
**Neutral outcome.**

**Scenario F: Competing Important Regular Content**
```
Query: "Compare Q3 and Q4 financial performance"
Retrieved:
  - Q3 report (financial) - 3000 tokens
  - Q4 report (financial) - 3000 tokens  
  - Audit letter (legal) - 2000 tokens
Total: 8000 tokens (borderline)
```
With priority: Audit letter gets 60% weight, squeezing out Q3/Q4 comparison.
**This is bad.** The audit letter is tangentially related; the reports ARE the answer.

#### The Core Problem

**Category-based allocation ignores query intent.**

A document being "legal" doesn't mean it's relevant to THIS question. Priority should be based on:
1. **Relevance to the query** (rerank score)
2. **Category importance** (secondary tiebreaker)

#### Possible Approaches

**Approach 1: Pure Category Priority (Risky)**
```python
# Special = 60%, Regular = 40%
# PROBLEM: Ignores query relevance
```
❌ Not recommended.

**Approach 2: Relevance-First, Category-Tiebreaker**
```python
def allocate_with_tiebreaker(chunks: List[dict], budget: int) -> List[dict]:
    # Sort by relevance score first
    sorted_chunks = sorted(chunks, key=lambda c: c['score'], reverse=True)
    
    # For chunks with similar scores, prefer special categories
    def tiebreaker_key(chunk):
        return (round(chunk['score'], 1), is_special_document(chunk['categories']))
    
    sorted_chunks = sorted(chunks, key=tiebreaker_key, reverse=True)
    
    # Take as many as fit in budget
    return take_until_budget(sorted_chunks, budget)
```
✅ Special content wins ties, but relevance still rules.

**Approach 3: Query-Aware Allocation**
```python
def allocate_query_aware(query: str, chunks: List[dict], budget: int) -> List[dict]:
    # Detect if query is about legal/formal matters
    query_wants_legal = detect_legal_intent(query)  # "terms", "contract", "agreement"
    
    if query_wants_legal:
        # Give special chunks priority
        return allocate_with_special_priority(chunks, budget, special_share=0.7)
    else:
        # Use pure relevance
        return allocate_by_relevance(chunks, budget)
```
✅ Only prioritizes special when query implies it.

**Approach 4: No Category-Based Allocation**
```python
# Just use relevance scores. Special categories already have:
# - 50% overlap (more context captured)
# - 95% citation threshold (more careful sourcing)
# Let relevance determine what matters for THIS query.
```
✅ Simplest. Let other special behaviors do the work.

#### Recommendation

**Use Approach 2 (Relevance-First, Category-Tiebreaker) OR Approach 4 (No Allocation).**

Reasoning:
- Special categories already benefit from 50% overlap (better chunking)
- Forcing allocation based on category creates query-blind behavior
- If two chunks have similar relevance, preferring legal is reasonable
- If a legal chunk has LOW relevance, it shouldn't get priority

#### Decision Matrix

| Approach | Query Accuracy | Implementation | Risk |
|----------|----------------|----------------|------|
| Pure category priority | 🔴 Low | Easy | High |
| Relevance + tiebreaker | 🟢 High | Medium | Low |
| Query-aware allocation | 🟢 High | Complex | Medium |
| No allocation | 🟢 High | None | None |

**Status:** Recommend Approach 2 or 4. Await decision.

---

### 5. Answer Generation Tone

When answers are primarily based on special documents, the AI uses **more careful language**.

```
Regular category answer:
"The meeting is scheduled for Friday at 3pm."

Special category answer:
"According to the contract dated March 15, 2025, the delivery deadline is 
set for Friday at 3pm. Please verify this against the original document 
for any critical decisions."
```

**Why?** Emphasize that this is important information that should be verified.

---

### 6. Audit Trail

Queries involving special documents get **enhanced logging**.

```python
async def log_query(query: str, sources: List[str], answer: str):
    categories_per_source = [get_categories(s) for s in sources]
    
    if any(is_special_document(cats) for cats in categories_per_source):
        await audit_log.create({
            'query': query,
            'sources': sources,
            'answer': answer,
            'timestamp': datetime.now(),
            'user': current_user,
            'special_categories': get_special_categories_used(categories_per_source)
        })
```

#### Why Audit Trail? Benefits Explained

**1. Compliance & Regulatory Requirements**
Many industries (finance, healthcare, legal, real estate) require tracking who accessed what sensitive information and when. An audit trail provides:
- Proof of due diligence
- Evidence for regulatory audits
- Documentation for legal discovery

**2. Accountability & Trust**
When decisions are based on legal documents, you want a record:
- Who asked about contract terms before a negotiation?
- What was the system's answer when someone queried the NDA?
- If something goes wrong, what information was provided?

**3. Quality Improvement**
Over time, the audit trail enables:
- Identifying which legal docs are queried most (training priorities)
- Spotting patterns in how users phrase legal questions
- Finding gaps where answers were incomplete

**4. Dispute Resolution**
If someone claims "the system told me X," the audit trail provides:
- Exact query text
- Exact answer given
- Sources that were cited
- Timestamp

**5. User Behavior Insights**
Understanding how teams interact with legal documents:
- Which departments query contracts most?
- Are the same documents queried repeatedly (maybe needs summarization)?
- Are there seasonal patterns in legal queries?

---

## Summary: What Changes When a Category Becomes Special

| Behavior | Regular Category | Special Category |
|----------|------------------|------------------|
| **Chunk overlap** | 30% | 50% |
| **Citation threshold** | 90% confidence | 95% confidence |
| **Legacy warnings** | Subtle | Strong warning |
| **Context allocation** | Standard | *Tentative (needs thought)* |
| **Answer tone** | Casual | Careful, verified |
| **Audit logging** | Standard | Enhanced |

### Removed from Proposal

The following were considered but **not included**:
- ~~Retrieval priority boost~~ — Let relevance speak for itself
- ~~Permanence protection~~ — AI should determine permanence fairly
- ~~Version supersession confirmation~~ — Keep process simple
- ~~Reranking behavior changes~~ — Unnecessary complexity

---

## Learning Thresholds

Before the system sends an inbox message, it requires:

- **Minimum observation period**: 14 days
- **Confidence threshold**: Pattern must appear in 60%+ of interactions

This prevents premature suggestions and gives the system enough time to observe meaningful patterns.

---

## Implementation Priority

### Phase 1: Core
- Multi-category tagging system
- `legal` = special (hardcoded)
- 50%/30% overlap

### Phase 2: Special Category Effects
- Citation threshold adjustment
- Legacy warnings
- Answer tone
- Audit trail

### Phase 3: Learning & Inbox
- Signal collection (positive + negative)
- Inbox message generation
- Admin approval flow

### Future Consideration
- Context window allocation (after more analysis)

---

## Open Questions

> [!NOTE]
> **Decisions needed:**
>
> 1. Is 14 days + 30 interactions the right threshold before suggesting category promotion?
> 2. Should positive signals (high query frequency) have equal weight to negative signals (incomplete answers)?
> 3. Do we need audit trail from day 1, or can it be Phase 2?

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/ingestion.py` | Category assignment, overlap settings |
| `backend/rag.py` | Citation thresholds, answer tone |
| `backend/database.py` | Multi-category storage, audit trail |
| `backend/document_lifecycle.py` | Legacy warnings, special category effects |
| `backend/learning_engine.py` | Signal detection, promotion workflows |

