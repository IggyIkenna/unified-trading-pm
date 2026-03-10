# Plan: UAC Orphan Contracts Utilization

## Status: Active

## Created: 2026-03-10

## Source: check_uac_adoption.py --orphans-only (86 schemas, no terminal consumer importer)

These 86 schemas are in UAC `__all__` and have clear intended consumers but are not yet explicitly imported by any of
the 20 scanned repos (18 terminal services + UMI + USEI).

---

## Group A: features-onchain-service (17 — DeFi protocol schemas)

- `AaveV3ReserveData`, `AaveV3UserAccountData`, `AaveV3UserReserveData`
- `CompoundV3MarketInfo`, `CompoundV3UserPosition`
- `EtherFiStakeResponse`, `EtherFiUnstakeResponse`
- `EulerUserPosition`, `EulerVaultData`
- `LidoSubmitResponse`, `LidoWstEthWrapResponse`
- `MorphoMarketParams`, `MorphoUserPosition`
- `UniswapV3PoolStateResponse`, `UniswapV3QuoteResponse`, `UniswapV3SwapTxReceipt`
- `PolymarketPosition`

**Action:** Import in `features_onchain_service/models.py` or data normalizer.

---

## Group B: features-sports-service (19 — sports/betting canonical + error types)

- `CanonicalBookmakerMarket`, `CanonicalComboBet`, `CanonicalComboLeg`
- `CanonicalFixture`, `CanonicalLeague`, `CanonicalPlayer`, `CanonicalReferee`, `CanonicalTeam`, `CanonicalVenue`
- `BetfairCurrentOrderSummary`, `BetfairListCurrentOrdersResponse`, `BetfairRunnerCatalog`
- `BookmakerCategory`, `BookmakerRegistry`
- `BettingSignal`
- `SportsError`, `FixtureNotFoundError`, `MarketClosedError`, `OddsChangedError`

**Action:** Import in `features_sports_service/schemas/output_schemas.py` or models layer.

---

## Group C: instruments-service (24 — venue exchange API + reference schemas)

- `BinanceFuturesExchangeInfo`, `BinanceInstrumentInfo`, `BinanceOptionInstrumentInfo`
- `BybitInstrumentInfo`, `BybitInstrumentsResponse`
- `CoinbaseProductInfo`, `CoinbaseProductsResponse`
- `OKXInstrumentInfo`, `OKXInstrumentsResponse`
- `DeribitGetInstrumentResponse`, `DeribitGetInstrumentsResponse`, `DeribitInstrumentInfoFull`
- `HyperliquidAssetInfo`, `HyperliquidMeta`
- `IBKRAccountValue`, `IBKRCorporateAction`
- `TardisExchangeDetail`, `TardisInstrumentDetail`
- `DatabentoReferenceInstrument`, `DatabentoError`
- `PolygonTicker`, `PolygonTickersResponse`
- `PolygonOptionContract`, `PolygonOptionContractsResponse`

**Action:** Import in `instruments_service/adapters/` or reference layer (prefer existing adapter files that use UAC).

---

## Group D: execution-service (9 — order/options/spread schemas)

- `CanonicalFill`
- `CanonicalOrderAmendment`, `CanonicalOrderRejection`
- `CanonicalSettlement`
- `CanonicalSpread`, `SpreadLeg`
- `OptionContract`, `OptionGreeks`
- `SettlementPrice`

**Action:** Import in `execution_service/engine/` or `execution_service/publishers/`.

---

## Group E: risk-and-exposure-service (4 — account/margin state schemas)

- `CanonicalAccountSnapshot`, `CanonicalAccountState`
- `CanonicalBalance`
- `CanonicalMarginState`

**Action:** Import in `risk_and_exposure_service/models.py` (already has UIC contract references).

---

## Group F: strategy-service (7 — signal/arbitrage/factor schemas)

- `ArbitrageMarket`, `ArbitrageOpportunity`, `ArbitrageStatus`
- `CommoditySignal`, `SignalSource`
- `ExpectedValue`, `FactorValue`

**Action:** Import in `strategy_service/engine/` or signal publisher layer.

---

## Group G: EXEMPT_CLASSES additions (6 — WebSocket protocol + registry infra)

Add to `EXEMPT_CLASSES` in `unified-api-contracts/scripts/check_uac_adoption.py`:

- `HeartbeatMessage`, `SubscribeRequest`, `UnsubscribeRequest` — ws-protocol: WS connection control; used via framework,
  not imported by class name
- `WebSocketConnectionState` — ws-infra: enum used internally by WS adapter layer
- `EndpointSpec` — registry-spec: endpoint registry type, accessed programmatically
- `OddsFormat` — re-exported-via-uic: terminal services import from unified_internal_contracts

---

## Remediation Progress (2026-03-10)

Baseline orphan count: **86** (confirmed 2026-03-10)

| Group | Target Service               | Count                      | Status         |
| ----- | ---------------------------- | -------------------------- | -------------- |
| A     | features-onchain-service     | 17 DeFi schemas            | 🔄 In Progress |
| B     | features-sports-service      | 19 sports/error schemas    | 🔄 In Progress |
| C     | instruments-service          | 24 exchange API schemas    | 🔄 In Progress |
| D     | execution-service            | 9 order/options schemas    | 🔄 In Progress |
| E     | risk-and-exposure-service    | 4 account schemas          | 🔄 In Progress |
| F     | strategy-service             | 7 signal/arbitrage schemas | 🔄 In Progress |
| G     | check_uac_adoption.py EXEMPT | 6 infra/protocol schemas   | 🔄 In Progress |

Target orphan count: **0**

## Tracking

Gate: `system-integration-tests/.github/workflows/smoke-test-gate.yml` — `contract-adoption-check` job Checker:
`unified-api-contracts/scripts/check_uac_adoption.py --orphans-only`
