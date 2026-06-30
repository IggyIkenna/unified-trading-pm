---
doc_type: codex-ssot
title: Strategy Config Drift Detection
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
type: strategy
---

# Strategy Config Drift Detection

> **STUB** — Reference: `codex/04-architecture/promote-workflow-architecture.md`.

Detects when a live strategy's runtime config has drifted from the promoted config snapshot. Triggers
`CONFIG_DRIFT_ALERT` event + pauses the strategy pending operator review. Full spec:
`codex/04-architecture/promote-workflow-architecture.md`.
