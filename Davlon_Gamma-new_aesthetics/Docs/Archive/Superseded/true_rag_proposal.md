# Proposal: True GraphRAG Architecture (The "No Compromise" Stack)

## 1. The Pivot: Context Stuffing vs. True RAG
*   **Current State (Context Stuffing)**: We dump every file into the prompt.
    *   *Reliability Risk*: Token overflow, distraction, high cost.
*   **Target State (True GraphRAG)**: We retrieve only the exact chunks needed, using both semantic similarity (Vectors) and structural relationships (Graph).

## 2. Architecture: Neo4j as the "One Truth"
We will not just add a Vector DB (like Pinecone); we will upgrade our existing **Neo4j** instance to handle Vectors too. This is **GraphRAG**.

### The Hybrid Index
1.  **Vector Index**: Stores embeddings of document chunks. Finds "conceptually similar" text.
2.  **Knowledge Graph**: Stores entities (Company, Contract, Person). Finds "factually related" data.

### The Pipeline
1.  **Ingestion ("The Shredder")**:
    *   PDF Upload -> Text Extraction -> **Chunking** (Recursive Splitter: 500 chars).
    *   **Embedding**: Convert chunks to vectors using **`gemini-embedding-001`** (SOTA Model).
    *   **Storage**: Save Chunk Nodes in Neo4j with Vector properties (Dimension: 768 or 3072).
2.  **Retrieval ("The Sniper")**:
    *   User Query -> Embedding.
    *   **Vector Search**: Find top 20 chunks similar to query.
    *   **Graph Traversal**: Expand to neighbor nodes (e.g., "Find the 'Revenue' node linked to these chunks").
    *   **Context Window**: Send *only* these verified chunks to Gemini 1.5 Pro.

## 3. The "Hidden Corners" Audit (Technical Debt)
You asked for transparency. Here is what else is currently "Lite" or missing:

| Feature | Current "Lite" Implementation | The "Production" Standard | Impact |
| :--- | :--- | :--- | :--- |
| **Chat History** | **Ephemeral (RAM)** | **Persistent DB (Postgres/Neo4j)** | Chats vanish if you refresh. No "Memory". |
| **User Auth** | **Zero (Single User)** | **OAuth2 / Clerk** | Anyone with the link is Admin. |
| **Testing** | **Manual Only** | **CI/CD Unit Tests (Pytest)** | Updates might break old features silently. |
| **Error Handling** | **Crash & Log** | **Retry Queues (Celery)** | Failed uploads are lost forever. |
| **Rate Limiting** | **None** | **Redis Token Bucket** | Spamming crashes the API quota. |

## 4. Implementation Steps (GraphRAG)
1.  **Update `database.py`**: Add `Vector Index` creation logic.
3.  **Update `rag.py`**: Switch from `genai.get_file` to `neo4j_vector_search`.

## 5. Alternatives Analysis: Is this the Best?

You asked if there are "better" alternatives. Here is the landscape:

### Option A: Unified GraphRAG (My Recommendation)
*   **Stack**: Neo4j (Vectors + Graph).
*   **Pros**: **Maximum Consistency**. The "Text Chunk" and the "Financial Fact" live in the same database row. ACID transactions ensure they never drift. True "Neuro-Symbolic" integration.
*   **Cons**: Slightly slower at massive scale (100M+ vectors) compared to dedicated vector engines.
*   **Verdict**: **Best for Reliability/Accuracy**.

### Option B: The "Split Stack" (Standard Industry)
*   **Stack**: Pinecone (Vectors) + Neo4j (Graph).
*   **Pros**: Pinecone is incredibly fast for pure similarity search.
*   **Cons**: **The Synchronization Nightmare**. You have to write data to two places. If one fails, your AI breaks. (e.g. Pinecone says "See Document A", but Neo4j says "Document A is deleted").
*   **Verdict**: Good for speed, **Dangerous for Reliability**.

### Option C: Agentic RAG
*   **Stack**: Agents that browse the web/tools.
*   **Pros**: Flexible.
*   **Cons**: Unpredictable and slow. "Thinking" takes time.
*   **Verdict**: Too disjointed for a trusted dashboard.

**Conclusion**: For a "Zero Compromise on Reliability" system, **Option A (Unified Neo4j)** is superior because it eliminates synchronization bugs.

## 6. The Lifecycle of a User Query (Step-by-Step)
Here is exactly what happens when you type *"What is the revenue growth?"*:

1.  **Input Guard**: The backend receives the text.
2.  **Embedding**: We send your text to Google's **`gemini-embedding-001`** model. It returns a high-dimensional vector.
3.  **Vector Search (The Net)**:
    *   We send those numbers to Neo4j.
    *   Neo4j finds the 20 text chunks that are mathematically closest to your question.
4.  **Graph Traversal (The Filter)**:
    *   For those 20 chunks, Neo4j checks their neighbors.
    *   *Example*: "Do these chunks belong to the 'Active' document?" "Are they linked to the 'Revenue' node?"
    *   We filter down to the 5 **Verified Chunks**.
5.  **Context Assembly**: We stick those 5 chunks into the prompt.
6.  **Generation**: Gemini 1.5 Pro reads the chunks and writes the answer.
7.  **Verification (The Truth Dot)**:
    *   We run the **Ghost Loop**.
    *   We check if the claimed sources are in the list of 5 chunks.
    *   We run the **Vector Judge** (Cosine Similarity) to confirm the answer matches the chunks.
8.  **Output**: You see the answer with a glowing verification dot.

## 7. The Mechanism: How Gemini "Uses" the Data (Context Injection)

You asked specifically: *How does the AI use this data to be reliable?*

Think of Gemini not as a specific **Encyclopedia** (Memory), but as a **Reasoning Engine** (Processor).
*   **Standard AI**: You ask a question. The AI closes its eyes and tries to remember what it read during training 2 years ago. (Result: Hallucination).
*   **True RAG**: You ask a question. We (the Backend) find the exact 3 pages from your PDF that contain the answer. We tape those pages to the user prompt.

**The Prompt We Send to Gemini:**
```text
SYSTEM: You are a helpful assistant.
CONTEXT DATA (Retrieved from Neo4j):
1. [Source: report.pdf] "Q3 Revenue was $1.2M."
2. [Source: email.txt] "We project 5% growth."

USER QUESTION: "What was the revenue?"
INSTRUCTION: Answer using ONLY the CONTEXT DATA above. Do not use outside knowledge.
```

**Why this makes Gemini 2.5 Flash reliable:**
Even though "Flash" is a smaller/faster model, it doesn't need to *know* your revenue. It just needs to be smart enough to **read the text we gave it** and summarize it.
*   We rely on **Neo4j** for *Memory* (Perfect Recall).
*   We rely on **Gemini** for *Synthesis* (Reading comprehension).

This separation of concerns is why RAG is the gold standard for accuracy.

### 7.1 The Decider: "Who chooses the pages?"

You asked: *What determines what information is required?*

The "Brain" that decides which pages to retrieve is NOT Gemini Flash. It is the **Embedding Model (`gemini-embedding-001`)**.

**The Process:**
1.  **Translation to Math**: The Embedding Model converts your question ("Revenue") into a **Vector** (a list of 3,072 numbers representing the *meaning* of business finance).
2.  **The Match**: It looks through the database for Document Chunks that act like magnets—chunks that have very similar numbers (similar meaning).
3.  **The Result**: If a page talks about "Q3 Earnings" (even if it doesn't say the word "Revenue"), the math will match because the *meaning* is close.

**So, the "Decider" is the Vector Math.** It finds the relevant needle in the haystack so Flash doesn't have to read the whole barn.
