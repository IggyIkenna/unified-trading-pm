---
doc_type: plan
title: prediction-markets-may-23-2026
summary:
status: complete
nature: record
asset_group: prediction
stage: [meta]
repos: []
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

## Deferred work — migrated to: `plans/epics/predictions_master.md` — successor: predictions_master (every open item —

Polymarket/Kalshi/data-pipeline/cross-asset-features/LookaheadBiasError/cluster-validation/strategy+execution — is
routed through that epic's "Workstream routing" table to its live children, e.g.
`plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md`,
`plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md`. Opinion Trade backtest + CME event-futures arb
backtest were explicitly ruled OUT-of-scope 2026-05-08. NOTE: `locked_by: live-defi-rollout` was never cleared at
archival — flagged for operator `[unlock-plan]` cleanup.)

# Epic — Prediction Markets (May 23 2026)

> **🔴 SUPERSEDED 2026-05-08** — folded into [`predictions_master_2026_05_07.md`](./predictions_master_2026_05_07.md) §
> "May-23 deliverable" per operator direction. This file is archived; content remains verbatim for archaeology. **Edit
> the master, not this file.**

## Why this epic exists

Prediction-markets ship **full backtest** for May 23 — features → strategy → execution all backtest, no live. Like the
sports ML epic, this is end-to-end pipeline coverage at every layer; unlike S&P prediction which only goes to ML
training. The archetypes covered:

- **Polymarket** prediction-market trading (canonical question groups: BTC/SPX up-down hourly/daily, election cycles).
- **Kalshi** prediction-market trading (CFTC-regulated US event markets).
- **Opinion Trade** (Indian prediction-market venue).
- **CME event futures arbitrage** — wherever a CME event future has a corresponding Polymarket / Kalshi market, the
  arbitrage is backtestable.

The features the strategies consume may include not just prediction-market features but also cross-asset features (S&P,
sports, crypto) — since prediction-markets often resolve based on outcomes that other features predict.

## End-state at May 23 (success criteria)

- [ ] **Polymarket backtest** runs end-to-end through unified pipeline for at least one canonical-question-group
      archetype (BTC up-down hourly OR SPX up-down daily OR similar).
- [ ] **Kalshi backtest** runs for at least one event family (e.g. CPI prints, FOMC outcomes).
- [ ] **Opinion Trade backtest** runs for at least one event family.
- [ ] **CME event futures arbitrage backtest** runs for at least one cross-venue pair (e.g. CME inflation event future
      vs Kalshi CPI market).
- [ ] **Prediction data pipeline clean**: instruments (per-market lifecycle: market_created_at / resolution_time /
      settlement_time) + tick data (CLOB captures respecting lifecycle bounds) + features (canonical-question-group
      bundle SSOT).
- [ ] **Cross-asset features wired**: S&P features, sports features, crypto features all consumable by prediction
      strategies as inputs.
- [ ] **LookaheadBiasError strict** at every features compute — feature compute at time T can only consume ticks where
      tick.timestamp ≤ T AND tick.market_id's market_created_at ≤ T (per CLAUDE.md "Prediction market lifecycle timing"
      SSOT).
- [ ] **Cluster validation MANDATORY** for `prediction_canonical_question_group` bundle data_type at `record_captured`
      (per CLAUDE.md SSOT — UAC `BUNDLED_DATA_TYPES` includes prediction).
- [ ] **Strategy + execution layers PROGRESSED** through unified pipeline — backtest is end-to-end, no inline
      settlement.

## What's IN scope

- Full backtest of 4 prediction-market archetypes (Polymarket / Kalshi / Opinion Trade / CME event futures arb).
- Prediction-market data pipeline: instrument lifecycle (3 timestamps per market_id), CLOB tick capture, canonical-
  question-group bundle aggregation.
- Cross-asset feature consumption (S&P, sports, crypto) by prediction-market strategies.
- Strategy + execution backtest through the unified pipeline — no standalone backtest engines, no inline settlement.

## What's OUT of scope (shipping later)

- **Live trading** — backtest-only this cycle.
- **Live tick capture** — batch-only is sufficient for the backtest deliverable.
- **Production deployment** of any prediction strategy — backtest-runnable is the deliverable.
- **Full canonical-question-group SSOT for every market_id** — cover at minimum the archetypes in scope; remaining
  market_id mappings can land post-May-23.

## Sub-plans this epic consumes

| Path                                                                                                                      | Role                                                                              | Status |
| ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------ |
| [`predictions_master_2026_05_07`](./predictions_master_2026_05_07.plan.md)                                                | Prediction asset_group umbrella (folds-in canonical-question-group migration)     | Active |
| [`active/cme_polymarket_arb_2026_05_08`](../active/cme_polymarket_arb_2026_05_08.plan.md)                                 | CME event futures × Polymarket arbitrage archetype                                | Active |
| [`ml_and_features_master_2026_05_07`](./ml_and_features_master_2026_05_07.plan.md)                                        | ML lifecycle + features umbrella (cross-asset features for prediction strategies) | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.plan.md)                                    | Strategy v2 + DART backtest harness                                               | Active |
| [`active/writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.plan.md) | Write-gate / honest-coverage umbrella                                             | Active |
| [`manifest_migration_master_2026_05_07`](./manifest_migration_master_2026_05_07.plan.md)                                  | Manifest schema v6 (prediction_canonical_question_group as bundle data_type)      | Active |
| [`active/features_repo_consolidation_2026_05_08`](../active/features_repo_consolidation_2026_05_08.plan.md)               | Features-repo consolidation                                                       | Active |

## Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue (prediction archetypes × all venues + canonical
  question groups enumerated). Cross-asset features depend on `sp_prediction_may_23_2026` (S&P features) +
  `sports_ml_may_23_2026` (sports features) + DeFi/CeFi crypto features (from `live_defi_rollout` + `cefi_ml`).
- **Shares with:** Cross-asset features pipeline shared with all other ML/backtest epics.

## Cross-cutting concerns inherited

See [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md). Specific to this epic:

- **Strategy catalogue (HARD)**: 4 prediction-market archetypes × all canonical-question-groups + all venues enumerated.
- **Infrastructure**: prediction lifecycle SSOT, canonical-question-group bundle SSOT, cross-asset feature DAG.

## Open questions

- [ ] **Which canonical question groups MUST land for May 23?** Operator-pick: BTC up-down hourly + SPX up-down daily
      seem like the strong candidates. Other recurring families (election, CPI prints) optional.
- [ ] **CME event futures inventory**: which CME event futures are in scope for the cross-venue arb backtest?
- [ ] **Opinion Trade integration depth**: API access + venue connector? Or static historical odds-only for backtest?

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.plan.md) — May-23 cutover master
- CLAUDE.md "Prediction market lifecycle timing" + "Cluster validation MANDATORY" sections
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
