---
doc_type: plan
title: Prediction satellite AO batch 6 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch6_2026_07_29.md — `gate_on_depends: true` machine-holds this
  finalize's tasks until that plan's todos are done (authored `status: active` per the 2026-07-30 no-double-gate ruling;
  caveat: the known `gate_on_depends` wiring gap tracked in
  plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md once released a task early, so
  re-verify source-doc statuses before acting). Mirrors the batch4-finalize pattern (reconcile each of the 9 distinct
  source docs' checkboxes/Progress-Log entries independently, re-check the deferred/excluded population for cleared
  gates, then archive).
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-30"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch6_2026_07_29]
gate_on_depends: true
source: >-
  Drafted alongside prediction_satellite_ao_dispatch_batch6_2026_07_29.md, per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Prediction satellite AO batch 6 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until all of that plan's todos are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last. **Caveat**: the
> `gate_on_depends` wiring gap (see Progress Log below;
> `plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`) once released a task early —
> re-verify batch6's own todo statuses before starting; do not trust the gate alone.

## Todos

- [ ] [REVIEW] P1. **Reconcile the 9 distinct source docs.** batch6's 13 todos cite 9 source docs
      (`prediction_capture_incident_remediation_2026_07_06.md`,
      `issues/prediction_arb_live_execution_bridge_2026_07_20.md`,
      `/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
      `/plans/archive/2026_08/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`,
      `issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md`,
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (3 todos cite this one),
      `prediction_live_clob_depth_capture_2026_07_24.md` (2 todos cite this one),
      `predictions_ml_walk_forward_and_arb_2026_06_20.md`, `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`).
      Confirm each source doc's checkbox/Progress Log was actually updated by its corresponding batch6 todo's execution
      (per each todo's own Done-when), citing the batch-6 commit(s). Also confirm the
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` fixture-pairing + politics/geo todos' completion is
      reflected back into `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s "RULED 2026-07-28" section (a
      one-line "shipped, see batch6" note), since that section is where the ruling — but not the build — currently
      lives. **Done when**: all 9 source-doc updates (11 checkbox sites total) are verified present with commit
      citations recorded in this plan's own Progress Log, and batch4's RULED section is updated.

- [ ] [DOC] P2. **Re-check the Deferred/excluded population for cleared gates.** batch6 excluded 11 docs across 6
      categories (self-dispatching, claimed-elsewhere, too-large, not-AO-eligible, sports-owned, housekeeping). Since
      time will have passed by the point this finalize runs, re-check each: (a) did
      `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` and
      `features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`'s self-dispatched items
      actually get picked up and closed via the direct backlog scan (confirm, don't just assume); (b) did
      `code_quick_cross_repo_fix_backlog_2026_07_28.md` ship the `prediction_cqg_residual_2026_07_24.md` MTDS dead-code
      cleanup it claimed; (c) has `data_completion_prediction_2026_07_15.md`'s Phase-B migration gotten a dedicated plan
      yet (if so, link it from the consolidated-closeout's Deferred section instead of leaving a bare "needs its own
      plan" note); (d) did the `ao`-tranche's own closeout audit pick up
      `prediction_trades_migration_concurrent_dispatch_2026_07_28.md`'s dispatcher-checkpoint design question; (e) did
      the sports tranche's own `/ag-closeout-audit sports` sibling run (dispatched the same wave as this run,
      2026-07-29) claim the 4 sports-owned docs + `gcs_path_resolution_centralization_audit_sports_prediction` flagged
      in batch6's Deferred section — if any gate cleared, note it here rather than leaving batch6's Deferred section
      stale (mirrors `prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`'s equivalent todo 2 pattern). Also
      verify `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`'s own finalize
      (`prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`) has been dispatched + completed by now — if
      not, re-flag it to the operator (it was fully unblocked, 7/7 done, as of this batch's own drafting). **Done
      when**: each of the 5 lettered checks above has a recorded verdict (cleared / still-open) in this plan's Progress
      Log.

- [ ] [DOC] P3. **Archive `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere if their blocker
      cleared during batch6's execution (per todo 2's re-check above) → add the archive banner → run the codex-alignment
      check → grep the corpus for every referrer of `prediction_satellite_ao_dispatch_batch6_2026_07_29` and fix each
      path to point at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan
      is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself
      gets archived alongside it in the same commit.

## Progress Log

- 2026-07-29 (slot 14, ag_closeout_auditor): drafted alongside batch6, `status: draft`, gated on batch6's 13 todos.
- 2026-07-30 (slot 7, worker on `assigned_role: review`, dispatch `...finalize-001`): **HOLDING OFF — todo 1 was
  dispatched prematurely.** Before starting the reconciliation, verified batch6's actual completion state: only 3/14
  todos are `done` (001 CQG fix, 002 EventTransport bridge, 004 VM launch-only) — 11 are still `queued` (003, 005-014,
  including the P1 VM-completion VERIFY, credential reshape, and several P2 backend/data items). The gate
  (`depends_on` + `gate_on_depends: true`) should have withheld this todo until all of batch6 is done, per this plan's
  own header — confirmed via `GET /api/backlog/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize-001/blockers`
  → `"ready (no blockers)"`, i.e. the gate never actually wired. **This is the same recurring dispatcher bug already
  tracked in `plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`** (10+ prior bounces
  across ≥6 distinct plan pairs, root-cause fix already P0 and in flight per that doc's Progress Log) — added this as a
  new recurrence there rather than filing a duplicate (my first attempt at a fresh issue doc duplicated it and was
  reverted). **Not flipping this todo's checkbox** — most of the 9 source docs genuinely have NOT been touched by batch6
  yet, so "all 9 verified present" is false today. Skipped the task back to the queue (slot 7) rather than ship a
  false-progress flip. Whoever picks this up next: re-check batch6's own todo statuses first — do not repeat this
  reconciliation until it reads 14/14 `done` (or re-verify the gate_on_depends fix has landed and genuinely holds).
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- added the gate_on_depends wiring-gap tracking doc
  (this plan's own Progress Log names it as the root cause the gate never held -- load-bearing, not previously scoped) +
  the batch4-finalize sibling this plan's pattern mirrors.
