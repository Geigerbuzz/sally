---
title: UI System Master
status: implemented
type: master
created: 2025-12-28
updated: 2025-12-28
tags: [frontend, ui, design-system, html, css]
consolidates:
  - Implemented/Proposals/markdown_overhaul.md
  - Implemented/Proposals/inline_citations_proposal.md
---

# UI System Master

The visual layer of Davlon. Apple-inspired design system with dark/light modes, animated effects, and custom components.

---

## Architecture

```
public/
├── index.html          # Dashboard (widget canvas)
├── chat.html           # AI chat interface
├── sessions.html       # Session history grid
├── sources.html        # Data & Sources tabs
├── inbox.html          # Notifications
├── settings.html       # User preferences
├── workspace.html      # Property listings (legacy)
│
├── style.css           # Core design system (37KB)
├── style_append.css    # Extension styles
├── popup.css           # Modal dialogs
│
├── chat.js             # Custom Markdown engine + citations
├── widgets.js          # Drag-drop dashboard
├── script.js           # Global utilities
├── sound_manager.js    # Synthesized SFX
└── neurons.js          # Particle animations
```

---

## Implemented Features

### 1. Design System
**Status**: ✅ Complete  
**Code**: `style.css`

| Token | Light | Dark |
|-------|-------|------|
| `--bg-body` | #f5f5f7 | #1c1c1e |
| `--bg-surface` | #ffffff | #2c2c2e |
| `--text-primary` | #1d1d1f | #f5f5f7 |
| `--accent` | #0a84ff | #0a84ff |
| `--dock-border` | rgba(0,0,0,0.1) | rgba(255,255,255,0.1) |

---

### 2. Dark/Light Mode
**Status**: ✅ Complete  
**Code**: `script.js`, `style.css`

- Toggle button in floating dock
- CSS custom properties switch
- Smooth transitions (0.3s)
- Persists to localStorage

---

### 3. Floating Dock
**Status**: ✅ Complete  
**Code**: `index.html`, `style.css`

- Glass-transparent navigation
- Icon-only buttons
- Fixed left position
- Hover labels

---

### 4. Custom Markdown Engine
**Status**: ✅ Complete  
**Code**: `chat.js`

Features:
- Headers (H1-H6)
- Bold, italic, code
- Lists (ordered, unordered)
- Code blocks with syntax highlighting
- Tables
- AI-friendly tight spacing

---

### 5. Inline Citations ("Truth Dots")
**Status**: ✅ Complete  
**Code**: `chat.js`

Format: `[[Source: filename (Page X)]]`

Renders as:
- Clickable dot icon
- Tooltip with source info
- Click to expand details

---

### 6. Session History Grid
**Status**: ✅ Complete  
**Code**: `sessions.html`

- 1x1 widget-like cards
- Shows topic, date, preview
- FAB to start new session

---

### 7. Living Particles
**Status**: ✅ Complete  
**Code**: `neurons.js`

- Canvas-based particle field
- Cursor interaction (dodge)
- Connects nearby particles

---

### 8. Sound Effects
**Status**: ✅ Complete  
**Code**: `sound_manager.js`

Synthesized audio for:
- Widget drop
- Success/error
- Navigation

---

## Pages

| Page | File | Purpose |
|------|------|---------|
| Dashboard | `index.html` | Widget canvas |
| Chat | `chat.html` | AI conversation |
| Sessions | `sessions.html` | History grid |
| Sources | `sources.html` | Upload + integrations |
| Inbox | `inbox.html` | Notifications |
| Settings | `settings.html` | Preferences |

---

## CSS Classes

### Layout
- `.container` — Max-width wrapper
- `.dock` — Floating navigation
- `.main-content` — Page body (with dock offset)

### Widgets
- `.widget` — Base widget styles
- `.w-1x1`, `.w-2x1`, `.w-1x2`, `.w-2x2` — Size classes

### Typography
- `.chat-md` — Custom Markdown scope
- `.widget-title` — Truncated single-line

---

## Related Documents

| Type | Document | Description |
|------|----------|-------------|
| 📋 Implemented | [Markdown Overhaul](../../Implemented/Proposals/markdown_overhaul.md) | Custom MD engine |
| 📋 Implemented | [Inline Citations](../../Implemented/Proposals/inline_citations_proposal.md) | Truth dots |
| 🔧 Master | [Widget System](./widget_system_master.md) | Dashboard widgets |
