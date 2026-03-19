---
name: debug-ui
description: >-
  Debug frontend UI errors using the browser MCP. Use when the user invokes /debugui, asks to debug a UI, check console
  errors, or fix something that broke in a running dev server.
---

# Debug UI

When the user reports a UI issue or invokes /debugui:

## 1. Get context

- **URL**: User provides it (e.g. `http://localhost:5183`) or infer from common ports (deployment-ui: 5183, strategy-ui:
  5173, etc.)
- **Workflow** (optional): User may describe what they clicked, e.g. "selected instruments-service, opened Deploy tab"

## 2. Use browser MCP

1. **Navigate**: `browser_navigate` to the app URL
2. **Read console**: `browser_console_messages` to capture errors
3. **Reproduce** (if needed): Use `browser_click`, `browser_snapshot` to replicate the user's steps
4. **Re-check console** after reproducing

## 3. Fix the issue

- Parse error message and stack trace from console
- Search the codebase for the failing component/line
- Add defensive checks (e.g. `?? []` for undefined arrays), fix null access, or address the root cause

## 4. Verify

- Refresh or re-navigate
- Confirm no new errors in `browser_console_messages`

## Minimal user prompt

User can say: "Something broke" or "deployment-ui at localhost:5183 - I clicked X and it crashed." One sentence is
enough.
