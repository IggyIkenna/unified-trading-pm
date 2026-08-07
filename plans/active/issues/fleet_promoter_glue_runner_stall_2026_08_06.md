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
    /plans/active/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
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
    /plans/active/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
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
- [ ] [INFRA] P2. Hardening: add a `workflow_dispatch` trigger to `ldr-to-main-promote-fleet.yml` so an operator can
      manually kick off a promotion tick when the schedule is stuck (already exists — documented here for awareness).

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
