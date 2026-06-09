# Technical Specification: Sessions (sessions.html)

## Overview
Sessions is a real-time collaboration space for team meetings and presence.

## Functional Requirements

### 1. Collaborative AI Rooms (The "Session")
A "Session" is a named, persistent chat room where a human team collaborates with an AI Agent.
- **Multi-Player UX**:
    - **Host**: The user who started the session (e.g., "Analyzing Q3 Revenue").
    - **Participants**: Team members who join to observe or contribute.
    - **The AI**: A participant in the chat that answers questions, generates widgets, or performs analysis.
- **Context Awareness**: The AI in a session has access to all documents/widgets shared in that specific session.

### 2. Real-Time Mechanics
- **Streaming Response**: All participants see the AI's response typing out in real-time (shared WebSocket stream).
- **Presence**: "Shay is typing..." indicators alongside "AI is processing..." stats.

## Technical Debt (Demo to Prod)
- The header bubbles are currently static HTML. These need to be hydrated by a global Context/Store state derived from the WebSocket connection.
- "Sessions" list needs to actually show active WebRTC rooms.
