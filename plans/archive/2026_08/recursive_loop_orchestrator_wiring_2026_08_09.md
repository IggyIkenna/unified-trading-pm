---
doc_type: plan
title: Wire RecursiveLoopOrchestrator — LTV/depth params + real translation layer for Family 1/2 carry archetypes
summary: >-
  CARRY_RECURSIVE_BORROW_LENDING_ONLY and CARRY_BASIS_PERP_INV are fully catalogued but permanently stubbed —
  CarryRecursiveStakedEngine.on_tick() returns [] whenever staking_yield_enabled=false, which both archetypes' catalog
  rows always set. RecursiveLoopOrchestrator (execution-service, 711 lines, unit-tested) and PerpHedgeSizer
  (execution-service) are both fully built but have ZERO production callers anywhere in the workspace — confirmed via
  exhaustive grep. Operator ruled 2026-08-09 on the 3 trading-parameter numbers this build needs (LTV-per-lending-mode,
  recursion-depth policy, perp-hedge rebalance formula) — see
  defi_catalog_engine_config_key_contract_drift_2026_07_23.md's RULED todo. This plan wires those numbers into the
  catalog builder and builds the real translation layer so both archetypes produce live AtomicInstruction output and
  RecursiveLoopOrchestrator gets its first real caller.
status: complete # archived 2026-08-09 — all 8 todos done, unlocked; 6-step ritual run
nature: process
asset_group: [defi]
stage: [strategy]
repos: [strategy-service, execution-service, unified-api-contracts]
scope: [engineer]
tags: [defi, carry, recursive-loop, perp-hedge, ltv, translation-layer, leveraged, money-path]
related:
  [
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by: recursive_loop_orchestrator_wiring_finalize_2026_08_09
resolved_by:
source: >-
  Operator ruling 2026-08-09 on defi_catalog_engine_config_key_contract_drift_2026_07_23.md's DRAFT PROPOSAL, followed
  by an exhaustive code-landscape research pass confirming exact file/function targets before this plan was authored —
  the operator explicitly asked for a tracked agent-orchestrator plan given the cross-repo, leveraged-money-path scope.
context_scope:
  [
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_carry.py,
    strategy-service/tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/recursive_loop_orchestrator.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_config.py,
    unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py,
    execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py,
    execution-service/execution_service/defi_execution/helpers/perp_hedge_sizer.py,
    execution-service/execution_service/algo_library/leveraged_leg_controller.py,
    unified-trading-library/unified_trading_library/risk/net_delta.py,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
  ]
---

# Wire RecursiveLoopOrchestrator — LTV/depth params + real translation layer

> **✅ ARCHIVED 2026-08-09 — COMPLETE.** All 8 todos shipped and independently re-verified (commits confirmed ancestors
> of `origin/live-defi-rollout`, full `quality-gates.sh` re-run green on all 3 touched repos): both Family 1/2
> archetypes now build real `AtomicInstruction` output via `CarryRecursiveStakedEngine.on_tick()`, and
> `RecursiveLoopOrchestrator` has its first production caller
> (`execution-service/algo_library/recursive_loop_runner.py`). Todo 6's evidence was reconciled into the source issue
> doc's `[DESIGN]` todo (`/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`, flipped
> `[x]`). Both codex archetype SSOTs
> (`/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md`,
> `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md`) updated `implementation_status: design` →
> `code-shipped` with the shipped-commit trail. Todo 7's audit found no suitable existing poller for
> `PerpHedgeSizer.compute_rebalance()`/`.compute_margin_topup()`; that open decision continues as its own `[DESIGN]`
> todo on the finalize companion (below), which stays `active` until it's resolved. Archived via the standard 6-step
> ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). Successor/companion:
> `/plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`.

## Background

`CARRY_RECURSIVE_BORROW_LENDING_ONLY` (Family 1) and `CARRY_BASIS_PERP_INV` (Family 2) are both fully catalogued
(`catalog_carry.py:621-719`) and route to `CarryRecursiveStakedEngine` (`factory.py:71-72`), but that engine's
`on_tick()` (`recursive_staked.py:194-200`) unconditionally returns `[]` whenever `staking_yield_enabled=false` — which
both archetypes' catalog rows set (`catalog_carry.py:654,708`). This is why the test suite carries both archetypes in
`_ALLOWED_EMPTY_ARCHETYPES` (`test_all_catalogued_archetypes_construct_and_fire.py:104-112`) as a documented, deliberate
exemption, not a bug.

A 2026-08-09 code-landscape research pass (cited in `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s
Progress Log) confirmed, with exact file:line citations:

- **`RecursiveLoopOrchestrator`**
  (`execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py`, 711 lines,
  `open()`/`unwind()`) and **`PerpHedgeSizer`**
  (`execution-service/execution_service/defi_execution/helpers/perp_hedge_sizer.py`) are both fully implemented and
  unit-tested but have **zero production callers anywhere in the workspace** (exhaustive grep, test files excluded).
- The **LTV-per-lending-mode table** the operator ruled on exists as real values in UAC
  (`unified_api_contracts/registry/defi_reserve_params.py` — Aave e-mode 0.93, Morpho `market_0945`=0.945,
  `market_086`=0.86, all matching the codex doc), but the catalog builder only ever writes an `ltv_mode` STRING param
  (`catalog_carry.py:653,707`) that **nothing reads back** — confirmed via grep, exactly 2 hits (the writes themselves).
- **`recursion_depth_max=5`** is correctly set for both archetypes (`archetype_config.py:271,299`) but has **zero
  production readers** — only schema/validation unit tests reference it.
- A **working example already exists in the same engine file** for the currently-live `CARRY_RECURSIVE_STAKED`
  archetype: `_build_loop_legs()` (`recursive_staked.py:382-447`) and `_build_instruction()` (`:350-380`) build a real
  `list[AtomicLeg]` → `AtomicInstruction` per loop iteration. This is the target shape Family 1/2's real `on_tick()`
  implementation needs to reproduce.

## Codex SSOTs

- `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md` — Family 1 spec: LTV table,
  per-chain recursion-depth figures (operator ruled: NOT adopted, keep shipped 5), execution semantics (STAKE → TRANSFER
  → LEND → BORROW per-loop bundle), LegController integration notes.
- `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md` — Family 2 spec: perp-hedge rebalance formula
  (`perp_short_size = max(0, E_actual - target_net_delta)`, 5%-of-`E_actual` rebalance trigger), `PerpHedgeSizer`
  docstring's "designed for 5-min poll cycle" framing.

## Todos

- [x] ✅ [BACKEND] P1. Add an `ltv_mode`-string → `(max_ltv, liquidation_threshold)` resolver in —
      unified-api-contracts@547b1d1b `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py` (or a
      new sibling helper in the same module) that maps the exact tokens `catalog_carry.py` already writes
      (`"emode_eth"`, `"market_0945"`, `"market_086"`) to real values via the existing
      `get_emode_params()`/`get_morpho_market_lltv()` functions — do not re-derive the numbers, only add the
      string-to-lookup indirection. Repo: unified-api-contracts. Done-when: a new unit test resolves all 3 tokens to the
      operator-ruled values (0.93/0.945/0.86) and `quality-gates.sh` is green.
- [x] ✅ [BACKEND] P1. Wire the resolver from the prior todo into — strategy-service@b98f74fb
      `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_carry.py`'s
      `build_carry_recursive_borrow_lending_only()` (`:621-662`) and `build_carry_basis_perp_inv()` (`:670-719`):
      replace the currently-unread `"ltv_mode": mode` catalog param with a real resolved
      `"ltv_per_loop": liquidation_threshold - config.safety_buffer_ltv` value (read `safety_buffer_ltv` from
      `get_archetype_config(archetype)` in `unified_api_contracts.internal.architecture_v2.archetype_config` — already
      `0.05` for both archetypes, do not hardcode). Repo: strategy-service. Done-when: a new/updated catalog-builder
      unit test asserts each of the 7 cataloged cells carries the correct numeric `ltv_per_loop` (0.93-0.05=0.88 for the
      Aave e-mode cell, etc.), and `quality-gates.sh` is green.
- [x] ✅ [BACKEND] P1. Wire `ArchetypeConfig.recursion_depth_max` (already `5` for both archetypes,
      `archetype_config.py:271,299`) into the same two catalog builders as an `"n_loops"` param, read via
      `get_archetype_config(archetype).recursion_depth_max` — do not hardcode `5` in the catalog file. Repo:
      strategy-service. Done-when: a catalog-builder unit test asserts `n_loops=5` on every cataloged cell for both
      archetypes, and `quality-gates.sh` is green. **Already shipped alongside todo 2** — strategy-service@b98f74fb3
      added `"n_loops": str(config.recursion_depth_max)` to both `build_carry_recursive_borrow_lending_only()` (`:662`)
      and `build_carry_basis_perp_inv()` (`:721`) in the same commit, plus
      `test_family1_recursion_borrow_lending_only_ltv_per_loop_and_n_loops`/
      `test_family2_basis_perp_inv_ltv_per_loop_and_n_loops` (`test_catalog_carry_recursive_ltv_wiring.py`) already
      assert `n_loops == "5"`. Re-verified live (slot 18, 2026-08-09): full `quality-gates.sh` on strategy-service green
      (5825 passed). This todo's own checkbox was simply never flipped when the prior dispatch landed — no new code
      needed.
- [x] ✅ [BACKEND] P1. Implement Family-1 (`CARRY_RECURSIVE_BORROW_LENDING_ONLY`) real `on_tick()` leg construction in
      `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py`: add a new code path
      (do not touch the shared `staking_yield_enabled=true` branch used by the live `CARRY_RECURSIVE_STAKED` archetype)
      that, for this archetype specifically, builds a `list[AtomicLeg]` per loop iteration following the codex doc's
      STAKE → TRANSFER → LEND → BORROW bundle, mirroring `_build_loop_legs()`/`_build_instruction()`'s existing pattern
      (`:350-447`) but driven by the new `ltv_per_loop`/`n_loops` params from the prior 2 todos instead of the
      staking-yield math. This replaces the unconditional `return []` (`:194-200`) for this archetype only —
      `CARRY_BASIS_PERP_INV` still returns `[]` until the next todo lands (same file, sequential). Repo:
      strategy-service. Done-when: a new unit test drives `on_tick()` for `CARRY_RECURSIVE_BORROW_LENDING_ONLY` with
      real catalog params and asserts a non-empty, correctly-shaped `AtomicInstruction` (leg count = `n_loops` ×
      legs-per-loop, correct `action`/`instrument`/`size_units` progression), and `quality-gates.sh` is green.
- [x] ✅ [BACKEND] P1. Implement Family-2 (`CARRY_BASIS_PERP_INV`) real `on_tick()` leg construction in the same file:
      the same lending-loop legs as the prior todo, plus a perp-hedge leg using `PerpLegConfig`
      (`unified_api_contracts.internal.architecture_v2.recursive_loop_orchestrator.PerpLegConfig`) sized via
      `unified_trading_library.risk.net_delta.residual_hedge_size()` (operator-ruled formula, already shipped — do not
      re-derive). Repo: strategy-service. Done-when: a new unit test drives `on_tick()` for `CARRY_BASIS_PERP_INV` and
      asserts a non-empty `AtomicInstruction` including the correctly-sized hedge leg, and `quality-gates.sh` is green.
      — strategy-service@f2ac7fdf
- [x] ✅ [BACKEND] P1. Build the `RecursiveLoopRequest` construction + `RecursiveLoopOrchestrator.open()`/`.unwind()`
      call site in execution-service — execution-service@2352a17e new
      `execution_service/algo_library/recursive_loop_runner.py` (sibling to `leveraged_leg_controller.py`, whose own
      responsibility — drift computation + rebalance-instruction EMISSION — is the opposite direction from this module's
      AtomicInstruction CONSUMPTION -> orchestrator call). `build_recursive_loop_request()` reconstructs a
      `RecursiveLoopRequest` from a Family 1/2 `AtomicInstruction`'s legs/attestations (start_amount from the leading
      STAKE leg, lending_protocol from that leg's venue, ltv_per_loop/n_loops/collateral_asset/debt_asset from
      attestations, share_class_coin from `identity.share_class`, opening_mode via the documented 5-ETH FLASH/
      PERSISTENT crossover, perp_leg_config reconstructed for Family 2); `open_recursive_loop_position()` /
      `unwind_recursive_loop_position()` call `RecursiveLoopOrchestrator.open()`/`.unwind()` — its first real production
      caller. Not wired into `atomic_instruction_router.py` (that router's `AtomicLegExecutor` bridges only
      `LEADER_HEDGE`/sports; `ATOMIC_ON_CHAIN` dispatch-by-mode routing is a separate follow-up, outside this todo's
      done-when). Repo: execution-service. Done-when: a new integration-style unit test feeds a real `AtomicInstruction`
      (as produced by the prior 2 todos' new tests) through this call site and asserts
      `RecursiveLoopOrchestrator.open()` is invoked with a correctly-populated `RecursiveLoopRequest`, and
      `quality-gates.sh` is green. New test file `tests/unit/algorithms/test_recursive_loop_runner.py` (13 tests,
      hand-built `AtomicInstruction` fixtures mirroring strategy-service's exact shape — no cross-repo import, per the
      NO service↔service deps rule) covers both families, request-field correctness, opening-mode crossover, and error
      paths. `quality-gates.sh` green on execution-service (full run, no skip flags).
- [x] ✅ [BACKEND] P2. Audit execution-service for an existing periodic-poller/scheduler mechanism suitable for
      `PerpHedgeSizer.compute_rebalance()`/`.compute_margin_topup()` (its own docstring states "designed for 5-min poll
      cycle", `perp_hedge_sizer.py:60-63`) — grep for existing Cloud Scheduler-triggered or in-process poll loops in
      `execution-service/execution_service/defi_execution/` and `algo_library/`. If a suitable poller exists, wire
      `PerpHedgeSizer` into it as a new call site for Family-2 open positions. If none exists, state that finding
      explicitly in this todo's evidence and stop — do NOT freehand-design new scheduler infrastructure as part of this
      bounded todo; file a follow-up `[DESIGN]` todo on this plan's finalize companion instead. Repo: execution-service.
      Done-when: either (a) `PerpHedgeSizer` has a real, tested, live-reachable caller, with a new unit test proving it
      fires on a poll tick, or (b) the audit's finding (no suitable poller exists) is recorded verbatim with the exact
      grep evidence, and a follow-up todo is filed. **(b) — no suitable poller exists**, evidence in Progress Log;
      follow-up `[DESIGN]` todo filed on `/plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`.
- [x] ✅ [BACKEND] P2. Remove the two `_ALLOWED_EMPTY_ARCHETYPES` entries for `CARRY_RECURSIVE_BORROW_LENDING_ONLY`
      (`:104-108`) and `CARRY_BASIS_PERP_INV` (`:109-112`) in
      `strategy-service/tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py` now that
      both produce real non-empty `on_tick()` output — this test's own `"on_tick returned [] -- engine no-op'd"` failure
      path (`:423-425`) should now correctly exercise both archetypes for real instead of silently exempting them. Repo:
      strategy-service. Done-when: the full `test_all_catalogued_archetypes_construct_and_fire.py` suite passes green
      with both entries removed, and `quality-gates.sh` is green across strategy-service. — strategy-service@d6c86f44

## Progress Log

- **2026-08-09**: Todo 1 shipped — `resolve_ltv_mode()` added to `defi_reserve_params.py` resolving `emode_eth`/
  `market_0945`/`market_086` tokens to `(max_ltv, liquidation_threshold)` via `get_emode_params()`/
  `get_morpho_market_lltv()`; new unit tests assert 0.93/0.945/0.86; `quality-gates.sh` green.
  unified-api-contracts@547b1d1b.
- **2026-08-09**: plan authored following an exhaustive code-landscape research pass (findings recorded in
  `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s Progress Log) that confirmed exact file/function
  targets for every todo above before this plan was written, per the operator's explicit request for a tracked
  agent-orchestrator plan given the cross-repo, leveraged-money-path scope. `sequential: true` — nearly every todo
  touches one of 3 shared files (`defi_reserve_params.py` → `catalog_carry.py` → `recursive_staked.py` →
  execution-service leg-controller → the test file), and each step's correctness genuinely depends on the prior step
  landing first.
- **2026-08-09 (slot 18, backend_engineer)**: Dispatched for todo 3 (`n_loops` wiring). Found it already fully done —
  `strategy-service@b98f74fb3` (todo 2's shipped commit) added the `n_loops` param AND its test coverage in the same
  commit as the `ltv_per_loop` wiring (adjacent lines in the same dict literal, one natural commit). Confirmed via
  `git blame` (both `"n_loops": str(config.recursion_depth_max)` lines attributed to `b98f74fb3`) and by re-running
  `quality-gates.sh` on strategy-service live (green, 5825 passed, including both `n_loops`-asserting tests). Flipped
  the checkbox to reflect actual completion — no new code shipped this dispatch. Next up: todo 4 (Family-1 real
  `on_tick()` leg construction) is genuinely unstarted and substantial (`recursive_staked.py`'s STAKE→TRANSFER→LEND→
  BORROW bundle) — not attempted this turn.
- **2026-08-09 (slot 20, backend_engineer)**: Todo 4 shipped — added
  `CarryRecursiveStakedEngine._on_tick_family1_borrow_lending_only()` +
  `_build_family1_loop_legs()`/`_build_family1_instruction()` to `recursive_staked.py`: a new code path (the shared
  `staking_yield_enabled=true` branch is untouched) that builds `n_loops` iterations of a
  STAKE(debt_asset)→TRANSFER(collateral_asset)→LEND(collateral_asset)→BORROW(debt_asset) `AtomicLeg` bundle per loop,
  each iteration's BORROW output (`current_amount * ltv_per_loop`) feeding the next iteration's STAKE input, driven by
  the catalog-resolved `ltv_per_loop`/`n_loops` params from todos 1-3 (no staking-yield APY math, no target-leverage
  cutoff — `n_loops` itself is the depth policy). `CARRY_BASIS_PERP_INV` (`perp_leg_enabled=true`) still stubs to `[]`
  pending todo 5. New test file `test_recursive_borrow_lending_only_family1_on_tick.py` (6 tests) drives `on_tick()`
  with the real `aave_v3/ethereum/wsteth/weth` catalog row and asserts: non-empty `AtomicInstruction`; leg count ==
  `n_loops`(5) × 4 legs/loop == 20; per-loop action/instrument/size_units progression matches the
  STAKE→TRANSFER→LEND→BORROW spec exactly; `[]` when already positioned; `[]` when `perp_leg_enabled=true` (Family 2
  still out of scope). `quality-gates.sh` green on strategy-service (full run, no skip flags).
  strategy-service@817bb4e0.
- **2026-08-09 (slot 22, backend_engineer)**: Todo 5 shipped — added
  `CarryRecursiveStakedEngine._on_tick_family2_basis_perp_inv()` +
  `_build_perp_hedge_leg()`/`_build_family2_instruction()` to `recursive_staked.py`. Reuses Family 1's
  `_build_family1_loop_legs()` for the lending loop unchanged, then appends one CeFi perp-hedge `AtomicLeg`
  (`action=TRADE, side="SELL"`) built from a real `PerpLegConfig`
  (`unified_api_contracts.internal.architecture_v2.recursive_loop_orchestrator`) and sized via
  `unified_trading_library.risk.net_delta.residual_hedge_size(target_equity, target_net_delta)` — per
  carry-basis-perp-inv.md's Phase 1 derivation, `E_actual` (gross underlying exposure) at opening equals `target_equity`
  because the recursive loop's net on-chain delta is invariant to `d`/`ltv`; live rebalancing against the
  actually-on-chain-read `E_actual` remains `PerpHedgeSizer`'s job (todo 6, not yet wired). This replaces the `[]` stub
  for `CARRY_BASIS_PERP_INV` (`perp_leg_enabled=true`). New test file `test_carry_basis_perp_inv_family2_on_tick.py` (6
  tests) drives `on_tick()` with the real `aave_v3/ethereum/wsteth/weth/hyperliquid` catalog row and asserts: non-empty
  `AtomicInstruction`; leg count == `n_loops`(5) × 4 + 1 hedge leg == 21; hedge leg is a `SELL` `TRADE` sized via
  `residual_hedge_size`; lending-loop legs match Family 1's exact progression; `[]` when already positioned; `[]` on an
  unrecognised `perp_venue`. Also updated the now-stale Family-1 test that asserted `perp_leg_enabled=true` stayed
  stubbed (it now correctly routes to — and no-ops within, since Family-1 catalog rows carry no `perp_venue`/`perp_pair`
  — the real Family-2 path). `quality-gates.sh` green on strategy-service (full run, no skip flags, 5836 passed).
  strategy-service@f2ac7fdf.
- **2026-08-09 (slot 20, backend_engineer)**: Todo 6 shipped — new
  `execution_service/algo_library/recursive_loop_runner.py` (sibling to `leveraged_leg_controller.py`, whose
  drift-computation/rebalance-emission responsibility is the opposite direction from this module's AtomicInstruction
  CONSUMPTION -> orchestrator call). `build_recursive_loop_request()` reconstructs a `RecursiveLoopRequest` from a
  Family 1/2 `AtomicInstruction`'s legs (leading STAKE leg's `size_units`/`venue` -> `start_amount`/
  `lending_protocol`) + attestations (`ltv_per_loop`/`n_loops`/`collateral_asset`/`debt_asset`, `perp_venue`/
  `perp_pair`/`target_net_delta` for Family 2) + `identity.share_class` -> `share_class_coin`; `opening_mode` derived
  via the orchestrator's own documented 5-ETH-equivalent FLASH/PERSISTENT crossover on Ethereum/Base.
  `open_recursive_loop_position()`/`unwind_recursive_loop_position()` call `RecursiveLoopOrchestrator.open()`/
  `.unwind()` — its first real production caller. Deliberately NOT wired into `atomic_instruction_router.py`: that
  router's `AtomicLegExecutor` only bridges `LEADER_HEDGE` (sports) instructions, a different execution surface from
  this `ATOMIC_ON_CHAIN` one — dispatch-by-`execution_mode` routing is a separate wiring concern the todo's own
  done-when doesn't require. New test file `tests/unit/algorithms/test_recursive_loop_runner.py` (13 tests) builds
  Family 1/2 `AtomicInstruction` fixtures BY HAND (mirroring strategy-service's real builder logic exactly) rather than
  importing strategy-service, per execution-service's NO service↔service deps rule — covers both families' request-field
  reconstruction, the FLASH/PERSISTENT crossover (amount + chain), perp_leg_config reconstruction (including the
  `usdc_margin_buffer_min_pct` schema-default fallback, since Family 2's attestations don't carry it), and error paths
  (wrong `instrument_type`, missing chain, unknown `lending_protocol`). `quality-gates.sh` green on execution-service
  (full run, no skip flags). execution-service@2352a17e.
- **2026-08-09 (slot 8, backend_engineer)**: Todo 7 audited — **outcome (b): no suitable existing periodic-poller/
  scheduler mechanism exists in execution-service.** Exact evidence:
  - `grep -rniE "cloud.?scheduler|periodic|poll_loop|poll_interval|APScheduler|scheduler\.|asyncio\.sleep|while True|@repeat|cron" execution_service/defi_execution/ execution_service/algo_library/`
    hit exactly 3 files: `leveraged_leg_controller.py` (only `CashSweepPolicy.PERIODIC`, `:323` — a policy enum checked
    by an external caller's own decision, not a scheduler itself, and nothing in the codebase drives it on a timer
    either), `health_factor_monitor.py`, `cctp.py` (only an attestation-poll-interval config field, not a running loop).
  - `HealthFactorMonitor` (`execution_service/defi_execution/monitors/health_factor_monitor.py`) IS a genuine
    per-instance asyncio poll-loop primitive (`run()`/`_poll_loop()`/`asyncio.sleep(self._interval)`) — structurally the
    closest match — but it has **ZERO production callers**: `grep -rln "HealthFactorMonitor" execution_service/ tests/`
    returns only its own file + its own unit test (`tests/unit/defi_execution/test_health_factor_monitor.py`); it is
    never instantiated or `.run()` in `api/app.py`'s `@app.on_event("startup")` handlers or `cli/main.py`. Wiring
    `PerpHedgeSizer` into it would not make either primitive live-reachable — same problem this whole plan exists to fix
    for `RecursiveLoopOrchestrator`.
  - `start_domain_config_reloaders()` (`config_reloaders.py`, live-reachable via `api/app.py:149-152`'s
    `@app.on_event("startup")`) is the ONE genuinely live scheduling-adjacent mechanism in the service, but it wraps
    UTL's `DomainConfigReloader`, which is **pub/sub event-driven config hot-reload** (its own module docstring:
    "subscribes to per-domain config events... reloads... when notified" —
    `unified-trading-library/unified_trading_library/domain_config_reloader.py:1-21`), not a fixed-interval
    business-logic scheduler — semantically wrong for a rebalance check that needs a fresh on-chain/market read every
    tick regardless of any config diff.
  - No Cloud-Scheduler-triggered HTTP endpoint exists anywhere in execution-service's API surface:
    `grep -rln "cloud_scheduler|CloudScheduler|X-CloudScheduler|scheduler_trigger" execution_service/` returns zero
    hits; `api/app.py` and `api/main.py` carry no scheduler-triggered route.
  - Follow-up `[DESIGN]` todo filed on `/plans/active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md` per
    this todo's own instruction (do not freehand-design scheduler infra in this bounded todo). No code shipped this
    dispatch — audit-only outcome, plan-doc-only commit.
- **2026-08-09 (slot 10, backend_engineer)**: Todo 8 (final todo) shipped — found the removal already committed locally
  but unshipped: a prior slot-10 session had already committed `d6c86f44` ("remove
  CARRY_RECURSIVE_BORROW_LENDING_ONLY/CARRY_BASIS_PERP_INV allow-list exemptions") on this slot's strategy-service clone
  but never ran it through quickmerge, leaving it 1 commit ahead of `origin/live-defi-rollout` with a stale QG sentinel.
  Re-ran `quality-gates.sh` fresh on that exact HEAD (full run, no skip flags, green — sentinel now matches `d6c86f44`),
  then shipped via `quickmerge --agent --files` and verified the SHA is an ancestor of `origin/live-defi-rollout`. No
  new code changes — the diff itself (9 lines removed from `test_all_catalogued_archetypes_construct_and_fire.py`) was
  already correct from the prior session. All 8 todos on this plan are now complete — archival is tracked as its own
  gated todo in the companion finalize plan (`recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`), which
  unblocks now that `depends_on`/`gate_on_depends` clears. strategy-service@d6c86f44. (This plan-flip itself was lost
  once already when the prior session died mid-commit; redone on resume — no new code shipped this turn, only the PM doc
  flip.)
