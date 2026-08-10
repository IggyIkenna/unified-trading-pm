---
doc_type: plan
title: Infra satellite AO batch 11 — na-eligibility-audit body-hash blind to context-scout's Progress Log marker line
summary: >-
  Eleventh AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-09, second run of the day — slot 9, dispatch agt-c74a01). Single source:
  `issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md`, filed by the `/na-eligibility-
  audit` tradfi-tranche run (dispatch agt-3df41f) at 06:05Z today, after this morning's `/ag-closeout-audit infra` run
  (dispatch agt-3b6f6b) had already closed out — the only genuinely never-triaged infra-tagged doc found this run (the
  other 11 never-cited candidates the Phase-0 pre-filter flagged are all already-tracked carried findings from prior
  days' parked-findings reports, re-verified unchanged, see the parked-findings append below). `body_content_hash()`
  (the frontmatter-blind diff mechanism `infra_satellite_ao_dispatch_batch7_2026_08_04.md` shipped, `[x]` done) strips
  its own verdict-marker lines but not `/context-scout`'s separate body-level Progress Log line, so a context-scout-only
  touch still flips `incremental_skip` to `false` — measured 44% false-positive rate (11/25 docs) on one tranche, one
  run. Both of the source doc's todos are bounded/deterministic (extend one regex + add a unit fixture; add one
  cross-reference line) with zero overlap against batch7's already-shipped work or any other in-flight plan.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-11, plan-hygiene, na-eligibility-audit]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch11_finalize_2026_08_09.md,
    /plans/active/issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/archive/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_09.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md,
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    tests/unit/test_generate_na_doc_tranche_inventory.py,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-09, second dispatch of the day (slot 9, dispatch agt-c74a01). Phase 0 re-ran
  `generate_ag_closeout_audit_candidates.py --tranche infra` live (50 members, 13 covering docs, 12 never-cited) and
  diffed against this morning's run's own reported candidate set: 11 of 12 never-cited docs were already addressed in
  some prior day's `ag_closeout_audit_infra_parked_*.md` or an archived/active batch doc (cross-checked by grepping
  every parked doc + every batch/finalize doc, active and archived, for each candidate's basename); exactly one —
  today's `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` — had zero hits anywhere in the
  infra tranche's history, confirming it is genuinely new since this morning's close-out. Direct-read in full (mirrors
  this morning's run's own "direct-read the net-new candidates" pattern rather than spinning up a Workflow for a single
  doc). Conflict-checked against `infra_consolidated_closeout_2026_07_25.md`, all `infra_*batch*`/`*finalize*` docs
  (active + archived), and a corpus-wide grep for the target function/regex names — see below. See
  `issues/ag_closeout_audit_infra_parked_2026_08_09.md`'s append entry for this run's full report.
---

# Infra satellite docs — AO dispatch batch 11

## Why this plan exists

`infra_satellite_ao_dispatch_batch7_2026_08_04.md` already shipped (`[x]`, 0 open todos) a frontmatter-blind
`body_content_hash()` for `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py`'s incremental-mode output, closing
`na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`. That fix strips YAML
frontmatter and any line matching `_VERDICT_MARKER_LINE_RE` (na-eligibility-audit's own
`**na-eligibility-audit YYYY-MM-DD**...` marker) before hashing.

Today's `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` (filed by the na-eligibility-audit
tradfi-tranche run, dispatch agt-3df41f, while manually `git diff`-verifying every doc its own Phase 0 flagged "changed
since verdict" — per SKILL.md's "grep-then-READ, not grep-then-conclude" discipline) found a follow-on gap in that same
shipped fix: `/context-scout` writes its own dated bookkeeping line directly into a doc's body Progress Log
(`- **context-scout YYYY-MM-DD**: populated/refreshed context_scope (N entries).`), which is not frontmatter and does
not match `_VERDICT_MARKER_LINE_RE`, so it survives into the hash. Any context-scout-only touch therefore still flips
`incremental_skip` to `false` on the next na-eligibility-audit run, forcing a needless full Phase-1 re-classification.
Measured live: 11 of 25 tradfi-tranche candidates (44%) were false-positive-flagged this way in one run, and since
context-scout runs corpus-wide on its own schedule independent of na-eligibility-audit's cadence, the class recurs
continuously across all 10 tranches.

## Conflict check (before drafting)

- **`body_content_hash` / `_VERDICT_MARKER_LINE_RE` / `generate_na_doc_tranche_inventory.py`**: grepped
  `infra_consolidated_closeout_2026_07_25.md`, every `infra_satellite_ao_dispatch_batch*`/`*_finalize*` doc (active +
  archived), and every `ag_closeout_audit_infra_parked_*.md` for
  `generate_na_doc_tranche_inventory\|body_content_hash\ |_VERDICT_MARKER_LINE_RE` — the only hits are
  `infra_satellite_ao_dispatch_batch7_2026_08_04.md`'s own now-`[x]`-done todo (the ORIGINAL frontmatter-blind hash, a
  different specific gap: na-eligibility-audit's own marker vs context-scout's marker) and unrelated `related:`-list
  citations of the sibling `generate_ag_closeout_audit_ candidates.py` script (a different script, same directory). No
  live claim on this specific delta. Corpus-wide grep (`plans/active/` + `plans/active/issues/`) for
  `body_content_hash\|_VERDICT_MARKER_LINE_RE` outside the source doc itself: zero hits.
- **`cursor-configs/skills/na-eligibility-audit/SKILL.md`'s Phase 0 section (todo 2's target)**: no other active plan
  proposes an edit to that section.
- **File-collision check across this batch's own 2 todos**: todo 1 touches
  `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` + `tests/unit/test_generate_na_doc_tranche_inventory.py`;
  todo 2 touches `cursor-configs/skills/na-eligibility-audit/SKILL.md` only. No shared file — safe to run concurrently
  (`sequential: false`).

## Todos

- [x] ✅ [SCRIPT] P2. **Extend `body_content_hash()`'s marker-line stripping to also exclude `/context-scout`'s
      body-level Progress Log line, generalized to a sibling-marker family rather than a second one-off special case.**
      In `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` (`_VERDICT_MARKER_LINE_RE` at line ~61,
      `body_content_hash()` at line ~78): add a sibling regex (or broaden the existing one) matching
      `**context-scout YYYY-MM-DD**...` body lines and strip them the same way before hashing. Before writing the fix,
      grep the active corpus for other dated bookkeeping-marker conventions already in informal use
      (`\*\*[a-z][a-z_-]* \d{4}-\d{2}-\d{2}\*\*:` beyond `na-eligibility-audit` and `context-scout` — e.g.
      `docs-reconciler`/`plan-reconciler`/`ag-closeout-audit` may write similarly-shaped dated lines) so the fix strips
      any known sibling-skill dated marker line as a general rule, not a second special case a third skill's marker
      convention re-triggers later. Add a unit fixture in `tests/unit/test_generate_na_doc_tranche_inventory.py`
      (natural sibling to the existing `test_body_content_hash_stable_across_frontmatter_change` /
      `test_body_content_hash_differs_on_body_change` tests at lines ~446/456) proving a doc whose only post-marker diff
      is a context-scout (or other confirmed sibling-marker) line computes the SAME hash as before that line was added.
      Done when: the regression fixture passes, and re-running the exact reproduction from the source doc's evidence
      table (`git diff <marker-sha>..HEAD` on the 11 named tradfi docs) shows `incremental_skip: true` for each. Source:
      `issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` todo 1. (repo:
      unified-trading-pm) — unified-trading-pm@a1f72c11c8. `_BOOKKEEPING_MARKER_SKILL_NAMES` generalizes stripping to
      `{na-eligibility-audit, context-scout}` (corpus-grepped for other `**<name> YYYY-MM-DD**:` conventions;
      docs-reconcile/plan-reconcile/ag-closeout-audit write doc-specific analysis in their marker lines, not
      boilerplate, so deliberately excluded — see the code comment). New regression fixture
      `test_body_content_hash_stable_across_context_scout_marker_line` passes; full 23-test file green. Re-running the
      evidence table's 11 named docs: 3 (no fresh verdict marker yet) directly confirm `incremental_skip: true` via the
      git-fallback path — exactly the false-positive class this fixes. The other 8 already carry a same-day
      `na-eligibility-audit` re-verification marker written before this fix (dispatch agt-3df41f) or a genuine
      post-marker content edit (e.g. `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s later commit) —
      `incremental_skip` correctly reads `false` for those since the corpus moved past the issue's evidence-table
      snapshot in the hours since filing; not a fix defect (verified: their stored `[body-hash:…]` predates/differs from
      what a same-content run of this code produces, and does NOT match what a pre-fix run of this code produces either
      — a pre-existing single-line-only marker-stripping limitation, out of this todo's scope, that already applied
      identically to na-eligibility-audit's own multi-line verdict markers before this change).
- [x] ✅ [DOCS] P3. **Cross-reference this issue in `SKILL.md`'s Phase 0 "Interim mitigation for date-fallback
      false-positives" section.** In `cursor-configs/skills/na-eligibility-audit/SKILL.md` (~line 116): add a one-line
      pointer naming the context-scout-specific sub-case explicitly, so the next tranche run that hits it can cite this
      finding instead of independently re-deriving the same by-hand `git diff` verification across a dozen docs. Done
      when: the cross-reference line exists and names both the mechanism (context-scout's body-level marker) and the fix
      doc. Source: `issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` todo 2. (repo:
      unified-trading-pm) — unified-trading-pm@4120fc45aa. Added a sentence naming the context-scout body-level marker
      mechanism and citing `issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md`
      immediately after the "unnecessary once the content-hash SCRIPT is live" line.

## Operator approval gate

**RULED 2026-08-09 (operator, bulk approval): approved.** Flipped `status: draft` → `status: active` in
`unified-trading-pm@78e91572f3` ("flip 14 satellite-extraction batches draft->active for AO dispatch") alongside 13
sibling batches (ao batch9-16, infra batch11-14, prediction batch10, sports batch12); its finalize twin was already
`status: active` per the no-double-gate ruling and stayed correctly gated either way. This banner was stale (still read
"awaiting review" against an already-`active` frontmatter) until fixed by `/ag-closeout-audit infra` 2026-08-10.

## Codex SSOTs (read before touching a todo)

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the procedure this batch was produced by
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol applied
  above
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule, dispatch-scope eligibility test

## Progress Log

- **2026-08-09** — Drafted by `/ag-closeout-audit infra` (autonomous mode, second dispatch of the day, slot 9, dispatch
  agt-c74a01). Paired with `infra_satellite_ao_dispatch_batch11_finalize_2026_08_09.md` in the same run per the
  finalize-plan-coverage rule.
- **2026-08-10 (slot-15, infra)**: shipped todo 2 — `unified-trading-pm@4120fc45aa`. Both todos now `[x]`; plan has 0
  open items (archival is the paired finalize plan's job, not this todo).
