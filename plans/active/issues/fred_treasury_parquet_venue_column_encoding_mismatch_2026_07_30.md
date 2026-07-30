---
doc_type: issue
title: MTDS-written FRED treasury (yield_curve) parquets crash on read — row-group `venue` column encoding mismatch
summary:
  Discovered while wiring `yield_curve`/`economic_results` into features-service's `CALENDAR_FEATURE_GROUPS`
  (defi_venue_pipeline_to_live_ao_build's parent issue doc, todo "Convert this doc's own Recommended decision Phase 1
  ... into a real tracked todo"). Every sampled MTDS-captured FRED treasury (DGS2/DGS5/DGS10/DGS30) daily parquet
  crashes `pd.read_parquet` with a pyarrow schema-merge error — the `venue` column is encoded inconsistently
  (dictionary-encoded in some row-groups, plain string in others) within the SAME single-day file. This makes every
  currently-captured yield_curve source row unreadable, blocking `_generate_yield_curve`'s done-when (non-empty output
  for a recent date) — root cause is write-side (MTDS's FredAdapter), out of this task's scope.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, features-service]
scope: [engineer]
tags: [data-correctness, fred, parquet, pyarrow, tradfi, yield-curve, cross-repo]
related:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/active/issues/fred_backfill_early_date_indefinite_stall_2026_07_30.md,
  ]
created: 2026-07-30
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
source: >-
  Discovered live while implementing plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md's line-492
  todo (wiring yield_curve into features-service CALENDAR_FEATURE_GROUPS) — a real read of MTDS-captured FRED DGS10
  January 2024 data crashed with a pyarrow ArrowTypeError, confirmed reproducible across every sampled day in that month
  and across all 4 treasury series (DGS2/DGS5/DGS10/DGS30).
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# MTDS-written FRED treasury parquets crash on read — row-group `venue` column encoding mismatch

## What I found

Every MTDS-captured FRED treasury (yield_curve) daily parquet sampled for January 2024 fails to read via
`pd.read_parquet` (pyarrow engine) with:

```
pyarrow.lib.ArrowTypeError: Unable to merge: Field venue has incompatible types: string vs dictionary<values=string, indices=int32, ordered=0>
```

Reproduced live (2026-07-30) via
`features_service.calendar.adapters.mtds_fred_reader.read_fred_observations("DGS10", start_date=date(2024,1,1), end_date=date(2024,1,31))`
against the real prod bucket (`central-element-323112` project) — every day in the range that has a captured file
(2024-01-01, -02, -03, -04, -16, -17, -18, -19, -22, -23, ...) hits the same error. Confirmed via direct
`pd.read_parquet` on the exact
`gs://.../raw_tick_data/by_date/day=2024-01-XX/pipeline_mode=batch_fred/asset_group=tradfi/venue=FRED/instrument_type=bond/data_type=yield_curve/FRED:BOND:DGS10-USD.parquet`
object path — this is ONE file per day (not a multi-file merge across days), so the schema conflict is BETWEEN
ROW-GROUPS WITHIN a single file: some row-groups were written with the `venue` column dictionary-encoded, others with it
as a plain string, and pyarrow's cross-row-group schema unification (which `pd.read_parquet`'s default `ParquetDataset`
path performs even for a single file) refuses to reconcile the two physical encodings.

This means the file was almost certainly written incrementally across multiple separate write calls (e.g. a retry, a
re-run, or an append) that used inconsistent pyarrow write settings for that column — a genuine write-side defect in
whatever wrote `FRED:BOND:DGS10-USD.parquet` (MTDS's `FredAdapter.write_canonical_shard` /
`tradfi_shared.write_tradfi_shard`, per `mtds_fred_reader.py`'s own module docstring on the canonical wire format), not
a read-side bug.

`ArrowTypeError` subclasses `TypeError`, not `ValueError`, so it silently escaped `mtds_fred_reader.py`'s existing
`_read_day_parquet` try/except (`(ConnectionError, TimeoutError, OSError, ValueError)`) and crashed the caller instead
of degrading to "unreadable, skip" like every other read failure that function already handles gracefully.

## Why it matters

- **Immediate impact**: `YieldCurveCalculator` / `features-service`'s new `_generate_yield_curve` (wired 2026-07-30,
  `features-service@4eb5d628`) cannot produce a non-empty `yield_curve` row for ANY date whose treasury data was
  actually captured, because reading that data crashes (now degrades to empty instead, see Mitigation below) — this
  blocks that todo's own done-when criterion (a `--operation compute` run showing non-empty `yield_curve` output for a
  recent date).
- **Broader impact**: this is likely NOT limited to `DGS10` — the same write path serves `DGS2`/`DGS5`/`DGS30`
  (yield_curve) and the economic_results series (`PAYEMS`/`CPIAUCSL`/`GDP`/`ICSA`/`FEDFUNDS`/`PCEPI`, `ohlcv_1d` shards)
  via the identical `tradfi_shared.write_tradfi_shard` code path. `economic_results` didn't visibly hit this in my
  testing only because its actual read pattern (NFP/CPI/GDP/CLAIMS/PCE monthly-trigger, narrow single-day lookback
  windows) apparently didn't land on an affected file during my sampling — it may still be affected for other dates.
- **Data-correctness**: every currently-captured historical FRED treasury row is silently unusable to any downstream
  reader going through the standard `pd.read_parquet` path (not just this new calendar wiring) until the underlying
  files are rewritten with consistent encoding.

## Mitigation shipped (read-side only, does not fix the root cause)

`features-service@4eb5d628` — `mtds_fred_reader.py::_read_day_parquet` now also catches `pyarrow.ArrowException` (covers
`ArrowTypeError`) alongside the existing error types, logging + skipping the unreadable file instead of crashing the
caller (matches the function's own documented "return an empty DataFrame if MTDS hasn't captured it yet" contract /
shard-level failure isolation). This prevents a crash but does NOT recover the data — affected days still read as empty.

## Recommended decision

1. **Root-cause the write-side encoding inconsistency** in MTDS's FRED writer (`market-tick-data-service`
   `market_tick_data_service/market_interface/adapters/tradfi/fred_adapter.py` → `tradfi_shared.write_tradfi_shard`) —
   likely a retry/re-run path that appends to an existing day's parquet using a different pyarrow write call/version
   than the original write, producing inconsistent row-group encoding for the `venue` column specifically (a constant
   string value across every row — an obvious dictionary-encoding candidate, which is exactly why some writers
   auto-dictionary-encode it and others don't).
2. **Fix the writer to always use ONE consistent encoding** (e.g. explicitly disable dictionary encoding for `venue`, or
   always enable it, via `pyarrow.parquet.write_table(..., use_dictionary=[...])` / equivalent pandas
   `to_parquet(engine="pyarrow", ...)` kwarg) so future writes don't reintroduce the mismatch.
3. **Rewrite/consolidate the already-affected historical files** (read each row-group separately via
   `pyarrow.parquet.ParquetFile(path).read_row_group(i)` — bypassing the dataset-level schema unification — concat,
   re-write with the fixed consistent encoding) so the existing captured FRED treasury history becomes readable again.
   Scope this against the FULL treasury history once the writer fix lands, not just January 2024.
4. Re-run `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md`'s line-492 todo's done-when check for
   `yield_curve` specifically once (2) + (3) land — the wiring itself (`features-service@4eb5d628`) is already correct
   and needs no further change.

## Todos

- [ ] [DATA] P1. Root-cause the `venue`-column row-group encoding inconsistency in MTDS's FRED writer
      (`market_tick_data_service/market_interface/adapters/tradfi/fred_adapter.py` /
      `market_tick_data_service/market_interface/adapters/tradfi/tradfi_shared.py`'s `write_tradfi_shard` /
      `write_canonical_shard`) — confirm which write path(s) produce dictionary-encoded vs plain-string `venue` columns
      for the same day (likely a retry/append path using different pyarrow write settings than the original write).
      Repo: market-tick-data-service. Done when: root cause identified with file:line evidence.
- [ ] [DATA] P1. Fix the writer to use ONE consistent `venue` column encoding on every write (retry/append included),
      confirmed via a targeted test that writes the same day twice through both code paths and asserts the resulting
      file reads cleanly via `pd.read_parquet`. Repo: market-tick-data-service.
- [ ] [DATA] P2. Rewrite/consolidate every already-affected historical FRED treasury parquet (yield_curve +
      economic_results series) with the fixed consistent encoding, reading each row-group independently
      (`pyarrow.parquet.ParquetFile(path).read_row_group(i)`) to recover the pre-existing data rather than discarding
      it. Scope: full treasury history, not just January 2024 (this doc only sampled one month). Repo:
      market-tick-data-service or a features-service/scripts one-off migration script (whichever owns the canonical
      write). Done when: `read_fred_observations` returns real observations (no skip-warnings) for a broad historical
      sample across DGS2/DGS5/DGS10/DGS30 and the NFP/CPI/GDP/CLAIMS/PCE/FOMC series.
- [ ] [VERIFY] P2. Re-run `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md`'s line-492 todo's own
      done-when for `yield_curve` specifically (`--operation compute --mode batch` for a recent/historical date shows
      non-empty `yield_curve` output) once the above land — the wiring code (`features-service@4eb5d628`,
      `CalendarOrchestrationService._generate_yield_curve`) needs no further change, only real readable upstream data.
      Repo: features-service (verification only).
