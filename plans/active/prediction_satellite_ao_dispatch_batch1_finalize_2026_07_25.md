---
doc_type: plan
title: Prediction satellite AO batch 1 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 7 of that plan's todos are done. Mirrors the sports/tradfi finalize-plan pattern
  (reconcile each of the 4 distinct source docs' checkboxes/Progress-Log entries independently), plus a batch1-specific
  addition: re-check the excluded item 9 and the 12 fully-deferred docs once the operator has ruled on the queued
  decision in autonomous_session_operator_decisions_2026_07_25.md.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25" # same-day correction (consolidated-closeout split pass): corrected stale "11 open total" phase_ab_residuals citation to 13 (that doc gained 2 relocated todos from the parent, untriaged by batch1)
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
depends_on: [prediction_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 1 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until all 7 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile the source doc(s).** `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`'s 7 todos
      all cite `prediction_phase_ab_residuals_2026_07_24.md` as Source, but each todo's own Done-when records results
      into a DIFFERENT sibling doc's Progress Log (`prediction_capture_incident_remediation_2026_07_06.md`,
      `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
      `issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`, plus
      `prediction_phase_ab_residuals_2026_07_24.md` itself for todo 7). Flip the corresponding checkbox in
      `prediction_phase_ab_residuals_2026_07_24.md` for each of the 7 items (they should already be cross-referenced via
      the target docs' Progress Log entries written by each todo's own execution), citing the batch-1 commit(s).
      Re-check whether `prediction_phase_ab_residuals_2026_07_24.md` now has 0 open todos remaining (unlikely — batch1
      was a partial extraction of 9 AO-eligible items out of the doc's total **as it stood pre-relocation (11)**;
      **corrected 2026-07-25 (same-day consolidated-closeout split pass, AFTER batch1 was drafted)**: that doc's open
      total is now 13, +2 relocated in from the parent's former "Queued audits + reviews" section (an adapter dead-code
      audit + a merged reconciliation-cadence todo) that batch1's triage never saw and does NOT cover — re-verify the
      exact count live rather than trusting either historical figure, and do not assume those 2 newer items are batch1's
      concern; they are untriaged, not blocked). **Done when**: `prediction_phase_ab_residuals_2026_07_24.md`'s 7
      corresponding checkboxes are flipped with verified evidence, and each of the 3 sibling target docs' Progress Log
      entries are confirmed present.
- [ ] [REVIEW] P1. **Re-check the excluded item 9 and the 12 fully-deferred docs**, now that the operator has
      (presumably) ruled on the queued decision in `autonomous_session_operator_decisions_2026_07_25.md`. For item 9
      (the instrument_type-canonicalization re-verify excluded from batch1 for conflicting with
      `prediction_consolidated_closeout_2026_07_18.md`'s own casing-gap-to-100% item): check if that master-plan item
      has since shipped — if so, item 9 becomes conflict-free, extract it into a new tracked todo. For each of the 12
      fully-deferred docs listed in batch1's own Deferred section: spot-check whether any conflict has cleared or any
      doc has reached genuine archivability since. If either, extract new tracked todo/plan(s). If not, leave explicitly
      deferred. **Done when**: item 9's status is re-verified (dispatched or confirmed still gated), and each of the 12
      deferred docs has an explicit current-state note (still gated / newly dispatchable, with a new todo/plan created
      if so).
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved what it could — verify none remain unaddressed) → add the archive banner → run the
      codex-alignment check → grep the corpus for every referrer of `prediction_satellite_ao_dispatch_batch1_2026_07_25`
      and fix each path to point at the archived location → clear `locked_by` (already empty here, confirm). **Done
      when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this
      finalize doc itself gets archived alongside it in the same commit.
