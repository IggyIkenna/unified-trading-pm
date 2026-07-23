---
doc_type: issue
title:
  Tardis canonical shards whose GCS upload fails (writer.close() 429 burst) were SILENTLY dropped — no manifest row at
  all, reported as clean success. Exposed and AMPLIFIED by the CeFi throughput rebuild.
summary:
  On the 32-way-concurrent finalise path, a shard whose writer.close() (parquet finalize + GCS multipart upload) raised
  after the SDK's own _GCS_RETRY was swallowed in StreamingShardFinalizer._close_writers_and_collect with
  `logger.exception(...); continue`. The shard vanished from FinalizeResult entirely, so download_symbol returned 0 rows
  as an int (looks like success) and _emit_per_symbol_manifest wrote NO manifest row for it — not captured, not
  empty_confirmed, not attempted_failed. A real, fetched instrument (rows already read from Tardis) became a silent hole
  a coverage gate cannot see. Measured 2026-07-17 on cefi-queue-heavy-binancefutu-x17-20260717-211655 — 27 large
  DERIBIT-perpetual book_snapshot_5 shards (ETH-USD@INV, ETH-USDC@LIN, BTC-USD@INV ...) lost to a startup GCS 429
  thundering-herd (195x 429 + 28x 503 total) while the run reported clean success at a healthy 13.8 MB/s. The throughput
  rebuild made this WORSE — higher write rate -> more concurrent multipart uploads -> more 429s -> more silent drops.
status: resolved
resolved_by:
  - unified-trading-library@f78d6362 (StreamingShardFinalizer.FinalizeResult.failed_paths — records a failed shard
    instead of silently dropping it; non-breaking, the only production caller is the Tardis path)
  - market-tick-data-service@3e48262b (finalise_and_write_cefi_shards_streaming raises TardisShardUploadError on a
    non-empty failed_paths BEFORE any partition_writer bookkeeping -> per-symbol shard isolation records it
    record_failed = attempted_failed = retryable next pass; the fixed shard path makes the re-upload an idempotent
    overwrite)
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, tardis, data-correctness, silent-data-loss, gcs, 429, honest-coverage, big-finding, backfill]
related:
  [
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
  ]
created: 2026-07-17
source:
  - Fell out of VM-verifying the GCS HTTP-pool fix (unified-trading-library@4a30bd27) for the CeFi throughput rebuild —
    the pool fix eliminated the "Connection pool is full" decay, but the run log still showed 27 `writer.close() failed
    ... shard skipped` ERROR lines with zero manifest consequence.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
parent_epic: cefi_master
execution_scope: local-only
drift_direction: advance-code
last_updated: 2026-07-17
depends_on: []
locked_by:
locked_since:
---

# Tardis silent shard-upload drop on a GCS 429 burst (data-correctness)

> **🟢 RESOLVED 2026-07-17** — the silent drop is fixed (failed shards are now recorded `attempted_failed` = retryable).
> One P2 efficiency follow-up remains (reduce the startup 429 burst so pass-1 lands the big shards). Notifying the
> operator per the data-correctness big-finding HARD RULE.

## What happened (root-cause chain)

1. The CeFi throughput rebuild took download `0.45 -> ~14 MB/s` (~30x). At that rate the 32-wide finalise pool uploads
   20-33 MB DERIBIT-perpetual `book_snapshot_5` parquets to GCS concurrently at startup — a thundering herd that trips
   GCS per-prefix write-QPS. Run log: **195x HTTP 429 + 28x HTTP 503**.
2. `providers/gcp.py::upload_file` already passes `retry=_GCS_RETRY` (429/503, `deadline=600s`), but on the
   **multipart** (`_do_multipart_upload`) path the media library gives up on `TooManyRequests` ~2 min in — the 600s
   deadline is not honored for multipart. All 27 escaping exceptions were `google.api_core.exceptions.TooManyRequests`.
3. `StreamingShardFinalizer._close_writers_and_collect` caught the escaping exception with
   `logger.exception("...shard skipped"); continue`. The shard was dropped from `written_paths`, `per_shard_metadata`,
   AND `total_rows`.
4. `download_symbol` therefore returned `_shard_rows = 0` as an **int** (not an exception). In
   `_emit_per_symbol_manifest` an `int` result writes **no manifest row at all** (only exception results route to
   `record_zero_rows`/`record_failed`). So the instrument had no capture_status row — indistinguishable from
   never-attempted, and invisible to the run's success report.

Net: 27 real, fetched instruments per run silently vanished, and the faster the pipeline runs the more vanish.

## Why it is P1 (not P0)

The dropped shard was NOT recorded `empty_confirmed`, so it is not permanently masked as honest-absence — a future
"re-attempt everything uncaptured" pass would re-download it. But it was also NOT recorded `attempted_failed` (the
honest retryable state the coverage gate acts on), and the run reported clean success, so nothing surfaced the loss.
Silent + throughput-amplified = P1 data-correctness.

## Fix (shipped)

- **unified-trading-library** — `FinalizeResult.failed_paths: list[str]`; `_close_writers_and_collect` appends the path
  instead of silently dropping it. Non-breaking: the generic finalizer still does not raise, and the Tardis path is its
  only production caller (`replay.py::finalize` is the unrelated replay publisher).
- **market-tick-data-service** — `finalise_and_write_cefi_shards_streaming` raises `TardisShardUploadError`
  (`GCS_UPLOAD_FAILED: ...`) on a non-empty `failed_paths`, BEFORE any `partition_writer` bookkeeping. The existing
  per-symbol shard isolation in `download_batch` catches it -> `_classify_tardis_error` -> `record_failed`
  (`attempted_failed`, retryable). A failed symbol does zero partial bookkeeping; the re-upload overwrites idempotently.
- Regression tests: `test_streaming_finalizer_failed_paths.py` (UTL), `test_tardis_finalise_raises_on_upload_failure.py`
  (MTDS) — both assert the failed shard is recorded, never silently dropped, and that a clean result does not
  over-raise.

## P2 efficiency follow-up — RESOLVED 2026-07-17 (unified-trading-library@546bd99d)

The startup 429 thundering-herd is now absorbed by an OUTER retry over the whole GCS upload
(`streaming_writer._upload_gcs_with_retry` → `with_retry`), so the big DERIBIT-perpetual shards land on pass-1 instead
of a later retry pass. `with_retry` now honors google.api_core's `.code` attribute (`TooManyRequests.code == 429`) so
429/5xx are retried while **400/precondition is NEVER retried** (`BadRequest.code == 400` is not in
`_RETRYABLE_STATUS_CODES`) — this also satisfies Tardis Support's "avoid immediate retries on 400" guidance, applied to
our writes. The gcp.py 900-line cap that originally blocked this is avoided by placing the retry in the io layer
(475→496 L) rather than the provider. The related Tardis download-side 400 behaviour was verified already-compliant and
locked in by a regression guard (market-tick-data-service: `tests/unit/test_tardis_no_immediate_retry_on_400.py`).

### Original follow-up notes (kept for provenance)

**Reduce the startup 429 thundering-herd so pass-1 lands the big shards** (today the biggest, most valuable DERIBIT
book_snapshot_5 shards systematically fail on pass-1 and only land on a later retry pass — correct, but a real tax):

- Add an OUTER app-level retry around `upload_file`'s `upload_from_filename` (belt over the SDK's early multipart
  give-up):
  `with_retry(..., retryable_exceptions=(TooManyRequests, ServiceUnavailable, ConnectionError), max_attempts~6, base_delay~2s, jitter=True)`.
  **Blocked-by**: `providers/gcp.py` is at the 900-line file-size cap (no headroom) — this needs either a small condense
  in gcp.py or placing the retry in `io/streaming_writer.py::_upload_to_gcs` (extend
  `utils/retry.py::_is_retryable_exception` to honor google's `.code` attribute so io/ need not import gcp exception
  types).
- OR route StreamingParquetWriter uploads through the existing `cloud_interface/gcs_rate_limiter.py` (halves rate on a
  429 for 60s) so the 32 concurrent writers self-pace instead of stampeding.

## Evidence

- VM `cefi-queue-heavy-binancefutu-x17-20260717-211655`, authenticated 2026-02-02, 32-wide, cap-1. Run log
  `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`: 27x `writer.close() failed ... shard skipped`
  (all DERIBIT:PERPETUAL book_snapshot_5), 0x "Connection pool is full", steady-state 11.7-13.8 MB/s stable.
- Traceback:
  `blob._do_multipart_upload -> upload.transmit -> wait_and_retry -> raise google.api_core.exceptions.TooManyRequests`.
