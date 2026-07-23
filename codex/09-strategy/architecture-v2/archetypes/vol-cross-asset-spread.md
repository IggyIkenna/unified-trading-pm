---
doc_type: codex-ssot
title: "Archetype: `VOL_CROSS_ASSET_SPREAD`"
summary:
  "Archetype spec for `VOL_CROSS_ASSET_SPREAD` — trades the vega-matched IV spread between correlated assets (e.g.
  BTC/ETH 30d) at matched expiry, entering at |spread_z| > 2 and exiting on reversion to the rolling mean; Deribit/OKX."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, cross-asset, spread, mean-reversion]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ratio-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_CROSS_ASSET_SPREAD archetype spec"]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/tradfi/relative-volatility.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ratio-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-slope.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_CROSS_ASSET_SPREAD
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_CROSS_ASSET_SPREAD`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous with matched expiries —
> positions in correlated asset pairs rolled simultaneously to maintain spread exposure. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_cross_asset_spread_engine.py`

## What it does

Trades the spread between implied volatilities of correlated assets at matched tenors. The primary crypto example is the
BTC/ETH vol spread: historically, 30-day BTC IV exceeds ETH IV by 5-15 vol points, with occasional inversions (ETH IV >
BTC IV) during ETH-specific events (upgrades, ETF decisions). When the spread exceeds its 2-sigma band relative to its
rolling mean, the strategy simultaneously buys vol on the relatively cheap asset and sells vol on the relatively
expensive asset at the same expiry. Profit is earned when the cross-asset vol spread reverts to its historical norm.

## Token / position flow

```
1. VOL SPREAD COMPUTATION (daily, per asset pair):
   - Extract ATM IV at target_tenor_dte for asset_A and asset_B
   - vol_spread = asset_A_IV - asset_B_IV  (positive = A more expensive)
   - rolling_mean = 30d mean of vol_spread
   - rolling_std = 30d std of vol_spread
   - spread_z = (vol_spread - rolling_mean) / rolling_std

2. SIGNAL CHECK:
   - LONG SPREAD (buy B vol / sell A vol): spread_z > +entry_z_threshold
     (A unusually expensive vs B → expect compression)
   - SHORT SPREAD (buy A vol / sell B vol): spread_z < -entry_z_threshold
     (B unusually expensive vs A → expect compression)

3. POSITION CONSTRUCTION:
   - Cheap asset: long straddle at target_tenor_dte (matched same expiry date)
   - Expensive asset: short straddle at same target_tenor_dte
   - Vega matched: size each leg to equal vega_notional_usd

4. ENTRY: ATOMIC fills on both asset legs
   (abort both legs if either fill fails — spread position requires both sides)

5. HOLD + MONITOR (daily):
   - Recompute spread_z; track mean reversion
   - Delta-hedge each asset leg independently via its perp/future
   - Roll both legs simultaneously at roll_before_expiry_dte (matched expiry)

6. EXIT:
   - spread_z crosses exit_z_threshold (spread compressed to mean)
   - Stop loss: vega P&L < -stop_loss_vega_pct × initial_premium
   - Correlation breakdown: if asset_A / asset_B 30d realised correlation < min_correlation,
     exit (spread no longer driven by correlated vol dynamics)
```

## Entry conditions + signal

- `|spread_z| > entry_z_threshold` (default 2.0)
- Correlated asset pair (30d realised correlation > min_correlation_for_entry, default 0.65)
- Liquid options at matched expiry date on both assets
- No single-asset fundamental event in the next dte_days (upgrade, ETF decision, etc.)

## Risk management

- Vega balance: both legs must be vega-matched within vega_balance_tolerance_pct (default 5%)
- Correlation stop: exit if realised 5d correlation drops below min_exit_correlation (default 0.50)
- Stop loss: total vega P&L < -stop_loss_vega_pct × initial_premium (default 75%)
- Roll both legs simultaneously — do not roll one leg without the other (creates unhedged vol exposure)
- Single-asset event risk: cancel/pause if known catalyst event for one asset in the next 48h

## Config parameters

- `asset_a`: primary asset symbol (e.g. `BTC`)
- `asset_b`: secondary asset symbol (e.g. `ETH`)
- `target_tenor_dte`: matched tenor DTE at entry (default 30)
- `spread_lookback_days`: rolling window for spread mean/std (default 30)
- `entry_z_threshold`: z-score required to enter (default 2.0)
- `exit_z_threshold`: z-score at which to exit (default 0.5)
- `vega_notional_usd`: per-leg vega target (default 25000)
- `vega_balance_tolerance_pct`: max vega mismatch at entry (default 5%)
- `min_correlation_for_entry`: minimum 30d realised correlation to enter (default 0.65)
- `min_exit_correlation`: exit if 5d realised correlation drops below this (default 0.50)
- `stop_loss_vega_pct`: exit if vega loss > this fraction of initial premium (default 0.75)
- `roll_before_expiry_dte`: roll both legs at this DTE (default 3)
- `share_class`: USDT
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: vol spread between correlated assets at multi-week extreme; both asset option chains liquid at same
  tenor; no known idiosyncratic event for the expensive-vol asset in the near term
- **Best regime**: BTC/ETH spread inversion during ETH upgrade hype (ETH IV spikes relative to BTC → sell ETH vol, buy
  BTC vol, profit when inversion corrects); or BTC IV spike during regulatory event while ETH relatively calm
- **Avoid**: correlation breakdown between assets (spread becomes a pure directional vol bet, not a spread trade); near
  an ETH hard fork or BTC halving where the fundamental vol dynamics shift; when matched expiry liquidity thin on one
  side
- **Crypto pairs**: BTC/ETH (primary); BTC/SOL (secondary — lower correlation, wider expected spread); ETH/SOL

## Example instances

```
VOL_CROSS_ASSET_SPREAD@deribit-btc-eth-spread-30dte-usdt-prod
VOL_CROSS_ASSET_SPREAD@deribit-btc-sol-spread-30dte-usdt-prod
VOL_CROSS_ASSET_SPREAD@okx-options-eth-sol-spread-30dte-usdt-prod
```

## Not in this archetype

- Index vs basket of components (correlation premium harvest) → [`VOL_DISPERSION`](vol-dispersion.md)
- Single-asset multi-strike skew harvest via ratio spread → [`VOL_RATIO_SPREAD`](vol-ratio-spread.md)
- Cross-tenor calendar spread on the same single underlying → [`VOL_TERM_STRUCTURE_ARB`](vol-term-structure-arb.md)
- Single-asset outright short-vol → [`VOL_CARRY`](vol-carry.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Single-asset vol carry: [vol-carry.md](vol-carry.md)
- Vol ratio spread (single-asset, multi-strike): [vol-ratio-spread.md](vol-ratio-spread.md)
