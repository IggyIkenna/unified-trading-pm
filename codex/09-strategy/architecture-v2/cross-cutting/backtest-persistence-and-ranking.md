---
doc_type: codex-ssot
title: Backtest Persistence and Ranking
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

# Backtest Persistence and Ranking

> **STUB** — Reference: `plans/epics/defi_master.md`.

Backtest results persisted to `gs://strategy-store-{pid}/backtests/`. Ranked by Sharpe ratio, max drawdown, and regime
stability. The top N configs per archetype are promoted to paper candidates. Full spec pending strategy Phase 3.
