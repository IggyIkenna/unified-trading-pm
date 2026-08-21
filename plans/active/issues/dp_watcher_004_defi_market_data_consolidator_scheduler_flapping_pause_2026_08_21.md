---
doc_type: issue
title: "DP-WATCHER-004: uts-prod-manifest-consolidator-market-data-defi-cron repeatedly paused/resumed by unified-trading-sa with no live maintenance window — resumed as immediate fix, root actuator not yet identified"
created: 2026-08-21
author: data_pipeline_failure (escalation agt-2b817b, slot 31)
parent_epic: observability_master
assigned_vm: planning
source:
  - DP-WATCHER-004
  - escalation agt-2b817b
locked_by:
summary: >-
  Cloud Scheduler job uts-prod-manifest-consolidator-market-data-defi-cron (asia-northeast1) fired
  DP-WATCHER-004 (CRITICAL, page) PAUSED-with-no-maintenance-window at 2026-08-21T15:39:11Z. Live
  investigation found this is NOT a one-time human pause: Cloud Audit Logs show
  unified-trading-sa@central-element-323112.iam.gserviceaccount.com toggling the SAME job
  PauseJob(14:25:50) -> ResumeJob(15:35:09/10) -> PauseJob(15:39:10/11) within the same ~75-minute
  window -- a flap pattern, not a single deliberate pause. scheduler_maintenance.maintenance_status()
  (the exact read-path DP-WATCHER-004 itself uses) confirmed NO live window on the owning bucket
  (market-data-tick-defi-prd-central-element-323112) at diagnosis time, and no VM matching the known
  canonical-migration-defi-rebuild pattern (or any other defi manifest-rewrite script) was running
  (full gcloud compute instances list checked). RESUMED the job as the immediate fix (data-pipeline
  correctness heartbeat) since no live window and no VM justify holding it paused. Root actuator of
  the repeated pause/resume toggling NOT yet identified -- deployment-service's
  RevocationActuator (FLEET_HALT) is correctly wired (consolidator_bucket_resolver passed at both
  call sites, escalation.py:663 + meta_watchers.py:211) and is the most likely mechanism (its
  pause/release cycle matches this shape exactly), but if it were firing for a defi-scoped alert it
  SHOULD have registered a maintenance window via _register_maintenance_windows() before pausing --
  and none was found live. Whether that means (a) the window write failed silently for this
  specific pause and the true driver IS FLEET_HALT re-triggering on a still-flapping defi CRITICAL
  alert, or (b) something else entirely (not RevocationActuator) is toggling this job, is the open
  question this issue exists to resolve.
status: open
nature: process
asset_group: [defi]
stage: [meta]
repos: [deployment-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-watcher-004, defi, manifest-consolidator, scheduler, fleet-halt, revocation]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md,
  ]
priority: P2
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py,
    deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py,
    deployment-service/deployment_service/data_pipeline_monitors/scheduler_maintenance.py,
  ]
---

# DP-WATCHER-004: defi market-data consolidator scheduler flapping pause, root actuator unconfirmed

## What I found

Escalation `agt-2b817b` (DP-WATCHER-004, wall_type=data_pipeline_failure) fired for
`uts-prod-manifest-consolidator-market-data-defi-cron` — no issue doc had been pre-filed (the alert
carried the details directly), so this doc is the first filing.

**Live evidence gathered:**

1. `gcloud scheduler jobs describe` confirmed `state: PAUSED`, `userUpdateTime:
   2026-08-21T15:39:11Z` at diagnosis time.
2. `scheduler_maintenance.maintenance_status("market-data-tick-defi-prd-central-element-323112")`
   (the SAME read path `check_consolidator_scheduler_paused`'s `maintenance_window_reader` uses)
   returned **no live window** — confirming this pause was correctly classified as unsanctioned by
   the watcher's own logic, not a reader bug.
3. `gcloud compute instances list` (full fleet, no filter) found no VM matching
   `canonical-migration-defi-rebuild-*` or any other name suggesting a manual defi manifest rewrite
   in progress — ruling out the exact precedent pattern from
   `/plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` (that
   incident's VM is long gone; current fleet has `instr-backfill-defi*`, `mdps-defi-2025-*`,
   `mdps-features-live-defi-*` running, none of which pause the consolidator per their own
   documented contract).
4. **Cloud Audit Logs** (`cloudaudit.googleapis.com/activity`,
   `protoPayload.resourceName:"uts-prod-manifest-consolidator-market-data-defi-cron"`, last 24h)
   show a flap, not a single pause:
   ```
   2026-08-21T14:25:50Z  unified-trading-sa@...  CloudScheduler.PauseJob
   2026-08-21T15:35:09Z  unified-trading-sa@...  CloudScheduler.ResumeJob
   2026-08-21T15:35:10Z  unified-trading-sa@...  CloudScheduler.ResumeJob
   2026-08-21T15:39:10Z  unified-trading-sa@...  CloudScheduler.PauseJob
   2026-08-21T15:39:11Z  unified-trading-sa@...  CloudScheduler.PauseJob
   ```
   The actor is the SERVICE ACCOUNT the runtime monitors/actuators use (`unified_trading_sa`), not
   a human operator identity — this points at an automated actuator, not a manual `gcloud` command.
5. The double Pause/double Resume (each pair ~1s apart) is itself notable — either two independent
   triggers fired within the same second, or one caller calls pause/resume twice per cycle.
6. `deployment-service`'s `RevocationActuator._pause_schedulers` (FLEET_HALT delivery for
   `DependentAction.FLEET_HALT`) is the only known mechanism in this codebase that pauses a
   consolidator scheduler programmatically outside a human `gcloud`/CLI call — see
   `revocation_actuator.py`. It is wired correctly at BOTH production call sites
   (`escalation.py:663`, `meta_watchers.py:211` both pass
   `consolidator_bucket_resolver=consolidator_job_to_bucket`), and per its own docstring it
   registers a maintenance window BEFORE pausing (`_register_maintenance_windows`, closing the
   2026-08-15 double-page gap) — so if FLEET_HALT were the driver, a live window should exist. None
   was found (point 2 above). This is either evidence FLEET_HALT is NOT the driver, or evidence the
   window write is failing silently for this specific bucket/target combination (the method
   swallows `MaintenanceWindowActiveError` and any other exception with only a `logger.warning`,
   so a failure here would not be visible without checking Cloud Logging for that warning
   specifically — NOT yet done in this session).
7. `vm-census/admission-hold/` (the FLEET_HALT hold-marker prefix) has 32 defi-related objects, but
   none inspected so far carry a timestamp matching the 15:39Z pause — the freshest-vs-stale split
   was not fully resolved this session (time-boxed by the one-shot escalation's liveness budget).

## Immediate action taken

Resumed the job (`gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron
--location=asia-northeast1`) at 2026-08-21T15:52:59Z — justified because (a) no live maintenance
window covers it, (b) no VM/backfill needs it paused, (c) per the "data pipeline correctness is the
heartbeat" HARD RULE, an unjustified pause is never left in place pending investigation. Armed a
5-minute background watch (`gcloud scheduler jobs describe` poll every 20s) to catch an immediate
re-pause, which would be strong evidence the driving condition is still live. See Progress Log for
the watch's outcome.

## Why root-cause is NOT closed by the resume alone

If an automated actuator (most likely FLEET_HALT, per point 6) is genuinely reacting to a still-
firing defi CRITICAL alert, resuming the scheduler only wins until the next actuation cycle — the
job will flap paused again. The real fix is identifying WHICH `alert_identity`/`target` is driving
this (if any) and root-causing THAT alert, not repeatedly resuming the scheduler. If the watch
below shows no re-pause, the flap may have been transient (the underlying alert self-cleared) —
still worth confirming what it was, since an unregistered FLEET_HALT-window bug (point 6) is itself
a real gap worth fixing even if this specific occurrence has now settled.

## Recommended decision

- [ ] [DATA] P1. Confirm whether the 5-minute post-resume watch (this session, Progress Log) caught
      a re-pause. If YES: this is an active FLEET_HALT (or equivalent) condition — find the exact
      `alert_identity` via Cloud Logging (`deployment-api` / `dp-alerting-subscriber` logs around
      the pause timestamps, grep for `revocation` / `FLEET_HALT` / `market-data-defi` / `defi`) and
      root-cause THAT alert per its own DP-* class in `/codex/05-infrastructure/data-pipeline-alerts.md`.
      If NO (stayed enabled 300s+): downgrade to P2, but still complete the two todos below — the
      missing-maintenance-window question is real regardless of whether this specific occurrence
      recurs.
- [ ] [CODE] P2. Determine why `scheduler_maintenance.maintenance_status()` found no live window
      for `market-data-tick-defi-prd-central-element-323112` at diagnosis time despite
      `RevocationActuator._register_maintenance_windows` being correctly wired for both production
      call sites. Check Cloud Logging for the `logger.warning` emitted on a
      `MaintenanceWindowActiveError`/generic-exception catch in `_register_maintenance_windows`
      around 14:25Z/15:39Z — either the window write is silently failing (a real bug to fix) or
      this pause genuinely wasn't FLEET_HALT-driven at all (in which case identify the actual
      caller — grep further callers of `make_scheduler_pauser()`/`CloudScheduler.PauseJob` beyond
      `revocation_actuator.py` and the human CLI path). Repo: deployment-service.
- [ ] [DATA] P3. Cross-check against `/plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`
      (filed earlier the same day, ~10:50 UTC) — that doc found the consolidator running healthily
      every ~1-2 min with a stale OUTPUT blob; this doc found the scheduler ITSELF paused a few
      hours later (14:25-15:39Z). If the flap traces back further than 14:25Z, the two findings may
      share a root cause (something intermittently disrupting the defi consolidator's steady
      state, of which "output blob staleness" and "scheduler flapping paused" are two symptoms) —
      not established this session, flagged as a hypothesis only.

## Codex SSOTs

- `/codex/05-infrastructure/data-pipeline-alerts.md` § DP-WATCHER-004, § "Alert-driven dependency
  revocation" (FLEET_HALT mechanism + the 2026-08-17-closed double-page gap this doc's finding 6
  may be a NEW recurrence of, in a different shape — a window that isn't just double-paging but
  possibly not writing at all for this bucket).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` (consolidator runtime + liveness
  contract).

## Progress Log

- **2026-08-21, data_pipeline_failure escalation agt-2b817b (slot 31)**: filed after live diagnosis.
  Resumed the job at 15:52:59Z (no live window, no justifying VM). 5-minute background watch armed
  to check for immediate re-pause — result pending, will be appended below before this escalation
  closes.
- **2026-08-21, same session, watch completed**: `gcloud scheduler jobs describe` polled every 20s
  for 300s straight — job stayed `state: ENABLED` the entire window (re-verified live once more
  after the watch exited: still `ENABLED`, `userUpdateTime` unchanged at `15:52:59Z`). No re-pause
  observed. Per this doc's own todo 1 decision rule: downgrading priority `P1 -> P2` (no active
  re-triggering condition caught live), but NOT closing the doc — the missing-maintenance-window
  question (todo 2) is real regardless of whether this specific occurrence recurs, since
  `RevocationActuator._register_maintenance_windows` is correctly wired yet no window was found at
  diagnosis time. Escalation `agt-2b817b` closing out here (one-shot lifecycle); this doc stays
  `assigned_vm: planning` for a future dispatch to pick up todos 1-3.
