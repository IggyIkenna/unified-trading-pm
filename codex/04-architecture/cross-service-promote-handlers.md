---
doc_type: codex-ssot
title: Cross-Service Promote Handlers
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

# Cross-Service Promote Handlers

> **STUB** — Reference: `codex/04-architecture/promote-workflow-architecture.md`.

Handlers that execute when a strategy is promoted from paper → live. Each service registers a `PromoteHandler` that
validates its preconditions (manifest freshness, schema version, credential ping). Full spec in
`codex/04-architecture/promote-workflow-architecture.md`.
