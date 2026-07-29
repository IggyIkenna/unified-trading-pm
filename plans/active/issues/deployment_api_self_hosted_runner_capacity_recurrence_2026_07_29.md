---
doc_type: issue
title:
  deployment-api's quality-gates-v2 recurred into the fleet-wide self-hosted-runner capacity crisis a 2nd time — the
  RAM-governor-based restore (a63f255) did not hold; re-reverted to ubuntu-latest
summary: >-
  Responding to an `ldr_qg_failure` escalation (`agt-3c6a0b`, no PR, `#0`) for `deployment-api` at commit `5d157d6c`.
  Confirmed NOT a code regression: local `bash scripts/quality-gates.sh` passed clean in ~100s at the current
  `live-defi-rollout` HEAD (`a8c20e1`) on an unconstrained 61GB/16-core host. Meanwhile 6 consecutive `quality-gates-v2`
  `workflow_dispatch` runs on the actual self-hosted `glue-ip-172-31-5-118-1` runner failed over ~12h (20min-4h35m
  each), with the exact signature already tracked in
  `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`: the `checks` leg's typecheck
  killed by `[qg-governor-watchdog] ... host RAM pressure >= 80% for 2 consecutive checks — sending SIGTERM` (a
  self-scoped abort, not a timeout), and the `tests` leg dying via a `pytest-xdist` `INTERNALERROR` (crashed worker)
  after 96 minutes wall-clock (`2788 passed` before the crash — not a real test failure, a worker death).
  `deployment-api` already hit this exact class once before (escalation `agt-b03e9f`, 2026-07-28, fixed via the
  precedented revert-to-`ubuntu-latest` at `deployment-api@3df07f9`) — but `a63f255` (2026-07-28 15:45 UTC, ~4.5h before
  this recurrence's first failing run) re-enabled self-hosted on the stated premise "RAM-aware reservation governor now
  live". The governor (visible in this run's own logs: `[qg-governor] deployment-api reserved 1768MB (ADMIT) after 24s`)
  IS live and did admit the run — but its own watchdog then SIGTERM'd it anyway once REAL host RAM crossed 80%, because
  that pressure came from OTHER concurrent jobs/sessions on the same shared box, which the per-job reservation
  accounting cannot see or control. So the governor solves over-admission by THIS job, not contention caused by
  everything else on the host — a real gap, not evidence the crisis is resolved. Re-applied the same precedented fix:
  reverted `self_hosted_runner_labels` + all 3 `runs-on: [self-hosted, glue]` lines back to `ubuntu-latest` in
  `deployment-api/.github/workflows/quality-gates-v2.yml` (`deployment-api@8561af10`) — this catches one job
  (`notify-ci-watcher`) that neither `3df07f9` nor `a63f255` explicitly touched in their diffs (it was on self-hosted
  continuously since `c19edcc`'s original Phase-7 rollout). Verified live: fresh `workflow_dispatch` run dispatched
  post-fix.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity-planning, ldr-qg-failure, deployment-api, recurrence]
related:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
created: 2026-07-29
priority: P2
parent_epic: infrastructure_master
source: "cicd agent, slot-3, escalation agt-3c6a0b, ldr_qg_failure on deployment-api, 2026-07-29"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by: "deployment-api@8561af10"
locked_by:
locked_since:
---

# deployment-api self-hosted-runner capacity recurrence (2nd instance)

## Why a new doc instead of appending to the master crisis doc

`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` is the correct SSOT for this issue CLASS and already
carries 10+ corroborating instances (including `deployment-api`'s first one) — but it is currently at exactly **1000
lines**, the hard cap (`scripts/plan-hygiene/check_line_caps.sh`). A file touched by a commit must not be over its cap,
so appending there would fail the PM hygiene gate. Filing this narrow, cross-referencing doc instead of forcing another
append; **flagging for whoever next does a hygiene/reconciliation pass**: that master doc is due a split (e.g. hoist the
`## Progress Log` history into a dated sub-doc, keep the live problem statement + recommended-fix section in the main
doc) — not something in scope for this one-shot `ldr_qg_failure` escalation to do itself.

## What I found

- `deployment-api`'s `quality-gates-v2` on `live-defi-rollout` failed 6 consecutive `workflow_dispatch` runs
  (`30414484359` through `30429820488`, 2026-07-28 20:27 → 2026-07-29 06:56 UTC), spanning commits `5d157d6c` (the
  escalation's named commit) through `8c639b2` (2 commits behind current HEAD at investigation time).
- Two distinct failure signatures across those runs, both consistent with host contention, not code:
  - `checks` leg: `basedpyright` admitted by `[qg-governor]` (reserved 1768MB) then SIGTERM'd by
    `[qg-governor-watchdog]` for sustained host RAM pressure >= 80% — `❌ Type check FAILED/timeout (exit=241)`.
  - `tests` leg: `pytest-xdist` `INTERNALERROR> AssertionError: (..., <WorkerController gwN>)` — a worker process died
    mid-suite (`2788 passed, 1 failed` — the "failure" is the crash, not a real assertion) after 5782s (96min); normal
    full-suite runtime elsewhere in this session was ~100s unconstrained.
  - A separate, faster-failing run (`30418508682`, head `23516a7`) hit a real-but-already-fixed test bug
    (`test_health_flags_recent_failures_dup_builds_and_registry_sprawl` `StopIteration`) — that HEAD predates
    `cf55369`'s fix for the same test; not relevant to the current HEAD, noted only to avoid double-counting it as a 3rd
    failure class.
- Local reproduction at current HEAD (`a8c20e1`) on the (unconstrained, 61GB/16-core) planning VM: full
  `bash scripts/quality-gates.sh` passed in ~100s, twice (once pre-fix to confirm the code baseline, once post-fix
  `--no-fix` on the workflow-only diff). Conclusively rules out a code/test regression.
- `git log` on `deployment-api/.github/workflows/quality-gates-v2.yml` shows the flip history: `c19edcc` (Phase-7
  self-host rollout, 2026-07-27) → `3df07f9` (revert to ubuntu-latest, escalation `agt-b03e9f`, 2026-07-28 05:27 UTC) →
  `a63f255` (restore self-hosted "RAM-aware reservation governor now live", 2026-07-28 15:45 UTC) → this doc's fix,
  `8561af10` (revert again, 2026-07-29).
- `a63f255`'s diff only touched 3 of the file's 4 self-hosted `runs-on` sites (input + `escalate-ldr-qg-failure` +
  `dispatch-cloud-build`); `notify-ci-watcher` (added by `f02b3b3`, flipped to self-hosted by `c19edcc`) was never
  explicitly touched by either `3df07f9` or `a63f255` and stayed self-hosted throughout. My fix reverts all 4 — the fix
  commit's blob hash for this file now matches the post-`3df07f9` blob exactly (`e5cfdad`), i.e. a clean, complete
  return to the known-good state.

## Why this matters

`a63f255`'s premise — that the host-adaptive RAM governor
(`/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`) closes the capacity gap — is only partially true. The
governor's own log line proves it ran and admitted the job within its own accounting (`reserved 1768MB (ADMIT)`), but
its watchdog then killed the job anyway because REAL host RAM pressure (driven by concurrent self-hosted-runner jobs
from OTHER repos, plus interactive AO slot sessions on the same shared VM — see the master doc's iowait/swap findings)
crossed 80%. A per-job reservation system cannot prevent contention from processes outside its own accounting. **This is
not evidence the crisis is resolved fleet-wide** — any other repo restored to self-hosted on the same premise should be
considered equally at risk of the same silent recurrence until the shared host's actual capacity (not just admission
accounting) is verified durable under real fleet load.

## Evidence

- Local pre-fix QG pass: `.qg_last_passed_sha=a8c20e191ed3aeb16956a6876bec2dfe1c7b5ae4`, "ALL QUALITY GATES PASSED
  (103s)".
- Local post-fix QG pass (workflow-only diff, `--no-fix`): "ALL QUALITY GATES PASSED (98s)", same sentinel SHA.
- Fix commit: `deployment-api@8561af10` ("fix(ci): revert self-hosted-runner flip for deployment-api (2nd recurrence) —
  fleet-wide capacity crisis"), pushed to `origin/live-defi-rollout` via
  `quickmerge --agent --files '.github/workflows/quality-gates-v2.yml'`.
- Post-fix verification: fresh `workflow_dispatch` run `30437785107` dispatched against the fixed HEAD; see this
  escalation's `/done` evidence for the completed conclusion (polled to completion before declaring the escalation
  resolved).

## Follow-up

- [ ] [REVIEW] P2. When the master crisis doc's `[SCRIPT] P0 allowlist-cleanup todo` (referenced in its
      `market-data-processing-service` progress-log entry) is eventually actioned, cross-check whether `deployment-api`
      should be REMOVED from `scripts/workflow-templates/self-hosted-qg-repos.txt` entirely (not just hand-reverted in
      its own copy) so a future template rollout doesn't silently re-flip it a 3rd time the same way `a63f255` did — the
      per-repo hand-edit fixes the symptom but the shared allowlist is still the source-of-truth a rollout would read
      from.
- [ ] [REVIEW] P3. `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` is at its 1000-line hard cap — due a
      split (hoist `## Progress Log` history to a dated sub-doc) at the next PM hygiene/reconciliation pass.
