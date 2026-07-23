---
doc_type: codex-runbook
title: VM log + lifecycle observability — verify durable shipping to GCS/S3 (no SSH, no lost logs)
summary:
  T+10min per-VM check that a launch is durably shipping its run log + heartbeat + terminal EXIT_STATUS to
  deployment-scripts-<pid> (GCP) / unified-trading-deployment-scripts-<account> (AWS) — the canonical prefixes, the two
  observability tiers (canonical tarball vs inline-bespoke), the done-definition, and failure-mode fixes so a dead VM's
  full log survives without SSH. Enforces the No fire-and-forget HARD RULE.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [runbook, observability, vm-tarball, infrastructure, monitoring, verification]
related:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/lib/aws_ec2_launch_lib.sh,
    deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
  ]
created: 2026-06-19
owner: operator (or the agent that launched the VM, at T+10min post-launch)
cadence: per-VM-launch (event-driven — verify each launched VM is shipping logs+events; plus a weekly fleet spot-check)
verifier: >-
  `gsutil ls gs://deployment-scripts-<pid>/vm-logs/<vm>/run.log` returns a growing object within ~2 min of boot AND a
  `vm-heartbeat/<vm>.txt` blob exists; on exit a `vm-logs/<vm>/EXIT_STATUS` marker is present
last_executed:
code_refs:
audience: dev / operator
last_updated: 2026-06-19
execution:
  {
    owner: "operator (or the agent that launched the VM, at T+10min post-launch)",
    cadence:
      per-VM-launch (event-driven — verify each launched VM is shipping logs+events; plus a weekly fleet spot-check),
    verifier:
      "`gsutil ls gs://deployment-scripts-<pid>/vm-logs/<vm>/run.log` returns a growing object within ~2 min of boot AND
      a `vm-heartbeat/<vm>.txt` blob exists; on exit a `vm-logs/<vm>/EXIT_STATUS` marker is present",
    last_executed: 2026-06-19,
  }
---

# VM log + lifecycle observability — verify durable shipping to GCS/S3

**Goal**: every VM launch ships its run log + lifecycle/heartbeat continuously to durable object storage, so progress is
visible WITHOUT SSH and a dead VM's full log + terminal status survive its termination. This is the "No fire-and-forget
VM launches" HARD RULE, verified per-launch.

## The two observability tiers (which one a VM is on)

| Tier                                 | How                                                                                                                                                                          | Provides                                                                                                                                             |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — canonical** (tarball+venv VMs) | `startup-script-url=…/vm/setup-data-pipeline-vm.sh` → `_launch_with_tee` → `vm-exec-with-gcs-tee.sh`                                                                         | 30 s GCS log stream + STARTED/PROGRESS/COMPLETED/FAILED deployment-registry events + stall watchdog + EXIT_STATUS + log-archive backup + self-delete |
| **B — inline** (bespoke startup VMs) | launcher sources `lib/launcher_common.sh`/`lib/aws_ec2_launch_lib.sh`, emits `lc_log_upload_trap_block`/`lc_aws_log_upload_trap_block` as the first line of the startup body | 30 s GCS/S3 log stream + 30 s liveness/progress heartbeat blob + terminal EXIT_STATUS + guaranteed final upload + `shutdown -h +1`                   |

Both write to the SAME canonical prefixes (`vm-logs/<vm>/run.log`, `vm-heartbeat/<vm>.txt`, `vm-logs/<vm>/EXIT_STATUS`)
on `deployment-scripts-<pid>` (GCP) / `unified-trading-deployment-scripts-<account>` (AWS).

## Procedure — T+10min post-launch check (per VM)

GCP:

```bash
PID=central-element-323112; VM=<vm-name>
# 1. Log is streaming (object exists + size grows across two reads ~30s apart):
gsutil ls -l gs://deployment-scripts-$PID/vm-logs/$VM/run.log
sleep 35; gsutil ls -l gs://deployment-scripts-$PID/vm-logs/$VM/run.log   # size MUST climb (or workload already done)
gsutil cat gs://deployment-scripts-$PID/vm-logs/$VM/run.log | tail -30
# 2. Heartbeat blob is fresh (alive_at within the last ~minute):
gsutil cat gs://deployment-scripts-$PID/vm-heartbeat/$VM.txt
# 3. On exit, the terminal status marker is present (rc=0 completed / rc!=0 failed):
gsutil cat gs://deployment-scripts-$PID/vm-logs/$VM/EXIT_STATUS
```

AWS (mirror with `aws s3` + `unified-trading-deployment-scripts-<account>`):

```bash
ACCT=<account>; VM=<vm-name>; R=ap-northeast-1
aws s3 ls   s3://unified-trading-deployment-scripts-$ACCT/vm-logs/$VM/run.log --region $R
aws s3 cp   s3://unified-trading-deployment-scripts-$ACCT/vm-logs/$VM/run.log - --region $R | tail -30
aws s3 cp   s3://unified-trading-deployment-scripts-$ACCT/vm-heartbeat/$VM.txt - --region $R
aws s3 cp   s3://unified-trading-deployment-scripts-$ACCT/vm-logs/$VM/EXIT_STATUS - --region $R
```

## Done-definition

- `run.log` exists and **grows** within ~2 min of boot (or the workload already finished with a clean tail).
- `vm-heartbeat/<vm>.txt` exists and its `alive_at` advances each ~30 s tick while the VM runs.
- After the VM exits, `vm-logs/<vm>/EXIT_STATUS` carries the workload rc (0 = completed, non-zero = failed).
- A killed/terminated VM still has its full log in `vm-logs/` (≤30 s loss) — you NEVER need SSH/SSM/serial-port to read
  it.

## Failure modes + fixes

- **`run.log` empty / never appears** → VM crashed before the streamer started (boot/apt/tarball failure). Read the
  serial console: GCP `gcloud compute instances get-serial-port-output <vm> --zone <z>`; AWS
  `aws ec2 get-console-output`. For Pattern A the setup-script EXIT trap also uploads `vm-logs/<vm>/vm-setup.log` +
  `SETUP_EXIT_STATUS`.
- **Log present but FROZEN (not growing) while VM still RUNNING** → the workload hung. Pattern A's stall watchdog
  SIGKILLs after `STALL_TIMEOUT_SEC` (default 1800 s) and writes a failure EXIT_STATUS. Pattern B has no in-VM stall
  watchdog — the zombie-watchdog reaps it via the stale heartbeat blob; investigate the workload (py-spy / serial).
- **Bespoke launcher with VM-LOCAL-only logs (no GCS/S3 object at all)** → the launcher is NOT on tier B. Wire it:
  source the lib, emit `lc_log_upload_trap_block`/`lc_aws_log_upload_trap_block` as the first startup-body line, and
  remove any trailing bare `shutdown -h now` (it races the trap's final upload). See the codex § "Observability +
  lifecycle — two tiers".

## Cleanup / lifecycle (no log accumulation)

`vm-logs/` (14 d), `vm-heartbeat/` (15 d), `log-archive/` (30 d) auto-delete via lifecycle rules — GCP
`terraform/gcp/main.tf` (`google_storage_bucket.deployment_scripts`) + daily durable archival
`terraform/gcp/vm_log_archival_scheduler.tf`; AWS `terraform/aws/vm_logs_lifecycle.tf`. No manual pruning required.
