---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This is the pre-v2 (category-organised) strategy catalogue, preserved from the
> strategy-docs-vs-system audit (PM main@03a37b6a1). Current canonical design:
> [`../architecture-v2/`](../architecture-v2/README.md). Do not use this document for implementation decisions — it is
> retained for historical reference only.

# 09 — Strategy Documentation

Canonical reference for all trading strategies in the Unified Trading System. **65+ strategy configurations** across 6
asset classes, powered by 7 feature services (150+ calculators), 13+ execution algorithms, and 5 matching engine types.
Each strategy has a dedicated document following the
[strategy description template](templates/strategy-description-template.md).

For a consolidated checklist of template + system expectations and **Codex vs `strategy-service` alignment gaps**, see
[STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md](STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md).

For **Tier 0 UI mock parity** (fixtures, cross-strategy UX expectations, promotion to T1/T2), see
[TIER_ZERO_UI_DEMO_AND_PARITY.md](TIER_ZERO_UI_DEMO_AND_PARITY.md) and the UI playbook
`unified-trading-system-ui/docs/END_TO_END_STATIC_TIER_ZERO_TESTING.md`.

## Instrument Filtering

All DeFi strategies depend on instrument discovery — which pools, lending markets, and derivatives are available to
trade. See **[cross-cutting/instrument-filtering.md](cross-cutting/instrument-filtering.md)** for the full filtering
pipeline:

- Major asset whitelist (`DEFI_MAJOR_ASSET_SYMBOLS` — ~65 tokens across EVM + Solana)
- DEX pools require BOTH sides to be major assets + TVL minimums
- Lending markets require base asset to be major
- Underlying families (stablecoin, ETH, BTC, SOL) as fixed strategy config parameters
- How to add new tokens

## Organisation

```
09-strategy/
├── cross-cutting/          # Concerns shared by ALL strategies
├── defi/                   # DeFi strategies (19 — EVM, Solana, BTC, multi-chain)
├── cefi/                   # CeFi strategies (6 — momentum, mean reversion, arb, ML, MM)
├── tradfi/                 # TradFi strategies (6 — ML directional, options, vol, momentum, MM)
├── sports/                 # Sports betting strategies (6 — arb, value, ML, halftime ML, Kelly, MM)
├── prediction/             # Prediction market strategies (1 — cross-venue arb)
└── templates/              # Strategy description template
```

## Strategy Index

### DeFi — Ethereum / EVM (9 strategies + 1 MM)

| Strategy                                                 | File                                              | Status        | Target APY |
| -------------------------------------------------------- | ------------------------------------------------- | ------------- | ---------- |
| [ETH Basis Trade](defi/basis-trade.md)                   | `defi_basis.py`                                   | Code complete | 10-25%     |
| [ETH Staked Basis](defi/staked-basis.md)                 | `defi_staked_basis.py`                            | Code complete | 15-30%     |
| [Recursive Staked Basis](defi/recursive-staked-basis.md) | `defi_recursive_basis.py`                         | Code complete | 20-40%     |
| [Unhedged Recursive](defi/unhedged-recursive.md)         | `defi_recursive_basis.py` (hedged=False)          | Code complete | 25-50%     |
| [AAVE Lending](defi/aave-lending.md)                     | `defi_lending.py`                                 | Code complete | 3-12%      |
| ETH Lending                                              | `defi_lending.py` (lending_basket=["ETH","WETH"]) | Code complete | 1-3%       |
| [Ethena Benchmark](defi/ethena-benchmark.md)             | `defi_ethena_benchmark.py`                        | Code complete | 8-12%      |
| [AMM Liquidity Provision](defi/market-making-lp.md)      | `defi_amm_lp.py`                                  | Code complete | 15-50%     |
| [Reward Lifecycle](defi/reward-lifecycle.md)             | (cross-cutting — EIGEN/ETHFI accrue/claim/sell)   | Documented    | N/A        |

### DeFi — Solana (4 strategies)

| Strategy                                                          | File                     | Status        | Target APY |
| ----------------------------------------------------------------- | ------------------------ | ------------- | ---------- |
| [SOL Basis Trade (Drift)](defi/sol-basis-trade.md)                | `sol_basis.py`           | Code complete | 15-30%     |
| [SOL Staked Basis (mSOL + Drift)](defi/sol-staked-basis.md)       | `sol_staked_basis.py`    | Code complete | 22-37%     |
| [SOL Lending Yield (Kamino)](defi/sol-lending-yield.md)           | `sol_lending.py`         | Code complete | 8-25%      |
| [SOL Concentrated LP (Raydium/Orca)](defi/sol-concentrated-lp.md) | `sol_concentrated_lp.py` | Code complete | 20-60%     |

### DeFi — BTC (2 strategies)

| Strategy                                                     | File             | Status        | Target APY |
| ------------------------------------------------------------ | ---------------- | ------------- | ---------- |
| [BTC Basis Trade (WBTC/cbBTC)](defi/btc-basis-trade.md)      | `btc_basis.py`   | Code complete | 8-18%      |
| [BTC Lending Yield (multi-chain)](defi/btc-lending-yield.md) | `btc_lending.py` | Code complete | 3-15%      |

### DeFi — Multi-Chain / Cross-Chain (5 strategies)

| Strategy                                                                  | File                       | Status        | Target APY |
| ------------------------------------------------------------------------- | -------------------------- | ------------- | ---------- |
| [Multi-Chain Lending Yield (SOR)](defi/multi-chain-lending-yield.md)      | `multichain_lending.py`    | Code complete | 5-12%      |
| [Cross-Chain Yield Arbitrage](defi/cross-chain-yield-arb.md)              | `cross_chain_yield_arb.py` | Code complete | 3-8%       |
| [L2 Basis Trade (low gas)](defi/l2-basis-trade.md)                        | `l2_basis.py`              | Code complete | 12-25%     |
| [Cross-Chain SOR Rebalancing (meta)](defi/cross-chain-sor-rebalancing.md) | `cross_chain_sor.py`       | Code complete | +2-5%      |
| [Omnichain Transfers](defi/omnichain-transfers.md)                        | N/A (meta-strategy)        | Documented    | N/A        |

### CeFi (5 strategies + 1 MM)

| Strategy                                           | File                         | Status        | Capital Target |
| -------------------------------------------------- | ---------------------------- | ------------- | -------------- |
| [Momentum](cefi/momentum.md)                       | `cefi_momentum.py`           | Code complete | TBD            |
| [Mean Reversion](cefi/mean-reversion.md)           | `mean_reversion_strategy.py` | Code complete | TBD            |
| [Cross-Exchange Arbitrage](cefi/cross-exchange.md) | `cross_exchange_strategy.py` | Code complete | TBD            |
| [Statistical Arbitrage](cefi/stat-arb.md)          | `stat_arb_strategy.py`       | Code complete | TBD            |
| [ML Directional](cefi/ml-directional.md)           | `cefi_ml_directional.py`     | Code complete | TBD            |
| [Market Making](cefi/market-making.md)             | `cefi_market_making.py`      | Code complete | TBD            |

### TradFi (5 strategies + 1 MM)

| Strategy                                                 | File                                | Status        | Capital Target |
| -------------------------------------------------------- | ----------------------------------- | ------------- | -------------- |
| [ML Directional](tradfi/ml-directional.md)               | `tradfi_ml_directional_strategy.py` | Code complete | TBD            |
| [Options ML](tradfi/options-ml.md)                       | `options_ml_strategy.py`            | Code complete | TBD            |
| [TradFi Momentum](tradfi/tradfi-momentum.md)             | `tradfi_momentum.py`                | Code complete | TBD            |
| [Relative Volatility](tradfi/relative-volatility.md)     | `rel_vol_strategy.py`               | Code complete | TBD            |
| [Volatility Surface](tradfi/volatility-surface.md)       | `vol_surface_strategy.py`           | Code complete | TBD            |
| [Options Market Making](tradfi/market-making-options.md) | `options_mm_strategy.py`            | Code complete | TBD            |

### Sports (5 strategies + 1 MM)

| Strategy                                 | File                    | Status        | Capital Target |
| ---------------------------------------- | ----------------------- | ------------- | -------------- |
| [Arbitrage](sports/arbitrage.md)         | `arbitrage.py`          | Code complete | TBD            |
| [Value Betting](sports/value-betting.md) | `value_betting.py`      | Code complete | TBD            |
| [ML Sports](sports/ml-sports.md)         | `ml_sports_strategy.py` | Code complete | TBD            |
| [Halftime ML](sports/halftime-ml.md)     | `halftime_ml.py`        | Code complete | TBD            |
| [Kelly Criterion](sports/kelly.md)       | `kelly.py`              | Code complete | TBD            |
| [Market Making](sports/market-making.md) | `market_making.py`      | Code complete | TBD            |

### Prediction Markets (1 strategy)

| Strategy                                             | File                         | Status        | Capital Target |
| ---------------------------------------------------- | ---------------------------- | ------------- | -------------- |
| [Prediction Arbitrage](prediction/prediction-arb.md) | `prediction_arb_strategy.py` | Code complete | TBD            |

### Planned Strategies (not yet implemented)

| Strategy Family    | Domain | Description                                                |
| ------------------ | ------ | ---------------------------------------------------------- |
| LendingProtocolArb | DeFi   | Cross-protocol lending rate arbitrage (Aave vs Compound)   |
| LiquidationCapture | DeFi   | Capture liquidation bounties on under-collateralized loans |
| ActiveDeFiMM       | DeFi   | Active market making on concentrated liquidity DEXes       |
| OmnichainTransfer  | DeFi   | Cross-chain capital rebalancing for yield optimization     |
| EventDrivenMacro   | TradFi | Macro event-driven positioning (FOMC, NFP, CPI)            |
| CommodityRegime    | TradFi | Regime-switching commodity futures strategies              |

## Strategy Infrastructure

### Feature Services (7 services, 150+ calculators)

All strategies consume pre-computed features; strategies NEVER access raw market data. Feature services:

1. **features-delta-one-service** — funding rates, basis spreads, carry signals
2. **features-onchain-service** — DeFi protocol metrics (staking APY, health factor, gas, rewards)
3. **features-cross-instrument-service** — cross-asset correlations, crowd sentiment, prediction market implied probs
4. **features-sports-service** — team form, xG, odds movement, halftime stats
5. **features-tradfi-service** — equity/FX/commodity features, macro indicators
6. **features-volatility-service** — implied/realized vol, vol surface, skew, term structure
7. **features-ml-service** — ML model inference, ensemble predictions, feature importance

### Execution Algorithms (13+)

Execution-service provides algorithm selection via SOR. Strategies set constraints (`allowed_venues`,
`max_slippage_bps`, `benchmark_price`); execution-service selects the appropriate algorithm:

1. **TWAP** — Time-weighted average price
2. **VWAP** — Volume-weighted average price
3. **Iceberg** — Hidden size, exposed clip
4. **Sniper** — Aggressive fill at target price
5. **PassiveJoin** — Passive limit at best bid/ask
6. **SOR** — Smart order routing across venues
7. **AtomicBundle** — Flash loan atomic sequences (DeFi)
8. **FlashLoanArb** — Flash loan arbitrage execution
9. **BetPlacement** — Sports bookmaker/exchange placement
10. **PredictionMarket** — Binary outcome market execution
11. **MarketMake** — Two-sided quoting
12. **PegOrder** — Pegged to reference price
13. **Bracket** — Entry + stop-loss + take-profit

### Matching Engine Types (5)

Internal matching engines for paper trading, backtesting, and SIT:

1. **SimpleMatch** — Immediate fill at mid-price
2. **QueueMatch** — FIFO queue simulation with latency
3. **ProbabilisticMatch** — Fill probability based on size/spread
4. **HistoricalReplay** — Replay recorded order book for realistic fills
5. **MockDeFi** — Simulated DeFi protocol interactions (flash loans, swaps, lending)

## Cross-Cutting Concerns

These apply to ALL strategies regardless of asset class:

| Document                                                                      | What It Covers                                                                            |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| [PnL Attribution](cross-cutting/pnl-attribution.md)                           | Balance-based SOT, 7 attribution buckets, 2% reconciliation tolerance                     |
| [Cost Modeling](cross-cutting/cost-modeling.md)                               | Transaction costs, gas, slippage, flash loan fees, opportunity cost                       |
| [ML Pipeline](cross-cutting/ml-pipeline.md)                                   | Feature ingestion, model lifecycle, signal generation, retraining                         |
| [Latency Profiles](cross-cutting/latency-profiles.md)                         | p50/p99 targets per segment, co-location decision framework                               |
| [Strategy Onboarding](cross-cutting/onboarding-checklist.md)                  | Checklist for adding a new strategy to the system                                         |
| [Client Onboarding](cross-cutting/client-onboarding.md)                       | Adding a new client to an existing strategy                                               |
| [Config Architecture](cross-cutting/config-architecture.md)                   | Config-driven PnL, live=batch parity, hot-reload vs restart                               |
| [Operational Modes Matrix](cross-cutting/operational-modes-matrix.md)         | Mock/real, testnet, local cloud, env axes, IBKR paper vs `TESTNET_MODE`, SIT expectations |
| [Margin & Health](cross-cutting/margin-health.md)                             | LTV, health factor, liquidation across CeFi/DeFi/TradFi                                   |
| [Prediction Markets](cross-cutting/prediction-markets.md)                     | Polymarket/Kalshi as features, execution, and arb surface                                 |
| [Share Classes](cross-cutting/share-classes.md)                               | ETH/USDT/BTC base currency denomination, delta targets, FX factor in P&L                  |
| [Reward Lifecycle](cross-cutting/reward-lifecycle.md)                         | Staking reward accrue/claim/sell/attribute pipeline (EIGEN, ETHFI)                        |
| [Venue Collateral & Wrapping](cross-cutting/venue-collateral-and-wrapping.md) | Venue collateral matrix, token wrapping (ETH/eETH/stETH), instruction blocking            |

## Key Principles

### Hard Rules (MUST NOT be violated)

1. **Strategies NEVER access raw data** — no streaming from market-tick-data-service or market-data-processing-service.
   All data arrives via features or ML inference. Strategy doesn't deal with WebSocket connections, orderbook snapshots,
   or candle assembly. See [config-architecture.md](cross-cutting/config-architecture.md) rule 1.

2. **All strategies are event-driven** — there are no "timer-based" strategies. What looks time-based is actually
   event-driven from upstream feature updates. Market-making triggers on underlying move threshold; DeFi triggers on
   hourly features; sports triggers on odds update. See [config-architecture.md](cross-cutting/config-architecture.md)
   rule 2.

3. **Strategy receives, never calculates** — strategy receives positions (ExposureMonitor), risk assessments
   (RiskMonitor), PnL (PnLCalculator), features (pub/sub). Strategy's only job: decide what to do and emit
   `StrategyInstruction`.

4. **Execution-service executes, strategy decides** — strategy sends instructions with `allowed_venues`,
   `max_slippage_bps`, `benchmark_price`. Execution-service handles SOR, order type selection, fill monitoring, and
   alpha measurement. Strategy never picks execution venue.

### Architecture Principles

5. **Unit of execution: `(strategy_id, client_id, config)`** — positions diverge due to execution timing; shared
   strategy template, isolated instances. Multiple tuples run in one process (async). Same architecture for live and
   batch. See [config-architecture.md](cross-cutting/config-architecture.md) rule 5.

6. **Config-driven, mode-independent** — same PnL calculator, same settlement service, same attribution for live and
   batch. Config defines rules; data defines events; time window is a slice.

7. **Balance-based PnL is source of truth** — `total_pnl = equity_current - equity_initial`. Attribution components must
   sum to match. Unexplained > 2% = alert.

8. **Index-based yield, never APY approximation** — Aave liquidity_index, weETH exchange rate, funding rate settlements.
   APY is display-only for signal generation; never used in PnL.

9. **Hot-reload where possible** — strategy config params reload from GCS via UCI without restart. New strategy types or
   risk types require restart.

## Related SSOTs

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md` + `STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (external/canonical surface + `unified_api_contracts.internal` subpackage)
- **Credentials:** `unified-cloud-interface/credentials_registry.py` + `unified-trading-pm/credentials-registry.yaml`
- **Venue capabilities:** `unified-api-contracts/registry/capability_declarations/`
- **Testing stages:** `unified-api-contracts/unified_api_contracts/internal/modes.py` (`TestingStage`,
  `OperationalMode`) — see [operational-modes-matrix.md](cross-cutting/operational-modes-matrix.md)
