---
doc_type: issue
title: MTDS live manifest-write to the -test- catalogue produces zero rows (silently)
summary: >-
  A paper-mode MTDS live run (2026-08-22, BINANCE-SPOT) captured 14,168 rows via record_captured and called
  MTDSShardManifestRecorder.close() → ManifestWriter.close(), but NO manifest index object landed in the -test-
  catalogue bucket; the write failure is swallowed by flush_window's per-instrument shard-isolation try/except. The
  tick parquet WAS written (direct-GCS sink), so capture works — only the manifest-write leg is silently lost. This
  blocks the manifest-verified-gap-rows done-when of the ws-resilience plan's MTDS C3 todo.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [live, data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [mtds, live, manifest, availability, test-bucket, silent-failure]
related:
  [
    /plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-22
parent_epic: system_readiness_master
assigned_vm: NA
priority: P1
context_scope:
  [
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
resolved_by:
locked_by:
source:
  "paper-mode MTDS rotation drill 2026-08-22, interactive session slot 4 — the ws-resilience C3 done-when's
  manifest-verified-gap-rows requirement surfaced that a -test--bucket live run persists zero manifest rows"
---

# MTDS live manifest-write to the -test- catalogue produces zero rows (silently)

## Evidence (paper-mode drill 2026-08-22, slot 4)

Real BINANCE-SPOT public trade feed through the landed `LiveWebsocketRunner` + `WsConnectorSessionBridge`
(market-tick-data-service@2bdad93bd5), every persistence surface on `-test-` infra
(`market-data-tick-cefi-test-central-element-323112`, direct-GCS `LiveWebsocketTickSink`, local Redis), 300s,
rotation at t+140s.

- `rows_captured_cum = 14168` (the runner's `_persist_window_to_sink` incremented it and awaited
  `record_flush_captured` → `MTDSShardManifestRecorder.record_captured` → `ManifestWriter.record_captured`).
- The runner's `_shutdown` called `self._manifest_recorder.close()` → `MTDSShardManifestRecorder.close()` →
  `getattr(self._writer, "close")()`.
- **GCS after the run**: the tick parquet `BINANCE-SPOT:SPOT_PAIR:BTC-USDT.parquet` is present (18,586 B), but
  `market-data-tick-cefi-test-central-element-323112` has **no `_catalogue/_index/per_vm/*` shard and no
  `_catalogue/_index/availability_index.parquet` (404)** — zero manifest rows persisted.

## Why it is silent

`LiveWebsocketRunner.flush_window` wraps each instrument's `_flush_instrument_window` in a per-instrument
try/except (shard-level failure isolation — correct for capture), so a raise inside the awaited
`record_flush_captured` is logged and swallowed, never surfaced. The manifest write failed inside that boundary.

## Candidate root causes (not yet bisected)

1. The `-test-` bucket lacks the manifest-writer SA write grant (prod live VMs write to the `-prd-` bucket, which
   has never exercised the `-test-` path).
2. `ManifestWriter(per_vm_shards=None)` resolves per-VM-shard mode from on-VM env detection; off-VM it may pick a
   write path that no-ops or targets an unexpected prefix.
3. A `ManifestWriter.close()` / `.flush()` early-return when `batch_size=1` + no explicit `.write()` between
   records (cf. the QG "record_*() early-return missing .write()/.flush()" rule).

## Fix / done-when

Bisect the three candidates (grant the `-test-` SA role if that is it — IAM self-service), make a paper/`-test-`
live run leave manifest rows readable from the `-test-` catalogue with honest `capture_status`, then flip the
ws-resilience plan's MTDS C3 done-when. Add a regression that fails if a `-test-` live run persists zero manifest
rows despite `rows_captured_cum > 0`.

## Scope note

This is a `-test-`-environment manifest-write-path gap, NOT a defect in the ws-resilience rotation logic — that
logic is proven end-to-end by the same drill (make-before-break, honest STALE-on-gap, ticks continuous across the
rotation). Filed separately so the ws-resilience code ships on its own evidence.
