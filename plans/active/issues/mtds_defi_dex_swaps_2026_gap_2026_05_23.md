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

## Actions taken (2026-05-23, slot-6)

- [x] **Manifest reset run** — `scripts/reset_source_returned_zero_manifest.py` applied to DeFi bucket. Deleted 13,826
      SOURCE_RETURNED_ZERO rows (defi-flat-prd-copy-20260522: 2, mtds-vault-share-price-20260508: 6911, consolidated
      index: 6913). MTDS tarball rebuilt at sha 498148da (includes e86a6ad8 + 69d694b1 fixes).
- [x] **MTDS DeFi backfill VM launched** — `mtds-backfill-defi-20260523` RUNNING (asia-northeast1-c, e2-standard-4).
      Range: 2024-01-01→2026-05-23, all DeFi data_types. Tarball sha 498148da. Handler fixes included: dex_swaps
      hardcode (69d694b1), gas_fees null (69d694b1), lending_indices SM (e86a6ad8).
- [x] **T+10 verify** — `mtds-backfill-defi-20260523` confirmed RUNNING at T+10.
- [x] **UAC lookup_contract bug fixed** — `SchemaContractNotFoundError` for `instrument_type='POOL'` (uppercase)
      diagnosed; fixed with lowercase fallback in `lookup_contract` (UAC@397e7195 local; equivalent 8e1e7e58 on LDR).
      Both slots independently landed the same fix.
- [x] **MDPS DeFi 2024+2025 VMs relaunched with fix** — killed buggy `195633` VMs, rebuilt UAC tarball (sha
      `397e71950270` with fix), relaunched `mdps-defi-2024-20260523-215530` + `mdps-defi-2025-20260523-215530` RUNNING
      (asia-northeast1-c, e2-standard-8, run-ts=20260523-215530).
- [x] **T+10 verify run-ts=215530** — both `mdps-defi-2024-20260523-215530` + `mdps-defi-2025-20260523-215530` confirmed
      RUNNING at T+10. Logs show 429 rate-limiting for 2024 (expected, not an error) and schema violations for
      `chain`/`swap_count`/`volume_quote_usd` (root-caused; fixes applied — see below)
- [x] **Root-caused 3 new bugs blocking all dex_pool_swaps candle writes** (2026-05-23, post-T+10): (1) `swaps_ohlcv_4h`
      missing from UAC schema registry — `_TIMEFRAMES_DEFI` lacked `"4h"` while MDPS `default_timeframes` includes it →
      every 4h shard fails `SchemaContractNotFoundError`. Fixed: added `"4h"` to `_TIMEFRAMES_DEFI` in UAC
      `_candle_contracts.py`. (2) `chain` column dropped during candle assembly — `_PASSTHROUGH_COLUMNS = ["league_id"]`
      missing `"chain"` → raw tick `chain='ETHEREUM'` never reaches the candle DataFrame → schema write validation
      fails. Fixed: added `"chain"` to `_PASSTHROUGH_COLUMNS` in MDPS `live_workers.py`. (3) `swap_count` and
      `volume_quote_usd` never computed — required by `_DEX_EXT` schema contract but absent from
      `DefiSwapAdapter.process_to_candles()` output. Fixed: added `swap_count` + `volume_quote_usd` fields to
      `CandleOutput` in UAC `adapter_models.py`; populated from `count_arr` / `volume_arr` in `swap_adapter.py`; added
      `"swap_count": "sum"` + `"volume_quote_usd": "sum"` to `COLUMN_AGG_RULES` in MDPS `aggregation_rules.py`.
- [x] **Rebuild tarballs + relaunch VMs with all fixes** — killed 222351 VMs; rebuilt UAC tarball (sha=897ba58da637,
      UAC@897ba58d) + MDPS tarball (sha=23d4cf9, MDPS@23d4cf9); launched `mdps-backfill-defi-20260523-232742` (2024) +
      `mdps-backfill-defi-20260523-232808` (2025), both RUNNING asia-northeast1-c e2-standard-8, confirmed RUNNING T+15s
- [x] **Root-caused 2 more bugs from monitoring 232742/232808 VMs** (2026-05-24): (1) `swap_count` dtype `int32` but
      schema expects `int64` — fixed: `count_arr = np.zeros(n_candles, dtype=np.int64)` in `swap_adapter.py`. (2) All
      venues (UNISWAP_V2, UNISWAP_V3, CURVE) have `partition_mismatch`: `venue` column = `UNISWAP_V2` (from tick data
      `venue` column) but partition path = `venue=UNISWAP_V2-ETHEREUM` (from instrument_id prefix via
      `_eager_preprocess_and_recover_metadata`). Root cause: `_eager_preprocess_and_recover_metadata` sets
      `input_venue = instrument_id.split(':')[0]` = `'UNISWAP_V2-ETHEREUM'` from the parquet's `instrument_id` column;
      adapter was using `info["venue"]` = `'UNISWAP_V2'` (tick data column). Fix: derive `canonical_venue` from
      `info["instrument_id"].split(':')[0]` in swap_adapter.py. MDPS@561fdbe.
- [x] **Rebuild tarball + relaunch VMs with venue+dtype fixes** — MDPS tarball rebuilt (MDPS@cb3d11b, includes 561fdbe
      venue+dtype fix); launched `mdps-backfill-defi-20260524-082217` (2024) + `mdps-backfill-defi-20260524-082231`
      (2025), both RUNNING asia-northeast1-c e2-standard-8, T+10 RUNNING confirmed 2026-05-24
- [ ] **Post-completion**: verify dex_pool_swaps candles appear in processed_candles/ for 2024+2025; verify dex_swaps
      rows for 2026-01-25+ in MTDS GCS; then relaunch `mdps-defi-2026-*`

## Evidence

- `gsutil ls gs://market-data-tick-defi-prd-central-element-323112/day=2026-01-24/` → returns CURVE/UNISWAP files
- `gsutil ls gs://market-data-tick-defi-prd-central-element-323112/day=2026-01-25/` → returns 0 DEX swap files
- MDPS 2026 VM (any run-ts) manifests: all DeFi dates in 2026 → `empty_confirmed/SOURCE_RETURNED_ZERO`
- Context: `mdps_backfill_phase3_2026_05_22.md` (archived) + `mtds_mdps_master.md` MDPS-3.3.DeFi-V note
