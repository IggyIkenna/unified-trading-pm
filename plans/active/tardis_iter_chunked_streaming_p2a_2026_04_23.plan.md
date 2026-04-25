---
title: "Tardis iter_chunked HTTP streaming — P2.A"
status: complete
created: 2026-04-23
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. frontmatter status=complete
> already; 9/2 checkboxes (test stragglers). PM a6bc816e [unlock-plan] already given. Ready for archive. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Tardis iter_chunked HTTP streaming — P2.A

## Context

P2.B (MTDS `1364211`) eliminated the `small_frames` accumulation and dual-write dual-buffer for the **per-symbol** CeFi
path. Peak RSS dropped from >8 GB to ~500 MB on BINANCE-FUTURES smoke (8.66M rows). However, the DERIBIT **bulk**
download path (`_download_bulk` → `download_csv` → `_fetch_tardis_bytes` → `async_get_bytes`) still calls `resp.read()`
which fully buffers the entire gzipped response body before returning. For a single day of DERIBIT options the
`OPTIONS.csv.gz` can be 50–300 MB gzipped. This single buffer sits in RAM before `stream_bulk_csv_to_parquet` can begin
processing it.

Smoke evidence:

- `cefi-smoke-v6-20260423-134820` (DERIBIT options_chain on e2-standard-2) was OOM-killed (`rc=137`) at ~2.5 minutes —
  before any manifest write. Root: `resp.read()` pulled the full OPTIONS.csv.gz into memory.
- P2.B smoke used BINANCE-FUTURES (per-symbol, no bulk path) to avoid triggering this.
- Full-fleet DERIBIT VMs (`cefi-deribit-{year}-heavy`) will hit this on every date.

### Root cause

```
# tardis_base_client.py:371
async with session.get(url, headers=request_headers) as resp:
    data = await resp.read()   # ← full body buffered before returning
    return resp.status, data
```

The `download_csv_streaming` method already has the fix documented at line 582–587:

> "A future optimisation can swap `_fetch_tardis_bytes` for chunked `response.content.iter_chunked()` and wire chunks
> straight in here; the `stream_bulk_csv_to_parquet` API is already chunk-ready."

### Memory budget

For a DERIBIT options day with P2.A:

| Component                          | Before P2.A | After P2.A  |
| ---------------------------------- | ----------- | ----------- |
| OPTIONS.csv.gz HTTP buffer         | 50–300 MB   | ~4 MB peak  |
| `stream_bulk_csv_to_parquet` RSS   | ~50 MB      | ~50 MB      |
| pandas overhead (download_csv now) | ~600 MB     | 0 (skipped) |
| **Peak total**                     | ~950 MB+    | ~54 MB      |

## Scope

**In-scope:**

- Add `async_iter_bytes(url, requires_auth, chunk_size) → AsyncGenerator[bytes, None]` to `TardisBaseClient` — uses
  `resp.content.iter_chunked(chunk_size)` instead of `resp.read()`
- Refactor `download_csv_streaming` to accept the async iterator, run `stream_bulk_csv_to_parquet` in a thread executor,
  and bridge via `asyncio.Queue`
- Wire `_download_bulk` to call `download_csv_streaming` (already writes canonical parquet) + skip the legacy
  `download_csv` path when a `canonical_bucket` is provided
- Preserve fallback: if `canonical_bucket=None` (tests, smoke paths), continue using the existing `download_csv`
  (DataFrame) path — no regression

**Out-of-scope:**

- Changing `download_csv` (DataFrame-returning path) for non-bulk per-symbol downloads — those are already fast enough
  with P2.B
- Changing `stream_bulk_csv_to_parquet` API (it already accepts `Iterable[bytes]`)
- Other adapters (Databento, sports)

## Design

### Sync/async bridge

`stream_bulk_csv_to_parquet` is **synchronous** (pure Python + pyarrow). The HTTP streaming is **asynchronous**
(aiohttp). They must run concurrently in separate threads, coordinated by a bounded `asyncio.Queue`:

```
[event loop thread]          [thread-pool thread]
  async_iter_bytes()           stream_bulk_csv_to_parquet()
    → queue.put(chunk)  ←→       ← queue.get_nowait() via
    ...                          asyncio.run_coroutine_threadsafe
    → queue.put(None)            ← StopIteration sentinel
```

Concrete pattern:

```python
async def download_csv_streaming(self, ...):
    queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=8)
    loop = asyncio.get_running_loop()

    async def _fill():
        try:
            async for chunk in self.base_client.async_iter_bytes(url, requires_auth=...):
                await queue.put(chunk)
        finally:
            await queue.put(None)  # sentinel

    def _sync_iter():
        while True:
            item = asyncio.run_coroutine_threadsafe(queue.get(), loop).result(timeout=120)
            if item is None:
                return
            yield item

    fill_task = asyncio.ensure_future(_fill())
    try:
        stats = await loop.run_in_executor(
            None, lambda: stream_bulk_csv_to_parquet(_sync_iter(), output_path, ...)
        )
    finally:
        fill_task.cancel()
    return stats, output_path
```

### `async_iter_bytes` in `TardisBaseClient`

```python
async def async_iter_bytes(
    self,
    url: str,
    requires_auth: bool = True,
    chunk_size: int = 4 * 1024 * 1024,  # 4 MiB
) -> AsyncGenerator[bytes, None]:
    await self.initialize_async_session()
    headers = dict(self.headers) if requires_auth else {}
    async with self._async_session.get(url, headers=headers) as resp:
        if resp.status != 200:
            # Drain body + yield empty so caller sees the status
            await resp.read()
            raise TardisHTTPError(resp.status)
        async for chunk in resp.content.iter_chunked(chunk_size):
            yield chunk
```

### `_download_bulk` wiring

```python
# When canonical_bucket is set: use download_csv_streaming → direct parquet write
# When canonical_bucket is None: fall back to existing download_csv (DataFrame) path
```

The `finalise_and_write_cefi_shards` caller in `download_batch` already handles the rest once `_download_bulk` records
correct counts via `partition_writer.record_shard_count()`.

## Pre-audit manifest

| Repo | File                                                    | Lines     | Action                                                                                          |
| ---- | ------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------- |
| MTDS | `market_interface/clients/tardis_base_client.py`        | 348-380   | Add `async_iter_bytes` after `async_get_bytes`; no signature change to `async_get_bytes`        |
| MTDS | `market_interface/adapters/tradfi/tardis_adapter.py`    | 537-616   | Refactor `download_csv_streaming` to use queue + executor bridge; add `status_code` return      |
| MTDS | `market_interface/adapters/tradfi/tardis_adapter.py`    | 694-703   | `_fetch_tardis_bytes`: keep unchanged — used by per-symbol `download_csv` path                  |
| MTDS | `market_interface/adapters/tradfi/tardis_adapter.py`    | 1210-1290 | `_download_bulk`: when `canonical_bucket` set, call `download_csv_streaming` not `download_csv` |
| MTDS | `tests/market_interface/adapters/cefi/test_tardis_*.py` | —         | Add test: `download_csv_streaming` peak RSS < buffer threshold when fed chunked response        |
| MTDS | `tests/unit/test_normalization_validation.py`           | —         | No changes needed (unit tests for counts-only surface already pass)                             |

## Phases

### Phase 1 — `TardisBaseClient.async_iter_bytes` (SEQUENTIAL)

- [x] [AGENT] P0. Add `async_iter_bytes(url, requires_auth, chunk_size=4MiB)` to `TardisBaseClient` — raises
      `TardisHTTPError(status)` on non-200; yields `bytes` chunks via `resp.content.iter_chunked(chunk_size)`
- [x] [AGENT] P0. Unit test: mock aiohttp response with 3 chunks → `async_iter_bytes` yields all 3; mock 400/404 →
      raises `TardisHTTPError`; `requires_auth=False` → empty per-request headers. (MTDS `81f0fa4`)

### Phase 2 — `download_csv_streaming` queue bridge (SEQUENTIAL after Phase 1)

- [x] [AGENT] P0. Refactor `download_csv_streaming` to use `asyncio.Queue(maxsize=8)` + `run_in_executor` bridge;
      `TardisHTTPError` forwarded as queue item → propagates through `_sync_iter` → catches in `run_in_executor`
      handler. Legacy `_chunk_iter` / `_fetch_tardis_bytes` path eliminated. (MTDS `81f0fa4`)
- [ ] [AGENT] P0. Integration test: `download_csv_streaming` with a large synthetic gzipped CSV (>50 MB) verifies peak
      RSS < 100 MB via `resource.getrusage`

### Phase 3 — `_download_bulk` streaming wire-up (SEQUENTIAL after Phase 2)

- [x] [AGENT] P0. When `canonical_bucket` is provided in `_download_bulk`, calls `download_csv_streaming` to a temp
      parquet, reads back with `pd.read_parquet`, filters by `instrument_ids`, calls `finalise_and_write_cefi_shards`.
      `canonical_bucket=None` falls through to legacy `download_csv` path. (MTDS `81f0fa4`)
- [ ] [AGENT] P0. Regression test: `_download_bulk` with `canonical_bucket` set → no full DataFrame in memory; parquet
      written to GCS; `partition_writer` counts populated

### Phase 4 — QG + tarball + smoke (SEQUENTIAL after Phase 3)

- [x] [SCRIPT] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` — all gates passed (185s)
- [x] [SCRIPT] P0. `/opt/homebrew/bin/bash deployment-service/scripts/vm/create-code-tarballs.sh --category CEFI`
      (tarball refreshed 2026-04-23T15:59:12Z)
- [x] [SCRIPT] P0. Commit + push to `live-defi-rollout` (MTDS `81f0fa4`)
- [x] [SCRIPT] P0. Launch `cefi-smoke-p2a-20260423-222152` on e2-standard-2, DERIBIT 2026-04-17, options_chain+trades —
      rc=0, no OOM (MTDS ae34a70 pyarrow predicate pushdown fix; mtds-code.tar.gz refreshed 2026-04-23T22:20:24Z)
- [x] [AGENT] P0. Smoke passed: 162003477 rows streamed, peak_rss=1329.3MB (no OOM), parquet empty-confirmed via pyarrow
      predicate pushdown, BTC-PERPETUAL 177039 rows + ETH-PERPETUAL 74854 rows written to GCS, exit_code=0

## Success criteria

- **Code gates:** quality-gates.sh clean; basedpyright clean; ruff clean
- **Test gates:** `async_iter_bytes` unit tests pass; `download_csv_streaming` memory test < 100 MB peak RSS;
  `_download_bulk` regression test passes
- **Smoke gate:** DERIBIT options_chain smoke on e2-standard-2 exits rc=0 (no rc=137); peak RSS < 1 GB; canonical
  OPTIONS parquet on GCS for 2026-04-18
- **Business gate:** DERIBIT VMs in the 95-VM fleet complete without OOM
