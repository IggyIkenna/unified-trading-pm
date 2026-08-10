---
doc_type: codex-ssot
title: Sports Data Source — Coverage Matrix SSOT
summary:
  Per-sports-data_type coverage matrix — responsible source, expected-league denominators (api_football 96, footystats
  50, understat 5, …), coverage axis, and record_empty expectations feeding the v5 honest-coverage aggregator.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, execution-service, instruments-service]
scope: [engineer, admin]
tags: [sports, honest-coverage, data-status, footystats, odds, audit]
related:
  [
    /codex/02-data/sports-adapter-dependency-order.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-04-20
authoritative_for: [sports data_type source-to-coverage-axis matrix, per-source expected-league denominators]
referenced_by:
  [
    /codex/01-domain/sports-instruments.md,
    /codex/02-data/chunk-safe-manifest-migrations.md,
    /codex/02-data/mtds-data-source-coverage-matrix.md,
    /codex/02-data/pipeline-coverage-matrix.md,
    /codex/02-data/sports-adapter-dependency-order.md,
    /codex/02-data/sports-data-types-catalog.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
  ]
owner:
last_reviewed: 2026-08-10
code_refs:
---

# Sports Data Source — Coverage Matrix SSOT

> **Note (2026-07-19, fixtures-migration status corrected 2026-07-24).** FIXTURES now writes across two entities —
> `entity=fixtures_schedule` + `entity=fixtures_outcomes` (2026-05-23) — and the fixtures **manifest atom** migration
> off the legacy `data_type="FIXTURES"` umbrella onto `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` **shipped for the CODE
> path** 2026-07-24 (`instruments-service@e19c5a7a` + `@47c1ffb3` — every writer/reader call site, including the
> previously missed `sports_fixture_status_refresh.py` trigger). **Historical backfill is still pending**: a read-only
> prod census (2026-07-24) found 337,464 pre-existing rows still stamped the legacy `FIXTURES` label — tracked as its
> own dispatchable todo in `sports_closeout_batch1_ao_ready_2026_07_24.md`, full analysis in
> `plans/active/issues/fixtures_manifest_legacy_backfill_2026_07_24.md`. Until that backfill lands, expect BOTH labels
> live in the manifest for historical dates. **Casing doctrine has reversed twice since this note's original K0-(b)
> UPPER claim**: 2026-07-22 (K1/K2) migrated `data_type`/`instrument_type` UP to UPPER-case; 2026-07-23 the closeout
> doc's Track C **reversed that decision fully to LOWER-case, for ALL sports data_types** — this is the operator-ruled,
> still-`migration_pending` target, including instruments-service-side reference data_types
> (FIXTURES/INJURIES/TEAMS/STANDINGS), not just the 9 MTDS/MDPS ones (operator ruling 2026-07-24, resolving the
> ambiguity `sports-batch-live.md`/`sports-data-types-catalog.md` left open). **Live data as of 2026-07-24 is still 100%
> UPPER-case for instruments-service sports reference data_types** (read-only prod census, same census that found the
> 337,464 legacy FIXTURES rows above — zero lowercase variants observed) — the lower-case target has NOT yet been
> executed for this bucket; every UPPER-cased `data_type` in §2 below is an accurate representation of CURRENT live
> data, not stale content, even though it will need re-casing once that migration is scoped and run. The 2026-07-22
> K1/K2 UPPER migration is itself now `SUPERSEDED, MUST BE REVERTED` per the closeout — do not treat any UPPER-cased
> sports `data_type`/`instrument_type` value as the FUTURE canonical target (it remains the CURRENT live value). See
> `sports_consolidated_closeout_2026_07_19.md` Track C for the live revert todo, and
> `sports_master_closeout_2026_07_21.md` for the K1/K2 execution history (superseded, not current truth).

**Status:** canonical — consumed by deployment-api data-status aggregator, instruments-service adapter audits, and
downstream coverage dashboards.

**2026-05-22 diagnostic**: `KNOWN_COVERAGE_GAPS = {}` confirmed — sports gaps (FIXTURE_EVENTS/LINEUPS 38d, INJURIES 22d,
ODDS 35d, MATCHES 10d as of 2026-05-22) were genuine unfetched data, NOT UAC coverage-window gaps. Recent-window fills
launched: API_FOOTBALL 2026-04-14→2026-05-22, FOOTYSTATS 2026-04-17→2026-05-22. `instr-backfill-sports` VM
(34.180.105.8) handling historical < 2026-04.

**Scope:** for every SPORTS `data_type` in the availability manifest, defines (a) the responsible adapter/source, (b)
which leagues are expected to produce this data_type, (c) the honest-coverage axis the aggregator must use, and (d)
whether `record_empty` is expected.

Cross-refs:

- `/codex/02-data/availability-manifest-and-data-status.md` — v5 honest-coverage schema (shard columns,
  `capture_status`, `record_empty` / `record_failed`).
- `/codex/02-data/sports-adapter-dependency-order.md` — adapter → entity mapping & T0/T1 wave order.
- `/codex/02-data/per-asset-group-bucket-layouts.md` — per-asset_group bucket layout SSOT (sports section).
- UAC: `unified_api_contracts.canonical.domain.sports.league_data` — `LEAGUE_REGISTRY`, `get_prediction_leagues`,
  `get_leagues_by_classification("Features"|"Reference")`, `get_league_fixture_calendar`.
- UAC: `unified_api_contracts.canonical.domain.sports.league_registry` —
  `LeagueDefinition.data_sources: frozenset[str]`.

## 1. Expected-league counts per source (re-verified live 2026-07-24, originally observed 2026-04-20)

These counts are live-derived from `LEAGUE_REGISTRY` and are the authoritative denominator for data-status coverage %.
**Re-verified 2026-08-10** directly against the live `LEAGUE_REGISTRY` — `footystats` drifted since the 2026-07-24
snapshot (subscription upgrade, see changelog); `odds_api`/`open_meteo`/`soccer_football_info`/`understat`/
`api_football`/`transfermarkt` are unchanged:

| `data_sources` key     | Leagues expecting this source | Classification breakdown                                      |
| ---------------------- | ----------------------------: | ------------------------------------------------------------- |
| `api_football`         |                            96 | PREDICTION 33 + FEATURES 24 + REFERENCE 39                    |
| `footystats`           |                            50 | PREDICTION 32 + FEATURES 18                                   |
| `odds_api`             |                            33 | PREDICTION 33                                                 |
| `open_meteo`           |                            33 | PREDICTION 33 (weather on fixture dates)                      |
| `soccer_football_info` |                            33 | PREDICTION 33                                                 |
| `transfermarkt`        |                            56 | PREDICTION 32 + FEATURES 24                                   |
| `understat`            |                             5 | PREDICTION 5 (EPL / LA_LIGA / BUNDESLIGA / SERIE_A / LIGUE_1) |

Totals: `LEAGUE_REGISTRY = 103` leagues (PREDICTION 33 + FEATURES 24 + REFERENCE 39 + NON_FOOTBALL 7). Query helpers
live at `UAC/canonical/domain/sports/league_data.py`.

## 2. data_type → source → coverage axis matrix

Every row is authoritative for:

1. **Aggregator denominator.** `expected_shards = |expected_leagues| × |expected_dates|` (or the axis-specific form
   below). No magic multipliers.
2. **Adapter invariant.** If the adapter fails for a league on a date, it must emit
   `record_failed(row_key=…, error=classify_venue_error(exc), attempted_at=…)`. If the adapter succeeded but there was
   legitimately no data, it must emit `record_empty(row_key=…, attempted_at=…)`.
3. **UI drilldown.** `league_id` is present when axis is `per-league`; dropped otherwise.

### 2.1 API-Football-sourced entities (source key = `api_football`)

Expected leagues: `get_leagues_by_classification("Prediction") ∪ ("Features") ∪ ("Reference")` = 96 leagues. Expected
dates resolved per league via `get_league_fixture_calendar(league_id, start, end)` unless the axis is season-scoped.

| data_type         | Coverage axis                          | Expected shards per day                                        | `record_empty` expected                                                                          |
| ----------------- | -------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `FIXTURES`        | per-league × per-fixture-date          | 96 leagues, but only dates inside each league's active season  | Yes — off-season dates write `capture_status=empty_confirmed` (or excluded via fixture calendar) |
| `FIXTURE_EVENTS`  | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes — a fixture with 0 events (rare) writes empty_confirmed                                      |
| `FIXTURE_LINEUPS` | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes                                                                                              |
| `FIXTURE_STATS`   | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes — tier-2+ leagues without stats support still write empty_confirmed                          |
| `PLAYER_STATS`    | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes                                                                                              |
| `INJURIES`        | per-league × daily                     | 96 leagues × active-season dates (daily refresh)               | Yes — no injuries on a date = empty_confirmed                                                    |
| `LEAGUES`         | global × daily snapshot                | 1 shard/day (no league_id — this IS the league reference list) | N/A — daily snapshot; empty means API outage                                                     |
| `TEAMS`           | per-league × trigger-date              | 96 leagues × trigger dates (season-start + transfer windows)   | Yes — off-season / non-trigger date per league = empty_confirmed                                 |
| `STANDINGS`       | per-league × periodic (weekly cadence) | 96 leagues × cadence dates inside active season                | Yes — off-season = empty_confirmed                                                               |
| `VENUES`          | global × season                        | 1 shard per season                                             | N/A                                                                                              |

#### Expected column counts per API-Football data_type (regression guard, codified 2026-05-08)

After the api_football minimal-flattening removal (plan:
`plans/active/api_football_minimal_flattening_removal_2026_05_07.md`, UAC@c76e6d0 + instruments-service@539130f), every
API-Football per-fixture parquet on disk must carry the expanded column shape declared in
`unified_api_contracts/internal/schemas/_sports_match_contracts.py`. A future regression to the prior "minimal
flattening" shape (only `fixture_id + data_available_at`) is caught by this row-count gate:

| data_type         | Expected column count\* | UAC SchemaContract       | Symbol column | Row grain                       |
| ----------------- | ----------------------: | ------------------------ | ------------- | ------------------------------- |
| `FIXTURE_STATS`   |                      23 | `SPORTS_FIXTURE_STATS`   | `fixture_id`  | one per (fixture, team)         |
| `FIXTURE_EVENTS`  |                      13 | `SPORTS_FIXTURE_EVENTS`  | `fixture_id`  | one per event                   |
| `FIXTURE_LINEUPS` |                      13 | `SPORTS_FIXTURE_LINEUPS` | `fixture_id`  | one per (fixture, team, player) |
| `INJURIES`        |                      11 | `SPORTS_INJURIES`        | `player_id`   | one per (player, team, fixture) |
| `PLAYER_STATS`    |                      38 | `SPORTS_PLAYER_STATS`    | `player_id`   | one per (fixture, team, player) |

\* Includes `data_available_at`. Authoritative column lists live in the SchemaContract definitions; this table is a
fast-glance regression catch — if a future audit shows fewer columns than listed here for any of these data_types, a
normalizer or adapter regression has dropped fields. Legitimate additions to the column count (new stat type, new event
field) require updating both the SchemaContract and this table in lockstep.

### 2.2 FootyStats-sourced entities (source key = `footystats`)

Expected leagues: `[l for l in LEAGUE_REGISTRY.values() if "footystats" in l.data_sources]` = 50 (PREDICTION 32 +
FEATURES 18). Note PRED_NO_FOOTYSTATS preset still excludes 1 PREDICTION league (subscription limit, raised but not
removed 2026-08-07 — see changelog).

| data_type     | Coverage axis                 | Expected shards per day                                         | `record_empty` expected |
| ------------- | ----------------------------- | --------------------------------------------------------------- | ----------------------- |
| `MATCHES`     | per-league × per-fixture-date | subset of (footystats league, date) pairs with fixtures         | Yes                     |
| `PREDICTIONS` | per-league × per-fixture-date | subset of (footystats league, date) pairs with fixtures         | Yes                     |
| `ODDS`        | per-league × per-fixture-date | (footystats league, date) pairs with fixtures — sparse backfill | Yes                     |

**`ODDS` here = footystats pre-match snapshot only** (one capture per league × date, opening odds across 68 markets,
`data_available_at = kickoff - 72h`). Per the C.2 resolution at §4, `odds_api` intra-day market movement (8 horizon
buckets) lives in MTDS as `odds_horizon_bucket`, not in instruments-service ODDS. They are different-purpose data that
legitimately coexist; do NOT merge in the aggregator.

**`PREDICTIONS` vs `ODDS` — disambiguation (C.3 audit 2026-05-07).** Both data_types render side-by-side in the
deployment-ui data-status panel and both come from FootyStats, but they are **different classes of data**:

- **`PREDICTIONS`** = FootyStats's PROPRIETARY pre-match forecast model. Carries `*_potential` fields (btts_potential,
  o05/o15/o25/o35/o45_potential, corners_potential, cards_potential, offsides_potential, avg_potential), pre-match xG
  (xg_prematch_home/away/total), and per-team PPG projections (pre_match_home_ppg / pre_match_away_ppg /
  home_overall_ppg / away_overall_ppg). These are MODEL OUTPUT — likelihood scores produced by FootyStats's own
  algorithm. They look odds-like but are NOT bookmaker quotes. Normalizer:
  `unified_api_contracts/external/footystats/normalize.py:normalize_footystats_predictions`. Path:
  `gs://instruments-store-sports-prd-{pid}/sports_reference/by_date/day=*/entity=footystats_predictions/league={L}/footystats_predictions.parquet`.

- **`ODDS`** = REAL bookmaker odds aggregated by FootyStats from named books. The pre-match snapshot variant captures 68
  markets at `kickoff - 72h`. These are MARKET DATA — what bookmakers actually offered. Normalizers:
  `normalize_footystats_odds` (per-row CanonicalOdds shape) and `normalize_footystats_odds_snapshot` (flat-row 68-market
  pre-match). Path: `entity=footystats_odds/league={L}/footystats_odds.parquet`.

**Implication for downstream consumers**: features-sports must NOT merge `PREDICTIONS` + `ODDS` into a single
"opinion-on-the-match" column — they have different statistical properties (FootyStats model bias / quality vs market
efficiency) and should be separate features. Strategy-service models that target ODDS as the prediction target should
NEVER use PREDICTIONS as an input feature for the same fixture (same-source label leakage).

### 2.3 Understat-sourced (source key = `understat`)

Expected leagues: 5 PREDICTION only — EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1.

| data_type | Coverage axis                 | Expected shards per day             | `record_empty` expected |
| --------- | ----------------------------- | ----------------------------------- | ----------------------- |
| `XG`      | per-league × per-fixture-date | 5 leagues × fixture dates in season | Yes                     |

**Dormant contingency — 3-way understat absence split (`EXPECTED_NO_PROVIDER_COVERAGE`), archived 2026-07-27**: the
2-way split above (`record_failed` for genuinely-errored leagues, `record_empty` for the rest) is currently CORRECT
because `get_expected_leagues_for_source("understat", ["Prediction"])` already returns ONLY the 5 understat-native
leagues (EPL/LA_LIGA/BUNDESLIGA/SERIE_A/LIGUE_1) — the denominator never contains a league understat doesn't cover, so a
3-way split has nothing to do today. A 3-way split (provider-not-covering → `EXPECTED_NO_PROVIDER_COVERAGE`;
covered+errored → `failed`; covered+no-fixture → `EXPECTED_NO_FIXTURE`) becomes necessary ONLY if the understat expected
denominator ever broadens to include a league understat lacks. If that happens: add `XG`/`XG_SHOTS` keys to UAC
`LEAGUE_ENTITY_COVERAGE` (`registry/sports_league_entity_coverage`) built from understat's OWN observed corpus (NOT
API-Football's, which is what that map is keyed on today — wiring it in as-is would mislabel every understat absence,
including real 404 failures and genuine no-fixture days, as `EXPECTED_NO_PROVIDER_COVERAGE`), then apply the
`is_league_entity_covered`-first ordering. Provenance:
`/plans/archive/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` P3 fix (originally diagnosed
2026-06-24).

### 2.4 Transfermarkt-sourced (source key = `transfermarkt`)

Expected leagues: 56 (PREDICTION 32 + FEATURES 24). Reference leagues NOT covered.

**2026-07-08 correction**: `PLAYER_VALUES`'s axis below was stale — it previously read
`per-league × periodic (weekly cadence)`, describing pre-2026-04-29 behavior. The 2026-04-29 reconciliation
(deployment-api commit `6b7aa696`, landed 2026-06-11) deleted 167k phantom denorm-to-fixture-date rows and moved
`PLAYER_VALUES` onto the axis below. Verified live 2026-07-08 by downloading the real production manifest
(`gs://instruments-store-sports-prd-{pid}/_index/availability_index.parquet`) and calling the real
`sports_honest_coverage()` against it: 2,564 / 3,400 expected (league, trigger-date) shards = 75.41% all-time
(2014-2026), 439 / 441 = 99.55% for the current era (2025-01-01 to 2026-07-08) — see
`instruments-service/docs/SPORTS_INSTRUMENTS.md` § "Reference-data providers" for the full before/after writeup.
**HISTORICAL-ONLY as of 2026-07-24**: this 2026-07-08 all-time figure predates the operator-ruled 2020-06-06 sports data
floor (`sports_master_closeout_2026_07_21.md`, ruled 2026-07-21; `/codex/02-data/sports-2020-06-data-floor.md`) —
pre-2020-06 rows are fabrication-by-construction and have since been wiped from the tick/features buckets (the
reference-data bucket's pre-floor wipe status is tracked separately in the closeout). The 75.41% all-time / 2014-2026
denominator above has NOT been re-measured against the post-floor manifest and should not be relied on for current
honest-coverage numbers — treat it as a historical record of the pre-floor state, not current truth. The 99.55%
current-era (2025-01-01 to 2026-07-08) figure is unaffected (entirely post-floor). `TRANSFERMARKT_LEAGUES` is retired
(2026-05-05, per `deployment-api`'s `sports_helpers.py` comment) — its row below is a historical record, not a
currently-active data_type.

| data_type               | Coverage axis                                                                                                              | Expected shards per day                                                 | `record_empty` expected |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------- |
| `PLAYER_VALUES`         | per-league × trigger-date (season-start + transfer-window-open + transfer-window-close, via `get_reference_refresh_dates`) | 56 leagues × ~3-4 trigger-dates/year (NOT daily/weekly cadence-sampled) | Yes                     |
| `TRANSFERMARKT_LEAGUES` | per-league × periodic (weekly cadence) — RETIRED 2026-05-05                                                                | 56 leagues × cadence-dates (historical only)                            | Yes                     |

### 2.5 Soccer-Football-Info (SFI) — source key = `soccer_football_info`

Expected leagues: 33 PREDICTION. Singleton-locked launcher per 2026-04-19 incident.

| data_type               | Coverage axis                                                                                                                                                                                                                | Expected shards per day                      | `record_empty` expected |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ----------------------- |
| `SFI_LEAGUES`           | per-league × periodic (weekly cadence) — RETIRED 2026-05-05 (same commit as `TRANSFERMARKT_LEAGUES` above, `unified-api-contracts@b5210c2b`; catalog mapping now lives in UAC `SOCCER_FOOTBALL_INFO_IDS`, not captured data) | 33 leagues × cadence-dates (historical only) | Yes                     |
| `SFI_STANDINGS`         | per-league × periodic (weekly cadence)                                                                                                                                                                                       | 33 leagues × cadence-dates                   | Yes                     |
| `SFI_PROGRESSIVE_STATS` | per-league × per-fixture-date                                                                                                                                                                                                | (33 SFI leagues, date) pairs with fixtures   | Yes                     |

### 2.6 Open-Meteo (weather) — source key = `open_meteo`

Expected leagues: 33 PREDICTION. Unit is (fixture, venue) — one weather row per fixture, looked up by stadium
coordinates.

| data_type | Coverage axis                                | Expected shards per day                                                | `record_empty` expected                 |
| --------- | -------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------- |
| `WEATHER` | per-league × per-fixture-date (venue-scoped) | (33 leagues, date) pairs where FIXTURES exist — 1 shard per league-day | Yes — indoor fixtures = empty_confirmed |

## 3. Aggregator algorithm (v5 honest-coverage)

For each `(category, data_type)` the data-status aggregator computes:

```python
src = DATA_TYPE_SOURCE_MAP[data_type]              # e.g. "api_football"
classes = DATA_TYPE_EXPECTED_CLASSIFICATIONS[data_type]  # e.g. {"Prediction","Features","Reference"}
expected_leagues = [
    l for l in LEAGUE_REGISTRY.values()
    if src in l.data_sources and l.classification in classes
]

axis = DATA_TYPE_AXIS[data_type]  # one of: per_league_per_fixture_date, per_league_periodic, global_periodic, global_season

if axis == "per_league_per_fixture_date":
    expected_pairs = set()
    for l in expected_leagues:
        for d in get_league_fixture_calendar(l.league_id, start, end):
            expected_pairs.add((l.league_id, d))
    found_pairs = set(
        (row.league_id, row.date) for row in manifest
        if row.data_type == data_type and row.capture_status in ("captured", "empty_confirmed")
    )
    ratio = len(found_pairs) / len(expected_pairs)

elif axis == "per_league_periodic":
    # cadence defined per data_type (daily, weekly). expected = |leagues| × |cadence_dates in window|
    ...

elif axis == "global_periodic":
    # expected = |cadence_dates in window| (no league axis)
    ...

elif axis == "global_season":
    # expected = |seasons in window|
    ...
```

No multipliers. No FIXTURES-as-denominator. `capture_status="empty_confirmed"` counts toward `found_shards` because the
adapter _tried_ and _recorded_ the legitimate zero — that's the whole point of v5.

## 4. Open questions / follow-ups

- **ODDS duplication — RESOLVED 2026-05-07** (C.2 audit per `plans/ai/session_2026_05_07_data_status_audit_findings.md`
  row C.2). The data-status panel surfaces `data_type=ODDS` in instruments-service AND `odds_horizon_bucket` in MTDS as
  separate panels, which had felt redundant. Investigation outcome: they are **not duplicates**, they serve different
  purposes and SHOULD coexist:
  - **`ODDS` in instruments-service** = pre-match snapshot from FootyStats `get_fixture_odds_snapshot()`
    (`instruments-service/instruments_service/engine/orchestrator.py:4760-4900`). Captures opening odds across 68
    markets at fetch time. PIT semantics: `data_available_at = kickoff - 72h` (FootyStats publishes ~3 days before
    kickoff; 98% by T-24h, 100% by T-72h). Path:
    `gs://instruments-store-sports-prd-{pid}/sports_reference/by_date/day=*/entity=footystats_odds/league={L}/footystats_odds.parquet`.
    Refdata-style: one snapshot per (league, date), captured once. Used by features-sports for backtest training.
  - **`odds_api` in MTDS** = live + historical intra-day market movement, bucketed at 8 horizons (T-24h, T-12h, T-6h,
    T-4h, T-2h, T-1h, T-10m, T-0). Coverage start per
    [`availability-manifest-and-data-status.md` § Source coverage start dates (canonical)](./availability-manifest-and-data-status.md#source-coverage-start-dates-canonical--source_coverage_start-ssot)
    (UAC `unified_api_contracts.sports.SOURCE_COVERAGE_START` runtime SSOT). Used by execution-service for live trading
    - features-sports for movement features (CLV, steam, late-money).
  - **api_football `/odds`** is NOT used by instruments-service. The footystats_odds adapter has `get_odds()` defined as
    a deprecated stub that logs "use get_fixture_odds_snapshot() instead" — there is no api_football odds path.
  - **Decision**: keep both in their current homes. NO migration. The data-status panel SHOULD render them under their
    respective service nodes (ODDS under instruments-service, odds_horizon_bucket under MTDS); operator clarity comes
    from the panel disambiguating the two purposes (pre-match opening snapshot vs intra-day movement). Schema-modal
    descriptions for both data_types should call out the distinction explicitly per C.3 (also folded into
    `sports_master.md` § Audit findings).

- **V2 manifest rows (496 rows, empty league_id).** Pollute per-league drilldown because they sum into totals with blank
  league. Aggregator must filter `schema_version >= 4` for per-league axes. A one-off delete of v2 rows is out of scope
  here (safe to leave; the v2 cohort writes stopped 2026-04-16).

- **FIXTURES undercount.** Per-league FIXTURES sums are 10–500× lower than a full season (EPL=5, BRASILEIRAO=2,
  SERIE_A=15) vs USL_CHAMPIONSHIP=639, UCL=132 which look right. Root cause likely the `rescan_sports_manifest.py`
  dedup-by-entity bug ignoring per-league parquet splits + live writes only covering the small set of leagues actively
  being ingested. Resolution path: VM backfill (production tarball, singleton-locked launcher). Tracked separately.

- **v5 rollout.** Only 2 rows are v5 on disk today (2026-04-20 01:28). `expected` + `available` + `capture_status`
  columns exist in schema but are only populated on the newest writes. v4 rows dominate; aggregator must treat
  `capture_status.isna()` as implicit `captured` for v4 rows, OR re-run the rescan to write v5-shaped rows once the
  dedup bug is fixed.

## 5. Changelog

- **2026-08-10** — `footystats` expected-league count corrected 48→50 (§1 table, §2.2, summary/frontmatter) — a
  2026-08-07 operator subscription upgrade (`unified-api-contracts@7810dad61`, `SPORTS_LEAGUES_CONFIG_VERSION` 2→3)
  raised the footystats league cap, moving 4 PREDICTION-tier leagues (ARGENTINA_PRIMERA, CHILE_PRIMERA, LIGA_MX,
  K_LEAGUE_1) from `PRED_NO_FOOTYSTATS`→`PRED_NO_UNDERSTAT` and dropping 2 FEATURES-tier leagues (CHINA_SUPER_LEAGUE,
  RUSSIA_PREMIER_LEAGUE, neither has a Prediction-tier sibling) entirely out of scope. New breakdown: PREDICTION 28→32,
  FEATURES 20→18, net 48→50. Verified same-day in prod: the 4 additions backfilled clean (0 gaps), the 2 removals' stale
  captured rows purged (4,458 rows, 0 residual). This doc had not been updated since the change landed — found stale via
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.
- **2026-07-24** — Stale-under-banner verification pass (`sports_closeout_batch1_ao_ready_2026_07_24.md` [DOC] P2):
  every claim in the top banner re-checked against a fresh read-only prod census. Corrected the FIXTURES-migration
  status claim (code path shipped `instruments-service@e19c5a7a`/`@47c1ffb3`, historical backfill of 337,464 legacy rows
  tracked separately — was stale-claiming "migration pending" for the whole thing). Clarified the LOWER-case casing
  target is still `migration_pending`, NOT yet live — a fresh census confirmed 100% UPPER-case live data for
  instruments-service sports reference `data_type`s, so the body's §2 UPPER-case examples are current-accurate, not
  stale. §1's expected-league-count table (LEAGUE_REGISTRY-derived) had drifted since its 2026-04-20 snapshot —
  re-verified live: `api_football` 95→96, `footystats` 46→48, `transfermarkt` 55→56, total registry 102→103
  (`odds_api`/`open_meteo`/`soccer_football_info`/`understat` unchanged at 33/33/33/5); propagated the corrected counts
  through §2.1/§2.2/§2.4's inline restatements too. Fixed the 5(now-7)-broken `related:` paths in `sports_master.md`
  (files archived from `active/` to dated `archive/` subdirs without their referrer being updated).

- **2026-07-08** — §2.4 `PLAYER_VALUES` axis corrected from stale `per-league × periodic (weekly cadence)` to the real,
  currently-shipped `per-league × trigger-date` axis (deployment-api commit `6b7aa696`, landed 2026-06-11 — this doc had
  not been updated since, despite `last_reviewed: 2026-05-22` postdating the code change). Verified live against the
  real production manifest + the real `sports_honest_coverage()` function (not re-implemented): 75.41% all-time / 99.55%
  current-era for Transfermarkt `PLAYER_VALUES`; 99.9% all-time / 99.56% current-era for SFI `SFI_PROGRESSIVE_STATS`
  (§2.5 axis — `per_league_per_fixture_date` — was already correct, no change needed there). Full writeup:
  `instruments-service/docs/SPORTS_INSTRUMENTS.md` § "Reference-data providers".

- **2026-04-20** — Initial SSOT. Authored during SPORTS data-status audit: manifest was v5-correct on disk but the
  deployment-api aggregator was using FIXTURES row-count as the denominator for 1-to-many children, producing nonsense
  ratios like "BRASILEIRAO 49/2 fixtures 100%" and mislabelling the entity drilldown as "venues". Matrix above
  supersedes any implicit per-data_type coverage rules previously scattered in adapters.

- **2026-05-07** — Resolved §4 "ODDS duplication" open question (C.2 audit per
  `plans/ai/session_2026_05_07_data_status_audit_findings.md` row C.2). Investigation: instruments-service
  `data_type=ODDS` writer is footystats `get_fixture_odds_snapshot()` only (no api_football, no odds_api). MTDS
  `odds_api` lives as `odds_horizon_bucket` data_type with 8-horizon intra-day movement buckets. The two are
  different-purpose data (refdata-style pre-match snapshot vs intra-day market movement) and should coexist in their
  current homes — NO migration, NO merge. §2.2 + §4 updated; schema-modal disambiguation tracked under C.3 in
  `sports_master.md`.

- **2026-05-08** — Added "Expected column counts per API-Football data_type" sub-section under §2.1 as a future-audit
  regression guard. Plan `plans/active/api_football_minimal_flattening_removal_2026_05_07.md` shipped flattening for
  FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES (UAC@c76e6d0 + instruments-service@539130f). Prior
  parquets carried only `fixture_id + data_available_at` (the "minimal flattening" known limitation called out in the
  `_sports_match_contracts.py` module docstring); the new normalizers expand to 11–23 columns per data_type matching the
  extended SchemaContract shapes. A future audit that finds the column count below the table values means a normalizer /
  adapter regression has dropped fields.
