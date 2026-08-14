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
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
archive_exempt: true
resolved_by:
last_updated: 2026-08-13
locked_since:
context_scope:
  [
    /plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
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

## Todos

- [x] [BACKEND] P1. **ADDED 2026-08-12 (/plan-reconcile, Section 2 zero-checkbox conversion)** — ✅ Parallelize the
      per-VM I/O in `sweep()` (`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` +
      `heartbeat_stall_watcher.py`) via `ThreadPoolExecutor` over the independent GCS reads (precedent: `cli.py`).
      Target: sweep completes in <5 min so cron overlap collapses to ~1 execution. Parallelize only the pure reads; keep
      classify/route/emit sequential to preserve the shared-state discipline (findings sink, `_EMITTED_THIS_SWEEP`,
      RESOLVED bookend). Fallback if not immediately shippable: reduce cron cadence to match sweep duration (stopgap
      only, trades detection latency). Repo: deployment-service.
- [x] [BACKEND] P1. **ADDED 2026-08-14 (slot 15, infra live-verify)** — the shipped `ThreadPoolExecutor` fix
      (`deployment-service@069ced1412`) is LIVE but empirically NOT sufficient: 3 consecutive hourly executions on 08-13
      (21:27, 22:00, 23:00 — all AFTER the fix landed) each still hit the full 1800s task-timeout, the same failure mode
      as pre-fix. Live logs from a 4th execution (08-14 00:00) show per-VM classification lines spaced ~30-90s apart
      (not the tight clustering expected from an effective 32-worker pool) plus at least one
      `download_bytes(...) exceeded the 30s bounded-call timeout` stall. Investigate why parallelizing the READ phase
      didn't collapse wall-clock: candidates — (a) the per-VM call chain (exit-code read + captured read +
      PREEMPTED-marker read + run.log download) may still be largely SEQUENTIAL _within_ each worker thread rather than
      genuinely fanned out, (b) the terminated-VM classify/route/emit stage (deliberately kept sequential) may itself
      now dominate wall-clock once the read phase is faster, (c) the fleet may have grown past what
      `_SWEEP_IO_MAX_WORKERS=32` was sized for, or (d) GCS API throttling under 32 concurrent readers is itself
      producing the observed 30s stalls. Verify with a timed/profiled sweep run (log phase boundaries) before attempting
      another fix. Full evidence in `/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md` Progress Log,
      2026-08-14 entry. Repo: deployment-service. — ✅ Confirmed candidate (a): the terminated-VM classify loop
      independently re-downloaded the SAME run.log blob up to 3x per VM (`no_capture_reason_from_run_log`, then
      `run_log_signals`, then `error_snippet_from_run_log`), each a separate GCS round-trip — this is what the
      ~30-90s-per-VM classify-loop spacing measured. Fixed by fetching run.log once per VM (lazily) and reusing the text
      across all consumers; regression test asserts ≤1 download per VM. `deployment-service@3c9d65dd50`, QG green.
- [x] [BACKEND] P2. **ADDED 2026-08-14 (slot 12, follow-up)** — ✅ Live-verified the redundant-download dedup
      (`deployment-service@3c9d65dd50`) actually collapses the exit-code-monitor sweep under its 1800s task-timeout:
      check the next few hourly Cloud Run executions after this fix deploys. If still timing out, candidates (b) fleet
      size past `_SWEEP_IO_MAX_WORKERS=32` and (c) GCS throttling under 32 concurrent readers (see the original
      investigate-todo above) remain unaddressed and need their own timed/profiled sweep run. Repo: deployment-service.
      **Result: still timing out — dedup fix insufficient.** Confirmed the deployed image (execution `q9wbf`,
      13:00-13:30Z, digest `a7b0293...`) is genuinely post-fix (ancestor check: `3c9d65dd50` is an ancestor of the
      vendored `deployment-service` commit baked into that build) — this is the first Cloud Run execution to actually
      run the fix (all 06:00-12:00Z executions ran the prior digest `bd4a2a8...`, pre-fix). It STILL hit the full 1800s
      timeout. Strong evidence for candidate (c): 116 `download_bytes(...) exceeded the 30s bounded-call timeout`
      warnings across 114 distinct VMs (~67% of the ~170-VM fleet) in that one execution's logs — every one of those
      stalls burns the full 30s bounded-call budget before the read is abandoned and classified as failed, which at
      `_SWEEP_IO_MAX_WORKERS=32` alone accounts for ~107s of pure stall time even under perfect parallelization, on top
      of ordinary per-VM read latency. This rate (two-thirds of VMs stalling their run.log read) is far above what
      normal network variance would produce and points at GCS throttling under 32 concurrent readers against the same
      `vm-logs/` prefix, not a residual redundant-download issue. Filed the next investigate/fix todo below. Repo:
      deployment-service.

- [ ] [BACKEND] P1. **ADDED 2026-08-14 (slot 7, live-verify follow-up)** — the dedup fix
      (`deployment-service@3c9d65dd50`) is confirmed live and confirmed insufficient (see the P2 verify todo above):
      execution `q9wbf` (13:00-13:30Z, first execution on the post-fix image digest) still hit the full 1800s timeout,
      with 116/~170 (≈67%) per-VM `run.log` reads hitting the 30s bounded-call timeout. Investigate + fix candidate (c)
      (GCS throttling under `_SWEEP_IO_MAX_WORKERS=32` concurrent readers against the same `vm-logs/` prefix): (1) run a
      profiled/instrumented sweep that logs per-phase wall-clock (running-census / terminated-classify) and per-call
      latency distribution, not just the 30s-timeout tail, to confirm throttling vs. genuinely slow individual reads;
      (2) if throttling is confirmed, try reducing `_SWEEP_IO_MAX_WORKERS` (fewer concurrent readers, less contention)
      AND/OR adding jittered backoff-retry on a stalled `download_bytes` call instead of treating a single 30s stall as
      terminal-failed (a retry after backoff may succeed where the first attempt was throttled); (3) also re-check
      candidate (b) (fleet size — is `_SWEEP_IO_MAX_WORKERS=32` sized for the CURRENT ~170-VM census, or did the fleet
      grow past what was true when 32 was chosen). Target: sweep completes well under 1800s with a near-zero
      bounded-call-timeout rate. Repo: deployment-service.

## Related

- `/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md` — the exit-code-monitor OOM (signal 9)
  recurrence; the sweep being chronically unable to finish is the same "fleet grew past the ceiling" class, and the
  resource re-bump alone is now confirmed insufficient.
- This sweep ALSO shipped (2026-08-10): meta-watchers defi-index streaming read + incremental tracker persist,
  preemption-relaunch GCS budget + 900s launcher timeout, GONE_NO_CAPTURE false-positive fixes (POLARS AGGREGATED +
  launcher-host exemption), and the DP_SOURCE_RATE_LIMITED cooldown.

## Progress Log

- 2026-08-14 (slot 7, backend): Live-verified the P2 todo. Confirmed the redundant-download-dedup fix
  (`deployment-service@3c9d65dd50`) is genuinely live in the running Cloud Run job image (job spec references
  `deployment-api:latest`; the FIRST execution to actually run the post-fix digest was `q9wbf`, started 13:00:04Z — the
  six preceding hourly executions 06:00-12:00Z all ran the prior digest `bd4a2a8...`, confirmed via
  `gcloud run jobs executions describe --format=value(spec.template.spec.containers[0].image)` per-execution digest
  comparison against the image push timestamp `2026-08-14T12:36:20Z`). `q9wbf` still hit the full 1800s task timeout
  (completed 13:30:29Z, "The configured timeout was reached") — the dedup fix alone does not collapse the sweep.
  `gcloud logging read` on that execution's logs shows 116 `download_bytes(...) exceeded the 30s bounded-call timeout`
  warnings across 114 distinct VMs (of the ~170-VM fleet), i.e. roughly two-thirds of VMs stalled their run.log read for
  the full 30s bounded-call budget before it was abandoned — a rate consistent with GCS throttling under
  `_SWEEP_IO_MAX_WORKERS=32` concurrent readers (candidate (c) from the earlier investigate-todo), not ordinary network
  latency. Flipped the P2 verify todo done with the result recorded inline; filed a new P1 investigate/fix todo
  (candidate (c) profiling + mitigation, re-checking candidate (b) fleet-size sizing) since this is a genuinely new fix
  attempt, not a mechanical follow-through of this verify-only task. No code changed this session (verification +
  issue-doc update only).

- 2026-08-14 (slot 12, backend): Picked up the 08-14 investigate/fix todo. Root cause confirmed: the terminated-VM
  classify loop in `exit_code_fleet_monitor.sweep()` called `no_capture_reason_from_run_log`, then (on SILENT)
  `run_log_signals`, then (once a finding fires) `error_snippet_from_run_log` — each independently downloading the SAME
  `run.log` blob via `_gcs.read_text`, up to 3x per VM. The earlier `ThreadPoolExecutor` fan-out (069ced1412)
  parallelized reads ACROSS VMs but did nothing for this redundancy WITHIN one VM's classify path — consistent with the
  measured ~30-90s-per-VM spacing once the read phase was already fast. Fix: fetch run.log once per VM (lazily, only
  when `needs_reason`), reuse the text across all three consumers via new pure `_from_text`/`_text` variants in
  `_gcs.py` (`run_log_signals_from_text`, `error_snippet_from_log_text`, `run_log_shows_stall_text`). Added a regression
  test (`test_sweep_gone_no_capture_downloads_run_log_at_most_once`) asserting ≤1 download per swept VM.
  `deployment-service@3c9d65dd50`, QG green (had to trim two docstrings to stay under the 960-line file cap on
  `_gcs.py`). Flipped the investigate/fix todo done; added a P2 follow-up todo to live-verify this actually collapses
  the sweep under its 1800s timeout (candidates (b) fleet size / (c) GCS throttling from the original todo are still
  unconfirmed either way).
- 2026-08-14 (slot 15, infra): While live-verifying the sibling OOM doc's gated todo, found the shipped parallelize fix
  (`069ced1412`) is live but NOT resolving the timeout — 3 consecutive post-fix hourly executions on 08-13 (21:27,
  22:00, 23:00) all still hit the full 1800s timeout, identical to pre-fix behavior. Added a new P1 investigate/fix todo
  above; did not attempt the fix myself (backend craft scope, out of bounds for this P2 verify-only task). Full evidence
  in the sibling doc's 2026-08-14 Progress Log entry.

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

**backend_engineer 2026-08-13** (slot-28): shipped the P1 parallelization — `ThreadPoolExecutor` fan-out of the per-VM
GCS reads in both `exit_code_fleet_monitor.sweep()` (running-census captured reads + terminated-VM base signals) and
`heartbeat_stall_watcher.sweep()` (run.log/shards/sidecar/mtime liveness reads), `_SWEEP_IO_MAX_WORKERS=32`;
classify/route/emit + auto-kill stay sequential (shared `finding_sink` + PubSub + per-sweep kill cap preserved).
`deployment-service@069ced1412`, QG green.

**archive_exempt: true reason (slot-28, 2026-08-13)** — this doc's only todo (the P1 above) is now shipped, so it reads
0-open/some-done and `check_archive_candidates --only` would demand immediate archival. It is NOT being `git mv`'d in
this task because it remains the SOURCE doc for still-open DERIVED todos in OTHER active plans — the duplicate
"parallelize sweep()" dispatches in `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` (P2) and
`..._batch13b_2026_08_13.md` (P2), and the "genuine unresolved" entry in `plan_reconciler_findings_all_2026_08_12.md`
§2. Archiving the source out from under those would orphan their references; closing/retiring them is a
`/plan-reconcile` coordination, not a single-worker flip. Drop `archive_exempt: true` and `git mv` to
`plans/archive/2026_08/issues/` once those derived todos are reconciled.

- **context-scout 2026-08-14**: populated context_scope (4 entries).
