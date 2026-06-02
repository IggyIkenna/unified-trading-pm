---
title: "Solana DeFi legacy→canonical migration (Kamino/Solend lending + Kamino/Orca/Raydium pools)"
created: 2026-05-27
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

> **🟡 CROSS-PLAN COORDINATION — DeFi C0 single-walk + canonical-naming lock (2026-06-01)**. This plan migrates the SAME
> dedicated DeFi buckets (`dex-pools` / `lending-indices`) for SOLANA venues (Kamino/Orca/Raydium/Solend) that the DeFi
> C0 single-walk in `defi_manifest_canonicalisation_2026_06_01.md` §C rewrites for ALL venues. **What starts / what ends
> (HARD)**: (1) **No concurrent whole-corpus walk on the DeFi `_index`** — this plan's Gate-2 history migration and the
> defi C0 `--apply` are MUTUALLY EXCLUSIVE (single-walk discipline); one finishes before the other starts. (2)
> **Canonical naming is operator-locked** — `codex/02-data/defi-canonical-naming-ssot.md`: pool data_type =
> `dex_pool_state` (NOT `dex_pools`), swaps = `dex_pool_swaps`; path carries `pipeline_mode=`; chain `HYPERLIQUID`. (3)
> **NEW — `dex_pool_state` is now the UNION of EVM + Solana pool state under ONE data_type** (operator 2026-06-01): EVM
> pools (`instrument_type=pool`) and Solana pools (`instrument_type=solana_amm_pool`/`solana_vault`) co-exist under
> `data_type=dex_pool_state`, distinguished by **`instrument_type` + `chain` + the superset columns** (EVM
> `price_a`/`fee_rate_bps` vs Solana `sqrt_price`/`token_a_mint` co-exist, null where N/A). So this plan's Solana
> `SOLANA_AMM_POOL`/`SOLANA_VAULT` instrument_types are the DISCRIMINATOR within `dex_pool_state`, **not a separate
> data_type** — do NOT re-key Solana pools to a distinct data_type. Banner-remove when defi C0 is C-GREEN.

> **🛑 SSOT REASSERTED 2026-05-28 (operator directive)**: **Dedicated per-data-type split buckets are canonical for
> `lending_indices`, `lst_rates`, `dex_pools` — EVERYWHERE.** No DeFi writer for these types may target the unified
> `market-data-tick-defi*` bucket. Any handler/script writing them to the unified bucket is a **bug** and must be fixed
> to use `get_write_bucket_name("lending-indices"|"lst-rates"|"dex-pools")` + the new `SOLANA_LENDING`/`SOLANA_VAULT`/
> `SOLANA_AMM_POOL` instrument_types (Gate-1 SchemaContracts UAC@7e9f4ad9 + UAC@90b2bb9d). Sources of truth for this
> SSOT: `deployment-service/configs/cloud-providers.yaml` (kind→bucket map),
> `unified_trading_library/core/cloud_constants.py` `get_write_bucket_name`, the live per-data-type handlers
> (`lending_indices_handler.py` / `lst_rates_handler.py` / `dex_pools_handler.py` all already do this for EVM). Solana
> write-path drift surfaced 2026-05-28: legacy monolithic `solana_defi_handler.py` writes to
> `market-data-tick-defi-central-element-323112/raw_tick_data/by_date/…/instrument_type=lending|pool/…` (wrong bucket +
> wrong instrument_type + flat-not-env-tier) — see new Gate-5 + Gate-7 below.
>
> **🛑 LEAK STOPPED 2026-05-28**: Cloud Scheduler `uts-prod-mtds-collect-solana-defi-cron` (was firing daily 02:05 UTC,
> wrong-bucket writes via legacy monolithic `SolanaDefiHandler`) **PAUSED** via
> `gcloud scheduler jobs pause uts-prod-mtds-collect-solana-defi-cron --location=asia-northeast1`. The autonomously-
> launched `mtds-solana-defi-backfill` VM self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`) after writing **72
> wrong-bucket Solana parquets** (Gate-7 scope). **DO NOT resume this cron** — it is being **DELETED** as part of Gate 5
> (operator directive: full per-data-type split; the monolithic handler + its dedicated cron are both retired). Solana
> venues become first-class citizens of the existing per-data-type crons (`collect-lending-indices-cron`,
> `collect-dex-pools-cron`, `collect-lst-rates-cron`) — one cron per data_type covers BOTH EVM and Solana. Until Gate 5
> ships, **no go-forward Solana DeFi collection happens** (acceptable: stop wrong-bucket leak > continue wrong-bucket
> collection per operator directive).

> **Provenance**: started from `defi_code_codex_drift_2026_05_27` **D2** ("delete legacy
> `lst_rates/`/`lending_indices/`/`dex_pools/` prefixes in `market-data-tick-defi-prd`; canonical is the dedicated split
> buckets"). Verification on 2026-05-27 showed it is **not** a clean delete — the legacy prefixes hold **unique Solana
> DeFi history** the EVM-only canonical buckets never received. This plan tracks the full migrate-then-delete chain so
> it survives a mid-way stop.

## What the audit found (2026-05-27, verified against prod GCS)

- **Bucket model**: split/dedicated per-data-type buckets are canonical — MTDS handlers write via
  `get_write_bucket_name("lending-indices"|"lst-rates"|"dex-pools")`. The `market-data-tick-defi-prd/{type}/` top-level
  prefixes (old `date=` layout) are the legacy pre-split copies.
- **Per-date coverage**: 0 legacy-only dates for all three (canonical date ranges ⊇ legacy 2023-01-01→2026-04-14).
- **`lst_rates`**: legacy venue = `MARINADE` only; canonical `lst-rates-central-element-323112` has MARINADE + 14 others
  → **redundant, safe to delete, no migration**.
- **`lending_indices`**: legacy = `KAMINO-SOLANA`, `SOLEND-SOLANA`; canonical = Aave/Compound/Spark (**EVM only**) →
  **legacy Solana lending is UNIQUE**.
- **`dex_pools`**: legacy = `KAMINO`/`ORCA`/`RAYDIUM`-SOLANA; canonical = Aerodrome/Balancer/Curve/GMX/Pancake/Sushi/
  Uniswap (**EVM only, 0 Solana**) → **legacy Solana pools/vaults are UNIQUE**.
- **Schema drift** (legacy ≠ EVM canonical contracts):
  - Solana lending: `apy, supply_apy, reward_apy, tvl_usd, market_id` (APY-snapshot) ≠ UAC `lending`/`lending_position`
    (`borrow_rate/supply_rate` or `supply_index/borrow_index`).
  - Solana dex*pools (Kamino): `vault_address, vault_type, token*\*\_mint/symbol,
    status`(vault metadata) ≠ UAC`pool/dex_pool_state` (`price, sqrt_price_x96, liquidity`).
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

- [x] ✅ [SCRIPT] P1. **Gate 0 — per-venue schema sample** — DONE 2026-05-27. Kamino+Solend lending = identical 9-col
      APY-snapshot; Kamino dex_pools = vault metadata (10c); Orca (16c) + Raydium (12c) = AMM pool metrics. Confirmed 3
      distinct shapes.
- [x] ✅ [CODE] P1. **Gate 1 — UAC SchemaContracts** — DONE — UAC@7e9f4ad9. Added `DEFI_SOLANA_LENDING_LENDING_INDICES`
      / `DEFI_SOLANA_VAULT_DEX_POOLS` / `DEFI_SOLANA_AMM_POOL_DEX_POOLS` to `contracts.py` + registered in
      `CONTRACT_REGISTRY` under `("defi", solana_lending|solana_vault|solana_amm_pool, lending_indices|dex_pools)`. All
      Solana fields preserved (venue-specific AMM cols nullable+optional). ruff + basedpyright 0; cassette parity 447
      passed.
- [x] ✅ [CODE] P1. **Gate 1.5 — InstrumentType enum + builder dispatch** — DONE — UAC@90b2bb9d. Added
      `SOLANA_LENDING`/`SOLANA_VAULT`/`SOLANA_AMM_POOL` to `InstrumentType` enum + `SUPPORTED_INSTRUMENT_TYPES`
      allow-list + `_DEFI_TYPES` (so `build_instrument_id` produces `VENUE-CHAIN:TYPE:SYMBOL`; e.g.
      `KAMINO-SOLANA:SOLANA_LENDING:<market_id>`). Cassette parity 447 passed.
- [~] [SCRIPT] P1. **Gate 2 — history migration** — SCRIPT SHIPPED + SMOKE VERIFIED, FULL RUN PENDING.
  `market-tick-data-service/scripts/migrate_legacy_solana_defi_to_canonical.py` (MTDS@c38d1ca3) reads legacy
  `defi-prd/{lending_indices,dex_pools}/<venue>/SOLANA/date=*` → writes canonical flat
  `day=/category=defi/venue=/chain=SOLANA/instrument_type=<solana_*>/data_type=*` to `lending-indices-*` / `dex-pools-*`
  (matches EVM canonical layout). Schema map: drops legacy `timestamp` (write-time); `ts_event` = midnight UTC of date
  partition; `instrument_id` via `build_instrument_id`. **Smoke** (2026-05-28, 1 date × 5 subsets): 14,807 rows
  migrated; sample parquet read-back clean (instrument_id format verified, ts_event correct, all legacy fields
  preserved); re-run idempotent (5/5 "skip (exists)"). **Remaining**: full ~5,995 shards across ~1199 distinct dates
  (~8–12h sequential at ~3–7s/shard). Best run with `--max-dates` chunks or backgrounded on a VM. CLI: `--dry-run` /
  `--only-protocol` / `--only-data-type` / `--max-dates` for control. Manifest emission deferred to Gate 3 consolidator
  (no explicit per-shard emit in the migration script — the consolidator discovers newly-written files).
- [x] ✅ [SCRIPT] P1. **Gate 3 — manifest reconcile + verify**: consolidate canonical bucket manifests; confirm Solana
      venues now show `captured` rows per (date, venue, chain, instrument_type); sample-inspect parquets. **DONE
      2026-05-30** — MTDS@86d0113. `scripts/gate3_solana_manifest_reconcile.py` scanned both split buckets + wrote
      per-VM shards + consolidated. lending-indices: **2,811 SOLANA rows** (KAMINO=1,259 SOLEND=1,039 MARGINFI=513),
      `instrument_type=solana_lending`, 2022-11-01→2026-05-28, all `captured`. dex-pools: **1,555 SOLANA rows**
      (ORCA=529 RAYDIUM=528 PHOENIX=497 KAMINO=1), `solana_amm_pool`+`solana_vault`, 2022-11-01→2026-05-28, all
      `captured`. Sample-inspect confirmed correct `instrument_id` format (`VENUE-SOLANA:SOLANA_LENDING:<market_id>`) +
      `ts_event=midnight UTC`. Kamino vault count=1 (not 1,199 expected) — Bug-K backfill rerun pending per plan.
- [~] [SCRIPT] P0. **Gate 4 — delete legacy**: after Gate 3 verified, delete `market-data-tick-defi-prd/lst_rates/`
  (redundant), `.../lending_indices/` + `.../dex_pools/` (migrated) via `gcs_delete_object`; remove stale manifest rows
  in `defi-prd/_index` for the top-level prefixes. NO duplicate source of truth remains. **`lst_rates/` DONE
  2026-05-28**: deleted 1,200 date-prefix parquets (MARINADE 2023-01-01→2026-04-14); pruned 64,373 stale manifest rows
  from defi-prd `_index/availability_index.parquet` (1,633,780→1,569,407 rows). Canonical
  `lst-rates-central-element-323112` confirmed superset (dates 2020-01-01→2026-05-19, MARINADE 902 rows).
  **`lending_indices/` + `dex_pools/` deferred**: Gate 2 migration has NOT completed (canonical buckets show 0 SOLANA
  rows — Gate 3 cannot be verified yet). Re-run this gate after Gate 2 migration VM completes and Gate 3 is verified.
- [x] ✅ [SCRIPT] P0. **Gate 7 — migrate ALL bad-bucket Solana data → canonical split buckets (operator directive
      2026-05-28: "migrate the old bad buckets too")**: in addition to Gate 2 (which sources from `defi-prd/{type}/…`
      legacy historical), this gate migrates the **2823 wrong-bucket parquets** (actual count; plan estimated 72) the
      autonomous `mtds-solana-defi-backfill` VM wrote (2022-11-01→2026-05-28). **Source**:
      `gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=*/[pipeline_mode=*/]asset_group=defi/venue=*/chain=SOLANA/     instrument_type={lending|pool|lst}/data_type={lending_indices,dex_pools,lst_rates}/...`
      **7 venue/type combos**: KAMINO+SOLEND+MARGINFI (lending→SOLANA_LENDING), ORCA+RAYDIUM+PHOENIX
      (pool→SOLANA_AMM_POOL), MARINADE (lst→LST). **Script**: added `--source-bucket defi` + `--delete-source` flags to
      `scripts/migrate_legacy_solana_defi_to_canonical.py`; reuses existing `_to_canonical_df` via thin
      `_to_canonical_df_wrong_bucket` wrapper (drops EVM `instrument_type` col + rebuilds `instrument_id` with correct
      `InstrumentType`). Ran `--source-bucket defi --delete-source` (no `--dry-run`) 2026-05-28: 2823 shards migrated, 0
      errors, 0 wrong-bucket Solana parquets remaining. Sample-inspected `KAMINO-SOLANA:SOLANA_LENDING:...`
      instrument_id (correct type). Gate 7 ends in: **zero Solana DeFi data outside the dedicated split buckets** (SSOT
      enforced). ✓
- [x] ✅ [CODE] P1. **Gate 5 — go-forward collectors: FULL PER-DATA-TYPE SPLIT (operator directive 2026-05-28 "the
      heavier path (full split) pls")** — DONE 2026-05-30. MTDS@896d5c9 + UAC@f98a639. Monolithic
      `solana_defi_handler.py` deleted; Solana DEX (orca/raydium/kamino/phoenix) → `dex_pools_handler.py`; Solana
      lending (kamino/solend/marginfi) → `lending_indices_handler.py`; UAC `mtds_operations` updated to per-data-type
      ops; QG exclusions removed; backfill script updated; MTDS QG: 2179 passed, 15 skipped. **Supplementary commits
      (slot-1 2026-05-30)**: MTDS@1f5fb5a + MTDS@3ba2501 + deployment-service@839fd53. `_solana_defi_fetch.py` shared
      async fetch module added; `lending_indices_handler.py` + `dex_pools_handler.py` extended via Solana branch in
      `_collect_protocol_chain`; `full-defi-backfill.sh` collect-solana-defi lines replaced with per-data-type
      equivalents; `launch-mtds-solana-defi-backfill-vm.sh` deleted. `solana_defi_handler.py` kept in main worktree for
      Drift backfill (`setup-data-pipeline-vm.sh:1082 --solana-drift-backfill`) pending separate Drift migration. Tests:
      157 passed, 1 skipped. **NOT modernize-in-place** — finish what `docs/DEFI_DOWNLOAD_STRATEGY.md:402` already
      declared was the direction: _"Old monolithic handlers (`evm_defi_handler`, `solana_defi_handler`) replaced by
      per-data-type handlers"_. The doc/code drift (file still on disk, QG-excluded at `scripts/quality-gates.sh:25`)
      means the split was never completed for Solana. **This gate completes it.**

      **NOT BLOCKED-CREDENTIALS** (verified 2026-05-28): GCP SM has `helius-api-key` + `solana-paper-keypair-private-key`
      + `solana-wallet-address`; `dependency_health_policies.yaml` lines 139/151/157 register `helius_solana_rpc` +
      `solana_rpc_primary` (Helius backup); UAC `SOLANA_RPC_TEMPLATES` + `get_solana_rpc_url` ready; KMNO/RAY/ORCA in
      `capability_declarations/_defi.py` declare `mtds_operations=["collect-solana-defi"]` (those declarations
      themselves need updating — see step 5 below).

      **Execution steps (HARD-ORDERED)**:
      1. **Extend per-data-type handlers** to include Solana venues. Each handler iterates a `_DEFAULT_PROTOCOLS` list
         then calls `get_supported_chains_for_protocol(protocol)` (EVM today). Add Solana protocols + ensure
         `get_supported_chains_for_protocol` returns `"SOLANA"` for them via UAC `capability_declarations/_defi.py`:
         - `lending_indices_handler.py`: add `kamino`, `solend`, `marginfi` (Kamino lending side, NOT vault).
           `_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3", "kamino", "solend", "marginfi"]`. Build Solana
           branch in the fetch path (Helius RPC + protocol-specific API). Write via the existing
           `get_write_bucket_name("lending-indices")` path with `instrument_type=InstrumentType.SOLANA_LENDING` +
           `symbol_column="market_id"`. SchemaContract = `DEFI_SOLANA_LENDING_LENDING_INDICES` (UAC@7e9f4ad9).
         - `dex_pools_handler.py`: add `kamino` (vault flavour → `SOLANA_VAULT`), `orca` (AMM → `SOLANA_AMM_POOL`),
           `raydium` (AMM → `SOLANA_AMM_POOL`), `phoenix` (CLOB pool → `SOLANA_AMM_POOL` if shape fits; else new IT).
           Dispatch per-venue to the correct `instrument_type` (Kamino-vault vs Orca/Raydium-AMM are different
           SchemaContracts even within the same data_type).
         - `lst_rates_handler.py`: confirm Marinade/Jito already handled (line 518 has `venue="MARINADE"`, line 475
           has `LST`); if not under the new Solana enum, route Marinade/Jito as `instrument_type=LST` (existing) unless
           Solana needs a distinct enum — design call: probably reuse `LST` since lst_rates is already canonical.
         - If `gas_fees` / `oracle_prices` for Solana are needed for the archetype, extend those handlers similarly;
           else defer.
      2. **Delete the monolithic `solana_defi_handler.py`** + unregister from `cli/main.py:436` + remove from
         `scripts/full-defi-backfill.sh:66`. Remove the QG-exclusion at `scripts/quality-gates.sh:25`. Delete the launcher
         `deployment-service/scripts/vm/launch-mtds-solana-defi-backfill-vm.sh` (created earlier today; superseded).
      3. **Delete the now-orphan `uts-prod-mtds-collect-solana-defi-cron` + its Cloud Run Job** (instead of un-pausing).
         The per-data-type crons (`collect-lending-indices-cron`, `collect-dex-pools-cron`, `collect-lst-rates-cron`)
         already fire daily and will now pick up Solana venues automatically via the extended handlers — **NO** new
         scheduler entry needed. Remove the cron's Terraform from
         `deployment-service/terraform/gcp/defi_collection_scheduler.tf` (whichever block defines it).
      4. **Update UAC capability declarations**: in `capability_declarations/_defi.py` flip Solana venue
         `mtds_operations` from `["collect-solana-defi"]` → the appropriate per-data-type op
         (`["collect-lending-indices"]` for Kamino-lending/Solend/Marginfi; `["collect-dex-pools"]` for Kamino-vault/
         Orca/Raydium/Phoenix; `["collect-lst-rates"]` for Marinade/Jito). This is the registry-side completion of the
         split.
      5. **QG green** the MTDS repo (handler file deletion + extensions). Add a unit test per Solana venue that mocks
         the Helius response + asserts canonical-path write + correct `instrument_type`.
      6. **Live smoke** against Helius (one-day collect via `python -m market_tick_data_service.cli.main
         collect-lending-indices --asset-group defi --protocols kamino,solend --date YYYY-MM-DD` etc.); verify rows
         land in canonical split-bucket paths.
      7. **Verify next day's daily cron fires correctly** for the per-data-type ops (which now include Solana). Watch
         the next 02:05-window-equivalent runs of `collect-lending-indices-cron` + `collect-dex-pools-cron` + smoke
         their `_index/availability_index.parquet` for the new Solana rows.

      **End state**: monolithic Solana handler + its dedicated cron are GONE; Solana venues are first-class citizens
      in the per-data-type handlers; one cron per data_type drives the whole DeFi pipeline (EVM + Solana); split-bucket
      SSOT enforced everywhere. **Estimate**: ~2–3 cal AI-days (was ~1–2 for the in-place modernize; full split adds
      registry-update + Terraform + per-venue tests).

- [x] ✅ [DOC] P2. **Gate 6 — close-out**: tick D2 in `defi_code_codex_drift_2026_05_27` (or archive that doc if D2 was
      its last open item — it is not; D7/D8/D10/D13/D15 remain); update `codex/02-data/defi-data-types-catalog.md` +
      `defi-data-pipeline.md` with the Solana instrument_types. D2 partial-update: lst_rates/ confirmed deleted
      2026-05-28; lending_indices/+dex_pools/ deferred to Gate-2 finish. Catalog instrument-type table gained
      solana_lending/solana_vault/solana_amm_pool rows (UAC@7e9f4ad9+UAC@90b2bb9d). Pipeline doc: collect-solana-defi
      deprecated; legacy-prefix note updated. — PM@(Gate-6 commit)

## Backfill launch findings 2026-05-28 (slot-1 four-VM dispatch)

> Slot-1 dispatch 2026-05-28 launched four Solana DeFi backfill VMs for `2025-01-17 → 2026-05-28`. All four hit T+10min
> RUNNING then self-deleted on `VM_SHUTDOWN_ON_COMPLETION=true`. Three surfaced bugs that bound the venue-keyed gap from
> being closed in this pass. Each is a `- [ ]` plan todo here; do NOT defer without operator [ack].

### VMs launched + outcome

| VM (deleted by self-shutdown)       | Launcher                                                                                 | Range                   | Outcome (run.log final line)                                                                                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mtds-solana-drift-backfill`        | `launch-mtds-solana-drift-backfill-vm.sh`                                                | 2025-01-17 → 2026-05-28 | 497 results, **0 records** — every date past Drift V1 S3 archive end (2025-01-08)                                                                                                            |
| `mtds-gas-fees-solana`              | `launch-mtds-solana-gas-backfill-vm.sh`                                                  | 2025-01-17 → 2026-05-28 | 497 results, **0 records** — every chain-id row logged `"Unknown chain_id 99999, skipping"`                                                                                                  |
| `marinade-backfill-20260528-140422` | `launch-marinade-solana-backfill-vm.sh`                                                  | 2025-01-17 → 2026-05-28 | 497 results, jitoSOL written for `2026-05-27` only; remaining dates `"all expected sentinels already captured"` (sentinel-bypass — collector treats live snapshot as sufficient for history) |
| `mtds-solana-defi-backfill` (NEW)   | `launch-mtds-solana-defi-backfill-vm.sh` (created this pass, deployment-service@4d9e6ce) | 2025-01-17 → 2026-05-28 | **PROGRESS** — writes per-day rows for MARGINFI/SOLEND/KAMINO_LENDING/RAYDIUM/ORCA/PHOENIX (~14k rows/day, mostly Orca). JITO and Kamino-vault each have a discrete bug (below).             |

### Discovered bugs (each gets a fix-or-ack todo)

- [x] ✅ [MTDS] P1. **Drift S3 backfill: archive end 2025-01-08 is hardcoded; entire post-2025-01-08 history must come
      from Drift Data API (or Drift V2 archive) not S3 V1.** `solana_defi_handler.py:172`
      (`_DRIFT_S3_ARCHIVE_END = date(2025, 1, 8)`) makes every requested date emit `EXPECTED_PAST_SOURCE_COVERAGE_END` —
      honest but useless for closing the venue-keyed Drift gap from 2025-01-17 onward. Fix path: either (a) wire a Drift
      V2 historical source (drift-historical-data S3 V2 bucket `drift-historical-data-v2`), or (b) replay the Drift Data
      API `/stats/markets` + funding endpoints per-day via the existing snapshot path, or (c) operator ack that
      2025-01-17 → today Drift coverage is `BLOCKED-OPERATOR-DECISION` until V2 source is signed up. Provenance: slot-1
      2026-05-28 run.log `gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`.
      **Shipped 2026-05-29**: code-fix Bug-D landed mtds@0e92e49a (Helius v0 dispatcher replaces 404-S3 path); backfill
      VM relaunched 2026-05-29T15:38:56Z via vm-ml SSM (i-02294132088f23e50) after IAM unblock —
      `vm:mtds-solana-drift-backfill` zone `asia-northeast1-c`, range 2025-01-09→2026-05-28, market SOL-PERP, verified
      RUNNING T+10min @ 15:49:32Z (STARTED event 15:41:57Z + 17 event files streaming, run.log shows per-date Helius
      progress through 2025-01-12 by 15:44Z).
- [x] ✅ [MTDS] P1. **Solana gas-fees chain_id=99999 is not registered in the gas-fee chain map → entire
      `mtds-gas-fees-solana` backfill silent no-op.** Launcher passes `--gas-fee-chains 99999` (per
      `setup-data-pipeline-vm.sh:1004`), but the gas-fees handler logs `"Unknown chain_id 99999, skipping"` for every
      date. Solana doesn't have an EVM-style numeric chain_id — the correct value is the canonical chain key from UAC
      `registry/data_source_continuity.py` (likely `"SOLANA"` or the registry's Solana sentinel, NOT 99999). Fix:
      replace `--gas-fee-chains 99999` with the correct Solana chain key in `setup-data-pipeline-vm.sh`
      `solana-gas-backfill` block; OR add a numeric→str mapping in the gas-fees handler. Provenance: slot-1 2026-05-28
      run.log `gs://deployment-scripts-central-element-323112/vm-logs/mtds-gas-fees-solana/run.log`. **FIXED
      2026-05-30** (MTDS@c3ae794c + deployment-service@3e83f30): handler accepts `solana` sentinel;
      setup-data-pipeline-vm.sh passes `--gas-fee-chains solana`. Backfill VM `mtds-gas-fees-solana` relaunched
      2026-05-30 (slot-1) with tarball@cef599e, range 2025-01-17→2026-05-28, verified RUNNING.
- [x] ✅ [MTDS] P1. **Marinade backfill bypasses historical days via "all expected sentinels already captured" check —
      only the latest date emits a real APY row.** `launch-marinade-solana-backfill-vm.sh` routes through
      `collect-lst-rates` which uses an LST-rates handler keyed on sentinel-cluster completion at the latest date; with
      the latest date captured, every prior date short-circuits. Net: the VM wrote jitoSOL + 12 EVM LSTs for 2026-05-27
      only, NOT 2025-01-17 → 2026-05-26 for Marinade. Marinade mSOL APY is also emitted via
      `solana_defi_handler._collect_marinade` (handler list `["drift","kamino",...,"marinade",...]`) — re-launching the
      new `launch-mtds-solana-defi-backfill-vm.sh` with `--protocols marinade` SHOULD close this without needing to fix
      the lst-rates sentinel logic, **assuming** Marinade APY endpoint `api.marinade.finance/msol/apy/365d` is
      daily-replayable (collector currently reads "latest" only — needs a `target_date_str` parameter analog to marginfi
      TVL filter). Provenance: slot-1 2026-05-28 run.log
      `gs://deployment-scripts-central-element-323112/vm-logs/marinade-backfill-20260528-140422/run.log`. **FIXED
      2026-05-30** (MTDS@c3ae794c): `_collect_marinade` now accepts `target_date_str` + routes past dates through
      `_collect_marinade_historical` (DeFiLlama yields chart, daily APY back to 2025-02-26). Note:
      `launch-marinade-solana-backfill-vm.sh` uses `collect-lst-rates` (wrong path for this fix); re-launch done via
      direct `collect-solana-defi --protocols marinade --solana-lending-backfill` VM
      `mtds-marinade-bugm-relaunch-20260530-052448` (asia-northeast1-c), range 2025-01-17→2026-05-28, verified RUNNING.
- [x] ✅ [MTDS] P1. **Kamino vault-strategies path raises `"row is missing required symbol column 'pool_id'"` schema
      error every date.** `solana_defi_handler._collect_kamino` emits rows with `vault_address` not `pool_id` but the
      `dex_pools` SchemaContract for `defi/pool/dex_pools` requires `pool_id`. Fix: rename the column in
      `_collect_kamino` (alias `vault_address` → `pool_id` for the dex_pools contract; keep `vault_address` as a
      secondary field) OR widen the SchemaContract. Provenance: slot-1 2026-05-28 run.log
      `gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-defi-backfill/run.log` (one warning per
      processed date). Composes with Gate 1 schema-contracts work above — if a `solana_vault` instrument_type lands as
      planned, the Kamino vault rows route there instead and this becomes moot. Capture so it doesn't slip. **FIXED
      2026-05-30** (MTDS@c3ae794c): `_collect_kamino` now emits `pool_id` (aliased from vault PDA `address`) +
      `vault_address` (secondary) + `token_a`/`token_b` from resolved mint symbols. Kamino backfill rerun via
      collect-solana-defi --protocols kamino (see Bug-K "Bug fixes" section above — already `[x] ✅`).
- [x] ✅ [MTDS] P2. **Jito Stakenet API `pool_token_supply=0` returned every fetch → `"cannot compute exchange rate"`
      every date in the new VM run.** `solana_defi_handler._collect_jito` hits
      `kobe.mainnet.jito.network/api/v1/stake_pool_stats` and gets back a body whose `pool_token_supply` field is 0 (or
      absent), so the handler gives up and returns empty. — MTDS@c3ae794c (backfill 2026-05-30). Root cause = API drift:
      Jito shape changed from single object to time-series payload. Rewrote `_collect_jito` to consume latest entry;
      added `_collect_jito_historical` via DeFiLlama yields chart.
- [x] ✅ [MTDS] P3. **GCS object-mutation 429s on per-VM manifest shard at the start of every backfill VM** — both
      `mtds-solana-drift-backfill` and the new `mtds-solana-defi-backfill` get `429 rateLimitExceeded ... per-VM shard`
      on the first few flushes. Non-blocking (manifest writes are best-effort) but it means the first ~10-30s of
      manifest rows are missing from the per-VM shard. Fix: add an exponential backoff inside `DefiManifestRecorder`
      flush, or batch the early flushes. Already a known pattern — track here so the next manifest-consolidator pass
      dedup-merges correctly. — Covered by Bug-R (UTL@cb1f4b5f, 2026-05-29): `ManifestWriter._write_per_vm_shard` now
      routes uploads through `_upload_with_backoff_on_429` — 3 retries at 1s/2s/4s base ±30% jitter on
      `429`/`rateLimitExceeded`/ `TooManyRequests`. `DefiManifestRecorder.close()` calls `self._writer.close()` which
      flows through this path; no additional layer needed at the recorder level (backfill 2026-05-30).

### Next slot-1 actions (sequenced)

1. Re-launch `launch-mtds-solana-defi-backfill-vm.sh` will continue progressing on the LDR codepath; let it finish (498
   dates × ~14k rows/day × 6 venues = the bulk of the venue-keyed gap).
2. File the 4 P1 fixes as MTDS handler PRs (Drift V2 source, gas-fee chain registry, Marinade per-date, Kamino pool_id
   alias). Each is a 1-2h fix.
3. Re-launch the affected VMs after the fixes land + setup-data-pipeline-vm.sh is re-uploaded to GCS.

### Discovered side-issues (2026-05-29 — slot-1 dispatch from vm-ml SSM)

- [x] ✅ [INFRA] P0. **Drift Helius backfill VM relaunch + Aave/Spark/Compound lending-indices backfill VM relaunch —
      IAM grant gap.** Operator granted `roles/compute.instanceAdmin.v1` on `central-element-323112` to
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` 2026-05-29 ~T15:25Z. Tarballs already
      rebuilt + uploaded at 2026-05-29T15:22Z (`mtds-code@0e92e49a36c3`, `unified-api-contracts-code@15e67b93`,
      `unified-trading-library-code@32e7424b505e`, `deployment-service@06d5961fc3bf`,
      `instruments-service@7727212009a0`). Two re-launch attempts via `aws ssm send-command i-02294132088f23e50` (vm-ml)
      both failed at the gcloud `instances.create` step: - Attempt 1 (default-SA route):
      `ERROR: The user does not have access to service account       '1060025368044-compute@developer.gserviceaccount.com'. ... Ask a project owner to grant you the       iam.serviceAccountUser role on the service account.` -
      Attempt 2 (`--service-account=unified-trading-sa@…` self-impersonation): same error against
      `unified-trading-sa@...` itself — `compute.instanceAdmin.v1` doesn't include `iam.serviceAccountUser`. **Unblock
      (operator-only — agent has no IAM-grant authority)**: pick ONE of: 1. Grant `roles/iam.serviceAccountUser` on
      `1060025368044-compute@developer.gserviceaccount.com` to
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (lets the existing launchers work as-written
      with the default compute SA); OR 2. Grant `roles/iam.serviceAccountUser` on
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` to itself (self-impersonation path; still
      needs a launcher patch to pass `--service-account=unified-trading-sa@…`). Option 1 is the cheaper unblock — no
      launcher edits. After grant lands, re-dispatch via:
      `     sudo -iu ubuntu bash -lc 'cd ~/unified-trading-system-repos/.tabs/1 && \       bash deployment-service/scripts/vm/launch-mtds-solana-drift-backfill-vm.sh \         --start 2025-01-09 --end 2026-05-28 --zone asia-northeast1-c --env prod'     sudo -iu ubuntu bash -lc 'cd ~/unified-trading-system-repos/.tabs/1 && \       DEPLOYMENT_ENV=prod bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh \         2025-01-01 2026-05-28'     `
      Provenance: SSM CommandIds `084d6352-2874-4d3d-92a3-eee78f330b46` (default-SA attempt) +
      `a77138ac-c472-4eba-b867-c059d9f34b82` (self-impersonation attempt). Per CLAUDE.md no-fire-and-forget +
      `Plans Run To Actual Completion`: parent P1 todos at lines 205 (Drift) + 470 (Aave OPTIMISM, code-fix already ✅;
      backfill relaunch outstanding) stay `- [ ]` until backfills complete + T+10min verify GREEN. **RESOLVED
      2026-05-29**: operator granted both `roles/compute.instanceAdmin.v1` + `roles/iam.serviceAccountUser` to
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` at project scope (verified). Re-dispatched via
      vm-ml SSM `i-02294132088f23e50`: (a) `vm:mtds-solana-drift-backfill` launched 2026-05-29T15:38:56Z zone
      `asia-northeast1-c`, mtds@0e92e49a + uac@15e67b93 + ist@77272120, verified RUNNING T+10min @ 15:49:32Z (17 event
      files, STARTED@15:41:57Z); (b) `vm:mtds-lending-indices-20260529-153923` launched 2026-05-29T15:39:25Z same zone,
      uac@15e67b93 + ist@77272120, verified RUNNING T+10min @ 15:49:32Z (273 event files, STARTED@15:42:17Z, run.log
      shows 44,489 lending-indices rows written for 2025-01-03 across AAVE_V3/COMPOUND_V3 on multiple chains;
      AAVE_V3-OPTIMISM still 0 rows on `messari_lending` fallback — separate side-issue tracked under Bug-A relaunch
      evidence at line ~509, NOT a relaunch-IAM blocker). <<<<<<< Updated upstream
- [x] ✅ [INFRA] P3. **Reset corrupt PM worktree on vm-ml (`tab/rootm/1`)** — `git fsck` reports unreachable objects
      under `tab/rootm/1` for unified-trading-pm
      (`Could not read 83fac63... Failed to traverse parents of commit 09b84d21`). Tarball build still worked (only PM
      worktree corrupted; 6 service dep repos clean). Workaround: do all PM plan-flips from the operator's laptop (local
      cwd `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm`) instead of from vm-ml
      SSM. Next maintenance pass: `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 1` on vm-ml
      (operator-only since slot reset destroys local state). Surfaced 2026-05-29 during Drift+Aave OP backfill launch
      dispatch. — vm-ml slot-6: ran setup-tab-worktrees.sh --reset-slot 1 2026-05-30; fsck clean, all repos rebased LDR
- [x] # ✅ [INFRA] P3. Capture GCP IAM grants on `unified-trading-sa@central-element-323112` in the canonical IAM SSOT
- [x] ✅ [INFRA] P3. **Reset corrupt PM worktree on vm-ml (`tab/rootm/1`)** — `git fsck` reports unreachable objects
      under `tab/rootm/1` for unified-trading-pm
      (`Could not read 83fac63... Failed to traverse parents of commit 09b84d21`). Tarball build still worked (only PM
      worktree corrupted; 6 service dep repos clean). Workaround: do all PM plan-flips from the operator's laptop (local
      cwd `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm`) instead of from vm-ml
      SSM. Next maintenance pass: `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 1` on vm-ml
      (operator-only since slot reset destroys local state). Surfaced 2026-05-29 during Drift+Aave OP backfill launch
      dispatch. — vm-ml slot-6: ran setup-tab-worktrees.sh --reset-slot 1 2026-05-30; fsck clean, all repos rebased LDR
- [ ] [INFRA] P3. Capture GCP IAM grants on `unified-trading-sa@central-element-323112` in the canonical IAM SSOT
  > > > > > > > Stashed changes
        (likely `deployment-service/terraform/gcp/*.tf` or a setup script). Roles granted ad-hoc 2026-05-29 during vm-ml
        backfill dispatch: `roles/compute.instanceAdmin.v1` + `roles/iam.serviceAccountUser` (project-scope). Without SSOT
        sync, a future `tofu apply` could revert them. — deployment-service@dab9a60 (2026-05-30). Added
        `google_project_iam_member.unified_trading_compute_instance_admin` +
        `google_project_iam_member.unified_trading_service_account_user` to `terraform/gcp/main.tf` after the existing SA
        IAM block.

## Not in scope (separately tracked)

- Flat→`-prd` env-tiered dedicated-bucket cutover (writers→flat, `resolve_bucket_name`→`-prd`) — `bucket_name_ssot`
  Phase 2.6 residual, tracked in `plans/epics/manifest_master.md`.
- The DeFi EVM GCS re-key (venue glued→underscore, `category`→`asset_group`) — tracked in
  `plans/epics/mtds_mdps_master.md` Phase 9 + the DeFi C0 single-walk in `defi_manifest_canonicalisation_2026_06_01.md`.
  **NAMING CORRECTION (operator-locked 2026-06-01)**: the canonical pool data_type is `dex_pool_state` EVERYWHERE (NOT
  `dex_pools` — the earlier "`dex_pool_state`→`dex_pools`" re-key here was backwards and is RETIRED). SSOT:
  `codex/02-data/defi-canonical-naming-ssot.md`.

## Dispatch-ready handoff (2026-05-28, vm-ml autonomous)

> **🟢 HANDOFF ACTIVE 2026-05-28**: operator closing laptop; Gates 2-full / 3 / 4 / 6 handed off to **vm-ml** (this
> plan's `assigned_vm`). Migration script + UAC contracts + enum extensions are on `live-defi-rollout`. A vm-ml worker
> can clone-and-run autonomously per the runbooks below. Gate 5 separately scoped (multi-day adapter dev — not in this
> handoff).

### Gate 2 runbook (vm-ml — tmux on the VM, log to GCS)

```bash
# 1. Ensure latest LDR
cd ~/code && for r in unified-api-contracts market-tick-data-service unified-trading-pm; do
  (cd "$r" && git fetch origin live-defi-rollout && git checkout origin/live-defi-rollout); done
# 2. Run in tmux + tee to GCS log
cd ~/code/market-tick-data-service
TS=$(date -u +%Y%m%dT%H%M%SZ)
LOCAL_LOG=/tmp/solana_defi_${TS}.log
GCS_LOG=gs://deployment-scripts-central-element-323112/migration-logs/solana_defi/${TS}.log
tmux new -d -s solana-mig "
  export GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod DEPLOYMENT_ENV_SHORT=prd CLOUD_PROVIDER=gcp PYTHONUNBUFFERED=1
  .venv/bin/python scripts/migrate_legacy_solana_defi_to_canonical.py --log-level INFO 2>&1 | tee ${LOCAL_LOG}
  ec=\$?
  gcloud storage cp ${LOCAL_LOG} ${GCS_LOG} || true
  echo MIGRATION_EXIT=\$ec | gcloud storage cp - ${GCS_LOG}.exit || true
"
tmux ls | grep solana-mig    # verify alive within 60s
```

**ETA ~4–5h** (lending kamino + solend ~60+60min; kamino vault ~60min; orca pool ~120min — long pole; raydium ~30min).
Idempotent: `blob_exists` skip — interrupted runs resume. **Local pre-handoff run already migrated 2,107 shards**
(lending kamino, dates ~2023-01-01→2023-04) which will print as "skip (exists)" early in the vm-ml resume run.
Completion signal: `done. shards processed = ...` line + `MIGRATION_EXIT=0` file on GCS.

### Gate 3 runbook (after Gate 2 emits `done. shards processed = ...`)

```bash
# Force-fire the manifest consolidator on the 2 dedicated buckets (or wait ~5min for the cron):
gcloud run jobs execute manifest-consolidator-lending-indices --region=asia-northeast1 --wait || true
gcloud run jobs execute manifest-consolidator-dex-pools --region=asia-northeast1 --wait || true
# Verify per-subset SOLANA captured rows landed:
cd ~/code/market-tick-data-service && .venv/bin/python <<'PY'
import io, pyarrow.parquet as pq
from unified_trading_library import get_storage_client
s = get_storage_client(project_id='central-element-323112')
for buc in ('lending-indices-central-element-323112','dex-pools-central-element-323112'):
    b = s.download_bytes(buc, '_index/availability_index.parquet')
    df = pq.read_table(io.BytesIO(b)).to_pandas()
    sol = df[df['chain']=='SOLANA'] if 'chain' in df.columns else df.iloc[0:0]
    by_it = sol['instrument_type'].value_counts().to_dict() if len(sol) and 'instrument_type' in sol.columns else {}
    print(buc, '— SOLANA rows:', len(sol), '| by instrument_type:', by_it)
PY
# Expected: lending-indices ~2,398 SOLANA rows (solana_lending); dex-pools ~3,597 SOLANA (~1,199 solana_vault + ~2,398 solana_amm_pool).
```

### Gate 4 runbook (after Gate 3 verified)

```bash
# Delete legacy top-level prefixes from defi-prd (no duplicate source of truth)
LEG=gs://market-data-tick-defi-prd-central-element-323112
for p in lst_rates lending_indices dex_pools; do
  echo "deleting $LEG/$p/ ..."
  gcloud storage rm --recursive "$LEG/$p/"
done
# Prune stale manifest rows in defi-prd/_index referring to those data_types:
cd ~/code/market-tick-data-service && .venv/bin/python <<'PY'
import io, pyarrow.parquet as pq, pandas as pd
from unified_trading_library import get_storage_client
s = get_storage_client(project_id='central-element-323112')
buc='market-data-tick-defi-prd-central-element-323112'
b = s.download_bytes(buc, '_index/availability_index.parquet')
df = pq.read_table(io.BytesIO(b)).to_pandas()
mask = df['data_type'].isin(['lst_rates','lending_indices','dex_pools']) if 'data_type' in df.columns else pd.Series([False]*len(df))
print('pruning legacy rows:', int(mask.sum()))
df_keep = df[~mask]
buf=io.BytesIO(); df_keep.to_parquet(buf, index=False, engine='pyarrow'); buf.seek(0)
s.upload_bytes(buc, '_index/availability_index.parquet', buf.read())
print('kept:', len(df_keep))
PY
```

### Gate 5 runbook (vm-ml — can chain after Gate 4; keys are SORTED, scope is bounded refactor)

```bash
# 1. Read the existing handler + decide modernize vs split per docs/DEFI_DOWNLOAD_STRATEGY.md
cd ~/code/market-tick-data-service
sed -n '1,80p' market_tick_data_service/cli/handlers/solana_defi_handler.py
sed -n '350,420p' docs/DEFI_DOWNLOAD_STRATEGY.md
# 2. The handler must write canonical SPLIT-bucket paths with the new instrument_types
#    (matches Gates 1/1.5 + the just-migrated history layout):
#       lending  → instrument_type=solana_lending  → lending-indices-central-element-323112
#       Kamino vault → instrument_type=solana_vault     → dex-pools-central-element-323112
#       Orca/Raydium AMM → instrument_type=solana_amm_pool → dex-pools-central-element-323112
#    Use get_write_bucket_name("lending-indices") / ("dex-pools") and build_instrument_id with
#    InstrumentType.SOLANA_LENDING / SOLANA_VAULT / SOLANA_AMM_POOL.
# 3. Smoke against Helius (creds in Secret Manager: helius-api-key + solana-paper-keypair-private-key):
#    one-day live capture per (venue, data_type) → confirm rows land in canonical buckets, manifest captures.
# 4. Re-enable the recurring DeFi schedule for Solana (collection stopped 2026-04-14). Composes with the
#    deployment-service/terraform/gcp/defi_collection_scheduler.tf scheduler.
# 5. QG green MTDS (handler is currently excluded from a QG check at scripts/quality-gates.sh:25 — bring it back in).
```

### Gate 6 (after Gates 3+4+5 GREEN)

Edit `plans/active/issues/defi_code_codex_drift_2026_05_27.md` D2 row + todo → `[x] ✅ RESOLVED 2026-05-28` citing
UAC@7e9f4ad9 + UAC@90b2bb9d + MTDS@c38d1ca3 + the MTDS Gate-5 sha + the GCS migration log URI. Flip all gates in this
plan. Commit + push via the standard `docs(plans):` flow.

## Status log

- 2026-05-27: Audit complete; operator authorized distinct-instrument_type model + full-chain execution.
- 2026-05-28: Gates 0/1/1.5/2-script shipped from operator laptop (UAC@7e9f4ad9 + UAC@90b2bb9d + MTDS@c38d1ca3); 2,107
  shards migrated via local tmux smoke; operator closing laptop → full Gate-2 run + Gates 3/4/6 handed off to vm-ml.

## AGENT-AUTO dispatch — remaining work (operator off-laptop 2026-05-28T13:18Z)

> Any orchestrator agent: pick up any unticked `- [AGENT-AUTO]` item below. Self-contained specs; in-flight VMs
> identified for monitoring. Don't double-launch — pre-check `gcloud compute instances list --filter="status=RUNNING"`.
> Cite repo@sha + VM name when flipping.

### In-flight (MONITOR + verify on completion — no relaunch unless they exit non-zero)

- [~] [IN-PROGRESS] [VERIFY] [AGENT-AUTO] P0. **`mdps-backfill-defi-20260528-071130`** — MDPS reprocess over
  2024-05-06→2026-01-17 closing the ~40,240 `SCHEMA_VALIDATION_FAILED` rows (UNISWAP_V3-ETHERNET 28,634 + 11
  companions). Verify on completion: MTDS DeFi manifest `attempted_failed` count for UNISWAP_V3-ETHEREUM drops from
  28,634 to <100; same for UNISWAP_V2-ETHEREUM (3,444), AAVEV3-OPTIMISM (2,820), EIGENLAYER (1,311), CURVE-ETHEREUM
  (1,281), MAKER (1,113), FRAX (1,032), COMPOUND_V3-BASE (300), DRIFT-SOLANA (200), KAMINO/JITO/MARGINFI (~75 each).
  MDPS fix already on LDR: `market-data-processing-service@7f1a5b5` + `@3799c8d`. **STATUS 2026-05-28 21:30 UTC**: VM
  still RUNNING (asia-northeast1-c). Per-VM shard: 35,701 entries (captured=10,596 via `venue=UNISWAP_V3`,
  empty_confirmed=24,878, attempted_failed=269). VM currently processing 2024-09-27 (145/620 dates, ~23% of date range).
  Note: successful captures write `venue=UNISWAP_V3` (not chain-qualified), so consolidated manifest's
  `UNISWAP_V3-ETHEREUM` legacy entries won't auto-drop — residual 132 `UNISWAP_V3-ETHEREUM` failures
  (2024-06-11→2024-09-27) represent truly un-fixable schema cases. Plan's "<100 UNISWAP_V3-ETHEREUM" criterion needs
  revision: post-VM the right check is `venue=UNISWAP_V3` captured count for 2024-05-06→2026-01-17 ≥ expected. Estimated
  completion: ~48h from 2026-05-28 21:30 UTC.
- [x] ✅ [VERIFY] [AGENT-AUTO] P0. **`mtds-solana-defi-backfill`** — `collect-solana-defi` for
      MARGINFI/SOLEND/KAMINO/KAMINO_LENDING/RAYDIUM/ORCA/PHOENIX/JITO over 2025-01-17→2026-05-28 (~498 dates). ETA
      ~58min from launch (~13:07 UTC). Verify on completion: MTDS DeFi manifest last_captured moves from 2025-01-17 to
      ~2026-05-28 for MARGINFI/SOLEND/KAMINO/RAYDIUM/ORCA. Note: Kamino vault-strategies path WILL fail per Bug-K below
      — retry after fix. **VERIFIED 2026-05-28**: VM self-deleted (VM_SHUTDOWN_ON_COMPLETION=true).
      market-data-tick-defi manifest: MARGINFI=527 rows last_captured=2026-05-28 ✅; SOLEND=526 last_captured=2026-05-28
      ✅; KAMINO=1,092 last_captured=2026-05-28 ✅; RAYDIUM=728 last_captured=2026-05-28 ✅; ORCA=741
      last_captured=2026-05-28 ✅. Kamino vault=0 captured (Bug-K pool_id mismatch — expected). JITO=0 captured (Bug-J
      Stakenet API — expected). Data wrote to unified defi bucket (wrong-bucket per Gate-7 scope; migration pending).

### Bug fixes (CODE P1 — relaunch the affected backfill after each fix ships)

- [x] ✅ [CODE] [AGENT-AUTO] P1. **Bug-D (Drift S3 archive cutoff)** — handler code shipped mtds@9a840e01; sig index gap
      FILLED (3547+876 parts, 2024-10-31→2026-05-29 continuous) 2026-05-30T09:36Z per SANITY_CHECK; OOM fix shipped
      mtds@93acab3 (pyarrow filter pushdown). Original fix MTDS@fc7e0636. **2026-05-30 sig index audit (slot-1)**:
      `_index/drift_v2_sig_index_parts/` has 2936 parts covering 2026-02-15→2026-05-28 (HEAD end);
      `_index/drift_v2_sig_index_parts_b/` has 876 parts covering 2024-10-31→2025-01-14. **GAP: 2025-01-14→2026-02-15
      (13 months) not in either index set.** Backfill VM ran 2026-05-29 (exit 0) but silently returned 0 rows for all
      dates in gap rather than "sig index missing" (handler fell through to "program activity quiet" branch for dates
      with no index hits). Consequence: dates 2025-01-09→2026-02-14 wrote empty/zero records — not actually missing
      data. **Relaunch BLOCKED** until index gap filled. **2026-05-30T09:36Z UPDATE (slot-1 on tab-1)**: SANITY_CHECK
      PASSED — `_index/drift_v2_sig_index_parts/` 3547 parts + `_index/drift_v2_sig_index_parts_b/` 876 parts;
      total_rows=442,205,000; blocktime range 2024-10-31→2026-05-29 (gap NOW FILLED — Builder #1 + #2 both completed).
      VM launched 2026-05-30T10:06Z but OOM'd at 10:07Z (handler loaded all 4423 parts into RAM simultaneously — ~35-70
      GB RSS). **OOM fix shipped 2026-05-30 (mtds@93acab3, slot-2)**: `_load_drift_v2_sig_index` rewritten with pyarrow
      row-group filter pushdown — only parts overlapping the target date window are decoded. Peak RSS: ~15 MB. 63/63
      tests green. **Operator action**: relaunch backfill VM via
      `launch-mtds-solana-drift-backfill-vm.sh --start 2025-01-09 --end 2026-05-28`. Root cause **CONFIRMED** by slot-1
      probe 2026-05-29: `drift-historical-data-v2.s3.eu-west-1.amazonaws.com` has NO `market/*` prefix entries at all
      (verified via S3 ListBucket: `prefix=market` → 0 keys; the only populated prefix is
      `program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/` with per-authority sub-paths). The legacy
      `_backfill_drift_s3_date` per-date HTTP gets at
      `market/<sym>/{fundingRateRecords,     tradeRecords}/<yyyy>/<yyyymmdd>` were always 404-ing post-V1; the
      `EXPECTED_PAST_SOURCE_COVERAGE_END` empty-record masked that. **NOT BLOCKED-CREDENTIALS** (corrected): operator
      confirmed `helius-api-key` in Secret Manager covers Drift V2 program — verified via slot-1 probes (getVersion →
      200; Helius v0 parsed-history `/v0/addresses/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/transactions` returns
      pre-decoded Drift transactions with `type=DEPOSIT/PERP_TRADE/...` + `source=DRIFT`). **Fix**: replaced the
      `EXPECTED_PAST_SOURCE_COVERAGE_END` branch in `_backfill_drift_s3_date` with a dispatcher into new
      `_backfill_drift_helius_date` method (loads `helius-api-key` via UTL `get_secret_client`, paginates Helius v0 with
      `before=<sig>` cursors, filters to target-day UTC window, writes canonical `perp_funding` parquet to the existing
      hive path). **Schema-mapping note** (in method docstring): Helius parsed-history is signature-level metadata, NOT
      decoded Drift V2 funding rates — the exact V1 S3 schema (`fundingRate24h`, `oraclePrice`, ...) is unrecoverable
      from Helius alone without bundling the Drift V2 Anchor IDL decoder. Rows carry
      `data_quality="helius_v2_signatures_only"` + extension columns
      (`helius_signature/slot/tx_type/fee_lamports/description/source`). Live `/stats/markets` snapshot path remains the
      canonical funding-rate source; this fix unblocks the historical date range for the carry_staked_basis backtest
      signal. Unit tests in `TestBackfillDriftHelius` cover all 4 dispatch paths (S3 vs Helius; missing key; empty page;
      success). **Sub-evidence**: test fixture corrected (mtds@05cc05b0) — in_range_ts was 1779200000 (May-19 actual)
      labelled as May-20 in comment; bumped to 1779260000. QG green. Re-run via
      `launch-mtds-solana-drift-backfill-vm.sh --start 2025-01-09 --end 2026-05-28` only AFTER Bug-D-followup fix below.
  - [x] ✅ [CODE] [AGENT-AUTO] P0. **Bug-D-followup (Helius integration emits 0 rows for active days)** — handler
        shipped mtds@9a840e01; awaiting index build at `gs://<market-data-bucket>/_index/drift_v2_sig_index.parquet`
        (running on vm-ml; multi-hour). Drift V2 density discovered higher than prior estimate (~1.6M sigs/day at April
        2026 peak); index build size + duration TBD. Shipped via Option 2 (persistent sig->blockTime index). **Probe
        results** (slot-1 2026-05-29): Option 1 (Helius v0 time-range params) FAILS —
        `startTime/endTime/from/to/minTime/maxTime` silently ignored (always return HEAD-anchored page); only `until`
        returns 400 "invalid query parameter". Option 3 (Drift V2 S3 archive) FAILS — bucket `drift-historical-data-v2`
        confirmed ends 2025-01-07 via ListObjectsV2 (last key
        `program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/market/SOL-PERP/tradeRecords/2025/20250107`; any
        `start-after=20250108` returns 0 keys). Option 2 wins architecturally; cost amortised as one-time index build
        per operator insight (on-chain data is append-only). **Implementation**: new script
        `market_tick_data_service/scripts/build_drift_v2_sig_index.py` walks Helius RPC `getSignaturesForAddress`
        HEAD→inception and persists `(signature, slot, blockTime)` tuples to
        `gs://<market-data-bucket>/_index/drift_v2_sig_index.parquet` (idempotent forward catch-up on re-run).
        `_backfill_drift_helius_date` rewritten to (1) load+cache the index per-process via UTL `download_bytes`, (2)
        filter by `[day_start_ts, day_end_ts]`, (3) batch-resolve in-window sigs via Helius `POST /v0/transactions` (100
        sigs/batch). Per-day cost: O(target_day) — 1 cache hit + N/100 batch calls. Tests
        `test_helius_no_sigs_in_window_records_empty` + `test_helius_missing_index_records_failed` +
        `test_helius_with_in_range_sigs_writes_parquet` cover all 3 paths (in-window, out-of-window-but-index-present,
        index-missing). QG green exit 0. **Volume side-finding (P3)**: Drift V2 program-level signature density is much
        higher than the operator brief estimated — at peak (e.g. 2026-04-01) a single day has > 1.6M signatures
        (observed in slot-1 build attempt walking 1275 pages all oldest=2026-04-01). Full back-walk to 2024-11-01 will
        produce a multi-GB parquet over many hours of RPC paging (initial build NOT yet uploaded to GCS — operator/cron
        run needed). Architecture degrades gracefully: handler emits
        `record_failed("sig index missing — run build_drift_v2_sig_index.py")` when index absent. **Operator action
        required before relaunching backfill VM**: run
        `python -m market_tick_data_service.scripts.build_drift_v2_sig_index --back-to 2024-11-01` (estimate: several
        hours; idempotent — safe to interrupt and resume; persistent across calls). Once index lands at
        `gs://market-data-tick-defi-central-element-323112/_index/drift_v2_sig_index.parquet`, relaunch via
        `launch-mtds-solana-drift-backfill-vm.sh --start 2025-01-09 --end 2026-05-28`. **slot-9 confirm 2026-05-29**:
        all 6 `TestBackfillDriftHelius` tests green; checkbox flipped.
- [x] ✅ [CODE] [AGENT-AUTO] P1. **Bug-G (Solana gas chain mapping)** — fixed both sides 2026-05-29.
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh:1102` now passes `--gas-fee-chains solana` sentinel
      (deployment-service@3e83f30); `market_tick_data_service/cli/handlers/gas_fee_handler.py` accepts the sentinel and
      gates `solana_enabled` on it (was hardcoded False) (MTDS@c3ae794c). Relaunch via
      `launch-mtds-solana-gas-backfill-vm.sh --start 2025-01-17 --end 2026-05-28` after tarball rebuild.
- [x] ✅ [CODE] [AGENT-AUTO] P1. **Bug-M (Marinade date-filter)** — fixed 2026-05-29 (MTDS@c3ae794c). Marinade's
      official `/msol/apy/365d` and `/msol/price_sol` endpoints don't honour date filters (per slot-1 probe 2026-05-29 —
      both return the current snapshot regardless of `from_date`/`to_date`). `_collect_marinade` now accepts
      `target_date_str` and for past dates routes through `_collect_marinade_historical` (DeFiLlama yields chart, pool
      `b3f93865-5ec8-4662-90a0-11808e0aa2bd`, daily APY back to 2025-02-26). Pre-2025-02-26 = honest empty (DeFiLlama
      coverage start). Re-run via `launch-marinade-solana-backfill-vm.sh 2025-01-17 2026-05-28` after tarball rebuild.
- [x] ✅ [CODE] [AGENT-AUTO] P1. **Bug-K (Kamino pool_id mismatch)** — fixed 2026-05-29 (MTDS@c3ae794c).
      `_collect_kamino` now emits both `pool_id` (aliased from the vault PDA `address`) and `vault_address` so the
      dex_pools `DEFI_POOL_DEX_POOLS` SchemaContract validates while preserving the vault-flavour dimension. Also added
      `token_a`/`token_b` from the resolved Solana mint symbols (required-nullable on the EVM contract). Re-run via
      scoped `collect-solana-defi --solana-protocols kamino` over 2025-01-17→2026-05-28 after tarball rebuild.

### Lower-priority bugs (capture-then-fix; no immediate backfill blocker)

- [x] ✅ [CODE] [AGENT-AUTO] P2. **Bug-J (JITO Stakenet API `pool_token_supply=0`)** — fixed 2026-05-29 (MTDS@c3ae794c).
      Root cause = API drift, NOT auth/tier issue. Jito's Stakenet API
      (`kobe.mainnet.jito.network/api/v1/stake_pool_stats`) shape changed from a single object with
      `pool_total_lamports`+`pool_token_supply` to a time-series payload with `apy[]`/`tvl[]`/`supply[]`/
      `num_validators[]`/`mev_rewards[]` arrays (each `{date, data}`). The endpoint returns only the latest ~8 days and
      ignores `?from=`/`?to=`/`?range=` filters. Rewrote `_collect_jito` to consume the latest entry of each series
      (exchange_rate = tvl_lamports/1e9 / supply_jitosol). Added `_collect_jito_historical` for past dates via DeFiLlama
      yields chart for the jito-liquid-staking JITOSOL pool (`0e7d0722-9054-4907-8593-567b353c0900`). No credential ask
      needed.
- [x] ✅ [CODE] [AGENT-AUTO] P2. **Bug-A (Aave lending-indices subgraph `marketDailySnapshots` field-missing)** — fixed
      2026-05-29 (UAC@15e67b93). Root cause confirmed via authenticated graph-api-key probes 2026-05-29: the
      github-README deployment `DSfLz8oQBUeU5atALgUFQKMTSYV9mZAVYp4noLSXAfvb` is schema-valid (has
      `reserveParamsHistoryItems` AND `reserves`) but contains ZERO entries at any timestamp despite being head- indexed
      (`_meta.block.number=152230969`, ts=1780060715; `reserves(first:5)` → []). The Messari `marketDailySnapshots`
      field absence on this deployment was the cascade's second-variant fingerprint — Bug-A reported it but the
      underlying issue was the empty native deployment. Swapped OPTIMISM in `SUBGRAPH_IDS["aave_v3"]` to
      `3RWFxWNstn4nP3dXiDfKi9GgBoHx7xzc7APkXs1MLEgi` (Messari-style deployment; populated history through 2024-09-11).
      The existing lending_indices cascade now resolves OPTIMISM via the `messari_lending` variant on second try. **NOT
      BLOCKED-CREDENTIALS** — was a subgraph-deployment-ID bug; existing `graph-api-key` Secret Manager entry works
      fine. Backfill re-run: launched `mtds-aave-optimism-backfill` covering attempted_failed/empty_confirmed dates;
      T+10min verify per plan.
- [x] ✅ [CODE] [AGENT-AUTO] P1. **Bug-A AAVE_V3-OPTIMISM follow-up — direct-RPC fallback shipped 2026-05-29
      (MTDS@119056a6)**. The earlier Messari-subgraph swap (Bug-A above) was correct in shape but the Messari deployment
      `3RWFxWNstn4nP3dXiDfKi9GgBoHx7xzc7APkXs1MLEgi` stopped indexing 2024-09-11, so 2025+ OPTIMISM days still came back
      empty — both subgraph variants (github-README + Messari swap) return 0 honest rows for 2025+. Added a 3rd-tier RPC
      fallback to `lending_indices_handler.py::_fetch_aave_v3_via_rpc` that reads `getReserveData(asset)` directly from
      the on-chain Pool `0x794a61358D6845594F94dc1DB02A252b5b4814aD` via the existing `alchemy-api-key` Secret Manager
      entry + `AlchemyBaseClient`. Reserve list comes from `AaveProtocolDataProvider.getAllReservesTokens()`. Output
      schema matches `_parse_aave_v3` exactly so no downstream diff. Sync `web3` calls wrapped in `asyncio.to_thread` to
      preserve the async loop. 8-chain coverage (ETH/ARB/OP/POLY/AVAX/BASE/BSC/LINEA). Verified locally: OPTIMISM @
      2026-01-15 returns 14 rows / 13 reserves with non-zero indices (USDC liquidity_rate=1.75%, WETH=0.93%,
      WBTC=0.018%). **NOT BLOCKED-CREDENTIALS** — uses the existing `alchemy-api-key` Secret Manager entry already in
      use by `aave_positions.py`. QG-green (only pre-existing foreign-file failure
      `test_solana_defi_handler.py::TestBackfillDriftHelius` remains). — + operational verify 2026-05-29T17:27Z:
      manifest cleaned (320 rows rewritten `empty_confirmed`→`expected_unattempted` across 4 per-VM shards via
      `/tmp/li_clean/scripts/clean_aave_op_empty_rows.py` on agent-orch-vm-ml) + tarballs rebuilt @ mtds@2e86a76 (DEFI
      scope, includes 119056a6 RPC fallback) + retry VM `mtds-lending-indices-20260529-171631` (asia-northeast1-c)
      launched RUNNING T+10min verified — log evidence: `aave_v3/OPTIMISM: direct-RPC fallback succeeded (14 rows)`
      writing to `lending-indices-central-element-323112/raw_tick_data/.../venue=AAVE_V3/chain=OPTIMISM/`. Bonus
      discovery: AAVE_V3-LINEA also had subgraph-empty; same RPC fallback now hydrates LINEA (9 rows/day).
- [x] ✅ [CODE] [AGENT-AUTO] P3. **Bug-R (GCS 429 rate-limit on per-VM manifest shard start)** — fixed 2026-05-29
      (UTL@cb1f4b5f). `_write_per_vm_shard` now routes upload through `_upload_with_backoff_on_429` — 3 retries at
      1s/2s/4s base ±30% jitter on `429`/`rateLimitExceeded`/`TooManyRequests`; non-429 errors re-raise immediately.
      Outer `write()` `try/except` still swallows the final raise so manifest writes stay best-effort. Unit tests cover
      all 4 classification paths + retry semantics in `tests/unit/test_manifest_writer_429_backoff.py`.

### Hardening — subgraph silent-data-loss + AAVE OP follow-ups

- [x] ✅ [DOCS] P3. **AAVE_V3-OPTIMISM `_defi.py` comment refresh — 2026-05-30 (uac@9f2da8d3)**. The previous comment
      said "Coverage: 2022 → 2024-09-11 (subgraph stops indexing past that)" — wrong. Re-verified 2026-05-30: both the
      Aave github-README deployment `DSfLz...` and the Messari deployment `3RWFx...` are AT HEAD with
      `hasIndexingErrors:false`, but Aave silently republished `DSfLz...` to an empty v0.0.5 between 2026-05-08 and
      2026-05-29 (both `reserveParamsHistoryItems` AND `reserves` return `[]`). Messari deployment has sparse
      post-2024-12 coverage and a broken `market{inputToken{symbol}}` join. Comment now captures the actual abandonment
      pattern + records that RPC fallback is the canonical primary path until a fresh rich deployment surfaces.
- [x] ✅ [INFRA] P2. **Subgraph silent-data-loss probe shipped — 2026-05-30 (mtds@cef599e3 +
      deployment-service@8f2a83c + alerting-service@b6cbb2f; TF applied deployment-service@ff0ad29 2026-05-30T09:00Z)**.
      Daily cron at `0 */6 * * *` UTC (Cloud Run Job `uts-prod-subgraph-health-probe` + Cloud Scheduler
      `uts-prod-subgraph-health-probe-cron`) probes every `(protocol, chain)` in `SUBGRAPH_IDS` for HEAD_LAG (>6h stale
      block) + EMPTY_YESTERDAY (zero rows yesterday UTC) + DEPLOYMENT_CHANGED (IPFS hash differs from fingerprint stored
      at `gs://<lending-indices-bucket>/_index/subgraph_fingerprints/fingerprints.parquet`) + SCHEMA_INVALID. Alerts
      publish to the new `defi_data_quality_alerts` Pub/Sub topic; alerting-service subscribes + routes via the existing
      PagerDuty/Slack router. Per-cell errors are isolated (shard-level failure isolation HARD RULE) — one bad probe
      never aborts the sweep. Protects against the silent republish pattern that hit AAVE_V3-OPTIMISM 2026-05-08→29. 16
      unit tests cover signal detection + fingerprint round-trip + alert payload shape + per-cell crash isolation.
      **Resources created 2026-05-30**: `google_pubsub_topic.defi_data_quality_alerts` +
      `google_cloud_run_v2_job.subgraph_health_probe` + `google_cloud_scheduler_job.subgraph_health_probe_cron` + 2 IAM
      bindings on `t1_batch` SA. Targeted apply used vars
      `project_id=central-element-323112 environment=prod     bucket_prefix=uts`. **First execution 2026-05-30T09:20Z
      (job ID `uts-prod-subgraph-health-probe-g4827`) FAILED exit=127** — container exited before producing logs. Likely
      entrypoint runtime issue (`cron_subgraph_health_probe_entrypoint.sh` install/import failure) — pre-existing in
      mtds@cef599e3 + deployment-service@8f2a83c shipped 2026-05-29. **Entrypoint + probe runtime fixes shipped
      2026-05-31** (mtds@e431e483 + deployment-service@ba635bf): (1) `_load_fingerprints` / `_write_fingerprints` were
      calling non-existent `download_blob_to_file` / `upload_blob` methods on `GCSStorageClient` — fixed to use the
      canonical UTL protocol methods `download_bytes(bucket, blob_path)` /
      `upload_bytes(bucket, blob_path, data, content_type=None)` (the AttributeError at line 451 was the actual cause of
      the post-127 exit-1 runs visible 2026-05-30T15:01Z onward). (2) `uts-prod-batch-sa` lacked Storage Object Admin on
      `gs://lending-indices-central-element-323112`; ad-hoc grant applied + made durable via new TF binding
      `google_storage_bucket_iam_member.t1_batch_lending_indices_object_admin`. (3) Entrypoint cleaned up: `python3 -u`
      for unbuffered stdio + 2s post-flush sleep + stderr routing for diagnostics (Cloud Run gen2 +
      `google-cloud-cli:slim` + `command=bash, args=-c` silently drops container STDOUT from Cloud Logging — confirmed
      against sister `orphan-ping-audit` job which also emits zero entrypoint stdout). Verified:
      `gcloud run jobs execute uts-prod-subgraph-health-probe` exits 0 in 1m20s (execution
      `uts-prod-subgraph-health-probe-lbxrp` 2026-05-31T10:41Z) and writes the 7.65 KB fingerprints parquet to
      `gs://lending-indices-central-element-323112/_index/subgraph_fingerprints/fingerprints.parquet`.
- [x] ✅ [INFRA] P2. **`vm_log_archival_scheduler.tf` SA refs unblocked workspace TF apply — 2026-05-30
      (deployment-service@40e85ef → rebased ff0ad29)**. Adjacent fix surfaced during the subgraph-probe TF apply:
      `vm_log_archival_scheduler.tf` referenced `google_service_account.unified_trading_sa` +
      `google_service_account.t1_batch_sa` (neither declared — canonical names are `unified_trading` from main.tf:1429 +
      `t1_batch` from t1_batch_scheduler.tf:38). Every `terraform plan/apply` against `terraform/gcp/` was failing
      before any `-target=` resolution. Fixed in same session per Findings Triage.
- [x] ✅ [POLICY] P3. **AAVE_V3-OPTIMISM canonical data source = RPC fallback (decision recorded 2026-05-30)** — Aave
      team abandoned the OP subgraph deployment (silently republished `DSfLz...` to empty v0.0.5 between 2026-05-08 and
      2026-05-29). No rich subgraph alternative exists. Messari `3RWFx...` kept as the cascade's 2nd variant for partial
      coverage. Native subgraph variant kept in the cascade for the day Aave revives the deployment. If a new rich
      deployment surfaces: swap `SUBGRAPH_IDS["aave_v3"]["OPTIMISM"]` to its ID + re-backfill the affected date range.
      Operationally: 14-row daily-resolution RPC data is sufficient for the carry archetype.
- [x] ✅ [CODE] P3. **Multi-parquet-per-day consolidator shipped — 2026-05-30 (mtds@16785fb6)**. Sweeps a
      hive-partitioned DeFi bucket and groups by `(day, asset_group, venue, chain, instrument_type, data_type)`; for
      each shard with ≥2 parquets picks the row-count-maximizing winner (tiebreakers: cols → newest write time) and
      archives losers to `raw_tick_data/_archive/multi_parquet_consolidator/<original-hive-path>/<filename>`. Reads
      parquet METADATA only (`pq.read_metadata`) — no full-row materialization. Per-shard failure isolation absorbs
      transient GCS errors without aborting the sweep. CLI:
      `python scripts/consolidate_multi_parquet_per_day.py --bucket <name> [--asset-group X --venue X --chain X     --days-from YYYY-MM-DD --days-to YYYY-MM-DD] [--apply]`
      — `--dry-run` is the default. Uses `unified_trading_library.cloud_interface.gcs_copy_object` / `gcs_delete_object`
      per GCS-ops SSOT. Writes a per-run audit parquet at
      `_index/multi_parquet_consolidator_runs/run_<ts>_<applied|dryrun>.parquet`. Unit tests
      (`tests/unit/scripts/test_consolidate_multi_parquet_per_day.py`, 9 tests) cover row/col/timestamp winner
      selection + archive path mapping + day-range filter + `_parse_path` hive-key extraction + dry-run no-op +
      per-shard failure isolation. **Dry-run preview kicked off for AAVE_V3-OPTIMISM lending_indices** 2026-05-30T10:43Z
      (preview output pending — bucket has 47,983 parquets; full sweep walks all → ~15-20min); summary will land in
      `gs://lending-indices-central-element-323112/_index/multi_parquet_consolidator_runs/run_<ts>_dryrun.parquet`.
      **`--apply` pending operator review** of the dry-run output (operator instructions: "Don't run --apply yet … so
      operator can review the impact before executing"). Affects AAVE_V3-OPTIMISM dates 2025-01-01 → 2026-05-28 (~320
      dates with co-existing rich May-08 parquets + sparse May-29 RPC parquets).

### Pre-existing (carry-over, lower urgency)

- [x] ✅ [CODE] [AGENT-AUTO] P3. **PACIFICA** is CeFi perp (not Solana DeFi) — coverage routes via CeFi perp pipeline
      (`unified_api_contracts/registry/cefi_perp_venue_endpoints.py`). Verify PACIFICA has current MTDS coverage via the
      CeFi path; if stale, file in CeFi backfill plan. — Verified 2026-05-30: PACIFICA has full CeFi perp coverage via
      MTDS `perp_funding_handler.py` (line 90 in DEFAULT_PROTOCOLS; `_collect_pacifica()` at line 962;
      `_PACIFICA_FUNDING_START_DATE = "2025-06-01"`). UAC registry confirms `PACIFICA-SOLANA: ["perp_funding"]` in
      expected_coverage.py. `umi_tick_provider._fetch_pacifica_rest()` routes via `api.pacifica.fi/api/v1` (CeFi REST),
      NOT Solana on-chain DEX path. No code change needed.

### Done-when

1. All 4 P1 bugs (D/G/M/K) shipped to LDR with QG-green commits.
2. Affected backfills re-run; MTDS DeFi manifest shows:
   - UNISWAP_V3-ETHEREUM `attempted_failed` < 100 (was 28,634).
   - DRIFT/MARGINFI/SOLEND/KAMINO/MARINADE/RAYDIUM/ORCA last_captured ≥ 2026-05-20.
3. Findings flipped with repo@sha + VM names.
4. Operator (slot-1 main) pinged on completion via `ikenna_orchestrator/pings/slot_1.md`.
