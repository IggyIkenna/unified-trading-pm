---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# TradFi Options Market Making

> **Asset class:** TradFi / CeFi (options available on Deribit, CME, IBKR) **Strategy type:** Options Market Making
> (multi-strike quoting, delta hedging) **Strategy ID pattern:** `{asset_group}_{UNDERLYING}_MM_OPT_{VENUE}_EVT_SUB1S`

## Overview

Delta-neutral options market making strategy that quotes bid/ask across multiple strikes and expiries on options
exchanges (Deribit, CME via FIX, IBKR). Earns the bid-ask spread while managing portfolio Greeks exposure via
Black-Scholes pricing, skew-adjusted spread widening on wings, per-strike risk limits (gamma, vega), and automatic delta
hedging with the underlying perpetual. Supports BTC (20 bps base spread) and ETH (25 bps base spread) deployments.

## How This Fits the Unified Trading System

Same event-driven architecture. Triggered by underlying price move (same as CeFi MM). Key difference: multi-strike means
many simultaneous orders, and delta hedging requires the ref pricing / underlying fixing mechanism from
[config-architecture.md](../cross-cutting/config-architecture.md).

```
features-volatility-service (publishes: IV surface, realized vol, skew)
features-delta-one-service (publishes: underlying price, funding rate)
  -> pub/sub events (on underlying move > threshold)
    -> strategy-service receives event
      -> strategy.generate_signal(features)
        -> emit QuoteInstruction[] (bid + ask per strike) + hedge instructions
```

**Multi-strike quoting:** Strategy sends N x 2 instructions (N strikes x bid+ask) on each trigger. This is a **batch of
instructions**, not a single instruction. Whether the venue supports mass quote (single API call for all) or requires
individual orders is an execution concern.

## Token / Position Flow

```
Start:  WALLET:BTC or WALLET:USDT  (100% collateral)

Step 1 - VOL_SURFACE_UPDATE: Receive IV surface data from features-volatility-service
Step 2 - STRIKE_GENERATION: Generate target deltas (e.g. [0.10, 0.25, 0.50, 0.75, 0.90])
Step 3 - PER_STRIKE LOOP (for each delta x call/put):
    a. Look up IV from vol surface model (nearest-neighbor; production uses SABR/SVI)
    b. Compute theoretical price via Black-Scholes
    c. Compute Greeks (delta, gamma, vega, theta) via BS closed-form
    d. Check per-strike risk limits (gamma < 0.10, vega < 5000 for BTC; 0.15/3000 for ETH)
    e. Compute skew-adjusted spread:
       base_spread * wing_multiplier * skew_adjustment
       wing_multiplier = 1.0 + 2.0 * |abs(delta) - 0.5|
       skew_adjustment = 1.0 + skew_adjustment_factor * |skew|
    f. Emit BID and ASK QuoteLevel at theo +/- half_spread
Step 4 - AGGREGATE: Sum portfolio Greeks across all quoted strikes
Step 5 - HEDGE CHECK: If |portfolio_delta| > hedge_threshold (0.10 BTC, 0.08 ETH):
    -> Emit HedgeInstruction on underlying perpetual (IMMEDIATE urgency)
Step 6 - RISK CIRCUIT BREAKER: If |portfolio_delta| > max_delta_exposure (0.50 BTC, 0.30 ETH):
    -> PULL_ALL quotes, force hedge

Actions: QUOTE_UPDATE, PULL_ALL, HEDGE_ONLY, HOLD

Wallet after deploy:
  - N x option positions (BID/ASK fills across strikes)
  - Underlying perpetual hedge position (delta-neutral target)
  - Earn: bid-ask spread on fills minus hedging costs
```

## Mass Quote Capabilities

| Venue           | Mass Quote?               | Mass Pull by Underlying? | Mass Pull All?      | Pull by Instrument? |
| --------------- | ------------------------- | ------------------------ | ------------------- | ------------------- |
| Deribit         | YES (mass_quote endpoint) | YES                      | YES                 | YES                 |
| CME (via FIX)   | YES (MassQuote message)   | YES (via QuoteCancel)    | YES                 | YES                 |
| IBKR            | NO (individual orders)    | NO                       | YES (global cancel) | YES                 |
| Binance Options | NO                        | NO                       | YES                 | YES                 |

## Instruments

| Instrument Key               | Venue   | Type      | Role                   |
| ---------------------------- | ------- | --------- | ---------------------- |
| BTC options (5 strikes x 2)  | Deribit | Option    | Quoting (bid + ask)    |
| ETH options (5 strikes x 2)  | Deribit | Option    | Quoting (bid + ask)    |
| `BTC-PERPETUAL`              | Deribit | Perpetual | Delta hedge instrument |
| `ETH-PERPETUAL`              | Deribit | Perpetual | Delta hedge instrument |
| `WALLET:BTC` / `WALLET:USDT` | Wallet  | Spot      | Collateral             |

## Key Features Consumed

| Feature                 | Source Service          | SLA | Used For                        |
| ----------------------- | ----------------------- | --- | ------------------------------- |
| `implied_vol` (surface) | features-volatility-svc | <1s | Theo pricing per strike         |
| `realized_vol`          | features-volatility-svc | 5m  | Vol surface calibration         |
| `skew_25d`              | features-volatility-svc | 10s | Spread adjustment on wings      |
| `term_structure_slope`  | features-volatility-svc | 10s | Term structure awareness        |
| `underlying_price`      | features-delta-one-svc  | <1s | Strike mapping + hedge sizing   |
| `portfolio_greeks`      | ExposureMonitor         | <1s | Delta/gamma/vega/theta tracking |

## Underlying Fixing for Options

When the underlying moves, ALL option quotes need updating. This uses the reference pricing mechanism from
[config-architecture.md](../cross-cutting/config-architecture.md):

```
Strategy sends for each strike:
  instruction.price = theo_option_price (at current underlying)
  instruction.ref_underlying = "ETH-USD"
  instruction.edge_offset = theo - market_mid  (our edge)

When underlying moves $10:
  Execution-service recalculates each option price using delta:
    new_price ~ old_price + delta * underlying_change
  Updates all orders simultaneously (mass quote if supported)
```

## Delta Hedging

After fills, portfolio delta changes. Strategy monitors and hedges:

| Condition                                | Action                                         |
| ---------------------------------------- | ---------------------------------------------- |
| `abs(portfolio_delta) > hedge_threshold` | Hedge: trade underlying to flatten delta       |
| Fill on a bid (bought option)            | Delta increases -> may need to sell underlying |
| Fill on an ask (sold option)             | Delta decreases -> may need to buy underlying  |

**Hedge instruction uses leader/follower model:**

- Follower: option quote (passive, wait for fill)
- Leader: delta hedge on underlying (aggressive, execute immediately on option fill)

## PnL Attribution

| Component         | Settlement Type | Mechanism                                     |
| ----------------- | --------------- | --------------------------------------------- |
| `spread_pnl`      | PER_FILL        | Bid-ask spread captured on fills              |
| `theta_pnl`       | DAILY_DECAY     | Time decay income on short options            |
| `delta_hedge_pnl` | MARK_TO_MARKET  | P&L from perpetual hedge trades               |
| `gamma_pnl`       | MARK_TO_MARKET  | Inventory gamma exposure between hedge cycles |
| `vega_pnl`        | MARK_TO_MARKET  | IV changes affecting option inventory value   |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target             | Notes                                         |
| -------------------- | ------------------ | --------------------------------------------- |
| Target annual return | 20-40%             | Theta capture + spread; depends on vol regime |
| Target Sharpe ratio  | 2.0+               | Spread income is consistent; vol events hurt  |
| Max drawdown         | 10%                | Vol spike / gap risk is primary               |
| Max leverage         | 3-5x               | Notional leverage high but Greeks-managed     |
| Capital scalability  | $5M per underlying | Depends on options market depth               |

## Latency Profile

| Segment                              | p50 Target | p99 Target | Co-location Needed?            |
| ------------------------------------ | ---------- | ---------- | ------------------------------ |
| Feature -> strategy                  | 2ms        | 10ms       | **YES**                        |
| Strategy -> instructions (N strikes) | 1ms        | 5ms        | --                             |
| Instructions -> mass quote           | 5ms        | 20ms       | **YES**                        |
| Delta hedge (after fill)             | 10ms       | 50ms       | **YES**                        |
| **End-to-end**                       | **~18ms**  | **~85ms**  | **YES for competitive venues** |

Options MM is the MOST latency-sensitive strategy due to adverse selection risk on stale quotes.

## Execution Details

- **Venues:** Deribit (primary), CME via FIX (TradFi), IBKR (TradFi)
- **Order types:** Limit quotes (bid + ask per strike); mass quote where venue supports it
- **Atomic execution required?** No -- quotes are independent; hedge is triggered post-fill
- **Rebalancing:** Event-driven (underlying price move > threshold triggers quote refresh); hedge triggered when
  |portfolio_delta| > hedge_threshold
- **Gas budget:** N/A (CeFi venues; standard exchange fees)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern   | Exposure Type | Used For                           |
| -------------------- | ------------- | ---------------------------------- |
| All quoted options   | Delta         | Portfolio delta for hedge trigger  |
| All quoted options   | Gamma         | Per-strike and portfolio gamma cap |
| All quoted options   | Vega          | Per-strike and portfolio vega cap  |
| Underlying perpetual | Notional      | Hedge position tracking            |

### Risk Type Subscriptions

| Risk Type        | Subscribed?      | Threshold                            | Action on Breach                   |
| ---------------- | ---------------- | ------------------------------------ | ---------------------------------- |
| `delta`          | YES              | 0.10 hedge / 0.50 pull (BTC)         | Hedge underlying or PULL_ALL       |
| `gamma`          | YES              | 0.10/strike (BTC), 0.15/strike (ETH) | Skip strike                        |
| `vega`           | YES              | 5000/strike (BTC), 3000/strike (ETH) | Skip strike                        |
| `theta`          | YES (monitoring) | --                                   | Expected daily P&L from time decay |
| `volga`          | YES              | Vol-of-vol risk                      | Widen spreads on wings             |
| `vanna`          | YES              | Delta-vol cross-risk                 | Adjust skew quotes                 |
| `venue_protocol` | YES              | Exchange issues                      | Cancel all (mass pull)             |
| `concentration`  | YES              | Too much OI in one strike            | Reduce                             |

### Custom Strategy Risk Types

| Custom Risk             | What It Measures                  | Evaluation Method   | SSOT            |
| ----------------------- | --------------------------------- | ------------------- | --------------- |
| Inventory concentration | Too many fills on one side/strike | Fill count per side | strategy config |
| Adverse selection       | Fills consistently on wrong side  | Post-fill mark      | execution svc   |
| Hedge slippage          | Cost of delta hedging vs theo     | Hedge execution log | execution svc   |

## Margin & Liquidation

- **Margin model:** Portfolio margin on Deribit (options + perp cross-margined)
- **Health factor threshold:** Maintenance margin > 10% of portfolio
- **Liquidation penalty:** Deribit auto-deleveraging (ADL)
- **Monitoring:** Sub-second margin check; PULL_ALL if margin ratio falls below 15%

## BTC vs ETH Configuration Comparison

| Parameter                | BTC (Deribit) | ETH (Deribit) |
| ------------------------ | ------------- | ------------- |
| `base_spread_bps`        | 20            | 25            |
| `skew_adjustment_factor` | 0.5           | 0.6           |
| `max_delta_exposure`     | 0.5           | 0.3           |
| `max_gamma_per_strike`   | 0.10          | 0.15          |
| `max_vega_per_strike`    | 5000          | 3000          |
| `hedge_threshold`        | 0.10          | 0.08          |
| `quote_size`             | 1.0 BTC       | 10.0 ETH      |
| `num_strikes`            | 5             | 5             |
| `target_expiry_days`     | 30            | 30            |

ETH has wider spreads (lower liquidity), tighter delta limits (higher vol), and larger quote sizes (lower unit price).

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue   | Secret Name           | Testnet Available? | Notes           |
| ------- | --------------------- | ------------------ | --------------- |
| Deribit | exec-{client}-deribit | Yes                | API key+secret  |
| CME     | exec-{client}-cme-fix | Yes (cert env)     | FIX credentials |
| IBKR    | exec-{client}-ibkr    | Yes (paper)        | TWS/Gateway API |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Deribit (or CME/IBKR) account with options + perp trading permissions
2. **Secret Manager:** Per-client secrets: `exec-{client}-{venue}-options`
3. **Config:** New OptionsMMConfig entry with client-specific spread, risk limits, and venue
4. **Position isolation:** One strategy instance per client (independent Greeks tracking)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                            | Restart?        |
| ----------------- | --------------------------------------- | --------------- |
| strategy-service  | New OptionsMMConfig entry in GCS        | No (hot-reload) |
| execution-service | New client routing + mass quote support | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown

### Strategy-specific views (extensions)

- Live quote ladder: strikes x bid/ask prices with fill indicators
- Portfolio Greeks dashboard (delta, gamma, vega, theta) with threshold lines
- Vol surface heatmap (delta x expiry, color = IV)
- Hedge activity log: timing, size, direction, slippage
- Spread earned vs spread quoted efficiency chart

## Testing Stage Status

| Stage        | Status  | Notes                                               |
| ------------ | ------- | --------------------------------------------------- |
| MOCK         | Done    | Static vol surface, verified Greeks and spread calc |
| HISTORICAL   | Pending | Deribit historical options data (via Tardis.dev)    |
| LIVE_MOCK    | Pending | Real IV features, paper quotes                      |
| LIVE_TESTNET | Pending | Deribit testnet (`test.deribit.com`)                |
| BATCH_REAL   | Pending | Historical options data replay                      |
| STAGING      | Pending | Deribit testnet with real timing                    |
| LIVE_REAL    | Pending | All above + co-location decision                    |

## References

- **Strategy implementation:**
  `strategy-service/strategy_service/engine/strategies/options_market_making/options_mm_strategy.py`
- **NormalizedStrikeCoordinate:** `unified-api-contracts/unified_api_contracts/` (UAC root)
- **Greeks calculator:** Built-in Black-Scholes in `options_mm_strategy.py` (`compute_greeks()`)
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Deribit adapter:**
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/deribit_execution.py`
- **Greeks schemas:** `unified-api-contracts/canonical/domain/derivatives/`
- **Hard rules:** [config-architecture.md](../cross-cutting/config-architecture.md)
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Execution adapters:** `execution-service/`
