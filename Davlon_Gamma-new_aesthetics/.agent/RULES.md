# Davlon Agent Rules

> **For AI Agents**: Read this file at the start of every session. These are mandatory rules for working on the Davlon project.

---

## 🎯 Project Mission

Davlon is a **zero-hallucination, self-adapting RAG system** for business document intelligence.

### Core Mantra
> *"Let the data teach the system, not the other way around."*

---

## 🧠 Philosophical Principles

These principles govern ALL design decisions in Davlon:

### 1. "Propose, Don't Dispose"
The AI **never executes the final mile** without human confirmation.
- ✅ Draft emails, prepare reports, suggest changes
- ❌ Send emails, delete data, auto-merge entities

> The AI's goal is to reduce friction to a single "Approve" click.

### 2. Zero-Hallucination Extraction
Use **deterministic code** to read data. AI only for what code can't do.
- ✅ `fitz.get_text()` to read PDF text
- ❌ Vision model "reading" a table from a screenshot

### 3. Zero Compression (Total Fidelity)
Extract **everything**. Discard **nothing**.
- Font names, colors (hex codes), sizes
- Headers, footers, page numbers
- Comments, tracked changes, metadata

> Test: *"What's the hex color of the footer on page 3?"* — Must be answerable.

### 4. Human-in-the-Loop (Confidence-Based)
The level of human involvement scales with confidence:

| Confidence | Action |
|------------|--------|
| **≥ 0.9** | Auto-apply (obvious cases) |
| **0.7–0.9** | Apply but flag for review |
| **0.5–0.7** | Create as "pending", notify user |
| **< 0.5** | Send to Inbox for explicit approval |

Examples:
- Entity merge at 0.95 confidence → Auto-merge
- Entity merge at 0.6 confidence → *"Is 'J. Smith' the same as 'John Smith'?"*
- Category promotion at 0.85 → Apply, note in activity log

### 5. Self-Adapting Intelligence
The system learns from data, not hardcoded rules:
- **Categories**: Discovered from document content, not predefined lists
- **Entity types**: Learned from what users upload (Patients, Properties, Cases...)
- **Terminology**: Domain vocabulary extracted from documents
- **Relationships**: Inferred from patterns, not fixed schemas

> The system should work for a hospital, law firm, or retailer — with zero configuration.

### 6. Sentinel-Style Learning
The AI continuously monitors patterns and surfaces what matters:
- **Observe** — Collect signals from user behavior, queries, and data changes
- **Learn** — Detect patterns, anomalies, and emerging importance
- **Surface** — Present insights proactively (widgets, briefings, suggestions)

Human decisions are only required when the system proposes a *change*, not when it presents *information*.

### 7. Domain-Agnostic Design
Davlon works for **any** industry, company size, or use case — without code changes.

No assumptions about what the user's business does. The system discovers terminology, entity types, and workflows from the data itself.

---

## 📋 Mandatory Workflows

Before performing these actions, **you MUST read and follow the corresponding workflow**:

| Action | Workflow | Why |
|--------|----------|-----|
| Creating documentation | `/create-doc` | Ensures frontmatter, status tables, related code sections |
| Moving to Implemented | `/mark-implemented` | Updates registry, moves files correctly |
| Updating registry | `/update-registry` | Keeps index in sync |
| Checking doc status | `/audit-doc` | Cross-references code and proposals |
| Finding related docs | `/find-docs` | Avoids duplicates |

**How to use**: Read `.agent/workflows/{workflow-name}.md` before taking action.

### 🔴 Mandatory Post-Edit Audit

- After **any** creation or modification of a document in `Docs/` → run `/audit-doc` on that document
- After **any** code change → audit all documents listed in the file's "Related Code Files" reverse-index

No exceptions.

### 🔴 Understand the Baseline First

Before proposing or designing **any** feature, understand what already exists:
1. Skim `Docs/Implemented/` for relevant masters
2. Check `REGISTRY.md` for related proposals
3. Reference the current state as context, not as a constraint

---

## 🔒 Ground Rules

### Code Quality
- Never use placeholder data — generate working examples or use real values
- Test changes before claiming completion
- Include error handling in all code

### Extraction & RAG
- **Zero hallucination**: Use deterministic parsers (`fitz`, `python-docx`, etc.)
- **Zero compression**: Preserve formatting, colors, metadata, page structure
- **AI only for images**: Captioning charts/photos, never reading text

### Communication
- When unsure, ask — don't assume
- Cite specific files and line numbers
- Acknowledge mistakes, don't hide them

---

## 🗂️ File Organization

```
Docs/
├── Active/           # Current work
│   ├── Proposals/    # Features pending implementation
│   ├── Specs/        # Technical specifications
│   └── Guides/       # How-to guides
├── Implemented/      # Completed work
├── Archive/          # Historical reference
│   ├── Superseded/   # Replaced by newer docs
│   └── Discarded/    # Rejected features
└── REGISTRY.md       # Master index — ALWAYS update this
```

**Rule**: Always update `REGISTRY.md` when creating, moving, or archiving documents.

---

## 🔗 Key Reference Documents

| Document | Purpose |
|----------|---------|
| [Preemptive AI Strategy](Docs/Active/Proposals/preemptive_ai_strategy.md) | "Propose, Don't Dispose" philosophy |
| [Self-Adapting RAG](Docs/Implemented/Proposals/self_adapting_rag_proposal.md) | Domain-agnostic architecture |
| [High-Fidelity Extraction](Docs/Active/Proposals/high_fidelity_extraction_proposal.md) | Zero-compression extraction |
| [Adaptive Learning System](Docs/Active/Proposals/adaptive_learning_system_proposal.md) | Sentinel-style learning |

---

## ⚠️ Before You Start Any Task

1. Check `Docs/REGISTRY.md` for existing related documents
2. Check `.agent/workflows/` for applicable workflows
3. Ensure your approach aligns with the philosophical principles above
4. Follow this file's ground rules throughout

---

*Last updated: 2026-01-08*
