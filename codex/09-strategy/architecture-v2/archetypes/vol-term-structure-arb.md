---
doc_type: codex-ssot
title: "Archetype: `VOL_TERM_STRUCTURE_ARB`"
summary:
  "Archetype spec for `VOL_TERM_STRUCTURE_ARB` — a discrete dual-expiry calendar spread that buys the underpriced tenor
  and sells the overpriced one on term-slope z-score (|z| > 2), vega-neutral and delta-hedged; Deribit/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, term-structure, calendar-spread, mean-reversion]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-slope.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_TERM_STRUCTURE_ARB archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-spread-structures.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-slope.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-variance-swap.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_TERM_STRUCTURE_ARB
family: VOL_TRADING
venue_universe: [DERIBIT, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_TERM_STRUCTURE_ARB`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Dual-expiry calendar spread — near-tenor
> position + far-tenor position rolled at respective expiries. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_term_structure_arb_engine.py`

## What it does

Exploits mispricings along the volatility term structure by simultaneously buying vol at an underpriced tenor and
selling vol at an overpriced tenor on the same underlying. The calendar spread is implemented via options at two expiry
dates, isolating the term structure bet from outright directional vol exposure. The signal compares the current term
structure slope (near IV / far IV ratio) against its rolling historical norm: a flat or inverted structure (front cheap
relative to back) signals a buy-front / sell-back entry expecting re-steepening; a steep structure signals sell-front /
buy-back expecting flattening. Profit is earned when the term structure shape normalises toward its historical average.

## Token / position flow

```
1. SURFACE FITTER: fit vol surface to full option chain at near + far expiries
   - Extract ATM IV at near tenor (e.g. 14 DTE) and far tenor (e.g. 30 DTE)
   - Compute term structure slope: slope = far_IV - near_IV (in vol points)

2. SIGNAL GENERATION:
   - Rolling 30d mean slope: mu_slope, std_slope
   - z_score = (slope - mu_slope) / std_slope
   - Entry LONG SLOPE (buy near, sell far): z_score < -entry_z_threshold
     (structure flat/inverted vs history → expect re-steepening)
   - Entry SHORT SLOPE (sell near, buy far): z_score > +entry_z_threshold
     (structure steep vs history → expect flattening)

3. POSITION SIZING:
   - Match vega_notional at near and far tenors (vega-neutral calendar spread)
   - Slight net vega if directional view: configured by vega_tilt_pct

4. ENTRY: ATOMIC dual-expiry option trade
   - Near leg: straddle at near_expiry_dte
   - Far leg: straddle at far_expiry_dte (opposite direction)

5. HOLD + MONITOR:
   - Track slope z_score daily; delta-hedge each leg independently
   - Roll near leg when dte < roll_before_expiry_dte

6. EXIT:
   - z_score crosses exit_z_threshold (mean reversion confirmed)
   - Stop loss: loss > max_loss_vega_pct × initial_premium
   - Time stop: hold > max_hold_days
```

## Entry conditions + signal

- `|z_score| > entry_z_threshold` (default 2.0)
- Both near and far options liquid enough for simultaneous fill (min open interest check)
- No high-vol regime active (IV > high_vol_regime_iv_threshold)
- Calendar spread transaction cost < signal edge estimate

## Risk management

- Vega must be matched at entry; tolerate residual < vega_mismatch_tolerance_pct
- Delta-hedge each leg on its own hedge band — do not net-delta across expiries
- Stop loss: total vega loss > stop_loss_vega_pct × initial_premium
- Roll near leg at roll_before_expiry_dte to avoid 0DTE gamma while holding far leg
- Venue outage: flatten both legs; never carry single-expiry calendar position

## Config parameters

- `near_tenor_dte`: target DTE for near leg at entry (default 14)
- `far_tenor_dte`: target DTE for far leg at entry (default 30)
- `entry_z_threshold`: z-score threshold for entry (default 2.0)
- `exit_z_threshold`: z-score threshold for exit (default 0.5)
- `slope_lookback_days`: rolling window for slope mean/std (default 30)
- `vega_notional_usd`: per-leg target vega exposure (default 25000)
- `vega_mismatch_tolerance_pct`: max residual vega imbalance at entry (default 5%)
- `vega_tilt_pct`: intentional vega lean if directional view present (default 0%)
- `roll_before_expiry_dte`: roll near leg at this DTE (default 3)
- `stop_loss_vega_pct`: exit if vega loss exceeds this fraction of premium (default 0.75)
- `max_hold_days`: time stop in calendar days (default 21)
- `share_class`: USDT | USD
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: vol term structure at multi-week extreme vs historical norm; sufficient option liquidity at both tenors
- **Best regime**: post-event vol crush (structure steeply inverted) or quiet trending markets (structure flat when
  fear-buying pushes front vol up)
- **Avoid**: low liquidity at far tenor; very steep carry costs make roll expensive; high-vol regime with persistent
  inverted structure (structure can stay inverted longer than position can stay solvent)
- **Best instruments**: BTC/ETH on Deribit; SPX/SPY on CBOE

## Example instances

```
VOL_TERM_STRUCTURE_ARB@deribit-btc-calendar-14v30dte-usdt-prod
VOL_TERM_STRUCTURE_ARB@deribit-eth-calendar-14v30dte-usdt-prod
VOL_TERM_STRUCTURE_ARB@cboe-spx-calendar-monthly-usd-prod
```

## Not in this archetype

- Continuous parametric slope signal (Heston/SVI fit, daily refit) →
  [`VOL_TERM_STRUCTURE_SLOPE`](vol-term-structure-slope.md)
- Outright single-tenor short-vol premium harvest → [`VOL_CARRY`](vol-carry.md)
- Cross-asset vol spread (two correlated underlyings, same tenor) →
  [`VOL_CROSS_ASSET_SPREAD`](vol-cross-asset-spread.md)
- Long-dated convexity via LEAPS (single far tenor, no calendar spread) →
  [`VOL_LEAPS_CONVEXITY`](vol-leaps-convexity.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Vol carry (outright short-vol): [vol-carry.md](vol-carry.md)
- Term structure slope trading: [vol-term-structure-slope.md](vol-term-structure-slope.md)
