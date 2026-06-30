---
doc_type: codex-ssot
title: Strategy Lifecycle State Machine
summary:
status: stub
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-21
authoritative_for:
referenced_by:
owner:
last_reviewed:
code_refs:
type: architecture
---

# Strategy Lifecycle State Machine

> **STUB** — Reference: `codex/04-architecture/promote-workflow-architecture.md`.

States: `draft → paper_1d → live_early → live_full`. Transitions validated by the promote endpoint. Rollback: any state
can move back to `paper_1d` via `/api/promote/{id}/rollback`. Full spec:
`codex/04-architecture/promote-workflow-architecture.md`.
