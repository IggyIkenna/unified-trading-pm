---
title: "MDPS Sports manifest MalformedRowKeyError + streaming read schema gaps"
created: 2026-05-22
author: slot-7
source:
  - plans/active/mdps_backfill_phase3_2026_05_22.md (MDPS-3.3.Sports-V)
locked_by: live-defi-rollout
---

## What I found

All 7 MDPS sports reprocessor VMs (`mdps-sports-{2020..2026}-20260522-161432`) exited with status 0 but produced **zero
new processed output** and **zero manifest entries**. Root causes:

### Root cause A — MalformedRowKeyError on manifest writes (blocking)

Every `empty_confirmed` manifest write attempt fails with:

```
MDPS canonical_writer: empty_confirmed manifest write failed for ticks_migrated_20260505T152043Z
day=2020-06-06 tf=15m: MalformedRowKeyError: shard-atom field 'chain' was explicitly passed as empty.
Fix: either remove 'chain' from row_key (non-per-chain shard) or populate it before calling record_captured.
row_key={'date': '2020-06-06', 'venue': 'ODDS_API', 'chain': '', 'instrument_type': '', ...}
```

The MDPS sports canonical_writer includes `chain` in the row_key but never sets a non-empty value (sports is not
chain-specific). Same pattern as MDPS-3.3.TradFi-SchemaContract and MDPS-3.3.Pred-SchemaContract.

Fix: remove `chain` from the sports canonical_writer row_key (or populate as `chain='sports'` if the shard-atom schema
requires it). UAC `hard_schema_enforcement Phase 4` rejects empty string for declared shard-atom fields.

### Root cause B — streaming read "no group column" on early raw tick data

```
Streaming read: no group column in raw_tick_data/by_date/day=2020-06-06/.../ticks.parquet
(candidates=('instrument_key', 'symbol'), schema=[...no symbol/instrument_key col...])
```

The 2020-era raw tick data parquets lack the `symbol` or `instrument_key` column that MDPS's streaming reader uses to
group aggregations. These files were written under a pre-canonical schema. MDPS skips or produces empty output for these
dates. Not all dates are affected — later dates (post-2022) have the column.

### Manifest state impact

- Existing availability_index.parquet (sports): 172,847 rows; schema_version dist: v6=140,212, v4=17,288, v8=15,347.
  Only 8.9% v8 (15,347 rows from 20260519 runs). MDPS-3.3.Sports-V requires "manifest 100% v8" — BLOCKED until
  migration.
- 20260522 VMs wrote 0 new manifest entries (all writes failed with MalformedRowKeyError).

### Processed bar output

Existing `processed/by_date/` blobs from 20260519 VMs are intact and valid:

- Sample (2024-01-01): 245 rows/day, home/draw/away odds 0 NaN, btts NaN expected, no `data_available_at` ✅
- Data from 20260522 VMs: 0 new blobs written

## Why it matters

**MDPS-3.3.Sports-V cannot be flipped GREEN** until:

1. chain=empty MalformedRowKeyError is fixed in MDPS sports canonical_writer
2. Manifest is re-migrated to v8 across all 172,847 rows
3. VMs are re-relaunched after fix to produce complete manifest coverage

This blocks `features_backfill_phase3` sports phase (gated on MDPS-3.3.Sports-V GREEN).

## Recommended decision

**Option A (recommended)**: Fix MDPS sports canonical_writer to remove `chain` from row_key (same fix as TradFi/Pred).
Add test. Relaunch 7 sports VMs after fix. Separately: schedule manifest v8 migration sweep for the existing 172,847
rows via Cloud Run migration job (Phase 2.2 pattern — single walk).

**Option B**: Accept 8.9% v8 existing manifest as-is, skip MDPS-3.3.Sports-V manifest check, gate only on bar output
quality. Risk: downstream consumers expecting v8 manifest will get v6 rows.

**Next steps (after operator ack)**:

1. Fix MDPS canonical_writer sports row_key
2. Migrate availability_index.parquet 172k rows to v8 (migration script)
3. Relaunch `mdps-sports-{2020..2026}-20260522-NNNNNN` VMs
4. Re-run MDPS-3.3.Sports-V verify

Successor plan item: `mdps_backfill_phase3_2026_05_22.md` § Phase 4 MDPS-3.3.Sports-SchemaContract.
