---
scope: [engineer, admin]
status: canonical
last_reviewed: 2026-06-21
---

# Prediction Crypto-Perps Sourcing (Kalshi-Perp / Polymarket-Perp)

> SSOT for the **crypto perpetual-futures** product on the prediction venues — distinct from the binary YES/NO
> prediction markets. Kalshi and Polymarket each launched CFTC-regulated crypto perps in 2026 (Kalshi 2026-05-29,
> Polymarket 2026-04-21). These are **`cefi` asset_group** instruments (regulated crypto perps), NOT `prediction`.
> Plan-of-record: `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.

## Venue tokens (UAC `registry/venue_constants.py` — already registered)

| Token             | Value             | asset_group | instrument_type | capability   | launch     |
| ----------------- | ----------------- | ----------- | --------------- | ------------ | ---------- |
| `KALSHI_PERP`     | `KALSHI-PERP`     | `cefi`      | `PERPETUAL`     | `PERP_TRADE` | 2026-05-29 |
| `POLYMARKET_PERP` | `POLYMARKET-PERP` | `cefi`      | `PERPETUAL`     | `PERP_TRADE` | 2026-04-21 |

These are **separate tokens** from the prediction `KALSHI` / `POLYMARKET` (YES/NO markets). Same vendor, different
product path + asset_group. Wired into `CLOB_VENUES`, `VENUE_CAPABILITIES`, `INSTRUMENT_TYPES_BY_VENUE`,
`VENUE_CATEGORY_MAP` (cefi), `VENUE_FEE_MODEL_MAP` (MAKER_TAKER), `VENUE_ALPHA_PROFILE`, `VENUE_ORDER_CAPABILITIES`,
`CEFI_VENUE_LAUNCH_DATES`, `CEFI_SOURCE_COVERAGE_START`, `VENUES_BY_ASSET_GROUP["cefi"]`,
`VenueMapping.venue_start_dates`.

## Kalshi perps API (Phase-0 verified)

- Base: `https://api.elections.kalshi.com/trade-api/v2/` (same base as prediction markets; separate product path).
- Exchange status: `GET /exchange/status` → `{"exchange_active":true,"trading_active":true}` (public, no auth).
- Contract list: `GET /markets?category=CRYPTO&status=active` (public read; category filter accepted). ~13 CFTC-approved
  crypto perpetual contracts (BTC/ETH/SOL/DOGE/AVAX/LINK/UNI/AAVE/...).
- Trades: `GET /markets/{ticker}/trades` → `{trades:[{trade_id, taker_side, count, yes_price, created_time}]}`
  (≤1000/call, cursor pagination).
- Funding rate: `GET /markets/{ticker}/funding_rates` (dedicated endpoint; periodic/hourly funding).
- Orderbook: `GET /markets/{ticker}/orderbook` (CLOB depth snapshot: bid/ask levels).
- Websocket: `wss://api.elections.kalshi.com/trade-api/ws/v2` —
  `{"cmd":"subscribe","params":{"channels":["orderbook_delta"],"market_tickers":[...]}}` for live book + trades.
- **Auth: public read** (market list, orderbook, trades, funding) = NO auth. Order placement = RSA-PSS key (same as the
  prediction-market API). Rate limit: 100 req/s on public-read endpoints (documented).
- History depth: from the 2026-05-29 launch only (no pre-launch perp history exists).

## Polymarket perps API

Polymarket crypto perps use the Polymarket product surface; the concrete live endpoint is captured in the plan's Phase-0
Polymarket-perps section. Sourcing is public-read (Gamma/CLOB), mirroring the prediction-market Polymarket pattern.
History from the 2026-04-21 launch only.

## Pipeline (IS → MTDS, same contract as every venue)

1. **instruments-service** enumerates active perp contracts → writes `InstrumentRecord` (type `PERPETUAL`) to the
   instrument store. Public-read enumerator adapter, mirrors the prediction-market `KalshiReferenceDataAdapter` pattern
   (`classify_venue_error()` on every error, `aiohttp`, cursor pagination, honest-absence on empty). IS owns the venue
   universe; MTDS derives URLs from IS (never hardcodes).
2. **market-tick-data-service** reads the IS universe and downloads perp **trades** + **funding rates** (batch
   historical window) + live CLOB **quotes (BBO) + order-book depth** (websocket). Batch=live: identical schema +
   data_types + manifest rows; only the fill differs.
3. Manifest: 4-state honest coverage; `source`-aware `pipeline_mode` (`batch_kalshi`/`live_kalshi` etc. resolve via UAC
   `pipeline_mode_for_source` / `live_pipeline_mode_for_venue`).

## data_types

- `trades` — perp trade executions (taker_side, count/size, price, ts).
- `funding_rate` / `perp_funding` — periodic funding (the carry leg for funding-rate-arb / basis archetypes).
- `book_snapshot` / depth — live CLOB BBO + levels (the arb-backtest data; live websocket).

## Strategy use

Kalshi/Polymarket perp **funding** feeds the funding-rate-arb + basis archetypes (cross-venue dispersion vs the CeFi
perp venues — Binance/Bybit/OKX/Deribit/Hyperliquid/Aster/Kraken). The perps are a CeFi perp surface, so they compose
with the existing CeFi perp-funding universe, not the prediction dispersion feature.

## Status

Venue tokens + Phase-0 API research: DONE. IS perp enumerator + MTDS perp trades/funding adapters + live CLOB
connectors: in build (plan lines 30/34/38). This doc is the sourcing SSOT; update the per-adapter status here as each
lands.
