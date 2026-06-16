---
scope: [engineer, admin]
---

# Commodity Regime Strategy

> **Asset class:** TradFi **Strategy type:** Regime-Conditional Multi-Factor **Strategy ID pattern:**
> `TRADFI_{CL|NG}_REGIME_{SCE|HUF}_1D`

## Overview

HMM regime-conditional 5-factor commodity futures strategy. Consumes CommoditySignal from features-commodity-service
(4-state HMM regime detector + IC-calibrated factor weights) and applies regime-specific weight overrides, position
sizing, and stop widths. Executes via IBKR CME adapter for WTI crude oil (CL) and Henry Hub natural gas (NG) futures.

## Token / Position Flow

```
Start:  BROKER:CASH:USD  (100% USD margin)

Step 1 - FEATURE_READ: Read CommoditySignal from features-commodity-service (GCS/Pub-Sub)
         Contains: master_signal, regime (4-state HMM), 5 factor values, IC-calibrated weights
Step 2 - REGIME_CHECK: Classify HMM regime:
         HIGH_VOL_TRENDING -> trend-follow weights (momentum 0.45)
         LOW_VOL_MEAN_REVERTING -> mean-revert weights (COT 0.35, storage 0.25)
         CRISIS/VOLATILE -> equal weights, 0.4x position size, 1.5x stop width
         UNKNOWN (low confidence) -> base weights, 0.6x position size
Step 3 - SIGNAL_REWEIGHT: Recompute master_signal with regime-adjusted factor weights
Step 4 - DIRECTION: master_signal > 0 -> LONG, < 0 -> SHORT (threshold: 0.20 CL, 0.25 NG)
Step 5 - SIZE: Apply regime position size multiplier to base max_position_size_usd
Step 6 - STOPS: Apply regime stop multiplier to base stop_loss_pct / take_profit_pct
Step 7 - EXECUTE: Emit signal for IBKR CME adapter

Wallet after deploy:
  - NYMEX:FUTURES:CL or NG = 1 position (LONG or SHORT)
  - Sized by regime-adjusted max_position_size_usd
```

## Instruments

| Instrument Key     | Venue | Type    | Role             |
| ------------------ | ----- | ------- | ---------------- |
| `NYMEX:FUTURES:CL` | NYMEX | Futures | WTI crude oil    |
| `NYMEX:FUTURES:NG` | NYMEX | Futures | Henry Hub natgas |
| `BROKER:CASH:USD`  | IBKR  | Cash    | Margin capital   |

## Key Features Consumed

| Feature             | Source Service             | SLA | Used For                                       |
| ------------------- | -------------------------- | --- | ---------------------------------------------- |
| `rig_count`         | features-commodity-service | 7d  | Factor 1: capacity indicator (Baker Hughes)    |
| `cot_positioning`   | features-commodity-service | 7d  | Factor 2: speculative vs commercial (CFTC)     |
| `storage_alpha`     | features-commodity-service | 7d  | Factor 3: inventory deviation (EIA)            |
| `price_momentum`    | features-commodity-service | 1d  | Factor 4: technical momentum                   |
| `weather_delta`     | features-commodity-service | 1d  | Factor 5: degree-day demand proxy (Open Meteo) |
| `regime`            | features-commodity-service | 1d  | HMM 4-state regime classification              |
| `regime_confidence` | features-commodity-service | 1d  | Posterior probability of regime state          |
| `master_signal`     | features-commodity-service | 1d  | Composite signal [-1, 1]                       |

## PnL Attribution

| Component      | Settlement Type | Mechanism                                          |
| -------------- | --------------- | -------------------------------------------------- |
| `directional`  | MARK_TO_MARKET  | Futures price movement in direction of signal      |
| `regime_alpha` | MARK_TO_MARKET  | Excess return from regime-conditional weighting    |
| `stop_loss`    | STOP_TRIGGER    | Exit at regime-adjusted stop (base 2.5% CL, 3% NG) |
| `take_profit`  | TP_TRIGGER      | Exit at regime-adjusted TP (base 5% CL, 6% NG)     |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target (CL) | Target (NG) | Notes                                    |
| -------------------- | ----------- | ----------- | ---------------------------------------- |
| Target annual return | 12-20%      | 15-25%      | Higher for NG due to higher vol          |
| Target Sharpe ratio  | 1.2         | 1.0         | NG Sharpe lower due to regime noise      |
| Max drawdown         | 12%         | 15%         | Enforced by max_drawdown_pct config      |
| Max leverage         | 1x          | 1x          | No leverage beyond futures margin        |
| Capital scalability  | $2M         | $1M         | NG less liquid than CL; front-month only |

## Latency Profile

| Segment               | p50 Target | p99 Target | Co-location Needed? |
| --------------------- | ---------- | ---------- | ------------------- |
| Feature compute       | 5s         | 30s        |                     |
| Feature -> signal     | 100ms      | 500ms      |                     |
| Signal -> instruction | 10ms       | 50ms       |                     |
| Instruction -> fill   | 200ms      | 1s         |                     |
| **End-to-end**        | **~6s**    | **~32s**   | **No**              |

## Execution Details

- **Venues:** NYMEX (via IBKR CME adapter)
- **Order types:** Limit (front-month contract)
- **Atomic execution required?** No -- single instrument
- **Rebalancing:** Daily (1d timeframe); HUF mode holds until signal flips direction
- **Gas budget:** N/A (futures market, standard commissions ~$2.25/contract)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern | Exposure Type    | Used For                 |
| ------------------ | ---------------- | ------------------------ |
| `NYMEX:FUTURES:CL` | Futures notional | Track commodity exposure |
| `NYMEX:FUTURES:NG` | Futures notional | Track commodity exposure |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold         | Action on Breach        |
| --------------- | ----------- | ----------------- | ----------------------- |
| `delta`         | Yes         | 100% notional     | Single instrument       |
| `funding`       | No          | --                | --                      |
| `basis`         | No          | --                | --                      |
| `protocol_risk` | No          | --                | --                      |
| `liquidity`     | Yes         | 5% daily volume   | Reduce position size    |
| `drawdown`      | Yes         | 12% CL / 15% NG   | Flatten position        |
| `regime_shift`  | Yes         | Confidence < 0.55 | Reduce to 0.6x position |

### Custom Strategy Risk Types

| Custom Risk              | What It Measures                          | Evaluation Method | SSOT                       |
| ------------------------ | ----------------------------------------- | ----------------- | -------------------------- |
| Regime confidence decay  | Drop in HMM posterior probability         | Per-signal check  | Strategy config            |
| Factor staleness cascade | 3+ factors stale simultaneously           | Pre-signal gate   | Strategy code              |
| IC degradation           | Rolling Spearman IC per factor per regime | IC calibrator     | features-commodity-service |

## Margin & Liquidation

- **Margin model:** SPAN margin (CME futures)
- **Health factor threshold:** N/A (exchange margin calls)
- **Liquidation penalty:** Exchange liquidation rules
- **Monitoring:** Per-signal regime-adjusted position size check

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue | Secret Name        | Testnet Available? | Notes            |
| ----- | ------------------ | ------------------ | ---------------- |
| IBKR  | exec-{client}-ibkr | Yes (paper)        | IBKR TWS/Gateway |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** IBKR account with futures trading permissions (NYMEX)
2. **Secret Manager:** Per-client secrets: `exec-{client}-ibkr-futures`
3. **Config:** New entry in strategy config YAML with client-specific risk_config params
4. **Position isolation:** One strategy instance per client per commodity
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes            | Restart?        |
| ----------------- | ----------------------- | --------------- |
| strategy-service  | New config entry in GCS | No (hot-reload) |
| execution-service | New client routing rule | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- HMM regime state timeline (color-coded: green=trending, blue=mean-reverting, red=crisis, grey=unknown)
- 5-factor radar chart with regime-adjusted weights
- IC heatmap: factor x regime Spearman correlation
- Factor staleness dashboard with threshold indicators

## Testing Stage Status

| Stage        | Status  | Notes                                             |
| ------------ | ------- | ------------------------------------------------- |
| MOCK         | Pending | Static CommoditySignal fixtures + factory tests   |
| HISTORICAL   | Pending | CL/NG daily backtest with historical features     |
| LIVE_MOCK    | Pending | Real features + paper execution                   |
| LIVE_TESTNET | N/A     | Paper trading via IBKR API                        |
| BATCH_REAL   | Pending | Historical replay with optimized config           |
| STAGING      | Pending | Paper trading with real features + IC calibration |
| LIVE_REAL    | Pending | Production execution                              |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/commodity_regime.py`
- **Features source:** `features-commodity-service/features_commodity_service/engine/`
- **HMM detector:** `features-commodity-service/features_commodity_service/engine/regime/hmm_detector.py`
- **Signal composer:** `features-commodity-service/features_commodity_service/engine/signal_composer.py`
- **IC calibrator:** `features-commodity-service/features_commodity_service/engine/ic_calibrator.py`
- **UAC types:** `unified-api-contracts/unified_api_contracts/internal/domain/features_commodity/commodity_signal.py`
- **Config (CL):** `strategy-service/configs/commodity_regime_oil.yaml`
- **Config (NG):** `strategy-service/configs/commodity_regime_natgas.yaml`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
