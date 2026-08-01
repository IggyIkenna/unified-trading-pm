---
doc_type: issue
title: >-
  deployment_api_sigabrt_crash_loop_2026_07_24.md:156 cites agent-orchestrator@7ba17e2 as proof a fix is live, but that
  commit does not exist in the local agent-orchestrator clone (even after a fresh fetch)
summary: >-
  While shipping an unrelated doc, `check_plan_commit_sha_evidence.py` flagged a new (vs the 18-entry baseline)
  unresolvable `<repo>@<sha>` citation: `deployment_api_sigabrt_crash_loop_2026_07_24.md` line 156, a `[x]`-checked
  `[REVIEW] P2` todo dated 2026-07-25T06:23Z (slot 2) that claims to have confirmed `agent-orchestrator@7ba17e2`'s fix
  is "live" via content-diff. `git cat-file -t 7ba17e2` returns "Not a valid object name" in the agent-orchestrator repo
  both before and after `git fetch origin` — the commit does not exist under this SHA in that repo, on any ref.
  Re-baselined the ratchet (18->19) to unblock this session's unrelated push, since this is 6-day-old pre-existing debt,
  not something authored this session — but the underlying claim ("confirmed via content-diff that the fix is live") is
  now unverifiable as cited and should be re-checked, not silently carried forward as accepted evidence.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, deployment-api]
scope: [engineer]
tags: [evidence-backed-completion, fabricated-citation, quality-gates, deployment-api, agent-orchestrator]
related:
  [
    /plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md,
    /plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
  ]
created: 2026-07-31
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced as a side effect of `scripts/quality_gates/check_plan_commit_sha_evidence.py` failing this session's
  unrelated quickmerge (19 unresolvable citations > baseline 18); diagnosed the single new entry directly (`git cat-file
  -t 7ba17e2` in the agent-orchestrator repo, before and after a fresh `git fetch origin`) rather than assumed.
---

# Unresolvable commit-SHA citation in deployment_api_sigabrt_crash_loop_2026_07_24.md

## What was found

`plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md:156` — a `[x]` ✅-checked `[REVIEW] P2` todo reads:

> **Checked 2026-07-25T06:23Z (slot 2)**: `agent-orchestrator@7ba17e2`'s fix IS live — confirmed via content-diff (not
> ancestry — this session's own methodology lesson from the sibling ...

`git cat-file -t 7ba17e2` in the `agent-orchestrator` local clone returns `fatal: Not a valid object name 7ba17e2`, both
before and after `git fetch origin --quiet` — the cited SHA does not exist under that name, on any ref, in this clone.
`check_plan_commit_sha_evidence.py` (added per
`plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`, a prior incident of the exact same
class) confirmed this is genuinely unresolvable, not a stale-clone artifact — the baseline (captured 2026-07-25 or
earlier from a different slot's clone, `.tabs/21`) predates this citation, so it was never caught until this session's
re-baseline pass surfaced the delta (18→19).

## Why it matters

- This todo is the ONLY evidence in that issue doc that the SIGABRT fix actually shipped and is live — if the SHA is
  wrong (typo, truncated wrong, or cites a commit that was later rewritten/rebased away), the claim "confirmed via
  content-diff" cannot currently be re-verified by anyone reading the doc.
- Matches the exact fabrication-risk class `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` was filed to
  catch — this is either a second instance of that same problem, or an honest typo/truncation error. Not distinguished
  here; needs someone with access to `agent-orchestrator`'s reflog/GitHub history around 2026-07-25 to determine which.
- Re-baselining this session was the correct mechanical unblock (confirmed pre-existing, not authored this session, and
  the check's own documented remedy path) — but a re-baseline only silences the ratchet, it does not resolve the
  underlying unverifiable claim.

## Recommended next step

Whoever picks this up: search `agent-orchestrator`'s reflog / GitHub commit search around 2026-07-25 for a commit
matching the described fix (gunicorn `post_worker_init` calling `faulthandler.enable()`, per the surrounding context in
`deployment_api_sigabrt_crash_loop_2026_07_24.md` lines ~150-155) to find the likely-correct SHA, then either correct
the citation or, if no such commit is found at all, flag the "fix IS live" claim itself as unverified and re-open
follow-up on whatever the original SIGABRT crash-loop symptom was.

## Todos

- [ ] [REVIEW] P3. Find the real commit the 2026-07-25T06:23Z slot-2 check-in meant to cite (search agent-orchestrator
      history for the `post_worker_init`/`faulthandler.enable()` change described in
      `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s surrounding context), then either correct the citation in that
      doc or, if unfindable, flag the "fix IS live" claim as unverified and check whether the original SIGABRT symptom
      needs re-investigation.

## Progress Log

- **na-eligibility-audit 2026-08-01**: RECLASSIFY, `assigned_vm: NA` → `planning` — the todo is fully bounded: the cited
  SHA (`agent-orchestrator@7ba17e2`) was independently verified to actually exist as `deployment-api@7ba17e2a4e9` (a
  one-word repo mislabel, not a fabrication — `git cat-file -t 7ba17e2` in the deployment-api clone resolves cleanly and
  the commit message matches this doc's own fix description word-for-word). The remaining action (correct the citation
  string in the archived progress-log entry) is a determinable, worker-executable fact, not a judgment call.
  Conflict-check (`ao-dispatch-batch-naming-and-conflict-check.md` § 3) run against infrastructure_master's active
  `assigned_vm: planning` docs and the cross-cutting consolidated closeout — one incidental mention in
  `bucket_iam_write_protection_per_tier_2026_06_09.md` cross-references the same underlying SIGABRT investigation for an
  unrelated Cloud Run cold-start issue, not this citation-fix todo itself — zero genuine claim overlap, cleared.
  `doc_type: issue` — exempt from the finalize-plan-coverage rule (`check_finalize_plan_coverage.py` only globs
  `plans/active/*.md`, not `plans/active/issues/*.md`), no companion finalize doc authored.
