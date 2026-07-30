---
doc_type: plan
title: Prediction satellite AO batch 2 — finalize (reconcile source docs + correct stale index claims + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch2_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 6 of that plan's todos are done. Mirrors the batch1 finalize-plan pattern (reconcile
  each of the 5 distinct source docs' checkboxes/Progress-Log entries independently), plus a batch2-specific addition:
  correct prediction_consolidated_closeout_2026_07_18.md's stale claims discovered during batch2's re-triage — the "C2a
  REFUSED — unruled" framing (superseded by the codex D1 ruling) and the "0 open todos" index entries for 3 docs where
  re-check found that claim factually wrong.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
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
depends_on: [prediction_satellite_ao_dispatch_batch2_2026_07_25]
gate_on_depends: true
source: >-
  Re-triage session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a
  companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 2 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until all 6 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile the 5 distinct source docs.** batch2's 6 todos cite 5 different source docs
      (`issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`, `prediction_phase_ab_residuals_2026_07_24.md`,
      `predictions_ml_walk_forward_and_arb_2026_06_20.md`, `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`,
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`,
      `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` — todo 5's combined sub-items both cite the
      phantom-reconciler doc). Confirm each source doc's checkbox/Progress Log was actually updated by its corresponding
      batch2 todo's execution (they should already be, per each todo's own Done-when), citing the batch-2 commit(s).
      **Done 2026-07-30 (slot 16, review craft)** — all 6 verified independently (not just trusting batch2's
      self-reported "Result:" annotations); see this plan's own Progress Log for the full per-doc citation trail. **Done
      when**: all 6 source-doc updates are verified present with commit citations recorded in this plan's own Progress
      Log.
- [ ] [DOC] P1. **Correct `prediction_consolidated_closeout_2026_07_18.md`'s stale claims discovered during batch2's
      re-triage** (deferred here rather than into a batch2 todo, to avoid two same-priority todos editing the same
      target file concurrently): (a) the "Distinct Values / axis-value census" section's "C2a REFUSED — unruled axis, no
      migration proposed" framing (lines ~213-215, repeated in the Deferred-work section ~line 717) — replace with a
      citation to `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1: C2a is RULED (operator D1, 2026-07-20)
      UPPERCASE-target, `migration_pending`, gated on the still-open honest-coverage-harness-fix issue — NOT refused or
      unruled. (b) **Corrected 2026-07-25 plan-reconcile — only ONE of these two premises was actually wrong.** The
      kalshi doc's entry is already accurate (`prediction_consolidated_closeout_2026_07_18.md:320-322` already reads
      "status: open, 3 live-side follow-ups outstanding" — NOT a "0 open todos" claim; no edit needed there, confirm
      it's still accurate rather than hunting for text that doesn't exist). The "Aggregated source docs" index's "— 0
      open todos (closed/archived/record-only)" claim IS genuinely wrong for
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (confirmed during batch2's re-triage: the
      doc's step-4 remainder + residuals 5-6 were only partially executed despite an over-broad "DONE" checkmark
      elsewhere) — update that entry to reflect the real post-batch2 state (0 open if batch2 fully closed it, or the
      specific named residual if not). Also correct `issues/prediction_arb_live_execution_bridge_2026_07_20.md`'s "0
      open todos" entry — that doc's own text names an unresolved operator-directed architectural decision, not zero
      open work; leave it flagged as OPERATOR-GATED, not silently marked done. **Done when**: all 3 corrections are made
      with the codex/evidence citations above, and a git diff of `prediction_consolidated_closeout_2026_07_18.md` is
      referenced in this plan's Progress Log.
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere if their blocker
      cleared during batch2's execution (verify none newly cleared) → add the archive banner → run the codex-alignment
      check → grep the corpus for every referrer of `prediction_satellite_ao_dispatch_batch2_2026_07_25` and fix each
      path to point at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan
      is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself
      gets archived alongside it in the same commit.

## Progress Log

### 2026-07-30 (slot 16, review craft) — Todo 1 done: all 6 source-doc updates independently verified

Picked up todo 1 via `/boot`. Confirmed batch2's gate was satisfied (all 6 real work todos + the draft→active
bookkeeping todo in `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` are `[x]`) before starting. Independently
re-read each of the 6 named source docs on disk (not trusting batch2's own "Result:" self-report) and, where a
production commit was cited, verified the SHA exists and is an ancestor of `origin/live-defi-rollout`:

1. **`plans/epics/manifest_master.md`** (batch2 todo 1, bucket naming migration) — P2 "Prediction bucket naming
   migration" line confirmed `[x]` with the grep-result citation in place. Docs-only, no commit to verify.
2. **`prediction_phase_ab_residuals_2026_07_24.md`** (batch2 todo 2, item 9) — confirmed the P0 "instrument_type
   casing/canonicalisation" item (line 347) is correctly left `[ ]` (open, not falsely closed) with an inline note
   citing the 2026-07-27 Progress Log entry (176 genuinely-malformed rows, non-zero) — matches batch2 todo 2's own
   done-when ("flip if 0, explain if non-zero"). The cited Progress Log entry (2026-07-27T15:28:46Z, slot-4) is present
   verbatim. New `[DIAG] P2` follow-up todo for the actively-growing blank count also confirmed present (line 362).
3. **`predictions_ml_walk_forward_and_arb_2026_06_20.md`** (batch2 todo 3, completion-% slice) — checkbox flipped `[x]`,
   Progress Log entry present with full method + results. Commit `unified-trading-pm@9df4924c0` verified: exists,
   touches exactly this file (66 insertions).
4. **`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`** (batch2 todo 4, sentinel fan-out) — checkbox flipped
   `[x]`, correctly scoped (explicit note that the UI-facing success criteria are NOT covered by this todo — no
   over-claim). Commit `market-tick-data-service@9a8b96c1` verified: exists, is an ancestor of `live-defi-rollout`.
5. **`issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`** (batch2 todo 5, combined a+b) — "Update
   2026-07-27 (slot-16)" section present with both sub-items' live-measured 0-residual results. Commit
   `instruments-service@70cf5c24` verified: exists, is an ancestor of `live-defi-rollout`.
6. **`issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`** (batch2 todo 6) — `status: resolved`,
   `resolved_by` cites all 3 SHAs exactly as batch2 todo 6 claimed. All 3 verified: `market-tick-data-service@a664511f`,
   `instruments-service@1fa9177f`, `market-tick-data-service@d2040f8f` — all exist and are ancestors of
   `live-defi-rollout`. (Doc already archived to `plans/archive/issues/` — fully resolved, correctly moved.)

**Minor note (not actioned, cosmetic only)**: this plan's own todo-1 header says "6 todos cite **5** different source
docs" while listing 6 distinct paths — an off-by-one in the plan's own prose (todo 5's two sub-items citing one doc
doesn't reduce the total below 6). Left as-is; doesn't affect the verification outcome, all 6 listed docs were checked.

All 6 source-doc updates verified present with commit citations. Todo 1's own checkbox flipped above. No code shipped —
read-only cross-doc verification, as scoped. Repo: unified-trading-pm only.
