---
doc_type: issue
title: CME options_chain legacy flat layout — ~187.5M rows outside the TradFi single-leg @LIN canonicalization
summary:
  The TradFi single-leg FUTURE/OPTION `@LIN`/`@INV`-`YYYYMMDD` migration (2026-07-09) deliberately excluded 120,946 real
  CME `data_type=options_chain` manifest entries (~187.5M rows) that sit under a different, unverified legacy
  per-contract/spread flat layout — no `underlying=X/` subdirectory, raw per-contract filenames
  (`CC__FMH0025!.parquet`), manifest `underlying` values are per-contract keys (`ESU4_C5675`). Real, confirmed via live
  GCS listing; correctly excluded rather than risked at this scale, but the historical instrument-id canonicalization
  for this population remains open.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [instrument-id, canonicalization, tradfi, cme, options-chain, legacy-layout]
related:
  [
    instrument_id_format_canonicalization_2026_07_08.md,
    ../canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
source:
  "Real finding surfaced by the TradFi single-leg migrate-stage agent (wf_118d8268-18c, 2026-07-09) while scoping the
  @LIN/@INV historical migration against the real availability_index.parquet manifest (single-walk discipline, not a
  fresh corpus walk). Re-confirmed 2026-07-14 against the correct market-data-tick-tradfi-prd- bucket after an earlier
  same-day re-verification wrongly checked a deprecated flat bucket name."
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

The 2026-07-09 TradFi single-leg canonicalization
(`market-tick-data-service/scripts/ migrate_tradfi_single_leg_product_root_lin_2026_07_09.py`) real-scoped its target
population from the existing `availability_index.parquet` manifest and found **158,812 real shard objects (~1.19B
rows)** in the bundled-chain layout it targets (CME `futures_chain` 147,807 + `options_chain` 8,419 + CBOE
`futures_chain` 2,586). That migration ran to completion on a VM (`canonical-migration-tradfi-20260709-160919`,
7,500.6s, `error=4` out of ~158,812).

Separately, real GCS listing found **120,946 CME `data_type=options_chain` manifest entries (~187.5M rows)** — an order
of magnitude larger than the migrated population — sitting under a structurally different, unverified legacy layout:

- Real filenames like `CC__FMH0025!.parquet` — no `underlying=X/` subdirectory grouping contracts by underlying.
- Manifest `underlying` values are per-contract keys (e.g. `ESU4_C5675`), not the human-readable product root (`SP500`)
  the rest of this canonicalization effort targets.

This population was **correctly excluded from the 2026-07-09 migration** rather than risked at ~187M-row scale without
first verifying the real layout's semantics — this doc tracks that exclusion as open work, not a decision to never do
it.

## Why it matters

This is a real, large population of CME options-chain historical data that does not yet carry the canonical
`@LIN`/`@INV`-`YYYYMMDD` instrument-id format or the human-readable product-root convention (`ES→SP500`, `VX→VIX`) the
rest of TradFi now has. It represents a meaningful fraction of the total TradFi historical corpus by row count.

## Recommended next step

1. Real investigation first: confirm the actual real-world meaning of this flat per-contract layout (is it a legacy
   pre-bundling write path, a different real data product, or a partial/abandoned migration from an earlier session?) —
   do not assume it mirrors the bundled-chain semantics.
2. Once understood, scope a dedicated migration (same backup-first, idempotent, VM-eligible pattern already proven for
   the rest of this effort) to bring this population's `instrument_id`/`underlying` values in line with the canonical
   target.
3. Given the real scale (~187.5M rows), this is a strong candidate for VM-based execution from the start (per the
   operator's standing durability preference), not a laptop-session migration.

## 🔴 2026-07-14 — re-verification could NOT confirm this population exists at the described location

Investigated step 1 of the recommended next step above (real investigation of the flat layout's semantics) as a
precondition to actually building + running the migration (operator asked to do the full migration, not just scope it).
Found:

- **The current TradFi writer structurally cannot produce this shape.**
  `market-tick-data-service/market_tick_data_service/ engine/orchestrator/partitioned_writer.py::_resolve_writer_file_name`
  (lines 135-162) has exactly two branches — `underlying={U}/ticks.parquet` for any derivative type (which
  `options_chain` always is, per `symbol_rules.py:258`), or a flat `{symbol}.parquet` for non-derivatives only. There is
  no code path that emits a flat filename for a `data_type=options_chain` row. So whatever wrote this layout predates
  the current writer — consistent with the doc's own hypothesis, not new.
- **Could not find the population itself.** The consolidated manifest (`_index/availability_index.parquet` in
  `market-data-tick-tradfi-central-element-323112`) is **17 days stale** (`gsutil stat` update time 2026-06-27,
  predating this doc's own 2026-07-10 creation) and shows only 291 CME `options_chain` rows today, all with blank
  `instrument_type`/`underlying` and `row_count=null` — nothing resembling 120,946 rows / 187.5M row_count sum. A
  **real, bounded GCS scan** (not a whole-corpus walk — scoped exactly to `venue=CME/instrument_type=options_chain/...`,
  across all 1,996 real day-partitions currently in the bucket, tried 4 plausible path-shape variants) found **zero
  matching objects on any variant, on any day**. Cross-checked the AWS S3 mirror (empty — GCP is the sole real store)
  and git history 2026-07-09→2026-07-14 for any intervening cleanup/migration (found only an unrelated, much smaller fix
  — `042ccc36`, 6 CME options_chain objects, three orders of magnitude short of 120,946).
- **This directly contradicts the finding this doc is built on.** Either (a) the 120,946/187.5M population was itself
  fully migrated or deleted by an untracked process sometime between 2026-07-10 and now with no commit evidence, (b) the
  original finding read a transient or incorrect manifest/index state, or (c) the real data lives somewhere this
  re-verification didn't check (a different bucket/region/path shape not among the 4 tried).

**Per the workspace's data-pipeline-correctness hard rule** (a data-correctness finding that contradicts a prior finding
needs operator notification, not a silent migration attempt against an unconfirmed target) — **status is NOT changed to
resolved**. No migration was designed or run against this population; doing so against an unconfirmed target risks
either a silent no-op or, worse, writing to the wrong location. Needs an operator decision on how to reconcile: re-run
the manifest consolidator (currently 17 days behind) and re-check, or track down exactly which manifest snapshot the
original 2026-07-09 finding-agent (`wf_118d8268-18c`) used to get the 120,946-row figure, since it doesn't match what's
queryable today.

## 🟢 2026-07-14 (later same day) — RESOLVED: (c) was correct, the 2026-07-14 re-verification used the WRONG bucket

Operator suggested checking whether the manifest consolidator itself needed attention. Investigating that surfaced the
real root cause of the 🔴 entry above: **`market-data-tick-tradfi-central-element-323112` (the flat, no-env-tier bucket
name the re-verification checked) is a DEPRECATED legacy bucket** — the live, current bucket is
`market-data-tick-tradfi-**prd**-central-element-323112` (env-tiered, per the workspace's bucket-name-SSOT
canonicalization). Two separate Cloud Run consolidator jobs exist for TradFi market-data:
`uts-prod-manifest-consolidator-market-data-tradfi` (targets the `-prd-` bucket, cron **ENABLED**, running successfully
every minute) and `uts-prod-manifest-consolidator-market-data-tradfi-legacy` (targets the flat bucket, cron **PAUSED** —
explaining the "17 days stale" reading exactly: nobody's been running it because it's the wrong bucket to be watching).

**Re-verified against the correct `-prd-` bucket, for real:**

- Consolidated manifest is fresh (updated minutes before this check, not 17 days stale).
- **242,210 real CME `options_chain` manifest entries, `capture_status=captured` on 100% of them, `row_count` summing to
  380,638,413 rows** — roughly double the original 120,946-entry / ~187.5M-row estimate (the population has grown since
  the 2026-07-09 finding, consistent with ongoing live capture, not a discrepancy).
- **120,946 of the 242,210 have `instrument_type=options_chain` explicitly stamped** — an EXACT match to the original
  finding's headline number, confirming the original 2026-07-09 finding was correct all along; the 2026-07-14
  re-verification's "population doesn't exist" conclusion was itself the error (wrong bucket, not stale/missing data).
- Confirmed the real object layout directly via `gsutil ls` (not just the manifest): real, live, flat per-contract files
  with no `underlying=X/` grouping, e.g.
  `raw_tick_data/by_date/day=2024-07-11/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/instrument_type=options_chain/data_type=options_chain/6AH5.parquet`
  — matches the doc's original description exactly (note the real path root is `raw_tick_data/by_date/`, not
  `instrument_availability/by_date/` — that prefix is instruments-service's reference-data tree, a different concept;
  this correction's path is MTDS's own market-data tree).

**Status: back to open (not resolved) for the RIGHT reason** — the population is real, confirmed, and needs the
migration this doc always called for. The 🔴 entry above is superseded, not deleted (kept for the record of how the
wrong-bucket mistake happened). Next: scope + build + run the real migration against
`market-data-tick-tradfi-prd-central-element-323112`, VM-eligible given the ~380M-row scale (comparable to or larger
than the prior 158,812-object/1.19B-row single-leg migration that took ~2h on a VM).
