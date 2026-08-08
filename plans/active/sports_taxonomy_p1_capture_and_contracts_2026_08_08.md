---
doc_type: plan
title: Sports taxonomy P1 — restore raw capture, then land the venue/data_type contracts
summary: >-
  Phase 1 of the sports venue/data-type canonicalisation chain authored from the 2026-08-08 live audit. Two blocks, in
  order. Block A restores raw sports capture, which has been DEAD since 2026-07-26 while the derived layer kept
  computing from a frozen source — nothing downstream is trustworthy until it is live, and a migration over a frozen
  corpus would have to be redone. Block B lands every UAC contract + codex change the operator ruled on 2026-08-08 —
  venue means "whose price is this" plus a separate executable flag, ODDS_API/FOOTYSTATS leave the venue axis for
  source-only, `trades` merges into a single lowercase `odds` with in_play as a column, a first-class `horizon` axis
  un-overloads `timeframe`, `arbitrage_opportunity` leaves the data layer, exchange_odds/fixed_odds is derived from the
  venue rather than stamped, markets/outcomes/settlements are retired, and the whole sports data_type vocabulary merges
  to one lowercase form. Contracts only — no GCS or manifest mutation happens in this phase.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, canonicalisation, venue-axis, data-types, horizon-axis, contracts, capture-outage, honest-coverage]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/active/sports_taxonomy_p4_backfill_2026_08_08.md,
    /plans/active/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md,
    /plans/active/issues/mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md,
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /codex/02-data/sports-data-types-catalog.md,
    /codex/02-data/sports-2020-06-data-floor.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/_sports_venue_constants.py,
    unified-api-contracts/unified_api_contracts/registry/expected_coverage.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
    /codex/02-data/sports-data-types-catalog.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — 27 operator rulings"]
locked_by:
locked_since:
---

# Sports taxonomy P1 — capture restoration + contracts

> **Chain**: P1 (this) → `p2_migration` → `p3_consumers` / `p4_backfill`. Later phases declare `depends_on` +
> `gate_on_depends: true` on this one. **This phase mutates NO GCS object and NO manifest row** — it lands contracts and
> writer behaviour only, so the migration phase has a settled target to migrate toward.

## The audit that produced this (evidence, measured 2026-08-07/08)

Read against the live prod manifest `market-data-tick-sports-prd-.../_index/availability_index.parquet` (615,130 rows)
and the honest-coverage rollup the Distinct-Values panel reads.

**The panel is not telling the truth.** It renders 10 venues / 7 data types and "0 non-canonical". The manifest carries
**31 venues and 10 data types**. `deployment-api::_distinct_values.py::enumerate_distinct_values` drops blanks and
everything in `_ACCEPTED_EXCEPTIONS` BEFORE enumerating — hiding 21 fan-out bookmakers (~340k shards), `KALSHI`, a blank
venue (2,490 shards), and the uppercase `ODDS`/`ODDS_MOVEMENT`/`ODDS_SNAPSHOT` data types. **"0 non-canonical" was
achieved by exclusion, not canonicalisation.**

**Every sports row is aggregator- or vendor-sourced. There is no venue-native capture anywhere**, and
`VENUE_TO_ADAPTER_KEY` returns `__no_adapter_yet__` for all 10 panel venues including Betfair:

| source                     | shards  | what it is                                                        |
| -------------------------- | ------- | ----------------------------------------------------------------- |
| `odds_api`                 | 445,264 | the aggregator, fanned out to 27 bookmaker venues                 |
| `mdps_odds_horizon_bucket` | 125,400 | our own derived output                                            |
| `footystats`               | 23,681  | a stats vendor                                                    |
| `polymarket_clob`          | 20,785  | prediction-market rows filed under sports (all `empty_confirmed`) |

**Data-type reality** (captured shards, live manifest):

| data_type                          | captured | date span                   | what it really is                       |
| ---------------------------------- | -------- | --------------------------- | --------------------------------------- |
| `trades`                           | 375,257  | 2020-06-06 → **2026-07-26** | bookmaker QUOTES. Nothing was traded.   |
| `odds_horizon_bucket`              | 135,980  | 2020-06-06 → 2026-08-06     | `trades` re-labelled by time-to-kickoff |
| `odds_snapshot`                    | 16,521   | **2026-07-25 → 08-06**      | LOCF resample of `trades`               |
| `odds_movement`                    | 16,470   | **2026-07-25 → 08-06**      | OHLC candle of `trades`                 |
| `arbitrage_opportunity`            | 16,441   | **2026-07-25 → 08-06**      | a strategy signal stored as market data |
| `odds`                             | 16,207   | 2020-06-06 → **2026-04-14** | footystats pre-match odds               |
| `ODDS`                             | 6,306    | 2020-06-05 → **2026-04-14** | the SAME thing, uppercase               |
| `trades_inplay`                    | 111      | **2022-09-07 → 2022-11-09** | a 2-month 2022 fossil, blank venue      |
| `markets`/`outcomes`/`settlements` | **0**    | —                           | declared in UAC, never written          |

`timeframe` is **overloaded**: candle grains (`15m`/`1h`) for derived types, time-to-kickoff labels (`T-0`…`T-24h`) for
`odds_horizon_bucket`, `T-0` for raw. Two meanings, one column.

`instrument_type` is **overloaded**: `odds`/`exchange_odds`/`fixed_odds` (product class) for raw, market tokens
(`MATCH_ODDS`, `OVER_UNDER_2_5`, `MATCH_ODDS_LAY`) for derived.

## Operator rulings this phase implements (2026-08-08)

1. **Venue means "whose price is this"** — keep all 27 books as venues; add a SEPARATE `executable` predicate.
2. **`ODDS_API` and `FOOTYSTATS` leave the venue axis entirely** — they are sources, and the manifest's `source` column
   already carries them correctly.
3. **Bare `BETFAIR`** stops being a data-axis venue and becomes the **operator-group parent**.
4. **`trades` → `odds`** (one raw type); `in_play` becomes a column; `trades` is RESERVED for genuine matched volume and
   will honestly report 0 captured everywhere.
5. **Add a first-class `horizon` axis**; fold `odds_horizon_bucket` into `odds`; `timeframe` reverts to candle grain.
6. **`arbitrage_opportunity` moves to the signals/features layer** with a real multi-venue key (done in P3).
7. **Merge the sports data_type vocabulary to ONE lowercase form** — this OVERTURNS the standing codex ruling.
8. **Delete `markets`/`outcomes`/`settlements`**; ML labels come from IS `fixtures_outcomes`/`matches`.
9. **Retire the `exchange_odds`/`fixed_odds` instrument_type split** — derive it from the venue.
10. **Model horizons gain BOTH T-2h and T-6h**.
11. **Betfair Exchange**: adapter scaffold only, `BLOCKED-CREDENTIALS`.

---

## Block A — restore raw capture (P0, gates everything else)

- [x] ✅ [DATA] P0. **Diagnose why raw sports capture stopped on 2026-07-26.** Measured: `trades` max date is
      2026-07-26; a recursive listing of `raw_tick_data/by_date/day=2026-08-01/` returns ZERO objects;
      `odds_horizon_bucket` and the derived types kept writing through 2026-08-06 off the frozen source. Two existing
      issue docs describe candidate causes (`mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md` — force-fetch
      writing no parquet; `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` — T1-recon OOM). READ both before
      diagnosing; they may already carry the answer. Do NOT conclude from a grep — read the writer and check live. —
      **DIAGNOSED 2026-08-08 (slot 3)**. Full root cause already in
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`; confirmed live and code-level. Summary: (1)
      `market-tick-data-service@410d7569` (2026-07-26) removed the future-date guard that had previously blocked all
      same-day SPORTS dispatches from reaching `OddsApiAdapter._fetch_all_leagues`; (2) `fire_trigger` in
      `deployment-service/deployment_service/sports_trigger_scheduler.py` dispatched `market-tick-data-service` with NO
      `--league` arg for fixture-proximate triggers, so `_candidate_leagues(registry, None)` returned all 30
      Prediction-tier leagues (~30x overfetch per single-fixture event); (3) the job OOM'd at 8Gi before writing any
      manifest row, so `_apply_freshness_skip` never fired → crash loop every 5 min starting ~2026-07-27. All fixes
      confirmed live: memory bump (16Gi/4cpu), `--league` scoping (`deployment-service@4e0e03d`), pre-flight
      source-scoping (`market-tick-data-service@afa8eaec`), freshness-skip demotion
      (`unified-trading-library@2e072fbf`). Live capture confirmed restored: Cloud Run executions completing (8hlxb
      2026-08-08T00:30Z wrote 293594 records for date=2026-08-07), `data_type=trades` parquet confirmed in GCS under
      day=2026-08-07/pipeline_mode=batch_odds_api/ (20 bookmaker venues present). `odds_horizon_bucket` and derived
      types were fed from frozen source because MDPS has no staleness guard against a dead raw source — this is the
      Block A todo-3 defect. unified-trading-pm (this plan)
- [x] ✅ [DATA] P0. **Restore capture and prove it with a MEASURED terminal verdict**: a fresh capture day writes real
      parquet objects at the canonical path AND lands `captured` manifest rows with non-zero `row_count`. "The job
      exited 0" is not proof — the outage's whole signature is a job that succeeds while writing nothing. Cite the day,
      the object count, and the manifest row count. — **MEASURED 2026-08-08 (slot 7)**. Day=2026-08-07:
      `market-data-tick-sports-prd-central-element-323112` contains **5,747 parquet objects** under `day=2026-08-07`.
      Manifest (`instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`): **225
      `capture_status=captured` rows** for `data_type=trades`, ALL with `row_count > 0`, total row_count sum =
      **9,154**. Sources: `odds_api`. Sample venues: FANDUEL, BETONLINEAG, BET888SPORT, CORAL, PINNACLE (25-bookmaker
      fan-out confirmed). Post-outage date coverage (trades, captured): 13 days spanning 2026-07-25 → 2026-08-07 with a
      2026-08-04 gap (previously noted). Verdict: capture IS real, NOT the silent-zero pattern the outage exhibited.
      unified-trading-pm
- [x] [CODE] P0. **Add a staleness guard so a frozen raw source can never again silently feed the derived layer.** MDPS
      must refuse (loudly) to derive `odds_snapshot`/`odds_movement`/`horizon` output for a day whose raw source shard
      is absent or older than a bounded threshold, rather than emitting derived rows off stale input. This is the defect
      that let 12 days of derived data be produced from a dead feed. Wire the failure into the existing
      data-pipeline-alerts registry rather than inventing a new alert path. ✅ market-data-processing-service@41cdb702d
      — `DependencyChecker.check_sports_raw_source_captured` reads MTDS manifest for SPORTS bucket;
      `_process_one_category` blocks odds_snapshot/odds_movement/odds_horizon_bucket when manifest has no
      `capture_status=captured` row for trades/odds; emits `DP_DOWNSTREAM_BEFORE_UPSTREAM` alert; fails-open on manifest
      read errors. 9 unit tests green. QG: ✅ ALL QUALITY GATES PASSED.

## Block B — contracts (P0/P1, after Block A's diagnosis, parallel within the block)

- [x] ✅ [CODE] P0. **Split the venue axis in UAC**: `venue` = the book whose price it is; a NEW `executable` predicate
      derived from `VENUE_TO_ADAPTER_KEY` (true only when a real adapter key exists, not `__no_adapter_yet__`). Remove
      `ODDS_API` and `FOOTYSTATS` from `VENUES_BY_ASSET_GROUP["sports"]`. Promote the 21 currently-excepted fan-out
      bookmakers INTO the canonical set — under the new model they are legitimate venues, so
      `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` should shrink toward empty rather than grow. Every venue in the
      set must resolve a `SportsVenueType`, an auth method, an instrument-type set, a fee model and an alpha profile —
      SMARKETS currently resolves NONE of these despite being canonical, and that gap must close here. — **DONE
      2026-08-08 (data_engineering, agt-9e871f, slot 8)** — `unified-api-contracts@05a709fd`. Added
      `venue_adapter_keys.is_venue_executable()`. Removed ODDS_API from the venue axis (it's a source; also dropped its
      now-stale `VENUE_TO_ADAPTER_KEY`/`VENUE_DATA_TYPE_CAPABILITIES`/`EXPECTED_COVERAGE_BY_ASSET_GROUP` entries + 2
      hardcoded test assertions). FOOTYSTATS was never in `VENUES_BY_ASSET_GROUP` (only in the noncanonical-exception
      set) so there was nothing to remove there; confirmed it stays excepted for its own unrelated two-registry-
      disjointness reason. Promoted all 22 real bookmakers from `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`
      (measured count, not the todo's approximate "21" — FOOTYSTATS is the 23rd, non-bookmaker member) — added
      `UNIBET_EU`/`UNIBET_UK` as new venue constants (didn't exist yet). Every venue in the resulting 32-member
      `VENUES_BY_ASSET_GROUP["sports"]` now resolves all 5 classification dicts (verified via direct import, zero gaps)
      — closed SMARKETS (added to `SPORTS_EXCHANGE_VENUES` + an explicit `SPORTS_AUTH_MAP` entry) and the same
      pre-existing gap on `BETFAIR_EX_UK`/`BETFAIR_EX_EU` (auth only). Also fixed an adjacent pre-existing bug: SMARKETS
      was in `registry/__init__.py`'s `__all__` since 2026-07-30 but never actually imported (would have broken any
      direct `from unified_api_contracts.registry import SMARKETS`). Full `quality-gates.sh` green (12528 passed) after
      2 rebases onto concurrent slots' commits to the same plan (arb-operator-group bugfix, horizon-axis todo) — no
      conflicts.
- [x] [CODE] P0. **Make bare `BETFAIR` an operator-group parent, not a venue.** Remove it from the data-axis venue set;
      add a real venue→operator hierarchy in UAC that `BETFAIR_EX_UK`/`EX_EU`/`SB_UK` roll up to. Coordinate with
      `/plans/active/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md`, which ships the consuming fix FIRST
      — this todo must not regress that fix; if the bugfix already added the hierarchy, extend it rather than
      duplicating it. 5. ✅ unified-api-contracts@49e83239 — removed BETFAIR from SPORTS_EXCHANGE_VENUES,
      VENUES_BY_ASSET_GROUP["sports"], VENUE_DATA_TYPE_CAPABILITIES, and representative_sample.py; updated 5 test files
      (test_sports_schemas, test_venue_context_integration, test_instrument_generator, representative_sample) to use
      BETFAIR_EX_UK as the canonical data-axis exchange representative; hierarchy already in place via arb bugfix
      (OPERATOR_GROUP_VENUES@b9a0be80); QG green (12533 passed).
- [ ] [CODE] P0. **Collapse the raw odds vocabulary to a single lowercase `odds`.** `trades` → `odds`; footystats
      `ODDS`/`odds` → `odds`; the two populations stay distinguishable via the existing `source` column (`odds_api` vs
      `footystats`), which is exactly the axis that should carry that distinction. Add an `in_play` boolean column
      (derivable from `bm_minutes_to_kickoff < 0`) and retire `trades_inplay`. Re-reserve `trades` for genuine matched
      volume with ZERO current producers. **Consumer inventory** (per
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`): UAC `market_data_categories.py`
      (DATA_TYPES_BY_ASSET_GROUP, FREQUENCY_MAP, CONTRACT_REGISTRY, `_is_consumable_trades_blob` matches FILENAME not
      data_type column — grep misses it); MTDS `odds_api_adapter.py` (writer); MDPS `canonical_writer.py` +
      `_process_one_category`; IS `enumerate_expected_universe.py`; features-service reads `odds_horizon_bucket` shards
      by GCS path prefix via `_ODDS_BUCKETED_PREFIXES` (NOT data_type column — a data_type rename does NOT find it);
      ml-service `sports_feature_loader._ODDS_BUCKETED_PREFIXES` (same); deployment-api distinct_values +
      honest-coverage rollup. Full exhaustive enumeration: P2 `[REVIEW] P0`.
- [x] ✅ [CODE] P0. **Add a first-class `horizon` axis** to the manifest/shard contract and stop overloading
      `timeframe`. `timeframe` reverts to meaning candle grain only. `odds_horizon_bucket` stops being a data_type and
      becomes `odds` at a horizon. Enumerate every reader of the current `timeframe` column BEFORE changing it (see the
      rename process rule below) — MDPS, the features loader's `_ODDS_BUCKETED_PREFIXES` path match, and the
      honest-coverage rollup all read it. — **LANDED 2026-08-08 (slot 3, data_engineering)**:
      `unified-api-contracts@685b288a` adds `SPORTS_HORIZONS` (T-24h..T-0) as the SSOT horizon vocabulary, separate from
      `TIMEFRAMES`/`timeframe` (candle grain only), plus `is_valid_horizon()`. Registers a NEW, additive
      `SPORTS_ODDS_HORIZON_BUCKET` SchemaContract at `CONTRACT_REGISTRY[("sports","odds","odds_horizon_bucket")]` — this
      data_type had NO contract at all before — with `horizon` as a required column, instead of bolting an optional
      column onto `SPORTS_ODDS_TRADES` (confirmed that breaks `validate_dataframe` for every currently-shipping
      unbucketed row — the same `validate_dataframe` ignores `nullable`/`required` footgun `broker`/`client` were
      removed for on this exact contract). Added the `("sports","odds")` → `odds_horizon_bucket` entry to
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`. 42/42 UAC sports-contract unit tests green; full UAC QG green.
      `market-data-processing-service@3e0fb852` wires `SportsBucketAssignmentAdapter.TIER1_HORIZONS`'s bucket NAMES to
      the new UAC SSOT with a module-load drift-guard assertion (this adapter is the sole writer of horizon-bucketed
      rows) — calibration values (target_minutes/staleness_cap) stay local, only the name vocabulary moved. No behavior
      change; 80/80 bucket-adapter unit tests green; full MDPS QG green. **Readers enumerated but NOT changed this
      phase** (contracts-only, no GCS/manifest mutation, per the plan header):
      `features-service/features_service/sports/data/gcs_reader.py` (`_BUCKETED_ODDS_*_PREFIX`,
      `read_bucketed_odds`/`read_odds_at_horizon`, physical column `horizon_name`) and the honest-coverage rollup
      (deployment-api `_distinct_values.py`) both still read the CURRENT `timeframe`-carries-horizon manifest shape —
      neither repo is in this plan's `repos:` list, and the physical `AvailabilityRecord.timeframe` column lives in
      `unified-trading-library`, also out of this plan's `repos:` list. The P1 phase header is explicit ("mutates NO GCS
      object and NO manifest row... lands contracts and writer behaviour only, so the migration phase has a settled
      target to migrate toward") — the physical manifest-column split (UTL) and the reader updates (features-service,
      deployment-api) are P2/P3 scope once the data re-stamp actually happens. Flagging here so P2 picks up: UTL
      `AvailabilityRecord.timeframe` needs the physical split, and the two readers above need to switch to the new
      `horizon` column once the writer stamps it.
- [ ] [CODE] P0. **Merge the sports data_type vocabulary to ONE lowercase form.** This is the operator ruling that
      OVERTURNS `/codex/02-data/sports-data-types-catalog.md`'s "legitimately coexist; do NOT merge". Blast radius is
      the WHOLE 19-token IS reference vocabulary (`FIXTURES`, `MATCHES`, `PLAYER_STATS`, `INJURIES`, `STANDINGS`,
      `TEAMS`, `XG`, …) — not just `ODDS`. Land the CONTRACT here; the data re-stamp is P2 and is gated on the in-flight
      API-Football campaign. **Consumer inventory** (per codex rename rule): UAC `data_type_capability.py`,
      `schema_spec.py`, `sports_league_entity_coverage.py`, `_source_priority_data.py`, `_honest_coverage_logic.py`
      (`SCHEDULE_DEFINING_DATA_TYPES` frozenset), `availability_semantics.py`, `required_window_registry.py`,
      `league_data.py`, `feature_upstream.py` — all carry uppercase IS tokens; IS scripts
      `enumerate_expected_universe.py` + `build_instrument_catalogue.py`; every features-service/ml-service loader
      keying on uppercase IS entity names. Full enumeration: P2 `[REVIEW] P0`.
- [ ] [CODE] P0. **Retire the `exchange_odds`/`fixed_odds` instrument_type split** — exchange-vs-sportsbook is a
      property of the VENUE (UAC `SportsVenueType` already encodes it), so stamping it per-instrument is redundant.
      Derive at read time. This also resolves
      `/plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md`'s "classify 19 unmapped
      bookmakers" todo mechanically, with no per-venue operator judgment. NOTE the count discrepancy: that doc says 19,
      the live manifest says **21** venues still carrying only the pre-fork `odds` token. **PRE-SPECIFIED**: the live
      prod manifest is authoritative; re-measure it and correct the issue doc's figure, do not reconcile by discussion.
      **Consumer inventory** (per codex rename rule): UAC `market_data_categories.py`
      `INSTRUMENT_TYPES_BY_ASSET_GROUP["sports"]` + CONTRACT_REGISTRY keys (`exchange_odds`/`fixed_odds` entries,
      ~L960-1011); MTDS (reads instrument_type keys from UAC registry); manifest rows carrying
      `instrument_type=exchange_odds`/`fixed_odds`. Full enumeration: P2 `[REVIEW] P0`.
- [ ] [CODE] P1. **Delete `markets`, `outcomes` and `settlements`** from `DATA_TYPES_BY_ASSET_GROUP["sports"]` — 0 rows
      ever written, pure phantom declarations. Record in codex that ML labels come from IS `fixtures_outcomes` /
      `matches` (post-lowercasing), so the real label lineage is documented rather than implied by a path that was never
      built.
- [ ] [CODE] P1. **Purge the cross-AG bleed from the sports denominator.** `KALSHI` carries 20,785 `empty_confirmed`
      `trades` rows sourced `polymarket_clob`, spanning 2020-06-06 → 2026-05-21 — prediction-market venues seeded into
      the sports expected-universe. Stop the seeding at the enumerator, and retire
      `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED` once it is genuinely empty. Manifest-row cleanup is P2.
- [ ] [CODE] P1. **Stop instruments-service writing into the MTDS tick manifest with a blank venue.** 2,490 rows
      (`service_name=instruments-service`, `venue=""`: 1,106 `odds_horizon_bucket` + 1,273 `trades` + 111
      `trades_inplay`). Find the writer, fix the attribution or stop the write. Row cleanup is P2.
- [ ] [CODE] P1. **Correct the false UAC exception comment.** `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` in
      `market_data_categories.py` asserts uppercase `ODDS` is "4 stale capture_status=empty_confirmed/row_count=0
      manifest rows with zero backing GCS content". The live manifest shows **6,306 `captured` rows** spanning
      2020-06-05 → 2026-04-14. Fix the comment to state what is actually true; the set itself is retired by the
      lowercase merge above.
- [ ] [CODE] P1. **Reconcile UAC's two contradictory odds-feature upstream registries.** For the SAME calculator,
      `required_inputs.py::odds_calculator` declares `ODDS_HORIZON_BUCKET` only and says footystats `ODDS` was "removed
      2026-06-25 — MTDS/odds-api owns raw odds", while `feature_upstream.py::odds_calculator` declares footystats `ODDS`
      as REQUIRED. Pick one, make the other derive from it, and add a test that the two can never diverge again.
- [x] ✅ [DOCS] P0. **Author the codex rename/split process rule** (operator ruling 2026-08-08, resolves
      `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`): an entity rename or
      split MUST enumerate and migrate every consumer in the SAME change. Then APPLY it to this chain — every rename
      todo above must carry its enumerated consumer list before P2 executes. The rule is validated by its first real
      use, not written abstractly. ✅ Rule authored at
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`; consumer inventories added to each rename
      todo (trades→odds, horizon/timeframe, lowercase-merge, exchange_odds/fixed_odds); issue doc `[PROCESS] P1`
      resolved. — unified-trading-pm
- [x] ✅ [DOCS] P0. **Put a SUPERSEDED banner on `/codex/02-data/sports-data-types-catalog.md`** and correct it. Three
      things in it are now wrong or stale: (a) the "IS `ODDS` and MTDS types legitimately coexist; do NOT merge" ruling
      is OVERTURNED; (b) its GCS path convention documents `asset_group=sports/source={BOOKMAKER}/data_type=…` while
      production actually writes
      `pipeline_mode=…/asset_group=…/venue={BOOKMAKER}/instrument_type=…/data_type=…/league_id=…` — wrong axis name,
      missing two segments; (c) it documents 8 data types and never documents `trades`/`trades_inplay`, the largest
      population in the estate. Rewrite against the new model rather than patching. ✅ unified-trading-pm@69db5f8ed
- [ ] [DOCS] P1. **Reaffirm the 2020-06 floor against the P4 backfill** in `/codex/02-data/sports-2020-06-data-floor.md`
      — no change expected, but state explicitly that the floor governs the derived-layer backfill and the C3 pre-launch
      corpus disposition, so the next reader does not re-open it.

## Codex SSOTs

- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — HARD RULE governing every rename/split in this
  chain; authored by this plan's [DOCS] P0.
- `/codex/02-data/sports-data-types-catalog.md` — **rewritten 2026-08-08** (unified-trading-pm@69db5f8ed); now documents
  the target model.
- `/codex/02-data/sports-2020-06-data-floor.md` — the floor; unchanged, reaffirmed.
- `/codex/02-data/availability-manifest-and-data-status.md` — shard atom must be identical across
  writer/manifest/status/gate/UI; the `horizon` axis addition must satisfy this.
- `/codex/02-data/honest-coverage-model.md` — two-layer/two-view model the denominators must respect.
- `/codex/06-coding-standards/quality-gates.md` — QG-green tree is the contract.

## Progress Log

- **2026-08-08** — Authored from the interactive sports venue/data-type audit (27 operator rulings). All figures above
  measured against the live prod manifest and the 2026-08-05 honest-coverage rollup, not inferred. Capture-outage block
  placed FIRST per operator ruling ("fix inside this plan, phase 0").
- **2026-08-08 (slot 3, data_engineering)** — Block A todo-1 (diagnose) flipped. Root cause in
  `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` (fully traced in prior sessions); code-confirmed writer
  read (`odds_api_adapter.py:105-119` — `_candidate_leagues` with `leagues=None` returns 30 Prediction-tier leagues);
  live-verified GCS (day=2026-08-01 through 2026-08-07 present, data_type=trades confirmed, 2026-08-04 gap noted); Cloud
  Run executions completing normally (8hlxb 2026-08-08T00:30Z: 293594 records written date=2026-08-07). The plan's
  "trades max date 2026-07-26" was a stale read from `market-data-tick-sports-prd` per-bucket index at plan-authoring
  time — the canonical `instruments-store-sports-prd` manifest and live GCS both show captures post-07-26 from the 08-06
  backfill VM and resumed live capture.
- **2026-08-08 (slot 11, infra)** — Block A todo-3 (staleness guard) flipped.
  `DependencyChecker.check_sports_raw_source_captured` added to MDPS: reads MTDS manifest (SPORTS bucket), checks
  `capture_status=captured` for `data_type in {trades, odds}`. `_process_one_category` blocks
  `odds_snapshot`/`odds_movement`/`odds_horizon_bucket` when manifest has no captured row, emits
  `DP_DOWNSTREAM_BEFORE_UPSTREAM` alert via existing UAC `DATA_PIPELINE_ALERT_RULES`. Fails-open on manifest read
  errors. 9 unit tests. Shipped: market-data-processing-service@41cdb702d. QG green.
- **2026-08-08 (slot 7, data_engineering)** — Block A todo-2 (measured terminal verdict) flipped. Ran pyarrow
  filter-pushdown reads (memory-bounded) against the live manifest. Day=2026-08-07: **5,747 GCS parquet objects** in
  `market-data-tick-sports-prd-central-element-323112` under `day=2026-08-07`; manifest shows **225
  `capture_status=captured` rows** for `data_type=trades`, ALL with `row_count > 0`, sum = **9,154**; source=`odds_api`.
  Post-outage capture confirmed for 13 dates spanning 2026-07-25 → 2026-08-07 (2026-08-04 gap consistent with prior
  note). Not the silent-zero pattern — this is genuine captured data. All 3 Block A todos now ✅.
- **2026-08-08 (slot 3, data_engineering)** — Block B "first-class horizon axis" todo flipped.
  `unified-api-contracts@685b288a` + `market-data-processing-service@3e0fb852`. See the todo's own note above for the
  full design + rationale (the `validate_dataframe`-ignores-`required` footgun, the new additive
  `SPORTS_ODDS_HORIZON_BUCKET` contract, the MDPS SSOT-drift-guard wiring). Both repos' full QG green. Deferred to P2/P3
  (out of this plan's `repos:` — UTL/features-service/deployment-api): the physical `AvailabilityRecord.timeframe`
  manifest-column split, and switching `gcs_reader.py`/the honest-coverage rollup to read the new `horizon` axis.
- **2026-08-08 (slot 11, backend_engineer)** — Block B [DOCS] P0 (rename/split process rule) flipped. Codex doc
  confirmed at `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` (authored in the plan-authoring
  commit). Applied to this chain: consumer inventories added to todos 3 (trades→odds), 5 (lowercase merge), and 6
  (exchange_odds/fixed_odds); todo 4 (horizon/timeframe) already carried its consumer list. Key non-obvious consumer
  across all four renames: features-service/ml-service `_ODDS_BUCKETED_PREFIXES` binds by GCS path prefix, not by
  data_type column — a data_type grep misses it entirely. Issue doc `[PROCESS] P1` also resolved.
- **2026-08-08 (slot 2, data_engineering)** — Block B [DOCS] P0 (sports-data-types-catalog rewrite) flipped. Rewrote
  `/codex/02-data/sports-data-types-catalog.md` in full against the 2026-08-08 operator ruling: (a) "do NOT merge"
  overturned — doc now states vocabulary merges to ONE lowercase `odds` with `in_play`+`horizon` columns; (b) GCS path
  corrected to `venue=` (not `source=`) with `pipeline_mode=` and `instrument_type=` segments; (c) `trades` (375k
  shards), `trades_inplay`, and all retired types now documented; (d) `markets`/ `outcomes`/`settlements` marked RETIRED
  (0 rows ever written); (e) 32-member venue axis, `executable` predicate, BETFAIR operator-group parent, and MDPS
  staleness guard documented. Shipped: unified-trading-pm@69db5f8ed.
