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

- [x] ✅ [SCRIPT] P1. **Gate 0 — per-venue schema sample** — DONE 2026-05-27. Kamino+Solend lending = identical 9-col
      APY-snapshot; Kamino dex_pools = vault metadata (10c); Orca (16c) + Raydium (12c) = AMM pool metrics. Confirmed
      3 distinct shapes.
- [x] ✅ [CODE] P1. **Gate 1 — UAC SchemaContracts** — DONE — UAC@7e9f4ad9. Added `DEFI_SOLANA_LENDING_LENDING_INDICES`
      / `DEFI_SOLANA_VAULT_DEX_POOLS` / `DEFI_SOLANA_AMM_POOL_DEX_POOLS` to `contracts.py` + registered in
      `CONTRACT_REGISTRY` under `("defi", solana_lending|solana_vault|solana_amm_pool, lending_indices|dex_pools)`. All
      Solana fields preserved (venue-specific AMM cols nullable+optional). ruff + basedpyright 0; cassette parity 447
      passed.
- [x] ✅ [CODE] P1. **Gate 1.5 — InstrumentType enum + builder dispatch** — DONE — UAC@90b2bb9d. Added
      `SOLANA_LENDING`/`SOLANA_VAULT`/`SOLANA_AMM_POOL` to `InstrumentType` enum + `SUPPORTED_INSTRUMENT_TYPES` allow-list
      + `_DEFI_TYPES` (so `build_instrument_id` produces `VENUE-CHAIN:TYPE:SYMBOL`; e.g.
      `KAMINO-SOLANA:SOLANA_LENDING:<market_id>`). Cassette parity 447 passed.
- [~] [SCRIPT] P1. **Gate 2 — history migration** — SCRIPT SHIPPED + SMOKE VERIFIED, FULL RUN PENDING.
      `market-tick-data-service/scripts/migrate_legacy_solana_defi_to_canonical.py` (MTDS@c38d1ca3) reads legacy
      `defi-prd/{lending_indices,dex_pools}/<venue>/SOLANA/date=*` → writes canonical flat
      `day=/category=defi/venue=/chain=SOLANA/instrument_type=<solana_*>/data_type=*` to `lending-indices-*` /
      `dex-pools-*` (matches EVM canonical layout). Schema map: drops legacy `timestamp` (write-time);
      `ts_event` = midnight UTC of date partition; `instrument_id` via `build_instrument_id`. **Smoke** (2026-05-28,
      1 date × 5 subsets): 14,807 rows migrated; sample parquet read-back clean (instrument_id format verified,
      ts_event correct, all legacy fields preserved); re-run idempotent (5/5 "skip (exists)"). **Remaining**: full
      ~5,995 shards across ~1199 distinct dates (~8–12h sequential at ~3–7s/shard). Best run with `--max-dates` chunks
      or backgrounded on a VM. CLI: `--dry-run` / `--only-protocol` / `--only-data-type` / `--max-dates` for control.
      Manifest emission deferred to Gate 3 consolidator (no explicit per-shard emit in the migration script — the
      consolidator discovers newly-written files).
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

### Gate 6 (after Gates 3+4 GREEN)

Edit `plans/active/issues/defi_code_codex_drift_2026_05_27.md` D2 row + todo → `[x] ✅ RESOLVED 2026-05-28` citing
UAC@7e9f4ad9 + UAC@90b2bb9d + MTDS@c38d1ca3 + the GCS migration log URI. Flip Gates 2/3/4/6 in this plan. Commit + push
via the standard `docs(plans):` flow.

## Status log

- 2026-05-27: Audit complete; operator authorized distinct-instrument_type model + full-chain execution.
- 2026-05-28: Gates 0/1/1.5/2-script shipped from operator laptop (UAC@7e9f4ad9 + UAC@90b2bb9d + MTDS@c38d1ca3); 2,107
  shards migrated via local tmux smoke; operator closing laptop → full Gate-2 run + Gates 3/4/6 handed off to vm-ml.
