---
title: DeFi expected_coverage VENUE-CHAIN phantom entries + handler naming inconsistency
created: 2026-05-22
author: slot-1-main
source:
  - data-status UI audit 2026-05-22
  - expected_coverage.py code review
locked_by: live-defi-rollout
parent_epic: epics/infrastructure_master.md
assigned_vm: planning-vm
---

## What I found

### Bug 1 (FIXED 2026-05-22): All DEX/lending entries in `_DEFI` were phantom

`expected_coverage.py` `_DEFI` used `VENUE-CHAIN` format keys (`"UNISWAPV3-ETHEREUM"`, `"AAVEV3-ETHEREUM"`, etc.) but
`is_expected()` does a plain `ag_scope.get(venue, [])` lookup using the raw `venue` field from the manifest.

Current handlers write `venue=protocol.upper()` with chain as a SEPARATE manifest field:

- `dex_pools_handler` / `dex_swaps_handler`: `"uniswap_v3".upper()` = `"UNISWAP_V3"` + `chain="ETHEREUM"`
- `evm_defi_handler`: `"aave_v3".upper()` = `"AAVE_V3"` + `chain="ETHEREUM"`

So `is_expected("defi", "UNISWAP_V3", "dex_pools")` → `_DEFI.get("UNISWAP_V3", [])` → `[]` → not expected. The
`"UNISWAPV3-ETHEREUM"` key in `_DEFI` only matches if `venue="UNISWAPV3-ETHEREUM"` in the manifest, which no handler
writes.

**Impact**: ALL DEX and lending shard counts were missing from the denominator. The 88.5% DeFi coverage score was
computed excluding all UNISWAP_V3, AAVE_V3, COMPOUND_V3, MORPHO, BALANCER, CURVE etc. shards.

**Fix shipped**: UAC@<sha-pending> — replaced all VENUE-CHAIN format entries with flat venue names matching actual
handler output.

### Bug 2 (OPEN): Handler venue naming inconsistency — `AAVE_V3` vs `AAVEV3`

Different handlers write different venue names for Aave V3:

- `evm_defi_handler.py` (lending_indices, position_data EVM path): `"aave_v3".upper()` = `"AAVE_V3"` (underscore)
- `flash_loan_events_handler.py`: hardcoded `venue="AAVEV3"` (no underscore)
- `position_data_handler.py`: hardcoded `venue="AAVEV3"` (no underscore)
- `liquidations_handler.py`: uses `protocol.upper()` where protocol may be `"aavev3"` → `"AAVEV3"`

This creates two distinct venue rows in the manifest for the same protocol. Both `AAVE_V3` and `AAVEV3` appear as
separate venues in the data-status UI.

**Workaround in place**: Both `"AAVE_V3"` and `"AAVEV3"` added to `expected_coverage._DEFI`.

**Required fix**: Normalise all Aave handlers to `venue="AAVE_V3"` (underscore, matching evm_defi_handler convention).
File: `flash_loan_events_handler.py`, `position_data_handler.py`, `liquidations_handler.py`.

### Bug 3 (OPEN): Ghost venue entries in manifest from old naming eras

GCS manifest parquets contain rows from 3+ naming convention eras:

- Era 1 (oldest): `venue="UNISWAP_V3"` (underscore, pre-capabilities)
- Era 2: `venue="UNISWAPV3"` (no underscore, capabilities-era)
- Era 3 (current): `venue="UNISWAP_V3"` (underscore, back to era 1 via `protocol.upper()`)

Same pattern for AAVEV3/AAVE_V3, COMPOUNDV3/COMPOUND_V3, MORPHOVAULTS/MORPHO_VAULTS, etc.

Ghost entries (UNISWAPV2, UNISWAPV3, COMPOUNDV3, AAVEV3 from era-2 handlers) show in the UI as venues with no data bar.
They won't disappear until:

1. A manifest phantom reconciler runs to delete/remap them, OR
2. Manifest TTL expires the old rows (if TTL is configured)

**Required fix**: Run `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi` to
identify and remove era-2 ghost rows.

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

- [x] Bug 1: FIXED — see UAC@<sha-pending>
- [ ] Bug 2: Normalise AAVEV3 → AAVE_V3 in flash_loan_events_handler + position_data_handler + liquidations_handler.
      Assign to MTDS slot.
- [ ] Bug 3: Run phantom reconciler for defi asset_group. Assign to MDPS/IS slot.
- [ ] Bug 4: Post-cutover — add `data_source_type` taxonomy enum.

## Temporary states + their canonical follow-up plans

- `"AAVEV3"` in expected_coverage: stays until Bug 2 handler fix ships + phantom reconciler runs for Bug 3.
