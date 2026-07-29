---
doc_type: issue
title: TradFi + prediction manifest-consolidator Cloud Scheduler crons stuck PAUSED ~20h (fixed live)
summary:
  "Both `uts-prod-manifest-consolidator-market-data-tradfi-cron` and
  `uts-prod-manifest-consolidator-market-data-prediction-cron` were stuck in PAUSED state for ~20 hours (since
  2026-07-29T01:05Z), causing the consolidated `_index/availability_index.parquet` for both buckets to go stale and the
  `uts-prod-consolidator-liveness-watchdog` to flag both DOWN every 2-minute cycle. Discovered mid-flight while running
  the FRED macro backfill (macro_micro_econ_data_capture_audit-003) — the smoke-test VM was losing 2/7 days per chunk to
  `ManifestConsolidatorStaleError`. Fixed live: resumed both crons; the TradFi catch-up merge processed 130 shards /
  6.2M rows in 6m31s, confirming a genuine backlog, not a false alarm."
status: open
nature: issue
asset_group: [tradfi, prediction]
stage: [data]
repos: [deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, manifest, consolidator, incident, cron, tradfi, prediction]
related: [macro_micro_econ_data_capture_audit_2026_06_05]
created: 2026-07-29
parent_epic: infrastructure_master
priority: P1
source:
  [
    "Discovered live 2026-07-29 while running macro_micro_econ_data_capture_audit-003 (FRED backfill) — smoke VM
    tradfi-bf-fred-2024-20260729-204729's run.log showed repeated ManifestConsolidatorStaleError",
    "gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-tradfi-cron (state=PAUSED)",
    "gcloud logging read (Cloud Audit Logs) for PauseJob/ResumeJob on both cron jobs, 60d window",
    "uts-prod-consolidator-liveness-watchdog Cloud Run Job execution logs (fires every 2 min)",
  ]
assigned_vm: planning
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-29
---

# TradFi + prediction manifest-consolidator crons stuck PAUSED (2026-07-29)

## What I found

While running the FRED macro backfill smoke test (`macro_micro_econ_data_capture_audit-003`), the launched VM's
`run.log` showed repeated `ManifestConsolidatorStaleError` failures — 2 of every 7 payloads in each date-chunk were
failing outright because `unified_trading_library.manifest_writer._state.assert_consolidator_healthy()` refuses to
proceed when the consolidated `_index/availability_index.parquet` heartbeat is older than the 120s freshness budget
while per-VM shards exist (a deliberate fail-loud guard — it will not silently fall back to a per-VM merge that can OOM
on a large bucket).

Investigation:

- `gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-tradfi-cron` showed `state: PAUSED`, while
  sibling crons (`…-features-tradfi-cron`, `…-instruments-tradfi-cron`) were `ENABLED`.
- Cloud Audit Logs (`google.cloud.scheduler.v1.CloudScheduler.PauseJob` / `…ResumeJob`) for this job over the prior 60
  days show a routine, short-duration pause/resume cadence (typically minutes to ~1h, performed by
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`) — e.g. paused 2026-07-27T21:00:17Z → resumed
  21:36:10Z; paused 2026-07-27T23:15:45Z → resumed 23:45:03Z; paused 2026-07-28T05:05:00Z → resumed 05:06:03Z. The
  **last** pause before the stuck state (2026-07-29T01:05:06Z, by `unified-trading-sa`) had **no matching resume** for
  ~20 hours — a clear outlier vs. the routine pattern. The preceding resume (2026-07-28T18:55:18Z) was by a human
  (`ikenna@odum-research.com`), then the automated pause/resume cadence appears to have broken down after the very next
  automated pause.
- `uts-prod-manifest-consolidator-market-data-prediction-cron` showed the identical symptom (`state: PAUSED`) and was
  independently flagged DOWN by the same watchdog run.
- `uts-prod-consolidator-liveness-watchdog` (Cloud Run Job, fires every 2 min) was actively detecting both buckets as
  `down` on every cycle (confirmed via its own execution logs, e.g. execution
  `uts-prod-consolidator-liveness-watchdog-2q2hr` at 2026-07-29T20:54:41Z:
  `2 bucket(s) DOWN: market-data-tick-pred-prd-…, market-data-tick-tradfi-prd-…`) but had no observed auto-recovery
  action — it appears to be detection/alerting-only, not self-healing.

## Why it matters

- **Data-correctness impact (live, not hypothetical):** every TradFi backfill VM running during the ~20h window (not
  just the FRED smoke test) was losing whichever dates' preflight/manifest lookups landed on the stale-consolidator
  guard — those payloads raised `ManifestConsolidatorStaleError` and were dropped from that run (shard-level failure
  isolation kept the rest of the chunk loop going, but those specific dates got zero capture attempt in that pass). They
  should self-heal on any subsequent run against the same date range since MTDS always retries `ATTEMPTED_FAILED`
  sentinels regardless of `--force` — but this is genuine, if self-correcting, corruption of a live production
  data-pipeline run.
- **Not a one-bucket fluke:** the prediction-market bucket hit the exact same symptom independently, and the pattern
  (routine short auto-pause/resume elsewhere, but this specific pause never auto-resumed) suggests a shared root cause
  upstream of either individual bucket (e.g. whatever process/Cloud Function performs the routine auto-resume itself
  failed or was itself down during this window).
- **Root cause NOT fully diagnosed.** I did not find what process performs the routine auto-resume (it isn't the
  liveness watchdog — that job is read-only/detection per its own logs), nor why it stopped firing after
  2026-07-29T01:05Z. This needs a deeper look at whatever scheduled process/Cloud Function is responsible for the
  `unified-trading-sa` pause/resume cadence seen in the audit log (possibly a maintenance-window drain/undrain
  coordinator).

## Recommended decision

Fixed live (see Todos) by resuming both crons — this restores correctness for ongoing/future runs. The remaining open
question is root-causing why the routine auto-resume mechanism stopped firing, and whether the
`uts-prod-consolidator-liveness-watchdog` should be extended from detect-only to auto-resume-on-stuck-pause (bounded,
e.g. only after N consecutive DOWN cycles, mirroring the auto-park/auto-recovery patterns used elsewhere in this
codebase).

## Todos

- [x] ✅ [OPS] P1. **Resume both stuck crons — DONE live 2026-07-29T20:55Z**, confirmed via
      `gcloud scheduler jobs describe … --format="yaml(state)"` (both now `ENABLED`) and the next
      `uts-prod-consolidator-liveness-watchdog` cycle (2026-07-29T21:02:48Z) reporting both
      `market-data-tick-tradfi-prd-…` and `market-data-tick-pred-prd-…` as `ok`. TradFi catch-up merge (execution
      `uts-prod-manifest-consolidator-market-data-tradfi-htmq6`) processed 130 shards / 6,208,190 rows_in → 5,870,199
      rows_out (337,991 deduped) in 6m30.85s, confirming a real ~20h backlog, not a false-positive staleness read.
- [ ] [INFRA] P2. **Root-cause why the routine `unified-trading-sa` auto-pause/resume cadence for these two crons
      stopped firing after 2026-07-29T01:05Z.** Identify the scheduled process/Cloud Function/Cloud Scheduler job that
      performs the routine short pause→resume cycle seen in the 60-day audit log (search `deployment-service/` +
      `agent-orchestrator/` for a maintenance-window / drain-undrain coordinator that calls
      `scheduler_jobs.pause`/`resume` on `manifest-consolidator-market-data-*-cron` jobs). Confirm whether it failed
      silently (needs its own alerting) or was itself paused/killed. Repo: deployment-service (watchdog source confirmed
      at `deployment-service/deployment_service/data_pipeline_monitors/` +
      `deployment-service/terraform/gcp/consolidator_liveness_scheduler.tf` — the pause/resume coordinator itself was
      NOT found in this pass, search from there).
- [ ] [INFRA] P3. **Extend `uts-prod-consolidator-liveness-watchdog` from detect-only to bounded auto-resume** — after N
      consecutive DOWN cycles (e.g. 5, ~10 min) for a bucket whose Scheduler job state is `PAUSED` (not genuinely
      mid-migration-drain), auto-`ResumeJob` it and emit an actionable alert, mirroring the auto-park/auto-recovery
      pattern already used elsewhere (e.g. `agent-orchestrator/server/auto_park.py`). Must NOT auto-resume a
      deliberately-paused job during a genuine drain window — needs a way to distinguish "stuck" from "intentionally
      paused for migration" (e.g. a companion drain-marker object, or simply bounding to the routine-cadence duration
      observed in this doc's audit-log evidence, ~1h max). Repo: deployment-service
      (`deployment-service/deployment_service/data_pipeline_monitors/deadman_poster.py` + `meta_targets.py` are the
      confirmed entry points for this watchdog).
