---
name: API Contracts — Full Cross-Venue Institutional Expansion
overview: Full cross-venue institutional gap analysis for api-contracts. Maps ~300+ missing schemas across every venue (CeFi, TradFi, DeFi, Sports) and the complete CCXT unified surface — not just Binance. Establishes what comes via CCXT vs. direct, what normalizes downstream, and what each venue uniquely exposes.
todos:
  - id: ccxt-completeness
    content: "Expand ccxt/schemas.py from 12% to ~90% CCXT unified API surface coverage: add ~50 method schemas (CcxtFundingRate, CcxtFundingRateHistory, CcxtLeverageTier, CcxtOpenInterest, CcxtOpenInterestHistory, CcxtLongShortRatio, CcxtGreeks, CcxtOption, CcxtCurrency, CcxtWithdrawal, CcxtDeposit, CcxtDepositAddress, CcxtLedgerEntry, CcxtTransfer, CcxtTradingFee, CcxtFees, CcxtSubaccount, CcxtInsuranceFund, CcxtLiquidation, CcxtSettlementHistory, CcxtBorrowRate, CcxtBorrowInterest, CcxtMarginAdjustment, CcxtVolatilityHistory, CcxtLeverage, CcxtMarginMode, CcxtPositionMode); expand CcxtPosition +18 fields (liquidationPrice, marginRatio, marginMode, initialMargin, maintenanceMargin, realizedPnl, collateral, notional, lastUpdateTimestamp), CcxtOrder +7, CcxtMarket +20, CcxtBalance +3, CcxtTicker +8, CcxtTrade +3; add CcxtOhlcv typed alias and CcxtAggTrade"
    status: pending
  - id: fee-borrow-all-venues
    content: "Add fee and borrow rate schemas across all venues: BinanceFeeRate, BinanceIsolatedMarginBorrowRate, BinanceCrossMarginData, BinanceIncome; BybitFeeRate, BybitSpotMarginBorrowRate; OKXFeeRate, OKXBorrowRate, OKXLendingRateHistory; DeribitAccountSummary (full), DeribitPortfolioMargins; IBKRCommissionReport, IBKRShortable, IBKRBorrowFeeRate; AsterIncome; shared ExchangeFeeSchedule and BorrowRate in schemas/accounts.py"
    status: pending
  - id: sentiment-oi-all-venues
    content: "Add market sentiment/positioning schemas: BinanceLongShortRatio, BinanceTopTraderLongShortRatio, BinanceBuySellVolume, BinanceOpenInterestHistory; OKXLongShortRatio, OKXOpenInterest, OKXOpenInterestHistory; BybitLongShortRatio, BybitOpenInterestHistory; HyperliquidFundingHistoryEntry, HyperliquidPredictedFunding; AsterOpenInterest, AsterOpenInterestHistory; shared OpenInterestHistory, LongShortRatio, FuturesBasis in schemas/derivatives.py"
    status: pending
  - id: risk-infrastructure-all-venues
    content: "Add risk infrastructure: BinanceInsuranceFund, BinanceAdlQuantile, BinancePositionRisk (full REST fields), BinanceLeverageBracket; BybitInsuranceFund, BybitRiskLimit; OKXInsuranceFund, OKXRiskLimit; DeribitRiskLimit, DeribitSessionBankruptcyDetails; HyperliquidInsuranceFund; AsterLeverageBracket; add liquidationPrice/bankruptcyPrice/maintenanceMarginRate/marginRatio to all venue position schemas missing them; shared PositionRisk, InsuranceFundState in schemas/derivatives.py"
    status: pending
  - id: account-lifecycle-all-venues
    content: "Add deposit/withdrawal/transfer lifecycle (100% missing across all venues): Binance (DepositAddress, DepositHistory, WithdrawalHistory, InternalTransfer, SubAccount, SubAccountAssets, PapiAccount, PapiBalance, PapiPosition); OKX (DepositAddress, DepositHistory, WithdrawalHistory, FundTransfer, SubAccount, PortfolioMarginAccount); Bybit (DepositAddress, DepositRecords, Withdrawals, AccountTransfer, SubAccount, UnifiedAccount); Deribit (Deposits, Withdrawals, Subaccount, PortfolioMarginSummary); Hyperliquid (SubAccount); Coinbase (Deposit, Withdrawal, FeeSchedule); Upbit (Deposit, Withdrawal); IBKR (CashReport, Statement, FlexQuery); shared schemas/accounts.py"
    status: pending
  - id: aggregate-trades-fills-mark-price
    content: "Add aggregate trades, my fills, and mark/index price OHLC history: BinanceAggTrade (spot+futures), BinanceMyTrades, BinanceMarkPriceKline, BinanceIndexPriceKline; BybitMyExecutions, BybitMarkPriceKline, BybitIndexPriceKline, BybitPremiumIndexKline; OKXMyTrades, OKXMarkPriceCandle, OKXIndexCandle; DeribitUserTrades, DeribitMarkPriceHistory, DeribitIndexPriceHistory; HyperliquidFill, HyperliquidOpenOrder, HyperliquidCandle; IBKR Execution/HistoricalTick/RealTimeBar; Aster AggTrade/Trade/MarkPrice"
    status: pending
  - id: funding-settlement-portfolio-margin
    content: "Add funding rate history REST + settlement + portfolio margin: BinanceFundingRateHistory, BinancePremiumIndex; OKXFundingRateHistory; BybitFundingRateHistory; DeribitFundingRateHistory; HyperliquidFundingHistoryEntry; AsterFundingRate; BinanceDeliveryHistory, OKXDeliveryExerciseHistory, BybitDeliveryRecord, DeribitSettlementCashFlows; BinancePapiAccount/Balance/Position, DeribitPortfolioMarginSummary, OKXPortfolioMarginAccount; shared FundingRateHistory and SettlementEvent in schemas/derivatives.py"
    status: pending
  - id: vol-surface-all-venues
    content: "Add volatility surface schemas: DeribitVolatilityIndex (DVOL WS+REST), DeribitMarkPriceHistory, DeribitIndexPriceHistory, DeribitRiskReversal25d; OKXOptionSummary (primary vol surface: delta/gamma/theta/vega/bidVol/askVol/markVol/fwdPx), OKXOptionTicker; BinanceMarkPriceKline, BinanceIndexPriceKline; IBKROptionComputation (delta/gamma/theta/vega/IV via tickOptionComputation), IBKRSecDefOptParams (strike/expiry grid), IBKRHistoricalVolatility; shared VolatilitySurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure, VixTermStructure in schemas/derivatives.py"
    status: pending
  - id: databento-additional-schemas
    content: "Add Databento schemas beyond planned TBBO/MBP-10: DatabentoBbo1s, DatabentoBbo1m (aggregated BBO), DatabentoCmbp1 (consolidated cross-venue BBO), DatabentoStatus (trading halts/limit-up-down/circuit breakers), DatabentoImbalance (open/close auction imbalance for MOO/MOC), DatabentoStatistics (settlement prices/OI/VWAP from exchange), DatabentoMbo (L3 market-by-order), DatabentoSystemMsg, DatabentoErrorMsg"
    status: completed
  - id: hyperliquid-aster-completeness
    content: "Add Hyperliquid (12 schemas): HyperliquidUserState, HyperliquidL2Book, HyperliquidFundingHistoryEntry, HyperliquidFill (with closedPnl/fee/feeToken/liquidationMarkPx), HyperliquidOpenOrder, HyperliquidCandle, HyperliquidVaultDetails, HyperliquidLiquidation, HyperliquidSpotMeta, HyperliquidSpotAssetInfo, HyperliquidUserFees, HyperliquidSubAccount. Add Aster (16 schemas): AggTrade, Trade, Kline, Ticker24hr, MarkPrice, FundingRate, OpenInterest, OpenInterestHistory, ExchangeInfo, Account, Balance, Income, LeverageBracket, OrderTradeUpdate/AccountUpdate/LiquidationOrder WS events"
    status: completed
  - id: ibkr-advanced-schemas
    content: "Add IBKR advanced schemas (21): IBKRScannerSubscription/Data; IBKRFAProfile/FAAccountGroup/FAAllocationProfile/AccountUpdateMulti; IBKROptionComputation, IBKRSecDefOptParams, IBKRHistoricalVolatility; IBKRExecution, IBKRCommissionReport; IBKRPnLSingle, IBKRPnLHistory; IBKRNewsProvider/Article/HistoricalNews; IBKRMarketDepth (L2); IBKRHistoricalTick/TickBidAsk/TickLast; IBKRFlexQuery/CashReport/Statement; IBKRRealTimeBar (5s), IBKRPortfolioAnalytics"
    status: completed
  - id: thegraph-alchemy-defi-schemas
    content: "Add The Graph user-position schemas (11): SubgraphAaveUserPosition, SubgraphUniV3Position, SubgraphUniV3PoolTick, SubgraphCurveGauge, SubgraphCurveVotingEscrow, SubgraphMorphoPosition, SubgraphLidoRebase, SubgraphEthenaYield, SubgraphERC20Transfer/Approval, SubgraphProtocolTvlSnapshot. Add Alchemy on-chain (12): AlchemyBlock, AlchemyTransaction, AlchemyTransactionReceipt, AlchemyLog, AlchemyDecodedLog, AlchemyGasOracle, AlchemyEnsResolution, AlchemyTokenMetadata, AlchemyNFTMetadata/Ownership, AlchemySimulationResult, AlchemyWebhookSubscription. Extend schemas/defi.py: DeFiLendingPosition, DeFiLPPosition, DeFiRebaseEvent, DeFiGaugeState, DeFiFlashLoanEvent. Add 14 protocol SDK schemas: AaveV3 (4), CompoundV3 (3), Morpho (4), Euler (3) user-account level with health factor and liquidation threshold"
    status: completed
  - id: sports-betting-modules
    content: "Add 5 sports betting venue modules: betfair/ (Exchange Streaming API: MarketBook, Runner, PriceSize, OrderUpdate), pinnacle/ (REST: League, Event, Moneyline, Totals, Spread, SettlementResponse), polymarket/ (CLOB: Market, Token, OrderBook, Trade, Order, Fill, MarketResult), odds_api/ (Fixture, Bookmaker, Market, Outcome, HistoricalOdds), api_football/ (Fixture, Team, League, Lineup, Stat, Score, PlayerStat, Standing) — each with schemas.py, examples/, mocks/, venue_manifest entries"
    status: completed
  - id: shared-schema-extensions
    content: "Extend schemas/derivatives.py with canonical forms: PositionRisk, InsuranceFundState, LongShortRatio, OpenInterestHistory, FundingRateHistory, SettlementEvent, VolatilitySurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure, VixTermStructure, FuturesBasis, AggregatedTrade, BorrowRate. Create schemas/accounts.py: DepositAddress, DepositRecord, WithdrawalRecord, InternalTransfer, SubAccount, LedgerEntry, PortfolioMarginAccount, MarginAdjustment, ExchangeFeeSchedule, BorrowRate"
    status: pending
isProject: false
---

# API Contracts — Full Cross-Venue Institutional Expansion

## Context

Current `api-contracts` covers ~12% of the CCXT unified API surface and has zero schemas for: deposits/withdrawals (100% missing across all 9 CeFi venues), borrow rates, long/short ratios, insurance funds, ADL quantile, aggregate trades, mark price history, funding rate history (REST), settlement lifecycle, vol surface, and all sports betting venues.

## Key Source Files

- `[api_contracts/ccxt/schemas.py](api-contracts/api_contracts/ccxt/schemas.py)` — 8 schemas, all partial
- `[api_contracts/binance/schemas.py](api-contracts/api_contracts/binance/schemas.py)` — extend with ~28 schemas
- `[api_contracts/hyperliquid/schemas.py](api-contracts/api_contracts/hyperliquid/schemas.py)` — extend with 12 schemas
- `[api_contracts/schemas/derivatives.py](api-contracts/api_contracts/schemas/derivatives.py)` — add canonical shared types
- New: `api_contracts/schemas/accounts.py` — deposit/withdrawal/fee canonical types

## CCXT Gap (GAP 0) — 88% Untyped

CCXT is the normalization layer. Every untyped method = unknown return contract. Currently at ~12% coverage. Needs ~50 new schemas plus expanding 6 existing ones:

- `CcxtFundingRate/History`, `CcxtLeverageTier`, `CcxtOpenInterest/History`, `CcxtLongShortRatio`
- `CcxtGreeks`, `CcxtOption`, `CcxtCurrency` (networks per asset)
- `CcxtWithdrawal`, `CcxtDeposit`, `CcxtDepositAddress`, `CcxtLedgerEntry`, `CcxtTransfer`
- `CcxtTradingFee`, `CcxtBorrowRate`, `CcxtMarginAdjustment`, `CcxtInsuranceFund`, `CcxtLiquidation`
- Expand: `CcxtPosition` (+18 fields incl. liquidationPrice, marginRatio), `CcxtOrder` (+7), `CcxtMarket` (+20), `CcxtOhlcv` (typed), `CcxtAggTrade`

## Cross-Venue Coverage Matrix (Key Gaps)


| Category             | Binance         | Bybit   | OKX  | Deribit | HL      | IBKR | Aster | CCXT |
| -------------------- | --------------- | ------- | ---- | ------- | ------- | ---- | ----- | ---- |
| Fee schedule         | MISS            | MISS    | MISS | MISS    | MISS    | MISS | MISS  | MISS |
| Borrow rates         | MISS            | MISS    | MISS | MISS    | N/A     | MISS | N/A   | MISS |
| L/S ratio            | MISS            | MISS    | MISS | N/A     | MISS    | N/A  | MISS  | MISS |
| OI history           | MISS            | MISS    | MISS | MISS    | PARTIAL | N/A  | MISS  | MISS |
| Insurance fund       | MISS            | MISS    | MISS | MISS    | MISS    | N/A  | MISS  | MISS |
| ADL quantile         | MISS            | MISS    | MISS | N/A     | MISS    | N/A  | MISS  | MISS |
| Risk limit tiers     | MISS            | MISS    | MISS | MISS    | MISS    | N/A  | MISS  | MISS |
| Deposits/withdrawals | **ALL MISSING** |         |      |         |         |      |       | MISS |
| Internal transfers   | **ALL MISSING** |         |      |         |         |      |       | MISS |
| Sub-accounts         | **ALL MISSING** |         |      |         |         |      |       | MISS |
| My fills (REST)      | MISS            | WS only | MISS | MISS    | MISS    | MISS | MISS  | MISS |
| Agg trades           | MISS            | N/A     | N/A  | N/A     | N/A     | N/A  | MISS  | MISS |
| Mark price OHLC      | MISS            | MISS    | MISS | MISS    | N/A     | N/A  | MISS  | MISS |
| Funding history REST | MISS            | MISS    | MISS | MISS    | MISS    | N/A  | MISS  | MISS |
| Vol surface          | MISS            | N/A     | MISS | MISS    | N/A     | MISS | N/A   | MISS |
| Portfolio margin     | MISS            | WS only | MISS | EXISTS  | MISS    | N/A  | N/A   | MISS |


## New Modules to Create

- `api_contracts/betfair/`, `pinnacle/`, `polymarket/`, `odds_api/`, `api_football/` — sports betting
- `api_contracts/schemas/accounts.py` — DepositAddress, DepositRecord, WithdrawalRecord, InternalTransfer, SubAccount, LedgerEntry, PortfolioMarginAccount, ExchangeFeeSchedule, BorrowRate

## Priority Breakdown

**P0 — Block live trading:**

- Fee schemas (P&L impossible without commission rates)
- Risk infrastructure: InsuranceFund, AdlQuantile, RiskLimitTiers, full PositionRisk (all venues)
- Funding rate history REST + PremiumIndex
- CcxtPosition (+18 missing fields) + CcxtFundingRate

**P1 — Institutional operations:**

- Account lifecycle — deposits/withdrawals/transfers/sub-accounts (100% missing everywhere)
- Sentiment — L/S ratio, OI history, buy/sell volume (all CeFi venues)
- Portfolio margin (Binance PAPI, Deribit, OKX)
- Settlement/delivery lifecycle
- Aggregate trades + my fills with fees (all venues)

**P2 — Strategy signals:**

- Vol surface (DVOL, OKXOptionSummary, canonical VolatilitySurface)
- Mark/index price OHLC history (Binance, Bybit, OKX, Deribit, Aster)
- Databento additional: Status (halts), Imbalance (auctions), Statistics, MBO (L3)
- Hyperliquid completeness (12 schemas incl. UserState, Fill, VaultDetails)
- Aster completeness (16 schemas — Binance-futures-compatible)
- IBKR advanced (21 schemas incl. Scanner, OptionGreeks, FAProfile, L2 depth)
- The Graph user positions (AAVE healthFactor, Uniswap V3 LP positions)
- Alchemy on-chain (Block, Log, GasOracle, SimulationResult)
- DeFi protocol SDK lending (AaveV3, CompoundV3, Morpho, Euler — user-account level)

**P3 — Sports betting:**

- Betfair, Pinnacle, Polymarket, Odds API, API-Football (5 new venue modules)

---

## Remaining (Post–Phase 6 Structure Integration)

**Completed (Phase 6):** Databento additional schemas (Bbo1s, Bbo1m, Cmbp1, Status, Imbalance, Statistics, Mbo); Hyperliquid + Aster completeness; IBKR advanced schemas (Scanner, SecDefOptParams, OptionGreeks, Execution, CommissionReport, PnLSingle/PnLHistory, MarketDepth, HistoricalTick*, RealTimeBar); The Graph + Alchemy user-position/on-chain schemas; sports betting modules (betfair, pinnacle, polymarket, odds_api, api_football); structure integration (ENDPOINT_SCHEMA_MAP, venue_manifest, INDEX.md references to API_CONTRACTS_AVAILABLE_INVENTORY.md and CROSS_VENUE_MATRIX.md).

**Still pending:**

- **ccxt-completeness**: CcxtLedgerEntry (vs CcxtLedger), CcxtBorrowInterest, CcxtMarginAdjustment, CcxtSettlementHistory, CcxtFees, CcxtVolatilityHistory, CcxtLeverage, CcxtMarginMode, CcxtPositionMode; expand CcxtPosition/CcxtOrder/CcxtMarket/CcxtBalance/CcxtTicker/CcxtTrade with missing fields
- **fee-borrow-all-venues**: BinanceIsolatedMarginBorrowRate, BinanceCrossMarginData, BinanceIncome; BybitSpotMarginBorrowRate; OKXBorrowRate, OKXLendingRateHistory; IBKRShortable, IBKRBorrowFeeRate; shared ExchangeFeeSchedule, BorrowRate in schemas/accounts.py
- **sentiment-oi-all-venues**: BinanceLongShortRatio, BinanceTopTraderLongShortRatio, BinanceBuySellVolume, BinanceOpenInterestHistory; shared OpenInterestHistory, LongShortRatio, FuturesBasis
- **risk-infrastructure-all-venues**: BinanceLeverageBracket; BybitInsuranceFund (done), OKXInsuranceFund; HyperliquidInsuranceFund; shared PositionRisk, InsuranceFundState
- **account-lifecycle-all-venues**: Deribit Deposits/Withdrawals/Subaccount; Hyperliquid SubAccount (done); IBKR CashReport, Statement, FlexQuery
- **aggregate-trades-fills-mark-price**: BinanceMyTrades, BinanceMarkPriceKline, BinanceIndexPriceKline; BybitMyExecutions, BybitMarkPriceKline, etc.; OKXMyTrades, OKXMarkPriceCandle; DeribitUserTrades, DeribitMarkPriceHistory
- **vol-surface-all-venues**: OKXOptionSummary, OKXOptionTicker; BinanceMarkPriceKline, BinanceIndexPriceKline; shared VolatilitySurface, VolSurfaceSlice, etc.
- **shared-schema-extensions**: schemas/derivatives.py canonical forms; schemas/accounts.py DepositAddress, DepositRecord, etc.
