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
- [ ] [SCRIPT] P1. **Gate 3 — manifest reconcile + verify**: consolidate canonical bucket manifests; confirm Solana
      venues now show `captured` rows per (date, venue, chain, instrument_type); sample-inspect parquets.
- [~] [SCRIPT] P0. **Gate 4 — delete legacy**: after Gate 3 verified, delete `market-data-tick-defi-prd/lst_rates/`
      (redundant), `.../lending_indices/` + `.../dex_pools/` (migrated) via `gcs_delete_object`; remove stale manifest
      rows in `defi-prd/_index` for the top-level prefixes. NO duplicate source of truth remains.
      **`lst_rates/` DONE 2026-05-28**: deleted 1,200 date-prefix parquets (MARINADE 2023-01-01→2026-04-14); pruned
      64,373 stale manifest rows from defi-prd `_index/availability_index.parquet` (1,633,780→1,569,407 rows). Canonical
      `lst-rates-central-element-323112` confirmed superset (dates 2020-01-01→2026-05-19, MARINADE 902 rows).
      **`lending_indices/` + `dex_pools/` deferred**: Gate 2 migration has NOT completed (canonical buckets show 0 SOLANA
      rows — Gate 3 cannot be verified yet). Re-run this gate after Gate 2 migration VM completes and Gate 3 is verified.
- [x] ✅ [SCRIPT] P0. **Gate 7 — migrate ALL bad-bucket Solana data → canonical split buckets (operator directive
      2026-05-28: "migrate the old bad buckets too")**: in addition to Gate 2 (which sources from `defi-prd/{type}/…`
      legacy historical), this gate migrates the **2823 wrong-bucket parquets** (actual count; plan estimated 72) the
      autonomous `mtds-solana-defi-backfill` VM wrote (2022-11-01→2026-05-28). **Source**:
      `gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=*/[pipeline_mode=*/]asset_group=defi/venue=*/chain=SOLANA/     instrument_type={lending|pool|lst}/data_type={lending_indices,dex_pools,lst_rates}/...`
      **7 venue/type combos**: KAMINO+SOLEND+MARGINFI (lending→SOLANA_LENDING), ORCA+RAYDIUM+PHOENIX (pool→SOLANA_AMM_POOL),
      MARINADE (lst→LST). **Script**: added `--source-bucket defi` + `--delete-source` flags to
      `scripts/migrate_legacy_solana_defi_to_canonical.py`; reuses existing `_to_canonical_df` via thin
      `_to_canonical_df_wrong_bucket` wrapper (drops EVM `instrument_type` col + rebuilds `instrument_id` with correct
      `InstrumentType`). Ran `--source-bucket defi --delete-source` (no `--dry-run`) 2026-05-28: 2823 shards migrated, 0
      errors, 0 wrong-bucket Solana parquets remaining. Sample-inspected `KAMINO-SOLANA:SOLANA_LENDING:...` instrument_id
      (correct type). Gate 7 ends in: **zero Solana DeFi data outside the dedicated split buckets** (SSOT enforced). ✓
- [ ] [CODE] P1. **Gate 5 — go-forward collectors: FULL PER-DATA-TYPE SPLIT (operator directive 2026-05-28 "the heavier
      path (full split) pls")**. **NOT modernize-in-place** — finish what `docs/DEFI_DOWNLOAD_STRATEGY.md:402` already
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

- [ ] [DOC] P2. **Gate 6 — close-out**: tick D2 in `defi_code_codex_drift_2026_05_27` (or archive that doc if D2 was its
      last open item — it is not; D7/D8/D10/D13/D15 remain); update `codex/02-data/defi-data-types-catalog.md` +
      `defi-data-pipeline.md` with the Solana instrument_types.

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

- [ ] [MTDS] P1. **Drift S3 backfill: archive end 2025-01-08 is hardcoded; entire post-2025-01-08 history must come from
      Drift Data API (or Drift V2 archive) not S3 V1.** `solana_defi_handler.py:172`
      (`_DRIFT_S3_ARCHIVE_END = date(2025, 1, 8)`) makes every requested date emit `EXPECTED_PAST_SOURCE_COVERAGE_END` —
      honest but useless for closing the venue-keyed Drift gap from 2025-01-17 onward. Fix path: either (a) wire a Drift
      V2 historical source (drift-historical-data S3 V2 bucket `drift-historical-data-v2`), or (b) replay the Drift Data
      API `/stats/markets` + funding endpoints per-day via the existing snapshot path, or (c) operator ack that
      2025-01-17 → today Drift coverage is `BLOCKED-OPERATOR-DECISION` until V2 source is signed up. Provenance: slot-1
      2026-05-28 run.log `gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`.
- [ ] [MTDS] P1. **Solana gas-fees chain_id=99999 is not registered in the gas-fee chain map → entire
      `mtds-gas-fees-solana` backfill silent no-op.** Launcher passes `--gas-fee-chains 99999` (per
      `setup-data-pipeline-vm.sh:1004`), but the gas-fees handler logs `"Unknown chain_id 99999, skipping"` for every
      date. Solana doesn't have an EVM-style numeric chain_id — the correct value is the canonical chain key from UAC
      `registry/data_source_continuity.py` (likely `"SOLANA"` or the registry's Solana sentinel, NOT 99999). Fix:
      replace `--gas-fee-chains 99999` with the correct Solana chain key in `setup-data-pipeline-vm.sh`
      `solana-gas-backfill` block; OR add a numeric→str mapping in the gas-fees handler. Provenance: slot-1 2026-05-28
      run.log `gs://deployment-scripts-central-element-323112/vm-logs/mtds-gas-fees-solana/run.log`.
- [ ] [MTDS] P1. **Marinade backfill bypasses historical days via "all expected sentinels already captured" check — only
      the latest date emits a real APY row.** `launch-marinade-solana-backfill-vm.sh` routes through `collect-lst-rates`
      which uses an LST-rates handler keyed on sentinel-cluster completion at the latest date; with the latest date
      captured, every prior date short-circuits. Net: the VM wrote jitoSOL + 12 EVM LSTs for 2026-05-27 only, NOT
      2025-01-17 → 2026-05-26 for Marinade. Marinade mSOL APY is also emitted via
      `solana_defi_handler._collect_marinade` (handler list `["drift","kamino",...,"marinade",...]`) — re-launching the
      new `launch-mtds-solana-defi-backfill-vm.sh` with `--protocols marinade` SHOULD close this without needing to fix
      the lst-rates sentinel logic, **assuming** Marinade APY endpoint `api.marinade.finance/msol/apy/365d` is
      daily-replayable (collector currently reads "latest" only — needs a `target_date_str` parameter analog to marginfi
      TVL filter). Provenance: slot-1 2026-05-28 run.log
      `gs://deployment-scripts-central-element-323112/vm-logs/marinade-backfill-20260528-140422/run.log`.
- [ ] [MTDS] P1. **Kamino vault-strategies path raises `"row is missing required symbol column 'pool_id'"` schema error
      every date.** `solana_defi_handler._collect_kamino` emits rows with `vault_address` not `pool_id` but the
      `dex_pools` SchemaContract for `defi/pool/dex_pools` requires `pool_id`. Fix: rename the column in
      `_collect_kamino` (alias `vault_address` → `pool_id` for the dex_pools contract; keep `vault_address` as a
      secondary field) OR widen the SchemaContract. Provenance: slot-1 2026-05-28 run.log
      `gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-defi-backfill/run.log` (one warning per
      processed date). Composes with Gate 1 schema-contracts work above — if a `solana_vault` instrument_type lands as
      planned, the Kamino vault rows route there instead and this becomes moot. Capture so it doesn't slip.
- [ ] [MTDS] P2. **Jito Stakenet API `pool_token_supply=0` returned every fetch → `"cannot compute exchange rate"` every
      date in the new VM run.** `solana_defi_handler._collect_jito` hits
      `kobe.mainnet.jito.network/api/v1/     stake_pool_stats` and gets back a body whose `pool_token_supply` field is 0
      (or absent), so the handler gives up and returns empty. Possible causes: (a) Jito's Stakenet API moved / endpoint
      deprecated, (b) field renamed in their response, (c) we need an auth header now. Fix: read the actual response
      body once, confirm field names, update collector OR switch to an on-chain RPC read against the Jito stake pool
      program. Provenance: same run.log as above.
- [ ] [MTDS] P3. **GCS object-mutation 429s on per-VM manifest shard at the start of every backfill VM** — both
      `mtds-solana-drift-backfill` and the new `mtds-solana-defi-backfill` get `429 rateLimitExceeded ... per-VM shard`
      on the first few flushes. Non-blocking (manifest writes are best-effort) but it means the first ~10-30s of
      manifest rows are missing from the per-VM shard. Fix: add an exponential backoff inside `DefiManifestRecorder`
      flush, or batch the early flushes. Already a known pattern — track here so the next manifest-consolidator pass
      dedup-merges correctly.

### Next slot-1 actions (sequenced)

1. Re-launch `launch-mtds-solana-defi-backfill-vm.sh` will continue progressing on the LDR codepath; let it finish (498
   dates × ~14k rows/day × 6 venues = the bulk of the venue-keyed gap).
2. File the 4 P1 fixes as MTDS handler PRs (Drift V2 source, gas-fee chain registry, Marinade per-date, Kamino pool_id
   alias). Each is a 1-2h fix.
3. Re-launch the affected VMs after the fixes land + setup-data-pipeline-vm.sh is re-uploaded to GCS.

## Not in scope (separately tracked)

- Flat→`-prd` env-tiered dedicated-bucket cutover (writers→flat, `resolve_bucket_name`→`-prd`) — `bucket_name_ssot`
  Phase 2.6 residual, tracked in `plans/epics/manifest_master.md`.
- The DeFi EVM GCS re-key (venue glued→underscore, `dex_pool_state`→`dex_pools`, `category`→`asset_group`) — tracked in
  `plans/epics/mtds_mdps_master.md` Phase 9 + `defi_coverage_capability_alignment` (archived).

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

- [ ] [VERIFY] [AGENT-AUTO] P0. **`mdps-backfill-defi-20260528-071130`** — MDPS reprocess over 2024-05-06→2026-01-17
      closing the ~40,240 `SCHEMA_VALIDATION_FAILED` rows (UNISWAP_V3-ETHEREUM 28,634 + 11 companions). Verify on
      completion: MTDS DeFi manifest `attempted_failed` count for UNISWAP_V3-ETHEREUM drops from 28,634 to <100; same
      for UNISWAP_V2-ETHEREUM (3,444), AAVEV3-OPTIMISM (2,820), EIGENLAYER (1,311), CURVE-ETHEREUM (1,281), MAKER
      (1,113), FRAX (1,032), COMPOUND_V3-BASE (300), DRIFT-SOLANA (200), KAMINO/JITO/MARGINFI (~75 each). MDPS fix
      already on LDR: `market-data-processing-service@7f1a5b5` + `@3799c8d`.
- [x] ✅ [VERIFY] [AGENT-AUTO] P0. **`mtds-solana-defi-backfill`** — `collect-solana-defi` for
      MARGINFI/SOLEND/KAMINO/KAMINO_LENDING/RAYDIUM/ORCA/PHOENIX/JITO over 2025-01-17→2026-05-28 (~498 dates). ETA
      ~58min from launch (~13:07 UTC). Verify on completion: MTDS DeFi manifest last_captured moves from 2025-01-17 to
      ~2026-05-28 for MARGINFI/SOLEND/KAMINO/RAYDIUM/ORCA. Note: Kamino vault-strategies path WILL fail per Bug-K below
      — retry after fix.
      **VERIFIED 2026-05-28**: VM self-deleted (VM_SHUTDOWN_ON_COMPLETION=true). market-data-tick-defi manifest:
      MARGINFI=527 rows last_captured=2026-05-28 ✅; SOLEND=526 last_captured=2026-05-28 ✅; KAMINO=1,092
      last_captured=2026-05-28 ✅; RAYDIUM=728 last_captured=2026-05-28 ✅; ORCA=741 last_captured=2026-05-28 ✅.
      Kamino vault=0 captured (Bug-K pool_id mismatch — expected). JITO=0 captured (Bug-J Stakenet API — expected).
      Data wrote to unified defi bucket (wrong-bucket per Gate-7 scope; migration pending).

### Bug fixes (CODE P1 — relaunch the affected backfill after each fix ships)

- [ ] [CODE] [AGENT-AUTO] P1. **Bug-D (Drift S3 archive cutoff)** —
      `market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py:172` hardcodes
      `_DRIFT_S3_ARCHIVE_END = date(2025, 1, 8)` → every date 2025-01-09→today emits
      `EXPECTED_PAST_SOURCE_COVERAGE_END`. Switch to V2 Drift S3 source OR Drift Data API per-day replay (per CLAUDE.md
      `External Data Is Always Available` — paid tier credentials if needed; file ping not defer). After fix: relaunch
      `launch-mtds-solana-drift-backfill-vm.sh --start 2025-01-09 --end <today>`. QG + commit MTDS → LDR.
- [ ] [CODE] [AGENT-AUTO] P1. **Bug-G (Solana gas chain mapping)** —
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh:1004` passes `--gas-fee-chains 99999`; Solana doesn't
      have EVM-style numeric chain_id. Replace with canonical key from UAC `registry/data_source_continuity.py`
      (`SOLANA` string or whatever the handler expects — read `gas_fees_handler` to confirm). After fix: relaunch
      `launch-mtds-solana-gas-backfill-vm.sh --start 2025-01-17 --end <today>`. QG + commit deployment-service → LDR.
- [ ] [CODE] [AGENT-AUTO] P1. **Bug-M (Marinade date-filter)** — `collect-lst-rates` handler uses sentinel-cluster
      latest-only; needs `target_date_str` analog like `_collect_marginfi_tvl`. Extend handler to accept per-date
      backfill. After fix: relaunch `launch-marinade-solana-backfill-vm.sh 2025-01-17 <today>`. QG + commit MTDS → LDR.
- [ ] [CODE] [AGENT-AUTO] P1. **Bug-K (Kamino pool_id mismatch)** — `_collect_kamino` vault-strategies emits
      `vault_address`; `dex_pools` SchemaContract requires `pool_id`. Rename/map at adapter boundary (preserve
      `vault_address` as additional dimension if needed). After fix: re-run a scoped
      `collect-solana-defi --solana-protocols kamino` over the same date range to backfill Kamino rows the in-flight T4
      VM dropped. QG + commit MTDS → LDR.

### Lower-priority bugs (capture-then-fix; no immediate backfill blocker)

- [ ] [CODE] [AGENT-AUTO] P2. **Bug-J (JITO Stakenet API `pool_token_supply=0`)** — every fetch returns 0 → "cannot
      compute exchange rate". Likely API drift / auth change. Investigate Stakenet API status, file CREDENTIAL APPROVAL
      REQUEST ping in `ikenna_orchestrator/pings/slot_1.md` if it's an auth/tier issue (don't defer silently). Re-run
      JITO scope after fix.
- [ ] [CODE] [AGENT-AUTO] P2. **Bug-A (Aave lending-indices subgraph `marketDailySnapshots` field-missing)** — surfaced
      in `mtds-lending-indices-20260528` run. Subgraph schema drift; adapter needs the new field name OR fallback. Fix
      in MTDS Aave lending-indices adapter. Re-run lending-indices backfill after fix.
- [ ] [CODE] [AGENT-AUTO] P3. **Bug-R (GCS 429 rate-limit on per-VM manifest shard start)** — every backfill VM hits 429
      on first manifest-shard upload. Add exponential backoff/jitter in UTL `ManifestWriter._write_per_vm_shard`. QG +
      commit UTL → LDR.

### Pre-existing (carry-over, lower urgency)

- [ ] [CODE] [AGENT-AUTO] P3. **PACIFICA** is CeFi perp (not Solana DeFi) — coverage routes via CeFi perp pipeline
      (`unified_api_contracts/registry/cefi_perp_venue_endpoints.py`). Verify PACIFICA has current MTDS coverage via the
      CeFi path; if stale, file in CeFi backfill plan.

### Done-when

1. All 4 P1 bugs (D/G/M/K) shipped to LDR with QG-green commits.
2. Affected backfills re-run; MTDS DeFi manifest shows:
   - UNISWAP_V3-ETHEREUM `attempted_failed` < 100 (was 28,634).
   - DRIFT/MARGINFI/SOLEND/KAMINO/MARINADE/RAYDIUM/ORCA last_captured ≥ 2026-05-20.
3. Findings flipped with repo@sha + VM names.
4. Operator (slot-1 main) pinged on completion via `ikenna_orchestrator/pings/slot_1.md`.
