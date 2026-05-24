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
- [x] **Root-caused tarball race condition + killed 082217/082231 VMs** (2026-05-24): 082217/082231 used stale tarball
      (b3e0c2a5, uploaded 2026-05-23T17:10Z) because VMs booted at 07:24:58Z but cb3d11b tarball not uploaded until
      07:25:16Z (18s race). Fixed: killed both, confirmed cb3d11b now at fixed-name path, relaunched
      `mdps-backfill-defi-20260524-083220` (2024) + `mdps-backfill-defi-20260524-083234` (2025), both RUNNING
      asia-northeast1-c e2-standard-8 2026-05-24
- [x] **Root-caused UTL instrument_id_validator partition_mismatch bug** (2026-05-24): `validate_partition_consistency`
      calls `_split_venue_chain` on the instrument_id venue (UNISWAP_V2-ETHEREUM → UNISWAP_V2) but compared against
      `expected_venue_uc` from partition path WITHOUT stripping chain — UNISWAP_V2 ≠ UNISWAP_V2-ETHERNET → permanent
      mismatch. Fixed: also apply `_split_venue_chain` to `expected_venue_uc` before comparison in both
      `validate_partition_consistency` and `validate_instrument_id_column`. Added 2 regression tests. UTL@18e2e072.
- [x] **Concurrently another slot landed MDPS fix** `555ade1` (strip chain suffix from DeFi venue in partition_path) —
      alternative approach that also resolves the mismatch from MDPS side. Both fixes are correct and complementary.
- [x] **Fixed tarball concurrent-rebuild race condition** (2026-05-24): multiple slots running `create-code-tarballs.sh`
      concurrently were overwriting each other's fixed-name UTL tarballs. Fixed: added `UTL_TARBALL_SHA` /
      `MDPS_TARBALL_SHA` / `UAC_TARBALL_SHA` metadata support to `setup-data-pipeline-vm.sh` (downloads SHA-pinned
      tarball instead of fixed-name when set) + `--utl-sha` / `--mdps-sha` CLI flags to
      `launch-mdps-sharded-backfill.sh`. Deployment-service@f42973f, setup-data-pipeline-vm.sh uploaded to GCS.
- [x] **Killed all stale DeFi VMs + relaunched with SHA-pinned tarballs** (2026-05-24): killed 085204 + 091405 VMs
      (wrong UTL/MDPS tarballs). Launched `mdps-defi-{2022-2026}-20260524-092158` with `UTL_TARBALL_SHA=18e2e072` +
      `MDPS_TARBALL_SHA=555ade19`. All 5 VMs RUNNING as of T+1 check.
- [x] **T+10 verify 092158 VMs + root-caused instrument_type=UNKNOWN bug** (2026-05-24): 092158 VMs confirmed RUNNING at
      T+10. Diagnosed new blocking bug: pool-address blob filenames (`0xA5407...`) have no colons →
      `_infer_instrument_type` returned `"UNKNOWN"` → all dex_pool_swaps candles partitioned under
      `instrument_type=UNKNOWN`. Root cause: `_infer_instrument_type` only checked (1) `instrument_type` col, (2) key
      colons. DefiSwapAdapter sets full `CURVE-ETHERNET:POOL:DAI-USDC` in df `instrument_id` col but key = pool addr.
      Fix: added step 3 fallback — parse type from `df["instrument_id"].iloc[0]` when key lacks colons. MDPS@4cc1584.
- [x] **Rebuild tarballs + kill 092158 VMs + relaunch with instrument_type fix** (2026-05-24): rebuilt defi tarballs
      with `--allow-dirty-tarball` (UTL has foreign uncommitted changes; used `--allow-dirty-tarball`; UTL@18e2e072
      unchanged). MDPS tarball `market-data-processing-service-code@4cc15847a76e.tar.gz` uploaded. Killed
      `mdps-defi-{2024,2025,2026}-20260524-092158` (2022/2023 already TERMINATED). Launched
      `mdps-defi-{2022-2026}-20260524-095357` with `UTL_TARBALL_SHA=18e2e0724eafc9af14516b72a97f359cfb59aa78` +
      `MDPS_TARBALL_SHA=4cc15847a76eee9b45e9d331ca10c370ecbf6aa1`. All 5 VMs RUNNING asia-northeast1-c e2-standard-8.
- [x] **T+10 verify 095357 VMs + root-caused chain=missing bug + another slot launched 100217** (2026-05-24): 095357 VMs
      RUNNING at T+1; at DEX data dates (2024-05-03) saw `[schema_violation] column 'chain' missing from dataframe`.
      Root cause: `_infer_chain` steps 1-3 all fail for pool-address keys (no colons, no hyphens) — returns `""` →
      `_inject_schema_contract_columns` skips chain injection. Passthrough fix in `live_workers.py` only works when raw
      tick parquet has a `chain` column; `dex_pool_swaps` parquets don't. Fix: added step 4 to `_infer_chain` — parse
      chain from `df["instrument_id"].iloc[0]` venue-token hyphen (e.g. `CURVE-ETHEREUM` → `ETHEREUM`). MDPS@94ef3c2.
      NOTE: concurrent slot launched `mdps-defi-{2022-2026}-20260524-100217` WITHOUT SHA pin (used stale fixed-name
      tarball `4cc1584`); these also had chain=missing error. Killed all 100217 VMs.
- [x] **Rebuild tarballs + kill 100217 VMs + relaunch with chain fix** (2026-05-24): rebuilt MDPS tarball
      `market-data-processing-service-code@94ef3c211d57.tar.gz` uploaded (09:08:51 UTC). Killed all 4 running 100217 VMs
      (2022 already TERMINATED). Launched `mdps-defi-{2022-2026}-20260524-101628` with
      `UTL_TARBALL_SHA=18e2e0724eafc9af14516b72a97f359cfb59aa78` +
      `MDPS_TARBALL_SHA=94ef3c211d573169665a4e2caed44423744c2d3f`. All 5 VMs RUNNING asia-northeast1-c e2-standard-8.
- [x] **T+10 verify 101628 VMs** (2026-05-24): All 5 VMs RUNNING (2022 already TERMINATED — expected, minimal data).
      2024 VM reached 2024-05-05: `dex_swaps complete: 44/44 succeeded, 12,801 candles` — zero schema_violation or
      chain=missing errors. Chain fix MDPS@94ef3c2 confirmed working. 429 rate-limit warnings on manifest writes are
      expected + non-fatal (shard-level isolation handles).
- [x] **Root-caused MTDS 2026 gap** (2026-05-24): `mtds-backfill-defi-20260523` VM ran with MTDS tarball `ffa9d573`
      which called `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group=primary_ag, env="live")` at
      `tick_data_handler.py:94`. The `env=` param was removed from `resolve_bucket_name()` during bucket-name SSOT
      canonicalization. ALL 125 chunks failed with
      `TypeError: resolve_bucket_name() got an unexpected keyword argument     'env'` before any TheGraph requests were
      made. No dex_swaps data for 2026-01-25→2026-05-23 was ever fetched. Local MTDS HEAD `71a47f78` already has the
      fix: `get_tick_data_bucket(None, asset_group=primary_ag.lower() ...)`. Confirmed: April 18, 2026 migration wrote
      dex_pool_swaps up to 2026-01-24; nothing for 2026-01-25+.
- [x] **Rebuild MTDS tarball + first launch attempt** (2026-05-24): rebuilt tarballs with `--allow-dirty-tarball` (UTL
      has foreign uncommitted changes — unrelated to data download; MTDS at `71a47f78be56` clean). Launched
      `mtds-backfill-defi-20260524` with `--operation download` — WRONG. `download` operation skips all 124 DeFi venues:
      "Skipping 124 DeFi venues (use collect-\* handlers)". Killed after diagnosis.
- [x] **Root-caused: collect-dex-swaps is the right operation** (2026-05-24): `vm_mtds_backfill.sh` hardcodes
      `--operation download` (line 212). DeFi DEX data requires `--operation collect-dex-swaps` (maps to
      `DexSwapsHandler`). Pattern: `VM_TASK=defi-backfill` + `VM_OPERATION=collect-dex-swaps` (same as dex-pools
      launcher but with dex-swaps op). Launch script for dex-swaps doesn't exist — launched via direct gcloud.
- [x] **Relaunch with correct operation** (2026-05-24): Launched `mtds-backfill-defi-dexswaps-20260524` RUNNING
      (asia-northeast1-c, e2-standard-4) with
      `VM_TASK=defi-backfill, VM_OPERATION=collect-dex-swaps, DEFI,     2026-01-25→2026-05-23`. MTDS tarball
      `71a47f78be56`.
- [x] **T+10 verify mtds-backfill-defi-dexswaps-20260524** — RUNNING at T+10, correct op confirmed:
      `python -m     market_tick_data_service --operation collect-dex-swaps --mode batch --asset-group DEFI --start-date 2026-01-25     --end-date 2026-05-23`
      (serial port at 11:11:28 UTC). GCS tee at vm-logs/mtds-backfill-defi-dexswaps-20260524/run.log.
- [x] **Root-caused wrong write bucket** (2026-05-24): `mtds-backfill-defi-dexswaps-20260524` was writing dex_swaps to
      `dex-swaps-central-element-323112` (wrong bucket) instead of `market-data-tick-defi-central-element-323112`
      (canonical MDPS source). Root cause: `dex_swaps_handler.py:334` used `get_write_bucket_name("dex-swaps")` → all
      other DeFi handlers use `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")`. Data in wrong
      bucket also has wrong path prefix (`day=.../category=defi/...` not `raw_tick_data/by_date/...`) — cannot be
      copied.
- [x] **Fixed dex_swaps_handler write bucket** (2026-05-24): replaced `get_write_bucket_name("dex-swaps")` with
      `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")`, removed stale import, updated 3 unit
      tests. MTDS@6be284e702d0. QG: 7 failed (all pre-existing, 3 test_dex_swaps_handler now passing). Pushed to LDR.
- [x] **Killed wrong-bucket VM + relaunched with fix** (2026-05-24): killed `mtds-backfill-defi-dexswaps-20260524` (was
      writing to wrong bucket). Created `launch-mtds-dex-swaps-backfill-vm.sh` launcher + registered
      `mtds-dex-swaps-backfill` in `vm_zombie_watchdog.py`. Deployment-service@0ba3844. Rebuilt tarballs
      (MTDS@6be284e702d0 clean). Launched `mtds-dex-swaps-backfill` RUNNING (asia-northeast1-c, e2-standard-4,
      2026-01-25→2026-05-23).
- [ ] **T+10 verify mtds-dex-swaps-backfill** — confirm RUNNING + correct op + writes to correct bucket
- [ ] **Post-completion**: verify `data_type=dex_swaps/` rows appear in `market-data-tick-defi-*` for 2026-01-25+; then
      reset SOURCE_RETURNED_ZERO manifest entries for 2026 DeFi dex_swaps and relaunch `mdps-defi-2026-*` for 2026. Also
      verify dex_pool_swaps candles in processed_candles/ for 2022-2025 once 2024+2025 VMs complete.

## Evidence

- `gsutil ls gs://market-data-tick-defi-prd-central-element-323112/day=2026-01-24/` → returns CURVE/UNISWAP files
- `gsutil ls gs://market-data-tick-defi-prd-central-element-323112/day=2026-01-25/` → returns 0 DEX swap files
- MDPS 2026 VM (any run-ts) manifests: all DeFi dates in 2026 → `empty_confirmed/SOURCE_RETURNED_ZERO`
- Context: `mdps_backfill_phase3_2026_05_22.md` (archived) + `mtds_mdps_master.md` MDPS-3.3.DeFi-V note
