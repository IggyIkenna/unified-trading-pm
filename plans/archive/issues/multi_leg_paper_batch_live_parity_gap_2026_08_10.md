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
status: resolved
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
resolved_by: >-
  Closed 2026-08-10 by `multi_leg_execution_systems_execution_2026_08_10.md` (all 8 todos live-verified): the dead
  `MultiLegOrchestrator`/`instruction_adapter.py` were retired (execution-service@0a2f6018, fresh-grep-confirmed zero
  importers), the `publish_atomic_instruction`/`route_atomic_instructions` seam was wired into live dispatch
  (strategy-service@4ca4385c + execution-service@27a4bd59), and `BenchmarkFillEngine.settle()` was fixed to settle
  LEADER_HEDGE through the real leader/hedge/unwind sequencing (strategy-service@aae2ae064d), with regression tests
  proving unhedged-position risk is now visible in paper/batch (strategy-service@11e23c5fb7) and ε=0 determinism still
  holds (strategy-service@5a8a014eed). The checkable invariant is codified in
  `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §4.2.1 (unified-trading-pm@a10c4ca341).
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

<!-- ARCHIVED 2026-08-10: fully resolved by multi_leg_execution_systems_execution_2026_08_10.md — dead multi-leg code
retired, LEADER_HEDGE routing wired into live dispatch, BenchmarkFillEngine settles via real leader/hedge/unwind
sequencing, invariant codified in paper-batch-live-reconciliation.md §4.2.1. -->

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

## Audit verdicts — multi-leg execution system disposition (2026-08-10)

> **Decision artifact for `multi_leg_execution_systems_audit_2026_08_10.md`.** This section records the definitive
> per-system disposition the paired execution plan (`multi_leg_execution_systems_execution_2026_08_10.md`,
> `depends_on` + `gate_on_depends` this audit) implements against. **Why in this issue doc, not a dedicated decisions
> doc:** this issue is the finding that spawned the audit; the execution plan already references it; splitting the
> decision from its investigative context would fragment the record without adding clarity.

### System 1: `MultiLegOrchestrator` → **DELETE**

**Verdict**: DELETE. Zero production callers, zero strategy-family demand for its unique capability.

**Evidence** (fresh grep 2026-08-10, not cached):

- `MultiLegOrchestrator(` instantiated ONLY in 3 test files; the `multi_leg_orchestrator` module imported nowhere
  outside its own file + tests; `execution_service/engine/__init__.py` does not export it.
- Zero of 9 strategy-family docs (`codex/09-strategy/architecture-v2/families/*.md`) reference `MultiLegOrchestrator`,
  `LIQUIDITY_AWARE`, or any book-depth-based leader-selection intent. The only codex doc describing `LIQUIDITY_AWARE` is
  the SUPERSEDED pre-v2 `/codex/09-strategy/_archived_pre_v2/cross-cutting/multi-leg-execution.md`.
- The current multi-leg model (`/codex/04-architecture/strategy-execution-protocol.md:259`) is
  `execution_mode: ATOMIC | LEADER_HEDGE | SEQUENCED_WITH_PACING` — the `AtomicLegExecutor` model, not
  `MultiLegOrchestrator`.

**Capability-gap note (why not KEEP-AS-REFERENCE):** `MultiLegOrchestrator`'s `LIQUIDITY_AWARE` mode (book-depth-based
auto leader selection) is not replicated by `AtomicLegExecutor`'s fixed `leader_leg` index. But the KEEP-AS-REFERENCE
bar — a NAMED, currently-planned strategy family needing it — is unmet. If such a need arises, add it to
`AtomicLegExecutor` as a leader-selection policy; do not revive `MultiLegOrchestrator`. Per the workspace
delete-deprecated-code HARD RULE: no shims.

**Implementation**: delete `execution-service/execution_service/engine/multi_leg_orchestrator.py` + its tests + its
references in `instruction_adapter.py` — tracked by `multi_leg_execution_systems_execution_2026_08_10.md`.

---

### System 2: `instruction_adapter.py`'s `_decompose_hedge_basis` / `HEDGE_BASIS` path → **DELETE**

**Verdict**: DELETE. Zero production callers, zero emission of the instruction type it decomposes, fully superseded by
`AtomicLegExecutor` LEADER_HEDGE.

**Evidence** (fresh grep 2026-08-10, not cached):

- `_decompose_hedge_basis` referenced ONLY inside `instruction_adapter.py` itself (dispatch at line 98, def at line
  360). The module's entry points (`adapt_strategy_instruction`, `group_instructions_to_multi_leg`,
  `adapt_to_engine_instruction`) have zero callers in ANY repo's non-test code.
- `StrategyInstructionType.HEDGE_BASIS` has **zero emission sites** in strategy-service production code. All
  basis/arb/MM/prediction v2 engines construct `AtomicInstruction` instead (the real mechanism).
- No strategy-family doc requests spot+perp `HEDGE_BASIS` decomposition. The one grep hit (`vol-trading.md` "Delta-hedge
  engine") is unrelated dynamic re-hedging for vol strategies. The only codex doc referencing `instruction_adapter` is
  SUPERSEDED pre-v2.

**Distinctness from System 1**: independent evidence, even though both land on DELETE. `MultiLegOrchestrator` is dead by
zero instantiation + no liquidity-aware-routing family intent; `instruction_adapter`'s `HEDGE_BASIS` path is dead by
zero emission of the instruction type it decomposes + zero callers of the whole module + the capability being fully
superseded by `AtomicLegExecutor` LEADER_HEDGE (the real basis engine `CarryStakedBasisEngine.on_tick()` already emits
the same spot+perp pair as `AtomicInstruction` with `execution_mode=LEADER_HEDGE`, which `AtomicLegExecutor.execute()`
covers with real sequencing/timing risk).

**Implementation**: delete the `HEDGE_BASIS`-specific path in `instruction_adapter.py` (the `_decompose_hedge_basis`
function + its dispatch branch + the `HEDGE_BASIS` member of `StrategyInstructionType` if no other consumer exists) —
tracked by `multi_leg_execution_systems_execution_2026_08_10.md`.

---

### System 3: `AtomicLegExecutor` / `AtomicInstruction` / LEADER_HEDGE routing seam → **WIRE-IN**

**Verdict**: WIRE-IN. This is the real mechanism — six production strategy engines emit LEADER_HEDGE
`AtomicInstruction`; the routing seam was built 2026-07-30 as a RULED round-trip proof and intentionally deferred on
live wiring (which was never re-tracked as a `- [ ]` todo).

#### Call-site map — the six emitting engines

| #   | Engine                                       | File                                                        | LEADER_HEDGE sites                                              |
| --- | -------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------- |
| 1   | `CarryStakedBasisEngine`                     | `carry_and_yield/staked_basis.py:784-793`                   | 5-leg ATOMIC, `leader_leg=0`, `CLOSE_LEADER_IF_HEDGE_FAILS`     |
| 2   | `CarryBasisDatedEngine`                      | `carry_and_yield/basis_dated.py:138,189,249`                | 3 sites: open-leg entry, rescale, dated-contract roll           |
| 3   | `ArbitrageCrossDomainEventEngine`            | `arbitrage_structural/cme_polymarket.py:201`                | CME ↔ Polymarket cross-domain event arb                         |
| 4   | `ArbitragePriceDispersionEngine`             | `arbitrage_structural/price_dispersion.py:255,348,713`      | 3 sites: cross-venue prediction, cross-exchange, DEX dispersion |
| 5   | `ArbitragePriceDispersionHierarchicalEngine` | `arbitrage_structural/price_dispersion_hierarchical.py:176` | 1 LEADER_HEDGE site                                             |
| 6   | `StatArbPairsFixedEngine`                    | `stat_arb_pairs/pairs_fixed.py:179,232`                     | 2 sites: open + rescale                                         |

The "prediction-arb engines" (plural) referenced by the parity-gap issue are engines 3, 4, 5 (all
`arbitrage_structural`-family).

#### The routing seam (built 2026-07-30, never wired)

- **Publish side**:
  `strategy-service/strategy_service/engine/strategies/v2/live_routing.py::publish_atomic_instruction()` — UTL
  `EventTransport` facade (`InMemoryTransport` for paper/colocated, Pub/Sub for live). Zero production callers.
- **Subscribe side**: `execution-service/execution_service/v2/atomic_instruction_router.py::route_atomic_instructions()`
  — reads from EventTransport, calls `AtomicLegExecutor.execute()`. Zero production callers.
- **Origin**: `plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md` — RULED 2026-07-28 (operator:
  the bridge goes via EventTransport event-log spine). Done-when scoped to the round-trip proof
  (`e2e-testing/tests/unit/test_atomic_instruction_live_routing_seam.py`), not live wiring. The wiring was an
  intentionally-deferred task that was never re-tracked as a `- [ ]` todo on archival — this audit (2026-08-10) surfaces
  it.

#### Exact wiring points — where each runtime needs a new call/branch

**1. Paper mode** (`GroupBRunner._process_tick()`, `runner.py:234-250`): After `V2EngineOrchestrator.on_tick()` returns
and before `BenchmarkFillEngine.settle()`, filter for LEADER_HEDGE `AtomicInstruction`s and call
`publish_atomic_instruction()` for each. In paper mode with `InMemoryTransport`, the publish→subscribe round-trip is
synchronous → `route_atomic_instructions` → `AtomicLegExecutor.execute()` produces the leader/hedge/unwind-aware fill in
the same tick. `BenchmarkFillEngine.settle()` must then be **replaced** (not supplemented) for LEADER_HEDGE instructions
— keeping both paths would double-count fills.

**2. Live/colocated mode**: A new tick driver is needed that calls `V2EngineOrchestrator.on_tick()`. The existing
`StrategySupervisor` (`colocated_engine.py`) spawns per-client `client_worker.py` subprocesses but neither currently
runs any tick loop. Wiring requires either (a) adding a tick loop to `client_worker.py` that drives
`V2EngineOrchestrator.on_tick()` → `publish_atomic_instruction()` per emitted LEADER_HEDGE instruction, or (b) adding
the same to `colocated_engine.py`'s main supervisor loop. Execution-service's `live_execution_handler.py` would then
invoke `route_atomic_instructions()` (the subscribe side) alongside its existing single-order `Instruction` handling.

**3. Batch/grid-search mode**: Identical to paper — `GroupBRunner._process_tick()` is the shared code path. Same wiring
point, same `InMemoryTransport` pattern.

---

### `BenchmarkFillEngine.settle()` — recommended fix approach

**Recommendation: Option (a)** — route multi-leg benchmark settlement through `AtomicLegExecutor`'s real
leader/hedge/unwind code in simulated-fill mode, NOT (b) a parallel model inside `BenchmarkFillEngine`.

**Current state**: `benchmark_fills.py:372` `_compute_atomic_fill` iterates `instruction.legs` independently — each leg
priced at its own benchmark reference, always-successful. No leader/follower ordering, no `hedge_deadline_ms`, no
partial-fill/naked/unwind modeling.

**Why (a) — route through AtomicLegExecutor with a synthetic venue adapter:**

- `AtomicLegExecutor` is already paper-default: constructed with no `sports_adapter`/`mode`, it builds a
  `PaperBettingAdapter` (registered under every venue key), zero real I/O. Its `execute()` already implements
  leader-first, hedge-within-deadline, and status-aware compensation (`CLOSE_LEADER_IF_HEDGE_FAILS` unwinds leader +
  placed hedges; `naked_position=False` only when the venue confirmed the unwind).
- **IBKR MEL precedent** (`runtime-topology.yaml` `ibkr_gateway_connectivity.batch_mode`): MEL replays historical events
  through the same adapter callback interface that IB Gateway uses live — adapters don't know whether the source is real
  or synthetic. This is the workspace's own proven pattern for batch=live symmetry. Benchmark settlement = replay
  benchmark fills through the same `AtomicLegExecutor` interface with a synthetic venue adapter.
- Requires: a synthetic benchmark venue adapter implementing the `SportsAdapter` protocol (`place_bet`/`cancel_bet`)
  returning arrival-mid/mark fills as pure functions of (instruction, snapshot, now_utc) for determinism;
  `hedge_deadline_ms` becomes a modeling parameter (hedge fills at reference within its modeled window, else fails →
  unwind at a modeled worse price); the async executor must be driven deterministically from the synchronous backtest
  loop.
- **Fallback (a′)** if the `SportsAdapter` protocol coupling proves too strong for non-sports legs: extract the
  leader/hedge/unwind state machine into a shared adapter-agnostic core that both the live executor and a benchmark
  driver invoke.

**Why NOT (b):** a parallel leader/hedge model inside `BenchmarkFillEngine` would be a SECOND implementation of
safety-critical sequencing semantics → the two diverge → breaks the paper(W)==batch(W) ε=0 determinism spine
(`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`). Duplicates tested logic; violates the
reuse-one-code-path pattern.

**Sequencing**: implement (a) AFTER the live-wiring call-site work, so the SAME executor serves live + benchmark.

---

### Summary table

| System                                    | Verdict              | Reason                                                                                                                      | Implementation                                                  |
| ----------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `MultiLegOrchestrator`                    | **DELETE**           | Zero callers, zero strategy-family demand for `LIQUIDITY_AWARE`                                                             | Remove module + tests; no shim                                  |
| `instruction_adapter.py` HEDGE_BASIS path | **DELETE**           | Zero callers, zero `HEDGE_BASIS` emission, superseded by `AtomicLegExecutor` LEADER_HEDGE                                   | Remove `_decompose_hedge_basis` + dispatch branch               |
| `AtomicLegExecutor` + routing seam        | **WIRE-IN**          | 6 engines emit LEADER_HEDGE; seam built but never wired; the real mechanism                                                 | Wire into paper/live/batch runtime at the 3 call sites above    |
| `BenchmarkFillEngine.settle()`            | **REPLACE with (a)** | Flat per-leg loop is structurally optimistic; route through `AtomicLegExecutor` with synthetic adapter per IBKR MEL pattern | Implement after live wiring; SAME executor for live + benchmark |

## Todos

- [x] ✅ [OPERATOR] P1. Decide whether to prioritize wiring the live multi-leg execution path (item 2 above) ahead of
      any live promotion of a basis/arb (CARRY_STAKED_BASIS, CARRY_BASIS_PERP, cross-venue arb) strategy — as things
      stand, such a strategy cannot execute live at all, independent of the fill-fidelity gap. — RESOLVED 2026-08-10:
      operator directed the wiring ahead of any live promotion (source of
      `multi_leg_execution_systems_execution_2026_08_10.md`: "Operator direction 2026-08-10, following the audit plan's
      decision"), and the execution plan's todo 2 wired `publish_atomic_instruction`/`route_atomic_instructions` into
      live dispatch (strategy-service@4ca4385c + execution-service@27a4bd59).
- [x] ✅ [SCRIPT] P1. Scope a plan (or fold into `citadel_paper_batch_live_reconciliation_2026_06_19.md` /
      `cross_cutting_strategy_execution_determinism_2026_07_26.md`) covering: retire
      `MultiLegOrchestrator`/`instruction_adapter.py` (dead code, HEDGE_BASIS nothing emits), wire the
      `publish_atomic_instruction`/`route_atomic_instructions` seam into the real live/paper runtime, and extend G1
      (single-leg fill-model unification) to explicitly require `AtomicLegExecutor` semantics for multi-leg paper
      settlement instead of `BenchmarkFillEngine`'s flat per-leg loop. — DONE via
      `multi_leg_execution_systems_execution_2026_08_10.md` (retired dead code execution-service@0a2f6018, wired seam
      strategy-service@4ca4385c + execution-service@27a4bd59, fixed `BenchmarkFillEngine.settle()`
      strategy-service@aae2ae064d, G1 extension codified in
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §4.2.1 @unified-trading-pm@a10c4ca341).
- [x] ✅ [DIAG] P2. Confirm whether any CARRY_STAKED_BASIS / CARRY_BASIS_PERP paper run's fill-rate or slippage figures
      were cited in an actual promotion/sizing decision (vs. only the directional P&L signal) — if so, flag that
      decision for a re-check once the real leader-follower fill model is wired. — MIGRATED 2026-08-10: still genuinely
      open, tracked as a `- [ ]` todo in `cross_cutting_strategy_execution_determinism_2026_07_26.md` (the active
      determinism/G1 coordination plan) so it does not evaporate with this archived issue.

## Progress Log

- **2026-08-10 (investigation)**: Traced the full call chain from `StrategyInstruction`/`AtomicInstruction` emission
  through to fill/settlement in all three modes, per the operator's request. Found and confirmed via grep (zero
  production callers) that BOTH multi-leg execution engines in this codebase (`MultiLegOrchestrator` and
  `AtomicLegExecutor`) are unwired in the actual running system; paper and batch share the same
  `BenchmarkFillEngine.settle()` shortcut (flat per-leg loop, no leader-follower risk), so paper==batch determinism
  holds but doesn't validate multi-leg execution fidelity. Filed as this issue per the findings-triage HARD RULE (big
  finding: batch≠live / cross-repo / SSOT-adjacent to the paper-batch-live-reconciliation determinism spine).
- **2026-08-10 (closeout, slot 19)**: All three audit verdicts implemented + live-verified by
  `multi_leg_execution_systems_execution_2026_08_10.md` (todos 1-7 all shipped, SHAs confirmed on origin): dead
  `MultiLegOrchestrator`/`instruction_adapter.py` retired; LEADER_HEDGE seam wired into live dispatch; paper/batch now
  settle via real leader/hedge/unwind sequencing with unhedged-risk visibility + ε=0 determinism preserved; invariant
  codified in the reconciliation SSOT §4.2.1. This issue closed with `resolved_by` evidence + archived.
