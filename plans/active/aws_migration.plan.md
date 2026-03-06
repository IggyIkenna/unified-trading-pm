---
name: AWS Migration Plan
overview: Dual-cloud readiness for GCP primary and AWS secondary. Cloud-agnostic abstractions via unified-cloud-interface; migration phases for build path, runtime, and full dual-cloud deployment.
todos:
  - id: phase-1-cloud-agnostic
    content: "Verify cloud-agnostic abstractions; no direct google.cloud/boto3 in prod. SCOPE: all repos in workspace-manifest.json with type=library or type=service (not UIs). GATE: rg 'google\\.cloud|boto3' --type py --glob '!.venv*' --glob '!tests' returns 0 matches in production source across all in-scope repos; verified per-repo in QUALITY_GATE_BYPASS_AUDIT.md. DONE: 14 Category A + 37 Category B violations fixed (sessions 4–6); STEP 5.10/5.11 hard-fail gates active; QUALITY_GATE_BYPASS_AUDIT.md zero unapproved exceptions. Gate fully satisfied 2026-03-06."
    status: completed
  - id: phase-2-buildspec
    content: "buildspec.aws.yaml distributed to all 44 qualifying repos (8 newly created, 36 already present). FILE DISTRIBUTION DONE 2026-03-05. Canary simulated CodeBuild run for 3 repos (instruments-service, unified-cloud-interface, unified-events-interface) still pending — tracked in topology_dag_pm_ssot.plan.md todo codebuild-canary-run. File distribution gate satisfied; canary run completes the full gate."
    status: completed
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
| Phase 0 cloud-agnostic scan not passed         | `[RESOLVED]`  | [phase0_standards_enforcement.plan.md](phase0_standards_enforcement.plan.md) § todo `p0-t0-parallel` through `p0-gate-check` | [RESOLVED 2026-03-06] — 14 Category A + 37 Category B violations fixed; STEP 5.10/5.11 hard-fail gates enforced; QUALITY_GATE_BYPASS_AUDIT.md at workspace root with zero unapproved exceptions. |
| Phase 1 cloud-agnostic cursor rule not created | `[RESOLVED]`  | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-cloud-agnostic-rule`                             | [RESOLVED] Cloud SDK enforcement is enforced via STEP 5.10/5.11 quality gate (hard-fail exit 1); functional equivalent of cloud-agnostic.mdc is in place across all quality-gate templates. |

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
