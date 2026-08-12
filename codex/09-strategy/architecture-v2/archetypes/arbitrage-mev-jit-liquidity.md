---
doc_type: codex-ssot
title: "Archetype: `ARBITRAGE_MEV_JIT_LIQUIDITY`"
summary: >-
  Archetype ARBITRAGE_MEV_JIT_LIQUIDITY: mints a 1-tick concentrated-LP position centred at spot just before a large
  pending swap, collects the swap fee, and burns next block (near-zero inventory). Triggers on jit_pending_swap_size_usd
  >= min_swap_threshold_usd (default $100k); runs only on 30/100 bps tiers; valid_blocks caps exposure to 2 blocks.
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
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
  ]
created: 2026-05-01
authoritative_for: [ARBITRAGE_MEV_JIT_LIQUIDITY archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ARBITRAGE_MEV_JIT_LIQUIDITY
family: ARBITRAGE_STRUCTURAL
venue_universe: [UNISWAP_V3, PANCAKESWAP_V3, SUSHISWAP_V3]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `ARBITRAGE_MEV_JIT_LIQUIDITY`

> **Family:** [Arbitrage / Structural](../families/arbitrage-structural.md) (`ARBITRAGE_STRUCTURAL`). **Settlement
> model:** ATOMIC mint / burn within a 2-block window. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/mev/jit_liquidity.py`.

## What it does

Mints a 1-tick-wide concentrated-liquidity position centred at the spot price immediately before a large pending swap is
expected to land, collects swap fees on the swap, and burns the position next block. JIT strategies eat the LP-fee tier
on the imminent swap with near-zero inventory exposure since the position lives only across the swap's block.

## Trigger

`jit_pending_swap_size_usd_<pool>` >= `min_swap_threshold_usd`.

The threshold filters out small swaps where fees won't cover the mint+burn gas cost. Default
`min_swap_threshold_usd=100000` based on the empirical break-even point on a 30 bps Uniswap V3 fee tier with mainnet
gas.

## Required feature keys

- `jit_pending_swap_size_usd_<pool_address>`
- `lp_pool_sqrt_price_<pool_address>` — for centring the 1-tick range

## Risks

- **Adverse selection on miss** — if the pending swap doesn't land in the expected block, the JIT position has to be
  cleared by the next swap, which is by definition on the wrong side of the trade. The `valid_blocks` param caps
  exposure to 2 blocks.
- **Mempool data dependence** — the pending-swap-size signal degrades in quality without a mempool feed. Today the
  engine reads a features-onchain inferred signal; with a real mempool feed (the deferred Phase 9 plan), the threshold
  can drop and capture rate goes up.
- **MEV competition** — multiple JIT searchers compete for the same swap; the pool's fee tier must be high enough that
  the surplus split N-ways is still positive. Run only on 30/100 bps tiers; skip 1/5 bps pools.

## Example instances

```
ARBITRAGE_MEV_JIT_LIQUIDITY@uniswapv3-eth-usdc-ethereum-prod
ARBITRAGE_MEV_JIT_LIQUIDITY@uniswapv3-wbtc-usdt-arbitrum-prod
ARBITRAGE_MEV_JIT_LIQUIDITY@pancakeswap-v3-bnb-usdt-bsc-prod
```

## Not in this archetype

- Persistent concentrated LP earning fees over time → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md)
- Backrunning a confirmed swap already on-chain → [`ARBITRAGE_MEV_BACKRUN`](arbitrage-mev-backrun.md)
- Front-running / sandwiching a pending victim tx → [`ARBITRAGE_MEV_SANDWICH`](arbitrage-mev-sandwich.md)
- Flash-loan liquidation of under-collateralised positions →
  [`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`](arbitrage-mev-liquidation-bundle.md)

## Plan

`plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 5.2.
