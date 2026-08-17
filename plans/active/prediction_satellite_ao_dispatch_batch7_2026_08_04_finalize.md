---
doc_type: plan
title: Prediction satellite AO batch 7 — finalize (reconcile source doc + re-check deferrals + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch7_2026_08_04.md — machine-held via depends_on +
  gate_on_depends: true until that plan's one todo is done. Mirrors the batch4/batch6-finalize pattern (reconcile the
  source doc's checkbox/Progress-Log entry, re-check the deferred/excluded population for cleared gates, then archive).
  Authored `status: active` (not draft) per the 2026-07-30 no-double-gate finding — `gate_on_depends` alone already
  machine-holds every task here until batch7's own todo lands, regardless of batch7's own draft/active status; a
  finalize plan carries no independent judgment call.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-7, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch7_2026_08_04]
gate_on_depends: true
source: >-
  Drafted alongside prediction_satellite_ao_dispatch_batch7_2026_08_04.md, per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Prediction satellite AO batch 7 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch7_2026_08_04.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until that plan's one task is `done`. `sequential: true` because todo 2
> (archival) must run after todo 1 (reconciliation).

## Todos

- [x] ✅ [REVIEW] P3. **Reconcile the source doc.** batch7's one todo cites
      `archive/2026_08/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`. Confirm that doc's own remaining
      todo (the downstream-consumer check) was actually updated with batch7's verdict + commit citation, per batch7's
      own Done-when clause. If the verdict was "no real consumer exists", confirm the source doc's checkbox is flipped
      and its `status` is updated toward `resolved` (0 open todos). If the verdict was "a real consumer exists", confirm
      a follow-up todo/plan was filed for the separately-scoped backfill (not left as a dangling prose note). **Done
      when**: the reconciliation is recorded in this plan's own Progress Log with the exact commit citation. — verified
      by plan_reconciler agt-2934ac 2026-08-17: source doc's checkbox is `[x]`, `status: resolved`, 0 open todos,
      banner "🟢 ARCHIVED 2026-08-16" — `unified-trading-pm@e3ca863b9d`.

- [ ] [DOC] P3. **Archive batch7 + this finalize plan.** Once the source doc is confirmed reconciled and batch7's one
      todo + this plan's todo 1 are both done, archive both `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` and
      this finalize doc to `plans/archive/2026_08/` per the 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — update every referrer (this doc's own
      `related:`, `prediction_consolidated_closeout_2026_07_18.md`'s aggregated-sources index if it names batch7,
      `ag_closeout_audit_prediction_parked_2026_08_04.md`'s `related:`). **Done when**: both files are in
      `plans/archive/2026_08/`, `regenerate_active_plan_inventory.py` shows 0 orphaned referrers, and
      `check_ag_closeout_linkage.py --tranche prediction` is still green.

      **STILL OPEN 2026-08-17 (plan_reconciler)** — todo 1 above is now done, clearing the content-side blocker, but
      the referrer-fix step cannot safely run this pass: `plans/epics/predictions_master.md` (the one REAL active
      referrer — the hub `prediction_consolidated_closeout_2026_07_18.md` does NOT cite batch7, verified via grep) was
      edited 8h ago, inside the 12h grace window. `ag_closeout_audit_prediction_parked_2026_08_04.md` is itself
      already archived (historical citation, not fixed per this corpus's "resolved issue doc describing history"
      exclusion); `plans/active/INDEX.md` is auto-regenerated, never hand-fixed. Next session: once
      `predictions_master.md` clears grace, `git mv` both files to `plans/archive/2026_08/`, update the epic's 4
      batch7 citation lines (2 `related_plans:` entries around line 47-48 + 2 body header links around line
      1021-1025), then flip this checkbox.

## Progress Log

- 2026-08-04 (slot 11, ag_closeout_auditor, dispatch agt-a7e099): drafted alongside batch7, per the finalize-plan-
  coverage rule. `status: active` from the start (not draft) — `gate_on_depends: true` already fully holds both todos
  above until batch7's own todo is `done`, so no second manual flip is needed later (2026-07-30 no-double-gate finding,
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`).
- **context-scout 2026-08-06**: populated context_scope (3 entries).
