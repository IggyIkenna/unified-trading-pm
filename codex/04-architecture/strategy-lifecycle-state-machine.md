---
scope: [engineer, admin]
title: Strategy Lifecycle State Machine
type: architecture
status: stub
created: 2026-05-21
---

# Strategy Lifecycle State Machine

> **STUB** — Reference: `codex/04-architecture/promote-workflow-architecture.md`.

States: `draft → paper_1d → live_early → live_full`. Transitions validated by the promote endpoint. Rollback: any state
can move back to `paper_1d` via `/api/promote/{id}/rollback`. Full spec:
`codex/04-architecture/promote-workflow-architecture.md`.
