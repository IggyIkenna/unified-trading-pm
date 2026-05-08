---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  latency_budget_ms: 150
  min_sla_tier: high
---

# Archetype: `ARBITRAGE_MEV_BACKRUN`

> **Family:** `ARBITRAGE_STRUCTURAL`. **Settlement model:** Single tx with per-block ordering. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/mev/backrun.py`.

## What it does

Detects a large directional swap landed in block `N` that left two DEX pools (or DEX vs CEX) momentarily out-of-sync,
computes the optimal arbitrage path, and submits a tx with priority gas chosen to win the next-tx-after-target slot in
block `N+1`.

Unlike sandwich (which needs the victim's pending tx in the mempool), backrun reads from confirmed blocks — the victim
already executed, the spread is already on-chain. Win-probability is a function of the priority-gas bid relative to the
block's P90 priority gas (computed by features-onchain `block_priority_gas_distribution`).

## Required feature keys

- `backrun_target_swap_size_usd_<chain>` — observed swap size in block N
- `backrun_target_pool_<chain>` — pool that received the swap
- `backrun_arb_spread_bps_<chain>` — current cross-DEX/CEX spread
- `block_priority_gas_p90_gwei_<chain>` — P90 priority gas, drives bid

## Trigger

```
target_swap_size_usd >= min_target_swap_usd  AND  spread_bps >= min_spread_bps
```

The engine bids `priority_gas_bid_gwei = priority_gas_p90 * priority_gas_uplift` to maximise inclusion probability
without overpaying.

## Risks

- **Reorg** — opposite of sandwich; backrun benefits from the victim already being confirmed. A reorg that drops the
  victim also drops the spread, so the arb is no-op (revert on price-floor check).
- **Path liquidity** — large arbs route through multiple pools; if any hop's liquidity is thinner than expected, the
  realised spread is lower than the headline `arb_spread_bps`. Set `min_spread_bps` conservatively.
- **CEX leg latency** — when the arb is DEX-vs-CEX, the CEX leg is not atomic with the DEX leg; treat it like a hedge
  with finite execution alpha and budget accordingly.

## Plan

`plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 5.3.
