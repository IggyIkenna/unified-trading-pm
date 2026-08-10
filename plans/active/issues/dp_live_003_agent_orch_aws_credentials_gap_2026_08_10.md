---
doc_type: issue
title: DP-LIVE-003 — agent-orch-planning-vm- AWS liveness check has ZERO AWS credentials in the production Cloud Run Job (uts-prod-dp-meta-watchers)
summary: >-
  The dedicated cross-cloud liveness check for `agent-orch-planning-vm-`
  (`missing_live_producer_watcher._agent_orch_planning_vm_present`, shipped
  `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`) is genuinely correct — live-verified against real AWS
  credentials (`aws ec2 describe-instances --region ap-northeast-1 --instance-ids i-0c9b283b31d6b5ca7` →
  `State.Name=running`, `PublicIpAddress=13.113.200.22`) — but the `uts-prod-dp-meta-watchers` Cloud Run Job that runs
  the DP-LIVE-003 meta sweep has ZERO AWS credentials wired in. Confirmed via
  `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `environment_variables` block (GCP-only; the same
  documented gap already called out in `cost_snapshot_scheduler.tf`'s AWS cost-slice comment). In production today this
  check calls `aws_census.describe_ec2_instance_state`, gets a `NoCredentialsError`, and honestly degrades to `None` —
  DP-LIVE-003 SKIPS `agent-orch-planning-vm-` every sweep (never pages, never falsely reports present). Functionally
  identical to the prior blanket `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` exclusion for now, but the code path is real,
  tested, and self-activates with zero further code change once credentials are provisioned.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [dp-live-003, missing-live-producer, aws, credentials, cloud-run, cross-cloud, data-pipeline-alerts]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-08-10
author: sub-agent (Claude Code session, dispatched to root-cause + fix the DP_CRON_DID_NOT_FIRE burst)
parent_epic: infrastructure_master
priority: P1
assigned_vm: NA
execution_scope: operator-gated
drift_direction: advance-code
depends_on: []
source:
  [
    "2026-08-10: raised while resolving the DP_CRON_DID_NOT_FIRE burst — the real AWS liveness check for
    `agent-orch-planning-vm-` was built and live-verified, but the production Cloud Run Job has no AWS credentials. The
    referencing issue doc (`/plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`) states the
    blocker and this doc was created to track it (the prose referenced it as filed but the file did not exist until now).",
  ]
resolved_by:
locked_by:
locked_since:
---

# DP-LIVE-003 — `agent-orch-planning-vm-` AWS liveness check: credentials gap in production

## What was found

The `DP_CRON_DID_NOT_FIRE` burst issue
(`/plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`) documents that a REAL, dedicated AWS
EC2 liveness check was built for `agent-orch-planning-vm-` (see its Progress Log, 2026-08-10 session):

- **Part 1 — real AWS liveness**: replaced the blanket `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` exclusion with
  `missing_live_producer_watcher._agent_orch_planning_vm_present`, via a new
  `deployment_service.backends.aws_census.describe_ec2_instance_state` seam (deferred boto3, honest degradation) —
  filters by the orchestrator's Elastic IP (`13.113.200.22`, resilient to instance replacement) with the instance id
  (`i-0c9b283b31d6b5ca7`) as a belt-and-braces cross-check. Evidence: `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`.
- **The blocker**: the `uts-prod-dp-meta-watchers` Cloud Run Job that runs this detector has ZERO AWS credentials wired
  in (confirmed via `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `environment_variables` block — GCP-only
  — and the SAME documented gap already called out in `cost_snapshot_scheduler.tf`'s AWS cost-slice comment).

## Impact

In production today the check calls `aws_census.describe_ec2_instance_state`, receives a `NoCredentialsError`, and
honestly degrades to `None` every sweep — DP-LIVE-003 skips `agent-orch-planning-vm-` (never pages, never falsely
reports present). This is functionally identical to the prior exclusion state for now, but it means production has no
real AWS-based liveness signal for the orchestrator VM until credentials are provisioned. The code is correct, tested,
and self-activates with zero further code change once credentials land.

## Required fix

Provision AWS credentials (least-privilege `ec2:DescribeInstances`, ap-northeast-1) into the
`uts-prod-dp-meta-watchers` Cloud Run Job's `environment_variables`, matching the AWS cost-slice pattern already
documented in `cost_snapshot_scheduler.tf`. Re-deploy, then confirm a live sweep calls `describe_ec2_instance_state`
successfully and reports `agent-orch-planning-vm-` present.

## Status

Open — awaiting credential provisioning (operator-gated; the credential itself is a secrets action outside the
data-pipeline-code fix that shipped in `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`).
