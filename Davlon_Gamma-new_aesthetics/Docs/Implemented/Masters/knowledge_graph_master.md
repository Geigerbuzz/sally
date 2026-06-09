---
title: Knowledge Graph Master
status: implemented
type: master
created: 2025-12-28
updated: 2025-12-28
tags: [neo4j, graph, database, entities]
consolidates:
  - Active/Proposals/knowledge_graph_enrichment_proposal.md
  - Active/Specs/Why_Neo4j.md
---

# Knowledge Graph Master

The data layer of Davlon. Neo4j Aura-based knowledge graph storing documents, entities, and relationships with vector search capability.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      NEO4J KNOWLEDGE GRAPH                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  NODE TYPES                                                           │
│  ├── Chunk         # Text chunks with embeddings                     │
│  ├── Document      # Source files                                    │
│  ├── Entity        # Dynamic entities (Patient, Invoice, etc.)       │
│  ├── Category      # Learned document categories                     │
│  ├── UnknownTopic  # Topics not in categories                        │
│  ├── AuditLog      # Special category query logs                     │
│  └── CompanyProfile # Company context singleton                      │
│                                                                       │
│  LEGACY NODES (backward compatible)                                   │
│  ├── Listing       # Real estate listings                            │
│  ├── Person        # Agents, contacts                                │
│  └── Message       # Inbox notifications                             │
│                                                                       │
│  INDEXES                                                              │
│  ├── chunk_embedding_index (vector, 768d, cosine)                    │
│  └── Standard indexes on id, name fields                             │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Key Files

| File | Size | Purpose |
|------|------|---------|
| [database.py](file:///Users/dora/Documents/Davlon_Gamma/backend/database.py) | 46KB | Neo4jDriver class, all DB operations |
| [graph_service.py](file:///Users/dora/Documents/Davlon_Gamma/backend/graph_service.py) | 15KB | High-level graph operations |
| [schema_learner.py](file:///Users/dora/Documents/Davlon_Gamma/backend/schema_learner.py) | 12KB | Dynamic schema inference |

---

## Implemented Features

### 1. Vector Index for Semantic Search
**Status**: ✅ Complete  
**Code**: `database.py:create_vector_index()`

```cypher
CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

---

### 2. Hybrid Graph+Vector Search
**Status**: ✅ Complete  
**Code**: `database.py:hybrid_graph_search()`

Combines:
- Vector similarity via index
- Graph traversal to related entities
- Temporal boost (newer = higher)
- Category filtering

---

### 3. Dynamic Entity Creation
**Status**: ✅ Complete  
**Code**: `graph_service.py:create_dynamic_entity()`

- Creates any entity type from learned schemas
- Builds Cypher dynamically
- Creates inferred relationships

---

### 4. Unknown Topic Tracking
**Status**: ✅ Complete  
**Code**: `database.py:log_unknown_topic()`

When users ask about unrecognized topics:
1. Log to `UnknownTopic` node
2. Track aliases (MVP → minimum_viable_product)
3. Alert admin if frequency exceeds threshold

---

### 5. Query Expansion Caching
**Status**: ✅ Complete  
**Code**: `database.py:get_cached_expansion()`, `save_expansion()`

- Cache LLM-generated query expansions
- Track hit/miss rates
- Prune low-performers

---

### 6. Chunk Linking
**Status**: ✅ Complete  
**Code**: `database.py:insert_chunk()`

Creates navigation relationships:
```cypher
(Chunk)-[:NEXT]->(Chunk)
(Chunk)-[:PREV]->(Chunk)
```

---

### 7. Category Management
**Status**: ✅ Complete  
**Code**: `database.py:get_unique_categories()`, `get_special_categories()`

- Dynamic category discovery
- Special category marking (legal, compliance)
- Category-based filtering in search

---

## Neo4j Schema

### Core Nodes

```cypher
// Document chunks with vectors
(:Chunk {
    id: string,
    text: string,
    embedding: [float x 768],
    source: string,
    category: [string],
    content_type: string,  // text|table|image|graph
    position: int,
    created_at: datetime
})

// Source documents
(:Document {
    id: string,
    filename: string,
    mime_type: string,
    uploaded_at: datetime,
    status: string  // active|deprioritized|archived
})

// Learned categories
(:Category {
    name: string,
    is_special: boolean,
    description: string,
    created_at: datetime
})
```

### Relationships

```cypher
(:Document)-[:HAS_CHUNK]->(:Chunk)
(:Chunk)-[:NEXT]->(:Chunk)
(:Chunk)-[:PREV]->(:Chunk)
(:Chunk)-[:MENTIONS]->(:Entity)
(:Entity)-[:RELATED_TO]->(:Entity)
```

### Uniqueness Constraints

```cypher
// Prevent duplicate entities and documents
CREATE CONSTRAINT FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT FOR (c:Category) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT FOR (p:Property) REQUIRE p.address IS UNIQUE;
CREATE CONSTRAINT FOR (co:Company) REQUIRE co.name IS UNIQUE;
```

---

## Configuration

```python
# Connection (from environment)
NEO4J_URI = "neo4j+s://xxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "..."

# Temporal settings
TEMPORAL_DECAY_DAYS = 365
TEMPORAL_DECAY_FACTOR = 0.3
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents` | GET | List all documents |
| `/api/listings` | GET | Legacy: real estate listings |
| `/api/inbox` | GET | Messages + knowledge gap alerts |

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| 📋 Proposal | [Knowledge Graph Enrichment](../../Active/Proposals/knowledge_graph_enrichment_proposal.md) | NER, relationship discovery |
| 📋 Spec | [Why Neo4j](../../Active/Specs/Why_Neo4j.md) | Technology rationale |
| 🔧 Master | [RAG System](./rag_system_master.md) | Consumes graph data |
| 🔧 Master | [Ingestion Pipeline](./ingestion_pipeline_master.md) | Populates graph |
