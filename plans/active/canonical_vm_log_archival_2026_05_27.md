---
name: canonical_vm_log_archival
title: "Canonical durable log archival for VMs (and per-repo log paths) — 2026-05-27"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
status: active
priority: P1
created: 2026-05-27
author: harsh (claude opus 4.7)
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: harsh-fleet-audit
related:
  - issues/running_vm_fleet_status_2026_05_27.md
  - deployment_ui_vm_and_venue_coverage_visibility_2026_05_27.md
---

# Canonical durable log archival for VMs (and per-repo log paths)

**Trigger (operator 2026-05-27)**: before we kill any VM we must be sure nothing important is lost. Need a reusable
backup script + a canonical, durable archive path usable across services/repos — assignable to a separate agent.

## Established facts (verified 2026-05-27)

- VMs stream stdout → `gs://deployment-scripts-{pid}/vm-logs/<vm>/run.log` via `heartbeat_daemon.py`, **uploaded every
  30s** (`UPLOAD_INTERVAL_SEC=30`) + a final full upload on clean exit (`vm-exec-with-gcs-tee.sh`).
- Measured fidelity: GCS trails the VM's local `/tmp/vm-exec-*.log` by **~30s / a few KB** → a hard kill loses **≤30s**
  of tail on a healthy VM.
- **Two gaps**: (a) the `vm-logs/` prefix has a **14-day delete lifecycle** → logs expire; (b) **boot-hung /
  network-wedged VMs have NO usable run.log** (workload never started, or can't upload) — their only durable record is
  the **serial console** (fetched via the GCP compute API, independent of the VM's network).
- No canonical backup script existed before this plan.

## Bucket homes — honest SSOT status (corrected 2026-05-27)

**These are INFRA buckets, deliberately NOT in the `resolve_bucket_name` / `cloud-providers.yaml` SSOT** (which models
the 38 data-pipeline kinds — `raw_tick`, `features-*`, `ml-*`, etc.). Infra buckets live outside that system, same as
`terraform-state` / `secrets` (the yaml says so explicitly). `deployment-scripts-{pid}` is "canonical-by-convention" —
produced by the helper `_resolve_default_bucket()` in `deployment_service/deployments_registry.py` and pinned by a unit
test (`gs://deployment-scripts-{pid}/vm-logs/{vm}/run.log`).

| Purpose                            | Path                                                                                            | Status                                                                                       |
| ---------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Live stream (existing, 14-day TTL) | `gs://deployment-scripts-{pid}/vm-logs/<vm>/run.log`                                            | convention + helper + unit test                                                              |
| Durable archive (corrected)        | `gs://deployment-scripts-{pid}/log-archive/snapshot_<UTC-ts>/<vm>/{run.log,serial-console.txt}` | same infra bucket; `log-archive/` prefix is NOT matched by the `vm-logs/` 14-day delete rule |

> **Correction**: the first draft of this plan + script used an invented bucket `gs://vm-logs-archive-{pid}` — that was
> NOT canonical (not in any registry, not derived from a helper). Replaced with the existing infra bucket under a
> durable `log-archive/` prefix so nothing is minted off-registry. The throwaway bucket
> `vm-logs-archive-central-element-323112` is pending retirement (see todo below).

## Todos

- [x] [SCRIPT] P0. Backup script committed: `deployment-service/scripts/vm/backup-vm-logs.sh` — snapshots all RUNNING
      (or named) VMs' `run.log` (server-side GCS→GCS copy) + serial console to
      `gs://deployment-scripts-{pid}/log-archive/snapshot_<ts>/`; read-only on source. (Created + corrected 2026-05-27.)
- [x] [AGENT] P1. **Formalise the archive path into a helper** (don't leave it as an inline string): add e.g.
      `vm_log_archive_uri(vm, ts)` next to `_resolve_default_bucket()` in `deployment_service/deployments_registry.py`,
      and have `backup-vm-logs.sh` + any consumer derive from it. Add a unit test pinning the
      `deployment-scripts-{pid}/log-archive/...` shape (mirroring the existing `vm-logs/` test). —
      deployment-service@e9e69b2 ✅
- [x] [AGENT] P2. **Retire the throwaway bucket** `gs://vm-logs-archive-central-element-323112` once today's snapshot is
      re-copied to the canonical `log-archive/` prefix (operator-confirm before delete — it currently holds the
      2026-05-27 fleet backup). **COPY COMPLETE (2026-05-30 slot-2)**: 44 objects / 7.4 GiB copied server-side from
      `gs://vm-logs-archive-central-element-323112/snapshot_20260527_1300/` →
      `gs://deployment-scripts-central-element-323112/log-archive/snapshot_20260527_1300/`. Verified: 44/44 files.
      **BUCKET DELETION PENDING operator confirm** — run `gsutil rm -r gs://vm-logs-archive-central-element-323112`
      then `gsutil rb gs://vm-logs-archive-central-element-323112` once confirmed safe.
- [x] [AGENT] P1. **Pre-kill hook**: any VM-delete path (operator teardown, `vm_zombie_watchdog.py` reaper,
      `VM_SHUTDOWN_ON_COMPLETION` self-delete) MUST call `backup-vm-logs.sh --vm <name>` (or inline equivalent) BEFORE
      `instances delete`, so a reaped/zombie VM's serial console is always captured. Wire into the watchdog + the
      self-delete block in `vm-exec-with-gcs-tee.sh`. — deployment-service@4b8a0c3 ✅
- [x] [AGENT] P1. **Durable retention**: decide + implement how the live `vm-logs/` stream survives the 14-day TTL —
      either (a) a daily
      `gcloud storage rsync gs://deployment-scripts-{pid}/vm-logs/ gs://deployment-scripts-{pid}/log-archive/rolling/`
      cron (Cloud Scheduler + Cloud Run, mirroring the manifest-consolidator pattern), or (b) lengthen the TTL on the
      `vm-logs/` prefix. Prefer (a) — keeps the hot prefix small + the archive immutable. (If durability demands a
      physically separate bucket, mint it via a helper, not an inline string — see the formalise-helper todo.) —
      deployment-service@3cd0b1d ✅ (implemented option a)
- [x] [AGENT] P2. **Periodic serial capture for long-lived VMs**: one-shot serial capture misses early boot output once
      the ring buffer wraps. For LONG_LIVED_LIVE / SCHEDULED_RECURRING VMs, capture serial on a schedule (or on
      state-change) into the archive. — deployment-service@e534481 ✅
      Extended `vm_log_archival_cron.py` with `capture_long_lived_serial()`: lists RUNNING VMs via compute_v1 API,
      filters to `_LONG_LIVED_VM_PREFIXES` (30 prefixes covering LONG_LIVED_LIVE + SCHEDULED_RECURRING from watchdog),
      captures serial via `get_serial_port_output()`, stores to canonical
      `log-archive/serial-rolling/{date}/{vm}/serial-console.txt`. Added `vm_serial_rolling_uri()` helper to
      `deployments_registry.py`. Daily cron now covers both log rolling AND serial history.
- [ ] [AGENT] P2. **Codex SSOT**: document the two canonical paths + the backup/retention contract in
      `codex/05-infrastructure/vm-tarball-deployment.md` (or a new `codex/05-infrastructure/vm-log-archival.md`), and
      reference it from the kill/teardown runbook.
- [ ] [AGENT] P2. **Per-repo log-destination convention**: extend the canonical-path idea beyond VMs — every
      service/repo that emits operational logs (Cloud Run services, local dev, batch jobs) declares a canonical archive
      destination so backups + analysis are uniform. Audit current per-service log sinks; document the standard;
      retrofit divergent ones. (This is the broad "for each repo a canonical path" ask — scope/confirm with operator
      before mass retrofit.)
- [ ] [AGENT] P2. **Deployment-UI integration**: the History tab links each archived run to its
      `gs://deployment-scripts-{pid}/log-archive/…` run.log + serial-console (cross-ref
      `deployment_ui_vm_and_venue_coverage_visibility_2026_05_27.md` §2).
