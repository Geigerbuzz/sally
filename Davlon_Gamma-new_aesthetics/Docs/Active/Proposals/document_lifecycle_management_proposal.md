---
title: Intelligent Document Lifecycle Management
status: draft
type: proposal
created: 2025-12-21
updated: 2025-12-28
tags: [documents, lifecycle, temporal, decay]
parent: null
children: []
related:
  - ./unified_document_labeling_proposal.md
  - ../../Implemented/Proposals/self_adapting_rag_proposal.md
---

# Intelligent Document Lifecycle Management

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [AI Permanence Score (A)](#proposal-a-ai-inferred-document-permanence-score) | ✅ Complete | 2025-12-27 | `document_lifecycle.py:analyze_permanence` |
| [Category Lifecycle (B)](#proposal-b-document-category-lifecycle-profiles) | ✅ Complete | 2025-12-27 | `document_lifecycle.py:_boost_category_permanence` |
| [Version Detection (C)](#proposal-c-version-detection--supersession-tracking) | ✅ Complete | 2025-12-27 | `document_lifecycle.py:detect_supersession` |
| [Hybrid Intelligence (D)](#proposal-d-hybrid-intelligence-recommended) | ✅ Complete | 2025-12-27 | `document_lifecycle.py:calculate_confidence` |

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md), [Self-Adapting RAG](../../Implemented/Proposals/self_adapting_rag_proposal.md)  
> **Affects**: [RAG System Master](../../Implemented/Masters/rag_system_master.md), [Unified Labeling](./unified_document_labeling_proposal.md)

---

## The Problem

The current temporal decay system treats all documents equally:
- **365 days** = maximum age for decay
- **30% reduction** = maximum score penalty

This fails for real-world document patterns:

| Document Type | True Relevance Lifespan |
|---------------|------------------------|
| Property Deed | Perpetual (decades+) |
| Company Policies | 1-5 years |
| Quarterly Reports | ~3 months |
| Draft Contracts | Hours to days |
| Meeting Notes | Weeks to months |
| Marketing Materials | Months |

**Core Challenge**: The system cannot rely on filenames, user labels, or manual tagging—it must infer document lifecycle characteristics from content.

---

## Proposed Solutions

### Proposal A: AI-Inferred Document Permanence Score

**Concept**: During ingestion, use AI to analyze document content and assign a "Permanence Score" (0-1) that determines how temporal decay applies.

**How It Works**:

1. **During Ingestion**, the AI analyzes:
   - Document type indicators (legal terms, dates, draft markers)
   - Version indicators ("v1", "draft", "final", "SUPERSEDED")
   - Time-sensitive language ("this quarter", "effective immediately")
   - Immutable content markers (signatures, notarization, official stamps)

2. **Permanence Score Mapping**:
   ```
   0.0 = Highly ephemeral (draft, temp, working doc)
   0.5 = Standard decay applies
   1.0 = Permanent (deeds, certificates, legal records)
   ```

3. **Decay Formula Adjustment**:
   ```
   effective_decay = base_decay × (1 - permanence_score)
   ```
   - Permanence 1.0 → No decay ever
   - Permanence 0.5 → Normal decay
   - Permanence 0.0 → Accelerated decay

**AI Prompt Example**:
```
Analyze this document and determine its permanence score (0.0 to 1.0):

Document: {filename}
Content Preview: {first_2000_chars}

Consider:
- Is this a legally binding document? (deed, contract, certificate, signed agreement)
- Does it contain draft/temporary indicators? ("draft", "v0.1", "working copy")
- Is it time-bound? ("Q3 2024", "this month's", "as of today")
- Is it a reference document meant to be superseded? (reports, updates, memos)

Respond in JSON:
{"permanence_score": 0.85, "reasoning": "...", "document_type": "legal_contract"}
```

**Pros**: Fully automatic, no user input required  
**Cons**: AI inference may occasionally be wrong

---

### Proposal B: Document Category Lifecycle Profiles

**Concept**: Leverage the existing dynamic category system. Each discovered category has a learned lifecycle profile.

**How It Works**:

1. **Category-Level Configuration** in Company Profile:
   ```python
   class CategoryLifecycle(BaseModel):
       category_name: str
       decay_mode: str  # "none", "standard", "rapid", "custom"
       decay_days: int = 365  # Only for "custom"
       decay_factor: float = 0.3
   ```

2. **AI Learns Lifecycle from Category Content**:
   - When a new category is discovered (e.g., "property_deeds"), AI analyzes representative documents
   - Infers appropriate decay profile
   - Stores in Company Profile for consistent application

3. **Default Category Profiles**:
   ```
   legal_deeds: decay_mode="none"
   contracts_draft: decay_mode="rapid", decay_days=30
   quarterly_reports: decay_mode="standard"
   meeting_notes: decay_mode="custom", decay_days=90
   ```

**Pros**: Consistent handling per document type, learnable  
**Cons**: New categories require inference before proper handling

---

### Proposal C: Version Detection & Supersession Tracking

**Concept**: Automatically detect when a document supersedes or replaces another, rather than relying on age alone.

**How It Works**:

1. **Version Detection During Ingestion**:
   - Parse filename and content for version indicators
   - Examples: `Contract_v2.pdf`, "Revision 3", "Updated Policy 2024"

2. **Supersession Relationship**:
   ```cypher
   (doc_new:Document)-[:SUPERSEDES]->(doc_old:Document)
   ```

3. **Automatic Detection Triggers**:
   - Same base filename with different version number
   - Content similarity >80% with newer timestamp
   - Explicit references ("This replaces the document dated...")

4. **Query-Time Handling**:
   - Superseded documents get severe decay (or exclusion)
   - Latest version gets priority
   - Historical access still possible if explicitly requested

**Pros**: Handles the draft→final workflow naturally  
**Cons**: Requires version pattern detection logic

---

### Proposal D: Hybrid Intelligence (Recommended)

**Concept**: Combine multiple signals for robust lifecycle management.

**Architecture**:

```
Document Ingestion
        │
        ▼
┌───────────────────┐
│ 1. Version Check  │ → Detect supersession relationships
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 2. AI Permanence  │ → Infer permanence score from content
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 3. Category Match │ → Apply category lifecycle if exists
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 4. Final Decay    │ → weighted combination of signals
└───────────────────┘
```

**Signal Weights**:
- Superseded by newer version: 90% decay (almost hidden)
- AI Permanence Score: Primary factor
- Category Lifecycle: Secondary/override
- Raw Age: Tertiary (fallback)

**Example Scenarios**:

| Document | Version | AI Permanence | Category | Final Behavior |
|----------|---------|---------------|----------|----------------|
| property_deed.pdf | v1 (only) | 0.95 | legal_deeds (no decay) | **Never decays** |
| contract_draft_v1.pdf | Superseded by v2 | 0.3 | contracts_draft | **90% decay** |
| contract_draft_v2.pdf | Latest | 0.3 | contracts_draft | **Rapid decay (30 days)** |
| board_meeting_2024.pdf | v1 | 0.5 | meeting_notes | **Standard 90-day decay** |
| employee_handbook.pdf | v1 | 0.8 | policies | **Slow decay (1 year)** |

---

## Implementation Complexity

| Proposal | Effort | Accuracy | Fully Automatic |
|----------|--------|----------|-----------------|
| A: AI Permanence | Low | Medium | ✅ |
| B: Category Lifecycle | Medium | High | ✅ |
| C: Version Detection | Medium | High for versions | ✅ |
| D: Hybrid (Recommended) | High | Highest | ✅ |

---

## Recommended Approach

**Phase 1** (Quick Win): Implement **Proposal A** (AI Permanence Score)
- Single AI call during ingestion
- Store `permanence_score` on each Document node
- Modify temporal decay to use this score
- ~2-3 days effort

**Phase 2** (Enhancement): Add **Proposal C** (Version Detection)
- Detect when documents supersede each other
- Create SUPERSEDES relationships
- Apply heavy decay to superseded documents
- ~2-3 days effort

**Phase 3** (Polish): Add **Proposal B** (Category Lifecycle)
- Define lifecycle profiles per category
- Allow category-level overrides
- Admin visibility into lifecycle settings
- ~2-3 days effort

---

## Questions for Review

1. Should users be able to manually override permanence scores?
2. How should the system handle explicit "archive" or "obsolete" requests?
3. Do you want versioned documents to remain searchable, or be hidden entirely?
4. Should there be alerts when documents are detected as superseded?

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/ingestion.py` | Permanence scoring during ingest |
| `backend/database.py` | Temporal decay queries |
| `backend/document_lifecycle.py` | Version detection, supersession |
