---
doc_type: codex-ssot
title: "Archetype: `VOL_DISPERSION`"
summary:
  "Archetype spec for `VOL_DISPERSION` — sells index vol and buys a weighted basket of component vols to harvest the
  implied-over-realised correlation premium (BTC index vs ETH/SOL/BNB); entry at dispersion_premium > ~3 vp;
  Deribit/OKX."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, dispersion, correlation, spread]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-variance-swap.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_DISPERSION archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-variance-swap.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_DISPERSION
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 200
  min_sla_tier: standard
---

# Archetype: `VOL_DISPERSION`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous — multiple simultaneous
> expiries across index and components, each rolled independently. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_dispersion_engine.py`

## What it does

Dispersion trading exploits the persistent premium that index implied volatility carries over the average implied
volatility of its constituents. This premium arises because index options buyers pay extra for the correlation
protection they provide — the index moves less than its components if they diverge, but index options still need to
price for the worst-case correlated drawdown. The strategy sells index volatility (short straddle on the index) and buys
volatility on a weighted basket of individual components, harvesting the correlation premium. Profit is earned when
realised correlation is lower than the implied correlation baked into index IV. In crypto, this is applied as BTC index
vol vs a weighted basket of ETH, SOL, and BNB component vol.

## Token / position flow

```
1. DISPERSION PREMIUM COMPUTATION:
   - implied_correlation = (index_IV² - weighted_avg_component_IV²) / cross_term
   - rolling 30d realised correlation: corr_RV_30d
   - dispersion_premium_vp = implied_correlation - corr_RV_30d (in vol-point equivalent)

2. SIGNAL CHECK:
   - Entry: dispersion_premium_vp > min_dispersion_premium_vp (premium elevated)
   - Signal stronger when: individual component IVs are low + index IV is elevated

3. POSITION CONSTRUCTION:
   - SHORT: index straddle (sell ATM call + put at target tenor)
   - LONG: weighted straddles on each component (weight = component weight in index)
   - Total component vega_notional matches index short_vega_notional × dispersion_ratio

4. ENTRY: simultaneous ATOMIC trades across index + component legs
   (leg failures abort full entry — no partial dispersion position)

5. HOLD + DAILY MONITOR:
   - Track realised correlation daily
   - Delta-hedge index leg via index future/perp
   - Delta-hedge each component leg via that component's perp
   - Roll any leg approaching roll_before_expiry_dte

6. EXIT:
   - dispersion_premium_vp < exit_premium_threshold (premium compressed)
   - Stop loss: vega P&L < -stop_loss_vega_pct × initial_premium
   - Correlation spike: realised correlation > correlation_stop_threshold
```

## Entry conditions + signal

- `dispersion_premium_vp > min_dispersion_premium_vp` (default 3.0 vol points)
- All component options liquid (OI > min_component_oi per strike)
- No high-vol regime on index underlying
- Correlation environment: realised 30d corr < implied corr (premium exists)

## Risk management

- Max single-component vega as fraction of total: max_single_component_vega_pct (default 40%)
- Correlation stop: exit all legs if realised 5d correlation spikes above correlation_stop_threshold
- Delta-hedge index and components independently — do not net delta across legs
- Leg failure on entry: abort and close any filled legs before next attempt
- Venue concentration: cap index and components on same venue to venue_concentration_cap_pct

## Config parameters

- `index_underlying`: e.g. `BTC` (for crypto BTC-tracking index) or `SPX`
- `components`: list of component symbols with weights, e.g. `[{ETH: 0.5}, {SOL: 0.3}, {BNB: 0.2}]`
- `target_tenor_dte`: target DTE for all legs at entry (default 14)
- `min_dispersion_premium_vp`: minimum implied-vs-realised correlation gap in vol points (default 3.0)
- `exit_premium_threshold`: exit when premium compresses below this (default 1.0)
- `dispersion_ratio`: component total vega as fraction of index vega (default 1.0)
- `max_single_component_vega_pct`: per-component vega concentration cap (default 40%)
- `correlation_lookback_days`: window for realised correlation (default 30)
- `correlation_stop_threshold`: 5d realised corr above which to exit (default 0.90)
- `stop_loss_vega_pct`: exit if vega loss > this fraction of initial premium (default 0.75)
- `roll_before_expiry_dte`: roll legs at this DTE (default 3)
- `share_class`: USDT | USD
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: index IV significantly elevated vs component IV average; market-wide fear buying pushing index options
  up
- **Best regime**: risk-off environments where index hedgers pile in; macro events that push index vol up without
  proportionally lifting component vols
- **Avoid**: highly correlated crash environments (all correlations go to 1); illiquid component option markets; very
  short tenor where simultaneous fills across many legs become impractical
- **Crypto note**: BTC serves as both index and dominant component — weight ETH/SOL/BNB carefully; BTC OI dominates
  Deribit; use OKX for ETH component; other components may have limited Deribit liquidity

## Example instances

```
VOL_DISPERSION@deribit-btc-index-dispersion-14dte-usdt-prod
VOL_DISPERSION@deribit-eth-components-dispersion-30dte-usdt-prod
VOL_DISPERSION@cboe-spx-dispersion-monthly-usd-prod
```

## Not in this archetype

- Single-underlying variance swap replication via 1/K² option strip → [`VOL_VARIANCE_SWAP`](vol-variance-swap.md)
- Outright index short-vol without component legs → [`VOL_CARRY`](vol-carry.md)
- Cross-asset vol spread between two correlated single underlyings →
  [`VOL_CROSS_ASSET_SPREAD`](vol-cross-asset-spread.md)
- Hard cross-venue single-option mispricing vs theoretical model price →
  [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Short-vol carry (simpler outright): [vol-carry.md](vol-carry.md)
- Variance swap positioning: [vol-variance-swap.md](vol-variance-swap.md)
