---
description: Synchronize and verify bidirectional links between documentation files
---

# Sync Document Links

Use this workflow to verify and maintain bidirectional links across documentation.

## When to Use
- After adding `related:` links to a document
- When creating a new document with relationships
- For periodic link hygiene checks

## Steps

### 1. Identify Outgoing Links

Read the frontmatter of the document you're working with:

```yaml
related:
  - ./other_doc.md
  - ../folder/another_doc.md
```

### 2. Verify Backlinks Exist

For each document in `related:`, check that it links back:

```bash
# If Doc A links to Doc B:
# Doc B should also link to Doc A in its frontmatter
```

If backlink is missing, add it to maintain bidirectionality.

### 3. Check Parent/Child Consistency

If a document has `parent: ./some_parent.md`:
- The parent should have this document in its `children:` array

If a document has `children:`:
- Each child should have this document as its `parent:`

### 4. Validate Links Are Valid

Confirm that all referenced files actually exist:

```bash
# For each path in related/parent/children:
# Verify the file exists at that relative path
```

### 5. Update REGISTRY.md (if needed)

If you added new relationships that affect document categorization, update the registry.

## Link Format

Use relative paths from the current document:

```yaml
# Same folder
related:
  - ./sibling_doc.md

# Parent folder
related:
  - ../other_folder/doc.md

# Cross-folder (from Active/Proposals to Implemented/Proposals)
related:
  - ../../Implemented/Proposals/old_version.md
```

## Common Relationship Types

| Frontmatter Key | Meaning | Backlink Required |
|-----------------|---------|-------------------|
| `parent:` | Document this is derived from | Yes (`children:`) |
| `children:` | Documents derived from this | Yes (`parent:`) |
| `related:` | Conceptually related docs | Recommended |
| `supersedes:` | Replaces an older doc | Yes (`superseded_by:`) |
| `superseded_by:` | Replaced by a newer doc | Yes (`supersedes:`) |

## Example Session

```
1. View target document's frontmatter
2. For each `related:` entry:
   a. View that document
   b. Check if it links back
   c. If not, add the backlink
3. Save changes
4. Run /update-registry if needed
```

---

## Impact Analysis (Cascading Updates)

When modifying a document, check for cascading effects:

### 1. Check Who Depends on This Document

Search for docs that reference this one in their `Depends on` links:

```bash
grep -r "Depends on.*current_doc.md" Docs/Active/
```

### 2. Check Implementation Status Tables

If you complete a feature, documents that depend on it may now be unblocked:

```
If: rag_retrieval.md marks "Query Expansion" as ✅ Complete
Then: adaptive_learning.md (which depends on it) can start that feature
```

### 3. Check Related Code Files Sections

When modifying code, search for proposals that reference that file:

```bash
grep -r "backend/rag.py" Docs/Active/Proposals/
```

Update the status or relevant sections in those proposals.

### 4. Notify Affected Documents

If your change affects behavior described in other docs:

1. View the affected document
2. Add an `[!NOTE]` if needed:
   ```markdown
   > [!NOTE]
   > Updated as of 2025-01-07: Query expansion now cached (per rag_retrieval changes).
   ```
3. Or update the relevant section directly

---

## Quick Reference: When to Propagate Updates

| Change Made | Documents to Check |
|-------------|--------------------|
| Completed a feature | Docs with `Depends on` pointing here |
| Changed file X | Docs with X in `Related Code Files` |
| Archived/moved a doc | Docs with links pointing to old path |
| Changed a proposal's scope | Docs in the `Affects` list |
| New Master doc created | Active Proposals that should reference it |
