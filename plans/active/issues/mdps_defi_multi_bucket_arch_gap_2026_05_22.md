---
title: "MDPS DeFi multi-bucket architectural gap — LST rates/DEX pools/lending indices not processable"
created: 2026-05-22
author: slot-7
source:
  - mdps_backfill_phase3_2026_05_22.md
  - plans/epics/mtds_mdps_master.md
---

## What I found

MDPS DeFi (`MDPS_ASSET_GROUP=DEFI`) can only process data from ONE source bucket
(`PROTOCOL_DATA_SOURCE_BUCKET_DEFI = market-data-tick-defi-central-element-323112`). That bucket contains only
**vault_share_price** data (venues: ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARNV3).

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

## Recommended decision

Operator / slot-1 main should clarify the intended pipeline for DeFi non-vault data types:

- Option A: Features-onchain reads directly from separate buckets → document this in codex as DeFi special-case (bypass
  MDPS for lst_rates/dex_pool_state/lending_indices). MDPS DeFi scope = vault_share_price only.
- Option B: Add multi-bucket support to MDPS config (PROTOCOL_DATA_SOURCE_BUCKET_DEFI becomes a list OR additional
  per-datatype env vars). Requires MDPS code change.
- Option C: Add a migration/copy step that consolidates all DeFi raw data into
  `market-data-tick-defi-*/raw_tick_data/by_date/`.

Current blocker: MDPS-3.3.DeFi-V can only verify vault_share_price bars until this is resolved.
