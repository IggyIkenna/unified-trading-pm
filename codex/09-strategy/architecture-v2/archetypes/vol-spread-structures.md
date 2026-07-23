---
doc_type: codex-ssot
title: "Archetype: `VOL_SPREAD_STRUCTURES`"
summary:
  "Archetype spec for `VOL_SPREAD_STRUCTURES` — trades vol-surface shape (not level) via vega-neutral calendar and
  butterfly spreads on term-structure slope and 25d smile signals, delta-hedged; Deribit/OKX/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, calendar-spread, butterfly, term-structure]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_SPREAD_STRUCTURES archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_SPREAD_STRUCTURES
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 200
  min_sla_tier: standard
---

# Archetype: `VOL_SPREAD_STRUCTURES`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven per leg — each leg settles
> at its own expiry; calendar and butterfly spreads managed to expiry with roll logic. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_spread_structures_engine.py`

## What it does

Trades the shape of the implied vol term structure and smile through calendar spreads and butterfly spreads. Calendar
spread: buy back-month vol and sell front-month vol when the term structure is inverted (backwardation), expecting
reversion to the normal contango shape; reverse when contango is extreme. Butterfly spread: sell two mid-strike options
and buy the wing strikes to capture flattening of the vol smile — profits when realized skew is lower than implied by
the smile. Both structures are vega-neutral at entry and isolate shape risk rather than level risk. Delta-hedge the
aggregate book to remove directional exposure.

## Token / position flow

```
1. TERM STRUCTURE READER:
   - Fetch ATM IV at multiple tenors: front (7 DTE), mid (30 DTE), back (90 DTE)
   - Compute term structure slope: slope = IV_back − IV_front
   - Detect backwardation: slope < -backwardation_threshold_vp

2. SMILE READER:
   - Fetch vol smile at target tenor (25d put IV, ATM IV, 25d call IV)
   - Compute 25d risk reversal: RR = IV_25d_put − IV_25d_call
   - Compute 25d butterfly: BF = (IV_25d_put + IV_25d_call) / 2 − IV_atm
   - Signal: BF > bf_entry_threshold_vp → expect flattening → short butterfly

3. CALENDAR SPREAD CONSTRUCTION:
   - Backwardation entry: BUY back-month straddle, SELL front-month straddle (same strike)
   - Contango entry (term arb reversed): BUY front-month, SELL back-month when spread extreme
   - Size: match vega across legs so net vega ≈ 0 at entry

4. BUTTERFLY SPREAD CONSTRUCTION:
   - SELL 2× ATM options (call or put), BUY 1× each OTM wing
   - Same expiry; strikes evenly spaced in delta space
   - Net vega ≈ 0 (long wings partially offset short body)

5. HOLD:
   - Calendar: monitor term structure slope convergence as take-profit signal
   - Butterfly: monitor butterfly premium decay as profit
   - Delta-hedge aggregate book via underlying perp

6. EXIT:
   - Calendar: slope reverts past exit_slope_threshold_vp, or front leg approaches expiry
   - Butterfly: spread captures > take_profit_pct of initial butterfly premium
   - Stop: mark-to-market loss > stop_loss_pct of initial notional
   - Forced roll: front leg at roll_before_expiry_dte DTE
```

## Entry conditions + signal

- **Calendar (backwardation)**: `IV_front − IV_back > backwardation_threshold_vp` and slope z-score > 1.5
- **Calendar (contango arb)**: `IV_back − IV_front > contango_extreme_vp` and slope z-score > 1.5
- **Butterfly**: `25d_BF_vol > bf_entry_threshold_vp` and BF is in top quintile of 60-day distribution
- All structures require underlying liquidity check: bid-ask < max_leg_spread_vp per leg

## Risk management

- Net vega ≈ 0 at entry; rebalance if vega drifts beyond vega_drift_limit_usd due to moves
- Calendar spread risk: front gamma can spike near expiry — roll before roll_before_expiry_dte
- Butterfly risk: convex loss if vol moves sharply past wing strikes; wings cap max loss
- Stop loss: aggregate portfolio loss > stop_loss_pct × initial_notional → close all legs
- Never add to a losing structure without explicit signal re-confirmation

## Config parameters

- `underlying`: BTC | ETH | SPX (etc.)
- `venue`: DERIBIT | OKX_OPTIONS | CBOE
- `structure_type`: calendar | butterfly | both
- `front_dte`: target front-month DTE (e.g. 7)
- `back_dte`: target back-month DTE (e.g. 30 for calendar)
- `roll_before_expiry_dte`: 3
- `backwardation_threshold_vp`: term-structure inversion threshold in vol points (e.g. 3.0)
- `contango_extreme_vp`: contango extreme threshold in vol points (e.g. 5.0)
- `bf_entry_threshold_vp`: minimum butterfly premium in vol points (e.g. 2.0)
- `butterfly_wing_delta`: delta of wing strikes (e.g. 0.25 = 25d)
- `max_leg_spread_vp`: maximum bid-ask per leg in vol points (liquidity filter)
- `vega_drift_limit_usd`: rebalance threshold for vega neutrality (e.g. 2000)
- `take_profit_pct`: exit on capturing this fraction of max profit (e.g. 0.60)
- `stop_loss_pct`: stop loss as fraction of initial notional (e.g. 0.30)

## When to use / market regime

- **Calendar (backwardation)**: after vol spikes when spot market recovers — front IV stays elevated while back IV
  normalises; expect curve to revert to contango within days to weeks
- **Butterfly**: quiet, range-bound markets where the smile is rich but unlikely to be realised; captures over-priced
  skew structure without large directional or vol-level risk
- **Avoid**: fast-trending markets or during liquidity crises where spreads widen materially per leg
- **Asset fit**: BTC, ETH (Deribit has the deepest multi-expiry options book); SPX for TradFi calendars

## Example instances

```
VOL_SPREAD_STRUCTURES@deribit-btc-calendar-7-30dte-usdt-prod
VOL_SPREAD_STRUCTURES@deribit-eth-butterfly-30dte-usdt-prod
VOL_SPREAD_STRUCTURES@cboe-spx-calendar-weekly-usd-prod
```

## Not in this archetype

- IV vs RV level divergence trade (not shape) — enter long or short vol on absolute spread threshold →
  [`VOL_ARB_RV_IV`](vol-arb-rv-iv.md)
- Structural short-vol carry (sell straddle to harvest theta/carry premium) → [`VOL_CARRY`](vol-carry.md)
- ATM straddle held for a binary event catalyst → [`VOL_STRADDLE`](vol-straddle.md)
- Hard calendar no-arb violation (calendar spread below zero cost-of-carry) — mechanical arbitrage, not statistical →
  [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## See also

- Vol carry: [vol-carry.md](vol-carry.md)
- RV vs IV arb: [vol-arb-rv-iv.md](vol-arb-rv-iv.md)
- Straddle: [vol-straddle.md](vol-straddle.md)
- Family: [vol-trading.md](../families/vol-trading.md)
