---
title: Decision Log
status: active
type: meta
created: 2025-12-28
updated: 2025-12-28
tags: [meta, decisions, architecture]
---

# Decision Log

> A record of key architectural and design decisions. Each entry captures the full thought process so future-you can remember why things are the way they are.

---

## 2025-12-28

### Use Neo4j Aura as the Single Database

**Decision**: Use Neo4j Aura for everything — vector embeddings, document chunks, entity relationships, and metadata.

**The Thinking**: The original pitch was to use a "proper" vector database like Pinecone or Weaviate for embeddings, then Postgres or a separate graph DB for structured data. But this split-stack approach creates problems:

1. **Latency**: Every query would need to hit two databases — first vector search, then graph lookup for relationships. That's two round trips.
2. **Consistency**: Keeping two databases in sync is a nightmare. What happens if a chunk is in the vector DB but the entity linking failed in the graph?
3. **Deployment complexity**: Two managed services, two connection strings, two failure modes.

Then Neo4j Aura added native vector indexes. Suddenly we could store the embedding *on the same node* as the text and relationships. One query can do: "find similar chunks" AND "traverse to related entities" in a single hop.

The tradeoff is that Neo4j's vector search isn't as feature-rich as dedicated vector DBs (no hybrid keyword search out of the box), but for our scale and use case, the simplicity wins. We can always add a dedicated vector DB later if we hit performance walls.

**Affects**: All data storage, the hybrid search in `database.py`, entity creation in `graph_service.py`. This is a foundational decision — changing it would be a major migration.

---

### Build a Custom Markdown Renderer

**Decision**: Write our own Markdown parser in `chat.js` instead of using marked.js or another library.

**The Thinking**: We tried marked.js first. It worked for normal Markdown, but AI output is *weird*. LLMs produce things like:

- **Headers without newlines**: `**Title**\nSome text` (not a real `## Header`)
- **Tight list spacing**: No blank lines between items
- **Mixed formatting**: Bold inside headers, nested code blocks

marked.js either choked on these or rendered them ugly. We'd get collapsed lists, broken code blocks, or just raw asterisks showing through.

The options were:
1. **Post-process AI output** before rendering — hacky, fragile
2. **Pre-process with regex** to "fix" the Markdown — also fragile
3. **Build our own parser** that's forgiving and handles AI quirks

We went with option 3. It's more work upfront, but now we have complete control. When the AI does something weird, we can adjust the parser without waiting for a library update. We also added the `.chat-md` CSS scope so chat styling doesn't leak elsewhere.

The downside is we're maintaining custom code, but it's ~200 lines and stable.

**Affects**: `public/chat.js`, chat interface rendering. If we ever switch chat UIs or frameworks, we'd port this logic.

---

### Template-Based Widget Generation (No Raw Code)

**Decision**: AI generates JSON payloads that conform to predefined templates (KPI, Chart, Table). The frontend renders these. AI never writes HTML/CSS directly.

**The Thinking**: The dream was "describe a widget in English, AI writes the code, widget appears." We tried it. It was a disaster:

- Random spacing, broken flexbox
- Hardcoded colors that clashed with dark mode
- Inline styles that couldn't be themed
- Sometimes the AI would forget to close a div

The fundamental problem is that code generation is *open-ended*. There are infinite ways to write a bar chart. The AI picks one, and it's usually subtly wrong.

Templates flip this around. We define *exactly* how a KPI card looks (the HTML, the CSS, the layout). The AI's job is just filling in: title, value, trend direction, icon. It's like a form, not a canvas.

Now widget generation is deterministic. If the JSON is valid, the widget *will* render correctly. The AI can focus on "what data should this show" instead of "how do I write a flexbox container."

The tradeoff is we can only generate widgets we have templates for. But that's actually a feature — it keeps the dashboard consistent.

**Affects**: `/api/generate-widget` endpoint, `widget_templates.js`, the entire widget creation flow.

---

### Semantic Chunking Instead of Fixed-Size Splitting

**Decision**: Split documents using embedding similarity to detect topic boundaries, not arbitrary character counts.

**The Thinking**: The naive approach is "split every 500 characters." Simple, fast, predictable. But it produces garbage retrieval:

- A chunk might start mid-sentence: "...the interest rate is 5.2% APR."
- Topic A and Topic B get mashed into one chunk
- Tables get sliced in half

When RAG retrieves these chunks, the LLM gets confused. It sees fragments, not coherent information.

Semantic chunking works differently:
1. Split into sentences
2. Embed each sentence
3. Compare consecutive sentences — if similarity drops, that's a topic boundary
4. Group sentences into chunks that stay within size limits but respect boundaries

Now each chunk is a complete "thought." When we retrieve "the chunk about interest rates," we get the full explanation, not a fragment.

The cost is complexity (embedding every sentence) and latency (more API calls during ingestion). But ingestion is a background job — we can afford to be slow there. Retrieval quality is what matters.

**Affects**: `semantic_chunker.py`, ingestion pipeline, and indirectly RAG quality. This was one of the bigger wins for answer accuracy.

---

### Soft Exclusion for Stale Documents

**Decision**: When a document becomes "legacy" (old, unused), deprioritize it in search rather than deleting it. Show admin an inbox notification for final decision.

**The Thinking**: The easy approach is automatic cleanup: "Documents not accessed in 90 days get deleted." But users hate this. They upload something important, forget about it, then panic when it's gone.

We considered:
1. **Auto-delete with warning** — Still deletes, users still panic
2. **Never delete** — Database bloat, irrelevant results
3. **Soft exclusion** — Keep the data, just lower its search weight

Soft exclusion is a middle ground. A "legacy" document:
- Doesn't appear in normal search results
- Is still in the database
- Can be restored with one click

The admin gets an inbox notification: "This document hasn't been accessed in 6 months. Archive, restore, or delete?" This puts a human in the loop for destructive actions.

The tradeoff is complexity — we need to track document status, permanence scores, and inbox workflows. But it matches how people actually think about data: "I might need this someday."

**Affects**: `document_lifecycle.py`, inbox notifications, search result filtering.

---

### Flash-Lite for Classification, Flash for Generation

**Decision**: Use `gemini-2.5-flash-lite` for fast, cheap tasks (query classification, expansion). Use `gemini-2.5-flash` for actual answer generation. Don't use Pro yet.

**The Thinking**: Not all AI tasks are equal. Classifying a query into "factual" vs "comprehensive" doesn't need a big model — it's essentially pattern matching. But generating a nuanced answer with citations? That needs more capability.

Flash-lite is ~2x cheaper and faster than Flash. For classification, it's plenty. We call it for:
- Query intent classification (factual, analytical, summary...)
- Multi-category detection
- Query expansion (synonyms)

Flash handles the main generation where quality matters. We configured Pro in the model dictionary but haven't activated it — Flash is good enough for now, and Pro is 8x more expensive.

The logic is in `select_model_for_corpus()`. It *could* pick Pro for complex queries, but currently it just returns Flash. We're leaving the door open for later.

**Affects**: API costs, latency. This is a tuning decision we can revisit as the corpus grows.

---

### Vanilla JS over React/Next.js

**Decision**: Keep the frontend as vanilla HTML/CSS/JS rather than migrating to a component framework.

**The Thinking**: We evaluated three paths for the frontend:

1. **React + Vite** — Industry standard, great component model
2. **Next.js** — Server-side rendering, file-based routing
3. **Vanilla JS** — No build step, no node_modules

The codebase is currently vanilla. Migrating would mean:
- Rewriting every page as components
- Adding a build pipeline (Vite/Webpack)
- Managing state (React Context, Zustand, etc.)
- Training on new patterns

For a small team (or solo), this is weeks of work with no user-visible benefit. The current pages load fast, have no hydration issues, and are easy to debug (just View Source).

The trigger to revisit: When we have 10+ pages sharing the same UI patterns (modals, tables, forms) and copy-pasting becomes painful. At that point, components pay for themselves.

For now, vanilla wins because:
- Zero build time
- Works on Railway without Node
- Any developer can read it immediately

**Affects**: All `public/` files. This is a "not yet" decision, not a "never" decision.

---

## Template for New Entries

```markdown
### [Short Title]

**Decision**: [What was decided — one sentence]

**The Thinking**: [The full thought process. What problem were we solving? What options did we consider? Why did we pick this one? What are the tradeoffs? Write this like you're explaining to yourself in 6 months.]

**Affects**: [What parts of the system this impacts, key files]
```
