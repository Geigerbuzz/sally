# Technical Specification: Backend Infrastructure

## Overview
To support the Davlon B2B product, a robust backend architecture is required beyond the static HTML/JS frontend.

## Core Services

### 1. API Gateway
- **Technology**: Node.js (Express/NestJS) or Go.
- **Role**: Routes requests, handles Rate Limiting, and validates Authentication tokens.

### 2. Databases
- **Relational (PostgreSQL)**: Users, Organizations, Transactions, Listings.
- **Vector (Pinecone/Milvus)**: Embeddings for the Data Pipeline (RAG).
- **Graph (Neo4j)**: Relationship mapping for complex B2B entity resolution (Who owns what LLC).
- **Cache (Redis)**: Caching API responses and storing WebSocket session state.

### 3. Real-Time Engine
- **WebSocket Server**: Dedicated cluster for handling real-time updates (Presence, Notifications, Widget live-streams).
- **Scaling**: Pub/Sub (Redis) to sync state across multiple server instances.

### 4. AI Services
- **Orchestrator**: Service to manage LLM context windows and prompts.
- **Auditor**: Dedicated agentic service for verifying citations (See `data_pipeline_proposal.md`).

## Deployment
- **Containerization**: Docker for all services.
- **Orchestration**: Kubernetes (EKS/GKE) for scaling.
- **CI/CD**: GitHub Actions pipeline for automated testing and deployment.
