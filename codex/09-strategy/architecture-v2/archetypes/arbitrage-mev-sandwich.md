---
doc_type: codex-ssot
title: "Archetype: `ARBITRAGE_MEV_SANDWICH` — theoretical-only (no live engine)"
summary: >-
  Archetype ARBITRAGE_MEV_SANDWICH — TRACER ONLY, no live engine (workspace has no mempool feed since Bloxroute
  removal). Walks confirmed blocks and computes the upper-bound theoretical sandwich profit (wedge minus fee_drag) to
  drive the mempool build-vs-buy decision; a load-bearing test pins that no live engine is factory-registered, gated on
  the paused mempool-feed-integration plan.
implementation_status: theoretical-only
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
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
  ]
created: 2026-05-01
authoritative_for: ["ARBITRAGE_MEV_SANDWICH archetype (theoretical tracer, no-live-engine policy)"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ARBITRAGE_MEV_SANDWICH
family: ARBITRAGE_STRUCTURAL
venue_universe: [UNISWAP_V3, BALANCER, CURVE, SUSHISWAP]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `ARBITRAGE_MEV_SANDWICH` — theoretical-only (no live engine)

> **Family:** [Arbitrage / Structural](../families/arbitrage-structural.md) (`ARBITRAGE_STRUCTURAL`). **Status:**
> **TRACER ONLY.** No live engine exists or is factory-registered. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/mev/sandwich_theoretical.py`.

## Why no live engine

Sandwich requires three transactions in three consecutive slots:

```
T0: frontrun  — buy the asset before the victim's swap
T1: victim    — the large directional swap
T2: backrun   — sell back at the post-victim price
```

The frontrun **must be inserted before** the victim's tx. That requires seeing the victim's pending tx in the mempool,
simulating its impact, and submitting the bundle through a relay that guarantees ordering (Flashbots / MEV-share /
private mempool).

The workspace does NOT currently collect a mempool feed. Bloxroute was removed and is on the Removed-providers list
(workspace `CLAUDE.md`). Live sandwich execution is therefore impossible until a mempool feed is wired back. That work
is the deferred Phase 9 plan `plans/archive/mempool_feed_integration_2026_06_01.plan.md` (status: paused, un-pause
trigger documented in the plan frontmatter).

## What the tracer DOES do

```python
from strategy_service.engine.strategies.v2.mev.sandwich_theoretical import (
    VictimSwap, compute_theoretical_profit, aggregate_theoretical_profit_usd,
)

result = compute_theoretical_profit(VictimSwap(
    block_number=12345,
    pool_address="0x...",
    chain="ETHEREUM",
    swap_size_usd=Decimal("100000"),
    pre_swap_price=Decimal("100"),
    post_swap_price=Decimal("101"),  # 100 bps impact
))
```

Walks confirmed blocks, identifies victim swaps that moved price by at least 20 bps (default threshold), and computes
the **upper-bound profit** assuming a perfect-foresight observer + atomic-bundle execution at zero slippage and zero
gas-bidding cost. Sums per-day theoretical profit and emits a "leave on table" number to drive the build-vs-buy decision
on a mempool subscription.

## Wedge formula

```
wedge        = victim_size * |price_impact_bps| / 10000
fee_drag     = victim_size * 2 * fee_tier_bps / 10000   (fees on frontrun + backrun)
profit_usd   = max(0, wedge - fee_drag)
```

This is an UPPER BOUND. Real execution would lose to:

- Slippage on frontrun + backrun legs
- Priority-gas competition with other searchers
- Bundle simulation cost
- Flash-loan fee if frontrun capital is borrowed

## Policy

Test `test_sandwich_theoretical_is_not_factory_registered` in
`strategy-service/tests/unit/engine/strategies/v2/test_sandwich_theoretical.py` is the **load-bearing assertion**: it
pins the policy that the live engine MUST NOT exist. Removing the test or registering an engine for this archetype must
be paired with the mempool-feed-integration plan shipping Phase 1.

## Example instances

```
ARBITRAGE_MEV_SANDWICH@uniswapv3-eth-usdc-ethereum-theoretical
ARBITRAGE_MEV_SANDWICH@uniswapv3-wbtc-usdt-arbitrum-theoretical
ARBITRAGE_MEV_SANDWICH@balancer-curve-eth-usdt-ethereum-theoretical
```

## Not in this archetype

- Post-confirmation backrun (no mempool required, live today) → [`ARBITRAGE_MEV_BACKRUN`](arbitrage-mev-backrun.md)
- JIT LP around an imminent swap (fee capture, not sandwich) →
  [`ARBITRAGE_MEV_JIT_LIQUIDITY`](arbitrage-mev-jit-liquidity.md)
- Flash-loan liquidation bundle → [`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`](arbitrage-mev-liquidation-bundle.md)
- Persistent cross-venue price arb (no tx-ordering dependency) →
  [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## Plan

Theoretical tracer landed in Phase 5.4 of `plans/archive/defi_pipeline_extension_2026_05_01.plan.md`.

Live execution gated on `plans/archive/mempool_feed_integration_2026_06_01.plan.md` (paused).
