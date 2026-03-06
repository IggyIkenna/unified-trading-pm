---
name: AWS Migration Plan
overview: Dual-cloud readiness for GCP primary and AWS secondary. Cloud-agnostic abstractions via unified-cloud-interface; migration phases for build path, runtime, and full dual-cloud deployment.
todos:
  - id: phase-1-cloud-agnostic
    content: "Verify cloud-agnostic abstractions; no direct google.cloud/boto3 in prod. SCOPE: all repos in workspace-manifest.json with type=library or type=service (not UIs). GATE: rg 'google\\.cloud|boto3' --type py --glob '!.venv*' --glob '!tests' returns 0 matches in production source across all in-scope repos; verified per-repo in QUALITY_GATE_BYPASS_AUDIT.md. DONE: 14 Category A + 37 Category B violations fixed (sessions 4–6); STEP 5.10/5.11 hard-fail gates active; QUALITY_GATE_BYPASS_AUDIT.md zero unapproved exceptions. Gate fully satisfied 2026-03-06."
    status: completed
  - id: phase-2-buildspec
    content: "buildspec.aws.yaml distributed to all 44 qualifying repos (8 newly created, 36 already present). FILE DISTRIBUTION DONE 2026-03-05. File distribution gate satisfied."
    status: completed
  - id: codebuild-canary-run
    content: |
      Validate that buildspec.aws.yaml files actually work in a simulated CodeBuild environment.
      All 44 repos have buildspec.aws.yaml files — none have been validated yet.

      Steps:
      (1) For 3 canary repos (instruments-service, unified-cloud-interface,
          unified-events-interface): run `act -j build --platform ubuntu-latest` against
          the buildspec.aws.yaml (using nektos/act or equivalent local simulation).
      (2) Confirm: install step installs uv + python 3.13; unit-test step runs pytest;
          quality-gate step runs quality-gates.sh; all exit 0.
      (3) Fix any discovered issues in buildspec.aws.yaml templates.
      (4) Document result in CLOUD_SDK_VIOLATIONS.md canary section.
      (5) Mark uci_cloud_abstraction_complete.plan.md p2-cloud-build-configs as completed.

      Gate: act simulation exits 0 for all 3 canary repos, no manual steps required.
    status: pending
  - id: aws-account-setup
    content: |
      AWS account and billing setup. Prerequisites for everything else.
      (1) AWS account created; billing ID attached; cost alerts configured.
      (2) IAM admin user + access keys for bootstrap only (rotated after OIDC live).
      (3) AWS CLI configured locally: `aws configure` with bootstrap credentials.
      (4) AWS_ACCOUNT_ID documented in deployment-service/configs/aws-account.env (gitignored).
      Gate: `aws sts get-caller-identity` exits 0; billing alert at $50/month active.
    status: pending
  - id: aws-team-access
    content: |
      Grant AWS console + CLI access to team members: Datadodo and Harsh.
      (1) Create IAM users for each: datadodo, harsh.
      (2) Attach policy: ReadOnlyAccess + specific write permissions for their scope
          (e.g. S3 read, ECR pull, CloudWatch logs — no billing, no IAM admin).
      (3) Generate access keys for each; share securely (not via git or Slack plaintext).
      (4) Add to relevant IAM groups (e.g. unified-trading-developers group).
      (5) Enable MFA for both accounts.
      (6) Document in deployment-service/configs/aws-team-access.md (names + roles, no keys).
      Gate: both users can `aws sts get-caller-identity` with their credentials.
    status: pending
  - id: github-aws-credentials
    content: |
      GitHub Actions can authenticate to AWS. Two options (OIDC preferred):
      OPTION A — OIDC (preferred, no static secrets):
        (1) Create IAM OIDC provider for token.actions.githubusercontent.com.
        (2) Create IAM role unified-trading-github-actions with trust policy for this repo org.
        (3) Grant role: ECR push, S3 read/write, Secrets Manager read, ECS deploy.
        (4) Add to all buildspec.aws.yaml: `aws sts assume-role-with-web-identity` step.
        (5) GitHub secret: AWS_ROLE_ARN (no static key needed).
      OPTION B — Static keys (fallback):
        (1) IAM user unified-trading-ci with minimal policy.
        (2) GitHub secrets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION.
      Gate: GitHub Actions workflow can call `aws sts get-caller-identity` with 0 exit.
    status: pending
  - id: ecr-setup
    content: |
      AWS ECR (Elastic Container Registry) — equivalent of GCP Artifact Registry.
      (1) Create ECR registry in primary AWS region (us-east-1 or eu-west-1).
      (2) Create per-service ECR repositories: one repo per service that builds a Docker image.
      (3) Add ECR lifecycle policy: keep last 10 images, expire untagged after 7 days.
      (4) Update buildspec.aws.yaml template: `aws ecr get-login-password | docker login`.
      (5) Update deployment-service/terraform/aws/ to include ECR resource definitions.
      (6) Document ECR registry URL in deployment-service/configs/aws-account.env.
      Gate: `aws ecr describe-repositories` lists all service repos; push/pull test passes.
    status: pending
  - id: terraform-aws-validate
    content: |
      Validate that deployment-service/terraform/aws/ actually works — files exist but have
      never been applied. This is the ground-truth test of the Terraform we assumed was correct.
      (1) Run `terraform init` in deployment-service/terraform/aws/.
      (2) Run `terraform plan` — review output for errors, missing variables, wrong region.
      (3) Fix any issues in the Terraform (S3 bucket names, IAM policies, ECS task defs).
      (4) Run `terraform apply` on a test workspace (not prod) — verify resources created.
      (5) Resources to confirm: S3 buckets (data + artifacts), Secrets Manager stubs,
          IAM roles (service roles + CI role), ECS cluster + task definition for instruments-service.
      (6) Run `terraform destroy` on test workspace after validation.
      Gate: `terraform plan` exits 0 with no errors; `terraform apply` creates expected resources.
    status: pending
  - id: uci-aws-storage-audit
    content: |
      Validate UCI storage (S3) works end-to-end with CLOUD_PROVIDER=aws.
      (1) CLOUD_PROVIDER=aws python -c 'from unified_cloud_interface import get_storage_client; c = get_storage_client(); c.upload_blob("test", b"hello")' exits 0.
      (2) S3 bucket naming: confirm {prefix}-{AWS_ACCOUNT_ID} pattern works in AWSStorageClient.
      (3) BlobMetadata, list_blobs, download_blob all tested against real S3 bucket.
      (4) instruments-service: run with CLOUD_PROVIDER=aws, confirm data reads/writes to S3.
      Gate: get_storage_client() round-trip (upload + download) passes with CLOUD_PROVIDER=aws.
    status: pending
  - id: uci-aws-secrets-audit
    content: |
      Validate UCI secrets (AWS Secrets Manager) works end-to-end.
      (1) Mirror all GCP Secret Manager secrets to AWS Secrets Manager (same names).
      (2) CLOUD_PROVIDER=aws python -c 'from unified_cloud_interface import get_secret_client; get_secret_client().get_secret("test-secret")' exits 0.
      (3) credentials-registry.yaml updated to document AWS secret names.
      (4) bootstrap_aws.sh creates secret stubs in Secrets Manager.
      Gate: get_secret_client().get_secret() resolves with CLOUD_PROVIDER=aws for all API keys.
    status: pending
  - id: uci-aws-messaging-audit
    content: |
      Validate UCI messaging (SQS/SNS) works end-to-end — PubSub equivalent.
      (1) Confirm AWSQueueClient in UCI uses SQS for point-to-point and SNS for pub/sub fan-out.
      (2) CLOUD_PROVIDER=aws python -c 'from unified_cloud_interface import get_queue_client; get_queue_client().publish("test-topic", {"event": "test"})' exits 0.
      (3) SQS queue names mirror GCP PubSub topic names (documented in runtime-topology.yaml).
      (4) Create SQS queues + SNS topics in deployment-service/terraform/aws/.
      (5) End-to-end: instruments-service publishes event → market-data-processing-service consumes.
      Gate: get_queue_client() publish + subscribe round-trip passes with CLOUD_PROVIDER=aws.
    status: pending
  - id: uci-aws-analytics-audit
    content: |
      Validate UCI analytics (Athena/Glue) works — BigQuery equivalent.
      (1) AWSAnalyticsClient in UCI uses Athena for queries, Glue for schema registry.
      (2) S3 data path structure matches what Athena external tables expect.
      (3) CLOUD_PROVIDER=aws python -c 'from unified_cloud_interface import get_analytics_client; get_analytics_client().query("SELECT 1")' exits 0.
      (4) Athena workgroup + Glue database created in terraform/aws/.
      Gate: get_analytics_client().query() executes with CLOUD_PROVIDER=aws; result matches GCP BigQuery output for same query.
    status: pending
  - id: image-build-ecr-push
    content: |
      Docker image build and ECR push working via CodeBuild.
      (1) Select 3 canary services with Dockerfiles: instruments-service, execution-service, ml-inference-service.
      (2) buildspec.aws.yaml build stage: docker build → tag → ecr push.
      (3) Run via `act` locally first (codebuild-canary-run gates this).
      (4) Then trigger real CodeBuild pipeline for canary services.
      (5) Confirm image is pullable from ECR: `docker pull {ecr_url}/instruments-service:latest`.
      Gate: ECR shows latest image tag for all 3 canary services after CodeBuild run.
    status: pending
  - id: phase-4-dual-cloud
    content: |
      Full dual-cloud deployment — GCP + AWS parity. Gate for going live on AWS.
      PARITY DEFINITION:
      (1) Same quality-gates.sh exit code on GCP (cloudbuild.yaml) and AWS (buildspec.aws.yaml) for all in-scope repos.
      (2) Same secret names in AWS Secrets Manager as GCP Secret Manager.
      (3) Same bucket structure in S3 as GCS (different names, same prefix + path pattern).
      (4) Same SQS queue names as GCP PubSub topic names (documented in runtime-topology.yaml).
      (5) CLOUD_PROVIDER switch changes only concrete adapters, zero business logic changes.
      (6) Pilot service (instruments-service) deployed on ECS/Batch, passes verify_bootstrap.py with CLOUD_PROVIDER=aws.
      Gate: instruments-service on AWS ECS: ingests data from S3, publishes to SQS, secrets from Secrets Manager, all Layer 2 infra checks pass.
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

| Blocker                                        | Type         | Specific Dependency                                                                                                          | Resolution                                                                                                                                                                                       |
| ---------------------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 0 cloud-agnostic scan not passed         | `[RESOLVED]` | [phase0_standards_enforcement.plan.md](phase0_standards_enforcement.plan.md) § todo `p0-t0-parallel` through `p0-gate-check` | [RESOLVED 2026-03-06] — 14 Category A + 37 Category B violations fixed; STEP 5.10/5.11 hard-fail gates enforced; QUALITY_GATE_BYPASS_AUDIT.md at workspace root with zero unapproved exceptions. |
| Phase 1 cloud-agnostic cursor rule not created | `[RESOLVED]` | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-cloud-agnostic-rule`                             | [RESOLVED] Cloud SDK enforcement is enforced via STEP 5.10/5.11 quality gate (hard-fail exit 1); functional equivalent of cloud-agnostic.mdc is in place across all quality-gate templates.      |

---

## Current State

- **CLOUD_PROVIDER** env var: `gcp | aws | local`
- **unified-cloud-interface:** StorageClient, SecretClient, QueueClient, AnalyticsClient, ComputeClient, CacheClient — all with GCP/AWS/Local providers (code exists, AWS providers untested against real AWS)
- **buildspec.aws.yaml** distributed to all 44 qualifying repos (never run against real CodeBuild)
- **Terraform AWS:** `deployment-service/terraform/aws/` exists — never applied
- **Secrets:** GCP Secret Manager live; AWS Secrets Manager — not provisioned
- **Storage:** GCS live; S3 — not provisioned
- **Messaging:** GCP PubSub live; SQS/SNS — not provisioned
- **ECR:** not set up (GCP Artifact Registry equivalent)
- **GitHub → AWS auth:** not configured (OIDC or static keys)

---

## Migration Phases

| Phase | Todo ID                   | Scope                                      | Gates                                     |
| ----- | ------------------------- | ------------------------------------------ | ----------------------------------------- |
| 0     | `aws-account-setup`       | AWS account, billing, IAM bootstrap        | `aws sts get-caller-identity` exits 0     |
| 0a    | `aws-team-access`         | IAM users for Datadodo + Harsh, MFA        | Both users authenticated                  |
| 0b    | `github-aws-credentials`  | GitHub Actions → AWS auth (OIDC preferred) | GH Actions can call AWS APIs              |
| 0c    | `ecr-setup`               | ECR registry + per-service repos           | Push/pull test passes                     |
| 1     | `phase-1-cloud-agnostic`  | No direct SDK in prod                      | ✅ DONE                                   |
| 2     | `phase-2-buildspec`       | buildspec.aws.yaml distributed             | ✅ DONE                                   |
| 2b    | `codebuild-canary-run`    | Canary `act` simulation for 3 repos        | act exits 0                               |
| 2c    | `image-build-ecr-push`    | Docker build + ECR push via CodeBuild      | ECR shows image                           |
| 3a    | `terraform-aws-validate`  | Terraform plan + apply on test workspace   | `terraform apply` succeeds                |
| 3b    | `uci-aws-storage-audit`   | S3 round-trip via UCI                      | get_storage_client() upload/download      |
| 3c    | `uci-aws-secrets-audit`   | Secrets Manager via UCI                    | get_secret_client() resolves all API keys |
| 3d    | `uci-aws-messaging-audit` | SQS/SNS via UCI                            | get_queue_client() pub/sub round-trip     |
| 3e    | `uci-aws-analytics-audit` | Athena/Glue via UCI                        | get_analytics_client() query executes     |
| 4     | `phase-4-dual-cloud`      | Full parity; pilot on ECS                  | instruments-service live on AWS           |
| 4b    | `per-service-checklist`   | All 44 repos audited                       | QUALITY_GATE_BYPASS_AUDIT.md complete     |

---

## Per-Service Checklist

1. All I/O via `get_storage_client()`, `get_secret_client()`, `get_queue_client()`
2. No hardcoded GCP project IDs, GCS bucket names, or PubSub topic names
3. `buildspec.aws.yaml` present and passing CodeBuild canary
4. Bucket/secret/queue naming documented in `credentials-registry.yaml`
5. Docker image builds and pushes to ECR successfully

---

## References

- unified-trading-codex/05-infrastructure/README.md
- unified-trading-codex/11-project-management/dual-cloud-cost-ops-playbook.md
- cursor-rules: cloud-agnostic.mdc
