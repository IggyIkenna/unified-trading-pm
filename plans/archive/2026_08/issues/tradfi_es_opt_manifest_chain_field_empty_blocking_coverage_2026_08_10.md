---
doc_type: issue
title: ES_OPT manifest registration fails — chain='' rejected by hard_schema_enforcement
summary: >-
  ES_OPT backfill VMs download and write data to GCS successfully, but `ManifestWriter.record_captured()` rejects every
  row with `MalformedRowKeyError: shard-atom field 'chain' was explicitly passed as empty`. Fix is to either remove
  `chain` from the row_key for non-per-chain shards like `options_chain`, or populate it with a valid value before
  calling `record_captured`.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [tradfi, es-opt, manifest, chain-field, schema-enforcement, backfill]
related:
  [
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
  ]
created: "2026-08-10"
priority: P1
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
parent_epic: tradfi_master
source: >-
  ES_OPT backfill VM run.log (2026-08-10, tradfi-bf-es-opt-light-2026-20260810-113302) —
  gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-es-opt-light-2026-20260810-113302/run.log
resolved_by:
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-12 (/plan-reconcile) — RESOLVED.** The root-cause diagnosis misidentified the code path; the
> real fix (commit `29b4310e`) landed 68 minutes before this doc was even filed. See the "RESOLVED" section below for
> the full evidence chain.

# ES_OPT manifest chain='' blocking coverage — 2026-08-10

## Finding

ES_OPT backfill VMs (standard, non-SPOT) launched 2026-08-10T11:32Z successfully downloaded OHLCV data from Databento
and wrote parquet files to `gs://market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/`. But
manifest registration failed for EVERY date with:

```
WARNING Manifest write failed (non-blocking): MalformedRowKeyError:
shard-atom field 'chain' was explicitly passed as empty.
Per hard_schema_enforcement Phase 4, callers that include 'chain' in row_key
MUST supply a non-empty value.
row_key={'date': '2026-01-26', 'venue': 'CME', 'chain': '',
         'data_type': 'ohlcv_1m', 'league_id': '',
         'instrument_type': 'options_chain', 'underlying': 'SP500',
         'quote_asset': 'USD', 'margin_type': 'linear',
         'instrument_id': 'CME:OPTION:SP500'}.
Fix: either remove 'chain' from row_key (non-per-chain shard) or
populate it before calling record_captured.
```

**Data IS in GCS** — 16 dates processed (2026-01-02 through 2026-01-26), ~300K records, ~5 MB total. But the manifest
index doesn't know about any of it. Manifest query shows 149/286 captured (52.1%) for 2026 — all from the concurrent CME
futures campaign's incidental capture, not today's dedicated ES_OPT backfill.

## Root cause

Two sites pass `chain=''` in the row_key:

1. **`market_tick_data_service/live/manifest_recorder.py:181`**: `chain=chain or ""` — normalises None→"", which then
   trips `hard_schema_enforcement`.
2. **`unified_trading_library/manifest_writer_normalising.py:142`**: `chain = str(row_key.get("chain") or "")` — same
   pattern in the normalising wrapper.

ES_OPT (S&P 500 index options) has `instrument_type=options_chain` but no meaningful `chain` value — index options don't
use futures chains. The `chain` field should be OMITTED from the row_key for non-per-chain shards, not passed as empty
string.

## Impact

- 2026 ES_OPT coverage stuck at 52.1% in manifest despite data existing in GCS
- 2025 ES_OPT manifest coverage (284/284, 100%) likely also from CME campaign, not today's dedicated backfill
- Todo #2 of `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` blocked on 2026≥95% manifest coverage

## Evidence

- `deployment-service` VM run.log:
  `gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-es-opt-light-2026-20260810-113302/run.log`
- 16 dates processed, all with "Manifest write failed (non-blocking): MalformedRowKeyError"
- GCS data confirmed uploaded: `raw_tick_data/by_date/day=2026-01-{02..26}/.../underlying=SP500/.../ticks.parquet`
- Manifest: `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` — 149/286
  captured for 2026

## Recommended fix

In `manifest_recorder.py:181`: don't include `chain` in the row_key when it's empty/falsy — omit the key entirely rather
than passing `""`. The `hard_schema_enforcement` correctly rejects empty strings; the bug is passing `chain` at all when
it has no value.

Alternatively, populate `chain` with a valid non-empty value for index options (e.g. `chain=underlying` or a canonical
placeholder like `chain=INDEX`), but this changes the shard-atom contract and requires consumer migration.

## RESOLVED 2026-08-12 (/plan-reconcile)

This was **already fixed before this doc was filed**. The root-cause diagnosis above misidentified the code path:
`manifest_recorder.py`'s `MTDSShardManifestRecorder` is used only by the live websocket streaming handler, never by
batch VM backfills (the actual source of the ES_OPT run this doc describes). The real bug was in
`market_tick_data_service/engine/orchestrator/manifest_finalize.py`'s `_write_bundle_shard_row` — the function that
actually builds the row_key for bundle-grain shards (`league_id`/`underlying`/`quote_asset`/`margin_type`/
`instrument_id`, matching this doc's error signature exactly). It was fixed by commit `29b4310e` ("omit chain from
row_key when empty — unblocks ES_OPT manifest registration"), landed 12:59:20 UTC 2026-08-10 — **68 minutes before**
this doc's own commit (14:00:45 UTC). The fix omits `chain` from `base_row_key` when falsy, and is instrument-type-
agnostic (applies uniformly after the cluster-expected branch), so it covers `options_chain` (ES_OPT) the same as
`futures_chain` (VIX). A later same-day commit, `f0345e7df4`, only adds regression tests locking this in plus a
separate, unrelated sentinel-row fix — it does not itself change the bundle-path logic. Re-run the ES_OPT backfill and
re-check manifest coverage before assuming this is still broken.
