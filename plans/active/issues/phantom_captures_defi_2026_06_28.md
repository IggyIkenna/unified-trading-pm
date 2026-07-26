---
doc_type: issue
title: Phantom captures — defi manifest (2026-06-28)
summary:
  219,529 phantom captures (10.5% of captured scope) in defi MTDS manifest — swaps_ohlcv_* dominant across Uniswap
  V3/V4, Balancer, SushiSwap. Major data integrity finding.
status: open
nature: process
asset_group: [defi]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [phantom, defi, manifest-hygiene, data-quality]
related: [mvp_backfill_defi_onchain_v10_2026_06_27]
created: 2026-06-28
parent_epic: observability_master
priority: P1
source: [reconcile_phantom_manifest_rows_all.py, mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-28
locked_since: 2026-05-21
---

# Phantom captures — defi manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`)
> run during Phase-0 catalogue finalization. Found 219,529 `capture_status=captured` rows in the MTDS defi manifest
> (`market-data-tick-defi-prd-central-element-323112/_index/`) with no backing GCS parquet. These are NOT
> catalogue-shape (they are DeFi market-data records — swaps OHLCV, DEX pool swaps, gas fees, etc.) → issue doc per plan
> triage rule.

## What I found

Manifest: `gcp://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 8,040,229
- Captured rows in scope: 2,089,059
- Unique (date, venue[, chain], hive-vocab) prefixes: 1,793,190
- **Real captures (parquet exists):** 1,869,530
- **Phantom captures (captured → no parquet):** 219,529 ← will flip to `attempted_failed` on `--apply`

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl` (219,529 records)

Phantom distribution by data_type (all 14 shown):

| data_type         | phantom count |
| ----------------- | ------------- |
| swaps_ohlcv_1d    | 25,437        |
| swaps_ohlcv_4h    | 25,432        |
| swaps_ohlcv_15m   | 25,424        |
| swaps_ohlcv_1h    | 25,424        |
| swaps_ohlcv_1m    | 25,418        |
| swaps_ohlcv_15s   | 25,399        |
| swaps_ohlcv_5m    | 25,397        |
| dex_pool_swaps    | 20,586        |
| gas_fees          | 12,249        |
| liquidations      | 8,509         |
| derivative_ticker | 103           |
| perp_funding      | 92            |
| vault_share_price | 30            |
| trades            | 29            |
| **TOTAL**         | **219,529**   |

Phantom distribution by venue (top 14 shown):

| venue          | phantom count |
| -------------- | ------------- |
| UNISWAP_V4     | 69,573        |
| UNISWAP_V3     | 42,807        |
| BALANCER       | 31,967        |
| SUSHISWAP_V3   | 15,579        |
| PANCAKESWAP_V3 | 13,283        |
| ALCHEMY        | 12,249        |
| CURVE          | 10,492        |
| AAVE_V3        | 7,611         |
| SUSHISWAP      | 6,233         |
| CAMELOT_V3     | 4,965         |
| AERODROME_V3   | 3,618         |
| COMPOUND_V3    | 898           |
| ASTER          | 224           |
| MORPHOVAULTS   | 30            |

## Pattern analysis

The 7 `swaps_ohlcv_*` variants each have ~25,400 phantoms — nearly identical counts. This strongly suggests a
**systematic writer failure** (not individual shard failures): the manifest recorded captures but the OHLCV aggregation
writers never wrote the parquets. The near-uniform counts across all 7 time granularities (1m/5m/15m/15s/1h/4h/1d)
suggest the same set of (date, venue, pool_address) cells were affected.

UNISWAP_V4 (69,573) is the single largest venue — it was added to the DeFi universe recently; its writer may have logged
`captured` before actually writing parquets.

ALCHEMY (12,249 gas_fees) suggests the gas-fee writer had a similar issue (likely the same batch window).

## Why it matters

219,529 phantom rows (10.5% of captured scope) is a major data-correctness issue:

- The defi backfill plan's G0 gap analysis will count these as "captured" (not gaps) and skip them
- Without reconciliation, the defi backfill will leave these ~220k cells unbackfilled
- The defi backfill plan's G3 final verification includes its own phantom check — this will catch it, but applying the
  fix first avoids false starts

## Recommended decision

1. **Apply phantom reconciliation BEFORE defi backfill G0 gap analysis**:
   `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi` (no `--dry-run`, with
   `MANIFEST_PER_VM_SHARDS=true VM_NAME=defi-reconcile` per consolidator-SSOT). Reference triage JSONL:
   `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl`.
2. **Diagnose root cause**: check DeFi writer logs for the UNISWAP_V4/swaps_ohlcv batch window when these captures were
   logged. The uniform 25,400 count across all 7 granularities is a smoking gun for a batch that recorded manifest
   entries but crashed before writing.
3. **After reconcile**: re-run `--dry-run` to confirm 0 phantoms, then proceed with defi backfill G0.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`/codex/05-infrastructure/manifest-consolidator-ssot.md` + `/codex/02-data/availability-manifest-and-data-status.md` +
`/codex/02-data/defi-canonical-naming-ssot.md`.

## Todos

- [ ] [SCRIPT] P1. Diagnose defi phantom root cause: uniform ~25,400 counts across 7 swaps_ohlcv_* granularities +
      UNISWAP_V4 dominance suggest a single batch writer failure. Check DeFi OHLCV writer logs for affected window.
      Repo: `market-tick-data-service`.
- [ ] [SCRIPT] P1. Apply defi phantom reconciliation (219,529 rows → `attempted_failed`) BEFORE defi backfill G0. Run
      `reconcile_phantom_manifest_rows_all.py --asset-group defi` (no dry-run) with `MANIFEST_PER_VM_SHARDS=true`.
      Verify with `--dry-run` post-apply confirms 0 phantoms. Repo: `instruments-service`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-26 (worker, slot 6).** Confirmed against the CURRENT writer code (the original
      batch OHLCV writer implicated in this finding was RETIRED 2026-07-18/19 for a per-instrument writer
      re-architecture, `market-tick-data-service@4ca2640d` — this re-checks the NEW path, not the retired one). Full
      writeup in Progress Log below. Verdict: SAFE across every active writer for `dex_pool_swaps`/`gas_fees` —
      `record_captured` fires only after a confirmed-successful parquet upload, in every handler checked. No new issue
      doc needed; nothing to fix. Repo: `market-tick-data-service`.

## Progress Log

- 2026-07-26 (worker, slot 6, `defi_satellite_ao_dispatch_batch2-021`): re-verified the write-then-record ordering (the
  exact bug class suspected here) across every active DeFi writer handling `dex_pool_swaps`/`gas_fees` in
  `market-tick-data-service` (repo scope per this doc + the batch2 todo). `swaps_ohlcv_*` is out of scope for this repo
  — it is written by market-data-processing-service (MDPS), not MTDS; not re-checked here.
  - `write_defi_rows` (`market_interface/adapters/defi/canonical_write.py:158-351`) — never touches GCS or calls
    `record_captured`; pure sharding helper. Not itself a risk point.
  - `evm_defi_collectors.py::_write_and_upload` (`cli/handlers/evm_defi_collectors.py:42-85`) — SAFE.
    `storage.upload_bytes` (line 81) runs per-shard before the counts are returned; `record_captured` (line 636) fires
    only from the `try` block whose exception path calls `record_failed` (line 597) instead.
  - `dex_swaps_handler.py` (`dex_pool_swaps`) — SAFE. `_write_swap_shard` (line 484-528) uploads every shard (line 525)
    before building the row-count map; `_collect_one_shard` (line 271-315) only reaches `record_captured`
    (`_dex_swaps_queries.py:154`) after that succeeds — an upload exception routes to `record_failed` (line 307)
    instead.
  - `gas_fee_handler.py` (`gas_fees`) — SAFE across all 4 write paths (EVM date-shard, Solana historical, Solana live,
    BTC); each uploads (e.g. line 770) inside the `try:` (line 330) that `record_captured` depends on (line 332); an
    exception routes to `record_failed` (line 303) instead.
  - Live WS streaming path (`live/websocket_runner.py` → `curve_defi_ws.py`/`dex_swap_uniswap_v3_ws.py`) — SAFE.
    `_persist_window_to_sink` (line 640-688) calls `record_captured` (line 676) only using the `blob_path` returned by a
    successful `flush` (line 651); `LiveWebsocketTickSink.flush` (line 164-190) has no swallowing try/except around
    `upload_bytes` (line 189), so a failure raises and `record_captured` is unreachable for that window.
  - Shared foundation: `GCPCloudProvider.upload_bytes` (unified-trading-library
    `cloud_interface/providers/gcp.py:230-246`) has no swallowing try/except — GCS SDK errors propagate as real
    exceptions, which every handler above relies on. `DefiManifestRecorder.record_captured`
    (`cli/handlers/_defi_manifest.py:153`) is a thin per-row `ManifestWriter` shim — no batch-level "mark all captured"
    shortcut exists that could decouple it from an individual write's success.
  - **Verdict: the 2026-06-28 phantom-capture ordering bug is CLOSED for the current writer generation** — every active
    `dex_pool_swaps`/`gas_fees` handler correctly gates `record_captured` on a confirmed prior write. No new issue doc
    filed (nothing found vulnerable). Todos 1+2 above (root-cause diagnosis of the ORIGINAL 2026-06-28 incident +
    applying the 219,529-row reconciliation) are unrelated to this check and remain open — out of this todo's scope
    (read-only code review, no live backfill/reconciliation run, per the batch2 plan's own todo text).
