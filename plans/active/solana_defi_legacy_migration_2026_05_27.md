---
title: "Solana DeFi legacy→canonical migration (Kamino/Solend lending + Kamino/Orca/Raydium pools)"
created: 2026-05-27
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-ml
locked_by: live-defi-rollout
locked_since: 2026-05-27
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
source:
  - issues/defi_code_codex_drift_2026_05_27.md (D2)
  - GCS audit 2026-05-27 (legacy defi-prd prefixes vs dedicated split buckets)
---

# Solana DeFi legacy→canonical migration

> **Provenance**: started from `defi_code_codex_drift_2026_05_27` **D2** ("delete legacy
> `lst_rates/`/`lending_indices/`/`dex_pools/` prefixes in `market-data-tick-defi-prd`; canonical is the dedicated
> split buckets"). Verification on 2026-05-27 showed it is **not** a clean delete — the legacy prefixes hold **unique
> Solana DeFi history** the EVM-only canonical buckets never received. This plan tracks the full migrate-then-delete
> chain so it survives a mid-way stop.

## What the audit found (2026-05-27, verified against prod GCS)

- **Bucket model**: split/dedicated per-data-type buckets are canonical — MTDS handlers write via
  `get_write_bucket_name("lending-indices"|"lst-rates"|"dex-pools")`. The `market-data-tick-defi-prd/{type}/`
  top-level prefixes (old `date=` layout) are the legacy pre-split copies.
- **Per-date coverage**: 0 legacy-only dates for all three (canonical date ranges ⊇ legacy 2023-01-01→2026-04-14).
- **`lst_rates`**: legacy venue = `MARINADE` only; canonical `lst-rates-central-element-323112` has MARINADE + 14
  others → **redundant, safe to delete, no migration**.
- **`lending_indices`**: legacy = `KAMINO-SOLANA`, `SOLEND-SOLANA`; canonical = Aave/Compound/Spark (**EVM only**) →
  **legacy Solana lending is UNIQUE**.
- **`dex_pools`**: legacy = `KAMINO`/`ORCA`/`RAYDIUM`-SOLANA; canonical = Aerodrome/Balancer/Curve/GMX/Pancake/Sushi/
  Uniswap (**EVM only, 0 Solana**) → **legacy Solana pools/vaults are UNIQUE**.
- **Schema drift** (legacy ≠ EVM canonical contracts):
  - Solana lending: `apy, supply_apy, reward_apy, tvl_usd, market_id` (APY-snapshot) ≠ UAC `lending`/`lending_position`
    (`borrow_rate/supply_rate` or `supply_index/borrow_index`).
  - Solana dex_pools (Kamino): `vault_address, vault_type, token_*_mint/symbol, status` (vault metadata) ≠ UAC
    `pool/dex_pool_state` (`price, sqrt_price_x96, liquidity`).
  - `timestamp` dtype drift (legacy int64 vs canonical string / ts[ns,UTC]).
- **Live collection gap**: legacy Solana collection **stopped 2026-04-14**; canonical buckets never received Solana →
  Solana DeFi is currently NOT collected anywhere going forward. (Composes with `defi_code_codex_drift` D10 — SOLEND/
  others `live` without capability backing.)

## Operator decisions (2026-05-27)

- **Schema model**: distinct **Solana instrument_types** + new SchemaContracts (NOT bucket/data_type suffix; NOT
  nullable-union; NOT lossy map-onto-EVM). Same `data_type` (`lending_indices`/`dex_pools`), new `instrument_type`
  partition. Proposed: `solana_lending` (Kamino/Solend), `solana_amm_pool` (Orca/Raydium), `solana_vault` (Kamino).
- **Scope**: do the whole chain (contracts → history migration → reconcile → delete legacy → go-forward collectors),
  checkpointing at each gate.

## Gates (HARD-ORDERED — do not delete legacy before history migrated)

- [ ] [SCRIPT] P1. **Gate 0 — per-venue schema sample** (Kamino/Solend lending; Kamino/Orca/Raydium pools) to design
      contracts. (in progress 2026-05-27)
- [ ] [CODE] P1. **Gate 1 — UAC SchemaContracts**: add `solana_lending` / `solana_amm_pool` / `solana_vault` contracts
      to `unified_api_contracts/internal/schemas/` + register in `CONTRACT_REGISTRY` (`("defi", <it>, "lending_indices"/
      "dex_pools")`). Preserve all Solana fields. `cd unified-api-contracts && quality-gates.sh` green + cassette parity.
- [ ] [SCRIPT] P1. **Gate 2 — history migration**: read legacy `defi-prd/{lending_indices,dex_pools}/<venue>/SOLANA/
      date=*` parquets → map to new canonical schema (incl. `timestamp` dtype fix + `instrument_id`/`venue`/`ts_event`
      derivation) → write to `lending-indices-*` / `dex-pools-*` canonical buckets under
      `day=/category=defi/venue=<V>/chain=SOLANA/instrument_type=<solana_*>/data_type=...` via
      `unified_trading_library.cloud_interface.gcs_copy_object`-style writes + `record_captured` manifest emission. NO
      data loss. (~2,402 lending + ~3,606 pool legacy objects; 2023-01-01→2026-04-14.)
- [ ] [SCRIPT] P1. **Gate 3 — manifest reconcile + verify**: consolidate canonical bucket manifests; confirm Solana
      venues now show `captured` rows per (date, venue, chain, instrument_type); sample-inspect parquets.
- [ ] [SCRIPT] P0. **Gate 4 — delete legacy**: after Gate 3 verified, delete `market-data-tick-defi-prd/lst_rates/`
      (redundant), `.../lending_indices/` + `.../dex_pools/` (migrated) via `gcs_delete_object`; remove stale manifest
      rows in `defi-prd/_index` for the top-level prefixes. NO duplicate source of truth remains.
- [ ] [CODE] P1. **Gate 5 — go-forward collectors**: wire Solana collectors (Kamino/Solend lending; Kamino/Orca/
      Raydium pools) to write canonically (close the post-2026-04-14 collection gap). Composes with D10 venue-capability
      backing. Adapter scaffold + `classify_venue_error` + manifest emission per writegate; integration tests
      `@requires_credentials` if RPC/subgraph keys needed (then `BLOCKED-CREDENTIALS` ping, not deferral).
- [ ] [DOC] P2. **Gate 6 — close-out**: tick D2 in `defi_code_codex_drift_2026_05_27` (or archive that doc if D2 was its
      last open item — it is not; D7/D8/D10/D13/D15 remain); update `codex/02-data/defi-data-types-catalog.md` +
      `defi-data-pipeline.md` with the Solana instrument_types.

## Not in scope (separately tracked)

- Flat→`-prd` env-tiered dedicated-bucket cutover (writers→flat, `resolve_bucket_name`→`-prd`) — `bucket_name_ssot`
  Phase 2.6 residual, tracked in `plans/epics/manifest_master.md`.
- The DeFi EVM GCS re-key (venue glued→underscore, `dex_pool_state`→`dex_pools`, `category`→`asset_group`) — tracked in
  `plans/epics/mtds_mdps_master.md` Phase 9 + `defi_coverage_capability_alignment` (archived).

## Status log

- 2026-05-27: Audit complete; operator authorized distinct-instrument_type model + full-chain execution. Gate 0 in
  progress.
