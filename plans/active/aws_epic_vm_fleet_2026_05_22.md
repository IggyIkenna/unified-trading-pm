---
title: AWS epic VM fleet — CLOUD_PROVIDER toggle + AWS-preferred default
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-05-22
related_plans:
  - epic_vm_fleet_commissioning_2026_05_21.md (archived)
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

- `codex/05-infrastructure/agent-orchestrator-worker-topology.md` — update Cloud provider toggle section when done
- `codex/05-infrastructure/vm-tarball-deployment.md` — no changes needed (trading VMs only)

---

## Phase 1 — bootstrap_vm.sh: add CLOUD_PROVIDER toggle

All cloud-specific calls in `bootstrap_vm.sh` must branch on `$CLOUD_PROVIDER`. GCP remains the fallback.

- [ ] [AGENT] P0. Add `--cloud-provider aws|gcp` arg to `bootstrap_vm.sh` (default `gcp` while GCP fleet is live; flips
      to `aws` once AWS fleet verified). Env var `CLOUD_PROVIDER` also respected as override.
- [ ] [AGENT] P0. Branch GH_PAT fetch: GCP → `gcloud secrets versions access latest --secret=GH_PAT`; AWS →
      `aws secretsmanager get-secret-value --secret-id GH_PAT --query SecretString --output text`.
- [ ] [AGENT] P0. Branch ORCHESTRATOR_ENV_LOCAL fetch: GCP →
      `gcloud secrets versions access latest --secret=ORCHESTRATOR_ENV_LOCAL`; AWS →
      `aws secretsmanager get-secret-value --secret-id ORCHESTRATOR_ENV_LOCAL --query SecretString --output text`.
- [ ] [AGENT] P0. Branch accounts.json + backlog.yaml fetch: GCP → `gcloud storage cp gs://.../config/...`; AWS →
      `aws s3 cp s3://uts-orchestrator-creds-{account}/config/... .` (bucket name TBD — see Phase 2).
- [ ] [AGENT] P0. Branch STARTED event emit: GCP → `gcloud storage cp - gs://.../STARTED`; AWS →
      `aws s3 cp - s3://uts-orchestrator-events-{account}/orchestrator/epic/{vm-name}/STARTED`.
- [ ] [AGENT] P0. VM_NAME detection: GCP → `curl -H 'Metadata-Flavor: Google' metadata.google.internal/...`; AWS →
      IMDSv2 token + `curl -H "X-aws-ec2-metadata-token: $TOKEN" 169.254.169.254/latest/meta-data/tags/instance/Name`.
- [ ] [AGENT] P1. Update PUBLIC_URL env var: GCP uses external IP from metadata; AWS uses public hostname from
      `169.254.169.254/latest/meta-data/public-hostname`.
- [ ] [AGENT] P1. Verify `su - ubuntu` pattern works on Ubuntu 24.04 on EC2 (AWS AMI uses same ubuntu user; uv HOME fix
      should carry over unchanged).

## Phase 2 — AWS resource prerequisites

IAM role, S3 buckets, Secrets Manager secrets, and security group must exist before launching fleet.

- [ ] [OPERATOR] P0. Create IAM instance profile `uts-orchestrator-epic` with permissions:
      `secretsmanager:GetSecretValue` (secrets: `GH_PAT`, `ORCHESTRATOR_ENV_LOCAL`), `s3:GetObject` (bucket:
      `uts-orchestrator-creds-{account}/config/*`), `s3:PutObject` (bucket:
      `uts-orchestrator-events-{account}/orchestrator/*`). Script:
      `deployment-service/scripts/aws/setup-orchestrator-iam.sh` (to be created — Phase 3).
- [ ] [OPERATOR] P0. Create S3 buckets (ap-northeast-1, account `427895769566`): `uts-orchestrator-creds-427895769566`
      (private, versioned) + `uts-orchestrator-events-427895769566` (private, 90-day lifecycle).
- [ ] [OPERATOR] P0. Upload GH_PAT + ORCHESTRATOR_ENV_LOCAL to AWS Secrets Manager (`ap-northeast-1`, account
      `427895769566`) — same values as GCP Secret Manager.
- [ ] [OPERATOR] P0. Upload `accounts.json` + `backlog.yaml` to `s3://uts-orchestrator-creds-427895769566/config/`.
- [ ] [OPERATOR] P0. Create/confirm security group `uts-orchestrator-epic-sg` in ap-northeast-1: inbound tcp:22
      (operator IPs), tcp:8026 (operator IPs); outbound all.
- [ ] [OPERATOR] P0. Identify subnet IDs in ap-northeast-1a/b/c for `AWS_SUBNET_ID`.

## Phase 3 — launch-epic-vm-aws.sh

New launcher: AWS EC2 equivalent of `launch-epic-vm.sh`. Reads same `orchestrator_vm_registry.yaml`.

- [ ] [AGENT] P0. Create `deployment-service/scripts/vm/launch-epic-vm-aws.sh`: - Same `--vm-id` / `--all` / `--dry-run`
      / `--force` flags as the GCP launcher - Uses `lib/aws_ec2_launch_lib.sh` (`lc_aws_ec2_run`,
      `lc_aws_singleton_check`, `lc_aws_resolve_ami`) - Instance type: `m7i.xlarge` (4 vCPU / 16GB — matches GCP
      `e2-standard-4`; cheaper on AWS) - Region: `ap-northeast-1` (same timezone as GCP `asia-northeast1`; minimize
      latency to GCS data) - Instance profile: `uts-orchestrator-epic` - User-data startup script: mirrors GCP startup
      script but with `CLOUD_PROVIDER=aws` set + no gcloud deps - VM naming: `agent-orch-{vm-id}-{YYYYMMDD}` (same
      convention as GCP) - Add `agent-orch-` prefixes to `vm_zombie_watchdog_aws.py` `VM_PREFIX_TO_BUCKET` after launch
- [ ] [AGENT] P0. Create `deployment-service/scripts/aws/setup-orchestrator-iam.sh` — idempotent IAM setup (role +
      policy + instance profile). Prerequisite before any fleet launch.
- [ ] [AGENT] P1. Add `CLOUD_PROVIDER=aws` to `launch-epic-vm-aws.sh` metadata so startup script and bootstrap both pick
      it up without extra args.

## Phase 4 — Single-VM smoke test

Launch one VM (vm-defi), verify bootstrap completes, health endpoint responds, STARTED event in S3.

- [ ] [AGENT] P0. Launch `vm-defi` on AWS: `bash launch-epic-vm-aws.sh --vm-id vm-defi`. Bootstrap should complete in
      ≤10 min. Verify: 1.
      `aws ec2 describe-instances --filters Name=tag:Name,Values=agent-orch-vm-defi-* --query ... --output text` =
      `running` 2. `curl -sf http://<public-ip>:8026/health` = `{"status":"ok"}` 3.
      `aws s3 ls s3://uts-orchestrator-events-427895769566/orchestrator/epic/agent-orch-vm-defi-.../STARTED`
- [ ] [AGENT] P0. If smoke fails: check `/var/log/epic-vm-bootstrap.log` via AWS SSM Session Manager
      (`aws ssm start-session --target <instance-id>`) or EC2 console serial output.
- [ ] [AGENT] P1. Once smoke passes: update `bootstrap_vm.sh` default `CLOUD_PROVIDER` from `gcp` to `aws`.

## Phase 5 — Full fleet launch on AWS + GCP decommission

- [ ] [AGENT] P0. `bash launch-epic-vm-aws.sh --all` — all 10 epic VMs on AWS. T+10min: all 10 health=ok + all 10 S3
      STARTED events confirmed.
- [ ] [AGENT] P1. Terminate GCP fleet once AWS fleet is stable for 24h:
      `gcloud compute instances list --filter="name~agent-orch-" --zones=asia-northeast1-c` → terminate all. Keep
      planning VM (34.146.53.106) running until DNS is wired to AWS.
- [ ] [AGENT] P1. Update `orchestrator_vm_registry.yaml` with AWS instance IDs + public IPs.
- [ ] [AGENT] P1. Update `codex/05-infrastructure/agent-orchestrator-worker-topology.md` — fleet IPs + AWS section.
- [ ] [AGENT] P2. `setup-orchestrator-iam.sh --dry-run` on CI — prevents IAM drift on future launches.

## Deferred (post-cutover)

- **GCP re-enable**: `CLOUD_PROVIDER=gcp bash launch-epic-vm.sh --all` should always work. Do not remove GCP path.
- **DNS**: point `api-<vm>.agent-orchestrator.odum-research.com` to AWS EIPs or ALB.
- **EIP allocation**: currently using dynamic public IPs; stable EIPs needed for DNS.
- **AWS Secrets Manager rotation**: automate quarterly rotation via Secrets Manager rotation lambda.
- **Cost monitoring**: add `aws ce get-cost-and-usage` weekly report for orchestrator fleet.

## Temporary states + canonical follow-up plans

- GCP fleet remains live until AWS smoke passes + 24h stability window.
- AWS IAM (Phase 2) is OPERATOR action — agent cannot create IAM roles without operator credentials.
- `CLOUD_PROVIDER` default is `gcp` until Phase 4 smoke passes; then flips to `aws`.
