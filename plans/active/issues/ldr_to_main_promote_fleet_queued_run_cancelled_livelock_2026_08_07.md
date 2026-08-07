---
doc_type: issue
title:
  ldr-to-main-promote-fleet stuck 2+ hours — every queued run cancelled before starting, likely account-wide
  GitHub-hosted concurrent-job saturation
summary: >-
  Since ~2026-08-07T12:00Z, every ldr-to-main-promote-fleet run (both schedule and workflow_dispatch triggers, from
  multiple concurrent sessions) shows conclusion=cancelled with ZERO jobs ever started (gh run view shows an empty JOBS
  list). concurrency.cancel-in-progress is false, so this isn't the usual cancel-in-progress churn — a run only gets
  superseded while still QUEUED, meaning no run has actually been allocated a ubuntu-latest runner in 2+ hours.
  promote-fleet-startup-failure-monitor.yml (the workflow meant to catch exactly this) reports success throughout — its
  failure signature doesn't cover "queued forever, never starts," a coverage gap of the same class found earlier today
  in ci_failure_watcher.py. Leading hypothesis (not confirmed): this session (an interactive /ci-reconcile pass) and
  other concurrent sessions on the same GitHub account generated an unusually large burst of parallel Actions activity
  (many quality-gates.sh runs, many gh workflow run dispatches across dozens of repos) that may have saturated an
  account-wide concurrent GitHub-hosted-runner job limit, starving this workflow of a runner slot indefinitely. Net
  effect: no repo has promoted from live-defi-rollout to main since ~12:00Z, which also blocks live-verifying the
  semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md fix end-to-end (fix is shipped and correct, but no tag
  can mint until a real promotion happens).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promotion-lag, contention, github-actions, monitoring-gap]
related:
  [
    /plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md,
    /plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /plans/active/issues/ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: "ci-reconcile sweep, 2026-08-07, waiting on semver-agent fix live verification"
resolved_by:
locked_by:
locked_since:
context_scope:
  [.github/workflows/ldr-to-main-promote-fleet.yml, .github/workflows/promote-fleet-startup-failure-monitor.yml]
---

# ldr-to-main-promote-fleet stuck — queued runs cancelled before ever starting

## What was measured (live, 2026-08-07, ~12:00Z-14:24Z)

- Every run in this window: `status=completed conclusion=cancelled`, `gh run view <id>` shows an EMPTY jobs list (no job
  ever started, not a mid-run cancellation).
- Mix of `event=schedule` (every 5 min, expected) and `event=workflow_dispatch` (multiple, from at least this session's
  own agents AND at least one other concurrent session — `14:00Z` and `14:15Z` workflow_dispatch events fired after this
  session stopped dispatching new agents).
- `concurrency.cancel-in-progress: false` on this workflow — confirmed in source. A queued (not started) run being
  superseded by a newer trigger is normal GitHub Actions concurrency-group behavior regardless of this flag (the flag
  only protects an already-IN-PROGRESS job); what's abnormal is that NOTHING has transitioned queued→in_progress in 2+
  hours despite `runs-on: ubuntu-latest`, which should have ample hosted capacity.
- `promote-fleet-startup-failure-monitor.yml` (5 most recent runs, spanning this exact window) reports `success`
  throughout — it is not catching this failure mode.
- Fleet-wide effect: `batch-live-reconciliation-service` main is 267 commits behind live-defi-rollout with no open
  promote PR; `promotion_lag_monitor.py` did not flag it as lagging yet (likely still inside its own grace window).

## Not fixed autonomously — why

The leading hypothesis (account-wide GitHub-hosted concurrent-job saturation from this session's own unusually high
parallel CI volume) is plausible but unconfirmed — I don't have visibility into the account's actual Actions capacity/
usage dashboard from `gh`/`gcloud`. If true, this should self-resolve once concurrent load drops and needs no code
change. If false (something is actually broken, e.g. a runner-group misconfiguration), it needs investigation with
account-admin visibility this session doesn't have. Recommend re-checking after this session's own concurrent activity
has fully wound down before concluding a code fix is needed.

## Todos

- [ ] [DEVOPS] P1. Re-check whether this has cleared on its own once concurrent Actions load across the account has
      settled. If still stuck with genuinely nothing else running concurrently, escalate to account-admin visibility
      (GitHub billing/usage dashboard) to confirm or rule out a concurrent-job cap.
- [ ] [DEVOPS] P2. If confirmed as account-wide job-limit contention: consider whether
      `promote-fleet-startup-failure-monitor.yml` should be hardened to also catch "queued, never started" as its own
      failure signature (same class of gap as `ci_failure_watcher.py`'s glue-starvation/escalation-label bugs found
      earlier today).
