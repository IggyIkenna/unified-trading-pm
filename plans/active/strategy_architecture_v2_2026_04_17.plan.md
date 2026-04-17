---
name: Strategy Architecture v2 — Family / Archetype / Axes / Cross-Cutting
status: active
owner: iggy
started: 2026-04-17
locked_by: live-defi-rollout
locked_since: 2026-04-17
---

# Strategy Architecture v2 — Implementation Plan

## Context

Canonical architecture converged across two prior sessions (2026-04-16 → 2026-04-17):

- **8 families** (orthogonal alpha styles): ML Directional, Rules Directional, Carry & Yield, Arbitrage/Structural,
  Market Making, Event-Driven, Vol Trading, Stat Arb/Pairs
- **18 archetypes** (code paths under families)
- **7 axes of composition**: signal source, edge method, staking method, venue eligibility, expression, hold policy,
  share class
- **10 cross-cutting concerns**: risk gates (4-layer), venue selection split, execution policies, transfer/rebalance,
  portfolio allocator, MEV protection, benchmark fills, capital/client isolation, trade expression, venue-account
  coordination
- **5-layer identity**: family → archetype → instance → config → derived categories
- **3-axis versioning**: code/build, artifact, schema
- **Polymorphic StrategyInstruction** (11 actions) + parallel AccountInstruction
- **3 backtest groups**: A (ML training), B (strategy alpha), C (execution alpha)
- **Batch = live** (benchmark fills contract)
- **Capital custody models** per category (CeFi SMA, CeFi fund future, DeFi client wallet, DeFi firm, Unity pool, sports
  direct, TradFi IBKR, TradFi counterparty)
- **Fund-client framing**: we face ONE client which may itself be a fund
- **Unity meta-broker**: 10 child books, single TCP, USD share class, Java Feed Connector sidecar
- **Kraken removed everywhere**

Supersedes legacy category-based organization in `09-strategy/{cefi,defi,sports,tradfi,prediction}/`. See
`codex/09-strategy/architecture-v2/MIGRATION.md` for complete old-doc → new-archetype mapping.

## Doc-writing progress (Phase 1)

- [x] [DOC] P0. Inventory existing strategy docs (cefi/defi/tradfi/sports/prediction + cross-cutting) to build migration
      reference
- [x] [DOC] P0. Create codex/09-strategy/architecture-v2/README.md (full taxonomy + Capital Flow Lifecycle section)
- [x] [DOC] P0. Create codex/09-strategy/architecture-v2/MIGRATION.md (56 legacy docs → v2 placement audit)
- [x] [DOC] P0. Update codex/04-architecture/capital-structure-and-regulatory.md with fund-client framing + per-category
      custody
- [x] [DOC] P0. Write 8 family docs in architecture-v2/families/ (ml-directional, rules-directional, carry-and-yield,
      arbitrage-structural, market-making, event-driven, vol-trading, stat-arb-pairs) — all include "Not in this family"
- [x] [DOC] P0. Write 18 archetype docs in architecture-v2/archetypes/ — all include "Not in this archetype"
- [x] [DOC] P0. Write axes/signal-sources.md
- [x] [DOC] P0. Write axes/edge-methods.md
- [x] [DOC] P0. Write axes/staking-methods.md
- [x] [DOC] P0. Write axes/venue-eligibility.md
- [x] [DOC] P0. Write axes/expression.md
- [x] [DOC] P0. Write axes/hold-policy.md
- [x] [DOC] P0. Write axes/share-class.md
- [x] [DOC] P0. Write cross-cutting/risk-gates.md
- [x] [DOC] P0. Write cross-cutting/venue-selection-split.md
- [x] [DOC] P0. Write cross-cutting/execution-policies.md
- [x] [DOC] P0. Write cross-cutting/transfer-rebalance.md
- [x] [DOC] P0. Write cross-cutting/portfolio-allocator.md
- [x] [DOC] P0. Write cross-cutting/mev-protection.md
- [x] [DOC] P0. Write cross-cutting/benchmark-fills.md
- [x] [DOC] P0. Write cross-cutting/capital-client-isolation.md
- [x] [DOC] P0. Write cross-cutting/trade-expression.md
- [x] [DOC] P0. Write cross-cutting/venue-account-coordination.md
- [x] [DOC] P0. Write codex/04-architecture/strategy-execution-protocol.md
- [x] [DOC] P0. Write codex/04-architecture/artifact-versioning.md
- [x] [DOC] P0. Write codex/04-architecture/execution-policy.md
- [x] [DOC] P0. Write codex/04-architecture/backtest-groups.md
- [x] [DOC] P0. Write codex/04-architecture/capital-flow-model.md
- [x] [DOC] P0. Write codex/04-architecture/schema-versioning.md
- [x] [DOC] P0. Write codex/04-architecture/slow-fast-routing-split.md
- [x] [DOC] P0. Write codex/04-architecture/capital-efficiency-patterns.md
- [x] [DOC] P0. Write codex/04-architecture/account-instructions.md
- [x] [DOC] P0. Write codex/02-venues/venue-registry-reference.md
- [x] [DOC] P0. Write codex/02-venues/prime-brokers.md
- [x] [DOC] P0. Write codex/02-venues/unity-integration.md
- [x] [DOC] P0. Write codex/03-services/portfolio-allocator.md
- [x] [DOC] P0. Write codex/03-services/venue-capability-registry.md
- [x] [DOC] P0. Write codex/06-coding-standards/strategy-identity-versioning.md
- [x] [DOC] P0. Write codex/06-coding-standards/artifact-naming.md

## Apply consistently to all remaining docs

- [ ] [RULE] Every family, archetype, axis, and cross-cutting doc MUST have a "Not in this X" section — makes grey areas
      explicit and anchors understanding against the full surface. Feedback from user: "It's not that I think we should
      have that in all of the docs; you put it in most of the families, so just put it in all the rest as well. Maybe
      archetypes as well."

## Outstanding architectural decisions (TBDs)

- [ ] [TBD] Unity 10 child books — 8 confirmed with commissions, 2 pending from quant-portal.olesportsresearch.com/unity
      (user-assisted)
- [ ] [TBD] Exact Kelly fraction defaults per archetype
- [ ] [TBD] Allocator cadence defaults per client size
- [ ] [TBD] Shadow deployment pattern specifics for archetype upgrades
- [ ] [TBD] Delta-neutral exit pathway when kill-switch fires on one venue but another eligible venue is alive
      (confirmed: delta-neutral exit default; reduction only if DATA_STALE)

## Phase 2 — UAC schema additions (LANDED)

Commit: `unified-api-contracts@4bc83bc` on `live-defi-rollout`.

- [x] [CODE] P1. Polymorphic StrategyInstruction (11 action variants + AccountInstruction) — `internal.architecture_v2.schemas`
- [x] [CODE] P1. Archetype / Instance / Config tiers as typed registry — `StrategyInstanceIdentity` + `StrategyInstanceDefinition`
- [x] [CODE] P1. Venue capability with haircuts, LTV, collateral, portfolio margin spec — `VenueCapabilityV2`, `LtvAndHaircut`, `CollateralRulesV2`, `MarginSpec`, `NettingRule`, `CommissionStructureV2`
- [x] [CODE] P1. Compatibility matrix (archetype, venue-category, action, instrument-type) — `CompatibilityEntry` + `COMPATIBILITY_SEED`
- [x] [CODE] P1. AllocationDirective schema (portfolio allocator → strategy equity) — `AllocationDirective` + `StrategyEquityDirective`
- [x] [CODE] P1. Child venue schema (Unity child books) — `UnityChildVenue` + `UNITY_CHILD_BOOKS` (10: 8 confirmed + 2 TBD)
- [x] [CODE] P1. venue_type enum (SINGLE_VENUE, META_BROKER, DATA_AGGREGATOR) — `VenueType`
- [x] [CODE] P1. Remove Kraken from UAC venue registry + adapters + credentials registry — external/kraken/ deleted, _KRAKEN SourceCapability removed, endpoint registry purged. External-provider-inventory mocks (tardis, defillama) retain Kraken in recorded responses (cassette parity).
- [ ] [CODE] P1. Remove Kraken from downstream consumers (execution-service adapters, MTDS adapters, UTL, credentials registry, deployment scripts) — workspace-wide sweep still TODO

## Phase 3 — Strategy-service refactor

- [ ] [CODE] P1. 18 family engines + archetype handlers + instance registry + config hash/version (strategy-service)

## Phase 4 — Execution-service polymorphic orchestrator

- [ ] [CODE] P1. 11 action handlers (TRADE, SWAP, LEND, BORROW, STAKE, UNSTAKE, QUOTE, TRANSFER, BRIDGE, ATOMIC, CANCEL)
- [ ] [CODE] P1. Execution policy registry (rule-table per venue×action×condition, artifact-versioned)
- [ ] [CODE] P1. Venue-account pre-flight
- [ ] [CODE] P1. ATOMIC multi-leg + LEADER_HEDGE sequencing
- [ ] [CODE] P1. Benchmark fills per action type
- [ ] [CODE] P1. META_BROKER child-venue SOR (Unity)
- [ ] [CODE] P1. Unity adapter: TCP feed connector sidecar, Python bridge, all 3 sports enabled, bet placement, wallet
      sync, rollover tracking, turnover for subscription waiver

## Phase 5 — Portfolio-allocator-service (new)

- [ ] [CODE] P1. 8 allocator archetypes: FIXED, PNL, SHARPE, RISK_PARITY, KELLY, MIN_CVAR, REGIME, MANUAL
- [ ] [CODE] P1. Per-client instances + AllocationDirective events

## Phase 6 — PBMS

- [ ] [CODE] P1. Venue-account aggregation view
- [ ] [CODE] P1. Strategy + venue-account dual projections
- [ ] [CODE] P1. Fill reconciliation
- [ ] [CODE] P1. Unity child-book position attribution

## Phase 7 — Risk-and-exposure-service

- [ ] [CODE] P1. Venue-account pre-flight checks
- [ ] [CODE] P1. Margin simulation with haircuts
- [ ] [CODE] P1. Family-level limits
- [ ] [CODE] P1. Kill switch coordination (multi-venue rules: delta-neutral exit default)

## Phase 8 — Features + ML

- [ ] [CODE] P1. Feature group versioning + artifact registry emission
- [ ] [CODE] P1. Model versioning + artifact registry emission

## Phase 9 — UI

- [ ] [CODE] P2. Family-first navigation, category-as-filter
- [ ] [CODE] P2. 8 family dashboards + archetype/instance/config views + dependency tab
- [ ] [CODE] P2. Allocator UI
- [ ] [CODE] P2. Venue capability view + execution policy view
- [ ] [CODE] P2. Unity dashboard

## Phase 10 — Backtest runners

- [ ] [CODE] P2. Group A (ML training)
- [ ] [CODE] P2. Group B (strategy) — uses benchmark fills
- [ ] [CODE] P2. Group C (execution alpha) — measures alpha vs benchmark

## Phase 11 — Strategy migration

- [ ] [CODE] P1. Map existing 53 strategies to archetype + instance + config
- [ ] [CODE] P1. Emit v1 configs; retire legacy naming
- [ ] [CODE] P2. Build remaining strategy instances to fill target universe (~240-250 v1, ceiling ~300-350)

## Success criteria

- All ~60 docs written + QG pass on PM repo
- Every archetype has a typed engine with tests
- Every instruction action has a handler with benchmark-fills contract
- All 53 legacy strategies mapped to archetype + instance + config
- UAC schema additions pass QG in all consumer repos
- UI navigates by family-first
- Kraken fully removed from codebase (grep returns zero matches)
- Docs wave: every family/archetype/axis/cross-cutting doc has "Not in this X" section

## Reference points for migration

- Legacy docs remain at `codex/09-strategy/{cefi,defi,sports,tradfi}/` and `codex/09-strategy/cross-cutting/` —
  referenced from MIGRATION.md, deleted only after each legacy doc's functionality is verified in v2
- Legacy code modules enumerated in MIGRATION.md with target archetype mapping
- e2e-testing configs enumerated with archetype assignment per strategy

## Related prior plans (partial overlap, do not duplicate)

- `strategy_docs_vs_system_audit_2026_04_15.plan.md` — closed gaps in codex/09-strategy docs vs backend implementations
- `identity_registry_and_shard_enrichment_2026_04_16.plan.md` — UAC strategy registry SSOT, unified TradingAccount
  model, SCE enforcement
- `consolidated_strategy_and_ui_2026_04_15.plan.md` — strategy lifecycle UI integration
- `autonomous_recovery_and_transfer_architecture_2026_04_16.plan.md` — G1-G5 recovery, transfer type router
- `strategy_system_citadel_master_2026_03_15.plan.md` (ai/) — prior citadel-grade master; superseded by v2 architecture
