---
doc_type: codex-ssot
title: "Archetype: `VOL_SYNTHETIC_DELTA`"
summary:
  "Archetype spec for `VOL_SYNTHETIC_DELTA` — replicates delta-1 exposure via a same-strike call/put synthetic (long
  call + short put, or reverse) to avoid perp funding and define max loss; used when funding > synthetic cost;
  Deribit/OKX/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, synthetic-delta, carry, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-covered-calls.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_SYNTHETIC_DELTA archetype spec"]
referenced_by: [/codex/09-strategy/architecture-v2/families/vol-trading.md]
owner:
last_reviewed:
code_refs:
archetype: VOL_SYNTHETIC_DELTA
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 200
  min_sla_tier: standard
---

# Archetype: `VOL_SYNTHETIC_DELTA`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven — synthetic position settles
> at expiry; rolled to next expiry to maintain continuous directional exposure. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_synthetic_delta_engine.py`

## What it does

Replicates directional delta-1 exposure using options rather than spot or perp instruments, gaining the specific
advantages of defined risk and no funding costs. A synthetic long (long call + short put at the same strike and expiry)
is economically equivalent to a forward purchase of the underlying but carries no perp funding rate and defines maximum
loss at the put strike minus the net premium. A synthetic short (short call + long put) replicates a forward short sale
without perp borrow fees and with defined loss at the call strike. This archetype is used when perp funding rates make
direct delta-1 exposure uneconomic, or when defined-risk exposure is operationally preferred. The engine monitors the
synthetic for early assignment risk and manages rolling to maintain continuous exposure.

## Token / position flow

```
1. DIRECTION SIGNAL:
   - Receive directional view from parent strategy or operator config: LONG | SHORT
   - Verify funding cost comparison: compare perp_funding_rate vs synthetic_cost
     synthetic_cost ≈ (call_ask − put_bid) − (forward_discount × dte / 365)
   - Proceed if synthetic is cheaper than perp funding OR defined risk is required

2. STRIKE SELECTION:
   - Select ATM or near-ATM strike at target_dte expiry
   - Compute mid-market synthetic cost (call − put at same strike/expiry)
   - Verify |synthetic_cost − forward_discount| < max_synthetic_slip_bps (no arb with futures)

3. SYNTHETIC LONG CONSTRUCTION:
   - BUY call (strike K, expiry T) + SELL put (strike K, expiry T)
   - ATOMIC TRADE — must fill both legs simultaneously
   - Net delta ≈ +1 at entry; net vega ≈ 0 (call and put vega partially cancel)
   - Max loss = K − net_premium_paid (put assignment floor)

4. SYNTHETIC SHORT CONSTRUCTION:
   - SELL call (strike K, expiry T) + BUY put (strike K, expiry T)
   - ATOMIC TRADE — must fill both legs simultaneously
   - Net delta ≈ −1 at entry; net vega ≈ 0
   - Max loss = K + net_premium_received (call assignment ceiling)

5. HOLD:
   - Monitor net delta (should stay near ±1 as underlying moves — synthetic tracks forward)
   - Early assignment risk check (American-style venues): if short leg deep ITM near expiry,
     evaluate early close to avoid assignment
   - Funding cost tracking: compare ongoing synthetic carrying cost vs perp roll cost

6. ROLL (before expiry):
   - At roll_before_expiry_dte DTE: ATOMIC close current synthetic + open next-expiry synthetic
   - Capture or pay roll spread (forward calendar spread)

7. EXIT:
   - Directional view closes: close synthetic (ATOMIC buy-back of short leg + sell long leg)
   - Stop loss: underlying moves against position by > stop_loss_underlying_pct
   - Assignment trigger: one leg deep ITM near expiry and early close is preferred
```

## Entry conditions + signal

- Directional signal exists (supplied externally or via operator config)
- `perp_funding_rate_annualised > synthetic_cost_annualised + min_cost_advantage_bps` OR defined-risk mode is active
  (operator preference, regulatory, or risk mandate)
- ATM or near-ATM bid-ask per leg <= max_leg_spread_bps × spot
- DTE within [min_dte_entry, max_dte_entry] (e.g. 14-30 DTE at entry)
- No early-assignment risk flags on synthetic's short leg

## Risk management

- Synthetic long: max loss bounded at put_strike − net_premium_paid; no unlimited downside
- Synthetic short: max loss bounded at call_strike + net_premium_received; no unlimited upside loss
- ATOMIC fill discipline: never carry a naked leg — if one leg fails to fill, abort and cancel other
- Roll cost tracking: synthetic rolling costs must remain cheaper than perp funding over the hold period; re-evaluate vs
  perp at each roll
- Assignment risk: on American-style options (OKX, CBOE), short leg deep ITM > 3 DTE from expiry triggers early-close
  evaluation
- Net vega near zero at construction but drifts as underlying moves; rebalance if vega > vega_drift_limit_usd

## Config parameters

- `underlying`: BTC | ETH | SPX (etc.)
- `venue`: DERIBIT | OKX_OPTIONS | CBOE
- `direction`: long | short
- `strike_selection`: atm | slightly_itm (e.g. 0.98 × spot for synthetic long put leg)
- `target_dte_entry`: DTE at construction (e.g. 14 or 30)
- `roll_before_expiry_dte`: 5
- `max_synthetic_slip_bps`: max acceptable deviation from theoretical fair value (e.g. 10)
- `min_cost_advantage_bps`: minimum annualised saving over perp funding to justify synthetic (e.g. 50)
- `max_leg_spread_bps`: max bid-ask per leg (e.g. 20)
- `vega_drift_limit_usd`: rebalance vega if drift exceeds this (e.g. 5000)
- `stop_loss_underlying_pct`: close if underlying moves this far against position (e.g. 0.08 = 8%)
- `max_notional_usd`: total synthetic position cap
- `early_assignment_dte_threshold`: check early assignment risk when short leg ≤ this DTE (e.g. 5)

## When to use / market regime

- **Best regime**: high perp funding environments (crypto bull runs) where long synthetic costs less than rolling the
  perp; or when operational risk policy mandates defined-max-loss positions
- **Avoid**: low-funding environments where perp is cheaper and simpler; also avoid on illiquid option chains where leg
  spreads erode the cost advantage
- **Asset fit**: BTC, ETH (Deribit; deep ATM liquidity); SPX/SPY for TradFi directional with defined risk
- **Complements**: `CARRY_BASIS_PERP` (use synthetic long instead of perp when funding is high); any strategy that would
  otherwise use a perp for delta-1 exposure

## Example instances

```
VOL_SYNTHETIC_DELTA@deribit-btc-synthetic-long-14dte-usdt-prod
VOL_SYNTHETIC_DELTA@deribit-eth-synthetic-long-30dte-usdt-prod
VOL_SYNTHETIC_DELTA@deribit-btc-synthetic-short-14dte-usdt-prod
```

## Not in this archetype

- Delta-1 long via spot or perp (no defined-risk structure, no expiry management) →
  [`CARRY_BASIS_PERP`](carry-basis-perp.md)
- Long straddle (ATM call + put at same strike to express a vol view, not delta-1) → [`VOL_STRADDLE`](vol-straddle.md)
- Directional options expression where the alpha is an ML or signal view on underlying price, not cost-of-carry vs perp
  → [`ML_DIRECTIONAL_CONTINUOUS`](ml-directional-continuous.md)
- Covered call overlay against an existing long (income generation, not directional replication) →
  [`VOL_OVERLAY_COVERED_CALLS`](vol-overlay-covered-calls.md)

## See also

- Vol carry: [vol-carry.md](vol-carry.md)
- Straddle: [vol-straddle.md](vol-straddle.md)
- Covered call overlay: [vol-overlay-covered-calls.md](vol-overlay-covered-calls.md)
- Family: [vol-trading.md](../families/vol-trading.md)
