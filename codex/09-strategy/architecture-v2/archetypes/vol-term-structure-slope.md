---
doc_type: codex-ssot
title: "Archetype: `VOL_TERM_STRUCTURE_SLOPE`"
summary:
  "Archetype spec for `VOL_TERM_STRUCTURE_SLOPE` — trades term-structure shape via a daily Heston/SVI parametric slope
  fit, entering front-vs-back straddle legs on slope z-score extremes with continuous roll; Deribit/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, term-structure, slope, mean-reversion]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_TERM_STRUCTURE_SLOPE archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_TERM_STRUCTURE_SLOPE
family: VOL_TRADING
venue_universe: [DERIBIT, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_TERM_STRUCTURE_SLOPE`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous with rolling expiry management
> — positions repriced daily; near leg rolled before expiry. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_term_structure_slope_engine.py`

## What it does

Trades the slope (shape) of the volatility term structure rather than its level. A long-slope position (buy front-tenor
vol, sell back-tenor vol) bets that the term structure is in backwardation and will transition toward contango. A
short-slope position (sell front-tenor, buy back-tenor) bets on steepening. The entry signal is derived from fitting the
full term structure to a parametric model (Heston or SVI) and extracting the slope parameter; entry triggers when the
slope deviates from its rolling 30-day mean by more than the configured threshold. The archetype continuously manages
rolling expiries to maintain constant exposure to the target DTE spread.

## Token / position flow

```
1. TERM STRUCTURE FIT: daily parametric fit of vol surface
   - Fit Heston or SVI model to option chain (all tenors simultaneously)
   - Extract slope parameter: d(IV)/d(T) at ATM across tenor grid
   - Compute slope_z = (slope - rolling_30d_mean) / rolling_30d_std

2. SIGNAL CHECK:
   - LONG SLOPE: slope_z < -entry_z_threshold
     (backwardation extreme → buy front vol / sell back vol)
   - SHORT SLOPE: slope_z > +entry_z_threshold
     (contango extreme → sell front vol / buy back vol)

3. POSITION CONSTRUCTION:
   - Leg A: straddle at front_dte (e.g. 7d)
   - Leg B: straddle at back_dte (e.g. 30d), opposite direction
   - Size to equal vega_notional per leg

4. HOLD + DAILY REFIT:
   - Recompute slope_z daily on fresh surface fit
   - Delta-hedge each leg independently
   - Roll front leg at roll_before_expiry_dte; re-entry at target front_dte

5. EXIT:
   - slope_z crosses exit_z_threshold (mean reversion complete)
   - Stop loss: vega P&L < -max_loss_vega_pct × initial_vega_notional
   - Time stop: exceeded max_hold_calendar_days
```

## Entry conditions + signal

- Parametric model fit converges (residual RMSE < model_fit_max_rmse)
- `|slope_z| > entry_z_threshold` (default 2.0σ from 30d rolling mean)
- Sufficient open interest at both front and back tenors (min OI check)
- Not in high-vol regime (regime filter applied at strategy level)

## Risk management

- Vega-neutral at entry across legs; residual vega imbalance < vega_balance_tolerance_pct
- Each leg delta-hedged independently on its own hedge band
- Rolling protocol: re-enter front leg within 1 day of roll to maintain continuous slope exposure
- Stop loss: cumulative vega loss > max_loss_vega_pct (default 75% of initial premium at risk)
- Model-fit failure: pause signal generation; hold existing position; alert operator

## Config parameters

- `surface_model`: `heston` | `svi` — parametric model for slope extraction
- `front_dte`: target DTE for front leg (default 7)
- `back_dte`: target DTE for back leg (default 30)
- `slope_lookback_days`: window for rolling slope mean/std (default 30)
- `entry_z_threshold`: slope z-score required to enter (default 2.0)
- `exit_z_threshold`: slope z-score at which to exit (default 0.5)
- `vega_notional_usd`: per-leg vega target (default 20000)
- `vega_balance_tolerance_pct`: max allowed vega imbalance at entry (default 5%)
- `roll_before_expiry_dte`: roll front leg at this DTE (default 2)
- `max_hold_calendar_days`: time stop (default 30)
- `max_loss_vega_pct`: stop loss fraction of initial vega exposure (default 0.75)
- `share_class`: USDT | USD
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: term structure shape at extremes relative to its own history; parametric fit converges cleanly
- **Ideal setup**: post-event vol crush leaves structure in deep contango (short slope); or macro uncertainty compresses
  back-tenor IV faster than front (long slope signal)
- **Avoid**: very shallow option chain at front tenor (low liquidity makes rolling expensive); rapidly evolving
  structural vol regime (slope can trend, not mean-revert, over weeks)
- **Best instruments**: BTC/ETH on Deribit; SPX on CBOE

## Example instances

```
VOL_TERM_STRUCTURE_SLOPE@deribit-btc-slope-7v30dte-usdt-prod
VOL_TERM_STRUCTURE_SLOPE@deribit-eth-slope-7v30dte-usdt-prod
VOL_TERM_STRUCTURE_SLOPE@cboe-spx-slope-weekly-v-monthly-usd-prod
```

## Not in this archetype

- Discrete two-tenor calendar spread without daily parametric refit →
  [`VOL_TERM_STRUCTURE_ARB`](vol-term-structure-arb.md)
- Outright single-tenor short-vol carry without slope signal → [`VOL_CARRY`](vol-carry.md)
- Long-dated LEAPS convexity (single far tenor, no front leg) → [`VOL_LEAPS_CONVEXITY`](vol-leaps-convexity.md)
- Cross-asset vol spread (two correlated underlyings) → [`VOL_CROSS_ASSET_SPREAD`](vol-cross-asset-spread.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Calendar spread (relative value across two tenors): [vol-term-structure-arb.md](vol-term-structure-arb.md)
- Short-vol carry: [vol-carry.md](vol-carry.md)
