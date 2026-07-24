---
doc_type: issue
title: MDPS DeFi multi-bucket architectural gap — LST rates/DEX pools/lending indices not processable
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-22
source: [mdps_backfill_phase3_2026_05_22.md, plans/epics/mtds_mdps_master.md]
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — RESOLVED — Option A (features-onchain raw bypass) confirmed;
> `/codex/02-data/defi-data-pipeline.md §7.1` documents the model; 3 unnecessary MDPS VMs deleted. Doc itself says
> 'close this issue'.
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

## What I found

MDPS DeFi (`MDPS_ASSET_GROUP=DEFI`) can only process data from ONE source bucket
(`PROTOCOL_DATA_SOURCE_BUCKET_DEFI = market-data-tick-defi-central-element-323112`). That bucket contains only
**vault_share_price** data (venues: ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3).

The other 3 DeFi raw-data categories are stored in **separate buckets** with a **flat** `day=YYYY-MM-DD/` prefix (not
`raw_tick_data/by_date/day=YYYY-MM-DD/` that MDPS expects):

| Data type           | Source bucket                                  | Path prefix                                     |
| ------------------- | ---------------------------------------------- | ----------------------------------------------- |
| `lst_rates`         | `lst-rates-central-element-323112`             | `day=*/`                                        |
| `lending_indices`   | `lending-indices-central-element-323112`       | `day=*/`                                        |
| `dex_pool_state`    | `dex-pools-central-element-323112`             | `day=*/`                                        |
| `vault_share_price` | `market-data-tick-defi-central-element-323112` | `raw_tick_data/by_date/day=*/asset_group=defi/` |

Attempted to launch 4 MDPS VMs with `--source-bucket` flag (deployment-service@f044f0a). All 4 immediately
self-terminated — MDPS scanner found 0 dates to process because the flat `day=*/` prefix is not recognised.

## Why it matters

MDPS DeFi produces `processed_candles` for `lst_yields`, `lending_indices`, `market_state` data types (per
`canonical_writer.py` mapping). If MDPS can't read from the separate buckets, those processed_candles are never produced
→ features-onchain has no aggregated bars to consume for LST/DEX/lending strategies.

Either:

1. **Features-onchain reads directly from separate buckets** (bypassing MDPS entirely for these data types), OR
2. **MDPS needs multi-bucket support** or data needs to be merged into main DeFi bucket before MDPS runs, OR
3. **There is a missing MTDS step** that copies/transforms data from separate buckets into the main DeFi bucket with the
   correct path structure.

## Resolution — CONFIRMED Option A (2026-05-22 slot-6)

**Option A is correct**: features-onchain reads directly from the specialized buckets — these are "bypass types".

Code evidence from features-service (slot-6 investigation 2026-05-22):

| Data type         | features-service entry point                     | Bucket domain     |
| ----------------- | ------------------------------------------------ | ----------------- |
| `lst_rates`       | `OnChainDataLoader.load_oracle_prices()`         | `lst-rates`       |
| `lending_indices` | `OnChainDataLoader.load_rate_indices()`          | `lending-indices` |
| `dex_pool_state`  | `_resolve_mtds_parquet_files("dex_pools", date)` | `dex-pools`       |

`dependency_checker.py` explicitly states: _"MDPS processed_candles is NOT required for DeFi on-chain snapshot types.
MDPS aggregates only 5 DeFi data_types: book_snapshot_5 / dex_swaps / fx_rates / market_state / liquidity. On-chain
snapshot data_types (vault_share_price / lst_rates / oracle_prices / lending_indices / perp_funding / etc.) flow
directly from MTDS raw_tick_data."_

**Actions taken (slot-6 2026-05-22)**:

- Deleted 3 unnecessary MDPS VMs that were processing bypass-type data: `mdps-backfill-defi-dex-pools-20260522-094538`,
  `mdps-backfill-defi-lending-indices-20260522-094523`, `mdps-backfill-defi-lst-rates-20260522-094503`
- `mdps-backfill-defi-20260522-095053` (main DeFi MDPS VM) kept running — it reads from `market-data-tick-defi-*` for
  `dex_swaps` data (which IS an MDPS-processed type)
- vault_share_price in main DeFi bucket is also a bypass type; MDPS will skip/write empty for it

**Codex update needed**: document DeFi data flow in `/codex/04-architecture/defi-execution-overview.md` or
`codex/02-data/` — "DeFi bypass types" section. Assign to features-service codex update pass.

**Status: RESOLVED — no operator decision needed.** Arch gap is expected design; 3 VMs deleted; main DeFi MDPS VM
continues for dex_swaps coverage. Close this issue doc.
