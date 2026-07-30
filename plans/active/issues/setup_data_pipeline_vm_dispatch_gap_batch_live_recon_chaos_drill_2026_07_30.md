---
doc_type: issue
title:
  setup-data-pipeline-vm.sh has no dispatch branch for VM_TASK=batch-live-recon or VM_SERVICE=chaos-drill — both real
  production launchers SETUP FAILED before doing any work
summary: >-
  Discovered while soak-testing the deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md fix:
  launching real (non-benchmark) production VMs via launch-batch-live-recon-cron-vm.sh and
  launch-disaster-drill-cron-vm.sh both hit "SETUP FAILED rc=1" inside setup-data-pipeline-vm.sh — neither
  VM_TASK=batch-live-recon nor VM_SERVICE=chaos-drill has a matching dispatch branch, so the VM self-deleted before ever
  running its real workload (and before the heartbeat daemon / DeploymentsRegistry registration ever started). Unrelated
  to the dualwrite fix itself — a pre-existing dispatch-coverage gap.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-launchers, setup-script, dispatch-gap, batch-live-recon, chaos-drill]
related: [/plans/active/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md]
created: 2026-07-30
priority: P2
parent_epic: infrastructure_master
source: "slot-16, review, discovered while soak-testing the dualwrite Firestore fix, 2026-07-30"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# What I found

Soak-testing `deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`'s fix required launching
real (non-benchmark) production VMs. Two of the three chosen launchers failed during VM setup, before ever reaching the
workload (and therefore before the heartbeat daemon / `DeploymentsRegistry` registration this soak test needed to
observe):

1. **`launch-batch-live-recon-cron-vm.sh`** (VM `batch-live-recon-20260729-20260730-033916`): `vm-setup.log` shows

   ```
   ERROR: VM_TASK=batch-live-recon has no dedicated dispatch branch in this script, but VM_BACKFILL_CMD metadata
   IS present (...). This launcher expects VM_BACKFILL_CMD to be run directly — add an
   'elif [[ "$VM_TASK" == "batch-live-recon" ]]' branch here that curls VM_BACKFILL_CMD and runs it via
   _launch_with_tee (mirror the datapoint-validation/orphan-sweep branches above). Refusing to fall through to
   the generic --operation dispatch, which would silently ignore VM_BACKFILL_CMD and crash deep in an unrelated
   CLI's argparse.
   SETUP FAILED rc=1 — uploading log + EXIT_STATUS, scheduling self-delete
   ```

   `setup-data-pipeline-vm.sh` has NO `elif [[ "$VM_TASK" == "batch-live-recon" ]]` branch (confirmed: grepped every
   `VM_TASK ==` / `VM_SERVICE ==` branch in the file — `batch-live-recon` is absent).

2. **`launch-disaster-drill-cron-vm.sh`** (VM `disaster-drill-cron-20260730-033955`): `vm-setup.log` shows
   `WARNING: Unknown VM_SERVICE=chaos-drill — installing all available tarballs` (defensively installs ALL 28 registered
   service tarballs, wasting ~2 minutes of boot time), then fails after the dependency-install step with
   `SETUP FAILED rc=1` (no explicit reason logged before the failure line — the log is silent on the actual
   `uv pip install` or subsequent step that failed; needs re-running with verbose/`set -x` to pin down which of the 28
   `-e` installs failed, or whether it's the same "no dispatch branch after code deploy" pattern as batch-live-recon).

Confirmed unrelated to the dualwrite fix: `deba676` only touched the `_meta()`/`_meta_project()` metadata-read lines: it
never touched the `VM_TASK`/`VM_SERVICE` dispatch `elif` chain. A third VM in the same soak batch
(`funding-ensemble-paper-20260730-034022`, `VM_TASK=strategy-paper` — a branch that DOES exist at line ~1494) completed
cleanly and produced a genuine Firestore dual-write (register + complete both mirrored, confirming the dualwrite fix
itself works). The dispatch gap is real but orthogonal.

# Why it matters

Both are genuine, currently-scheduled production launchers (batch-live-recon is the nightly T+1 reconciliation cron per
GAP-18; disaster-drill is the nightly chaos-drill per Phase 6.A) — if these VM_TASK/VM_SERVICE values have never
actually been exercised end-to-end since this dispatch-branch style was introduced, their nightly Cloud
Scheduler-triggered runs have likely been silently failing (self-deleting on every scheduled invocation) rather than
doing the reconciliation/drill work. Worth checking whether these two crons are even wired to a scheduler yet, or
whether this is the first real invocation.

# Recommended decision

1. Add the missing `elif [[ "$VM_TASK" == "batch-live-recon" ]]` branch to `setup-data-pipeline-vm.sh`, mirroring the
   existing `datapoint-validation`/`orphan-sweep` branches (curl `VM_BACKFILL_CMD` metadata, run via `_launch_with_tee`)
   — the failing log message already names the exact fix.
2. Register `VM_SERVICE=chaos-drill` (or whatever the correct `VM_TASK`/`VM_SERVICE` pairing should be for
   `launch-disaster-drill-cron-vm.sh`) in the tarball-selection logic so it stops defensively installing all 28
   tarballs, and re-run with verbose logging to pin the actual `SETUP FAILED` root cause.
3. Once both dispatch branches exist, re-launch each real launcher once to confirm SETUP_EXIT_STATUS=0 and a genuine
   `status=running` → `status=completed` Firestore transition (same evidence pattern as `funding-ensemble-paper` already
   showed).

## Todos

- [ ] [INFRA] P2. Add the missing `VM_TASK=batch-live-recon` dispatch branch to
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (curl `VM_BACKFILL_CMD` + `_launch_with_tee`, mirroring
      the datapoint-validation/orphan-sweep branches) so `launch-batch-live-recon-cron-vm.sh` VMs actually run the
      nightly reconciliation instead of self-deleting on SETUP FAILED (repo: deployment-service).
- [ ] [INFRA] P2. Register `chaos-drill`'s correct `VM_TASK`/`VM_SERVICE` pairing in `setup-data-pipeline-vm.sh`'s
      tarball-selection + dispatch logic (currently falls through to "Unknown VM_SERVICE — installing all available
      tarballs" then SETUP FAILED with no logged reason); re-run with `set -x` if the root cause isn't obvious once the
      tarball-selection gap is fixed, so `launch-disaster-drill-cron-vm.sh` VMs actually run the nightly chaos drill
      (repo: deployment-service).
- [ ] [INFRA] P3. Check whether either nightly cron (`batch-live-recon`, `disaster-drill-cron`) is actually wired to a
      live Cloud Scheduler job today, and if so, how long it has been silently failing every scheduled invocation (repo:
      deployment-service / infra — read `gcloud scheduler jobs list` + recent VM history for both prefixes).
