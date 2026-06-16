---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# CeFi Mean Reversion

> **Asset class:** CeFi / TradFi (cross-asset) **Strategy type:** Mean Reversion **Strategy ID pattern:**
> `MEAN_REV_{ASSET}_V1`

## Overview

Z-score-based mean reversion strategy that enters positions when price deviates significantly from a rolling mean and
exits when price reverts. Supports CRYPTO (BTC, ETH, SOL on Binance Futures), EQUITY (SPY on NASDAQ), FX (6E Euro
futures on CME), and COMMODITY (CL crude on NYMEX). Optionally replaces the rolling mean with an ML-predicted mean for
improved signal quality.

## Token / Position Flow

```
Start:  WALLET:USDT or WALLET:USD  (100% cash margin)

Step 1 - PRICE UPDATE: Append close price to rolling window (deque, maxlen=lookback_period)
Step 2 - DATA GUARD: Check window is fully populated (default 20 bars) and std > 0
Step 3 - Z-SCORE: Compute zscore = (price - mean) / rolling_std
         - Statistical mode: mean = rolling_mean of window
         - ML mode: mean = ml_predicted_mean (from external model)
Step 4 - ENTRY CHECK:
         - zscore < -entry_z_score (default -2.0) -> ENTER_LONG (price far below mean)
         - zscore > +entry_z_score (default +2.0) -> ENTER_SHORT (price far above mean)
Step 5 - EXIT CHECK: |zscore| < exit_z_score (default 0.5) -> EXIT (price reverted)
Step 6 - HOLD: If no entry or exit condition met -> HOLD

Wallet after deploy:
  - {VENUE}:{TYPE}:{ASSET} = 1x (long or short, or flat)
```

## Instruments

| Instrument Key                           | Venue           | Type    | Role              | Asset Class |
| ---------------------------------------- | --------------- | ------- | ----------------- | ----------- |
| `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` | Binance Futures | Perp    | BTC crypto        | CRYPTO      |
| `BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN` | Binance Futures | Perp    | ETH crypto        | CRYPTO      |
| `BINANCE-FUTURES:PERPETUAL:SOL-USDT@LIN` | Binance Futures | Perp    | SOL crypto        | CRYPTO      |
| `NASDAQ:EQUITY:SPY`                      | NASDAQ          | Equity  | S&P 500 ETF       | EQUITY      |
| `CME:FUTURES:6E`                         | CME             | Futures | Euro FX futures   | FX          |
| `NYMEX:FUTURES:CL`                       | NYMEX           | Futures | Crude oil futures | COMMODITY   |

## Key Features Consumed

| Feature             | Source Service     | SLA | Used For                                 |
| ------------------- | ------------------ | --- | ---------------------------------------- |
| `rolling_mean`      | (internal)         | --  | Baseline: mean for z-score (stat mode)   |
| `rolling_std`       | (internal)         | --  | Baseline: standard deviation for z-score |
| `ml_predicted_mean` | ml-service         | 5m  | Signal: replaces rolling_mean in ML mode |
| `close` (price)     | features-delta-one | 5m  | Input: current price for z-score calc    |

**Note:** The rolling mean and standard deviation are computed internally from a `deque` of close prices
(`lookback_period` bars). Feature subscriptions are configurable via `feature_subscriptions` in config.

## PnL Attribution

| Component         | Settlement Type | Mechanism                                |
| ----------------- | --------------- | ---------------------------------------- |
| `directional_pnl` | Mark-to-market  | Price reversion toward mean after entry  |
| `funding_pnl`     | `FUNDING_8H`    | Funding rate on perpetuals (CRYPTO only) |
| `trading_fees`    | Per-trade       | Maker/taker fees on entry and exit       |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target    | Notes                                                     |
| -------------------- | --------- | --------------------------------------------------------- |
| Target annual return | TBD       |                                                           |
| Target Sharpe ratio  | TBD       |                                                           |
| Max drawdown         | TBD       |                                                           |
| Max leverage         | 1x        | Single instrument position                                |
| Capital scalability  | TBD       |                                                           |
| Entry threshold      | 2.0 sigma | `entry_z_score` default; configurable per instrument      |
| Exit threshold       | 0.5 sigma | `exit_z_score` default; position closes on mean reversion |
| Lookback window      | 20 bars   | `lookback_period`; Oil uses 10 bars (faster mean)         |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> signal      | 1ms        | 5ms        |                     |
| Signal -> instruction  | 5ms        | 20ms       |                     |
| Instruction -> fill    | 50ms       | 200ms      |                     |
| **End-to-end**         | **156ms**  | **725ms**  | **No**              |

## Execution Details

- **Venues:** Binance Futures (CRYPTO), NASDAQ (EQUITY), CME (FX), NYMEX (COMMODITY)
- **Order types:** Market for entries, Limit for exits on reversion
- **Atomic execution required?** No -- single-leg position
- **Rebalancing:** Event-driven on each price bar; exit triggered when z-score crosses exit threshold
- **Gas budget:** N/A (all CeFi/TradFi venues)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern       | Exposure Type  | Used For              |
| ------------------------ | -------------- | --------------------- |
| `{VENUE}:{TYPE}:{ASSET}` | Notional value | Position size monitor |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold          | Action on Breach |
| --------------- | ----------- | ------------------ | ---------------- |
| `delta`         | Yes         | entry/exit z-score | Entry or exit    |
| `funding`       | No          | --                 | --               |
| `basis`         | No          | --                 | --               |
| `protocol_risk` | No          | --                 | --               |
| `liquidity`     | No          | --                 | --               |

## Margin & Liquidation

- **Margin model:** Isolated (CeFi perps), Reg-T (TradFi equities/futures)
- **Health factor threshold:** N/A (venue-specific maintenance margin)
- **Liquidation penalty:** Venue-dependent
- **Monitoring:** Z-score checked on every price update

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue           | Secret Name               | Testnet Available? | Notes         |
| --------------- | ------------------------- | ------------------ | ------------- |
| Binance Futures | `exec-{client}-binance-*` | Yes                |               |
| NASDAQ (IBKR)   | `exec-{client}-ibkr-*`    | Yes (paper)        | Paper trading |
| CME (IBKR)      | `exec-{client}-ibkr-*`    | Yes (paper)        | Paper trading |
| NYMEX (IBKR)    | `exec-{client}-ibkr-*`    | Yes (paper)        | Paper trading |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Venue account per asset class (Binance for crypto, IBKR for TradFi)
2. **Secret Manager:** `exec-{client}-{venue}-api-key`, `exec-{client}-{venue}-api-secret`
3. **Config:** New `MeanReversionConfig` entry with `strategy_id`, `instrument_id`, `asset_classes`, thresholds
4. **Position isolation:** One strategy instance per client per instrument
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

- Z-score time series with entry/exit threshold lines
- Rolling mean vs price overlay chart
- ML predicted mean vs statistical mean comparison (when ML mode enabled)
- Signal action breakdown (ENTER_LONG / ENTER_SHORT / EXIT / HOLD histogram)

## Testing Stage Status

| Stage        | Status  | Notes                                        |
| ------------ | ------- | -------------------------------------------- |
| MOCK         | Done    | Static seed data + paper execution           |
| HISTORICAL   | Done    | Backtested across CRYPTO/EQUITY/FX/COMMODITY |
| LIVE_MOCK    | Done    | Real market data + paper execution           |
| LIVE_TESTNET | Pending |                                              |
| BATCH_REAL   | Done    | Config optimised per asset class             |
| STAGING      | Pending |                                              |
| LIVE_REAL    | Pending |                                              |

## References

- **Strategy implementation:**
  `strategy-service/strategy_service/engine/strategies/mean_reversion/mean_reversion_strategy.py`
- **Config type:** `strategy-service/strategy_service/config.py` (`MeanReversionConfig`)
- **Signal type:** `MeanReversionSignal` dataclass in same file
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
