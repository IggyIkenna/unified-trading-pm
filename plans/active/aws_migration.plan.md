---
name: AWS Migration Plan
overview: Dual-cloud readiness for GCP primary and AWS secondary. Cloud-agnostic abstractions via unified-cloud-interface; migration phases for build path, runtime, and full dual-cloud deployment.
todos:
  - id: phase-1-cloud-agnostic
    content: "Verify cloud-agnostic abstractions; no direct google.cloud/boto3 in prod. SCOPE: all repos in workspace-manifest.json with type=library or type=service (not UIs). GATE: rg 'google\\.cloud|boto3' --type py --glob '!.venv*' --glob '!tests' returns 0 matches in production source across all in-scope repos; verified per-repo in QUALITY_GATE_BYPASS_AUDIT.md."
    status: pending
  - id: phase-2-buildspec
    content: "AWS build path (CodeBuild) — buildspec.aws.yaml passes per service. SCOPE: all repos that have cloudbuild.yaml. GATE: buildspec.aws.yaml exists alongside cloudbuild.yaml in every in-scope repo; buildspec.aws.yaml runs quality-gates.sh --no-fix --quick inside the built image (same pattern as cloud-build-test-in-image.mdc); CodeBuild simulated run exits 0 for at least 3 canary repos (one T0, one T2, one service)."
    status: pending
  - id: phase-3-runtime
    content: "AWS runtime (S3, Secrets Manager) — CLOUD_PROVIDER=aws works. GATE: CLOUD_PROVIDER=aws python -c 'from unified_cloud_interface import get_storage_client, get_secret_client; get_storage_client(); get_secret_client()' exits 0; S3 bucket naming matches {prefix}-${AWS_ACCOUNT_ID} pattern in aws_batch.py/aws_ec2.py; aws_batch.py and aws_ec2.py match cloud_run.py public interface (same method signatures)."
    status: pending
  - id: phase-4-dual-cloud
    content: "Full dual-cloud deployment — GCP + AWS parity. PARITY DEFINITION: (1) same quality-gates.sh exit code on GCP (cloudbuild.yaml) and AWS (buildspec.aws.yaml) for all in-scope repos; (2) same secret names mirrored in AWS Secrets Manager as in GCP Secret Manager; (3) same bucket structure in S3 as in GCS (different names, same prefix pattern); (4) CLOUD_PROVIDER switch changes only the concrete adapter, not business logic. GATE: pilot deployment of at least one service (instruments-service) on AWS ECS/Batch passes Layer 2 infra verification (verify_infra.py with CLOUD_PROVIDER=aws)."
    status: pending
  - id: per-service-checklist
    content: "Per-service checklist — I/O via get_storage_client/get_secret_client; no hardcoded IDs. GATE: each service repo has a completed QUALITY_GATE_BYPASS_AUDIT.md section for AWS migration listing: (1) all get_storage_client/get_secret_client calls confirmed; (2) no hardcoded GCP project IDs or bucket names in production source; (3) buildspec.aws.yaml present; (4) secret names documented in credentials-registry.yaml."
    status: pending
isProject: false
---

# AWS Migration Plan (Dual-Cloud Readiness)

**Order:** See master_pre_deployment_plan_chain.plan.md
**Reference:** dual-cloud-cost-ops-playbook.md, 05-infrastructure/README.md, cloud-agnostic.mdc
**Status:** GCP primary; AWS secondary [PLANNED]

---

## Blockers

| Blocker                                        | Type          | Specific Dependency                                                                                                          | Resolution                                                                                                                    |
| ---------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 cloud-agnostic scan not passed         | `[PLAN_TODO]` | [phase0_standards_enforcement.plan.md](phase0_standards_enforcement.plan.md) § todo `p0-t0-parallel` through `p0-gate-check` | All repos must pass the cloud-agnostic scan (zero direct google.cloud/boto3 imports in prod) before AWS migration work begins |
| Phase 1 cloud-agnostic cursor rule not created | `[PLAN_TODO]` | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-cloud-agnostic-rule`                             | cloud-agnostic.mdc cursor rule must exist and be enforced before verifying compliance across repos                            |

---

## Current State

- **CLOUD_PROVIDER** env var: gcp | aws
- **unified-cloud-interface:** StorageClient, SecretClient, QueueClient with GCP/AWS/Local providers
- **buildspec.aws.yaml** present in many repos (CodeBuild)
- **Secrets:** GCP Secret Manager primary; AWS Secrets Manager secondary
- **Storage:** GCS primary; S3 secondary (bucket naming: `{prefix}-${AWS_ACCOUNT_ID}`)

---

## Migration Phases

| Phase | Scope                                | Gates                                |
| ----- | ------------------------------------ | ------------------------------------ |
| 1     | Cloud-agnostic abstractions verified | No direct google.cloud/boto3 in prod |
| 2     | AWS build path (CodeBuild)           | buildspec.aws.yaml passes            |
| 3     | AWS runtime (S3, Secrets Manager)    | CLOUD_PROVIDER=aws works             |
| 4     | Full dual-cloud deployment           | GCP + AWS parity                     |

---

## Per-Service Checklist

1. All I/O via get_storage_client(), get_secret_client()
2. No hardcoded project/account IDs
3. buildspec.aws.yaml present and passing
4. Bucket/secret naming follows cloud-agnostic pattern

---

## References

- unified-trading-codex/05-infrastructure/README.md
- unified-trading-codex/11-project-management/dual-cloud-cost-ops-playbook.md
- cursor-rules: cloud-agnostic.mdc
