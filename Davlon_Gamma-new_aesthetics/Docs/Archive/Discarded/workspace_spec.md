# Technical Specification: Workspace (workspace.html)

## Overview
The Workspace is the document management and collaboration center.

## Functional Requirements

### 1. Content Generation Engine
The Workspace is where users leverage the AI to create complex Real Estate assets. It is NOT a document editor (like Word); it is a **Generator**.
- **Supported Media Types**:
    - **Market Reports (PDF)**: Automated CMA (Comparative Market Analysis) generation for specific neighborhoods.
    - **Contracts (PDF)**: Filling out state-specific listing agreements or purchase offers.
    - **CSVs**: Exporting lead lists or financial projections.
    - **Email Templates**: Personalizing drip campaigns for different client segments.

### 2. Asset Management
- **Cloud Storage**: Secure hosting for generated assets.
- **Workflow Status**: `Draft` -> `Review` -> `Approved` -> `Sent`.
- **RBAC**: Who can *generate* vs who can *approve* active contracts.

## Technical Debt (Demo to Prod)
- Replace static "Recent Files" list with a dynamic query `GET /api/files/recent`.
- Implement actual file upload/download handlers with virus scanning.
