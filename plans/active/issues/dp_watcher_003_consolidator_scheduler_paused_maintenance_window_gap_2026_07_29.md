---
doc_type: issue
title:
  DP-WATCHER-003 has no maintenance-window awareness — pages CRITICAL on deliberate, plan-tracked cron pauses
  (2026-07-29)
summary: >-
  Escalation triage (escalation agt-4ec68a, wall_type=data_pipeline_failure) for a CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED page on `uts-prod-manifest-consolidator-market-data-prediction-cron`. Confirmed NOT a
  bug: the cron was deliberately paused 2026-07-29 as part of `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s
  tracked pause/apply/resume sequence, whose own resume todo is intentionally still open pending the apply step. The
  real (pre-existing, undispatched) gap: `consolidator_scheduler_watcher.py` (DP-WATCHER-003) has zero
  maintenance-window awareness by design — unlike DP-WATCHER-002's `check_cron_fired` pause-awareness (KEY #2) — and the
  ad-hoc `gcloud scheduler jobs pause` workflows used by backfill plans (this one, and the cefi migration before it)
  never register via the already-shipped `scheduler_maintenance.pause_for_maintenance()` CAS primitive either. The
  combination guarantees every deliberate backfill-driven cron pause pages CRITICAL with no suppression path until the
  cron is resumed.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags: [data_pipeline_failure, dp-alerts, consolidator, maintenance-window, scheduler, false-positive-by-design]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-29
parent_epic: manifest_master
assigned_vm:
locked_by:
priority: P2
source: >-
  data_pipeline_failure escalation agt-4ec68a (dp-fleet-monitor → slot-4), CONTEXT: "CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-003) — manifest-consolidator scheduler
  'uts-prod-manifest-consolidator-market-data-prediction-cron' is PAUSED (not -legacy-)."
resolved_by:
---

# DP-WATCHER-003 maintenance-window gap

## What I found

The escalation named a CRITICAL `DP_CONSOLIDATOR_SCHEDULER_PAUSED` page for
`uts-prod-manifest-consolidator-market-data-prediction-cron`. No issue doc had been pre-filed (the alert carried the
detail directly). Traced the finding:

1. **`deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py`** —
   `check_consolidator_scheduler_paused()` (DP-WATCHER-003) pages CRITICAL for **every** non-`-legacy-` consolidator
   scheduler job found `PAUSED`, no exceptions. Its own docstring states this is deliberate: it is the INVERSE of
   `meta_watchers.check_cron_fired`'s pause-awareness (KEY #2, which treats `PAUSED` as "intentional, suppress") —
   DP-WATCHER-003 exists specifically to catch an **accidental** pause nobody meant to leave in place (root-caused
   2026-07-13: both sports consolidator schedulers found PAUSED with no maintenance marker, for an unbounded period,
   discovered only by chance). It has zero code path that consults any "this pause is sanctioned" signal.
2. **`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`** Progress Log, 2026-07-29 entry ("crons
   paused, fresh snapshots taken") — slot-10 paused BOTH `uts-prod-manifest-consolidator-market-data-prediction-cron`
   and `…-tradfi-cron` today via raw `gcloud scheduler jobs pause`, as the pause half of that plan's tracked
   pause→apply→resume sequence. The plan's own downstream todos ("Apply the prediction available_at backfill" / "Resume
   the prediction consolidator cron") are open and un-dispatched — the resume todo is INTENTIONALLY not yet executed (a
   prior progress-log entry explicitly declined to resume early: "nothing to resume — the backfill hasn't been applied
   yet; resuming the cron now would defeat the pause/apply/resume sequence").
3. **`deployment-service/deployment_service/data_pipeline_monitors/scheduler_maintenance.py`** — a CAS
   maintenance-window primitive (`pause_for_maintenance`/`resume_after_maintenance`/`maintenance_status`, wrapping
   `unified_trading_library.maintenance_window`) already exists, built for exactly this "a deliberate pause is invisible
   to a second agent/watcher" problem (cites `sports_cf8_available_at_backfill_regression_2026_07_13.md` Finding 1). Its
   own docstring says adoption by the ad-hoc backfill pause scripts was **deliberately deferred** ("routing which
   scripts should switch and when is an operator/infra-owner decision, not this module's own scope"). Confirmed: neither
   the `mtds_available_at_...` backfill's pause step, nor the cefi migration's pause/resume calls
   (`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`), use it — every observed cron pause in the corpus
   is a raw `gcloud scheduler jobs pause/resume` call.

## Why it matters

Today's page is a **correctly-functioning, false-positive-by-current-design** alert: DP-WATCHER-003 is doing exactly
what it was built to do (page on any non-legacy pause, no exceptions, because distinguishing accidental-from-deliberate
reliably was judged not worth the risk of re-introducing the 2026-07-13 blind spot). No code defect exists in
DP-WATCHER-003 today — do NOT silently suppress it or the accidental-pause detection that motivated it is gone.

The gap is a genuine, pre-existing, un-adopted retrofit: (a) DP-WATCHER-003 has no way to check a live, operator-
sanctioned maintenance window even though the primitive to register one already ships, and (b) the ad-hoc pause scripts
that plans keep hand-rolling (`mtds_available_at_cross_asset_backfill_2026_07_13.md`, the cefi migration before it)
don't register one either — so the two halves that would make suppression safe are both currently unwired. Every future
backfill-driven deliberate pause will keep paging CRITICAL for its full duration with no suppression path, which is
alert-fatigue-inducing (and risks operators/agents learning to reflexively dismiss DP-WATCHER-003 pages — the exact
failure mode that let the 2026-07-13 pause go unnoticed in the first place).

## Recommended decision

Not urgent (today's page requires no action beyond what `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own
open apply+resume todos already do — completing them clears the page). This is a scoped hardening follow-up, not a live
incident.

- [ ] [CODE] P2. Wire `consolidator_scheduler_watcher.check_consolidator_scheduler_paused()` to call
      `scheduler_maintenance.maintenance_status(bucket)` before paging — if a live, unexpired window's `scheduler_jobs`
      covers the paused `job_name`, downgrade to INFO (log + skip the page) instead of CRITICAL; an expired/absent
      window still pages exactly as today. Repo: `deployment-service`.
- [ ] [CODE] P2. Retrofit the two known ad-hoc pause/resume call sites (`mtds_available_at_cross_asset_backfill`'s
      remaining prediction/tradfi resume todos in `market-tick-data-service`'s backfill scripts, and any future
      backfill-cron-pause script) to acquire/release via `scheduler_maintenance.pause_for_maintenance()` /
      `resume_after_maintenance()` instead of raw `gcloud scheduler jobs pause/resume` — this is the operator/
      infra-owner adoption decision `scheduler_maintenance.py`'s own docstring flags as deferred; do this only after the
      first todo above ships, so the registration is meaningful. Repo: `market-tick-data-service` (+ any other repo with
      a raw-gcloud consolidator pause script found during the sweep).
