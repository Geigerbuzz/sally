---
title: Workspace Expansion & Automated Listings
status: draft
type: proposal
created: 2025-12-15
updated: 2025-12-28
tags: [workspace, listings, neo4j, team]
parent: null
children: []
related:
  - ./preemptive_ai_strategy.md
---

# Proposal: Workspace Expansion & Automated Listing Creation

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Navigation Bar](#21-top-navigation-bar) | ⬜ Pending | — | — |
| [Listings View](#3-the-listings-view) | ⬜ Pending | — | — |
| [Graph Schema](#41-graph-schema-proposal) | ⬜ Pending | — | — |
| [AI Context Awareness](#42-ai-context-awareness) | ⬜ Pending | — | — |
| [Agentic Data Gathering](#43-agentic-data-gathering-the-active-ai) | ⬜ Pending | — | — |

> **Depends on**: [Knowledge Graph Master](../../Implemented/Masters/knowledge_graph_master.md)  
> **Affects**: [Preemptive AI Strategy](./preemptive_ai_strategy.md)

---

## 1. Overview
This proposal details the expansion of the existing `workspace.html` into a multi-view interface comprising **Listings**, **Team**, and **Clients**. It integrates advanced **Neo4j Graph** capabilities to link people to properties and defines agentic AI behaviors for automated data gathering.

## 2. Workspace Navigation (UI/UX)
The navigation structure will mirror the existing "Data & Sources" pages.

### 2.1 Top Navigation Bar
Centered tab navigation under the main title:
- **Listings** (Default view)
- **Team**
- **Clients**

## 3. The "Listings" View
### 3.1 Listing Container UI
1.  **Status Indicator (Traffic Light)**:
    - 🔴 **Red**: Stagnating
    - 🟡 **Yellow**: Some Interest (**Default State**)
    - 🟢 **Green**: Sale in Progress

2.  **Key Visuals & Data**:
    - **Cover Picture** (Placeholder if missing)
    - **Address**, **Bed/Bath Count**, **Floor Space**.
    - **Bonuses Section**: (Pool, Gym, etc.)

3.  **Auto-Creation Logic**:
    - Uploading documents with contact/property data auto-generates a Listing Container.
    - Default state is **Yellow**.

## 4. Neo4j Graph Integration (The "Brain")
To enable high-level AI reasoning, we will model relationships in the Neo4j database.

### 4.1 Graph Schema Proposal
We will introduce specific node relationships:
- `(:Person)-[:MANAGES]->(:Listing)`: Links Team Members (e.g., Mark, Alice) to a specific Property.
- `(:Person)-[:INTERESTED_IN]->(:Listing)`: Links Clients to Properties.
- `(:Listing)-[:HAS_DOCUMENT]->(:Document)`: Links uploaded files to the listing.

### 4.2 AI Context Awareness
When the user queries the chatbot (e.g., "What's the status of the Downtown Loft?"):
1.  **Graph Lookup**: The system queries Neo4j for the `Listing` node and retrieves all connected `Person` nodes with the `MANAGES` relationship.
2.  **Response Generation**: "The Downtown Loft is currently Yellow. Mark and Alice are managing this listing. [Graph Context] indicates Mark last updated the price on Tuesday."

### 4.3 Agentic Data Gathering (The "Active" AI)
If the AI detects missing critical information (e.g., missing "Square Footage" for a listing):

**Workflow:**
1.  **Identify Gap**: AI sees `sq_ft` is null.
2.  **Identify Owner**: AI queries `MATCH (p:Person)-[:MANAGES]->(l:Listing) ...` to find Mark and Alice.
3.  **Action - Data Request**:
    - The AI generates a structured "Data Request" message.
    - This is sent to Mark and Alice's **Inbox** (in the `inbox.html` functionality).
    - *Subject*: "Action Required: Missing details for Downtown Loft".
4.  **Ingestion**:
    - Mark replies to the message with "It is 1200 sq ft".
    - The System parses this reply, updates the `Listing` node properties in Neo4j, and resolves the request.

## 5. Technical Implementation Options

### Option A: Graph-First (Recommended)
**Architecture**: The backend relies heavily on Neo4j for state.
- **Listing Creation**: Creates a Node in Neo4j immediately.
- **Linking**: When assigning a team member in the UI, we write a `MERGE (p)-[:MANAGES]->(l)` query.
- **Chatbot**: The RAG pipeline is augmented with a "Graph Tool" that executes Cypher queries before searching vector embeddings.
- **Inbox**: Stored as `(:Message)` nodes in the graph, linked to users.

### Option B: Hybrid SQL + Vector
**Architecture**: Use a relational DB for the UI state (tables) and only use Vector DB for RAG.
- **Pros**: Simpler for standard CRUD.
- **Cons**: Complex questions like "Who manages the properties that satisfy client X's requirements?" become very hard to answer efficiently compared to a Graph traversal.
- **Verdict**: Given the requirement for "Understanding relationships," **Option A (Neo4j)** is superior.

## 6. Next Steps
1.  **Schema Definition**:Define the exact Node labels and edge property names.
2.  **UI Mockup**: Update `workspace.html` to show "Assigned Agents" on the listing card.
3.  **Inbox Logic**: Prototype the "AI Auto-Message" feature in the backend.
