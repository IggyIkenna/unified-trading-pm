# UAC Exempt Class Adoption Plan

## Purpose

68 public classes defined in UAC core source (`schemas/` + `unified_normalised_contracts/`) are currently exempted from
the `check_uac_completeness.py` gate because no terminal consumer service imports them yet. This plan tracks their
adoption and promotion to `unified_api_contracts.__all__`.

**These are real, well-defined contracts** — they are exempt only because wiring is incomplete, not because they should
not exist. The end state is: every class below is imported by **every service that logically needs it**, promoted to
`__all__`, and cleared from `EXEMPT_MISSING`.

Adoption means **correct multi-service wiring** — not just a single reference. Each group lists all critical, strong,
and medium consumers. A group is complete only when all critical consumers are wired, adoption check exits 0.

Reference:

- Completeness checker: `unified-api-contracts/scripts/check_uac_completeness.py`
- SIT test: `system-integration-tests/tests/integration/test_uac_completeness.py`
- Adoption checker: `unified-api-contracts/scripts/check_uac_adoption.py`
- Adoption plan (separate): `orphan-uac-utilization.plan.md` (completed 2026-03-10)

---

## Group 1 — Analytics / Alternative Data (13 classes)

**File:** `unified_api_contracts/schemas/analytics.py`

| Class                         | Purpose                                             |
| ----------------------------- | --------------------------------------------------- |
| `FactorType`                  | Enum — factor model category                        |
| `AlternativeDataType`         | Enum — alt-data signal category                     |
| `CorrelationRegime`           | Enum — correlation state (low/normal/stress/crisis) |
| `FactorExposure`              | Per-factor beta + vol contribution                  |
| `FactorAttributionRecord`     | Single-period factor P&L decomposition              |
| `FactorAttributionModel`      | Full multi-factor attribution model                 |
| `CrossAssetCorrelationMatrix` | Snapshot correlation matrix across assets           |
| `CorrelationRegimeChange`     | Regime transition event                             |
| `SentimentScore`              | NLP/sentiment alt-data signal                       |
| `SatelliteObservation`        | Satellite imagery alt-data record                   |
| `OptionsFlowRecord`           | Dark-pool options flow record                       |
| `DarkPoolPrintRecord`         | Dark pool equity print                              |
| `AlternativeDataSignal`       | Composite alt-data signal output                    |

### Target Consumers

**CRITICAL — already has active attribution/correlation/analytics code:**

- `pnl-attribution-service` — `engine/types.py`, `analytics/`, `execution_alpha/calculator.py` have local factor
  attribution types; must migrate to `FactorType`, `FactorExposure`, `FactorAttributionRecord`, `FactorAttributionModel`
- `features-cross-instrument-service` — `regime_calculator.py`, `cross_asset_correlation.py`,
  `polymarket_crowd_sentiment_calculator.py`; must consume `CorrelationRegime`, `CorrelationRegimeChange`,
  `CrossAssetCorrelationMatrix`, `SentimentScore`, `AlternativeDataSignal`, `AlternativeDataType`
- `strategy-service` — `pnl_monitor.py`, `execution_alpha`; consumes attribution outputs for multi-factor strategy
  selection; must consume `FactorAttributionRecord`, `FactorExposure`

**STRONG — clear domain match:**

- `market-data-processing-service` — processes risk parameter and alternative data feeds; should consume
  `DarkPoolPrintRecord`, `OptionsFlowRecord`, `SatelliteObservation`, `AlternativeDataType`
- `features-volatility-service` — regime-aware vol surface models; should consume `CorrelationRegime`,
  `CorrelationRegimeChange` for cross-asset vol context
- `trading-analytics-api` — exposes analytics to UI layer; should return `FactorAttributionModel`, `SentimentScore`,
  `AlternativeDataSignal` in API responses

**MEDIUM — should consider:**

- `ml-inference-service` — ingests feature vectors that may include `SentimentScore`, `AlternativeDataSignal` as inputs
  to ML models
- `ml-training-service` — trains on historical `FactorAttributionRecord` and `AlternativeDataSignal` sequences

### Promotion Steps

1. Wire CRITICAL consumers (`pnl-attribution-service`, `features-cross-instrument-service`, `strategy-service`)
2. Wire STRONG consumers
3. Remove 13 classes from `EXEMPT_MISSING` in `check_uac_completeness.py` and `_UAC_EXEMPT` in
   `test_uac_completeness.py`
4. Add all 13 to `unified_api_contracts/__init__.py` `__all__`
5. Run `check_uac_adoption.py` → all 13 must have ≥1 importer (adoption gate)

---

## Group 2 — CEX Withdrawals (10 classes)

**File:** `unified_api_contracts/schemas/cex_withdrawals.py`

| Class                                                  | Venue    |
| ------------------------------------------------------ | -------- |
| `BinanceWithdrawRequest` / `BinanceWithdrawResponse`   | Binance  |
| `OKXWithdrawRequest` / `OKXWithdrawResponse`           | OKX      |
| `BybitWithdrawRequest` / `BybitWithdrawResponse`       | Bybit    |
| `UpbitWithdrawRequest` / `UpbitWithdrawResponse`       | Upbit    |
| `CoinbaseWithdrawRequest` / `CoinbaseWithdrawResponse` | Coinbase |

### Target Consumers

**CRITICAL — already implements withdrawal logic:**

- `execution-service` — `transfer_handler.py` has `CEX_VENUES: [BINANCE, BYBIT, OKX, COINBASE]` and explicit withdraw
  flow; must migrate to venue-typed `BinanceWithdrawRequest`, `OKXWithdrawRequest`, `BybitWithdrawRequest`,
  `CoinbaseWithdrawRequest` schemas

**STRONG — withdrawal events affect their state:**

- `risk-and-exposure-service` — withdrawal events change net exposure; should consume withdrawal response types to
  trigger re-computation of position snapshots
- `position-balance-monitor-service` — cash/token balances change on withdrawal completion; should consume all
  `*WithdrawResponse` types for balance state updates

**MEDIUM — venue configuration layer:**

- `instruments-service` — may need to track venue-specific withdrawal limits, fees, and network config by venue

### Promotion Steps

1. Wire `execution-service` (CRITICAL)
2. Wire `risk-and-exposure-service`, `position-balance-monitor-service` (STRONG)
3. Remove 10 classes from exempt lists, add to `__all__`, run adoption check

---

## Group 3 — Latency Metrics (8 classes)

**File:** `unified_api_contracts/schemas/latency.py`

| Class                         | Purpose                                                          |
| ----------------------------- | ---------------------------------------------------------------- |
| `LatencyComponent`            | Enum — pipeline stage (tick-recv, order-submit, fill-recv, etc.) |
| `LatencyPercentile`           | p50/p95/p99/p999 latency snapshot                                |
| `TickToTradeMetric`           | End-to-end tick-to-trade timing                                  |
| `OrderLatencyRecord`          | Per-order latency breakdown by component                         |
| `CoLocationPerformanceMetric` | Co-location hardware performance metric                          |
| `NetworkJitterMetric`         | Network jitter + packet loss measurement                         |
| `SubMillisecondLatencyRecord` | Sub-millisecond precision record                                 |
| `LatencyBenchmarkReport`      | Aggregated benchmark summary across runs                         |

### Target Consumers

**CRITICAL — actively instruments latency:**

- `execution-service` — 171 files with latency patterns; `benchmark/` directory, `metrics.py`, scattered latency
  calculations; must migrate to `TickToTradeMetric`, `OrderLatencyRecord`, `CoLocationPerformanceMetric`,
  `SubMillisecondLatencyRecord`
- `market-tick-data-service` — 28 files; `models.py`, `metrics.py` track data feed latency; should consume
  `NetworkJitterMetric`, `SubMillisecondLatencyRecord`, `LatencyPercentile` for stream health reporting

**STRONG — consumes or routes latency outputs:**

- `pnl-attribution-service` — `execution_alpha/calculator.py` correlates slippage to latency; should consume
  `OrderLatencyRecord`, `TickToTradeMetric` for execution cost attribution
- `alerting-service` — should trigger alerts when `LatencyPercentile` thresholds are breached; consumes
  `LatencyBenchmarkReport` for degradation detection
- `unified-market-interface` — WebSocket manager; should track per-connection `NetworkJitterMetric`, `LatencyPercentile`
  for adaptive stream management

**MEDIUM — reporting layer:**

- `trading-analytics-api` — exposes latency dashboards to UI; should return `LatencyBenchmarkReport`,
  `LatencyPercentile` in analytics API responses

### Promotion Steps

1. Wire `execution-service`, `market-tick-data-service` (CRITICAL)
2. Wire `pnl-attribution-service`, `alerting-service`, `unified-market-interface` (STRONG)
3. Remove 8 classes from exempt lists, add to `__all__`, run adoption check

---

## Group 4 — Prediction Market Arb (9 classes)

**File:** `unified_api_contracts/schemas/prediction_market_arb.py`

| Class                      | Purpose                                      |
| -------------------------- | -------------------------------------------- |
| `CrossVenueLink`           | Polymarket ↔ Betfair market link            |
| `BucketMarket`             | Probability-bucket market definition         |
| `ProbabilityBucket`        | Bucket membership and probability range      |
| `SportsbookLink`           | Sportsbook market link + odds type           |
| `NegRiskBucket`            | Polymarket neg-risk bucket definition        |
| `NegRiskArbSignal`         | Neg-risk arbitrage opportunity               |
| `CrossVenueArbLeg`         | Single leg of a cross-venue arb              |
| `CrossVenueArbSignal`      | Full cross-venue arb signal with all legs    |
| `PredictionMarketUniverse` | Complete prediction market universe snapshot |

### Target Consumers

**CRITICAL — actively implements prediction market arb:**

- `strategy-service` — `prediction_arb/prediction_arb_strategy.py` (Polymarket, Kalshi, Betfair arb),
  `sports/arbitrage.py`; has local `PredictionArbSignal`, `PredictionArbLeg` types; must migrate to
  `CrossVenueArbSignal`, `CrossVenueArbLeg`, `NegRiskArbSignal`, `NegRiskBucket`
- `features-sports-service` — `arb/vig.py`, cross-sportsbook signal calculators; must consume `SportsbookLink`,
  `NegRiskBucket`, `NegRiskArbSignal`, `CrossVenueLink`, `PredictionMarketUniverse`
- `unified-sports-execution-interface` — `prediction_markets/polymarket.py`, `prediction_markets/kalshi.py`,
  `adapters/exchanges/betfair.py`; venue routing requires `CrossVenueLink`, `BucketMarket`, `ProbabilityBucket`,
  `SportsbookLink`

**STRONG — routes or manages arb positions:**

- `execution-service` — `sports/router.py`, `sports/factory.py` route multi-leg sports/prediction orders; should consume
  `CrossVenueArbSignal` to execute multi-leg positions atomically
- `risk-and-exposure-service` — prediction market positions have neg-risk accounting; should consume `NegRiskBucket` for
  correct exposure calculation on Polymarket

### Promotion Steps

1. Wire `strategy-service`, `features-sports-service`, `unified-sports-execution-interface` (CRITICAL)
2. Wire `execution-service`, `risk-and-exposure-service` (STRONG)
3. Remove 9 classes from exempt lists, add to `__all__`, run adoption check

---

## Group 5 — Protocol SDK Action Params (19 classes)

**File:** `unified_api_contracts/schemas/protocol_sdks.py`

Action parameter types (send-side — response types already in `__all__`):

| Classes                                                                                  | Protocol |
| ---------------------------------------------------------------------------------------- | -------- |
| `AaveDepositParams`, `AaveBorrowParams`, `AaveRepayParams`, `AaveFlashLoanParams`        | Aave     |
| `MorphoSupplyParams`, `MorphoBorrowParams`, `MorphoRepayParams`, `MorphoFlashLoanParams` | Morpho   |
| `EulerDepositParams`, `EulerBorrowParams`, `EulerRepayParams`                            | Euler    |
| `FluidDepositParams`, `FluidBorrowParams`, `FluidRepayParams`                            | Fluid    |
| `LidoSubmitParams`, `LidoRequestWithdrawalsParams`                                       | Lido     |
| `CurveDepositParams`, `CurveWithdrawParams`, `CurveSwapParams`                           | Curve    |

### Target Consumers

**CRITICAL — actively implements protocol connectors:**

- `execution-service` — 149 files; `venues/aave.py`, `venues/morpho.py`, `venues/lido.py`, `handlers/lend_handler.py`,
  `handlers/borrow_handler.py`, `handlers/stake_handler.py`, `handlers/swap_handler.py`, `flash_loan_handler.py`;
  already imports `AaveV3ReserveData` from UAC; must add `AaveDepositParams`, `AaveBorrowParams`, `AaveRepayParams`,
  `AaveFlashLoanParams`, `MorphoSupplyParams`, `MorphoBorrowParams`, `LidoSubmitParams`, `CurveSwapParams`, etc.
- `unified-defi-execution-interface` — 27 files; `protocols/aave.py`, `protocols/morpho.py`, `protocols/lido.py`,
  `protocols/etherfi.py`; wraps protocol interactions; must consume the full set of action param classes for typed
  instruction building

**STRONG — computes or routes DeFi actions:**

- `features-onchain-service` — `onchain_orchestration.py`, `dex_swap_adapter.py`; should consume `CurveDepositParams`,
  `CurveSwapParams` for feature engineering from DeFi strategy outputs
- `strategy-service` — `defi_basis.py`, `defi_lending.py`, `defi_staked_basis.py`; should consume `AaveDepositParams`,
  `MorphoSupplyParams`, `LidoSubmitParams` for instruction generation

**MEDIUM — position validation layer:**

- `risk-and-exposure-service` — tracks on-chain collateral/debt positions; should consume protocol param schemas to
  validate collateral ratios and debt exposure bounds

### Promotion Steps

1. Wire `execution-service`, `unified-defi-execution-interface` (CRITICAL)
2. Wire `features-onchain-service`, `strategy-service` (STRONG)
3. Remove 19 classes from exempt lists, add to `__all__`, run adoption check

---

## Group 6 — Rate Limits (2 classes)

**File:** `unified_api_contracts/schemas/rate_limits.py`

| Class                  | Purpose                                                  |
| ---------------------- | -------------------------------------------------------- |
| `HttpRateLimitHeaders` | Parsed HTTP 429 / rate-limit response headers            |
| `VenueRateLimitSpec`   | Per-venue rate-limit configuration (weight/burst/window) |

### Target Consumers

**CRITICAL — already implements rate limit infrastructure:**

- `unified-market-interface` — 45 files; `connectivity/rate_limiter.py`, `VenueRateLimiter`; must formalize via
  `HttpRateLimitHeaders` + `VenueRateLimitSpec` UAC schemas
- `unified-trade-execution-interface` — 9 files; Bybit, OKX, Deribit, Binance, Coinbase, Hyperliquid adapters all handle
  venue rate limits; must consume `HttpRateLimitHeaders`, `VenueRateLimitSpec`
- `market-tick-data-service` — 18 files; per-provider configs track rate limits; must consume `VenueRateLimitSpec` for
  dynamic throttling

**STRONG — rate limits affect their correctness:**

- `unified-sports-execution-interface` — `odds_api.py`, `api_football.py`, `pinnacle.py`, `smarkets.py`; sports data
  feeds have strict rate limits; should consume `VenueRateLimitSpec`
- `execution-service` — kline/async data fetching; `VenueRateLimitSpec` for backtest data loading rate management
- `instruments-service` — `ccxt_service.py` fetches instrument data from venues; should respect `VenueRateLimitSpec` per
  venue

**MEDIUM — client-side rate limiting:**

- `trading-analytics-api` — may expose `HttpRateLimitHeaders` in API responses to inform clients about throttling state

### Promotion Steps

1. Wire `unified-market-interface`, `unified-trade-execution-interface`, `market-tick-data-service` (CRITICAL)
2. Wire `unified-sports-execution-interface`, `execution-service`, `instruments-service` (STRONG)
3. Remove 2 classes from exempt lists, add to `__all__`, run adoption check

---

## Group 7 — Ethereum Transfers (6 classes)

**File:** `unified_api_contracts/schemas/transfers.py`

| Class                           | Purpose                            |
| ------------------------------- | ---------------------------------- |
| `EthSendRawTransactionRequest`  | Raw signed transaction submission  |
| `EthSendRawTransactionResponse` | Transaction hash + status response |
| `EthTransactionRequest`         | Unsigned transaction parameter set |
| `EthSendTransactionRequest`     | Signed transaction submission      |
| `Erc20TransferCalldata`         | ERC20 `transfer()` calldata        |
| `Erc20TransferFromCalldata`     | ERC20 `transferFrom()` calldata    |

### Target Consumers

**CRITICAL — actively handles on-chain transfers:**

- `execution-service` — `transfer_handler.py` explicitly handles "CEX → on-chain (withdrawal)" and "wallet → wallet
  (on-chain transfer)"; `gas_cost_model.py` calculates transaction costs; must consume `EthTransactionRequest`,
  `EthSendTransactionRequest`, `Erc20TransferCalldata`, `Erc20TransferFromCalldata`, `EthSendRawTransactionRequest`,
  `EthSendRawTransactionResponse`

**STRONG — builds or executes on-chain calldata:**

- `unified-defi-execution-interface` — `protocols/*.py` build transaction calldata for on-chain protocol interactions
  (Aave, Morpho, Lido deposits/borrows use ERC20 transferFrom internally); should consume `Erc20TransferCalldata`,
  `Erc20TransferFromCalldata`, `EthSendRawTransactionRequest/Response`
- `features-onchain-service` — transaction simulation and feature extraction; should consume `EthTransactionRequest` for
  simulating on-chain strategy actions

**MEDIUM — strategy instruction layer:**

- `strategy-service` — DeFi multi-leg strategies build transaction sequences; should consume `EthSendTransactionRequest`
  for instruction generation in DeFi strategies

### Promotion Steps

1. Wire `execution-service` (CRITICAL)
2. Wire `unified-defi-execution-interface`, `features-onchain-service` (STRONG)
3. Remove 6 classes from exempt lists, add to `__all__`, run adoption check

---

## Group 8 — WebSocket Internal (1 class)

**File:** `unified_api_contracts/schemas/websocket.py`

| Class                | Purpose                                    |
| -------------------- | ------------------------------------------ |
| `HealthPingResponse` | Server-side WebSocket health ping sentinel |

### Target Consumers

**CRITICAL — owns WebSocket connection management:**

- `unified-market-interface` — `websocket/manager.py` manages long-lived WS connections to all venues; must consume
  `HealthPingResponse` for internal ping/pong health protocol

**STRONG — streams data or orders over WebSocket:**

- `market-tick-data-service` — ingests streaming market data via WebSocket (tardis, databento); should consume
  `HealthPingResponse` for stream health checks
- `unified-trade-execution-interface` — live order streaming via CEX WebSocket APIs; should consume `HealthPingResponse`
  for connection health monitoring
- `unified-sports-execution-interface` — sports market data streams over WebSocket; should consume `HealthPingResponse`
  for stream health signaling

**MEDIUM — monitors stream health:**

- `execution-service` — subscribes to venue order-update and fill WebSocket streams; should consume `HealthPingResponse`
  for connection monitoring
- `alerting-service` — monitors service health; should emit alerts when WebSocket streams stop responding to
  `HealthPingResponse` within threshold

### Promotion Steps

1. Wire `unified-market-interface` (CRITICAL)
2. Wire `market-tick-data-service`, `unified-trade-execution-interface`, `unified-sports-execution-interface` (STRONG)
3. Remove `HealthPingResponse` from exempt lists, add to `__all__`, run adoption check

---

## Cross-Service Summary

| Service                            | G1       | G2       | G3       | G4       | G5       | G6       | G7       | G8       |
| ---------------------------------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- |
| execution-service                  | STRONG   | CRITICAL | CRITICAL | STRONG   | CRITICAL | STRONG   | CRITICAL | MEDIUM   |
| unified-defi-execution-interface   | —        | —        | —        | —        | CRITICAL | —        | STRONG   | —        |
| unified-sports-execution-interface | —        | —        | —        | CRITICAL | —        | STRONG   | —        | STRONG   |
| unified-market-interface           | —        | —        | STRONG   | —        | —        | CRITICAL | —        | CRITICAL |
| unified-trade-execution-interface  | —        | —        | —        | —        | —        | CRITICAL | —        | STRONG   |
| strategy-service                   | STRONG   | —        | —        | CRITICAL | STRONG   | —        | MEDIUM   | —        |
| pnl-attribution-service            | CRITICAL | —        | STRONG   | —        | —        | —        | —        | —        |
| features-cross-instrument-service  | CRITICAL | —        | —        | —        | —        | —        | —        | —        |
| features-sports-service            | —        | —        | —        | CRITICAL | —        | —        | —        | —        |
| features-onchain-service           | —        | —        | —        | —        | STRONG   | —        | STRONG   | —        |
| market-tick-data-service           | —        | —        | CRITICAL | —        | —        | CRITICAL | —        | STRONG   |
| market-data-processing-service     | STRONG   | —        | —        | —        | —        | —        | —        | —        |
| risk-and-exposure-service          | —        | STRONG   | —        | STRONG   | MEDIUM   | —        | —        | —        |
| position-balance-monitor-service   | —        | STRONG   | —        | —        | —        | —        | —        | —        |
| alerting-service                   | —        | —        | STRONG   | —        | —        | —        | —        | MEDIUM   |
| trading-analytics-api              | STRONG   | —        | MEDIUM   | —        | —        | MEDIUM   | —        | —        |
| ml-inference-service               | MEDIUM   | —        | —        | —        | —        | —        | —        | —        |
| ml-training-service                | MEDIUM   | —        | —        | —        | —        | —        | —        | —        |

---

## Promotion Sequencing

Suggested order — lowest effort + most CRITICAL consumers first:

1. **Group 5** (19 protocol SDK params) — `execution-service` + `unified-defi-execution-interface` have 150+ files
   actively implementing these; natural schema migration
2. **Group 7** (6 ETH transfers) — `execution-service` `transfer_handler.py` directly implements these; same service
   batch
3. **Group 6** (2 rate limits) — `unified-market-interface` + `unified-trade-execution-interface` already have rate
   limit infrastructure; formalizing is low-effort
4. **Group 4** (9 prediction market arb) — `strategy-service` + `features-sports-service` +
   `unified-sports-execution-interface` all have active arb code
5. **Group 2** (10 CEX withdrawals) — `execution-service` `transfer_handler.py` already has the withdraw flow; add
   STRONG consumers
6. **Group 8** (1 WS health) — `unified-market-interface` is the primary owner; small change
7. **Group 3** (8 latency metrics) — `execution-service` + `market-tick-data-service` have latency instrumentation;
   requires broader adoption across alerting + pnl
8. **Group 1** (13 analytics) — most complex; requires coordinating `pnl-attribution-service`,
   `features-cross-instrument-service`, `strategy-service`, `market-data-processing-service`

---

## Completion Criteria

- [x] All 68 classes removed from `EXEMPT_MISSING` in `check_uac_completeness.py` — **done 2026-03-10**
- [x] All 68 classes removed from `_UAC_EXEMPT` in `test_uac_completeness.py` — **done 2026-03-10**
- [x] All 68 classes added to `unified_api_contracts/__init__.py` `__all__` — **done 2026-03-10**
- [x] All CRITICAL consumer services have import wiring — **done 2026-03-10**
- [x] All STRONG consumer services have import wiring — **done 2026-03-10**
- [x] `check_uac_adoption.py` exits 0 (all newly promoted classes have ≥1 importer)
- [x] `test_uac_completeness_no_gaps` passes in SIT with no mock/skip

## UAC Completeness Achievement (2026-03-10)

UAC `__all__` grew from **166 → 329 entries** across three commits:

| Commit    | Change                                        | `__all__` size |
| --------- | --------------------------------------------- | -------------- |
| `5384a0e` | +68 specialty classes (G1–G8 groups)          | 234            |
| `7cd753b` | Narrow `EXEMPT_MISSING` to 14 (internal only) | 234            |
| `38b58cd` | +95 core classes (domain, errors, execution)  | 329            |

`check_uac_completeness.py` now exits 0: **224 defined, 14 exempt, 0 missing**.

All 18 terminal consumer services wired with appropriate UAC specialty type imports.

## Status

Created: 2026-03-10 **Completed: 2026-03-10** — all groups wired, completeness gate clean, adoption matrix regenerated.
