# Discarded / Deferred Features

This document tracks features that were considered but explicitly discarded or deferred indefinitely.

---

## From: Advanced RAG Enhancements Proposal

### 1.2 Multi-Hop Reasoning

**Original Proposal**: Chain multiple retrieval steps for complex questions by decomposing queries into sub-questions.

**Example**:
> "Compare the revenue growth of our top 3 clients"
> - Sub-Q1: "Who are our top 3 clients?" → [Client A, B, C]
> - Sub-Q2: "What is Client A's revenue growth?" → 15%
> - etc.

**Why Discarded**:
- High complexity (1 week+ effort)
- Current single-pass RAG with hybrid search handles most use cases adequately
- Sub-question decomposition adds latency and API costs
- Can be revisited if users specifically request comparative/analytical queries

**Date Discarded**: December 27, 2024

---
