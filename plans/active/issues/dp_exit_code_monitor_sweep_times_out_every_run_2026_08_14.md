---
doc_type: issue
title:
  dp-exit-code-monitor times out at 1800s on every execution — the sweep never finishes, so revocation coverage will be
  truncated
summary: |
  uts-prod-dp-exit-code-monitor is killed by the Cloud Run 1800s task timeout on every execution measured, spending the
  whole budget on per-VM run.log downloads that each blow the 30s bounded-call. route_finding() runs inline per VM, so
  once the revocation wiring deploys it will actuate only for the VMs the sweep reaches before the kill — partial
  coverage biased by iteration order, with no signal that anything was skipped. Separate from, and surviving, the
  arming work in revocation_arming_2026_08_14.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [alerting, self-healing, vm-lifecycle, monitoring, cloud-run, revocation]
related:
  [
    /plans/active/revocation_arming_2026_08_14.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
effort: high
drift_direction: advance-code
context_scope:
  [
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    /plans/active/revocation_arming_2026_08_14.md,
  ]
resolved_by:
supersedes:
superseded_by:
depends_on:
locked_by:
locked_since:
source: Live confirmation pass on revocation_arming_2026_08_14's OPERATOR P0 todo, 2026-08-14
---

# dp-exit-code-monitor times out at 1800s on every execution

## What was measured (2026-08-14, read-only)

Running the live-confirmation checklist from
[`/plans/active/revocation_arming_2026_08_14.md`](/plans/active/revocation_arming_2026_08_14.md)'s open `[OPERATOR]` P0
todo produced three results. Two are expected deploy lag; the third is a new defect.

**(a) The deployed image predates the wiring.** `uts-prod-dp-exit-code-monitor` runs
`unified-trading-system/deployment-api:latest`. The last SUCCESS `deployment-api` build was `9a4d1e5e` at
2026-08-14T07:34:41Z. The arming commit `deployment-service@79864746` landed 11:40Z and the release bookend `@375835a9`
11:48Z — both after that build. Build `4a6adee9` (started 12:31Z) is the first that can carry them and was still
`WORKING` at check time. So no execution so far could have called the actuator regardless of correctness.

**(b) Zero markers, consistent with (a).** `vm-census/admission-hold/` and `vm-census/revocation-actuation` under
`deployment-scripts-central-element-323112` (via `scripts.recovery._durable_state.state_bucket()`) both list **0**
objects.

**(c) NEW — every execution is killed by the task timeout.** Measured on the 10:00Z, 11:00Z and 12:00Z executions:

```
2026-08-14T12:30:29Z  Terminating task because it has reached the maximum timeout of 1800 seconds.
2026-08-14T11:30:23Z  Terminating task because it has reached the maximum timeout of 1800 seconds.
2026-08-14T10:30:19Z  Terminating task because it has reached the maximum timeout of 1800 seconds.
```

Each starts on the hour and dies at :30 having never reached the end of the fleet. `gcloud run jobs executions list`
shows `succeededCount` empty and `failedCount=1` for every recent execution.

The budget goes on per-VM log fetches. Interleaved through the run:

```
12:29:29 WARNING _gcs: download_bytes(.../vm-logs/mdps-defi-2025-20260810-043618/run.log) exceeded the 30s bounded-call
12:27:40 WARNING _gcs: download_bytes(.../vm-logs/mdps-defi-2025-20260807-203541/run.log) exceeded the 30s bounded-call
12:26:23 WARNING _gcs: download_bytes(.../vm-logs/mdps-defi-2024-20260810-051606/run.log) exceeded the 30s bounded-call
```

## Why this matters after the arming work lands

`route_finding()` is called **inline, per VM** — `exit_code_fleet_monitor.py` calls it immediately before the
`exit_code_fleet_monitor: <vm> verdict=<v> ...` warning that appears throughout the logs. That is good news for arming:
revocation does not wait for the sweep to finish, so the VMs processed before the kill will actuate.

It is also the problem. The sweep is truncated at a wall-clock boundary, so revocation coverage becomes "whatever the
iteration reached in 30 minutes" — biased by fleet order, varying run to run, and **silent**: nothing distinguishes "no
finding for this VM" from "never examined". The detections are real and firing (many `verdict=gone_no_capture` lines on
`mdps-defi-2022-*` / `-2024-*` / `-2025-*` in a single run), so this directly bounds how much of a real condition the
mechanism can ever act on.

This survives the arming work — it is not fixed by giving `actuate()` a caller, and it will not show up as a failure of
that plan.

## Todos

- [ ] [INFRA] P0. Stop the sweep hitting the 1800s task timeout — the run.log fetch is best-effort snippet enrichment
      (`if snippet: finding.details["run_log_tail"] = ...`) yet costs up to 30s per VM, so bound it fleet-wide (a total
      enrichment budget, skip-on-first-timeout, or drop the fetch for `gone_no_capture` where the log is usually the
      thing that is missing) — DoD: an execution of `uts-prod-dp-exit-code-monitor` completes without a
      `Terminating task` line, cited by its execution log.
- [ ] [INFRA] P0. Make a truncated sweep loud instead of silent — if the fleet is not fully walked, the run must say so
      (count examined vs total, non-zero exit or an explicit alert) — DoD: a deliberately shortened run emits a "sweep
      incomplete, N of M examined" signal rather than looking identical to a clean pass.
- [ ] [INFRA] P1. Reconcile the schedule discrepancy — `revocation_arming_2026_08_14.md`'s OPERATOR todo states the job
      runs on a `*/5` schedule, but executions are hourly (09:00Z, 10:00Z, 11:00Z, 12:00Z starts) — DoD: either the
      Cloud Scheduler cron or the plan's claim is corrected, stating which was wrong; a 30-minute run on a `*/5` cadence
      would also overlap itself, which is worth checking for while there.
- [ ] [INFRA] P1. Re-run the live confirmation once build `4a6adee9` (or its successor carrying `@79864746` +
      `@375835a9`) has deployed — DoD: a `DP-REVOCATION-*` line in an execution log plus a marker under
      `vm-census/admission-hold/`, per the parent plan's OPERATOR todo; this issue's (a) and (b) results were pure
      deploy lag and should be re-measured, not carried forward.

## Progress Log

_(append dated entries here)_
