---
doc_type: codex-ssot
title: Concentrated liquidity — tick math + per-implementation addendum
summary:
  "Shared concentrated-liquidity (CL) tick-math SSOT for all CL AMMs (Uniswap V3/V4, Velodrome/Aerodrome Slipstream,
  Solana CLMM): sqrtPriceX96 representation, tick↔sqrtPrice, active-liquidity xy=L², position + single-step swap math,
  tick traversal, and per-implementation addenda."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer]
tags: [concentrated-liquidity, amm, defi, execution, uniswap, solana, tick-math, slippage]
related: [/codex/04-architecture/amm-slippage-simulation.md, /codex/04-architecture/batch-live-architecture.md]
created: 2026-05-11
authoritative_for: [concentrated-liquidity tick-math invariants shared across CL AMM implementations]
referenced_by:
  [/codex/04-architecture/amm-slippage-simulation.md, /codex/04-architecture/tenderly-execution-provider.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Concentrated liquidity — tick math + per-implementation addendum

> SSOT for concentrated-liquidity (CL) tick math shared across Uniswap V3 / Uniswap V4 / Velodrome Slipstream /
> Aerodrome Slipstream / Solana CLMM (Raydium + Orca) per-shape matcher implementations. Created 2026-05-12 (Phase
> 9B-NEW per `defi_simulation_realism_2026_05_10` Day-1 slot-6 design ship).

This doc factors out the **shared tick-math invariants** used by all CL-style AMMs, plus per-implementation addenda for
the parts that differ (decimals semantics, tick spacing, hook layer). Pair with
[`amm-slippage-simulation.md`](amm-slippage-simulation.md) § "Pool shape taxonomy" — that doc has the per-shape
narrative + sample pools + golden fixtures; this doc has the cross-cutting math reference.

## Core CL invariants (shared across V3 / V4 / Slipstream / Solana CLMM)

### Price representation

```
sqrtPriceX96 = uint160(sqrt(price) * 2^96)
price        = (sqrtPriceX96 / 2^96)^2 = token1 / token0
```

Q64.96 fixed-point: 64 integer bits + 96 fractional bits in a `uint160`. Multiplications use `FullMath.mulDiv` to avoid
intermediate overflow. **Token-decimal asymmetry** (USDC=6 vs WETH=18): raw `sqrtPriceX96` requires
`· 10^(decimals0 - decimals1)` adjustment before interpretation as human-readable price.

### Tick ↔ sqrtPrice

```
sqrtPriceAtTick(t) = uint160(sqrt(1.0001^t) * 2^96)
tickAtSqrtPrice(s) = floor(log(s / 2^96, 1.0001) * 2)
```

Each tick = 1 bp price step. `MIN_TICK = -887272`, `MAX_TICK = +887272` (bounds enforce that price stays within
`~[2^-128, 2^128]` representable range).

### Active liquidity invariant

Within a single tick range `[tickLower, tickUpper)`, liquidity `L` is constant and the constant-product invariant takes
the form:

```
x * y = L^2
```

where `x` = virtual token0 reserves, `y` = virtual token1 reserves in that range.

### Position math

For a position with `liquidity = L` over `[sqrtPriceLower, sqrtPriceUpper]`:

```
amount0(L, sqrtPCurrent, sqrtPUpper) = L * (sqrtPUpper - sqrtPCurrent) / (sqrtPCurrent * sqrtPUpper)
amount1(L, sqrtPLower, sqrtPCurrent) = L * (sqrtPCurrent - sqrtPLower)
```

When current price is below range: position is 100% token0. Above range: 100% token1. Inside range: mixed.

### Single-step swap math

Per `SwapMath.computeSwapStep(sqrtPCurrent, sqrtPTarget, L, amountRemaining, feePips)`:

```
amountInWithoutFee  = ceil(L * |sqrtPNext - sqrtPCurrent| / Q96)     # token0-side
                   OR L * |sqrtPNext - sqrtPCurrent| / Q96           # token1-side (no ceil)
amountIn            = ceil(amountInWithoutFee * 1e6 / (1e6 - feePips))
feeAmount           = amountIn - amountInWithoutFee
amountOut           = L * |sqrtPNext - sqrtPCurrent| / (sqrtPCurrent * sqrtPNext) * Q96
```

**Rounding semantics differ by swap direction** (exact-input vs exact-output) — round-down vs round-up on
remaining-amount math. Matching-engine MUST replicate the contract rounding direction exactly; otherwise fill prices
drift by 1 wei per swap which compounds across multi-tick crossings.

### Tick traversal

When a swap consumes all liquidity in the current tick range, the matching engine crosses to the next initialised tick:

```python
def cross_tick(pool, current_tick, zero_for_one):
    next_tick = pool.tick_bitmap.next_initialized_tick(current_tick, zero_for_one)
    liquidity_delta = pool.ticks[next_tick].liquidity_net
    # Flip sign on the side of the crossing
    new_liquidity = pool.liquidity_active + (
        liquidity_delta if not zero_for_one else -liquidity_delta
    )
    return next_tick, new_liquidity
```

**Liquidity jumps**: at each crossing, marginal price-impact slope changes discontinuously. A swap crossing N ticks
fills at a **path-dependent average price** — closed-form `xy=k` approximation fails for any swap that crosses
concentrated ranges.

## Per-implementation addenda

### Uniswap V3 (Ethereum mainnet + L2s)

- `tickSpacing` enforces per-fee-tier: 1 (0.01%), 10 (0.05%), 60 (0.30%), 200 (1.00%). Only ticks at multiples of
  `tickSpacing` host LP-position boundaries.
- Polygon V3 historically added a 100bps tier with `tickSpacing=1` (not present on Ethereum) — matching-engine MUST read
  `pool.tickSpacing()` per pool at simulation time. Same hazard on Arbitrum / Optimism / Base.
- LP positions are ERC-721 NFTs via `NonfungiblePositionManager`; fee accrual via `feeGrowthInside0LastX128` /
  `feeGrowthInside1LastX128` accumulators.
- Reference impl: `UniswapV3Pool.sol` swap() + `SwapMath.computeSwapStep()` from `v3-core`.
- Pool class shipped: `amm.py:259` (`UniswapV3Pool`). Phase 2A refactor: add `pool_shape` + `quote()` + `apply()` +
  `snapshot()` per `PoolMatcher` Protocol.

### Uniswap V4 (singleton + hooks)

- Same V3 tick math at the core curve level.
- NEW: **PoolManager singleton** holds all pools; pools register with PoolManager via `PoolKey`.
- NEW: **Hooks** intercept BEFORE_SWAP / AFTER_SWAP with returnable deltas. Hook can override fee, apply side-channel
  transfer, short-circuit the swap.
- Hook bytecode address bits encode WHICH callbacks fire (not WHAT they compute) — matcher needs hook execution backend
  (Tenderly fork / archive node) or curated registry to model hook-active pools.
- Singleton state access via `extsload(bytes32 slot)` / `exttload` (transient storage for V4) — backtest data pipeline
  needs a slot-derivation helper (see `v4-core/src/libraries/StateLibrary.sol`).
- Pool class shipped: `amm.py:403` (`UniswapV4Pool`). Hook math in
  `execution-service/execution_service/matching_engine/hooks.py`.

### Velodrome Slipstream + Aerodrome Slipstream (Optimism + Base)

- V3-clone CL pools deployed by separate `CLFactory` per fork.
- Same V3 tick math. **Per-pool fee** configurable by team (not Uniswap's fixed tier set).
- Recommended enum member: `SOLIDLY_CL_FORK` (shared matcher with `(chain_id, factory_address)` discriminator) — see
  `defi_simulation_realism_2026_05_10.md` Phase 1A enum amendment.
- Implementation: NEW `solidly_fork.py::SolidlyCLForkPool` reusing V3 base.

### Solana CLMM (Raydium V3 + Orca Whirlpool)

- Same tick-bucket math as Uniswap V3.
- Different decimal semantics: Solana token decimals span 0-18 typically; SPL-token `decimals` field per-mint.
  `sqrtPriceX64` (NOT X96) — Q64.64 fixed-point in Raydium / Orca; matcher must use the right precision.
- Tick-array layout differs from Uniswap's tick bitmap — Raydium uses fixed-size tick arrays per pool; Orca uses sparse
  arrays. Both factor down to "next initialized tick lookup" but the on-chain storage layout requires per-implementation
  deserialisation.
- Implementation: NEW `solana_clmm.py::SolanaCLMMPool` reusing V3 base.
- Pool class status: **NOT YET** (Phase 2F).

## Cross-references

- [`amm-slippage-simulation.md`](amm-slippage-simulation.md) — per-shape narrative + sample pools + golden fixtures +
  sim contract Protocol.
- [`batch-live-architecture.md`](batch-live-architecture.md) — matching-engine integration shape.
- Code:
  [`execution-service/execution_service/matching_engine/amm.py`](../../../execution-service/execution_service/matching_engine/amm.py)
  — pool class implementations.
- Plan: [`defi_simulation_realism_2026_05_10.md`](../../plans/archive/defi_simulation_realism_2026_05_10.md) Phase
  2A-H + Phase 9B.
- Reference: [Uniswap V3 Whitepaper](https://uniswap.org/whitepaper-v3.pdf) (Adams, Zinsmeister, Salem, Robinson, Keefer
  2021).
- Reference: [Uniswap V4 Whitepaper](https://github.com/Uniswap/v4-core/blob/main/docs/whitepaper-v4.pdf).
