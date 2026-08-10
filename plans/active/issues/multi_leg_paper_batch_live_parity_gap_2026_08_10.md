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

## Audit verdicts — multi-leg execution engine disposition (2026-08-10)

> **This section is the audited decision artifact.** It is the durable record the gated execution plan
> (`/plans/active/multi_leg_execution_systems_execution_2026_08_10.md`, `depends_on` +
> `gate_on_depends: true` on `/plans/active/multi_leg_execution_systems_audit_2026_08_10.md`) implements against. Every
> verdict below was reached by a dispatched AO worker reading the cited source files + running fresh greps (2026-08-10,
> not cached from this issue doc's investigation). The audit plan's Progress Log carries the full per-verdict evidence;
> this section consolidates the decisions themselves — the execution plan reads this, not the audit plan's log entries.

### System 1: `MultiLegOrchestrator` → DELETE

`execution-service/execution_service/engine/multi_leg_orchestrator.py` — CeFi/TradFi-flavoured multi-leg engine
(`SEQUENTIAL` / `LEADER_FOLLOWER` / `PARALLEL` / `LIQUIDITY_AWARE` modes, unhedged-position handling via
`_handle_follower_failure` → `UNHEDGED_POSITION_ALERT` + market-order unwind + circuit-breaker fallback).

- **Zero production callers** (fresh grep 2026-08-10, not cached from the issue doc's original investigation):
  `MultiLegOrchestrator(` instantiated ONLY in test files. The module is imported nowhere outside its own file + tests.
  `execution_service/engine/__init__.py` does not export it.
- **No strategy-family doc requests order-book-liquidity-aware CeFi leg routing**: all 9
  `codex/09-strategy/architecture-v2/families/*.md` contain zero references to `MultiLegOrchestrator` /
  `AtomicLegExecutor` / `LIQUIDITY_AWARE`. The only codex doc describing `LIQUIDITY_AWARE` is the SUPERSEDED pre-v2
  `codex/09-strategy/_archived_pre_v2/cross-cutting/multi-leg-execution.md`.
- **Capability-gap note**: `AtomicLegExecutor` uses a fixed `leader_leg` index (default 0);
  `MultiLegOrchestrator`'s `LIQUIDITY_AWARE` (book-depth-based auto leader selection) is NOT replicated. But the
  KEEP-AS-REFERENCE bar — a NAMED, currently-planned strategy family needing that capability — is unmet. If such a need
  ever arises it should be added to `AtomicLegExecutor` as a leader-selection policy, not by reviving
  `MultiLegOrchestrator`.
- **Verdict**: DELETE per this workspace's own "delete deprecated code, no shims" HARD RULE. Actual code removal is
  tracked by the gated execution plan (`multi_leg_execution_systems_execution_2026_08_10.md`, todo "Retire whichever
  system(s) the audit verdicted DELETE").

### System 2: `instruction_adapter.py`'s `_decompose_hedge_basis` / `HEDGE_BASIS` path → DELETE

`execution-service/execution_service/engine/instruction_adapter.py` — decomposes a
`StrategyInstructionType.HEDGE_BASIS` into a spot+perp `ExecutionStep` pair with `depends_on=[spot_step.step_id]` via
the pre-v2 `StrategyInstruction`→`ExecutionPlan` intent-engine path.

- **Zero production callers** (fresh grep 2026-08-10): `_decompose_hedge_basis` is referenced ONLY inside
  `instruction_adapter.py` itself. The module's entry points (`adapt_strategy_instruction`,
  `group_instructions_to_multi_leg`, `adapt_to_engine_instruction`) have zero callers in ANY repo's non-test code.
  `execution_service/engine/__init__.py` does not export the module or anything from it.
- **`StrategyInstructionType.HEDGE_BASIS` has zero emission sites**: no strategy engine constructs this instruction type
  (all basis/arb/MM/prediction v2 engines construct `AtomicInstruction` instead).
- **No strategy-family doc requests spot+perp HEDGE_BASIS decomposition**: the single grep hit in
  `vol-trading.md` is a "Delta-hedge engine" (dynamic re-hedging for vol strategies) — unrelated to spot+perp basis
  decomposition. The only codex doc referencing `instruction_adapter` is the SUPERSEDED pre-v2
  `codex/09-strategy/_archived_pre_v2/cross-cutting/strategy-instruction-bus.md`.
- **Capability superseded, not missing**: the real basis engine `CarryStakedBasisEngine.on_tick()` already emits the same
  spot+perp pair as `AtomicInstruction` with `execution_mode=LEADER_HEDGE` (`staked_basis.py:784-793`), which
  `AtomicLegExecutor.execute()` covers with real sequencing/timing risk — leader-first, `hedge_deadline_ms`, and
  unwind-on-hedge-failure per `CompensationPolicy.CLOSE_LEADER_IF_HEDGE_FAILS`. No named currently-planned strategy
  family needs the dead `HEDGE_BASIS` path.
- **Verdict**: DELETE per the workspace delete-deprecated-code HARD RULE (no shims). This is a SEPARATE system from
  `MultiLegOrchestrator` with independent evidence, even though both verdicts land on DELETE — the former is dead by
  zero instantiation + no liquidity-aware-routing family intent; this one is dead by zero emission of the instruction
  type it decomposes + zero callers of the whole module + the capability being fully superseded by `AtomicLegExecutor`
  `LEADER_HEDGE`.

### System 3: `AtomicLegExecutor` / `AtomicInstruction` / `AtomicExecutionMode.LEADER_HEDGE` → WIRE-IN

`execution-service/execution_service/v2/atomic_leg_executor.py` — the REAL mechanism DeFi basis + prediction-arb
engines actually emit. Six engines across three strategy families construct `AtomicInstruction` with
`execution_mode=LEADER_HEDGE`:

| Engine | Family | File | Sites |
|--------|--------|------|-------|
| `CarryStakedBasisEngine` | carry_and_yield | `staked_basis.py:784-793` | 1 (5-leg ATOMIC) |
| `CarryBasisDatedEngine` | carry_and_yield | `basis_dated.py:138,189,249` | 3 (open/rescale/roll) |
| `ArbitrageCrossDomainEventEngine` | arbitrage_structural | `cme_polymarket.py:201` | 1 (CME↔Polymarket) |
| `ArbitragePriceDispersionEngine` | arbitrage_structural | `price_dispersion.py:255,348,713` | 3 (cross-venue-prediction / cross-exchange / dex-dispersion) |
| `ArbitragePriceDispersionHierarchicalEngine` | arbitrage_structural | `price_dispersion_hierarchical.py:176` | 1 |
| `StatArbPairsFixedEngine` | stat_arb_pairs | `pairs_fixed.py:179,232` | 2 (open + rescale) |

**The routing seam** (built 2026-07-30, the ruled EventTransport-spine mechanism):
- **Publish side**: `strategy-service/strategy_service/engine/strategies/v2/live_routing.py::publish_atomic_instruction()`
- **Subscribe side**: `execution-service/execution_service/v2/atomic_instruction_router.py::route_atomic_instructions()`
- Both use UTL `EventTransport` facade (`InMemoryTransport` for paper/colocated, Pub/Sub for live)
- **Why it was never wired**: the seam was an intentionally-scoped round-trip proof (the `prediction_arb_live_execution_bridge_2026_07_20.md` issue, ruled 2026-07-28, shipped 2026-07-30); its done-when was the e2e round-trip test + QG-green, explicitly gating live activation. The wiring was left as prose in `live_routing.py`'s docstring ("the paper/colocated tick runtime calls `publish_atomic_instruction` per emitted `AtomicInstruction`") and NEVER re-tracked as a `- [ ]` todo — a dropped follow-up per this workspace's own "every follow-up is a tracked todo" HARD RULE.

**Exact wiring points** (where each runtime needs a new call/branch):

1. **Paper mode** (`GroupBRunner._process_tick()`, `runner.py:234-250`): after `V2EngineOrchestrator.on_tick()` returns
   and before `BenchmarkFillEngine.settle()`, filter LEADER_HEDGE `AtomicInstruction`s and call
   `publish_atomic_instruction()` for each. With `InMemoryTransport`, the publish→subscribe round-trip is synchronous,
   so `route_atomic_instructions` → `AtomicLegExecutor.execute()` produces the leader/hedge/unwind-aware fill in the
   same tick. Then `BenchmarkFillEngine.settle()` should be REPLACED (not supplemented) for LEADER_HEDGE instructions —
   keeping both paths would double-count fills. `AtomicLegExecutor`'s report output should be converted into
   `BenchmarkFillRecord`s to maintain the existing ledger-emit contract downstream.

2. **Live/colocated mode**: a new tick driver is needed that calls `V2EngineOrchestrator.on_tick()`. The existing
   `StrategySupervisor` (colocated_engine.py) spawns per-client `client_worker.py` subprocesses but neither currently
   runs any tick loop. The wiring requires either (a) adding a tick loop to `client_worker.py` that drives
   `V2EngineOrchestrator.on_tick()` → `publish_atomic_instruction()` per emitted LEADER_HEDGE instruction, or (b)
   adding the same to `colocated_engine.py`'s main supervisor loop. `live_execution_handler.py` in execution-service
   would then need to invoke `route_atomic_instructions()` as part of its live execution loop, alongside its existing
   single-order `Instruction` handling.

3. **Batch/grid-search mode**: identical code path to paper — `GroupBRunner._process_tick()` is shared. Same wiring
   point, same `InMemoryTransport` pattern.

- **Verdict**: WIRE-IN — this is the real, currently-needed mechanism. The architecture is already RULED (2026-07-28,
  EventTransport-spine) and the mechanism already shipped; the remaining work is purely the missing caller wiring. This
  is "finishing an intentionally-deferred task whose follow-up was dropped," not "fixing a broken design."

### `BenchmarkFillEngine.settle()` — recommended fix approach

**Current state**: `BenchmarkFillEngine.settle()` (`benchmark_fills.py:488-502`) delegates to
`_compute_atomic_fill()` (`benchmark_fills.py:372-437`), which iterates `for leg in instruction.legs:` — a flat loop
pricing each leg independently at its own benchmark reference with NO leader/follower ordering, NO `hedge_deadline_ms`,
and NO partial-fill/naked-position/unwind modeling.

**Recommendation: option (a) — call `AtomicLegExecutor`'s actual logic in simulated-fill mode**, reusing the SAME
sequencing/timing code for paper vs. live. This is the workspace's own proven pattern:

- **IBKR MEL precedent** (`runtime-topology.yaml:1242-1254`): In `batch_mode`, the IBKR Matching Engine Layer replays
  historical events through the **same adapter EWrapper callback interface** that IB Gateway uses live. Adapters are
  written against the callback protocol only — they do not know whether the source is real or synthetic. This is
  explicitly documented as "the invariant that makes batch/live symmetry possible for TradFi."

- **`AtomicLegExecutor` already supports this**: it defaults to PAPER mode
  (`create_sports_adapter(OperationalMode.PAPER)` → `PaperBettingAdapter`). The `InMemoryTransport` for the
  publish→subscribe seam already exists. The same `AtomicLegExecutor.execute()` (leader-first → hedge within
  `hedge_deadline_ms` → `CLOSE_LEADER_IF_HEDGE_FAILS` unwind per `CompensationPolicy`) runs in paper mode with
  synthetic fills — the paper adapter fills "immediately" at the benchmark price, but the sequencing/timing/unwind
  LOGIC is identical to live. In paper mode, the adapter SHOULD be extended to simulate follower-fill failure
  probabilistically (based on `hedge_deadline_ms` and venue liquidity), so paper/batch results surface realistic
  leader-follower risk signals instead of the current per-leg-independent assumption.

- **Option (b) — building a parallel simulated leader/hedge model inside `BenchmarkFillEngine` — is explicitly rejected**:
  it would create the exact kind of two-implementation problem the batch=live determinism spine exists to prevent. One
  code path for sequencing/timing/unwind risk, two transport modes (`InMemoryTransport` for paper, Pub/Sub for live) —
  same pattern as every other EventTransport-spine shard.

**Mechanics**: `GroupBRunner._process_tick()` should, for LEADER_HEDGE `AtomicInstruction`s, call
`publish_atomic_instruction()` instead of `BenchmarkFillEngine.settle()`. The `InMemoryTransport` subscriber
(`route_atomic_instructions` → `AtomicLegExecutor.execute()`) produces `AtomicExecutionReport`s with the real
leader/hedge/unwind outcomes. The `AtomicExecutionReport` should then be converted into `BenchmarkFillRecord`s (one
per leg, carrying the fill price, filled amount, and the atomic execution status) to maintain the existing
ledger-emit contract — `GroupBRunner` still writes P&L attribution the same way; only the fill path changes.

For non-LEADER_HEDGE `AtomicInstruction`s (e.g. `ATOMIC` mode used by `sports_arb_dutching.py`), `BenchmarkFillEngine`'s
flat loop remains correct — those instructions genuinely have no leader-follower dependency, so independent per-leg
benchmark pricing is appropriate.

**Precedent cross-reference**: this is the same synthetic-callback pattern described in
`runtime-topology.yaml:1242-1254`'s `ibkr_gateway_connectivity.batch_mode` — "Adapters are written against the callback
protocol only — they do not know whether the source is real or synthetic. This is the invariant that makes batch/live
symmetry possible for TradFi." The `AtomicLegExecutor`→`EventTransport`→`route_atomic_instructions` round-trip IS the
synthetic callback for multi-leg execution; `InMemoryTransport` vs. Pub/Sub IS the paper/colocated vs. live switch.

## Todos

- [ ] [OPERATOR] P1. Decide whether to prioritize wiring the live multi-leg execution path ahead of any
      live promotion of a basis/arb (CARRY_STAKED_BASIS, CARRY_BASIS_PERP, cross-venue arb) strategy — as things stand,
      such a strategy cannot execute live at all, independent of the fill-fidelity gap.
- [x] ✅ [SCRIPT] P1. Scope a plan covering: retire `MultiLegOrchestrator`/`instruction_adapter.py` (dead code),
      wire the `publish_atomic_instruction`/`route_atomic_instructions` seam into the real live/paper runtime, and
      extend G1 to require `AtomicLegExecutor` semantics for multi-leg paper settlement —
      **unified-trading-pm@<PLACEHOLDER>** (DONE 2026-08-10: the audit plan `multi_leg_execution_systems_audit_2026_08_10.md`
      + gated execution plan `multi_leg_execution_systems_execution_2026_08_10.md` together cover all three items with
      AO-dispatched todos; the audit plan's `depends_on` + `gate_on_depends: true` relationship means the execution plan
      dispatches only after the audit's decision artifact — this section — is committed, so the rollout plan's three
      requirements map directly to the execution plan's todos 1 (retire dead code), 2 (wire seam), and 3 (fix
      BenchmarkFillEngine per the IBKR-MEL precedent))
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
