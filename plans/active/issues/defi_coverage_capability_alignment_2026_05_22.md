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
- [x] Bug 2: ✅ FULLY FIXED — MTDS@d6862ca2 (2026-05-23) + MTDS@3e48ac9b (2026-05-26). Prior fix: renamed AAVEV3 →
      AAVE_V3 across handlers. Residual fix (3e48ac9b): `liquidations_handler.py` manifest
      `record_captured/empty/failed` called `venue=protocol` (lowercase "aave_v3") instead of `venue=protocol.upper()`,
      diverging from GCS path and freshness-cache row_key which both used `.upper()`. Now all three manifest recording
      calls use `protocol.upper()`.
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

| Asset group   | Active partition key | `category=` still on disk?                                                      |
| ------------- | -------------------- | ------------------------------------------------------------------------------- |
| DeFi prd/flat | `asset_group=defi/`  | No — fully migrated                                                             |
| CEFI prd/flat | `asset_group=cefi/`  | **No — 336,800 objects deleted 2026-05-23** (spot-checked: 5 random days clean) |
| Sports prd    | `category=sports/`   | Yes — all days; migration never ran                                             |
| TradFi        | `pipeline_mode=`     | N/A — different first-level key                                                 |
| Prediction    | `asset_group=`       | No                                                                              |

CEFI `category=` orphans are redundant dead data (canonical `asset_group=` copies cover 100% of days).

**CEFI prd cleanup (2026-05-23) ✅ COMPLETE**: `gsutil -m rm -r ".../day=*/category=cefi"` deleted **336,800 objects**
(exit 0). Spot-check verified 5 random days (2020-06-15, 2021-11-30, 2023-04-01, 2024-08-15, 2026-01-10): all return
CommandException for `category=cefi/` and have 7-14 `asset_group=cefi/` objects intact.

Pre-deletion note (2019-03-31): only day with `category=cefi/` but no `asset_group=cefi/`. 6 DERIBIT objects/11 MiB were
copied before deletion. The copy landed at `asset_group=cefi/category=cefi/venue=DERIBIT/` (nested path, not flat
canonical). Original `category=cefi/` is gone. Non-canonical path is acceptable for 2019 historical data with no active
consumers — no corrective action needed.

**AWS bucket audit (2026-05-23)**: `market-data-tick-cefi-prd-427895769566` and
`market-data-tick-sports-prd-427895769566` are EMPTY — no objects on AWS. All CEFI and Sports MTDS data is GCP-only. No
AWS migration needed.

**Sports `category=sports/` migration**: active plan at `plans/active/sports_gcs_partition_rekey_2026_05_23.md`
(parent_epic=sports_master). Blocked pending Sports VM drain (VMs actively running 2026-05-23).

## 2026-05-25 data-quality audit cross-reference (DQ-02 / DQ-04)

The cross-cutting data-quality audit (`audits/data_quality_backfill_status_audit_instructions.md`) re-confirmed two
findings that belong here, not as parallel issues:

- **DQ-04 (contamination → Bug 4)**: Ikenna's review found the ETH "42 protocols" count inflated by (a) legacy
  camelCase↔underscore alias dupes (= Bug 3, mostly suppressed) and (b) non-protocol entries: `COINBASE-SPOT` (a CeFi
  oracle source leaking into the DeFi grid via `oracle-prices-{pid}` — handler-level filter gap), `ALCHEMY`/`ANKR` (RPC
  providers — though `ANKR` is also the ankrETH LST per Bug 4), `GAS_FEES` (a data_type). Note: `ALCHEMY`/`CHAINLINK`/
  `PYTH` ARE intentional data-source entries in `expected_coverage._DEFI` (provider-level, comment lines 274-278) — the
  "inflation" is the missing `data_source_type` taxonomy (**Bug 4**, post-cutover), not scope contamination. The
  `COINBASE-SPOT`-into-defi-grid leak is the one genuinely-new sub-finding → close the `oracle_prices_handler` filter so
  CeFi oracle sources don't write defi-grid rows (fold into Bug 4 / a handler fix).
- **DQ-02 (LST capture)**: the LST venues (LIDO/ROCKETPOOL/COINBASE-cbETH/JITO/MARINADE/ETHERFI/…) ARE correctly scoped
  in `_DEFI` — not mis-enumerated against Aave. The `lst_rates`/`lending_indices`/`perp_funding` `attempted_failed` rows
  are OLD (2022→2025-01) **Solana** protocol rows (Jito/Marinade/Kamino/Marginfi/Solend/Drift) carrying
  `error_reason=legacy_bare_name_migrated_to_protocol_solana_2026_05_14` + `LegacyBlankErrorReasonError` = manifest
  hygiene (same era as Bug 3) → fix via `reconcile_legacy_blank_to_typed_reason`. The empties elsewhere are legitimate
  honest-absence (`EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_INSTRUMENT_NOT_LISTED`). Residual to verify: that LST
  staking-APR is actually captured for the real LST venues (currently 0 captured for `lst_rates`/`staking_yields`).

## Bug 5 (OPEN — surfaced 2026-05-26 via deployment-ui pool-breakdown): IS parquet PATH still glued while manifest venue is canonical

**Provenance**: operator drilled `Pool breakdown · AAVE_V3-ARBITRUM · 2026-05-03` in deployment-ui → "No pool data".

**Precise divergence** (instruments-store-defi, verified 2026-05-26):

- **Manifest is canonical**: `availability_index` has `venue=AAVE_V3`, `chain=ARBITRUM`, `capture_status=captured`, 8
  rows for 2026-05-03. ✅ (Bug 2 fix canonicalised the `manifest.record_captured(venue=manifest_venue)` call.)
- **Parquet PATH is still glued**: the actual reference data is at
  `instrument_availability/by_date/day=2026-05-03/venue=AAVEV3-ARBITRUM/instruments.parquet` (no underscore). There is
  **no** canonical `venue=AAVE_V3-ARBITRUM/` (combined) nor `venue=AAVE_V3/chain=ARBITRUM/` (split) parquet for this
  date.
- **Root cause**: `instruments-service/instruments_service/engine/orchestrator.py:3155` builds the parquet path from
  `venue_str` (raw glued protocol-chain) while the manifest call (line 3149) uses `manifest_venue` (canonical,
  underscore). Bug 2 canonicalised the manifest venue but NOT the parquet partition key → they diverged. deployment-ui
  pool-breakdown reads the canonical manifest venue → derives canonical path → misses the glued-path parquet → "No pool
  data".

**Scope — ALL version-suffixed DeFi venues** (operator 2026-05-26: "AAVE_V3-ARBITRUM is canonical … same with other
venues for defi"). Glued GCS keys needing underscore insertion before the version: `AAVEV3→AAVE_V3`,
`COMPOUNDV3→COMPOUND_V3`, `CAMELOTV3→CAMELOT_V3`, `AERODROMEV3→AERODROME_V3`, `PANCAKESWAPV3→PANCAKESWAP_V3`,
`SUSHISWAPV3→SUSHISWAP_V3`, `UNISWAPV2/V3/V4→UNISWAP_V2/V3/V4`, `VELODROMEV2→VELODROME_V2`,
`TRADER_JOEV2→TRADER_JOE_V2`, `MORPHOVAULTS→MORPHO_VAULTS`. (BALANCER/CURVE/GMX/JITO/LIDO/etc. have no version → already
canonical.) Scale: **9,663 glued objects for AAVEV3 alone** in instruments-store-defi; × ~10 venue families ×
(instruments + MTDS-defi + features-onchain buckets).

**Operator directive (2026-05-26)**: migrate to canonical + DELETE the old glued keys in **gcs, manifest, deployment-ui,
UAC**. This REVERSES the Bug-3 prior decision ("Old parquets at VENUE-CHAIN paths can remain").

### Phased migration (HARD-ORDERED — writer fix MUST precede GCS re-key or it regenerates glued paths)

- [x] ✅ [CODE] P1. **B5.1 — IS writer parquet-path canonicalization (ROOT CAUSE)** — **DONE** — unified-api-contracts@fdc9206b
      + instruments-service@a57ae01c (both QG-green exit 0). Authoritative canonicalizer added to UAC:
      `unified_api_contracts.registry.capability_declarations._defi.canonicalize_defi_venue_combined(raw: str) -> str`
      (next to `parse_defi_venue`; exported in `__all__`; 7-case unit test in
      `tests/internal/test_canonicalize_defi_venue_combined.py`). It splits on the last known-chain suffix
      (`KNOWN_CHAINS`) and canonicalises the protocol via strip-underscore match against the 33-member
      `{c.venue_prefix for c in PROTOCOL_CAPABILITIES.values()}` set (verified zero strip-underscore collisions);
      unknown protocol / non-DeFi (no known chain) → passthrough. `orchestrator.py:_write_venue` now calls it (replacing
      the prior `parse_defi_venue`-based attempt, which did NOT canonicalise the glued protocol). Rewrites `venue_str`
      only when result differs AND not a sports-ref venue (existing `_sports_ref_prefixes` guard kept). This makes the
      parquet partition (line ~3094), the `venue=` arg (~3096), the manifest split (~3132–3144), and the else-branch path
      (~3178) all use the canonical combined form consistently. Pre-audit: `_write_venue` is the SOLE DeFi parquet-write
      site; `_write_futures_contracts` (~3225) is TradFi-only (CME/ICE → passthrough). Tests: UAC 7/7, IS
      `TestWriteVenueCanonicalPartition` 4/4. **NOTE (slot-master):** slot-1's `unified-api-contracts` worktree on
      `tab/ikennaigboaka/1` was 143 behind / 83 ahead of `origin/live-defi-rollout` (stale `semver-rollout[bot]`
      ghost-venue lineage `5b61be50`); rebase hit a foreign CODE conflict (`scenario_overlay.py`, `registry/__init__.py`
      @ `c0102a9f`). Worked around non-destructively by branching off `origin/live-defi-rollout`
      (`b5-defi-venue-canonicalize`) + pushing from there. The stale `tab/ikennaigboaka/1` UAC branch + its un-pushed
      commits + 4 foreign stashes are LEFT INTACT for slot-master reconciliation (all other slots' UAC worktrees are
      already at LDR HEAD ca992033 — only slot-1 is stale).
- [x] ✅ [CODE] P2. **B5.2 — UAC alias cleanup** — **DONE (no change required) — FINDING**: `LEGACY_DEFI_VENUE_ALIASES`
      targets `VELODROME_V2→VELODROMEV2-OPTIMISM`, `TRADER_JOE_V2→TRADER_JOEV2-AVALANCHE`, `MORPHO_VAULTS→MORPHOVAULTS-…`
      are **already consistent with the authoritative canonicalizer** and were LEFT AS-IS. Rationale: (1) `VELODROMEV2`
      and `TRADER_JOEV2` ARE the canonical `venue_prefix` in `PROTOCOL_CAPABILITIES` (glued, no underscore) — confirmed
      via `build_defi_venues()` (`VELODROMEV2-OPTIMISM` / `TRADER_JOEV2-AVALANCHE` are the built canonical venues), so
      glued IS canonical for these two and `canonicalize_defi_venue_combined` is a no-op on them; changing the alias
      target would CREATE divergence from the writer-path canonicalizer. (2) `MORPHOVAULTS` is NOT in
      `PROTOCOL_CAPABILITIES` at all (neither glued nor underscore) and is NOT in `build_defi_venues()`; it is the
      manifest/legacy form listed in `DEPRECATED_DEFI_GHOST_VENUE_NAMES` ("superseded by MORPHO_VAULTS"), and
      `canonicalize_defi_venue_combined("MORPHOVAULTS-ETHEREUM")` passes it through unchanged (unknown protocol) — so the
      writer never produces `MORPHO_VAULTS-…`, and re-targeting the alias to a venue absent from the built universe would
      break alias resolution. Aliases retained as read-time back-compat shim per operator directive (do NOT remove during
      migration). The plan's "3 stray glued refs" line refs (`chain_env.py:190`, `_defi_coverage.py:31`,
      `defi_venues.py:285`) are stale line numbers — those lines are AAVE_V3 deployment dates / ghost-name comments, not
      glued-bug sites. **NOTE:** `_defi_coverage.py` `DEPRECATED_DEFI_GHOST_VENUE_NAMES` comments `VELODROMEV2 # superseded
      by VELODROME_V2`, which contradicts `PROTOCOL_CAPABILITIES` (where glued `VELODROMEV2` is canonical). This is a stale
      comment — see new todo B5.8.
- [ ] [CODE] P3. **B5.8 — reconcile stale VELODROMEV2/TRADER_JOEV2 ghost-name comments** (provenance: B5.2 finding
      2026-05-27). `DEPRECATED_DEFI_GHOST_VENUE_NAMES` in `_defi_coverage.py` comments `VELODROMEV2 # superseded by
      VELODROME_V2`, but the authoritative `PROTOCOL_CAPABILITIES.venue_prefix` is glued `VELODROMEV2` (glued = canonical).
      The comment direction is backwards for these two venues. Low-risk doc/comment fix; verify no consumer treats
      `VELODROME_V2`/`TRADER_JOE_V2` (underscore) as canonical before adjusting. **NICE-TO-HAVE** — no data impact (the
      canonicalizer + writer already treat glued as canonical).
- [ ] [SCRIPT] P1. **B5.3 — GCS re-key (SCHEDULED MIGRATION WINDOW — single-walk-discipline gate)**: re-key
      `venue=<GLUED>-<CHAIN>/` → `venue=<UNDERSCORE>-<CHAIN>/` across instruments-store-defi (+ MTDS-defi,
      features-onchain). This is a partition-key change = whole-corpus walk = review-blocking ad-hoc per single-walk
      discipline → MUST run as an operator-scheduled migration window (operator-acked 2026-05-26). Use
      `gcs_copy_object`/`gcs_delete_object` (workers=32), idempotent, dry-run first. Verify row-parity per (venue,date)
      before deleting old.
- [ ] [SCRIPT] P1. **B5.4 — Manifest reconcile**: confirm manifest venue is canonical for ALL families (AAVE_V3
      verified; audit COMPOUND_V3/UNISWAP_V\*/etc.). Where manifest still carries glued venue, write corrector shard →
      canonical.
- [ ] [SCRIPT] P0. **B5.5 — Delete old glued GCS keys** (after B5.3 parity verified) + assert no consumer reads glued.
- [ ] [UI] P2. **B5.6 — deployment-ui/api**: verify pool-breakdown resolves canonical path post-migration (the
      `_is_legacy_defi_venue_row` regex already handles `_?V\d+$`); remove any hardcoded glued venue strings; `pw:L2`.
- [ ] [VERIFY] P0. **B5.7**: re-drill `AAVE_V3-ARBITRUM · 2026-05-03` in deployment-ui → pool data renders. Sample 3
      other venue families.

## Temporary states + their canonical follow-up plans

- `"AAVE_V3"` in expected_coverage: stays until Bug 2 handler fix ships + phantom reconciler runs for Bug 3.
- Bug 5 GCS re-key is a scheduled migration window (single-walk-discipline gate); glued parquet paths remain readable
  until B5.3 completes + B5.5 deletes them.
