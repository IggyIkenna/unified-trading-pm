---
name: API Contracts Institutional Gaps
overview: Full cross-venue gap analysis — every institutional data category mapped against every venue (CeFi, TradFi, DeFi, Sports) plus complete CCXT surface coverage. Identifies ~300+ missing schemas not covered by the existing plan.
todos:
  - id: ccxt-completeness
    content: "Expand ccxt/schemas.py from 12% to full coverage: ~50 missing method schemas including FundingRate, FundingRateHistory, LeverageTiers, OpenInterest, OpenInterestHistory, LongShortRatio, Greeks, Options, Currencies, Withdrawals, Deposits, DepositAddress, Ledger, Transfer, TradingFee, Subaccounts, InsuranceFund, Liquidations, SettlementHistory, BorrowRate, BorrowInterest, MarginAdjustment; expand CcxtPosition (18 missing fields), CcxtOrder (missing reduceOnly/stopPrice/trades), CcxtMarket (20 missing fields), CcxtBalance (missing debt/timestamp), CcxtTrade (missing takerOrMaker/fees array); add CcxtOhlcv, CcxtAggTrade"
    status: completed
  - id: sports-betting-modules
    content: "Add 5 sports betting venue modules: betfair/, pinnacle/, polymarket/, odds_api/, api_football/ — each with schemas.py, examples/, mocks/, venue_manifest entries"
    status: completed
  - id: fee-data-all-venues
    content: "Add fee schemas across all venues: BinanceFeeRate, BybitFeeRate, OKXFeeRate, DeribitAccountSummary, CoinbaseFeeSchedule, UpbitFeeRate, IBKRCommissionReport, AsterIncome; add BinanceIsolatedMarginBorrowRate, BinanceCrossMarginData, OKXBorrowRate, OKXLendingRateHistory, BybitSpotMarginBorrowRate, DeribitPortfolioMargins, IBKRShortable, IBKRBorrowFeeRate; shared ExchangeFeeSchedule in schemas/"
    status: completed
  - id: sentiment-positioning-all-venues
    content: "Add market sentiment/positioning across all venues: BinanceLongShortRatio, BinanceTopTraderLongShortRatio, BinanceBuySellVolume, BinanceOpenInterestHistory, OKXLongShortRatio, OKXOpenInterest, OKXOpenInterestHistory, BybitLongShortRatio, BybitOpenInterestHistory, HyperliquidFundingHistoryEntry, HyperliquidPredictedFunding, DeribitOpenInterestHistory; shared OpenInterestHistory, LongShortRatio, FuturesBasis in schemas/derivatives.py"
    status: completed
  - id: risk-infrastructure-all-venues
    content: "Add risk infrastructure: BinanceInsuranceFund, BinanceAdlQuantile, BinancePositionRisk (full REST), BinanceLeverageBracket, BybitInsuranceFund, BybitRiskLimit, OKXRiskLimit, OKXInsuranceFund, DeribitRiskLimit, DeribitSessionBankruptcyDetails, HyperliquidInsuranceFund, AsterLeverageBracket; add liquidationPrice/bankruptcyPrice/maintenanceMarginRate to every venue position schema that's missing it; shared PositionRisk, InsuranceFundState in schemas/"
    status: completed
  - id: account-lifecycle-all-venues
    content: "Add deposit/withdrawal/transfer lifecycle (100% missing across all venues): BinanceDepositAddress, BinanceDepositHistory, BinanceWithdrawalHistory, BinanceInternalTransfer, BinanceSubAccount, BinanceSubAccountAssets; OKXDepositAddress, OKXDepositHistory, OKXWithdrawalHistory, OKXFundTransfer, OKXSubAccount; BybitDepositAddress, BybitDepositRecords, BybitWithdrawals, BybitAccountTransfer; DeribitDeposits, DeribitWithdrawals, DeribitSubaccount; CoinbaseDeposit, CoinbaseWithdrawal; UpbitDeposit, UpbitWithdrawal; shared DepositAddress, DepositRecord, WithdrawalRecord, InternalTransfer, SubAccount in schemas/accounts.py"
    status: completed
  - id: aggregate-trades-all-venues
    content: "Add aggregate/execution quality schemas: BinanceAggTrade (spot + futures REST + WS), BinanceMyTrades (REST fills with fees), OKXTradeFill (paginated history), OKXMyTrades, BybitPublicTrade, BybitMyExecutions (REST history), DeribitUserTrades, HyperliquidFill (fills with fees/closedPnl), HyperliquidOpenOrder, AsterAggTrade, AsterTrade, IBKRExecution, IBKRHistoricalTickLast, IBKRHistoricalTickBidAsk; shared AggregatedTrade, ExecutionFill in schemas/"
    status: completed
  - id: funding-premium-mark-price-history
    content: "Add funding rate history + mark/index price REST timeseries: BinanceFundingRateHistory, BinancePremiumIndex, BinanceMarkPriceKline, BinanceIndexPriceKline; OKXFundingRateHistory, OKXMarkPriceCandle, OKXIndexCandle; BybitFundingRateHistory, BybitMarkPriceKline, BybitIndexPriceKline, BybitPremiumIndexKline; DeribitFundingRateHistory, DeribitMarkPriceHistory, DeribitIndexPriceHistory; HyperliquidFundingHistory; AsterFundingRate, AsterMarkPrice; shared FundingRateHistory in schemas/derivatives.py"
    status: completed
  - id: portfolio-margin-all-venues
    content: "Add portfolio margin mode schemas: BinancePapiAccount, BinancePapiBalance, BinancePapiPosition; DeribitPortfolioMarginSummary (delta/gamma/theta/vega totals); OKXPortfolioMarginAccount (adjEq, imr, mmr); BybitUnifiedAccount (extend BybitWalletWS with full REST equivalent)"
    status: completed
  - id: settlement-delivery-all-venues
    content: "Add settlement/delivery lifecycle: BinanceDeliveryHistory, OKXDeliveryExerciseHistory, BybitDeliveryRecord, DeribitSettlementCashFlows, AsterSettlement; shared SettlementEvent in schemas/derivatives.py"
    status: completed
  - id: vol-surface-all-venues
    content: "Add vol surface schemas: DeribitVolatilityIndex (DVOL WS + REST history), DeribitMarkPriceHistory, DeribitIndexPriceHistory, DeribitRiskReversal25d; OKXOptionSummary (primary vol surface endpoint), OKXOptionTicker (full greeks WS); BinanceMarkPriceKline, BinanceIndexPriceKline; IBKROptionGreeks (tickOptionComputation), IBKRHistoricalVolatility, IBKRSecDefOptParams; shared VolatilitySurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure, VixTermStructure in schemas/derivatives.py"
    status: completed
  - id: databento-additional-schemas
    content: "Add Databento schemas beyond what's planned: DatabentoMbp10 (10-level book), DatabentoBbo1s, DatabentoBbo1m (aggregated BBO), DatabentoCmbp1 (consolidated cross-venue BBO), DatabentoStatus (trading halts/limit-up-down), DatabentoImbalance (open/close auction), DatabentoStatistics (settlement prices, OI, VWAP from exchange), DatabentoMbo (market-by-order, L3), DatabentoSystemMsg, DatabentoErrorMsg"
    status: completed
  - id: hyperliquid-completeness
    content: "Add Hyperliquid schemas: HyperliquidUserState (clearinghouse state: equity, margin, withdrawable, assetPositions), HyperliquidL2Book (order book snapshot), HyperliquidFundingHistoryEntry, HyperliquidFill (fills with fees/closedPnl/feeToken), HyperliquidOpenOrder, HyperliquidCandle (OHLCV), HyperliquidVaultDetails, HyperliquidLiquidation (historical), HyperliquidSpotMeta, HyperliquidSpotAssetInfo, HyperliquidUserFees (fee tier/rebate), HyperliquidSubAccount"
    status: completed
  - id: aster-completeness
    content: "Add Aster schemas (Binance Futures-compatible): AsterAggTrade, AsterTrade, AsterKline, AsterMarkPrice, AsterFundingRate, AsterOpenInterest, AsterOpenInterestHistory, AsterTicker24hr, AsterExchangeInfo, AsterAccount, AsterBalance, AsterIncome (PnL/funding/commission history), AsterLeverageBracket, AsterOrderTradeUpdate (WS), AsterAccountUpdate (WS), AsterLiquidationOrder (WS forceOrder stream)"
    status: completed
  - id: ibkr-advanced-schemas
    content: "Add IBKR advanced schemas: IBKRScannerSubscription, IBKRScannerData; IBKRFAProfile, IBKRFAAccountGroup, IBKRFAAllocationProfile; IBKROptionComputation (Greeks via tickOptionComputation); IBKRExecution, IBKRCommissionReport; IBKRPnLSingle, IBKRPnLHistory; IBKRNewsProvider, IBKRNewsArticle, IBKRHistoricalNews; IBKRMarketDepth (L2); IBKRHistoricalTick, IBKRHistoricalTickBidAsk, IBKRHistoricalTickLast; IBKRFlexQuery, IBKRCashReport, IBKRStatement; IBKRPortfolioAnalytics; IBKRRealTimeBar (5s bars); IBKRAccountUpdateMulti; IBKRSecDefOptParams, IBKRHistoricalVolatility, IBKROptionGreeks"
    status: completed
  - id: thegraph-defi-protocol-schemas
    content: "Add The Graph protocol-specific schemas: SubgraphAaveUserPosition (healthFactor, collateral, debt per reserve), SubgraphUniV3Position (NFT LP positions, tick range, fee accrual), SubgraphUniV3PoolTick, SubgraphCurveGauge, SubgraphCurveVotingEscrow, SubgraphMorphoPosition (supply/borrow shares), SubgraphLidoRebase, SubgraphEthenaYield, SubgraphERC20Transfer, SubgraphERC20Approval, SubgraphProtocolTvlSnapshot; extend defi.py with DeFiLendingPosition, DeFiLPPosition, DeFiRebaseEvent, DeFiGaugeState, DeFiFlashLoanEvent"
    status: completed
  - id: alchemy-onchain-schemas
    content: "Add Alchemy on-chain schemas: AlchemyBlock, AlchemyTransaction, AlchemyTransactionReceipt, AlchemyLog, AlchemyDecodedLog (Transfer/Approval/Swap/Mint/Burn events), AlchemyGasOracle (baseFee, priorityFee history), AlchemyEnsResolution, AlchemyNFTMetadata (for Uniswap V3 LP NFT positions), AlchemyNFTOwnership, AlchemyTokenMetadata, AlchemySimulationResult (pre-trade DeFi validation), AlchemyWebhookSubscription"
    status: completed
  - id: defi-protocol-sdk-lending-schemas
    content: "Add DeFi protocol lending position schemas (user-account level, not just market rates): AaveV3ReserveData, AaveV3UserAccountData, AaveV3UserReserveData, AaveV3EModeData; CompoundV3MarketInfo, CompoundV3UserPosition, CompoundV3AssetInfo; MorphoMarketParams, MorphoMarketState, MorphoUserPosition, MorphoVaultData; EulerVaultData, EulerUserPosition, EulerOracleData"
    status: completed
  - id: shared-schema-extensions
    content: "Extend/add shared canonical schemas: derivatives.py — PositionRisk, InsuranceFundState, LongShortRatio, OpenInterestHistory, FundingRateHistory, SettlementEvent, VolatilitySurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure, VixTermStructure, FuturesBasis, AggregatedTrade, BorrowRate; add schemas/accounts.py — DepositAddress, DepositRecord, WithdrawalRecord, InternalTransfer, SubAccount, ExchangeFeeSchedule, PortfolioMarginAccount, MarginAdjustment, LedgerEntry"
    status: completed
isProject: false
---

# API Contracts — Institutional Gap Analysis (Beyond the Existing Plan)

## What the Existing Plan Already Covers (Do Not Repeat)

The [API_CONTRACTS_AUDIT_ADDENDUM.md](unified-trading-pm/plans/ai/API_CONTRACTS_AUDIT_ADDENDUM.md) + [API_CONTRACTS_TASK_LIST.md](unified-trading-pm/plans/ai/tasks/API_CONTRACTS_TASK_LIST.md) + [existing plan](/.cursor/plans/api_contracts_verbose_update_2b4e50bd.plan.md) already cover:

- Tardis full migration (BookSnapshot5, Liquidations, DerivativeTicker, OptionsChain)
- DatabentoTbbo, MBP-10
- CEX order submit/ack/cancel schemas for Binance/OKX/Bybit/Upbit/Coinbase
- CEX withdrawal schemas
- WebSocket lifecycle, ENDPOINT_SCHEMA_MAP, health/ping
- MEV protection (Flashbots, MEV Blocker, bloXroute)
- Protocol SDKs (AAVE, Compound, Morpho, Lido, Curve, Fluid, Euler)
- Cloud SDKs (GCP + AWS), quota broker
- SCHEMA_VERSIONS.md, collected_responses pipeline
- Instrument types matrix, chain-instruction validation
- Kraken removal

---

## TRUE GAPS: Not in Any Plan, Not in Any Schema

### GAP 1 — Sports Betting API Modules (5 New Venue Modules)

**Status: 0 schemas exist in api-contracts. Fully documented in codex but never contracted.**

The codex has detailed specs in `01-domain/asset-classes.md`, `02-data/sports-data-sources.md`, and `01-domain/sports-instruments.md`, but `api-contracts/api_contracts/` has zero sports-related modules.

New modules needed:

- `api_contracts/betfair/schemas.py` — Betfair Exchange Streaming API
  - `BetfairAuthRequest`, `BetfairAuthResponse`
  - `BetfairMarketSubscription`, `BetfairOrderSubscription`
  - `BetfairMarketChangeMessage`, `BetfairRunnerChange`
  - `BetfairMarketBook`, `BetfairRunner`, `BetfairPriceSize`
  - `BetfairOrderUpdate`, `BetfairError`
- `api_contracts/pinnacle/schemas.py` — Pinnacle REST API (polling 5-10s)
  - `PinnacleLeague`, `PinnacleEvent`, `PinnaclePeriod`
  - `PinnacleMoneyline`, `PinnacleTotals`, `PinnacleSpread`
  - `PinnacleOddsResponse`, `PinnacleSettlementResponse`, `PinnacleError`
- `api_contracts/polymarket/schemas.py` — Polymarket CLOB (Polygon chain)
  - `PolymarketMarket`, `PolymarketToken`, `PolymarketOrderBook`
  - `PolymarketTrade`, `PolymarketOrder`, `PolymarketFill`
  - `PolymarketMarketResult`, `PolymarketError`
- `api_contracts/odds_api/schemas.py` — The Odds API (T+1 batch, 15+ bookmakers)
  - `OddsApiFixture`, `OddsApiBookmaker`, `OddsApiMarket`
  - `OddsApiOutcome`, `OddsApiHistoricalOdds`, `OddsApiError`
- `api_contracts/api_football/schemas.py` — API-Football (reference data)
  - `ApiFootballFixture`, `ApiFootballTeam`, `ApiFootballLeague`
  - `ApiFootballLineup`, `ApiFootballStat`, `ApiFootballScore`
  - `ApiFootballPlayerStat`, `ApiFootballStanding`, `ApiFootballError`

All 5 need: `examples/`, `mocks/`, `venue_manifest` entries, VCR endpoints.

---

### GAP 2 — Exchange Risk Infrastructure (Insurance Fund, ADL, Risk Limits)

**Status: Entirely absent. Comments in Binance/Bybit schemas mention ADL as strings but zero typed schemas exist.**

Critical for institutional risk monitoring — you cannot safely run a levered book without these.

New schemas needed in existing venue modules:

- `BinanceInsuranceFund` — `GET /fapi/v1/fundingInfo` response; insurance fund size per asset
- `BinanceAdlQuantile` — `GET /fapi/v1/adlQuantile`; ADL queue position per position
- `BybitInsuranceFund` — insurance fund endpoint
- `HyperliquidInsuranceFund` — from `/info type=metaAndAssetCtxs`
- `DeribitSessionBankruptcyDetails` — socialized loss event schema (distinct from settlement)

New schemas for risk limit tiers:

- `BybitRiskLimit` — `GET /v5/position/get-risk-limit`; tier, maxLeverage, maintenanceMarginRate, initialMarginRate per tier
- `OKXRiskLimit` — underlying tier schema
- `DeribitRiskLimit` — per instrument/account
- `BinancePositionRisk` — `GET /fapi/v2/positionRisk`; full per-position risk (maintMargin, initialMargin, liquidationPrice, marginRatio, maxNotionalValue)

New shared schema in `schemas/derivatives.py`:

- `PositionRisk` — canonical: liquidationPrice, bankruptcyPrice, maintenanceMarginRate, initialMarginRate, marginRatio, adlRank, riskTier
- `InsuranceFundState` — canonical: asset, amount, timestamp

---

### GAP 3 — Volatility Surface & Vol Index Data

**Status: Per-instrument IV exists on Deribit and Binance options schemas, but no surface aggregation or vol index schemas exist.**

Needed for options strategies and risk management:

- `DeribitVolatilityIndex` — DVOL/BVOL index value stream; WS channel `deribit_volatility_index.{index_name}`; fields: index, open, high, low, close
- `VolSurface` — canonical shared schema; strikes × expiries grid; fields: underlying, timestamp, strikes: `list[VolSurfaceSlice]`
- `VolSurfaceSlice` — single expiry slice: expiry, forward, atm_iv, skew, kurtosis, smile: `list[VolSmilePoint]`
- `VolSmilePoint` — strike, delta, iv, bid_iv, ask_iv
- `OKXOptionSummary` — `GET /api/v5/market/opt-summary`; vol surface aggregate by expiry
- `BinanceOptionRiskInfo` — underlying vol data
- `VolTermStructure` — list of (expiry, atm_vol) pairs

---

### GAP 4 — Market Sentiment / Positioning Data

**Status: Snapshot OI on individual tickers exists (Deribit, Hyperliquid); no historical timeseries, no L/S ratio schemas.**

Required for macro positioning signals and strategy risk calibration:

- `BinanceLongShortRatio` — `GET /futures/data/globalLongShortAccountRatio`; longShortRatio, longAccount, shortAccount
- `BinanceTopTraderLongShortRatio` — top trader positioning
- `BinanceBuySellVolume` — taker buy/sell volume ratio
- `BinanceOpenInterestHistory` — `GET /futures/data/openInterestHist`; OI timeseries
- `OKXLongShortRatio` — `GET /api/v5/rubik/stat/contracts/long-short-account-ratio`
- `BybitLongShortRatio` — similar endpoint
- `HyperliquidFundingHistory` — historical funding rate per asset
- Shared `OpenInterestHistory`, `LongShortRatio` in `schemas/derivatives.py`

---

### GAP 5 — Fee Schedules and Commission Structures

**Status: Per-instrument commission precision exists on Binance; Deribit has per-instrument maker/taker. No exchange-level fee tier / VIP tier schema.**

Required for accurate P&L calculation and execution cost modeling:

- `BinanceFeeRate` — `GET /sapi/v1/asset/tradeFee`; symbol, makerCommission, takerCommission
- `BybitFeeRate` — `GET /v5/account/fee-rate`; baseFeeRate, discountFeeRate, takerFeeRate per category
- `OKXFeeRate` — `GET /api/v5/account/trade-fee`; maker, taker, tier, category
- `CoinbaseFeeSchedule` — pricing tier schema
- `DeribitAccountSummary` — full account snapshot with fee tier, options fees, perpetual fees
- Shared `ExchangeFeeSchedule` — canonical: tier, makerRate, takerRate, volumeThreshold

---

### GAP 6 — Account Lifecycle (Deposits, Withdrawals, Transfers, Sub-accounts)

**Status: CEX withdrawal request/response schemas are in the existing plan but deposit addresses, deposit history, internal transfers, and sub-accounts are entirely absent.**

Deposit/custody flows:

- `BinanceDepositAddress` — network, address, addressTag, url
- `BinanceDepositHistory` — status, amount, asset, network, txId, confirmTimes
- `BinanceWithdrawalHistory` — status, amount, asset, network, txId, fee
- `OKXDepositAddress`, `OKXDepositHistory`, `OKXWithdrawalHistory`
- `BybitDepositAddress`, `BybitDepositRecords`, `BybitWithdrawals`
- Shared `DepositAddress`, `DepositRecord`, `WithdrawalRecord` in `schemas/`

Internal transfers (between spot↔futures, margin modes):

- `BinanceInternalTransfer` — `POST /sapi/v1/asset/transfer`; fromAccountType, toAccountType, asset, amount
- `OKXFundTransfer` — `POST /api/v5/asset/transfer`
- `BybitAccountTransfer`

Sub-account management (critical for institutional):

- `BinanceSubAccount` — sub-account list, email, isFreeze
- `BinanceSubAccountAssets` — consolidated sub-account balances
- `OKXSubAccount`, `DeribitSubaccount`

---

### GAP 7 — Aggregate Trade Streams (Execution Quality)

**Status: Completely absent. BinanceTrade exists but BinanceAggTrade is missing.**

Required for execution quality analysis, VWAP calculations, and market microstructure:

- `BinanceAggTrade` — REST `GET /api/v3/aggTrades` + WS `@aggTrade`; aggTradeId, price, qty, firstTradeId, lastTradeId, isBuyerMaker, isBestMatch
- `BinanceFuturesAggTrade` — USDT-M `@aggTrade` stream
- `BybitPublicTrade` — `GET /v5/market/recent-trade`; trickle of individual trades
- `OKXTradeFill` — `GET /api/v5/market/trades` with pagination

---

### GAP 8 — Portfolio Margin Mode Schemas

**Status: Entirely absent. Only isolated/cross-margin WS updates exist for OKX/Bybit.**

Required for institutional accounts running portfolio margin:

- `BinancePapiAccount` — `GET /papi/v1/account`; Binance Portfolio Margin; totalEquity, actualEquity, availableBalance, uniMMR, accountMaintMargin
- `BinancePapiBalance` — `GET /papi/v1/balance`; per-asset balance under PM
- `BinancePapiPosition` — `GET /papi/v1/um/positionRisk` for PM mode
- `DeribitPortfolioMarginSummary` — projected maintenance margin, initial margin, delta_total across all positions
- `OKXPortfolioMarginAccount` — adjEq, imr, mmr fields

---

### GAP 9 — Funding Rate History and Premium Index (REST)

**Status: WS funding rate streams exist (Deribit, OKX). Historical REST endpoints absent.**

Required for strategy backtesting and carry calculation:

- `BinanceFundingRateHistory` — `GET /fapi/v1/fundingRate`; fundingTime, fundingRate
- `BinancePremiumIndex` — `GET /fapi/v1/premiumIndex`; markPrice, indexPrice, lastFundingRate, nextFundingTime, interestRate
- `OKXFundingRateHistory` — `GET /api/v5/public/funding-rate-history`
- `BybitFundingRateHistory` — `GET /v5/market/funding/history`
- `HyperliquidFundingHistory` — predicted/historical funding
- `DeribitFundingRateHistory` — `GET /public/get_funding_rate_history`
- Shared `FundingRateHistory` in `schemas/derivatives.py` — fundingTime, rate, markPrice, indexPrice

---

### GAP 10 — Settlement / Delivery Lifecycle

**Status: DeribitSettlementRecord and BinanceDeliveryPrice exist but settlement scheduling, notifications, and delivery history REST endpoints are mostly absent.**

- `BinanceDeliveryHistory` — quarterly futures delivery events with settlement price, amount
- `OKXSettlement` — `GET /api/v5/public/delivery-exercise-history`; options/futures exercise events
- `BybitDeliveryRecord` — delivery price, size, fee, contract
- `DeribitSettlementCashFlows` — per-instrument cash flows on settlement
- Shared `SettlementEvent` — canonical: instrument, settlementPrice, deliveryTime, cashFlow, fee

---

## Prioritized Implementation Order

**P0 — Risk-Critical (block live trading without these):**

- GAP 2: Insurance fund, ADL quantile, risk limits, full `PositionRisk` schema across all venues
- GAP 5: Fee schedules (needed for accurate P&L)
- GAP 9: Funding rate history REST (critical for carry strategies)

**P1 — Institutional Operations:**

- GAP 6: Deposit/withdrawal lifecycle, internal transfers
- GAP 4: Long/short ratio, OI history (positioning signals)
- GAP 8: Portfolio margin mode schemas
- GAP 10: Settlement/delivery lifecycle

**P2 — Strategy Signals and Analytics:**

- GAP 3: Vol surface, DVOL index (options strategies)
- GAP 7: Aggregate trades (execution quality / microstructure)
- GAP 1: Sports betting modules (Betfair, Pinnacle, Polymarket, Odds API, API-Football)

---

## Files to Create/Modify

**New modules:**

- `api_contracts/betfair/schemas.py` + examples + mocks
- `api_contracts/pinnacle/schemas.py` + examples + mocks
- `api_contracts/polymarket/schemas.py` + examples + mocks
- `api_contracts/odds_api/schemas.py` + examples + mocks
- `api_contracts/api_football/schemas.py` + examples + mocks

**Extend existing modules:**

- `api_contracts/binance/schemas.py` — AggTrade, FundingRateHistory, PremiumIndex, DepositAddress, DepositHistory, WithdrawalHistory, FeeRate, InternalTransfer, SubAccount, AdlQuantile, InsuranceFund, PositionRisk (full fields), PapiAccount, PapiBalance
- `api_contracts/bybit/schemas.py` — RiskLimit, FeeRate, FundingRateHistory, DepositAddress, DepositRecords, Withdrawals, LongShortRatio, DeliveryRecord
- `api_contracts/okx/schemas.py` — FeeRate, FundingRateHistory, DepositAddress, DepositHistory, WithdrawalHistory, LongShortRatio, SettlementHistory, PortfolioMarginAccount, FundTransfer
- `api_contracts/deribit/schemas.py` — AccountSummary (full), PortfolioMarginSummary, VolatilityIndex, FundingRateHistory, SettlementCashFlows
- `api_contracts/hyperliquid/schemas.py` — InsuranceFund, FundingHistory, UserState (equity, margin, positions)
- `api_contracts/coinbase/schemas.py` — FeeSchedule, Order, Fill (missing from current schemas)

**Extend shared schemas:**

- `api_contracts/schemas/derivatives.py` — PositionRisk, InsuranceFundState, LongShortRatio, OpenInterestHistory, FundingRateHistory, SettlementEvent, VolSurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure
- `api_contracts/schemas/` — add `accounts.py`: DepositAddress, DepositRecord, WithdrawalRecord, InternalTransfer, SubAccount, ExchangeFeeSchedule, PortfolioMarginAccount
