---
scope: [engineer, admin]
---

# CeFi ML Directional

> **Asset class:** CeFi **Strategy type:** ML Directional **Strategy ID pattern:**
> `CEFI_{ASSET}_ML_DIR_{MODE}_{TIMEFRAME}`

## Overview

ML-driven directional strategy for CeFi crypto instruments (BTC, ETH, SOL) that extends the momentum approach with
crypto-specific features: funding rates, orderbook imbalance, volume profile, and open interest. Uses the same
swing_high/swing_low ML prediction framework as CeFi Momentum but enriches signals with deeper crypto microstructure
data. Trades on Binance spot and Hyperliquid perpetuals.

## Token / Position Flow

```
Start:  WALLET:USDT  (100% USDT margin)

Step 1 - ML PREDICTION: Receive swing_high/swing_low predictions from ML pipeline (model: cefi_{asset}_swing_v1)
Step 2 - DIRECTION MAP: Map prediction to direction via BaseStrategy.process_ml_predictions()
         - swing_high_pred=1 (high_breakout) -> LONG
         - swing_low_pred=-1 (low_reversion) -> LONG
         - swing_high_pred=-1 (high_reversion) -> SHORT
         - swing_low_pred=1 (low_breakout) -> SHORT
Step 3 - CONFIDENCE GATE: Only act when max(swing_high_conf, swing_low_conf) >= threshold (default 0.65)
Step 4 - CRYPTO FEATURE ENRICHMENT: Attach funding_rate, orderbook_imbalance, volume_profile, open_interest to signal
Step 5 - ENTRY: Open perpetual position in signal direction
Step 6 - EXIT: SCE mode exits same candle; HUF mode holds until signal flips direction

Wallet after deploy:
  - BINANCE-FUTURES:PERPETUAL:{ASSET}-USDT@LIN = 1x (long or short)
  - USDT margin held at venue
```

## Instruments

| Instrument Key                           | Venue           | Type       | Role            |
| ---------------------------------------- | --------------- | ---------- | --------------- |
| `WALLET:USDT`                            | Wallet          | Stablecoin | Initial capital |
| `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` | Binance Futures | Perp       | BTC variant     |
| `BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN` | Binance Futures | Perp       | ETH variant     |
| `BINANCE-FUTURES:PERPETUAL:SOL-USDT@LIN` | Binance Futures | Perp       | SOL variant     |

## Key Features Consumed

| Feature                 | Source Service     | SLA | Used For                               |
| ----------------------- | ------------------ | --- | -------------------------------------- |
| `swing_high_pred`       | ml-service         | 5m  | Signal: direction determination        |
| `swing_high_conf`       | ml-service         | 5m  | Signal: confidence gating              |
| `swing_low_pred`        | ml-service         | 5m  | Signal: direction determination        |
| `swing_low_conf`        | ml-service         | 5m  | Signal: confidence gating              |
| `funding_rate`          | features-delta-one | 10s | Context: crypto microstructure         |
| `funding_rate_8h`       | features-delta-one | 8h  | Context: 8h settlement rate            |
| `orderbook_imbalance`   | features-delta-one | 1s  | Context: buy/sell pressure             |
| `orderbook_depth_ratio` | features-delta-one | 1s  | Context: depth asymmetry               |
| `volume_profile_vwap`   | features-delta-one | 5m  | Context: volume-weighted average price |
| `volume_profile_poc`    | features-delta-one | 5m  | Context: point of control              |
| `volume_delta`          | features-delta-one | 5m  | Context: net buy/sell volume           |
| `open_interest`         | features-delta-one | 5m  | Context: market participation          |
| `open_interest_change`  | features-delta-one | 5m  | Context: OI delta                      |
| `liquidation_volume`    | features-delta-one | 5m  | Context: liquidation cascade risk      |

## PnL Attribution

| Component         | Settlement Type | Mechanism                                        |
| ----------------- | --------------- | ------------------------------------------------ |
| `directional_pnl` | Mark-to-market  | Price change in direction of position            |
| `funding_pnl`     | `FUNDING_8H`    | Funding rate payments received/paid on perpetual |
| `trading_fees`    | Per-trade       | Maker/taker fees on entry and exit               |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target   | Notes                             |
| -------------------- | -------- | --------------------------------- |
| Target annual return | TBD      |                                   |
| Target Sharpe ratio  | TBD      |                                   |
| Max drawdown (BTC)   | 10%      | `max_drawdown_pct` in risk_config |
| Max drawdown (ETH)   | 8%       | Tighter for ETH                   |
| Max drawdown (SOL)   | 12%      | Wider for SOL volatility          |
| Max leverage         | 1x       | Single perpetual position         |
| Max position (BTC)   | $100,000 | `max_position_size_usd`           |
| Max position (ETH)   | $100,000 | `max_position_size_usd`           |
| Max position (SOL)   | $50,000  | Smaller due to higher volatility  |
| Stop loss            | 2-2.5%   | BTC/ETH: 2%, SOL: 2.5%            |
| Take profit          | 4-5%     | BTC/ETH: 4%, SOL: 5%              |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> ML pred     | 200ms      | 1s         |                     |
| ML pred -> signal      | 5ms        | 20ms       |                     |
| Signal -> instruction  | 5ms        | 20ms       |                     |
| Instruction -> fill    | 50ms       | 200ms      |                     |
| **End-to-end**         | **360ms**  | **1.7s**   | **No**              |

## Execution Details

- **Venues:** Binance Futures, Hyperliquid
- **Order types:** Market (SCE mode), Limit (HUF mode entry)
- **Atomic execution required?** No -- single-leg position
- **Rebalancing:** SCE: every candle (5m default). HUF: only on signal flip
- **Gas budget:** N/A (CeFi)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern                           | Exposure Type  | Used For              |
| -------------------------------------------- | -------------- | --------------------- |
| `BINANCE-FUTURES:PERPETUAL:{ASSET}-USDT@LIN` | Notional value | Position size monitor |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold     | Action on Breach |
| --------------- | ----------- | ------------- | ---------------- |
| `delta`         | Yes         | stop_loss_pct | Close position   |
| `funding`       | No          | --            | --               |
| `basis`         | No          | --            | --               |
| `protocol_risk` | No          | --            | --               |
| `liquidity`     | No          | --            | --               |

## Margin & Liquidation

- **Margin model:** Isolated margin on Binance Futures / Hyperliquid
- **Health factor threshold:** N/A (CeFi margin maintenance ratio)
- **Liquidation penalty:** Venue-dependent
- **Monitoring:** Per-candle via risk_config thresholds

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue           | Secret Name                   | Testnet Available? | Notes           |
| --------------- | ----------------------------- | ------------------ | --------------- |
| Binance Futures | `exec-{client}-binance-*`     | Yes                | Futures testnet |
| Hyperliquid     | `exec-{client}-hyperliquid-*` | Yes                | Testnet         |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Binance Futures and/or Hyperliquid account with USDT margin
2. **Secret Manager:** `exec-{client}-{venue}-api-key`, `exec-{client}-{venue}-api-secret`
3. **Config:** New entry with `strategy_id`, `asset_class=CRYPTO`, `ml_model_id`, feature flags
4. **Position isolation:** One strategy instance per client per asset
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes            | Restart?        |
| ----------------- | ----------------------- | --------------- |
| strategy-service  | New config entry in GCS | No (hot-reload) |
| execution-service | New client routing rule | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Swing prediction confidence overlay on price chart
- Crypto feature heatmap (funding rate, OI change, orderbook imbalance)
- Liquidation volume spike alerts
- SCE vs HUF mode performance comparison

## Testing Stage Status

| Stage        | Status  | Notes                                         |
| ------------ | ------- | --------------------------------------------- |
| MOCK         | Done    | Static seed data + paper execution            |
| HISTORICAL   | Done    | Backtested on BTC/ETH/SOL 5m candles          |
| LIVE_MOCK    | Done    | Real market data + paper execution            |
| LIVE_TESTNET | Pending | Binance Futures testnet + Hyperliquid testnet |
| BATCH_REAL   | Done    | Config optimised per asset                    |
| STAGING      | Pending |                                               |
| LIVE_REAL    | Pending |                                               |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/cefi_ml_directional.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/base_strategy.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
