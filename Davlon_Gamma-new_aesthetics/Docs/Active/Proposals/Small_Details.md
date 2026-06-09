---
title: Small Details & Polish Checklist
status: active
type: notes
created: 2025-12-15
updated: 2025-12-28
tags: [ui, ux, polish, animations]
parent: null
children: []
related:
  - ./shock_ideas.md
---

# Small Details & Polish Checklist

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| Widget Auto-Arrange Animation | ⬜ Pending | — | — |
| Tab Transitions | ⬜ Pending | — | — |
| Hover States | ⬜ Pending | — | — |
| Loading Skeletons | ⬜ Pending | — | — |
| Sound Design | ⬜ Pending | — | — |
| Mobile Responsiveness | ⬜ Pending | — | — |

> **Affects**: [UI System Master](../../Implemented/Masters/ui_system_master.md)

---

This document tracks minor UI/UX details and interactions that need to be added to the production version to ensure a premium feel.

- [ ] **Widget Auto-Arrange Animation**: When the widgets are auto-arranged (either by button click or on load), they should animate to their new positions smoothly instead of snapping instantly. This requires calculating element transforms.
- [ ] **Tab Transitions**: The switching between Static/Live/Legacy views in Sources currently uses a simple `display: none/block`. This should be a smooth fade or slide transition.
- [ ] **Hover States**: Add more subtle hover states to table rows and list items in the Sources list.
- [ ] **Loading Skeletons**: Use skeleton screens instead of spinners when loading the Live Data feed.
- [ ] **Sound Design**: Consider adding very subtle sound effects for "Connect" or "Upload" actions (optional, user preference).
- [ ] **Mobile Responsiveness**: Verify the Floating Dock behavior on mobile screens (currently it might block content).
