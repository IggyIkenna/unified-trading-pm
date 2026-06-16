---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# CeFi Momentum

> **Asset class:** CeFi **Strategy type:** Momentum **Strategy ID pattern:**
> `CEFI_{ASSET}_MOM_{INDICATOR}_{MODE}_{TIMEFRAME}`

## Overview

ML-driven momentum strategy for CeFi crypto perpetual futures (BTC, ETH, SOL). Uses swing_high/swing_low ML predictions
to generate directional signals, with MACD and RSI as supporting feature context. Supports both Same Candle Exit (SCE)
and Hold Until Flip (HUF) execution modes.

## Token / Position Flow

```
Start:  WALLET:USDT  (100% USDT margin)

Step 1 - ML PREDICTION: Receive swing_high/swing_low predictions from ML pipeline
Step 2 - DIRECTION MAP: Map prediction to direction via BaseStrategy.process_ml_predictions()
         - swing_high_pred=1 (high_breakout) -> LONG
         - swing_low_pred=-1 (low_reversion) -> LONG
         - swing_high_pred=-1 (high_reversion) -> SHORT
         - swing_low_pred=1 (low_breakout) -> SHORT
Step 3 - CONFIDENCE GATE: Only act when max(swing_high_conf, swing_low_conf) >= threshold (default 0.65)
Step 4 - ENTRY: Open perpetual position in signal direction
Step 5 - EXIT: SCE mode exits same candle; HUF mode holds until signal flips direction

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

| Feature           | Source Service     | SLA | Used For                        |
| ----------------- | ------------------ | --- | ------------------------------- |
| `swing_high_pred` | ml-service         | 5m  | Signal: direction determination |
| `swing_high_conf` | ml-service         | 5m  | Signal: confidence gating       |
| `swing_low_pred`  | ml-service         | 5m  | Signal: direction determination |
| `swing_low_conf`  | ml-service         | 5m  | Signal: confidence gating       |
| `macd`            | features-delta-one | 5m  | Context: signal metadata        |
| `macd_signal`     | features-delta-one | 5m  | Context: signal metadata        |
| `rsi`             | features-delta-one | 5m  | Context: signal metadata        |
| `momentum`        | features-delta-one | 5m  | Context: signal metadata        |

## PnL Attribution

| Component         | Settlement Type | Mechanism                                        |
| ----------------- | --------------- | ------------------------------------------------ |
| `directional_pnl` | Mark-to-market  | Price change in direction of position            |
| `funding_pnl`     | `FUNDING_8H`    | Funding rate payments received/paid on perpetual |
| `trading_fees`    | Per-trade       | Maker/taker fees on entry and exit               |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target   | Notes                                  |
| -------------------- | -------- | -------------------------------------- |
| Target annual return | TBD      |                                        |
| Target Sharpe ratio  | TBD      |                                        |
| Max drawdown         | 10%      | `max_drawdown_pct` in risk_config      |
| Max leverage         | 1x       | Single perpetual position              |
| Max position (BTC)   | $100,000 | `max_position_size_usd`                |
| Max position (SOL)   | $50,000  | Smaller due to higher volatility       |
| Stop loss            | 2-2.5%   | BTC/ETH: 2%, SOL: 2.5% (wider for vol) |
| Take profit          | 4-5%     | BTC/ETH: 4%, SOL: 5% (wider for vol)   |

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

- **Venues:** Binance Futures
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

- **Margin model:** Isolated margin on Binance Futures
- **Health factor threshold:** N/A (CeFi margin maintenance ratio)
- **Liquidation penalty:** Venue-dependent (Binance tiered)
- **Monitoring:** Per-candle via risk_config thresholds

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue           | Secret Name               | Testnet Available? | Notes           |
| --------------- | ------------------------- | ------------------ | --------------- |
| Binance Futures | `exec-{client}-binance-*` | Yes                | Futures testnet |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Binance Futures account with USDT margin
2. **Secret Manager:** `exec-{client}-binance-futures-api-key`, `exec-{client}-binance-futures-api-secret`
3. **Config:** New entry in strategy config YAML with client-specific params (asset, mode, thresholds)
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
- SCE vs HUF mode performance comparison
- Signal count and hit rate dashboard

## Testing Stage Status

| Stage        | Status  | Notes                                |
| ------------ | ------- | ------------------------------------ |
| MOCK         | Done    | Static seed data + paper execution   |
| HISTORICAL   | Done    | Backtested on BTC/ETH/SOL 5m candles |
| LIVE_MOCK    | Done    | Real market data + paper execution   |
| LIVE_TESTNET | Pending | Binance Futures testnet              |
| BATCH_REAL   | Done    | Config optimised per asset           |
| STAGING      | Pending |                                      |
| LIVE_REAL    | Pending |                                      |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/cefi_momentum.py`
- **Base class:** `strategy-service/strategy_service/engine/strategies/base_strategy.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
