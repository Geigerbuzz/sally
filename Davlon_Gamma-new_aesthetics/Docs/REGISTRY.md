---
title: Documentation Registry
status: active
type: master
created: 2025-12-28
updated: 2025-12-28
tags: [meta, documentation, index]
---

# Documentation Registry

> **For AI Agents**: Always read this file first when asked to work with documentation.
> Use this registry to discover, create, and update documents.
> See `.agent/workflows/` for standard operations.

## Quick Stats
- Active documents: 36
- Implemented: 16
- Archived: 3
- Last updated: 2025-12-28

---

## How to Use This Registry

1. **Finding docs**: Search this file for keywords, check the tables below
2. **Creating docs**: Use `/create-doc` workflow — add entry here after creation
3. **Implementing**: Use `/mark-implemented` workflow — move entry between sections
4. **Full refresh**: Use `/update-registry` workflow to rescan all docs
5. **Maintain links**: Use `/sync-links` workflow to verify bidirectional hyperlinks

---

## Active Work

### Proposals (Pending Implementation)

| Document | Status | Tags | Summary |
|----------|--------|------|---------|
| [unified_document_labeling_proposal.md](./Active/Proposals/unified_document_labeling_proposal.md) | review | `rag`, `documents`, `categories` | Adaptive AI-discovered categories with special category behaviors |
| [adaptive_learning_system_proposal.md](./Active/Proposals/adaptive_learning_system_proposal.md) | draft | `ai`, `learning`, `categories` | Category intelligence engine with signal-based learning |
| [advanced_rag_enhancements_proposal.md](./Active/Proposals/advanced_rag_enhancements_proposal.md) | draft | `rag`, `search`, `retrieval` | Query expansion, semantic chunking, document lifecycle |
| [confidence_calibrated_retrieval_proposal.md](./Active/Proposals/confidence_calibrated_retrieval_proposal.md) | draft | `rag`, `confidence`, `retrieval` | Calibrated confidence scoring for retrieval |
| [document_lifecycle_management_proposal.md](./Active/Proposals/document_lifecycle_management_proposal.md) | draft | `documents`, `lifecycle` | Permanence scoring and decay management |
| [high_fidelity_extraction_proposal.md](./Active/Proposals/high_fidelity_extraction_proposal.md) | draft | `ingestion`, `extraction` | Comprehensive document extraction (all formats) |
| [intelligent_ingestion_proposal.md](./Active/Proposals/intelligent_ingestion_proposal.md) | draft | `ingestion`, `ai` | Smart document ingestion pipeline |
| [knowledge_graph_enrichment_proposal.md](./Active/Proposals/knowledge_graph_enrichment_proposal.md) | draft | `neo4j`, `knowledge-graph` | Enriching the knowledge graph |
| [multi_category_query_proposal.md](./Active/Proposals/multi_category_query_proposal.md) | draft | `rag`, `categories`, `query` | Multi-category document handling |
| [multimodal_ingestion_proposal.md](./Active/Proposals/multimodal_ingestion_proposal.md) | draft | `ingestion`, `multimodal` | Image and chart extraction |
| [rag_retrieval_improvements_proposal.md](./Active/Proposals/rag_retrieval_improvements_proposal.md) | draft | `rag`, `retrieval` | RAG retrieval optimizations |
| [widget_customization_implementation.md](./Active/Proposals/widget_customization_implementation.md) | draft | `widgets`, `ui` | Widget customization system |
| [widget_generation_proposal.md](./Active/Proposals/widget_generation_proposal.md) | draft | `widgets`, `ai` | AI-powered widget generation |
| [widget_types_and_visualization_proposal.md](./Active/Proposals/widget_types_and_visualization_proposal.md) | draft | `widgets`, `visualization` | Widget types and visualization standards |
| [workspace_expansion_proposal.md](./Active/Proposals/workspace_expansion_proposal.md) | draft | `workspace`, `multi-tenant` | Workspace expansion features |
| [adaptive_entity_intelligence_proposal.md](./Active/Proposals/adaptive_entity_intelligence_proposal.md) | draft | `ai`, `entities`, `knowledge-graph` | Self-correcting entity & relationship discovery |
| [multi_tenant_security_proposal.md](./Active/Proposals/multi_tenant_security_proposal.md) | draft | `security`, `auth`, `multi-tenant` | RBAC, row-level security, Clerk integration |
| [document_storage_format_proposal.md](./Active/Proposals/document_storage_format_proposal.md) | draft | `storage`, `neo4j`, `rag`, `architecture` | Storage format strategy: Markdown vs JSON vs Hybrid |

### Specs (Technical Specifications)

| Document | Status | Tags | Summary |
|----------|--------|------|---------|
| [Master_Data_Pipeline.md](./Active/Specs/Master_Data_Pipeline.md) | approved | `pipeline`, `data` | Master data pipeline architecture |
| [Why_Neo4j.md](./Active/Specs/Why_Neo4j.md) | approved | `neo4j`, `architecture` | Neo4j selection rationale |

### Notes & Working Documents

| Document | Tags | Summary |
|----------|------|---------|
| [Small_Details.md](./Active/Proposals/Small_Details.md) | `ui`, `polish` | Small UI polish items |
| [backend_reminders.md](./Active/Proposals/backend_reminders.md) | `backend`, `todo` | Backend implementation reminders |
| [preemptive_ai_strategy.md](./Active/Proposals/preemptive_ai_strategy.md) | `ai`, `philosophy` | Preemptive AI design philosophy |
| [production_hardening.md](./Active/Proposals/production_hardening.md) | `production`, `security` | Production hardening checklist |
| [shock_ideas.md](./Active/Proposals/shock_ideas.md) | `ideas`, `wow-factor` | Impressive feature ideas |
| [widget_implementation_checklist.md](./Active/Proposals/widget_implementation_checklist.md) | `widgets`, `checklist` | Widget implementation tracking |

---

## Implemented

Documents for features that are now in production code.

### Proposals

| Document | Implemented Date | Code Location | Summary |
|----------|-----------------|---------------|---------|
| [inline_citations_proposal.md](./Implemented/Proposals/inline_citations_proposal.md) | 2025-12-18 | `public/chat.js` | Inline "Truth Dot" citations in chat |
| [markdown_overhaul.md](./Implemented/Proposals/markdown_overhaul.md) | 2025-12-18 | `public/chat.js` | Custom forgiving Markdown engine |
| [legacy_document_management_proposal.md](./Implemented/Proposals/legacy_document_management_proposal.md) | 2025-12-27 | `backend/document_lifecycle.py` | Soft exclusion legacy handling |
| [data_sources_ux_proposal.md](./Implemented/Proposals/data_sources_ux_proposal.md) | 2025-12-27 | `public/sources_legacy.html` | Legacy tab UX design |
| [finishing_partial_implementations.md](./Implemented/Proposals/finishing_partial_implementations.md) | 2025-12-27 | Various | RAG implementation completion |
| [self_adapting_rag_proposal.md](./Implemented/Proposals/self_adapting_rag_proposal.md) | 2025-12-21 | `company_profile.py`, `category_agent.py` | Self-learning company profile and RAG |

### Guides (Production Documentation)

| Document | Tags | Summary |
|----------|------|---------|
| [first_run_guide.md](./Implemented/Guides/first_run_guide.md) | `setup`, `guide` | First-time setup guide |
| [railway_deployment_checklist.md](./Implemented/Guides/railway_deployment_checklist.md) | `deployment`, `railway` | Railway deployment steps |

---

## Masters (Source of Truth)

Consolidated documents that supersede multiple proposals.

| Topic | Document | Last Updated | Consolidates |
|-------|----------|--------------|--------------|
| RAG System | [rag_system_master.md](./Implemented/Masters/rag_system_master.md) | 2025-12-28 | Query classification, hybrid search, verification |
| Widget System | [widget_system_master.md](./Implemented/Masters/widget_system_master.md) | 2025-12-28 | Templates, drag-drop, AI generation |
| Ingestion Pipeline | [ingestion_pipeline_master.md](./Implemented/Masters/ingestion_pipeline_master.md) | 2025-12-28 | Extraction, chunking, embedding |
| Knowledge Graph | [knowledge_graph_master.md](./Implemented/Masters/knowledge_graph_master.md) | 2025-12-28 | Neo4j schema, vector search, entities |
| UI System | [ui_system_master.md](./Implemented/Masters/ui_system_master.md) | 2025-12-28 | Design system, pages, Markdown engine |
| Document Lifecycle | [document_lifecycle_master.md](./Implemented/Masters/document_lifecycle_master.md) | 2025-12-27 | Legacy management, permanence scoring |

---

## Archive

### Superseded

Documents replaced by newer versions or consolidated into masters.

| Document | Superseded By | Reason |
|----------|---------------|--------|
| [data_pipeline_proposal.md](./Archive/Superseded/data_pipeline_proposal.md) | `Active/Specs/Master_Data_Pipeline.md` | Consolidated into master pipeline doc |
| [true_rag_proposal.md](./Archive/Superseded/true_rag_proposal.md) | Various RAG proposals | Split into specific RAG proposals |
| [universal_data_extraction_strategy.md](./Archive/Superseded/universal_data_extraction_strategy.md) | `high_fidelity_extraction_proposal.md` | Merged into comprehensive extraction proposal |

### Discarded

Features that were considered but rejected.

| Document | Reason |
|----------|--------|
| [discarded_features.md](./Archive/Discarded/discarded_features.md) | Tracks all discarded feature decisions |

---

## Reports

Generated analysis and audit reports.

| Document | Generated | Summary |
|----------|-----------|---------|
| [code_revision_lifecycle_2024_12_21.md](./Reports/code_revision_lifecycle_2024_12_21.md) | 2024-12-21 | Code revision analysis |

---

## Agent Guidelines

### Document Lifecycle

```
Draft → Review → Approved → Implemented → (Master if consolidating)
                         ↓
                    Archived (if superseded)
                         ↓
                    Discarded (if rejected)
```

### When Creating New Documents

1. Check this registry for existing related docs
2. Use `/create-doc` workflow for proper structure
3. Add entry to this registry under "Active Work"
4. Use standardized frontmatter (see workflow)

### When Updating Documents

1. Update the `updated:` field in frontmatter
2. If status changes, update this registry
3. If implementing, use `/mark-implemented` workflow

### Related Workflows

- `/create-doc` — Create new documentation
- `/find-docs` — Search for related documents
- `/mark-implemented` — Mark as implemented and move
- `/update-registry` — Refresh this registry from source

---

## Folder Structure

```
Docs/
├── REGISTRY.md           # 👈 You are here - the index
├── Active/               # Current work
│   ├── Proposals/        # 23 proposals awaiting implementation
│   ├── Specs/            # 13 technical specifications
│   └── Guides/           # (empty - guides go to Implemented when done)
├── Implemented/          # Completed work
│   ├── Proposals/        # 5 implemented proposals
│   ├── Specs/            # (empty)
│   ├── Masters/          # 1 consolidated source-of-truth doc
│   └── Guides/           # 10 production guides
├── Archive/              # Historical reference
│   ├── Superseded/       # 2 replaced documents
│   └── Discarded/        # 1 rejected features tracker
└── Reports/              # 1 generated report
```
