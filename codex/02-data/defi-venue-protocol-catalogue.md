---
scope: [engineer, admin]
---

# DeFi Venue + Protocol Catalogue

> SSOT for the cross-chain × cross-protocol × cross-asset DeFi catalogue. Maps every protocol the system trades or
> reads against to its UAC entry, instruments-service catalog adapter, MTDS capture adapter, and execution-service
> connector. Last updated 2026-05-12 (defi_catalogue_chain_primitives_2026_05_10 Phase 1J refresh by slot 2
> `ikenna-defi-catalogue-tab`).
>
> **2026-05-12 refresh deltas**: (a) **CORRECTED 2026-05-12 by slot 8 audit IN-1**: `defi_venue_capabilities.py`
> DOES exist (178 LOC, holds `DEFI_VENUE_DATA_TYPE_CAPABILITIES`); both `defi_venues.py` AND
> `defi_venue_capabilities.py` are canonical SSOTs covering DIFFERENT axes — `defi_venues.py` carries
> `ALL_DEFI_VENUES` + per-venue chain support; `defi_venue_capabilities.py` carries per-(venue, data_type)
> capability matrix. The prior "does not exist" claim was drift-introducing (slot 5's 2026-05-11 finding at
> uac@`495d262` referred to a SUBSET of references being stale, NOT the file itself). Per operator triage
> 2026-05-12 (PM@`79f73426` relayed to slot 2) + slot 8 audit `catalogue_audit_defi_2026_05_12.md` DF-2/DF-3/DF-8;
> (b) Lending § Aave V3 Ethereum silent-zero row marked CLOSED AS STALE FRAMING per slot 3 audit 2026-05-11 +
> slot 2 verification 2026-05-12 (data exists on-disk; consolidator fix shipped); (c) Restaking § Renzo (ezETH) +
> KelpDAO (rsETH) UAC + LST mapping rows flipped ✅ (UAC@`961af767` extended `LST_TOKEN_TO_PROTOCOL_ASSET`);
> (d) Phase 1D Solana MEV cell flipped ✅ — `MevSubmissionMode.JITO_BUNDLE` shipped at UAC@`5241fad0` +
> execution-service@`38710bef`; (e) Phase 1B slot 5 chain × protocol matrix shipping confirmed at uac@`458f17d`
> (45/46 PROTOCOL_LAUNCH_DATES pairs). Remaining ◐ /✗ statuses reflect Phase 2+3+4 buildout not yet complete.

## How to read this doc

This is a catalogue, not an architecture. Every row tells you: where the protocol lives, what data we capture, what
we can execute, and which chain × asset_group axis it occupies. If a protocol is mentioned anywhere in CLAUDE.md or
plans, it must appear here — if it doesn't, that's a finding (file an issue doc per
[`Findings Triage Discipline`](../../cursor-configs/CLAUDE.md#findings-triage-discipline)).

**Status legend** (tightened 2026-05-12 per codex audit IN-10 — split code-shipped vs data-flowing):

- ✅ **PRODUCTION** — UAC entry + instruments-service adapter + MTDS adapter + execution connector ALL green AND
  **manifest coverage ≥ 99% verified by sample-parquet inspection** (rows present, OHLC populated, NOT 1440-NaN per
  the 2026-05-05 MDPS reference incident). Data is actually flowing.
- 🟢 **CODE-SHIPPED-AWAITING-BACKFILL** — UAC entry + adapter + connector all wired, code passes QG, but the first
  manifest-coverage backfill has not landed yet OR backfill is < 99% coverage. Distinct from ✅ — "code shipped" is
  NOT "operationally shipped" per CLAUDE.md "Plans Run To Actual Completion" rule. Cross-references catalogue findings
  DF-6 (vault venues "live"-labelled with no adapter / handler / capability) + DF-20 (MARGINFI / SOLEND "live" ghosts).
- ◐ **PARTIAL** — some axes live, others zero. See per-row notes.
- ✗ **ZERO** — no implementation. Either P0 buildout or post-cutover deferred per
  [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md).
- 🔍 **VERIFY** — claimed shipped but unverified in current codebase. Treat as ✗ until verification ships.

When a row flips from 🟢 to ✅, the commit message includes a manifest-coverage cite (sample-parquet inspection
result + manifest row count). The "UAC-symbol-shipped ≠ data-flowing" rule applies workspace-wide; the strictness here
mirrors the master-plan readiness-checklist Continuous-Verification column.

**Axis legend**: UAC = entry in
[`registry/defi_venues.py`](../../../unified-api-contracts/unified_api_contracts/registry/defi_venues.py)
(canonical SSOT for `ALL_DEFI_VENUES` + per-venue chain support) +
[`registry/defi_venue_capabilities.py`](../../../unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py)
(per-(venue, data_type) capability matrix — `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, 178 LOC) +
[`registry/chain_env.py`](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py)
(`PROTOCOL_LAUNCH_DATES` per `(chain, protocol)`) +
[`registry/defi_reserve_params.py`](../../../unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py)
(per-asset risk params for lending) + supporting registries; INSTR = instruments-service adapter at
`reference_data/adapters/defi/`; MTDS = market-tick-data-service adapter at `market_interface/adapters/defi/`
(or sibling); EXEC = execution-service connector at `defi_execution/protocols/`. **Note 2026-05-12 (slot 8 audit
IN-1 correction)**: `defi_venue_capabilities.py` IS canonical — covers the per-(venue, data_type) capability axis
that `defi_venues.py` (per-venue chain support) does NOT. The two registries are complementary, not redundant.

## Lending protocols

| Protocol | Chains | UAC | INSTR | MTDS | EXEC | Notes |
| -------- | ------ | --- | ----- | ---- | ---- | ----- |
| **Aave V3 Ethereum** | Ethereum | ✅ | ✅ (10 reserves × 2 tokens = 20 instruments) | ✅ captured 2022-03-16 → 2026-05-07 (silent-zero CLOSED AS STALE FRAMING 2026-05-11 slot 3 audit + 2026-05-12 slot 2 verification per `defi_master_2026_05_07.md` DONE-2026-05-12 block; data exists on-disk, consolidator fix shipped at deployment-service@`ad4d448` + slot 6@`2a76a2a`). Recent-days catch-up `2026-05-07..today` pending 5-10min scoped VM. | ✅ flash-loan + borrow/lend/repay; Sepolia validated | Reference flash-loan receiver per [`flash-loan-receiver.md`](../04-architecture/flash-loan-receiver.md). Coverage start 2022-03-16 |
| **Aave V3 multi-chain** | Arbitrum, Avalanche, Base, BSC, Linea, Optimism, Polygon, Scroll, ZkSync (9 chains) | ✅ | ✗ | ✗ | ✗ | All 9 chains P0 buildout [`defi_catalogue_chain_primitives` Phase 2/3/4 — parallel-agent J] |
| **Compound V3** | Ethereum, Arbitrum, Base, Optimism, Polygon, Scroll | ✅ | ◐ Ethereum only | ✗ | ✗ | Multi-chain buildout deferred until Phase 2/3/4 |
| **Spark** | Ethereum (live 2024-01-01) | ✅ ghost (UAC declares but downstream zero) | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent I |
| **Morpho** | Ethereum, Arbitrum, Base, Optimism, Polygon | ✅ | ◐ Ethereum curated | ✗ | ◐ lending connector exists; testnet pending | |
| **Morpho Blue** | Ethereum | ✅ (curated vault params at `defi_reserve_params.py:352-390`) | ◐ curated only | ✗ | ✗ | Per-market metadata not enumerated |
| **Fluid** | Ethereum | ✅ | ◐ limited | ✗ | ✗ | |
| **Radiant** | Arbitrum, BSC | ✗ orphan (INSTR adapter exists, UAC missing) | ✅ | ✗ | ✗ | Phase 1A adds UAC entry; Phase 2/3/4 builds out |
| **Kamino (Solana)** | Solana | ✅ | ✅ | ✗ (referenced in `lst_adapters.py` for LST rates only, not lending) | ✗ | Solana-only; cross-chain execution limited |

## DEX protocols (spot + swap)

| Protocol | Chains | UAC | INSTR | MTDS | EXEC | Notes |
| -------- | ------ | --- | ----- | ---- | ---- | ----- |
| **Uniswap V2** | Ethereum | ✅ | ✅ | ✅ TheGraph subgraph | ◐ subsumed under V3 | Coverage start 2020-05-04 |
| **Uniswap V3** | Ethereum, Arbitrum, Base, Optimism, Polygon | ✅ | ✅ top 1000 by liquidity | ✅ swaps + pools + position_data | ✅ SwapRouter02 + ERC20-approve + exactInputSingle; Sepolia validated | Reference DEX |
| **Uniswap V4** | Ethereum (launch 2025-01-30) | ✅ | ◐ Ethereum, limited pools | ✗ subgraph not yet live | ✗ V4 hooks-aware connector pending [Phase 2B sim plan; Phase 4 catalogue plan] | |
| **Curve stable + crypto** | Ethereum, Avalanche, Optimism | ✅ | ✅ | ✅ swaps + pools | ✗ | D-invariant + gamma slippage modeling lives in [`defi_simulation_realism` Phase 2C] |
| **Balancer** | Ethereum, Arbitrum, Avalanche, Base, Optimism, Polygon | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent C. Weighted + boosted + composable pool shapes |
| **Sushi V2** | Arbitrum | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent D |
| **Sushi V3** | Ethereum, Base, Avalanche | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent D |
| **PancakeSwap V3** | Ethereum, Arbitrum, Base, BSC | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent E |
| **Camelot V3** | Arbitrum | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent E |
| **Aerodromeq V3** | Base | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent F |
| **Velodrome V2** | Optimism | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent F |
| **TraderJoe V2** | Avalanche | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent G; bin-step pools |
| **Raydium (Solana)** | Solana | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent G; CLMM + standard AMM |
| **Orca (Solana)** | Solana | ✅ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent H; Whirlpool CLMM |
| **Jupiter aggregator (Solana)** | Solana | ✗ | ✗ | ✗ | ✗ | Phase 1A adds UAC entry; aggregator is read-only routing layer + per-route execution decomposition |

## LST (Liquid Staking Token) protocols

| Protocol | Token | Chain | UAC | INSTR | MTDS | EXEC | Notes |
| -------- | ----- | ----- | --- | ----- | ---- | ---- | ----- |
| **Lido** | stETH / wstETH | Ethereum | ✅ | ✅ | ✅ stETH-ETH peg + APY (on-chain contract reads) | ✅ stake/unstake/submit; Holesky testnet | Reference LST |
| **Ether.fi** | eETH / weETH | Ethereum | ✅ | ✅ | ✅ weETH-ETH rate + APY | ✅ Holesky testnet | LRT view of weETH covered in restaking section |
| **Ethena** | USDe | Ethereum | ✅ | ✗ | ✗ live (DefiLlama offline only) | ✗ | Limited use case for current archetypes |
| **Jito (Solana)** | jitoSOL | Solana | ✅ | ✗ Solana-specific catalog gap | ✅ Pyth-oracle-based via `lst_adapters.py` | ✗ | Pyth unbanned 2026-05-06 for Solana LST yields. Coverage cadence ~monthly pending Pyth historical backfill |
| **Marinade** | mSOL | Solana | ✅ | ✗ Solana-specific catalog gap | ✅ via `lst_adapters.py` | ✗ | Solana liquid-staking; read-only |
| **Rocket Pool** | rETH | Ethereum | ✗ | ✗ | ✗ | ✗ | Orphan in CLAUDE.md. Phase 1A adds UAC entry; Phase 2/3/4 builds out |
| **Solblaze** | bSOL | Solana | ✗ | ✗ | ✗ | ✗ | Orphan in CLAUDE.md. Phase 1A adds UAC entry; Phase 2/3/4 builds out |

## Restaking + LRT (Liquid Restaking Token) protocols

| Protocol | Token / Vault | Chain | UAC | INSTR | MTDS | EXEC | Notes |
| -------- | ------------- | ----- | --- | ----- | ---- | ---- | ----- |
| **EigenLayer** | (delegation, no token) | Ethereum | ✅ (rewards + staking_yields) | ✗ | ✗ | 🔍 claimed shipped 2026-03-13 but not in current `execution-service/venues/` or `defi_execution/protocols/` | Phase 4 verify-or-rebuild |
| **Symbiotic** | (vault) | Ethereum | ✗ | ✗ | ✗ | ✗ | Phase 1A adds UAC; Phase 2/3/4 — parallel-agent L |
| **Karak** | (vault) | Ethereum, Arbitrum | ✗ | ✗ | ✗ | ✗ | Phase 1A adds UAC; Phase 2/3/4 — parallel-agent M |
| **Renzo** | ezETH | Ethereum, Arbitrum | ✅ (UAC@`495d262` venue entry + UAC@`961af767` LST mapping (RENZO, ETH)) | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent M. Reserve params + INSTR/MTDS/EXEC adapters pending. |
| **KelpDAO** | rsETH | Ethereum | ✅ (UAC@`495d262` venue entry + UAC@`961af767` LST mapping (KELPDAO, ETH)) | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent N. Reserve params + INSTR/MTDS/EXEC adapters pending. |
| **Puffer** | (vault) | Ethereum | ✗ | ✗ | ✗ | ✗ | Phase 1A adds UAC; Phase 2/3/4 — parallel-agent N |
| **Jito restaking (Solana)** | (vault) | Solana | ✗ | ✗ | ✗ | ✗ | Phase 1A adds UAC; Phase 2/3/4 — parallel-agent O |

## Vault / yield-aggregator protocols

| Protocol | Chains | UAC | INSTR | MTDS | EXEC | Notes |
| -------- | ------ | --- | ----- | ---- | ---- | ----- |
| **Yearn** | Ethereum, Arbitrum, Optimism | ✗ | ✗ | ✗ (orphan calculator `vault_share_price_apy_calculator.py` in features-onchain has no upstream) | ✗ | Phase 1A adds UAC; wire orphan calculator upstream as part of Phase 3 |
| **Convex** | Ethereum | ✗ | ✗ | ✗ | ✗ | Curve-LP-staking-vault. Phase 2/3/4 — parallel-agent A |
| **Beefy** | Ethereum, Arbitrum, Base, Polygon, BSC, Avalanche | ✗ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent B |
| **Pendle** | Ethereum, Arbitrum | ✗ | ✗ | ✗ | ✗ | PT/YT/SY tokens with maturity dates. Phase 2/3/4 — parallel-agent B |
| **Idle** | Ethereum, Arbitrum, Polygon | ✗ | ✗ | ✗ | ✗ | Phase 2/3/4 — parallel-agent C |

## Perp DEX / on-chain CLOB venues

**FLAG 1 RESOLVED 2026-05-10**: All on-chain perp / CLOB venues classified under `VENUES_BY_ASSET_GROUP["cefi"]`
axis (CLOB-style data shape, regardless of on-chain settlement). Captures wired across the 6 perp venues.

| Venue | Chain | UAC | INSTR | MTDS | EXEC | Notes |
| ----- | ----- | --- | ----- | ---- | ---- | ----- |
| **Hyperliquid** | Hyperliquid L1 (Arbitrum-anchored) | ✅ (cefi axis) | ◐ CeFi treats as venue, not on-chain | ✅ tick-tape via market_interface/cefi adapter | ✅ mainnet validated | Master plan "6 perp venues" |
| **Aster** | Arbitrum | ✅ (cefi axis) | ✅ instrument registry | ✅ on-chain perp adapter | ◐ skeleton at `defi_execution/protocols/aster.py` — error handling only, full trade execution PENDING [Phase 4 catalogue plan] | Master plan "6 perp venues" |
| **GMX** | Arbitrum, Avalanche | ✅ (UAC + cefi axis dual-classified — Phase 1C cleanup pending) | ✗ | ✗ MTDS adapter for perp_funding declared but not implemented | ✗ | Phase 1C resolves dual classification (recommendation: cefi axis only) |
| **DRIFT (Solana)** | Solana | ✅ (UAC + cefi axis dual-classified — Phase 1C cleanup) | ✗ | ✗ | ✗ | Same dual-classification issue as GMX |
| **Pacifica (Solana)** | Solana | ✅ (cefi axis) | ✗ | ◐ OHLCV partial (code shipped, ABI parsing PENDING) | ✗ | Phase 6D backfill |
| **Extended (StarkNet)** | StarkNet | ✅ (cefi axis) | ✗ | ◐ OHLCV partial | ✗ | Phase 6D backfill |
| **Lighter (zkSync)** | zkSync | ✅ (cefi axis) | ✗ | ◐ OHLCV partial | ✗ | Phase 6D backfill |
| **dYdX V4** | Cosmos (dYdX chain) | ✗ | ✗ | ✗ | ✗ | OUT OF SCOPE for May-23 (operator may revisit post-cutover) |
| **Vertex** | Arbitrum | ✗ | ✗ | ✗ | ✗ | OUT OF SCOPE |
| **Jupiter perps (Solana)** | Solana | ✗ | ✗ | ✗ | ✗ | OUT OF SCOPE |

## Per-protocol shard-atom matrix

> **Codex SSOT for per-protocol shard atom** (mirrored from
> [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md)
> Phase 2 design — published 2026-05-12 + mirrored to codex 2026-05-13 by slot 2). Decides bundled-vs-per-instrument
> per protocol family. Composes with [`shard-level-failure-isolation.md`](../04-architecture/shard-level-failure-isolation.md)
> + writegate Phase 3.D.5 cluster validation.

**Base shard atom for ALL DeFi protocols** (per
[`per-asset-group-bucket-layouts.md`](per-asset-group-bucket-layouts.md) line 69 + UAC
`canonical/domain/defi/gcs_paths.py`): `(date, asset_group=defi, chain, venue, instrument_type, data_type)`. Path:
`raw_tick_data/by_date/day={date}/asset_group=defi/chain={chain}/venue={v}/instrument_type={it}/data_type={dt}/ticks.parquet`.

**Per-protocol-family refinement** (whether instrument is a row-level column INSIDE the parquet vs hive-partition
shard axis OUTSIDE; mirrors the predictions/sports multi-axis correction pattern banner from 2026-05-06):

| Protocol family | Per-instrument count | Shard granularity | Instrument axis location | Cluster validation |
|-----------------|----------------------|-------------------|--------------------------|--------------------|
| **Lending** (Aave / Spark / Compound / Morpho / Radiant / Fluid) | ~10-20 reserves per (protocol, chain) | **Per-(chain, protocol, asset, data_type, day)** = one manifest row per `(asset, day)` | `asset_symbol` IS a hive shard key | Not bundled |
| **DEX V3 + CLMM** (Uniswap V3 / Sushi V3 / PancakeSwap / Camelot / Aerodromeq / Velodrome / TraderJoe V2 / Balancer / Curve / Raydium / Orca) | 100-1000+ pools per (protocol, chain) | **BUNDLED per-(chain, protocol, data_type, day)** | `pool_address` is row-level | **MANDATORY** |
| **DEX V2** (Uniswap V2 / Sushi V2) | smaller pool catalog | BUNDLED same as V3 | row-level `pool_address` | MANDATORY |
| **LST** (Lido / Ether.fi / Rocket Pool / Jito / Marinade / Solblaze / Ethena / Spark sDAI) | 1 token per (protocol, chain) | Per-(chain, protocol, token, data_type, day) | hive key on `token_symbol` | Not bundled |
| **Restaking single-token LRT** (Renzo ezETH / KelpDAO rsETH / Ether.fi weETH) | 1 token per (protocol, chain) | Same as LST | hive key on `token_symbol` | Not bundled |
| **Restaking multi-vault** (Symbiotic / Karak / EigenLayer / Puffer / Jito-restaking) | dozens of vaults per (protocol, chain) | **BUNDLED per-(chain, protocol, data_type, day)** | row-level `vault_address` | MANDATORY |
| **Vaults / yield-aggregator** (Yearn / Convex / Beefy / Pendle / Idle) | 50-200+ vaults per (protocol, chain) | **BUNDLED per-(chain, protocol, data_type, day)** | row-level `vault_address` | MANDATORY |
| **Aggregators** (Jupiter Solana) | n/a (read-only routing) | per-(chain, protocol, data_type, day) | route is row-level | Not bundled (registry snapshot) |
| **Perp DEX / on-chain CLOB** (Hyperliquid / Aster / GMX / Drift / Pacifica / Extended / Lighter) | per FLAG 1 RESOLVED 2026-05-10 → classified under cefi asset_group | Per-(venue, instrument, data_type, day) — same as CEFI venues | hive key on `instrument_id` | Not bundled |

**Rationale — why BUNDLED for DEX / Vaults / multi-vault Restaking**: per-pool/per-vault shard would inflate
manifest by 100-1000× per (protocol, chain). Bundled keeps manifest ≤ ~30k rows per DEX protocol per year. Per-pool
detail recoverable via row-level columns + cluster validation gates silent loss
(`expected_root_clusters` + `cluster_extractor` per UTL `record_captured` HARD RULE).

**Compliance with Shard-granularity SSOT** (per
[`shard-level-failure-isolation.md`](../04-architecture/shard-level-failure-isolation.md) +
`plans/epics/infrastructure_master_2026_05_07.md`): shard atom MUST be identical across (a) writer atomicity,
(b) manifest row key, (c) data-status display, (d) downstream pre-flight gate, (e) deployment-UI drilldown.
Per-protocol Phase 2 adapter implementations MUST honor this matrix; deployment-UI drilldowns roll up to this same
granularity.

## Per-chain coverage summary

| Chain | Genesis | RPC primary | RPC fallback | Gas oracle | MEV protection | DeFi protocols (this catalogue) |
| ----- | ------- | ----------- | ------------ | ---------- | -------------- | ------------------------------- |
| Ethereum | 2015-07-30 | Alchemy | Infura (Phase 5B) | EIP-1559 base+priority via `gas_fee_client.py` | Flashbots Protect (`rpc.flashbots.net`) | Aave / Compound / Spark / Morpho / Fluid / Lido / Ether.fi / Ethena / Uniswap V2/V3/V4 / Curve / Balancer / Sushi V3 / PancakeSwap V3 / EigenLayer / Symbiotic / Karak / Renzo / KelpDAO / Puffer / Yearn / Beefy / Idle |
| Arbitrum | 2021-08-31 | Alchemy | Phase 5B | sequencer RPC (centralised; structural MEV reduction) | Sequencer (centralised) | Aave V3 / Compound V3 / Morpho / Radiant / Uniswap V3 / Curve / Balancer / Sushi V2 / Camelot V3 / PancakeSwap V3 / Pendle / Beefy / Idle / Karak / Renzo |
| Base | 2023-08-09 | Alchemy | Phase 5B | sequencer RPC | Sequencer | Aave V3 / Compound V3 / Morpho / Uniswap V3 / Sushi V3 / PancakeSwap V3 / Aerodromeq V3 / Beefy |
| Optimism | 2021-12-16 | Alchemy | Phase 5B | sequencer RPC | Sequencer | Aave V3 / Compound V3 / Morpho / Uniswap V3 / Curve / Balancer / Velodrome V2 / Yearn |
| Polygon | 2020-05-30 | Alchemy | Phase 5B | EIP-1559 | (no Flashbots equivalent yet) | Aave V3 / Compound V3 / Morpho / Uniswap V3 / Balancer / Beefy / Idle |
| Avalanche | 2020-09-22 | Alchemy | Phase 5B | EIP-1559 | (no Flashbots equivalent) | Aave V3 / Curve / Balancer / Sushi V3 / TraderJoe V2 / Beefy |
| BSC | 2020-08-29 | Alchemy | Phase 5B | EIP-1559 | (no Flashbots equivalent) | Aave V3 / Radiant / PancakeSwap V3 / Beefy |
| Linea | 2023-07-11 | Alchemy | Phase 5B | sequencer | Sequencer | Aave V3 |
| Scroll | 2023-10-17 | Alchemy | Phase 5B | sequencer | Sequencer | Aave V3 / Compound V3 |
| ZkSync Era | 2023-03-24 | Alchemy | Phase 5B | sequencer | Sequencer | Aave V3 / Lighter |
| Solana | 2020-03-16 | Helius | Alchemy + public Solana RPC (Phase 5B) | priority-fees-lamports + compute-unit-price | ✅ Jito bundle submission via `MevSubmissionMode.JITO_BUNDLE` UAC enum + `_DEFAULT_POLICIES[JITO_BUNDLE]` in `execution-service/v2/mev_router.py` (Phase 1D shipped 2026-05-12 UAC@`5241fad0` + execution-service@`38710bef`; `endpoint_ref=jito_bundle_rpc`, `max_block_delay=2`, `bundle_mode=private`). Block-engine RPC endpoint resolved via UCI/Secret Manager at dispatch. | Jito (LST) / Marinade / Solblaze / Raydium / Orca / Jupiter agg / Drift / Pacifica / Kamino / Jito restaking |
| StarkNet | n/a (L2) | Voyager / Alchemy | Phase 5B | n/a | Sequencer | Extended |

Other chains in `CHAIN_GENESIS_DATES` (Celo / Aurora / Fantom / Mantle / Gnosis / Metis / Moonbeam / Blast / Mode /
BSC alt-name / Polygon zkEVM if distinct) — UAC-declared genesis but currently no protocols catalogued. Out of scope
for May-23 unless explicitly added.

## Cross-references

- **Plan**:
  [`defi_catalogue_chain_primitives_2026_05_10.md`](../../plans/active/defi_catalogue_chain_primitives_2026_05_10.md)
  is the buildout plan for everything ✗ in this catalogue.
- **Plan**: [`defi_simulation_realism_2026_05_10.md`](../../plans/active/defi_simulation_realism_2026_05_10.md)
  consumes this catalogue (per-pool-shape models per protocol; per-protocol staking yield decomposition).
- **Codex**: [`defi-data-type-taxonomy.md`](defi-data-type-taxonomy.md) — what data we capture per protocol per
  data_type.
- **Codex**: [`chain-rpc-mev-tenderly.md`](../05-infrastructure/chain-rpc-mev-tenderly.md) — chain-level RPC + MEV +
  Tenderly + gas oracle SSOT.
- **UAC SSOT**:
  [`registry/defi_venue_capabilities.py`](../../../unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py),
  [`registry/defi_reserve_params.py`](../../../unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py),
  [`registry/chain_env.py`](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py).
- **CLAUDE.md**: [Master Plan — Live DeFi Trading by 2026-05-23](../../cursor-configs/CLAUDE.md#master-plan--live-defi-trading-by-2026-05-23)
  + [DeFi Execution Architecture](../../cursor-configs/CLAUDE.md#defi-execution-architecture).

## Update protocol

- **Adding a new protocol** = adding a row here + UAC entry + INSTR adapter + MTDS adapter + EXEC connector (per
  scope) + manifest backfill. Do all in one logical unit per Citadel-Grade § 3 No Technical Debt.
- **Status change** (✗ → ◐ → ✅) requires updating this row + the corresponding plan checkbox per
  [`Commit + Push + Flip Plan Checkboxes`](../../cursor-configs/CLAUDE.md#commit--push--flip-plan-checkboxes-as-you-ship-each-item-hard-rule).
- **Removing a protocol** (decision: post-May-23 deferral or genuinely out of scope) = same logical unit removes
  this row + UAC entry + downstream consumers per Citadel-Grade § 6.
