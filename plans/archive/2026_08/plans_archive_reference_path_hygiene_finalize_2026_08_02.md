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
    /plans/archive/2026_08/plans_archive_reference_path_hygiene_2026_08_02.md,
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/task_template.md,
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

> **🟢 ARCHIVED 2026-08-03.** Both todos done. **New finding, disposed of here**: TWO additional gated finalize plans
> were independently authored for this same parent, unaware of this one or each other —
> `plans_archive_reference_path_hygiene_2026_08_02_finalize.md` (2026-08-02, cites the stale pre-`dfdb0887` baseline
> numbers 161/901) and `plans_archive_reference_path_hygiene_2026_08_02_finalize_2026_08_03.md` (2026-08-03, authored
> after this doc — its own `source:` field even names the same `check_finalize_plan_coverage.py` trigger this doc's
> `source:` already documents). All three were still `status: active`/queued with zero todos executed when this session
> found them (verified live backlog: none dispatched). Since THIS doc is the most mature (already itself the product of
> a 2026-08-02 slot-10/slot-8 reconciliation merge — see its own Progress Log) and is the one actually executing the
> ritual right now, the other two are marked duplicate + archived alongside it (see each doc's own banner) rather than
> left as live zombie gates that would otherwise dispatch 4 more redundant `queued` tasks the moment this parent's
> `depends_on` gate cleared. Flagging the `check_finalize_plan_coverage.py`/dispatch flow gap that let 3 authors hit the
> same gap unaware of each other as worth a look, not chasing it further here (out of this doc's own scope).
>
> Both parent-plan checkboxes reconciled (all 6 `[x]`, evidence-backed, verified live not just read) and
> `plans_archive_reference_path_hygiene_2026_08_02.md` archived to `/plans/archive/2026_08/`. This finalize doc itself
> moves alongside it in a follow-up commit (per the never-combine-checkbox-flip-with-git-mv rule) to
> `/plans/archive/2026_08/plans_archive_reference_path_hygiene_finalize_2026_08_02.md`. No new durable contract — codex
> alignment check: nothing to update.

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
      reference-path ratchet is verified actually cleared (not just claimed). **DONE 2026-08-03 (slot-10)** — all 6
      checkboxes confirmed `[x]` with cited evidence in the parent doc itself (todo 1-3: `Files changed: 0`, confirmed
      idempotent; todo 4: `+47/+14` regression already resolved via `dfdb0887`; todo 5: duplicate-archived-docs finding
      resolved keep-both; todo 6, the +1 existence gap: resolved live this session — see the parent's own todo 6 RESULT
      note). `check_reference_paths.py` re-run live (not trusted from the doc): format 81/81 ✅, existence 87/90 ✅ —
      genuinely improved, not just restored (baseline lowered to 87 in the same session, `unified-trading-pm@a4409ab45`,
      verified on `origin/live-defi-rollout`).
- [x] ✅ [DOC] P2. **Archive `plans_archive_reference_path_hygiene_2026_08_02.md`** via the standard 6-step ritual
      (CLAUDE.md § plan archival) once todo 1 confirms it is fully done: add the archive banner → confirm no codex
      contract needs updating (this plan only runs an existing script over an existing population; it does not establish
      a new contract) → grep the corpus for every referrer of `plans_archive_reference_path_hygiene_2026_08_02` and
      repoint each to the archived path → move to `plans/archive/2026_08/` → clear `locked_by` (already empty; confirm)
      → archive this finalize doc alongside it in the same commit. **Done when**: the plan is in
      `plans/archive/2026_08/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it. **DONE 2026-08-03 (slot-10)** — banner added, `locked_by` confirmed empty
      on both docs, codex-alignment check confirmed nothing to update. Corpus referrer sweep: only the 3 duplicate
      finalize docs themselves carried leading-slash (`/plans/active/...`) references to the parent — all repointed to
      the new archived path as part of disposing of the duplicates (see this doc's own banner); 3 bare-filename prose
      mentions elsewhere (`ao_satellite_ao_dispatch_batch3_2026_07_31.md`,
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`, `issues/plan_reconcile_parked_operator_decisions_2026_08_02.md`)
      carry no leading-slash path prefix, out of `check_reference_paths.py`'s scope, left as historical record —
      matching this corpus's established convention for archived-doc citations (precedent:
      `cefi_misc_audits_and_hygiene_finalize_2026_07_25.md`'s own archival ritual). Moved to `plans/archive/2026_08/`
      (verified against the live directory, not assumed).

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
