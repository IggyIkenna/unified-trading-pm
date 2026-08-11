---
doc_type: issue
title: >-
  exit-code-monitor 5-min cron vs >30-min sweep — ~6 overlapping executions multiply the DP_VM_* alert storm (re-fire is
  NOT a dedup bug, it's cadence vs wall-clock)
summary: >-
  The `uts-prod-dp-exit-code-monitor` Cloud Run Job fires every 5 min (`*/5 * * * *`) but its sweep takes >30 min even
  after the 2026-08-10 live re-bump to 16Gi/4cpu/1800s — the per-VM `captured_reader` + terminated-VM GCS reads in
  `sweep()` are SEQUENTIAL over ~170 VMs. So up to ~6 executions overlap at any time, each independently re-reading the
  same fleet, re-classifying the same preempted / drained VMs, and re-emitting the same DP_VM_PREEMPTED /
  DP_VM_PREEMPTED_NO_RELAUNCH / DP_VM_GONE_NO_CAPTURE findings. The #data-pipeline-alerts storm is therefore MULTIPLIED
  by the overlap factor (measured 2026-08-10: 130 DP_VM_GONE_NO_CAPTURE in a single hour, with the same handful of VMs
  re-firing every 5-min tick), and the freshness sentinel (`vm-census/exit-code-last-run.json`) stays stale 12h+ because
  the sweep never reaches its terminal `write_monitor_last_run` before the next execution starts. Overlapping executions
  also race on the GCS census blob. This is NOT primarily a dedup/cooldown bug (those exist and merely cap the
  per-execution rate) — it is a wall-clock-vs-cadence structural mismatch: the sweep cannot finish within its own cron
  interval.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [data-pipeline-monitors, exit-code-monitor, cloud-run-job, sweep-overlap, storm, dp-vm]
related:
  - /plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md
  - /codex/05-infrastructure/data-pipeline-alerts.md
created: 2026-08-10
author: data_pipeline_alerts_reconciler (scheduled 6-hourly sweep, slot 18)
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-10
locked_since:
source: >-
  Found during the 2026-08-10 scheduled /data-pipeline-alerts-reconcile sweep. Live evidence: `gcloud run jobs
  executions list` shows 4-6 concurrent "Waiting for execution to complete" rows for the exit-code-monitor at any time;
  each execution starts 5 min apart and takes >30 min (the 17:45 run with the 900s pre-bump timeout died at 15:00;
  post-bump runs at 1800s are still running 30+ min without writing the freshness sentinel, which has been stale since
  05:41Z). Cloud Logging shows the SAME VMs (mdps-cefi-2019-*, mdps-cefi-2022-*) re-classified preempted/gone_no_capture
  every 5-min tick across overlapping executions. The resource re-bump to 16Gi/4cpu/1800s (applied live 2026-08-10
  ~17:44) is necessary but NOT sufficient — the sweep is I/O-bound (per-VM GCS reads), and CPU doesn't fix wall-clock
  when each of ~170 VMs needs 2-4 sequential GCS round-trips.
---

# exit-code-monitor sweep-overlap storm

## Root cause

`sweep()` (`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`) does its per-VM GCS reads
SEQUENTIALLY:

- running-VM census: `for name in running: captured_reader(name)` (~170 GCS reads)
- terminated-VM processing: `for name in terminated: ...` (exit-code read + captured read + PREEMPTED-marker read +
  run.log download each)

At ~2-6s per GCS round-trip this is a 20-35 min sweep, while the cron fires every 5 min → ~6 overlapping executions.
Each overlaps execution re-detects the same preempted/drained VMs and re-emits the same findings (bounded only by the
`_RECURRING_ALERT_COOLDOWNS` 30-min window in alerting-service, which caps per-event rate but still allows a
2x-per-window re-page per VM).

## Measured evidence (2026-08-10)

- 5-min cron; sweep duration > 30 min (post 16Gi/4cpu re-bump) → 4-6 concurrent executions observed at all times.
- Freshness sentinel `vm-census/exit-code-last-run.json` stale since 05:41Z (12h+ at finding time) — the sweep never
  reaches `write_monitor_last_run`.
- #data-pipeline-alerts: 130 DP_VM_GONE_NO_CAPTURE in one hour, the SAME mdps-cefi-2019/2020/2022 VMs re-firing every
  5-min tick.
- The overlap ALSO races the GCS census blob (multiple executors read-modify-write `exit-code-fleet-census.json`).

## SIBLING FINDING — heartbeat-watcher is the SAME overlap class (2026-08-11, reconciler slot-20)

`uts-prod-dp-heartbeat-watcher` (same family, same `data_pipeline_fleet_monitor_scheduler.tf`) is now confirmed the
identical structural problem: its sweep takes **> 900s** (measured `vsm6k` ran 936s and was killed at the 900s task
timeout, `status=False`), while its cron fires every 5 min. It was the LAST of the three monitors that never got the
growth-past-ceiling timeout bump (exit-code 300→900 2026-07-29, meta 300→900 2026-08-09; heartbeat sat at 300s), so
every `*/5` run timed out and the freshness sentinel `vm-census/heartbeat-last-run.json` went stale ~18h (05:45Z →
23:45Z, verified 2026-08-10), which is exactly why `DP_CRON_DID_NOT_FIRE` for `dp-heartbeat-monitor` fired (208
msgs/24h).

- **Shipped this sweep (partial)**: timeout bumped 300→900 live (`gcloud run jobs update --task-timeout=900`, 2026-08-10
  ~23:47Z) + terraform backport `deployment-service@e9c656f8ba`. **Necessary but NOT sufficient** — the 900s run still
  times out, proving heartbeat is I/O-bound like exit-code (per-VM GCS reads), and now overlaps ~3x instead of ~1x. The
  REAL fix is the same parallelization below; extend its scope to heartbeat's `sweep()` in `heartbeat_stall_watcher.py`
  as well as exit-code's.

## Fix (deferred — needs its own focused pass, NOT rushable this sweep)

Parallelize the per-VM I/O in `sweep()` with a `ThreadPoolExecutor` over the independent GCS reads (the fleet is
embarrassingly parallel; the codebase already uses `ThreadPoolExecutor` in `cli.py`). Target: sweep completes in < 5 min
so the overlap collapses to ~1 execution. The terminated-VM processing must preserve the shared-state discipline
(findings sink, `_EMITTED_THIS_SWEEP`, RESOLVED bookend) — parallelize only the pure reads, keep the classify/route/emit
sequential.

Fallback if parallelization is not immediately shippable: reduce the exit-code cron cadence to match the sweep duration
(e.g. `*/15` or `*/30`) so fewer executions overlap — but that trades detection latency (a VM dying at T+0 won't be seen
until the next sweep) and is a stopgap, not the root fix.

## Related

- `/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md` — the exit-code-monitor OOM (signal 9)
  recurrence; the sweep being chronically unable to finish is the same "fleet grew past the ceiling" class, and the
  resource re-bump alone is now confirmed insufficient.
- This sweep ALSO shipped (2026-08-10): meta-watchers defi-index streaming read + incremental tracker persist,
  preemption-relaunch GCS budget + 900s launcher timeout, GONE_NO_CAPTURE false-positive fixes (POLARS AGGREGATED +
  launcher-host exemption), and the DP_SOURCE_RATE_LIMITED cooldown.
