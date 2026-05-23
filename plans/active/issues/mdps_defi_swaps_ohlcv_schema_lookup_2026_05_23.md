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

## Status

- 2026-05-23 ~21:xx UTC — Fix shipped at UAC@8e1e7e58. In-flight 195633 VMs cannot benefit (stale tarball). Awaiting
  operator: VM completion + tarball rebuild + relaunch.

## Plan refs

`plans/epics/mtds_mdps_master.md` — MDPS-3.3.DeFi-V verify gate
