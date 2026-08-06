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
- [ ] [INFRA] P2. Investigate why glue-3 and glue-5 are offline — restart or replace (repo: unified-trading-pm).
- [ ] [INFRA] P2. Hardening: add a `workflow_dispatch` trigger to `ldr-to-main-promote-fleet.yml` so an operator can
      manually kick off a promotion tick when the schedule is stuck (already exists — documented here for awareness).

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — promoter gate set
- `/codex/05-infrastructure/vm-launcher-runbook.md` — runner infrastructure

## Progress Log

- **2026-08-06 (slot 12)**: Filed after discovering promoter stall during sit-gate fleet-green investigation. Promoter
  self-recovered at ~22:35 UTC when a glue runner picked up the 22:30 run.
