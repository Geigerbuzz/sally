# Demo to Production: Required Changes

This document outlines the necessary steps to transition the current frontend demo into the full production application defined in the `Production/` plans.

## 1. Codebase Structure
- [ ] **Migrate to React/Next.js/Solid**: The current standard HTML/JS structure should be migrated to a Component-Based Framework (as hinted by the "Production" plans using detailed component logic). *Note: The user currently has standard HTML. If staying with Vanilla JS for production, strict module separation is needed.*
- [ ] **Environment Variables**: Replace hardcoded API keys (if any) and local paths with `.env` variables.

## 2. Backend Integration
- [ ] **Remove Simulations**:
    - Delete `simulateUpdates()` in `widgets.js`.
    - Delete `initRealTimeData()` mock data.
    - Replace with real WebSocket connections (`Production/05_Sessions.md`).
- [ ] **Connect Uploads**: Wire up the Drag & Drop zone in `sources.html` to the `/ingest` API endpoint (`Production/02_Static_Pipeline.md`).
- [ ] **Connect Live Feeds**: Wire up the "Connect" buttons in `sources_live.html` to the Backend Integrations service.

## 3. Security & Auth
- [ ] **Implement Auth Guard**: Wrap the entire application (except Login) in an Authentication check (Clerk/Auth0).
- [ ] **RBAC Restrictions**: Hide the "Settings" and "Legacy" tabs for non-admin users.

## 4. UI/UX Hardening
- [ ] **Error Handling**: Add Toast Notifications for failed uploads or lost connections (currently no feedback).
- [ ] **Performance**: Optimize the Neural Network background (`neurons.js`) to pause when the tab is not active to save battery.

## 5. Deployment
- [ ] **Dockerize**: Create a `Dockerfile` for the frontend service.
- [ ] **CI/CD**: Set up GitHub Actions to deploy to Railway.
