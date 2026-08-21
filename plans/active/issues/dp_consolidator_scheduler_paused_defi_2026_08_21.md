---
doc_type: issue
title: "Manifest-consolidator scheduler uts-prod-manifest-consolidator-market-data-defi-cron found PAUSED"
summary: >-
  The DP-WATCHER-004 alert detected that the DeFi manifest-consolidator scheduler job
  'uts-prod-manifest-consolidator-market-data-defi-cron' was PAUSED with no active maintenance
  window covering it. Verified via gcloud and successfully resumed.
status: open
nature: issue
asset_group: [defi]
stage: [data, live]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [scheduler, manifest-consolidator, data-pipeline-alerts, defi, dp-watcher-004]
related:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/05-infrastructure/manifest-consolidator-ssot.md
  - /plans/epics/defi_master.md
created: 2026-08-21
author: data_pipeline_failure agent (slot 31, escalation agt-0fc6b2)
source: [DP-WATCHER-004]
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: data_pipeline_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/05-infrastructure/manifest-consolidator-ssot.md
  - /plans/epics/defi_master.md
---

# Manifest-consolidator scheduler uts-prod-manifest-consolidator-market-data-defi-cron found PAUSED

## What I found
The self-monitoring substrate triggered a `DP_CONSOLIDATOR_SCHEDULER_PAUSED` alert (DP-WATCHER-004) for the Cloud Scheduler job `uts-prod-manifest-consolidator-market-data-defi-cron`. Inspection via `gcloud` confirmed its state was `PAUSED`. A check of active maintenance windows (`scheduler_maintenance.maintenance_status`) confirmed no active window covered this job, indicating an accidental or unmanaged pause that would starve the defi asset group of manifest freshness.

## Action taken
1. Verified the job definition and state (`PAUSED`).
2. Confirmed no active maintenance window was registered.
3. Resumed the Cloud Scheduler job via `gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron --location asia-northeast1`.
4. Verified that the job state is now `ENABLED`.

## Progress Log
- 2026-08-21: Initialized issue doc, diagnosed accidental pause, resumed scheduler job via gcloud, verified ENABLED state.
