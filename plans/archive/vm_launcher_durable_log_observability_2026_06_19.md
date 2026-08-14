---
doc_type: plan
title: VM launcher durable log + lifecycle observability — ship every launch's logs+events to GCS/S3
summary:
  Ship every VM launch logs and lifecycle events to durable GCS/S3 storage so progress is visible without SSH and logs
  survive termination.
status: complete
nature: process
asset_group: [cross-cutting]
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
last_updated: 2026-07-02
archived: 2026-07-02
locked_by: NA
locked_since: NA
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
assigned_role: infra-engineer
drift_direction: advance-code
---

## Deferred work — migrated to: `plans/archive/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md` — successor:

long_lived_vm_logs_not_backed_up_2026_07_02 (the one remaining P3 item — sweeping the 3 long-lived `*-aws.sh` launchers
— was DEFERRED by operator decision 2026-07-02 and migrated to that issue doc; see the item's own note below)

# VM launcher durable log + lifecycle observability

> **🗄️ ARCHIVED 2026-07-02 (operator-directed).** Core goal shipped: every **batch/backfill** VM launch streams its
> run.log + heartbeat + terminal `EXIT_STATUS` to durable GCS/S3, and a coverage guard prevents regression.
> Remaining-item review (2026-07-02) confirmed **6 of 7 open items were already done or resolved-by-decision** (see
> below); the one genuinely-open item — **durable logs for long-lived orchestrator VMs (Tier 3, GCP + AWS)** — is
> consciously **DEFERRED, not lost**, and migrated to
> [`plans/archive/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md`](../active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md).
> Codex SSOT for the shipped contract: `/codex/05-infrastructure/vm-tarball-deployment.md` § "Observability + lifecycle
> — two tiers" + runbook `/codex/15-runbooks/vm-log-observability-verify.md`.

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
- [x] [DOC] P0. Codex § "Observability + lifecycle — two tiers" (`/codex/05-infrastructure/vm-tarball-deployment.md`) +
      runbook `/codex/15-runbooks/vm-log-observability-verify.md` (owner/cadence/verifier/last_executed).

## Remaining — migrate the rest of the bespoke GCP launchers to the SSOT helper

These bespoke GCP launchers ALREADY have an ad-hoc continuous-streaming loop (so they are NOT the freeze-and-lose
class), but they roll their own loop with non-canonical log paths and **lack the terminal `EXIT_STATUS` marker**.
Migrate each to source `lib/launcher_common.sh` + emit `lc_log_upload_trap_block` (deleting the bespoke loop) so they
converge on the canonical `vm-logs/`/`vm-heartbeat/`/`EXIT_STATUS` contract. Target repo: **deployment-service**.

**Closure review 2026-07-02**: verified each remaining item against the actual tree. The four P2 launchers + the
coverage guard shipped in **deployment-service@5d07bb1** (2026-06-22, Phase 4). The epic/planning migration was
superseded by a re-classification decision (added to the guard's EXEMPT whitelist as LONG_LIVED). Only the AWS
long-lived sweep is genuinely open, and is migrated to the Tier-3 issue doc (deferred per operator).

- [x] [SCRIPT] P2. `launch-aave-lending-rate-validation-vm.sh` — replace bespoke stream loop with
      `lc_log_upload_trap_block`. ✅ deployment-service@5d07bb1 — wired at
      `launch-aave-lending-rate-validation-vm.sh:138`; bespoke loop removed; `bash -n` clean.
- [x] [SCRIPT] P2. `launch-amm-golden-fixture-validation-vm.sh` — same (already sources launcher_common; swap to the
      helper). ✅ deployment-service@5d07bb1 — `launch-amm-golden-fixture-validation-vm.sh:203`; `bash -n` clean.
- [x] [SCRIPT] P2. `launch-gcs-migration-bundle-vm.sh` — same. ✅ deployment-service@5d07bb1 —
      `launch-gcs-migration-bundle-vm.sh:109`; `bash -n` clean.
- [x] [SCRIPT] P2. `launch-features-sports-parallel-backfill-vm.sh` — writes a separate VM-runner script
      (`vm_fss_features.sh`); inject the trap block at the top of that runner body (higher care — test the runner
      heredoc render). ✅ deployment-service@5d07bb1 — trap injected into the runner body at
      `launch-features-sports-parallel-backfill-vm.sh:311`; `bash -n` clean.
- [x] [SCRIPT] P3. `launch-epic-vm.sh` + `launch-planning-vm.sh` — long-lived/daemon VMs; converge their inline stream
      loop onto the helper for EXIT_STATUS + heartbeat parity. ✅ **RESOLVED BY DECISION (2026-06-22)**: rather than
      migrate, both were classified LONG_LIVED (no batch run-log lifecycle) and added to the coverage-guard EXEMPT
      whitelist with reasons (`tests/unit/test_vm_launcher_scripts.py:666-669`); monitored by the zombie-watchdog. NOTE:
      this means their runtime logs are NOT backed up off-box — tracked as a separate deferred gap, see the Tier-3 issue
      doc below.
- [ ] [SCRIPT] P3. Sweep the remaining `*-aws.sh` non-backfill launchers (`launch-central-brain-aws.sh`,
      `launch-orchestrator-worker-vm.sh`, `launch-epic-vm-aws.sh`) for the same lc_aws_log_upload_trap_block wiring. →
      **DEFERRED (operator, 2026-07-02) & MIGRATED** to
      [`plans/archive/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md`](../active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md).
      These three are long-lived orchestrator VMs (their GCP twins are EXEMPT); today they only `tee` to VM-local
      `/var/log/*-bootstrap.log` with no S3 backup. Closing this is the Tier-3 continuous-tail shipper, not the batch
      EXIT_STATUS trap.
- [x] [SCRIPT] P3. Add a QG/lint check (deployment-service `quality-gates.sh` post-gate) that flags any
      `scripts/vm/launch-*.sh` whose inline `startup-script=`/`user-data` heredoc neither uses
      `setup-data-pipeline-vm.sh` NOR emits `lc_log_upload_trap_block`/`lc_aws_log_upload_trap_block` — so a future
      bespoke launcher can't ship VM-local-only logs silently. ✅ deployment-service@5d07bb1 — shipped as the
      `TestDurableLogStreamerCoverage` guard (`tests/unit/test_vm_launcher_scripts.py:628`), which scans every GCP
      `launch-*.sh`, fails on any unconverted+non-whitelisted launcher, and self-tests the regression it prevents. (Runs
      in CI via the test suite rather than as a `quality-gates.sh` post-gate — functionally equivalent.)

## Codex SSOT updates

- `/codex/05-infrastructure/vm-tarball-deployment.md` § "Observability + lifecycle — two tiers" (updated 2026-06-19).
- `/codex/15-runbooks/vm-log-observability-verify.md` (new runbook).
