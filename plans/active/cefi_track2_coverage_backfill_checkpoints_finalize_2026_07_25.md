---
doc_type: plan
title: CeFi Track-2 coverage backfill checkpoints — finalize (reconcile checkboxes + archive)
summary: >-
  Gated closeout for cefi_track2_coverage_backfill_checkpoints_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's sequential todos are done. Reconciles the parent
  (cefi_consolidated_closeout_2026_07_18.md) Track-2 checkboxes, cross-checks the 2 PRE-BACKFILL baselines (drafted
  separately in cefi_consolidated_native_ao_extract_2026_07_25.md) actually landed, then archives.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, coverage, backfill, archival]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]
gate_on_depends: true
source: >-
  Per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan. Precedent: cefi_satellite_ao_dispatch_batch1_2026_07_25.md /
  cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi Track-2 coverage backfill checkpoints — finalize

> **Machine-gated on `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`.
> `sequential: true` because todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile `cefi_consolidated_closeout_2026_07_18.md`'s Track-2 checkboxes.** Flip the
      resume-backfill checkbox and the 4 checkpoint-cadence checkboxes (`/data-pipeline-check-is` MID/POST,
      `/data-pipeline-check-mtds` MID/POST), citing the shipped evidence (report paths, run dates) — verify each cited
      report actually exists before citing it. Record the new coverage % superseding the archived 50.79% in the Track-2
      section. Repo: unified-trading-pm. **Done when**: all 5 named checkboxes are flipped with verified evidence and
      the new coverage % is recorded.
- [ ] [REVIEW] P1. **Cross-check the 2 PRE-BACKFILL baseline checkpoints landed.**
      `cefi_consolidated_native_ao_extract_2026_07_25.md` drafted the `/data-pipeline-check-is`/`-mtds` PRE-BACKFILL
      baselines as independent, ungated todos (timing-independent of when the backfill itself launches). Confirm both
      actually ran (report path + date) before this plan's resume-backfill todo launched — if either never ran, note the
      gap explicitly rather than silently treating the MID/POST checkpoints as a complete checkpoint cadence. Repo:
      unified-trading-pm. **Done when**: a recorded PASS/FAIL-landed verdict for both PRE-BACKFILL baselines, with
      evidence or an explicit gap note, is in this plan's Progress Log.
- [ ] [DOC] P2. **Archive `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`** via the standard 6-step ritual
      (per CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked → add the archive banner → run
      the codex-alignment check → grep the corpus for every referrer of
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus
      referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same commit.
