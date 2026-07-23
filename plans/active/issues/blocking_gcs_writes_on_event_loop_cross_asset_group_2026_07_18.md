---
doc_type: issue
title: >-
  Blocking GCS writes on the asyncio event loop — cross-asset-group audit (3 fixed, DeFi concurrency still open)
summary: >-
  After the Tardis batch finalizer was found to freeze the event loop (~97% of wall time), three parallel read-only
  audits swept the OTHER live and batch writers for the same class. Three real instances were found and fixed the same
  day — the live websocket_runner hot path, the shared venue_fetch writer.close, and sports per-shard writes. The
  largest remaining item is not a blocking-IO bug at all: the DeFi CLI handler family has ZERO concurrency at any level
  (dates serial, protocol x chain serial), which is a throughput ceiling rather than a wedge. Fixing that concurrency
  first REQUIRES fixing the latent blocking writes underneath it, or it converts them into live event-loop bugs.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [asyncio, event-loop, gcs, throughput, defi, sports, live]
related:
  [
    /plans/archive/issues/backfill_vm_disk_starvation_misdiagnosed_as_tardis_quota_2026_07_18.md,
    /plans/archive/issues/launcher_gcloud_continuation_broken_by_disk_sweep_2026_07_18.md,
  ]
created: 2026-07-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: advance-code
depends_on: []
source: ["three parallel read-only writer audits run after the 2026-07-18 CeFi disk/throughput investigation"]
resolved_by:
locked_by:
---

# Blocking GCS writes on the event loop — cross-asset-group audit

## Why this audit ran

The 2026-07-18 CeFi throughput investigation found that a synchronous GCS upload called inline in an async coroutine
froze the single event loop for ~1.6s per shard, serialising every concurrent fetch — about 97% of that run's wall
clock. The operator asked whether the same class exists in the other live and batch writers. Three read-only audits ran
in parallel over (a) MTDS/MDPS live, (b) TradFi/Databento, (c) DeFi + sports/prediction.

## Fixed the same day

| Path                | Site                                                                      | Why it mattered                                                                                                                                                                                                                                                                         |
| ------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Live (MTDS)         | `live/websocket_runner.py` `_persist_window_to_sink`, `_emit_empty_shard` | `record_captured` / `record_zero_rows` cascade into a full GCS download + parquet merge + upload of the per-VM shard, on the loop, every window. Worsens through the day as the shard grows; the 5s flush debounce never helps because the live `base_timeframe` is 60s.                |
| Shared venue writer | `engine/orchestrator/venue_fetch.py` `_process_venue` (3 sites)           | `writer.close()` walks every partition doing a blocking `upload_file()` (5 retries / 60s backoff). Up to 6 venues run concurrently under `asyncio.gather` on multi-venue cron/poll VMs, so one venue's upload tail stalled all the others. Used by TradFi, CeFi, sports AND prediction. |
| Sports              | `venue_fetch.py` `_process_sports_venue_with_leagues` (2 sites)           | One `shard_writer.close()` per (bookmaker, league, fixture) shard — dozens to hundreds per venue per day, each a round trip AND a loop freeze. Direct sibling of the row above, 60 lines below it, missed when that fix was written.                                                    |

Ordering is preserved at every site: the call is still awaited before the coroutine continues, so rows and manifest
entries are written in the same sequence. Only the loop is released during the GCS I/O.

## Open — in priority order

### 1. DeFi handlers have no concurrency at any level (the real throughput item)

`unified_trading_library/service_framework/_adapter.py` processes BatchPayloads (dates) one at a time via
`async for ... await self._handler.process(payload)`, never gathered. Inside a date, `dex_pools_handler`,
`dex_swaps_handler`, `evm_defi_collectors` and siblings (gas_fees, lst_rates, solana_defi, liquidations,
vault_share_price, eigenlayer_rewards) run nested `for protocol: for chain: await ...` with no semaphore or gather. A
default launch (e.g. `launch-mtds-dex-swaps-backfill-vm.sh`, START_DATE 2023-01-01) is ~1300 days x 20-35 protocol/chain
combos of strictly sequential round trips on ONE VM.

The fetches themselves are already correctly server-side batched (The Graph `first:100-1000`, <=500-pool batches), so
the win is purely adding `asyncio.gather` + a `Semaphore` across the (protocol, chain) loop — the pattern Polymarket and
Kalshi already use correctly (`polymarket_adapter.py`, `kalshi_adapter.py`, `_solana_defi_fetch.py`).

**Do the blocking-write fix (item 2) FIRST or in the same change.** Parallelising the loop while the writes are still
inline converts every latent blocking write below into a live event-loop bug.

### 2. Latent blocking writes in DeFi handlers — needs per-site verification, NOT a mass edit

The audit reported ~12 handlers calling `storage.upload_bytes` synchronously from async handlers. **Spot-checking showed
the reported line numbers had drifted and the characterisation was too broad**: of three sampled sites, only one
(`dex_swaps_handler.py` `_collect_protocol_chain` -> `_write_swap_shard`) actually has an async caller invoking a
blocking writer. The other two (`gas_fee_handler._collect_solana_historical`, `lst_rates_handler._finalize_lst_rows`)
sit in SYNC functions, so they are not event-loop bugs as written, and one cited line was not an upload call at all.

So the fix is per-site: find where async code invokes each sync writer helper and wrap **that call**, rather than
editing the helpers. Verify each site's enclosing function is genuinely `async def` before touching it.

Note `dex_swaps_handler.py` is already at exactly its 900-line cap, and `_collect_protocol_chain` is at its function
size cap — a one-line fix does not fit. That file needs the concurrency refactor (item 1) anyway, so do both together.

### 3. Live sibling sites in SYNC functions

`live/websocket_runner.py::_record_empty_window` and
`unified_trading_library/streaming/live_aggregator.py::_handle_zero_tick_window` perform the same blocking manifest
write but from sync functions, so fixing them needs signature changes up the call chain. Lower value than items 1-2
(they are the zero-row paths).

### 4. Default-executor DNS contention — watch, do not fix yet

Every live WS connector and several DeFi adapters build `aiohttp.TCPConnector(resolver=ThreadedResolver())`, and
`ThreadedResolver` runs `getaddrinfo` on the DEFAULT thread pool, which `asyncio.to_thread` also uses. This is the
mechanism that once wedged the Tardis path at cpu=0% with 203 ConnectionTimeouts. It does NOT bite today because live
runs ~1 blocking call at a time (one OS process per shard) and DeFi's `Semaphore(10)` x <=3 venues stays under the
default pool's ~32 slots. It becomes real if item 1 raises DeFi concurrency, or if live ever fans out per-instrument
flushes. If either happens, give those paths a dedicated executor first.

## Verification standard for this issue

Every fix above must be verified the way the shipped ones were: confirm the enclosing function is `async def`, confirm
the call is still awaited (ordering preserved), and check the file's line/function caps before adding comments — the
900-line cap is enforced and a rationale comment is enough to break it.
