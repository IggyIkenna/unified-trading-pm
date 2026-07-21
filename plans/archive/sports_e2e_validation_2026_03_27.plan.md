---
doc_type: plan
title: Sports E2E Validation + Arb Pipeline
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-27
priority: P0
updated: 2026-03-27
supersedes: [sports_batch_pipeline_end_to_end_2026_03_25.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

## Deferred work — migrated to: `plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md`,

`plans/archive/2026_07/sports_features_readiness_for_predictions_2026_06_20.md` — successor:
sports_p2_features_history_to_ml_ready_2026_06_27 (Phase 2 MTDS/MDPS/FSS bucket-validation goal, now on the 8-bucket ML
grid); the Phase-4 credit-cost/288M-row/BigQuery cluster was explicitly DROPPED per this plan's own archive banner and
independently superseded (288M migration shipped 2026-05-23). **GENUINELY ORPHANED**: `spread_calculator` +
strategy-service arb backtest + optimal-window analysis (Phase 3), and MTDS/MDPS/FSS/strategy live-mode wiring (Phase 5)
— bundled into `plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`. No
`locked_by` is set on this file.)

> **ARCHIVED 2026-05-05.** Folded into
> [`sports_predictions_e2e_2026_05_05`](../active/sports_predictions_e2e_2026_05_05.plan.md). Phases 2/3/5 (MTDS Tier 2
> 1-week validation, arb backtest, live pipeline) are absorbed there. **Phase 4 (Tier 1 ML 126M + Tier 2 arb 103M = 207M
> credit re-collection) is DROPPED, not deferred** — predictions don't need fine-grain arb bucketing, and the 8-bucket
> ML horizon adapter (`SportsBucketAssignmentAdapter` in MDPS) covers what predictions need on the existing 288M rows.
> Treat this archived plan as historical context only; do not revive Phase 4 without reopening the predictions-vs-arb
> scope debate first.
>
> **Reconciliation note (2026-04-25):** This plan absorbs
> [sports_batch_pipeline_end_to_end_2026_03_25.plan.md](./sports_batch_pipeline_end_to_end_2026_03_25.plan.md).
> sports_e2e_validation supersedes the MTDS adapter portion of sports_batch_pipeline per its body text See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Sports E2E Validation + Arb Pipeline

> **Conflict resolution**: This plan supersedes sports_batch_pipeline MTDS adapter work.
> canonical_team_mapping_propagation owns all MTDS/FSS-level team name and fixture validation infrastructure — this plan
> owns arb pipeline validation only (arb scan, backtest, live pipeline). Avoid duplicating fixture validation logic.

## Context

Phase A (reference data backfill) and Phase D (odds migration) complete. MTDS validated for 1 day (248K rows, 16min).
Critical discovery: MTDS used fixed UTC timestamps instead of per-fixture kickoff-relative timestamps. T-120m was a dead
zone (3% coverage) — confirmed as collection artifact via live API test showing 20/20 bookmakers within 93s bm_time
spread at correct T-120m. User upgrading Odds API to 50M credits per refill. Total budget: ~207M credits for full
backfill (4.1 refills).

**Design doc**: `memory/sports_odds_final_design_2026_03_27.md`

## Phase 1: MTDS Adapter Rewrite (SEQUENTIAL)

Rewrite odds adapter for per-fixture timestamps. `bm_time` as ground truth.

- [x] [SCRIPT] P0. Validate MTDS for 1 day with current adapter (248K rows, 16min, 72K credits)
- [x] [ANALYSIS] P0. Confirm T-120m dead zone is collection artifact (live API test: 93s bm_time spread at correct time)
- [x] [DESIGN] P0. Final bucket design: Tier 1 (12 ML buckets) + Tier 2 (57 arb buckets)
- [x] [CODE] P0. Rewrite `OddsApiAdapter.download_batch()` — per-fixture timestamps from kickoff times
- [x] [CODE] P0. Add `fetch_utc, staleness_seconds, minutes_to_kickoff, bm_time` columns to output
- [x] [CODE] P0. Change GCS path: `venue=ODDS_API` → `source=ODDS_API`
- [x] [CODE] P1. Support Tier 1 (12 buckets) and Tier 2 (57 buckets) modes via `--tier` CLI flag

**Success criteria**: MTDS downloads odds at correct per-fixture times. bm_time matches expected bucket within
tolerance.

## Phase 2: 1-Week Validation (SEQUENTIAL, after Phase 1)

Run full pipeline for 1 week. Validate data quality, arb opportunities, feature computation.

- [ ] [SCRIPT] P0. Run MTDS Tier 2 (57 buckets) for 1 recent week — all leagues
- [ ] [ANALYSIS] P0. Verify bm_time freshness: ≥18 bookmakers within ±60s at T-10m, T-30m, T-60m, T-120m
- [ ] [ANALYSIS] P0. Arb scan: find cross-bookmaker arb opportunities (bm_time ±60s, implied prob > 100%)
- [ ] [ANALYSIS] P0. Arb by time horizon: how much arb at T-4h vs T-2h vs T-30m vs T-10m?
- [ ] [ANALYSIS] P0. Arb by league: which leagues have most/least efficient markets?
- [ ] [SCRIPT] P1. Run MDPS cleaning pass — filter by bm_time freshness, add buckets
- [ ] [SCRIPT] P1. Run FSS on cleaned data — verify odds features (velocity, CLV, steam)
- [ ] [SCRIPT] P1. Verify feature matrix is ML-ready (one row per fixture, all features as columns)

**Success criteria**: Clear picture of arb landscape. Features compute correctly from clean data. Arb backtest possible.

## Phase 3: Arb Backtest (SEQUENTIAL, after Phase 2)

Run actual arb backtest using the full system.

- [ ] [CODE] P0. Implement arb_calculator in FSS (cross-bookmaker arb %, eligible pairs, duration)
- [ ] [CODE] P0. Implement spread_calculator in FSS (sharp-soft spread, vig, max-min)
- [ ] [SCRIPT] P0. Run strategy-service arb backtest on 1-week data
- [x] [ANALYSIS] P0. P&L analysis: expected arb return per fixture, per league, per time horizon
- [ ] [ANALYSIS] P1. Determine optimal X hours window for arb (cost vs opportunity trade-off)

**Success criteria**: Arb backtest runs E2E. Clear P&L picture per league/time horizon.

## Phase 4: Full System Integration (after Phase 3)

When satisfied with 1-week results, plan the full backfill.

- [ ] [PLAN] P0. Cost plan: Tier 1 (126M credits, 5.8yr) + Tier 2 (103M credits, 1yr) = 207M total
- [x] [CODE] P0. Wire MDPS for sports odds processing (L2.5 in pipeline) — DONE (2026-04-03):
      SportsBucketAssignmentAdapter registered in MDPS
- [ ] [SCRIPT] P0. Run Tier 2 backfill (1 year, arb quality) — ~103M credits
- [ ] [SCRIPT] P1. Run Tier 1 backfill (5.8 years, ML quality) — ~126M credits
- [ ] [SCRIPT] P1. Regenerate features from backfilled data
- [ ] [SCRIPT] P2. Migrate existing 288M rows to `source=ODDS_API`, relabel with bm_time for long-horizon features
- [ ] [SCRIPT] P2. BigQuery external tables over new data
- [ ] [SCRIPT] P2. Cleanup old `venue=ODDS_API` paths

**Success criteria**: Full historical coverage. Features regenerated. Arb backtest on full history.

## Phase 5: Live Pipeline (after Phase 4)

- [ ] [CODE] P1. MTDS live mode: capture odds per fixture schedule (Pub/Sub trigger)
- [ ] [CODE] P1. MDPS live mode: clean + bucket in real-time
- [ ] [CODE] P1. FSS live mode: compute features per fixture ~60min pre-KO
- [ ] [CODE] P2. Strategy live mode: arb detection + signal generation

**Success criteria**: Batch = live. Same schema, same paths, same features.

## Dependency Graph

```
Phase 1 (adapter rewrite)
    │
    └──→ Phase 2 (1-week validation)
              │
              └──→ Phase 3 (arb backtest)
                        │
                        └──→ Phase 4 (full integration + backfill)
                                  │
                                  └──→ Phase 5 (live pipeline)
```
