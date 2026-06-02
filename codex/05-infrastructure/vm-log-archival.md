---
title: VM Log Archival — Canonical Paths, Backup Contract, and Retention
type: infrastructure
status: living
last_reviewed: 2026-05-30
execution:
  owner: "deployment-platform"
  cadence: "daily (Cloud Run Job) + on VM kill"
  verifier: "gsutil ls -r gs://deployment-scripts-central-element-323112/log-archive/ | head -20"
  last_executed: "2026-05-30 (slot-2: throwaway bucket migration + periodic serial capture)"
---

# VM Log Archival — Canonical Paths, Backup Contract, and Retention

**Author**: slot-2 agent (2026-05-30) **Related plan**: `plans/active/canonical_vm_log_archival_2026_05_27.md`

> **⚠️ NOT YET DEPLOYED — `tofu apply` pending (as of 2026-06-02).** The **daily rolling log-archive** + **rolling
> serial-capture** schedulers (`deployment-service/terraform/gcp/vm_log_archival_scheduler.tf` +
> `vm_serial_capture_scheduler.tf`) are **TF-authored but not applied** — the scheduled `log-archive/rolling/` and
> `log-archive/serial-rolling/` paths below are not being populated by a live cron yet. On-demand pre-kill snapshots
> (`snapshot_*/`) and the live `vm-logs/` stream are live; only the _scheduled rolling_ archives await the apply.
> Tracked as an operator-gated infra item in `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md` §
> "Operator-gated infra" + `fleet_audit_triad_deferred_followups_2026_06_01.md`. Remove this banner once `tofu apply`
> lands the two schedulers.

---

## Two Canonical Paths

| Use case                                          | GCS path                                                                                                  | Retention                                        | SSOT helper                       |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------- |
| **Live stream** (hot, short-lived)                | `gs://deployment-scripts-{pid}/vm-logs/{vm}/run.log`                                                      | **14-day delete lifecycle** on `vm-logs/` prefix | `vm_log_stream_uri(vm)`           |
| **Durable snapshot** (pre-kill, on-demand)        | `gs://deployment-scripts-{pid}/log-archive/snapshot_{YYYYMMDD_HHMM}/{vm}/run.log` + `/serial-console.txt` | No lifecycle rule — **persists indefinitely**    | `vm_log_archive_uri(vm, ts)`      |
| **Daily rolling log archive**                     | `gs://deployment-scripts-{pid}/log-archive/rolling/{YYYYMMDD}/{relative_path}`                            | No lifecycle rule — **persists indefinitely**    | _(inline in cron)_                |
| **Daily rolling serial capture** (long-lived VMs) | `gs://deployment-scripts-{pid}/log-archive/serial-rolling/{YYYYMMDD}/{vm}/serial-console.txt`             | No lifecycle rule — **persists indefinitely**    | `vm_serial_rolling_uri(vm, date)` |

`{pid}` = GCP project ID (e.g. `central-element-323112`). Helpers live in `deployment_service/deployments_registry.py`.
**Never construct these paths inline** — use the helpers so path-shape is single-SSOT.

> **Why `log-archive/` is safe from the 14-day rule**: the delete lifecycle rule targets only the `vm-logs/` prefix. All
> `log-archive/` sub-prefixes (`snapshot_*/`, `rolling/`, `serial-rolling/`) are outside that rule's scope and persist
> indefinitely.

---

## Backup Script: `backup-vm-logs.sh`

`deployment-service/scripts/vm/backup-vm-logs.sh`

**When to run**: before killing any VM — mandatory pre-kill hook (wired into `vm_zombie_watchdog.py`
`_archive_vm_logs()` and `vm-exec-with-gcs-tee.sh` self-delete block).

**What it captures**:

1. `run.log` — server-side GCS→GCS copy (instant, no download). Captures the last 30s upload from `heartbeat_daemon.py`.
   A VM killed mid-30s-window loses ≤30s of tail.
2. `serial-console.txt` — fetched via `gcloud compute instances get-serial-port-output`. Works even when the VM has no
   network (boot-hung / wedged). This is the **only forensic record** for VMs that never produced a `run.log` (network
   wedge, failed startup-script, boot hang).

**Usage**:

```bash
# All RUNNING VMs in the default zone
bash deployment-service/scripts/vm/backup-vm-logs.sh

# Specific VMs
bash deployment-service/scripts/vm/backup-vm-logs.sh --vm vm-name-1 --vm vm-name-2

# Non-default zone or project
bash deployment-service/scripts/vm/backup-vm-logs.sh --zone asia-northeast1-b --project central-element-323112
```

**Output path**: `gs://deployment-scripts-{project}/log-archive/snapshot_{YYYYMMDD_HHMM}/{vm}/`

---

## Daily Cron: `vm_log_archival_cron.py`

`deployment-service/scripts/vm/vm_log_archival_cron.py`

Runs daily as a Cloud Run Job scheduled via Cloud Scheduler. Two jobs per run:

### Job 1 — Log rolling

Copies all objects from `vm-logs/` (14-day TTL) to `log-archive/rolling/{date}/` (no TTL). Preserves VM logs past the
14-day window for long-running investigations, compliance, and forensics.

- **Source**: `gs://deployment-scripts-{pid}/vm-logs/**`
- **Destination**: `gs://deployment-scripts-{pid}/log-archive/rolling/{YYYYMMDD}/`
- **Idempotent**: skips objects that already exist at the destination.

### Job 2 — Periodic serial capture (LONG_LIVED_LIVE / SCHEDULED_RECURRING VMs)

One-shot serial capture at kill time is insufficient for VMs that run for days or weeks, because the GCE serial ring
buffer (~1 MB / ~65 KB of text) wraps and early boot output is lost. This job captures serial on a daily cadence for all
RUNNING VMs whose name prefix maps to `LONG_LIVED_LIVE` or `SCHEDULED_RECURRING` in
`vm_zombie_watchdog.py VM_PREFIX_TO_BUCKET`.

- **Source**: GCP Compute API `get_serial_port_output()`
- **Destination**: `gs://deployment-scripts-{pid}/log-archive/serial-rolling/{YYYYMMDD}/{vm}/serial-console.txt`
- **Filter**: `_LONG_LIVED_VM_PREFIXES` tuple in `vm_log_archival_cron.py` (30 prefixes: `strategy-live-`,
  `mtds-live-*`, `agent-orch-vm-*`, `cefi-fwd-daily-cron-`, etc.)
- **SSOT sync**: when adding a new `LONG_LIVED_LIVE` / `SCHEDULED_RECURRING` prefix to `vm_zombie_watchdog.py`, also add
  it to `_LONG_LIVED_VM_PREFIXES` in the cron.

---

## Pre-kill Hook — Mandatory Before Every VM Delete

Per `CLAUDE.md` **No fire-and-forget VM launches (CRITICAL)** and
`plans/active/canonical_vm_log_archival_2026_05_27.md`, every VM-delete path MUST call `backup-vm-logs.sh --vm <name>`
(or its Python equivalent) before `instances delete`.

Three enforcement points (all wired as of 2026-05-27):

| Kill path                                         | Hook location                                           |
| ------------------------------------------------- | ------------------------------------------------------- |
| Watchdog kill (`vm_zombie_watchdog.py`)           | `_archive_vm_logs()` called before `_kill_vm()`         |
| VM self-delete (`VM_SHUTDOWN_ON_COMPLETION=true`) | `vm-exec-with-gcs-tee.sh` self-delete block             |
| Manual operator kill                              | Operator must run `backup-vm-logs.sh --vm <name>` first |

---

## Retirement of Throwaway Buckets

If a snapshot was written to an **ad-hoc** bucket (e.g. `gs://vm-logs-archive-{pid}`) rather than the canonical
`log-archive/` prefix:

1. Copy to canonical: `gsutil -m cp -r gs://{throwaway}/snapshot_*/ gs://deployment-scripts-{pid}/log-archive/`
2. Verify file count matches (source == destination).
3. Get operator confirm before deleting the throwaway bucket.
4. Delete: `gsutil rm -r gs://{throwaway} && gsutil rb gs://{throwaway}`

> The `vm-logs-archive-central-element-323112` bucket (created 2026-05-27 before this SSOT existed) was migrated to
> canonical at `snapshot_20260527_1300/` on 2026-05-30. Pending operator-confirm deletion.

---

## Runbook: Verify Archive State

```bash
# List all snapshot archives
gsutil ls -r gs://deployment-scripts-central-element-323112/log-archive/ | grep -E "snapshot_[0-9]+" | head -20

# List today's rolling serial captures
gsutil ls gs://deployment-scripts-central-element-323112/log-archive/serial-rolling/$(date +%Y%m%d)/

# Check a specific VM's serial history
gsutil ls -r gs://deployment-scripts-central-element-323112/log-archive/serial-rolling/ | grep <vm-name>
```

---

## Per-Service Log-Destination Convention (Beyond VMs)

### Standard

Every service or script that runs in production MUST have an explicit declared log destination:

| Runtime                                         | Log destination                        | Retention                                | Action required                                            |
| ----------------------------------------------- | -------------------------------------- | ---------------------------------------- | ---------------------------------------------------------- |
| **GCE VM** (workload, backfill, live)           | `vm-logs/` → `log-archive/` (this doc) | 14-day live; indefinite archive          | `heartbeat_daemon.py` wired by `setup-data-pipeline-vm.sh` |
| **Cloud Run service** (API, background workers) | stdout → Cloud Logging (managed)       | GCP default 30 days in `_Default` bucket | No custom sink — Cloud Logging automatic                   |
| **Cloud Run Job** (cron, batch)                 | stdout → Cloud Logging (managed)       | Same as above                            | No custom sink — Cloud Logging automatic                   |
| **Local dev script**                            | stderr only                            | None (ephemeral)                         | No archival needed                                         |

### Audit — 2026-05-30 findings

All 21 workspace repos have Dockerfiles (Cloud Run capable). Production service log paths:

| Service                                                         | Runtime                             | Log destination            | Status                |
| --------------------------------------------------------------- | ----------------------------------- | -------------------------- | --------------------- |
| `deployment-api`, `unified-trading-api`, `client-reporting-api` | Cloud Run service                   | Cloud Logging stdout       | ✅ canonical          |
| `execution-service`, `strategy-service`, `features-service`     | Cloud Run Job / Cloud Run           | Cloud Logging stdout       | ✅ canonical          |
| `market-tick-data-service`, `market-data-processing-service`    | Cloud Run Job + GCE VM              | Cloud Logging + `vm-logs/` | ✅ canonical          |
| `instruments-service`, `alerting-service`, `greeks-service`     | Cloud Run                           | Cloud Logging stdout       | ✅ canonical          |
| `agent-orchestrator`                                            | Cloud Run (API) + GCE VMs (workers) | Cloud Logging + `vm-logs/` | ✅ canonical          |
| `deployment-service` crons                                      | Cloud Run Jobs                      | Cloud Logging stdout       | ✅ canonical          |
| Local dev scripts (`scripts/`)                                  | Manual run                          | stderr                     | ✅ no archival needed |

**No divergent sinks found** in the 2026-05-30 audit. All production workloads follow the two-path model: Cloud Run →
Cloud Logging (automatic), VM workloads → `vm-logs/` + `log-archive/` (this doc).

### Operator items (pending confirmation before retrofit)

| Item                    | Status                       | Notes                                                                                                                                                                                       |
| ----------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cloud Logging retention | ❓ Confirm current retention | GCP default is 30 days. For compliance/forensics, operator should confirm whether 30-day is sufficient or a custom `_Default` bucket retention + BigQuery export sink should be configured. |
| Mass retrofit           | ⏸ Pending operator confirm  | No divergent services found — no mass retrofit needed as of 2026-05-30.                                                                                                                     |

---

## Related Docs

- `codex/05-infrastructure/vm-tarball-deployment.md` — VM launch + live-stream log path
- `codex/05-infrastructure/vm-launcher-runbook.md` — per-launcher usage; references this doc for kill/backup
- `deployment-service/scripts/vm/backup-vm-logs.sh` — backup script (SSOT for snapshot path)
- `deployment-service/scripts/vm/vm_log_archival_cron.py` — daily rolling + serial capture cron
- `deployment-service/deployment_service/deployments_registry.py` — canonical URI helpers
