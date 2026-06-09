---
title: Document Storage Format Strategy
status: draft
type: proposal
created: 2026-01-08
updated: 2026-01-08
tags: [storage, neo4j, rag, markdown, json, architecture]
parent: null
children: []
related:
  - ./high_fidelity_extraction_proposal.md
  - ./advanced_rag_enhancements_proposal.md
  - ./knowledge_graph_enrichment_proposal.md
---

# Proposal: Document Storage Format Strategy

> **Problem**: After extracting document content with full fidelity, how should we store it for optimal RAG retrieval and Neo4j querying?

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Pure Markdown Option](#2-option-a-pure-markdown) | ⬜ Pending | — | — |
| [Pure JSON Option](#3-option-b-pure-json) | ⬜ Pending | — | — |
| [Hybrid: Structured Nodes](#4-option-c-hybrid---structured-nodes--markdown-content) | ⬜ Pending Review | — | — |
| [Hybrid: JSON Properties](#5-option-d-hybrid---json-properties--markdown-content) | ⬜ Pending | — | — |
| [Vector Embedding Strategy](#6-vector-embedding-considerations) | ⬜ Pending | — | — |

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md), [Knowledge Graph Master](../../Implemented/Masters/knowledge_graph_master.md)  
> **Affects**: [High-Fidelity Extraction](./high_fidelity_extraction_proposal.md), [Advanced RAG Enhancements](./advanced_rag_enhancements_proposal.md), [Knowledge Graph Enrichment](./knowledge_graph_enrichment_proposal.md)

---

## 1. Problem Statement

After extracting document content (text, tables, images, formatting, metadata, page structure), we must store it in a way that enables:

| Requirement | Description |
|-------------|-------------|
| **RAG retrieval** | LLM can understand and use the content |
| **Vector search** | Semantic similarity on embeddings |
| **Graph queries** | "Find all docs by author X", "Get page 27" |
| **Zero compression** | All extracted data accessible |
| **Citation support** | Link answers back to page/section |

### The Core Tension

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   LLM wants:              Neo4j wants:                      │
│   ─────────               ───────────                       │
│   • Natural prose         • Structured fields               │
│   • Token-efficient       • Queryable properties            │
│   • Markdown/text         • Indexed relationships           │
│                                                             │
│   These are DIFFERENT formats!                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Option A: Pure Markdown

Store everything as a single Markdown string with embedded annotations.

### Schema

```cypher
(d:Document {
  id: "doc_123",
  filename: "report.pdf",
  content: "---\nauthor: Jane...\n---\n# Chapter 1\n..."  // Everything here
})
```

### Example Content

```markdown
---
source: annual_report_2024.pdf
author: Jane Smith
created: 2025-01-05
total_pages: 45
---

<!-- PAGE 1 -->
# Annual Report 2024

Executive summary text here...

<!-- PAGE 27 -->
## Chapter 4: Financial Results

| Quarter | Revenue |
|---------|---------|
| Q1 | $1M |
| Q2 | $1.5M |

![Chart](chart_001.png)
**Visual Analysis**: Bar chart showing growth...
```

### Pros

| Advantage | Explanation |
|-----------|-------------|
| **Token efficient** | ~3x fewer tokens than JSON |
| **LLM-native** | Models trained on Markdown documentation |
| **Human readable** | Easy to debug and inspect |
| **Single source** | One field contains everything |
| **Annotations flexible** | HTML comments for metadata |

### Cons

| Disadvantage | Explanation |
|--------------|-------------|
| **No structured queries** | Can't do `WHERE doc.author = "Jane"` |
| **Parsing required** | Must parse Markdown to extract fields |
| **Blob storage** | Everything in one giant string |
| **No relationships** | No graph edges between pages/sections |

### When to Use
- Simple RAG with no complex queries
- Prototyping
- Small document collections

---

## 3. Option B: Pure JSON

Store everything as structured JSON with explicit fields.

### Schema

```cypher
(d:Document {
  id: "doc_123",
  filename: "report.pdf",
  content: '{"pages": [{"number": 1, "blocks": [...]}], "metadata": {...}}'
})
```

### Example Content

```json
{
  "source": "annual_report_2024.pdf",
  "metadata": {
    "author": "Jane Smith",
    "created": "2025-01-05T00:00:00Z",
    "total_pages": 45
  },
  "pages": [
    {
      "number": 1,
      "blocks": [
        {
          "type": "heading",
          "level": 1,
          "text": "Annual Report 2024",
          "formatting": {"font": "Arial", "size": 24, "bold": true}
        },
        {
          "type": "paragraph",
          "text": "Executive summary text here...",
          "formatting": {"font": "Arial", "size": 11}
        }
      ]
    },
    {
      "number": 27,
      "section": "Chapter 4: Financial Results",
      "blocks": [
        {
          "type": "table",
          "headers": ["Quarter", "Revenue"],
          "rows": [["Q1", "$1M"], ["Q2", "$1.5M"]]
        },
        {
          "type": "image",
          "id": "chart_001",
          "caption": "Bar chart showing growth",
          "analysis": {
            "chart_type": "bar",
            "data_points": {"Q1": 1000000, "Q2": 1500000}
          }
        }
      ]
    }
  ]
}
```

### Pros

| Advantage | Explanation |
|-----------|-------------|
| **Fully structured** | Every field explicitly named |
| **Programmatic access** | Easy to traverse in code |
| **Schema validation** | Can enforce structure |
| **Neo4j APOC support** | `apoc.convert.fromJsonMap()` |

### Cons

| Disadvantage | Explanation |
|--------------|-------------|
| **Token expensive** | ~3x more tokens than Markdown |
| **LLM unfriendly** | Models can get "lost" in deep nesting |
| **Verbose** | Lots of boilerplate (`"type":`, `"text":`) |
| **Still a blob** | Can't query inside without parsing |

### When to Use
- API responses
- Programmatic processing before LLM
- Interchange format between systems

---

## 4. Option C: Hybrid - Structured Nodes + Markdown Content

Store metadata as Neo4j properties/relationships, content as Markdown.

### Schema

```cypher
// Document node with queryable properties
(d:Document {
  id: "doc_123",
  filename: "report.pdf",
  author: "Jane Smith",
  created: datetime("2025-01-05"),
  total_pages: 45,
  file_type: "pdf"
})

// Page nodes with relationships
(p:Page {number: 27, section: "Chapter 4: Financial Results"})
(d)-[:HAS_PAGE]->(p)

// Chunk nodes with embeddings + Markdown content
(c:Chunk {
  id: "chunk_456",
  content: "## Financial Results\n\nOur Q4 performance exceeded...",
  page: 27,
  section: "Chapter 4",
  block_type: "text"
})
(p)-[:CONTAINS]->(c)

// Embedding stored separately or as vector property
(c)-[:HAS_EMBEDDING]->(e:Embedding {vector: [0.1, 0.2, ...]})
```

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        DOCUMENT                             │
│  Properties: author, created, filename, total_pages         │
│                           │                                 │
│              ┌────────────┼────────────┐                    │
│              ▼            ▼            ▼                    │
│          PAGE 1       PAGE 27      PAGE 45                  │
│           │              │             │                    │
│           ▼              ▼             ▼                    │
│        CHUNKS         CHUNKS        CHUNKS                  │
│    ┌─────────────┐                                         │
│    │ content:    │  ← Markdown string for LLM              │
│    │ "## Title   │                                         │
│    │ Text..."    │                                         │
│    │             │                                         │
│    │ embedding:  │  ← Vector for similarity search         │
│    │ [0.1, ...]  │                                         │
│    └─────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

### Example Queries

```cypher
// Find all documents by author
MATCH (d:Document {author: "Jane Smith"}) RETURN d

// Get all content from page 27
MATCH (d:Document)-[:HAS_PAGE]->(p:Page {number: 27})-[:CONTAINS]->(c:Chunk)
RETURN c.content

// Vector similarity search (with Neo4j vector index)
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $query_vector)
YIELD node, score
RETURN node.content, node.page, score

// Find chunks in Chapter 4
MATCH (c:Chunk {section: "Chapter 4"}) RETURN c.content
```

### Pros

| Advantage | Explanation |
|-----------|-------------|
| **Best of both worlds** | Structured queries + LLM-friendly content |
| **Graph relationships** | Navigate Document → Page → Chunk |
| **Queryable metadata** | Fast filters on author, date, page |
| **RAG-optimized chunks** | Each chunk is right-sized for context window |
| **Citation-ready** | Chunk knows its page/section for attribution |

### Cons

| Disadvantage | Explanation |
|--------------|-------------|
| **More complex schema** | Multiple node types and relationships |
| **Ingestion logic** | Must split document into chunks |
| **Storage overhead** | More nodes = more storage |
| **Chunking decisions** | How to split content (paragraph? section?) |

---

## 5. Option D: Hybrid - JSON Properties + Markdown Content

Similar to Option C, but use JSON for complex metadata within nodes.

### Schema

```cypher
(d:Document {
  id: "doc_123",
  filename: "report.pdf",
  // Simple fields as properties
  author: "Jane Smith",
  created: datetime("2025-01-05"),
  // Complex data as JSON
  formatting_summary: '{"fonts": ["Arial", "Times"], "colors": ["#000", "#333"]}'
})

(c:Chunk {
  content: "## Financial Results\n\n...",  // Markdown
  page: 27,
  bbox: '{"x": 72, "y": 100, "width": 468, "height": 200}',  // JSON for complex data
  formatting: '{"font": "Arial", "size": 11, "color": "#333333"}'
})
```

### When JSON is Appropriate

| Use JSON For | Example |
|--------------|---------|
| Bounding boxes | `{"x": 72, "y": 100, ...}` |
| Font details | `{"name": "Arial", "size": 11}` |
| Color palettes | `["#000", "#333", "#666"]` |
| Chart data points | `{"Q1": 1000000, "Q2": 1500000}` |

### When to Use Properties

| Use Properties For | Why |
|-------------------|-----|
| Author | Query: `WHERE d.author = "Jane"` |
| Date | Query: `WHERE d.created > date("2025-01-01")` |
| Page number | Query: `WHERE c.page = 27` |
| Section name | Query: `WHERE c.section = "Chapter 4"` |

---

## 6. Vector Embedding Considerations

Regardless of storage format, vector embeddings require special handling.

### What Gets Embedded?

| Content | Embed? | Rationale |
|---------|--------|-----------|
| Main text | ✅ Yes | Primary semantic content |
| Table data | ✅ Yes | Valuable for data queries |
| Image captions | ✅ Yes | Only text representation of visual |
| Formatting details | ❌ No | Not semantically meaningful |
| Metadata (author) | ❌ No | Use exact match queries instead |

### Chunking Strategy

```
Document (45 pages)
    │
    ├── Chunk 1: "# Executive Summary\n\nThis report covers..." (500 tokens)
    ├── Chunk 2: "## Market Analysis\n\nThe market grew..." (500 tokens)
    ├── Chunk 3: "| Quarter | Revenue |..." (300 tokens)
    └── ...
```

Each chunk needs:
- `content`: The Markdown text (for LLM)
- `embedding`: Vector representation (for similarity search)
- `page`: Source page number (for citation)
- `section`: Source section (for context)

### Embedding Storage in Neo4j

```cypher
// Option 1: Inline vector property
(c:Chunk {
  content: "...",
  embedding: [0.1, 0.2, 0.3, ...]  // 768 floats (Gemini embedding - current)
})

// Create vector index
CREATE VECTOR INDEX chunk_embeddings FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}
```

---

## 7. Comparison Matrix

| Criteria | Pure Markdown | Pure JSON | Hybrid (Nodes) | Hybrid (JSON Props) |
|----------|---------------|-----------|----------------|---------------------|
| **Token efficiency** | ✅ Excellent | ❌ Poor | ✅ Excellent | ✅ Excellent |
| **LLM comprehension** | ✅ Native | ⚠️ Ok | ✅ Native | ✅ Native |
| **Structured queries** | ❌ None | ⚠️ Parse first | ✅ Full | ✅ Full |
| **Graph traversal** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Schema complexity** | ✅ Simple | ✅ Simple | ⚠️ Medium | ⚠️ Medium |
| **Zero compression** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Citation support** | ⚠️ Parse | ⚠️ Parse | ✅ Native | ✅ Native |
| **Ingestion effort** | ✅ Low | ⚠️ Medium | ⚠️ Medium | ⚠️ Medium |

---

## 8. Recommendation

### For Davlon: **Option C (Hybrid - Structured Nodes + Markdown Content)**

```
┌───────────────────────────────────────────────────────────────┐
│                     RECOMMENDED ARCHITECTURE                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│   │  Document   │───▶│    Page     │───▶│   Chunk     │      │
│   │             │    │             │    │             │      │
│   │ author      │    │ number: 27  │    │ content: MD │      │
│   │ created     │    │ section     │    │ embedding   │      │
│   │ filename    │    │             │    │ page: 27    │      │
│   │ total_pages │    │             │    │ section     │      │
│   └─────────────┘    └─────────────┘    └─────────────┘      │
│                                                               │
│   Queryable fields    Graph edges       LLM-ready content    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Rationale

| Requirement | How Option C Satisfies |
|-------------|----------------------|
| RAG retrieval | Chunk `content` is Markdown → token efficient |
| Vector search | `embedding` property with Neo4j vector index |
| Graph queries | Properties like `author`, `page`, `section` |
| Zero compression | Formatting stored in JSON properties where needed |
| Citation support | Chunk knows `page` and `section` for attribution |

### Storage Pattern

```cypher
// Document level
CREATE (d:Document {
  id: $doc_id,
  filename: "report.pdf",
  author: "Jane Smith",
  created: datetime("2025-01-05"),
  total_pages: 45
})

// Page level (optional, for multi-page documents)
CREATE (p:Page {document_id: $doc_id, number: 27, section: "Chapter 4"})
CREATE (d)-[:HAS_PAGE]->(p)

// Chunk level (primary unit for RAG)
CREATE (c:Chunk {
  id: $chunk_id,
  content: "## Chapter 4: Financial Results\n\nOur Q4 exceeded...",
  embedding: $embedding_vector,
  document_id: $doc_id,
  page: 27,
  section: "Chapter 4",
  // Optional JSON for complex metadata
  formatting: '{"font": "Arial", "primary_color": "#333"}'
})
CREATE (p)-[:CONTAINS]->(c)
```

### When to Use JSON Properties

Only for **complex, non-queryable** metadata:
- Bounding boxes: `bbox: '{"x":72,"y":100,...}'`
- Font details: `formatting: '{"font":"Arial","size":11}'`
- Chart data: `chart_data: '{"Q1":1000000,"Q2":1500000}'`

**Never** for frequently queried fields (author, date, page, section).

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/ingestion.py` | Document extraction and storage |
| `backend/database.py` | Neo4j schema and queries |
| `backend/rag.py` | RAG retrieval and embeddings |
| `backend/graph_service.py` | Graph operations |
| `backend/semantic_chunker.py` | **Existing** embedding-based chunking implementation |

---

## Open Questions

1. ~~**Chunking granularity**: Should chunks be by paragraph, section, or page?~~  
   **RESOLVED**: System uses semantic chunking via `semantic_chunker.py` (embedding-based topic detection, target 600 chars, max 1500)
2. **Page node necessity**: Is the Page intermediate node worth the complexity for citation?
3. ~~**Embedding model**: Which embedding model for Neo4j vector index?~~  
   **RESOLVED**: Uses `text-embedding-3-small` (see `ingestion_pipeline_master.md`)

---

## Current Baseline vs. Proposed Enhancements

> This proposal builds upon the existing implementation. Below shows what exists vs. what this proposal adds.

| Aspect | Current Implementation | This Proposal Adds |
|--------|------------------------|-------------------|
| **Schema** | `Document → HAS_CHUNK → Chunk` | `Page` intermediate node for citation |
| **Chunk content** | Plain `text` string | Enriched Markdown with formatting annotations |
| **Metadata** | `source`, `category`, `content_type` | `page`, `section`, `bbox`, `formatting` (JSON) |
| **Embeddings** | 768d Gemini | Keep 768d (no change recommended) |
| **Spatial context** | None | Bounding boxes, adjacency relationships |

### Migration Notes

Adopting the full proposal would require:
1. Adding `Page` nodes and `:HAS_PAGE` relationships
2. Enriching `Chunk.text` with Markdown annotations (backward compatible)
3. Adding new properties (`page`, `section`, `bbox`) — no breaking changes

