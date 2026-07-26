---
doc_type: plan
title: Sports satellite AO batch 5 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch5_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 25 of that plan's todos are done. Mirrors batch3/batch4-finalize's pattern (reconcile each distinct
  source doc's checkboxes independently once its batch-5 todo lands, then re-check the Deferred conflict-gated +
  operator-gated items for any that have since cleared), then archives batch5 via the standard 6-step ritual.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: sports_master
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
depends_on: [sports_satellite_ao_dispatch_batch5_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the batch2/batch3/batch4 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 5 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch5_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 25 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 25 distinct source docs' checkboxes.** For each of
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in
      its named source doc(s) (each todo's text ends with "Source: `<doc>.md`" — 2 todos cite two source docs each, the
      ml-service odds-feature-naming migration and the T2.9/T2.10 MDT schema-drift fix; flip both cited docs for those),
      citing the batch-5 commit(s) that shipped it — verify the actual shipped commit exists before citing it. For each
      source doc: after flipping, re-check whether it now has 0 open todos remaining (checkbox AND prose-form — do not
      trust checkbox count alone). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos. **Done
      when**: all 25+ source-doc checkboxes/sections are flipped with verified evidence, and any doc that genuinely
      reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 4 conflict-gated + 12 operator-gated Deferred items from batch5's own doc**, now that
      time has passed and batch5's own todos have landed (some of which may resolve a Deferred item's blocker as a side
      effect — e.g. `sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`'s item C is explicitly gated on
      batch2_finalize's own re-check mechanism, which may have already run by the time this executes). For each of the
      16 Deferred items: re-read the specific conflicting/gating ground to check if it has since shipped, been ruled on
      by the operator, or otherwise cleared — if so, extract it as a new tracked todo in a follow-up `batch6` (do not
      draft it directly here, this finalize plan's own scope is reconciliation not fresh drafting); if still genuinely
      unresolved, leave it explicitly deferred (not speculative) — do not re-surface it as a fresh operator-decision
      entry a second time if already asked, just note the re-check happened and it's still awaiting an answer. **Done
      when**: each of the 16 Deferred items has either (a) a note that it's ready for `batch6` extraction because its
      blocker cleared, or (b) an explicit re-verified confirmation the conflict/decision is still open.
- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch5_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 16 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `sports_satellite_ao_dispatch_batch5_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
