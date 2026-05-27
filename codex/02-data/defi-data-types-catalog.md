---
scope: [engineer]
status: canonical
last_reviewed: 2026-05-13
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

| instrument_type | Data types                                                                                                                  |
| --------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `spot_asset`    | dex_swaps, dex_pool_state, bridge_events, mev_events, token_transfers, governance_events, staking_yields, vault_share_price |
| `lending`       | lending_indices, liquidations, liquidation_events, flash_loan_events, position_data, risk_params                            |
| `staking`       | staking_yields, lst_rates, rewards, eigenlayer_rewards, native_staking_rates                                                |
| `perpetual`     | perp_funding                                                                                                                |

---

## Data Type Catalog

### 1. dex_swaps (canonical; was `swap_events`)

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

### 2. dex_pool_state (canonical; was `pool_state`)

| Field               | Value                                                                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **CLI operation**   | (legacy evm_defi_handler / dex_pools_handler)                                                                                                          |
| **Sources**         | The Graph: uniswap_v3, pancakeswap_v3, sushiswap_v3, aerodrome_v3, camelot_v3, balancer, curve, sushiswap, gmx                                         |
| **Shard key**       | venue × chain × date                                                                                                                                   |
| **Instrument type** | `spot_asset`                                                                                                                                           |
| **Status**          | Production                                                                                                                                             |
| **Actual columns**  | protocol, chain, pool_id, token_a, token_b, fee_rate_bps, date, volume_usd, tvl_usd, fees_usd, tx_count, price_a, price_b, liquidity, sqrt_price, tick |

Hourly/daily pool snapshots. ⚠ **D14 code-bug (2026-05-27)**: `dex_pools_handler.py` records the manifest under
`_DEX_POOLS_DATA_TYPE = "dex_pools"` (L62) but writes the parquet with `data_type="dex_pool_state"` (L569) — the hive
partition key is `dex_pool_state`; the manifest/data data_type names diverge. Deferred-until-pipeline-done.

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

| Field               | Value                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-perp-funding` (perp_funding_handler)                                                                             |
| **Sources**         | Hyperliquid REST, Aster REST, GMX (The Graph), Pacifica REST, Lighter (Tardis CSV), Drift (Data API + S3). NOT Synthetix. |
| **Shard key**       | venue × chain × date                                                                                                      |
| **Instrument type** | `perpetual`                                                                                                               |
| **Status**          | Production                                                                                                                |
| **Schema fields**   | symbol, ts_event, venue, chain, funding_rate, annualized_rate                                                             |

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
| `restaking_rewards` / `cross_chain_restaking_routes` / `restaking_operator_set` | —                              | —                               | SOLAYER/PICASSO/CAMBRIAN PROTOCOL_CAPABILITIES                                           | declared in UAC but **no MTDS collection + venues absent from `ALL_DEFI_VENUES`** (see findings D-new)                                                                                                    | Declared, not collected         |

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

---

## Related Documents

- `codex/02-data/mtds-data-source-coverage-matrix.md` — full MTDS source coverage
- `codex/02-data/instrument-pipeline-defi.md` — DeFi instrument discovery pipeline
- `codex/02-data/per-asset-group-bucket-layouts.md` — GCS bucket layout
- `deployment-service/configs/venue_data_types.yaml` — expected data type declarations per venue
- Plan: `plans/archive/defi_data_types_completeness_2026_04_24.plan.md`
