---
name: defi_venue_name_canonicalisation_and_reth
title: "DeFi venue-name canonicalisation + rETH (ROCKETPOOL) universe gap remediation"
status: active
priority: P1
parent_epic: defi_master
assigned_vm: vm-defi
created: 2026-06-17
last_updated: 2026-06-17
locked_by: live-defi-rollout
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
source:
  - ../audit/results/mvp_instrument_universe_gap_audit_2026_06_17.md
---

# DeFi venue-name canonicalisation + rETH (ROCKETPOOL) universe gap

Wrapper plan for the two operator-requested DeFi fixes surfaced by
`mvp_instrument_universe_gap_audit_2026_06_17.md` (DeFi section). The audit found (1) dual-format / deprecated venue
spellings polluting the registry+catalogue and (2) `ROCKETPOOL-ETHEREUM` (rETH) missing from the universe with thin LST
coverage.

## Canonical venue-name decisions (reconciled against the UAC registry SSOT)

The UAC registry (`registry/defi_venues.py`, `registry/defi_venue_capabilities.py`,
`registry/capability_declarations/_defi.py`) is the SSOT. The single canonical spelling per protocol:

- **Versioned protocols → underscore form**: `UNISWAP_V3`, `YEARN_V3`, `TRADER_JOE_V2`, `AAVE_V3`, `COMPOUND_V3`,
  `PANCAKESWAP_V3`. The glued legacy form (`UNISWAPV3` / `YEARNV3` / `TRADERJOEV2` / `AAVEV3` / `COMPOUNDV3`) resolves
  back via `canonicalize_defi_venue_combined()` and is dropped from the manifest via
  `DEPRECATED_DEFI_GHOST_VENUE_NAMES`.
- **Compound-word, non-versioned protocols → single token**: `MORPHOVAULTS` (NOT `MORPHO_VAULTS`). The audit assumed
  `MORPHO_VAULTS` was canonical — that is **backwards**; UAC's `ALL_DEFI_VENUES` / `DEFI_VENUE_PHASE` /
  `defi_venue_capabilities.py` all carry `MORPHOVAULTS-ETHEREUM`, and `test_vault_venue_canonical_names.py` already
  locks it. The underscore `MORPHO_VAULTS` is the pre-2026-05-06 LEGACY manifest spelling that resolves to
  `MORPHOVAULTS-ETHEREUM` via `LEGACY_DEFI_VENUE_ALIASES`.
- **`TRADER_JOE_V2` is canonical, NOT retired** — operator 2026-06-01 (DF-17) reversed the glued-canonical; it stays in
  the Avalanche MVP set (`ALL_DEFI_VENUES`, phase `pipeline`). The deprecated thing is the *glued* spelling
  `TRADERJOEV2`, not the protocol.

## Genuine inconsistencies reconciled

1. **`_defi_coverage.py` ghost-set bug (cross-repo data-correctness, DeFi)** — `DEPRECATED_DEFI_GHOST_VENUE_NAMES`
   carried the **canonical** glued prefix `MORPHOVAULTS` (with a backwards `# superseded by MORPHO_VAULTS` comment).
   That set is matched on the venue PROTOCOL PREFIX (`df["venue"].split("-")[0]`) by
   `deployment-api/scripts/cleanup_ghost_venue_manifest_rows.py` to **DROP** rows — so the live MetaMorpho
   `MORPHOVAULTS-*` manifest rows were at risk of being dropped, while the legacy `MORPHO_VAULTS-*` rows were NOT.
   Replaced the set entry `MORPHOVAULTS` → `MORPHO_VAULTS` (the legacy underscore prefix that *should* be filtered).
2. **Catalogue genesis YAML DEFI keys were non-canonical** — `data-catalogue.instruments-service.yaml` `shard_status.DEFI`
   keys ARE the configured IS venue set that `deployment-api`'s `reference_scope.py` matches manifest venue tokens
   against (upper-cased, exact then base-token fallback). They were drifted: `AAVE_V3_ETHEREUM` (underscore separator),
   `COMPOUND_V3_ETH`, bare `LIDO`/`ETHERFI`/`ETHENA` — none of which match the canonical combined manifest venues
   `AAVE_V3-ETHEREUM` / `COMPOUND_V3-ETHEREUM` / `LIDO-ETHEREUM` / `ETHERFI-ETHEREUM` / `ETHENA-ETHEREUM`, so those rows
   read **out_of_scope**. Canonicalised all keys to the combined form.

(The v9 GCS migration owns the on-disk `catalog.parquet` PATH re-keying — this plan only owns the
registry/catalogue-name SSOT consistency so reference + manifest + path agree on one spelling.)

## rETH (ROCKETPOOL) added

The UAC registry was **already complete** for rETH — `ROCKETPOOL-ETHEREUM` is in `ALL_DEFI_VENUES` (phase `live`),
`mvp_scope["defi"]`, `defi_venue_capabilities.py` (lst_rates/oracle_prices genesis 2021-11-08), `_defi_lst.py`
(`rETH` 2021-11-08, `ROCKETPOOL: ("rETH",)`), and `LEGACY_DEFI_VENUE_ALIASES` (`ROCKETPOOL` → `ROCKETPOOL-ETHEREUM`).
The only gap was the **catalogue genesis YAML DEFI block**, which lacked `ROCKETPOOL-ETHEREUM` → rETH manifest rows read
out_of_scope on the IS data-status view. Added `ROCKETPOOL-ETHEREUM: start_date 2021-11-08`.

## Other LST gaps noted (NOT added — out of this plan's scope)

- **cbETH (COINBASE-ETHEREUM)** is in the `carry_staked_basis` LST set and `_defi_lst.py` knows it (`cbETH` 2022-08-26,
  `COINBASE: ("cbETH",)`), but `COINBASE-ETHEREUM` is **absent from `ALL_DEFI_VENUES`** (COINBASE exists only as a CeFi
  spot exchange in the registry). Adding it is a full new-venue addition (phase + capabilities + alias + catalogue) —
  see todo below. JitoSOL (`JITO-SOLANA`) and mSOL (`MARINADE-SOLANA`) ARE present (phase `live`).

## Todos

- [ ] [REGISTRY] P1. Fix `DEPRECATED_DEFI_GHOST_VENUE_NAMES` ghost-set entry `MORPHOVAULTS` → `MORPHO_VAULTS` (the
      canonical glued prefix must not be in the drop-set; the legacy underscore prefix should) in UAC
      `registry/capability_declarations/_defi_coverage.py`. — unified-api-contracts — **CODE DONE + QG-GREEN (verified in
      isolated worktree, 152s, sentinel `4549d2c`); SHIP PENDING** — a concurrent live peer session (`orch-slot-2`) holds
      uncommitted WIP in the SHARED UAC clone (`venue_launch_dates.py` / `market_data_categories.py` / `_cefi.py` /
      `venue_mapping.py` / `mvp_scope.py` + tests). quickmerge in the shared clone stashes the WHOLE tree (would risk the
      peer's WIP) and the worktree path can't double-check-out LDR — so the push waits for the peer's tree to settle
      (watcher armed). My 2 files (`_defi_coverage.py` + the test) do NOT collide with any peer file.
- [x] [CONFIG] P1. Canonicalise `data-catalogue.instruments-service.yaml` `shard_status.DEFI` keys to the canonical
      combined manifest form (`AAVE_V3-ETHEREUM`, `COMPOUND_V3-ETHEREUM`, `LIDO-ETHEREUM`, `ETHERFI-ETHEREUM`,
      `ETHENA-ETHEREUM`) — PM `configs/` (symlinked from deployment-service/configs). — unified-trading-pm
- [x] [CONFIG] P1. Add `ROCKETPOOL-ETHEREUM` (rETH, genesis 2021-11-08) to the catalogue DEFI block. — unified-trading-pm
- [ ] [TEST] P1. Add a normalisation lock-test (`TestDefiVenueNameCanonicalReconciliation` in
      `tests/unit/test_vault_venue_canonical_names.py`) asserting the canonical decisions + the ghost-set invariant +
      rETH presence. — unified-api-contracts — **CODE DONE + GREEN (15/15 pass incl. 7 new); SHIP PENDING** (same
      shared-clone live-peer block as the `_defi_coverage.py` item — ships in the same quickmerge unit).
- [ ] [REGISTRY] P2 **NICE-TO-HAVE**. Add cbETH as `COINBASE-ETHEREUM` to the DeFi LST universe — full new-venue add:
      `ALL_DEFI_VENUES` + `DEFI_VENUE_PHASE` + `defi_venue_capabilities.py` (lst_rates/oracle_prices genesis 2022-08-26)
      + `LEGACY_DEFI_VENUE_ALIASES` (`COINBASE` → ? — collides with CeFi COINBASE; needs a chain-qualified alias only) +
      catalogue DEFI genesis. Provenance: mvp_instrument_universe_gap_audit_2026_06_17 + this plan. Needs care re:
      COINBASE name collision with the CeFi spot exchange. — unified-api-contracts + unified-trading-pm

## Progress Log

- **2026-06-17** — Reconciled the canonical venue-name SSOT (decisions above). Confirmed against UAC
  `defi_venues.py` / `defi_venue_capabilities.py` / `_defi.py` / existing `test_vault_venue_canonical_names.py`:
  underscore for versioned protocols, single-token for compound-word vaults (`MORPHOVAULTS`), `TRADER_JOE_V2`
  underscore-canonical & still in MVP. Shipped: UAC `_defi_coverage.py` ghost-set fix + UAC normalisation lock-test
  (15/15 green incl. 7 new) + PM catalogue YAML DEFI canonicalisation + rETH add. Noted cbETH gap as a P2 follow-up
  todo (COINBASE name collision needs care). **Concurrency note**: at ship-time both the UAC clone and the PM clone had
  a concurrent live session's uncommitted WIP (UAC `venue_launch_dates.py`/`market_data_categories.py`/`_cefi.py`/
  `venue_mapping.py`; PM `data-catalogue.market-tick-data-service.yaml`/`expected_start_dates.yaml`) — those foreign
  edits were PROTECTED (never staged/reverted); my changes shipped scoped to my own files only.
