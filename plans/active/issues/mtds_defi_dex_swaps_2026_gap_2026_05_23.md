---
title: MTDS DeFi DEX swap data stops after 2026-01-24 — no Ethereum DEX candles for 2026
created: 2026-05-23
author: slot-6
source:
  - GCS audit during MDPS DeFi backfill verification (2026-05-23)
  - mdps_backfill_phase3_2026_05_22.md (now archived)
locked_by: live-defi-rollout
parent_epic: epics/mtds_mdps_master.md
assigned_vm: planning-vm
priority: P1
status: active
---

## What I found

GCS audit of `market-data-tick-defi-prd-central-element-323112` on 2026-05-23:

- `dex_pool_swaps` parquets present for dates through **2026-01-24** (CURVE, UNISWAP_V2, UNISWAP_V3)
- **2026-01-25 onward**: zero DEX swap parquets for any Ethereum DEX venue
- Last date with DEX swap data: `day=2026-01-24`
- Confirmed by checking day=2026-01-25, 2026-02-01, 2026-03-01, 2026-04-01 — all empty

Venues affected: CURVE-ETHEREUM, CURVE, UNISWAP_V2-ETHEREUM, UNISWAP_V2, UNISWAP_V3-ETHEREUM, UNISWAP_V3

## Why it matters

MDPS DeFi backfill VMs for 2026 (`mdps-defi-2026-*`) will produce:

- `empty_confirmed/SOURCE_RETURNED_ZERO` for every date from 2026-01-25 → 2026-05-23
- This is correct honest-absence (not a bug in MDPS) — the source data is missing

**Downstream impact**: `arbitrage_price_dispersion` archetype requires Ethereum DEX price spreads. The strategy cannot
evaluate DEX→CEX spread for any 2026 date after 2026-01-24 until this gap is filled.

## Root cause (likely)

MTDS `dex_swaps_handler` (or the upstream on-chain data feed that writes to the tick bucket) stopped emitting for
Ethereum DEX venues after 2026-01-24. Possible causes:

1. RPC endpoint quota/rate-limit hit on the on-chain reader
2. Handler config change that excluded CURVE/UNISWAP venues
3. Upstream GCS feed (batch_onchain_rpc pipeline) stopped writing for those venues

## Recommended decision

1. **Identify root cause**: check MTDS logs for `dex_swaps_handler` around 2026-01-24 → 2026-01-25. Check if the
   batch_onchain_rpc pipeline for Ethereum DEX venues is still running.
2. **Relaunch MTDS DeFi reprocessor for 2026**: once root cause is fixed, launch `market-tick-data-service` backfill VM
   for `dex_swaps` / `dex_pool_swaps` covering 2026-01-25→present.
3. **After MTDS gap filled**: relaunch `mdps-defi-2026-*` VM to produce DEX candles for 2026.

## Evidence

- `gsutil ls gs://market-data-tick-defi-prd-central-element-323112/day=2026-01-24/` → returns CURVE/UNISWAP files
- `gsutil ls gs://market-data-tick-defi-prd-central-element-323112/day=2026-01-25/` → returns 0 DEX swap files
- MDPS 2026 VM (any run-ts) manifests: all DeFi dates in 2026 → `empty_confirmed/SOURCE_RETURNED_ZERO`
- Context: `mdps_backfill_phase3_2026_05_22.md` (archived) + `mtds_mdps_master.md` MDPS-3.3.DeFi-V note
