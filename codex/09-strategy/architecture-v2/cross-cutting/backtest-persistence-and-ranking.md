---
scope: [engineer, admin]
title: Backtest Persistence and Ranking
type: strategy
status: stub
created: 2026-05-21
---

# Backtest Persistence and Ranking

> **STUB** — Reference: `plans/epics/defi_master.md`.

Backtest results persisted to `gs://strategy-store-{pid}/backtests/`. Ranked by Sharpe ratio, max drawdown, and regime
stability. The top N configs per archetype are promoted to paper candidates. Full spec pending strategy Phase 3.
