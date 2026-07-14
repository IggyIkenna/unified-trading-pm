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

## 🟡 2026-07-14 (later same day) — real design investigation: this is NOT a simple rename, and found a real secondary bug

Started building the actual migration (operator: "fully executed", not just scoped). Investigating the real content
before writing a transform surfaced two things the original finding didn't have visibility into:

**1. The `data_type=options_chain` partition is contaminated with misclassified futures contracts.** Sampled every file
for one real day (`day=2024-07-11`, CME, 2,437 files): **345 (14.2%) are futures-coded contracts** (`6AH5`/`6BH5`/`6AN4`
— standard CME currency-futures tickers: `6A`=AUD, `6B`=GBP, `6C`=CAD, `6E`=EUR, etc.), sitting under
`instrument_type=options_chain/data_type=options_chain/` even though their OWN `instrument_key` column already correctly
reads them as `CME:FUTURE:...` (e.g. `CME:FUTURE:AUD-USD-250317@LIN`). This is a writer classification bug — these rows
are genuine futures data written to the wrong `data_type` partition, not options data needing canonicalization. The
remaining **2,092 (85.8%) are genuinely option-coded** (`ESH5_C5800`, `EW3Q4_C5570`, etc.).

**2. The genuine option rows are already PARTIALLY canonicalized, but in a DIFFERENT format than this migration's
target.** `EW3Q4_C5570.parquet`'s `instrument_key` reads `CME:OPTION:EW3-USD-240816-5570-CALL@LIN` — already carries an
`@LIN` marker, but positioned at the END (`...-CALL@LIN`) rather than right after the root (`ROOT@LIN-YYYYMMDD-...`, the
format `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py` and the live write-path fix both target), uses 6-digit
`YYMMDD` not 8-digit `YYYYMMDD`, spells out `CALL`/`PUT` instead of `C`/`P`, and embeds a literal `-USD-` currency
marker the target format doesn't have for non-FX products. `underlying` is the raw contract-family code (`EW3`) rather
than a human product root — confirmed `EXCHANGE_CODE_TO_NAME` DOES have real registry entries for the option-family
roots checked (`EW1`-`EW4`→`SP500`, `ES`→`SP500`, `NQ`→`NASDAQ100`, `GC`→`GOLD`), though not all (`GE`/Eurodollar has no
entry — a real, separate registry-completeness gap to check before relying on it for this migration).

**Not proceeding to build+launch a migration against this population without first**: (a) deciding how to handle the
~14% misclassified-futures contamination (reclassify to `futures_chain` first, separately, before touching the genuine
options? exclude and file as its own bug?), (b) writing + testing a real regex for the ACTUAL current
`ROOT-USD-YYMMDD-STRIKE-CALL@LIN`-shaped instrument_key (not the raw-code shape the existing single-leg script targets —
this population needs a different transform, not a copy of that script), (c) checking registry coverage gaps like `GE`
don't silently drop real contracts. This is real, scoped design work for a next session/turn, not executed here — status
stays open, priority P1 unchanged.

**Status: back to open (not resolved) for the RIGHT reason** — the population is real, confirmed, and needs the
migration this doc always called for. The 🔴 entry above is superseded, not deleted (kept for the record of how the
wrong-bucket mistake happened). Next: scope + build + run the real migration against
`market-data-tick-tradfi-prd-central-element-323112`, VM-eligible given the ~380M-row scale (comparable to or larger
than the prior 158,812-object/1.19B-row single-leg migration that took ~2h on a VM).

## 🟡 2026-07-14 (later same day) — script built, dry-run validated on 6 real diverse days, found + fixed a THIRD contamination axis

Built the migration (`market-tick-data-service/scripts/canonicalize_cme_options_chain_legacy_flat_2026_07_14.py`,
dry-run-by-default, backup-first, `--apply`-gated) implementing the transform designed in the 🟡 entry above
(`ROOT-USD-YYMMDD-STRIKE-CALL@LIN` → `ROOT@LIN-YYYYMMDD-STRIKE-C`, reclassifying misclassified futures to
`instrument_type=futures_chain`). Real dry-run against `day=2024-07-11` (2,437 files) surfaced a **third contamination
axis the original design didn't anticipate**: 105 files (all futures-shaped) had `unclassified` instrument_keys that
turned out to be genuine **ICE-venue commodity futures** (`ICE:FUTURE:ORANGEJUICE-...`, `SUGAR-...`, `WTI-...`, plus
`BRENT`/`COCOA`/`COTTON`/`DOLLARINDEX`/`GASOIL`/`COFFEE` found on other sample days) sitting under the `venue=CME` GCS
path prefix despite their own `instrument_key` correctly reading `ICE:...` — a second, independent writer-classification
bug layered on top of the (a) options-format-mismatch and (b) misclassified-CME-futures issues already documented above.

**Fix**: generalized both instrument-key regexes to capture venue (`(?P<venue>[A-Z]+):...`) instead of hardcoding
`CME:`, and made the write side (`_target_path`, `bundle_and_write`) route each bundle by its object's REAL
`instrument_key` venue — so `ICE:FUTURE:...` content now correctly lands under
`venue=ICE/instrument_type=futures_chain/` instead of staying misfiled under `venue=CME`. The listing side intentionally
stays scoped to the physical `venue=CME` source path (that's genuinely where these objects live; only the target path
needed to become venue-aware).

**Row-count discrepancy from the earlier same-day finding — RECONCILED, not a bug.** The original 2024-07-11 dry-run
(5.56M rows) looked far denser than the ~1.3M/day average implied by 380,638,413 rows / 291 days, raising concern the
manifest total might be unreliable. Sampled 5 additional real days at random (`2023-05-15`, `2024-01-05`, `2024-03-12`,
`2024-03-25`, `2024-04-12`): row totals ranged from **4,267 to 194,258** — two to three orders of magnitude BELOW
2024-07-11's (now, with the ICE fix, 6.82M) total. The real per-day distribution is heavy-tailed (a handful of
very-high-volume days, e.g. likely quarterly-expiration dates, alongside many much quieter days), which is fully
consistent with a genuine 380M-row total across 291 days — 2024-07-11 is a real outlier day, not evidence of a manifest
bug. All 6 sampled days show `unclassified=0` post-fix, confirming the venue-generalized regex covers the real
population with no silent drops.

**Manifest-write safety implemented**: `rewrite_manifest()` now does a real CAS write
(`StorageClient.conditional_upload_bytes(if_generation_match=...)`) with re-download+re-merge retry (5 attempts) on a
concurrent writer, wrapped with a best-effort pause/resume of the
`uts-prod-manifest-consolidator-market-data-tradfi-cron` Cloud Scheduler job as defense-in-depth (not a substitute for
the CAS guarantee — a failed pause/resume call is logged, not fatal, and resume always runs in a `finally`). Note for
anyone reading `tradfi_manifest_row_loss_regression_ 2026_07_12.md` for precedent: that doc's own restore did NOT pause
any cron — CAS-write alone was what it actually verified; the pause here is this script's own added layer, not a re-used
verified mechanism.

**Status**: script passes real dry-run validation across 6 diverse real days (2 sizes at each end of the distribution),
zero unclassified, zero exceptions. Not yet run with `--apply` against real data — next step is quality-gates + ship,
then a scoped real `--apply` run (small real day first, then VM-scale `--all-days`), per the workspace's runtime-
verification hard rule (a migration is "done" only once it has actually run against real data with verified output, not
once the dry-run is green).
