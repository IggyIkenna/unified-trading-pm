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

- [ ] [BACKEND] P0. **Finish the prediction canonical-identity migration — now 5/8 done (slot-2 verified 2026-07-18).**
      Shipped: todos 1/3/4/5 (`instruments-service@0d0c3742` — adapter `underlying` from
      `classify_*_to_canonical_group`, cross-venue `canonical_instrument_id`, titles-map decision, Polymarket sports
      `build_fixture_id`) + todo 6 as VERIFY (`unified-trading-pm@16272205a` — downstream `instrument_id` uniqueness
      SAFE, venue embedded by construction). **3 DEFERRED (not prediction-specific-file):** todo 2 = full
      `prod/catalog.parquet` regen (prod-GCS operational run, gated on the in-flight shared canonical migration so it
      doesn't bake transitional ids); todo 7 = `gcs_paths.py` bucket-abbreviation flip (SHARED UAC file + gated on MTDS
      `migrate_prediction_to_pred_prd_v9.py`); todo 8 = MDPS UAC-pin verify (market-data-processing-service repo, its CI
      catches the drift). Source: `prediction_canonical_identity_migration_2026_07_08.md`. **Phase-E Leg-1 seam** = todo
      5 (done Polymarket; Kalshi extended in Phase E). (repos: instruments-service, unified-api-contracts)
- [ ] [BACKEND] P1. **Route every prediction id/underlying/CQG writer through the shared canonical builder + a QG that
      fails a non-canonical prediction `instrument_id`/`canonical_question_group` on write** — re-drift prevention, so
      new writes can't reintroduce the dupes A0 enumerates. (repos: instruments-service, market-tick-data-service,
      unified-api-contracts)

### A3 — Venue-perps + live CLOB depth residuals (fold)

- [ ] [BACKEND] P1. **Close the 12 residuals on Kalshi/Polymarket perpetual futures + live CLOB depth/quotes** (funding
      / basis / dispersion arb inputs). `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` (12 open of 85).
      (repos: market-tick-data-service, unified-api-contracts, features-service)

### A4 — Fixture-attribute WRITERS (Phase E depends on this landing before the Phase-D re-backfill)

- [x] ✅ [BACKEND] P0. **Fixture-match attributes on prediction soccer — RESOLVER + SCHEMA + MATERIALIZATION COMPLETE
      (instrument-level, 2026-07-18).** The 6 fixture columns now flow resolver→side-table→instrument parquet: UAC
      `InstrumentRecord` + `INSTRUMENTS_PARQUET_SCHEMA` `unified-api-contracts@e7ed754e` (additive nullable) + IS
      `process_write._records_to_dataframe` join `instruments-service@e3ffc613` (type-boundary handled: side-table
      int/str → contract str/date, honest-absence on bad values; cross-AG round-trip verified — non-prediction rows keep
      all 6 None; QG-green 4579 passed). MTDS prediction-tick schema = OPTIONAL/DEFERRED (catalogue carries the attrs;
      tick-grain only if the arb path needs it). Historical BACKFILL of the columns for existing instruments = held with
      the Phase-B prod run. Resolver increment SHIPPED `instruments-service@85988ade` (QG-green, 662 lines, 8 files):
      new `adapters/prediction/fixture_match.py` resolver + per-instrument side-table — **Polymarket** soccer resolves +
      stamps `af_fixture_id` off the SAME fixtures parquet the MTDS `FixtureIdResolver` reads
      (`candidate_parquet_paths("FIXTURES",…,BATCH_API_FOOTBALL)`, cached per (league,day), canonicalising both sides
      through the SAME `validate_team_resolution` alias index — no new GCS walk); **Kalshi** soccer stamps
      honest-absence (`af_fixture_match_status=UNRESOLVED_TEAM_NAME`, `af_fixture_id=None`,
      `af_league_id`+`fixture_date` still resolved) pending E2; closed set
      `MATCHED`/`UNRESOLVED_TEAM_NAME`/`NO_FIXTURE_DATA`, nullable int, no sentinel; resolver never raises. Tests:
      `test_prediction_fixture_match.py`. **NOW SHIPPING (round-2, constraint lifted)** — materialize the 6 attrs as
      real parquet/manifest COLUMNS: UAC `InstrumentRecord` ✅ e7ed754e + IS `process_write._records_to_dataframe` join
      (reads `fixture_match_for_instrument_key`, ~6-line extension of the `clob_token_ids` block) + the MTDS
      prediction-tick schema — see HELD list. (repos: instruments-service ✅; unified-api-contracts +
      market-tick-data-service DEFERRED)

## Phase B — run the migrations (gated on Phase A green)

> Pre-migration drain per the VM runbook; direct manifest mutation MUST use the additive per-VM-shard write (race-free
> vs the ~10-min consolidator) — do NOT do a naive `_index`-only rewrite.

- [x] ✅ [DATA] P0. **CQG-bundle-atom wipe FIXED (verified 2026-07-18, slot-2 A0).** The phantom-reconciler bundle-atom
      exemption (`MANIFEST_ONLY_BUNDLE_DATA_TYPES` in `unified_trading_library/reconcile/manifest.py`) landed 2026-07-11
      and the rebuild restored the CQG cluster rows; A0 live read confirms **17,352 captured**
      `prediction_canonical_question_group` rows (was "ZERO"). Original P0 closed —
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` steps 1-4 landed.
- [x] ✅ [BACKEND] P1. **CQG-issue residuals 5-6 — DONE (2026-07-18).** (5) `pipeline_mode=live_*` prefixes shipped —
      `unified-api-contracts@e7ed754e` (operator DECIDED union batch+live): `live_kalshi`/`live_polymarket_clob` were
      already emitted (2026-07-11); added the missing `live_polymarket_gamma_api` via a prediction-scoped
      `_EXTRA_LIVE_PROBE_SOURCES_BY_AG` probe (did NOT fabricate a `LIVE_POLYMARKET_GAMMA_API` enum member — that source
      is batch-only by design); rule-11 verified cefi/tradfi/defi/sports template counts byte-unchanged. (6) KALSHI
      provenance mislabel already fixed `market-tick-data-service@3397e7ae` (see §6).
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` §5 flipped `pm@4436e59f0`. (repos:
      unified-api-contracts ✅, market-tick-data-service ✅)
- [ ] [DATA] P0. **Enumeration-driven canonical/dedupe migration of the prediction manifest (A0-driven, single source of
      truth, operator 2026-07-18)** — CONCRETE A0 targets, catalogue is SSOT: (a) `data_type` `prediction_trades` →
      `trades`; (b) `instrument_type` → `PREDICTION_MARKET` — fold lowercase `prediction`/`prediction_market`, and
      re-stamp the underlying-asset-leakage rows (`BTC`/`ETH`/`SPX`/`DJIA`/`NDX`/`GOLD`/`SILVER`/`CRUDE_OIL`/`DOGE`/
      `XRP`/`BNB`/`HYPE`/`OTHER`/`''`, the pre-Plan-A legacy `data_type=<base_asset>` shape) by classifying from the
      CQG/underlying, NOT trusting the column; (c) stamp empty `source=''` from the writer's `default_source`; (d)
      catalogue `base_asset` whitespace-strip + dedupe (leading-space title variants). Additive per-VM-shard write
      (race-free vs the ~10-min consolidator). Fold: the prediction slice of `data_completion_prediction_2026_07_15.md`
      (23 open). (repos: market-tick-data-service, instruments-service, unified-trading-library) **SCRIPT WRITTEN +
      dry-run measured — `market-tick-data-service@5392b20b`** (initial) **+ `@916dd992`** (COMPLETE — now handles both
      findings: `--bundle-mode {normalize,leave}` default normalize, and `--remove-stragglers` design =
      pause-consolidator + snapshot + in-place `_index` CAS rewrite, guarded, NOT run). The 916dd992 agent found the
      WRITER ROOT of finding (i): `engine/orchestrator/manifest_finalize._finalize_prediction_bundles` stamps lowercase
      `instrument_type="prediction"` on every bundle row — so the bundle is emitted lowercase, not null; the writer-root
      fix is on the operator-review checklist (else a `--force` rebuild resurrects stragglers).
      (`scripts/canonicalize_prediction_manifest_2026_07_18.py`, `--dry-run` DEFAULT, `--apply` behind
      `--confirm-prod-write`; prod RUN HELD per operator). Live dry-run (756,817 rows): #1 `prediction_trades`→`trades`
      3,385 rows (99.55%→100%); #2 per-CID `instrument_type`→`PREDICTION_MARKET` 648,616 rows (per-CID 4.16%→100%,
      all-rows 11.70%→**97.40%**); #3 `source` 2 empty→`polymarket_clob`. **TWO FINDINGS FOR THE HELD RUN
      (operator-decision, revises decision-2):** (i) the CQG bundle is NOT null-by-design in practice — 80,068 rows =
      60,427 `PREDICTION_MARKET` + 17,361 lowercase `prediction` + only 2,280 null; keeping it unstamped caps all-rows
      at 97.40%, and its 17,361 lowercase `prediction` are themselves non-canonical → decide: normalize the bundle to
      `PREDICTION_MARKET` too (→~100%) vs enforce SSOT "bundle null" (un-stamps 77,788) vs leave inconsistent. (ii)
      `instrument_type`/`data_type` are consolidator DEDUP-KEY columns → the additive shard adds the corrected rows but
      leaves ~652k OLD rows as stragglers (doubling); reaching the target % needs an old-row sweep = the "naive direct
      `_index` rewrite" that resurrects on `--force` rebuild → the run needs a tombstone/removal strategy. Both
      documented in the script docstring + printed by dry-run.
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

- [x] ✅ [BACKEND] P1. **Fixture matching to the ~0% gap — DONE (Kalshi + South-American).** (b) ✅ Kalshi soccer team
      resolution SHIPPED: parser `instruments-service@ec8633ac` (`parse_kalshi_soccer_participants` → A4's
      `PredictionFixtureResolver` via the shared `validate_team_resolution` index, no new GCS walk) + 8 aliases
      `unified-api-contracts@e7ed754e` → **~0% → 82.6%→~100%** on 92 live Kalshi fixtures. (a) ✅ SHIPPED South-American
      club aliases `unified-api-contracts@98d757f9` (Chile/Argentina — Universidad Católica (CHI), Audax Italiano,
      Estudiantes L.P., Argentinos JRS, Central Córdoba de Santiago, Colo-Colo, O'Higgins, …), each verified against the
      API-Football FIXTURES parquet `af_home_name`; canonical ids pre-existed → closes the odds-side ~66% cap. Kalshi
      home/away title-order caveat ✅ CLOSED `instruments-service@ba3528d4` (order-robust lookup: probes both orderings,
      home/away from the matched fixture). (repos: instruments-service ✅, unified-api-contracts ✅ / South-American
      remaining))

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
- [x] ✅ [BACKEND] P2. **Venue-derivation for prediction/sports `instrument_id`s in execution-service — BOTH sites FIXED
      (2026-07-18).** The naive `split(":")[0]` returned the TYPE/SPORT for TYPE-first ids. (1) ✅
      `validation/instrument_format.py::get_venue_from_instrument_id` `execution-service@e3707472` (latent, no prod
      caller). (2) ✅ the production-critical sibling `utils/instruction_type.py::extract_venue`
      `execution-service@730fcd1c0` — it had the identical bug but is HEAVILY USED (~40 call sites: matching engines,
      preflight_gate, `infer_instruction_type`, `get_asset_group_from_instrument_id`) and HARD-CRASHED
      (`UnknownVenueError`) on a type-first id. Both use the SAME additive robust-parse via UAC `VENUE_CATEGORY_MAP`
      (venue-first byte-unchanged for cefi/defi/tradfi; type-first → `parts[1]`); QG-green, tests cover both. (repos:
      execution-service ✅)

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
- **A2 residual** (shared / other repo): identity-migration todos 2 (`prod/catalog.parquet` regen — prod-GCS run, gated
  on the shared canonical migration so it doesn't bake transitional ids), 7 (`gcs_paths.py` bucket-abbreviation flip), 8
  (MDPS UAC-pin verify).
- **CQG residual §5** (shared + operator decision): add `pipeline_mode=live_*` prefix shapes to UAC `possible_manifest`
  — needs the BATCH-satisfied-by-LIVE-evidence semantics call (A: union batch+live [REC]; B: batch-only).
- **Phase-B prod migration** (drain window): the enumeration-driven manifest canonicalisation (`prediction_trades`→
  `trades`, `instrument_type`→`PREDICTION_MARKET` 11.70%→100%, empty `source`, `base_asset` whitespace) + the
  fixture-attr backfill — needs a pre-migration VM drain the concurrent tradfi/cefi migrations currently occupy.
- **Phase C/D/E remainders** gated on the above (data-status dimensions view is partly already-served by
  `catalogue-filter-options`; smoke-test needs the MTDS prediction `-test-` bucket; arb-path unification needs the
  materialized columns + E2 resolution).

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

- **2026-07-18 (slot-2, autonomous tick 4) — A2 sweep verified + accepted; exec-service finding captured; A4
  dispatched.**
  - **A2 (prediction canonical-identity) verified & accepted.** Adversarially confirmed: todo 6 flip is real
    (`unified-trading-pm@16272205a` — "downstream instrument_id uniqueness VERIFIED SAFE, venue embedded by
    construction"), the sub-agent left ZERO uncommitted mess and did NOT touch this plan, and todos 1/3/4/5 are
    pre-shipped (`instruments-service@0d0c3742` ancestor of HEAD). Identity migration now **5/8**; the 3 remaining
    (catalog regen / `gcs_paths.py` shared file / MDPS repo) are genuinely NOT prediction-specific-file → deferred with
    reasons (A2 item updated above). No QG needed (IS/UAC only READ; pure PM flip).
  - **NEW cross-repo data-correctness finding (captured as Phase-E P2, flagged for execution-service owner):**
    `execution-service .../validation/instrument_format.py::get_venue_from_instrument_id()` = `split(":")[0]`
    mis-derives venue for TYPE-first prediction/sports ids (`FOOTBALL:POLYMARKET:…`→"FOOTBALL",
    `PREDICTION:KALSHI:…`→"PREDICTION"). Verified by reading the function (L100-102) + the id shapes (market_state.py
    L401 `{venue}:PREDICTION:{ticker}` venue-first vs the type-first sports/prediction ids). Relevant to Phase-E arb
    venue derivation; possibly not-yet-triggered.
  - **A4 (Phase-E Leg-1 fixture-attribute writers) dispatched** — scope-first sub-agent: implement the
    prediction-specific-file-safe increment (Polymarket `af_fixture_id` resolve + honest Kalshi absence stamping), DEFER
    - report any shared-UAC-schema requirement. Will verify + flip on completion.

- **2026-07-18 (slot-2, autonomous tick 5) — A4 SHIPPED (real code) + verified; E2 dispatched.**
  - **A4 fixture-attribute resolver SHIPPED — `instruments-service@85988ade` (QG-green, 662 lines, 8 files).**
    Adversarially verified: commit real + on origin/LDR; QG-green (sentinel `166934e4` is A4's PARENT — the normal
    quickmerge signature: QG runs on the working tree WITH A4's changes, writes sentinel=pre-commit-HEAD, then commits
    on top); reuses the SAME single-walk sports reader (`candidate_parquet_paths`) + `validate_team_resolution` alias
    index (no new GCS walk); honest-absence closed set; did NOT touch this plan. **Polymarket** soccer now
    resolves+stamps `af_fixture_id`; **Kalshi** soccer stamps honest `UNRESOLVED_TEAM_NAME` pending E2. New
    `adapters/prediction/ fixture_match.py` side-table + `fixture_match_for_instrument_key()` accessor + tests.
  - **DEFERRED to the shared-file window (the A4 column MATERIALIZATION):** UAC `InstrumentRecord` 6 new fields + IS
    `process_write._records_to_dataframe` join (~6-line extension of the `clob_token_ids` block reading the
    side-table) + the MTDS prediction-tick schema. All shared files the active tradfi/cefi slots are migrating → HELD,
    added to the HELD list. The side-table stamping is live now; materializing it as parquet/manifest columns is the
    next unit when those files free.
  - **E2 (Phase-E Leg-2, ~0% matching) dispatched** — scope-first sub-agent: a Kalshi soccer team parser (prediction
    files only) feeding A4's resolver via the shared alias index, + measure the resolution rate + emit the missing-alias
    WORKLIST for the deferred shared-`team_mappings` addition.
  - **Progress metric climbing:** shipped code units this session = A4 (is@85988ade) on top of the already-shipped A2
    1/3/4/5 + §6 (mtds@3397e7ae); plan items advanced A0/§6/CQG/A2/A4; the manifest-canonical climbing metric (11.70%)
    moves only once Phase-B runs (held for the drain window).

- **2026-07-18 (slot-2, autonomous tick 6) — E2 SHIPPED + verified; Kalshi creds confirmed LIVE; window-boundary
  reached.**
  - **E2 (Phase-E Leg-2, Kalshi soccer → af_fixture_id) SHIPPED — `instruments-service@ec8633ac` (QG-green, 187 lines, 3
    files).** Verified: real commit on origin/LDR, working tree clean, reuses A4's `PredictionFixtureResolver` +
    `validate_team_resolution` (no new GCS walk), didn't touch this plan. New `parse_kalshi_soccer_participants(title)`
    - kalshi.py wiring feeds the pair into A4's resolver → Kalshi soccer now resolves `af_fixture_id` (was ~0%).
  - **Live-measured resolution: 82.6% (76/92 real Kalshi soccer fixtures) both clubs already alias-resolvable** (pulled
    92 live from `api.elections.kalshi.com` — **this also CONFIRMS Kalshi creds are LIVE/valid**, not just present).
    100% parsed; 16/92 have exactly one club missing.
  - **MISSING-ALIAS WORKLIST (8 → ~100%, DEFERRED to the shared `team_mappings.py`):** `Bilbao`→`ATHLETIC_CLUB`,
    `Vallecano`→`RAYO_VALLECANO`, `Atletico`→`ATLETICO_MADRID`, `Nottingham`→`NOTTM_FOREST`, `Parma Calcio`→`PARMA`,
    `Stade Brest`→`BREST`, `Paris`→`PARIS_FC` (⚠ NOT PSG — Kalshi renders PSG as `PSG`), `M´gladbach`→`MGLADBACH`
    (U+00B4 acute → normalizer collapses to a space; alias must carry the exact Kalshi rendering).
  - **CAVEAT (real, tracked):** the af_fixture_id join is an exact `(home_cid, away_cid)` lookup; E2 stamps title order
    as home-first (soccer convention). If Kalshi soccer is "Away vs Home" (US convention per UAC `fixture_parsing.py`),
    an alias-resolvable fixture degrades to honest `UNRESOLVED_TEAM_NAME` until order is verified against the FIXTURES
    parquet or the lookup is made order-robust. The 82.6% alias-resolution win is order-independent.

- **2026-07-18 (slot-2) — AUTONOMOUS WINDOW FINAL REPORT (rule 9).** Operator directed `/autonomous`
  "prediction-specific files only" for ~2h while away. **Verdict: every prediction-specific-file-safe, in-order unit is
  DONE; all remaining work is genuinely blocked** (shared UAC/IS files the concurrent tradfi/cefi Phase-B migrations are
  actively editing, an irreversible prod-migration drain window those migrations occupy, or an operator decision) —
  documented in the Deferred ledger above, not abandoned. No `DEFERRED`-without-reason, no fabricated completion.
  - **SHIPPED (real code, QG-green, on origin/LDR):** A4 fixture-attribute resolver `is@85988ade` (Polymarket
    `af_fixture_id` + Kalshi honest-absence, new `fixture_match.py`); E2 Kalshi resolution `is@ec8633ac` (82.6%
    resolvable, was ~0%). Plus verified-already-shipped: §6 provenance fix `mtds@3397e7ae`, A2 identity 1/3/4/5
    `is@0d0c3742` + todo-6 `pm@16272205a`.
  - **AUDIT/CORRECTIONS (evidence-backed, committed):** A0 live baseline (manifest `instrument_type` 11.70% canonical,
    `data_type` 99.55%, CQG clean 81 values) + concrete dedupe worklist; corrected the Ground-truth CQG row (present at
    captured 17,352, not ZERO); verified the CQG-wipe + §6 were already fixed; captured the execution-service
    venue-derivation finding (Phase-E P2). Kalshi confirmed live-credentialed.
  - **HELD (see Deferred ledger, each with its exact blocker):** A4 column materialization (UAC `InstrumentRecord` + IS
    `process_write` + MTDS tick schema); E2's 8 alias additions; A2 todos 2/7/8; §5 `possible_manifest` live-mode
    prefixes (+ BATCH-vs-LIVE semantics decision, REC = union); Phase-B prod migration (drain window); Phase C/D/E
    remainders.
  - **OPERATOR ON RETURN — 3 unblocks:** (1) confirm the concurrent tradfi/cefi migrations are done / lift the
    "prediction-specific files only" constraint → I ship the A4 materialization + E2 aliases + §5 immediately; (2)
    answer §5 (BATCH-satisfied-by-LIVE? A=union [REC] / B=batch-only); (3) authorize the Phase-B prediction prod
    migration in its own drain window (the 11.70%→100% manifest canonicalization). Loop stopped (stall-safety: metric
    can't climb under the current constraint); resumes on any of the above.

- **2026-07-18 (slot-2, autonomous tick 7) — operator answered all 4 decisions; loop RESUMED; shared-file round-1
  landed.**
  - **Operator decisions (2026-07-18):** §5 = **union batch+live**; Phase-B instrument_type = **stamp
    PREDICTION_MARKET** (per-CID; bundle null); **proceed on shared files = YES** (constraint lifted); Phase-B prod
    **RUN = HOLD** (code-ready only, awaits drain-window authorization). Pre-flight confirmed the target shared files
    were quiet (UAC 0 commits/15m, `InstrumentRecord` 27h, `process_write` 4d).
  - **UAC base-tier SHIPPED + verified — `unified-api-contracts@e7ed754e` (QG-green 399s, 7 files).** (1) 6 additive
    nullable `af_fixture_id` fields on `InstrumentRecord` + `INSTRUMENTS_PARQUET_SCHEMA` (model↔schema 1:1 kept); (2)
    E2's 8 Kalshi aliases in `team_mappings` (+ a PSG-non-collision guard); (3) §5 union —
    `live_kalshi`/`live_polymarket_clob` were already emitted (2026-07-11), added the missing
    `live_polymarket_gamma_api` via a prediction-scoped `_EXTRA_LIVE_PROBE_SOURCES_BY_AG` probe (correctly did NOT
    fabricate a `LIVE_POLYMARKET_GAMMA_API` enum member — that source is batch-only). **Rule-11 PASS:**
    cefi/tradfi/defi/sports pipeline_mode template counts byte-for-byte unchanged (16/6/15/0), prediction 5→6. §5
    flipped `pm@4436e59f0`. Flipped in this plan: §5 residuals 5-6 DONE; E2 Kalshi side DONE; A4 header → schema-done +
    materialization-in-flight.
  - **Type-boundary note (carried into round-2a):** the IS side-table `FixtureMatchAttributes` types `af_league_id` int
    / `fixture_date` str, but the operator-decided `InstrumentRecord` fields are str / date — the round-2a
    materialization join converts (`str(af_league_id)`, `date.fromisoformat(fixture_date)`, honest-absence on bad
    values), does NOT re-edit the shipped UAC schema.
  - **Round-2a DISPATCHED** — IS `process_write._records_to_dataframe` join (reads `fixture_match_for_instrument_key` →
    emits the 6 columns; non-prediction rows None; rule-11 cross-AG round-trip verify). Round-1b (MTDS Phase-B migration
    SCRIPT, dry-run) still running; round-2b (MTDS prediction-tick schema) waits for it (same repo). Every sub-agent
    ship adversarially verified before flipping (2 sub-agents flaked this session — an API death + a 0-tool-use dud —
    neither trusted).

- **2026-07-18 (slot-2, autonomous tick 8) — Phase-B migration SCRIPT written + dry-run measured; 2 findings for the
  held run; round-2b re-scoped optional.**
  - **`market-tick-data-service@5392b20b` SHIPPED + verified** (QG-green 238s; 554-line script + 260-line test, 22 pure
    transform tests). `--dry-run` DEFAULT; `--apply` behind `--confirm-prod-write` + a loud guard; prod RUN HELD per
    operator. Additive per-VM-shard write, `resolve_bucket_name`, UTL GCS helpers, single-object `_index` read.
  - **Live dry-run split-confirmation** (756,817 rows): matches A0 — `prediction_trades`→`trades` 3,385; per-CID
    `instrument_type`→`PREDICTION_MARKET` 648,616 (640,701 null + 7,007 lowercase `prediction_market` + 908 leakage);
    `source` 2 empty. Per-CID 4.16%→100%; **all-rows 11.70%→97.40%** (bundle held back).
  - **FINDING (i) — decision-2 was premised on a wrong assumption.** The CQG bundle instrument_type is NOT uniformly
    null: 80,068 = 60,427 `PREDICTION_MARKET` + 17,361 lowercase `prediction` + 2,280 null. So the bundle is
    inconsistent (and its 17,361 lowercase `prediction` are non-canonical). Keeping it unstamped caps all-rows at
    97.40%. **Operator re-decision needed** (annotated on the Phase-B item): normalize bundle→PREDICTION_MARKET (→~100%)
    / enforce SSOT bundle-null (un-stamp 77,788) / leave inconsistent.
  - **FINDING (ii) — additive-shard straggler problem.** `instrument_type`/`data_type` are consolidator dedup-key cols;
    the additive shard adds corrected rows but leaves ~652k OLD rows (doubling). The target-% needs an old-row sweep =
    the "naive direct `_index` rewrite" that resurrects on `--force` rebuild → the held run needs a tombstone/removal
    strategy. Script reports the residual counts; does NOT auto-delete.
  - **Round-2b (MTDS prediction-tick schema) RE-SCOPED to OPTIONAL/DEFERRED** — the ESSENTIAL A4 materialization is
    instrument-level (round-2a, IS `process_write`, in flight); the fixture attrs live on the instrument catalogue, so
    prediction consumers can join by `instrument_id` without a tick-grain denormalization. Adding 6 columns to the
    shared MTDS prediction-tick schema is only warranted if the Phase-E arb path needs tick-grain fixture attrs (like
    the odds-tick side does) — deferred pending that call, to avoid a shared-schema change of uncertain necessity.

- **2026-07-18 (slot-2, autonomous tick 9) — A4 materialization COMPLETE (instrument-level); shared-file CODE round
  done.**
  - **IS `process_write` materialization SHIPPED + verified — `instruments-service@e3ffc613` (QG-green, 4579 passed).**
    The `_records_to_dataframe` join reads `fixture_match_for_instrument_key` and emits the 6 columns, handling the type
    boundary (side-table `af_league_id` int → contract str; `fixture_date` str → date via a guarded
    `_fixture_date_to_date`, honest-absence on bad values); additive/rule-11 is structural (all 6 default None → emitted
    None for every record, overwritten only on a prediction side-table hit; cefi/tradfi/defi round-trip verified None).
    **A4 flipped ✅** — resolver (85988ade) + schema (e7ed754e) + materialization (e3ffc613) = the fixture columns now
    materialize into the instrument parquet end-to-end.
  - **Cross-agent interaction caught + fixed by the IS agent:** E2's honest-absence test used `Bilbao`/`Vallecano` as
    "unresolvable" — but the UAC agent then ADDED those exact aliases (uac@e7ed754e), turning the test RED on LDR. Fixed
    minimally with guaranteed-fictional club renderings ("Zzyzx Wanderers"/"Noexist Rovers") so the honest-absence guard
    survives future alias growth. (A good reminder to keep negative-resolution tests keyed on structurally-impossible
    names, not real-but-currently-absent clubs.)
  - **STATE — the prediction-close-out shared-file CODE work is now essentially DONE.** Shipped + verified this session:
    A2 identity (is@0d0c3742 + pm@16272205a), §6 (mtds@3397e7ae), A4 resolver+schema+materialization (is@85988ade +
    uac@e7ed754e + is@e3ffc613), E2 Kalshi resolution+aliases (is@ec8633ac + uac@e7ed754e), §5 union (uac@e7ed754e),
    Phase-B migration SCRIPT (mtds@5392b20b, dry-run). **Remaining is prod-RUN + small remainders** — see the Deferred
    ledger + the Phase-B item's two findings.

- **2026-07-18 (slot-2, autonomous tick 10) — operator freed the usage limit + re-dispatched /autonomous (4h away).
  Phase-D `-test-` bucket isolation COMPLETE end-to-end; Kalshi order-robust + South-American aliases in flight.**
  - **Session-limit interlude:** two polish sub-agents (Kalshi order-robust, MTDS `-test-` bucket) died mid-run on the
    account session limit (reset 9:40pm). No commits lost; the Kalshi agent left correct-but-uncommitted WIP in IS. On
    the operator freeing the limit, both were resumed.
  - **MTDS `-test-` bucket isolation FIXED end-to-end (flipped Phase-D item):** verify-read `mtds@b06d1e6b` +
    batch-write `mtds@2e50851d` + live-write twin `mtds@86d70de9`. The `-test-` bucket pre-existed; all three paths now
    route prediction to `market-data-tick-pred-test-*` under `IS_TEST_RUN`, cross-AG byte-unchanged, QG-green (6320).
    This unblocks the Phase-D prediction smoke test (the RUN still needs an operator-given `--day`). Follow-ups: stale
    prose in `data_pipeline_e2e_check_2026_07_10.md` + a UTL `get_write_bucket_name` prediction-PROD-only branch
    (non-tick path).
  - **Kalshi order-robust lookup — WIP correct (reviewed) + QG-green, quickmerge racing the hyper-active branch.** The
    fix probes both `(home,away)` orderings against the date-scoped cached lookup and takes home/away from the matched
    FIXTURE's orientation (closes the "Away vs Home title" caveat so the 82.6% Kalshi resolvable rate actually MATCHes).
    A peer FF staled the sentinel on first quickmerge; an atomic re-gate+quickmerge retry loop (background) is landing
    it.
  - **South-American club aliases (odds-side ~66% gap) dispatched** — UAC sub-agent enumerating the failing Chile (265)
    / Brazil / Argentina renderings from the FIXTURES parquet, verifying each against API-Football canonical ids,
    additive to `team_mappings`.

- **2026-07-18 (slot-2, autonomous tick 11) — Kalshi order-robust LANDED; data_pipeline prose reconciled.**
  - **Kalshi order-robust lookup SHIPPED — `instruments-service@ba3528d4`** (landed attempt-1 via the atomic
    re-gate+quickmerge retry loop after the first quickmerge staled on a peer FF). Probes both `(home,away)` orderings
    against the date-scoped cached lookup, takes home/away from the matched FIXTURE's orientation → the 82.6% Kalshi
    resolvable rate now actually MATCHes regardless of "Away vs Home" title order; Polymarket benefits too. E2 order
    caveat CLOSED. Tests cover reversed-title MATCH (both venues) + the "both orderings = one GCS read" assertion.
  - **Reconciled `data_pipeline_e2e_check_2026_07_10.md` todo-13 prose** (`pm@11293b9a3`) — the "prediction has no
    `-test-` sibling bucket" claims (L267/683/1030) were made false by the `-test-` bucket fixes; corrected in place.
  - **South-American aliases agent still running** (UAC, enumerate+verify+add for Chile/Brazil/Argentina).

- **2026-07-18 (slot-2, autonomous tick 12) — South-American aliases LANDED; E2 fully DONE; exec-service venue bug (real
  one) surfaced + in flight.**
  - **South-American club aliases SHIPPED — `unified-api-contracts@98d757f9`** (landed attempt-1). Chile + Argentina
    clubs (Universidad Católica (CHI), Audax Italiano "A. Italiano", Estudiantes L.P., Argentinos JRS, Central Córdoba
    de Santiago, Colo-Colo, O'Higgins, …), EACH verified against the API-Football FIXTURES parquet `af_home_name` (not
    guessed), canonical ids pre-existed. Closes the odds-side ~66% fixture-match cap. **E2 (fixture matching to ~0%)
    flipped ✅ — both the Kalshi side AND the South-American side done + the home/away order caveat closed.**
  - **exec-service venue-derivation: `get_venue_from_instrument_id` fixed `execution-service@e3707472`** (robust
    known-venue discrimination via UAC `VENUE_CATEGORY_MAP`, cefi/defi unchanged, QG-green) — but it has NO prod caller
    (latent). **The agent surfaced the REAL bug:** the sibling `utils/instruction_type.py::extract_venue` (~40 prod call
    sites — matching engines, preflight_gate, `infer_instruction_type`, `get_asset_group_from_instrument_id`) has the
    identical `split(":")[0]` and HARD-CRASHES (`UnknownVenueError`) on a type-first prediction/sports id. Dispatched
    the fix (same additive robust-parse; venue-first byte-unchanged — the safety requirement).
  - **Multi-agent-branch note:** the aliases + Kalshi WIPs each landed via an atomic re-gate+quickmerge retry loop after
    a peer FF staled the first quickmerge (the hyper-active branch drifted 40+ commits during the session). The
    exec-service ship correctly used the sanctioned `--skip-preflight` when my aliases WIP showed as a dirty dep.

- **2026-07-18 (slot-2) — AUTONOMOUS WINDOW FINAL REPORT (rule 9): all prediction close-out CODE SHIPPED + verified.**
  The operator's originating question — _do we have canonical football fixture ids linking sports→prediction so we can
  arb live-odds vs Polymarket vs Kalshi?_ — is now answered IN CODE, not just in the plan. Every implementable unit is
  shipped, QG-green, on `origin/live-defi-rollout`, and adversarially verified (git + code read) — 3 sub-agents flaked
  on API/session-limit errors and NONE was trusted; each ship was re-verified.
  - **Fixture-id threading (the ask):** Polymarket + Kalshi soccer resolve `af_fixture_id` (resolver `is@85988ade`,
    Kalshi parser `is@ec8633ac`, order-robust `is@ba3528d4`), materialized as real instrument-parquet columns (UAC
    schema `uac@e7ed754e` + IS `process_write` join `is@e3ffc613`). Reuses the SAME single-walk fixtures reader +
    `validate_team_resolution` index the odds side uses — so a Polymarket, a Kalshi, and a bookmaker-odds row for the
    same match now share one `af_fixture_id`.
  - **Matching to ~0% gap:** Kalshi ~0% → 82.6% → ~100% (8 Kalshi aliases `uac@e7ed754e`); South-American odds gap
    closed (`uac@98d757f9`, each alias verified vs the API-Football FIXTURES `af_home_name`); home/away order-robust.
  - **Canonical/dedupe audit + migration:** A0 live baseline (manifest `instrument_type` 11.70% canonical) → Phase-B
    dry-run migration script `mtds@5392b20b` (measured 11.70%→97.40%); §5 union path-templates `uac@e7ed754e`; §6
    provenance `mtds@3397e7ae`; A2 identity 5/8.
  - **Phase-D smoke isolation:** the prediction `-test-` bucket now used by verify-read + batch-write + live-write
    (`mtds@b06d1e6b/2e50851d/86d70de9`), cross-AG byte-unchanged.
  - **Bonus data-correctness:** execution-service venue-derivation fixed at BOTH sites (`exs@e3707472` + the
    production-critical `exs@730fcd1c0` — `extract_venue` hard-crashed on type-first ids); + a `data_pipeline` prose
    reconcile.
  - **HELD — needs the operator (NOT abandoned; each is one decision/authorization away):** (1) the Phase-B prod
    migration RUN (dry-run script ready; operator chose code-ready-only) + its TWO findings that revise the plan — the
    CQG bundle `instrument_type` is inconsistent not null-by-design (normalize it → ~100% vs 97.40%?), and the
    additive-shard leaves ~652k dedup-key stragglers needing a removal strategy; (2) the Phase-D smoke RUN needs an
    operator-given `--day`; (3) minor follow-ups: UTL `get_write_bucket_name` prediction-PROD-only non-tick path,
    `book_snapshot_5` prediction-MVP-rule reconcile, and the A2 residuals (catalog regen / gcs_paths.py / MDPS). Loop
    stopped — the metric can't climb further without an operator decision/authorization; resumes on any of them.

- **2026-07-19 (slot-2, autonomous tick 14) — operator resumed /autonomous; two code-ready follow-ups.**
  - **`book_snapshot_5` MVP-scope RECONCILED — `unified-api-contracts@53bf01d6`** (flipped its P1). It was an un-updated
    outlier (in all 3 data registries, absent from `PredictionMvpRule`); added it + config-version bump + rule-11
    cross-AG-unchanged tests. `--mvp-only` prediction now tests all 4 shards.
  - **Phase-B script completion IN FLIGHT** (MTDS retry-loop) — a sub-agent wrote the `--bundle-mode {normalize,leave}`
    flag (finding 1) + the straggler-removal design/code (finding 2, `--remove-stragglers`: pause-consolidator +
    snapshot + in-place `_index` CAS rewrite, guarded, NOT run) + found the writer ROOT:
    `manifest_finalize. _finalize_prediction_bundles` stamps lowercase `instrument_type="prediction"` on bundle rows (so
    the bundle is emitted lowercase, not null — explains the inconsistency; the writer-root-fix is on the operator
    checklist so a `--force` rebuild doesn't resurrect stragglers). Landing via retry-loop; prod RUN still HELD.
  - **Reminder — the prod-migration RUN + its two decisions remain operator-gated** (bundle-mode choice;
    straggler-removal mechanism review). The script now SUPPORTS both, defaulting to my recommendations, one
    authorization away.
