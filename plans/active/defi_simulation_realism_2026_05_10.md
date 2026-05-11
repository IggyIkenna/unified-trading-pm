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

- [ ] [AGENT] P0. **1A — `PoolShape` enum** in UAC `internal/domain/defi/`. Members: `UNISWAP_V2`, `UNISWAP_V3`,
      `UNISWAP_V4_HOOK`, `CURVE_STABLE`, `CURVE_CRYPTO`, `BALANCER_WEIGHTED`, `BALANCER_BOOSTED`, `BALANCER_COMPOSABLE`,
      `SOLANA_CLMM` (Raydium / Orca shared), `SOLANA_AMM` (Raydium V4 standard pool), `JUPITER_ROUTE_AGGREGATOR`,
      `1INCH_AGGREGATOR`, `0X_AGGREGATOR`. Each pool instrument metadata gets a `pool_shape: PoolShape` field.
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

**Codex SSOT update (Phase 1 boundary)** — stub `codex/04-architecture/amm-slippage-simulation.md` (NEW) with section
headers for Phases 2-8 deliverables; full content lands at each phase boundary.

**Full-execution criterion**:

- ✅ All 6 schemas land in UAC + import-clean from consumer repos.
- ✅ `PoolShape` enum has all 13 members + Pydantic validation tests green.
- ✅ Codex doc stub exists with section anchors that downstream phases fill.

## Phase 2 — Per-pool-shape AMM model implementations (PARALLEL × 7 shapes; ~10-15 AI-days)

Owner: harsh + parallel agents per shape.

Success criterion: matching engine `amm.py` extends to model each `PoolShape` exactly. Backtest fill price within ~5bps
of on-chain real fill at the same block (verified via Tenderly fork comparison).

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

- [ ] [AGENT] P0. **6A — Audit `carry_staked_basis` engine** for hedge ratio shape. Read
      `strategy-service/strategy_service/engine/strategies/v2/stat_arb_pairs/pairs_fixed.py` + carry archetype config in
      `configs/defaults/default_basis_trade.yaml`. Confirm: static fixed ratio? Or dynamic-adjusted? File:line evidence.
- [ ] [AGENT] P0. **6B — If static**: implement dynamic hedge-ratio adjustment using LST/SOL exchange rate stream from
      Phase 1A captures (jitoSOL/SOL, mSOL/SOL, bSOL/SOL, rETH/ETH, stETH/ETH, weETH/ETH). Per-tick or per-bar rebalance
      trigger when |peg_drift| > N bps.
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
- [ ] [AGENT] P0. **9B — Update `codex/04-architecture/concentrated-liquidity.md`** (V3/V4 + Solana CLMM addendum).
- [ ] [AGENT] P0. **9C — Update `codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`** with
      restaking yield decomposition + LRT-fee + seasonal-points models.
- [ ] [AGENT] P0. **9D — Update `codex/04-architecture/batch-live-architecture.md`** with the matching-engine
      extensions + the live=batch principle as it applies to new sim primitives.
- [ ] [AGENT] P0. **9E — Update `master_to_live_defi_2026_05_23.md`** Group F items 17 + 18 status rows.

## Cross-plan dependencies

- **`defi_catalogue_chain_primitives_2026_05_10.md`** Phase 3 (MTDS adapters) ships pool reserves + lending indices +
  oracle prices + slashing events that this plan's Phase 2-7 simulators consume. Phase 1 here can run in parallel with
  catalogue Phase 1, but Phases 2-7 here depend on catalogue Phase 3 captures.
- **`risk_simulations_limits_alerting_2026_05_08.md`** sibling question doc — risk-simulation surface consumes Phase 4
  governance simulator + Phase 5 yield streams + Phase 7 slashing MC.
- **`master_to_live_defi_2026_05_23.md`** Group F items 17 + 18 are the cutover gates this plan unblocks.

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
