---
doc_type: issue
title: Honest-coverage nightly cron ran undersized (16GB) for weeks — launcher SSOT drift + false column-prune claim
summary:
  The nightly honest-coverage cron produced 1-asset-group partial coverage.json for weeks because its VM launcher
  (launch-measure-honest-coverage-vm.sh, the file the Cloud Run Job actually fetches) was downsized to e2-standard-4
  (16GB) on 2026-06-16 citing a column-pruned reader that was NEVER shipped. Fixed the machine type to the proven
  e2-highmem-4 (32GB). Surfaces a wider launcher-SSOT drift across four conflicting honest-coverage launcher artifacts,
  a publisher/consumer GCS path mismatch, and the parent plan's INFRA P0 fix targeting the wrong launcher.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [honest-coverage, data-status, cron, vm-launcher, ssot-drift, oom, false-progress]
related:
  [
    /plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    /plans/archive/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
assigned_role: infra_engineer
drift_direction: advance-code
resolved_by:
locked_by:
source: discovered while executing data_status_page_ux_and_canonicalisation_2026_07_16 P1-remaining INFRA
depends_on: []
---

# Honest-coverage nightly cron undersized + launcher SSOT drift

> **Big finding** (live data-correctness + SSOT contradiction + false-progress commit) surfaced 2026-07-16 while working
> `data_status_page_ux_and_canonicalisation_2026_07_16` P1-remaining. The user-facing P1 bug (partial served as
> complete) was already fixed (partial-stamping writer + amber banner + manual full regen). This issue is the NIGHTLY
> path that kept producing partials.

## The live cron path (verified via gcloud)

`Cloud Scheduler honest-coverage-daily (30 0 * * *, ENABLED)` → `Cloud Run Job honest-coverage-daily-launcher` →
`gsutil cp gs://deployment-scripts-central-element-323112/vm/launch-measure-honest-coverage-vm.sh /tmp/launcher.sh && bash /tmp/launcher.sh`
→ launches a GCE VM running `measure_honest_coverage.py` from the instruments-service tarball.

## Root cause

- The GCS launcher `vm/launch-measure-honest-coverage-vm.sh` (last uploaded **2026-06-16**) hardcoded
  `--machine-type=e2-standard-4` (16 GiB). Its header comment claimed the VM was "right-sized once the column-pruned
  measure_honest_coverage.py (reads only capture_status/venue/data_type → ~5 GiB peak) propagated into the tarball."
- **That column-prune was never shipped** — `measure_honest_coverage._READ_COLUMNS` still reads 6 columns incl. the
  high-cardinality `instrument_id` + `instrument_type` (verified at HEAD). The 2026-06-16 downsize commit (deployment-
  service `24337a0`) is a **false-progress** artifact: it justified a 16GB downsize by a fix that doesn't exist.
- 16 GiB empirically OOM'd most asset_groups. Live `coverage.json` history: 07-12 `[defi]`, 07-13 `[cefi]`, 07-15
  `[defi]` (all 00:30-ish nightly, `partial=None`); the full-5 files 07-14 + 07-16 were **off-schedule manual runs**.

## SSOT drift (why this was hard to see)

Four honest-coverage launcher artifacts disagree on machine type — and the parent plan's INFRA P0 fixed the wrong one:

| Artifact                                                                                      | Machine                 | Is it the live cron path?                                                              |
| --------------------------------------------------------------------------------------------- | ----------------------- | -------------------------------------------------------------------------------------- |
| `vm/launch-measure-honest-coverage-vm.sh` (GCS, cron fetches this)                            | was 16GB → **now 32GB** | ✅ YES                                                                                 |
| `scripts/vm/launch-honest-coverage-vm.sh` (`$MACHINE_TYPE`, plan INFRA P0 `9d97eb2` set 32GB) | 32GB                    | ❌ NO (not fetched by the cron)                                                        |
| `scripts/vm/honest-coverage-daily-workflow.yaml` (Cloud Workflow, 8GB)                        | 8GB                     | ❌ NO (no such workflow is deployed)                                                   |
| `terraform/gcp/honest_coverage_scheduler.tf` (describes a Cloud Run Job + Scheduler)          | n/a                     | partial (the Scheduler + Job are real; the VM-launch details live in the GCS launcher) |

Also: the tarball publisher (`create-code-tarballs.sh`) publishes launchers to
`code/deployment-service/scripts/vm/launch-*.sh`, but the Cloud Run Job reads `vm/launch-measure-honest-coverage-vm.sh`
— a path the publisher does NOT maintain, which is why the GCS launcher went stale (2026-06-16).

## What was fixed (this session)

- ✅ `launch-measure-honest-coverage-vm.sh` `e2-standard-4` (16GB) → **`e2-highmem-4` (32GB)** — the size a manual run
  measured all 5 AGs on 2026-07-16; corrected the false "column-pruning live" header comment. — deployment-service
  `@4f10b9b`.
- ✅ **Uploaded the fixed launcher to the cron's actual GCS path**
  `gs://deployment-scripts-central-element-323112/vm/ launch-measure-honest-coverage-vm.sh` (Update Time
  2026-07-16T08:36Z, verified `--machine-type=e2-highmem-4`). Tonight's 00:30 UTC run will use 32GB → expected full
  5-AG.

## Open follow-ups (need operator awareness / clean tree)

- [ ] [DATA] P2. Real column-prune of `measure_honest_coverage.py` so 16GB suffices — see parent plan DATA P2. NOTE
      (traced): a naive drop of `instrument_id` from `_READ_COLUMNS` is UNSAFE — `_merge_manifests` dedups the
      prd+oracle merge on `(date, venue, instrument_id, data_type)`; dropping it falls back to
      `(date, venue, data_type)` and collapses distinct instruments, corrupting the coverage denominator (the shard atom
      is per-instrument). The correct fix is a pyarrow row-group streaming aggregation OR a metadata-deferred primary
      read (secondaries are already re-read eu-only) — a real refactor with correctness surface + ~6 selection-test
      updates, not a one-line column drop.
- [ ] [INFRA] P2. Republish the instruments-service tarball so the nightly writer has partial-stamping (a29e483) —
      CURRENTLY BLOCKED: `create-code-tarballs.sh` rebuilds fleet-wide core tarballs (UAC 922M / UTL 1.2G / MTDS 1.3G)
      and errors on the foreign uncommitted `terraform/services/features-service-sports/gcp/terraform.tfvars`. Do NOT
      `--allow-dirty-tarball` (ships another worker's uncommitted state fleet-wide). Run from a clean tree.
- [ ] [INFRA] P3. Reconcile the launcher SSOT drift: make the tarball publisher maintain the `vm/` path the Cloud Run
      Job reads (or point the Job at `code/deployment-service/scripts/vm/`), and delete/merge the redundant
      `launch-honest-coverage-vm.sh` + `honest-coverage-daily-workflow.yaml` so ONE launcher is the SSOT.
