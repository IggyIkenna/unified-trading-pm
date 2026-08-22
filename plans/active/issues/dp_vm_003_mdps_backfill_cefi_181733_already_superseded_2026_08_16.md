---
doc_type: issue
title:
  DP-VM-003 heartbeat stall on mdps-backfill-cefi-20260815-181733 — VM confirmed gone from the live fleet; a live,
  healthy replacement (mdps-backfill-cefi-20260816-162418, wider date range) already covers the outstanding work; no
  relaunch action taken; open question on whether the checkpoint frontier was honored
summary: >-
  A DP_VM_STALL (DP-VM-003, WARN) escalation (agt-576027) reported `mdps-backfill-cefi-20260815-181733` heartbeat 15m
  stale, with `RELAUNCH vm=mdps-backfill-cefi-20260815-181733 launcher=launch-mdps-backfill-vm.sh asset_group=cefi`.
  This worker followed `RB-INFRA-RELAUNCH`: `launcher_registry.LAUNCHER_FOR_VM_PREFIX["mdps-backfill-cefi-"]` confirmed
  `launch-mdps-backfill-vm.sh` (matches the dispatch), no supervising wrapper exists for this launcher, and no
  suppression marker existed at `vm-census/relaunch-paged/vm/mdps-backfill-cefi-20260815-181733.json`. `gcloud compute
  instances list --filter="name~'^mdps-backfill-cefi'"` showed the target VM is **no longer in the live fleet** at all
  (superseded by a different, freshly-launched VM — see below), so per the runbook's "check for an already-running
  replacement before relaunching" step, this worker verified via the GCS SDK helpers
  (`deployment_service.data_pipeline_monitors._gcs.read_launch_params`/`read_progress_checkpoint`/`run_log_signals`, no
  subprocess `gsutil`/`gcloud storage`) rather than blind-relaunching.

  `mdps-backfill-cefi-20260815-181733`'s own `PROGRESS.json` showed `last_completed_date=2022-06-21` — identical to its
  own `LAUNCH_PARAMS.json` `RESUME_START_DATE=2022-06-21` — i.e. this incarnation made ZERO forward progress before
  dying; all three liveness signals (pipeline heartbeat, run.log mtime, infra heartbeat sidecar) read ~46 minutes stale
  at read time (vs. 15 min when the alert first fired — it never recovered on its own). Comparing against the
  `dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md` Progress Log's 2026-08-15T17:48Z observation of
  this SAME `vm_name` (`RESUME_START_DATE=2020-01-01` at that time) against today's read
  (`RESUME_START_DATE=2022-06-21`) proves `...181733` was itself already checkpoint-resumed/relaunched at least once
  under its own fixed name between then and now (`VM_NAME_OVERRIDE` reuse — the same same-name checkpoint-continuity
  contract `RelaunchPreemptedVm`/`RelaunchStalledVm` document) — this dispatch is at minimum the SECOND stall this
  fixed name has hit.

  A live, healthy replacement already exists: `mdps-backfill-cefi-20260816-162418`, `gcloud` `creationTimestamp`
  `2026-08-16T15:24:57Z` — ~4.5 minutes after `...181733`'s last `PROGRESS.json` write (`15:20:28Z`). Same
  `RESUME_ASSET_GROUP=cefi`, same `MDPS_DATA_TYPES=liquidations`, `FORCE=false` (matching); its
  `RESUME_START_DATE=2020-01-01`/`RESUME_END_DATE=2026-01-31` is a strict superset of `...181733`'s outstanding range
  (`2022-06-21`→`2026-01-31`). All three liveness signals read <1 minute old at read time; `run_log_shows_stall=False`.
  Per `rb_infra_relaunch.md`'s explicit rule, this worker did **not** relaunch — a live, covering replacement already
  exists, and launching a third VM would duplicate the shard.

  **Open question, not asserted as fact** (mirrors the same-shape caution the 2026-08-15 slot-12 duplicate-dispatch
  entry in the tarball-race doc used): `RelaunchStalledVm.relaunch()`'s own code (read in full this session — see
  `context_scope`) explicitly resumes from a monotonic `PROGRESS.json` checkpoint's `last_completed_date` when one
  exists — so if this new VM really was dispatched by that actuator reading `...181733`'s checkpoint, it should have
  used `RESUME_START_DATE=2022-06-21`, not `2020-01-01`. The observed `2020-01-01` restart is consistent with EITHER
  (a) an independent launch path unrelated to this specific stall (an operator/AO-driven broader cefi-liquidations
  sweep that happens to also cover the gap — benign coincidence), or (b) an actuator dispatch that did not
  read/honor the checkpoint for this launcher. `FORCE=false` on the new VM means the launcher's own per-date
  manifest-freshness pre-flight should skip the already-captured `2020-01-01`→`2022-06-21` window quickly (idempotent,
  not a data-correctness risk) — so at worst this is wasted compute/time, not a fabrication or gap risk. Not
  investigated further in this one-shot pass (would need a Cloud Logging query this worker did not have fast access
  to); left as a P3 follow-up below rather than asserted either way.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [dp-vm-003, heartbeat-stall, mdps-backfill-cefi, relaunch, checkpoint-resume, no-op-verified]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/archive/issues/dp_vm_003_canonical_migration_cefi_deribit_sweep_wedged_relaunched_fresh_name_2026_08_16.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py, deployment-service/scripts/recovery/relaunch_stalled_vm.py, deployment-service/scripts/vm/launch-mdps-backfill-vm.sh]
created: "2026-08-16"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-576027 (wall_type=data_pipeline_failure, dispatched to slot 1, 2026-08-16) — context carried
  `RELAUNCH vm=mdps-backfill-cefi-20260815-181733 launcher=launch-mdps-backfill-vm.sh asset_group=cefi`, no separate
  audit CSV attached ("Filed issue: (none — alert carries the details)").
---

# DP-VM-003 — mdps-backfill-cefi-20260815-181733 stalled + gone, already superseded by a live covering replacement

## What happened

- `mdps-backfill-cefi-20260815-181733` (cefi liquidations MDPS backfill) went WARN-stale on heartbeat (15m at alert
  time). This worker's read (via GCS SDK helpers, ~30+ min later) found it ~46 min stale on all 3 liveness signals and
  **absent from the live GCE fleet** (`gcloud compute instances list`) — genuinely gone, not just slow.
- Its own `PROGRESS.json` (`last_completed_date=2022-06-21`) matched its own `LAUNCH_PARAMS.json`
  (`RESUME_START_DATE=2022-06-21`) exactly — this incarnation made zero forward progress before dying.
- Cross-referencing the 2026-08-15 tarball-race issue doc's Progress Log (which observed THIS SAME `vm_name` at
  `RESUME_START_DATE=2020-01-01` as of `17:48Z` that day) against today's `2022-06-21` read proves `...181733` was
  already checkpoint-resumed/relaunched at least once under its own fixed name (`VM_NAME_OVERRIDE` reuse) between then
  and now — this WARN is at least the second stall this fixed name has hit.
- A live, healthy, differently-named replacement already exists: `mdps-backfill-cefi-20260816-162418` — launched
  `15:24:57Z`, ~4.5 min after `...181733`'s last `PROGRESS.json` write (`15:20:28Z`); same asset_group/data_type; date
  range `2020-01-01→2026-01-31` (strict superset of `...181733`'s outstanding `2022-06-21→2026-01-31`); all liveness
  signals <1 min old; no stall marker.

## Decision

Per `rb_infra_relaunch.md`'s "check the live VM fleet for an already-running replacement before relaunching" step: a
live, healthy, covering replacement already exists. **No relaunch action taken** — launching a third VM here would
duplicate the shard for no benefit. This dispatch is a no-op, mirroring the 2026-08-15 slot-12 precedent
(`dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`) for the exact same `mdps-backfill-cefi-` family.

## Todos

- [ ] [SCRIPT] P3. If a similar `mdps-backfill-cefi-` stall recurs, confirm via Cloud Logging (`uts-prod-dp-heartbeat-
      watcher` / `uts-prod-dp-exit-code-monitor` execution logs around the relaunch timestamp) whether the replacement
      VM was dispatched by `RelaunchStalledVm`'s `auto_recover` tier or an independent path, and if the former, why
      `RESUME_START_DATE` did not honor the prior incarnation's monotonic checkpoint frontier (a possible gap in
      checkpoint plumbing specific to `launch-mdps-backfill-vm.sh`, or a silent `read_progress_checkpoint` failure) —
      not investigated further here since `FORCE=false` makes it a compute-waste question, not a correctness one.

## Progress Log

- 2026-08-16 (agt-576027, slot 1): Diagnosed via GCS SDK reads (`uv sync` to build a working venv first — none existed
  in this slot's `deployment-service` checkout; no subprocess `gcloud`/`gsutil`). Confirmed `...181733` gone from the
  live fleet, frozen ~46min, zero progress past its own checkpoint. Confirmed `...162418` is a live, healthy,
  range-covering replacement. No relaunch attempted (would duplicate the shard). Filed this issue with the verification
  evidence + the open checkpoint-frontier question as a P3 follow-up. `AUTHORING_SLOT=dp-fleet-monitor` is not a
  numeric slot id, so the authoring-slot ping step was skipped per `data_pipeline_failure.md`'s own rule (the
  dispatch-time Slack alert already covers the FYI). `/done` posted with `one_shot_complete: true`.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
