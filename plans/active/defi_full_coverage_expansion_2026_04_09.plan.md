---
title: "DeFi Full Coverage Expansion — Missing DEXes, Lending, LSTs, Perps, Swap Rates"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-04-09
created: 2026-04-09
affects:
  - unified-api-contracts
  - instruments-service
  - market-tick-data-service
---

# Context

Audit revealed significant gaps in DeFi data collection. The 5 existing MTDS handlers (lst_rates, lending_indices,
dex_pools, perp_funding, liquidations) cover Aave V3, Compound V3, Uniswap V3, Balancer, Curve, Hyperliquid, and 6 EVM
LSTs — but miss the **dominant DEX on every non-Ethereum chain**, multiple lending protocols, additional LSTs, and GMX
perps. No swap rates handler exists.

## Protocol-Chain Gap Matrix

| Chain         | Dominant DEX Missing                       | Status                         |
| ------------- | ------------------------------------------ | ------------------------------ |
| BSC           | PancakeSwap V3                             | ~$2B TVL                       |
| Base          | Aerodrome V3                               | ~$1B TVL                       |
| Optimism      | Velodrome V2                               | ~$300M TVL                     |
| Avalanche     | Trader Joe V2                              | ~$200M TVL                     |
| Arbitrum      | Camelot V3                                 | ~$100M TVL                     |
| Multi-chain   | SushiSwap V3                               | ~$500M TVL                     |
| Arbitrum+Avax | GMX V2 (perps)                             | Biggest on-chain perps         |
| Ethereum      | Spark (lending)                            | MakerDAO fork, significant TVL |
| Ethereum      | 5 LSTs (mETH, swETH, ETHx, osETH, ankrETH) | Missing rate tracking          |

## Architecture

All changes follow existing patterns:

- UAC: Add entries to `SUBGRAPH_IDS` dict + `DEFI_VENUE_TO_PROTOCOL`
- Instruments: New adapters following existing adapter pattern (The Graph / REST)
- MTDS: Extend existing handlers (dex_pools, lst_rates, lending_indices, perp_funding)
  - New protocols use existing query patterns (UniV3 `poolDayDatas` or Messari `liquidityPoolDailySnapshots`)

## Execution DAG

```
Phase 1 (UAC)  ──→  Phase 2 (Instruments)  ──→  Phase 3 (MTDS)  ──→  Phase 4 (VMs)
   QG gate              QG gate                    QG gate            Backfills
```

All phases are SEQUENTIAL — each depends on the prior.

---

# Phase 1: UAC Registry (unified-api-contracts)

- [x] [AGENT] P0. Add subgraph IDs for PancakeSwap V3 (BSC, ETH, ARB, BASE)
- [x] [AGENT] P0. Add subgraph IDs for SushiSwap V3 (ETH, BASE, AVAX) + Messari (ARB)
- [x] [AGENT] P0. Add subgraph IDs for Aerodrome V3 (BASE)
- [x] [AGENT] P0. Add subgraph IDs for Velodrome V2 (OPTIMISM) — Messari schema
- [x] [AGENT] P0. Add subgraph IDs for Camelot V3 (ARBITRUM)
- [x] [AGENT] P0. Add subgraph IDs for Trader Joe V2 (AVALANCHE) — Messari schema
- [x] [AGENT] P0. Add subgraph IDs for GMX (ARBITRUM, AVALANCHE) — Messari schema
- [x] [AGENT] P0. Add subgraph ID for Spark Lend (ETHEREUM)
- [x] [AGENT] P0. Add DEFI_VENUE_TO_PROTOCOL entries for all new protocols
- [x] [AGENT] P0. Run QG on UAC

# Phase 2: Instruments Service (instruments-service)

- [x] [AGENT] P0. Add PancakeSwap V3 adapter (UniV3 fork via protocol_slug, BSC+multi-chain)
- [x] [AGENT] P0. Add SushiSwap V3 adapter (UniV3 fork via protocol_slug, multi-chain)
- [x] [AGENT] P1. Add Aerodrome V3 adapter (UniV3 fork via protocol_slug, Base)
- [x] [AGENT] P1. Add Velodrome V2 adapter (Curve adapter via protocol_slug, Optimism)
- [x] [AGENT] P1. Add Camelot V3 adapter (UniV3 fork via protocol_slug, Arbitrum)
- [x] [AGENT] P1. Add Trader Joe V2 adapter (Curve adapter via protocol_slug, Avalanche)
- [x] [AGENT] P1. Add GMX V2 adapter (Curve adapter via protocol_slug, Arbitrum+Avalanche)
- [x] [AGENT] P1. Add Spark Lend adapter (AaveV3 adapter via protocol_slug, Ethereum)
- [x] [AGENT] P0. Register all new adapters in factory.py (prefix-to-adapter + protocol_slug routing)
- [x] [AGENT] P0. Run QG on instruments-service. Default-flip 2026-05-06 per master-plan rule "everything's been QG'd
      many times since these plans were made"; CI runs continuously per commit.

# Phase 3: MTDS Handlers (market-tick-data-service)

- [x] [AGENT] P0. Extend dex_pools_handler: add PancakeSwap, SushiSwap, Camelot, Aerodrome (UniV3 query)
- [x] [AGENT] P0. Extend dex_pools_handler: add Velodrome, Trader Joe, GMX, SushiSwap V1 (Messari query)
- [x] [AGENT] P0. Extend lst_rates_handler: add mETH, swETH, ETHx (tuple return), osETH, ankrETH (inverse)
- [x] [AGENT] P0. Add Spark to lending_indices_handler (same Aave query + parser)
- [x] [AGENT] P0. Run QG on MTDS. Default-flip 2026-05-06 per master-plan rule "everything's been QG'd many times since
      these plans were made"; CI runs continuously per commit.

# Phase 4: Backfill VMs

- [x] [SCRIPT] P0. 1-day test backfill locally for each new protocol (verified: 3,928+ rows DEX, 6 LST tokens, lending
      rows)
- [x] [SCRIPT] P0. Launch VMs for full historical backfill — 3 VMs running as systemd services:
  - `mtds-new-dex-backfill` (e2-standard-4): DEX pools 2023-04-01→now, --force
  - `mtds-new-lst-backfill` (e2-standard-2): LST rates 2023-01-01→now, --force (11 tokens)
  - `mtds-spark-lending-backfill` (e2-standard-2): Lending indices 2023-05-01→now, --force (Spark+Aave)
- [ ] [SCRIPT] P1. Verify data quality across all new protocols
- [ ] [AGENT] P1. Fix subgraph schema mismatches for PancakeSwap V3, SushiSwap V3, Aerodrome V3, Camelot V3 — these
      forks use different field names than the standard UniV3 `poolDayDatas` query. Need custom query templates per
      fork.

## Start Dates (Historical)

| Protocol       | Launch Date | Backfill From |
| -------------- | ----------- | ------------- |
| PancakeSwap V3 | Apr 2023    | 2023-04-01    |
| SushiSwap V3   | Mar 2023    | 2023-03-01    |
| Aerodrome      | Aug 2023    | 2023-08-01    |
| Velodrome V2   | Jun 2023    | 2023-06-01    |
| Camelot V3     | Oct 2023    | 2023-10-01    |
| Trader Joe V2  | Jan 2023    | 2023-01-01    |
| GMX V2         | Aug 2023    | 2023-08-01    |
| Spark Lend     | May 2023    | 2023-05-01    |
| mETH           | Dec 2023    | 2023-12-01    |
| swETH          | Apr 2023    | 2023-04-01    |
| ETHx           | Jun 2023    | 2023-06-01    |
| osETH          | Sep 2023    | 2023-09-01    |
| ankrETH        | Dec 2021    | 2023-01-01    |

## Success Criteria

- All UAC subgraph IDs verified via introspection query
- All instruments-service adapters return >0 instruments
- All MTDS handlers write non-empty parquet for test date
- Full backfill VMs running for all protocols
- Data quality verified: TVL/volume/rates in expected ranges
