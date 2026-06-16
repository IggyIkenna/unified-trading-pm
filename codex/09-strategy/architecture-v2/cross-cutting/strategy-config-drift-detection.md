---
scope: [engineer, admin]
title: Strategy Config Drift Detection
type: strategy
status: stub
created: 2026-05-21
---

# Strategy Config Drift Detection

> **STUB** — Reference: `codex/04-architecture/promote-workflow-architecture.md`.

Detects when a live strategy's runtime config has drifted from the promoted config snapshot. Triggers
`CONFIG_DRIFT_ALERT` event + pauses the strategy pending operator review. Full spec:
`codex/04-architecture/promote-workflow-architecture.md`.
