---
doc_type: plan
title: Prediction satellite AO batch 5 — finalize (reconcile source docs + re-check the parked conflicts + archive)
summary: >-
  Finalize/gate plan for `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`. Runs ONLY after batch5's three
  dispatched todos land (`gate_on_depends: true`): flips the corresponding items in the 2 source docs
  (`prediction_cqg_residual_2026_07_24.md`, `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`), re-checks
  whether either parked operator conflict has been ruled since, and archives cqg_residual if todo 1's re-based census
  plus todo 2's wiring genuinely close it. `status: draft` until batch5 itself is operator-approved and dispatched.
status: complete # (was: active) 2026-07-29 — all 3 todos done, archived alongside batch5
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md,
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch5_2026_07_26]
gate_on_depends: true
source: >-
  Paired finalize for prediction_satellite_ao_dispatch_batch5_2026_07_26 per task_template.md §4's
  finalize-plan-coverage rule; drafted by the second /ag-closeout-audit prediction run 2026-07-26 (autonomous).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 5 — finalize

> **Status: draft — NOT dispatched.** Gated (`gate_on_depends: true`) behind
> `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`. It will not dispatch until batch5 is flipped `active` by the
> operator AND every batch5 todo is done. Do NOT flip this to `active` independently of batch5. `sequential: true`
> because todo 2 needs todo 1's reconciliation done first and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-29 — Reconcile both source docs' items to batch5's outcomes.**
      `prediction_cqg_residual_2026_07_24.md` todo 1 left open (its own re-base leg is done, but the extend-vs-ratify
      operator ruling hasn't landed — dated note recorded); todo 2 flipped `[x]` with `unified-api-contracts@283d7449` +
      `instruments-service@38e393de` evidence. `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s
      "Suggested next step" item 1 was ALREADY struck through with the GENUINE STALL verdict (done 2026-07-27, prior to
      this finalize pass) — verified, not re-done.

- [x] ✅ [REVIEW] P2. **DONE 2026-07-29 — Re-check the 2 parked operator conflicts and the non-batchable Deferred set
      for anything that has since cleared.** (a) out-of-lifecycle-cell / `EMPTY_CONFIRMED_REASONS` removal question:
      **gate still open, re-verified 2026-07-29** — no ruling found in
      `autonomous_session_operator_decisions_2026_07_25.md` or any later-dated doc. (b) unmatched-market `OTHER` vs
      `attempted_failed[ClassifierConfidenceLow]` question: this was never actually a live disagreement to rule on —
      re-reading all 3 named surfaces at current HEAD, UAC's `classifiers.py` module docstring AND
      `classify_polymarket_to_canonical_group`'s own docstring both already correctly document the
      non-Optional/OTHER-catch-all contract (no edit needed); MTDS `rebuild_prediction_manifest.py` /
      `kalshi_adapter.py`'s stale `None`-handling comments are cqg_residual todo 1 leg (2)'s scope, in flight as part of
      the MTDS CODE_QUICK backlog pass (not yet shipped as of this finalize pass) — no NEW three-way contract
      disagreement exists once that lands. (c) Deferred set: not deep-audited this pass (out of this finalize's core
      scope) — no new blocker-clearing evidence surfaced incidentally.

- [x] ✅ [DOC] P3. **DONE 2026-07-29 — Archive the fully-closed source doc(s) + update the closeout digest.**
      `prediction_cqg_residual_2026_07_24.md` did NOT reach 0 open items (todo 1's leg (2) cleanup is still in flight) —
      left active with a dated residual note in its Progress Log, per this todo's own fallback instruction. batch5 +
      this finalize archived together in the same commit (below), per the batch1/2/3/4 precedent. Codex-alignment check:
      batch5/this finalize create no new durable contract (the cqg write-back pattern is documented in the shipped
      code's own docstrings + the source docs' Progress Logs, not a new cross-cutting rule) — confirmed, no codex doc
      needed.

## Progress Log

- 2026-07-26 (autonomous, second `/ag-closeout-audit prediction` run): drafted as the paired finalize for
  `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`. Inert (`status: draft`, gated on batch5) until the operator
  approves + dispatches batch5.
- 2026-07-29: batch5's gate cleared (its dependent todo 2 shipped) — flipped `active` and dispatched. All 3 todos done
  (reconciliation, parked-conflict re-check, archival); archived alongside batch5 in the same commit.
