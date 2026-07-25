---
doc_type: plan
title: TradFi satellite AO batch 3 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for `tradfi_satellite_ao_dispatch_batch3_2026_07_25.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 4 of that plan's todos are done. Mirrors the batch1/batch2 finalize pattern
  (reconcile each of the 5 distinct source docs' checkboxes/frontmatter independently), plus a batch3-specific addition:
  re-check the 1 conflict-gated item and the 2 dependency-gated groups in batch3's own Deferred section, since by the
  time batch3 completes its unrelated upstream prerequisites (Surfaces C+D at scale;
  `data_completion_tradfi_2026_07_15.md`'s `instrument_availability` gap) may have shipped independently.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch3_2026_07_25]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi gap-check session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 3 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch3_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 4 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 5 distinct source docs' checkboxes/frontmatter.** For each of
      `tradfi_satellite_ao_dispatch_batch3_2026_07_25.md`'s 4 now-done todos: flip the corresponding checkbox/section
      (or frontmatter field) in its named source doc, citing the batch-3 commit(s) that shipped it — verify the actual
      shipped commit exists before citing it. The 5 source docs:
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (2 items, 1 combined todo),
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` (2 checkboxes, 1 combined todo),
      `issues/tradfi_canonical_path_migration_design_2026_07_19.md` (3-section rewrite),
      `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md` (frontmatter `status`/`resolved_by` flip),
      `issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md` (1 checkbox). For each: after flipping,
      re-check whether it now has 0 open todos remaining. Only flip a doc's `status` to `resolved` if it genuinely
      reaches 0 open todos (checkbox AND prose-form). **Done when**: all 5 source docs' corresponding
      checkboxes/sections/frontmatter are flipped with verified evidence, and any doc that genuinely reaches 0 open
      todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 1 conflict-gated item and the 2 dependency-gated groups in batch3's own Deferred
      section**, now that time has passed. (1) Re-read
      `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s "fix the FX write path + backfill manifest
      instrument_id" candidate and its competing claim (the closeout family's "two live defects" finding, now on
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`) — if either has shipped or been superseded, extract
      `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`'s FX/cash-type diagnostic as a new tracked todo
      in a follow-up batch4; if still genuinely unresolved, leave it explicitly deferred. (2) Check whether
      `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s Surfaces C+D `--apply`-at-scale P0 has landed — if
      so, extract `issues/tradfi_docs_reconciliation_findings_2026_07_21.md`'s 3 now-actionable doc/codex rewrites into
      batch4. (3) Check whether `data_completion_tradfi_2026_07_15.md`'s `instrument_availability` gap for historical
      TradFi has closed — if so, extract `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s 6 dependency-gated
      run/backtest items into batch4. **Done when**: each of the 3 deferred groups has either (a) a new tracked
      todo/plan created because its gate cleared, or (b) an explicit re-verified confirmation the conflict/dependency is
      still open.
- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch3_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all resolvable ones — verify none remain unaccounted-for) → add the archive banner →
      run the codex-alignment check → grep the corpus for every referrer of
      `tradfi_satellite_ao_dispatch_batch3_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
