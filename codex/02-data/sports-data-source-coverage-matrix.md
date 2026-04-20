---
scope: [engineer, admin]
---

# Sports Data Source — Coverage Matrix SSOT

**Status:** canonical — consumed by deployment-api data-status aggregator, instruments-service adapter audits, and
downstream coverage dashboards.

**Scope:** for every SPORTS `data_type` in the availability manifest, defines (a) the responsible adapter/source, (b)
which leagues are expected to produce this data_type, (c) the honest-coverage axis the aggregator must use, and (d)
whether `record_empty` is expected.

Cross-refs:

- `codex/02-data/availability-manifest-and-data-status.md` — v5 honest-coverage schema (shard columns, `capture_status`,
  `record_empty` / `record_failed`).
- `codex/02-data/sports-adapter-dependency-order.md` — adapter → entity mapping & T0/T1 wave order.
- `codex/02-data/sports-data-migration.md` — per-league partition migration.
- UAC: `unified_api_contracts.canonical.domain.sports.league_data` — `LEAGUE_REGISTRY`, `get_prediction_leagues`,
  `get_leagues_by_classification("Features"|"Reference")`, `get_league_fixture_calendar`.
- UAC: `unified_api_contracts.canonical.domain.sports.league_registry` —
  `LeagueDefinition.data_sources: frozenset[str]`.

## 1. Expected-league counts per source (observed 2026-04-20)

These counts are live-derived from `LEAGUE_REGISTRY` and are the authoritative denominator for data-status coverage %:

| `data_sources` key     | Leagues expecting this source | Classification breakdown                                      |
| ---------------------- | ----------------------------: | ------------------------------------------------------------- |
| `api_football`         |                            95 | PREDICTION 33 + FEATURES 22 + REFERENCE 40                    |
| `footystats`           |                            46 | PREDICTION 28 + FEATURES 18                                   |
| `odds_api`             |                            33 | PREDICTION 33                                                 |
| `open_meteo`           |                            33 | PREDICTION 33 (weather on fixture dates)                      |
| `soccer_football_info` |                            33 | PREDICTION 33                                                 |
| `transfermarkt`        |                            55 | PREDICTION 33 + FEATURES 22                                   |
| `understat`            |                             5 | PREDICTION 5 (EPL / LA_LIGA / BUNDESLIGA / SERIE_A / LIGUE_1) |

Totals: `LEAGUE_REGISTRY = 102` leagues (PREDICTION 33 + FEATURES 22 + REFERENCE 40 + NON_FOOTBALL 7). Query helpers
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

Expected leagues: `get_leagues_by_classification("Prediction") ∪ ("Features") ∪ ("Reference")` = 95 leagues. Expected
dates resolved per league via `get_league_fixture_calendar(league_id, start, end)` unless the axis is season-scoped.

| data_type         | Coverage axis                          | Expected shards per day                                        | `record_empty` expected                                                                          |
| ----------------- | -------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `FIXTURES`        | per-league × per-fixture-date          | 95 leagues, but only dates inside each league's active season  | Yes — off-season dates write `capture_status=empty_confirmed` (or excluded via fixture calendar) |
| `FIXTURE_EVENTS`  | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes — a fixture with 0 events (rare) writes empty_confirmed                                      |
| `FIXTURE_LINEUPS` | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes                                                                                              |
| `FIXTURE_STATS`   | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes — tier-2+ leagues without stats support still write empty_confirmed                          |
| `PLAYER_STATS`    | per-league × per-fixture-date          | subset of (league, date) pairs with `FIXTURES` rows present    | Yes                                                                                              |
| `INJURIES`        | per-league × daily                     | 95 leagues × active-season dates (daily refresh)               | Yes — no injuries on a date = empty_confirmed                                                    |
| `LEAGUES`         | global × daily snapshot                | 1 shard/day (no league_id — this IS the league reference list) | N/A — daily snapshot; empty means API outage                                                     |
| `TEAMS`           | global × daily snapshot                | 1 shard/day (no league_id — full team directory)               | N/A                                                                                              |
| `STANDINGS`       | per-league × periodic (weekly cadence) | 95 leagues × cadence dates inside active season                | Yes — off-season = empty_confirmed                                                               |
| `VENUES`          | global × season                        | 1 shard per season                                             | N/A                                                                                              |

### 2.2 FootyStats-sourced entities (source key = `footystats`)

Expected leagues: `[l for l in LEAGUE_REGISTRY.values() if "footystats" in l.data_sources]` = 46 (PREDICTION 28 +
FEATURES 18). Note PRED_NO_FOOTYSTATS preset excludes some PREDICTION leagues (subscription limit).

| data_type     | Coverage axis                 | Expected shards per day                                         | `record_empty` expected |
| ------------- | ----------------------------- | --------------------------------------------------------------- | ----------------------- |
| `MATCHES`     | per-league × per-fixture-date | subset of (footystats league, date) pairs with fixtures         | Yes                     |
| `PREDICTIONS` | per-league × per-fixture-date | subset of (footystats league, date) pairs with fixtures         | Yes                     |
| `ODDS`        | per-league × per-fixture-date | (footystats league, date) pairs with fixtures — sparse backfill | Yes                     |

`ODDS` also feeds from `odds_api` (33 PREDICTION leagues) in the live-capture path; batch/backfill currently uses
`footystats_odds`. Aggregator should merge both sources under `ODDS` OR expose them as separate data_types — see §4.

### 2.3 Understat-sourced (source key = `understat`)

Expected leagues: 5 PREDICTION only — EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1.

| data_type | Coverage axis                 | Expected shards per day             | `record_empty` expected |
| --------- | ----------------------------- | ----------------------------------- | ----------------------- |
| `XG`      | per-league × per-fixture-date | 5 leagues × fixture dates in season | Yes                     |

### 2.4 Transfermarkt-sourced (source key = `transfermarkt`)

Expected leagues: 55 (PREDICTION 33 + FEATURES 22). Reference leagues NOT covered.

| data_type               | Coverage axis                          | Expected shards per day    | `record_empty` expected |
| ----------------------- | -------------------------------------- | -------------------------- | ----------------------- |
| `PLAYER_VALUES`         | per-league × periodic (weekly cadence) | 55 leagues × cadence-dates | Yes                     |
| `TRANSFERMARKT_LEAGUES` | per-league × periodic (weekly cadence) | 55 leagues × cadence-dates | Yes                     |

### 2.5 Soccer-Football-Info (SFI) — source key = `soccer_football_info`

Expected leagues: 33 PREDICTION. Singleton-locked launcher per 2026-04-19 incident.

| data_type               | Coverage axis                          | Expected shards per day                    | `record_empty` expected |
| ----------------------- | -------------------------------------- | ------------------------------------------ | ----------------------- |
| `SFI_LEAGUES`           | per-league × periodic (weekly cadence) | 33 leagues × cadence-dates                 | Yes                     |
| `SFI_STANDINGS`         | per-league × periodic (weekly cadence) | 33 leagues × cadence-dates                 | Yes                     |
| `SFI_PROGRESSIVE_STATS` | per-league × per-fixture-date          | (33 SFI leagues, date) pairs with fixtures | Yes                     |

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

- **ODDS duplication.** Aggregator currently merges `odds_api` live capture and `footystats_odds` backfill under `ODDS`.
  Decision: split into `ODDS_LIVE` (odds_api, 33 leagues) vs `ODDS_HIST` (footystats, 46 leagues), or keep merged with
  source-breakdown sub-column. Default pick here: **keep merged, expose source split in drilldown.**

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

- **2026-04-20** — Initial SSOT. Authored during SPORTS data-status audit: manifest was v5-correct on disk but the
  deployment-api aggregator was using FIXTURES row-count as the denominator for 1-to-many children, producing nonsense
  ratios like "BRASILEIRAO 49/2 fixtures 100%" and mislabelling the entity drilldown as "venues". Matrix above
  supersedes any implicit per-data_type coverage rules previously scattered in adapters.
