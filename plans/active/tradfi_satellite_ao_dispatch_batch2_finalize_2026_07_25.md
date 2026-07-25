---
doc_type: plan
title: TradFi satellite AO batch 2 — finalize (reconcile source docs + re-check remaining deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch2_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 11 of that plan's todos are done. Mirrors the batch1_finalize pattern (reconcile each of the 11
  distinct source docs' checkboxes independently — corrected 2026-07-25 plan-reconcile, the doc list below always had 11
  entries but the prose said 9), plus one batch2-specific addition: re-check the 8 still-genuinely-conflicted Deferred
  items + the 1 operator-gated item once the operator has ruled on the queued FX-sequencing / mvp_mode decisions, and
  recommend whether `tradfi_manifest_content_recovery_completion_2026_07_24.md` (excluded from both batch1 and batch2)
  is ready for its own dedicated triage/design pass yet.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
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
depends_on: [tradfi_satellite_ao_dispatch_batch2_2026_07_25]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi re-triage session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 2 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 11 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 11 distinct source docs' checkboxes.** For each of
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s 11 now-done todos: flip the corresponding checkbox/section
      in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-2 commit(s) that
      shipped it — verify the actual shipped commit exists before citing it. The 11 source docs:
      `data_completion_tradfi_2026_07_15.md` (2 checkboxes, 1 combined todo),
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (7 checkboxes, 1 combined todo),
      `tradfi_backfill_throughput_followups_2026_07_24.md` (3 checkboxes, 1 combined todo — plus confirm the
      `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`-sourced todo also flipped this doc's own P2
      candidate on the 182,407-cell cohort), `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`,
      `issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`,
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md`,
      `issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`,
      `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`,
      `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`,
      `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`,
      `tradfi_multisource_backfill_2026_06_22.md`. For each: after flipping, re-check whether it now has 0 open todos
      remaining. Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos (checkbox AND
      prose-form). **Done when**: all 11 source docs' corresponding checkboxes/sections are flipped with verified
      evidence, and any doc that genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 8 still-genuinely-conflicted Deferred items + the 1 operator-gated item from batch2's
      own Deferred section**, now that time has passed and the operator may have ruled on the queued decisions in
      `autonomous_session_operator_decisions_2026_07_25.md`. For each of the 5 docs listed there
      (`data_completion_tradfi_2026_07_15.md`, `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
      `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`,
      `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`, `tradfi_multisource_backfill_2026_06_22.md`, plus
      `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`): re-read the specific conflicting todo in
      `tradfi_consolidated_closeout_2026_07_18.md` to check if it has since shipped (resolving the conflict by making
      the item redundant/already-covered) or if an operator ruling clarified which side should execute — if either,
      extract the item as a new tracked todo in a follow-up batch3. If still genuinely unresolved, leave it explicitly
      deferred. Also separately re-review `tradfi_manifest_content_recovery_completion_2026_07_24.md` (still flagged
      too-large/risky, excluded from both batch1 and batch2) and recommend whether it warrants its own dedicated batch3
      triage pass yet, or whether its in-flight migration state still makes that premature. **Done when**: each of the 8
      conflict-gated items + the 1 operator-gated item has either (a) a new tracked todo/plan created because a conflict
      cleared or a ruling landed, or (b) an explicit re-verified confirmation the conflict/decision is still open; and a
      fresh recommendation is recorded for the large/risky doc.
- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all resolvable ones — verify none remain unaccounted-for) → add the archive banner →
      run the codex-alignment check → grep the corpus for every referrer of
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
