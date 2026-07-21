---
doc_type: plan
title: sp-prediction-may-23-2026
summary:
status: complete
nature: record
asset_group: tradfi
stage: [meta]
repos: [execution-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
plan_type: epic
owner: ikenna
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
parent: master_to_live_defi_2026_05_23
deadline: 2026-05-23
---

## Deferred work — migrated to: `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`,

`plans/active/master_to_live_defi_2026_05_23.md` — successor: tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20,
master_to_live_defi_2026_05_23 (per `plans/epics/tradfi_master.md`'s explicit routing: the S&P feature/ML/backtest chain
is extracted to the first plan; strategy+execution progression is routed to the second plan's Group F. The 3
open-questions items were resolved 2026-05-08 per `plans/epics/tradfi_master.md`. NOTE: `locked_by: live-defi-rollout`
was never cleared at archival — flagged for operator `[unlock-plan]` cleanup.)

# Epic — S&P Prediction (CME) (May 23 2026)

> **🔴 SUPERSEDED 2026-05-08** — folded into [`tradfi_master_2026_05_07.md`](./tradfi_master_2026_05_07.md) § "May-23
> deliverable A — S&P prediction" per operator direction. This file is archived; content remains verbatim for
> archaeology. **Edit the master, not this file.**

## Why this epic exists

The S&P 500 prediction is the **TradFi ML deliverable** for May 23: a swing high/low ML model (re-using the C5 model
shape) that predicts the S&P from SP futures + Bitcoin features + calendar features. Batch-only ML — no live trading, no
live tick collection, no live instruments required. **Everything in the data pipeline that relates to this ML signal
must work end-to-end in batch.** All bugs, all backfills, all schema fixes — inclusive. Strategy and execution layers
can progress (where we can fix things, we still fix them) but are not gating for May 23.

## End-state at May 23 (success criteria)

- [ ] **S&P swing high/low ML model trains end-to-end in batch** on representative 2-year history.
- [ ] **Feature inputs complete**: SP futures (ES + MES + micro variants on CME) features + Bitcoin features + calendar
      features (holidays, half-days, expiries, FOMC, NFP, CPI).
- [ ] **Instrument data clean** for ES/MES/Bitcoin futures across the training window — manifest 100% honest, no
      empty-placeholder rows, no phantom captured rows, no stale schema parquets.
- [ ] **MTDS tick data clean** for ES/MES/BTC futures + S&P spot index sources + ETF references — full backfill across
      training window, every (venue, data_type, day) row resolves to honest captured/empty_confirmed/attempted_failed.
- [ ] **MDPS bar data clean** — no 1440-NaN-OHLCV-placeholder regression, every (venue, data_type, day) bar populated or
      honestly empty per `venue_trading_calendar`.
- [ ] **Features pipeline clean** — features-tradfi (or post-consolidation features-service) emits feature parquets
      without NaN-blanket placeholders; `available_at` correctly stamped per row; LookaheadBiasError strict-mode passes.
- [ ] **ML training pipeline clean** — model trains with no skipped windows, no silent NaN-substitution, no leaked
      future data; reproducible from a single config + random seed.
- [ ] **Strategy + execution layers PROGRESSED, not gated** — no stubs, no removals; whatever can be fixed in
      `strategy_and_dart_master` + execution-service for this archetype is fixed; the gating success criterion is the ML
      model trains cleanly, not full strategy/execution coverage.
- [ ] **Backtest harness wired** — 2-year config grid runner exists (per Group F item 18 of master plan readiness) even
      though we're not launching live; the backtest is part of the ML deliverable.

## What's IN scope

- The full ML data pipeline for S&P prediction: instruments → MTDS → MDPS → features → ML training.
- All bugs, backfills, schema fixes, NaN-placeholder cleanups, manifest reconcilers, feature `available_at` stamping
  fixes, LookaheadBias strict-mode wiring — every blocking item that prevents a clean batch ML run.
- 2-year batch backtest config grid for the S&P swing high/low archetype.
- Calendar features end-to-end: holidays, expiries, half-days, macro releases (FOMC, NFP, CPI).
- Bitcoin feature inputs (cross-asset features from CeFi + DeFi BTC sources).
- TradFi infrastructure cleanup: ES.OPT bundle cluster validation, ETF backfill, futures continuous-contract rolling.

## What's OUT of scope (shipping later)

- **Live trading** — no live this cycle.
- **Live tick collection** for any of the inputs — batch-only.
- **Live instrument refresh** — batch-only.
- **Strategy catalogue completeness for this archetype** — the strategy catalogue cross-cutting requirement still
  applies (see cross_cutting epic), but launching the strategy live is post-May-23.
- **Production deployment of the model** — model trains cleanly, that's the deliverable; live serving is post-cycle.

## Sub-plans this epic consumes

| Path                                                                                                                                   | Role                                                                                               | Status |
| -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------ |
| [`tradfi_master_2026_05_07`](./tradfi_master_2026_05_07.md)                                                                            | TradFi data pipeline umbrella (instruments + MTDS + MDPS + features for ES/MES/ETFs/SPX)           | Active |
| [`ml_and_features_master_2026_05_07`](./ml_and_features_master_2026_05_07.md)                                                          | ML lifecycle + features umbrella (training pipeline, calendar features, Bitcoin cross-asset feats) | Active |
| [`active/instruments_and_market_tick_data_completion_2026_05_01`](../active/instruments_and_market_tick_data_completion_2026_05_01..md | Instruments + MTDS completion (full backfill, manifest honesty)                                    | Active |
| [`active/writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md)                   | Write-gate / honest-coverage umbrella — gates manifest honesty for every TradFi shard              | Active |
| [`manifest_migration_master_2026_05_07`](./manifest_migration_master_2026_05_07.md)                                                    | Manifest schema v6 + migration coordination                                                        | Active |
| [`active/features_repo_consolidation_2026_05_08`](../active/features_repo_consolidation_2026_05_08.md)                                 | Features-repo consolidation (pre-req for clean features pipeline)                                  | Active |
| [`active/live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md)                       | Live-pipeline activation (batch-mode is also covered here; live mode itself OUT of scope)          | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.md)                                                      | Strategy v2 — progressed-not-gated for this epic                                                   | Active |

## Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue completeness (S&P archetype + venue combos
  enumerated even though not launching), infrastructure baseline.
- **Shares with:** `cefi_ml_may_23_2026` shares the ML lifecycle infrastructure (training pipeline, model registry,
  features-service consolidation). `price_arbitrage_may_23_2026` shares the ES/MES/ETF instrument + MTDS data — both
  epics need the same TradFi backfill clean.
- **Provides to:** `prediction_markets_may_23_2026` may consume S&P features as cross-asset inputs for prediction-market
  strategies (e.g. SPX-up-down canonical question groups).

## Cross-cutting concerns inherited

See [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md). Specific to this epic:

- **Strategy catalogue (HARD)**: S&P swing high/low archetype × venue combos enumerated even though not launching this
  cycle.
- **Infrastructure**: features-service consolidation, manifest honesty, write-gate coverage, AWS↔GCP parity at the
  batch-data layer.
- **UI replication**: not gating for this epic (no live trading), but DART harness should still be able to backtest /
  inspect the S&P signal.

## Open questions

- [ ] **C5 model shape — is the swing high/low ML model spec already stable, or does this epic include
      model-architecture work?** If the latter, scope expands. Expected: spec stable; this epic is about the data + ML
      pipeline, not model R&D.
- [ ] **Calendar feature inputs**: which exact macro events? FOMC + NFP + CPI minimum; PCE + retail sales optional.
      Operator-pick before May 14.
- [ ] **Bitcoin features at what granularity?** Daily? Hourly? 15-min? Affects which CeFi/DeFi sources are needed.

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md)
- [`codex/04-architecture/batch-live-pipeline.md`](../../codex/04-architecture/batch-live-pipeline.md)
