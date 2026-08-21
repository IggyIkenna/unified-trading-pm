---
doc_type: plan
title: strategy-docs-vs-system-audit
summary: Full audit of codex/09-strategy docs against backend system — close all gaps in both directions, implement new
  strategies, add centralised on-chain primitives
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-15"
type: mixed
epic: epic-code-completion
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-trading-pm, code: C1, deployment: none, business: none }
  - { repo: strategy-service, code: C1, deployment: none, business: none }
  - { repo: execution-service, code: C1, deployment: none, business: none }
  - { repo: features-onchain-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C1, deployment: none, business: none }
  - { repo: unified-trading-system-ui, code: C1, deployment: none, business: none }
  - { repo: unified-trading-api, code: C1, deployment: none, business: none }
depends_on: []
todos:
  - { id: p0-index, content: "- [x] [AGENT] P0. Update /codex/09-strategy/README.md — strategy count 37→65+, add all
        missing entries, update domain tables, add new strategy families

        ", status: done }
  - { id: p0-catalog, content: "- [x] [AGENT] P0. Update STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md — all families
        present, 70 strategy IDs in factory, 13+ execution algos documented

        ", status: done }
  - { id: p1a-cefi-momentum, content: "- [x] [AGENT] P0. DOC: cefi/momentum.md — REAL doc (1113 words), confirmed by
        audit

        ", status: done }
  - { id: p1b-cefi-meanrev, content: "- [x] [AGENT] P0. DOC: cefi/mean-reversion.md — REAL doc (1252 words), confirmed
        by audit

        ", status: done }
  - { id: p1c-sports-arb, content: "- [x] [AGENT] P0. DOC: sports/arbitrage.md — REAL doc (1343 words), confirmed by
        audit

        ", status: done }
  - { id: p2a-cefi-ml, content: "- [x] cefi/ml-directional.md — REAL (1259 words)

        ", status: done }
  - { id: p2b-cefi-crossex, content: "- [x] cefi/cross-exchange.md — REAL (1265 words)

        ", status: done }
  - { id: p2c-cefi-statarb, content: "- [x] cefi/stat-arb.md — REAL (1367 words)

        ", status: done }
  - { id: p2d-tradfi-momentum, content: "- [x] tradfi/tradfi-momentum.md — REAL (1048 words)

        ", status: done }
  - { id: p2e-tradfi-relvol, content: "- [x] tradfi/relative-volatility.md — REAL (1127 words)

        ", status: done }
  - { id: p2f-tradfi-volsurf, content: "- [x] tradfi/volatility-surface.md — REAL (1248 words)

        ", status: done }
  - { id: p2g-tradfi-optionsmm, content: "- [x] tradfi/market-making-options.md — REAL (2050 words)

        ", status: done }
  - { id: p2h-sports-kelly, content: "- [x] sports/kelly.md — REAL (1264 words)

        ", status: done }
  - { id: p2i-sports-halftime, content: "- [x] sports/halftime-ml.md — REAL (1451 words)

        ", status: done }
  - { id: p2j-prediction-arb, content: "- [x] prediction/prediction-arb.md — REAL (1377 words)

        ", status: done }
  - { id: p3a-ethena, content: "- [x] defi/ethena-benchmark.md — REAL (2244 words)

        ", status: done }
  - { id: p3b-btc-basis, content: "- [x] defi/btc-basis-trade.md — REAL (2512 words)

        ", status: done }
  - { id: p3c-btc-lending, content: "- [x] defi/btc-lending-yield.md — REAL (2640 words)

        ", status: done }
  - { id: p3d-sol-basis, content: "- [x] defi/sol-basis-trade.md — REAL (2037 words)

        ", status: done }
  - { id: p3e-sol-staked, content: "- [x] defi/sol-staked-basis.md — REAL (2405 words)

        ", status: done }
  - { id: p3f-sol-lending, content: "- [x] defi/sol-lending-yield.md — REAL (2346 words)

        ", status: done }
  - { id: p3g-sol-lp, content: "- [x] defi/sol-concentrated-lp.md — REAL (3000 words)

        ", status: done }
  - { id: p3h-multichain-lending, content: "- [x] defi/multi-chain-lending-yield.md — REAL (2710 words)

        ", status: done }
  - { id: p3i-crosschain-yield, content: "- [x] defi/cross-chain-yield-arb.md — REAL (2648 words)

        ", status: done }
  - { id: p3j-crosschain-sor, content: "- [x] defi/cross-chain-sor-rebalancing.md — REAL (3408 words)

        ", status: done }
  - { id: p3k-l2-basis, content: "- [x] defi/l2-basis-trade.md — REAL (2550 words)

        ", status: done }
  - { id: p3l-unhedged, content: "- [x] defi/unhedged-recursive.md — REAL (4557 words)

        ", status: done }
  - { id: p4a-ml-pipeline, content: "- [x] cross-cutting/ml-pipeline.md — REAL (2424 words)

        ", status: done }
  - { id: p4b-config-arch, content: "- [x] cross-cutting/config-architecture.md — REAL (4320 words)

        ", status: done }
  - { id: p4c-margin-health, content: "- [x] cross-cutting/margin-health.md — REAL (3216 words)

        ", status: done }
  - { id: p4d-pnl-attribution, content: "- [x] cross-cutting/pnl-attribution.md — REAL (2985 words)

        ", status: done }
  - { id: p4e-prediction-markets, content: "- [x] cross-cutting/prediction-markets.md — REAL (2018 words)

        ", status: done }
  - { id: p4f-cost-modeling, content: "- [x] cross-cutting/cost-modeling.md — REAL (2819 words)

        ", status: done }
  - { id: p4g-latency, content: "- [x] cross-cutting/latency-profiles.md — REAL (2096 words)

        ", status: done }
  - { id: p4h-rate-impact, content: "- [x] cross-cutting/rate-impact-model.md — REAL (770 words); RateImpactEngine
        implemented in execution-service

        ", status: done }
  - { id: p5a-factory-promote, content: "- [x] All 6 strategies already in factory: CROSS_EXCHANGE_BTC,
        STAT_ARB_BTC_ETH, REL_VOL_BTC_ETH, VOL_SURFACE_BTC, BTC_OPTIONS_MM/ETH_OPTIONS_MM, PREDICTION_ARB_BTC

        ", status: done }
  - { id: p5b-omnichain-strategy, content: "- [x] OmnichainTransferStrategy exists at
        engine/strategies/omnichain_transfer.py, factory ID OMNICHAIN_TRANSFER

        ", status: done }
  - { id: p6a-rate-impact-engine, content: "- [x] RateImpactEngine implemented at
        execution_service/engine/rate_impact_engine.py. Dual-mode (live + batch), all 4 protocols (Aave V3, Compound V3,
        Morpho Blue, Kamino), Decimal arithmetic, 236 lines

        ", status: done }
  - { id: p6b-lst-collateral-resolver, content: "- [x] LSTCollateralResolver implemented at
        execution_service/engine/lst_collateral_resolver.py. Static venue/LST registry, staking options, decision tree
        (LST/DIRECT/HYBRID), 179 lines

        ", status: done }
  - { id: p6c-onchain-sor-service, content: "- [x] SmartOrderRouter exists at execution_service/algorithms/sor.py,
        exported as DeFiSmartOrderRouter from __init__.py. Strategy-callable via execution orchestrator.

        ", status: done }
  - { id: p6d-strategy-instruction-bus, content: "- [x] StrategyInstructionType exists in UAC
        internal/domain/strategy_service/instruction.py (MARKET_ORDER, SWAP, LEND, FLASH_LOAN, HEDGE_BASIS, etc.).
        cross-cutting/strategy-instruction-bus.md doc written (617 words).

        ", status: done }
  - { id: p6e-liquidity-leg-ordering, content: "- [x] MultiLegOrchestrator exists with LEADER_FOLLOWER mode in
        multi_leg_orchestrator.py. UAC MultiLegInstruction and MultiLegExecutionMode support leg ordering. Audit
        confirmed retry + compensation wired.

        ", status: done }
  - { id: p6f-compensation-unwind, content: "- [x] Compensation/unwind exists: _handle_follower_failure,
        UNHEDGED_POSITION_ALERT, unwind helpers in multi_leg_orchestrator.py

        ", status: done }
  - { id: p6g-retry-in-multileg, content: "- [x] ErrorAction.RETRY wired via _submit_leg_with_retry and
        _classify_leg_error in multi_leg_orchestrator.py

        ", status: done }
  - { id: p6h-multileg-doc, content: "- [x] cross-cutting/multi-leg-execution.md — REAL (925 words)

        ", status: done }
  - { id: p7a-lending-arb-backend, content: "- [x] LendingProtocolArbStrategy exists, factory IDs: LENDING_PROTOCOL_ARB,
        LENDING_PROTOCOL_ARB_ETH, LENDING_PROTOCOL_ARB_ARB

        ", status: done }
  - { id: p7a-lending-arb-doc, content: "- [x] defi/lending-protocol-arb.md — REAL (1400 words)

        ", status: done }
  - { id: p7a-lending-arb-ui, content: "- [x] lending-arb-dashboard-widget.tsx created with 4-protocol x 4-token APY
        spread table, registered in strategies tab

        ", status: done }
  - { id: p7b-liquidation-backend, content: "- [x] LiquidationCaptureStrategy exists, factory ID: LIQUIDATION_CAPTURE

        ", status: done }
  - { id: p7b-liquidation-doc, content: "- [x] defi/liquidation-cascade-capture.md — REAL (521 words)

        ", status: done }
  - { id: p7b-liquidation-ui, content: "- [x] liquidation-monitor-widget.tsx created with summary cards + at-risk
        positions table + HF color coding, registered in strategies tab

        ", status: done }
  - { id: p7c-enhanced-basis-backend, content: "- [x] EnhancedBasisTradeStrategy exists, factory IDs:
        ENHANCED_BASIS_MULTI_VENUE, ENHANCED_BASIS_MULTI_COIN

        ", status: done }
  - { id: p7c-enhanced-basis-doc, content: "- [x] defi/basis-trade.md — REAL (4171 words), includes
        multi-coin/multi-venue sections

        ", status: done }
  - { id: p7c-enhanced-basis-ui, content: "- [x] DeFi strategy config widget covers basis trade families; CeFi config
        widget covers CeFi basis. Lending arb dashboard shows per-protocol spreads.

        ", status: done }
  - { id: p7d-active-lp-backend, content: "- [x] ActiveDeFiMMStrategy exists, factory IDs: ACTIVE_LP_ETH_USDC,
        ACTIVE_LP_SOL_USDC

        ", status: done }
  - { id: p7d-active-lp-doc, content: "- [x] defi/active-defi-mm.md — REAL (1379 words)

        ", status: done }
  - { id: p7d-active-lp-ui, content: "- [x] active-lp-dashboard-widget.tsx created with TVL/fees/IL metrics, LP position
        table with in-range badges, rebalance alert. Registered in strategies tab.

        ", status: done }
  - { id: p7e-event-macro-backend, content: "- [x] EventDrivenMacroStrategy exists, factory IDs: EVENT_MACRO_CRYPTO,
        EVENT_MACRO_TRADFI

        ", status: done }
  - { id: p7e-event-macro-doc, content: "- [x] cross-cutting/event-driven-macro.md — REAL (758 words)

        ", status: done }
  - { id: p7e-event-macro-ui, content: "- [x] calendar-event-feed.tsx already exists with economic results, corporate
        actions, countdown timers. hooks/api/use-calendar.ts provides data. No new widget needed.

        ", status: done }
  - { id: p7f-commodity-backend, content: "- [x] CommodityRegimeStrategy exists, factory IDs: OIL_COMMODITY_REGIME,
        NG_COMMODITY_REGIME

        ", status: done }
  - { id: p7f-commodity-doc, content: "- [x] tradfi/commodity-regime.md — REAL (1316 words)

        ", status: done }
  - { id: p7f-commodity-ui, content: "- [x] commodity-regime-widget.tsx created with regime indicator badge, 5-factor
        scores table, active positions table. Registered in strategies tab.

        ", status: done }
  - { id: p8a-qg-pm, content: "- [x] QG on PM: 4 failures all pre-existing (deployment-ui manifest tags); plan/codex
        changes clean

        ", status: done }
  - { id: p8b-qg-strategy, content: "- [x] No changes to strategy-service code (strategies already existed); QG not
        needed

        ", status: done }
  - { id: p8c-qg-execution, content: "- [x] QG on execution-service: fixed circular import (onchain_execution_service
        lazy imports), removed dead unified_trading_library.events imports. 18/18 onchain tests pass. 54+58 pre-existing
        failures (socket-blocked, missing modules)

        ", status: done }
  - { id: p8d-qg-features, content: "- [x] No changes to features-onchain-service; QG not needed

        ", status: done }
  - { id: p8e-qg-uac, content: "- [x] No changes to unified-api-contracts; instruction types already existed; QG not
        needed

        ", status: done }
  - { id: p8f-qg-ui, content: "- [x] QG on UI: all new widgets compile cleanly (0 TS errors in new files). Pre-existing
        canvas ERR_DLOPEN_FAILED + other TS errors in unrelated files

        ", status: done }
  - { id: p9a-api-catalog, content: "- [x] GET /analytics/strategies/catalog — returns all 65 factory strategy IDs
        grouped by domain + family with parameter schemas

        ", status: done }
  - { id: p9b-api-pnl-filter, content: "- [x] GET /analytics/pnl now accepts strategy_id query param for per-strategy
        PnL attribution

        ", status: done }
  - { id: p9c-api-exec-analysis, content: "- [x] GET /execution/analysis/{execution_id} — returns full instruction
        pipeline (signal → risk → algo → routing → fills) with input/output at each step

        ", status: done }
  - { id: p9d-ui-exec-analysis-page, content: "- [x] /services/execution/[executionId] — drill-down page showing
        instruction pipeline timeline, step cards with input/output, fills table. Uses useExecutionAnalysis hook.

        ", status: done }
  - { id: p9e-ui-family-browser, content: "- [x] strategy-family-browser-widget.tsx — cross-domain strategy catalog
        browser with domain filter, family grouping, parameter badges. Registered in strategies tab Full preset. Uses
        useStrategyCatalog hook.

        ", status: done }
  - { id: p8g-qg-api, content: "- [x] QG on unified-trading-api: 3 new endpoints (strategies/catalog, pnl?strategy_id,
        execution/analysis/{id}) pass ruff lint cleanly. 50 pre-existing test failures (KeyError/AssertionError in
        unrelated routes) — not introduced by this plan.

        ", status: done }
isProject: false
---

# Strategy Docs vs System Audit — 2026-04-15

## Context

Full audit of `codex/09-strategy/` documentation against the actual backend system. The system has **59 strategy
implementations** across 4 domains; the docs cover **37 strategies** with many stubs and missing files. This plan closes
every gap in both directions, adds new strategies for untapped potential, and introduces centralised on-chain primitives
that any strategy can compose.

## Audit Findings Summary

| Category      | Docs                                        | System                                    | Gap                                         |
| ------------- | ------------------------------------------- | ----------------------------------------- | ------------------------------------------- |
| DeFi          | 6 real docs + 11 referenced-no-file         | 18 strategies + 21 protocol connectors    | 12 docs to write + 4 new strategies         |
| CeFi          | 1 real doc + 2 stubs                        | 12 strategies (9 default + 3 non-default) | 3 stubs to complete + 3 new docs            |
| TradFi        | 1-2 real docs + 4 referenced-no-file        | 8 strategies + IBKR (6 venues)            | 4 docs to write + 1 new strategy            |
| Sports        | 3 real docs + 1 stub + 2 referenced-no-file | 6 strategies + 6 betting venues           | 1 stub + 2 new docs                         |
| Prediction    | 1 cross-cutting mention                     | 1 strategy + 2 venues                     | 1 new directory + doc                       |
| Cross-cutting | 15 docs (all substantive)                   | Full risk/ML/execution/PnL infra          | 9 docs to update + 4 centralised primitives |

## Human Decisions (2026-04-15, all resolved)

1. **Omnichain transfers** → Implement OmnichainTransferStrategy wrapping BridgeConnector
2. **Rate impact model** → Dual-mode: live simulation (like slippage preview for swaps) + batch (actual execution
   prices). Must use actual protocol math per chain/protocol
3. **Lending protocol arb** → Yes. Must compose with recursive staking + multi-venue SOR
4. **Liquidation cascade capture** → Yes
5. **Cross-exchange funding rate arb** → Not a new strategy. Enhance existing basis trade to support cross-venue +
   cross-coin baskets + LST collateral decision
6. **Active DeFi MM** → Yes. ML-driven rebalancing to minimise impermanent loss
7. **Event-driven macro** → Yes. UI needs news/events feed for manual trading on signals. Backend uses calendar features
   as primary trigger
8. **Commodity regime trading** → Yes. HMM regime + 5 factors. IBKR CME execution

## Architectural Principle: Centralised Primitives

**Key insight 1:** On-chain operations (SOR, transfers, LST collateral resolution, rate impact simulation) must be
**centralised services** that any strategy can compose, not reimplemented per strategy.

**Key insight 2:** Multi-leg execution must be safe by default. Illiquid leg first, liquid hedge after. Retries for
transient errors. Automatic compensation/unwind if hedge leg fails after primary fills. No unhedged positions left
silently.

| Primitive                              | Location                                 | Used by                                                              |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------- |
| RateImpactEngine                       | execution-service or UTL                 | All lending/borrowing strategies                                     |
| LSTCollateralResolver                  | execution-service                        | All basis/staked-basis/recursive strategies                          |
| On-chain SOR service                   | execution-service (formalise existing)   | All DeFi strategies needing swaps/transfers                          |
| Strategy Instruction Bus               | UAC types + execution-service            | All strategies (typed instructions: SWAP, LEND, STAKE, BRIDGE, etc.) |
| Liquidity-aware leg ordering           | execution-service multi-leg orchestrator | All spread/basis/arb strategies                                      |
| Compensation/unwind on partial failure | execution-service multi-leg orchestrator | All non-atomic multi-leg trades                                      |
| Retry policy in multi-leg              | execution-service multi-leg orchestrator | All multi-leg trades                                                 |

## Multi-Leg Execution: Current State vs Target

**What exists:**

- 3 execution modes: SEQUENTIAL, LEADER_FOLLOWER (configurable leader index + partial fill threshold), PARALLEL
- DeFi flash loan atomicity (all-or-nothing on-chain tx revert)
- Error classification: RETRY/SKIP/FAIL via UAC `classify_venue_error()`
- 13 DeFi error codes from revert reasons
- Intent engine with `depends_on` dependency DAG + `multicall_group` batching

**What's missing (Phase 6E-6H):**

- No automatic liquidity-based leg ordering (strategy must manually set leader_leg_index)
- No compensation/unwind when leg 1 fills but leg 2 fails in non-atomic (CeFi) mode
- Retry classification exists but isn't wired into multi-leg orchestrator flow
- No PRIMARY/HEDGE leg tagging in strategy instructions

## Execution DAG

```
Phase 0: Index + Catalog update ──────────────────────────────────────────────┐
    │                                                                          │
Phase 1: Complete 3 stubs ─── PARALLEL                                        │
Phase 2: Write 10 missing docs ─── PARALLEL                                   │
Phase 3: Write 12 DeFi variant docs ─── PARALLEL                              │
Phase 4: Update 9 cross-cutting docs ─── PARALLEL                             │
    │                                                                          │
    ├── All doc phases are PARALLEL with each other AND with Phase 5/6 ────────┘
    │
Phase 5: Promote 6 strategies + implement OmnichainTransferStrategy ─── strategy-service
    │
Phase 6: Centralised primitives + execution hardening ─── MIXED
    │   6a: RateImpactEngine (prerequisite for 7a, 7c)
    │   6b: LSTCollateralResolver (prerequisite for 7c)
    │   6c: On-chain SOR service formalisation
    │   6d: Strategy Instruction Bus (UAC types, prerequisite for 6e leg tagging)
    │   6e: Liquidity-aware leg ordering (PARALLEL with 6a-6c)
    │   6f: Compensation/unwind on partial failure (depends on 6g for retry)
    │   6g: Retry policy wired into multi-leg orchestrator (PARALLEL with 6e)
    │   6h: Doc: cross-cutting/multi-leg-execution.md (after 6e-6g)
    │
Phase 7: New strategies (backend + doc + UI per strategy) ─── PARALLEL
    │   7a: LendingProtocolArb (depends on 6a)
    │   7b: LiquidationCascadeCapture
    │   7c: Enhanced Basis Trade (depends on 6a, 6b, 6e for leg ordering)
    │   7d: ActiveDeFiMM
    │   7e: EventDrivenMacro (+ UI news feed)
    │   7f: CommodityRegime
    │
Phase 8: Quality gates — all affected repos
```

**Phases 1-4 + Phase 5 + Phase 6 run in PARALLEL** (doc writes don't block code). **Phase 6e-6g are PARALLEL** with
6a-6d (different parts of execution-service). **Phase 7 items are PARALLEL** except 7a depends on 6a, 7c depends on
6a+6b+6e.

## Repos Affected

| Repo                      | Change type                                                  | Phase |
| ------------------------- | ------------------------------------------------------------ | ----- |
| unified-trading-pm        | ~35 doc files in codex/09-strategy/                          | 0-4   |
| strategy-service          | Factory promotion + 7 new strategy classes                   | 5, 7  |
| execution-service         | RateImpactEngine, LSTCollateralResolver, SOR formalisation   | 6     |
| unified-api-contracts     | Strategy instruction types (IntentType extensions)           | 6d    |
| unified-trading-library   | RateImpactEngine if placed here instead of execution-service | 6a    |
| features-onchain-service  | Rate impact live mode if needed                              | 6a    |
| unified-trading-system-ui | 6+ new dashboard panels, news/events feed                    | 7     |
| unified-trading-api       | 6+ new API endpoints for strategy dashboards                 | 7     |

## Doc Writing Guidelines

All new strategy docs MUST follow `templates/strategy-description-template.md` (20-section template). Key sections:

- Overview, Token/Position Flow, Instruments table, Key Features Consumed, PnL Attribution, Risk Profile
- **Source content from the actual strategy class implementation** — read the code, don't guess
- Cross-reference execution adapters, feature services, risk checks, and centralised primitives
- For new strategies (Phase 7): write doc concurrently with implementation, doc describes target state
