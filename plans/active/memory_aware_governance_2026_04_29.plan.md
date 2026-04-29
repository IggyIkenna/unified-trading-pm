---
title: "Memory-aware shard governance: aggregate semaphore + active MemoryWatchdog"
priority: P2
status: active
owner: agent
created: 2026-04-29
type: feature
epic: none
completion_gates:
  code: C3
  deployment: D2
  business: none
repo_gates:
  - repo: market-tick-data-service
    code: C2
    deployment: D0
  - repo: unified-trading-library
    code: C1
    deployment: D0
  - repo: unified-trading-pm
    code: C0
    business: B0
depends_on: []
isProject: false
---

## Context

Three logical memory limits exist today but **none of them prevent OOM**:

1. **`MemoryWatchdog` at 85% RSS threshold** (UTL `unified_trading_library/memory_watchdog.py`) — started in every
   service runtime. Logs warnings when RSS crosses threshold. **Does not** flush in-flight buffers, cancel current
   Tardis streams, or block new shards. Purely advisory.

2. **`_graph_semaphore=4`** (MTDS `engine/orchestrator.py`) — caps concurrent shards-in-flight at 4.
   **Concurrency-bounded**, not memory-aware. Four heavy shards × 20 GB DataFrame each = 80 GB peak; the semaphore can't
   see this.

3. **`shard_memory_profile.recommended_machine_type`** — proactive sizing at launch time. Static, can't react to a
   one-day spike (e.g. 2025-05-06 DERIBIT had 82M options rows / ~20 GB DF — 8x larger than the 7-14M earlier days the
   profile was calibrated against).

Reference incident (2026-04-29): the streaming canonical write (MTDS `3145615`) reduces per-shard peak from ~20 GB to
~30 MB. Per-shard governance is no longer the bottleneck — but the platform still has no **aggregate memory governor**,
so a future regression (or a new non-streaming code path) can blow past the ceiling without protection.

## What we want

Two cooperating governors:

### (A) Memory-aware `_graph_semaphore`

Today: `asyncio.Semaphore(N)` blocks acquires when N shards in flight. Replace with a `MemoryAwareSemaphore` that:

- Tracks an **estimated memory budget** per shard. Each shard provides a hint via
  `shard_memory_profile.estimated_peak_ram_gb([(venue, dt, itype)])`.
- On `acquire(estimate_gb)`: blocks until **aggregate live estimates + estimate_gb ≤ budget** AND concurrency limit not
  exceeded.
- Budget = `psutil.virtual_memory().total * SHARD_BUDGET_FRACTION` (default 0.6 — leaves 40% headroom for Python heap /
  OS / logging / pyarrow scratch).
- On `release(estimate_gb)`: subtracts and signals waiters.

This means:

- 4 light shards × 1 GB each = 4 GB → all 4 run concurrently.
- 2 heavy shards × 20 GB each = 40 GB → both run; 3rd blocks until one releases.
- 1 catastrophic shard × 100 GB → only 1 in flight at a time.

The estimate must be conservative (favor over-estimation; an under-estimate causes OOM).

### (B) Active `MemoryWatchdog` shedding

Today: at 85% RSS, log a warning. Replace with **graduated response**:

- **At 75%**: log warning, **disable new shard acquires** (set the semaphore's `paused=True`; existing shards drain).
- **At 85%**: emit a `MEMORY_PRESSURE` event, force-flush every open `StreamingParquetWriter` (the per-(underlying,
  quote, margin) writer cache), close transient pyarrow readers.
- **At 92%**: log critical, **cancel the heaviest in-flight Tardis stream** (the one with highest accumulated rows;
  leaves the others to finish), record the cancelled shard as `attempted_failed` in the manifest with
  `error_reason="MEMORY_PRESSURE_CANCEL"`.
- **At 96%**: emergency exit `os._exit(2)` — better to die clean than OOM-kill via SIGKILL (which prevents `atexit`
  flush of the manifest writer; see `vm-tarball-deployment.md` rc=137 docs).

The 92% cancel is the genuinely new behavior — today everything runs to either OOM or completion, no in-flight
cancellation. Cancellation needs a `CancellationToken` plumbed through `download_csv_streaming` /
`_stream_finalise_chain_bulk`.

## Pre-audit

| Repo / file                                                                                            | Action                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-library/unified_trading_library/memory_watchdog.py`                                   | Extend with graduated thresholds (75/85/92/96), shed callbacks (`on_pressure`, `on_critical`, `on_emergency`), per-threshold cooldown          |
| `market-tick-data-service/market_tick_data_service/engine/orchestrator.py`                             | Replace `_graph_semaphore = asyncio.Semaphore(4)` with `MemoryAwareSemaphore` from UTL; pass per-shard estimate at acquire-site                |
| `unified-trading-library/unified_trading_library/io/streaming_writer.py`                               | Add `flush()` API that finalises the local temp parquet without GCS upload (cooperative with watchdog's force-flush at 85%)                    |
| `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py` | Plumb `CancellationToken` through `download_csv_streaming` + `_stream_finalise_chain_bulk` so the 92% threshold can cancel the heaviest stream |
| `unified-api-contracts/unified_api_contracts/external/...`                                             | Add `VenueErrorCode.MEMORY_PRESSURE_CANCEL` for manifest `attempted_failed` rows                                                               |

## Phased execution DAG

```
Phase 1 — MemoryAwareSemaphore (P0, ~half day)
   1.1 New class in UTL: track aggregate budget, per-acquire estimate
   1.2 Integration test: 4 acquires of 1 GB on a 4 GB budget all run;
       3rd acquire of 20 GB on a 40 GB budget blocks until release
   1.3 Wire into MTDS orchestrator, pass shard estimates from
       shard_memory_profile.estimated_peak_ram_gb
              ─── QG: synthetic burst of 8 heavy shards on a 32 GB VM
                       waits + serialises instead of OOMing ───
                              ↓
Phase 2 — MemoryWatchdog graduated thresholds (P1, ~half day)
   2.1 Refactor watchdog with on_pressure / on_critical / on_emergency
       callbacks and per-threshold cooldown
   2.2 Wire 75% threshold to MemoryAwareSemaphore.pause()
   2.3 Wire 85% threshold to flush all open StreamingParquetWriters
       in the orchestrator's writer cache (need to expose the cache
       to the watchdog — pass via callback registry on service start)
              ─── QG: synthetic 85% RSS injection triggers writer flush
                       within 5s; partial parquets land in GCS ───
                              ↓
Phase 3 — In-flight cancellation (P1, ~1 day)
   3.1 Add CancellationToken to download_csv_streaming
       (asyncio.iter_chunked loop checks token between chunks)
   3.2 Plumb token through _stream_finalise_chain_bulk per-batch loop
       (check token between iter_batches yields)
   3.3 Wire 92% threshold to cancel the heaviest in-flight stream;
       mark the cancelled shard as attempted_failed in manifest
              ─── QG: synthetic 92% RSS injection cancels the heaviest
                       stream within 10s; manifest row appears
                       attempted_failed with MEMORY_PRESSURE_CANCEL ───
                              ↓
Phase 4 — Emergency exit (P2, ~1h)
   4.1 96% threshold: emit MEMORY_PRESSURE_EMERGENCY event,
       atexit-flush manifest writer, os._exit(2)
   4.2 Verify: a deliberately-OOM'd VM at e2-standard-2 + 16GB
       allocator exits cleanly with manifest written instead of
       getting SIGKILL'd
              ─── QG: rc=2 on EXIT_STATUS file (clean emergency)
                       not rc=137 (OOM-killer SIGKILL) ───
```

## Success criteria

- **Phase 1**: 8-shard burst on a 32 GB VM with budget=20GB serialises to 1-shard-at-a-time when all shards estimate >20
  GB. Aggregate live RSS stays under budget.
- **Phase 2**: synthetic memory injection at 85% triggers `flush()` on every open writer; the GCS objects are finalised
  within 5s; in-flight Tardis streams continue.
- **Phase 3**: 92% threshold cancels heaviest stream within 10s; manifest row appears with
  `error_reason="MEMORY_PRESSURE_CANCEL"`; other in-flight shards complete normally.
- **Phase 4**: 96% threshold writes `EXIT_STATUS` rc=2 + flushes manifest before `os._exit(2)`. No SIGKILL signature (no
  rc=137 ghost).

## What we are NOT doing

- Not adding swap. GCE VMs without swap are intentional (swapping during ML+IO workloads tanks throughput).
- Not changing the streaming refactor (already shipped MTDS `3145615`). This plan layers on top — even if every shard is
  bounded to 30 MB, aggregate governance still matters when something regresses.
- Not adding distributed memory governance. Per-VM is sufficient — the orchestrator's \_graph_semaphore is already
  per-process.
- Not touching `shard_memory_profile.py` proactive sizing — that's a separate proactive layer and stays.

## Verification

End-to-end after Phase 3 ships:

1. Deploy a deliberate-OOM probe: 1 VM at e2-standard-4 (16 GB) processing a synthetic 50M-row "options_chain" payload
   (~12 GB DataFrame in legacy code, ~30 MB streaming).
2. With governance OFF: streaming refactor alone keeps it under 1 GB (verified empirically by the current rollout).
3. With governance ON + a regressed code path that loads the full DataFrame: the watchdog's 85% threshold force-flushes
   any open writers, the 92% cancels the heaviest stream, manifest records `attempted_failed` with
   `MEMORY_PRESSURE_CANCEL`, the VM stays alive and processes the remaining shards.

## Owner / when

P2 — depends on the streaming refactor having soaked in production for at least one rollout. The CeFi 366-VM rollout
firing 2026-04-29 is the soak. After it completes cleanly at e2-highmem-8 (or e2-standard-4), pick this up. Reference:
2026-04-29 v2/v3 audit + streaming refactor MTDS `3145615` + operator pushback "we should be memory aware at least
aggregate all the memory not just the memory on that thread".
