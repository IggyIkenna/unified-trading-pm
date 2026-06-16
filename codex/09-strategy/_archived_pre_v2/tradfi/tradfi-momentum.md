---
scope: [engineer, admin]
---

# TradFi Momentum

> **Asset class:** TradFi **Strategy type:** Momentum **Strategy ID pattern:** `TRADFI_SPY_MOM_MACD_{SCE|HUF}_5M`

## Overview

ML-driven momentum strategy for TradFi equities (primarily SPY). Uses swing_high and swing_low ML predictions to
generate directional signals, with market-hours awareness via instruments-service trading calendar lookups. Supports two
execution modes: same-candle-exit (SCE) for intraday and hold-until-flip (HUF) for swing trading.

## Token / Position Flow

```
Start:  BROKER:EQUITY:USD  (100% USD)

Step 1 - MARKET_HOURS_CHECK: Verify timestamp is within instrument trading hours
         (instruments-service SSOT, fallback to hardcoded NYSE hours)
Step 2 - ML_PREDICTION: Process swing_high_pred/swing_low_pred from ML model
Step 3 - DIRECTION: Map ML prediction to LONG/SHORT/FLAT via direction_mapping:
         high_breakout/low_reversion -> LONG, high_reversion/low_breakout -> SHORT
Step 4 - HUF_FILTER (if hold_until_flip): Suppress signal if direction == last_direction
Step 5 - EXECUTE: Emit signal with direction, price, confidence

Wallet after deploy:
  - NASDAQ:EQUITY:SPY = position (LONG or SHORT)
  - Sized by max_position_size_usd (default $100K)
```

## Instruments

| Instrument Key      | Venue  | Type   | Role            |
| ------------------- | ------ | ------ | --------------- |
| `NASDAQ:EQUITY:SPY` | NASDAQ | Equity | Trade target    |
| `BROKER:EQUITY:USD` | Broker | Cash   | Initial capital |

## Key Features Consumed

| Feature             | Source Service      | SLA | Used For                              |
| ------------------- | ------------------- | --- | ------------------------------------- |
| `swing_high_pred`   | features-tradfi-svc | 5m  | Signal: high breakout/reversion       |
| `swing_low_pred`    | features-tradfi-svc | 5m  | Signal: low breakout/reversion        |
| `swing_high_conf`   | features-tradfi-svc | 5m  | Confidence filtering (threshold 0.65) |
| `swing_low_conf`    | features-tradfi-svc | 5m  | Confidence filtering (threshold 0.65) |
| `is_trading_day`    | instruments-service | 1d  | Market hours gate                     |
| `regular_open_utc`  | instruments-service | 1d  | Market hours gate                     |
| `regular_close_utc` | instruments-service | 1d  | Market hours gate                     |

## PnL Attribution

| Component     | Settlement Type | Mechanism                                |
| ------------- | --------------- | ---------------------------------------- |
| `directional` | MARK_TO_MARKET  | Price movement in direction of signal    |
| `stop_loss`   | STOP_TRIGGER    | Exit at 1.5% loss (tighter for equities) |
| `take_profit` | TP_TRIGGER      | Exit at 3.0% gain                        |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target | Notes                                       |
| -------------------- | ------ | ------------------------------------------- |
| Target annual return | 15-25% | Depends on ML model accuracy                |
| Target Sharpe ratio  | 1.5    |                                             |
| Max drawdown         | 8%     | Enforced by max_drawdown_pct config         |
| Max leverage         | 1x     | Long/short equity, no leverage              |
| Capital scalability  | $5M    | SPY is highly liquid; minimal market impact |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> signal      | 50ms       | 200ms      |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 50ms       | 200ms      |                     |
| **End-to-end**         | **210ms**  | **950ms**  | **No**              |

## Execution Details

- **Venues:** NASDAQ (via broker)
- **Order types:** Market
- **Atomic execution required?** No -- single instrument
- **Rebalancing:** Per 5-minute candle; HUF mode holds until direction flips
- **Gas budget:** N/A (equity market, standard commissions)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern  | Exposure Type  | Used For              |
| ------------------- | -------------- | --------------------- |
| `NASDAQ:EQUITY:SPY` | Position value | Track equity exposure |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold     | Action on Breach     |
| --------------- | ----------- | ------------- | -------------------- |
| `delta`         | Yes         | 100% notional | Single instrument    |
| `funding`       | No          | --            | --                   |
| `basis`         | No          | --            | --                   |
| `protocol_risk` | No          | --            | --                   |
| `liquidity`     | No          | --            | SPY is highly liquid |
| `drawdown`      | Yes         | 8%            | Flatten position     |

## Margin & Liquidation

- **Margin model:** Reg-T (50% initial, 25% maintenance for equities)
- **Health factor threshold:** N/A (no leverage used)
- **Liquidation penalty:** Broker margin call rules
- **Monitoring:** Per-candle equity check against max_drawdown_pct

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue  | Secret Name          | Testnet Available? | Notes      |
| ------ | -------------------- | ------------------ | ---------- |
| NASDAQ | exec-{client}-nasdaq | Yes (paper)        | Broker API |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Brokerage account with equity trading permissions
2. **Secret Manager:** Per-client secrets: `exec-{client}-nasdaq-equity`
3. **Config:** New entry in strategy config YAML with client-specific risk_config params
4. **Position isolation:** One strategy instance per client
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

- Swing high/low prediction confidence overlay on price chart
- Signal direction timeline (LONG/SHORT/FLAT transitions)
- Market hours indicator with instrument-service trading calendar

## Testing Stage Status

| Stage        | Status  | Notes                                           |
| ------------ | ------- | ----------------------------------------------- |
| MOCK         | Done    | Static candle fixtures + ML prediction stubs    |
| HISTORICAL   | Done    | SPY 5m candle backtest with historical features |
| LIVE_MOCK    | Done    | Real market data + paper execution              |
| LIVE_TESTNET | N/A     | Paper trading via broker API                    |
| BATCH_REAL   | Pending | Historical replay with optimized config         |
| STAGING      | Pending | Paper trading with real ML predictions          |
| LIVE_REAL    | Pending | Production execution                            |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/tradfi_momentum.py`
- **Market hours utils:** `strategy-service/strategy_service/engine/core/market_hours_utils.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
