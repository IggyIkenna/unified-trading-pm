---
scope: [engineer, admin]
status: theoretical-only
topology_requirements:
  isolation:
    execution-service: isolated
  latency_budget_ms: 150
  min_sla_tier: high
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Archetype: `ARBITRAGE_MEV_SANDWICH` — theoretical-only (no live engine)

> **Family:** `ARBITRAGE_STRUCTURAL`. **Status:** **TRACER ONLY.** No live engine exists or is factory-registered.
> **Code module:** `strategy-service/strategy_service/engine/strategies/v2/mev/sandwich_theoretical.py`.

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
is the deferred Phase 9 plan `plans/active/mempool_feed_integration_2026_06_01.plan.md` (status: paused, un-pause
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

## Plan

Theoretical tracer landed in Phase 5.4 of `plans/active/defi_pipeline_extension_2026_05_01.plan.md`.

Live execution gated on `plans/active/mempool_feed_integration_2026_06_01.plan.md` (paused).
