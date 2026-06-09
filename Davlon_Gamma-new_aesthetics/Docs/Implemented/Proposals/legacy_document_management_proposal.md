---
title: Legacy Document Management
status: implemented
type: proposal
created: 2025-12-27
updated: 2025-12-27
tags: [documents, lifecycle, rag, search]
implemented_in: backend/document_lifecycle.py
related:
  - Docs/Implemented/Proposals/data_sources_ux_proposal.md
  - Docs/Implemented/Masters/document_lifecycle_master.md
---

# Legacy Document Management Proposal

## Context

This document explores how the system should handle "legacy" documents—documents that have been deprioritized due to age, supersession, or low permanence scores.

Key constraints from previous discussion:
- Users should NOT be overwhelmed with options
- One-click recovery from Legacy status (system learns from this)
- Inbox notifications only when system is genuinely uncertain
- No manual permanence score assignment

---

## What is a "Legacy" Document?

A document enters Legacy status when:
1. **Superseded**: A newer version exists (`contract_v1` → `contract_v2`)
2. **Decayed**: Temporal decay + low permanence score pushed it below threshold
3. **Explicitly archived**: User marked it as obsolete (future feature)

---

## Option 1: Soft Exclusion (Recommended)

**Concept**: Legacy documents remain indexed and searchable, but are deprioritized—not hidden.

### How It Works

| Status | In Default Search | In "Include Legacy" Search | User Visibility |
|--------|-------------------|---------------------------|-----------------|
| Active | ✅ Full weight | ✅ Full weight | Normal |
| Legacy | ⚠️ 90% decay | ✅ Full weight | Faded/labeled |

### Query Behavior

```
Default Query: "What are the property boundaries?"
→ Searches Active documents first
→ Legacy docs heavily deprioritized but not excluded
→ If no good Active results, may return Legacy with warning

Explicit Query: "What are the property boundaries? [include legacy]"
→ Searches all documents equally
→ Legacy results labeled as such
```

### UI Implications

- **RAG Response**: If citing a Legacy doc, add warning:
  > ⚠️ This information is from a legacy document (contract_v1.pdf, superseded 2024-03-15). Verify currency.

- **Document List**: Legacy docs shown in separate "Legacy" section or with visual indicator

### Pros
- Never lose access to historical data
- Users can always find old information if needed
- Minimal user friction

### Cons
- Users might accidentally rely on outdated info without noticing

---

## Option 2: Hard Exclusion with Recovery

**Concept**: Legacy documents are excluded from all searches by default, but remain in the system for recovery.

### How It Works

| Status | In Default Search | Recoverable | Storage |
|--------|-------------------|-------------|---------|
| Active | ✅ | N/A | Neo4j + Vector Index |
| Legacy | ❌ | ✅ One-click | Neo4j only (no vector search) |

### Query Behavior

```
Default Query: "What are the property boundaries?"
→ Only searches Active documents
→ Legacy documents are never returned

Recovery Query (UI button): "Show legacy versions of this document"
→ Returns all superseded versions
```

### Recovery Flow

1. User goes to **Legacy Documents** section
2. Sees list of documents with reason (superseded, decayed, etc.)
3. Clicks **"Restore"** on any document
4. System:
   - Moves doc back to Active
   - Increases its permanence score (learns this doc type shouldn't decay)
   - Logs for future learning

### Pros
- Clean separation—users only see current data by default
- No risk of accidental reliance on outdated info
- Clear mental model

### Cons
- Users might forget legacy docs exist
- Extra step to access historical data

---

## Option 3: Tiered Legacy (Hybrid)

**Concept**: Multiple levels of "legacy" with different treatment.

### Tiers

| Tier | Criteria | Search Behavior | Recovery |
|------|----------|-----------------|----------|
| **Active** | Permanence > 0.5, not superseded | Full weight | N/A |
| **Aging** | Permanence 0.3-0.5, or >6 months | 50% decay | Auto if cited |
| **Legacy** | Permanence < 0.3, or superseded | 90% decay | One-click |
| **Archived** | User-marked or >2 years + low permanence | Excluded | Explicit request |

### Gradual Transition

Documents don't suddenly "become legacy"—they transition:
```
Active → Aging (warning state) → Legacy (deprioritized) → Archived (excluded)
```

### Pros
- Graceful degradation
- Users have time to notice before documents disappear
- Fine-grained control

### Cons
- More complex to implement and explain
- Users might not understand the tiers

---

## Option 4: Context-Aware Legacy

**Concept**: Whether a document is "legacy" depends on the query context.

### How It Works

```
Query: "Current employee handbook policies"
→ Word "current" triggers Active-only search
→ Legacy excluded

Query: "History of our contract with Acme Corp"
→ Word "history" triggers include-all search
→ Legacy included
```

### AI Query Analysis

Before searching, AI classifies query intent:
- **Historical intent**: Include legacy
- **Current state intent**: Exclude legacy
- **Comparative intent**: Include both, label clearly

### Pros
- Most intelligent behavior
- Users don't need to think about it

### Cons
- AI classification might be wrong sometimes
- Less predictable behavior

---

## Recommendation

**Option 1 (Soft Exclusion)** as the default, with elements from Option 3:

### Proposed Behavior

1. **Active Documents**: Normal search behavior

2. **Legacy Documents**:
   - Remain searchable with 90% decay
   - Clearly labeled in responses with warning
   - Shown in separate UI section

3. **One-Click Recovery**:
   - User clicks "Keep Active" on any Legacy doc
   - System learns: increases category/type permanence for future
   - Document immediately restored to Active

4. **Inbox Notification** (for uncertainty):
   - When system is <60% confident about Legacy decision
   - Send to relevant team member (based on doc ownership/category)
   - Simple Yes/No: "Should [filename] be moved to Legacy?"
   - Response teaches the system

5. **"Archived" as Explicit Action**:
   - Never auto-archive
   - User must explicitly click "Archive"
   - Archived docs excluded from search but not deleted

---

## Data Model Changes

```python
class DocumentStatus(str, Enum):
    ACTIVE = "active"
    LEGACY = "legacy"
    ARCHIVED = "archived"

class Document:
    status: DocumentStatus
    status_reason: str  # "superseded_by_v2", "age_decay", "user_archived"
    status_changed_at: datetime
    superseded_by: Optional[str]  # doc_id of newer version
    permanence_score: float
    legacy_confidence: float  # How sure was system about legacy decision
```

---

## Recovery Learning Mechanism

When user recovers a Legacy document:

```python
async def recover_from_legacy(doc_id: str):
    doc = await get_document(doc_id)
    
    # 1. Restore to Active
    doc.status = "active"
    doc.status_reason = "user_recovered"
    
    # 2. Boost permanence
    doc.permanence_score = min(1.0, doc.permanence_score + 0.2)
    
    # 3. Learn for category
    await boost_category_permanence(doc.category, 0.1)
    
    # 4. Log for pattern learning
    await log_recovery_event(doc_id, doc.category, doc.document_type)
```

Over time, the system learns:
- "property_deeds" category recoveries → boost that category's permanence
- Similar document types → adjust default permanence scores

---

## Questions Resolved

| Original Question | Resolution |
|-------------------|------------|
| Manual override? | No direct score editing; one-click recovery instead |
| Handle "archive" requests? | Explicit "Archive" action, separate from auto-Legacy |
| Versioned docs searchable? | Yes, with 90% decay and clear labeling |
| Alerts for supersession? | Yes, via Inbox when system is uncertain |

---

## Next Steps

1. Confirm preferred Legacy behavior (Option 1 recommended)
2. Design UI for Legacy document list
3. Design Inbox notification format
4. Implement hybrid lifecycle with learning
