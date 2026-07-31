---
doc_type: plan
title: Prediction satellite AO batch 1 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 7 of that plan's todos are done. Mirrors the sports/tradfi finalize-plan pattern
  (reconcile each of the 4 distinct source docs' checkboxes/Progress-Log entries independently), plus a batch1-specific
  addition: re-check the excluded item 9 and the 12 fully-deferred docs once the operator has ruled on the queued
  decision in autonomous_session_operator_decisions_2026_07_25.md.
status: complete
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25" # same-day correction (consolidated-closeout split pass): corrected stale "11 open total" phase_ab_residuals citation to 13 (that doc gained 2 relocated todos from the parent, untriaged by batch1)
parent_epic: predictions_master
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
depends_on: [prediction_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 1 — finalize

> **🟢 ARCHIVED 2026-07-30.** All 3 todos done: source-doc reconciliation (todo 1), the item-9 + 12-doc Deferred
> re-check (todo 2), and this archival (todo 3) — parent moved to
> `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md`, corpus referrers updated. No new
> durable contract from this batch — codex-alignment check: nothing to update.
>
> **Machine-gated on `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until all 7 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-13).** **Reconcile the source doc(s).**
      `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`'s 7 todos all cite
      `prediction_phase_ab_residuals_2026_07_24.md` as Source, but each todo's own Done-when records results into a
      DIFFERENT sibling doc's Progress Log (`prediction_capture_incident_remediation_2026_07_06.md`,
      `/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
      `issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`, plus
      `prediction_phase_ab_residuals_2026_07_24.md` itself for todo 7). Flip the corresponding checkbox in
      `prediction_phase_ab_residuals_2026_07_24.md` for each of the 7 items (they should already be cross-referenced via
      the target docs' Progress Log entries written by each todo's own execution), citing the batch-1 commit(s).
      Re-check whether `prediction_phase_ab_residuals_2026_07_24.md` now has 0 open todos remaining (unlikely — batch1
      was a partial extraction of 9 AO-eligible items out of the doc's total **as it stood pre-relocation (11)**;
      **corrected 2026-07-25 (same-day consolidated-closeout split pass, AFTER batch1 was drafted)**: that doc's open
      total is now 13, +2 relocated in from the parent's former "Queued audits + reviews" section (an adapter dead-code
      audit + a merged reconciliation-cadence todo) that batch1's triage never saw and does NOT cover — re-verify the
      exact count live rather than trusting either historical figure, and do not assume those 2 newer items are batch1's
      concern; they are untriaged, not blocked). **Done when**: `prediction_phase_ab_residuals_2026_07_24.md`'s 7
      corresponding checkboxes are flipped with verified evidence, and each of the 3 sibling target docs' Progress Log
      entries are confirmed present. — **Result**: all 3 sibling docs' Progress Log entries + own checkboxes were
      already correctly flipped by batch1's own execution (confirmed by direct read); the gap was purely that
      `prediction_phase_ab_residuals_2026_07_24.md`'s own checkbox list had never cited any of batch1's 7 commit SHAs.
      Flipped 4 of that doc's checkboxes to DONE: A1b (dead Kalshi host, `e2e-testing@371ac1b`), A2a (canonical-identity
      migration now 8/8, cron-already-covers-it verdict), A2b (route writer through canonical builder, 3 commits), A2c
      (POLYMARKET legacy dual-write trees, diagnostic + batch4's separate schema work — issue doc now
      resolved/archived). A1a (capture-incident remediation) stays open — annotated with todo 2's diagnostic + todo 3's
      Phase 5 guardrail closure, but that doc's own Phase 6 fix is still unimplemented. Also flipped Phase 5's
      write-time `*-PERP` guardrail checkbox directly in `prediction_capture_incident_remediation_2026_07_06.md` (it was
      shipped 2026-07-27 via batch1 todo 3 but never cited there) and struck through a stale prose "suggested next step"
      in `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md` that batch1 todo 1 already resolved.
      **Re-verified live** (not trusting historical counts): `prediction_phase_ab_residuals_2026_07_24.md` now has **9
      open / 10 done / 19 total** — 0 open is NOT the outcome, as predicted; the 9 remaining are genuinely outside
      batch1's scope (A1a, A1c reconciled by a different batch, A5, and 6 Phase-B items including the excluded item 9).
      No code changed — doc-only reconciliation across 3 files.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-13, review craft).** **Re-check the excluded item 9 and the 12
      fully-deferred docs**, now that the operator has (presumably) ruled on the queued decision in
      `autonomous_session_operator_decisions_2026_07_25.md`. For item 9 (the instrument_type-canonicalization re-verify
      excluded from batch1 for conflicting with `prediction_consolidated_closeout_2026_07_18.md`'s own
      casing-gap-to-100% item): check if that master-plan item has since shipped — if so, item 9 becomes conflict-free,
      extract it into a new tracked todo. For each of the 12 fully-deferred docs listed in batch1's own Deferred
      section: spot-check whether any conflict has cleared or any doc has reached genuine archivability since. If
      either, extract new tracked todo/plan(s). If not, leave explicitly deferred. **Done when**: item 9's status is
      re-verified (dispatched or confirmed still gated), and each of the 12 deferred docs has an explicit current-state
      note (still gated / newly dispatchable, with a new todo/plan created if so). — **Result**: found this exact
      re-check had ALREADY happened, one level removed — `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`'s own
      "Re-check status (2026-07-25)" banner records that a subsequent `/ag-closeout-audit` re-triage pass already
      re-checked item 9 + all 12 deferred docs against current content and extracted
      `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` (since executed to completion, all 6 todos + wrapper
      `[x]`). This todo's job became: independently re-verify batch2's re-check is still accurate TODAY (2026-07-30),
      not stale, given 3+ more days and 4 further batches (batch3-6) have since landed. **Item 9**: batch2 todo 2
      (2026-07-27) re-ran the case-insensitive live read the C2a ruling mandates and found 176 genuinely-malformed
      (non-casing) rows — non-zero, so item 9 stayed correctly `[ ]` (explained, not falsely closed) in
      `prediction_phase_ab_residuals_2026_07_24.md`, with a new `[DIAG] P2` follow-up todo filed for the
      actively-growing blank-row writer defect (30→70→100 rows, ~10/day). **Re-verified live today**: both lines are
      still open, unchanged, in the current doc (9 open / 10 done total, matching this same plan's todo-1 citation) —
      item 9 is CONFIRMED STILL GATED, not silently dropped (the P2 follow-up is itself a real tracked, open todo).
      **The 12 deferred docs** — batch2's own Deferred section (and Progress Log) already gives each an explicit
      current-state note; independently re-verified today, none are stale: (1-2) `prediction_phase_ab_residuals` items
      1-3/5/7 + `prediction_lifecycle_prefetch_gate_and_resolution_day_     catalogue_2026_07_14.md` —
      DUPLICATE-OF-BATCH1, unchanged. (3) `data_completion_prediction_2026_07_15.md` — still `status: active`, 0
      AO-eligible, its 21 human-only items + 3 conflicts unchanged — OPERATOR-GATED, unchanged. (4)
      `issues/prediction_arb_live_execution_bridge_2026_07_20.md` — its design blocker was RULED 2026-07-28 (UTL
      `EventTransport` facade, no operator decision remains) and is now `[BACKEND]`-tagged, no longer `[OPERATOR]` — but
      this NEWLY-CLEARED state is already captured downstream: its build todo is already extracted + dispatched as
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s own todo (line 130, `status: active`) — no new todo
      needed from this pass, would be a duplicate. (5-7) `prediction_phase_c_data_status_ui_2026_07_24.md` /
      `_phase_d_formal_smoke_and_backfill_2026_07_24.md` / `_phase_e_football_arb_live_2026_07_24.md` — still 0
      AO-eligible each, still machine-gated on `prediction_phase_ab_residuals`'s 9 open items (re-verified count
      unchanged today) — unchanged. (8)
      `issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` — CONFIRMED fully resolved +
      archived (now at `plans/archive/issues/`); its 2 AO-eligible candidates were duplicate-of-batch1 (todo 5), its own
      operator-gated `prediction_trades`-axis question folded into `prediction_phase_ab_residuals`'s A2 todo. (9)
      `predictions_ml_walk_forward_and_arb_2026_06_20.md` — its 1 AO-eligible item already shipped via batch2 todo 3; no
      remaining AO-eligible content. (10) `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` — its 1 AO-eligible
      item (sentinel fan-out) already shipped via batch2 todo 4; re-checked its other 2 open items directly: the
      `[VERIFY][UI]` re-walk (line 106) remains genuinely blocked by `[BLOCKED-PLAYWRIGHT]` (fleet VM has no dev server)
      — unchanged, not this doc's sentinel-fan-out dependency as batch2's Deferred note implied; the Phase 5
      canonical-groups backfill (line 127, ~24 remaining groups) was never flagged AO-eligible by the original 13-agent
      triage and stays that way — not re-litigated here (that would be re-running triage, out of this todo's scope).
      (11) `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` — CONFIRMED fully resolved + archived
      (now at `plans/archive/issues/`, `status: resolved`, all 3 SHAs verified live-defi-rollout ancestors) via batch2
      todo 6. No conflict/doc newly cleared beyond what batch2 already captured, except item (4) above — and that
      clearance is already correctly absorbed into `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`, so no new
      todo/plan is created by this pass (one would duplicate existing dispatched work). No code changed — doc-only
      re-verification across the cited docs, all read live, no historical snapshot re-cited as current.
- [x] ✅ [DOC] P1. **DONE 2026-07-30 (slot-4).** **Archive `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`** via
      the standard 6-step ritual (per CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked
      todo elsewhere (todo 2 above should have already resolved what it could — verify none remain unaddressed) → add
      the archive banner → run the codex-alignment check → grep the corpus for every referrer of
      `prediction_satellite_ao_dispatch_batch1_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). — **Result**: Deferred-item migration — none needed; todo 2's own
      re-verification already confirmed every Deferred item has a home elsewhere (6 of 12 executed via batch2, 1
      absorbed into batch6's dispatched todo, the rest genuinely still tracked/gated in their own source docs). Archive
      banners added to both this doc and the parent, `status` flipped `active` → `complete` on both. Codex-alignment
      check: this plan's own "Codex SSOTs" section already states no new durable contract — confirmed, nothing to update
      (every todo executed an already-decided spec from its source doc). Corpus referrers fixed (path-shaped
      `related:`/link references only — bare-filename prose citations of what happened are left as historical narrative,
      per the sports/tradfi precedent): `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` (2 refs),
      `prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`,
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`, `defi_satellite_ao_dispatch_batch1_2026_07_25.md`,
      `prediction_consolidated_closeout_2026_07_18.md`, `prediction_consolidated_native_ao_extract_2026_07_25.md`,
      `issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md`. `plans/active/INDEX.md` is
      auto-generated (`scripts/plans/regenerate_active_plan_index.py`) — regenerated rather than hand-edited. Already-
      archived docs referencing the old path (`prediction_satellite_ao_dispatch_batch3_2026_07_26.md`,
      `active_plan_inventory_dashboard_2026_07_24.md`,
      `issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`) are historical narrative
      snapshots, correctly left as-is. `/codex/02-data/non-canonical-path-inventory.md`'s citation is a provenance note
      for a fact already stated in that same codex table cell, not a bare path — left as-is. `locked_by` was already
      empty on both docs. Both moved to `plans/archive/2026_07/` in the same commit. **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
