---
description: Find documentation related to a topic or feature
---

# Find Documentation Workflow

Use this workflow when asked to find or research existing documentation.

## Steps

1. **Start with Registry**
   - Read `Docs/REGISTRY.md` first
   - Search for keywords in document titles, tags, and summaries
   - Check all sections: Active, Implemented, Masters, Archive

2. **If Found in Registry**
   - Read the matching documents
   - Check their `related:` frontmatter for connected docs
   - Check `superseded_by:` to ensure you have the latest version

3. **If Not Found in Registry**
   - Use `find_by_name` to search `Docs/` for relevant `.md` files
   - Use `grep_search` to search for keywords within document content
   - Check `tags:` frontmatter for topic matches

4. **Report Findings**
   - List all relevant documents with:
     - File path
     - Status (draft/review/approved/implemented/archived)
     - Brief summary
   - Note any supersession relationships
   - Identify which document is the "source of truth" if multiple exist

## Quick Search Locations

| Looking For | Check First |
|-------------|-------------|
| Feature proposals | `Docs/Active/Proposals/` then `Docs/Implemented/Proposals/` |
| Technical specs | `Docs/Active/Specs/` then `Docs/Implemented/Specs/` |
| Source of truth | `Docs/Implemented/Masters/` |
| Deprecated ideas | `Docs/Archive/` |
| How-to guides | `Docs/Active/Guides/` or `Docs/Implemented/Guides/` |
