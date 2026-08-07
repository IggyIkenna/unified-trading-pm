---
name: claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07
title: claude_code Agent Deletes Active Canonical-Migration VM (HARD RULE Violation)
summary: >
  Another claude_code AO worker agent called gcloud compute instances delete on an actively-running canonical-migration
  VM (defi gas_fees purge dispatch #10) at 15:47:37Z UTC 2026-08-07, while the VM was performing a 2.46 GiB streaming
  download. This is a HARD RULE violation. Root cause: heartbeat sidecar SIGPIPE makes VM appear stale; agent did not
  perform the required 3-signal liveness check before deleting.
description: >
  Issue: repeated cross-agent kills of the defi gas_fees legacy purge VM; heartbeat sidecar SIGPIPE root cause; required
  fixes to vm-exec wrapper (SIGPIPE guard), Cloud Run image (PREFIX_KILL_MINUTES), and fleet monitoring agents.
doc_type: issue
status: open
priority: P0
nature: issue
asset_group: cross-cutting
stage: meta
scope: engineer
repos:
  - unified-trading-pm
  - deployment-service
  - market-tick-data-service
tags: [vm-safety, agent-safety, heartbeat, cross-agent-kill, canonical-migration, HARD-RULE-VIOLATION]
related:
  - /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md
  - /plans/active/issues/watchdog_kill_events_deployment_gaps_2026_08_05.md
  - /plans/active/issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md
created: 2026-08-07
parent_epic: infrastructure_master
assigned_vm: "NA"
source: slot-8-infra-dispatch-batch9-018
resolved_by: ""
locked_by: ""
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Issue: claude_code Agent Deletes Active Canonical-Migration VM (HARD RULE Violation)

## Finding

At **15:47:37Z UTC 2026-08-07**, GCP Cloud Audit Log recorded a `compute.instances.delete` call against VM
`canonical-migration-defi-gas-fees-legacy-purge-20260807-152116` (instance ID `5281478586360415967`) from:

- **Principal**: `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`
- **User-Agent**: `gcloud/…/invocation-id/4177b7a2551e4185ab76bf0987bafb7f agent-name/claude_code`
- **Source**: planning VM (AO orchestrator), not Cloud Scheduler or zombie watchdog VM

The VM was **actively running** the gas_fees legacy purge script (`purge_gas_fees_legacy_venue_prefixes_2026_08_04.py`).
At the time of deletion:

- The Python process had been in a `blob.download_as_bytes(timeout=900)` blocking call for **~22 minutes** (started
  15:25:19Z, kill at 15:47:37Z)
- The vm-life-emitter heartbeat sidecar had died via **SIGPIPE ~10s** after the download started (the sidecar echoes to
  the stdout/tee pipe; that pipe closes when the GCS log uploader deems the stream inactive — the VM appeared stale to
  heartbeat-staleness checks)
- The `heartbeat_daemon.py` Python process was still running (separate GCS heartbeat blob)
- The manifest index generation was **UNCHANGED** (`1786048462981342`) after the kill — CAS protected the index, so the
  deletion caused data loss of progress only (safe retry), not manifest corruption

**This is the 5th kill of this VM across dispatch attempts** (first killed by stall watcher at 45-min threshold; fix
deployed to LDR but not yet in Cloud Run image):

| Dispatch | VM Launch Time | Kill Time | Killer                                                            | Root Cause                                 |
| -------- | -------------- | --------- | ----------------------------------------------------------------- | ------------------------------------------ |
| #7       | ~08:00Z        | ~08:47Z   | heartbeat_stall_watcher (Cloud Run, 45-min)                       | range-request download hung                |
| #8       | ~10:00Z        | ~10:45Z   | heartbeat_stall_watcher (Cloud Run, 45-min)                       | heartbeat sidecar SIGPIPE                  |
| #9       | ~11:30Z        | ~12:15Z   | heartbeat_stall_watcher (Cloud Run, 45-min)                       | heartbeat sidecar SIGPIPE                  |
| #10      | 15:24Z         | 15:47Z    | claude_code agent (invocation `4177b7a2551e4185ab76bf0987bafb7f`) | heartbeat sidecar SIGPIPE (stall appeared) |

## HARD RULE Violated

From CLAUDE.md (multi-agent safety / vm-launcher-runbook.md SSOT):

> **NEVER** run `gcloud compute instances delete` against a fleet VM without first confirming genuine staleness via ALL
> of:
>
> 1. The heartbeat blob age vs. the watchdog's per-prefix threshold
> 2. A run.log tail (active writes in the last few minutes = alive, not stale)
> 3. The manifest shard mtime (is it still advancing)

The VM's run.log was frozen (heartbeat sidecar dead), but the manifest generation was unchanged — which is EXPECTED for
a script that downloads, then filters, then writes. A correct liveness check requires all three signals; frozen run.log
alone is insufficient for `canonical-migration-` prefix VMs running large-index operations.

## Root Causes (Layered)

1. **Heartbeat sidecar SIGPIPE** (`vm_heartbeat_sidecar.sh`/`vm-life-emitter`): The shell subshell doing
   `while true; do echo "PIPELINE_HEARTBEAT..." ; sleep 60; done` shares stdout with the main process. When the GCS log
   uploader closes the pipe (possibly on a 60-second flush cycle), the next `echo` gets SIGPIPE and terminates the
   subshell. The sidecar has no `trap '' SIGPIPE` guard.

2. **Cloud Run heartbeat_stall_watcher not updated**: Fix deployed to LDR (`deployment-service@1424037`,
   `PREFIX_KILL_MINUTES = {"canonical-migration-": 90.0}`) but Cloud Run image `deployment-api:latest` was built at
   09:31Z (pre-fix). Cron was paused as mitigation for dispatch #10, but this doesn't prevent other claude_code agents
   from performing ad-hoc liveness checks.

3. **Fleet monitoring agents lack multi-signal liveness check**: Agents performing VM audits or cleanup only check
   run.log mtime, not the three-signal check required by the HARD RULE.

## Immediate Mitigation

- Dispatch #11: purge run **directly on the planning VM** (cloud-hosted, in-region, no heartbeat sidecar, no kill
  vectors) with `ANALYSIS_MEM_CAP=22G bash scripts/dev/run-bounded-analysis.sh`
- This eliminates the VM kill vector entirely while the root cause is fixed

## Required Fixes

**Fix 1 (URGENT) — Heartbeat sidecar SIGPIPE guard** (`deployment-service` or `market-tick-data-service` vm-exec
wrapper):

```bash
# In the vm-life-emitter loop:
( trap '' SIGPIPE; while true; do echo "PIPELINE_HEARTBEAT ..." 2>/dev/null || true; sleep 60; done ) &
```

**Fix 2 — LDR→main promote for `deployment-service@1424037`** (pending), then redeploy Cloud Run image to activate the
`PREFIX_KILL_MINUTES` per-prefix threshold. Resume `uts-prod-dp-heartbeat-watcher-cron` after image is in Cloud Run.

**Fix 3 — Fleet monitoring agents must verify ALL THREE signals** before any `gcloud instances delete` call on
`canonical-migration-` prefix VMs:

1. Heartbeat blob mtime vs per-prefix threshold
2. run.log mtime vs per-prefix threshold
3. Manifest generation unchanged for >90 min → proceed with human confirmation, not autonomous delete

## Triage Disposition

- **Scope**: cross-cutting (affects all `canonical-migration-` prefix VM operations)
- **Blocker for**: defi_satellite_ao_dispatch_batch9 gas_fees purge
- **Next action**: Fix 1 → ship to LDR → promote → redeploy → resume heartbeat cron. Then Fix 3 as a codex rule update.
- **Operator notification**: REQUIRED (cross-agent HARD RULE violation, repeated pattern)
