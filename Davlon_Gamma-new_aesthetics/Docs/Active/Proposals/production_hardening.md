---
title: Production Hardening
status: draft
type: proposal
created: 2025-12-15
updated: 2025-12-28
tags: [production, security, deployment, devops]
parent: null
children: []
related:
  - ./backend_reminders.md
---

# Production Hardening Proposal

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [API Key Security](#1-security--secrets-management) | ✅ Complete | 2025-12-15 | Railway vars |
| [Input Sanitization](#1-security--secrets-management) | ✅ Complete | 2025-12-15 | `models.py` |
| [Rate Limiting](#1-security--secrets-management) | ⬜ Pending | — | — |
| [Circuit Breakers](#2-reliability--resilience) | ⬜ Pending | — | — |
| [Dockerization](#3-deployment-docker--cicd) | ⬜ Pending | — | — |
| [CI/CD Pipeline](#3-deployment-docker--cicd) | ⬜ Pending | — | — |
| [Sentry Integration](#4-monitoring--observability) | ⬜ Pending | — | — |

> **Depends on**: [Backend Reminders](./backend_reminders.md)  
> **Affects**: All production deployments

---

## 1. Security & Secrets Management
- [ ] **API Keys**: Ensure `GOOGLE_API_KEY`, `NEO4J_PASSWORD` are never committed. Use Railway variables.
- [ ] **Input Sanitization**: We currently use Pydantic (`models.py`), which is good.
    - *Action*: Audit all file upload endpoints for mime-type validation (prevent executable uploads).
- [ ] **Rate Limiting**: Add `slowapi` or Redis-based rate limiting to `main.py` to prevent abuse.

## 2. Reliability & Resilience
- [ ] **Circuit Breakers**: Implement retry logic for Gemini API calls using `tenacity`.
    - *Reason*: LLM APIs can have transient failures.
- [ ] **Fallback Models**: If `gemini-3-flash` is overloaded, fallback to `gemini-2.0-flash`.
- [ ] **Queue Separation**: Ensure heavy ingestion jobs (PDF parsing) run on a separate worker (Redis/Celery or Railway dependent service) so they don't block the HTTP API.

## 3. Deployment (Docker & CI/CD)
- [ ] **Dockerization**: Create a `Dockerfile` for the backend.
    - Allows consistent running on Railway, AWS, or local.
- [ ] **CI/CD Pipeline**: Add `.github/workflows/main.yml`.
    - Run `pytest` on every push.
    - Run `black` / `ruff` formatting checks.

## 4. Monitoring & Observability
- [ ] **Logging**: Integrate **Sentry** for error tracking.
- [ ] **Structured Logs**: Change `print()` statements to strict JSON logging for easy parsing in Datadog/Railway logs.

## 5. Immediate Action: Model Upgrade
- [ ] Upgrade `backend/rag.py` to use `gemini-3-flash`.
