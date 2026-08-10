---
doc_type: plan
title:
  Execution — wire AtomicLegExecutor into live dispatch, fix paper/batch to model real leg-sequencing risk, retire dead
  multi-leg code
summary: >-
  Implements the decision artifact produced by `multi_leg_execution_systems_audit_2026_08_10.md` (`depends_on` +
  `gate_on_depends: true`). Closes the real gap this session found: multi-leg (basis/arb) trades have no wired execution
  consumer in live mode, and paper/batch both bypass real leg-sequencing risk via `BenchmarkFillEngine.settle()`'s flat
  loop — so paper(W)==batch-rerun(W) determinism holds only because both sides share the same shortcut, not because
  multi-leg execution risk is actually validated. This plan wires the real
  `AtomicLegExecutor`/`AtomicInstruction`/`LEADER_HEDGE` mechanism into live dispatch, brings paper/batch simulation
  onto the SAME sequencing/timing logic (not a parallel simulated model), and retires whichever of
  `MultiLegOrchestrator`/`instruction_adapter.py`'s dead HEDGE_BASIS path the audit verdicted DELETE.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [execution-service, strategy-service, e2e-testing]
scope: [engineer]
tags: [multi-leg, basis, arbitrage, leader-follower, determinism, batch-live-parity, atomic-instruction, execution]
related:
  [
    /plans/active/multi_leg_execution_systems_audit_2026_08_10.md,
    /plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-08-10
last_updated: 2026-08-10
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
depends_on: [multi_leg_execution_systems_audit_2026_08_10]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/active/multi_leg_execution_systems_audit_2026_08_10.md,
    execution-service/execution_service/v2/atomic_leg_executor.py,
    execution-service/execution_service/v2/atomic_instruction_router.py,
    strategy-service/strategy_service/engine/strategies/v2/live_routing.py,
    strategy-service/strategy_service/engine/backtest/benchmark_fills.py,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
supersedes:
superseded_by:
source: >-
  Operator direction 2026-08-10, following the audit plan's decision. AO-dispatchable; every todo gated on the audit's
  decision artifact so scope is fixed before implementation starts.
---

# Execution — wire the real multi-leg execution path, fix paper/batch parity

## Todos

- [x] ✅ [SCRIPT] P1. **Retire whichever system(s) the audit verdicted DELETE** — remove the dead code entirely (no
      shim, no `# removed` comment, per this workspace's HARD RULE), update/remove its now-orphaned tests, confirm
      nothing else imports it before deleting (a final grep, not trust in the audit's earlier grep alone — code may have
      moved between the audit and this execution phase). — execution-service@0a2f6018 + evidence: deleted
      `execution_service/engine/multi_leg_orchestrator.py` + `execution_service/engine/instruction_adapter.py` (both
      audit DELETE verdicts) + 4 orphaned test files; fresh grep (2026-08-10) confirmed zero non-test importers remain;
      QG green (7892 passed) + adapter-contract baseline entry for `multi_leg_orchestrator.py` removed (ratchet OK, 327
      files).
- [x] ✅ [SCRIPT] P1. **Wire `publish_atomic_instruction`/`route_atomic_instructions` into live dispatch** at the exact
      call sites the audit plan mapped (`colocated_engine.py`/`client_worker.py`/`live_execution_handler.py` or wherever
      the audit's todo actually found) — `AtomicInstruction` composites from `CarryStakedBasisEngine` and the
      prediction-arb engine the audit identified must actually reach `AtomicLegExecutor` in live mode. —
      strategy-service@4ca4385c + execution-service@27a4bd59 + evidence: publish side wired into the shared paper/batch
      tick path — `GroupBRunner` gains an opt-in `atomic_publisher` hook fired per LEADER_HEDGE `AtomicInstruction` at
      `_process_tick` (the audit-mapped call site), and `paper_run_handler.replay_carry_strategy` + `group_b_handler`
      wire it to `publish_atomic_instruction` via a new sync adapter in `live_routing.py` (family-derived `asset_group`
      shard key, e.g. CARRY_AND_YIELD→defi / ARBITRAGE_STRUCTURAL→prediction); subscribe side wired into
      `live_execution_handler._run_live_async` — a background task drains `(asset_group, atomic_instruction)` via
      `route_atomic_instructions` → paper-default `AtomicLegExecutor`. Unit tests on both sides
      (`test_live_routing_publish_wiring.py`, `test_atomic_routing_live_wiring.py`) prove the round-trip;
      `quality-gates.sh` green both repos.
- [x] ✅ [SCRIPT] P1. **Fix `BenchmarkFillEngine.settle()`** per the audit's recommended approach — the target is paper
      and batch BOTH exercising the same leader/hedge-deadline/unwind sequencing logic `AtomicLegExecutor` uses live
      (simulated fills, real sequencing), not a second parallel model. If the audit recommended the IBKR-MEL
      synthetic-callback pattern, follow that precedent's actual mechanics rather than inventing a new one. —
      strategy-service@aae2ae064d + evidence: `_compute_atomic_fill` now branches on LEADER_HEDGE mode to
      `_compute_atomic_leader_hedge_fill` (leader-first → hedge(s) within modeled deadline → compensation on failure);
      `_compute_single_leg_benchmark_fill` returns None on missing market state (modeled hedge failure);
      `_compute_unwind_fill` offsets the leader at 50 bps penalty; `_NO_FILL_ACTIONS` legs
      (TRANSFER/BRIDGE/CANCEL/CONVERT_DUST) are skipped in hedge loop (not failures). Updated
      `test_atomic_missing_leg_state_raises`→`test_atomic_missing_leg_state_models_hedge_failure` to assert
      leader+unwind fills instead of KeyError. QG green (5849 passed, 248 skipped, 3 xfailed).
- [ ] [SCRIPT] P1. **Regression test: unhedged-position risk is now VISIBLE in paper/batch results** — construct a test
      scenario where the follower/hedge leg would fail after the leader/lead leg fills (a real, not hypothetical, market
      condition) and confirm paper mode now surfaces the resulting unhedged-position alert/unwind behavior, where
      previously the flat-loop settlement would have silently filled both legs independently with no risk signal at all.
      This is the core proof that the parity gap is actually closed, not just that code compiles.
- [ ] [SCRIPT] P1. **Regression test: paper(W)==batch-rerun(W) determinism still holds** after the fix — the ε=0 proof
      this workspace requires elsewhere for batch=live symmetry, now validated against the REAL sequencing logic rather
      than the old shared shortcut. Cite/reuse the existing `citadel_paper_batch_live_reconciliation_2026_06_19.md`
      plan's proof methodology if it has one, rather than inventing a new verification approach.
- [ ] [DATA] P1. **Re-run (or newly run) a real paper-trading session for a basis/arb strategy** covering enough history
      to hit at least one genuine hedge-leg-failure scenario if the market data supports it, and compare the resulting
      P&L/fill-rate figures against whatever was previously reported (if any prior paper runs exist) to characterize how
      much the old flat-loop shortcut was overstating execution quality — this is a real, evidence-backed answer to "how
      wrong were we," not a theoretical concern.
- [ ] [DOC] P2. **Update `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`** with the new
      multi-leg-specific verification the regression tests above establish, so this class of gap has a named, checkable
      invariant going forward rather than relying on someone noticing the same way this session did.
- [ ] [DOC] P3. **Close out `plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md`** with
      `resolved_by` evidence once all of the above is live-verified — archive per the workspace's completion discipline.

## Progress Log

- 2026-08-10: Plan created, gated on the paired audit plan's decision artifact. This closes a confirmed real gap in the
  workspace's own "Batch=Live determinism" HARD RULE for multi-leg execution specifically.
- 2026-08-10 (todo 2, slot 20): **Seam wired into live dispatch on both sides.** Publish: `GroupBRunner`'s
  `_process_tick` (the shared paper/batch tick path the audit mapped) now forwards each emitted LEADER_HEDGE
  `AtomicInstruction` to an opt-in `atomic_publisher` hook; `replay_carry_strategy` (paper) + `GroupBHandler` (batch)
  wire it to `publish_atomic_instruction` via `live_routing.publish_atomic_instruction_sync` (sync adapter over the
  async seam; family-derived `asset_group` shard key via `resolve_asset_group_for_family`). Subscribe:
  `live_execution_handler._run_live_async` starts a background `_run_atomic_routing_loop` that drains the
  `(asset_group, atomic_instruction)` shards (configured + defi + prediction) through `route_atomic_instructions` into a
  PAPER-default `AtomicLegExecutor` — a LEADER_HEDGE composite from `CarryStakedBasisEngine` /
  `ArbitragePriceDispersionEngine` now actually reaches `AtomicLegExecutor` in live/paper dispatch. Unit tests both
  sides prove the publish→InMemory→route round-trip settles COMPLETE. `quality-gates.sh` green both repos (exit 0,
  sentinel = shipping HEAD). Remaining gated work unchanged (todo 3 settles `BenchmarkFillEngine` on the SAME executor).
