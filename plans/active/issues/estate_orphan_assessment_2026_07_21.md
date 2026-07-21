---
doc_type: issue
title:
  Estate orphan assessment 2026-07-21 — sports has 214K ORPHAN_REAL objects; defi/cefi/tradfi blocked on multi-GB
  manifest download (need a VM)
summary:
  Ran migration_orphan_sweep per asset_group (GCS→manifest, single-walk, read-only). SPORTS is measured — 214,319
  ORPHAN_REAL objects (real data with no manifest row — the silent-write gap) plus 34,385 LEGACY_DUPLICATE, reports
  written to the GCS audit parquets. prediction hung in the classification phase (30 min no progress, killed).
  defi/cefi/tradfi FAILED in-session on the multi-GB availability-index download (ChunkedEncodingError — defi index is
  ~1.8GB) — the assessment for those three needs the sanctioned VM run, not an in-session walk.
status: open
nature: issue
asset_group: [sports, defi, cefi, tradfi, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [orphan, orphan-real, single-walk, manifest-completeness, silent-write, sports, migration-orphan-sweep]
related:
  [
    data_pipeline_reconciliation_skill_2026_07_20.md,
    ../../codex/02-data/orphan-object-detection.md,
    ../../codex/02-data/reconciliation-census-and-compute-tiers.md,
    migration_verification_orphan_safety_2026_06_10.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: operator request 2026-07-21 — "Orphans not assessed for any AG — lets assess then"
depends_on: []
---

# Estate orphan assessment 2026-07-21 (partial)

> **What ran:** `instruments-service/scripts/migration_orphan_sweep.py --asset-group <ag> --dry-run` (+ the
> sports-specific `migration_orphan_sweep_sports.py --bucket both --dry-run`). A GCS→manifest single-walk, read-only
> (never deletes), classifying every object A_canonical_manifested / B_legacy_duplicate / C_manifest_infra /
> **E_orphan_real** (valid shape, rows>0, NO manifest row → the silent-write / manifest-completeness gap).

## MEASURED — SPORTS (both indexes; reports durable in GCS)

| bucket                                     | A_canonical | B_legacy_dup | C_infra | **E_ORPHAN_REAL** | size      |
| ------------------------------------------ | ----------- | ------------ | ------- | ----------------- | --------- |
| `market-data-tick-sports-prd` (odds)       | 474,125     | 0            | 3,096   | **27,348**        | 12.99 GiB |
| `instruments-store-sports-prd` (reference) | 960,703     | **34,385**   | 165,603 | **186,971**       | 22.60 GiB |

**≈214,319 ORPHAN_REAL** (real sports data on disk with no manifest row) + **34,385 LEGACY_DUPLICATE** (reference).
Per-object detail written to `gs://{bucket}/_index/audit/orphan_sweep_sports.parquet` (DURABLE — re-read these, do not
re-walk). ORPHAN_REAL = the data exists but honest-coverage under-reports it (a manifest-completeness hole, the inverse
of a phantom); these must be back-filled with `record_captured` (never deleted). This is a data-correctness finding —
operator-notified 2026-07-21.

## NOT COMPLETED — the manifest-download scale wall

- **prediction** — swept 1.15M objects cleanly (~8.8k/s) but then HUNG in the classification/manifest-join phase (30 min
  with zero progress; process killed). No result.
- **defi / cefi / tradfi** — FAILED in-session at "loading manifest cells":
  `requests.exceptions.ChunkedEncodingError: Connection broken: IncompleteRead` pulling the multi-GB consolidated
  `_index/availability_index.parquet` (defi's is ~1.8GB; tradfi died the same way; cefi never got past the load). **This
  is not a code bug** — a single-process in-session download of a multi-GB manifest is unreliable; this single-walk is
  meant to run on a VM (robust network + memory), which is why the tool is the CF-17 deliverable of
  `migration_verification_orphan_safety_2026_06_10.md`.

## Todos

- [ ] 1. [DATA] P1. **Back-fill the 214,319 sports ORPHAN_REAL rows** via `record_captured` (read the durable
      `orphan_sweep_sports.parquet` audit reports; NEVER delete — this is real data honest-coverage is missing). Verify
      the sports honest-coverage rises after.
- [ ] 2. [DATA] P1. **Triage the 34,385 sports LEGACY_DUPLICATE** (reference bucket) — content-verify each has a
      manifested canonical twin (the 5-part proof), then the human-only delete disposition.
- [ ] 3. [INFRA] P1. **Run the orphan sweep for defi / cefi / tradfi / prediction on a VM** (the in-session multi-GB
      manifest download is unreliable). Reuse the Tier-2 datapoint-validation VM (todo 32) or a migration VM; SPOT,
      monitored (no fire-and-forget), reports to `_index/audit/orphan_sweep_{ag}.parquet`. Operator
      offered/authorization pending 2026-07-21.
- [ ] 4. [CODE] P2. **Make the manifest load resumable / streamed** in `migration_orphan_sweep.py` (chunked download
      with retry, or read the index in row-group batches) so a multi-GB index does not break a single connection — this
      is what blocked defi/cefi/tradfi in-session.

## Lesson (do not re-learn)

The in-session single-walk works for small AGs but the **manifest DOWNLOAD** (not the object walk) is the bottleneck at
scale: a ~1.8GB `availability_index.parquet` breaks a single-process HTTP read (`ChunkedEncodingError`). Run large-AG
orphan sweeps on a VM, or fix the loader to stream/resume. Object listing (`list_blobs`) was NOT the problem —
prediction swept 1.15M objects fine; it was the manifest join-load that hung/broke.
