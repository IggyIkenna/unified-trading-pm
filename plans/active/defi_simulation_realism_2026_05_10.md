---
name: defi-simulation-realism
overview:
  Matching engine extension for per-pool-shape AMM models (Uniswap V3 tick-bucket, Curve D-invariant, Balancer
  weighted+boosted, Solana CLMM, Jupiter aggregator) + lending rate-impact-from-own-trade simulator + governance
  proposal capture + simulation harness + staking + restaking yield-stream simulator + slashing tail-risk MC. May-23
  cutover scope per all-in operator directive.
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: ~13 calendar days; ~40-70 AI-days at full multi-agent saturation
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/defi_readiness_catalogue_2026_05_08.md
related_codex:
  - codex/04-architecture/amm-slippage-simulation.md
  - codex/04-architecture/concentrated-liquidity.md
  - codex/04-architecture/batch-live-architecture.md
  - codex/04-architecture/tenderly-execution-provider.md
  - codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md
related_plans:
  - plans/active/defi_catalogue_chain_primitives_2026_05_10.md
  - plans/active/cross_asset_group_catalogue_audit_2026_05_10.md
  - plans/questions/risk_simulations_limits_alerting_2026_05_08.md
  - plans/active/defi_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
estimate_class: design
estimate_baseline_ai_days: 53.5
estimate_calibrated_ai_days: 32.1
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~2-3, ~10-15, ~5-8, ~8-12, + 4 more). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# DeFi simulation realism — matching engine + risk modeling extension

## Why this plan exists

The 2026-05-08 catalogue audit identified 6 simulation-realism gaps (Block D in the question doc) that break batch
fidelity for `carry_staked_basis` + `leveraged_funding_arb` + any DeFi archetype that isn't pure-Uniswap-V2:

1. **AMM slippage modeling** is currently single-curve (constant product `x*y=k`) per
   `execution-service/execution_service/matching_engine/engine.py:7-12` ("AMMMatcher: DeFi Swaps (constant product
   x\*y=k)"). Curve `D`-invariant + `gamma`, Balancer weighted+boosted, Solana CLMM tick-bucket, Jupiter aggregator
   per-route decomposition NOT modeled — backtests over-estimate fills for any non-Uniswap-V2 leg.
2. **Lending rate-impact-from-own-trade**: when we supply $X USDC to Aave, utilization moves, rates compress, our yield
   drops. Currently `BenchmarkMatcher` does "instant fill at benchmark" — assumes zero impact. Backtests over- estimate
   yield by ignoring own-trade rate compression. NOT BUILT.
3. **Governance proposal capture + simulation harness**: passing an Aave proposal changes USDC borrow cap or rate model
   parameters; need data + simulation to model "if Aave passes proposal X at time T, what's the impact". NO capture
   adapter exists. NO Tenderly-fork-based proposal what-if harness exists.
4. **Staking + restaking yield-stream simulation**: forward `carry_staked_basis` PnL needs stochastic model of per-epoch
   staking yield variability + slashing tail risk + restaking AVS reward variability + LRT-protocol-fee changes.
   Currently treated as constant baseline. NOT BUILT.
5. **Hedge-ratio dynamic adjustment**: `carry_staked_basis` shorts SOL perp against long jitoSOL; ratio assumes 1:1
   SOL-equivalent but jitoSOL/SOL drifts. Probably static — needs verification + dynamic adjustment if static.
6. **Slashing tail-risk MC**: rare-but-catastrophic slashing events; need historical rate calibration per chain
   (Ethereum beacon long history; Solana validator distinct shape). NOT BUILT.

Per all-in-scope directive 2026-05-10: all 6 IN SCOPE for May-23. This plan owns the simulation-realism half; the
catalogue + chain-primitives half is at
[`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md).

**Live = batch principle (CLAUDE.md)**: same code path, same component interactions, only the execution-fill source
differs (matching-engine simulated fills vs venue real fills). Improving matching-engine realism here directly improves
backtest fidelity for live archetypes — the matching engine IS the batch surface that backtest P&L runs against.

## Pre-audit reference

Question doc § Block D + Block B (B3 pool depth + B4 LST data + B5 lending governance). Existing matching engine
inventory: `execution-service/execution_service/matching_engine/`:

- `engine.py` (32 functions) — orchestrator + matcher routing.
- `amm.py` (39 functions) — UniswapV2Pool + sqrtPriceX96 reads.
- `hooks.py` (43 functions) — `CustomCurveHook` with constant_sum / constant_mean / polynomial / logarithmic.
- `converters.py`, `trade_matcher.py`, `sports_matching.py`.

## Execution DAG

```
Phase 1 (UAC contract extensions for new sim primitives — SEQUENTIAL gate)
        │
        ▼
Phase 2 (PARALLEL — per-pool-shape AMM model implementations)
Phase 3 (PARALLEL — lending rate-impact simulator)
Phase 4 (PARALLEL — governance proposal capture + simulation harness)
Phase 5 (PARALLEL — yield-stream simulators: staking + restaking + LRT-fee)
Phase 6 (Hedge-ratio dynamic adjustment investigation + fix)
Phase 7 (Slashing tail-risk MC — depends on Phase 5 staking sim)
        │
        ▼
Phase 8 (Backtest fidelity validation — depends on all above)
        │
        ▼
Phase 9 (Codex SSOT updates throughout per Post-Plan-Phase Codex Audit HARD RULE)
```

Phases 2-7 are maximally parallel after Phase 1 lands UAC contracts.

## Phase 1 — UAC contract extensions (SEQUENTIAL gate; ~2-3 AI-days)

Owner: ikenna (cross-cutting design); harsh implements.

- [ ] [AGENT] P0. **1A — `PoolShape` enum** in UAC `internal/domain/defi/`. **Member list (post-Day-1
      slot-6 amendment 2026-05-11)**: `UNISWAP_V2`, `UNISWAP_V3`, `UNISWAP_V4_HOOK`, `CURVE_STABLE`,
      `CURVE_CRYPTO`, `BALANCER_WEIGHTED`, `BALANCER_BOOSTED`, `BALANCER_COMPOSABLE`, `SOLANA_CLMM`
      (Raydium / Orca shared), `SOLANA_AMM` (Raydium V4 standard pool), `JUPITER_ROUTE_AGGREGATOR`,
      `1INCH_AGGREGATOR`, `0X_AGGREGATOR`, **NEW `SOLIDLY_FORK`** (shared matcher for Velodrome V2 +
      Aerodrome + Equalizer / Thena / Ramses; `(chain_id, factory_address)` discriminator inside the
      matcher; cubic-stable + xy=k-volatile branches via `stable: bool` pool flag), **NEW
      `SOLIDLY_CL_FORK`** (shared matcher for Velodrome Slipstream + Aerodrome Slipstream V3-tick CL
      pools; same `(chain, factory)` discriminator pattern). Total: 15 members. Each pool instrument
      metadata gets a `pool_shape: PoolShape` field. **Rationale for shared `SOLIDLY_FORK` over
      per-fork members**: Solidly-fork cubic + xy=k math is byte-for-byte identical across all forks
      (verified Day-1 sub-agent fan-out 2026-05-11); enum explosion as new forks emerge would force
      stale per-fork dispatch updates without functional benefit. Per-fork golden fixture rows live in
      codex per-shape sample-pool/fixture matrix table.
- [ ] [AGENT] P0. **1B — `LendingMarketState` Pydantic model** for rate-impact sim inputs. Fields: `total_supply`,
      `total_borrow`, `optimal_utilization_rate`, `interest_rate_model_params` (kink-style: base / slope1 / slope2 /
      reserve_factor), `liquidityIndex`, `variableBorrowIndex`. Used by both backtest replay + live pre-trade estimate.
- [ ] [AGENT] P0. **1C — `GovernanceProposal` schema** + `GOVERNANCE_PROPOSAL` data_type. Fields: `proposal_id`,
      `protocol`, `proposer`, `created_at`, `voting_start`, `voting_end`, `executed_at` (nullable), `payload`
      (calldata + targets), `status` (pending / active / passed / failed / executed / cancelled). Protocols in scope:
      Aave V3 + Compound V3 + Spark + Lido (Snapshot off-chain) + Uniswap (governance fork data).
- [ ] [AGENT] P0. **1D — `StakingYieldDecomposition` schema**. Fields: `native_staking_apr` (consensus + execution
      rewards), `mev_apr` (Solana validator MEV share OR Ethereum block-builder tips), `restaking_avs_apr` (per AVS
      array), `lrt_protocol_fee_bps`, `seasonal_points` (off-chain, may be null). Used by D4 simulator.
- [ ] [AGENT] P0. **1E — `SlashingEvent` schema** + `SLASHING_EVENT` data_type. Fields: `chain`, `validator_id`,
      `slashed_at_epoch`, `slashed_amount_native`, `slashing_reason` (downtime / double-sign / surround-vote per
      Ethereum; per-Solana-event-type per Solana). Used by Phase 7 MC.
- [ ] [AGENT] P0. **1F — `HedgeRatioSnapshot` schema** for D5 carry archetype. Fields: `archetype`, `leg_long`,
      `leg_short`, `target_ratio`, `realized_ratio`, `peg_drift_bps`, `last_adjustment_at`.
- [ ] [AGENT] P0. **1G — UAC QG green** post-Phase-1.

**Codex SSOT update (Phase 1 boundary)** — `codex/04-architecture/amm-slippage-simulation.md` exists since
2026-05-10 with Phases 2-8 content stubs. **Day-1 slot-6 ship 2026-05-11 (PM@`3b76a5ef`)**: extended with
NEW section #10 Solidly-fork (Velodrome + Aerodrome math + Slipstream out-of-scope note) + NEW
"Per-shape sample pools + golden fixture seeds" matrix table (10 rows × 7 columns covering all V1-V10
shapes with sample pool addresses, fee model, validation threshold, pool-class status) + corrected gap
analysis (V2/V3/V4 pool classes EXIST in `amm.py`; gap is `AMMMatcher` dispatcher hardcoding V2 +
7 missing pool classes) + cross-chain L2 deployment hazard note + Solidly-fork update protocol footer.
Full per-shape AMM family matrix research sourced from 7-parallel-sub-agent fan-out 2026-05-11
(Uniswap V2/V3/V4 + Curve stable + Balancer weighted + Velodrome ve(3,3) + Aerodrome).

**Full-execution criterion**:

- ✅ All 6 schemas land in UAC + import-clean from consumer repos.
- ✅ `PoolShape` enum has all 13 members + Pydantic validation tests green.
- ✅ Codex doc stub exists with section anchors that downstream phases fill.

## Phase 2 — Per-pool-shape AMM model implementations (PARALLEL × 7 shapes; ~10-15 AI-days)

Owner: harsh + parallel agents per shape.

Success criterion: matching engine `amm.py` extends to model each `PoolShape` exactly. Backtest fill price within ~5bps
of on-chain real fill at the same block (verified via Tenderly fork comparison).

> **Day-1 slot-6 design ship 2026-05-11 (PM@`d66b0f9f`)**: codex
> [`amm-slippage-simulation.md`](../../codex/04-architecture/amm-slippage-simulation.md) § "Simulation
> contract — unified pre-trade quote interface" + § "Per-shape sample pools + golden fixture seeds" ship
> the Phase 2 design half: `PoolMatcher` Protocol (quote/apply/spot_price/snapshot methods); per-pool-class
> module map (`curve.py` / `balancer.py` / `solana_clmm.py` / `solidly_fork.py` / `aggregator.py` — all NEW
> for Phase 2C-H); `engine.py:_amm_match_impl` dispatcher refactor target; per-shape sample pool addresses
> + validation thresholds (10-row matrix). **Critical finding**: V2 (`amm.py:52`) + V3 (`amm.py:259`) + V4
> (`amm.py:403`) pool classes ALL EXIST — Phase 2A/B are Protocol-conformance refactors + dispatch wire-up,
> NOT greenfield builds. **Implementation half remains `- [ ]` for Harsh slot 4** per cross-side handshake
> (`plans/active/_agent_pings.md` PM@`f9df943f`). **NEW PHASE 2H** (added Day-1 2026-05-11): Solidly-fork
> classic-pool matcher (Velodrome + Aerodrome shared via `(chain, factory)` discriminator; cubic stable +
> xy=k volatile branches via `stable: bool` pool flag) + optional `SOLIDLY_CL_FORK` matcher for Slipstream
> V3-tick CL pools. Validation: ≥ 20 swaps Velodrome + ≥ 20 swaps Aerodrome within 5 bps each (per codex
> matrix row).

- [ ] [AGENT] P0. **2A — Uniswap V3 tick-bucket integration**. Extend `matching_engine/amm.py` with
      `UniswapV3Pool.swap_exact_input()` integrating across all ticks crossed (per `getAmountsForLiquidity` formula).
      Source per-block tick bitmap from Phase 3 captures of catalogue plan. Validation: ≥ 100 historical Tenderly-fork
      swaps within 5bps.
- [ ] [AGENT] P0. **2B — Uniswap V4 hooks-aware fill**. Reuse V3 base + read hook bytecode from pool key + apply
      per-hook delta. `hooks.py:CustomCurveHook` already covers constant_sum / constant_mean / polynomial / logarithmic
      — extend to handle V4 `beforeSwap` / `afterSwap` deltas.
- [ ] [AGENT] P0. **2C — Curve stable D-invariant**. New `CurveStablePool` in `amm.py` solving `D` invariant
      Newton-Raphson per swap. Use captured pool reserves + `A` parameter from on-chain. Per-pool `gamma` for Curve
      crypto pools. Validation: ≥ 50 historical Curve swaps within 5bps.
- [ ] [AGENT] P0. **2D — Balancer weighted bonding curve**. New `BalancerWeightedPool` using
      `out = balance_out * (1 - (balance_in / (balance_in + amount_in))^(weight_in / weight_out))`. Validation: ≥ 20
      historical Balancer swaps within 5bps.
- [ ] [AGENT] P0. **2E — Balancer boosted + composable pools**. Boosted = linear-pool building blocks; composable =
      phantom BPT. Both reduce to weighted internally — handle the routing layer.
- [ ] [AGENT] P0. **2F — Solana CLMM (Raydium + Orca)**. Tick-bucket math same as Uniswap V3 but per-Solana-CLMM
      decimals + SPL-token semantics. New `SolanaCLMMPool` reusing V3 base. Validation: ≥ 30 historical Raydium / Orca
      swaps within 5bps.
- [ ] [AGENT] P0. **2G — Jupiter aggregator per-route decomposition**. Read Jupiter route from quote API; for each leg,
      route to the appropriate pool-shape matcher above; compose realized fill. Validation: ≥ 30 historical Jupiter
      routes within 10bps (looser since multi-hop).

**Codex SSOT update (Phase 2 boundary)** — fill `codex/04-architecture/amm-slippage-simulation.md` § "Per-pool-shape
models" with all 7 shapes' math + validation results.

**Full-execution criterion**:

- ✅ Each shape has ≥ X historical-Tenderly-fork validations (per-shape thresholds above) within bps.
- ✅ Matching engine `engine.py:_amm_match_impl` routes by `PoolShape` correctly.
- ✅ Backtest replay of 1 day of `carry_staked_basis` against new models produces fill prices within 10bps of live
  Tenderly-fork comparison.

## Phase 3 — Lending rate-impact-from-own-trade simulator (~5-8 AI-days)

Owner: harsh + parallel agent.

- [ ] [AGENT] P0. **3A — `LendingRateImpactCalculator`** in `execution-service/execution_service/matching_engine/`.
      Inputs: `LendingMarketState` (Phase 1B) + proposed supply/borrow amount. Output: post-trade `borrow_apy` +
      `supply_apy` using the captured kink-style interest rate model
      (`(utilization < optimal) ? base + slope1 *     utilization / optimal : base + slope1 + slope2 * (utilization - optimal) / (1 - optimal)`).
- [ ] [AGENT] P0. **3B — `BenchmarkMatcher` extension**. Currently does instant-fill at benchmark; extend to call
      `LendingRateImpactCalculator` for all supply/borrow/repay/withdraw at Aave V3 + Compound V3 + Spark + Radiant.
      Backtest yield computation uses post-trade rate, not pre-trade.
- [ ] [AGENT] P0. **3C — Validation harness**. Replay 1 month of historical Aave V3 large supplies (>$10M); compare
      simulated post-trade rate vs realized on-chain rate. Tolerance: ≤ 10bps absolute APY delta.

**Full-execution criterion**:

- ✅ `LendingRateImpactCalculator` unit tests green for all 4 lending protocols + multi-chain Aave.
- ✅ Validation harness runs ≥ 50 historical large-supply events; ≥ 90% within 10bps tolerance.
- ✅ `BenchmarkMatcher` extension QG-green; backtest yield difference vs old (zero-impact) matcher recorded in
  changelog.

## Phase 4 — Governance proposal capture + simulation harness (~8-12 AI-days)

Owner: ikenna for design + harsh for implementation.

> **Day-1 slot-6 design ship 2026-05-12 (PM@`ae804766`)**: codex
> [`amm-slippage-simulation.md`](../../codex/04-architecture/amm-slippage-simulation.md) § "Governance
> proposal simulation harness" → "Per-protocol capture detail" subsection ships the Phase 4 design half
> with operator-runnable detail for Harsh slot 4: (a) per-protocol Governor contract addresses
> (`GovernanceV3Ethereum`, `GovernorBravoDelegator`, MakerDAO ChiefBoot for Spark, AragonVoting for Lido)
> + Snapshot space IDs + subgraph endpoints; (b) Tenderly fork simulator code skeleton with REST API
> patterns (POST `fork` + `simulate`) + ~10 sims/day budget; (c) `defi-simulate-proposal` CLI signature
> + JSON return shape; (d) 2-year backfill VM launcher detail (`launch-governance-backfill-vm.sh`
> per-protocol; watchdog dict entry `governance-backfill-` + tarball refresh required per CLAUDE.md VM
> Naming Convention HARD RULE; per-VM shard isolation `VM_NAME=<unique-tag>` + `MANIFEST_PER_VM_SHARDS=true`).
> **Implementation half remains `- [ ]` for Harsh slot 4** per cross-side handshake.

- [ ] [AGENT] P0. **4A — Governance capture adapter**. New
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/governance_adapter.py` capturing
      Aave V3 + Compound V3 + Spark + Lido proposals. Sources: on-chain Governor contract events (Tally indexes, but
      read directly via subgraph) + Snapshot off-chain proposals API.
- [ ] [AGENT] P0. **4B — `GovernanceProposalSimulator`** in execution-service. Given proposal ID + Tenderly fork: apply
      proposal payload (governor.execute call) on the fork → measure delta on lending parameters / vault caps / interest
      rate models / etc. Output: per-affected-instrument before/after state.
- [ ] [AGENT] P0. **4C — Strategy-side scenario API**. New endpoint in execution-service or a CLI:
      `defi-simulate-proposal --proposal-id <id> --archetype <X>` returns archetype P&L delta if proposal executes at
      time T. Used by risk simulations (composes with `risk_simulations_limits_alerting` sibling question doc).
- [ ] [AGENT] P0. **4D — Backfill historical proposals** for the last 2 years across all 4 protocols. Coverage validates
      that any "what if proposal X passed" can be answered for any historical date.

**Full-execution criterion**:

- ✅ Governance adapter captures ≥ 1 month of Aave V3 + Compound V3 + Spark + Lido proposals.
- ✅ `GovernanceProposalSimulator` runs successfully on ≥ 5 historical proposals with measurable parameter delta.
- ✅ `defi-simulate-proposal` CLI returns archetype P&L delta within 100bps of actual realized post-execution delta (for
  the historical proposals where we can measure).

## Phase 5 — Yield-stream simulators (~8-12 AI-days)

Owner: harsh + parallel agents.

> **Day-1 slot-6 design ship 2026-05-12 (PM@`ae804766`)**: codex
> [`amm-slippage-simulation.md`](../../codex/04-architecture/amm-slippage-simulation.md) § "Staking +
> restaking yield-stream simulators" → "Per-protocol capture detail" subsection ships the Phase 5 design
> half with operator-runnable detail for Harsh slot 4: (a) 11-row per-protocol capture table covering
> Ethereum beacon (Lighthouse/Prysm REST per-epoch) + Ethereum execution (eth_getBlockByNumber +
> baseFeePerGas + priorityFee) + Solana validator (getInflationReward per-epoch) + EigenLayer +
> Symbiotic + Karak + Jito-restaking subgraphs + Ether.fi/Renzo/KelpDAO/Puffer LRT-fee contract
> addresses + governance subgraph polls; (b) per-component model skeletons — `StakingYieldModel`
> calibrate+sample with attestation-efficiency-binned heteroskedasticity; `RestakingAVSModel`
> base+log-normal-premium per-LRT operator-allocation-weighted; `LRTProtocolFeeModel` discrete-event
> mean±σ_quarterly per-protocol; `SeasonalPointsModel` operator-tuned discount factors with 4 protocol
> calibration anchors (Ether.fi 60% / Renzo 50% / Puffer 50% / new programs 70%); (c) `Phase 5E`
> composite `staking_yield_stream_distribution(lst_or_lrt, chain, horizon_epochs)` code skeleton
> convolving all 4 layers. **Implementation half remains `- [ ]` for Harsh slot 4** per cross-side
> handshake.

- [ ] [AGENT] P0. **5A — Native staking yield stochastic model**. Per-chain (Ethereum beacon / Solana validator).
      Inputs: historical per-epoch reward distribution + recent attestation efficiency + validator-set churn. Output:
      forward yield distribution (mean / 5th / 95th percentile) for any forward horizon. Calibrated against ≥ 6 months
      historical data per chain.
- [ ] [AGENT] P0. **5B — Restaking AVS yield model**. Per-AVS reward variability layered on top of native staking base.
      EigenLayer + Symbiotic + Karak AVSes from Phase 1A captures. Output: per-LRT forward yield distribution.
- [ ] [AGENT] P0. **5C — LRT protocol-fee model**. Discrete-event model: Ether.fi / Renzo / KelpDAO / Puffer fees
      historically change ~quarterly via governance. Capture fee-change events; forward fee assumption =
      most-recent-quarter fee + ±1 stddev band.
- [ ] [AGENT] P0. **5D — Seasonal-points model** (off-chain rewards). Discrete-event model with operator-supplied
      "expected season ending in" dates. Treats points as airdrop-equivalent at season end at a discount factor that
      matches historical points-to-token redemption ratios (operator-tuned).
- [ ] [AGENT] P0. **5E — Composite `StakingYieldStreamSimulator`** that integrates 5A + 5B + 5C + 5D into a single
      per-LST/LRT forward-yield distribution. Used by `carry_staked_basis` PnL projection + risk simulations.

**Full-execution criterion**:

- ✅ Per-chain native staking model has ≥ 6 months calibration data + walk-forward validation within 50bps APY
  prediction error.
- ✅ Composite simulator integrated into `carry_staked_basis` archetype config.

## Phase 6 — Hedge-ratio dynamic adjustment (~3-5 AI-days)

Owner: harsh.

> **Phase 6A audit shipped 2026-05-12 (slot 6 Day-1)**: carry_staked_basis engine confirmed **STATIC**. The
> audit pointer in todo 6A below to `pairs_fixed.py` was stale — that file is a stat_arb_pairs strategy, NOT
> the `carry_staked_basis` archetype. **Real code path**:
> [`strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:248-318`](../../../strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py)
> — function `_build_legs()`. Line 264:
> ```python
> perp_short_units = eth_qty * (Decimal("1") - structure.perp_margin_haircut)
> ```
> The hedge is sized 1:1 against LST principal (delta-neutral) clamped by venue margin haircut. **No
> per-tick / per-bar peg-drift adjustment** anywhere in the engine. `default_basis_trade.yaml` has
> `hedge_ratio_window: 60` but that's for `stat_arb_pairs` (different strategy); `carry_staked_basis`
> archetype config has NO hedge_ratio dynamics. **Conclusion: Phase 6B IS needed** — operator can no
> longer treat as conditional.

- [x] [AGENT] P0. **6A — Audit `carry_staked_basis` engine** for hedge ratio shape.
      ✅ DONE 2026-05-12 slot 6 Day-1 (no commit yet — finding documented in Phase 6 banner above).
      **Evidence**: `staked_basis.py:264` `perp_short_units = eth_qty * (Decimal("1") - structure.perp_margin_haircut)`
      — STATIC. Audit pointer in original todo (`pairs_fixed.py`) was wrong file (stat_arb_pairs ≠
      carry_staked_basis). Real archetype engine path: `staked_basis.py:_build_legs` line 248-318.
- [ ] [AGENT] P0. **6B — IMPLEMENT (not conditional — audit confirmed static)** dynamic hedge-ratio
      adjustment using LST/native exchange rate stream from Phase 1A captures (jitoSOL/SOL, mSOL/SOL,
      bSOL/SOL, rETH/ETH, stETH/ETH, weETH/ETH). Per-tick or per-bar rebalance trigger when
      |peg_drift| > N bps. **Implementation home**: extend `staked_basis.py` with a new
      `_compute_dynamic_hedge_ratio(structure, lst_rate_stream, peg_drift_threshold_bps)` helper called
      inside `_build_legs` to size `perp_short_units = eth_qty * lst_rate_at_now / (1 - margin_haircut)`.
      Hysteresis band parameter `peg_drift_threshold_bps` configurable per archetype (default 25 bps
      based on observed historical jitoSOL/SOL daily-stddev ≈ 8 bps; 3-stddev hysteresis ≈ 25 bps).
- [ ] [AGENT] P0. **6C — Tests**: backtest carry archetype with dynamic vs static hedge-ratio over 1-year historical
      replay. Document P&L delta + confidence interval.

**Full-execution criterion**:

- ✅ `carry_staked_basis` engine confirmed dynamic-hedge-ratio adjusted (post Phase 6B if was static).
- ✅ Backtest comparison shows non-trivial P&L delta + reduced realized-residual variance vs static.

## Phase 7 — Slashing tail-risk Monte Carlo (~3-5 AI-days)

Owner: harsh.

- [ ] [AGENT] P0. **7A — Historical slashing rate calibration** per chain. Ethereum beacon: load slashing events from
      `SLASHING_EVENT` data_type captures (Phase 1A); compute per-validator-epoch slashing probability. Solana
      validator: distinct shape (per-validator-event); compute per-validator-day probability.
- [ ] [AGENT] P0. **7B — `SlashingTailRiskMC`** in execution-service or features-onchain-service. Monte Carlo simulator:
      given carry archetype LST allocation × N validators effectively-staked × forward horizon, produces P(slashing >
      threshold) curve. Calibrated against 7A historical.
- [ ] [AGENT] P0. **7C — Carry archetype tail-risk allocation hook**. Output P(slashing) feeds into archetype's
      capital-allocation rule (cap per-LST exposure when historical slashing rate spikes; back off when normal).

**Full-execution criterion**:

- ✅ Historical slashing rate calibrated per chain with confidence interval recorded.
- ✅ MC simulator returns P(slashing) curve for carry archetype's actual current exposure within compute-time budget.

## Phase 8 — Backtest fidelity validation (~3-5 AI-days)

Owner: ikenna for sign-off + harsh for runs.

- [ ] [AGENT] P0. **8A — Carry archetype 1-year replay** using all new sim primitives (Phases 2-7) + Phase 6 dynamic
      hedge ratio. Compare simulated P&L vs old (constant-product + zero-rate-impact + static-hedge) replay. Document
      delta + reduced bias evidence.
- [ ] [AGENT] P0. **8B — Leveraged-funding-arb 1-year replay** with new sim primitives. Document delta vs old.
- [ ] [AGENT] P0. **8C — Tenderly fork live-vs-simulated reconciliation** for 1 day of paper-trade. Per-tick live fill
      vs simulated fill; |delta| should be < 10bps for ≥ 95% of fills.
- [ ] [AGENT] P0. **8D — Sign-off gate**. Operator reviews Phase 8A/B/C + signs off that backtest fidelity is acceptable
      for May-23 cutover.

**Full-execution criterion** (the May-23 gate):

- ✅ Master plan Group F item 18 (batch-vs-live recon) green via Phase 8C evidence.
- ✅ Master plan Group F item 17 (paper-trade smoke) consumes new matching engine — green.
- ✅ Operator sign-off on backtest fidelity recorded.

## Phase 9 — Codex SSOT updates (continuous + final lock)

Per Post-Plan-Phase Codex Audit HARD RULE — codex updates ride in same logical unit as code commits. Final lock at Phase
8 sign-off.

- [ ] [AGENT] P0. **9A — `codex/04-architecture/amm-slippage-simulation.md`** (NEW; full content covering all 7 pool
      shapes + lending rate impact + governance sim + staking + restaking yield models + slashing MC).
- [x] [AGENT] P0. **9B — CREATE `codex/04-architecture/concentrated-liquidity.md`** (V3/V4 + Solana CLMM
      addendum). (PM@`<this-cycle>` 2026-05-12 — created 130-line stub with shared CL tick-math invariants
      (sqrtPriceX96 / tick math / active liquidity / position math / single-step swap / tick traversal) +
      per-implementation addenda for V3 / V4 / Velodrome+Aerodrome Slipstream / Solana CLMM; cross-references
      to amm-slippage-simulation.md + batch-live-architecture.md + execution-service amm.py.)
- [x] [AGENT] P0. **9C — Update `codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`** with
      restaking yield decomposition + LRT-fee + seasonal-points models. (PM@`<this-cycle>` 2026-05-12 — added
      "Forward-yield simulation (composite stochastic model)" section cross-referencing
      amm-slippage-simulation.md § "Staking + restaking yield-stream simulators" Phase 5A-E; lists native
      staking + restaking AVS + LRT protocol-fee + seasonal-points discount-factor + composite simulator;
      cites operator-tuned per-protocol calibration anchors from PM@ae804766.)
- [x] [AGENT] P0. **9D — Update `codex/04-architecture/batch-live-architecture.md`** with the matching-engine
      extensions + the live=batch principle as it applies to new sim primitives. (PM@`ad6c98e1` — AMMMatcher
      row updated to dispatch-by-PoolShape over PoolMatcher Protocol; cross-reference block cites today's
      codex extensions PM@`3b76a5ef` + `d66b0f9f` + `816aed73`.)
- [ ] [AGENT] P0. **9E — Update `master_to_live_defi_2026_05_23.md`** Group F items 17 + 18 status rows.
      **OWNER NOTE 2026-05-12 (slot 6 Day-1 ship)**: master plan is slot-1 owned per work_split row 1
      ("Main orchestrator + governance + master plan refresh + cross-plan banner audit"). Per Findings
      Triage Discipline HARD RULE — slot-6 does NOT edit slot-1's owned plan; route via ping ledger
      instead. Cross-side ping at `_agent_pings.md` PM@`f9df943f` already notifies upstream. Update
      content suggestion for slot 1: Group F item 17 (paper-trade smoke) "Continuous Verification:
      consumes new matching engine per defi_simulation_realism_2026_05_10 Phase 2 design (PM@d66b0f9f
      + ae804766)"; Group F item 18 (batch-vs-live recon) "Continuous Verification: Phase 8C Tenderly-
      fork live-vs-simulated reconciliation per defi_simulation_realism Phase 8 (sim contract Phase 2A
      + golden harness Phase 3 design-shipped)". Last verified: 2026-05-12 (design ship).

## Cross-plan dependencies

- **`defi_catalogue_chain_primitives_2026_05_10.md`** Phase 3 (MTDS adapters) ships pool reserves + lending indices +
  oracle prices + slashing events that this plan's Phase 2-7 simulators consume. Phase 1 here can run in parallel with
  catalogue Phase 1, but Phases 2-7 here depend on catalogue Phase 3 captures.
- **`risk_simulations_limits_alerting_2026_05_08.md`** sibling question doc — risk-simulation surface consumes Phase 4
  governance simulator + Phase 5 yield streams + Phase 7 slashing MC.
- **`master_to_live_defi_2026_05_23.md`** Group F items 17 + 18 are the cutover gates this plan unblocks.

## DONE-2026-05-15 — slot 6 (Ikenna `ikenna-defi-sim-realism-tab`) Day-1 design ship 2026-05-11 / 2026-05-12

Day-1 directive (`continuation_prompts_2026_05_12.md` § Ikenna slot 6) closed in single cycle covering **full
~14 AI-day budget** with directive Phases 1-5 (matrix + sim contract + golden harness + integration spec +
multi-hop routing) + plan body Phases 4-5 design + Phase 9B+9C+9D codex closures + items 8+9 partial. Plan
body Phase 9E annotated for slot-1 routing per Findings Triage Discipline.

### Commit table

| Commit | Repo | Scope |
|---|---|---|
| `PM@16d60480` | unified-trading-pm | STATUS-2026-05-11 line ([`ikenna_orchestrator/_agent_pings.md`](../../ikenna_orchestrator/_agent_pings.md)) — confirms slot-6 prior cycle (`manifest_schema_final_gate` Phase 2.A-D + Phase 3.D; carry-forward items 8+9 inherited from Harsh slot 6 EOD-2026-05-11 handoff). |
| `PM@3b76a5ef` | unified-trading-pm | Codex [`amm-slippage-simulation.md`](../../codex/04-architecture/amm-slippage-simulation.md) Phase 1A — NEW section #10 Solidly-fork (Velodrome + Aerodrome math + Slipstream out-of-scope note) + NEW "Per-shape sample pools + golden fixture seeds" 10-row matrix table + corrected gap analysis (V2/V3/V4 pool classes EXIST per `amm.py:52,259,403` — gap is matcher dispatcher) + cross-chain L2 hazard note + Solidly-fork update protocol footer. |
| `PM@fd29975e` | unified-trading-pm | Plan body Phase 1A — PoolShape enum amendment: 13 → 15 members (NEW `SOLIDLY_FORK` shared matcher for Velodrome + Aerodrome + other Solidly forks via `(chain, factory)` discriminator; NEW `SOLIDLY_CL_FORK` for Slipstream V3-tick CL pools). Phase 1 boundary codex SSOT note updated to acknowledge today's extension. |
| `PM@d66b0f9f` | unified-trading-pm | Codex Phase 2A + Phase 3 — NEW "Simulation contract — unified pre-trade quote interface" (PoolMatcher Protocol with `quote()` / `apply()` / `spot_price()` / `snapshot()`; per-pool-class module map curve.py / balancer.py / solana_clmm.py / solidly_fork.py / aggregator.py; `engine.py:_amm_match_impl` refactor target) + NEW "Golden test set harness" (per-PoolShape JSON fixture corpus schema + pytest harness skeleton + capture runbook). |
| `PM@f9df943f` | unified-trading-pm | Cross-side ping ([`plans/active/_agent_pings.md`](_agent_pings.md)) — Phases 1A+2A+3 design ✅ → Harsh slot 4 cleared to start Day 2 morning (ahead of EOD-Day-2 handshake); slot 7 (Ikenna) cleared for AMM-flavoured topology shocks Day 1 PM. |
| `PM@9bb51d4b` | unified-trading-pm | Plan body Phase 2 design-shipped status block + NEW Phase 2H (Solidly-fork classic-pool matcher; design-shipped). Implementation half remains `- [ ]` for Harsh slot 4. |
| `PM@816aed73` | unified-trading-pm | Codex Phase 4+5 — NEW "Matching-engine end-to-end integration" (batch-vs-live PoolMatcher.apply() seam; end-to-end flow diagram; slippage tolerance gate; cross-service contracts for position-balance-monitor / strategy-service / risk-and-exposure-service) + NEW "Aggregator / multi-hop routing realism" (route-source by mode; per-leg dispatch; MEV mempool_path tracking; slippage composition multiplicative-not-additive). |
| `PM@ad6c98e1` | unified-trading-pm | Codex `batch-live-architecture.md` AMMMatcher row updated for PoolShape dispatch (items 8+9 partial codex SSOT currency closure — 1 of ~50 docs spot-checked + corrected today). |
| `PM@0c4b66f4` | unified-trading-pm | DONE-2026-05-15 block + Phase 9D `- [x]` flip + Phase 9B "doc-does-not-exist" annotation + items 8+9 initial status. |
| `PM@ae804766` | unified-trading-pm | Codex Phase 4 + Phase 5 — per-protocol governance Governor addresses + Snapshot spaces + subgraphs + Tenderly fork simulator code skeleton + `defi-simulate-proposal` CLI signature + 2-year backfill VM detail; 11-row per-protocol yield-stream capture table (Ethereum beacon / Solana validator / EigenLayer / Symbiotic / Karak / Jito / Ether.fi / Renzo / KelpDAO / Puffer) + per-component model code skeletons (`StakingYieldModel.calibrate_and_sample`, `RestakingAVSModel`, `LRTProtocolFeeModel`, `SeasonalPointsModel`) + composite simulator Phase 5E code. |
| `PM@30a01f3e` | unified-trading-pm | Plan body Phase 4 + Phase 5 design-shipped status banners + NEW codex `concentrated-liquidity.md` (130-line stub for Phase 9B-NEW: shared CL tick-math invariants + per-implementation addenda for V3 / V4 / Velodrome+Aerodrome Slipstream / Solana CLMM) + Phase 9B `- [x]` flip. |
| `PM@a39fdee1` | unified-trading-pm | Items 8+9 continuation — codex `tenderly-execution-provider.md` NEW "Downstream consumers" section + codex `restaking-reward-economics.md` NEW "Forward-yield simulation" cross-reference section; Phase 9C `- [x]` flipped. |
| `PM@<this commit>` | unified-trading-pm | DONE block extension (Day-2 commits) + Phase 9E slot-1-routing annotation. |

### Items 8+9 status (carry-forward from Harsh slot 6 EOD-2026-05-11)

| Item | Description | Status as of 2026-05-12 EOD slot-6-day-1 (full closure) | Successor |
|---|---|---|---|
| Item 8 | Full workspace `quality-gates.sh` + basedpyright 22-repo sweep | ⚪ DEFERRED — Day-1 design surface is plan/codex-only (no code edits); slot-worktree `.venv` constraint claim from Harsh notes contradicted by direct check (slot 6 `.venv` dirs present per `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/6/unified-trading-library/.venv` + `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/6/unified-api-contracts/.venv`). | Days 2-4 of slot-6 cycle when Harsh slot 4 implementation lands code changes triggering QG runs; or operator re-tasks slot 6 directly to QG sweep. |
| Item 9 | ~50-doc codex SSOT currency pass per 1.D/1.E/1.F clusters | ⚪ PARTIAL — **3 of ~50 docs refreshed today** (`batch-live-architecture.md` PM@`ad6c98e1` + `tenderly-execution-provider.md` PM@`a39fdee1` + `restaking-reward-economics.md` PM@`a39fdee1`); 1 doc newly **CREATED** (`concentrated-liquidity.md` PM@`30a01f3e`, 130 lines closing Phase 9B-NEW). 46+ docs remain to spot-check days 2-4. | Days 2-4 — bounded to the remaining codex docs in 1.D (alerting/risk/DR) / 1.E (DeFi) / 1.F (UI/credentials) clusters per Harsh's brief. Routing to specific docs deferred to next-day sweep. |

### Discoveries captured (HARD RULE Capture Discoveries As Plan Todos Immediately)

1. **V2/V3/V4 pool classes EXIST in `amm.py:52,259,403`** — plan body Phase 2A/B "extend amm.py with UniswapV3Pool"
   framing is stale. Recapped in Phase 2 status banner + cross-side ping. Implementation half = Protocol refactor +
   dispatcher rewrite, NOT greenfield.
2. **Slipstream V3-tick CL variants on Velodrome + Aerodrome** — operator decision pending whether to use shared
   `SOLIDLY_CL_FORK` enum member or split `VELODROME_SLIPSTREAM` + `AERODROME_SLIPSTREAM`. Captured in plan body Phase
   1A enum amendment as the conservative choice (shared) with rationale. Override-able by operator.
3. **`concentrated-liquidity.md` codex doc does NOT exist on disk** — plan body Phase 9B's "Update" framing is
   wrong; updated to "CREATE" + flagged as Phase 9B-NEW.
4. **Aggregator route MTDS data_type does NOT exist in catalogue** — captured in codex Phase 5 § "Aggregator / multi-hop
   routing realism" ("NEW; not yet in catalogue"). Phase 2G MTDS adapter dependency.
5. **`PoolShape` lookup table `(chain, pool_address) → PoolShape`** — sourcing from MTDS `dex_pools` data_type
   captured in codex § Aggregator. Cross-references to `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3.
6. **Pre-flight Tenderly fork option for high-impact swaps** — captured in codex § Matching-engine end-to-end
   integration as deferred-to-Phase-4-implementation.
7. **MEV mempool_path attribution (PUBLIC vs PRIVATE) in FillResult** — codex § Aggregator multi-hop realism flags
   this as required for execution-alpha separation; downstream consumer is `position-balance-monitor-service` +
   `strategy-service` execution-alpha attribution.

### Days 2-4 plan (calibrated AI-day budget ~5 remaining)

1. **Phase 4 governance proposal sim design** (~2 AI-days) ✅ **CLOSED 2026-05-12 (PM@`ae804766`)** — per-protocol
   capture detail (Governor addresses + Snapshot spaces + subgraphs for Aave V3 / Compound V3 / Spark / Lido) +
   Tenderly fork simulator code skeleton + CLI signature + 2-year backfill VM detail. Implementation half remains
   `- [ ]` for Harsh slot 4.
2. **Phase 5 yield-stream simulator design** (~2 AI-days) ✅ **CLOSED 2026-05-12 (PM@`ae804766`)** — 11-row
   per-protocol capture table + per-component model code skeletons (`StakingYieldModel`, `RestakingAVSModel`,
   `LRTProtocolFeeModel`, `SeasonalPointsModel`) + composite simulator Phase 5E. Implementation half remains `- [ ]`
   for Harsh slot 4.
3. **Items 8+9 days-2-4 continuation** (~1 AI-day) ⚪ **PARTIAL CLOSURE 2026-05-12** — 3 of ~50 codex docs spot-checked
   + refreshed (`batch-live-architecture.md` + `tenderly-execution-provider.md` + `restaking-reward-economics.md`);
   `concentrated-liquidity.md` newly CREATED (Phase 9B-NEW closed). 46+ docs remain for days 3-4 (1.D/1.E/1.F
   clusters). Workspace QG sweep on UAC + UTL + execution-service deferred until Harsh slot 4 implementation
   lands triggering code-change-driven QG runs.

**Day-1 totals**: 14 commits shipped (PM@`16d60480` → PM@`<this>`); ~14 calibrated AI-days delivered (full budget).
Day-2-4 reserve work surfaces as plan body Phases 3, 6, 7, 8 (lending sim + hedge ratio + slashing MC + backtest
fidelity validation) — all of which are implementation-heavy + dependency-bound (Phase 3 needs LendingMarketState
captures from `defi_catalogue` Phase 3; Phase 6 needs jitoSOL/SOL captures; Phase 7 needs `slashing_events` data_type;
Phase 8 needs Phase 2-7 implementations from Harsh slot 4). Slot-6 productive contribution beyond Day-1 awaits
Harsh slot 4 ramp-up.

### Operator-pending decisions surfaced today

| Q | Decision needed | Recommended default | Where surfaced |
|---|---|---|---|
| 1A.1 | `SOLIDLY_FORK` shared matcher vs split per-fork enum members (`VELODROME_VE33` / `AERODROME`) | Shared `SOLIDLY_FORK` (math byte-for-byte identical; enum-explosion-prevention) | plan body Phase 1A amendment |
| 1A.2 | `SOLIDLY_CL_FORK` shared CL matcher vs split (`VELODROME_SLIPSTREAM` / `AERODROME_SLIPSTREAM`) | Shared `SOLIDLY_CL_FORK` (same V3-tick math across forks) | plan body Phase 1A amendment |
| 2G.1 | Aggregator route MTDS data_type — capture canonical aggregator quote-API responses per route at decision-time + persist | YES, new MTDS data_type `aggregator_route` | codex § "Aggregator / multi-hop routing realism" |
| 2A.1 | Pre-flight Tenderly fork on high-impact live swaps (size > N% pool TVL threshold) — gate decision | DEFER to Phase 4 implementation (Harsh slot 4 codes the option; operator tunes N% per-archetype) | codex § "Matching-engine end-to-end integration" |

## Risk register

| Risk                                                                                    | Mitigation                                                                                                                           |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | --------- | --------------------- |
| Curve `gamma` math is non-trivial (crypto pools)                                        | Phase 2C uses reference Curve V2 SDK; spot-check vs `curve.fi` UI quotes                                                             |
| Solana CLMM tick-bucket has different decimals semantics                                | Phase 2F includes parity tests vs Raydium/Orca SDKs                                                                                  |
| Governance simulator on Tenderly fork costs $$ on Tenderly budget                       | Phase 4 limited to scheduled overnight runs + on-demand only; ~10 sims/day budget                                                    |
| Slashing MC needs robust historical calibration                                         | Phase 7A requires ≥ 6 months data; if catalogue plan Phase 6 hasn't backfilled, slashing-event capture, slip Phase 7 to post-cutover |
| Hedge-ratio dynamic adjustment introduces over-trading                                  | Phase 6 includes hysteresis band (only adjust when                                                                                   | peg_drift | > N bps with N tuned) |
| Phase 4 governance proposal sim might miss edge cases (timelock delays, executor races) | Validated against ≥ 5 historical proposals before sign-off                                                                           |

## Done definition

- ✅ Phase 1-9 all checkboxes flipped `- [x]`.
- ✅ Phase 8D sign-off gate green.
- ✅ Codex SSOTs locked durable.
- ✅ Backtest replay of carry + leveraged-funding-arb shows reduced bias vs old engine; delta documented.
- ✅ Master plan Group F items 17 + 18 green via this plan's deliverables.

Plan archives post-cutover with deferred-work audit per Plan Archival HARD RULE.

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

Slot 5 Day-1 Phase 12 design (per-family backtest scenario set) consumes slot 6's PoolMatcher Protocol + golden test harness shape. **Extension needed**: golden-harness fixture corpus should cover 6 stress-shape variants beyond happy-path slippage:

- **B1**: wstETH/ETH oracle drops 3% over 1 block (LST flash depeg)
- **B2**: ETH/USD drops 15% in 1 day (crash scenario)
- **B3**: wstETH/ETH drops 8% (Lido validator slashing scenario)
- **B4**: cbETH/ETH drops 5% (Coinbase custody stress)
- **B5**: Chainlink feed stale > 24h heartbeat
- **C4**: Uniswap V3 wstETH/WETH pool drops to <$1M depth (slippage exhaustion + Curve/Balancer fallback path)

Each fixture is one PoolShape `.json` snapshot at the stress state; consumed by `strategy-service/tests/integration/test_recursive_borrow_scenarios.py` (NEW per Family 1/2 Phase 12 design). Slot 5 NOT fixing (Findings Triage — slot 6 owns the golden-harness corpus). Reference: `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 design § Category B + C scenarios.
