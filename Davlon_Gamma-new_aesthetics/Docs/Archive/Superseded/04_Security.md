# Production Step 4: Security & Permissions

**Goal**: Ensure Role-Based Access Control (RBAC) so users only see their data.

## 1. Authentication (Clerk / Auth0)
Don't roll your own auth.
1.  **Frontend**: Use Clerk React SDK (or similar) to handle Login/SignUp.
2.  **Backend**: Verify the JWT (JSON Web Token) on every request.
    ```python
    @app.get("/api/secure")
    async def secure_route(user: User = Depends(verify_token)):
        return {"msg": "You are " + user.id}
    ```

## 2. Row-Level Security (RLS) in Neo4j
We need to restrict *Graph Traversals*.

### Pattern:
1.  **User Node**: Every user has a node `(u:User {id: "auth0|123"})`.
2.  **Organization**: Users belong to an Org `(u)-[:MEMBER_OF]->(o:Org)`.
3.  **Data Isolation**: All data is linked to the Org. `(d:Document)-[:OWNED_BY]->(o:Org)`.

### Query Enforcement:
NEVER write a query like `MATCH (d:Document) RETURN d`.
ALWAYS write:
```cypher
MATCH (u:User {id: $uid})-[:MEMBER_OF]->(o:Org)
MATCH (o)<-[:OWNED_BY]-(d:Document)
RETURN d
```
This physically prevents a user from seeing data outside their Org.

## 3. Document Security (Gemini)
1.  **Metadata**: When uploading to Gemini, we cannot easily "hide" parts of a file.
2.  **Strategy**: We must rely on our **Pre-Filtering**.
    - If User X asks a question, we query Neo4j for *allowed* file URIs first.
    - Then we generate content using *only* those URIs.
    - `model.generate_content([prompt] + allowed_file_refs)`
