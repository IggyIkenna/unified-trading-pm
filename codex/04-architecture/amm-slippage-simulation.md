---
scope: [engineer]
---

# AMM Slippage + Simulation Realism

> SSOT for matching engine simulation realism: per-pool-shape AMM models, lending rate-impact-from-own-trade,
> governance proposal simulation harness, staking + restaking yield-stream models, slashing tail-risk MC.
> Last updated 2026-05-10 (defi_simulation_realism_2026_05_10 Phase 9A).

This doc is the architecture-side companion to
[`defi_simulation_realism_2026_05_10.md`](../../plans/active/defi_simulation_realism_2026_05_10.md). It declares the
mathematical models + their input shapes + their validation thresholds for every simulation primitive. The plan
ships the implementation; this doc locks the contract.

## Why simulation realism matters

The matching engine is the **batch surface** that backtest P&L runs against, per CLAUDE.md "Batch = Live" principle:
"Batch and live use the SAME code path, same component interactions. The ONLY difference is execution fills." The
matching engine produces the simulated fills for batch (and for live's "always fill at requested price" strategy
P&L mode). If the matching engine model is wrong, backtest P&L is wrong, the strategy ships with the wrong sizing
+ the wrong tail risk, and live trade losses surprise everyone.

Pre-2026-05-10 matching engine had ONE AMM model (constant product `x*y=k`) per
[`engine.py:7-12`](../../../execution-service/execution_service/matching_engine/engine.py): "AMMMatcher: DeFi Swaps
(constant product x*y=k)". This is correct only for Uniswap V2; every other AMM (V3 / V4 / Curve / Balancer / Solana
CLMM / aggregators) was approximated, producing 50-500bps fill-price errors for any non-V2 leg.

This doc fixes that by declaring per-pool-shape models that match production within ~5-10bps.

## Pool shape taxonomy + slippage models

**Per-pool-shape model** (UAC `PoolShape` enum, declared in `defi_simulation_realism` Phase 1A):

### 1. Uniswap V2 (constant product x*y=k)

```
amount_out = (reserve_out * amount_in) / (reserve_in + amount_in)
```

Realized fill = pre-fee output minus 0.3% LP fee. Existing in `matching_engine/amm.py:UniswapV2Pool`. ✅ correct.

### 2. Uniswap V3 (concentrated liquidity, tick-bucket integration)

V3 fills consume liquidity at the current tick first; if size pushes through tick boundaries, integrates over each
tick crossed. Per-tick: `getAmountsForLiquidity(sqrtPriceLower, sqrtPriceUpper, liquidity)`.

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

Existing `hooks.py:CustomCurveHook` covers `constant_sum`, `constant_mean`, `polynomial`, `logarithmic` curves.
Phase 2B extends to V4 hook semantics.

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

Boosted = linear-pool building blocks (Aave aTokens wrapped); composable = phantom BPT in pool. Both reduce to
weighted internally — handle the routing layer (decompose multi-leg via Balancer Vault).

### 8. Solana CLMM (Raydium + Orca)

Same tick-bucket math as Uniswap V3 but per-Solana-CLMM decimals + SPL-token semantics. New `SolanaCLMMPool`
reuses V3 base.

**Inputs**: per-pool tick bitmap (Solana-specific layout), `sqrt_price_x96`-equivalent, `liquidity_active`.
**Validation**: ≥ 30 historical Raydium / Orca swaps within 5bps.

### 9. Aggregator (Jupiter / 1inch / 0x / ParaSwap)

Read route from quote API; for each route leg, route to the appropriate pool-shape matcher above; compose realized
fill across legs.

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
`total_borrow`, `optimal_utilization_rate`, `irm_base`, `irm_slope1`, `irm_slope2`, `reserve_factor`,
`liquidityIndex`, `variableBorrowIndex`. **Validation**: replay ≥ 50 historical large-supply events; ≥ 90% within
10bps APY tolerance.

`BenchmarkMatcher` extension (Phase 3B): all supply/borrow/repay/withdraw at Aave V3 + Compound V3 + Spark + Radiant
call this calculator. Backtest yield uses post-trade rate.

## Governance proposal simulation harness

Capture (`defi_simulation_realism` Phase 4A): on-chain Governor events + Snapshot off-chain proposals API for
Aave V3 + Compound V3 + Spark + Lido.

Simulator (Phase 4B): given proposal ID + Tenderly fork:

1. Apply `governor.execute(proposal_id)` on the fork (advances to executed state).
2. Read affected parameters (`getReserveData(asset)` for Aave, etc.) from fork before + after.
3. Output: per-affected-instrument before/after parameter delta.

CLI (Phase 4C): `defi-simulate-proposal --proposal-id <id> --archetype <X> --time T` returns archetype P&L delta if
proposal executes at time T. Used by risk simulations sibling.

**Inputs**: `GovernanceProposal` schema (`defi_simulation_realism` Phase 1C). **Validation**: ≥ 5 historical
proposals' P&L delta within 100bps of actual realized post-execution delta.

## Staking + restaking yield-stream simulators

### Native staking (Phase 5A)

Per-chain stochastic model:

- **Ethereum beacon**: per-epoch reward distribution = consensus reward + execution layer (block-builder tip).
  Historical 6+ months from `staking_yields` data_type. Forward distribution = 5-day rolling mean ± 2 stddev band
  per epoch + churn-adjusted (validator entry/exit queue length feeds attestation efficiency).
- **Solana validator**: per-validator-epoch reward = base inflation + transaction fees + MEV (validator-tip share).
  Historical from `staking_yields` data_type. Forward distribution similar.

### Restaking AVS (Phase 5B)

Per-AVS reward variability layered on top of native staking base. EigenLayer + Symbiotic + Karak + Jito-restaking
AVSes from Phase 1A captures (`restaking_rewards` data_type). Per-LRT forward distribution: composite of native +
AVS rewards weighted by operator allocation share.

### LRT protocol-fee (Phase 5C)

Discrete-event model — Ether.fi / Renzo / KelpDAO / Puffer fees historically change ~quarterly via governance.
Capture `governance_proposals` for fee-change events; forward fee assumption = most-recent-quarter fee + ±1 stddev
band per protocol.

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

## Slashing tail-risk Monte Carlo

Per-chain calibration (Phase 7A): from `slashing_events` data_type captures.

- **Ethereum beacon**: per-validator-epoch slashing probability ≈ 0.01-0.05 bp historical baseline; spikes during
  fork events / client bugs. Heavy-tailed distribution.
- **Solana validator**: per-validator-day slashing probability higher base rate (~0.5-1 bp), distinct shape (per-
  validator-event vs per-validator-epoch).

MC simulator (Phase 7B): `SlashingTailRiskMC(allocation, horizon)`:

1. Sample N=10000 paths from per-validator slashing distribution.
2. Per path, compute expected slashing loss given allocation × N validators.
3. Output P(slashing > threshold) curve.

Carry archetype hook (Phase 7C): output P(slashing) feeds into capital-allocation rule. Cap per-LST exposure when
historical slashing rate spikes; back off when normal.

## Hedge-ratio dynamic adjustment (Phase 6)

`carry_staked_basis` shorts SOL perp against long jitoSOL; ratio assumes 1:1 SOL-equivalent but jitoSOL/SOL drifts
with peg behavior + accrual.

Phase 6A audit: read `pairs_fixed.py` + `default_basis_trade.yaml` to determine whether ratio is static or dynamic.

If static (Phase 6B): implement dynamic adjustment using LST/SOL exchange rate stream from Phase 1A captures
(jitoSOL/SOL, mSOL/SOL, bSOL/SOL, rETH/ETH, stETH/ETH, weETH/ETH). Per-tick or per-bar rebalance trigger when
|peg_drift| > N bps with hysteresis band (avoid over-trading).

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
- **Phase 8C — Tenderly fork live-vs-simulated reconciliation** for 1 day of paper-trade. Per-tick |delta| < 10bps
  for ≥ 95% of fills.
- **Phase 8D — Operator sign-off** that backtest fidelity acceptable for May-23 cutover.

## Cross-references

- Plan: [`defi_simulation_realism_2026_05_10.md`](../../plans/active/defi_simulation_realism_2026_05_10.md) — owns
  implementation.
- Plan: [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md)
  Phase 3 — ships data_types this doc consumes.
- Codex: [`defi-data-type-taxonomy.md`](../02-data/defi-data-type-taxonomy.md) — input data shapes.
- Codex: [`concentrated-liquidity.md`](concentrated-liquidity.md) — V3/V4 + Solana CLMM addendum (Phase 9B update).
- Codex: [`batch-live-architecture.md`](batch-live-architecture.md) — live=batch principle (Phase 9D update).
- Codex: [`tenderly-execution-provider.md`](tenderly-execution-provider.md) — Tenderly provider used by governance
  sim.
- Codex:
  [`../09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`](../09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md)
  — restaking yield decomposition (Phase 9C update).
- Code: [`execution-service/execution_service/matching_engine/`](../../../execution-service/execution_service/matching_engine/)
  — implementation home.
- UAC: `internal/domain/defi/` — schemas (`PoolShape`, `LendingMarketState`, `GovernanceProposal`,
  `StakingYieldDecomposition`, `SlashingEvent`, `HedgeRatioSnapshot`).

## Update protocol

When adding a new pool shape:

1. Add to UAC `PoolShape` enum.
2. Add model implementation to `matching_engine/amm.py` or `hooks.py`.
3. Add validation harness (≥ N historical Tenderly-fork swaps within bps).
4. Add row to "Pool shape taxonomy + slippage models" section of this doc.
5. Update routing in `engine.py:_amm_match_impl`.

When adding a new simulation primitive (governance / staking / slashing / etc.):

1. Add to UAC `internal/domain/defi/` schema if new data shape.
2. Add MTDS capture adapter if new data_type per `defi-data-type-taxonomy.md`.
3. Add simulator class to `matching_engine/`.
4. Add Phase to `defi_simulation_realism` plan with success criteria.
5. Update this doc's relevant section + cross-references.
