---
doc_type: codex-ssot
title: "Archetype: `VOL_OVERLAY_PROTECTIVE_PUT`"
summary:
  "Archetype spec for `VOL_OVERLAY_PROTECTIVE_PUT` — buys 15-30 delta OTM puts as tail insurance on a delta-1 long
  (optionally financed as a collar via a covered call); a cost-centre bounding drawdown to strike + premium;
  Deribit/OKX."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, protective-put, overlay, hedging]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-covered-calls.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_OVERLAY_PROTECTIVE_PUT archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-covered-calls.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_OVERLAY_PROTECTIVE_PUT
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 300
  min_sla_tier: standard
---

# Archetype: `VOL_OVERLAY_PROTECTIVE_PUT`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven — puts purchased per expiry
> cycle; rolled before expiry to maintain continuous tail protection. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_overlay_protective_put_engine.py`

## What it does

Buys OTM puts as tail-risk insurance against existing delta-1 long positions (spot or perp). Targets 15-30 delta puts
(roughly 1-2 standard deviations below spot), providing meaningful downside protection without excessive premium cost.
The put floor limits maximum drawdown on the underlying long to the distance between spot and strike, plus the premium
paid. When the put premium budget is constrained, the overlay is structured as a collar: simultaneously writing a
covered call (see `VOL_OVERLAY_COVERED_CALLS`) to finance the put purchase, capping both upside and downside. This
archetype is a cost centre by design — P&L is the insurance cost paid against the protected underlying position's P&L.

## Token / position flow

```
1. UNDERLYING POSITION CHECK:
   - Read delta-1 long (spot qty or perp notional) from position manager
   - Compute max_put_contracts = floor(underlying_qty / contract_multiplier)

2. PUT SELECTION:
   - Fetch options chain for target expiry (target_dte_entry DTE)
   - Find OTM put at target_put_delta (e.g. 0.20 = 20d put)
   - Compute ask premium; check against max_premium_budget_pct of position notional

3. COLLAR CHECK (if collar_mode = true):
   - Simultaneously select OTM call at target_call_delta to finance put
   - Collar net premium = call_bid − put_ask; must be >= collar_min_net_credit (can be zero/negative)

4. POSITION SIZING:
   - Buy put_coverage_ratio × max_put_contracts
   - In collar mode: write same ratio of calls (matched notional)

5. ENTRY:
   - Standalone put: BUY put via TRADE instruction
   - Collar: ATOMIC (BUY put + SELL call simultaneously)

6. HOLD:
   - Monitor underlying vs put strike for exercise probability
   - Monitor IV change: if IV collapses post-entry (put cheapens), evaluate early roll to new strike
   - If underlying rallies > put_roll_down_trigger_pct above entry, optionally roll put up
     to lock in gains while maintaining protection

7. EXIT / ROLL:
   - Roll before expiry: at roll_before_expiry_dte DTE, close expiring put and buy next cycle
   - Underlying crashes through put strike: put P&L offsets underlying loss (payoff activated)
   - IV spike: put mark-to-market increases — hold or partially take profit if IV extreme
   - Operator closes underlying: sell put back before closing underlying
```

## Entry conditions + signal

- Underlying delta-1 long position exists and size >= min_underlying_qty
- Put ask premium <= max_premium_budget_pct × position_notional (budget discipline)
- ATM IV within acceptable range (avoid buying puts at IV extremes — expensive protection)
- In collar mode: collar net debit <= max_collar_net_debit_pct × position_notional
- DTE within [min_dte_entry, max_dte_entry] — prefer 30-60 DTE for better time value balance

## Risk management

- Max loss on underlying side = (entry_spot − put_strike) + put_premium_paid per unit
- Collar adds upside cap at call_strike; gains above call strike are foregone
- Never let put expire without rolling: lapse in protection creates unhedged tail risk window
- Put premium cost is an explicit drag on portfolio returns — track as `insurance_cost_bps` in attribution
- Avoid over-hedging: put_coverage_ratio <= 1.0 (cannot hedge more than the underlying position size)
- Rolling cost escalation: if IV rises sharply, rolling becomes expensive; track rolling_annualised_cost

## Config parameters

- `underlying`: BTC | ETH | SOL (etc.)
- `venue`: DERIBIT | OKX_OPTIONS
- `underlying_position_source`: spot | perp | both
- `target_put_delta`: delta of put to buy (e.g. 0.20 = 20d, 0.30 = 30d)
- `target_dte_entry`: DTE at put purchase (e.g. 30 or 60)
- `roll_before_expiry_dte`: 5 (roll earlier than vol_carry to avoid gamma whipsaw)
- `put_coverage_ratio`: fraction of underlying quantity to protect (e.g. 1.0 = fully covered)
- `max_premium_budget_pct`: max annual premium as % of notional (e.g. 0.03 = 3% budget)
- `collar_mode`: false | true (also write covered call to finance put)
- `target_call_delta`: if collar_mode, delta of call to write (e.g. 0.20)
- `max_collar_net_debit_pct`: max acceptable net debit in collar as % of notional (e.g. 0.005)
- `put_roll_up_trigger_pct`: roll put up if underlying rallies this much above entry (e.g. 0.10 = 10%)
- `rolling_cost_alert_bps`: alert if annualised rolling cost exceeds threshold

## When to use / market regime

- **Best regime**: after a strong rally when tail risk is elevated but IV is still moderate — puts are relatively cheap
  relative to the downside risk of an extended position
- **Collar regime**: low-IV, sideways markets where upside is limited anyway — the collar funds itself and reduces drag
- **Avoid**: very high IV environments (put premium is prohibitively expensive); or when portfolio already has natural
  hedges (DeFi protocol shorts, basis trades on the other side)
- **Asset fit**: BTC, ETH with large spot or perp longs; any position where drawdown management is critical

## Example instances

```
VOL_OVERLAY_PROTECTIVE_PUT@deribit-btc-put-30dte-usdt-prod
VOL_OVERLAY_PROTECTIVE_PUT@deribit-eth-put-30dte-usdt-prod
VOL_OVERLAY_PROTECTIVE_PUT@deribit-btc-collar-30dte-usdt-prod
```

## Not in this archetype

- Writing calls against the long to generate premium income (covered call overlay) →
  [`VOL_OVERLAY_COVERED_CALLS`](vol-overlay-covered-calls.md)
- Buying puts without an existing delta-1 long as a standalone vol view → [`VOL_STRADDLE`](vol-straddle.md) or
  [`VOL_ARB_RV_IV`](vol-arb-rv-iv.md)
- Structural short-vol carry — this archetype is a cost centre (long vol insurance), not a carry harvester →
  [`VOL_CARRY`](vol-carry.md)
- Tail hedging via perp short rather than options (delta-1 hedge, no premium) →
  [`CARRY_BASIS_PERP`](carry-basis-perp.md)

## See also

- Covered call overlay: [vol-overlay-covered-calls.md](vol-overlay-covered-calls.md)
- Straddle: [vol-straddle.md](vol-straddle.md)
- Family: [vol-trading.md](../families/vol-trading.md)
