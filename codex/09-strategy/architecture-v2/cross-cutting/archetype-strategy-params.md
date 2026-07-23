---
doc_type: codex-ssot
title: Archetype Strategy Parameters
summary:
  STUB pointer for per-archetype parameter schema (target LTV, rebalance threshold, hedge ratio, entry/exit signals)
  validated by StrategyConfig in strategy-service; the concrete source-cited realisation is
  archetype-param-schema-inventory.md, full per-archetype specs under architecture-v2/archetypes/.
implementation_status: stub
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, archetypes, params, defi]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md,
    /codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md,
  ]
created: 2026-05-21
authoritative_for: []
referenced_by: [/codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md]
owner:
last_reviewed:
code_refs:
type: strategy
---

# Archetype Strategy Parameters

> **STUB** — Reference: `codex/09-strategy/architecture-v2/archetypes/`.

Parameter schema for each archetype: target LTV, rebalance threshold, hedge ratio, entry/exit signals. Validated by
`StrategyConfig` in strategy-service. Full spec per-archetype in `codex/09-strategy/architecture-v2/archetypes/`.
