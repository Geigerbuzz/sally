# Technical Specification: Inbox (inbox.html)

## Overview
A centralized messaging and notification center.

## Functional Requirements

### 1. External Communications (Unified Box)
- **Aggregated Stream**: View emails (Gmail/Outlook) and SMS (Twilio/RingCentral) in a single timeline.
- **AI Triage**: Incoming messages are auto-tagged (`Lead`, `Urgent`, `Spam`) and prioritized.

### 2. The "Preemptive" Review Tray
This is the home for the **"Propose, Don't Dispose"** engine (See `Proposals/preemptive_ai_strategy.md`).
- **Drafts requiring Approval**:
    - "Drafted reply to Lead X"
    - "Detected anomaly in server latency - Drafted Jira Ticket"
    - "Market Report for Neighborhood Y ready for review"
- **Action UI**: Simple [Approve] / [Edit] / [Reject] buttons for each item.
- **System Alerts**: Critical system failures or downtime notifications.

## Technical Debt (Demo to Prod)
- The "No new messages" state is hardcoded. Needs a polling or WebSocket event listener for new message counts.
