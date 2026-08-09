---
doc_type: plan
title: Prediction satellite AO batch 4 — finalize (reconcile sibling source docs + resolve deferrals + archive)
summary: >-
  Finalize/gate plan for `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`. Runs ONLY after batch4's dispatched
  todos land (`gate_on_depends: true`): flips the corresponding checkboxes back in the 2 sibling source docs
  (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`),
  re-checks the gated `[OPERATOR]` walk/backfill deferrals for whether their gate cleared, and archives any sibling doc
  whose remaining work is fully closed. `status: draft` until batch4 itself is operator-approved and dispatched.
status: active
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
last_updated: "2026-07-30"
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
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Prediction satellite AO batch 4 — finalize

> **Status: draft — NOT dispatched.** Gated (`gate_on_depends: true`) behind
> `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`. It will not dispatch until batch4 is flipped `active` by the
> operator AND every batch4 dispatched todo is done. Do NOT flip this to `active` independently of batch4.

## Todos

- [x] ✅ [DATA] P1. **Reconcile the 2 sibling source docs' checkboxes to batch4's outcomes.** For each batch4 dispatched
      todo that shipped, flip the corresponding `- [ ]` in its `Source:` doc to `- [x] ✅ — <repo>@<sha>` with evidence:
      the P0 lifecycle item + (if its gate opened) the manifest-canonicalisation walk in
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md`; the MDPS depth-history retention verify + (if run) the
      `book_snapshot_5` re-backfill in `prediction_live_clob_depth_capture_2026_07_24.md`; the cqg recent-window
      re-enumeration in `prediction_cross_venue_arb_and_coverage_2026_07_24.md`. Repo: unified-trading-pm. **Done
      when**: every shipped batch4 todo has its source-doc checkbox flipped with a resolving `<repo>@<sha>` + evidence
      in the same commit; any NOT-shipped todo is left `- [ ]` with a dated note on why.

- [x] ✅ [DATA] P2. **Re-check the two gated `[OPERATOR]` deferrals now that todo #1 (lifecycle code) has landed.** With
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
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- swapped the generic epic ref for the
  archival-ritual codex SSOT (todo 3's target, finalize gate has no source-code target).
- **2026-08-07 (slot-16, data_engineering, task `…finalize-001`) — P1 reconcile DONE.** Flipped the source-doc
  checkboxes for every batch4 dispatched todo that shipped, in one commit `unified-trading-pm@bb48fc09e`:
  - `prediction_cross_venue_arb_and_coverage_2026_07_24.md` P0 lifecycle item → `[x] ✅` (batch4 P0 shipped
    `instruments-service@3617261f`; its struck legs (1)/(2)/KALSHI/taxonomy confirmed DONE; remaining leg (3) = the
    separate `[OPERATOR]` combined `_index` canonicalisation walk, permanent operator hard-stop 2026-07-28, NOT part of
    this checkbox). Its two NICE-TO-HAVE residual items (lowercase/blank/UNKNOWN venue rows + 1,454 v4→v9 rows) stay
    `- [ ]` with a dated note — they ride that operator-held walk.
  - `prediction_live_clob_depth_capture_2026_07_24.md` DEFERRED-CROSS-DEP `book_snapshot_5` re-backfill item → stays
    `- [ ]` with a dated note — NOT run: batch4's Deferred re-enum+backfill is still parked there (P0 gate has now
    cleared with the `instruments-service@3617261f` ship, but the item itself has NOT been dispatched/run). Recommended
    re-opening it as a ready `[DATA]` candidate in a future batch now that its P0 dependency has landed.
  - The MDPS depth-history retention verify (live_clob_depth doc) and the cqg recent-window re-enumeration (cross_venue
    doc) were ALREADY `[x] ✅` (flipped by the 2026-08-04 slot-5/slot-6 ships) — no change needed; confirmed in place.
  - Not-touched: the archived trades issue doc (`prediction_polymarket_legacy_dual_write_trees_metadata_loss_…`) — all
    its checkboxes were already `[x]`. Tree clean (rev-list 0), P1 checkbox flipped same commit. P2 (re-check the 2
    gated `[OPERATOR]` deferrals) + P3 (archival) remain for the follow-on dispatches.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (4 entries), unchanged — genuinely code-free
  finalize gate; the 4 plan/codex entries still cover the remaining P2/P3 work.
- **2026-08-07 (slot-11, data_engineering, task `…finalize-002`) — P2 re-check DONE.** Gate confirmed cleared:
  `instruments-service@3617261f` (batch4 P0, lifecycle-bounds code). Live counts re-measured 2026-08-07 from
  `_index/availability_index.parquet` (2,666,644 total rows; pyarrow column-pruned batched scan,
  market-tick-data-service venv): out-of-lifecycle POLYMARKET `empty_confirmed` = **38,020** (was ~49.6k, 2026-06-23);
  `SOURCE_RETURNED_ZERO` (all `empty_confirmed`) = **1,953,482** (was 93,264 — pipeline running since); lowercase
  `venue=kalshi` = **0** (was ~124 — cleaned); blank venue = **0** (was ~168 — cleaned); UNKNOWN venue = **0** (was ~21
  — cleaned); v4 schema rows = **0** (was 1,454 — POLYMARKET v9 re-walk completed). **Deferral (a)** — combined `_index`
  canonicalisation single-walk: gate cleared; legs (b)/(c) already resolved (0 rows) — source doc P2/P3
  (`cross_venue_arb`) flipped `[x] ✅` in this commit. Remaining: only leg (a) (38,020 out-of-lifecycle rows + 1,953,482
  `SOURCE_RETURNED_ZERO` out-of-lifecycle scope audit). Still a **permanent `[OPERATOR]` hard-stop** (workspace policy
  unchanged — manifest `--apply` reserved for human execution forever). Batch4 Deferred entry updated with fresh counts;
  filed as batch5 candidate. **Deferral (b)** — POLYMARKET re-enum + `book_snapshot_5` backfill: gate cleared; re-tagged
  off `[OPERATOR]` 2026-07-28; **promoted to ready `[DATA]` candidate** — batch5 or standalone plan, AO-dispatchable, no
  remaining gates. Batch4 Deferred entry updated.

## Deferred work — migrated to:

- **Deferral (b)** (POLYMARKET re-enum + `book_snapshot_5` backfill, `DEFERRED-CROSS-DEP` on
  `prediction_live_clob_depth_capture_2026_07_24.md`'s own checkbox) — migrated to:
  `plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1, drafted 2026-08-09 (2026-08-09,
  ag_closeout_auditor).
