# Document Lifecycle System — Master Specification

**Last Updated**: December 27, 2025  
**Status**: ✅ Implemented (minor polish remaining)

> This document consolidates the Document Lifecycle system from multiple proposals into a single source of truth.

---

## Implementation Status Overview

| Component | Status | Location |
|-----------|--------|----------|
| Core Lifecycle Logic | ✅ Done | `backend/document_lifecycle.py` (540 lines) |
| AI Permanence Analysis | ✅ Done | `document_lifecycle.py` |
| Version Supersession Detection | ✅ Done | `document_lifecycle.py` |
| Recovery Learning | ✅ Done | `document_lifecycle.py` |
| Semantic Chunking Integration | ✅ Done | `backend/ingestion.py` |
| Scheduled Re-evaluation Jobs | ✅ Done | `backend/main.py` (APScheduler, daily at 3 AM) |
| Legacy Tab UI | ✅ Done | `public/sources_legacy.html` (378 lines) |
| Inbox Notification Logic | ✅ Done | `should_notify_for_legacy()` in `document_lifecycle.py` |
| APOC Dependency | ⚠️ Graceful Fallback | Used in `_boost_category_permanence()`, has try/catch |

> **Note**: The APOC functions are wrapped in try/catch with a warning log. System continues working even if APOC isn't installed.

---

## 1. Core Concepts

### 1.1 Document States

| State | Description | Search Behavior |
|-------|-------------|-----------------|
| **Active** | Current, relevant documents | Full weight |
| **Legacy (Deprioritized)** | Older but still searchable | 90% decay applied |
| **Archived** | Explicitly excluded | Not searchable |

### 1.2 How Documents Become Legacy

A document enters Legacy status when:

1. **Superseded**: A newer version exists (`contract_v1` → `contract_v2`)
2. **Age Decay**: Temporal decay + low permanence score pushed it below threshold
3. **Explicitly Archived**: User marked it as obsolete

---

## 2. Permanence Scoring (✅ Implemented)

During ingestion, AI analyzes document content and assigns a **Permanence Score** (0-1).

### Score Mapping

```
0.0 = Highly ephemeral (draft, temp, working doc)
0.5 = Standard decay applies
1.0 = Permanent (deeds, certificates, legal records)
```

### Decay Formula

```python
effective_decay = base_decay × (1 - permanence_score)
```

- Permanence 1.0 → No decay ever
- Permanence 0.5 → Normal decay
- Permanence 0.0 → Accelerated decay

### AI Analysis Factors

- Document type indicators (legal terms, dates, draft markers)
- Version indicators ("v1", "draft", "final", "SUPERSEDED")
- Time-sensitive language ("this quarter", "effective immediately")
- Immutable content markers (signatures, notarization, official stamps)

---

## 3. Version Supersession (✅ Implemented)

### Detection Triggers

- Same base filename with different version number
- Content similarity >80% with newer timestamp
- Explicit references ("This replaces the document dated...")

### Graph Relationship

```cypher
(doc_new:Document)-[:SUPERSEDES]->(doc_old:Document)
```

### Query-Time Handling

- Superseded documents get 90% decay
- Latest version gets priority
- Historical access still possible if explicitly requested

---

## 4. Recovery Learning (✅ Implemented)

When a user restores a Legacy document:

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
- Categories with frequent recoveries get boosted permanence
- Similar document types get adjusted default scores

---

## 5. Special Category Behavior

Documents tagged with **special categories** (e.g., `legal`) get enhanced treatment:

| Behavior | Regular | Special |
|----------|---------|---------|
| Chunk overlap | 30% | 50% |
| Citation threshold | 90% confidence | 95% confidence |
| Legacy warnings | Subtle | Strong warning |
| Answer tone | Casual | Careful, verified |
| Audit logging | Standard | Enhanced |

---

## 6. Implementation References

### 6.1 Scheduled Re-evaluation Jobs (✅ Implemented)

**Location:** `backend/main.py` lines 47-94

```python
# Daily at 3 AM: Re-evaluate stale documents
scheduler.add_job(
    daily_maintenance_job,
    CronTrigger(hour=3, minute=0),
    id="daily_maintenance"
)
```

The `daily_maintenance_job()` calls `lifecycle_manager.reevaluate_stale_documents()`.

---

### 6.2 Legacy Tab UI (✅ Implemented)

**Location:** `public/sources_legacy.html` (378 lines)

**Design:** Implements **Option 4 (Smart Defaults)** from `data_sources_ux_proposal.md`

**UI Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  Data & Sources                                             │
├─────────────────────────────────────────────────────────────┤
│      [ Static ]    [ Live ]    [ Legacy (active) ]          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 💡 About Legacy Documents                              │  │
│  │ These documents are deprioritized in search results.  │  │
│  │ Click "Restore" to make them active again.            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ⏱️ DEPRIORITIZED (2)                                      │
│  ─────────────────────────────────────────────────────────  │
│  │ 📄 contract_v1.pdf     │ Superseded by v2 │ [Restore] │  │
│  │ 📄 Q1_report_2024.pdf  │ Age decay        │ [Restore] │  │
│                                                             │
│  📦 ARCHIVED (Excluded from Search) (1)                    │
│  ─────────────────────────────────────────────────────────  │
│  │ 📄 old_branding.pdf    │ User archived │ [Restore][Delete] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implemented Features:**
- ✅ Separate Legacy tab in Data & Sources navigation
- ✅ Notice banner with amber styling explaining Legacy status
- ✅ **Deprioritized** section (amber icons) — still searchable
- ✅ **Archived** section (red icons) — excluded from search
- ✅ Reason badges: "Superseded by v2", "Age decay", "User archived"
- ✅ [Restore] button on all items
- ✅ [Delete] button only on Archived items
- ✅ Responsive mobile design
- ✅ Calls `/api/documents/legacy` endpoint

---

### 6.3 Inbox Notification Logic (✅ Implemented)

**Location:** `document_lifecycle.py` lines 457-471

```python
async def should_notify_for_legacy(self, doc_id: str) -> bool:
    # Only notify when confidence < 60%
    ...
    return confidence < 0.6
```

**Note:** The logic is in place. Inbox message creation uses the existing inbox infrastructure at `/api/inbox`.

---

### 6.4 APOC Dependency (⚠️ Graceful Fallback)

**Location:** `document_lifecycle.py` lines 404-421

The `_boost_category_permanence()` function uses APOC for JSON manipulation but wraps it in try/catch:

```python
try:
    await self.db.run_query(query, {...})
except Exception as e:
    # APOC may not be installed, log and continue
    logger.warning(f"Category boost failed (APOC not available?): {e}")
```

**Future improvement:** Replace APOC with simple property increment:
```cypher
SET c.permanence_boost = COALESCE(c.permanence_boost, 0.0) + $boost
```

---

## 7. Data Model

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

## 8. Source Documents

This master document consolidates information from:

| Document | Relevance |
|----------|-----------|
| `Proposals/document_lifecycle_management_proposal.md` | Primary source — permanence scoring, options analysis |
| `IMPLEMENTED/data_sources_ux_proposal.md` | ✅ **Chosen design**: Option 4 (Smart Defaults with Legacy Tab) |
| `IMPLEMENTED/legacy_document_management_proposal.md` | Soft exclusion approach, recovery learning |
| `Proposals/unified_document_labeling_proposal.md` | Special category behaviors, warnings |
| `Proposals/finishing_partial_implementations.md` | Implementation status tracking |

---

## 9. Remaining Polish

| Priority | Task | Effort |
|----------|------|--------|
| 🟡 P2 | Replace APOC with simple property increment | 0.5 day |
| 🟡 P3 | Add inbox message creation when `should_notify_for_legacy()` is true | 0.5 day |

