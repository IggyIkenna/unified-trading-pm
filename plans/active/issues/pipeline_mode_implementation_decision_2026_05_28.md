---
title: "pipeline_mode column — half-implemented; operator-decided IMPLEMENT properly (2026-05-28)"
created: 2026-05-28
author: slot-1 (ikenna)
source:
  - plans/active/cefi_venue_backfill_coverage_remediation_2026_05_27.md §6I item 3
  - plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md (original design intent)
  - ikenna_orchestrator/pings/slot_9.md (2026-05-28 05:58Z BLOCKED-OPERATOR-DECISION)
  - GCS spot-check 2026-05-27 of `_index/availability_index.parquet` (both cefi buckets)
locked_by: pipeline_mode_implementation_2026_05_28
---

## What I found

`pipeline_mode` was designed as a manifest column tagging each captured row with the source pipeline that produced it —
`batch_tardis`, `batch_databento`, `batch_ccxt`, `live_websocket`, etc. Original design intent (archived
[`live_pipeline_mtds_mdps_features_2026_05_08`](../../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)):
"batch ↔ live reconciliation is a `GROUP BY pipeline_mode` over the same manifest."

**Current state** (verified 2026-05-27, both `market-data-tick-cefi-prd-…` 2.6M rows + legacy no-env
`market-data-tick-cefi-…` 35.7M rows):

- UAC manifest schema **declares** the column.
- Code passes a `pipeline_mode` arg through ~50 files (writers, readers, function signatures).
- **The column is empty/NULL on every one of ~38M manifest rows** across both buckets.
- **The on-disk partition path does NOT include `pipeline_mode=`** — actual path is
  `day=…/asset_group=…/venue=…/instrument_type=…/data_type=…`.
- Any `GROUP BY pipeline_mode` consumer is currently grouping by an always-empty column.

It is a half-implemented half-feature: schema column + function arg present, but no write-side persistence and no
on-disk partition.

## Why it matters

- **Batch ↔ live reconciliation cannot distinguish source pipelines** — a Tardis batch backfill row and a
  live-websocket-captured row for the same shard are indistinguishable.
- Any analytics querying "captured rows by pipeline source" returns garbage (all NULL).
- The column is dishonest — declared in schema but unpopulated. Composes with the data-pipeline-correctness HARD RULE:
  this is exactly the "constant-says-vN-but-data-says-X" pattern the operator codified 2026-05-20.

## Recommended decision (operator-decided 2026-05-28)

**IMPLEMENT properly.** REMOVE was rejected because the documented downstream consumer (batch ↔ live reconciliation per
pipeline mode) is a real architecture decision worth preserving.

## Scope + constraint

Phased implementation in
[`plans/active/pipeline_mode_implementation_2026_05_28.md`](../pipeline_mode_implementation_2026_05_28.md).

**Key constraint**: CLAUDE.md HARD RULE "Single-walk discipline" — partition-key additions are review-blocking outside a
whole-corpus migration window. Therefore:

- **Ships now (this plan)**: column-level implementation — schema enum, writer-fill, existing-row backfill, consumer
  migration.
- **Deferred to next migration window (named successor plan)**: on-disk partition path — `pipeline_mode=` partition
  piggybacks on the next whole-corpus walk, not a separate pass.

## Unblocks

- `cefi_venue_backfill_coverage_remediation_2026_05_27.md` §6I item 3 (slot 9's BLOCKED-OPERATOR-DECISION cleared).
- Re-opens the reconciliation pattern in `batch_live_symmetry_master` epic.
