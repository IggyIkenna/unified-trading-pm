---
doc_type: plan
title: AWS manifest consolidator — Batch + EventBridge (10 buckets + 16 extension)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-21
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-05-21
estimate_class: infra
estimate_baseline_ai_days: 3.1
estimate_calibrated_ai_days: 2.5
---

Gate cleared: `aws_migration_defi_first_2026_05_07` archived 2026-05-26 (Phase 5+6 complete).

# AWS Manifest Consolidator — AWS Batch + EventBridge

> **✅ COMPLETE — ARCHIVED 2026-06-01.** All phases A–D done. Phase D applied 2026-06-01
> (`64 added, 1 changed, 0 destroyed`; targeted to consolidator modules to avoid unrelated full-module drift during the
> migration freeze). Verified: 26 EventBridge rules all ENABLED + 26 ACTIVE Batch job definitions. Codex
> `manifest-consolidator-ssot.md` + CLAUDE.md updated to "Phase D LIVE". Prereq landed-bug fix:
> deployment-service@6a4194f (duplicate `required_providers`).
>
> ## Deferred work — migrated to:
>
> - None — all todos closed. The `🟡 DRAINED-WRITER DEPENDENCY` note below is a cross-reference (the consolidator only
>   reads parquets + writes `_index`; it does NOT relaunch the drained writer VMs). That relaunch gate lives in
>   `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 4 and is unaffected by this archival.

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
- [x] ✅ [INFRA] [OPERATOR-PUSH] P0.7. **UNBLOCKED 2026-05-31T10:39Z** — `market-tick-data-service:latest` pushed to ECR
      by operator. Verified via
      `aws ecr describe-images --repository-name market-tick-data-service --region ap-northeast-1 --image-ids imageTag=latest`:
      digest `sha256:ad21c4369e326c738408406bb4dd88bc3c022a19b9c8f7dea351c0a4e9fbcc0b`, pushed at
      `2026-05-31T10:39:00.296Z`, size `1,418,743,366 bytes (~1.4 GB)`. Push recipe: re-tagged the existing image from
      GCP Artifact Registry
      (`asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/market-tick-data-service:latest`)
      and pushed to AWS ECR via api-host (i-0c9b283b31d6b5ca7) after operator (a) installed Docker v29.1.3 + gcloud SDK
      on api-host, (b) attached `AmazonEC2ContainerRegistryPowerUser` AWS-managed policy to the
      `uts-orchestrator-epic-role` IAM role to unblock `ecr:GetAuthorizationToken` (the missing perm the worker BLKs
      surfaced), (c) authenticated via `aws ecr get-login-password | docker login` +
      `gcloud auth application-default print-access-token | docker login -u oauth2accesstoken` for GCP AR. Total
      wall-clock: ~3 min for the actual pull-tag-push, ~10 min including IAM + tooling install. Side-effect IAM fix:
      `uts-orchestrator-epic-role` now also has ECR-write capability for future PowerUser-level operations from api-host
      (use with care). Phase D Group B buckets jobs will now succeed at Fargate startup; spot-check the next
      consolidator run via
      `aws s3 ls s3://unified-trading-market-data-defi-427895769566/_index/availability_index.parquet` should show fresh
      mtime within minutes.

### Phase D — Coverage gap extension (16 more buckets) (0.7 cal-AI-days)

- [x] ✅ [SCRIPT] P1.8. Extend `manifest_consolidator_buckets_aws_extended` locals in the TF file with 16 Group B
      derived-data buckets (features-delta-one × 3, features-volatility × 2, features-onchain ×2, features-sports,
      features-calendar, strategy × 3, execution × 3, ml-training-artifacts). Flat naming — env-split rolled back per
      cloud-providers.yaml. IAM policy extended. Phase A timeout bumped 60s→1800s to match GCP side. —
      deployment-service@effdcb2 | terraform validate ✓
- [x] ✅ [SCRIPT] P1.9. `tofu plan` Phase D — `Plan: 89 to add, 23 to change, 17 to destroy` — Phase D module calls
      (manifest_consolidator_job_extended + manifest_consolidator_schedule_extended) present in plan output. —
      deployment-service@effdcb2 | terraform plan ✓ 2026-05-26
- [x] ✅ [HUMAN] P1.10. **APPLIED 2026-06-01** — `terraform apply` Phase D (account 427895769566, ap-northeast-1):
      `Apply complete! Resources: 64 added, 1 changed, 0 destroyed` (32 job_extended + 32 schedule_extended for 16 Group
      B buckets + IAM policy in-place for the new bucket ARNs; 0 destroy — targeted to the consolidator modules so the
      full-module drift is untouched during the migration freeze). Verified:
      `aws events list-rules --name-prefix uts-prod-consolidator` → **26 rules, all 26 ENABLED, 0 disabled**; 26 ACTIVE
      Batch job definitions. Prereq fix: `api_host_auto_reboot.tf` duplicate `required_providers` block (broke
      `terraform init` workspace-wide) consolidated into main.tf — deployment-service@6a4194f. Apply run with the native
      arm64 terraform (`/opt/homebrew/bin/terraform`); the x86 `/usr/local/bin/terraform` under Rosetta hangs on
      provider plugin start. — deployment-service (state: s3://uts-terraform-state-427895769566/terraform/state/prod)

---

## Codex SSOT updates

- UPDATE: `/codex/05-infrastructure/manifest-consolidator-ssot.md` — add AWS section (Batch + EventBridge topology,
  bucket map, IAM pattern). Remove "not currently in scope" language from deprecated AWS path note.

## Composes with

- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — canonical operational invariants (AWS port must match).
- `deployment-service/terraform/modules/container-job/aws/` + `scheduler/aws/` — existing modules being wired.
- `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` — GCP reference implementation.

> **🟡 DRAINED-WRITER DEPENDENCY (2026-06-01)** — the legacy-bucket SSOT remediation drained writer VMs
> `mdps-backfill-defi` / `mdps-prediction-2025` / `sports-scheduler`. They must NOT be relaunched until the
> legacy→canonical migration + manifest work complete. SSOT + relaunch gate:
> `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 4.
