---
doc_type: issue
title: >-
  DP-LIVE-003's new AWS liveness check for agent-orch-planning-vm- is code-correct but cannot execute in production —
  the uts-prod-dp-meta-watchers Cloud Run Job has zero AWS credentials wired in
summary: >-
  A follow-up to `dp_cron_did_not_fire_false_positive_burst_2026_08_10.md` built a real, dedicated AWS EC2 liveness
  check for the `agent-orch-planning-vm-` registry prefix
  (`missing_live_producer_watcher._agent_orch_planning_vm_present` →
  `deployment_service.backends.aws_census.describe_ec2_instance_state`, deferred boto3, honest degradation), replacing
  the prior blanket `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` exclusion. The check's LOGIC is confirmed correct —
  live-verified in a dev session with real AWS CLI credentials (`aws ec2 describe-instances --region ap-northeast-1
  --instance-ids i-0c9b283b31d6b5ca7` → `State.Name=running`, `PublicIpAddress=13.113.200.22`) and covered by mocked
  unit tests. But the DETECTOR itself runs as the `uts-prod-dp-meta-watchers` Cloud Run Job on GCP
  (`terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`), authenticated as the `unified_trading` GCP service account
  — this runtime has ZERO AWS identity configured (no `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` in its
  `environment_variables` block, no cross-cloud workload-identity federation). In production, every call to
  `describe_ec2_instance_state` will hit boto3's credential-resolution chain, find nothing, and the sanctioned
  honest-degradation contract will return `None` — DP-LIVE-003 SKIPS the `agent-orch-planning-vm-` prefix every sweep
  (never a false page, never a false "present" either) — functionally identical to the prior blanket-exclusion state,
  NOT actively monitored, despite the code path now being real and ready.

  This is not a new gap — it is the SAME documented credential gap already called out in
  `terraform/gcp/cost_snapshot_scheduler.tf`'s AWS cost-slice comment ("`aws.parquet` only populates once the service
  has AWS creds... Absent creds, the AWS cloud is skipped... the same credential gap that keeps AWS cost data off the
  deployed API today — the API works locally only via `~/.aws/credentials`"), now confirmed to ALSO block
  `deployment_api.routes._aws_deployments`'s `list_ec2_census`-backed AWS inventory route in production, and now this
  new DP-LIVE-003 check as a third affected consumer. All three share ONE root cause and would share ONE fix.
status: open
nature: issue
asset_group: [cross-cutting, infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [data-pipeline-monitors, dp-live-003, aws-credentials, cross-cloud, missing-live-producer, agent-orchestrator-vm]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
created: 2026-08-10
author: sub-agent (Claude Code session, dispatched to build the AWS liveness check + not_yet_active lifecycle state)
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-10
locked_since:
context_scope:
  [
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    deployment-service/deployment_service/backends/aws_census.py,
    deployment-service/terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf,
  ]
source: >-
  Discovered while resolving dp_cron_did_not_fire_false_positive_burst_2026_08_10.md's [OPERATOR] todo on the fate of
  agent-orch-planning-vm-: building the real cross-cloud check surfaced that the detector's own production runtime has
  no path to actually execute it. Per this task's explicit instruction: "if AWS access genuinely isn't available from
  wherever this detector runs, DON'T fake it — document that as a real blocker in the issue doc instead of building
  something that can't actually execute in production."
---

# DP-LIVE-003 AWS liveness check — credentials gap blocking production activation

## What's confirmed

1. **The check is real and correct.** `deployment_service.backends.aws_census.describe_ec2_instance_state` (new,
   `deployment-service@f6a830f94f044fa9ee98b567ea47217629e9052d`) reuses the SAME sanctioned deferred-boto3 seam
   (`_ensure_boto3`/`_make_client`) as the existing `list_ec2_census`/`list_batch_census`/`list_ecs_census`/
   `list_lambda_census` functions in the same module — never an inline `boto3` import. Live-verified in this dev session
   (real AWS CLI credentials, `arn:aws:iam::427895769566:user/admin_od`):

   ```
   aws ec2 describe-instances --region ap-northeast-1 --instance-ids i-0c9b283b31d6b5ca7 \
     --query 'Reservations[].Instances[].{Id:InstanceId,State:State.Name,PublicIp:PublicIpAddress}'
   → [{"Id": "i-0c9b283b31d6b5ca7", "State": "running", "PublicIp": "13.113.200.22"}]
   ```

   Mocked unit coverage: `tests/unit/test_aws_census.py` (parsing/filter logic) +
   `tests/unit/test_missing_live_producer_watcher.py::test_agent_orch_planning_vm_present_maps_*` (state→bool/None
   mapping) + `::test_agent_orch_planning_vm_confirmed_stopped_pages` /
   `::test_agent_orch_planning_vm_check_unavailable_skips_without_paging` (end-to-end wiring).

2. **The production runtime has zero AWS credentials.** `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s
   `data_pipeline_meta_watchers_job` module (the Cloud Run Job that runs
   `python -m deployment_service.data_pipeline_monitors.cli --mode meta`, which is what invokes
   `missing_live_producer_watcher`) declares only:

   ```
   environment_variables = {
     GCP_PROJECT_ID = var.project_id
     DEPLOYMENT_ENV = var.environment
     CLOUD_PROVIDER = "gcp"
   }
   ```

   and runs as `service_account_email = google_service_account.unified_trading.email` — a GCP identity with no AWS IAM
   role, access key, or workload-identity-federation trust relationship. `boto3`'s default credential chain (env vars →
   shared config file → EC2/ECS instance-profile metadata endpoint) finds nothing on a GCP Cloud Run Job, so every
   `describe_ec2_instance_state` call in production raises (unauthenticated / no credentials found), which
   `aws_census.py`'s honest-degradation `except Exception` catches and logs, returning `None`.

3. **Net production effect today: no regression, but no new coverage either.** `None` propagates through
   `_agent_orch_planning_vm_present()` → `_resolve_presence()` → `check_missing_live_producers()`'s
   `if present is None: continue` branch — the prefix is skipped every sweep, never paged, never falsely marked present.
   This is the SAME observable behavior as the prior `_GCP_CENSUS_UNOBSERVABLE_PREFIXES` blanket exclusion it replaced —
   so shipping this change did not make anything WORSE, but it also does not yet deliver the "actively monitored again"
   outcome until credentials are provisioned.

4. **Not a new gap — a documented, pre-existing one.** `terraform/gcp/cost_snapshot_scheduler.tf`'s AWS-slice comment
   already states: "`aws.parquet` only populates once the service has AWS creds (`AWS_ACCESS_KEY_ID`/
   `AWS_SECRET_ACCESS_KEY` from a Secret Manager secret, e.g. `*-worker-aws-creds`)... This is the same credential gap
   that keeps AWS cost data off the deployed API today (the API works locally only via `~/.aws/credentials`)."
   `deployment_api.routes._aws_deployments`'s `GET /api/deployments/inventory` AWS slice (backed by the SAME
   `aws_census.list_ec2_census`/etc.) is a second, independently-affected consumer of this identical gap. This
   DP-LIVE-003 check is a third.

## Why this session didn't fix the credentials gap itself

Provisioning real AWS credentials into a GCP-hosted Cloud Run Job's runtime is a genuine infrastructure/security
decision, not a narrow code change: it requires (a) creating a least-privilege AWS IAM identity (read-only EC2 Describe
— note `ec2:DescribeInstances` does not support resource-level ARN scoping, so the grant is necessarily
account-wide-read, not instance-scoped) or standing up AWS↔GCP workload-identity federation (more involved but avoids a
long-lived key), (b) storing the resulting credential in GCP Secret Manager, (c) binding that secret + new env vars into
the `data_pipeline_meta_watchers_job` Terraform module (and re-deploying), and (d) deciding whether the SAME credential
should also unblock the cost-snapshot and deployment-inventory AWS slices (points 4 above) at the same time, since all
three share this root cause. That is materially bigger than "this incident needs" — the SAME reasoning the original
2026-08-10 fix already used to justify NOT touching the shared GCP-only `_list_running_vms()` census. Per this task's
explicit instruction, faking or hand-waving execution here was avoided; this doc documents the real blocker instead.

## Todos

- [ ] [OPERATOR] P2. Decide the credential-provisioning approach for AWS access from GCP-hosted Cloud Run Jobs: a
      long-lived least-privilege IAM access key stored in GSM (`*-worker-aws-creds`, matching the pattern
      `cost_snapshot_scheduler.tf` already names) vs. AWS↔GCP workload-identity federation (no long-lived key, more
      setup). Scope: should this be provisioned ONCE and shared by all three known-blocked consumers (DP-LIVE-003's
      `agent-orch-planning-vm-` check, `cost_snapshot_scheduler`'s AWS cost slice, `deployment_api`'s AWS deployment
      inventory), or per-consumer? Repo: deployment-service.
- [ ] [SCRIPT] P2. Once credentials are provisioned (blocked on the todo above), bind the secret + required env vars
      into `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `data_pipeline_meta_watchers_job` module, and
      live-verify the `agent-orch-planning-vm-` prefix goes from "skipped every sweep" to "actively evaluated" — check
      the meta-watchers job's own logs for the `describe_ec2_instance_state` warning disappearing, and confirm no new
      false pages fire. Repo: deployment-service.

## Progress Log

- 2026-08-10: Filed after confirming, via the terraform env-var block + the pre-existing `cost_snapshot_scheduler.tf`
  documentation of the identical gap, that the new (code-correct, live-verified-in-dev) AWS liveness check for
  `agent-orch-planning-vm-` cannot yet execute with real credentials in its actual production runtime
  (`uts-prod-dp-meta-watchers` Cloud Run Job, GCP service-account identity only). No code fix attempted here per this
  task's explicit instruction to document rather than fake — see
  `dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`'s Part 1 resolution for the shipped check itself.
- **context-scout 2026-08-14**: populated context_scope (4 entries).
