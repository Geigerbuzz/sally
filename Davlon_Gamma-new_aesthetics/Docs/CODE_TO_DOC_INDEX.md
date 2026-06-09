# Code to Documentation Index

This file maps **code files** to **documentation** that should be updated when those files change.

> **How to use:** When you modify a code file, check this index to find related docs.
> 
> **How to maintain:** When adding `Related Code Files` sections to proposals, also add entries here.

---

## Backend Files

| Code File | Related Documents |
|-----------|-------------------|
| `backend/rag.py` | [RAG Retrieval Improvements](./Active/Proposals/rag_retrieval_improvements_proposal.md), [Adaptive Learning](./Active/Proposals/adaptive_learning_system_proposal.md), [Self-Adapting RAG](./Implemented/Proposals/self_adapting_rag_proposal.md), [Unified Labeling](./Active/Proposals/unified_document_labeling_proposal.md), [RAG Master](./Implemented/Masters/rag_system_master.md) |
| `backend/database.py` | [Adaptive Entity Intelligence](./Active/Proposals/adaptive_entity_intelligence_proposal.md), [Adaptive Learning](./Active/Proposals/adaptive_learning_system_proposal.md), [RAG Retrieval](./Active/Proposals/rag_retrieval_improvements_proposal.md), [Self-Adapting RAG](./Implemented/Proposals/self_adapting_rag_proposal.md), [Unified Labeling](./Active/Proposals/unified_document_labeling_proposal.md), [Knowledge Graph Master](./Implemented/Masters/knowledge_graph_master.md) |
| `backend/ingestion.py` | [Adaptive Entity Intelligence](./Active/Proposals/adaptive_entity_intelligence_proposal.md), [Adaptive Learning](./Active/Proposals/adaptive_learning_system_proposal.md), [RAG Retrieval](./Active/Proposals/rag_retrieval_improvements_proposal.md), [Self-Adapting RAG](./Implemented/Proposals/self_adapting_rag_proposal.md), [Unified Labeling](./Active/Proposals/unified_document_labeling_proposal.md), [Ingestion Master](./Implemented/Masters/ingestion_pipeline_master.md) |
| `backend/graph_service.py` | [Adaptive Entity Intelligence](./Active/Proposals/adaptive_entity_intelligence_proposal.md), [Self-Adapting RAG](./Implemented/Proposals/self_adapting_rag_proposal.md), [Knowledge Graph Master](./Implemented/Masters/knowledge_graph_master.md) |
| `backend/schema_learner.py` | [Adaptive Entity Intelligence](./Active/Proposals/adaptive_entity_intelligence_proposal.md), [Self-Adapting RAG](./Implemented/Proposals/self_adapting_rag_proposal.md) |
| `backend/learning_engine.py` | [Adaptive Learning](./Active/Proposals/adaptive_learning_system_proposal.md), [Unified Labeling](./Active/Proposals/unified_document_labeling_proposal.md) |
| `backend/semantic_chunker.py` | [RAG Retrieval](./Active/Proposals/rag_retrieval_improvements_proposal.md), [Ingestion Master](./Implemented/Masters/ingestion_pipeline_master.md) |
| `backend/document_lifecycle.py` | [Unified Labeling](./Active/Proposals/unified_document_labeling_proposal.md), [Document Lifecycle Master](./Implemented/Masters/document_lifecycle_master.md) |
| `backend/main.py` | [Widget Checklist](./Active/Proposals/widget_implementation_checklist.md) |

---

## Frontend Files

| Code File | Related Documents |
|-----------|-------------------|
| `public/widget_templates.js` | [Widget Checklist](./Active/Proposals/widget_implementation_checklist.md), [Widget Master](./Implemented/Masters/widget_system_master.md) |
| `public/widgets.js` | [Widget Checklist](./Active/Proposals/widget_implementation_checklist.md), [Widget Master](./Implemented/Masters/widget_system_master.md) |
| `public/dashboard.js` | [Widget Checklist](./Active/Proposals/widget_implementation_checklist.md) |
| `public/styles.css` | [Widget Checklist](./Active/Proposals/widget_implementation_checklist.md), [UI Master](./Implemented/Masters/ui_system_master.md) |
| `public/chat.js` | [UI Master](./Implemented/Masters/ui_system_master.md), [RAG Master](./Implemented/Masters/rag_system_master.md) |

---

## How Cascading Updates Work

```
1. You modify backend/rag.py
          ↓
2. Check this index → Find 5 related docs
          ↓
3. For each doc:
   - Update Implementation Status if feature completed
   - Check "Affects" links for downstream docs
   - Add [!NOTE] if behavior changed
          ↓
4. Run /sync-links to verify all links valid
```

---

## Adding New Entries

When you add a `Related Code Files` section to a proposal:

1. Find the code files listed
2. Add rows to this index file
3. Include the proposal in the "Related Documents" column

This keeps the reverse index in sync.
