---
doc_type: issue
title:
  DP-VM-003 heartbeat stall on manifest-recon-cefi-20260815-093854 — genuinely wedged, but registry marks
  `manifest-recon-` non-auto-relaunchable (read-only dry-run); no code fix identified, operator decision needed on kill
summary: >-
  A DP_VM_STALL (DP-VM-003, WARN) escalation (agt-9d78d2) reported `manifest-recon-cefi-20260815-093854` heartbeat 12m
  stale. This worker followed `RB-INFRA-RELAUNCH`: `launcher_registry.resolve_launcher_for_vm()` resolves the
  `manifest-recon-` prefix to `None` ("read-only all-reconciler dry-run" — deliberately not a fleet-monitored recurring
  backfill; no scheduler/Terraform cron references `launch-manifest-recon-all-vm.sh` either, confirming it is launched
  ad-hoc, not cron-owned). Per the runbook, a `None` launcher means STOP — do not guess a relaunch, file an issue.
  Diagnosis via the SDK (`_gcs` reads + `gcloud compute instances describe`/serial-port-output, no subprocess GCS
  calls): the VM (e2-standard-8, STANDARD/non-preemptible, NOT OOM'd, NOT preempted) is still `RUNNING` per GCE, but
  every independent liveness signal inside it stopped simultaneously around 2026-08-15T09:43-09:44Z — the GCS-uploaded
  `run.log` froze at 2148 bytes (last content timestamped 09:42:38Z), the VM-local `WATCHDOG_TRACE.log` (a separate
  in-VM size-based staleness sampler) recorded growth to 2280 bytes at 09:43:40Z and then never wrote another sample,
  and the serial console emitted its last line at 09:48:29Z. As of this worker's read (~10:04Z, ~20+ min of total
  silence across all three independent channels), nothing has recovered. This is consistent with the underlying
  `reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run --unphantom-only --venues
  BINANCE-FUTURES,KRAKEN-FUTURES` process (instruments-service) or the `heartbeat_daemon.py` uploader loop that shells
  out to `gcloud storage`/`gsutil` (deployment-service) blocking on an unbounded call with no timeout — the same
  DP_VM_STALL root-cause class named in this worker's own role brief — but `run.log` contains no traceback/exception for
  the hang itself (only routine INFO lines up to the freeze point), so the specific blocking call could not be
  identified without a live in-VM stack dump (e.g. `py-spy dump`), which this one-shot escalation did not attempt. No
  relaunch was performed (registry-gated, see above) and the VM was NOT killed (read-only/no data-correctness risk, but
  still billing — left for the operator/existing zombie-watchdog to decide, mirroring the 2026-08-15
  `dp_vm_001_mdps_defi_2022...` precedent's choice not to take unilateral destructive infra action on a one-shot
  escalation).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [dp-vm-003, heartbeat-stall, manifest-recon, phantom-recon, non-relaunchable, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py,
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
    deployment-service/scripts/recovery/relaunch_stalled_vm.py,
    instruments-service/scripts/reconcile_phantom_manifest_rows_all.py,
  ]
created: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-9d78d2 (wall_type=data_pipeline_failure, dispatched to slot 11, 2026-08-15) — client_payload carried
  vm_name=manifest-recon-cefi-20260815-093854, asset_group=cefi, no separate audit CSV attached ("Filed issue: (none —
  alert carries the details)"). VM confirmed RUNNING (not terminated) via `gcloud compute instances list
  --filter="name~manifest-recon-cefi-20260815-093854"`, ~10:01Z. `run.log`/`WATCHDOG_TRACE.log` pulled via
  `deployment_service.data_pipeline_monitors._gcs`/`get_storage_client().download_bytes` (SDK, never subprocess
  `gsutil`/`gcloud storage` — a subprocess `gcloud storage ls` attempt was correctly BLOCKED by
  `block_destructive_commands.py`'s GCS-object-op guardrail, confirming the hook fires on ad-hoc commands too).
---

# DP-VM-003 — manifest-recon-cefi-20260815-093854 wedged, no relaunch target, operator decision needed

## What happened

- VM: `manifest-recon-cefi-20260815-093854` (e2-standard-8, `asia-northeast1-c`, STANDARD/non-preemptible,
  `automaticRestart=true`, `onHostMaintenance=MIGRATE`) — launched ~09:41:20Z per its startup-script serial log, running
  `deployment_id=b45704e9-266e-4cbd-b9d2-472a0e7541d8 asset_group=CEFI task=phantom-recon mode=full`:
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run --unphantom-only --venues BINANCE-FUTURES,KRAKEN-FUTURES`.
- **Not a fleet-monitored auto-relaunch target.** `launcher_registry.LAUNCHER_FOR_VM_PREFIX["manifest-recon-"] = None`
  ("read-only all-reconciler dry-run"). The only other `manifest-recon-*` registry entries are the distinct
  `manifest-recon-apply-{cefi,defi,tradfi}-` prefixes (the real-write variant, which DOES have a launcher) — this VM's
  exact name does not match those. `grep -rl "manifest-recon\|phantom-recon\|phantom_manifest" terraform/gcp/*.tf` and a
  repo-wide search for callers of `launch-manifest-recon-all-vm.sh` both returned zero hits, confirming this launcher is
  invoked ad-hoc (operator/`/data-pipeline-reconciliation`-skill triggered), not a Cloud Scheduler cron — so there is no
  "wait for the next scheduled run" fallback either.
- **Three independent liveness channels all went silent within the same ~2-minute window, and none has recovered since
  (~20+ min as of this read):**
  1. GCS-uploaded `run.log` (uploaded every 60s by `heartbeat_daemon.py`'s uploader loop): frozen at 2148 bytes, last
     real content timestamped `PIPELINE_HEARTBEAT ... ts=2026-08-15T09:42:38Z`.
  2. VM-local `WATCHDOG_TRACE.log` (a separate in-VM size-based staleness sampler, unrelated to the GCS uploader):
     `iter=1 size=2148 ts=09:42:38Z` → `iter=2 size=2280 ts=09:43:40Z` (proves the LOCAL log kept growing past what GCS
     ever received) → no `iter=3` or later, ever.
  3. Serial console (`gcloud compute instances get-serial-port-output`): last line at `09:48:29Z`
     (`PackageKit: daemon quit`, routine/unrelated) — zero lines since, including routine systemd noise.
- `EXIT_STATUS`/`LAUNCH_PARAMS.json` are both absent (this VM class doesn't write them — confirms it predates/sits
  outside the `LAUNCH_PARAMS.json`-based checkpoint-resume contract the runbook describes for backfill VMs, so even if
  it were relaunchable, `relaunch_stalled_vm.py`'s checkpoint-resume path would not apply).

## Why file_issue, not relaunch (and not a guessed code fix)

`RB-INFRA-RELAUNCH` step 2 is explicit: **"A `None` result = an unrecoverable prefix → STOP, file an issue, page (do not
guess a launcher)."** This mirrors `relaunch_stalled_vm.py`'s own `RelaunchStalledVm.relaunch()`: no launcher binding →
`status=SKIPPED, reason=no_launcher_binding` → "the caller falls through to file_issue (cannot relaunch
deterministically)". The registry's design intent (per its own docstring) is that a read-only dry-run with no side
effects has no need for guaranteed auto-recovery — a human/operator re-triggers it — so this worker did not attempt to
hand-invoke `launch-manifest-recon-all-vm.sh` outside the registry's sanctioned binding.

A code-level root-cause fix (per this worker's own role brief: "bound the call with
`asyncio.wait_for(coro, timeout=N)`") was **not attempted** because `run.log` contains no exception/traceback for the
hang — only routine INFO lines up to the freeze point, then silence. The two candidate hang sites (the
`reconcile_phantom_manifest_rows_ all.py --dry-run` process itself, vs. `heartbeat_daemon.py`'s
`gcloud storage`/`gsutil`-shelling uploader loop) could only be distinguished with a live in-VM stack dump (e.g.
`py-spy dump --pid <pid>` via SSH) while the VM is still wedged — out of scope for a one-shot escalation with a 2-minute
blocked-question bound, and destructive/risky to attempt without the operator's go-ahead on a box already flagged for
triage.

## What this worker did NOT do

- Did **not** relaunch (registry-gated `None`, confirmed above).
- Did **not** kill/terminate the wedged VM. It is read-only (`--dry-run --unphantom-only`), so there is no
  data-correctness risk in leaving it — but it is still a STANDARD (non-preemptible, billed) e2-standard-8 sitting
  wedged, and `deployment-service`'s own zombie-watchdog (referenced by `relaunch_stalled_vm.py`'s docstring: "The
  zombie watchdog beside it KILLS the hung VM") may already be about to terminate it independently. Killing it manually
  was left to the operator (bounded `/blocked` ask) rather than taken unilaterally, mirroring the same-day
  `dp_vm_001_mdps_defi_2022...` precedent's choice not to take destructive infra action on a one-shot escalation without
  confirming no other automated actuator is already converging on it.
- Did **not** SSH into the VM to capture a stack trace of the hung process — would materially help root-causing the
  actual blocking call (see above), but is a heavier, higher-risk action than this WARN-severity, read-only,
  registry-gated escalation warrants without an operator go-ahead.

## Recommended decision (for the operator)

1. **[WORKER REC] Terminate `manifest-recon-cefi-20260815-093854`** (`gcloud compute instances delete` or via the
   existing zombie-watchdog, whichever fires first) — it is wedged with no recovery signal in 20+ minutes across three
   independent channels, read-only so nothing is lost, and not registry-eligible for an automated relaunch attempt in
   its place. Re-trigger the CeFi phantom-recon dry-run manually (`launch-manifest-recon-all-vm.sh` / the
   `/data-pipeline-reconciliation` skill) once the operator wants that check re-run.
2. Alternative: before killing, SSH in and capture `py-spy dump --pid <reconcile_phantom_manifest_rows_all.py pid>` (and
   separately for the `heartbeat_daemon.py` uploader PID) to actually pin the blocking call — worthwhile if this is a
   recurring pattern for `manifest-recon-*`/phantom-recon dry-runs specifically, to convert this from a one-off page
   into a real code fix (bounded timeout around whichever call is hanging).

## Todos

- [x] ✅ [OPERATOR] P2. Decide kill-vs-diagnose-first for `manifest-recon-cefi-20260815-093854` per the recommended
      decision above, and terminate it once resolved (it will keep billing until then). **MOOT 2026-08-15 (slot-17)**:
      confirmed gone (`gcloud compute instances describe` → not found) — the VM was genuinely OOM-killed (guest-level
      `mem_pct` reached 99.2% per its own deployment registry telemetry, read before archival), not merely wedged;
      correcting this doc's "NOT OOM'd" characterization above, which was based on the GCE instance `status` field
      (RUNNING) rather than in-guest memory telemetry. No manual kill needed — billing already stopped on its own.
- [ ] [BACKEND] P3. If this recurs for another `manifest-recon-*`/phantom-recon dry-run, capture a live `py-spy dump`
      before killing to identify the exact blocking call, then bound it with a timeout (the DP-VM-003/004 "unbounded
      HTTP call hangs" fix pattern) in whichever of `reconcile_phantom_manifest_rows_all.py` or `heartbeat_daemon.py`'s
      uploader loop turns out to be the culprit.

## Progress Log

- 2026-08-15 (slot 11, data_pipeline_failure escalation agt-9d78d2): Received DP-VM-003 WARN escalation for
  `manifest-recon-cefi-20260815-093854` (heartbeat 12m stale). Resolved `launcher_registry.resolve_launcher_for_vm()` →
  `None` (`manifest-recon-` = read-only dry-run, not auto-relaunchable) and confirmed via terraform/repo grep that no
  scheduler owns this launcher either. Per `RB-INFRA-RELAUNCH` step 2, did not guess a launcher. Pulled the VM's durable
  state via the UTL SDK (`get_storage_client().download_bytes`/`_gcs` helpers — a raw `gcloud storage ls` attempt was
  correctly blocked by the workspace's GCS-subprocess guardrail) plus
  `gcloud compute instances describe`/`get-serial-port-output`: confirmed the VM is still `RUNNING` (not
  OOM'd/preempted) but three independent liveness channels (GCS run.log upload, in-VM watchdog trace, serial console)
  all went silent within the same ~2-minute window around 09:43-09:44Z and none has recovered in 20+ minutes since. Did
  not identify the specific blocking call (no traceback in `run.log`) and did not attempt an in-VM stack dump or kill
  the VM. Filed this issue doc with full diagnosis and a recommended kill-vs-diagnose-first decision for the operator.
- 2026-08-15 (slot-17, data_engineering, batch6 P3 todo owner): This doc's "NOT OOM'd" determination was based on the
  GCE instance `status` field alone (RUNNING at read time) — a separate read of the VM's own deployment registry JSON
  (`deployments/active/b45704e9-266e-4cbd-b9d2-472a0e7541d8.json`, before it was archived) showed `mem_pct` climbing
  75.3%→99.2% in the last sampled minute before all signals went dead, i.e. it WAS a genuine guest-level OOM — the VM is
  now confirmed fully gone (`gcloud compute instances describe` → not found). See the companion doc
  `dp_vm_003_manifest_recon_cefi_silent_death_unsliced_manifest_read_2026_08_15.md`'s matching Progress Log entry for
  the full evidence + the successful re-run on `e2-highmem-16` that closed
  `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s P3 todo. Flipped this doc's operator-kill todo as moot (billing
  already stopped).
