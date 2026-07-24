---
doc_type: issue
title: Long-lived orchestrator VM logs are not backed up off-box (GCP + AWS) — lost on termination
summary:
  '**Finding 2026-07-02:** the durable-log streamer shipped by `vm_launcher_durable_log_observability_2026_06_19` covers
  batch/backfill VMs (run.log→GCS/S3 every 30s + EXIT_STATUS). Long-lived orchestrator VMs (planning / epic /
  central-brain / orchestrator-worker, GCP AND AWS) only `tee` a cold-boot bootstrap log to VM-local
  `/var/log/*-bootstrap.log`, ship no log content off-box, and run no logging agent — so their logs die with the VM.
  They were EXEMPTED from the coverage guard on a misleading "systemd/container logging" rationale (no agent is
  installed; journald is VM-local too).'
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, agent-orchestrator]
scope: [engineer, admin]
tags: [vm, logging, observability, gcs, s3, long-lived, orchestrator]
related: [vm_launcher_durable_log_observability_2026_06_19]
created: "2026-07-02"
parent_epic: infrastructure_master
priority: P2
source:
  [
    "vm_launcher_durable_log_observability_2026_06_19 remaining-items review 2026-07-02",
    "deployment-service/scripts/vm launcher audit",
    "coverage-guard EXEMPT whitelist inspection tests/unit/test_vm_launcher_scripts.py:661",
  ]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-02
---

## What I found

The `vm_launcher_durable_log_observability_2026_06_19` plan closed the batch/backfill freeze-and-lose incident, but a
review of its remaining items (2026-07-02) surfaced a distinct, still-open gap for **long-lived VMs**. Three tiers:

- **Tier 1 — batch/backfill VMs → fully backed up.** `run.log` streamed to GCS/S3 every 30 s + `EXIT_STATUS` +
  log-archive, via `lc_log_upload_trap_block` / `lc_aws_log_upload_trap_block` / `vm-exec-with-gcs-tee.sh`. Survives
  termination.
- **Tier 2 — live consolidated MTDS VMs (cefi/prediction) → partial.** `setup-cefi-live-consolidated-vm.sh:48` uploads
  `vm-setup.log` to `vm-logs/<vm>/` **only on the exit trap**; per-shard runtime `live-*.log` stay VM-local. Heartbeat
  sidecar is liveness-only.
- **Tier 3 — long-lived orchestrator VMs → NOT backed up.** `launch-planning-vm.sh`, `launch-central-brain-aws.sh`,
  `launch-orchestrator-worker-vm.sh` do only `exec > >(tee /var/log/<name>-bootstrap.log) 2>&1` (VM-local). No GCS/S3
  upload of that log; `agent-orchestrator` ships no runtime logs off-box; **no logging agent is installed anywhere**
  (`ops-agent` / `google-fluentd` / `amazon-cloudwatch-agent` grep = 0). They emit only a one-shot `STARTED` event + a
  60 s heartbeat blob (`vm-heartbeat/<vm>.txt` = `<epoch>\n<rc>\n<status>`, per
  `deployment_service/data_pipeline_monitors/_gcs.py:148`). To read them you must SSH in; on termination they are gone —
  the same incident class the parent plan was created to close, for a different VM set.

### The misleading exemption

Tier 3 launchers are whitelisted in the coverage guard
(`deployment-service/tests/unit/test_vm_launcher_scripts.py:661-687`) with reasons like _"no batch run-log lifecycle"_ /
_"systemd/container logging."_ That conflates _"doesn't need EXIT_STATUS"_ with _"doesn't need durable logs."_ A
long-lived VM accumulates more history before it dies, so it arguably needs off-box logs **more**. The guard exemption
should be corrected to reflect that these are deferred-not-exempt (or the gap closed).

(Possible partial exception: `launch-dashboard-vm.sh` is a container VM — if on COS, Docker stdout auto-ships to Cloud
Logging. The orchestrator VMs are plain Ubuntu `apt-get`, so no auto-logging.)

## Proposed fix (deferred per operator 2026-07-02 — not scheduled)

Add a lightweight **continuous log-tail shipper** for Tier 3: a `nohup` loop that `gcloud storage cp` / `aws s3 cp` the
bootstrap log + the orchestrator's own log dir to `vm-logs/<vm>/` every N seconds — same GCS/S3 contract as Tier 1,
minus the EXIT_STATUS/shutdown semantics (these VMs don't self-terminate). Small addition to
`scripts/vm/lib/launcher_common.sh` + `scripts/vm/lib/aws_ec2_launch_lib.sh`. When done, correct the coverage-guard
EXEMPT reasons accordingly.

- [ ] [SCRIPT] P2. Add a continuous (non-terminating) log-tail→GCS shipper helper to `launcher_common.sh`; wire into
      `launch-planning-vm.sh`.
- [ ] [SCRIPT] P2. AWS mirror in `aws_ec2_launch_lib.sh`; wire into `launch-central-brain-aws.sh`,
      `launch-orchestrator-worker-vm.sh`. (Was also `launch-epic-vm-aws.sh` — REMOVED 2026-07-24 with the rest of the
      per-epic-VM code; `launch-central-brain-aws.sh` is the sole surviving central/planning launcher.)
- [ ] [SCRIPT] P3. Once shipped, replace the misleading Tier-3 EXEMPT reasons in `test_vm_launcher_scripts.py`
      (durable-log coverage guard) with the streamer wiring, or a correct "long-lived continuous-tail (not EXIT_STATUS)"
      rationale.

> **Decision (operator, 2026-07-02):** not needed right now. Captured here so the parent plan can archive without losing
> the finding. Revive by scheduling these todos.
