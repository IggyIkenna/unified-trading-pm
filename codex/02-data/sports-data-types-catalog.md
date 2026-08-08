---
doc_type: codex-ssot
title: Sports Data Types Catalog
summary: >-
  Catalog of MTDS/MDPS sports data types under the 2026-08-08 operator taxonomy (P1 rewrite). Raw vocabulary unifies to
  lowercase `odds` with `in_play` and `horizon` as columns; derived types are `odds_snapshot` and `odds_movement`;
  `arbitrage_opportunity` moves to signals layer; `markets`/`outcomes`/`settlements` retired (0 rows ever written). GCS
  path uses `venue=` (not `source=`) with `pipeline_mode=` and `instrument_type=` segments. Contracts landed in P1;
  physical data migration in P2.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, market-tick-data-service, market-data-processing-service, instruments-service]
scope: [engineer, admin]
tags: [sports, mtds, mdps, odds, data-status, catalogue, taxonomy-2026-08-08]
related:
  [
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/02-data/sports-fixtures-lifecycle.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
  ]
created: 2026-05-24
last_revised: 2026-08-08
authoritative_for: [MTDS/MDPS sports data_type catalog, sports bookmaker/venue coverage]
referenced_by:
  [/codex/01-domain/sports-instruments.md, /codex/02-data/README.md, /codex/02-data/sports-fixtures-lifecycle.md]
owner:
last_reviewed: 2026-08-08
code_refs:
---

# Sports Data Types Catalog

> **Rewritten 2026-08-08 (P1, `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`).** This doc supersedes all
> pre-2026-08-08 content. Three sections of the prior version were wrong:
>
> 1. **"do NOT merge" is OVERTURNED.** The old § "Disambiguation with instruments-service ODDS" ruled that IS
>    `data_type=ODDS` and the MTDS types "legitimately coexist; do NOT merge". The operator ruled 2026-08-08 that the
>    sports data_type vocabulary **merges to ONE lowercase form** — footystats `ODDS`/`odds` folds into `odds`, and the
>    19-token IS uppercase vocabulary (`FIXTURES`, `MATCHES`, `PLAYER_STATS`, …) lowercases with it. The `source` column
>    becomes the discriminator.
> 2. **GCS path was wrong.** The old doc showed `asset_group=sports/source={BOOKMAKER}/data_type=…`. Production actually
>    writes
>    `.../pipeline_mode={mode}/asset_group=sports/venue={BOOKMAKER}/instrument_type={it}/data_type={dt}/league_id={LEAGUE}/`
>    — the bookmaker segment is `venue=` (not `source=`), and `pipeline_mode=` and `instrument_type=` were undocumented.
>    `source=` is a COLUMN inside the parquet, not a path segment.
> 3. **Data-type list was incomplete and partly phantom.** The old doc listed 8 types, never documented `trades`
>    (375,257 captured shards — the largest population in the estate) or `trades_inplay`, and listed
>    `markets`/`outcomes`/`settlements` as "Production" when all three have **0 rows ever written**.
>
> Governing plans: `/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md` (contracts) and
> `/plans/active/sports_taxonomy_p2_migration_2026_08_08.md` (physical migration). **This rewrite documents the decided
> TARGET model. Physical GCS and manifest migration happens in P2.**

> SSOT for all MTDS/MDPS Sports data type definitions, sources, shard keys, and GCS path convention. Last updated:
> 2026-08-08.

---

## Model Overview (2026-08-08 ruling)

Every sports price quote — pre-match or in-play, from any bookmaker or aggregator — lands under a SINGLE raw data type
**`odds`**. Two concepts previously overloaded into `data_type` or `timeframe` names become real schema columns:

- **`in_play: bool`** — `True` for quotes captured while the match is live; `False` for pre-match. Replaces the retired
  `trades_inplay` data type.
- **`horizon: str | None`** — first-class time-to-kickoff label (`T-24h`, `T-12h`, `T-6h`, `T-4h`, `T-2h`, `T-1h`,
  `T-10m`, `T-0`) for horizon-bucketed rows; `None` for tick-level or non-bucketed rows. Replaces the retired
  `odds_horizon_bucket` data type. UAC SSOT: `SPORTS_HORIZONS` constant (landed `unified-api-contracts@685b288a`);
  validated via `is_valid_horizon()`.

The **`source`** column (`odds_api` / `footystats`) distinguishes the two raw-odds producers. `ODDS_API` and
`FOOTYSTATS` are sources only — they do NOT appear on the `venue` axis. The `venue` column carries the bookmaker whose
price is quoted.

### Aggregator vs venue

`ODDS_API` is a redistribution aggregator that fans prices from 27+ bookmakers into individual venue rows. The manifest
`source=odds_api` identifies aggregator-sourced rows; `venue` carries the bookmaker (e.g. `BETFAIR_EX_UK`, `PINNACLE`,
`FANDUEL`). `FOOTYSTATS` is a stats vendor supplying pre-match snapshots (`source=footystats`). Neither appears in
`VENUES_BY_ASSET_GROUP["sports"]` (landed `unified-api-contracts@05a709fd`).

### `executable` predicate

Each venue in the 32-member canonical set carries an `executable` flag derived from
`venue_adapter_keys.is_venue_executable()`: `True` only when a real adapter key exists (not `__no_adapter_yet__`). As of
2026-08-08 no exchange-type venue has a complete adapter (`BLOCKED-CREDENTIALS` for Betfair Exchange). All ODDS_API
aggregator-fanned venues are `executable=False` — we receive via aggregator, not direct.

### `BETFAIR` as operator-group parent

`BETFAIR` (bare, without region suffix) is the operator-group parent, not a data-axis venue. It does not appear in
`VENUES_BY_ASSET_GROUP["sports"]`. The three exchange venues (`BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `BETFAIR_EX_AU`) roll up
to it in the venue→operator hierarchy. **P1 todo still in flight** — see
`/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`.

---

## Data Type Catalog (target model)

All types use `instrument_type=odds`. All data type names are **lowercase** — sports no longer has an UPPER-case
exception.

### 1. `odds` — unified raw quotes

| Field               | Value                                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Producers**       | MTDS `OddsApiAdapter` (`source=odds_api`), MTDS footystats adapter (`source=footystats`)                                 |
| **Shard key**       | `venue` × `league_id` × `day`                                                                                            |
| **Instrument type** | `odds`                                                                                                                   |
| **Schema fields**   | `fixture_id`, `league_id`, `venue`, `market_type`, `outcome`, `odds_decimal`, `in_play`, `horizon`, `source`, `ts_event` |
| **UAC contract**    | `CONTRACT_REGISTRY[("sports", "odds", "odds")]` = `SPORTS_ODDS_TRADES` (P2 rename pending)                               |
| **Status**          | CONTRACT LANDED (P1); physical data migration in P2                                                                      |

One row per (fixture, market, outcome, venue, timestamp). `in_play=True` rows were formerly `data_type=trades_inplay`
(retired). `horizon` is populated only for horizon-bucketed captures (formerly `odds_horizon_bucket`).

**Prior names merged into `odds` (physical migration in P2):**

| Old data_type         | Captured shards | What it actually was                                          |
| --------------------- | --------------- | ------------------------------------------------------------- |
| `trades`              | 375,257         | Bookmaker quotes via ODDS_API; misleading name (no execution) |
| `odds`                | 16,207          | Footystats pre-match snapshots; distinguished by `source` col |
| `ODDS`                | 6,306           | Same footystats population, uppercase manifest artefact       |
| `trades_inplay`       | 111             | In-play quotes; 2022 fossil with blank venue                  |
| `odds_horizon_bucket` | 135,980         | Time-to-kickoff buckets; folds into `odds` with `horizon` col |

---

### 2. `odds_snapshot` — MDPS periodic resample

| Field               | Value                                                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Producer**        | MDPS `odds_snapshot_adapter` (derived from `odds`)                                                              |
| **Shard key**       | `venue` × `league_id` × `day`                                                                                   |
| **Instrument type** | `odds`                                                                                                          |
| **NEEDS_CANDLE**    | True                                                                                                            |
| **Schema fields**   | `fixture_id`, `league_id`, `venue`, `market_type`, `outcome`, `odds_decimal`, `ts_snapshot`, `interval_minutes` |
| **Upstream guard**  | `DependencyChecker.check_sports_raw_source_captured` blocks if raw `odds` source is absent/stale                |
| **Status**          | Production (16,521 captured shards since 2026-07-25)                                                            |

LOCF resample of raw `odds` ticks at fixed intervals (default 15m). One row per (fixture, market, outcome, venue,
snapshot-time). The MDPS staleness guard (landed `market-data-processing-service@41cdb702d`) blocks derivation when the
raw `odds` source shard is absent or stale — prevents the 2026-07 incident where 12 days of derived data were produced
from a dead feed.

**Cluster validation MANDATORY**: `cluster_extractor=venue` — all venue shards for a fixture must be captured before
MDPS snapshot runs. A partial venue set corrupts downstream cross-bookmaker comparisons.

---

### 3. `odds_movement` — MDPS OHLC delta

| Field               | Value                                                                                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Producer**        | MDPS `odds_movement_adapter` (derived from `odds_snapshot`)                                                                   |
| **Shard key**       | `venue` × `league_id` × `day`                                                                                                 |
| **Instrument type** | `odds`                                                                                                                        |
| **NEEDS_CANDLE**    | True                                                                                                                          |
| **Schema fields**   | `fixture_id`, `league_id`, `venue`, `market_type`, `outcome`, `price_prev`, `price_curr`, `delta`, `delta_pct`, `ts_snapshot` |
| **Upstream guard**  | Same `DependencyChecker` staleness gate as `odds_snapshot`                                                                    |
| **Status**          | Production (16,470 captured shards since 2026-07-25)                                                                          |

OHLC delta of odds from the prior snapshot interval. `delta` = absolute change; `delta_pct` = percentage change. Primary
steam-move and closing-line signals for features-service. Requires `odds_snapshot` as upstream.

---

## Retired Data Types

| data_type               | Final shards | Retirement reason                                                       | Migration |
| ----------------------- | ------------ | ----------------------------------------------------------------------- | --------- |
| `trades`                | 375,257      | Merged into `odds` (misleading name — no execution)                     | P2        |
| `trades_inplay`         | 111          | Merged into `odds` with `in_play=True` (2022 fossil, blank venue)       | P2        |
| `odds_horizon_bucket`   | 135,980      | Folded into `odds` with `horizon` column                                | P2        |
| `ODDS`                  | 6,306        | Uppercase manifest phantom — merges into lowercase `odds`               | P2        |
| `arbitrage_opportunity` | 16,441       | Moved to signals/features layer (P3); was strategy output in data layer | P3        |
| `markets`               | 0            | Never written; ML labels come from IS `fixtures_outcomes`/`matches`     | N/A       |
| `outcomes`              | 0            | Never written; ML labels come from IS `fixtures_outcomes`/`matches`     | N/A       |
| `settlements`           | 0            | Never written; ML labels come from IS `fixtures_outcomes`/`matches`     | N/A       |

Manifest rows for retired types and physical GCS objects are cleaned up in P2.

---

## IS Reference Data (not MTDS/MDPS)

The following types live in the **instruments-service** manifest (not the MTDS tick manifest) and will lowercase in P1
alongside the vocabulary merge:

`FIXTURES` → `fixtures`, `MATCHES` → `matches`, `PLAYER_STATS` → `player_stats`, `INJURIES` → `injuries`, `STANDINGS` →
`standings`, `TEAMS` → `teams`, `XG` → `xg`, `FIXTURES_OUTCOMES` → `fixtures_outcomes`, `PLAYERS` → `players`, `COACHES`
→ `coaches`, and ~9 further IS entity types.

These are structurally separate from MTDS odds data — IS bucket, not MTDS tick bucket. ML labels (match outcomes,
fixture results) come from IS `fixtures_outcomes`/`matches`, not from the retired `markets`/`outcomes`/`settlements`
types above. **Do NOT mix IS entity types with the MTDS data type catalog.**

---

## GCS Path Convention

### Current production path (pre-P2 migration)

```
{market-data-tick-sports-bucket}/raw_tick_data/by_date/day={date}/pipeline_mode={mode}/asset_group=sports/
  venue={BOOKMAKER}/instrument_type={it}/data_type={dt}/league_id={LEAGUE}/ticks.parquet
```

Axis order (verified against live prod 2026-08-08): `pipeline_mode` → `asset_group` → `venue` → `instrument_type` →
`data_type` → `league_id`

**Key correction**: `venue={BOOKMAKER}` is the segment name — never `source=`. The `source` column (`odds_api`,
`footystats`) lives INSIDE the parquet, not in the GCS path. Current prod objects use `data_type=trades` and
`data_type=odds_horizon_bucket` (old names); P2 migrates them to `data_type=odds`.

### Bucket resolution

```python
unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(
    cloud=..., kind="market-data-tick", asset_group="sports", env=...
)
```

Never inline `gs://...` strings — QG STEP 5.69 enforces. See `/codex/02-data/bucket-naming-and-config.md`.

### Path resolver

`unified_api_contracts.sports.candidate_parquet_paths()` in
`unified_api_contracts/canonical/domain/sports/gcs_paths.py`. Key helpers:

- `clip_dates_to_source_coverage()` — clamps date range to per-venue availability window.
- `is_in_known_gap()` — True for known data-dark periods (API outages, subscription gaps).
- `get_expected_bookmakers()` — returns the 32 canonical venues with per-venue start dates; authoritative denominator
  for expected-shard counts. Never hardcode venue lists inline.

---

## Venue Axis (32 canonical members as of P1)

All 32 venues are in `VENUES_BY_ASSET_GROUP["sports"]` (landed `unified-api-contracts@05a709fd`). Every venue resolves
all 5 classification dicts: `SportsVenueType`, auth method, instrument-type set, fee model, alpha profile.

**Exchange venues** (`SportsVenueType.EXCHANGE`, `executable=False` pending credentials — per the `executable` predicate
above, no exchange-type venue has a complete adapter as of 2026-08-08): `BETFAIR_EX_UK`, `BETFAIR_EX_EU`,
`BETFAIR_EX_AU`, `SMARKETS`, `MATCHBOOK`

**Fixed-odds sportsbooks** (`executable=False` unless direct adapter exists): `PINNACLE`, `BET365`, `BETWAY`,
`WILLIAM_HILL`, `BWIN`, `UNIBET_EU`, `UNIBET_UK`, `CORAL`, `FANDUEL`, `DRAFTKINGS`, `BETMGM`, `CAESARS`, `POINTSBET_US`,
`BETONLINEAG`, `BOVADA`, `MYBOOKIEAG`, `LOWVIG`, `WYNNBET`, `FOXBET`, `MARATHONBET`, `BETSSON`, `1XBET`, `BET888SPORT`,
`SUPABETS`, and additional regional books.

`BETFAIR` (bare) is the operator-group parent — NOT a data-axis venue (P1 todo still in flight).

### `exchange_odds` / `fixed_odds` instrument_type retirement

The `exchange_odds`/`fixed_odds` `instrument_type` split is being retired in P1 (todo in flight). Exchange vs fixed-odds
is a property of the venue (encoded in `SportsVenueType`), not the instrument type. Derive at read time from the venue.
All sports rows use `instrument_type=odds`.

---

## Shard Atom

**Canonical shard atom**: `asset_group` / `venue` / `instrument_type` / `data_type` / `league_id` / `day`. Identical
across writer, manifest, status gate, and UI.

`fixture_id` is a ROW-LEVEL column inside the parquet — NOT a shard axis. All fixtures for a `(league_id, day)` pair
land in one shard file.

---

## Manifest Status Rules

| data_type       | `attempted_failed`         | `empty_confirmed`                        | `expected_unattempted`            |
| --------------- | -------------------------- | ---------------------------------------- | --------------------------------- |
| `odds`          | Venue API error or timeout | Venue does not cover this league/fixture | Pre-source-coverage-start date    |
| `odds_snapshot` | MDPS processing error      | Fewer than 2 intervals available         | No upstream `odds` shard captured |
| `odds_movement` | MDPS processing error      | Fewer than 2 snapshot intervals          | No upstream `odds` shard captured |

`attempted_failed` = data MAY exist but was unretrievable. `empty_confirmed` = genuinely no data (correct reason enum
required). Key reason enums: `EXPECTED_PRE_SOURCE_COVERAGE_START` (before per-venue start date),
`EXPECTED_FIXTURE_CANCELLED`, `EXPECTED_FIXTURE_POSTPONED`.

**Open follow-up**: no `EmptyConfirmedReason` member exists for horizon windows missed because a match started early
(`EXPECTED_FIXTURE_STARTED_EARLY` does NOT exist in UAC as of 2026-08-08). Do not cite it as a shipped reason until the
member is minted.

---

## MDPS Dependency + Upstream Guard

`DependencyChecker.check_sports_raw_source_captured` (landed `market-data-processing-service@41cdb702d`):

- Reads MTDS manifest for the SPORTS bucket
- Checks `capture_status=captured` for `data_type in {trades, odds}` (both old and new name during P2 migration)
- Blocks `odds_snapshot`/`odds_movement`/`odds_horizon_bucket` when no captured upstream row found
- Emits `DP_DOWNSTREAM_BEFORE_UPSTREAM` alert via UAC `DATA_PIPELINE_ALERT_RULES`
- Fails-open on manifest read errors (does not block if manifest is unreachable)

---

## Cluster Validation (MANDATORY for bundled types)

| data_type       | `cluster_extractor` | Reason                                                     |
| --------------- | ------------------- | ---------------------------------------------------------- |
| `odds_snapshot` | `venue`             | Consistent venue set required for cross-bookmaker analysis |
| `odds_movement` | `venue`             | Derived from `odds_snapshot` with same cluster requirement |

UTL `record_captured()` asserts `cluster_extractor` and `cluster_keys` kwargs present for bundled types. Missing →
`MissingClusterValidationError`. QG STEP 5.64 statically checks handler source files.

`arbitrage_opportunity` previously had `cluster_extractor=bookmaker` — retired from the data layer; moves to
signals/features in P3.

---

## Implementation Notes

### Shard-level failure isolation

All MTDS sports odds handlers follow shard-level isolation: exceptions caught per-venue/per-league loop, recorded via
`record_failed(error=classify_venue_error(exc))`, loop continues. No `raise` inside per-shard loops. SSOT:
`/codex/04-architecture/shard-level-failure-isolation.md`.

### API key requirements

| handler                   | Secret Manager key | Notes                                              |
| ------------------------- | ------------------ | -------------------------------------------------- |
| sports_odds_handler       | `odds-api-key`     | Gates ~90% of venue coverage (27 fanned-out books) |
| Betfair Exchange (future) | `betfair-api-key`  | `BLOCKED-CREDENTIALS` — scaffold only as of P1     |

### 2020-06 Data Floor

All sports capture is gated to 2020-06-06 or later. Pre-floor dates emit `empty_confirmed` with
`EXPECTED_PRE_SOURCE_COVERAGE_START`. Denominators, launchers, and gates clamp to this floor. SSOT:
`/codex/02-data/sports-2020-06-data-floor.md`.

### Consumer inventory for pending renames (P2 migration)

Per `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`, every rename must enumerate and migrate all
consumers in the same change. Consumers for the `trades → odds` rename (P2 scope):

- UAC `market_data_categories.py` (`DATA_TYPES_BY_ASSET_GROUP`, `FREQUENCY_MAP`, `CONTRACT_REGISTRY`,
  `_is_consumable_trades_blob` — matches FILENAME not `data_type` column; grep misses it)
- MTDS `odds_api_adapter.py` (writer)
- MDPS `canonical_writer.py` + `_process_one_category`
- IS `enumerate_expected_universe.py`
- features-service `gcs_reader.py` (`_ODDS_BUCKETED_PREFIXES` — binds by GCS PATH PREFIX, not `data_type` column; a
  data_type rename grep WILL MISS IT; must update the prefix string explicitly)
- ml-service `sports_feature_loader._ODDS_BUCKETED_PREFIXES` (same pattern as features-service)
- deployment-api `_distinct_values.py` (honest-coverage rollup)

---

## Related Documents

- `/codex/02-data/sports-gcs-path-ssot.md` — canonical GCS path resolver for all sports parquets
- `/codex/02-data/sports-data-source-coverage-matrix.md` — expected league counts, coverage axes
- `/codex/02-data/sports-scheduling-and-sharding.md` — scheduling cadence, shard-atom definition
- `/codex/02-data/sports-fixtures-lifecycle.md` — fixture state transitions and honest-absence semantics
- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — HARD RULE governing every rename in P2
- `/codex/02-data/sports-2020-06-data-floor.md` — data floor governing all sports captures
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest v9 honest-coverage schema
- `/codex/04-architecture/shard-level-failure-isolation.md` — per-shard error handling invariant
- `/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md` — contracts phase (this rewrite's plan)
- `/plans/active/sports_taxonomy_p2_migration_2026_08_08.md` — physical migration of GCS objects + manifest rows
