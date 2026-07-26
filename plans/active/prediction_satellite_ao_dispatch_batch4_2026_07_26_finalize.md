---
doc_type: plan
title: Prediction satellite AO batch 4 — finalize (reconcile sibling source docs + resolve deferrals + archive)
summary: >-
  Finalize/gate plan for `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`. Runs ONLY after batch4's dispatched
  todos land (`gate_on_depends: true`): flips the corresponding checkboxes back in the 2 sibling source docs
  (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`),
  re-checks the gated `[OPERATOR]` walk/backfill deferrals for whether their gate cleared, and archives any sibling doc
  whose remaining work is fully closed. `status: draft` until batch4 itself is operator-approved and dispatched.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch4_2026_07_26]
gate_on_depends: true
source: >-
  Paired finalize for prediction_satellite_ao_dispatch_batch4_2026_07_26 per task_template.md §4 finalize-plan-coverage
  rule; drafted by the /ag-closeout-audit prediction scheduled run 2026-07-26 (ag_closeout_auditor, slot 7).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 4 — finalize

> **Status: draft — NOT dispatched.** Gated (`gate_on_depends: true`) behind
> `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`. It will not dispatch until batch4 is flipped `active` by the
> operator AND every batch4 dispatched todo is done. Do NOT flip this to `active` independently of batch4.

## Todos

- [ ] [DATA] P1. **Reconcile the 2 sibling source docs' checkboxes to batch4's outcomes.** For each batch4 dispatched
      todo that shipped, flip the corresponding `- [ ]` in its `Source:` doc to `- [x] ✅ — <repo>@<sha>` with evidence:
      the P0 lifecycle item + (if its gate opened) the manifest-canonicalisation walk in
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md`; the MDPS depth-history retention verify + (if run) the
      `book_snapshot_5` re-backfill in `prediction_live_clob_depth_capture_2026_07_24.md`; the cqg recent-window
      re-enumeration in `prediction_cross_venue_arb_and_coverage_2026_07_24.md`. Repo: unified-trading-pm. **Done
      when**: every shipped batch4 todo has its source-doc checkbox flipped with a resolving `<repo>@<sha>` + evidence
      in the same commit; any NOT-shipped todo is left `- [ ]` with a dated note on why.

- [ ] [DATA] P2. **Re-check the two gated `[OPERATOR]` deferrals now that todo #1 (lifecycle code) has landed.** With
      the lifecycle bounds populated, (a) confirm the combined prediction `_index` manifest canonicalisation single-walk
      is now unblocked (gate on #1 cleared) and re-file it as a ready `[OPERATOR]` item (or a batch5 candidate) with the
      current out-of-lifecycle-empty / lowercase-venue / v4-tail counts re-measured live; (b) same for the POLYMARKET
      re-enum + `book_snapshot_5` backfill. Repo: unified-trading-pm. **Done when**: each of the 2 gated deferrals is
      either promoted to a ready `[OPERATOR]` todo (with re-measured live counts) or left deferred with a dated reason;
      recorded in this plan's Progress Log.

- [ ] [DATA] P3. **Archive fully-closed sibling docs + update the closeout digest.** For each of the 3 A3-relocated
      sibling docs (`prediction_cross_venue_arb_and_coverage`, `prediction_live_clob_depth_capture`,
      `prediction_perps_kalshi_polymarket_parked`): if every open item is now either shipped, promoted to a live
      `[OPERATOR]`/batch todo, or a confirmed non-batchable (upstream/design/operator) residual, run the 6-step archival
      ritual and move it to `plans/archive/2026_07/`; otherwise leave it active with the residual clearly scoped. Update
      `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs" digest to reflect any archival. Repo:
      unified-trading-pm. **Done when**: each sibling doc is either archived (with the ritual completed + digest
      updated) or has a one-line dated residual note explaining why it stays active; no sibling doc is left in a
      half-reconciled state.

## Progress Log

- 2026-07-26 (slot 7, ag_closeout_auditor): drafted as the paired finalize for
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`. Inert (`status: draft`, gated on batch4) until the operator
  approves + dispatches batch4.
