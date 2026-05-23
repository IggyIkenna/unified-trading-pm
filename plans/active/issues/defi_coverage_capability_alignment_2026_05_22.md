---
title: DeFi expected_coverage VENUE-CHAIN phantom entries + handler naming inconsistency
created: 2026-05-22
source:
  - data-status UI audit 2026-05-22
  - expected_coverage.py code review
locked_by: live-defi-rollout
parent_epic: epics/infrastructure_master.md
assigned_vm: planning-vm
priority: P2
status: active
---

## What I found

### Bug 1 (FIXED 2026-05-22): All DEX/lending entries in `_DEFI` were phantom

`expected_coverage.py` `_DEFI` used `VENUE-CHAIN` format keys (`"UNISWAP_V3-ETHEREUM"`, `"AAVE_V3-ETHEREUM"`, etc.) but
`is_expected()` does a plain `ag_scope.get(venue, [])` lookup using the raw `venue` field from the manifest.

Current handlers write `venue=protocol.upper()` with chain as a SEPARATE manifest field:

- `dex_pools_handler` / `dex_swaps_handler`: `"uniswap_v3".upper()` = `"UNISWAP_V3"` + `chain="ETHEREUM"`
- `evm_defi_handler`: `"aave_v3".upper()` = `"AAVE_V3"` + `chain="ETHEREUM"`

So `is_expected("defi", "UNISWAP_V3", "dex_pools")` → `_DEFI.get("UNISWAP_V3", [])` → `[]` → not expected. The
`"UNISWAP_V3-ETHEREUM"` key in `_DEFI` only matches if `venue="UNISWAP_V3-ETHEREUM"` in the manifest, which no handler
writes.

**Impact**: ALL DEX and lending shard counts were missing from the denominator. The 88.5% DeFi coverage score was
computed excluding all UNISWAP_V3, AAVE_V3, COMPOUND_V3, MORPHO, BALANCER, CURVE etc. shards.

**Fix shipped**: UAC@3d43382b — replaced all VENUE-CHAIN format entries with flat venue names matching actual handler
output. Both legacy VENUE-CHAIN format entries (e.g. `"UNISWAP_V3-ETHEREUM"`) AND flat format entries (e.g.
`"UNISWAP_V3"`) now coexist in `_DEFI` to cover migrated rows until a phantom reconciler pass removes era-2 names.

### Bug 2 (OPEN): Handler venue naming inconsistency — `AAVE_V3` vs `AAVE_V3`

Different handlers write different venue names for Aave V3:

- `evm_defi_handler.py` (lending_indices, position_data EVM path): `"aave_v3".upper()` = `"AAVE_V3"` (underscore)
- `flash_loan_events_handler.py`: hardcoded `venue="AAVE_V3"` (no underscore)
- `position_data_handler.py`: hardcoded `venue="AAVE_V3"` (no underscore)
- `liquidations_handler.py`: uses `protocol.upper()` where protocol may be `"aavev3"` → `"AAVE_V3"`

This creates two distinct venue rows in the manifest for the same protocol. Both `AAVE_V3` and `AAVE_V3` appear as
separate venues in the data-status UI.

**Workaround in place**: Both `"AAVE_V3"` and `"AAVE_V3"` added to `expected_coverage._DEFI`.

**Required fix**: Normalise all Aave handlers to `venue="AAVE_V3"` (underscore, matching evm_defi_handler convention).
File: `flash_loan_events_handler.py`, `position_data_handler.py`, `liquidations_handler.py`.

### Bug 3 (OPEN): Ghost venue entries in manifest from old naming eras

GCS manifest parquets contain rows from 3+ naming convention eras:

- Era 1 (oldest): `venue="UNISWAP_V3"` (underscore, pre-capabilities)
- Era 2: `venue="UNISWAP_V3"` (no underscore, capabilities-era)
- Era 3 (current): `venue="UNISWAP_V3"` (underscore, back to era 1 via `protocol.upper()`)

Same pattern for AAVE_V3/AAVE_V3, COMPOUND_V3/COMPOUND_V3, MORPHOVAULTS/MORPHO_VAULTS, etc.

Ghost entries (UNISWAP_V2, UNISWAP_V3, COMPOUND_V3, AAVE_V3 from era-2 handlers) show in the UI as venues with no data
bar.

**UPDATED 2026-05-22 schema audit findings (schema check complete)**:

Consolidated manifest ghost rows vs canonical per-VM shard rows (audited 2026-05-22):

| Venue          | Consolidated manifest                        | Per-VM shard (local-10889) | GCS canonical parquets                            |
| -------------- | -------------------------------------------- | -------------------------- | ------------------------------------------------- |
| `UNISWAP_V3`   | 187,769 rows captured, 2024-05-06→2026-01-23 | —                          | at `venue=UNISWAP_V3-ETHEREUM/` (VENUE-CHAIN)     |
| `UNISWAP_V3`   | **0 rows**                                   | 187,769 rows captured      | ✅ EXIST at canonical split path, full date range |
| `UNISWAP_V2`   | 22,168 rows captured, 2024-05-03→2026-01-24  | —                          | at `venue=UNISWAP_V2-ETHEREUM/` (VENUE-CHAIN)     |
| `UNISWAP_V2`   | **0 rows**                                   | 20,254 rows captured       | ✅ EXIST at canonical split path, full date range |
| `AAVE_V3`      | 29,782 rows captured, 2024-05-02→2026-01-23  | —                          | at `venue=AAVE_V3-ETHEREUM/` (VENUE-CHAIN)        |
| `AAVE_V3`      | **0 rows**                                   | 27,482 rows captured       | ✅ EXIST at canonical split path, full date range |
| `MORPHOVAULTS` | 2,325 rows mixed, 2020→2026-05-18            | —                          | not audited                                       |
| `YEARN_V3`     | 2,324 rows mixed, 2020→2026-05-18            | —                          | not audited                                       |

**Root cause — NOT a GCS migration problem**: Canonical GCS parquets already exist at canonical split paths for ALL
ghost date ranges. The fix is manifest-only. The consolidator's **incremental merge skips `local-10889-bd08.parquet`**
(written 2026-05-03) because it predates the current consolidated index (updated 2026-05-22 03:44 UTC). Canonical per-VM
shard rows sit unreachable.

**Schema comparison (UNISWAP_V3-ETHEREUM parquet vs UNISWAP_V3 canonical parquet)**:

- Old (30 cols): in-file `data_type='swaps'/'liquidity'`, missing `instrument_id`, `chain`, `instrument_type`
- Canonical (33 cols): in-file `data_type='dex_pool_state'`, has all three extra columns
- **For AAVE_V3**: manifest data_types match between ghost and canonical rows: `oracle_prices`, `rate_indices`,
  `risk_params`, `utilization` — GCS confirms these data_types exist at canonical `AAVE_V3/` path

**Why phantom reconciler still won't work**: Ghost consolidated manifest rows say `venue=UNISWAP_V3 chain=ETHEREUM` →
reconciler probes `venue=UNISWAP_V3/chain=ETHEREUM/` path → MISS (parquets at `UNISWAP_V3-ETHEREUM/`). Would incorrectly
flip to `attempted_failed`.

**Required fix — manifest-only (no GCS migration needed)**:

1. Re-upload `_index/per_vm/local-10889-bd08.parquet` as a new dated corrector shard (e.g.
   `ikenna-slot1-canonical-defi-20260522.parquet`) so consolidator incremental merge picks it up. Adds UNISWAP_V3
   (187k), UNISWAP_V2 (20k), AAVE_V3 (27k), UNISWAP_V4 (6.5k) rows to consolidated manifest.
2. In the same corrector shard: write superseding rows for ghost venues (UNISWAP_V3, UNISWAP_V2, AAVE_V3) with newer
   `attempted_at` timestamp and `capture_status='empty_confirmed'` + valid `EmptyConfirmedReason`. Consolidator
   last-write-wins on `(date, venue, data_type, ...)` key — ghost rows get overridden.
3. Verify `EmptyConfirmedReason` enum has a suitable reason for venue-renamed rows (check UAC
   `canonical.crosscutting.honest_coverage.EmptyConfirmedReason`). If not, add one.
4. Run manifest consolidator to pick up the new shard.
5. Old parquets at VENUE-CHAIN paths (`UNISWAP_V3-ETHEREUM/`) can remain — canonical split-path parquets already have
   the same data with correct 33-column schema.

### Bug 4 (OPEN): LST venue name `ANKR` confusingly displayed

ANKR in the DeFi data-status is the **Ankr Staking Protocol** (ankrETH LST), NOT an RPC provider. The LST handler maps
`ankrETH → "ankr" → "ANKR"` and writes `data_type="lst_rates"`. It appears alphabetically between AAVE_V3 and BALANCER
under the ETHEREUM chain, making it look like a sub-item of AAVE_V3.

No functional bug — coverage is correct (99.9%). The confusion is a UI grouping issue: LST protocol venues (ANKR,
ROCKETPOOL, STADER etc.) are intermixed with DeFi protocol venues (AAVE_V3, UNISWAP_V3) in the same list. A
`data_source_type` taxonomy would separate them.

Tracked as follow-on: `defi_coverage_capability_alignment_2026_05_22.md` (this doc) — extend with `data_source_type`
enum.

## Why it matters

- Missing shard counts from denominator → overall DeFi coverage % misleadingly high (excludes all DEX/lending volume)
- Operator cannot trust the 88.5% figure until Bug 2+3 are resolved
- New agents reading expected_coverage will get wrong denominator unless Bugs 2+3 are fixed

## Recommended decision

- [x] Bug 1: FIXED — UAC@3d43382b (2026-05-22)
- [x] Bug 2: ✅ FULLY FIXED — MTDS@d6862ca2 (2026-05-23). `_DEFAULT_PROTOCOLS = ["aave_v3", ...]` uses underscore, so
      `protocol.upper() = "AAVE_V3"` (canonical). All 3 handlers verified: no `AAVEV3` (no-underscore) string anywhere
      in MTDS handlers. Workspace-wide rename + handler-level fix both complete.
- [x] Bug 3: ✅ FULLY SUPPRESSED — IS@dbf7bf6 + IS@5a709c4 (2026-05-22). MTDS (dbf7bf6): UNISWAP_V3/V2/AAVE_V3 →
      empty_confirmed. Canonical rows UNISWAP_V3(187k)/UNISWAP_V2(22k)/AAVE_V3(30k) restored. IS DeFi (5a709c4): 31,709
      rows suppressed — AAVE_V3(9252), UNISWAP_V3(7641), COMPOUND_V3(4087), PANCAKESWAP_V3(3141), SUSHISWAP_V3(2962),
      UNISWAP_V2(2146), CAMELOT_V3(1036), VELODROMEV2(1007), UNISWAP_V4(437). MTDS residual (5a709c4): 20,102 rows
      suppressed — UNISWAP_V4(15093), YEARN_V3(2360), MORPHOVAULTS(2325), others(396). All shards merged by consolidator
      within 1 min of upload.
- [ ] Bug 4: Post-cutover — add `data_source_type` taxonomy enum.

### Related fixes shipped 2026-05-23 (deployment-api)

- [x] `_is_legacy_defi_venue_row` regex fixed — deployment-api@ce554bc. Regex `r"V\d+$"` → `r"_?V\d+$"` so canonical
      `AAVE_V3-ETHEREUM` (venue=`AAVE_V3`, chain=`ETHEREUM`) correctly detected as legacy row, not missed.
- [x] `_mtds_shard_path` `asset_group=` fallback — deployment-api@9b8e9ad. Tries canonical `asset_group={cat}` hive key
      first, falls back to `category={cat}` for pre-migration parquets. GCS audit 2026-05-23 confirms fallback IS still
      needed: Sports prd all `category=sports/`; CEFI has `category=` orphans on days 2019-12-01→2026-04-30 (migration
      wrote `asset_group=` copies but never deleted originals; DeFi is clean).

### GCS partition key audit (2026-05-23)

| Asset group   | Active partition key | `category=` still on disk?                                                           |
| ------------- | -------------------- | ------------------------------------------------------------------------------------ |
| DeFi prd/flat | `asset_group=defi/`  | No — fully migrated                                                                  |
| CEFI prd/flat | `asset_group=cefi/`  | Yes — orphans (deletion running 2026-05-23; 2019-03-31 gap pre-filled before delete) |
| Sports prd    | `category=sports/`   | Yes — all days; migration never ran                                                  |
| TradFi        | `pipeline_mode=`     | N/A — different first-level key                                                      |
| Prediction    | `asset_group=`       | No                                                                                   |

CEFI `category=` orphans are redundant dead data (canonical `asset_group=` copies cover 100% of days).

**CEFI prd cleanup (2026-05-23)**: Before deletion, 2019-03-31 was the only day with `category=cefi/` but NO
`asset_group=cefi/` — 6 objects/11 MiB copied to canonical path first. Then `gsutil -m rm -r ".../day=*/category=cefi"`
started (confirmed running 2026-05-23). Awaiting completion.

**AWS bucket audit (2026-05-23)**: `market-data-tick-cefi-prd-427895769566` and
`market-data-tick-sports-prd-427895769566` are EMPTY — no objects on AWS. All CEFI and Sports MTDS data is GCP-only. No
AWS migration needed.

**Sports `category=sports/` migration**: active plan at `plans/active/sports_gcs_partition_rekey_2026_05_23.md`
(parent_epic=sports_master). Blocked pending Sports VM drain (VMs actively running 2026-05-23).

## Temporary states + their canonical follow-up plans

- `"AAVE_V3"` in expected_coverage: stays until Bug 2 handler fix ships + phantom reconciler runs for Bug 3.
