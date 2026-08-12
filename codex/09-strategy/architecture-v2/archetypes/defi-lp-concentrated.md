---
doc_type: codex-ssot
title: "Archetype: `DEFI_LP_CONCENTRATED`"
summary: >-
  Archetype DEFI_LP_CONCENTRATED: mints a Uniswap-V3-style concentrated-liquidity position +-range_pct around spot,
  earns swap fees while in range, and rebalances (burn+mint) when spot exits rebalance_band_pct subject to a gas-aware
  min_rebalance_interval_seconds. Exports the closed-form position_value / liquidity_for_amounts / compute_il_pct
  helpers as the SSOT for IL calculators.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, defi, execution, archetype, features]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-pool.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
  ]
created: 2026-05-01
authoritative_for: [DEFI_LP_CONCENTRATED archetype specification]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/defi/active-defi-mm.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-pool.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-vault.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: DEFI_LP_CONCENTRATED
family: MARKET_MAKING
venue_universe: [UNISWAP_V3, PANCAKESWAP_V3, SUSHISWAP_V3, TRADER_JOE_LB]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 500
  min_sla_tier: premium
---

# Archetype: `DEFI_LP_CONCENTRATED`

> **Family:** [Market Making](../families/market-making.md) (`MARKET_MAKING` — provides liquidity vs taking it).
> **Settlement model:** ATOMIC mint/burn via Uniswap V3 NonfungiblePositionManager. **Code module (SHIPPED):**
> `strategy-service/strategy_service/engine/strategies/v2/defi_lp/concentrated.py`.

## What it does

Mints a Uniswap V3 (or clone — PancakeSwap V3, SushiSwap V3, Trader Joe Liquidity Book) concentrated-liquidity position
spanning a configurable price range (`±range_pct`) around the current spot. Earns swap fees while spot is inside the
range; rebalances when spot drifts outside the `rebalance_band_pct` band, subject to a gas-cost-aware
`min_rebalance_interval_seconds` rate limit.

## Math

V3 uses `sqrt(P)` (Q64.96) as the price representation. Liquidity `L` is constant across the active range. Closed-form
helpers exported from `strategy_service/engine/strategies/v2/defi_lp/concentrated.py`:

```
position_value(s, sl, su, L) -> (amount0, amount1)
  amount0 = L * (su - s)/(s * su)        (in-range)
  amount1 = L * (s - sl)
liquidity_for_amounts(s, sl, su, a0, a1) -> L
compute_il_pct(s_entry, s_now, sl, su, L) -> Decimal
  IL = V_position(s_now) / V_hold(s_now) - 1
```

These helpers are the SSOT — the features-onchain `concentrated_liquidity_il_realised` calculator imports them rather
than re-implementing.

## State machine

```
NEUTRAL  --on first qualifying tick-->  MINTED(range, liquidity)
                                              |
                            spot exits band  +
                            interval elapsed |
                                              v
                                        REBALANCE_PENDING
                                              |
                                              v
                                        MINTED (new range)
                                              |
                            kill switch       +
                                              v
                                          BURNED
```

## Trigger conditions

| Trigger        | Condition                                                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| MINT (initial) | `_PositionState == NEUTRAL` and `lp_pool_sqrt_price_<pool>` is positive                                                           |
| REBALANCE      | `\|sqrt_price_now / sqrt_price_entry - 1\| > rebalance_band_pct` AND time since last rebalance ≥ `min_rebalance_interval_seconds` |
| BURN (kill)    | `flatten_on_kill()` — kill switch fired or strategy retired                                                                       |

The rebalance burn + mint is emitted as two consecutive `AtomicInstruction` envelopes (burn first, mint second);
execution-service sequences them through the same V3 position manager.

## Required feature keys

- `lp_pool_sqrt_price_<pool_address>` — current sqrt(P) Q64.96 fixed-point
- `lp_pool_token0_price_usd_<pool_address>` — for USD denomination of fees
- `lp_pool_token1_price_usd_<pool_address>`

## Wire format

`InstructionActionV2.SWAP` with `params["lp_operation"] = "mint" | "burn"`. Position metadata (sqrt_price_lower,
sqrt_price_upper, liquidity, amount0_initial, amount1_initial) carried in `params`.

The dedicated `LP_MINT` / `LP_BURN` enum values now exist (actions 13/14 in the instruction catalog), but the engine
still routes LP ops through `SWAP` + `lp_operation` (`concentrated.py` emits `lp_operation="mint"|"burn"|"rebalance"`);
migrating to the dedicated actions for clearer wire-level routing is a non-blocking follow-up.

### LegController integration

`LegController.update(slot, tick, execution_mode=ATOMIC)` resolves the rebalance burn + mint as a 2-leg ATOMIC bundle:
leg-1 = `LP_BURN` (existing position), leg-2 = `LP_MINT` (new range). The NonfungiblePositionManager multicall is the
atomic unit; execution-service sequences both legs through the same call.

**Code-backport status:** DEFERRED — `defi_lp/concentrated.py` currently emits `AtomicInstruction` pairs hand-built
without `LegController`. Backport tracked in `defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs
ship now per operator decision 2026-05-07.

## Risks

- **Out-of-range exposure** — when spot exits the range without a timely rebalance, the position becomes single-sided
  and stops earning fees. Hold-and-wait is fine for stable pairs, fatal for volatile pairs.
- **Gas-cost vs rebalance frequency** — a tighter band captures more fees but burns more gas. Tune `rebalance_band_pct`
  and `min_rebalance_interval_seconds` jointly.
- **MEV on rebalance** — the burn + swap-the-imbalance + mint sequence is a sandwich target. Use a private-mempool /
  Flashbots Protect path to submit. (Tracked in the deferred mempool-feed plan.)

## Example instances

```
DEFI_LP_CONCENTRATED@uniswap-v3-eth-usdc-ethereum-prod
DEFI_LP_CONCENTRATED@uniswap-v3-wbtc-usdc-arbitrum-prod
DEFI_LP_CONCENTRATED@pancakeswap-v3-bnb-usdt-bsc-prod
```

## Not in this archetype

- Full-range / passive pool LP (Curve stableswap, Balancer weighted) → [`DEFI_LP_POOL`](defi-lp-pool.md)
- ERC-4626 yield-vault deposit → [`DEFI_LP_VAULT`](defi-lp-vault.md)
- Single-block JIT concentrated LP minted around a pending swap →
  [`ARBITRAGE_MEV_JIT_LIQUIDITY`](arbitrage-mev-jit-liquidity.md)
- CEX / CLOB order-book quoting → [`MARKET_MAKING_CONTINUOUS`](market-making-continuous.md) + granular variants

## Plan

`plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 4.1.
