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
status: complete
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
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
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

> **🟢 ARCHIVED 2026-07-30.** All 3 todos done: source-doc reconciliation (todo 1), correcting
> `prediction_consolidated_closeout_2026_07_18.md`'s stale claims (todo 2), and this archival (todo 3) — parent moved to
> `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch2_2026_07_25.md`, corpus referrers updated. No new
> durable contract from this batch — codex-alignment check: nothing to update.
>
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
- [x] ✅ [DOC] P1. **Correct `prediction_consolidated_closeout_2026_07_18.md`'s stale claims discovered during batch2's
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
- [x] ✅ [DOC] P1. **DONE 2026-07-30 (slot-2, backend_engineer craft).** **Archive
      `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`** via the standard 6-step ritual (per CLAUDE.md's
      plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere if their blocker cleared
      during batch2's execution (verify none newly cleared) → add the archive banner → run the codex-alignment check →
      grep the corpus for every referrer of `prediction_satellite_ao_dispatch_batch2_2026_07_25` and fix each path to
      point at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved
      to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.

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

### 2026-07-30 (slot 8, data_engineering craft) — Todo 2 done: `prediction_consolidated_closeout_2026_07_18.md` corrected

Picked up todo 2 via `/boot`. All 3 corrections made, each re-verified against live doc state (not blindly copying this
finalize-plan's 2026-07-25 framing, since one item had since moved on further):

(a) **C2a framing (2 occurrences, lines ~232 and ~571)** — replaced "**C2a REFUSED** — unruled axis, no migration
proposed" / "C2a-REFUSED lowercase tail (no migration proposed)" with a citation to
`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1: C2a is RULED UPPERCASE-target (operator D1, 2026-07-20),
`migration_pending`, compared case-insensitively (no casing finding emitted during the migration_pending window). Also
noted the harness case-robustness gate
(`honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`) is itself `status: resolved`
(verified via grep on the archived doc) — so the finalize-plan's "gated on the still-open honest-coverage-harness-fix
issue" framing was itself already stale; did not carry that stale detail forward.

(b) **Kalshi doc entry (`kalshi_live_capture_regression_and_drift_2026_07_13.md`, line 345)** — confirmed already
accurate ("status: open, 3 live-side follow-ups outstanding") — no edit made, per this todo's own note.

(c) **`prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`'s "0 open todos" entry** — confirmed genuinely
wrong: read the doc, found `status: open` at the frontmatter and one real open `- [ ] [DATA] P2.` todo (the KALSHI-venue
scaffold-row provenance mislabel, 129,227 rows). Corrected the index entry to "1 open" with the todo summarized inline.

(d) **`prediction_arb_live_execution_bridge_2026_07_20.md`'s "0 open todos" entry** — confirmed genuinely wrong: the doc
carries one open `- [ ] [BACKEND] P1.` todo (the paper-LIVE `AtomicInstruction`→`AtomicLegExecutor` routing seam).
Diverged from this finalize todo's literal instruction here: the doc's own text shows the architecture question was
**RULED by the operator on 2026-07-28** (after this finalize plan was authored 2026-07-25), so it is no longer "an
unresolved operator-directed architectural decision" — it reads as build-ready work now. Flagged it accurately as 1 open
build-ready todo, with the doc's genuinely-still-open OPERATOR-GATED items (paper-vs-live promotion, Betfair
credentials) called out separately rather than conflating the two.

Diff: `unified-trading-pm@<see commit below>` touches only `plans/active/prediction_consolidated_closeout_2026_07_18.md`
(656 lines post-edit, under the 1000-line hard cap). Todo 2's own checkbox flipped above. No code shipped — doc-only
correction, as scoped.

### 2026-07-30 (slot-2, backend_engineer craft) — Todo 3 done: batch2 archived via the standard 6-step ritual

Picked up todo 3 via `/boot`. Confirmed todos 1 and 2 above were both `[x]` before starting.

**Step 1 (Deferred-item migration check)** — re-verified the batch2 Deferred section's 8 remaining item-groups against
current corpus state, checking specifically whether any blocker cleared during batch2's own execution:
`prediction_phase_ab_residuals_2026_07_24.md` still has 9 open todos (nonzero — phase_c/d/e's gate is still shut,
unchanged); `data_completion_prediction_2026_07_15.md` still `status: active`, unchanged (independently re-confirmed by
`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s own Deferred section as "too large for a batch todo"); the
arb-bridge doc's ruling is already reflected (this plan's own todo 2 +
`prediction_satellite_ao_dispatch_batch6_ 2026_07_29.md`'s dispatched todo — no duplicate needed);
`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`'s Phase-5 canonical-groups backfill item is already tracked as
its own `[SCRIPT] P1` todo in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (line 219) — no migration needed;
that same doc's `[VERIFY][UI]` deployment-ui re-walk item (line 106) is still genuinely blocked, but on
`[BLOCKED-PLAYWRIGHT]` (no UI-capable dev-server slot) — a different, still-open blocker than batch2's Deferred note
implied, not something that cleared when this batch's sentinel-fan-out todo shipped;
`prediction_universe_capture_dead_since_07_01_2026_07_06.md`'s secondary conflicts (MVP-backfill-gate overlap,
adapter-file collision note) remain explicitly Phase-D's own P0, unchanged — its main doc is separately confirmed fully
archived (`plans/archive/issues/`) via batch2 todo 6. **Result: nothing newly cleared beyond what's already reflected in
the Deferred section as written — no new todo migration required.**

**Step 2** — archive banners added to both this doc and the parent
(`prediction_satellite_ao_dispatch_batch2_2026_07_ 25.md`); `status` flipped `active` → `complete` on both frontmatters.

**Step 3 (codex-alignment check)** — this plan's own "Codex SSOTs" section and the parent's already state no new durable
contract; confirmed — every todo executed an already-decided spec from its source doc or an already-RULED codex
standard. Nothing to update.

**Step 4** — no new CLAUDE.md contract to add (same reasoning as step 3).

**Step 5 (corpus referrer fixup)** — grepped the full corpus for `prediction_satellite_ao_dispatch_batch2_2026_07_25`
and `prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25`. Fixed all 6 path-shaped (`plans/active/...`-prefixed
`related:`/citation) hits, per the batch1-finalize precedent (path-shaped references only — bare-filename prose
citations of "what happened" left as historical narrative): `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (2
refs, `related:`), `prediction_consolidated_closeout_ 2026_07_18.md` (`related:`),
`prediction_consolidated_native_ao_extract_2026_07_25.md` (`related:`),
`issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (Source citation),
`plans/epics/manifest_master.md` (Source citation) — all now point at `/plans/archive/2026_07/...`.
`plans/active/INDEX.md` is auto-generated (`scripts/plans/regenerate_active_plan_index.py`) — regenerated, not
hand-edited. Already-archived docs referencing the old path (`prediction_satellite_ao_dispatch_batch3_2026_07_26.md`,
`prediction_satellite_ao_dispatch_batch1_2026_07_25.md`,
`prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md`, `active_plan_inventory_dashboard_2026_07_24.md`,
`ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md`) are historical narrative snapshots, correctly left
as-is, per the same precedent. Bare-filename prose citations in
`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`, `ag_closeout_audit_rollout_2026_07_25.md`,
`prediction_phase_ab_residuals_2026_07_24.md`, `predictions_ml_walk_forward_and_arb_2026_06_20.md`, and
`prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md` (all
"`prediction_satellite_ao_dispatch_batch2_2026_ 07_25.md` todo N" / "batch2's own finalize" style narrative, no
`plans/active/` prefix) left as-is, same precedent.

**Step 6** — `locked_by` confirmed empty on both docs (was already empty). Both docs moved to `plans/archive/2026_07/`
in this same commit.

Todo 3's own checkbox flipped above. All 3 finalize-plan todos now done — this finalize doc itself archives alongside
the parent in this same commit, per its own Done-when. Repo: unified-trading-pm only.
