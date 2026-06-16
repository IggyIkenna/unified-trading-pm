---
scope: [engineer, admin]
---

# DeFi Liquidation Cascade Capture

> **Asset class:** DeFi **Strategy type:** Event-Driven Collateral Capture (post-liquidation discount) **Strategy ID
> pattern:** `DEFI_ETH_LIQ_CAPTURE_SCE_1H`

## Overview

Monitors liquidation cascades on Aave V3 and other lending protocols. When cascading liquidations push collateral asset
prices below fair value, the strategy buys discounted collateral (WETH, WBTC, wstETH) via DEX in controlled scale-in
tranches. Captures the spread between post-liquidation market price and fair value as the market recovers.

This is a pure event-driven strategy -- it sits idle until a liquidation cascade is detected, then acts quickly with
time-sensitive (urgency=HIGH) execution.

## Signal Pipeline

### Features Consumed

| Feature                            | Source Service            | Purpose                                                         |
| ---------------------------------- | ------------------------- | --------------------------------------------------------------- |
| `liquidation_cluster_density`      | features-cross-instrument | Measures concentration of positions near liquidation thresholds |
| `liquidation_band_prediction`      | features-cross-instrument | ML prediction of further liquidation likelihood                 |
| `aave_avg_health_factor`           | features-onchain          | Average health factor across major Aave positions               |
| `price_discount_to_fair_value_pct` | features-onchain          | Current discount of collateral prices vs oracle fair value      |

### Signal Flow

```
features-cross-instrument   features-onchain
  (cluster density)           (health factors)
         \                       /
          v                     v
      LiquidationCaptureStrategy
              |
         DeFiSignal
              |
     SWAP instructions (urgency=HIGH)
              |
         execution-service
```

## Position Flow

### Entry (Scale-In Tranches)

```
Cascade detected  -->  Wait for subsiding  -->  Tranche 1: SWAP USDC -> WETH
                                            -->  Tranche 2: SWAP USDC -> WBTC
                                            -->  Tranche 3: SWAP USDC -> WSTETH
                                            (each tranche = max_position / tranche_count)
```

### Exit

- **Normal exit:** Sell captured collateral back to USDC once prices recover to fair value
- **Circuit breaker:** If discount exceeds `cascade_depth_limit` (15%), exit all positions immediately
- **Emergency exit:** Triggered by rebalancing threshold breach

## Risk Controls

| Control                | Parameter                    | Default  |
| ---------------------- | ---------------------------- | -------- |
| Max position per asset | `max_position_per_asset_usd` | $100,000 |
| Max total exposure     | `max_total_exposure_usd`     | $500,000 |
| Scale-in tranches      | `tranche_count`              | 3        |
| Circuit breaker depth  | `cascade_depth_limit`        | 15%      |
| Min discount to buy    | `min_discount_pct`           | 3%       |
| Health factor watch    | `health_factor_watch`        | 1.15     |

### Why Scale-In

Liquidation cascades can deepen unpredictably. Buying in tranches (never all-in) limits exposure if the cascade
continues. Each tranche is `max_position_per_asset_usd / tranche_count`, and the strategy tracks total exposure across
all captured assets to stay under `max_total_exposure_usd`.

### Circuit Breaker

If the price discount to fair value exceeds `cascade_depth_limit`, the cascade is dangerously deep (systemic event,
oracle failure, or protocol exploit). The circuit breaker exits all positions immediately and disables further captures
until the cascade subsides.

## Configuration

Config file: `strategy-service/configs/liquidation_capture_eth.yaml`

Factory function: `create_liquidation_capture_eth_strategy()` in
`strategy_service/engine/strategies/liquidation_capture.py`

Registered in `batch_utils.py` as `LIQUIDATION_CAPTURE`.

## Execution

All SWAP instructions are emitted with `urgency: HIGH` in metadata, signalling execution-service to prioritise
time-sensitive fills. Smart order routing is enabled across Uniswap V3, Curve, and 1inch for best execution on
potentially illiquid post-liquidation markets.

## Key Assumptions

1. Liquidation cluster features are available from features-cross-instrument-service with <5 min latency
2. Health factor data from features-onchain-service is current (block-level or near-block-level)
3. Post-liquidation discounts are transient (typically recover within 1-4 hours)
4. DEX liquidity is sufficient even during cascades (may need aggregator routing)
