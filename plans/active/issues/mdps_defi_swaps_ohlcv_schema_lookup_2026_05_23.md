---
title: MDPS DeFi dex_swaps → swaps_ohlcv schema lookup fails — instrument_type case mismatch (POOL vs pool)
created: 2026-05-23
author: slot-2-ikenna
source:
  - market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py
  - unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py
  - vm-logs/mdps-defi-2024-20260523-195633/run.log
  - vm-logs/mdps-defi-2025-20260523-195633/run.log
locked_by: live-defi-rollout
---

## What I found

MDPS DeFi backfill VMs (195633 batch) are logging repeated CRITICAL errors for every `dex_pool_swaps` pool shard:

```
[CRITICAL] unknown error in market-data-processing-service.process_instrument_file:
  No SchemaContract registered for asset_group='defi' instrument_type='POOL'
  data_type='swaps_ohlcv_15s' venue='UNISWAP_V3-ETHEREUM'.
  Add a contract to unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY...
```

**Root cause**: `_infer_instrument_type` in `canonical_writer.py:228` reads the `instrument_type` column directly from
the raw tick parquet — MTDS writes `"POOL"` (uppercase). `lookup_contract` looked up
`("defi", "POOL", "swaps_ohlcv_15s")` in `CONTRACT_REGISTRY`, which stores keys as lowercase `"pool"`. Case mismatch →
miss → `SchemaContractNotFoundError` on every DEX pool shard.

Affected venues: `UNISWAP_V3-ETHEREUM`, `UNISWAP_V2-ETHEREUM`, `CURVE-ETHEREUM`, `UNISWAP_V3-ARBITRUM`, and likely all
other DEX venues whose raw parquets use uppercase `instrument_type`. The 2025 VM logged "175 more errors" for a single
date.

## Fix shipped

**UAC@8e1e7e58** (`fix(contracts): add lowercase fallback in lookup_contract for instrument_type`) — 2026-05-23 ~21:xx
UTC, slot-2.

`lookup_contract` now retries with `instrument_type.lower()` after the exact key misses. Preserves existing uppercase
registrations (`UNKNOWN`, `PREDICTION_MARKET`) — they still match on the first-pass exact lookup. 10 pre-existing QG
failures, 0 new failures.

## Impact on in-flight 195633 VMs

The 195633 batch VMs have **stale UAC** in their tarball (provisioned before UAC@8e1e7e58). Their dex_swaps processing
will produce:

- `attempted_failed` manifest rows for every Uniswap/Curve/etc. pool shard across all dates they're processing
  (2024-01-01+, 2025-01-01+)
- No `swaps_ohlcv_*` candle parquets for those pool×date combinations

When operator rebuilds tarballs post-195633 and relaunches, new MDPS VMs pick up UAC@8e1e7e58 and will correctly produce
`swaps_ohlcv_*` candles. Pre-flight should retry `attempted_failed` dex_swaps cells.

## Recommended decision

1. **Let 195633 VMs complete** (they're still producing valid candles for other data_types — gas_fees, lending_indices,
   lst_rates, etc.). Killing them would require reprocessing those dates entirely.
2. **Operator: after 195633 VMs terminate**, rebuild tarballs:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh` (picks up UAC@8e1e7e58
   - any other LDR fixes). Relaunch MDPS DeFi for 2024-2025 to pick up the dex_swaps candles that are currently absent.
3. **Verify**: after relaunch, spot-check `swaps_ohlcv_15s` parquets for `UNISWAP_V3-ETHEREUM` pool shards in 2024-07
   and 2025-02 dates.

## Third schema gap — found from 083200 VM (partition_mismatch + GCS 429)

**Root cause 1: `partition_path` built with chain-qualified venue**

`canonical_writer.write_candle_parquet()` built `partition_path` with `venue=UNISWAP_V3-ETHEREUM` (full form), but UTL's
`instrument_id_validator._split_venue_chain()` strips the chain suffix from the instrument_id's venue token before
comparing against the partition — getting `base_venue=UNISWAP_V3`. So it compared `UNISWAP_V3` against
`UNISWAP_V3-ETHEREUM` → `partition_mismatch` on every shard using the new MTDS format (`UNISWAP_V3-ETHEREUM:POOL:0x…`
instrument_ids). Old-format tick parquets (`UNISWAP_V3:POOL:0x…`) were unaffected (venue=UNISWAP_V3, no chain).

**Root cause 2 (related): `asset_group=` in partition_path**

An adjacent bug: the partition_path used `category=` instead of `asset_group=`. Fixed separately in MDPS@8d4639f.

**Root cause 3 (related): chain column not injected before validator**

MDPS@6fe0f01 fixed `_inject_schema_contract_columns` to add the inferred `chain` to the DataFrame when missing.

**Root cause 4: GCS 429 on per-VM manifest parquet**

The per-VM manifest file (`_index/per_vm/{vm}.parquet`) was hit by hundreds of concurrent writes (8 workers × 300+
shards × 7 timeframes per date, all calling `manifest_writer.flush()` per shard). GCS rate-limits object mutations to
~1/sec per object → 429 on every manifest write for failed shards.

### Fixes shipped (2026-05-24 ~09:xx UTC)

| Repo | Commit   | Change                                                                                                    |
| ---- | -------- | --------------------------------------------------------------------------------------------------------- |
| MDPS | 6fe0f01  | `canonical_writer.py`: inject inferred chain column into candle DataFrame before validator                |
| MDPS | 8d4639f  | `canonical_writer.py`: use `asset_group=` not `category=` in partition_path                               |
| MDPS | 555ade1  | `canonical_writer.py`: strip chain suffix from DeFi venue in partition_path (`_strip_chain_from_venue()`) |
| UAC  | 954ff6d3 | `registry`: remove stale `rate_indices` alias from processed_data_dependencies                            |

**VM 083200 outcome**: both VMs TERMINATED ~15 min after start (07:48 UTC). 2024 VM processed 128 of 366 dates
(completed Jan 1 – May 7, failed on May 8+ with new-format instrument_ids). 2025 VM processed 4 of 365 dates. The candle
parquets for successful dates ARE in GCS. Failed dates will be retried on relaunch.

## Second schema gap — found from 215530 VM (SCHEMA_VALIDATION_FAILED)

The 215530 MDPS VMs (relaunched after POOL→pool fix) produced zero captured rows with `SCHEMA_VALIDATION_FAILED` on
**all** `swaps_ohlcv_*` shards. Three root causes from run.log investigation:

### Root cause 1: Missing `chain`/`swap_count`/`volume_quote_usd` columns

`DefiSwapAdapter.process_to_candles()` returned `CandleOutput` without `chain`, `swap_count`, `volume_quote_usd`. The
UAC `(defi, pool, swaps_ohlcv_*)` contract requires all three (chain: non-nullable; swap_count/volume_quote_usd:
nullable). `CandleOutput.to_dataframe()` produced a DataFrame missing these columns → `missing_column` violations.

### Root cause 2: No `swaps_ohlcv_4h` contract

`_TIMEFRAMES_DEFI` was `("15s", "1m", "5m", "15m", "1h", "1d")` — no `4h`. MDPS generates 4h candles for DeFi but no
contract existed → `SchemaContractNotFoundError: swaps_ohlcv_4h`.

### Root cause 3 (manifest only): `_infer_chain()` returns "" for 3-part instrument IDs

`UNISWAP_V3:POOL:0x...` is 3-part — `_infer_chain()` needed a fallback to parse chain from venue canonical form.
`canonical_writer.py` was updated to also extract chain from `UNISWAP_V3-ETHEREUM` → `ETHEREUM`.

### Fixes shipped (2026-05-23 ~22:xx UTC)

| Repo | Commit   | Change                                                                                                                                                                                  |
| ---- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UAC  | c8c93328 | `_candle_contracts.py`: add `"4h"` to `_TIMEFRAMES_DEFI`; `adapter_models.py`: add `chain`, `swap_count`, `volume_quote_usd` to `CandleOutput`                                          |
| MDPS | 7f1a5b5  | `swap_adapter.py`: extract `chain` from tick data `chain` column; set `swap_count`=trade_count, `volume_quote_usd`=USD volume; `canonical_writer.py`: improve `_infer_chain()` fallback |
| UTL  | a56c22c6 | `freshness_monitor.py`: rename `asset_class` → `asset_group` (pre-existing MDPS test failure)                                                                                           |

## Third schema gap — found 2026-05-24 (chain column absent from DataFrame)

083200 VMs (cb3d11b tarball) still produced 0 captured rows — all `SCHEMA_VALIDATION_FAILED`.

**Root cause**: `_infer_chain()` correctly infers `"ETHEREUM"` from `UNISWAP_V2-ETHEREUM` venue token and uses it in
`partition_path=.../chain=ETHEREUM`. BUT `_inject_schema_contract_columns()` did not inject the `chain` column into
`candles_df` before calling `_utl_write_chunk`. The adapter sets `chain_arr=None` for legacy UNISWAP_V2 ticks (no
explicit `chain` column in raw tick data) → `CandleOutput.to_dataframe()` drops it → UTL partition consistency validator
raised `SCHEMA_VALIDATION_FAILED`.

**Fix shipped**: MDPS@6fe0f01 — extend `_inject_schema_contract_columns(chain: str = "")` to backfill the column when
absent; add `chain: str = ""` field to `CandleStreamingWriteContext`; both callers updated.

## Fourth schema gap — found 2026-05-24 (venue mismatch in partition_path)

085204 VMs (6fe0f01 tarball) still produced 0 captured rows — all `SCHEMA_VALIDATION_FAILED`.

**Root cause**: `partition_path` used `venue=UNISWAP_V2-ETHEREUM` (full token with chain suffix). UTL's partition
consistency validator derives the venue from each row's instrument_id by stripping the chain suffix
(`UNISWAP_V2-ETHEREUM` → `UNISWAP_V2`). Chain is already captured separately as `chain=ETHEREUM` partition key. Mismatch
→ `SCHEMA_VALIDATION_FAILED` on every DeFi pool shard.

Also: incoming commit `8d4639f` changed `category=` → `asset_group=` in partition_path — merged into this fix.

**Fix shipped**: MDPS@555ade1 — add `_strip_chain_from_venue(venue, chain)` helper; guard with
`asset_group == MarketAssetGroup.DEFI` so CeFi venues like `BINANCE-FUTURES` are untouched; both `write_candle_parquet`
and `open_candle_streaming_writer` updated for both `partition_path` and `row_key["venue"]`. QG green (2 pre-existing
failures unchanged, 0 new). Basedpyright 0 errors.

## Status

- 2026-05-23 ~21:xx UTC — POOL→pool fix shipped at UAC@8e1e7e58. 195633 VMs stale tarball.
- 2026-05-23 ~22:xx UTC — chain/swap_count/volume_quote_usd + 4h fix shipped: UAC@c8c93328 + MDPS@7f1a5b5 +
  UTL@a56c22c6. 215530 VMs also failed (stale tarball).
- 2026-05-24 ~08:25 UTC — Tarballs rebuilt (UAC@8cb9036f + UTL@ad99ec7a + MDPS@cb3d11b). All 11 fixes included.
- 2026-05-24 ~08:32 UTC — 083200 VMs launched (2024+2025 only) — still failed (chain column bug).
- 2026-05-24 ~08:44 UTC — MDPS@6fe0f01 chain column injection fix shipped. QG green (0 type errors).
- 2026-05-24 ~08:47 UTC — Tarballs rebuilt with DEFI asset group (MDPS@6fe0f01 included). 083200 VMs stopped.
- 2026-05-24 ~08:52 UTC — **5 VMs relaunched** (run-ts=20260524-085204, ALL years) — failed (venue mismatch bug).
- 2026-05-24 ~09:08 UTC — MDPS@555ade1 venue mismatch fix shipped. QG green (2 pre-existing, 0 new). 085204 VMs stopped.
- 2026-05-24 ~09:09 UTC — Tarballs rebuilt (MDPS@555ade1 + asset_group= fix included).
- 2026-05-24 ~09:14 UTC — **5 VMs relaunched** (run-ts=20260524-091405, ALL years):
  - `mdps-defi-2022-20260524-091405` → 2022-11-01..2022-12-31 RUNNING ✓
  - `mdps-defi-2023-20260524-091405` → 2023-01-01..2023-12-31 RUNNING ✓
  - `mdps-defi-2024-20260524-091405` → 2024-01-01..2024-12-31 RUNNING ✓
  - `mdps-defi-2025-20260524-091405` → 2025-01-01..2025-12-31 RUNNING ✓
  - `mdps-defi-2026-20260524-091405` → 2026-01-01..2026-05-24 RUNNING ✓
- 2026-05-24 ~09:30 UTC — **VERIFIED**: 2025 per-VM shard shows 27 `captured` rows (UNISWAP_V3-ETHEREUM pools),
  venue=`UNISWAP_V3` (chain suffix stripped ✓), chain=`ETHEREUM` ✓. Zero `SCHEMA_VALIDATION_FAILED`. All 5 VMs running.
- 2026-05-24 ~09:22 UTC — 091405 VMs hit GCS 429 on per-VM manifest parquet (8 workers × 322 shards × 7 timeframes
  flooding `_index/per_vm/*.parquet`). Candle parquets written OK; manifest rows dropped for rate-limited writes. VMs
  terminated after completing. 092158 batch relaunched (ALL years) to cover remaining dates + retry 429-dropped rows.
- 2026-05-24 ~09:22 UTC — **5 VMs relaunched** (run-ts=20260524-092158, ALL years) — RUNNING (startup, no log dirs yet).

## Plan refs

`plans/epics/mtds_mdps_master.md` — MDPS-3.3.DeFi-V verify gate
