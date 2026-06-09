---
description: Audit a proposal document against its related code files
---

# Audit Document Workflow

Use this workflow to verify that a proposal document accurately reflects the current code implementation.

> ⚠️ **MANDATORY**: Ensure you have read `.agent/RULES.md` for project standards.

## When to Use
- After completing feature tracking rollout on a proposal
- When freshness_scorer.py shows a doc as stale
- Periodically for important proposals
- Before marking features as "Complete"

## Steps

### 1. Read the Proposal Document

View the entire proposal, especially:
- Implementation Status table
- Feature descriptions
- Code examples in the doc

### 2. Extract Related Code Files

Find the "Related Code Files" section at the bottom. Note each file listed.

### 3. Read the Actual Code

For each related code file:
```
view_file /path/to/code_file.py
```

Focus on:
- Functions mentioned in the proposal
- Data structures described
- Algorithms/logic explained

### 4. Compare and Report

Check for these issues:

| Issue Type | What to Look For |
|------------|------------------|
| **Outdated claim** | Doc says "we do X" but code does Y |
| **Missing feature** | Doc describes feature that doesn't exist in code |
| **Implemented but not marked** | Feature exists in code but Status shows ⬜ |
| **Stale code reference** | Doc references `function_name()` that was renamed/deleted |
| **Wrong file path** | Related Code Files lists a file that doesn't exist |

### 5. Update the Document

For each issue found:

**If feature is implemented but not marked:**
```markdown
| [Feature](#anchor) | ✅ Complete | 2025-01-07 | `file.py:function_name` |
```

**If doc claim is outdated:**
- Update the section to match current behavior
- Add `[!NOTE]` if significant change

**If feature doesn't exist:**
- Change status to `❌ Dropped` or leave as `⬜ Pending`
- Add note explaining the gap

### 6. Run Validators

After making changes:
```bash
python3 .agent/scripts/check-doc-links.py
python3 .agent/scripts/freshness_scorer.py
```

---

## Example Audit

```
📄 Auditing: rag_retrieval_improvements_proposal.md

Related Code Files:
- backend/rag.py ✓ exists
- backend/database.py ✓ exists

Checking claims:
- "Query expansion uses hybrid approach" → ✅ Confirmed in rag.py:expand_query
- "Semantic chunking preserves paragraphs" → ⚠️ Outdated: now uses sentence boundaries
- "Reranking with Cohere API" → ❌ Not implemented, still pending

Actions taken:
- Updated chunking description
- Confirmed Reranking status as Pending
```

---

## Quick Checklist

- [ ] Read full proposal document
- [ ] Read each related code file
- [ ] Check Implementation Status accuracy
- [ ] Verify code examples still work
- [ ] Update any mismatches found
- [ ] Run validators
