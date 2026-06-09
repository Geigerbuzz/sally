---
title: Ingestion Pipeline Master
status: implemented
type: master
created: 2025-12-28
updated: 2025-12-28
tags: [ingestion, pipeline, chunking, extraction]
consolidates:
  - Active/Proposals/intelligent_ingestion_proposal.md
  - Active/Proposals/high_fidelity_extraction_proposal.md
  - Active/Proposals/multimodal_ingestion_proposal.md
---

# Ingestion Pipeline Master

The document processing layer of Davlon. Transforms uploaded files into searchable, embeddable chunks stored in Neo4j.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. FILE UPLOAD                                                       │
│     └── /api/ingest-document                                         │
│                                                                       │
│  2. EXTRACTION (file → text)                                          │
│     ├── PDF       → PyMuPDF text + pdfplumber tables + image caption │
│     ├── DOCX      → python-docx paragraphs                           │
│     ├── XLSX      → openpyxl row extraction                          │
│     ├── CSV       → Hybrid schema learning + entity creation         │
│     ├── PPTX      → Slide text + image captioning                    │
│     └── TXT/MD    → Direct text                                       │
│                                                                       │
│  3. CLASSIFICATION                                                    │
│     └── AI-driven category discovery (multi-category supported)      │
│                                                                       │
│  4. CHUNKING                                                          │
│     ├── Semantic chunking (embedding-based boundary detection)       │
│     ├── Content type tagging (text, table, image, graph)             │
│     └── Overlap application (30%, 50% for special categories)        │
│                                                                       │
│  5. EMBEDDING & STORAGE                                               │
│     ├── Gemini embedding (768 dimensions)                            │
│     ├── Neo4j Chunk nodes with vector index                          │
│     └── Parent-child chunk linking (:NEXT/:PREV)                     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Key Files

| File | Size | Purpose |
|------|------|---------|
| [ingestion.py](file:///Users/dora/Documents/Davlon_Gamma/backend/ingestion.py) | 22KB | HighFidelityIngestor class |
| [semantic_chunker.py](file:///Users/dora/Documents/Davlon_Gamma/backend/semantic_chunker.py) | 19KB | Embedding-based chunking |
| [csv_service.py](file:///Users/dora/Documents/Davlon_Gamma/backend/csv_service.py) | 12KB | Structured data + entity creation |
| [category_agent.py](file:///Users/dora/Documents/Davlon_Gamma/backend/category_agent.py) | 12KB | AI-driven category discovery |

---

## Implemented Features

### 1. Multi-Format Extraction
**Status**: ✅ Complete  
**Code**: `ingestion.py:HighFidelityIngestor`

| Format | Extractor | Notes |
|--------|-----------|-------|
| PDF | PyMuPDF + pdfplumber | Text + tables merged |
| DOCX | python-docx | Paragraphs preserved |
| XLSX | openpyxl | Sheets → rows |
| CSV | csv_service.py | Schema learning + graph entities |
| PPTX | python-pptx | Slide text + images |
| TXT/MD | Direct read | No processing needed |

---

### 2. AI-Driven Category Discovery
**Status**: ✅ Complete  
**Code**: `ingestion.py:_classify_document()`

- Categories learned from documents, not hardcoded
- Multi-category support (e.g., `["legal", "real_estate"]`)
- Updates Company Profile with new categories
- Uses CategoryManager for consistency

---

### 3. Semantic Chunking
**Status**: ✅ Complete  
**Code**: `semantic_chunker.py:semantic_chunk()`

Embedding-based boundary detection:

1. Split text into sentences
2. Embed each sentence
3. Calculate similarity between consecutive sentences
4. Break chunks at low-similarity points (topic shifts)
5. Merge small chunks, split large ones

Parameters:
```python
min_chunk_size: 100
max_chunk_size: 1500
target_chunk_size: 600
lookahead_window: 4
```

---

### 4. Content Type Detection
**Status**: ✅ Complete  
**Code**: `semantic_chunker.py:detect_content_type()`

| Type | Detection |
|------|-----------|
| `table` | Markdown table syntax (`\|...\|`) |
| `image` | Image captions (`[Image: ...]`) |
| `graph` | Chart/graph descriptions |
| `text` | Default for prose |

---

### 5. Chunk Overlap
**Status**: ✅ Complete  
**Code**: `semantic_chunker.py:apply_overlap()`

- Standard: 30% overlap
- Special categories (legal): 50% overlap
- Overlap uses whole sentences, not character boundaries

---

### 6. Parent-Child Chunk Linking
**Status**: ✅ Complete  
**Code**: `database.py:insert_chunk()`

Creates `:NEXT` and `:PREV` relationships:
```cypher
(Chunk1)-[:NEXT]->(Chunk2)
(Chunk2)-[:PREV]->(Chunk1)
```

Enables context expansion during retrieval.

---

### 7. Image Captioning
**Status**: ✅ Complete  
**Code**: `ingestion.py:_generate_caption()`

- Extracts images from PDFs via PyMuPDF
- Sends to Gemini for description
- Stores as `[Image: <caption>]` in chunks

---

## Neo4j Schema

```cypher
(:Chunk {
    id: string,
    text: string,
    embedding: [float],      // 768d vector
    source: string,          // Original filename
    category: [string],      // Dynamic categories
    content_type: string,    // text|table|image|graph
    position: int,           // Order in document
    created_at: datetime
})

(:Chunk)-[:NEXT]->(:Chunk)
(:Chunk)-[:PREV]->(:Chunk)
(:Document)-[:HAS_CHUNK]->(:Chunk)
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ingest` | POST | Legacy upload |
| `/api/upload` | POST | High-fidelity ingest |
| `/api/documents` | GET | List ingested docs |

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| 📋 Proposal | [Intelligent Ingestion](../../Active/Proposals/intelligent_ingestion_proposal.md) | Enhanced ingestion concepts |
| 📋 Proposal | [High Fidelity Extraction](../../Active/Proposals/high_fidelity_extraction_proposal.md) | Multi-layer extraction |
| 📋 Proposal | [Multimodal Ingestion](../../Active/Proposals/multimodal_ingestion_proposal.md) | Vision-first processing |
| 🔧 Master | [RAG System](./rag_system_master.md) | Consumes ingested chunks |
| 🔧 Master | [Knowledge Graph](./knowledge_graph_master.md) | Entity storage |
