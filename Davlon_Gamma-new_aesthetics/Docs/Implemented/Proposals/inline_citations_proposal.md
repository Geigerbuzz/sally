---
title: Granular Inline Citations ("The Truth Dot")
status: implemented
type: proposal
created: 2025-12-18
updated: 2025-12-18
tags: [rag, citations, chat, ui]
implemented_in: public/chat.js
related:
  - Docs/Implemented/Proposals/markdown_overhaul.md
---

# Proposal: Granular Inline Citations ("The Truth Dot")

## 1. The Problem
Current AI models often provide "Citations" as a list of links at the very bottom of the response. This is insufficient for high-trust workflows (like Real Estate or Legal) because the user doesn't know *which* specific sentence came from *which* document.

## 2. The Solution: Inline "Truth Dots"
We want a user experience where critical claims in the text are immediately followed by a small, interactive indicator (a "dot"). Clicking this dot allows the user to verify the source instantly.

### Desired UX
> "The property revenue last year was $1.2M 🟣, with a projected growth of 5% 🔵."

*   Clicking **🟣** opens "Financial_Report_2024.pdf" (Page 12).
*   Clicking **🔵** opens "Market_Forecast_Q3.csv".

## 3. Technical Strategy

Since reliable *native* inline citation support varies between models (and often doesn't give page numbers), we will enforce this behavior via **System Prompting**.

### A. Backend: The "Auditor" Prompt
We will modify the System Instruction sent to Gemini to enforce a strict output format.

**System Prompt Injection:**
```text
You are a rigorous data auditor. 
For every factual claim you make, you MUST append a citation tag in the exact format: [[Source: <filename>]]
If a claim comes from multiple sources, use multiple tags.
Example: "The roof was replaced in 2020 [[Source: Inspection.pdf]]."
Do not create a bibliography at the end; use inline tags only.
```

### B. Frontend: The Parser (`chat.js`)
We will write a JavaScript parser that runs on the AI's text response before it is added to the DOM.

**Regex Logic:**
1.  Detect pattern: `\[\[Source: (.*?)\]\]`
2.  Replace with HTML: `<span class="citation-dot" data-source="$1" title="Source: $1"></span>`

### C. Styling (`style.css`)
The dot should be subtle but distinct.
```css
.citation-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: var(--accent); /* Neon Green/Purple */
    border-radius: 50%;
    cursor: pointer;
    margin-left: 4px;
    box-shadow: 0 0 5px var(--accent);
    transition: transform 0.2s;
}
.citation-dot:hover {
    transform: scale(1.5);
}
```

## 4. Implementation Steps

1.  **Update `backend/rag.py`**: Inject the "Auditor" prompt into the `generate_content` call.
2.  **Update `public/chat.js`**: Implement the Regex parser and click handler.
3.  **Update `style.css`**: Add the "Truth Dot" styling.

## 5. Potential Pitfalls
*   **Hallucinated Filenames**: The AI might make up a filename if it's confused. We can mitigate this by passing the list of valid, available filenames in the prompt ("You typically have access to: [A.pdf, B.pdf]").
*   **Formatting Noise**: If the AI messes up the brackets `[[`, the regex might fail. We will use a robust instruction to minimize this.

## 6. Enhanced Safety: Ghost Reprompting & Verification

To prevent "Citation Hallucination" (citing valid-looking but non-existent files) and "Fake Support" (citing a real file that doesn't actually contain the info), we will implement a two-tier safety layer.

### Tier 1: "Ghost Reprompting" (Structure Guard)
**Goal:** Prevent non-existent filenames from appearing.
**Mechanism:**
1.  The Backend maintains a list of `valid_filenames` (e.g., `["Report.pdf", "Data.csv"]`).
2.  After the AI generates a response, the backend parses all `[[Source: X]]` tags.
3.  **Check:** Does `X` exist in `valid_filenames`?
4.  **If Invalid (Hallucination Detected):**
    *   **Discard** the entire response immediately.
    *   **Silent Retry**: Trigger `generate_content` again (up to 3 times) with a fresh seed/temperature.
    *   **Constraint**: We do *not* tell the model "You failed". We simply re-roll the dice. This prevents the model from "gaming" the correction.
    *   **Result**: The user never sees the broken response, only the final valid one (or a generic failure if 3 retries fail).

### Tier 2: Neuro-Symbolic Grounding (The Hard Truth)
**Goal:** Verify claims using deterministic logic and specialized discriminators, NOT just another "chatty" AI.

**Mechanism:**
Instead of asking a Generative AI "Do you think this is true?" (which can hallucinate), we use **Neuro-Symbolic Verification**:

1.  **Symbolic Check (The Graph):**
    *   For quantitative claims (e.g., "$1.2M Revenue"), we query the **Neo4j Knowledge Graph**.
    *   If the Graph has `(Company)-[HAS_REVENUE]->($1.2M)`, the claim is verified **deterministically**. 100% reliability.

2.  **Discriminative Check (The Judge):**
    *   For qualitative claims, we use a **Natural Language Inference (NLI)** model (like DeBERTa or a dedicated Cross-Encoder).
    *   This is a **Discriminative Model**, not a Generative one. It doesn't write text; it outputs a strictly mathematical score (0.0 to 1.0) on the question: *"Does Sentence A mathematically imply Sentence B?"*
    *   If Score < 0.9, we discard the response.

**Why this is better:**
*   **No Hallucination**: Discriminative models cannot "make up" facts; they can only judge the relationship between two inputs.
*   **Hard Math**: It relies on vector similarity and symbolic graph matches, not probabalistic word-guessing.
