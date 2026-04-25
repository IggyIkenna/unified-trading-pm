---
scope: [engineer, admin]
---

# Prediction Market Schema Paths

SSOT for prediction market data flowing through the unified trading system.

## Category

`PREDICTION` — one of five `MarketCategory` values in UIC (`market_category.py`).

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

```
instruments-store-prediction-{project}/
  instrument_availability/by_date/day={date}/venue=POLYMARKET/instruments.parquet

market-data-tick-prediction-{project}/
  raw_tick_data/by_date/day={date}/data_type=trades/venue=POLYMARKET/
    sub_category=crypto/{asset}_{timeframe}.parquet
    sub_category=macro/{index}_{timeframe}.parquet
    sub_category=football/{fixture_id}.parquet
```

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
