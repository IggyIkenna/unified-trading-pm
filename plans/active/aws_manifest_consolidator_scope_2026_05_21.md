---
title: AWS manifest consolidator — Batch + EventBridge (10 buckets + 16 extension)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
estimate_class: infra
estimate_baseline_ai_days: 3.1
estimate_calibrated_ai_days: 2.5
created: 2026-05-21
---

Gate cleared: `aws_migration_defi_first_2026_05_07` archived 2026-05-26 (Phase 5+6 complete).

# AWS Manifest Consolidator — AWS Batch + EventBridge

Port of the GCP Cloud Run manifest consolidator to AWS. GCP runs 10 Cloud Run Jobs + Cloud Scheduler crons at
`*/1 * * * *`. AWS equivalent uses the existing `container-job/aws` (AWS Batch Fargate) and `scheduler/aws` (EventBridge
Scheduler) Terraform modules in `deployment-service/terraform/modules/`.

UTL's `manifest_consolidator` is already cloud-agnostic: `CLOUD_PROVIDER=aws` routes `get_storage_client()` to S3. No
Python changes needed.

## Full-Execution Criterion

Phase C: `aws events list-rules --name-prefix uts-prod-consolidator --query 'Rules[].State'` returns 10 `"ENABLED"`.
Spot-check: `aws s3 ls s3://unified-trading-market-data-defi-427895769566/_index/availability_index.parquet` mtime < 90s
after first successful run (gated on `market-tick-data-service:latest` pushed to ECR). Phase D: same rules command
returns 26 `"ENABLED"`.

**Note**: Switched from EventBridge Scheduler to EventBridge Rules — `aws_cloudwatch_event_rule` + `batch_target` —
because EventBridge Scheduler does not support Batch as a direct target in ap-northeast-1.

---

### Phase A — Terraform authoring (0.8 cal-AI-days)

- [x] ✅ [SCRIPT] P0.1. Write `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf` with: 10-bucket
      `locals.manifest_consolidator_buckets_aws` map (Group A naming:
      `unified-trading-{instruments,market-data}-{cefi,tradfi,defi,sports,prediction}-{account_id}`); shared Batch
      Fargate compute environment + job queue `uts-prod-manifest-consolidator`; `for_each` module calls per bucket:
      `container-job/aws` (job def) + `scheduler/aws` (EventBridge `*/1 * * * *`); `CLOUD_PROVIDER=aws` +
      `MANIFEST_BUCKET` env vars; ECR image for market-tick-data-service. — deployment-service@pending |
      `terraform validate` ✓
- [x] ✅ [SCRIPT] P0.2. Add IAM policy `manifest_consolidator` (S3 GetObject/PutObject/DeleteObject/ListBucket on all 10
      bucket ARNs + `/*` prefixes). Attach to existing `aws_iam_role.unified_trading`. — inline in
      manifest_consolidator_scheduler.tf
- [x] ✅ [SCRIPT] P0.3. Add EventBridge scheduler IAM role with `batch:SubmitJob` permission on the job queue +
      `uts-prod-manifest-consolidator-*` job definitions. Wire to all schedule module calls. — inline in
      manifest_consolidator_scheduler.tf

### Phase B — tofu plan (0.3 cal-AI-days)

- [x] ✅ [SCRIPT] P0.4. `terraform validate` in `deployment-service/terraform/aws/` — exits 0. `tofu plan` (requires
      operator AWS creds) is Phase C P0.5 gate. — `terraform validate` ✓ 2026-05-26

### Phase C — tofu apply + verify (0.7 cal-AI-days)

- [x] ✅ [SCRIPT] P0.5. `terraform apply` with default AWS profile (account 427895769566). Applied: 10 EventBridge
      rules + 10 Batch job definitions (shared compute env + job queue pre-existing). ECR policy added to execution
      role. — deployment-service@abdb1fb | `terraform apply` ✓ 2026-05-26
- [x] ✅ [SCRIPT] P0.6. Verified 10 EventBridge rules ENABLED:
      `aws events list-rules --name-prefix uts-prod-consolidator` → all 10 `ENABLED`, `rate(1 minute)`. —
      deployment-service@abdb1fb | rules verified 2026-05-26
- [ ] [BLOCKED-INFRA] P0.7. Spot-check consolidation running — BLOCKED until `market-tick-data-service:latest` pushed to
      ECR repo `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com/market-tick-data-service`. Current ECR repo exists but
      is empty. Jobs fire and submit correctly (EventBridge invocations metric = 1, FailedInvocations = 0) but fail at
      Fargate startup with `ResourceInitializationError: ecr:GetAuthorizationToken`. ECR pull auth now granted via
      `AmazonEC2ContainerRegistryReadOnly` on `unified-trading-role-prod`. Unblocked once image is pushed.

### Phase D — Coverage gap extension (16 more buckets) (0.7 cal-AI-days)

- [ ] [SCRIPT] P1.8. Extend `manifest_consolidator_buckets_aws_extended` locals in the TF file with 16 Group B
      derived-data buckets (features-delta-one × 3, features-volatility × 2, features-onchain, features-sports,
      features-calendar, strategy × 2, execution × 3, ml-artifacts, ml-training-artifacts). Add to IAM policy + schedule
      module calls.
- [ ] [SCRIPT] P1.9. `tofu plan` Phase D — verify 16 additional job definitions + schedules in plan output.
- [ ] [HUMAN] P1.10. `tofu apply` Phase D + verify 26 schedules ENABLED.

---

## Codex SSOT updates

- UPDATE: `codex/05-infrastructure/manifest-consolidator-ssot.md` — add AWS section (Batch + EventBridge topology,
  bucket map, IAM pattern). Remove "not currently in scope" language from deprecated AWS path note.

## Composes with

- `codex/05-infrastructure/manifest-consolidator-ssot.md` — canonical operational invariants (AWS port must match).
- `deployment-service/terraform/modules/container-job/aws/` + `scheduler/aws/` — existing modules being wired.
- `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` — GCP reference implementation.
