---
title: Data Sources UX - Legacy Document Handling
status: implemented
type: proposal
created: 2025-12-27
updated: 2025-12-27
tags: [ui, sources, documents, legacy, ux]
implemented_in: public/sources_legacy.html
related:
  - Docs/Implemented/Proposals/legacy_document_management_proposal.md
  - Docs/Implemented/Masters/document_lifecycle_master.md
---

# Data & Sources UX Proposal: Legacy Document Handling

## Current State

The Data & Sources page has 3 tabs:
- **Static** - Uploaded documents
- **Live** - Connected data sources
- **Legacy** - Deprioritized/old documents

## The Problem

With the new lifecycle system, we have:
- **Legacy**: Deprioritized but searchable (90% decay)
- **Archived**: Excluded from search, explicit user action

**Question**: Should users see both Legacy and Archived? Will they understand the difference?

---

## Option 1: Keep It Simple - Single "Legacy" Tab

**Concept**: Merge Legacy and Archived into one "Legacy" tab with visual distinction.

### Tab Structure
```
[ Static ] [ Live ] [ Legacy ]
```

### Within Legacy Tab

| Document | Status | Visual | Actions |
|----------|--------|--------|---------|
| contract_v1.pdf | Deprioritized | Faded, amber dot | "Restore" |
| old_memo.pdf | Deprioritized | Faded, amber dot | "Restore" |
| obsolete_policy.pdf | Archived | Grayed out, red dot | "Restore" / "Delete" |

### UI Design

```
┌─────────────────────────────────────────────────────────────┐
│  Legacy Documents                                    [?]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ These documents are deprioritized in search results.    │
│     Click "Restore" to make them active again.             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🟠 contract_v1.pdf           Superseded by v2         │ │
│  │    Last accessed: 3 months ago          [ Restore ]   │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🟠 Q1_report.pdf             Age decay               │ │
│  │    Last accessed: 6 months ago          [ Restore ]   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ─────────────── Archived (Excluded from Search) ───────── │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ⛔ old_branding.pdf          User archived            │ │
│  │    Archived: 2024-01-15     [ Restore ] [ Delete ]   │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Pros
- Simple 3-tab structure maintained
- Visual hierarchy shows difference without extra tabs
- Users don't need to understand terminology

### Cons
- Mixed concerns in one view

---

## Option 4: Smart Defaults with Expandable Section (Recommended)

**Concept**: Keep current 3-tab structure but make Legacy smarter.

### Tab Structure (Unchanged)
```
[ Static ] [ Live ] [ Legacy ]
```

### Static Tab - Active Documents Only
- Shows only Active documents
- When a doc becomes Legacy, it moves automatically
- Toast notification: "contract_v1.pdf moved to Legacy (superseded)"

### Legacy Tab - Clear Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Legacy Documents                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 💡 These documents are still searchable, but results    ││
│  │    are deprioritized. Click Restore to make active.     ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  📁 Superseded Versions (4)                         [▼]    │
│  ├── contract_v1.pdf → replaced by contract_v2.pdf         │
│  ├── policy_v2.pdf → replaced by policy_v3.pdf             │
│  └── ...                                                    │
│                                                             │
│  📁 Aged Documents (7)                              [▼]    │
│  ├── Q1_report_2023.pdf (12 months old)                    │
│  ├── meeting_jan_2024.pdf (8 months old)                   │
│  └── ...                                                    │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│  ▶ Archived (3)                        [ Show archived ]   │
│    Documents you've explicitly archived. Not searchable.   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Elements

1. **Grouped by Reason**: Users understand WHY it's legacy
2. **Collapsible Sections**: Not overwhelming
3. **Archived Hidden by Default**: Requires explicit action to view
4. **Clear Messaging**: Explains searchability status

---

## Recommendation

**Option 4** (Smart Defaults) with:

1. **Keep 3-tab structure**: Static, Live, Legacy
2. **Legacy tab** groups by reason (Superseded, Aged)
3. **Archived** collapsed at bottom, requires click to expand
4. **Smart labels** explain status without jargon:
   - "Deprioritized" → "Reduced priority in search"
   - "Archived" → "Excluded from search"
5. **Warning Design B** for RAG responses

### User-Friendly Terminology

| Internal Term | User-Facing Term |
|---------------|------------------|
| Legacy | "Legacy" (familiar) |
| Deprioritized | "Reduced priority" |
| Archived | "Excluded from search" |
| Superseded | "Replaced by newer version" |
| Age decay | "Low recent activity" |

---

## Next Steps

1. Confirm preferred option (4 recommended)
2. Implement backend lifecycle system
3. Update Data & Sources UI
4. Add warning labels to chat responses
