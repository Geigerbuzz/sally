---
title: Multi-Tenant Security Proposal
status: draft
type: proposal
created: 2025-12-28
updated: 2025-12-28
tags: [security, auth, multi-tenant, rbac]
---

# Multi-Tenant Security Proposal

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Clerk Authentication](#1-authentication) | ⬜ Pending | — | — |
| [Row-Level Security](#2-row-level-security-graph-structure) | ⬜ Pending | — | — |
| [Gemini Pre-filtering](#3-pre-filtering-for-gemini) | ⬜ Pending | — | — |
| [RBAC Roles](#4-role-based-access-control-rbac) | ⬜ Pending | — | — |

---

## Overview

Currently Davlon runs as a single-tenant application with no authentication. This proposal outlines the architecture for adding:

1. **Authentication** via Clerk or Auth0
2. **Row-Level Security** via graph structure
3. **Pre-filtering** for Gemini queries

---

## 1. Authentication {#authentication}

> **Depends on**: None (foundation)  
> **Affects**: [Row-Level Security](#2-row-level-security-graph-structure), [RBAC](#4-role-based-access-control-rbac)

### Recommended: Clerk

Don't roll your own auth. Use a managed provider.

**Frontend**:
```javascript
// Clerk React SDK (or plain JS)
import { ClerkProvider, SignIn } from '@clerk/clerk-react';

<ClerkProvider publishableKey="pk_...">
  <SignIn />
</ClerkProvider>
```

**Backend**:
```python
from fastapi import Depends

async def verify_token(token: str = Header(...)) -> User:
    """Verify JWT and return user object."""
    # Decode Clerk JWT
    # Extract user.id, org.id
    return user

@app.get("/api/secure")
async def secure_route(user: User = Depends(verify_token)):
    return {"msg": f"You are {user.id}"}
```

---

## 2. Row-Level Security (Graph Structure)

### The Pattern

Data isolation is enforced by graph structure, not application code.

**Nodes**:
```cypher
(:User {id: "clerk|abc123", email: "user@example.com"})
(:Organization {id: "org_xyz", name: "Acme Realty"})
(:Document {id: "doc_001", filename: "contract.pdf"})
```

**Relationships**:
```cypher
(:User)-[:MEMBER_OF]->(:Organization)
(:Document)-[:OWNED_BY]->(:Organization)
(:Chunk)-[:PART_OF]->(:Document)
```

### Query Enforcement

**NEVER** write:
```cypher
MATCH (d:Document) RETURN d  // Exposes ALL documents
```

**ALWAYS** write:
```cypher
MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(o:Organization)
MATCH (o)<-[:OWNED_BY]-(d:Document)
RETURN d
```

This physically prevents a user from seeing documents outside their organization.

---

## 3. Pre-Filtering for Gemini

Gemini File API doesn't support per-user isolation. We must pre-filter before calling.

**Flow**:
1. User asks a question
2. Query Neo4j for this user's allowed file URIs:
   ```cypher
   MATCH (u:User {id: $uid})-[:MEMBER_OF]->(o)
   MATCH (o)<-[:OWNED_BY]-(d:Document {status: 'active'})
   RETURN d.uri AS file_uri
   ```
3. Pass only those URIs to Gemini:
   ```python
   allowed_refs = [genai.FileReference(uri=f) for f in allowed_uris]
   response = model.generate_content([prompt] + allowed_refs)
   ```

---

## 4. Role-Based Access Control (RBAC)

### Roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read documents, ask questions |
| `editor` | Upload documents, create widgets |
| `admin` | Manage users, access Settings, Legacy tab |

### Enforcement

```python
def require_role(required: str):
    def checker(user: User = Depends(verify_token)):
        if user.role not in ROLE_HIERARCHY[required]:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker

@app.post("/api/settings")
async def update_settings(user = Depends(require_role("admin"))):
    ...
```

---

## Implementation Priority

| Phase | Feature | Effort |
|-------|---------|--------|
| 1 | Clerk integration (frontend + backend) | 1 week |
| 2 | Organization nodes + OWNED_BY relationships | 2 days |
| 3 | Query rewriting for RLS | 1 week |
| 4 | RBAC roles | 2 days |

---

## Related Documents

| Document | Description |
|----------|-------------|
| [knowledge_graph_master.md](../Implemented/Masters/knowledge_graph_master.md) | Neo4j schema |
| [document_lifecycle_master.md](../Implemented/Masters/document_lifecycle_master.md) | Document status handling |
