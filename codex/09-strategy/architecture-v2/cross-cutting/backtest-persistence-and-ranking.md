---
doc_type: codex-ssot
title: Backtest Persistence and Ranking
summary:
  STUB — backtest results persisted to gs://strategy-store-{pid}/backtests/, ranked by Sharpe ratio + max drawdown +
  regime stability, with the top-N configs per archetype promoted to paper candidates; full spec pending strategy Phase
  3.
implementation_status: stub
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, backtest, ranking, archetypes]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/backtest-run-manifest.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md,
  ]
created: 2026-05-21
authoritative_for: []
referenced_by: [/codex/09-strategy/architecture-v2/cross-cutting/backtest-run-manifest.md]
owner:
last_reviewed:
code_refs:
type: strategy
---

# Backtest Persistence and Ranking

> **STUB** — Reference: `plans/epics/defi_master.md`.

Backtest results persisted to `gs://strategy-store-{pid}/backtests/`. Ranked by Sharpe ratio, max drawdown, and regime
stability. The top N configs per archetype are promoted to paper candidates. Full spec pending strategy Phase 3.
