# The "Nuclear Option" for Data Extraction
**Goal**: Maximum Reliability. Cost and Speed are irrelevant.

Standard OCR (Tesseract) makes mistakes (e.g., reading `$800,000` as `$800.000` or `$B00,000`).
To achieve 99.999% accuracy, we move beyond simple "extraction" to **Consensus Verification**.

## 1. The Strategy: "Adversarial Consensus"
We do not trust any single AI model. We run **three** state-of-the-art models in parallel on the same document and only accept facts where they unanimous agree.

### The Stack
1.  **Model A**: **Azure AI Document Intelligence** (formerly Form Recognizer). Best-in-class for strict table structures and financial data.
2.  **Model B**: **Google Cloud Vision / Gemini 1.5 Pro**. Excellent at "reasoning" through complex layouts.
3.  **Model C**: **GPT-4o**. Used as the "Judge" to compare A and B.

### The Pipeline
1.  **Ingest**: `Quarterly_Report.pdf`
2.  **Extraction A**: Azure AI extracts table rows -> JSON A.
3.  **Extraction B**: Gemini 1.5 Pro extracts table rows -> JSON B.
4.  **Comparison**:
    - The code compares JSON A and JSON B bit-for-byte.
    - **Match**: Data is accepted as **Golden Truth**.
    - **Conflict**: (e.g., Azure says `$500`, Gemini says `$600`). **STOP**.
5.  **The Human Circuit Breaker (HITL)**:
    - Any conflict triggers a "Data Verification Task" in the **Inbox**.
    - A Human (or a specialized human service like Scale AI) manually reviews the crop of the image and selects the correct value.

## 2. Why this is "Ultimate Reliability"
- **Redundancy**: Probability of Azure AND Google making the *exact same* error on the *exact same* pixel is infinitesimally small.
- **Human Fallback**: We never guess. If models disagree, we pause and ask a human.

## 3. Technology Choice
- **Unstructured.io**: Great base, but for "Nuclear" reliability, we wrap it in the **LangChain Extraction consensus** pattern described above.
