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

Each venue in the 31-member canonical set carries an `executable` flag derived from
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

### 3. `odds_movement` — MDPS OHLC candle

| Field               | Value                                                                                                                                                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Producer**        | MDPS `SportsOddsMovementAdapter` (`odds_movement_adapter.py`, derived from raw `odds`/`trades` ticks)                                                                                                                           |
| **Shard key**       | `venue` × `league_id` × `day`                                                                                                                                                                                                   |
| **Instrument type** | `odds`                                                                                                                                                                                                                          |
| **NEEDS_CANDLE**    | True                                                                                                                                                                                                                            |
| **Schema fields**   | `timestamp`, `timestamp_out`, `venue`, `symbol`, `instrument_id`, `open`, `high`, `low`, `close`, `volume` (always 0), `trade_count` (tick count in the interval) — genuine OHLC of `home_odds`, one row per timeframe interval |
| **Upstream guard**  | Same `DependencyChecker` staleness gate as `odds_snapshot`                                                                                                                                                                      |
| **Status**          | Production (16,470 captured shards since 2026-07-25)                                                                                                                                                                            |

**Corrected 2026-08-08** (P1 discriminator todo): the schema fields above were previously mis-documented as
`price_prev`/`price_curr`/`delta`/`delta_pct` (a two-point delta shape) — verified against the live adapter code
(`market-data-processing-service/.../adapters/sports/odds_movement_adapter.py`), the actual output is a genuine OHLC
candle: `grouped["home_odds"].agg(["first", "max", "min", "last"])` → `open`/`high`/`low`/`close`, with `trade_count` =
the tick count observed in that interval. This is computationally the same SHAPE as any other fleet OHLCV candle (e.g.
`odds_ohlcv_{tf}`, `ohlcv_{tf}`) — it is the candle-of-`home_odds` form, not a delta/movement metric between two prior
points. See § "Snapshot vs Candle Discriminator" below for how this reconciles with the collapsed `odds` raw model.

---

## Snapshot vs Candle Discriminator (P1 decision, 2026-08-08)

> Resolves `/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`'s "Decide and record the
> snapshot-vs-candle discriminator on the collapsed model" todo. `odds_snapshot` and `odds_movement` are two DIFFERENT
> computations over the same raw `odds` ticks at the same grain, so `timeframe` alone cannot distinguish them once the
> raw `odds_snapshot`/`odds_movement` `data_type` names are retired from the RAW MTDS vocabulary (done in the prior P0
> todo — raw vocabulary is now `odds` + `timeframe`/`horizon`/`in_play` only).

**Verified against the real adapter code** (`market-data-processing-service/app/adapters/sports/`):

- **`odds_movement`** (`SportsOddsMovementAdapter`) computes a genuine OHLC aggregation — `open`/`high`/`low`/`close` =
  first/max/min/last of `home_odds` within the interval, `trade_count` = observed-tick count. This **is** the
  fleet-standard "OHLC form" the plan's pre-specified ruling describes as "the candle (`odds` + `timeframe`)" — it is
  architecturally identical in kind to `odds_ohlcv_{tf}` (open/high/low/close/volume/trade_count), just computed from
  the sports-specific `home_odds` field via the sports MDPS adapter rather than the generic candle builder.
- **`odds_snapshot`** (`SportsOddsSnapshotAdapter`) computes LOCF — `open`=`high`=`low`=`close` = the single last
  observed `home_odds` value in the interval (a degenerate/flat candle), `trade_count`=0. This is the point-in-time
  "value as of T" form, semantically distinct from price-action-within-interval even though it shares the same
  `CandleOutput` container shape.

**Discriminator ruling**: both forms remain **MDPS-internal processed-output keys**, minted via
`canonical_writer_shaping.mdps_data_type_key(source_data_type, timeframe)` using the sports `CandleAdapterRegistry`
product name (`"odds_snapshot"` / `"odds_movement"`) as `source_data_type` — **confirmed against the function's real
implementation**: neither name is an entry in `_DATA_TYPE_TO_MDPS_PREFIX` (MDPS) / `_RAW_TO_PROCESSED_PREFIX` (UAC
`processed_data_dependencies.py`), so both fall through `mdps_data_type_key`'s deterministic generic-fallback branch
(`f"{source_data_type}_{tf}"`), producing `odds_snapshot_{tf}` / `odds_movement_{tf}` — already registered as real
per-timeframe contracts in UAC `_candle_contracts.py`'s sports-derived-candle loop and matched by
`_SPORTS_ODDS_DERIVED_CANDLE_PREFIXES` for contract lookup. **This is deliberately NOT routed through
`_RAW_TO_PROCESSED_PREFIX`/`_DATA_TYPE_TO_MDPS_PREFIX`**: those two tables are raw-MTDS-`data_type`-scoped SSOTs
(consumed by `MDPS_DERIVABLE_DATA_TYPES` and `PROCESSED_REQUIRES_RAW` for raw-vs-blocked-on-raw honest-coverage
classification — verified via `processed_data_dependencies.py`'s own docstring + consumers) — `odds_snapshot`/
`odds_movement` are NOT raw MTDS capture types (that raw vocabulary is `odds` alone, per the P0 collapse), so adding
them there would misclassify them as raw sources and would collide `odds_movement_{tf}`'s key with the unrelated base
`odds_ohlcv_{tf}` candle if a prefix entry pointed both at the same `"odds_ohlcv"` prefix.

**Net**: no functional key-minting code change is required — the existing fallback mechanism already discriminates the
two forms correctly and deterministically. What was missing (this todo's actual deliverable) is this recorded decision
plus explicit source comments (see `canonical_writer_shaping.py` and `processed_data_dependencies.py`) marking the
omission of `odds_snapshot`/`odds_movement` from the raw-prefix tables as deliberate, so a future edit doesn't "fix" it
as an oversight and collide the movement candle's key with the base `odds` candle.

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

### ML label lineage — the full path, verified against live code (2026-08-09)

`markets`/`outcomes`/`settlements` were phantom sports MTDS `data_type` declarations (0 rows ever written — see Retired
Data Types above); they were never the source of match-outcome ML labels. The real lineage — traced end-to-end through
the actual reader/writer code, not asserted — is:

1. **instruments-service writes the outcome** (`instruments_service/engine/orchestrator/sports_fixtures.py`,
   `_write_fixtures_per_league`): for each completed fixture (`home_score_regulation` populated — regulation always
   finishes even in ET/PEN games) it writes the Q6 outcome columns (`_Q6_OUTCOME_COLUMNS` in
   `instruments_service/engine/orchestrator/__init__.py`: `home_score_regulation`, `away_score_regulation`,
   `home_score_after_extra_time`, `away_score_after_extra_time`, `home_score_after_penalty_shootout`,
   `away_score_after_penalty_shootout`, `home_penalty_shootout_score`, `away_penalty_shootout_score`,
   `went_to_extra_time`, `went_to_penalties`, `match_result`) to
   `sports_reference/by_date/day={date}/entity=fixtures_outcomes/league={league}/fixtures_outcomes.parquet`, keyed on
   `af_fixture_id`. The companion `entity=fixtures_schedule` write carries everything else (kickoff time, teams, league)
   for ALL fixtures (not just completed ones) — the schedule/outcomes split
   (`sports_fixtures_schema_split_completion_2026_06_20.md`) has no legacy dual-write. FootyStats' `MATCHES` entity
   (`instruments_service/engine/orchestrator/footystats.py`, GCS `entity=footystats_matches`) is a SEPARATE, secondary
   provider's match-result feed — same purpose (outcome ground truth), different provider, used for cross-provider
   enrichment rather than as the primary label source. This is the "matches" half of "IS `fixtures_outcomes`/`matches`".
2. **features-service reads + joins the split** (`features_service/sports/data/gcs_reader.py::read_fixtures_joined` /
   `_read_split_fixtures_fallback`, delegating to UTL's `read_fixtures_joined(date, league_id=None)`): reads both
   `entity=fixtures_schedule` and `entity=fixtures_outcomes` per league and joins them on `af_fixture_id`.
3. **features-service normalizes the raw provider columns**
   (`features_service/sports/data/gcs_normalizers.py::_FIXTURE_COL_MAP`): renames the raw score columns to the canonical
   `home_goals`/`away_goals` (+ `ht_home_goals`/`ht_away_goals`, `ft_home_goals`/`ft_away_goals`). FootyStats' `matches`
   rows go through the separate `_normalize_footystats_matches` normalizer to the same canonical column names. **Bug
   found + fixed here (2026-08-09)**: `_FIXTURE_COL_MAP` only knew the LEGACY singleton `entity=fixtures` column names
   (`home_score`/`away_score`, from before the 2026-07-14 schedule/outcomes split cutover). UTL's
   `read_fixtures_joined()` — the reader `read_fixtures_joined`/`_read_split_fixtures_fallback` above delegates to —
   returns the CURRENT Q6 names (`home_score_regulation`/`away_score_regulation`) for every date on/after the cutover,
   and its own source comment states the legacy bare names "are retired and no longer written". Since `_FIXTURE_COL_MAP`
   never mapped the Q6 names, `home_goals`/`away_goals` were silently ABSENT (not merely NaN — the column didn't exist)
   from the normalized frame for every post-cutover fixture, which propagated through the exporter (step 4) and into
   ml-service's `sports_target_generator.py` (step 5) as `_safe_col`'s "Missing column, filling with nan" path — i.e.
   XG/win-draw-loss/meta ML labels were silently all-NaN for current data. Fixed by adding
   `home_score_regulation`/`away_score_regulation` → `home_goals`/`away_goals` to `_FIXTURE_COL_MAP`
   (`_rename_coalescing_collisions` already merges both eras' names when a lookback window straddles the cutover — no
   additional handling needed). Halftime scores (`ht_home_goals`/`ht_away_goals`) are NOT in `_Q6_OUTCOME_COLUMNS` at
   all (Q6 only carries regulation/ET/penalty scores + `match_result`) — whether halftime labels have an equivalent
   post-cutover gap is unverified and out of scope of this fix; flagging for a follow-up if halftime-target training is
   exercised against current dates.
4. **features-service exports `home_goals`/`away_goals` into the fixture-level feature output**
   (`features_service/sports/exporters/derived_features_helpers.py`, e.g. the `home_win`/clean-sheet/venue-context
   calculators keying directly off `completed_keyed["home_goals"]`/`["away_goals"]`) — these columns pass through into
   the `derived_features`/`fixture_features` parquet that ml-service reads.
5. **ml-service reads the exported features** (`ml_service/training/app/core/sports_feature_loader.py`, fixture-based
   GCS layout — one row per fixture, joined on `fixture_id` across feature groups) and **ml-service builds labels from
   them** (`ml_service/training/app/core/sports_target_generator.py`: `COL_HOME_GOALS = "home_goals"`,
   `COL_AWAY_GOALS = "away_goals"`, `COL_HT_HOME_GOALS = "ht_home_goals"`, `COL_HT_AWAY_GOALS = "ht_away_goals"` —
   consumed by the XG/win-draw-loss/halftime/meta target generators).

**Net**: retiring `markets`/`outcomes`/`settlements` required no lineage change — those three types were never wired
into this path (0 rows, phantom declarations); the ML label lineage was always meant to run through IS
`fixtures_outcomes`/`matches`. What step 3 found is a SEPARATE, real bug on that same path (the normalizer lagging
behind the 2026-07-14 schedule/outcomes entity split, fixed in the same session this section was written) — labels were
silently broken for current data for a different reason than "retired types," which is exactly the kind of thing a
reader chasing "why is there no settlements data_type" needs to know is NOT the actual gap. This section exists so a
future reader who greps for `settlements` and finds nothing does not conclude labels are missing (they weren't, once
fixed) or re-open the wrong question.

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
- `get_expected_bookmakers()` — returns the 31 canonical venues with per-venue start dates; authoritative denominator
  for expected-shard counts. Never hardcode venue lists inline.

---

## Venue Axis (31 canonical members, verified live 2026-08-09)

All 31 venues are in `VENUES_BY_ASSET_GROUP["sports"]` (landed `unified-api-contracts@05a709fd`; this list re-verified
2026-08-09 via direct import against `market_data_categories.VENUES_BY_ASSET_GROUP['sports']` — corrects a prior "32
canonical members" version of this section that had drifted: several named venues (`BETFAIR_EX_AU`, `WILLIAM_HILL`,
`BWIN`, `BET365`, `CAESARS`, `POINTSBET_US`, `MYBOOKIEAG`, `LOWVIG`, `WYNNBET`, `FOXBET`, `MARATHONBET`, `1XBET`,
`SUPABETS`, plus the open-ended "and additional regional books" tail) were never actually registered, while several real
members (`BETFAIR_SB_UK`, `WILLIAMHILL` — no underscore, `BETOPENLY`, `BETRIVERS`, `BETVICTOR`, `CASUMO`, `LADBROKES`,
`LIVESCOREBET`, `NOVIG`, `ONEXBET`, `PADDYPOWER`, `PROPHETX`, `SKYBET`, `VIRGINBET`, bare `UNIBET`) went unnamed). Every
venue resolves all 5 classification dicts: `SportsVenueType`, auth method, instrument-type set, fee model, alpha
profile. `executable=False` for all 31 as of 2026-08-09 — no venue has a complete adapter yet (per the `executable`
predicate above).

**Exchange venues** (`SportsVenueType.EXCHANGE_API`): `BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `SMARKETS`, `MATCHBOOK`

**Prediction-market-style venues** (`SportsVenueType.PREDICTION_MARKET_API`): `BETOPENLY`, `NOVIG`, `PROPHETX`

**Bookmaker-API venues** (`SportsVenueType.BOOKMAKER_API`): `PINNACLE`, `ONEXBET`

**Web-scraper sportsbooks** (`SportsVenueType.WEB_SCRAPER`): `BET888SPORT`, `BETFAIR_SB_UK`, `BETMGM`, `BETONLINEAG`,
`BETRIVERS`, `BETSSON`, `BETVICTOR`, `BETWAY`, `BOVADA`, `CASUMO`, `CORAL`, `DRAFTKINGS`, `FANDUEL`, `LADBROKES`,
`LIVESCOREBET`, `PADDYPOWER`, `SKYBET`, `UNIBET`, `UNIBET_EU`, `UNIBET_UK`, `VIRGINBET`, `WILLIAMHILL`

`BETFAIR` (bare) is the operator-group parent — NOT a data-axis venue.

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
