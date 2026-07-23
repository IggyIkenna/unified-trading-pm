---
doc_type: codex-ssot
title: "Archetype: `VOL_STRADDLE`"
summary:
  "Archetype spec for `VOL_STRADDLE` — long ATM straddle ahead of binary catalysts (gamma-scalped, exit post IV-crush)
  or short straddle in IV-elevated calm; a directionless pure-vol view; Deribit/OKX/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, straddle, event-driven, gamma-scalping]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-spread-structures.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_STRADDLE archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-covered-calls.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-protective-put.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-spread-structures.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-synthetic-delta.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_STRADDLE
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_STRADDLE`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Event-driven or expiry — straddles held
> through a catalyst or to expiry; long straddles gamma-scalped intraday. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_straddle_engine.py`

## What it does

Buys or sells the ATM straddle (equal quantities of ATM call and ATM put at the same strike and expiry) to express a
pure volatility view without directional bias. Long straddle is entered before binary catalysts — protocol upgrades,
governance votes, major macro prints, ETF approval decisions — when realized vol is expected to exceed current implied
vol; the position profits from large moves in either direction. Short straddle is entered during IV-elevated quiet
periods when the market is over-pricing uncertainty and a calm outcome is expected. At entry, delta is approximately
zero. Long straddle holders gamma-scalp by delta-hedging intraday moves, collecting realized gamma against the theta
bleed; the strategy wins if cumulative gamma scalp income exceeds theta cost.

## Token / position flow

```
1. CATALYST CALENDAR (long-straddle mode):
   - Ingest event calendar: protocol upgrades, governance votes, macro prints, listing events
   - days_to_event <= entry_days_before_event: begin monitoring for straddle entry
   - Compute expected_move = ATM IV × sqrt(event_dte / 365) (market-implied 1σ move for event)
   - If analyst_expected_move > expected_move × event_move_premium_threshold: LONG straddle signal

2. IV SIGNAL (short-straddle mode):
   - Compute IV_z_score_60d: current ATM IV z-score on 60-day rolling window
   - If IV_z_score > iv_zscore_short_entry and no binary event within tenor: SHORT straddle signal
   - Confirm: RV_5d < IV × rv_suppression_threshold (RV is quiet relative to IV)

3. POSITION SIZING:
   - Size in vega_notional_usd per config; map to ATM straddle contracts
   - ATM straddle cost ≈ 2 × ATM_IV × sqrt(dte/365) × spot_price × contracts

4. ENTRY: ATOMIC TRADE — simultaneous ATM call + ATM put at same strike and expiry

5. HOLD (long straddle):
   - Delta monitor: as underlying moves, |delta| grows; scalp when |delta| > gamma_scalp_band
   - Gamma scalp: TRADE underlying perp to delta-hedge; profit from realised move
   - Theta bleed: debit accrues daily; track cumulative_theta_cost vs gamma_scalp_income

6. HOLD (short straddle):
   - Delta monitor: rehedge when |delta| > delta_hedge_band_pct × vega_notional
   - Theta income: credit accrues daily; primary P&L source
   - Stop: vol spike detection → exit if IV rises > iv_stop_pct above entry IV

7. EXIT:
   - Long straddle: event passes + IV crush collapses straddle value → exit within hours post-event
   - Long straddle: P&L target reached (cumulative gamma income > theta_pnl_target_multiple × theta_paid)
   - Short straddle: theta_income_target_pct of initial premium collected
   - Stop loss (both): mark-to-market loss > stop_loss_pct × initial_premium (straddle notional)
   - Time: roll or close at roll_before_expiry_dte DTE
```

## Entry conditions + signal

- **Long straddle**: event within entry_days_before_event DTE;
  `analyst_expected_move > market_implied_move × event_move_premium_threshold`; or `IV_z_score < iv_zscore_long_entry`
  (vol depressed vs history)
- **Short straddle**: `IV_z_score_60d > iv_zscore_short_entry`; RV_5d < IV × rv_suppression_threshold; no binary event
  within tenor; underlying in range-bound regime check
- Both: ATM bid-ask per leg <= max_leg_spread_vp; sufficient liquidity at target strike

## Risk management

- Long straddle: max loss = full premium paid; loss is bounded, profit unlimited
- Short straddle: max loss theoretically unlimited (underlying gaps past stop before hedge executes); stop loss
  mandatory; iron condor variant with long wings caps loss
- Gamma scalp discipline: scalp thresholds must be wide enough to cover round-trip taker fees
- Post-event IV crush on long straddle: exit quickly post-event — IV collapse erodes straddle value rapidly even if the
  move was large
- Never hold short straddle through a binary event without explicit event-risk approval in config

## Config parameters

- `underlying`: BTC | ETH | SPX (etc.)
- `venue`: DERIBIT | OKX_OPTIONS | CBOE
- `direction`: long | short | auto (auto reads signal)
- `target_dte_entry`: days to expiry at entry (e.g. 7 for event, 14 for short)
- `roll_before_expiry_dte`: 2 (short straddle) or 1 (long straddle held to event)
- `max_vega_notional_usd`: vega exposure cap in USD
- `event_calendar_source`: internal_calendar | manual (for long-straddle catalyst mode)
- `entry_days_before_event`: enter long straddle this many days ahead of event (e.g. 3)
- `event_move_premium_threshold`: enter if expected_move > market_implied × this (e.g. 1.20)
- `iv_zscore_short_entry`: z-score threshold to enter short straddle (e.g. 1.5)
- `iv_zscore_long_entry`: z-score threshold to enter long straddle on IV depression (e.g. -1.5)
- `rv_suppression_threshold`: short straddle confirmation: RV < IV × this (e.g. 0.70)
- `gamma_scalp_band`: delta threshold for scalp trade (e.g. 0.05 = 5% of vega_notional)
- `delta_hedge_band_pct`: short straddle delta rehedge threshold
- `take_profit_theta_pct`: short straddle: exit when this fraction of premium collected (e.g. 0.50)
- `stop_loss_pct`: max loss as fraction of initial premium (both directions, e.g. 0.75)
- `iv_stop_pct`: short straddle vol-spike exit — exit if IV rises > X above entry (e.g. 0.15 absolute)

## When to use / market regime

- **Long straddle**: ahead of high-uncertainty binary events where the market is known to under-price tail moves; also
  when the vol surface is systematically compressed (IV historically low)
- **Short straddle**: post-event calm, earnings-like windows after a catalyst resolves with a small move; VIX/crypto IV
  at multi-month highs without a near-term catalyst to justify the premium
- **Avoid (long)**: expensive IV environments with no specific catalyst — theta bleed will dominate
- **Avoid (short)**: any period with known scheduled binary events within the tenor
- **Asset fit**: BTC, ETH (Deribit 0DTE + weekly expirations); SPX/SPY weeklies for TradFi event plays

## Example instances

```
VOL_STRADDLE@deribit-btc-straddle-7dte-usdt-prod
VOL_STRADDLE@deribit-eth-straddle-14dte-usdt-prod
VOL_STRADDLE@cboe-spx-straddle-weekly-usd-prod
```

## Not in this archetype

- Structural short-vol carry (systematically sell straddle every cycle to harvest theta, no event catalyst) →
  [`VOL_CARRY`](vol-carry.md)
- IV vs RV divergence with mean-reversion timing signal (not event-driven) → [`VOL_ARB_RV_IV`](vol-arb-rv-iv.md)
- 0DTE intraday gamma scalping on expiry-day ATM options → [`VOL_0DTE_GAMMA_SCALPING`](vol-0dte-gamma-scalping.md)
- Calendar or butterfly spread trading shape risk rather than vol level →
  [`VOL_SPREAD_STRUCTURES`](vol-spread-structures.md)
- ML-model-directed straddle sizing where signal is a forecast, not an event calendar → [`VOL_ML_LEAN`](vol-ml-lean.md)

## See also

- 0DTE gamma scalping: [vol-0dte-gamma-scalping.md](vol-0dte-gamma-scalping.md)
- RV vs IV arb: [vol-arb-rv-iv.md](vol-arb-rv-iv.md)
- Vol carry (short straddle structural): [vol-carry.md](vol-carry.md)
- Family: [vol-trading.md](../families/vol-trading.md)
