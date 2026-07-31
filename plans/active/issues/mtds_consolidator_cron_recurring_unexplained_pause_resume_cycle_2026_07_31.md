---
doc_type: issue
title:
  "prediction + tradfi manifest-consolidator crons found live ENABLED in production despite this plan's tracked pause
  state — a pre-existing, unexplained ~daily pause/resume cycle (source unknown) keeps silently undoing deliberate
  maintenance pauses, including this plan's own"
summary: >-
  While preparing to execute `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s -001 (prediction apply) todo,
  found `uts-prod-manifest-consolidator-market-data-prediction-cron` AND
  `uts-prod-manifest-consolidator-market-data-tradfi-cron` both live `ENABLED` (actively firing every ~60s per Cloud
  Scheduler execution logs) even though this plan's own Progress Log states both were paused 2026-07-29 and neither
  cron's downstream apply/resume todos have executed. Cloud Audit Log shows the prediction cron was resumed
  2026-07-31T12:38:43Z by `unified-trading-sa` — but the `_maintenance_window.json` registration this plan's own
  retrofit relies on was NEVER released (still shows the original 04:56:45Z `acquired_at`), meaning whatever resumed it
  did NOT go through `resume_via_maintenance_window()` (that call releases the window as its last step). Pulling the
  FULL 7-day pause/resume history for the tradfi cron reveals this is not a one-off: a recurring PauseJob-then-ResumeJob
  cycle (interval ranging from ~6 seconds to ~20 hours, principal usually `unified-trading-sa`, occasionally
  `ikenna@odum-research.com`) has been happening roughly once a day since at least 2026-07-27 — PREDATING this plan's
  own 2026-07-29 backfill pause and continuing to fire independently of it, which explains why the tradfi cron was back
  to resumed by 2026-07-29T20:55:40Z (under 20 hours after this plan's own deliberate pause). Re-paused both crons as a
  protective action (raw `gcloud scheduler jobs pause`, verified `PAUSED`) before proceeding with this session's
  backfill apply work — root cause of the recurring cycle NOT investigated (outside data_engineering craft; smells like
  a CI/CD deploy or Terraform-apply side effect on the scheduler resource, needs backend_engineer/infra craft).
status: open
nature: issue
asset_group: [tradfi, prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-correctness, scheduler, consolidator, maintenance-window, cron, ci-cd, infra, production-safety]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/archive/issues/dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md,
  ]
created: "2026-07-31"
parent_epic: manifest_master
source: [mtds_available_at_cross_asset_backfill-006, slot 12]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.72
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# Prediction + tradfi consolidator crons found live despite plan's tracked pause state

## What I found

1. `gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-prediction-cron --location asia-northeast1`
   (under `unified-trading-sa`) returned `ENABLED`. Cloud Scheduler execution logs (`freshness=1h`) showed real
   `AttemptStarted`/`AttemptFinished` (HTTP 200) entries firing every ~60s, i.e. genuinely live, not a stale state
   cache.
2. `gcloud storage cat gs://market-data-tick-pred-prd-central-element-323112/_index/_maintenance_window.json` still
   showed the ORIGINAL registration: `acquired_at: 2026-07-31T04:56:45Z`,
   `locked_by: mtds_available_at_cross_asset_backfill_2026_07_13`, `expires_at: 2026-08-03T04:56:45Z` — i.e. the window
   object was never deleted/released.
3. Cloud Audit Log (`cloudaudit.googleapis.com/activity`, `protoPayload.serviceName="cloudscheduler.googleapis.com"`)
   for the prediction cron's `resourceName`:
   - `2026-07-31T04:56:46Z` `PauseJob` (unified-trading-sa) — matches the window's `acquired_at`.
   - `2026-07-31T12:38:43Z` `ResumeJob` (unified-trading-sa) — **this is what actually un-paused it**, ~67 minutes
     before I found it live at 13:41. `resume_via_maintenance_window()` (the plan's own retrofit script,
     `market-tick-data-service@5ca75583`) calls `resume_job` THEN `release_maintenance_window()` as its last step — the
     window's continued presence proves this call path was NOT what fired (or the release step failed silently after the
     resume succeeded); root cause not determined.
4. Checked the TRADFI cron's full 7-day pause/resume history (same audit log, filtered to its own `resourceName`) — this
   is the significant part: a recurring `PauseJob` → `ResumeJob` cycle, principal almost always `unified-trading-sa`
   (occasionally `ikenna@odum-research.com`), interval ranging from ~6 SECONDS to ~20 HOURS, occurring roughly once a
   day going back to at least `2026-07-27T23:15Z` — well before this plan's own 2026-07-29 backfill pause. This explains
   why the tradfi cron, deliberately paused by this plan at `2026-07-29T01:05:06Z`, was already back to `ResumeJob` by
   `2026-07-29T20:55:40Z` (under 20h later) — NOT this plan's own resume todo (still unexecuted/`queued` in the
   backlog), but this SAME pre-existing recurring cycle.
5. Re-paused both crons as an immediate protective action (`gcloud scheduler jobs pause`, both `unified-trading-sa`),
   verified `PAUSED` via `describe` immediately after. Given the discovered recurring cycle, THIS pause is also not
   guaranteed durable — flagging for whoever next touches this plan's tradfi/prediction lanes to re-verify `PAUSED`
   immediately before any apply/write step, not just trust an earlier "paused" Progress Log entry.

## Why it matters

This plan's entire safety model (pause → snapshot → apply → verify → resume) assumes the pause HOLDS for the duration of
the apply window — the sports CF-8 regression this plan is explicitly designed around was caused by exactly a
cron-vs-rebuild-write collision. If some other, unidentified mechanism silently un-pauses these crons on a roughly-daily
cadence regardless of who paused them or why, then:

- Any apply run assumed to be running against a genuinely-paused cron may actually race a live consolidator cycle,
  reintroducing the sports CF-8 failure mode without anyone noticing (the plan's Progress Log would still say "cron
  PAUSED" based on a check done BEFORE the apply, not continuously through it).
- The `_maintenance_window.json` CAS registration this plan's DP-WATCHER-003 retrofit relies on to suppress false-
  positive pages is NOT actually reflecting ground truth reliably — a live cron with a stale "still paused" window
  object is worse than no window at all, since it looks authoritative.
- This is NOT scoped to this one plan — whatever causes the cycle likely affects every consolidator cron the same way, a
  fleet-wide latent risk for any future backfill-style pause/apply/resume workflow.

## What I did NOT do

Did not root-cause the recurring cycle's actual source — candidate hypotheses (untested): (a) a CI/CD deploy pipeline
step that recreates/updates the Cloud Scheduler job resource (Terraform `google_cloud_scheduler_job` or an equivalent
apply) as a side effect of an unrelated `market-tick-data-service`/`deployment-service` deploy, consistent with the
`CreateJob`/`UpdateJob` audit entries seen around `2026-07-30T06:44Z`; (b) some other standing automation (health-check
self-heal, a liveness watchdog like `uts-prod-consolidator-liveness-watchdog-fast-cron`/`-slow-cron` seen in the full
job listing, possibly "fixing" a paused state it doesn't distinguish from accidental); (c) a scheduled maintenance
routine unrelated to this plan entirely. This needs `backend_engineer`/`infra` craft (CI/CD + Terraform/infra
investigation), out of `data_engineering` scope. Did not attempt to fix or disable whatever is causing it. Did not touch
any manifest data — this touch was scheduler-state investigation + a protective re-pause only.

## Recommended decision

- [ ] [INFRA] P1. Root-cause the recurring PauseJob→ResumeJob cycle on the manifest-consolidator crons (start with
      `uts-prod-manifest-consolidator-market-data-tradfi-cron`'s 7-day audit history above as the reproduction case).
      Check whether a CI/CD deploy step or Terraform apply for `market-tick-data-service`/`deployment-service`
      recreates/updates the scheduler job resource as a side effect (candidate hypothesis (a) above), and whether
      `uts-prod-consolidator-liveness-watchdog-fast-cron`/`-slow-cron` has any code path that resumes a paused
      consolidator scheduler job it doesn't distinguish from an accidental pause (candidate (b)). Repo:
      deployment-service (or wherever the Terraform/CI config for these scheduler jobs lives — confirm during
      investigation). Done when: the actual trigger is identified with audit-log correlation (a deploy/build id, a
      watchdog code path, etc.) and either fixed (stop resuming a job under an active, unexpired maintenance window) or
      the mechanism is confirmed benign/intentional and documented.
- [ ] [DATA] P2. Once the root cause above is known, re-verify `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s
      prediction+tradfi lanes: confirm the crons are still genuinely paused immediately before any future apply step
      (not relying on an earlier Progress Log entry), and if the recurring cycle DID race a live consolidator cycle
      against any past apply/write in that plan, re-verify the resulting manifest data for a sports-CF8-shaped
      regression (a fill-rate/row-count check against the pre-apply snapshot). Repo: market-tick-data-service.

## Progress Log

- 2026-07-31 (data_engineering slot-12): found while gathering the -001 apply's before-state; killed the memory-heavy
  audit script (separate finding, see `available_at_fill_rate_audit_script_unbounded_memory_2026_07_31.md`), then
  investigating the manifest read's "waiting on a live consolidator lock" warning surfaced the live-ENABLED state.
  Traced via Cloud Audit Log, re-paused both crons protectively, filed this doc. `assigned_vm: NA` — the root-cause todo
  needs backend_engineer/infra investigation judgment, not a mechanically-bounded fix; the P2 re-verify todo is gated on
  that investigation's output.
