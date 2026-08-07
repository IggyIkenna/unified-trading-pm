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

## ACTUAL root cause found 2026-08-07 ~17:42Z — corrects the trigger-volume theory above

The trigger-volume-asymmetry theory (§ Evidence chain item 5) was **wrong as the primary cause** — the convention-rule

- schedule-trim fix shipped against it (Todo 1) did NOT clear the livelock; re-checked ~3 hours after shipping,
  `batch-live-reconciliation-service` was still 267 commits behind main, unchanged, and a fresh manually-triggered run
  still showed `total_count:0` jobs.

**The real mechanism**: `python3 scripts/cicd/glue_pool_starvation_monitor.py --repo IggyIkenna/unified-trading-pm` (the
actual script behind the `glue-pool-starvation-monitor` Slack alert — read it, don't just trust the alert text) listed
run `31176101874` ("promote-ldr-to-main", queued 344+ minutes) among 10 glue-starved jobs. Traced it directly:

```
gh api repos/IggyIkenna/unified-trading-pm/actions/runs/31176101874 →
  {"name":"ldr-to-main-promote-fleet","path":".github/workflows/ldr-to-main-promote-fleet.yml",
   "event":"schedule","head_branch":"main","created_at":"2026-08-07T11:56:22Z","status":"queued"}
gh api .../31176101874/jobs → {"name":"promote-ldr-to-main","labels":["self-hosted","glue"],"status":"queued"}
```

**This is the chicken-and-egg bug**: a `schedule:`-triggered GitHub Actions run ALWAYS uses whatever version of the
workflow file exists on the repo's DEFAULT branch (`main`) — never `live-defi-rollout`, regardless of what's on LDR
(this is a documented GitHub Actions rule, already noted elsewhere in this repo's own CLAUDE.md: "A scheduled/`push`
workflow fires ONLY from the DEFAULT branch"). The `runs-on: [self-hosted, glue] → ubuntu-latest` fix (`c8cd56251e`,
11:23:30 UTC) landed on LDR, but **had not yet promoted to `main`** — because the very promoter that would carry it
there was the thing broken. So the very next native schedule tick at 11:56:22Z fired against the STILL-OLD version of
the workflow on `main`, declaring `runs-on: [self-hosted, glue]` — a pool with permanently ZERO runners (see
`self_hosted_runner_public_repo_revert_2026_08_05.md`, todo 21 DONE). That job queued forever, waiting for a runner that
will never appear.

Because `concurrency.cancel-in-progress: false`, and GitHub Actions concurrency groups track exactly one "currently
claiming the group" run, this permanently-unstartable zombie run appears to have been occupying that single slot — so
every SUBSEQUENT trigger (even `workflow_dispatch` runs correctly using the FIXED ubuntu-latest spec from LDR) just
queued behind it and got superseded by the next arrival, forever, never getting a turn. Verified: this was the ONLY
currently-queued run of either promote workflow
(`gh api .../actions/runs --jq 'select(.name=="ldr-to-main- promote-fleet" or .name=="ldr-to-main-promote") | select(.status=="queued" or .status=="in_progress")'`
→ exactly this one run, nothing else).

**Fix applied**: `gh run cancel 31176101874` at ~17:42Z. **Live-verified working**: triggered a fresh
`gh workflow run ldr-to-main-promote-fleet.yml` immediately after — run `31203568988` reached `status: in_progress` (job
`promote-ldr-to-main: in_progress`) at 17:44:23Z — **the first non-cancelled run of this workflow all day**.

**Side finding, false-positive, filed separately below**: while investigating, found `glue-runner-crash-loop- watchdog`
paging CRITICAL on 4 repos' (e2e-testing, strategy-service, market-tick-data-service, ml-service) dedicated self-hosted
runners for "continuously active >3h, likely hung." Live SSM check (`systemctl status` + `ps`) on `i-042a6332509482556`
showed **3.3s total CPU time** across 3h+ of "active" runtime for all 4, and GitHub's own runner API confirms
`status:online, busy:false` for each — these are healthy IDLE runners, not hung processes; the watchdog's ">10800s
active" heuristic doesn't check actual CPU/busy state, so it false-positives when overall job throughput craters (as it
did fleet-wide during this incident) rather than when a runner is actually wedged. Did NOT restart these services —
restarting a healthy runner achieves nothing and would just reset the false-positive's timer. Filed as its own
coverage-gap todo below (same class as `ci_failure_watcher.py`'s bugs and `promote-fleet-startup-failure-monitor.yml`'s
blind spot, all found 2026-08-07).

**Still open**: confirm this stays clear — the operator's explicit instruction (2026-08-07) is to keep this
`/ci-reconcile` session running until a full 60 consecutive minutes pass with zero new CI alerts, not to declare victory
on one successful `in_progress` transition. If the SAME class of chicken-and-egg zombie recurs (any future workflow-file
fix that changes `runs-on:` needs to reach `main` via a working promoter before the OLD spec stops being able to
zombie-queue on the next native schedule tick — a structural risk any time this exact workflow's own `runs-on:` changes
again), the mitigation is: after any fix to a `schedule:`-triggered workflow's `runs-on:`, check for and cancel any
pre-existing queued run of that same workflow before/immediately after shipping, don't assume the fix alone is
sufficient.

## Todos

- [x] 1. ✅ [OPERATOR] P1. **Decided 2026-08-07 — ship (b) + (d)-lite now, defer (a).** Operator chose the convention
      fix + schedule trim as the immediate action; the in-workflow self-debounce (option (a) below) is deferred, gated
      on whether the problem recurs after these two land (observe via run history / live recheck, not built
      preemptively). - **(b) rate-limit ad-hoc verification — DONE.** Added a HARD RULE against
      `gh workflow run       ldr-to-main-promote-fleet.yml` used just to check promotion status, in TWO places (both
      needed — see `codex/05-infrastructure/claude-code-settings-symlink.md` for why one alone doesn't cover both AO
      workers and Task-tool sub-agents): `unified-trading-pm/cursor-configs/CLAUDE.md`'s
      `## CI verification after every push` section (auto-loaded by every AO top-level worker + interactive session) and
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`'s `## Async-wait / background work` section (pasted at every
      Task/Agent-tool sub-agent spawn, which is what actually caused 3+ of today's confirmed triggers). Both point to
      `promotion_lag_monitor.py`'s live output / `gh pr list --search "chore(promote)"` as the correct check. -
      **(mechanical, folds into (d)) trim the redundant native schedule — DONE.** `*/5` → `*/15` in
      `ldr-to-main-promote-fleet.yml`, matching `ldr-to-main-promote-heartbeat.timer`'s already-deterministic `*/15`
      cadence — the native schedule was compensating for GHA's own unreliable delivery, a problem the heartbeat already
      solves; cuts baseline trigger volume with no SLA regression (still ≤15 min worst case).
- [ ] [OPERATOR] P1 (deferred, conditional). **(a) in-workflow self-debounce** — only build this if the livelock recurs
      after the above two land. Check via: (i) run history — does `ldr-to-main-promote-fleet.yml` show a sustained run
      of `conclusion=cancelled` + empty jobs list again on any later date, or (ii) live — if you're investigating a
      fresh "no repo promoting" report, re-run this doc's own diagnostic steps first before assuming it's this same
      issue again. If confirmed recurring, add a fast lightweight first job that checks "already-queued/in-progress?"
      and exits immediately if so, keeping the concurrency-heavy job isolated from dispatch volume — needs care around
      the existing `needs:`-chained notify/arm-failed jobs, a full QG pass, and live verification under real multi-agent
      load before shipping.
- [x] 2. ✅ [DEVOPS] P1. **Real root cause found + fixed 2026-08-07 ~17:42Z — see section above.** Was a zombie queued
      run (`31176101874`) from a `schedule` trigger that fired against `main` before the `runs-on:` fix had promoted
      there, permanently occupying the workflow's one concurrency slot. Cancelled it; a fresh run immediately reached
      `in_progress` (`31203568988`) for the first time all day. NOT the trigger-volume theory from Todo 1 — that fix was
      still worth keeping (real, if secondary, load reduction) but did not by itself clear this.
- [ ] [DEVOPS] P1. **In progress, not yet closed.** Confirm the fix HOLDS for a full 60 consecutive minutes with zero
      new `ldr-to-main-promote-fleet` cancelled-with-zero-jobs runs, AND confirm at least one real repo promotion
      completes end-to-end (a `chore(promote)` PR actually merges to `main`) AND the
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` fix mints a real, verifiable tag as the final
      proof. Do not mark this doc `resolved` on the strength of one `in_progress` transition alone.
- [ ] [DEVOPS] P2. Harden `promote-fleet-startup-failure-monitor.yml` to also catch "queued, never started for an
      extended period" as its own failure signature — it currently reports success throughout this entire incident (same
      class of coverage gap as `ci_failure_watcher.py`'s glue-starvation/escalation-label bugs found earlier
      2026-08-07).
- [ ] [DEVOPS] P2. **New, 2026-08-07.** `glue-runner-crash-loop-watchdog`'s ">10800s active = probably hung" heuristic
      false-positived on 4 healthy, idle, `busy:false` runners (e2e-testing, strategy-service, market-tick-data-service,
      ml-service) during this incident's low-throughput window — add an actual CPU-time or GitHub-API `busy` check
      before paging, not wall-clock active-duration alone. Do not restart these services; they were never actually
      stuck.
