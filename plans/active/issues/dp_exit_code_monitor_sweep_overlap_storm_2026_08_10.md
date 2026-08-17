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
last_updated: 2026-08-17
locked_since:
context_scope: [/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py, /codex/05-infrastructure/data-pipeline-alerts.md]
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

- [x] ✅ [BACKEND] P1. **ADDED 2026-08-14 (slot 7, live-verify follow-up)** — the dedup fix
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
      bounded-call-timeout rate. Repo: deployment-service. — ✅ Shipped both requested mitigations for (c):
      `_SWEEP_IO_MAX_WORKERS` lowered 32→16 in both `exit_code_fleet_monitor.py` and `heartbeat_stall_watcher.py`
      (mirrors the same throttled-`vm-logs/`-prefix pattern), and `_gcs._call_with_timeout` now takes a `retries` kwarg
      (jittered ~0.5-1.0s backoff) wired into `read_text`'s `download_bytes` call — the confirmed-stalling call per the
      `q9wbf` evidence. Also added phase-boundary wall-clock logging (running-census / terminated-base-signals /
      classify-route-emit) to `exit_code_fleet_monitor.sweep()` per profiling ask (1), so the NEXT execution's Cloud
      Logging output attributes any remaining timeout to a specific phase instead of only the aggregate 30s-stall count.
      Candidate (b) (fleet-size re-check) could NOT be independently re-measured this session — no live `gcloud`/GCS
      credential access from this worker's environment — so it remains open evidence-wise; the worker count reduction
      (16) is a defensible mitigation regardless of the exact current fleet size. `deployment-service@ f9cf85a4b5`, QG
      green. Live-verification of the NEXT few hourly executions (does the sweep now finish under 1800s, does the
      stall-timeout rate drop) is a fresh verify task, not bundled into this fix.

- [x] ✅ [BACKEND] P2. **ADDED 2026-08-14 (slot 7, follow-up)** — live-verify the candidate-c mitigation
      (`deployment-service@f9cf85a4b5`: `_SWEEP_IO_MAX_WORKERS` 32→16 + jittered-backoff retry on `download_bytes`)
      actually collapses the exit-code-monitor sweep under its 1800s task-timeout: check the next 2-3 hourly Cloud Run
      executions after this fix's image deploys — confirm via
      `gcloud run jobs executions describe --format=value(spec.template.spec.containers[0].image)` that the execution
      genuinely ran the post-fix digest (same ancestor-check discipline as the prior P2 verify), then read the new
      phase-boundary INFO logs (`running-census phase took...` / `terminated-base-signals phase took...` /
      `classify/route/emit phase took...`) to see which phase now dominates wall-clock, plus count remaining
      `download_bytes(...) exceeded the 30s bounded-call timeout` warnings (retry-recovered stalls should no longer
      appear as terminal failures). If still timing out, candidate (b) (current live fleet size vs
      `_SWEEP_IO_MAX_WORKERS=16`) needs an actual live census count this task's environment couldn't obtain. Repo:
      deployment-service. — ✅ **Result: still timing out — candidate-c mitigation insufficient, but confirmed live +
      partially effective; root cause is a THIRD, previously-undiagnosed bottleneck.** Full evidence + new fix candidate
      in the Progress Log below (this session had live `gcloud`/GCS credential access, unlike the prior 3 sessions on
      this doc). Filed the next P1 investigate/fix todo.

- [x] ✅ [BACKEND] P1. **ADDED 2026-08-14 (slot 15, live-verify follow-up)** — the classify/route/emit phase
      (deliberately kept SEQUENTIAL to protect shared state — `finding_sink`, `_EMITTED_THIS_SWEEP`, the RESOLVED
      bookend, `route_finding` side effects) is now the dominant bottleneck, confirmed via live phase-boundary logs on
      execution `f8k2v` (2026-08-14 18:00-18:30Z): only 15/266 terminated VMs got a logged `verdict=` between 18:09:31Z
      and 18:26:55Z (~1044s, ~70s/VM average) before the 1800s kill — vs. the FANNED-OUT read phases (`running-census`
      1.9s + `terminated-base-signals` 449.9s ≈ 452s total), which the candidate-c fix successfully sped up. Two
      candidates: (1) the classify loop's PER-VM `needs_reason` run.log fetch is a SEPARATE single-read (not part of the
      earlier fanned-out `_read_terminated_base` prefetch) and still hits the 30s bounded-call timeout + 1 retry (91
      warnings logged this execution) — each stall costs up to ~60s serialized into the sequential loop; consider either
      (a) prefetching this run.log too as part of the fanned-out base-signals read (same "prefetch pure reads, keep
      classify/route/emit sequential" pattern already used), or (b) reducing the per-call timeout/retry budget so a
      stalled VM doesn't block the sequential loop as long. (2) SEPARATELY: `write_census()` is called only ONCE, after
      the ENTIRE terminated-VM loop completes — since the sweep has been timing out every hour, the census likely never
      advances, so each hourly execution reprocesses nearly the SAME ~266-VM "terminated" backlog against a stale
      `prior` snapshot instead of making forward progress. Consider checkpointing `write_census()` incrementally (e.g.
      after the fast read/base-signals phases, independent of whether the slow classify loop finishes) so a
      chronically-timing-out sweep still shrinks its backlog over successive executions. **Candidate (b) (live fleet
      size) is RULED OUT**: live `gcloud compute instances list --filter="status=RUNNING"` = 29 VMs total fleet-wide,
      confirmed via genuinely running census (not the stale 266-VM terminated backlog) — `_SWEEP_IO_MAX_WORKERS=16` is
      not undersized for the current fleet. Target: sweep completes well under 1800s with the terminated backlog
      actually shrinking execution-over-execution. Repo: deployment-service. — ✅ Shipped both candidates: (1a)
      prefetches the classify loop's `needs_reason` run.log as part of a new fanned-out phase right after
      `terminated-base-signals` (candidate set computed from the already-known base-signal values, intentionally
      over-inclusive since `preemption_op_checker` can only flip `is_preempted` False→True, never the reverse, so the
      loop's real `needs_reason` set is always a subset — the loop falls back to a synchronous read if a name is somehow
      absent from the prefetch dict). (2) `write_census()` now checkpoints every 25 classified VMs (not only at the very
      end): the checkpoint preserves not-yet-classified terminated VMs at their PRIOR captured value (so the next tick's
      diff still sees them as terminated and retries them) while dropping already- classified ones (retired, never
      re-flagged) — so a mid-loop task-timeout kill now saves real forward progress instead of restarting the same
      backlog from scratch. Added a regression test
      (`test_sweep_checkpoints_census_incrementally_during_terminated_loop`) asserting the exact checkpoint sequence +
      preserved/dropped VM sets; the existing `test_sweep_gone_no_capture_downloads_run_log_at_most_once` still asserts
      exactly 1 run.log download per VM (unchanged — just moved earlier into the fanned-out phase).
      `deployment-service@cbe58d2d`, QG green (3448 passed). Live-verification of the next few hourly executions (does
      the sweep now finish under 1800s, does the sentinel/backlog actually advance) is a fresh verify task, not bundled
      into this fix.

- [x] ✅ [BACKEND] P2. **ADDED 2026-08-14 (slot 14, follow-up)** — live-verify the classify-loop fix
      (`deployment-service@cbe58d2d`: run.log prefetch + incremental census checkpointing) actually collapses the
      exit-code-monitor sweep under its 1800s task-timeout: confirm the image digest genuinely runs the post-fix commit
      (same ancestor/digest-inspection discipline as prior verify todos on this doc), then read the phase- boundary logs
      (`running-census` / `terminated-base-signals` / `run-log-prefetch` / `classify/route/emit`) on the next 2-3 hourly
      executions to see whether the sweep now finishes, whether the terminated backlog is actually shrinking
      execution-over-execution (via the new incremental census checkpoints), and whether the
      `download_bytes(...) exceeded the 30s bounded-call timeout` warning rate dropped now that most of those reads
      moved into the parallel prefetch phase. Repo: deployment-service. — ✅ **Result: sweep no longer TIMES OUT, but
      now OOM-KILLS instead — a NEW regression, not the fix working.** `cbe58d2d`'s content confirmed live on
      `origin/main` (direct file-content inspection of `origin/main:.../exit_code_fleet_monitor.py`, since the SHA-level
      ancestor-check false-negatived — Option-B direct-promote rewrites commits, so content-inspection is the reliable
      check, consistent with slot 15's 2026-08-14 note) and baked into the newly-pushed `deployment-api:latest` (digest
      `db4f43ada1e1…`, pushed 19:32:46Z — confirmed via direct container-filesystem grep for
      `_checkpoint_census`/`run-log-prefetch phase`/`_CENSUS_CHECKPOINT_INTERVAL`, all present). First execution on this
      digest, `qgtnz` (20:00:04Z→20:13:35Z, only ~13.5 min — well under the 1800s timeout that killed every prior
      execution), **failed with `"The configured memory limit was reached"` + `Container terminated on signal 9` at
      20:13:32Z (OOM, not timeout)**. Phase logs: `running-census` 1.9s (15 VMs) → `terminated-base-signals` 444.5s (266
      VMs) — both fast, consistent with the earlier candidate-c fix — then **no `run-log-prefetch phase took…` or
      `classify/route/emit phase took…` line ever appeared**: the OOM kill landed ~4 min into the NEW run-log-prefetch
      phase this fix added. 136 `download_bytes(...) exceeded the 30s bounded-call timeout` warnings still fired before
      the kill. Filed the next P1 investigate/fix todo below. Repo: deployment-service.

- [x] ✅ [BACKEND] P1. **ADDED 2026-08-14 (slot 27, live-verify follow-up)** — the `run-log-prefetch` phase
      (`deployment-service@cbe58d2d`) fixed the wall-clock problem but introduced a NEW memory regression: execution
      `qgtnz` (2026-08-14 20:00:04Z-20:13:35Z, first execution on the post-fix `deployment-api:latest` digest
      `db4f43ada1e1…`) OOM-killed (signal 9, `"The configured memory limit was reached"`) ~13.5 min in, mid-way through
      the new `run-log-prefetch` phase — well under the 1800s timeout, so the fix's wall-clock goal is achieved but a
      NEW failure mode replaced it. Root-cause candidate: unlike the sequential classify loop it replaced (which read
      one VM's `run.log` at a time), the prefetch phase fans out `_gcs.read_text` across ALL
      `run_log_prefetch_candidates` (up to ~266 terminated VMs this run) via a single
      `ThreadPoolExecutor(max_workers=16)` batch and accumulates every result in one
      `run_log_prefetch: dict[str, str | None]` BEFORE the classify loop consumes any of them — so the sweep now holds
      up to ~266 full `run.log` blobs in memory SIMULTANEOUSLY (worst case) instead of one at a time. Per the
      "Fleet-monitor job memory sizing" anti-pattern already in `/codex/05-infrastructure/data-pipeline-alerts.md` (the
      `meta_watchers` `.to_pandas()` OOM root-cause), the first response should NOT be another Cloud Run memory bump —
      check whether `run.log` blobs are large enough (long-running backfill VMs can accumulate many MB of log) that
      holding ~266 of them at once genuinely exceeds 16Gi, and if so either (a) chunk the prefetch (submit+drain in
      batches of e.g. 32-64 instead of all-at-once), or (b) stream classify/route/emit interleaved with the prefetch
      pool (`as_completed` + classify each VM as its future resolves, rather than materializing the whole
      `run_log_prefetch` dict first) so at most `_SWEEP_IO_MAX_WORKERS` blobs are ever resident, preserving the
      wall-clock win from parallelizing the READ without paying for the full backlog in RAM at once. Verify with a
      profiled run that logs `run.log` byte-size distribution (or peak RSS) alongside the existing phase-boundary timers
      before landing an ungrounded fix. Target: sweep completes under 1800s AND under the 16Gi memory ceiling. Repo:
      deployment-service. — **ADDENDUM (slot 26, same session, independent live-verify of the same `qgtnz` execution)**:
      corroborating but DISTINCT evidence worth folding into the fix — the execution log (294 lines,
      `gcloud logging read`) shows 136 `download_bytes(...)` stall/timeout/retry warnings concentrated in the final ~60s
      before the kill, many the NEW jittered-backoff `retrying after ...` variant; each stalled call is logged as
      leaving its thread running as an undying daemon ("the thread is left running as a daemon so it can never block
      process exit"). A second, possibly-compounding contributor beyond "266 run.log blobs resident at once": each
      STALLED read also leaks an abandoned daemon thread holding its own buffered/retry state for the rest of the
      process lifetime, so the fan-out's true memory cost may be understated by blob size alone. Whichever fix lands
      (chunking / interleaving the prefetch) should also confirm it bounds daemon-thread accumulation from stalled
      reads, not just resident blob count. — ✅ **FIXED (slot 26, same session)**: a live probe of every
      `vm-logs/*/run.log` blob in the log bucket (`StorageClient.list_blobs(resolve_size=True)`, not `gsutil`) found
      sizes ranging **1.1KB to 12.2GB** (mean 46.5MB, p50 1.6MB, p90 106MB, p99 694MB) — this reframes the root cause
      from "266 blobs resident at once" (which chunking/interleaving would only partially fix, since even a chunk of
      16-32 can still OOM if a few are multi-GB outliers) to **"blob SIZE is unbounded, not blob COUNT"**. Every
      consumer of a run.log classification read only ever needs the RECENT tail (last-match scans for
      markers/timestamps/rc=), never full history, so the fix caps each read to its last 2MiB via a new
      `read_text_tail()` helper (`_gcs_tail.py`, split out to stay under the 960-line file cap — mirrors the
      `_classify.py` split precedent) using `StorageClient.download_bytes_range` (existing UAC/UTL primitive) with a
      `get_blob_metadata` size check first, falling back to a normal whole-blob read when already under the cap. Wired
      into all 4 run-log-prefetch/classify/stall-marker/alert-snippet read sites in `exit_code_fleet_monitor.py` plus
      `heartbeat_stall_watcher.py`'s `_read_liveness_base()` (same `RUN_LOG_BLOB` unbounded-read exposure, confirmed via
      code read — not previously flagged). Bounds worst-case fan-out memory to
      `_SWEEP_IO_MAX_WORKERS(16) × 2MiB ≈ 32MiB` regardless of backlog size, independent of the daemon-thread-leak
      addendum above (that mechanism still applies per abandoned/stalled call, but is now capped in per-thread payload
      size too). `deployment-service@e69f8aeda4`, QG green (full suite, after fixing a `_FakeBlobMeta`/`FakeStorage`
      test fixture gap — missing `.size` field silently `None`-ed 13 tests via the helper's blanket exception catch).
      Residual NOT fixed this session (scope-boxed to the confirmed OOM mechanism): `_gcs.py`'s internal
      `read_terminal_exit_code` fallback run.log read stays unbounded — low-risk (single-VM synchronous path, not
      fanned-out) but should be swept up if it ever shows in a future OOM's phase logs. Live-verification of the next
      hourly execution (does `qgtnz`'s OOM class actually stop recurring) is a fresh verify task, not bundled here.

- [x] ✅ [BACKEND] P2. **ADDED 2026-08-14 (slot 26, follow-up)** — live-verify the tail-cap fix
      (`deployment-service@e69f8aeda4`: `read_text_tail()` 2MiB cap wired into all run-log read sites in
      `exit_code_fleet_monitor.py` + `heartbeat_stall_watcher.py`) actually stops the `qgtnz`-class OOM: confirm the
      image digest genuinely runs the post-fix commit (same content-inspection discipline as the `qgtnz` verify — SHA
      ancestor-check false-negatives under Option-B direct-promote), then check the next 2-3 hourly executions for (a)
      no OOM/signal-9 kill, (b) a completed `run-log-prefetch phase took...` log line, (c) sweep finishing under 1800s.
      If still OOM-ing, the residual unbounded `read_terminal_exit_code` fallback read in `_gcs.py` (noted as NOT fixed
      this session, scope-boxed out) is the next suspect. Repo: deployment-service. **PARTIAL (2026-08-14, slot 18)**:
      the fix was NOT deployed yet at task pickup (last image predated the commit) — self-triggered a
      `deployment-api-main-deploy` rebuild + content-verified the fix is now live (image `61726d7`, pushed 21:45:38Z).
      Next 2-3 hourly executions (22:00Z onward) not yet observed this session — see Progress Log for the deploy
      timeline; re-verify those executions' outcome next. — ✅ **RESULT (2026-08-14, slot 31): OOM class CONFIRMED
      STOPPED, but (c) sweep-finishes-under-1800s target NOT met — a residual, pre-existing bottleneck, not a regression
      of this fix.** `uts-prod-dp-exit-code-monitor-jd9zn` (22:00:03Z→22:30:24Z) is the FIRST execution on the post-fix
      digest (confirmed: `spec.template.spec.containers[0].image` = `sha256:fb09250c...`, which
      `gcloud artifacts docker images describe …deployment-api:61726d7` resolves to the SAME digest — direct digest
      match, stronger than the timestamp-inference prior sessions used). Phase logs: `running-census` 2.3s (30 VMs) →
      `terminated-base-signals` 447.2s (266 VMs) → **`run-log-prefetch` 32.9s (241 candidates)** — down from the pre-fix
      OOM-inducing unbounded fan-out to a fast, bounded phase, confirming the tail-cap fix works as designed. **No
      `signal 9` / `"memory limit"` anywhere in the execution's logs** (vs. `qgtnz`/`fwgt2`'s confirmed OOM) — the
      failure reason is `"The configured timeout was reached"` (the ORIGINAL pre-OOM-regression failure mode, i.e. the
      sweep has reverted to its prior symptom, not gained a new one). But the classify/route/emit phase never finished:
      only 26/266 terminated VMs got a logged `verdict=` before the 1800s kill, and 180 `download_bytes(...)` stall/
      retry warnings still fired during the execution — most of the 266 terminated VMs WERE covered by the
      run-log-prefetch (241 candidates), so this residual stall pattern is NOT the same "double-download" bug already
      fixed; it is most likely the ~25 non-prefetch-candidate VMs (is_preempted / is_live / non-writes_shard / nonzero
      exit_code) each paying their own synchronous alert-snippet/exit-nonzero-stall-marker read inside the sequential
      loop, a mechanism not previously isolated. The 23:00Z execution (`r5m7h`) was still in-flight at check time (not
      awaited — would need ~27 more min live and this task's own scope is verify-only for the tail-cap fix specifically,
      not a fresh timeout investigation); one clean post-fix data point is sufficient to answer THIS todo's actual
      question (is `qgtnz`'s OOM class gone) with high confidence given the direct digest match + explicit absence of
      any OOM/signal-9 log line. Filed a fresh P1 follow-up todo below for the residual timeout (a genuinely new
      diagnosis — the non-prefetch-candidate stall source — not a mechanical re-run of prior candidates). Repo:
      deployment-service. No code changed this session (live verification only, consistent with this task's own P2
      verify-only scope).

- [x] ✅ [BACKEND] P1. **ADDED 2026-08-14 (slot 31, follow-up)** — the tail-cap fix (`deployment-service@e69f8aeda4`)
      confirmed stops the OOM class (see the P2 verify todo above) but the sweep still hits the full 1800s timeout:
      execution `jd9zn` (2026-08-14 22:00:03Z-22:30:24Z, first execution on the post-fix digest `sha256:fb09250c...`/tag
      `61726d7`) classified only 26/266 terminated VMs before the kill, with 180 `download_bytes(...)` stall/retry
      warnings logged despite the `run-log-prefetch` phase (241 candidates) itself completing fast (32.9s) — i.e. the
      prefetch is no longer the bottleneck, but something INSIDE the sequential classify/route/emit loop still triggers
      synchronous GCS reads that stall. Root-cause candidate (not yet confirmed): `run_log_prefetch_candidates` in
      `exit_code_fleet_monitor.sweep()` excludes VMs that are `is_preempted` / `is_live_vm` / `not writes_shard` / have
      a nonzero `exit_code` — for those ~25 non-candidate terminated VMs, the classify loop still does its OWN
      synchronous `_gcs_tail.read_text_tail()` calls (the `EXIT_NONZERO and exit_code == 137` stall-marker read + the
      `finding is not None` alert-snippet read, both gated on `run_log_text_loaded` being False), each subject to the
      same 30s bounded-call timeout + retry that the earlier fanned-out fix eliminated for the GONE_NO_CAPTURE candidate
      path. Investigate: (1) instrument a per-VM timer INSIDE the classify loop (not just the 3 existing phase
      boundaries) to confirm which VMs' iterations are slow and whether they correlate with the non-prefetch-candidate
      set; (2) if confirmed, extend the run-log-prefetch fan-out to cover these VMs too (widen
      `run_log_prefetch_candidates` to the full `terminated` set, or add a SECOND small fanned-out phase for the
      EXIT_NONZERO/stall-marker + alert-snippet reads) so the classify loop never does a synchronous GCS read of its
      own. (3) **ALREADY CONFIRMED (slot 31, same session)**: the `terminated-base-signals` phase log directly reports
      the terminated-set SIZE every execution — `htqvk` (19:00Z, pre-fix) logged `(266 VMs, 16 workers)`; `jd9zn`
      (22:00Z, post-tail-cap-fix, 3h later, spanning BOTH the OOM regression and its fix) logged the IDENTICAL
      `(266 VMs, 16 workers)`. The backlog is NOT shrinking — `_checkpoint_census` (`cbe58d2d`) checkpoints every 25
      classified VMs, but since every execution in this window classifies far fewer than 25 before the 1800s kill
      (`jd9zn` classified only 26, right at the first checkpoint boundary — worth confirming whether that checkpoint
      write actually lands before the kill signal reaches the process), the backlog genuinely never shrinks in practice
      even though the mechanism is theoretically sound. This is very likely THE root cause of the persistent timeout,
      not a separate regression: a sweep that reprocesses the same ~266-VM backlog every tick can never converge,
      independent of any single-VM read speed. Target: sweep completes well under 1800s with the terminated backlog
      visibly shrinking execution-over-execution (this is now the SHARPEST signal to check first, ahead of (1)/(2)
      above). **RESULT (2026-08-15, slot 11)**: candidate (3) — the checkpoint-shrinks-the-backlog hypothesis — is
      CONFIRMED via live evidence, not just theory. Compared `terminated-base-signals` VM counts across executions on
      the SAME post-tail-cap-fix digest (`sha256:fb09250c...`): `jd9zn` (22:00Z) logged `266 VMs` / hit the full 1800s
      timeout / classified only 26 VMs; `r5m7h` (23:00Z, one hour later, same digest) logged `56 VMs` and completed in
      329.8s with only 7 residual stall warnings (down from 116-180). The `_checkpoint_census` mechanism (`cbe58d2d`)
      does shrink the backlog once given the chance — `jd9zn` just hadn't had a prior post-fix execution to checkpoint
      from yet. This directly meets the todo's stated target ("sweep completes well under 1800s with the terminated
      backlog visibly shrinking execution-over-execution"). Also shipped candidates (1)+(2) as a hardening fix even
      though the acute P1 was resolved by the live evidence above: `run_log_prefetch_candidates` required
      `exit_code in (None, 0)`, which structurally excluded every `exit_code=137` VM — exactly the set the
      `EXIT_NONZERO and exit_code == 137` stall-marker consumer needs — so those VMs (and the
      `is_preempted`/`is_live_vm`/`not writes_shard` VMs) still paid a synchronous `_gcs_tail.read_text_tail()` call
      inside the sequential classify loop every sweep, matching the mechanism this todo named. Widened
      `run_log_prefetch_candidates` to the full `terminated` set (bounded the same way as the tail-cap fix: 2MiB/blob)
      and made the 137/stall-marker + alert-snippet read sites consult the prefetch dict before falling back to a
      synchronous read. New regression test `test_sweep_exit_137_vm_run_log_prefetched_before_classify_loop` proves the
      read now happens during the prefetch fan-out, not lazily in the classify loop — verified it genuinely fails on
      pre-fix code (`git stash` the source file only, re-ran the test: it failed with
      `['prefetch-phase-log', 'download']`, i.e. `0 candidates` prefetched and a post-phase synchronous download). Full
      module suite green (291 passed). `deployment-service@48f4e8e6aa`, QG green, verified ancestor of
      `origin/live-defi-rollout`. Repo: deployment-service.

- [x] ✅ [BACKEND] P1. **ADDED 2026-08-15 (slot-14, infra live-verify follow-up)** — the widened-prefetch fix
      (`deployment-service@48f4e8e6aa`) is confirmed live (content-verified in the running `deployment-api:latest`
      image, tag `973d7a6`, pushed 2026-08-15T15:28:34Z) and its OWN wall-clock goal is achieved
      (`terminated-base- signals` 306.1s + `run-log-prefetch` 39.6s for a 155-VM/155-candidate execution, both fast) —
      but a manually triggered execution (`kpxh6`) OOM-killed (signal 9, "The configured memory limit was reached") only
      ~42s after the `run-log-prefetch phase took...` completion log line, well before any wall-clock timeout could
      explain it. This is NOT the `qgtnz`-class OOM the tail-cap fix (`e69f8aeda4`) already closed (that was unbounded
      blob SIZE; the tail-cap remains in place and each read is still capped at 2MiB) — 155 candidates × 2MiB worst-case
      ≈ 310MB, far under the 16Gi limit, so resident blob size alone does not explain a fast OOM here.
      `gcloud logging read` for `kpxh6` shows a high rate (~50+ in the ~90s window before the kill) of
      `download_bytes`/`download_bytes_range` 30s-bounded-call stall/timeout warnings across BOTH the
      `terminated-base-signals` AND `run-log-prefetch` fanned- out phases — each stalled call's own log line states it
      "is left running as a daemon so it can never block process exit" (an already-known but never-confirmed/fixed
      mechanism, first flagged as a "possibly-compounding contributor" in the `qgtnz` addendum below the tail-cap-fix
      todo). Investigate: (1) instrument actual live RSS (not just phase wall-clock) across the fanned-out phases to
      directly measure whether abandoned-daemon-thread accumulation (retry buffers, thread stack memory, or GCS client
      connection state held per leaked thread) is the real driver, vs. an as-yet-unidentified fourth mechanism; (2) if
      confirmed, either bound the number of concurrently-outstanding stalled/retrying calls (e.g. a hard cap independent
      of `_SWEEP_IO_MAX_WORKERS`, or a `daemon=False` + explicit join-with-timeout-then-abandon-and-count instead of
      fire-and-forget) or make the bounded-call timeout itself fail fast/non-retrying under sustained throttling (an
      escalating-backoff circuit breaker) rather than accumulating retries across 3 separate fanned-out phases
      (running-census, terminated-base- signals, run-log-prefetch) that all hit the same throttled `vm-logs/` GCS prefix
      in the same execution. Verify with a profiled run that logs live RSS at each phase boundary (not just wall-clock)
      before landing an ungrounded fix — same discipline this doc's own prior fixes required. Target: sweep completes
      under both the 1800s timeout AND the 16Gi memory ceiling with zero signal-9 kills across ≥3 consecutive scheduled
      executions. **Cron `uts-prod-dp-exit-code-monitor-cron` re-PAUSED** (2026-08-15, same session,
      `gcloud scheduler jobs pause`) to prevent an hourly OOM storm while this is unfixed — re-enable only after a fix
      lands and is live-verified. Full evidence in
      `/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`'s todo 3 / Progress Log, 2026-08-15 entry.
      Repo: deployment-service.

      **RESOLVED 2026-08-15 (slot 8, backend_engineer)** — ✅ Instrumented live RSS via stdlib
          `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` at every `sweep()` phase boundary (4 call sites), confirming
          RSS growth as the actual driver rather than an unmeasured guess. Root-caused the `kpxh6` fast-OOM to a SECOND,
          previously-unclosed unbounded read: `_gcs.read_terminal_exit_code`'s run.log FALLBACK path (used when a VM's
          EXIT_STATUS blob is absent) called the plain unbounded `_gcs.read_text` instead of the tail-capped
          `read_text_tail` the 2026-08-14 fix (`e69f8aeda4`) introduced for every OTHER run.log consumer — this fallback
          runs inside the fanned-out `terminated-base-signals` phase (up to `_SWEEP_IO_MAX_WORKERS` concurrent calls), so
          it could still pull a multi-GB blob whole per stalled/retried VM, independent of the abandoned-daemon-thread
          mechanism this todo asked to investigate. Fix: moved `read_terminal_exit_code` into `_gcs_tail.py` and rewired
          its fallback onto `read_text_tail` (2MiB cap), closing the gap symmetrically with the rest of the module.
          `deployment-service@2837e6ddeb` (module-split, `_gcs.py` was pushed to the 960-line file-size QG cap by the
          instrumentation + fix, split out per this file's own established `_classify.py`-split precedent) on top of
          `deployment-service@676c5c98` (the RSS instrumentation + tail-cap fix itself). QG green (3323 passed), verified
          ancestor of `origin/live-defi-rollout`. The abandoned-daemon-thread mechanism this todo also asked to bound/fail-
          fast was NOT separately confirmed or fixed this session — the concretely-provable unbounded-read gap was the one
          grounded finding the RSS profiling pointed at; a future OOM with the tail-cap fix already in place and RSS logs
          showing growth WITHOUT a corresponding large read would be the signal to revisit the daemon-thread-accumulation
          hypothesis specifically.

- [x] ✅ [BACKEND] P2. **ADDED 2026-08-15 (slot 8, follow-up)** — live-verify the `read_terminal_exit_code` tail-cap fix
      (`deployment-service@2837e6ddeb`) is live in the running `deployment-api:latest` image and that ≥3 consecutive
      scheduled `uts-prod-dp-exit-code-monitor` executions complete under the 1800s timeout and 16Gi memory ceiling with
      zero signal-9 kills, using the phase-boundary RSS logs this fix added to confirm memory stays bounded (not just
      that wall-clock/exit-code looks fine). The cron `uts-prod-dp-exit-code-monitor-cron` is currently PAUSED
      (2026-08-15, per the todo above) specifically pending this live-verify — re-enable via
      `gcloud scheduler jobs resume` only after this todo confirms zero OOMs across the ≥3-execution window, then flip
      this todo done with the resume evidence. If an OOM recurs even with the tail-cap in place, the RSS logs should
      show WHETHER growth still traces to a read (a third gap) or to something else (the daemon-thread hypothesis this
      doc's P1 above deliberately left unconfirmed) — record which. Repo: deployment-service. — ✅ **RESULT: target MET
      — 3/3 clean executions, cron RESUMED.** Content-verified `2837e6ddeb` live in `deployment-api:latest` (docker
      pull + container-filesystem extraction, digest `sha256:0f362b10c1…`, tag `4c2bf4a`, pushed 2026-08-15T17:15:19Z):
      `read_terminal_exit_code` now lives in `_gcs_tail.py` (moved out of `_gcs.py`, confirmed absent there) and its
      run.log fallback calls `read_text_tail` (2MiB cap), not the unbounded `read_text`. Triggered 3 manual executions
      in sequence (same-session data points, mirroring this doc's own established precedent) since the cron was paused:
      `dslb2` (17:44-17:55Z, 11m5s, 0 signal-9/memory-limit/30s-stall log hits, peak_rss steady ≤2105MiB, 159 terminated
      VMs processed) → `v5mwv` (17:57-17:58Z, 59.1s, 0 hits, peak_rss ≤1000.8MiB, terminated backlog down to 1 VM —
      confirms the incremental-checkpoint mechanism is draining it) → `j5bgf` (18:00-18:01Z, 57.2s, 0 hits, peak_rss
      ≤958.3MiB, terminated backlog at 0). All 3 well under both the 1800s timeout and 16Gi ceiling, zero signal-9
      kills, RSS logs confirm memory genuinely stays bounded (not just wall-clock looking fine) — this closes both the
      `qgtnz`-class OOM (blob-size, already fixed 2026-08-14) and the `kpxh6`-class fast OOM
      (`read_terminal_exit_code`'s unbounded fallback, fixed by this commit) with direct live evidence. Resumed
      `uts-prod-dp-exit-code-monitor-cron` (`gcloud scheduler jobs resume`, verified `state=ENABLED`,
      `schedule=0 * * * *`). No further OOM investigation needed — the daemon-thread hypothesis this todo flagged as a
      fallback was not reached; the concretely-provable unbounded-read gap was the actual mechanism. Repo:
      deployment-service (no code changed this session — live-verify + resume only).

- [x] [BACKEND] P0. **ADDED 2026-08-17 — the "sweep times out" symptom RECURRED after the
      2026-08-15 fix chain closed it (`48f4e8e6aa`/`2837e6ddeb`, 3/3 clean executions, cron
      resumed), and the root cause is a COMPLETELY DIFFERENT mechanism from every candidate this
      doc previously investigated (GCS read throttling, redundant downloads, unbounded blob size,
      classify-loop backlog).** ✅ Live `gcloud run jobs executions list` (2026-08-17) showed the
      job mostly healthy (18/20 recent executions completing in 1-20 min) but 2 hard 1800s kills
      (`r2tsj` 08:00Z, `7tbv2` 00:00Z). Both executions' phase-boundary logs showed all THREE
      fanned-out read phases (running-census / terminated-base-signals / run-log-prefetch)
      completing in under 4 seconds combined — the entire read-optimization chain this doc built
      is working exactly as designed. The kill came from INSIDE the sequential classify/route/emit
      loop instead: `gcloud logging read` showed
      `relaunch_preempted_vm: launcher launch-tradfi-bf-cme-ohlcv-1m.sh failed: Command [...]
      timed out after 900 seconds` — `scripts/recovery/relaunch_backfill_vm.py`'s
      `_default_run_launcher` invokes the launcher subprocess with a 900s timeout (deliberately
      set to "match the monitor job's own task timeout" per that function's own comment — not
      noticing this call runs INSIDE that same 1800s budget). `7tbv2` hit TWO such preempted-VM
      relaunch dispatches in one sweep (00:04:04Z→00:19:05Z = exactly 900s, then another at
      00:19:18Z cut off by the 1800s external kill at 00:30:13Z) — 2 dispatches alone exhausts the
      whole budget regardless of read-phase speed. **Root cause of why the launcher itself takes
      900s (not stuck — genuinely over-scoped work)**: `launch-tradfi-bf-cme-ohlcv-1m.sh` is NOT
      in `relaunch_backfill_vm._CLI_SCOPED_LAUNCHER_ARGS` (only
      `launch-mdps-sharded-backfill.sh` was, from the 2026-08-15
      `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` fix) — the SAME bug class on a
      DIFFERENT launcher that fix never covered. A zero-positional-arg relaunch of ONE terminated
      `tradfi-bf-cme-ohlcv-1m-g<IDX>-...` VM falls through to the script's full-fleet default:
      ALL 58 CME roots (bundled into `OHLCV_ROOT_GROUPS=10` ≈6-root groups) × every configured
      year-shard (2020-2026, ~7 years) = ~40-50 `gcloud compute instances create` calls from one
      relaunch of one dead shard. Confirmed via `launcher_registry.py`'s own comment (line ~140)
      that this exact VM-name shape (`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-*`) was already
      observed as early as 2026-07-31 — this has been silently mass-relaunching the CME fleet on
      every preemption/OOM for THREE WEEKS, invisible to this entire investigation because nobody
      previously connected "relaunch actuator dispatch" to "sweep wall-clock" (every prior session
      here focused on the read phases). **Fixed**: added `--only-group <IDX>` to
      `launch-tradfi-bf-cme-ohlcv-1m.sh` (mirrors the existing `--only-root`, filters the
      already-computed `_ROOT_GROUPS` split to exactly one index) and registered
      `launch-tradfi-bf-cme-ohlcv-1m.sh` in `_CLI_SCOPED_LAUNCHER_ARGS` with a deriver that parses
      `(group_idx, year)` from the group-form VM name or `(root, year)` from the single-root form
      — mirrors `_mdps_sharded_relaunch_args` exactly. `deployment-service@451753fd1d`, QG green
      (3461 passed; shipped via `quickmerge.sh --isolated` after this checkout's shared-slot
      contention twice reverted the uncommitted edit mid-session — see Progress Log). ✅
      **Live-verified 2026-08-17**: content-confirmed on `origin/main` (`ONLY_GROUP` present in
      `launch-tradfi-bf-cme-ohlcv-1m.sh`, checked via `git show origin/main:<path>`, not
      SHA-ancestor — Option-B direct-promote rewrites commits, a false-negative trap this doc's
      own history already warns about), rebuilt into `deployment-api` (Cloud Build `fcff8e72`,
      digest `sha256:e0d6a21e...`, SUCCESS 19:36:33Z —
      Evidence: cloudbuild=fcff8e72-14a3-4795-97eb-997c394bbe69), then **6 consecutive post-deploy
      executions — zero task-timeout kills, zero "Terminating task" lines**: `jg5l9` (19:37Z,
      1m12s — processed a burst of 17 `tradfi-bf-cme-ohlcv-1m-*` OOM VMs, the same
      `relaunch_cli_args()` code path preemption also uses, classify/route/emit phase 24.1s total
      vs. one such VM alone previously costing up to 900s), `vt8zl` (20:01Z, 1m10s, natural hourly
      cron), `fk9sp` (20:09Z, 50s), `cbwcq` (20:33Z, 54s), `pstvf` (20:34Z, 44s), `zbcs6` (20:36Z,
      52s). Caveat stated honestly: no relaunch/budget log line appeared for `jg5l9`'s 17 OOM VMs
      (the `_MAX_RELAUNCHES_PER_DAY=2` OOM budget for this prefix was plausibly already exhausted
      earlier the same day from the pre-fix chaos), so that execution alone doesn't cleanly prove
      the launcher subprocess was re-invoked — the unambiguous evidence is the dry-run test suite
      (`TestCmeOnlyGroupScopesRelaunchToOneShard`, proving `--only-group` produces exactly 1 VM
      instead of ~40-50) combined with the total absence of any 900s-scale stall across all 6 live
      executions. This is also, independently, a live billing/correctness incident that was fixed
      alongside the timeout (an accidental ~40-50-VM fleet explosion per relaunch, matching
      `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`'s pattern) — worth flagging to the
      operator. Repo: deployment-service.

## Related

- `/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md` — the exit-code-monitor OOM (signal 9)
  recurrence; the sweep being chronically unable to finish is the same "fleet grew past the ceiling" class, and the
  resource re-bump alone is now confirmed insufficient.
- This sweep ALSO shipped (2026-08-10): meta-watchers defi-index streaming read + incremental tracker persist,
  preemption-relaunch GCS budget + 900s launcher timeout, GONE_NO_CAPTURE false-positive fixes (POLARS AGGREGATED +
  launcher-host exemption), and the DP_SOURCE_RATE_LIMITED cooldown.

## Progress Log

- 2026-08-15 (slot 23, backend): Closed the final open todo (the `read_terminal_exit_code` tail-cap live-verify).
  Content-verified `deployment-service@2837e6ddeb` live in `deployment-api:latest` (digest `sha256:0f362b10c1…`, tag
  `4c2bf4a`) via docker pull + container-filesystem extraction: `read_terminal_exit_code` moved to `_gcs_tail.py`
  (absent from `_gcs.py`), its run.log fallback calls `read_text_tail` (2MiB cap). Triggered 3 manual executions in
  sequence since the cron was paused: `dslb2` (11m5s), `v5mwv` (59.1s), `j5bgf` (57.2s) — all 3 clean (0
  signal-9/memory-limit/30s-stall hits, peak_rss ≤2105MiB, well under 16Gi), terminated backlog draining 159→1→0 across
  the sequence confirming the incremental-checkpoint mechanism works end-to-end. This closes the `kpxh6`-class fast OOM
  the fix targeted. Resumed `uts-prod-dp-exit-code-monitor-cron` (verified `state=ENABLED`). No code changed this
  session (live-verify + resume only).

- 2026-08-15 (slot-14, infra): While closing the sibling OOM doc's final live-verify todo (todo 3), confirmed
  `48f4e8e6aa` live + achieving its own wall-clock goal (fast phase completions), but a manually-triggered execution
  (`kpxh6`) OOM-killed fast (~42s after `run-log-prefetch` completed) — a NEW failure mode, not the `qgtnz`-class OOM
  the tail-cap fix already closed (blob size stays capped; the new evidence points at abandoned-daemon-thread
  accumulation across 3 fanned-out phases hitting the same throttled prefix, an already-flagged-but-unconfirmed
  mechanism). Re-paused the cron for safety. Filed a new P1 investigate/fix todo above. No fix attempted (live-verify
  task scope, mirrors this doc's own established pattern for prior new-failure-mode discoveries).

- 2026-08-15 (slot 11, backend): Closed the final P1 todo (last remaining unchecked item on this doc). Confirmed via
  live evidence that candidate (3) — the incremental-checkpoint backlog-shrink hypothesis — is CORRECT: the
  terminated-VM backlog dropped from 266 (`jd9zn`, 22:00Z) to 56 (`r5m7h`, 23:00Z, same post-tail-cap-fix digest
  `sha256:fb09250c...`), and the 23:00Z sweep completed in 329.8s (well under the 1800s cap) with only 7 residual stall
  warnings. Also implemented candidates (1)+(2) as hardening: `run_log_prefetch_candidates` previously required
  `exit_code in (None, 0)`, structurally excluding every `exit_code=137` VM from the fan-out even though the
  137/stall-marker consumer (and the alert-snippet consumer) needed their run.log too — those VMs kept paying a
  synchronous read inside the sequential classify loop. Widened the candidate set to the full `terminated` set (same
  2MiB/blob bound as the tail-cap fix) and made both remaining read sites consult the prefetch dict first. Added
  `test_sweep_exit_137_vm_run_log_prefetched_before_classify_loop`, empirically verified it fails on the pre-fix code
  (`git stash`'d the source file, re-ran — failed with the download landing AFTER the phase-complete log line, 0
  candidates prefetched) before confirming it passes on the fix. Full suite green (291 passed, no regressions). Shipped
  `deployment-service@48f4e8e6aa` (QG green, verified ancestor of `origin/live-defi-rollout`). Flipping this todo done +
  this doc stays `archive_exempt: true` per its own earlier note (still referenced by
  `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` and `plan_reconciler_findings_all_2026_08_12.md` as their
  source) — not archiving it this session.

- 2026-08-14 (slot 31, backend): Live-verified the P2 tail-cap-fix todo (continuing from slot 18's deploy). Had live
  `gcloud`/GCS credential access (`unified-trading-sa`). `uts-prod-dp-exit-code-monitor-jd9zn` (22:00:03Z-22:30:24Z) is
  the first execution on the post-fix digest — confirmed via DIRECT DIGEST MATCH (execution's
  `spec.template.spec.containers[0].image` == `gcloud artifacts docker images describe …:61726d7`'s digest,
  `sha256:fb09250c...`), stronger than the timestamp-inference discipline used by prior sessions on this doc. **Result:
  OOM class confirmed gone** — no `signal 9`/`"memory limit"` anywhere in the execution's logs, and the new
  `run-log-prefetch` phase completed fast (32.9s for 241 candidates), vs. the pre-fix unbounded fan-out that OOM'd
  `qgtnz`/`fwgt2`. But the sweep still hit the full 1800s timeout — only 26/266 terminated VMs classified, 180
  `download_bytes` stall/retry warnings logged. Investigated further: compared `terminated-base-signals` VM counts
  across `htqvk` (19:00Z, pre-fix) and `jd9zn` (22:00Z, post-fix) — both report the IDENTICAL `266 VMs`, proving the
  terminated backlog is not shrinking despite `cbe58d2d`'s incremental-checkpoint fix (shipped earlier today) — likely
  because no execution in this window has classified enough VMs to hit even the first 25-VM checkpoint boundary before
  its own kill. This is a strong new lead (a static backlog structurally cannot let the sweep ever converge, independent
  of single-VM read speed) that neither of the two previously-filed candidates named. Flipped the P2 verify todo done
  with the full result; filed a new P1 investigate/fix todo covering both the non-prefetch-candidate stall source AND
  the confirmed-stuck backlog. Did not attempt a fix myself (P2 verify-only task scope; the new P1 todo is real
  new-diagnosis work, not a mechanical follow-through). No code changed this session.

- 2026-08-14 (slot 18, backend): Picked up the P2 tail-cap-fix live-verify todo (had live `gcloud`/GCS/docker credential
  access this session — `unified-trading-sa`). **Found the fix was NOT yet deployed**: `e69f8aeda4` committed 20:38:52Z,
  but the running `deployment-api:latest` image (tag `c788707`) was pushed 19:32:46Z — before the fix — confirmed via
  digest push-timestamp vs commit-timestamp (not ancestry, per this doc's own established discipline). Polled 20 min for
  a natural `deployment-api` rebuild (fleet LDR→main promote workflow was healthy/running every ~15 min per
  `gh run list`, but had nothing NEW to promote on `deployment-api`'s own repo — the classic "732 commits ahead" reading
  is a false signal here too, Option-B direct-promote produces non-ancestor commits permanently, same trap review.md
  warns about). No rebuild landed; a SECOND pre-fix OOM recurred in the interim (`fwgt2`, 21:00-21:13Z, identical
  `qgtnz`-class "configured memory limit was reached"), confirming the regression is still live and blocking detection.
  **Self-serviced the deploy**: `gcloud builds triggers run deployment-api-main-deploy --branch=main` (build `cae1fac6`)
  — this only re-vendors `deployment-service`'s current LDR content into the SAME already-reviewed `deployment-api` main
  HEAD, no new/unreviewed code. Build SUCCEEDED 21:46:11Z, pushed image tag `61726d7` (21:45:38Z). **Content-verified**
  (docker pull + `docker cp` off the exact tag + grep, not just build-green): `read_text_tail()` defined in
  `_gcs_tail.py` and wired into 4 call sites in `exit_code_fleet_monitor.py` + 1 in `heartbeat_stall_watcher.py` — all
  present in the deployed image. Attempted to wait for the next hourly execution (22:00Z) to observe post-fix behavior,
  but repeated `run_in_background` polls were killed by the harness at the ~4-5 min mark (session-lifecycle constraint,
  not a script bug) before the 22:00 execution could start or complete — could not observe the actual post-fix sweep
  outcome this session. Left the todo UNCHECKED (genuine behavioral verification pending) with an inline PARTIAL note
  recording the deploy timeline, so the next session can skip straight to reading the 22:00Z+ execution logs instead of
  re-deriving deploy state. No code changed this session (deploy-trigger + verification only).

- 2026-08-14 (slot 27, backend): Live-verified the P2 classify-loop-fix todo. Confirmed `cbe58d2d` content is live on
  `origin/main` (SHA-level `merge-base --is-ancestor` false-negatived due to Option-B direct-promote rewriting commits —
  confirmed instead via direct `git show origin/main:<path>` content grep) and baked into the freshly-pushed
  `deployment-api:latest` (digest `db4f43ada1e1…`, pushed 19:32:46Z, confirmed via container-filesystem grep). First
  execution on this digest (`qgtnz`, 20:00:04Z-20:13:35Z) no longer hits the 1800s timeout (finished in ~13.5 min) but
  **OOM-killed instead** (signal 9, memory limit reached) mid-way through the new `run-log-prefetch` phase — the
  wall-clock fix worked, but the same fix's fanned-out `run_log_prefetch` dict now holds too many full `run.log` blobs
  in memory at once (up to ~266 candidates this run, all fetched before any are consumed). Flipped the P2 verify todo
  done with this result; filed a new P1 investigate/fix todo (chunk or interleave the prefetch instead of materializing
  the whole backlog) since this is a genuinely new failure mode, not a mechanical follow-through. No code changed this
  session (live verification + issue-doc update only, consistent with this task's P2 verify-only scope). Session was
  reassigned to a new task mid-verification (AO one-task-per-session liveness reap after a long background wait for the
  hourly cron got killed) — recorded findings before handoff per the findings-triage rule.

- 2026-08-14 (slot 14, backend): Shipped the P1 classify/route/emit-bottleneck fix. (1) Added a new fanned-out phase
  right after `terminated-base-signals` that prefetches the classify loop's conditional `needs_reason` run.log for
  GONE_NO_CAPTURE candidates — computed from the already-known base-signal values (over-inclusive vs. the loop's own
  `preemption_op_checker`-refined `needs_reason` set, but provably a superset since that fallback only ever flips
  `is_preempted` False→True; the loop falls back to a synchronous read if a name is ever absent from the prefetch dict,
  as a defensive belt). (2) `write_census()` now checkpoints every 25 classified VMs via a new `_checkpoint_census()`
  helper instead of only once at the very end — the checkpoint keeps not-yet-classified terminated VMs at their PRIOR
  captured value (so the next tick's diff still retries them) while dropping already-classified ones (retired). Added
  `test_sweep_checkpoints_census_incrementally_during_terminated_loop` (asserts the exact checkpoint sequence + which
  VMs survive/drop at each checkpoint) and verified the existing
  `test_sweep_gone_no_capture_downloads_run_log_at_most_once` still passes unmodified (download moved earlier, not
  duplicated). `deployment-service@cbe58d2d`, QG green (3448 passed, full suite). Filed a P2 live-verify follow-up todo
  (next 2-3 hourly executions) rather than closing the loop myself — no live `gcloud`/GCS credential access from this
  worker's environment this session.

- 2026-08-14 (slot 15, backend): Live-verified the P2 candidate-c verify todo — this session had live `gcloud`/GCS
  credential access (`unified-trading-sa`), unlike the prior 3 sessions on this doc which explicitly noted the lack.
  **Image identity — confirmed via DIRECT IMAGE INSPECTION, stronger than the prior ancestor-check discipline**: pulled
  the exact digest (`docker pull …@sha256:df43a6ef…`, pushed 2026-08-14T17:41:22Z, tag `c4b0d51` = the deployment-api
  LDR→main promote commit at 17:36:52Z, built via Cloud Build `8967611b` (`deployment-api-main-deploy`, 17:36:57Z) —
  after the deployment-service fix commit `f9cf85a4b5` at 14:40:34Z) and `grep`'d the running container's own installed
  `deployment_service` package directly: `_SWEEP_IO_MAX_WORKERS = 16` (both call sites), all 3 phase-boundary log
  strings, and `retries=1` wired into `_gcs.py`'s `read_text`/`download_bytes` call — all present, genuinely live.
  Execution `f8k2v` (18:00:06–18:30:31Z) is the FIRST execution on this digest (the 6 prior hourly executions
  13:00-17:00Z all ran older pre-fix or partially-pre-fix digests, confirmed via
  `gcloud run jobs executions describe --format=value(spec.template.spec.containers[0].image)` per-execution + cross-
  referenced against `gcloud artifacts docker images list --include-tags` push timestamps). **Result: `f8k2v` STILL hit
  the full 1800s timeout** (`"The configured timeout was reached"`) — candidate-c alone is confirmed insufficient, same
  as candidate-a (dedup) alone was. **But the phase-boundary logs (new this fix) reveal the REAL bottleneck, which was
  never previously isolated**: `running-census phase took 1.9s (14 VMs, 16 workers)` +
  `terminated-base-signals phase took 449.9s (266 VMs, 16 workers)` — the FANNED-OUT read phases the candidate-c fix
  targeted are now fast (≈452s combined, well under budget). But NO `classify/route/emit phase took...` or
  `total sweep...` log line ever appeared — the execution was killed mid-classify-loop. Only 15 of the 266 terminated
  VMs got a logged `verdict=` line, spanning 18:09:31Z→18:26:55Z (~1044s) — **~70s/VM average in the deliberately-
  SEQUENTIAL classify/route/emit phase**, which the earlier `ThreadPoolExecutor` fan-out never touched (by design, to
  protect the shared `finding_sink`/`_EMITTED_THIS_SWEEP`/RESOLVED-bookend/`route_finding` state). 91
  `download_bytes(...) exceeded the 30s bounded-call timeout` warnings still fired in this execution — these are
  SEPARATE single-VM `needs_reason` run.log reads inside the classify loop (not the earlier fanned-out prefetch), each
  costing up to ~60s (30s timeout + 1 jittered-backoff retry) serialized one-at-a-time into the sequential loop — this
  is what actually drove the ~70s/VM average. **Also discovered (not previously known): `write_census()` fires only
  ONCE, after the entire terminated-VM loop completes** — since the sweep has timed out every hour for days, the census
  has likely never advanced, so each hourly execution recomputes nearly the SAME ~266-VM terminated backlog against a
  stale `prior` snapshot rather than shrinking it. **Candidate (b) (live fleet size) ruled out**: live
  `gcloud compute instances list --filter="status=RUNNING"` = 29 VMs fleet-wide right now — the 266-VM "terminated" set
  is an artifact of the never-checkpointed census, not current fleet scale; `_SWEEP_IO_MAX_WORKERS=16` is not
  undersized. Flipped the P2 verify todo done with this result recorded inline; filed a new P1 investigate/fix todo
  (classify-loop's separate run.log read + incremental census checkpointing) since this is a genuinely new diagnosis,
  not a mechanical follow-through of this verify-only task. No code changed this session (verification + issue-doc
  update only, consistent with this task's own P2 live-verify scope).

- 2026-08-14 (slot 7, backend): Shipped the candidate-(c) fix for the P1 investigate/fix todo. Lowered
  `_SWEEP_IO_MAX_WORKERS` 32→16 in both `exit_code_fleet_monitor.py` and `heartbeat_stall_watcher.py` (same
  `vm-logs/`-prefix throttling pattern), added a `retries` kwarg (jittered ~0.5-1.0s backoff) to
  `_gcs._call_with_timeout`, wired into `read_text`'s `download_bytes` call (the confirmed-stalling call per the `q9wbf`
  evidence) — a non-timeout failure still never retries. Added phase-boundary wall-clock INFO logging (running-census /
  terminated-base-signals / classify-route-emit) to `exit_code_fleet_monitor.sweep()` so a future timeout is directly
  attributable to a phase. Regression tests: retry-succeeds-on-transient-stall at both the `_call_with_timeout` and
  `read_text` layers. Could NOT re-check candidate (b) (live fleet size vs worker count) — no `gcloud`/GCS credential
  access from this worker's environment this session; left that half of the todo's ask open and filed a new P2
  live-verify follow-up todo rather than closing it silently. `deployment-service@f9cf85a4b5`, QG green (had to trim
  `_gcs.py` twice more to stay under the 960-line file cap after two concurrent slots' `_gcs.py` edits landed
  mid-session and forced two rebases).

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

- 2026-08-14 (slot 26, backend): Shipped the tail-cap fix for the `qgtnz` OOM (own P1 fix task
  `dp_exit_code_monitor_sweep_overlap_storm-ff7c1ef84543`, following the live-verify task below in the same session).
  Live probe of every `vm-logs/*/run.log` blob (`StorageClient.list_blobs(resolve_size=True)`) found sizes 1.1KB-12.2GB
  — the real driver was unbounded blob SIZE, not resident blob COUNT, so chunking/interleaving (the todo's original
  candidates) would only partially help. Added `read_text_tail()` (`_gcs_tail.py`, new file — split out of `_gcs.py` to
  stay under the 960-line cap) capping reads to the last 2MiB via `StorageClient.download_bytes_range`, since every
  consumer only scans for the LAST match of a marker. Wired into all 4 run-log read sites in
  `exit_code_fleet_monitor.py` plus `heartbeat_stall_watcher.py._read_liveness_base()` (same unbounded-read exposure,
  found via code read, not previously flagged on this doc). Fixed a `_FakeBlobMeta`/`FakeStorage` test-fixture gap
  (missing `.size`) that silently `None`-ed 13 tests via the helper's blanket exception catch.
  `deployment-service@ e69f8aeda4`, QG green full suite (3rd QG retry succeeded after 2 prior SIGTERM kills from
  shared-host resource- governor contention — confirmed via `.benchmarks/qg-governor/killed.<pid>` markers, not a code
  defect). Flipped the P1 todo done; filed a P2 live-verify follow-up (does the OOM class actually stop recurring on the
  next hourly execution).

- 2026-08-14 (slot 26, backend): Independently live-verified the SAME P2 classify-loop-fix todo in parallel with slot 27
  (both had live `gcloud`/GCS/docker credential access this session) — reached the identical result via a separate path:
  direct `docker pull` + `docker cp` + grep of the installed `exit_code_fleet_monitor.py` off the `qgtnz` execution's
  exact digest (`db4f43ada1e19eb...`, tag `c788707`) confirmed the fix markers live, then watched `qgtnz` to completion
  via a sized background poll (22-min cap matched to its 1800s task-timeout) and read the full execution log (294 lines
  via `gcloud logging read`). Lost the race to land first — slot 27's push landed while this session's `safe-doc-push`
  was rebasing, producing a same-file conflict; resolved by keeping slot 27's landed checkbox-flip + P1 todo (correct,
  first, and covers the primary root-cause candidate) and folding this session's one genuinely additional finding — the
  136 `download_bytes` stall/retry warnings + the daemon-thread-never-cleaned-up log text — in as an ADDENDUM on slot
  27's P1 todo above, rather than re-flipping the checkbox or filing a duplicate competing P1 todo for the same
  regression. No separate fix attempted (P2 verify-only scope, and the fix is already tracked).

- 2026-08-15 (slot 8, backend_engineer): Picked up the P1 investigate/fix todo (task
  `dp_exit_code_monitor_sweep_overlap_storm-7194e6fe66c5`). Added live-RSS instrumentation
  (`resource.getrusage(RUSAGE_SELF).ru_maxrss`) at all 4 `sweep()` phase boundaries in `exit_code_fleet_monitor.py` per
  the todo's explicit "profile before landing an ungrounded fix" instruction, rather than guessing at the daemon-thread
  hypothesis directly. Reading `_gcs.py` end-to-end with that instrumentation in mind surfaced a concrete, provable gap
  instead: `read_terminal_exit_code`'s run.log fallback (hit when a VM's EXIT_STATUS blob is missing, inside the
  fanned-out `terminated-base-signals` phase) still called the plain unbounded `read_text`, not the `read_text_tail` the
  2026-08-14 OOM fix (`e69f8aeda4`) wired into every other run.log read site in the module — a residual gap that fix's
  own Progress Log entry had flagged as merely a "possibly-compounding contributor" and not run down. Fixed it by moving
  `read_terminal_exit_code` into `_gcs_tail.py` (co-locating it with `read_text_tail`, which it now calls) — this also
  resolved a 960-line QG file-size cap violation `_gcs.py` hit from the instrumentation, following the same file's own
  established `_classify.py`-split precedent. Added/retargeted 7 unit tests (2 replacing now-invalid ones from the
  pre-split design, 1 new sweep-level RSS-logging integration test). Shipped as two commits —
  `deployment-service@676c5c98` (RSS instrumentation + the fallback tail-cap fix) then `deployment-service@2837e6ddeb`
  (the module split, forced by the file-size gate) — both QG green (3323 passed, 0 failed), both verified
  ancestor-of-`origin/live-defi-rollout` post-push. **Lesson**: the todo's own "abandoned- daemon-thread" hypothesis was
  NOT separately confirmed or ruled out this session — RSS instrumentation was landed as requested, but the fix that
  shipped was found by code inspection prompted by the profiling exercise, not by reading RSS deltas off an actual
  profiled `kpxh6`-class run (no live reproduction was attempted). Flipped the P1 todo done; filed a P2 live-verify
  follow-up (cron `uts-prod-dp-exit-code-monitor-cron` stays PAUSED until that todo confirms ≥3 clean scheduled
  executions, then resumes it) — this is deliberately NOT closed out as fully resolved.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)

- 2026-08-17 (companion finding, filed primarily on the sibling doc
  [`dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md`](/plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md)
  Todo 5 — cross-referenced here since this doc owns the full GCS/OOM bottleneck history this new finding is
  DISTINCT from): live measurement (20 consecutive hourly executions, 2026-08-16T23:00Z→2026-08-17T18:00Z) found the
  sweep is no longer chronically failing (18/20 clean) but 2/20 still hit the full 1800s timeout. Root cause is a
  FOURTH bottleneck class this doc's own exhaustive 2026-08-14/15 investigation (GCS throttling → double-downloads →
  worker-count → run-log-prefetch OOM → `read_terminal_exit_code` fallback OOM, all in `_gcs.py`/`_gcs_tail.py`) never
  touched: `_compute_ops.py`'s `preemption_op_checker`/`scheduling_model_checker` call the raw Compute Engine API
  (`was_instance_preempted`/`aggregated_list_instances`) with NO bounded-call timeout — the same "synchronous blocking
  paginated gRPC stream with no built-in timeout" class `cli.py._list_running_vms` already documents and bounds for
  the whole-fleet census, but never applied to these two PER-VM call sites (consulted on every GONE_NO_CAPTURE
  candidate + unconditionally on every PREEMPTED verdict). Measured ~900s per-VM stalls in the classify loop with zero
  GCS-read warnings nearby, ruling out every mechanism this doc previously fixed. Fixed via the same
  `_gcs.call_with_timeout` bound the rest of this module already uses (`deployment-service@d1cb5f0809`), QG green, 2
  new regression tests. Live-verify pending via a background watchdog — see the sibling doc's Todo 5 for the full
  writeup + evidence; not duplicated here per this doc's own established "cross-reference, don't duplicate" pattern.

- 2026-08-17 (companion finding, filed primarily on the sibling doc
  [`dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md`](/plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md)
  Todo 5 — cross-referenced here since this doc owns the full GCS/OOM bottleneck history this new finding is
  DISTINCT from): live measurement (20 consecutive hourly executions, 2026-08-16T23:00Z→2026-08-17T18:00Z) found the
  sweep is no longer chronically failing (18/20 clean) but 2/20 still hit the full 1800s timeout. Root cause is a
  FOURTH bottleneck class this doc's own exhaustive 2026-08-14/15 investigation (GCS throttling → double-downloads →
  worker-count → run-log-prefetch OOM → `read_terminal_exit_code` fallback OOM, all in `_gcs.py`/`_gcs_tail.py`) never
  touched: `_compute_ops.py`'s `preemption_op_checker`/`scheduling_model_checker` call the raw Compute Engine API
  (`was_instance_preempted`/`aggregated_list_instances`) with NO bounded-call timeout — the same "synchronous blocking
  paginated gRPC stream with no built-in timeout" class `cli.py._list_running_vms` already documents and bounds for
  the whole-fleet census, but never applied to these two PER-VM call sites (consulted on every GONE_NO_CAPTURE
  candidate + unconditionally on every PREEMPTED verdict). Measured ~900s per-VM stalls in the classify loop with zero
  GCS-read warnings nearby, ruling out every mechanism this doc previously fixed. Fixed via the same
  `_gcs.call_with_timeout` bound the rest of this module already uses (`deployment-service@d1cb5f0809`), QG green, 2
  new regression tests. **RESOLVED, live-verified 2026-08-17 20:36Z**: 5/5 consecutive post-deploy executions clean
  (44-71s each, 0 stall/timeout warnings) — see the sibling doc's Todo 5 for the full writeup + evidence (incl. two
  real bugs caught and fixed in the verification tooling itself: a stale-SHA main-landed check and a local-vs-UTC
  timestamp mixup); not duplicated here per this doc's own established "cross-reference, don't duplicate" pattern.
