---
doc_type: codex-ssot
title: Sports Data Types Catalog
summary:
  Catalog of the 9 MTDS/MDPS sports data types (trades, odds, odds_snapshot, odds_movement, arbitrage_opportunity,
  odds_horizon_bucket, markets, outcomes, settlements) — sources, shard keys, NEEDS_CANDLE, and bookmaker coverage.
  lower-case `data_type` is canonical (2026-07-22 reversal of the 2026-07-19 K0-DECISION(b)); instrument_type=`odds` is
  canonical (not `sports_market`).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: [sports, mtds, mdps, odds, data-status, catalogue]
related:
  [
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/02-data/sports-fixtures-lifecycle.md,
  ]
created: 2026-05-24
authoritative_for: [MTDS/MDPS sports data_type catalog (odds and derived types), sports bookmaker coverage matrix]
referenced_by:
  [/codex/01-domain/sports-instruments.md, /codex/02-data/README.md, /codex/02-data/sports-fixtures-lifecycle.md]
owner:
last_reviewed: 2026-07-22
code_refs:
---

# Sports Data Types Catalog

> **⚠️ CANONICAL CORRECTION (2026-07-22) — data_type is LOWER-CASE for sports; this REVERSES the 2026-07-19
> K0-DECISION(b) below.** Operator ruling 2026-07-22 (interactive session), on physical-estate evidence from the 7-agent
> audit in `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` § 4.3 / § 2.1: GCS holds
> **only** lowercase `data_type=odds` directories on every sampled day — day=2020-07-21 (5 objects), day=2023-05-10 (5
> objects), day=2026-04-14 (2 objects) — and **zero** `data_type=ODDS` objects on any of them, while the manifest
> carries BOTH spellings for those same days (e.g. 2020-07-21: 6 uppercase + 5 lowercase). Uppercase `ODDS` is therefore
> a **manifest-only phantom** (22,145 rows, no backing GCS objects); the 20,331 lowercase `odds` rows match disk. **The
> canonical forms are now LOWER-case: `odds`, `odds_snapshot`, `odds_movement`, `arbitrage_opportunity`,
> `odds_horizon_bucket`, `markets`, `outcomes`, `settlements`** — sports is no longer the UPPER-case exception; it now
> matches the tradfi/cefi/defi lower-case convention. **`timeframe` is its own column, never baked into `data_type`** —
> the suffixed `odds_horizon_bucket_{15m,1h,4h,1d}` cohort is still DEAD (F3), unaffected by this reversal. The two
> shipped normalizers that point UPPER→lower (`migrate_sports_canonical_v9.py:122-133`,
> `normalize_sports_mtds_data_type_case_2026_06_25.py:44-51`, neither of which ever completed) are now pointed in the
> CORRECT direction — re-point/complete them; do **not** build a lower→UPPER migration. The phantom uppercase `ODDS`
> manifest rows are tracked for physical purge in the same issue doc § 3.4, gated on this reversal (§ 4.3, now DECIDED)
> and § 4.4 (Phase 6d, still open). SSOT for the reversal:
> `plans/active/issues/ sports_shard_enumeration_cartesian_blowup_2026_07_20.md` § 4.3 + Part 4 + Progress Log
> (2026-07-22 entry).
>
> <details><summary>Superseded 2026-07-19 K0-DECISION(b) text (retained for history — do NOT act on this)</summary>
>
> CANONICAL CORRECTION (2026-07-19) — data_type is UPPER-CASE for sports. Per operator K0-DECISION (b) (2026-07-18):
> sports `data_type` is UPPER-case everywhere — sports is the only asset_group that is UPPER (tradfi/cefi/defi are
> lower-case). The canonical forms were declared `ODDS`, `ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE_OPPORTUNITY`,
> `ODDS_HORIZON_BUCKET`, `MARKETS`, `OUTCOMES`, `SETTLEMENTS` (+ the reference types `FIXTURES_SCHEDULE`/
> `FIXTURES_OUTCOMES`/`TEAMS`/… already UPPER). SSOT for the original decision:
> `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md` § K0-DECISION.
>
> </details>

> SSOT for all MTDS/MDPS Sports data type definitions, sources, shard keys, and implementation status. Last updated:
> 2026-07-22.

## Overview

> **Doc↔prod correction (2026-07-22)**: this catalog previously said "8 distinct data types" and every worked example
> below prescribed `instrument_type=sports_market`. Measurement (7-agent audit, 2026-07-20) found `sports_market` has
> **zero rows** in prod against `instrument_type=odds` on 91.5% of the manifest, and this catalog never documented the
> production-dominant raw-ingest `trades` data_type (1,806,527 rows) at all. Corrected below — see
> `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` § 2.4. `sports_market` remains a real
> `unified_api_contracts.registry.taxonomy` enum member but is **not** registered against any sports
> `(asset_group, instrument_type, data_type)` contract — do not use it in new sports code.

MTDS collects and MDPS processes Sports market data across 9 distinct data types in three categories. **All are
registered under `instrument_type=odds`** (see § "Instrument Type Mapping" below) — `sports_market` is not the
production instrument_type for any of them.

- **MTDS-raw, production-dominant**: `trades` — the actual live-writer raw-odds ingest data_type
  (`CONTRACT_REGISTRY[("sports", "odds", "trades")]` = `SPORTS_ODDS_TRADES`,
  `unified_api_contracts/internal/schemas/_sports_prediction_contracts.py:51-95`; columns include `data_source` ∈
  {`ODDS_API`, `SFI`, `FOOTYSTATS`}, `league_id`, `fixture_id`, `market_type`, `outcome`, `odds_decimal`). Whether
  `trades` and the catalogued `odds` data_type below are one logical stream under two names, or two genuinely distinct
  writers, is open vocabulary-canonicalisation work — see
  `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` Part 2. Do not assume they merge without
  reading that section first.
- **MTDS-raw, catalogued**: `odds` — tick-level odds captured directly from bookmakers via The Odds API and direct venue
  APIs.
- **MDPS-processed** (NEEDS_CANDLE=True): `odds_snapshot`, `odds_movement`, `arbitrage_opportunity`,
  `odds_horizon_bucket` — derived from raw `odds` ticks by the market data processing service.
- **Reference** (NEEDS_CANDLE=False): `markets`, `outcomes`, `settlements` — structural and result data per event;
  pass-through from source to GCS without MDPS transformation.

**Shard atom** (canonical per `/codex/02-data/sports-scheduling-and-sharding.md` § "Multi-axis correction"):
`asset_group=sports / source={bookmaker} / data_type={dt} / league_id={league} / day={date}` for all odds-based types.
`fixture_id` is a **row-level column inside the parquet, NOT a shard axis** — `(league_id, day)` already bounds the
per-day fixture set; per-fixture detail surfaces from reading the parquet rows. This avoids ~10× manifest inflation that
would result from per-fixture sharding.

**Cluster validation MANDATORY** for bundled data types (`odds_snapshot`, `arbitrage_opportunity`):
`cluster_extractor=bookmaker` — all bookmaker shards for a fixture must be present before MDPS derived computations run.
UTL guard `MissingClusterValidationError` if kwargs absent; QG STEP 5.64 statically checks.

**Disambiguation with instruments-service ODDS**: `data_type=ODDS` in instruments-service is the FootyStats pre-match
snapshot (`entity=footystats_odds/`), a one-per-fixture-date refdata-style capture (~72h before kickoff). The MTDS
Sports data types in this catalog are intra-day market movement — live ticks, horizon buckets, and cross-bookmaker arb
scanning. These are different-purpose data that legitimately coexist; do NOT merge in the aggregator. See
`/codex/02-data/sports-data-source-coverage-matrix.md` § 4 for the full disambiguation.

### GCS Path Convention

```
{resolved-sports-tick-bucket}/raw_tick_data/by_date/day={date}/asset_group=sports/
  source={BOOKMAKER}/data_type={data_type}/league_id={LEAGUE}/ticks.parquet
```

Bucket name resolved via:

```python
unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(
    cloud=..., kind="market-data-tick", asset_group="sports", env=...
)
```

Never inline `gs://...` strings — QG STEP 5.69 ratchet enforces. See `/codex/02-data/bucket-naming-and-config.md`.

Path resolver: `unified_api_contracts.sports.candidate_parquet_paths()` in
`unified_api_contracts/canonical/domain/sports/gcs_paths.py`. Coverage windows:

- `clip_dates_to_source_coverage()` — clamps date range to per-bookmaker availability window.
- `is_in_known_gap()` — returns True for known data-dark periods (API outages, subscription gaps).
- `get_expected_bookmakers()` — returns ~23 bookmakers with `per_bookmaker_start_dates` dict; this is the authoritative
  denominator for expected-shard counts per data type.

### Instrument Type Mapping

> **Corrected 2026-07-22** — was `sports_market` (zero rows in prod); see
> `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` § 2.4.

| instrument_type | Data types                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `odds`          | trades, odds, odds_snapshot, odds_movement, arbitrage_opportunity, odds_horizon_bucket, markets, outcomes, settlements |

---

## Data Type Catalog

### 1. odds

| Field               | Value                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-odds` (sports_odds_handler)                                                      |
| **Sources**         | The Odds API (`api.the-odds-api.com/v4/`), Pinnacle REST API, Betfair Exchange API        |
| **Shard key**       | source (bookmaker) × league_id × fixture-date                                             |
| **Instrument type** | `odds`                                                                                    |
| **Status**          | Production                                                                                |
| **Schema fields**   | fixture_id, league_id, bookmaker, market_type, outcome, price, last_update, ts_event      |
| **Requires**        | `odds-api-key` (The Odds API, Secret Manager); Pinnacle/Betfair credentials per-bookmaker |

Raw tick-level odds from bookmakers. One row per (fixture, market, outcome, bookmaker, timestamp) — multiple rows per
fixture as odds update throughout the pre-match and in-play windows. `market_type` ∈ {`h2h`, `spreads`, `totals`}.

Coverage gated by `is_in_known_gap()` and `clip_dates_to_source_coverage()`. `fixture_id` is a row-level filter key, not
a shard axis — all fixtures for a (league_id, day) pair land in one shard parquet.

Match-state-driven polling cadence (per `/codex/02-data/sports-scheduling-and-sharding.md` § 3):

| Match state            | Cadence                                        |
| ---------------------- | ---------------------------------------------- |
| Pre-match (> T-24h)    | Daily refresh                                  |
| Pre-match (T-24h→T-1h) | Hourly + trigger snapshots T-24h / T-6h / T-1h |
| Kickoff → full time    | 5–30s per venue (WS or REST poll)              |
| T+0 → T+15m            | Final settlement capture                       |
| T+1h onwards           | No further polling                             |

---

### 2. odds_snapshot

| Field               | Value                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------- |
| **CLI operation**   | MDPS processed (`odds_snapshot_adapter`)                                                     |
| **Sources**         | Derived from `odds` raw tick data via MDPS aggregation                                       |
| **Shard key**       | source (bookmaker) × league_id × fixture-date                                                |
| **Instrument type** | `odds`                                                                                       |
| **Status**          | Production                                                                                   |
| **NEEDS_CANDLE**    | True (MDPS candle adapter — input: `odds`)                                                   |
| **Schema fields**   | fixture_id, league_id, bookmaker, market_type, outcome, price, ts_snapshot, interval_minutes |

Periodic odds snapshots at fixed time intervals (default 15m). One row per (fixture, market, outcome, bookmaker,
snapshot-time). MDPS takes raw `odds` ticks and resamples at fixed intervals to produce a regularised time series.

Cluster validation MANDATORY: `cluster_extractor=bookmaker` — ensures all bookmaker shards for a fixture are captured
before MDPS snapshot computation runs. A partial bookmaker set would silently produce snapshot rows for only a subset of
books, corrupting downstream cross-bookmaker comparisons.

---

### 3. odds_movement

| Field               | Value                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | MDPS processed (`odds_movement_adapter`)                                                                      |
| **Sources**         | Derived from `odds_snapshot` via MDPS delta computation                                                       |
| **Shard key**       | source (bookmaker) × league_id × fixture-date                                                                 |
| **Instrument type** | `odds`                                                                                                        |
| **Status**          | Production                                                                                                    |
| **NEEDS_CANDLE**    | True (MDPS candle adapter — input: `odds`)                                                                    |
| **Schema fields**   | fixture_id, league_id, bookmaker, market_type, outcome, price_prev, price_curr, delta, delta_pct, ts_snapshot |

Delta in odds from the prior snapshot interval. One row per (fixture, market, outcome, bookmaker, interval). `delta` =
absolute change in decimal odds; `delta_pct` = percentage change. Large `delta_pct` movements are steam-move signals
used by features-service to compute closing-line value (CLV) and late-money-detection features.

Used by features-service for odds-drift signals, steam-move detection, and market-efficiency metrics. Requires
`odds_snapshot` as an upstream input — MDPS must have at least two consecutive snapshot intervals before `delta` can be
computed.

---

### 4. arbitrage_opportunity

| Field               | Value                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | MDPS processed (`arbitrage_scanner_adapter`)                                                                               |
| **Sources**         | Derived from `odds` across multiple bookmakers via MDPS cross-bookmaker scan                                               |
| **Shard key**       | league_id × fixture-date (cross-bookmaker — source dimension dropped for the output shard)                                 |
| **Instrument type** | `odds`                                                                                                                     |
| **Status**          | Production                                                                                                                 |
| **NEEDS_CANDLE**    | True (MDPS computed type — input: `odds` from all bookmakers)                                                              |
| **Schema fields**   | fixture_id, league_id, market_type, outcome_A, bookmaker_A, price_A, outcome_B, bookmaker_B, price_B, arb_pct, detected_at |
| **Processed dep**   | `odds` (any bookmaker shard captured — `_DERIVED_ONLY["arbitrage_opportunity"] = ["odds"]` in UAC)                         |

Cross-bookmaker arbitrage opportunities. One row per detected arb (back-lay or multi-way). `arb_pct` = guaranteed profit
percentage assuming equal stakes proportionally distributed across bookmakers. A positive `arb_pct` means the implied
probability sum across outcomes is less than 1.0 — a risk-free profit opportunity exists if fills can be obtained at the
observed prices.

MDPS scans all captured `odds` shards for a fixture at each 15m interval. The `source` shard dimension is dropped from
the output because the arb row references multiple bookmakers inline (`bookmaker_A`, `bookmaker_B`).

Cluster validation MANDATORY: `cluster_extractor=bookmaker` ensures all bookmaker shards are present before arb
computation runs. Computing arb from an incomplete bookmaker set would produce false positives (missing the book that
closes the loop) or false negatives (missing the book that creates the opportunity).

---

### 5. odds_horizon_bucket

| Field               | Value                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------- |
| **CLI operation**   | MDPS processed (`odds_horizon_adapter`)                                                   |
| **Sources**         | Derived from `odds_snapshot` bucketed by time-to-kickoff                                  |
| **Shard key**       | source (bookmaker) × league_id × fixture-date                                             |
| **Instrument type** | `odds`                                                                                    |
| **Status**          | Production                                                                                |
| **NEEDS_CANDLE**    | True (MDPS candle adapter — input: `odds`)                                                |
| **Schema fields**   | fixture_id, league_id, bookmaker, market_type, outcome, price, horizon_label, ts_snapshot |
| **Horizon labels**  | `T-24h`, `T-12h`, `T-6h`, `T-4h`, `T-2h`, `T-1h`, `T-10m`, `T-0`                          |

Pre-game odds captured at fixed time horizons before kickoff (T-X labels). One row per (fixture, market, outcome,
bookmaker, horizon). Enables analysis of how odds compress or drift as the match approaches — the compression of spreads
and convergence of bookmaker lines in the final hours is a key market-efficiency signal.

`T-0` = last captured odds before kickoff; this is the "closing line" used for CLV computation in strategy-service.
`T-24h` is typically the opening line for fixtures announced more than 24h ahead. Horizons where the match had already
started (e.g. a fixture kicked off early) have `empty_confirmed` status with reason `EXPECTED_FIXTURE_STARTED_EARLY`.

Used by features-service for betting-market-implied probability signals, CLV (closing line value), and line-movement
trajectory features. The 8-horizon structure provides a standardised time series for ML feature engineering without
requiring the raw tick granularity.

---

### 6. markets

| Field               | Value                                                                                                     |
| ------------------- | --------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-markets` (sports_markets_handler)                                                                |
| **Sources**         | The Odds API (`/sports/{sport}/events` + `/events/{eventId}/odds`), instruments-service fixture catalogue |
| **Shard key**       | league_id × fixture-date                                                                                  |
| **Instrument type** | `odds`                                                                                                    |
| **Status**          | Production                                                                                                |
| **NEEDS_CANDLE**    | False (structural reference data — pass-through)                                                          |
| **Schema fields**   | fixture_id, league_id, sport, home_team, away_team, commence_time, market_type, status                    |

Betting market structure for each fixture. One row per (fixture, market_type). Captures which markets (`h2h`, `spreads`,
`totals`, `btts`, `h2h_lay`, etc.) are available per event and their current status (`pre-game`, `in-play`, `closed`).

`markets` is the reference table consumed by MDPS to determine which (fixture, market_type) combinations have odds
coverage and should be included in derived computations. Used by instruments-service as the authoritative fixture
catalogue for the MTDS sports domain (parallel to api_football `FIXTURES` for the instruments-service sports domain).

Structural reference: a `markets` row exists for every fixture that The Odds API knows about, regardless of whether any
bookmaker has offered prices. The `status` column tracks lifecycle from `pre-game` through `in-play` to `closed`.

---

### 7. outcomes

| Field               | Value                                                                              |
| ------------------- | ---------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-outcomes` (sports_outcomes_handler)                                       |
| **Sources**         | The Odds API (`/events/{eventId}/odds?markets={market_type}`), instruments-service |
| **Shard key**       | league_id × fixture-date                                                           |
| **Instrument type** | `odds`                                                                             |
| **Status**          | Production                                                                         |
| **NEEDS_CANDLE**    | False (structural reference data — pass-through)                                   |
| **Schema fields**   | fixture_id, league_id, market_type, outcome_name, outcome_key, sort_order          |

Available selections/runners per market type for each fixture. One row per (fixture, market, outcome). `outcome_key` ∈
{`home`, `draw`, `away`, `over`, `under`, `yes`, `no`}. Normalised across bookmakers so `outcome_key` is canonical
regardless of bookmaker-specific naming conventions (e.g. Betfair uses "Team A" and "Team B"; The Odds API uses home
team name — both map to canonical `home`/`away` keys).

Used together with `markets` to construct the full betting-market instrument universe. `sort_order` preserves the
canonical display ordering for UI rendering (e.g. `home, draw, away` for h2h; `over, under` for totals).

---

### 8. settlements

| Field               | Value                                                                                         |
| ------------------- | --------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-settlements` (sports_settlement_handler)                                             |
| **Sources**         | The Odds API scores endpoint (`/sports/{sport}/scores`), official league APIs where available |
| **Shard key**       | league_id × fixture-date                                                                      |
| **Instrument type** | `odds`                                                                                        |
| **Status**          | Production                                                                                    |
| **NEEDS_CANDLE**    | False (reference data — pass-through)                                                         |
| **Schema fields**   | fixture_id, league_id, home_score, away_score, winner, market_outcomes, settled_at, status    |

Final match results and settlement data. One row per fixture. `winner` ∈ {`home`, `draw`, `away`}. `market_outcomes` is
a JSON field containing per-market settlement (e.g. `{"h2h": "home", "totals_2.5": "over", "btts": "yes"}`).

Available approximately 2–24h post-match depending on the league and data provider's scoring pipeline latency. The
`status` column transitions through `in_progress` → `completed` → `settled`; consumers should only read rows with
`status = "settled"` for P&L calculation.

Used by strategy-service for P&L settlement of open sports positions. Used by features-service to label training targets
(realised outcome vs model-implied / market-implied probability). The `settled_at` timestamp preserves point-in-time
semantics — downstream ML must not use settlement data with `settled_at > kickoff_utc` as a training feature for any
pre-match model.

---

## Bookmaker Coverage Matrix

| bookmaker              | data_types                           | start date availability | notes                                                                                |
| ---------------------- | ------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------ |
| THE_ODDS_API           | odds, markets, outcomes, settlements | varies by sport/league  | Aggregator; ~90% bookmaker coverage via single API; per-bookmaker start dates in UAC |
| PINNACLE               | odds, odds_snapshot                  | varies by league        | Sharp book; included in arb scanner; highest-quality closing lines                   |
| BETFAIR_EX             | odds, odds_snapshot                  | varies by league        | Exchange pricing; lay odds available; key arb source (back/lay spread)               |
| DRAFTKINGS             | odds                                 | varies by league        | US market; via The Odds API aggregator                                               |
| FANDUEL                | odds                                 | varies by league        | US market; via The Odds API aggregator                                               |
| BET365                 | odds                                 | varies by league        | Global market; via The Odds API aggregator; key reference book                       |
| WILLIAM_HILL           | odds                                 | varies by league        | UK market; via The Odds API aggregator                                               |
| BWIN                   | odds                                 | varies by league        | EU market; via The Odds API aggregator                                               |
| UNIBET                 | odds                                 | varies by league        | EU/AU market; via The Odds API aggregator                                            |
| BETWAY                 | odds                                 | varies by league        | Global market; via The Odds API aggregator                                           |
| MARATHON_BET           | odds                                 | varies by league        | Sharp EU book; via The Odds API aggregator                                           |
| BETSSON                | odds                                 | varies by league        | EU market; via The Odds API aggregator                                               |
| SUPABETS               | odds                                 | varies by league        | Africa market; via The Odds API aggregator                                           |
| (additional ~10 books) | odds                                 | varies by league        | via The Odds API aggregator; see `get_expected_bookmakers()` for full list           |

**Note:** Per-bookmaker start dates and availability windows are declared in UAC `get_expected_bookmakers()` returning a
dict with `per_bookmaker_start_dates: dict[str, date]`. This is the authoritative denominator for expected-shard counts
— never hardcode bookmaker lists inline. Coverage varies significantly by sport: football (soccer) has the broadest
coverage (~23 books); niche sports may have 5–8 books.

---

## Coverage Axes

| data_type               | Coverage axis                                   | Expected shards (per day)                                             | record_empty expected                                                                                 |
| ----------------------- | ----------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `odds`                  | per-league × per-bookmaker × per-fixture-date   | league × bookmaker × fixture_calendar                                 | Yes — bookmaker dark for a match day = `attempted_failed` (not `empty_confirmed`)                     |
| `odds_snapshot`         | per-league × per-bookmaker × per-fixture-date   | same as odds                                                          | Yes — same rule as `odds`                                                                             |
| `odds_movement`         | per-league × per-bookmaker × per-fixture-date   | same as odds                                                          | Yes — fewer than 2 intervals available = `empty_confirmed`                                            |
| `arbitrage_opportunity` | per-league × per-fixture-date (cross-bookmaker) | league × fixture_calendar (1 shard per league-day, not per-bookmaker) | Yes — no arb found in interval = `empty_confirmed`; missing bookmaker = `attempted_failed`            |
| `odds_horizon_bucket`   | per-league × per-bookmaker × per-fixture-date   | same as odds                                                          | Yes — horizon window missed (match started early) = `empty_confirmed[EXPECTED_FIXTURE_STARTED_EARLY]` |
| `markets`               | per-league × per-fixture-date                   | league × fixture_calendar                                             | Yes — fixture cancelled before any book offered prices = `empty_confirmed`                            |
| `outcomes`              | per-league × per-fixture-date                   | same as markets                                                       | Yes — market type has no outcomes (e.g. totals not offered) = `empty_confirmed`                       |
| `settlements`           | per-league × per-fixture-date                   | same as markets                                                       | Yes — unsettled (match not yet finished) = `expected_unattempted`; postponed = `empty_confirmed`      |

**Key distinction on `attempted_failed` vs `empty_confirmed` for odds types**: if a bookmaker's API returned an error or
timeout for a fixture, the correct status is `attempted_failed` — the data MAY exist but we could not retrieve it. If
the bookmaker genuinely did not offer prices for a specific match (e.g. a bookmaker does not cover lower-league
football), the correct status is `empty_confirmed` with an `EXPECTED_*` reason.

---

## Implementation Notes

### NEEDS_CANDLE processing summary

| NEEDS_CANDLE | data_types                                                                       |
| ------------ | -------------------------------------------------------------------------------- |
| True         | `odds_snapshot`, `odds_movement`, `arbitrage_opportunity`, `odds_horizon_bucket` |
| False        | `odds`, `markets`, `outcomes`, `settlements`                                     |

NEEDS_CANDLE=True types are processed by MDPS after MTDS collects raw `odds` ticks. The MTDS handler writes `odds`
shards; MDPS reads those shards, runs the derived computation, and writes the processed output. The two services are
decoupled: MTDS does not invoke MDPS directly. MDPS determines when to process based on manifest `capture_status` of the
upstream `odds` shards.

### Cluster validation

Cluster validation is MANDATORY for bundled data types when the bundle has multi-bookmaker structure:

- **`odds_snapshot`** — `cluster_extractor=bookmaker`: snapshot computation requires a consistent bookmaker set per
  fixture-day. If bookmaker B was captured but bookmaker C was not, the snapshot still runs for B's shard, but the
  cluster validator gate records which bookmakers were expected vs present.
- **`arbitrage_opportunity`** — `cluster_extractor=bookmaker`: arb detection requires ALL expected bookmakers. If any
  bookmaker shard is missing (`attempted_failed` or `expected_unattempted`), the arb computation will silently miss
  opportunities. The cluster validator ensures the MDPS job flags partial bookmaker coverage before running.

Implementation: UTL `record_captured()` asserts `cluster_extractor` and `cluster_keys` kwargs present for bundled types.
Missing kwargs → `MissingClusterValidationError`. QG STEP 5.64 statically checks handler source files.

### API key requirements

| handler                   | Secret Manager key | Fallback               |
| ------------------------- | ------------------ | ---------------------- |
| sports_odds_handler       | `odds-api-key`     | `ODDS_API_KEY` env     |
| sports_markets_handler    | `odds-api-key`     | `ODDS_API_KEY` env     |
| sports_outcomes_handler   | `odds-api-key`     | `ODDS_API_KEY` env     |
| sports_settlement_handler | `odds-api-key`     | `ODDS_API_KEY` env     |
| Pinnacle direct           | `pinnacle-api-key` | `PINNACLE_API_KEY` env |
| Betfair Exchange          | `betfair-api-key`  | `BETFAIR_API_KEY` env  |

The Odds API key is the gateway credential for ~90% of bookmaker coverage. Without it, only direct-API bookmakers
(Pinnacle, Betfair) are reachable.

### Shard-level failure isolation

All MTDS sports odds handlers follow the shard-level isolation pattern: exceptions caught per-bookmaker/per-league loop,
recorded via manifest `record_failed(error=classify_venue_error(exc))`, loop continues. No `raise` inside per-shard
loops. SSOT: `/codex/04-architecture/shard-level-failure-isolation.md`.

### Manifest honest-absence emission

All sports MTDS handlers emit honest-coverage entries per the manifest v5 contract:

- `record_captured(...)` — rows written to GCS parquet
- `record_empty(reason=<EmptyConfirmedReason>)` — zero rows, legitimate absence (e.g. bookmaker does not cover league)
- `record_failed(error=classify_venue_error(exc))` — exception caught; data may exist but was unretrievable

`available_at` is per-row write-time, asserted by UTL `record_captured` internally.

### Known gaps

- **UK/EU scraper bookmakers** (Coral, PaddyPower, WilliamHill native scraper) — not available through The Odds API
  aggregator endpoint; scraper-based adapters would require browser automation or unofficial API reverse-engineering.
  Status: `BLOCKED-CREDENTIALS` for native API keys; The Odds API covers WilliamHill as an aggregated source.
- **In-play odds** — The Odds API in-play endpoint requires a separate subscription tier. In-play odds collection from
  5–30s WS or REST poll is architecturally wired (see `sports-scheduling-and-sharding.md` § 3) but the in-play
  subscription credential is a separate operator approval item. Status: `BLOCKED-CREDENTIALS`.
- **Asian bookmakers** (Pinnacle Asia, SBOBet, IBC) — jurisdiction restrictions may apply; some routes require Cayman
  entity routing (see user memory: `project_trading_entities.md`). Status: `BLOCKED-OPERATOR-DECISION` for full
  coverage; Pinnacle global is included.
- **Historical odds before bookmaker start dates** — `get_expected_bookmakers()` `per_bookmaker_start_dates` defines the
  per-bookmaker coverage floor. Historical requests before the start date are gated by `clip_dates_to_source_coverage()`
  which returns an empty range — no backfill is possible. Status: legitimate gap, `empty_confirmed` with
  `EXPECTED_SOURCE_COVERAGE_START`.

---

## Related Documents

- `/codex/02-data/sports-gcs-path-ssot.md` — canonical GCS path resolver for all sports parquets
- `/codex/02-data/sports-data-source-coverage-matrix.md` — expected league counts, coverage axes, aggregator algorithm
- `/codex/02-data/sports-adapter-dependency-order.md` — T0/T1 adapter dependency order for instruments-service
- `/codex/02-data/sports-scheduling-and-sharding.md` — scheduling cadence, shard-atom definition, lookahead-bias rules
- `/codex/02-data/sports-fixtures-lifecycle.md` — fixture state transitions and honest-absence semantics
- `/codex/02-data/per-asset-group-bucket-layouts.md` — GCS bucket layout per asset_group (sports section)
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest v5 honest-coverage schema
- `/codex/04-architecture/shard-level-failure-isolation.md` — per-shard error handling invariant
- Plans epic: `plans/epics/sports_master.md` — sports asset_group umbrella epic
- `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` — 7-agent audit that reversed
  K0-DECISION(b) case direction and corrected the `instrument_type`/`trades` doc↔prod gap (2026-07-22, Part 4)
