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
- [x] ✅ [INFRA] P2. **Root-caused 2026-07-30 (autonomous session) — NOT a broken automation.** The premise ("routine
      auto-pause/resume cadence stopped firing") is wrong: there is no standing scheduled Cloud Function/coordinator
      performing a routine pause→resume cycle at all (none found under `deployment-service/` or `agent-orchestrator/`
      calling `scheduler_jobs.pause`/`resume` on `manifest-consolidator-market-data-*-cron` on any cadence) — every
      pause/resume in the 60-day audit log is a ONE-OFF, agent/backfill-driven `gcloud scheduler jobs pause/resume`
      call, and the "routine short cadence" this doc observed is just many DIFFERENT short-lived backfill plans each
      pausing-then-quickly-resuming their own run, not one recurring job. The actual root cause for THIS specific
      2026-07-29T01:05Z pause is documented in an already-resolved sibling issue,
      `/plans/archive/issues/dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md`: both
      `uts-prod-manifest-consolidator-market-data-prediction-cron` and `…-tradfi-cron` were deliberately paused that day
      by `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own tracked pause→apply→resume backfill
      sequence — the resume half was INTENTIONALLY deferred pending that plan's apply step (still open as of this
      writing: `mtds_available_at_cross_asset_backfill-006`/`-009`), not a failure. The ~20h "stuck" duration this doc
      measured was simply how long that plan's apply step took to get scheduled, not evidence of a broken mechanism.
      **Was it caught silently with no alerting?** No — it WAS correctly, loudly detected: DP-WATCHER-003
      (`consolidator_scheduler_watcher.py`) pages CRITICAL for exactly this case by design (confirmed in the same
      archived doc), and the `uts-prod-consolidator-liveness-watchdog` this doc's own investigation found flagging both
      buckets DOWN was working as intended too — the gap the archived doc identified (and already fixed,
      `deployment-service@3a1cf3a`) was that DP-WATCHER-003 had no way to tell a SANCTIONED pause from an accidental
      one, so it paged CRITICAL even for deliberate, plan-tracked pauses — now resolved via a
      `scheduler_maintenance.maintenance_status()` check that downgrades to INFO when a live maintenance window covers
      the paused job. No further root-cause work needed; this todo's original "find the broken coordinator" framing
      doesn't describe reality.
- [ ] [INFRA] P3. **Extend `uts-prod-consolidator-liveness-watchdog` from detect-only to bounded auto-resume** — after N
      consecutive DOWN cycles (e.g. 5, ~10 min) for a bucket whose Scheduler job state is `PAUSED` (not genuinely
      mid-migration-drain), auto-`ResumeJob` it and emit an actionable alert, mirroring the auto-park/auto-recovery
      pattern already used elsewhere (e.g. `agent-orchestrator/server/auto_park.py`). **2026-07-30 update: the "how to
      distinguish stuck from intentionally paused" blocker this todo originally flagged is now SOLVED** — the sibling
      DP-WATCHER-003 fix (`deployment-service@3a1cf3a`, see the P2 todo above) already wired exactly this distinction
      via `deployment-service`'s `scheduler_maintenance.maintenance_status()` (a live, CAS-backed maintenance-window
      primitive); this todo's own auto-resume logic could check the identical primitive before acting. **Not implemented
      in this pass**: the watchdog's actual runtime logic is `unified_trading_library.monitors.consolidator_liveness`
      (confirmed via `deployment-service/terraform/gcp/consolidator_liveness_scheduler.tf`'s own docstring — the Cloud
      Run Job image is `market-tick-data-service:latest` purely because UTL ships bundled as its dependency, but the
      watchdog CODE lives in `unified-trading-library`, NOT
      `deployment-service`/`deployment_service/data_pipeline_monitors/` as this todo's own citation assumed —
      `deadman_poster.py`/`meta_targets.py` are a DIFFERENT deadman-staleness monitor, not this watchdog). Implementing
      the auto-resume behavior means editing UTL — a shared T0 dependency every service imports — to make it actively
      mutate live production Cloud Scheduler state, which is a real, fleet-wide-blast-radius design decision (per
      `AUTONOMOUS_AGENT_RULES.md` rule 11) outside a same-session mechanical port; also outside this dispatch's assigned
      repo scope (market-tick-data-service / deployment-service / deployment-api only). Recommend as its own follow-up
      AO todo targeting `unified-trading-library`, now unblocked by the maintenance-window primitive above.
