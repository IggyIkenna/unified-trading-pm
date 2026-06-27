---
doc_type: plan
title: VM launcher durable log + lifecycle observability — ship every launch's logs+events to GCS/S3
summary: "Ship every VM launch logs and lifecycle events to durable GCS/S3 storage so progress is visible without SSH and logs survive termination."
status: active
nature: process
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm, logging, observability, gcs, s3, lifecycle, durable-log]
related: []
created: 2026-06-19
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
depends_on:
source:
  - {
      operator incident 2026-06:
        "SFI + gas-fees + AWS-backfill VM logs to VM-local /tmp froze + were lost on termination, forcing
        serial-port/SSH diagnosis",
    }
  - audit 2026-06-19 of deployment-service/scripts/vm/ (134 launchers) vs the canonical vm-exec-with-gcs-tee.sh
    observability stack
asset_group: cross-asset
---

# VM launcher durable log + lifecycle observability

**Goal**: every VM launch ships its run log + lifecycle/heartbeat continuously to durable object storage (GCS/S3), so
progress is visible WITHOUT SSH and a dead VM's full log + terminal status survive termination. Closes the operator
incident where bespoke-launcher VMs (SFI / gas-fees / AWS backfills) logged only to VM-local `/tmp/*.log`.

## What shipped (2026-06-19)

The canonical tarball path (`setup-data-pipeline-vm.sh` → `_launch_with_tee` → `vm-exec-with-gcs-tee.sh`) already
streams the log to GCS every 30 s + emits STARTED/PROGRESS/COMPLETED/FAILED registry events + EXIT_STATUS + log-archive
backup. **The named problem launchers (SFI, gas-fees) were already on this path** — their freeze was a streamer/uploader
stall, not missing wiring. The real systemic gap was the bespoke/AWS launchers that inline their own startup script and
bypass that stack. SSOT fix landed in the shared trap-block helpers + the active backfill launchers:

- [x] [SCRIPT] P0. Upgrade `lc_log_upload_trap_block` (GCP, `scripts/vm/lib/launcher_common.sh`) from
      upload-on-EXIT-only to **continuous 30 s GCS log streamer + liveness/progress heartbeat blob
      (`vm-heartbeat/<vm>.txt`) + terminal `EXIT_STATUS` marker + STARTED banner**, signature
      `(vm_name, project_id, [asset_group], [task])` (backward-compat).
- [x] [SCRIPT] P0. Same upgrade to the AWS mirror `lc_aws_log_upload_trap_block`
      (`scripts/vm/lib/aws_ec2_launch_lib.sh`) — continuous `aws s3 cp` stream + heartbeat + EXIT_STATUS.
- [x] [SCRIPT] P0. Wire the 6 AWS EC2 backfill launchers to the upgraded helper (replace bare
      `exec >(tee /var/log/...)` + remove racing trailing `shutdown -h now`): `launch-mtds-backfill-vm-aws.sh`,
      `launch-cefi-sharded-backfill-aws.sh`, `launch-defi-backfill-vm-aws.sh`, `launch-features-backfill-vm-aws.sh`,
      `launch-instruments-backfill-vm-aws.sh`, `launch-mdps-backfill-vm-aws.sh` (+
      `launch-features-onchain-backfill-vm-aws.sh` covered — it delegates to features-backfill).
- [x] [SCRIPT] P0. Wire the 2 bespoke GCP launchers that had exit-only (freeze-and-lose) uploads:
      `launch-prediction-pipeline-vm.sh`, `launch-prediction-features-vm.sh`.
- [x] [TF] P0. Add AWS S3 lifecycle for the AWS deployment-scripts bucket (`terraform/aws/vm_logs_lifecycle.tf`: vm-logs
      14 d / vm-heartbeat 15 d / log-archive 30 d) mirroring the GCP `deployment_scripts` bucket. (GCP lifecycle already
      existed in `terraform/gcp/main.tf` + `vm_log_archival_scheduler.tf`.)
- [x] [DOC] P0. Codex § "Observability + lifecycle — two tiers" (`codex/05-infrastructure/vm-tarball-deployment.md`) +
      runbook `codex/15-runbooks/vm-log-observability-verify.md` (owner/cadence/verifier/last_executed).

## Remaining — migrate the rest of the bespoke GCP launchers to the SSOT helper

These bespoke GCP launchers ALREADY have an ad-hoc continuous-streaming loop (so they are NOT the freeze-and-lose
class), but they roll their own loop with non-canonical log paths and **lack the terminal `EXIT_STATUS` marker**.
Migrate each to source `lib/launcher_common.sh` + emit `lc_log_upload_trap_block` (deleting the bespoke loop) so they
converge on the canonical `vm-logs/`/`vm-heartbeat/`/`EXIT_STATUS` contract. Target repo: **deployment-service**. Each
is independent (parallelizable). Verify per launcher: `bash -n` + `shellcheck -S error` clean + (where supported)
`--dry-run` exits 0; do NOT actually create a VM.

- [ ] [SCRIPT] P2. `launch-aave-lending-rate-validation-vm.sh` — replace bespoke stream loop with
      `lc_log_upload_trap_block`.
- [ ] [SCRIPT] P2. `launch-amm-golden-fixture-validation-vm.sh` — same (already sources launcher_common; swap to the
      helper).
- [ ] [SCRIPT] P2. `launch-gcs-migration-bundle-vm.sh` — same.
- [ ] [SCRIPT] P2. `launch-features-sports-parallel-backfill-vm.sh` — writes a separate VM-runner script
      (`vm_fss_features.sh`); inject the trap block at the top of that runner body (higher care — test the runner
      heredoc render).
- [ ] [SCRIPT] P3. `launch-epic-vm.sh` + `launch-planning-vm.sh` — long-lived/daemon VMs; converge their inline stream
      loop onto the helper for EXIT_STATUS + heartbeat parity (lower priority — these are monitored by the
      zombie-watchdog already).
- [ ] [SCRIPT] P3. Sweep the remaining `*-aws.sh` non-backfill launchers (`launch-central-brain-aws.sh`,
      `launch-orchestrator-worker-vm.sh`, `launch-epic-vm-aws.sh`) for the same lc_aws_log_upload_trap_block wiring.
- [ ] [SCRIPT] P3. Add a QG/lint check (deployment-service `quality-gates.sh` post-gate) that flags any
      `scripts/vm/launch-*.sh` whose inline `startup-script=`/`user-data` heredoc neither uses
      `setup-data-pipeline-vm.sh` NOR emits `lc_log_upload_trap_block`/`lc_aws_log_upload_trap_block` — so a future
      bespoke launcher can't ship VM-local-only logs silently.

## Codex SSOT updates

- `codex/05-infrastructure/vm-tarball-deployment.md` § "Observability + lifecycle — two tiers" (updated 2026-06-19).
- `codex/15-runbooks/vm-log-observability-verify.md` (new runbook).
