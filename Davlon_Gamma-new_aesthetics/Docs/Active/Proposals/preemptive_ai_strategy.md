---
title: Preemptive AI Strategy
status: draft
type: proposal
created: 2025-12-15
updated: 2025-12-28
tags: [ai, proactive, strategy, automation]
parent: null
children: []
related:
  - ./shock_ideas.md
  - ./b2b_widget_expansion.md
---

# Strategy: Preemptive AI & The "Proactive" Dashboard

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Briefing Engine](#1-the-briefing-engine-expanded-executive-chat) | ⬜ Pending | — | — |
| [Sentinel Mode](#2-sentinel-mode-anomaly-detection) | ⬜ Pending | — | — |
| [Prescient Forecasting](#3-prescient-work-forecasting) | ⬜ Pending | — | — |
| [AI Suggestions Tray](#4-user-experience-the-review-tray) | ⬜ Pending | — | — |

> **Depends on**: [Widget System Master](../../Implemented/Masters/widget_system_master.md), [RAG System Master](../../Implemented/Masters/rag_system_master.md)  
> **Affects**: [Shock Ideas](./shock_ideas.md), [B2B Expansion](./b2b_widget_expansion.md)

---

> "The system generally shouldn't wait for user input. It should have work ready."

## Core Philosophy: The "Draft" Protocol
The AI operates on a **"Propose, Don't Dispose"** model. It can perform analysis, draft emails, simulate scenarios, and prepare reports, but it **never executes the final mile** (sending, purchasing, deleting) without human confirmation. The AI's goal is to reduce the friction of action to a single "Approve" click.

---

## 1. The Briefing Engine (Expanded "Executive Chat")
Instead of a static "play" button, the Briefing Engine is a configurable intelligence layer.

### Features
- **Frequency Controls**:
    - **Morning Brief (8:00 AM)**: "Catch me up." High-level KPIs, overnight alerts, today's calendar context.
    - **Weekly Deep Dive (Friday)**: "How did we do?" Trend analysis, performance vs. goals.
    - **Event-Triggered**: "The Board Meeting Brief" (Generated 1 hour before a calendar event labeled 'Board Meeting').
- **Format Options**:
    - **Audio Podcast**: Natural voice synthesis for commuting.
    - **Smart Digest (Text)**: Bullet points with links to specific widgets.

---

## 2. Sentinel Mode (Anomaly Detection)
The system constantly monitors all connected Live Data streams for statistical outliers.

### Use Cases
- **The "Good" Spike**: "Sales in the APAC region jumped 400% in the last hour."
    - **AI Insight**: "This correlates with the viral mention by Influencer X on Twitter."
    - **AI Recommended Action**: "Drafted a 'Thank you' tweet to Influencer X" (User clicks *Post*).
- **The "Bad" Drift**: "Server latency has been creeping up 1% every hour for 12 hours."
    - **AI Insight**: "This looks like a potential memory leak in the authentication service."
    - **AI Recommended Action**: "Prepared a JIRA ticket for the DevOps team." (User clicks *Create*).

---

## 3. Prescient Work (Forecasting)
The AI looks forward, not just backward.

### "Ghost" Scenarios
- **Inventory Forecast**: "Based on current velocity, you will run out of Stock X in 4 days."
    - **Pre-Work**: The AI places a *draft* Purchase Order for Stock X in the ERP system. The user just needs to review and hit "Send".
- **Staffing Alert**: "Ticket volume is predicted to spike on Black Friday."
    - **Pre-Work**: The AI suggests a modified shift schedule adding 2 support agents.

---

## 4. User Experience: The "Review" Tray
To manage this "Preemptivity" without being annoying, these suggestions live in a dedicated **"AI Suggestions" Tray** (perhaps a subtle sidebar or notification center), rather than popping up modals.

- **Status**: 🟢 Ready for Review
- **Item**: "Weekly Report Draft"
- **Action**: [Edit] [Approve] [Discard]
