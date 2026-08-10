---
doc_type: issue
title:
  Multi-leg (basis/arb) execution has NO wired leader-follower/unhedged-position risk path in ANY currently-running mode
  — paper==batch (both use a flat leg-settlement loop with no sequencing risk), and the real leader/hedge executors
  (MultiLegOrchestrator + AtomicLegExecutor) have ZERO production callers, so "live" has no evident execution consumer
  for AtomicInstruction-based multi-leg trades either
summary: >-
  Investigated the operator's 2026-08-10 concern: does paper/batch simulation for multi-leg trades (basis, cross-venue
  arb) take a shortcut that live wouldn't (e.g. assuming simultaneous fills) vs. real leader-follower sequencing +
  unhedged-position risk? Finding is more severe than "paper shortcuts, live doesn't" — there are TWO sophisticated
  leader-follower/unhedged-position-risk engines in this codebase (execution-service's `MultiLegOrchestrator`,
  CeFi/TradFi-oriented; and `AtomicLegExecutor`, the newer LEADER_HEDGE mechanism used by DeFi basis + prediction-arb
  engines), and BOTH have zero production callers — confirmed by grep across execution-service and strategy-service
  (only test files instantiate them; `execution_service/engine/__init__.py` doesn't even export `MultiLegOrchestrator`).
  The mechanism that ACTUALLY runs today for every currently-exercised mode (batch grid-search AND the canonical
  `paper_run` CLI operation, which strategy-service's own docstrings confirm both drive the identical `GroupBRunner`)
  settles a multi-leg `AtomicInstruction` via `BenchmarkFillEngine.settle()`'s flat `for leg in instruction.legs:` loop
  (benchmark_fills.py:385) — each leg priced independently at its own benchmark reference, with NO leader/follower
  ordering, no `hedge_deadline_ms` gap, and no partial-fill/naked-position/unwind modeling. So paper(W)==batch-rerun(W)
  determinism likely DOES hold for multi-leg trades (both use the same shortcut) — but that shared shortcut means the
  ε=0 proof gives a false sense that multi-leg execution is validated; the divergence the operator is actually worried
  about is real, it just also silently affects "live" (or rather: live has no evident execution consumer for
  AtomicInstruction composites at all right now, since `live_execution_handler.py` never references
  `V2EngineOrchestrator`/`on_tick`/`AtomicInstruction`).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, execution-service, unified-api-contracts, e2e-testing]
scope: [engineer, admin]
tags:
  [
    multi-leg,
    basis,
    arbitrage,
    leader-follower,
    determinism,
    batch-live-parity,
    atomic-instruction,
    execution,
    hard-invariant,
  ]
related:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md,
    /plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md,
  ]
created: 2026-08-10
author: worker (investigation, operator-raised concern)
source: >-
  Operator raised a specific concern 2026-08-10 about whether multi-leg (basis/arb) execution runs the SAME
  leg-sequencing/timing logic in paper/batch vs live, or whether simulation takes a shortcut misrepresenting real
  slippage/fill risk. Session had already found `execution-service/execution_service/engine/multi_leg_orchestrator.py`
  (sophisticated LEADER_FOLLOWER/LIQUIDITY_AWARE modes) and `instruction_adapter.py`'s `_decompose_hedge_basis`, with a
  suspicious signal that nothing outside tests references `MultiLegOrchestrator`. This doc's investigation confirmed
  that suspicion, traced the REAL multi-leg mechanism actually used by production strategy engines
  (`AtomicInstruction`/`AtomicLeg`/`AtomicExecutionMode.LEADER_HEDGE`, NOT the dead `HEDGE_BASIS`
  StrategyInstructionType path), and found the newer mechanism is ALSO unwired end-to-end.
assigned_vm: NA
execution_scope: local-only
assigned_role: strategy
priority: P1
estimate_class: research
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 3.6
drift_direction: advance-code
parent_epic: batch_live_symmetry_master
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    execution-service/execution_service/engine/multi_leg_orchestrator.py,
    execution-service/execution_service/engine/instruction_adapter.py,
    execution-service/execution_service/v2/atomic_leg_executor.py,
    execution-service/execution_service/v2/atomic_instruction_router.py,
    strategy-service/strategy_service/engine/strategies/v2/live_routing.py,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
    strategy-service/strategy_service/engine/backtest/benchmark_fills.py,
    strategy-service/strategy_service/cli/handlers/paper_run_handler.py,
  ]
---

# Multi-leg execution: paper==batch parity holds, but only because BOTH bypass the real leader-follower/unhedged-position risk engines — which have no live consumer either

## The operator's question, answered precisely

**Does paper/batch invoke the real leader/follower sequencing + unhedged-position handling via the SAME code path as
live, or does paper/batch take a shortcut (simultaneous fills, no partial-fill/failure modeling)?**

Answer: **paper and batch take the identical shortcut (confirmed same code path, so no paper≠batch divergence) — but
that shortcut is ALSO effectively what live gets today, because the two purpose-built leader-follower engines in this
codebase are not wired into ANY running mode.** This is not "paper diverges from live"; it's "the sophisticated
risk-management code exists, is tested in isolation, and is invoked by nothing in the real system, in any mode."

## Two separate multi-leg engines exist — both orphaned

### 1. `MultiLegOrchestrator` (execution-service, CeFi/TradFi-flavoured)

`execution-service/execution_service/engine/multi_leg_orchestrator.py:80` — `SEQUENTIAL` / `LEADER_FOLLOWER` /
`PARALLEL` / `LIQUIDITY_AWARE` modes, real unhedged-position handling (`_handle_follower_failure` →
`UNHEDGED_POSITION_ALERT` + market-order unwind + circuit-breaker fallback). Fed by
`execution-service/execution_service/engine/instruction_adapter.py` (`_decompose_hedge_basis`,
`group_instructions_to_multi_leg`, `adapt_strategy_instruction`) which decomposes a
`StrategyInstructionType.HEDGE_BASIS` into a spot + perp `ExecutionStep` pair with `depends_on=[spot_step.step_id]`.

**Verified zero production callers.** Grepped every `.py` file in execution-service:

- `MultiLegOrchestrator(` is instantiated ONLY in `tests/unit/engine/test_multi_leg_orchestrator.py`,
  `tests/unit/engine/test_multi_leg_orchestrator_new.py`,
  `tests/integration/test_multi_leg_orchestrator_integration.py`.
- `adapt_strategy_instruction`, `group_instructions_to_multi_leg`, `adapt_to_engine_instruction` (the only entry points
  into `instruction_adapter.py`) have **zero callers anywhere** except their own module and
  `tests/unit/engine/test_instruction_adapter.py`.
- `execution_service/engine/__init__.py` — the package's own public surface — exports `ExecutionOrchestrator`,
  `DefaultAlgorithmFactory`, `OrderAdapterMatchingEngine`, `SimpleDataSource`, circuit-breaker helpers. It does **not**
  export `MultiLegOrchestrator` or anything from `instruction_adapter.py`.
- `StrategyInstructionType.HEDGE_BASIS` (the type `_decompose_hedge_basis` exists to handle) has **zero emission sites**
  in strategy-service's production engine code (grepped `strategy_service/`, excluding tests) — nothing ever constructs
  a `HEDGE_BASIS` instruction, so `_decompose_hedge_basis` could never fire even if something called
  `adapt_strategy_instruction`.

This is fully dead code: a real, well-tested leader-follower/unhedged-position engine that nothing in the live system
can reach, for any strategy, in any mode.

### 2. `AtomicLegExecutor` / `AtomicInstruction` LEADER_HEDGE (the mechanism actually used by real strategies)

Real basis/arb engines don't use `HEDGE_BASIS` — they emit `AtomicInstruction` with multiple `AtomicLeg`s and
`execution_mode=AtomicExecutionMode.LEADER_HEDGE` (`unified_api_contracts/internal/architecture_v2/enums.py:376-378`).
Confirmed live in `CarryStakedBasisEngine.on_tick()` (the actual CARRY_STAKED_BASIS basis-trade engine):
`strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:784-793` constructs

```python
instruction = AtomicInstruction(
    ...
    legs=legs,
    execution_mode=AtomicExecutionMode.LEADER_HEDGE,
    leader_leg=0,
    hedge_deadline_ms=hedge_deadline_ms,
    compensation_policy=CompensationPolicy.CLOSE_LEADER_IF_HEDGE_FAILS,
    ...
)
```

The REAL leader/hedge logic lives in `execution-service/execution_service/v2/atomic_leg_executor.py:335`
(`AtomicLegExecutor`), `:362` (`execute`), `:424` (honours `instruction.hedge_deadline_ms`) — leader fires first, the
hedge leg must fill within `hedge_deadline_ms`, and `CLOSE_LEADER_IF_HEDGE_FAILS` unwinds the leader (real offsetting
order sized to the FILLED amount, not the requested amount) so `naked_position=False` is only ever reported when the
venue actually confirmed the unwind (per the archived design doc below — this is a carefully built, safety-conscious
executor).

**This is the module the archived issue `plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md` built
the "paper-LIVE routing seam" for** (shipped `execution-service@db75d51d`, 2026-07-30): strategy-service publishes each
emitted `AtomicInstruction` via
`strategy-service/strategy_service/engine/strategies/v2/live_routing.py::publish_atomic_instruction` (UTL
`EventTransport` facade, `InMemoryTransport` for paper/colocated / Pub/Sub for live); execution-service subscribes via
`execution-service/execution_service/v2/atomic_instruction_router.py::route_atomic_instructions` and calls
`AtomicLegExecutor.execute`. The archived issue's "done when" was scoped to a round-trip proof
(`e2e-testing/tests/unit/test_atomic_instruction_live_routing_seam.py`), not to wiring it into the real running system.

**Verified: it never got wired in.** Grepped every `.py` file in strategy-service and execution-service for
`publish_atomic_instruction` and `route_atomic_instructions` — each has **zero callers outside its own defining module**
(plus the isolated e2e round-trip test). Specifically checked the real paper/live runtime entry points:

- `strategy-service/strategy_service/colocated_engine.py` (`StrategySupervisor`) — no reference to `AtomicInstruction`,
  `publish_atomic_instruction`, `on_tick`, or `BenchmarkFillEngine` at all.
- `strategy-service/strategy_service/client_worker.py` (the per-client subprocess spawned by the supervisor) — same,
  zero references.
- `execution-service/execution_service/cli/handlers/live_execution_handler.py` (the actual `--mode live` handler,
  "Integrates ExecutionOrchestrator for algorithm-based execution... Routes TRADE to UTEI, DeFi... to UDEI") — never
  references `V2EngineOrchestrator`, `on_tick`, or `AtomicInstruction`. It operates on the older, single-order
  `Instruction`/`ExecutionInstruction` model (TWAP/VWAP algos), a structurally different, simpler contract than the
  multi-leg `AtomicInstruction`.

So the publish side (strategy-service, "the paper/colocated tick runtime") described in `live_routing.py`'s own
docstring as the intended caller does not exist as a real call site, and the subscribe side likewise has nothing
consuming it in a live service process.

## What ACTUALLY runs today for multi-leg trades (paper AND batch)

`strategy-service/strategy_service/cli/handlers/paper_run_handler.py` is the canonical `paper_run` CLI operation (the
one behind every `paper-<timestamp>-<hash>` run_id cited in the codex determinism-spine doc, e.g. the real 7-day
CARRY_STAKED_BASIS run `paper-20260620002237-378a3735`, 4 legs × 2 strategies). Its own docstring
(`paper_run_handler.py:2058`) states it drives:

> "Drive the SAME `V2EngineOrchestrator` (via `GroupBRunner`) the live path runs → benchmark fills."

i.e. `paper_run` and batch (grid backtest, batch rerun) both call the identical
`strategy-service/strategy_service/engine/backtest/runner.py::GroupBRunner._process_tick()` →
`strategy-service/strategy_service/engine/backtest/benchmark_fills.py::BenchmarkFillEngine.settle()`. Settling an
`AtomicInstruction` there (`benchmark_fills.py:385`) is a **flat loop**:

```python
for leg in instruction.legs:
    ...  # each leg priced independently at its own benchmark reference (arrival mid / signal-candle close)
```

No leader/follower ordering, no `hedge_deadline_ms`, no partial-fill or naked-position modeling — every leg is treated
as an independent, always-successful fill at its benchmark price. This is exactly the "assumes simultaneous/instant fill
of both legs, no partial-fill/follower-failure modeling" shortcut the operator asked about.

## Why this matters for real trading decisions

1. **paper(W) == batch-rerun(W) likely holds for multi-leg trades** — both go through the identical
   `GroupBRunner`/`BenchmarkFillEngine` path, so the workspace's ε=0 determinism proof (`reconcile_day`) would not flag
   this as a bug. That is the trap: the existing determinism proof gives confidence that multi-leg execution is
   "validated," when what it actually validates is that two simulations using the same shortcut agree with each other —
   it says nothing about whether that shortcut matches real execution risk.
2. **Backtested/paper performance for basis/arb strategies is structurally optimistic on execution risk.** Every
   CARRY_STAKED_BASIS / CARRY_BASIS_PERP / cross-venue-arb paper run to date (including the verified real runs cited in
   `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §4.3, e.g. the 2026-06-21 8-transfer-row /
   56-attribution-row run) has its P&L, fill-rate, and slippage figures computed assuming BOTH legs always fill at their
   independent benchmark price with zero leader-follower gap risk. If any promotion or sizing decision leaned on those
   figures' fill-rate/slippage assumptions specifically (as opposed to the directional signal), that decision was made
   on an execution model strictly better than what real leader-follower-sequenced execution (a leader fills, the hedge
   leg is pursued for `hedge_deadline_ms`, may fail and require an unwind at a worse price) would produce.
3. **Live has no evident execution path for `AtomicInstruction` composites at all right now** — not "live takes a
   different, real shortcut," but that the wiring to consume `V2EngineOrchestrator`'s multi-leg output in a live process
   does not exist yet (`live_execution_handler.py` never touches `on_tick`/`AtomicInstruction`; the one seam built for
   this, `live_routing.py`/`atomic_instruction_router.py`, is uncalled). This means multi-leg basis/arb strategies are
   **not actually live-executable today**, independent of the fill-model-fidelity question the operator raised — a
   strategy promoted from paper today would have nothing to execute its `AtomicInstruction`s if launched live.

## Recommended fix approach (NOT attempted here — scope for a plan)

1. **Pick ONE multi-leg engine, retire the other.** `MultiLegOrchestrator`/`instruction_adapter.py` is fully dead and
   targets a `StrategyInstructionType.HEDGE_BASIS` nothing emits; `AtomicLegExecutor`/`AtomicInstruction` is the one
   real strategy engines actually construct. Recommend deleting the former (workspace HARD RULE: delete deprecated code,
   no shims) rather than maintaining two competing multi-leg execution designs.
2. **Wire the live/paper `AtomicInstruction` seam into the real runtime**, not just the isolated round-trip test — find
   (or build) the actual per-tick driver that calls `V2EngineOrchestrator.on_tick()` in the colocated/live topology
   (this investigation did not find one; `Phase6Driver.tick()` in
   `strategy-service/strategy_service/engine/strategies/v2/phase6_driver.py` brackets `on_tick()` but is itself only
   invoked from `batch_harness.py`/`runner.py`-style callers in the code paths checked) and have it call
   `publish_atomic_instruction` per emitted `AtomicInstruction`, with execution-service's subscriber
   (`route_atomic_instructions`) actually running as part of a live/paper service process.
3. **Extend the G1 fill-model unification (already tracked in
   `/plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` /
   `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §3 G1) to explicitly cover the multi-leg case** —
   today G1 is scoped to single-leg smart-matching (`GroupCRunner`); it should also require that once wired, paper's
   `AtomicInstruction` settlement runs through `AtomicLegExecutor`'s leader/hedge/unwind semantics (with a SIMULATED
   venue adapter honouring `hedge_deadline_ms` and modeling follower-fill failure probability), not
   `BenchmarkFillEngine`'s flat per-leg loop, so paper/batch fill-rate and slippage figures for multi-leg strategies
   stop being structurally optimistic.
4. **Re-run `reconcile_day`-style determinism AND a live-shadow comparison specifically for multi-leg trades** once (2)
   and (3) ship, to get a real measured execution-alpha figure for leader-follower risk on basis/arb strategies (today
   there is none — the gap was invisible precisely because paper==batch agree with each other).

## Todos

- [ ] [OPERATOR] P1. Decide whether to prioritize wiring the live multi-leg execution path (item 2 above) ahead of any
      live promotion of a basis/arb (CARRY_STAKED_BASIS, CARRY_BASIS_PERP, cross-venue arb) strategy — as things stand,
      such a strategy cannot execute live at all, independent of the fill-fidelity gap.
- [ ] [SCRIPT] P1. Scope a plan (or fold into `citadel_paper_batch_live_reconciliation_2026_06_19.md` /
      `cross_cutting_strategy_execution_determinism_2026_07_26.md`) covering: retire
      `MultiLegOrchestrator`/`instruction_adapter.py` (dead code, HEDGE_BASIS nothing emits), wire the
      `publish_atomic_instruction`/`route_atomic_instructions` seam into the real live/paper runtime, and extend G1
      (single-leg fill-model unification) to explicitly require `AtomicLegExecutor` semantics for multi-leg paper
      settlement instead of `BenchmarkFillEngine`'s flat per-leg loop.
- [ ] [DIAG] P2. Confirm whether any CARRY_STAKED_BASIS / CARRY_BASIS_PERP paper run's fill-rate or slippage figures
      were cited in an actual promotion/sizing decision (vs. only the directional P&L signal) — if so, flag that
      decision for a re-check once the real leader-follower fill model is wired.

## Progress Log

- **2026-08-10 (investigation)**: Traced the full call chain from `StrategyInstruction`/`AtomicInstruction` emission
  through to fill/settlement in all three modes, per the operator's request. Found and confirmed via grep (zero
  production callers) that BOTH multi-leg execution engines in this codebase (`MultiLegOrchestrator` and
  `AtomicLegExecutor`) are unwired in the actual running system; paper and batch share the same
  `BenchmarkFillEngine.settle()` shortcut (flat per-leg loop, no leader-follower risk), so paper==batch determinism
  holds but doesn't validate multi-leg execution fidelity. Filed as this issue per the findings-triage HARD RULE (big
  finding: batch≠live / cross-repo / SSOT-adjacent to the paper-batch-live-reconciliation determinism spine).
