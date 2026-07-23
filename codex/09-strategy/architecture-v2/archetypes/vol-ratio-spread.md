---
doc_type: codex-ssot
title: "Archetype: `VOL_RATIO_SPREAD`"
summary:
  "Archetype spec for `VOL_RATIO_SPREAD` — sells excess OTM options against a long strike (e.g. 1x2 call ratio) for net
  credit to harvest rich OTM skew; breach-proximity trigger + hard USD stop cap the naked-wing tail; Deribit/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, ratio-spread, skew, credit]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-variance-swap.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_RATIO_SPREAD archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-variance-swap.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_RATIO_SPREAD
family: VOL_TRADING
venue_universe: [DERIBIT, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_RATIO_SPREAD`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven — held to expiry or closed
> before to avoid short-gamma zone near expiry. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_ratio_spread_engine.py`

## What it does

A ratio spread positions one long option at a lower strike and multiple short options at a higher strike (or vice versa
for puts) in a ratio greater than 1:1 (e.g. 1 long ATM call, 2 short OTM calls — a 1x2 call ratio). The net position
collects a credit at entry (the excess premium from selling more options than bought). The position is profitable if the
underlying stays below the short strikes at expiry; above the short strikes, the naked short options create uncapped
(call ratio) or wide-range loss. The strategy harvests premium from selling excess OTM options, betting that realised
vol will be insufficient to push the underlying through the short strike zone.

## Token / position flow

```
1. SIGNAL: identify ratio spread opportunity
   - Extract vol smile at target expiry
   - Compute richness of OTM options vs ATM: skew_premium = OTM_IV - ATM_IV
   - Entry when: skew_premium > min_skew_premium_vp (OTM options rich vs model)
   - Net credit check: ensure ratio_spread_net_credit > min_net_credit_pct × ATM_premium

2. LEG CONSTRUCTION:
   - LONG leg: 1 unit at strike_L (ATM or slightly OTM)
   - SHORT leg: ratio_n units at strike_S (further OTM, same expiry)
   - Net credit: premium_short × ratio_n - premium_long > 0 (required for entry)
   - Example (1x2 call ratio): buy 1 ATM call + sell 2 OTM calls at delta ~0.20

3. POSITION SIZING:
   - Size by max_loss_per_position_usd (loss occurs above strike_S for calls)
   - max_contracts_long = max_loss_per_position_usd / max_loss_per_contract

4. ENTRY: ATOMIC multi-leg TRADE (long + short legs simultaneously)
   - Never enter with only long leg filled (creates naked long — not this archetype)
   - Never enter with only short legs filled (creates naked short — catastrophic)

5. HOLD:
   - Delta-hedge net position if |net_delta| > delta_hedge_band_pct × notional
   - Monitor underlying price vs short strike distance daily
   - Exit if underlying approaches within breach_proximity_pct of short strike

6. EXIT:
   - PROFIT EXIT: close when position value > take_profit_pct × initial_credit
   - BREACH EXIT: underlying within breach_proximity_pct of short strike → close all legs
   - TIME EXIT: roll or close at roll_before_expiry_dte to avoid binary expiry gamma
   - STOP LOSS: position value loss > stop_loss_usd_per_position
```

## Entry conditions + signal

- `skew_premium_vp > min_skew_premium_vp` (OTM IV premium over ATM, default 3.0 vol points)
- Net credit at entry > min_net_credit_pct × ATM_premium (default 20%)
- Underlying not near the short strike at entry (spot must be below/above by > safe_zone_pct)
- No high-vol regime (if IV > regime_iv_threshold, OTM options may be rich for good reason)

## Risk management

- Call ratio: unlimited loss above short strike if not closed — breach_proximity_pct trigger is critical
- Put ratio: large loss below short strike — symmetric risk management applies
- Never allow ATOMIC entry to partially fill — abort on any leg failure
- Breach proximity trigger: close all legs if spot within breach_proximity_pct of short strike (default 2%)
- Stop loss: hard USD stop per position at max_loss_per_position_usd (caps the theoretical unlimited loss)
- Do not hold through expiry if near short strike — roll at roll_before_expiry_dte

## Config parameters

- `underlying`: `BTC` | `ETH` | `SPX` | etc.
- `option_type`: `call` | `put` — direction of ratio spread
- `target_tenor_dte`: target DTE at entry (default 14-21)
- `ratio_n`: number of short contracts per long contract (default 2, i.e. 1x2)
- `strike_l_moneyness`: moneyness of long leg (default 1.00 = ATM)
- `strike_s_delta`: delta of short leg options (default 0.20 = 20d OTM)
- `min_skew_premium_vp`: minimum skew richness required for entry (default 3.0 vol points)
- `min_net_credit_pct`: minimum net credit as fraction of ATM premium (default 0.20)
- `take_profit_pct`: close when credit captured > this fraction of initial credit (default 0.50)
- `breach_proximity_pct`: close if spot within this percentage of short strike (default 2.0%)
- `delta_hedge_band_pct`: rehedge threshold (default 0.05 of notional)
- `roll_before_expiry_dte`: close/roll at this DTE (default 5)
- `max_loss_per_position_usd`: hard USD stop loss per position (default 5000)
- `safe_zone_pct`: minimum distance spot must be from short strike at entry (default 5.0%)
- `share_class`: USDT | USD
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: OTM option skew is rich (OTM vol significantly above ATM vol); underlying in a slow-trending or
  rangebound regime with low probability of large directional move; premium collection desired without full short
  straddle exposure
- **Call ratio (1x2 calls)**: mildly bullish or neutral; expecting underlying to rally modestly but not explosively
- **Put ratio (1x2 puts)**: mildly bearish or neutral; expecting modest downside without crash scenario
- **Avoid**: high-vol regimes; when underlying is near the short strike at entry; when skew premium is justified by
  upcoming known event (earnings, FOMC, protocol upgrade)
- **Best instruments**: BTC/ETH on Deribit; SPX weeklies on CBOE via IBKR (SPX has very rich put skew)

## Example instances

```
VOL_RATIO_SPREAD@deribit-btc-call-1x2-14dte-usdt-prod
VOL_RATIO_SPREAD@deribit-eth-put-1x2-21dte-usdt-prod
VOL_RATIO_SPREAD@cboe-spx-put-1x2-weekly-usd-prod
```

## Not in this archetype

- Symmetric short straddle / strangle at a single strike pair (no naked short wing) → [`VOL_CARRY`](vol-carry.md)
- Full 1/K² strike strip replicating variance swap payoff → [`VOL_VARIANCE_SWAP`](vol-variance-swap.md)
- Cross-asset vol spread (two correlated underlyings, same tenor) →
  [`VOL_CROSS_ASSET_SPREAD`](vol-cross-asset-spread.md)
- OTM skew richness exploited via hard mispricing arbitrage →
  [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Vol carry (simpler short straddle/strangle): [vol-carry.md](vol-carry.md)
- Cross-asset vol spread: [vol-cross-asset-spread.md](vol-cross-asset-spread.md)
