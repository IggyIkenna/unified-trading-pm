---
scope: [engineer, admin]
---

# Volatility Surface

> **Asset class:** TradFi / CeFi **Strategy type:** Options (Volatility) **Strategy ID pattern:**
> `QUANT_VOL_SURFACE_BTC`

## Overview

Volatility surface strategy that trades implied volatility percentile relative to its 252-day historical range. Buys
straddles when IV is cheap (percentile < 20%) and sells strangles when IV is rich (percentile > 80%). Uses normalized
strike coordinates (delta + expiry) rather than absolute strikes -- execution-service StrikeMapper resolves to real
strikes at order time. Default deployment is BTC options on Deribit.

## Token / Position Flow

```
Start:  WALLET:BTC or WALLET:USDT  (100% collateral)

BUY_VOL path (IV percentile < 20%):
  Step 1 - BUY ATM CALL: NormalizedStrikeCoordinate(delta=0.5, expiry_days=30, type=call)
  Step 2 - BUY ATM PUT:  NormalizedStrikeCoordinate(delta=0.5, expiry_days=30, type=put)
  -> Long straddle: profit from vol expansion

SELL_VOL path (IV percentile > 80%):
  Step 1 - SELL OTM CALL: NormalizedStrikeCoordinate(delta=0.25, expiry_days=30, type=call)
  Step 2 - SELL OTM PUT:  NormalizedStrikeCoordinate(delta=0.25, expiry_days=30, type=put)
  -> Short strangle: profit from vol contraction / theta decay

Wallet after deploy (BUY_VOL):
  - Long ATM call (delta ~0.5, 30 DTE)
  - Long ATM put (delta ~-0.5, 30 DTE)
  - Net delta ~ 0, long gamma, long vega
```

## Instruments

| Instrument Key                | Venue   | Type   | Role           |
| ----------------------------- | ------- | ------ | -------------- |
| BTC options (ATM call)        | Deribit | Option | Straddle leg A |
| BTC options (ATM put)         | Deribit | Option | Straddle leg B |
| BTC options (OTM call/put)    | Deribit | Option | Strangle legs  |
| `WALLET:BTC` or `WALLET:USDT` | Wallet  | Spot   | Collateral     |

## Key Features Consumed

| Feature                  | Source Service          | SLA | Used For                            |
| ------------------------ | ----------------------- | --- | ----------------------------------- |
| `atm_iv_percentile_252d` | features-volatility-svc | 1m  | Entry signal: buy/sell vol decision |
| `atm_iv_30d`             | features-volatility-svc | 1m  | Current ATM IV level                |
| `skew_25d_30d`           | features-volatility-svc | 1m  | Put-call skew for combo selection   |
| `term_structure_slope`   | features-volatility-svc | 1m  | Far/near ATM IV ratio               |

## PnL Attribution

| Component   | Settlement Type | Mechanism                                           |
| ----------- | --------------- | --------------------------------------------------- |
| `vega_pnl`  | MARK_TO_MARKET  | IV expansion/contraction on long/short vol position |
| `gamma_pnl` | MARK_TO_MARKET  | Realized vol exceeding/trailing implied vol         |
| `theta_pnl` | DAILY_DECAY     | Time decay cost (long vol) or income (short vol)    |
| `delta_pnl` | MARK_TO_MARKET  | Residual directional exposure (should be ~0)        |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target | Notes                                   |
| -------------------- | ------ | --------------------------------------- |
| Target annual return | 15-25% | Volatility risk premium capture         |
| Target Sharpe ratio  | 1.0    | Vol strategies have inherent variance   |
| Max drawdown         | 15%    | Short vol can have sharp drawdowns      |
| Max leverage         | 2x     | Notional options exposure vs collateral |
| Capital scalability  | $2M    | BTC options liquidity on Deribit        |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 200ms      | 1000ms     |                     |
| Feature -> signal      | 50ms       | 200ms      |                     |
| Signal -> instruction  | 10ms       | 50ms       |                     |
| Instruction -> fill    | 500ms      | 2000ms     |                     |
| **End-to-end**         | **760ms**  | **3250ms** | **No**              |

## Execution Details

- **Venues:** Deribit
- **Order types:** Limit (options are quoted with wide spreads; market orders costly)
- **Atomic execution required?** Yes -- straddle/strangle legs should be filled together
- **Rebalancing:** IV percentile re-evaluated at feature update frequency; position held until percentile returns to
  neutral zone (20-80%)
- **Gas budget:** N/A (CeFi venue)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern     | Exposure Type | Used For                 |
| ---------------------- | ------------- | ------------------------ |
| BTC options (all legs) | Delta         | Net directional exposure |
| BTC options (all legs) | Vega          | Vol exposure monitoring  |
| BTC options (all legs) | Gamma         | Convexity risk           |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold   | Action on Breach            |
| --------------- | ----------- | ----------- | --------------------------- |
| `delta`         | Yes         | 0.10 net    | Delta-hedge with underlying |
| `funding`       | No          | --          | --                          |
| `basis`         | No          | --          | --                          |
| `protocol_risk` | No          | --          | --                          |
| `liquidity`     | Yes         | Spread > 5% | Reduce position or exit     |
| `vega`          | Yes         | Per config  | Cap total vega exposure     |

### Custom Strategy Risk Types

| Custom Risk              | What It Measures                    | Evaluation Method    | SSOT         |
| ------------------------ | ----------------------------------- | -------------------- | ------------ |
| IV crush risk            | Sharp drop in IV on short vol       | IV percentile shift  | vol surface  |
| Gamma squeeze            | Large underlying move on long vol   | Realized vs implied  | features svc |
| Term structure inversion | Backwardation in vol term structure | term_structure_slope | features svc |

## Margin & Liquidation

- **Margin model:** Portfolio margin on Deribit (options + perp cross-margined)
- **Health factor threshold:** Maintenance margin > 10% of portfolio
- **Liquidation penalty:** Deribit auto-deleveraging
- **Monitoring:** Per-minute margin check; alert at 15% threshold

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue   | Secret Name           | Testnet Available? | Notes          |
| ------- | --------------------- | ------------------ | -------------- |
| Deribit | exec-{client}-deribit | Yes                | API key+secret |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Deribit account with options trading permissions
2. **Secret Manager:** Per-client secrets: `exec-{client}-deribit-options`
3. **Config:** New VolSurfaceConfig entry with client-specific IV thresholds and combo type
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

- IV percentile gauge (0-100 with 20/80 thresholds marked)
- Vol surface heatmap (delta x expiry, color = IV)
- Skew time series (25-delta put-call skew)
- Position Greeks dashboard (delta, gamma, vega, theta)

## Testing Stage Status

| Stage        | Status  | Notes                                               |
| ------------ | ------- | --------------------------------------------------- |
| MOCK         | Done    | Static IV percentile fixtures, verified entry logic |
| HISTORICAL   | Pending | BTC options vol surface backtest                    |
| LIVE_MOCK    | Pending | Real vol surface data + paper execution             |
| LIVE_TESTNET | Pending | Deribit testnet                                     |
| BATCH_REAL   | Pending | Historical replay with optimized IV thresholds      |
| STAGING      | Pending | Testnet execution with real vol features            |
| LIVE_REAL    | Pending | Production execution                                |

## References

- **Strategy implementation:** `strategy-service/strategy_service/engine/strategies/volatility/vol_surface_strategy.py`
- **NormalizedStrikeCoordinate:** `unified-api-contracts/unified_api_contracts/` (UAC root)
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
