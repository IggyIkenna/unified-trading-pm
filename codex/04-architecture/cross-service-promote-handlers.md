---
scope: [engineer, admin]
title: Cross-Service Promote Handlers
type: architecture
status: stub
created: 2026-05-21
---

# Cross-Service Promote Handlers

> **STUB** — Reference: `codex/04-architecture/promote-workflow-architecture.md`.

Handlers that execute when a strategy is promoted from paper → live. Each service registers a `PromoteHandler` that
validates its preconditions (manifest freshness, schema version, credential ping). Full spec in
`codex/04-architecture/promote-workflow-architecture.md`.
