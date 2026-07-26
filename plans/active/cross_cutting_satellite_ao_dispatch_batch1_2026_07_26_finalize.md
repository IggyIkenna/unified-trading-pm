---
doc_type: plan
title: Cross-cutting satellite AO batch 1 — finalize (reconcile source docs + resolve deferrals + archive both parts)
summary: >-
  Gated closeout for cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md AND its sibling
  cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md — machine-held via depends_on + gate_on_depends: true until
  all 31 todos across both parts are done. Reconciles each distinct source doc's checkboxes independently, then
  re-checks the Deferred conflict-gated/operator-gated/time-gated items (4/13/2) plus the 7 mistags and 2 archivable_now
  docs found during Phase 0/1, then archives both batch docs via the standard 6-step ritual.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26, cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan; this one gates on BOTH halves of the split batch.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 1 — finalize

> **Machine-gated on BOTH `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (16 todos) AND
> `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (15 todos)** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 31 tasks across both parts are `done`. `sequential: true`
> because todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all distinct source docs' checkboxes across both batch parts.** For each of the 31
      now-done todos (across batch1 + batch1b): flip the corresponding checkbox/section in its named source doc (each
      todo's text ends with "Source: `<doc>.md`"), citing the batch commit(s) that shipped it — verify the actual
      shipped commit exists before citing it. For each source doc: after flipping, re-check whether it now has 0 open
      todos remaining (checkbox AND prose-form). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open
      todos. **Done when**: all 31 source-doc checkboxes/sections are flipped with verified evidence.
- [ ] [REVIEW] P1. **Re-check the 4 conflict-gated + 13 operator-gated + 2 time-gated Deferred items** (all in
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred sections — batch1b defers to that same
      doc, not a duplicate), now that time has passed and batch1/1b's own todos have landed. For each of the 19 Deferred
      items: re-read the specific gating ground to check if it has since cleared — if so, extract it as a new tracked
      todo in a follow-up `batch2`; if still genuinely unresolved, leave it explicitly deferred, do not re-surface an
      already-asked operator question a second time. **Done when**: each of the 19 Deferred items has either (a) a note
      that it's ready for `batch2` extraction, or (b) an explicit re-verified confirmation the gate is still open.
- [ ] [DOC] P2. **Action the 7 mistags + 2 archivable_now docs found during Phase 0/1.** (1) Retag the 2 genuinely
      single-AG docs (`plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` → `[defi]`,
      `plans/active/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` → `[cefi]`) and the 5 genuinely
      infra-scoped docs (`plans/active/bucket_fold_ml_2026_07_17.md`,
      `plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md`,
      `plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md`,
      `plans/active/issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md`,
      `plans/active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_26.md` → `[infra]` or fold into
      `infra_consolidated_closeout_2026_07_25.md`'s Sources list per that doc's own convention) — read each doc's real
      content first to confirm before retagging (do not blind-apply), then re-run
      `scripts/plan-hygiene/check_ag_closeout_linkage.py` after each retag. (2) Archive
      `plans/active/bucket_estate_fold_design_2026_07_13.md` and
      `plans/active/issues/gcs_data_access_audit_log_cost_2026_07_24.md` (both `archivable_now`) via the standard 6-step
      ritual. **Done when**: all 7 retags are applied with `check_ag_closeout_linkage.py` passing 0 new orphans, and
      both archivable_now docs are moved to `plans/archive/2026_07/` with every corpus referrer fixed.
- [ ] [DOC] P1. **Archive both `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` and
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`** via the standard 6-step ritual (per CLAUDE.md's
      plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above should have
      already resolved or re-confirmed all 19 — verify none silently vanish) → add the archive banner to both → run the
      codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for every
      referrer of either doc and fix each path to point at the archived location → clear `locked_by` (already empty on
      both, confirm). **Done when**: both plans are moved to `plans/archive/2026_07/`, every corpus referrer resolves to
      the new path, and this finalize doc itself gets archived alongside them in the same commit.
