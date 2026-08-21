---
doc_type: plan
title: defi-full-data-coverage
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15
overview: Build all missing DeFi data handlers in MTDS — lending indices, DEX pools, LST rates, perp funding, liquidations, bridge flows
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: B4}
repo_gates:
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: deployment-service, code: C0, deployment: none, business: none}
depends_on: [defi-data-pipeline-e2e]
todos:
- {id: phase1-lending-indices, content: '- [x] [AGENT] P0. Build collect-lending-indices handler — Aave V3 reserveParamsHistoryItems (liquidityIndex, variableBorrowIndex, stableBorrowRate, variableBorrowRate, utilizationRate) per reserve per day. Compound V3 daily market snapshots. All chains from SUBGRAPH_IDS. GCS: lending-indices-{project}/lending_indices/{protocol}/{chain}/date={date}/

    ', status: done}
- {id: phase1-dex-pools, content: '- [x] [AGENT] P0. Build collect-dex-pools handler — Uniswap V3 poolDayData (volumeUSD, tvlUSD, feesUSD, txCount), Balancer poolSnapshots (swapVolume, totalLiquidity, swapFees), Curve poolDayData (dailyVolumeUSD, tvl). All chains from SUBGRAPH_IDS. GCS: dex-pools-{project}/dex_pools/{protocol}/{chain}/date={date}/

    ', status: done}
- {id: phase1-lst-rates, content: '- [x] [AGENT] P0. Build collect-lst-rates handler — On-chain oracle exchange rates via Alchemy RPC at historical block numbers. stETH (getPooledEthByShares), wstETH (stEthPerToken), rETH (getExchangeRate), cbETH (exchangeRate), sUSDe (convertToAssets), sDAI (convertToAssets). Daily rate snapshots for exact P&L attribution (APY = annualised growth in rate). GCS: lst-rates-{project}/lst_rates/date={date}/

    ', status: done}
- {id: phase1-perp-funding, content: '- [x] [AGENT] P1. Build collect-perp-funding handler — Hyperliquid S3 archive fundingRates (already have adapter), GMX subgraph fundingRateUpdated events. Daily funding rate, OI, volume per market. GCS: perp-funding-{project}/perp_funding/{protocol}/date={date}/

    ', status: done}
- {id: phase1-liquidations, content: '- [x] [AGENT] P1. Build collect-liquidations handler — Aave V3 LiquidationCall events from subgraph, Compound V3 AbsorbCollateral events. Per-chain per-day. GCS: liquidations-{project}/liquidations/{protocol}/{chain}/date={date}/

    ', status: done}
- {id: phase1-rewrite-evm-defi, content: '- [x] [AGENT] P0. Rewrite collect-evm-defi to fetch historical lending rate indices per day in batch mode (Aave liquidityIndex/variableBorrowIndex from subgraph time-travel queries with block number) instead of live APY snapshots. Keep live snapshot path for --mode live.

    ', status: done}
- {id: phase2-cli-args, content: '- [x] [AGENT] P0. Register all new operations in ServiceBootstrap. Add CLI args: --lending-protocols, --dex-protocols, --lst-tokens, --perp-protocols, --liquidation-protocols. All reading from SUBGRAPH_IDS in UAC.

    ', status: done}
- {id: phase2-uac-schemas, content: '- [x] [AGENT] P0. Add parquet schemas to UAC internal domain types: LendingIndexRecord, DexPoolDayRecord, LstRateRecord, PerpFundingRecord, LiquidationRecord. All in unified_api_contracts.internal.domain.defi.

    ', status: done}
- {id: phase2-manifest-buckets, content: '- [x] [AGENT] P1. Register new GCS buckets in deployment-service manifest_reader _EXTRA_BUCKETS and UTL get_bucket_name for: lending-indices, dex-pools, lst-rates, perp-funding, liquidations.

    ', status: done}
- {id: phase3-vm-scripts, content: '- [x] [AGENT] P1. Create VM launch scripts for each new handler in e2e-testing/scripts/defi/ — all using proper service CLI invocation (no MagicMock).

    ', status: done}
- {id: phase4-validate, content: "- [x] [HUMAN+AGENT] P0. Run each handler locally for 1 day, verify GCS output, check data manifest shows coverage.\n  *(archived 2026-04-22 — operational burn-in; run per handler when scheduling production backfills.)*\n", status: todo}
isProject: false
---

# DeFi Full Data Coverage

## Problem

MTDS currently only covers gas fees, EigenLayer rewards, live lending rate snapshots, and Solana DeFi snapshots.
Missing: historical lending indices (the actual on-chain liquidityIndex/variableBorrowIndex that compound over time),
DEX pool metrics (volume/TVL/fees), LST exchange rates, on-chain perp funding rates, and liquidation events.

The existing `collect-evm-defi` handler only fetches live APY snapshots — useless for batch mode historical analysis. We
need the actual index values from subgraph historical queries.

## Data Source Matrix

| Handler                 | Protocol        | Chains                              | Data Source                           | Fields                                                                                                                                  |
| ----------------------- | --------------- | ----------------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| collect-lending-indices | Aave V3         | ETH,ARB,OP,POLY,AVAX,BASE,LINEA,BSC | The Graph (reserveParamsHistoryItems) | liquidityIndex, variableBorrowIndex, stableBorrowRate, variableBorrowRate, utilizationRate, totalATokenSupply, totalCurrentVariableDebt |
| collect-lending-indices | Compound V3     | ETH,ARB,BASE,OP                     | The Graph (marketDailySnapshots)      | supplyRate, borrowRate, totalSupply, totalBorrow, utilization                                                                           |
| collect-dex-pools       | Uniswap V3      | ETH,ARB,BASE,OP,POLY                | The Graph (poolDayDatas)              | volumeUSD, tvlUSD, feesUSD, txCount, token0Price, token1Price                                                                           |
| collect-dex-pools       | Balancer        | ETH,ARB,POLY,OP,AVAX,BASE           | The Graph (poolSnapshots)             | swapVolume, totalLiquidity, swapFees                                                                                                    |
| collect-dex-pools       | Curve           | ETH,OP,AVAX                         | The Graph (poolDayData)               | dailyVolumeUSD, tvl, fee                                                                                                                |
| collect-lst-rates       | Lido stETH      | ETH                                 | DefiLlama yields + on-chain           | stETH/ETH rate, APY                                                                                                                     |
| collect-lst-rates       | RocketPool rETH | ETH                                 | DefiLlama yields                      | rETH/ETH rate, APY                                                                                                                      |
| collect-lst-rates       | Coinbase cbETH  | ETH                                 | DefiLlama yields                      | cbETH/ETH rate, APY                                                                                                                     |
| collect-lst-rates       | Ethena sUSDe    | ETH                                 | DefiLlama yields                      | sUSDe yield, APY                                                                                                                        |
| collect-lst-rates       | MakerDAO sDAI   | ETH                                 | DefiLlama yields                      | DSR rate, APY                                                                                                                           |
| collect-perp-funding    | Hyperliquid     | N/A (L1)                            | S3 archive                            | fundingRate, openInterest, volume per market                                                                                            |
| collect-perp-funding    | GMX             | ARB,AVAX                            | The Graph                             | fundingRate, borrowRate, OI per market                                                                                                  |
| collect-liquidations    | Aave V3         | all 10 chains                       | The Graph (liquidationCalls)          | collateralAsset, debtAsset, debtToCover, liquidatedCollateralAmount, liquidator                                                         |
| collect-liquidations    | Compound V3     | ETH,ARB,BASE                        | The Graph (absorbCollateral)          | asset, amount, borrower                                                                                                                 |

## GCS Bucket Layout

```
lending-indices-{project}/
  lending_indices/{protocol}/{chain}/date={YYYY-MM-DD}/{protocol}_{chain}_{timestamp}.parquet

dex-pools-{project}/
  dex_pools/{protocol}/{chain}/date={YYYY-MM-DD}/{protocol}_{chain}_{timestamp}.parquet

lst-rates-{project}/
  lst_rates/date={YYYY-MM-DD}/lst_rates_{timestamp}.parquet

perp-funding-{project}/
  perp_funding/{protocol}/date={YYYY-MM-DD}/{protocol}_{timestamp}.parquet

liquidations-{project}/
  liquidations/{protocol}/{chain}/date={YYYY-MM-DD}/{protocol}_{chain}_{timestamp}.parquet
```

## Execution DAG

```
Phase 1: BUILD HANDLERS (PARALLEL — all independent)
  ├── collect-lending-indices handler
  ├── collect-dex-pools handler
  ├── collect-lst-rates handler
  ├── collect-perp-funding handler
  ├── collect-liquidations handler
  └── rewrite collect-evm-defi for historical mode
         │
    ── QG gate: MTDS passes ──
         │
Phase 2: WIRING (PARALLEL)
  ├── Register operations + CLI args in ServiceBootstrap
  ├── UAC internal schemas for parquet records
  └── Deployment-service manifest reader + UTL bucket names
         │
    ── QG gate: MTDS + UAC + deployment-service pass ──
         │
Phase 3: VM SCRIPTS
  └── Create launch scripts for each handler
         │
Phase 4: VALIDATION
  └── Run each handler for 1 day, verify GCS output
```
