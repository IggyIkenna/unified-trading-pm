---
doc_type: plan
title:
  Prediction Phase A-B residuals — code-ready writers + manifest migration follow-through (split from
  prediction_consolidated_closeout_2026_07_18)
summary: >-
  Phases A (get-the-code-ready — capture path, canonical-identity writers, venue-perps residuals, fixture-attribute
  writers) and B (manifest/catalogue migrations) of the prediction consolidated close-out, split out verbatim (line-cap
  remediation, 2026-07-24) — most items already shipped and verified; residual open work is finishing the
  capture-incident remediation, the shared canonical-builder QG, the venue-perps/live-CLOB-depth residuals, the
  historical fixture-match-attribute backfill, and the ambiguous-canonical-value operator-decision gate.
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
    capture-incident,
    canonical-identity,
    manifest,
    canonicalisation,
    fixture-attributes,
    venue-perps,
    clob-depth,
  ]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
sequential: true
source: >-
  Split from `prediction_consolidated_closeout_2026_07_18.md` (Phase A section, lines 177-266, and Phase B section,
  lines 267-343, of that doc as of 2026-07-18/2026-07-24) per the operator-approved line-cap remediation triage
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries"). Content moved verbatim, not summarized. Phase A and Phase B are combined into one child per the triage's
  specific guidance for this plan ("Phase A-B residuals"). `sequential: true` added 2026-07-24 (plan audit finding) to
  encode this doc's own "Phase B — run the migrations (gated on Phase A green)" header text as a real ordering — this is
  a WITHIN-plan A-before-B ordering, not a cross-plan gate, so `sequential` (not `depends_on`) is the correct mechanism.
---

# Prediction Phase A-B residuals — code-ready writers + manifest migration follow-through

> **Split from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-24).** This is the Phase A + Phase B sections
> of that close-out, moved verbatim (Phase A = get-the-code-ready; Phase B = run the migrations, gated on Phase A
> green). For the full historical execution narrative (Progress Log, ticks 1-31, 2026-07-18 through 2026-07-20) and
> shared cross-phase context (the Ground-truth verdict table, the prediction shard-atom definition — the CQG-bundle vs
> per-CID `instrument_type` key distinction that is the root of the Phase-B canonicalisation work below — and the MVP
> universe scope), see the parent doc. Sibling phase children: `prediction_phase_c_data_status_ui_2026_07_24.md` (Phase
> C), `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (Phase D),
> `prediction_phase_e_football_arb_live_2026_07_24.md` (Phase E — gated on this plan + Phase D, since this plan carries
> the Phase-B fixture-attribute backfill Phase E depends on).

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

- [ ] [BACKEND] P0. **Finish the prediction canonical-identity migration — now 7/8 done (confirmed 2026-07-19), only
      todo 2 open.** Shipped: todos 1/3/4/5 (`instruments-service@0d0c3742` — adapter `underlying` from
      `classify_*_to_canonical_group`, cross-venue `canonical_instrument_id`, titles-map decision, Polymarket sports
      `build_fixture_id`) + todo 6 as VERIFY (`unified-trading-pm@16272205a` — downstream `instrument_id` uniqueness
      SAFE, venue embedded by construction) + todo 7 (`unified-api-contracts@511a9c62` — `gcs_paths.py` bucket
      abbreviation flip, migration gate re-confirmed live 2026-07-19: legacy `market-data-tick-prediction-prd-*` 404s,
      `market-data-tick-pred-prd-*` is the sole live SSOT) + todo 8 (MDPS UAC-pin — assessed 2026-07-19, NO bump needed;
      the MDPS→UAC dep is an in-workspace editable range-pin that absorbs the 0.x flip by design; MDPS assertions
      already reconciled at `market-data-processing-service@27bce46`/`@5febb77`). **Only todo 2 remains open:** full
      `prod/catalog.parquet` regen (`build_instrument_catalogue.py --asset-group prediction` against real GCS data,
      manifest-verified row counts) to bake in the shipped `underlying` + cross-venue `canonical_instrument_id` fields.
      Real scoping/smoke-test/ETA done 2026-07-09 (~21k blobs, ETA ~25-40 min for a full non-dry-run regen); the full
      run is intentionally NOT executed yet (staged rollout, gated on the in-flight shared canonical-identity migration
      so it doesn't bake transitional/half-migrated ids into the persisted catalogue — schedule after that migration
      settles). **NOTE**: a daily/weekly cron (`lifecycle-catalogue-regen-prediction-daily`) already regenerates this
      catalogue on schedule for OTHER fixes (base_asset whitespace @49ff29ea, `af_fixture_id` propagation) — verify
      whether it has ALREADY carried the underlying/canonical_instrument_id fields through before treating this as a
      fresh manual-run requirement. Source: `prediction_canonical_identity_migration_2026_07_08.md` (folded in +
      archived 2026-07-21, consolidation pass — all other todos resolved, this was its sole remaining open item).
      **Phase-E Leg-1 seam** = todo 5 (done Polymarket; Kalshi extended in Phase E). (repos: instruments-service,
      unified-api-contracts)
- [ ] [BACKEND] P1. **Route every prediction id/underlying/CQG writer through the shared canonical builder + a QG that
      fails a non-canonical prediction `instrument_id`/`canonical_question_group` on write** — re-drift prevention, so
      new writes can't reintroduce the dupes A0 enumerates. (repos: instruments-service, market-tick-data-service,
      unified-api-contracts)

### A3 — Venue-perps + live CLOB depth residuals (fold)

- [ ] [BACKEND] P1. **Close the 12 residuals on Kalshi/Polymarket perpetual futures + live CLOB depth/quotes** (funding
      / basis / dispersion arb inputs). `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` (12 open of 85) —
      **split + archived 2026-07-24** (plan line-cap remediation) into
      `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (1 open),
      `prediction_live_clob_depth_capture_2026_07_24.md` (2 open), and
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (9 open + 2 in-progress); the residual-fold above should
      now target those 3 successors, not the archived original. (repos: market-tick-data-service, unified-api-contracts,
      features-service)

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
      documented in the script docstring + printed by dry-run. **✅ MANIFEST `--apply` APPLIED 2026-07-19 (tick 18) —
      `market-data-tick-pred-prd/_index` CAS REPLACE, generation `…161980856`→`…195626006`, 745,107 rows, 12,524
      stragglers removed, `instrument_type` 11.80%→100% / `data_type` 100% / `source` 100%, 0 captured cells lost;
      snapshot `_index/backups/pre_prediction_canonicalize_20260719T103301075148Z.parquet`; consolidator paused→resumed
      (ENABLED). Manifest targets (a)(b)(c) DONE; catalogue `base_asset` (d) = the separate A2 catalogue regen (below).
      Durability caveat: per-CID + `prediction_trades` re-accumulate until the items-2+3 follow-up lands.**
- [x] [DATA] P1. **✅ DONE 2026-07-19 (tick 21) — item 2 `market-tick-data-service@71761d7f` (per-CID shard-key itype
      folds to canonical `PREDICTION_MARKET`, prediction-venue-gated RULE-11, +tests; note the writer actually carried
      lowercase `prediction_market` not null, so the fold is unconditional) + item 3 `unified-api-contracts@1794f3e5`
      (`prediction_trades` dual-seed retired across 7 files, +34/−186; adversarially verified no live consumer requires
      it; QG green). The Phase-B `--apply` cleanup is now DURABLE (per-CID no longer re-accumulates; the phantom
      `prediction_trades` expected rows are gone). Writer-root durability COMPLETION (items 2+3 of the migration
      checklist step 0) — the Phase-B `--apply` cleanup is DURABLE for the CQG bundle (item 1 SHIPPED
      `market-tick-data-service@1ec415f8`) but TRANSIENT for per-CID + `prediction_trades` until these land** (surfaced
      tick 17): (2) canonicalize the prediction per-CID `instrument_type` at the **shard-key construction** UPSTREAM of
      the generic per-CID writer (which stamps `itype_key` verbatim, RULE-11 — do NOT canonicalize in the generic
      writer; 640,701 per-CID null rows re-accumulate otherwise); (3) retire the legacy `prediction_trades` seed key —
      `PREDICTION_MVP_SEED_INSTRUMENTS` dual-seeds `("VENUE","trades")` + `("VENUE","prediction_trades")` "during
      rollout" (retired 2026-04-19); rollout-completion across 6 UAC files (`defi_prediction_instrument_seeds`,
      `data_type_capability`, `schema_spec`, `_schema_spec_prediction`, `expected_coverage`, `market_data_categories`) —
      DELICATE (breaks un-migrated callers; affects the `expected_unattempted` denominator) → verify no live consumer
      still emits/expects `prediction_trades` before removing. Until both land, a periodic re-run of
      `canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers --apply` closes the drift. (repos:
      market-tick-data-service, unified-api-contracts)
- [ ] [DATA] P0. **Backfill the fixture-match attributes (A4 columns) across historical Polymarket + Kalshi soccer** —
      resolve `af_fixture_id` per market from the fixtures parquet (canonical `home_id`/`away_id` + `af_league_id` +
      `fixture_date`) OR by parsing the human-readable canonical name, stamping `af_fixture_match_status`. Honest nulls
      where unresolved; the match-rate summary line logged per (league, day). (repos: market-tick-data-service,
      instruments-service)
- [ ] [DECISION] P1. **Any prediction dimension value whose canonical form is AMBIGUOUS = BLOCKED-OPERATOR-DECISION** —
      surface the A0-enumerated ambiguous set to the operator (options + a marked recommendation) rather than guessing;
      does not block the unambiguous majority of the migration.
- [ ] [DATA] P0. **Re-verify + close the `instrument_type` casing/canonicalisation gap to literal 100% (operator,
      2026-07-24) — the historical numbers in this doc DISAGREE and need reconciling, not just re-citing.** The tick-18
      `--apply` (line 229 above) measured `instrument_type` 11.80%→100% live on 2026-07-19; but the cross-AG D1 ruling
      snapshot (`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1) measured prediction at only 99.46% UPPER one
      day later (2026-07-20) — the two don't agree, most likely because ongoing captures between the two reads
      re-introduced non-canonical rows (the durability gap items 2+3 above were still open at the 07-19 apply and only
      closed at tick 21). **Done when**: a FRESH live manifest read today shows literal 0 non-canonical
      `instrument_type` rows (not either historical snapshot) AND the deployment-ui data-status Distinct Values panel
      confirms 0 non-canonical entries for prediction. This is the cross-AG standard — tradfi/cefi/sports all target the
      same 100% bar; DeFi is the sole exception (genuinely mixed per-instrument_type, tracked separately in
      `defi_consolidated_closeout_2026_07_18.md`).

## Progress Log

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase A + Phase B sections verbatim (14 todos total: 5 done / 9 open at split time). See the parent's
  Progress Log (ticks 1-31, especially the A0/A2/A4/§5/§6 and Phase-B `--apply` entries — ticks 1, 4-9, 16-18, 21) for
  the full session-by-session history of what is already shipped here. Future work on this plan logs new entries below.
