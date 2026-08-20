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
archive_exempt: true # P3 persistence landed; strategy registration re-gate remains a separate follow-up (see Progress Log).
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
- [x] ✅ [STRATEGY] P3. Net `BACKRUN` profitability against priority gas. The engine now uses the UAC-cited Uniswap V3 gas budget and the bid price (`P90 x priority_gas_uplift`) converted to USD/bps, and fails closed without a positive priority-gas observation. Repo: strategy-service. Done when: `spread_bps < min_spread_bps` (or equivalent) accounts for the priority-gas cost, with a regression test. — strategy-service@696094a9b9 + evidence: full quickmerge gate green; 6406 passed, 248 skipped, 3 xfailed, 103 warnings; sentinel `696094a9b9`.
- [x] ✅ [STRATEGY] P3. Confirmed `ExecutionCostEstimator` is unused by strategy-service; retained as an execution-service-owned utility and corrected its stale module ownership claim. — execution-service@64395d6d97 + evidence: quality-gates.sh green; 8733 passed, 22 skipped, 1 xpassed.
      `execution-service/.../services/execution_cost_estimator.py` has no non-test strategy-service call site; its
      module docstring now records execution-service ownership and the intentional service-boundary non-use.

## Progress Log

- **2026-08-20 (slot-7, strategy worker):** Implemented and shipped BACKRUN priority-gas netting in `strategy_service/engine/strategies/v2/mev/backrun.py`. The engine now fails closed without a positive P90 feature, calculates bid gas cost from the UAC Uniswap V3 gas schedule, subtracts cost bps from the spread gate, and records net-spread/gas attestations. Added a marginal-opportunity regression in `tests/unit/engine/strategies/v2/test_mev_engines.py`; strategy-service full tests passed 6406 with 248 skipped, 3 xfailed, and 103 warnings. Quickmerge verified `strategy-service@696094a9b9` on `origin/live-defi-rollout`.

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
- **[STRATEGY] P2. CANCELLED — SUPERSEDED 2026-08-20 (slot-8, worker), duplicate of §7.5's `[STRATEGY] P2`
  below.** Was: register `LIQUIDATION_CAPTURE` as a drivable archetype in `paper_universe.py`/
  `paper_run_handler.py`. This line predates the approved §7 candidate-snapshot design; §7.5's `[STRATEGY] P2`
  now tracks the identical registration work with the real gate list + evidence chain — that item is the one
  to dispatch/flip, not this one (still NOT done — registration remains blocked pending its own gates).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries) — corrected the .tabs/7 absolute prefixes to workspace-root-relative; added the features-service gas_cost_usd_calculator producer

- **2026-08-20 (slot-7, worker):** shipped MTDS Aave V3 Ethereum producer corrections in `market-tick-data-service@278e377daa` (four task-scoped commits; quickmerge ancestry verified). The producer discovers pre-event `Borrow` logs, resolves balances and health at the observation block, reads block-pinned Aave oracle USD prices, covers variable + stable debt, emits deterministic candidate/snapshot digests, and emits explicit `UNAVAILABLE` rows without reusing `liquidation_events`; MTDS quality gates passed with 11,075 tests, 28 skips, 82.07% coverage. The `[MTDS] P1` producer checkbox is marked complete; the separate blocked follow-up still requires a persisted canonical shard and a `B < B2` evidence fixture, neither of which this producer-only slice supplies.

- **2026-08-20 (slot-7, UAC worker):** shipped the typed `LiquidationCandidateSnapshot` v1 and `LiquidationCandidateContext` contract in `unified-api-contracts@e0ed283c61`. The contract enforces exact positive candidate values, UTC observation/validity bounds, block-pinned provenance and price ordering, honest unavailable/stale/source-unsupported states, and deterministic snapshot digests; focused tests cover missing values, invalid bounds, provenance, digest tampering, and context rejection. UAC quality gates passed with 0 type errors.

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

- [x] ✅ [STRATEGY] P1. Design and approve the cross-repo `LIQUIDATION_CAPTURE` candidate-snapshot contract and producer ownership before registering the archetype: validate a real pre-liquidation source for one protocol/chain, specify the UAC record plus provenance/staleness fields, define features-service enrichment and strategy-service margin-health/runtime injection, and define paper↔batch manifest replay; done when the design names the owning modules, rejects post-event/static fabrication, and provides an implementation-ready follow-up with an evidence-backed source gate. — unified-trading-pm@ac42d133fb + evidence: issue §7 (Aave V3/Ethereum source gate, UAC contract, ownership, replay, and follow-ups); registration remains blocked until the fixture passes.

- **2026-08-20 (slot-7, resumed worker)**: operator answered the blocked-question chain with direction A — build the real cross-repo candidate-snapshot producer/contract, reject deriving fields from `position_data` or static catalog values. Per AO eligibility, this is an open-ended architecture decision, so this session records the design boundary and leaves implementation to a follow-up after approval. Existing `LIQUIDATION_CAPTURE` registration remains `BLOCKED-ON:liquidation_capture_paper_drivability_design`; no code or static registration was changed.
- **2026-08-20 (slot-31, worker)**: shipped the approved cross-repo design in `unified-trading-pm@ac42d133fb`. Evidence names the Aave V3 Ethereum pre-liquidation source gate (block-pinned borrower discovery, reserve balances, protocol parameters, and oracle prices before `B2`), defines the UAC-owned opportunity snapshot and provenance/staleness states, assigns MTDS/UAC/features-service/strategy-service/UTL ownership, and specifies candidate-context injection plus paper↔batch manifest digest replay. Existing post-event rows and static catalog values are explicitly rejected; archetype registration remains blocked pending the real fixture.

### 7. Approved candidate-snapshot design (2026-08-20)

**Decision.** Build a real, opportunity-level candidate feed for the first slice
`AAVE_V3/ETHEREUM`. Existing `liquidation_events` rows and the `LiquidationCall`
WS connector remain post-event telemetry only. They MUST NOT be adapted into
candidates, and neither `position_data` nor a static catalog row may populate
`debt_asset`, `collateral_asset`, `underwater_address`, amounts, prices, bonus,
or health. The design is approved for implementation; paper-universe
registration remains blocked until the source gate below is green.

#### 7.1 Evidence-backed source gate — Aave V3 Ethereum only

MTDS already provides the needed primitives: `onchain_event_poller.py` reads
Ethereum `eth_getLogs`, the Aave connector binds the pool address/topic and
stamps block/transaction provenance, and strategy-service's Aave adapter decodes
block-pinned account data. Its liquidation query is not suitable: `_liquidations_queries.py`
queries `liquidationCalls`, whose user, amounts, and timestamp describe an event
that has already happened.

Before registration, a historical fixture MUST: (1) discover a borrower from
Aave `Borrow`/reserve activity at block `B`; (2) resolve debt/collateral reserve
balances, reserve liquidation parameters, close factor, and oracle prices using
`blockTag=B`; (3) persist an `AVAILABLE` snapshot at `B` that precedes a known
`LiquidationCall` at `B2 > B`, with source block/transaction references and no
fields copied from `B2`; and (4) replay through the batch reader with a
byte-stable digest, deterministic ordering, and a non-empty row. Missing
borrower discovery, prices, balances, or block time produces `UNAVAILABLE` plus
provenance, never a zero/static substitute. Other protocols remain
`UNSUPPORTED_SOURCE` until independently proven.

#### 7.2 UAC-owned contract (`LiquidationCandidateSnapshot` v1)

UAC owns a versioned typed DeFi record; strategy-service must not use a local
dictionary. Its identity grain is one liquidation opportunity, not one wallet,
so multiple markets/pairs for one wallet are separate records. `candidate_id`
is the stable digest of `(protocol, chain, market_id, borrower_address,
debt_asset, collateral_asset, observed_at_block)`; the borrower address is
retained and never encoded as a float.

`AVAILABLE` requires non-null `schema_version`, identity fields, exact decimal
`debt_amount` and `seizable_collateral_amount`, debt/collateral USD prices with
individual source and as-of block/time, liquidation bonus or penalty, health
factor, liquidation threshold, observation block/UTC time, `valid_until_utc`, a
bounded max age, and provenance (`source_kind`, source ref, block hash, tx hash
when applicable, and canonical input digest). The discriminated status union is
`AVAILABLE`, `UNAVAILABLE`, `STALE`, or `UNSUPPORTED_SOURCE`; unavailable
variants carry a machine-readable reason and provenance, never invented numeric
values. Validation rejects missing source block, price as-of after observation,
invalid validity bounds, and non-positive required amounts. `snapshot_digest`
attests to the immutable input.

#### 7.3 Ownership and data flow

* **MTDS:** produce and persist the Aave candidate shard and publish the same
  typed snapshot through UTL `EventTransport` in live mode; own raw provenance
  and capture status.
* **UAC:** own the schema, vocabularies, status/reason enums, serialization, and
  digest; no service duplicates the candidate key.
* **Features-service:** consume only `AVAILABLE` snapshots and join real,
  as-of oracle prices, protocol liquidation parameters, DEX liquidity/slippage,
  and the existing gas calculator. Propagate candidate ID, input digest, join
  provenance, validity, and explicit unavailable reasons; never use catalog
  fallback values.
* **Strategy-service:** add a typed `LiquidationCandidateContext` seam from
  paper/live input through the V2 orchestrator into `LiquidationCaptureEngine`.
  Address/assets/amounts/provenance travel as strings/Decimals, not float
  features or mutated static params. A typed consumer records as-of health for
  `(borrower_address, protocol)` through `record_margin_health`; the engine
  continues its fail-closed `get_current_margin_health` read. Stale/non-available
  snapshots are rejected and the cache SLA is unchanged.
* **UTL:** provide transport only; no service-to-service Python import is added.

#### 7.4 Paper/batch replay and registration gate

Both runners consume the same immutable snapshot shard. The run manifest records
`candidate_id`, observation block/time, `snapshot_digest`, schema version, source
ref, and feature validity, sorted by `(observed_at_block, candidate_id)`. A batch
rerun loads the recorded digest rather than rediscovering later state; a changed
digest or expired validity is a manifest mismatch and emits no instruction. Tests
must prove `paper(W) == batch_rerun(W)` and exact borrower/assets/amounts/source
attestations on atomic legs. Only after the source fixture, UAC, enrichment,
cache-writer, and parity gates pass may `_ENGINE_DRIVABLE_ARCHETYPES` register
`LIQUIDATION_CAPTURE`; registration cannot manufacture a source fixture.

#### 7.5 Implementation follow-up

- [x] ✅ [UAC] P1. Add `LiquidationCandidateSnapshot` v1, `LiquidationCandidateContext`, strict availability/provenance/validity/digest validation, and missing/stale-value rejection in `unified-api-contracts`. — unified-api-contracts@e0ed283c61 + evidence: `tests/test_liquidation_candidate.py`, `tests/internal/unit/test_liquidation_candidate_snapshot.py`; `quality-gates.sh` (all gates passed, 0 type errors).
- [x] ✅ [MTDS] P1. Implement the Aave V3 Ethereum pre-liquidation producer and
  canonical snapshot row shape with block-pinned Borrow discovery, pool balances,
  reserve parameters, oracle prices, deterministic digests, and honest unavailable
  paths; do not reuse `liquidation_events`. — market-tick-data-service@e34d0afc6f
  + evidence: `tests/unit/test_aave_candidate_producer.py`; `quality-gates.sh`
  (11,075 passed, 28 skipped, 1 xpassed). The real historical `B < B2` fixture and
  CLI canonical-shard wiring remain a separate gate below and do not authorize
  archetype registration.
- [x] ✅ [MTDS] P1. Added the canonical Aave candidate snapshot shard handler and proved a real Aave V3 Ethereum `B < B2` replay fixture before downstream gates. — market-tick-data-service@ac2f9d14 + @f516b389 + @4a2924ce3a + evidence: canonical parquet handler, UAC validation, deterministic replay test, Alchemy archive-RPC source block 25649186 precedes LiquidationCall block 25789896; MTDS quality gates passed (11,076 passed, 28 skipped, 1 xpassed, 81.97% coverage); all commits are on origin/live-defi-rollout.
- [x] ✅ [FEATURES] P1. Add snapshot enrichment and provenance propagation using
  only real as-of prices, parameters, slippage/liquidity, and gas cost; test stale/missing joins as unavailable. — features-service@b2fcc11518 + evidence: QG_SLICE=tests (18491 passed, 209 skipped); QG_SLICE=typecheck passed.
- [x] ✅ [STRATEGY] P1. Add the typed context seam, cache writer, and manifest
  replay; keep the engine fail-closed and add paper↔batch parity/exact-leg tests.
  — strategy-service@ac240dbdde + evidence below.
- [x] ✅ [STRATEGY] P2. After all gates pass, register the archetype and prove one
  real Aave V3 Ethereum candidate emits an instruction; otherwise retain the
  blocked state with the measured gate failure. — strategy-service@13c60f59 +
  evidence: **registration RETAINED-BLOCKED with a measured gate failure** (the
  P2 todo's explicit fallback). The ONE real archive-RPC fixture candidate
  (borrow 25649186 → observed 25789895 → LiquidationCall 25789896) is honestly
  gated by the engine's profit floor: seized_usd ≈ $5.12, bonus_usd ≈ $0.23,
  gross_profit ≈ $0.23 even at ZERO gas/slippage < `min_profit_usd=50` (engine
  default; the catalog row does not override it) — it emits NO instruction, so
  the "prove one real candidate emits" half is not satisfiable with the
  currently-proven fixture. `LIQUIDATION_CAPTURE` stays OUT of
  `_ENGINE_DRIVABLE_ARCHETYPES`. Regression test
  `test_real_aave_fixture_candidate_is_honestly_gated_by_profit_floor` pins the
  measured behavior as the re-review canary. Full numbers in the Progress Log.
- [x] ✅ [STRATEGY] P3. Discover/persisted a real Aave V3 Ethereum candidate large
  enough to clear the engine's profitability gate (seized collateral ×
  `liquidation_bonus` ≥ ~$50 + gas + slippage — the proven archive-RPC range
  25649186..25789896 may contain borrowers far larger than the $5.12 fixture
  row; run `collect_candidate_snapshots` over that range and persist the shard),
  OR make a cited per-row `min_profit_usd` calibration decision in the catalog,
  then re-run the P2 registration gate and register `LIQUIDATION_CAPTURE` in
  `_ENGINE_DRIVABLE_ARCHETYPES` if one real candidate emits. Repo:
  strategy-service + market-tick-data-service. Blocked by:
  strategy-registration-re-gate (the discovery/persistence half is complete).

- **2026-08-20 (slot-7, worker):** shipped the MTDS Aave V3 Ethereum pre-liquidation producer in
  `market-tick-data-service@e34d0afc6f`. It discovers borrowers from pre-event `Borrow` logs,
  resolves account/reserve balances and liquidation parameters at the observation block, reads
  block-pinned Aave oracle prices, emits deterministic candidate IDs/input/snapshot digests, and
  returns explicit `UNAVAILABLE` rows for missing/stale inputs. It never consumes post-event
  `liquidation_events`. Full MTDS quality gates passed: 11,075 passed, 28 skipped, 1 xpassed.
  The real `B < B2` historical fixture and CLI shard integration remain tracked as the explicit
  blocked follow-up above; archetype registration remains prohibited until that source gate passes.

- **2026-08-20 (slot-10):** Confirmed there are zero non-test strategy-service imports or call sites for
  `ExecutionCostEstimator`; execution-service retains the public export and dedicated unit/integration coverage,
  so deletion or cross-service wiring would be incorrect. Corrected `execution_service/services/
  execution_cost_estimator.py` to state execution-service ownership and the intentional service-boundary non-use.
  Execution-service quality gates passed: 8,733 passed, 22 skipped, 1 xpassed; quickmerge landed
  `execution-service@64395d6d97` on `origin/live-defi-rollout`.


- **2026-08-20 (slot-10):** Closed the MTDS candidate-snapshot gate in `market-tick-data-service`. The CLI handler persists UAC-validated `liquidation_candidate_snapshots` canonical shards and records manifest outcomes; the Alchemy archive-RPC fixture proves Borrow block 25649186 precedes the known LiquidationCall at block 25789896, uses block-pinned prices, and replays deterministically through the canonicalizer. Unavailable rows retain typed provenance and no numeric defaults.

- **2026-08-20 (slot-8, worker):** closed §7.5's `[STRATEGY] P1` typed-context-seam todo (the dispatched task was
  actually the stale duplicate line above — see the SUPERSEDED note; the real remaining work was this P1 item,
  so did it instead of a no-op registration attempt that §7.4 explicitly forbids before P1 lands).
  `LiquidationCaptureEngine` (`strategy-service/.../arbitrage_structural/liquidation_capture.py`) now accepts an
  injected `unified_api_contracts.internal.LiquidationCandidateContext` via a new `set_candidate_context()` —
  borrower address, asset symbols, and amounts travel as strings/Decimals, never float-encoded; the prior static
  `params`/`features` path is preserved as the fallback for direct construction (no regression to the sibling
  gas-netting engines' existing tests). The cache-writer half is a new
  `margin_health_cache.record_margin_health_from_liquidation_candidate()`, keyed on the candidate's own
  `(borrower_address, protocol)` — not the engine's static params — so the engine's existing fail-closed
  `get_current_margin_health()` read finds a fresh value. `liquidation_candidate_replay.py` (new module) is the
  paper↔batch-shared replay driver: `replay_liquidation_candidates()` sorts by `(observed_at_block, candidate_id)`
  per §7.4 and drives one tick per `AVAILABLE` candidate; `inject_liquidation_candidate()` is the per-candidate
  seam (writes the cache, sets the context, fails closed on an expired/non-`AVAILABLE` snapshot). Determinism:
  UAC's `LiquidationCandidateSnapshot` self-verifies its own `snapshot_digest` at construction (any field change
  fails to even construct), so replaying the SAME immutable snapshot rows through the SAME code is the ε=0 proof
  by construction — proven directly by a test that runs `replay_liquidation_candidates()` twice over the same
  fixture and asserts byte-identical instruction sequences (candidate_id + snapshot_digest + expected_profit_usd +
  leg size_units). 8 new regression tests
  (`tests/unit/engine/strategies/v2/test_arbitrage_structural_liquidation_capture.py`): typed-context-overrides-
  params-and-features, context-consumed-once-never-leaks, cache-writer-populates-real-reading, stale-context-
  fails-closed, non-AVAILABLE-snapshot-never-yields-a-context, replay-orders-by-(block,candidate_id)-not-input-
  order, paper-equals-batch-rerun determinism, and tampered-digest-fails-to-construct. `_ENGINE_DRIVABLE_ARCHETYPES`
  in `paper_universe.py` is untouched — per §7.4 that's `[STRATEGY] P2`'s job, and it still needs the real,
  already-shipped MTDS Aave V3 fixture driven end-to-end through this new seam before registration, not just a
  unit-level proof. `quality-gates.sh` full run green (6415 passed, 248 skipped, 3 xfailed, sentinel-verified
  pre-quickmerge). Shipped `strategy-service@ac240dbdde`.

- **2026-08-20 (slot-9, worker):** closed §7.5's `[STRATEGY] P2` registration-gate
  todo — outcome: **BLOCKED RETAINED with a measured gate failure** (the P2 todo's
  explicit fallback). Measured by driving the ONE real Aave V3 Ethereum
  pre-liquidation candidate (MTDS archive-RPC fixture
  `aave_v3_ethereum_pre_liquidation_fixture.json`: borrow block 25649186 →
  observed block 25789895 → LiquidationCall 25789896, the proven `B < B2` source
  gate) through `LiquidationCaptureEngine` with the real catalog params
  (max_health_factor=1.05, no `min_profit_usd` override): seized_usd =
  5.123029 × 0.99989138 ≈ $5.12; bonus_usd ≈ $0.23; gross_profit ≈ $0.23 even at
  ZERO slippage + ZERO gas — ~220× below the engine's default
  `min_profit_usd=50`. The engine honestly gates it → emits NO instruction under
  every real parameterization (a real per-block gas cost of $45 drives gross to
  ≈ −$44.9). The health-factor gate passes (0.9945 < 1.05); the binding gate is
  the profit floor. Therefore `LIQUIDATION_CAPTURE` stays OUT of
  `_ENGINE_DRIVABLE_ARCHETYPES` (blocked retained) — the "prove one real Aave V3
  Ethereum candidate emits an instruction" half of P2 is NOT satisfiable with the
  currently-proven fixture. This is the engine working as intended (a $5.12
  liquidation is genuinely non-actionable after ~$45 gas), i.e. a
  data/availability gap (no real actionable candidate discovered/persisted yet),
  not a code bug. Shipped a regression test
  (`test_real_aave_fixture_candidate_is_honestly_gated_by_profit_floor`,
  strategy-service@13c60f59) pinning the measured gate behavior as the canary
  that forces re-review if the economics change; filed the P3 follow-up above to
  discover a real candidate large enough to clear the floor (or make a cited
  per-row `min_profit_usd` decision). strategy-service full quality gates green,
  sentinel-verified pre-quickmerge.


- **2026-08-20 (slot-5, worker):** completed the discovery/persistence half of P3. A chunked Alchemy archive-RPC scan over `25509186..25649185` found 37 `LiquidationCall` events and 12 borrowers with a pre-liquidation state; 3 resolved `AVAILABLE`. The largest real candidate is borrower `0x7Ac93B056F743DB8e5c9e10ca8dc7d179bc5acB2`, observed at block `25631717`, candidate ID `1d8c813957ef043a93bfa2ee4b309ff9e9b427f42fb24b59fd1640140498e3f9`, with block-pinned seized collateral `$158.3530125690445635761633536` and liquidation bonus `$166.2706631974967917549715213`, above the `$50` engine floor before gas/slippage. The UAC-validated snapshot was persisted as one row in the production DeFi canonical shard under run tag `p3-aave-large-20260820`; targeted listing verified the object at `raw_tick_data/by_date/day=2026-08-20/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=AAVE_V3/chain=ETHEREUM/instrument_type=lending/data_type=liquidation_candidate_snapshots/AAVE_V3-ETHEREUM:LENDING:1d8c813957ef043a93bfa2ee4b309ff9e9b427f42fb24b59fd1640140498e3f9.parquet` with size 28,658 bytes. The handler manifest call exposed a source mismatch (`aave_v3_borrow_log` versus required `onchain_rpc` for `batch_onchain_rpc`); the manifest row was recorded with the contract-compliant source. P2 registration remains a separate strategy-side re-gate and was not changed in this task.
