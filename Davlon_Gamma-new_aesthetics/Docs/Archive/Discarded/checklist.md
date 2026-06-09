# Production Roadmap Checklist

This is the definitive "Huge Checklist" for moving Davlon Beta to production readiness, focusing on the Hybrid Intelligence pipeline and B2B features.

## 1. Backend Core & Infrastructure
- [x] **FastAPI Setup**
    - [x] Create app scaffolding (`main.py`, `config.py`).
    - [x] Implement global Exception Handlers (return JSON errors).
    - [x] Add Logging middleware (requests/responses).
- [x] **WebSockets (Real-Time Layer)**
    - [x] Create `ConnectionManager` class in `backend/websockets.py`.
    - [x] Implement `/ws/{client_id}` endpoint.
    - [x] Handle connection/disconnection lifecycle.
    - [x] implement `broadcast(message)` for live widget updates.
- [x] **Database (Neo4j)**
    - [x] Basic Driver setup (`database.py`).
    - [x] Define **Constraints** (Unique IDs for Users, Widgets, Sources).
    - [x] Create bootstrap script (`backend/bootstrap_db.py`) to init indices.

## 2. Data Pipeline: Unstructured (The "Document Brain")
*Powered by Google Gemini File Search API*
- [x] **Ingestion Endpoint (`POST /api/ingest/doc`)**
    - [x] Accept File Upload (`UploadFile`).
    - [x] Upload to Google Cloud (Gemini File API).
    - [x] Store metadata (File ID, Name, Google URI) in Neo4j Node `(:Document)`.
- [x] **RAG / Query Endpoint**
    - [x] Implement `GeminiClient.query_with_files(prompt, file_ids)`.
    - [x] Parse response for **Citations** (Extracted from `citation_metadata`).
    - [x] Return structured response `{ answer: str, citations: list }`.

## 3. Data Pipeline: Structured (The "Graph Brain")
*Powered by Neo4j*
- [x] **Ingestion Endpoint (`POST /api/ingest/data`)**
    - [x] Accept CSV/JSON Upload.
    - [x] **Dynamic Parser**: Map CSV headers to Graph Properties.
    - [x] **Graph Write**: Create Nodes/Relationships from rows.
- [x] **Live Feed Connectors**
    - [x] **MLS Stub**: Create a background task that "polls" a mock MLS API.
    - [x] **CRM Stub**: Create a background task for mock Salesforce updates.
    - [x] Push updates to Graph -> Trigger WebSocket broadcast.

## 4. Frontend Wiring (The "Nerve Endings")
- [x] **WebSocket Client (`public/socket.js`)**
    - [x] Connect to `ws://localhost:8000/ws/web`.
    - [x] Handle `widget_update` events -> Update DOM numbers/charts.
    - [x] Handle `reconnect` logic (robustness).
- [x] **Source Page wiring**
    - [x] **Static Tab**: `dropzone` should POST to `/api/ingest/doc` (or data for CSV).
    - [ ] **Live Tab**: "Connect" button should POST to `/api/integrations/toggle`.
    - [ ] **Legacy Tab**: Fetch archived file list from `/api/documents?status=archived`.

## 5. B2B Real Estate Features
- [ ] **Widget Data Providers**
    - [ ] Implement `get_revenue_metrics()` (Neo4j Query).
    - [ ] Implement `get_active_listings()` (Neo4j Query).
    - [ ] Implement `get_agent_performance()` (Neo4j Query).
- [ ] **Widget Generator Scaffolding**
    - [ ] Secure the "Generate Widget" prompt.
    - [ ] Feed Graph Schema to Gemini ("Here are the node types we have...").
    - [ ] Parse Gemini response into correct HTML/CSS grid layout.

## 6. Pre-Deployment Polish
- [x] **Frontend Cleanup**
    - [x] Remove fake "Team Online" avatars (Single user mode).
    - [x] Remove mock entries in `sources.html` (Live/Static/Legacy).
    - [x] Reset Dashboard widgets to "Zero State" (No hardcoded numbers).
- [x] **Deployment Prep**
    - [x] Create `Procfile` for Railway (`web: uvicorn...`).
    - [x] Verify `requirements.txt`.
    - [ ] **Manual Deployment** (Follow `railway_deployment_checklist.md`).

## 7. Production Hardening
- [ ] **Security (Basic)**
    - [ ] Add API Key validation for Admin routes.
    - [ ] Sanitize filenames on upload.
- [ ] **Deployment**
    - [ ] Create `Dockerfile`.
    - [ ] Create `docker-compose.yml` (App + Neo4j Community for local testing).
    - [ ] Verify functionality in Docker container.
