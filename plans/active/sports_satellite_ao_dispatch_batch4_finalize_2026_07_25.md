---
doc_type: plan
title: Sports satellite AO batch 4 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch4_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 3 of that plan's todos are done. Mirrors sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md's
  pattern (reconcile each distinct source doc's checkboxes independently), plus the same batch3-style addition: re-check
  the 4 conflict-gated Deferred items once the operator has ruled on entries #5-8 in
  autonomous_session_operator_decisions_2026_07_25.md — some may become dispatchable as a batch5 once the operator
  confirms which side (the narrow batch-style fix vs. the master closeout's broader claim) should execute first, or how
  the ambiguous phantom-audit/decision-16 overlap should be sequenced.
status: complete
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-31"
parent_epic: sports_master
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
depends_on: [sports_satellite_ao_dispatch_batch4_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan, mirroring the batch2/batch3 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 4 — finalize

> **🟢 ARCHIVED 2026-07-31 — COMPLETE.** All 4 todos shipped with verified evidence (see each todo below). Todo 2 was
> vacuously satisfied (0 of the 3 source docs reached a terminal status, so nothing qualified for archival under its
> scope). Successor: none — this batch's closeout is complete, not superseded.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-13, review craft).** Reconcile all 3 distinct source docs' checkboxes. For
      each of `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s 3 now-done todos: flip the corresponding
      checkbox/section in its named source doc, citing the batch-4 commit(s) that shipped it — verify the actual shipped
      commit exists before citing it. The 3 source docs:
      `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`,
      `issues/fixtures_manifest_legacy_backfill_2026_07_24.md`,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`. For each: after flipping, re-check whether it now
      has 0 open todos remaining (checkbox AND prose-form — do not trust checkbox count alone). Only flip a doc's
      `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 3 source docs' corresponding
      checkboxes/sections are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped
      to `status: resolved`.

      **Evidence per doc**:
                                  1. `footystats_matches_predictions_fetch_gaps_2026_07_08.md` — batch4 todo 1 was diagnosis-only (found a genuine
                                     REGRESSION, not a fix) and its own worker (slot, 2026-07-27) already wrote the reconciling Progress Log entry
                                     directly into this doc at execution time (self-reconciling — no new edit needed). Verified current state: 1
                                     genuinely open todo (#4, `BLOCKED-PREREQUISITES` on the 2026-07-27 regression doc); `status: open` correctly
                                     unchanged — NOT 0 open todos, no resolved-flip warranted.
                                  2. `fixtures_manifest_legacy_backfill_2026_07_24.md` — batch4 todo 2 (slot-5/review, 2026-07-26) already edited
                                     this doc directly at execution time (the "Update (2026-07-26, slot-5/review — sports_satellite_ao_dispatch_
                                     batch4-002)" section is the reconciliation itself, self-reconciling). Verified current state: 1 genuinely open
                                     todo (the 55,233-row collision-residual delete-vs-leave decision); `status: open` correctly unchanged.
                                  3. `sports_odds_stale_fixture_reinjection_2026_07_14.md` — batch4 todo 3's read-only DIAG sweep
                                     (`market-tick-data-service@76ca401f`, verified ancestor of `origin/live-defi-rollout`) had NOT been reconciled
                                     into this doc yet. Updated todo 2's entry with the actual findings (RUSSIA_PREMIER_LEAGUE zombie confirmed
                                     still live across 18 `day=` partitions / 20 shards / 54 rows; AUSTRALIA_ALEAGUE resolved; CHINA_SUPER_LEAGUE
                                     correctly excluded) and filed the still-open purge/re-derive work as a new tracked `- [ ]` todo (batch4's DIAG
                                     scope was deliberately read-only — per the HARD RULE that every follow-up is a tracked todo, never left as
                                     prose). Verified current state: 2 genuinely open todos (the new purge todo + the pre-existing P3 gate-
                                     reassessment todo); `status: open` correctly unchanged.

                                  **Net**: none of the 3 source docs reached 0 open todos, so none was flipped to `status: resolved` — all 3
                                  genuinely still carry open work, verified per-doc rather than trusting checkbox counts. `unified-trading-pm`
                                  commit (this same commit).

- [x] ✅ [DOC] P1. **DONE 2026-07-31 (slot-12, data_engineering) — vacuously satisfied, 0 docs to archive.** Re-verified
      todo 1's own evidence against current on-disk state before treating this as a no-op: all 3 source docs
      (`footystats_matches_predictions_fetch_gaps_2026_07_08.md`, `fixtures_manifest_legacy_backfill_2026_07_24.md`,
      `sports_odds_stale_fixture_reinjection_2026_07_14.md`) confirmed still `status: open` (grepped each doc's
      frontmatter directly) — none of the 3 reached `resolved`/`complete`, so this todo's scope ("archive every source
      doc todo 1 drives to resolved") has zero qualifying docs; nothing to `git mv`. Ran
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci`: 2 pre-existing hard failures found (`check_reference_paths`
      format 191/baseline 161, existence 919/baseline 901; `check_archive_candidates` 7 candidates/baseline 4) — both
      are corpus-wide ratchet regressions from UNRELATED work (none of the 7 archive-candidate docs or the
      reference-path violations touch this plan's 3 source docs or either doc this plan itself drives to archival),
      already tracked (`issues/reference_path_convention_2026_07_23.md`); out of this P1 DOC-archival todo's scope per
      findings-triage (outside-plan, not small+clear — a multi-domain corpus sweep, not a 3-doc reconciliation). Not
      absorbing into this todo. `unified-trading-pm` (this commit).
- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 — resolved via `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md` todo
      3 (same 4 items, same operator-decisions entries #5-8 — one worker's pass covers both plans' identical todo,
      avoiding duplicate re-investigation).** All 4 operator-ruled entries were confirmed resolved but 2 had never
      actually been converted into tracked work (batch4's own `[DECISION] P2` retag over-claimed batch5 covered all 4 —
      it only genuinely covered 2). Outcome per item: (1) Transfermarkt re-attempt [entry #5] + (2) ODDS+PREDICTIONS
      blank-reason measurement [entry #6] — converted from prose into 2 new tracked `- [ ]` todos directly in
      `data_completion_sports_2026_07_24.md`, citing each entry's ruling. (3) fixtures-path census [entry #7] —
      confirmed already correctly scoped (no todo-text edit needed per the operator's own ruling); added a note in
      `sports_legacy_fixtures_path_migration_2026_07_24.md` confirming the Track S/E/C1 conflict is cleared (its
      remaining blocker is a separate, unrelated na-eligibility-audit AO-dispatch-authority park, not this conflict).
      (4) phantom spot-check [entry #8] — explicitly folded into `sports_satellite_ao_dispatch_batch7_2026_07_27.md`'s
      decision-16 `[DIAG] P2` todo (amended to name the fold-in), and the phantom-audit doc's own todo marked "do not
      dispatch independently" (a same-day, unrelated na-eligibility-audit pass had reclassified it
      `assigned_vm:     planning` with a stale "conflict-check CLEAR" claim that missed this exact ruling — corrected in
      place). Full write-up + citations: `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md` Progress Log.
      `unified-trading-pm` (this commit).
- [x] ✅ [DOC] P1. **DONE 2026-07-31 (slot-12, data_engineering)** — Archived
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md` via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) Deferred migration — verified todo 3's
      resolution of the 4 conflict-gated items and the plan's own last todo's filing of
      `sports_satellite_ao_dispatch_batch8_2026_07_30.md` for the 2 `doc_too_large_or_risky_for_batch` docs; nothing
      silently vanished. (2) Archive banner added to both this doc and the parent plan, `status: complete` on both,
      `superseded_by:` left empty (no successor — work complete). (3) Codex-alignment check: confirmed the parent plan's
      own "no new durable contract" claim still holds — grepped codex/ for the two findings this batch produced (the
      `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE` FIXTURES-key gap, the RUSSIA_PREMIER_LEAGUE zombie-tick contamination) and
      confirmed neither is a durable architectural pattern warranting a new/updated SSOT — both are point fixes /
      findings already fully written up in their own issue docs. (4) No CLAUDE.md/codex update needed (same reason). (5)
      Fixed every corpus-wide leading-slash (`/plans/active/...`) referrer of both docs' pre-archive paths:
      `sports_satellite_ao_dispatch_batch8_2026_07_30.md`, `sports_satellite_ao_dispatch_batch5_2026_07_26.md` (both its
      batch4 and batch4_finalize refs), `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md`,
      `issues/footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md`,
      `sports_consolidated_native_ao_extract_2026_07_25.md` — all repointed to `/plans/archive/2026_07/`. Bare-filename
      prose mentions (no leading slash) left as historical citations, consistent with how the batch3 archival
      (`unified-trading-pm@6315e0823`, same day) handled the identical case. (6) `locked_by` confirmed empty on both
      docs; both moved to `plans/archive/2026_07/` in this same commit. `unified-trading-pm` (this commit).
