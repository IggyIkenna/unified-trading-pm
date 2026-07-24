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
umbrella: true
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

**Per-child open-todo snapshot (2026-07-24 — so the split itself is AO-legible without opening each child):**

- [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md) — **9
  open** (all P0/P1, no P2/P3). Top: [BACKEND] P0. Finish the prediction capture-incident remediation — harden the
  capture path; [BACKEND] P0. Kill the dead Kalshi `trading-api.kalshi.com` host reintroduced into the smoke matrix.
- [`prediction_phase_c_data_status_ui_2026_07_24.md`](/plans/active/prediction_phase_c_data_status_ui_2026_07_24.md) —
  **4 open**. Top P0: [UI] P0. RE-ADD the data-status "dimensions enumeration" view to deployment-ui/api.
- [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`](/plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)
  — **3 open** (all P0). Top: [DATA] P0. Run `data-pipeline-check-is` for prediction-only, all shards, post-migration;
  [DATA] P0. Run `data-pipeline-check-mtds` for prediction-only, all shards, post-migration.
- [`prediction_phase_e_football_arb_live_2026_07_24.md`](/plans/active/prediction_phase_e_football_arb_live_2026_07_24.md)
  — **3 open** (all P1, no P0 yet). Top: [BACKEND] P1. Verified end-to-end fixture link on Polymarket + Kalshi soccer;
  [BACKEND] P1. Wire the arb engine to CONSUME `af_fixture_id`.
- [`prediction_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/prediction_consolidated_closeout_history_2026_07_18.md)
  (archived) — **0 open** — VERIFIED: `status: complete`, 995 lines, zero unchecked checkboxes; pure verbatim record.

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

> Format: path (real repo-root link) → its currently-OPEN todos only, one line each (`[TAG] P<N>.` prefix preserved,
> evidence/prose dropped). Docs with 0 open todos say so explicitly. >8-open docs list every P0/P1 in full and cap P2/P3
> with a `+N more` marker — nothing is silently dropped. Re-verified 2026-07-24 against the live corpus.

- **Capture / correctness**:
  - [`plans/active/prediction_capture_incident_remediation_2026_07_06.md`](/plans/active/prediction_capture_incident_remediation_2026_07_06.md)
    (9 open total)
    - **[VERIFY] P0.** Demo dry-run: returned tickers are genuine perps (`BTC-PERPETUAL` shape, `contract_type` present)
    - **[CODE] P1.** Make the perp base URL config-driven — `KALSHI_PERP_ENV=demo|prod` (via `UnifiedCloudConfig`)
    - **[CODE] P1.** Extract the RSA-PSS signing that ALREADY EXISTS in `adapters/prediction/kalshi.py`
    - **[CODE] P1.** Rewrite `KalshiPerpReferenceDataAdapter.get_instruments` to hit `…/trade-api/v2/markets/margin`
    - **[RESEARCH] P1.** `docs.polymarket.com` perps API — find the markets-listing endpoint + auth (beta-gated)
    - **[CODE] P1.** Repoint `polymarket_perp` against Polymarket's perps API (demo/testnet if available)
    - **[VERIFY] P1.** Pin the prediction-store event-capture gap (the real question the purge-vs-move decision needs)
    - +2 more (P2/P3, one DESCOPED-NOT-MVP) — see file for the rest
  - [`plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`](/plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md)
    - **[VERIFY] P2.** Post-fix: re-measure prediction attempted/captured trajectory on a sampled window
    - **[INFRA] P1** [BLOCKED-OPERATOR-DECISION]. Launch the historical prediction re-backfill under the widened
      catalogue
  - [`plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`](/plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`](/plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md)
    (resolved, 1 residual — cross-link; note: archived location, not `plans/active/issues/`)
    - **[CODE] P2.** Durable fix: bound memory in the prediction CLOB universe scan (chunked pagination → incremental)
- **Manifest / CQG / phantom**:
  - [`plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`](/plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/phantom_captures_prediction_2026_06_28.md`](/plans/active/issues/phantom_captures_prediction_2026_06_28.md)
    - **[CODE] P2.** Fix MTDS prediction writer to use `empty_confirmed` for 0-activity contracts (pre-event future)
  - [`plans/archive/issues/mtds_prediction_migration_connection_pool_hardening_2026_07_10.md`](/plans/archive/issues/mtds_prediction_migration_connection_pool_hardening_2026_07_10.md)
    (resolved residual; archived location) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md`](/plans/archive/issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md)
    (done-evidence; archived location) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md`](/plans/archive/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md)
    (done-evidence; archived location) — 0 open todos (closed/archived/record-only)
- **Canonicalisation / data-completion**:
  - [`plans/active/data_completion_prediction_2026_07_15.md`](/plans/active/data_completion_prediction_2026_07_15.md)
    (primary open data track; 23 open total)
    - **[DATA] P0.** C0 ONE bundled walk: copy legacy `raw_tick_data/` + `processed_candles/` objects → canonical
      `pred-prd`
    - **[DATA] P0.** C-pipeline_mode RIDER: the `pipeline_mode=` partition for prediction lands in THIS walk
    - **[DATA] P0.** Post-walk: re-run the `(date,venue,data_type)` comparison → legacy-only CELLS = 0
    - **[CODE] P0.** Ship the MTDS+UAC live-writer bundle change (spec above) TOGETHER WITH the MDPS companion change
    - **[DATA] P0.** Per-AG (cefi/tradfi/prediction): Phase-0 layout audit → re-tarball+pin SHAs → G1 full-corpus
    - **[DATA] P1.** C-source RIDER: stamp `source` = the data-source API (`polymarket_clob` / `polymarket_gamma_api`)
    - **[DATA] P1.** E6 CF-7 relabel — CF-7 NOW BAKED INTO THE MIGRATOR (mtds@4b311c93)
    - **[DATA] P1.** Build the historical rollup migration script (reuse `rebuild_prediction_manifest.py` logic)
    - **[DATA] P1.** Pre-migration drain (stop prediction writers/crons per the HARD RULE) → snapshot `_index`
    - **[DATA] P1.** Post-verify: CF-audit the pred surface (row-parity per (day,venue,cqg) sampled; manifest
      cross-check)
    - **[CODE] P1.** FLAG-3 (deployment-api) — DECIDED (operator 2026-06-02): env-tier the `*-store` buckets
    - **[DATA] P1.** Downstream service C-walks (MDPS rides the AG tick walk; features/strategy/execution)
    - **[CODE] P1.** FLAG 3 (bucket-SSOT, deployment-api) — DECIDED (operator 2026-06-02): env-tier the `*-store`
      buckets
    - **[DATA] P1.** MDPS C-walk: bundle any `processed_candles/` debt into the SAME AG tick-bucket walk
    - **[DATA] P1.** features C-walk: ONE bundled walk per `features-*-{ag}` index for any P0 debt
    - **[DATA] P1.** strategy C-walk: ONE bundled walk for strategy output `_index` debt
    - **[DATA] P1.** execution C-walk: ONE bundled walk for execution-record/ledger `_index` debt
    - **[DATA] P1.** Post-walk per service: re-run the P0 CF audit → all applicable CF GREEN (data-state)
    - +5 more (3×P2, 2×P3) — see file for the rest
  - [`plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md`](/plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md)
    (archived location, `status: active` retained on the doc itself)
    - **[DATA] P1.** Regenerate/backfill `prod/catalog.parquet` for Prediction after the `raw_symbol`/`base_asset` fix
- **Venue-perps / CLOB depth**: split + archived 2026-07-24 (was
  `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`) into:
  - [`plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`](/plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md)
    - **[SCRIPT] P1.** Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet — CONFIRMED)
  - [`plans/active/prediction_live_clob_depth_capture_2026_07_24.md`](/plans/active/prediction_live_clob_depth_capture_2026_07_24.md)
    - **[DATA] P2.** Verify END-TO-END depth-history retention — the RAW live book store is rolling-latest-window
  - [`plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md`](/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md)
    (8 open total — listed in full, not over the >8 cap threshold)
    - **[SCRIPT] P0.** Populate POLYMARKET instrument lifecycle start/end + bound manifest empty-emission to it
    - **[SCRIPT] P1.** e2e-testing/instruments-service — series-scoped historical backfill — DEEP CORPUS DONE
    - **[OPS] P2.** Tarball-overwrite race: a concurrent fleet `create-code-tarballs` (from a clone behind LDR) clobbers
    - **[UAC] P2.** Politics/geo cross-venue canonicalization — Kalshi Politics (2049 series: electoral-college)
    - **[DESIGN] P2.** Per-instrument same-game/same-settlement arb PAIRING within a shared cqg group
    - **[DATA] P2.** Residual lowercase `venue=kalshi` + blank/UNKNOWN venue rows in the prediction `_index` manifest
    - **[SCRIPT] P2.** cqg partition-completeness — recent-window catalogue re-enumeration
    - **[DATA] P3.** 1,454 prediction `_index` rows still at schema v4 (vs 192,713 at v9; DISCOVERED 2026-06-23)
- **UI / bucket**:
  - [`plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md`](/plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md)
    - [VERIFY]**[UI] P0.** After the writer + UI ship: re-walk the deployment-ui prediction panel; POLYMARKET drill-down
    - **[SCRIPT] P1.** Phase 5 — canonical-groups backfill (30+ groups beyond the initial 9). Full list in the archived
    - **[SCRIPT] P2.** Prediction sentinel fan-out for `prediction_canonical_question_group` empty rows
- **ML / arb (downstream, gated)**:
  - [`plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md`](/plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md)
    - **[SCRIPT] P0.** Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix (BLOCKED-ON)
    - **[ANALYSIS] P0.** Run the acceptance-metrics computation above against the real walk-forward output (BLOCKED-ON)
    - **[GATE] P0.** Block Group F until walk-forward AUC ≥ 0.55 AND calibration error ≤ 5% (ACTIVE GATE)
    - **[ANALYSIS] P1.** Persist model + metrics to the ml-models registry; tag `model_family=sports_arb_v1`
    - **[AGENT] P1.** Predictions MTDS completion-% slice — per-(canonical_question_group, day) completion %
- **Cross-cutting (shared w/ sports)**:
  - [`plans/active/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/active/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    (resolved)
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run (next `0 1 * * *` UTC)
    - **[INFRA] P3.** Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`
  - sports feeder side lives in `sports_master` (fixtures/odds that Phase E consumes) — cross-link, not owned here.
- **Cross-asset arb (separate, archived/tradfi)**:
  - [`plans/archive/2026_05/cme_polymarket_arb_2026_05_08.md`](/plans/archive/2026_05/cme_polymarket_arb_2026_05_08.md)
    (CME↔Polymarket, `status: complete`) — 0 open todos (closed/archived/record-only)
- **Skills / engine**:
  - [`plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md`](/plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md)
    (archived location, `status: active` retained on the doc itself) — 0 open todos (closed/archived/record-only)
  - - the `data-pipeline-check-mtds` / `data-pipeline-check-is` skills (skill definitions, not plan files — no todos to
      track here).
- **Parent epic (stale — see Progress Log)**:
  - [`plans/epics/predictions_master.md`](/plans/epics/predictions_master.md) (38 open total — 24 P0 + 5 P1 + 9 untagged
    success-criteria checkboxes; frontmatter says `status: active` but this doc is functionally SUPERSEDED by the Phase
    A-E children + the aggregated docs above — the items below are UNVERIFIED against current reality, listed here only
    per the completeness rule)
    - **[SCRIPT] P0.** Replace POLYMARKET writer (`orchestrator.py:1990–1995`): old `data_type = <base_asset>` → new
    - **[SCRIPT] P0.** Reader migration: every callsite with `data_type=BTC|ETH|...` →
    - **[SCRIPT] P0.** Per-market lifecycle gating in feature compute: `LookaheadBiasError` extension
    - **[SCRIPT] P0.** Strategy-service prediction archetypes: archetype configs reference `canonical_question_group`
    - **[TEST] P0.** End-to-end smoke: 1 canonical_group (`BTC_UP_DOWN_HOURLY`) × 1 day; run feature compute + verify
    - **[SCRIPT] P0.** New script `mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` (in scripts/)
    - **[SCRIPT] P0.** Manifest reflip script `mtds_reflip_polymarket_per_base_asset.py`
    - **[SCRIPT] P0.** Old parquet deletion — only AFTER new parquets verified by hand-inspection (sample 10 random)
    - **[SCRIPT] P0.** Backfill any missing canonical_groups — markets in `conditionid_universe.csv` that classifier
      maps
    - **[SCRIPT] P0.** Confirm `migrate_polymarket_canonical.py` (MTDS) ran for all targets; afterwards delete legacy
    - **[SCRIPT] P0.** Every reconciler wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)`
    - **[SCRIPT] P0.** Each reconciler supports `--max-flips-per-run=10000` halt safety; operator confirms first 10k
    - **[SCRIPT] P0.** CSV audit at `gs://{pid}-reconciler-audit/{run_id}/`
    - **[SCRIPT] P0.** Predictions asset_group panel — drill-down shape: `(venue, canonical_question_group, day)`
    - **[SCRIPT] P0.** Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix (gated on
      sports)
    - **[ANALYSIS] P0.** Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per consolidated
      plan
    - **[SCRIPT] P0.** Training-config sanity check: feature columns match FSS schema, label leakage absent
    - **[GATE] P0.** Block Group F until walk-forward AUC ≥ 0.55 and calibration error ≤ 5% (ACTIVE GATE)
    - **[SCRIPT] P0.** Synthetic `OTHER` canonical-question-group bucket — the classifier MUST map every Polymarket
    - **[VERIFY] P0.** Phase 1 timeline check against 2026-05-23 master deadline: 14/37 done (38%) as of 2026-05-07
    - **[VERIFY] P0.** After Phase 1 ships: re-walk deployment-ui prediction panel; POLYMARKET drill-down renders
    - **[SCRIPT] P0.** features per-market LookaheadBiasError check — per CLAUDE.md prediction-lifecycle rule
    - **[SCRIPT] P0.** deployment-ui 3-level hierarchy + per-shard parquet download — today MARKETS list is flat
    - **[SCRIPT] P0.** Lifecycle-bounded `available_at` stamping for Polymarket + Kalshi adapters
    - **[ANALYSIS] P1.** Persist model + metrics to ml-models registry; tag `model_family=sports_arb_v1`
    - **[AGENT] P1.** Per-(canonical_question_group, day) completion %: HOURLY = 24 expected/day, DAILY = 1, ELECTION =
      1
    - **[SCRIPT] P1.** Phase 5 — canonical-groups backfill (30+ groups beyond initial 9). Full list in archived issue
    - **[SCRIPT] P1.** Predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`. Per-canonical_question_group
      (line 818)
    - **[SCRIPT] P1.** Predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`. Per-canonical_question_group (line
      1000, duplicate of the 818 entry)
    - +9 more (untagged success-criteria checklist items, e.g. "Polymarket backtest runs end-to-end") — see file for the
      rest

**Additional cross-cutting / issue-doc coverage (2026-07-24 index enrichment)**:

- [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md)
  (9 open total)
  - **[DATA] P1.** Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string
  - **[DATA] P1.** Resolve the non-canonical TYPE-token question before retrofitting todo 1
  - **[DATA] P1.** Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters — Kalshi
  - +6 more (3×P2, 3×P3) — see file for the rest
- [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/active/candle_canonical_path_migration_execution_2026_07_24.md)
  (16 open total — all P0/P1, listed in full)
  - **[DATA] P0.** Rebuild code tarballs (`refresh_code_tarballs.sh`) for the 4 already-shipped repos
  - **[DATA] P0.** VERIFY on `-test-` via `/data-pipeline-check-mdps` (force+skip+canonical legs)
  - **[DATA] P0.** VERIFY readers dual-read correctly (features-service delta_one + volatility, unified-trading-api)
  - **[SCRIPT] P0.** Run the sanctioned Tier-2 spot-VM single-walk census (bounded in-session sampling already)
  - **[SCRIPT] P0.** Build the migration executor (P5): clone
  - **[SCRIPT] P0.** Implement the path transform in the executor: backward-add `instrument_type=` via
  - **[SCRIPT] P0.** Implement DEDUP in the executor for the split-brain candle layout (same object present under both)
  - **[SCRIPT] P0.** Implement PURGE of empty-stem objects (`venue={V}/.parquet` with no leaf id, ~0.6-0.8% defect)
  - **[SCRIPT] P0.** Implement QUARANTINE (never guess) for unresolvable legacy TradFi `E1AF0_*_migrated_*` leaf ids
  - **[SCRIPT] P0.** Wire manifest re-record to the SOURCE-keyed row (via `record_captured`, path-independent) into
  - **[SCRIPT] P0.** Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum before any prod
  - **[DATA] P0.** Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch (target)
  - **[DATA] P0.** P7 per-AG SPOT migration apply, in order defi→prediction→cefi→tradfi (tradfi last)
  - **[DATA] P0.** P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle
  - **[DATA] P1.** P6 drain+snapshot: coordinate with the running `canonical-migration-cefi-wp*` raw_tick VMs
  - **[DATA] P1.** Root-cause + close the candle object↔manifest disconnect (6 degenerate MDPS manifest rows vs 20k+)
- [`plans/active/data_pipeline_check_mdps_features_2026_07_20.md`](/plans/active/data_pipeline_check_mdps_features_2026_07_20.md)
  (28 open total)
  - 8. **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-mdps` e2e: auto-select high-coverage day per AG
  - 9. **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-features` e2e: multi-day input window per family
  - 11. **[DATA] P0.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE existing
        candle/feature
  - 13. **[DATA] P0.** Produce concrete ETA to backfill all remaining DeFi MVP (from benchmark + remaining-shard count)
  - NEW todo. **[DATA] P0.** Verify whether MDPS `max_workers` (8 on e2-standard-8) actually OVERLAPS the GCS writes
  - NEW todo. **[DATA] P0.** Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe)
  - NEW todo. **[DATA] P0.** Run `/data-pipeline-check-mdps` across all relevant AGs NOT already in candles
  - NEW todo. **[DATA] P0.** Run `/data-pipeline-check-features` across ALL shards (8 families x valid AGs)
  - NEW todo. **[DATA] P0.** VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win
  - NEW todo. **[SCRIPT] P0.** Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`)
  - NEW todo. **[DATA] P0.** Audit every `read_availability_index` caller on defi for a missing column/filter projection
  - NEW todo. **[SCRIPT] P0.** Fix the shared seed context (per-call immutable value object + collision-proof
    frame-cache)
  - NEW todo. **[SCRIPT] P0.** Implement R1 (concurrent date-subprocesses) — the months->weeks lever that is SAFE today
  - NEW todo. **[DATA] P0.** Real-VM re-measure of end-to-end per-instrument-day rate against a PROD-sized index
  - 10. **[DATA] P1.** Steady-state benchmark VMs (250GB disk) per representative shard-type
  - 12. **[SCRIPT] P1.** Backfill-processing path (download→process→upload) code-ready + OPTIMIZED learning from cefi
  - 15. **[DATA] P1.** Full DeFi-MVP candle backfill on real infra — GATED
  - NEW todo. **[DOC] P1.** Correct `/codex/05-infrastructure/spot-vms-for-backfill.md`: the preemption signal was NOT
  - NEW todo. **[SCRIPT] P1.** Close residual risk 1 — make arg-required launchers relaunchable (features especially)
  - NEW todo. **[DATA] P1.** Blast radius: did any PAST prod MDPS run use max_workers>1 over a heterogeneous list
  - NEW todo. **[SCRIPT] P1.** Implement R1: bounded-concurrent `_run_date_as_subprocess` dispatch (the 2-week
    throughput)
  - +6 more (P2) — see file for the rest
- [`plans/active/is_daily_enum_capture_heal_2026_07_07.md`](/plans/active/is_daily_enum_capture_heal_2026_07_07.md)
  (`status: draft`)
  - **[CODE] P0.** Add `exc_info=True` to the UTL shard-isolation catch (`service_framework/_adapter.py`)
  - **[CODE] P0.** With the real traceback now visible, re-run `is-daily-enum-{prediction,sports}` and read the ACTUAL
  - **[VERIFY] P1.** Backfill the missed windows: prediction 07-01→07-06, sports 06-28→07-06
- [`plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md)
  (`status: draft`) — 0 open todos (closed/archived/record-only)
- [`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`](/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md)
  (9 open total)
  - **[OPERATOR] P0.** BLOCKED-OPERATOR-DECISION — coordinate a maintenance window with the operator for the prediction
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Snapshot the prediction canonical manifest index
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Apply `rebuild_prediction_manifest.py` (full date range)
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Resume the prediction consolidator cron; record the before/after
    fill-rate
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Snapshot the tradfi canonical manifest index and pause its consolidator
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Apply `rebuild_tradfi_manifest.py` (full date range)
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Resume the tradfi consolidator cron; record evidence in the Progress Log
  - +2 more (P2/P3) — see file for the rest
- [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
  - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
  - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers
  - **[DECISION] P2.** Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
- [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
  - 1. **[DATA] P1.** instruments-service: canonicalise the `instrument_availability` write to
  - 2. **[DATA] P1.** market-tick-data-service: rule on and fix the cefi chain tail — `partitioned_writer.py:291-293`
  - 3. **[DOCS] P2.** instruments-service + market-tick-data-service: correct the three in-repo comments that assert
  - 4. **[SCRIPT] P2.** unified-trading-pm: add a Phase-0 `-test-` assertion on the resolved WRITE bucket
  - 5. **[DOCS] P2.** unified-trading-pm: add an explicit "never pass `--allow-live-prod-writes`" prohibition
  - 6. **[DATA] P3.** instruments-service: decide whether `market_lifecycle` (`writers.py:495-501`) should
- [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - 7. **[DATA] P0.** Root-cause the object↔manifest disconnect (20,734 cefi candle objects on 2026-04-14 vs 6 MDPS)
  - 2. **[DATA] P1.** Corpus-wide count of zero-length-stem candle objects (`…/venue=*/.parquet`); purge or repair
  - 3. **[DATA] P1.** Canonicalise TradFi candle leaf ids (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`)
  - 9. **[DATA] P1.** Split-brain candle layout (addendum iii-a): the same cefi day (2026-05-23) holds BOTH
  - 19. **[SCRIPT] P2.** Fix `_copy_verify_delete()`'s retry-idempotency gap
  - 13. **[DATA] P3.** `ProvisionalTargetIndex` keys lack a bucket component, so the split-brain COUNT is off
  - 15. **[DOC] P3.** `unified-trading-library`'s `build_canonical_candle_path()` docstring example still shows
  - 16. **[SCRIPT] P3.** Investigate why `CEFI:DERIBIT:trades:24h`'s force-leg MEASURED classification shows
- [`plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`](/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md)
  - **[CODE] P1.** Add a falsifier test (mirroring `scripts/check_coverage_exclusions.py`'s pattern)
  - **[DATA] P1.** Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT)
  - **[DATA] P2.** Resolve the CME mismatch — `coverage_starts.py`'s 2010-01-01 carries `# TODO verify`
  - **[DATA] P2.** Resolve the POLYMARKET mismatch (2022-11-21 CLOB-launch vs 2025-03-14 first-actual-instrument)
  - **[DATA] P3.** Resolve the small 1-21 day DeFi protocol drifts (CURVE, UNISWAP_V2, UNISWAP_V4, BALANCER, LIDO)
  - **[DATA] P3.** Publish an explicit key-mapping table between `coverage_starts.py`'s bare venue/protocol keys
- [`plans/active/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`](/plans/active/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - 5. **[DATA] P0.** Read `unified-trading-library`'s manifest consolidator (`manifest_consolidator.py`)
  - 6. **[DATA] P0.** Check whether the round-2 remediation script
  - 7. **[DATA] P0.** Confirm whether a consolidation cycle has actually run since the 2026-07-23 remediation
  - 8. **[DATA] P0.** Once todos 5-7 pin the actual mechanism, re-run the remediation (or fix the consolidator input)
  - 1. **[DATA] P1.** Pin the true full count and composition — read the `instruments-store-sports` index
  - 2. **[BACKEND] P1.** Locate the writer — trace which job/uploader writes `asset_group=prediction` rows
  - 3. **[BACKEND] P1.** Fix the misattribution at the writer so a prediction shard's manifest row lands only
  - 4. **[DATA] P2.** Remediate the already-written bleed rows — decide whether to relocate them
- [`plans/active/issues/estate_orphan_assessment_2026_07_21.md`](/plans/active/issues/estate_orphan_assessment_2026_07_21.md)
  - 3. **[INFRA] P1.** Run the orphan sweep for defi / cefi / tradfi / prediction on a VM — deployment-service@f8e885f
  - 4. **[CODE] P2.** Make the manifest load resumable / streamed in `migration_orphan_sweep.py`
  - 5. **[CODE] P3.** `GcsEventSink` never `.shutdown()`s its background `ThreadPoolExecutor` (4 workers)
  - 6. **[CODE] P2.** Give `backfill_orphan_class_e.py --apply` a batched-incremental `record_cells()` call
- [`plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
  - **[INFRA] P1.** Decide + implement a default-to-yesterday date bridge for MTDS's batch CLI
- [`plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`](/plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md)
  (14 open total)
  - **[DESIGN] P1.** Fix the mockup's leaf model everywhere it still needs it (Finding 1) — CEFI/TRADFI/DEFI's
  - **[DESIGN] P1.** Design the CEFI instrument-definition parquet resharding (Finding 2, decided)
  - **[CODE] P1.** Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM (same CEFI instrument-definition parquet
    resharding design as the item above)
  - **[CODE] P1.** Pull the real per-instrument_type breakdown for DERIBIT live (the comparison built for this doc)
  - **[CODE] P1.** Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
  - **[CODE] P1.** Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis
  - **[VERIFY] P1.** Raw-parquet spot-check the 5 additional CeFi venues flagged by the pre-audit's registry read
  - **[CODE] P1.** Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split
  - +6 more (4×P2, 2×P3) — see file for the rest
- [`plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
  - 7. **[DATA] P1.** PROVE the fixed writers green on one real day (write + skip-if-fresh + manifest row)
  - 8. **[REVIEW] P1.** On writer ship, record the `instrument_availability` full-hive cutover date
- [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md)
  - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols) — real code is already correct
  - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (finding 4) — ASTER/PACIFICA
- [`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`](/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`](/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
  - 1. **[DATA] P0.** VERIFY the prod projection before sizing the win — is `_publish_emission_check` actually firing
  - 5. **[DATA] P0.** The 1.58 GB defi-prd index is its own P0 — audit every `read_availability_index` caller on defi
  - 6. **[DOC] P2.** Record in codex that the per-VM manifest flush is ALREADY debounced (50 entries/5.0s,
       `utl@6b6d53bd`)
- [`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`](/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - 3. **[SCRIPT] P1.** S1-c — `mdps-sports-<year>-<ts>` emitted by `launch-mdps-sharded-backfill.sh:206` but registered
  - 1. **[SCRIPT] P2.** S1-a — `launch-prediction-features-vm.sh` BROKEN (packages removed)
  - 2. **[SCRIPT] P2.** S1-b — `launch-mdps-features-live.sh` non-runnable (no dispatcher branch)
  - 4. **[SCRIPT] P3.** S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (lines 170-309 unreachable)
  - 5. **[SCRIPT] P3.** S2-b — delete the 8 stale `features_*_service` keys in `setup-data-pipeline-vm.sh`
  - 6. **[SCRIPT] P3.** S3-a — delete MDPS one-offs past `Delete-when` after verifying each condition
  - 7. **[SCRIPT] P3.** S3-c — repoint `features-service/scripts/sports/smoke_matrix.py` SSOT citations
  - 8. **[SCRIPT] P3.** S3-b — sports dual entrypoint (`python -m features_service.sports`)
- [`plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
  - 3. **[DATA] P1.** Assess blast radius on EXISTING candle data: any past MDPS run with `max_workers>1`
- [`plans/active/issues/migration_orphan_sweep_performance_decay_2026_07_22.md`](/plans/active/issues/migration_orphan_sweep_performance_decay_2026_07_22.md)
  - 7. **[CODE] P3.** Genuinely stream `_load_manifested_cells()`'s parquet read (row-group batches)
- [`plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`](/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md)
  - **[VERIFY] P1.** NEW (2026-07-14) — FLUID lending_indices silently returns 0 rows for ~18 months of its own declared
  - **[VERIFY] P1.** Root-cause the 273 mistagged DERIBIT/COMBO rows (open question #1) — not attempted this session
  - **[CODE] P2.** Update both drilldown mockups — not attempted this session (out of dispatched scope)
- [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`](/plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md)
  (dup ref — see Capture / correctness above for its 2 open todos)
- [`plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`](/plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
  — 0 open todos (closed/archived/record-only)

**Sports-tagged, prediction-relevant (shared infra/scope with sports_master)** — primary tracking: `sports_master` /
sports's own consolidated closeout plan; short digest only:

- [`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`](/plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)
  (8 open, all `[DESIGN] P3`) — top: define the decay-window STATISTIC precisely; define the WINDOW boundaries
  (signal-time → first-leg fill vs last-leg). +6 more — see file for the rest.
- [`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`](/plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md)
  (5 open, all `[BACKEND]/[DESIGN]/[SCRIPT] P3`) — top: add `run_sports_backtest(args, config, config_path) -> int`;
  wire a data source (reuse the Group-B fixture dataset). +3 more — see file for the rest.
- [`plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`](/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - **[DATA] P1.** NEW compute, not a rename: add per-bookmaker raw decimal-odds retention
  - **[DATA] P1.** Update `unified_api_contracts`'s `OddsFeaturesMixin`/`SportsFeatureVector` fields to the names chosen
  - **[DATA] P2.** Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS`
  - **[BACKEND] P2.** Close the silent-agnostic gap in `SportsFeatureLoaderMixin`
  - **[BACKEND] P2.** Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine` (`on_tick`'s)
  - **[BACKEND] P2.** Migrate the legacy `strategy_service/adapters/sports_feature_subscriber.py`
  - **[REVIEW] P3.** Once todos 2–6 land, write the FSS-output ↔ ml-service-input ↔ strategy-service-input parity test
  - **[REVIEW] P3.** Cross-reference this migration against whichever plan ends up doing the "wire sports end-to-end"
- [`plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`](/plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md)
  (6 open, all `[OPERATOR]/[INFRA]/[DATA]/[REVIEW] P3`) — top: decide whether to pursue a live sports-odds ingestion
  path at all (the structural blocker); once that's a yes, scope the MTDS live-odds connector. +4 more — see file.
- [`plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`](/plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`](/plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md)
  (resolved) — 0 open todos (closed/archived/record-only)

**Newly discovered (2026-07-24 completeness check via `grep -l '^asset_group:.*prediction'` — not previously named in
this section)**:

- [`plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md`](/plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md)
  — 0 open todos (closed/archived/record-only)

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
