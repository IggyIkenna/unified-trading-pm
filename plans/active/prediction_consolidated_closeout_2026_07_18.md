---
doc_type: plan
title:
  Prediction consolidated close-out — one-pass code→migrations→coverage→smoke-test to MVP-backfill-ready (+ football
  cross-venue arb enablement)
summary:
  Single coordination plan that AGGREGATES (references, does not duplicate) every open prediction + prediction-touching
  IS/MTDS plan and issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md and
  tradfi_consolidated_closeout_2026_07_18.md — Phase A get ALL the code ready (writers live+batch, migration scripts,
  adapters, fixture-attribute writers), Phase B run the migrations (manifest/catalogue/CQG canonicalisation + backfill),
  Phase C data-status + honest-coverage (RE-ADD the removed dimensions-enumeration view + enumeration-driven canonical
  dedupe audit), Phase D re-smoke-test the backfills with data-pipeline-check-mtds and data-pipeline-check-is ADAPTED to
  prediction against -test- buckets — so prediction is verified complete and ready for the MVP backfills. Adds Phase E —
  the originating operator ask — football (soccer) cross-venue arb enablement — thread the canonical API-Football
  fixture id (af_fixture_id / build_fixture_id string) onto Polymarket AND Kalshi soccer markets as additive attributes,
  drive the join off the fixtures parquet OR name-parsing with robust alias resolution to a ~0% team-name gap (close the
  South-American alias hole + build a Kalshi soccer team registry), and unify the two currently-disconnected arb paths
  (features-service Kalshi↔Polymarket kernel + the e2e bookmaker/Betfair scanner) onto that shared fixture identity so
  live-odds-vs-Polymarket-vs-Kalshi arb becomes possible on a canonical basis.
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
tags:
  [
    prediction,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    manifest,
    honest-coverage,
    backfill,
    mvp,
    cross-venue-arb,
    sports-fixtures,
  ]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md,
    /plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    /plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Operator, 2026-07-18 — asked whether we have canonical football fixture ids linking sports→prediction such that we can
  arb football live-odds-API vs Polymarket vs Kalshi, and whether the question groups are canonical. Finding — the
  fixture side is canonical (af_fixture_id / build_fixture_id) and joined to live bookmaker odds (~66% match); the
  question groups are canonical as a cross-venue THEMATIC label (canonical_question_group) but NOT keyed to the fixture
  id — Polymarket soccer computes the build_fixture_id string, Kalshi carries nothing, and the two arb code paths are
  disconnected. Operator then directed a single consolidated prediction close-out mirroring the cefi + tradfi ones that
  aggregates ALL prediction IS/MTDS plans+issues into one pass, ADDS the fixture-id threading + ~0% alias matching +
  arb-path unification, RE-ADDS the removed data-status dimensions-enumeration view and bakes an enumeration-driven
  canonical/dedupe audit into the migration (single source of truth), and re-smoke-tests prediction the same way cefi +
  tradfi are, using -test- buckets via data-pipeline-check-is / data-pipeline-check-mtds scoped to prediction shards for
  IS and MTDS. Authored slot-2 from a 6-agent read-only research pass; tab-2 unified-trading-pm was first synced from a
  stale June-12 HEAD up to origin/live-defi-rollout 6c4787972 so this is authored against the current corpus.
---

# Prediction consolidated close-out — one pass to MVP-backfill-ready (+ football arb)

> **Purpose.** ONE place that aggregates every open prediction + prediction-touching IS/MTDS plan/issue into a single
> ordered pass. This plan **references** the source docs; it does not duplicate them. Close a track by closing its
> source doc(s), then tick it here. Mirrors `cefi_consolidated_closeout_2026_07_18.md` and
> `tradfi_consolidated_closeout_2026_07_18.md`; ordered per the operator's directive: **Phase A code → Phase B
> migrations → Phase C data-status/honest-coverage → Phase D re-smoke-test → MVP-backfill-ready**, then **Phase E** the
> originating football cross-venue arb enablement (gated on B+D). Two identity systems must be kept straight throughout:
> **`canonical_question_group` (CQG)** = a venue-agnostic THEMATIC family label (`SPORTS_EPL_MATCH`,
> `BTC_UP_DOWN_DAILY`) shared across Polymarket+Kalshi by design; **`af_fixture_id` / `build_fixture_id`** = the
> canonical API-Football fixture identity. They are separate today; Phase E is where a prediction soccer market gains a
> fixture link.

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 1488 lines and forked 5 ways**, per the operator-approved split in
> `/plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 22: "4-way split along the plan's own Phase A-E
> boundaries"). Every todo and every Progress Log line was moved **verbatim** to its destination — nothing was
> summarized, rewritten, or silently dropped.
>
> | Child doc                                                                                                                                                                | Carries                                                                                      |
> | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
> | [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md)                                                               | Phase A (writers/adapters/migration-scripts) + Phase B (run the migrations) residual todos   |
> | [`prediction_phase_c_data_status_ui_2026_07_24.md`](/plans/active/prediction_phase_c_data_status_ui_2026_07_24.md)                                                       | Phase C — data-status + honest-coverage                                                      |
> | [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`](/plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)                                 | Phase D — re-smoke-test the backfills, all shards                                            |
> | [`prediction_phase_e_football_arb_live_2026_07_24.md`](/plans/active/prediction_phase_e_football_arb_live_2026_07_24.md)                                                 | Phase E — football cross-venue arb enablement (depends_on-gated on B+D per the original ask) |
> | [`prediction_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/prediction_consolidated_closeout_history_2026_07_18.md) (archived, `status: complete`) | The full chronological Progress Log (autonomous ticks 1-31, ~917 lines, verbatim)            |
>
> **Retained here**: the Ground-truth verdict + MVP universe (foundational context every Phase depends on), the Codex
> SSOTs + aggregated source-doc index, the still-genuinely-open "Deferred work after 2026-07-18" items (blocked on
> shared-file drain windows, not stale), and a condensed pointer replacing the full tick-by-tick Progress Log.

## Ground-truth verdict (from the folded issues — RE-VERIFY live before migrating, per Phase A0)

Authored from the folded plans/issues; **A0 (autonomous tick 1, 2026-07-18) has since re-measured prod live** — rows
marked "A0 live read" carry the measured correction (see Progress Log § A0). What the docs + A0 establish:

| Surface                                   | Canonical / linked?                                                          | Reality (cited source doc)                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CQG cluster atom in the live manifest     | **present at `captured`: 17,352 rows** — CORRECTED 2026-07-18 (A0 live read) | A0 measured 80,068 CQG bundle rows (captured 17,352 / empty_confirmed 60,286 / expected_unattempted 2,421 / attempted_failed 9), 81 distinct canonical CQG values — this SUPERSEDES the folded issue's "ZERO at captured" claim; the phantom wipe is fixed or intermittent. **Re-check** `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` status before assuming a wipe (Phase-B item downgraded to verify-not-fix) |
| Prediction capture liveness               | **was dead 07-01→07-06**                                                     | capture-outage remediation in flight; KALSHI/POLYMARKET-PERP adapters hit the wrong Kalshi host → **fake PERPETUAL contaminated cefi (25,473 rows)** (`prediction_capture_incident_remediation_2026_07_06.md`)                                                                                                                                                                                                                            |
| MTDS prediction `-test-` bucket isolation | **MISSING (writes to PROD)**                                                 | `_test_bucket("prediction")` has no `-test-` sibling and falls back to the PROD `market-data-tick-prediction` bucket (`market-tick-data-service/scripts/pipeline_e2e_check.py:434-450`) — a prediction force/skip leg would write to PROD, breaking the test-bucket-only invariant cefi/tradfi enjoy                                                                                                                                      |
| Instrument-id canonical shape             | **partial**                                                                  | adapter `underlying` from `classify_*_to_canonical_group` + `canonical_instrument_id` from cross_venue_mapping are 4/8 done (`prediction_canonical_identity_migration_2026_07_08.md`)                                                                                                                                                                                                                                                     |
| Football fixture ↔ live bookmaker odds    | **joined, ~66%**                                                             | odds ticks carry `af_fixture_id` + `af_fixture_match_status`; ~66% fixture-level match, gap = South-American team-alias hole, not a join bug (`instruments-service/docs/SPORTS_INSTRUMENTS.md`)                                                                                                                                                                                                                                           |
| Football fixture ↔ Polymarket market      | **string bridge only**                                                       | Polymarket soccer computes the same `build_fixture_id()` string (`LEAGUE:HOME_v_AWAY:YYYYMMDD`) as the sports asset group (`instruments-service/.../reference_data/adapters/prediction/polymarket/parsing.py::_build_sports_id`) — the STRING, not the numeric `af_fixture_id`                                                                                                                                                            |
| Football fixture ↔ Kalshi market          | **NONE**                                                                     | Kalshi titles are city-level ("Seattle vs Cleveland") with no team registry → no fixture id at all; per-venue Kalshi↔Polymarket sports pairing needs a title-map the schema doesn't persist → honestly absent                                                                                                                                                                                                                             |
| Cross-venue arb code                      | **two disconnected paths**                                                   | features-service `cross_venue_arb_detector` (Kalshi↔Polymarket, crypto-oriented in practice) + e2e `live_arb_scanner.py` (bookmakers+Betfair+Polymarket, NO Kalshi, prototype); neither keys on `af_fixture_id`                                                                                                                                                                                                                           |

**Conclusion**: prediction is NOT MVP-backfill-ready — the CQG cluster atom is being wiped from the manifest, capture
only just recovered, MTDS prediction has no test-bucket isolation, and the football fixture identity that would enable
live-odds-vs-Polymarket-vs-Kalshi arb is threaded onto Polymarket-as-a-string only and onto Kalshi not at all. This plan
scopes the full end-to-end.

### Shard atom for prediction (SSOT-canonical — key is `canonical_question_group`, NOT `(instrument_id OR underlying)`)

The cross-AG shard-atom frame
(`pipeline_mode · date · asset_group · venue · [chain] · instrument_type · data_type · (instrument_id OR underlying) · [quote · margin] · source`)
applies to prediction on every axis EXCEPT the key column. Per the SSOT
(`/codex/02-data/availability-manifest-and-data-status.md:57-60`) the prediction atom is
`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` — keyed
on **`canonical_question_group`**, which is neither a per-market `instrument_id` nor `underlying`. Two grains, kept
straight:

- **Manifest/shard grain** = a MANIFEST-ONLY bundle (`data_type=prediction_canonical_question_group`) keyed on
  `canonical_question_group` (`BTC_UP_DOWN_DAILY`, `SPORTS_EPL_MATCH`), re-computed at rebuild. `underlying` is a
  ROW-LEVEL display column here, NOT the key — drop `underlying` as a key axis for prediction.
- **Raw object grain** = per-CID: raw `trades` / `book_snapshot_5` objects stay per-market (`instrument_id` = Polymarket
  condition_id / Kalshi ticker) — the per-market rows INSIDE the bundle.

Corollaries the generic frame misses for prediction: `[chain]` absent; `[quote · margin]` present only for KALSHI-PERP /
POLYMARKET-PERP; **IS side collapses to `venue → dates`** (no data_type axis — the instruments parquet IS the metadata);
MTDS drilldown is **CQG-led** — `venue → canonical_question_group → data_type → date`
(`/codex/02-data/data-status-drilldown-hierarchy.md:42`), i.e. CQG sits ABOVE data_type (opposite ordering to the flat
atom). Representative rows:

| shard (venue · data_type · type)                                       | key                                                  | notes                                                                                                        |
| ---------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| POLYMARKET · `prediction_canonical_question_group` · prediction_market | `canonical_question_group` (e.g. `SPORTS_EPL_MATCH`) | manifest-only bundle; per-market rows carry CID `instrument_id` + `underlying` + `build_fixture_id` (soccer) |
| KALSHI · `trades` · prediction_market                                  | per-CID `instrument_id` (market ticker)              | flat per-market raw object                                                                                   |

**This is the root of the Phase-B CQG-wipe**: the phantom reconciler treats prediction as if keyed on a per-object
`instrument_id` instead of the `(canonical_question_group, day)` bundle, so it wipes the bundle rows. A0/A2/B and the
Phase-D verify gate MUST assert the atom key is `canonical_question_group` (bundle) / per-CID `instrument_id` (raw),
never `underlying`.

## MVP universe (the Phase-D / Phase-E readiness target)

- **Venues**: POLYMARKET + KALSHI (`VENUES_BY_ASSET_GROUP["prediction"]`).
- **Data-types (MVP)**: `trades` + `book_snapshot_5` (the depth/orderbook grain — top-5 CLOB ladder; there is no
  separate `quotes`/`orderbook` type) at the market grain; `prediction_canonical_question_group` at the cluster grain;
  `market_lifecycle` at the market-id grain. Market groups: crypto, politics, sports.
- **Football-arb slice (Phase E)**: the Kalshi × Polymarket football-league overlap — Polymarket
  `POLYMARKET_PREDICTION_LEAGUES` (23 football leagues) ∩ Kalshi `KALSHI_SPORTS_TICKER_PREFIXES` (6 football: EPL,
  Bundesliga, La Liga, Serie A, Ligue 1, Champions League) against the 33 API-Football Prediction leagues + ~20
  bookmakers via the Odds API. Start where all three overlap (EPL, top-5 European leagues).

Everything below is scoped so these cells are captured, canonical, honestly-covered, smoke-tested green, and (Phase E)
fixture-linked before MVP backfill.

---

## Phases A-E — forked out (see Split notice above)

> All 5 phase bodies (writers/adapters/migrations/data-status/smoke-test/football-arb) now live in the 4 child plans
> listed above. This parent keeps only the ground-truth context, the aggregated index, and still-open
> cross-phase-blocked items (below) that don't cleanly belong to one child.

## Codex SSOTs (read before touching a phase)

`/codex/02-data/prediction-data-types-catalog.md`, `/codex/02-data/prediction-schema-paths.md`,
`/codex/02-data/prediction-perps-sourcing.md`, `/codex/02-data/prediction-settlement-availability-convention.md`,
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/data-status-drilldown.md`,
`/codex/02-data/data-status-drilldown-hierarchy.md`, `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`,
`/codex/02-data/venue-availability.md`, `/codex/02-data/honest-absence-downstream-handling.md`,
`/codex/04-architecture/prediction-batch-live.md`, `/codex/04-architecture/cross-venue-prediction-arb-detection.md`,
`/codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md`,
`/codex/09-strategy/operational/prediction-markets-codification-gaps.md`, `/codex/01-domain/sports-instruments.md`,
`/codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md`. Plus (Phase E odds/fixture side, out-of-repo):
`instruments-service/docs/SPORTS_INSTRUMENTS.md`.

## Aggregated source docs (referenced, not duplicated)

- **Capture / correctness**: `prediction_capture_incident_remediation_2026_07_06.md`,
  `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
  `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`,
  `issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md` (resolved, 1 residual — cross-link).
- **Manifest / CQG / phantom**: `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`,
  `issues/phantom_captures_prediction_2026_06_28.md`,
  `issues/mtds_prediction_migration_connection_pool_hardening_2026_07_10.md` (resolved residual),
  `issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md` (done-evidence),
  `issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md` (done-evidence).
- **Canonicalisation / data-completion**: `data_completion_prediction_2026_07_15.md` (primary open data track),
  `prediction_canonical_identity_migration_2026_07_08.md`.
- **Venue-perps / CLOB depth**: split + archived 2026-07-24 (was
  `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`) into
  `prediction_perps_kalshi_polymarket_parked_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`,
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md`.
- **UI / bucket**: `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`.
- **ML / arb (downstream, gated)**: `predictions_ml_walk_forward_and_arb_2026_06_20.md`.
- **Cross-cutting (shared w/ sports)**: `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`; sports feeder
  side lives in `sports_master` (fixtures/odds that Phase E consumes) — cross-link, not owned here.
- **Cross-asset arb (separate, archived/tradfi)**: `archive/2026_05/cme_polymarket_arb_2026_05_08.md` (CME↔Polymarket).
- **Skills / engine**: `data_pipeline_e2e_check_2026_07_10.md` + the `data-pipeline-check-mtds` /
  `data-pipeline-check-is` skills.
- **Parent epic (stale — see Progress Log)**: `epics/predictions_master.md`.

- **Additional cross-cutting / issue-doc coverage (2026-07-24 index enrichment)**:
  `canonical_id_builder_retrofit_checklist_2026_07_08.md`, `candle_canonical_path_migration_execution_2026_07_24.md`,
  `data_pipeline_check_mdps_features_2026_07_20.md`, `is_daily_enum_capture_heal_2026_07_07.md`,
  `mdps_features_reduced_artifact_tracker_2026_06_28.md`, `mtds_available_at_cross_asset_backfill_2026_07_13.md`,
  `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`,
  `issues/candle_feature_canonical_path_divergence_2026_07_20.md`,
  `issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`,
  `issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`,
  `issues/estate_orphan_assessment_2026_07_21.md`, `issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`,
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`,
  `issues/instrument_availability_hive_canonicalisation_2026_07_21.md`,
  `issues/instrument_id_format_canonicalization_2026_07_08.md`,
  `issues/instruments_docs_audit_outstanding_items_2026_07_08.md`,
  `issues/instruments_remaining_work_audit_2026_07_10.md`,
  `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`,
  `issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`,
  `issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
  `issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`,
  `issues/migration_orphan_sweep_performance_decay_2026_07_22.md`,
  `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`,
  `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
  `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`,
  `issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`.
- **Sports-tagged, prediction-relevant (shared infra/scope with sports_master)**:
  `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`,
  `sports_group_c_execution_backtest_harness_2026_07_21.md`,
  `sports_odds_feature_naming_canonicalization_2026_07_21.md`,
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md`,
  `issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`,
  `issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`.

## Deferred work after 2026-07-18 (HELD — unblock when the concurrent tradfi/cefi migrations free the shared files / a drain window opens)

The autonomous slot-2 pass (operator: "prediction-specific files only") shipped every prediction-specific-file-safe
unit; the items below each require a SHARED file another slot is actively migrating, an irreversible prod-migration
drain window, or an operator decision. They are ordered, not abandoned — each names its exact blocker.

- **A4 column materialization** (shared): add the 6 fixture-match fields to UAC `InstrumentRecord`; IS
  `process_write._records_to_dataframe` join (~6-line extension of the `clob_token_ids` block reading
  `fixture_match_for_instrument_key`); MTDS prediction-tick schema. The resolver + side-table stamping already shipped
  (`is@85988ade`); this turns it into real parquet/manifest columns.
- **E2 alias additions** (shared): add the missing Kalshi soccer team aliases (E2's worklist) to
  `unified_api_contracts.external.api_football.team_mappings`, plus the South-American club aliases for the odds-side
  ~66%→~100% — to reach the operator's ~0% gap.
- **A2 residual** (shared / other repo): identity-migration todo 2 only (`prod/catalog.parquet` regen — prod-GCS run,
  gated on the shared canonical migration so it doesn't bake transitional ids) — corrected 2026-07-21, plan-reconcile:
  todos 7 (`gcs_paths.py` bucket-abbreviation flip) and 8 (MDPS UAC-pin verify) were resolved 2026-07-19 (see the A2
  todo above), this residual list was never trimmed to match.
- **CQG residual §5** (shared + operator decision): add `pipeline_mode=live_*` prefix shapes to UAC `possible_manifest`
  — needs the BATCH-satisfied-by-LIVE-evidence semantics call (A: union batch+live [REC]; B: batch-only).
- **Phase-B prod migration** (drain window): the enumeration-driven manifest canonicalisation (`prediction_trades`→
  `trades`, `instrument_type`→`PREDICTION_MARKET` 11.70%→100%, empty `source`, `base_asset` whitespace) + the
  fixture-attr backfill — needs a pre-migration VM drain the concurrent tradfi/cefi migrations currently occupy.
- **Phase C/D/E remainders** gated on the above (data-status dimensions view is partly already-served by
  `catalogue-filter-options`; smoke-test needs the MTDS prediction `-test-` bucket; arb-path unification needs the
  materialized columns + E2 resolution).

## Progress Log — condensed (2026-07-24, replaces the pre-split ~917-line tick-by-tick log)

> **The full tick-by-tick history was NOT deleted** — it lives verbatim in
> [`prediction_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/prediction_consolidated_closeout_history_2026_07_18.md)
> (autonomous ticks 1-31, 2026-07-18 through 2026-07-20). Every genuinely-open item that log surfaced was cross-checked
> against the 4 Phase children and the "Deferred work after 2026-07-18" section above — nothing was silently dropped.

- **2026-07-18** — Plan authored, folding prior prediction plans/issues; Phase A-E structure set; football arb (Phase E)
  added as the originating operator ask.
- **2026-07-18/19** — Phase A writers/adapters shipped incrementally (autonomous ticks); fixture-attribute resolver +
  side-table stamping shipped (`is@85988ade`).
- **2026-07-19/20** — 3-venue paper arb proof landed end-to-end (Kalshi/Polymarket/Betfair, `execution@5ed8a029`);
  cross-repo seam e2e proof shipped (`e2e@7665a027`); the autonomous slot-2 pass shipped every prediction-specific-
  file-safe unit, leaving only shared-file/drain-window/operator-decision items open (the "Deferred work after
  2026-07-18" section above).
- **2026-07-24** — Plan line-cap remediation: 4 Phase children extracted (A+B, C, D, E), full Progress Log archived
  verbatim to `prediction_consolidated_closeout_history_2026_07_18.md`, this parent condensed to a lean coordination
  index with an enriched Aggregated source docs index covering every active prediction + prediction-touching plan/issue.
