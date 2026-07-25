---
doc_type: plan
title:
  Prediction Phase D — formal smoke-test green + MVP backfill (split from prediction_consolidated_closeout_2026_07_18)
summary:
  Phase D of the prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — the `-test-`
  bucket isolation, MVP-scope reconciliation, and smoke-adaptation code fixes are shipped; residual open work is running
  `data-pipeline-check-is` / `data-pipeline-check-mtds` for prediction-only, all shards, to a formal post-migration
  green, then the MVP backfill readiness gate.
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [prediction, close-out, smoke-test, data-pipeline-check-is, data-pipeline-check-mtds, mvp-backfill, test-buckets]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_phase_ab_residuals_2026_07_24]
gate_on_depends: true
source: >-
  Split from `prediction_consolidated_closeout_2026_07_18.md` (Phase D section, lines 370-437 of that doc as of
  2026-07-18/2026-07-24) per the operator-approved line-cap remediation triage
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries"). Content moved verbatim, not summarized. `depends_on` + `gate_on_depends: true` added 2026-07-24 (plan
  audit finding) to encode this doc's own header text ("post-migration completion gate") as a real dispatch gate,
  matching the Phase E sibling's already-correct pattern — the migration is carried by
  `prediction_phase_ab_residuals_2026_07_24.md`.
---

# Prediction Phase D — formal smoke-test green + MVP backfill

> **Split from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-24).** This is the Phase D section of that
> close-out, moved verbatim. For the full historical execution narrative (Progress Log, ticks 1-31, 2026-07-18 through
> 2026-07-20 — including the tick-19/20/22/23 smoke-RED triage and fixes this phase's remaining formal-green run depends
> on) and shared cross-phase context (the Ground-truth verdict table, the prediction shard-atom definition, the MVP
> universe scope), see the parent doc. Sibling phase children: `prediction_phase_c_data_status_ui_2026_07_24.md` (Phase
> C), `prediction_phase_ab_residuals_2026_07_24.md` (Phase A-B), `prediction_phase_e_football_arb_live_2026_07_24.md`
> (Phase E — gated on this plan + the Phase A-B residuals plan).

## Phase D — re-smoke-test the backfills, prediction-only, ALL shards (post-migration completion gate)

> **Terminal data-readiness gate.** Post-migration, run BOTH pipeline-check skills scoped to **prediction only** and
> require green across every prediction shard — force-refetch + skip-if-fresh + a canonical-shape assertion — so we KNOW
> prediction is complete before any MVP backfill. Both skills already accept `--asset-group PREDICTION`; **do NOT pass
> `--tardis-only`** (Polymarket/Kalshi are not Tardis-sourced → it would enumerate 0 shards). Prediction shards: **IS =
> 2** `(PREDICTION, POLYMARKET)`, `(PREDICTION, KALSHI)` (IS atom has no data_type axis); **MTDS = 4**
> `{POLYMARKET, KALSHI} × {trades, book_snapshot_5}`.

- [x] ✅ [INFRA] P0. **MTDS prediction `-test-` bucket isolation FIXED end-to-end (2026-07-18).** The `-test-` bucket
      `market-data-tick-pred-test-central-element-323112` already exists (derived from `cloud-providers.yaml`
      `canonical_tiers=["prd","test"]`; no provisioning needed). THREE write/read paths converged to it: (1)
      verify-read + force-consolidate — `_test_bucket("prediction")` now returns the `-test-` bucket (was PROD
      fallback), `market-tick-data-service@b06d1e6b`; (2) batch WRITE — `get_tick_data_bucket(test_aware=True)` honours
      `IS_TEST_RUN` for prediction (was PROD-only), `mtds@2e50851d`; (3) live WRITE twin — `_resolve_live_bucket`
      honours `IS_TEST_RUN` (preserves `live=batch`), `mtds@86d70de9`. Guard test flipped + cross-AG
      (cefi/tradfi/defi/sports) byte-unchanged; QG-green (6320 passed). **Follow-ups flagged:** stale prose in
      `data_pipeline_e2e_check_2026_07_10.md` (L267-269 / 341-342 / 1025 / 1623 now false — "prediction stays
      PROD-only"), and UTL `get_write_bucket_name` still has a prediction-PROD-only branch (not a tick-write path, but a
      live inconsistency worth a follow-up). (repos: market-tick-data-service ✅)
- [x] ✅ [DATA] P1. **`book_snapshot_5` MVP-scope RECONCILED — `unified-api-contracts@53bf01d6`.** It was in all THREE
      data registries (`DATA_TYPES_BY_ASSET_GROUP`, `VENUE_DATA_TYPE_CAPABILITIES`, `expected_coverage`) but absent from
      `PredictionMvpRule.data_types` — verified NOT a deliberate trades-only exclusion (only COINBASE + Deribit-OPTION
      have such decisions; prediction cited none; all 3 registries re-added it 2026-06-23 when both CLOB venues began
      emitting it — the MVP rule was the un-updated outlier). Added `book_snapshot_5` to `PredictionMvpRule.data_types`
      (captured: 399,713 rows) + bumped `MVP_SCOPE_CONFIG_VERSION` 17→18; rule-11 cross-AG-unchanged test added
      (cefi/tradfi/defi/sports MVP sets pinned). `--mvp-only` prediction now tests all 4 shards. Operator can narrow
      back to trades-only if that was the intent (documented in the code). (repos: unified-api-contracts ✅)
- [x] ✅ [DATA] P1. **CQG cluster grain + `market_lifecycle` smoke coverage SHIPPED — `instruments-service@a3abd7a3`.**
      Added on the IS side — the genuine PRODUCER of both grains (the CQG bundle is written by IS `process_write`;
      `market_lifecycle` by IS `writers._write_market_lifecycle`). Correctly NOT faked on MTDS: MTDS only READS
      `market_lifecycle` as a pre-fetch gate + the CQG bundle is a manifest-only atom with no MTDS producer path, so a
      force/skip cell there would be fiction (documented in the MTDS smoke engine). (repos: instruments-service ✅)
- [x] ✅ [DATA] P0. **Prediction smoke adaptation + canonical regression cell SHIPPED (code-ready) —
      `market-tick-data-service@c805e6cb` + `instruments-service@a3abd7a3`.** Per-shard canonical regression cell added
      (prediction-scoped, mirrors `assert_tradfi_derivative_ids_canonical`): asserts per-CID
      `instrument_type == PREDICTION_MARKET` (the single equality catches every A0 drift — lowercase dupes,
      underlying-leakage, empty) + canonical `instrument_id` (non-empty, whitespace-free, PREDICTION_MARKET
      type-segment); soccer rows checked for `af_fixture_match_status`. Cross-AG byte-unchanged (cefi/tradfi/defi/sports
      pinned). Skills already accept `--asset-group PREDICTION`; the RUN (below) needs an operator `--day`. (repos:
      market-tick-data-service ✅, instruments-service ✅)
- [ ] [DATA] P0. **Run `data-pipeline-check-is` for prediction-only, all shards, post-migration** — real operator-given
      `--day` against `-test-` buckets; both prediction IS shards prove force/skip + canonical shape; report path cited.
- [ ] [DATA] P0. **Run `data-pipeline-check-mtds` for prediction-only, all shards, post-migration** — same day, all 4
      prediction MTDS shards prove force/skip + canonical shape; report path cited. **BOTH skills green across all
      prediction shards = prediction is code-complete, migrated, honestly-covered, and verified.** **PARTIAL 2026-07-19
      (tick 22):** all 6 smoke fixes landed; IS force leg DEMONSTRATED end-to-end (0-obj→182 CQG-first objects w/
      canonical `PREDICTION_MARKET`, `-test-` bucket, day=2026-06-28) — the dominant IS 0/14 RED is resolved;
      `book_snapshot_5` now honest live-only skip. Formal all-green still blocked ONLY by the `trades` catalogue-gating
      (next todo). The orphaned re-run produced no formal report (VM cleaned up); re-run cleanly once the
      catalogue-order follow-up lands.
- [x] [DATA] P1. **✅ DONE 2026-07-19 (tick 23) — `market-tick-data-service@7b0768d9`: pinned `deployment_env="prod"` on
      the 3 prediction universe-enumeration catalogue reads (`_polymarket_helpers.py` load + JSON fallback,
      `base_prediction_adapter.py::_load_market_lifecycle_for_date` = Kalshi's universe) — option (a): the market
      universe is global PROD reference data, so under `IS_TEST_RUN` the smoke reads the real prod universe (was empty
      `-test-` → 0 trades). Tick WRITES still isolated to `-test-` (separate bucket kind `market-data-tick-prediction`,
      test-aware, untouched); PROD byte-unchanged; RULE-11. +6 tests; QG green. Smoke-orchestration follow-up — `trades`
      `-test-` catalogue-gating (blocks Phase-D formal green) (surfaced tick 22).** The MTDS batch `trades` adapter
      enumerates its market universe from the `instruments-store-prediction` catalogue via ambient
      `DEPLOYMENT_ENV_SHORT`; on the `IS_TEST_RUN` smoke VM it read the empty `-test-` catalogue → 0 trades fetched →
      force/skip RED. Fix EITHER by (a) ordering the smoke so the IS force leg (which now populates the `-test-`
      catalogue — 182 objects proven tick 22) runs before the MTDS `trades` leg AND making the adapter's catalogue read
      `IS_TEST_RUN`-aware (`deployment_env="test"`), OR (b) accepting the prod-catalogue read as canonical (arguably
      more correct) and marking the `-test-` trades universe as prod-catalogue-sourced. NOT a data-correctness bug. Then
      re-run both skills for a formal all-green Phase-D. (repos: market-tick-data-service)
- [ ] [DATA] P0. **MVP backfill readiness gate** — only after A–D green: run the prediction MVP backfills and verify
      manifest-counted canonical rows for each MVP cell (Polymarket + Kalshi × trades + book_snapshot_5, CQG cluster).

## Progress Log

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase D section verbatim (8 todos total: 5 done / 3 open at split time). See the parent's Progress Log
  (ticks 10, 15, and especially 19-25 — the smoke-RED triage, Class A/B/C fixes, and the IS 0/14→11/14 re-run) for the
  full session-by-session history of what is already shipped here, and for why formal all-green is not yet cited (SPOT
  flakiness + a canonical-read residual + the MTDS `trades` `-test-` catalogue-gating follow-up, per tick 25). Future
  work on this plan logs new entries below.
