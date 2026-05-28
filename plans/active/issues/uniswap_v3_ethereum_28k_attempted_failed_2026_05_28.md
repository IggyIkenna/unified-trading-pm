---
title:
  "MTDS DeFi manifest: 28,634 UNISWAP_V3-ETHEREUM swaps_ohlcv attempted_failed rows — all SCHEMA_VALIDATION_FAILED, fix
  already shipped (chain propagation + amount_usd column), needs retry pass not new code"
created: 2026-05-28
author: slot-1
source:
  - gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet
  - market-data-processing-service@7f1a5b5 (2026-05-23 22:49 BST — chain propagation fix)
  - market-data-processing-service@3799c8d (2026-05-24 16:45 BST — amount_usd column support)
locked_by: live-defi-rollout
parent_epic: plans/epics/infrastructure_master.md
status: OPEN — needs retry pass (no new code required)
priority: P2
---

## What I found

MTDS DeFi availability manifest (`gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet`)
contains **28,634 attempted_failed rows** keyed `venue=UNISWAP_V3-ETHEREUM` (pre-B5 glued form — chain segment carried
in venue column, separate `chain` column blank).

### Failure-axis breakdown (100% saturation, no other failure modes mixed in)

- **error_reason**: 100% `SCHEMA_VALIDATION_FAILED` (28,634 / 28,634)
- **service_name**: 100% `market-data-processing-service` (MDPS, not MTDS upstream)
- **schema_version**: 100% v8
- **data_type**: distributed across all 7 swaps OHLCV timeframes — `swaps_ohlcv_15s` 4,942 · `swaps_ohlcv_1m` 4,540 ·
  `swaps_ohlcv_5m` 4,358 · `swaps_ohlcv_15m` 4,291 · `swaps_ohlcv_1h` 4,191 · `swaps_ohlcv_1d` 3,170 · `swaps_ohlcv_4h`
  3,142
- **date range** (`date` column): 2024-05-06 → 2026-01-17
- **attempted_at**: 2026-05-23 20:59:43 UTC → 2026-05-24 13:05:41 UTC (a single ~16-hour MDPS backfill sweep)

### Diagnostic on a sample failed row

```
venue:             UNISWAP_V3-ETHEREUM
data_type:         swaps_ohlcv_15m
instrument_type:   POOL
instrument_id:     UNISWAP_V3-ETHEREUM:POOL:0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa
chain:             ''                  ← blank, despite UAC contract `nullable=False`
asset_group:       None
schema_version:    8
service_name:      market-data-processing-service
error_reason:      SCHEMA_VALIDATION_FAILED
```

## Why it matters

UAC internal contract `_CHAIN = ColumnSpec(name="chain", dtype="string", nullable=False)` in
`unified_api_contracts/internal/schemas/contracts.py:193`. MDPS DEX swaps adapter
(`market_data_processing_service/app/adapters/defi/swap_adapter.py:212-217`) reads `chain` from the input tick frame:

```python
chain_value = ""
if "chain" in tick_data.columns and len(tick_data) > 0:
    raw_chain = cast(object, tick_data["chain"].iloc[0])
    if isinstance(raw_chain, str) and raw_chain:
        chain_value = raw_chain.upper()
chain_arr: object = np.full(n_valid, chain_value, dtype=object) if chain_value else None
```

Empty `chain_value` → `chain_arr = None` → output candle frame has no `chain` column → schema enforcer rejects with
non-nullable violation → `record_failed_for_shard(error="SCHEMA_VALIDATION_FAILED")`.

## Root-cause diagnosis — fix already shipped

The fix landed in **two commits on 2026-05-23 / 2026-05-24** — AFTER the 28,634 failed attempts but BEFORE today's date:

| sha       | date                 | message                                                                           |
| --------- | -------------------- | --------------------------------------------------------------------------------- |
| `7f1a5b5` | 2026-05-23 22:49 BST | fix(defi): populate chain/swap_count/volume_quote_usd in DefiSwapAdapter output   |
| `23d4cf9` | 2026-05-23 23:xx BST | fix(defi): populate swap_count/volume_quote_usd and pass chain through to candles |
| `3799c8d` | 2026-05-24 16:45 BST | fix(defi): handle amount_usd column from new prd-bucket dex_swaps parquets        |

The 28,634 failures attempted_at 2026-05-23T20:59 → 2026-05-24T13:05 UTC straddle the fix-deploy window: most rows
attempted BEFORE `7f1a5b5` landed; a tail attempted between `7f1a5b5` and `3799c8d`.

**Conclusion**: no new code is required. The failed rows are stale — a retry of the same MTDS→MDPS pipeline against the
fixed `swap_adapter` should write candles successfully.

## Recommended decision

1. **No code fix required.** `7f1a5b5` + `3799c8d` are already on `live-defi-rollout`.
2. **Retry pass needed** on UNISWAP_V3-ETHEREUM swaps_ohlcv for the 2024-05-06 → 2026-01-17 date range covered by the
   28,634 attempted_failed rows. Two paths:
   - **Path A (preferred)**: launch a focused MDPS reprocess VM (`mtds-backfill-defi-...` or MDPS-specific launcher if
     one exists) scoped to `venue=UNISWAP_V3` + `chain=ETHEREUM` (canonical B5 form) for the swaps_ohlcv data types
     across the failed date range. Manifest skip-if-exists will only re-touch the attempted_failed rows.
   - **Path B (folded into Task 2)**: the MTDS EVM forward-fill VM launched 2026-05-28
     (`mtds-backfill-defi-evm-20260528`, range 2026-01-23 → 2026-05-28) does NOT cover this date range (failures are
     2024-05-06 → 2026-01-17, pre-2026-01-23). A separate **historical** retry pass is required.
3. **Pre-retry verification**: spot-check that the MTDS upstream `dex_swaps` ticks for UNISWAP_V3-ETHEREUM contain the
   `chain` column (B5 canonicalization promise). If the tick parquets DON'T have `chain`, MTDS upstream needs a separate
   handler-side fix before MDPS retry will succeed.

## Status flip path

- [ ] Verify MTDS upstream tick parquets for UNISWAP_V3-ETHEREUM 2024-05-06 → 2026-01-17 have `chain` column populated
      (Path A pre-flight)
- [ ] Launch MDPS reprocess VM for UNISWAP_V3-ETHEREUM swaps_ohlcv historical range
- [ ] Verify post-retry: `attempted_failed` count for UNISWAP_V3-ETHEREUM drops from 28,634 to 0; equivalent rows now
      `captured` (or `empty_confirmed` for legitimately empty pool-days)
- [ ] Archive this issue doc

## Cross-references

- Companion swaps_ohlcv failures (already on attempted_failed list, lower-priority):
  - UNISWAP_V2-ETHEREUM: 3,444
  - AAVEV3-OPTIMISM: 2,820 (lending indices — different adapter)
  - EIGENLAYER: 1,311 · CURVE-ETHEREUM: 1,281 · MAKER: 1,113 · FRAX: 1,032
  - DRIFT-SOLANA: 200 + KAMINO/JITO/MARGINFI: ~75
  - Each may share the same chain-column root cause; verify on first retry.
- B5 canonicalization plan: `plans/active/.../venue_axis_asset_group_vocabulary_2026_04_25.md`
- Hard schema enforcement plan: `plans/active/.../hard_schema_enforcement_2026_05_08.md`
