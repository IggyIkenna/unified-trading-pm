---
doc_type: issue
title: "Seven enabled Cloud Scheduler jobs target missing Cloud Run Jobs"
summary: >-
  The 2026-08-20 data-pipeline alerts reconciliation cross-checked 118 enabled Scheduler targets against 125 live
  Cloud Run Jobs in asia-northeast1 and found seven enabled targets whose jobs do not exist. Direct gcloud run jobs
  describe checks returned NOT_FOUND for each. They are firing into a 404/void and have no corresponding DP_* alert,
  so this is an uncovered infra failure (classification f), not a routing or dedup bug.
status: open
nature: issue
asset_group: [meta]
stage: [data, live]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [scheduler, zombie, cloud-run, data-pipeline-alerts, uncovered-failure]
related:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/05-infrastructure/deployment-observability.md
created: 2026-08-20
author: data_pipeline_alerts_reconciler (slot 29, one-shot dispatch agt-88ddd3)
source: data_pipeline_alerts_reconcile live scheduler census
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: infrastructure_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    deployment-service/terraform/gcp/t1_batch_scheduler.tf,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
---

# Enabled Scheduler targets with no matching Cloud Run Job - 2026-08-20

## Live evidence

The reconciliation sweep mechanically compared every Scheduler HTTP target in asia-northeast1 against gcloud run jobs
list for project central-element-323112:

- Scheduler targets parsed: 118
- Cloud Run Jobs present: 125
- Missing data-pipeline targets: 7

Direct gcloud run jobs describe calls returned Cannot find job for all seven:

- uts-prod-features-calendar-service-t1-recon
- uts-prod-features-commodity-service-t1-recon
- uts-prod-features-cross-instrument-service-t1-recon
- uts-prod-features-delta-one-service-t1-recon
- uts-prod-features-multi-timeframe-service-t1-recon
- uts-prod-features-volatility-service-t1-recon
- uts-prod-ml-service-t1-recon

The Scheduler jobs are enabled. Their targets point at deleted or never-created Cloud Run Jobs and can produce recurring
404/NOT_FOUND executions without a DP alert. This is classification (f) from the reconciliation procedure: a real
infra failure with no alerting coverage, not a DP router/dedup defect.

Two other missing targets were found but are outside this issue's data-pipeline scope:
uts-prod-client-reporting-daily-snapshot and uts-prod-execution-service-config-snapshot. They need ownership
confirmation before cleanup or replacement is selected.

## Required resolution

- Confirm whether each seven target is retired, renamed, or expected to exist in another region/project.
- If retired, remove or disable the Scheduler job through owning deployment configuration and verify no further executions;
  if renamed, repoint it to the live job and verify a successful execution.
- Add or extend a standing zombie-target detector so future missing targets are surfaced outside Slack.
- Re-run the full target-vs-job census and record terminal evidence before closing.

No Scheduler job was paused, deleted, or repointed by this pass.

## Progress Log

- 2026-08-20T08:04Z (data_pipeline_alerts_reconciler, slot 29, dispatch agt-88ddd3): issue filed from live
  cross-check; direct NOT_FOUND evidence captured above. Operator/owner decision is required for cleanup or repointing.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
