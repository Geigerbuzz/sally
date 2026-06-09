---
title: Backend Reminders & Future Work
status: active
type: notes
created: 2025-12-15
updated: 2025-12-28
tags: [reminders, backend, infrastructure]
parent: null
children: []
related:
  - ./multi_category_query_proposal.md
  - ./production_hardening.md
---

# Backend Reminders & Future Work

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Pydantic Schemas](#1-code-implemented) | ✅ Complete | 2025-12-15 | `pipeline/models.py` |
| [Citation Enforcer](#1-code-implemented) | ✅ Complete | 2025-12-15 | `pipeline/auditor.py` |
| [PDF Ingestion](#b-ingestion-priority) | ✅ Complete | 2025-12-20 | `ingestion.py` |
| [APScheduler Jobs](#4-reminders--future-work) | ⬜ Pending | — | — |
| [Error Reporting Config](#4-reminders--future-work) | ⬜ Pending | — | — |

> **Affects**: [Production Hardening](./production_hardening.md), [Multi-Category Query](./multi_category_query_proposal.md)

---

I have successfully scaffolded the **Zero-Hallucination Pipeline**. 

## 1. Code Implemented
- **`backend/pipeline/models.py`**: Strict Pydantic schemas defining `Citation`, `DataChunk`, and `VerifiedInsight`.
- **`backend/pipeline/auditor.py`**: The "Citation Enforcer" logic. It strictly rejects any sentence in a drafted answer that cannot be grounded in a retrieved chunk.

## 2. Critical Decisions Required

### A. Infrastructure Mode
To make this "real code" runnable, I need to know the target environment.
- **Option A: Cloud Native (Recommended for Prom)**
    - Depends on **Neo4j Aura** and **Pinecone** active instances.
    - Requires API Keys.
- **Option B: Local Simulation (Easier for Dev)**
    - Uses **NetworkX** (in-memory graph) and **ChromaDB** (local vector).
    - No API keys needed, runs fully on your machine.

### B. Ingestion Priority
Which part of the pipeline should I build next?
1.  **PDF/Document Ingestion**: Parsing "Quarterly Report.pdf" into chunks?
2.  **Live API Streams**: Validating JSON data from Zillow/MLS?

## 3. Next Steps
Once you define the above, I will:
1.  Implement `ingest.py` for the chosen data type.
2.  Wire up a `FastAPI` server in `main.py`.
3.  Connect the Frontend "Upload" button to this local server.

---

## 4. Reminders / Future Work

- **Update the document ingestion tagger** to have the AI have more tags like "memos" and also "misc" and have the system first go through all documents with relevant tags before going through the "misc" tags to see if there is any citation to be done.

- **Link related categories to each widget** so that they can be checked for updates when changes happen to these categories.

- **Auto-create empty categories from knowledge gaps?** When an admin acknowledges a knowledge gap alert, should the system automatically create an empty category for it? Or wait for user to upload documents first? (See multi_category_query_proposal.md)

- **Reconsider max K ceiling (currently ~45-60)** — With Gemini's 1M token context, we could increase max chunks to 100-200 for enterprise-scale deployments. Current conservative limit is fine for early adoption. Revisit when users have 10K+ chunks.

- **Consider LLM reranking (Flash-Lite ~$0.0015/query)** — If answer quality degrades or verification failures increase, add a reranking step using Gemini Flash-Lite. Currently skipped since we verify at output stage. Revisit if corpus grows past 10K chunks or users complain about relevance.

- **Configure Error Reporting Notifications** — Error reports from the frontend popup require `.env` configuration:
  ```bash
  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  ERROR_REPORT_EMAIL=your-email@example.com
  SMTP_USER=your-gmail@gmail.com
  SMTP_PASSWORD=your-app-password  # Use Gmail App Password
  SMTP_HOST=smtp.gmail.com  # Default
  SMTP_PORT=587  # Default
  ```

- **Install APScheduler for scheduled jobs** — The daily maintenance jobs (lifecycle re-evaluation, expansion pruning) require APScheduler:
  ```bash
  pip install apscheduler
  ```
  Add to `requirements.txt`: `apscheduler>=3.10.0`
