---
name: defi-catalogue-chain-primitives
overview:
  Full DeFi-protocol catalogue buildout (vaults / lending / LSTs / restaking-LRTs / perp DEXes / spot DEXes) + chain
  primitives (Solana Jito MEV / Tenderly bundle-sim policy / per-chain RPC redundancy / margin-tier tables) for May-23
  cutover per all-in-scope operator directive.
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: ~13 calendar days; ~80-130 AI-days at full multi-agent saturation
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/defi_readiness_catalogue_2026_05_08.md
related_codex:
  - codex/02-data/defi-venue-protocol-catalogue.md
  - codex/02-data/defi-data-type-taxonomy.md
  - codex/05-infrastructure/chain-rpc-mev-tenderly.md
  - codex/04-architecture/interface-credential-convention.md
  - codex/04-architecture/flash-loan-receiver.md
  - codex/04-architecture/mev-protection.md
  - codex/04-architecture/tenderly-execution-provider.md
  - codex/02-data/availability-manifest-and-data-status.md
related_plans:
  - plans/active/defi_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/defi_simulation_realism_2026_05_10.md
  - plans/active/cross_asset_group_catalogue_audit_2026_05_10.md
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
estimate_class: design
estimate_baseline_ai_days: 342.5
estimate_calibrated_ai_days: 205.5
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~3-5, ~30-45, ~30-45, ~25-40, + 4 more). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# DeFi catalogue + chain primitives buildout (May-23 cutover)

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BLOCK)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) § "Anti-sequencing audit" row 334 flags this plan as a Phase 1.E freeze-gate critical-path item. NEW UAC `data_type` enums (`SUPPLY_APY` / `BORROW_APY` / `UTILISATION` / `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` — shipped uac@`d02cce2` per slot 5 audit 2026-05-11) MUST be referenced in `manifest_schema_final_gate_2026_05_09.md` v8 schema declaration BEFORE Phase 1 freeze 2026-05-15. ALL_DEFI_VENUES 74→99 venue declarations shipped uac@`495d262` (slot 5 2026-05-11). Phase 1A still open: per-protocol `SourceCapability` objects + Solana Jito MEV + per-venue margin-tier table + LST_TOKEN_TO_PROTOCOL_ASSET verify. Phase 1 (UAC SSOT extensions) is the SEQUENTIAL gate for Phases 2-6 fan-out. Reader contract: scan top-of-file banners before touching `data_type` column / `BUNDLED_DATA_TYPES` registry / chain primitives / `PROTOCOL_LAUNCH_DATES` / venue-capability tables.

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
[`defi_simulation_realism_2026_05_10.md`](defi_simulation_realism_2026_05_10.md). The cross-asset-group SSOT cleanup +
manifest-coverage-% UI surface lives in
[`cross_asset_group_catalogue_audit_2026_05_10.md`](cross_asset_group_catalogue_audit_2026_05_10.md).

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
  `features-onchain-service/app/calculators/vault_share_price_apy_calculator.py` exists with no upstream.
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
      validation wire-in is automatic via `DataType` StrEnum membership — no extra work. Coordinate
      with [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) Phase 1
      reframed-as-blocker section — that plan no longer ships these; this plan ships them as part of Phase 1.

- [ ] [AGENT] P0. **1A — Extend `defi_venue_capabilities.py`** (`unified-api-contracts/unified_api_contracts/registry/`)
      with entries for: Yearn, Convex, Beefy, Pendle, Idle, Balancer (verify already present), Sushi V2+V3, PancakeSwap
      V3, Camelot V3, Aerodromeq V3, Velodrome V2, TraderJoe V2, Raydium, Orca, Jupiter aggregator, Spark (verify
      already present), Radiant, Rocket Pool, Solblaze, Symbiotic, Karak, Renzo, KelpDAO, Puffer, Jito-restaking.
      Per-entry: `(venue_id, chain_id, data_types, start_date)`. Match shape of existing Aave V3 / Lido entries.
      **PARTIAL 2026-05-11 by slot 5 (ikenna-defi-phase-1e-tab) — venue_id + chain_id + start_date shipped at
      uac@`495d262`** in the **actual SSOT location** `unified_api_contracts/registry/defi_venues.py` (the plan body
      reference to `defi_venue_capabilities.py` is stale — grep-verified that file does not exist; the canonical venue
      registry lives in `defi_venues.py` per the file's own header SSOT pointer to
      `codex/02-data/mtds-data-source-coverage-matrix.md`). Shipped: ALL_DEFI_VENUES extended from 74 → 99 (25 new
      entries — 8 ETH + 7 ARB + 1 BASE + 1 OP + 2 POLY + 1 AVAX + 2 BSC + 3 SOL); DEFI_VENUE_PHASE 1:1 invariant
      preserved with all 25 marked "pipeline"; LEGACY_DEFI_VENUE_ALIASES extended with 13 bare-name aliases;
      `chain_env.py` PROTOCOL_LAUNCH_DATES extended with 12 confident dates (CONVEX/PENDLE/IDLE on ETH,
      SYMBIOTIC/KARAK/RENZO/KELPDAO on ETH, PENDLE/RADIANT on ARB, RADIANT on BSC, JUPITER/JITORESTAKING on SOL);
      `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` extended with 13 pairs (Beefy multi-chain rollouts + YEARNV3 L2 rollouts
      + IDLE/KARAK/RENZO L2 + SOLBLAZE) that fall back to chain genesis until subgraph-truth probe lands.
      **Phase 1B research close-out 2026-05-12 by slot 5 (ikenna-aggressive-may15-tab) — 45 of 46 pending pairs
      shipped @uac@`458f17d` via 5-sub-agent fan-out**: PROTOCOL_LAUNCH_DATES now 98 pairs (was 53);
      `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` reduced to 2 pairs (`(POLYGON, COMPOUNDV3)` — Compound not on Polygon;
      `(SOLANA, SOLBLAZE)` — medium-low confidence pending Solscan pool-creation-tx audit). Per-sub-agent partitioning:
      A (ETH lending/vault, 8) + B (LST/restaking + Solana, 8) + C (Balancer/PancakeSwap/Sushi multi-chain, 9) +
      D (DEX/AMM multi-chain, 9) + E (Beefy/Yearn/Idle/Karak/Renzo, 12) = 46 pairs researched, 45 shipped. Confidence
      tiers: 32 high (primary-source verified) + 11 medium (announcement-anchored) + 2 low (conservative pre-launch
      placeholders for Beefy ETH + Yearn V3 ARB/OPT — flagged for tightening if precision matters). Test fix: 2 BASE
      pairs (BALANCER, SUSHISWAPV3) CLAMPED to BASE chain genesis 2023-08-09 (sub-agent dates pre-dated chain
      mainnet GA). tests/unit/test_protocol_launch_dates.py 19/19 pass.
      **DEFERRED — `data_types` per-venue declarations**: each new protocol's `data_types` matrix (vault_share_price /
      dex_swaps / lending_indices / etc.) is encoded via per-protocol `SourceCapability` objects in
      `registry/capability_declarations/_defi_source_capabilities.py` (currently 5 protocols: UNISWAP / AAVE / etc.).
      Per-protocol `SourceCapability` blocks include `operations`, `base_urls` per env, `operation_details` per env +
      signing scheme + credential type — that's per-adapter research depth, naturally co-shipped with the catalogue
      Phase 2 (instruments adapter) + Phase 3 (MTDS adapter) per-protocol cells (parallel-agent A through O in the
      Phase 2 matrix). Slot 5 venue declarations enable the manifest shard-atom population shape (Phase 2 anti-
      sequencing risk closed); per-protocol SourceCapability adds the data-source contracts (Phase 2-3 scope).
- [x] [AGENT] P0. **1B — Extend `defi_reserve_params.py`** for Spark + Radiant + multi-chain Aave V3 (9 chains × N
      reserves each). Per-asset: LTV, liquidation threshold, liquidation bonus, can-be-collateral, can-be-borrowed,
      borrow cap, supply cap, reserve factor, optimal_utilization_rate, interest-rate-model parameters.
      **DESIGN-SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab); IMPLEMENTATION HANDED TO HARSH SLOT 2**
      per cross-side handshake "Ikenna designs, Harsh implements per protocol" (`work_split_2026_05_12_ikenna.md`).
      Canonical SSOT shape ALREADY in place at
      `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py`:
      `ReserveParams` dataclass (max_ltv / liquidation_threshold / liquidation_bonus / reserve_factor) +
      `EModeCategory` (category_id / label / max_ltv / liquidation_threshold / liquidation_bonus / assets) +
      `AAVE_V3_ETHEREUM_RESERVES` dict (10 assets) + `AAVE_V3_EMODE_CATEGORIES` (ETH_CORRELATED + STABLECOIN) +
      `MORPHO_BLUE_ETHEREUM_RESERVES` (line 352) + `get_reserve_params(asset, chain="ETHEREUM")` already accepts
      `chain` parameter. **Harsh implementation scope** (12 per-chain dicts to ship; ~3 calibrated AI-days via
      sub-agent fan-out per chain):
      `AAVE_V3_ARBITRUM_RESERVES` (https://app.aave.com/reserve-overview/?marketName=proto_arbitrum_v3) +
      `AAVE_V3_OPTIMISM_RESERVES` (proto_optimism_v3) +
      `AAVE_V3_BASE_RESERVES` (proto_base_v3) +
      `AAVE_V3_AVALANCHE_RESERVES` (proto_avalanche_v3) +
      `AAVE_V3_POLYGON_RESERVES` (proto_polygon_v3) +
      `AAVE_V3_BSC_RESERVES` (proto_bnb_v3) +
      `AAVE_V3_LINEA_RESERVES` (proto_linea_v3) +
      `AAVE_V3_SCROLL_RESERVES` (proto_scroll_v3) +
      `AAVE_V3_ZKSYNC_RESERVES` (proto_zksync_v3) +
      `SPARK_ETHEREUM_RESERVES` (https://app.spark.fi/markets) +
      `RADIANT_ARBITRUM_RESERVES` + `RADIANT_BSC_RESERVES` (https://app.radiant.capital).
      Plus extend `get_reserve_params()` chain dispatch from single-dict lookup to per-chain dict-of-dicts. Same
      pattern; same dataclass; primary-source values from Aave/Spark/Radiant governance UIs cross-verified with
      on-chain `getReserveData()` reads. Per-chain E-Mode categories also extend `AAVE_V3_EMODE_CATEGORIES` if
      governance has chain-specific categories (some chains have RWA-collateralised stablecoins as separate
      category). Harsh-side cross-side handshake: pickup Day 2 morning per `work_split_2026_05_12_ikenna.md` row 2.
- [x] [AGENT] P0. **1C — Verify `CHAIN_GENESIS_DATES`** at `chain_env.py:91` covers all 22 chains in scope. Add any
      missing (BNB Chain alt-name normalisation, Polygon zkEVM if distinct from Polygon PoS). Confirm Solana mainnet
      (2020-03-16) is the canonical entry for Solana DeFi.
      **✅ SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)** at UAC@`4a155143`. **Verification result**:
      current table has 21 chains; all 9 Phase 1A in-scope chains present (ETHEREUM / ARBITRUM / OPTIMISM / BASE /
      POLYGON / BSC / AVALANCHE / LINEA / SOLANA). Solana mainnet `2020-03-16` canonical. **No 22nd chain added**:
      grep-verified `POLYGON_ZKEVM` zero references in UAC; not in Phase 1A scope (distinct chain ID 1101 from
      Polygon PoS 137; defer until a protocol enters scope). BSC alt-name (BNB Chain): pinned naming-convention
      comment at top of `CHAIN_GENESIS_DATES` — callers normalise BNB/BNBCHAIN → BSC at entry, no alias key (avoid
      duplicate-entry drift). The "22 chains" target in the plan body's framing is approximate; the actual
      done-state is "all in-scope chains present with naming-convention pinned."
- [x] [AGENT] P0. **1D — Add `MevSubmissionMode.JITO_BUNDLE`** to UAC (`unified_api_contracts/internal/`). Update
      `execution-service/execution_service/v2/mev_router.py` `_DEFAULT_POLICIES` dict with the policy:
      `endpoint_ref="jito_bundle_rpc"`, `bundle_mode="private"`, `max_block_delay=2`, `supported_chains=("solana",)`,
      `private=True`. Endpoint resolved via UCI/Secret Manager at dispatch.
      **✅ SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)**: UAC@`5241fad0` extended
      `MevSubmissionMode` StrEnum at `internal/architecture_v2/enums.py:344` with `JITO_BUNDLE = "JITO_BUNDLE"` (after
      `CUSTOM_PRIVATE_RPC`); execution-service@`38710bef` extended `_DEFAULT_POLICIES` dict at
      `execution_service/v2/mev_router.py:73-80` with exact policy spec from plan
      (`endpoint_ref="jito_bundle_rpc"` / `bundle_mode="private"` / `max_block_delay=2` /
      `supported_chains=("solana",)` / `private=True`). Endpoint ref is a Secret-Manager pointer per existing
      _DEFAULT_POLICIES convention; raw URL never enters source. No tech debt — clean extension of existing dispatch.
- [x] [AGENT] P0. **1E — Per-venue margin-tier table SSOT.** New file
      `unified-api-contracts/unified_api_contracts/registry/perp_margin_tiers.py` declaring
      `PERP_MARGIN_TIERS:     dict[(venue, instrument_type), list[MarginTier]]` for the 6 perp venues. Each tier:
      `(notional_lower, notional_upper, initial_margin_bps, maintenance_margin_bps)`. Per-venue table sourced from venue
      docs (Bybit / Binance / OKX / Deribit) + on-chain constants (Hyperliquid / Aster). Versioned (these change
      occasionally).
      **DESIGN-SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab); IMPLEMENTATION HANDED TO HARSH SLOT 2.**
      **🟡 DESIGN CORRECTION**: NEW file `perp_margin_tiers.py` would DUPLICATE the existing SSOT at
      `unified-api-contracts/unified_api_contracts/registry/cefi_margin_tiers.py` (194 lines; `MarginTier` +
      `VenueMarginSchedule` dataclasses + `CEFI_MARGIN_TIERS: dict[tuple[str, str], VenueMarginSchedule]` with 6
      entries — BINANCE_BTC/ETH, BYBIT_BTC/ETH, OKX_BTC/ETH; + `get_margin_schedule`, `get_margin_tier`,
      `maintenance_margin_for` helpers). Per FLAG 1 RESOLVED 2026-05-10 (`defi_catalogue` Pre-audit § Perp DEXes),
      on-chain perp venues (Hyperliquid / Aster / GMX / Drift / Pacifica / Extended / Lighter) are classified
      under `VENUES_BY_ASSET_GROUP["cefi"]` axis. So `cefi_margin_tiers.py` IS the canonical perp margin-tier SSOT
      for ALL perp venues (CEX + on-chain) — no separate `perp_margin_tiers.py` file needed. Per System-First
      Architecture ("never work around"), extending the existing file is the right design.
      **Harsh implementation scope** (per cross-side handshake `Ikenna designs, Harsh implements`; ~1.5 calibrated
      AI-days):
      Extend `cefi_margin_tiers.py` `CEFI_MARGIN_TIERS` dict with entries for:
      - **Deribit** BTC + ETH (https://www.deribit.com/kb/leverage-and-margin-perpetuals)
      - **Hyperliquid** BTC + ETH (https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-trade-perpetuals)
      - **Aster** BTC + ETH (on-chain constant from `defi_execution/protocols/aster.py` reading
        `getLeverageBracket` per market)
      Optional add for completeness (post-cutover, not May-23-blocking):
      - **GMX V2** BTC + ETH (https://gmx-docs.io/docs/trading/leverage/)
      - **Drift v2** BTC + ETH + SOL (https://docs.drift.trade/trading/leverage)
      Each schedule: same `VenueMarginSchedule` shape as existing entries (sequence of `MarginTier` per notional
      bracket). Per-venue research sources cited in docstring per existing pattern. Optional: rename
      `cefi_margin_tiers.py` → `perp_margin_tiers.py` for visual clarity — DEFERRED (mechanical refactor across 1+
      importer; not May-23-blocking).
- [x] [AGENT] P0. **1F — UAC dual-prediction module pick.** Delete `canonical/domain/prediction/__init__.py` (legacy
      pre-canonical-question-group) AND any references; canonical = `canonical/domain/predictions/` per the
      `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md` SSOT. Workspace-grep audit for
      downstream consumers; update each.
      **🔴 FINDING 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) — PLAN BODY INSTRUCTION MIS-FRAMED; corrected
      via Findings Triage Discipline.** The pre-audit shows `canonical/domain/prediction/` (legacy, singular) and
      `canonical/domain/predictions/` (new, plural) serve **DIFFERENT purposes**, not redundant duplicates:
      - **Legacy `prediction/`** (614 bytes `__init__.py` + 9514 bytes `prediction_mapping.py`) — cross-venue
        mapping. Exports: `CanonicalPredictionMarket`, `MappingRule`, `OrphanDetector`,
        `PredictionMarketCategory`, `PredictionMarketCrossVenueMapping`, `PredictionMarketMapper`. Maps individual
        Polymarket markets to Kalshi market equivalents (1:1 cross-venue dispatch).
      - **New `predictions/`** (canonical_groups.py + classifiers.py + lifecycle.py) — canonical-question-group
        taxonomy. Exports: `CanonicalQuestionGroup` (StrEnum), `CanonicalGroupMetadata`, `MarketLifecycle`,
        `classify_polymarket_to_canonical_group`, `classify_kalshi_to_canonical_group`. Groups markets across
        venues into shared canonical questions (e.g., all "US Election 2024" markets across Polymarket + Kalshi).
      **Real consumers verified workspace-grep**: legacy `prediction/` has 2 live consumers — UAC facade
      `unified_api_contracts/prediction.py` (`from canonical.domain.prediction import *`) +
      `instruments-service/.../adapters/prediction/polymarket.py:25` import. Deleting it would break polymarket
      adapter. **Migration plan SSOT** (`plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`)
      line 459-460 explicitly says the legacy `PredictionMarketCategory` enum **needs alignment with
      CanonicalQuestionGroup**, NOT outright deletion. Migration plan is ARCHIVED — alignment work was
      completed without retiring the legacy module.
      **Decision**: keep BOTH modules; the plan-body instruction was wrong. The cross-venue mapping role of
      legacy `prediction/` is distinct from the canonical-question-group role of new `predictions/`. Phase 1F
      design-shipped as a clarification. Lower-priority cleanup (post-cutover): rename legacy `prediction/`
      → `prediction_mapping/` (to disambiguate from the new module visually), which is mechanical refactor
      across the 2 live consumers + facade re-export — DEFERRED to post-cutover plan since not May-23-blocking.
- [x] [AGENT] P0. **1G — `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT verification.** Confirm presence at the documented location
      (per `defi_master_2026_05_07.md` Phase 9.1A); if missing, add as
      `unified_api_contracts/canonical/domain/predictions/lifecycle.py` sibling for LSTs at
      `canonical/domain/onchain/lst_protocol_mapping.py`. Map: `(lst_token_symbol, chain) → (protocol, base_asset)`.
      **✅ SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)** at UAC@`961af767`. **Actual SSOT location**:
      `unified_api_contracts/internal/domain/defi/lst.py:37` (NOT the plan body's hypothesised
      `canonical/domain/onchain/lst_protocol_mapping.py`; grep-verified that file doesn't exist). **Actual shape**:
      `dict[str, tuple[str, str]]` mapping `token → (protocol, base_asset)` — chain is NOT in the key (multi-chain
      LSTs like wstETH-on-Optimism are the SAME ERC20 token contract bridged; chain dimension lives in
      `instrument_id` + instruments-service `LST_REFERENCE_DATA` registry). Slot 2 extended with restaking LRTs
      (`ezETH` → RENZO/ETH, `rsETH` → KELPDAO/ETH) to cover Phase 1A scope. Symbiotic/Karak DELIBERATELY not added
      (per-vault shares, not a single canonical LRT). Test `test_table_has_all_canonical_lsts` updated; helpers
      `tokens_for_protocol_asset` + `protocol_asset_for_token` already cover the new entries.
- [x] [AGENT] P0. **1H — UAC QG green** (`bash scripts/quality-gates.sh` from UAC repo). All new entries pass
      basedpyright + ruff + Bandit + pytest.
      **✅ SHIPPED 2026-05-13 (Day 2) by slot 2 (ikenna-defi-catalogue-tab)** — full QG run from UAC repo exited 0
      after slot 2's Day-1 Phase 1 edits (MevSubmissionMode.JITO_BUNDLE enum + LST_TOKEN_TO_PROTOCOL_ASSET ezETH/rsETH
      + CHAIN_GENESIS_DATES naming-convention comment + test_lst_protocol_asset.py expected-set extension).
      basedpyright + ruff + Bandit + pytest all green. No regressions from Phase 1 edits.

**Codex SSOT update (Phase 1 boundary)** — per Post-Plan-Phase Codex Audit HARD RULE:

- [x] [AGENT] P0. **1J — Update `codex/02-data/defi-venue-protocol-catalogue.md`** with all 26 protocols added in Phase
      1A. Per-protocol: chain coverage, data_types declared, instruments-service catalog status (Phase 2), MTDS capture
      status (Phase 3), execution connector status (Phase 4), testnet readiness, GCS bucket path, backfill plan
      reference.
      **✅ SHIPPED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)** at PM@`f54dd90c`. Codex doc already comprehensive
      (165 lines, 6 protocol sections + per-chain coverage summary + cross-references + update protocol). 5
      refresh-deltas landed: (a) corrected stale `defi_venue_capabilities.py` references → actual `defi_venues.py`;
      (b) Aave V3 Ethereum silent-zero row flipped to ✅ captured (slot 3 + slot 2 audit closure); (c) Renzo/KelpDAO
      UAC + LST mapping ✅; (d) Solana MEV cell flipped ✅ for JITO_BUNDLE (Phase 1D); (e) header bumped to 2026-05-12
      with delta summary. Remaining ◐/✗ statuses reflect Phase 2/3/4 buildout still in flight (harsh-side per
      cross-side handshake).

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE):

- ✅ UAC `defi_venue_capabilities.py` git-grep returns ≥ 26 new entries.
- ✅ `bash scripts/quality-gates.sh` from `unified-api-contracts/` exits 0 on Phase 1 commit.
- ✅ Workspace-grep for legacy `canonical/domain/prediction/` returns zero hits in non-test code.
- ✅ Codex doc `defi-venue-protocol-catalogue.md` exists + lists every Phase 1A protocol.

## Phase 2 — Instruments-service buildout (PARALLEL × 26 protocols; ~30-45 AI-days at full saturation)

Owner: harsh + parallel agents per protocol.

> **🟢 PHASE 2 PER-PROTOCOL SHARD-ATOM DESIGN — published 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) per
> work_split_2026_05_12 row 2 cross-side handshake "Ikenna publishes per-protocol shard-atom decision by Day 1 EOD
> per protocol family; Harsh starts implementation Day 2 morning".**
>
> **Base shard atom for ALL DeFi protocols** (per
> [`codex/02-data/per-asset-group-bucket-layouts.md`](../../codex/02-data/per-asset-group-bucket-layouts.md) line 69 +
> `unified_api_contracts/canonical/domain/defi/gcs_paths.py`):
> `(date, asset_group=defi, chain, venue, instrument_type, data_type)`. Path:
> `raw_tick_data/by_date/day={date}/asset_group=defi/chain={chain}/venue={v}/instrument_type={it}/data_type={dt}/ticks.parquet`.
>
> **Per-protocol-family refinement** (whether instrument is a row-level column INSIDE the parquet vs hive-partition
> shard axis OUTSIDE; mirrors the predictions/sports multi-axis correction pattern banner from 2026-05-06):
>
> | Protocol family | Per-instrument count | Shard granularity | Instrument axis location | Cluster validation |
> |-----------------|----------------------|-------------------|--------------------------|--------------------|
> | **Lending** (Aave / Spark / Compound / Morpho / Radiant / Fluid) | ~10-20 reserves per (protocol, chain) | **Per-(chain, protocol, asset, data_type, day)** = one manifest row per `(asset, day)` | `asset_symbol` IS a hive shard key (existing pattern at `lending_indices_handler.py`) | Not bundled (each asset is own shard) |
> | **DEX V3 + CLMM** (Uniswap V3 / Sushi V3 / PancakeSwap / Camelot / Aerodromeq / Velodrome / TraderJoe V2 / Balancer / Curve / Raydium / Orca) | 100-1000+ pools per (protocol, chain) | **BUNDLED per-(chain, protocol, data_type, day)** = one manifest row per protocol+chain+day; `pool_address` is row-level column INSIDE parquet | `pool_address` is ROW-LEVEL (NOT hive shard axis) | **MANDATORY** per `UTL.record_captured` — `expected_root_clusters=set_of_pool_addresses` + `cluster_extractor=lambda row: row["pool_address"]` |
> | **DEX V2** (Uniswap V2 / Sushi V2) | smaller pool catalog | Same as DEX V3 — BUNDLED | row-level `pool_address` | MANDATORY |
> | **LST** (Lido / Ether.fi / Rocket Pool / Jito / Marinade / Solblaze + Ethena / Spark sDAI) | 1 token per (protocol, chain) | Per-(chain, protocol, token, data_type, day) — token is the shard atom in 1:1 case | `token_symbol` is hive shard key OR row-level (single-token protocols use hive) | Not bundled (1:1) |
> | **Restaking LRT — single-token** (Renzo ezETH / KelpDAO rsETH / Ether.fi weETH) | 1 token per (protocol, chain) | Same as LST — per-token shard | hive shard key on `token_symbol` | Not bundled |
> | **Restaking — multi-vault** (Symbiotic / Karak / EigenLayer / Puffer / Jito-restaking) | dozens of vaults per (protocol, chain) | **BUNDLED per-(chain, protocol, data_type, day)** = one manifest row per protocol+chain+day; `vault_address` is row-level | row-level `vault_address` | MANDATORY — `expected_root_clusters=set_of_vault_addresses` |
> | **Vaults / yield-aggregator** (Yearn / Convex / Beefy / Pendle / Idle) | 50-200+ vaults per (protocol, chain) | **BUNDLED per-(chain, protocol, data_type, day)** = one row per protocol+chain+day; `vault_address` is row-level | row-level `vault_address` | MANDATORY |
> | **Aggregators** (Jupiter Solana) | n/a (read-only routing) | per-(chain, protocol, data_type, day) — single route registry per day | route is row-level | Not bundled (registry snapshot) |
> | **Perp DEX / on-chain CLOB** (Hyperliquid / Aster / GMX / Drift / Pacifica / Extended / Lighter) | per FLAG 1 RESOLVED 2026-05-10 → classified under `VENUES_BY_ASSET_GROUP["cefi"]` axis | **Per-(venue, instrument, data_type, day)** — same as CEFI venues, NOT DEFI shape | hive shard key on `instrument_id` (per-instrument shard) | Not bundled (per-instrument shard already) |
>
> **Rationale — why BUNDLED for DEX/Vaults/multi-vault Restaking**:
> - Per-pool/per-vault shard would inflate manifest by 100-1000× per (protocol, chain) — 1000 Uniswap V3 pools × 5
>   chains × 4 data_types × 1y days = 7.3M rows per protocol. Across 11 EVM DEX protocols = 80M+ rows. Unmanageable.
> - Bundled per-(chain, protocol, data_type, day) keeps manifest ≤ ~30k rows per DEX protocol per year (5 chains × 4
>   data_types × 365 days × 4 instrument_types).
> - Per-pool/per-vault detail STILL fully recoverable by reading the parquet — `pool_address` / `vault_address`
>   columns survive in parquet rows; row-level filters work for backtest + live reads.
> - Cluster validation at `record_captured()` ensures no silent data loss: `expected_root_clusters` (set of pool
>   addresses we EXPECT in the bundle) + `cluster_extractor` (lambda extracting `pool_address` from each row) gates
>   the write — if any expected pool is missing from the parquet, `MissingClusterValidationError` raises (QG STEP
>   5.64 enforces statically; UTL `record_captured` guard raises at runtime).
>
> **Shard-granularity SSOT compliance** (per
> [`codex/04-architecture/shard-level-failure-isolation.md`](../../codex/04-architecture/shard-level-failure-isolation.md)
> + `plans/epics/infrastructure_master_2026_05_07.md`): shard atom MUST be identical across (a) writer atomicity,
> (b) manifest row key, (c) data-status display, (d) downstream pre-flight gate, (e) deployment-UI drilldown.
> Per the matrix above, the shard atom for each protocol family is documented here as the SSOT; Phase 2 adapter
> implementations MUST honor this matrix; deployment-UI drilldowns roll up to this same granularity.
>
> **Codex SSOT update** (Phase 2 boundary, per HARD RULE Post-Plan-Phase Codex Audit) — slot 2 today extends
> [`codex/02-data/defi-venue-protocol-catalogue.md`](../../codex/02-data/defi-venue-protocol-catalogue.md) with a
> "Per-protocol shard-atom matrix" subsection (Phase 1J refresh) — DEFERRED to Day-2 follow-up commit (this 6-row
> matrix is the canonical content).
>
> **Harsh implementation handoff**: per-protocol Phase 2 adapter authors consume this matrix at adapter-write time.
> The bundled protocols (DEX / multi-vault Restaking / Vaults) MUST pass `expected_root_clusters` +
> `cluster_extractor` kwargs to `record_captured()` per cluster-validation HARD RULE. Single-instance protocols
> (lending / LST / single-token LRT) can omit cluster kwargs.

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

Per-protocol todo template (instantiated 27 times):

- [ ] [AGENT] P0. **2.<X> — `<protocol>` instruments-service adapter** at
      `instruments-service/reference_data/adapters/defi/<protocol>_adapter.py`. Source:
      `<on-chain registry contract     OR off-chain catalog API>`. Output: per-instrument row matching UAC contract from
      Phase 1A. Cluster validation wired (per data_type if bundled). Manifest writes via `record_captured` with
      `expected_root_clusters` + `cluster_extractor` for bundled types.

**Codex SSOT update (Phase 2 boundary)**:

- [ ] [AGENT] P0. **2J — Update `codex/02-data/instrument-pipeline-defi.md`** with the 27 new protocol adapters +
      cluster validation rules per protocol.

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
> (ikenna-defi-catalogue-tab). Day-2 EOD gate to slot 5 Family-1 design (per `work_split_2026_05_12_ikenna.md`
> handshake row).**
>
> **TL;DR for slot 5**: Lending-indices data for Family-1 backtest is **broadly available NOW**. All three "bugs"
> from the original 2026-05-08 framing turned out to be stale at 2026-05-11 audit (slot 3) + 2026-05-12 audit (this
> agent). Slot 5 can START Family-1 design Day-1 using current captured horizons; final tail-end catch-up (5-10min
> VM, scoped) lands Day-2.
>
> **Per-pair capture status** (verified 2026-05-12, sample-inspected at slot 3 audit 2026-05-11):
>
> | Protocol  | Chain    | SUPPLY_APY / BORROW_APY / UTILISATION | Horizon | Slot 5 unblock |
> |-----------|----------|---------------------------------------|---------|----------------|
> | AAVEV3    | ETHEREUM | ✅ captured                           | 2022-03-01 → 2026-05-07 (tail behind today) | ✅ NOW |
> | AAVEV3    | ARBITRUM | ✅ captured (consolidator-confirmed)  | 2022-03-16 → 2026-05-07 | ✅ NOW |
> | AAVEV3    | OPTIMISM | ✅ captured                           | 2022-03-16 → 2026-05-07 | ✅ NOW |
> | AAVEV3    | BASE     | ✅ captured                           | 2023-08-09 → 2026-05-07 | ✅ NOW |
> | AAVEV3    | LINEA    | ✅ captured (slot 3 reclaim 451 rows) | 2025-02-11 → 2026-05-07 | ✅ NOW |
> | AAVEV3    | BSC      | ✅ captured (slot 3 reclaim 836 rows) | 2024-01-23 → 2026-05-07 | ✅ NOW |
> | COMPOUNDV3| ETHEREUM | ✅ adapter wired + dispatched         | 2022-08-13 → present (verify on next consolidator cycle) | ✅ NOW |
> | COMPOUNDV3| ARBITRUM | ✅ adapter wired + dispatched         | 2023-05-04 → present | ✅ NOW |
> | COMPOUNDV3| BASE     | ✅ adapter wired + dispatched         | 2023-08-04 → present | ✅ NOW |
> | COMPOUNDV3| OPTIMISM | ✅ adapter wired + dispatched         | 2024-04-06 → present | ✅ NOW |
> | COMPOUNDV3| SCROLL   | ✅ adapter wired                      | 2024-04-22 → present | ✅ NOW |
> | COMPOUNDV3| POLYGON  | ⛔ INTENTIONALLY EXCLUDED — Compound V3 not deployed on Polygon (`SUBGRAPH_IDS` no POLYGON entry per `chain_env.py:218`) | n/a | n/a |
> | SPARK     | ETHEREUM | ✅ adapter wired (`_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3"]`) | 2023-05-09 → present | ✅ NOW |
>
> **Family-1 backtest data envelope** (slot 5 plan dependency): ≥2-year window of SUPPLY_APY / BORROW_APY /
> UTILISATION for Aave V3 + Compound V3 on Ethereum / Arbitrum / Base. **Met** for all 3 chains; per-pair launch
> dates per `PROTOCOL_LAUNCH_DATES` (`chain_env.py:204-221`).
>
> **Remaining Day-2 work** (does NOT block slot 5 Family-1 design — slot 5 pulls fix Day 3):
> - (a) Recent-days catch-up `2026-05-07..today` (~5-10min scoped VM via
>   `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07 today`) — closes the 5-day tail-end gap.
> - (b) [P1] `ManifestFreshnessCache` wire-in (refactor; not Family-1-blocking — slot 5 reads what's captured today).
> - (c) [P2] Clean full-history all-chains re-run after (b) lands (cosmetic; cleans the ~142 LINEA +
>   ~296 BSC `SOURCE_RETURNED_ZERO` pre-launch nits to `EXPECTED_PRE_GENESIS_CHAIN`).
> - (d) [P1] `create-code-tarballs.sh` stale-repo list (tooling debt; not Family-1-blocking).
>
> **What slot 5 should DO on Day 1** (2026-05-12):
> 1. Read `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 1 reframed-as-blocker section + AD-1 through AD-6.
> 2. Start Family-1 design (orchestrator config schema + per-chain dispatch + recursion params + flash-vs-persistent
>    mode toggle) using the data envelope above.
> 3. Sample parquet probe (gcs-cat) for 1 row of AAVEV3 ETHEREUM SUPPLY_APY @ `2024-01-15` to verify non-NaN value
>    BEFORE committing to backtest harness shape. (Slot 3's 2026-05-11 audit confirmed parquet shape is real, but
>    re-verify for Family-1's specific data_type subset.)
> 4. Day 3 (2026-05-14): pull fix — re-fetch latest manifest state including recent-days catch-up (a).
>
> ---
>
> - [x] [MTDS] P0. **3-LENDING.1 — Bug 1: Aave V3 Ethereum silent-zero**. Audit `adapters/aave_v3_lending_rates.py`:
>       when subgraph returns zero rows, current behaviour writes `empty_confirmed`. Per CLAUDE.md "Honest absence vs
>       fake placeholders" — should classify per the 4-category tree: if catalog says alive AND day in coverage, attempt
>       failed → `record_failed` with typed reason; only legitimate empties get `empty_confirmed`.
>       **✅ CLOSED AS STALE FRAMING 2026-05-11 by slot 3 + verified 2026-05-12 by slot 2.** Per
>       `defi_master_2026_05_07.md` DONE-2026-05-12 block: "routing config absent" framing was stale; data exists
>       on-disk (LINEA 2025-03-01 = 475 real rows, BSC 2024-06-01 = 316 real rows — NOT 1440-NaN placeholders). The
>       actual gap was operational (canonical manifest stale vs per-VM shards) — closed by slot 3 manual
>       consolidator + Case-5 bucket fix (deployment-service@`ad4d448`, slot 6@`2a76a2a`). Aave V3 Ethereum 0/343
>       silent-zero specifically: slot 3 confirmed the ~576 stale "404 GET https" `attempted_failed` rows reclaimed.
>       No code change needed — root cause was consolidator dispatch + per-VM shard reconciliation, not adapter
>       classification.
> - [x] [MTDS] P0. **3-LENDING.2 — Bug 2: Compound V3 multi-chain subgraph routing**. Compound V3 has separate subgraphs
>       per chain (Ethereum / Arbitrum / Base). Adapter must dispatch per chain; per-chain failures are isolated.
>       **✅ CLOSED AS STALE FRAMING 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) — pre-audit verified at
>       MTDS `cli/handlers/lending_indices_handler.py:90` (`_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3"]`)
>       + per-chain dispatch via `chains_override or get_supported_chains_for_protocol(protocol)` loop. The
>       "2026-05-07 COMPOUND_V3 ARB/BASE/OPT" empty-routing bug referenced in the handler's comment was already fixed
>       upstream. Per-chain failures isolated via `record_failed`/`record_empty` per shard. SUBGRAPH_IDS map at MTDS
>       `subgraph_service.py` covers ETHEREUM + ARBITRUM + BASE + OPTIMISM + SCROLL; POLYGON intentionally excluded
>       (Compound V3 not on Polygon — confirmed at UAC `chain_env.py:218`).
> - [x] [MTDS] P0. **3-LENDING.3 — Bug 3: instruments-store 2022 metadata floor**. Aave V3 mainnet launched 2022-03-01;
>       instruments-store currently lacks pre-March-2022 dates as `expected_unattempted`. Add
>       `LENDING_INDICES_COVERAGE_START` per (protocol, chain) to UAC.
>       **✅ CLOSED AS STALE FRAMING 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab) — pre-audit verified at UAC
>       `chain_env.py:144-225` `PROTOCOL_LAUNCH_DATES` dict, which already covers exactly the (chain, protocol)
>       → launch-date semantic the plan body asked for `LENDING_INDICES_COVERAGE_START` to provide. Per
>       `lending_indices_handler.py:322` the handler reads
>       `get_protocol_launch_date(chain, venue_prefix)` and short-circuits to `expected_unattempted` for pre-launch
>       dates (per MTDS@`c6bdf96`). Pairs covered: `(ETHEREUM, AAVEV3)` 2022-03-16, `(ETHEREUM, COMPOUNDV3)`
>       2022-08-13, `(ETHEREUM, SPARK)` 2023-05-09, etc. — full per-chain matrix already in the registry; slot 5
>       confirmed 45/46 pending-pairs shipped 2026-05-12 at UAC@`458f17d`. No separate
>       `LENDING_INDICES_COVERAGE_START` constant needed (single PROTOCOL_LAUNCH_DATES SSOT covers it).
> - [x] [VM] P0. **3-LENDING.4 — Lending-indices backfill VM**.
>       `deployment-service/scripts/vm/launch-defi-lending-indices-backfill-vm.sh` (new launcher per VM-launcher-SSOT
>       rule). Per CLAUDE.md "Plans Run To Actual Completion" — backfill VM must run to completion with
>       manifest-verified coverage 2022-03-01 → present before Phase 3 reports done. Recursive-borrow Phase 9 gates on
>       this.
>       **✅ SHIPPED 2026-05-13 (Day 2) by slot 2 (ikenna-defi-catalogue-tab)** — recent-days catch-up VM
>       `mtds-lending-indices-20260511-204908` launched via `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07
>       2026-05-13` in `asia-northeast1-c` (e2-standard-4 + 50GB). Lifecycle observed via
>       `gs://central-element-323112-events/events/market-tick-data-service/2026-05-11/mtds-lending-indices-20260511-204908/hour=19/`:
>       234 events including STARTED + ~232 progress events + STOPPED at 19:55:59 UTC. VM auto-deleted on
>       completion (shutdown_on_completion=true). Total runtime ~3 minutes for 7-day window.
>       **Manifest verification**: read `gs://lending-indices-central-element-323112/_index/availability_index.parquet`
>       — 65 captured rows for 2026-05-07..2026-05-11 (13/day across AAVEV3 × 6 chains + COMPOUNDV3 × 5 chains +
>       SPARK × 1 chain = 12 protocol-chain combos). 2026-05-12+ → `empty_confirmed` (legitimate — The Graph
>       subgraphs lag ~1 day behind real-time; not a data gap). **Priority #5 in `defi_master_2026_05_07.md`
>       cleared** — slot 3's handoff item (a) "Recent-days catch-up" done.
>
> Original PARTIAL annotation from 2026-05-11 by slot 3 retained for provenance:
> launcher exists at
>       `deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh` (verified at slot 3 status note);
>       2026-05-11 full-history backfill VM `mtds-lending-indices-20260511-181115` killed at ~3373 events / ~375 dates
>       (operator decision — `lending_indices_handler` re-downloads already-`captured` data; no manifest-freshness
>       skip). **Remaining work**: (a) recent-days catch-up `2026-05-07..today` 5-10min scoped run with event-stream
>       verification (`STARTED+progress+STOPPED`); (b) ManifestFreshnessCache wire-in (P1 from
>       `defi_master_2026_05_07.md` DONE-2026-05-12 block § Discoveries during Priority #5); (c) clean full-history
>       re-run after (b) lands. **Slot 5 Family-1 design NOT blocked** — pulls fix Day 3 per spec above.
> - [ ] [SCRIPT] P0. **3-LENDING.5 — Manifest reconciler one-shot**.
>       `instruments-service/scripts/reconcile_lending_indices_phantom.py` to clean any phantom-captured rows from
>       pre-fix runs.
>       **PARTIAL 2026-05-11 by slot 3** — manual `manifest_consolidator --bucket lending-indices-{pid} --once`
>       executed; canonical now AAVEV3/LINEA = 451 captured + AAVEV3/BSC = 836 captured. Consolidator-bucket Case-5
>       fix shipped (deployment-service@`ad4d448` + slot 6@`2a76a2a`); daemon `manifest-consolidator-20260511-181538`
>       relaunched and verified consolidating lending-indices/dex-swaps/evm-defi/etc on first cycle. **Remaining
>       work**: phantom-audit script wrapper (not the daemon — the one-shot scripted reconciler for pre-fix
>       drift cleanup). Defer until ManifestFreshnessCache (P1 from (b) above) lands — clean re-run will reconcile
>       residual `SOURCE_RETURNED_ZERO` pre-launch nits to `EXPECTED_PRE_GENESIS_CHAIN`.

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

Per-protocol todo template:

- [ ] [AGENT] P0. **3.<X> — `<protocol>` MTDS adapter.** TheGraph subgraph (EVM) or RPC poller (Solana, Pyth) source.
      Captures per-tick or per-block data per UAC Phase 1A data_types. Manifest writes via
      `ManifestWriter.record_captured` with all 4 capture states wired. Per-protocol cluster validation if bundled
      data_type.

**Codex SSOT updates (Phase 3 boundary)**:

- [ ] [AGENT] P0. **3J — Update `codex/02-data/defi-data-type-taxonomy.md`** (NEW) with full per-venue data-type matrix.
- [ ] [AGENT] P0. **3K — Update `codex/02-data/availability-manifest-and-data-status.md`** with new bundled data_types
      from Phase 1A.

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

- [ ] [AGENT] P0. **4.<X> — `<protocol>` execution-service connector.** Implements credential-injection per
      `codex/04-architecture/interface-credential-convention.md`. Error classification via UAC
      `classify_venue_error()` + `DefiErrorCode` (extend taxonomy if new revert reasons). Tenderly fork integration test
      green (per `tests/defi_execution/integration/conftest.py` shape). Testnet validation (Sepolia / devnet).

**Codex SSOT update (Phase 4 boundary)**:

- [ ] [AGENT] P0. **4J — Update `codex/04-architecture/interface-credential-convention.md`** with new connectors'
      credential shapes.
- [ ] [AGENT] P0. **4K — Update `codex/04-architecture/defi-execution-overview.md`** with connector inventory.

**Full-execution criterion**:

- ✅ Every connector has ≥ 1 Tenderly-fork integration test passing.
- ✅ Each connector has ≥ 1 testnet tx (Sepolia/Holesky/devnet) successfully placed (recorded in test logs).
- ✅ `DefiErrorCode` taxonomy extended with new revert codes; per-code `FAIL/RETRY/SKIP` routing declared.

## Phase 5 — Chain primitives (PARALLEL with 2-4; ~5-10 AI-days)

Owner: ikenna for design + harsh for implementation.

- [x] [AGENT] P0. **5A — Solana Jito bundle submission**. New file
      `execution-service/execution_service/defi_execution/mev/jito_bundle.py` implementing `JitoBundleProvider` per the
      `flashbots.py` / `private_mempool.py` shape. Submits Solana tx bundles via Jito block-engine RPC. Wired into
      `mev_router.py` per Phase 1D.
      **PARTIAL — design-shipped via Phase 1D 2026-05-12 by slot 2** (UAC@`5241fad0` + execution-service@`38710bef`):
      `MevSubmissionMode.JITO_BUNDLE` enum value + `_DEFAULT_POLICIES[JITO_BUNDLE]` policy entry shipped
      (endpoint_ref=`jito_bundle_rpc`, bundle_mode=private, max_block_delay=2, supported_chains=(solana,), private=True).
      **REMAINING (Harsh-side implementation)**: `JitoBundleProvider` class at
      `execution-service/execution_service/defi_execution/mev/jito_bundle.py` mirroring the `PrivateMempoolProvider`
      shape at `execution-service/execution_service/defi_execution/mev/private_mempool.py`. Submits via Jito block-engine
      RPC (`https://mainnet.block-engine.jito.wtf/api/v1/bundles`). Bundle = 1-5 Solana transactions with a tip
      transaction included for prioritisation. Endpoint URL + tip-account pubkey resolved via UCI/Secret Manager.
      Authentication: optional paid Jito subscription OR free with rate limits.
- [x] [AGENT] P0. **5B — Per-chain RPC redundancy**. Update
      `execution-service/execution_service/config/chain_config.yaml` (or equivalent) to declare ≥ 2 independent RPC
      providers per chain in scope (Alchemy + Infura + QuickNode + Ankr + Helius for Solana + project-specific public
      RPC). Add `RpcProviderFallback` class that auto-fails-over on connection-drop / 429 / 5xx within configurable
      retry budget.
      **DESIGN-SHIPPED 2026-05-13 (Day 3) by slot 2 — IMPLEMENTATION HANDED TO HARSH SLOT 2.** Design SSOT lives in
      [`codex/05-infrastructure/chain-rpc-mev-tenderly.md`](../../codex/05-infrastructure/chain-rpc-mev-tenderly.md)
      § "RPC provider redundancy" (lines 36-63) — pre-existing codex content from Phase 5D already specifies the exact
      `chain_config.yaml` shape (per-chain `primary: <provider>` + `fallbacks: [<provider1>, <provider2>]` +
      `fallback_policy: auto-failover-on-5xx-or-429` + `retry_budget: 3`). **Harsh implementation scope** (~2
      calibrated AI-days):
      - Create `execution-service/execution_service/config/chain_config.yaml` with per-chain stanza per the codex
        template. Chains in May-23 scope: ETHEREUM / ARBITRUM / OPTIMISM / BASE / POLYGON / AVALANCHE / BSC / LINEA /
        SCROLL / ZKSYNC / SOLANA. Each with ≥ 2 fallback providers per the per-chain matrix at codex doc lines 18-31.
      - Add `RpcProviderFallback` class at
        `execution-service/execution_service/providers/rpc_fallback.py` (NEW). Public surface: `class
        RpcProviderFallback: def __init__(chain: str, config_path: Path); def execute(method: str, params: list)
        -> Any` with auto-failover on `httpx.ConnectError | httpx.TimeoutException | (status_code in {429, 500,
        502, 503, 504})` within `retry_budget`. Emits `RPC_PROVIDER_FAILOVER` events per CLAUDE.md "No fire-and-
        forget VM launches" event-stream contract.
      - Wire `RpcProviderFallback` at every `web3 = Web3(HTTPProvider(...))` callsite in defi_execution/protocols/.
      - Tests: `pytest execution-service/tests/unit/providers/test_rpc_fallback.py` — simulate primary down +
        verify secondary picks up; verify event emission; verify `RuntimeError` after retry_budget exhausted.
- [x] [AGENT] P0. **5C — Tenderly bundle-sim API + gating policy**. Extend
      `execution-service/execution_service/providers/tenderly.py` with `simulate_bundle()` method using Tenderly's
      `/api/v1/account/{slug}/project/{slug}/simulate-bundle` endpoint. Wire pre-flight gating in execution-service
      handlers: every live order goes through bundle-sim, BLOCK on revert, advisory-log on slippage>threshold. Default
      per-archetype daily Tenderly budget = $50/day per archetype (operator-set ceiling); 1 sim per live order. Budget
      exhaustion downgrades to advisory-only.
      **DESIGN-SHIPPED 2026-05-13 (Day 3) by slot 2 — IMPLEMENTATION HANDED TO HARSH SLOT 2.** Design SSOT lives in
      [`codex/05-infrastructure/chain-rpc-mev-tenderly.md`](../../codex/05-infrastructure/chain-rpc-mev-tenderly.md)
      § "Tenderly setup" (lines 91-126) — pre-existing codex content from Phase 5D specifies the API key flow (Secret
      Manager `tenderly_api_key`), bundle-sim endpoint shape, and per-archetype $50/day budget policy.
      **Harsh implementation scope** (~1.5 calibrated AI-days):
      - Extend `execution-service/execution_service/providers/tenderly.py` (verify exists; if not, create) with
        `simulate_bundle(transactions: list[TenderlyTx], chain_id: int) -> BundleSimResult` calling Tenderly's
        `POST /api/v1/account/{slug}/project/{slug}/simulate-bundle` endpoint. `BundleSimResult` dataclass: `revert:
        bool` + `revert_reason: str | None` + `expected_slippage_bps: int` + `gas_used: int`.
      - Wire pre-flight gating in defi_execution/protocols/ — every `execute()` method on a live (non-paper-trade)
        order: `bundle_sim = tenderly.simulate_bundle(...)` → if `bundle_sim.revert` raise `BlockOnSimulationRevert(...)`;
        if `bundle_sim.expected_slippage_bps > threshold` log advisory event.
      - Per-archetype daily Tenderly budget tracked in
        `unified-cloud-interface/secret_budget_tracker.py` (NEW or extend existing rate-limit primitive). Budget
        exhaustion → degrade to `advisory-only` mode (logs but doesn't block).
      - Tests: `pytest execution-service/tests/unit/providers/test_tenderly_bundle_sim.py` — mock Tenderly responses
        for (a) clean simulate; (b) revert → assert BlockOnSimulationRevert raised; (c) high-slippage → assert
        advisory event emitted; (d) budget exhaustion → assert downgrade behaviour.
- [x] [AGENT] P0. **5D — Codex SSOT** at `codex/05-infrastructure/chain-rpc-mev-tenderly.md` (NEW) with full per-chain
      table: RPC primary + fallback, MEV-protected RPC, gas oracle source, Tenderly account/project, historical capture
      bucket.
      **✅ SHIPPED — already exists at
      [`codex/05-infrastructure/chain-rpc-mev-tenderly.md`](../../codex/05-infrastructure/chain-rpc-mev-tenderly.md)
      (204 lines).** Audit 2026-05-13 by slot 2 confirms doc covers: per-chain matrix (11 chains in May-23 scope +
      StarkNet); RPC provider redundancy spec with `chain_config.yaml` template; MEV protection per chain (5
      MevSubmissionMode endpoint registry rows + per-chain MEV story); Tenderly setup (account / project / budget /
      bundle-sim API gating); Gas oracles per chain; Oracle prices per chain; Cross-references; Update protocol.
      **JITO_BUNDLE row** in MEV registry (line 77) correctly marked as Phase 5A buildout. **MINOR DELTA Day 3**:
      slot 2 should add a note line that JITO_BUNDLE enum + `_DEFAULT_POLICIES` policy shipped Phase 1D 2026-05-12
      so the Status column for that row flips to ◐ (enum + policy ✅, provider class pending Harsh implementation).
      Deferred to a separate codex-doc-touch commit to keep this checkbox flip clean.

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

- [ ] [AGENT] P0. **6A — Aave V3 Ethereum silent-zero diagnose + re-run**. Per writegate Phase 2.A; root-cause the
      0/343-shards bug, fix at MTDS adapter, re-run via launcher
      `deployment-service/scripts/vm/launch-mtds-lending-indices-vm.sh`. Coverage end-state: ≥ 99% captured by
      2026-05-13.
- [ ] [AGENT] P0. **6B — Aave V3 multi-chain backfill** (9 non-Ethereum chains × N reserves × dates). Launcher
      `launch-mtds-lending-multichain-vm.sh` (NEW); per-chain VM with `MANIFEST_PER_VM_SHARDS=true` +
      `VM_NAME=aave-multi-<chain>-<ts>`.
- [ ] [AGENT] P0. **6C — Solana LST historical** (jitoSOL / mSOL / bSOL / Rocket Pool / Solblaze) — Pyth Hermes backfill
      2023-10-01 → today. Launcher `launch-mtds-solana-lst-vm.sh` (NEW).
- [ ] [AGENT] P0. **6D — Lighter / Pacifica / Extended OHLCV backfill** + contract addresses + ABI parsing completion.
      Launcher `launch-mtds-defi-perp-backfill-vm.sh`.
- [ ] [AGENT] P0. **6E — Vaults + restaking + DEX historical** for all 26 Phase 1A protocols. Per-protocol VM where TVL
      × dates × instruments justifies (default: 2-year backfill). Launchers under `deployment-service/scripts/vm/`.
- [ ] [AGENT] P0. **6F — Manifest phantom audit** post-backfill. Run
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi` per CLAUDE.md § Manifest
      phantom audit; surface any drift.

**Codex SSOT updates (Phase 6 boundary)**:

- [ ] [AGENT] P0. **6J — Update `codex/02-data/availability-manifest-and-data-status.md`** with the new protocol capture
      coverage + manifest health % per asset_group post-backfill.

**Full-execution criterion**:

- ✅ Every Phase 1A protocol has ≥ 1 captured shard in production GCS bucket per manifest.
- ✅ Per-asset-group manifest coverage ≥ 99% for in-scope (asset_group, venue, data_type, day) cells.
- ✅ Phantom audit shows zero drift between manifest + on-disk parquets.
- ✅ Sample parquet inspection (5 random captures per protocol) shows populated rows.

## Phase 7 — Codex SSOT updates (continuous; per-phase boundaries above; final lock at end)

Per "Post-Plan-Phase Codex Audit HARD RULE" — every major phase boundary triggers codex update in same logical unit as
code commit. End-of-plan check: every codex doc reflects shipped state.

- [ ] [AGENT] P0. **7A — `codex/02-data/defi-venue-protocol-catalogue.md`** (NEW; Phase 1J). Final lock at Phase 8.
- [ ] [AGENT] P0. **7B — `codex/02-data/defi-data-type-taxonomy.md`** (NEW; Phase 3J). Final lock at Phase 8.
- [ ] [AGENT] P0. **7C — `codex/05-infrastructure/chain-rpc-mev-tenderly.md`** (NEW; Phase 5D). Final lock at Phase 8.
- [ ] [AGENT] P0. **7D — `codex/02-data/instrument-pipeline-defi.md`** (UPDATE; Phase 2J).
- [ ] [AGENT] P0. **7E — `codex/02-data/availability-manifest-and-data-status.md`** (UPDATE; Phase 3K + 6J).
- [ ] [AGENT] P0. **7F — `codex/04-architecture/interface-credential-convention.md`** (UPDATE; Phase 4J).
- [ ] [AGENT] P0. **7G — `codex/04-architecture/defi-execution-overview.md`** (UPDATE; Phase 4K).
- [ ] [AGENT] P0. **7H — `defi_master_2026_05_07.md`** body — gap-fill priorities + per-archetype readiness matrix
      refreshed.
- [ ] [AGENT] P0. **7I — `master_to_live_defi_2026_05_23.md`** Group F items 17-20 status rows refreshed.

## Phase 8 — Paper-trade smoke + 7-day live-trade proof (depends on Phase 6; ~7-10 AI-days)

Owner: ikenna for design + harsh for runs.

- [ ] [AGENT] P0. **8A — Paper-trade run**. All archetypes (carry_staked_basis + leveraged_funding_arb + any new
      archetypes leveraging Phase 1A protocols) on Tenderly fork + Solana devnet for ≥ 24h. Reconciliation pass per
      master plan Group F item 18 (batch-vs-live recon). Drift > 5bps triggers alerting.
- [ ] [AGENT] P0. **8B — Reconciliation rule wired**. Live ⊥ batch P&L delta tracked per archetype per day; alerting
      fires when |delta| > 5bps. Composes with `alerting_service_live_rules` plan.
- [ ] [AGENT] P0. **8C — 7-day continuous live-trade proof**. Real wallet on testnet (production-equivalent network) for
      ≥ 7 continuous days. Master plan Group F item 17 gate. Coverage: paper-grade fills, real-time observability,
      circuit breakers + kill switches per Group F item 21, auto-recovery semantics tested. Cutover-ready by 2026-05-21
      latest (2 days buffer to 2026-05-23).

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

## DONE-2026-05-15 — slot 2 (ikenna-defi-catalogue-tab) Day 1 (2026-05-12)

Density-push cycle Day 1 closed at high throughput. Phase 1 mostly done; Phase 2 design SSOT shipped; Phase 3 spec
artefact for slot 5 handshake published with all 3 "Bug 1/2/3" framings closed as stale. No new findings blocking
slot 5 Family-1 design.

### Commits shipped Day 1 (slot 2 = ikenna-defi-catalogue-tab)

| Phase | Repo | SHA | Summary |
|-------|------|-----|---------|
| 1D | UAC | `5241fad0` | `MevSubmissionMode.JITO_BUNDLE` enum value added |
| 1D | execution-service | `38710bef` | `_DEFAULT_POLICIES[JITO_BUNDLE]` policy wired |
| 1G | UAC | `961af767` | `LST_TOKEN_TO_PROTOCOL_ASSET` extended with `ezETH` (RENZO) + `rsETH` (KELPDAO); test expected-set updated |
| 1C | UAC | `4a155143` | `CHAIN_GENESIS_DATES` naming convention pinned (BSC alt-name + Polygon zkEVM future-deferral) |
| 1J | PM | `f54dd90c` | Codex `defi-venue-protocol-catalogue.md` refresh 2026-05-12 (5 deltas: stale-path / Aave silent-zero / Renzo+KelpDAO UAC / JITO_BUNDLE / header) |
| 3 / 3-LENDING.1+.2+.3 | PM | `fafecddf` | Phase 3 LENDING-INDICES spec for slot 5 Family-1 handshake; all 3 bugs closed as STALE FRAMING with audit evidence |
| 3 handshake | PM | `3d9afbbc` | Cross-plan banner on `defi_recursive_borrow_archetypes_2026_05_10.md` line 38 + intra-side ping to slot 5 |
| 1B | PM | `2675e2f7` | Phase 1B design-shipped (existing `defi_reserve_params.py` shape sufficient) + Harsh implementation handoff doc |
| 1F | PM | `aa74cea8` | Phase 1F finding — plan body instruction mis-framed; legacy + new prediction modules serve different purposes (cross-venue mapping vs canonical-question-group); both retained |
| 1E | PM | `27c6ce39` | Phase 1E design-correction — extend existing `cefi_margin_tiers.py` rather than create new `perp_margin_tiers.py` (no duplicate SSOT); Harsh implementation handoff |
| 2 | PM | `48a55845` | Phase 2 per-protocol shard-atom design matrix — bundled vs per-instrument decision per protocol family |

### Deferred work after 2026-05-12 session (carry-forward to Day 2 morning)

| Phase / item | Status as of 2026-05-12 EOD | Successor / blocker |
|--------------|-----------------------------|----------------------|
| 1H — UAC QG green | deferred-to-day-2 | Quick local QG run by slot 2 Day 2 AM (`bash scripts/quality-gates.sh` from UAC) — edits Day 1 were small/clean, deferring to start-of-day batch verify |
| 3-LENDING.4 — recent-days catch-up VM | deferred-to-day-2 | 5-10min scoped run on `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07 today` + event-stream verify per CLAUDE.md "No fire-and-forget VM launches". NOT slot-5-blocking (Family-1 design has 2-year+ horizon already available). Slot 2 Day 2 AM action — closes `defi_master_2026_05_07.md` Priority #5 `[x]`. |
| 3-LENDING.5 reconciler one-shot wrapper | deferred-after-3-LENDING.4 | Phantom-audit script wrapper for pre-fix drift cleanup; daemon already running per slot 3 manual consolidator (`manifest-consolidator-20260511-181538`). Defer until 3-LENDING.4 catch-up lands. |
| ManifestFreshnessCache wire-in (P1, from `defi_master` handover-block (b)) | deferred-after-3-LENDING.4 | Refactor across `lending_indices_handler` + sibling MTDS DeFi backfill handlers (`gas_fees`/`lst_rates`/`dex_pools`/`liquidations`/`perp_funding`). Slot 2 or Harsh slot 2 Day 2-3 work. Not 2026-05-23-blocking but unlocks clean full-history re-run. |
| Clean full-history all-chains lending-indices re-run (P2) | deferred-after-ManifestFreshnessCache | Cosmetic cleanup of ~142 LINEA + ~296 BSC `SOURCE_RETURNED_ZERO` pre-launch nits to `EXPECTED_PRE_GENESIS_CHAIN`. |
| `create-code-tarballs.sh` stale-repo list (P1, from `defi_master` handover-block (d)) | deferred-after-ManifestFreshnessCache | Tooling debt; not May-23-blocking. |
| Phase 2 codex matrix subsection in `defi-venue-protocol-catalogue.md` | deferred-to-day-2 AM | Mirror the Phase 2 per-protocol shard-atom matrix from the plan body into the codex doc as a "Per-protocol shard-atom matrix" subsection (Phase 1J refresh extension). Quick edit, slot 2 Day 2 AM. |
| Optional rename `cefi_margin_tiers.py` → `perp_margin_tiers.py` (visual clarity) | deferred-post-cutover | Mechanical refactor; not May-23-blocking. |
| Optional rename legacy `canonical/domain/prediction/` → `prediction_mapping/` (visual disambiguation from new `predictions/`) | deferred-post-cutover | Mechanical refactor across 2 live consumers + facade re-export; not May-23-blocking. |
| Polygon zkEVM `CHAIN_GENESIS_DATES` entry | deferred-until-needed | Add `"POLYGON_ZKEVM": "2023-03-27"` only when a protocol on that chain enters Phase 1A scope. |

### Cross-side handshakes for Harsh slot 2 (Day 2 morning pickup)

Per `work_split_2026_05_12_ikenna.md` row 2 cross-side handshake — "Ikenna designs (Phases 1-3), Harsh implements
(Phases 2-6 across protocols)":

- **Phase 1B** — per-chain `AAVE_V3_<CHAIN>_RESERVES` + `SPARK_ETHEREUM_RESERVES` + `RADIANT_<CHAIN>_RESERVES`
  dicts (12 total). Provenance URLs documented per protocol. Extend `get_reserve_params()` chain dispatch.
- **Phase 1E** — extend `cefi_margin_tiers.py` `CEFI_MARGIN_TIERS` with Deribit / Hyperliquid / Aster × BTC + ETH
  entries. Same `VenueMarginSchedule` shape.
- **Phase 2** — per-protocol instruments-service adapters per the bundled-vs-per-instrument matrix shipped today.
  Cluster validation MANDATORY for DEX / multi-vault restaking / vaults.

### Critical-path handshake status

- **Slot 5 (ikenna-recursive-borrow-tab) Family-1 design**: ✅ UNBLOCKED Day 1. Lending-indices data with 2-year+
  horizons across AAVEV3 (6 chains) + COMPOUNDV3 (5 chains) + SPARK (ETH). Slot 5 confirmed pivot per their STATUS
  line; Family-1 + Family-2 topology design SSOT shipped same-day (PM@`5cb0952f` + PM@`3fbe82ca`).
- **Slot 5 Day-3 (2026-05-14)**: pull fix after 3-LENDING.4 recent-days catch-up VM lands (slot 2 Day 2 AM action).

### Operator-triage closures (informational — closed by slot 3)

Prior-cycle slot-2 STATUS-2026-05-11 flagged 3 PipelineMode findings as 🟡 BLOCKED. Operator triage 2026-05-11 PM
landed Q1=(α) + Q2=(A) approvals routed to slot 3 at PM@`4c573302`. Phase 4.GREP-VERIFY AST-walk QG check shipped
by slot 3 at PM@`4159b7ae`. Phase 4.MTDS → Phase 4.DEFAULT-REMOVAL path now clear for 2026-05-15 freeze gate.
Slot 2's prior cycle deferrals all closed via slot 3 follow-up.

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

Slot 5 Day-1 design ship surfaced 2 Phase 3 dependencies for slot 2 to verify or close:

1. **Funding-rate data_type capture for ETH-PERP on Hyperliquid + Bybit** at ≥1h cadence, ≥1y horizon. Required for Family 2 Phase 7.5 `funding_rate_apr_rolling_30d_mean` feature (adaptive sizing). Grep-then-READ before concluding adapter missing (HARD RULE) — check `market-tick-data-service/market_tick_data_service/adapters/` for `hyperliquid_funding_*.py` or `bybit_funding_*.py` patterns.
2. **Instruments-service per-(chain, protocol) reserve listings** for Arbitrum Aave V3 (11 reserves: USDC, USDC.E, USDT, DAI, WETH, WBTC, WSTETH, WEETH, RETH, ARB, LINK) + Base Aave V3 (7 reserves: USDC, USDBC, WETH, CBBTC, WSTETH, WEETH, CBETH). Without these listings, MTDS `lending_indices` adapter has no instrument universe for non-Ethereum chains — Family 1 Arbitrum/Base cells unblock requires these.

Slot 5 NOT fixing (Findings Triage — outside-plan scope); slot 2 owns this Phase 3 detail. Reference: `defi_recursive_borrow_archetypes_2026_05_10.md` Family 1 topology design section (Arbitrum + Base ReserveParams matrix).
