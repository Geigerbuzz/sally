---
description: Run after implementing code to update related documentation
---

# After Implementation Workflow

Run this workflow after making significant code changes to keep documentation in sync.

> [!IMPORTANT]
> **This workflow is MANDATORY after any code implementation.**
> The agent MUST follow these steps and notify the user of all updates made.

---

## Automatic Actions

When I complete a code implementation, I will automatically:

1. ✅ Update the **Implementation Status** table in related proposals
2. ✅ Update the relevant **Master doc** with new behavior details
3. ✅ Run the link validator
4. ✅ Notify you with a summary of all doc changes

---

## Step-by-Step Process

### 1. Identify Changed Files

List all code files modified in this implementation:
```
backend/rag.py
backend/database.py
```

### 2. Find Related Documents

Use `CODE_TO_DOC_INDEX.md` or grep:
```bash
grep -r "rag.py" Docs/Active/Proposals/ --include="*.md"
```

### 3. Update Implementation Status Tables

For each related proposal, update the feature row:

**If completed:**
```markdown
| [Feature](#anchor) | ✅ Complete | 2025-01-07 | `file.py:function` |
```

**If modified:**
```markdown
| [Feature](#anchor) | 🔄 Revised | 2025-01-07 | `file.py:function` |
```

### 4. Update Master Docs (AUTOMATIC)

Identify which Master doc governs this code:

| Code Area | Master Doc |
|-----------|------------|
| `backend/rag.py`, `backend/database.py` | `rag_system_master.md` |
| `backend/ingestion.py` | `ingestion_pipeline_master.md` |
| `backend/graph_service.py` | `knowledge_graph_master.md` |
| `public/widget*.js` | `widget_system_master.md` |
| `public/style.css`, `public/*.html` | `ui_system_master.md` |

**Required Master doc updates:**
- [ ] Update "Current Behavior" sections if behavior changed
- [ ] Add new functions/methods to API reference
- [ ] Update code examples if they're now incorrect
- [ ] Add `[!NOTE]` if significant change from original design

### 5. Check Downstream Dependencies

Look at `Affects` links in the updated proposal:
```markdown
> **Affects**: [Some Other Proposal](./other.md)
```

If the feature you completed is a dependency for that doc, add a note:
```markdown
> [!NOTE]
> The dependency on [Feature X](other.md#anchor) has been fulfilled as of 2025-01-07.
```

### 6. Run Validators

```bash
// turbo
python3 .agent/scripts/check-doc-links.py
```

### 7. Notify User (MANDATORY)

After all updates complete, notify the user with:

```
## 📝 Documentation Updated

**Implementation:** [describe what you built]

### Docs Updated:
- ✅ `rag_retrieval_improvements_proposal.md` — Marked "Query Expansion" complete
- ✅ `rag_system_master.md` — Added expand_query() function details
- ✅ `adaptive_learning_proposal.md` — Noted dependency fulfilled

### Validation:
- Link Validator: ✅ All links valid
```

---

## Quick Reference

After ANY code change:

| Step | Action | Automatic? |
|------|--------|------------|
| 1 | Find related docs | Yes |
| 2 | Update Implementation Status | Yes |
| 3 | Update Master doc | Yes |
| 4 | Check `Affects` links | Yes |
| 5 | Run validator | Yes |
| 6 | Notify user | Yes |

---

## Examples

### Example: Completed Query Expansion

**Code changed:** `backend/rag.py` — added `expand_query()` function

**Automatic updates:**

1. **rag_retrieval_improvements_proposal.md:**
   ```diff
   -| [Query Expansion](#22-query-expansion) | ⬜ Pending | — | — |
   +| [Query Expansion](#22-query-expansion) | ✅ Complete | 2025-01-07 | `rag.py:expand_query` |
   ```

2. **rag_system_master.md:**
   ```markdown
   ### Query Expansion
   
   The `expand_query()` function in `rag.py` now:
   - Uses synonym lookup via Gemini
   - Adds related terms to improve recall
   - Limits expansion to 3 terms max
   ```

3. **Notification to user:**
   ```
   📝 Documentation Updated
   
   Implementation: Query expansion in rag.py
   
   Docs Updated:
   - ✅ rag_retrieval_improvements_proposal.md (marked complete)
   - ✅ rag_system_master.md (added function details)
   
   Validation: ✅ All links valid
   ```
