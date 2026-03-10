# UAC Exempt Class Adoption Plan

## Purpose

68 public classes defined in UAC core source (`schemas/` + `unified_normalised_contracts/`) are currently exempted from
the `check_uac_completeness.py` gate because no terminal consumer service imports them yet. This plan tracks their
adoption and promotion to `unified_api_contracts.__all__`.

**These are real, well-defined contracts** — they are exempt only because wiring is incomplete, not because they should
not exist. The end state is: every class below is imported by at least one terminal service, promoted to `__all__`, and
cleared from `EXEMPT_MISSING`.

Reference:

- Completeness checker: `unified-api-contracts/scripts/check_uac_completeness.py`
- SIT test: `system-integration-tests/tests/integration/test_uac_completeness.py`
- Adoption checker: `unified-api-contracts/scripts/check_uac_adoption.py`
- Adoption plan (separate): `orphan-uac-utilization.plan.md` (completed 2026-03-10)

---

## Group 1 — Analytics / Alternative Data (13 classes)

**File:** `unified_api_contracts/schemas/analytics.py` **Target services:** `pnl-attribution-service`,
`features-cross-instrument-service`

| Class                         | Purpose                         | Target                            |
| ----------------------------- | ------------------------------- | --------------------------------- |
| `FactorType`                  | Enum — factor model category    | pnl-attribution-service           |
| `AlternativeDataType`         | Enum — alt-data signal category | features-cross-instrument-service |
| `CorrelationRegime`           | Enum — correlation state        | features-cross-instrument-service |
| `FactorExposure`              | Per-factor beta + vol           | pnl-attribution-service           |
| `FactorAttributionRecord`     | Factor P&L decomposition record | pnl-attribution-service           |
| `FactorAttributionModel`      | Full factor attribution model   | pnl-attribution-service           |
| `CrossAssetCorrelationMatrix` | Correlation matrix snapshot     | features-cross-instrument-service |
| `CorrelationRegimeChange`     | Regime change event             | features-cross-instrument-service |
| `SentimentScore`              | NLP/sentiment alt-data signal   | features-cross-instrument-service |
| `SatelliteObservation`        | Satellite imagery alt-data      | features-cross-instrument-service |
| `OptionsFlowRecord`           | Options dark-pool flow record   | features-volatility-service       |
| `DarkPoolPrintRecord`         | Dark pool print                 | market-data-processing-service    |
| `AlternativeDataSignal`       | Composite alt-data signal       | features-cross-instrument-service |

**Promotion steps:**

1. Wire `FactorType`, `FactorExposure`, `FactorAttributionRecord`, `FactorAttributionModel` into
   `pnl-attribution-service/pnl_attribution_service/models.py`
2. Wire remaining 9 classes into `features-cross-instrument-service` and `features-volatility-service`
3. Remove from `EXEMPT_MISSING` in `check_uac_completeness.py` and `_UAC_EXEMPT` in `test_uac_completeness.py`
4. Add to `unified_api_contracts/__init__.py` `__all__`
5. Run `check_uac_adoption.py` to confirm 0 new orphans

---

## Group 2 — CEX Withdrawals (10 classes)

**File:** `unified_api_contracts/schemas/cex_withdrawals.py` **Target service:** `execution-service` (venue adapter
layer)

| Class                                                  | Venue    |
| ------------------------------------------------------ | -------- |
| `BinanceWithdrawRequest` / `BinanceWithdrawResponse`   | Binance  |
| `OKXWithdrawRequest` / `OKXWithdrawResponse`           | OKX      |
| `BybitWithdrawRequest` / `BybitWithdrawResponse`       | Bybit    |
| `UpbitWithdrawRequest` / `UpbitWithdrawResponse`       | Upbit    |
| `CoinbaseWithdrawRequest` / `CoinbaseWithdrawResponse` | Coinbase |

**Promotion steps:**

1. Wire all 10 into `execution-service/execution_service/adapters/` or `models.py` as type references
2. Remove from `EXEMPT_MISSING` / `_UAC_EXEMPT`
3. Add to UAC `__all__`
4. Run adoption check

---

## Group 3 — Latency Metrics (8 classes)

**File:** `unified_api_contracts/schemas/latency.py` **Target service:** `execution-service` (latency monitoring
subsystem)

| Class                         | Purpose                         |
| ----------------------------- | ------------------------------- |
| `LatencyComponent`            | Enum — latency pipeline stage   |
| `LatencyPercentile`           | p50/p95/p99 latency snapshot    |
| `TickToTradeMetric`           | End-to-end tick-to-trade timing |
| `OrderLatencyRecord`          | Per-order latency breakdown     |
| `CoLocationPerformanceMetric` | Co-lo HW performance            |
| `NetworkJitterMetric`         | Network jitter measurement      |
| `SubMillisecondLatencyRecord` | <1ms precision record           |
| `LatencyBenchmarkReport`      | Aggregated benchmark summary    |

**Promotion steps:**

1. Wire into `execution-service/execution_service/metrics/` or `models.py`
2. Remove from exempt lists, add to UAC `__all__`, run adoption check

---

## Group 4 — Prediction Market Arb (9 classes)

**File:** `unified_api_contracts/schemas/prediction_market_arb.py` **Target service:** `features-sports-service` (arb
signal pipeline)

| Class                      | Purpose                           |
| -------------------------- | --------------------------------- |
| `CrossVenueLink`           | Polymarket ↔ Betfair market link |
| `BucketMarket`             | Probability-bucket market         |
| `ProbabilityBucket`        | Bucket definition                 |
| `SportsbookLink`           | Sportsbook market link            |
| `NegRiskBucket`            | Polymarket neg-risk bucket        |
| `NegRiskArbSignal`         | Neg-risk arb opportunity          |
| `CrossVenueArbLeg`         | Single arb leg                    |
| `CrossVenueArbSignal`      | Full cross-venue arb signal       |
| `PredictionMarketUniverse` | Full market universe snapshot     |

**Promotion steps:**

1. Wire into `features-sports-service/features_sports_service/schemas/output_schemas.py`
2. Remove from exempt lists, add to UAC `__all__`, run adoption check

---

## Group 5 — Protocol SDK Action Params (19 classes)

**File:** `unified_api_contracts/schemas/protocol_sdks.py` **Target service:** `features-onchain-service` (DeFi
execution layer)

Action parameter types (send-side only — response types already in `__all__`):

| Classes                                                                                  | Protocol |
| ---------------------------------------------------------------------------------------- | -------- |
| `AaveDepositParams`, `AaveBorrowParams`, `AaveRepayParams`, `AaveFlashLoanParams`        | Aave     |
| `MorphoSupplyParams`, `MorphoBorrowParams`, `MorphoRepayParams`, `MorphoFlashLoanParams` | Morpho   |
| `EulerDepositParams`, `EulerBorrowParams`, `EulerRepayParams`                            | Euler    |
| `FluidDepositParams`, `FluidBorrowParams`, `FluidRepayParams`                            | Fluid    |
| `LidoSubmitParams`, `LidoRequestWithdrawalsParams`                                       | Lido     |
| `CurveDepositParams`, `CurveWithdrawParams`, `CurveSwapParams`                           | Curve    |

**Promotion steps:**

1. Wire all 19 into `features-onchain-service/features_onchain_service/models.py` (alongside existing response-type
   references)
2. Remove from exempt lists, add to UAC `__all__`, run adoption check

---

## Group 6 — Rate Limits (2 classes)

**File:** `unified_api_contracts/schemas/rate_limits.py` **Target service:** `unified-market-interface` (adapter layer)

| Class                  | Purpose                            |
| ---------------------- | ---------------------------------- |
| `HttpRateLimitHeaders` | Parsed HTTP 429 rate-limit headers |
| `VenueRateLimitSpec`   | Per-venue rate-limit configuration |

**Promotion steps:**

1. Wire into `unified-market-interface` adapters as type references
2. Remove from exempt lists, add to UAC `__all__`, run adoption check

---

## Group 7 — Ethereum Transfers (6 classes)

**File:** `unified_api_contracts/schemas/transfers.py` **Target service:** `features-onchain-service` (onchain transfer
layer)

| Class                           | Purpose                         |
| ------------------------------- | ------------------------------- |
| `EthSendRawTransactionRequest`  | Raw signed tx submission        |
| `EthSendRawTransactionResponse` | Tx hash response                |
| `EthTransactionRequest`         | Unsigned tx parameter set       |
| `EthSendTransactionRequest`     | Signed tx submission            |
| `Erc20TransferCalldata`         | ERC20 `transfer()` calldata     |
| `Erc20TransferFromCalldata`     | ERC20 `transferFrom()` calldata |

**Promotion steps:**

1. Wire into `features-onchain-service/features_onchain_service/models.py`
2. Remove from exempt lists, add to UAC `__all__`, run adoption check

---

## Group 8 — WebSocket Internal (1 class)

**File:** `unified_api_contracts/schemas/websocket.py` **Target service:** `unified-market-interface` (WS health layer)

| Class                | Purpose                             |
| -------------------- | ----------------------------------- |
| `HealthPingResponse` | Server-side WS health ping sentinel |

**Promotion steps:**

1. Wire into `unified-market-interface`
2. Remove from exempt lists, add to UAC `__all__`, run adoption check

---

## Promotion Sequencing

Suggested order (highest value / lowest effort first):

1. **Group 5** (protocol SDK params) — features-onchain-service already imports response types; adding params is
   low-effort and completes the DeFi action contract surface
2. **Group 7** (ETH transfers) — same service, same pattern
3. **Group 4** (prediction market arb) — features-sports-service already imports sports UAC types; natural extension
4. **Group 2** (CEX withdrawals) — execution-service has venue adapters; adds per-venue withdraw surface
5. **Group 3** (latency) — execution-service; adds latency monitoring surface
6. **Group 6** (rate limits) — UMI adapter layer; small, self-contained
7. **Group 1** (analytics) — requires pnl-attribution-service and features-cross-instrument-service wiring; most complex
8. **Group 8** (WS health) — UMI WS layer; minimal change

---

## Completion Criteria

- [ ] All 68 classes removed from `EXEMPT_MISSING` in `check_uac_completeness.py`
- [ ] All 68 classes removed from `_UAC_EXEMPT` in `test_uac_completeness.py`
- [ ] All 68 classes added to `unified_api_contracts/__init__.py` `__all__`
- [ ] `check_uac_adoption.py` exits 0 (all newly promoted classes have ≥1 importer)
- [ ] `test_uac_completeness_no_gaps` passes in SIT with no mock/skip

## Status

Created: 2026-03-10 Status: Active — not yet started
