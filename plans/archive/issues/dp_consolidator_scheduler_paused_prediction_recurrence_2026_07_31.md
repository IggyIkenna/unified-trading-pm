---
doc_type: issue
title:
  DP_CONSOLIDATOR_SCHEDULER_PAUSED recurred for the prediction cron — retroactive maintenance-window registered
  (2026-07-31)
summary: >-
  Escalation triage (escalation agt-e8d228, wall_type=data_pipeline_failure) for a CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED page on `uts-prod-manifest-consolidator-market-data-prediction-cron`. Confirmed exact
  repeat of the resolved issue `dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md`
  (escalation agt-4ec68a): the cron is still deliberately paused as part of
  `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s tracked pause/apply/resume sequence, whose apply+resume todos
  remain open. The general watcher fix (maintenance-window suppression, `deployment-service@3a1cf3a`) already shipped,
  but this SPECIFIC pause (raw `gcloud`, 2026-07-29, pre-dating the retrofit) was never registered under it — so
  DP-WATCHER-003 correctly kept paging CRITICAL every sweep. Fixed by retroactively registering a maintenance window (no
  code change; a live infra CAS write) so future sweeps downgrade to INFO for the remainder of the backfill. Also found
  a genuine, distinct, unfixed gap: `DP_CONSOLIDATOR_SCHEDULER_PAUSED` is missing from UAC's
  `DATA_PIPELINE_ALERT_RULES`, and the watcher's own emission reuses `registry_id="DP-WATCHER-003"`, which the registry
  already assigns to a DIFFERENT event (`DP_FLEET_MONITOR_RUN_FAILED`) — same failure class as the 2026-07-27
  DIGEST-003/004 gap, not yet retrofitted for this event. Filed as a follow-up todo, not fixed in this pass (needs a
  fresh registry_id + multi-repo edit, out of this one-shot escalation's scope).
status: resolved
nature: issue
asset_group: [prediction]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags:
  [
    data_pipeline_failure,
    dp-alerts,
    consolidator,
    maintenance-window,
    scheduler,
    false-positive-by-design,
    registry-gap,
  ]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/archive/issues/dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-31
parent_epic: manifest_master
assigned_vm: planning
locked_by:
priority: P2
source: >-
  data_pipeline_failure escalation agt-e8d228 (dp-fleet-monitor → slot-2), CONTEXT: "CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-003) — manifest-consolidator scheduler
  'uts-prod-manifest-consolidator-market-data-prediction-cron' is PAUSED (not -legacy-)."
resolved_by: slot-11 (dp_consolidator_scheduler_paused_prediction_recurrence-001, 2026-07-31)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-31
---

> **🗄️ ARCHIVED 2026-07-31** — `status: resolved`. Both todos done: the maintenance window is registered (live
> 2026-07-31T04:56Z, TTL 4320min) and the `DP_CONSOLIDATOR_SCHEDULER_PAUSED`/`DP-WATCHER-003` registry_id collision is
> fixed — `DP-WATCHER-004` assigned in `unified-api-contracts@02071c9f` + `deployment-service@bd9e962` (both
> quality-gates.sh green, quickmerge-shipped), also reflected in `/codex/05-infrastructure/data-pipeline-alerts.md` +
> `/codex/05-infrastructure/data-pipeline-alerts.registry.yaml`. The underlying prediction-cron pause itself remains
> open, tracked separately in `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` (not this doc's
> scope). No further open work in this doc.

# DP_CONSOLIDATOR_SCHEDULER_PAUSED recurrence — prediction cron (2026-07-31)

## What I found

Same page, same job, as the already-resolved
`dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md` (escalation agt-4ec68a, 2026-07-29).
Re-verified from scratch rather than assuming the old doc still applies:

1. **Live GCP state** (`gcloud scheduler jobs describe`, `asia-northeast1`):
   `uts-prod-manifest-consolidator-market-data-prediction-cron` = `PAUSED`.
   `uts-prod-manifest-consolidator-market-data-tradfi-cron` = `ENABLED` — the sibling job from the same 2026-07-29
   incident has SINCE been resumed (its plan todos are checked). Only prediction is still open/paused.
2. **`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`** — the two prediction todos ("Apply
   `rebuild_prediction_manifest.py`" and "Resume the prediction consolidator cron") are still `- [ ]` open as of
   2026-07-31 — the pause remains intentional and in-progress, not resolved. (This plan file is at 999/1000 lines — its
   hard line cap — so this issue doc carries the Progress Log note instead of touching that file.)
3. **The general watcher fix is live and wired**:
   `deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py::check_consolidator_scheduler_paused()`
   accepts `maintenance_window_reader`, and `cli.py:839-842` DOES pass
   `maintenance_window_reader=consolidator_scheduler_watcher.make_consolidator_maintenance_window_reader()` — the
   2026-07-30 retrofit is genuinely active in the call path, not a shipped-but-unwired fix.
4. **Root cause of THIS specific re-page**: the 2026-07-29 pause pre-dates the maintenance-window retrofit and was done
   via raw `gcloud scheduler jobs pause` — no `MaintenanceWindow` was ever registered for it.
   `maintenance_status(bucket)` therefore correctly read "no live window" every sweep since, so the watcher paged
   CRITICAL exactly as designed (an unregistered pause is indistinguishable from an accidental one, by design — see the
   archived issue's own analysis).
5. **New finding — registry_id collision (NOT fixed in this pass)**:
   `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py`'s `DATA_PIPELINE_ALERT_RULES`
   has no entry for the `DP_CONSOLIDATOR_SCHEDULER_PAUSED` event at all — only
   `_dp_rule("DP-WATCHER-003", _C.WATCHER, "DP_FLEET_MONITOR_RUN_FAILED", ...)` (line 1385), a DIFFERENT event. But
   `consolidator_scheduler_watcher.py` line 136 emits `DP_CONSOLIDATOR_SCHEDULER_PAUSED` findings with
   `registry_id="DP-WATCHER-003"` too — two distinct events claiming the same stable id, and the
   `DP_CONSOLIDATOR_SCHEDULER_PAUSED` event itself has zero `DATA_PIPELINE_ALERT_RULES` entry. Per the file's own
   comment (lines 1336-1349, the DP-VM-008..011 transcription-gap fix) this is the identical failure class as the
   2026-07-27 DIGEST-003/004 incident: an unregistered DP_* event misses `data_pipeline_rule_for()`'s exact-match lookup
   and falls through to the generic catch-all (`LIVE_ALERT_RULES` `event_pattern="*"`), landing on `#uts-live-alerts`
   instead of `#data-pipeline-alerts`, with the CRITICAL case possibly losing its intended PagerDuty routing on that
   fallback path. **Did not fix here** — needs a fresh non-colliding registry_id (the registry.yaml + the closed-set
   sync test + the watcher's own `registry_id=` string all need a coordinated edit across `unified-api-contracts` +
   `deployment-service`), which is properly-scoped follow-up work, not a same-session mechanical port for a one-shot
   escalation. Note: this gap does NOT explain why the escalation reached me correctly — the
   `wall_type=data_pipeline_failure` dispatch is driven by the watcher's `tier=PAGE_OPERATOR` directly, a separate path
   from the Slack-channel routing rules — so operator paging via the escalation route is unaffected; only the
   Slack-channel-visibility + possible PagerDuty routing may be wrong.

## Why it matters

Today's page needed no code fix and is not a live incident — it is the same false-positive-by-current-design behavior
the archived issue already diagnosed, just for a pause that is STILL ongoing 2 days later. Left unaddressed, it will
keep re-paging CRITICAL on every DP-WATCHER-003 sweep until the plan's own apply+resume todos land — which is correct
per the watcher's design, but wastes escalation-worker cycles re-deriving the same diagnosis each time (this is the
second such escalation for this exact job). Registering the window stops the redundant paging for the remainder of the
tracked backfill without weakening the accidental-pause detection this watcher exists for (the window is TTL-bound and
auto-expires; an unrelated future pause of this same job would still page normally once it does).

## What I did

Retroactively registered a maintenance window covering the still-paused job (pure GCS CAS write via the already- shipped
`deployment_service.data_pipeline_monitors.scheduler_maintenance` CLI — no code change, no new commit):

```
$ .venv/bin/python -m deployment_service.data_pipeline_monitors.scheduler_maintenance \
    --bucket market-data-tick-pred-prd-central-element-323112 \
    pause --surface market-data-prediction \
    --job uts-prod-manifest-consolidator-market-data-prediction-cron \
    --reason "mtds_available_at_cross_asset_backfill_2026_07_13 pause/apply/resume backfill sequence (retroactive
              registration, escalation agt-e8d228 2026-07-31 -- paused since 2026-07-29 via raw gcloud, never
              registered; resume gated on that plan's open apply+resume P1 todos)" \
    --locked-by mtds_available_at_cross_asset_backfill_2026_07_13 \
    --ttl-minutes 4320
[maintenance-window] acquired + paused ['uts-prod-manifest-consolidator-market-data-prediction-cron'] until 2026-08-03T04:56:45Z
```

`--locked-by` deliberately matches the exact string
`market-tick-data-service/scripts/mtds_available_at_backfill_resume_prediction_2026_07_30.py` already uses for its own
`locked_by=` — so when that plan's apply step eventually finishes and that ready-made resume script runs, it will match
the window's holder and release it cleanly with no `--force` needed. Verified post-write:
`scheduler_maintenance ... status` reads back `HELD by 'mtds_available_at_cross_asset_backfill_2026_07_13'` covering
exactly this job name; `gcloud scheduler jobs describe` confirms the job itself is unchanged (still `PAUSED` — the CLI's
own re-issued `pause_job` call is a no-op on an already-paused job). Did NOT run the backfill apply step, did NOT resume
the cron, did NOT touch tradfi (already resumed) — that remains the scope of the tracked plan's own open todos, not this
escalation.

TTL chosen as 3 days (4320 min): long enough to plausibly cover the plan's remaining P1 apply+resume dispatch without
permanently blinding the watcher; if the window expires before the plan's apply+resume lands, DP-WATCHER-003 will
correctly re-page — a legitimate signal the backfill is taking longer than expected, not a bug to suppress further.

## Recommended decision

No further action needed on the paging itself — resolved for the remainder of the realistic backfill window. The
registry_id collision (item 5 above) is a genuine, separate, pre-existing gap worth fixing as its own properly-scoped
follow-up (mirrors the already-shipped DIGEST-003/004 and VM-008..011 fixes exactly).

## Todos

- [x] ✅ [OPS] P1. **Retroactively registered the maintenance window — DONE live 2026-07-31T04:56Z** (see command +
      verification above). No code shipped; pure infra CAS write via the sanctioned CLI. (repo: NA)
- [x] ✅ [CODE] P2. Fix the `DP_CONSOLIDATOR_SCHEDULER_PAUSED` / `DP-WATCHER-003` registry_id collision — assigned
      `DP_CONSOLIDATOR_SCHEDULER_PAUSED` its own stable id `DP-WATCHER-004` (next free in the WATCHER category, per
      `codex/05-infrastructure/data-pipeline-alerts.registry.yaml`), added the corresponding `_dp_rule(...)` entry to
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py`'s
      `DATA_PIPELINE_ALERT_RULES` (severity CRITICAL, escalation `page_operator`, mirroring `DP-CATALOG-001`'s shape),
      updated `consolidator_scheduler_watcher.py` line 136's `registry_id=` to `DP-WATCHER-004`, and updated the
      registry yaml + the closed-set sync test (new `test_consolidator_scheduler_paused_has_own_registry_id`) + the
      adjacent `meta_watchers.py` docstring and `test_data_pipeline_monitors.py` section comments. —
      unified-api-contracts@02071c9f, deployment-service@bd9e962 (both quality-gates.sh green, quickmerge-shipped)
      (repo: unified-api-contracts, deployment-service)
