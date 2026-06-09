---
description: Update the implementation status of features in a proposal
---

# Update Feature Status Workflow

Use this workflow after implementing a feature from a proposal to update its tracking status.

## Steps

1. **Locate the Proposal**
   - Find the relevant proposal in `Docs/Active/Proposals/`
   - Or use `/find-docs` to search by topic

2. **Update the Implementation Status Table**
   
   Change the feature row from:
   ```markdown
   | [Feature Name](#1-feature-name) | ⬜ Pending | — | — |
   ```
   
   To:
   ```markdown
   | [Feature Name](#1-feature-name) | ✅ Complete | 2025-12-28 | `file.py:123` |
   ```
   
   Status icons:
   - `⬜ Pending` — Not started
   - `🔄 In Progress` — WIP (add "WIP in `file.py`" to notes)
   - `✅ Complete` — Done (add date and code reference)
   - `❌ Dropped` — Decided not to implement (add reason)

3. **Check if All Features Complete**
   
   If all features in the table are `✅ Complete`:
   - Update frontmatter `status: implemented`
   - Use `/mark-implemented` workflow to move to `Implemented/`

4. **Update Related Documents**
   
   If your implementation affects other proposals:
   - Find docs listed in the feature's "Affects" section
   - Check if they need status updates too

5. **Update Registry if Needed**
   - If status changed (draft → implemented), update `REGISTRY.md`

## Quick Reference

```markdown
## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Semantic Chunking](#1-semantic-chunking) | ✅ Complete | 2025-12-28 | `semantic_chunker.py` |
| [Query Expansion](#2-query-expansion) | 🔄 In Progress | — | WIP in `rag.py:324` |
| [Confidence Scoring](#3-confidence-scoring) | ⬜ Pending | — | — |
| [Legacy Detection](#4-legacy-detection) | ❌ Dropped | — | Replaced by permanence scoring |
```
