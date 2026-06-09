# Why Neo4j? (Knowledge Graph)

## The Core Problem: "Hallucination & Context"
Vector databases (Pinecone) are great at finding *similar* text, but they are terrible at understanding **Exact Relationships**.
- **Vector Failure**: If you ask "Who owns LLC X?", a vector DB might return a document about "LLC Y" because the text looks similar.
- **RAG Hallucination**: The AI sees two similar names and might confidently invent a connection that doesn't exist.

## The Solution: Knowledge Graph
Neo4j stores data as **Nodes** (Entities) and **Edges** (Relationships).
- `(Person: "John Doe") -[:OWNS]-> (Company: "Alpha LLC")`
- `(Company: "Alpha LLC") -[:OWNER_OF]-> (Property: "123 Main St")`

## Why Neo4j specifically?
1.  **Zero Hallucination**: The "Auditor" Agent uses Neo4j to verify facts. If the link `[:OWNS]` does not exist in the graph, the AI is **forbidden** from stating unrelated ownership.
2.  **Complex Queries**: B2B Real Estate is all about relationships. "Show me all properties owned by shell companies connected to John Smith."
    - Relational DB (SQL): extremely slow and complex joins.
    - Neo4j: A simple, instant graph traversal (Cypher query).
3.  **Aura (Cloud)**: Like Pinecone, Neo4j Aura is a fully managed cloud service. It fits perfectly with your Railway hosting plan—no heavy database maintenance required on your end.
