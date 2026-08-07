---
doc_type: issue
title: >-
  ci_failure_watcher.py had two real bugs found while chasing why a stuck promotion PR went silent instead of re-paging
  after AO's escalation system had already partially fixed it: (1) detect_glue_starvation hardcoded to scan only
  unified-trading-pm's own glue runner pool, now stale since image-build-validate.yml is fleet-wide since 2026-08-06;
  (2) the escalation-dispatched label used as a permanent, reason-blind idempotency marker with no re-arm when the
  blocking reason changes
summary: >-
  Two independently-diagnosed bugs in the CI failure watcher (`scripts/repo-management/ ci_failure_watcher.py`), found
  while investigating why `batch-live-reconciliation-service#315` (a promotion PR AO had already partially fixed earlier
  the same day) went silent instead of re-paging when it became blocked again for a completely unrelated reason.

  1. `detect_glue_starvation` only ever scanned `unified-trading-pm`'s own `run list` for stuck
     glue-labelled QUEUED jobs. That was correct while PM was the only repo whose OWN workflows
     referenced `runs-on: [self-hosted, glue]` — but `image-build-validate.yml` was extracted out of
     PM into the public `unified-trading-ci` repo on 2026-08-06
     (`shared_ci_workflow_repo_extraction_2026_08_06.md`) and is now invoked BY every fleet repo's
     promotion PRs via `workflow_call`. A reusable workflow's runner matching resolves against the
     CALLING repo's own run queue (the run is created in the caller), not the reusable workflow's
     host repo — so a glue-labelled job stuck QUEUED on ANY fleet repo's promotion PR would surface
     in THAT repo's `run list`, never PM's, and a PM-only scan would silently miss it entirely (see
     the sibling `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` incident
     this generalizes the detector for).
  2. The `escalation-dispatched` GitHub label was used as a blunt, PERMANENT per-PR idempotency
     marker with no re-arm when the blocking reason changes. Concretely:
     `batch-live-reconciliation-service#315` was correctly escalated and fixed for a RUNS_ON
     workflow-yaml bug earlier the same day (which added the label) — then it became blocked again
     for an UNRELATED dead-glue-runner stuck-QUEUED-check reason, and the watcher stayed silent
     because the label was already present. `stuck_prs_to_page`/`escalate_stuck_prs` treated
     "carries the label" as "handled forever", so neither the Slack page nor a fresh
     escalate-to-orchestrator dispatch fired for the new, different reason.
status: resolved
nature: issue
asset_group: [cross-cutting, ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, ci-failure-watcher, escalation, glue-runners, idempotency, fleet-wide, monitoring, regression]
related:
  [
    /plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md,
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  "sub-agent dispatch chasing why batch-live-reconciliation-service#315 went silent after an earlier same-day AO
  escalation, 2026-08-07"
resolved_by: "unified-trading-pm@ace3f5ea2417c4af0256f6fbbf30dda47338cb25 (live-defi-rollout)"
locked_by:
locked_since:
context_scope: [/plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md]
---

> **🟢 ARCHIVED 2026-08-07 — RESOLVED** (status: resolved, 0 open todos, unlocked). Archived by cicd wall-resolution
> (`agt-6f2b99`) as part of the `check_terminal_status_archived` ratchet fix.

# ci_failure_watcher.py: PM-only glue scan + permanent escalation label

## Fix applied

**Bug 1 — `detect_glue_starvation` generalized to the fleet.** Signature changed to
`detect_glue_starvation(repos: list[str], now, queued_minutes=...)`; it now loops `run list` over every repo in the
canonical fleet list (`REPOS` from `pin_branch_protection_rulesets`, the same list already used by the billing-block and
transition detectors) instead of only `unified-trading-pm`. The returned dict gained a `repos` field (comma-joined,
sorted) naming which repo(s) actually have a starved job, and the Slack alert message now names that instead of
hardcoding `unified-trading-pm`. `main()`'s call site updated to pass `repos` (the same fleet list already resolved
there).

**Bug 2 — escalation idempotency scoped to the blocking reason, not just label presence.** Added:

- `_blocking_check_names(rollup)` (pure) — extracts the check name(s) in a PR's `statusCheckRollup` that are NOT a clean
  success (a failure, `action_required`, a pending commit status, or a check with no conclusion/state reported yet — the
  never-draining-QUEUED symptom).
- `_blocking_signature(state, blocking_checks)` (pure) — a short deterministic hash of `mergeStateStatus` + the sorted
  blocking check names, stored as `blocking_signature` on every `detect_stuck_prs` result.
- `_pr_escalation_suppressed(repo, number, signature)` (replaces `_pr_has_escalation_label`) — suppresses only when the
  PR carries BOTH the `escalation-dispatched` label AND a matching reason-marker comment for the CURRENT signature. A
  labelled PR with NO reason-marker comment at all (escalated before this fix shipped, or via the label-only
  `agent-runner.yml` path used for non-CI-watcher wall types) is grandfathered — stays suppressed exactly as before, so
  shipping this fix cannot itself trigger a re-page/re-escalate storm across every PR that already carries the label.
  Once a PR has a reason-marker from this mechanism, a signature MISMATCH re-arms it.
- `_post_escalation_reason_marker(repo, number, signature)` — posts a hidden
  `<!-- ci-watcher:escalation-reason:<sig> -->` marker comment at dispatch time (called from `_dispatch_escalation`),
  deduped against existing comments so a PR parked in the 503/no-headroom retry loop gets exactly one marker per reason,
  not one per `*/15` retry tick.

Deliberately did NOT change the `escalation-dispatched` label string itself or its application site
(`escalate-to-orchestrator.yml` labels on confirmed spawn) — `agent-runner.yml` and the dep-update-conflict-resolution
flow key off that exact label for their own, unrelated, presence-only dedup (`rg -l "escalation-dispatched"` checked
before deciding the approach) and must not be affected.

`stuck_prs_to_page`, `conflict_prs_to_escalate`, and `blocked_failing_prs_to_escalate` (the pure selectors) are
UNCHANGED — only their IO-derived `already_escalated` set (`_already_escalated_set`) and `escalate_stuck_prs`'s
per-candidate gate now call the reason-aware check.

## Tests added/adjusted

- `tests/unit/test_ci_failure_watcher_glue_starvation.py`: `_router` gained a `runs_by_repo` mode (per-repo run-list
  fixtures); all existing single-repo tests updated to pass `PM_REPO = [ "unified-trading-pm"]`; added
  `test_scans_every_fleet_repo_not_just_pm`, `test_pm_only_scan_would_have_missed_a_non_pm_repo` (a negative-control
  companion proving the fleet scan is what catches it), and `test_starved_jobs_across_multiple_repos_are_aggregated`.
- `tests/unit/test_ci_failure_watcher_core.py`: `TestBlockingCheckNames` + `TestBlockingSignature` (pure-function
  coverage), plus `test_blocking_signature_differs_by_which_check_is_blocking` and
  `test_blocking_signature_stable_for_the_same_reason` on `detect_stuck_prs`.
- `tests/unit/test_ci_failure_watcher_escalate.py`: `TestPrEscalationSuppressed` (grandfathered legacy label / matching
  marker stays suppressed / mismatched marker re-arms / gh-error fails open), `TestPostEscalationReasonMarker` (posts
  once, deduped on retry), and `TestAlreadyEscalatedSetReasonScoped` — the end-to-end regression test reproducing
  `batch-live-reconciliation-service#315` directly: `test_pr_labelled_for_reason_a_pages_again_for_unrelated_reason_b`
  and `test_pr_labelled_for_the_same_reason_stays_suppressed`.

## Progress Log

- **2026-08-07**: found, root-caused, fixed, and tested in one pass via sub-agent dispatch while chasing why
  `batch-live-reconciliation-service#315` stayed silently BLOCKED after an earlier same-day AO escalation had already
  fixed its original RUNS_ON failure. `quality-gates.sh --no-fix` green (1783 passed, 0 failed); shipped
  `unified-trading-pm@ace3f5ea24` via quickmerge onto `live-defi-rollout`.
