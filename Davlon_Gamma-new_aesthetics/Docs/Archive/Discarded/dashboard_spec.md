# Technical Specification: Dashboard (index.html)

## Overview
The Dashboard is the central hub for B2B Real Estate analytics. It currently features a drag-and-drop grid with mock widgets.

## Functional Requirements

### 1. Widget Grid System
- **State Persistence**: Widget positions, sizes, and configurations must be saved to the user's profile in the database (Layout API).
- ** responsive Layout**: Grid must reliably adapt to different screen sizes while maintaining "locked" relative positions.
- **Conflict Resolution**: Logic to handle two users editing the same dashboard layout simultaneously (Last-write-wins or locking).

### 2. B2B Real Estate Widget Library
The platform should support a comprehensive library of widgets that agencies can pin to their dashboard. These go beyond the demo set to cover all aspects of brokerage operations.

#### A. Financial Performance
- **GCI (Gross Commission Income) Tracker**: `GET /api/financials/gci`. Tracks revenue against monthly/quarterly targets.
- **Deal Flow Forecast**: `GET /api/financials/forecast`. Predictive revenue based on pipeline probability (e.g., 90% closing * $10k comm).
- **Expense Ratio**: `GET /api/financials/expenses`. Real-time visualization of marketing spend vs. closed revenue.

#### B. Agent & Team Productivity
- **Agent Leaderboard**: `GET /api/team/leaderboard`. Ranks agents by volume, units, or GCI. Essential for motivating sales teams.
- **Activity Log**: `GET /api/team/activity`. Tracks calls made, appointments set, and open houses hosted.
- **Task Compliance**: `GET /api/compliance/alert`. flagged transactions missing critical documents before closing.

#### C. Marketing & Leads
- **Lead Source ROI**: `GET /api/marketing/sources`. Bar chart comparing different channels (Zillow, Referral, PPC) by Cost Per Lead (CPL) and Conversion Rate.
- **Client Sentiment**: `GET /api/crm/sentiment`. AI analysis of recent email/text communications (Positive/Neutral/Negative).
- **Website Traffic Details**: `GET /api/marketing/traffic`. Vistors vs. Inquiries conversion funnel.

#### D. Inventory & Market
- **Listing Expirations**: `GET /api/listings/expiring`. Alert list of listings expiring in the next 30 days.
- **Neighborhood Trends**: `GET /api/market/trends`. Price per SqFt trends in specific farm areas over 6/12/24 months.
- **Off-Market "Pocket" Listings**: `GET /api/listings/private`. internal-only display of pre-market opportunities.

### 3. AI Widget Creator (Chatbar)
- **Natural Language Processing**: Connect the input to an LLM Service (e.g., OpenAI API).
- **Code Generation**: The LLM must generate standardized Davlon Widget JSON/HTML.
- **Sandbox**: Generated widgets must be rendered in a sandboxed iframe or shadow DOM to prevent XSS.

## Technical Debt (Demo to Prod)
- Remove `Math.random()` simulation logic.
- Replace HTML drag-and-drop with a robust library (e.g., `dnd-kit` or `react-grid-layout` if migrating to React) for mobile touch support and accessibility.
