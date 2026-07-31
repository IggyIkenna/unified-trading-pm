---
doc_type: issue
title:
  DP_CONSOLIDATOR_SCHEDULER_PAUSED recurred for the tradfi cron — retroactive maintenance-window registered
  (2026-07-31), self-corrected a premature resume
summary: >-
  Escalation triage (escalation agt-a7b8b8, wall_type=data_pipeline_failure) for a CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-004) page on `uts-prod-manifest-consolidator-market-data-tradfi-cron`.
  Same failure class as the same-day sibling `dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md`: the
  cron is deliberately paused as part of `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s tracked
  pause/apply/resume backfill sequence (re-paused 2026-07-31T13:45:52Z by slot-16's dry-run session per that plan's own
  HARD constraint — pause before any apply attempt), whose apply+resume todos remain open. No maintenance window was
  registered for THIS specific pause (raw `gcloud`, not the sanctioned CLI), so DP-WATCHER-004 correctly paged.
  **Self-correction**: before finding the sibling plan context, I resumed the cron directly (a mistake — it silently
  races the plan's own pause/apply/resume protocol); caught it ~3 minutes later with zero consolidator ticks having
  fired in between (verified via the bucket's `_index/availability_index.parquet` `consolidator_run_at` custom field,
  unchanged across the window), so no data-correctness harm occurred. Re-paused the job and retroactively registered a
  maintenance window (mirroring the prediction fix) so the page stops recurring for the remainder of this backfill.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags:
  [
    data_pipeline_failure,
    dp-alerts,
    consolidator,
    maintenance-window,
    scheduler,
    false-positive-by-design,
    self-correction,
  ]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md,
    /plans/archive/issues/dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-31
parent_epic: manifest_master
assigned_vm: planning
locked_by:
priority: P2
source: >-
  data_pipeline_failure escalation agt-a7b8b8 (dp-fleet-monitor → slot-2), CONTEXT: "CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-004) — manifest-consolidator scheduler
  'uts-prod-manifest-consolidator-market-data-tradfi-cron' is PAUSED (not -legacy-)."
resolved_by: slot-12 (dp_consolidator_scheduler_paused_tradfi_recurrence-001, 2026-07-31)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-31
---

> **🗄️ ARCHIVED 2026-07-31** — `status: resolved`. Both todos done: the maintenance window was registered live
> 2026-07-31T18:25-18:26Z (TTL 4320min), and the pause-action retrofit shipped — market-tick-data-service@99b3c953
> (`scripts/mtds_available_at_backfill_pause_{tradfi,prediction}_2026_07_31.py`). The plan's own 1000-line hard-cap
> breach (finding "Recommended decision" § 2) that blocked authoring this todo directly inside
> `mtds_available_at_cross_asset_backfill_2026_07_13.md` is tracked forward at
> `/plans/active/issues/mtds_available_at_cross_asset_backfill_line_cap_remediation_2026_07_31.md`. The underlying
> tradfi-cron pause itself remains open, tracked separately in
> `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` (not this doc's scope). No further open work in
> this doc.

# DP_CONSOLIDATOR_SCHEDULER_PAUSED recurrence — tradfi cron (2026-07-31)

## What I found

1. **Live GCP state at escalation time**: `uts-prod-manifest-consolidator-market-data-tradfi-cron` (`asia-northeast1`) =
   `PAUSED`, `userUpdateTime: 2026-07-31T13:45:52Z`. No maintenance-window marker existed at
   `gs://market-data-tick-tradfi-prd-central-element-323112/_index/_maintenance_window.json` (404 on read).
2. **Cloud Audit Logs** (`protoPayload.resourceName` filter, 14d window) showed a `PauseJob` by
   `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` at exactly `2026-07-31T13:45:52Z` with no
   matching `ResumeJob` since — plus a history of many prior short pause/resume cycles back to 2026-07-27, all by the
   same principal or `ikenna@odum-research.com`, none via the sanctioned maintenance-window CLI.
3. **Mistake (self-corrected)**: at this point I had not yet found the owning plan. Reasoning from the DP-WATCHER-004
   definition alone ("accidental pause, no maintenance window") plus no currently-running VM correlating to the
   13:45:52Z timestamp, I resumed the cron directly (`gcloud scheduler jobs resume`, `18:22:28Z`) to restore manifest
   freshness — the correct remedy for a _genuinely_ accidental pause, but wrong here.
4. **Found the real owner before any harm landed**: `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`
   Progress Log entry **"#7 — 2026-07-31 (slot 16)"** — same day, hours earlier — records: "Verified cron still `PAUSED`
   live... Launched a full-range dry-run as a final safety check before the live write and found a real unbounded-memory
   risk (killed before it could OOM the shared host)... Did NOT proceed to the real apply this session. Cron still
   `PAUSED`... nothing written to production." That dry-run session's defensive re-pause call (idempotent no-op on an
   already-paused job, but still a real `PauseJob` API call — explaining the 13:45:52Z audit entry) is the actual cause.
   The plan's own todos "Apply `rebuild_tradfi_manifest.py`..." and "Resume the tradfi consolidator cron..." are both
   still open (`- [ ]`) as of this writing — the pause is intentional and ongoing, not accidental. This exactly mirrors
   the sibling `dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md` finding for the prediction cron,
   filed by a different slot earlier the same day.
5. **Verified zero harm from the premature resume**: polled the bucket's consolidated index object
   (`_index/availability_index.parquet`) custom field `consolidator_run_at` every 20s for ~2 minutes after the resume —
   it stayed pinned at `2026-07-31T14:07:05.128914+00:00` (the last real run, from before the 13:45:52Z pause) the
   entire time I held the job `ENABLED`, so the `*/1 * * * *` schedule never actually fired a consolidator tick in the
   ~3-minute window before I re-paused. No incremental merge raced anything; the plan's snapshot/pause invariant was
   never actually violated in practice, only in scheduler _state_ for a few minutes.
6. **Corrected live**: re-paused the job (`18:25:11Z`, confirmed `PAUSED`), then registered a maintenance window via the
   sanctioned CLI (`deployment_service.data_pipeline_monitors.scheduler_maintenance`),
   `--locked-by mtds_available_at_cross_asset_backfill_2026_07_13` — the exact string
   `market-tick-data-service/scripts/mtds_available_at_backfill_resume_tradfi_2026_07_30.py` already uses for its own
   `locked_by=`, so that plan's existing ready-made resume script will release this window cleanly (no `--force`) once
   its apply+resume todos actually complete. TTL 4320min (3 days), matching the sibling prediction fix's reasoning: long
   enough to plausibly cover the remaining P1 dispatch without permanently blinding the watcher; an expiry before the
   plan lands would correctly re-page, not silently suppress forever.

## Why it matters

Same false-positive-by-current-design class as the prediction sibling: DP-WATCHER-004 cannot distinguish a plan-tracked,
protocol-following pause from a genuinely accidental one when the pause was made via raw `gcloud` instead of the
sanctioned `scheduler_maintenance` CLI — by design, since an unregistered pause must fail toward paging (the watcher's
whole reason to exist). The **real** finding worth surfacing to the operator is process, not code: this plan's
pause/apply/resume protocol has now generated **three** escalation-worker sessions in three days (2026-07-29
tradfi+prediction, 2026-07-31 prediction, 2026-07-31 tradfi — this doc) purely because the plan's own scripts pause via
raw `gcloud` instead of always going through `scheduler_maintenance.pause_for_maintenance()`. The already-filed P3
follow-up (extend the liveness watchdog to bounded auto-resume, in the archived 2026-07-29 issue) does not fix this —
it's a different gap (watchdog auto-resume vs. pause-time registration). A cleaner fix would be: the plan's OWN pause
action (not just its resume script) should call `pause_for_maintenance()` from the start, so no retroactive registration
is ever needed. Not fixing that here (out of this one-shot escalation's scope, and the plan file is already at 1003
lines — over its 1000-line hard cap — so it cannot absorb a new todo without an archival/split pass first, itself out of
scope for a data-pipeline-failure escalation).

## Recommended decision

No further paging-remediation action needed — resolved for the remainder of the realistic backfill window (until
2026-08-03T18:26Z or until the plan's resume script releases it, whichever first). Two follow-ups worth tracking (not
fixed here, per scope):

1. Retrofit `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own pause action to call
   `scheduler_maintenance.pause_for_maintenance()` instead of raw `gcloud`, closing the registration gap at the source
   instead of needing a reactive retroactive-registration escalation each time. Blocked on the plan itself being over
   its line cap — needs an archival/split pass first.
2. The plan's own line-cap breach (1003/1000) should be resolved (archive completed lanes — prediction's todos all read
   `[x]` in the file except the still-open apply/resume pair also blocked on the same protocol; tradfi is likewise all
   done except apply/resume) by whoever next works this plan, so future Progress Log entries have room.

## Todos

- [x] ✅ [OPS] P1. **Re-paused the tradfi cron + retroactively registered its maintenance window — DONE live
      2026-07-31T18:25-18:26Z.** No code shipped; pure infra actions (`gcloud scheduler jobs pause` + the sanctioned
      `scheduler_maintenance` CLI CAS write). Verified: `gcloud scheduler jobs describe` reads `PAUSED`;
      `scheduler_maintenance ... status` reads `HELD by 'mtds_available_at_cross_asset_backfill_2026_07_13'` until
      `2026-08-03T18:26:16Z`. Confirmed zero consolidator ticks fired during the ~3min the job was briefly `ENABLED`
      (see finding 5 above). (repo: NA)
- [x] ✅ [CODE] P3. Retrofit `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s pause action(s) (currently raw
      `gcloud scheduler jobs pause`, both tradfi and prediction lanes) to call
      `scheduler_maintenance.pause_for_maintenance()` at pause time instead of only at resume time — closes the
      registration gap at the source — market-tick-data-service@99b3c953. Shipped
      `scripts/mtds_available_at_backfill_pause_{tradfi,prediction}_2026_07_31.py`, calling the already-tested
      `_scheduler_pause_resume_2026_07_30.pause_via_maintenance_window()` local composition (same primitive the existing
      `resume_{tradfi,prediction}_2026_07_30.py` scripts already release), mirroring their structure exactly. Did NOT
      touch `mtds_available_at_cross_asset_backfill_2026_07_13.md` itself — the checkbox flip for this todo lives
      entirely in this issue doc, so the plan's own 1000-line hard cap (1003/1000, still unresolved) never gated this
      change; `check_line_caps.sh`'s scoped (staged-files) mode only enforces the cap on files the commit actually
      touches. Full `quality-gates.sh` green on market-tick-data-service (9779 passed), shipped via quickmerge, verified
      on `origin/live-defi-rollout`. (repo: market-tick-data-service)
