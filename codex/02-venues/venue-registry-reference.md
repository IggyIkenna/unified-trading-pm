---
doc_type: codex-ssot
title: Venue Registry — Reference
summary:
  "Human-readable mirror of the UAC venue capability registry: the catalog of every venue the system trades on or pulls
  data from, classified SINGLE_VENUE / META_BROKER / DATA_AGGREGATOR — 5 CeFi execution + 2 pricing-only, 3 TradFi
  (IBKR/CME/ICE), 7 DeFi chains + DEXes/lending/staking/perps, Unity + sports exchanges + aggregators, prediction
  markets; lists permanently-removed venues (LSE/TSX/Elysium/Arkham/Bloxroute/Infura; Pyth Solana-only)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [venue, registry, cefi, defi, tradfi, sports, prediction]
related:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/02-venues/unity-integration.md,
    /codex/03-services/venue-capability-registry.md,
    /codex/02-data/venue-availability.md,
  ]
created: 2026-04-17
authoritative_for: [venue registry human-readable reference, permanently-removed venues list]
referenced_by:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/02-venues/unity-integration.md,
    /codex/03-services/venue-capability-registry.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Venue Registry — Reference

> **What it is:** The canonical catalog of every venue the Unified Trading System trades on or pulls data from. Each
> entry includes venue_type (SINGLE_VENUE / META_BROKER / DATA_AGGREGATOR), supported operations, supported instruments,
> collateral / margin specs, and commercial notes. SSOT is the UAC venue capability registry; this doc is the
> human-readable mirror.

## Venue types (3)

| Type              | Definition                                                | Examples                                           |
| ----------------- | --------------------------------------------------------- | -------------------------------------------------- |
| `SINGLE_VENUE`    | One endpoint, one account type                            | Binance, OKX, Deribit, Aave V3 on one chain        |
| `META_BROKER`     | One endpoint, one wallet, internal routing to child books | Unity (10 child books), IBKR (internal aggregator) |
| `DATA_AGGREGATOR` | Data only, no execution                                   | SharpAPI, odds-api.io, SFI, Databento              |

## Supported operation enum

`TRADE`, `SWAP`, `LEND`, `BORROW`, `STAKE`, `UNSTAKE`, `QUOTE`, `TRANSFER`, `BRIDGE`, `ATOMIC`, `CANCEL`, plus data
operations `TICKS`, `OHLC`, `ORDERBOOK`, `TRADES`, `FUNDING`, `LIQUIDATIONS`, `REFERENCE_DATA`.

## CeFi — Execution venues (5)

| Venue       | Type         | Operations                                                           | Instruments                                               | Notes                                                                     |
| ----------- | ------------ | -------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------- |
| Binance     | SINGLE_VENUE | TRADE, QUOTE, TRANSFER internal sub, TICKS, OHLC, ORDERBOOK, FUNDING | Spot, Perp (USDT, USDC, coin-margined), Options (BTC/ETH) | Cross-margin; VIP tiers (VIP_0 → VIP_9); ~5% cross-margin on hedged basis |
| OKX         | SINGLE_VENUE | TRADE, QUOTE, TICKS, OHLC, ORDERBOOK, FUNDING                        | Spot, Perp, Options                                       | Cross-margin; portfolio margin available                                  |
| Bybit       | SINGLE_VENUE | TRADE, QUOTE, TICKS, OHLC, ORDERBOOK, FUNDING                        | Spot, Perp, Options                                       | Cross-margin                                                              |
| Hyperliquid | SINGLE_VENUE | TRADE, QUOTE, TICKS, OHLC, ORDERBOOK, FUNDING                        | Perp only                                                 | On-chain perp DEX; USDC-margined                                          |
| Deribit     | SINGLE_VENUE | TRADE, QUOTE, TICKS, OHLC, ORDERBOOK, FUNDING                        | BTC/ETH Options + Futures                                 | Portfolio margin; greek netting                                           |

## CeFi — Pricing-only (2)

| Venue    | Type            | Operations             | Instruments      | Notes                                         |
| -------- | --------------- | ---------------------- | ---------------- | --------------------------------------------- |
| Coinbase | DATA_AGGREGATOR | TICKS, OHLC, ORDERBOOK | Spot crypto      | Reference pricing; no execution in this stack |
| CBOE     | DATA_AGGREGATOR | REFERENCE_DATA         | Options, futures | Reference pricing for TradFi                  |

## TradFi — Execution venues (3)

| Venue | Type                                    | Operations                | Instruments                       | Notes                                                                        |
| ----- | --------------------------------------- | ------------------------- | --------------------------------- | ---------------------------------------------------------------------------- |
| IBKR  | META_BROKER                             | TRADE, QUOTE, TICKS, OHLC | Equity, ETF, Options, Futures, FX | Routes internally to underlying exchanges; venue = IBKR always for our stack |
| CME   | SINGLE_VENUE (via IBKR)                 | TRADE                     | Futures (ES, NQ, CL, GC, NG, ...) | Access via IBKR; ES-only SSOT for CME codes                                  |
| ICE   | SINGLE_VENUE (via IBKR or counterparty) | TRADE                     | Futures, swaps                    | Counterparty-dependent                                                       |

**Note:** LSE and TSX removed permanently. UK/Canadian equities route via IBKR to underlying markets; we don't have
LSE/TSX-specific adapters.

## DeFi — Chains (7)

| Chain     | Primary role            | DEX support                       | Lending                             | Staking           |
| --------- | ----------------------- | --------------------------------- | ----------------------------------- | ----------------- |
| Ethereum  | Primary, most liquidity | Uniswap V2/V3/V4, Curve, Balancer | Aave V3, Compound V3, Morpho, Spark | Lido, Rocket Pool |
| Arbitrum  | L2 primary              | Uniswap V3, Balancer              | Aave V3                             | — (bridged LSTs)  |
| Optimism  | L2                      | Uniswap V3, Velodrome             | Aave V3                             | —                 |
| Base      | L2 Coinbase             | Uniswap V3, Aerodrome             | Aave V3, Morpho                     | —                 |
| Polygon   | Legacy L2               | Uniswap V3, Curve, Balancer       | Aave V3                             | —                 |
| Avalanche | Alt-L1                  | Joe V2, Uniswap V3                | Aave V3                             | —                 |
| Solana    | Alt-L1                  | Orca CLMM, Raydium                | Kamino, MarginFi                    | Jito, Marinade    |

## DeFi — DEXes (5)

| DEX          | Chains              | Pool model                | Notes                                |
| ------------ | ------------------- | ------------------------- | ------------------------------------ |
| Uniswap V2   | Ethereum, many L2   | Full-range LP             | Passive LP, IL per standard xy=k     |
| Uniswap V3   | All EVM             | Concentrated LP           | Active LP, IL amplified within range |
| Uniswap V4   | Ethereum (new)      | Hooks + concentrated      | Active LP with custom hooks          |
| Curve        | Ethereum, EVM L2    | Stableswap + crypto pools | Low-IL for correlated pairs          |
| Balancer     | Ethereum, EVM L2    | Weighted + stable pools   | Custom weight allocations            |
| Aerodrome    | Base                | ve(3,3) style             | Active/passive; incentives           |
| Joe V2 (LFJ) | Avalanche, Arbitrum | Liquidity book            | Bin-based active LP                  |
| Orca (CLMM)  | Solana              | Concentrated              | Solana-native; see also Raydium      |
| Raydium      | Solana              | AMM + CL                  | —                                    |

## DeFi — Lending (5)

| Protocol    | Chains                | Collateral assets                     | LTV examples                   |
| ----------- | --------------------- | ------------------------------------- | ------------------------------ |
| Aave V3     | Ethereum + all EVM L2 | ETH, stETH, wstETH, WBTC, stablecoins | stETH 75%, ETH 82.5%, USDC 77% |
| Compound V3 | Ethereum + EVM L2     | USDC, WBTC, ETH                       | Market-specific                |
| Morpho      | Ethereum              | Variable per market                   | Market-created                 |
| Spark       | Ethereum              | ETH, stETH, wstETH                    | Based on MakerDAO; ETH 83%     |
| Kamino      | Solana                | SOL, USDC, LSTs                       | Solana market                  |

## DeFi — Staking (4)

| Protocol    | Chain    | Asset | LST           | Notes                    |
| ----------- | -------- | ----- | ------------- | ------------------------ |
| Lido        | Ethereum | ETH   | stETH, wstETH | Most liquid LST          |
| Rocket Pool | Ethereum | ETH   | rETH          | Decentralized validators |
| Jito        | Solana   | SOL   | jitoSOL       | MEV-boosted Solana stake |
| Marinade    | Solana   | SOL   | mSOL          | Solana-native            |

## DeFi — Perp protocols (2)

| Protocol    | Chain        | Notes                                     |
| ----------- | ------------ | ----------------------------------------- |
| Hyperliquid | Own chain    | Listed in CeFi execution (hybrid CEX/DEX) |
| dYdX V4     | Cosmos-based | Perp DEX                                  |

(Hyperliquid double-listed because it's classified CEFI for execution flows but is on-chain.)

## Sports — Prime broker (1)

| Venue | Type        | Operations                              | Child books    | Notes                                                                                                                                                                                                                                            |
| ----- | ----------- | --------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Unity | META_BROKER | TRADE (BET_BACK, BET_LAY), QUOTE, TICKS | 10 child books | Single TCP connection; Java Feed Connector sidecar; USD share class; all 3 sports enabled (Soccer + Tennis + Basketball); $10.8k deposit (refundable at $5.3M volume); $2.6k/mo subscription (waived at $260k turnover); 1x rollover on deposits |

Child books (8 confirmed + 2 TBD):

| Child book         | Commission    | Notes                                                 |
| ------------------ | ------------- | ----------------------------------------------------- |
| PINNACLE_VIA_UNITY | 0.4%          | Sharp book                                            |
| VX                 | 0.2%          | Lowest commission                                     |
| SHARPBET           | 0.2%          | Lowest commission                                     |
| BETFAIR_VIA_UNITY  | 0.5% exchange | Via Unity aggregated book                             |
| BROKER3            | TBD           | Per commercial agreement                              |
| BROKER4            | TBD           | Per commercial agreement                              |
| BROKER5            | 3.0%          | Expensive; avoid unless spread justifies              |
| IBCBET             | 1.5%          | Mid commission                                        |
| (book 9)           | TBD           | Pending from quant-portal.olesportsresearch.com/unity |
| (book 10)          | TBD           | Pending                                               |

## Sports — Direct exchanges (3)

| Venue     | Type         | Operations                              | Notes                               |
| --------- | ------------ | --------------------------------------- | ----------------------------------- |
| Betfair   | SINGLE_VENUE | TRADE (BET_BACK, BET_LAY), QUOTE, TICKS | Exchange with back+lay; GBP primary |
| Smarkets  | SINGLE_VENUE | TRADE, QUOTE, TICKS                     | Exchange                            |
| Matchbook | SINGLE_VENUE | TRADE, QUOTE, TICKS                     | Exchange                            |

## Sports — Data aggregators

| Venue              | Type            | Operations                      | Notes                                                                     |
| ------------------ | --------------- | ------------------------------- | ------------------------------------------------------------------------- |
| SharpAPI           | DATA_AGGREGATOR | TICKS, ORDERBOOK                | Multi-book odds feed                                                      |
| odds-api.io        | DATA_AGGREGATOR | TICKS                           | Public odds feed                                                          |
| SFI (via RapidAPI) | DATA_AGGREGATOR | REFERENCE_DATA, FIXTURES, STATS | Championships + standings work; `/matches/date/` deprecated (returns 404) |
| FootyStats         | DATA_AGGREGATOR | REFERENCE_DATA                  | Fixture metadata, xG                                                      |
| API Football       | DATA_AGGREGATOR | FIXTURES, STATS, LIVE           | 65 Tier 0+1 leagues for live stats                                        |

## Prediction markets

| Venue      | Type         | Operations                            | Status                                                                                                                                                                                                                               |
| ---------- | ------------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Polymarket | SINGLE_VENUE | TRADE (BET_CLOB_YES/NO), QUOTE, TICKS | Active. CLOB migration done (49K→863K markets). USDC on Polygon.                                                                                                                                                                     |
| Kalshi     | SINGLE_VENUE | TRADE, QUOTE                          | API migrated to `api.elections.kalshi.com` (2026-05-20, Phase 1 shipped). Status: `BLOCKED-CREDENTIALS` — integration verification pending credential provisioning (see `/codex/02-data/prediction-schema-paths.md` § Kalshi delta). |

## Permanently removed

Do NOT re-introduce:

| Venue     | Why removed                                                                                                                                                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LSE       | UK equities route via IBKR                                                                                                                                                                                                               |
| TSX       | Canadian equities route via IBKR                                                                                                                                                                                                         |
| Elysium   | Removed per earlier architecture decisions                                                                                                                                                                                               |
| Arkham    | Removed; not a data source we use                                                                                                                                                                                                        |
| Bloxroute | Removed from MEV provider list                                                                                                                                                                                                           |
| Pyth      | **UNBANNED 2026-05-06 for Solana only** — Pyth is the canonical on-chain price feed for Solana DeFi adapters (per CLAUDE.md). Chainlink for EVM chains. This row is a historical note only; do NOT remove Pyth from Solana adapter code. |
| Infura    | Not an RPC provider we use (via UCI templates)                                                                                                                                                                                           |

## Capability registry

Each venue entry in the UAC venue capability registry declares:

```yaml
venue_id: BINANCE
venue_type: SINGLE_VENUE
category: CEFI
supported_operations:
  - { op: TRADE, instruments: [SPOT, PERP, OPTIONS] }
  - { op: QUOTE, instruments: [SPOT, PERP] }
  - { op: TRANSFER, intra_account: true }
  - { op: TICKS, instruments: [SPOT, PERP, OPTIONS] }
  - ...
collateral_rules:
  cross_margin_supported: true
  portfolio_margin_supported: true
  ltv_by_asset:
    USDT: 1.0
    BTC: 0.90
    ETH: 0.90
  min_cross_margin_pct_hedged: 0.05
liquidation_spec:
  trigger: MAINT_MARGIN_BREACH
  fee_bps: 50
margin_netting_rules:
  - { hedged_pair: [SPOT, PERP], netting_factor: 0.95 }
commission_structure:
  type: TIERED
  tiers: VIP_0 ... VIP_9
regional_restrictions:
  blocked_jurisdictions: [US]
```

Full schema: [/codex/02-data/contracts-scope-and-layout.md](/codex/02-data/contracts-scope-and-layout.md) + UAC
`registry/capability_declarations/`.

## Chain RPC templates

`CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py` is SSOT for chain→RPC mappings.
execution-service DeFi connectors import from UAC, never define their own.

Per CLAUDE.md.

## Cross-references

- Prime brokers: [prime-brokers.md](prime-brokers.md)
- Unity: [unity-integration.md](unity-integration.md)
- Venue capability registry service:
  [/codex/03-services/venue-capability-registry.md](/codex/03-services/venue-capability-registry.md)
- Venue availability (data shards): [/codex/02-data/venue-availability.md](/codex/02-data/venue-availability.md)
- Capital efficiency × venue features:
  [/codex/04-architecture/capital-efficiency-patterns.md](/codex/04-architecture/capital-efficiency-patterns.md)
- Transfer types:
  [/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md](/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md)

## Not in this doc

- **Per-venue adapter code** — execution-service/adapters/
- **Credential management** — ops / Secret Manager
- **VIP tier progression logic** — execution-service runtime
- **Per-chain gas models** — execution-service + UCI
- **Historical venue onboarding timeline** — audit
