# Master Data Pipeline Architecture

**Status**: Definitive Strategy
**Core Philosophy**: "Hybrid Intelligence"
- **Unstructured Data (Docs)**: Handled by **Gemini File Search API** (The "NotebookLM" Brain).
- **Structured Data (Relationships/Live)**: Handled by **Neo4j** (The "Graph" Brain).

---

## 1. The "NotebookLM" Backend (Gemini File Search)
*User Question: "How is NotebookLM able to cite sources? Can we use it as a backend?"*
**Yes.** The technology powering NotebookLM is the **Gemini File Search API**.
- **What it replaces**: It kills the traditional RAG stack (Pinecone, LangChain Chunking, Embedding Models).
- **How it verifies**: Google's models have native access to the file tokens during generation. It doesn't "guess" citations; it tracks which token ranges in the source influenced the output.
- **The API**: `google.generativeai` (Python SDK).

### Use Case in Pipeline
When a user uploads a **PDF, Contract, or Report**:
1.  **Ingest**: File is uploaded to Google's context cache (via API).
2.  **Query**: Users ask questions in the Session.
3.  **Answer**: Gemini returns the answer *with* inline citations metadata.
4.  **Zero-Hallucination**: We display these citations as clickable footnotes.

---

## 2. The Relationship Engine (Neo4j)
Gemini is great for reading *one* or *ten* documents, but it doesn't know "The Company". It doesn't know that "Alice" manages "Bob".
**Neo4j** stores the **State of the World**.

### Use Case in Pipeline
When a user uploads **CSVs, Live Feeds, or Org Charts**:
1.  **Ingest**: We parse the structured data.
2.  **Graph API**: `CREATE (p:Person {name: "Alice"})-[:MANAGES]->(p2:Person {name: "Bob"})`.
3.  **Reasoning**: "Who leads the biggest team?" -> Cypher Query to Neo4j.
4.  **Widget Configs**: Neo4j stores the dashboard layouts and widget definitions (Schemaless flexibility).

---

## 3. The Unified "Zero Hallucination" Workflow

### Scenario A: "Summarize the Q3 Report" (Document Task)
1.  **User** uploads `Q3_Report.pdf`.
2.  **System** sends to **Gemini File Search API**.
3.  **User Prompt**: "What was the churn rate?"
4.  **Backend**: Calls `model.generate_content([prompt, file_ref])`.
5.  **Result**: "Churn was 5% [Source: Page 12]".
6.  **Safety**: We trust Google's citation engine (proven state-of-the-art).

### Scenario B: "Create a Widget for Sales Leaders" (Structured Task)
1.  **User** connects `Salesforce API`.
2.  **System** ingests rows into **Neo4j** nodes `(:SalesPerson)-[:CLOSED]->(:Deal)`.
3.  **User Prompt**: "Show me the top 3 agents."
4.  **Backend**: Runs Cypher Query `MATCH (s:SalesPerson)... RETURN s, count(d)`.
5.  **Result**: Renders a Bar Chart Widget.
6.  **Safety**: Database queries are deterministic. No hallucination possible.

### Scenario C: "Complex Hybrid" (The Holy Grail)
*Question: "Does the Q3 Report explain why Alice's sales dropped?"*
1.  **Step 1 (Neo4j)**: System checks "Alice's Sales" in the Graph. -> *Confirms sales dropped 10%.*
2.  **Step 2 (Gemini)**: System asks Gemini: "Read `Q3_Report.pdf`. Does it mention 'Alice' or 'Sales Drop' reasons?"
3.  **Synthesized Answer**: "Yes. Neo4j confirms a 10% drop. The Q3 Report (Page 4) attributes this to 'Sector Volatility'."

---

## 4. Implementation Next Steps
1.  **Backend**:
    - Install `google-generativeai` SDK.
    - Set up `neo4j-driver`.
2.  **Frontend**:
    - Update `Sources` UI to distinguish "Documents" (sent to Google) vs "Data Feeds" (sent to Neo4j).
