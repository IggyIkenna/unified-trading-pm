---
scope: [engineer, admin]
---

# DeFi canonical naming SSOT (data_type · chain · instrument_type · path · bucket)

> **Status: AUTHORITATIVE (operator-locked 2026-06-01).** This is the single source of truth for the DeFi canonical
> wire/storage vocabulary. The DeFi C0 migration (`migrate_defi_full_v9_canonical.py`) writes to these forms; every
> writer/reader/plan/codex listed below MUST converge on them. A surface that diverges is **review-blocking** (it makes
> migrated data unreadable or splits the SSOT). Provenance: the 2026-06-01 naming-alignment audit (codex +
> instruments-service + MTDS handlers + MDPS/features) caught two regressions (data_type + pipeline_mode) before the
> migration applied; the operator then locked the canonical forms and directed "converge on canonical, fix the
> readers/writers + plans + codex — do not bend the migration to legacy."

## Locked canonical forms

| Axis                                                                     | Canonical value(s)                                                                                                                                                    | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Object path**                                                          | `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=defi/venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{file}`                                  | `pipeline_mode=` IS canonical (operator 2026-06-01), inserted after `day=` — the form `candidate_parquet_paths(pipeline_mode=…)` probes first. `mode` ∈ `batch`/`live`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **data_type** (path + column + manifest + handler const + bucket-domain) | `dex_pool_state` (pools), `dex_pool_swaps` (swaps), `lst_rates`, `lending_indices`, `oracle_prices`, `perp_funding`                                                   | **Collapsed to ONE name everywhere** (operator 2026-06-01). The legacy 2-layer split (on-disk `dex_pool_state` vs manifest `dex_pools`) is RETIRED — `dex_pool_state`/`dex_pool_swaps` are canonical at every layer. (Bucket _name_ stays `dex-pools`/`dex-swaps` — that's a bucket id, not the data_type.) **See "dex_pool_state = EVM + Solana union" below.**                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **chain**                                                                | `HYPERLIQUID` (not `HYPERLIQUID_L1`), `ETHEREUM`/`ARBITRUM`/`BASE`/`OPTIMISM`/`POLYGON`/`BSC`/`AVALANCHE`/`SOLANA`/`ZKSYNC`/`SCROLL`/`LINEA`                          | App-chain perps: `HYPERLIQUID→HYPERLIQUID`, `PACIFICA→SOLANA`, `LIGHTER→ZKSYNC`, `ASTER→BSC`, `DRIFT→SOLANA`. UAC `ChainKind.HYPERLIQUID_L1.value` MUST resolve to wire `HYPERLIQUID`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **instrument_type**                                                      | `pool` (dex), `lending`, `lst`, `spot_asset` (oracle), **`perpetual`** (DeFi on-chain perps: Drift/GMX/HL) + Solana `solana_amm_pool`/`solana_vault`/`solana_lending` | **DeFi DOES have perps** (operator 2026-06-01): Drift/GMX/Hyperliquid are on-chain perp DEXs. `instrument_type=perpetual` is valid for `asset_group=defi`. IS `DEFI_ONCHAIN_INSTRUMENT_TYPES` MUST include `PERPETUAL`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **venue**                                                                | bare `venue={PROTOCOL}` (UAC `to_canonical_venue` → `UNISWAP_V3`, `AERODROME_V3`, `TRADER_JOE_V2`, `AAVE_V3`, `LIDO`, `GMX`, …) + separate `chain=`                   | NEVER the legacy combined `PROTOCOL-CHAIN` overload in the path; `chain=` is its own segment (per `build_defi_partition_path`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **bucket**                                                               | **CONSOLIDATED `market-data-tick-defi-prd-{pid}`** (data_type lives in the `data_type=` path/column, NOT a separate bucket)                                           | **CORRECTED 2026-06-21 (operational reality — supersedes the 2026-05-28 dedicated-bucket directive):** the consolidated `market-data-tick-defi-prd-{pid}` is the ONLY defi bucket with a live consolidator (`manifest_consolidator_scheduler.tf` covers it, NOT any `{stem}-prd`) AND the canonical 6.16M-row v9 `_index` (honest-cov source). The 2026-05-28 dedicated `{stem}-prd` migration was never consolidated → operationally incomplete. ALL defi handlers resolve `get_write_bucket_name("market_data", "defi")` (lst_rates mtds@4c85340 + gas_fee/dex_pools/lending_indices/liquidations/oracle_prices/perp_funding/evm_defi/aggregator_route mtds@1c99e5c). Provenance: `plans/active/data_completion_to_100_all_ag_2026_06_21.md` Progress Log 2026-06-21 DEFI lane. |
| **v9 metadata columns**                                                  | `schema_version=9`, `asset_group=defi`, `pipeline_mode`, `source`, `available_at`                                                                                     | Stamped per row at write/migration time.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

## On-chain perp CLOBs are CeFi, NOT DeFi (asset_group boundary — codified 2026-06-25)

On-chain perpetual CLOB exchanges are classified **`asset_group=cefi`** (UAC `VENUE_TO_ASSET_GROUP` /
`VENUES_BY_ASSET_GROUP["cefi"]`), even though they settle on-chain — they trade the perp/hedge leg, not the DeFi
long/stake/lend/AMM leg. **CeFi on-chain perps: `HYPERLIQUID` (HYPERLIQUID), `ASTER` (BSC), `EXTENDED` (STARKNET),
`PACIFICA` (SOLANA), `LIGHTER` (ZKSYNC)** — each has a cefi `SourceCapability` (`_cefi.py`) + a cefi venue-launch date +
per-CEFI-instrument manifest shape (`venue, instrument_id, data_type, day`), and rides the **cefi backfill**, not the
defi path. The only **DeFi** perps are `DRIFT` (SOLANA) + `GMX` (ARBITRUM/AVALANCHE) — DEX-pool-shaped, in
`DEFI_PERP_VENUES`. **2026-06-25 alignment:** the instruments-service capture path (`engine/orchestrator/defi.py`
`_SOLANA_DEFI_VENUES`/`_L2_DEX_PERP_VENUES`) had wrongly enumerated EXTENDED/PACIFICA/LIGHTER as defi → 1,802
contaminant defi `_index` rows; they were moved to `venue_core._CEFI_VENUES` (adapters relocated
`adapters/defi/`→`adapters/cefi/`) and the contaminant rows purged. SSOT:
`plans/active/instruments_foundation_completeness_2026_06_24.md`.

## `dex_pool_state` = EVM + Solana pool-state UNION under one data_type (CHANGE — operator-noted 2026-06-01)

After the collapse, **`data_type=dex_pool_state` carries BOTH EVM pools and Solana pools under a single name** — it is a
union, not EVM-only:

- **EVM** (Uniswap/Curve/Balancer/Aerodrome/…) → `instrument_type=pool`, columns `price_a`/`price_b`/`fee_rate_bps`/
  `liquidity`/`tvl_usd`/…
- **Solana** (Orca/Raydium/Kamino/…) → `instrument_type=solana_amm_pool` / `solana_vault`, columns
  `sqrt_price`/`tick_spacing`/`token_a_mint`/`vault_type`/`total_shares`/…

The **discriminators are `instrument_type` + `chain`** (+ the superset columns, which co-exist and are null where N/A —
e.g. an EVM cell has `sqrt_price=null`, a Solana cell has `price_a=null`). A consumer that wants only EVM (or only
Solana) pool state filters by `instrument_type`/`chain`, NOT by a separate data*type. **Implication for
`solana_defi_legacy_migration`**: its `SOLANA_AMM_POOL`/`SOLANA_VAULT` instrument_types are the discriminator \_within*
`dex_pool_state` — Solana pools must NOT be re-keyed to a distinct data_type (that would re-split the SSOT). Same logic
for `lending_indices` (EVM `lending` + Solana `solana_lending` instrument_types under one data_type).

## Per-surface alignment status (the fan-out — each is a tracked todo)

| Surface                                                     | Repo                                | Needs                                                                                                                        | Status                                                |
| ----------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| C0 migration `migrate_defi_full_v9_canonical.py`            | market-tick-data-service            | writes all canonical forms                                                                                                   | ✅ mtds@6a8372b2                                      |
| DeFi handlers `_DATA_TYPE` consts                           | market-tick-data-service            | `dex_pools_handler`→`dex_pool_state`, `dex_swaps_handler`→`dex_pool_swaps`; write `pipeline_mode=` partition                 | ✅ mtds@0a3a7071 (C0-CN2)                             |
| Manifest consolidator + `_PATH_DATA_TYPE`/bucket-domain map | market-tick-data-service / features | drop on-disk→logical `dex_pool_state→dex_pools` remap (now identity)                                                         | ✅ mtds@0a3a7071 + features@dec1b687 (C0-CN3)         |
| features-onchain reader + calculators                       | features-service                    | pipeline_mode-aware reads (pass `pipeline_mode` to `candidate_parquet_paths`); `_PATH_DATA_TYPE` identity                    | ✅ features@dec1b687 (C0-CN4)                         |
| MDPS reader                                                 | market-data-processing-service      | pipeline_mode-aware reads; data_type `dex_pool_state`                                                                        | ✅ mdps@4b9e6e5 (C0-CN5)                              |
| UAC `build_defi_partition_path` + `ChainKind`               | unified-api-contracts               | make `pipeline_mode=` canonical in the builder (not just a probe); `ChainKind.HYPERLIQUID_L1.value='HYPERLIQUID'` (or alias) | ✅ uac@dad96e42 (C0-CN6)                              |
| IS `DEFI_ONCHAIN_INSTRUMENT_TYPES`                          | instruments-service                 | include `PERPETUAL` for DeFi on-chain perps                                                                                  | ✅ verified, IS already produces `perpetual` (C0-CN7) |

> **Status updated 2026-06-02 (slot-2):** all per-surface alignment rows above are SHIPPED on LDR (C0-CN1–8 in
> `defi_manifest_canonicalisation_2026_06_01.md`). The table previously read ☐ TODO — that was stale relative to the
> shipped code. Remaining DeFi-lane work is the OPERATIONAL half (re-dry → apply → RD4 → RD5) + the attribution
> registries (oracle `contract→chain`, lst tokens), tracked in the plan's §C0-RD.

## Sequencing (HARD — prevents the regression the audit caught)

1. **Reader fixes land FIRST** (features + MDPS pipeline_mode-aware; data_type identity) — otherwise consumers reading
   the base `build_defi_partition_path` (no `pipeline_mode=`) won't find migrated data.
2. **Writer fixes land WITH the migration** (handlers write `dex_pool_state`/`dex_pool_swaps` + `pipeline_mode=`) so
   live = batch (identical path).
3. **THEN** the C0 `--apply` migration runs → RD4 completeness+CF gate per bucket → **RD5 delete legacy** per bucket
   (only after that bucket is canonical + readers proven on it).

Applying the migration before the reader fixes would write data the live consumers can't read = the exact "fake
buckets/paths to fit code" regression this SSOT prevents.

## Cross-plan

- `plans/active/defi_manifest_canonicalisation_2026_06_01.md` §C/C2 + C0-RD — the migration owner (this codex is its
  naming SSOT).
- `plans/active/pipeline_mode_partition_migration_2026_06_01.md` — owns making `pipeline_mode=` canonical in the
  writer/reader (lands WITH C0, not after).
- `plans/active/solana_defi_legacy_migration_2026_05_27.md` — dedicated-bucket directive; uses `dex_pool_state`.
- `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` — owns the legacy DELETE (RD5), gated
  per-AG on C-GREEN.

## DeFi data-pipeline DURABLE gotchas (codified 2026-06-21 — root causes that kept defi MTDS stuck at 6% honest-cov)

These are reader/writer + seeding contracts an agent MUST honour; each was a multi-hour root-cause hunt. Read before
touching defi MTDS capture / honest-cov.

1. **Instruments preflight reader ↔ writer bucket MISMATCH (env-less vs `-prd-`).** The MTDS DeFi capture preflight
   `assert_defi_catalog_fresh` → `run_preflight(DEFI_COLLECT_DAILY)` resolves its bucket via
   `_defi_manifest.build_bucket("instruments", asset_group="defi")` → **`instruments-store-defi-{pid}` (env-LESS
   legacy)**. But every WRITER (IS instruments backfill, `build_instrument_catalogue` roll-up, the instruments
   consolidator) writes **`instruments-store-defi-prd-{pid}` (env-SHORT canonical)**. So the reader reads a stale/empty
   legacy index → catalog preflight `age=None` → handlers route honest-absence → **zero capture**. FIX (durable): align
   the reader to canonical `-prd-` (or write both). Stop-gap: `gcs_copy_object` the fresh `-prd-`
   `_index/availability_index.parquet` → the env-less bucket (valid ≤24h per the staleness window). Same
   env-less-vs-`-prd-` class as the market-data bucket bug.
2. **Consolidated-index staleness default (120s) is FAR too short for a DAILY reference catalog.**
   `read_availability_index` (`manifest_writer/_read_index.py`) checks the consolidated blob's GCS `updated` vs
   `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default **120s**); if older AND per-VM shards exist it FALLS BACK to merging
   per-VM shards. For the daily instrument catalog the consolidated blob is minutes-to-hours old in normal operation →
   it ALWAYS fell back to per-VM shards, which carry **pre-canonicalisation columns (blank `data_type`)** → the
   `data_type='instrument-catalog'` filter matched 0 rows → `age=None`. FIX: defi MTDS launchers pass
   **`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`** (24h — a daily catalog is fresh for 24h) so the reader trusts the
   consolidated index. `setup-data-pipeline-vm.sh` already propagates the metadata.
3. **`expected_unattempted` MUST be seeded in CANONICAL venue/chain or captures NEVER convert it.** The IS
   expected-universe enumerator (`enumerate_expected_universe.py` / `expected-universe-v2-defi`) seeded defi
   `expected_unattempted` with the LEGACY combined `venue=PROTOCOL-CHAIN`, `chain=''`. Handlers CAPTURE canonical
   `venue=PROTOCOL` + separate `chain=X` (this SSOT). Different shard keys → captures create NEW rows, the legacy
   unattempted persist → honest-cov flat at ~6% despite real data flowing. The enumerator/seeder MUST emit the canonical
   venue/chain split (this SSOT applies to the SEEDER, not only the migration + handlers).
4. **NEVER call a synchronous GCS read inside an `async def` handler.** `ManifestFreshnessCache.bulk_load()` /
   `assert_defi_catalog_fresh` do blocking GCS I/O; called directly in async handler code they block the event loop →
   the 120s log-uploader heartbeat starves → the VM LOOKS hung (no log progress) though it's alive. Wrap in
   `await asyncio.to_thread(...)`. And `assert_defi_catalog_fresh` is **keyword-only**
   (`*, project_id, on_date, correlation_id`) — wrap as
   `asyncio.to_thread(lambda: assert_defi_catalog_fresh(project_id=…, on_date=…, correlation_id=…))`, never positional
   (positional → `takes 0 positional arguments but 3 were given`).
5. **DeFi DEX subgraph handlers MUST shard across the 9-key TheGraph pool.** `thegraph-api-key` +
   `thegraph-api-key-2..9` exist in Secret Manager for sharding; `TheGraphBaseClient` has round-robin but
   `dex_pools_handler`/`dex_swaps_handler` hand-rolled a SINGLE key → all DEX VMs collided on key #1. Use the
   round-robin pool (per-request) — not a single key.
6. **Catalogue rollup MUST key `venue_day_counts` on the CANONICAL venue (2026-06-27).** `build_catalogue_dataframe`
   accumulates per-(venue, day) instrument counts for the §7.3 thin-day-aware liveness window. If keyed on the RAW
   snapshot venue (e.g. `PANCAKESWAPV3-BSC`), old ghost venues generate a separate, tiny window ending May 8 — every
   pool that last appeared on that ghost venue's last full day gets `available_to=None` (false-active, the +73
   PANCAKESWAP_V3-BSC discrepancy). FIX: `venue_day_counts` is keyed via `canonicalize_defi_venue_combined(raw_venue)`
   so ghost and canonical forms share ONE liveness window. When looking up `venue_last_full`, the aggregate's meta venue
   is also canonicalised before the dict lookup. Provenance: `instruments-service@50308e0`
   (`fix(catalogue): collapse defi ghost dual-keys …`).
7. **Non-pool DeFi instrument_ids with ghost venue prefixes create dual catalogue rows (2026-06-27).** DeFi lending rows
   (AAVE_V3 / COMPOUND_V3) have `instrument_key=VENUE-CHAIN:TYPE:SYMBOL`. When the IS adapter switched from the
   no-underscore ghost form (`AAVEV3-ARBITRUM`) to canonical (`AAVE_V3-ARBITRUM`) around 2026-05-08, the same logical
   market appears under two `instrument_key`s → two catalogue rows (the +171 AAVE_V3 / +26 COMPOUND_V3 triad
   discrepancy). POOL rows are already protected by the pool-address agg_key collapse. Non-pool rows are fixed by
   `_canonical_instrument_id()` in `_aggregate_key`: the venue-prefix portion (before the first `:`) is normalised via
   `canonicalize_defi_venue_combined` so ghost-keyed rows collapse onto the canonical aggregate key. Provenance:
   `instruments-service@50308e0`.
