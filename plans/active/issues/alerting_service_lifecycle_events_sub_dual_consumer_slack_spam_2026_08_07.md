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
author: unknown
priority: P1
parent_epic: observability_master
source: >-
  Traced from a live #data-pipeline-alerts Slack reconciliation session, 2026-08-07 — the mirror_live fix
  (unified-api-contracts@8f670c459 + alerting-service@60d525fc6) was verified correct in code but ineffective live.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
---

## Todos

- [ ] [SCRIPT] P1. Fix the stale base-image `unified-api-contracts` dependency (rebuild/republish the
      `unified-trading-library` base image, or find the existing `update-dependency-version.yml` fan-out mechanism
      referenced in CLAUDE.md and use it) so `DataPipelineAlertRule.mirror_live` actually resolves instead of raising
      `AttributeError`.
- [ ] [OPERATOR] P1. Pause Cloud Scheduler job `uts-prod-alerting-paging-cron` (asia-northeast1). Let existing
      `uts-prod-alerting-paging` executions drain naturally (no force-kill — avoid dropping in-flight Pub/Sub acks). Do
      NOT delete the Job/Scheduler outright until confirmed `dp-alerting-subscriber` fully covers its role.
- [ ] [SCRIPT] P1. Verify live: after old executions drain, confirm via
      `scripts/dev/slack-read-channel.py --channel data-pipeline-alerts` that DP_FLEET_MONITOR_RUN_STARTED/COMPLETED
      genuinely stop appearing, and that a real CRITICAL DP event still mirrors to Slack correctly via
      `dp-alerting-subscriber` alone (PagerDuty delivery not expected to succeed — deprecated per operator decision).
- [ ] [SCRIPT] P3. Once confirmed stable for a few days, consider deleting `uts-prod-alerting-paging` +
      `uts-prod-alerting-paging-cron` outright rather than leaving them paused indefinitely (dead infra).

## Progress Log

- 2026-08-07: Filed after tracing the real root cause via Cloud Logging (dual Pub/Sub consumers on
  `lifecycle-events-sub`) + a direct `docker run` inspection of the deployed image (confirmed the base-image UAC
  staleness). Proceeding to fix in this same session per operator direction ("Consolidate onto dp-alerting-subscriber").
