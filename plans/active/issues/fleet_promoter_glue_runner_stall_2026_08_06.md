---
doc_type: issue
title: "Fleet promoter ldr-to-main-promote-fleet stalled 3+ hours — glue runner pool depleted"
summary: >-
  Discovered while investigating sit-gate/fleet-green auto-retrigger failures (slot 12, 2026-08-06). The LDR→main fleet
  promoter (ldr-to-main-promote-fleet.yml) produced 13 consecutive cancelled runs between 19:00–22:30 UTC because only 1
  of 4 `glue`-labeled self-hosted runners was online and not busy. Each `*/5` schedule event queued a new run that
  cancelled its queued predecessor before any runner picked it up — effectively zero promotions for 3+ hours fleet-wide,
  blocking all ldr_main repos including system-integration-tests (215 commits behind main with the SIT poll-budget fix
  system-integration-tests@69b93bc staged on LDR but unreachable).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, fleet-promoter, self-hosted-runners, ldr-to-main]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-06
author: slot-12
priority: P1
parent_epic: infrastructure_master
source: ["Surfaced while investigating sit-gate fleet-green auto-retrigger failures (slot 12, 2026-08-06)."]
execution_scope: orchestrator-agent
assigned_vm: planning
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    .github/workflows/ldr-to-main-promote-fleet.yml,
    scripts/cicd/glue_runner_health_monitor.py,
  ]
---

# Fleet promoter stalled 3+ hours — glue runner pool depleted

## What I found

1. The `ldr-to-main-promote-fleet` workflow produced **13 consecutive cancelled runs** between 19:00 and 22:30 UTC on
   2026-08-06 (runs 31126553404 through 31128865834). Zero promotions completed in this window.
2. Root cause: the `glue` self-hosted runner pool was at 25% capacity. Of 4 `glue`-labeled runners, only 2 were online
   (`glue-ip-172-31-3-59-1` and `-2`), and one of those was busy with another job. The remaining 2 runners (`-3` and
   `-5`) were offline.
3. With `concurrency.group: ldr-to-main-promote-fleet` + `cancel-in-progress: false`, GitHub allows at most one queued
   run behind the in-progress one. Each new `*/5` schedule event replaced the queued run — but with no runner available,
   no run ever started, creating an indefinite cancel-treadmill.
4. Resolved when a glue runner became available: the 22:30 run (31129033588) reached `in_progress` at ~22:35 UTC.
5. Impact: system-integration-tests (215 commits behind main) and all other `ldr_main` repos were blocked from promotion
   for the entire duration. The SIT poll-budget fix (system-integration-tests@69b93bc) remains on LDR only.

## Why it matters

The fleet promoter is the single chokepoint for all LDR→main promotion. When it stalls, every `ldr_main` repo's fixes
are trapped on LDR indefinitely. The current runner pool has no headroom: 4 runners with only 2 online means any burst
of load or a single additional offline runner triggers a complete stall.

## Recommended decision

- [x] ✅ [INFRA] P1. Add a runner-health monitor for the `glue` pool: alert when fewer than N runners are online (repo:
      unified-trading-pm). Minimum viable: a scheduled workflow that counts online glue runners and posts to Slack when
      the count drops below a threshold (suggest 3). — unified-trading-pm@64c3fd63a + evidence
- [x] ✅ [INFRA] P2. Investigate why glue-3 and glue-5 are offline — restart or replace (repo: unified-trading-pm). —
      unified-trading-pm@HEAD (investigation finding: no restart/replace needed — see Progress Log 2026-08-07)
- [x] ✅ [INFRA] P2. Hardening: add a `workflow_dispatch` trigger to `ldr-to-main-promote-fleet.yml` so an operator can
      manually kick off a promotion tick when the schedule is stuck (already exists — confirmed at line 53 of
      .github/workflows/ldr-to-main-promote-fleet.yml with dry_run + only_repo inputs; no code change needed).

## Follow-ups

- [x] ✅ [INFRA] P1. **Live recurrence signal (2026-08-07, slots 2 + archive-candidates-audit):** the glue runner pool
      has been observed at genuinely 0 registered runners twice on 2026-08-07 (13:34-13:38 UTC per slot 2's finding, and
      re-confirmed via `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` returning `{"total_count": 0}` again
      during this archive sweep) — worse than the original 08-06 incident's 25% pool and the 08-07 morning 100%-online
      check. Determine whether this is the same JIT-restart-window false-positive class the 08-07 morning investigation
      ruled out, or a genuine new pool-depletion/deregistration event; if genuine, escalate per the runner-health
      monitor shipped in this doc's first todo (repo: unified-trading-pm). — unified-trading-pm@HEAD (see Progress Log
      2026-08-08)

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — promoter gate set
- `/codex/05-infrastructure/vm-launcher-runbook.md` — runner infrastructure

## Progress Log

- **2026-08-06 (slot 12)**: Filed after discovering promoter stall during sit-gate fleet-green investigation. Promoter
  self-recovered at ~22:35 UTC when a glue runner picked up the 22:30 run.
- **context-scout 2026-08-07**: populated context_scope (5 entries).
- **2026-08-07 (slot 9, fleet_promoter_glue_runner_stall-002)**: Investigated glue-3 and glue-5 offline status. GitHub
  API (`repos/IggyIkenna/unified-trading-pm/actions/runners`) confirms all 5 glue runners (`glue-ip-172-31-3-59-{1..5}`)
  are **online** and not busy as of 2026-08-07. Cross-referenced
  `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` Progress Log (2026-08-06 session): glue-3 and glue-5 were in
  the **normal JIT-runner between-job restart window** (`Restart=always`, `StartLimitIntervalSec=0`), not a real failure
  — they self-recovered within ~6 minutes, and the crash-loop watchdog was false-positiving on clean `Result=success`
  exits throughout that window. That false-positive bug was already fixed and shipped as `879e3e109`. **No restart or
  replacement was needed**: the runners recovered by design, monitoring is now correct, and the pool is fully healthy.
  SSM host-level verification not possible from `ikenna-worker` identity (consistent with all prior entries in the
  sibling issue doc); GitHub API is the authoritative signal and shows clean state.
- **2026-08-07 (slot 2, semver_agent_squash_promote_blind_to_patch_fixes investigation)**: Recurrence observed while
  verifying an unrelated semver-agent fix — `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` returned
  `{"total_count": 0, "runners": []}` (HTTP 200, not an auth artifact), checked repeatedly 13:34–13:38 UTC: genuinely 0
  runners registered, not just some offline — worse than the 08-06 incident (25% pool) and the 08-07 morning check (100%
  online). Preceding `ldr-to-main-promote-fleet` runs across roughly an hour (12:23–13:30 UTC) show a run of consecutive
  `cancelled` conclusions matching the original incident's cancel-treadmill signature (`cancel-in-progress: false`
  should queue, not cancel — something external is re-dispatching faster than any runner can pick up work, or the pool
  emptied entirely). The most recent dispatch (run `31182919694`, 13:30:06 UTC) was still `status=pending` as of 13:38
  UTC (~8 min, not yet a new multi-hour stall by itself — flagging the pattern, not overstating this one run's age). Did
  not investigate further or attempt a fix (out of scope for the semver-agent task in progress; this doc's owners
  already have the runbook). Impact: blocks LDR→main promotion fleet-wide, which in turn is delaying live-fire
  verification of 15 repos' semver-agent fix. Flagging as a live recurrence — worth a fresh look at whether this is the
  same JIT-restart-window false-positive class or a genuine new pool-depletion event.
- **archive-candidates-audit 2026-08-07 (slot 3, cicd)**: KEEP_OPEN — re-checked
  `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` while classifying this doc for the archive sweep: still
  `{"total_count": 0}`, corroborating slot 2's same-day finding rather than a one-off blip. Out of scope for this
  escalation to investigate further (unrelated to the QG wall dispatched here — the failing quality-gates-v2 slice runs
  on GitHub-hosted runners, not `glue`). Synthesized a tracked Follow-up todo above; doc stays open pending that
  investigation.
- **2026-08-07 (fleet_workflow_template_dedup todo 5 session)**: **Correction — the "0 glue runners" signal above was a
  red herring for THIS workflow specifically, not a real blocker.** `ldr-to-main-promote-fleet.yml`'s own `runs-on:` was
  flipped `[self-hosted, glue]` → `ubuntu-latest` by `unified-trading-pm@c8cd56251e` (12:23 UTC, the
  `self_hosted_runner_public_repo_revert_2026_08_05.md` todo-24 revert) — i.e. BEFORE slot-2's 13:34–13:38 UTC
  observation. Once on `ubuntu-latest`, this workflow's runs no longer depend on the glue pool's registered-runner count
  at all, so a genuinely-empty glue pool (itself real and expected post-revert — PM no longer routes ANY workflow to
  self-hosted) cannot be what stalled it. The real cause was the separate cancel-treadmill livelock slot-2 root-caused
  and fixed at 16:36 UTC (`383090a998`, `*/5`→`*/15` cadence cut) — confirmed via `gh run list`: runs 15:45–17:19 UTC
  are all `cancelled` (the livelock), runs 17:30 UTC onward are all `completed success`. **Fleet promotion is healthy
  again as of this check (18:00 UTC).** Also observed several `workflow_dispatch` events firing every few minutes in
  that 17:00–18:00 UTC window — looks like the exact ad-hoc-dispatch anti-pattern this doc's sibling livelock issue
  warns against (multiple sessions manually checking their own promotion status); did not dispatch it myself, flagging
  for whoever owns that pattern to stop.
- **2026-08-08 (slot 4, fleet_promoter_glue_runner_stall-004)**: Investigated the P1 follow-up.
  `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` still returns `{"total_count":0,"runners":[]}` (confirmed
  same empty glue pool) — but this is **not a genuine new pool-depletion event**: the 08-07 afternoon session's finding
  holds. `ldr-to-main-promote-fleet.yml` runs on `ubuntu-latest` (line 75 confirmed), not the glue pool; 0 glue runners
  is expected post-`c8cd56251e` revert and has no bearing on this workflow. Fleet promotion is **healthy**: last 9
  completed runs (01:30–03:00 UTC today) are all `completed success`; the `*/15` cadence is stable; no cancel-treadmill.
  **Verdict: same class as 08-07 morning's JIT-restart-window false-positive — the 0-glue-runner count is structural,
  not a recurrence of the original stall pattern.** No escalation needed. Todo flipped closed.
