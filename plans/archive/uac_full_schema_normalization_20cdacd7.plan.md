---
doc_type: plan
title: UAC Full Schema Normalization
summary: Complete specification for normalizing all external API contracts across 60+ venues into canonical formats, with
  full matrix generation, live/batch symmetry, and references for every data source and schema.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-06"
todos: []
isProject: false
---

# UAC Full Schema Normalization — Complete Task Specification

## 1. Scope and Objectives

**Goal:** Every external schema from every data source (60+ venues) must have a `normalize_<provider>_<schema>()`
function that maps to a canonical type. Output is identical regardless of source (live WebSocket vs batch GCS/API).

**Principles:**

- **Live-batch symmetry:** Same canonical output whether data comes from live stream or historical batch. No
  `if mode == "batch"` in normalizers.
- **Single source of truth:** `unified_api_contracts/unified_normalised_contracts/domain.py` defines all `Canonical`\*
  types.
- **Matrix-driven:** `scripts/generate_schema_audit_matrix.py` scans schemas + normalizers and produces
  `docs/SCHEMA_AUDIT_MATRIX.md` as SSOT for coverage.

---

## 2. Canonical Types (domain.py)

| Canonical Type                         | Purpose              | Key Fields                                                    |
| -------------------------------------- | -------------------- | ------------------------------------------------------------- |
| CanonicalTrade                         | Spot/perp trades     | venue, symbol, price, size, side, timestamp, trade_id         |
| CanonicalOrderBook                     | Order books          | venue, symbol, bids, asks, timestamp, sequence_number         |
| CanonicalTicker                        | Spot tickers         | venue, symbol, last, bid, ask, volume, timestamp              |
| CanonicalOrder                         | Orders               | venue, symbol, order_id, side, size, price, status, timestamp |
| CanonicalFill                          | Fills/executions     | venue, symbol, fill_id, order_id, price, size, fee, timestamp |
| CanonicalOhlcvBar                      | OHLCV bars           | venue, symbol, open, high, low, close, volume, timestamp      |
| CanonicalOptionsChainEntry             | Options chain        | symbol, strike, expiry, bid, ask, delta, gamma, iv            |
| CanonicalDerivativeTicker              | Perp/futures tickers | funding_rate, mark_price, index_price, open_interest          |
| CanonicalMarketInfo / InstrumentRecord | Reference data       | symbol, base, quote, venue, type (spot/perp/option)           |
| CanonicalFee                           | Fee rates/amounts    | amount, currency, fee_type (maker/taker), venue               |
| CanonicalLiquidation                   | Liquidations         | symbol, side, size, price, timestamp, is_market_feed          |
| CanonicalError                         | Normalized errors    | error_code, message, category (rate_limit/auth/business)      |
| CanonicalWebSocketLifecycle            | Connect/disconnect   | event (connect/disconnect/ping/pong), timestamp               |

---

## 3. Venue Matrix (60+ Data Sources)

### 3.1 CeFi Exchanges (20+)

| Venue       | Trades | OrderBook | Ticker | Order  | Fill   | OHLCV | Fee            | Reference         | Liquidation | Derivative Ticker |
| ----------- | ------ | --------- | ------ | ------ | ------ | ----- | -------------- | ----------------- | ----------- | ----------------- |
| binance     | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | BinanceFeeRate | BinanceSymbol     | market+own  | ✓                 |
| bybit       | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | BybitFeeRate   | BybitMarket       | market+own  | ✓                 |
| okx         | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | OKXFeeRate     | OKXMarket         | market+own  | ✓                 |
| coinbase    | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | —              | —                 | —           | —                 |
| deribit     | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | fee in fill    | DeribitInstrument | market+own  | ✓                 |
| hyperliquid | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | —              | —                 | market+own  | ✓                 |
| upbit       | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | —              | —                 | —           | —                 |
| aster       | ✓      | ✓         | ✓      | ✓      | ✓      | ✓     | —              | —                 | —           | —                 |
| kraken      | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| kucoin      | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| gateio      | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| bitfinex    | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| bitstamp    | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| mexc        | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| huobi/htx   | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| bitget      | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | —                 |
| dydx        | schema | schema    | schema | schema | schema | —     | —              | —                 | —           | ✓                 |
| nautilus    | —      | —         | —      | ✓      | ✓      | —     | —              | —                 | —           | —                 |

### 3.2 Aggregators / Multi-Venue

| Provider  | Scope                                                                        | Notes                              |
| --------- | ---------------------------------------------------------------------------- | ---------------------------------- |
| ccxt      | CcxtTrade, CcxtOrder, CcxtOrderBook, CcxtTicker, CcxtFee                     | 100+ exchanges via unified adapter |
| tardis    | TardisTrade, TardisOrderBook, TardisTicker                                   | Historical; live via WebSocket     |
| databento | DatabentoOhlcvBar, Mbp1/10, Bbo1s/1m, Cmbp1, OptionQuote, Symbol, Definition | TradFi + CeFi feeds                |

### 3.3 TradFi

| Provider     | Scope                                                     | Notes                 |
| ------------ | --------------------------------------------------------- | --------------------- |
| ibkr         | IBKRTicker, IBKROrder, IBKRExecution, IBKRContractDetails | Gateway/API           |
| fix          | FIX ExecutionReport → Order/Fill, NewOrderSingle          | FIX protocol          |
| prime_broker | PrimeBrokerFill                                           | Prime brokerage fills |
| versifi      | VersiFi schemas                                           | If applicable         |

### 3.4 DeFi / On-Chain

| Provider  | Scope             | Notes                   |
| --------- | ----------------- | ----------------------- |
| alchemy   | RPC, logs, traces | EVM chains              |
| the_graph | Subgraph queries  | Indexed blockchain data |
| defillama | TVL, protocols    | —                       |
| pyth      | Oracle prices     | —                       |

### 3.5 Sports / Prediction Markets

| Provider   | Scope                     | Notes             |
| ---------- | ------------------------- | ----------------- |
| kalshi     | KalshiMarket, KalshiOrder | Prediction market |
| polymarket | PolymarketMarket, Order   | Prediction market |
| manifold   | ManifoldMarket            | Prediction market |
| predictit  | PredictItMarket           | Prediction market |
| betdaq     | BetdaqOdds, Order         | Exchange          |
| smarkets   | SmarketsOdds, Order       | Exchange          |
| pinnacle   | PinnacleOdds              | Bookmaker         |

### 3.6 Alt Data / Macro

| Provider  | Scope            | Notes        |
| --------- | ---------------- | ------------ |
| fred      | FRED series      | Macro        |
| ofr       | OFR bond data    | Bonds        |
| ecb       | ECB data         | FX, rates    |
| openbb    | OpenBB unified   | Multi-source |
| barchart  | Barchart data    | Commodities  |
| glassnode | On-chain metrics | —            |
| coingecko | Coin metadata    | —            |
| arkham    | Arkham intel     | —            |

---

## 4. Field-Level Mapping Rules

### 4.1 Common Field Mappings

| External Field                            | Canonical Field | Notes                      |
| ----------------------------------------- | --------------- | -------------------------- |
| `price` / `px` / `lastPrice`              | `price`         | Decimal                    |
| `size` / `qty` / `amount` / `volume`      | `size`          | Decimal                    |
| `symbol` / `instrument` / `pair`          | `symbol`        | Normalized (e.g. BTC-USDT) |
| `timestamp` / `ts` / `time` / `createdAt` | `timestamp`     | datetime UTC               |
| `side` / `direction`                      | `side`          | BUY/SELL                   |
| `orderId` / `order_id` / `clOrdId`        | `order_id`      | str                        |
| `tradeId` / `executionId` / `fillId`      | `fill_id`       | str                        |

### 4.2 Optional Fields (Proxy Pattern)

When provider lacks a field, use `None`. Document per-provider in `docs/SCHEMA_AUDIT_MATRIX.md` which fields are
populated.

### 4.3 Decimal and Timestamp

- All prices/sizes: `Decimal`
- All timestamps: `datetime` with `tzinfo=timezone.utc`

---

## 5. Normalizer Implementation Pattern

```python
# normalize/<category>.py
def normalize_<provider>_<schema>(raw: ExternalSchema, venue: str = "...", symbol: str = "") -> CanonicalType:
    """Convert <Provider><Schema> to <CanonicalType>. Live and batch produce identical output."""
    return CanonicalType(
        venue=venue or raw.venue,
        symbol=symbol or raw.symbol,
        # ... map every field; use None for missing
    )
```

- **No mode branching:** Normalizers are pure functions; no `if mode == "batch"`.
- **Thin adapters:** Normalizers only map fields; no business logic.

---

## 6. Matrix Generation Script

**Path:** `unified-api-contracts/scripts/generate_schema_audit_matrix.py`

**Inputs:**

- Scan `unified_api_contracts_external/<provider>/schemas.py` for all Pydantic models
- Scan `unified_normalised_contracts/normalize/*.py` for all `normalize_`\* functions
- Parse `domain.py` for all `Canonical`\* types

**Output:** `docs/SCHEMA_AUDIT_MATRIX.md`

**Format:**

| Provider | External Schema | Canonical Type | Normalizer              | Status |
| -------- | --------------- | -------------- | ----------------------- | ------ |
| binance  | BinanceTrade    | CanonicalTrade | normalize_binance_trade | Mapped |
| binance  | BinanceFeeRate  | CanonicalFee   | —                       | Gap    |

**Script logic:**

1. Discover all external schemas (Pydantic models in `*_external/**/schemas.py`)
2. Discover all normalizers (regex `def normalize_(\w+)_(\w+)`)
3. Match by naming convention: `normalize_<provider>_<schema_lower>` ↔ `<Provider><Schema>`
4. Output markdown table; flag gaps (schema exists, no normalizer)

**Run:** `python scripts/generate_schema_audit_matrix.py` (idempotent; overwrites matrix)

---

## 7. Live-Batch Symmetry Checklist

- Same `CanonicalTrade` from Tardis batch file vs Binance WebSocket
- Same `CanonicalOrderBook` from Databento MBP1 vs CCXT REST
- Same `CanonicalFill` from FIX ExecutionReport vs IBKR execution callback
- Timestamp normalization: epoch ms → UTC datetime in all paths
- Symbol normalization: `BTCUSDT` vs `BTC-USDT` vs `BTC/USDT` → single canonical form

---

## 8. References

| Doc          | Path                                                            | Purpose                    |
| ------------ | --------------------------------------------------------------- | -------------------------- |
| GAPS Audit   | `docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md`                       | Full gap list, remediation |
| Full Audit   | `docs/SCHEMA_NORMALIZATION_AUDIT_FULL.md`                       | Complete mapping table     |
| Audit Matrix | `docs/SCHEMA_AUDIT_MATRIX.md`                                   | Generated SSOT             |
| Rate Limits  | `docs/RATE_LIMIT_HANDLING_GAPS.md`                              | Rate limit normalization   |
| Codex        | `unified-trading-/codex/02-data/contracts-scope-and-layout.md`  | Architecture               |
| Codex        | `unified-trading-/codex/02-data/canonical-schema-groups.md`     | Canonical types            |
| Batch-Live   | `unified-trading-/codex/04-architecture/batch-live-symmetry.md` | Symmetry rules             |

---

## 9. Implementation Phases (Ordered)

1. **Phase 2a — Fees:** CanonicalFee + normalize for Binance, CCXT, Bybit, OKX, Deribit
2. **Phase 2b — Reference:** BinanceSymbol, BybitMarket, OKXMarket, CcxtMarket, DeribitInstrument, DatabentoSymbol,
   IBKRContractDetails → CanonicalMarketInfo/InstrumentRecord
3. **Phase 2c — Liquidations:** Market (public) + own (private) feeds per venue
4. **Phase 2d — Derivative Ticker:** Tardis, Binance, Deribit, Bybit, OKX, Hyperliquid → CanonicalDerivativeTicker
5. **Phase 2e — Options Chain:** Tardis, Deribit, Databento, Yahoo, IBKR → CanonicalOptionsChainEntry
6. **Phase 3a — Errors:** `normalize/errors.py` + taxonomy; `normalize_<provider>_error` for 50+ venues
7. **Phase 3b — Rate Limits:** Full implementation per RATE_LIMIT_HANDLING_GAPS.md
8. **Phase 4 — Sports:** 20+ bookmakers; kalshi, polymarket, manifold, predictit, betdaq, smarkets, pinnacle
9. **Phase 5 — Bonds/FX/Alt:** OFR, ECB, FRED, OpenBB, IBKR, barchart, glassnode, coingecko, arkham, pyth, defillama
10. **Phase 6 — Connectivity:** WebSocket lifecycle normalization; MarketState
11. **Matrix Script:** Enhance to cover all providers; run in CI
12. **UAC Coverage:** Tests ≥70%; all normalizers have unit tests

---

## 10. Validation

- `bash scripts/quality-gates.sh --no-fix` passes
- `timeout 120 basedpyright unified_api_contracts/` passes
- `pytest tests/` passes
- `python scripts/generate_schema_audit_matrix.py` produces matrix with 0 gaps (or documented exceptions)
