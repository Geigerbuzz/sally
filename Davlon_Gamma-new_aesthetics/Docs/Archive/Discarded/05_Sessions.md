# Production Step 5: Collaborative Sessions

**Goal**: A "Multiplayer" Chat experience where AI is a participant.

## 1. WebSocket Server
1.  **Technology**: `FastAPI WebSockets` + `Redis Pub/Sub`.
2.  **Why Redis?**: To scale across multiple server instances (Railway might spin up 2+ containers).

## 2. The Logic Flow
1.  **User Joins**:
    - Connect WS: `ws://api.davlon.com/sessions/{session_id}`
    - Server subscribes this connection to Redis channel `session_{session_id}`.
2.  **User Types**:
    - Sends message JSON.
    - Server broadcasts to all humans in room.
    - Server *also* sends to **AI Worker Queue**.
3.  **AI Responds**:
    - Worker gets history.
    - Worker calls Gemini/Neo4j.
    - Worker streams tokens back to Redis channel.
    - Server forwards tokens to human WebSockets.

## 3. Context Management
The AI needs to know *what* is in the session.
1.  **Session Graph**:
    `(Session)-[:HAS_CONTEXT]->(Document)`
    `(Session)-[:HAS_CONTEXT]->(Widget)`
2.  **Prompt Assembly**:
    When the AI runs, it queries this graph: "What files are pinned to this session?"
    Then it includes those files in the generation context.
