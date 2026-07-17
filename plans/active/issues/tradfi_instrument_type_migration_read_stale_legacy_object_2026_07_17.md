---
doc_type: issue
title:
  Completed TradFi instrument_type migration corrupted its own manifest by reading the STALE legacy object (425,096
  instruments' coverage lost)
summary:
  canonicalize_tradfi_instrument_type_2026_07_16.py (run + flipped DONE on 2026-07-16) re-derived each blank captured
  row's instrument_type from the LEGACY by_date object path instead of the CANONICAL pipeline_mode-partitioned one.
  Where both exist they can disagree wildly — the legacy object is a stale partial. The migration therefore overwrote
  correct manifest counts with partial ones and mis-attributed the shortfall to a "pre-existing manifest-vs-object
  staleness bug" in its own DRIFT warnings, its docstring, and the parent plan's P9 entry. Independently reproduced
  2026-07-17. Rollback snapshot exists; repair = re-run with canonical-path-first.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [data-correctness, manifest, instrument_type, migration, tradfi, availability-index]
related: [data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
source:
  surfaced by the cefi/defi instrument_type backfill (sibling migration) 2026-07-17; independently reproduced before
  filing
---

# TradFi instrument_type migration read the STALE legacy object → 425,096 instruments' coverage lost

> **Big finding — operator notified in chat 2026-07-17.** A migration that was run, verified, and flipped `- [x] DONE`
> yesterday corrupted the data it was fixing. The bug is in the migration, not in the writer it was repairing.

## What happened

`instruments-service/scripts/canonicalize_tradfi_instrument_type_2026_07_16.py` (parent plan
`data_status_page_ux_and_canonicalisation_2026_07_16.md`, P9 Q2, shipped `instruments-service@66258618`) backfilled
blank `instrument_type` on tradfi's `_index/availability_index.parquet` by doing a targeted per-shard read of that
shard's own `instruments.parquet` and re-deriving the type from the object's own column. That design is right.

**The bug: it resolved the object at the LEGACY path** (`instrument_availability/by_date/day=<D>/venue=<V>/`) rather
than the **CANONICAL** source-aware path
(`instrument_availability/by_date/day=<D>/pipeline_mode=<M>/asset_group=<AG>/venue=<V>/`). Both objects can exist for
the same shard, and **they are not the same data** — the legacy one is a stale partial left behind by the pipeline_mode
partition migration. Because the script re-stamps `row_count`/`instrument_count` from whatever object it read, it wrote
the PARTIAL counts over the manifest's correct ones.

It then **mis-diagnosed its own damage**: the discrepancy surfaced in its per-shard `shard count DRIFT` warnings, and
was written up (in the script docstring AND the parent plan's P9 Q2 checkbox) as "a separate, pre-existing
manifest-vs-object staleness bug likely not tradfi-specific, worth its own follow-up investigation". That explanation is
wrong — the drift was **manufactured by the migration itself**.

## Evidence (independently reproduced 2026-07-17, not taken from the sibling agent's report)

Aggregate, live vs the migration's own pre-migration snapshot
(`_index/snapshots/pre_tradfi_instrument_type_canon_2026_07_16_20260716T143452Z.parquet`):

| metric                        | pre-migration snapshot | live now   | delta        |
| ----------------------------- | ---------------------- | ---------- | ------------ |
| Σ `instrument_count` (tradfi) | 47,149,715             | 46,724,619 | **−425,096** |

Worked example — **CME 2026-06-28**:

| source                                    | rows / counts                                              |
| ----------------------------------------- | ---------------------------------------------------------- |
| manifest BEFORE (snapshot)                | ONE blank-type row, `instrument_count=74,005`              |
| manifest AFTER (live)                     | OPTION 2,566 + FUTURE 32 + COMBO 228 = **2,826**           |
| **CANONICAL object** (`pipeline_mode=…`)  | **74,005 rows** — OPTION 69,212 / COMBO 4,446 / FUTURE 347 |
| **LEGACY object** (`by_date/day=/venue=`) | **2,826 rows** — OPTION 2,566 / COMBO 228 / FUTURE 32      |

The canonical object matches the ORIGINAL manifest count (74,005) **exactly**; the legacy object matches what the
migration WROTE (2,826) **exactly**. That is conclusive: the migration read the legacy object.

## Why it matters

- The tradfi availability manifest now **understates real coverage by 425,096 instruments**. Anything reading
  `instrument_count`/`row_count` for tradfi coverage (data-status page, honest-coverage denominators, gates) is being
  told less data exists than actually does.
- It is a **false-negative**, which is the quieter and more dangerous direction: nobody gets paged for coverage that
  looks lower than it is, and the manifest's own DRIFT log already "explained" it.
- The parent plan's P9 Q2 entry currently records the wrong root cause, so the next agent would inherit the wrong mental
  model.

## Fix

1. **Repair = re-run the same backfill with canonical-path-first**, NOT a rollback (a rollback would restore the blank
   `instrument_type` the migration correctly fixed). The sibling script
   `scripts/canonicalize_cefi_defi_instrument_type_2026_07_17.py` already implements the correct rule — it reads the
   CANONICAL path first and falls back to legacy ONLY when the canonical object does not exist (measured on defi:
   canonical existed for 67/120 sampled targets, legacy for 99/120, and the two AGREE where both exist, 127/143 — so the
   fallback is genuinely needed, but must never win over an existing canonical object). Generalise that script to tradfi
   (it is already `--asset-group`-parameterised) and re-run.
2. **Verify** by re-reading live and confirming Σ `instrument_count` returns to ~47,149,715 and CME 2026-06-28 reads
   74,005 across OPTION/COMBO/FUTURE.
3. **Correct the record**: the parent plan's P9 Q2 checkbox + the tradfi script's docstring both assert the
   "pre-existing staleness" explanation. Both must be corrected or the next reader re-inherits it.
4. **Blast-radius check (not yet done)**: are there OTHER migrations that resolve a by_date object path? Any that
   hardcode the legacy layout have the same latent bug. `canonicalize_cefi_split_venue_chain_2026_07_17.py` (shipped
   today) only _checks existence_ at the canonical path and never re-stamps counts from an object, so it is unaffected;
   `drain_residual_lending_rows_2026_07_17.py` reads no objects at all. Others are unaudited.

## Rollback / safety

- Pre-migration snapshot (tradfi):
  `gs://instruments-store-tradfi-prd-central-element-323112/_index/snapshots/pre_tradfi_instrument_type_canon_2026_07_16_20260716T143452Z.parquet`
- The blank rows the migration fixed are genuinely fixed (0 captured rows remain blank in tradfi) — only the COUNTS on
  the re-stamped shards are wrong. So the repair is a re-derive, not a restore.
