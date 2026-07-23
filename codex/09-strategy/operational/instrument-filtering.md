---
doc_type: codex-ssot
title: Instrument Filtering — DeFi Pool & Market Discovery
summary:
  The DeFi instrument-filtering pipeline keyed on the ~65-symbol DEFI_MAJOR_ASSET_SYMBOLS whitelist (UAC
  defi_major_assets.py) — per-adapter rules (both-sides-major for DEX pools, base-asset-major for lending, TVL minimums
  for Solana), address maps for subgraph/RPC filtering, and strategy-level underlying families.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [instruments, defi, catalogue, uac, registry, data-quality]
related:
  [
    ../../04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/09-strategy/operational/client-strategy-config.md,
  ]
created: 2026-03-30
authoritative_for: [DeFi instrument filtering rules + DEFI_MAJOR_ASSET_SYMBOLS major-asset whitelist]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/defi/aave-lending.md,
    /codex/09-strategy/_archived_pre_v2/defi/basis-trade.md,
    /codex/09-strategy/_archived_pre_v2/defi/btc-basis-trade.md,
    /codex/09-strategy/_archived_pre_v2/defi/btc-lending-yield.md,
    /codex/09-strategy/_archived_pre_v2/defi/cross-chain-sor-rebalancing.md,
    /codex/09-strategy/_archived_pre_v2/defi/cross-chain-yield-arb.md,
    /codex/09-strategy/_archived_pre_v2/defi/ethena-benchmark.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Instrument Filtering — DeFi Pool & Market Discovery

## Overview

DeFi protocols (DEXes, lending, staking) expose thousands of instruments — most are illiquid shitcoin pools. The
instrument filtering pipeline ensures only tradeable, liquid instruments reach the strategy layer.

**SSOT**: `unified-api-contracts/registry/defi_major_assets.py`

## Major Asset Whitelist

`DEFI_MAJOR_ASSET_SYMBOLS` is a `frozenset` of ~65 symbols across all chains:

| Category             | Tokens                                                                                                             | Purpose                            |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| **ETH + LSTs**       | ETH, WETH, STETH, WSTETH, CBETH, RETH, WEETH, EETH, SFRXETH, FRXETH, EZETH, RSETH, METH, PUFETH, ANKRETH, + 4 more | Lending collateral, staking, LP    |
| **BTC + Wrapped**    | BTC, WBTC, TBTC, CBBTC, LBTC                                                                                       | Cross-chain BTC exposure           |
| **Stablecoins**      | USDT, USDC, DAI, FRAX, USDE, SUSDE, GHO, CRVUSD, LUSD, PYUSD, EURC, SUSD, TUSD, USDP                               | Quote currency, lending, LP        |
| **DeFi Governance**  | AAVE, LINK, UNI, MKR, CRV, SNX, BAL, LDO, RPL, COMP, YFI, SUSHI, 1INCH, FXS                                        | Aave collateral, governance LP     |
| **Multi-chain**      | SOL, MATIC, WMATIC, AVAX, WAVAX, BNB, WBNB                                                                         | Cross-chain native tokens          |
| **Solana LSTs**      | WSOL, MSOL, STSOL, JITOSOL, BSOL, JSOL                                                                             | Solana staking, recursive leverage |
| **Solana Ecosystem** | JUP, RAY, ORCA, BONK, PYTH, JTO, WIF, HNT, MNDE                                                                    | Top Solana LP pairs                |
| **Bridged Variants** | WETH.E, USDC.E, USDT.E                                                                                             | Avalanche/Polygon bridged tokens   |

## Filtering Rules by Adapter Type

### DEX Pools (Uniswap, Curve, Balancer, Orca, Raydium)

**Rule: BOTH sides of the pool must be in `DEFI_MAJOR_ASSET_SYMBOLS`.**

This means SOL/FARTCOIN gets rejected (FARTCOIN not in list) but SOL/USDC passes (both in list).

| Adapter    | Chain        | Filter                                   | TVL Minimum                     |
| ---------- | ------------ | ---------------------------------------- | ------------------------------- |
| Uniswap V2 | Ethereum     | Both sides major                         | None (query-level via subgraph) |
| Uniswap V3 | ETH/Arb/Base | Both sides major                         | $100k (query param `minTvl`)    |
| Uniswap V4 | Ethereum     | Both sides major                         | None                            |
| Curve      | Ethereum     | Both sides major                         | None                            |
| Balancer   | Multi-EVM    | **ALL** tokens major (multi-token pools) | None                            |
| Orca       | Solana       | Both sides major                         | $10k TVL minimum                |
| Raydium    | Solana       | Both sides major                         | $10k TVL minimum                |

**Why Solana needs TVL minimum but EVM doesn't**: EVM DEXes are filtered at the subgraph query level (address
whitelist). Solana DEXes return all pools via REST API and filter client-side — without TVL minimum, you get thousands
of dust pools.

### Lending Markets (Aave, Compound, Morpho, Kamino)

**Rule: Base/loan asset must be in `DEFI_MAJOR_ASSET_SYMBOLS`.**

Only one side is checked because lending is single-sided (you supply ONE token). Collateral assets are validated by the
protocol itself (Aave only accepts whitelisted collateral).

| Adapter     | Filter                  | Notes                                  |
| ----------- | ----------------------- | -------------------------------------- |
| Aave V3     | Base asset major        | Returns A_TOKEN + DEBT_TOKEN per asset |
| Compound V3 | Base asset major        | Per-Comet market filtering             |
| Morpho Blue | Loan + collateral major | Both sides for isolated markets        |
| Kamino      | Base asset major        | Solana lending vaults                  |

### Perpetuals / Derivatives (Hyperliquid, Aster, Drift)

**Rule: Base asset must be in CeFi base asset universe** (separate from DeFi whitelist).

Perp exchanges have their own instrument listing — we use `VenueMapping.hyperliquid_aster_mvp_base_assets` (21 coins)
for CeFi on-chain CLOBs.

### LST / Yield Protocols (Lido, EtherFi, Ethena, Marinade)

**Rule: No filtering needed.** These protocols have a small, curated instrument set (1-3 instruments each). The adapter
returns all of them.

## Token Address Filtering (EVM Subgraph Optimization)

For EVM subgraph queries, we also maintain `DEFI_MAJOR_ASSET_ADDRESSES` — Ethereum mainnet contract addresses for the
major tokens. This allows filtering at the GraphQL query level:

```graphql
pools(where: { token0_in: ["0xC02a...", "0x2260..."], token1_in: [...] })
```

This is more efficient than fetching all pools and filtering client-side.

## Solana Token Addresses

In addition to symbol-based filtering, Solana adapters maintain `SOLANA_TOKEN_ADDRESSES` -- a mapping of ~35+ token mint
addresses for major Solana assets. This includes:

- **Native + LSTs:** WSOL, mSOL, stSOL, JitoSOL, bSOL, JSOL
- **Stablecoins:** USDC, USDT (SPL token mints)
- **Ecosystem tokens:** JUP, RAY, ORCA, BONK, PYTH, JTO, WIF, HNT, MNDE, and more

These addresses enable on-chain filtering at the RPC level (e.g., querying Raydium CLMM pools by token mint) rather than
fetching all pools and filtering client-side. The address mapping is maintained alongside `DEFI_MAJOR_ASSET_SYMBOLS` and
kept in sync.

## Adding New Tokens

1. Add symbol to `DEFI_MAJOR_ASSET_SYMBOLS` in `defi_major_assets.py`
2. If EVM: add contract address to `DEFI_MAJOR_ASSET_ADDRESSES`
3. If new chain/protocol: add to `DEX_VENUE_KEYWORDS` if it's a DEX
4. Update UCI `InstrumentDomainConfig.defi_major_assets` (kept in sync manually)
5. No service restart needed for instruments-service (next discovery run picks it up)

## Underlying Families (Strategy-Level Grouping)

The whitelist defines what instruments are **discoverable**. Strategy configs then select **which subset to trade**
using underlying families:

- **Stablecoin family**: USDC, USDT, DAI — used by lending basket strategies
- **ETH family**: ETH, WETH — used by ETH lending variant
- **BTC family**: WBTC, CBBTC, TBTC — used by BTC basis strategies
- **SOL family**: SOL, WSOL, mSOL, JitoSOL — used by Solana staking/basis

The possible universe comes from UAC (this whitelist). The configured family is a **fixed** strategy config parameter
(not gridded). Validated against the whitelist at strategy init time.

## References

- **SSOT**: [defi_major_assets.py](unified-api-contracts/unified_api_contracts/registry/defi_major_assets.py)
- **Instrument adapters**:
  [instruments-service/reference_data/adapters/](instruments-service/instruments_service/reference_data/adapters/)
- **Underlying families feedback**: [memory/feedback_underlying_families_and_depeg.md]
