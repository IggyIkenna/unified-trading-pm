---
scope: [engineer, admin]
---

# Active DeFi Market Making (ML-Driven Concentrated LP)

> **Asset class:** DeFi **Strategy type:** Active Market Making via ML-Driven Concentrated LP Rebalancing **Strategy ID
> pattern:** `DEFI_{CHAIN}_ACTIVE_LP_{PROTOCOL}_{PAIR}_SCE_1H`

## Overview

Provide concentrated liquidity on AMM DEXs (Uniswap V3, Raydium CLMM, Orca Whirlpools) with ML-driven rebalancing to
minimise impermanent loss. Unlike the passive AmmLPStrategy which rebalances only when price drifts near the range edge,
this strategy uses ML predictions from three feature services to decide WHEN and HOW to adjust the LP range:

- **features-delta-one:** momentum score, microstructure score, price trend
- **features-volatility:** vol regime, VRP, realized vol, implied vol
- **features-onchain:** pool volume, TVL, current tick, fee APY, liquidity density

The ML model outputs a rebalance confidence score, direction forecast, and optimal tick width. When confidence exceeds
the threshold AND the cost-benefit gate passes (IL savings > gas cost multiplied by minimum ratio), the strategy emits
one of four rebalance actions: widen range, narrow range, shift center, or full exit.

## How This Fits the Unified Trading System

Same event-driven architecture as all DeFi strategies. Strategy receives features and ML predictions, decides on LP
range adjustments, and emits instructions. Strategy NEVER reads pool state directly.

```
features-onchain-service (pool_volume, pool_tvl, current_tick, fee_apy, liquidity_density)
features-volatility-service (vol_regime, vrp, realized_vol_1h, implied_vol)
features-delta-one-service (momentum_score, microstructure_score, price_trend)
ml-service (rebalance_confidence, direction, vol_forecast, optimal_width)
  -> strategy-service receives features + ML predictions
    -> ActiveDeFiMMStrategy.evaluate_rebalance()
      -> emit StrategyInstruction (ADD_LIQUIDITY / REMOVE_LIQUIDITY / SWAP)
```

## Rebalance Decision Engine

| Decision     | Trigger                                                     | Action                                        |
| ------------ | ----------------------------------------------------------- | --------------------------------------------- |
| Full exit    | IL > tolerance AND ML confidence >= threshold               | REMOVE_LIQUIDITY + COLLECT_FEES               |
| Shift range  | Price outside current range                                 | REMOVE + SWAP + ADD at new ML-adjusted center |
| Widen range  | ML confidence high + proposed width >20% wider than current | REMOVE + SWAP + ADD at wider range            |
| Narrow range | ML confidence high + proposed width >20% narrower           | REMOVE + SWAP + ADD at narrower range         |
| Hold         | None of the above                                           | No action (earning fees in current range)     |

### Gas-Aware Cost-Benefit Gate

Every rebalance must pass: `IL_savings > gas_cost * min_il_savings_ratio`

This prevents unnecessary rebalancing in low-IL scenarios where gas would eat the savings. On Solana (gas ~$0.60), the
ratio is lower (1.5x) enabling more frequent rebalancing. On Ethereum L1 (gas ~$15-50), the ratio is higher (2.0x).

### Vol-Adaptive Range Width

| Vol Regime | Realized Vol | Width Multiplier | Effect                          |
| ---------- | ------------ | ---------------- | ------------------------------- |
| HIGH (>=2) | >80%         | 1.8x             | Wider range, fewer rebalances   |
| NORMAL     | 20-80%       | 1.0x             | Base width                      |
| LOW (<=0)  | <20%         | 0.6x             | Narrower range, more fee income |

ML vol forecast overrides heuristic when available and confident.

### Momentum-Based Center Shift

When ML predicts directional movement with confidence, the range center shifts ahead of the expected move. This
positions the LP to earn fees in the zone where price is heading, rather than trailing behind.

Shift = `momentum_shift_ticks * (0.6 * ml_direction + 0.4 * momentum_score)`

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC

Step 1 - SWAP: Convert 50% of USDC to base token (ETH/SOL)
Step 2 - ADD_LIQUIDITY: Deploy to ML-adjusted tick range [tick_lower, tick_upper]

On ML-driven rebalance:
Step 3 - REMOVE_LIQUIDITY: Withdraw from current range
Step 4 - SWAP: Adjust token ratio for new range (~5%)
Step 5 - ADD_LIQUIDITY: Deploy at new ML-adjusted range

On exit:
Step 6 - REMOVE_LIQUIDITY: Full withdrawal
Step 7 - COLLECT_FEES: Harvest remaining accrued fees
```

## Instruments

| Instrument Key                     | Venue   | Type | Role             |
| ---------------------------------- | ------- | ---- | ---------------- |
| `UNISWAPV3-ETHEREUM:POOL:ETH-USDC` | Uniswap | Pool | ETH/USDC LP      |
| `RAYDIUM-SOLANA:POOL:SOL-USDC`     | Raydium | Pool | SOL/USDC LP      |
| `WALLET:SPOT_ASSET:ETH`            | Wallet  | Spot | Base token (EVM) |
| `WALLET:SPOT_ASSET:SOL`            | Wallet  | Spot | Base token (SOL) |
| `WALLET:SPOT_ASSET:USDC`           | Wallet  | Spot | Quote token      |

## Key Features Consumed

| Feature                | Source Service      | SLA | Used For                                |
| ---------------------- | ------------------- | --- | --------------------------------------- |
| `pool_volume`          | features-onchain    | 60s | Fee APY estimation                      |
| `pool_tvl`             | features-onchain    | 60s | Position sizing, concentration risk     |
| `current_tick`         | features-onchain    | 5s  | Range boundary check, rebalance trigger |
| `fee_apy`              | features-onchain    | 60s | Deploy/hold decision                    |
| `liquidity_density`    | features-onchain    | 60s | Optimal range placement                 |
| `momentum_score`       | features-delta-one  | 60s | Range center shift direction            |
| `microstructure_score` | features-delta-one  | 60s | Market regime assessment                |
| `price_trend`          | features-delta-one  | 60s | Directional bias                        |
| `vol_regime`           | features-volatility | 60s | Range width sizing (widen/narrow)       |
| `realized_vol_1h`      | features-volatility | 60s | Range width sizing                      |
| `vrp`                  | features-volatility | 60s | Risk premium assessment                 |
| `implied_vol`          | features-volatility | 60s | Forward-looking vol for range sizing    |

## ML Predictions Consumed

| Prediction             | Source     | Used For                                   |
| ---------------------- | ---------- | ------------------------------------------ |
| `rebalance_confidence` | ml-service | Gate: must exceed threshold to act         |
| `direction`            | ml-service | Range center shift (+1 = up, -1 = down)    |
| `vol_forecast`         | ml-service | Forward vol for range width sizing         |
| `optimal_width`        | ml-service | Direct ML-suggested tick width (overrides) |

## Configuration (Two Presets)

### ETH/USDC on Uniswap V3 (Ethereum)

- Fee tier: 500 (0.05%)
- Base range: 200 ticks (~2%)
- ML confidence threshold: 0.65
- IL tolerance: 3%
- Gas cost: $15 (Ethereum L1)
- IL savings ratio: 2.0x

### SOL/USDC on Raydium (Solana)

- Fee tier: 3000 (0.3%)
- Base range: 300 ticks (~3%)
- ML confidence threshold: 0.60
- IL tolerance: 4%
- Gas cost: $0.60 (Solana)
- IL savings ratio: 1.5x

## PnL Attribution

| Component               | Settlement Type   | Mechanism                                  |
| ----------------------- | ----------------- | ------------------------------------------ |
| `fee_income_pnl`        | LP fee accrual    | Fees earned from swaps within active range |
| `il_pnl`                | Mark-to-market    | Concentrated IL from price divergence      |
| `rebalance_cost_pnl`    | Per-rebalance     | Gas cost of REMOVE + SWAP + ADD cycle      |
| `range_utilization_pct` | Monitoring metric | % of candles where price was within range  |

**Source of truth:** `net_pnl = cumulative_fee_pnl + cumulative_il_pnl - cumulative_rebalance_cost`

## Risk Profile

| Metric               | ETH/USDC Target | SOL/USDC Target | Notes                                |
| -------------------- | --------------- | --------------- | ------------------------------------ |
| Target annual return | 15-40%          | 25-60%          | Fee income minus IL and gas          |
| Target Sharpe ratio  | 1.5-2.5         | 1.2-2.0         | Higher with good ML predictions      |
| Max drawdown         | 15%             | 25%             | Primarily from IL during large moves |
| Max leverage         | 1x              | 1x              | Fully funded, no leverage            |
| Capital scalability  | $10M+           | $2M per pool    | Ethereum pools have deeper TVL       |

## Risk & Exposure Subscriptions

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold                | Action on Breach             |
| ------------------ | ----------- | ------------------------ | ---------------------------- |
| `impermanent_loss` | YES         | IL > il_tolerance_pct    | ML-gated exit or range shift |
| `protocol_risk`    | YES         | Smart contract exploit   | Emergency exit               |
| `liquidity`        | YES         | Pool TVL drops > 30% 24h | Exit position                |
| `concentration`    | YES         | Our share of TVL > 5%    | Reduce position size         |
| `gas_spike`        | YES         | Gas > 3x normal          | Delay non-critical rebalance |

## Testing Stage Status

| Stage        | Status  | Notes                                               |
| ------------ | ------- | --------------------------------------------------- |
| MOCK         | Pending | Need ML prediction mocks + pool state simulation    |
| HISTORICAL   | Pending | Backtest with historical pool data + feature replay |
| LIVE_MOCK    | Pending | Feature service integration test                    |
| LIVE_TESTNET | Pending | Uniswap V3 Sepolia / Raydium devnet                 |
| LIVE_REAL    | Pending | All above + ML model validated + capital deployed   |

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/active_defi_mm.py`
- **Config ETH/USDC:** `strategy-service/strategy_service/configs/active_lp_eth_usdc.yaml`
- **Config SOL/USDC:** `strategy-service/strategy_service/configs/active_lp_sol_usdc.yaml`
- **Passive LP (base):** `strategy-service/strategy_service/engine/strategies/defi_amm_lp.py`
- **Tick math:** Shared with AmmLPStrategy (`compute_concentrated_il`, `tick_to_price`, etc.)
- **Base class:** `DeFiBaseStrategy` (tiered rebalancing, health factor, SOR)
