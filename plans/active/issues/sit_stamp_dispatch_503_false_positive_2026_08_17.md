---
doc_type: issue
title: >-
  full-workspace-sit "failures" were GitHub API 503s in the SIT_VALIDATED stamp-dispatch step, not broken cross-repo
  invariants — escalation context wrongly framed it as "identify which pending repo broke the suite"
summary: >-
  A cluster of full-workspace-sit runs in system-integration-tests (2026-08-17 ~13:17-17:40Z) were reported/escalated
  as `sit_failure` with the hypothesis "identify which pending repo broke the cross-repo invariant suite". Direct log
  inspection of 3 runs across the cluster (14:40, 17:40, and the eventual 19:12 green) shows all 26 cross-repo
  invariants passed EVERY time ("✅ full-workspace SIT GREEN — all cross-repo invariants pass") — the job-level
  FAILURE came entirely from a downstream step that dispatches `ci-status-update` repository_dispatch events to stamp
  each pending repo SIT_VALIDATED. That step hit `HTTP 503` from the GitHub API on ~15-16 of ~16 repos simultaneously
  (plus a few ci-status-update.yml runs that themselves failed), which is GitHub-side transient unavailability, not a
  code defect in any pending repo. No pending repo needed (or got) a fix; the cluster self-resolved once GitHub's API
  stabilized (3 consecutive green runs 18:45-19:12Z, stamping included).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests, unified-trading-pm]
scope: [engineer]
tags: [ci-cd, sit, false-positive, github-api-503, stamp-verification, escalation-context]
related:
  - /codex/08-workflows/ci-cd-flow.md
  - /codex/06-coding-standards/integration-testing-layers.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
created: 2026-08-17
author: cicd (escalation agt-0e693e, slot 3)
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
archive_exempt:
resolved_by:
last_updated: 2026-08-18
locked_since:
context_scope: [system-integration-tests/scripts/run_cross_repo_invariants.sh, /codex/08-workflows/ci-cd-flow.md]
source: >-
  cicd escalation agt-0e693e (wall_type=sit_failure, dispatched from unified-trading-pm run 32040085860, itself
  triggered by system-integration-tests full-workspace-sit run 32039884966 @ 2026-08-17T14:40:56Z). Investigated by
  reading the actual job logs of 3 runs spanning the failure cluster instead of trusting the escalation's own
  hypothesis.
---

# SIT stamp-dispatch 503s misclassified as invariant failures

## What actually happened

`full-workspace-sit` (system-integration-tests, dispatched by `sit-gate.yml`/`sit-debounce-trigger.yml`) runs one job,
`cross-repo-invariants`, with two logically separate steps:

1. `run_cross_repo_invariants.sh` — the 26 actual cross-repo invariants. Prints its own GREEN/RED summary and exits
   accordingly.
2. A stamping step that, for every repo whose invariant PASSED, POSTs a `repository_dispatch` (`ci-status-update`) to
   mark it `SIT_VALIDATED`, then polls the triggered `ci-status-update.yml` run for `conclusion=success`. Any dispatch
   HTTP status != 204, or a polled run that doesn't conclude `success`, is collected into `STAMP_FAILURES` and the step
   `exit 1`s — which flips the WHOLE JOB (and therefore the whole run) to `conclusion=failure`, indistinguishable at
   the run-conclusion level from a genuine invariant regression.

## Measured evidence

| Run (system-integration-tests) | Created (UTC) | Conclusion | Invariant summary | Stamp step |
|---|---|---|---|---|
| 32039884966 (my escalation's trigger) | 2026-08-17T14:40:56Z | failure | ✅ all 26 invariants pass | 16 `STAMP_FAILURES` — mostly `dispatch-http-503`, a few `run-<id>-conclusion-failure` |
| 32051402995 | 2026-08-17T17:40:47Z | failure | ✅ all 26 invariants pass | same shape — `dispatch POST for <repo> returned HTTP 503` for ~15 repos in sequence |
| 32059081596 (first clean run after the cluster) | 2026-08-17T19:12:43Z | success | ✅ all 26 invariants pass | stamped clean |

Every run in the 13:17-17:40Z failure cluster shows the identical signature: invariant summary 100% green, stamp step
failing on a wide simultaneous spread of `HTTP 503` responses from `api.github.com` — the signature of a GitHub-side
transient outage/rate-limit, not a per-repo code problem. `grep`ing this workspace's issue corpus for
`dispatch-http-503` / `stamp verification failure` turned up nothing prior — this looks like the first time this
specific class was diagnosed down to the log line rather than assumed to be a real invariant break.

## Current state (verified live, 2026-08-18)

- `main` branch `workspace-manifest.json` `staging_status`: `locked: false`, `locked_reason: "SIT passed — validated +
  unlocked"`, `pending_repos: []`, `breaking_pending: []`, `sit_retry_count: 0`.
- 3 consecutive green `full-workspace-sit` runs (18:45, 19:01, 19:12Z on 2026-08-17); no run since — consistent with
  nothing currently pending/breaking.
- No open GitHub issue matching "SIT" in `unified-trading-pm` — the auto-filed SIT-failure issue (sit-unlock.yml's
  `add-sit-rollback` step) is not currently open.
- **No code change was made to any pending repo** — there was nothing to fix. Pushing a speculative "fix" against a
  100%-green invariant suite would have been an unjustified change against the HARD RULE (never force a fix the
  evidence doesn't call for).

## Why this is worth recording

- `sit-debounce-trigger.yml`'s `sit_retry_count` and `sit-gate.yml`'s `harness-lint` "3 consecutive failures ⇒
  persistent harness issue" heuristic both count this stamp-only failure the same as a genuine invariant break —
  burning retry budget / triggering harness-lint fix-tasks for a GitHub-side blip.
- The `sit_failure` escalation `context` template hands the responding cicd worker the hypothesis "identify which
  pending repo broke the cross-repo invariant suite" unconditionally — true for a real invariant regression, actively
  misleading here (all 26 invariants passed). A worker that pushed a "fix" on faith in that hypothesis, instead of
  reading the actual job log first, would have shipped an unjustified change.

## Follow-up

- [ ] [SCRIPT] P3. In `system-integration-tests`' full-workspace-sit stamp-verification step, when `STAMP_FAILURES` is
      non-empty but the invariant runner's own per-repo results were all PASS (no FAILED/SKIPPED invariants), emit a
      distinct signal (e.g. a `failure_class=stamp_infra_only` GitHub Actions output/annotation). Have
      `unified-trading-pm`'s SIT-failure escalation/issue-filing steps (`sit-unlock.yml`) read that signal and include
      the actual per-invariant PASS/FAIL list (or "all green — stamp-dispatch-only failure, likely transient GitHub
      API 503s") in the `escalate-to-orchestrator` `context` payload, instead of the generic "identify which pending
      repo broke it" framing, so a future cicd worker doesn't have to re-derive this from raw GH Actions logs.

## Progress Log

- 2026-08-18 (cicd, slot 3, escalation agt-0e693e): Diagnosed — all 3 sampled runs across the 2026-08-17 failure
  cluster show 100% green cross-repo invariants; the run-level failure was entirely GitHub API 503s in the
  SIT_VALIDATED stamp-dispatch step. Verified live `main` staging_status is unlocked/clean and 3 consecutive SIT runs
  went fully green (invariants + stamping) by 19:12Z the same day — self-resolved once GitHub's API recovered. No code
  fix pushed (none was needed/justified). Filed this issue for the stamp-vs-invariant failure-class disambiguation
  follow-up above; closing out the escalation as resolved-on-arrival.
