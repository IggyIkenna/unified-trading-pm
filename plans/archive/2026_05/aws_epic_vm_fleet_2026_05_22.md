---
doc_type: plan
title: AWS epic VM fleet — CLOUD_PROVIDER toggle + AWS-preferred default
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: []
related: [epic_vm_fleet_commissioning_2026_05_21.md (archived)]
created: "2026-05-22"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
---

# AWS Epic VM Fleet — CLOUD_PROVIDER Toggle

GCP fleet is live (10 VMs, all healthy). Now add AWS EC2 as the **default** cloud provider for the orchestrator epic VM
fleet. AWS is preferred because we have existing credits there. GCP path must remain fully functional — toggle, not
replace.

**Current state**: `bootstrap_vm.sh` is GCP-only (uses `gcloud secrets`, `gcloud storage`). `launch-epic-vm.sh` is
GCP-only (`gcloud compute instances create`). AWS lib already exists (`lib/aws_ec2_launch_lib.sh`, `launch-ec2-vm.sh`,
`vm_zombie_watchdog_aws.py`).

**Target**: `CLOUD_PROVIDER=aws` (default) | `CLOUD_PROVIDER=gcp` (kept working). Single toggle drives both the launcher
and bootstrap. Same VM registry (`orchestrator_vm_registry.yaml`), same `bootstrap_vm.sh`, same `orchestrator.service` —
only the cloud-specific calls branch.

Codex SSOTs:

- `/codex/05-infrastructure/agent-orchestrator-worker-topology.md` — update Cloud provider toggle section when done
- `/codex/05-infrastructure/vm-tarball-deployment.md` — no changes needed (trading VMs only)

---

## Phase 1 — bootstrap_vm.sh: add CLOUD_PROVIDER toggle

All cloud-specific calls in `bootstrap_vm.sh` must branch on `$CLOUD_PROVIDER`. GCP remains the fallback.

- [x] ✅ [AGENT] P0. Add `--cloud-provider aws|gcp` arg to `bootstrap_vm.sh` (default `gcp` while GCP fleet is live;
      flips to `aws` once AWS fleet verified). Env var `CLOUD_PROVIDER` also respected as override. agent-orch@6591afb.
- [x] ✅ [AGENT] P0. Branch GH_PAT fetch: GCP → `gcloud secrets versions access latest --secret=GH_PAT`; AWS →
      `aws secretsmanager get-secret-value --secret-id GH_PAT --query SecretString --output text`. agent-orch@6591afb.
- [x] ✅ [AGENT] P0. Branch ORCHESTRATOR_ENV_LOCAL fetch: GCP →
      `gcloud secrets versions access latest --secret=ORCHESTRATOR_ENV_LOCAL`; AWS →
      `aws secretsmanager get-secret-value --secret-id ORCHESTRATOR_ENV_LOCAL --query SecretString --output text`.
      agent-orch@6591afb.
- [x] ✅ [AGENT] P0. Branch accounts.json + backlog.yaml fetch: GCP → `gcloud storage cp gs://.../config/...`; AWS →
      `aws s3 cp s3://uts-orchestrator-creds-{account}/config/... .` (bucket name TBD — see Phase 2).
      agent-orch@6591afb.
- [x] ✅ [AGENT] P0. Branch STARTED event emit: GCP → `gcloud storage cp - gs://.../STARTED`; AWS →
      `aws s3 cp - s3://uts-orchestrator-events-{account}/orchestrator/epic/{vm-name}/STARTED`. agent-orch@6591afb.
- [x] ✅ [AGENT] P0. VM_NAME detection: GCP → `curl -H 'Metadata-Flavor: Google' metadata.google.internal/...`; AWS →
      IMDSv2 token + `curl -H "X-aws-ec2-metadata-token: $TOKEN" 169.254.169.254/latest/meta-data/tags/instance/Name`.
      agent-orch@6591afb.
- [x] ✅ [AGENT] P1. Update PUBLIC_URL env var: GCP uses external IP from metadata; AWS uses public hostname from
      `169.254.169.254/latest/meta-data/public-hostname`. agent-orch@6591afb.
- [x] ✅ [AGENT] P1. Verify `su - ubuntu` pattern works on Ubuntu 24.04 on EC2 (AWS AMI uses same ubuntu user; uv HOME
      fix should carry over unchanged). Verified: vm-defi console log shows deps installed to /home/ubuntu correctly,
      orchestrator service started, health=ok. agent-orch@ff0d5ff.

## Phase 2 — AWS resource prerequisites

IAM role, S3 buckets, Secrets Manager secrets, and security group must exist before launching fleet.

- [x] ✅ [OPERATOR] P0. Create IAM instance profile `uts-orchestrator-epic` with permissions:
      `secretsmanager:GetSecretValue` (secrets: `GH_PAT`, `ORCHESTRATOR_ENV_LOCAL`), `s3:GetObject` (bucket:
      `uts-orchestrator-creds-{account}/config/*`), `s3:PutObject` (bucket:
      `uts-orchestrator-events-{account}/orchestrator/*`). Role `uts-orchestrator-epic-role`, policy
      `uts-orchestrator-epic-policy`, profile `uts-orchestrator-epic` created in account 427895769566.
- [x] ✅ [OPERATOR] P0. Create S3 buckets (ap-northeast-1, account `427895769566`):
      `uts-orchestrator-creds-427895769566` (private, versioned) + `uts-orchestrator-events-427895769566` (private,
      90-day lifecycle). Both created.
- [x] ✅ [OPERATOR] P0. Upload GH_PAT + ORCHESTRATOR_ENV_LOCAL to AWS Secrets Manager (`ap-northeast-1`, account
      `427895769566`) — same values as GCP Secret Manager. Both secrets present in ap-northeast-1.
- [x] ✅ [OPERATOR] P0. Upload `accounts.json` + `backlog.yaml` to `s3://uts-orchestrator-creds-427895769566/config/`.
      Both files uploaded from GCS; confirmed by vm-defi bootstrap log showing successful S3 fetches.
- [x] ✅ [OPERATOR] P0. Create/confirm security group `uts-orchestrator-epic-sg` in ap-northeast-1: inbound tcp:22
      (operator IPs), tcp:8026 (operator IPs); outbound all. sg-0080310387e84f613 in vpc-6ee70e08.
- [x] ✅ [OPERATOR] P0. Identify subnet IDs in ap-northeast-1a/b/c for `AWS_SUBNET_ID`. subnet-852f84cd (1a),
      subnet-fc09eca6 (1c), subnet-5c16a477 (1d). Using 1c (subnet-fc09eca6) for fleet.

## Phase 3 — launch-epic-vm-aws.sh

New launcher: AWS EC2 equivalent of `launch-epic-vm.sh`. Reads same `orchestrator_vm_registry.yaml`.

- [x] ✅ [AGENT] P0. Create `deployment-service/scripts/vm/launch-epic-vm-aws.sh`: same flags as GCP launcher; uses
      `lib/aws_ec2_launch_lib.sh`; m7i.xlarge in ap-northeast-1; instance profile `uts-orchestrator-epic`; user-data
      fetches GH_PAT from Secrets Manager + runs `bootstrap_vm.sh --cloud-provider aws`; same VM naming convention.
      Added 10 `agent-orch-` prefixes to `vm_zombie_watchdog_aws.py` VM_PREFIX_TO_BUCKET. deployment-service@9caa5e7.
- [x] ✅ [AGENT] P0. Create `deployment-service/scripts/aws/setup-orchestrator-iam.sh` — idempotent IAM setup (role +
      policy + instance profile). deployment-service@9caa5e7.
- [x] ✅ [AGENT] P1. `CLOUD_PROVIDER=aws` set in user-data env AND passed as explicit `--cloud-provider aws` arg to
      bootstrap_vm.sh — both paths covered. deployment-service@9caa5e7.

## Phase 4 — Single-VM smoke test

Launch one VM (vm-defi), verify bootstrap completes, health endpoint responds, STARTED event in S3.

- [x] ✅ [AGENT] P0. Launch `vm-defi` on AWS: `bash launch-epic-vm-aws.sh --vm-id vm-defi`. PASSED. Instance
      i-05805eb07fdf180b6 (agent-orch-vm-defi-20260522), public IP 43.207.178.164, state=running. Health:
      `{"status":"ok","service":"agent-orchestrator","version":"0.6.0"}` at attempt 2 (~90s after launch). S3 STARTED:
      `s3://uts-orchestrator-events-427895769566/orchestrator/epic/agent-orch-vm-defi-20260522/STARTED` (104 bytes,
      2026-05-22 00:13:47 UTC).
- [x] ✅ [AGENT] P0. Smoke passed — no failure path needed. Console log confirmed clean bootstrap: deps OK, creds OK,
      service started, health=ok, STARTED emitted. deployment-service@6d1b94d (tag-spec fix) applied.
- [x] ✅ [AGENT] P1. `bootstrap_vm.sh` default `CLOUD_PROVIDER` flipped from `gcp` to `aws`. agent-orch@ff0d5ff.

## Phase 5 — Full fleet launch on AWS + GCP decommission

- [x] ✅ [AGENT] P0. `bash launch-epic-vm-aws.sh --all` — all 10 epic VMs on AWS. T+10min: all 10 health=ok + all 10 S3
      STARTED events confirmed. deployment-service@03ec7a2. vm-defi 43.207.178.164 STARTED 01:13:47 | vm-cefi
      43.207.36.161 STARTED 01:22:50 | vm-tradfi 18.181.221.162 STARTED 01:22:56 | vm-sports 13.115.221.87 STARTED
      01:22:57 | vm-prediction 43.207.224.187 STARTED 01:23:11 | vm-ml 13.114.121.99 STARTED 01:23:17 | vm-trading-core
      54.238.66.156 STARTED 01:23:22 | vm-operator-ops 18.183.155.33 STARTED 01:23:32 | vm-cross-cutting 13.158.82.128
      STARTED 01:23:41 | vm-orchestrator 52.193.229.193 STARTED 01:23:44.
- [x] ✅ [AGENT] P1. Terminate GCP fleet. Operator directed early decommission (no 24h wait) to avoid cost. All 9 epic
      VMs deleted: agent-orch-vm-{cefi,cross-cutting,defi,ml,operator-ops,orchestrator,prediction,sports,
      tradfi,trading-core}-20260521 in asia-northeast1-c. Planning VM 34.146.53.106 kept live.
- [x] ✅ [AGENT] P1. Updated `orchestrator_vm_registry.yaml` with AWS instance IDs + public IPs. pm@e2efe990e.
- [x] ✅ [AGENT] P1. Updated `/codex/05-infrastructure/agent-orchestrator-worker-topology.md` — AWS fleet table, cloud
      toggle section, bootstrap steps, event bus with both S3 + GCS paths, re-launch commands. pm@8ca18cfba. Also
      updated `data/config/backends.json` in agent-orchestrator with all 10 AWS VMs so Fleet tab shows them.
      agent-orch@79e5d23.
- [x] ✅ [AGENT] P2. `setup-orchestrator-iam.sh --dry-run` on CI — prevents IAM drift on future launches.
      deployment-service@9db6221.

## Deferred (post-cutover)

- **GCP re-enable**: `CLOUD_PROVIDER=gcp bash launch-epic-vm.sh --all` should always work. Do not remove GCP path.
- **DNS**: point `api-<vm>.agent-orchestrator.odum-research.com` to AWS EIPs or ALB.
- **EIP allocation**: currently using dynamic public IPs; stable EIPs needed for DNS. backends.json needs manual update
  on re-launch until EIPs are allocated.
- **AWS Secrets Manager rotation**: automate quarterly rotation via Secrets Manager rotation lambda.
- **Cost monitoring**: add `aws ce get-cost-and-usage` weekly report for orchestrator fleet.

## Temporary states + canonical follow-up plans

- GCP planning VM (34.146.53.106) remains live until DNS cutover to AWS. Successor: DNS + EIP allocation (deferred).
- AWS IAM (Phase 2) complete — profile `uts-orchestrator-epic` in account 427895769566.
- `CLOUD_PROVIDER` default is `aws` (flipped at agent-orch@ff0d5ff after Phase 4 smoke).

## Deferred work — migrated to:

**MIGRATED FROM:** this plan → `plans/epics/orchestrator_master.md` P2:

- **DNS**: point `api-<vm>.agent-orchestrator.odum-research.com` to AWS EIPs or ALB once EIPs allocated
- **EIP allocation**: replace dynamic public IPs with stable EIPs; update `backends.json` once allocated
- **AWS Secrets Manager rotation**: automate quarterly secret rotation via Lambda rotation function
- **Cost monitoring**: add `aws ce get-cost-and-usage` weekly cost report for orchestrator fleet
