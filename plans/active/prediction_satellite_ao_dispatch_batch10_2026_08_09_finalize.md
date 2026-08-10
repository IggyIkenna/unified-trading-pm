---
doc_type: plan
title: Prediction satellite AO batch 10 — finalize (reconcile 4 source docs + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch10_2026_08_09.md — machine-held via depends_on +
  gate_on_depends: true until all 4 of that plan's todos are done. Reconciles each of the 4 source docs' own checkboxes
  (prediction_live_clob_depth_capture_2026_07_24.md, prediction_capture_incident_remediation_2026_07_06.md,
  issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
  issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md), then archives batch10 via the standard
  6-step ritual. Authored `status: active` (not draft) per the skill's no-double-gate finding — `gate_on_depends: true`
  already machine-holds every task here until batch10's own todos are done, regardless of batch10's own draft/active
  status, so a second manual flip on this plan would be a redundant gate.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-10, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
    /plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
depends_on: [prediction_satellite_ao_dispatch_batch10_2026_08_09]
gate_on_depends: true
source: >-
  Scheduled /ag-closeout-audit prediction run 2026-08-09, per task_template.md §4's finalize-plan-coverage rule.
assigned_role: data_engineering
effort: medium
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 10 — finalize

**status: active — gated on batch10's 4 todos via `depends_on` + `gate_on_depends: true`.**

## Todos

- [ ] [REVIEW] P1. **Reconcile `prediction_live_clob_depth_capture_2026_07_24.md`**: confirm its "DEFERRED-CROSS-DEP"
      checkbox (`book_snapshot_5` batch row-proof) is flipped `[x]` with batch10 todo 1's commit/evidence citation.
      Repo: unified-trading-pm. Done when: the checkbox is closed-by-citation, no orphaned "still looks open" gap.
- [ ] [REVIEW] P1. **Reconcile `prediction_capture_incident_remediation_2026_07_06.md`**: confirm Phase 6's second
      checkbox (historical Kalshi `OTHER`-bucket reclassify) is flipped `[x]` with batch10 todo 2's backup location +
      post-patch distribution-check evidence. Repo: unified-trading-pm. Done when: the checkbox is closed-by-citation
      and the backup location is recorded in this doc's own Progress Log for future auditability.
- [ ] [REVIEW] P1. **Reconcile the 2 dead-code issue docs**
      (`issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md`,
      `issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`): confirm each sole todo is flipped
      `[x]` with batch10 todo 3/4's commit SHA, and that `quality-gates.sh` was reported green for both deletions. Repo:
      unified-trading-pm. Done when: both checkboxes are closed-by-citation.
- [ ] [DOC] P2. **Re-check the 4 Deferred (not-extracted) items** from batch10's own Deferred section — in particular
      whether `data_completion_prediction_2026_07_15.md`'s Phase-B migration has finally gotten its own dedicated plan
      (now 6 audit passes deep without one), and whether `sports_master:Group E` has cleared for
      `predictions_ml_walk_forward_and_arb_2026_06_20.md`. Repo: unified-trading-pm. Done when: an explicit still-held /
      cleared verdict is recorded for each of the 4.
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch10_2026_08_09.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): confirm the prior 4 todos' verdicts are
      recorded, add the archived-banner cross-reference, run the post-phase codex audit, confirm no new CLAUDE.md
      contract is owed, update every corpus referrer, `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm.
      Done when: batch10 is at its archived path with every referrer updated and this finalize plan's own todos all
      `[x]`.

## Progress Log

- 2026-08-09 (ag_closeout_auditor, slot 14, dispatch agt-465129): drafted alongside batch10, `status: active`, gated via
  `depends_on` + `gate_on_depends: true`. No work started — waiting on the operator to approve + flip batch10 to
  `active`, then on its dispatch + completion.

## Deferred work — migrated to:

- N/A — the `DEFERRED-CROSS-DEP` token above (todo 1) is a citation of
  `prediction_live_clob_depth_capture_2026_07_24.md`'s own deferred checkbox, not a deferral owned by this doc; this
  plan's own todo tracks reconciling that item, not deferring further work. See that doc's own Deferred section for the
  live tracking.
