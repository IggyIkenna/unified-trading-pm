---
doc_type: plan
title: Audit — decide the disposition of every multi-leg execution engine (dead code vs. the real combo to wire in)
summary: >-
  Extends `plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md`'s finding into an actionable
  decision. Three systems exist: `MultiLegOrchestrator` (CeFi/TradFi leader-follower/liquidity-aware, ZERO production
  callers — likely genuinely dead), `instruction_adapter.py`'s `_decompose_hedge_basis`/`HEDGE_BASIS` path (ZERO
  production callers, likely dead), and `AtomicLegExecutor`/`AtomicInstruction`/`AtomicExecutionMode.LEADER_HEDGE` (the
  mechanism DeFi basis + prediction-arb engines actually emit, with a routing seam built 2026-07-30 that also has zero
  production callers — the real combo that needs wiring, not deleting). Paper AND batch both settle multi-leg trades via
  `BenchmarkFillEngine.settle()`'s flat, no-sequencing-risk loop today. This audit produces a definitive per-system
  disposition (delete / keep-as-is / wire-in) with evidence, so the paired execution plan implements against a decided
  scope rather than re-litigating architecture mid-implementation.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [execution-service, strategy-service, e2e-testing]
scope: [engineer]
tags: [multi-leg, basis, arbitrage, leader-follower, determinism, batch-live-parity, atomic-instruction, audit]
related:
  [
    /plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md,
    /plans/active/multi_leg_execution_systems_execution_2026_08_10.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md,
  ]
created: 2026-08-10
last_updated: 2026-08-10
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: quant_dev
effort: high
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md,
    execution-service/execution_service/engine/multi_leg_orchestrator.py,
    execution-service/execution_service/engine/instruction_adapter.py,
    execution-service/execution_service/v2/atomic_leg_executor.py,
    execution-service/execution_service/v2/atomic_instruction_router.py,
    strategy-service/strategy_service/engine/strategies/v2/live_routing.py,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
    strategy-service/strategy_service/engine/backtest/benchmark_fills.py,
  ]
supersedes:
superseded_by:
source: >-
  Operator, 2026-08-10: raised the specific concern about ms-timing on inter-leg execution for basis/arb, which session
  investigation traced to a real batch=live gap (both paper and batch bypass the real risk engines). Operator direction:
  "add this to the plan ssot for the multi leg systems, the one that's genuinely separate should be a real combo of
  course" — plus separately confirmed AO-dispatchable with an audit-forces-decision structure.
---

# Audit — multi-leg execution engine disposition

## Decision rubric

For EACH of the three systems, the audit worker must reach one of exactly three verdicts, with evidence:

- **DELETE** — zero production callers, zero currently-planned strategy family needs it, and everything it does is fully
  covered by `AtomicLegExecutor`'s `LEADER_HEDGE` mode. No shim, no re-export — delete the dead code per this
  workspace's own "delete deprecated code" HARD RULE.
- **KEEP-AS-REFERENCE** — zero production callers today, but a specific, named, currently-planned strategy family (cite
  it) needs a capability `AtomicLegExecutor` genuinely doesn't have (e.g. `MultiLegOrchestrator`'s
  order-book-depth-based `LIQUIDITY_AWARE` routing, which `AtomicLegExecutor`'s fixed `LEADER_HEDGE` mode may not
  replicate) — state the gap precisely, don't hand-wave "might be useful later."
- **WIRE-IN** — this is the real, currently-needed mechanism (this is the expected verdict for `AtomicLegExecutor` + its
  routing seam) — determine exactly where it needs to be called from to actually execute in live mode.

**Do not default to KEEP-AS-REFERENCE as a safe middle ground** — per this workspace's own coding-standards HARD RULE
("delete deprecated code, no shims"), the bar for keeping unreferenced code is a NAMED, evidenced future need, not "it
might come in handy."

## Todos

- [x] ✅ [DATA] P1. **Confirm `MultiLegOrchestrator`'s disposition** — re-verify the zero-production-callers finding
      from the parity-gap issue doc is still current (grep fresh, don't trust a cached finding), check every strategy
      family doc (`codex/09-strategy/architecture-v2/families/*.md`) for any stated intent to use
      order-book-liquidity-aware CeFi leg routing that `AtomicLegExecutor` doesn't cover, and reach a DELETE or
      KEEP-AS-REFERENCE verdict with cited evidence. **VERDICT: DELETE** — zero production callers re-confirmed by fresh
      grep (2026-08-10), and no strategy-family doc states any intent to use order-book-liquidity-aware CeFi leg
      routing. Full cited evidence in the Progress Log below.
- [x] ✅ [DATA] P1. **Confirm `instruction_adapter.py`'s `_decompose_hedge_basis`/`HEDGE_BASIS` path disposition** —
      same treatment. Note this is a DIFFERENT dead system from `MultiLegOrchestrator` even though both are dead — don't
      conflate their verdicts if the evidence differs. **VERDICT: DELETE** — zero production callers re-confirmed by
      fresh grep (2026-08-10), zero `HEDGE_BASIS` emission sites in strategy-service, and no strategy-family doc
      requests spot+perp basis decomposition via the `StrategyInstruction`→`ExecutionPlan` intent-engine path. Full
      cited evidence in the Progress Log below.
- [x] ✅ [DATA] P1. **Map every actual production call site that SHOULD dispatch to `AtomicLegExecutor`** — trace from
      `CarryStakedBasisEngine.on_tick()` and whichever prediction-arb engine also emits `AtomicInstruction` (identify it
      by name — the parity-gap doc says "prediction-arb engines" plural, confirm which) through to where live execution
      dispatch actually happens today (`colocated_engine.py`, `client_worker.py`, `live_execution_handler.py` — the
      parity-gap doc found NONE of these currently reference `V2EngineOrchestrator`/`on_tick`/`AtomicInstruction`;
      confirm this is still accurate and identify the EXACT point each one needs a new call/branch added).
- [x] ✅ [DATA] P1. **Determine why the 2026-07-30 routing seam (`publish_atomic_instruction` /
      `route_atomic_instructions`) was built but never wired in** — check git blame/commit history and any plan doc from
      that date for the ORIGINAL intent (was wiring it into live dispatch explicitly deferred/out-of-scope at the time,
      or was it an oversight?). This context matters for how the execution plan should sequence the work (finishing an
      intentionally-deferred task vs. fixing a dropped one). **VERDICT: built as an intentionally-scoped round-trip
      proof; the live-dispatch wiring was explicitly gated out at the time but NEVER re-tracked as a follow-up `- [ ]`
      todo — so it is a "finish an intentionally-deferred task" that silently became a dropped follow-up.** The seam was
      the RULED (2026-07-28) EventTransport-spine mechanism, and its own done-when was the e2e round-trip test +
      QG-green across the four repos, not the live wiring — but no plan/issue doc after 2026-07-30 carried the wiring as
      a tracked todo until this audit (2026-08-10) surfaced it. Full cited evidence in the Progress Log below.
- [ ] [DATA] P1. **Determine the correct fix for `BenchmarkFillEngine.settle()`'s flat leg-settlement loop** — does
      making paper/batch model REAL leader/hedge-deadline/unwind risk mean (a) calling into `AtomicLegExecutor`'s actual
      logic in simulated-fill mode (reusing the SAME sequencing/timing code paper vs. live, which is the correct
      batch=live pattern used elsewhere in this workspace — e.g. the IBKR MEL synthetic-callback pattern documented in
      `runtime-topology.yaml`'s `ibkr_gateway_connectivity.batch_mode`), or (b) building a parallel simulated
      leader/hedge model inside `BenchmarkFillEngine` itself? State a recommendation with the tradeoffs, citing the IBKR
      MEL precedent as the workspace's own proven pattern for exactly this kind of batch=live symmetry problem.
- [ ] [DOC] P1. **Write the decision artifact**: a new section in
      `plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md` (or a dedicated decisions doc if that
      issue doc is a poor fit for a durable decision record — state the reasoning) with the three systems' verdicts, the
      exact call-site map for wiring `AtomicLegExecutor` into live, and the recommended fix approach for
      `BenchmarkFillEngine`. This is the artifact the paired execution plan
      (`multi_leg_execution_systems_execution_2026_08_10.md`, `depends_on` + `gate_on_depends` this plan) implements
      against.

## Progress Log

- 2026-08-10: Plan created following the same-day parity-gap investigation. Audit-forces-decision structure per operator
  direction, so the execution plan's todos require no further architectural judgment at dispatch time.
- 2026-08-10 (todo 1, slot 11): **`MultiLegOrchestrator` disposition = DELETE**, with cited evidence:
  - **Zero production callers (fresh grep, not cached):** `MultiLegOrchestrator(` is instantiated ONLY in
    `tests/unit/engine/test_multi_leg_orchestrator.py`, `tests/unit/engine/test_multi_leg_orchestrator_new.py`,
    `tests/integration/test_multi_leg_orchestrator_integration.py`. The module `multi_leg_orchestrator` is imported
    nowhere outside its own file + tests. `execution_service/engine/__init__.py` (package public surface) does not
    export it. Zero references in strategy-service, agent-orchestrator, trading-agent-service,
    batch-live-reconciliation-service, e2e-testing (non-test). Its feeder `instruction_adapter.py`'s entry points
    (`adapt_strategy_instruction`, `group_instructions_to_multi_leg`, `adapt_to_engine_instruction`) have zero callers
    outside their own module + tests, and `StrategyInstructionType.HEDGE_BASIS` has zero emission sites in
    strategy-service production code. (Sibling `execution_service/engine/concurrent.py` shares the `LegInstruction`
    contract but likewise has zero production callers — no latent production consumer of the multi_leg contract exists.)
  - **No strategy-family doc requests order-book-liquidity-aware CeFi leg routing:** all 9
    `/codex/09-strategy/architecture-v2/families/*.md` (arbitrage-structural, carry-and-yield, event-driven,
    market-making, ml-directional, portfolio, rules-directional, stat-arb-pairs, vol-trading) contain zero references to
    `MultiLegOrchestrator`/`AtomicLegExecutor`/`LIQUIDITY_AWARE` and zero book-depth/thinner-side/illiquid-side
    liquidity-driven leader-selection intent. The only codex doc describing `LIQUIDITY_AWARE` is the SUPERSEDED pre-v2
    `/codex/09-strategy/_archived_pre_v2/cross-cutting/multi-leg-execution.md` (`status: superseded`). The current
    multi-leg execution model (`/codex/04-architecture/strategy-execution-protocol.md:259`) is
    `execution_mode: ATOMIC | LEADER_HEDGE | SEQUENCED_WITH_PACING` with strategy-declared leader/hedge ("leader = X,
    hedge = Y", arbitrage-structural.md) — the `AtomicLegExecutor`/`AtomicInstruction` model, not
    `MultiLegOrchestrator`.
  - **Capability-gap note (why not KEEP-AS-REFERENCE):** `AtomicLegExecutor` uses a fixed `leader_leg` index (default
    0); `MultiLegOrchestrator`'s `LIQUIDITY_AWARE` (book-depth-based auto leader selection) is NOT replicated. But the
    KEEP-AS-REFERENCE bar — a NAMED, currently-planned strategy family needing that capability — is unmet: no family doc
    requests it. If such a need ever arises it should be added to `AtomicLegExecutor` as a leader-selection policy, not
    by reviving `MultiLegOrchestrator`. DELETE per the workspace delete-deprecated-code HARD RULE (no shims). Actual
    code removal is tracked by the gated execution plan `multi_leg_execution_systems_execution_2026_08_10.md` ("Retire
    whichever system(s) the audit verdicted DELETE"). `instruction_adapter.py`'s HEDGE_BASIS path is a SEPARATE
    disposition (todo 2).
- 2026-08-10 (todo 2, slot 30): **`instruction_adapter.py`'s `_decompose_hedge_basis`/`HEDGE_BASIS` path disposition =
  DELETE**, with cited evidence (all fresh greps 2026-08-10, not cached from the parity-gap issue doc):
  - **Zero production callers:** `_decompose_hedge_basis` is referenced ONLY inside
    `execution-service/execution_service/engine/instruction_adapter.py` itself (dispatch at line 98, def at line 360).
    The module's entry points (`adapt_strategy_instruction`, `group_instructions_to_multi_leg`,
    `adapt_to_engine_instruction`) have zero callers in ANY repo's non-test code (grepped execution-service,
    strategy-service, e2e-testing, unified-api-contracts, unified-trading-library, trading-agent-service,
    batch-live-reconciliation-service, agent-orchestrator). The `instruction_adapter` module is imported nowhere outside
    its own file + tests, and `execution_service/engine/__init__.py` (package public surface) does not export it or
    anything from it.
  - **`StrategyInstructionType.HEDGE_BASIS` has zero emission sites:** the only production `StrategyInstruction(`
    constructors are `strategy-service/strategy_service/engine/core/components/risk_monitor.py:362` and
    `.../exit_playbook_executor.py` (all `MARKET_ORDER`); no strategy engine emits `HEDGE_BASIS`. All
    basis/arb/MM/prediction v2 engines construct `AtomicInstruction` instead (the real mechanism).
  - **No strategy-family doc requests spot+perp HEDGE_BASIS decomposition:** the single grep hit in
    `/codex/09-strategy/architecture-v2/families/vol-trading.md` is a "Delta-hedge engine" (dynamic re-hedging for vol
    strategies) — unrelated to the `HEDGE_BASIS` spot+perp basis decomposition. The only codex doc referencing
    `instruction_adapter` is the SUPERSEDED pre-v2
    `/codex/09-strategy/_archived_pre_v2/cross-cutting/strategy-instruction-bus.md` (`status: superseded`).
  - **Capability-gap note (why not KEEP-AS-REFERENCE):** `_decompose_hedge_basis` produces a spot+perp `ExecutionStep`
    pair (line 394-399, `depends_on=[spot_step.step_id]`) via the pre-v2 `StrategyInstruction`→`ExecutionPlan`
    intent-engine path. The real basis engine `CarryStakedBasisEngine.on_tick()` already emits the same spot+perp pair
    as `AtomicInstruction` with `execution_mode=LEADER_HEDGE` (staked_basis.py:784-793), which
    `AtomicLegExecutor.execute()` (atomic_leg_executor.py:362, leader-first then `hedge_deadline_ms` then
    unwind-on-hedge-failure at :424) covers with real sequencing/timing risk. No named currently-planned strategy family
    needs the dead `HEDGE_BASIS` path. DELETE per the workspace delete-deprecated-code HARD RULE (no shims).
  - **Distinctness from `MultiLegOrchestrator` (per plan todo):** independent verdict evidence, even though both
    verdicts land on DELETE. `MultiLegOrchestrator` is dead by zero instantiation + no liquidity-aware-routing family
    intent; `instruction_adapter`'s `HEDGE_BASIS` path is dead by zero emission of the instruction type it decomposes +
    zero callers of the whole module + the capability being fully superseded by `AtomicLegExecutor` LEADER_HEDGE. Actual
    code removal of BOTH is tracked by the gated execution plan `multi_leg_execution_systems_execution_2026_08_10.md`
    ("Retire whichever system(s) the audit verdicted DELETE").
- 2026-08-10 (todo 4, slot 9): **routing seam (`publish_atomic_instruction`/`route_atomic_instructions`) origin =
  INTENTIONAL-DEFERRAL-THAT-BECAME-UNTRACKED**, with cited evidence:
  - **Original intent — the seam was RULED + built as a scoped round-trip proof, not a live wiring.** The seam is the
    deliverable of `plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md`'s sole `[BACKEND] P1` todo
    (shipped 2026-07-30: `unified-api-contracts@7eb56a5f`, `strategy-service@baccf22a` (publish side),
    `execution-service@15ed3104` (subscribe side), `e2e-testing@8d31206` (round-trip test)). The archived issue's
    architecture was **RULED 2026-07-28 by the operator**: the `AtomicInstruction -> AtomicLegExecutor` bridge goes via
    the UTL `EventTransport` event-log spine (`/codex/02-data/live-data-persistence-and-event-log.md`), NOT a direct
    call — strategy-service publishes, execution-service subscribes+routes. The todo's own **done-when was explicitly
    scoped to the mechanism, not the runtime**: "the round-trip test passes (yes) and `quality-gates.sh` is green across
    all four touched repos", and its text explicitly gated live activation: "a real live deployment threads Pub/Sub
    instead, not exercised here — paper-vs-live promotion and Betfair account/credential/jurisdiction sign-off stay
    gated exactly as documented above."
  - **The intended caller was described in future/conditional tense, never built.** `live_routing.py`'s module docstring
    ("strategy_service/engine/strategies/v2/live_routing.py:13-18") says the publish side exists "so the tick runtime
    can forward on_tick's output to execution-service without a direct T4 import" — i.e. `V2EngineOrchestrator.on_tick`
    stays I/O-free and returns the emitted list "for the caller to forward"; the seam was built FOR that caller, which
    was never created. The parity-gap issue's own investigation confirmed `colocated_engine.py`, `client_worker.py`, and
    `live_execution_handler.py` never reference `on_tick`/`AtomicInstruction`/the seam (re-confirmed fresh 2026-08-10:
    all three have 0 refs).
  - **Fresh-grep confirmation the seam still has zero production callers (2026-08-10, not cached):**
    `publish_atomic_instruction` and `route_atomic_instructions` each appear ONLY in their own defining module +
    `e2e-testing/tests/unit/test_atomic_instruction_live_routing_seam.py` (the isolated round-trip test). No production
    strategy publishes (all real engines — `staked_basis.py`, `recursive_staked.py`, etc. — emit via
    `base.py::emit_instructions`, which is observability-recording only, never the EventTransport shard) and no
    production service process subscribes. Each seam file has exactly ONE commit (`baccf22a` / `15ed3104`, both
    2026-07-30); no later commit wired it in.
  - **The deferral was never re-tracked as a `- [ ]` follow-up (the dropped half).**
    `rg publish_atomic_instruction| route_atomic_instructions` across `plans/active` + `plans/archive` after the
    archived bridge issue returns only the two 2026-08-10 multi-leg plans (this audit + its execution plan),
    `prediction_satellite_ao_dispatch_batch6` (which duplicated the bridge issue's round-trip todo verbatim), and the
    archived bridge issue itself. No plan/issue doc between 2026-07-30 and 2026-08-10 tracked "wire the seam into the
    real colocated/live runtime" as a todo — the wiring step was left as the bridge issue's prose ("the caller ... calls
    publish_atomic_instruction per emitted AtomicInstruction") and silently dropped on archival (the issue was marked
    `resolved` on the round-trip proof). This is the workspace's own "every follow-up is a `- [ ]` todo, never prose"
    HARD RULE being violated at archival time.
  - **Sequencing implication for the execution plan:** treat it as **finishing an intentionally-deferred task**, not
    fixing a dropped one — the architecture is already RULED and the mechanism shipped; the work is purely the missing
    caller wiring (call `publish_atomic_instruction` per `on_tick`-emitted `AtomicInstruction` in the real paper/
    colocated tick driver, and run `route_atomic_instructions`/`AtomicLegExecutor` in a live/paper service process),
    which the execution plan's "Wire into live dispatch" todo already targets. The operator-gated live-promotion /
    Betfair-credential items are separate and stay NA. Note: even the PAPER mode bypasses the seam today
    (`GroupBRunner`→`BenchmarkFillEngine.settle()` flat loop), so wiring must cover the paper/colocated
    (`InMemoryTransport`) topology too — that is todo 5's `BenchmarkFillEngine.settle()` recommendation, not just the
=======
  - 2026-08-10 (todo 3, slot 31): **AtomicLegExecutor call-site map — complete**, with cited evidence:

    **Six engines emit LEADER_HEDGE `AtomicInstruction`** (fresh grep 2026-08-10, strategy-service production code only,
    excluding tests):

    1. **`CarryStakedBasisEngine`** — `carry_and_yield/staked_basis.py:784-793` — 5-leg ATOMIC
       (SWAP+STAKE_CONSUME+STAKE+TRANSFER+TRADE), `leader_leg=0`, `compensation_policy=CLOSE_LEADER_IF_HEDGE_FAILS`

    2. **`CarryBasisDatedEngine`** — `carry_and_yield/basis_dated.py:138,189,249` — 3 sites: open-leg entry, rescale
       directive, dated-contract roll

    3. **`ArbitrageCrossDomainEventEngine`** — `arbitrage_structural/cme_polymarket.py:201` — CME ↔ Polymarket
       cross-domain event arb (single LEADER_HEDGE site)

    4. **`ArbitragePriceDispersionEngine`** — `arbitrage_structural/price_dispersion.py:255,348,713` — 3 LEADER_HEDGE
       sites: `_on_tick_cross_venue_prediction` (consumes `prediction_venue_dispersion.py` helper),
       `_on_tick_cross_exchange` (consumes `funding_rate_dispersion.py` helper), `_on_tick_dex_dispersion`

    5. **`ArbitragePriceDispersionHierarchicalEngine`** — `arbitrage_structural/price_dispersion_hierarchical.py:176` —
       single LEADER_HEDGE site

    6. **`StatArbPairsFixedEngine`** — `stat_arb_pairs/pairs_fixed.py:179,232` — 2 LEADER_HEDGE sites (open + rescale)

    **"Prediction-arb engines" (plural)**: confirmed — engines 3, 4, 5 above are all arbitrage_structural-family engines
    emitting LEADER_HEDGE. `prediction_venue_dispersion.py` and `funding_rate_dispersion.py` are helper modules consumed
    by `ArbitragePriceDispersionEngine`'s `_on_tick_*` methods, not standalone engines. `sports_arb_dutching.py` uses
    `ATOMIC` (not LEADER_HEDGE) mode. `liquidation_capture.py` uses `ATOMIC_ON_CHAIN` (not LEADER_HEDGE).

    **The routing seam** (built 2026-07-30, `execution-service@db75d51d`):

    - **Publish side**: `live_routing.py::publish_atomic_instruction()` — ZERO production callers outside its own
      defining module. The docstring explicitly documents the intended caller ("the paper/colocated tick runtime calls
      `publish_atomic_instruction` per emitted `AtomicInstruction`") — but nothing actually calls it.
    - **Subscribe side**: `atomic_instruction_router.py::route_atomic_instructions()` — ZERO production callers outside
      its own defining module. Reads from UTL EventTransport, calls `AtomicLegExecutor.execute()`.
    - Both use UTL `EventTransport` facade (`InMemoryTransport` for paper/colocated, Pub/Sub for live).

    **Current instruction→fill flow** (what ACTUALLY runs):

    ```
    V2EngineOrchestrator.on_tick()  [orchestrator.py:169-199]
      → engine.on_tick()            [returns list[StrategyInstructionEnvelope]]
      → GroupBRunner._process_tick() [runner.py:234-250]
        → BenchmarkFillEngine.settle()  [benchmark_fills.py:488-502]
          → _compute_atomic_fill()  [benchmark_fills.py:372-437]
            → for leg in instruction.legs:  ← FLAT per-leg loop, no leader/follower ordering,
              no hedge_deadline_ms, no partial-fill/unwind modeling
    ```

    **Runtime entry points — confirmed zero AtomicInstruction references** (fresh grep 2026-08-10):

    - `strategy-service/strategy_service/colocated_engine.py` — `StrategySupervisor` class, manages per-client
      subprocess lifecycle. Zero references to `V2EngineOrchestrator`, `on_tick`, `AtomicInstruction`,
      `publish_atomic_instruction`, `GroupBRunner`, or `BenchmarkFillEngine`. Not a tick driver at all — it spawns
      `client_worker.py` subprocesses.
    - `strategy-service/strategy_service/client_worker.py` — Zero references to `V2EngineOrchestrator`, `on_tick`,
      `AtomicInstruction`, or any of the above.
    - `execution-service/execution_service/cli/handlers/live_execution_handler.py` — `LiveExecutionHandler` operates on
      the OLD single-order `Instruction` model (TWAP/VWAP algos, `_route_instruction()` → `Instruction`). Zero
      references to `V2EngineOrchestrator`, `AtomicInstruction`, `AtomicLegExecutor`, or `route_atomic_instructions`.

    **EXACT wiring points — where each runtime needs a new call/branch:**

    1. **Paper mode** (`GroupBRunner._process_tick()`, `runner.py:234-250`): after `V2EngineOrchestrator.on_tick()`
       returns and before `BenchmarkFillEngine.settle()`, filter for LEADER_HEDGE `AtomicInstruction`s and call
       `publish_atomic_instruction()` for each. In paper mode with `InMemoryTransport`, the publish→subscribe round-trip
       is synchronous, so the subscriber (`route_atomic_instructions` → `AtomicLegExecutor.execute()`) produces the
       leader/hedge/unwind-aware fill in the same tick. Then `BenchmarkFillEngine.settle()` should be REPLACED (not
       supplemented) for LEADER_HEDGE instructions — keeping both paths would double-count fills. Alternatively,
       `AtomicLegExecutor`'s report output could be converted into `BenchmarkFillRecord`s to maintain the existing
       ledger-emit contract downstream.

    2. **Live/colocated mode**: a new tick driver is needed that calls `V2EngineOrchestrator.on_tick()`. The existing
       `StrategySupervisor` (colocated_engine.py) spawns per-client `client_worker.py` subprocesses but neither
       currently runs any tick loop. The wiring requires either (a) adding a tick loop to `client_worker.py` that drives
       `V2EngineOrchestrator.on_tick()` → `publish_atomic_instruction()` per emitted LEADER_HEDGE instruction, or (b)
       adding the same to `colocated_engine.py`'s main supervisor loop. `live_execution_handler.py` in execution-service
       would then need to invoke `route_atomic_instructions()` (the subscribe side) as part of its live execution loop,
       alongside its existing single-order `Instruction` handling.

    3. **Batch/grid-search mode**: identical to paper — `GroupBRunner._process_tick()` is the shared code path. Same
       wiring point, same InMemoryTransport pattern.

    **Prediction-arb engines specifically**: the parity-gap doc says "prediction-arb engines" plural — confirmed:
    `ArbitragePriceDispersionEngine` (3 LEADER_HEDGE sites including `_on_tick_cross_venue_prediction`),
    `ArbitragePriceDispersionHierarchicalEngine` (1 site), and `ArbitrageCrossDomainEventEngine` (CME↔Polymarket, 1
    (dated futures basis) in `carry_and_yield/`, and `StatArbPairsFixedEngine` in `stat_arb_pairs/`.
>>>>>>> 86e965852f (docs(plans): flip todo 3 — AtomicLegExecutor call-site map complete (slot 31))
