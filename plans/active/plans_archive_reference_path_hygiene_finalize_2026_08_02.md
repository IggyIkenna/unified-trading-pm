---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/ — finalize
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until ALL of that plan's own todos are done (6 as of 2026-08-02: the original 4, now closed, plus 2 new P3
  follow-ups the parent's own work surfaced). Reconciles the parent's own checkboxes against real evidence
  (self-contained plan, no external source docs to flip back), re-checks the 2 deferred findings for whether their
  blocker has cleared, and archives the parent via the standard 6-step ritual.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical, finalize]
related:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/task_template.md,
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02_finalize.md,
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02_finalize_2026_08_03.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-03"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
source: >-
  Authored 2026-08-02 (slot-10) to close a check_finalize_plan_coverage.py regression (1 > baseline 0) found while
  shipping an unrelated fix in the same repo — plans_archive_reference_path_hygiene_2026_08_02.md (assigned_vm:
  planning) shipped without a companion gated finalize plan, per plans/active/task_template.md §4's mandatory-pairing
  rule. Updated 2026-08-02 (slot-8, concurrent session) after the parent plan's own work surfaced 2 new P3 follow-up
  todos (duplicate-named archived docs; a pre-existing +1 existence-ratchet gap) — this doc's gate already covers them
  automatically (gate_on_depends reads the parent's live todo state), only the prose needed updating.
assigned_role: review
sequential: true
drift_direction: advance-code
---

# Scoped reference-path hygiene pass over `plans/archive/` — finalize

> **🟢 ARCHIVED 2026-08-03.** Both todos confirmed evidence-backed and executed — see RESULTs below. Consolidated with
> two duplicate finalize plans that independently gated the same parent (see Progress Log) into this single archival
> commit. Moved to `/plans/active/plans_archive_reference_path_hygiene_finalize_2026_08_02.md`.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile the parent plan's own checkboxes against real evidence, including its 2 newer P3
      follow-ups.** The parent plan is self-contained (no external `Source:` docs to flip back — its todos are the work,
      not an extraction from other docs). For the original 4: verify the cited shipping commit exists and is an ancestor
      of `origin/live-defi-rollout` (`git merge-base --is-ancestor`), and confirm the claim that `check_reference_paths`
      format/exist counts dropped back toward baseline against a fresh
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` run rather than trusting the recorded number. For the 2
      newer P3 todos, re-check whether their blocker has since cleared: (1) the duplicate-named archived docs
      (`work_split_2026_05_22_ikenna.md`'s 3 cited backfill_phase3 docs;
      `mock_data_pipeline_benchmarking_2026_05_10.md`) — re-run `diff` on each pair; if still diverged, this needs the
      parent plan's own todo done first, not this finalize's job to resolve. (2) The pre-existing +1 existence-ratchet
      gap — re-run `python3 scripts/plan-hygiene/check_reference_paths.py` and confirm whether the live existence count
      is still exactly baseline+1, or whether some other commit already fixed/re-baselined it. **Done when**: all 6
      checkboxes are confirmed evidence-backed (or a note explaining why one is still legitimately blocked) and the
      reference-path ratchet is verified actually cleared (not just claimed). **RESULT (slot-11, 2026-08-03): all 6
      confirmed evidence-backed, live-verified, not just trusted from the doc.** Cited commits `dfdb0887f`, `77be36524`
      both verified real and ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`). Fresh
      `python3 scripts/plan-hygiene/check_reference_paths.py` run: format 81/81 ✅, existence 87/87 ✅ — exact match to
      the parent's final `--update-baseline` (90→87), confirming the ratchet claim rather than trusting the recorded
      number. The 2 P3 follow-ups were themselves already closed with RESULT sections by the time this task was
      dispatched (a fresh worker's own work, not this finalize's); re-verified rather than re-trusted: (1) the 4
      duplicate-named archived docs (`work_split_2026_05_22_ikenna.md` ×2 copies,
      `mock_data_pipeline_benchmarking_2026_05_10.md` ×2 copies) all confirmed present on disk, and every hand-fixed
      `related:` entry (3 files) points at an existing, correctly-vintage-matched target. (2) The pre-existing +1
      existence gap is confirmed resolved — folded into the same `b53ce2c59` commit that also fixed a NEW +4 format
      regression and shrank existence 90→87 (a real improvement, not just a restore), matching the fresh
      `check_reference_paths.py` run above. Full `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` also confirms the
      "Reference path convention" hard check ✅ PASS (3 unrelated hard failures elsewhere in the corpus —
      prettier-proseWrap ratchet, `assigned_vm:NA` size ratchet, archive-candidates ratchet — all already tracked by
      other active issue docs, out of this plan's reference-path scope, not chased here).
- [x] ✅ [DOC] P2. **Archive `plans_archive_reference_path_hygiene_2026_08_02.md`** via the standard 6-step ritual
      (CLAUDE.md § plan archival) once todo 1 confirms it is fully done: add the archive banner → confirm no codex
      contract needs updating (this plan only runs an existing script over an existing population; it does not establish
      a new contract) → grep the corpus for every referrer of `plans_archive_reference_path_hygiene_2026_08_02` and
      repoint each to the archived path → move to `plans/archive/2026_08/` → clear `locked_by` (already empty; confirm)
      → archive this finalize doc alongside it in the same commit. **Done when**: the plan is in
      `plans/archive/2026_08/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it. **RESULT (slot-11, 2026-08-03): archived, PLUS a real corpus-hygiene defect
      found and fixed in the same pass — see Progress Log for the triple-duplicate-finalize consolidation.** No codex
      contract needed updating (confirmed — the parent only ran an existing script over an existing population).
      Corpus-wide referrer grep + repoint done for all 4 docs in the consolidated cluster (this doc, the parent, and the
      2 duplicate finalize plans — see Progress Log); `INDEX.md` + `active_plan_inventory_dashboard` regenerated via the
      standard scripts, not hand-edited. `locked_by` confirmed empty on all 4. `check_reference_paths.py` re-verified
      clean post-move (format 81/81, existence 87/87 — no regression from the archival itself).

## Codex SSOTs

- `/codex/11-project-management/cross-reference-path-convention.md` — the ratchet the parent plan's work targets
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-02 (slot-10)** — Authored after-the-fact to close a `check_finalize_plan_coverage.py` regression discovered
  while shipping an unrelated fix in the same repo (the parent plan had already shipped without its required companion).
  `status: active` (not `draft`) per the established no-double-gate precedent — `gate_on_depends: true` already
  machine-holds every todo here until the parent's own todos are `done`.
- **2026-08-02 (slot-8, concurrent)** — Independently hit the same coverage gap while working the parent plan itself
  (which by this point had grown from 4 to 6 todos — 2 new P3 follow-ups surfaced by the parent's own investigation).
  Rebase surfaced slot-10's already-landed version of this exact file; reconciled by updating the stale "4 todos"
  wording and folding the 2 new findings' specific re-check steps into todo 1, rather than shipping a second competing
  copy. No functional gap existed in slot-10's version — `gate_on_depends` already reads the parent's live todo state
  regardless of what the prose says — this is a prose-accuracy fix only.
- **2026-08-03 (slot-11, review craft, dispatched to this doc's own P2 todos)** — Worked todo 1 (live-verified, not
  trusted — see RESULT). While gathering referrers for todo 2's corpus-wide repoint, discovered this doc has **two
  independently-authored duplicate siblings**, both also gated on the same parent plan and both doing essentially the
  same reconcile+archive job: `plans_archive_reference_path_hygiene_2026_08_02_finalize.md` (authored 2026-08-02,
  already had its own reconcile-equivalent todos 1+2 done by slot-15/slot-14, only its archival todo 3 still open) and
  `plans_archive_reference_path_hygiene_2026_08_02_finalize_2026_08_03.md` (authored 2026-08-03, nothing done yet). This
  is the exact same `check_finalize_plan_coverage.py`-regression trigger independently re-discovered by 3 separate
  sessions (this doc's own Progress Log already records 2 near-simultaneous authors on 2026-08-02; a 3rd, unrelated
  session repeated it again on 2026-08-03) — a real duplicate-tracked-work defect, not a false alarm (all 3 gate on the
  identical `depends_on`, cite the identical parent, and their todos overlap almost verbatim). Rather than performing
  the archival a 3rd/4th time in parallel (a genuine race risk — the archival is a single one-time `git mv`),
  consolidated: performed the actual archival ONCE covering the parent + all 3 finalize plans in one commit, flipped
  each doc's remaining open todo(s) citing this consolidation, and archived all 4 docs together. This also closes the
  two duplicates' own now-redundant `assigned_vm: planning` dispatch (they would otherwise sit `active` forever with no
  further work to do, since the one archival any of them was gating on has already happened).
