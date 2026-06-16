---
scope: [engineer, admin]
---

# Options ML (Strike Selection)

> **Asset class:** TradFi **Strategy type:** Options **Strategy ID pattern:**
> `OPTIONS_ML_{STRIKE|DELTA|VOL}_{BTC|ETH|SPY}_{VENUE}_V1`

## Overview

ML-driven options strategy that uses trained models to predict optimal strike selection, directional delta conversion,
or volatility mispricings for options on Deribit (BTC/ETH) and CBOE/IBKR (SPY). Unlike the companion Options Market
Making strategy which earns bid-ask spread through continuous quoting, Options ML takes directional or volatility views
informed by ML inference and expresses them through targeted option positions. The strategy supports three distinct
prediction types — each consuming different ML model outputs and producing different trade structures — unified under a
single `OptionsMLStrategy` class with a dispatch-based signal architecture.

## Token / Position Flow

```
Start:  WALLET:COLLATERAL (100% USDT on Deribit, USD on IBKR/CBOE)

--- STRIKE_SELECTION (Type 1) ---
Step 1 - ML_INFERENCE: ml-inference-service publishes strike scoring candidates
         (normalized_strike, expiry_bucket, expected_pnl, greek_risk_score, theta_cost, vol_risk)
Step 2 - CANDIDATE_SCORING: Strategy scores each candidate:
         score = expected_pnl - greek_risk_score - theta_cost - vol_risk
Step 3 - SELECTION: Pick highest positive score; emit BUY_OPTION instruction
Step 4 - EXECUTION: Limit order at theo price on selected strike/expiry

--- DELTA_CONVERSION (Type 2) ---
Step 1 - ML_INFERENCE: ml-inference-service publishes direction (bullish/bearish) + confidence
Step 2 - STRIKE_MAPPING: Convert to fixed delta strike:
         bullish -> buy call at target_delta (default 0.30)
         bearish -> buy put at target_delta (default 0.30)
Step 3 - EXPIRY_SELECTION: Closest-to-target_expiry_days option
Step 4 - EXECUTION: Limit order on the mapped NormalizedStrikeCoordinate

--- VOLATILITY_COMBO (Type 3) ---
Step 1 - ML_INFERENCE: ml-inference-service publishes predicted_realized_vol
Step 2 - VOL_COMPARISON: Compare predicted_realized_vol vs market implied_vol
         If realized > implied -> BUY_STRADDLE (long vol)
         If realized < implied -> SELL_STRADDLE (short vol)
Step 3 - STRIKE_MAPPING: ATM straddle (delta=0.5) at target_expiry_days
Step 4 - EXECUTION: Two-leg order (call + put at same strike)

Wallet after deploy:
  - Option position(s) per prediction type output
  - Delta hedge on underlying if net delta exceeds threshold
  - Earn: directional move (Type 2), vol edge (Type 1/3), or premium decay (short vol)
```

## Instruments

| Instrument Key                 | Venue         | Type      | Role                                        |
| ------------------------------ | ------------- | --------- | ------------------------------------------- |
| BTC options (variable strikes) | Deribit       | Option    | Type 1/2/3 trade targets                    |
| ETH options (variable strikes) | Deribit       | Option    | Type 1/3 trade targets                      |
| SPY options (variable strikes) | CBOE via IBKR | Option    | Type 2 directional trades (equity)          |
| `BTC-PERPETUAL`                | Deribit       | Perpetual | Delta hedge instrument (crypto underlyings) |
| `ETH-PERPETUAL`                | Deribit       | Perpetual | Delta hedge instrument (crypto underlyings) |
| `SPY` underlying               | IBKR          | ETF       | Delta hedge instrument (equity)             |
| `WALLET:USDT` / `WALLET:USD`   | Wallet        | Spot      | Collateral                                  |

## Key Features Consumed

| Feature                     | Source Service              | SLA | Used For                                   |
| --------------------------- | --------------------------- | --- | ------------------------------------------ |
| `strike_scoring_candidates` | ml-inference-service        | 30s | Type 1: candidate set with PnL/risk scores |
| `ml_direction`              | ml-inference-service        | 10s | Type 2: bullish/bearish + confidence       |
| `predicted_realized_vol`    | ml-inference-service        | 60s | Type 3: forward vol prediction             |
| `implied_vol` (surface)     | features-volatility-service | <1s | Type 1 vol_risk input, Type 3 comparison   |
| `realized_vol`              | features-volatility-service | 5m  | ML model feature input (training)          |
| `skew_25d`                  | features-volatility-service | 10s | Strike risk adjustment                     |
| `underlying_price`          | features-delta-one-service  | <1s | Strike coordinate resolution               |
| `term_structure_slope`      | features-volatility-service | 10s | Expiry bucket preference weighting         |

## PnL Attribution

| Component        | Settlement Type | Mechanism                                                    |
| ---------------- | --------------- | ------------------------------------------------------------ |
| `premium_pnl`    | PER_FILL        | Net premium paid/received on option entry/exit               |
| `delta_pnl`      | MARK_TO_MARKET  | Directional move of underlying x option delta                |
| `gamma_pnl`      | MARK_TO_MARKET  | Convexity gain/loss from large underlying moves              |
| `theta_pnl`      | DAILY_DECAY     | Time decay cost on long positions, income on short positions |
| `vega_pnl`       | MARK_TO_MARKET  | IV changes affecting position value (primary for Type 3)     |
| `hedge_cost_pnl` | PER_FILL        | Slippage and fees from delta hedging via underlying          |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target             | Notes                                                           |
| -------------------- | ------------------ | --------------------------------------------------------------- |
| Target annual return | 15-30%             | Varies by prediction type: Type 1 highest alpha, Type 2 fastest |
| Target Sharpe ratio  | 1.5+               | ML edge degrades in regime changes; retrain cycle matters       |
| Max drawdown         | 15%                | Capped by position sizing and stop-loss on premium paid         |
| Max leverage         | 2-3x               | Notional leverage through options; delta-managed                |
| Capital scalability  | $3M per underlying | Options liquidity thinner than spot; Deribit BTC best depth     |

## Latency Profile

| Segment                             | p50 Target | p99 Target | Co-location Needed?           |
| ----------------------------------- | ---------- | ---------- | ----------------------------- |
| ML inference → strategy             | 50ms       | 200ms      | No                            |
| Feature (vol surface) → strategy    | 5ms        | 20ms       | No                            |
| Strategy → instruction              | 2ms        | 10ms       | No                            |
| Instruction → fill (limit order)    | 100ms      | 500ms      | No (passive fill)             |
| Delta hedge (after fill, if needed) | 10ms       | 50ms       | Preferred for crypto          |
| **End-to-end (signal → position)**  | **~170ms** | **~780ms** | **No (ML latency dominates)** |

Options ML is less latency-sensitive than Options MM because it trades on ML signals (seconds-to-minutes frequency)
rather than continuous quoting. The binding constraint is ML inference latency, not network RTT.

## Execution Details

- **Venues:** Deribit (BTC/ETH options, primary), CBOE via IBKR (SPY options, equity), Binance Options (secondary
  crypto)
- **Order types:** Limit orders for option entry/exit; TWAP for delta hedging on underlying when hedge size > 10% of
  ADV; market orders for urgent hedges when |delta| breaches circuit breaker
- **Atomic execution required?** No for single-leg trades (Types 1, 2). Yes for straddle entry (Type 3) — both legs
  should fill within the same pricing window to avoid leg risk
- **Rebalancing:** Signal-driven (new ML inference output triggers re-evaluation); positions held for
  `prediction_horizon_days` (default 7 days for Type 1/3, 1 day for Type 2)
- **Gas budget:** N/A (CeFi venues; standard exchange fees — Deribit maker 0.02%, IBKR $0.65/contract)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern      | Exposure Type | Used For                                   |
| ----------------------- | ------------- | ------------------------------------------ |
| Active option positions | Delta         | Net directional exposure for hedge trigger |
| Active option positions | Gamma         | Convexity risk; large move sensitivity     |
| Active option positions | Vega          | Vol exposure; primary for Type 3 positions |
| Active option positions | Theta         | Daily time decay P&L estimate              |
| Underlying hedge        | Notional      | Hedge position tracking                    |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?      | Threshold                          | Action on Breach                   |
| ---------------- | ---------------- | ---------------------------------- | ---------------------------------- |
| `delta`          | YES              | 0.20 hedge / 0.50 circuit breaker  | Hedge underlying or flatten        |
| `gamma`          | YES              | Portfolio gamma > 0.15             | Reduce position size               |
| `vega`           | YES              | Portfolio vega > 8000 (BTC)        | Reduce Type 3 straddle exposure    |
| `theta`          | YES (monitoring) | —                                  | Expected daily P&L from time decay |
| `concentration`  | YES              | >50% of portfolio in single expiry | Diversify across expiry buckets    |
| `model_risk`     | YES              | ML confidence < 0.3                | HOLD — no new positions            |
| `venue_protocol` | YES              | Exchange downtime/issues           | Cancel pending orders              |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Custom Strategy Risk Types

| Custom Risk               | What It Measures                             | Evaluation Method          | SSOT             |
| ------------------------- | -------------------------------------------- | -------------------------- | ---------------- |
| ML model staleness        | Time since last model retrain                | `last_retrain_timestamp`   | ml-inference-svc |
| Prediction accuracy decay | Rolling accuracy of ML predictions vs actual | 20-trade rolling accuracy  | strategy config  |
| Vol regime mismatch       | Predicted vol regime vs actual market regime | Regime classification diff | features-vol-svc |

## Margin & Liquidation

- **Margin model:** Portfolio margin on Deribit (options + perp cross-margined); Reg-T margin on IBKR (SPY options)
- **Health factor threshold:** Deribit: maintenance margin > 10% of portfolio; IBKR: Reg-T excess > $25K
- **Liquidation penalty:** Deribit auto-deleveraging (ADL); IBKR forced liquidation at broker discretion
- **Monitoring:** Pre-trade margin check before every new position; 10-second interval margin monitoring for open
  positions; alert at 15% margin utilization, flatten at 25%

## Authentication & Credentials

Links to SSOT — do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue           | Secret Name           | Testnet Available? | Notes                          |
| --------------- | --------------------- | ------------------ | ------------------------------ |
| Deribit         | exec-{client}-deribit | Yes                | API key + secret               |
| IBKR            | exec-{client}-ibkr    | Yes (paper)        | TWS/Gateway API                |
| CBOE (via IBKR) | exec-{client}-ibkr    | Yes (paper)        | Routed through IBKR connection |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Deribit account with options trading enabled (BTC/ETH); IBKR account with options permissions
   (SPY)
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-options-ml`
3. **Config:** New `OptionsMLConfig` entry in GCS with client-specific `prediction_type`, `ml_model_id`, risk limits
4. **Position isolation:** One strategy instance per client per prediction type (predictions diverge)
5. **Restart required?** No — hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service              | What Changes                                 | Restart?        |
| -------------------- | -------------------------------------------- | --------------- |
| strategy-service     | New OptionsMLConfig entry in GCS             | No (hot-reload) |
| execution-service    | New client routing rule for options venue    | No (hot-reload) |
| ml-inference-service | Client-specific model assignment (if custom) | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- ML prediction confidence histogram with outcome overlay (correct/incorrect)
- Strike selection heatmap: normalized_strike x expiry_bucket, color = composite score
- Vol prediction vs realized scatter plot (Type 3 performance tracking)
- Greeks exposure dashboard: delta, gamma, vega, theta with threshold lines per prediction type
- Position holding period distribution by prediction type

## Testing Stage Status

| Stage        | Status  | Notes                                                             |
| ------------ | ------- | ----------------------------------------------------------------- |
| MOCK         | Done    | Static ML outputs, verified scoring, delta conversion, vol combos |
| HISTORICAL   | Pending | Deribit historical options + vol surface data (via Tardis.dev)    |
| LIVE_MOCK    | Pending | Real vol features, paper option orders                            |
| LIVE_TESTNET | Pending | Deribit testnet (`test.deribit.com`), IBKR paper trading          |
| BATCH_REAL   | Pending | Historical replay with trained ML models                          |
| STAGING      | Pending | Deribit testnet + real ML inference timing                        |
| LIVE_REAL    | Pending | All above passed; model retrain pipeline validated                |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/options_ml/options_ml_strategy.py`
- **Config schema:** `strategy-service/strategy_service/config.py` (`OptionsMLConfig`)
- **Prediction types:** `strategy-service/strategy_service/types.py` (`OptionMLPredictionType`)
- **NormalizedStrikeCoordinate:** `unified-api-contracts/unified_api_contracts/` (UAC root)
- **Factory functions:** `create_btc_strike_ml_strategy()`, `create_spy_delta_ml_strategy()`,
  `create_eth_vol_ml_strategy()`, `create_btc_delta_ml_strategy()`
- **Related strategy:** [market-making-options.md](./market-making-options.md) (companion MM strategy)
- **Vol surface features:** `features-volatility-service` (IV surface, realized vol, skew)
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
