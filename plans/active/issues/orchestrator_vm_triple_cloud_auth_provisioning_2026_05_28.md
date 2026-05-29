---
title: "Orchestrator VM triple-cloud auth parity — GCP ADC + GitHub + AWS on every epic VM"
created: 2026-05-28
author: ikenna-slot-1
parent_epic: epics/infrastructure_master.md
assigned_vm: planning-vm
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
source:
  - agent-orchestrator/scripts/bootstrap_vm.sh
  - deployment-service/terraform/aws/orchestrator_epic_vms.tf
  - codex/12-agent-workflow/agent-orchestrator-overview.md
locked_by: live-defi-rollout
---

## What I found

Every orchestrator epic VM (the 10 `agent-orch-vm-*-20260522` EC2 instances) only had **AWS auth** (via instance role
`uts-orchestrator-epic-role`) but **no GCP ADC and no GitHub auth** for the `ubuntu` user. Concrete gap:

- ❌ `gcloud` binary not installed; no `~/.config/gcloud/application_default_credentials.json`
- ❌ `gh` CLI not installed; `gh auth status` would fail
- ❌ `git config --global user.{name,email}` unset for `ubuntu`
- ❌ Any `gsutil ls`, `google-cloud-storage` Python client, or `gcsfs` call from a worker would fail with 401
- ✅ AWS already covered by instance role (verified `aws sts get-caller-identity` returns the assumed-role ARN)

The bootstrap script DID already fetch `GH_PAT` from AWS SM and use it for `git clone` URLs, so private-repo cloning
worked — but interactive `gh` workflows, ssh-style git remotes, and git ops that bounce through
`git ls-remote https://github.com/...` all failed (no credential helper wired).

This blocked any plan with `assigned_vm: vm-*` from touching GCS, GitHub-CLI, or `git ls-remote` flows.

## Why it matters

- All 10 epic-VM plans depend on auth-parity with the operator laptop. Without it, agents silently fall back to
  ungraceful failure modes (e.g. `gcsfs.exceptions.HttpError`, `git: could not read Username`).
- The data pipeline + manifest consolidator runs that the operator-ops VM owns hit GCS hourly — they were OK as long as
  they happened to run via the orchestrator's Python venv (which uses the instance-role AWS creds) but ANY ad-hoc
  worker-shell `gsutil`/`gcloud` invocation would 401.
- Composes with `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` (setup-tokens for the Claude account
  fleet) — auth parity is the per-cloud equivalent.

## What shipped

**Bootstrap extension** — `agent-orchestrator/scripts/bootstrap_vm.sh`:

- `0febb19` — feat: `STEP 1.6` (install gcloud + gh CLIs via official apt repos, idempotent) + `STEP 5.5` (fetch GCP SA
  JSON from AWS SM secret `ORCHESTRATOR_VM_GCP_ADC`, write to `~/.config/gcloud/application_default_credentials.json`
  with mode 600, activate SA via `gcloud auth activate-service-account`, `gh auth login --with-token` using the existing
  GH_PAT, set `git config --global user.name=Claude / user.email=noreply@anthropic.com`, append
  `GOOGLE_APPLICATION_CREDENTIALS` to `.env.local` + `~/.bashrc` + `~/.profile`, sanity-check report to
  `/var/log/bootstrap_vm.log`).
- `843c187` — fix: `gh auth setup-git` (so `git ls-remote https://github.com/...` uses gh's credential helper) +
  resilient `git pull --ff-only` on `unified-trading-pm` (don't abort the bootstrap mid-script when PM has diverged
  history — STEP 5.5 must always run).

**GCP SA + secret**:

- Reused existing SA `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (no new SA created — the
  existing IAM bindings cover the orchestrator VM needs):
  - `roles/storage.objectAdmin`
  - `roles/secretmanager.secretAccessor`
  - `roles/bigquery.dataEditor`
  - `roles/pubsub.editor`
  - `roles/run.invoker`
- New SA key created (key id `4af7b762c69e34eda225428a0979c039db4ad18a`); JSON pushed to AWS SM:
  - Secret name: `ORCHESTRATOR_VM_GCP_ADC`
  - ARN: `arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:ORCHESTRATOR_VM_GCP_ADC-wTMgZC`
  - SecretString length: 2397 bytes (full SA JSON)
- IAM policy `uts-orchestrator-epic-policy` extended to v2 to grant `secretsmanager:GetSecretValue` on the new secret
  ARN. v2 set as default.

**Fleet rollout** — all 10 EC2 instances:

| InstanceId          | Role tag                             | GCP  | gsutil | gh   | AWS  | git ls-remote | ADC file |
| ------------------- | ------------------------------------ | ---- | ------ | ---- | ---- | ------------- | -------- |
| i-007e8d99d12831578 | agent-orch-vm-orchestrator-20260522  | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-06e33c6e188798333 | agent-orch-vm-cross-cutting-20260522 | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-0a663001399ef5f49 | agent-orch-vm-tradfi-20260522        | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-05805eb07fdf180b6 | agent-orch-vm-defi-20260522          | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-0e51b9c73666b3a8b | agent-orch-vm-trading-core-20260522  | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-0e89a5f6bd7123521 | agent-orch-vm-operator-ops-20260522  | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-063bc8dbf59f36220 | agent-orch-vm-prediction-20260522    | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-005e1bada21b1653f | agent-orch-vm-sports-20260522        | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-003be935f72c13d51 | agent-orch-vm-cefi-20260522          | PASS | PASS   | PASS | PASS | PASS          | PASS     |
| i-02294132088f23e50 | agent-orch-vm-ml-20260522            | PASS | PASS   | PASS | PASS | PASS          | PASS     |

10/10 VMs green on all 6 checks.

## What blocked (and was worked around)

3 VMs (trading-core, cefi, ml) had a diverged-history `unified-trading-pm` working tree that caused the bootstrap's Step
3 `git pull --ff-only` to abort with `set -e`. STEP 5.5 was never reached on the second bootstrap re-run. Two recovery
actions:

1. Direct STEP 5.5 logic re-ran on the 3 VMs via SSM (ADC fetched + gcloud activated + gh login + git config set).
2. Bootstrap script hardened with `||` so a diverged PM pull no longer aborts the script (commit `843c187`).

After the third bootstrap run on a future host, both fixes will compose: pull failure logs a WARN and STEP 5.5 still
runs.

## Residual / follow-ups

- [ ] [INFRA] P2. Fold `ORCHESTRATOR_VM_GCP_ADC` IAM grant into Terraform (`uts-orchestrator-epic-policy`) — currently
      the v2 policy version is set as default but the TF source-of-truth still encodes v1. Re-apply the TF will revert.
- [ ] [INFRA] P2. SA-key rotation: the new key expires `unified-trading-sa` keys rotate. Add a calendar reminder 90d out
      (or move to short-lived workload-identity-federation post-cutover).
- [ ] [INFRA] P3. Pre-bake the AMI so `gcloud + gh` install (~30s) happens once at AMI build time, not per cold boot.

## Codex SSOT updates

- `codex/12-agent-workflow/agent-orchestrator-overview.md` — add a "triple-cloud auth" section pointing at this issue
  doc + the bootstrap STEP 5.5.
- `codex/05-infrastructure/orchestrator-vm-fleet.md` (if it exists) — add the IAM-policy + SM-secret + SA-key entries.

## Provenance

- Bootstrap commits: `agent-orchestrator@0febb19` (initial) + `agent-orchestrator@843c187` (gh-setup-git + resilient
  pull).
- AWS SM secret: `ORCHESTRATOR_VM_GCP_ADC`
  (arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:ORCHESTRATOR_VM_GCP_ADC-wTMgZC).
- GCP SA key id: `4af7b762c69e34eda225428a0979c039db4ad18a` (created via `gcloud iam service-accounts keys create`).
- IAM policy v2: `arn:aws:iam::427895769566:policy/uts-orchestrator-epic-policy` version `v2` (default).
- Operator authorization: 2026-05-28 — "every orchestrator VM gets the same triple-cloud auth as the operator's laptop".
