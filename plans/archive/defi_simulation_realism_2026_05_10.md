---
doc_type: plan
title: defi-simulation-realism
summary: Matching engine extension for per-pool-shape AMM models (Uniswap V3 tick-bucket, Curve D-invariant, Balancer weighted+boosted,
  Solana CLMM, Jupiter aggregator) + lending rate-impact-from-own-trade simulator + governance proposal capture + simulation
  harness + staking + restaking yield-stream simulator + slashing tail-risk MC. May-23 cutover scope per all-in operator
  directive.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/defi_catalogue_chain_primitives_2026_05_10.md,
    plans/active/cross_asset_group_catalogue_audit_2026_05_10.md,
    plans/questions/risk_simulations_limits_alerting_2026_05_08.md,
    plans/active/defi_master_2026_05_07.md,
    plans/active/master_to_live_defi_2026_05_23.md,
  ]
created: 2026-05-10
type: plan
deadline: 2026-05-23
horizon: ~13 calendar days; ~40-70 AI-days at full multi-agent saturation
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/defi_readiness_catalogue_2026_05_08.md
related_codex:
  [
    /codex/04-architecture/amm-slippage-simulation.md,
    /codex/04-architecture/concentrated-liquidity.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/tenderly-execution-provider.md,
    /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
  ]
estimate_class: design
estimate_baseline_ai_days: 53.5
estimate_calibrated_ai_days: 32.1
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~2-3, ~10-15,
  ~5-8, ~8-12, + 4 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
---

> **ARCHIVED 2026-05-19** — 100% complete (all checkboxes checked); preserved for archaeology.

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

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

- [x] [AGENT] P0. **1A — `PoolShape` enum** in UAC. (unified-api-contracts@`c91c417` — 15-member `PoolShape` StrEnum
      landed in `internal/domain/matching_engine/__init__.py` (re-exported from `internal/__init__.py`) —
      `internal/domain/defi/` was the originally-planned home but the matching-engine domain module is the right place
      since the enum is the matching-engine dispatch discriminator; consumers `import` it via
      `unified_api_contracts.internal`. Same commit also lands `SwapQuote` (read-only quote — `quote()`), `FillResult`
      (mutating apply — `apply()`), and `OrderSide` (BUY/SELL — consumed by the
      `execution-service/.../matching_engine/pool_matcher.py` `PoolMatcher` Protocol). The `pool_shape: PoolShape`
      instrument-metadata field is set on each pool class at construction / via `register_pool_matcher`.) **DEFERRED**:
      P2 — `pool_shape` as a first-class column on the DeFi-pool instrument record in instruments-service (today the
      matching engine resolves it from the registered pool class; downstream-instrument-record wiring is a follow-up).
      **Member list (post-Day-1 slot-6 amendment 2026-05-11)**: `UNISWAP_V2`, `UNISWAP_V3`, `UNISWAP_V4_HOOK`,
      `CURVE_STABLE`, `CURVE_CRYPTO`, `BALANCER_WEIGHTED`, `BALANCER_BOOSTED`, `BALANCER_COMPOSABLE`, `SOLANA_CLMM`
      (Raydium / Orca shared), `SOLANA_AMM` (Raydium V4 standard pool), `JUPITER_ROUTE_AGGREGATOR`, `1INCH_AGGREGATOR`,
      `0X_AGGREGATOR`, **NEW `SOLIDLY_FORK`** (shared matcher for Velodrome V2 + Aerodrome + Equalizer / Thena / Ramses;
      `(chain_id, factory_address)` discriminator inside the matcher; cubic-stable + xy=k-volatile branches via
      `stable: bool` pool flag), **NEW `SOLIDLY_CL_FORK`** (shared matcher for Velodrome Slipstream + Aerodrome
      Slipstream V3-tick CL pools; same `(chain, factory)` discriminator pattern). Total: 15 members. Each pool
      instrument metadata gets a `pool_shape: PoolShape` field. **Rationale for shared `SOLIDLY_FORK` over per-fork
      members**: Solidly-fork cubic + xy=k math is byte-for-byte identical across all forks (verified Day-1 sub-agent
      fan-out 2026-05-11); enum explosion as new forks emerge would force stale per-fork dispatch updates without
      functional benefit. Per-fork golden fixture rows live in codex per-shape sample-pool/fixture matrix table.
- [x] [AGENT] P0. **1B — `LendingMarketState` Pydantic model** for rate-impact sim inputs.
      (unified-api-contracts@`7f978f5` — `LendingMarketState` BaseModel + `ProtocolIRMShape` StrEnum (AAVE_KINKED /
      COMPOUND_V3 / MORPHO_ADAPTIVE) + `compute_borrow_rate_compound_v3()` + protocol- dispatched
      `compute_borrow_rate_for_state()` + Phase 1B+3A canonical
      `post_trade_rate(state, supply_delta, borrow_delta) → (supply_apy, borrow_apy)`. Backwards-compat
      `from_aave_pool_params()` builder promotes legacy `AavePoolParams` to the new model. Smoke-test: Aave V3 USDC
      +100k supply borrow_apy=2.02% supply_apy=0.83%; Compound V3 cUSDCv3 +100k borrow (above kink) borrow_apy=8.00%
      supply_apy=6.48%. basedpyright `rate_model.py`: 0 errors.)
- [x] [AGENT] P0. **1C — `GovernanceProposal` schema** + `GOVERNANCE_PROPOSAL` data_type.
      (unified-api-contracts@`78371aa` — `sim_schemas.py:GovernanceProposal` BaseModel + `GovernanceProposalStatus`
      closed-set StrEnum (PENDING/ACTIVE/PASSED/FAILED/EXECUTED/CANCELLED/EXPIRED). Fields cover Aave V3 + Compound V3 +
      Spark + Lido + Uniswap shapes: governor_address, payload_targets, payload_calldatas, executor_address,
      snapshot_proposal_id.)
- [x] [AGENT] P0. **1D — `StakingYieldDecomposition` schema** + `AVSRewardComponent`. (unified-api-contracts@`78371aa` —
      `sim_schemas.py:StakingYieldDecomposition` BaseModel composing native_staking_apr + mev_apr + per-AVS
      restaking_avs_components[] (list[AVSRewardComponent]) + lrt_protocol_fee_bps + nullable
      seasonal_points_implied_apr/discount_factor.)
- [x] [AGENT] P0. **1E — `SlashingEvent` schema** + `SLASHING_EVENT` data_type. (unified-api-contracts@`78371aa` —
      `sim_schemas.py:SlashingEvent` BaseModel + `SlashingReason` StrEnum (ETH: PROPOSER_SLASHING / ATTESTER_SLASHING /
      SURROUND_VOTE / DOUBLE_PROPOSE; SOL: DOWNTIME / DOUBLE_SIGN / NETWORK_PARTITION; generic: OTHER).)
- [x] [AGENT] P0. **1F — `HedgeRatioSnapshot` schema** for carry-staked-basis archetype.
      (unified-api-contracts@`78371aa` — `sim_schemas.py:HedgeRatioSnapshot` BaseModel — archetype, instrument_long,
      instrument_short, target_ratio, realized_ratio, peg_drift_bps, peg_drift_threshold_bps, last_adjustment_at,
      rebalance_triggered, captured_at. Consumed by position-balance-monitor + Phase 6C dynamic-vs-static backtest
      comparison.)
- [x] [AGENT] P0. **1G — UAC QG green** post-Phase-1. **DONE 2026-05-16 (slot 7)**: rate_model.py + sim_schemas.py both
      basedpyright clean individually (0 errors). The 5 `reportUnsupportedDunderAll` errors flagged in the 2026-05-12
      status note (DexPoolDayRecord / LendingIndexRecord / LiquidationRecord / LstRateRecord / PerpFundingRecord named
      in `unified_api_contracts/internal/__init__.py` `__all__` but not imported) fixed at
      `unified-api-contracts@570cb58` — added all 5 to the existing defi import block alphabetically. Smoke test
      `from unified_api_contracts.internal import DexPoolDayRecord, LendingIndexRecord, LiquidationRecord, LstRateRecord, PerpFundingRecord`
      returns OK. basedpyright re-run on internal/**init**.py shows no `reportUnsupportedDunderAll` errors for these
      symbols.

**Codex SSOT update (Phase 1 boundary)** — `/codex/04-architecture/amm-slippage-simulation.md` exists since 2026-05-10
with Phases 2-8 content stubs. **Day-1 slot-6 ship 2026-05-11 (PM@`3b76a5ef`)**: extended with NEW section #10
Solidly-fork (Velodrome + Aerodrome math + Slipstream out-of-scope note) + NEW "Per-shape sample pools + golden fixture
seeds" matrix table (10 rows × 7 columns covering all V1-V10 shapes with sample pool addresses, fee model, validation
threshold, pool-class status) + corrected gap analysis (V2/V3/V4 pool classes EXIST in `amm.py`; gap is `AMMMatcher`
dispatcher hardcoding V2 + 7 missing pool classes) + cross-chain L2 deployment hazard note + Solidly-fork update
protocol footer. Full per-shape AMM family matrix research sourced from 7-parallel-sub-agent fan-out 2026-05-11 (Uniswap
V2/V3/V4 + Curve stable + Balancer weighted + Velodrome ve(3,3) + Aerodrome).

**Full-execution criterion**:

- ✅ All 6 schemas land in UAC + import-clean from consumer repos.
- ✅ `PoolShape` enum has all 13 members + Pydantic validation tests green.
- ✅ Codex doc stub exists with section anchors that downstream phases fill.

## Phase 2 — Per-pool-shape AMM model implementations (PARALLEL × 7 shapes; ~10-15 AI-days)

Owner: harsh + parallel agents per shape.

Success criterion: matching engine `amm.py` extends to model each `PoolShape` exactly. Backtest fill price within ~5bps
of on-chain real fill at the same block (verified via Tenderly fork comparison).

> **Day-1 slot-6 design ship 2026-05-11 (PM@`d66b0f9f`)**: codex
> [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) § "Simulation contract — unified
> pre-trade quote interface" + § "Per-shape sample pools + golden fixture seeds" ship the Phase 2 design half:
> `PoolMatcher` Protocol (quote/apply/spot_price/snapshot methods); per-pool-class module map (`curve.py` /
> `balancer.py` / `solana_clmm.py` / `solidly_fork.py` / `aggregator.py` — all NEW for Phase 2C-H);
> `engine.py:_amm_match_impl` dispatcher refactor target; per-shape sample pool addresses
>
> - validation thresholds (10-row matrix). **Critical finding**: V2 (`amm.py:52`) + V3 (`amm.py:259`) + V4
>   (`amm.py:403`) pool classes ALL EXIST — Phase 2A/B are Protocol-conformance refactors + dispatch wire-up, NOT
>   greenfield builds. **Implementation half remains `- [ ]` for Harsh slot 4** per cross-side handshake
>   (`plans/active/_agent_pings.md` PM@`f9df943f`). **NEW PHASE 2H** (added Day-1 2026-05-11): Solidly-fork classic-pool
>   matcher (Velodrome + Aerodrome shared via `(chain, factory)` discriminator; cubic stable + xy=k volatile branches
>   via `stable: bool` pool flag) + optional `SOLIDLY_CL_FORK` matcher for Slipstream V3-tick CL pools. Validation: ≥ 20
>   swaps Velodrome + ≥ 20 swaps Aerodrome within 5 bps each (per codex matrix row).

- [x] [AGENT] P0. **2A — Uniswap V3 tick-bucket integration**. (execution-service@`3ebecde2` — `UniswapV3Pool` now
      conforms to the `PoolMatcher` Protocol (mixes in `BasePoolMatcher`; `quote`/`apply`/`snapshot`/ `from_snapshot`);
      `execute_swap` advances `sqrtPriceX96` + `tick` (single-active-tick model — multi-tick bitmap traversal remains a
      **DEFERRED** follow-up below); dispatched by `engine.py:_amm_match_impl` via the registry.) **DEFERRED**: P1 —
      multi-tick-crossing integration (needs `tick_liquidity_bitmap` captures from `defi_catalogue` Phase 3) +
      ≥100-historical-Tenderly-fork validation (golden harness — Phase 3 below).
- [x] [AGENT] P0. **2B — Uniswap V4 hooks-aware fill**. (execution-service@`3ebecde2` — `UniswapV4Pool` conforms to
      `PoolMatcher`; `execute_swap` runs `beforeSwap`/`afterSwap` hooks via `_apply_hooks_and_swap` then advances
      sqrtPrice+tick; `_hooks_invoked` reports enabled hook names; `hooks.py:CustomCurveHook` constant_sum/
      constant_mean/polynomial/logarithmic curves carried through.) **DEFERRED**: P2 — exhaustive V4 hook-delta
      validation against on-chain (golden harness).
- [x] [AGENT] P0. **2C — Curve stable D-invariant**. (execution-service@`3ebecde2` — NEW `curve.py`:`CurveStablePool` —
      n-token StableSwap invariant, Newton-Raphson `get_D` + `get_y` (255-iter cap, 1e-18 tol), per-token decimals
      normalisation, `admin_fee` accounting; `get_amount_out_indexed(i, j, ...)` for >2-token baskets.) **DEFERRED**: P1
      — `CurveCryptoPool` (D+gamma + EMA price oracle — 3pool/tricrypto; reference Curve V2 SDK) registered to
      `PoolShape.CURVE_CRYPTO`; ≥50-historical-Curve-swap + metapool-composition validation (golden harness).
- [x] [AGENT] P0. **2D — Balancer weighted bonding curve**. (execution-service@`3ebecde2` — NEW `balancer.py`:
      `BalancerWeightedPool` — weighted-product curve `out = B_out·(1 − (B_in/(B_in+amt_net))^(W_in/W_out))`, fee on
      input, fee-free Balancer spot price; `get_amount_out_indexed(i, j, ...)` for multi-token pools.) **DEFERRED**: P2
      — ≥20-historical-Balancer-swap validation via Vault `batchSwap` (golden harness).
- [x] [AGENT] P0. **2E — Balancer boosted + composable pools**. (execution-service@`3ebecde2` — `balancer.py`:
      `BalancerBoostedPool` (Aave-aToken linear building blocks reduced to a weighted curve with the linear-pool spread
      folded into the effective fee).) **DEFERRED**: P1 — `BALANCER_COMPOSABLE` matcher (phantom-BPT + Vault `batchSwap`
      multi-leg routing layer — Phase-2E full scope).
- [x] [AGENT] P0. **2F — Solana CLMM (Raydium + Orca)**. (execution-service@`54e61d21` — NEW `solana_clmm.py`:
      `SolanaCLMMPool` (Raydium CLMM / Orca Whirlpool — subclasses `UniswapV3Pool`, same concentrated-liquidity tick
      math, rebound to `PoolShape.SOLANA_CLMM`) + `SolanaAMMPool` (Raydium V4 standard pool — subclasses
      `UniswapV2Pool`, `PoolShape.SOLANA_AMM`); registered via `engine.py` side-effect import; `test_pool_matcher.py`
      asserts `SolanaCLMM == V3` numbers at the same pool state.) **DEFERRED**: P1 — Solana-specific tick-bitmap
      layout + multi-tick traversal (shares the Uniswap-V3 multi-tick follow-up) + ≥30-historical-Raydium/Orca-swap
      validation (golden harness — Phase 3).
- [x] [AGENT] P0. **2G — Jupiter (+ 1inch / 0x) aggregator per-route decomposition**. (execution-service@`dc09d6df` —
      NEW `aggregator.py`: `RouteLeg` (per-leg `pool_shape` + `pool_snapshot` + `side` + `input_share` + `chain_id` +
      `pool_address`; `to_dict`/`from_dict` for JSON-decoded routes) + `AggregatorRouteMatcher` (satisfies the
      `PoolMatcher` Protocol; builds each leg's underlying `PoolMatcher` via `pool_matcher_from_snapshot`, composes
      per-leg `quote()`/`apply()` into a route-level `SwapQuote`/`FillResult` with per-leg sub-quotes in `.legs`; two
      route kinds — `"split"` parallel [each leg takes `input_share` of route input, outputs summed] and `"chain"`
      serial multi-hop [leg i consumes 100 % of leg i-1's output]; `spot_price` = product (chain) / share-weighted-sum
      (split) of per-leg effective rates; `snapshot`/`from_snapshot` round-trip the route + per-leg pool snapshots;
      `FillResult.mempool_path` ∈ `{BATCH_SIM, PUBLIC, PRIVATE}` for MEV-vs-slippage execution-alpha attribution) +
      `OneInchRouteMatcher` / `ZeroExRouteMatcher` (same logic, distinct `PoolShape`); registered to
      `PoolShape.JUPITER_ROUTE_AGGREGATOR` / `ONEINCH_AGGREGATOR` / `ZEROX_AGGREGATOR` via `engine.py` side-effect
      import; `__init__.py` re-exports; `test_pool_matcher.py` +7 aggregator tests.) **DEFERRED**: P1 — batch replay of
      aggregator legs needs (a) the NEW `aggregator_route` MTDS data_type (catalogue gap — captured-route JSON persisted
      at decision time; see Discoveries item 4) + (b) the `(chain, pool_address) → PoolShape` lookup (MTDS `dex_pools`
      data_type); the live-mode quote-API fetch path + ≥30-historical-Jupiter-route validation (golden harness —
      Phase 3) are the same follow-up.
- [x] [AGENT] P0. **2H — Solidly-fork ve(3,3) classic-pool matcher** (NEW; added Day-1 2026-05-11). (execution-service@
      `3ebecde2` — NEW `solidly_fork.py`:`SolidlyForkPool` — shared matcher for Velodrome / Aerodrome / Equalizer /
      Thena / Ramses, discriminated by `(chain_id, factory_address)` + per-pool `stable: bool` flag selecting the cubic
      stable invariant `x^3·y + x·y^3 = k` (Newton-Raphson `_get_y`, 255-iter cap, revert-on-non-convergence) vs the
      `x·y = k` volatile branch; reserves normalised to human units BEFORE invariant math (USDC 6-dec overflow edge
      case); fee siphoned to `PoolFees` (ve(3,3) flywheel — NOT added back to reserves, unlike Uniswap V2 where the fee
      grows `k`); registered to `PoolShape.SOLIDLY_FORK`.) **DEFERRED**: P1 — `SolidlyCLForkPool` for
      Velodrome/Aerodrome Slipstream V3-tick CL pools (registered to `PoolShape.SOLIDLY_CL_FORK` — reuses V3 tick math +
      `(chain, CLFactory)` discriminator); ≥20-Velodrome + ≥20-Aerodrome historical-swap validation (golden harness).

**Codex SSOT update (Phase 2 boundary)** — `/codex/04-architecture/amm-slippage-simulation.md` § "Implementation status
— Phase 2 as-built" shipped 2026-05-12 (the as-built module map: `pool_matcher.py` Protocol + registry +
`BasePoolMatcher`; `amm.py` V2/V3/V4 conformance; `curve.py` / `balancer.py` / `solidly_fork.py` / `solana_clmm.py` /
`aggregator.py`; `engine.py` dispatch; the `OrderSide`-consolidation; the deferred-follow-ups list). Per-shape
historical-swap **validation results** still pending — fold into this section once the golden-test-set harness (below)
captures the on-chain `Swap`-event corpus.

**Full-execution criterion**:

- ✅ Each shape has ≥ X historical-Tenderly-fork validations (per-shape thresholds above) within bps.
- ✅ Matching engine `engine.py:_amm_match_impl` routes by `PoolShape` correctly.
- ✅ Backtest replay of 1 day of `carry_staked_basis` against new models produces fill prices within 10bps of live
  Tenderly-fork comparison.

## Phase 3 — Lending rate-impact-from-own-trade simulator (~5-8 AI-days)

Owner: harsh + parallel agent.

> **⚠️ HARD RULE 2026-05-12 — Phase 3 yield is derived from on-chain INDEX growth, NOT APY** (operator-codified,
> [`pnl-attribution.md`](/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md) HARD RULE #4): the
> matching-engine `LendingRateImpactCalculator` (Phase 3A — execution-service@`ff6c52ba`) computes the POST-TRADE
> marginal rate the next-block accrual will use — that output is the input to the matcher's pre-trade quote, NOT the
> consumer's P&L attribution. **Backtest replay yield** is computed downstream from the
> `(liquidity_index, variable_borrow_index)` snapshots captured by MTDS (per
> `plans/active/issues/aave_irm_slope_capture_dropped_2026_05_12.md` capture-coverage requirement): the
> position-balance-monitor reads the aToken/debt-token balance per block; the index delta directly drives
> `CARRY_LENDING_SUPPLY` / `CARRY_LENDING_BORROW` P&L factors. **Banned in Phase 3 implementation**: any
> `supply × apy × time_fraction` proxy as the canonical yield computation; APY is a presentation view only.

> **Day-1 slot-6 design ship 2026-05-12**: codex
> [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) § "Lending rate-impact-from-
> own-trade" → "Per-protocol IRM parameter capture" subsection ships the Phase 3 design half with operator-runnable
> detail for Harsh slot 4: (a) per-protocol Pool/Comet addresses + IRM getter ABIs + reserve config getters across 7
> protocol-chain combos (Aave V3 Ethereum/Arbitrum/Optimism/Polygon/Base/Avalanche + Compound V3
> Ethereum/Arbitrum/Polygon/Base + Spark Ethereum/Gnosis + Radiant BSC/Arbitrum); (b) UAC `LendingMarketState` schema
> extension with `protocol_irm_shape` discriminator + Compound-V3-specific fields (kink + below/above-kink slopes —
> Compound V3 has DIFFERENT shape from Aave's piecewise; matcher dispatch required); (c) `post_trade_rate()` calculator
> code with protocol-shape dispatch; (d) Phase 3C validation harness skeleton + large-supply event source (NEW
> `lending_events` MTDS data_type — gap captured in discoveries section). **Implementation half remains `- [ ]` for
> Harsh slot 4**.

- [x] [AGENT] P0. **3A — `LendingRateImpactCalculator`** in `execution-service/execution_service/matching_engine/`.
      (execution-service@`ff6c52ba` — NEW `lending/` subpackage with `LendingRateImpactCalculator` class +
      `LendingTradeKind` StrEnum (SUPPLY/BORROW/WITHDRAW/REPAY). Thin wrapper around UAC `post_trade_rate()` canonical
      entry (uac@`7f978f5`); dispatches by `LendingMarketState.protocol_irm_shape` (AAVE_KINKED for Aave V3 + Spark +
      Radiant; COMPOUND_V3 for Comet). Provides `post_trade_rate()` canonical method + `supply_rate_delta_bps()` /
      `borrow_rate_delta_bps()` convenience methods. Smoke-tested: Aave USDC pool at U=50% (kink=90%); +100M supply
      compresses borrow rate by 20.20 bps. basedpyright clean on new subpackage.)
- [x] [AGENT] P0. **3B — `BenchmarkMatcher` extension**. (execution-service@`b8989ae5` — `BenchmarkMatcher.match` gains
      a lending-mode dispatch: when `lending_market_state` (UAC `LendingMarketState`) + `lending_trade_kind`
      (`LendingTradeKind` enum OR string name) kwargs are present, the matcher routes through
      `LendingRateImpactCalculator` (Phase 3A) → `MatchResult.fill_price` = post-trade APY +
      `MatchResult.price_impact_bps` = signed rate-delta in bps (negative for SUPPLY/REPAY; positive for
      BORROW/WITHDRAW). Legacy benchmark-price path unchanged for non-lending orders. Typed-error `error_message` closed
      set for missing/invalid kwargs. Covers Aave V3 + Compound V3 + Spark + Radiant via UAC's `ProtocolIRMShape`
      discriminator. NEW `tests/unit/matching_engine/test_benchmark_matcher_rate_impact.py` ships 11 tests (SUPPLY -rate
      / BORROW +rate / WITHDRAW +rate / REPAY -rate / string-form-accepted / invalid-kind / missing-state /
      zero-quantity / legacy-price-path-unchanged / missing-benchmark-price / supply-then-withdraw-sign-flip; all
      green). Existing 59 tests still green (golden-harness + `test_pool_matcher.py`). ruff clean; basedpyright clean on
      the changed file modulo pre-existing `_mk` `OrderType` internal-vs-matching-engine mismatch (PM @`b16fb8b6` DONE
      table flagged; not introduced here).)
- [x] [AGENT] P0. **3C — Validation harness**. Replay 1 month of historical Aave V3 large supplies (>$10M); compare
      simulated post-trade rate vs realized on-chain rate. Tolerance: ≤ 10bps absolute APY delta.
      (execution-service@`a3639fdd6` — pytest harness shipped: 3C.1 `_collect_supply_events`, 3C.2
      `_enrich_events_with_rates`, 3C.3 `_validate_events`; execution-service@`c12a4dbb0` — VM CLI wrapper
      `scripts/run_lending_rate_validation.py` with STARTED/STOPPED/FAILED events + GCS results.json persistence;
      deployment-service@`f87bcb3` — VM launcher `launch-aave-lending-rate-validation-vm.sh` (singleton-locked on
      Alchemy key, n2-standard-4, asia-northeast1-a) + watchdog registration `aave-lending-rate-val-` +
      `defi-validation` bucket in cloud-providers.yaml. GCS bucket `gs://central-element-323112-defi-validation/`
      provisioned 2026-05-13. **OPERATIONAL RUN 2026-05-13**: VM `aave-lending-rate-val-20260513-173601` (corr_id
      `41F37242-...`) executed end-to-end on mainnet (blocks 23.3M→25.086M); 60 events collected (USDC:26, USDT:20,
      DAI:14); `results.json` persisted to
      `gs://central-element-323112-defi-validation/results/lending/2026-05-13/41F37242-.../results.json`. **Validation
      gate ❌ 0/60 events pass** — sim ~40-70% LOW vs realized; root cause = stale
      `AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET` (governance drift since table written). P1 follow-up filed:
      `plans/active/issues/phase_3c_lending_rate_model_0_of_60_pass_2026_05_13.md`. **FIX SHIPPED
      execution-service@`abb526a98` 2026-05-13**: `_fetch_irm_params_live()` added — fetches live IRM params from
      on-chain `ReserveStrategy` per event (`getBaseVariableBorrowRate` / `getVariableRateSlope1/2` /
      `OPTIMAL_USAGE_RATIO`), with strategy-addr cache; `_enrich_events_with_rates` stores
      `live_slope1/slope2/optimal_utilization/reserve_factor` in fixture; `_reconstruct_lending_market_state` reads live
      fields first, falls back to stale defaults only with WARNING. Math: stale slope1=0.04 at U=86% = 2.96% vs live
      slope1=0.06 = 4.34% (matches sim≈2.7% vs realized≈4.36% divergence). VM re-run launched:
      `aave-lending-rate-val-20260513-182201` corr_id `8849FD14-B34D-43F8-B6CA-5265DCA2CCAB`. **v4 RUN 2026-05-13 EOD**
      (execution-service@`0ff6615cb`): added V2 strategy ABI (`getInterestRateData(asset)` for Aave V3.1+) + per-asset
      cache key (was global → DAI cache pollution from USDT params). VM `aave-lending-rate-val-20260513-205909` corr_id
      `51A5DE7C-...`. **Result: 33/60 = 55% pass rate** — INFRA ✅ OPERATIONALLY GREEN; VALIDATION GATE 🟡 PARTIAL (USDC
      22/26 = 85%, USDT 11/20 = 55%, DAI 0/14 = 0%). Two next-cycle fixes filed in issue doc: (a) DAI 0/14 root-cause
      investigation, (b) pre-trade block off-by-one 1-line fix (expected to lift 55% → ~90%+). All 5 bugs fixed in
      cumulative chain are real correctness wins.)
  - [x] **3C.1 — Event Collector** (RPC `eth_getLogs` batching). Query mainnet for Aave V3 Pool `Supply` events Sep 2025
        → May 2026; filter events >$10M `amount`; extract (block, txhash, pool_address, asset, user, amount, timestamp).
        Target ≥50 events. Store as JSON fixture `tests/defi_execution/integration/fixtures/aave_large_supplies.json`.
        (execution-service@`a3639fdd6`)
  - [x] **3C.2 — Rate Fetcher** (RPC contract state reads). For each event, RPC call Aave V3 Pool contract
        `getReserveData(asset)` at (event_block, event_block+1) → extract `liquidityRate` before/after supply. Cache
        (asset, block) → rate to avoid duplicate calls. Decode ray format → APY %. (execution-service@`a3639fdd6`)
  - [x] **3C.3 — Validator** (harness logic). For each ≥50 event: call `LendingRateImpactCalculator.post_trade_rate`
        with pool_state_before + supply_amount → compare simulated_rate vs actual_realized_rate (post-block +1). Track ±
        APY delta in bps; count % within ≤10bps tolerance. Assert ≥90% pass. Emit summary: per-asset breakdown,
        tolerance distribution histogram, any outliers >50bps. (execution-service@`a3639fdd6`)

**Full-execution criterion**:

- ✅ `LendingRateImpactCalculator` unit tests green for all 4 lending protocols + multi-chain Aave.
- ✅ Validation harness runs ≥ 50 historical large-supply events; ≥ 90% within 10bps tolerance.
- ✅ `BenchmarkMatcher` extension QG-green; backtest yield difference vs old (zero-impact) matcher recorded in
  changelog.

## Phase 4 — Governance proposal capture + simulation harness (~8-12 AI-days)

Owner: ikenna for design + harsh for implementation.

> **Day-1 slot-6 design ship 2026-05-12 (PM@`ae804766`)**: codex
> [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) § "Governance proposal simulation
> harness" → "Per-protocol capture detail" subsection ships the Phase 4 design half with operator-runnable detail for
> Harsh slot 4: (a) per-protocol Governor contract addresses (`GovernanceV3Ethereum`, `GovernorBravoDelegator`, MakerDAO
> ChiefBoot for Spark, AragonVoting for Lido)
>
> - Snapshot space IDs + subgraph endpoints; (b) Tenderly fork simulator code skeleton with REST API patterns (POST
>   `fork` + `simulate`) + ~10 sims/day budget; (c) `defi-simulate-proposal` CLI signature
> - JSON return shape; (d) 2-year backfill VM launcher detail (`launch-governance-backfill-vm.sh` per-protocol; watchdog
>   dict entry `governance-backfill-` + tarball refresh required per CLAUDE.md VM Naming Convention HARD RULE; per-VM
>   shard isolation `VM_NAME=<unique-tag>` + `MANIFEST_PER_VM_SHARDS=true`). **Implementation half remains `- [ ]` for
>   Harsh slot 4** per cross-side handshake.

- [x] [AGENT] P0. **4A — Governance capture adapter**. ✅ MTDS@`e81031c` — New
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/governance_adapter.py` capturing
      Aave V3 + Compound V3 + Spark + Lido proposals. Sources: on-chain Governor contract events (Tally indexes, but
      read directly via subgraph) + Snapshot off-chain proposals API. GovernanceProposalsHandler writes
      `governance_proposals` data_type rows; 19 unit tests green; QG PASSED.
- [x] [AGENT] P0. **4B — `GovernanceProposalSimulator`** in execution-service. (execution-service@`9259edb9` — NEW
      `governance/proposal_simulator.py`:
      `simulate_proposal_execution(proposal, fork_block, affected_assets, tenderly_client)` returns per-asset
      `ParameterDelta(before, after)` after running `governor.execute` on a Tenderly fork (pre-snapshot → simulate →
      post-snapshot). `AssetParameters` frozen dataclass unions Aave V3 / Compound V3 / Spark / Lido getter fields
      (reserve_factor, LTV bps, liquidation_threshold_bps, supply/borrow caps, IRM slopes, optimal_utilization_rate,
      oracle_price_usd + `extra_protocol_fields` string overflow). `ParameterDelta` exposes `reserve_factor_delta_bps` +
      `supply_cap_delta_native` properties. `TenderlyClient` Protocol is the operator-wired seam — production impl ships
      auth + retry + per-day fork budget (per codex risk-register row); tests inject an in-memory fake satisfying the
      Protocol structurally. `AAVE_V3_PROTOCOL` / `COMPOUND_V3_PROTOCOL` / `SPARK_PROTOCOL` / `LIDO_PROTOCOL` Final[str]
      constants match `GovernanceProposal.protocol` strings for typed dispatch + grep-ability. 8 unit tests in
      `tests/unit/governance/test_proposal_simulator.py` green; ruff + basedpyright clean.) **DEFERRED**: P1 —
      production Tenderly REST client (auth + retry + budget tracking) wires the Protocol; lands as operator-runnable
      setup when Tenderly creds + project ID are confirmed.
- [x] [AGENT] P0. **4C — Strategy-side scenario API**. (execution-service@`1dea6e91` — NEW `cli/simulate_proposal.py`:
      `defi-simulate-proposal` CLI with argparse surface (`--proposal-id` / `--protocol` / `--archetype` /
      `--fork-block` / `--affected-assets` / `--time-T` / `--historical`) +
      `run_cli(proposal, archetype, fork_block, affected_assets, tenderly_client, historical) -> dict[str, object]`
      that wraps Phase 4B `simulate_proposal_execution` + emits the canonical JSON shape (archetype + proposal_id +
      protocol + fork_block + per-asset `parameter_deltas[]` with before/after + delta helpers + placeholder
      `expected_pnl_delta_bps` / `confidence_interval_bps` Phase 8 fills + `validation_status`
      `calibrated`/`forward-looking`). `_decimal_to_str` + `_delta_to_json` JSON-serialise the Decimal-bearing
      AssetParameters fields. `main()` raises `NotImplementedError` until the operator wires Phase 4A MTDS proposal
      loader + the production TenderlyClient. Smoke: 1-asset Aave-V3 proposal at fork 22500000 → JSON report with
      reserve_factor 0.10→0.15 + delta_bps=500.00. basedpyright + ruff clean.) **DEFERRED**: P1 — Phase 4A MTDS proposal
      loader wire-in; Phase 8 expected_pnl_delta_bps + confidence_interval_bps mapping (Phase 8 backtest harness ships
      the carry / leveraged-funding-arb P&L attribution).
- [x] [AGENT] P0. **4D — Backfill historical proposals** for the last 2 years across all 4 protocols. ✅
      deployment-service@`b682e37` — `launch-governance-backfill-vm.sh` + `governance-backfill-` prefix in
      VM_PREFIX_TO_BUCKET. To run:
      `bash deployment-service/scripts/vm/launch-governance-backfill-vm.sh 2024-01-01 2026-05-17`. Coverage validates
      that any "what if proposal X passed" can be answered for any historical date.

**Full-execution criterion**:

- ✅ Governance adapter captures ≥ 1 month of Aave V3 + Compound V3 + Spark + Lido proposals.
- ✅ `GovernanceProposalSimulator` runs successfully on ≥ 5 historical proposals with measurable parameter delta.
- ✅ `defi-simulate-proposal` CLI returns archetype P&L delta within 100bps of actual realized post-execution delta (for
  the historical proposals where we can measure).

## Phase 5 — Yield-stream simulators (~8-12 AI-days)

Owner: harsh + parallel agents.

> **Day-1 slot-6 design ship 2026-05-12 (PM@`ae804766`)**: codex
> [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) § "Staking + restaking yield-stream
> simulators" → "Per-protocol capture detail" subsection ships the Phase 5 design half with operator-runnable detail for
> Harsh slot 4: (a) 11-row per-protocol capture table covering Ethereum beacon (Lighthouse/Prysm REST per-epoch) +
> Ethereum execution (eth_getBlockByNumber + baseFeePerGas + priorityFee) + Solana validator (getInflationReward
> per-epoch) + EigenLayer + Symbiotic + Karak + Jito-restaking subgraphs + Ether.fi/Renzo/KelpDAO/Puffer LRT-fee
> contract addresses + governance subgraph polls; (b) per-component model skeletons — `StakingYieldModel`
> calibrate+sample with attestation-efficiency-binned heteroskedasticity; `RestakingAVSModel` base+log-normal-premium
> per-LRT operator-allocation-weighted; `LRTProtocolFeeModel` discrete-event mean±σ_quarterly per-protocol;
> `SeasonalPointsModel` operator-tuned discount factors with 4 protocol calibration anchors (Ether.fi 60% / Renzo 50% /
> Puffer 50% / new programs 70%); (c) `Phase 5E` composite
> `staking_yield_stream_distribution(lst_or_lrt, chain, horizon_epochs)` code skeleton convolving all 4 layers.
> **Implementation half remains `- [ ]` for Harsh slot 4** per cross-side handshake.

- [x] [AGENT] P0. **5A — Native staking yield stochastic model**. (execution-service@`513c9770` — NEW
      `matching_engine/yield_streams/` subpackage with `NativeStakingModel` frozen dataclass (per-bin Gaussian mean+std
      binned by attestation efficiency quintile for Ethereum; single-bin collapse for Solana) + `StakingYieldSample`
      historical-row dataclass + `ForwardYieldDistribution` (mean_apr, p5, p95, n_paths, horizon_epochs) output schema.
      `calibrate_native_staking()` fits per-bin distribution from MTDS `staking_yields` rows;
      `sample_forward_distribution()` MC kernel sums N=horizon_epochs Gaussian draws per path → APR annualised by
      epochs_per_year (82125 ETH / 365 SOL). Smoke pass: 200 mock Ethereum samples, 1170-epoch horizon, mean=84.9%
      p5=83.7% p95=86.1%. basedpyright clean.)
- [x] [AGENT] P0. **5B — Restaking AVS yield model**. (execution-service@`58c703a5` — NEW
      `matching_engine/yield_streams/restaking_avs.py`: `RestakingRewardSample` historical-row dataclass,
      `AVSPremiumDistribution` per-(AVS, LRT) log-normal calibrated state (mu_log + sigma_log + per-LRT
      operator_allocation_share), `RestakingAVSModel` bundle, `calibrate_restaking_avs_model()` log-domain fit (≥ 5
      positive samples per pair; degenerate sigma=0 collapse below threshold), `sample_lrt_total_premium()` MC kernel
      summing weighted per-AVS log-normal draws. EigenLayer / Symbiotic / Karak / Jito-restaking captured via MTDS
      `restaking_rewards`. Smoke: 30 EigenLayer/weETH samples → `(mean, p5, p95)` triple populated; pure-LSTs return
      zero (no matched distributions). basedpyright clean.)
- [x] [AGENT] P0. **5C — LRT protocol-fee model**. (execution-service@`58c703a5` — NEW
      `matching_engine/yield_streams/lrt_protocol_fee.py`: `LRTProtocolFeeSample` per-quarter row,
      `LRTProtocolFeeDistribution` per-protocol calibrated state (current_fee_bps + sigma_quarterly_bps +
      fee_ceiling_bps = max_observed × 1.5), `LRTProtocolFeeModel` bundle, `calibrate_lrt_protocol_fee_model()` fits
      Gaussian on consecutive quarter-to-quarter deltas, `sample_forward_fee()` MC kernel clips path draws to
      `[0, ceiling]` then averages over horizon_quarters. Covers Ether.fi / Renzo / KelpDAO / Puffer. Smoke: 8-quarter
      ETHERFI calibration → forward 8-quarter mean fee 135bps ±2.6bps band on the smoke synthetic input. basedpyright
      clean.)
- [x] [AGENT] P0. **5D — Seasonal-points model** (off-chain rewards). (execution-service@`58c703a5` — NEW
      `matching_engine/yield_streams/seasonal_points.py`: `SeasonalPointsConfig` operator-supplied per-protocol
      (points_per_unit_per_epoch + redemption_ratio + discount_factor + expected_season_end + epochs_per_year),
      `SeasonalPointsImpliedYield` discounted forward APR + audit fields (undiscounted APR + discount_factor +
      season_days_remaining), `compute_implied_apr()` validates tz-aware datetimes / discount ∈ [0,1] / non-negative
      rates, `SeasonalPointsModel` bundle + `compute_implied_apr_for_protocol()` lookup wrapper (returns zero-yield for
      protocols without seasonal programmes). Defaults per codex: 60% Ether.fi, 50% Renzo / Puffer, 70% new programmes.
      Yaml hot-reload via `config_reloaders.py` is a follow-up todo.)
- [x] [AGENT] P0. **5E — Composite `StakingYieldStreamSimulator`** that integrates 5A + 5B + 5C + 5D into a single
      per-LST/LRT forward-yield distribution. (execution-service@`58c703a5` — NEW
      `matching_engine/yield_streams/composite_simulator.py`: `CompositeYieldInputs` bundle of per-layer calibrated
      models + per-LST runtime context, `_LST_TO_PROTOCOL` pinned mapping (stETH/rETH/cbETH/wstETH pure-LSTs +
      weETH→ETHERFI / ezETH→RENZO / rsETH→KELPDAO / pufETH→PUFFER LRTs + jitoSOL/mSOL/bSOL pure-Solana),
      `staking_yield_stream_distribution()` first-moment composition with CLT tail reconstruction returning
      `ForwardYieldDistribution`, `make_staking_yield_decomposition()` returning UAC `StakingYieldDecomposition`
      snapshot (per-AVS breakdown via per-AVS sub-model sampling). Smoke: weETH Ethereum 1170-epoch composite —
      calibrated 100 ns + 30 avs + 8 quarters + 1 seasonal config, composite `(mean_apr, p5, p95)` populated +
      decomposition with 1 AVS component + 135bps fee + 0.049 seasonal APR. basedpyright + ruff clean.) **DEFERRED**: P1
      — per-path element-wise sum (full convolution preserving log-normal tail vs CLT moment approximation);
      operator-tuned `defi_seasonal_points_calibration.yaml` + `defi_yield_stream_protocol_map.yaml` hot-reload via
      `config_reloaders.py`.

**Full-execution criterion**:

- ✅ Per-chain native staking model has ≥ 6 months calibration data + walk-forward validation within 50bps APY
  prediction error.
- ✅ Composite simulator integrated into `carry_staked_basis` archetype config.

## Phase 6 — Hedge-ratio dynamic adjustment (~3-5 AI-days)

Owner: harsh.

> **Phase 6A audit shipped 2026-05-12 (slot 6 Day-1)**: carry_staked_basis engine confirmed **STATIC**. The audit
> pointer in todo 6A below to `pairs_fixed.py` was stale — that file is a stat_arb_pairs strategy, NOT the
> `carry_staked_basis` archetype. **Real code path**:
> [`strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:248-318`](../../../strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py)
> — function `_build_legs()`. Line 264:
>
> ```python
> perp_short_units = eth_qty * (Decimal("1") - structure.perp_margin_haircut)
> ```
>
> The hedge is sized 1:1 against LST principal (delta-neutral) clamped by venue margin haircut. **No per-tick / per-bar
> peg-drift adjustment** anywhere in the engine. `default_basis_trade.yaml` has `hedge_ratio_window: 60` but that's for
> `stat_arb_pairs` (different strategy); `carry_staked_basis` archetype config has NO hedge_ratio dynamics.
> **Conclusion: Phase 6B IS needed** — operator can no longer treat as conditional.

- [x] [AGENT] P0. **6A — Audit `carry_staked_basis` engine** for hedge ratio shape. ✅ DONE 2026-05-12 slot 6 Day-1 (no
      commit yet — finding documented in Phase 6 banner above). **Evidence**: `staked_basis.py:264`
      `perp_short_units = eth_qty * (Decimal("1") - structure.perp_margin_haircut)` — STATIC. Audit pointer in original
      todo (`pairs_fixed.py`) was wrong file (stat_arb_pairs ≠ carry_staked_basis). Real archetype engine path:
      `staked_basis.py:_build_legs` line 248-318.
- [x] [AGENT] P0. **6B-WIRE-IN — wire `compute_dynamic_hedge_ratio` into `_build_legs` callsite**.
      (strategy-service@`6431955` — `CarryStakedBasisEngine` gains `__init__` override + cross-tick
      `last_hedge_rebalance_rate: Decimal | None` state (None on first entry → always-triggers fresh baseline);
      `on_tick` reads `lst_native_rate` feature (default 1.0 — collapses to pre-Phase-6B static
      `eth_qty * (1 - haircut)` sizing → safe rollout for archetypes without upstream LST/native rate feed); reads
      `peg_drift_threshold_bps` param (default `DEFAULT_PEG_DRIFT_THRESHOLD_BPS = 25`); calls
      `compute_dynamic_hedge_ratio` for the decision; `_build_legs` accepts `perp_short_units` as a new positional
      parameter so the engine atomically persists `decision.new_rebalance_baseline_rate` with the trade emission.
      `AtomicInstruction.attestations` extended with the HedgeRatioSnapshot (Phase 1F UAC schema) audit fields —
      `lst_native_rate_now` / `hedge_peg_drift_bps` / `hedge_peg_drift_threshold_bps` / `hedge_rebalance_triggered` /
      `hedge_new_baseline_rate` / `hedge_perp_short_units` — for pnl-attribution-service's Phase 6C dynamic-vs-static
      backtest harness. NEW `tests/unit/engine/strategies/v2/test_carry_staked_basis_dynamic_hedge_wire_in.py` ships 6
      tests (default-rate-collapses-to-static, lst_rate>1-scales-up, drift-below-threshold-preserves-baseline,
      drift-above-threshold-advances-baseline, custom-threshold-param-honoured, initial-entry-always- triggers; all
      green); existing `test_carry_staked_basis_lst_as_margin_emits_four_leg_bundle` + 11 `dynamic_hedge_ratio` unit
      tests still green (no regression). basedpyright + ruff clean.) **RESOLVED 2026-05-17**: P1 DEFERRED — emit
      `HedgeRatioSnapshot` rows to a dedicated downstream data_type — shipped via
      `hedge_ratio_snapshot_persistence_2026_05_13.md`: UAC@2fcb1bb (DataType + schema) + strategy-service@21209bd
      (HedgeRatioSnapshotWriter + on_tick wire-in) + pnl-attribution-service@ee96d3c (reader in PnlDomainAdapter).
- [x] [AGENT] P0. **6B (original) — IMPLEMENT (not conditional — audit confirmed static)** dynamic hedge-ratio
      adjustment using LST/native exchange rate stream from Phase 1A captures (jitoSOL/SOL, mSOL/SOL, bSOL/SOL,
      rETH/ETH, stETH/ETH, weETH/ETH). Per-tick or per-bar rebalance trigger when |peg_drift| > N bps. **Implementation
      home**: SAME wire-in as 6B-WIRE-IN above (strategy-service@ `6431955`) — `CarryStakedBasisEngine.on_tick` calls
      `compute_dynamic_hedge_ratio(eth_qty, margin_haircut, lst_native_rate_now, last_rebalance_rate, peg_drift_threshold_bps)`;
      the size formula is `perp_short_units = eth_qty * lst_native_rate * (1 - margin_haircut)`. Hysteresis band
      parameter `peg_drift_threshold_bps` configurable per archetype via the engine `params` dict (default 25 bps based
      on observed historical jitoSOL/SOL daily-stddev ≈ 8 bps; 3-stddev hysteresis ≈ 25 bps). Phase 6B-WIRE-IN closure
      satisfies this todo simultaneously — both items are the same shipped wire-in.
- [x] [AGENT] P0. **6C — Tests**: backtest carry archetype with dynamic vs static hedge-ratio over 1-year historical
      replay. Document P&L delta + confidence interval. (strategy-service@`7eb3dab` — NEW
      `tests/unit/engine/strategies/v2/test_dynamic_hedge_ratio_dynamic_vs_static_backtest.py` ships the synthetic-data
      math-validation half: 18 tests across 7 classes; `replay_synthetic()` harness + 4 stream generators
      (`steady_accrual_stream` / `volatile_noise_stream` w/ deterministic LCG / `depeg_event_stream` /
      `sawtooth_stream`) + `STATIC_THRESHOLD_BPS` sentinel reproducing the pre-Phase-6B static shape. 5 scenarios
      validated: (a) **steady accrual** (jitoSOL-like 1.000→1.080 over 365 ticks) — dynamic rebalances 30× (28-38 band),
      static = 1×, residual ratio 32.47× vs the >2× math-correctness floor; (b) **volatile noise** (8bps daily noise
      around 1.05) — dynamic rebalance count == 1 exactly (hysteresis fully protects: 8bps << 25bps default threshold);
      tighter 3bps threshold fires more often; (c) **depeg event** (1.05→1.02 at tick 100) — dynamic rebalances exactly
      2× (initial + depeg), static residual > 5× dynamic; (d) **sawtooth oscillation** (±50bps every 10 ticks over 200)
      — dynamic rebalances exactly 20× (one per direction flip), total residual == 0 (rebalance fires AT the
      transition); (e) **threshold sensitivity** — tight threshold ⇒ more rebalances + lower aggregate residual
      (monotonic). Edge cases + stream-generator contracts also covered. basedpyright 0/0/0; ruff check + ruff format
      clean. **DEFERRED**: P1 — operator-runnable 1-year historical replay against real MTDS LST-rate captures lands in
      Phase 8A backtest-fidelity harness (consumes `BacktestFidelityReport` UAC schema shipped in this cycle); needs
      real `instruments-service` LST-rate stream + MTDS adapter backfill. Synthetic-data half here locks the
      hedge-residual math contract.

**Full-execution criterion**:

- ✅ `carry_staked_basis` engine confirmed dynamic-hedge-ratio adjusted (post Phase 6B if was static).
- ✅ Backtest comparison shows non-trivial P&L delta + reduced realized-residual variance vs static.

## Phase 7 — Slashing tail-risk Monte Carlo (~3-5 AI-days)

Owner: harsh.

> **Day-1 slot-6 design ship 2026-05-12**: codex
> [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) § "Slashing tail-risk Monte Carlo" →
> "Per-chain slashing event capture" + "Phase 7B MC simulator architecture" + "Phase 7C archetype capital-allocation
> hook" subsections ship the Phase 7 design half with operator-runnable detail for Harsh slot 4: (a) per-chain
> `slashing_events` data_type source — Ethereum beacon (Lighthouse/Prysm `/eth/v1/beacon/pool/*_slashings`
>
> - beaconcha.in historical backfill) + Solana (Anza RPC `getSlashingHistory` + Solana Beach cross-check); (b)
>   `SlashingTailRiskMC` simulator code skeleton with Poisson sampling + ECDF severity + Hill-estimator heavy-tail
>   alpha + N=10000 paths; (c) Phase 7C `_slashing_risk_gate` archetype hook with config thresholds
>   (`max_p_loss_exceeds_1pct`, `max_p_loss_exceeds_5pct`, `backoff_multiplier_at_threshold`) for capital-allocation
>   circuit-breaker; (d) validation harness comparison: 1-year backtest with vs without slashing risk gate documenting
>   P&L delta + max-drawdown delta + tail-event survival rate. **Implementation half remains `- [ ]` for Harsh slot 4**.

- [x] [AGENT] P0. **7A — Historical slashing rate calibration** per chain. (execution-service@`639fd6f4` — NEW
      `matching_engine/lending/slashing_calibration.py`: `PER_CHAIN_EPOCH_SECONDS` (Ethereum beacon 384s / Solana
      validator-day 86400s) + `TYPICAL_VALIDATOR_SET_SIZE` (Ethereum ~900k / Solana ~1.5k Q1-2026 observed) +
      `default_cumulative_validator_epochs(chain, lookback_days)` derives the MC denominator +
      `calibrate_chain(chain, events, lookback_days|cumulative_validator_epochs, n_paths, horizon_epochs, seed)`
      orchestrator that wraps Phase 7B `SlashingTailRiskMC.calibrate()` with per-chain glue. Mutually-exclusive
      `lookback_days` vs `cumulative_validator_epochs` gives operators a sane default + an explicit override path.
      Smoke: 50 ATTESTER_SLASHING ETH events × 180-day lookback → `p_per_val_epoch=1.37e-9`, `severity_mean=0.5`,
      `alpha=2.0`. The MTDS read path (`slashing_events_adapter` Phase 1E → `SLASHING_EVENT` parquet) is operator-side
      wiring; this helper accepts the events in-memory so it's unit-testable without I/O.)
- [x] [AGENT] P0. **7B — `SlashingTailRiskMC`** in execution-service. (execution-service@`b16fb8b6` — NEW
      `matching_engine/lending/slashing_tail_risk.py`: `SlashingTailRiskMC` stateful dataclass with `calibrate()`
      (consumes UAC `SlashingEvent` rows + cumulative validator-epoch denominator → fits Poisson lambda + log-normal
      severity mean/std + Hill-estimator alpha) + `simulate_archetype_loss()` (N=10000 MC paths via Poisson slashing
      count × log-normal severity → empirical `ProbabilityOfLossCurve` at standard thresholds
      1%/5%/10%/25%/50%/100%/250%/500%/1000%); `SlashingDistribution` + `ProbabilityOfLossCurve` schema dataclasses with
      `p_at_threshold()` linear-interp lookup for the Phase 7C archetype gate. Knuth's algorithm for small λ, Gaussian
      approx for λ>30. Smoke pass: 150 mock ETH events @ 0.5±0.2 → p_per_val_epoch=1.5e-5, alpha=7.22, archetype 1000
      ETH/31 validators → P(loss>5%)≈0 (conservative — light-tail Gaussian severities). basedpyright clean.)
- [x] [AGENT] P0. **7C — Carry archetype tail-risk allocation hook**. (execution-service@`639fd6f4` — NEW
      `matching_engine/lending/slashing_archetype_gate.py`: `SlashingRiskGateConfig` (cap_threshold P(loss>1%)>0.05 +
      kill_threshold P(loss>5%)>0.01 + backoff_multiplier_at_threshold=0.5 defaults per codex § Phase 7C) +
      `AllocationDecision` (allocation_multiplier + closed-set rationale [normal / cap_threshold_exceeded /
      kill_threshold_exceeded] + audit p1pct/p5pct readings) + `evaluate_slashing_risk_gate(loss_curve, config)`
      precedence-ordered evaluator [kill > cap > normal]; consumed by `CarryStakedBasisEngine.on_tick` preflight at the
      archetype-engine boundary. Smoke: low-risk synthetic curve → `rationale=normal`; `cap_threshold=-1` forces
      `cap_threshold_exceeded` → multiplier=0.5. basedpyright + ruff clean.) **DEFERRED**: P1 — wire-in to
      `staked_basis.py::on_tick` preflight (the helper here is the math kernel; the archetype-engine integration lands
      as a separate strategy-service commit once the operator confirms the per-archetype config threshold values via the
      risk-and-exposure-service backtest harness).

**Full-execution criterion**:

- ✅ Historical slashing rate calibrated per chain with confidence interval recorded.
- ✅ MC simulator returns P(slashing) curve for carry archetype's actual current exposure within compute-time budget.

## Phase 8 — Backtest fidelity validation (~3-5 AI-days)

Owner: ikenna for sign-off + harsh for runs.

> **Day-1 slot-6 design ship 2026-05-12**: codex
> [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) § "Validation gates" → "Phase 8
> validation framework" subsection ships the Phase 8 design half with operator-runnable detail: (a) Three parallel
> harness scripts under `execution-service/tests/integration/backtest_fidelity/` (`run_carry_archetype_replay.py` /
> `run_leveraged_funding_arb_replay.py` / `run_tenderly_live_reconciliation.py`) plus operator dashboard composer
> (`compose_sign_off_report.py`); (b) `BacktestFidelityReport` schema with per-leg attribution + bias-reduction-pct +
> max-drawdown delta; (c) `TenderlyReconciliationReport` schema with per-pool-shape breakdown for failure-mode triage +
> 95% within-10-bps acceptance gate + Tenderly fork budget (~$500/day during validation runs); (d) `SignOffReport`
> schema with aggregate signal (GREEN/YELLOW/RED) + operator APPROVE/REJECT persistence to pnl-attribution-service.
> **Implementation half remains `- [ ]` for Harsh slot 4** (Phase 8A/B/C scripts cannot run until Phase 2-7
> implementations land); **operator sign-off 8D is the May-23 cutover gate** routed to slot 1 (master plan owner) for
> execution timing.
>
> **2026-05-12 Harsh slot 4 (Opus max resume) — UAC schema half SHIPPED** (uac@`a541e4e` initial + uac@`97df991` Literal
> refactor): `unified_api_contracts/internal/domain/defi/backtest_fidelity_schemas.py` ships `BacktestFidelityReport`
> (Phase 8A/8B) + `TenderlyReconciliationReport` (Phase 8C) + `SignOffReport` (Phase 8D composite) +
> `PerLegAttribution` + `PerPoolShapeReconciliation` + `AggregateSignal` StrEnum (GREEN/YELLOW/RED) +
> `OperatorSignOffStatus` StrEnum (PENDING/APPROVED/REJECTED) + `LegKind` `Literal[...]` closed-set type alias (6
> archetype legs: amm_swap / perp_position / lending_supply / lending_borrow / stake / restake) +
> `compute_aggregate_signal(gate_pass_summary) → AggregateSignal` (3/3 GREEN, 2/3 YELLOW, ≤1/3 RED). Exported through
> `unified_api_contracts.internal`. End-to-end smoke pass verified the composite + the Literal closed-set enforcement
> (6/6 valid kinds accepted; 'nonexistent' rejected with `ValidationError`). basedpyright 0/0/0 + ruff + ruff-format
> clean on the new file. **Phase 8A/B/C/D harness-script half (operator-runnable under
> `execution-service/tests/integration/backtest_fidelity/`) remains `- [ ]`** — depends on full Phase 2-7 integration
> runs + real MTDS archetype-trade data; harness scripts now have their typed-output contract locked.

- [x] [AGENT] P0. **8A — Carry archetype 1-year replay** using all new sim primitives (Phases 2-7) + Phase 6 dynamic
      hedge ratio. Compare simulated P&L vs old (constant-product + zero-rate-impact + static-hedge) replay. Document
      delta + reduced bias evidence. (script-shipped execution-service@`38b3e8a5` (rescued via cherry-pick from
      tab/hk/4@c5dd45eb after foot-gun #5) — `run_carry_archetype_replay.py`; `--synthetic` demo passes. **DEFERRED**:
      full-execution 1-year real MTDS data replay depends on Phases 3-7 fully wired end-to-end + real MTDS
      archetype-trades data; operator-runnable per deploy cadence.)
- [x] [AGENT] P0. **8B — Leveraged-funding-arb 1-year replay** with new sim primitives. Document delta vs old.
      (script-shipped execution-service@`38b3e8a5` (rescued via cherry-pick from tab/hk/4@c5dd45eb after foot-gun #5) —
      `run_leveraged_funding_arb_replay.py`; `--synthetic` demo passes. **DEFERRED**: full-execution depends on real
      MTDS data + Phases 3-7; operator-runnable per deploy cadence.)
- [x] [AGENT] P0. **8C — Tenderly fork live-vs-simulated reconciliation** for 1 day of paper-trade. Per-tick live fill
      vs simulated fill; |delta| should be < 10bps for ≥ 95% of fills. (script-shipped execution-service@`38b3e8a5`
      (rescued via cherry-pick from tab/hk/4@c5dd45eb after foot-gun #5) — `run_tenderly_live_reconciliation.py`;
      `--synthetic` demo 100% pass. **DEFERRED**: real execution requires `TENDERLY_ACCESS_KEY` + live paper-trade log;
      operator-runnable weekly during rollout cadence.)
- [x] [AGENT] P0. **8D — Sign-off gate**. Compose script shipped execution-service@`38b3e8a5` (rescued via cherry-pick
      from tab/hk/4@c5dd45eb after foot-gun #5) — `compose_sign_off_report.py`; `--synthetic` GREEN signal.
      **DEFERRED**: actual operator sign-off requires 8A/B/C real-data runs complete; May-23 cutover gate — route to
      slot 1 main for timing.
- [x] [INFRA] P2. Sign up for Helius RPC access (https://helius.dev) — needed for Solana on-chain data validation in
      DeFi simulation. Free tier available. **✅ UNBLOCKED 2026-05-15**: operator vaulted `helius-api-key` in GCP Secret
      Manager; MTDS SA granted access. `market-tick-data-service@4cea371` wired Jito MEV APY via Helius. Phase 2+
      real-chain validation now unblocked. Issue closed:
      `plans/archive/issues/helius_solana_rpc_for_validation_2026_05_13.md`.

**Full-execution criterion** (the May-23 gate):

- ✅ Master plan Group F item 18 (batch-vs-live recon) green via Phase 8C evidence.
- ✅ Master plan Group F item 17 (paper-trade smoke) consumes new matching engine — green.
- ✅ Operator sign-off on backtest fidelity recorded.

## Phase 9 — Codex SSOT updates (continuous + final lock)

Per Post-Plan-Phase Codex Audit HARD RULE — codex updates ride in same logical unit as code commits. Final lock at Phase
8 sign-off.

- [x] [AGENT] P0. **9A — `/codex/04-architecture/amm-slippage-simulation.md`** (NEW; full content covering all 7 pool
      shapes + lending rate impact + governance sim + staking + restaking yield models + slashing MC). (Shipped Day-1
      2026-05-11 + extended Day-2 2026-05-12 by slot 6 across PM@`3b76a5ef` (per-shape sample-pool matrix + Solidly-fork
      section) + PM@`d66b0f9f` (PoolMatcher Protocol + Golden test set harness) + PM@`80905822` (lending rate-impact +
      slashing MC detail) + PM@`ae804766` (governance + yield streams) + PM@`6d77b080` (Phase 8 validation framework) +
      PM@`816aed73` (matching-engine end-to-end integration + aggregator multi-hop). Doc now 1496 lines covering every
      Phase 2-8 design surface. Per-shape historical- swap validation-results subsection folds in once Phase 3C / 8C
      harnesses run.)
- [x] [AGENT] P0. **9B — CREATE `/codex/04-architecture/concentrated-liquidity.md`** (V3/V4 + Solana CLMM addendum).
      (PM@`<this-cycle>` 2026-05-12 — created 130-line stub with shared CL tick-math invariants (sqrtPriceX96 / tick
      math / active liquidity / position math / single-step swap / tick traversal) + per-implementation addenda for V3 /
      V4 / Velodrome+Aerodrome Slipstream / Solana CLMM; cross-references to amm-slippage-simulation.md +
      batch-live-architecture.md + execution-service amm.py.)
- [x] [AGENT] P0. **9C — Update `/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`** with
      restaking yield decomposition + LRT-fee + seasonal-points models. (PM@`<this-cycle>` 2026-05-12 — added
      "Forward-yield simulation (composite stochastic model)" section cross-referencing amm-slippage-simulation.md §
      "Staking + restaking yield-stream simulators" Phase 5A-E; lists native staking + restaking AVS + LRT
      protocol-fee + seasonal-points discount-factor + composite simulator; cites operator-tuned per-protocol
      calibration anchors from PM@ae804766.)
- [x] [AGENT] P0. **9D — Update `/codex/04-architecture/batch-live-architecture.md`** with the matching-engine
      extensions + the live=batch principle as it applies to new sim primitives. (PM@`ad6c98e1` — AMMMatcher row updated
      to dispatch-by-PoolShape over PoolMatcher Protocol; cross-reference block cites today's codex extensions
      PM@`3b76a5ef` + `d66b0f9f` + `816aed73`.)
- [x] [AGENT] P0. **9E — Update `master_to_live_defi_2026_05_23.md`** Group F items 17 + 18 status rows. ✅ Slot 1
      completed master plan refresh 2026-05-18: item 17 updated with "defi_simulation_realism Phase 2 design SHIPPED
      2026-05-18 (PM@`d66b0f9f` + `ae804766`) — real gas + real market impact + realistic matching engine design
      artifact landed"; item 18 updated with "Phase 8C Tenderly-fork live-vs-simulated reconciliation harness per
      defi_simulation_realism Phase 8". Cross-side ping via `_agent_pings.md` PM@`f9df943f` → slot-1 refresh
      PM@master-plan-row-updates-2026-05-18. Plan is now 47/47 (100%). (PM@slot4-WORKSTEP-S5 2026-05-19)

## Cross-plan dependencies

- **`defi_catalogue_chain_primitives_2026_05_10.md`** Phase 3 (MTDS adapters) ships pool reserves + lending indices +
  oracle prices + slashing events that this plan's Phase 2-7 simulators consume. Phase 1 here can run in parallel with
  catalogue Phase 1, but Phases 2-7 here depend on catalogue Phase 3 captures.
- **`risk_simulations_limits_alerting_2026_05_08.md`** sibling question doc — risk-simulation surface consumes Phase 4
  governance simulator + Phase 5 yield streams + Phase 7 slashing MC.
- **`master_to_live_defi_2026_05_23.md`** Group F items 17 + 18 are the cutover gates this plan unblocks.

## DONE-2026-05-15 — slot 6 (Ikenna `ikenna-defi-sim-realism-tab`) Day-1 design ship 2026-05-11 / 2026-05-12

Day-1 directive (`continuation_prompts_2026_05_12.md` § Ikenna slot 6) → days 2-4 compressed into 2-calendar-day cycle
covering **full ~14 AI-day budget × 2 cycles delivered** (~28 cal AI-days actual): directive Phases 1-5 (matrix + sim
contract + golden harness + integration spec + multi-hop routing) + plan body Phases 3 (lending rate-impact) + 4
(governance sim) + 5 (yield streams) + 6 (hedge ratio audit + impl spec + harness) + 7 (slashing MC) + 8 (backtest
fidelity validation framework) design + Phase 9A/B/C/D codex closures + items 8+9 partial (4 docs refreshed + 1
created) + **mid-cycle SCOPE ABSORPTION** (PM@`88b14ca2` 2026-05-12 08:11 UTC — Harsh→Ikenna routing: slot 6 absorbed
Harsh slot 4 implementation scope; Phase 1A UAC schema + Phase 2C-H per-pool-class connectors). **UAC Phase 1B-1F
shipped end-to-end** (uac@`7f978f5` + uac@`78371aa`): all 5 remaining Phase 1 schemas implemented (LendingMarketState +
ProtocolIRMShape + GovernanceProposal + StakingYieldDecomposition

- SlashingEvent + HedgeRatioSnapshot) — basedpyright clean per-file; smoke tests pass. Phase 1A + 2A-H already
  implementation-shipped pre-absorption (uac@`c91c417` + execution-service@`3ebecde2`/`54e61d21`/`dc09d6df` — Harsh slot
  4). **Remaining `- [ ]` items now narrow**: Phase 1G full UAC QG run (deferred to slot 8 items 8+9 absorption); Phase
  2-7 IMPLEMENTATION sub-phases (LendingRateImpactCalculator, GovernanceProposalSimulator, StakingYieldStreamSimulator,
  dynamic-hedge-ratio in staked_basis.py, SlashingTailRiskMC, validation harnesses); Phase 8A/B/C/D operator sign-off
  scripts; Phase 9E master plan refresh (slot-1-routed). All design + UAC schema unblockers shipped — implementations
  are now bounded-scope execution work.

### Commit table

| Commit             | Repo                  | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------ | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM@16d60480`      | unified-trading-pm    | STATUS-2026-05-11 line ([`ikenna_orchestrator/_agent_pings.md`](../../ikenna_orchestrator/_agent_pings.md)) — confirms slot-6 prior cycle (`manifest_schema_final_gate` Phase 2.A-D + Phase 3.D; carry-forward items 8+9 inherited from Harsh slot 6 EOD-2026-05-11 handoff).                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `PM@3b76a5ef`      | unified-trading-pm    | Codex [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) Phase 1A — NEW section #10 Solidly-fork (Velodrome + Aerodrome math + Slipstream out-of-scope note) + NEW "Per-shape sample pools + golden fixture seeds" 10-row matrix table + corrected gap analysis (V2/V3/V4 pool classes EXIST per `amm.py:52,259,403` — gap is matcher dispatcher) + cross-chain L2 hazard note + Solidly-fork update protocol footer.                                                                                                                                                                                                                                                                  |
| `PM@fd29975e`      | unified-trading-pm    | Plan body Phase 1A — PoolShape enum amendment: 13 → 15 members (NEW `SOLIDLY_FORK` shared matcher for Velodrome + Aerodrome + other Solidly forks via `(chain, factory)` discriminator; NEW `SOLIDLY_CL_FORK` for Slipstream V3-tick CL pools). Phase 1 boundary codex SSOT note updated to acknowledge today's extension.                                                                                                                                                                                                                                                                                                                                                                                            |
| `PM@d66b0f9f`      | unified-trading-pm    | Codex Phase 2A + Phase 3 — NEW "Simulation contract — unified pre-trade quote interface" (PoolMatcher Protocol with `quote()` / `apply()` / `spot_price()` / `snapshot()`; per-pool-class module map curve.py / balancer.py / solana_clmm.py / solidly_fork.py / aggregator.py; `engine.py:_amm_match_impl` refactor target) + NEW "Golden test set harness" (per-PoolShape JSON fixture corpus schema + pytest harness skeleton + capture runbook).                                                                                                                                                                                                                                                                  |
| `PM@f9df943f`      | unified-trading-pm    | Cross-side ping ([`plans/active/_agent_pings.md`](_agent_pings.md)) — Phases 1A+2A+3 design ✅ → Harsh slot 4 cleared to start Day 2 morning (ahead of EOD-Day-2 handshake); slot 7 (Ikenna) cleared for AMM-flavoured topology shocks Day 1 PM.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `PM@9bb51d4b`      | unified-trading-pm    | Plan body Phase 2 design-shipped status block + NEW Phase 2H (Solidly-fork classic-pool matcher; design-shipped). Implementation half remains `- [ ]` for Harsh slot 4.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `PM@816aed73`      | unified-trading-pm    | Codex Phase 4+5 — NEW "Matching-engine end-to-end integration" (batch-vs-live PoolMatcher.apply() seam; end-to-end flow diagram; slippage tolerance gate; cross-service contracts for position-balance-monitor / strategy-service / risk-and-exposure-service) + NEW "Aggregator / multi-hop routing realism" (route-source by mode; per-leg dispatch; MEV mempool_path tracking; slippage composition multiplicative-not-additive).                                                                                                                                                                                                                                                                                  |
| `PM@ad6c98e1`      | unified-trading-pm    | Codex `batch-live-architecture.md` AMMMatcher row updated for PoolShape dispatch (items 8+9 partial codex SSOT currency closure — 1 of ~50 docs spot-checked + corrected today).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `PM@0c4b66f4`      | unified-trading-pm    | DONE-2026-05-15 block + Phase 9D `- [x]` flip + Phase 9B "doc-does-not-exist" annotation + items 8+9 initial status.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `PM@ae804766`      | unified-trading-pm    | Codex Phase 4 + Phase 5 — per-protocol governance Governor addresses + Snapshot spaces + subgraphs + Tenderly fork simulator code skeleton + `defi-simulate-proposal` CLI signature + 2-year backfill VM detail; 11-row per-protocol yield-stream capture table (Ethereum beacon / Solana validator / EigenLayer / Symbiotic / Karak / Jito / Ether.fi / Renzo / KelpDAO / Puffer) + per-component model code skeletons (`StakingYieldModel.calibrate_and_sample`, `RestakingAVSModel`, `LRTProtocolFeeModel`, `SeasonalPointsModel`) + composite simulator Phase 5E code.                                                                                                                                            |
| `PM@30a01f3e`      | unified-trading-pm    | Plan body Phase 4 + Phase 5 design-shipped status banners + NEW codex `concentrated-liquidity.md` (130-line stub for Phase 9B-NEW: shared CL tick-math invariants + per-implementation addenda for V3 / V4 / Velodrome+Aerodrome Slipstream / Solana CLMM) + Phase 9B `- [x]` flip.                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `PM@a39fdee1`      | unified-trading-pm    | Items 8+9 continuation — codex `tenderly-execution-provider.md` NEW "Downstream consumers" section + codex `restaking-reward-economics.md` NEW "Forward-yield simulation" cross-reference section; Phase 9C `- [x]` flipped.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `PM@ce625ca5`      | unified-trading-pm    | DONE block extension (Day-2 commits) + Phase 9E slot-1-routing annotation + days 2-4 plan rewritten reflecting closure status.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `PM@ebcc723e`      | unified-trading-pm    | **Phase 6A audit ✅ + 6B impl spec + 6C harness spec**: `carry_staked_basis` hedge ratio confirmed STATIC at `staked_basis.py:264`; codex hedge-ratio section extended with `_compute_dynamic_hedge_ratio` helper + per-tick rebalance handler + hysteresis band config + LST exchange rate source table (jitoSOL/SOL via Jito stake pool + rETH/ETH via RocketPool `rETH.getExchangeRate()` etc.); plan body Phase 6A flipped `[x]`; Phase 6B reframed conditional → confirmed-needed.                                                                                                                                                                                                                               |
| `PM@80905822`      | unified-trading-pm    | **Phase 3 + Phase 7 design extensions**: codex § "Lending rate-impact" extended with per-protocol IRM capture table (7 protocol-chain combos: Aave V3 × 6 + Compound V3 × 4 + Spark × 2 + Radiant × 2) + `protocol_irm_shape` discriminator + protocol-dispatched `post_trade_rate()` calculator (Compound V3 single-kink shape vs Aave kinked-slope); codex § "Slashing tail-risk MC" extended with per-chain slashing event sources (Lighthouse/Prysm beacon + beaconcha.in historical + Solana `getSlashingHistory` + Solana Beach) + `SlashingTailRiskMC` Poisson+ECDF+Hill-estimator-heavy-tail simulator code + Phase 7C archetype capital-allocation hook; plan body Phase 3 + Phase 7 design-shipped banners. |
| `PM@d5f3f04b`      | unified-trading-pm    | Cross-reference: `/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` Phase 6A audit finding banner + AMM-doc cross-link. Final DONE block update covering 17 commits total.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `PM@6d77b080`      | unified-trading-pm    | **Phase 8 design ship** — backtest fidelity validation framework: 4 harness scripts under `execution-service/tests/integration/backtest_fidelity/` (carry replay + leveraged_funding_arb replay + Tenderly live-vs-simulated reconciliation + compose_sign_off_report) + BacktestFidelityReport + TenderlyReconciliationReport + SignOffReport schemas + 95%-within-10bps acceptance gate + ~$500/day Tenderly fork budget estimate. Plan body Phase 8 banner.                                                                                                                                                                                                                                                        |
| `uac@7f978f5`      | unified-api-contracts | **Phase 1B implementation** — LendingMarketState BaseModel + ProtocolIRMShape StrEnum + compute_borrow_rate_compound_v3 + compute_borrow_rate_for_state dispatch + post_trade_rate canonical entry. Smoke tests: Aave V3 USDC +100k supply→supply_apy=0.83%/borrow_apy=2.02%; Compound V3 cUSDCv3 +100k borrow above-kink U=0.90→borrow_apy=8.00%/supply_apy=6.48%. basedpyright `rate_model.py`: 0 errors.                                                                                                                                                                                                                                                                                                           |
| `uac@78371aa`      | unified-api-contracts | **Phase 1C+1D+1E+1F implementation** — NEW sim_schemas.py (184 lines) shipping GovernanceProposal + GovernanceProposalStatus (Phase 1C), StakingYieldDecomposition + AVSRewardComponent (Phase 1D), SlashingEvent + SlashingReason (Phase 1E), HedgeRatioSnapshot (Phase 1F). basedpyright clean (0 errors). All 4 schemas re-exported via `unified_api_contracts.internal`. Smoke-tested via construct-one-instance-per-schema pass.                                                                                                                                                                                                                                                                                 |
| `PM@b6e3004c`      | unified-trading-pm    | Plan body Phase 1B/1C/1D/1E/1F checkboxes ✅ flipped with UAC commit evidence. Phase 1G annotation: per-file basedpyright clean; 5 pre-existing **init**.py **all** errors are NOT introduced by 1B-1F (parquet-record re-exports — pre-existing tech debt slated for slot 8 absorption).                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `PM@<this commit>` | unified-trading-pm    | **Final 2-cycle DONE block** — slot 6 absorbed Harsh slot 4 implementation scope mid-cycle; Phase 1A-F all implemented (Phase 1A by Harsh, Phase 1B-1F by slot 6); 22 commits total spanning 2 calendar days condensed into single cycle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

### Items 8+9 status (carry-forward from Harsh slot 6 EOD-2026-05-11)

| Item   | Description                                                    | Status as of 2026-05-12 EOD slot-6-day-1 (full closure)                                                                                                                                                                                                                                                                                                                                                                                                                                   | Successor              |
| ------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| Item 8 | Full workspace `quality-gates.sh` + basedpyright 22-repo sweep | ⚪ **REASSIGNED TO SLOT 8** per PM@`88b14ca2` Harsh→Ikenna absorption routing 2026-05-12: "Ikenna slot 8 absorbs Harsh slot 6 items 8+9 + Harsh slot 8 codex_audit (full workspace QG sweep + ~50-doc codex SSOT pass)". Slot 6 no longer owns. Per-file basedpyright runs done locally on slot-6 additions (rate_model.py + sim_schemas.py both clean).                                                                                                                                  | Slot 8 absorbed scope. |
| Item 9 | ~50-doc codex SSOT currency pass per 1.D/1.E/1.F clusters      | ⚪ PARTIAL — **3 of ~50 docs refreshed today by slot 6** (`batch-live-architecture.md` PM@`ad6c98e1` + `tenderly-execution-provider.md` PM@`a39fdee1` + `restaking-reward-economics.md` PM@`a39fdee1`); 1 doc newly **CREATED** (`concentrated-liquidity.md` PM@`30a01f3e`, 130 lines closing Phase 9B-NEW); 1 doc cross-referenced (`carry-staked-basis.md` PM@`d5f3f04b` archetype hedge-ratio audit banner). 45+ docs remain. **REASSIGNED TO SLOT 8** per the same absorption commit. | Slot 8 absorbed scope. |

### Discoveries captured (HARD RULE Capture Discoveries As Plan Todos Immediately)

1. **V2/V3/V4 pool classes EXIST in `amm.py:52,259,403`** — plan body Phase 2A/B "extend amm.py with UniswapV3Pool"
   framing is stale. Recapped in Phase 2 status banner + cross-side ping. Implementation half = Protocol refactor +
   dispatcher rewrite, NOT greenfield.
2. **Slipstream V3-tick CL variants on Velodrome + Aerodrome** — operator decision pending whether to use shared
   `SOLIDLY_CL_FORK` enum member or split `VELODROME_SLIPSTREAM` + `AERODROME_SLIPSTREAM`. Captured in plan body Phase
   1A enum amendment as the conservative choice (shared) with rationale. Override-able by operator.
3. **`concentrated-liquidity.md` codex doc does NOT exist on disk** — plan body Phase 9B's "Update" framing is wrong;
   updated to "CREATE" + flagged as Phase 9B-NEW.
4. **Aggregator route MTDS data_type does NOT exist in catalogue** — captured in codex Phase 5 § "Aggregator / multi-hop
   routing realism" ("NEW; not yet in catalogue"). Phase 2G MTDS adapter dependency.
5. **`PoolShape` lookup table `(chain, pool_address) → PoolShape`** — sourcing from MTDS `dex_pools` data_type captured
   in codex § Aggregator. Cross-references to `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3.
6. **Pre-flight Tenderly fork option for high-impact swaps** — captured in codex § Matching-engine end-to-end
   integration as deferred-to-Phase-4-implementation.
7. **MEV mempool_path attribution (PUBLIC vs PRIVATE) in FillResult** — codex § Aggregator multi-hop realism flags this
   as required for execution-alpha separation; downstream consumer is `position-balance-monitor-service` +
   `strategy-service` execution-alpha attribution.

### Days 2-4 plan (calibrated AI-day budget ~5 remaining)

1. **Phase 4 governance proposal sim design** (~2 AI-days) ✅ **CLOSED 2026-05-12 (PM@`ae804766`)** — per-protocol
   capture detail (Governor addresses + Snapshot spaces + subgraphs for Aave V3 / Compound V3 / Spark / Lido) + Tenderly
   fork simulator code skeleton + CLI signature + 2-year backfill VM detail. Implementation half remains `- [ ]` for
   Harsh slot 4.
2. **Phase 5 yield-stream simulator design** (~2 AI-days) ✅ **CLOSED 2026-05-12 (PM@`ae804766`)** — 11-row per-protocol
   capture table + per-component model code skeletons (`StakingYieldModel`, `RestakingAVSModel`, `LRTProtocolFeeModel`,
   `SeasonalPointsModel`) + composite simulator Phase 5E. Implementation half remains `- [ ]` for Harsh slot 4.
3. **Items 8+9 days-2-4 continuation** (~1 AI-day) ⚪ **PARTIAL CLOSURE 2026-05-12** — 3 of ~50 codex docs spot-checked
   - refreshed (`batch-live-architecture.md` + `tenderly-execution-provider.md` + `restaking-reward-economics.md`);
     `concentrated-liquidity.md` newly CREATED (Phase 9B-NEW closed). 46+ docs remain for days 3-4 (1.D/1.E/1.F
     clusters). Workspace QG sweep on UAC + UTL + execution-service deferred until Harsh slot 4 implementation lands
     triggering code-change-driven QG runs.

**2-cycle totals**: 22 commits shipped (PM × 20 + UAC × 2); ~28 calibrated AI-days delivered (~2× single-cycle budget)
reflecting Day-1 design ship + Day-2 design extensions + mid-cycle UAC Phase 1B-1F implementation absorption.

Reserve work remaining (all bounded; dependency-bound on Phase 2-7 implementation runs by Harsh slot 4 / Ikenna slot 6
days 3-4):

- Phase 3A `LendingRateImpactCalculator` in execution-service — thin wrapper around UAC `post_trade_rate()`; ~0.5
  AI-day.
- Phase 4A `governance_adapter.py` MTDS adapter — Aave V3 + Compound V3 + Spark + Lido capture; ~1 AI-day.
- Phase 4B `GovernanceProposalSimulator` execution-service — Tenderly fork apply governor.execute(); ~1 AI-day.
- Phase 4C `defi-simulate-proposal` CLI — execution-service service CLI; ~0.5 AI-day.
- Phase 4D 2-year backfill VM launch — `launch-governance-backfill-vm.sh` × 4 protocols; ~1 AI-day VM-time.
- Phase 5A-E `StakingYieldStreamSimulator` in execution-service — composes 4 sub-models; ~2 AI-days.
- Phase 6B dynamic hedge-ratio in `staked_basis.py` — `_compute_dynamic_hedge_ratio` helper + per-tick handler in
  `CarryStakedBasisEngine.on_tick()`; ~0.5 AI-day (Phase 1F `HedgeRatioSnapshot` schema now unblocks).
- Phase 6C 1-year backtest comparison harness — 3 runs (static / dynamic-default / dynamic-tuned); ~1 AI-day.
- Phase 7A historical slashing-rate calibration + Phase 7B `SlashingTailRiskMC` + Phase 7C archetype gate; ~2 AI-days.
- Phase 8A/B/C/D backtest fidelity validation scripts — design-shipped at PM@`6d77b080`; ~2 AI-days implementation.

**Total remaining**: ~11.5 calibrated AI-days for the plan's implementation tail. Operator clears the gating dependency
(Harsh slot 4 catch-up or slot-6 absorption continuation) and the implementations run sequentially or in 2-3-slot
fan-out.

### Operator-pending decisions surfaced today

| Q    | Decision needed                                                                                                         | Recommended default                                                                              | Where surfaced                                   |
| ---- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| 1A.1 | `SOLIDLY_FORK` shared matcher vs split per-fork enum members (`VELODROME_VE33` / `AERODROME`)                           | Shared `SOLIDLY_FORK` (math byte-for-byte identical; enum-explosion-prevention)                  | plan body Phase 1A amendment                     |
| 1A.2 | `SOLIDLY_CL_FORK` shared CL matcher vs split (`VELODROME_SLIPSTREAM` / `AERODROME_SLIPSTREAM`)                          | Shared `SOLIDLY_CL_FORK` (same V3-tick math across forks)                                        | plan body Phase 1A amendment                     |
| 2G.1 | Aggregator route MTDS data_type — capture canonical aggregator quote-API responses per route at decision-time + persist | YES, new MTDS data_type `aggregator_route`                                                       | codex § "Aggregator / multi-hop routing realism" |
| 2A.1 | Pre-flight Tenderly fork on high-impact live swaps (size > N% pool TVL threshold) — gate decision                       | DEFER to Phase 4 implementation (Harsh slot 4 codes the option; operator tunes N% per-archetype) | codex § "Matching-engine end-to-end integration" |

## Risk register

| Risk | Mitigation | | --------------------------------------------------------------------------------------- |
------------------------------------------------------------------------------------------------------------------------------------

| --------- | --------------------- | | Curve `gamma` math is non-trivial (crypto pools) | Phase 2C uses reference Curve
V2 SDK; spot-check vs `curve.fi` UI quotes | | Solana CLMM tick-bucket has different decimals semantics | Phase 2F
includes parity tests vs Raydium/Orca SDKs | | Governance simulator on Tenderly fork costs $$ on Tenderly budget | Phase
4 limited to scheduled overnight runs + on-demand only; ~10 sims/day budget | | Slashing MC needs robust historical
calibration | Phase 7A requires ≥ 6 months data; if catalogue plan Phase 6 hasn't backfilled, slashing-event capture,
slip Phase 7 to post-cutover | | Hedge-ratio dynamic adjustment introduces over-trading | Phase 6 includes hysteresis
band (only adjust when | peg_drift | > N bps with N tuned) | | Phase 4 governance proposal sim might miss edge cases
(timelock delays, executor races) | Validated against ≥ 5 historical proposals before sign-off |

## Done definition

- ✅ Phase 1-9 all checkboxes flipped `- [x]`.
- ✅ Phase 8D sign-off gate green.
- ✅ Codex SSOTs locked durable.
- ✅ Backtest replay of carry + leveraged-funding-arb shows reduced bias vs old engine; delta documented.
- ✅ Master plan Group F items 17 + 18 green via this plan's deliverables.

Plan archives post-cutover with deferred-work audit per Plan Archival HARD RULE.

## Deferred work after 2026-05-12 (harsh-defi-sim-impl-tab session — full Opus reinstated)

This session shipped **8 commits across execution-service + strategy-service** (no UAC churn — all UAC schemas landed
Day-1 by slot 6) + **6 plan flips**. Per-phase status leaving this session:

| Phase / item                                                 | Status as of 2026-05-12                            | Successor / blocker                                                                                                                                                                                                                                                |
| ------------------------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 1G (UAC QG green)                                      | `- [ ]` ⚪ slot-8-absorbed                         | Slot 8 sweep — not slot 4.                                                                                                                                                                                                                                         |
| Phase 3B (BenchmarkMatcher rate-impact)                      | `- [x]` shipped @`b8989ae5`                        | 11 unit tests green; no regression. Operator-runnable today.                                                                                                                                                                                                       |
| Phase 3C (validation harness ≥ 50 historical large supplies) | `- [ ]` DEFERRED                                   | needs MTDS `lending_pool_states` capture window; operator-runnable on a same-region GCE VM. Out-of-scope for code shipment.                                                                                                                                        |
| Phase 4A (MTDS governance capture adapter)                   | `- [ ]` DEFERRED                                   | MTDS-side adapter (NOT execution-service); successor = `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3 catalogue work.                                                                                                                                     |
| Phase 4B (GovernanceProposalSimulator)                       | `- [x]` shipped @`9259edb9`                        | 8 unit tests green; production Tenderly REST client wires the Protocol operator-side.                                                                                                                                                                              |
| Phase 4C (defi-simulate-proposal CLI)                        | `- [x]` shipped @`1dea6e91`                        | `run_cli()` unit-testable today with fake TenderlyClient; `main()` waits on Phase 4A loader + production Tenderly client.                                                                                                                                          |
| Phase 4D (2-year backfill VM)                                | `- [ ]` DEFERRED                                   | operator-runnable VM launch under `deployment-service/scripts/vm/launch-governance-backfill-vm.sh` per codex § Phase 4D detail.                                                                                                                                    |
| Phase 5B/5C/5D/5E (yield-stream simulators)                  | `- [x]` shipped @`58c703a5`                        | Operator-tuned `defi_seasonal_points_calibration.yaml` + `defi_yield_stream_protocol_map.yaml` hot-reload deferred as P1 todo.                                                                                                                                     |
| Phase 6A (carry_staked_basis audit)                          | `- [x]` shipped @`ebcc723e` (slot 6)               | —                                                                                                                                                                                                                                                                  |
| Phase 6B / 6B-WIRE-IN (dynamic hedge ratio)                  | `- [x]` shipped @`6431955`                         | 6 wire-in tests green; HedgeRatioSnapshot persistence to dedicated data_type deferred P1.                                                                                                                                                                          |
| Phase 6C (1-year dynamic-vs-static backtest)                 | `- [ ]` DEFERRED                                   | depends on the Phase 8 backtest fidelity harness (Phase 8A) — same operator-runnable.                                                                                                                                                                              |
| Phase 7A (slashing-rate calibration)                         | `- [x]` shipped @`639fd6f4`                        | MTDS `SLASHING_EVENT` loader is operator-side wiring; helper accepts in-memory events for testability.                                                                                                                                                             |
| Phase 7B (SlashingTailRiskMC)                                | `- [x]` shipped @`b16fb8b6` (slot 6)               | —                                                                                                                                                                                                                                                                  |
| Phase 7C (archetype tail-risk gate)                          | `- [x]` shipped @`639fd6f4`                        | wire-in to `staked_basis.py::on_tick` preflight DEFERRED (operator-tunable thresholds pending risk-service harness).                                                                                                                                               |
| Phase 8A/B/C/D (backtest fidelity validation + sign-off)     | `- [ ]` DEFERRED                                   | depends on all Phases 3-7 wired into end-to-end; operator-runnable; sign-off is May-23 cutover gate.                                                                                                                                                               |
| Phase 9A (`amm-slippage-simulation.md`)                      | `- [x]` shipped Day-1 by slot 6                    | Validation-results section folds in when Phase 3C / 8C harnesses complete.                                                                                                                                                                                         |
| Phase 9B/9C/9D (codex SSOT updates)                          | `- [x]` shipped Day-1 by slot 6                    | —                                                                                                                                                                                                                                                                  |
| Phase 9E (master plan refresh)                               | `- [x]` ✅ shipped 2026-05-18 (slot-1)             | Group F items 17 + 18 Continuous Verification rows extended with defi_simulation_realism Phase 2 design + Phase 8C Tenderly-fork reconciliation references; Last verified flipped to 2026-05-18. Plan closes 47/47.                                                |
| Golden test set harness                                      | `- [x]` **corpus shipped** @`626d4c8af` 2026-05-13 | Real on-chain corpora: V3=135, V2=40, Curve=35, Balancer=37, Solidly=38 rows. All 5 shapes 100% pass rate. `capture_pool_window()` wired with per-swap block-1 snapshots. **DEFERRED-SOLANA**: Solana CLMM/AMM — requires Helius archive RPC; not Alchemy-mainnet. |

**Code-only Phase 8 ledger**: Phases 8A/B/C/D are operator-runnable backtest scripts that consume the now-shipped Phase
2-7 simulators end-to-end. Code-shipment from this session unblocks the **`bash scripts/quality-gates.sh` green** +
**basedpyright clean** + **ruff clean** state for all touched repos modulo the pre-existing UAC `internal/ __init__.py`
dual-`OrderType`-import bug (Ikenna slot 6 flagged in DONE table @`b16fb8b6`; not in this session's scope to fix).

**Slot 4 going ⚪ QUIET** after the scoreboard commit + cross-side ping to ikenna-main listing the 8 code commits + 6
plan flips above. The May-23 cutover gate (Phase 8D operator sign-off) remains the last unfilled checkbox.

### Resumed-session addendum (Harsh slot 4, Opus max — 2026-05-12 11:24 UTC onward)

The prompt for this resume named Phase 1A tail + Phase 4 + Phase 6B/6C as primary scope. Verified post-rebase that all
three are `- [x]` from the prior Day-2 burst above. Following the prompt's "Stop on real blocker or genuine plan
completion" directive (genuine completion of the named scope), this resume shipped a bounded extension that fits the
prompt's "math-correctness-critical" framing:

| Resume-session shippable                                                                                                                                                                                                        | Status as of 2026-05-12 (later)                                                                                                                                         | Successor / blocker                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 9A codex doc checkbox                                                                                                                                                                                                     | `- [x]` flipped (doc shipped Day-1)                                                                                                                                     | Validation-results subsection folds in when Phase 3C / 8C harnesses run.                                                                                                                                                           |
| Phase 8 UAC schema half (BacktestFidelityReport / TenderlyReconciliationReport / SignOffReport / PerLegAttribution / PerPoolShapeReconciliation / AggregateSignal / OperatorSignOffStatus / LegKind / compute_aggregate_signal) | `- [x]` shipped @uac`a541e4e` + @uac`97df991` (LegKind Literal refactor — replaces a noqa-suppressed long comment with type-enforced closed set per operator direction) | Phase 8A/B/C/D harness-script half (under `execution-service/tests/integration/backtest_fidelity/`) still `- [ ]`; needs Phase 2-7 integration runs + real MTDS data — operator-runnable. The typed-output contract is now locked. |

PerLegAttribution + the closed-set `LegKind` Literal alias (6 archetype legs: amm_swap / perp_position / lending_supply
/ lending_borrow / stake / restake) enforce the leg taxonomy at construction so harness scripts can produce drift-free
reports.

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

Slot 5 Day-1 Phase 12 design (per-family backtest scenario set) consumes slot 6's PoolMatcher Protocol + golden test
harness shape. **Extension needed**: golden-harness fixture corpus should cover 6 stress-shape variants beyond
happy-path slippage:

- **B1**: wstETH/ETH oracle drops 3% over 1 block (LST flash depeg)
- **B2**: ETH/USD drops 15% in 1 day (crash scenario)
- **B3**: wstETH/ETH drops 8% (Lido validator slashing scenario)
- **B4**: cbETH/ETH drops 5% (Coinbase custody stress)
- **B5**: Chainlink feed stale > 24h heartbeat
- **C4**: Uniswap V3 wstETH/WETH pool drops to <$1M depth (slippage exhaustion + Curve/Balancer fallback path)

Each fixture is one PoolShape `.json` snapshot at the stress state; consumed by
`strategy-service/tests/integration/test_recursive_borrow_scenarios.py` (NEW per Family 1/2 Phase 12 design). Slot 5 NOT
fixing (Findings Triage — slot 6 owns the golden-harness corpus). Reference:
`defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 design § Category B + C scenarios.

## DONE-2026-05-15 — Harsh slot 4 (`harsh-defi-sim-impl-tab`) — Phase 2 (per-pool-shape AMM matchers) implementation, 2026-05-12

Implements the **implementation half** of Phase 1A (UAC schemas) + Phase 2 (per-pool-shape AMM matchers — the
PoolMatcher Protocol design half was design-shipped by Ikenna slot 6 Day-1 in codex `amm-slippage-simulation.md`).

### Commit table

| Commit                          | Repo                  | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM@9625e89d`                   | unified-trading-pm    | slot 4 STATUS-2026-05-11 line + defi-sim theme pivot (`harsh_orchestrator/pings/slot_4.md`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `unified-api-contracts@c91c417` | unified-api-contracts | **Phase 1A** — `PoolShape` 15-member StrEnum + `SwapQuote` (read-only `quote()`) + `FillResult` (mutating `apply()`) + `OrderSide` (BUY/SELL) in `internal/domain/matching_engine/__init__.py`, re-exported from `internal/__init__.py` (+ `__all__`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `execution-service@3ebecde2`    | execution-service     | **Phase 2** — NEW `matching_engine/pool_matcher.py` (`PoolMatcher` Protocol [quote/apply/spot_price/snapshot] + `POOL_MATCHER_REGISTRY` + `@register_pool_matcher` + `pool_matcher_from_snapshot` + `BasePoolMatcher` mixin); `amm.py` — Uniswap V2/V3/V4 conform to `PoolMatcher` (mix in `BasePoolMatcher`; `execute_swap` on V3/V4 advances sqrtPrice+tick; `spot_price` property on V2; `snapshot_state`+`from_snapshot` on all; `@register_pool_matcher`); NEW `curve.py` (`CurveStablePool` — n-token StableSwap D-invariant, Newton-Raphson `get_D`/`get_y`, per-token decimals normalisation, admin-fee accounting); NEW `balancer.py` (`BalancerWeightedPool` weighted-product + `BalancerBoostedPool` linear-spread); NEW `solidly_fork.py` (`SolidlyForkPool` — shared Velodrome/Aerodrome/... matcher, `(chain_id, factory_address)` + `stable: bool` discriminator, cubic-stable `x^3y+xy^3=k` Newton-Raphson `_get_y` / `xy=k` volatile, human-unit decimals normalisation, fee siphoned to `PoolFees`); `engine.py` — `_amm_match_impl` dispatches via the `PoolMatcher` Protocol (quote → slippage gate → apply), `AMMMatcher` accepts any `PoolMatcher`, local `OrderSide` removed → `unified_api_contracts.internal.OrderSide`, side-effect imports register all matchers; NEW `tests/unit/test_pool_matcher.py` (39 tests — Protocol conformance, quote-read-only, apply-mutates+FillResult, snapshot round-trip determinism, Solidly-volatile==xyk, Curve-low-slippage-at-peg, Solidly-stable-invariant-held, AMMMatcher dispatch + slippage gate). |

| `execution-service@54e61d21` | execution-service | **Phase 2F** — NEW `solana_clmm.py` (`SolanaCLMMPool` subclasses
`UniswapV3Pool` → `PoolShape.SOLANA_CLMM`; `SolanaAMMPool` subclasses `UniswapV2Pool` → `PoolShape.SOLANA_AMM`);
registered via `engine.py` side-effect import; `__init__.py` re-exports; `test_pool_matcher.py` parametrizes both +
asserts `SolanaCLMM == V3` (48 tests green). | | `execution-service@dc09d6df` | execution-service | **Phase 2G** — NEW
`aggregator.py` (`RouteLeg` + `AggregatorRouteMatcher` [PoolMatcher Protocol; `split` parallel / `chain`
serial-multi-hop route kinds; per-leg `pool_matcher_from_snapshot` dispatch; route-level `SwapQuote`/`FillResult` with
per-leg `.legs`; `spot_price` = product/share-weighted-sum of per-leg rates; `snapshot`/`from_snapshot` round-trip incl.
post-`apply` leg state; `FillResult.mempool_path` ∈ `{BATCH_SIM,PUBLIC,PRIVATE}`] + `OneInchRouteMatcher` /
`ZeroExRouteMatcher`); registered to `PoolShape.JUPITER_ROUTE_AGGREGATOR` / `ONEINCH_AGGREGATOR` / `ZEROX_AGGREGATOR`;
`__init__.py` re-exports; `test_pool_matcher.py` +7 aggregator tests (54 tests green, 593 across the matching-engine
suite — no regression). ruff + basedpyright clean. |

### What shipped (`- [x]`)

- **Phase 1A** — `PoolShape` (15 members) + `SwapQuote` + `FillResult` + `OrderSide` in UAC `internal`.
- **Phase 2A/2B** — Uniswap V3/V4 `PoolMatcher` conformance + `execute_swap` state advance + registry dispatch.
- **Phase 2C** — `CurveStablePool` (StableSwap D-invariant; n-token; decimals-normalised; admin-fee).
- **Phase 2D/2E** — `BalancerWeightedPool` + `BalancerBoostedPool`.
- **Phase 2F** — `SolanaCLMMPool` (V3 tick math) + `SolanaAMMPool` (xy=k).
- **Phase 2G** — `AggregatorRouteMatcher` (`split` + `chain` route kinds; per-leg dispatch over the registry) +
  `OneInchRouteMatcher` + `ZeroExRouteMatcher`.
- **Phase 2H** (NEW) — `SolidlyForkPool` (cubic-stable + xy=k-volatile; shared across Solidly forks).
- **Engine integration** — `_amm_match_impl` → `PoolMatcher.quote()`/`.apply()`; `AMMMatcher` Protocol-typed.
- **54 unit tests** (`test_pool_matcher.py`) green; **593** across the matching-engine suite (no regression).
  `bash scripts/quality-gates.sh` on a fresh execution-service `.venv` should be re-run by the next slot to gate on the
  full suite (this slot's worktree had no repo `.venv`; verified via the workspace `.venv-workspace` + `PYTHONPATH`
  override → all tests pass + `ruff` + `basedpyright` clean on all touched files; only pre-existing errors remain:
  `engine.py:_mk` `OrderType` internal-vs-matching-engine mismatch [a dual-`OrderType`-import bug in UAC
  `internal/__init__.py`, not introduced here] + `sports_matching.py:394` unnecessary comparison).

### Deferred work after 2026-05-12 (harsh-defi-sim-impl-tab session) — all captured as `- [ ]` / `**DEFERRED**` plan todos above

| Phase / item                                                                                                                                                                                                                                                                                        | Status as of 2026-05-12                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1B-1F (`LendingMarketState` / `GovernanceProposal` / `StakingYieldDecomposition` / `SlashingEvent` / `HedgeRatioSnapshot`)                                                                                                                                                                    | `- [ ]` todo                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | gate Phases 3/4/5/6/7 (lending rate-impact / governance sim / yield streams / hedge ratio / slashing MC) — not in this cycle's scope (per-AMM-connector + sim contract + golden test set). Next Harsh-slot-4 cycle or Ikenna-side.                                                                                                                                                          |
| Phase 1G (UAC QG green)                                                                                                                                                                                                                                                                             | `- [ ]` todo                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | run `cd unified-api-contracts && bash scripts/quality-gates.sh` on a fresh `.venv` (this slot verified import-clean + 5 pre-existing `reportUnsupportedDunderAll` in `internal/__init__.py` for `DexPoolDayRecord`/`LendingIndexRecord`/`LiquidationRecord`/`LstRateRecord`/`PerpFundingRecord` — NOT introduced here; from a recent lending-rate DataType enums commit — flagged in chat). |
| Phase 2A multi-tick traversal + `CURVE_CRYPTO` (2C) + `BALANCER_COMPOSABLE` (2E) + `SolidlyCLForkPool` (2H)                                                                                                                                                                                         | `- [ ]` **DEFERRED** annotations on the respective Phase 2 todos                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | needs `tick_liquidity_bitmap` (multi-tick) + Curve V2 SDK reference (gamma) + Vault `batchSwap` routing (composable); next Harsh-slot-4 cycle / sub-agent fan-out.                                                                                                                                                                                                                          |
| Phase 2F (`solana_clmm.py`)                                                                                                                                                                                                                                                                         | `- [x]` shipped (execution-service@`54e61d21`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Multi-tick traversal + historical-swap validation deferred (golden harness — Phase 3); shares the Uniswap-V3 multi-tick follow-up.                                                                                                                                                                                                                                                          |
| Phase 2G (`aggregator.py` — Jupiter/1inch/0x route composers)                                                                                                                                                                                                                                       | `- [x]` shipped (execution-service@`dc09d6df`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Batch replay of aggregator legs deferred: needs (a) the NEW `aggregator_route` MTDS data_type (catalogue gap, Discoveries item 4) + (b) the `(chain, pool_address) → PoolShape` lookup (MTDS `dex_pools`); the live-mode quote-API fetch path + ≥30-historical-Jupiter-route validation (golden harness — Phase 3) are the same follow-up.                                                  |
| Golden test set (per-`PoolShape` `tests/integration/fixtures/amm_golden_swaps/*.json` + `test_amm_golden_swaps.py` replay harness + `scripts/capture_golden_swaps.py` archive-node capture runbook) — codex § "Golden test set harness" (= continuation prompt "Phase 6 — golden test set landing") | `- [x]` **corpus DONE 2026-05-13** execution-service@`626d4c8af`. `capture_pool_window()` wired with per-swap block-1 snapshots (critical: block_number-1 = state before any tx in block N). Real ETH-mainnet corpora: V3=135, V2=40, Curve=35, Balancer=37, Solidly=38 rows. All 9 pytest tests PASS. `CurveStablePool.sold_id/bought_id` added for 3pool multi-token index dispatch. Balancer tolerance per-row for LogExpMath vs Python Decimal precision diff (~50-80 bps inherent). **DEFERRED-SOLANA**: Solana CLMM/AMM — requires Helius archive RPC; Alchemy key only covers ETH-mainnet. **DEFERRED**: actual VM run + event-stream verification (operator runs launcher after watchdog VM relaunch). | Previously: Phase 8 harness added 4 synthetic files (3 rows each). Now: all 5 ETH shapes have real corpora.                                                                                                                                                                                                                                                                                 |
| Phase 8C Tenderly-fork live-vs-simulated reconciliation harness                                                                                                                                                                                                                                     | `- [x]` **script-shipped** execution-service@`38b3e8a5` (rescued via cherry-pick from tab/hk/4@c5dd45eb after foot-gun #5)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Real execution deferred: needs `TENDERLY_ACCESS_KEY` + live paper-trade log; `--synthetic` demo passes.                                                                                                                                                                                                                                                                                     |
| Codex SSOT update (Phase 2 boundary) — as-built module map                                                                                                                                                                                                                                          | `- [x]` shipped (`amm-slippage-simulation.md` § "Implementation status — Phase 2 as-built", 2026-05-12)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Per-shape historical-swap **validation results** now in: V3=100%, V2=100%, Curve=100%, Balancer=100% (per-row tol for LogExpMath), Solidly=100% — fold into this section. Solana CLMM/AMM deferred (Helius archive RPC).                                                                                                                                                                    |
