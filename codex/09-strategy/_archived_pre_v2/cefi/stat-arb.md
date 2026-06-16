---
scope: [engineer, admin]
---

# CeFi Statistical Arbitrage

> **Asset class:** CeFi **Strategy type:** Statistical Arbitrage (cointegrated pairs) **Strategy ID pattern:**
> `QUANT_STAT_ARB_{ASSET_A}_{ASSET_B}`

## Overview

Statistical arbitrage strategy that trades cointegrated pairs (e.g. BTC/ETH) based on spread z-score, cointegration
score, and Ornstein-Uhlenbeck half-life. Entry requires all three gates to pass simultaneously: the pair must be
cointegrated above a minimum score, the OU half-life must be short enough to ensure mean reversion is practical, and the
spread z-score must exceed the entry threshold. Exits on mean reversion when the spread normalises.

## Token / Position Flow

```
Start:  WALLET:USDT  (100% USDT margin)

Step 1 - FEATURE INGEST: Receive PairSpreadFeatureRecord from features-cross-instrument:
         - spread_zscore: z-score of spread vs rolling window
         - half_life_bars: OU half-life (must be <= max_half_life_bars)
         - cointegration_score: must exceed min_cointegration_score
         - hedge_ratio: beta for sizing leg B vs leg A
Step 2 - EXIT CHECK (if positioned): |spread_zscore| < exit_zscore (default 0.5) -> EXIT
Step 3 - ENTRY GATES (all must pass):
         Gate 1: cointegration_score >= min_cointegration_score (default 0.5)
         Gate 2: half_life_bars <= max_half_life_bars (default 30)
         Gate 3: |spread_zscore| >= entry_zscore (default 2.0)
Step 4 - DIRECTION:
         - zscore > +entry_zscore -> ENTER_LONG_B (spread too high: short A, long B)
         - zscore < -entry_zscore -> ENTER_LONG_A (spread too low: long A, short B)
Step 5 - SIZING: Leg B sized as hedge_ratio * Leg A notional

Wallet after deploy:
  - Instrument A = 1x (long or short)
  - Instrument B = hedge_ratio * 1x (opposite direction)
```

## Instruments

| Instrument Key                           | Venue           | Type | Role                |
| ---------------------------------------- | --------------- | ---- | ------------------- |
| `WALLET:USDT`                            | Wallet          | Cash | Initial capital     |
| `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` | Binance Futures | Perp | Leg A (BTC default) |
| `BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN` | Binance Futures | Perp | Leg B (ETH default) |

## Key Features Consumed

| Feature               | Source Service            | SLA | Used For                          |
| --------------------- | ------------------------- | --- | --------------------------------- |
| `spread_zscore`       | features-cross-instrument | 5m  | Signal: entry/exit z-score gating |
| `half_life_bars`      | features-cross-instrument | 5m  | Gate: OU mean reversion speed     |
| `cointegration_score` | features-cross-instrument | 1h  | Gate: pair cointegration strength |
| `hedge_ratio`         | features-cross-instrument | 5m  | Sizing: beta for leg B vs leg A   |

**Feature source type:** `PairSpreadFeatureRecord` from `unified_api_contracts.internal`.

**Cointegration lookback:** 252 bars (default), used upstream for Engle-Granger or Johansen test. **Hedge ratio
window:** 60 bars (rolling OLS beta).

## PnL Attribution

| Component         | Settlement Type | Mechanism                                       |
| ----------------- | --------------- | ----------------------------------------------- |
| `spread_pnl`      | Mark-to-market  | Profit from spread convergence toward mean      |
| `hedge_ratio_pnl` | Mark-to-market  | P&L from hedge ratio drift (beta changes)       |
| `funding_pnl`     | `FUNDING_8H`    | Net funding: leg A rate - leg B rate            |
| `trading_fees`    | Per-trade       | Maker/taker fees on both legs at entry and exit |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target     | Notes                                                 |
| -------------------- | ---------- | ----------------------------------------------------- |
| Target annual return | TBD        |                                                       |
| Target Sharpe ratio  | TBD        |                                                       |
| Max drawdown         | TBD        |                                                       |
| Max leverage         | 1x per leg | Market-neutral when properly hedged                   |
| Capital scalability  | TBD        | Limited by pair liquidity and cointegration stability |
| Entry threshold      | 2.0 sigma  | `entry_zscore` on pair spread                         |
| Exit threshold       | 0.5 sigma  | `exit_zscore` -- spread reverted                      |
| Max half-life        | 30 bars    | `max_half_life_bars` -- reject slow-reverting pairs   |
| Min cointegration    | 0.5        | `min_cointegration_score` -- reject weak pairs        |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 100ms      | 500ms      |                     |
| Feature -> signal      | 1ms        | 5ms        |                     |
| Signal -> instruction  | 5ms        | 20ms       |                     |
| Instruction -> fill    | 50ms       | 200ms      |                     |
| **End-to-end**         | **156ms**  | **725ms**  | **No**              |

## Execution Details

- **Venues:** Binance Futures (both legs on same venue for netting)
- **Order types:** Market on both legs for simultaneous execution
- **Atomic execution required?** Yes -- both legs must execute together; single-leg exposure is directional risk
- **Rebalancing:** Event-driven on PairSpreadFeatureRecord update; hedge ratio refreshed on each signal
- **Gas budget:** N/A (CeFi)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern                       | Exposure Type    | Used For                |
| ---------------------------------------- | ---------------- | ----------------------- |
| `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` | Notional (leg A) | Leg A position tracking |
| `BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN` | Notional (leg B) | Leg B position tracking |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold               | Action on Breach               |
| --------------- | ----------- | ----------------------- | ------------------------------ |
| `delta`         | Yes         | Net delta drift         | Rebalance hedge ratio          |
| `basis`         | Yes         | Spread z-score reversal | Exit both legs                 |
| `funding`       | Yes         | Net funding cost        | Factor into hold/exit decision |
| `protocol_risk` | No          | --                      | --                             |
| `liquidity`     | Yes         | Pair liquidity drop     | Reduce size or skip entry      |

### Custom Strategy Risk Types

| Custom Risk             | What It Measures                             | Evaluation Method     | SSOT        |
| ----------------------- | -------------------------------------------- | --------------------- | ----------- |
| Cointegration breakdown | Pair loses cointegration (score < threshold) | Engle-Granger p-value | Config YAML |
| Half-life regime shift  | OU half-life exceeds max during hold         | Rolling OU estimation | Config YAML |
| Hedge ratio instability | Beta changes >20% during position lifetime   | Rolling OLS window    | Config YAML |

## Margin & Liquidation

- **Margin model:** Cross margin on Binance Futures (legs net against each other)
- **Health factor threshold:** N/A (CeFi margin maintenance; hedged positions have lower margin req)
- **Liquidation penalty:** Venue-dependent; leg divergence during liquidation creates tail risk
- **Monitoring:** Per-bar spread z-score, cointegration score, and hedge ratio drift

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

1. **Execution accounts:** Binance Futures account with cross margin enabled
2. **Secret Manager:** `exec-{client}-binance-futures-api-key`, `exec-{client}-binance-futures-api-secret`
3. **Config:** New `StatArbConfig` with `strategy_id`, `instrument_a`, `instrument_b`, thresholds, hedge_ratio_window
4. **Position isolation:** One strategy instance per client per pair
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
- Position breakdown (both legs with hedge ratio)

### Strategy-specific views (extensions)

- Pair spread z-score time series with entry/exit bands
- Cointegration score rolling window chart
- OU half-life evolution over time
- Hedge ratio (beta) drift monitor
- Leg A vs Leg B price normalised overlay

## Testing Stage Status

| Stage        | Status  | Notes                                         |
| ------------ | ------- | --------------------------------------------- |
| MOCK         | Done    | Static seed data + paper execution            |
| HISTORICAL   | Done    | Backtested BTC/ETH pair, 252-bar coint window |
| LIVE_MOCK    | Pending | Real pair spread data + paper execution       |
| LIVE_TESTNET | Pending | Binance Futures testnet                       |
| BATCH_REAL   | Pending |                                               |
| STAGING      | Pending |                                               |
| LIVE_REAL    | Pending |                                               |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/stat_arb/stat_arb_strategy.py`
- **Config type:** `strategy-service/strategy_service/config.py` (`StatArbConfig`)
- **Signal type:** `StatArbSignal` dataclass in same file
- **Feature type:** `unified-api-contracts/unified_api_contracts/internal/` (`PairSpreadFeatureRecord`)
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
