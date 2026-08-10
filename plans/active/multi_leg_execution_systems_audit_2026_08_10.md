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

- [ ] [DATA] P1. **Confirm `MultiLegOrchestrator`'s disposition** — re-verify the zero-production-callers finding from
      the parity-gap issue doc is still current (grep fresh, don't trust a cached finding), check every strategy family
      doc (`codex/09-strategy/architecture-v2/families/*.md`) for any stated intent to use order-book-liquidity-aware
      CeFi leg routing that `AtomicLegExecutor` doesn't cover, and reach a DELETE or KEEP-AS-REFERENCE verdict with
      cited evidence.
- [ ] [DATA] P1. **Confirm `instruction_adapter.py`'s `_decompose_hedge_basis`/`HEDGE_BASIS` path disposition** — same
      treatment. Note this is a DIFFERENT dead system from `MultiLegOrchestrator` even though both are dead — don't
      conflate their verdicts if the evidence differs.
- [ ] [DATA] P1. **Map every actual production call site that SHOULD dispatch to `AtomicLegExecutor`** — trace from
      `CarryStakedBasisEngine.on_tick()` and whichever prediction-arb engine also emits `AtomicInstruction` (identify it
      by name — the parity-gap doc says "prediction-arb engines" plural, confirm which) through to where live execution
      dispatch actually happens today (`colocated_engine.py`, `client_worker.py`, `live_execution_handler.py` — the
      parity-gap doc found NONE of these currently reference `V2EngineOrchestrator`/`on_tick`/`AtomicInstruction`;
      confirm this is still accurate and identify the EXACT point each one needs a new call/branch added).
- [ ] [DATA] P1. **Determine why the 2026-07-30 routing seam (`publish_atomic_instruction` /
      `route_atomic_instructions`) was built but never wired in** — check git blame/commit history and any plan doc from
      that date for the ORIGINAL intent (was wiring it into live dispatch explicitly deferred/out-of-scope at the time,
      or was it an oversight?). This context matters for how the execution plan should sequence the work (finishing an
      intentionally-deferred task vs. fixing a dropped one).
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
