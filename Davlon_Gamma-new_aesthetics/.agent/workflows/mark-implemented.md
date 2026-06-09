---
description: Mark a proposal or spec as implemented after code is complete
---

# Mark Implemented Workflow

Use this workflow after implementing a feature to update its documentation status.

> ⚠️ **MANDATORY**: Ensure you have read `.agent/RULES.md` for project standards.

## Steps

1. **Update Document Frontmatter**
   ```yaml
   status: implemented
   updated: [today's date]
   implemented_in: [path to main implementation file]
   ```

2. **Move Document**
   - From: `Docs/Active/{type}s/{filename}.md`
   - To: `Docs/Implemented/{type}s/{filename}.md`

3. **Update Registry**
   - Remove from "Active Work" table in `Docs/REGISTRY.md`
   - Add to "Implemented" table with:
     - Document path
     - Implementation date
     - Code location
     - Summary

4. **Consider Creating a Master**
   If this implementation consolidates multiple related proposals/specs:
   - Create `Docs/Implemented/Masters/{topic}_master.md`
   - Reference all source documents in frontmatter `related:` field
   - Add a "Source Documents" section listing consolidated proposals
   - Update registry "Masters" section

5. **Update Related Documents**
   - Check if any documents in `Docs/Active/` reference this one
   - Update their `related:` frontmatter if needed
   - If this supersedes an older doc, update that doc's `superseded_by:` field
