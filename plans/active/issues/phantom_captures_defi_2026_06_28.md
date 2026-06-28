---
doc_type: plan
title: "Phantom captures — defi manifest (2026-06-28)"
created: 2026-06-28
parent_epic: observability_master
assigned_vm: NA
source:
  - reconcile_phantom_manifest_rows_all.py
  - mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)
summary: "219,529 phantom captures (10.5% of captured scope) in defi MTDS manifest — swaps_ohlcv_* dominant across Uniswap V3/V4, Balancer, SushiSwap. Major data integrity finding."
status: active
nature: process
asset_group: defi
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [phantom, defi, manifest-hygiene, data-quality]
related: []
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-28
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Phantom captures — defi manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`)
> run during Phase-0 catalogue finalization. Found 219,529 `capture_status=captured` rows in the MTDS defi manifest
> (`market-data-tick-defi-prd-central-element-323112/_index/`) with no backing GCS parquet.
> These are NOT catalogue-shape (they are DeFi market-data records — swaps OHLCV, DEX pool swaps, gas fees, etc.)
> → issue doc per plan triage rule.

## What I found

Manifest: `gcp://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 8,040,229
- Captured rows in scope: 2,089,059
- Unique (date, venue[, chain], hive-vocab) prefixes: 1,793,190
- **Real captures (parquet exists):** 1,869,530
- **Phantom captures (captured → no parquet):** 219,529 ← will flip to `attempted_failed` on `--apply`

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl` (219,529 records)

Phantom distribution by data_type (all 14 shown):

| data_type          | phantom count |
|--------------------|--------------|
| swaps_ohlcv_1d     | 25,437       |
| swaps_ohlcv_4h     | 25,432       |
| swaps_ohlcv_15m    | 25,424       |
| swaps_ohlcv_1h     | 25,424       |
| swaps_ohlcv_1m     | 25,418       |
| swaps_ohlcv_15s    | 25,399       |
| swaps_ohlcv_5m     | 25,397       |
| dex_pool_swaps     | 20,586       |
| gas_fees           | 12,249       |
| liquidations       | 8,509        |
| derivative_ticker  | 103          |
| perp_funding       | 92           |
| vault_share_price  | 30           |
| trades             | 29           |
| **TOTAL**          | **219,529**  |

Phantom distribution by venue (top 14 shown):

| venue           | phantom count |
|-----------------|--------------|
| UNISWAP_V4      | 69,573       |
| UNISWAP_V3      | 42,807       |
| BALANCER        | 31,967       |
| SUSHISWAP_V3    | 15,579       |
| PANCAKESWAP_V3  | 13,283       |
| ALCHEMY         | 12,249       |
| CURVE           | 10,492       |
| AAVE_V3         | 7,611        |
| SUSHISWAP       | 6,233        |
| CAMELOT_V3      | 4,965        |
| AERODROME_V3    | 3,618        |
| COMPOUND_V3     | 898          |
| ASTER           | 224          |
| MORPHOVAULTS    | 30           |

## Pattern analysis

The 7 `swaps_ohlcv_*` variants each have ~25,400 phantoms — nearly identical counts. This strongly suggests
a **systematic writer failure** (not individual shard failures): the manifest recorded captures but the
OHLCV aggregation writers never wrote the parquets. The near-uniform counts across all 7 time granularities
(1m/5m/15m/15s/1h/4h/1d) suggest the same set of (date, venue, pool_address) cells were affected.

UNISWAP_V4 (69,573) is the single largest venue — it was added to the DeFi universe recently; its writer
may have logged `captured` before actually writing parquets.

ALCHEMY (12,249 gas_fees) suggests the gas-fee writer had a similar issue (likely the same batch window).

## Why it matters

219,529 phantom rows (10.5% of captured scope) is a major data-correctness issue:
- The defi backfill plan's G0 gap analysis will count these as "captured" (not gaps) and skip them
- Without reconciliation, the defi backfill will leave these ~220k cells unbackfilled
- The defi backfill plan's G3 final verification includes its own phantom check — this will catch it,
  but applying the fix first avoids false starts

## Recommended decision

1. **Apply phantom reconciliation BEFORE defi backfill G0 gap analysis**:
   `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi` (no `--dry-run`,
   with `MANIFEST_PER_VM_SHARDS=true VM_NAME=defi-reconcile` per consolidator-SSOT).
   Reference triage JSONL: `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl`.
2. **Diagnose root cause**: check DeFi writer logs for the UNISWAP_V4/swaps_ohlcv batch window when
   these captures were logged. The uniform 25,400 count across all 7 granularities is a smoking gun for
   a batch that recorded manifest entries but crashed before writing.
3. **After reconcile**: re-run `--dry-run` to confirm 0 phantoms, then proceed with defi backfill G0.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`codex/05-infrastructure/manifest-consolidator-ssot.md` +
`codex/02-data/availability-manifest-and-data-status.md` +
`codex/02-data/defi-canonical-naming-ssot.md`.

## Todos

- [ ] [SCRIPT] P1. Diagnose defi phantom root cause: uniform ~25,400 counts across 7 swaps_ohlcv_* granularities
      + UNISWAP_V4 dominance suggest a single batch writer failure. Check DeFi OHLCV writer logs for affected window.
      Repo: `market-tick-data-service`.
- [ ] [SCRIPT] P1. Apply defi phantom reconciliation (219,529 rows → `attempted_failed`) BEFORE defi backfill G0.
      Run `reconcile_phantom_manifest_rows_all.py --asset-group defi` (no dry-run) with `MANIFEST_PER_VM_SHARDS=true`.
      Verify with `--dry-run` post-apply confirms 0 phantoms. Repo: `instruments-service`.
- [ ] [SCRIPT] P2. After reconcile + backfill: confirm defi OHLCV writers are fixed so new writes don't re-create
      phantom pattern. Repo: `market-tick-data-service`.
