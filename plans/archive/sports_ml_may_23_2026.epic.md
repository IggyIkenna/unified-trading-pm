---
doc_type: plan
title: sports-ml-may-23-2026
summary:
status: complete
nature: record
asset_group: sports
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

## Deferred work — migrated to: `plans/active/sports_consolidated_closeout_2026_07_19.md`,

`plans/active/sports_master_closeout_2026_07_21.md`, `plans/active/sports_manifest_canonicalisation_2026_06_01.md` —
successor: sports_consolidated_closeout_2026_07_19, sports_master_closeout_2026_07_21,
sports_manifest_canonicalisation_2026_06_01 (data-pipeline-clean, honest-coverage-baseline, and phantom-recovery items
are actively owned by these plans + several still-open issue docs; the matching-engine code for the sports L0 TOB
matcher already shipped per `plans/active/master_to_live_defi_2026_05_23.md`; the open-questions cluster was resolved
2026-05-08 per `plans/epics/sports_master.md`. **Two items are GENUINELY ORPHANED** — running a sports strategy backtest
and an execution backtest through the shipped L0 TOB matcher — filed as
`plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`. NOTE:
`locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]` cleanup.)

# Epic — Sports ML (May 23 2026)

> **🔴 SUPERSEDED 2026-05-08** — folded into [`sports_master_2026_05_07.md`](./sports_master_2026_05_07.md) § "May-23
> deliverable" per operator direction. This file is archived; content remains verbatim for archaeology. **Edit the
> master, not this file.**

## Why this epic exists

Sports ML prediction ships **backtest-only** for May 23, but unlike S&P prediction (which only goes up to ML training),
this epic goes **all the way through strategy backtest + execution backtest** as well. ML signal + strategy + execution
all backtest in the unified pipeline. No live trading.

The deliverable is a complete backtested sports ML archetype: instruments → odds → features → ML model → strategy
decision → execution-with-fills (matching engine). Every layer must work end-to-end in batch, and bugs/backfills/schema
fixes are inclusive at every layer.

## End-state at May 23 (success criteria)

- [ ] **Sports ML model trains end-to-end in batch** on representative history.
- [ ] **Strategy backtest** of the ML signal runs end-to-end through the unified pipeline (no standalone backtest
      engine, no inline settlement) — strategy interacts with position-balance-monitor, risk-and-exposure, and
      execution-service per the unified `Batch = Live` rule.
- [ ] **Execution backtest** runs through the matching engine (Sports L0 TOB matcher, per matching_engine SSOT) —
      simulated fills with accurate slippage / commission / latency / venue liquidity, NOT face-value odds.
- [ ] **Sports data pipeline clean** end-to-end: instruments (URDI sports/) + odds (api_football, footystats, odds_api,
      etc.) + features (features-sports) — no phantom rows, no NaN placeholders, manifest 100% honest, all
      `available_at` columns correctly stamped per row.
- [ ] **Honest-coverage baseline** for sports manifest: ratchet established + monitored.
- [ ] **Phantom recovery complete** for sports fixtures (truthset rebuild + capture-status reclassification finished).
- [ ] **Strategy + execution layers fixed where needed** — bugs across all 3 layers (ML + strategy + execution) caught
      in this cycle.

## What's IN scope

- Full backtest pipeline for sports ML: instruments → odds → features → ML training → ML inference → strategy →
  execution → position + risk + P&L attribution.
- Sports data backfill end-to-end: api_football, footystats, transfermarkt, understat, soccer_football_info, open_meteo,
  odds_api, MDPS odds horizon bucket.
- Sports phantom-recovery + honest-coverage close-outs.
- Sports `available_at` rename + per-row stamping (kickoff − 60min for lineups, event-time for events, match_end_time
  for post-match stats, etc.).
- Sports execution backtest with L0 TOB matcher (real fills, not face-value).
- 2-year-equivalent backtest config grid for the sports ML archetype.

## What's OUT of scope (shipping later)

- **Live trading** — backtest-only this cycle.
- **Live odds capture** — batch-only is sufficient for the ML deliverable (forward-poll continues but is not gating).
- **Multiple ML archetypes** — one sports ML archetype is the bar.
- **Production deployment** of the sports model — backtest-runnable is the deliverable.

## Sub-plans this epic consumes

| Path                                                                                                                           | Role                                                                       | Status |
| ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ------ |
| [`sports_master_2026_05_07`](./sports_master_2026_05_07.md)                                                                    | Sports umbrella (data pipeline + features + ML + strategy + execution)     | Active |
| [`ml_and_features_master_2026_05_07`](./ml_and_features_master_2026_05_07.md)                                                  | ML lifecycle + features umbrella                                           | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.md)                                              | Strategy v2 + DART manual-trade lane                                       | Active |
| [`active/api_football_minimal_flattening_removal_2026_05_07`](../active/api_football_minimal_flattening_removal_2026_05_07.md) | api_football odds schema cleanup                                           | Active |
| [`active/writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md)           | Write-gate / honest-coverage umbrella                                      | Active |
| [`active/features_repo_consolidation_2026_05_08`](../active/features_repo_consolidation_2026_05_08.md)                         | Features-repo consolidation (features-sports merges into features-service) | Active |
| [`active/live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md)               | Live-pipeline activation — batch portion is required here                  | Active |
| [`manifest_migration_master_2026_05_07`](./manifest_migration_master_2026_05_07.md)                                            | Manifest schema v6                                                         | Active |

## Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue (sports ML archetype + venues), infrastructure
  baseline, UI replication of backtest harness.
- **Shares with:** `cefi_ml_may_23_2026`, `sp_prediction_may_23_2026`, `prediction_markets_may_23_2026` share ML
  lifecycle (training pipeline, model registry, drift detection, batch backtest harness). Wins here propagate.
- **Provides to:** `prediction_markets_may_23_2026` may consume sports ML signals as inputs to sports-betting
  prediction-market strategies (Polymarket fixture markets).

## Cross-cutting concerns inherited

See [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md). Specific to this epic:

- **Strategy catalogue (HARD)**: sports ML archetype × all sports venues + bookmaker combos enumerated.
- **Infrastructure**: features-service consolidation, manifest honesty, matching engine fidelity for sports L0 TOB.

## Open questions

- [ ] **Which sports ML archetype?** Match-outcome prediction? Goal-scorer prediction? In-play live-odds? Operator-pick.
- [ ] **Which leagues are in scope** for the ML signal? All-leagues universal model, or top-tier subset
      (EPL/LaLiga/Serie A/Bundesliga/MLS)?
- [ ] **Bookmaker scope**: which odds sources for execution backtest? odds_api closing prices? MDPS odds horizon bucket
      for in-play snapshots?

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`codex/02-data/sports-scheduling-and-sharding.md`](../../codex/02-data/sports-scheduling-and-sharding.md)
- [`codex/04-architecture/batch-live-pipeline.md`](../../codex/04-architecture/batch-live-pipeline.md)
