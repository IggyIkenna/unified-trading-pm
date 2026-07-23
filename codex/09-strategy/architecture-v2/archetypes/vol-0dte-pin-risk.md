---
doc_type: codex-ssot
title: "Archetype: `VOL_0DTE_PIN_RISK`"
summary:
  "Archetype spec for `VOL_0DTE_PIN_RISK` — manages extreme near-expiry gamma when spot pins a high-OI strike, detecting
  pin proximity then carrying, flattening, or rolling the short-gamma book; Deribit + CBOE SPX, 50ms premium SLA."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, pin-risk, delta-hedge, 0dte]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_0DTE_PIN_RISK archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_0DTE_PIN_RISK
family: VOL_TRADING
venue_universe: [DERIBIT, CBOE]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 50
  min_sla_tier: premium
---

# Archetype: `VOL_0DTE_PIN_RISK`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Same-day or next-day expiry — positions
> closed or rolled before final settlement. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_0dte_pin_risk_engine.py`

## What it does

Manages pin risk when the underlying price approaches an option strike near expiry. As expiry approaches and spot
converges on a strike, gamma becomes extreme and delta flips discontinuously at the pin point — creating significant P&L
uncertainty for any short-gamma book. This archetype detects proximity to open-interest-weighted strikes in the expiring
chain, then decides whether to carry, flatten, or roll the position before the binary gamma event resolves. Operates
both proactively (pre-expiry risk management scanning all live positions) and reactively (triggered by real-time delta
breaches near expiry).

## Token / position flow

```
1. OPEN INTEREST SCAN: read option chain OI across all strikes for expiring series
   - Compute OI-weighted strike grid
   - Identify max-pain strike (max aggregate OI)

2. PIN PROXIMITY CHECK (runs on each tick near expiry):
   pin_proximity = |spot - nearest_high_oi_strike| / spot
   - If pin_proximity < pin_threshold_pct AND dte_hours < pin_risk_window_hours:
     → enter PIN RISK ZONE

3. PIN RISK ZONE — choose action:
   a. CARRY: tolerate; delta-hedge aggressively every tick (gamma too high to leave open)
   b. FLATTEN: close net delta to 0 immediately via underlying trade
   c. ROLL: close expiring position, open next-expiry equivalent to escape binary

4. DELTA HEDGE (if CARRY chosen):
   - Rehedge frequency: every hedge_interval_seconds near expiry
   - Max delta_free_band_pct: tight near expiry (e.g. 0.5% of notional)

5. EXIT / ROLL:
   - ATOMIC roll: close 0DTE leg + open next-expiry leg simultaneously
   - Abort if roll fill fails on either leg (never carry one leg only)

6. POST-EXPIRY: confirm settlement price; reconcile P&L vs expected pin outcome
```

## Entry conditions + signal

- `dte_hours < pin_risk_window_hours` (default: 4 hours to expiry)
- `pin_proximity_pct < pin_threshold_pct` (default: 0.5% of spot)
- Portfolio has open short-gamma exposure in expiring series
- Signal strength: scaled by open interest at the nearby strike (higher OI = stronger pin magnet)

## Risk management

- Never carry unhedged short gamma inside pin risk window — rehedge on every tick
- Stop loss: if delta-hedge cost exceeds `max_hedge_cost_pct` of position value, force flatten
- Roll trigger: roll before expiry if `roll_cost < carry_gamma_cost_estimate`
- Kill switch: if spot moves past pin threshold by more than `blowthrough_pct`, flatten immediately (pin failed — binary
  loss)
- Venue outage during pin risk window: flatten via alternate hedge venue

## Config parameters

- `pin_threshold_pct`: proximity to strike that triggers pin risk zone (default 0.5%)
- `pin_risk_window_hours`: DTE hours before expiry to begin scanning (default 4.0)
- `hedge_interval_seconds`: rehedge frequency inside pin risk zone (default 10)
- `max_hedge_cost_pct`: maximum cumulative hedge cost before forced flatten (default 2.0%)
- `roll_cost_threshold_vp`: max vol-points spread cost acceptable for roll (default 1.5)
- `default_action`: `carry` | `flatten` | `roll` (operator-configured per instrument)
- `share_class`: USDT | USD
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: short-gamma book (vol carry, short straddle) approaches expiry with spot near a high-OI strike
- **Avoid**: no open options positions in expiring series; underlying has low OI concentration
- **Regime**: most relevant during quiet trending markets where spot slowly drifts into a strike zone; also triggered by
  sudden large moves that push spot through a previously-distant strike near expiry
- **Best instruments**: BTC and ETH on Deribit (Friday expiries, weekly), SPX 0DTE (CBOE)

## Example instances

```
VOL_0DTE_PIN_RISK@deribit-btc-friday-expiry-usdt-prod
VOL_0DTE_PIN_RISK@deribit-eth-friday-expiry-usdt-prod
VOL_0DTE_PIN_RISK@cboe-spx-0dte-weekly-usd-prod
```

## Not in this archetype

- Proactive intraday gamma scalping via bought straddle → [`VOL_0DTE_GAMMA_SCALPING`](vol-0dte-gamma-scalping.md)
- Passive theta harvest (generates the short-gamma exposure managed here) → [`VOL_CARRY`](vol-carry.md)
- Longer-tenor straddle positioning without pin-proximity logic → [`VOL_STRADDLE`](vol-straddle.md)
- Calendar spread rolling to escape binary expiry risk → [`VOL_TERM_STRUCTURE_ARB`](vol-term-structure-arb.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Short-vol carry that generates the pin-risk exposure: [vol-carry.md](vol-carry.md)
- Gamma scalping archetype: [vol-0dte-gamma-scalping.md](vol-0dte-gamma-scalping.md)
