---
doc_type: issue
title:
  DP-VM-003 heartbeat stall on sports-manifest-rescan-20260817-165755 — relaunch budget for this VM-name-group already
  2/2 today; launcher registry marks this prefix non-auto-relaunchable by design; a live, healthy successor VM already
  covers the work; no relaunch taken
summary: >-
  A DP_VM_STALL (DP-VM-003, WARN) escalation (agt-ebee7a) reported `sports-manifest-rescan-20260817-165755` heartbeat
  19m stale, with an explicit dispatch-time instruction NOT to relaunch (the `sports-manifest-rescan-` group had already
  hit its `RB-INFRA-RELAUNCH` bound of 2/2 relaunch dispatches earlier today) and to check for an existing open issue +
  page the operator instead.

  No existing issue doc named this `vm_name` (grepped `plans/active/issues/` for the vm_name and `DP-VM-003` — 0 hits on
  this specific incarnation; several unrelated `dp_vm_003_*` docs exist for other VMs/asset_groups).

  `gcloud compute instances list --filter="name~'^sports-manifest-rescan'"` shows the stalled VM is **no longer in the
  live fleet at all** — only `sports-manifest-rescan-20260818-020336` (RUNNING, created `2026-08-18T01:08:10Z`, ~7h
  after the stalled VM's name-timestamp) is present. Read via the UTL/GCS SDK helpers
  (`deployment_service.data_pipeline_monitors._gcs.run_log_signals`, no subprocess `gcloud`/`gsutil`):
  - `sports-manifest-rescan-20260817-165755`: pipeline-heartbeat / run.log age **529.99 min** stale (~8.8h) — long dead,
    not merely slow.
  - `sports-manifest-rescan-20260818-020336`: pipeline-heartbeat / run.log age **1.28 min** — fresh, actively running.
  - Neither VM has a `LAUNCH_PARAMS.json`/`PROGRESS.json` in `deployment-scripts-<project>` — expected for this
    launcher class, not a read failure: `deployment_service/data_pipeline_monitors/launcher_registry.py` maps
    `"sports-manifest-rescan-": None  # coordinator+chunk fan-out (multi-shape) — file_issue` — i.e. this prefix is
    **registry-marked non-auto-relaunchable by design**, independent of and in addition to today's 2/2 daily-bound
    exhaustion. `RelaunchStalledVm`/`RelaunchPreemptedVm` cannot deterministically resolve a launcher + resume args for
    a coordinator+chunk fan-out VM the way they can for a single-shape backfill VM — every stall in this VM class always
    falls through to `file_issue`, per `rb_infra_relaunch.md` step 2 ("A `None` result = an unrecoverable prefix →
    STOP, file an issue, page (do not guess a launcher)").
  - No suppression marker at `vm-census/relaunch-paged/vm/sports-manifest-rescan-20260817-165755.json` (checked via
    `StorageClient.blob_exists`) — this stall was never auto-relaunch-adjudicated (consistent with the registry's
    `None` entry routing it straight to `file_issue` rather than through `RelaunchStalledVm`).
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [dp-vm-003, heartbeat-stall, sports-manifest-rescan, relaunch-budget-exhausted, non-auto-relaunchable, no-op-verified]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_003_mdps_backfill_cefi_181733_already_superseded_2026_08_16.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
    deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh,
  ]
created: "2026-08-18"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-ebee7a (wall_type=data_pipeline_failure, dispatched to slot 11, 2026-08-18) — context: "WARN
  DP_VM_STALL (DP-VM-003) — VM sports-manifest-rescan-20260817-165755 stalled — heartbeat 19m stale. ... DO NOT RELAUNCH
  ... group sports-manifest-rescan- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound). Check for an
  existing open issue doc and page the operator instead of relaunching again."
---

# DP-VM-003 — sports-manifest-rescan-20260817-165755 stalled, gone, budget-exhausted, non-auto-relaunchable — no-op, operator paged

## What happened

- `sports-manifest-rescan-20260817-165755` went WARN-stale on heartbeat (19m at alert time, agt-ebee7a). This worker's
  read (via GCS SDK helpers, later) found it **~530 min (~8.8h) stale** on both liveness signals and **absent from the
  live GCE fleet** — genuinely gone, not slow.
- The dispatching escalation carried an explicit **DO NOT RELAUNCH**: the `sports-manifest-rescan-` VM-name group had
  already hit `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix, day)` bound earlier today.
- Independently of that daily bound, `launcher_registry.LAUNCHER_FOR_VM_PREFIX["sports-manifest-rescan-"]` is `None`
  with an explicit comment — `coordinator+chunk fan-out (multi-shape) — file_issue` — meaning `resolve_launcher_for_vm`
  can never deterministically resolve a relaunch for this VM class in the first place; every stall in this prefix
  family routes to `file_issue` by the runbook's own step 2, budget or no budget.
- A live, healthy successor already exists: `sports-manifest-rescan-20260818-020336`, `RUNNING`, created
  `2026-08-18T01:08:10Z` (~7h after the stalled VM's own name-timestamp), heartbeat/run.log **1.28 min** old at read
  time — actively producing progress. No suppression marker exists for the old VM name (this stall was never routed
  through the auto-relaunch adjudicator, consistent with the registry's `None` entry).

## Decision

**No relaunch taken** — both because it was explicitly forbidden by the dispatching escalation (budget exhausted) and
because the launcher registry marks this VM class as fundamentally non-auto-relaunchable (coordinator+chunk fan-out,
no deterministic single-launcher resume). A live, healthy, differently-named successor is already running and
producing fresh heartbeats, so this incident reads as **already self-resolved** — the coordinator/orchestration layer
above this VM class evidently re-dispatched a fresh coordinator+fan-out run on its own schedule, independent of the
stalled-VM relaunch machinery.

**Operator paged** (per the dispatching escalation's explicit instruction) via this issue doc + a `/blocked`
informational post from this worker's slot (see Progress Log) — no existing open issue doc named this `vm_name` before
this one.

## Todos

- [ ] [SCRIPT] P3. `sports-manifest-rescan-` is the only launcher-registry prefix mapped to `None` purely because of its
      coordinator+chunk fan-out shape (not a one-off like `cefi-rogue-`) — evaluate whether it's worth teaching
      `resolve_launcher_for_vm`/`RelaunchStalledVm` to resolve the COORDINATOR's own launcher (distinct from its
      per-chunk children) so a genuine coordinator stall (as opposed to a benign chunk-level restart, which this
      incident may actually be) gets a real auto-relaunch path instead of always falling to manual `file_issue` triage.
- [ ] [SCRIPT] P3. Confirm (Cloud Logging / the coordinator's own scheduling code, not investigated in this one-shot
      pass) whether `sports-manifest-rescan-20260818-020336` was dispatched by a periodic coordinator re-trigger (the
      benign, expected case implied by the evidence above) or is itself evidence of a duplicate/overlapping rescan
      fan-out — if the latter, check for wasted/duplicate compute across the two runs' chunk windows.

## Progress Log

- 2026-08-18 (agt-ebee7a, slot 11): Diagnosed via GCS SDK reads (`deployment_service.data_pipeline_monitors._gcs`, no
  subprocess `gcloud`/`gsutil` for object ops) + `gcloud compute instances list` for fleet membership. Confirmed
  `...165755` gone from the live fleet, ~8.8h stale on both liveness signals, no `LAUNCH_PARAMS.json`/`PROGRESS.json`
  (expected — this launcher class never writes them). Confirmed `launcher_registry.py` maps
  `"sports-manifest-rescan-"` → `None` with an explicit `file_issue` comment, independent of today's 2/2 daily-bound
  exhaustion. Confirmed `...020336` is a live, healthy, actively-heartbeating successor. No relaunch attempted (forbidden
  by dispatch + registry-non-relaunchable + a healthy successor already covers it). Filed this issue (no pre-existing
  doc named this vm_name) and posted a `/blocked` informational page to main/operator per the dispatch instruction.
  `/done` posted with `one_shot_complete: true`.
