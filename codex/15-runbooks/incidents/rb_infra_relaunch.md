---
doc_type: codex-runbook
title: RB-INFRA-RELAUNCH — Registry-driven VM relaunch (escalate-to-orchestrator)
summary:
  Runbook for a planning-VM worker spawned by an escalate-to-orchestrator repository_dispatch (action=relaunch_vm) to
  relaunch a failed/stalled/OOM'd data VM — read DeploymentsRegistry + resolve_launcher_for_vm, re-run the launcher,
  verify STARTED@T+60s / PROGRESS@T+10min; bounded ≤2 relaunches/(vm-prefix,day) then page.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [admin, engineer]
tags: [runbook, incident, infrastructure, vm, data-pipeline, orchestrator, self-healing]
related: [/codex/15-runbooks/incidents/rb_data_001.md, codex/05-infrastructure/data-pipeline-alerts.registry.yaml]
created: 2026-06-23
owner: ikenna@odum-research.com
cadence: On-demand (fired by a data-pipeline auto_recover hand-off)
verifier: test_dp_recovery_actuators.py (dispatch-fires + payload-binding tests)
last_executed: never
code_refs:
authoritative_for: [How a planning-VM worker relaunches a failed/stalled/OOM'd data VM from the registries]
referenced_by:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
  ]
---

# RB-INFRA-RELAUNCH — Registry-driven VM relaunch via escalate-to-orchestrator

## When you get here

A `repository_dispatch` `escalate-to-orchestrator` (`wall_type=data_pipeline_failure`) spawned you with
`client_payload.action=relaunch_vm`. This means a data-pipeline fleet monitor (exit-code / heartbeat-stall) detected a
VM that **exited non-zero (OOM=137), stalled, or whose consolidator is down**, and its in-image `auto_recover` actuator
**could not actuate the relaunch** — because the monitor runs in the `deployment-api` Cloud Run image, which does NOT
carry `scripts/recovery` + `scripts/vm` (the 2026-06-23 decision: relaunch on a planning-VM slot, not by packaging
launchers into the monitor image). **You** have the full env, so you do the relaunch.

## The structured binding you were handed (`client_payload`)

| Field               | Meaning                                                                               |
| ------------------- | ------------------------------------------------------------------------------------- |
| `action`            | `relaunch_vm`                                                                         |
| `vm_name`           | the failed VM's name (its prefix → launcher)                                          |
| `relaunch_launcher` | the `deployment-service/scripts/vm/launch-*.sh` to re-run (may be empty → resolve it) |
| `deployment_id`     | the `DeploymentsRegistry` row id (carries asset_group/task/mode/dates)                |
| `asset_group`       | `cefi`/`defi`/`tradfi`/`sports`/`prediction`                                          |

The `context` field repeats this in prose; **prefer the structured fields**.

## Procedure (deterministic — read the registries, do NOT re-derive args by hand)

1. **Read the registry row** for the failed deployment to recover its launch tags:
   `deployment_service.deployments_registry.DeploymentsRegistry().get(deployment_id)` → `asset_group` / `task` / `mode`
   / `start_date` / `end_date`. (If `deployment_id` is absent, fall back to the most-recent active/archive row for
   `vm_name`.)
2. **Resolve the launcher** if `relaunch_launcher` is empty:
   `deployment_service.data_pipeline_monitors.launcher_registry.resolve_launcher_for_vm(vm_name)` (longest-prefix
   match). A `None` result = an unrecoverable prefix → STOP, file an issue, page (do not guess a launcher).
3. **Re-run the launcher** from `deployment-service/scripts/vm/<relaunch_launcher>` with the registry's tags
   (`VM_ASSET_GROUP=<asset_group>`, the task/mode/date metadata the launcher expects). The launcher streams durable GCS
   logs + registers a deployment heartbeat, so the relaunch is **never fire-and-forget**.
4. **Verify STARTED at T+60s** (deployment-registry heartbeat + `gcloud compute instances describe <vm_name>` = RUNNING)
   and **PROGRESS at T+10min** (per the no-fire-and-forget rule). If it re-fails the SAME way twice, the shard is wedged
   (network partition / unbounded HTTP hang) — STOP relaunching, file an issue to fix the root cause (almost always an
   outbound call lacking `timeout=`).

## Bounds + safety

- The original in-image actuators bound relaunches to **≤2 / (vm-prefix, day)** — honour the same: if the registry
  archive shows ≥2 relaunches of this prefix today, do NOT relaunch again; page the operator. **Root-cause-diagnosed
  carve-out (ruled 2026-08-02, `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 25):**
  the ≤2/day bound resets for a relaunch that is not blind retry — root cause diagnosed, a fix shipped, AND this exact
  launch is the first attempt made WITH that fix live (i.e. genuinely new information, not a 3rd identical guess). Page
  the operator with the diagnosis + shipped fix reference before using the carve-out, don't invoke it silently.
- Protective/fail-safe actions are autonomous; a destructive `manual_unkill`-class action is human-only (see
  `/codex/04-architecture/autonomous-recovery-matrix.md`).

## Why this exists (don't "fix" it by packaging scripts into the monitor)

The monitor image deliberately stays light (no gcloud/launchers). Relaunch capability lives where the auth + tools
already are (a planning-VM slot). Migrate to a dedicated relaunch VM later if slot contention warrants — the dispatch
contract (this runbook + the `client_payload`) is stable across that move. SSOT:
`/codex/05-infrastructure/data-pipeline-alerts.md` § "Self-heal actuator layer".
