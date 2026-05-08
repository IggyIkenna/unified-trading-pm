---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: shared
  co_location: []
  latency_budget_ms: 500
  min_sla_tier: standard
---

# Archetype: `DEFI_LP_CONCENTRATED`

> **Family:** `MARKET_MAKING` (provides liquidity vs taking it). **Settlement model:** ATOMIC mint/burn via Uniswap V3
> NonfungiblePositionManager. **Code module:**
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

A future extension adds dedicated `LP_MINT` / `LP_BURN` enum values for clearer wire-level routing, but is not blocking.

## Risks

- **Out-of-range exposure** — when spot exits the range without a timely rebalance, the position becomes single-sided
  and stops earning fees. Hold-and-wait is fine for stable pairs, fatal for volatile pairs.
- **Gas-cost vs rebalance frequency** — a tighter band captures more fees but burns more gas. Tune `rebalance_band_pct`
  and `min_rebalance_interval_seconds` jointly.
- **MEV on rebalance** — the burn + swap-the-imbalance + mint sequence is a sandwich target. Use a private-mempool /
  Flashbots Protect path to submit. (Tracked in the deferred mempool-feed plan.)

## Plan

`plans/active/defi_pipeline_extension_2026_05_01.plan.md` Phase 4.1.
