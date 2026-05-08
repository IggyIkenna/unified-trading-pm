---
scope: [engineer, admin]
---

# Prediction Market Schema Paths

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

> **Multi-axis correction (2026-05-06)** — shard atoms vs display axes (row-level columns) per asset_group are the SSOT
> in
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical).
> See that doc for the full per-asset-group shard-atom matrix (sports / prediction / cefi options-futures / DeFi chain /
> ML+strategy+execution job_id / TradFi EVENT_CONTRACT).

SSOT for prediction market data flowing through the unified trading system.

**Active migration**: predictions Plan A
([`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](../../plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md))
migrates from per-base_asset shard atom (`data_type=BTC|ETH|SPX|FOOTBALL|OTHER`) to canonical_question_group bundled
shard atom + per-market lifecycle. Both shapes documented below: legacy (pre-Plan A) + target (post-Plan A).

**Related**: [availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md),
[04-architecture/shard-level-failure-isolation.md](../04-architecture/shard-level-failure-isolation.md),
[05-infrastructure/deployment-clusters-live-vs-batch.md](../05-infrastructure/deployment-clusters-live-vs-batch.md),
[06-coding-standards/validation-patterns.md](../06-coding-standards/validation-patterns.md).

## Asset group

`PREDICTION` — one of five `MarketAssetGroup` values in UAC. (Legacy term: "category".)

## Venues

| Venue      | API Auth      | Data Sources                                                    |
| ---------- | ------------- | --------------------------------------------------------------- |
| POLYMARKET | None (public) | Gamma API (metadata), CLOB API (books/trades), Data API (fills) |
| KALSHI     | API key       | REST API (markets, trades, books)                               |

## Sub-Categories

```
PREDICTION
├── PREDICTION::CRYPTO       — BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up/down (5m to monthly)
├── PREDICTION::MACRO        — SPX/NDX/DJIA/DAX/crude/gold/silver/forex up/down (daily+)
├── PREDICTION::FOOTBALL     — 25+ soccer leagues (moneyline/spreads/totals/btts)
└── PREDICTION::SPORTS_OTHER — NBA/NFL/MLB/MMA/esports (future)
```

## Canonical Instrument ID Format

| Sub-category     | Format                                                  | Example                                    |
| ---------------- | ------------------------------------------------------- | ------------------------------------------ |
| Crypto up/down   | `POLYMARKET::UP_DOWN::{ASSET}::{TF}::{WINDOW_END_TS}`   | `POLYMARKET::UP_DOWN::BTC::5M::1774230900` |
| Macro up/down    | `POLYMARKET::UP_DOWN::{INDEX}::{TF}::{DATE}`            | `POLYMARKET::UP_DOWN::SPX::1D::2026-03-25` |
| Soccer moneyline | `POLYMARKET::MONEYLINE::{FIXTURE_ID}::{OUTCOME}`        | `POLYMARKET::MONEYLINE::1034567::HOME`     |
| Soccer spreads   | `POLYMARKET::SPREADS::{FIXTURE_ID}::{OUTCOME}_{LINE}`   | `POLYMARKET::SPREADS::1034567::AWAY_-1.5`  |
| Soccer totals    | `POLYMARKET::TOTALS::{FIXTURE_ID}::{OVER_UNDER}_{LINE}` | `POLYMARKET::TOTALS::1034567::OVER_2.5`    |
| Soccer BTTS      | `POLYMARKET::BTTS::{FIXTURE_ID}::{YES_NO}`              | `POLYMARKET::BTTS::1034567::YES`           |

## GCS Hive Paths

### Legacy (pre-Plan A — current as of 2026-05-06)

```
instruments-store-prediction-{project}/
  instrument_availability/by_date/day={date}/venue=POLYMARKET/instruments.parquet

market-data-tick-prediction-{project}/
  raw_tick_data/by_date/day={date}/data_type=trades/venue=POLYMARKET/
    sub_category=crypto/{asset}_{timeframe}.parquet
    sub_category=macro/{index}_{timeframe}.parquet
    sub_category=football/{fixture_id}.parquet
```

Pre-Plan A shards at the legacy `instrument_type=<base_asset>` level (BTC / ETH / SPX / FOOTBALL / OTHER) with no
per-market identification preserved at write-time. **NEW BUG SURFACED** (Phase 0 audit 2026-05-06): orchestrator
prediction empty path returns `success=True, candles_generated=0` with NO manifest record — distinct from 1440-NaN class
but equally opaque. Fix in writegate Phase 2.A scope expansion: adds `record_empty(row_key)` so prediction empties
surface as honest absence.

### Target (post-Plan A)

```
instruments-store-prediction-{project}/
  by_date/day={date}/asset_group=prediction/
    venue=POLYMARKET/data_type=MARKET_LIFECYCLE/{market_id}.parquet     ← per-market lifecycle metadata

market-data-tick-prediction-{project}/
  raw_tick_data/by_date/day={date}/asset_group=prediction/venue=POLYMARKET/
    data_type=prediction_canonical_question_group/
      canonical_question_group={cqg}/
        {market_id}.parquet     ← per-market CLOB ticks within canonical_question_group bundle
```

**Shard atom**:
`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)`.
Bundled by canonical_question_group with per-market_id rows. **Cluster validation MANDATORY** (writegate Phase 1A):
`cluster_extractor=lambda row: row["market_id"]` + `PREDICTION_GROUPS` registry per cadence (HOURLY=24/day, DAILY=1/day,
ELECTION=1 over months). UTL guard `MissingClusterValidationError` raised if absent.

### Canonical question groups (UAC `CanonicalQuestionGroup` enum, predictions Plan A)

| Cadence           | Examples                                                                          | Expected market_ids per (canonical_group, day) |
| ----------------- | --------------------------------------------------------------------------------- | ---------------------------------------------- |
| Hourly recurring  | `BTC_UP_DOWN_HOURLY`, `ETH_UP_DOWN_HOURLY`                                        | 24                                             |
| Daily recurring   | `BTC_UP_DOWN_DAILY`, `SPX_UP_DOWN_DAILY`, `BTC_PRICE_AT_CLOSE_DAILY`              | 1                                              |
| Weekly recurring  | `BTC_UP_DOWN_WEEKLY`                                                              | ~1/7                                           |
| Monthly recurring | `BTC_UP_DOWN_MONTHLY`, `SPX_UP_DOWN_MONTHLY`                                      | ~1/30                                          |
| Single-event      | `ELECTION_PRESIDENT_2028`, `ELECTION_HOUSE_2026`, `OSCARS_2026`, `WORLD_CUP_2026` | 1 over months/years                            |
| Macro / FOMC      | `FED_RATE_DECISION_PER_FOMC`                                                      | irregular per FOMC schedule                    |
| Sports outcome    | (per-fixture; cross-references sports per-fixture sharding)                       | 1 per fixture                                  |
| `OTHER`           | Catch-all for unclassifiable; classifier-confidence-low                           | varies                                         |

Mapping driven by:

- `unified_api_contracts.canonical.domain.predictions.classifiers.classify_market_to_canonical_group(market_metadata)` —
  word-boundary regex + token-overlap scoring + classifier stability hash.
- `POLYMARKET_CONDITION_ID_TO_GROUP` (UAC) — hand-curated overrides for headline markets.
- `KALSHI_TICKER_TO_GROUP` (UAC) — same shape for Kalshi.

Markets where classifier returns `None` (sub-threshold confidence) → `record_failed(ClassifierConfidenceLow)`.

### Per-market lifecycle (instruments-service)

Each market_id has lifecycle timestamps captured in instruments-service `MARKET_LIFECYCLE` data_type:

| Field               | Semantics                                                                                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `market_created_at` | When the market was listed on Polymarket / Kalshi. `available_at` for the metadata row = this value (we couldn't have known about the market before it was listed). |
| `resolution_time`   | When the outcome was determined (oracle resolution).                                                                                                                |
| `settlement_time`   | When payouts happened (typically resolution_time + small buffer).                                                                                                   |
| `current_status`    | `created` / `active` / `resolved` / `settled`                                                                                                                       |

**MTDS respects lifecycle bounds**: NO ticks captured before `market_created_at`, NO new ticks captured after
`settlement_time` (the market is closed; post-settlement data is not informative). **LookaheadBiasError
per-market-aware**: a feature compute at time T can only consume ticks where `tick.timestamp <= T` AND
`tick.market_id`'s `market_created_at <= T` AND `tick.market_id`'s `settlement_time > T`.

### Migration (predictions Plan A Phase 3.A reconciler)

`mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` reads existing per-base_asset Polymarket parquets, looks
up each row's `condition_id` via UAC classifier to derive `canonical_question_group`, regroups by
`(canonical_question_group, day)`, writes new parquets at canonical path. Old `data_type=BTC|ETH|...` rows flip to
`attempted_failed[reason=ShardSchemaMigrated]` for cleanup. Old parquets deleted only after sample verification.

## Polymarket API Endpoints

| API   | Base URL                   | Auth                  | Rate Limit              |
| ----- | -------------------------- | --------------------- | ----------------------- |
| Gamma | `gamma-api.polymarket.com` | None                  | ~100 req/s              |
| CLOB  | `clob.polymarket.com`      | L2 HMAC (trades only) | ~50 req/s               |
| Data  | `data-api.polymarket.com`  | None                  | ~20 req/s (429 backoff) |

## Soccer League Mappings (SSOT)

35 Polymarket series slugs mapped to canonical league IDs in
`unified_api_contracts/external/polymarket/sports_mappings.py:POLYMARKET_SERIES_TO_LEAGUE`.

## Team Name Normalization

196 Polymarket team names mapped to canonical team IDs in
`unified_api_contracts/external/polymarket/sports_mappings.py:POLYMARKET_TEAM_TO_CANONICAL`.

Covers: La Liga, Serie A, Ligue 1, A-League, MLS, Copa del Rey, Portuguese Primeira Liga, Scottish Premiership, Turkish
Süper Lig, UCL/UEL, Colombian Primera A, Argentine Primera.

EPL and Bundesliga teams already covered by `api_football/team_mappings.py`.

## Crypto/Macro Underlyings

20 underlyings with timeframes in
`unified_api_contracts/external/polymarket/crypto_macro_mappings.py:POLYMARKET_TIMEFRAMES`.

| Asset                              | Timeframes                  |
| ---------------------------------- | --------------------------- |
| BTC                                | 5m, 15m, 1h, 4h, 1d, 1w, 1M |
| ETH                                | 5m, 15m, 1h, 4h, 1d, 1w, 1M |
| SOL                                | 5m, 15m, 1h, 4h, 1d         |
| SPX                                | 1d, 1M                      |
| NDX                                | 1d, 1M                      |
| DJIA, DAX, Hang Seng, Russell 2000 | 1d                          |
| Crude Oil, Gold, Silver            | 1d                          |
| EUR/USD, GBP/USD, USD/JPY, USD/KRW | 1d                          |

## Pipeline Flow

```
instruments-service --asset-group PREDICTION
  └─ URDI PolymarketReferenceDataAdapter → Gamma API → InstrumentRecord[]
       └─ Writes to: instruments-store-prediction-{project}/by_date/day={date}/

market-tick-data-service --asset-group PREDICTION
  └─ UMI PolymarketAdapter → Data API + CLOB API → trade fills
       └─ Writes to: market-data-tick-prediction-{project}/by_date/day={date}/
```
