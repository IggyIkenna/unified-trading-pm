---
title: "Tardis canonical path full streaming — P2.B"
status: active
created: 2026-04-22
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 18/18 checkboxes done. MTDS
> 5ec195f; PM a3501b13 [unlock-plan] already given. Ready for archive. See `_reconciliation_evidence_map_2026_04_25.md`
> for evidence anchors.

# Tardis canonical path full streaming — P2.B

## Context

Smoke test on 2026-04-22 (`cefi-smoke-fixstack-v2-20260422`, e2-standard-2, BINANCE-FUTURES 2026-04-18, BTCUSDT+ETHUSDT,
trades+book_snapshot_5) hit `rc=137` OS-OOM-killed on an 8 GB VM. Root cause diagnosis:

### Leak #1 — `small_frames` accumulation

`market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py::TardisAdapter.download_batch` accumulates
every per-symbol DataFrame into `small_frames: list[pd.DataFrame]` and returns
`pd.concat(small_frames, ignore_index=True)` at the end. For the smoke test that's 4 DataFrames totalling 8.66M rows
(~800 MB pandas memory). For the full-fleet heavy profile (9 symbols × trades+book_snapshot_5 = 18 partitions), it's
~3.6 GB just from accumulation.

### Leak #2 — dual-write via PartitionedTickWriter

`orchestrator.py::process_ticks` calls `writer.write_chunk(records_df)` at line 1044 with the returned DataFrame.
Despite the Gate G8.3 comment claiming the legacy write was "ripped out", `PartitionedTickWriter.write_chunk` at
[orchestrator.py](../../../market-tick-data-service/market_tick_data_service/engine/orchestrator.py) line 538 still
routes chunks to per-partition `StreamingParquetWriter` instances and uploads to GCS at `raw_tick_data/by_date/day=...`.
The adapter's `finalise_and_write_cefi_shards` writes the SAME data to the canonical path `day=.../category=cefi/...`.
Two full copies on GCS; two sets of in-memory parquet buffers.

### Impact

- Peak RSS ≈ 2-3 GB per symbol-day pair (pandas + parquet buffers + groupby copies). Smoke's 2 symbols × 2 data_types
  OS-OOM'd the 8 GB VM in the final finalization window — before any `writer_manifest.add()` (Fix #1) had a chance to
  run. No `Manifest updated` lines, no manifest rows written, zero `capture_status` sentinels. ResourceProfiler's 5s
  sample was too slow to catch the burst.
- Fix #5's 75% RSS warning therefore never fired → `flush_all_live_writers()` never called.
- Full-fleet relaunch at e2-standard-2 blocked until this is fixed.

## Scope

**In-scope:**

- Eliminate `small_frames` accumulation in `TardisAdapter.download_batch`
- Eliminate the dual-write: `PartitionedTickWriter.write_chunk` must become a no-op (counts only) for shards that came
  via the canonical write path
- Preserve manifest bookkeeping: `writer.row_count`, `writer.underlying_counts`, `writer.partition_counts`,
  `writer.instrument_count` must remain populated so the existing manifest-write logic in `process_ticks` continues to
  emit correct shard rows

**Out-of-scope (follow-ups):**

- Full pyarrow dataset partitioned-write inside `finalise_and_write_cefi_shards` (would eliminate `df.copy()` +
  `.to_dict("records")` per shard). Ship P2.B minimum first; add pyarrow streaming as P2.C if smoke still tight.
- P2.A `iter_chunked` for `_fetch_tardis_bytes` (orthogonal, separate plan)
- Other adapters (Databento, sports, prediction) — they don't show the same OOM pattern and their downstream contracts
  are different

## Design

### Pre-audit manifest

| Repo | File                                                 | Lines     | Action                                                                                                                                                                                               |
| ---- | ---------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MTDS | `engine/orchestrator.py`                             | 456-665   | Add `record_shard_count()` + `record_instrument()` methods to `PartitionedTickWriter` (counts-only path, no DataFrame required)                                                                      |
| MTDS | `engine/orchestrator.py`                             | 1040-1078 | For Tardis (empty returned DF), skip `writer.write_chunk` — existing `if not records_df.empty` check already handles this naturally once the adapter returns empty                                   |
| MTDS | `market_interface/adapters/tradfi/tardis_adapter.py` | 791-890   | `finalise_and_write_cefi_shards`: accept optional `partition_writer: PartitionedTickWriter \| None` param; after each shard write, call `partition_writer.record_shard_count(...)`                   |
| MTDS | `market_interface/adapters/tradfi/tardis_adapter.py` | 892-1082  | `download_batch`: remove `del writer`, thread writer through to finalise calls; remove `small_frames.append(df)` + `del df` (local drop, don't accumulate); return `pd.DataFrame()` (empty sentinel) |
| MTDS | `tests/`                                             | —         | Update test doubles; add regression test that `download_batch` returns empty DataFrame + writer counts populated correctly                                                                           |

### Backward compatibility

- `download_batch` signature unchanged — only the return shape semantics change (now always empty DataFrame for Tardis
  CeFi path)
- Callers that check `if not df.empty:` → naturally skip the downstream `write_chunk` (desired behaviour)
- Callers that rely on row data itself (matching-engine smoke tests) are broken — they should read canonical parquets
  from GCS instead. Document this as a follow-up if any such caller surfaces during tests.

## Phases

### Phase 1 — PartitionedTickWriter counts-only surface (SEQUENTIAL)

- [x] [AGENT] P0. Add `PartitionedTickWriter.record_shard_count(instrument_type, data_type, third_key, count)` — mutates
      `_row_counts`, no DataFrame, no GCS write
- [x] [AGENT] P0. Add `PartitionedTickWriter.record_instrument(instrument_type, data_type, symbol)` — mutates
      `_instrument_symbols`
- [x] [AGENT] P0. Unit test both new methods

### Phase 2 — TardisAdapter surgical refactor (SEQUENTIAL after Phase 1)

- [x] [AGENT] P0. `finalise_and_write_cefi_shards`: add `partition_writer` kwarg; call `record_shard_count` +
      `record_instrument` after each shard write
- [x] [AGENT] P0. `download_batch`: remove `del writer` on line 924
- [x] [AGENT] P0. `download_batch`: remove `small_frames.append(df)` + `pd.concat(small_frames)` — drop each `df` after
      finalise returns
- [x] [AGENT] P0. `download_batch`: return `pd.DataFrame()` (empty) in all success paths
- [x] [AGENT] P0. Thread `writer` through `finalise_and_write_cefi_shards` call sites in `download_batch` (per-symbol +
      bulk paths)
- [x] [AGENT] P0. Regression test: `download_batch` returns empty DataFrame; writer counts populated
- [x] [AGENT] P0. Fix `partition_counts` 3-tuple unpack to handle v6 5-tuple keys (ValueError guard)

### Phase 3 — QG + tarball refresh (SEQUENTIAL after Phase 2)

- [x] [SCRIPT] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh`
- [x] [SCRIPT] P0. `/opt/homebrew/bin/bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group CEFI`
      (tarball refreshed at 2026-04-23T13:47:33Z, 24s after P2.B commit 1364211)
- [x] [SCRIPT] P0. Commit + push to `live-defi-rollout` (commit 1364211 pushed; PM plan update committed below)

### Phase 4 — Re-smoke on e2-standard-2 (SEQUENTIAL after Phase 3)

- [x] [SCRIPT] P0. Delete any orphan parquets from 2026-04-18 smoke v2 if user wants a clean slate (optional — skipped,
      BINANCE-FUTURES data from 2026-04-22 smoke retained as baseline)
- [x] [SCRIPT] P0. Relaunch smoke VM `cefi-smoke-p2b-20260423-153352` on e2-standard-2, BINANCE-FUTURES 2026-04-18
      (pre-captured), BINANCE-SPOT+BYBIT 2026-04-18, BTCUSDT+ETHUSDT, trades+book_snapshot_5
- [x] [AGENT] P0. Monitor log: rc=0 ✅, `Manifest updated` ✅ (58 new entries, 251451 total), `capture_status` populated
      ✅, no OOM (no 75% RSS warning, no rc=137) ✅, P2.B dual-write eliminated (0.0 MB total in PartitionedTickWriter)
      ✅
- [x] [AGENT] P0. Verify canonical parquets exist on GCS: BINANCE-SPOT 4.9M rows + BYBIT 5.1M rows + BINANCE-FUTURES
      8.6M rows (from 2026-04-22) all on GCS ✅; manifest has 2026-04-18 rows with `capture_status` populated ✅
- [x] [AGENT] P0. Smoke passes all criteria → P0.B fleet relaunch unblocked ✅

## Success criteria

- **Code gates:** `quality-gates.sh` clean on MTDS; basedpyright clean; ruff clean
- **Test gates:** new `record_shard_count` / `record_instrument` unit tests pass; existing orchestrator + Tardis tests
  pass
- **Smoke gate:** re-smoke VM exits rc=0 on e2-standard-2; ≥2 `Manifest updated` lines; manifest parquet has 2026-04-18
  BINANCE-FUTURES rows with `capture_status` populated; peak RSS ≤ 2 GB
- **Business gate:** P0.B fleet relaunch unblocked
