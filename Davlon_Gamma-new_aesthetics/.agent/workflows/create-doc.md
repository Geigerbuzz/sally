---
description: Create a new documentation file with proper structure
---

# Create Documentation Workflow

Use this workflow when asked to create any new documentation for the project.

> ⚠️ **MANDATORY**: Read `.agent/RULES.md` before proceeding. This workflow enforces project standards.

## Steps

1. **Check Registry First**
   - Read `Docs/REGISTRY.md` to find existing related documents
   - Use as context for your proposal (reference, extend, or improve — not blindly duplicate)

2. **Determine Document Type**
   | Type | Use For |
   |------|---------|
   | `proposal` | Feature/change proposals with options and recommendations |
   | `spec` | Technical specifications for a component |
   | `guide` | How-to guides for developers/users |
   | `report` | Generated analysis or audit |
   | `master` | Consolidated source of truth for a topic |
   | `notes` | Working notes, reminders, checklists |

3. **Create File in Correct Location**
   ```
   Docs/Active/Proposals/{filename}.md   # for proposals
   Docs/Active/Specs/{filename}.md       # for specs
   Docs/Active/Guides/{filename}.md      # for guides
   ```

4. **Include Required Frontmatter**
   ```yaml
   ---
   title: [Human-readable title]
   status: draft
   type: [proposal|spec|guide|report|master|notes]
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   tags: [array of topic tags]
   related: [optional - paths to related docs]
   ---
   ```

5. **Add Implementation Status Table (for proposals)**
   
   After the title, include a feature tracking table:
   ```markdown
   ## Implementation Status
   
   | Feature | Status | Implemented | Code Reference |
   |---------|--------|-------------|----------------|
   | [Feature Name](#1-feature-name) | ⬜ Pending | — | — |
   ```
   
   Status icons:
   - `⬜ Pending` — Not started
   - `🔄 In Progress` — WIP
   - `✅ Complete` — Done (add date and code reference)
   - `❌ Dropped` — Decided not to implement

6. **Structure Feature Sections with Dependencies**
   
   Each feature section should include dependency links:
   ```markdown
   ### 1. Feature Name {#feature-name}
   
   > **Depends on**: [Other Feature](./other_doc.md#other-feature)  
   > **Affects**: [Downstream Feature](./downstream_doc.md#feature)
   
   Description of the feature...
   ```
   
   Use `{#anchor-id}` to create linkable anchors.

7. **Write Document Content**
   - Use clear headers and structure
   - Include "Open Questions" section if decisions are needed
   - For proposals: include options, pros/cons, and recommendation

8. **Add Related Code Files Section (for proposals)**
   
   At the end of the document, add a reverse index of code files:
   ```markdown
   ## Related Code Files

   When modifying these files, consider updating this proposal:

   | File | Relevance |
   |------|-----------|
   | `backend/rag.py` | Query classification, expansion |
   | `public/widgets.js` | Widget rendering |
   ```
   
   This helps agents know which docs to update when they modify code.

9. **Update Registry**
   - Add entry to `Docs/REGISTRY.md` under "Active Work" section
   - Include document path, status, tags, and one-line summary
