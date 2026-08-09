---
doc_type: issue
title: >-
  2 residual CI-monitor alert-hygiene gaps found during the recovery/all-clear bookend audit — not fixed there
  (different fix shape than the audit's scope)
summary: >-
  `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 4 audited all 27 schedule-active `.github/workflows/*.yml`
  monitors in `unified-trading-pm` for a missing state-diffed recovery/all-clear post and fixed 6 (see
  `unified-trading-pm@c717af0fd`). Two smaller gaps surfaced in the same audit but were deliberately NOT fixed there —
  they need a different fix (adding dedup/cooldown, or a second resolved job) rather than the recovery-bookend pattern
  the audit's `done_definition` scoped to. Filed here so they are tracked `- [ ]` work, not just prose in a Progress Log
  (workspace HARD RULE — every deferral needs a checkbox).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, cicd, monitoring-gap, slack-alerting, dedup, follow-up]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: 2026-08-09
author: ikennaigboaka [slot-7]
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: cicd
resolved_by:
locked_by:
locked_since:
source: >-
  Found during the `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 4 audit (2026-08-09, slot 7) of every
  schedule-active CI monitor's recovery/all-clear behavior; deliberately out of that audit's scope.
drift_direction: advance-code
depends_on: []
---

# CI-monitor alert-hygiene residual gaps (post recovery-bookend audit)

## What I found

### 1. `ldr-to-main-promote-fleet.yml` / `ldr-to-main-promote.yml` have no `dedup_key` at all on their alert jobs

`ldr-to-main-promote-fleet.yml`'s `notify` (conflict alert) and `notify-arm-failed`, and `ldr-to-main-promote.yml`'s
`notify-arm-failed`, all call `notify-slack.yml` without a `dedup_key`. Per `notify-slack.yml`'s own contract, a blank
`dedup_key` means "no dedup — always posts." These three jobs run on a `*/15` cron, so a standing conflict/arm-failure
condition re-pages **every 15 minutes** until fixed — the opposite defect from the recovery-bookend audit (that audit
was about monitors that go SILENT once a page fires; these are too NOISY). Adding a recovery bookend to these would be
the wrong fix — they need a `dedup_key` (e.g. per-repo, `ldr-main-conflict:<repo>` / `ldr-main-arm-failed:<repo>`) +
`cooldown_min` FIRST, and only then would a resolved bookend make sense on top.

**Done when**: each of the 3 alert calls gets a stable per-condition `dedup_key` + a `cooldown_min` matched to the
`*/15` cron cadence (mirrors `promote-fleet-startup-failure-monitor.yml`'s `cooldown_min: 60`), regression-tested
against a synthetic repeat-alert-same-condition tick (suppressed) and a genuinely-new-condition tick (still posts).

### 2. `branch-health.yml`'s `ar-lag-notify` job has no resolved sibling

Unlike its sibling jobs in the SAME file (`lag-notify`/`lag-notify-resolved`), the AR-dep-publish-lag alert
(`ar-lag-notify`, `dedup_key: ar-dep-publish-lag`, `cooldown_min: 60`) has no `ar-lag-notify-resolved` counterpart — the
exact gap this audit fixed for 6 other monitors, but not caught there because `branch-health.yml` as a WHOLE file was
already correctly classified "present" (its `lag-monitor`/`lag-notify-resolved` pair IS the reference pattern). Lower
priority than the 6 fixed in `c717af0fd` — AR-dep-publish-lag is a WARNING-level advisory (a repo hasn't published an
internal dep floor yet), not an operator-named pain point.

**Done when**: `ar-lag`'s `scan` step (in `branch-health.yml`) emits a `cleared`/`cleared_report` output pair (mirrors
`lag-monitor`'s own `cleared`/`cleared_report` outputs — likely needs a small persisted-state diff in
`assert_deps_published_to_ar.py`'s caller, same `.lag-state.json`-style cache), and a new `ar-lag-notify-resolved` job
(severity INFO, `recovery: true`, its own `dedup_key`/short `cooldown_min`) fires on the AR-lag-cleared transition.

## Still open

- [ ] [SCRIPT] P3. Add `dedup_key` + `cooldown_min` to `ldr-to-main-promote-fleet.yml`'s `notify` (conflict) and
      `notify-arm-failed` jobs, and to `ldr-to-main-promote.yml`'s `notify-arm-failed` job — see finding 1 above for the
      exact done-when and regression-test requirement. (repo: `unified-trading-pm`)
- [ ] [SCRIPT] P3. Add an `ar-lag-notify-resolved` job to `branch-health.yml` (state-diffed, mirrors
      `lag-notify-     resolved`) — see finding 2 above for the exact done-when. (repo: `unified-trading-pm`)

## Progress Log

- **2026-08-09 (slot 7)**: Filed while closing out `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 4 — these 2 gaps
  were mentioned in that todo's source doc Progress Log entry as prose ("not fixed here") without a tracked checkbox,
  which is a workspace hard-rule violation (every deferral needs a `- [ ]`, not just prose). Filing this doc closes that
  gap; no code changed here yet.
