---
description: Refresh the documentation registry after changes
---

# Update Registry Workflow

Use this workflow periodically or after major documentation changes.

> ⚠️ **MANDATORY**: Ensure you have read `.agent/RULES.md` for project standards.

## Steps

1. **Scan All Document Directories**
   ```
   Docs/Active/Proposals/*.md
   Docs/Active/Specs/*.md
   Docs/Active/Guides/*.md
   Docs/Implemented/Proposals/*.md
   Docs/Implemented/Specs/*.md
   Docs/Implemented/Masters/*.md
   Docs/Implemented/Guides/*.md
   Docs/Archive/Superseded/*.md
   Docs/Archive/Discarded/*.md
   Docs/Reports/*.md
   ```

2. **Parse Frontmatter**
   For each document, extract:
   - `title`
   - `status`
   - `type`
   - `tags`
   - `updated`
   - `implemented_in` (if applicable)
   - `superseded_by` (if applicable)

3. **Update Registry Tables**
   Generate tables for each section:
   - **Active Work**: Group by status (draft → review → approved)
   - **Implemented**: Order by implementation date (newest first)
   - **Masters**: List all source-of-truth documents
   - **Archive**: Separate superseded vs discarded

4. **Update Quick Stats**
   ```markdown
   ## Quick Stats
   - Active documents: [count]
   - Implemented: [count]
   - Archived: [count]
   - Last updated: [today's date]
   ```

5. **Verify Integrity**
   - Check for documents not in registry
   - Check for registry entries pointing to missing files
   - Report any inconsistencies

## Registry Template

See `Docs/REGISTRY.md` for the expected format and structure.
