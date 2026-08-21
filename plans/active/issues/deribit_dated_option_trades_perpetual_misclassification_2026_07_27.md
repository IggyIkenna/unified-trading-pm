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
    /plans/archive/2026_08/issues/deribit_combo_perpetual_partition_move_2026_07_21.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
created: 2026-07-27
author: unknown
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
context_scope: [/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md, /plans/archive/2026_08/issues/deribit_combo_perpetual_partition_move_2026_07_21.md, market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py, /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch6_2026_08_02.md]
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
2. ✅ **Exhaustive census — DONE 2026-08-07** (see Progress Log and Evidence §2 below). Corpus-wide listing across all
   `day=*` partitions: **28,158 option-shaped objects** across **497 distinct days**, totalling **≈988 GB**. Affected
   period: **2024-03-08 to 2026-05-01** (not "2019-present" — no such objects exist before March 2024). Affected base
   assets: AVAX_USDC, MATIC_USDC, TRX_USDC, XRP_USDC. Source:
   `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch6_2026_08_02.md` todo 2.
3. **Backfill/reclassify pass** — once the writer bug is fixed going forward, already-captured mis-classified objects
   need their own migration (split the merged file back into per-instrument `option/` objects, or reclassify+recanon in
   place) — likely mirroring the `--exclude-venues`-then-dedicated-pass pattern already used for HYPERLIQUID/ASTER in
   the parent migration.
4. **Re-run Script 1 for DERIBIT specifically**, once (1)-(3) land, so DERIBIT's `instrument_id` content column is
   canonicalized like every other venue — tracked as a standing follow-up in
   `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s Progress Log alongside the
   HYPERLIQUID/ASTER follow-up.

## Evidence / how to reproduce

**§1 — Original 5-day samples (2026-07-27):**

```
gcloud storage ls -l gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2025-12-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/data_type=trades/** | sort -k1 -n -r | head -5
```

returns the 6.3GB `XRP_USDC-5DEC25-2D2-C.parquet` object as the largest file in that partition by a wide margin (next
largest legitimate perpetual object in the same partition is <2MB). Repeat for any of the 5 days in the table above to
reproduce.

**§2 — Corpus-wide census (2026-08-07, `cefi_satellite_ao_dispatch_batch6_2026_08_02.md` todo 2):**

```bash
# List all objects in the DERIBIT perpetual/trades path across all day= partitions
gcloud storage ls -l \
  "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=*/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/data_type=trades/**" \
  > full_listing.txt

# Filter for dated-option-shaped files (ending -C.parquet or -P.parquet)
# then tally distinct days and total bytes
awk '$3 ~ /-[CP]\.parquet$/' full_listing.txt | awk '
  match($3, /day=([0-9]{4}-[0-9]{2}-[0-9]{2})/, a) { days[a[1]] = 1 }
  { total += $1; count++ }
  END { printf "Objects: %d  Days: %d  Bytes: %d (%.2f GB)\n", count, length(days), total, total/(1024^3) }
'
```

Output:

```
Objects: 28158  Days: 497  Bytes: 1060914050589 (988.05 GB)
```

**Census key findings:**

- **38,839** total objects in the `instrument_type=perpetual/data_type=trades/` path (all day partitions)
- **28,158** (72.5%) are option-shaped (`-C.parquet` / `-P.parquet`) — misclassified in the perpetual partition
- **497** distinct `day=` partitions affected
- **Total affected byte volume: ~988 GB** (1,060,914,050,589 bytes)
- **Affected date range: 2024-03-08 to 2026-05-01** — no option-shaped objects exist before March 2024
- **Affected base assets:** AVAX_USDC, MATIC_USDC, TRX_USDC, XRP_USDC
- **Year breakdown:** 2024: 7,816 objects | 2025: 17,248 objects | 2026: 3,094 objects
- **Largest single object:** `day=2024-12-01/XRP_USDC-6DEC24-2D6-C.parquet` — 9.65 GB

## Todos

- [x] ✅ [DATA] P1. **Root-cause + fix the writer-side bug — DONE, verified by plan_reconciler (cefi tranche,
      agt-2e82f7, 2026-08-16).** `market-tick-data-service@06c07089` (2026-08-15, "fix(cefi): recognize Deribit
      decimal-strike (D-separator) option symbols"), verified ancestor of `origin/live-defi-rollout`. `_OPTION_SYMBOL_RE`
      required a pure-digit strike, so DERIBIT's `D`-decimal-separator sub-dollar strikes (e.g. `2D3`=2.3, the exact
      `XRP_USDC-30JAN26-2D3-P.parquet` shape cited in this doc's own evidence table) fell through to the venue-level
      PERPETUAL default. Ships with a 6-test regression suite pinning the symbol to `InstrumentType.OPTION`.
- [ ] [DATA] P1. **DEFERRED — census/backfill/reclassify/Script-1-rerun still open.** Run an exhaustive corpus-wide
      census, backfill/reclassify already-captured objects, then re-run Script 1 for DERIBIT specifically (see "What's
      NOT done / follow-up needed" above). The 2026-08-07 census (28,158 objects/497 days/~988GB) predates the writer
      fix and needs re-running against it.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - `execution_scope: human`; the sole
  todo bundles a writer root-cause, a corpus-wide census, and a reclassify migration of already-captured multi-GB
  objects.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged) — all four still resolve and remain the
  right minimal set for the still-open writer root-cause todo.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict; the
  sole todo still bundles an unsolved writer root-cause, a corpus-wide census, and a reclassify migration, none of which
  is worker-determinable alone.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict; the
  sole todo still bundles an untraced writer root-cause, a corpus-wide census, and an open design fork on the
  remediation approach, none of which is worker-determinable alone.
- **corpus-wide census 2026-08-07** (`cefi_satellite_ao_dispatch_batch6_2026_08_02.md` todo 2, slot 13): "What's NOT
  done" item 2 is now complete. Full `gcloud storage ls -l` enumeration across all `day=*` partitions in the
  `venue=DERIBIT/instrument_type=perpetual/data_type=trades/` path: **28,158 option-shaped objects** (72.5% of 38,839
  total) across **497 distinct days**, totalling **≈988 GB** (1,060,914,050,589 bytes). Affected period corrected to
  **2024-03-08 to 2026-05-01** — no option-shaped objects found before March 2024 despite "2019-present" range
  enumerated. Affected base assets: AVAX_USDC, MATIC_USDC, TRX_USDC, XRP_USDC. Items 1/3/4 remain open. Evidence: see §2
  above.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — execution_scope: human. Sole checkbox
  bundles the untraced writer-side classification root-cause (adapter/code path not yet identified) with other
  sub-items; the corpus-wide census sub-item is now done (2026-08-07, batch6 todo 2) but root-cause itself remains open
  investigation.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — added
  `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch6_2026_08_02.md`, the source of the 2026-08-07 corpus-wide
  census now cited 3 times in this doc's own text (todo 2's completion note, Evidence §2, and the Progress Log entry
  above); the prior 4 entries re-verified, still resolve, unchanged.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid - the sole open todo still bundles an
  untraced writer-side classification root-cause with the (now-blocked-on-that-root-cause) backfill/reclassify migration
  and the DERIBIT-specific Script-1 re-run; "find the writer-side bug" has no stated done-when a worker can hit
  deterministically. No cheat-sheet precedent from today's rulings applies (not an IAM/credential gate, not a
  reversibility-qualified delete, not a self-service script-flag gap). Independently corroborated by
  `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`'s "Deferred — human-only" section (same-day, separate
  `/ag-closeout-audit` run): "the root-cause item is open-ended investigation into an untraced adapter/code path with no
  stated done-when beyond 'find the bug.'" Reaffirms 4 prior passes (2026-07-30, 2026-08-04, 2026-08-06, 2026-08-07).

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — execution_scope: human, explicitly
  declared. Sole todo bundles an untraced root-cause investigation (no code path identified) plus a ~988GB/497-day
  reclassification migration gated on that root cause.
- **na-eligibility-audit 2026-08-16** [body-hash:e0e6e2c3ca7c4051]: KEEP-NA, valid — Doc read in full end-to-end. Todo 1 (writer root-cause) is genuinely DONE: independently verified commit market-tick-data-service@06c07089 is an ancestor of origin/live-defi-rollout (checked pre- and post-fetch in the slot's own c…
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
