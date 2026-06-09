# Technical Specification: Settings (settings.html)

## Overview
User configuration and account management.

## Functional Requirements

### 1. Authentication & Security
- **Providers**: Google, Microsoft, and Email/Password login (Auth0 / Firebase Auth).
- **Session Management**: Secure HTTP-only cookies and JWT rotation.
- **MFA**: Multi-Factor Authentication requirement for enterprise users.

### 2. User Preferences
- **Theme**: Sync `data-theme` preference to the user's DB profile so it persists across devices.
- **Dock Position**: Sync dock preference.

### 3. Enterprise Features
- **Team Management**: Invite users, assign roles (Admin, Analyst, Viewer).
- **Billing**: Stripe integration for subscription management.
- **Audit Logs**: View login history and data access logs.

## Technical Debt (Demo to Prod)
- All settings are currently stored in `localStorage`. This must migrate to a backend database (`users` table).
