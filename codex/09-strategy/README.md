# 09 — Strategy Documentation

Canonical reference for all trading strategies in the Unified Trading System. Each strategy has a dedicated document
following the [strategy description template](templates/strategy-description-template.md).

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
├── defi/                   # DeFi strategies (15 — EVM, Solana, BTC, multi-chain)
├── cefi/                   # CeFi strategies (momentum, mean reversion, arb)
├── tradfi/                 # TradFi strategies (ML directional, options, vol)
├── sports/                 # Sports betting strategies (arb, value, ML)
├── prediction/             # Prediction market strategies (cross-venue arb)
└── templates/              # Strategy description template
```

## Strategy Index

### DeFi — Ethereum / EVM (8 strategies + 1 MM)

| Strategy                                                 | File                                              | Status        | Target APY |
| -------------------------------------------------------- | ------------------------------------------------- | ------------- | ---------- |
| [ETH Basis Trade](defi/basis-trade.md)                   | `defi_basis.py`                                   | Code complete | 10-25%     |
| [ETH Staked Basis](defi/staked-basis.md)                 | `defi_staked_basis.py`                            | Code complete | 15-30%     |
| [Recursive Staked Basis](defi/recursive-staked-basis.md) | `defi_recursive_basis.py`                         | Code complete | 20-40%     |
| Unhedged Recursive                                       | `defi_recursive_basis.py` (hedged=False)          | Code complete | 25-50%     |
| [AAVE Lending](defi/aave-lending.md)                     | `defi_lending.py`                                 | Code complete | 3-12%      |
| ETH Lending                                              | `defi_lending.py` (lending_basket=["ETH","WETH"]) | Code complete | 1-3%       |
| [Ethena Benchmark](defi/ethena-benchmark.md)             | `defi_ethena_benchmark.py`                        | Code complete | 8-12%      |
| [AMM Liquidity Provision](defi/market-making-lp.md)      | `defi_amm_lp.py`                                  | Code complete | 15-50%     |

### DeFi — Solana (4 strategies)

| Strategy                                                          | File | Status     | Target APY |
| ----------------------------------------------------------------- | ---- | ---------- | ---------- |
| [SOL Basis Trade (Drift)](defi/sol-basis-trade.md)                | TBD  | Documented | 15-30%     |
| [SOL Staked Basis (mSOL + Drift)](defi/sol-staked-basis.md)       | TBD  | Documented | 22-37%     |
| [SOL Lending Yield (Kamino)](defi/sol-lending-yield.md)           | TBD  | Documented | 8-25%      |
| [SOL Concentrated LP (Raydium/Orca)](defi/sol-concentrated-lp.md) | TBD  | Documented | 20-60%     |

### DeFi — BTC (2 strategies)

| Strategy                                                     | File | Status     | Target APY |
| ------------------------------------------------------------ | ---- | ---------- | ---------- |
| [BTC Basis Trade (WBTC/cbBTC)](defi/btc-basis-trade.md)      | TBD  | Documented | 8-18%      |
| [BTC Lending Yield (multi-chain)](defi/btc-lending-yield.md) | TBD  | Documented | 3-15%      |

### DeFi — Multi-Chain / Cross-Chain (5 strategies)

| Strategy                                                                  | File | Status     | Target APY |
| ------------------------------------------------------------------------- | ---- | ---------- | ---------- |
| [Multi-Chain Lending Yield (SOR)](defi/multi-chain-lending-yield.md)      | TBD  | Documented | 5-12%      |
| [Cross-Chain Yield Arbitrage](defi/cross-chain-yield-arb.md)              | TBD  | Documented | 3-8%       |
| [L2 Basis Trade (low gas)](defi/l2-basis-trade.md)                        | TBD  | Documented | 12-25%     |
| [Cross-Chain SOR Rebalancing (meta)](defi/cross-chain-sor-rebalancing.md) | TBD  | Documented | +2-5%      |
| [Omnichain Transfers](defi/omnichain-transfers.md)                        | N/A  | Documented | N/A        |

### CeFi (4 strategies + 1 MM)

| Strategy                                           | File                         | Status        | Capital Target |
| -------------------------------------------------- | ---------------------------- | ------------- | -------------- |
| [Momentum](cefi/momentum.md)                       | `cefi_momentum.py`           | Code complete | TBD            |
| [Mean Reversion](cefi/mean-reversion.md)           | `mean_reversion_strategy.py` | Code complete | TBD            |
| [Cross-Exchange Arbitrage](cefi/cross-exchange.md) | `cross_exchange_strategy.py` | Code complete | TBD            |
| [Statistical Arbitrage](cefi/stat-arb.md)          | `stat_arb_strategy.py`       | Code complete | TBD            |
| [Market Making](cefi/market-making.md)             | TBD                          | Documented    | TBD            |

### TradFi (5 strategies + 1 MM)

| Strategy                                                 | File                                | Status        | Capital Target |
| -------------------------------------------------------- | ----------------------------------- | ------------- | -------------- |
| [ML Directional](tradfi/ml-directional.md)               | `tradfi_ml_directional_strategy.py` | Code complete | TBD            |
| [Options ML](tradfi/options-ml.md)                       | `options_ml_strategy.py`            | Code complete | TBD            |
| [TradFi Momentum](tradfi/tradfi-momentum.md)             | `tradfi_momentum.py`                | Code complete | TBD            |
| [Relative Volatility](tradfi/relative-volatility.md)     | `rel_vol_strategy.py`               | Code complete | TBD            |
| [Volatility Surface](tradfi/volatility-surface.md)       | `vol_surface_strategy.py`           | Code complete | TBD            |
| [Options Market Making](tradfi/market-making-options.md) | TBD                                 | Documented    | TBD            |

### Sports (6 strategies + 1 MM)

| Strategy                                                 | File                    | Status        | Capital Target |
| -------------------------------------------------------- | ----------------------- | ------------- | -------------- |
| [Arbitrage](sports/arbitrage.md)                         | `arbitrage.py`          | Code complete | TBD            |
| [Value Betting](sports/value-betting.md)                 | `value_betting.py`      | Code complete | TBD            |
| [Pre-Game ML](sports/pre-game-ml.md)                     | `ml_sports_strategy.py` | Code complete | TBD            |
| [Halftime ML](sports/halftime-ml.md)                     | `halftime_ml.py`        | Code complete | TBD            |
| [Odds Drift / CLV Capture](sports/odds-drift.md)         | TBD                     | Documented    | TBD            |
| [First-Half Prediction](sports/first-half-prediction.md) | TBD                     | Documented    | TBD            |
| [Market Making](sports/market-making.md)                 | `market_making.py`      | Documented    | TBD            |

**Cross-cutting:** [Staking Methods](sports/staking-methods.md) — Kelly (fractional, portfolio, venue-constrained),
Fixed, Percentage, Adaptive Daily

### Prediction Markets (1 strategy)

| Strategy                                             | File                         | Status        | Capital Target |
| ---------------------------------------------------- | ---------------------------- | ------------- | -------------- |
| [Prediction Arbitrage](prediction/prediction-arb.md) | `prediction_arb_strategy.py` | Code complete | TBD            |

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
