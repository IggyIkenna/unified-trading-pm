---
doc_type: issue
title:
  Two small residual findings from defi_satellite_ao_dispatch_batch2-018 (spot_venue axis + capability-manifest UI sync)
summary: >-
  While closing defi_satellite_ao_dispatch_batch2-018 (unified-api-contracts@13266bf8, strategy-service@1bf99b8e), found
  two small, real gaps that were mentioned in the plan-flip prose but never converted into tracked todos: (1)
  CARRY_STAKED_BASIS_DATED's spot_venue is still hardcoded (the base CARRY_STAKED_BASIS archetype's spot_venue axis is
  fully shipped; the DATED variant was out of that todo's scope but never separately tracked); (2) UAC's regenerated
  openapi/ capability manifests have no established sync path into unified-trading-system-ui's lib/registry/ copies
  (unlike coverage.ts, which has sync-archetype-capability-to-ui.sh) -- so a raydium-for-CARRY_BASIS_PERP-style fix
  landing in UAC does not automatically reach the wizard UI.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer]
tags: [defi, wizard, capability-manifest, sync, staked-basis, residual]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md,
  ]
created: 2026-07-26
parent_epic: defi_master
priority: P3
estimate_class: refactor
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source:
  [
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py,
    unified-trading-pm/scripts/openapi/generate_capability_manifest.py,
    unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh,
  ]
---

## What I found

**Finding 1 — `CARRY_STAKED_BASIS_DATED` spot_venue still hardcoded.** The base `CARRY_STAKED_BASIS` archetype's
spot_venue axis (`catalog_staked_basis.py`'s `_STAKED_BASIS_ETH_SPOT_VENUES` / `_STAKED_BASIS_SOL_SPOT_VENUES`) is
already fully shipped per the 2026-06-17 operator directive — orca/raydium/jupiter/binance are all selectable, and a
regression test (`test_carry_staked_basis_spot_venue_axis.py`) covers it. `build_carry_staked_basis_dated()` (same file,
~line 386-451) is a separate function for the `_DATED` variant and still hardcodes `"spot_venue": "BINANCE-SPOT"` (line
~439) with no equivalent axis. This was out of scope for `defi_satellite_ao_dispatch_batch2-018`'s done-when (which only
named "staked-basis", not "staked-basis-dated"), so it was never fixed — but it was also never filed as a tracked todo,
so it would be forgotten.

**Finding 2 — UAC's regenerated capability manifests have no established UI sync path.** While closing item (1) of
batch2-018 (the CARRY_BASIS_PERP Solana-DEX spot-leg gap),
`unified-api-contracts/openapi/capability-verdict-matrix.json`

- `capability-manifest.json` were found stale (still listing removed `drift`/`gmx_v2` venues, missing
  `raydium`/`aster`/`kalshi_perp`/`polymarket_perp`) and were regenerated (`unified-api-contracts@13266bf8`). Looking
  for a corresponding UI-side sync mechanism:
  `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh` syncs a DIFFERENT source file
  (`unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`) into
  `unified-trading-system-ui/lib/architecture-v2/coverage.ts` — but there is no equivalent sync script for
  `openapi/capability-manifest.json` / `capability-verdict-matrix.json` into
  `unified-trading-system-ui/lib/registry/capability-manifest.json` (confirmed via
  `grep -rln "lib/registry" unified-trading-pm/scripts/openapi/` — zero hits). So a fix landing in UAC's `openapi/`
  manifests (like the raydium addition) does not automatically propagate to whatever the wizard UI actually renders from
  its own `lib/registry/capability-manifest.json` copy — that file's provenance/update mechanism is unclear and wasn't
  investigated further (out of scope for a data_engineering-scoped todo; UI work is a different craft).

## Why it matters

Neither is urgent (both P3), but both are exactly the kind of small, easily-forgotten gap that resurfaces as a "why
doesn't the wizard show X" confusion later if left as prose instead of a tracked todo.

## Recommended decision

- [x] ✅ [REGISTRY] P3. **DONE 2026-07-26 (slot 6), `strategy-service@9fc7c2bd`.** Made `spot_venue` a selectable axis
      for `CARRY_STAKED_BASIS_DATED`, mirroring the base archetype's `_STAKED_BASIS_ETH_SPOT_VENUES` pattern (ETH-only —
      no SOL equivalent exists for either archetype post-DRIFT-cull): `build_carry_staked_basis_dated()` now loops
      `(dated_expiry_tag × _STAKED_BASIS_ETH_SPOT_VENUES)` instead of hardcoding `spot_venue="BINANCE-SPOT"`, emitting 6
      slots (was 2) — `lido-deribit-eth-{uniswapv3,curve,binance}-{q1,q2}-usdc-v1-prod`. Added
      `TestDatedSpotVenueCatalogAxis` (4 tests) mirroring the base archetype's `TestSpotVenueCatalogAxis`, proving the
      slot count/spot-venue set/label-uniqueness and that spot_venue is the ONLY thing that varies per expiry tag.
      Updated 2 stale references (a comment + a test docstring) that assumed the old single-slot/2-slot shape; verified
      the 2 hardcoded-label backtest fixtures (`test_paper_run_passive.py`/`test_paper_run_attribution.py`) use the old
      label as an arbitrary passthrough string, not a real catalog lookup — unaffected. 94+107 tests green, full
      `quality-gates.sh` green.
- [ ] [UI] P3. Determine whether `unified-trading-system-ui/lib/registry/capability-manifest.json` /
      `ui-reference-data.json` are hand-maintained, generated by some other undiscovered mechanism, or genuinely
      unsynced from UAC's `openapi/capability-manifest.json` — and if genuinely unsynced, either add a sync script
      (mirroring `sync-archetype-capability-to-ui.sh`'s pattern) or document why the two are allowed to drift. Repos:
      unified-trading-system-ui, unified-trading-pm (if a new sync script is warranted).
