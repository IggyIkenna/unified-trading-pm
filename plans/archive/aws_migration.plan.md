---
doc_type: plan
title: aws-migration
summary: Dual-cloud readiness for GCP primary and AWS secondary. Cloud-agnostic abstractions via unified-cloud-interface;
  migration phases for build path, runtime, and full dual-cloud deployment.
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-05"
type: deployment
epic: epic-deployment
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - {
      repo: unified-cloud-interface,
      code: C5,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: deployment-service,
      code: C1,
      deployment: D3,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: instruments-service,
      code: C5,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
depends_on: []
todos:
  - {
      id: phase-1-cloud-agnostic,
      content:
        'Verify cloud-agnostic abstractions; no direct google.cloud/boto3 in prod. SCOPE: all repos in
        workspace-manifest.json with type=library or type=service (not UIs). GATE: rg ''google\.cloud|boto3'' --type py
        --glob ''!.venv*'' --glob ''!tests'' returns 0 matches in production source across all in-scope repos; verified
        per-repo in QUALITY_GATE_BYPASS_AUDIT.md. DONE: 14 Category A + 37 Category B violations fixed (sessions 4–6);
        STEP 5.10/5.11 hard-fail gates active; QUALITY_GATE_BYPASS_AUDIT.md zero unapproved exceptions. Gate fully
        satisfied 2026-03-06.',
      status: completed,
    }
  - {
      id: phase-2-buildspec,
      content:
        "buildspec.aws.yaml distributed to all 66 qualifying repos (unified-trading-codex intentionally excluded —
        docs-only). Total workspace: 67 repos (confirmed 2026-03-12 via manifest + git scan; prior count of 44/63 was
        incorrect). 5 new buildspecs added 2026-03-12: batch-live-reconciliation-service, elysium-defi-system,
        deployment-ui (+ Dockerfile), unified-trading-ui-kit. All 66 validated via validate-buildspec.py. FILE
        DISTRIBUTION DONE 2026-03-12. Canary simulated CodeBuild run for 3 repos (instruments-service,
        unified-cloud-interface, unified-events-interface) still pending — tracked in codebuild-canary-run below.",
      status: completed,
    }
  - {
      id: codebuild-canary-run,
      content:
        "Validate that buildspec.aws.yaml files actually work in a simulated CodeBuild environment.\nAll 66 repos have
        buildspec.aws.yaml files (67 total workspace; unified-trading-codex excluded).\n\nSteps:\n(1) For 3 canary repos
        (instruments-service, unified-cloud-interface,\n    unified-events-interface): run `act -j build --platform
        ubuntu-latest` against\n    the buildspec.aws.yaml (using nektos/act or equivalent local simulation).\n(2)
        Confirm: install step installs uv + python 3.13; unit-test step runs pytest;\n    quality-gate step runs
        quality-gates.sh; all exit 0.\n(3) Fix any discovered issues in buildspec.aws.yaml templates.\n(4) Document
        result in CLOUD_SDK_VIOLATIONS.md canary section.\n(5) Mark uci_cloud_abstraction_complete.plan.md
        p2-cloud-build-configs as completed.\n\nGate: act simulation exits 0 for all 3 canary repos, no manual steps
        required.\n",
      status: pending,
    }
  - { id: aws-account-setup, content: "AWS account and billing setup. Prerequisites for everything else.

        (1) AWS account created; billing ID attached; cost alerts configured.

        (2) IAM admin user + access keys for bootstrap only (rotated after OIDC live).

        (3) AWS CLI configured locally: `aws configure` with bootstrap credentials.

        (4) AWS_ACCOUNT_ID documented in deployment-service/configs/aws-account.env (gitignored).

        Gate: `aws sts get-caller-identity` exits 0; billing alert at $50/month active.

        ", status: pending }
  - {
      id: aws-team-access,
      content:
        "Grant AWS console + CLI access to team members: Datadodo and Harsh.\n(1) Create IAM users for each: datadodo,
        harsh.\n(2) Attach policy: ReadOnlyAccess + specific write permissions for their scope\n    (e.g. S3 read, ECR
        pull, CloudWatch logs — no billing, no IAM admin).\n(3) Generate access keys for each; share securely (not via
        git or Slack plaintext).\n(4) Add to relevant IAM groups (e.g. unified-trading-developers group).\n(5) Enable
        MFA for both accounts.\n(6) Document in deployment-service/configs/aws-team-access.md (names + roles, no
        keys).\nGate: both users can `aws sts get-caller-identity` with their credentials.\n",
      status: pending,
    }
  - {
      id: github-aws-credentials,
      content:
        "GitHub Actions can authenticate to AWS. Two options (OIDC preferred):\nOPTION A — OIDC (preferred, no static
        secrets):\n  (1) Create IAM OIDC provider for token.actions.githubusercontent.com.\n  (2) Create IAM role
        unified-trading-github-actions with trust policy for this repo org.\n  (3) Grant role: ECR push, S3 read/write,
        Secrets Manager read, ECS deploy.\n  (4) Add to all buildspec.aws.yaml: `aws sts assume-role-with-web-identity`
        step.\n  (5) GitHub secret: AWS_ROLE_ARN (no static key needed).\nOPTION B — Static keys (fallback):\n  (1) IAM
        user unified-trading-ci with minimal policy.\n  (2) GitHub secrets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
        AWS_DEFAULT_REGION.\nGate: GitHub Actions workflow can call `aws sts get-caller-identity` with 0 exit.\n",
      status: pending,
    }
  - {
      id: aws-region-selection,
      content:
        "Confirm primary AWS region for latency-sensitive trading workloads.\nBinance matching engine is in Tokyo.
        Closest AWS region: ap-northeast-1 (Tokyo).\nGCP equivalent: asia-northeast1 (Tokyo) — confirm this is where GCP
        workloads currently run.\n(1) Verify Binance WebSocket + REST API latency from ap-northeast-1 vs
        candidates\n    (ap-southeast-1 Singapore, us-east-1). Target: <5ms to Binance order submission endpoint.\n(2)
        Set ap-northeast-1 as AWS_DEFAULT_REGION in deployment-service/configs/aws-account.env.\n(3) Update all
        Terraform aws/ configs to use ap-northeast-1 as default region.\n(4) Secondary region for DR: ap-southeast-1
        (Singapore) — S3 cross-region replication.\n(5) Document region decision in
        deployment-service/configs/REGION-STRATEGY.md.\nGate: latency test confirms ap-northeast-1 to Binance API is <=
        GCP asia-northeast1 latency.\n",
      status: pending,
    }
  - { id: aws-service-roles, content: "IAM roles for compute (ECS tasks, EC2 instances) — equivalent of GCP service
        accounts.\nGCP service accounts attach to Cloud Run/VM instances and grant scoped access.\nAWS equivalent: IAM
        roles with instance profiles (EC2) or task execution roles (ECS).\n(1) Create per-service IAM execution roles,
        e.g.:\n    - unified-trading-instruments-service-role: S3 read, Secrets Manager read, SQS publish\n    -
        unified-trading-execution-service-role: S3 read/write, Secrets Manager read, SQS pub/consume\n    -
        unified-trading-ml-inference-role: S3 read (models), Secrets Manager read, SQS consume\n(2) Principle of least
        privilege: each role only gets what its service actually calls.\n(3) Create ECS task execution role (separate):
        ECR pull, CloudWatch Logs write.\n(4) Add all roles to deployment-service/terraform/aws/iam.tf.\n(5) Bind roles
        in ECS task definitions (taskRoleArn + executionRoleArn).\nGate: ECS task for instruments-service starts with
        scoped role; `aws\
        \ iam simulate-principal-policy` passes for all expected actions.\n", status: pending }
  - { id: aws-quota-review, content: "Review and request AWS quota increases before go-live. Default quotas are often
        lower than GCP.

        (1) ECS: running tasks per cluster (default 1000 — verify sufficient for full deployment).

        (2) EC2: vCPU on-demand limits per region for instance types (t3/c5/m5).

        (3) SQS: messages/s per queue (3000/s standard, 300/s FIFO — verify execution order flow needs).

        (4) ECR: image push rate (default 10 TPS — may need increase for 44-repo CI).

        (5) CodeBuild: concurrent builds (default 60 — sufficient).

        (6) Secrets Manager: API request rate (10k TPS — fine).

        Submit quota increase requests BEFORE terraform apply (approvals take 24-48h).

        Gate: all quotas confirmed or increases approved before phase 4 go-live.

        ", status: pending }
  - { id: ecr-setup, content: "AWS ECR (Elastic Container Registry) — equivalent of GCP Artifact Registry.

        (1) Create ECR registry in ap-northeast-1 (Tokyo — primary region).

        (2) Create per-service ECR repositories: one repo per service that builds a Docker image.

        (3) Add ECR lifecycle policy: keep last 10 images, expire untagged after 7 days.

        (4) Update buildspec.aws.yaml template: `aws ecr get-login-password | docker login`.

        (5) Update deployment-service/terraform/aws/ to include ECR resource definitions.

        (6) Document ECR registry URL in deployment-service/configs/aws-account.env.

        Gate: `aws ecr describe-repositories` lists all service repos; push/pull test passes.

        ", status: pending }
  - {
      id: terraform-aws-validate,
      content:
        "Validate that deployment-service/terraform/aws/ actually works — files exist but have\nnever been applied. This
        is the ground-truth test of the Terraform we assumed was correct.\n(1) Run `terraform init` in
        deployment-service/terraform/aws/.\n(2) Run `terraform plan` — review output for errors, missing variables,
        wrong region.\n(3) Fix any issues in the Terraform (S3 bucket names, IAM policies, ECS task defs).\n(4) Run
        `terraform apply` on a test workspace (not prod) — verify resources created.\n(5) Resources to confirm: S3
        buckets (data + artifacts), Secrets Manager stubs,\n    IAM roles (service roles + CI role), ECS cluster + task
        definition for instruments-service.\n(6) Run `terraform destroy` on test workspace after validation.\nGate:
        `terraform plan` exits 0 with no errors; `terraform apply` creates expected resources.\n",
      status: pending,
    }
  - { id: uci-aws-storage-audit, content: 'Validate UCI storage (S3) works end-to-end with CLOUD_PROVIDER=aws.

        (1) CLOUD_PROVIDER=aws python -c ''from unified_cloud_interface import get_storage_client; c =
        get_storage_client(); c.upload_blob("test", b"hello")'' exits 0.

        (2) S3 bucket naming: confirm {prefix}-{AWS_ACCOUNT_ID} pattern works in AWSStorageClient.

        (3) BlobMetadata, list_blobs, download_blob all tested against real S3 bucket.

        (4) instruments-service: run with CLOUD_PROVIDER=aws, confirm data reads/writes to S3.

        Gate: get_storage_client() round-trip (upload + download) passes with CLOUD_PROVIDER=aws.

        ', status: pending }
  - { id: uci-aws-secrets-audit, content: 'Validate UCI secrets (AWS Secrets Manager) works end-to-end.

        (1) Mirror all GCP Secret Manager secrets to AWS Secrets Manager (same names).

        (2) CLOUD_PROVIDER=aws python -c ''from unified_cloud_interface import get_secret_client;
        get_secret_client().get_secret("test-secret")'' exits 0.

        (3) credentials-registry.yaml updated to document AWS secret names.

        (4) bootstrap_aws.sh creates secret stubs in Secrets Manager.

        Gate: get_secret_client().get_secret() resolves with CLOUD_PROVIDER=aws for all API keys.

        ', status: pending }
  - { id: uci-aws-messaging-audit, content: 'Validate UCI messaging (SQS/SNS) works end-to-end — PubSub equivalent.

        (1) Confirm AWSQueueClient in UCI uses SQS for point-to-point and SNS for pub/sub fan-out.

        (2) CLOUD_PROVIDER=aws python -c ''from unified_cloud_interface import get_queue_client;
        get_queue_client().publish("test-topic", {"event": "test"})'' exits 0.

        (3) SQS queue names mirror GCP PubSub topic names (documented in runtime-topology.yaml).

        (4) Create SQS queues + SNS topics in deployment-service/terraform/aws/.

        (5) End-to-end: instruments-service publishes event → market-data-processing-service consumes.

        Gate: get_queue_client() publish + subscribe round-trip passes with CLOUD_PROVIDER=aws.

        ', status: pending }
  - { id: uci-aws-analytics-audit, content: 'Validate UCI analytics (Athena/Glue) works — BigQuery equivalent.

        (1) AWSAnalyticsClient in UCI uses Athena for queries, Glue for schema registry.

        (2) S3 data path structure matches what Athena external tables expect.

        (3) CLOUD_PROVIDER=aws python -c ''from unified_cloud_interface import get_analytics_client;
        get_analytics_client().query("SELECT 1")'' exits 0.

        (4) Athena workgroup + Glue database created in terraform/aws/.

        Gate: get_analytics_client().query() executes with CLOUD_PROVIDER=aws; result matches GCP BigQuery output for
        same query.

        ', status: pending }
  - { id: image-build-ecr-push, content: "Docker image build and ECR push working via CodeBuild.

        (1) Select 3 canary services with Dockerfiles: instruments-service, execution-service, ml-inference-service.

        (2) buildspec.aws.yaml build stage: docker build → tag → ecr push.

        (3) Run via `act` locally first (codebuild-canary-run gates this).

        (4) Then trigger real CodeBuild pipeline for canary services.

        (5) Confirm image is pullable from ECR: `docker pull {ecr_url}/instruments-service:latest`.

        Gate: ECR shows latest image tag for all 3 canary services after CodeBuild run.

        ", status: pending }
  - {
      id: phase-4-dual-cloud,
      content:
        "Full dual-cloud deployment — GCP + AWS parity. PARITY DEFINITION: (1) same quality-gates.sh exit code on GCP
        (cloudbuild.yaml) and AWS (buildspec.aws.yaml) for all in-scope repos; (2) same secret names mirrored in AWS
        Secrets Manager as in GCP Secret Manager; (3) same bucket structure in S3 as in GCS (different names, same
        prefix pattern); (4) CLOUD_PROVIDER switch changes only the concrete adapter, not business logic. GATE: pilot
        deployment of at least one service (instruments-service) on AWS ECS/Batch passes Layer 2 infra verification
        (verify_infra.py with CLOUD_PROVIDER=aws).",
      status: pending,
    }
  - {
      id: per-service-checklist,
      content:
        "Per-service checklist — I/O via get_storage_client/get_secret_client; no hardcoded IDs. GATE: each service repo
        has a completed QUALITY_GATE_BYPASS_AUDIT.md section for AWS migration listing: (1) all
        get_storage_client/get_secret_client calls confirmed; (2) no hardcoded GCP project IDs or bucket names in
        production source; (3) buildspec.aws.yaml present; (4) secret names documented in credentials-registry.yaml.",
      status: pending,
    }
  - {
      id: aws-s3-bucket-setup,
      content:
        "Run setup-buckets.py --cloud aws --include-test --dry-run first, then --create to provision S3 buckets per
        aws_bucket_mappings in bucket_config.yaml. AWS equivalent buckets use account_id instead of project_id. Script
        already written and tested (deployment-service). Runs after aws-account-setup completes. Gate: setup-buckets.py
        --cloud aws --dry-run exits 0; all bucket names listed match bucket_config.yaml aws_bucket_mappings; SIT
        test_aws_s3_smoke.py passes with AWS creds.",
      status: pending,
      notes: Migrated from cloud_infra_bucket_auth_2026_03_10.plan.md todo aws-bucket-setup (archived 2026-03-11).,
    }
  - {
      id: aws-billing-alerts,
      content:
        "Run setup-billing-alerts.sh --cloud aws to create AWS Budgets entry and CloudWatch billing alarm. Script
        already written (deployment-service/scripts/setup-billing-alerts.sh --cloud aws section). Equivalent to GCP
        unified-trading-monthly-budget ($500/month) + unified-trading-dev-budget ($50). Thresholds: 50%/80%/100%/120%.
        Alerts → SNS → alerting-service → Telegram. Gate: aws budgets describe-budgets lists both budgets; CloudWatch
        billing alarm ALARM triggers below threshold.",
      status: pending,
      notes:
        Migrated from cloud_infra_extended_bootstrap_2026_03_10.plan.md todo billing-alerts-aws (archived 2026-03-11).,
    }
isProject: false
---

# AWS Migration Plan (Dual-Cloud Readiness)

**Order:** See master_pre_deployment_plan_chain.plan.md **Reference:** dual-cloud-cost-ops-playbook.md,
05-infrastructure/README.md, cloud-agnostic.mdc **Status:** GCP primary; AWS secondary [PLANNED]

---

## Blockers

| Blocker                                        | Type         | Specific Dependency                                                                                                          | Resolution                                                                                                                                                                                       |
| ---------------------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 0 cloud-agnostic scan not passed         | `[RESOLVED]` | [phase0_standards_enforcement.plan.md](phase0_standards_enforcement.plan.md) § todo `p0-t0-parallel` through `p0-gate-check` | [RESOLVED 2026-03-06] — 14 Category A + 37 Category B violations fixed; STEP 5.10/5.11 hard-fail gates enforced; QUALITY_GATE_BYPASS_AUDIT.md at workspace root with zero unapproved exceptions. |
| Phase 1 cloud-agnostic cursor rule not created | `[RESOLVED]` | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-cloud-agnostic-rule`                             | [RESOLVED] Cloud SDK enforcement is enforced via STEP 5.10/5.11 quality gate (hard-fail exit 1); functional equivalent of cloud-agnostic.mdc is in place across all quality-gate templates.      |

---

## Current State

- **CLOUD_PROVIDER** env var: gcp | aws
- **unified-cloud-interface:** StorageClient, SecretClient, QueueClient with GCP/AWS/Local providers
- **buildspec.aws.yaml** present in many repos (CodeBuild)
- **Secrets:** GCP Secret Manager primary; AWS Secrets Manager secondary
- **Storage:** GCS primary; S3 secondary (bucket naming: `{prefix}-${AWS_ACCOUNT_ID}`)

---

## Migration Phases

| Phase | Todo ID                   | Scope                                              | Gates                                     |
| ----- | ------------------------- | -------------------------------------------------- | ----------------------------------------- |
| 0     | `aws-account-setup`       | AWS account, billing, IAM bootstrap                | `aws sts get-caller-identity` exits 0     |
| 0a    | `aws-region-selection`    | Confirm Tokyo (ap-northeast-1) for Binance latency | Latency test <= GCP asia-northeast1       |
| 0b    | `aws-team-access`         | IAM users for Datadodo + Harsh, MFA                | Both users authenticated                  |
| 0c    | `aws-service-roles`       | Per-service IAM roles (ECS task + execution roles) | `simulate-principal-policy` passes        |
| 0d    | `aws-quota-review`        | Request quota increases before go-live             | All quotas confirmed/approved             |
| 0e    | `github-aws-credentials`  | GitHub Actions → AWS auth (OIDC preferred)         | GH Actions can call AWS APIs              |
| 0f    | `ecr-setup`               | ECR registry in ap-northeast-1 + per-service repos | Push/pull test passes                     |
| 1     | `phase-1-cloud-agnostic`  | No direct SDK in prod                              | ✅ DONE                                   |
| 2     | `phase-2-buildspec`       | buildspec.aws.yaml distributed                     | ✅ DONE                                   |
| 2b    | `codebuild-canary-run`    | Canary `act` simulation for 3 repos                | act exits 0                               |
| 2c    | `image-build-ecr-push`    | Docker build + ECR push via CodeBuild              | ECR shows image                           |
| 3a    | `terraform-aws-validate`  | Terraform plan + apply on test workspace           | `terraform apply` succeeds                |
| 3b    | `uci-aws-storage-audit`   | S3 round-trip via UCI                              | get_storage_client() upload/download      |
| 3c    | `uci-aws-secrets-audit`   | Secrets Manager via UCI                            | get_secret_client() resolves all API keys |
| 3d    | `uci-aws-messaging-audit` | SQS/SNS via UCI                                    | get_queue_client() pub/sub round-trip     |
| 3e    | `uci-aws-analytics-audit` | Athena/Glue via UCI                                | get_analytics_client() query executes     |
| 4     | `phase-4-dual-cloud`      | Full parity; pilot on ECS                          | instruments-service live on AWS           |
| 4b    | `per-service-checklist`   | All 44 repos audited                               | QUALITY_GATE_BYPASS_AUDIT.md complete     |

---

## Per-Service Checklist

1. All I/O via get_storage_client(), get_secret_client()
2. No hardcoded project/account IDs
3. buildspec.aws.yaml present and passing
4. Bucket/secret naming follows cloud-agnostic pattern

---

## References

- unified-trading-/codex/05-infrastructure/README.md
- unified-trading-/codex/11-project-management/dual-cloud-cost-ops-playbook.md
- cursor-rules: cloud-agnostic.mdc

---

## GCP → AWS Equivalence Matrix (added 2026-03-10)

Complete mapping of every GCP service used to its AWS equivalent, with specific operational steps required per phase.
This ensures no GCP capability is missed when running CLOUD_PROVIDER=aws.

| GCP Service                | AWS Equivalent        | Phase | Specific Ops Required                                                                                              |
| -------------------------- | --------------------- | ----- | ------------------------------------------------------------------------------------------------------------------ |
| Cloud Run                  | ECS Fargate           | 0c/3a | Task definition per service (CPU/mem from table below), ECS service + ALB, auto-scaling policy                     |
| GCS                        | S3                    | 0/3b  | Bucket per GCS bucket (same naming convention), bucket policy matching GCS IAM, versioning on, lifecycle rules     |
| Pub/Sub                    | SQS + SNS             | 3d    | Queue per Pub/Sub subscription, SNS topic per Pub/Sub topic, DLQs with 3-retry policy, 7-day retention             |
| BigQuery                   | Athena + S3 + Glue    | 3e    | S3 bucket for raw data, Glue database + table schemas, Athena workgroup, partition scheme matching BQ              |
| Cloud Build                | CodeBuild             | 2b/2c | buildspec.aws.yaml (already distributed), CodeBuild project per repo, OIDC role, ECR pull permission               |
| Secret Manager             | AWS Secrets Manager   | 3c    | Secret per GCP secret (same names), rotation config, resource policy per service role                              |
| Cloud Scheduler            | EventBridge           | 3a    | EventBridge rule per Cloud Scheduler job, target = ECS task run or Lambda                                          |
| Artifact Registry          | ECR                   | 0f    | Repository per service, image scanning enabled, lifecycle: keep last 10                                            |
| Cloud IAM (SA per service) | IAM role per ECS task | 0c    | ECS task execution role + task role per service, OIDC federation for GHA                                           |
| Cloud Logging              | CloudWatch Logs       | 3a    | Log group per service (`/unified-trading/{service}`), metric filters for ERROR/CRITICAL, 30d retention             |
| Cloud Monitoring           | CloudWatch Metrics    | 3a    | Dashboard per service, alarms: CPU>80%, memory>80%, error_rate>1%                                                  |
| Cloud Run jobs (batch)     | ECS task runs         | 3a    | One-off task execution via `aws ecs run-task` for batch jobs                                                       |
| VPC (auto)                 | VPC + subnets         | 0     | VPC with private subnets (one per AZ in ap-northeast-1 + ap-southeast-1), NAT gateway, security groups per service |
| Cloud DNS                  | Route 53              | 4     | Hosted zone, A/ALIAS records for each service endpoint                                                             |
| Memorystore Redis          | ElastiCache Redis     | 3a    | Redis cluster per env (dev/staging/prod), security group access only from service SGs                              |
| Cloud SQL                  | RDS Postgres          | 3a    | Required for Grafana state if deploying Grafana to AWS                                                             |

### ECS Task Resource Sizes (per service tier)

| Service Tier                   | CPU (vCPU) | Memory   | Notes                      |
| ------------------------------ | ---------- | -------- | -------------------------- |
| T0–T2 libraries (no runtime)   | N/A        | N/A      | Library only, no container |
| Data services (MTDH, MDPS)     | 0.5        | 2048 MB  | I/O bound                  |
| Feature services (all 8)       | 0.5        | 1536 MB  | Compute + GCS reads        |
| ML inference                   | 1.0        | 4096 MB  | Model loading + inference  |
| ML training                    | 4.0        | 16384 MB | Fargate Spot recommended   |
| Strategy service               | 0.5        | 1024 MB  | Signal generation          |
| Execution service              | 0.5        | 2048 MB  | Order management           |
| Monitoring services (PBS, PNL) | 0.25       | 512 MB   | Lightweight                |

### S3 Bucket creation requirements (Phase 3b)

File to create: `unified-trading-pm/scripts/aws/setup-s3-buckets.sh`

Required S3 buckets (mirroring GCS):

- `unified-trading-{env}-tick-data` → GCS: `unified-trading-{env}-tick-data`
- `unified-trading-{env}-features` → GCS: `unified-trading-{env}-features`
- `unified-trading-{env}-models` → GCS: `unified-trading-{env}-models`
- `unified-trading-{env}-instruments` → GCS: `unified-trading-{env}-instruments`
- `unified-trading-{env}-artifacts` → GCS: `unified-trading-{env}-artifacts`

All buckets: versioning ON, SSE-S3 encryption, public access blocked, lifecycle: archive to Glacier after 90 days.

### SQS/SNS topic requirements (Phase 3d)

File to create: `unified-trading-pm/scripts/aws/setup-sqs-sns.sh`

Creates SQS queues + SNS topics for every Pub/Sub topic in `runtime-topology.yaml`. Dead-letter queues: 3 retry
attempts, then DLQ with 14-day retention. FIFO queues for execution service (order preservation required).

### CloudWatch Alarms (Phase 3a — add to Terraform)

Per service:

- `{service}-cpu-high`: CPU utilization >80% for 5 minutes → SNS alert
- `{service}-memory-high`: memory utilization >80% for 5 minutes → SNS alert
- `{service}-error-rate`: >1% error rate on ALB target group → SNS alert
- `{service}-task-stopped`: ECS task stopped unexpectedly → SNS alert (immediate)
