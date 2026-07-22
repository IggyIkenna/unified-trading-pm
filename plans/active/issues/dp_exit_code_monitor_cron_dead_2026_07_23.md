---
doc_type: issue
title:
  "uts-prod-dp-exit-code-monitor Cloud Run job has HUNG-and-timed-out on every single 5-minute execution since
  2026-07-19 12:05:01 UTC (~990 consecutive failures, ~83h and climbing) -- the Cloud Scheduler itself is healthy and
  firing on schedule, the underlying job body never completes; likely root cause an untimed GCS read added
  2026-07-19T12:01:35Z, same failure class as the already-documented gcsfs stall; a SEPARATE, real bug found in the
  alert path itself -- DP_CRON_DID_NOT_FIRE has no re-nag cooldown and is spamming every 15min meta-sweep"
summary: >-
  `data-pipeline-alerts` fired DP_CRON_DID_NOT_FIRE (CRITICAL) repeatedly 2026-07-22 23:16 through 00:02 for
  `dp-exit-code-monitor`, staleness climbing 4935m -> 4981m. Investigation (`gcloud run jobs executions list/describe`,
  read-only) confirms this is REAL, not a false alarm: `uts-prod-dp-exit-code-monitor` (Cloud Run job backing the `*/5 *
  * * *` `uts-prod-dp-exit-code-monitor-cron` Cloud Scheduler job, which IS `ENABLED` and IS firing every 5 minutes as
  designed) has failed EVERY execution since `uts-prod-dp-exit-code-monitor-vm44f` at 2026-07-19T12:05:01Z (the prior
  execution, `qs2jw` at 12:00:01Z, was the last success) -- each failure is `"Task ... failed with exit code: 0 and
  message: The configured timeout was reached"` (a HANG that runs past the 300s Cloud Run task timeout, not a crash/OOM
  -- OOM was the June 2026-06-23 incident, already fixed by bumping to 8Gi/cpu2). Live logs from today's executions show
  the job makes ~20s of real progress (init, one VM verdict logged) then goes completely silent for the remaining ~4.5
  minutes until Cloud Run kills it. Leading hypothesis: an untimed GCS read (`_gcs.read_progress_checkpoint`, added to
  `exit_code_fleet_monitor.sweep()` in `deployment-service@c138957`, landed 2026-07-19T12:01:35Z -- ~3.5 minutes before
  the first failure, consistent with CI build/deploy latency) hangs on some VM in the fleet the same way the
  already-filed `mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md` finding describes for a different
  repo/script. SEPARATE finding: `DP_CRON_DID_NOT_FIRE` itself has no re-nag/cooldown suppression in
  `meta_watchers.check_cron_fired` (unlike its sibling `DP_RUN_MOSTLY_EMPTY`, which got a 30-min `RenagTracker` cooldown
  fix for this EXACT spam pattern on 2026-07-15) -- so it re-pages on every 15-minute meta-sweep for as long as the
  underlying condition holds, which is why this alert (and likely `DP_VM_GONE_NO_CAPTURE` if it shares the same gap)
  fired every ~15-16 minutes rather than deduping per CLAUDE.md's "fire on change / RESOLVED / re-remind, never every
  tick" rule.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [alerting, monitoring, cron, infra, reliability, untimed-gcs-read, dp-exit-code-monitor, renag]
related:
  [
    plans/active/issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md,
    plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md,
    plans/archive/issues/exit_code_fleet_monitor_clean_misclassifies_premature_kill_2026_07_21.md,
  ]
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: >-
  `data-pipeline-alerts` Slack channel, DP_CRON_DID_NOT_FIRE / dp-exit-code-monitor, fired 2026-07-22 23:16, 23:32,
  23:48, 00:02 (staleness 4935m -> 4950m -> 4965m -> 4981m). Investigated read-only via `gcloud scheduler jobs
  describe`, `gcloud run jobs executions list/describe`, `gcloud logging read` (Cloud Run job + audit logs), and `git
  log`/source read of `deployment-service`. No `gcloud` mutation, trigger, enable/disable, or manual run was executed as
  part of this investigation.
resolved_by:
---

## What happened (VERIFIED, not inferred)

### 1. The Cloud Scheduler job is healthy -- the underlying Cloud Run job body is not

`gcloud scheduler jobs describe uts-prod-dp-exit-code-monitor-cron --project=central-element-323112 --location=asia-northeast1`
(found via `gcloud scheduler jobs list`, which returned 50 jobs; the name is `uts-prod-dp-exit-code-monitor-cron`, not
the un-prefixed `dp-exit-code-monitor` guessed in the task brief):

```
schedule: '*/5 * * * *'   (UTC)
state: ENABLED
lastAttemptTime: 2026-07-22T23:05:01Z    -- i.e. it fired ON TIME, 4 min before the investigation started
scheduleTime:    2026-07-22T23:10:00Z    -- and its NEXT tick was already correctly queued
httpTarget.uri:  .../namespaces/central-element-323112/jobs/uts-prod-dp-exit-code-monitor:run
```

The scheduler is doing its job: firing the target Cloud Run **Job** `uts-prod-dp-exit-code-monitor` every 5 minutes,
without interruption. The alert's own wording ("the cron stopped firing") is a **slight mischaracterization** -- the
correct framing is "the cron fires on schedule but its body never completes," which matters for the fix (nothing to
re-enable; the JOB needs debugging, not the SCHEDULER).

### 2. The Cloud Run job has failed EVERY execution for ~83 hours straight

`gcloud run jobs executions list --job=uts-prod-dp-exit-code-monitor --project=central-element-323112 --region=asia-northeast1 --limit=1000`
(job has been "Executed 8764 times" total, per `jobs describe`):

- **Last success**: `uts-prod-dp-exit-code-monitor-qs2jw`, started `2026-07-19T12:00:04Z`, `1/1` complete.
- **First failure**: `uts-prod-dp-exit-code-monitor-vm44f`, started `2026-07-19T12:05:04Z`, `0/1` complete -- **the very
  next scheduled tick after the last success**, no gap.
- **Every execution since** (verified by scanning the full 1000-execution page back past 2026-07-19T12:05, plus
  spot-checks at 06:30, 09:xx, 11:xx, 16:xx, 22:xx, 23:0x on both 2026-07-19 and 2026-07-22): `0/1`, same failure
  message. At `*/5` cadence, `2026-07-19T12:05Z` -> `2026-07-22T23:08Z` (when this investigation started) is **~83.05
  hours = ~997 consecutive failed executions**, closely matching the alert's own 4935m-4981m (82.25h-83.02h) staleness
  readings (the small delta is the gap between the last successful _sentinel write_ -- which happens at end-of-sweep,
  slightly after the process starts -- and the scheduler's `lastAttemptTime`).
- `gcloud run jobs executions describe uts-prod-dp-exit-code-monitor-vm44f` shows the failure reason directly:
  `"Task uts-prod-dp-exit-code-monitor-vm44f-task0 failed with exit code: 0 and message: The configured timeout was reached."`
  -- **this is a HANG that outlives the job's `timeoutSeconds: 300` (5 min) limit, not a crash or exception** (exit code
  0 confirms the process was killed externally by Cloud Run, not that it exited/raised on its own). This directly rules
  out a repeat of the 2026-06-23 OOM incident on this same job (`dp_alert_flood_triage_and_ monitor_fixes_2026_06_23.md`
  -- OOM was signal 9 at 2Gi, already fixed by bumping to 8Gi/cpu2, confirmed still in place via
  `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`: `cpu=2, memory=8Gi, timeout_seconds=300, max_retries=0`).

### 3. Live logs show WHERE it hangs -- consistent across every recent execution sampled

`gcloud logging read` for the 3 most recent executions (`7pbsj` 23:05:01Z, `56slm` 23:00:01Z, `fft57` 22:55:01Z, all
2026-07-22) shows the **identical** pattern, timestamps only shifting:

```
HH:MM:38  INFO    Event logging initialized: mode=live, service=dp-fleet-monitor
HH:MM:55  WARNING dispatch: repository_dispatch HTTP 422 (best-effort): HTTP Error 422: Unprocessable Entity
HH:MM:55  WARNING exit_code_fleet_monitor: canonical-migration-cefi-content-20260719-121302 verdict=gone_no_capture
                    exit_code=None captured=0->0
[... total silence for ~4.5 minutes ...]
HH+4:MM   ERROR   Terminating task because it has reached the maximum timeout of 300 seconds.
```

The job starts, evaluates exactly ONE VM (the same wedged `canonical-migration-cefi-content-20260719-121302` that a
parallel investigation is separately tracking), logs its verdict, then produces **zero further output** until Cloud Run
kills it. The very FIRST failing execution (`vm44f`, 2026-07-19T12:05Z) is different in one respect: its
`resource.type="cloud_run_job"` application-log stream is completely EMPTY (only the Cloud Run system `RunJob` audit
-log entry exists) -- meaning that one hung even before printing the "Event logging initialized" line, or before any
app-level log reached Cloud Logging. Both are consistent with a hang inside the sweep loop; the exact hang point appears
to differ execution-to-execution (which VM in the fleet trips it), while the SYMPTOM (never completes, whatever line was
last printed) is identical every time.

## Root cause -- leading hypothesis (well-evidenced, NOT proven with a stack trace)

**Timing correlation**: `deployment-service@c138957` ("feat(deployment): SPOT preemption resume-from-PROGRESS checkpoint
(reader side)") landed `2026-07-19T13:01:35+01:00 = 12:01:35 UTC` -- **3.5 minutes before the first failure** (`vm44f`,
12:05:04Z), well within normal CI build+push+redeploy latency for a `:latest`-tagged Cloud Run job image (confirmed the
job resolves `:latest` per-execution, not a pinned digest -- `vm44f`'s resolved image sha `...1fc49097...` differs from
today's `...261137b8...`, i.e. a NEW image landed between them without any Terraform "last updated" bump, exactly what a
`:latest` push would produce).

**What that commit changed** (`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`, `sweep()`): added
a new call, gated `if is_preempted`:

```python
progress_checkpoint = _gcs.read_progress_checkpoint(storage_client, log_bucket, name) if is_preempted else None
```

`read_progress_checkpoint()` (new in the same commit, `deployment_service/data_pipeline_monitors/_gcs.py:587`) and the
pre-existing sibling `read_launch_params()` (same file, line 544, similarly gated `if is_preempted`) both funnel through
`read_text()` (line 386):

```python
def read_text(storage_client: StorageClient, bucket: str, blob_path: str) -> str | None:
    try:
        if not storage_client.blob_exists(bucket, blob_path):
            return None
        return storage_client.download_bytes(bucket, blob_path).decode("utf-8", errors="replace")
    except Exception:
        return None
```

**No timeout parameter is passed to either `blob_exists()` or `download_bytes()` anywhere in this file** (grepped the
whole file for `timeout` -- zero hits). If the underlying `unified_trading_library.StorageClient`'s default GCS HTTP
client has no read timeout (or a very long one) and hits a stalled connection, this call blocks forever -- the
`try/except Exception` only catches a raised exception, never a hang. **This is the identical failure class already
root-caused and fixed THIS SAME WEEK in a different repo/script**:
`plans/active/issues/ mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md` documents `gcsfs`-backed reads with
no timeout anywhere in the call chain hanging a `ThreadPoolExecutor` consumer indefinitely in `market-tick-data-service`
-- same defect shape (untimed cloud-storage read inside a time-bounded execution context), different repo and different
specific call site.

**Why the currently-logged VM (`gone_no_capture`) doesn't fully explain it**: `read_progress_checkpoint` is gated
`if is_preempted`, and the VM logged in every recent execution has verdict `gone_no_capture`, not `preempted` -- so that
logged line is not itself the hanging call. The most likely explanation is that `sweep()` continues iterating the fleet
after logging that VM's verdict and reaches a DIFFERENT VM later in iteration order that IS in a `preempted` state,
hanging there on the untimed read -- the `gone_no_capture` line is simply the last thing flushed before the loop reaches
the actual stuck VM. **This is a hypothesis, not a confirmed root cause** -- Cloud Run does not expose a stack trace or
thread dump for a killed task, so the exact hanging call was not directly observed, only inferred from (a) the timing
correlation with the commit, (b) the code pattern matching an already-proven failure class, and (c) the consistent "some
progress then total silence" log shape.

**The 2026-07-21 follow-up commit did not touch this** -- `2e22c54` ("fix(monitors): add PARTIAL_UNCONFIRMED verdict to
exit_code_fleet_monitor") landed 2026-07-21T04:07:39Z, two days after the hang started, and modified the same file, but
added a new verdict classification, not a timeout on any GCS read. The job has continued failing every 5-minute run
before AND after that commit -- consistent with it not being the fix (or the cause).

## SEPARATE finding: DP_CRON_DID_NOT_FIRE has no re-nag cooldown -- it pages every 15-minute meta-sweep, not on a dedup interval

The task brief flagged the ~15-16 minute repeat cadence (23:16, 23:32, 23:48, 00:02) as possibly a broken
dedup/cooldown. Read `deployment_service/data_pipeline_monitors/meta_watchers.py` (the module that emits
`DP_CRON_DID_NOT_FIRE` via `check_cron_fired()`) to check -- **confirmed real, but it is NOT the GH-Actions
`notify-slack.yml` carrier** the task brief guessed at (that carrier is for the separate `ci-failures` channel per
`codex/04-architecture/ci-alerting.md`); `data-pipeline-alerts` is a distinct, Python-side alerting path specific to the
`dp-*` fleet monitors.

- `MONITOR_CRON_CADENCE_MIN["meta"] = 15.0` -- the meta-watcher sweep (which runs `check_cron_fired`) itself runs every
  15 minutes. The observed ~15-16 min alert spacing is **exactly this sweep's own cadence**, not some intermediate
  cooldown value.
- `check_cron_fired()` uses `MissTracker` for **onset gating only** (a probe must be stale for `min_consecutive`
  consecutive sweeps before its FIRST page -- a good anti-flap gate, unrelated to this bug). Grepped the function body
  (lines ~684-860): **no `RenagTracker` reference anywhere in it.**
- Its sibling detector, `check_high_attempted_failed()` (emits `DP_RUN_MOSTLY_EMPTY`), DOES import and use
  `RenagTracker` (confirmed at `meta_watchers.py:118,151-152,537-641`) -- a 30-minute cross-sweep re-nag cooldown added
  2026-07-15 for **this exact symptom**: `deployment_service/data_pipeline_monitors/renag_tracker.py`'s own docstring
  states it was built because "`meta_watchers.MissTracker` gates ONSET only... it has no ongoing re-fire suppression, so
  a detector wired only with `MissTracker` re-emits an identical CRITICAL page every sweep for as long as the underlying
  condition stays true," citing `plans/active/issues/ dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` as the
  incident that motivated it.
- **That fix was never generalized to `check_cron_fired`/`DP_CRON_DID_NOT_FIRE`.** So this alert (and structurally any
  OTHER `check_cron_fired`-sourced page, plus possibly `DP_VM_GONE_NO_CAPTURE` if it shares the same gap -- not verified
  here, out of scope for this doc) re-fires on literally every meta-sweep for as long as the condition holds, in direct
  violation of CLAUDE.md's "standing conditions dedup by state-transition... never every tick" rule. This inflates
  on-call noise for the ENTIRE duration of any monitoring-cron outage, not just this one.

## What is NOT claimed

- The exact hanging call/line inside `sweep()` was not captured with a stack trace or profiler -- the untimed-read
  hypothesis is circumstantial (strong timing correlation + matching failure class + matching log shape), not directly
  observed.
- Whether `DP_VM_GONE_NO_CAPTURE` (the other repeatedly-firing alert flagged in the task brief) shares the exact same
  "no RenagTracker" gap was not checked -- it is emitted from `exit_code_fleet_monitor.py`, a different detector module
  than `meta_watchers.py`, so its dedup path (if any) is a separate code read not performed here.
- Whether the `repository_dispatch HTTP 422` warning (present in every sampled recent execution, logged as "best-effort"
  and non-fatal) is a pre-existing, unrelated, already-tolerated condition or a NEW regression was not determined --
  flagged as a real but distinct finding, not chased further (it does not block or explain the hang itself, since the
  sweep continues past it and logs the next VM's verdict).
- Whether the hang is deterministic on this ONE VM's fleet state (i.e., would clear on its own once
  `canonical-migration-cefi-content-20260719-121302` is cleaned up / no longer `preempted`-adjacent in the fleet) or is
  a general defect that will resurface on the next preempted VM was not tested -- would require either a local repro
  against a mocked slow storage client, or (post-fix) observing whether the job recovers once the wedged VM is resolved.

## Recommended action (NOT executed -- this investigation was read-only per its own scope)

1. **Do not manually trigger a catch-up run yet** (`gcloud run jobs execute` / `gcloud scheduler jobs run`) -- given
   every one of the last ~997 ticks has hung identically, a manual trigger would almost certainly hang too (5 more
   minutes with zero observability gain) and burns another timeout cycle. It only becomes a useful/safe next step AFTER
   either (a) the untimed-read hypothesis is confirmed and a timeout/bound is added to `_gcs.read_text()` (or its
   callers), or (b) the specific wedged VM state that triggers the hang is identified and cleared.
2. **Add a bounded timeout** to `_gcs.read_text()` in `deployment_service/data_pipeline_monitors/_gcs.py` (used by
   `read_launch_params`, `read_progress_checkpoint`, and other callers in this file) -- either pass an explicit timeout
   through to `storage_client.blob_exists`/`download_bytes` if the UTL `StorageClient` interface supports one, or wrap
   the call in the same bounded-polling pattern already shipped for the analogous MTDS fix
   (`concurrent.futures.wait(..., timeout=..., return_when=FIRST_COMPLETED)` -- abandon-and-log rather than block). This
   is the highest-leverage fix: it turns "one stuck VM's read hangs the entire 5-minute sweep and produces ZERO signal
   for every other VM" into "one stuck VM's read fails fast, gets logged/skipped, and the sweep finishes."
3. **Wire `RenagTracker` into `check_cron_fired`** (`meta_watchers.py`), mirroring exactly how it is already wired into
   `check_high_attempted_failed` -- same `DEFAULT_RENAG_COOLDOWN_SECONDS` (1800s / 30 min) unless a CRITICAL/page-tier
   alert warrants a shorter one (operator call). Low-risk, mechanical change; the pattern is already proven in the same
   file for a sibling detector.
4. **Once (2) ships and deploys**, confirm recovery by watching (not triggering) the next few naturally-scheduled `*/5`
   executions via `gcloud run jobs executions list` -- expect `1/1` complete and a fresh
   `vm-census/exit-code-last-run.json` sentinel, which should self-clear the `DP_CRON_DID_NOT_FIRE` condition (and, once
   (3) ships, produce a RESOLVED bookend per the alerting convention instead of just going quiet).
5. Cross-reference whoever is investigating the wedged `canonical-migration-cefi-content-20260719-121302` VM (parallel
   workstream per the task brief) -- if that VM's state changes (cleaned up / re-classified), re-check whether this
   job's hang clears on its own, which would be informative for confirming or ruling out this doc's root-cause
   hypothesis.

## Related

Same untimed-cloud-storage-read failure CLASS as `mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md`
(different repo/script/call-site, same shape: a `try/except`-wrapped or otherwise unguarded network read with no
timeout, hung inside a time-bounded execution context). Same missing-re-nag-cooldown CLASS as the now-archived
`dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` (`plans/archive/issues/`; same file, same
`MissTracker`-without-`RenagTracker` gap, different detector function within it). Same Cloud Run job as the OOM incident
in `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` (already fixed, ruled out as this incident's cause). Touches
the same source file as the now-archived 2026-07-21 verdict-classification fix
`exit_code_fleet_monitor_clean_misclassifies_premature_kill_2026_07_21.md` (`plans/archive/issues/`; that fix did not
address this hang).
