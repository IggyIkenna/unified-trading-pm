---
scope: [engineer, admin]
---

# DeFi Data-Type Taxonomy

> SSOT for the per-venue × per-data_type matrix: what we capture, where, in what shape, with what cluster validation.
> Last updated 2026-05-10 (defi_catalogue_chain_primitives_2026_05_10 Phase 3J).

This doc complements
[`defi-venue-protocol-catalogue.md`](defi-venue-protocol-catalogue.md) (which lists protocols)
and [`defi-data-types-catalog.md`](defi-data-types-catalog.md) (which lists the 14 MTDS data types and their shard
keys). This doc is the **per-(venue, data_type) matrix** — for every protocol in the catalogue, what data_types are
captured, what's the canonical schema, and what cluster validation rule applies.

## Canonical data-type families

| Family | Members |
| ------ | ------- |
| **Lending** | `lending_indices`, `oracle_prices`, `rewards`, `risk_params`, `liquidation_events`, `flash_loan_events`, `position_data` |
| **DEX (spot)** | `dex_swaps`, `dex_pools`, `position_data` |
| **DEX (aggregator)** | `aggregator_routes` (read-only API capture) |
| **LST** | `lst_rates`, `oracle_prices`, `staking_yields` |
| **Vault** | `vault_share_price`, `vault_apy`, `vault_tvl` |
| **Restaking + LRT** | `restaking_rewards` (formerly `eigenlayer_rewards`), `staking_yields`, `restaking_yields`, `slashing_events` |
| **Perp** (DeFi-side; CeFi handled separately) | `perp_funding`, `liquidations`, `oracle_prices` |
| **Governance** | `governance_proposals` (NEW per `defi_simulation_realism` Phase 1C) |
| **Bridge** | `bridge_events` |
| **MEV** | `mev_events` |
| **Token transfers** | `token_transfers` |

## Per-protocol-family data-type matrix

### Lending (Aave V3 / Compound V3 / Spark / Morpho / Morpho Blue / Fluid / Radiant / Kamino)

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `lending_indices` | TheGraph subgraph (EVM) / Solana RPC (Kamino) | `(asset_group=defi, chain, venue, data_type, instrument_type=lending, instrument_id, day)` | per-day per-reserve min row count | symbol, ts_event, venue, chain, supply_apy, borrow_apy, utilization_rate, total_supply, total_borrow, liquidityIndex, variableBorrowIndex |
| `oracle_prices` | Chainlink eth_call / Pyth Hermes | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-feed min row count | feed_id, ts_event, chain, oracle, price, confidence, updated_at, round_id |
| `rewards` | TheGraph subgraph | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-reserve | symbol, ts_event, reward_token, reward_amount, recipient |
| `risk_params` | UAC SSOT `defi_reserve_params.py` (snapshot per change) | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-change-event row | symbol, ts_event, ltv, liquidation_threshold, liquidation_bonus, can_be_collateral, can_be_borrowed, borrow_cap, supply_cap, reserve_factor, optimal_utilization_rate, irm_base, irm_slope1, irm_slope2 |
| `liquidation_events` | TheGraph subgraph | `(asset_group=defi, chain, venue, data_type, day)` | per-day | tx_hash, ts_event, liquidator, liquidatee, collateral_asset, debt_asset, collateral_amount, debt_amount, liquidation_bonus_realised |
| `flash_loan_events` | TheGraph subgraph | `(asset_group=defi, chain, venue, data_type, day)` | per-day | tx_hash, ts_event, borrower, asset, amount, fee_premium, success |
| `position_data` | TheGraph subgraph (per-user position snapshots, top-K by debt) | `(asset_group=defi, chain, venue, data_type, day)` | sample-bundle | user_address, ts_event, asset, supply_balance, borrow_balance, health_factor |

### DEX (spot)

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `dex_swaps` | TheGraph subgraph (EVM) / Solana RPC (Raydium/Orca) | `(asset_group=defi, chain, venue, data_type, instrument_type=spot_asset, instrument_id, day)` | per-day per-pool min row count | symbol, ts_event, venue, chain, pool_address, token_in, token_out, amount_in, amount_out, price, sender, recipient |
| `dex_pools` | TheGraph subgraph hourly snapshots | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-pool 24-hour-snapshots | symbol, ts_event, pool_address, tvl_usd, volume_24h, fee_tier, sqrtPriceX96 (V3), tick (V3), tick_liquidity_bitmap (V3), reserves[] (V2), D_invariant (Curve), gamma (Curve crypto), weights[] (Balancer), bin_step (TraderJoe V2) |
| `position_data` | TheGraph (V3+ NFT positions) | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day | position_token_id, owner, ts_event, pool_address, tick_lower, tick_upper, liquidity |

### DEX (aggregator)

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `aggregator_routes` | Jupiter API (Solana) / 1inch API / 0x API / ParaSwap API | `(asset_group=defi, chain, venue, data_type, day)` | sample-bundle | ts_event, aggregator, token_in, token_out, amount_in, route_legs (json), output_amount, slippage_bps |

### LST

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `lst_rates` | On-chain contract reads (Lido oracle / Rocket Pool / Jito) / Pyth Hermes (Solana) | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-LST | symbol, ts_event, lst_token, base_asset, exchange_rate, peg_drift_bps |
| `oracle_prices` | Chainlink (LST/USD feeds) / Pyth | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-feed | feed_id, ts_event, oracle, price, confidence, updated_at |
| `staking_yields` | On-chain reads (Lido oracle pushes / Rocket Pool node operator distribution / Solana validator MEV) | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-LST | symbol, ts_event, period_apr, native_staking_apr, mev_apr, last_oracle_push_ts |

### Vault

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `vault_share_price` | On-chain `convertToAssets(1e18)` (ERC-4626) / vault-specific reads | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-vault | symbol, ts_event, vault_address, share_to_asset_rate, total_assets, total_supply |
| `vault_apy` | TheGraph / DefiLlama / vault-specific harvest events | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-vault | symbol, ts_event, period_apr, fees_bps |
| `vault_tvl` | TheGraph hourly | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-vault | symbol, ts_event, tvl_usd, deposits_24h, withdrawals_24h |

### Restaking + LRT

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `restaking_rewards` | EigenLayer + Symbiotic + Karak + Jito-restaking subgraphs / on-chain `RewardsClaimed` events | `(asset_group=defi, chain, venue, data_type, day)` | per-day | tx_hash, ts_event, operator, recipient, reward_token, amount, avs (nullable) |
| `restaking_yields` | Aggregated from `restaking_rewards` + UAC `StakingYieldDecomposition` | `(asset_group=defi, chain, venue, data_type, instrument_id, day)` | per-day per-LRT | symbol, ts_event, native_staking_apr, mev_apr, restaking_avs_apr, lrt_protocol_fee_bps, seasonal_points_implied_apr |
| `slashing_events` (NEW per `defi_simulation_realism` Phase 1E) | Beacon chain + Solana validator gossip / per-AVS slashing events | `(asset_group=defi, chain, data_type, day)` | per-day | tx_hash, ts_event, chain, validator_id, slashed_at_epoch, slashed_amount_native, slashing_reason |

### Perp (DeFi-side; CeFi handled in CeFi taxonomy)

CeFi-axis classification per FLAG 1 RESOLUTION; on-chain CLOBs (Hyperliquid / Aster / GMX / DRIFT / Pacifica /
Extended / Lighter) capture under cefi axis. DeFi-axis perp would only apply to non-CLOB perps if any; currently
none.

### Governance (NEW per `defi_simulation_realism` Phase 1C)

| data_type | Source | Shard key | Cluster validation | Schema fields |
| --------- | ------ | --------- | ------------------ | ------------- |
| `governance_proposals` | On-chain Governor events (Aave / Compound / Spark) + Snapshot off-chain API (Lido / others) | `(asset_group=defi, chain, venue, data_type, day)` | per-day per-protocol | proposal_id, ts_event, protocol, proposer, created_at, voting_start, voting_end, executed_at, payload (calldata + targets), status |

### Bridge / MEV / Token transfers

Existing per [`defi-data-types-catalog.md`](defi-data-types-catalog.md). No changes from this audit.

## GCS path convention

Shared with [`defi-data-types-catalog.md`](defi-data-types-catalog.md):

```
gs://{tick-defi-bucket}/raw_tick_data/by_date/day={date}/category=defi/
  venue={VENUE}-{CHAIN}/instrument_type={type}/data_type={data_type}/ticks.parquet
```

Per the workspace asset-group vocabulary rule, new writes use `asset_group=defi` (canonical hive key); legacy
`category=defi` preserved on disk without re-keying. Readers try canonical first, fall back to legacy.

## Cluster validation matrix

Per CLAUDE.md "Cluster validation MANDATORY at `record_captured` for bundled shards" — every bundled data_type
requires `expected_root_clusters` + `cluster_extractor` kwargs at write time. This table declares the bundle
unit + cluster registry source per data_type:

| data_type | Bundled? | Cluster unit | Cluster registry SSOT |
| --------- | -------- | ------------ | --------------------- |
| `lending_indices` | per-(venue, chain) | per-reserve | UAC `defi_reserve_params.py` per-protocol reserve list |
| `oracle_prices` | per-(venue, chain) | per-feed | UAC `_defi_oracle_coverage.py` |
| `dex_swaps` | per-pool | n/a | n/a (per-shard) |
| `dex_pools` | per-(venue, chain) | per-pool | TheGraph + UAC top-K-by-liquidity |
| `lst_rates` | per-(venue, chain) | per-LST | UAC `defi_venue_capabilities.py` LST list |
| `vault_share_price` | per-(venue, chain) | per-vault | UAC vault registry (Phase 1A) |
| `restaking_rewards` | per-(venue, chain) | per-AVS | UAC AVS registry (Phase 1A) |
| `governance_proposals` | per-protocol | per-proposal | n/a (per-event) |

## Per-protocol coverage (extends `defi-venue-protocol-catalogue.md`)

For each protocol in the catalogue, this matrix declares which data_types are captured. ✅ = captured today;
◐ = partial (per silent-zero / partial backfill); ✗ = zero capture.

### Lending

| Protocol | lending_indices | oracle_prices | rewards | risk_params | liquidation_events | flash_loan_events | position_data |
| -------- | --------------- | ------------- | ------- | ----------- | ------------------ | ----------------- | ------------- |
| Aave V3 Ethereum | ◐ silent-zero | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Aave V3 multi-chain (9) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Compound V3 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Spark | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Morpho | ◐ Ethereum | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Morpho Blue | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Fluid | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Radiant | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Kamino (Solana) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

### DEX (spot)

| Protocol | dex_swaps | dex_pools | position_data |
| -------- | --------- | --------- | ------------- |
| Uniswap V2 | ✅ | ✅ | n/a (V2 has no NFT positions) |
| Uniswap V3 | ✅ | ✅ | ✅ top-K |
| Uniswap V4 | ✗ | ✗ | ✗ |
| Curve | ✅ | ✅ | n/a |
| Balancer | ✗ | ✗ | n/a |
| Sushi V2 / V3 | ✗ | ✗ | ✗ |
| PancakeSwap V3 | ✗ | ✗ | ✗ |
| Camelot V3 | ✗ | ✗ | ✗ |
| Aerodromeq V3 | ✗ | ✗ | ✗ |
| Velodrome V2 | ✗ | ✗ | ✗ |
| TraderJoe V2 | ✗ | ✗ | ✗ |
| Raydium (Solana) | ✗ | ✗ | ✗ |
| Orca (Solana) | ✗ | ✗ | ✗ |

### DEX aggregator

| Protocol | aggregator_routes |
| -------- | ----------------- |
| Jupiter (Solana) | ✗ |
| 1inch | ✗ |
| 0x | ✗ |
| ParaSwap | ✗ |

### LST

| Protocol | lst_rates | oracle_prices | staking_yields |
| -------- | --------- | ------------- | -------------- |
| Lido | ✅ | ✅ | ✅ |
| Ether.fi | ✅ | ✅ | ✅ |
| Ethena | ◐ DefiLlama only | ✗ | ✗ |
| Jito (Solana) | ✅ Pyth-based, ~monthly | ✅ Pyth | ✗ |
| Marinade (Solana) | ✅ Pyth-based, ~monthly | ✅ Pyth | ✗ |
| Rocket Pool | ✗ | ✗ | ✗ |
| Solblaze | ✗ | ✗ | ✗ |

### Vault

| Protocol | vault_share_price | vault_apy | vault_tvl |
| -------- | ----------------- | --------- | --------- |
| Yearn | ✗ | ✗ | ✗ |
| Convex | ✗ | ✗ | ✗ |
| Beefy | ✗ | ✗ | ✗ |
| Pendle | ✗ | ✗ | ✗ |
| Idle | ✗ | ✗ | ✗ |

### Restaking + LRT

| Protocol | restaking_rewards | restaking_yields | slashing_events |
| -------- | ----------------- | ---------------- | --------------- |
| EigenLayer | ✗ (declared in UAC, no adapter) | ✗ | ✗ |
| Symbiotic | ✗ | ✗ | ✗ |
| Karak | ✗ | ✗ | ✗ |
| Renzo | ✗ | ✗ | ✗ |
| KelpDAO | ✗ | ✗ | ✗ |
| Puffer | ✗ | ✗ | ✗ |
| Jito restaking (Solana) | ✗ | ✗ | ✗ |

### Governance

| Protocol | governance_proposals |
| -------- | -------------------- |
| Aave | ✗ |
| Compound | ✗ |
| Spark | ✗ |
| Lido (Snapshot) | ✗ |
| Uniswap | ✗ |

## Cross-references

- [`defi-venue-protocol-catalogue.md`](defi-venue-protocol-catalogue.md) — protocol catalogue.
- [`defi-data-types-catalog.md`](defi-data-types-catalog.md) — original 14-data-type catalog (this doc extends it).
- [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) — manifest schema.
- [`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md) — empty/missing handling per
  data_type.
- [`amm-slippage-simulation.md`](../04-architecture/amm-slippage-simulation.md) — how `dex_pools` data feeds
  matching engine.
- Plan: [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md)
  Phase 3 owns the buildout for every ✗ above.

## Update protocol

When adding a new data_type:

1. Add to "Canonical data-type families" + "Per-protocol-family data-type matrix" with full schema.
2. Add to "Cluster validation matrix" if bundled.
3. Add UAC entry: `BUNDLED_DATA_TYPES` + `EMPTY_CONFIRMED_REASONS` if applicable.
4. Add cluster registry SSOT entry.
5. Add column to "Per-protocol coverage" section.
6. Update `availability-manifest-and-data-status.md`.
