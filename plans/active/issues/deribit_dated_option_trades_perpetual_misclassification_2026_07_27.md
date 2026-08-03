---
doc_type: issue
title:
  DERIBIT dated-option trades mis-classified into instrument_type=perpetual/data_type=trades — monolithic 1.7-6.3GB
  files OOM Script 1's canonical-migration workers
summary: >-
  Found live during the /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md Script-1
  corpus-wide parquet-content migration (--apply, 42-VM fan-out). Every OOM (`rc=137`) hit so far correlates with the
  SAME signature — a single
  `venue=DERIBIT/instrument_type=perpetual/data_type=trades/<BASE>_<QUOTE>-<DATE>-<STRIKE>-<C|P>.parquet` object (a
  DATED-OPTION wire symbol, wrongly living in the `perpetual/` partition) at 1.7-6.3GB, vs. <1-2MB for any correctly-
  classified single-instrument file in the same partition. The size implies many distinct dated-option instruments'
  trades are being merged into one "perpetual" blob per day, not a single mis-tagged instrument. This is a genuine,
  separate data-quality/writer bug, NOT the same as `deribit_combo_perpetual_partition_move_2026_07_21.md`'s COMBO-
  shape mispartitioning (different symbol shape, different suspected code path), and NOT fixed by this migration —
  Script 1 works around it via `--exclude-venues ... DERIBIT`, so DERIBIT's content-column canonicalization for
  `perpetual/trades` remains OPEN after this campaign completes. Needs its own follow-up: (1) find + fix the writer-
  side classification bug, (2) a dedicated backfill/reclassify pass for already-captured data once the classifier is
  fixed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [deribit, misclassification, data-correctness, oom, canonical-migration, script-1, options]
related:
  [
    /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
created: 2026-07-27
parent_epic: cefi_master
priority: P1
estimate_class: research
assigned_role: data_engineering
source:
  "Found live during the Script-1 (migrate_cefi_content_instrument_id_catalogue_2026_07_17.py) corpus-wide --apply
  campaign, 2026-07-27 — see /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md's
  Progress Log, 2026-07-27T06:55Z and 07:05Z entries, for the full incident trail this doc summarizes."
assigned_vm: NA
execution_scope: human
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py,
  ]
resolved_by:
---

# DERIBIT dated-option trades mis-classified into `instrument_type=perpetual` — monolithic multi-GB files

> Investigation-only record (this doc). No code changed, no GCS objects moved/deleted, no manifest rows written by this
> doc's own author — the workaround described below (`--exclude-venues`) is a migration-scope skip, not a data fix.

## What I found

While running Script 1 (`migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`, the parquet-content
canonicalization pass for `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s todo 3)
as a 42-VM `--apply` fan-out over the full cefi corpus, 6 of the 42 shard VMs were killed with `rc=137` (SIGKILL/OOM) on
`e2-standard-16` (64GB RAM) machines. Reducing `--workers` from 24 to 10 did NOT fix it (one retry died even faster:
4,000/168,624 files @ 391s vs. the original attempt's 7,800/168,622 @ ~2,020s) — ruling out worker-concurrency as the
cause.

Sampling the largest objects in each OOM'd shard's date range found the exact same signature every time: one giant file
at
`raw_tick_data/by_date/day=<D>/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/ instrument_type=perpetual/data_type=trades/<BASE>_<QUOTE>-<EXPIRY>-<STRIKE>-<C|P>.parquet`
— a **dated single-leg option** wire symbol (e.g. `XRP_USDC-30JAN26-2D3-P`, `MATIC_USDC-20MAY24-0D67-P`) sitting in the
`perpetual/` partition, where every correctly-classified perpetual object in the same partition is <2MB.

Confirmed across 5 independent day samples spanning most of the corpus's history:

| Day        | File                                | Size    | Shard date-range hit              |
| ---------- | ----------------------------------- | ------- | --------------------------------- |
| 2024-05-20 | `MATIC_USDC-20MAY24-0D67-P.parquet` | 1.73 GB | `cs8-1` (2024-05-11..06-23)       |
| 2024-11-10 | `XRP_USDC-10NOV24-0D6-C.parquet`    | 2.08 GB | `cs8-5` (2024-11-05..12-18)       |
| 2025-05-15 | `XRP_USDC-23MAY25-3D1-C.parquet`    | 2.33 GB | `cs9-3` (2025-05-02..06-15)       |
| 2025-12-01 | `XRP_USDC-5DEC25-2D2-C.parquet`     | 6.30 GB | `cs10-2` (2025-11-23..12-20)      |
| 2025-12-25 | `XRP_USDC-30JAN26-2D3-P.parquet`    | 2.45 GB | `cs10-3` (2025-12-21..2026-01-16) |

(Shard ranges are from `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s Script-1
fan-out plan — every sampled range that hit `rc=137` had one of these files; no range that stayed healthy was checked
for a similar file, so this is not yet an exhaustive corpus census — see "What's NOT done" below.)

## Why this OOMs Script 1's workers (impact, not root cause)

Script 1 downloads a parquet object's full bytes, parses to a pandas `DataFrame`, computes a patched copy (`df.copy()`),
serializes the result, and — after the write — re-downloads and re-parses the SAME object to verify idempotency. For a
single ~2-6GB parquet file, that round-trip plausibly holds 30-50GB+ resident at peak (raw bytes + parsed frame + copied
frame + serialized output + the verify re-read/re-parse), which is enough to OOM even a 64GB machine on its own —
independent of how many OTHER (normal-sized) files other concurrent workers are processing. This is why lowering
`--workers` made no difference: the failure is one worker hitting one oversized file, not many workers competing for
memory.

## Why the file is so large (my working theory, not confirmed)

Every correctly-classified single-instrument object in this partition is under 2MB. A multi-GB file implies MANY
distinct dated-option instruments' trades are being merged/appended into ONE "perpetual" file per day, rather than one
mis-tagged instrument sitting alone. That's consistent with a writer-side bug that (a) misclassifies dated-option trades
as `instrument_type=perpetual` (rather than `option`) AND (b) as a consequence, routes them all through whatever
key/grouping the perpetual lane uses for that (venue, day) — likely collapsing what should be N separate per-instrument
objects into one shared object. This has NOT been traced to a specific adapter/code path in `market-tick-data-service` —
that's the first open item below.

## What this is NOT

- **Not** the same issue as `deribit_combo_perpetual_partition_move_2026_07_21.md` — that doc covers DERIBIT **COMBO**
  instruments (multi-leg spread symbols) mispartitioned into `perpetual`/`future`; the files here are single-leg DATED
  OPTIONS, a different symbol shape, and the scale (1.7-6.3GB vs. that doc's 15,119-row census) suggests a different
  mechanism. Worth cross-checking once someone picks this up, but not assumed to share a root cause or a fix.
- **Not** the DERIBIT spot/perpetual mislabel-collision class from
  `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 8/10 (a FILENAME-rename collision between a
  spot and perpetual instrument wanting the same canonical name) — unrelated symbol shape and unrelated failure mode
  (that one causes a rename skip, not an OOM).

## Current workaround (does not fix the underlying data)

Script 1's corpus-wide `--apply` campaign added `DERIBIT` to `--exclude-venues` (alongside a pre-existing
HYPERLIQUID/ASTER exclusion for an unrelated live-writer-race reason) for every shard that hit this OOM class, so the
migration can complete for the rest of the corpus. **This means DERIBIT's `perpetual/trades` content-column
canonicalization is NOT being done by this campaign at all** — those files (mis-classified AND correctly-classified
DERIBIT perpetual/trades objects alike, since `--exclude-venues` skips the whole venue, not just the offending files)
remain exactly as they were before Script 1 ran, for every shard where the exclusion was applied.

## What's NOT done / follow-up needed

1. **Root-cause the writer-side classification bug** — find the exact `market-tick-data-service` adapter/ingestion path
   that produces `instrument_type=perpetual` for a DERIBIT dated-option trade, and why multiple instruments' trades
   appear to land in one merged object instead of per-instrument objects.
2. **Exhaustive census** — this doc's evidence is 5 sampled days, not a corpus-wide count. Someone should determine how
   many days/how much of DERIBIT's history (2019-present) carries this pattern, and the total affected byte volume,
   before scoping a fix.
3. **Backfill/reclassify pass** — once the writer bug is fixed going forward, already-captured mis-classified objects
   need their own migration (split the merged file back into per-instrument `option/` objects, or reclassify+recanon in
   place) — likely mirroring the `--exclude-venues`-then-dedicated-pass pattern already used for HYPERLIQUID/ASTER in
   the parent migration.
4. **Re-run Script 1 for DERIBIT specifically**, once (1)-(3) land, so DERIBIT's `instrument_id` content column is
   canonicalized like every other venue — tracked as a standing follow-up in
   `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s Progress Log alongside the
   HYPERLIQUID/ASTER follow-up.

## Evidence / how to reproduce

```
gcloud storage ls -l gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2025-12-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/data_type=trades/** | sort -k1 -n -r | head -5
```

returns the 6.3GB `XRP_USDC-5DEC25-2D2-C.parquet` object as the largest file in that partition by a wide margin (next
largest legitimate perpetual object in the same partition is <2MB). Repeat for any of the 5 days in the table above to
reproduce.

## Todos

- [ ] [DATA] P1. **Root-cause + fix DERIBIT's dated-option-into-perpetual misclassification** — find the writer-side
      bug, run an exhaustive corpus-wide census, backfill/reclassify already-captured objects, then re-run Script 1 for
      DERIBIT specifically (see "What's NOT done / follow-up needed" above).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - `execution_scope: human`; the sole
  todo bundles a writer root-cause, a corpus-wide census, and a reclassify migration of already-captured multi-GB
  objects.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged) — all four still resolve and remain the
  right minimal set for the still-open writer root-cause todo.
