---
title: AWS manifest consolidator — scope + Terraform plan
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: blocked
locked_by: live-defi-rollout
locked_since: 2026-05-21
estimate_class: infra
estimate_baseline_ai_days: 3.1
created: 2026-05-21
parent: aws_migration_defi_first_2026_05_07
gates:
  - aws_migration_defi_first_2026_05_07:Phase-5-cross-cloud-rsync
  - aws_migration_defi_first_2026_05_07:Phase-6-ECS-Fargate
estimate_calibrated_ai_days: 2.5
blocked_by: |
  Phase 5 cross-cloud data rsync + Phase 6 ECS Fargate deployment must land first.
  Without Phase 6 VMs writing manifest shards to S3, there is nothing to consolidate.
---

> **GATE**: Execute ONLY after Phase 5 (cross-cloud rsync) + Phase 6 (ECS Fargate writing v8 manifest shards to S3) are
> green in `aws_migration_defi_first_2026_05_07.md`. Pre-authoring the Terraform now is safe; `tofu apply` must wait for
> the gate.

# AWS Manifest Consolidator — Scope + Plan

Port of the GCP Cloud Run manifest consolidator stack to AWS. The GCP side runs 10 Cloud Run Jobs triggered by Cloud
Scheduler every minute. The AWS equivalent uses the existing `container-job/aws` (AWS Batch + Fargate) and
`scheduler/aws` (EventBridge Scheduler) Terraform modules already present in `deployment-service/terraform/modules/`.

## Why this is simpler than it looks

Three things are already done:

1. **UTL consolidator is cloud-agnostic.** `unified_trading_library.manifest_consolidator` calls
   `cloud_interface.get_storage_client()` which routes to S3 when `CLOUD_PROVIDER=aws`. No Python changes needed.

2. **Terraform modules already exist.** `deployment-service/terraform/modules/container-job/aws/` (AWS Batch + Fargate)
   and `deployment-service/terraform/modules/scheduler/aws/` (EventBridge Scheduler) are the direct AWS counterparts of
   the GCP modules used by the existing GCP consolidator.

3. **Bucket list is known.** Same 10 buckets as GCP (substituting account ID for project ID), plus the 16 coverage-gap
   buckets identified in the GCP codex once they're wired server-side (features, strategy-store, execution-store,
   ml-artifacts).

## Scope

### Phase A — Terraform (target: pre-apply, can author now)

Create `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf`:

```hcl
locals {
  manifest_consolidator_buckets_aws = {
    "instruments-cefi"       = "instruments-store-cefi-${var.aws_account_id}"
    "instruments-tradfi"     = "instruments-store-tradfi-${var.aws_account_id}"
    "instruments-defi"       = "instruments-store-defi-${var.aws_account_id}"
    "instruments-sports"     = "instruments-store-sports-${var.aws_account_id}"
    "instruments-prediction" = "instruments-store-prediction-${var.aws_account_id}"
    "market-data-cefi"       = "market-data-tick-cefi-${var.aws_account_id}"
    "market-data-tradfi"     = "market-data-tick-tradfi-${var.aws_account_id}"
    "market-data-defi"       = "market-data-tick-defi-${var.aws_account_id}"
    "market-data-sports"     = "market-data-tick-sports-${var.aws_account_id}"
    "market-data-prediction" = "market-data-tick-prediction-${var.aws_account_id}"
  }
}
```

Wire each entry to:

- `module "manifest_consolidator_job"` using `source = "../modules/container-job/aws"` (AWS Batch + Fargate)
- `module "manifest_consolidator_cron"` using `source = "../modules/scheduler/aws"` (EventBridge `*/1 * * * *`)
- Container image: the same `market-tick-data-service` ECR image (UTL is a dep)
- Env var: `CLOUD_PROVIDER=aws` (routes `get_storage_client()` to S3)
- IAM execution role: `unified_trading_fargate_role` with S3 `GetObject` + `PutObject` + `ListBucket` on
  `arn:aws:s3:::${bucket}/_index/*` prefix per bucket

### Phase B — IAM (can author now, apply at gate)

New IAM policy document for the consolidator execution role, attached to the Fargate task role:

```hcl
data "aws_iam_policy_document" "manifest_consolidator" {
  statement {
    sid    = "ManifestConsolidatorS3"
    effect = "Allow"
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = concat(
      [for b in local.manifest_consolidator_buckets_aws : "arn:aws:s3:::${b}"],
      [for b in local.manifest_consolidator_buckets_aws : "arn:aws:s3:::${b}/_index/*"],
    )
  }
}
```

### Phase C — Verification (after `tofu apply`)

```bash
# List active jobs (expect 10)
aws batch list-jobs --job-queue uts-prod-manifest-consolidator --status SUCCEEDED --max-results 10

# Confirm EventBridge crons enabled (expect 10 ENABLED schedules)
aws scheduler list-schedules --group-name uts-prod-consolidator | jq '.Schedules[].State'

# Spot-check canonical blob freshness (expect mtime < 90s ago)
aws s3 ls s3://market-data-tick-defi-427895769566/_index/availability_index.parquet
```

### Phase D — Coverage gap extension (after Phase C green)

Extend `manifest_consolidator_buckets_aws` with the 16 missing service buckets (features, strategy-store,
execution-store, ml-artifacts) that match the GCP coverage gap in the consolidator codex. Same IAM additions apply.

## Estimate

| Phase                              | Work                                                                                                                 | Cal-AI-days |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------- |
| A — Terraform authoring            | Write `manifest_consolidator_scheduler.tf`, wire container-job/aws + scheduler/aws modules, set `CLOUD_PROVIDER=aws` | 0.8         |
| B — IAM policy                     | Write + attach Fargate task role policy                                                                              | 0.3         |
| C — Apply + verify                 | `tofu apply` + smoke-test 10 buckets + mtime check                                                                   | 0.7         |
| D — Coverage gap (16 more buckets) | Extend locals + apply + verify                                                                                       | 0.7         |
| **Total**                          |                                                                                                                      | **2.5**     |

## Decision: file sub-plan (not BLOCKED-OPERATOR-DECISION)

The AWS consolidator IS needed once Phase 6 ECS Fargate VMs run on AWS. Without it, S3 manifest shards accumulate
indefinitely (identical to the GCP VM-only state before Cloud Run was wired). The operator decision from 2026-05-20
codex update applies: "consolidation is canonical; the legacy VM is deprecated."

AWS runs the same UTL, same manifest shards, same canonical index blob pattern — the consolidator is a pre-condition for
correct `read_availability_index` on AWS-side readers.

**Pre-author now, gate on Phase 5 + 6.** This plan is filed BLOCKED; Terraform authoring (Phase A + B) can proceed in
the same slot that executes Phase 5 rsync.

## Composes with

- [`codex/05-infrastructure/manifest-consolidator-ssot.md`](../../codex/05-infrastructure/manifest-consolidator-ssot.md)
  — canonical spec; AWS port must satisfy the same operational invariants.
- [`aws_migration_defi_first_2026_05_07.md`](./aws_migration_defi_first_2026_05_07.md) — parent; Phase 5 + 6 are the
  gate.
- `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf` — the output artefact (create in Phase A).
- `deployment-service/terraform/modules/container-job/aws/` + `scheduler/aws/` — existing modules to wire.
