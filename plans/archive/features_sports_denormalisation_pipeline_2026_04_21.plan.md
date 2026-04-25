---
title: "features-sports-service — Per-Fixture Denormalisation Pipeline (Player Values / Standings / Weather Joins)"
priority: P0
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
depends_on: []
isProject: false
---

## PRE-AUDIT-FINDINGS (2026-04-21 — agent)

Executed Phase 0 audit before any code. Key deltas from the plan's conceptual design:

### Existing service shape

- `features-sports-service` already has a comprehensive per-fixture feature pipeline —
  `features_sports_service/exporters/derived_features_exporter.py` (1,505 LoC) — that produces one row per fixture ×
  ~780 columns by running 24 calculators over `read_all_reference_data(date_str)` output from the instruments-store GCS
  bucket.
- Output already written by `BatchHandler` with per-shard `ManifestWriter` + `record_empty`/`record_failed` (v5
  discipline in place; shard-level isolation enforced).
- CLI: `--operation compute --mode batch --date YYYY-MM-DD [--tables ...]` (ServiceBootstrap pattern). Feature-group
  tables: `derived_features`, `odds_features`, plus 14 reference passthrough tables.
- GCS output prefix: `gs://features-sports-{project}/sports_features/by_date/day={D}/feature_group={fg}/`.
- `TABLE_SCHEMAS` registry in `features_sports_service/schemas/output_schemas.py`; column lists in
  `features_sports_service/schemas/feature_catalog.py` (local, mirror UAC `SportsFeatureVector` mixins in
  `unified_api_contracts.internal.domain.features_sports`).

### Raw-input GCS paths confirmed for `day=2024-09-01` (project `central-element-323112`)

| Entity                        | Path                                                                                                              | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| fixtures                      | `sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet`                                               | 170 rows on 2024-09-01; cols use af-prefix (`af_fixture_id`, `af_home_id`, `af_league_id`, `af_home_name`, …); `timestamp` = kickoff UTC; no canonical `kickoff_utc`/`league_id`/`home_team_id` columns                                                                                                                                                                                                                                     |
| weather                       | `…/entity=weather/weather.parquet`                                                                                | Already denormalised by venue: one row per `(venue_id, date)` with pre-computed kickoff-hour buckets — `actual_ko_temp`, `actual_ko_precip_mm`, `actual_ko_wind_kmh`, `actual_ko_humidity_pct`, `actual_ko_cloud_pct`, `actual_ko_weather_code` for historical; `forecast_t24h_ko_*` / `forecast_t0_ko_*` for forecast slots. Includes `kickoff_hour` + lat/lon. Hourly-bucket join is already pre-computed upstream by instruments-service |
| standings (API-Football)      | `…/entity=standings/standings.parquet`                                                                            | 720 rows on 2024-09-01; cols `rank, team (nested dict with id/name/logo), points, goalsDiff, form, league_id, data_available_at`. Per-day partition; no `season`/`date` columns in rows                                                                                                                                                                                                                                                     |
| venues (static)               | `…/by_date/day=all/entity=venues/venues.parquet`                                                                  | 3,445 rows; cols `venue_id, name, city, country, capacity, surface, latitude, longitude, altitude`. Lat/lon NaN for many rows (pre-audit sample had both NaN)                                                                                                                                                                                                                                                                               |
| player_values (Transfermarkt) | `…/entity=player_values/player_values.parquet` (also `entity=player_values/league=*/transfermarkt_teams.parquet`) | Only `day=2019-01-01 / 2019-01-02` partitions populated in prod bucket. No `day=2024-*` partitions exist. For 2024-09-01 dry-run the Transfermarkt join legitimately produces NULL columns — honest-coverage                                                                                                                                                                                                                                |
| sfi_standings                 | not present under `entity=sfi_standings/` on any date partition in prod bucket                                    | Only `entity=sfi_leagues` (2019 only) exists. For this plan's SFI-standings join we fall back to API-Football `entity=standings` from `day=kickoff_date - 1` as the pre-match proxy and NULL when absent                                                                                                                                                                                                                                    |

### Gaps vs plan's conceptual design

1. Weather join — existing `exporters/_weather_fetcher.py` does NOT consume the raw `entity=weather` parquet; it reads
   columns off the fixtures DataFrame (which does not have them). New pipeline must read `weather.parquet` directly,
   join on `venue_id`, and pick `actual_ko_*` for historical / `forecast_t0_ko_*` for forward-poll dates.
2. Transfermarkt team-value asof — existing `calculators/squad_value_calculator.py` reads team-level `squad_data`
   aggregates (`total_market_value_eur`, `squad_size`) from `player_values` partition on the target date and defaults
   missing data to zero (data-crime per codex §5). A new pipeline is needed that performs
   `FIXTURE_LINEUPS × PLAYER_VALUES` asof join (`as_of_date <= kickoff_date` strict), with NULL propagation and a
   `team_value_coverage_pct` column.
3. SFI standings pre-match — existing `_compute_league_batch` reads `entity=standings` from `day=kickoff_date` (could
   include post-match updates → lookahead). Correct read is `day=kickoff_date - 1` (pre-match table) for API-Football
   standings used as SFI proxy.
4. FixtureFeatures UAC contract — not present. `SportsFeatureVector` (in
   `internal/domain/features_sports/feature_vector.py`) is a 20-mixin composite covering all feature families; there is
   no dedicated Pydantic model for the three-way denormalisation output. Must add `FixtureFeatures` BaseModel in
   `internal/domain/features_sports/fixture_features.py` and re-export via `internal/__init__.py`.
5. `asof_lookup` helper in UTL — not present. UTL has `PointInTimeEnforcer`, `enforce_point_in_time`, and
   `validate_pit_safety` (row-filter after observation ≤ as_of), but no per-key latest-before-or-equal lookup. Helper
   goes in `unified_trading_library/domain_client/asof_join.py`.

### Downstream consumer impact

Consumers of UAC features_sports domain: `strategy-service`, `ml-training-service`, `ml-inference-service`, plus
internal `SportsFeatureVector` importers in this repo. Adding a new `FixtureFeatures` Pydantic model and a new
`fixture_features` feature-group table is purely additive — no rename, no column deletion, no consumer changes required
in this plan.

### Execution strategy (confirmed after audit)

The new pipeline ships as a new feature-group `fixture_features` alongside `derived_features` + `odds_features`:

- New file `features_sports_service/pipeline/fixture_features.py` — owns the three-way as-of join (Transfermarkt team
  value, SFI/API-Football standings pre-match, OpenMeteo kickoff-hour weather).
- New entry in `TABLE_SCHEMAS`, `feature_catalog.py` column list.
- Wired into `BatchHandler` with its own `record_empty` / `record_failed` /
  `manifest.add(…, feature_group="fixture_features")` block.
- UAC schema `FixtureFeatures` imported and used to type the output row.
- Existing `derived_features` pipeline is untouched — fixing its squad-value zero-default and standings-lookahead are
  out-of-scope for this plan.

### Plan deltas — column list stays as declared

The conceptual column list in Phase 1 is valid. Two minor renames for parquet-source clarity:

- `kickoff_temp_c → kickoff_temperature_c`
- Add provenance columns: `transfermarkt_values_partition_used: str | None`, `standings_partition_used: str | None` —
  both the shard-partition day the join consumed, or `None` when no parquet matched.

### Out-of-scope follow-ups (logged for later plans)

1. Fix `calculators/squad_value_calculator.py` zero-default → `None`. Separate plan.
2. Fix `_compute_league_batch` to read `day=kickoff_date - 1` standings partition. Separate plan.
3. Transfermarkt `player_values` 2020-2026 backfill VM run (paths exist for 2019 only). Backfill operator.
4. SFI_STANDINGS proper backfill under `entity=sfi_standings/`. Backfill operator.

---

## Context

The sports raw-data layer shards by the **natural key** of each source:

- API-Football `FIXTURES` / `FIXTURE_EVENTS` / `FIXTURE_STATS` / `FIXTURE_LINEUPS` / `PLAYER_STATS` → `fixture_id`.
- Transfermarkt `PLAYER_VALUES` → `(player_id, as_of_date)`.
- SFI `SFI_STANDINGS` → `(date, league_id)`.
- OpenMeteo `WEATHER` → `(venue_lat, venue_lon, date)`.
- Understat `XG` → `fixture_id` (after parsing).
- FootyStats → `fixture_id`.

The 2026-04-21 codex `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §9 locks the contract: raw
shards stay normalised by their natural key; `features-sports-service` **denormalises everything onto `fixture_id`**
with strict **as-of discipline** so every fixture has:

- `home_team_value_eur_as_of_kickoff`, `away_team_value_eur_as_of_kickoff` (Transfermarkt).
- `home_standing_pre_match`, `away_standing_pre_match` (SFI).
- `kickoff_weather_temp_c`, `kickoff_weather_precip_mm`, `kickoff_weather_wind_kph`, … (OpenMeteo).
- …in addition to the fixture-native columns already present.

The join must NEVER leak lookahead: `as_of_date <= kickoff_date` strict for time-varying values; `kickoff_utc` bucket
for hourly weather.

### Blast radius

- **features-sports-service** (primary):
  - Determine if a fixture-level feature writer exists today. If yes, add the new columns to it. If no, this plan
    creates the writer.
  - GCS output path — suggest
    `gs://features-sports-{pid}/by_date/day={D}/ entity=fixture_features/fixture_features.parquet` or per-league
    sharding mirroring the manifest. Final path decided in Phase 1 pre-audit.
  - Manifest writes via UTL `ManifestWriter` with `data_type=FIXTURE_FEATURES` (or existing name — confirm in
    pre-audit).
- **unified-api-contracts**:
  - `unified_api_contracts.internal.features.sports` or similar — add the `FixtureFeatures` schema (TypedDict / pydantic
    model) with all join output columns. Must be in UAC since features cross repo boundaries.
  - Add a helper like `as_of_lookup(records, as_of_date, date_col="as_of_date")` if one doesn't already live in UAC for
    time-series lookups.
- **unified-trading-library**:
  - If there's a shared "as-of join" helper (check `domain_client/` or `feature_calculator/`), use it. Otherwise keep
    the join logic in features-sports-service; hoist only if a second service needs it.
- **Downstream consumers**:
  - `strategy-service` sports strategies will need to know these new columns exist. Grep for any hardcoded column list —
    if absent, no downstream change needed; strategy code reads from UAC schema.
  - `ml-training-service` + `ml-inference-service` — same: they read via UAC-declared feature contract.

### Pre-audit manifest (partial — some unknown until executed)

| File / thing to find                                                | Purpose                                                                    | Expected outcome                                                          |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `features-sports-service/features_sports_service/` tree             | Understand current service shape: entry point, feature computers, outputs. | Map existing feature-write paths to decide: extend or greenfield.         |
| `features-sports-service/features_sports_service/*/main.py`         | Service entry (`__main__`) + CLI.                                          | Confirm how batch date ranges trigger feature compute.                    |
| `unified-api-contracts/unified_api_contracts/internal/features/`    | Existing sports feature schemas.                                           | Find existing `FixtureFeatures` or equivalent. Extend it.                 |
| `unified-api-contracts/unified_api_contracts/sports/league_data.py` | Existing helpers for league / fixture lookups.                             | Confirm `get_league_fixture_calendar`, `get_expected_leagues_for_source`. |
| Raw data paths on GCS                                               | Actual layout of Transfermarkt / SFI / weather parquets.                   | Validate join-path assumptions below.                                     |

The execution agent MUST run this pre-audit in Phase 0 before writing code. The join columns listed below assume the
codex as source of truth but are subject to correction on empirical audit.

### The join — conceptual

For each fixture in the target date range:

```
fixture_id, kickoff_utc, home_team_id, away_team_id, venue_id, league_id
        │
        ├── join Transfermarkt PLAYER_VALUES
        │   filter: player_id in (home_lineup ∪ away_lineup ∪ home_squad ∪ away_squad)
        │   filter: as_of_date <= kickoff_date
        │   aggregate: per team, sum-of-max(value) per player → team_value_eur
        │
        ├── join SFI_STANDINGS
        │   filter: league_id == fixture.league_id
        │   filter: date == kickoff_date - 1 day (use "pre-matchday" table)
        │   extract: home_standing, away_standing, home_points, away_points
        │
        ├── join OPENMETEO_WEATHER
        │   resolve: venue_id → (lat, lon)
        │   filter: date == kickoff_date, hour == kickoff_utc.hour
        │   extract: temp_c, precip_mm, wind_kph, humidity, cloud_cover, weather_code
        │
        └── produce: FixtureFeatures row
```

Missing inputs:

- Transfermarkt value absent for a player → treat as `NULL` (leave in aggregate; do NOT default to 0 — it's not
  "zero-value" it's "unknown").
- SFI standings absent → row has `NULL` standing; do NOT fall back to alphabetical or today's standings (lookahead
  bias).
- OpenMeteo weather absent (pre-deployment history for 2018-2019) → `NULL` columns. Do NOT fetch current-date weather
  onto a 2018 fixture.

### Success criteria

- `features-sports-service` produces a per-fixture parquet with all three joined data sources (Transfermarkt / SFI /
  weather) for any date where the raw inputs exist on GCS.
- `as_of_date <= kickoff_date` is strictly enforced for Transfermarkt values; a unit test proves lookahead is not
  possible even when the source has future data.
- Weather join picks the hourly bucket containing `kickoff_utc` — unit test with a 15:30 UTC kickoff picks the
  15:00-16:00 bucket.
- Fixtures with missing raw inputs produce a row with `NULL` columns (not zeros, not "latest available");
  `capture_status` reflects partial vs complete (decide in Phase 1 whether the manifest shard status should be
  `captured` / `partial_captured` / `empty_confirmed` when inputs are missing).
- Schema declared in UAC `internal.features.sports` — downstream services consume via import, not by reading parquet
  columns.
- `bash features-sports-service/scripts/quality-gates.sh` green.
- `bash unified-api-contracts/scripts/quality-gates.sh` green.
- One end-to-end dry-run on 2024-09-01 (EPL Matchday 3) produces fixture features for all ~10 EPL matches with populated
  weather + Transfermarkt + SFI columns. Spot-check one fixture manually.

## Phases

### Phase 0: Pre-audit [SEQUENTIAL — do first, do not skip]

- [x] [AGENT] P0. Read `features-sports-service/features_sports_service/` tree. Document: existing entry points,
      existing feature schemas, existing output paths, existing manifest conventions. Update this plan's pre-audit table
      with what you found (embed in a PRE-AUDIT-FINDINGS section at the top of this file).

- [x] [AGENT] P0. Read `unified-api-contracts/unified_api_contracts/internal/features/` — enumerate existing sports
      feature contracts. Identify the right place to add `FixtureFeatures` (extend existing or create new).

- [x] [AGENT] P0. List GCS paths for all four raw inputs via `gsutil ls gs://instruments-store-sports-.../` for a
      known-good date (e.g. 2024-09-01): - Fixtures:
      `sports_reference/by_date/day=2024-09-01/entity=fixtures/fixtures.parquet`. - SFI standings: path TBC. -
      Transfermarkt values: path TBC. - OpenMeteo weather: path TBC. Update the plan with confirmed paths.

- [x] [AGENT] P0. Spot-check the real parquet schemas with `pd.read_parquet(...).head()` / `.columns` to confirm column
      names assumed in the conceptual join above. Discrepancies update this plan.

### Phase 1: UAC schema + shared as-of helper [SEQUENTIAL, depends on Phase 0]

- [x] [AGENT] P0. Declare `FixtureFeatures` in UAC (internal module) with these columns minimum: - `fixture_id: str`,
      `kickoff_utc: datetime`, `league_id: str`, `home_team_id: str`, `away_team_id: str`, `venue_id: str`. -
      Transfermarkt: `home_team_value_eur_as_of_kickoff: float | None`,
      `away_team_value_eur_as_of_kickoff: float | None`, `team_value_coverage_pct: float` (fraction of lineup with known
      values). - SFI: `home_standing_pre: int | None`, `away_standing_pre: int | None`, `home_points_pre: int | None`,
      `away_points_pre: int | None`. - Weather: `kickoff_temp_c: float | None`, `kickoff_precip_mm: float | None`,
      `kickoff_wind_kph: float | None`, `kickoff_humidity_pct: float | None`, `kickoff_cloud_cover_pct: float | None`,
      `kickoff_weather_code: int | None`. - Metadata: `feature_computed_at: datetime`, `schema_version: int = 1`.

- [x] [AGENT] P0. If a reusable "as-of-join" helper doesn't exist in UTL, add one to
      `unified-trading-library/unified_trading_library/domain_client/` or similar:
      `asof_lookup(df, key_col, date_col, as_of_date) ->     row_or_none`. Single file, single function, tested. If it
      DOES exist, reuse it.

- [x] [AGENT] P0. Unit tests for the schema + the helper: - Schema round-trips via pydantic / TypedDict instantiation. -
      `asof_lookup` picks the latest-before-or-equal; returns None if no row satisfies; strict `<=` semantics.

### Phase 2: Join pipeline — per fixture [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. Create (or extend) `features_sports_service/pipeline/fixture_features.py` — the denormalisation
      pipeline:
      `python     def compute_fixture_features(         fixture_date: date,         categories: list[str] = None,     ) -> list[FixtureFeatures]:         # 1. Load fixtures for date from sports_reference/by_date/day=D/entity=fixtures/         # 2. For each fixture:         #    a. Transfermarkt join (home + away team squad × PLAYER_VALUES asof)         #    b. SFI join (league standings asof kickoff_date - 1)         #    c. Weather join (venue lat/lon × hourly OpenMeteo asof kickoff hour)         # 3. Return list of FixtureFeatures dicts     `

- [x] [AGENT] P0. Transfermarkt join specifically: - Read lineup parquet if available, else squad parquet. - For each
      player, `asof_lookup(values_for_player, as_of=kickoff_date)`. - Aggregate per team: sum-of-values, count with
      known value, `team_value_coverage_pct = known / total_lineup_size`.

- [x] [AGENT] P0. SFI join specifically: - Read `SFI_STANDINGS` for `kickoff_date - 1 day`, fall back to most recent
      prior date if absent (but only if within 7 days). - Extract `position`, `points` for home_team_id and
      away_team_id. - If team not in standings (promoted / relegated mid-season), `NULL`.

- [x] [AGENT] P0. Weather join specifically: - Resolve `venue_id` to `(lat, lon)` via UAC `sports.venues` lookup
      (confirm helper exists in Phase 0; add if missing). - Find hourly bucket for `kickoff_utc.floor(hour)`. - Populate
      the weather columns.

- [x] [AGENT] P0. Write output parquet to features-sports-service's output bucket. Manifest row via `ManifestWriter`
      with shard columns: `date`, `league_id`, `data_type="FIXTURE_FEATURES"`.

- [x] [AGENT] P0. Unit tests with synthetic fixtures + synthetic Transfermarkt / SFI / weather inputs proving: - As-of
      invariant held (future values never leak). - Hourly weather bucket is the correct one. - NULL propagation on
      missing inputs. - Coverage percentage math.

### Phase 3: Orchestrator CLI integration [SEQUENTIAL, depends on Phase 2]

- [x] [AGENT] P0. Add a `--operation fixture-features` (or extend existing) on the features-sports-service CLI. Must
      accept `--start-date`, `--end-date`, `--asset-group SPORTS`, `--league-id L` (optional filter).

- [x] [AGENT] P0. Batch runner iterates dates, calls `compute_fixture_features` per date, writes outputs.

- [x] [AGENT] P0. Integration test: end-to-end for one date (can use GCS emulator) with three fixtures, confirm output
      parquet has three rows with populated join columns.

### Phase 4: Manifest + data-status integration [PARALLEL with Phase 3]

- [x] [AGENT] P1. Update `deployment-api` aggregator if `FIXTURE_FEATURES` isn't already a known data_type. Ensure it
      appears in the data-status drilldown with its own completion percentage.

- [x] [AGENT] P2. Document in `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §9 — update the
      denormalisation diagram to point at the shipped pipeline (not just the intent).

### Phase 5: Backfill smoke + quality gates [SEQUENTIAL]

- [x] [AGENT] P0. Dry-run on 2024-09-01 (known EPL Matchday 3 date with all four data sources present on GCS).
      Spot-check one fixture's output (home_team_value / standings / weather populate correctly, no lookahead).

- [x] [AGENT] P0. `bash unified-api-contracts/scripts/quality-gates.sh` green.

- [x] [AGENT] P0. `bash features-sports-service/scripts/quality-gates.sh` green.

- [x] [AGENT] P0. Commit + quickmerge each repo (`--agent`). Order: UAC first (dep), then features-sports-service.

## Dependency graph

```
Phase 0 (pre-audit) ─► Phase 1 (UAC schema + asof helper) ─► Phase 2 (join pipeline)
                                                                    │
                                                                    ├─► Phase 3 (CLI integration)
                                                                    │        │
                                                                    └─► Phase 4 (manifest + codex) ─► Phase 5 (smoke + QG)
```

## SSOT cross-refs

- Join contract: `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §§1, 2 (per-provider shard keys),
  §9 (denormalisation diagram).
- Manifest v5: `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`.
- Chunk-safe writes (if backfill is multi-year): `unified-trading-pm/codex/02-data/chunk-safe-manifest-migrations.md`.

## Out of scope

- **Raw data backfill** — this plan assumes the raw parquets exist for target dates. If they don't (e.g. 2018
  pre-deployment), run `launch-api-football-backfill-vm.sh` first or wait for the historical backfill that's currently
  in flight (VM `af-backfill-20260421-113002`).
- **Live feature streaming** — this plan is batch. Real-time pre-match feature updates (Tier-3 T-1h) can reuse the same
  pipeline but are dispatched by the scheduler (see `sports_scheduler_periodic_tier_dispatch_2026_04_21`).
- **ML model retraining** — out of scope; ml-training-service consumes the new features but retraining cadence isn't
  owned here.
- **Per-player features** (player xG, player value trajectory) — this plan produces per-fixture features. Per-player
  features can layer on later using the same join machinery.
