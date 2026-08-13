---
doc_type: codex-ssot
title: DeFi Data Types Catalog
summary: >-
  Per-data_type capture catalog for the ~24 MTDS DeFi data_types (dex_swaps, dex_pool_state, lending_indices,
  perp_funding, lst_rates, oracle_prices, gas_fees, +Solana basis MVP types) — CLI operation, sources, shard key,
  instrument_type, schema fields, GCS path convention and per-protocol coverage matrix; carries a partial staleness
  banner deferring current-state to defi-data-pipeline + defi-canonical-naming.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, features-service, instruments-service]
scope: [engineer]
tags: [defi, mtds, catalogue, data-pipeline, features]
related:
  [
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/defi-data-type-taxonomy.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/instrument-pipeline-defi.md,
    /codex/02-data/mtds-data-source-coverage-matrix.md,
  ]
created: 2026-04-24
authoritative_for: [DeFi MTDS per-data_type definitions catalog, DeFi data_type to CLI-operation and source mapping]
referenced_by:
  [
    /codex/02-data/README.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/defi-data-type-taxonomy.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/04-architecture/drift-v2-data-sources.md,
    /codex/15-runbooks/backfill-completion-playbook.md,
    plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md,
  ]
owner:
last_reviewed: 2026-07-24
code_refs:
---

# DeFi Data Types Catalog

> SSOT for all MTDS DeFi data type definitions, sources, shard keys, and implementation status. Last updated: 2026-05-12
> (codex audit IN-7 + IN-15 + IN-19 refresh — asset_group canonical hive vocab + 3-doc consolidation cross-link +
> currency stamp added). Prior: 2026-04-24 (defi_data_types_completeness_2026_04_24).

> **🟡 PARTIAL STALENESS (code↔codex audit 2026-05-27).** This catalog drifted from code. Verified against handlers +
> UAC on 2026-05-27: (1) the canonical `data_type=` strings are **`dex_swaps`** (was `swap_events`),
> **`dex_pool_state`** (was `pool_state`), **`lending_indices`** (was `lending_metrics`), **`perp_funding`** (was
> `funding_rates`) — renamed in this rev. (2) Code emits **~22** DeFi data_types; this catalog documents 14 —
> **missing** `lst_rates`, `vault_share_price`, `liquidations`, `risk_params`, `rewards`, `eigenlayer_rewards`,
> `native_staking_rates`, `aggregator_route`, `restaking_rewards`, `governance_proposals`, etc. (3) Some source/venue
> entries are stale (e.g. `oracle_prices` also uses Pyth Hermes on Solana; `lending_indices` also covers Spark +
> Compound V3). **Authoritative current-state**: [`defi-data-pipeline.md`](./defi-data-pipeline.md) (code-grounded) +
> audit findings
> [`plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27`](../../plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md).
> **Reconciliation applied 2026-05-27**: missing types added in § "Additional data types"; `oracle_prices` /
> `lending_indices` / `perp_funding` sources corrected; remaining **code-registry bugs** (D14
> dex_pools-vs-dex_pool_state data_type, governance handler dup, live-venues-without-capability) are
> deferred-until-pipeline-done and tracked in the findings + issue docs.

> **🛑 D14 RESOLVED + CANONICAL NAMING LOCKED (operator 2026-06-01) — SSOT
> [`defi-canonical-naming-ssot.md`](./defi-canonical-naming-ssot.md)**: the D14 `dex_pools`-vs-`dex_pool_state`
> ambiguity is settled — **canonical data_type = `dex_pool_state` (pools) / `dex_pool_swaps` (swaps) EVERYWHERE**
> (path + column + manifest + handler const + bucket-domain logical key). The earlier "canonical is `dex_pools`, rename
> `dex_pool_state`→`dex_pools` pending D14" direction is **REVERSED** — `dex_pools`/`dex_swaps` are retired. Other
> locked forms: object path carries **`pipeline_mode={mode}/`** after `day=`; Hyperliquid chain wire value =
> **`HYPERLIQUID`**; **`instrument_type=perpetual` is VALID for DeFi** (on-chain perps GMX/HL — GMX REMOVED 2026-07-25,
> see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; Drift removed 2026-07-16). Note: `dex_pool_state`
> is the **EVM + Solana union** (EVM `instrument_type=pool`; Solana `solana_amm_pool`/`solana_vault`) — discriminate by
> instrument_type + chain, NOT a separate data_type. Shipped: migration mtds@6a8372b2; writer/reader alignment
> uac@dad96e42 + mtds@0a3a7071 + features-service@dec1b687 + mdps@4b9e6e5. References below to `dex_pools`/ `dex_swaps`
> as the canonical data_type are SUPERSEDED by this banner.

> **🟡 NEEDS_CANDLE_PROCESSING gap (found 2026-07-24, `data_pipeline_e2e_milestones_gate_2026_07_24.md` §5).** This
> catalog's README claims "comprehensive" coverage, but UAC's `market_data_categories.py` NEEDS_CANDLE_PROCESSING dict
> (the same mechanism `tradfi-data-types-catalog.md` documents in a dedicated table) is mentioned only ONCE here (the
> `dex_pools` bypass/False note in item 2 below) — the other ~23 DeFi data_types' NEEDS_CANDLE_PROCESSING values are
> undocumented in this file. Todo (not yet done): audit every DeFi data_type against the live UAC dict and add a
> dedicated table mirroring `tradfi-data-types-catalog.md`'s exact structure.

## Overview

MTDS collects DeFi market data in **~24** distinct data_types across lending, DEX, staking, restaking, bridging,
governance, oracle, and MEV domains (14 detailed below + § "Additional data types"). Each data type maps to one or more
MTDS CLI operations (`--operation collect-<type>`), one or more venues, and a canonical GCS path. **Note**: raw on-chain
snapshot types (`lst_rates`, `lending_indices`, `dex_pools`, `oracle_prices`, `perp_funding`, `vault_share_price`) write
to **dedicated buckets** (`lst-rates-*`, `lending-indices-*`, `dex-pools-*`, …), not all under one defi tick bucket —
see [`defi-data-pipeline.md`](./defi-data-pipeline.md) §2.

### GCS Path Convention

**Canonical** (per CLAUDE.md § "Asset-group vocabulary"; `asset_group=` hive key per
`market_tick_data_service/raw_tick_hive.RAW_TICK_ASSET_GROUP_HIVE_KEY`):

```
{resolved-defi-tick-bucket}/raw_tick_data/by_date/day={date}/asset_group=defi/
  venue={VENUE}-{CHAIN}/instrument_type={type}/data_type={data_type}/ticks.parquet
```

Bucket name is resolved via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind="market-data-tick", asset_group="defi", env=...)`
per CLAUDE.md § "Bucket-name SSOT (b+)" — never inline `gs://...` / `s3://...` (QG STEP 5.69 ratchet enforces).

**Legacy** (data coexists on disk until ~2026-06-15 deletion cutoff per
[`per-asset-group-bucket-layouts.md`](./per-asset-group-bucket-layouts.md) § "Asset-group hive vocabulary"):
`category=defi/` instead of `asset_group=defi/`. Readers try canonical → fall back. Migration scripts at
`instruments-service/scripts/migrate_defi_bare_to_asset_group.py` +
`instruments-service/scripts/migrate_defi_legacy_venue_chain.py`.

### Instrument Type Mapping

| instrument_type   | Data types                                                                                                                  | Notes                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `spot_asset`      | dex_swaps, dex_pool_state, bridge_events, mev_events, token_transfers, governance_events, staking_yields, vault_share_price | EVM DEX + bridging + governance                                            |
| `lending`         | lending_indices, liquidations, liquidation_events, flash_loan_events, position_data, risk_params                            | EVM lending protocols (Aave/Compound/Spark)                                |
| `staking`         | staking_yields, lst_rates, rewards, eigenlayer_rewards, native_staking_rates                                                | LST + restaking + native staking                                           |
| `perpetual`       | perp_funding                                                                                                                | DeFi perps (Hyperliquid; GMX REMOVED 2026-07-25, Drift removed 2026-07-16) |
| `solana_lending`  | lending_indices                                                                                                             | Solana lending (Kamino/Solend/Marginfi) — UAC@7e9f4ad9                     |
| `solana_vault`    | dex_pools                                                                                                                   | Kamino vault strategies (Solana) — UAC@90b2bb9d                            |
| `solana_amm_pool` | dex_pools                                                                                                                   | Solana AMM pools (Orca/Raydium/Phoenix) — UAC@90b2bb9d                     |

---

## Data Type Catalog

### 1. dex_swaps (canonical; was `swap_events`)

| Field               | Value                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-dex-swaps` (`dex_swaps_handler.DexSwapsHandler`)                                                                                                                                                                                                                                                                                                                                          |
| **Sources**         | The Graph, EVM-only (12 protocols, `_dex_swaps_queries._DEFAULT_PROTOCOLS`, verified against code 2026-07-24): `uniswap_v3`, `pancakeswap_v3`, `aerodrome_v3`, `camelot_v3`, `balancer`, `curve`, `sushiswap_v3`, `sushiswap`, `velodrome_v2`, `trader_joe_v2`, `uniswap_v4`, `uniswap_v2`. No Solana route (contrast `dex_pool_state` below) and no `gmx` (GMX has no traditional AMM swap feed). |
| **Shard key**       | venue × chain × date                                                                                                                                                                                                                                                                                                                                                                               |
| **Instrument type** | `spot_asset`                                                                                                                                                                                                                                                                                                                                                                                       |
| **Status**          | Production                                                                                                                                                                                                                                                                                                                                                                                         |
| **Schema fields**   | symbol, ts_event, venue, chain, token_in, token_out, amount_in, amount_out, price                                                                                                                                                                                                                                                                                                                  |

Captures AMM swap transactions. One row per swap event.

---

### 2. dex_pools (canonical registry name; on-disk today as `dex_pool_state` pending D14 rename; was `pool_state`)

| Field               | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-dex-pools` (`dex_pools_handler.DexPoolsHandler`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Sources**         | 16 protocols total (`dex_pools_handler._DEFAULT_PROTOCOLS`, verified against code 2026-07-24; `gmx` REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) — **EVM via The Graph** (12): `uniswap_v3`, `pancakeswap_v3`, `sushiswap_v3`, `aerodrome_v3`, `camelot_v3`, `balancer`, `curve`, `sushiswap`, `velodrome_v2`, `trader_joe_v2`, `uniswap_v4`, `uniswap_v2`; **Solana via `_collect_solana_dex`** (4, routed by `_solana_defi_fetch.SOLANA_DEX_PROTOCOLS`, bypassing the subgraph cascade): `kamino`→`SOLANA_VAULT`, `orca`/`raydium`/`phoenix`→`SOLANA_AMM_POOL`. (`solana_defi_handler.py`'s separate `collect-solana-defi` CLI command additionally writes `dex_pool_state` for `meteora`/`lifinity` — a DIFFERENT dispatch path, not part of this `_DEFAULT_PROTOCOLS` list.) |
| **Shard key**       | venue × chain × date                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Instrument type** | `spot_asset`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Status**          | Production                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Actual columns**  | protocol, chain, pool_id, token_a, token_b, fee_rate_bps, date, volume_usd, tvl_usd, fees_usd, tx_count, price_a, price_b, liquidity, sqrt_price, tick                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

Hourly/daily pool snapshots. ⚠ **D14 (2026-05-27, resolved-by-ikenna):** **canonical is `dex_pools`** — UAC
`needs_candle_processing` keys it `dex_pools` (= bypass/False) and the handler manifest const is
`_DEX_POOLS_DATA_TYPE = "dex_pools"` (L62). But `dex_pools_handler.py` writes the parquet with
`data_type="dex_pool_state"` (L569), so the on-disk hive partition today is `dex_pool_state` (manifest≠data divergence).
The write-flip to `dex_pools` **cannot be standalone** — it would split forward-writes from historical (violating
single-walk discipline) — so it is **bundled into [`mtds_mdps_master`](../../plans/epics/mtds_mdps_master.md) Phase 9**
(GCS hive rename `dex_pool_state`→`dex_pools` + the handler write-flip, together). Deferred-until-pipeline-done.

---

### 3. lending_indices (canonical; was `lending_metrics`)

| Field               | Value                                                                                                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-lending-indices` (lending_indices_handler)                                                                                                                                               |
| **Sources**         | The Graph: Aave V3, **Spark, Compound V3** (`collect-lending-indices`); Morpho via blue-api.morpho.org + Solana (Kamino/Marginfi/Solend) via DeFiLlama (`collect-evm-defi`/`collect-solana-defi`) |
| **Shard key**       | venue × chain × date                                                                                                                                                                              |
| **Instrument type** | `lending`                                                                                                                                                                                         |
| **Status**          | Production                                                                                                                                                                                        |
| **Schema fields**   | symbol, ts_event, venue, chain, supply_apy, borrow_apy, utilization_rate, total_supply, total_borrow                                                                                              |

Daily lending rate indices. One row per market (token) per day.

---

### 4. perp_funding (canonical; was `funding_rates`)

| Field               | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-perp-funding` (perp_funding_handler) — was GMX's operation, GMX REMOVED 2026-07-25 (see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`); no venue currently writes via this operation. (`solana-defi` / `_collect_drift` for DRIFT-SOLANA removed 2026-07-16 -- operator ruling, all Solana perp DEXes dropped except Jupiter, not integrated.)                                                                                                                         |
| **Sources**         | None currently (GMX, the sole source, REMOVED 2026-07-25). (Drift Data API + S3 removed 2026-07-16 -- operator ruling.) **Hyperliquid/Aster/Lighter-ZKSYNC standalone perp_funding capture was RETIRED 2026-07-08** (operator-approved; Pacifica-Solana was a fourth venue in this retirement until removed entirely 2026-07-16) — those venues' funding is now sourced solely from `derivative_ticker`'s embedded `funding_rate` field (byte-identical, same underlying fetch). See §4a below. |
| **Shard key**       | venue × chain × date                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Instrument type** | `perpetual`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Status**          | No venue currently active — GMX (the sole `perp_funding` writer) REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`. Drift removed 2026-07-16 -- operator ruling, all Solana perp DEXes dropped except Jupiter, not integrated.                                                                                                                                                                                                                              |
| **Schema fields**   | symbol, ts_event, venue, chain, funding_rate, annualized_rate                                                                                                                                                                                                                                                                                                                                                                                                                                   |

Perpetual funding rates — the PER-INTERVAL canonical VIEW (operator ruling 2026-07-15,
`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`). One row per market per funding
interval. `annualized_rate` (a simple multiplicative annualization of ONE rate — e.g. Drift's `_collect_drift` now
computes `funding_rate * 365` from its 24h-window rate) is fine; venue-specific rolling-WINDOW aggregates are NOT — the
Drift-only `funding_rate_24h`/`funding_rate_7d`/`funding_rate_30d` columns (a pre-ruling divergence: no other venue's
writer aggregated funding into rolling windows) were removed from `_collect_drift`'s write path 2026-07-15.
Already-written historical rows carrying those columns are NOT restamped — `schema_validation.py`'s required-columns
check already accepts `funding_rate_24h` as an alternative to `funding_rate` (reader tolerance, not schema breakage).

---

### 4a. derivative_ticker (canonical raw-funding home for ALL perps, 2026-07-15)

| Field               | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | UMI tick-provider batch-live (Hyperliquid/Aster/Extended-Starknet, native REST/S3) · Tardis (Lighter-ZKSYNC, `date >= 2026-04-17` only). (`collect-perp-funding` GMX dual-write REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; Drift `solana-defi`/UMI batch-live + Pacifica-Solana removed 2026-07-16 -- operator ruling.)                                                                                     |
| **Sources**         | Hyperliquid S3 `asset_ctxs` + REST, Aster `/fapi/v1/fundingRate`, Extended `/info/{symbol}/funding`, Tardis archive (Lighter). (The Graph (GMX) source REMOVED 2026-07-25; Drift Data API `/fundingRates` + Pacifica `/funding_rate/history` removed 2026-07-16 -- operator ruling.)                                                                                                                                                                    |
| **Shard key**       | venue × chain × date                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **Instrument type** | `perpetual`                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **Status**          | Production (Hyperliquid/Aster/Extended/Lighter all wired; GMX REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`). MANGO-SOLANA/ZETA-SOLANA/FLASH-SOLANA — DELETED 2026-07-15; DRIFT-SOLANA/PACIFICA-SOLANA — DELETED 2026-07-16 (operator ruling: all Solana perp DEXes dropped except Jupiter, not integrated). No adapters exist for any of these five now. See `/codex/04-architecture/solana-defi-coverage.md`. |
| **Schema fields**   | instrument_id, venue, chain, symbol, ts_event, funding_rate (nullable — but effectively always populated), open_interest (nullable), mark_price (nullable), index_price (nullable)                                                                                                                                                                                                                                                                      |

**Operator ruling (2026-07-15, verbatim intent)**: "the highest-resolution derivative_ticker data should be run for ALL
perps — even if they don't have OI at the data source — for canonicalisation of where raw funding is." This is the
canonical RAW-funding home for every perp venue — captured at the highest resolution the source genuinely offers
(settlement-event grain where available; a poll/snapshot where the source has no settlement-level feed), never
synthesized. OI/mark/index are honestly nullable — GMX's native `fundingRateChangedEvents` query had no OI field at all
(GMX REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`), and Aster/Extended
similarly omit it at this grain (Drift/Pacifica removed 2026-07-16); only Hyperliquid (S3 archive) and Lighter (Tardis)
genuinely have real OI. `funding_rate` + `ts_event` are mandatory. No venue-specific raw-layer aggregation (that's what
§4's `perp_funding` divergence-removal above is about) — aggregation windows belong downstream in features, not in
either raw capture data_type. Full per-venue coverage-table evidence (file:line, verified 2026-07-15):
`unified-trading-pm/plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`.

---

### 5. liquidation_events

| Field               | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-liquidation-events` (liquidation_events_handler)                                                      |
| **Sources**         | The Graph: Aave V3 `liquidationCalls`, Morpho `liquidationEvents`                                              |
| **Shard key**       | venue × chain × date                                                                                           |
| **Instrument type** | `lending`                                                                                                      |
| **Status**          | Production (2026-04-24)                                                                                        |
| **Schema fields**   | symbol, ts_event, venue, chain, collateral_asset, debt_asset, collateral_amount, debt_amount, liquidator, user |
| **Protocols**       | AAVE_V3 (ETHEREUM, ARBITRUM, POLYGON), MORPHO (ETHEREUM)                                                       |

On-chain liquidation call events. One row per liquidation transaction. Distinct from `liquidations` (GMX-style
position-level data) — this is the on-chain event log.

---

### 6. flash_loan_events

| Field               | Value                                                                       |
| ------------------- | --------------------------------------------------------------------------- |
| **CLI operation**   | `collect-flash-loan-events` (flash_loan_events_handler)                     |
| **Sources**         | The Graph: Aave V3 `flashLoans` entity                                      |
| **Shard key**       | venue × chain × date                                                        |
| **Instrument type** | `lending`                                                                   |
| **Status**          | Production (2026-04-24)                                                     |
| **Schema fields**   | symbol, ts_event, venue, chain, asset, amount, premium, initiator, borrower |
| **Protocols**       | AAVE_V3 (all supported chains via `get_supported_chains_for_protocol`)      |

Aave V3 FlashLoan events. Captures flash loans including amount, premium (fee), initiator, and receiver address.

---

### 7. staking_yields

| Field               | Value                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-staking-yields` (staking_yields_handler)                                                                         |
| **Sources**         | Lido REST API (`api.lido.fi/v1/protocol/steth/apr/sma`), EtherFi REST API, DefiLlama (`api.llama.fi/protocol/eigenlayer`) |
| **Shard key**       | venue × chain × date                                                                                                      |
| **Instrument type** | `spot_asset` (written as `SPOT_ASSET`)                                                                                    |
| **Status**          | Production (bumped 2026-08-13 — scheduler-wiring shipped 2026-07-26, leaf-verification shipped 2026-08-05, both live)     |
| **Schema fields**   | symbol, ts_event, venue, chain, apy, apy_7d, apy_30d                                                                      |
| **Protocols**       | LIDO-ETHEREUM (stETH), ETHERFI-ETHEREUM (weETH), EIGENLAYER-ETHEREUM                                                      |

Daily staking yield snapshots from liquid staking protocols. One row per venue per day.

---

### 8. position_data

| Field               | Value                                                                                                 |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-position-data` (position_data_handler)                                                       |
| **Sources**         | The Graph: Aave V3 `users` (top 500 by variable debt), Uniswap V3 `positions` (top 1000 by liquidity) |
| **Shard key**       | venue × chain × date                                                                                  |
| **Instrument type** | `lending`                                                                                             |
| **Status**          | Production (2026-04-24)                                                                               |
| **Schema fields**   | symbol, ts_event, venue, chain, user, supplied_usd, borrowed_usd, health_factor                       |
| **Protocols**       | AAVE_V3 (all supported chains), UNISWAP_V3-ETHEREUM                                                   |

Daily snapshot of top user positions. Captures collateral, debt, and health factor for at-risk lending positions.
Uniswap positions use `liquidity` field mapped to `supplied_usd`.

---

### 9. token_transfers

| Field               | Value                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-token-transfers` (token_transfers_handler)                                               |
| **Sources**         | Alchemy `alchemy_getAssetTransfers` API                                                           |
| **Shard key**       | venue × chain × date (venue = token symbol, e.g. `WETH-ETHEREUM`)                                 |
| **Instrument type** | `spot_asset`                                                                                      |
| **Status**          | Production (2026-04-24)                                                                           |
| **Schema fields**   | symbol, ts_event, venue, chain, from_addr, to_addr, value, block_num, tx_hash                     |
| **Tokens**          | ETHEREUM: WETH, USDC, USDT, DAI, WBTC, AAVE, UNI, EIGEN; ARBITRUM/BASE/OPTIMISM: WETH, USDC, USDT |
| **Requires**        | Alchemy API key (`alchemy-api-key` in Secret Manager)                                             |

ERC-20 transfer events for top DeFi tokens. One row per transfer transaction. Chains: ETHEREUM, ARBITRUM, BASE,
OPTIMISM.

---

### 10. bridge_events

| Field               | Value                                                                                         |
| ------------------- | --------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-bridge-events` (bridge_events_handler)                                               |
| **Sources**         | The Graph: Across Protocol `fundsDepositeds`, Stargate Finance `swaps`                        |
| **Shard key**       | venue × chain × date (venue = bridge protocol)                                                |
| **Instrument type** | `spot_asset`                                                                                  |
| **Status**          | Production (2026-04-24)                                                                       |
| **Schema fields**   | symbol, ts_event, venue, chain, source_chain, dest_chain, token, amount, depositor, recipient |
| **Protocols**       | ACROSS-ETHEREUM, STARGATE-ETHEREUM                                                            |

Cross-chain bridge transfer events. Across: `FundsDeposited` (origin chain deposit). Stargate: `Swap` (cross-chain
swap).

---

### 11. governance_events

| Field               | Value                                                                          |
| ------------------- | ------------------------------------------------------------------------------ |
| **CLI operation**   | `collect-governance-events` (governance_events_handler)                        |
| **Sources**         | The Graph: Compound, Aave, Uniswap DAO governance subgraphs                    |
| **Shard key**       | venue × chain × date (venue = DAO protocol)                                    |
| **Instrument type** | `spot_asset`                                                                   |
| **Status**          | Production (2026-04-24)                                                        |
| **Schema fields**   | symbol, ts_event, venue, chain, proposal_id, event_type, voter, support, votes |
| **Protocols**       | COMPOUND-ETHEREUM, AAVE-ETHEREUM, UNISWAP-ETHEREUM                             |

DAO proposal and vote events. `event_type` = `PROPOSAL_CREATED` or `VOTE_CAST`. For proposals: voter = proposer,
support/votes = null.

---

### 12. mev_events

| Field               | Value                                                                          |
| ------------------- | ------------------------------------------------------------------------------ |
| **CLI operation**   | `collect-mev-events` (mev_events_handler)                                      |
| **Sources**         | Flashbots relay REST API: `relay/v1/data/bidtraces/proposer_payload_delivered` |
| **Shard key**       | venue × chain × date (venue = `FLASHBOTS`)                                     |
| **Instrument type** | `spot_asset`                                                                   |
| **Status**          | Production (2026-04-24)                                                        |
| **Schema fields**   | symbol, ts_event, venue, chain, relay, block_number, builder_pubkey, value_eth |
| **Protocols**       | FLASHBOTS-ETHEREUM                                                             |

MEV-Boost relay proposer payload delivery stats. One row per block delivered through Flashbots relay. `value_eth` =
block value in ETH (wei → ETH conversion applied). No API key required (public relay).

---

### 13. oracle_prices

| Field               | Value                                                                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-oracle-prices` (oracle_prices_handler)                                                                                                                                                |
| **Sources**         | **Chainlink** `latestRoundData()` via Alchemy RPC (EVM: ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON) + **Pyth Hermes REST** (Solana: SOL/BTC/ETH/JitoSOL/mSOL/bSOL/INF) — Pyth unbanned 2026-05-06 |
| **Shard key**       | venue × chain × date                                                                                                                                                                           |
| **Instrument type** | `spot_asset`                                                                                                                                                                                   |
| **Status**          | Production                                                                                                                                                                                     |
| **Schema fields**   | symbol, ts_event, venue, chain, price_usd                                                                                                                                                      |

On-chain oracle price snapshots from Chainlink-backed oracles.

---

### 14. gas_fees

| Field               | Value                                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **CLI operation**   | `collect-gas-fees` (gas_fee_handler)                                                                                     |
| **Sources**         | On-chain block headers, Etherscan API                                                                                    |
| **Shard key**       | venue (chain name) × date                                                                                                |
| **Instrument type** | `spot_asset`                                                                                                             |
| **Status**          | Production                                                                                                               |
| **Schema fields**   | symbol, ts_event, venue, chain, mean_gas_price, median_gas_price, p95_gas_price, p99_gas_price, base_fee, total_gas_used |

Daily aggregate gas stats per EVM chain. One row per chain per day.

---

## Additional data types (2026-05-27 reconciliation)

These data_types are emitted by code but were absent from the 14 documented above (verified against MTDS handlers + UAC,
2026-05-27). Compact form; promote to full sections as needed.

| data_type                                                                       | CLI operation                  | Handler                         | Source(s)                                                                                | Key columns / notes                                                                                                                                                                                       | Status                          |
| ------------------------------------------------------------------------------- | ------------------------------ | ------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `lst_rates`                                                                     | `collect-lst-rates`            | `LstRatesHandler`               | Alchemy `eth_call` @ historical block (EVM); Marinade/Jito REST (Solana)                 | timestamp, token, exchange_rate, apy, quote_asset, protocol, chain, block_number, method, contract. **Distinct from `staking_yields`** (which is APY from protocol REST; this is on-chain exchange rate). | Production                      |
| `vault_share_price`                                                             | `collect-vault-share-price`    | `VaultSharePriceHandler`        | Alchemy `eth_call` `convertToAssets()` (ERC-4626)                                        | timestamp, vault_address, vault_symbol, protocol, chain, block_number, share_price, underlying_symbol/decimals                                                                                            | Production                      |
| `liquidations`                                                                  | `collect-liquidations`         | `LiquidationsHandler`           | The Graph (Aave V3 `liquidationCalls`, Compound V3)                                      | collateral/principal symbol+amount, liquidator, user                                                                                                                                                      | Production                      |
| `risk_params`                                                                   | (derived in `_LENDING_DATA`)   | lending handlers                | The Graph (Aave reserve config)                                                          | ltv, liquidation_threshold, reserve_factor — declared in UAC `_LENDING_DATA`; no standalone handler                                                                                                       | Partial                         |
| `utilization`                                                                   | (derived from lending capture) | `LendingIndicesHandler`         | extracted from `lending_indices` (no separate fetch)                                     | utilization_rate                                                                                                                                                                                          | Production                      |
| `rewards`                                                                       | (PROTOCOL_CAPABILITIES)        | —                               | declared for LIDO/ETHERFI/EIGENLAYER in UAC; no dedicated MTDS handler                   | reward_rate                                                                                                                                                                                               | Declared, no handler            |
| `eigenlayer_rewards`                                                            | `collect-eigenlayer-rewards`   | `EigenlayerRewardsHandler`      | Ethereum on-chain (RewardsCoordinator + Season-1 distributors)                           | venue=EIGENLAYER/ETHEREUM, instrument_type=staking                                                                                                                                                        | Production                      |
| `native_staking_rates`                                                          | `collect-native-staking-rates` | `NativeStakingHandler`          | Solana RPC `getInflationRate`/`getEpochInfo`; Helius (per-validator) BLOCKED-CREDENTIALS | epoch, validator_vote_account, commission_pct, base_apy, mev_apy, total_apy                                                                                                                               | Partial (per-validator blocked) |
| `aggregator_route`                                                              | `collect-aggregator-routes`    | `AggregatorRouteHandler`        | Jupiter v6 (Sol, public); 1inch/0x (EVM, need keys); ParaSwap (EVM)                      | token_in/out, amount_in/out, route_kind, route_json, source, quote_block_number                                                                                                                           | Partial (1inch/0x need creds)   |
| `protocol_outages`                                                              | `detect-protocol-outages`      | `ProtocolOutageDetectorHandler` | The Graph (Aave V2 reserve-freeze, Compound V2 pause)                                    | ProtocolPauseWindow objects                                                                                                                                                                               | Production                      |
| `governance_proposals`                                                          | (NOT registered in CLI)        | `GovernanceProposalsHandler`    | on-chain + Snapshot                                                                      | UAC `GovernanceProposal`; **scaffold for Phase-4B sim harness — not wired in `cli/main.py`** (cf. `governance_events`, which IS the active handler)                                                       | Scaffold (unregistered)         |
| `dex_pool_swaps`                                                                | (UAC schema only)              | —                               | —                                                                                        | UAC declares a `(defi, pool, dex_pool_swaps)` schema; code uses `dex_swaps` + `dex_pool_state` instead                                                                                                    | Schema-only                     |
| `restaking_rewards` / `cross_chain_restaking_routes` / `restaking_operator_set` | —                              | —                               | (none — SOLAYER/PICASSO/CAMBRIAN removed 2026-06-02)                                     | Solayer/Picasso/Cambrian removed 2026-06-02 — no usable/decodable data source (operator decision). Venues + UAC capabilities + IS adapters wiped.                                                         | Removed                         |

## Solana Basis MVP data types (added 2026-06-01)

> Added 2026-06-01 from `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` Phase 1+2. Canonical UAC contracts:
> uac@f26097f9 (7 new types) + uac@9ad04ab0 (`InstrumentType.DEX_POOL`). SSOT:
> `/codex/04-architecture/drift-v2-data-sources.md`.

| data_type            | CLI / handler                                                                               | Source(s)                                                                          | Key columns                                                                                                                                       | Status                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `perp_trades`        | ~~`backfill_drift_v2_historical.py --data-types trades` / `DriftV2HistoricalIngester`~~     | ~~Drift Velocity Data API `/market/{symbol}/trades/{Y}/{M}/{D}?format=csv` (CSV)~~ | timestamp, side, base_amount_filled, quote_amount_filled, oracle_price, market_index                                                              | **REMOVED 2026-07-16** (operator ruling, all Solana perp DEXes dropped except Jupiter, not integrated) |
| `perp_mark_oracle`   | ~~(derived from `perp_funding` columns)~~                                                   | ~~Drift Velocity Data API `perp_funding` row `oraclePriceTwap` / `markPriceTwap`~~ | timestamp, market, oracle_price_twap, mark_price_twap                                                                                             | **REMOVED 2026-07-16**                                                                                 |
| `perp_open_interest` | ~~(derived from `perp_funding` columns)~~                                                   | ~~Drift Velocity Data API `perp_funding` row `baseAssetAmountWithAmm`~~            | timestamp, market, open_interest_base (signed)                                                                                                    | **REMOVED 2026-07-16**                                                                                 |
| `dex_pool_state`     | `backfill_solana_dex_state.py` / `OrcaWhirlpoolStateIngester` + `RaydiumClassicAmmIngester` | On-chain RPC via Alchemy archive (`getAccountInfo` at historical slot)             | timestamp, pool_address, sqrt_price_x96, liquidity, tick_current_index, fee_rate, price (Orca Whirlpool); reserveA/reserveB/fee (Raydium classic) | Production                                                                                             |
| `dex_orderbook`      | `backfill_solana_dex_state.py` (Phoenix branch — **stub at archive time**)                  | On-chain RPC of Phoenix market account state                                       | timestamp, market_address, bid_levels, ask_levels                                                                                                 | Stub (Phoenix decode P3 nice-to-have, tracked in `defi_manifest_canonicalisation_2026_06_01.md` § G)   |
| `dex_quote`          | `JupiterQuoteIngester`                                                                      | `https://quote-api.jup.ag/v6/quote?inputMint=...&outputMint=...&amount=...` (HTTP) | timestamp, input_mint, output_mint, input_amount, output_amount, route_json, fee_components                                                       | Production                                                                                             |
| `dex_trades`         | (Solana spot DEX per-swap; AMM venues)                                                      | On-chain RPC `getSignaturesForAddress(<pool_pda>)` filtered to swap instructions   | timestamp, pool_address, side, amount_in, amount_out, signer                                                                                      | Production (Orca/Raydium); Phoenix stub                                                                |

**Instrument-type mapping**: all 7 types use `InstrumentType.DEX_POOL` (uac@9ad04ab0) for AMM-state / orderbook / quote
rows on Solana DEX venues; `InstrumentType.PERPETUAL` was used for the 3 perp\_\* types on DRIFT until DRIFT was removed
entirely 2026-07-16 (operator ruling: all Solana perp DEXes dropped except Jupiter, not integrated) — those 3 perp\_\*
rows have no producing venue now.

**Output paths** (per CLAUDE.md bucket-name SSOT + asset-group vocabulary):

```
gs://market-data-tick-defi-prd-${PROJECT_ID}/raw_tick_data/by_date/day={Y-M-D}/
    pipeline_mode={batch|live}/asset_group=defi/venue={ORCA|RAYDIUM|PHOENIX|JUPITER}/
    chain=SOLANA/instrument_type={perpetual|dex_pool}/data_type={...}/ticks.parquet
```

The `pipeline_mode=` partition is the canonical batch/live distinguisher; the `--live --continuous` flag on the backfill
scripts is the concrete realization of CLAUDE.md "Live = batch (CRITICAL)" — same script, same handler, same partition
path, same schema.

## Protocol Coverage Matrix

| Protocol         | Chain(s)                           | Data Types                                                            |
| ---------------- | ---------------------------------- | --------------------------------------------------------------------- |
| UNISWAP_V2       | ETHEREUM                           | swap_events, pool_state                                               |
| UNISWAP_V3       | ETHEREUM, ARBITRUM, BASE, OPTIMISM | swap_events, pool_state, position_data                                |
| UNISWAP_V4       | ETHEREUM                           | swap_events, pool_state                                               |
| AAVE_V3          | ETHEREUM, ARBITRUM, POLYGON        | lending_metrics, liquidation_events, flash_loan_events, position_data |
| MORPHO           | ETHEREUM                           | lending_metrics, liquidation_events                                   |
| LIDO             | ETHEREUM                           | oracle_prices, staking_yields                                         |
| ETHERFI          | ETHEREUM                           | oracle_prices, staking_yields                                         |
| EIGENLAYER       | ETHEREUM                           | staking_yields                                                        |
| ACROSS           | ETHEREUM                           | bridge_events                                                         |
| STARGATE         | ETHEREUM                           | bridge_events                                                         |
| COMPOUND         | ETHEREUM                           | governance_events                                                     |
| AAVE (DAO)       | ETHEREUM                           | governance_events                                                     |
| UNISWAP (DAO)    | ETHEREUM                           | governance_events                                                     |
| FLASHBOTS        | ETHEREUM                           | mev_events                                                            |
| ALCHEMY          | ETHEREUM, ARBITRUM, BASE, OPTIMISM | token_transfers                                                       |
| ETHEREUM (chain) | N/A                                | gas_fees                                                              |

---

## Implementation Notes

### API Key Requirements

| Handler            | Secret Manager Key      | Fallback                |
| ------------------ | ----------------------- | ----------------------- |
| liquidation_events | `the-graph-api-key`     | `THE_GRAPH_API_KEY` env |
| flash_loan_events  | `the-graph-api-key`     | `THE_GRAPH_API_KEY` env |
| position_data      | `the-graph-api-key`     | `THE_GRAPH_API_KEY` env |
| bridge_events      | `the-graph-api-key`     | `THE_GRAPH_API_KEY` env |
| governance_events  | `the-graph-api-key`     | `THE_GRAPH_API_KEY` env |
| staking_yields     | None (public APIs)      | N/A                     |
| token_transfers    | `alchemy-api-key`       | `ALCHEMY_API_KEY` env   |
| mev_events         | None (public relay API) | N/A                     |

### Subgraph IDs

Registered in UAC `registry/capability_declarations/_defi.py` via `SUBGRAPH_IDS` dict. All handlers call
`get_subgraph_id(protocol, chain)` and skip gracefully if no ID is registered.

### Pagination

All subgraph queries use `first: 1000` — no cursor-based pagination for the initial implementation. High-volume data
types (token_transfers) use Alchemy's API which returns up to 1000 transfers per request.

### Shard-Level Failure Isolation

All handlers follow the MTDS shard-level isolation pattern: exceptions caught per-protocol/per-chain loop, recorded via
`DefiManifestRecorder.record_failed()`, and loop continues. No `raise` in per-shard loops.

### Availability Manifest

All handlers use `DefiManifestRecorder` to write honest-coverage entries:

- `record_captured(venue, chain, data_type, row_count, instrument_type, attempted_at)` — rows written
- `record_empty(venue, chain, data_type, attempted_at)` — zero rows, no exception (legitimate empty)
- `record_failed(venue, chain, data_type, error, attempted_at)` — exception caught
- `emit_expected_unattempted_for_remaining(data_type, declared_venues_chains, pipeline_mode)` — called once per handler
  run, immediately before `recorder.close()`; stamps `expected_unattempted` for every UAC-declared `(venue, chain)` this
  run never attempted for `data_type` (dedup via the recorder's own in-memory `_attempted_keys`, populated by the three
  methods above — no second manifest read). Denominator comes from UAC
  `get_defi_declared_venues_for_data_type(data_type, as_of)`
  (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`), which excludes any
  `(venue, chain)` listed in `DEFI_VENUE_COLLECTIBILITY_EXCEPTIONS[data_type]` — the one place a disposed-exclude venue
  (data proven genuinely unobtainable) is kept out of the denominator, so no handler needs its own per-venue skip check.
  **Venue/chain-grain only** — wired into `lending_indices_handler.py`, `liquidations_handler.py`,
  `lst_rates_handler.py`. NOT wired into the 5 per-instrument-grain handlers (`risk_params_handler.py`,
  `liquidation_events_handler.py`, `dex_pools_handler.py`, `dex_swaps_handler.py`, `oracle_prices_handler.py`) — calling
  it there would write an incorrect coarse-grain row; those data_types' honest-coverage instead comes from the v2
  `enumerate_expected_universe.py` enumerator's per-instrument denominator. It OOM'd daily for DeFi specifically from
  2026-07-14 through 2026-08-01 (streaming write + streaming read fixes plus a DeFi-only cpu=8/memory=32Gi stopgap fixed
  it 2026-08-02; `expected-universe-v2-defi` now completes on its normal 01:30 UTC schedule — see
  `/plans/archive/issues/defi_v2_expected_universe_enumerator_oom_2026_08_01.md`). Full design + rationale:
  `/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md`.

---

## Related Documents

- `/codex/02-data/mtds-data-source-coverage-matrix.md` — full MTDS source coverage
- `/codex/02-data/instrument-pipeline-defi.md` — DeFi instrument discovery pipeline
- `/codex/02-data/per-asset-group-bucket-layouts.md` — GCS bucket layout
- `deployment-service/configs/venue_data_types.yaml` — expected data type declarations per venue
- Plan: `plans/archive/defi_data_types_completeness_2026_04_24.plan.md`
