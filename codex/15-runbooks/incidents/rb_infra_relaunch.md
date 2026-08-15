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
last_executed:
  2026-08-15 (DP-VM-008 escalation agt-9c7b77, cefi-binance-futures-2026-heavy — verified an already-succeeded
  auto-recovered relaunch, corrected two stale doc claims in the same pass)
code_refs:
authoritative_for: [How a planning-VM worker relaunches a failed/stalled/OOM'd data VM from the registries]
referenced_by:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
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

1. **Read the VM's own durable launch/progress record to recover its launch tags** —
   `deployment_service.deployments_registry.DeploymentsRegistry` does NOT exist in `deployment-service` (confirmed
   2026-08-15, DP-VM-008 escalation agt-9c7b77 — a repo-wide grep for `deployments_registry` returns nothing); the real
   SSOT is the per-VM GCS state the actuators themselves read:
   `deployment_service.data_pipeline_monitors._gcs.read_launch_params(storage_client, bucket, vm_name)` →
   `LAUNCH_PARAMS.json` (the exact env the VM was launched with — venue/year/group filters, instrument ids) and
   `..._gcs.read_progress_checkpoint(storage_client, bucket, vm_name)` → `PROGRESS.json` (`last_completed_date` /
   `monotonic`, for resume-from-checkpoint). `bucket = f"deployment-scripts-{project}"`. `asset_group` /
   `relaunch_launcher` come from the finding's `client_payload` directly, not a lookup. This is exactly what
   `deployment_service.data_pipeline_monitors.escalation._recover_preempted_vm` / `RelaunchPreemptedVm.relaunch()`
   (`scripts/recovery/relaunch_backfill_vm.py`) already do in-band — prefer invoking that actuator directly (or its
   exact GCS reads) over hand-deriving args.
2. **Resolve the launcher** if `relaunch_launcher` is empty:
   `deployment_service.data_pipeline_monitors.launcher_registry.resolve_launcher_for_vm(vm_name)` (longest-prefix
   match). A `None` result = an unrecoverable prefix → STOP, file an issue, page (do not guess a launcher).
3. **Check for a supervising wrapper before relaunching.** Some VM families are already driven by a self-managed retry
   wrapper — grep `deployment-service/scripts/vm/` for a `*-historical-*` or loop-style caller of the resolved launcher
   (e.g. `launch-expected-universe-v2-historical-backfill-vm.sh` wraps `launch-expected-universe-v2-vm.sh`). If one
   exists, check `DeploymentsRegistry` for recent same-prefix launches: an actively-cycling wrapper is already retrying
   the same window sequentially (respecting its own singleton lock) on its own known-retriable exit codes. A manual
   out-of-band relaunch in that case races the wrapper and risks a duplicate concurrent run — do NOT relaunch; confirm
   the wrapper is still converging and stand down instead. Mirrors the "if it re-fails the SAME way twice, STOP" pattern
   below — easy to skip past under dispatch pressure, so check this explicitly, not just when a relaunch fails.
   Root-cause example: `/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`.
4. **Re-run the launcher** from `deployment-service/scripts/vm/<relaunch_launcher>` with the registry's tags
   (`VM_ASSET_GROUP=<asset_group>`, the task/mode/date metadata the launcher expects). The launcher streams durable GCS
   logs + registers a deployment heartbeat, so the relaunch is **never fire-and-forget**.
5. **Verify STARTED at T+60s** (deployment-registry heartbeat + `gcloud compute instances describe <vm_name>` = RUNNING)
   and **PROGRESS at T+10min** (per the no-fire-and-forget rule). If it re-fails the SAME way twice, the shard is wedged
   (network partition / unbounded HTTP hang) — STOP relaunching, file an issue to fix the root cause (almost always an
   outbound call lacking `timeout=`).

## Bounds + safety

- The OOM/exit-137 actuator (`RelaunchBackfillVm`) bounds relaunches to **≤2 / (vm-prefix, day)** — honour the same for
  that class: if the registry archive shows ≥2 relaunches of this prefix today, do NOT relaunch again; page the
  operator. **The PREEMPTED actuator (`RelaunchPreemptedVm`, DP-VM-008/this runbook) has its OWN, more generous budget —
  `_MAX_PREEMPTION_RELAUNCHES_PER_DAY = 48`** (confirmed 2026-08-15 by reading `relaunch_backfill_vm.py` directly) — a
  SPOT VM legitimately preempts far more often than an OOM crash-loops, so do not apply the ≤2/day figure to a
  preemption relaunch; the actuator enforces its own bound atomically. **Root-cause-diagnosed carve-out (ruled
  2026-08-02, `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 25):** the ≤2/day OOM
  bound resets for a relaunch that is not blind retry — root cause diagnosed, a fix shipped, AND this exact launch is
  the first attempt made WITH that fix live (i.e. genuinely new information, not a 3rd identical guess). Page the
  operator with the diagnosis + shipped fix reference before using the carve-out, don't invoke it silently.
- **A prior FAILED relaunch attempt for the SAME vm_name pages CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH` and durably
  SUPPRESSES further automated retries for that exact vm_name** (`RelaunchPreemptedVm._already_paged`, a
  page-once-per-VM-name marker in `gs://deployment-scripts-<project>/vm-census/relaunch-paged/vm/<vm_name>.json` — check
  its `last_modified` via `gcs_describe_object` to see when/whether an attempt already ran). This is BY DESIGN — it
  hands the retry decision to whoever reads the page (you). Before hand-relaunching: **check the live VM fleet
  (`gcloud compute instances list`, filtered to the launcher's VM-name prefix) for an ALREADY-RUNNING replacement** — a
  later automated sweep (once the earlier blocker, e.g. the launcher's own `tardis_concurrency_guard` refusing while
  another Tardis consumer held the slot, cleared) may have already relaunched successfully under a fresh timestamped VM
  name (each launch mints a new name, so the suppression on the OLD name never blocks it). Confirmed live 2026-08-15
  (this escalation): the OLD `cefi-binance-futures-2026-heavy-20260814-161717` was suppressed (`already_adjudicated`,
  paged at `00:01:19Z`), but `cefi-binance-futures-2026-heavy-20260815-002451` was already RUNNING with matching
  `LAUNCH_PARAMS.json` and an advancing `PROGRESS.json`/`run.log` — launching a second VM here would have violated the
  Tardis 1-concurrent-VM cap and duplicated the shard. Verify a genuine replacement exists (matching launch params +
  advancing checkpoint/run.log) before concluding the relaunch is done; if none exists, proceed with the manual relaunch
  as normal.
- Protective/fail-safe actions are autonomous; a destructive `manual_unkill`-class action is human-only (see
  `/codex/04-architecture/autonomous-recovery-matrix.md`).

## Why this exists (don't "fix" it by packaging scripts into the monitor)

The monitor image deliberately stays light (no gcloud/launchers). Relaunch capability lives where the auth + tools
already are (a planning-VM slot). Migrate to a dedicated relaunch VM later if slot contention warrants — the dispatch
contract (this runbook + the `client_payload`) is stable across that move. SSOT:
`/codex/05-infrastructure/data-pipeline-alerts.md` § "Self-heal actuator layer".
