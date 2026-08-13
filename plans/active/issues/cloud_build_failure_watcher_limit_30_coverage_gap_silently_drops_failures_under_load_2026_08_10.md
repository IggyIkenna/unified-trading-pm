---
doc_type: issue
title:
  "cloud-build-failure-watcher's fixed --limit=30 fetch silently drops a failing build from its own declared 20-minute
  lookback whenever fleet-wide Cloud Build volume is high — root cause of a 5+ hour silent
  uts-prod-data-status-rollup-svc deploy blocker never paging Slack"
summary: >-
  While root-causing why `uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md`'s 7
  consecutive Cloud Build failures (2026-08-10T14:58Z-20:20Z) never paged `#ci-failures`, found and fixed a real bug in
  `cloud-build-failure-watcher.yml`: `gcloud builds list --limit=30` (both the regional and global pools) can return a
  page whose OLDEST entry is much newer than the watcher's own declared 20-minute `LOOKBACK_MINUTES` window — the
  python-side time filter only ever sees what gcloud actually returned, so a build that fell off the --limit=30 page
  before the filter runs is silently indistinguishable from "did not fail." Measured live 2026-08-10 ~23:00Z: the oldest
  of the top-30 most-recent Cloud Builds (either pool) was only ~55 MINUTES old at that moment — meaning --limit=30
  could not reliably cover even ONE 20-minute lookback tick, let alone survive a burst. Confirmed via a REAL miss: a
  deployment-api Cloud Build failed at 15:20:28Z, squarely inside the 15:23:06Z watcher tick's own [15:03,15:23]
  lookback window, and that exact tick's job log shows "No failed Cloud Builds in the last 20m across 60 recent
  build(s). All clear." — the watcher ran successfully, authenticated correctly, and reported a false all-clear because
  the failing build was never even fetched.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, alerting, slack, monitoring, coverage-gap, silent-failure, data-pipeline-alerts]
related:
  [
    /plans/archive/2026_08/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md,
    /codex/04-architecture/ci-alerting.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-10
author: claude-agent
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: unified-trading-pm@5078a6c31e # CORRECTED 2026-08-12 (/plan-reconcile): filled from git log — "fix(ci): raise cloud-build-failure-watcher's --limit=30 coverage gap..." (2026-08-11)
source:
  User asked, after the uts-prod-data-status-rollup-svc deploy blocker was fixed, why the 5+ hour silent failure never
  paged data-pipeline-alerts or any CI/live Slack channel, and to diagnose + fix it via /autonomous.
context_scope:
  [
    .github/workflows/cloud-build-failure-watcher.yml,
    /plans/archive/2026_08/issues/uts_prod_data_status_rollup_svc_container_startup_failure_blocks_deploy_2026_08_10.md,
  ]
---

## What was found

`cloud-build-failure-watcher.yml` (Gap 2 of `cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md`) polls
Cloud Build every ~hour, looking back `LOOKBACK_MINUTES=20`, and pages `#ci-failures` CRITICAL for any
FAILURE/TIMEOUT/INTERNAL_ERROR/EXPIRED build in that window. It is the ONLY mechanism that watches Cloud Build directly
(GCB image builds run outside GitHub Actions, so `ci-failure-watcher` never sees them). This mechanism genuinely worked
for a sibling incident the SAME day — `mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md` records it paging
CRITICAL for a market-tick-data-service build at 13:32Z — which is what made the deployment-api silence so confusing:
the watcher clearly CAN and DOES page.

The actual bug: the two `gcloud builds list` calls (regional + global) each cap at `--limit=30`, ordered newest-first,
with NO server-side time filter (the workflow's own comment explains why: "server-side create_time filters proved flaky
across regions, so the time window is enforced in python below"). The python filter is correct — it does check
`createTime >= cutoff` — but it can only filter what gcloud actually returned. When fleet-wide Cloud Build throughput
exceeds roughly 1 build/minute (very plausible in this workspace given the constant multi-repo CI/CD activity observed
all session), the 30 most-recent builds in either pool can be younger, in aggregate, than the 20-minute lookback itself
— so a real failure sitting just past the --limit=30 page boundary is fetched by NEITHER query and never reaches the
time filter at all. It doesn't fail the filter; it's simply never seen.

**Direct proof, live, 2026-08-10 15:23:06Z tick**: the deployment-api build that failed at 15:20:28Z was inside this
tick's own declared [15:03,15:23] window. The job's `poll` step log reads:
`No failed Cloud Builds in the last 20m across 60 recent build(s). All clear.` — 60 = 30 regional + 30 global,
confirming the cap was hit and the target build simply wasn't in either page.

**Measured margin, live, ~23:00Z (unrelated moment, to gauge typical fleet load)**: the oldest of the top-30 regional
builds was ~55 minutes old — barely 2.75x the 20-minute lookback, and this was NOT even during an unusually busy window.
Raising the fetch to `--limit=150` per pool pushed the same measurement to ~6.5 hours of coverage — a ~19x margin over
the 20-minute requirement, healthy headroom even against a 3-5x burst.

## Why it matters

- This is the SAME class of bug the "silent config-rejection" half of this watcher was originally built to catch (a
  failure invisible to the developer) — except this time the watcher ITSELF is the blind spot, and it can't self-report
  a miss it doesn't know it made. A fixed `--limit=N` with no coverage self-check is a silent-failure time bomb that
  gets MORE likely to fire as the fleet's build volume grows, not less.
- Directly caused a real, 5+ hour production deploy blocker (`uts_prod_data_status_rollup_svc_...`) to go completely
  unnoticed until surfaced by an unrelated task.
- `data-pipeline-alerts` was never the right channel for this class of failure in the first place (that channel is for
  DATA-correctness DP-* alerts, not CI/CD build failures) — the correct channel, `#ci-failures`, DOES have a working
  pipe for Cloud Build failures; the pipe itself just had a capacity bug.

## What was done

Fixed both the immediate gap and its recurrence risk:

1. **Raised `--limit` 30 -> 150** for both the regional and global `gcloud builds list` calls — verified live this gives
   ~19x margin over the 20-minute lookback under normal load (see measurement above).
2. **Added a coverage-gap self-check** (new, not previously present): after fetching, compute the OLDEST `createTime`
   actually returned by each pool. If a pool's oldest fetched build is still newer than the lookback cutoff, the fetch
   may not have reached far enough back to guarantee full coverage — this now triggers its own CRITICAL alert
   (`:warning: COVERAGE GAP...`) distinct from (and in addition to, if both occur) a real build failure, so a FUTURE
   volume spike that outpaces even 150 can never repeat this exact silent-miss class again — it will page "I might have
   missed something" instead of falsely reporting "all clear."
3. Did NOT re-attempt server-side `createTime` filtering — the existing comment already documents that path as
   tried-and-found-flaky; re-litigating it wasn't warranted in scope for this fix.

## Todos

- [x] [CI] P1. Fix `cloud-build-failure-watcher.yml`'s `--limit=30` coverage gap: raise the fetch size + add a loud
      coverage-gap self-check. Done-when: QG green, shipped, and the fix is live on the branch the schedule trigger
      actually reads (`main` — see the workflow's own DEFAULT-BRANCH GOTCHA comment).
- [ ] [CI] P3. Live-verify the coverage-gap self-check actually fires correctly on a real future tick where fleet load
      pushes the pool's oldest fetched build newer than cutoff (a synthetic/forced test, or opportunistic observation) —
      not urgent, the logic was traced + syntax-validated but not executed against a live gap condition this session.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- **2026-08-10 (interactive session, /autonomous)**: root-caused live via direct comparison of the 15:23:06Z watcher
  tick's job log against the actual failing build's timestamp, then confirmed the mechanism by directly measuring the
  top-30/top-150 fetch depth against wall-clock time. Fixed + QG'd + shipped same session (see `resolved_by` once the
  quickmerge lands). This workflow only fires from `main` (GitHub `schedule:` triggers are default-branch-only) — the
  standing LDR->main promote carries it there automatically; no manual dispatch needed for the schedule to pick it up,
  though a `workflow_dispatch` run can verify sooner if desired.
