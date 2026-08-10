---
doc_type: issue
title:
  "DP_FLEET_MONITOR_RUN_STARTED/COMPLETED kept mirroring to Slack after the mirror_live fix shipped — real cause is a
  legacy Cloud Run Job dual-consuming lifecycle-events-sub, compounded by a stale base-image UAC dependency"
summary: >-
  A code-level fix (unified-api-contracts `mirror_live` field + alerting-service router gate, shipped 2026-08-07 as
  unified-api-contracts@8f670c459 + alerting-service@60d525fc6) to stop DP_FLEET_MONITOR_RUN_STARTED/ COMPLETED
  mirroring to #data-pipeline-alerts had ZERO live effect despite a correct, deployed, 100%-traffic Cloud Run revision
  (dp-alerting-subscriber-00021-spf). Root cause, confirmed via direct docker inspection of the deployed image + Cloud
  Logging: a SEPARATE Cloud Run JOB, `uts-prod-alerting-paging` (triggered hourly by Cloud Scheduler
  `uts-prod-alerting-paging-cron`, `0 * * * *`), independently pulls from the SAME `lifecycle-events-sub` Pub/Sub
  subscription and is the ACTUAL source of every successfully-delivered "Data-Pipeline Alert[...]" Slack message
  (confirmed via `Event: SLACK_MESSAGE_SENT ... channel: data-pipeline-alerts` log lines attributed to
  `resource.labels.job_name=uts-prod-alerting-paging`, not the Service). `alerting_service/config.py`'s
  `run_subscriber_in_api` docstring literally says the Service (`dp-alerting-subscriber`, `RUN_SUBSCRIBER_IN_API=true`)
  was built to replace "the fragile batch-VM (stall-watchdog) deployment" — this Job appears to be exactly that legacy
  predecessor, never decommissioned.

  Two compounding bugs made this invisible to "is the fix deployed" checks: 1. Each hourly Job execution runs for ~1-2h
  (observed: an execution started 10:00 UTC completed 11:50 UTC), so
     Cloud Scheduler's hourly trigger causes OVERLAPPING executions. Each execution resolves the mutable
     `alerting-service:latest` tag fresh AT ITS OWN START — confirmed via `gcloud run jobs executions describe`
     matching the exact digest to the fix's build. Executions that started BEFORE the fix's ~10:53 UTC build kept
     running pre-fix code and mirroring unconditionally well past the "deploy" timestamp.
  2. Executions that DO pick up the fix's code CRASH: `AttributeError: 'DataPipelineAlertRule' object has no
     attribute 'mirror_live'` (confirmed live in Cloud Logging AND via a direct `docker run` against the exact
     deployed image, digest `sha256:f3e63806b256f49dac6801d30829e71e0bf6c52b779dcc6497dceeefc91df51a`). Cause: the
     `unified-trading-library` BASE IMAGE bakes in a stale `unified-api-contracts` copy at
     `/app/.deps/unified-api-contracts/` predating the `mirror_live` field entirely. alerting-service's Dockerfile
     runs `uv pip install --system --no-sources -e .`, which deliberately ignores the local path-dependency override
     (comment: "Sibling source repos are NOT in Cloud Build's context") and resolves `unified-api-contracts` from the
     Artifact Registry wheel index constrained by `pyproject.toml`'s `>=0.95.0,<1.0.0` — but since the base image's
     pre-baked copy already satisfies that wide range, `uv` (no `--upgrade`) never fetches a newer wheel, so the
     crash persists until the base image itself is refreshed. The crash is caught by `_page_own_dispatch_failure`,
     which posts a DIFFERENT-format `ALERT_DISPATCH_FAILED` message to `#uts-live-alerts` — not the channel the
     operator was watching, making the fix look silently ineffective rather than visibly broken.

  Operator decision 2026-08-07: PagerDuty is being deprecated for now (Slack-only routing); PagerDuty will be re-added
  later as part of the same unified alert flow. `dp-alerting-subscriber` already has `PAGERDUTY_DISABLED=true`;
  `uts-prod-alerting-paging` does not (and its logs show it actively — and currently unsuccessfully — attempting
  PagerDuty delivery for `CONSOLIDATOR_DOWN`, see the linked consolidator issue). Given PagerDuty is being deprecated,
  there is no live-paging reason to keep the legacy Job running; the fix is to pause `uts-prod-alerting-paging-cron`,
  let in-flight executions drain naturally, and consolidate all lifecycle-events-sub consumption onto
  `dp-alerting-subscriber` — plus fix the stale base-image UAC dependency so the mirror_live gate works once
  dp-alerting-subscriber is the sole consumer.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [alerting-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags:
  [
    alerting,
    slack-spam,
    dual-consumer,
    cloud-run-job,
    cloud-scheduler,
    stale-dependency,
    base-image,
    pagerduty-deprecation,
    P1,
  ]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
  ]
created: 2026-08-07
last_updated: "2026-08-09"
author: unknown
priority: P3
parent_epic: observability_master
source: >-
  Traced from a live #data-pipeline-alerts Slack reconciliation session, 2026-08-07 — the mirror_live fix
  (unified-api-contracts@8f670c459 + alerting-service@60d525fc6) was verified correct in code but ineffective live.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
    alerting-service/alerting_service/config.py,
    alerting-service/Dockerfile,
  ]
---

## Todos

- [x] [SCRIPT] P1. Fix the stale base-image `unified-api-contracts` dependency — alerting-service Dockerfile now runs
      `uv pip install --system --no-sources --upgrade-package unified-api-contracts -e .` instead of a plain resolve, so
      it always fetches the freshest AR-published UAC wheel rather than silently accepting the base image's pre-baked
      copy. Shipped `alerting-service@db580b65e` to LDR, QG-green. NOT YET on `main` — blocked by an unrelated,
      already-tracked fleet-wide LDR→main promotion stall, see
      `/plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md` (fresh recurrence
      confirmed same day). Will drain automatically once that clears; no manual bypass attempted.
- [x] [OPERATOR] P1. Paused Cloud Scheduler job `uts-prod-alerting-paging-cron` (state: PAUSED, confirmed via
      `gcloud scheduler jobs pause`). Existing executions (`uts-prod-alerting-paging-xc57k` started 12:00Z, `-xkkv5`
      started 13:00Z) left to drain naturally, no force-kill.
- [x] [SCRIPT] P1. Verified live: `slack-read-channel.py --channel data-pipeline-alerts --hours 1` returned 0 messages
      as of ~13:09Z and again ~14:48Z — DP_FLEET_MONITOR_RUN_STARTED/COMPLETED have genuinely stopped. (The
      `dp-alerting-subscriber`-still-crashes-on-mirror_live half of this todo — confirming a real CRITICAL DP event
      mirrors cleanly post-fix — is still open pending the Dockerfile fix reaching `main` + a redeploy; see above.)
- [x] ✅ [SCRIPT] P3. Deleted `uts-prod-alerting-paging` + `uts-prod-alerting-paging-cron` — both confirmed NOT FOUND
      via `gcloud run jobs describe` + `gcloud scheduler jobs list` as of 2026-08-10 (~3 days stable since scheduler
      pause on 2026-08-07). Dead infra cleaned up.

## Progress Log

- 2026-08-10 (slot 16, infra): Confirmed both `uts-prod-alerting-paging` (Cloud Run Job) and
  `uts-prod-alerting-paging-cron` (Cloud Scheduler) are already deleted (NOT FOUND / no matching scheduler jobs).
  Scheduler had been PAUSED since 2026-08-07; dp-alerting-subscriber remains the sole lifecycle-events-sub consumer.
  Flipped final P3 todo — all items done, doc eligible for archival.
- 2026-08-07: Filed after tracing the real root cause via Cloud Logging (dual Pub/Sub consumers on
  `lifecycle-events-sub`) + a direct `docker run` inspection of the deployed image (confirmed the base-image UAC
  staleness). Proceeding to fix in this same session per operator direction ("Consolidate onto dp-alerting-subscriber").
- 2026-08-07 ~13:00-14:48Z: Shipped the Dockerfile fix (`alerting-service@db580b65e`) + paused the legacy Job's
  scheduler. Live-verified the user-visible symptom (Slack spam) is gone. The Dockerfile fix itself is stuck on LDR —
  traced this to an UNRELATED, already-known fleet-wide LDR→main promotion stall (zero promotions landed across a 5-repo
  sample in 4+ hours), added confirmation to the existing tracking doc rather than duplicating it. Primary bug closed;
  this doc stays open only for the base-image-fix-reaches-main tail + the P3 dead-infra cleanup.
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — the sole open item (P3, delete the paused legacy
  Job/scheduler outright) is deliberately time-gated ("once confirmed stable for a few days"), not blocked on anything
  external; genuine unscheduled follow-up.
- **context-scout 2026-08-09**: populated context_scope (4 entries).
- **round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09)**: RECLASSIFIED `assigned_vm: NA -> planning`.
  The sole open item's time-gate ("once confirmed stable for a few days") is now live-confirmed: the scheduler has been
  `PAUSED` and the Job has had ZERO executions for ~2 days since the last in-flight execution drained
  (`2026-08-07T14:50:53Z` -> now), per fresh `gcloud` checks this run — evidence added to the todo above.
  Conflict-checked: no other active plan/issue tracks deletion of `uts-prod-alerting-paging`/`-cron` (2 incidental
  mentions found, `june_2026_vintage_audit_findings_2026_07_27.md` and
  `issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`, both read-only context references, not
  trackers). Finalize twin authored:
  `alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07_finalize_2026_08_09.md`.
