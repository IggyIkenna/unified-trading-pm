---
doc_type: codex-ssot
title: "Archetype: `ARBITRAGE_MEV_BACKRUN`"
summary: >-
  Archetype ARBITRAGE_MEV_BACKRUN: submits a priority-gas tx in block N+1 to capture the cross-DEX/CEX spread left by a
  large confirmed swap in block N. Reads confirmed blocks (no mempool needed); bids priority_gas_bid = priority_gas_p90
  * uplift; triggers on target_swap_size_usd >= min_target_swap_usd AND spread_bps >= min_spread_bps.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, arbitrage, defi, mev, execution, archetype]
related:
  [
    ../families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
  ]
created: 2026-05-01
authoritative_for: [ARBITRAGE_MEV_BACKRUN archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ARBITRAGE_MEV_BACKRUN
family: ARBITRAGE_STRUCTURAL
venue_universe: [UNISWAP_V3, BALANCER, CURVE, SUSHISWAP, BINANCE, BYBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `ARBITRAGE_MEV_BACKRUN`

> **Family:** [Arbitrage / Structural](../families/arbitrage-structural.md) (`ARBITRAGE_STRUCTURAL`). **Settlement
> model:** Single tx with per-block ordering. **Code module:**
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

## Example instances

```
ARBITRAGE_MEV_BACKRUN@uniswapv3-eth-usdc-ethereum-prod
ARBITRAGE_MEV_BACKRUN@uniswapv3-balancer-wbtc-usdt-arbitrum-prod
ARBITRAGE_MEV_BACKRUN@uniswapv3-binance-eth-usdt-ethereum-prod
```

## Not in this archetype

- Front-running a pending victim tx (requires mempool feed) → [`ARBITRAGE_MEV_SANDWICH`](arbitrage-mev-sandwich.md)
- JIT LP minted around an imminent swap → [`ARBITRAGE_MEV_JIT_LIQUIDITY`](arbitrage-mev-jit-liquidity.md)
- Flash-loan liquidation bundle (different profit mechanism) →
  [`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`](arbitrage-mev-liquidation-bundle.md)
- Persistent cross-venue price arb (no per-block ordering dependency) →
  [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## Plan

`plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 5.3.
