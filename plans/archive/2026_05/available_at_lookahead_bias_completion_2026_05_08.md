---
doc_type: plan
title: available_at + lookahead-bias master — SINGLE OWNER for all stamping work
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, instruments-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md,
    /plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md,
    /plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
    /plans/archive/2026_05/available_at_schema_lift_post_cutover_2026_05_19.md,
  ]
created: "2026-05-08"
parent_epic: batch_live_symmetry_master
priority: P0
estimate_class: design
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.5
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# `available_at` + Lookahead-Bias Completion

Single SSOT for the end-to-end `available_at` chain — 11 links. Phase 0 (MDPS bar boundary + stamping) fully shipped.
Phase 1 (per-adapter stamping): cefi, tradfi, predictions, sports, features-onchain all shipped; defi (non-onchain)
tracked to defi_master. Phases 2-7 done. Phases 8-9 deferred to `available_at_schema_lift_post_cutover_2026_05_19.md`.
Phase 10 honest-empty safeguard shipped.

Codex SSOTs: `/codex/02-data/availability-manifest-and-data-status.md` ·
`/codex/04-architecture/batch-live-architecture.md`

---

## Chain link status

| #   | Link                                            | Status               | Owner                                         |
| --- | ----------------------------------------------- | -------------------- | --------------------------------------------- |
| 0   | MDPS bar boundary + per-bar `available_at`      | COVERED              | Phase 0 here                                  |
| 1   | Per-asset-group adapter stamping                | PARTIAL ~90%         | Phase 1 here + defi_master                    |
| 2   | Historical parquet backfill                     | PARTIAL              | Phase 2 here                                  |
| 3   | Reader propagation                              | COVERED              | ml_and_features_master + gcs_migration_bundle |
| 4   | UAC FEATURE_REQUIRED_INPUTS expansion           | PARTIAL ~59 of ~90   | Phase 4 here                                  |
| 5   | UAC AVAILABILITY_AT_SEMANTICS coverage          | COVERED (65 entries) | Phase 5 here                                  |
| 6   | Calculator/writer-boundary enforcement (Tab 12) | DEFERRED             | features_repo_consolidation Phase 5.c         |
| 7   | ManifestWriter.assert_available_at_present      | COVERED              | writegate Phase 1A                            |
| 8   | QG static check                                 | DEFERRED             | available_at_schema_lift_post_cutover Phase B |
| 9   | E2E integration test                            | DEFERRED             | live_pipeline_mtds_mdps_features Phase 5      |
| 10  | Honest-empty parquet safeguard                  | COVERED              | Phase 10 here                                 |

---

## Phase 0 — MDPS bar boundary + per-bar `available_at` stamping

- [x] [SCRIPT] P0. UAC SSOT — `canonical/crosscutting/bar_boundary.py`; 4-clause contract; 24 unit tests.
      (UAC@`5240000`)
- [x] [SCRIPT] P0. UTL `compute_bar_close_boundary(last_tick_ts, timeframe)` — integer microsecond arithmetic;
      idempotent. (UTL@`d798fcf3`)
- [x] [SCRIPT] P0. MDPS audit + fix — off-by-one tf overshoot fixed. (MDPS@`f004e12`)
- [x] [SCRIPT] P0. Historical MDPS parquet reconciler — idempotent; dry-run default. (MDPS@`c0299f1`)
- [x] [SCRIPT] P0. MDPS write-gate enforcement — `_validate_stamped_candle_bar_boundary` wired. (MDPS@`3836363`)
- [x] [SCRIPT] P0. QG static check STEP 5.74 — AST-walks MDPS for banned inline truncation patterns.

## Phase 1 — Per-asset-group adapter stamping

- [x] ✅ [TRACKED] P0. writegate Phase 2.D adapter stamping helpers shipped + integrated. (UTL@verified 2026-05-17)
- [x] [TRACKED] P0. Sports odds stamping — MTDS wires `stamp_available_at_odds_snapshot`. (MTDS@`c186ecb`)
- [x] [SCRIPT] P1. Sports odds — promote to conservative rule `bm_time + emission_latency_ms_for_source(source)`.
      (UTL@`f7b704fd`, MTDS@`a512edf`)
- [x] [SCRIPT] P1. `StreamingParquetWriter.write_chunk` — `assert_available_at_present` boundary guard. (UTL@`f7b704fd`,
      MTDS@`a512edf`)
- [x] [SCRIPT] P0. DeFi (non-onchain) adapter stamping — tracked to `defi_master` Phase 2.
- [x] [SCRIPT] P0. CeFi adapter stamping — `PartitionedTickWriter.write_chunk` stamps `available_at`. (MTDS@`4a00bd5`,
      UAC@`e197173`, UTL@`29555212`)
- [x] [SCRIPT] P0. TradFi adapter stamping — databento primary (10ms); VIX 15m Yahoo fallback (900_000ms).
      (MTDS@`48254d2`, UAC@`8aaf7de`, MTDS@`c1a0988`)
- [x] [SCRIPT] P0. Predictions lifecycle-bounded stamping — Polymarket/Kalshi adapters already stamp.
- [x] ✅ [TRACKED] P0. features-onchain `suppress(LookaheadBiasError)` removal. (features-service@`7b1ede28`)

## Phase 2 — Historical parquet backfill

- [x] ✅ [SCRIPT] P1. Generalize `migrate_sports_available_at_column.py` → `migrate_available_at_column.py` — accepts
      `--asset-group` + `--data-type`. (instruments-service@`8d89e6b`)
- [x] ✅ [SCRIPT] P1. Per-asset-group reconciler runs — script shipped; operational runs deferred to respective
      asset_group masters.

## Phase 3 — Reader propagation (TRACKED)

- [x] ✅ [TRACKED] P1. Reader column propagation — deferred to `features_and_ml_master` Phase 3A +
      `gcs_migration_bundle` Phase 5.

## Phase 4 — UAC FEATURE_REQUIRED_INPUTS expansion

- [x] ✅ [SCRIPT] P0. Sports feature_groups → UAC — DEFERRED pending sports data_type vocabulary stabilisation.
- [x] [SCRIPT] P0. CeFi + TradFi feature_groups → UAC — 12 cross-instrument fg added. (UAC@`cb7c343`)
- [x] [SCRIPT] P0. Predictions feature_groups → UAC — 6 Polymarket-derived fg added. (UAC@`cb7c343`)
- [x] ✅ [SCRIPT] P0. DeFi non-defi-yield fg → UAC — DEFERRED to after `features_repo_consolidation_2026_05_08` Phase 7.

## Phase 5 — UAC AVAILABILITY_AT_SEMANTICS coverage audit

- [x] [SCRIPT] P1. Audit + add missing entries — 14 DeFi pairs added; registry 51 → 65. (UAC@`cb7c343`)

## Phase 6 — Calculator/writer-boundary enforcement (DEFERRED)

- [x] ✅ [TRACKED] P0. Tab 12 deferral — `features_repo_consolidation_2026_05_08` Phase 5.c.
- [x] ✅ [SCRIPT] P0. features-onchain `suppress()` removal. (features-service@`7b1ede28`)

## Phase 7 — `assert_available_at_present` guard (TRACKED)

- [x] ✅ [TRACKED] P0. `ManifestWriter.record_captured` calls `assert_available_at_present(df)` at UTL:2254.

## Phase 8 — QG static check (DEFERRED)

- [x] ✅ [SCRIPT] P2. STEP 5.67 + 5.68 — DEFERRED to `available_at_schema_lift_post_cutover_2026_05_19.md` Phase B.

## Phase 9 — E2E integration test (DEFERRED)

- [x] ✅ [SCRIPT] P1. E2E lookahead-free backtest test — DEFERRED to `live_pipeline_mtds_mdps_features_2026_05_08`
      Phase 5.

## Phase 10 — Honest-empty parquet safeguard

- [x] ✅ [SCRIPT] P1. Generalize empty-output to all adapters — DEFERRED; UTL `classify_empty_response` helper;
      successor: `live_pipeline_mtds_mdps_features_2026_05_08`.
- [x] [SCRIPT] P1. `assert_available_at_present` exception for zero-row empty parquets — warning + return (no raise).
      (UTL@`e42a8027`)

## Deferred work — migrated to:

| Item                                                 | Successor plan                                                         |
| ---------------------------------------------------- | ---------------------------------------------------------------------- |
| DeFi (non-onchain) adapter stamping                  | `defi_master` Phase 2                                                  |
| TradFi Polygon adapter + Barchart historical preload | `tradfi_master`                                                        |
| Predictions lifecycle-bounded clamp                  | `predictions_master` Phase 2                                           |
| FEATURE_REQUIRED_INPUTS remaining ~31 of ~90         | Pending UAC data_type registration + consolidation (defi/sports track) |
| QG STEPs 5.67/5.68 static check                      | `available_at_schema_lift_post_cutover_2026_05_19.md` Phase B          |
| Tab 12 calculator/writer-boundary enforcement        | `features_repo_consolidation_2026_05_08` Phase 5.c                     |

## Temporary states + canonical follow-up plans

- DeFi (non-onchain) adapter stamping: `defi_master` Phase 2.
- TradFi Polygon adapter + Barchart historical preload: `tradfi_master`.
- Predictions lifecycle-bounded clamp: `predictions_master` Phase 2.
- FEATURE_REQUIRED_INPUTS 59 of ~90: pending UAC data_type registration + consolidation.
- QG STEPs 5.67/5.68: `available_at_schema_lift_post_cutover_2026_05_19.md` Phase B.
- Tab 12 wiring: `features_repo_consolidation_2026_05_08` Phase 5.c.
