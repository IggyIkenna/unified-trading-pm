---
doc_type: codex-ssot
title: "Archetype: `VOL_VARIANCE_SWAP`"
summary:
  "Archetype spec for `VOL_VARIANCE_SWAP` — replicates a variance swap via a 1/K² static option strip plus daily
  delta-hedging, trading the var_strike vs realised-variance gap; payoff (RV²−K²)×vega/2; Deribit BTC/ETH only."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, variance-swap, replication, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ratio-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_VARIANCE_SWAP archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ratio-spread.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_VARIANCE_SWAP
family: VOL_TRADING
venue_universe: [DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 200
  min_sla_tier: standard
---

# Archetype: `VOL_VARIANCE_SWAP`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven — variance swap replication
> held to expiry or unwound early; strike and notional fixed at entry. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_variance_swap_engine.py`

## What it does

Replicates a synthetic variance swap position via a static strip of options across all available strikes, combined with
continuous delta-hedging. The variance swap payoff is `(RV² - strike_variance²) × vega_notional / 2`, where
`strike_variance` is the fair variance (vol-squared) at entry. A long variance position profits if realised variance
exceeds implied; short position profits if realised variance is below implied. The log-contract replication approach
requires holding options at every available strike in proportion to `1/K²`, with the full strip delta-hedged daily.
Deribit provides sufficient strike breadth for BTC and ETH to approximate the theoretical continuous strip closely.

## Token / position flow

```
1. FAIR VARIANCE COMPUTATION:
   - Integrate option prices across strike grid: var_strike = 2/T × ∫(C(K)/K² + P(K)/K²)dK
   - Compare against rolling realised variance (30d RV²)
   - variance_premium = var_strike - RV²  (positive = rich implied variance)

2. SIGNAL CHECK:
   - SHORT VARIANCE (collect premium): variance_premium > min_variance_premium
   - LONG VARIANCE (buy cheap vol): variance_premium < -min_variance_premium

3. OPTION STRIP CONSTRUCTION:
   - Buy/sell options at each strike K in proportion to weight_K = 1/K²
   - Span full available strike range (OTM puts: low K; ATM; OTM calls: high K)
   - Normalise to target_vega_notional_usd across full strip

4. ENTRY: staged ATOMIC fills across strike grid
   - Enter low-liquidity strikes first (OTM extremes) to ensure full strip coverage
   - Abort strip if any anchor strike fails to fill within fill_timeout_seconds

5. DELTA HEDGE (daily):
   - Aggregate delta of full strip
   - Hedge via BTC-PERPETUAL on Deribit (or underlying future)
   - Rehedge when |net_delta| > delta_hedge_band_pct × vega_notional

6. EXIT:
   - HOLD TO EXPIRY: settle variance swap at realised variance over the period
   - EARLY EXIT: unwind all legs if variance_pnl < -stop_loss_pct × notional
   - PARTIAL EXIT: trim strip symmetrically when equity falls below equity_floor
```

## Entry conditions + signal

- `|variance_premium| > min_variance_premium` in vol-points-squared (default 5.0)
- Strike grid spans at least strike_coverage_ratio (default 0.6) of theoretical weight
- Sufficient OI at OTM wings (min_wing_oi check per strike)
- No venue-wide liquidity event (OI drop > oi_drop_alert_threshold within 24h)

## Risk management

- Short variance position has theoretically unlimited loss (variance can spike to infinity)
- Mandatory stop loss: `stop_loss_pct` of notional (default 50%); DO NOT wave for short variance
- Long variance: limited to premium paid; upside uncapped
- Wing concentration limit: no single OTM strike > max_single_strike_weight_pct of total strip weight
- Delta hedge drift: recompute aggregate delta on every option-price update; hedge daily minimum
- Expiry: never hold incomplete strip past roll_before_expiry_dte (missing strikes break replication)

## Config parameters

- `underlying`: `BTC` | `ETH` (Deribit; sufficient strike breadth)
- `target_tenor_dte`: target DTE at entry (default 30)
- `direction`: `short` | `long` — position in variance swap
- `target_vega_notional_usd`: total strip notional in USD (default 50000)
- `min_variance_premium`: minimum var_strike vs RV² gap to enter (default 5.0, in vol-pt²)
- `strike_coverage_ratio`: minimum fraction of theoretical strip filled (default 0.60)
- `min_wing_oi`: minimum OI at each OTM strike to count in strip (default 100)
- `max_single_strike_weight_pct`: max weight any single strike can contribute (default 15%)
- `delta_hedge_band_pct`: rehedge when |delta| > this fraction of vega_notional (default 0.05)
- `stop_loss_pct`: maximum loss as fraction of notional before forced exit (default 0.50)
- `roll_before_expiry_dte`: exit all legs at this DTE if not expired (default 3)
- `fill_timeout_seconds`: max wait per strike fill during strip entry (default 30)
- `share_class`: USDT
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: clear and significant gap between implied variance and realised variance; option chain has broad strike
  coverage (Deribit BTC/ETH monthly expiries are best candidates)
- **Short variance**: high IV relative to recent RV; post-event when options still rich; carry-extracting regime
- **Long variance**: anticipating a vol event; IV historically cheap vs future vol expectations; tail-risk hedge
- **Avoid**: thin option chains with few strikes (replication breaks down); very near-term expiries where strip entry
  costs exceed variance premium; altcoins without sufficient OTM option liquidity

## Example instances

```
VOL_VARIANCE_SWAP@deribit-btc-varswap-30dte-usdt-prod
VOL_VARIANCE_SWAP@deribit-eth-varswap-30dte-usdt-prod
VOL_VARIANCE_SWAP@deribit-btc-varswap-30dte-usdt-paper
```

## Not in this archetype

- Dispersion trade (index vs basket of component vols) → [`VOL_DISPERSION`](vol-dispersion.md)
- Outright short straddle / strangle (single-strike, no replication strip) → [`VOL_CARRY`](vol-carry.md)
- OTM skew harvest via ratio spread (two strikes, single expiry) → [`VOL_RATIO_SPREAD`](vol-ratio-spread.md)
- Calendar vol spread across two expiry tenors → [`VOL_TERM_STRUCTURE_ARB`](vol-term-structure-arb.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Vol carry (simpler short-vol implementation): [vol-carry.md](vol-carry.md)
- Dispersion (trades correlation vs average component vol): [vol-dispersion.md](vol-dispersion.md)
