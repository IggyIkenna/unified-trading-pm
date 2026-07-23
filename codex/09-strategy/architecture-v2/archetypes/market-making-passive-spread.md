---
doc_type: codex-ssot
title: "Archetype: `MARKET_MAKING_PASSIVE_SPREAD`"
summary: >-
  `MARKET_MAKING_PASSIVE_SPREAD` archetype — the simplest MM: post symmetric limit bid/ask at mid ± `half_spread_ticks`
  and repost the opposite side on each fill to target near-zero inventory; pauses below `min_spread_ticks` or above
  `latency_threshold_ms`, with `inventory_hard_cap` market-order exit and a daily P&L stop.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [market-making, clob, spread, strategy, binance]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
  ]
created: 2026-05-19
authoritative_for: [MARKET_MAKING_PASSIVE_SPREAD archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: MARKET_MAKING_PASSIVE_SPREAD
family: MARKET_MAKING
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 20
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_PASSIVE_SPREAD`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Continuous — quotes posted and managed
> in real time; positions closed on each matched fill pair. **Code module (target):**
> `strategy-service/engine/strategies/v2/market_making/passive_spread_engine.py`

## What it does

The simplest market making archetype: post limit orders at both the bid and the ask simultaneously, earn the bid-ask
spread on matched fills, and repost immediately after each fill. Minimal inventory management — the strategy targets
near-zero inventory by reposting on the opposite side after each fill, flipping the book to realise the spread. Best
suited for high-liquidity, tight-spread instruments where adverse selection is low and fill rates are high enough to
sustain a positive expected value per round trip.

## Token / position flow

```
1. QUOTE GENERATION (per refresh interval):
   - mid_price = (best_bid + best_ask) / 2 from venue order book
   - post_bid = mid_price - half_spread_ticks × tick_size
   - post_ask = mid_price + half_spread_ticks × tick_size
   - Size: order_size_base per side (symmetric)

2. POST QUOTES: submit LIMIT bid + LIMIT ask simultaneously
   - Cancel any stale existing quotes before reposting
   - Respect venue rate limits (max_orders_per_second)

3. FILL HANDLING:
   - Bid filled: we bought; immediately post ask at post_ask = fill_price + spread_ticks
   - Ask filled: we sold; immediately post bid at post_bid = fill_price - spread_ticks
   - Partial fill: update remaining size; leave order; re-evaluate on next refresh

4. INVENTORY CHECK (per fill):
   - |net_inventory| > max_inventory_base: pause new same-side quotes until rebalanced
   - Rebalance: aggressive exit via market order if inventory > inventory_hard_cap

5. SPREAD CAPTURE:
   - net P&L per round trip ≈ spread_ticks × tick_size × order_size - fees
   - Break-even: fill_rate_pct × spread_capture > adverse_selection_cost + fees

6. STOP CONDITIONS:
   - Spread < min_spread_ticks: pause quoting (spread too tight for positive EV)
   - Venue latency > latency_threshold_ms: pause (stale quotes = adverse selection risk)
```

## Entry conditions + signal

- `current_spread_ticks >= min_spread_ticks` (market spread wide enough to profit after fees)
- `venue_latency_ms < latency_threshold_ms` (execution speed sufficient for safe reposting)
- `not in inventory_breach` (net inventory within configured bounds)
- No known high-impact event in the next event_blackout_minutes

## Risk management

- Inventory hard cap: max_inventory_base — market-order exit if breached (accepts taker fees to limit inventory risk)
- Spread floor: min_spread_ticks — do not quote inside the minimum spread (fees exceed capture)
- Latency kill switch: pause if venue round-trip latency > latency_threshold_ms (stale quotes invite toxic fills)
- Daily P&L stop: stop if realized_daily_pnl < -daily_stop_loss_usd
- Adverse selection monitor: if fill_then_adverse_move_pct > adverse_selection_threshold, widen quotes

## Config parameters

- `venue`: target exchange (e.g. `BINANCE`, `DERIBIT`, `HYPERLIQUID`)
- `instrument`: instrument ID (e.g. `BINANCE:SPOT:BTC-USDT`)
- `half_spread_ticks`: half-spread in ticks from mid (default 1)
- `order_size_base`: base order size per side in base currency units
- `min_spread_ticks`: minimum market spread required to quote (default 2)
- `max_inventory_base`: maximum net inventory before pausing same-direction quotes
- `inventory_hard_cap`: inventory above which a market-order exit is triggered
- `refresh_interval_ms`: quote refresh cadence in milliseconds (default 500)
- `latency_threshold_ms`: max tolerated venue round-trip latency (default 50)
- `event_blackout_minutes`: minutes before/after known events to suspend quoting (default 5)
- `daily_stop_loss_usd`: daily loss limit; stop quoting if breached (default 500)
- `adverse_selection_threshold`: fill-then-move rate above which quotes are widened (default 0.30)
- `share_class`: USDT | USD
- `execution_policy_ref`: mm-passive-v1

## When to use / market regime

- **Use when**: tight-spread, high-liquidity instrument; maker rebate available; low adverse selection; high fill rate
- **Best regime**: stable, low-volatility markets where mid-price is predictable between quote refreshes
- **Avoid**: high-volatility regimes (adverse selection eats spread); very wide-spread instruments (large inventory risk
  per fill); venues with no maker rebate and high taker fees
- **Best instruments**: major spot pairs (BTC/USDT, ETH/USDT) on Binance/OKX; high-liquidity perp funding markets

## Example instances

```
MARKET_MAKING_PASSIVE_SPREAD@binance-btc-usdt-spot-mm-prod
MARKET_MAKING_PASSIVE_SPREAD@okx-eth-usdt-spot-mm-prod
MARKET_MAKING_PASSIVE_SPREAD@hyperliquid-sol-usdt-perp-mm-prod
```

## Not in this archetype

- Inventory-skewed quoting with Avellaneda-Stoikov reservation price →
  [`MARKET_MAKING_INVENTORY_SKEW`](market-making-inventory-skew.md)
- ML-guided directional lean on top of spread capture → [`MARKET_MAKING_ML_LEAN`](market-making-ml-lean.md)
- Queue-position and VPIN-aware posting → [`MARKET_MAKING_QUEUE_MICROSTRUCTURE`](market-making-queue-microstructure.md)
- Sports/event-settled back-lay quoting → [`MARKET_MAKING_EVENT_SETTLED`](market-making-event-settled.md)
- DEX concentrated-liquidity LP fee capture → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md)

## See also

- Family: [market-making.md](../families/market-making.md)
- Inventory-skewed variant: [market-making-inventory-skew.md](market-making-inventory-skew.md)
- ML-guided quote tilt: [market-making-ml-lean.md](market-making-ml-lean.md)
