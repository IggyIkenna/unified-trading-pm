---
doc_type: codex-ssot
title: "Archetype: `MARKET_MAKING_QUEUE_MICROSTRUCTURE`"
summary: >-
  `MARKET_MAKING_QUEUE_MICROSTRUCTURE` archetype — queue-aware MM modelling VPIN order-flow toxicity and FIFO queue
  position; posts only when fill-probability-adjusted EV > `min_ev_threshold`, cancels all quotes on VPIN >
  `vpin_kill_threshold` (0.85), reprices on queue-rank decay; ultra-premium / co-located (10ms latency budget).
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [market-making, vpin, queue-position, book-microstructure, clob]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
  ]
created: 2026-05-19
authoritative_for: [MARKET_MAKING_QUEUE_MICROSTRUCTURE archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: MARKET_MAKING_QUEUE_MICROSTRUCTURE
family: MARKET_MAKING
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 10
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_QUEUE_MICROSTRUCTURE`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Continuous — queue position modelled
> explicitly; only posts when expected fill probability × spread capture > adverse selection cost. **Code module
> (target):** `strategy-service/engine/strategies/v2/market_making/queue_microstructure_engine.py`

## What it does

Queue-aware market making extends the ML-lean and inventory-skew approaches by modelling microstructure phenomena
explicitly: order flow toxicity (trade imbalance and arrival rate patterns), queue position priority (time-priority in
FIFO price-time order books), and expected fill probability given current queue depth. The strategy only posts a quote
when the queue-position-adjusted expected value is positive — accounting for the fact that a limit order deep in the
queue has low fill probability and may get adversely selected more often than one at the front. Tracks own queue rank at
each price level and reprices aggressively when queue position deteriorates.

## Token / position flow

```
1. ORDER FLOW TOXICITY ASSESSMENT (per refresh):
   - Compute VPIN (Volume-Synchronized Probability of Informed Trading):
     VPIN = |buy_vol - sell_vol| / total_vol over rolling vol_bucket_size
   - trade_arrival_rate = trades_per_second (rolling 60s)
   - Toxicity regime: HIGH if VPIN > vpin_threshold; LOW otherwise

2. QUEUE POSITION MODEL:
   - own_queue_rank = orders ahead of ours at bid/ask price (estimated from L2 changes)
   - estimated_fill_prob = exp(-lambda × own_queue_rank / total_queue_depth)
   - lambda: queue decay parameter (calibrated per instrument)

3. EXPECTED VALUE COMPUTATION (per side):
   - ev_bid = estimated_fill_prob × (spread_capture - adverse_selection_cost)
   - adverse_selection_cost = VPIN × mid_move_per_fill × order_size
   - Post bid only if ev_bid > min_ev_threshold

4. QUOTE DECISION:
   - ev > min_ev_threshold: post/maintain quote
   - ev <= min_ev_threshold: cancel quote; wait for queue to clear
   - Queue rank deteriorates (new orders jump ahead): reprice to restore queue position
     subject to max_reprice_cost (taker spread to cancel + repost)

5. FILL HANDLING + INVENTORY: same as MARKET_MAKING_INVENTORY_SKEW

6. QUEUE RANK MONITORING:
   - Track L2 order book changes to estimate own rank movement
   - If queue_rank > max_acceptable_queue_rank: cancel + reprice or skip
```

## Entry conditions + signal

- `VPIN < vpin_threshold` (LOW toxicity regime; high toxicity → pause quoting)
- `estimated_fill_prob > min_fill_prob_threshold` (queue position delivers sufficient fill rate)
- `ev_bid or ev_ask > min_ev_threshold` (positive expected value for at least one side)
- Venue provides sufficient L2 order book depth data for queue estimation

## Risk management

- VPIN kill switch: if VPIN spikes above vpin_kill_threshold, cancel ALL quotes immediately (informed trading event)
- Queue deterioration: cancel and reprice within max_reprice_cost tolerance; do not blindly chase queue position
- Adverse selection monitor: if post-fill adverse price moves > adverse_selection_threshold consistently, pause and
  recalibrate VPIN model
- Inventory hard cap and daily stop loss: same as inventory-skew archetype
- Latency kill switch: if own_order_latency > latency_kill_threshold_ms, pause (queue estimation becomes unreliable)

## Config parameters

- `venue`: target exchange (must support L2 order book with sufficient depth)
- `instrument`: instrument ID
- `vpin_threshold`: VPIN level triggering HIGH toxicity regime; pause new quotes (default 0.70)
- `vpin_kill_threshold`: VPIN above which all quotes cancelled immediately (default 0.85)
- `vol_bucket_size`: trade volume per VPIN computation bucket (instrument-specific)
- `queue_decay_lambda`: queue fill probability decay parameter (calibrated per instrument)
- `max_acceptable_queue_rank`: maximum own queue rank before cancelling + repricing (default 10)
- `min_fill_prob_threshold`: minimum estimated fill probability to post (default 0.15)
- `min_ev_threshold`: minimum expected value per fill to justify posting (default 0.02 in quote units)
- `max_reprice_cost`: maximum spread cost tolerated to cancel + repost for queue position (default 0.5 ticks)
- `half_spread_ticks`: base half-spread (default 1)
- `order_size_base`: base order size per side
- `max_inventory_base`: inventory target for skew
- `inventory_hard_cap`: forced market-order exit threshold
- `refresh_interval_ms`: quote refresh cadence (default 100)
- `latency_kill_threshold_ms`: order round-trip latency above which quoting pauses (default 20)
- `daily_stop_loss_usd`: daily loss limit (default 750)
- `share_class`: USDT | USD
- `execution_policy_ref`: mm-queue-v1

## When to use / market regime

- **Use when**: FIFO time-priority venue where queue position is a key P&L determinant; co-located or low-latency setup
  allowing real-time L2 queue tracking; instrument where adverse selection is modellable via VPIN
- **Best regime**: liquid, active markets where queue position is achievable (not a winner-takes-first race against
  HFT); moderate-flow environments where VPIN signals are stable
- **Avoid**: venues without time-priority (pro-rata matching does not reward queue position); very high-frequency HFT
  environments where achieving and maintaining queue rank requires sub-millisecond infrastructure; instruments where L2
  data quality is insufficient for queue estimation
- **Upgrade path from**: MARKET_MAKING_INVENTORY_SKEW or MARKET_MAKING_ML_LEAN when adverse selection is the binding P&L
  constraint

## Example instances

```
MARKET_MAKING_QUEUE_MICROSTRUCTURE@binance-btc-usdt-spot-mm-prod
MARKET_MAKING_QUEUE_MICROSTRUCTURE@okx-eth-usdt-perp-mm-prod
MARKET_MAKING_QUEUE_MICROSTRUCTURE@hyperliquid-sol-usdt-perp-mm-prod
```

## Not in this archetype

- Symmetric spread without queue or VPIN modelling → [`MARKET_MAKING_PASSIVE_SPREAD`](market-making-passive-spread.md)
- Inventory-skewed quotes without queue estimation → [`MARKET_MAKING_INVENTORY_SKEW`](market-making-inventory-skew.md)
- ML-directed short-horizon lean without explicit queue model → [`MARKET_MAKING_ML_LEAN`](market-making-ml-lean.md)
- Sports/prediction event-settled quoting → [`MARKET_MAKING_EVENT_SETTLED`](market-making-event-settled.md)
- DEX concentrated-liquidity LP fee capture → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md)

## See also

- Family: [market-making.md](../families/market-making.md)
- Simpler inventory-skewed variant: [market-making-inventory-skew.md](market-making-inventory-skew.md)
- ML-lean for directional prediction overlay: [market-making-ml-lean.md](market-making-ml-lean.md)
