---
doc_type: issue
title:
  ldr-to-main-promote-fleet's single concurrency group starves under heavy multi-agent trigger volume — queued runs keep
  getting superseded before ever starting a job
summary: >-
  Since ~2026-08-07T11:23Z (the moment its sibling ldr-to-main-promote.yml's own runs-on flipped self-hosted→
  ubuntu-latest in the same commit, ruled out as cause — see evidence), every ldr-to-main-promote-fleet run shows
  conclusion=cancelled with ZERO jobs ever created (gh api .../jobs → total_count:0, not a mid-run cancellation).
  Account-wide GitHub-hosted concurrent-job saturation was the leading hypothesis but is RULED OUT: (1) operator
  confirmed no account-wide cap is in effect; (2) other workflows in the same repo (ci-status-update, sit-gate-stuck-
  detector, glue-pool-starvation-monitor, promote-fleet-startup-failure-monitor) ran successfully throughout the same
  window; (3) most tellingly, ldr-to-main-promote.yml — the sibling workflow dispatched by the SAME 15-min heartbeat at
  the SAME instant, verified via live SSM inspection of the orchestrator VM's systemd timer (firing exactly on its
  documented */15 schedule, no drift) — succeeded on every single run in the same window, one even mid-flight
  in_progress when checked. The heartbeat itself is fully healthy and not the cause. The asymmetry between the two
  sibling workflows is the real lead: ldr-to-main-promote-fleet is the one every per-repo agent verifying a fleet-wide
  promotion naturally triggers via workflow_dispatch (confirmed: at least 3 different agents in this session alone did
  exactly this for instruments-service, market-data-processing-service, and unified-trading-ci), while
  ldr-to-main-promote.yml (PM-only) is not a natural target for that pattern. Combined with its own native */5 schedule
  AND the 15-min heartbeat AND ad-hoc manual dispatches from potentially multiple concurrent sessions, the trigger rate
  for THIS SPECIFIC concurrency group appears to exceed whatever rate at which GitHub actually promotes a queued run to
  in_progress for it — each new arrival keeps re-winning the single queued-waiter slot before the previous one is ever
  allocated a runner. A genuine GitHub-side incident today (ARC runner pods stuck idle, job assignment failures,
  status.github.com, marked resolved) may have contributed a baseline layer of flakiness on top, but does not explain
  the sustained, isolated-to-one-workflow pattern by itself. Net effect: no repo has promoted from live-defi-rollout to
  main since ~11:23Z, which also blocks live-verifying the
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

The fix here is a design choice with fleet-wide behavioral consequences, not a mechanical patch: debouncing/rate-
limiting manual dispatches of a shared fleet-critical workflow, or changing its concurrency semantics, changes how every
agent's "did my repo promote yet" verification pattern needs to work going forward. That's worth an operator decision on
the actual mechanism (see options below), not a same-session unilateral change to CI infrastructure this central to the
whole fleet's shipping pipeline.

## Evidence chain (in order investigated, ruled out is marked)

1. ❌ RULED OUT — account-wide GitHub-hosted concurrent-job cap (operator confirmed no cap in effect).
2. ❌ RULED OUT — general GitHub-side outage (other workflows in the same repo ran fine throughout).
3. ❌ RULED OUT — heartbeat misconfiguration (live SSM check: systemd timer firing exactly on its documented `*/15`
   schedule, zero drift, both dispatches per tick succeed at the API-call level).
4. ❌ RULED OUT (as sole cause) — the same-commit self-hosted→ubuntu-latest revert (`c8cd56251e`, landed 11:23:30 UTC,
   suspicious timing match): the sibling workflow changed `runs-on` in the identical commit and works perfectly, so the
   revert itself isn't the mechanism, though its timing coincides with when the pattern was first observed.
5. ✅ LEADING, evidenced — trigger-volume asymmetry: `ldr-to-main-promote-fleet` uniquely absorbs schedule (`*/5`) +
   heartbeat (`*/15`, both workflows) + ad-hoc `workflow_dispatch` from every per-repo agent verifying its own repo's
   promotion (confirmed 3 separate agents did this today) + potentially other concurrent sessions. Its PM-only sibling
   shares the schedule+heartbeat baseline but not the ad-hoc per-repo-verification trigger pattern, and never starved.
6. Contributing, unconfirmed — a same-day GitHub Actions incident (ARC runner pods stuck idle, job assignment failures)
   may add background flakiness but doesn't explain the isolation to one specific workflow.

## Todos

- [ ] [OPERATOR] P1. Decide the fix mechanism: (a) debounce — the workflow itself checks for an already-queued/
      in-progress run of itself before accepting more dispatches (e.g. an early `gh run list --status queued` guard that
      no-ops instead of piling on), (b) rate-limit ad-hoc verification — establish a convention that agents check
      `promotion_lag_monitor.py`'s live output instead of manually dispatching this specific workflow to verify their
      repo promoted, (c) split concurrency groups per triggering source so ad-hoc verification dispatches don't compete
      with the schedule/heartbeat's own slot, or (d) something else.
- [ ] [DEVOPS] P2. Once decided: implement + verify a real promotion completes end-to-end under normal multi-agent load,
      not just in isolation.
- [ ] [DEVOPS] P2. Harden `promote-fleet-startup-failure-monitor.yml` to also catch "queued, never started for an
      extended period" as its own failure signature — it currently reports success throughout this entire incident (same
      class of coverage gap as `ci_failure_watcher.py`'s glue-starvation/escalation-label bugs found earlier
      2026-08-07).
