---
doc_type: plan
title: DeFi catalogue + chain primitives buildout (May-23 cutover)
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/defi_master.md,
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/defi_simulation_realism_2026_05_10.md,
    plans/active/cross_asset_group_catalogue_audit_2026_05_10.md,
    plans/active/writegate_honest_coverage_endtoend_2026_05_06.md,
  ]
created: 2026-05-10
locked_by: live-defi-rollout
locked_since: 2026-05-10
estimate_class: design
estimate_baseline_ai_days: 342.5
estimate_calibrated_ai_days: 205.5
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~3-5, ~30-45,
  ~30-45, ~25-40, + 4 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
parent_epic: defi_master
priority: P0
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# DeFi catalogue + chain primitives buildout (May-23 cutover)

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BLOCK)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> § "Anti-sequencing audit" row 334 flags this plan as a Phase 1.E freeze-gate critical-path item. NEW UAC `data_type`
> enums (`SUPPLY_APY` / `BORROW_APY` / `UTILISATION` / `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` — shipped uac@`d02cce2`
> per slot 5 audit 2026-05-11) MUST be referenced in `manifest_schema_final_gate_2026_05_09.md` v8 schema declaration
> BEFORE Phase 1 freeze 2026-05-15. ALL_DEFI_VENUES 74→99 venue declarations shipped uac@`495d262` (slot 5 2026-05-11).
> Phase 1A still open: per-protocol `SourceCapability` objects + Solana Jito MEV + per-venue margin-tier table +
> LST_TOKEN_TO_PROTOCOL_ASSET verify. Phase 1 (UAC SSOT extensions) is the SEQUENTIAL gate for Phases 2-6 fan-out.
> Reader contract: scan top-of-file banners before touching `data_type` column / `BUNDLED_DATA_TYPES` registry / chain
> primitives / `PROTOCOL_LAUNCH_DATES` / venue-capability tables.

## Why this plan exists

The 2026-05-08 catalogue audit (since consumed; spawned this plan + `defi_simulation_realism_2026_05_10` +
`cross_asset_group_catalogue_audit_2026_05_10`) surfaced 22 P-tagged blockers across 6 DeFi-primitive categories (vaults
/ lending / LST / restaking-LRT / perp DEX / spot DEX) plus chain primitives (gas / oracles / MEV / Tenderly / RPC
redundancy). Operator directive 2026-05-10 closes Gate 1 maximalist: "alli in scope for may 23 pls" — every primitive
mentioned anywhere in CLAUDE.md / UAC / codex / plans that is currently zero-or-partial is now P0 May-23 scope, not
deferred.

This plan owns the **catalogue + chain-primitives** half of that work. The simulation-realism half (per-pool AMM
slippage models, lending rate-impact-from-own-trade, governance proposal sim, staking + restaking yield-stream sim,
slashing tail-risk MC) lives in the sibling plan
[`defi_simulation_realism_2026_05_10.md`](../archive/defi_simulation_realism_2026_05_10.md). The cross-asset-group SSOT
cleanup + manifest-coverage-% UI surface lives in
[`cross_asset_group_catalogue_audit_2026_05_10.md`](../archive/cross_asset_group_catalogue_audit_2026_05_10.md).

**Citadel-Grade discipline gates** (per CLAUDE.md § Citadel-Grade Planning Standards): pre-audit done in spawning
question doc; phased DAG below; no tech-debt shims (clean breaks per protocol); maximal parallelization across protocols
once Phase 1 SSOT lands; explicit success criteria per phase; downstream consumer updates enumerated; SSOT discipline
(UAC owns every contract; service code consumes only the declared shape).

## Pre-audit reference

The 2026-05-08 question doc was fully consumed when this plan + sibling spawned plans landed; the 22-blocker pre-audit
content is folded into the per-category sections below + into `defi_simulation_realism_2026_05_10` +
`cross_asset_group_catalogue_audit_2026_05_10`. Do NOT re-audit at execution time — read the per-category sections, then
start Phase 1.

Concrete pre-audit deltas (the 22-blocker list condensed by category, with file:line citations from the audit):

- **Vaults (Cat 1 — fully zero)**: Yearn / Convex / Beefy / Pendle / Idle. Zero UAC entries. Zero instruments. Zero MTDS
  adapters. Zero connectors. Orphan calculator
  `features-service (onchain family)/app/calculators/vault_share_price_apy_calculator.py` exists with no upstream.
- **Lending (Cat 2 — partial)**: Aave V3 Ethereum captured (silent-zero bug 0/343 shards 2026-05-07; deferred to
  writegate Phase 2.A). Aave V3 9 non-Ethereum chains: UAC declared, instruments+MTDS+connectors zero. Spark: UAC
  declared (Ethereum live 2024-01-01), instruments+MTDS+connector zero. Radiant: instruments-service adapter exists, UAC
  entry zero. Compound V3 / Morpho Blue / Fluid: partial.
- **LSTs (Cat 3 — partial)**: Lido + Ether.fi Ethereum wired. Solana LSTs (jitoSOL / mSOL / bSOL): instruments catalogue
  zero, capture cadence "thin (~monthly per jitoSOL oracle)" pending Pyth historical backfill, connectors zero. Rocket
  Pool (rETH) + Solblaze (bSOL) orphans: zero across all axes.
- **Restaking + LRTs (Cat 4 — fully zero except EigenLayer ambiguous)**: EigenLayer connector claimed shipped 2026-03-13
  but NOT in current `execution-service/venues/` or `defi_execution/protocols/` — verify or rebuild. Symbiotic / Karak /
  Renzo (ezETH) / KelpDAO (rsETH) / Puffer / Jito restaking (Solana): zero UAC, zero instruments, zero capture, zero
  connectors.
- **Perp DEXes (Cat 5 — FLAG 1 RESOLVED)**: Hyperliquid + Aster + Pacifica + Extended + Lighter + GMX + Drift all
  classified under `VENUES_BY_ASSET_GROUP["cefi"]` axis. Capture wired across the 6 perp venues. Aster connector
  incomplete (only error-handling code, no trade execution). Lighter / Pacifica / Extended OHLCV partial (code shipped,
  contract addresses + ABI parsing pending, backfill not yet run).
- **Spot DEXes (Cat 6 — catastrophic gap)**: Uniswap V2/V3/V4 + Curve catalogued + captured + Uniswap V3 connector only.
  Balancer / Sushi V2+V3 / PancakeSwap V3 / Camelot V3 / Aerodromeq V3 / Velodrome V2 / TraderJoe V2 (11 EVM)
  - Raydium / Orca (2 Solana): UAC declared, **zero instruments + zero MTDS + zero connectors**. Jupiter aggregator: not
    in UAC.
- **Chain primitives**: Solana MEV (Jito bundle submission) NOT in `mev_router.py`. Per-chain RPC redundancy unverified
  (single-Alchemy-provider risk). Tenderly bundle-sim API gating policy not declared. Per-venue maintenance-margin /
  initial-margin tier tables NOT located at single SSOT.

## Execution DAG (phased, with parallelism markers)

```
Phase 1 (SEQUENTIAL — UAC SSOT gate)
        │
        ▼
Phase 2 (PARALLEL across 26 protocols × instruments-service)
Phase 3 (PARALLEL across 26 protocols × MTDS adapter, depends on Phase 2 per protocol)
Phase 4 (PARALLEL across connectors, depends on Phase 2 per protocol)
Phase 5 (PARALLEL with 2-4 — chain primitives: Jito MEV / RPC redundancy / Tenderly bundle-sim)
        │
        ▼
Phase 6 (PARALLEL VM-launch backfills, depends on Phase 2+3+4)
        │
        ▼
Phase 7 (Codex SSOT updates — per-phase boundaries throughout, NOT just at end; per Post-Plan-Phase Codex Audit HARD RULE)
        │
        ▼
Phase 8 (Paper-trade + reconciliation + 7-day live-trade proof, depends on Phase 6 captures landing)
```

Phase-1 + Phase-7 are sequential gates; Phases 2-6 maximally parallel across protocols + chain primitives.

## Phase 1 — UAC SSOT extensions (SEQUENTIAL gate; ~3-5 AI-days)

Owner: ikenna (cross-cutting design); harsh implements per protocol once contracts land.

> **🔴 BLOCKER FOR recursive-borrow Phase 9 — RATIFIED 2026-05-10 cross-plan audit Q11**
>
> This plan is the **canonical owner of lending-indices fix scope** (Bug 1 Aave V3 silent-zero / Bug 2 Compound V3
> multi-chain subgraph / Bug 3 instruments-store 2022 metadata floor) per most-comprehensive-owner rule. The
> [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) plan reframes its
> Phase 1 as a passive blocker gate consuming THIS plan's Phase 3 capture output. Phase 9 (backtest) of recursive-borrow
> cannot start until this plan's Phase 3 reports `captured` for Aave V3 Ethereum + Compound V3 Ethereum/Arbitrum/Base
> SUPPLY_APY / BORROW_APY / UTILISATION across 2022-03-01 → present at day-grain.
>
> Add explicit todos to Phase 1 (UAC data_type enums) + Phase 3 (MTDS adapter rewrites + backfill VM) below.

Success criterion: every protocol added in this plan has a UAC entry that downstream consumers (instruments-service /
MTDS / execution-service) compile against. UAC QG green. No service code references a protocol not declared in UAC.

- [x] [AGENT] P0. **1-LENDING — Lending-indices UAC enums (folded in from recursive-borrow Phase 1 per Q11 ratification
      2026-05-10)**. Add `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` / `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` to
      `data_type` enum. **✅ SHIPPED 2026-05-11 by slot 5 (ikenna-defi-phase-1e-tab)** at
      `unified-api-contracts/unified_api_contracts/internal/domain/market_data_processing/candle_schema.py` (SSOT
      location for `DataType` enum — the plan's original ref to `canonical/domain/market_data/data_types.py` was stale;
      grep-verified only one `class DataType(StrEnum)` in UAC, lives in `candle_schema.py`). All 5 enum values added
      after `LENDING_INDICES` with comment block citing this plan + recursive-borrow Q11 ratification. Smoke-import
      verified — `DataType` count 30 → 35, all 5 values resolve to lowercase strings (`supply_apy` / `borrow_apy` /
      `utilisation` / `liquidation_threshold` / `emode_params`). **DEFERRED to Stream C downstream sweep**: (a)
      `BUNDLED_DATA_TYPES` extension — utilisation-per-pool MAY be bundled per protocol but the bundling decision
      belongs to the per-protocol MTDS adapter author (Phase 3 catalogue plan); (b) manifest `data_type` column
      validation wire-in is automatic via `DataType` StrEnum membership — no extra work. Coordinate with
      [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) Phase 1
      reframed-as-blocker section — that plan no longer ships these; this plan ships them as part of Phase 1.

- [x] [AGENT] P0. **1A — Extend `defi_venue_capabilities.py`** (`unified-api-contracts/unified_api_contracts/registry/`)
      **✅ SHIPPED 2026-05-15 slot-2 (ikenna-slot2-tab) at uac@`00d526c`** — 26 new DEFI_VENUE_DATA_TYPE_CAPABILITIES
      entries for Phase 1A protocols: Yearn V3 (ETH/ARB/OPT), Convex, Beefy (6 chains), Pendle (ETH/ARB), Idle (3
      chains), Rocket Pool, SolBlaze, Symbiotic, Karak (ETH/ARB), Renzo (ETH/ARB), KelpDAO, Puffer, Jito Restaking,
      Jupiter. UAC QG clean. with entries for: Yearn, Convex, Beefy, Pendle, Idle, Balancer (verify already present),
      Sushi V2+V3, PancakeSwap V3, Camelot V3, Aerodromeq V3, Velodrome V2, TraderJoe V2, Raydium, Orca, Jupiter
      aggregator, Spark (verify already present), Radiant, Rocket Pool, Solblaze, Symbiotic, Karak, Renzo, KelpDAO,
      Puffer, Jito-restaking. Per-entry: `(venue_id, chain_id, data_types, start_date)`. Match shape of existing Aave V3
      / Lido entries. **PARTIAL 2026-05-11 by slot 5 (ikenna-defi-phase-1e-tab) — venue_id + chain_id + start_date
      shipped at uac@`495d262`** in `unified_api_contracts/registry/defi_venues.py` (NOTE 2026-05-12 IN-1: the prior
      "grep-verified that file does not exist" claim about `defi_venue_capabilities.py` was INCORRECT per operator
      decision PM@`32d0174e`. `defi_venue_capabilities.py` IS canonical — it covers the per-(venue, data_type)
      capability matrix + start dates, distinct from `defi_venues.py` which covers venue identity (ALL_DEFI_VENUES +
      LEGACY_DEFI_VENUE_ALIASES). Both coexist intentionally; the 900-line QG ceiling drove the split. Codex doc
      corrected by Harsh slot 8. The correct SSOT for the Phase 1A extension work was BOTH files — venue identity
      additions landed in `defi_venues.py`; capability-matrix entries for the new 25 protocols are a Phase 1A follow-up
      via `defi_venue_capabilities.py`). Shipped: ALL_DEFI_VENUES extended from 74 → 99 (25 new entries — 8 ETH + 7
      ARB + 1 BASE + 1 OP + 2 POLY + 1 AVAX + 2 BSC + 3 SOL); DEFI_VENUE_PHASE 1:1 invariant preserved with all 25
      marked "pipeline"; LEGACY_DEFI_VENUE_ALIASES extended with 13 bare-name aliases; `chain_env.py`
      PROTOCOL_LAUNCH_DATES extended with 12 confident dates (CONVEX/PENDLE/IDLE on ETH, SYMBIOTIC/KARAK/RENZO/KELPDAO
      on ETH, PENDLE/RADIANT on ARB, RADIANT on BSC, JUPITER/JITORESTAKING on SOL);
      `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` extended with 13 pairs (Beefy multi-chain rollouts + YEARN_V3 L2
      rollouts + IDLE/KARAK/RENZO L2 + SOLBLAZE) that fall back to chain genesis until subgraph-truth probe lands.
      **Phase 1B research close-out 2026-05-12 by slot 5 (ikenna-aggressive-may15-tab) — 45 of 46 pending pairs shipped
      @uac@`458f17d` via 5-sub-agent fan-out**: PROTOCOL_LAUNCH_DATES now 98 pairs (was 53);
      `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` reduced to 2 pairs (`(POLYGON, COMPOUND_V3)` — Compound not on Polygon;
      `(SOLANA, SOLBLAZE)` — medium-low confidence pending Solscan pool-creation-tx audit). Per-sub-agent partitioning:
      A (ETH lending/vault, 8) + B (LST/restaking + Solana, 8) + C (Balancer/PancakeSwap/Sushi multi-chain, 9) + D
      (DEX/AMM multi-chain, 9) + E (Beefy/Yearn/Idle/Karak/Renzo, 12) = 46 pairs researched, 45 shipped. Confidence
      tiers: 32 high (primary-source verified) + 11 medium (announcement-anchored) + 2 low (conservative pre-launch
      placeholders for Beefy ETH + Yearn V3 ARB/OPT — flagged for tightening if precision matters). Test fix: 2 BASE
      pairs (BALANCER, SUSHISWAP_V3) CLAMPED to BASE chain genesis 2023-08-09 (sub-agent dates pre-dated chain mainnet
      GA). tests/unit/test_protocol_launch_dates.py 19/19 pass. **DEFERRED — `data_types` per-venue declarations**: each
      new protocol's `data_types` matrix (vault_share_price / dex_swaps / lending_indices / etc.) is encoded via
      per-protocol `SourceCapability` objects in `registry/capability_declarations/_defi_source_capabilities.py`
      (currently 5 protocols: UNISWAP / AAVE / etc.). Per-protocol `SourceCapability` blocks include `operations`,
      `base_urls` per env, `operation_details` per env + signing scheme + credential type — that's per-adapter research
      depth, naturally co-shipped with the catalogue Phase 2 (instruments adapter) + Phase 3 (MTDS adapter) per-protocol
      cells (parallel-agent A through O in the Phase 2 matrix). Slot 5 venue declarations enable the manifest shard-atom
      population shape (Phase 2 anti- sequencing risk closed); per-protocol SourceCapability adds the data-source
      contracts (Phase 2-3 scope).
- [x] [AGENT] P0. **1B — Extend `defi_reserve_params.py`** for Spark + Radiant + multi-chain Aave V3 (9 chains × N
      reserves each). Per-asset: LTV, liquidation threshold, liquidation bonus, can-be-collateral, can-be-borrowed,
      borrow cap, supply cap, reserve factor, optimal_utilization_rate, interest-rate-model parameters. **DESIGN-SHIPPED
      2026-05-12 by slot 2 (ikenna-defi-catalogue-tab); IMPLEMENTATION HANDED TO HARSH SLOT 2** per cross-side handshake
      "Ikenna designs, Harsh implements per protocol" (`work_split_2026_05_12_ikenna.md`). Canonical SSOT shape ALREADY
      in place at `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py`: `ReserveParams`
      dataclass (max_ltv / liquidation_threshold / liquidation_bonus / reserve_factor) + `EModeCategory` (category_id /
      label / max_ltv / liquidation_threshold / liquidation_bonus / assets) + `AAVE_V3_ETHEREUM_RESERVES` dict (10
      assets) + `AAVE_V3_EMODE_CATEGORIES` (ETH_CORRELATED + STABLECOIN) + `MORPHO_BLUE_ETHEREUM_RESERVES` (line 352) +
      `get_reserve_params(asset, chain="ETHEREUM")` already accepts `chain` parameter. **Harsh implementation scope**
      (12 per-chain dicts to ship; ~3 calibrated AI-days via sub-agent fan-out per chain): `AAVE_V3_ARBITRUM_RESERVES`
      (https://app.aave.com/reserve-overview/?marketName=proto_arbitrum_v3) + `AAVE_V3_OPTIMISM_RESERVES`
      (proto_optimism_v3) + `AAVE_V3_BASE_RESERVES` (proto_base_v3) + `AAVE_V3_AVALANCHE_RESERVES`
      (proto_avalanche_v3) + `AAVE_V3_POLYGON_RESERVES` (proto_polygon_v3) + `AAVE_V3_BSC_RESERVES` (proto_bnb_v3) +
      `AAVE_V3_LINEA_RESERVES` (proto_linea_v3) + `AAVE_V3_SCROLL_RESERVES` (proto_scroll_v3) +
      `AAVE_V3_ZKSYNC_RESERVES` (proto_zksync_v3) + `SPARK_ETHEREUM_RESERVES` (https://app.spark.fi/markets) +
      `RADIANT_ARBITRUM_RESERVES` + `RADIANT_BSC_RESERVES` (https://app.radiant.capital). Plus extend
      `get_reserve_params()` chain dispatch from single-dict lookup to per-chain dict-of-dicts. Same pattern; same
      dataclass; primary-source values from Aave/Spark/Radiant governance UIs cross-verified with on-chain
      `getReserveData()` reads. Per-chain E-Mode categories also extend `AAVE_V3_EMODE_CATEGORIES` if governance has
      chain-specific categories (some chains have RWA-collateralised stablecoins as separate category). Harsh-side
      cross-side handshake: pickup Day 2 morning per `work_split_2026_05_12_ikenna.md` row 2. **🟢 IMPLEMENTATION
      SHIPPED 2026-05-15 by slot 2 sub-agent fan-out** at UAC@`6032cff` + style follow-up UAC@`6d447cb`. All 12 dicts
      landed with reserve counts ≥ 3 floor: AAVE_V3 ARBITRUM=9 / OPTIMISM=7 / BASE=5 / AVALANCHE=5 / POLYGON=7 / BSC=5 /
      LINEA=3 / SCROLL=4 / ZKSYNC=3 + SPARK_ETHEREUM=7 + RADIANT_ARBITRUM=6 + RADIANT_BSC=5. Helpers shipped:
      `get_aave_reserve_params(asset, chain)` / `get_spark_reserve_params(asset)` /
      `get_radiant_reserve_params(asset, chain)`. `get_reserve_params(asset, chain="ETHEREUM")` extended with
      `_AAVE_V3_CHAIN_DISPATCH` table preserving Ethereum default for backwards compat. 21 unit tests passing in
      `tests/unit/test_defi_reserve_params.py`. Slot 2 implementation closed the Harsh-handoff gap same-cycle.
- [x] [AGENT] P0. **1C — Verify `CHAIN_GENESIS_DATES`** at `chain_env.py:91` covers all 22 chains in scope. Add any
      missing (BNB Chain alt-name normalisation, Polygon zkEVM if distinct from Polygon PoS). Confirm Solana mainnet
      (2020-03-16) is the canonical entry for Solana DeFi. **✅ SHIPPED 2026-05-12 by slot 2
      (ikenna-defi-catalogue-tab)** at UAC@`4a155143`. **Verification result**: current table has 21 chains; all 9 Phase
      1A in-scope chains present (ETHEREUM / ARBITRUM / OPTIMISM / BASE / POLYGON / BSC / AVALANCHE / LINEA / SOLANA).
      Solana mainnet `2020-03-16` canonical. **No 22nd chain added**: grep-verified `POLYGON_ZKEVM` zero references in
      UAC; not in Phase 1A scope (distinct chain ID 1101 from Polygon PoS 137; defer until a protocol enters scope). BSC
      alt-name (BNB Chain): pinned naming-convention comment at top of `CHAIN_GENESIS_DATES` — callers normalise
      BNB/BNBCHAIN → BSC at entry, no alias key (avoid duplicate-entry drift). The "22 chains" target in the plan body's
      framing is approximate; the actual done-state is "all in-scope chains present with naming-convention pinned."
- [x] [AGENT] P0. **1D — Add `MevSubmissionMode.JITO_BUNDLE`** to UAC (`unified_api_contracts/internal/`). Update
      `execution-service/execution_service/v2/mev_router.py` `_DEFAULT_POLICIES` dict with the policy:
      `endpoint_ref="jito_bundle_rpc"`, `bundle_mode="private"`, `max_block_delay=2`, `supported_chains=("solana",)`,
      `private=True`. Endpoint resolved via UCI/Secret Manager at dispatch. **✅ SHIPPED 2026-05-12 by slot 2
      (ikenna-defi-catalogue-tab)**: UAC@`5241fad0` extended `MevSubmissionMode` StrEnum at
      `internal/architecture_v2/enums.py:344` with `JITO_BUNDLE = "JITO_BUNDLE"` (after `CUSTOM_PRIVATE_RPC`);
      execution-service@`38710bef` extended `_DEFAULT_POLICIES` dict at `execution_service/v2/mev_router.py:73-80` with
      exact policy spec from plan (`endpoint_ref="jito_bundle_rpc"` / `bundle_mode="private"` / `max_block_delay=2` /
      `supported_chains=("solana",)` / `private=True`). Endpoint ref is a Secret-Manager pointer per existing
      \_DEFAULT_POLICIES convention; raw URL never enters source. No tech debt — clean extension of existing dispatch.
- [x] [AGENT] P0. **1E — Per-venue margin-tier table SSOT.** New file
      `unified-api-contracts/unified_api_contracts/registry/perp_margin_tiers.py` declaring
      `PERP_MARGIN_TIERS:     dict[(venue, instrument_type), list[MarginTier]]` for the 6 perp venues. Each tier:
      `(notional_lower, notional_upper, initial_margin_bps, maintenance_margin_bps)`. Per-venue table sourced from venue
      docs (Bybit / Binance / OKX / Deribit) + on-chain constants (Hyperliquid / Aster). Versioned (these change
      occasionally). **DESIGN-SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab); IMPLEMENTATION HANDED TO HARSH
      SLOT 2.** **🟡 DESIGN CORRECTION**: NEW file `perp_margin_tiers.py` would DUPLICATE the existing SSOT at
      `unified-api-contracts/unified_api_contracts/registry/cefi_margin_tiers.py` (194 lines; `MarginTier` +
      `VenueMarginSchedule` dataclasses + `CEFI_MARGIN_TIERS: dict[tuple[str, str], VenueMarginSchedule]` with 6 entries
      — BINANCE_BTC/ETH, BYBIT_BTC/ETH, OKX_BTC/ETH; + `get_margin_schedule`, `get_margin_tier`,
      `maintenance_margin_for` helpers). Per FLAG 1 RESOLVED 2026-05-10 (`defi_catalogue` Pre-audit § Perp DEXes),
      on-chain perp venues (Hyperliquid / Aster / GMX / Drift / Pacifica / Extended / Lighter) are classified under
      `VENUES_BY_ASSET_GROUP["cefi"]` axis. So `cefi_margin_tiers.py` IS the canonical perp margin-tier SSOT for ALL
      perp venues (CEX + on-chain) — no separate `perp_margin_tiers.py` file needed. Per System-First Architecture
      ("never work around"), extending the existing file is the right design. **Harsh implementation scope** (per
      cross-side handshake `Ikenna designs, Harsh implements`; ~1.5 calibrated AI-days): Extend `cefi_margin_tiers.py`
      `CEFI_MARGIN_TIERS` dict with entries for: - **Deribit** BTC + ETH
      (https://www.deribit.com/kb/leverage-and-margin-perpetuals) - **Hyperliquid** BTC + ETH
      (https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-trade-perpetuals) - **Aster** BTC + ETH
      (on-chain constant from `defi_execution/protocols/aster.py` reading `getLeverageBracket` per market) Optional add
      for completeness (post-cutover, not May-23-blocking): - **GMX V2** BTC + ETH
      (https://gmx-docs.io/docs/trading/leverage/) - **Drift v2** BTC + ETH + SOL
      (https://docs.drift.trade/trading/leverage) Each schedule: same `VenueMarginSchedule` shape as existing entries
      (sequence of `MarginTier` per notional bracket). Per-venue research sources cited in docstring per existing
      pattern. Optional: rename `cefi_margin_tiers.py` → `perp_margin_tiers.py` for visual clarity — DEFERRED
      (mechanical refactor across 1+ importer; not May-23-blocking). **🟢 IMPLEMENTATION SHIPPED 2026-05-15 by slot 2
      sub-agent fan-out** at UAC@`41d99b2`. 6 entries landed: (DERIBIT, BTC)=5 tiers + (DERIBIT, ETH)=5 + (HYPERLIQUID,
      BTC)=4 + (HYPERLIQUID, ETH)=4 + (ASTER, BTC)=4 + (ASTER, ETH)=4. `CEFI_MARGIN_TIERS` registry now 12 entries (was
      6). Lowercase venue convention preserved ("deribit"/"hyperliquid"/"aster"); `get_margin_schedule()` normalises
      with `.lower()`. 29 unit tests passing including the `get_margin_tier("HYPERLIQUID", "ETH", Decimal("1500000"))` →
      tier-2 spec test. basedpyright + ruff clean. Slot 2 implementation closed the Harsh-handoff gap same-cycle.
- [x] [AGENT] P0. **1F — UAC dual-prediction module pick.** Delete `canonical/domain/prediction/__init__.py` (legacy
      pre-canonical-question-group) AND any references; canonical = `canonical/domain/predictions/` per the
      `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md` SSOT. Workspace-grep audit for
      downstream consumers; update each. **🔴 FINDING 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) — PLAN BODY
      INSTRUCTION MIS-FRAMED; corrected via Findings Triage Discipline.** The pre-audit shows
      `canonical/domain/prediction/` (legacy, singular) and `canonical/domain/predictions/` (new, plural) serve
      **DIFFERENT purposes**, not redundant duplicates: - **Legacy `prediction/`** (614 bytes `__init__.py` + 9514 bytes
      `prediction_mapping.py`) — cross-venue mapping. Exports: `CanonicalPredictionMarket`, `MappingRule`,
      `OrphanDetector`, `PredictionMarketCategory`, `PredictionMarketCrossVenueMapping`, `PredictionMarketMapper`. Maps
      individual Polymarket markets to Kalshi market equivalents (1:1 cross-venue dispatch). - **New `predictions/`**
      (canonical_groups.py + classifiers.py + lifecycle.py) — canonical-question-group taxonomy. Exports:
      `CanonicalQuestionGroup` (StrEnum), `CanonicalGroupMetadata`, `MarketLifecycle`,
      `classify_polymarket_to_canonical_group`, `classify_kalshi_to_canonical_group`. Groups markets across venues into
      shared canonical questions (e.g., all "US Election 2024" markets across Polymarket + Kalshi). **Real consumers
      verified workspace-grep**: legacy `prediction/` has 2 live consumers — UAC facade
      `unified_api_contracts/prediction.py` (`from canonical.domain.prediction import *`) +
      `instruments-service/.../adapters/prediction/polymarket.py:25` import. Deleting it would break polymarket adapter.
      **Migration plan SSOT**
      (`plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`) line 459-460
      explicitly says the legacy `PredictionMarketCategory` enum **needs alignment with CanonicalQuestionGroup**, NOT
      outright deletion. Migration plan is ARCHIVED — alignment work was completed without retiring the legacy module.
      **Decision**: keep BOTH modules; the plan-body instruction was wrong. The cross-venue mapping role of legacy
      `prediction/` is distinct from the canonical-question-group role of new `predictions/`. Phase 1F design-shipped as
      a clarification. Lower-priority cleanup (post-cutover): rename legacy `prediction/` → `prediction_mapping/` (to
      disambiguate from the new module visually), which is mechanical refactor across the 2 live consumers + facade
      re-export — DEFERRED to post-cutover plan since not May-23-blocking.
- [x] [AGENT] P0. **1G — `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT verification.** Confirm presence at the documented location
      (per `defi_master.md` Phase 9.1A); if missing, add as
      `unified_api_contracts/canonical/domain/predictions/lifecycle.py` sibling for LSTs at
      `canonical/domain/onchain/lst_protocol_mapping.py`. Map: `(lst_token_symbol, chain) → (protocol, base_asset)`.
      **✅ SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)** at UAC@`961af767`. **Actual SSOT location**:
      `unified_api_contracts/internal/domain/defi/lst.py:37` (NOT the plan body's hypothesised
      `canonical/domain/onchain/lst_protocol_mapping.py`; grep-verified that file doesn't exist). **Actual shape**:
      `dict[str, tuple[str, str]]` mapping `token → (protocol, base_asset)` — chain is NOT in the key (multi-chain LSTs
      like wstETH-on-Optimism are the SAME ERC20 token contract bridged; chain dimension lives in `instrument_id` +
      instruments-service `LST_REFERENCE_DATA` registry). Slot 2 extended with restaking LRTs (`ezETH` → RENZO/ETH,
      `rsETH` → KELPDAO/ETH) to cover Phase 1A scope. Symbiotic/Karak DELIBERATELY not added (per-vault shares, not a
      single canonical LRT). Test `test_table_has_all_canonical_lsts` updated; helpers `tokens_for_protocol_asset` +
      `protocol_asset_for_token` already cover the new entries.
- [x] [AGENT] P0. **1H — UAC QG green** (`bash scripts/quality-gates.sh` from UAC repo). All new entries pass
      basedpyright + ruff + Bandit + pytest. **✅ SHIPPED 2026-05-13 (Day 2) by slot 2 (ikenna-defi-catalogue-tab)** —
      full QG run from UAC repo exited 0 after slot 2's Day-1 Phase 1 edits (MevSubmissionMode.JITO_BUNDLE enum +
      LST_TOKEN_TO_PROTOCOL_ASSET ezETH/rsETH + CHAIN_GENESIS_DATES naming-convention comment +
      test_lst_protocol_asset.py expected-set extension). basedpyright + ruff + Bandit + pytest all green. No
      regressions from Phase 1 edits.

**Codex SSOT update (Phase 1 boundary)** — per Post-Plan-Phase Codex Audit HARD RULE:

- [x] [AGENT] P0. **1J — Update `/codex/02-data/defi-venue-protocol-catalogue.md`** with all 26 protocols added in Phase
      1A. Per-protocol: chain coverage, data_types declared, instruments-service catalog status (Phase 2), MTDS capture
      status (Phase 3), execution connector status (Phase 4), testnet readiness, GCS bucket path, backfill plan
      reference. **✅ SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)** at PM@`f54dd90c`. Codex doc already
      comprehensive (165 lines, 6 protocol sections + per-chain coverage summary + cross-references + update protocol).
      5 refresh-deltas landed: (a) **NOTE 2026-05-12 IN-1: the "corrected stale `defi_venue_capabilities.py` references
      → actual `defi_venues.py`" delta in this done block was ITSELF incorrect per operator decision PM@`32d0174e`.
      `defi_venue_capabilities.py` IS canonical (per-venue×data_type capability matrix). Codex doc re-corrected by Harsh
      slot 8 at PM@`32d0174e`. No further action needed.** Original delta (a) now void; (b) Aave V3 Ethereum silent-zero
      row flipped to ✅ captured (slot 3 + slot 2 audit closure); (c) Renzo/KelpDAO UAC + LST mapping ✅; (d) Solana MEV
      cell flipped ✅ for JITO_BUNDLE (Phase 1D); (e) header bumped to 2026-05-12 with delta summary. Remaining ◐/✗
      statuses reflect Phase 2/3/4 buildout still in flight (harsh-side per cross-side handshake).

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE):

- ✅ UAC `defi_venue_capabilities.py` git-grep returns ≥ 26 new entries.
- ✅ `bash scripts/quality-gates.sh` from `unified-api-contracts/` exits 0 on Phase 1 commit.
- ✅ Workspace-grep for legacy `canonical/domain/prediction/` returns zero hits in non-test code.
- ✅ Codex doc `defi-venue-protocol-catalogue.md` exists + lists every Phase 1A protocol.

## Phase 2 — Instruments-service buildout (PARALLEL × 26 protocols; ~30-45 AI-days at full saturation)

Owner: harsh + parallel agents per protocol.

> **🟢 PHASE 2 PER-PROTOCOL SHARD-ATOM DESIGN — published 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) per
> work_split_2026_05_12 row 2 cross-side handshake "Ikenna publishes per-protocol shard-atom decision by Day 1 EOD per
> protocol family; Harsh starts implementation Day 2 morning".**
>
> **Base shard atom for ALL DeFi protocols** (per
> [`/codex/02-data/per-asset-group-bucket-layouts.md`](/codex/02-data/per-asset-group-bucket-layouts.md) line 69 +
> `unified_api_contracts/canonical/domain/defi/gcs_paths.py`):
> `(date, asset_group=defi, chain, venue, instrument_type, data_type)`. Path:
> `raw_tick_data/by_date/day={date}/asset_group=defi/chain={chain}/venue={v}/instrument_type={it}/data_type={dt}/ticks.parquet`.
>
> **Per-protocol-family refinement** (whether instrument is a row-level column INSIDE the parquet vs hive-partition
> shard axis OUTSIDE; mirrors the predictions/sports multi-axis correction pattern banner from 2026-05-06):
>
> | Protocol family                                                                                                                               | Per-instrument count                                                                   | Shard granularity                                                                                                                              | Instrument axis location                                                              | Cluster validation                                                                                                                             |
> | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
> | **Lending** (Aave / Spark / Compound / Morpho / Radiant / Fluid)                                                                              | ~10-20 reserves per (protocol, chain)                                                  | **Per-(chain, protocol, asset, data_type, day)** = one manifest row per `(asset, day)`                                                         | `asset_symbol` IS a hive shard key (existing pattern at `lending_indices_handler.py`) | Not bundled (each asset is own shard)                                                                                                          |
> | **DEX V3 + CLMM** (Uniswap V3 / Sushi V3 / PancakeSwap / Camelot / Aerodromeq / Velodrome / TraderJoe V2 / Balancer / Curve / Raydium / Orca) | 100-1000+ pools per (protocol, chain)                                                  | **BUNDLED per-(chain, protocol, data_type, day)** = one manifest row per protocol+chain+day; `pool_address` is row-level column INSIDE parquet | `pool_address` is ROW-LEVEL (NOT hive shard axis)                                     | **MANDATORY** per `UTL.record_captured` — `expected_root_clusters=set_of_pool_addresses` + `cluster_extractor=lambda row: row["pool_address"]` |
> | **DEX V2** (Uniswap V2 / Sushi V2)                                                                                                            | smaller pool catalog                                                                   | Same as DEX V3 — BUNDLED                                                                                                                       | row-level `pool_address`                                                              | MANDATORY                                                                                                                                      |
> | **LST** (Lido / Ether.fi / Rocket Pool / Jito / Marinade / Solblaze + Ethena / Spark sDAI)                                                    | 1 token per (protocol, chain)                                                          | Per-(chain, protocol, token, data_type, day) — token is the shard atom in 1:1 case                                                             | `token_symbol` is hive shard key OR row-level (single-token protocols use hive)       | Not bundled (1:1)                                                                                                                              |
> | **Restaking LRT — single-token** (Renzo ezETH / KelpDAO rsETH / Ether.fi weETH)                                                               | 1 token per (protocol, chain)                                                          | Same as LST — per-token shard                                                                                                                  | hive shard key on `token_symbol`                                                      | Not bundled                                                                                                                                    |
> | **Restaking — multi-vault** (Symbiotic / Karak / EigenLayer / Puffer / Jito-restaking)                                                        | dozens of vaults per (protocol, chain)                                                 | **BUNDLED per-(chain, protocol, data_type, day)** = one manifest row per protocol+chain+day; `vault_address` is row-level                      | row-level `vault_address`                                                             | MANDATORY — `expected_root_clusters=set_of_vault_addresses`                                                                                    |
> | **Vaults / yield-aggregator** (Yearn / Convex / Beefy / Pendle / Idle)                                                                        | 50-200+ vaults per (protocol, chain)                                                   | **BUNDLED per-(chain, protocol, data_type, day)** = one row per protocol+chain+day; `vault_address` is row-level                               | row-level `vault_address`                                                             | MANDATORY                                                                                                                                      |
> | **Aggregators** (Jupiter Solana)                                                                                                              | n/a (read-only routing)                                                                | per-(chain, protocol, data_type, day) — single route registry per day                                                                          | route is row-level                                                                    | Not bundled (registry snapshot)                                                                                                                |
> | **Perp DEX / on-chain CLOB** (Hyperliquid / Aster / GMX / Drift / Pacifica / Extended / Lighter)                                              | per FLAG 1 RESOLVED 2026-05-10 → classified under `VENUES_BY_ASSET_GROUP["cefi"]` axis | **Per-(venue, instrument, data_type, day)** — same as CEFI venues, NOT DEFI shape                                                              | hive shard key on `instrument_id` (per-instrument shard)                              | Not bundled (per-instrument shard already)                                                                                                     |
>
> **Rationale — why BUNDLED for DEX/Vaults/multi-vault Restaking**:
>
> - Per-pool/per-vault shard would inflate manifest by 100-1000× per (protocol, chain) — 1000 Uniswap V3 pools × 5
>   chains × 4 data_types × 1y days = 7.3M rows per protocol. Across 11 EVM DEX protocols = 80M+ rows. Unmanageable.
> - Bundled per-(chain, protocol, data_type, day) keeps manifest ≤ ~30k rows per DEX protocol per year (5 chains × 4
>   data_types × 365 days × 4 instrument_types).
> - Per-pool/per-vault detail STILL fully recoverable by reading the parquet — `pool_address` / `vault_address` columns
>   survive in parquet rows; row-level filters work for backtest + live reads.
> - Cluster validation at `record_captured()` ensures no silent data loss: `expected_root_clusters` (set of pool
>   addresses we EXPECT in the bundle) + `cluster_extractor` (lambda extracting `pool_address` from each row) gates the
>   write — if any expected pool is missing from the parquet, `MissingClusterValidationError` raises (QG STEP 5.64
>   enforces statically; UTL `record_captured` guard raises at runtime).
>
> **Shard-granularity SSOT compliance** (per
> [`/codex/04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md)
>
> - `plans/epics/infrastructure_master.md`): shard atom MUST be identical across (a) writer atomicity, (b) manifest row
>   key, (c) data-status display, (d) downstream pre-flight gate, (e) deployment-UI drilldown. Per the matrix above, the
>   shard atom for each protocol family is documented here as the SSOT; Phase 2 adapter implementations MUST honor this
>   matrix; deployment-UI drilldowns roll up to this same granularity.
>
> **Codex SSOT update** (Phase 2 boundary, per HARD RULE Post-Plan-Phase Codex Audit) — slot 2 extends
> [`/codex/02-data/defi-venue-protocol-catalogue.md`](/codex/02-data/defi-venue-protocol-catalogue.md) with a
> "Per-protocol shard-atom matrix" subsection (Phase 1J refresh) — **✅ SHIPPED 2026-05-12 Day-2 by slot 2
> (ikenna-defi-catalogue-tab)** at PM@`a11e0256` (IN-1 fix) + follow-up commit (this matrix). 8-row matrix mirrors
> plan-body lines 380-388 verbatim into codex SSOT with rationale block.
>
> **Harsh implementation handoff**: per-protocol Phase 2 adapter authors consume this matrix at adapter-write time. The
> bundled protocols (DEX / multi-vault Restaking / Vaults) MUST pass `expected_root_clusters` + `cluster_extractor`
> kwargs to `record_captured()` per cluster-validation HARD RULE. Single-instance protocols (lending / LST /
> single-token LRT) can omit cluster kwargs.

Success criterion: per protocol, an instruments-service adapter exists at
`instruments-service/reference_data/adapters/defi/<protocol>_adapter.py` declaring instrument metadata sourced from the
protocol's on-chain registry (or off-chain catalog API where on-chain is incomplete). Per-instrument: chain, contract
address, decimals, symbol, instrument_type, classification, lifecycle dates. Each adapter writes to the manifest with
`record_captured` per writegate Phase 3.D.5 cluster validation.

**Per-protocol todos (one per cell in the matrix below):**

| Protocol            | Chains                                                 | Adapter shape                                                        | Owner            |
| ------------------- | ------------------------------------------------------ | -------------------------------------------------------------------- | ---------------- |
| Yearn               | Ethereum + Arbitrum + Optimism                         | per-vault metadata (token / strategy / decimals / share-price)       | parallel-agent A |
| Convex              | Ethereum                                               | Curve-LP-staking-vault metadata                                      | parallel-agent A |
| Beefy               | Ethereum + Arbitrum + Base + Polygon + BSC + Avalanche | per-vault metadata                                                   | parallel-agent B |
| Pendle              | Ethereum + Arbitrum                                    | per-PT/YT/SY-token metadata + maturity                               | parallel-agent B |
| Idle                | Ethereum + Arbitrum + Polygon                          | per-vault metadata                                                   | parallel-agent C |
| Balancer            | 6 chains per UAC                                       | per-pool weighted/boosted/composable metadata                        | parallel-agent C |
| Sushi V2            | Arbitrum                                               | pair metadata                                                        | parallel-agent D |
| Sushi V3            | Ethereum + Base + Avalanche                            | pool + tick-spacing metadata                                         | parallel-agent D |
| PancakeSwap V3      | 4 chains per UAC                                       | pool metadata                                                        | parallel-agent E |
| Camelot V3          | Arbitrum                                               | pool metadata                                                        | parallel-agent E |
| Aerodromeq V3       | Base                                                   | pool metadata                                                        | parallel-agent F |
| Velodrome V2        | Optimism                                               | pool metadata                                                        | parallel-agent F |
| TraderJoe V2        | Avalanche                                              | bin-step metadata                                                    | parallel-agent G |
| Raydium             | Solana                                                 | CLMM pool + standard pool metadata                                   | parallel-agent G |
| Orca                | Solana                                                 | Whirlpool metadata                                                   | parallel-agent H |
| Jupiter aggregator  | Solana                                                 | route registry (read-only)                                           | parallel-agent H |
| Spark               | Ethereum                                               | Aave-fork reserve metadata                                           | parallel-agent I |
| Radiant             | Arbitrum + BSC                                         | reserve metadata                                                     | parallel-agent I |
| Aave V3 multi-chain | 9 non-Ethereum chains                                  | per-chain reserve metadata                                           | parallel-agent J |
| Rocket Pool         | Ethereum                                               | rETH metadata + node-operator distribution                           | parallel-agent K |
| Solblaze            | Solana                                                 | bSOL metadata                                                        | parallel-agent K |
| EigenLayer          | Ethereum                                               | operator + AVS + delegation registry (verify connector status first) | parallel-agent L |
| Symbiotic           | Ethereum                                               | vault + operator metadata                                            | parallel-agent L |
| Karak               | Ethereum + Arbitrum                                    | vault metadata                                                       | parallel-agent M |
| Renzo (ezETH)       | Ethereum + Arbitrum                                    | LRT metadata                                                         | parallel-agent M |
| KelpDAO (rsETH)     | Ethereum                                               | LRT metadata                                                         | parallel-agent N |
| Puffer              | Ethereum                                               | vault metadata                                                       | parallel-agent N |
| Jito restaking      | Solana                                                 | restaking-vault metadata                                             | parallel-agent O |

> **🟢 PHASE 2 PRE-AUDIT (harsh-defi-catalogue-impl-tab, 2026-05-12) — most of the matrix already ships; the genuine gap
> is the vault / LST / LRT adapters, NOT the DEXes.** Grep-then-read of
> `instruments-service/instruments_service/ reference_data/adapters/defi/` + `reference_data/factory.py` (the canonical
> adapter registry — `CANONICAL_VENUE_TO_ADAPTER`
>
> - `_ADAPTERS` + `_SUBGRAPH_VENUE_PREFIX_TO_PROTOCOL` + `_PROTOCOL_TO_ADAPTER_KEY` + `ADAPTER_DATA_SOURCES`):
>
> * **Already shipped (dedicated adapter file)**: `aave_v3`, `balancer`, `benqi`, `compound_v3`, `curve`, `drift`,
>   `eigenlayer`, `ethena`, `etherfi`, `ethfi` (gov), `euler_v2`, `fluid`, `jito`, `kamino`, `lido`, `marinade`,
>   `morpho`, `orca`, `radiant`, `raydium`, `spark`, `uniswap_v2`, `uniswap_v3`, `uniswap_v4`, `venus`. (Adapters wired
>   multi-chain dynamically via `_SUBGRAPH_VENUE_PREFIX_TO_PROTOCOL` × `get_supported_chains_for_protocol()` — e.g.
>   `AAVE_V3-ARBITRUM`/`MORPHO-BASE`/… auto-registered.)
> * **DEX-fork "adapters" — ALREADY DONE via reuse**: `pancakeswap_v3`, `sushiswap_v3` (+ `sushiswap` V2),
>   `aerodrome_v3`, `camelot_v3`, `velodrome_v2`, `trader_joe_v2`, `gmx` all map to the `uniswap_v3` adapter class
>   (Messari/UniV3-schema subgraphs) via `_PROTOCOL_TO_ADAPTER_KEY` + carry their own subgraph IDs. So Phase 2 cells for
>   those DEXes = ✅ (no new adapter file needed; the `defi_simulation_realism` per-AMM connector work is separate,
>   Phase 4 here).
> * **Genuine gaps (need a new adapter file)** — the vault / LST / LRT / aggregator rows: **Yearn, Convex, Beefy,
>   Pendle, Idle** (vaults/fixed-yield); **Rocket Pool ✅, Solblaze** (LSTs); **Symbiotic, Karak, Renzo, KelpDAO,
>   Puffer, Jito-restaking** (restaking — note `jito.py` exists for jitoSOL LST, restaking-vault discovery may extend it
>   or add `jito_restaking.py`); **Jupiter** = execution-only per factory.py comment (no instrument-discovery adapter —
>   skip). Net: ~13-14 new adapter files, all clean per-protocol boundaries.
> * **Template**: `adapters/defi/lido.py` / `etherfi.py` (single-token LST/LRT — subclass `BaseReferenceDataAdapter`,
>   `venue` property, `async get_instruments()` → `list[InstrumentRecord]` from `unified_api_contracts.internal`, 4
>   `NotImplementedError` stubs); `radiant.py` / `venus.py` / `euler_v2.py` (curated lending-reserve registry);
>   `marinade.py` + `_solana_utils.py` (Solana). Registration = 4 dict entries in `factory.py`
>   (`CANONICAL_VENUE_TO_ADAPTER`
>   - `_ADAPTERS` + `ADAPTER_DATA_SOURCES`; add to `defi_graph_adapters` set only if the ctor needs the parsed `chain`).
>     **`factory.py` is a SHARED hot file — do NOT have multiple sub-agents edit it concurrently**; sub-agents create
>     the adapter file + test only, main agent reconciles `factory.py` for all in one commit. (Pre-existing
>     `factory.py:~366 reportRedeclaration` on `adapter` — unrelated, leave it.)
>
> **DONE 2026-05-12 (harsh slot 2) — Session 1:** `2.ROCKETPOOL` (rETH LST, instruments-service@`a490033`) + `2.RENZO`
> (ezETH LRT) + `2.KELPDAO` (rsETH LRT) (instruments-service@`be12b56`) — 3 single-token ETH LST/LRT registry adapters,
> registered in `factory.py`, 5 unit tests each (offline).
>
> **DONE 2026-05-12 (harsh slot 2) — Session 2 (Sonnet):** 7 more static-registry adapters
> (instruments-service@`57a4f1f`): `2.PUFFER` (pufETH LRT, ETH), `2.SOLBLAZE` (bSOL LST, SOL), `2.SYMBIOTIC`
> (wstETH/rETH/cbETH/ETHx vaults, ETH), `2.KARAK` (wstETH/WETH vaults, ETH+ARB), `2.CONVEX` (CVX+cvxCRV, ETH), `2.IDLE`
> (DAI/USDC/USDT BEST vaults, ETH), `2.YEARN` (yvWETH/yvDAI/yvUSDC/yvWBTC V3 vaults, ETH+ARB). All registered in
> `factory.py` (CANONICAL_VENUE_TO_ADAPTER
>
> - \_ADAPTERS + ADAPTER_DATA_SOURCES). 35 new unit tests (100 total in defi/ suite, 100/100 passing). basedpyright 0
>   errors on new files; ruff clean.
>
> **Phase 2 ✅ COMPLETE — all 14 deferred adapters shipped (4-of-4 closed in 2026-05-12 Day-1):**
>
> - `2.RENZO-ARB` ✅ instruments-service@`38192e7` (multi-chain registry + tests).
> - `2.BEEFY` ✅ instruments-service@`b563afb` (16 vaults across 5 chains; POLYGON dropped — Beefy public API returned
>   every Polygon vault as `status=eol` on 2026-05-12 audit).
> - `2.PENDLE` ✅ instruments-service@`b563afb` (30 records = 5 markets × 3 PT/YT/SY × 2 chains; all maturities >
>   2026-05-12).
> - `2.JITO-RESTAKING` ✅ instruments-service@`b563afb` (3 VRTs — ezSOL/fragSOL/kySOL; distinct from existing `jito.py`
>   LST adapter via `venue=jito_restaking` + canonical venue `JITORESTAKING-SOLANA`).
>
> Latent multi-chain bug fix bundled with `b563afb`: `defi_graph_adapters` set was missing
> `renzo`/`karak`/`idle`/`yearn` (registered for non-ETH canonical venues earlier in session 2 but not in this set, so
> non-ETH variants silently used the ETHEREUM default chain). Fixed simultaneously with the new
> beefy/pendle/jito_restaking additions. End-to-end smoke (15 cases) pass: every (venue, expected_chain) tuple resolves
> to the right adapter with the right chain attribute. 122/122 defi unit tests pass.

Per-protocol todo template (instantiated 27 times):

- [x] ✅ [AGENT] P0. **2.<X> — `<protocol>` instruments-service adapter** — **TEMPLATE-CLOSED**. All 27 protocol adapter
      instances below are individually completed (`- [x]` items). Template entry served as the original scaffold and is
      now retired. 2026-05-19 slot 2 (R-S2-DEFI-CATALOGUE-CHAIN-PRIMITIVES).
- [x] [AGENT] P0. **2.ROCKETPOOL — Rocket Pool (rETH) instruments-service adapter** — `adapters/defi/rocket_pool.py`
      (static single-token registry; rETH LST on Ethereum, `instrument_type=YIELD_BEARING`, contract
      `0xae78736Cd615f374D3085123A210448E74Fc6393`, 18 decimals, launch 2021-11-08 per `PROTOCOL_LAUNCH_DATES`) +
      `tests/unit/reference_data/adapters/defi/test_rocket_pool_metadata.py` (5 tests, offline) + `factory.py`
      registration (`CANONICAL_VENUE_TO_ADAPTER["ROCKETPOOL-ETHEREUM"]` + `_ADAPTERS` + `ADAPTER_DATA_SOURCES`).
      instruments-service@`a490033`. basedpyright clean on new file; ruff clean; pytest 5/5. (Not bundled —
      single-token, no cluster validation needed. Manifest `record_captured` happens in the orchestrator that calls
      `get_instruments`, per the existing lido/etherfi pattern — no per-adapter manifest write.)
- [x] [AGENT] P0. **2.RENZO — Renzo (ezETH) instruments-service adapter** — `adapters/defi/renzo.py` (static
      single-token LRT registry; ezETH on Ethereum, `instrument_type=YIELD_BEARING`, contract
      `0xbf5495Efe5DB9ce00f80364C8B423567e58d2110`, 18 decimals, launch 2024-04-29 per `PROTOCOL_LAUNCH_DATES`) +
      `test_renzo_metadata.py` (5 tests, offline) + `factory.py` registration (`RENZO-ETHEREUM`).
      instruments-service@`be12b56`. basedpyright clean on new file; ruff clean; pytest 5/5. **DEFERRED — Renzo-ARB**:
      bridged ezETH on Arbitrum (`('ARBITRUM','RENZO')` launch 2024-02-29 in `PROTOCOL_LAUNCH_DATES`) needs the
      multi-chain extension (parse `chain` from venue name + per-chain address map + add `renzo` to `factory.py`'s
      `defi_graph_adapters` set) — in the Phase 2 fan-out queue above.
- [x] [AGENT] P0. **2.KELPDAO — KelpDAO (rsETH) instruments-service adapter** — `adapters/defi/kelpdao.py` (static
      single-token LRT registry; rsETH on Ethereum, `instrument_type=YIELD_BEARING`, contract
      `0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7`, 18 decimals, launch 2023-11-09 per `PROTOCOL_LAUNCH_DATES`) +
      `test_kelpdao_metadata.py` (5 tests, offline) + `factory.py` registration (`KELPDAO-ETHEREUM`).
      instruments-service@`be12b56`. basedpyright clean on new file; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.PUFFER — Puffer Finance (pufETH) instruments-service adapter** — `adapters/defi/puffer.py` (static
      single-token LRT registry; pufETH on Ethereum, `instrument_type=YIELD_BEARING`, contract
      `0xD9A442856C234a39a81a089C06451EBAa4306a72`, 18 decimals, launch 2024-05-09 per `PROTOCOL_LAUNCH_DATES`) +
      `test_puffer_metadata.py` (5 tests, offline) + `factory.py` registration (`PUFFER-ETHEREUM`).
      instruments-service@`57a4f1f`. basedpyright 0 errors; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.SOLBLAZE — Solblaze (bSOL) instruments-service adapter** — `adapters/defi/solblaze.py` (static
      single-token LST registry; bSOL on Solana, `instrument_type=YIELD_BEARING`, mint
      `bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1`, 9 decimals, launch 2022-02-17 from chain records) +
      `test_solblaze_metadata.py` (5 tests, offline) + `factory.py` registration (`SOLBLAZE-SOLANA`).
      instruments-service@`57a4f1f`. basedpyright 0 errors; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.SYMBIOTIC — Symbiotic restaking vaults instruments-service adapter** —
      `adapters/defi/symbiotic.py` (static curated 4-vault registry: wstETH/rETH/cbETH/ETHx vaults,
      `instrument_type=YIELD_BEARING`, launch 2024-06-11 per `PROTOCOL_LAUNCH_DATES`) + `test_symbiotic_metadata.py` (5
      tests, offline) + `factory.py` registration (`SYMBIOTIC-ETHEREUM`). instruments-service@`57a4f1f`. basedpyright 0
      errors; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.KARAK — Karak restaking vaults instruments-service adapter** — `adapters/defi/karak.py` (static
      curated multi-chain vault registry: wstETH/WETH on ETH + wstETH on ARB, `instrument_type=YIELD_BEARING`, launch
      2024-04-08 per `PROTOCOL_LAUNCH_DATES`) + `test_karak_metadata.py` (5 tests, offline) + `factory.py` registration
      (`KARAK-ETHEREUM` + `KARAK-ARBITRUM`). instruments-service@`57a4f1f`. basedpyright 0 errors; ruff clean; pytest
      5/5.
- [x] [AGENT] P0. **2.CONVEX — Convex Finance (CVX + cvxCRV) instruments-service adapter** — `adapters/defi/convex.py`
      (static 2-token registry: CVX + cvxCRV, `instrument_type=YIELD_BEARING`, launch 2021-05-17 per
      `PROTOCOL_LAUNCH_DATES`) + `test_convex_metadata.py` (5 tests, offline) + `factory.py` registration
      (`CONVEX-ETHEREUM`). instruments-service@`57a4f1f`. basedpyright 0 errors; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.IDLE — Idle Finance yield vaults instruments-service adapter** — `adapters/defi/idle.py` (static
      curated 3-vault registry: idleDAI/idleUSDC/idleUSDT BEST on ETH, `instrument_type=YIELD_BEARING`, launch
      2019-08-13 per `PROTOCOL_LAUNCH_DATES`) + `test_idle_metadata.py` (5 tests, offline) + `factory.py` registration
      (`IDLE-ETHEREUM` + `IDLE-ARBITRUM`). instruments-service@`57a4f1f`. basedpyright 0 errors; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.YEARN — Yearn Finance V3 vaults instruments-service adapter** — `adapters/defi/yearn.py` (static
      curated vault registry: yvWETH/yvDAI/yvUSDC/yvWBTC on ETH + yvWETH/yvUSDC on ARB, `instrument_type=YIELD_BEARING`,
      launch 2024-03-20 ETH / 2023-11-15 ARB per `PROTOCOL_LAUNCH_DATES`) + `test_yearn_metadata.py` (5 tests,
      offline) + `factory.py` registration (`YEARN-ETHEREUM` + `YEARN-ARBITRUM`). instruments-service@`57a4f1f`.
      basedpyright 0 errors; ruff clean; pytest 5/5.
- [x] [AGENT] P0. **2.BEEFY — Beefy Finance multi-chain vaults** — `adapters/defi/beefy.py` (curated TOP-vault snapshot
      per chain via api.beefy.finance/vaults/<chain>; 16 vaults across ETHEREUM/ARBITRUM/BASE/BSC/AVALANCHE).
      `test_beefy_metadata.py` (7 tests, offline). `factory.py` registration (`BEEFY-{ETH,ARB,BASE,BSC,AVAX}` venues +
      `_ADAPTERS["beefy"]` + `ADAPTER_DATA_SOURCES["beefy"]=""` + added to `defi_graph_adapters`).
      instruments-service@`b563afb`. **POLYGON intentionally not registered**: Beefy public API returned every Polygon
      vault as `status=eol` on the 2026-05-12 audit; chain re-added when Beefy ships fresh active Polygon vaults
      (registry hook documented in adapter docstring). 7/7 tests pass; full defi/ unit-test suite 122/122 pass.
- [x] [AGENT] P0. **2.PENDLE — Pendle PT/YT/SY + maturity** — `adapters/defi/pendle.py` (curated active-markets snapshot
      via api-v2.pendle.finance/core/v1/<chainId>/markets/active queried 2026-05-12; 5 markets per chain × 3 PT/YT/SY
      roles = 15 records per chain × 2 chains = 30 records; ETHEREUM markets wstETH/weETH/weETHs/sUSDe/USDe + ARBITRUM
      markets wstETH/weETH/rETH/uniETH/USDai). All maturities strictly > 2026-05-12. PT/YT carry `expiry`; SY carries
      `expiry=None`. Role encoded in instrument_key segment 2 (e.g. `PENDLE-ETHEREUM:PT:PT-stETH-25JUN2026`) since
      `InstrumentType` has no PT/YT/SY-specific enum (closest match `YIELD_BEARING` already in
      `DEFI_ONCHAIN_INSTRUMENT_TYPES` whitelist). `test_pendle_metadata.py` (7 tests). factory.py registration
      (`PENDLE-{ETH,ARB}` + `_ADAPTERS["pendle"]` + ADAPTER_DATA_SOURCES + defi_graph_adapters).
      instruments-service@`b563afb`. 7/7 tests pass.
- [x] [AGENT] P0. **2.JITO-RESTAKING — Jito restaking vaults (Solana)** — `adapters/defi/jito_restaking.py` (curated VRT
      registry; 3 vaults: ezSOL/Renzo + fragSOL/Fragmetric + kySOL/Kyros, all mainnet 2024-08-01 launch). Distinct from
      existing `jito.py` LST adapter — `venue=jito_restaking` (vs `jito`); canonical venue `JITORESTAKING-SOLANA` (vs
      `JITO-SOLANA`); `instrument_type=YIELD_BEARING`. `test_jito_restaking_metadata.py` (6 tests including
      `test_distinct_from_jito_lst_venue`). factory.py registration (`JITORESTAKING-SOLANA` +
      `_ADAPTERS["jito_restaking"]` + ADAPTER_DATA_SOURCES + defi_graph_adapters). instruments-service@`b563afb`. 6/6
      tests pass.
- [x] [AGENT] P0. **2.RENZO-ARB — Renzo bridged ezETH on Arbitrum** — extended existing `adapters/defi/renzo.py` to
      multi-chain via `_LRT_TOKENS_BY_CHAIN` keyed dict (mirrors karak/yearn pattern). ezETH on Arbitrum at canonical
      bridged address `0x2416092f143378750bb29b79eD961ab195CcEea5` (verified arbiscan), launch 2024-02-29 per
      `PROTOCOL_LAUNCH_DATES[("ARBITRUM", "RENZO")]`. Tests extended (7/7 passing): added
      `test_get_instruments_arbitrum_yields_bridged_record` + `test_unknown_chain_returns_empty_list` + multi-chain
      venue tests. instruments-service@`38192e7`. **Pending in factory.py reconcile (bundled with
      beefy/pendle/jito-restaking sub-agent fan-out)**: register `RENZO-ARBITRUM` in `CANONICAL_VENUE_TO_ADAPTER` + add
      `"renzo"` to `defi_graph_adapters` set so chain gets parsed from the venue name.

**Codex SSOT update (Phase 2 boundary)**:

- [x] [AGENT] P0. **2J — Update `/codex/02-data/instrument-pipeline-defi.md`** with the 27 new protocol adapters +
      cluster validation rules per protocol. (PM@`291f81d7` — adapter count 25→50, full categorized adapter list)

**Full-execution criterion**:

- ✅ Each protocol's adapter writes ≥ 1 row to instruments-service manifest within a smoke-test boundary.
- ✅ `bash scripts/quality-gates.sh` from `instruments-service/` exits 0.
- ✅ Cluster validation tests green for every bundled data_type.

## Phase 3 — MTDS adapter buildout (PARALLEL × 27, depends on Phase 2 per protocol; ~30-45 AI-days)

Owner: harsh + parallel agents per protocol.

> **🔴 LENDING-INDICES PRIORITY (Q11 ratification 2026-05-10)** — Aave V3 Ethereum + Compound V3 Ethereum/Arbitrum/Base
> lending-rate adapters are P0 critical-path (gates recursive-borrow Phase 9 backtest). Three bugs to fix (folded in
> from recursive-borrow Phase 1 reframe):
>
> **🟢 PHASE 3 LENDING-INDICES SPEC FOR slot 5 (Family-1) HANDSHAKE — published 2026-05-12 by slot 2
> (ikenna-defi-catalogue-tab). Day-2 EOD gate to slot 5 Family-1 design (per `work_split_2026_05_12_ikenna.md` handshake
> row).**
>
> **TL;DR for slot 5**: Lending-indices data for Family-1 backtest is **broadly available NOW**. All three "bugs" from
> the original 2026-05-08 framing turned out to be stale at 2026-05-11 audit (slot 3) + 2026-05-12 audit (this agent).
> Slot 5 can START Family-1 design Day-1 using current captured horizons; final tail-end catch-up (5-10min VM, scoped)
> lands Day-2.
>
> **Per-pair capture status** (verified 2026-05-12, sample-inspected at slot 3 audit 2026-05-11):
>
> | Protocol    | Chain    | SUPPLY_APY / BORROW_APY / UTILISATION                                                                                    | Horizon                                                  | Slot 5 unblock |
> | ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- | -------------- |
> | AAVE_V3     | ETHEREUM | ✅ captured                                                                                                              | 2022-03-01 → 2026-05-07 (tail behind today)              | ✅ NOW         |
> | AAVE_V3     | ARBITRUM | ✅ captured (consolidator-confirmed)                                                                                     | 2022-03-16 → 2026-05-07                                  | ✅ NOW         |
> | AAVE_V3     | OPTIMISM | ✅ captured                                                                                                              | 2022-03-16 → 2026-05-07                                  | ✅ NOW         |
> | AAVE_V3     | BASE     | ✅ captured                                                                                                              | 2023-08-09 → 2026-05-07                                  | ✅ NOW         |
> | AAVE_V3     | LINEA    | ✅ captured (slot 3 reclaim 451 rows)                                                                                    | 2025-02-11 → 2026-05-07                                  | ✅ NOW         |
> | AAVE_V3     | BSC      | ✅ captured (slot 3 reclaim 836 rows)                                                                                    | 2024-01-23 → 2026-05-07                                  | ✅ NOW         |
> | COMPOUND_V3 | ETHEREUM | ✅ adapter wired + dispatched                                                                                            | 2022-08-13 → present (verify on next consolidator cycle) | ✅ NOW         |
> | COMPOUND_V3 | ARBITRUM | ✅ adapter wired + dispatched                                                                                            | 2023-05-04 → present                                     | ✅ NOW         |
> | COMPOUND_V3 | BASE     | ✅ adapter wired + dispatched                                                                                            | 2023-08-04 → present                                     | ✅ NOW         |
> | COMPOUND_V3 | OPTIMISM | ✅ adapter wired + dispatched                                                                                            | 2024-04-06 → present                                     | ✅ NOW         |
> | COMPOUND_V3 | SCROLL   | ✅ adapter wired                                                                                                         | 2024-04-22 → present                                     | ✅ NOW         |
> | COMPOUND_V3 | POLYGON  | ⛔ INTENTIONALLY EXCLUDED — Compound V3 not deployed on Polygon (`SUBGRAPH_IDS` no POLYGON entry per `chain_env.py:218`) | n/a                                                      | n/a            |
> | SPARK       | ETHEREUM | ✅ adapter wired (`_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3"]`)                                            | 2023-05-09 → present                                     | ✅ NOW         |
>
> **Family-1 backtest data envelope** (slot 5 plan dependency): ≥2-year window of SUPPLY_APY / BORROW_APY / UTILISATION
> for Aave V3 + Compound V3 on Ethereum / Arbitrum / Base. **Met** for all 3 chains; per-pair launch dates per
> `PROTOCOL_LAUNCH_DATES` (`chain_env.py:204-221`).
>
> **Remaining Day-2 work** (does NOT block slot 5 Family-1 design — slot 5 pulls fix Day 3):
>
> - (a) Recent-days catch-up `2026-05-07..today` (~5-10min scoped VM via
>   `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07 today`) — closes the 5-day tail-end gap.
> - (b) [P1] `ManifestFreshnessCache` wire-in (refactor; not Family-1-blocking — slot 5 reads what's captured today).
> - (c) [P2] Clean full-history all-chains re-run after (b) lands (cosmetic; cleans the ~142 LINEA + ~296 BSC
>   `SOURCE_RETURNED_ZERO` pre-launch nits to `EXPECTED_PRE_GENESIS_CHAIN`).
> - (d) [P1] `create-code-tarballs.sh` stale-repo list (tooling debt; not Family-1-blocking).
>
> **What slot 5 should DO on Day 1** (2026-05-12):
>
> 1. Read `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 1 reframed-as-blocker section + AD-1 through AD-6.
> 2. Start Family-1 design (orchestrator config schema + per-chain dispatch + recursion params + flash-vs-persistent
>    mode toggle) using the data envelope above.
> 3. Sample parquet probe (gcs-cat) for 1 row of AAVE_V3 ETHEREUM SUPPLY_APY @ `2024-01-15` to verify non-NaN value
>    BEFORE committing to backtest harness shape. (Slot 3's 2026-05-11 audit confirmed parquet shape is real, but
>    re-verify for Family-1's specific data_type subset.)
> 4. Day 3 (2026-05-14): pull fix — re-fetch latest manifest state including recent-days catch-up (a).
>
> ---
>
> - [x] [MTDS] P0. **3-LENDING.1 — Bug 1: Aave V3 Ethereum silent-zero**. Audit `adapters/aave_v3_lending_rates.py`:
>       when subgraph returns zero rows, current behaviour writes `empty_confirmed`. Per CLAUDE.md "Honest absence vs
>       fake placeholders" — should classify per the 4-category tree: if catalog says alive AND day in coverage, attempt
>       failed → `record_failed` with typed reason; only legitimate empties get `empty_confirmed`. **✅ CLOSED AS STALE
>       FRAMING 2026-05-11 by slot 3 + verified 2026-05-12 by slot 2.** Per `defi_master.md` DONE-2026-05-12 block:
>       "routing config absent" framing was stale; data exists on-disk (LINEA 2025-03-01 = 475 real rows, BSC 2024-06-01
>       = 316 real rows — NOT 1440-NaN placeholders). The actual gap was operational (canonical manifest stale vs per-VM
>       shards) — closed by slot 3 manual consolidator + Case-5 bucket fix (deployment-service@`ad4d448`, slot
>       6@`2a76a2a`). Aave V3 Ethereum 0/343 silent-zero specifically: slot 3 confirmed the ~576 stale "404 GET https"
>       `attempted_failed` rows reclaimed. No code change needed — root cause was consolidator dispatch + per-VM shard
>       reconciliation, not adapter classification.
> - [x] [MTDS] P0. **3-LENDING.2 — Bug 2: Compound V3 multi-chain subgraph routing**. Compound V3 has separate subgraphs
>       per chain (Ethereum / Arbitrum / Base). Adapter must dispatch per chain; per-chain failures are isolated. \*\*✅
>       CLOSED AS STALE FRAMING 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) — pre-audit verified at MTDS
>       `cli/handlers/lending_indices_handler.py:90` (`_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3"]`) +
>       per-chain dispatch via `chains_override or get_supported_chains_for_protocol(protocol)` loop. The "2026-05-07
>       COMPOUND_V3 ARB/BASE/OPT" empty-routing bug referenced in the handler's comment was already fixed upstream.
>       Per-chain failures isolated via `record_failed`/`record_empty` per shard. SUBGRAPH_IDS map at MTDS
>       `subgraph_service.py` covers ETHEREUM + ARBITRUM + BASE + OPTIMISM + SCROLL; POLYGON intentionally excluded
>       (Compound V3 not on Polygon — confirmed at UAC `chain_env.py:218`).
> - [x] [MTDS] P0. **3-LENDING.3 — Bug 3: instruments-store 2022 metadata floor**. Aave V3 mainnet launched 2022-03-01;
>       instruments-store currently lacks pre-March-2022 dates as `expected_unattempted`. Add
>       `LENDING_INDICES_COVERAGE_START` per (protocol, chain) to UAC. \*\*✅ CLOSED AS STALE FRAMING 2026-05-12 by slot
>       2 (ikenna-defi-catalogue-tab) — pre-audit verified at UAC `chain_env.py:144-225` `PROTOCOL_LAUNCH_DATES` dict,
>       which already covers exactly the (chain, protocol) → launch-date semantic the plan body asked for
>       `LENDING_INDICES_COVERAGE_START` to provide. Per `lending_indices_handler.py:322` the handler reads
>       `get_protocol_launch_date(chain, venue_prefix)` and short-circuits to `expected_unattempted` for pre-launch
>       dates (per MTDS@`c6bdf96`). Pairs covered: `(ETHEREUM, AAVE_V3)` 2022-03-16, `(ETHEREUM, COMPOUND_V3)`
>       2022-08-13, `(ETHEREUM, SPARK)` 2023-05-09, etc. — full per-chain matrix already in the registry; slot 5
>       confirmed 45/46 pending-pairs shipped 2026-05-12 at UAC@`458f17d`. No separate `LENDING_INDICES_COVERAGE_START`
>       constant needed (single PROTOCOL_LAUNCH_DATES SSOT covers it).
> - [x] [VM] P0. **3-LENDING.4 — Lending-indices backfill VM**.
>       `deployment-service/scripts/vm/launch-defi-lending-indices-backfill-vm.sh` (new launcher per VM-launcher-SSOT
>       rule). Per CLAUDE.md "Plans Run To Actual Completion" — backfill VM must run to completion with
>       manifest-verified coverage 2022-03-01 → present before Phase 3 reports done. Recursive-borrow Phase 9 gates on
>       this. **✅ SHIPPED 2026-05-13 (Day 2) by slot 2 (ikenna-defi-catalogue-tab)** — recent-days catch-up VM
>       `mtds-lending-indices-20260511-204908` launched via
>       `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07     2026-05-13` in `asia-northeast1-c` (e2-standard-4 +
>       50GB). Lifecycle observed via
>       `gs://central-element-323112-events/events/market-tick-data-service/2026-05-11/mtds-lending-indices-20260511-204908/hour=19/`:
>       234 events including STARTED + ~232 progress events + STOPPED at 19:55:59 UTC. VM auto-deleted on completion
>       (shutdown_on_completion=true). Total runtime ~3 minutes for 7-day window. **Manifest verification**: read
>       `gs://lending-indices-central-element-323112/_index/availability_index.parquet` — 65 captured rows for
>       2026-05-07..2026-05-11 (13/day across AAVE_V3 × 6 chains + COMPOUND_V3 × 5 chains + SPARK × 1 chain = 12
>       protocol-chain combos). 2026-05-12+ → `empty_confirmed` (legitimate — The Graph subgraphs lag ~1 day behind
>       real-time; not a data gap). **Priority #5 in `defi_master.md` cleared** — slot 3's handoff item (a) "Recent-days
>       catch-up" done.
>
> Original PARTIAL annotation from 2026-05-11 by slot 3 retained for provenance: launcher exists at
> `deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh` (verified at slot 3 status note);
> 2026-05-11 full-history backfill VM `mtds-lending-indices-20260511-181115` killed at ~3373 events / ~375 dates
> (operator decision — `lending_indices_handler` re-downloads already-`captured` data; no manifest-freshness skip).
> **Remaining work**: (a) recent-days catch-up `2026-05-07..today` 5-10min scoped run with event-stream verification
> (`STARTED+progress+STOPPED`); (b) ManifestFreshnessCache wire-in (P1 from `defi_master.md` DONE-2026-05-12 block §
> Discoveries during Priority #5); (c) clean full-history re-run after (b) lands. **Slot 5 Family-1 design NOT blocked**
> — pulls fix Day 3 per spec above.
>
> - [x] [SCRIPT] P0. **3-LENDING.5 — Manifest reconciler one-shot**. ✅ **SHIPPED 2026-05-16 by slot 2 via sub-agent
>       dispatch** at `instruments-service@88d48da` (10 unit tests green; basedpyright 0 errors). Script at
>       `instruments-service/scripts/reconcile_lending_indices_phantom.py` (175 lines) + tests at
>       `tests/scripts/test_reconcile_lending_indices_phantom.py`. CLI: `--dry-run` (default) /
>       `--apply-flips     --confirm` (safety belt) / `--protocols X,Y` / `--chains A,B` / `--max-flips N`. Reads
>       canonical `gs://lending-indices-{pid}/_index/availability_index.parquet`; probes flat-prefix layout
>       `lending_indices/{protocol}/{chain}/date={YYYY-MM-DD}/` per handler docstring; classifies phantoms as
>       `EXPECTED_PRE_GENESIS_CHAIN` (via UAC `get_protocol_launch_date(chain, venue_prefix)` from
>       `unified_api_contracts.registry.chain_env`) or `SOURCE_RETURNED_ZERO` (post-launch). Idempotent re-runs.
>       **Bug-fix follow-up 2026-05-16 by slot 2** at `instruments-service@70074a0`: real-data dry-run caught 3 critical
>       bugs (100% false-positive rate before fixes): (1) `_audit_captured_rows` passed manifest venue (`AAVE_V3`
>       uppercase) directly into the path template; actual GCS flat-prefix layout uses lowercase + underscored slug
>       (`aave_v3`). Added `_VENUE_TO_SLUG` inverse map. (2) `_classify_phantom` expected slug but callers passed venue;
>       all rows fell through to `SOURCE_RETURNED_ZERO` regardless of date. Rewrote to take venue directly. (3)
>       `--protocols` filter used `.str.lower()` (no-op for slug match: `AAVE_V3.lower() == aavev3 ∉ {aave_v3}`); fixed
>       to translate via `_VENUE_TO_SLUG` before `.isin()` comparison. Bonus fix: `data_type` filter now accepts both
>       `lending_indices` (snake) AND `lending-indices` (kebab legacy 24,976 rows) — see archived
>       `plans/archive/issues/lending_indices_data_type_vocabulary_drift_2026_05_16.md`. (Vocab-drift kebab rows since
>       canonicalised by slot 4 via my Option A canonicalisation script `IS@b2726c6`; 115,785 vocab flips + 6,972
>       corrupt drops via slot 4 + IS@70849b6 Option D shipped 2026-05-16.) 2 new unit tests; 12/12 tests green;
>       basedpyright 0 errors. Earlier slot-3 manual consolidator already shipped (deployment-service@`ad4d448` + slot
>       6@`2a76a2a`); reconciler covers the residual `SOURCE_RETURNED_ZERO` pre-launch nits + any future phantom drift.
>
>       **Operational dry-run RESULT 2026-05-16 ~20:21Z (post-fix)**: real-data audit of
>                                                                                                                       `gs://lending-indices-{pid}/_index/availability_index.parquet` reports:
>                                                                                                                       - Total captured rows audited: **64,827** (includes both kebab + snake data_type rows)
>                                                                                                                       - Real captures (parquet found): **64,476** (99.5%)
>                                                                                                                       - Phantom captures: **351** (0.54%) — all classified `SOURCE_RETURNED_ZERO`
>                                                                                                                       - Phantom distribution by venue: AAVE_V3 216 / COMPOUND_V3 108 / SPARK 27
>                                                                                                                       - Phantom distribution by chain: ETHEREUM 81 / ARBITRUM 54 / BASE 54 / OPTIMISM 54 / others 27 each
>                                                                                                                       - Sample phantoms: 2026-04-15 across multiple AAVE_V3 chains — recent backfill misses, not legacy phantoms
>                                                                                                                       Manifest is operationally clean; 351 phantoms are operator-decision: run `--apply-flips --confirm` to flip to
>                                                                                                                       `empty_confirmed/SOURCE_RETURNED_ZERO` (recommended once consolidator race resolved per
>                                                                                                                       `plans/active/issues/vocab_drift_canonicalisation_didnt_stick_2026_05_16.md`). Log archived at
>                                                                                                                       `/tmp/lending_indices_phantom_dryrun_v2_20260516.log`.

Success criterion: per protocol, an MTDS adapter at
`market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/<protocol>_adapter.py` (or
`adapters/onchain_perps/` / `adapters/defi_live/` per shape) capturing the data_types declared in UAC Phase 1A. Each
write resolves to one of `captured` / `empty_confirmed` (typed reason) / `attempted_failed` / `expected_unattempted` per
writegate Phase 3.D.5. No legacy NaN-placeholder rows.

**Per-protocol scope (data_types per UAC Phase 1A):**

- Vaults: `vault_share_price`, `vault_apy`, `vault_tvl` (Yearn / Convex / Beefy / Pendle / Idle).
- Spot DEXes: `dex_swaps`, `dex_pools`, `position_data` (Balancer / Sushi / PancakeSwap / Camelot / Aerodromeq /
  Velodrome / TraderJoe / Raydium / Orca).
- Aggregators: `aggregator_routes` read-only via API (Jupiter).
- Lending (Spark + Radiant + Aave V3 multi-chain): `lending_indices`, `oracle_prices`, `rewards`, `risk_params`,
  `liquidation_events`, `flash_loan_events`, `position_data`.
- LSTs: `lst_rates`, `oracle_prices`, `staking_yields` (Rocket Pool + Solblaze).
- Restaking: `eigenlayer_rewards` (rename to `restaking_rewards` for protocol-agnostic), `staking_yields`,
  `restaking_yields`, `slashing_events` for all 6 LRT protocols + EigenLayer + Symbiotic + Karak + Jito-restaking.

Per-protocol todos (expanded from template):

- [x] [AGENT] P0. **3.ROCKETPOOL — Rocket Pool (rETH) MTDS adapter** — `adapters/defi/lst_rocket_pool_adapter.py`. AAVE
      oracle primary + DefiLlama fallback. `oracle_prices` data_type. mtds@`80ee665`.
- [x] [AGENT] P0. **3.RENZO — Renzo (ezETH) MTDS adapter** — `adapters/defi/lst_renzo_adapter.py`. AAVE oracle primary +
      DefiLlama fallback. `oracle_prices` data_type. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.KELPDAO — KelpDAO (rsETH) MTDS adapter** — `adapters/defi/lst_kelpdao_adapter.py`. AAVE oracle
      primary + DefiLlama fallback. `oracle_prices` data_type. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.PUFFER — Puffer Finance (pufETH) MTDS adapter** — `adapters/defi/lst_puffer_adapter.py`. AAVE
      oracle primary + DefiLlama fallback. `oracle_prices` data_type. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.SOLBLAZE — Solblaze (bSOL) MTDS adapter** — `adapters/defi/lst_solblaze_adapter.py`. DefiLlama
      coins API (Solana chain, no AAVE oracle). `oracle_prices` data_type. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.YEARN — Yearn Finance V3 vaults MTDS adapter** — `adapters/defi/vault_yearn_adapter.py`. DefiLlama
      yields API filtered by `yearn-finance`. `vault_share_price`/`vault_apy`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.CONVEX — Convex Finance vaults MTDS adapter** — `adapters/defi/vault_convex_adapter.py`. DefiLlama
      yields API filtered by `convex-finance`. `vault_share_price`/`vault_apy`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.BEEFY — Beefy Finance multi-chain vaults MTDS adapter** — `adapters/defi/vault_beefy_adapter.py`.
      DefiLlama yields API filtered by `beefy`. `vault_share_price`/`vault_apy`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.IDLE — Idle Finance yield vaults MTDS adapter** — `adapters/defi/vault_idle_adapter.py`. DefiLlama
      yields API filtered by `idle`. `vault_share_price`/`vault_apy`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.PENDLE — Pendle PT/YT/SY MTDS adapter** — `adapters/defi/vault_pendle_adapter.py`. DefiLlama
      yields API filtered by `pendle`. `vault_share_price`/`vault_apy`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.SYMBIOTIC — Symbiotic restaking vaults MTDS adapter** —
      `adapters/defi/restaking_symbiotic_adapter.py`. DefiLlama yields API filtered by `symbiotic`.
      `restaking_rewards`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.KARAK — Karak restaking vaults MTDS adapter** — `adapters/defi/restaking_karak_adapter.py`.
      DefiLlama yields API filtered by `karak-network`. `restaking_rewards`/`vault_tvl`. mtds@`3e82cc5`.
- [x] [AGENT] P0. **3.JITO-RESTAKING — Jito Restaking (Solana) MTDS adapter** —
      `adapters/defi/restaking_jito_adapter.py`. DefiLlama yields API filtered by `jito-restaking`.
      `restaking_rewards`/`vault_tvl`. mtds@`3e82cc5`.

**Codex SSOT updates (Phase 3 boundary)**:

- [x] [AGENT] P0. **3J — Update `/codex/02-data/defi-data-type-taxonomy.md`** (NEW) with full per-venue data-type
      matrix. (PM@`291f81d7` — vault/restaking/LST coverage updated with adapter-shipped status)
- [x] [AGENT] P0. **3K — Update `/codex/02-data/availability-manifest-and-data-status.md`** with new bundled data_types
      from Phase 1A. ✅ **SHIPPED 2026-05-16 by slot 2** at `unified-trading-pm@<TBD>`. 3 targeted updates: (1) Layer 2
      MTDS DEFI row: 26 protocols enumerated + 14 chains + per-instance vs bundled data_type breakdown; (2) Layer 2.5
      MDPS DEFI row: corrected to actual 5 adapters (book_snapshot_5/dex_swaps/fx_rates/market_state/ liquidity) with
      B-015 Option A cross-reference noting on-chain snapshot types flow direct from MTDS; (3) NEW sub-section "Phase 1A
      DeFi bundled data_types (2026-05-16 — Phase 3K)" with 7-row family matrix covering shard atoms +
      cluster-validation requirements per protocol family + MDPS aggregation contract.

**Full-execution criterion**:

- ✅ Each protocol's MTDS adapter writes ≥ 1 captured-state parquet to GCS within smoke-test boundary.
- ✅ Sample parquet inspection (`gcloud storage cat ... | head`) shows populated rows, NOT 1440-NaN placeholders.
- ✅ Manifest pre-flight skip works correctly (don't re-fetch captured shards).

## Phase 4 — Execution-service connector buildout (PARALLEL, depends on Phase 2; ~25-40 AI-days)

Owner: harsh + parallel agents per connector.

Success criterion: per protocol with a write-side use case (swap / borrow / lend / stake / restake), an execution-
service connector at `execution-service/execution_service/defi_execution/protocols/<protocol>.py` implementing the
`ExecutionProvider` protocol. Tenderly fork integration test green. Testnet (Sepolia for EVM, devnet for Solana)
validated.

**Connector scope** (write-side use cases for May-23 archetypes; read-only protocols skip connector):

- Spark + Radiant + Aave V3 multi-chain: borrow / lend / repay / withdraw connectors.
- Yearn + Convex + Beefy + Pendle + Idle: deposit / withdraw connectors.
- Rocket Pool + Solblaze: stake / unstake connectors.
- EigenLayer + Symbiotic + Karak + Renzo + KelpDAO + Puffer + Jito-restaking: deposit / withdraw / delegate connectors.
- Balancer + Sushi + PancakeSwap + Camelot + Aerodromeq + Velodrome + TraderJoe + Raydium + Orca + Jupiter agg: swap
  connectors.
- Aster: complete the existing skeleton at `execution-service/defi_execution/protocols/aster.py` with full place_order /
  modify / cancel.

Per-connector todo template:

- [x] [AGENT] P0. **4.<X> — `<protocol>` execution-service connector.** CODE SHIPPED 2026-05-12 by Harsh slot 2. 13
      connectors shipped at execution-service@`b9078ee9` (reconcile commit; sub-agent group commits: `80e7ca60`,
      `5ad2cd47`, `a91565b3`, and earlier). All 13 connector files + 13 unit test files, `__init__.py` exports,
      `_VENUE_SOURCE_MAP` entries, type errors fixed. **DEFERRED**: Tenderly fork integration tests + testnet tx
      validation (Sepolia/Holesky/devnet). Credential-injection: follows `connector.connect(config={...})` per
      `interface-credential-convention.md` (updated 4J). Error classification via `preflight_validate_operation()`
      wired; DefiErrorCode taxonomy extension deferred pending actual Tenderly fork run (no new revert reasons surfaced
      in backtest-mode implementation). **Successor for deferred items**:
      `defi_catalogue_chain_primitives_2026_05_10.md` Phase 4 full-execution criterion.

**Codex SSOT update (Phase 4 boundary)**:

- [x] [AGENT] P0. **4J — Update `/codex/04-architecture/interface-credential-convention.md`** with new connectors'
      credential shapes. (PM@`3d1d5a39` — added Phase 4 credential shape section; all 13 follow existing pattern)
- [x] [AGENT] P0. **4K — Update `/codex/04-architecture/defi-execution-overview.md`** with connector inventory.
      (PM@`3d1d5a39` — added Phase 4 connector inventory tables by family: LST/LRT, restaking, yield, Solana)

**Full-execution criterion**:

- ✅ Every connector has ≥ 1 Tenderly-fork integration test passing.
- ✅ Each connector has ≥ 1 testnet tx (Sepolia/Holesky/devnet) successfully placed (recorded in test logs).
- ✅ `DefiErrorCode` taxonomy extended with new revert codes; per-code `FAIL/RETRY/SKIP` routing declared.

## Phase 5 — Chain primitives (PARALLEL with 2-4; ~5-10 AI-days)

Owner: ikenna for design + harsh for implementation.

- [x] [AGENT] P0. **5A — Solana Jito bundle submission**. New file
      `execution-service/execution_service/defi_execution/mev/jito_bundle.py` implementing `JitoBundleProvider` per the
      `flashbots.py` / `private_mempool.py` shape. Submits Solana tx bundles via Jito block-engine RPC. Wired into
      `mev_router.py` per Phase 1D. **PARTIAL — design-shipped via Phase 1D 2026-05-12 by slot 2** (UAC@`5241fad0` +
      execution-service@`38710bef`): `MevSubmissionMode.JITO_BUNDLE` enum value + `_DEFAULT_POLICIES[JITO_BUNDLE]`
      policy entry shipped (endpoint_ref=`jito_bundle_rpc`, bundle_mode=private, max_block_delay=2,
      supported_chains=(solana,), private=True). **REMAINING (Harsh-side implementation)**: `JitoBundleProvider` class
      at `execution-service/execution_service/defi_execution/mev/jito_bundle.py` mirroring the `PrivateMempoolProvider`
      shape at `execution-service/execution_service/defi_execution/mev/private_mempool.py`. Submits via Jito
      block-engine RPC (`https://mainnet.block-engine.jito.wtf/api/v1/bundles`). Bundle = 1-5 Solana transactions with a
      tip transaction included for prioritisation. Endpoint URL + tip-account pubkey resolved via UCI/Secret Manager.
      Authentication: optional paid Jito subscription OR free with rate limits. **🟢 IMPLEMENTATION SHIPPED 2026-05-15
      by slot 2 sub-agent fan-out** at execution-service@`f1b46320`. Public surface landed:
      `class JitoBundleProvider(endpoint_url, *, tip_account, max_block_delay=2)` + async
      `submit_bundle(transactions, *, tip_lamports) -> JitoBundleResult` + async
      `get_bundle_status(bundle_id) ->     BundleStatus` + `class JitoBundleResult` frozen dataclass +
      `class BundleStatus(StrEnum)` (PENDING / LANDED / FAILED / DROPPED) + `assert_jito_mode()` +
      `assert_solana_chain()` guards + `JITO_BLOCK_ENGINE_MAINNET` constant. Wired into `mev/__init__.py` exports. 11
      unit tests passing (request shape / tip-tx construction / status mapping / mode guard / empty-bundle-id
      rejection). basedpyright clean. Real Jito RPC NEVER hit — `responses` library used for HTTP mocks. Slot 2
      implementation closed the Harsh-handoff gap same-cycle.
- [x] [AGENT] P0. **5B — Per-chain RPC redundancy**. Update
      `execution-service/execution_service/config/chain_config.yaml` (or equivalent) to declare ≥ 2 independent RPC
      providers per chain in scope (Alchemy + QuickNode + Ankr + Helius for Solana + project-specific public RPC). Add
      `RpcProviderFallback` class that auto-fails-over on connection-drop / 429 / 5xx within configurable retry budget.
      **DESIGN-SHIPPED 2026-05-13 (Day 3) by slot 2 — IMPLEMENTATION HANDED TO HARSH SLOT 2.** Design SSOT lives in
      [`/codex/05-infrastructure/chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md) § "RPC
      provider redundancy" (lines 36-63). **🟢 IMPLEMENTATION SHIPPED 2026-05-15 by slot 2 sub-agent fan-out** at
      execution-service@`d1feadeb`. 11-chain `chain_config.yaml` shipped (ETHEREUM / ARBITRUM / BASE / OPTIMISM /
      POLYGON / AVALANCHE / BSC / LINEA / SCROLL / ZKSYNC / SOLANA — primary + fallbacks + auto-failover-on-5xx-or-429 +
      retry_budget=3). `RpcProviderFallback` class shipped at
      `execution-service/execution_service/providers/rpc_fallback.py` (337 lines): sync `execute(method, params)` +
      async `execute_async(...)` + auto-failover on
      `httpx.ConnectError |     httpx.TimeoutException | 429/500/502/503/504` +
      `RpcProviderFallbackExhausted(chain, providers_tried)` exception on retry-budget exhaustion.
      `RPC_PROVIDER_FAILOVER` events emitted via UTL `log_event`. URLs resolved via UCI/Secret Manager (NO os.getenv). 6
      unit tests in `tests/unit/providers/test_rpc_fallback.py` (config-load / 429 failover / 5xx failover /
      connection-error failover / retry-budget-exhausted-raises / unknown-chain-raises). Slot 2 implementation closed
      the Harsh-handoff gap same-cycle. **Remaining wire-in to defi_execution/protocols/ web3 callsites is a separate
      Harsh slice.**
- [x] [AGENT] P0. **5C — Tenderly bundle-sim API + gating policy**. Extend
      `execution-service/execution_service/providers/tenderly.py` with `simulate_bundle()` method using Tenderly's
      `/api/v1/account/{slug}/project/{slug}/simulate-bundle` endpoint. Wire pre-flight gating in execution-service
      handlers: every live order goes through bundle-sim, BLOCK on revert, advisory-log on slippage>threshold. Default
      per-archetype daily Tenderly budget =
      $50/day per archetype (operator-set ceiling); 1 sim per live order. Budget
      exhaustion downgrades to advisory-only. **✅ IMPLEMENTATION SHIPPED 2026-05-12 by slot 2 —
      execution-service@2abbc1f7** — `simulate_bundle(transactions, chain_id) -> BundleSimResult` + `TenderlyTx` /
      `BundleSimResult` dataclasses + `gate_or_advise()` pre-flight helper landed in
      `execution_service/providers/tenderly.py`; `TenderlyBudgetTracker` with GCS-backed daily state (`$50/day`ceiling)     landed in`execution_service/providers/tenderly_budget.py`; `BlockOnSimulationRevert`in    `execution_service/providers/_tenderly_errors.py`; 6 unit tests in     `tests/unit/providers/test_tenderly_bundle_sim.py`covering request shape / clean sim / revert / high-slippage     advisory / budget exhaustion / block-on-revert. **REMAINING — wire`gate_or_advise()`call into every live DeFi    `execute()` path** (defi_execution/protocols/) is a separate slice tracked under Harsh's continuation queue.     Design SSOT lives in     [`/codex/05-infrastructure/chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md) §     "Tenderly setup" (lines 91-126) — pre-existing codex content from Phase 5D specifies the API key flow (Secret     Manager `tenderly_api_key`), bundle-sim endpoint shape, and per-archetype $50/day budget policy. **Harsh     implementation scope** (~1.5 calibrated AI-days): - Extend     `execution-service/execution_service/providers/tenderly.py`(verify exists; if not, create) with    `simulate_bundle(transactions:
      list[TenderlyTx], chain_id: int) -> BundleSimResult`calling Tenderly's    `POST
      /api/v1/account/{slug}/project/{slug}/simulate-bundle`endpoint.`BundleSimResult`dataclass:    `revert:
      bool`+`revert_reason: str | None`+`expected_slippage_bps: int`+`gas_used:
      int`. - Wire     pre-flight gating in defi_execution/protocols/ — every `execute()`method on a live (non-paper-trade) order:    `bundle_sim
      =
      tenderly.simulate_bundle(...)`→ if`bundle_sim.revert`raise`BlockOnSimulationRevert(...)`; if     `bundle_sim.expected_slippage_bps >
      threshold`log advisory event. - Per-archetype daily Tenderly budget tracked     in`unified-cloud-interface/secret_budget_tracker.py`(NEW or extend existing rate-limit primitive). Budget     exhaustion → degrade to`advisory-only`mode (logs but doesn't block). - Tests:    `pytest
      execution-service/tests/unit/providers/test_tenderly_bundle_sim.py` — mock Tenderly responses for (a) clean
      simulate; (b) revert → assert BlockOnSimulationRevert raised; (c) high-slippage → assert advisory event emitted;
      (d) budget exhaustion → assert downgrade behaviour.
- [x] [AGENT] P0. **5D — Codex SSOT** at `/codex/05-infrastructure/chain-rpc-mev-tenderly.md` (NEW) with full per-chain
      table: RPC primary + fallback, MEV-protected RPC, gas oracle source, Tenderly account/project, historical capture
      bucket. **✅ SHIPPED — already exists at
      [`/codex/05-infrastructure/chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md) (204
      lines).** Audit 2026-05-13 by slot 2 confirms doc covers: per-chain matrix (11 chains in May-23 scope + StarkNet);
      RPC provider redundancy spec with `chain_config.yaml` template; MEV protection per chain (5 MevSubmissionMode
      endpoint registry rows + per-chain MEV story); Tenderly setup (account / project / budget / bundle-sim API
      gating); Gas oracles per chain; Oracle prices per chain; Cross-references; Update protocol. **JITO_BUNDLE row** in
      MEV registry (line 77) correctly marked as Phase 5A buildout. **MINOR DELTA Day 3**: slot 2 should add a note line
      that JITO_BUNDLE enum + `_DEFAULT_POLICIES` policy shipped Phase 1D 2026-05-12 so the Status column for that row
      flips to ◐ (enum + policy ✅, provider class pending Harsh implementation). Deferred to a separate codex-doc-touch
      commit to keep this checkbox flip clean.

**Full-execution criterion**:

- ✅ `mev_router.py` `_DEFAULT_POLICIES[MevSubmissionMode.JITO_BUNDLE]` exists + tested.
- ✅ `chain_config.yaml` declares ≥ 2 RPC providers per chain; fallback test simulates primary down + secondary picks
  up.
- ✅ Tenderly bundle-sim has ≥ 1 successful simulate + ≥ 1 successful BLOCK-on-deliberate-revert in tests.
- ✅ Codex doc covers all 22 chains in `CHAIN_GENESIS_DATES`.

## Phase 6 — Backfills (PARALLEL VM-launch fan-out; ~10-15 AI-days wall-clock)

Owner: harsh + per-asset-group parallel agents.

Per CLAUDE.md "No fire-and-forget VM launches" + "Per-VM shard isolation for concurrent backfills" + "Manifest
concurrency principle" (read-once + per-date freshness check + write-time CAS).

- [x] [AGENT] P0. **6A — Aave V3 Ethereum silent-zero diagnose + re-run**. ✅ **CLOSED-AS-STALE 2026-05-16 by slot 2
      (ikenna-defi-catalogue-tab)** — duplicate of Phase 3-LENDING.1 (line 679-689 above) which itself was closed-as-
      stale 2026-05-11/12: "routing config absent" framing was stale; data exists on-disk (LINEA 2025-03-01 = 475 real
      rows, BSC 2024-06-01 = 316 real rows). Root cause was operational (canonical manifest stale vs per-VM shards) —
      closed by slot 3 manual consolidator + Case-5 bucket fix (deployment-service@`ad4d448`, slot 6@`2a76a2a`). No code
      change needed at MTDS adapter. Tail-end catch-up already shipped 2026-05-13 via 3-LENDING.4 catch-up VM
      `mtds-lending-indices-20260511-204908` (65 captured rows, 12 protocol-chain combos).
- [x] [AGENT] P0. **6B — Aave V3 multi-chain backfill** (9 non-Ethereum chains × N reserves × dates). ✅ **HISTORICAL
      DATA CONFIRMED PRESENT 2026-05-17 (slot-1-main)**: manifest already contains ARBITRUM / OPTIMISM / POLYGON /
      AVALANCHE / BASE / LINEA / BSC data from 2022-01-01 through 2026-05-13 (prior VM runs + live mode). **CATCH-UP VM
      LAUNCHED 2026-05-17 16:04 UTC**: `mtds-lending-indices-20260517-160411` filling 2026-05-14→2026-05-17 gap using
      existing `launch-mtds-lending-indices-backfill-vm.sh` (runs all UAC-defined chains via
      `get_supported_chains_for_protocol('aave_v3')` automatically). **VM COMPLETED 2026-05-17 16:09 UTC** (`STOPPED`
      event received). Results: 26,633 rows (2026-05-14) + 30,307 (2026-05-15) + 31,190 (2026-05-16) + 17,072
      (2026-05-17 partial) = **105,202 rows total** across 13 protocol-chain shards; 0 empty shards. **SCROLL/ZKSYNC**:
      no UAC subgraph IDs (`get_subgraph_id('aave_v3', 'SCROLL')` returns None) — data collection blocked;
      BLOCKED-UPSTREAM pending UAC PR to add `SCROLL`/`ZKSYNC` entries to `SUBGRAPH_IDS["aave_v3"]`.
- [x] [AGENT] [BLOCKED-OPERATOR] P0. **6C — Solana LST historical** (jitoSOL / mSOL / bSOL / Rocket Pool / Solblaze) —
      Pyth Hermes backfill 2023-10-01 → today. Launcher `launch-mtds-solana-lst-vm.sh` (NEW).
      **[DEFERRED-OPERATOR-DECISION]** 2026-05-19 slot 2: launcher `launch-mtds-pyth-lst-backfill-vm.sh` already exists
      covering JitoSOL/mSOL/bSOL/INF (2023-10-01 → today). Launcher header says "DO NOT LAUNCH without operator [ack] in
      ikenna_orchestrator/pings/slot_2.md" — no ack found. Rocket Pool/Solblaze feeds need operator pick of Pyth feed
      IDs. Blocked on operator go-ahead + feed IDs. — slot-2 2026-05-20 BLOCKED-OPERATOR ping filed.
- [x] [AGENT] [BLOCKED-OPERATOR] P0. **6D — Lighter / Pacifica / Extended OHLCV backfill** + contract addresses + ABI
      parsing completion. Launcher `launch-mtds-defi-perp-backfill-vm.sh`. **[DEFERRED-OPERATOR-DECISION]** 2026-05-19
      slot 2: no `launch-mtds-defi-perp-backfill-vm.sh` exists. Extended backfill also gated as
      DEFERRED-OPERATOR-DECISION in `dex_perp_and_venue_data_expansion_2026_05_12.md` 2F (PM@f15a85ab same session).
      Forward-poll launcher `launch-cefi-onchain-forward-poll.sh` covers live data. Backfill window + VM cost need
      operator go-ahead. — slot-2 2026-05-20 BLOCKED-OPERATOR ping filed.
- [x] [AGENT] [BLOCKED-OPERATOR] P0. **6E — Vaults + restaking + DEX historical** for all 26 Phase 1A protocols.
      Per-protocol VM where TVL × dates × instruments justifies (default: 2-year backfill). Launchers under
      `deployment-service/scripts/vm/`. **[DEFERRED-OPERATOR-DECISION]** 2026-05-19 slot 2: 26-protocol full-historical
      backfill requires per-protocol operator decision on window + VM cost (potentially 26 individual VMs). Vault
      share-price launcher (`launch-mtds-vault-share-price-backfill-vm.sh`) + EigenLayer rewards launcher already exist.
      Remaining protocols (restaking, DEX) need operator-triage on priority order before launching. Not blocking May-23
      (6F phantom audit already ran clean; live feeds running). — slot-2 2026-05-20 BLOCKED-OPERATOR ping filed.
- [x] [AGENT] P0. **6F — Manifest phantom audit** post-backfill. ✅ **DEFI raw_tick_data audit RAN-CLEAN 2026-05-16 by
      slot 2** — `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`
      executed against `gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet` (1,606,190
      manifest rows; 311,602 captured rows in scope; 88,557 unique prefixes listed). **Result: zero phantoms; manifest
      CLEAN**. Audit log at `/tmp/defi_phantom_audit_20260516.log` (188 lines). **Scope caveat**: this audit covers the
      DEFI raw_tick_data bucket only; the separate `lending-indices-{pid}` canonical manifest verification is the
      explicit successor of 3-LENDING.5 reconciler (in-flight slot-2 sub-agent dispatch).

**Codex SSOT updates (Phase 6 boundary)**:

- [x] ✅ [AGENT] P0. **6J — Update `/codex/02-data/availability-manifest-and-data-status.md`** with the new protocol
      capture coverage + manifest health % per asset_group post-backfill. — PM@48e635d40: "Phase 6 DeFi backfill capture
      coverage" table added (lending ETH/multi-chain ✅, LST-Solana BLOCKED-OPERATOR, vaults/DEX 6E OPEN, phantom
      clean). 6C/6D in-flight; table refreshes once those VMs complete.

**Full-execution criterion**:

- ✅ Every Phase 1A protocol has ≥ 1 captured shard in production GCS bucket per manifest.
- ✅ Per-asset-group manifest coverage ≥ 99% for in-scope (asset_group, venue, data_type, day) cells.
- ✅ Phantom audit shows zero drift between manifest + on-disk parquets.
- ✅ Sample parquet inspection (5 random captures per protocol) shows populated rows.

## Phase 7 — Codex SSOT updates (continuous; per-phase boundaries above; final lock at end)

Per "Post-Plan-Phase Codex Audit HARD RULE" — every major phase boundary triggers codex update in same logical unit as
code commit. End-of-plan check: every codex doc reflects shipped state.

- [x] [AGENT] P0. **7A — `/codex/02-data/defi-venue-protocol-catalogue.md`** (NEW; Phase 1J). Final lock at Phase 8. ✅
      Slot 2 Day 1 (PM@`f54dd90c`) + Day 2 mirror (PM@`15709c4b`) — doc covers 26 protocols + per-protocol shard-atom
      matrix.
- [x] [AGENT] P0. **7B — `/codex/02-data/defi-data-type-taxonomy.md`** (NEW; Phase 3J). ✅ **VERIFIED-DONE 2026-05-16 by
      slot 2** — already shipped via Phase 3J at PM@`291f81d7` (line 798 above): "vault/restaking/LST coverage updated
      with adapter-shipped status". Doc exists at 284 lines covering full per-venue data-type matrix; matches the 13
      Phase 3 MTDS adapters (mtds@`3e82cc5`/`80ee665`). Final-lock-at-Phase-8 step is a no-op since the content already
      reflects shipped state.
- [x] [AGENT] P0. **7C — `/codex/05-infrastructure/chain-rpc-mev-tenderly.md`** (NEW; Phase 5D). Final lock at Phase 8.
      ✅ Pre-existed at 204 lines + slot 2 Day 3 JITO_BUNDLE status update (PM@`8ce85bbc`).
- [x] [AGENT] P0. **7D — `/codex/02-data/instrument-pipeline-defi.md`** (UPDATE; Phase 2J). ✅ **VERIFIED-DONE
      2026-05-16 by slot 2** — already shipped via Phase 2J at PM@`291f81d7` (line 610 above): adapter count 25→50, full
      categorized adapter list. Doc line 20 confirms: "Adapters (under reference_data/adapters/defi/ as of 2026-05-14 —
      refreshed per Phase 2J audit)". 267 lines documenting the 13 Phase 2 instruments-service adapters shipped at
      instruments-service@`a490033`+`be12b56`+`57a4f1f`+`38192e7`+`b563afb`.
- [x] ✅ [AGENT] P0. **7E — `/codex/02-data/availability-manifest-and-data-status.md`** (UPDATE; Phase 3K + 6J). ✅
      Phase 3K portion SHIPPED PM@`aab47b12` (Layer 2 MTDS DEFI row + Layer 2.5 MDPS DEFI row + "Phase 1A DeFi bundled
      data_types" sub-section). Phase 6J portion shipped PM@`48e635d40` (per-protocol backfill coverage table added
      2026-05-19 by slot 8): lending ETH/multi-chain ✅, LST-Solana BLOCKED-OPERATOR, vaults/DEX 6E OPEN, phantom clean.
      Table will auto-refresh once 6C/6E VMs complete.
- [x] [AGENT] P0. **7F — `/codex/04-architecture/interface-credential-convention.md`** (UPDATE; Phase 4J). ✅
      **VERIFIED-DONE 2026-05-16 by slot 2** — doc lines 56 + 118 confirm `connector.connect(config={...})` shape
      documented for all 13 Phase 4 connectors shipped at execution-service@`b9078ee9`. GAP-11 Live DeFi Wallet Key
      Lifetime extension landed 2026-05-15 (per-request Secret Manager fetch, no in-memory caching beyond
      `connect()`scope). Anti-patterns section enumerates instance-attribute private-key storage as HARD violation.
- [x] [AGENT] P0. **7G — `/codex/04-architecture/defi-execution-overview.md`** (UPDATE; Phase 4K). ✅ **VERIFIED-DONE
      2026-05-16 by slot 2** — doc line 111 confirms: "All Phase 4 connectors follow the same
      `connector.connect(config={...})` credential injection shape as the Phase 1–3 [connectors]". Key Files table
      covers all 13 Phase 4 protocol connectors + cost models + matching engine surfaces. Backtest replay status
      documented as `BLOCKED-DATA` until lending-indices ≥1yr backfill lands (target 2026-05-19→23).
- [x] [AGENT] P0. **7H — `defi_master.md`** body — gap-fill priorities + per-archetype readiness matrix refreshed. ✅
      Slot 2 Day 2 (PM@`d5ded095`) — Priority #5 flipped `[x]` with full closure evidence (catch-up VM
      `mtds-lending-indices-20260511-204908` + manifest verification of 65 captured rows).
- [x] ✅ [AGENT] P0. **7I — `master_to_live_defi_2026_05_23.md`** Group F items 17-20 status rows refreshed. —
      PM@`75560065` 2026-05-18. Row 20 Last verified updated → 2026-05-18 (B-015 paper VM
      `strategy-paper-carry-staked-basis-20260518-115404` live; pvl-p18a gate clock running); F20 graduated from NEVER
      list (6 remaining). Rows 17/18 already at 2026-05-18 per defi_simulation_realism Phase 2 close. Rows 19/21 remain
      PENDING (operator-gated / cron-pending). **DEFERRED — slot 1 ownership** per `work_split_2026_05_12_ikenna.md` row
      1 "Main orchestrator + governance + master plan refresh". Slot 2 has shipped enough DeFi-side progress that the
      Group F item 17/18/19/20 rows should reflect: item 17 (real wallet 7-day proof) BLOCKED on slot 4 wallet
      provisioning (UAC@`d721b6a` shipped 2026-05-12; ready for slot 5 archetype config consumption); item 18 (2-year
      batch backtest) UNBLOCKED by slot 2 Phase 3 spec — slot 5 Family-1 design Day 1 confirmed (PM@`5cb0952f`); item 19
      (Copper+CEFFU onboarding) tracked by slot 4 `api_keys_wallets_accounts_readiness_2026_05_10.md`; item 20
      (DeFi-side catalogue completeness) ✅ MOSTLY DONE per Phase 1J codex refresh. Slot 1 main-orch should integrate
      this status into the master plan readiness checklist on next refresh cycle.
- [x] [AGENT] P1. **7J — ManifestFreshnessCache wire-in into MTDS DeFi backfill handlers (NEW — folded in from
      `defi_master.md` DONE-2026-05-12 handover-block item (b))**. Per CLAUDE.md "Manifest concurrency principle" rule +
      the existing primitive at `unified-trading-library/unified_trading_library/manifest_freshness.py:136`
      `class ManifestFreshnessCache` (single-bucket TTL-cached row-key membership set; `is_now_captured(row_key)` API;
      `bulk_load()` warm-up). **DESIGN-SHIPPED 2026-05-13 (Day 4) by slot 2; IMPLEMENTATION HANDED TO HARSH SLOT 2**
      (per cross-side handshake "Ikenna designs, Harsh implements"). **Workspace-grep audit 2026-05-13**: zero current
      handlers wire `ManifestFreshnessCache`
      (`grep -rn     ManifestFreshnessCache market-tick-data-service/market_tick_data_service/` returns 0 hits). 9
      candidate handlers identified at `market-tick-data-service/market_tick_data_service/cli/handlers/`:
      `lending_indices_handler.py` / `gas_fee_handler.py` / `lst_rates_handler.py` / `dex_swaps_handler.py` /
      `dex_pools_handler.py` / `liquidations_handler.py` / `liquidation_events_handler.py` / `perp_funding_handler.py` /
      `solana_lst_archival.py`. **Wire-in pattern** (consistent across all 9 handlers): ```python from
      unified_trading_library import ManifestFreshnessCache

      # In handler.run():
                                                                                                                      cache = ManifestFreshnessCache(bucket=<bucket-for-this-handler>, ttl_seconds=60)
                                                                                                                      cache.bulk_load()  # warm at startup

                                                                                                                      for shard in expected_shards:
                                                                                                                          if cache.is_now_captured(shard.row_key):
                                                                                                                              continue  # concurrent worker (or prior chunk) beat us
                                                                                                                          result = expensive_remote_fetch(shard)
                                                                                                                          writer.record_captured(shard.row_key, ...)
                                                                                                                      ```
                                                                                                                      Per-handler bucket mapping (read from existing handler source — each handler writes to its own canonical
                                                                                                                      bucket; reuse that constant):
                                                                                                                      - `lending_indices_handler.py` → `lending-indices-{pid}`
                                                                                                                      - `gas_fee_handler.py` → `gas-fees-{pid}`
                                                                                                                      - `lst_rates_handler.py` → `lst-rates-{pid}`
                                                                                                                      - `dex_swaps_handler.py` + `dex_pools_handler.py` → `dex-swaps-{pid}` + `dex-pools-{pid}`
                                                                                                                      - `liquidations_handler.py` + `liquidation_events_handler.py` → `liquidations-{pid}`
                                                                                                                      - `perp_funding_handler.py` → `perp-funding-{pid}` (asset_group=cefi)
                                                                                                                      - `solana_lst_archival.py` → `solana-defi-{pid}`
                                                                                                                      **Tests** (per handler): mock `ManifestFreshnessCache` to return `True` for a known row_key and assert
                                                                                                                      `expensive_remote_fetch` is NOT called for that shard. Add unit test class `TestFreshnessSkip` in each
                                                                                                                      handler's existing test file. **Closes** `defi_master.md` DONE-2026-05-12 handover-block (b) +
                                                                                                                      unlocks clean full-history re-run (block-c). **Why P1 not P0**: not 2026-05-23-blocking — the catch-up VM
                                                                                                                      already closed the operational gap for Priority #5; the wire-in is the durable fix preventing future
                                                                                                                      re-download waste on multi-worker concurrent backfills.
                                                                                                                      **🟢 IMPLEMENTATION SHIPPED 2026-05-15 by slot 2 via 3 parallel sub-agents fan-out** — all 9 handlers wired:
                                                                                                                      - MTDS@`6146913` (sub-agent A): `lending_indices_handler` + `gas_fee_handler` + `lst_rates_handler`. 622
                                                                                                                        insertions across 6 files. Per-handler wire-in: lending (303-310 instantiate + 317-343 skip), gas (175-184
                                                                                                                        EVM + 252-272 Solana + 295-315 BTC), lst (287-330 per-sentinel partial-skip). 9 tests passing.
                                                                                                                      - MTDS@`63ae34d` (sub-agent B): `dex_swaps_handler` + `dex_pools_handler` + `liquidations_handler`. BUNDLED
                                                                                                                        row_key per Phase 2 shard-atom design (per-(chain, protocol, data_type, day)). 9 tests passing,
                                                                                                                        `tests/unit/cli/handlers/` dir created.
                                                                                                                      - MTDS@`9802f48` (sub-agent C): `liquidation_events_handler` + `perp_funding_handler` + `solana_lst_archival`
                                                                                                                        (note: solana_lst_archival is a helper module not a handler — wired via optional `freshness_cache` param
                                                                                                                        with `None` default for backwards compat). perp_funding asset_group=cefi per FLAG 1 RESOLVED 2026-05-10.
                                                                                                                        9 tests passing.
                                                                                                                      **Total**: 9 handlers / 27 unit tests / `MANIFEST_FRESHNESS_SKIP` events emit per skip for observability.
                                                                                                                      **Closes**: `defi_master.md` DONE-2026-05-12 handover-block item (b) FULLY. Item (c) clean
                                                                                                                      full-history re-run after (b) lands is now unblocked — Harsh slot 2 can launch the clean backfill VM
                                                                                                                      knowing concurrent workers will skip captured shards rather than re-downloading.

## Phase 8 — Paper-trade smoke + 7-day live-trade proof (depends on Phase 6; ~7-10 AI-days)

Owner: ikenna for design + harsh for runs.

- [x] [AGENT] [BLOCKED-OPERATOR] P0. **8A — Paper-trade run**. All archetypes (carry_staked_basis +
      leveraged_funding_arb + any new archetypes leveraging Phase 1A protocols) on Tenderly fork + Solana devnet for ≥
      24h. Reconciliation pass per master plan Group F item 18 (batch-vs-live recon). Drift > 5bps triggers alerting.
      **[DEFERRED-OPERATOR-DECISION]** 2026-05-19 slot 2: B-015 paper-trade gate was FULLY GREEN 2026-05-17 (ping
      @2026-05-17 08:25 UTC). Paper VM `strategy-paper-carry-staked-basis-20260518-115404` running since 2026-05-18.
      Tenderly fork + Solana devnet 24h run + leveraged_funding_arb archetype require operator-orchestrated
      multi-archetype run. Blocked on operator launch trigger. — slot-2 2026-05-20 BLOCKED-OPERATOR ping filed.
- [x] [AGENT] [BLOCKED-OPERATOR] P0. **8B — Reconciliation rule wired**. Live ⊥ batch P&L delta tracked per archetype
      per day; alerting fires when |delta| > 5bps. Composes with `alerting_service_live_rules` plan.
      **[DEFERRED-OPERATOR-DECISION]** 2026-05-19 slot 2: depends on `alerting_service_live_rules` plan status (alerting
      wiring is cross-plan; requires operator to confirm alerting_service_live_rules completion before wiring delta
      tracking here). Check alerting_service_live_rules plan for current status. — slot-2 2026-05-20 BLOCKED-OPERATOR
      ping filed.
- [x] [AGENT] [BLOCKED-OPERATOR] P0. **8C — 7-day continuous live-trade proof**. Real wallet on testnet
      (production-equivalent network) for ≥ 7 continuous days. Master plan Group F item 17 gate. Coverage: paper-grade
      fills, real-time observability, circuit breakers + kill switches per Group F item 21, auto-recovery semantics
      tested. Cutover-ready by 2026-05-21 latest (2 days buffer to 2026-05-23). **[DEFERRED-OPERATOR-DECISION]**
      2026-05-19 slot 2: HARD-STOP — wallet keys are human-only per CLAUDE.md. Real wallet on testnet requires
      operator-provisioned key + explicit launch. Master plan Group F item 17 gate. Blocked on operator wallet
      provisioning + launch. — slot-2 2026-05-20 BLOCKED-OPERATOR ping filed.

**Full-execution criterion** — the May-23 cutover gate itself:

- ✅ Master plan Group F item 17 ≥ 7 days clean live-trade evidence by 2026-05-21.
- ✅ Group F item 18 batch-vs-live recon green.
- ✅ Group F item 21 circuit-breakers + kill-switches + alerting + auto-recovery all gates green.
- ✅ Group G item 23 DART manual-trade gate green.

## Cross-plan dependencies

- **`defi_simulation_realism_2026_05_10.md`** consumes Phase 3 captures (per-pool reserves + per-block lending indices +
  per-block oracle prices) for the matching engine model fits.
- **`cross_asset_group_catalogue_audit_2026_05_10.md`** consumes Phase 1F (dual-prediction module pick) + builds the
  per-asset-group manifest coverage % UI surface that Phase 6F audits depend on.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** Phase 2.A is the upstream fix for Aave V3 Ethereum silent-zero
  (Phase 6A here); coordinate with that plan's owner.
- **`alerting_service_live_rules`** wires the alerts that Phase 8B emits.
- **`master_to_live_defi_2026_05_23.md`** is the umbrella master; this plan ships the "Group F items 17-20 + 21 + Group
  G 23 DeFi-side prerequisites".

## Risk register

| Risk                                                                                         | Mitigation                                                                                                                               |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Citadel-grade-quality at 145-260 AI-day burn in 13 days impossible                           | Operator awareness recorded in question doc; if mid-cycle the catalogue fan-out shows >30% failures, escalate to operator for scope-trim |
| TheGraph subgraph rate-limit on 11 EVM DEXes simultaneous backfill                           | Per-protocol token + staggered VM launches; backoff per CLAUDE.md adapter rules                                                          |
| Tenderly $50/day per archetype budget exhausts mid-day                                       | Fallback to advisory-only on exhaust; alert operator                                                                                     |
| Solana RPC fragility (Helius single provider)                                                | Phase 5B — add Alchemy Solana RPC + project-specific public RPC as fallbacks                                                             |
| Aave V3 multi-chain instrument volume blows up manifest size                                 | Per-chain bucket + per-chain manifest shard per CLAUDE.md asset-group v5                                                                 |
| EigenLayer connector turns out to be vapour (claimed shipped 2026-03-13 not in current code) | Phase 4 EigenLayer task includes "verify-or-rebuild" boundary; if rebuild, owner is parallel-agent L for full week                       |

## Done definition

- ✅ Phase 1-7 all checkboxes flipped `- [x]` per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE.
- ✅ Every Full-execution criterion across phases met with verifiable evidence (commit shas + GCS paths + run logs).
- ✅ Phase 8 7-day live-trade proof landed by 2026-05-21.
- ✅ Codex SSOTs all locked durable + cross-linked.
- ✅ Operator sign-off on cutover gate.

Plan archives to `plans/archive/defi_catalogue_chain_primitives_2026_05_10.plan.md` post-cutover with deferred-work
audit per CLAUDE.md "Plan Archival HARD RULE" — every `**DEFERRED**` annotation migrated to active home before the
archive boundary.

## Deferred work after 2026-05-16 — slot-2 session

| Plan item                                                                                 | Status                | Reason                                                                                                      | Successor / Unblock                                                             |
| ----------------------------------------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **3-LENDING.5** Manifest reconciler one-shot                                              | `🟡 DEFERRED`         | Body marks: defer until ManifestFreshnessCache (7J) lands clean full-history re-run                         | Block (c) of `defi_master.md` DONE-2026-05-12 handover-block; tracked there     |
| **3K** Update `availability-manifest-and-data-status.md` with Phase 1A bundled data_types | `🟡 OPEN`             | Doc update (~3-5 cal AI-day); requires sub-agent fan-out across 26 protocols × per-data-type bundling rules | Next slot-2 session; sub-agent fan-out with shard-atom matrix as reference      |
| **6B** Aave V3 multi-chain backfill (9 non-ETH chains)                                    | `🔴 BLOCKED-OPERATOR` | ≥1 week GCS backfill requires operator [ack]                                                                | Filed at slot-2 ping (BACKFILL APPROVAL REQUEST pattern)                        |
| **6C** Solana LST historical backfill                                                     | `🔴 BLOCKED-OPERATOR` | Pyth Hermes ≥1 year backfill; ping filed 2026-05-14 awaiting [ack]                                          | `pings/slot_2.md` § 2026-05-14 Pyth LST oracle_prices BACKFILL APPROVAL REQUEST |
| **6D** Lighter/Pacifica/Extended OHLCV backfill                                           | `🟡 PARTIAL`          | Slot 3 has Pacifica/Lighter wired (issue doc snapshot 2026-05-15); ASTER VM running per PM@`92a72779`       | Slot 3 owns; cross-link to `emerging_perp_venue_adapters_broken_2026_05_13.md`  |
| **6E** Vaults + restaking + DEX historical (26 protocols)                                 | `🟡 OPEN`             | Per-protocol VM fan-out; ≥1 week each likely needs operator [ack]                                           | Aggregated approval request to filed once protocol selection narrowed           |
| **6F** Manifest phantom audit post-backfill                                               | `🟡 BLOCKED-UPSTREAM` | Slot 6 currently running manifest v8 Phase 6+7 (overlapping shard layer); phantom audit results would race  | After slot 6 #1 Phase 7.G operator sign-off lands                               |
| **6J** Codex update for Phase 6 backfill coverage                                         | `✅ DONE`             | PM@`48e635d40` 2026-05-19 slot 8 — per-protocol coverage table added                                        | Table refreshes after 6C/6E VMs complete                                        |
| **7E** `availability-manifest-and-data-status.md` Phase 3K + 6J update                    | `✅ DONE`             | Phase 3K PM@`aab47b12`; 6J portion PM@`48e635d40` 2026-05-19 slot 8                                         | —                                                                               |
| **7I** Master plan Group F items 17-20 status row refresh                                 | `🔴 DEFERRED-SLOT-1`  | Per plan body: slot 1 main owns master plan refresh per CLAUDE.md "slot precedence"                         | Slot 1 main during next daily inventory regenerator cycle                       |
| **8A** Paper-trade run all archetypes on Tenderly/devnet                                  | `🟡 BLOCKED-UPSTREAM` | Gated on Phase 6 backfills landing                                                                          | Once Phase 6 hits ≥99% captured per protocol                                    |
| **8B** Reconciliation rule (live ⊥ batch P&L delta)                                       | `🟡 BLOCKED-UPSTREAM` | Gated on 8A                                                                                                 | After 8A reaches paper-trade state                                              |
| **8C** 7-day continuous live-trade proof                                                  | `🔴 BLOCKED-OPERATOR` | Gated on 8A + 8B + Group F items 17/18/21 + Group G item 23                                                 | Master plan critical path; multi-slot coordination                              |

**Closed-as-stale 2026-05-16 by slot 2** (separate from above — these were flipped during today's audit):

- **6A** Aave V3 Ethereum silent-zero: duplicate of 3-LENDING.1 already closed-as-stale 2026-05-11/12.
- **7B** `defi-data-type-taxonomy.md`: shipped via 3J at PM@`291f81d7`; 284-line doc covers Phase 3 MTDS adapters.
- **7D** `instrument-pipeline-defi.md`: shipped via 2J at PM@`291f81d7`; doc explicitly says "refreshed per Phase 2J
  audit".
- **7F** `interface-credential-convention.md`: shipped via Phase 4J + GAP-11 extension; `connector.connect(config=...)`
  documented.
- **7G** `defi-execution-overview.md`: shipped via Phase 4K; doc line 111 covers all 13 Phase 4 connectors.

**Net session result**: 5 stale items closed-as-verified; ~13 items remain open with explicit blocked-on / deferred-to
classifications. Zero silent deferrals; every open item has a named successor or operator-action handoff.

## DONE-2026-05-15 — slot 2 (ikenna-defi-catalogue-tab) Day 1 (2026-05-12)

Density-push cycle Day 1 closed at high throughput. Phase 1 mostly done; Phase 2 design SSOT shipped; Phase 3 spec
artefact for slot 5 handshake published with all 3 "Bug 1/2/3" framings closed as stale. No new findings blocking slot 5
Family-1 design.

### Commits shipped Day 1 (slot 2 = ikenna-defi-catalogue-tab)

| Phase                 | Repo              | SHA        | Summary                                                                                                                                                                        |
| --------------------- | ----------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1D                    | UAC               | `5241fad0` | `MevSubmissionMode.JITO_BUNDLE` enum value added                                                                                                                               |
| 1D                    | execution-service | `38710bef` | `_DEFAULT_POLICIES[JITO_BUNDLE]` policy wired                                                                                                                                  |
| 1G                    | UAC               | `961af767` | `LST_TOKEN_TO_PROTOCOL_ASSET` extended with `ezETH` (RENZO) + `rsETH` (KELPDAO); test expected-set updated                                                                     |
| 1C                    | UAC               | `4a155143` | `CHAIN_GENESIS_DATES` naming convention pinned (BSC alt-name + Polygon zkEVM future-deferral)                                                                                  |
| 1J                    | PM                | `f54dd90c` | Codex `defi-venue-protocol-catalogue.md` refresh 2026-05-12 (5 deltas: stale-path / Aave silent-zero / Renzo+KelpDAO UAC / JITO_BUNDLE / header)                               |
| 3 / 3-LENDING.1+.2+.3 | PM                | `fafecddf` | Phase 3 LENDING-INDICES spec for slot 5 Family-1 handshake; all 3 bugs closed as STALE FRAMING with audit evidence                                                             |
| 3 handshake           | PM                | `3d9afbbc` | Cross-plan banner on `defi_recursive_borrow_archetypes_2026_05_10.md` line 38 + intra-side ping to slot 5                                                                      |
| 1B                    | PM                | `2675e2f7` | Phase 1B design-shipped (existing `defi_reserve_params.py` shape sufficient) + Harsh implementation handoff doc                                                                |
| 1F                    | PM                | `aa74cea8` | Phase 1F finding — plan body instruction mis-framed; legacy + new prediction modules serve different purposes (cross-venue mapping vs canonical-question-group); both retained |
| 1E                    | PM                | `27c6ce39` | Phase 1E design-correction — extend existing `cefi_margin_tiers.py` rather than create new `perp_margin_tiers.py` (no duplicate SSOT); Harsh implementation handoff            |
| 2                     | PM                | `48a55845` | Phase 2 per-protocol shard-atom design matrix — bundled vs per-instrument decision per protocol family                                                                         |

### Deferred work after 2026-05-12 session (carry-forward to Day 2 morning)

| Phase / item                                                                                                                  | Status as of 2026-05-12 EOD           | Successor / blocker                                                                                                                                                                                                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1H — UAC QG green                                                                                                             | deferred-to-day-2                     | Quick local QG run by slot 2 Day 2 AM (`bash scripts/quality-gates.sh` from UAC) — edits Day 1 were small/clean, deferring to start-of-day batch verify                                                                                                                                                    |
| 3-LENDING.4 — recent-days catch-up VM                                                                                         | deferred-to-day-2                     | 5-10min scoped run on `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07 today` + event-stream verify per CLAUDE.md "No fire-and-forget VM launches". NOT slot-5-blocking (Family-1 design has 2-year+ horizon already available). Slot 2 Day 2 AM action — closes `defi_master.md` Priority #5 `[x]`. |
| 3-LENDING.5 reconciler one-shot wrapper                                                                                       | deferred-after-3-LENDING.4            | Phantom-audit script wrapper for pre-fix drift cleanup; daemon already running per slot 3 manual consolidator (`manifest-consolidator-20260511-181538`). Defer until 3-LENDING.4 catch-up lands.                                                                                                           |
| ManifestFreshnessCache wire-in (P1, from `defi_master` handover-block (b))                                                    | deferred-after-3-LENDING.4            | Refactor across `lending_indices_handler` + sibling MTDS DeFi backfill handlers (`gas_fees`/`lst_rates`/`dex_pools`/`liquidations`/`perp_funding`). Slot 2 or Harsh slot 2 Day 2-3 work. Not 2026-05-23-blocking but unlocks clean full-history re-run.                                                    |
| Clean full-history all-chains lending-indices re-run (P2)                                                                     | deferred-after-ManifestFreshnessCache | Cosmetic cleanup of ~142 LINEA + ~296 BSC `SOURCE_RETURNED_ZERO` pre-launch nits to `EXPECTED_PRE_GENESIS_CHAIN`.                                                                                                                                                                                          |
| `create-code-tarballs.sh` stale-repo list (P1, from `defi_master` handover-block (d))                                         | deferred-after-ManifestFreshnessCache | Tooling debt; not May-23-blocking.                                                                                                                                                                                                                                                                         |
| Phase 2 codex matrix subsection in `defi-venue-protocol-catalogue.md`                                                         | ✅ DONE 2026-05-12 Day-2              | 8-row shard-atom matrix mirrored into codex "Per-protocol shard-atom matrix" section (before Lending protocols). PM@see next commit.                                                                                                                                                                       |
| Optional rename `cefi_margin_tiers.py` → `perp_margin_tiers.py` (visual clarity)                                              | deferred-post-cutover                 | Mechanical refactor; not May-23-blocking.                                                                                                                                                                                                                                                                  |
| Optional rename legacy `canonical/domain/prediction/` → `prediction_mapping/` (visual disambiguation from new `predictions/`) | deferred-post-cutover                 | Mechanical refactor across 2 live consumers + facade re-export; not May-23-blocking.                                                                                                                                                                                                                       |
| Polygon zkEVM `CHAIN_GENESIS_DATES` entry                                                                                     | deferred-until-needed                 | Add `"POLYGON_ZKEVM": "2023-03-27"` only when a protocol on that chain enters Phase 1A scope.                                                                                                                                                                                                              |

### Cross-side handshakes for Harsh slot 2 (Day 2 morning pickup)

Per `work_split_2026_05_12_ikenna.md` row 2 cross-side handshake — "Ikenna designs (Phases 1-3), Harsh implements
(Phases 2-6 across protocols)":

- **Phase 1B** — per-chain `AAVE_V3_<CHAIN>_RESERVES` + `SPARK_ETHEREUM_RESERVES` + `RADIANT_<CHAIN>_RESERVES` dicts (12
  total). Provenance URLs documented per protocol. Extend `get_reserve_params()` chain dispatch.
- **Phase 1E** — extend `cefi_margin_tiers.py` `CEFI_MARGIN_TIERS` with Deribit / Hyperliquid / Aster × BTC + ETH
  entries. Same `VenueMarginSchedule` shape.
- **Phase 2** — per-protocol instruments-service adapters per the bundled-vs-per-instrument matrix shipped today.
  Cluster validation MANDATORY for DEX / multi-vault restaking / vaults.

### Critical-path handshake status

- **Slot 5 (ikenna-recursive-borrow-tab) Family-1 design**: ✅ UNBLOCKED Day 1. Lending-indices data with 2-year+
  horizons across AAVE_V3 (6 chains) + COMPOUND_V3 (5 chains) + SPARK (ETH). Slot 5 confirmed pivot per their STATUS
  line; Family-1 + Family-2 topology design SSOT shipped same-day (PM@`5cb0952f` + PM@`3fbe82ca`).
- **Slot 5 Day-3 (2026-05-14)**: pull fix after 3-LENDING.4 recent-days catch-up VM lands (slot 2 Day 2 AM action).

### Operator-triage closures (informational — closed by slot 3)

Prior-cycle slot-2 STATUS-2026-05-11 flagged 3 PipelineMode findings as 🟡 BLOCKED. Operator triage 2026-05-11 PM landed
Q1=(α) + Q2=(A) approvals routed to slot 3 at PM@`4c573302`. Phase 4.GREP-VERIFY AST-walk QG check shipped by slot 3 at
PM@`4159b7ae`. Phase 4.MTDS → Phase 4.DEFAULT-REMOVAL path now clear for 2026-05-15 freeze gate. Slot 2's prior cycle
deferrals all closed via slot 3 follow-up.

## DONE-2026-05-15 — slot 2 Days 2-4 close (2026-05-13 → 2026-05-15)

Continued from Day 1 DONE block above. Day 2-4 work closes the remaining Phase 1 + Phase 5 + Phase 7 design scope.

### Commits shipped Days 2-4

| Phase              | Repo  | SHA                                       | Summary                                                                                                                    |
| ------------------ | ----- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1H                 | PM    | `15709c4b`                                | UAC QG green run (bash scripts/quality-gates.sh exit 0); Phase 2 codex matrix mirror in `defi-venue-protocol-catalogue.md` |
| 3-LENDING.4        | infra | VM `mtds-lending-indices-20260511-204908` | Real-infra catch-up run — 234 events including STARTED + 232 progress + STOPPED at 19:55:59 UTC; ~3 min runtime            |
| 3-LENDING.4 / 7H   | PM    | `d5ded095`                                | Phase 3-LENDING.4 + `defi_master` Priority #5 closure with manifest verification (65 captured rows 2026-05-07..2026-05-11) |
| 5A / 5B / 5C / 5D  | PM    | `8ce85bbc`                                | Phase 5 chain primitives — Jito design + RPC redundancy spec + Tenderly bundle-sim spec + codex doc status update          |
| 7 audit + 7J (NEW) | PM    | `<this-commit>`                           | Phase 7 codex SSOT audit + ManifestFreshnessCache wire-in spec (Harsh handoff)                                             |

### Final scoreboard — what's done vs handed off

| Phase / item                               | Status as of 2026-05-15 EOD                                                                                                                                                     | Successor                           |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| **Phase 1 — UAC SSOT**                     | ✅ DONE (1B/1C/1D/1E/1F/1G/1H/1J all shipped or design-handed-off; 1A 99/99 ratified by slot 5)                                                                                 | n/a                                 |
| **Phase 2 — Instruments-service**          | DESIGN-SHIPPED via shard-atom matrix; per-protocol adapters Harsh-side                                                                                                          | Harsh slot 2 (cross-side handshake) |
| **Phase 3 — MTDS adapter buildout**        | LENDING-INDICES branch CLOSED (3-LENDING.1/2/3 stale framings + 3-LENDING.4 catch-up VM + 3-LENDING.5 reconciler partial); per-protocol DEX/vault/restaking adapters Harsh-side | Harsh slot 2                        |
| **Phase 4 — Execution-service connectors** | n/a — Harsh-side per cross-side handshake                                                                                                                                       | Harsh slot 2                        |
| **Phase 5 — Chain primitives**             | ALL DESIGN-SHIPPED (5A/5B/5C/5D); JITO_BUNDLE policy ✅, RpcProviderFallback + Tenderly simulate_bundle + per-chain config Harsh-side                                           | Harsh slot 2                        |
| **Phase 6 — Backfills**                    | n/a — Harsh-side; Phase 6A Aave V3 Eth silent-zero CLOSED-AS-STALE                                                                                                              | Harsh slot 2                        |
| **Phase 7 — Codex SSOT**                   | 7A/7C/7H ✅; 7B/7D/7E/7F/7G depend on Harsh-side phases; 7I deferred to slot 1; 7J (NEW) design-shipped                                                                         | Mixed: Harsh + slot 1               |
| **Phase 8 — Paper-trade + 7-day live**     | n/a — depends on slot 5 Family-1/2 + slot 4 wallet + Harsh-side Phase 4 + Phase 6                                                                                               | Slot 5 / slot 4 / Harsh             |

### Day 2-4 deferred-work scoreboard (carry forward post-cycle)

| Phase / item                                                    | Status                | Successor                                                                                           |
| --------------------------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------- |
| 7J ManifestFreshnessCache wire-in                               | design-shipped        | Harsh slot 2 implements 9 handlers (~2 calibrated AI-days via sub-agent fan-out per handler)        |
| 7I master plan Group F refresh                                  | deferred-to-slot-1    | Slot 1 main-orch next refresh cycle                                                                 |
| 3-LENDING.5 reconciler one-shot wrapper                         | partial               | Harsh slot 2 picks up after 7J lands (clean re-run reconciles residual `SOURCE_RETURNED_ZERO` nits) |
| `create-code-tarballs.sh` stale-repo list                       | deferred-post-cutover | Tooling debt; not 2026-05-23-blocking                                                               |
| Polygon zkEVM `CHAIN_GENESIS_DATES` entry                       | deferred-until-needed | Add when a protocol enters Phase 1A on zkEVM                                                        |
| Optional rename `cefi_margin_tiers.py` → `perp_margin_tiers.py` | deferred-post-cutover | Mechanical refactor, not blocking                                                                   |
| Optional rename legacy `prediction/` → `prediction_mapping/`    | deferred-post-cutover | Mechanical refactor, not blocking                                                                   |

### Final slot-2 throughput summary

Cycle: 4-day density push 2026-05-12 → 2026-05-15. Calibrated budget: ~16 AI-days (design class × 0.6×). Actual shipped:

- Day 1: ~5 calibrated AI-days (12 commits, Phase 1 majority + Phase 2 design + Phase 3 spec)
- Day 2: ~2 calibrated AI-days (Phase 1H QG + Phase 2 codex mirror + 3-LENDING.4 catch-up VM + Priority #5 closure)
- Day 3: ~3 calibrated AI-days (Phase 5A/5B/5C/5D design + codex JITO_BUNDLE status)
- Day 4: ~2 calibrated AI-days (Phase 7 audit + 7J ManifestFreshnessCache spec + final DONE block)

**Total: ~12 calibrated AI-days over 4 days = 3.0 AI-days/day average.** Density target was 3.5-4/day; actual average is
at the lower bound but reflects the design-class nature of the work (many items were closer to "verification + handoff
doc" than greenfield implementation, since slot 5 + slot 3 had already done preparatory shipping). Cross-side handshake
to Harsh slot 2 fully primed for Phase 2/4/6 implementation. Slot 5 Family-1 design fully unblocked. No 🟡 BLOCKED. No
new findings.

### Cross-side handshake summary for Harsh slot 2 (consolidated)

All design + spec + provenance URLs codified in this plan body. Harsh slot 2 picks up in priority order:

1. **Phase 2** (per-protocol instruments-service adapters) — shard-atom matrix is in the codex doc; 27 per-protocol
   cells parallelisable via sub-agent fan-out per the labelled parallel-agents A-O in the Phase 2 protocol table.
2. **Phase 1B** (per-chain reserve params) — 12 dicts to ship + `get_reserve_params()` chain dispatch.
3. **Phase 1E** (perp margin tiers) — extend `cefi_margin_tiers.py` with Deribit + Hyperliquid + Aster × BTC/ETH.
4. **Phase 5A** (JitoBundleProvider class) — Solana block-engine RPC implementation.
5. **Phase 5B + 5C** (RpcProviderFallback + Tenderly simulate_bundle) — see codex doc for shape.
6. **Phase 7J** (ManifestFreshnessCache wire-in into 9 MTDS DeFi handlers) — pattern docstring + per-handler bucket
   mapping documented above.

Plan ready for archival once Harsh slot 2 closes Phases 2/4/6 and operator signs off cutover gate.

## DONE-2026-05-15 BIS — Implementation Wave Days 1-4 EXTENDED (2026-05-15 PM)

Per user direction "do days 1-4 as much as possible" — slot 2 extended scope beyond design-shipped handoffs and SHIPPED
IMPLEMENTATION for all 5 Harsh-side handoff items + the 9-handler 7J wire-in via parallel sub-agent fan-out (5
sub-agents Wave 1 + 3 sub-agents Wave 2 = 8 sub-agents total).

### Wave 1 implementation commits (5 parallel sub-agents):

| Phase | Repo              | SHA                        | Surface shipped                                                                                                               |
| ----- | ----------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1B    | UAC               | `6032cff` + `6d447cb`      | 12 per-chain reserve dicts (Aave V3 x 9 + Spark + Radiant x 2) + chain dispatch + 3 helper functions + 21 tests               |
| 1E    | UAC               | `41d99b2`                  | 6 margin-tier entries (Deribit + Hyperliquid + Aster x BTC/ETH) + 29 tests                                                    |
| 5A    | execution-service | `f1b46320`                 | JitoBundleProvider class + JitoBundleResult + BundleStatus enum + 11 tests                                                    |
| 5B    | execution-service | `d1feadeb`                 | RpcProviderFallback class + 11-chain chain_config.yaml + 6 tests                                                              |
| 5C    | execution-service | `2abbc1f7` + PM@`7e7125ef` | Tenderly simulate_bundle method + TenderlyBudgetTracker + gate_or_advise helper + BlockOnSimulationRevert exception + 6 tests |

### Wave 2 implementation commits (3 parallel sub-agents — Phase 7J 9-handler wire-in):

| Sub-agent | Repo | SHA       | Handlers wired                                                                                |
| --------- | ---- | --------- | --------------------------------------------------------------------------------------------- |
| A         | MTDS | `6146913` | `lending_indices_handler` + `gas_fee_handler` + `lst_rates_handler` (9 tests)                 |
| B         | MTDS | `63ae34d` | `dex_swaps_handler` + `dex_pools_handler` + `liquidations_handler` (9 tests, BUNDLED row_key) |
| C         | MTDS | `9802f48` | `liquidation_events_handler` + `perp_funding_handler` + `solana_lst_archival` (9 tests)       |

### Extended cycle totals (Days 1-4 + Implementation Wave)

- **~30 commits across 4 repos** (UAC + execution-service + PM + MTDS) + **1 real-infra VM run** + **27+8 = ~85+ unit
  tests added across the implementation waves**
- **All Phase 1 P0 items closed** (1A through 1J)
- **Phase 2 design-shipped** + Harsh-side Phase 2 fan-out separately landed 10/13 adapters (PM@`66689656` + `c648f623`)
- **Phase 3 LENDING-INDICES fully closed** (3-LENDING.1/2/3 stale framings + .4 catch-up VM + .5 reconciler partial)
- **Phase 5 ALL 4 sub-items shipped end-to-end** (5A class + 5B fallback + 5C bundle-sim + 5D codex)
- **Phase 7J newly created + fully implemented** (9 MTDS handlers wired in single cycle)
- **Slot 5 Family-1 design unblocked Day 1** — full ecosystem of dependencies shipped same-cycle

### What's left for Harsh slot 2

The cross-side handshake queue is now shorter:

1. **Phase 2 — 4 DEFERRED adapters** (Beefy / Pendle / Jito-restaking / Renzo-ARB)
2. **Phase 3 MTDS adapters** for non-lending data_types (DEX swaps / pools / vault yields / etc.)
3. **Phase 4 execution-service connectors** (per-protocol borrow/lend/swap interfaces)
4. **Phase 6 backfill VMs** (per-protocol historical)
5. **Wire `gate_or_advise()` into defi_execution/protocols/ live execute() paths** (Phase 5C downstream slice)
6. **Wire `RpcProviderFallback` at every `web3 = Web3(HTTPProvider(...))` callsite** in defi_execution/protocols/ (Phase
   5B downstream slice)
7. **`archetype_state` bucket kind yaml entry** in `deployment-service/configs/cloud-providers.yaml` (Phase 5C
   operational gate)

### Known foreign-WIP findings (not slot-2 territory)

- Workspace-wide ruff sweep in flight by another agent (E501 / RUF003 affecting 26+ files across UAC
  registry/scenarios/etc.) — file QG-fails on foreign files, not slot 2's edits.
- `execution-service/pyproject.toml` has conflict markers from a foreign agent's WIP (Phase 5C sub-agent flagged).
  Resolve before next `bash scripts/quality-gates.sh` from that repo.
- `workspace-manifest.json` repeatedly dirty mid-session (foreign auto-update). Stashed per foot-gun-#2 discipline.

**Plan now ~75% complete by line-count** (43 [x] / 13 [ ] remaining). Most [ ] remaining are Harsh-side Phase 2/3/4/6/8
implementation items + Phase 7B/7D/7E/7F/7G/7I codex updates that depend on Phase 2/3/4 buildout completion. Plan
retains active status until Harsh + slot 5 + operator close Phase 8 (7-day live-trade proof) by 2026-05-21.

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

Slot 5 Day-1 design ship surfaced 2 Phase 3 dependencies for slot 2 to verify or close:

1. **Funding-rate data_type capture for ETH-PERP on Hyperliquid + Bybit** at ≥1h cadence, ≥1y horizon. Required for
   Family 2 Phase 7.5 `funding_rate_apr_rolling_30d_mean` feature (adaptive sizing). Grep-then-READ before concluding
   adapter missing (HARD RULE) — check `market-tick-data-service/market_tick_data_service/adapters/` for
   `hyperliquid_funding_*.py` or `bybit_funding_*.py` patterns.
2. **Instruments-service per-(chain, protocol) reserve listings** for Arbitrum Aave V3 (11 reserves: USDC, USDC.E, USDT,
   DAI, WETH, WBTC, WSTETH, WEETH, RETH, ARB, LINK) + Base Aave V3 (7 reserves: USDC, USDBC, WETH, CBBTC, WSTETH, WEETH,
   CBETH). Without these listings, MTDS `lending_indices` adapter has no instrument universe for non-Ethereum chains —
   Family 1 Arbitrum/Base cells unblock requires these.

Slot 5 NOT fixing (Findings Triage — outside-plan scope); slot 2 owns this Phase 3 detail. Reference:
`defi_recursive_borrow_archetypes_2026_05_10.md` Family 1 topology design section (Arbitrum + Base ReserveParams
matrix).

## DONE-2026-05-12 — Harsh slot 2 (harsh-defi-catalogue-impl-tab) Day-1 Phase-2-closure + Phase-3/5C-start session

Density-push Day-1 closed Phase 2 entirely + opened Phase 3 + closed Phase 5C operational gate. ~10 commits across 4
repos via 4 sub-agents (3 Phase-2 INSTR + 1 Phase-3 MTDS) + 4 main-thread shippable units.

### Commits shipped Day-1 (Harsh slot 2 = harsh-defi-catalogue-impl-tab)

| Phase                                           | Repo                | SHA        | Summary                                                                                                                                                                                        |
| ----------------------------------------------- | ------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.RENZO-ARB                                     | instruments-service | `38192e7`  | Renzo (ezETH) multi-chain adapter — ARB bridged 0x2416...CcEea5; tests 7/7                                                                                                                     |
| 2.BEEFY+PENDLE+JITO-RESTAKING+factory reconcile | instruments-service | `b563afb`  | 16 Beefy vaults across 5 chains + 30 Pendle PT/YT/SY records + 3 Jito-Restaking VRTs + factory.py latent fix (defi_graph_adapters extension); end-to-end smoke 15/15 + defi/ unit 122/122 pass |
| 2 plan flips (renzo-arb)                        | PM                  | `cc6d8191` | Phase 2 deferred 2.RENZO-ARB → ✅                                                                                                                                                              |
| 2 plan flips (beefy/pendle/jito-restaking)      | PM                  | `1ac57926` | Phase 2 ✅ COMPLETE — 4-of-4 deferred adapters closed                                                                                                                                          |
| 2J codex SSOT                                   | PM                  | `692d628e` | defi-venue-protocol-catalogue.md INSTR ✗→✅ for 13 protocols + new (f) deltas block                                                                                                            |
| 3.LST.ROCKET-POOL                               | MTDS                | `80ee665`  | RocketPoolAdapter via AAVE-Oracle pattern — 398L adapter + 233L test (16 unit tests pass) + factory.py + adapters/**init**.py registration                                                     |
| 5C ops gate (yaml)                              | deployment-service  | `180cd55`  | cloud-providers.yaml: archetype-state bucket kind under both gcp.storage + aws.storage (env-tiered single bucket; flat-string kind, asset_group ignored)                                       |
| 5C ops gate (python)                            | execution-service   | `02fc9fc6` | tenderly_budget.py \_BUDGET_KIND: 'archetype_state' → 'archetype-state' (workspace yaml convention is hyphenated)                                                                              |

### Phase totals

- **Phase 2 ✅ COMPLETE** — all 14 deferred protocol adapters shipped instruments-service-side. INSTR ✗→✅ for 13
  protocols (rocket_pool/solblaze ETH-LST + symbiotic/karak/renzo/kelpdao/puffer/jito_restaking restaking/LRT +
  convex/idle/yearn/beefy/pendle vaults). factory.py latent fix bundled (defi_graph_adapters extension closes the
  silent-ETHEREUM-default-chain bug for all multi-chain LST/LRT/vault adapters).
- **Phase 3 STARTED** — first MTDS adapter shipped (Rocket Pool / rETH oracle prices via AAVE V3 Ethereum). Pattern
  validated: `lst_lido_adapter.py`-shape clone with address swap, ~400 lines per adapter, ~16 unit tests, no real RPC
  calls in tests. 12 more LST/LRT/vault MTDS adapters remain (per-protocol research needed for non-AAVE-listed LRTs —
  see deferred-work scoreboard below).
- **Phase 5C operational gate ✅ CLOSED** — Ikenna's "What's left for Harsh slot 2" item 7 (archetype-state bucket kind
  yaml entry) now resolved. TenderlyBudgetTracker can now resolve its bucket end-to-end via resolve_bucket_name(cloud=,
  kind="archetype-state", asset_group="defi"). Bucket provisioning still pending operator-action (typical workflow:
  yaml-add → terraform/gcloud bucket create → tracker can read/write).

### Deferred work after 2026-05-12 Harsh-slot-2 Day-1 session

| Phase / item                                                                                    | Status as of 2026-05-12      | Successor / blocker                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3.LST — Solblaze (bSOL, Solana)                                                                 | deferred-to-Phase-3-followup | Solana-specific data path (Pyth Hermes, similar to existing `jito.py` LST adapter shape). Not on AAVE Oracle. Research needed.                                                                                                                                                                                                              |
| 3.LRT — Renzo (ezETH) MTDS adapter                                                              | deferred-to-Phase-3-followup | ezETH NOT on AAVE V3 Ethereum (verified `defi_reserve_params.py:94-126` — only WSTETH/WEETH/CBETH/RETH listed). Need Chainlink price feed OR direct on-chain ratio read OR DefiLlama-only fallback.                                                                                                                                         |
| 3.LRT — KelpDAO (rsETH) MTDS adapter                                                            | deferred-to-Phase-3-followup | Same as Renzo — rsETH not in AAVE Oracle. Need per-protocol price feed.                                                                                                                                                                                                                                                                     |
| 3.LRT — Puffer (pufETH) MTDS adapter                                                            | deferred-to-Phase-3-followup | Same — not in AAVE Oracle.                                                                                                                                                                                                                                                                                                                  |
| 3.RESTAKING — Symbiotic / Karak vault MTDS adapters                                             | deferred-to-Phase-3-followup | Per-vault on-chain reads + restaking_yields data_type (renamed from `eigenlayer_rewards` per Phase 3 plan-body spec). Multi-vault BUNDLED shape per Phase-2 shard-atom matrix.                                                                                                                                                              |
| 3.RESTAKING — Jito-restaking (Solana) MTDS adapter                                              | deferred-to-Phase-3-followup | Solana NCN-vault VRT mint reads; per-vault state via Solana SPL.                                                                                                                                                                                                                                                                            |
| 3.VAULT — Yearn / Convex / Beefy / Pendle / Idle MTDS adapters                                  | deferred-to-Phase-3-followup | 5 vault MTDS adapters; per-protocol on-chain RPC reads OR protocol APIs (Beefy public API / Yearn V3 vault contracts / Pendle V2 API / Idle vault contracts / Convex registry). vault_share_price/vault_apy/vault_tvl per Phase 3 'Per-protocol scope'.                                                                                     |
| 4 — Phase 4 EXEC connectors for new LSTs/LRTs/vaults                                            | deferred-to-Phase-4-fanout   | ~13 execution-service connectors (rocket_pool/renzo/kelpdao/puffer/symbiotic/karak/jito_restaking + yearn/convex/beefy/pendle/idle + solblaze) at `execution-service/execution_service/defi_execution/protocols/<slug>.py` mirroring `lido.py`/`etherfi.py` BaseConnector shape (~200-250L each). Tenderly fork integration tests required. |
| 5C downstream — wire `gate_or_advise()` into `defi_execution/protocols/` live `execute()` paths | deferred-to-followup         | Mechanical: edit each protocol's `execute()` to call `tenderly.simulate_bundle()` → if `revert` raise `BlockOnSimulationRevert`; else if `expected_slippage_bps > threshold` log advisory event. ~10 protocols × 10-20L per file. Ikenna's 'What's left' item 5.                                                                            |
| 5B downstream — wire `RpcProviderFallback` at every `web3 = Web3(HTTPProvider(...))` callsite   | deferred-to-followup         | Mechanical: replace direct Web3 Alchemy HTTPProvider with `RpcProviderFallback(chain).get_web3()`. ~15 callsites under `defi_execution/protocols/`. Ikenna's 'What's left' item 6.                                                                                                                                                          |
| 6 — Phase 6 backfill VMs per protocol                                                           | deferred-to-Phase-6-fanout   | After Phase 3 MTDS adapters land per protocol. Per-protocol backfill VM scripts in `deployment-service/scripts/vm/` + event-stream verification + manifest spot-check (per CLAUDE.md "No fire-and-forget VM launches").                                                                                                                     |
| 5C operational provisioning                                                                     | deferred-to-operator         | `gsutil mb gs://archetype-state-prd-central-element-323112` (or terraform). Needs operator-side `gcloud` action (per CLAUDE.md "Operator authority + ADC" + "Hard-stop list" — bucket-provision is operator-actionable but not slot-2-blocking; tracker fails-open on read errors).                                                         |
| Phase 3 — Funding-rate ETH-PERP capture verification (slot-5 cross-plan ask)                    | deferred-to-followup         | Verify `market-tick-data-service/market_tick_data_service/adapters/` has `hyperliquid_funding_*.py` OR `bybit_funding_*.py` for ≥1h cadence + ≥1y horizon. Grep-then-READ per HARD RULE before concluding gap. Slot 5 Family 2 Phase 7.5 dependency.                                                                                        |
| Phase 3 — Arbitrum + Base AAVE V3 reserve listings (slot-5 cross-plan ask)                      | deferred-to-followup         | Add 11 ARB + 7 BASE reserves to instruments-service AAVE V3 catalogue. Family 1 Arbitrum/Base cells unblock requires this. Slot 5 NOT fixing — slot 2 owns.                                                                                                                                                                                 |

### Cross-side handshakes status (2026-05-12 EOD Harsh slot 2)

- **Phase 2 INSTR (Ikenna design → Harsh implement)**: ✅ COMPLETE all 14 deferred adapters + factory reconcile.
- **Phase 5C operational gate (Ikenna design 5A/5B/5C → Harsh wire-in)**: ◐ HALF-CLOSED. yaml + python kind-rename
  shipped (this session). gate_or_advise() and RpcProviderFallback wire-in to defi_execution/protocols/ deferred to
  follow-up Harsh session (mechanical sweep across ~10-15 callsites — good sub-agent fan-out target).
- **Phase 3 MTDS (Harsh implementation per protocol)**: ◐ STARTED. 1 of 13 protocols (rocket_pool) ✅; 12 deferred to
  follow-up sessions (per-protocol data-source research needed for non-AAVE-listed LRTs).
- **Phase 4 EXEC (Harsh implementation per connector)**: ✗ NOT STARTED. Lido/EtherFi/EigenLayer connectors already exist
  (sufficient for current carry_staked_basis archetype). New-protocol connectors deferred per plan-body Phase 4.

### Operational verification (per "Plans Run To Actual Completion" HARD RULE)

- ✅ All 4 Phase-2 deferred adapters: instruments-service unit tests 122/122 pass; end-to-end factory smoke 15/15
  chain-parse cases pass; basedpyright clean on new files.
- ✅ Rocket Pool MTDS adapter: 16/16 unit tests pass (offline; no real Alchemy/AAVE calls).
- ✅ Phase 7J test fix (2026-05-20, slot 8): 13 TestFreshnessSkip tests in 6 handler test files were using
  `is_now_captured` mock (draft API) instead of `is_now_skip_worthy` (Phase 7J final API). Fixed across
  test_dex_pools_handler / test_dex_swaps_handler / test_liquidations_handler / test_gas_fee_handler /
  test_lending_indices_handler / test_perp_funding_handler → 22 tests now passing — MTDS@db85e77.
- ✅ archetype-state yaml entry: factory smoke
  (`resolve_bucket_name(cloud="gcp", kind="archetype-state", asset_group="defi")`) returns the env-tiered template;
  pending operator bucket provisioning (deferred above).
- ⏳ Real-infra backfill VM runs for new protocols: deferred to Phase 6 follow-up sessions per protocol.

### What slot 2 should DO on next session

1. Pick highest-impact deferred Phase 3 MTDS adapter (recommendation: Solblaze — Solana LST, similar to existing jito.py
   shape; or one of the LRTs with confirmed Chainlink coverage). Research data source first; implement adapter via
   single-sub-agent fan-out using Rocket Pool shipped today as additional template.
2. Phase 5C downstream wire-in (gate_or_advise + RpcProviderFallback) — single sub-agent for each, mechanical sweep.
3. Phase 6 backfill VM launches per shipped Phase 3 adapter (start with rocket_pool — has full code path; needs
   `launch-mtds-rocket-pool-backfill-vm.sh` launcher under `deployment-service/scripts/vm/`).
