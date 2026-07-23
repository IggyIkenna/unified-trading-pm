---
doc_type: codex-ssot
title: AMM Slippage + Simulation Realism
summary:
  Matching-engine simulation-realism SSOT — per-PoolShape AMM slippage models (V2/V3/V4/Curve/Balancer/Solana
  CLMM/Solidly/aggregator) behind the PoolMatcher quote()/apply() Protocol, lending rate-impact-from-own-trade,
  golden-swap ≤5-10bps fidelity gate; the batch=live seam is apply() (in-memory mutate vs on-chain tx).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    deployment-ui,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer]
tags: [defi, execution, amm, backtest, data-quality, verification]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/04-architecture/cefi-batch-live.md,
  ]
created: 2026-05-10
authoritative_for: [AMM per-pool-shape slippage and matching-engine simulation realism]
referenced_by:
  [
    /codex/02-data/defi-data-type-taxonomy.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/cefi-batch-live.md,
    /codex/04-architecture/concentrated-liquidity.md,
    /codex/04-architecture/matching-engine-assumptions.md,
    /codex/04-architecture/tenderly-execution-provider.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# AMM Slippage + Simulation Realism

> SSOT for matching engine simulation realism: per-pool-shape AMM models, lending rate-impact-from-own-trade, governance
> proposal simulation harness, staking + restaking yield-stream models, slashing tail-risk MC. Last updated 2026-05-10
> (defi_simulation_realism_2026_05_10 Phase 9A).

This doc is the architecture-side companion to
[`defi_simulation_realism_2026_05_10.md`](../../plans/archive/defi_simulation_realism_2026_05_10.md). It declares the
mathematical models + their input shapes + their validation thresholds for every simulation primitive. The plan ships
the implementation; this doc locks the contract.

## Why simulation realism matters

The matching engine is the **batch surface** that backtest P&L runs against, per CLAUDE.md "Batch = Live" principle:
"Batch and live use the SAME code path, same component interactions. The ONLY difference is execution fills." The
matching engine produces the simulated fills for batch (and for live's "always fill at requested price" strategy P&L
mode). If the matching engine model is wrong, backtest P&L is wrong, the strategy ships with the wrong sizing

- the wrong tail risk, and live trade losses surprise everyone.

Pre-2026-05-10 matching engine had ONE AMM **matcher** (constant product `x*y=k`) per
[`engine.py:7-12`](../../../execution-service/execution_service/matching_engine/engine.py): "AMMMatcher: DeFi Swaps
(constant product x\*y=k)". The pool **classes** for `UniswapV2Pool` (`amm.py:52`), `UniswapV3Pool` (`amm.py:259`), and
`UniswapV4Pool` (`amm.py:403`) all exist with full math, but the `AMMMatcher` dispatcher at
[`engine.py:433`](../../../execution-service/execution_service/matching_engine/engine.py) hardcodes V2 only (line 471
`cast("UniswapV2Pool | None", ...)`) — V3 + V4 pool classes are unreachable through current routing. Every other AMM
family (Curve / Balancer / Solana CLMM / Solidly-fork / aggregators) is BOTH unrouted AND has no pool-class
implementation, producing 50-500bps fill-price errors for any non-V2 leg.

This doc fixes that by declaring per-pool-shape models that match production within ~5-10bps + by separating the gap
into (a) wire up existing V3/V4 pool classes via dispatch-by-`PoolShape`, (b) ship the 7 missing pool classes (Curve
stable + crypto, Balancer weighted + boosted, Solana CLMM, Solidly-fork, Jupiter aggregator).

## Pool shape taxonomy + slippage models

**Per-pool-shape model** (UAC `PoolShape` enum, declared in `defi_simulation_realism` Phase 1A):

### 1. Uniswap V2 (constant product x\*y=k)

```
amount_out = (reserve_out * amount_in) / (reserve_in + amount_in)
```

Realized fill = pre-fee output minus 0.3% LP fee. Existing in `matching_engine/amm.py:UniswapV2Pool`. ✅ correct.

### 2. Uniswap V3 (concentrated liquidity, tick-bucket integration)

V3 fills consume liquidity at the current tick first; if size pushes through tick boundaries, integrates over each tick
crossed. Per-tick: `getAmountsForLiquidity(sqrtPriceLower, sqrtPriceUpper, liquidity)`.

```python
def v3_swap_exact_input(pool, amount_in, zero_for_one):
    sqrtP = pool.sqrt_price_x96
    tick = pool.current_tick
    liquidity = pool.liquidity_active
    amount_in_remaining = amount_in
    amount_out_total = 0

    while amount_in_remaining > 0:
        # Find next initialized tick boundary
        sqrtP_next = pool.next_tick_sqrt_price(tick, zero_for_one)

        # Compute fill within current tick range (closed-form)
        delta_in, delta_out, sqrtP_after = compute_tick_swap(
            sqrtP, sqrtP_next, liquidity, amount_in_remaining, zero_for_one
        )

        amount_in_remaining -= delta_in
        amount_out_total += delta_out
        sqrtP = sqrtP_after

        if amount_in_remaining > 0:
            # Crossed boundary; load next tick's liquidity
            tick = pool.cross_tick(tick, zero_for_one)
            liquidity = pool.liquidity_at_tick(tick)

    return amount_out_total
```

**Inputs** (from MTDS captures): `sqrtPriceX96`, `tick`, `liquidity_active`, `tick_liquidity_bitmap`, fee tier.
**Validation**: ≥ 100 historical Tenderly-fork swaps within 5bps of on-chain real fill at the same block.

### 3. Uniswap V4 (V3 + hooks)

V3 base + per-pool hook bytecode applied at `beforeSwap` / `afterSwap`. Hook deltas:

- `BeforeSwapDelta`: hook can override input amount or short-circuit return value.
- `AfterSwapDelta`: hook can adjust output post-swap.

Existing `hooks.py:CustomCurveHook` covers `constant_sum`, `constant_mean`, `polynomial`, `logarithmic` curves. Phase 2B
extends to V4 hook semantics.

### 4. Curve stable (D-invariant)

Stable pools use the StableSwap invariant:

```
A * n^n * sum(x_i) + D = A * D * n^n + D^(n+1) / (n^n * prod(x_i))
```

where `A` is the amplification coefficient, `n` is number of tokens, `x_i` are reserves.

Solving for output given input requires Newton-Raphson on the invariant. Reference: Curve V1 paper.

### 5. Curve crypto (D + gamma)

Crypto pools (3pool / tricrypto) use a gamma-augmented invariant:

```
K = A * D^(n-1) / (n^n * prod(x_i))
G = gamma^2 / (gamma + 1 - K)^2
sum(x_i) + G * D = D + (G + 1) * D^(n+1) / (n^n * prod(x_i))
```

More expensive to solve; reference Curve V2 SDK.

**Inputs**: per-pool reserves, `A`, `gamma`, `D`. **Validation**: ≥ 50 historical Curve swaps within 5bps.

### 6. Balancer weighted

```
amount_out = balance_out * (1 - (balance_in / (balance_in + amount_in))^(weight_in / weight_out))
```

**Inputs**: per-pool token balances + weights. **Validation**: ≥ 20 historical Balancer swaps within 5bps.

### 7. Balancer boosted + composable

Boosted = linear-pool building blocks (Aave aTokens wrapped); composable = phantom BPT in pool. Both reduce to weighted
internally — handle the routing layer (decompose multi-leg via Balancer Vault).

### 8. Solana CLMM (Raydium + Orca)

Same tick-bucket math as Uniswap V3 but per-Solana-CLMM decimals + SPL-token semantics. New `SolanaCLMMPool` reuses V3
base.

**Inputs**: per-pool tick bitmap (Solana-specific layout), `sqrt_price_x96`-equivalent, `liquidity_active`.
**Validation**: ≥ 30 historical Raydium / Orca swaps within 5bps.

### 9. Aggregator (Jupiter / 1inch / 0x / ParaSwap)

Read route from quote API; for each route leg, route to the appropriate pool-shape matcher above; compose realized fill
across legs.

```python
def aggregator_swap(route, amount_in):
    amount_in_remaining = amount_in
    amount_out_total = 0
    for leg in route.legs:
        leg_amount_in = amount_in_remaining * leg.input_share
        leg_amount_out = match_per_pool_shape(leg.pool_shape, leg.pool_state, leg_amount_in)
        amount_in_remaining -= leg_amount_in
        amount_out_total += leg_amount_out
    return amount_out_total
```

**Validation**: ≥ 30 historical Jupiter routes within 10bps (looser since multi-hop variance).

### 10. Solidly-fork ve(3,3) — Velodrome / Aerodrome (and other Solidly forks)

Single matcher serves all classic Solidly forks (Velodrome on Optimism, Aerodrome on Base, Equalizer on Fantom, Thena on
BSC, Ramses on Arbitrum, etc.) discriminated by `(chain_id, factory_address)`. Each pool carries a `stable: bool` flag
at pool creation selecting between two invariants:

- **Volatile** (`stable=false`): `x * y = k` (identical to Uniswap V2 constant product).
- **Stable** (`stable=true`): Solidly cubic invariant `x^3 * y + x * y^3 = k` — flatter than Curve near peg but uses a
  closed-form cubic rather than amplification-coefficient interpolation.

Output amount for the stable branch is computed via Newton-Raphson `_get_y(x_new, k, y_old)` solver (Velodrome
`Pool.sol::_get_y`, 255-iteration cap, revert-on-non-convergence). Decimals are normalised to 1e18 internally BEFORE
invariant math — critical edge case for 6-decimal tokens like USDC; cube terms overflow naïve uint256 arithmetic without
scale-down.

Fee model: per-pool, configurable by factory admin (`PoolFactory.setFee(pool, fee)`); defaults ~5 bps stable / ~30 bps
volatile. **Fees are siphoned to `PoolFees` distributor** (NOT added to reserves) — this is the ve(3,3) flywheel hook
that distributes to veVELO / veAERO voters. Backtest reserve reconstruction must subtract the siphoned fee, unlike
Uniswap V2 where fee grows `k`.

**Inputs** (from MTDS captures): `(reserve0, reserve1, stable: bool, fee_bps, decimals0, decimals1)`. Optional
`PoolFees` accumulator if backtest tracks LP fee distribution separately. **Validation**: ≥ 20 historical Velodrome + ≥
20 historical Aerodrome swaps within 5bps; mixed flavour coverage (stable + volatile per fork).

**Out-of-scope for this matcher** (separate enum members): **Velodrome Slipstream** (concentrated-liquidity Uniswap-V3
clone on Optimism, late-2024 launch) and **Aerodrome Slipstream** (CL fork on Base, mid-2024 launch) — both use V3 tick
math + a separate `CLFactory`. Either model as `SOLIDLY_CL_FORK` with `(chain, factory)` discriminator (sharing V3
math + tick mechanics) or as parallel enum members `VELODROME_SLIPSTREAM` / `AERODROME_SLIPSTREAM`. **Open question for
Phase 1A operator decision** — see plan body Phase 1A note.

## Per-shape sample pools + golden fixture seeds (Day-1 slot 6 design ship 2026-05-11)

Below table enumerates the matrix that Phase 2 implementations validate against. Pool addresses verified at research
time; TX hashes + exact reserves to be pinned by master agent (or Harsh slot 4 implementer) at fixture-capture time via
`cast logs` / Etherscan / subgraph queries. **Validation harness reads fixture file, re-runs each leg through
`_amm_match_impl`, asserts |fill-bps delta| < tolerance.**

| Shape                      | Chain                | Sample pool address                                                                                               | Primary token pair                         | Fee                                                | Validation threshold                                                  | Pool class status                                                                                    |
| -------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `UNISWAP_V2`               | Ethereum mainnet     | `0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc`                                                                      | USDC / WETH                                | 30 bps flat                                        | ≥1 swap exact (0 wei drift on V2 integer math)                        | ✅ `UniswapV2Pool` shipped (`amm.py:52`)                                                             |
| `UNISWAP_V3`               | Ethereum mainnet     | `0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`                                                                      | USDC / WETH (0.05% tier)                   | 5 / 30 / 100 / 1000 bps tiered                     | ≥100 swaps within 5 bps                                               | ✅ `UniswapV3Pool` shipped (`amm.py:259`)                                                            |
| `UNISWAP_V4_HOOK`          | Ethereum mainnet     | `PoolManager 0x000000000004444c5dc75cB358380D2e3dE08A90` + vanilla USDC/WETH pool key                             | USDC / WETH (varies)                       | base + hook delta dynamic                          | ≥10 vanilla swaps (V3-equivalent) + ≥5 hook-active swaps within 5 bps | ✅ `UniswapV4Pool` shipped (`amm.py:403`) — hook dispatch via `hooks.py`                             |
| `CURVE_STABLE`             | Ethereum mainnet     | `0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7` (3pool DAI/USDC/USDT)                                                | n-token stable basket                      | 1-4 bps; `admin_fee` 50%                           | ≥50 swaps within 5 bps; metapool composition path required            | ❌ NOT YET — Phase 2C needs new `CurveStablePool` class                                              |
| `CURVE_CRYPTO`             | Ethereum mainnet     | `0xD51a44d3FaE010294C616388b506AcdA1bfAAE46` (tricrypto USDT/WBTC/ETH)                                            | 3-token crypto basket                      | dynamic `mid_fee`/`out_fee` + EMA oracle           | ≥30 swaps within 10 bps (looser; gamma math non-trivial)              | ❌ NOT YET — Phase 2C deferred to crypto-pool extension                                              |
| `BALANCER_WEIGHTED`        | Ethereum mainnet     | `0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56` (B-80BAL-20WETH; Vault `0xBA12222222228d8Ba445958a75a0704d566BF2C8`) | BAL / WETH (80/20)                         | 10 bps (per-pool configurable; bounds 0.0001%-10%) | ≥20 swaps within 5 bps via Vault `batchSwap`                          | ❌ NOT YET — Phase 2D needs new `BalancerWeightedPool` class                                         |
| `BALANCER_BOOSTED`         | Ethereum mainnet     | Phase 2E candidate: a `bb-a-USD` boosted pool — pin at impl time                                                  | stable basket via Aave aToken linear pools | composite (linear-pool spread + weighted swap fee) | ≥5 swaps within 5 bps                                                 | ❌ NOT YET — Phase 2E                                                                                |
| `SOLANA_CLMM`              | Solana mainnet       | Phase 2F candidate: Raydium USDC/SOL CLMM — pin at impl time                                                      | USDC / SOL                                 | tiered (Raydium 5/25/100/1000 bps; Orca similar)   | ≥30 swaps within 5 bps                                                | ❌ NOT YET — Phase 2F (reuses V3 base)                                                               |
| `JUPITER_ROUTE_AGGREGATOR` | Solana mainnet       | n/a (route from Jupiter quote API)                                                                                | varies per route                           | composite of leg fees                              | ≥30 routes within 10 bps (looser; multi-hop variance)                 | ❌ NOT YET — Phase 2G (route decomposition)                                                          |
| `SOLIDLY_FORK`             | Optimism (Velodrome) | `0x2B4C76d0dc16BE1C31D4C1DC53bF9B45987Fc75c` (USDC/USDT stable, `stable=true`, ~5 bps fee)                        | USDC / USDT                                | 5-30 bps per-pool configurable                     | ≥20 swaps Velodrome within 5 bps                                      | ❌ NOT YET — Phase 2H (NEW: was not in original Phase 1A enum; added Day-1 slot 6 design 2026-05-11) |
| `SOLIDLY_FORK`             | Base (Aerodrome)     | `0x6cDcb1C4A4D1C3C6d054b27AC5B77e89eAFb971d` (USDC/AERO volatile, `stable=false`, ~30 bps fee)                    | USDC / AERO                                | 5-30 bps per-pool configurable                     | ≥20 swaps Aerodrome within 5 bps; shared matcher with Velodrome       | ❌ NOT YET — Phase 2H (shared matcher)                                                               |

**Reading the "Pool class status" column**: pool-class-shipped means `amm.py` has a Python class implementing the math;
it does NOT mean the `AMMMatcher` dispatcher in
[`engine.py:433`](../../../execution-service/execution_service/matching_engine/engine.py) routes to it. Per 2026-05-11
slot-6 read, the matcher hardcodes `UniswapV2Pool` only at line 471
(`pool = cast("UniswapV2Pool | None", kwargs.get("pool", self._pool))`). **Phase 2 work is therefore: (a) extend
`AMMMatcher` to dispatch by `pool.pool_shape` attribute, (b) add the 7 missing pool classes (Curve stable + crypto,
Balancer weighted + boosted, Solana CLMM, Solidly-fork volatile + stable, Jupiter route composer), (c) validate each per
its row above.** V3 + V4 are NOT greenfield — they need wiring only.

## Simulation contract — unified pre-trade quote interface (Day-1 slot 6 design ship 2026-05-11)

Phase 2 of `defi_simulation_realism` extends `AMMMatcher` (`engine.py:433`) to dispatch by `pool.pool_shape` instead of
hardcoding `UniswapV2Pool`. All pool classes implement a common `PoolMatcher` Protocol that the matching engine +
strategy P&L backtest replay engine call uniformly:

```python
# execution-service/execution_service/matching_engine/pool_matcher.py (NEW Phase 2A)
from typing import Protocol
from decimal import Decimal
from unified_api_contracts.internal import OrderSide, PoolShape, SwapQuote, FillResult

class PoolMatcher(Protocol):
    """Pre-trade quote + post-trade apply protocol implemented by every PoolShape.

    `quote()` is read-only (does NOT mutate pool state) and returns the simulated
    fill INCLUDING fee + price impact. `apply()` is mutating (advances reserves /
    tick / sqrtPrice / D) and is called by the matching engine after the strategy
    accepts the quote. Idempotency requirement: `quote()` is referentially-transparent
    for a fixed pool snapshot.

    Implementers: UniswapV2Pool (shipped), UniswapV3Pool (shipped), UniswapV4Pool
    (shipped, hooks via hooks.py), CurveStablePool (Phase 2C), CurveCryptoPool
    (Phase 2C-deferred), BalancerWeightedPool (Phase 2D), BalancerBoostedPool
    (Phase 2E), SolanaCLMMPool (Phase 2F), SolidlyForkPool (Phase 2H — NEW),
    SolidlyCLForkPool (Phase 2H — NEW), JupiterAggregatorRoute (Phase 2G).
    """

    pool_shape: PoolShape

    def quote(self, amount_in: Decimal, side: OrderSide) -> SwapQuote:
        """Read-only pre-trade quote. Returns expected fill + fee + price-impact.

        Args:
            amount_in: input amount in token0 (BUY) or token1 (SELL) native decimals.
            side: BUY (swap token1→token0) or SELL (swap token0→token1).
        Returns:
            SwapQuote(amount_out, fee_amount, price_impact_bps, spot_price_pre,
                      spot_price_post, gas_estimate_units, hooks_invoked,
                      ticks_crossed, used_curves).
        """
        ...

    def apply(self, amount_in: Decimal, side: OrderSide) -> FillResult:
        """Mutating apply. Advances pool state; returns realized FillResult.

        FillResult fields match SwapQuote + adds: filled_at_block (None for
        Tenderly fork sim), realized_slippage_vs_quote_bps, hooks_log.
        """
        ...

    def spot_price(self, base: str, quote: str) -> Decimal:
        """Read-only mid-price. No fee, no impact."""
        ...

    def snapshot(self) -> dict:
        """Read-only state snapshot — enables Tenderly-fork comparison harness +
        per-test fixture replay determinism. Returned dict is sufficient to
        re-construct the pool via the inverse `cls.from_snapshot(snapshot_dict)`."""
        ...
```

The matching engine dispatcher resolves `pool.pool_shape` → matcher fn via a registry, then calls the unified `quote()`
/ `apply()` interface. Required dispatcher refactor at
[`engine.py:_amm_match_impl`](../../../execution-service/execution_service/matching_engine/engine.py#L94):

```python
# BEFORE (current — hardcoded V2 only):
def _amm_match_impl(pool: UniswapV2Pool, ...): ...

# AFTER (Phase 2 wiring):
def _amm_match_impl(pool: PoolMatcher, ...):
    quote = pool.quote(amount_in, side)
    if not _passes_slippage_check(quote, slippage_tolerance):
        return MatchResult(failed=True, reason="SLIPPAGE_EXCEEDED", ...)
    fill = pool.apply(amount_in, side)
    return MatchResult(filled=True, fill=fill, quote_delta=quote_vs_fill, ...)
```

`SwapQuote` + `FillResult` + `PoolShape` + `OrderSide` are UAC `internal` schemas (declared in Phase 1A). Pool-class
implementations live in `execution-service/execution_service/matching_engine/` per `pool_shape`:

- `amm.py` — Uniswap V2/V3/V4 pool classes (shipped; add `pool_shape` field + `quote()`/`apply()`/`snapshot()` methods
  to satisfy `PoolMatcher` Protocol — Phase 2A refactor).
- `curve.py` (NEW Phase 2C) — `CurveStablePool` (D-invariant + Newton-Raphson + A ramp) + `CurveCryptoPool` (D + gamma)
  classes.
- `balancer.py` (NEW Phase 2D) — `BalancerWeightedPool` (closed-form weighted) + `BalancerBoostedPool` (Phase 2E
  linear-pool wrapper).
- `solana_clmm.py` (NEW Phase 2F) — `SolanaCLMMPool` reusing V3 tick math + Solana decimals semantics.
- `solidly_fork.py` (NEW Phase 2H) — `SolidlyForkPool` (cubic stable + xy=k volatile branch via `stable: bool` flag) +
  `SolidlyCLForkPool` (V3-tick CL clone — Slipstream variants).
- `aggregator.py` (NEW Phase 2G) — `JupiterAggregatorRoute` (multi-leg route composer reading from Jupiter quote API +
  dispatching per-leg to the appropriate `PoolMatcher`).
- `hooks.py` (shipped) — V4 `BeforeSwapHook` / `AfterSwapHook` Protocols + custom-curve implementations (constant_sum /
  constant_mean / polynomial / logarithmic).

**Multi-hop routing** (aggregator path) reuses the Protocol uniformly: each leg's pool is a `PoolMatcher`; the
aggregator sums per-leg `SwapQuote`s into a composite route quote.

### Implementation status — Phase 2 as-built (execution-service, 2026-05-12)

Harsh slot 4 landed the Phase 2 implementation half against the design above:

- **`pool_matcher.py`** (NEW) — `PoolMatcher` Protocol (`quote` / `apply` / `spot_price` property / `snapshot`),
  `POOL_MATCHER_REGISTRY` + `@register_pool_matcher(shape)` class decorator (sets `cls.pool_shape`; rejects a
  _different_ class for an already-registered shape), `pool_matcher_from_snapshot(shape, dict)` (dispatches to the
  registered class's `from_snapshot` classmethod), and a `BasePoolMatcher` mixin that implements
  `quote`/`apply`/`snapshot` over three subclass primitives: `simulate_swap(amount_in, token_in)` (read-only),
  `execute_swap(amount_in, token_in)` (mutating), `snapshot_state()` (+ classmethod `from_snapshot`). `side_to_token_in`
  maps `SELL → "x"` (token0 in), `BUY → "y"` (token1 in); `amount_in` is in the input token's native decimals. UAC
  schemas (`PoolShape` 15-member enum, `SwapQuote`, `FillResult`, `OrderSide`) live in
  `unified_api_contracts/internal/domain/matching_engine/`.
- **`amm.py`** — `UniswapV2Pool` / `UniswapV3Pool` / `UniswapV4Pool` mix in `BasePoolMatcher` + `@register_pool_matcher`
  (`UNISWAP_V2` / `UNISWAP_V3` / `UNISWAP_V4_HOOK`); `execute_swap` added to V3/V4 (advances `sqrtPriceX96` + `tick`
  within the active tick range — single-active-tick model; multi-tick-bitmap traversal is a Phase-3-validation
  follow-up); `spot_price` property + `snapshot_state` + `from_snapshot` on all three.
- **`curve.py`** (NEW) — `CurveStablePool` (`CURVE_STABLE`): n-token StableSwap D-invariant, Newton–Raphson `_get_d`
  - `_get_y` (255-iter cap, 1e-18 tol), reserves normalised to human units (`balance / 10**decimals`) so
    6-/8-/18-decimal baskets coexist, `admin_fee` removed from reserves on `execute_swap`,
    `get_amount_out_indexed(i, j, …)` for >2-token baskets. `CURVE_CRYPTO` (D + γ + EMA oracle) is unimplemented —
    Phase-2C follow-up.
- **`balancer.py`** (NEW) — `BalancerWeightedPool` (`BALANCER_WEIGHTED`): weighted-product curve, fee on input, fee-free
  Balancer spot price `(B_j/W_j) / (B_i/W_i)`, `get_amount_out_indexed`. `BalancerBoostedPool` (`BALANCER_BOOSTED`):
  linear-pool spread folded into the effective fee. `BALANCER_COMPOSABLE` (phantom-BPT + Vault `batchSwap` routing) is
  unimplemented — Phase-2E follow-up.
- **`solidly_fork.py`** (NEW) — `SolidlyForkPool` (`SOLIDLY_FORK`): shared matcher for all classic Solidly forks
  (Velodrome / Aerodrome / Equalizer / Thena / Ramses…), discriminated by `(chain_id, factory_address)` + a per-pool
  `stable: bool` flag — cubic stable invariant `x^3·y + x·y^3 = k` (Newton–Raphson `_get_y`, 255-iter cap,
  revert-on-non-convergence) / `x·y = k` volatile branch; reserves normalised to human units BEFORE invariant math (USDC
  6-dec overflow edge case); fee siphoned to `PoolFees` (ve(3,3) flywheel — NOT added back to reserves, unlike Uniswap
  V2 where the fee grows `k`); `_hooks_invoked → ("poolFeesNotify",)`. `SOLIDLY_CL_FORK` (Slipstream V3-tick CL pools —
  reuses V3 tick math + `(chain, CLFactory)` discriminator) is unimplemented — Phase-2H follow-up.
- **`solana_clmm.py`** (NEW) — `SolanaCLMMPool` (`SOLANA_CLMM`) subclasses `UniswapV3Pool` (same concentrated-liquidity
  tick math); `SolanaAMMPool` (`SOLANA_AMM`) subclasses `UniswapV2Pool` (Raydium V4 standard `xy=k` pool).
- **`aggregator.py`** (NEW) — `RouteLeg` (per-leg `pool_shape` + `pool_snapshot` + `side` + `input_share` + `chain_id`
  - `pool_address`; `to_dict`/`from_dict`) + `AggregatorRouteMatcher` (`JUPITER_ROUTE_AGGREGATOR`): satisfies the
    `PoolMatcher` Protocol; builds each leg's underlying `PoolMatcher` via `pool_matcher_from_snapshot` and composes
    per-leg `quote()`/`apply()` into a route-level `SwapQuote`/`FillResult` with per-leg sub-quotes in `.legs`; two
    route kinds — `"split"` (parallel — each leg takes `input_share` of route input, outputs summed) and `"chain"`
    (serial multi-hop — leg _i_ consumes 100 % of leg _i-1_'s output); `spot_price` = product (chain) /
    share-weighted-sum (split) of per-leg effective rates; `snapshot`/`from_snapshot` round-trip the route + per-leg
    pool snapshots (reflecting prior `apply` mutations); `FillResult.mempool_path ∈ {BATCH_SIM, PUBLIC, PRIVATE}` for
    MEV-vs-slippage execution-alpha attribution. `OneInchRouteMatcher` / `ZeroExRouteMatcher` subclasses bind the same
    logic to `ONEINCH_AGGREGATOR` / `ZEROX_AGGREGATOR`. **Batch replay** of aggregator legs is gated on the NEW
    `aggregator_route` MTDS data_type (captured-route JSON persisted at decision time — catalogue gap) + the
    `(chain, pool_address) → PoolShape` lookup (MTDS `dex_pools`); the **live-mode** quote-API fetch path
    (`jup.ag/quote` / `1inch.io/.../quote` / `api.0x.org/swap/v1/quote`) is the same follow-up.
- **`engine.py`** — `_amm_match_impl` dispatches via the `PoolMatcher` Protocol (`quote()` → slippage gate → `apply()`);
  `AMMMatcher` accepts any `PoolMatcher`; the per-shape modules are side-effect-imported by `engine.py` so the registry
  is populated; the local `OrderSide` enum was deleted in favour of `unified_api_contracts.internal.OrderSide`.

`bash scripts/quality-gates.sh` on a fresh execution-service `.venv` should be re-run to gate on the full suite —
verified this session via the workspace `.venv-workspace` + `PYTHONPATH` override (`tests/unit/test_pool_matcher.py` 54
tests + 593 across the matching-engine suite green; `ruff` + `basedpyright` clean on all touched files, modulo the
pre-existing `engine.py:_mk` `OrderType` mismatch [a dual-`OrderType`-import bug in UAC `internal/__init__.py`] and
`sports_matching.py:394` unnecessary comparison — neither introduced here). Per-shape historical-swap validation (the ≥
N-Tenderly-fork / on-chain-`Swap`-event corpus) lands with the golden-test-set harness below — until then the matchers
are math-correct (round-trip-tested + invariant-tested) but not yet bps-validated against on-chain fills.

## Golden test set harness (Day-1 slot 6 design ship 2026-05-11)

Phase 3 of `defi_simulation_realism` ships the per-shape fixture corpus that locks the matcher fidelity gate in CI.
Lives at
[`execution-service/tests/integration/fixtures/amm_golden_swaps/`](../../../execution-service/tests/integration/fixtures/)
as one JSON file per `PoolShape`:

```
amm_golden_swaps/
├── uniswap_v2.json           # ≥ 5 swaps (V2 is integer-exact — small corpus OK)
├── uniswap_v3.json           # ≥ 100 swaps spanning multi-tick crossings
├── uniswap_v4.json           # ≥ 10 vanilla (hooks=address(0)) + ≥ 5 hook-active
├── curve_stable.json         # ≥ 50 swaps on 3pool + ≥ 10 metapool compositions
├── balancer_weighted.json    # ≥ 20 swaps on B-80BAL-20WETH + ≥ 5 batchSwap routes
├── solana_clmm.json          # ≥ 30 swaps on Raydium + Orca CLMMs
├── jupiter_routes.json       # ≥ 30 multi-leg routes
└── solidly_fork.json         # ≥ 20 Velodrome + ≥ 20 Aerodrome (mixed stable + volatile)
```

Fixture row schema (canonical JSON shape — same across all `PoolShape`s):

```json
{
  "pool_shape": "UNISWAP_V3",
  "chain_id": 1,
  "pool_address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
  "block_number": 19500000,
  "tx_hash": "0x...",
  "snapshot_pre": {
    "sqrt_price_x96": "1234567890",
    "liquidity": "1000000000000",
    "tick": 195000,
    "fee_tier_bps": 5
  },
  "swap": {
    "amount_in_native": "100000000000",
    "token_in_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "side": "SELL",
    "amount_out_native_expected": "54500000000000000000",
    "token_out_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "fee_amount_native": "300000",
    "price_impact_bps_expected": 8,
    "ticks_crossed_expected": 3
  },
  "snapshot_post": {
    "sqrt_price_x96": "1234560000",
    "liquidity": "1000000000000",
    "tick": 194997,
    "fee_tier_bps": 5
  },
  "tolerance_bps": 5,
  "source": "etherscan-swap-event-2024-Q2-window"
}
```

Harness (`execution-service/tests/integration/test_amm_golden_swaps.py` — NEW Phase 3C):

```python
@pytest.mark.parametrize("fixture_file", AMM_GOLDEN_FIXTURE_FILES)
def test_amm_golden_swap_replay(fixture_file: Path) -> None:
    for row in load_fixture(fixture_file):
        pool = pool_from_snapshot(row["pool_shape"], row["snapshot_pre"])
        quote = pool.quote(
            Decimal(row["swap"]["amount_in_native"]),
            OrderSide[row["swap"]["side"]],
        )
        # Pure-math fidelity: simulated quote within tolerance of on-chain Swap event
        delta_bps = abs(
            (quote.amount_out / Decimal(row["swap"]["amount_out_native_expected"]) - 1) * 10000
        )
        assert delta_bps < row["tolerance_bps"], (
            f"{row['pool_shape']} {row['pool_address']} block={row['block_number']} "
            f"tx={row['tx_hash']}: |fill delta| = {delta_bps} bps > {row['tolerance_bps']}"
        )
        pool.apply(...)  # mutate
        assert pool.snapshot() == row["snapshot_post"], (
            f"{row['pool_shape']} post-state drift"
        )
```

Fixture capture (Phase 3A operator/Harsh runbook): per-shape script under
`execution-service/scripts/capture_golden_swaps.py --pool-shape <X> --pool <addr> --from-block <N> --window <K>` queries
archive node via `eth_getLogs` for the pool's `Swap` event topic, snapshots `slot0()` / reserves at `block - 1` and
`block`, persists JSON row matching schema above. **Run on same-region GCE VM** per CLAUDE.md "Manifest phantom audit"
pattern (cross-region archive node listing is 18× slower).

**Capture cadence**: fixture refresh per-shape on each AMM-family-upgrade (V3 → V4 hook activation, Balancer V2 → V3
launch, new fee tier deployment). Cron VM under `deployment-service/scripts/vm/` per CLAUDE.md "Runbook Execution-Owner
SSOT" — owner: Harsh slot 4 (implementer); cadence: per-deploy when matcher code changes; verifier: harness exit code +
`|delta| < tolerance_bps` per row.

### Cross-chain L2 deployment notes (Phase 2 implementation hazard)

V3 deployed on Arbitrum / Optimism / Polygon / Base under the SAME factory bytecode but with `factory.enableFeeAmount()`
overrides — Polygon historically added a 100bps tier with `tickSpacing=1` not present on Ethereum. **Matcher MUST read
`pool.tickSpacing()` per pool at simulation time, NOT hardcode by fee tier**. Same hazard applies to Balancer (Vault
address `0xBA12222222228d8Ba445958a75a0704d566BF2C8` is identical across Ethereum / Polygon / Arbitrum / Optimism /
Gnosis / Avalanche / Base, but per-pool fees diverge) and to Curve (per-chain `A` parameters may differ from Ethereum
reference). Per-chain calibration data must be captured per Phase 2 validation rows.

## Matching-engine end-to-end integration (Day-1 slot 6 design ship 2026-05-11)

Per CLAUDE.md "Batch = Live" HARD RULE: batch + live use the SAME `MatchingEngine` code path; only the execution-fill
source differs. The `PoolMatcher` Protocol is the seam — `quote()` is read-only and identical in both modes; `apply()`
differs:

- **Batch / backtest replay mode**: `apply()` advances the pool's in-memory snapshot (reserves / tick / sqrtPrice / D),
  emits a synthetic `FillResult` keyed to the replay block. Strategy P&L backtest = sum of synthetic fills against
  historical position snapshots.
- **Live mode**: `apply()` is a thin wrapper that submits the swap tx to the execution venue (Uniswap `SwapRouter02` /
  Aave `Pool.supply()` / Curve metapool router / etc.) and reconstructs `FillResult` from the resulting on-chain
  transaction receipt + emitted `Swap` event. **Critical**: the pool snapshot is refreshed from the chain AFTER the tx
  confirms (or from a Tenderly fork pre-flight if the tx is queued but not yet broadcast).
- **Execution-alpha measurement** (CLAUDE.md "Batch = Live" sub-rule): live fills P&L − simulated fills P&L (where
  simulated runs the SAME `PoolMatcher.quote()` against the SAME pool snapshot at the same block).

End-to-end flow (both modes):

```
                          Strategy intent (SwapIntent: pool_address, amount, side, max_slippage_bps)
                                                  │
                                                  ▼
                                    +─────────────────────────+
                                    │ MatchingEngine          │   engine.py:562
                                    │  - book_type lookup     │
                                    │  - per-pool matcher fn  │
                                    +─────────────────────────+
                                                  │
                                                  ▼
                                    +─────────────────────────+
                                    │ AMMMatcher              │   engine.py:433
                                    │  - PoolShape dispatch   │   (Phase 2A refactor)
                                    │  - pool_from_address    │
                                    +─────────────────────────+
                                                  │
                                                  ▼
            +───────────────────────────────────────────────────────────────────+
            │ PoolMatcher Protocol (Phase 2A; implementers per pool_shape)      │
            │  .quote(amount_in, side) → SwapQuote                              │
            │  .apply(amount_in, side) → FillResult     ← differs batch vs live │
            │  .spot_price() / .snapshot()                                      │
            +───────────────────────────────────────────────────────────────────+
                                                  │
                          ┌───────────────────────┴────────────────────────┐
                          ▼                                                ▼
        +───────────────────────────────+                  +───────────────────────────────+
        │ BATCH                         │                  │ LIVE                          │
        │ apply() mutates in-memory     │                  │ apply() submits tx to venue   │
        │   pool snapshot               │                  │   reconstructs FillResult     │
        │ FillResult.filled_at_block =  │                  │   from on-chain tx receipt    │
        │   replay block                │                  │ FillResult.filled_at_block =  │
        │                               │                  │   confirmed block             │
        +───────────────────────────────+                  +───────────────────────────────+
                          │                                                │
                          └───────────────────────┬────────────────────────┘
                                                  ▼
                                    +─────────────────────────+
                                    │ position-balance-monitor│   (position-balance-monitor-service)
                                    │  - apply FillResult     │
                                    │  - update positions     │
                                    +─────────────────────────+
                                                  │
                                                  ▼
                                       Strategy P&L attribution
                                       (execution alpha = live − sim)
```

**Slippage tolerance gate**: `_amm_match_impl` calls `.quote()` first; if
`|quote.amount_out − strategy.min_amount_out| / strategy.min_amount_out > strategy.max_slippage_bps`, returns
`MatchResult(failed=True, reason="SLIPPAGE_EXCEEDED")`. **Quote vs fill realized-slippage** is captured in
`FillResult.realized_slippage_vs_quote_bps` — a non-trivial value here is the matcher-realism signal.

**Pre-flight Tenderly fork check** (live mode, pre-broadcast): for high-impact swaps (size > N% of pool TVL), the live
`apply()` MAY run a Tenderly-fork pre-flight `.quote()` against the upstream RPC state before broadcasting — protects
against pool-state drift between strategy decision and tx inclusion. Out-of-scope for Day-1; deferred to Phase 4
implementation (originally plan body Phase 4 was governance sim — clarification needed; this matching-engine integration
spec is separate).

### Cross-service contracts (downstream consumer SSOTs)

- **position-balance-monitor-service** (`position_balance_monitor/__init__.py`): consumes `FillResult` via bus
  subscription. Position update logic must handle: (a) successful fill → reduce intent + add to filled positions; (b)
  partial fill → split intent; (c) failed fill → log + emit `FILL_FAILED` event for strategy-service replay.
- **strategy-service** (`strategy_service/engine/`): drives backtest replay by iterating historical `SwapIntent`
  events + dispatching to `MatchingEngine`. Live mode subscribes to strategy-decision-bus + dispatches identically.
  Execution-alpha attribution = batch P&L (sim fills) vs live P&L (real fills) on the same historical-or-paper-trade
  window.
- **risk-and-exposure-service**: consumes `FillResult` for position-limit / VaR / leverage checks. Reads
  `PoolMatcher.snapshot()` for forward-impact projection (what if strategy wants to scale up?).

## Aggregator / multi-hop routing realism (Day-1 slot 6 design ship 2026-05-11; supersedes section #9 stub)

Aggregator pool shapes (`JUPITER_ROUTE_AGGREGATOR`, `1INCH_AGGREGATOR`, `0X_AGGREGATOR`) are NOT single-pool matchers —
they are **route composers** that route a single user-facing swap across N legs of underlying AMMs. Phase 2G
implementation must handle:

**Route-source by mode**:

- **Live mode**: fetch route from aggregator quote API (`POST jup.ag/quote` / `1inch.io/v4.0/{chain}/quote` /
  `api.0x.org/swap/v1/quote`) at strategy-decision time. Route is a JSON object listing per-leg pool addresses + per-leg
  input share + expected per-leg amount_out + slippage cost. Returned route is ephemeral — quote expires after ~5-15
  seconds; matcher must re-fetch on stale-quote rejection.
- **Batch mode**: replay needs historical routes. Aggregator quote APIs do NOT serve historical routes — workaround:
  capture aggregator routes at decision time + persist per-route JSON to MTDS data_type `aggregator_route` (NEW; not yet
  in catalogue). Backtest replay reconstructs per-leg state from MTDS per-pool captures + replays the captured route,
  NOT the route the aggregator would have chosen at replay-block (route choice is path-dependent on liquidity that's
  already been consumed — would be a lookahead bias).

**Per-leg dispatch**: for each leg in the route, the `AggregatorRouteMatcher` looks up the underlying-pool `PoolMatcher`
from the leg's pool address + `PoolShape` lookup table (`(chain, pool_address) → PoolShape`; sourced from MTDS
`dex_pools` data_type), calls `.quote(leg_amount_in, leg_side)`, and sums per-leg outputs:

```python
def aggregator_quote(route, amount_in):
    amount_in_remaining = amount_in
    amount_out_total = Decimal("0")
    legs_quote: list[SwapQuote] = []
    for leg in route.legs:
        leg_amount_in = amount_in_remaining * Decimal(leg.input_share)
        leg_pool = pool_registry.get_pool_matcher(leg.chain, leg.pool_address)
        leg_quote = leg_pool.quote(leg_amount_in, leg.side)
        legs_quote.append(leg_quote)
        amount_in_remaining -= leg_amount_in
        amount_out_total += leg_quote.amount_out
    return SwapQuote(
        amount_out=amount_out_total,
        fee_amount=sum(q.fee_amount for q in legs_quote),
        price_impact_bps=composite_price_impact(legs_quote),
        legs=legs_quote,
    )
```

**MEV considerations** (live mode): aggregator routes are **MEV-prone**. Front-running risk = high (bot sees your tx in
mempool + sandwiches with bigger size on the same route legs). Mitigation: use private mempool (Flashbots Protect /
MEV-Blocker) or private order flow (Cowswap / 1inch Fusion). The `FillResult` should record
`mempool_path: PUBLIC | PRIVATE` so execution-alpha attribution can separate "lost to public mempool MEV" from "lost to
genuine slippage."

**Slippage composition**: per-leg fees + per-leg price-impact compound multiplicatively, not additively, for multi-hop.
A 30-bp leg fee × 3 hops = 90 bps fee (additive) but the per-hop price impact compounds on a non-linear curve. For
backtest realism, use the composite price-impact formula:

```
composite_fill = leg_1_amount_out * leg_2_amount_in_share * ... * leg_N_amount_in_share
```

Each per-leg `amount_in_share` is the strategy's chosen split; aggregator-API returns the optimal split.

**Validation threshold**: ≥ 30 historical Jupiter routes within 10 bps composite fill (looser than per-pool ≤5 bps
because multi-hop variance is inherent — different routes can be near-optimal). Per `defi_master` plan, aggregator
captures land via Phase 2G MTDS adapter (NEW; not yet shipped).

## Lending rate-impact-from-own-trade

When we supply $X USDC to Aave, utilization moves, rates compress, our yield drops. Rate-impact calculator
(`defi_simulation_realism` Phase 3A):

```python
def post_trade_rate(state: LendingMarketState, supply_delta: Decimal, borrow_delta: Decimal) -> tuple[Decimal, Decimal]:
    new_total_supply = state.total_supply + supply_delta
    new_total_borrow = state.total_borrow + borrow_delta
    new_utilization = new_total_borrow / new_total_supply

    if new_utilization < state.optimal_utilization_rate:
        # Below kink — linear in slope1
        borrow_apy = state.irm_base + state.irm_slope1 * new_utilization / state.optimal_utilization_rate
    else:
        # Above kink — slope1 + slope2 jump
        excess = new_utilization - state.optimal_utilization_rate
        borrow_apy = state.irm_base + state.irm_slope1 + state.irm_slope2 * excess / (1 - state.optimal_utilization_rate)

    supply_apy = borrow_apy * new_utilization * (1 - state.reserve_factor)
    return supply_apy, borrow_apy
```

**Inputs** (from MTDS captures via `defi_simulation_realism` Phase 1B `LendingMarketState`): `total_supply`,
`total_borrow`, `optimal_utilization_rate`, `irm_base`, `irm_slope1`, `irm_slope2`, `reserve_factor`, `liquidityIndex`,
`variableBorrowIndex`. **Validation**: replay ≥ 50 historical large-supply events; ≥ 90% within 10bps APY tolerance.

`BenchmarkMatcher` extension (Phase 3B): all supply/borrow/repay/withdraw at Aave V3 + Compound V3 + Spark + Radiant
call this calculator. Backtest yield uses post-trade rate.

### Per-protocol IRM parameter capture (Day-1 slot 6 design ship 2026-05-12; operator-runnable for Harsh slot 4)

> **⚠️ CRITICAL — Phase 1B IRM-slope capture gap (2026-05-12)**: pre-fix the Aave V3 lending-indices MTDS adapter at
> `aave_lending.py` was DROPPING the per-block `optimalUtilisationRate` + `variableRateSlope1` + `variableRateSlope2`
> fields it fetched from The Graph subgraph (line 77-79). Consumers fell back to the static
> `AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET` snapshot ("governance current as of 2026-05-05") — mis-pricing post-trade rates
> by 10-30 bps on the wing of the kink. **Fixed at mtds@`4b38a9b` + uac@`bd9c202` + features-service@`e292a4d4`**; see
> `plans/active/issues/aave_irm_slope_capture_dropped_2026_05_12.md` for full remediation path. **Backfill VM (Step 3 of
> issue doc) must land before Phase 8A/B carry-archetype + leveraged-funding-arb 1-year replay runs** — otherwise the
> replays use the proxy snapshot and the resulting P&L delta is uninterpretable. **Tenderly fork live-vs-sim recon
> (Phase 8C) WILL mask this drift** — Tenderly forks current chain state which holds today's slopes; the drift only
> surfaces during historical-replay 8A/8B where the matcher uses today's slopes against historical pool reserves.

Per-protocol IRM parameter source for Phase 3A `LendingMarketState` capture by MTDS adapter
`market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/lending_indices.py`:

| Protocol        | Chain                                            | Pool/Comet address                                                                                                         | IRM getter                                                                                                                                                                                        | Reserve config getter                                                                                                                                | Capture cadence                                                |
| --------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Aave V3**     | Ethereum                                         | `PoolAddressesProvider` `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e` → `Pool` `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` | `DefaultReserveInterestRateStrategyV2.getInterestRateData(asset)` — returns `baseVariableBorrowRate`, `variableRateSlope1`, `variableRateSlope2`, `optimalUsageRatio`                             | `Pool.getReserveData(asset)` — returns `liquidityIndex`, `variableBorrowIndex`, `currentVariableBorrowRate`, `currentLiquidityRate`, `aTokenAddress` | Per-block (12s slot) for active markets; per-hour for inactive |
| **Aave V3**     | Arbitrum / Optimism / Polygon / Base / Avalanche | Per-chain Pool address — see UAC `CHAIN_PROTOCOL_DEPLOYMENTS`                                                              | Same `DefaultReserveInterestRateStrategyV2` ABI                                                                                                                                                   | Same `Pool.getReserveData` ABI                                                                                                                       | Per-chain block time                                           |
| **Compound V3** | Ethereum                                         | `Comet` per market (e.g. cUSDCv3 `0xc3d688B66703497DAA19211EEdff47f25384cdc3`)                                             | `Comet.getUtilization()` + `Comet.getBorrowRate(utilization)` + `Comet.getSupplyRate(utilization)` (single-asset borrow model — DIFFERENT shape from Aave's kinked-slope)                         | `Comet.getAssetInfo(i)` for each collateral; `Comet.totalSupply()` / `Comet.totalBorrow()`                                                           | Per-block                                                      |
| **Compound V3** | Arbitrum / Polygon / Base                        | Per-chain Comet markets                                                                                                    | Same Comet ABI                                                                                                                                                                                    | Same                                                                                                                                                 | Per-chain block time                                           |
| **Spark**       | Ethereum                                         | `SparkPool` `0xC13e21B648A5Ee794902342038FF3aDAB66BE987` (Aave-V3-fork)                                                    | Same Aave V3 IRM ABI                                                                                                                                                                              | Same Aave V3 ABI                                                                                                                                     | Per-block                                                      |
| **Spark**       | Gnosis                                           | `SparkPool` Gnosis address                                                                                                 | Same ABI                                                                                                                                                                                          | Same                                                                                                                                                 | Per-block (~5s)                                                |
| **Radiant**     | BSC / Arbitrum                                   | Radiant V2 LendingPool addresses (Aave V2 fork — different ABI from V3)                                                    | `LendingPool.getReserveData(asset)` returns legacy V2 struct with `currentLiquidityRate`, `currentVariableBorrowRate`, IRM params accessed via separate `InterestRateStrategy` contract per-asset | Same V2-shape getter                                                                                                                                 | Per-block                                                      |

**Compound V3 IRM is NOT kinked-slope** — uses a separate `kink` parameter where below-kink rate is linear in
utilization, above-kink rate jumps to a different linear slope (different shape from Aave's piecewise). Matcher must
dispatch by `(protocol, asset)` and use protocol-specific IRM formula:

```python
# execution-service/execution_service/matching_engine/lending/rate_impact.py (NEW Phase 3A)
def post_trade_rate(
    state: LendingMarketState,
    supply_delta: Decimal,
    borrow_delta: Decimal,
) -> tuple[Decimal, Decimal]:
    new_total_supply = state.total_supply + supply_delta
    new_total_borrow = state.total_borrow + borrow_delta
    new_utilization = new_total_borrow / new_total_supply if new_total_supply > 0 else Decimal("0")
    if state.protocol_irm_shape == "AAVE_KINKED":
        # Aave V3 + Spark + Radiant — piecewise linear
        if new_utilization < state.optimal_utilization_rate:
            borrow_apy = state.irm_base + state.irm_slope1 * new_utilization / state.optimal_utilization_rate
        else:
            excess = new_utilization - state.optimal_utilization_rate
            borrow_apy = state.irm_base + state.irm_slope1 + state.irm_slope2 * excess / (Decimal("1") - state.optimal_utilization_rate)
    elif state.protocol_irm_shape == "COMPOUND_V3":
        # Comet — single-asset base + below/above-kink slope
        if new_utilization <= state.compound_kink:
            borrow_apy = state.compound_base_rate + state.compound_below_kink_slope * new_utilization
        else:
            borrow_apy = (
                state.compound_base_rate
                + state.compound_below_kink_slope * state.compound_kink
                + state.compound_above_kink_slope * (new_utilization - state.compound_kink)
            )
    else:
        raise UnknownIRMShapeError(state.protocol_irm_shape)
    supply_apy = borrow_apy * new_utilization * (Decimal("1") - state.reserve_factor)
    return supply_apy, borrow_apy
```

UAC `LendingMarketState` schema (Phase 1B) extends with discriminator field
`protocol_irm_shape: Literal["AAVE_KINKED", "COMPOUND_V3", "MORPHO_ADAPTIVE"]` (future Morpho support) +
Compound-specific fields `compound_kink`, `compound_base_rate`, `compound_below_kink_slope`,
`compound_above_kink_slope`.

### Phase 3C validation harness (operator-runnable for Harsh slot 4)

Replay 1 month of historical large-supply events; compare simulated post-trade rate vs realized on-chain rate.

```python
# execution-service/tests/integration/test_lending_rate_impact_validation.py (NEW Phase 3C)
@pytest.mark.parametrize("protocol", ["aave_v3_ethereum", "aave_v3_arbitrum", "compound_v3_ethereum", "spark_ethereum"])
def test_post_trade_rate_within_tolerance(protocol: str) -> None:
    events = mtds.read_large_supply_events(
        protocol=protocol,
        min_supply_usd=Decimal("10_000_000"),
        lookback_days=30,
    )
    for event in events:
        state = mtds.read_lending_market_state(protocol, event.asset, event.block_number - 1)
        simulated_supply_apy, simulated_borrow_apy = post_trade_rate(
            state, supply_delta=event.amount_usd, borrow_delta=Decimal("0"),
        )
        realized_state_post = mtds.read_lending_market_state(protocol, event.asset, event.block_number)
        delta_supply_bps = abs(simulated_supply_apy - realized_state_post.current_liquidity_rate) * Decimal("10000")
        delta_borrow_bps = abs(simulated_borrow_apy - realized_state_post.current_variable_borrow_rate) * Decimal("10000")
        # Acceptance: ≥ 90% within 10 bps absolute APY delta
        if delta_supply_bps > Decimal("10") or delta_borrow_bps > Decimal("10"):
            failures.append((protocol, event.tx_hash, delta_supply_bps, delta_borrow_bps))
    assert len(failures) / len(events) < Decimal("0.1"), failures
```

**Large-supply event source** (`mtds.read_large_supply_events`): on-chain `Supply` event topic filter on Aave V3 Pool /
Compound V3 Comet — captured by MTDS `lending_events` data_type (NEW; not yet in catalogue; gap captured in
`defi_simulation_realism_2026_05_10.md` DONE block discoveries section). Backfill: 30-day rolling window across 6
protocol-chain combos = ~200-500 events/window.

## Governance proposal simulation harness

Capture (`defi_simulation_realism` Phase 4A): on-chain Governor events + Snapshot off-chain proposals API for Aave V3 +
Compound V3 + Spark + Lido.

Simulator (Phase 4B): given proposal ID + Tenderly fork:

1. Apply `governor.execute(proposal_id)` on the fork (advances to executed state).
2. Read affected parameters (`getReserveData(asset)` for Aave, etc.) from fork before + after.
3. Output: per-affected-instrument before/after parameter delta.

CLI (Phase 4C): `defi-simulate-proposal --proposal-id <id> --archetype <X> --time T` returns archetype P&L delta if
proposal executes at time T. Used by risk simulations sibling.

**Inputs**: `GovernanceProposal` schema (`defi_simulation_realism` Phase 1C). **Validation**: ≥ 5 historical proposals'
P&L delta within 100bps of actual realized post-execution delta.

### Per-protocol capture detail (Day-1 slot 6 design ship 2026-05-11; operator-runnable for Harsh slot 4)

Per-protocol Governor contract addresses + data sources for Phase 4A adapter:

| Protocol        | Chain    | Governor address                                                                   | Snapshot space      | Subgraph (preferred)                                                  | Capture method                                                                                                                                    |
| --------------- | -------- | ---------------------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Aave V3**     | Ethereum | `GovernanceV3Ethereum` `0x9AEE0B04504CeF83A65AC3f0e838D0593BCb2BC7`                | `aave.eth`          | `https://api.thegraph.com/subgraphs/name/aave/governance-v2`          | On-chain `ProposalCreated` / `ProposalExecuted` events via subgraph + Snapshot REST API for off-chain temperature checks (`hub.snapshot.org/api`) |
| **Compound V3** | Ethereum | `GovernorBravoDelegator` `0xc0Da02939E1441F497fd74F78cE7Decb17B66529`              | `comp-vote.eth`     | `https://api.thegraph.com/subgraphs/name/arr00/compound-governance-2` | Same shape; `GovernorBravo` event ABI                                                                                                             |
| **Spark**       | Ethereum | `MakerDAO`-style ChiefBoot delegation `0x0a3f6849f78076aefaDf113F5BED87720274dDC0` | `spark.eth`         | `https://api.thegraph.com/subgraphs/name/makerdao/governance`         | Spark proposals execute through MakerDAO's chief; capture via MakerDAO subgraph + filter for Spark-asset-list proposals                           |
| **Lido**        | Ethereum | `AragonVoting` `0x2e59A20f205bB85a89C53f1936454680651E618e`                        | `lido-snapshot.eth` | `https://api.thegraph.com/subgraphs/name/lidofinance/lido`            | Aragon-style voting events; LDO-token weighted; Snapshot dominates pre-execution signalling                                                       |

**Subgraph schema** for each: `id`, `proposer`, `createdAt`, `votingStartTime`, `votingEndTime`, `executedAt`
(nullable), `status`, `payload_targets[]`, `payload_calldatas[]`. Adapter parses into UAC `GovernanceProposal` schema
(Phase 1C). Capture cadence: 5-minute poll while voting active; 1-hour poll when no active proposals.

### Tenderly fork simulator detail (Phase 4B operator-runnable)

```python
# execution-service/execution_service/governance/proposal_simulator.py (NEW Phase 4B)
def simulate_proposal_execution(
    proposal: GovernanceProposal,
    fork_block: int,
    affected_assets: list[str],
) -> dict[str, ParameterDelta]:
    """Run governor.execute(proposalId) on a Tenderly fork pinned at fork_block.

    Returns per-asset before/after parameter delta. Tenderly API:
      POST tenderly.co/api/v1/account/{user}/project/{proj}/fork
        body: {"network_id": "1", "block_number": fork_block}
      POST .../fork/{fork_id}/simulate
        body: {"network_id": "1", "from": <governor>, "to": <governor>,
               "input": <encoded executeProposal calldata>}
    """
    fork_id = tenderly.create_fork(chain_id=1, block_number=fork_block)
    # Snapshot baseline params
    before = {asset: read_asset_params(fork_id, asset) for asset in affected_assets}
    # Execute proposal payload
    tenderly.simulate(
        fork_id=fork_id,
        from_=proposal.executor_address,
        to=proposal.governor_address,
        input=encode_execute_call(proposal.proposal_id),
    )
    after = {asset: read_asset_params(fork_id, asset) for asset in affected_assets}
    return {
        asset: ParameterDelta(before=before[asset], after=after[asset])
        for asset in affected_assets
    }
```

`read_asset_params(fork_id, asset)` calls protocol-specific getters: Aave V3 = `Pool.getReserveData(asset)`

- `Pool.getConfiguration(asset)` + `AaveOracle.getAssetPrice(asset)`; Compound V3 = `Comet.getAssetInfo()`
- `Comet.baseTrackingSupplyIndex`; Spark = `SparkPool.getReserveData(asset)`. Tenderly fork budget constraint: ~10
  sims/day per `defi_simulation_realism` risk register row.

### CLI signature (Phase 4C operator-runnable)

```bash
# Returns archetype P&L delta if proposal executes at time T
defi-simulate-proposal \
  --proposal-id 0x<32-byte-hex-id> \
  --protocol aave_v3|compound_v3|spark|lido \
  --archetype carry_staked_basis|leveraged_funding_arb \
  --time-T 2026-05-15T12:00:00Z \
  --fork-block 22500000

# Returns JSON:
# {
#   "archetype": "carry_staked_basis",
#   "proposal_id": "0x...",
#   "parameter_deltas": [{"asset": "USDC", "before": {...}, "after": {...}}, ...],
#   "expected_pnl_delta_bps": -45,   # negative = archetype P&L worsens by 45bps
#   "confidence_interval_bps": [-60, -30],
#   "validation_status": "calibrated"  # if proposal already executed historically
# }
```

CLI lives in `execution-service/execution_service/cli/simulate_proposal.py` (NEW Phase 4C); wired into
`execution-service`'s service CLI per `/codex/06-coding-standards/cli-convention.md`
(`--operation simulate-proposal --mode batch --asset-group defi`). Used by
`risk_simulations_limits_alerting_2026_05_10.md` sibling for governance-axis scenario coverage.

### Backfill historical proposals (Phase 4D operator-runnable)

Two-year backfill across 4 protocols using subgraph paginated queries. Per protocol:

```python
# instruments-service or backfill VM under deployment-service/scripts/vm/
def backfill_governance_proposals(
    protocol: Literal["aave_v3", "compound_v3", "spark", "lido"],
    from_date: date = date(2024, 5, 1),
    to_date: date = date(2026, 5, 11),
) -> None:
    subgraph_url = PROTOCOL_SUBGRAPH_MAP[protocol]
    cursor = None
    while True:
        page = subgraph_paginated_query(subgraph_url, cursor, batch_size=100)
        proposals = parse_to_uac_governance_proposal(page, protocol)
        manifest_writer.record_captured(
            data_type="governance_proposals",
            asset_group="defi",
            venue=protocol.upper(),
            rows=proposals,
            shard_atom=("defi", protocol),  # SSOT per writegate plan Phase 1A
        )
        if not page.has_next: break
        cursor = page.cursor
```

VM launch: `deployment-service/scripts/vm/launch-governance-backfill-vm.sh aave_v3` (NEW; needs watchdog dict entry
`governance-backfill-` + tarball refresh per CLAUDE.md VM Naming Convention HARD RULE). Expected output: ~500-1500
proposals/protocol/year × 4 protocols × 2 years = ~4k-12k rows. Per-VM shard isolation mandatory (`VM_NAME` +
`MANIFEST_PER_VM_SHARDS=true`).

## Staking + restaking yield-stream simulators

### Native staking (Phase 5A)

Per-chain stochastic model:

- **Ethereum beacon**: per-epoch reward distribution = consensus reward + execution layer (block-builder tip).
  Historical 6+ months from `staking_yields` data_type. Forward distribution = 5-day rolling mean ± 2 stddev band per
  epoch + churn-adjusted (validator entry/exit queue length feeds attestation efficiency).
- **Solana validator**: per-validator-epoch reward = base inflation + transaction fees + MEV (validator-tip share).
  Historical from `staking_yields` data_type. Forward distribution similar.

### Restaking AVS (Phase 5B)

Per-AVS reward variability layered on top of native staking base. EigenLayer + Symbiotic + Karak + Jito-restaking AVSes
from Phase 1A captures (`restaking_rewards` data_type). Per-LRT forward distribution: composite of native + AVS rewards
weighted by operator allocation share.

### LRT protocol-fee (Phase 5C)

Discrete-event model — Ether.fi / Renzo / KelpDAO / Puffer fees historically change ~quarterly via governance. Capture
`governance_proposals` for fee-change events; forward fee assumption = most-recent-quarter fee + ±1 stddev band per
protocol.

### Seasonal-points (Phase 5D)

Off-chain reward model. Operator supplies "expected season ending in" date + airdrop-equivalent ratio (historical
points-to-token redemption ratios; tunable). Treats points as discounted forward-airdrop at season end.

### Composite (Phase 5E)

`StakingYieldStreamSimulator(lst_or_lrt, horizon)` returns forward-yield distribution combining all 4 layers:

```python
distribution = (
    native_staking_yield(chain, horizon)
    + restaking_avs_yield(protocol, horizon)
    - lrt_protocol_fee(protocol, horizon)
    + seasonal_points_implied_yield(protocol, horizon)
)
```

Used by `carry_staked_basis` PnL projection + risk simulations.

**Validation**: walk-forward 6+ months calibration; per-period error within 50bps APY.

### Per-protocol capture detail (Day-1 slot 6 design ship 2026-05-11; operator-runnable for Harsh slot 4)

Native staking + restaking yield streams — per-protocol data sources for `staking_yields` / `restaking_rewards` /
`lrt_protocol_fee_history` data_types under
`market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/`:

| Protocol / source            | Data_type                                     | Endpoint / SDK                                                                                                                                                        | Per-period grain                  | Capture cadence                    |
| ---------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ---------------------------------- |
| **Ethereum beacon**          | `staking_yields`                              | Lighthouse / Prysm REST `https://beacon-mainnet.{provider}.com/eth/v1/validator/duties/attester/{epoch}` + `/beacon/rewards/blocks/{block_root}`                      | Per-epoch (32 slots, ~6.4 min)    | Every epoch via WS subscription    |
| **Ethereum execution layer** | `staking_yields` (execution_rewards subfield) | `eth_getBlockByNumber` + decode block.baseFeePerGas + block.transactions.priorityFee                                                                                  | Per-block                         | Every 12-second slot via WS        |
| **Solana validator**         | `staking_yields`                              | Solana RPC `getInflationReward` + Validator Info program                                                                                                              | Per-epoch (432k slots, ~2-3 days) | Once per epoch (post-finalization) |
| **EigenLayer AVS rewards**   | `restaking_rewards`                           | Subgraph `https://api.thegraph.com/subgraphs/name/eigen-labs/eigenlayer-rewards-mainnet` + `RewardsCoordinator` contract `0x7750d328b314EfFa365A0402CcfD489B80B0adda` | Per-`rewardsSubmitted` event      | 5-minute poll                      |
| **Symbiotic**                | `restaking_rewards`                           | Subgraph `https://api.studio.thegraph.com/query/symbiotic/symbiotic-mainnet`                                                                                          | Per-`RewardClaimed` event         | 5-minute poll                      |
| **Karak**                    | `restaking_rewards`                           | Subgraph `https://api.thegraph.com/subgraphs/name/karak-network/karak-mainnet`                                                                                        | Per-reward-distribution event     | 5-minute poll                      |
| **Jito (Solana restaking)**  | `restaking_rewards`                           | Jito API `https://kobe.mainnet.jito.network/api/v1/validators` + on-chain `jitoSOL` stake pool                                                                        | Per-epoch                         | Once per epoch                     |
| **Ether.fi LRT fee**         | `lrt_protocol_fee_history`                    | Etherfi `LiquidityPool` `0x308861A430be4cce5502d0A12724771Fc6DaF216` `setProtocolFee` event                                                                           | Per-governance-change             | Subgraph poll on governance state  |
| **Renzo LRT fee**            | `lrt_protocol_fee_history`                    | Renzo `RestakeManager` `0x74a09653A083691711cF8215a6ab074BB4e99ef5` fee getter                                                                                        | Per-governance-change             | Subgraph poll on governance state  |
| **KelpDAO LRT fee**          | `lrt_protocol_fee_history`                    | KelpDAO `LRTConfig` `0x947Cb49334e6571ccBFEF1f1f1178d8469D65ec7`                                                                                                      | Per-governance-change             | Subgraph poll on governance state  |
| **Puffer LRT fee**           | `lrt_protocol_fee_history`                    | Puffer `PufferVaultV2` `0xD9A442856C234a39a81a089C06451EBAa4306a72`                                                                                                   | Per-governance-change             | Subgraph poll on governance state  |

**Native staking stochastic model** (`StakingYieldSimulator.calibrate_and_sample(chain, horizon_epochs)`):

```python
# execution-service/execution_service/yield_streams/native_staking.py (NEW Phase 5A)
def calibrate_native_staking(chain: Literal["ethereum", "solana"]) -> StakingYieldModel:
    history = mtds.read_staking_yields(chain, lookback_days=180)  # 6+ months
    epoch_rewards = history.groupby("epoch")["reward_per_validator"].sum()
    # Heteroskedasticity around validator-set churn — bin by attestation_efficiency
    bins = pd.qcut(history["attestation_efficiency"], q=5)
    per_bin_mean = epoch_rewards.groupby(bins).mean()
    per_bin_std = epoch_rewards.groupby(bins).std()
    return StakingYieldModel(per_bin_mean=per_bin_mean, per_bin_std=per_bin_std, chain=chain)

def sample_forward_distribution(
    model: StakingYieldModel,
    horizon_epochs: int,
    current_attestation_efficiency: float,
) -> ForwardYieldDistribution:
    bin_idx = bisect(model.per_bin_mean.index, current_attestation_efficiency)
    mean = model.per_bin_mean.iloc[bin_idx]
    std = model.per_bin_std.iloc[bin_idx]
    samples = np.random.normal(mean, std, size=(10_000, horizon_epochs)).sum(axis=1)
    return ForwardYieldDistribution(
        mean=samples.mean(),
        p5=np.percentile(samples, 5),
        p95=np.percentile(samples, 95),
    )
```

**Restaking AVS model** (`RestakingAVSModel.sample(protocol, lst, horizon)`): per-AVS reward variability is generally
higher than native staking (smaller AVS operator set, more concentrated reward distribution). Model as **base + AVS
premium** where base = native staking yield distribution + AVS premium ~ `LogNormal(μ_avs, σ_avs)` calibrated from
`restaking_rewards` data_type. Per-LRT forward yield = base + weighted-sum-of-AVS-premia where weights = LRT's operator
allocation shares.

**LRT protocol-fee discrete-event model** (`LRTProtocolFeeModel.sample(protocol, horizon)`): fees change ~quarterly via
governance. State = `most_recent_quarter_fee_bps + std_band(historical_changes)`. Forward sample =
`current_fee_bps + N(0, σ_quarterly)` capped at `[0, max_observed_fee_bps × 1.5]`.

**Seasonal-points discount factor** (operator-tuned per-protocol):

- Ether.fi loyalty points → ETHFI airdrop (2024-03): redemption ratio ~0.001 ETHFI / point at launch; 60% discount
  applied.
- Renzo ezPoints → REZ airdrop (2024-04): similar ~0.0008 REZ / point; 50% discount applied.
- Puffer carrot points → PUFFER airdrop (2024-10): ~0.0006 PUFFER / point; 50% discount applied.
- New programs (KelpDAO Kelp Miles, Karak XP) — operator-tunable; default 70% discount on first calibration.

Discount factor accounts for: token-launch volatility, vesting cliffs, illiquidity-at-redemption, market sell-pressure
at airdrop. Operator updates the per-protocol ratio quarterly via `config_reloaders.py` reload of
`defi_seasonal_points_calibration.yaml`.

**Composite simulator integration** (Phase 5E):

```python
# execution-service/execution_service/yield_streams/composite_simulator.py (NEW Phase 5E)
def staking_yield_stream_distribution(
    lst_or_lrt: str,                # e.g., "weETH", "ezETH", "jitoSOL"
    chain: Literal["ethereum", "solana"],
    horizon_epochs: int,
) -> ForwardYieldDistribution:
    protocol = LST_TO_PROTOCOL[lst_or_lrt]
    base = sample_forward_distribution(
        model=NATIVE_STAKING_MODELS[chain],
        horizon_epochs=horizon_epochs,
        current_attestation_efficiency=mtds.current_attestation_efficiency(chain),
    )
    avs_premium = RESTAKING_AVS_MODEL.sample(protocol, lst_or_lrt, horizon_epochs)
    fee = LRT_PROTOCOL_FEE_MODEL.sample(protocol, horizon_epochs)
    points = SEASONAL_POINTS_MODEL.sample(protocol, lst_or_lrt, horizon_epochs)
    # Composite distribution: convolve all 4 layers
    return convolve_distributions([base, avs_premium, -fee, points])
```

Used by `carry_staked_basis` archetype config (per-LST forward yield) + `leveraged_funding_arb` (debt cost vs LST yield
differential) + `risk_simulations_limits_alerting` sibling.

## Slashing tail-risk Monte Carlo

Per-chain calibration (Phase 7A): from `slashing_events` data_type captures.

- **Ethereum beacon**: per-validator-epoch slashing probability ≈ 0.01-0.05 bp historical baseline; spikes during fork
  events / client bugs. Heavy-tailed distribution.
- **Solana validator**: per-validator-day slashing probability higher base rate (~0.5-1 bp), distinct shape (per-
  validator-event vs per-validator-epoch).

MC simulator (Phase 7B): `SlashingTailRiskMC(allocation, horizon)`:

1. Sample N=10000 paths from per-validator slashing distribution.
2. Per path, compute expected slashing loss given allocation × N validators.
3. Output P(slashing > threshold) curve.

Carry archetype hook (Phase 7C): output P(slashing) feeds into capital-allocation rule. Cap per-LST exposure when
historical slashing rate spikes; back off when normal.

### Per-chain slashing event capture (Day-1 slot 6 design ship 2026-05-12; operator-runnable for Harsh slot 4)

Per-chain `slashing_events` data_type source — Phase 7A capture for MTDS adapter
`market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/slashing_events.py`:

| Chain                              | Source / endpoint                                                                                                                                      | Per-event grain      | Historical depth                                                                             | Capture cadence                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Ethereum beacon**                | Lighthouse/Prysm REST `/eth/v1/beacon/pool/attester_slashings` + `/eth/v1/beacon/pool/proposer_slashings` + block-body parsing for slashing operations | Per-slot (every 12s) | Genesis 2020-12-01 → now (~5.5 years; ~1.5M slashings catalogued via beaconcha.in cross-ref) | WS subscription to head + epoch-finalization replay                               |
| **Ethereum beacon** (historical)   | beaconcha.in REST `https://beaconcha.in/api/v1/slashings` (rate-limited; 10 req/sec free tier)                                                         | Per-slashing event   | Same                                                                                         | One-shot historical backfill via paginated API; ongoing capture via Lighthouse WS |
| **Solana validator**               | Solana RPC `getSlashingHistory` (Anza Solana 1.18+) + Validator Info program account scan                                                              | Per-validator-event  | Genesis 2020-03 → now; per-epoch grain (~2-3 days)                                           | Once per epoch (post-finalization); replay from epoch 0 for historical            |
| **Solana validator (cross-check)** | Solana Beach API `https://api.solanabeach.io/v1/validators/slashing` (rate-limited; needs API key)                                                     | Per-event            | Same                                                                                         | Cross-validation against on-chain getSlashingHistory                              |

UAC `SlashingEvent` schema (Phase 1E) fields: `chain`, `validator_id`, `slashed_at_epoch`, `slashed_at_slot` (ETH-only),
`slashed_amount_native`, `slashing_reason` (Ethereum: `proposer_slashing` / `attester_slashing` / `surround_vote` /
`double_propose`; Solana: `downtime` / `double_sign` / `network_partition`), `slasher_validator_id` (ETH-only — who
reported), `evidence_block_hash`.

### Phase 7B MC simulator architecture (operator-runnable)

```python
# execution-service/execution_service/risk/slashing_tail_risk_mc.py (NEW Phase 7B)
@dataclass
class SlashingTailRiskMC:
    """Monte Carlo simulator for carry archetype slashing tail-risk.

    Calibration: per-chain slashing rate histogram from `slashing_events` data_type.
    Simulation: N=10000 forward paths × archetype LST allocation × N_effective_validators.
    Output: P(loss > threshold) curve for risk dashboard + archetype capital-allocation gate.
    """

    chain: Literal["ethereum", "solana"]
    n_paths: int = 10_000
    horizon_epochs: int = 1170  # ~6 months Ethereum, ~3 months Solana

    def calibrate(self) -> SlashingDistribution:
        """Returns per-validator-epoch slashing probability + per-event severity distribution
        from historical `slashing_events` data_type."""
        events = mtds.read_slashing_events(chain=self.chain, lookback_days=365)
        # Probability bin: events per validator-epoch (Ethereum) or per validator-day (Solana).
        total_validator_epochs = mtds.cumulative_validator_epochs(self.chain, lookback_days=365)
        p_per_validator_epoch = Decimal(len(events)) / Decimal(total_validator_epochs)
        # Severity: native_token amount slashed per event (heavy-tailed; log-normal or empirical CDF).
        severities = [e.slashed_amount_native for e in events]
        return SlashingDistribution(
            p_per_validator_epoch=p_per_validator_epoch,
            severity_distribution=ECDF(severities),
            heavy_tail_alpha=fit_power_law_tail(severities),  # Hill estimator on top-quintile
        )

    def simulate_archetype_loss(
        self,
        allocation_native_units: Decimal,           # e.g., 1000 ETH staked
        effective_n_validators: int,                # = allocation / 32 ETH per validator
        distribution: SlashingDistribution,
    ) -> ProbabilityOfLossCurve:
        """For each MC path: sample slashing events over horizon, sum severity, compute loss fraction."""
        rng = np.random.default_rng(42)
        path_losses = np.zeros(self.n_paths)
        for i in range(self.n_paths):
            # Number of slashings on this path ~ Poisson(N_val * horizon_epochs * p_per_val_epoch).
            lam = float(effective_n_validators * self.horizon_epochs * distribution.p_per_validator_epoch)
            n_slashings = rng.poisson(lam)
            # Sample severity per slashing.
            severities = [distribution.severity_distribution.sample(rng) for _ in range(n_slashings)]
            path_losses[i] = sum(severities) / float(allocation_native_units)  # loss fraction
        return ProbabilityOfLossCurve(
            thresholds_pct=[0.01, 0.05, 0.10, 0.25, 0.50, 1.00, 2.50, 5.00, 10.00],
            p_loss_exceeds=np.percentile(path_losses, [99, 95, 90, 75, 50, 25, 10, 5, 1]).tolist(),
        )
```

### Phase 7C archetype capital-allocation hook (operator-runnable)

```python
# strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py — extend on_tick()
def _slashing_risk_gate(
    self,
    current_allocation_eth: Decimal,
    p_loss_curve: ProbabilityOfLossCurve,
    config: _BasisConfig,
) -> Decimal:
    """Returns the multiplier on next-bar's target allocation based on tail risk.

    Risk gate parameters in default_basis_trade.yaml:
      slashing_risk:
        max_p_loss_exceeds_1pct: 0.05         # if P(loss > 1%) > 5%, back off
        max_p_loss_exceeds_5pct: 0.01         # if P(loss > 5%) > 1%, back off harder
        backoff_multiplier_at_threshold: 0.5  # halve allocation when threshold breached
    """
    risk_config = config.slashing_risk
    if p_loss_curve.p_at_threshold(0.05) > risk_config.max_p_loss_exceeds_5pct:
        return Decimal("0")  # circuit-break — no new allocation
    if p_loss_curve.p_at_threshold(0.01) > risk_config.max_p_loss_exceeds_1pct:
        return Decimal(str(risk_config.backoff_multiplier_at_threshold))
    return Decimal("1.0")  # normal-rate operation
```

Validation harness (Phase 7C tests): compare 1-year archetype backtest with vs without slashing risk gate; document
realized P&L delta + max-drawdown delta + tail-event survival rate.

## Hedge-ratio dynamic adjustment (Phase 6)

> **✅ FULLY SHIPPED 2026-05-17** — hedge_ratio_snapshot persistence pipeline complete:
>
> - **UAC@2fcb1bb**: `DataType.HEDGE_RATIO_SNAPSHOT` + `HedgeRatioSnapshotRecord` schema in
>   `unified_api_contracts/internal/domain/defi/sim_schemas.py`; bucket: `strategy-store/defi`
> - **strategy-service@21209bd**: `HedgeRatioSnapshotWriter` + `CarryStakedBasisEngine.on_tick` wire-in; emits on
>   `decision.rebalance_triggered=True`; ManifestWriter records per-archetype-per-day
> - **pnl-attribution-service@ee96d3c**: `read_hedge_ratio_snapshots` reader in `PnlDomainAdapter`
>
> Sub-plan: `hedge_ratio_snapshot_persistence_2026_05_13.md` Phases 0-3 complete. Phase 6C validation harness:
> `strategy-service@7eb3dab`.
>
> **✅ Phase 5 — Pre-decision audit trail shipped 2026-05-18** (B-015 paper VM: 5 consecutive `fills=0` hold-ticks were
> opaque — Phases 1-4 only emit on `rebalance_triggered=True`):
>
> - **UAC@b8bdedf**: `StrategyDecisionContext` / `StrategyDecisionContextRecord` schemas; `availability_semantics` +
>   `source_priority` entries for `("defi", "strategy_decision_context")`. **UAC@2494e0d** + **UAC@d3872a3**:
>   `DecisionOutcome(StrEnum)` typed enum + export from `unified_api_contracts.internal` (slot 3 2026-05-18).
> - **strategy-service@3c332ac**: `decision_context_writer.py` (Pattern A inline) + wire-in in
>   `CarryStakedBasisEngine.on_tick` — emits on EVERY tick (not just rebalance); outcomes: `REBALANCED` /
>   `HOLD_WITHIN_DRIFT_BAND` / `HOLD_POSITION_OPTIMAL`.
> - **strategy-service@285f154**: 11 unit tests (`test_decision_context_writer.py`) — schema, row values, exception
>   swallowing, all `DecisionOutcome` values. **strategy-service@df2ff9f**: autouse perf guard (slot 3 2026-05-18).
> - **pnl-attribution-service@f8db566**: `read_strategy_decision_context()` reader in `PnlDomainAdapter`.
>
> Sub-plan Phase 5 closed: `hedge_ratio_snapshot_persistence_2026_05_13.md` Phase 5.
>
> **✅ Phase 6 — Features-onchain audit trail scaffold shipped 2026-05-19** (slot-5):
>
> Full audit chain target:
>
> ```
> correlation_id → StrategyDecisionContextRecord (strategy-service, Phase 5 ✅)
>               → FeatureObservationRecord (features-onchain-service, Phase 6 scaffold ✅)
>               → MTDS source rows (GCS parquet path + row ID)
> ```
>
> - **UAC@4f29dbb (features-service scaffold) + UAC@9892679**: `FeatureObservation` / `FeatureObservationRecord`
>   Pydantic schemas in `sim_schemas.py`; `("defi", "feature_observation_snapshot")` in `availability_semantics` +
>   `source_priority`; exported from `internal/domain/defi/__init__.py` + `internal/__init__.py`.
>   `correlation_id: str | None = None` wired (propagation from engine tick pending Phase 3 of
>   `features_tick_observation_audit_2026_05_18.md`).
> - **features-service@4f29dbb**: `feature_observation_writer.py` — `emit_feature_observation()` Pattern A inline
>   writer; 4 unit tests in `test_feature_observation_writer.py`. Engine wiring pending (Phase 2.2 of sub-plan).
>
> Sub-plan: `features_tick_observation_audit_2026_05_18.md`.

`carry_staked_basis` shorts SOL perp against long jitoSOL; ratio assumes 1:1 SOL-equivalent but jitoSOL/SOL drifts with
peg behavior + accrual.

### Phase 6A audit ✅ DONE 2026-05-12 (slot 6 Day-1 finding)

**Hedge ratio is STATIC.** Original Phase 6A todo pointer (`pairs_fixed.py` + `default_basis_trade.yaml`) was stale —
`pairs_fixed.py` is the stat_arb_pairs strategy, not the `carry_staked_basis` archetype.

**Real code path**: `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:248-318`
(function `_build_legs()`).

Line 264:

```python
perp_short_units = eth_qty * (Decimal("1") - structure.perp_margin_haircut)
```

The hedge is sized 1:1 against LST principal (delta-neutral) clamped by venue margin haircut. There is **no per-tick /
per-bar peg-drift adjustment** anywhere in the carry-staked-basis engine. `default_basis_trade.yaml` has a
`hedge_ratio_window: 60` parameter — but that's consumed by `stat_arb_pairs` strategy (rolling OLS hedge ratio for fixed
pairs), NOT by `carry_staked_basis`. The carry archetype has no hedge_ratio dynamics in either code or config.

### Phase 6B implementation spec (operator-runnable for Harsh slot 4)

Audit-confirmed: **Phase 6B IS needed** (no longer conditional on "if static" — finding closed).

Extend `staked_basis.py::_build_legs()` to consume an LST/native exchange rate stream from MTDS:

```python
# strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py
def _compute_dynamic_hedge_ratio(
    structure: _DerivedStructure,
    lst_rate_now: Decimal,            # current jitoSOL/SOL (or rETH/ETH, etc.) from MTDS lst_rates data_type
    last_rebalance_rate: Decimal | None,  # stored in StrategyState
    peg_drift_threshold_bps: Decimal = Decimal("25"),  # hysteresis band — default = ~3σ daily for jitoSOL/SOL
) -> tuple[Decimal, bool]:
    """Returns (hedge_ratio_multiplier, should_rebalance).

    hedge_ratio_multiplier = lst_rate_now (always; this is what perp_short_units is scaled by).
    should_rebalance = True if |lst_rate_now / last_rebalance_rate - 1| * 10000 > peg_drift_threshold_bps.
    """
    if last_rebalance_rate is None:
        return lst_rate_now, True  # initial entry — always set
    drift_bps = abs(lst_rate_now / last_rebalance_rate - Decimal("1")) * Decimal("10000")
    return lst_rate_now, drift_bps > peg_drift_threshold_bps
```

Then in `_build_legs()` line 264 refactor:

```python
# BEFORE (static):
perp_short_units = eth_qty * (Decimal("1") - structure.perp_margin_haircut)

# AFTER (dynamic):
hedge_multiplier, _ = _compute_dynamic_hedge_ratio(
    structure, lst_rate_now=mtds.current_lst_rate(config.lst_asset),
    last_rebalance_rate=strategy_state.last_hedge_rebalance_rate,
)
perp_short_units = eth_qty * hedge_multiplier * (Decimal("1") - structure.perp_margin_haircut)
```

Plus a per-tick handler in `CarryStakedBasisEngine.on_tick()` (line 326) that reads current LST rate, calls
`_compute_dynamic_hedge_ratio`, and if `should_rebalance` emits a rebalance leg adjusting `perp_short_units` to the new
size. Rebalance leg is an `InstructionActionV2.TRADE` on the perp venue with `params={"role": "hedge_rebalance"}`.

### Hysteresis band calibration

Default `peg_drift_threshold_bps = 25` based on observed historical jitoSOL/SOL daily-stddev ≈ 8 bps (~3σ rebalance
trigger). Per-archetype config overridable in `default_basis_trade.yaml`:

```yaml
hedge_ratio:
  dynamic: true # NEW flag — Phase 6B enables
  peg_drift_threshold_bps: 25 # rebalance trigger
  min_rebalance_interval_seconds: 300 # rate-limit (5 min) — prevents thrash on volatile peg
  max_rebalance_per_day: 24 # circuit-breaker — Phase 6 risk register
```

LST exchange rate stream source (per MTDS `lst_rates` data_type catalogue):

- **jitoSOL/SOL**: Jito stake pool on-chain getter `getStakeAccountRentExemption` + Solana RPC `getMultipleAccounts` for
  stake delegations.
- **mSOL/SOL**: Marinade `marinadeProgramAccountInfo` + on-chain stake.
- **bSOL/SOL**: BlazeStake stake pool getter.
- **rETH/ETH**: RocketPool `rETH.getExchangeRate()` view function.
- **stETH/ETH**: Lido `stEthPerToken()` getter (always ~1.0 for stETH — rebasing token; use wstETH/ETH for the actual
  drift signal: `wstETH.stEthPerToken()`).
- **weETH/ETH**: Ether.fi `weETH.getRate()`.

Capture cadence: per-block on EVM chains (Ether.fi / RocketPool / Lido), per-epoch on Solana (Jito / Marinade /
BlazeStake). Backtest replay reads historical rates from MTDS at simulation block.

### Phase 6C validation harness

Backtest carry archetype with dynamic vs static hedge-ratio over 1-year historical replay:

- Run A: static hedge (current production code, pre-Phase-6B).
- Run B: dynamic hedge (post-Phase-6B with default `peg_drift_threshold_bps=25`).
- Run C: dynamic hedge with operator-tuned threshold (`peg_drift_threshold_bps ∈ {10, 25, 50, 100}` sweep).

Document P&L delta + confidence interval per Phase 6 full-execution criterion.

### Phase 6 writeback + consumer chain (landed 2026-05-17)

`hedge_ratio_snapshots` persistence sub-plan (`hedge_ratio_snapshot_persistence_2026_05_13.md`) delivered the full
writeback chain:

- **UAC data_type**: `("defi", "hedge_ratio_snapshot")` registered in `availability_semantics` + `source_priority` +
  `pipeline_mode`. `HedgeRatioSnapshotRecord` (13 columns: all `HedgeRatioSnapshot` fields + `partition_dt` /
  `available_at` / `correlation_id`) in `unified_api_contracts/internal/domain/defi/sim_schemas.py`. uac@`2fcb1bb`.
- **Producer**: `strategy_service/engine/strategies/v2/carry_and_yield/hedge_ratio_writer.py` —
  `emit_hedge_ratio_snapshot()` writes inline (Pattern A) on every `rebalance_triggered=True` tick.
  `CarryStakedBasisEngine.on_tick` calls it with `correlation_id=instruction.instruction_id`. ManifestWriter
  `record_captured(category="defi", data_type="hedge_ratio_snapshot")` best-effort. strategy-service@`21209bd`. Path:
  `gs://{pid}-strategy-store/hedge_ratio_snapshots/asset_group=defi/archetype={a}/dt={YYYY-MM-DD}/{ts}_{a}.parquet`.
- **Consumer**: `PnlDomainAdapter.read_hedge_ratio_snapshots(archetype, dates)` in
  `pnl_attribution_service/adapters/domain_adapter.py` — loads per-archetype per-date shards via
  `resolve_bucket_name(kind="strategy-store", asset_group="defi")` + `get_storage_client().download_bytes()`.
  pnl-attribution-service@`ee96d3c`.
- **Attribution decomposition**: `read_hedge_ratio_snapshots` feeds P&L decomposition into (a) carry yield, (b)
  hedge-residual P&L, (c) execution alpha at each rebalance point.

## Architecture diagram

```
                                    Catalogue captures
                                    (defi_catalogue_chain_primitives)
                                              │
                                              ▼
                                    +─────────────────────+
                                    │ MTDS data_types     │
                                    │  - dex_pools        │
                                    │  - lending_indices  │
                                    │  - oracle_prices    │
                                    │  - lst_rates        │
                                    │  - staking_yields   │
                                    │  - slashing_events  │
                                    │  - governance_props │
                                    +─────────────────────+
                                              │
                                              ▼
+──────────────────────────────────────────────────────────────────────+
│ Matching Engine (execution-service/execution_service/matching_engine/) │
│                                                                       │
│  amm.py        — UniswapV2 / V3 / V4 / Curve / Balancer / Solana CLMM │
│  hooks.py      — V4 hooks + custom curves                              │
│  benchmark     — LendingRateImpactCalculator                           │
│  governance    — GovernanceProposalSimulator (Tenderly fork)           │
│  yield_stream  — StakingYieldStreamSimulator                           │
│  slashing      — SlashingTailRiskMC                                    │
│  hedge_ratio   — DynamicHedgeRatio (peg-drift driven)                 │
+──────────────────────────────────────────────────────────────────────+
                                              │
                                              ▼
                                    Per-strategy + per-archetype
                                    backtest replay engine
                                    + risk simulations sibling
```

## Validation gates

Per `defi_simulation_realism` Phase 8 (backtest fidelity validation):

- **Phase 8A — Carry archetype 1-year replay**: simulated P&L vs old (constant-product + zero-rate-impact + static-
  hedge) replay. Document delta + reduced bias.
- **Phase 8B — Leveraged-funding-arb 1-year replay**: ditto.
- **Phase 8C — Tenderly fork live-vs-simulated reconciliation** for 1 day of paper-trade. Per-tick |delta| < 10bps for ≥
  95% of fills.
- **Phase 8D — Operator sign-off** that backtest fidelity acceptable for May-23 cutover.

### Phase 8 validation framework (Day-1 slot 6 design ship 2026-05-12; operator-runnable for Harsh slot 4)

Validation harness lives at `execution-service/tests/integration/backtest_fidelity/` (NEW Phase 8). Three parallel
scripts produce JSON reports the operator reviews for Phase 8D sign-off:

```
backtest_fidelity/
├── run_carry_archetype_replay.py          # Phase 8A
├── run_leveraged_funding_arb_replay.py    # Phase 8B
├── run_tenderly_live_reconciliation.py    # Phase 8C
└── compose_sign_off_report.py             # Phase 8D — operator dashboard
```

**Phase 8A — Carry archetype 1-year replay** (`run_carry_archetype_replay.py`):

```python
def run_carry_replay(
    archetype: str = "carry_staked_basis",
    lookback_days: int = 365,
    engine_old: MatchingEngineConfig = MATCHING_ENGINE_OLD,   # pre-2026-05-10 V2-only + zero-impact + static-hedge
    engine_new: MatchingEngineConfig = MATCHING_ENGINE_NEW,   # post-Phase-2-7 PoolMatcher + rate-impact + dynamic-hedge
) -> BacktestFidelityReport:
    """Replay 1-year carry archetype trades through both old + new matching engines; diff P&L + metrics."""
    historical_trades = mtds.read_archetype_trades(archetype, lookback_days)
    pnl_old = []
    pnl_new = []
    for trade in historical_trades:
        fill_old = engine_old.replay_trade(trade, pool_snapshot_at(trade.block_number))
        fill_new = engine_new.replay_trade(trade, pool_snapshot_at(trade.block_number))
        pnl_old.append(fill_old.realized_pnl_usdc)
        pnl_new.append(fill_new.realized_pnl_usdc)
    return BacktestFidelityReport(
        archetype=archetype,
        n_trades=len(historical_trades),
        old_pnl_total=sum(pnl_old),
        new_pnl_total=sum(pnl_new),
        delta_total_pnl_bps=(sum(pnl_new) - sum(pnl_old)) / sum(abs(p) for p in pnl_old) * 10_000,
        old_pnl_std=stdev(pnl_old),
        new_pnl_std=stdev(pnl_new),
        bias_reduction_pct=(stdev(pnl_old) - stdev(pnl_new)) / stdev(pnl_old) * 100,
        per_leg_breakdown=compute_per_leg_attribution(historical_trades, pnl_old, pnl_new),
        max_drawdown_old=max_dd(pnl_old),
        max_drawdown_new=max_dd(pnl_new),
    )
```

Expected output for a 1-year carry replay: simulated P&L delta in the range 50-300 bps (new engine has higher fidelity →
less optimistic estimates due to rate-impact + dynamic-hedge + per-shape pool dispatch). Negative delta means new engine
reports LOWER P&L than old — this is the EXPECTED direction (old engine over-estimated because zero-impact assumptions
favor the strategy). **A POSITIVE delta is a red flag** — investigate matcher bugs.

**Phase 8B — Leveraged-funding-arb 1-year replay** (`run_leveraged_funding_arb_replay.py`): same shape as 8A but with
`archetype="leveraged_funding_arb"`. Per-leg attribution differs (funding-arb has perp + lending legs vs
carry-staked-basis's stake + perp legs). Expected delta range 30-200 bps (smaller than carry because funding-arb is less
LST-rate-impact-sensitive).

**Phase 8C — Tenderly fork live-vs-simulated reconciliation** (`run_tenderly_live_reconciliation.py`):

```python
def run_tenderly_reconciliation(
    paper_trade_window_hours: int = 24,
    tolerance_bps: Decimal = Decimal("10"),
    coverage_threshold_pct: Decimal = Decimal("95"),
) -> TenderlyReconciliationReport:
    """For each tick of yesterday's paper-trade window: re-simulate via Tenderly fork at same block."""
    paper_trades = paper_trade_log.read(window_hours=paper_trade_window_hours)
    per_tick_deltas: list[Decimal] = []
    for trade in paper_trades:
        # Live fill: from paper-trade log
        live_fill = trade.realized_fill
        # Simulated fill: re-run via current PoolMatcher against Tenderly fork at the same block
        fork_id = tenderly.create_fork(
            chain_id=trade.chain_id,
            block_number=trade.block_number,
        )
        pool = pool_from_address(trade.pool_address, fork_state=tenderly.read_pool_state(fork_id, trade.pool_address))
        sim_quote = pool.quote(trade.amount_in, trade.side)
        delta_bps = abs(sim_quote.amount_out - live_fill.amount_out) / live_fill.amount_out * Decimal("10000")
        per_tick_deltas.append(delta_bps)
        tenderly.delete_fork(fork_id)  # ~10c per fork; 5000 ticks/day = ~$500/day during validation runs
    within_tolerance_pct = (
        Decimal(sum(1 for d in per_tick_deltas if d < tolerance_bps))
        / Decimal(len(per_tick_deltas))
        * Decimal("100")
    )
    return TenderlyReconciliationReport(
        n_ticks=len(per_tick_deltas),
        within_tolerance_pct=within_tolerance_pct,
        median_delta_bps=median(per_tick_deltas),
        p95_delta_bps=percentile(per_tick_deltas, 95),
        pass_phase_8c_gate=within_tolerance_pct >= coverage_threshold_pct,
    )
```

**Acceptance gate**: `within_tolerance_pct >= 95%` (per Phase 8C criterion). Failure mode flags per-pool-shape breakdown
so operator can identify which matcher (V3 / Curve / Solidly-fork / etc.) is drifting.

**Phase 8D — Operator sign-off report** (`compose_sign_off_report.py`):

```python
@dataclass
class SignOffReport:
    """Operator dashboard for May-23 cutover gate. Plain JSON; rendered by deployment-ui."""
    plan_version: str
    generated_at: datetime
    phase_8a_carry: BacktestFidelityReport
    phase_8b_leveraged: BacktestFidelityReport
    phase_8c_tenderly: TenderlyReconciliationReport
    aggregate_signal: Literal["GREEN", "YELLOW", "RED"]   # GREEN if all 3 pass; YELLOW if 2/3; RED otherwise
    operator_sign_off_status: Literal["PENDING", "APPROVED", "REJECTED"]
    operator_sign_off_at: datetime | None
    operator_sign_off_notes: str

    @property
    def gate_pass_summary(self) -> dict[str, bool]:
        return {
            "carry_replay_pass": self.phase_8a_carry.delta_total_pnl_bps < Decimal("0"),  # new engine LOWER P&L = expected
            "leveraged_replay_pass": self.phase_8b_leveraged.delta_total_pnl_bps < Decimal("0"),
            "tenderly_reconciliation_pass": self.phase_8c_tenderly.pass_phase_8c_gate,
        }
```

`SignOffReport` rendered by deployment-ui as a Phase-8 dashboard tile (NEW Phase 8D UI work — slot-8 owns DART surfaces
per cross_cutting #4; cross-side coordinate). Operator clicks APPROVE / REJECT button + types notes; status persists to
`pnl-attribution-service` as a one-off audit row keyed by `plan_version`.

### Phase 8 cross-plan dependencies

- **Phase 8A/B** requires `MATCHING_ENGINE_NEW` config — wired AFTER Harsh slot 4 ships Phase 2-7 implementations.
- **Phase 8C** requires Tenderly fork API + paper-trade log — Tenderly already wired
  ([`tenderly-execution-provider.md`](tenderly-execution-provider.md)); paper-trade log is master plan Group F item 17.
- **Phase 8D operator sign-off** is a Group F item 17+18 entry in `master_to_live_defi_2026_05_23.md` — refresh routed
  to slot 1 per Phase 9E annotation in `defi_simulation_realism_2026_05_10.md`.

## Cross-references

- Plan: [`defi_simulation_realism_2026_05_10.md`](../../plans/archive/defi_simulation_realism_2026_05_10.md) — owns
  implementation.
- Plan:
  [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md)
  Phase 3 — ships data_types this doc consumes.
- Codex: [`defi-data-type-taxonomy.md`](/codex/02-data/defi-data-type-taxonomy.md) — input data shapes.
- Codex: [`concentrated-liquidity.md`](concentrated-liquidity.md) — V3/V4 + Solana CLMM addendum (Phase 9B update).
- Codex: [`batch-live-architecture.md`](batch-live-architecture.md) — live=batch principle (Phase 9D update).
- Codex: [`tenderly-execution-provider.md`](tenderly-execution-provider.md) — Tenderly provider used by governance sim.
- Codex:
  [`/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`](/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md)
  — restaking yield decomposition (Phase 9C update).
- Code:
  [`execution-service/execution_service/matching_engine/`](../../../execution-service/execution_service/matching_engine/)
  — implementation home.
- UAC: `internal/domain/defi/` — schemas (`PoolShape`, `LendingMarketState`, `GovernanceProposal`,
  `StakingYieldDecomposition`, `SlashingEvent`, `HedgeRatioSnapshot`).

## Update protocol

When adding a new pool shape:

1. Add to UAC `PoolShape` enum (in `unified-api-contracts/unified_api_contracts/internal/domain/defi/` — currently TO BE
   CREATED per Phase 1A; member list locked in plan body Phase 1A todo).
2. Add model implementation to `matching_engine/amm.py` or `hooks.py`.
3. Add validation harness (≥ N historical Tenderly-fork swaps within bps).
4. Add row to "Pool shape taxonomy + slippage models" section of this doc + new row to "Per-shape sample pools + golden
   fixture seeds" table.
5. Update routing in `engine.py:_amm_match_impl` to dispatch by `pool.pool_shape` (currently hardcoded to V2 per
   `engine.py:471`).

When adding a new ve(3,3) Solidly fork (e.g., Equalizer / Thena / Ramses):

1. **Prefer `SOLIDLY_FORK` shared matcher** with `(chain_id, factory_address)` discriminator over a new enum member. The
   cubic stable + xy=k volatile math is byte-for-byte identical across forks.
2. If the fork has a **Slipstream / CL variant** (Velodrome Slipstream, Aerodrome Slipstream), that is a SEPARATE
   matcher (V3-tick math) — either fold into `SOLIDLY_CL_FORK` shared matcher or add a parallel enum member.
   Operator-decision in Phase 1A.
3. Add per-fork golden fixture (≥ 1 stable + 1 volatile swap) to "Per-shape sample pools + golden fixture seeds" table.

When adding a new simulation primitive (governance / staking / slashing / etc.):

1. Add to UAC `internal/domain/defi/` schema if new data shape.
2. Add MTDS capture adapter if new data_type per `defi-data-type-taxonomy.md`.
3. Add simulator class to `matching_engine/`.
4. Add Phase to `defi_simulation_realism` plan with success criteria.
5. Update this doc's relevant section + cross-references.
