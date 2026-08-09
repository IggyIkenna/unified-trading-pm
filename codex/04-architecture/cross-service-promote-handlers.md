---
doc_type: codex-ssot
title: Cross-Service Promote Handlers
summary:
  "STUB (see promote-workflow-architecture.md): per-service PromoteHandler that validates preconditions (manifest
  freshness, schema version, credential ping) when a strategy promotes paper→live."
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [promote, handlers, strategy, stub, paper-live]
related: [/codex/04-architecture/promote-workflow-architecture.md]
created: 2026-05-21
authoritative_for:
referenced_by: [/codex/04-architecture/live-deployment-manifest.md]
owner:
last_reviewed: 2026-10-22
code_refs:
type: architecture
---

# Cross-Service Promote Handlers

> **STUB** — Reference: `/codex/04-architecture/promote-workflow-architecture.md`.

Handlers that execute when a strategy is promoted from paper → live. Each service registers a `PromoteHandler` that
validates its preconditions (manifest freshness, schema version, credential ping). Full spec in
`/codex/04-architecture/promote-workflow-architecture.md`.
