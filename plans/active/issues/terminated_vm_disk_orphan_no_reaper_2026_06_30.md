---
doc_type: issue
title:
  TERMINATED VMs orphan their boot disks forever — completion path stops instead of deleting, and nothing reaps stopped
  instances
summary:
  "127 stopped (TERMINATED) GCE VMs had accumulated in central-element-323112, each billing its 50GB boot disk (~$330/mo
  total) with zero compute value. Two leaks: (1) the shared completion trap + inline-heredoc startup template ended VMs
  with `shutdown -h` (STOP, keeps the disk) instead of self-deleting; (2) externally-stopped VMs (fleet drain,
  hang-then-stop, manual stop) never run any completion handler, and the zombie-watchdog only reaped RUNNING zombies —
  never TERMINATED instances. Resolved: deleted the 127 orphans, fixed both completion paths to self-delete, and added a
  TERMINATED-reaper second pass to the watchdog."
status: resolved
nature: record
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-lifecycle, zombie-watchdog, cost, boot-disk, orphan, self-delete, reaper, infrastructure, resolved]
related:
  [
    ../../../codex/05-infrastructure/deployment-observability.md,
    ../../../codex/05-infrastructure/vm-tarball-deployment.md,
    ../../../codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-06-30
parent_epic: infrastructure_master
priority: P2
source: [operator request 2026-06-30 (GCP cost review), GCP central-element-323112 VM inventory, session 2026-06-30]
assigned_vm: NA
resolved_by: deployment-service@b5f8dec + deployment-service@738637c
locked_by:
execution_scope: human
assigned_role: backend_engineer
drift_direction: advance-code
last_updated: 2026-06-30
resolved_at: 2026-06-30
depends_on: []
---

# TERMINATED VMs orphan their boot disks forever (no reaper for stopped instances)

## Symptom (operator-reported 2026-06-30)

A GCP cost review found **133 VM instances** in `central-element-323112` with only **6–7 RUNNING** and **127
TERMINATED**. Stopped VMs incur
**$0 compute**, but every TERMINATED instance kept its boot disk (`autoDelete=True` but
the disk only frees on instance _deletion_, not stop) — **134 disks / 6,590 GB**, of which ~127 × 50GB pd-standard
belonged to the stopped fleet, ≈ **$330/mo**
billed for zero value. (Also found + released one idle reserved static IP `harsh-static-ip`, ~$7/mo — never attached to
anything in its ~5-month life.)

Critically, the orphans were **not ancient** — every one had stopped within the prior 32 days (most within a week). This
is a steady-state leak, not a one-time historical mess.

## Root cause — two independent leaks

1. **Completion path stops instead of deletes.** The shared completion trap `lc_log_upload_trap_block` /
   `_lc_final_upload` in [`deployment-service/scripts/vm/lib/launcher_common.sh`] ended a finished VM with
   `shutdown -h +1`, and the inline startup template [`scripts/vm/templates/startup-inline-heredoc.sh.tmpl`] with
   `shutdown -h now`. On GCE a guest halt → **TERMINATED**, not deletion — so the boot disk persists. (The data-pipeline
   wrapper `vm-exec-with-gcs-tee.sh` already self-deleted, which is why not 100% of launchers leaked.) The
   `VM_SHUTDOWN_ON_COMPLETION=true` flag (set by 123 launchers) was meant to mean "go away when done" but these two
   paths ignored it and only stopped.

2. **No reaper for stopped instances.** Most orphans' GCS `run.log`s cut off **mid-execution** with no `VM EXIT rc=`
   line — they were stopped _abruptly_ (fleet drain / hung on RPC-429 storms then stopped / manual stop), so they never
   ran _any_ completion handler. The `vm_zombie_watchdog.py` only enumerates `status=RUNNING` zombies, so once a VM is
   TERMINATED it is never re-examined and orphans forever. No completion-path fix can catch this class — only a reaper
   that looks at stopped instances.

## Resolution (DONE — do not re-do)

### 1. Cleanup — 127 orphans deleted (2026-06-30)

Deleted all 127 TERMINATED instances (+ boot disks via `autoDelete`) after a single-VM smoke-test; **0 failures**.
Verified final state: 7 RUNNING / 0 TERMINATED, all RUNNING VMs (incl. the live watchdog `vm-zombie-watchdog-20260623`)
untouched. The one `mtds-live-tradfi-cme-trades` "live"-named VM was operator-confirmed a test and deleted. Released
idle static IP `harsh-static-ip`. One unrelated pre-existing standalone disk `pricetester-reports` (40GB,
europe-west1-b, 2022) was left alone.

### 2. Source fix #1 — completion path self-deletes — `deployment-service@b5f8dec`

`_lc_final_upload` (launcher_common.sh) and `startup-inline-heredoc.sh.tmpl` now self-DELETE
(`gcloud compute instances delete … --delete-disks=all`, zone from metadata) when `VM_SHUTDOWN_ON_COMPLETION=true`, with
a `shutdown -h` fallback if the delete is refused. VMs that omit the flag (recurring cron / persistent) keep the stop
behavior. Mirrors the proven self-delete in `vm-exec-with-gcs-tee.sh`.

### 3. Source fix #2 — TERMINATED-reaper in the watchdog — `deployment-service@738637c`

A second pass in `vm_zombie_watchdog.py`'s `main()` deletes abandoned ephemeral TERMINATED VMs. A stopped VM does zero
work, so **no stall detection is needed** — only four gates (`_evaluate_terminated_vm`):

1. `status == TERMINATED` — already stopped; no live work at risk.
2. `lifecycle_class ∈ {EPHEMERAL_BATCH, EPHEMERAL_EXPERIMENT}` (longest-prefix match against `VM_PREFIX_TO_BUCKET`) —
   `LONG_LIVED_LIVE` / `SCHEDULED_RECURRING` / **unknown** prefixes are never reaped.
3. stopped longer than `--reap-terminated-after` (default **1440 min / 24h** restart window).
4. no `keep=true` label and not a daemon opt-out (the watchdog can't reap itself).

Re-uses `_kill_vm` (pre-kill log backup + `--delete-disks=all`). Honours `--dry-run`; `--no-reap-terminated` disables.
**15 new unit tests** in `tests/unit/test_vm_zombie_watchdog.py` cover every gate; verified end-to-end dry-run against
live GCP (reported 0 reapable post-cleanup, exit 0). Quality-gates green on both commits.

Together #2 + #3 would have prevented all 127 orphans: #2 stops clean completions from orphaning; #3 sweeps up anything
stopped by drain / hang / manual that no completion handler can catch.

## Verification evidence

- Cleanup: `gcloud compute instances list --filter=status=TERMINATED` → 0; RUNNING → 7 (unchanged).
- `b5f8dec`: `bash -n` + shellcheck clean; rendered trap snippet inspected.
- `738637c`: `pytest tests/unit/test_vm_zombie_watchdog.py -k "Terminated or LifecycleClass or Reapable"` → 15 passed;
  full `quality-gates.sh` → ALL PASSED; live dry-run exit 0.

## Follow-up — `- [ ]` watchdog redeploy (P3)

The currently-running `vm-zombie-watchdog-20260623` is on the **pre-`738637c`** code. The reaper activates only once the
watchdog runs fresh code: automatically if its cron re-downloads code tarballs each cycle, otherwise on a relaunch via
`launch-vm-zombie-watchdog.sh`. Confirm which, and relaunch if it bakes code in, so the reaper actually starts running.

> **SAFETY (operator ruling 2026-07-12, finding 83, per
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2):** launch with `--dry-run` FIRST,
> review the would-reap list, only then arm — the launcher defaults `dry_run=false` and this watchdog previously reaped
> LIVE backfill VMs (was: "that's this doc's own incident" — corrected 2026-07-14, verify-rerun-2 finding 104: that
> 9-live-VM-reaped incident is tracked in the separate, still-open
> `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`, not this doc — this doc's own subject is
> TERMINATED/stopped VMs never being reaped, a different failure mode; the safety note applies regardless of which doc
> owns the incident, but the attribution was wrong). Liveness-check code fix has NOT shipped (grep-verified).

> **Distinct from** `plans/ai/vm_deployment_registry_reaper_and_ssot_2026_04_21.plan.md`, which reaps stale
> `/api/vm-deployments` **registry JSON blobs** in GCS — a different artifact from the GCE **instances + disks** this
> issue addresses.
