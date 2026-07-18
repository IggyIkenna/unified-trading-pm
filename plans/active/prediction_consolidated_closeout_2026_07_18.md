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
    cefi_consolidated_closeout_2026_07_18.md,
    tradfi_consolidated_closeout_2026_07_18.md,
    data_completion_prediction_2026_07_15.md,
    prediction_canonical_identity_migration_2026_07_08.md,
    prediction_capture_incident_remediation_2026_07_06.md,
    prediction_venue_perps_and_live_clob_depth_2026_06_20.md,
    predictions_ml_walk_forward_and_arb_2026_06_20.md,
    predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    data_pipeline_e2e_check_2026_07_10.md,
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
(`codex/02-data/availability-manifest-and-data-status.md:57-60`) the prediction atom is
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
(`codex/02-data/data-status-drilldown-hierarchy.md:42`), i.e. CQG sits ABOVE data_type (opposite ordering to the flat
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

## Phase A — get ALL the code ready (writers live+batch · adapters · migration scripts · fixture-attribute writers)

> Nothing migrates until every WRITER emits the canonical shape and the capture path is honest. Includes the fixture
> attribute-writer work (Phase E depends on it) so the Phase-D re-backfill already carries the new columns.

### A0 — Enumerate the live prediction dimensions FIRST (single source of truth)

- [x] ✅ [AUDIT] P0. **Enumerated the FULL distinct prediction dimension set from live prod GCS (slot-2, 2026-07-18)** —
      manifest `availability_index` 756,817 rows + catalogue `prod/catalog.parquet` 2,900,318 rows; see Progress Log §
      A0. **Non-canonical/dedupe targets found (drive Phase B), catalogue = SSOT:** (1) `data_type` DUPE
      `prediction_trades` vs canonical `trades`; (2) manifest `instrument_type` 18 distinct — canonical
      `PREDICTION_MARKET` mixed with lowercase dupes `prediction`/`prediction_market` + underlying-asset LEAKAGE
      (BTC/ETH/SPX/DJIA/NDX/GOLD/SILVER/CRUDE_OIL/DOGE/XRP/BNB/HYPE/OTHER) + `''`, while the catalogue is clean
      (`PREDICTION_MARKET` only); (3) `source` empty `''`; (4) catalogue `base_asset` 572,211 distinct raw market-title
      text w/ leading-whitespace dupes. **Clean:** CQG (81 canonical UPPERCASE values, no dupes) + catalogue
      `instrument_type`. Reusable reads: scratchpad `enumerate_prediction_dimensions.py` /
      `count_prediction_baseline.py`. (repos: instruments-service, market-tick-data-service)

### A1 — Capture path honest + live (fold: capture-incident remediation)

- [ ] [BACKEND] P0. **Finish the prediction capture-incident remediation** — harden the capture path (consolidator utf8
      typing, backfill the 07-01→07-06 missed window) and confirm the KALSHI/POLYMARKET-PERP adapters no longer hit the
      wrong Kalshi host (the fake-PERPETUAL cefi contamination). `prediction_capture_incident_remediation_2026_07_06.md`
      (9 open). (repos: market-tick-data-service, unified-trading-library, deployment-service)
- [ ] [BACKEND] P0. **Kill the dead Kalshi `trading-api.kalshi.com` host reintroduced into the smoke matrix** + add the
      regression check that the elections-subdomain plan Phase 4 never added; fix the `raw_tick_data/by_date/` drift.
      `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`. (repos: market-tick-data-service)
- [ ] [BACKEND] P1. **Adapters must apply lifecycle bounds BEFORE the network call** — today inactive days land as
      `SOURCE_RETURNED_ZERO` instead of an honest `EXPECTED_*`, and the CLOB catalogue scoped to `end_date_iso==day` can
      cap backfills to the resolution day.
      `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`. (repos:
      market-tick-data-service)

### A2 — Instrument-id / underlying / CQG writers converge (fold: canonical-identity migration)

- [ ] [BACKEND] P0. **Finish the prediction canonical-identity migration (4 open of 8)** — adapter-level `underlying`
      from `classify_*_to_canonical_group`, materialise `canonical_instrument_id` from `cross_venue_mapping`, and align
      the Prediction sports-fixture key with the Sports asset group's `build_fixture_id()`.
      `prediction_canonical_identity_migration_2026_07_08.md`. **This is the Phase-E Leg-1 seam** — the
      sports-fixture-key alignment todo here is exactly what Phase E extends to Kalshi + `af_fixture_id`. (repos:
      instruments-service, unified-api-contracts)
- [ ] [BACKEND] P1. **Route every prediction id/underlying/CQG writer through the shared canonical builder + a QG that
      fails a non-canonical prediction `instrument_id`/`canonical_question_group` on write** — re-drift prevention, so
      new writes can't reintroduce the dupes A0 enumerates. (repos: instruments-service, market-tick-data-service,
      unified-api-contracts)

### A3 — Venue-perps + live CLOB depth residuals (fold)

- [ ] [BACKEND] P1. **Close the 12 residuals on Kalshi/Polymarket perpetual futures + live CLOB depth/quotes** (funding
      / basis / dispersion arb inputs). `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` (12 open of 85).
      (repos: market-tick-data-service, unified-api-contracts, features-service)

### A4 — Fixture-attribute WRITERS (Phase E depends on this landing before the Phase-D re-backfill)

- [ ] [BACKEND] P0. **Add the additive fixture-match attributes to the prediction soccer instrument/tick schema — keep
      prediction's canonical naming, ADD columns.** On Polymarket AND Kalshi soccer rows, emit (nullable,
      honest-absence, no sentinel): `af_league_id` (canonical), `home_team_canonical_id`, `away_team_canonical_id`,
      `fixture_date`, `af_fixture_id` (int), `af_fixture_match_status`
      (`MATCHED`/`UNRESOLVED_TEAM_NAME`/`NO_FIXTURE_DATA`) — mirroring the odds-tick schema already shipped in MTDS
      (`SPORTS_INSTRUMENTS.md`, `fixture_id_resolver.py`). Polymarket already computes the `build_fixture_id()` string
      in `.../adapters/prediction/polymarket/parsing.py::_build_sports_id` — add the resolved `af_fixture_id` alongside
      it; Kalshi gets the whole set new. (repos: unified-api-contracts, instruments-service, market-tick-data-service)

## Phase B — run the migrations (gated on Phase A green)

> Pre-migration drain per the VM runbook; direct manifest mutation MUST use the additive per-VM-shard write (race-free
> vs the ~10-min consolidator) — do NOT do a naive `_index`-only rewrite.

- [x] ✅ [DATA] P0. **CQG-bundle-atom wipe FIXED (verified 2026-07-18, slot-2 A0).** The phantom-reconciler bundle-atom
      exemption (`MANIFEST_ONLY_BUNDLE_DATA_TYPES` in `unified_trading_library/reconcile/manifest.py`) landed 2026-07-11
      and the rebuild restored the CQG cluster rows; A0 live read confirms **17,352 captured**
      `prediction_canonical_question_group` rows (was "ZERO"). Original P0 closed —
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` steps 1-4 landed.
- [ ] [BACKEND] P1. **Close the CQG-issue RESIDUALS (steps 5-6, still open).** (5) Add `pipeline_mode=live_kalshi` /
      `live_polymarket_clob` / `live_polymarket_gamma_api` prefix shapes to UAC `possible_manifest` /
      `canonical_path_templates('prediction')` so the phantom-audit can distinguish genuinely-batch-absent from
      batch-absent-but-live-captured (13,292 phantom rows currently indeterminate) — rule-11 cross-AG regression + a
      BATCH-satisfied-by-LIVE-evidence SEMANTICS call (may be BLOCKED-OPERATOR-DECISION). (6) Root-cause the KALSHI →
      `batch_polymarket_clob` / `source=polymarket_clob` provenance mislabel (11,988 rows) in
      `market_tick_data_service/scripts/rebuild_prediction_manifest.py`'s writer — this is what skews A0's `source`
      counts (KALSHI undercounted). `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` §5-6 +
      `issues/phantom_captures_prediction_2026_06_28.md`. (repos: unified-api-contracts, market-tick-data-service)
- [ ] [DATA] P0. **Enumeration-driven canonical/dedupe migration of the prediction manifest (A0-driven, single source of
      truth, operator 2026-07-18)** — CONCRETE A0 targets, catalogue is SSOT: (a) `data_type` `prediction_trades` →
      `trades`; (b) `instrument_type` → `PREDICTION_MARKET` — fold lowercase `prediction`/`prediction_market`, and
      re-stamp the underlying-asset-leakage rows (`BTC`/`ETH`/`SPX`/`DJIA`/`NDX`/`GOLD`/`SILVER`/`CRUDE_OIL`/`DOGE`/
      `XRP`/`BNB`/`HYPE`/`OTHER`/`''`, the pre-Plan-A legacy `data_type=<base_asset>` shape) by classifying from the
      CQG/underlying, NOT trusting the column; (c) stamp empty `source=''` from the writer's `default_source`; (d)
      catalogue `base_asset` whitespace-strip + dedupe (leading-space title variants). Additive per-VM-shard write
      (race-free vs the ~10-min consolidator). Fold: the prediction slice of `data_completion_prediction_2026_07_15.md`
      (23 open). (repos: market-tick-data-service, instruments-service, unified-trading-library)
- [ ] [DATA] P0. **Backfill the fixture-match attributes (A4 columns) across historical Polymarket + Kalshi soccer** —
      resolve `af_fixture_id` per market from the fixtures parquet (canonical `home_id`/`away_id` + `af_league_id` +
      `fixture_date`) OR by parsing the human-readable canonical name, stamping `af_fixture_match_status`. Honest nulls
      where unresolved; the match-rate summary line logged per (league, day). (repos: market-tick-data-service,
      instruments-service)
- [ ] [DECISION] P1. **Any prediction dimension value whose canonical form is AMBIGUOUS = BLOCKED-OPERATOR-DECISION** —
      surface the A0-enumerated ambiguous set to the operator (options + a marked recommendation) rather than guessing;
      does not block the unambiguous majority of the migration.

## Phase C — data-status + honest-coverage (gated on Phase B)

- [ ] [UI] P0. **RE-ADD the data-status "dimensions enumeration" view to deployment-ui/api (operator, 2026-07-18 — "I
      really need to add it back").** Per asset_group, list every distinct `instrument_type` / `data_type` / `venue` /
      `canonical_question_group` present in the manifest/GCS honest-coverage rollup WITH counts, so non-canonical
      naming + duplications are VISIBLE — the standing canonical-drift detector (how we catch the next drift without a
      manual parquet read). NOTE: the underlying query already exists today —
      `GET /data-status/catalogue-filter-options` (`deployment-api/.../routes/data_status/_catalogue.py`) returns
      distinct `{venues, instrument_types, data_types}` and `GET /data-status/prediction-catalogue` returns `cqg_counts`
      — so this is mostly a UI dimensions-panel + wiring task, plus adding the counts/CQG axis to the panel. pw:L2 ✓ +
      regression required for the UI leg. Mirrors the identical tradfi Phase-C todo. (repos: deployment-api,
      deployment-ui)
- [ ] [BACKEND] P1. **Honest-coverage green for prediction** — confirm `measure_honest_coverage.py` rolls up prediction
      correctly once the CQG cluster rows exist again (output
      `gs://central-element-323112-honest-coverage/{date}/coverage.json`); verify the daily scheduler actually fires
      (`measure_honest_coverage.py` header says `last_executed: NEVER`; the Cloud Scheduler `honest-coverage-daily`
      create was pending — `gcloud scheduler jobs describe honest-coverage-daily     --location=asia-northeast1`).
      (repos: instruments-service, deployment-service)
- [ ] [BACKEND] P1. **Close the prediction UI drilldown + synthetic OTHER CQG bucket** — the 3 residuals on the
      catch-all `OTHER` canonical-question-group bucket end-to-end + the deployment-ui 3-level drilldown
      (`venue → canonical_question_group → day`). `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` (3 open).
      (repos: deployment-api, deployment-ui)
- [ ] [BACKEND] P2. **DP_CATALOG stale alert (shared w/ sports)** — the `DP_CATALOG_NOT_RUNNING` alert fired for both
      sports + prediction `prod/catalog.parquet` (~25h stale); confirm the prediction catalogue writer runs on schedule.
      Cross-link `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (owned jointly with sports_master).

## Phase D — re-smoke-test the backfills, prediction-only, ALL shards (post-migration completion gate)

> **Terminal data-readiness gate.** Post-migration, run BOTH pipeline-check skills scoped to **prediction only** and
> require green across every prediction shard — force-refetch + skip-if-fresh + a canonical-shape assertion — so we KNOW
> prediction is complete before any MVP backfill. Both skills already accept `--asset-group PREDICTION`; **do NOT pass
> `--tardis-only`** (Polymarket/Kalshi are not Tardis-sourced → it would enumerate 0 shards). Prediction shards: **IS =
> 2** `(PREDICTION, POLYMARKET)`, `(PREDICTION, KALSHI)` (IS atom has no data_type axis); **MTDS = 4**
> `{POLYMARKET, KALSHI} × {trades, book_snapshot_5}`.

- [ ] [INFRA] P0. **FIX the missing MTDS prediction `-test-` bucket isolation (biggest smoke-test gap).**
      `_test_bucket("prediction")` (`market-tick-data-service/scripts/pipeline_e2e_check.py:434-450`) has no `-test-`
      sibling and returns the PROD `market-data-tick-prediction` bucket — so a prediction force/skip leg writes to PROD.
      Add `market-data-tick-pred-test-central-element-323112` (Phase-0 provision) and wire `_test_bucket` to it,
      matching the cefi/tradfi test-bucket-only invariant. Until this lands, Phase-0's `pred` gate reports GAP by
      design. (repos: market-tick-data-service, deployment-service)
- [ ] [DATA] P1. **Reconcile the `book_snapshot_5` MVP-scope disagreement** — it is in `VENUE_DATA_TYPE_CAPABILITIES` +
      `expected_coverage` (so a plain MTDS matrix gives 4 shards) but is ABSENT from `PredictionMvpRule.data_types`
      (`_mvp_scope_rules.py`), so an `--mvp-only` run silently tests only `trades` (2 shards). Decide the canonical set
      and align the registries. (repos: unified-api-contracts)
- [ ] [DATA] P1. **Add force/skip smoke coverage for the CQG cluster grain + `market_lifecycle`** — today MTDS enumerate
      explicitly excludes `prediction_canonical_question_group` and IS collapses its atom to `(asset_group, venue)`, so
      neither is smoke-tested as a distinct shard. Extend the prediction adaptation so the CQG bundle + lifecycle grains
      get a genuine force/skip proof (post the Phase-B wipe fix). (repos: unified-trading-pm, market-tick-data-service)
- [ ] [DATA] P0. **Adapt `data-pipeline-check-mtds` + `data-pipeline-check-is` to prediction** — iterate every
      prediction shard (IS 2, MTDS 4 above). Per shard: force-refetch + skip-if-fresh proof
      (`--require-captured --auto-day` so a day before `book_snapshot_5` onset 2026-06-22 yields a GENUINE not ambiguous
      skip) + a **canonical regression cell** asserting the written shard's `instrument_id` / `canonical_question_group`
      is canonical (0 raw, 0 whitespace, 0 non-canonical variant) and, for soccer rows, that `af_fixture_match_status`
      is stamped. Build on the shared engine in `data_pipeline_e2e_check_2026_07_10.md`. (repos: unified-trading-pm,
      market-tick-data-service, instruments-service)
- [ ] [DATA] P0. **Run `data-pipeline-check-is` for prediction-only, all shards, post-migration** — real operator-given
      `--day` against `-test-` buckets; both prediction IS shards prove force/skip + canonical shape; report path cited.
- [ ] [DATA] P0. **Run `data-pipeline-check-mtds` for prediction-only, all shards, post-migration** — same day, all 4
      prediction MTDS shards prove force/skip + canonical shape; report path cited. **BOTH skills green across all
      prediction shards = prediction is code-complete, migrated, honestly-covered, and verified.**
- [ ] [DATA] P0. **MVP backfill readiness gate** — only after A–D green: run the prediction MVP backfills and verify
      manifest-counted canonical rows for each MVP cell (Polymarket + Kalshi × trades + book_snapshot_5, CQG cluster).

## Phase E — football (soccer) cross-venue arb enablement (the originating ask; gated on B+D)

> Makes live-odds-API-vs-Polymarket-vs-Kalshi football arb possible on a CANONICAL basis. Depends on the A4 writers +
> the Phase-B fixture-attribute backfill landing. SSOTs:
> `codex/04-architecture/cross-venue-prediction-arb-detection.md`,
> `codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md`, `instruments-service/docs/SPORTS_INSTRUMENTS.md`.

### E1 — Thread the fixture id onto BOTH prediction venues (Leg 1)

- [ ] [BACKEND] P1. **Verified end-to-end fixture link on Polymarket + Kalshi soccer** — confirm A4/B produced a
      resolved `af_fixture_id` (or `build_fixture_id` string) on Polymarket soccer markets, and BUILT the same for
      Kalshi (which has none today). Keep the prediction canonical naming; the fixture id is an ADDITIVE attribute.
      Acceptance: a Polymarket market and a Kalshi market for the same real fixture resolve to the SAME `af_fixture_id`,
      and both resolve to the same odds-tick `af_fixture_id`. (repos: instruments-service, market-tick-data-service,
      unified-api-contracts)

### E2 — Close the team-name matching gap to ~0% (Leg 2)

- [ ] [BACKEND] P1. **Robust/logical fixture matching to a ~0% team-name gap.** Drive the join off the fixtures parquet
      (canonical `home_id`/`away_id` + `af_league_id` + `fixture_date`) OR by parsing the human canonical name; add the
      missing aliases so the ~66% odds-side match rate climbs toward 100%. Two known holes: (a) the South-American club
      alias gap in `unified_api_contracts.external.api_football.team_mappings` (e.g. `Coquimbo Unido`, `O'Higgins`,
      `Universidad Católica (CHI)`) — verify each against API-Football's own naming, don't guess; (b) **build a Kalshi
      soccer team registry** — Kalshi titles are city-level with no team-name-to-canonical mapping today. Log the
      per-day match rate so the gap is visible in monitoring. (repos: unified-api-contracts, instruments-service,
      market-tick-data-service)

### E3 — Unify the two arb paths onto the shared fixture identity (Leg 3)

- [ ] [BACKEND] P2. **Unify the disconnected arb paths onto `af_fixture_id`.** Today: features-service
      `cross_venue_arb_detector` does Kalshi↔Polymarket (crypto-oriented in practice) and the e2e `live_arb_scanner.py`
      does bookmakers+Betfair+Polymarket (no Kalshi, heuristic team-name match, prototype) — neither keys on
      `af_fixture_id`. Give both a shared fixture-keyed join so a single comparison spans bookmakers ∧ Polymarket ∧
      Kalshi on one fixture; wire Kalshi into the scanner (needs the Kalshi API key in Secret Manager — currently 401).
      Fold the predictions-ML arb half: `predictions_ml_walk_forward_and_arb_2026_06_20.md` (5 open; GATED on
      `sports_master:Group     E` FSS ≥95% non-NULL). (repos: features-service, e2e-testing, market-tick-data-service)
- [ ] [BACKEND] P2. **3-way arb correctness guards** — prediction-market "lay" is the NO-side complement, not a real
      exchange lay (exclude from back-lay arbs; include in 3-way with exchange_meta validation); keep the honest gate
      that a real two-sided book must exist on BOTH venues before emitting an arb row.
      `codex/04-architecture/cross-venue-prediction-arb-detection.md`. (repos: features-service)

## Codex SSOTs (read before touching a phase)

`codex/02-data/prediction-data-types-catalog.md`, `codex/02-data/prediction-schema-paths.md`,
`codex/02-data/prediction-perps-sourcing.md`, `codex/02-data/prediction-settlement-availability-convention.md`,
`codex/02-data/availability-manifest-and-data-status.md`, `codex/02-data/data-status-drilldown.md`,
`codex/02-data/data-status-drilldown-hierarchy.md`, `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`,
`codex/02-data/venue-availability.md`, `codex/02-data/honest-absence-downstream-handling.md`,
`codex/04-architecture/prediction-batch-live.md`, `codex/04-architecture/cross-venue-prediction-arb-detection.md`,
`codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md`,
`codex/09-strategy/operational/prediction-markets-codification-gaps.md`, `codex/01-domain/sports-instruments.md`,
`codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md`. Plus (Phase E odds/fixture side, out-of-repo):
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
- **Venue-perps / CLOB depth**: `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.
- **UI / bucket**: `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`.
- **ML / arb (downstream, gated)**: `predictions_ml_walk_forward_and_arb_2026_06_20.md`.
- **Cross-cutting (shared w/ sports)**: `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`; sports feeder
  side lives in `sports_master` (fixtures/odds that Phase E consumes) — cross-link, not owned here.
- **Cross-asset arb (separate, archived/tradfi)**: `archive/2026_05/cme_polymarket_arb_2026_05_08.md` (CME↔Polymarket).
- **Skills / engine**: `data_pipeline_e2e_check_2026_07_10.md` + the `data-pipeline-check-mtds` /
  `data-pipeline-check-is` skills.
- **Parent epic (stale — see Progress Log)**: `epics/predictions_master.md`.

## Progress Log

- **2026-07-18 (slot-2) — Plan authored from a 6-agent read-only research pass; tab-2 corpus first synced to current.**
  - **Sync**: tab-2 `unified-trading-pm` was on a stale `live-defi-rollout @ 2f94ae04b` (June 12; ~11.8k commits behind,
    10 local commits already preserved on `origin/wip-preserve/human-planning-pm-2026-06-16`). Hard-reset to
    `origin/live-defi-rollout @ 6c4787972` after backing the old HEAD up as `backup/pre-sync-june12-2f94ae04b`; skills
    re-linked (6 surfaced). Authored against the current corpus.
  - **Originating question (answered)**: canonical football fixture id = `af_fixture_id` (API-Football) / the
    `build_fixture_id` string; odds ticks are joined to it (~66%, alias-gapped). `canonical_question_group` is canonical
    as a cross-venue THEMATIC label but NOT keyed to the fixture id. Polymarket soccer carries the `build_fixture_id`
    STRING; Kalshi carries no fixture id; the two arb paths (features-service kernel + e2e scanner) are disconnected and
    neither keys on `af_fixture_id`. → Phase E scopes the fix.
  - **Fold set (current corpus)**: 6 active plans + 4 open issues folded; 3 cross-linked (shared w/ sports); 4 excluded
    (resolved / footystats-is-sports). `parent_epic: predictions_master` set (one-directional, matching cefi/tradfi
    precedent — the epic does not back-reference its close-out).
  - **Epic staleness noted (not fixed here)**: `epics/predictions_master.md` `related:` still points at the two
    now-archived June files (`../archive/2026_07/prediction_manifest_canonicalisation_2026_06_01.md`,
    `../archive/2026_07/predictions_lookahead_and_reader_migration_2026_06_20.md`) and references none of the 3 newest
    prediction plans — worth an epic `related:` refresh on a plan-reconcile pass.
  - **NOT re-measured live**: the Ground-truth verdict is from the folded issues, not a fresh prod GCS read — A0 is the
    first migration step precisely to enumerate the live prediction dimensions before migrating (mirrors tradfi's
    enumeration-driven single-source-of-truth).
  - **Shard-atom correction added (operator, 2026-07-18)**: confirmed against the SSOT
    (`codex/02-data/availability-manifest-and-data-status.md:57-60`) that the prediction shard atom is keyed on
    `canonical_question_group` (manifest-only bundle) / per-CID `instrument_id` (raw), NOT
    `(instrument_id OR underlying)` — `underlying` is display-only. Added the "Shard atom for prediction" subsection to
    Ground-truth; it is the root cause of the Phase-B CQG-wipe and the verify-gate assertion for A0/A2/B/D.

- **2026-07-18 (slot-2, autonomous tick 1) — A0 live enumeration DONE; climbing-metric baseline set (this SUPERSEDES the
  "NOT re-measured live" caveat above).** Read-only prod GCS (scratchpad `enumerate_prediction_dimensions.py` +
  `count_prediction_baseline.py`, own venv, ADC `central-element-323112`). Manifest
  `market-data-tick-pred-prd/_index/availability_index.parquet` = 756,817 rows; catalogue
  `instruments-store-pred-prd/prod/catalog.parquet` = 2,900,318 rows.
  - **CLIMBING METRIC baselines (manifest):** `instrument_type` **11.70% canonical** (88,560 `PREDICTION_MARKET` /
    756,817; rest = 633,521 null + 17,361 `prediction` + 9,460 `''` + 7,007 `prediction_market` + ~1,100
    underlying-asset leakage BTC/ETH/SPX/SOL/NDX/GOLD/DJIA/SILVER/CRUDE_OIL/BNB/DOGE/HYPE/XRP/OTHER); `data_type`
    **99.55%** (only `prediction_trades` 3,385 = dupe of `trades`); `source` **~100%** (only 2 empty rows). Catalogue is
    CLEAN (`instrument_type`=`PREDICTION_MARKET` only; `data_type` no dupe).
  - **Dedupe/canonical targets (drive Phase B, catalogue = SSOT):** `prediction_trades`→`trades`; manifest
    `instrument_type`→`PREDICTION_MARKET` (fold lowercase dupes + re-stamp null/underlying-leakage per-CID rows,
    classify from CQG/underlying — verify null-vs-required for the raw grain against writer intent, don't blind-stamp);
    stamp the 2 empty `source`; catalogue `base_asset` (572,211 distinct raw titles) whitespace-strip + dedupe
    leading-space variants.
  - **CQG dimension CLEAN:** 81 distinct canonical UPPERCASE values, no dupes — incl. football `SPORTS_EPL_MATCH` /
    `SPORTS_LA_LIGA_MATCH` / `SPORTS_SERIE_A_MATCH` / `SPORTS_BUNDESLIGA_MATCH` / `SPORTS_CHAMPIONS_LEAGUE_MATCH` /
    `SPORTS_UEFA_MATCH` / `SPORTS_WORLD_CUP_MATCH` (the Phase-E football slice).
  - **CORRECTION to Ground-truth:** CQG cluster atom is **present at `captured` (17,352 rows)**, NOT "ZERO" as the
    folded issue `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` claimed — the wipe is fixed or
    intermittent; Ground-truth row updated, Phase-B item downgraded to verify-not-fix.
  - **Env:** 9 target repos present on `live-defi-rollout`; ADC `central-element-323112`; other slots mid-migration
    (HEAD = tradfi Phase B) → prediction work scoped to prediction-specific files, no VM drain.

- **2026-07-18 (slot-2, autonomous tick 2) — CQG-wipe VERIFIED-FIXED + reframed; Kalshi creds confirmed present; honest
  execution-gate status.**
  - **CQG-wipe (the plan's headline "biggest gap") is ALREADY FIXED** —
    `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` §Update-2026-07-11 confirms the
    `MANIFEST_ONLY_BUNDLE_DATA_TYPES` reconciler exemption landed + rebuild restored the CQG rows; A0 corroborates
    (17,352 captured). Flipped the Phase-B P0 to done; opened a P1 for the issue's REAL open residuals — (5) UAC
    `possible_manifest` missing `live_*` path-template prefixes (13,292 phantom rows indeterminate; BATCH-vs-LIVE
    semantics = operator call) and (6) the KALSHI→`polymarket_clob` provenance mislabel (11,988 rows) in
    `rebuild_prediction_manifest.py` — (6) is the cause of A0's skewed `source` counts (KALSHI undercounted).
  - **Kalshi is NOT credential-blocked** — Secret Manager has `kalshi-api-credentials` (`gcloud secrets list`,
    names-only). Per autonomous rule 1 the creds exist, so Kalshi capture / soccer-team-registry / arb work is
    executable, not deferrable as BLOCKED-CREDENTIALS (the codex "pending" framing is stale for the secret's existence;
    runtime validity TBD when the adapter runs).
  - **EXECUTION GATE (honest, per rule 12e stall-diagnosis).** The shared branch is under heavy concurrent slot activity
    (rebased across +44 then +6 commits mid-session; HEAD = tradfi/cefi Phase B). The remaining prediction CODE units
    (A2 identity, A4 fixture writers, CQG residual §5-6, Phase-C UI, Phase-E arb) live in repos those slots are ACTIVELY
    editing (UAC / MTDS / IS / features-service), and the irreversible Phase-B prod migration needs a pre-migration VM
    drain that would kill their live migrations. Per rule 5 (never two agents on the same repo/file) + no-drain-while-
    others-migrate, these are **SEQUENCED behind the concurrent tradfi/cefi migrations**, not abandoned. Safe unblocked
    work done this window: plan authored + committed, A0 baseline, CQG-verify, residual reframing — all committed.
  - **NEXT actionable tick (resume conditions):** when the concurrent tradfi/cefi migrations clear the shared repos +
    free the prod-migration infra, resume dependency-ordered A2/A4 (prediction-scoped files, per-repo sub-agents,
    QG-green + quickmerge) → then Phase-B prediction migration (own drain window) → C/D/E. Operator-decision to unblock
    §5: does a BATCH manifest row count as satisfied by LIVE-only object evidence? (A: yes, union batch+live for the
    cell [REC — CF-12 batch=live symmetry]; B: no, BATCH tracks batch-path completeness only; Other).

- **2026-07-18 (slot-2, autonomous tick 3) — operator left 2h (/autonomous, "prediction-specific files only"); fanned
  out sub-agents; §6 verified already-fixed; INDEX re-added.**
  - **§6 (KALSHI→polymarket_clob provenance mislabel) — CODE already RESOLVED** by `market-tick-data-service@3397e7ae`
    ("rebuild_prediction_manifest venue-resolves bundle pipeline_mode/source per-venue"). Verified INDEPENDENTLY (git
    log
    - current write site L543-560 uses `derive_pipeline_mode_for_row(venue,…)`), NOT trusting the §6 sub-agent — which
      died on an API error after reaching the same conclusion, leaving ZERO uncommitted MTDS changes. Annotated the
      issue doc §6 CODE-RESOLVED; the ~11,988 historical mislabeled rows self-correct on the next rebuild (held Phase-B
      DATA step, not a code task). §6 code side done.
  - **INDEX `### Prediction` re-added** — my entry had been dropped from the committed tree by a rebase (heavy
    concurrent INDEX churn from other slots' verify-rerun-2 syncs); re-committed to make it durable.
  - **A2 sub-agent (IS `adapters/prediction/**` + UAC `canonical/domain/predictions/**`) still running** — will
    verify/journal/flip its shipped items on completion, then fan out A4 (fixture-attribute writers) + E2 (Kalshi soccer
    team registry).
  - **Method note:** sub-agent code-ships are adversarially verified (git log + code read) before I flip anything — a
    dead/incomplete agent's claim is never taken on trust.
