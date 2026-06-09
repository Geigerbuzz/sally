---
title: Custom Markdown Engine for Chat
status: implemented
type: proposal
created: 2025-12-18
updated: 2025-12-18
tags: [chat, ui, markdown, rendering]
implemented_in: public/chat.js
related:
  - Docs/Implemented/Proposals/inline_citations_proposal.md
---

# Proposal: Custom Markdown Engine for Chat

## Executive Summary
The current approach of relying on third-party libraries (`marked.js`) combined with unstable regex "preprocessing" has failed to produce consistent, high-quality rendering. The AI's output is variable (sometimes "tight" spacing, sometimes "bold" headers), and standard libraries are too strict or unpredictable.

This proposal outlines a plan to **build a custom, lightweight Markdown formatter from scratch**. This ensures we have 100% control over how every character is rendered, allowing us to handle "AI-flavored" Markdown (like missing newlines or bolded headers) gracefully without fighting a black-box library.

## Core Philosophy: "Forgiving & Robust"
Unlike standard parsers that require strict CommonMark compliance, our engine will be **forgiving**. It will assume the AI *meant* to make a list, even if it forgot a newline. It will assume `**Title**` is a header if it sits on its own line.

## Architecture

### 1. The Pipeline
We will implement a 3-stage pipeline in `chat.js`:
1.  **Tokenizer**: Breaks the raw text stream into logical "blocks" (Paragraphs, Code Fences, Headers, Lists).
2.  **Parser**: Converts these blocks into an Intermediate Representation (IR), cleaning up messy syntax (e.g., stripping `**` from headers).
3.  **Renderer**: Generates safe, clean HTML strings with explicit classes for styling.

### 2. Supported Syntax (The "Chat Standard")
We will support a strict subset of Markdown optimized for chat, ignoring complex features that break layouts (like tables or footnotes) unless requested.

| Feature | Robustness Rule |
| :--- | :--- |
| **Headers** | Supports `#`, `##` and bolded lines `**Title**`. Force-styles them as H1-H3. |
| **Lists** | Supports `*`, `-`, `1.`. **Critically**: Does NOT require preceding newlines. |
| **Code** | Supports backticks `` ` `` and fences ` ``` `. explicitly detects languages. |
| **Emphasis** | Standard `**bold**` and `*italic*`. |
| **Newlines** | All single newlines are treated as `<br>` (Chat standard), unlike strict Markdown which ignores them. |

### 3. Implementation Phases

#### Phase 1: The Tokenizer (No more Regex Soup)
Instead of running 50 regex replacements on the whole string (which corrupts data), we scan the text **line-by-line**.
- Iterate through lines.
- Maintain a "state" (e.g., `in_list`, `in_code_block`).
- If we see a line starting with `* ` and we are not in a list, *open* a `<ul>`.
- If the next line doesn't start with `* `, *close* the `</ul>`.
- This state-machine approach guarantees lists always open/close correctly.

#### Phase 2: The Style System
We will completely decouple the Markdown styles from the global CSS.
- Create a dedicated CSS scope: `.chat-md`.
- All generated HTML will be wrapped in this class (e.g., `<div class="chat-md">...</div>`).
- Styles will be explicit: `.chat-md ul { list-style: disc; margin-left: 1em; }`.

#### Phase 3: The "Sanitizer"
Since we are manually building HTML, we must handle XSS.
- Simple rule: We never execute scripts.
- We will escape `<` and `>` characters in the text *before* processing syntax.

## Why This Wins
1.  **Zero Dependencies**: No CDN failures, no version conflicts.
2.  **Pixel-Perfect Control**: We decide exactly how much spacing a list has.
3.  **AI Compatibility**: We treat "lazy" formatting as valid, fixing the core issue effectively.

## Next Steps
1.  Approve this architectural direction.
2.  I will write the `MarkdownEngine` class in `chat.js`.
3.  We will flip the switch and disable the old library.
