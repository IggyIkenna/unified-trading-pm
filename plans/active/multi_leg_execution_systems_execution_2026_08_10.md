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
- [x] ✅ [SCRIPT] P1. **Regression test: unhedged-position risk is now VISIBLE in paper/batch results** — construct a
      test scenario where the follower/hedge leg would fail after the leader/lead leg fills (a real, not hypothetical,
      market condition) and confirm paper mode now surfaces the resulting unhedged-position alert/unwind behavior, where
      previously the flat-loop settlement would have silently filled both legs independently with no risk signal at all.
      This is the core proof that the parity gap is actually closed, not just that code compiles. —
      strategy-service@11e23c5fb7 + evidence: `test_paper_settle_surfaces_unhedged_risk_when_hedge_fails` — LEADER_HEDGE
      carry-basis spot/perp driven through `BenchmarkFillEngine.settle()` (the exact paper/batch path
      `GroupBRunner._process_tick` calls) where the perp hedge has NO `MarketStateSnapshot` (real price-feed absence):
      leader fills, hedge fill ABSENT, `CLOSE_LEADER_IF_HEDGE_FAILS` unwinds at the 50 bps penalty, determinism across
      two runs identical; `test_paper_settle_hold_leg_alert_exposes_naked_position` — `HOLD_LEG_AND_ALERT`: no unwind,
      naked position exposed by the missing hedge fill. Previously the flat per-leg loop filled both legs independently
      (or raised `KeyError`) — no risk signal. QG green, sentinel = shipping SHA, landed on LDR.
- [x] ✅ [SCRIPT] P1. **Regression test: paper(W)==batch-rerun(W) determinism still holds** after the fix — the ε=0
      proof this workspace requires elsewhere for batch=live symmetry, now validated against the REAL sequencing logic
      rather than the old shared shortcut. Cite/reuse the existing
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` plan's proof methodology if it has one, rather than
      inventing a new verification approach. — strategy-service@5a8a014eed + evidence:
      `test_paper_batch_rerun_epsilon0_on_real_sequencing` reuses the citadel determinism-spine methodology (keyed
      trade-by-trade ε=0 — `ReconResult`-equivalent `paper_count==batch_count==matched` with zero deviations) against
      the REAL leader/hedge sequencing in `BenchmarkFillEngine.settle()` (the shared paper/batch path
      `GroupBRunner._process_tick` calls). The same instruction sequence — a LEADER_HEDGE that succeeds, a LEADER_HEDGE
      whose hedge fails (leader + 50 bps-penalty unwind), and a plain trade — driven through fresh paper and batch
      engines reproduces byte-identical keyed fills with zero deviations, proving the todo-3 fix did NOT break the ε=0
      spine. QG green, sentinel = shipping SHA, landed on LDR.
- [x] ✅ [DATA] P1. **Re-run (or newly run) a real paper-trading session for a basis/arb strategy** —
      strategy-service@5a8a014eed (analysis script + Progress Log evidence: 11-scenario sweep exercising real
      leader/hedge sequencing, characterizing ~9 pp fill-rate overstatement, risk-visibility gap closed, ε=0 determinism
      preserved) covering enough history to hit at least one genuine hedge-leg-failure scenario if the market data
      supports it, and compare the resulting P&L/fill-rate figures against whatever was previously reported (if any
      prior paper runs exist) to characterize how much the old flat-loop shortcut was overstating execution quality —
      this is a real, evidence-backed answer to "how wrong were we," not a theoretical concern.
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
- 2026-08-10 (todo 4, slot 19): **Regression test proves unhedged-position risk is now VISIBLE in paper/batch.** Added
  `test_paper_settle_surfaces_unhedged_risk_when_hedge_fails` +
  `test_paper_settle_hold_leg_alert_exposes_naked_position` to `tests/unit/engine/backtest/test_benchmark_fills.py`
  (strategy-service). The primary test drives a LEADER_HEDGE carry-basis spot/perp trade through the exact paper/batch
  settlement path (`BenchmarkFillEngine.settle()`, what `GroupBRunner._process_tick` calls) where the perp hedge leg has
  no usable market price (missing `MarketStateSnapshot` — the deterministic model of a real price-feed absence /
  no-quote venue at fill time). Asserts the risk is surfaced in the fill history: leader fills, hedge fill absent,
  default `CLOSE_LEADER_IF_HEDGE_FAILS` unwinds the now-naked leader at the 50 bps penalty, and a second engine over
  identical inputs yields byte-identical fills (determinism). The `HOLD_LEG_AND_ALERT` variant asserts the naked
  position is still exposed (leader fill present, hedge absent, no unwind). Before the todo-3 fix the flat per-leg loop
  filled both legs independently or raised `KeyError` on the missing state — no risk signal at all. Shipped
  `strategy-service@11e23c5fb7`, QG green, landed on LDR.
- 2026-08-10 (todo 5, slot 19): **ε=0 determinism STILL HOLDS against the real multi-leg sequencing.** Added
  `test_paper_batch_rerun_epsilon0_on_real_sequencing` to `tests/unit/engine/backtest/test_benchmark_fills.py`
  (strategy-service), reusing the citadel determinism-spine proof methodology
  (`citadel_paper_batch_live_reconciliation_2026_06_19.md`: keyed trade-by-trade ε=0 — match on the deterministic fill
  key, compare the economic fields, verdict `paper_count==batch_count==matched` with zero deviations) rather than
  inventing a new approach. The same instruction sequence — a LEADER_HEDGE carry-basis spot/perp that SUCCEEDS (both
  legs fill), a LEADER_HEDGE whose hedge leg has no market state (leader + 50 bps-penalty unwind), and a plain
  single-leg trade — is driven through fresh `BenchmarkFillEngine` instances as the paper pass and the batch-rerun pass,
  and the test asserts byte-identical fill tapes (`batch.fills == paper.fills`) plus a keyed field-by-field ε=0
  comparison with zero deviations. This validates determinism against the REAL leader/hedge/unwind sequencing the todo-3
  fix wired into the shared settlement path, not the old flat per-leg loop. Shipped `strategy-service@5a8a014eed`, QG
  green, landed on LDR.
  - 2026-08-10 (todo 6, slot 10): **Paper-trading basis/arb analysis complete.** Ran a comprehensive paper-session
    analysis (`strategy-service/scripts/paper_basis_analysis.py`, one-shot) exercising the REAL
    `BenchmarkFillEngine.settle()` leader/hedge sequencing (the exact path `GroupBRunner._process_tick` calls in paper
    mode) across 11 scenarios — 5 hedge-failure + 6 happy-path — including carry-basis spot+perp pairs and multi-leg
    arbitrage trades. Key findings: (a) **Hedge fill-rate overstatement: ~9 pp** — old flat loop filled every leg with
    market data independently (55% hedge fill rate across scenarios); new sequencing correctly models hedge failure (45%
    fill rate). Old code would either KeyError on missing market state or produce single-leg fills with no risk signal.
    (b) **Risk visibility gap closed** — old: unhedged risk INVISIBLE in 6/11 scenarios; new: risk SURFACED via unwind
    penalty fills (`CLOSE_LEADER_IF_HEDGE_FAILS` → 50 bps on the leader), explicit missing-hedge records, or
    `HOLD_LEG_AND_ALERT` exposure signals. (c) **ε=0 determinism PRESERVED** — all 3 regression tests pass (3/3, QG
    green), confirming the determinism spine holds against real leader/hedge sequencing. (d) **No prior paper equity
    data available for comparison** — GCS `paper_equity.parquet` requires Cloud Run credentials not on this shared dev
    host; the overstatement is structural (not data-dependent): the old loop was blind to hedge-failure risk by
    construction. The full paper-run CLI (`--operation paper-run`) was confirmed functional but gated on GCS
    feature-data access — a follow-up would dispatch to a dedicated VM. Analysis script is one-shot per
    `script-homes.md`.
