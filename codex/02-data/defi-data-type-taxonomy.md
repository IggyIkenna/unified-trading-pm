---
doc_type: codex-ssot
title: DeFi Data-Type Taxonomy
summary: >-
  Canonical per-(venue, data_type) ↔ adapter ↔ handler ↔ cluster-validation matrix for DeFi — data-type families
  (lending/DEX/aggregator/LST/vault/restaking+LRT/perp/native-staking/governance/bridge/MEV), per-family shard keys and
  schema fields, the bundled cluster-validation registry map, and per-protocol capture status (✅/◐/✗); wins over the
  catalogue + venue docs on disagreement.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, data-quality, manifest, features, catalogue, cefi, data-pipeline]
related:
  [
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-05-10
authoritative_for: [DeFi per-(venue, data_type) capture matrix, DeFi bundled cluster-validation registry map]
referenced_by:
  [
    /codex/02-data/README.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/04-architecture/amm-slippage-simulation.md,
    /codex/05-infrastructure/chain-rpc-mev-tenderly.md,
  ]
owner:
last_reviewed: 2026-07-15
code_refs:
---

# DeFi Data-Type Taxonomy

> SSOT for the per-venue × per-data_type matrix: what we capture, where, in what shape, with what cluster validation.
> Last updated 2026-05-15 (solana_lst_native_staking_adapters_2026_05_14 Phase 5 — added native_staking_rates family +
> SOLANA-NATIVE-SOLANA coverage row); prior: 2026-05-12 (codex audit IN-15 — 3-doc consolidation cross-link added).

> ## DeFi 3-doc reconciliation (codex audit IN-15 2026-05-12)
>
> Three DeFi codex docs form an overlapping set. **This doc — `defi-data-type-taxonomy.md` — is the canonical
> per-(venue, data_type, cluster-validation, canonical-schema) matrix.** The other two reference it:
>
> | Doc                                                                      | Role                                                                                 |
> | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
> | [`defi-venue-protocol-catalogue.md`](./defi-venue-protocol-catalogue.md) | Per-protocol status legend + per-venue PRODUCTION-DEV-PLANNED tracking               |
> | [`defi-data-types-catalog.md`](./defi-data-types-catalog.md)             | Per-data_type capture overview + GCS path convention                                 |
> | **`defi-data-type-taxonomy.md`** (this doc)                              | **Canonical per-(venue, data_type) ↔ adapter ↔ handler ↔ cluster-validation matrix** |
>
> When the three disagree, this doc + the UAC registries (`defi_venues.py` + `defi_venue_capabilities.py` +
> `market_data_categories.py:NEEDS_CANDLE_PROCESSING`) win. The other two are refresh-as-they-go summaries. Catalogue
> audits DF-14/DF-15/DF-16 motivate this rule — those findings flagged data_types declared in the taxonomy but with no
> venue-capability row (i.e. the matrix had a hole). Going forward, every new (venue, data_type) row added to the
> taxonomy MUST be matched by a UAC `defi_venue_capabilities.py` row.

This doc complements [`defi-venue-protocol-catalogue.md`](defi-venue-protocol-catalogue.md) (which lists protocols) and
[`defi-data-types-catalog.md`](defi-data-types-catalog.md) (which lists the 14 MTDS data types and their shard keys).
This doc is the **per-(venue, data_type) matrix** — for every protocol in the catalogue, what data_types are captured,
what's the canonical schema, and what cluster validation rule applies.

## Canonical data-type families

| Family                                        | Members                                                                                                                            |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Lending**                                   | `lending_indices`, `oracle_prices`, `rewards`, `risk_params`, `liquidation_events`, `flash_loan_events`, `position_data`           |
| **DEX (spot)**                                | `dex_swaps`, `dex_pools`, `position_data`                                                                                          |
| **DEX (aggregator)**                          | `aggregator_routes` (read-only API capture)                                                                                        |
| **LST**                                       | `lst_rates`, `oracle_prices`, `staking_yields`                                                                                     |
| **Vault**                                     | `vault_share_price`, `vault_apy`, `vault_tvl`                                                                                      |
| **Restaking + LRT**                           | `restaking_rewards` (formerly `eigenlayer_rewards`), `staking_yields`, `restaking_yields`, `slashing_events`                       |
| **Perp** (DeFi-side; CeFi handled separately) | `perp_funding`, `derivative_ticker` (added 2026-07-15 — canonical raw-funding home for ALL perps), `liquidations`, `oracle_prices` |
| **Native Staking (Solana)**                   | `native_staking_rates` (NEW per `solana_lst_native_staking_adapters_2026_05_14` Phase 5)                                           |
| **Governance**                                | `governance_proposals` (NEW per `defi_simulation_realism` Phase 1C)                                                                |
| **Bridge**                                    | `bridge_events`                                                                                                                    |
| **MEV**                                       | `mev_events`                                                                                                                       |
| **Token transfers**                           | `token_transfers`                                                                                                                  |

## Per-protocol-family data-type matrix

### Lending (Aave V3 / Compound V3 / Spark / Morpho / Morpho Blue / Fluid / Radiant / Kamino)

| data_type            | Source                                                         | Shard key                                                                                  | Cluster validation                | Schema fields                                                                                                                                                                                           |
| -------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lending_indices`    | TheGraph subgraph (EVM) / Solana RPC (Kamino)                  | `(asset_group=defi, chain, venue, data_type, instrument_type=lending, instrument_id, day)` | per-day per-reserve min row count | symbol, ts_event, venue, chain, supply_apy, borrow_apy, utilization_rate, total_supply, total_borrow, liquidityIndex, variableBorrowIndex                                                               |
| `oracle_prices`      | Chainlink eth_call / Pyth Hermes                               | `(asset_group=defi, chain, venue, data_type, instrument_id, day)`                          | per-day per-feed min row count    | feed_id, ts_event, chain, oracle, price, confidence, updated_at, round_id                                                                                                                               |
| `rewards`            | TheGraph subgraph                                              | `(asset_group=defi, chain, venue, data_type, instrument_id, day)`                          | per-day per-reserve               | symbol, ts_event, reward_token, reward_amount, recipient                                                                                                                                                |
| `risk_params`        | UAC SSOT `defi_reserve_params.py` (snapshot per change)        | `(asset_group=defi, chain, venue, data_type, instrument_id, day)`                          | per-change-event row              | symbol, ts_event, ltv, liquidation_threshold, liquidation_bonus, can_be_collateral, can_be_borrowed, borrow_cap, supply_cap, reserve_factor, optimal_utilization_rate, irm_base, irm_slope1, irm_slope2 |
| `liquidation_events` | TheGraph subgraph                                              | `(asset_group=defi, chain, venue, data_type, day)`                                         | per-day                           | tx_hash, ts_event, liquidator, liquidatee, collateral_asset, debt_asset, collateral_amount, debt_amount, liquidation_bonus_realised                                                                     |
| `flash_loan_events`  | TheGraph subgraph                                              | `(asset_group=defi, chain, venue, data_type, day)`                                         | per-day                           | tx_hash, ts_event, borrower, asset, amount, fee_premium, success                                                                                                                                        |
| `position_data`      | TheGraph subgraph (per-user position snapshots, top-K by debt) | `(asset_group=defi, chain, venue, data_type, day)`                                         | sample-bundle                     | user_address, ts_event, asset, supply_balance, borrow_balance, health_factor                                                                                                                            |

> **Lending instrument_type keying (INTERIM):** the market/event lending DATA_TYPES above key to the market-level
> `lending` (EVM) / `solana_lending` (Solana / Kamino) instrument_type — NOT the `a_token`/`debt_token` HOLDINGS split
> (that is the operator-ruled IS reference/holdings SSOT). The Wave-B flat-`LENDING`-retire over-reached (broke 5+ MTDS
> writers) and was reversed (`wn12e7itc`); whether these DATA_TYPES adopt A_TOKEN/DEBT_TOKEN was **RULED 2026-07-20
> (operator D2 — FULL retire)** (⛔ corrected 2026-07-20: ~~"is PARKED for the operator
> (`issues/canonical_closeout_open_questions_2026_07_18.md` § D)"~~). The FULL retire — market/event lending data_types
> also adopt the split — is the RULED TARGET but is **NOT yet implemented** (`migration_pending`), gated on
> `../../plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`; the uniform-`LENDING` interim holds until
> then. It is neither refused nor flagged — `migration_pending`, not an open question. See
> `defi-canonical-naming-ssot.md` (instrument_type row, D2) and `reconciliation-finding-taxonomy.md` §5.2.

### DEX (spot)

| data_type       | Source                                              | Shard key                                                                               | Cluster validation                 | Schema fields                                                                                                                                                                                                                      |
| --------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dex_swaps`     | TheGraph subgraph (EVM) / Solana RPC (Raydium/Orca) | `(asset_group=defi, chain, venue, data_type, instrument_type=pool, instrument_id, day)` | per-day per-pool min row count     | symbol, ts_event, venue, chain, pool_address, token_in, token_out, amount_in, amount_out, price, sender, recipient                                                                                                                 |
| `dex_pools`     | TheGraph subgraph hourly snapshots                  | `(asset_group=defi, chain, venue, data_type, instrument_id, day)`                       | per-day per-pool 24-hour-snapshots | symbol, ts_event, pool_address, tvl_usd, volume_24h, fee_tier, sqrtPriceX96 (V3), tick (V3), tick_liquidity_bitmap (V3), reserves[] (V2), D_invariant (Curve), gamma (Curve crypto), weights[] (Balancer), bin_step (TraderJoe V2) |
| `position_data` | TheGraph (V3+ NFT positions)                        | `(asset_group=defi, chain, venue, data_type, instrument_id, day)`                       | per-day                            | position_token_id, owner, ts_event, pool_address, tick_lower, tick_upper, liquidity                                                                                                                                                |

### DEX (aggregator)

| data_type           | Source                                                   | Shard key                                          | Cluster validation | Schema fields                                                                                        |
| ------------------- | -------------------------------------------------------- | -------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------- |
| `aggregator_routes` | Jupiter API (Solana) / 1inch API / 0x API / ParaSwap API | `(asset_group=defi, chain, venue, data_type, day)` | sample-bundle      | ts_event, aggregator, token_in, token_out, amount_in, route_legs (json), output_amount, slippage_bps |

### LST

| data_type        | Source                                                                                              | Shard key                                                         | Cluster validation | Schema fields                                                                  |
| ---------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------ |
| `lst_rates`      | On-chain contract reads (Lido oracle / Rocket Pool / Jito) / Pyth Hermes (Solana)                   | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-LST    | symbol, ts_event, lst_token, base_asset, exchange_rate, peg_drift_bps          |
| `oracle_prices`  | Chainlink (LST/USD feeds) / Pyth                                                                    | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-feed   | feed_id, ts_event, oracle, price, confidence, updated_at                       |
| `staking_yields` | On-chain reads (Lido oracle pushes / Rocket Pool node operator distribution / Solana validator MEV) | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-LST    | symbol, ts_event, period_apr, native_staking_apr, mev_apr, last_oracle_push_ts |

### Vault

| data_type           | Source                                                             | Shard key                                                         | Cluster validation | Schema fields                                                                    |
| ------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------- |
| `vault_share_price` | On-chain `convertToAssets(1e18)` (ERC-4626) / vault-specific reads | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-vault  | symbol, ts_event, vault_address, share_to_asset_rate, total_assets, total_supply |
| `vault_apy`         | TheGraph / DefiLlama / vault-specific harvest events               | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-vault  | symbol, ts_event, period_apr, fees_bps                                           |
| `vault_tvl`         | TheGraph hourly                                                    | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-vault  | symbol, ts_event, tvl_usd, deposits_24h, withdrawals_24h                         |

### Restaking + LRT

| data_type                                                      | Source                                                                                       | Shard key                                                         | Cluster validation | Schema fields                                                                                                       |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `restaking_rewards`                                            | EigenLayer + Symbiotic + Karak + Jito-restaking subgraphs / on-chain `RewardsClaimed` events | `(asset_group=defi, chain, venue, data_type, day)`                | per-day            | tx_hash, ts_event, operator, recipient, reward_token, amount, avs (nullable)                                        |
| `restaking_yields`                                             | Aggregated from `restaking_rewards` + UAC `StakingYieldDecomposition`                        | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-LRT    | symbol, ts_event, native_staking_apr, mev_apr, restaking_avs_apr, lrt_protocol_fee_bps, seasonal_points_implied_apr |
| `slashing_events` (NEW per `defi_simulation_realism` Phase 1E) | Beacon chain + Solana validator gossip / per-AVS slashing events                             | `(asset_group=defi, chain, data_type, day)`                       | per-day            | tx_hash, ts_event, chain, validator_id, slashed_at_epoch, slashed_amount_native, slashing_reason                    |

### Perp (DeFi-side; CeFi handled in CeFi taxonomy)

CeFi-axis classification per FLAG 1 RESOLUTION; on-chain CLOBs (Hyperliquid / Aster / Extended / Lighter) capture under
cefi axis (Pacifica was a fifth venue here until removed 2026-07-16 -- operator ruling, all Solana perp DEXes dropped
except Jupiter, not integrated). The defi-axis (on-chain settlement, not CLOB-style) perp category is defined via
`DEFI_PERP_VENUES` in `unified_api_contracts/registry/defi_venues.py`, but is currently EMPTY — GMX, its sole venue, was
REMOVED 2026-07-25 (see `defi_gmx_venue_removal_2026_07_25.md`); DRIFT-SOLANA was the other defi-axis perp venue here
until removed 2026-07-16, same ruling.

**derivative_ticker canonicalisation (operator ruling 2026-07-15,
`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`)**: `derivative_ticker` is the canonical
RAW-funding home for EVERY perp venue, defi-axis and cefi-axis alike — captured at the highest resolution each source
offers, even where the source has no open interest (OI/mark/index fields nullable; `funding_rate` + `ts_event`
mandatory). `perp_funding` stays the per-interval canonical VIEW (annualizing a single rate into `annualized_rate` is
fine — a unit conversion, not aggregation) but MUST NOT carry venue-specific rolling-window aggregates (the Drift-only
`funding_rate_24h`/`funding_rate_7d`/`funding_rate_30d` columns were removed 2026-07-15 —
`market-tick-data-service/.../cli/handlers/solana_defi_drift.py`'s `_collect_drift`). Per-venue resolution (verified
2026-07-15, see the issue doc's coverage table for full evidence + file:line):

| Venue                            | Axis     | derivative_ticker source                                                                                           | OI at source        | Notes                                                                                                                                                               |
| -------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ~~GMX-ARBITRUM / GMX-AVALANCHE~~ | ~~defi~~ | ~~The Graph `fundingRateChangedEvents` (event-driven, dual-written alongside `perp_funding` from the SAME fetch)~~ | —                   | **REMOVED 2026-07-25** (synthetic OI-imbalance proxy, not real funding-rate data; see `defi_gmx_venue_removal_2026_07_25.md`). Native query had no OI field at all. |
| ~~DRIFT-SOLANA~~                 | ~~defi~~ | ~~Drift Data API `/fundingRates` (per-settlement)~~                                                                | —                   | **REMOVED 2026-07-16** (operator ruling, all Solana perp DEXes dropped except Jupiter, not integrated).                                                             |
| HYPERLIQUID                      | cefi     | S3 `hyperliquid-archive/asset_ctxs/` (real OI) + REST fallback                                                     | Yes (S3), No (REST) | `hyperliquid_s3.py`.                                                                                                                                                |
| ASTER                            | cefi     | `/fapi/v1/fundingRate` REST                                                                                        | No                  | `_umi_aster.py`.                                                                                                                                                    |
| ~~PACIFICA-SOLANA~~              | ~~cefi~~ | ~~`/funding_rate/history` REST~~                                                                                   | —                   | **REMOVED 2026-07-16** (operator ruling, same as above).                                                                                                            |
| EXTENDED-STARKNET                | cefi     | `/info/{symbol}/funding` REST                                                                                      | No                  | `_umi_extended.py`.                                                                                                                                                 |
| LIGHTER-ZKSYNC                   | cefi     | Tardis archive, `date >= 2026-04-17` only                                                                          | Yes (Tardis)        | Native REST has zero funding code; a public current-snapshot endpoint exists but has no history — Tardis is the real source.                                        |

MANGO-SOLANA / ZETA-SOLANA / FLASH-SOLANA — DELETED 2026-07-15 (operator ruling): the whole vertical slice (URDI
reference-data adapters, factory registrations, UAC venue-adapter-key entries) was removed rather than completing
onboarding. All 3 declared API hosts were dead and DeFiLlama TVL was ~$0; zero MTDS market-data capture was ever wired
for any of them (not derivative_ticker-specific — no trades/book_snapshot either). See
`/codex/04-architecture/solana-defi-coverage.md` for the full removal record.

### Native Staking — Solana (NEW per `solana_lst_native_staking_adapters_2026_05_14` Phase 5)

Venue: `SOLANA-NATIVE-SOLANA`. Chain: `SOLANA`. One row per target date (aligned to Solana epoch boundaries). Aggregate
mode (`validator_vote_account="AGGREGATE"`) ships without credentials. Per-validator mode requires Helius API key
(`BLOCKED-CREDENTIALS` ping in `ikenna_orchestrator/pings/slot_3.md` 2026-05-15).

| data_type              | Source                                                                                                                                  | Shard key                                                                      | Cluster validation                        | Schema fields                                                               |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------- |
| `native_staking_rates` | Solana RPC `getEpochInfo`+`getInflationRate` (live) / inflation schedule (historical) + Helius APY (per-validator, BLOCKED-CREDENTIALS) | `(asset_group=defi, chain=SOLANA, venue=SOLANA-NATIVE-SOLANA, data_type, day)` | not bundled (1 row/day in aggregate mode) | epoch, validator_vote_account, commission_pct, base_apy, mev_apy, total_apy |

### Governance (NEW per `defi_simulation_realism` Phase 1C)

| data_type              | Source                                                                                      | Shard key                                          | Cluster validation   | Schema fields                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `governance_proposals` | On-chain Governor events (Aave / Compound / Spark) + Snapshot off-chain API (Lido / others) | `(asset_group=defi, chain, venue, data_type, day)` | per-day per-protocol | proposal_id, ts_event, protocol, proposer, created_at, voting_start, voting_end, executed_at, payload (calldata + targets), status |

### Bridge / MEV / Token transfers

Existing per [`defi-data-types-catalog.md`](defi-data-types-catalog.md). No changes from this audit.

## GCS path convention

Shared with [`defi-data-types-catalog.md`](defi-data-types-catalog.md):

```
gs://{tick-defi-bucket}/raw_tick_data/by_date/day={date}/pipeline_mode={mode}_{source}/asset_group=defi/
  venue={PROTOCOL}/chain={CHAIN}/instrument_type={type}/data_type={data_type}/ticks.parquet
```

`venue=` is the bare canonical PROTOCOL (`AAVE_V3`, `UNISWAP_V3`, `LIDO` — never `AAVEV3`/`AAVE`) and `chain=` is a
SEPARATE hive segment (`ETHEREUM`, `ARBITRUM`, `SOLANA`) — the two are NEVER combined into one `PROTOCOL-CHAIN` segment.
`instrument_type={type}` is lowercase in the path (upper only in the canonical id segment). Per the workspace
asset-group vocabulary rule, new writes use `asset_group=defi` (canonical hive key); legacy `category=defi` (and the
legacy combined `venue={VENUE}-{CHAIN}` shape) is preserved on disk without re-keying. Readers try canonical first, fall
back to legacy.

> **📌 CANONICAL PATH (2026-07-10) — the fully-canonical raw path carries a `pipeline_mode={mode}_{source}` hive segment
> LEFT of `asset_group=`** (as shown above), with `venue=` the bare canonical PROTOCOL and a SEPARATE `chain=` segment.
> SSOT: [`pipeline-mode-partition.md`](pipeline-mode-partition.md) (source-aware `{mode}_{source}[_{transport}]`;
> readers PREFIX-MATCH). Writers emit this canonical shape PRIMARY; the legacy no-`pipeline_mode=` /
> combined-`venue={VENUE}-{CHAIN}` shape coexists on disk until the per-AG canonical migration deletes it.

## Cluster validation matrix

Per CLAUDE.md "Cluster validation MANDATORY at `record_captured` for bundled shards" — every bundled data_type requires
`expected_root_clusters` + `cluster_extractor` kwargs at write time. This table declares the bundle unit + cluster
registry source per data_type.

**Static enforcement (codex audit IN-11 2026-05-12)**: QG STEP 5.64 ratchet enforces statically — the AST-walk script at
`unified-trading-pm/scripts/quality_gates/check_cluster_validation_kwargs.py` (see CLAUDE.md § "Manifest + honest
absence" cluster-validation rule) fails any callsite to `record_captured()` for a bundled data_type below without the
two kwargs. UTL guard raises `MissingClusterValidationError` at runtime as second line of defence. **Which adapters MUST
pass cluster kwargs** = every adapter writing a bundled data_type below; if a row is missing the kwargs at write time,
the row is a candidate for catalogue-audit findings (cross-ref: catalogue_audit_sports SP-10 "sports bundle writers",
catalogue_audit_prediction PR-6 "PREDICTION_GROUPS empty placeholder", catalogue_audit_tradfi TF-6 "no futures_chain row
for any TradFi venue").

| data_type              | Bundled?           | Cluster unit | Cluster registry SSOT                                  |
| ---------------------- | ------------------ | ------------ | ------------------------------------------------------ |
| `lending_indices`      | per-(venue, chain) | per-reserve  | UAC `defi_reserve_params.py` per-protocol reserve list |
| `oracle_prices`        | per-(venue, chain) | per-feed     | UAC `_defi_oracle_coverage.py`                         |
| `dex_swaps`            | per-pool           | n/a          | n/a (per-shard)                                        |
| `dex_pools`            | per-(venue, chain) | per-pool     | TheGraph + UAC top-K-by-liquidity                      |
| `lst_rates`            | per-(venue, chain) | per-LST      | UAC `defi_venue_capabilities.py` LST list              |
| `vault_share_price`    | per-(venue, chain) | per-vault    | UAC vault registry (Phase 1A)                          |
| `restaking_rewards`    | per-(venue, chain) | per-AVS      | UAC AVS registry (Phase 1A)                            |
| `governance_proposals` | per-protocol       | per-proposal | n/a (per-event)                                        |

## Per-protocol coverage (extends `defi-venue-protocol-catalogue.md`)

For each protocol in the catalogue, this matrix declares which data_types are captured. ✅ = captured today; ◐ = partial
(per silent-zero / partial backfill); ✗ = zero capture.

### Lending

| Protocol                | lending_indices | oracle_prices | rewards | risk_params | liquidation_events | flash_loan_events | position_data |
| ----------------------- | --------------- | ------------- | ------- | ----------- | ------------------ | ----------------- | ------------- |
| Aave V3 Ethereum        | ◐ silent-zero   | ✅            | ✅      | ✅          | ✅                 | ✅                | ✅            |
| Aave V3 multi-chain (9) | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Compound V3             | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Spark                   | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Morpho                  | ◐ Ethereum      | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Morpho Blue             | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Fluid                   | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Radiant                 | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |
| Kamino (Solana)         | ✗               | ✗             | ✗       | ✗           | ✗                  | ✗                 | ✗             |

### DEX (spot)

| Protocol         | dex_swaps | dex_pools | position_data                 |
| ---------------- | --------- | --------- | ----------------------------- |
| Uniswap V2       | ✅        | ✅        | n/a (V2 has no NFT positions) |
| Uniswap V3       | ✅        | ✅        | ✅ top-K                      |
| Uniswap V4       | ✗         | ✗         | ✗                             |
| Curve            | ✅        | ✅        | n/a                           |
| Balancer         | ✗         | ✗         | n/a                           |
| Sushi V2 / V3    | ✗         | ✗         | ✗                             |
| PancakeSwap V3   | ✗         | ✗         | ✗                             |
| Camelot V3       | ✗         | ✗         | ✗                             |
| Aerodromeq V3    | ✗         | ✗         | ✗                             |
| Velodrome V2     | ✗         | ✗         | ✗                             |
| TraderJoe V2     | ✗         | ✗         | ✗                             |
| Raydium (Solana) | ✗         | ✗         | ✗                             |
| Orca (Solana)    | ✗         | ✗         | ✗                             |

### DEX aggregator

| Protocol         | aggregator_routes |
| ---------------- | ----------------- |
| Jupiter (Solana) | ✗                 |
| 1inch            | ✗                 |
| 0x               | ✗                 |
| ParaSwap         | ✗                 |

### LST

| Protocol          | lst_rates                                                       | oracle_prices | staking_yields |
| ----------------- | --------------------------------------------------------------- | ------------- | -------------- |
| Lido              | ✅                                                              | ✅            | ✅             |
| Ether.fi          | ✅                                                              | ✅            | ✅             |
| Ethena            | ◐ DefiLlama only                                                | ✗             | ✗              |
| Jito (Solana)     | ✅ Pyth-based, ~monthly                                         | ✅ Pyth       | ✗              |
| Marinade (Solana) | ✅ Pyth-based, ~monthly                                         | ✅ Pyth       | ✗              |
| Rocket Pool       | ◐ adapter shipped (lst_rocket_pool_adapter.py, no backfill yet) | ✗             | ✗              |
| Solblaze          | ◐ adapter shipped (lst_solblaze_adapter.py, no backfill yet)    | ✗             | ✗              |

### Vault

| Protocol | vault_share_price                                                                                      | vault_apy | vault_tvl |
| -------- | ------------------------------------------------------------------------------------------------------ | --------- | --------- |
| Yearn    | ◐ MTDS adapter shipped (vault_yearn_adapter.py), instruments adapter shipped (yearn.py), no backfill   | ✗         | ✗         |
| Convex   | ◐ MTDS adapter shipped (vault_convex_adapter.py), instruments adapter shipped (convex.py), no backfill | ✗         | ✗         |
| Beefy    | ◐ MTDS adapter shipped (vault_beefy_adapter.py), instruments adapter shipped (beefy.py), no backfill   | ✗         | ✗         |
| Pendle   | ◐ MTDS adapter shipped (vault_pendle_adapter.py), instruments adapter shipped (pendle.py), no backfill | ✗         | ✗         |
| Idle     | ◐ MTDS adapter shipped (vault_idle_adapter.py), instruments adapter shipped (idle.py), no backfill     | ✗         | ✗         |

### Restaking + LRT

| Protocol                | restaking_rewards                                                                                                | restaking_yields | slashing_events |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------- | --------------- |
| EigenLayer              | ✗ (declared in UAC, no adapter)                                                                                  | ✗                | ✗               |
| Symbiotic               | ◐ MTDS adapter shipped (restaking_symbiotic_adapter.py), instruments adapter shipped (symbiotic.py), no backfill | ✗                | ✗               |
| Karak                   | ◐ MTDS adapter shipped (restaking_karak_adapter.py), instruments adapter shipped (karak.py), no backfill         | ✗                | ✗               |
| Renzo                   | ◐ instruments adapter shipped (renzo.py), no MTDS adapter, no backfill                                           | ✗                | ✗               |
| KelpDAO                 | ◐ instruments adapter shipped (kelpdao.py), no MTDS adapter, no backfill                                         | ✗                | ✗               |
| Puffer                  | ◐ instruments adapter shipped (puffer.py), no MTDS adapter, no backfill                                          | ✗                | ✗               |
| Jito restaking (Solana) | ◐ MTDS adapter shipped (restaking_jito_adapter.py), instruments adapter shipped (jito_restaking.py), no backfill | ✗                | ✗               |

### Native Staking (Solana)

| Protocol             | native_staking_rates                                                                                     |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| SOLANA-NATIVE-SOLANA | ◐ aggregate row only (MTDS@1ec3a46; per-validator BLOCKED-CREDENTIALS Helius; backlog: 2020-03-16→today) |

### Governance

| Protocol        | governance_proposals |
| --------------- | -------------------- |
| Aave            | ✗                    |
| Compound        | ✗                    |
| Spark           | ✗                    |
| Lido (Snapshot) | ✗                    |
| Uniswap         | ✗                    |

## Cross-references

- [`defi-venue-protocol-catalogue.md`](defi-venue-protocol-catalogue.md) — protocol catalogue.
- [`defi-data-types-catalog.md`](defi-data-types-catalog.md) — original 14-data-type catalog (this doc extends it).
- [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) — manifest schema.
- [`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md) — empty/missing handling per
  data_type.
- [`amm-slippage-simulation.md`](/codex/04-architecture/amm-slippage-simulation.md) — how `dex_pools` data feeds
  matching engine.
- Plan:
  [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md)
  Phase 3 owns the buildout for every ✗ above.

## Update protocol

When adding a new data_type:

1. Add to "Canonical data-type families" + "Per-protocol-family data-type matrix" with full schema.
2. Add to "Cluster validation matrix" if bundled.
3. Add UAC entry: `BUNDLED_DATA_TYPES` + `EMPTY_CONFIRMED_REASONS` if applicable.
4. Add cluster registry SSOT entry.
5. Add column to "Per-protocol coverage" section.
6. Update `availability-manifest-and-data-status.md`.
