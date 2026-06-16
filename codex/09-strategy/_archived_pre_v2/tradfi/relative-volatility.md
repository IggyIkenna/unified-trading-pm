---
scope: [engineer, admin]
---

# Relative Volatility

> **Asset class:** Cross-Asset (CeFi) **Strategy type:** Mean Reversion **Strategy ID pattern:** `QUANT_REL_VOL_BTC_ETH`

## Overview

Relative volatility strategy that trades the ratio of realized volatility between two instruments (e.g. BTC vs ETH
perpetuals). When the z-score of the volatility ratio diverges beyond a threshold, the strategy goes long vol on the
"cheap" leg and short vol on the "rich" leg. Exits when the z-score reverts below a lower threshold. This is a
statistical arbitrage on the mean-reverting nature of cross-instrument volatility relationships.

## Token / Position Flow

```
Start:  WALLET:USDT  (100% USDT)

Step 1 - OBSERVE: Consume relative_vol_ratio and relative_vol_zscore from CrossInstrumentFeatures
Step 2 - ENTRY CHECK:
         zscore > +2.0 -> A is rich (ENTER_LONG_B): short vol A, long vol B
         zscore < -2.0 -> A is cheap (ENTER_LONG_A): long vol A, short vol B
Step 3 - EXIT CHECK: |zscore| < 0.5 -> EXIT position
Step 4 - HOLD: zscore between -2.0 and +2.0 with no position -> HOLD

Wallet after deploy (ENTER_LONG_A example):
  - BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN = long position (vol exposure)
  - BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN = short position (vol exposure)
```

## Instruments

| Instrument Key                           | Venue           | Type       | Role               |
| ---------------------------------------- | --------------- | ---------- | ------------------ |
| `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` | Binance Futures | Perpetual  | Instrument A (BTC) |
| `BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN` | Binance Futures | Perpetual  | Instrument B (ETH) |
| `WALLET:USDT`                            | Wallet          | Stablecoin | Initial capital    |

## Key Features Consumed

| Feature               | Source Service            | SLA | Used For                               |
| --------------------- | ------------------------- | --- | -------------------------------------- |
| `relative_vol_ratio`  | features-cross-instrument | 10s | Ratio: realized_vol_A / realized_vol_B |
| `relative_vol_zscore` | features-cross-instrument | 10s | Z-score of ratio vs 90-bar window      |

## PnL Attribution

| Component         | Settlement Type | Mechanism                                             |
| ----------------- | --------------- | ----------------------------------------------------- |
| `vol_convergence` | MARK_TO_MARKET  | Profit when vol ratio reverts to mean                 |
| `funding_pnl`     | FUNDING_8H      | Funding rate differential between long and short legs |
| `spread_cost`     | PER_FILL        | Entry/exit spread on perpetual markets                |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target | Notes                                               |
| -------------------- | ------ | --------------------------------------------------- |
| Target annual return | 10-20% | Mean reversion alpha on vol ratio                   |
| Target Sharpe ratio  | 1.5    |                                                     |
| Max drawdown         | 10%    | Divergence can persist longer than expected         |
| Max leverage         | 2x     | Long/short perpetual pair                           |
| Capital scalability  | $5M    | BTC/ETH perps are deep; larger pairs may be thinner |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> signal      | 10ms       | 50ms       |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 100ms      | 500ms      |                     |
| **End-to-end**         | **220ms**  | **1100ms** | **No**              |

## Execution Details

- **Venues:** Binance Futures
- **Order types:** Limit (to minimize slippage on paired entry)
- **Atomic execution required?** Yes -- both legs must be filled; partial fill creates directional exposure
- **Rebalancing:** Signal-driven; entry at z-score divergence, exit at z-score convergence
- **Gas budget:** N/A (CeFi venue)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern                       | Exposure Type  | Used For             |
| ---------------------------------------- | -------------- | -------------------- |
| `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` | Notional long  | Net delta monitoring |
| `BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN` | Notional short | Net delta monitoring |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold         | Action on Breach            |
| --------------- | ----------- | ----------------- | --------------------------- |
| `delta`         | Yes         | 5% net notional   | Rebalance leg sizes         |
| `funding`       | Yes         | Funding > 0.1%/8h | Monitor; exit if persistent |
| `basis`         | No          | --                | --                          |
| `protocol_risk` | No          | --                | --                          |
| `liquidity`     | Yes         | Spread > 10bps    | Widen entry threshold       |

### Custom Strategy Risk Types

| Custom Risk           | What It Measures                     | Evaluation Method       | SSOT                      |
| --------------------- | ------------------------------------ | ----------------------- | ------------------------- |
| Correlation breakdown | Vol ratio divergence beyond 3 sigma  | z-score monitoring      | strategy config           |
| Regime change         | Structural shift in vol relationship | Rolling mean shift test | features-cross-instrument |

## Margin & Liquidation

- **Margin model:** Cross margin on Binance Futures
- **Health factor threshold:** Maintenance margin ratio > 5%
- **Liquidation penalty:** Varies by tier; typically 0.5-1.5%
- **Monitoring:** Per-tick margin check via position-balance-monitor-service

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue           | Secret Name                   | Testnet Available? | Notes          |
| --------------- | ----------------------------- | ------------------ | -------------- |
| Binance Futures | exec-{client}-binance-futures | Yes                | API key+secret |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Binance Futures account with perpetual trading enabled
2. **Secret Manager:** Per-client secrets: `exec-{client}-binance-futures-perpetual`
3. **Config:** New RelVolConfig entry with client-specific instrument pair and thresholds
4. **Position isolation:** One strategy instance per client (independent z-score tracking)
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

- Relative vol ratio time series with z-score bands (+/-2.0 entry, +/-0.5 exit)
- Entry/exit markers overlaid on z-score chart
- Realized vol comparison: instrument A vs instrument B (rolling window)

## Testing Stage Status

| Stage        | Status  | Notes                                       |
| ------------ | ------- | ------------------------------------------- |
| MOCK         | Done    | Static features, verified z-score logic     |
| HISTORICAL   | Pending | BTC/ETH vol ratio backtest                  |
| LIVE_MOCK    | Pending | Real features + paper execution             |
| LIVE_TESTNET | Pending | Binance Futures testnet                     |
| BATCH_REAL   | Pending | Historical replay with optimized thresholds |
| STAGING      | Pending | Testnet execution with real features        |
| LIVE_REAL    | Pending | Production execution                        |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/rel_vol/rel_vol_strategy.py`
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
