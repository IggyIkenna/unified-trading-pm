---
doc_type: plan
title: Prediction satellite AO batch 2 — finalize (reconcile source docs + correct stale index claims + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch2_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 6 of that plan's todos are done. Mirrors the batch1 finalize-plan pattern (reconcile
  each of the 5 distinct source docs' checkboxes/Progress-Log entries independently), plus a batch2-specific addition:
  correct prediction_consolidated_closeout_2026_07_18.md's stale claims discovered during batch2's re-triage — the "C2a
  REFUSED — unruled" framing (superseded by the codex D1 ruling) and the "0 open todos" index entries for 3 docs where
  re-check found that claim factually wrong.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch2_2026_07_25]
gate_on_depends: true
source: >-
  Re-triage session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a
  companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 2 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until all 6 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile the 5 distinct source docs.** batch2's 6 todos cite 5 different source docs
      (`issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`, `prediction_phase_ab_residuals_2026_07_24.md`,
      `predictions_ml_walk_forward_and_arb_2026_06_20.md`, `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`,
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`,
      `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` — todo 5's combined sub-items both cite the
      phantom-reconciler doc). Confirm each source doc's checkbox/Progress Log was actually updated by its corresponding
      batch2 todo's execution (they should already be, per each todo's own Done-when), citing the batch-2 commit(s).
      **Done when**: all 6 source-doc updates are verified present with commit citations recorded in this plan's own
      Progress Log.
- [ ] [DOC] P1. **Correct `prediction_consolidated_closeout_2026_07_18.md`'s stale claims discovered during batch2's
      re-triage** (deferred here rather than into a batch2 todo, to avoid two same-priority todos editing the same
      target file concurrently): (a) the "Distinct Values / axis-value census" section's "C2a REFUSED — unruled axis, no
      migration proposed" framing (lines ~213-215, repeated in the Deferred-work section ~line 717) — replace with a
      citation to `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1: C2a is RULED (operator D1, 2026-07-20)
      UPPERCASE-target, `migration_pending`, gated on the still-open honest-coverage-harness-fix issue — NOT refused or
      unruled. (b) **Corrected 2026-07-25 plan-reconcile — only ONE of these two premises was actually wrong.** The
      kalshi doc's entry is already accurate (`prediction_consolidated_closeout_2026_07_18.md:320-322` already reads
      "status: open, 3 live-side follow-ups outstanding" — NOT a "0 open todos" claim; no edit needed there, confirm
      it's still accurate rather than hunting for text that doesn't exist). The "Aggregated source docs" index's "— 0
      open todos (closed/archived/record-only)" claim IS genuinely wrong for
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (confirmed during batch2's re-triage: the
      doc's step-4 remainder + residuals 5-6 were only partially executed despite an over-broad "DONE" checkmark
      elsewhere) — update that entry to reflect the real post-batch2 state (0 open if batch2 fully closed it, or the
      specific named residual if not). Also correct `issues/prediction_arb_live_execution_bridge_2026_07_20.md`'s "0
      open todos" entry — that doc's own text names an unresolved operator-directed architectural decision, not zero
      open work; leave it flagged as OPERATOR-GATED, not silently marked done. **Done when**: all 3 corrections are made
      with the codex/evidence citations above, and a git diff of `prediction_consolidated_closeout_2026_07_18.md` is
      referenced in this plan's Progress Log.
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere if their blocker
      cleared during batch2's execution (verify none newly cleared) → add the archive banner → run the codex-alignment
      check → grep the corpus for every referrer of `prediction_satellite_ao_dispatch_batch2_2026_07_25` and fix each
      path to point at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan
      is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself
      gets archived alongside it in the same commit.
