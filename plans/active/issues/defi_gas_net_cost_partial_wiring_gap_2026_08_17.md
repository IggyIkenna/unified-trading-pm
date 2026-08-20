---
doc_type: issue
title: DeFi gas net-cost wiring is genuinely mixed — several live strategy engines silently default gas cost to 0
summary: >-
  Grep-then-read verification (defi_satellite_ao_dispatch_batch16_2026_08_17.md's gas-net-cost-consumer todo) found
  gas_price × gas_units cost netting is REAL and wired in some places (execution-service's DeFi cost aggregator, the
  liquidation-bundle MEV engine, the realized-PnL pipeline) but in four other live strategy-engine code paths the
  formula exists yet reads a feature/config value that nothing ever produces, so it silently evaluates to gas_cost=0
  in actual paper/live runs — a real profitability-gating correctness gap, not a documentation gap.
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [strategy-service, execution-service, features-service]
scope: [engineer]
tags: [data-correctness, defi, gas-cost, strategy-correctness, silent-default, pnl]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
  ]
created: 2026-08-17
author: unknown
priority: P1
parent_epic: defi_master
source: >-
  Grep-then-read verification pass for defi_satellite_ao_dispatch_batch16_2026_08_17.md's `[STRATEGY] [EXECUTION] P2`
  "verify (and wire if absent) the downstream gas net-cost consumer" todo (source: defi_migration_audit_log_2026_07_24.md
  line ~552). A prior thoroughness pass (2026-06-16, carry_staked_basis_funding_scan_experiment_2026_06_16.md) already
  confirmed `gas_cost_usd = gas_units × gas_price × native_price` exists in execution-service and the gas-price DATA is
  captured; this doc is the first to trace the CONSUMER side per live strategy engine and find several read a value
  nothing produces.
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
context_scope:
  [
    strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/liquidation_capture.py,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
    strategy-service/strategy_service/engine/strategies/v2/mev/jit_liquidity.py,
    strategy-service/strategy_service/engine/strategies/v2/mev/backrun.py,
    strategy-service/strategy_service/cli/handlers/paper_run_handler.py,
    features-service/features_service/onchain/app/calculators/gas_cost_usd_calculator.py,
  ]
resolved_by:
---

# DeFi gas net-cost wiring — genuinely mixed, several silent-zero gaps

> **🔴 A live DeFi arb/carry strategy engine that silently computes profitability with an unaccounted (defaulted to
> zero) gas cost can gate a trade as profitable when it is not.** This is a strategy-correctness class finding, not a
> data-pipeline one — flagging per the cross-cutting "big finding" triage rule rather than closing quietly.

## 1. What was checked (grep-then-read, not a grep-only scan)

Every DeFi arb/carry/MEV strategy engine in `strategy-service/strategy_service/engine/strategies/v2/`, plus
execution-service's gas-cost models and features-service's onchain calculators. Full per-file citations below.

## 2. WIRED — real gas_price × gas_units, netted into a decision or into realized P&L

1. `execution-service/execution_service/matching_engine/defi/gas_cost_model.py:87-109` —
   `estimate_gas_cost_usd(action, gas_price_gwei, native_token_usd, l1_data_cost_usd)`, calibrated per-action gas
   units.
2. `execution-service/execution_service/matching_engine/defi/cost_aggregator.py:112-202` —
   `DefiCostAggregator.estimate_recursive_loop_cost()` / `build_defi_fill_context()` feeds gas + slippage + flash
   premium into `FillAttributionContext.fee_amount_modelled` for the recursive-borrow DeFi archetypes.
3. `strategy-service/strategy_service/engine/strategies/v2/mev/liquidation_bundle.py:87-107,158,166,290-303` —
   `estimate_bundle_profit_usd()` computes `profit = seized - swap_loss - debt_amount_usd - flash_fee - gas_cost_usd`
   and gates emission on `profit >= min_net_profit_usd`. Self-contained (`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`), no
   missing upstream dependency.
4. `strategy-service/strategy_service/pnl/engine/pnl_input_builder.py:153-186,304-321` →
   `strategy_service/pnl/engine/breakdown.py:68-69` → `strategy_service/pnl/engine/orchestrator.py:574-594` →
   `strategy_service/engine/core/pnl_calculator.py:373-376` — a real, fail-loud (no silent default)
   `gas_used × gas_price × native_token_price_usd` chain subtracted from realized/attributed P&L per fill. This is
   POST-trade accounting, not a pre-trade profitability gate.

## 3. NOT WIRED — formula/docstring exists, but the consumed value is never produced (silently 0 in real runs)

1. **`LIQUIDATION_CAPTURE`** — `strategy-service/.../arbitrage_structural/liquidation_capture.py:87,99-108`:
   `gas_cost = features.get("gas_cost_usd") or 0.0`, then `gross_profit = bonus_usd - slippage_usd - gas_cost`,
   gated on `min_profit_usd`. No calculator under `features-service/features_service/onchain/` emits a
   `gas_cost_usd` feature key (grepped the whole tree — only `gas_price_gwei` raw price and a regime-label bucketing
   exist, see §4). So this engine's own real netting formula runs with `gas_cost` permanently `0.0` today.
2. **`CARRY_STAKED_BASIS`** — `strategy-service/.../carry_and_yield/staked_basis.py:459-460`:
   `net_carry = f * (staking_apy + funding_apy) - fees`, `fees = features.get("fees_apy_bps", 0.0)`. The field's own
   docstring says it folds in "funding, swap, gas." Grepped every producer of `fees_apy_bps` workspace-wide: it is set
   ONLY in tests (hardcoded) and in `strategy-service/.../cli/handlers/paper_run_handler.py:342,1196`, which itself
   hardcodes `"fees_apy_bps": 0.0`. **`elysium_carveout_stubbed_strategy_service_2026_08_12.md`'s §-on `fees_apy_bps`
   already noted this field is "optional" for that specific client-scope question — this finding is broader**: even
   outside the elysium carve-out, every real paper/live run of `CARRY_STAKED_BASIS` today nets a permanent 0 for gas,
   not just an elysium-scope omission.
3. **`JIT_LIQUIDITY`** — `strategy-service/.../mev/jit_liquidity.py:4-7,68-113`: module docstring explicitly states
   "the economic threshold is that the captured fees exceed gas + impermanent loss + the flash-loan fee," but the
   actual `on_tick()` only checks `pending_size < min_swap_threshold_usd` — no gas, IL, or flash-fee computation
   exists anywhere in the file. This is a documentation-promises-a-gate-that-does-not-exist case, not a
   feature-plumbing gap.
4. **`BACKRUN`** — `strategy-service/.../mev/backrun.py:73-93`: uses
   `block_priority_gas_p90_gwei_<chain>` (a real, produced feature — see
   `features-service/.../calculators/block_priority_gas_distribution_calculator.py:72-151`) only to size the
   inclusion bid (`priority_gas_bid = priority_gas_p90 * priority_gas_uplift`) — it is never subtracted from the
   arb spread the engine gates on (`spread_bps < min_spread_bps`, `:86`). The gas DATA reaches this engine; it is
   simply never netted against the profit gate.

## 4. features-service — confirms the search was thorough, not merely absent

- `block_priority_gas_distribution_calculator.py:72-151` — produces per-block P50/P90/P99 priority-fee gwei
  percentiles (consumed only by BACKRUN's bid-sizing, per §3.4).
- `onchain_regime_calculator.py:87-97,133,176` — `_bucket_gas(gas_price)` classifies raw `gas_price_gwei` into a
  low/medium/high regime label — a classification, not a cost.
- No calculator anywhere under `features-service/features_service/onchain/` produces `gas_cost_usd` or
  `fees_apy_bps`. `execution_cost_estimator.py`'s `ExecutionCostEstimator` (execution-service) is explicitly
  documented (module docstring) as intended "for strategy-service signal filtering," but strategy-service has zero
  import/call sites of it (grepped the whole `strategy_service/` tree) — an unconfirmed/likely-unused consumer path,
  a fifth candidate gap not counted in §3 since it was never claimed to be wired.

## 5. Todos

- [x] ✅ [FEATURES] P1. Add a `gas_cost_usd` feature calculator under `features-service/features_service/onchain/` (per
      chain/action, mirroring `execution-service/execution_service/matching_engine/defi/gas_cost_model.py`'s
      `GAS_UNITS` table and `gas_price × gas_units × native_token_price` formula) so `LIQUIDATION_CAPTURE`
      (`strategy-service/.../arbitrage_structural/liquidation_capture.py:87`) stops reading a permanent `0.0`. Repo:
      features-service. Done when: `LIQUIDATION_CAPTURE`'s `gas_cost` is confirmed non-zero on a real block in a
      paper run, with a regression test. — features-service@20d71ed0fb, strategy-service@0088d62fe8 (see Progress
      Log for the "paper run" scope note).
- [x] ✅ [STRATEGY] P1. Wire a real `fees_apy_bps` (or an explicit gas-only sub-term) into
      `strategy-service/.../carry_and_yield/staked_basis.py:459-460`'s `net_carry` calc — replace
      `paper_run_handler.py:342,1196`'s hardcoded `0.0` with the real computed value once the features.py-side
      producer exists (may share the P1 calculator above, or a dedicated funding/swap/gas composite — needs a short
      design decision on scope, not a blind guess). Repo: strategy-service (+ features-service if the composite
      lives there). Done when: `CARRY_STAKED_BASIS` nets a real non-zero gas term in a live/paper run, with a
      regression test; `paper_run_handler.py`'s hardcode removed. — strategy-service@f09969fe94
- [x] ✅ [STRATEGY] P2. Implement `JIT_LIQUIDITY`'s (`strategy-service/.../mev/jit_liquidity.py`) documented
      gas+IL+flash-fee profitability threshold in `on_tick()`, or correct the docstring if the threshold is
      deliberately not enforced (state which, with the reasoning). Repo: strategy-service. Done when: either the
      threshold is implemented and unit-tested, or the docstring is corrected to match actual behavior with a cited
      reason. — strategy-service@fbf78dfe20 (see Progress Log for the scope note on the IL term).
- [ ] [STRATEGY] P3. Net `BACKRUN`'s (`strategy-service/.../mev/backrun.py:73-93`) already-available
      `block_priority_gas_p90_gwei_<chain>` feature against its `spread_bps` profitability gate (currently used only
      for inclusion-bid sizing, never subtracted from the gated spread). Repo: strategy-service. Done when:
      `spread_bps < min_spread_bps` (or equivalent) accounts for the priority-gas cost, with a regression test.
- [ ] [STRATEGY] P3. Confirm whether execution-service's `ExecutionCostEstimator`
      (`execution-service/.../services/execution_cost_estimator.py:170-190`) is genuinely unused by strategy-service
      (0 import/call sites confirmed this session) — if so, either wire it in as originally intended (module
      docstring says "for strategy-service signal filtering") or mark it dead code / retarget its purpose. Repo:
      strategy-service, execution-service. Done when: either a real call site exists, or the docstring/lifecycle
      marker is corrected to reflect it is unused.

## Progress Log

- **2026-08-17 (slot-7, data_engineering, via defi_satellite_ao_dispatch_batch16_2026_08_17.md)**: filed after a
  grep-then-read verification pass (Explore sub-agent, 29 tool calls) found the wiring genuinely mixed — see §2/§3
  for the full per-engine breakdown. Not fixed inline: implementing 4 separate strategy-engine changes + a new
  features-service calculator is quant_dev/features craft scope, not data_engineering, and is bigger than this
  todo's 1-hour estimate. Cited back into the source todo's checkbox in
  `defi_satellite_ao_dispatch_batch16_2026_08_17.md` rather than left as an unresolved verification.
- **2026-08-17 (slot-17)**: closed the `[STRATEGY] P1` `CARRY_STAKED_BASIS` `fees_apy_bps` todo — scope decision: a
  **gas-only sub-term** (the todo's own offered alternative to a full funding+swap+gas composite), computed inside
  `CarryStakedBasisEngine._preflight`/`_estimate_gas_fees_apy_bps` rather than as a new features-service producer, so
  the fix stayed strategy-service-only (no features-service touch needed). Real inputs, never fabricated: on-chain
  swap-gas units come from UAC's already-cited `unified_api_contracts.internal.architecture_v2.FEES_REGISTRY` (the
  same execution-service-sourced numbers other DeFi cost models reuse — no new number invented); gas price + native
  price are real per-tick values (`features["gas_price_gwei"]` now sourced in `paper_run_handler.py` from MTDS's
  captured `gas_fees` corpus via the SAME real reader `pnl_input_builder._load_gas_fee_data` already uses for
  post-trade gas accounting; native price reuses the tick's real `mid_price`). The one-time round-trip gas cost is
  annualised via a new tunable `fee_amortization_days` engine param (default 30) to make it comparable to
  `staking_apy_bps`/`funding_rate_apy_bps`. `fees_apy_bps` stays an OPTIONAL feature override — the gas estimate only
  fires when the key is absent, so every existing test that explicitly passes `fees_apy_bps` (including F-10's own
  suite) is unaffected. Both `paper_run_handler.py:342,1196` hardcodes (`"fees_apy_bps": 0.0`) removed. 10 new
  regression tests added (`TestFeesApyBpsGasFallback` + `TestEstimateGasFeesApyBpsUnit`) covering: absent-both
  matches pre-change behaviour, a real gas price computes a nonzero fee that can suppress entry (mirrors F-10), a CEX
  `spot_venue` correctly stays 0.0 (no on-chain gas leg — honest, not a gap), and the exact annualisation arithmetic.
  Shipped strategy-service@f09969fe94 (Pass-1 QG green, sentinel-verified). Remaining sibling todos in this doc
  (FEATURES P1 `LIQUIDATION_CAPTURE`, STRATEGY P2 `JIT_LIQUIDITY`, STRATEGY P3 `BACKRUN` + `ExecutionCostEstimator`)
  are untouched — separate scope, not part of this task.
- **2026-08-17 (slot-7, data_engineering)**: closed the `[FEATURES] P1` `gas_cost_usd` calculator todo. Added
  `GasCostUsdCalculator` (`features-service/features_service/onchain/app/calculators/gas_cost_usd_calculator.py`,
  registered via `FeatureCalculatorRegistry` + wired into `app/calculators/__init__.py` and
  `schemas/feature_builder_registry.py`'s `_metadata`, so it is a genuine, discoverable pipeline calculator, not an
  orphaned file). Reads the SAME real MTDS `gas_fees` canonical shards
  `block_priority_gas_distribution_calculator.py` already reads; groups per real `(chain, block_number)` and takes
  the per-block median gas price; emits `gas_cost_usd_<action>` for every calibrated `GAS_UNITS` action (duplicated
  from execution-service's `gas_cost_model.py` — T4 forbids the cross-service import) plus a
  `LIQUIDATION_BUNDLE`-action `gas_cost_usd` (mirroring strategy-service's own `liquidation_bundle.py`'s
  `_LIQUIDATION_BUNDLE_GAS_UNITS = 750_000` calibration, the closest existing match to `LIQUIDATION_CAPTURE`'s 5-leg
  flash-loan bundle) — the bare key `LiquidationCaptureEngine` reads. Native-token USD price: no live per-chain
  native-price feed exists anywhere in features-service/onchain today (grepped the whole tree — zero hits); the
  calculator reads an optional `native_token_usd` column when an upstream caller has already joined a real price in,
  else falls back to a documented per-chain constant mirroring `liquidation_bundle.py`'s own established $3000
  ETH-equivalent fallback convention — a real gas price times a conservative constant, never a fabricated zero.
  **Scope note on the "paper run" done-when bar**: confirmed via grep of `paper_universe.py`'s full
  `StrategyArchetype.*` coverage that `LIQUIDATION_CAPTURE` is NOT currently in the paper-run drivable archetype set
  at all (no `ARBITRAGE_STRUCTURAL`/`LIQUIDATION_CAPTURE` entry) — driving it through a real end-to-end paper-run CLI
  invocation is a separate, larger strategy-service wiring task (registering a new drivable archetype in
  `paper_universe.py`/`paper_run_handler.py`), out of this todo's 1-hour FEATURES-craft scope and out of
  data_engineering craft (strategy math). Filed as a new todo below rather than silently absorbed or left unstated.
  Satisfied "confirmed non-zero ... with a regression test" via two regression suites instead: (1)
  `features-service/tests/onchain/unit/test_gas_cost_usd_calculator.py` — proves the calculator's real-block,
  real-formula, non-zero output (11 tests: pure-formula parity with gas_cost_model.py's math, L1 overhead on L2s,
  real per-block grouping, live-native-price override, per-chain fallback, empty/missing-column honest-empty paths);
  (2) `strategy-service/tests/unit/engine/strategies/v2/test_arbitrage_structural_liquidation_capture.py` — feeds
  `LiquidationCaptureEngine.on_tick()` the exact `gas_cost_usd` value the new calculator produces for a real
  Ethereum block (20 gwei, $3000 ETH -> 45.0 USD) and proves it is correctly subtracted from gross profit (not
  defaulted to zero), including a case where a realistic gas cost flips a marginal opportunity from profitable to
  gated. Both repos' `quality-gates.sh` green (sentinel-verified pre-quickmerge); features-service's own
  `test_golden_fixture_phase0_resolve_build_order.py` updated for the new calculator group (expected drift, not a
  regression). Shipped features-service@20d71ed0fb, strategy-service@0088d62fe8.
- **2026-08-18 (slot-16, ui_developer craft, adopted STRATEGY per craft-adoption rule)**: closed the `[STRATEGY] P2`
  `JIT_LIQUIDITY` todo — implemented, not docstring-only. Gate: captured swap fee (`pending_size *
  dex_swap_fee_bps_<pool> / 10000` — real per-pool fee tier feature from
  `features-service/.../dex_pool_swap_flow_calculator.py`, falling back to UAC `FEES_REGISTRY`'s cited Uniswap V3
  30bps default only when that feature is absent/0.0) must exceed the mint+burn gas cost (2x `FEES_REGISTRY`'s cited
  Uniswap V3 gas-unit estimate x the real `gas_price_gwei_<chain>` feature, at the same $3000 ETH-equivalent fallback
  already established twice — `mev/liquidation_bundle.py`'s `_bundle_gas_cost_usd` + features-onchain's
  `GasCostUsdCalculator`) plus, only when a new `flash_loan_source` param is set, a real
  `flash_loan_fee_bps_<flash_loan_source>` fee on the deployed capital — by `min_profit_usd` (new param, default
  $10). Mirrors the sibling `mev/liquidation_bundle.py` engine's exact feature-key + registry-fallback conventions
  (closest same-package precedent, not staked_basis's) rather than inventing a new pattern.
  **Scope decision on the IL term**: NOT netted into the gate — grepped the whole codebase for a live pre-trade
  price-impact producer and found none; the only price-impact computation anywhere (`mev/sandwich_theoretical.py`)
  is an explicitly POST-hoc tracer over CONFIRMED pre/post-swap prices, structurally unusable before an
  as-yet-unconfirmed pending swap lands. Docstring corrected to state this explicitly with the cited reasoning
  (module-level, not a passing comment) rather than silently omitting the term or leaving the stale claim in place —
  this satisfies the todo's own "implement, or correct the docstring... state which, with reasoning" alternative for
  the one term that has no real data to net. 4 new regression tests added
  (`test_jit_nets_captured_fee_against_gas_and_reports_attestations`,
  `test_jit_skips_when_gas_cost_exceeds_captured_fee`, `test_jit_nets_flash_loan_fee_when_flash_loan_source_set`, plus
  the 2 pre-existing entry-trigger tests re-verified unaffected) covering: real-feature profitable case, an
  extreme-gas unprofitable case, and the conditional flash-loan-fee path. `quality-gates.sh` full run green (6119
  passed, sentinel-verified at HEAD before quickmerge — not a sentinel-hit skip). Shipped strategy-service@fbf78dfe20.
  Remaining sibling todos in this doc (STRATEGY P3 `BACKRUN`, STRATEGY P3 `ExecutionCostEstimator`, STRATEGY P2
  `LIQUIDATION_CAPTURE` paper-universe registration below) are untouched — separate scope, not part of this task.
- [ ] [STRATEGY] P2. BLOCKED-ON:liquidation_capture_paper_drivability_design — Register `LIQUIDATION_CAPTURE` as a drivable archetype in `paper_universe.py`/
      `paper_run_handler.py` (mirroring how `ARBITRAGE_PRICE_DISPERSION`/DEX-pool archetypes are wired) so it can
      actually run end-to-end in a real paper run — currently NOT in `paper_universe.py`'s drivable
      `StrategyArchetype.*` set at all (confirmed via grep, 2026-08-17). Repo: strategy-service. Done when: a real
      paper run emits at least one `LIQUIDATION_CAPTURE` tick/instruction over real captured on-chain lending data.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries) — corrected the .tabs/7 absolute prefixes to workspace-root-relative; added the features-service gas_cost_usd_calculator producer

### 6. Required prerequisite design — candidate snapshot and paper injection

The existing `DEFI_LENDING_LIQUIDATIONS` / `liquidation_events` data is a record of positions that were already
liquidated. It cannot be replayed as a pre-trade candidate feed: it has no current health factor, remaining debt and
collateral balances, or as-of prices for deciding whether a new liquidation is executable. The features-service
`health_factor` path is protocol-level aggregate data, not an arbitrary-wallet read, and strategy-service's
`margin_health_cache` is fail-closed and is populated by the own-position risk path; no current writer scans third-party
borrowers. Therefore static catalog values, the existing `position_data`, or the post-event liquidation rows must not be
repurposed to fill the engine's `debt_asset`, `collateral_asset`, `underwater_address`, amounts, prices, bonus, or
health-cache inputs.

The follow-up design must resolve these boundaries before any paper-universe registration:

1. **Raw producer ownership and honest source gate.** MTDS remains the owner of raw on-chain lending observations and
canonical event/data-type persistence. The design must first prove, for one supported protocol/chain (recommended
first slice: Aave V3 Ethereum, where the existing `liquidation_events` handler and live `LiquidationCall` connector
provide source precedents), that a historical/live source can discover *candidate borrowers before liquidation* and
provide an as-of block/timestamp. A post-event liquidation feed alone fails this gate. Compound, Morpho, Kamino, and
the other catalog rows remain honest skips until each has the same source proof; no cross-protocol fallback is allowed.

2. **Canonical candidate snapshot contract.** UAC must own a typed, versioned candidate record (rather than a
strategy-local dict) containing at minimum: `candidate_id`/underwater account address, protocol, chain, observation
block and UTC timestamp, debt asset + exact debt amount, collateral asset + exact seizable amount, collateral and debt
USD prices with their source/as-of metadata, liquidation bonus/penalty, and a validity/staleness bound. It must also
carry the source event/block identifiers needed for audit and deterministic paper↔batch replay. Missing or stale
fields are an explicit unavailable status, never zero/default values. The contract must define whether the snapshot is
keyed by candidate address, position, or liquidation opportunity when one wallet has multiple markets.

3. **Feature enrichment and health-cache population.** Features-service should consume the canonical candidate snapshot,
join only real oracle prices, protocol liquidation parameters, DEX slippage/liquidity, and the existing gas-cost
calculator, then emit a deterministic candidate feature row for the paper tick. A separate, typed writer must update
strategy-service's `margin_health_cache` for the same (`underwater_address`, `protocol`) subject and observation time,
or the strategy contract must carry an equivalent signed/as-of health reading; the design must not bypass the cache's
fail-closed semantics. The enrichment must expose provenance and validity so the engine can reject stale candidates.

4. **Runtime and replay injection.** Strategy-service must add an explicit candidate-context injection seam between
`paper_universe.py`/`paper_run_handler.py` and `LiquidationCaptureEngine.on_tick()`. It must bind the candidate's
address and debt asset/amount to the generated atomic instruction without encoding an address as a float or mutating
static catalog rows. The same immutable candidate snapshot and ordering must be recorded in the run manifest and used
by batch rerun, preserving paper↔batch determinism. Only after this seam and a real source-backed fixture exist may
`LIQUIDATION_CAPTURE` enter `_ENGINE_DRIVABLE_ARCHETYPES` and the catalog's static rows be mapped to discovered
candidates.

- [ ] [STRATEGY] P1. Design and approve the cross-repo `LIQUIDATION_CAPTURE` candidate-snapshot contract and producer ownership before registering the archetype: validate a real pre-liquidation source for one protocol/chain, specify the UAC record plus provenance/staleness fields, define features-service enrichment and strategy-service margin-health/runtime injection, and define paper↔batch manifest replay; done when the design names the owning modules, rejects post-event/static fabrication, and provides an implementation-ready follow-up with an evidence-backed source gate.

- **2026-08-20 (slot-7, resumed worker)**: operator answered the blocked-question chain with direction A — build the real cross-repo candidate-snapshot producer/contract, reject deriving fields from `position_data` or static catalog values. Per AO eligibility, this is an open-ended architecture decision, so this session records the design boundary and leaves implementation to a follow-up after approval. Existing `LIQUIDATION_CAPTURE` registration remains `BLOCKED-ON:liquidation_capture_paper_drivability_design`; no code or static registration was changed.
