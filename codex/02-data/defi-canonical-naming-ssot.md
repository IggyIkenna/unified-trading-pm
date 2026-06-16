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

| Axis                                                                     | Canonical value(s)                                                                                                                                                    | Notes                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Object path**                                                          | `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=defi/venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{file}`                                  | `pipeline_mode=` IS canonical (operator 2026-06-01), inserted after `day=` — the form `candidate_parquet_paths(pipeline_mode=…)` probes first. `mode` ∈ `batch`/`live`.                                                                                                                                                                                          |
| **data_type** (path + column + manifest + handler const + bucket-domain) | `dex_pool_state` (pools), `dex_pool_swaps` (swaps), `lst_rates`, `lending_indices`, `oracle_prices`, `perp_funding`                                                   | **Collapsed to ONE name everywhere** (operator 2026-06-01). The legacy 2-layer split (on-disk `dex_pool_state` vs manifest `dex_pools`) is RETIRED — `dex_pool_state`/`dex_pool_swaps` are canonical at every layer. (Bucket _name_ stays `dex-pools`/`dex-swaps` — that's a bucket id, not the data_type.) **See "dex_pool_state = EVM + Solana union" below.** |
| **chain**                                                                | `HYPERLIQUID` (not `HYPERLIQUID_L1`), `ETHEREUM`/`ARBITRUM`/`BASE`/`OPTIMISM`/`POLYGON`/`BSC`/`AVALANCHE`/`SOLANA`/`ZKSYNC`/`SCROLL`/`LINEA`                          | App-chain perps: `HYPERLIQUID→HYPERLIQUID`, `PACIFICA→SOLANA`, `LIGHTER→ZKSYNC`, `ASTER→BSC`, `DRIFT→SOLANA`. UAC `ChainKind.HYPERLIQUID_L1.value` MUST resolve to wire `HYPERLIQUID`.                                                                                                                                                                           |
| **instrument_type**                                                      | `pool` (dex), `lending`, `lst`, `spot_asset` (oracle), **`perpetual`** (DeFi on-chain perps: Drift/GMX/HL) + Solana `solana_amm_pool`/`solana_vault`/`solana_lending` | **DeFi DOES have perps** (operator 2026-06-01): Drift/GMX/Hyperliquid are on-chain perp DEXs. `instrument_type=perpetual` is valid for `asset_group=defi`. IS `DEFI_ONCHAIN_INSTRUMENT_TYPES` MUST include `PERPETUAL`.                                                                                                                                          |
| **venue**                                                                | bare `venue={PROTOCOL}` (UAC `to_canonical_venue` → `UNISWAP_V3`, `AERODROME_V3`, `TRADER_JOE_V2`, `AAVE_V3`, `LIDO`, `GMX`, …) + separate `chain=`                   | NEVER the legacy combined `PROTOCOL-CHAIN` overload in the path; `chain=` is its own segment (per `build_defi_partition_path`).                                                                                                                                                                                                                                  |
| **bucket**                                                               | dedicated per-type `{stem}-prd-{pid}` (`dex-pools-prd-…`, `oracle-prices-prd-…`, …)                                                                                   | Operator 2026-05-28 directive (`solana_defi_legacy_migration`): dedicated split buckets are canonical; NO DeFi writer targets the consolidated `market-data-tick-defi-*`.                                                                                                                                                                                        |
| **v9 metadata columns**                                                  | `schema_version=9`, `asset_group=defi`, `pipeline_mode`, `source`, `available_at`                                                                                     | Stamped per row at write/migration time.                                                                                                                                                                                                                                                                                                                         |

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
