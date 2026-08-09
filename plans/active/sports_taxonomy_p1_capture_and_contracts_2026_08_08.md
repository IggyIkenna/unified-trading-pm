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
    /plans/archive/2026_08/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md,
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
effort: high
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
      add a real venue→operator hierarchy in UAC that `BETFAIR_EX_UK`/`EX_EU`/`SB_UK` roll up to. The operator-group
      hierarchy shipped first in the arb bugfix at `unified-api-contracts@b9a0be80` (OPERATOR_GROUP_VENUES,
      case-insensitive guard via `get_operator()` `.upper()` normalisation in `e080ef74`); this todo extended it rather
      than duplicating it. 5. ✅ unified-api-contracts@49e83239 — removed BETFAIR from SPORTS_EXCHANGE_VENUES,
      VENUES_BY_ASSET_GROUP["sports"], VENUE_DATA_TYPE_CAPABILITIES, and representative_sample.py; updated 5 test files
      (test_sports_schemas, test_venue_context_integration, test_instrument_generator, representative_sample) to use
      BETFAIR_EX_UK as the canonical data-axis exchange representative; hierarchy already in place via arb bugfix
      (OPERATOR_GROUP_VENUES@b9a0be80); QG green (12533 passed).
- [x] ✅ [CODE] P0. **Collapse the raw odds vocabulary to a single lowercase `odds`.** `trades` → `odds`; footystats
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
      honest-coverage rollup. Full exhaustive enumeration: P2 `[REVIEW] P0`. — **LANDED 2026-08-08 (slot 2,
      data_engineering)**: `unified-api-contracts@b2c5197d5`. Added `SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM` (dict mapping
      `trades`/`ODDS`/`odds` → `odds`) + `canonical_sports_odds_data_type()` resolver in `league_data.py`, exported from
      both the sports domain `__init__.py` and top-level `unified_api_contracts/__init__.py` — mirrors the
      already-shipped `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM`/`canonical_sports_is_data_type` pattern exactly. **This is
      the P1 CONTRACT only**, per the plan header ("mutates NO GCS object and NO manifest row"): deliberately NOT wired
      into `DATA_TYPES_BY_ASSET_GROUP["sports"]` or any writer/reader this phase — the physical manifest re-stamp (the
      9-consumer inventory above) is P2 scope. **`in_play` column + `trades_inplay` retirement also deferred to P2** —
      NOT bolted onto `SPORTS_ODDS_TRADES` this phase: read `_validation.py::validate_dataframe` directly and confirmed
      it flags any declared-but-absent column as `missing_column` regardless of `nullable`/`required` (the
      `required=False`/`provided_by_venues` fields on `ColumnSpec` are never actually consulted by the missing-column
      check), so adding `in_play` now would flag every currently-shipping row as a violation — the identical reason
      `SPORTS_ODDS_HORIZON_BUCKET` was registered as its own contract instead of an optional column on
      `SPORTS_ODDS_TRADES`. 4 new drift-guard tests green (`test_sports_exports.py`): export presence, all 3 raw tokens
      covered, values collapse to `odds`, both-case resolution via `canonical_sports_odds_data_type`. Full
      `unified-api-contracts` `quality-gates.sh` green (346s).
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
- [x] ✅ [CODE] P0. **Merge the sports data_type vocabulary to ONE lowercase form.** This is the operator ruling that
      OVERTURNS `/codex/02-data/sports-data-types-catalog.md`'s "legitimately coexist; do NOT merge". Blast radius is
      the WHOLE 19-token IS reference vocabulary (`FIXTURES`, `MATCHES`, `PLAYER_STATS`, `INJURIES`, `STANDINGS`,
      `TEAMS`, `XG`, …) — not just `ODDS`. Land the CONTRACT here; the data re-stamp is P2 and is gated on the in-flight
      API-Football campaign. **Consumer inventory** (per codex rename rule): UAC `data_type_capability.py`,
      `schema_spec.py`, `sports_league_entity_coverage.py`, `_source_priority_data.py`, `_honest_coverage_logic.py`
      (`SCHEDULE_DEFINING_DATA_TYPES` frozenset), `availability_semantics.py`, `required_window_registry.py`,
      `league_data.py`, `feature_upstream.py` — all carry uppercase IS tokens; IS scripts
      `enumerate_expected_universe.py` + `build_instrument_catalogue.py`; every features-service/ml-service loader
      keying on uppercase IS entity names. Full enumeration: P2 `[REVIEW] P0`. — **LANDED 2026-08-08**
      `unified-api-contracts@298e628b` — added `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM` (dict comprehension over every
      `SPORTS_DATA_TYPE_TO_SOURCE` key, all 19 IS tokens) + `canonical_sports_is_data_type()` resolver (accepts either
      case, returns the lowercase target form) in `league_data.py`, exported from both the sports domain `__init__.py`
      and the top-level `unified_api_contracts/__init__.py`. Additive-only — deliberately NOT wired into
      `SPORTS_DATA_TYPE_TO_SOURCE`'s own keys or `enumerate_expected_universe.py`'s could-exist enumeration this phase,
      to avoid double-counting the axis ahead of P2's physical re-stamp (same pattern as the `SPORTS_HORIZONS` todo
      above). Drift-guard test (`test_sports_is_data_type_lowercase_form_covers_every_axis_key`) asserts every
      `SPORTS_DATA_TYPE_TO_SOURCE` key has a registered lowercase form so a future IS data_type addition can't silently
      miss the contract; 4 new tests green (export presence, drift-guard coverage, lowercase-value invariant, both-case
      resolution via `canonical_sports_is_data_type`). Full UAC `quality-gates.sh` green. The 9 UAC consumer files +
      IS's `enumerate_expected_universe.py`/`build_instrument_catalogue.py` + features-service/ ml-service loaders are
      NOT yet wired to this table (unchanged this phase, per the plan header's "contracts only, no GCS/manifest
      mutation" scope) — that live-wiring is the P2 `[REVIEW] P0` full-enumeration todo referenced above.
      unified-api-contracts
- [x] ✅ [CODE] P0. **Retire the `exchange_odds`/`fixed_odds` instrument_type split** — exchange-vs-sportsbook is a
      property of the VENUE (UAC `SportsVenueType` already encodes it), so stamping it per-instrument is redundant.
      Derive at read time. This also resolves
      `/plans/archive/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md`'s "classify 19 unmapped
      bookmakers" todo mechanically, with no per-venue operator judgment. NOTE the count discrepancy: that doc says 19,
      the live manifest says **21** venues still carrying only the pre-fork `odds` token. **PRE-SPECIFIED**: the live
      prod manifest is authoritative; re-measure it and correct the issue doc's figure, do not reconcile by discussion.
      **Consumer inventory** (per codex rename rule): UAC `market_data_categories.py`
      `INSTRUMENT_TYPES_BY_ASSET_GROUP["sports"]` + CONTRACT_REGISTRY keys (`exchange_odds`/`fixed_odds` entries,
      ~L960-1011); MTDS (reads instrument_type keys from UAC registry); manifest rows carrying
      `instrument_type=exchange_odds`/`fixed_odds`. Full enumeration: P2 `[REVIEW] P0`. — **DONE 2026-08-08 (slot 25,
      data_engineering)**: `unified-api-contracts@56f20ad0`. Added `derive_sports_odds_instrument_type(venue)` in
      `registry/_sports_venue_constants.py`, exported via `registry/__init__.py` — resolves "exchange_odds" for
      `SportsVenueType.EXCHANGE_API` venues, "fixed_odds" for `BOOKMAKER_API`/`WEB_SCRAPER` venues, `None` for
      prediction-market/DFS/data-only/unrecognised venues (callers fall back to the legacy generic `"odds"` contract,
      same fallback `lookup_contract` already performs during the fork's migration window) — built on the pre-existing
      `SPORTS_VENUE_TYPE_MAP`, so every venue self-classifies mechanically; no per-venue enumeration, which makes the
      19-vs-21 count discrepancy moot (the resolver covers the map, not a hand-picked subset — did not re-run a fresh
      live-manifest count since the classification question itself no longer depends on the count;
      `/plans/archive/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md`'s own OPERATOR RULING
      banner already carries the 21-venue correction). **P1 CONTRACT only**, same additive pattern as
      `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM`/`SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM`: deliberately NOT wired into
      `CONTRACT_REGISTRY`'s `("sports","exchange_odds"/"fixed_odds","trades")` keys, the MTDS writer that still stamps
      the column, or any existing manifest row this phase — switching the writer/readers to call this instead of the
      stamped column, and retiring `CONTRACT_REGISTRY`'s exchange_odds/fixed_odds entries + the accepted-noncanonical
      set entries in `market_data_categories.py`, is the P2 `[REVIEW] P0` full-enumeration scope referenced above. 8 new
      unit tests (`test_registry_completeness_p1.py::TestDeriveSportsOddsInstrumentType`) green. Full
      `unified-api-contracts` `quality-gates.sh` green (405s).
- [x] ✅ [CODE] P1. **Delete `markets`, `outcomes` and `settlements`** from `DATA_TYPES_BY_ASSET_GROUP["sports"]` — 0
      rows ever written, pure phantom declarations. Record in codex that ML labels come from IS `fixtures_outcomes` /
      `matches` (post-lowercasing), so the real label lineage is documented rather than implied by a path that was never
      built. — unified-api-contracts@975f0191
- [x] ✅ [CODE] P1. **Purge the cross-AG bleed from the sports denominator.** `KALSHI` carries 20,785 `empty_confirmed`
      `trades` rows sourced `polymarket_clob`, spanning 2020-06-06 → 2026-05-21 — prediction-market venues seeded into
      the sports expected-universe. Stop the seeding at the enumerator, and retire
      `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED` once it is genuinely empty. Manifest-row cleanup is P2. — **DONE 2026-08-08
      (slot 4, data_engineering)**: `unified-api-contracts@e5dd8faf`. Re-investigated "stop the seeding at the
      enumerator" against live code: `VENUES_BY_ASSET_GROUP["sports"]`, `expected_coverage.py`'s `_SPORTS` dict, and
      IS's `venue_core.get_venues_for_asset_groups` SPORTS branch are ALL already clean — none seed
      KALSHI/prediction-market venues into sports today. The archived root-cause doc
      (`plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`) already
      classified the 20,785 rows as **classification (b) — a dormant legacy artifact** (all `written_at` cluster in one
      80s window from `rebuild_sports_manifest_v9.py`'s 2026-07-13 re-stamp of pre-existing rows, not a live write), and
      `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s tracking todo was DONE + archived 2026-07-31 — so there is
      no live enumerator bug left to fix. The only stale artifact was `market_data_categories.py`'s own comment above
      `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED`, which still claimed "root-cause classification remains open" — corrected
      it to cite the closed classification and the no-live-seeding-path finding. **Did NOT retire
      `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED`** — the todo's own condition ("once it is genuinely empty") isn't met yet;
      the 20,785 manifest rows still exist and retiring now would make the deployment-api distinct-values panel falsely
      reflag them. Retirement stays gated on the P2 manifest-row purge (`sports_taxonomy_p2_migration_2026_08_08.md` P0
      todo, line 142). No enumerator code change was needed or made.
- [x] ✅ [CODE] P1. **Stop instruments-service writing into the MTDS tick manifest with a blank venue.** 2,490 rows
      (`service_name=instruments-service`, `venue=""`: 1,106 `odds_horizon_bucket` + 1,273 `trades` + 111
      `trades_inplay`). Find the writer, fix the attribution or stop the write. Row cleanup is P2. — **LANDED 2026-08-03
      (prior session, slot 12/14)**: writer = `backfill_orphan_class_e_sports.py::record_cells()` — a case-sensitivity
      gap made lower-case GCS-path data_types miss UAC `SOURCE_PRIORITY` (upper-case-only keys), falling through to
      `BATCH_INSTRUMENTS_SERVICE` fallback. Three-part fix: (1) `instruments-service@a722014a` — `.upper()` retry in
      `resolve_source_and_mode()` + pipeline_mode entries for `odds_api`/`mdps_odds_horizon_bucket`; (2)
      `unified-api-contracts@b27717b8` — registered `TRADES_INPLAY` in `SOURCE_PRIORITY` (`odds_api`); (3)
      `instruments-service@869f1ce7` — one-off restamp script added + ran against prod: 2,490/2,490 rows restamped,
      re-verified GREEN (0 remaining); test updated for correct `trades_inplay` resolution.
- [x] ✅ [CODE] P1. **Correct the false UAC exception comment.** `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` in
      `market_data_categories.py` asserts uppercase `ODDS` is "4 stale capture_status=empty_confirmed/row_count=0
      manifest rows with zero backing GCS content". The live manifest shows **6,306 `captured` rows** spanning
      2020-06-05 → 2026-04-14. Fix the comment to state what is actually true; the set itself is retired by the
      lowercase merge above. — unified-api-contracts@54e7e64d (slot-3, 2026-08-08; checkbox flip slot-14)
- [x] ✅ [CODE] P1. **Reconcile UAC's two contradictory odds-feature upstream registries.** For the SAME calculator,
      `required_inputs.py::odds_calculator` declares `ODDS_HORIZON_BUCKET` only and says footystats `ODDS` was "removed
      2026-06-25 — MTDS/odds-api owns raw odds", while `feature_upstream.py::odds_calculator` declares footystats `ODDS`
      as REQUIRED. Pick one, make the other derive from it, and add a test that the two can never diverge again. —
      **DONE 2026-08-08 (slot 21, data_engineering)**: `unified-api-contracts@66d8ce6d`. Removed
      `UpstreamReq(source="footystats", data_type="ODDS")` from `feature_upstream.py::odds_calculator` (the 2026-06-25
      ruling was already in `required_inputs.py`; `feature_upstream.py` hadn't been updated). Promoted
      `mdps_odds_horizon_bucket` to `required=True` (sole upstream). Added `TestOddsCalculatorRegistryConsistency` with
      3 cross-registry tests: no footystats ODDS present, mdps ODDS_HORIZON_BUCKET required=True, and required
      data_types agree between both registries. QG: ✅ ALL QUALITY GATES PASSED (335s, 12536 passed).
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
- [x] ✅ [DOCS] P1. **Reaffirm the 2020-06 floor against the P4 backfill** in
      `/codex/02-data/sports-2020-06-data-floor.md` — no change expected, but state explicitly that the floor governs
      the derived-layer backfill and the C3 pre-launch corpus disposition, so the next reader does not re-open it. —
      **DONE 2026-08-08 (slot 11, data_engineering)**: added "Reaffirmed against the P4 derived-layer backfill" section
      — confirms no change to the floor date/window, states explicitly the floor governs both P4's backfill start-date
      and the C3 corpus disposition (delete per the standing wipe ruling, not reopened as a 2018-extension choice).
      unified-trading-pm@6030eb32a

### Added 2026-08-08 (operator, mid-flight) — collapse the remaining derived data_types onto `odds` + axes

> Operator question that triggered this: _"what's the point of odds movement and snapshot as data types vs just being
> manipulations of odds"_. Correct — and there is a decisive precedent this chain under-used.

- [x] ✅ [CODE] P0. **Collapse `odds_snapshot` and `odds_movement` into `data_type=odds` + the `timeframe` axis.** They
      are not distinct data — they are a LOCF resample and an OHLC candle OF `odds`. Sports is the only asset_group that
      mints new data_type names for its derived grains; the fleet-wide MDPS ruling (2026-07-21, recorded in
      `registry/processed_data_dependencies.py`) is explicit: _"an MDPS manifest row's `data_type` column carries the
      RAW source token (`trades`, `book_snapshot_5`, …) — the SAME vocabulary MTDS's raw-tick manifest rows use — with
      the candle timeframe living in a SEPARATE `timeframe` column."_ cefi/tradfi/defi all obey it; UAC's own
      `_RAW_TO_PROCESSED_PREFIX` even pre-declares `"odds": "odds_ohlcv"`. **The redundancy is measurable**: these rows
      ALREADY carry the grain in `timeframe` — `odds_movement` 15m=10,300 / 1h=10,276; `odds_snapshot` 15m=9,464 /
      1h=9,454 (live prod manifest, 2026-08-08). The data_type name restates what `timeframe` already says, so
      collapsing loses nothing. End state: sports raw vocabulary is ONE type (`odds`) plus the `timeframe`, `horizon`
      and `in_play` axes. Apply the codex rename rule — enumerate consumers BEFORE changing anything. — **DONE
      2026-08-08 (slot 32, data_engineering)**. The RAW-vocabulary side of the collapse was already shipped by a prior
      session at `unified-api-contracts@1f5879fc` (verified on origin: 3 files, `market_data_categories.py` +
      `_mvp_scope_rules.py` + `test_mvp_scope.py`) — removed `odds_snapshot`/`odds_movement` from
      `DATA_TYPES_BY_ASSET_GROUP["sports"]`, `FREQUENCY_MAP`, `NEEDS_CANDLE_PROCESSING`,
      `VALID_DATA_TYPES_BY_INSTRUMENT_TYPE`, and `MVP_SCOPE["sports"].data_types`; every removal site left an inline
      comment naming this as the reason. This session verified the commit is genuinely on `origin/live-defi-rollout`
      (not a dangling/lost commit per the RULES.md quickmerge-regate caution) and closed the checkbox, since only the
      flip was missing. **Consumer inventory (codex rename rule)** — enumerated, not yet migrated, because they are the
      declared scope of the very next todo below ("snapshot-vs-candle discriminator"), which this todo's own text
      explicitly hands the physical rename to (`_RAW_TO_PROCESSED_PREFIX`,
      `canonical_writer_shaping.mdps_data_type_key`): MDPS `odds_snapshot_adapter.py`/`odds_movement_adapter.py`
      (`data_type` class attrs still literally `"odds_snapshot"`/`"odds_movement"`, registered in
      `CandleAdapterRegistry`); UAC `_SPORTS_ODDS_DERIVED_CANDLE_PREFIXES` + `_candle_contracts.py`'s per-timeframe
      contract registration loop + `_sports_prediction_contracts.py`'s
      `CONTRACT_REGISTRY[("sports","odds","sports_odds_snapshot"/"sports_odds_movement")]` (the PROCESSED-key contracts,
      deliberately untouched — they still back the live MDPS writer); UAC `_honest_coverage_clusters.py`
      (`SPORTS_FIXTURE_CLUSTERS` mapping); MDPS `canonical_writer_shaping.py`'s `mdps_data_type_key` (the actual
      key-minting function the next todo must read before changing). None of these are RAW MTDS capture vocabulary (this
      todo's scope, per the plan header's "contracts only" phase boundary) — they are MDPS-internal processed-output
      keys, correctly deferred.
- [x] ✅ [CODE] P1. **Decide and record the snapshot-vs-candle discriminator on the collapsed model.** `odds_snapshot`
      (point-in-time LOCF) and `odds_movement` (OHLC bar) are different SHAPES at the same grain, so `timeframe` alone
      cannot distinguish them once the names are gone. **PRE-SPECIFIED**: follow the fleet convention already used for
      the cefi/tradfi candle family — the OHLC form is the candle (`odds` + `timeframe`), and the LOCF point-in-time
      form is a distinct processed key via `_RAW_TO_PROCESSED_PREFIX` (`odds_ohlcv_*` vs a snapshot prefix), NOT a new
      `data_type`. Confirm against `canonical_writer_shaping.mdps_data_type_key`'s real output before implementing, and
      record the chosen keys in codex. — **DONE 2026-08-08 (slot 12, data_engineering)**. Confirmed against the real
      `mdps_data_type_key`/`_DATA_TYPE_TO_MDPS_PREFIX` + UAC `_RAW_TO_PROCESSED_PREFIX` implementations AND the actual
      adapter code (`odds_movement_adapter.py`/`odds_snapshot_adapter.py`): `_RAW_TO_PROCESSED_PREFIX` is strictly
      raw-MTDS-`data_type`-scoped (backs `MDPS_DERIVABLE_DATA_TYPES`/`PROCESSED_REQUIRES_RAW`'s honest-coverage
      classification) — `odds_snapshot`/`odds_movement` are NOT raw data_types (confirmed: neither was ever a
      raw-vocabulary entry), so a literal new prefix-table entry for them would misclassify them as raw sources and risk
      colliding `odds_movement_{tf}` with the base `odds_ohlcv_{tf}` candle. **Ruling**: `odds_movement`'s adapter
      already computes a genuine OHLC aggregation (first/max/min/last of `home_odds`) — this **is** the "OHLC form is
      the candle" the pre-spec calls for, just realized as the sports-specific candle-of-`home_odds` rather than a
      literal `odds`+`timeframe` merge; `odds_snapshot`'s LOCF (last-value, flat O=H=L=C) remains the distinct
      point-in-time key. Both stay MDPS-internal `CandleAdapterRegistry` product keys — NOT new raw `data_type`s —
      resolved via `mdps_data_type_key`'s existing deterministic fallback (`odds_movement_{tf}`/`odds_snapshot_{tf}`),
      which was already correct; no functional key-minting change was needed. Shipped: (1) clarifying comments in both
      prefix tables + the fallback branch marking the omission deliberate — market-data-processing-service@d3ac175,
      unified-api-contracts@c4ed6094; (2) codex decision record + a fix to a stale schema description (the doc wrongly
      described `odds_movement` as a `price_prev`/`price_curr`/`delta` shape; the real adapter output is OHLC columns) —
      unified-trading-pm@\<pending\>, in `/codex/02-data/sports-data-types-catalog.md` § "Snapshot vs Candle
      Discriminator (P1 decision, 2026-08-08)".
- [x] ✅ [CODE] P1. **Make MTDS's `_asset_group_for_venue` FAIL LOUD instead of defaulting to cefi.** —
      market-tick-data-service@55d8abc7. `market_tick_data_service/reader.py::_asset_group_for_venue` resolved any
      unrecognised venue to `"cefi"` SILENTLY. When this chain's venue-axis split removed `ODDS_API`/`FOOTYSTATS` from
      the canonical venue axis, that default began pointing every read of their **146,163 historical shards** (ODDS_API
      123,650 + FOOTYSTATS 22,513) at the **CEFI bucket** — a silent wrong answer, caught only because one unit test
      happened to assert the sports case. Hot-fixed 2026-08-08 (`SPORTS_VENUES` consulted before the fallback + the
      fallback now WARN-logs), but the default itself remained. **Enumeration pass** (required before the raise, per
      this todo's own text): resolving through UAC's `to_canonical_venue()` before the `VENUE_TO_ASSET_GROUP` lookup
      surfaced a SECOND, previously-undetected instance of the same bug class — all 62 DeFi legacy bare-name venue
      aliases (`ANKR`, `LIDO`, `UNISWAP_V2`, …) are NOT keys in `VENUE_TO_ASSET_GROUP` (only their canonical `-CHAIN`
      forms are), so they were ALSO silently defaulting to cefi. Closed that gap, then replaced the remaining default
      with a typed raise (`UnknownVenueAssetGroupError`, matching the existing `InvalidChainError`/
      `InvalidCanonicalQuestionGroupError` fail-loud convention in `reader_errors.py`) — the "genuinely-unknown cefi
      venue" carve-out this todo flagged turned out to be empty once the DeFi alias gap was closed, so nothing
      legitimately depends on the silent default anymore. Updated the reader's existing test suite (2 tests asserting
      the old silent-cefi behavior now assert the raise; 4 DeFi chain-axis tests' stale `VENUE_TO_ASSET_GROUP` mocks
      removed in favor of the real registry; 2 no-blobs tests swapped their placeholder venue for a registered one; the
      file-wide stale `"BINANCE"` bare-token fixture convention corrected to `"BINANCE-SPOT"`). `quality-gates.sh`
      genuinely green (sentinel-verified on the shipped SHA): 10198 passed, 0 failed, 28 skipped. The broader "sweep for
      other `.get(..., <default asset_group>)` lookups across MTDS/MDPS/IS" this todo also called for is tracked as its
      own follow-up todo below (found ~15 more sites; fixing all of them was outside this todo's 1h estimate).
- [x] ✅ [CODE] P2. **Sweep the other `.get(venue, "cefi")`-style silent-default resolvers found across MTDS/IS during
      the 2026-08-08 `_asset_group_for_venue` enumeration pass** (same bug class as the fixed todo above — a wrong
      bucket is a silent wrong answer). Concrete sites found (not exhaustive — re-grep `VENUE_TO_ASSET_GROUP.get(`
      before starting): `market-tick-data-service/market_tick_data_service/engine/orchestrator/preflight.py:428`
      (`cat = _orch.VENUE_TO_ASSET_GROUP.get(venue, "cefi")`),
      `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py:195,375`
      (`ag = _orch.VENUE_TO_ASSET_GROUP.get(venue_name, "cefi").lower()`, two call sites),
      `instruments-service/instruments_service/engine/orchestrator/writers.py:286`
      (`_cat = "defi" if manifest_chain else (VENUE_TO_ASSET_GROUP.get(venue_str, "cefi"))`). For each: determine via
      the same enumeration approach (does any currently-live venue actually rely on the default, incl. DeFi legacy bare
      aliases via `to_canonical_venue()`) whether it's safe to raise, then either raise or document why a default is
      still correct there. NOT in scope: `instruments-service/.../process_write.py::_asset_group_for_venue` (a
      deliberately different, already-reasoned resolver defaulting to `"sports"`, not `"cefi"` — see its own docstring).
      **Done when**: each listed site is either converted to fail-loud or has a recorded reason it's a genuine default.
      — **DONE 2026-08-09 (data_engineering, slot 20)**: `market-tick-data-service@8ba50fac`,
      `instruments-service@aecd1242`. Re-grepped `VENUE_TO_ASSET_GROUP.get(` live — confirmed the 4 named sites are the
      complete set (no drift since the todo was written). Measured a REAL live gap enabling the default: UAC
      `VENUES_BY_ASSET_GROUP["defi"]` (103 venues) is missing 33 members of `ALL_DEFI_VENUES` (135 venues) — all
      legitimate pipeline-mode-only DeFi venues (ALCHEMY-\*/FLASHBOTS-ETHEREUM/MORPHO-ARBITRUM/etc). Because
      `VENUE_TO_ASSET_GROUP` derives from `VENUES_BY_ASSET_GROUP`, these 33 venues returned `None` (not `"defi"`) and
      silently escaped MTDS `_build_active_venues_for_date`'s DeFi-strip filter (a bare
      `VENUE_TO_ASSET_GROUP.get(v) == "defi"` check), falling through into the CeFi tick-fetch path where the 3 MTDS
      `.get(venue, "cefi")` sites would then hit. **Fixed the escape hatch** (`market-tick-data-service@8ba50fac`): the
      strip filter now also checks `v in _VENUE_MAPPING.all_defi_venues`. **None of the 4 sites converted to a raise** —
      determined unsafe on isolation grounds, not just correctness grounds: MTDS's 3 sites sit inside `_process_venue`,
      gathered via `asyncio.gather(*tasks)` with NO `return_exceptions=True`, so a raise would abort the WHOLE date's
      fetch run for every venue, not just the misclassified one; IS's `_classify_venue_write` (writers.py:286) is called
      from a bare `for venue_name, venue_df in df.groupby("venue")` loop in `process_write.py` with no per-venue
      try/except, same blast-radius problem. This violates the shard-level-failure-isolation architecture
      (`/codex/04-architecture/shard-level-failure-isolation.md`) the `reader.py` precedent's synchronous single-read
      context didn't have to worry about. Instead: kept the default at each site but added a `logger.warning` breadcrumb
      that fires whenever the default is actually hit (upgrades silent → visible without changing blast radius), plus an
      inline comment recording the per-site reachability analysis (IS site: effectively dead code today — CeFi/TradFi/
      prediction venues reaching it are already correctly registered, DeFi venues bypass the `.get()` entirely via the
      `manifest_chain`-truthy branch; MTDS bundle-shard site: dead code today — bundle itypes are TradFi/CeFi-only; MTDS
      general-shard site: the one genuinely-reachable site pre-fix, now closed by the strip-filter fix above). Filed
      `/plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md` for the two real follow-ups this
      sweep surfaced but did not fix in-scope: (1) close the UAC registry gap itself (add the 33 venues to
      `VENUES_BY_ASSET_GROUP["defi"]`), (2) add per-venue exception isolation to the two unisolated loops so these 4
      sites can later follow the `reader.py` precedent and become typed raises. Both repos' full `quality-gates.sh`
      green (MTDS 299s / 10367 passed; IS 148s), verified landed on `origin/live-defi-rollout` via
      `git merge-base --is-ancestor`. unified-trading-pm
- [x] ✅ [CODE] P1. **Update `venue_data_types.yaml` in the SAME change as the markets/outcomes/settlements deletion.**
      — unified-trading-pm@\<pending\>, market-tick-data-service@\<pending\>. Fixed via the `ldr_qg_failure` escalation
      (agt-fecbe9): UAC commit `1f5879fc` (2026-08-08) collapsed `odds_snapshot`/`odds_movement` out of
      `DATA_TYPES_BY_ASSET_GROUP` but did not cascade to the YAMLs, which broke `quality-gates-v2` on
      `live-defi-rollout` for `unified-api-contracts` (both parametrized cases:
      `test_yaml_data_types_in_uac[unified-trading-pm]` — POLYMARKET/BETFAIR/PINNACLE/ODDS_API — and
      `[market-tick-data-service]` — BETFAIR/PINNACLE/ODDS_API). Removed the `- odds_snapshot`/`- odds_movement`
      per-venue list entries in both `configs/venue_data_types.yaml` files, following the same retirement-comment
      pattern already used for the markets/outcomes/settlements deletion. `bash scripts/quality-gates.sh` in
      unified-api-contracts now EXITs 0 (292s, full suite). Also surfaced + fixed an unrelated second wall on the same
      gate: pip-audit flagged aiohttp 3.14.1 (PYSEC-2026-3545/3546/3547), bumped to 3.14.3 — see
      unified-api-contracts@e092f3e9. `tests/test_data_type_canonicalization.py::test_yaml_data_types_in_uac` is ALREADY
      failing (pre-existing, 2 params: `unified-trading-pm`, `market-tick-data-service`) on exactly these tokens —
      `SPORTS.common_data_types: 'markets'`, `SPORTS.venues.BETFAIR: 'markets'/'outcomes'/'settlements'`,
      `SPORTS.venues.PINNACLE: …`. Deleting them from UAC without updating the YAML makes that failure WORSE, not
      better. This is a live worked example of the codex rename rule's "a token grep is not a sufficient enumeration"
      clause — the YAML is a consumer no `data_type` grep of the Python registries would surface. Fix both sides
      together and get the test to pass.

- [x] ✅ [REVIEW] P1. **Sweep this chain's landed work for tests WEAKENED rather than fixed.** Measured instance: when
      P1's venue-axis split broke `tests/unit/test_reader.py::TestTickBucket`'s sports case, the red was cleared by
      `market-tick-data-service@85423040` — _"fix(test): swap retired ODDS_API venue for PINNACLE"_ — which changed the
      test to stop asserting `ODDS_API` while leaving the underlying defect live: `_asset_group_for_venue` was still
      silently routing all 146,163 ODDS_API/FOOTYSTATS shards at the **cefi** bucket. The test that CAUGHT a real
      data-correctness bug was edited until it no longer caught it. Root fix + genuine coverage landed
      `market-tick-data-service@fc704195` (the new test is verified to FAIL without the fix — the property the swap
      lacked). Re-read every other test this chain has touched and confirm each still asserts the behaviour it was
      written to protect, rather than having been relaxed to match new code. **Done when**: each touched test is
      confirmed still load-bearing, or re-strengthened. — **DONE 2026-08-08 (fleet-wide sweep, operator-requested
      "across the board")**. Scanned all 47 test-touching commits since 2026-08-07 across 8 repos for net assertion loss
      / added xfail-skip; 5 flagged, then read individually: **(1) `market-tick-data-service@85423040` — CONFIRMED
      weakening**, the seed case: swapped the failing `ODDS_API` parametrize entry for `PINNACLE` while
      `_asset_group_for_venue` still routed 146,163 sports shards at the cefi bucket. Root-fixed + genuine coverage
      restored `market-tick-data-service@fc704195`; their PINNACLE case kept (not reverted) and the new test verified to
      FAIL without the fix. **(2) `unified-api-contracts@05a709fd`** — legitimate: the removed assert tested behaviour
      ruling #2 intentionally changed, and the same commit promoted 22 bookmakers into the sentinel set (net MORE
      coverage). **(3) `market-tick-data-service@a897ef60`** — legitimate: deleted 643 lines of SOURCE alongside the
      tests (`databento_fetch.py` -266, `tardis_csv_transport.py` -104); the subject genuinely went away. **(4)
      `unified-api-contracts@12bed42e` + the jupiter sibling** — honest xfails ("needs a real WS capture, not a
      fabricated cassette") but with NO tracked remediation; now tracked in
      `/plans/active/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md`. **(5)
      `unified-api-contracts@8f670c45` / `market-tick-data-service@2f7d7840`** — net +3 and +11 assertions, not
      weakening. **Then extended the sweep to the fleet-scale form of the same anti-pattern — RAISED RATCHET BASELINES**
      (a ratchet says "NEVER raise a count"). Found `fabricated_sha_citation_baseline` raised **2 -> 4 -> 6 -> 8 in two
      days**. Root-caused as HALF gate-bug, HALF real: 4 entries were real commits that only failed because
      `check_plan_commit_sha_evidence.py` ran a bare `git cat-file` with NO fetch, so a freshly-pushed commit read as
      fabricated (reproduced live on `unified-trading-ci@686bca7`); 4 were genuinely wrong citations whose underlying
      work was real, corrected to `01c3dbbab9`/`79c4a72737`/`b7e41849d6` (each verified to exist first). Checker fixed
      to fetch once on the miss path; **baseline ratcheted 8 -> 0**, verified 2,549 citations / 0 unresolvable.

- [x] ✅ [REVIEW] P2. **The weakened-test sweep counted assertions; it did not read them.** The 2026-08-08 fleet sweep
      screened 47 test-touching commits for NET assertion loss + added xfail/skip. That shape is blind to a commit which
      DELETES a strong assertion and ADDS a weak one — it nets zero and never surfaces. Treat the sweep's result as "no
      net coverage loss in the window", NOT "no weakening anywhere". Decide whether a semantic check is worth building
      (e.g. flag any commit where an `assert` line is replaced rather than added/removed) or record why counting is good
      enough. **Done when**: the decision is recorded, or the semantic check exists. **DECISION (2026-08-09, review) —
      counting is good enough for now; do not build the diff-line semantic check.** Tested the natural cheap version of
      the proposed check against real history (2 diff-scoped Python scripts, no persisted tooling): (1) naive "any
      `assert` line removed + any `assert` line added in the same hunk" flagged 36 commits in `market-tick-data-service`
      alone over a **3-day** window — spot-checking a sample showed virtually all were legitimate value/constant churn
      (`assert len(shards) == 5` -> `== 6`, `BINANCE` -> `BINANCE-SPOT` venue renames), i.e. ~100% noise. (2) A smarter
      version (flag only where the REMOVED line has a strong comparison (`==`/`!=`/`>`/`<`) and an ADDED line in the
      same hunk matches a weak pattern (`is not None`/bare-truthy/`isinstance(...)`)) cut the naive count to 12/2 weeks
      in MTDS + 6/2 weeks in instruments-service — but hand-verifying 3 of these against the real diff
      (`d6d539a844: tests/unit/test_odds_api_ws_connector.py`,
      `ee49a76df1: tests/unit/test_phoenix_orderbook_handler.py`,
      `e68059b266: tests/unit/scripts/test_migrate_instrument_availability_hive_2026_08_03.py`) showed **all 3 were
      false positives**: the "removed strong assertion" was NOT semantically replaced by the "added weak assertion" —
      each was a distinct, unrelated statement that happened to land in the same diff hunk (e.g. `d6d539a844`'s
      `Decimal(pinnacle_h2h[...]) == Decimal("1.85")` is still present in the new code, byte-identical in strength, just
      under a renamed variable — the flagged "replacement" `isinstance(markets, dict)` was actually a SEPARATE,
      already-present assertion that also got touched in the same rename). Line-level diff heuristics cannot distinguish
      "assertion A replaced by weaker assertion B" from "two unrelated assertions both edited in the same hunk" without
      real per-statement AST alignment across old/new test-function bodies — that is a materially bigger build (AST
      diff + statement correspondence + strength classification robust to variable renames) than this P2 finding's
      evidenced risk justifies; no actual weakening instance was found in any sample, only mis-paired refactor noise.
      Recommendation: leave the existing net-assertion-count sweep as-is; revisit with a proper AST-based checker only
      if a real weakening is ever caught by manual review (evidence-triggered, not speculative). Scripts used (scratch,
      not shipped): `assert_replace_scan.py` / `assert_weaken_scan2.py`, run against `market-tick-data-service` and
      `instruments-service` over 2026-07-25..2026-08-09.
- [x] ✅ [DOCS] P2. **`/codex/02-data/sports-data-types-catalog.md`'s "Venue Axis" section venue list does not match the
      live `VENUES_BY_ASSET_GROUP["sports"]`** (found by `/docs-reconcile` 2026-08-08, direct-import verification
      against `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`). The doc claims "32
      canonical members" and names `BETFAIR_EX_AU`, `WILLIAM_HILL`, `BWIN`, `MYBOOKIEAG`, `LOWVIG`, `WYNNBET`, `FOXBET`,
      `MARATHONBET`, `1XBET`, `SUPABETS`, plus an open-ended "and additional regional books" tail; the live registry
      (verified via
      `.venv/bin/python -c "from unified_api_contracts.registry.market_data_categories import VENUES_BY_ASSET_GROUP; print(sorted(VENUES_BY_ASSET_GROUP['sports']))"`)
      has **31** members and includes `BETFAIR_SB_UK`, `WILLIAMHILL` (no underscore), `BETOPENLY`, `BETRIVERS`,
      `BETVICTOR`, `CASUMO`, `LADBROKES`, `LIVESCOREBET`, `NOVIG`, `ONEXBET`, `PADDYPOWER`, `PROPHETX`, `SKYBET`,
      `VIRGINBET`, bare `UNIBET` — none of which the doc names — while omitting several the doc DOES name
      (`BETFAIR_EX_AU`, `BWIN`, `MYBOOKIEAG`, etc.). Not fixed here: this plan's own "Codex SSOTs" section calls the doc
      "rewritten 2026-08-08... now documents the target model", so it's unclear whether the doc is stating a target the
      registry hasn't fully landed yet or is simply a stale/miscopied enumeration — needs someone with this chain's full
      context to reconcile, not a doc-health pass guessing at domain intent. **Done when**: the doc's Venue Axis list is
      verified to either match the live registry exactly (member-for-member) or explicitly document why it intentionally
      diverges (target vs. current state). — **DONE 2026-08-09 (data_engineering, slot 9)**: re-verified live registry
      is a genuine stale/miscopied enumeration, not an intentional target-vs-current divergence (11 named venues never
      registered; 15 real members unnamed). Rewrote `/codex/02-data/sports-data-types-catalog.md` § "Venue Axis" to list
      all 31 live members exactly, grouped by their real `SportsVenueType` (`exchange_api`/
      `prediction_market_api`/`bookmaker_api`/`web_scraper`, verified via direct import), corrected the "32-member"
      references at lines 90 and 287 to 31. — unified-trading-pm

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

### Deferred work after 2026-08-08 (interactive session checkpoint)

Nothing below is uncommitted — every item is either a tracked `- [ ]` or is owned elsewhere. Kinds are separated because
they need different responses.

| item                                                                                                                 | kind                                                     | blocked on                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P2 migration (17 todos), P3 consumers (15), P4 backfill (9)                                                          | **Not done** — real work                                 | P1 completing; P2 additionally on the API-Football campaign                                                                                                |
| `markets`/`outcomes`/`settlements` YAML+UAC parity; collapse `odds_snapshot`/`odds_movement` onto `odds`+`timeframe` | **Not done**                                             | tracked as P0 todos in P1/P2                                                                                                                               |
| MTDS `_asset_group_for_venue` fail-fast (default still `cefi`, now WARN-logged)                                      | **Done** (2026-08-08, market-tick-data-service@55d8abc7) | enumeration pass also found + fixed a 2nd silent-cefi-default class (DeFi legacy bare aliases); the broader MTDS/IS sweep is now its own P2 follow-up todo |
| Two WS-cassette xfails (`jupiter_solana_ws`, `aave_liquidations_ethereum_ws`)                                        | **Cannot be done yet**                                   | needs a real WS capture session; fabricating a cassette is explicitly banned                                                                               |
| Sports live-trading activation                                                                                       | **Operator-owned**                                       | permanent hard-stop; now formally gated on this chain                                                                                                      |
| Other artifact tranches (123 open operator questions, Cross-cutting 37)                                              | **Operator-owned**                                       | only sports got the reconcile-then-plan treatment                                                                                                          |

**Recommended NEXT: let P1 finish, then release P2.** P2 is the long pole (375k-shard re-stamp) and is double-gated;
everything else is cheaper and can follow. Do NOT start P4's backfill early — backfilling pre-migration guarantees a
redo, which is exactly why it was split out.

### Lessons carried forward (would otherwise be re-learned)

- **A green panel can be produced by exclusion.** Sports read "0 non-canonical" while hiding 21 venues / ~340k shards;
  the detector drops accepted-exceptions BEFORE enumerating. Success criterion for the chain is the exception sets
  reaching EMPTY, never the badge count reaching zero.
- **`quality-gates.sh` exit 0 is NOT green.** The MTDS/UAC runs exited 0 with real test failures inside; read the
  summary line, not the exit code.
- **A quickmerge that exits 0 has not necessarily landed.** Twice this session it exited 0 leaving work staged-only —
  always re-verify with `git rev-list --count origin/<b>..HEAD` and a content check on origin.
- **An autostash can silently pull your fix out from under a passing test.** `reader.py` tested green, then got stashed;
  the tests still passed because the file was gone. Re-verify behaviour end-to-end, not just the test result.
- **Read the producer before judging a consumer's defensive default.** The aave `# noqa` disposition and the
  `remediate_risk_params` fix were both settled by reading the upstream contract, not by reasoning about the call site.
- **Baselines that only ever rise are a smell, not a policy.** `fabricated_sha_citation` went 2->4->6->8 because the
  gate itself mis-reported; the fix was to the gate, and the baseline then ratcheted to 0.

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
- **2026-08-08 (slot 8, data_engineering)** — Block B [CODE] P1 (delete markets/outcomes/settlements) checkbox flip.
  Code was already shipped by a prior slot-8 session at `unified-api-contracts@975f0191`: removed from
  `DATA_TYPES_BY_ASSET_GROUP["sports"]`, `FREQUENCY_MAP`, `NEEDS_CANDLE_PROCESSING`,
  `VALID_DATA_TYPES_BY_INSTRUMENT_TYPE`, `VENUE_DATA_TYPE_CAPABILITIES`, and `SportsMvpRule`; 3 test files updated.
  Codex note already in `/codex/02-data/sports-data-types-catalog.md` lines 183-185, 200-201: "ML labels come from IS
  `fixtures_outcomes`/`matches`, not from the retired types." Session ended before the checkbox was flipped; flipping
  now.
- **2026-08-08 (slot 11, data_engineering)** — Block B [DOCS] P1 (reaffirm 2020-06 floor against P4 backfill) flipped.
  Added a "Reaffirmed against the P4 derived-layer backfill" section to `/codex/02-data/sports-2020-06-data-floor.md`:
  no change to the floor date/window, but states explicitly that (1) the floor's `START_DATE` clamp governs P4's
  `odds_snapshot`/`odds_movement`/arbitrage/`horizon` backfill launchers, same as every other sports launcher already
  enumerated in the enforcement surface, and (2) the P4 C3 pre-launch corpus disposition (10,345 objects) is settled by
  this doc's standing supersession of the 2018 coverage-window-extension option, not a fresh decision — P4 cites this
  doc rather than re-litigating.
