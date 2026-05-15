---
title:
  "MDPS Option A migration to UTL lifecycle blocked by GCS-upload semantics gap — `close_candle_writer` finalizes
  locally + `shutil.move`s, but `write_candle_parquet` consumers all upload to GCS"
created: 2026-05-10
author: chain-agent-2026-05-10-evening
source:
  - plans/active/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md (Option A spec)
  - market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py:476-485
    (StreamingParquetWriter.close() → _upload_to_gcs)
  - unified-trading-library/unified_trading_library/streaming/candle_writer.py:355-366 (close_candle_writer →
    shutil.move LOCAL only)
  - unified-trading-library/unified_trading_library/io/streaming_writer.py:341-377
    (StreamingParquetWriter._upload_to_gcs)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: operator triage → next MDPS-dedicated tab in work-split
  cadence: one-shot — resume Option A migration once architectural decision lands (R1 vs R2)
  verifier:
    write_candle_parquet flows through UTL lifecycle internally on a real CeFi backfill VM (writegate Phase 5 baseline +
    plan Phase 4 end-to-end) AND uploads to GCS correctly
  last_executed: "NEVER"
---

# MDPS Option A blocked by GCS-upload semantics gap (extension to mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10)

> **Severity**: P1 — blocks Option A migration of `write_candle_parquet` to UTL lifecycle. Same downstream blast radius
> as the parent issue (live-pipeline Phase 4 + Phase 1.2B + Phase 2). NOT a data-correctness bug today; a clean-shape
> blocker for the lifecycle unification.
>
> **Blast radius**: market-data-processing-service `canonical_writer.py`, `candle_write_mixin.py`, `io/writer.py`,
> `live_workers.py`. Potentially extends to UTL `streaming/candle_writer.py` if R2 adopted (cross-service primitives
> extension).
>
> **Suggested owner**: MDPS-dedicated tab in next work-split. Architectural decision (R1 vs R2) is operator-judgment-
> level; can be punted to operator triage if neither resolution is clearly better.

## What I found (grep-then-read audit per CLAUDE.md HARD RULE)

### Step 1 — Read `canonical_writer.write_candle_parquet` end-to-end

Current shape (post-Phase 1.2A + 1.2A.1, simplified):

```python
def write_candle_parquet(*, candles_df, bucket, gcs_path, asset_group, source_data_type, timeframe, ...) -> int | None:
    if candles_df.empty: return None
    candles_df = _stamp_candle_available_at(...)
    contract = lookup_mdps_contract(...)
    partition_path = f"day=.../category=.../venue=.../instrument_type=.../data_type=..."
    writer = StreamingParquetWriter(bucket=bucket, gcs_path=gcs_path, schema_contract=contract, partition_path=...)
    writer.write_chunk(candles_df)
    bytes_written = writer.close()                  # ← writes parquet to tempfile, THEN uploads to GCS via _upload_to_gcs()
    manifest_writer = ManifestWriter(...)
    manifest_writer.record_captured(row_key=..., df=candles_df, ...)
    manifest_writer.write(); manifest_writer.flush()
    return bytes_written
```

**`StreamingParquetWriter.close()` (UTL `io/streaming_writer.py:315-339`)**:

```python
def close(self) -> int:
    self._closed = True
    self._release_local_resources()
    file_size = os.path.getsize(self._tmp.name)
    if self._row_count == 0:
        os.unlink(self._tmp.name); return 0
    self._upload_to_gcs(file_size)            # ← SYNC GCS UPLOAD
    return file_size
```

`_upload_to_gcs` (UTL `io/streaming_writer.py:341-377`) calls
`client.upload_file(self._bucket, self._gcs_path, self._tmp.name)` then unlinks the tempfile.

### Step 2 — Audit every `write_candle_parquet` callsite

```
$ grep -rn "write_candle_parquet\b" market-data-processing-service/ --include='*.py'
```

4 production callsites. ALL pass `bucket=` and `gcs_path=` and ALL expect upload to GCS:

1. **`candle_write_mixin.py:314`** (`_upload_candles_to_gcs`): used by `orchestration_writer._write_candles` →
   batch_workers + live_workers. Single fully-materialised df + GCS bucket + path.
2. **`io/writer.py:144`** (`write_candles`): polars df → pandas one-shot. Same shape.
3. **`live_workers.py:1170`** (via `_write_candles`): per-tf concat'd df after streaming accumulator. Same shape.
4. **`batch_workers.py`** (via `_write_candles`): batch path mirror of live_workers. Same shape.

Plus 2 test callsites in `tests/unit/test_canonical_writer_record_helpers.py` exercising the success + empty-df paths.

### Step 3 — Read UTL `close_candle_writer` (the proposed migration target)

```python
def close_candle_writer(handle, *, manifest_writer, error=None, attempted_at=None) -> None:
    ...
    if error is not None:
        handle.writer._release_local_resources()    # close pyarrow writer
        _attempt_unlink_temp(handle)                # delete tempfile
        manifest_writer.record_failed(row_key, error=str(error), ...)
        return
    if handle.total_rows == 0:
        handle.writer.finalize_local()              # closes pyarrow writer + unlinks tempfile, returns ""
        manifest_writer.record_empty(row_key, reason=SOURCE_RETURNED_ZERO, ...)
        return
    final_tmp = handle.writer.finalize_local()      # ← LOCAL tempfile, NO GCS UPLOAD
    df = _all_chunks_df_from_path(final_tmp)        # read parquet back for record_captured df validation
    manifest_writer.record_captured(row_key, df=df, attempted_at=..., **manifest_kwargs)
    os.makedirs(os.path.dirname(handle.parquet_path) or ".", exist_ok=True)
    shutil.move(final_tmp, handle.parquet_path)     # ← LOCAL FILE MOVE, NOT GCS UPLOAD
```

**Critical gap**: UTL `close_candle_writer` is local-only. It uses `finalize_local()` (which does NOT upload to GCS)
then `shutil.move(tmp_path, parquet_path)` to a local destination. There is NO path through UTL primitives that uploads
the finalized parquet to GCS as part of the close.

The `parquet_path` argument on `CandleWriterHandle` is documented as "Final on-disk destination path. Renamed atomically
on close" (UTL `candle_writer.py:75-83`) — explicitly local.

## Why Option A as spec'd doesn't compose cleanly

Option A's key design: **single UTL lifecycle for the parquet finalize + manifest emission**. But the existing MDPS
production callsites all upload to GCS via `StreamingParquetWriter.close()`'s integrated `_upload_to_gcs(...)` step.
Migrating internally to UTL `open + write_chunk + close` lifecycle drops the GCS upload — silent regression: parquets
finalize to local tempfiles + manifest records `captured`, but the bytes are NOT in the GCS bucket the manifest row
points at.

The dual-SSOT we're trying to ELIMINATE was the duplicated `record_captured` callsite. The dual-SSOT we'd CREATE is the
duplicated finalize-and-upload path: UTL handles `record_captured` on a finalized-LOCAL parquet, MDPS would still need
to upload that local parquet to GCS in a separate post-close step → MDPS still owns half the lifecycle.

## Recommended decision (R1 vs R2)

### R1 — MDPS-level wrapper (contained scope, ~3-4 hours)

`write_candle_parquet` becomes a thin one-shot wrapper that:

1. Calls UTL `open_candle_writer(...)` with `parquet_path=tmp_local_path` (a tempfile chosen by MDPS, not the GCS path).
2. Calls UTL `write_chunk(handle, candles_df)`.
3. Calls UTL `close_candle_writer(handle, manifest_writer=..., ...)` — which finalizes + records manifest + moves
   tempfile to `tmp_local_path`.
4. **Then MDPS-side**: explicit GCS upload of `tmp_local_path` to `(bucket, gcs_path)` using the same
   `get_storage_client().upload_file(...)` shape `_upload_to_gcs` uses today.
5. **Then MDPS-side**: unlink the local tempfile.

Pro: doesn't touch UTL's stable contract (UTL@`ac6e3244`). Contained to MDPS. Con: MDPS still owns part of the
close-lifecycle (the GCS upload). Phase 1.2B's `_streaming_write_per_tf` migration still needs the same MDPS-side upload
glue. Two-step close logic exists in MDPS even after migration. Mild violation of the "single lifecycle" intent.

**However**: this preserves the ELIMINATED dual-SSOT for the manifest verb (which is what Option A actually targeted)

- schema validation + cluster validation + atomic finalize. The GCS upload is OUTSIDE the parquet-finalize-and-manifest
  unit, which arguably is fine because GCS uploads are post-finalize side effects.

### R2 — Extend UTL `close_candle_writer` to support GCS upload (~1.5 days, touches stable UTL contract)

Add optional kwargs to `open_candle_writer` + `close_candle_writer`:

```python
def open_candle_writer(*, parquet_path: str | None = None, gcs_bucket: str | None = None,
                      gcs_path: str | None = None, ...) -> CandleWriterHandle: ...

def close_candle_writer(handle, *, manifest_writer, ...) -> int:
    """Returns bytes_written when uploaded to GCS; 0 on local-only path."""
    ...
    final_tmp = handle.writer.finalize_local()
    df = _all_chunks_df_from_path(final_tmp)
    manifest_writer.record_captured(...)
    if handle.gcs_bucket and handle.gcs_path:
        _upload_local_to_gcs(handle.gcs_bucket, handle.gcs_path, final_tmp)
        os.unlink(final_tmp)
        return file_size
    elif handle.parquet_path:
        os.makedirs(...)
        shutil.move(final_tmp, handle.parquet_path)
        return file_size
    else:
        os.unlink(final_tmp); raise ValueError("close_candle_writer requires either gcs_bucket+gcs_path OR parquet_path")
```

Pro: cleanest single-lifecycle shape. Future consumers (features-\* live aggregator, ML serving) get GCS-aware finalize
for free. Close path is genuinely centralized in UTL. Con: touches UTL's stable contract (UTL@`ac6e3244`). UTL needs new
tests for the GCS path. Cross-service migration. Tests need to mock `get_storage_client()` similar to MDPS.

### Recommendation

**Operator triage between R1 and R2.** Both are valid; the choice is engineering taste vs. cross-service value. If the
live-pipeline Phase 4 + features-\* live serving will both consume the lifecycle close path with GCS uploads, R2 pays
off across consumers. If MDPS is the only consumer, R1 is sufficient.

The chain-agent's bias: **R2** for the cleaner cross-service primitive. But R1 is the lower-risk path if UTL is
considered stable and we want to minimize cross-cutting changes during the May-23 cutover window.

## What I shipped this session

Nothing under code (intentionally — STOP condition). Audit findings live in:

- This issue doc.
- The 4-callsite audit table above (durable record beyond the chat scrollback).

`unified-trading-library@6ce59900` UTL streaming facade re-exports + `c06942ff` PM commit (deferring 1.2B + Phase 2)
remain the prior shipped state from the parent issue.

## Why I did NOT ship Option A internal migration today

Per the parent issue + this session's spawn prompt: **"If during Step 1-2 you find that the existing
`write_candle_parquet` callsites depend on internal one-shot behaviour that doesn't compose cleanly with the lifecycle
wrapper: STOP, file an extension issue doc, ship Step 1 only as foundation + defer Phase 1.2B + 2 to a re-scoped agent.
Don't ship a fake."**

The GCS-upload semantics gap is exactly this case. Shipping a refactor where `write_candle_parquet` calls UTL lifecycle
BUT also has a separate GCS-upload step is technically sound (R1) but partially violates Option A's "single lifecycle"
intent. Shipping R2 expands scope into UTL contract changes that warrant operator-direction.

## Cross-references

- [`mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md)
  — the parent issue this extends.
- [`mdps_phase_1_2_phase_2_deferral_2026_05_10.md`](mdps_phase_1_2_phase_2_deferral_2026_05_10.md) — original Phase
  1.2B + Phase 2 deferral.
- [`audit_2026_05_08_substantial_unfixed_items.md`](audit_2026_05_08_substantial_unfixed_items.md) Item #3 — the
  audit-level tracking of this work.
- [`mdps_streaming_and_backpressure_2026_05_07.md`](../mdps_streaming_and_backpressure_2026_05_07.md) Phase 1.2B + Phase
  2 — the plan-of-record.
- [`live_pipeline_mtds_mdps_features_2026_05_08.md`](../live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4 — the
  downstream consumer of the unified lifecycle.
- UTL@`ac6e3244` — the streaming-candle-writer primitives (the lifecycle this migration consumes).
- UTL@`6ce59900` — UTL streaming facade re-exports (this prior session's pre-requisite ship).
- MDPS@`afdb754` — Phase 1.2A manifest-verb migration (the foundation that Option A builds on).
- MDPS@`1cdcda7` — Phase 1.2A.1 `available_at` stamping (production blocker retired).

## Exit criteria (closing this extension issue)

- Operator triage decision logged (R1 / R2). — `[ ]` open
- If R1: `write_candle_parquet` refactored internally with the post-close GCS-upload step + tests for the
  `(open + write_chunk + close + upload + unlink)` lifecycle. Phase 1.2B `_streaming_write_per_tf` migrated using the
  same MDPS-side `open_candle_streaming_writer / close_candle_streaming_writer` helpers. — `[ ]` open
- If R2: UTL `open_candle_writer` + `close_candle_writer` extended with optional GCS-upload kwargs + tests. MDPS
  `write_candle_parquet` migrated to use the GCS-upload path. Phase 1.2B uses the same. — `[ ]` open
- Live-pipeline Phase 4 banner removable. — `[ ]` open
- Phase 1.2B + Phase 2 + Phase 4 ship under the chosen path. — `[ ]` open
