---
doc_type: plan
title: defi-pipeline-extension-2026-05-01
summary: Volatility-derived max-leverage primitive + leveraged funding-arb + 5 derivable archetype engines (LP concentrated/pool/vault,
  MEV liquidation-bundle/JIT/backrun) + sandwich theoretical, with venue/chain coverage backfill and codex enhancement
status: complete
nature: record
asset_group: ALL
stage: [meta]
repos:
  [
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    system-integration-tests,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-01
locked_by: live-defi-rollout
locked_since: 2026-05-01
plan_type: mixed
owner: ikenna
type: mixed
epic: epic-code-completion
completion_gates: { code: C5, deployment: D2, business: B3 }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: features-onchain-service, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: risk-and-exposure-service, code: C0, deployment: none, business: none }
  - { repo: system-integration-tests, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [leveraged_leg_controller_2026_05_01]
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# DeFi Pipeline Extension — Volatility-Capped Leverage + Derivable Archetype Coverage

## Why this plan exists

The 8-archetype tracer pass on 2025-06-15..21 (CARRY_RECURSIVE_STAKED, CARRY_STAKED_BASIS, CARRY_BASIS_PERP,
ARBITRAGE_PRICE_DISPERSION, REBASING_YIELD, YIELD_ROTATION_LENDING, LIQUIDATION_CAPTURE, TARGET_UNIVERSE_REBALANCE)
proved the leg-controller primitive works end-to-end against real on-chain data, but exposed five concrete gaps:

1. **No instrument-side leverage cap.** Controller currently clamps target_leverage to `venue.max_leverage` only. A
   strategy that wants 10x on Hyperliquid LINK perps and 10x on Hyperliquid AVAX perps gets identical caps despite AVAX
   moving ~2.4× harder than LINK in stress windows. Liquidation risk is asymmetric and not modelled.
2. **Cross-venue funding arb runs at target_leverage=1.0.** The 9.34% Hyperliquid BTC short × 3 CeFi long book in
   `ArbitragePriceDispersionHierarchicalEngine` is delta-neutral but un-leveraged. Net 6% spread at 3x is 18%; we are
   leaving the spread-multiplier on the table.
3. **Five archetype enum values exist with zero engine code.** `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT`,
   `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN` are in `StrategyArchetype`
   but nothing implements them. All are derivable from existing MTDS/features-onchain data.
4. **MEV sandwich is gated on mempool data we do not collect.** Sandwich requires pending-tx visibility (Flashbots
   Protect / MEV-share / Alchemy private mempool). We can simulate the theoretical-profit upper bound from confirmed
   blocks but must not pretend it is executable today.
5. **Venue/chain coverage in the analysis was ~5/39 DeFi venues and ~4/9 CeFi venues.** Missing chain coverage:
   AVALANCHE, BSC, LINEA, MANTLE, AURORA, BLAST, CELO, FANTOM, GNOSIS, METIS, MODE, MOONBEAM (12 chains). Missing
   protocol coverage: COMPOUND_V3 (5 chains), MORPHO (5 chains), FLUID, UNISWAP_V2/V3/V4 (LP positions, not just swaps),
   Balancer, Curve, ETHENA, JITO-SOLANA. The pipeline silently treats these as unsupported.

The user's directive: build a single PM action plan covering all five gaps end-to-end (UAC primitive → controller clamp
→ engines → tracers → codex docs → venue/chain backfill) so we don't lose the thread when context resets.

## Pre-audit manifest

### Primitive: `MaxUnderlyingMove` + `INSTRUMENT_VOLATILITY_REGISTRY` (new)

UAC currently has venue-side liquidation thresholds but NO instrument-side volatility-derived caps:

- **Has:** `unified_api_contracts/internal/risk.py:714` `LIQUIDATION_PARAMS_REGISTRY` — 11 `MarginModel` entries
  (AAVE_V3, COMPOUND_V3, MORPHO_BLUE, BINANCE_CROSS, BINANCE_ISOLATED, BYBIT, OKX, DYDX_V4, HYPERLIQUID, FUTURES_SPAN,
  EXPOSURE_CAP) with HF/MMR thresholds.
- **Missing:** No per-instrument `max_underlying_move_pct` to derive a volatility-driven leverage cap. The controller
  only enforces venue-side ceilings.

### Existing controller clamp surface

`execution-service/execution_service/algo_library/leveraged_leg_controller.py::compute_drift` calls
`clamp_to_venue_capabilities(venue, target_leverage)` which only consults `instruments-service` venue capability
declarations. The clamp must become `min(venue.max_leverage, instrument.max_safe_leverage)`.

### Existing funding-arb engine

`strategy-service/strategy_service/engine/strategies/v2/arbitrage/dispersion_hierarchical.py`
`ArbitragePriceDispersionHierarchicalEngine` (commit `9e33ba2`) currently builds N legs at target_leverage=1.0. The
extension is a per-leg `derive_max_safe_leverage(instrument)` lookup BEFORE submitting to the controller — the
controller already enforces the cap; the engine just needs to pass the desired leverage in.

### Strategy archetype enums (already present)

`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py`:

- Line 85-87: `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT` — present
- Line 70-73: `ARBITRAGE_MEV_SANDWICH`, `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN`,
  `ARBITRAGE_MEV_LIQUIDATION_BUNDLE` — present

No new enum values needed — only the engine implementations + factory wiring + parity tests.

### Engine factory + registry

`strategy-service/strategy_service/engine/strategies/v2/factory.py` — register 6 new engine classes (LP_CONCENTRATED,
LP_POOL, LP_VAULT, MEV_LIQUIDATION_BUNDLE, MEV_JIT_LIQUIDITY, MEV_BACKRUN). Sandwich theoretical-only goes into
`tracers/` not `factory.py` (no live deployment until mempool data lands).

### MTDS / features-onchain coverage gap

`market-tick-data-service` adapters that need to be added/verified:

- LP-tick capture: Uniswap V3 swap events with (sqrtPriceX96, liquidity, tick) — exists for swap routing, NOT persisted
  as LP-state ticks per-pool per-block.
- Curve / Balancer pool-state ticks (token balances + invariant) — not collected.
- ERC-4626 vault share-price ticks (totalAssets / totalSupply) — not collected.
- MEV-block ordering (per-block tx position + priority gas + base fee) — partial; needs full ordering.
- Liquidation-event capture across protocols — exists for AAVE on 5 chains; missing COMPOUND_V3, MORPHO_BLUE, FLUID,
  EULER_V2, RADIANT, VENUS, BENQI, GMX (perp liquidations).

`features-onchain-service` calculators needed:

- `pool_invariant_drift` — for LP_POOL strategies.
- `concentrated_liquidity_il_realised` — closed-form Uniswap V3 IL given (entry_sqrt_price, current_sqrt_price, range).
- `vault_share_price_apy` — annualised drift of share price net of fees.
- `block_priority_gas_distribution` — for MEV backrun win-probability.

### Volatility data source

`features-onchain-service` and `features-cefi-service` already publish realised-volatility feature groups
(`vol_realised_30d`, `vol_realised_1y`, `vol_garch_forecast`). The volatility registry seeds from these, with manual
overrides for new coins.

### Codex docs touched

- `unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/` — add 6 new archetype docs (LP_CONCENTRATED,
  LP_POOL, LP_VAULT, MEV_LIQUIDATION_BUNDLE, MEV_JIT_LIQUIDITY, MEV_BACKRUN), update ARBITRAGE_MEV_SANDWICH with
  "theoretical-only" caveat, update ARBITRAGE_PRICE_DISPERSION to document leverage-net-spread mode.
- `unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/leverage-and-volatility.md` — new SSOT for the
  `max_underlying_move → max_safe_leverage` derivation, registry seed/override workflow, controller integration.
- `unified-trading-pm/codex/14-playbooks/defi/lp-strategies.md` — playbook for LP archetype family.
- `unified-trading-pm/codex/14-playbooks/defi/mev-strategies.md` — playbook for MEV archetype family + mempool-data
  deferral.

### Tests & gates

- UAC unit tests: registry parity + `derive_max_safe_leverage()` boundary cases.
- execution-service tests: controller clamp test extension.
- strategy-service v2 parity tests: 6 new engines × tick-driven scenarios.
- system-integration-tests: e2e for LP_CONCENTRATED + MEV_LIQUIDATION_BUNDLE on Tenderly fork.

## Phased execution DAG

```
Phase 1 — UAC primitives (PARALLEL within phase)
   ├─ 1.1 internal/risk/instrument_volatility.py — MaxUnderlyingMove BaseModel, INSTRUMENT_VOLATILITY_REGISTRY,
   │      derive_max_safe_leverage()
   ├─ 1.2 Re-export from unified_api_contracts.risk + facade
   ├─ 1.3 Seed registry from features-{cefi,onchain}-service vol_realised_30d (script under uac/scripts/)
   ├─ 1.4 Tests: registry coverage, helper boundary cases, frozen Pydantic
   └─ 1.5 GATE — UAC quality-gates.sh passes; helper importable from unified_api_contracts.risk

Phase 2 — Controller clamp extension (after Phase 1)
   ├─ 2.1 execution-service: clamp_to_venue_capabilities → min(venue.max_leverage, instrument.max_safe_leverage)
   ├─ 2.2 LeveragedLegController.compute_drift now logs both ceilings; emits LEVERAGE_CAP_TRIPPED metric
   ├─ 2.3 Tests: vol-cap-binds, venue-cap-binds, both-equal, missing-instrument-fallback
   └─ 2.4 GATE — execution-service QG green

Phase 3 — Funding-arb leverage extension (PARALLEL with Phase 4)
   ├─ 3.1 ArbitragePriceDispersionHierarchicalEngine: per-leg target_leverage now derived from
   │      derive_max_safe_leverage(instrument) × strategy.leverage_quality_multiplier
   ├─ 3.2 Promote net_spread_threshold from constant to per-leg-pair dynamic threshold
   ├─ 3.3 Tracer: re-run cross-venue funding arb 2025-06-15..21 with leveraged delta-neutral
   ├─ 3.4 Parity tests: 1.0x parity (existing) + 3x leveraged scenario + risk-overlay LEVERAGE_BREACH
   └─ 3.5 GATE — strategy-service QG green; results table delta vs un-leveraged reproduced

Phase 4 — DeFi LP archetype family (PARALLEL within sub-phases; PARALLEL with Phase 3)
   ├─ 4.1 LP_CONCENTRATED engine (Uniswap V3 sqrt-price math; closed-form IL; entry/exit/rebalance ticks;
   │      gas budget; fee-tier-aware)
   │   ├─ 4.1.a Engine class + factory wiring
   │   ├─ 4.1.b features-onchain calculator: concentrated_liquidity_il_realised
   │   ├─ 4.1.c MTDS: per-pool sqrt_price + liquidity tick capture (block-granularity) for top-50 V3 pools
   │   └─ 4.1.d Parity tests + tracer
   ├─ 4.2 LP_POOL engine (Curve stableswap invariant; Balancer weighted invariant; deposit/withdraw IL on
   │      depeg; pool-share APY)
   │   ├─ 4.2.a Engine class + factory wiring
   │   ├─ 4.2.b features-onchain calculator: pool_invariant_drift
   │   ├─ 4.2.c MTDS: per-pool token-balance + invariant tick capture for top Curve/Balancer pools
   │   └─ 4.2.d Parity tests + tracer
   ├─ 4.3 LP_VAULT engine (ERC-4626 share-price evolution; perf+mgmt fee accrual; deposit/withdraw queues)
   │   ├─ 4.3.a Engine class + factory wiring
   │   ├─ 4.3.b features-onchain calculator: vault_share_price_apy
   │   ├─ 4.3.c MTDS: ERC-4626 share-price tick capture for top vaults (Yearn V3, Morpho, Aave Vaults,
   │           Sommelier, MetaMorpho)
   │   └─ 4.3.d Parity tests + tracer
   └─ 4.4 GATE — all three engines green; tracer results published in memory

Phase 5 — MEV archetype family (PARALLEL within sub-phases; SEQUENTIAL after Phase 4)
   ├─ 5.1 MEV_LIQUIDATION_BUNDLE engine (extends LIQUIDATION_CAPTURE: flash-loan source + atomic bundle +
   │      flash fee + gas budget + protocol coverage matrix)
   ├─ 5.2 MEV_JIT_LIQUIDITY engine (swap-size threshold detection; 2-block window; 1-tick-wide V3 mint;
   │      fee capture; un-mint on next block)
   ├─ 5.3 MEV_BACKRUN engine (per-block ordering; priority-gas win-probability; arbitrage following
   │      large directional swap)
   ├─ 5.4 MEV_SANDWICH theoretical-profit tracer ONLY (no live engine; explicit caveat: requires
   │      mempool feed not yet collected)
   └─ 5.5 GATE — engines + tracers + parity tests; SANDWICH file documents the deferred requirement

Phase 6 — Venue / chain coverage backfill (PARALLEL within phase)
   ├─ 6.1 Add 12 missing chains (AVALANCHE, BSC, LINEA, MANTLE, AURORA, BLAST, CELO, FANTOM, GNOSIS,
   │      METIS, MODE, MOONBEAM) to UAC CHAIN_RPC_TEMPLATES + MAINNET_CHAIN_IDS
   ├─ 6.2 Add COMPOUND_V3 (5 chains), MORPHO_BLUE (5 chains), FLUID, EULER_V2, RADIANT, VENUS, BENQI to
   │      LIQUIDATION_PARAMS_REGISTRY (HF / liquidation_threshold / close_factor)
   ├─ 6.3 Add UNISWAP_V2 / V3 / V4, BALANCER, CURVE, ETHENA, JITO-SOLANA to VENUES_BY_ASSET_GROUP defi
   ├─ 6.4 instruments-service adapters for the missing protocols (LP positions, vault deposits)
   ├─ 6.5 MTDS adapters for the missing chains (block subscription + log filtering)
   ├─ 6.6 features-onchain calculators routed to the new venues (per-protocol lending rates, LP TVL)
   └─ 6.7 GATE — pipeline E2E across the union runs without `unsupported_venue` warnings

Phase 7 — Codex docs (PARALLEL with Phase 6)
   ├─ 7.1 /codex/09-strategy/architecture-v2/archetypes/lp_concentrated.md
   ├─ 7.2 /codex/09-strategy/architecture-v2/archetypes/lp_pool.md
   ├─ 7.3 /codex/09-strategy/architecture-v2/archetypes/lp_vault.md
   ├─ 7.4 /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_liquidation_bundle.md
   ├─ 7.5 /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_jit_liquidity.md
   ├─ 7.6 /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_backrun.md
   ├─ 7.7 /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_sandwich.md (theoretical caveat)
   ├─ 7.8 /codex/09-strategy/architecture-v2/cross-cutting/leverage-and-volatility.md (new SSOT)
   ├─ 7.9 /codex/14-playbooks/defi/lp-strategies.md (family playbook)
   ├─ 7.10 /codex/14-playbooks/defi/mev-strategies.md (family playbook + mempool deferral)
   └─ 7.11 GATE — codex-sync agent green; rules-alignment agent green

Phase 8 — End-to-end validation + results memory (SEQUENTIAL after Phases 4/5/6/7)
   ├─ 8.1 SIT: e2e LP_CONCENTRATED on Tenderly fork (full mint → swap-driven IL → rebalance → burn)
   ├─ 8.2 SIT: e2e MEV_LIQUIDATION_BUNDLE on Tenderly fork (flash loan → liquidate → swap collateral →
   │      repay flash → profit)
   ├─ 8.3 Comprehensive tracer pass: ALL 14 archetypes (8 existing + 6 new) on 2025-06-15..21
   ├─ 8.4 Memory: project_archetype_results_2025_06_15_21.md update with new rows
   ├─ 8.5 Memory: project_defi_pipeline_extension_2026_05_01.md (this plan's closeout note)
   └─ 8.6 GATE — workspace QG sweep across all 11 repos; all green

Phase 9 — Mempool feed integration (DEFERRED follow-up plan, NOT in this plan)
   └─ 9.1 Created as plans/active/mempool_feed_integration_2026_06_01.md after Phase 8 closeout
```

## Mempool data — explicit deferral

ARBITRAGE_MEV_SANDWICH **cannot** ship as a live engine in this plan. The simulation in Phase 5.4 produces an
upper-bound theoretical profit by walking confirmed block transactions (frontrun-victim-backrun ordering) and computing
what a perfect mempool observer could have captured. The live execution requires:

- **Mempool feed** — Flashbots Protect / MEV-share subscription, OR Alchemy private-mempool stream, OR Bloxroute
  (removed from workspace, would need re-add).
- **Bundle relay** — Flashbots / Eden / bloXroute relay to land the bundle atomically.
- **Reorg protection** — bundle simulation pre-submission to avoid reverts.

These are tracked in a separate Phase 9 plan (`mempool_feed_integration_2026_06_01.md`) which this plan **creates a stub
for** but does not execute. The theoretical tracer publishes a per-day "leave on table" number so the business can
decide whether the mempool data subscription cost is justified.

## Volatility-leverage primitive — design

```python
# unified_api_contracts/internal/risk/instrument_volatility.py
class MaxUnderlyingMove(BaseModel):
    instrument_key: InstrumentKey
    horizon_days: int            # 1, 7, 30 — windows for which the move is calibrated
    max_move_pct: Decimal        # e.g., Decimal("0.20") for 20%
    confidence: Decimal          # e.g., Decimal("0.95") — 95% one-sided
    source: Literal["realised_30d", "garch_forecast", "manual_override"]
    derived_at: datetime

INSTRUMENT_VOLATILITY_REGISTRY: dict[InstrumentKey, MaxUnderlyingMove] = {...}

def derive_max_safe_leverage(
    instrument: InstrumentKey,
    safety_buffer: Decimal = Decimal("0.5"),  # leave 50% headroom from liquidation
) -> Decimal:
    """
    Returns max leverage such that a `max_move_pct` adverse move leaves
    `safety_buffer × maintenance_margin` of equity on the position.

    Formula:
        max_safe_leverage = (1 - safety_buffer) / max_move_pct

    Examples:
        BTC max_move_pct=0.10, buffer=0.5 → 5.0x
        AVAX max_move_pct=0.25, buffer=0.5 → 2.0x
        SOL max_move_pct=0.20, buffer=0.5 → 2.5x
    """
```

The controller clamp becomes:

```python
# execution-service/.../leveraged_leg_controller.py
def clamp_to_venue_capabilities(venue, instrument, target_leverage):
    venue_cap = venue.max_leverage  # from instruments-service
    vol_cap = derive_max_safe_leverage(instrument)  # from UAC
    effective_cap = min(venue_cap, vol_cap)
    if target_leverage > effective_cap:
        emit_metric("LEVERAGE_CAP_TRIPPED", {
            "venue_cap": venue_cap, "vol_cap": vol_cap,
            "requested": target_leverage, "applied": effective_cap,
        })
    return min(target_leverage, effective_cap)
```

## Success criteria

| Phase | Code Gate  | Deployment Gate | Business Gate                                      |
| ----- | ---------- | --------------- | -------------------------------------------------- |
| 1     | C5 (UAC)   | none            | B1 — registry seeded for ≥30 instruments           |
| 2     | C5 (exec)  | none            | B1 — clamp tested on synthetic + real              |
| 3     | C5 (strat) | D2              | B3 — net leveraged spread P&L > 1.0x baseline      |
| 4     | C5 (×3)    | D2              | B3 — each LP archetype ≥0% net APY post-fees       |
| 5     | C5 (×3)    | D2              | B3 — bundle/JIT/backrun tracers ≥0% theoretical    |
| 6     | C5 all     | D2              | B1 — pipeline E2E green across union of venues     |
| 7     | C3 (PM)    | none            | B1 — codex-sync + rules-alignment green            |
| 8     | C5 all     | D2              | B3 — 14-archetype results published; SIT e2e green |
| 9     | DEFERRED   | DEFERRED        | DEFERRED                                           |

## Todos

### Phase 1 — UAC volatility primitive

- id: p1-1-instrument-volatility-schema content: |
  - [ ] [AGENT] P0. Create unified_api_contracts/internal/risk/instrument_volatility.py with MaxUnderlyingMove BaseModel
        (instrument_key, horizon_days, max_move_pct, confidence, source, derived_at), frozen=True. Define
        INSTRUMENT_VOLATILITY_REGISTRY: dict[InstrumentKey, MaxUnderlyingMove]. Implement derive_max_safe_leverage(
        instrument, safety_buffer=Decimal("0.5")) -> Decimal with formula `(1 - safety_buffer) / max_move_pct`.
        Re-export from unified_api_contracts.risk facade. status: todo

- id: p1-2-registry-seed-script content: |
  - [ ] [AGENT] P0. Create unified-api-contracts/scripts/seed_instrument_volatility_registry.py reading vol_realised_30d
        feature group from features-cefi-service + features-onchain-service via the existing domain_client. Write seeded
        entries to unified_api_contracts/internal/risk/\_volatility_seeds.py imported by INSTRUMENT_VOLATILITY_REGISTRY
        at module load. Initial coverage: top 30 instruments (BTC/ETH/SOL/AVAX/LINK/ ATOM/DOT/NEAR/SUI/APT + 20 ETH-side
        LSTs / lending tokens). status: todo

- id: p1-3-tests-coverage content: |
  - [ ] [AGENT] P0. Tests: registry coverage check (seeded ≥30 instruments), helper boundary cases (zero move →
        ZeroDivisionError raised; max_move>1.0 → ValueError; safety_buffer=1.0 → 0.0x cap), frozen Pydantic enforcement,
        source enum exhaustiveness. status: todo

- id: p1-4-uac-qg content: |
  - [ ] [AGENT] P0. GATE — cd unified-api-contracts && bash scripts/quality-gates.sh passes; helper importable via
        `from unified_api_contracts.risk import derive_max_safe_leverage`. status: todo

### Phase 2 — Controller clamp extension

- id: p2-1-clamp-extension content: |
  - [ ] [AGENT] P0. Extend execution-service/.../leveraged_leg_controller.py::clamp_to_venue_capabilities to take
        instrument param + look up derive_max_safe_leverage(instrument). effective_cap = min(venue_cap, vol_cap). Emit
        LEVERAGE_CAP_TRIPPED metric (via UTL log_event) when requested > effective_cap. status: todo

- id: p2-2-controller-tests content: |
  - [ ] [AGENT] P0. Tests: vol-cap-binds (vol < venue), venue-cap-binds (venue < vol), both-equal,
        missing-instrument-fallback (no registry entry → use venue cap only + WARNING event). status: todo

- id: p2-3-execution-qg content: |
  - [ ] [AGENT] P0. GATE — cd execution-service && bash scripts/quality-gates.sh passes. status: todo

### Phase 3 — Funding-arb leveraged extension

- id: p3-1-engine-extension content: |
  - [ ] [AGENT] P0. ArbitragePriceDispersionHierarchicalEngine: replace constant target_leverage=1.0 with per-leg
        derive_max_safe_leverage(instrument) × leverage_quality_multiplier (config param, default 1.0). Promote
        net_spread_threshold from constant to per-leg-pair dynamic value scaled by min(leg_a.vol_cap, leg_b.vol_cap).
        status: todo

- id: p3-2-tracer-rerun content: |
  - [ ] [AGENT] P0. Re-run cross-venue funding arb tracer 2025-06-15..21 with leveraged delta-neutral. Save output to
        execution-service/scripts/tracers/output/arbitrage_dispersion_leveraged_2025_06_15_21.json. status: todo

- id: p3-3-parity-tests content: |
  - [ ] [AGENT] P0. v2 parity tests: 1.0x parity (matches existing tracer) + 3x leveraged scenario + risk overlay
        LEVERAGE_BREACH triggers when actual leverage drifts >10% above target. status: todo

- id: p3-4-strategy-qg content: |
  - [ ] [AGENT] P0. GATE — cd strategy-service && bash scripts/quality-gates.sh passes. status: todo

### Phase 4 — DeFi LP archetype family

- id: p4-1a-lp-concentrated-engine content: |
  - [ ] [AGENT] P1. strategy-service: DefiLpConcentratedEngine in engine/strategies/v2/defi/lp_concentrated.py. State
        machine: NEUTRAL → MINTED(range, liquidity) → REBALANCE_PENDING → BURNED. Closed-form IL given
        (entry_sqrt_price, current_sqrt_price, range_lower, range_upper). Emit MintInstruction / BurnInstruction /
        ReBalanceInstruction. Factory + identity wiring + declare_leg_portfolio_state hook. status: todo

- id: p4-1b-il-calculator content: |
  - [ ] [AGENT] P1. features-onchain-service: concentrated_liquidity_il_realised calculator. Per-pool per-block. Inputs:
        pool_address, position_token_id, current_sqrt_price. Outputs: il_pct, fees_earned_pct, net_pct. status: todo

- id: p4-1c-mtds-v3-tick-capture content: |
  - [ ] [AGENT] P1. market-tick-data-service: per-pool sqrt_price + liquidity + tick state capture for top-50 Uniswap V3
        pools across ETHEREUM, ARBITRUM, OPTIMISM, BASE, POLYGON. Adapter:
        mtds/adapters/onchain/uniswap_v3_pool_state.py. Schema: pool_state_v3 parquet with (block_number,
        sqrt_price_x96, liquidity, tick). status: todo

- id: p4-1d-lp-concentrated-tests content: |
  - [ ] [AGENT] P1. Parity tests + tracer: WBTC/USDC 0.05% pool 2025-06-15..21 with $1M starting equity, ±5% range.
        Validate fees vs IL crossover. status: todo

- id: p4-2a-lp-pool-engine content: |
  - [ ] [AGENT] P1. strategy-service: DefiLpPoolEngine for Curve stableswap + Balancer weighted. Invariant drift
        detection. Deposit / withdraw with depeg-aware sizing. Factory + parity tests + tracer. status: todo

- id: p4-2b-pool-invariant-feature content: |
  - [ ] [AGENT] P1. features-onchain-service: pool_invariant_drift calculator (Curve D-invariant, Balancer V-invariant).
        Inputs: token_balances, weights/A. Outputs: invariant_value, drift_vs_book. status: todo

- id: p4-2c-mtds-pool-state-capture content: |
  - [ ] [AGENT] P1. MTDS: per-pool token-balance + invariant capture for top 30 Curve pools (3pool, frax, sUSDe,
        ETH-stETH, etc.) and top 20 Balancer pools (wstETH-rETH, B-80BAL-20WETH, etc.). status: todo

- id: p4-2d-lp-pool-tests content: |
  - [ ] [AGENT] P1. Parity tests + tracer for Curve 3pool depeg + Balancer wstETH-rETH 2025-06-15..21. status: todo

- id: p4-3a-lp-vault-engine content: |
  - [ ] [AGENT] P1. strategy-service: DefiLpVaultEngine for ERC-4626 vaults. Share-price evolution; perf+mgmt fee
        accrual; deposit/withdraw queues. Factory + parity tests + tracer. status: todo

- id: p4-3b-vault-share-feature content: |
  - [ ] [AGENT] P1. features-onchain-service: vault_share_price_apy calculator. Inputs: totalAssets, totalSupply,
        fee_curve. Outputs: share_price, annualised_apy_net. status: todo

- id: p4-3c-mtds-vault-capture content: |
  - [ ] [AGENT] P1. MTDS: ERC-4626 share-price tick capture for top 40 vaults across Yearn V3, Morpho, Aave Vaults,
        Sommelier, MetaMorpho. Adapter: mtds/adapters/onchain/erc4626_share_price.py. status: todo

- id: p4-3d-lp-vault-tests content: |
  - [ ] [AGENT] P1. Parity tests + tracer: top 5 yvUSDC/yvETH/yvDAI variants 2025-06-15..21. status: todo

- id: p4-gate content: |
  - [ ] [AGENT] P1. GATE — cd strategy-service && bash scripts/quality-gates.sh passes; cd features-onchain-service &&
        bash scripts/quality-gates.sh passes; cd market-tick-data-service && bash scripts/quality-gates.sh passes.
        status: todo

### Phase 5 — MEV archetype family

- id: p5-1-liquidation-bundle-engine content: |
  - [ ] [AGENT] P1. strategy-service: ArbitrageMevLiquidationBundleEngine. Extends LIQUIDATION_CAPTURE with: flash loan
        source resolution (Aave / Balancer / Maker DAI flash mint, lowest-fee wins), atomic bundle assembly (flashLoan →
        liquidationCall → swap collateral → repay flash → keep profit), gas budget curve, protocol-coverage matrix
        (AAVE_V3, COMPOUND_V3, MORPHO_BLUE, FLUID, EULER_V2, RADIANT, VENUS, BENQI). Engine emits
        AtomicBundleInstruction. Factory + parity tests + tracer. status: todo

- id: p5-2-mev-jit-engine content: |
  - [ ] [AGENT] P1. strategy-service: ArbitrageMevJitLiquidityEngine. Detects pending-large-swap signal (≥$X USD on a
        target V3 pool), 2-block window, mints 1-tick-wide concentrated liquidity around the mid, captures fee on the
        swap, burns next block. Requires MTDS block-N → block-N+1 ordering capture. Factory + parity tests + tracer.
        status: todo

- id: p5-3-mev-backrun-engine content: |
  - [ ] [AGENT] P1. strategy-service: ArbitrageMevBackrunEngine. Per-block ordering capture. Detects large directional
        swap on block N. Computes optimal arbitrage path across N other DEXes/CEXes using MTDS LP-tick data. Submits
        backrun tx with priority gas chosen via block_priority_gas_distribution feature. Factory + parity tests +
        tracer. status: todo

- id: p5-3a-priority-gas-feature content: |
  - [ ] [AGENT] P1. features-onchain-service: block_priority_gas_distribution calculator. Per-block, returns P50/P90/P99
        of priority-gas across all included txs. Used by backrun engine to size priority gas for win-probability target.
        status: todo

- id: p5-4-sandwich-theoretical-tracer content: |
  - [ ] [AGENT] P1. strategy-service: ArbitrageMevSandwichTheoreticalTracer (NOT a live engine). Walks confirmed blocks,
        identifies victim swaps where a perfect-mempool-observer could have inserted a frontrun + backrun pair, computes
        theoretical profit. Output: per-day theoretical profit + frequency distribution. Documents the explicit
        deferral: "live execution requires mempool feed; see mempool_feed_integration_2026_06_01.md". status: todo

- id: p5-5-mev-gate content: |
  - [ ] [AGENT] P1. GATE — cd strategy-service && bash scripts/quality-gates.sh passes; tracer outputs saved to
        scripts/tracers/output/. status: todo

### Phase 6 — Venue / chain coverage backfill

- id: p6-1-chains content: |
  - [ ] [AGENT] P2. UAC: add 12 chains to CHAIN_RPC_TEMPLATES + MAINNET_CHAIN_IDS (AVALANCHE=43114, BSC=56, LINEA=59144,
        MANTLE=5000, AURORA=1313161554, BLAST=81457, CELO=42220, FANTOM=250, GNOSIS=100, METIS=1088, MODE=34443,
        MOONBEAM=1284). Re-export. status: todo

- id: p6-2-liquidation-protocols content: |
  - [ ] [AGENT] P2. UAC: add COMPOUND_V3, MORPHO_BLUE (already partially), FLUID, EULER_V2, RADIANT, VENUS, BENQI to
        LIQUIDATION_PARAMS_REGISTRY with HF, liquidation_threshold, close_factor per chain deployment. status: todo

- id: p6-3-defi-venues content: |
  - [ ] [AGENT] P2. UAC: add UNISWAP_V2, UNISWAP_V3, UNISWAP_V4, BALANCER_V2, BALANCER_V3, CURVE, ETHENA, JITO_SOLANA to
        VENUES_BY_ASSET_GROUP['defi'] with capability declarations (supports_margin, max_leverage, fee_tiers, etc.).
        status: todo

- id: p6-4-instruments-adapters content: |
  - [ ] [AGENT] P2. instruments-service: adapters for the missing protocols. LP positions for Uniswap/Curve/Balancer
        (NFT IDs / pool tokens). Vault deposits for ERC-4626. Lending positions for Compound V3 / Morpho / Fluid / Euler
        V2. status: todo

- id: p6-5-mtds-chain-adapters content: |
  - [ ] [AGENT] P2. MTDS: chain adapters for the 12 new chains (block subscription + log filtering). Reuse existing
        onchain.evm framework; add per-chain RPC endpoints + reorg depth. status: todo

- id: p6-6-features-coverage content: |
  - [ ] [AGENT] P2. features-onchain-service: route lending-rate / LP-TVL calculators to the new protocols. No new
        calculator code — registry expansion + adapter wiring. status: todo

- id: p6-7-coverage-gate content: |
  - [ ] [AGENT] P2. GATE — pipeline E2E across the union runs without `unsupported_venue` warnings. Validation:
        instruments-service ingests; MTDS captures ≥ 1 block per new chain; features-onchain computes ≥ 1 calculator per
        new venue. status: todo

### Phase 7 — Codex docs

- id: p7-1-lp-concentrated-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/lp_concentrated.md — family/archetype placement, leg
        structure, IL closed form, fee-tier selection, rebalance triggers, gas/Tendermint considerations, parity test
        references. status: todo

- id: p7-2-lp-pool-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/lp_pool.md — Curve / Balancer invariants, depeg
        modelling, deposit-share APY, parity test references. status: todo

- id: p7-3-lp-vault-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/lp_vault.md — ERC-4626 share-price math, fee-curve
        handling, withdraw queues, parity test references. status: todo

- id: p7-4-mev-bundle-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_liquidation_bundle.md — flash loan
        source matrix, atomic bundle structure, gas budget, protocol coverage. status: todo

- id: p7-5-mev-jit-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_jit_liquidity.md — detection signal,
        2-block window, fee math, timing risk. status: todo

- id: p7-6-mev-backrun-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_backrun.md — ordering, priority gas win
        prob, arbitrage path resolution. status: todo

- id: p7-7-mev-sandwich-doc content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/archetypes/arbitrage_mev_sandwich.md — theoretical-only status;
        explicit deferral pointer to mempool_feed_integration plan; theoretical profit upper-bound formula. status: todo

- id: p7-8-leverage-vol-ssot content: |
  - [ ] [AGENT] P2. /codex/09-strategy/architecture-v2/cross-cutting/leverage-and-volatility.md — new SSOT covering MaxUnderlyingMove
        primitive, derive_max_safe_leverage formula, registry seed/override workflow, controller clamp integration,
        LEVERAGE_CAP_TRIPPED + LEVERAGE_BREACH events. status: todo

- id: p7-9-lp-playbook content: |
  - [ ] [AGENT] P2. /codex/14-playbooks/defi/lp-strategies.md — LP family playbook covering archetype selection,
        fee-tier selection, IL/fees crossover, gas-budget guidance. status: todo

- id: p7-10-mev-playbook content: |
  - [ ] [AGENT] P2. /codex/14-playbooks/defi/mev-strategies.md — MEV family playbook covering bundle building, RPC
        selection, mempool feed deferral, sandwich theoretical-only status. status: todo

- id: p7-11-codex-gate content: |
  - [ ] [AGENT] P2. GATE — cd unified-trading-pm && bash scripts/quality-gates.sh passes; codex-sync agent green;
        rules-alignment agent green. status: todo

### Phase 8 — End-to-end validation + results memory

- id: p8-1-sit-lp-concentrated content: |
  - [ ] [AGENT] P2. system-integration-tests: e2e LP_CONCENTRATED on Tenderly fork. Mint position → execute swaps that
        move price out of range → trigger rebalance → burn at exit. Validate fee capture + IL realisation against
        closed-form expectation. status: todo

- id: p8-2-sit-mev-bundle content: |
  - [ ] [AGENT] P2. system-integration-tests: e2e MEV_LIQUIDATION_BUNDLE on Tenderly fork. Set up undercollateralised
        position → flash-loan-bundle to liquidate → swap collateral → repay flash → profit transferred to wallet.
        status: todo

- id: p8-3-comprehensive-tracer content: |
  - [ ] [AGENT] P2. Comprehensive tracer pass: ALL 14 archetypes (8 existing + 6 new) on 2025-06-15..21. Save to
        execution-service/scripts/tracers/output/all_archetypes_2025_06_15_21.json + summary markdown table. status:
        todo

- id: p8-4-results-memory content: |
  - [ ] [AGENT] P2. Memory update: project_archetype_results_2025_06_15_21.md adds 6 new archetype result rows
        (LP_CONCENTRATED top pool, LP_POOL top stable, LP_VAULT top vault, MEV_BUNDLE bundle profitability, MEV_JIT
        capture rate, MEV_BACKRUN backrun spread). Update INDEX. status: todo

- id: p8-5-closeout-memory content: |
  - [ ] [AGENT] P2. Memory: project_defi_pipeline_extension_2026_05_01.md (this plan's closeout note) summarising
        commits per repo + key decisions. status: todo

- id: p8-6-workspace-qg-sweep content: |
  - [ ] [AGENT] P2. GATE — workspace QG sweep across all 11 repos in repo_gates. All green. Plan eligible for archive.
        status: todo

### Phase 9 — Mempool feed integration (DEFERRED)

- id: p9-1-stub-plan content: |
  - [ ] [AGENT] P3. Create plans/active/mempool_feed_integration_2026_06_01.md stub with: scope (Flashbots Protect /
        MEV-share / Alchemy private mempool / Bloxroute re-add evaluation), cost analysis (subscription tiers), bundle
        relay design, reorg protection, decision criteria (theoretical profit > 12 mo subscription cost). Stub only —
        execution gated on Phase 8 closeout AND business decision. status: todo

## Risks & open questions

| Risk                                                           | Mitigation                                                                 |
| -------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Volatility registry stale after market regime shift            | Schedule 30-day reseed via cron from features-cefi/onchain-service         |
| Controller silently uses venue cap when registry entry missing | Phase 2.2 test ensures WARNING event fires; Phase 1.2 seed covers top-30   |
| LP IL closed-form differs from EVM-realised due to rebalance   | Tenderly fork SIT validates within ±0.5% tolerance                         |
| MEV bundle reverts on-chain (gas underestimated)               | Phase 5.1 emits FLASH_BUNDLE_FAILED event; controller does NOT retry blind |
| Sandwich theoretical inflates business case                    | Phase 5.4 explicit "theoretical upper bound"; no live deployment           |
| Chain-12 backfill rate-limits free RPC tiers                   | Phase 6.5 wires Alchemy / QuickNode paid tiers via Secret Manager          |
| Coverage backfill blast radius larger than scoped              | Phase 6 each subitem QG-gated; pause if ≥3 downstream consumers break      |

## Dependencies

- **leveraged_leg_controller_2026_05_01.md** — Phase 1-6 closeout shipped 2026-05-01. This plan is the follow-on
  extension and inherits the controller + UAC schema as-is.
- **eigenlayer_rewards plan + restaking_reward_economics SSOT** (shipped 2026-05-01) — independent; LP_VAULT share-price
  math is orthogonal to dust-conversion router.
- **workspace_audit_wave_a_committed_2026_05_01** — Wave A foundations (events SSOT, EventEnvelope, topic registry)
  shipped; this plan reuses them for LEVERAGE_CAP_TRIPPED / FLASH_BUNDLE_FAILED events.

## What this plan does NOT do

- Does NOT add a live MEV sandwich engine — gated on mempool feed (Phase 9 stub plan).
- Does NOT replace existing leg-controller — extends the clamp surface only.
- Does NOT introduce backwards-compat shims — all consumers updated in-band per Citadel Standard #3.
- Does NOT expand StrategyArchetype enum — values already exist; this plan only implements them.
- Does NOT modify execution alpha measurement (matching engine still owns simulated fills per CLAUDE.md Batch=Live
  SSOT).
