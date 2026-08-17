---
doc_type: plan
title: AO satellite AO batch 23 — conflict-clear bounded extraction from the 2026-08-17 na-eligibility-audit ao run
summary: >-
  TWENTY-THIRD AO-dispatch batch for the `ao` topic tranche — output of a `/na-eligibility-audit ao` Phase 0-3 run
  (2026-08-17, dispatch agt-614193). Phase 1 classified 57 in-scope `assigned_vm: NA` docs via a 7-batch Workflow
  fan-out; 5 items across 3 source docs survive the Phase 2 conflict-check (verbatim/near-verbatim duplicate check
  against every active `assigned_vm: planning` plan in the same parent_epic, the tranche's own consolidated closeout,
  and every other satellite batch created this run or earlier) as genuinely bounded, already-decided, conflict-clear
  work. A 6th RECLASSIFY candidate (`codex_luna_flex_bridge_2026_08_14.md`'s Luna rate-card entry) was found
  conflicted against a standing operator-direction redirect banner cited in `ag_closeout_audit_ao_parked_2026_08_16.md`
  and deliberately EXCLUDED — see that doc + this run's report. A 7th (`plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`,
  all 3 open todos) was found ALREADY claimed verbatim by the active `ao_satellite_ao_dispatch_batch22_2026_08_16.md`
  and reclassified to KEEP-NA-STALE (already-duplicated) instead — not re-extracted here.
status: draft
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-23, satellite-docs, satellite-extraction, na-eligibility-audit]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch23_finalize_2026_08_17.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md,
    /plans/active/issues/docs_reconcile_findings_2026_08_17.md,
    /plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md,
    /plans/active/issues/docs_reconcile_findings_2026_08_17.md,
    /plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  `/na-eligibility-audit ao` (2026-08-17, dispatch agt-614193, slot 30). Phase 1 classified 57 in-scope docs (of 69
  total ao-tranche candidates, 12 skipped via an unchanged incremental-diff marker) via a 7-batch Workflow fan-out.
  Phase 2 conflict-check: grepped every status:draft/active `ao_satellite_ao_dispatch_batch*` (3/8/14/21/22) +
  finalizes, `ao_consolidated_closeout_2026_08_12.md`, and every other `assigned_vm: planning` doc under
  `parent_epic: orchestrator_master`/`agent_operating_framework_master` for each of the 6 RECLASSIFY candidates'
  subject matter (distinctive function/mechanism names, not just titles) — zero hits for the 5 items extracted here.
  Two candidates were caught by this same check and NOT extracted: `codex_luna_flex_bridge_2026_08_14.md` (redirect
  banner on a sibling surface) and `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` (already claimed by
  batch22 — 3 of batch22's own 6 todos cite it by path).
---

# AO satellite AO batch 23

> **`status: draft`** — the safety rail. Never auto-ingested/dispatched until an operator flips this to `active`.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once activated.

## Why this plan exists

`/na-eligibility-audit ao`'s 2026-08-17 run classified the full `assigned_vm: NA` "ao" tranche population. Of 57
in-scope docs, the large majority are genuine KEEP-NA (operator-gated, live-infra judgment, unresolved design forks,
or already tracked elsewhere) — see this run's report for the full breakdown. This batch extracts the handful that
are bounded, already-decided, and conflict-clear:

1. **Audit whether other `plan_reconciler`/`na-eligibility-audit` runs have silently missed answers to still-open
   blocked questions** — a bounded, stated-done-when audit with no open judgment call. Source:
   `plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md`.
2. **Fix `fix_frontmatter.py`'s summary-truncation logic** — a fully scoped, single-file code fix with two named
   defects and a stated fix direction. Source: `docs_reconcile_findings_2026_08_17.md`.
3-5. **Three `check_reference_paths.py`/`find_moved_doc_referrers.sh` fixes** (hard-error on an unresolvable `--only`
   path; print offending references on failure even under `--quiet`; retire the now-dead `--quiet`-workaround
   rationale once #4 ships) — each a well-specified, deterministic script change with a stated test to add. Source:
   `check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md`.

**Explicitly excluded** (named here so nobody re-derives them as candidates without reading why):

1. **`codex_luna_flex_bridge_2026_08_14.md`'s Luna `model_pricing.py` rate-card entry** — individually bounded
   (mirrors an already-shipped identical pattern for GLM Coding Plan), but `ag_closeout_audit_ao_parked_2026_08_16.md`
   (this same tranche's standing parking register) explicitly states the WHOLE doc is "excluded from AO-dispatch by
   operator direction 2026-08-14 (operator is handling both elsewhere, not via this tracker)" — a redirect-banner
   never-relitigate case found on a sibling surface, not inside the candidate doc itself. Flagged in this run's report
   for an operator/human cross-check rather than dispatched here.
2. **`plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`'s all 3 open todos** — individually bounded (the operator's
   2026-08-15 Option-A ruling resolved the judgment call), but ALL THREE are already claimed verbatim by the active
   `ao_satellite_ao_dispatch_batch22_2026_08_16.md` (its todos 1-3 cite this doc by path + exact todo text; its own
   finalize plan's todo 2 already owns reconciling/archiving this source doc once batch22 ships). Reclassified to
   KEEP-NA-STALE (already-duplicated) instead of re-extracted — would otherwise dispatch a duplicate.
3. **Every other doc's remaining open items** — operator-gated, design-fork, credential-blocked, or already tracked
   via an existing active plan/epic per this run's own report; re-triage on the next `/na-eligibility-audit ao` run,
   not re-derived here.

## Rules for every worker on this plan

- The 5 todos below are file-disjoint (different scripts/mechanisms) — safe to run concurrently, no `sequential: true`.
- Todos 3-5 all touch `scripts/plan-hygiene/check_reference_paths.py` (todos 3-4) or
  `scripts/plan-hygiene/find_moved_doc_referrers.sh` (todo 5) — todos 3 and 4 share `check_reference_paths.py` but
  touch disjoint functions (`_run_only`'s existence-check vs its failure-printing path); todo 5 is gated on todo 4
  landing first by its own done-when (it retires a workaround whose reason for existing is todo 4's defect), not by
  `sequential: true` — a worker picking up todo 5 first should check todo 4's status before starting.

## Todos

- [ ] [BACKEND] P2. **Audit whether other `plan_reconciler`/`na-eligibility-audit` runs have silently missed answers
      to still-open blocked questions**, now that this gap is confirmed live (not just suspected — reproduced
      2026-08-16, dispatch agt-3eb42b). Query the escalation/blocked-question table for any row with a recorded
      operator answer but no corresponding worker-side pickup, across recent runs. **Done when**: a count of
      affected historical rows is reported (0 is a valid, good answer) and, if any are found, each is individually
      resolved (apply the answer now, or re-ask if too stale to trust). Source:
      `/plans/active/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md` todo "[BACKEND] P2.
      Audit whether other plan_reconciler/na-eligibility-audit runs...". Repo: agent-orchestrator (+ unified-trading-pm
      for the source doc's own historical-scan scope).
- [ ] [SCRIPT] P2. **Fix `fix_frontmatter.py`'s summary-truncation logic**
      (`scripts/plan-hygiene/fix_frontmatter.py` `get_first_paragraph_after_heading()`, lines ~245-294, called at
      ~646-654 only `if not has_field(new_fm, "summary")`). Two confirmed defects: (a) hard-cuts mid-word at 197
      chars with a literal `" ..."` suffix when no sentence/space boundary is found in budget; (b) locks onto the
      FIRST `". "`/`"! "`/`"? "` in the source paragraph even when that leaves most of the 197-char budget unused,
      producing dangling lead-ins. **Fix direction**: widen the sentence-boundary search to use more of the 197-char
      budget before falling back to a hard cut, and prefer a hard cut mid-clause (not mid-word) as the last resort.
      **Done when**: the widened search + mid-clause-cut fallback ship with a regression test covering both defect
      classes (a truncation that previously stopped before the doc's real point, and a dangling first-sentence
      lead-in), and `quality-gates.sh` is green. Source: `/plans/active/issues/docs_reconcile_findings_2026_08_17.md`
      todo "[SCRIPT] P2. Fix fix_frontmatter.py's summary-truncation logic". Repo: unified-trading-pm.
- [ ] [SCRIPT] P1. **Make an unresolvable `--only` path a hard error** in `check_reference_paths.py`'s `_run_only()`
      — today `if not p.is_file(): continue` silently drops an unresolvable path and the function reports "0
      violation(s)" / exit 0, a false-clean-bill-of-health that cost 7 failed `safe-doc-push` attempts and 6 wrong
      diagnoses on one real incident (2026-08-12). **Fix**: print the attempted path (including its resolved
      absolute form) and exit non-zero when a named `--only` path does not resolve. **Done when**: a regression test
      asserts non-zero exit for a non-existent `--only` path, and `quality-gates.sh` is green. Source:
      `/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md` todo "[SCRIPT]
      P1. Make an unresolvable --only path a hard error". Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. **Print offending references on failure even under `--quiet`** in `check_reference_paths.py`'s
      `_run_only()`, `_run_diff_base()`, and the corpus-wide path — `--quiet` currently suppresses the per-violation
      `FORMAT`/`DANGLING` lines but keeps the summary count, so a precommit failure says "N violation(s)" without
      ever naming the offending reference. **Fix**: print offending references on FAILURE regardless of `--quiet`;
      quiet should suppress noise on success, never evidence on failure. **Done when**: a regression test confirms
      `--quiet` + a real violation still prints the offending reference(s), and `quality-gates.sh` is green. Source:
      `/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md` todo "[SCRIPT]
      P2. Print offending references on failure even under --quiet". Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **Retire the `--quiet`-workaround rationale in `find_moved_doc_referrers.sh`'s header** once todo
      4 ships, and re-check whether that script still has a reason to exist. Its header currently documents its own
      existence as a workaround specifically for `run_hygiene_sweep.sh` calling `check_reference_paths.py` with
      `--quiet`, which todo 4 makes obsolete. **Done when**: the header comment is corrected (or the script is
      retired if it truly has no other purpose once the workaround rationale is gone) and any caller that depended
      on it is checked. Source:
      `/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md` todo "[SCRIPT]
      P3. Retire the --quiet-workaround rationale in find_moved_doc_referrers.sh's header". Repo: unified-trading-pm.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`, `/codex/12-agent-workflow/measurement-claims-discipline.md`.

## Progress Log

- **2026-08-17 (na_eligibility_auditor, dispatch agt-614193, autonomous)**: Drafted per `/na-eligibility-audit ao`'s
  Phase 3 — 5 conflict-clear, file-disjoint, bounded todos extracted from 3 source docs after Phase 2's conflict-check
  excluded 2 further candidates (a redirect-banner case and an already-claimed-by-batch22 case, both detailed above).
  `status: draft` per autonomous-mode safety rail; flipping to `active` is an operator decision.
