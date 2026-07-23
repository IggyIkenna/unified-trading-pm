---
doc_type: codex-ssot
title: "Archetype: `VOL_MARKET_MAKING`"
summary:
  "Archetype spec for `VOL_MARKET_MAKING` — posts two-sided vol quotes around an SVI/SSVI fair-value surface with
  inventory skew, earning the bid-ask spread and delta-hedging accumulated option inventory; Deribit/OKX, 50ms premium
  SLA."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, market-making, delta-hedge, book-microstructure]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_MARKET_MAKING archetype spec"]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/tradfi/market-making-options.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_MARKET_MAKING
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 50
  min_sla_tier: premium
---

# Archetype: `VOL_MARKET_MAKING`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous quote lifecycle — orders rest
> on the options order book; fills accumulate as inventory; inventory delta-hedged continuously. **Code module
> (target):** `strategy-service/engine/strategies/v2/vol_trading/vol_market_making_engine.py`

## What it does

Posts two-sided vol quotes (bid and ask) on the options order book at target spread widths, earning the bid-ask spread
as primary P&L. The engine maintains a real-time theoretical fair-value surface (using SVI or SSVI), computes bid and
ask IV quotes at a target half-spread around fair-value, and continuously manages the resulting inventory of options
fills. Delta exposure from accumulating inventory is hedged via the underlying perp or future. Greek risk accumulates
across the book: vega and gamma concentrations at active strikes require active monitoring and selective quote
withdrawal when inventory limits are breached. Primary venues are Deribit (BTC/ETH options — deepest liquidity, REST +
WebSocket) and OKX options.

## Token / position flow

```
1. SURFACE CONSTRUCTION:
   - Fit live SVI/SSVI surface to current options chain (bid/ask mid-points)
   - Update surface every surface_update_interval_sec

2. QUOTING LOOP (per strike × expiry in active_strikes):
   - Compute fair_iv = surface.get_iv(strike, expiry)
   - Compute bid_iv = fair_iv − half_spread_vp, ask_iv = fair_iv + half_spread_vp
   - Convert IV quotes to option price quotes (Black-Scholes + vol adjustments)
   - Apply inventory skew: if long vega inventory > skew_threshold, widen ask / tighten bid
     (lean the book to reduce inventory in the direction of exposure)
   - Place/refresh LIMIT orders for bid and ask; cancel stale orders older than quote_ttl_ms

3. FILL PROCESSING:
   - On fill: update option inventory ledger (qty × delta × vega per leg)
   - Recompute portfolio Greeks: delta_total, vega_total, gamma_total

4. DELTA HEDGE:
   - When |delta_total| > delta_hedge_band: emit hedge TRADE on underlying perp
   - Hedge via DERIBIT perpetual or futures (same venue preferred to minimise lag)

5. GREEK RISK MONITORING:
   - Vega limit: |vega_total_usd| > max_vega_usd → pause quoting on breached strikes
   - Gamma limit: |gamma_total_usd| > max_gamma_usd → widen spreads on nearest strikes
   - Charm (delta decay): near-expiry options require more frequent delta hedge rebalancing

6. EXIT / POSITION UNWIND:
   - Venue outage: cancel all orders; initiate inventory unwind via taker if exposure > unwind_threshold
   - EOD / session close: cancel resting orders; leave inventory or initiate taker-close per config
   - Inventory limit breach: cancel quotes on breached strikes; unwind excess via taker
```

## Entry conditions + signal

- Session start: venue is reachable, surface fitting converges, bid-ask on options market < max_raw_spread_vp
- Quote only strikes within [min_moneyness, max_moneyness] range around ATM
- Suppress quoting if underlying moves > underlying_move_pause_pct in past quote_pause_lookback_sec (fast-market pause —
  avoid adverse selection during price discovery)
- Minimum fill rate check: if historical fill rate on a strike < min_fill_rate, remove from active_strikes

## Risk management

- Delta hedge continuously: |portfolio_delta| > delta_hedge_band triggers perp hedge within hedge_ttl_ms
- Vega cap: total short/long vega exposure bounded by max_vega_usd; quotes withdrawn on breach
- Gamma cap: large gamma at short-dated strikes; withdraw quotes from DTE < min_dte_quote to avoid expiry-day gamma risk
- Adverse selection guard: cancel quotes on a strike after fill_cancel_count rapid same-direction fills (signal that an
  informed trader is picking off stale quotes)
- Circuit breaker: if cumulative session P&L < session_pnl_floor_usd, cancel all quotes and halt

## Config parameters

- `underlying`: BTC | ETH
- `venue`: DERIBIT | OKX_OPTIONS
- `active_strike_count`: number of strikes quoted per expiry (e.g. 10)
- `active_expiries`: list of expiry DTEs to quote (e.g. [7, 14, 30])
- `min_dte_quote`: suppress quoting below this DTE (e.g. 2)
- `half_spread_vp`: target half-spread in vol points (e.g. 0.5 = 1.0 vol pt full spread)
- `surface_model_ref`: SVI or SSVI surface reference key
- `surface_update_interval_sec`: how often to refit surface (e.g. 5)
- `quote_ttl_ms`: cancel and re-quote after this age (e.g. 2000)
- `delta_hedge_band`: hedge perp when |portfolio_delta| exceeds this (e.g. 0.05 delta units)
- `hedge_ttl_ms`: max delay from delta trigger to hedge TRADE execution (e.g. 500)
- `max_vega_usd`: max aggregate vega exposure in USD before pausing new quotes (e.g. 100_000)
- `max_gamma_usd`: max aggregate gamma exposure in USD (e.g. 10_000)
- `skew_threshold_vega_usd`: inventory skew activation level for quote lean (e.g. 20_000)
- `underlying_move_pause_pct`: fast-market pause threshold (e.g. 0.02 = 2% move in pause window)
- `quote_pause_lookback_sec`: lookback for fast-market detection (e.g. 60)
- `session_pnl_floor_usd`: session circuit-breaker P&L floor (e.g. -5000)
- `fill_cancel_count`: adverse selection threshold per strike (e.g. 3 rapid fills → cancel)

## When to use / market regime

- **Best regime**: moderate IV with stable underlying and decent options volume; spreads are wide enough to earn
  meaningful edge but liquidity is sufficient to rebalance delta hedges without excessive slippage
- **Avoid**: extreme fast markets (large crypto moves > 5% / hour) — adverse selection and delta hedging slippage erode
  P&L rapidly; also avoid during major options expirations where the term structure distorts
- **Latency requirement**: premium SLA tier — quote refresh and delta hedge must execute within 50ms; deploy on
  co-located or low-latency cloud nodes near Deribit matching engine
- **Asset fit**: BTC and ETH on Deribit (deepest crypto options book); OKX as secondary venue

## Example instances

```
VOL_MARKET_MAKING@deribit-btc-options-7-30dte-usdt-prod
VOL_MARKET_MAKING@deribit-eth-options-7-30dte-usdt-prod
VOL_MARKET_MAKING@okx-options-btc-options-14dte-usdt-prod
```

## Not in this archetype

- Passive short-vol carry (sell straddle/strangle and hold to expiry; no two-sided quoting) →
  [`VOL_CARRY`](vol-carry.md)
- Spot or perp order-book quoting (no vol surface, no options Greeks management) →
  [`MARKET_MAKING_CONTINUOUS`](market-making-continuous.md)
- 0DTE intraday gamma scalping (directional delta rehedge on expiry day, not resting limit orders) →
  [`VOL_0DTE_GAMMA_SCALPING`](vol-0dte-gamma-scalping.md)
- Vol view trade (directional position sized by IV/RV divergence, not inventory spread capture) →
  [`VOL_ARB_RV_IV`](vol-arb-rv-iv.md)

## See also

- Vol carry (passive short vol): [vol-carry.md](vol-carry.md)
- 0DTE gamma scalping: [vol-0dte-gamma-scalping.md](vol-0dte-gamma-scalping.md)
- Market making (spot/perp): [market-making-continuous.md](market-making-continuous.md)
- Family: [vol-trading.md](../families/vol-trading.md)
