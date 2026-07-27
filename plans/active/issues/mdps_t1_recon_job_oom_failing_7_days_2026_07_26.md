---
doc_type: issue
title: MDPS t1-recon Cloud Run job OOMs every day — 7 consecutive failures, unrelated to reader-bridge deploy
summary: >-
  `uts-prod-market-data-processing-service-t1-recon` (GCP Cloud Run job, asia-northeast1) has failed EVERY scheduled
  execution for the past 7 days (2026-07-20 through 2026-07-26), each time with "The configured memory limit was
  reached" despite an already-generous 32Gi container limit. Discovered incidentally while triggering the job to verify
  the D3 reader-bridge deploy — the reader-bridge code is unrelated to this failure and is not implicated.
status: open
nature: issue
asset_group: [cefi, tradfi, defi, sports, prediction]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, oom, cloud-run-job, candle-derivation, production-incident]
related: [/plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Discovered 2026-07-26 while verifying the cefi reader-bridge Cloud Run job deploy (see
  cefi_satellite_ao_dispatch_batch2_2026_07_26.md / cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md)
resolved_by:
---

# MDPS t1-recon Cloud Run job — 7 consecutive daily OOM failures

## What I found

Triggered `uts-prod-market-data-processing-service-t1-recon` manually (execution
`uts-prod-market-data-processing-service-t1-recon-kv4br`) purely to confirm the D3 reader-bridge fix
(`market-data-processing-service@0035f79`, already on `origin/main`) runs correctly. The execution failed at
2026-07-26T14:35:19Z:

```
Task uts-prod-market-data-processing-service-t1-recon-kv4br-task0 failed with exit code: 0 and message:
The configured memory limit was reached.
```

Logs show the job successfully bootstrapped, validated cloud connectivity, and began "Processing candles for 2026-07-25"
across **all 5 asset groups** (`cefi, tradfi, defi, sports, prediction`) and a combined list of **~50 data_types** in
one process, before being OOM-killed ~22 minutes in.

**This is not a one-off.** `gcloud run jobs executions list` shows every execution for the past 7 days failed
(`status.conditions[type=Completed].status = False`):

| Execution                                              | Completion (UTC)     |
| ------------------------------------------------------ | -------------------- |
| uts-prod-market-data-processing-service-t1-recon-kv4br | 2026-07-26T14:35:19Z |
| uts-prod-market-data-processing-service-t1-recon-p9kqm | 2026-07-26T03:09:31Z |
| uts-prod-market-data-processing-service-t1-recon-9lxrk | 2026-07-25T01:19:03Z |
| uts-prod-market-data-processing-service-t1-recon-pl2dx | 2026-07-24T01:14:27Z |
| uts-prod-market-data-processing-service-t1-recon-fcgp9 | 2026-07-23T01:09:06Z |
| uts-prod-market-data-processing-service-t1-recon-ffndb | 2026-07-22T01:06:00Z |
| uts-prod-market-data-processing-service-t1-recon-gcq7k | 2026-07-21T01:05:50Z |

The job's container is already configured with a 32Gi memory limit
(`spec.template.spec.template.spec.containers[0] .resources.limits.memory`), so this is not a case of an
obviously-too-small default — either the per-run working set has grown past 32Gi (more instruments/data_types/history
than when this limit was set), or there is a memory leak / unbounded accumulation in the candle-derivation path for a
subset of these data_types. **Not investigated further here** — root-causing which asset_group/data_type combination is
actually driving the memory growth, and whether the fix is a memory bump, a workload split (per-asset-group executions
instead of one combined run), or a code-level leak fix, is a real engineering judgment call, not a bounded todo I can
resolve unattended.

## Why it matters

MDPS candle derivation for `t1-recon` has not completed successfully in at least 7 days across ALL FIVE asset groups —
this is the process that reconciles/backfills candles this job is meant to keep current. Silent for a week because the
failure produces `exit code: 0` (a clean-looking shutdown from the container platform's point of view) rather than a
loud crash — worth checking whether this job's failures are even reaching the standing CI/VM-billing-waste alerting
paths, since "exit code 0 but OOM-killed" is exactly the kind of ambiguous signal those monitors are built to catch.

## Recommended next step

Operator/engineer judgment call on the fix direction (memory bump vs. per-asset-group split vs. leak fix) — flagging
rather than resolving unilaterally, per this being a genuine design decision, not a scoped todo.

## Resolution update (2026-07-26, interactive session)

Root-caused (not just flagged) and fixed. `check_upstream_manifest_has_live_gap()` in
`market_data_processing_service/app/core/dependency_checker.py` read the upstream `availability_index.parquet` with
`columns=` pruning but **no date filter**. Confirmed via `RESOURCE_SAMPLE` log timing correlation (both RSS spikes —
15947MiB and 18706MiB — land entirely inside this one call's window, both times, deterministically) and via a direct
`pyarrow.parquet.ParquetFile` metadata check: the DEFI upstream index has grown to ~27.4M rows (~1.0GB compressed) vs
CEFI's 8.7M rows (~152MB) — an unfiltered decode of even a handful of pruned columns across every row still materializes
12-18GB of pandas/polars overhead. The sibling call `check_shard_freshness` (same function, called just before this one)
already applies `filters=[("date", "==", date)]` via UTL's row-group pushdown — this call site was simply the one left
unfiltered. Not a regression of the archived `mdps_filter_pushdown_memory_audit_and_fix_2026_05_28` plan's fix (that
covered scanner file-listing + per-day `gc.collect()`; this is a different, previously-uncovered call site).

**Fix shipped**: added `filters=[("date", "==", date)]` to match the established pushdown pattern, plus a regression
test asserting the kwarg is passed. QG green. `market-data-processing-service@6b44226` (landed on `live-defi-rollout`).

**Not yet verified against a real production run** — the fix needs to reach `main` (GCP Cloud Build only triggers on
push:main; it's currently only on `live-defi-rollout`, pending the normal ~15-60min auto-promotion) and a fresh image
built before `uts-prod-market-data-processing-service-t1-recon` can be re-triggered to prove the OOM is actually gone,
not just theoretically fixed. That's the one remaining step — see Todos.

## Update 3 (2026-07-26/27, interactive session) — original fix CONFIRMED, but job still fails via a SECOND, distinct OOM

`market-data-processing-service@6b44226` promoted to `main` (verified: git content-diff, not SHA-ancestor — LDR→main
promotion squashes/rewrites, so `git merge-base --is-ancestor` is unreliable here; the actual
`filters=[("date", "==", date)]` line was confirmed present in `git show origin/main:.../dependency_checker.py`). Fresh
Cloud Build `dbfbf45a-09ba-496b-8463-7d5102aaff0c` (tag `14617c1`, 2026-07-26T22:59:10Z) matches that content exactly.

Re-ran the job: execution `uts-prod-market-data-processing-service-t1-recon-7q78v`, confirmed via
`gcloud artifacts docker images list --include-tags` to have used image `sha256:4ab492d3...` tagged `14617c1` — the
correct, fix-containing image, not stale.

**The original bug IS fixed** — `RESOURCE_SAMPLE` trend for this execution shows rss peaking at ~6.3GB (23:15:43) then
resetting to <1GB (23:16:47, next asset_group/date_type boundary) and climbing again to ~3.5GB (23:21:51). This is
categorically different from the pre-fix pattern (a gradual, unbroken climb to 14.86 GiB from the single unfiltered
27.4M-row DEFI manifest read) — no evidence of that call site reappearing.

**But the job still failed** — `Completed=False`, "The configured memory limit was reached", at 2026-07-26T23:23:00Z,
this time at ~13 min elapsed (vs ~22 min pre-fix — earlier, not later). Container limit confirmed unchanged at 32Gi
(`gcloud run jobs describe ... resources.limits` = `memory=32Gi`). Logs show:

- Last RESOURCE_SAMPLE before death: 23:21:51, rss=3516MiB (13.6%) — nowhere near the limit.
- Last app log line: 23:21:29, finishing `POLARS AGGREGATED` candle work for DEFI `dex_pool_swaps`/2026-07-25 (704
  files, 0 skipped, just-listed from `market-data-tick-defi-prd-central-element-323112`).
- **Zero log lines of any kind between 23:21:51 and the `WARNING Container terminated on signal 9` at 23:22:58** — a
  67-89s gap where >28GB was allocated with no intermediate log output at all (confirmed via direct
  `gcloud logging read` on the execution, not the truncated default 2000-line pull which only covered the first 34s of
  the run).

**A genuinely different, not-yet-root-caused bug** — this is NOT a regression of the fix; it's a second OOM path, likely
specific to `defi`/`dex_pool_swaps`'s unusually high per-day file count (704 for one asset_group/data_type/date) or
whatever runs immediately after that data_type's `ThreadPoolExecutor` batch completes (the trailing
`MEMORY_HIGH_WATER_MARK` `log_event()` call, or the transition to the next data_type/asset_group). Ruled out during this
session: `ProcessingResult` (lightweight dataclass, no embedded DataFrames — not the accumulator);
`ManifestFreshnessCache._refresh_locked` / `check_shard_freshness` (already date-filtered per the 2026-07-14
`mtds_backfill_vm_startup_oom_rc137` fix, and called once per category/date, not per data_type, so not in the hot path
here).

**Also fixed in this session, unrelated**: the interactive-session watcher script used to monitor this execution had its
own bug — it parsed `gcloud run jobs executions describe` output via a Python `print(status, '|', msg)` call, which
inserts a space before the `|`; the bash `${var%%|*}` split then left a trailing space on the status value, so
`[ "$cond_status" = "False" ]` never matched and the watcher polled uselessly for the full 45-minute timeout instead of
exiting the moment the real terminal `Completed=False` appeared at the 12-minute mark. Caught by manually re-deriving
state from `gcloud run jobs executions describe` directly, not from the watcher's own output.

## Todos

- [ ] [SCRIPT] P1. **Root-cause and fix the second OOM path** (the silent >28GB spike after DEFI `dex_pool_swaps`
      finishes candle aggregation, described above). Suggested approach: instrument the code between the end of
      `_process_files_parallel`'s `ThreadPoolExecutor` block and the following data_type's first log line with
      additional `RESOURCE_SAMPLE`-style checkpoints (entry/exit of the `log_event("MEMORY_HIGH_WATER_MARK", ...)` call,
      entry into the next data_type's `_resolve_files_to_process`), ship, re-trigger the job, and correlate against a
      finer-grained log window than the default 2000-line `gcloud logging read` pull (query with an explicit
      `timestamp>=/<=` range instead). Once root-caused, apply the same date/column-pushdown discipline as the first fix
      if it's another unfiltered read, or a chunked/streaming write if it's a bulk accumulation. Re-run the job and
      confirm `status.conditions[type=Completed].status = True` with a bounded `RESOURCE_SAMPLE` trend end-to-end (not
      just up to the point this session's run reached) before flipping this todo. (repo: market-data-processing-service)
