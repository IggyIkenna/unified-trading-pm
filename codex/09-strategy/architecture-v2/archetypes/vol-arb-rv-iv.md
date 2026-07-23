---
doc_type: codex-ssot
title: "Archetype: `VOL_ARB_RV_IV`"
summary:
  "Archetype spec for `VOL_ARB_RV_IV` — trades mean-reversion in the IV−RV spread (buy vol when IV is below RV, sell
  when above), delta-hedged; entry at |IV−RV| ≥ ~4 vol points with z-score confirm; Deribit/OKX/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, iv-rv, mean-reversion, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-spread-structures.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ml-lean.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_ARB_RV_IV archetype spec"]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/tradfi/volatility-surface.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-protective-put.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-spread-structures.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-trading-options.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_ARB_RV_IV
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 200
  min_sla_tier: standard
---

# Archetype: `VOL_ARB_RV_IV`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous — positions rolled at expiry;
> delta-hedged throughout hold. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_arb_rv_iv_engine.py`

## What it does

Trades the divergence between realized volatility (RV) and implied volatility (IV) on a directional basis: buy vol when
IV is significantly below RV (vol depressed, market under-pricing realized risk), and sell vol when IV is significantly
above RV (vol premium, market over-pricing risk). Unlike `VOL_CARRY` which harvests the steady IV-over-RV structural
premium, this archetype times entries around periods when that relationship breaks down or inverts. The edge is
mean-reversion in the IV-RV spread, not structural carry. Delta-hedge the options book continuously to isolate the vol
view from directional noise.

## Token / position flow

```
1. RV CALCULATOR:
   - Compute rolling realized vol windows: RV_5d, RV_10d, RV_20d (annualised, close-to-close)
   - Compute composite RV_blend = weighted average of windows per config

2. IV READER:
   - Fetch ATM IV at target tenor from surface fitter or live options chain
   - Compute IV_RV_spread = IV − RV_blend (positive = vol premium, negative = vol depressed)

3. SIGNAL:
   - IV_RV_spread > +entry_threshold_vp → SELL_VOL entry (IV elevated vs RV)
   - IV_RV_spread < −entry_threshold_vp → BUY_VOL entry (IV depressed vs RV)
   - |spread| < exit_threshold_vp (normalised) → close vol position

4. POSITION SIZING:
   - Size in vega_notional_usd proportional to |IV_RV_spread| (larger spread → larger position)
   - Cap at max_vega_notional_usd

5. ENTRY: ATOMIC multi-leg TRADE (straddle or strangle per expression config)
   - SELL_VOL: short straddle/strangle
   - BUY_VOL: long straddle/strangle

6. HOLD + REHEDGE:
   - Delta-hedge via underlying perp/future when |net_delta| > delta_hedge_band_pct
   - Monitor IV_RV_spread convergence as exit signal

7. EXIT:
   - Spread convergence: |IV_RV_spread| < exit_threshold_vp
   - Stop loss: P&L < -stop_loss_pct × initial_premium_notional
   - Time: roll at roll_before_expiry_dte DTE
   - Regime override: if RV accelerates past rv_stop_multiple × IV, exit long-vol trade
```

## Entry conditions + signal

- Long vol: `IV_RV_spread < -entry_threshold_vp` (IV under-pricing realized moves)
- Short vol: `IV_RV_spread > +entry_threshold_vp` (IV over-pricing realized moves)
- Confirm with z-score: `|z_score_20d| > zscore_min_entry` to filter noise
- Suppress entry during known binary events unless event-driven mode enabled

## Risk management

- Delta-hedge continuously; rehedge when |portfolio_delta| > delta_hedge_band_pct × vega_notional
- Stop loss on both long-vol (theta bleed) and short-vol (vol spike) sides
- Long-vol stop: cumulative theta cost > max_theta_bleed_pct × notional without convergence
- Short-vol stop: vega loss > stop_loss_vega_pct × initial_premium
- Never hold through expiry without explicit roll instruction

## Config parameters

- `underlying`: BTC | ETH | SPX (etc.)
- `venue`: DERIBIT | OKX_OPTIONS | CBOE
- `target_dte_entry`: 7-21 (days to expiry at entry)
- `roll_before_expiry_dte`: 3 (roll when ≤ this DTE)
- `entry_threshold_vp`: minimum |IV - RV| in vol points to trigger entry (e.g. 4.0)
- `exit_threshold_vp`: spread convergence threshold to exit (e.g. 1.5)
- `zscore_min_entry`: z-score of spread required for entry confirmation (e.g. 1.5)
- `rv_windows_days`: [5, 10, 20] — rolling RV calculation windows
- `rv_blend_weights`: [0.3, 0.4, 0.3] — weighted blend across windows
- `max_vega_notional_usd`: position cap in USD vega exposure
- `delta_hedge_band_pct`: rehedge threshold as fraction of vega_notional
- `stop_loss_vega_pct`: short-vol stop (e.g. 0.75 = exit at 75% premium loss)
- `max_theta_bleed_pct`: long-vol stop (e.g. 0.40 = exit after losing 40% to theta)
- `expression`: straddle | strangle

## When to use / market regime

- **Best regime**: post-vol-spike recovery (IV remains elevated, RV has collapsed → short vol); or pre-event calm (RV
  rising, IV lagging → long vol before binary event)
- **Avoid**: trending markets with fast-moving RV where spread oscillates without mean-reverting
- **Asset fit**: BTC, ETH (deepest options liquidity on Deribit); SPX weeklies for TradFi expression
- **Complements**: `VOL_CARRY` (carry harvests structural premium; this archetype times the breakdowns)

## Example instances

```
VOL_ARB_RV_IV@deribit-btc-straddle-14dte-usdt-prod
VOL_ARB_RV_IV@deribit-eth-straddle-14dte-usdt-prod
VOL_ARB_RV_IV@cboe-spx-straddle-weekly-usd-prod
```

## Not in this archetype

- Structural short-vol carry harvesting the steady IV-over-RV premium without timing entries →
  [`VOL_CARRY`](vol-carry.md)
- Calendar or butterfly spread trading on term structure and smile shape rather than IV-RV level →
  [`VOL_SPREAD_STRUCTURES`](vol-spread-structures.md)
- ATM straddle held for a specific binary catalyst (event-driven vol) → [`VOL_STRADDLE`](vol-straddle.md)
- ML-forecast-driven vol sizing where the signal is a model prediction, not a rule-based spread threshold →
  [`VOL_ML_LEAN`](vol-ml-lean.md)
- Hard no-arb violations (put-call parity, butterfly convexity) →
  [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## See also

- Vol carry: [vol-carry.md](vol-carry.md)
- Spread structures: [vol-spread-structures.md](vol-spread-structures.md)
- Family: [vol-trading.md](../families/vol-trading.md)
