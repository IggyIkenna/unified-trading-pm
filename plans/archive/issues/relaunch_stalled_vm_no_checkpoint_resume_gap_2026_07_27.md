---
doc_type: issue
title: >-
  RelaunchStalledVm (the DP_VM_STALL auto-recover actuator) has ZERO checkpoint/resume logic — every stall-triggered
  relaunch replays the launcher blind, unlike RelaunchPreemptedVm's checkpoint-aware path
summary: >-
  Discovered as a byproduct of reconciling
  /plans/active/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md's 6 todos, 2026-07-27. That doc's own
  todo 2 evidence text already flagged (in passing) that `RelaunchStalledVm` "has NO checkpoint/resume logic at all,"
  but this was never converted into its own tracked todo or issue doc. Independently re-verified this session by a
  full-file read of `deployment-service/scripts/recovery/relaunch_stalled_vm.py`: `RelaunchStalledVm.relaunch()` takes
  only `launcher`, `asset_group`, and an opaque `launcher_env` dict, and does nothing but budget-check + re-invoke the
  launcher subprocess with that env — no `read_progress_checkpoint()` call, no `PROGRESS.json`/`vm-logs/` reference, no
  `START_DATE`/day-frontier override anywhere in the 278-line file. This is the SAME actuator that fires for EVERY VM
  matched by `heartbeat_stall_watcher.py`'s `_is_backfill_vm()` — not just the canonical-migration family added by that
  doc's todo 2, but also the pre-existing `af-backfill-*`/`tradfi-bf-*`/`tm-backfill`/`fs-backfill` families. So today,
  a STALL-triggered relaunch (VM still running or in-VM-watchdog-killed, not GCE-preempted) always replays the ORIGINAL
  launch params from scratch, regardless of any PROGRESS.json checkpoint that may exist for that VM — in contrast to
  `RelaunchPreemptedVm` (`relaunch_backfill_vm.py`), which already reads that checkpoint and overrides `START_DATE`
  accordingly. This directly bears on the operator's "spot vms should auto recover at large from where they left off
  too" ask: the answer is YES for genuine preemption, NO for stall-triggered relaunch, and this doc is the tracked
  follow-up for the NO half.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags:
  [
    vm-monitoring,
    hung-vm,
    stall-detection,
    spot-preemption,
    checkpoint-resume,
    deployment-observability,
    relaunch-stalled-vm,
  ]
related:
  [
    /plans/active/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /plans/archive/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
assigned_role: infra
source: >-
  Surfaced while reconciling migration_vm_hung_detection_monitoring_gap_2026_07_27.md's todos against the actual shipped
  code, 2026-07-27 — a follow-up/reconciliation session, not an implementation session. Re-verified independently this
  session by a full read of `deployment-service/scripts/recovery/relaunch_stalled_vm.py` (not trusted from the parent
  doc's in-passing note) plus a `grep -n "checkpoint\|PROGRESS\|resume\|START_DATE"` over the file (zero hits) and a
  cross-check of `escalation.py` confirming `DP_VM_STALL` routes to this actuator's `auto_recover` tier unconditionally.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by: deployment-service@02ac568
last_updated: 2026-07-30
---

> **🗄️ ARCHIVED 2026-07-30** — `status: resolved`, `resolved_by: deployment-service@02ac568`
> (`fix(dp-recovery): file OOM-investigate issue doc + checkpoint-resume for stalled VMs`). Found ALREADY SHIPPED on
> inspection: `RelaunchStalledVm.relaunch()` carries the checkpoint-read/`START_DATE`-override step, wired through
> `escalation.py::_recover_stalled_vm`, with 5 covering unit tests incl. the explicit no-regression-for-no-checkpoint
> case. Done-when satisfied verbatim; no new code needed.

# RelaunchStalledVm has no checkpoint/resume logic — stall-triggered relaunches replay blind

> Investigation-only record (this doc). No code was changed while authoring this doc. `assigned_vm: NA`,
> `execution_scope: local-only` — a human decides when to pick up the fix below.

## What I found

`deployment-service/scripts/recovery/relaunch_stalled_vm.py`, class `RelaunchStalledVm` (lines 106-227), is the
auto-recover actuator for `DP_VM_STALL` findings (fired by `heartbeat_stall_watcher.py` when a heartbeat or run.log goes
stale past its threshold; `escalation.py` line 371 docstring: "Auto-recover `DP_VM_STALL` → re-launch the
watchdog-killed stalled VM"). Its `relaunch()` method (lines 131-226):

- Takes `vm_name`, `launcher`, `asset_group`, and `launcher_env: dict[str, str] | None` as its only inputs.
- Budget-checks (`_MAX_RELAUNCHES_PER_DAY = 2` per vm-prefix/day) then either pages (`status=PAGE`, `budget_exceeded`)
  or calls `self._run_launcher(launcher, env=env)` with `env = launcher_env or {}` — a straight passthrough, no
  augmentation.
- `grep -n "checkpoint\|PROGRESS\|resume\|START_DATE" deployment-service/scripts/recovery/relaunch_stalled_vm.py` →
  **zero hits.** No `read_progress_checkpoint()` call, no `vm-logs/{vm}/PROGRESS.json` reference anywhere in the file.

Contrast with `RelaunchPreemptedVm` (`deployment-service/scripts/recovery/relaunch_backfill_vm.py`, the actuator for the
DISTINCT `DP_VM_PREEMPTED` finding), which DOES call `_gcs.read_progress_checkpoint()` and overrides `START_DATE` in the
relaunch env when a checkpoint exists (confirmed by the SPOT-recovery investigation already recorded in
`migration_vm_hung_detection_monitoring_gap_2026_07_27.md`'s todo 6 evidence, and independently re-confirmed this
session).

`DP_VM_STALL` fires for EVERY VM `heartbeat_stall_watcher.py`'s `_is_backfill_vm()` matches — this is not scoped to
canonical-migration VMs. Before `migration_vm_hung_detection_monitoring_gap_2026_07_27.md`'s todo 2 shipped, that
already included `af-backfill-*`, `tradfi-bf-*`, `tm-backfill`, `fs-backfill`; todo 2 added the canonical-migration
family on top. So the blind-relaunch gap documented here is **broader than the parent doc's canonical-migration scope**
— it is a pre-existing gap for the ORIGINAL backfill families too, just newly surfaced during this reconciliation pass
because the operator's SPOT-recovery question ("does it resume from where it left off") forced a direct comparison
between the two actuators.

## Net effect

A VM whose workload is genuinely hung (not GCE-preempted) gets killed by the in-VM stall watchdog, detected by
`heartbeat_stall_watcher.py`, and auto-relaunched by `RelaunchStalledVm` — but that relaunch always restarts from the
ORIGINAL launch parameters, even if a `vm-logs/{vm}/PROGRESS.json` checkpoint exists recording real progress made before
the hang. Any per-file idempotent-skip logic in the underlying script (e.g.
`migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s `rows_changed == 0` skip) still avoids re-WRITING
already-migrated data, but the full re-discovery/re-download/re-parse cost of the entire prior scope is paid again on
every stall-triggered relaunch — the same class of waste `migration_vm_hung_detection_monitoring_gap_2026_07_27.md`'s
todo 6 fixed for the PREEMPTION path, still present here for the STALL path.

## What this is NOT

- **Not a duplicate of todo 6** in the parent doc. Todo 6 fixed the SCRIPT's own missing checkpoint EMISSION (the Python
  migration script never called `record_vm_progress()`). This doc is about the CONSUMING actuator on the stall-relaunch
  side (`RelaunchStalledVm`) never reading that checkpoint at all — a gap that persists even now that the script emits
  one, because this actuator's code path doesn't look for it.
- **Not itself a fix.** No code was changed while authoring this doc.

## Recommendation (not yet implemented)

Give `RelaunchStalledVm.relaunch()` the same checkpoint-read/`START_DATE`-override step `RelaunchPreemptedVm.relaunch()`
already has — likely by factoring that logic out of `relaunch_backfill_vm.py` into a shared helper both actuators call,
since the checkpoint format (`vm-logs/{vm}/PROGRESS.json`, monotonic-gated) and read path (`_gcs.py`'s
`read_progress_checkpoint()`) are already identical infrastructure. Scope this as its own plan/todo when picked up — it
touches a shared actuator used by every `_is_backfill_vm()`-matched VM class, so the blast-radius rule applies: verify
the change doesn't regress the (already-working) budget/paging behavior for VMs that have no checkpoint at all (the
common case today, since checkpoint emission is opt-in per script).

## Evidence / how to reproduce

```bash
# RelaunchStalledVm — confirm zero checkpoint/resume logic
grep -n "checkpoint\|PROGRESS\|resume\|START_DATE" deployment-service/scripts/recovery/relaunch_stalled_vm.py
# expect: zero matches

# Contrast — RelaunchPreemptedVm DOES have this logic
grep -n "read_progress_checkpoint\|START_DATE" deployment-service/scripts/recovery/relaunch_backfill_vm.py
# expect: non-zero matches

# Confirm DP_VM_STALL routes to RelaunchStalledVm unconditionally (auto_recover tier)
grep -n "DP_VM_STALL" deployment-service/deployment_service/data_pipeline_monitors/escalation.py
```

## What's NOT done / follow-up needed

- [x] ✅ [HUMAN] P2. **DONE — already shipped, found already-complete on inspection.** `RelaunchStalledVm.relaunch()`
      (`deployment-service/scripts/recovery/relaunch_stalled_vm.py`) already carries the checkpoint-read/`START_DATE`-
      override step (`checkpoint`/`launch_env` params, `resume_date` derivation, `force_run_not_replayable` PAGE path),
      wired through `escalation.py::_recover_stalled_vm` (threads
      `details["launch_env"]`/`details["progress_checkpoint"]` to the actuator, mirroring `_recover_preempted_vm`) —
      deployment-service@02ac568
      (`fix(dp-recovery): file OOM-investigate issue doc + checkpoint-resume for stalled VMs`). Verified via
      `tests/unit/test_dp_recovery_actuators.py`: `test_stalled_relaunch_resumes_from_monotonic_checkpoint`,
      `test_stalled_relaunch_force_run_no_checkpoint_pages`,
      `test_stalled_relaunch_non_force_no_checkpoint_replays_verbatim`,
      `test_stalled_relaunch_no_launch_env_or_checkpoint_still_works` (the explicit no-regression-for-no-checkpoint-VMs
      case) + `test_route_auto_recover_stalled_relaunch_resumes_from_checkpoint` (the `escalation.py` wiring test) —
      full `quality-gates.sh` green. Done-when satisfied verbatim.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
