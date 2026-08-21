---
doc_type: issue
title: "DP drilldown reconciliation Cloud Run Job OOMs without a DP alert"
summary: >-
  Live reconciliation found the enabled uts-prod-dp-drilldown-reconciliation Cloud Run Job reaching its configured
  memory limit on all three latest executions, while no DP-* alert for the failure appeared in the 24-hour
  #data-pipeline-alerts snapshot. The job is absent from deployment-service's CLOUD_RUN_JOBS registry, so the generic
  DP-WATCHER-006 population check cannot observe it.
status: open
nature: issue
asset_group: [meta]
stage: [data, live]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-watcher-006, drilldown, cloud-run-job, oom, uncovered-failure]
related:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/05-infrastructure/deployment-observability.md
created: 2026-08-21
author: data_pipeline_alerts_reconciler (slot 27, one-shot dispatch agt-827215)
source: data_pipeline_alerts_reconcile live Cloud Run execution census
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
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/05-infrastructure/deployment-observability.md
  - deployment-service/deployment_service/cloud_run_job_registry.py
  - deployment-service/deployment_service/data_pipeline_monitors/cloud_run_job_failure_watcher.py
  - deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf
---

# DP drilldown reconciliation Cloud Run Job OOM is uncovered — 2026-08-21

## Live evidence

The 24-hour `#data-pipeline-alerts` snapshot contained 1,403 messages and no `DP_CLOUD_RUN_JOB_FAILED` or other
alert naming `dp-drilldown-reconciliation`. Direct live Cloud Run execution checks in project
`central-element-323112`, region `asia-northeast1`, showed:

- `uts-prod-dp-drilldown-reconciliation-7bm4m` (2026-08-20 09:30Z): configured memory limit reached.
- `uts-prod-dp-drilldown-reconciliation-lmxrk` (2026-08-19 09:30Z): configured memory limit reached.
- `uts-prod-dp-drilldown-reconciliation-wlb9l` (2026-08-18 09:30Z): configured memory limit reached.

The Cloud Scheduler target `uts-prod-dp-drilldown-reconciliation-cron` is ENABLED and targets the live job. The job's
Terraform definition is provisioned at `cpu=8`, `memory=32Gi`, with `max_retries=0`; therefore the repeated limit
exhaustion is a failed production execution, not an intentional successful `DP_PHANTOM_ROWS` finding.

## Root cause and classification

This is classification (f), an infrastructure failure with missing alert coverage. The generic
`cloud_run_job_failure_watcher.py` scans GCP Cloud Run jobs from `CLOUD_RUN_JOBS`, but
`deployment_service/cloud_run_job_registry.py` contains the sibling audit jobs (`dp-daily-digest` and both manifest
hygiene jobs) and no `dp-drilldown-reconciliation` entry. `DP-WATCHER-006` consequently cannot inspect this job.

The failure class itself is already represented by `DP_CLOUD_RUN_JOB_FAILED`; no new DP registry event is warranted.
The missing registry population and the job's memory behavior are separate fixes: add the job to the monitored
population, then diagnose whether the 32Gi limit is insufficient or the unbounded manifest-index read needs the
planned bounded-memory implementation. Do not mute `DP_PHANTOM_ROWS` and do not write an empty or placeholder result.

## Required resolution

- Add `dp-drilldown-reconciliation` to the canonical Cloud Run job registry and verify DP-WATCHER-006 emits a live
  `DP_CLOUD_RUN_JOB_FAILED` finding on a failed execution, with a resolved bookend after a successful run.
- Diagnose and fix the OOM at the root (bounded manifest-index read or justified resource sizing), then verify a fresh
  scheduled execution succeeds and still performs the epsilon=0 drilldown check.
- Re-run the channel and scheduler/job census; close only with live execution success and alert-coverage evidence.

No Cloud Scheduler job was paused, deleted, or repointed by this reconciliation pass.

## Progress Log

- 2026-08-21 (slot 27, dispatch `agt-827215`): live 24-hour Slack snapshot and Cloud Run census found the three
  consecutive OOM executions and confirmed the job is absent from `CLOUD_RUN_JOBS`. Existing registry and watcher
  entries were read; no code or production resource was changed in this one-shot pass.
