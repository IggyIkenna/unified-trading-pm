---
doc_type: codex-ssot
title: "Archetype: `MARKET_MAKING_INVENTORY_SKEW`"
summary: >-
  `MARKET_MAKING_INVENTORY_SKEW` archetype — Avellaneda-Stoikov quoting that offsets from mid by an inventory-risk
  penalty (reservation_price = mid − net_inventory × gamma × sigma² × T), widening the over-filled side to self-correct;
  `gamma`-calibrated, with `inventory_hard_cap` market-order exit and end-of-day flush.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [market-making, avellaneda-stoikov, inventory-skew, clob, strategy]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
  ]
created: 2026-05-19
authoritative_for: [MARKET_MAKING_INVENTORY_SKEW archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: MARKET_MAKING_INVENTORY_SKEW
family: MARKET_MAKING
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 30
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_INVENTORY_SKEW`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Continuous — quotes adjusted
> dynamically in real time based on current inventory state. **Code module (target):**
> `strategy-service/engine/strategies/v2/market_making/inventory_skew_engine.py`

## What it does

Inventory-skewed market making extends the passive spread archetype by adjusting bid and ask quotes asymmetrically based
on current net inventory. When the strategy is long (over-filled on the buy side), it widens the bid and tightens the
ask — making it harder to accumulate more inventory and easier for sellers to offload against us. When short, the
opposite applies. This approach implements the core insight of the Avellaneda-Stoikov framework: the optimal quote is
not centred on mid but offset by an inventory-risk penalty term. The result is a self-correcting mechanism that reduces
inventory blowout risk without resorting to aggressive market-order exits.

## Token / position flow

```
1. INVENTORY STATE (computed per fill and per refresh):
   - net_inventory_base: current position in base currency (positive = long)
   - inventory_ratio = net_inventory_base / max_inventory_base  ∈ [-1, 1]

2. AVELLANEDA-STOIKOV RESERVATION PRICE:
   - reservation_price = mid - (net_inventory × gamma × sigma² × T_remaining)
   - gamma: inventory-risk aversion parameter
   - sigma: short-term realised vol estimate
   - T_remaining: time to next quote refresh (or to end-of-day reset)

3. SKEWED QUOTE GENERATION:
   - base_half_spread = half_spread_ticks × tick_size
   - inventory_adjustment = skew_factor × inventory_ratio × base_half_spread
   - post_bid = reservation_price - base_half_spread - inventory_adjustment
   - post_ask = reservation_price + base_half_spread + inventory_adjustment
   (When long: bid shifts down, ask shifts down → easier to sell, harder to buy more)

4. POST + MANAGE: identical to MARKET_MAKING_PASSIVE_SPREAD quote lifecycle

5. FILL HANDLING:
   - Recompute inventory_ratio after every fill
   - Apply new skew immediately on next quote refresh
   - No aggressive exit unless inventory_hard_cap breached

6. DAILY RESET: at session end, aggressively exit remaining inventory via market orders
   if abs(net_inventory) > end_of_day_inventory_tolerance
```

## Entry conditions + signal

- Same liquidity and spread conditions as MARKET_MAKING_PASSIVE_SPREAD
- `vol_estimate_sigma available` (from realised vol or EWMA of recent ticks)
- `abs(inventory_ratio) < 1.0` (not at hard cap before start of session)

## Risk management

- Inventory hard cap: market-order exit when `|net_inventory| > inventory_hard_cap` (bypasses skew; accepts taker fees)
- Gamma calibration: if skew_factor too low, skew insufficient to self-correct; if too high, quotes become too one-sided
  and fill rates drop — calibrate via backtest per instrument
- End-of-day inventory flush: mandatory aggressive exit of residual position
- Vol spike: widen both bid and ask (increase base_half_spread) when sigma spikes; do not skew further while vol high
- Daily P&L stop: same as passive spread (daily_stop_loss_usd)

## Config parameters

- `venue`: target exchange
- `instrument`: instrument ID
- `half_spread_ticks`: base half-spread before inventory adjustment (default 1)
- `skew_factor`: amplification of inventory-driven quote adjustment (default 0.5)
- `gamma`: Avellaneda-Stoikov risk-aversion parameter (default 0.1; tune per instrument)
- `sigma_lookback_seconds`: lookback for short-term realised vol estimate (default 300)
- `order_size_base`: base order size per side
- `max_inventory_base`: inventory target; beyond this skew maximises
- `inventory_hard_cap`: inventory above which market-order exit is forced
- `end_of_day_inventory_tolerance`: residual inventory (abs) tolerated at session close
- `refresh_interval_ms`: quote refresh cadence (default 200)
- `latency_threshold_ms`: max venue round-trip latency before pause (default 50)
- `daily_stop_loss_usd`: daily loss limit (default 500)
- `share_class`: USDT | USD
- `execution_policy_ref`: mm-inventory-v1

## When to use / market regime

- **Use when**: passive spread works but inventory management is the binding constraint; frequent one-sided flow creates
  inventory blowout risk; instrument has enough depth that skewed quotes still attract fills
- **Best regime**: trending markets where passive spread accumulates directional inventory; the skew auto-corrects
  without manual intervention
- **Avoid**: very low-liquidity instruments where skewed quotes lead to zero fills on the skewed side; regime with
  highly persistent directional trends exceeding the inventory correction capacity
- **Replaces**: pure passive spread when inventory blowout is the observed P&L driver

## Example instances

```
MARKET_MAKING_INVENTORY_SKEW@binance-btc-usdt-spot-mm-prod
MARKET_MAKING_INVENTORY_SKEW@okx-eth-usdt-perp-mm-prod
MARKET_MAKING_INVENTORY_SKEW@hyperliquid-sol-usdt-perp-mm-prod
```

## Not in this archetype

- Symmetric spread with no skew logic → [`MARKET_MAKING_PASSIVE_SPREAD`](market-making-passive-spread.md)
- ML-directed short-horizon lean on top of inventory skew → [`MARKET_MAKING_ML_LEAN`](market-making-ml-lean.md)
- Queue-position and VPIN-aware posting decision →
  [`MARKET_MAKING_QUEUE_MICROSTRUCTURE`](market-making-queue-microstructure.md)
- Sports/event-settled back-lay quoting → [`MARKET_MAKING_EVENT_SETTLED`](market-making-event-settled.md)
- DEX concentrated-liquidity LP fee capture → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md)

## See also

- Family: [market-making.md](../families/market-making.md)
- Simpler passive variant: [market-making-passive-spread.md](market-making-passive-spread.md)
- ML-augmented quote tilt: [market-making-ml-lean.md](market-making-ml-lean.md)
- Queue microstructure: [market-making-queue-microstructure.md](market-making-queue-microstructure.md)
