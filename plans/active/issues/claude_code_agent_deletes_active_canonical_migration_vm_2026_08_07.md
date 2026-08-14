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
  - /plans/archive/2026_08/watchdog_kill_events_deployment_gaps_2026_08_05.md
  - /plans/active/issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md
context_scope:
  - deployment-service/scripts/vm/setup-data-pipeline-vm.sh
  - deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py
  - /codex/05-infrastructure/vm-launcher-runbook.md
created: 2026-08-07
parent_epic: infrastructure_master
assigned_vm: planning
source: slot-8-infra-dispatch-batch9-018
resolved_by: ""
locked_by: ""
execution_scope: orchestrator-agent
assigned_role: infra
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

## Todos

- [x] [INFRA] P0. ✅ **Fix 1 (URGENT) — heartbeat sidecar SIGPIPE guard.** Target:
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`, the `_hb_prefix` vm-life-emitter loop construction
      (currently ~line 1204:
      `_hb_prefix="( while true; do echo \"PIPELINE_HEARTBEAT vm=${VM_NAME_SELF} ag=${VM_ASSET_GROUP} task=${VM_TASK:-} source=vm-life-emitter ts=\$(date -u +%Y-%m-%dT%H:%M:%SZ)\"; sleep 60; done ) & __DP_HB_PID=\$!; trap 'kill \"\$__DP_HB_PID\" 2>/dev/null || true' EXIT; "`).
      This loop shares stdout with the tee'd main process; when the GCS log uploader closes the pipe (possibly on a 60s
      flush cycle) the next `echo` gets SIGPIPE and terminates the subshell, making the VM look stale to
      heartbeat-staleness checks — root cause of all 4 kills in the table above. Add a `trap '' SIGPIPE` guard around
      the loop body:

  ```bash
  # In the vm-life-emitter loop:
  ( trap '' SIGPIPE; while true; do echo "PIPELINE_HEARTBEAT ..." 2>/dev/null || true; sleep 60; done ) &
  ```

  Preserve the existing `PIPELINE_HEARTBEAT vm=... ag=... task=... source=vm-life-emitter ts=...` payload and the
  existing `__DP_HB_PID` / `trap ... EXIT` kill wiring — only add the SIGPIPE guard, do not restructure the rest of the
  construction. Ship via quickmerge + verify CI green. — deployment-service@3b25aae4 (QG green, verified on
  origin/live-defi-rollout)

- [x] [INFRA] P0. ✅ **Fix 2 — LDR→main promote `deployment-service@1424037`
      (`14240378194039fe5a2cfb5e2d86dbed6cffe8d8`, ships `PREFIX_KILL_MINUTES = {"canonical-migration-": 90.0}` +
      `_resolve_kill_minutes()` in `heartbeat_stall_watcher.py`), then redeploy the Cloud Run image.** The fix is
      already on `live-defi-rollout` (shipped during dispatch #8, `quality-gates.sh` green — see
      `/plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md`), but the live `deployment-api:latest` Cloud Run
      image was built at 09:31Z on 2026-08-07, pre-fix — the per-prefix `canonical-migration-` 90-minute threshold is
      therefore NOT active in production. Promote LDR→main via the standard pipeline (`sit-gate/fleet-green` +
      `quality-gates-v2` + quickmerge-provenance — the only 3 blocking gates), redeploy the Cloud Run image, verify
      `status.traffic` shows the new revision live (not just a green build), then resume the paused
      `uts-prod-dp-heartbeat-watcher-cron` (paused as dispatch-#10 mitigation). — deployment-service@1157abe1 (squash
      promote, PREFIX_KILL_MINUTES verified on origin/main; `uts-shared-deployment-api-00464` at 100% traffic, image
      sha256:7042ab88 built 2026-08-08T00:24Z; cron ENABLED, last run 2026-08-08T03:30Z)

- [x] [INFRA] P1. ✅ **Fix 3 — codify a `canonical-migration-` prefix carve-out on the VM-delete guardrail** in the two
      role files that mirror it: `agents/infra.md` STEP 0.65 and `agents/data_engineering.md` STEP 0.55. Both currently
      require confirming genuine staleness via ALL of (1) the heartbeat blob mtime vs. the watchdog's per-prefix
      threshold, (2) a `run.log` tail/mtime (active writes in the last few minutes = alive), and (3) the manifest shard
      mtime (is it still advancing) — but treat a pass on all 3 as sufficient to delete. Add, to both files: for
      `canonical-migration-` prefix VMs specifically, even when all 3 signals read stale, if the manifest generation has
      been unchanged for **>90 minutes**, that is NOT sufficient to autonomously delete — escalate for human
      confirmation instead. Rationale to include: these VMs run large-index download-then-filter-then-write operations
      where the manifest generation is EXPECTED to sit unchanged through the whole download phase (confirmed in this
      incident: the VM was 22 minutes into a `blob.download_as_bytes(timeout=900)` call when killed, manifest generation
      genuinely unchanged, not evidence of staleness) — a frozen run.log/heartbeat alone is not dispositive the way it
      is for other fleet VM classes. — unified-trading-pm@4fbb6113e (agents/infra.md STEP 0.65 +
      agents/data_engineering.md STEP 0.55 updated)

## Triage Disposition

- **Scope**: cross-cutting (affects all `canonical-migration-` prefix VM operations)
- **Blocker for**: defi_satellite_ao_dispatch_batch9 gas_fees purge — RESOLVED via a different path (dispatch #11 ran
  directly on the planning VM, bypassing the VM-kill vector; manifest confirmed 0 of 12,425 TARGET rows, GCS 0 objects,
  per `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s Progress Log). The acute blocker is gone; the systemic safety
  gap below (Fixes 1 and 3) is generic to ALL future `canonical-migration-` VM dispatches and remains live/unaddressed.
- **Operator notification**: REQUIRED (cross-agent HARD RULE violation, repeated pattern)

## Resolution

- [x] [INFRA] P0 (URGENT). ✅ Heartbeat sidecar SIGPIPE guard: wrap the `vm-life-emitter` loop in `trap '' SIGPIPE`
      (exact snippet in "Required Fixes" Fix 1 above) — confirmed in
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` line 1204. deployment-service@3b25aae4, QG green,
      verified on origin/live-defi-rollout.
- [x] [INFRA] P0. ✅ LDR→main promote `deployment-service@14240378`, redeploy the Cloud Run image to activate
      `PREFIX_KILL_MINUTES`, then resume `uts-prod-dp-heartbeat-watcher-cron`. Content-verified on `origin/main` via
      squash promote `1157abe1` (Promoted-From-LDR: f514b6a0). `PREFIX_KILL_MINUTES` grep returns 3 lines on main. Image
      sha256:7042ab88 built 2026-08-08T00:24Z deployed to `uts-shared-deployment-api-00464` (100% traffic, created
      2026-08-08T00:28Z). `uts-prod-dp-heartbeat-watcher-cron` ENABLED in asia-northeast1, last run 2026-08-08T03:30Z,
      running every 5 min successfully.
- [x] [INFRA] P0. ✅ Fleet monitoring agents must verify ALL THREE liveness signals (heartbeat blob mtime, run.log
      mtime, manifest generation advancing) before any `gcloud instances delete` on `canonical-migration-` prefix VMs —
      fold the SIGPIPE-can-fake-a-frozen-run.log nuance into `/codex/05-infrastructure/vm-launcher-runbook.md` (the
      underlying 3-signal HARD RULE already exists there; what's missing is this doc's specific nuance). —
      unified-trading-pm@762008c33

## Progress Log

- **slot-7 Fix 2 verification 2026-08-08T03:35Z**: Fix 2 (PREFIX_KILL_MINUTES promote) confirmed complete. Squash
  promote `1157abe1` (Promoted-From-LDR: f514b6a0) carried the content of `14240378` to `origin/main` — grep for
  `PREFIX_KILL_MINUTES` in `deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py` on main returns 3
  matches (lines 110-117). Image sha256:7042ab88 built 2026-08-08T00:24Z (11h after fix commit at 13:27Z on 2026-08-07)
  deployed to Cloud Run service `uts-shared-deployment-api-00464-94g` with 100% traffic (created 2026-08-08T00:28Z).
  Cloud Run job `uts-prod-dp-heartbeat-watcher` uses `deployment-api:latest` (same digest, modified 2026-08-08T00:28Z).
  `uts-prod-dp-heartbeat-watcher-cron` scheduler is ENABLED in asia-northeast1 (schedule: `*/5 * * * *`), last ran
  2026-08-08T03:30Z successfully. Flipped Fix 2 checkboxes in Todos and Resolution sections. Fix 3 (codex guardrail
  update) remains open.

- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: KEEP-NA, valid — doc self-flags "Operator notification:
  REQUIRED (cross-agent HARD RULE violation, repeated pattern)," the 5th VM-kill in this saga; continued human
  visibility is appropriate even though the 3 fixes are individually fairly bounded. Hygiene fix: this doc had ZERO
  checkbox syntax anywhere despite carrying real P0 "Required Fixes" work in prose only — per CLAUDE.md's "every
  follow-up is a `- [ ]` todo, never prose" HARD RULE, converted the 3 Required Fixes into a new "## Resolution" section
  with tracked checkboxes (content unchanged, evidence live-reverified: Fix 2's commit confirmed still not on
  `origin/main`; no SIGPIPE guard found anywhere in deployment-service or market-tick-data-service via targeted grep).
  This is a small, clear, in-file fix per the findings-triage HARD RULE, not a reclassification — the doc stays NA
  (operator-notification flag above is dispositive on its own).
- **context-scout 2026-08-14**: populated context_scope (3 entries).
