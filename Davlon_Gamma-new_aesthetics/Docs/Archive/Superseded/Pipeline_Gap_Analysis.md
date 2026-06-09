# Master Pipeline: Missing Pieces & Gap Analysis

The `Master_Data_Pipeline.md` covers the **Ingestion** and **Reasoning** flow perfectly.
However, for a Production B2B App, we are missing three critical "Invisible" layers.

## 1. Data Governance & RBAC (The Security Gap)
*Current State*: If a file is uploaded, Gemini/Neo4j answers questions about it.
*The Problem*: Not every agent should see the "CEO Compensation Report".
*The Fix*: **Row-Level Security (RLS)**.
- **Neo4j**: Tags nodes with `(n:Sensitive {role: "admin"})`.
- **Gemini**: The prompt must include a filter: *"Only answer using chunks tagged with roles the user possesses."*
- **Action**: We need a "Permissions" module in `models.py`.

## 2. Data Freshness & Expiry (The Stale Data Gap)
*Current State*: Data is ingested and stays forever.
*The Problem*: Specific data expires. "Active Listings" become "Sold". "Q3 Report" becomes irrelevant in Q4.
*The Fix*: **TTL (Time To Live)** policies.
- **Graph**: Auto-archive nodes after X days.
- **Vector**: Purge old indices to keep search relevant.

## 3. Feedback Loop (The Learning Gap)
*Current State*: The "Auditor" is a hardcoded logic gate.
*The Problem*: What if the Auditor is wrong? What if it redacts a true fact?
*The Fix*: **RLHF (Reinforcement Learning from Human Feedback)**.
- **UI**: When the user sees a "Redacted" answer or a widget, add a "Report Issue" button.
- **Loop**: These reports go to a "Training Queue" to fine-tune the Auditor prompts over time.
