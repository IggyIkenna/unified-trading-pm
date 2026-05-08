---
scope: [engineer]
---

# DeFi Data Types Catalog

> SSOT for all MTDS DeFi data type definitions, sources, shard keys, and implementation status. Last updated: 2026-04-24
> (defi_data_types_completeness_2026_04_24)

## Overview

MTDS collects DeFi market data in 14 distinct data types across lending, DEX, staking, bridging, governance, and MEV
domains. Each data type maps to one or more MTDS CLI operations (`--operation collect-<type>`), one or more venues, and
a canonical GCS path under the DeFi tick-data bucket.

### GCS Path Convention

```
gs://{tick-defi-bucket}/raw_tick_data/by_date/day={date}/category=defi/
  venue={VENUE}-{CHAIN}/instrument_type={type}/data_type={data_type}/ticks.parquet
```

### Instrument Type Mapping

| instrument_type | Data types                                                                                                            |
| --------------- | --------------------------------------------------------------------------------------------------------------------- |
| `spot_asset`    | swap_events, pool_state, bridge_events, mev_events, token_transfers, governance_events, staking_yields (Lido/EtherFi) |
| `lending`       | lending_metrics, liquidation_events, flash_loan_events, position_data                                                 |
| `staking`       | staking_yields                                                                                                        |
| `perpetual`     | funding_rates                                                                                                         |

---

## Data Type Catalog

### 1. swap_events

| Field               | Value                                                                             |
| ------------------- | --------------------------------------------------------------------------------- |
| **CLI operation**   | (legacy evm_defi_handler / dex_swaps_handler)                                     |
| **Sources**         | The Graph: Uniswap V2/V3/V4, Curve, Balancer, SushiSwap subgraphs                 |
| **Shard key**       | venue × chain × date                                                              |
| **Instrument type** | `spot_asset`                                                                      |
| **Status**          | Production                                                                        |
| **Schema fields**   | symbol, ts_event, venue, chain, token_in, token_out, amount_in, amount_out, price |

Captures AMM swap transactions. One row per swap event.

---

### 2. pool_state

| Field               | Value                                                                       |
| ------------------- | --------------------------------------------------------------------------- |
| **CLI operation**   | (legacy evm_defi_handler / dex_pools_handler)                               |
| **Sources**         | The Graph: Uniswap V2/V3/V4, Curve poolHourDatas / pairHourDatas            |
| **Shard key**       | venue × chain × date                                                        |
| **Instrument type** | `spot_asset`                                                                |
| **Status**          | Production                                                                  |
| **Schema fields**   | symbol, ts_event, venue, chain, pool_address, tvl_usd, volume_24h, fee_tier |

Hourly pool TVL and volume snapshots. One row per pool per hour.

---

### 3. lending_metrics

| Field               | Value                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-lending-indices` (lending_indices_handler)                                                  |
| **Sources**         | The Graph: Aave V3, Morpho; Morpho REST API                                                          |
| **Shard key**       | venue × chain × date                                                                                 |
| **Instrument type** | `lending`                                                                                            |
| **Status**          | Production                                                                                           |
| **Schema fields**   | symbol, ts_event, venue, chain, supply_apy, borrow_apy, utilization_rate, total_supply, total_borrow |

Daily lending rate indices. One row per market (token) per day.

---

### 4. funding_rates

| Field               | Value                                                         |
| ------------------- | ------------------------------------------------------------- |
| **CLI operation**   | `collect-perp-funding` (perp_funding_handler)                 |
| **Sources**         | Hyperliquid, GMX, Synthetix on-chain funding rate methods     |
| **Shard key**       | venue × chain × date                                          |
| **Instrument type** | `perpetual`                                                   |
| **Status**          | Production                                                    |
| **Schema fields**   | symbol, ts_event, venue, chain, funding_rate, annualized_rate |

Perpetual funding rates. One row per market per funding interval.

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
| **Protocols**       | AAVEV3 (ETHEREUM, ARBITRUM, POLYGON), MORPHO (ETHEREUM)                                                        |

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
| **Protocols**       | AAVEV3 (all supported chains via `get_supported_chains_for_protocol`)       |

Aave V3 FlashLoan events. Captures flash loans including amount, premium (fee), initiator, and receiver address.

---

### 7. staking_yields

| Field               | Value                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-staking-yields` (staking_yields_handler)                                                                         |
| **Sources**         | Lido REST API (`api.lido.fi/v1/protocol/steth/apr/sma`), EtherFi REST API, DefiLlama (`api.llama.fi/protocol/eigenlayer`) |
| **Shard key**       | venue × chain × date                                                                                                      |
| **Instrument type** | `spot_asset` (written as `SPOT_ASSET`)                                                                                    |
| **Status**          | Production (2026-04-24)                                                                                                   |
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
| **Protocols**       | AAVEV3 (all supported chains), UNISWAPV3-ETHEREUM                                                     |

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

| Field               | Value                                                                |
| ------------------- | -------------------------------------------------------------------- |
| **CLI operation**   | `collect-oracle-prices` (oracle_prices_handler)                      |
| **Sources**         | Aave V3 price oracle (Chainlink), Lido/EtherFi/Ethena exchange rates |
| **Shard key**       | venue × chain × date                                                 |
| **Instrument type** | `spot_asset`                                                         |
| **Status**          | Production                                                           |
| **Schema fields**   | symbol, ts_event, venue, chain, price_usd                            |

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

## Protocol Coverage Matrix

| Protocol         | Chain(s)                           | Data Types                                                            |
| ---------------- | ---------------------------------- | --------------------------------------------------------------------- |
| UNISWAPV2        | ETHEREUM                           | swap_events, pool_state                                               |
| UNISWAPV3        | ETHEREUM, ARBITRUM, BASE, OPTIMISM | swap_events, pool_state, position_data                                |
| UNISWAPV4        | ETHEREUM                           | swap_events, pool_state                                               |
| AAVEV3           | ETHEREUM, ARBITRUM, POLYGON        | lending_metrics, liquidation_events, flash_loan_events, position_data |
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

---

## Related Documents

- `codex/02-data/mtds-data-source-coverage-matrix.md` — full MTDS source coverage
- `codex/02-data/instrument-pipeline-defi.md` — DeFi instrument discovery pipeline
- `codex/02-data/per-category-bucket-layouts.md` — GCS bucket layout
- `deployment-service/configs/venue_data_types.yaml` — expected data type declarations per venue
- Plan: `plans/archive/defi_data_types_completeness_2026_04_24.plan.md`
