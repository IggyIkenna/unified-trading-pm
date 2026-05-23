---
name: strategy_master
title: "Strategy Master (L2)"
type: epic
tier: L2
status: active
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/compute_optimization_mock_data_2026_05_13.md
  - ../archive/2026_05/config_grid_archetype_extend_2026_05_20.md
  - ../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - ../active/defi_recursive_borrow_archetypes_2026_05_10.md
  - ../active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md
  - ../archive/2026_05/strategy_archetype_taxonomy_2026_05_12.md
  - ../archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md
  - ../archive/2026_05/strategy_repo_consolidation_2026_05_19.md
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# Strategy Master (L2)

**Owns**: strategy-service post-consolidation 2026-05-19 (engine + portfolio_allocator + risk + position + pnl + 53
archetype engines); per-client subprocess isolation; archetype lifecycle.

**Assigned VM**: `vm-trading-core` (co-located with `execution_master` + `trading_agent_master`).

## Scope inherited from `strategy_and_dart_master_SUPERSEDED_2026_05_21` (split 2026-05-21)

The pre-2026-05-21 `strategy_and_dart_master` umbrella was split into two everlasting epics. **This epic owns the
strategy side**:

- **Archetype engine v2 finalization** — factory cutover, shadow deployment registry + ledger, 18-archetype shadow
  observation, capability gaps (SOR, hold-policy mixin, transfer-rebalance integration, benchmark-fills, dated-future
  roll, IM/Trading allocator split).
- **Cross-domain alpha + strategy lifecycle visibility** — UAC schemas + UTL SLA engine + DataQualityScorer +
  cross-domain calc + DeFi alpha features + execution cost prediction.
- **53 archetypes** per `codex/09-strategy/architecture-v2/archetypes/` — closed-set strategy taxonomy.
- **Portfolio allocator** + risk_rules + position-balance-monitor + pnl-attribution (consolidated into strategy-service
  2026-05-19).

DART operator UX + promote workflow scope went to [`dart_and_promote_master.md`](dart_and_promote_master.md) (L3). Full
archaeology: [`strategy_and_dart_master_SUPERSEDED_2026_05_21.md`](strategy_and_dart_master_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`codex/09-strategy/architecture-v2/`](../../codex/09-strategy/architecture-v2/) — strategy v2 SSOT (53 archetypes
  - 7 axes + 11 cross-cutting + 2 architecture docs)
- [`codex/04-architecture/shadow-deployment-pattern.md`](../../codex/04-architecture/shadow-deployment-pattern.md) —
  shadow window contract for archetype builds
- [`codex/11-project-management/epic-execution-with-sub-agents.md`](../../codex/11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT (pointer to [`README.md`](README.md))

## Composition with other epics

- **Upstream**: `mtds_mdps_master` (raw market data) + `features_and_ml_master` (features + ML inference) +
  `instruments_master` (universe SSOT) + `manifest_master` (data completeness gate)
- **Downstream**: `execution_master` (handlers + transfers) + `trading_agent_master` (closed-loop allocator directives)
- **Operator surfaces**: `dart_and_promote_master` (DART UI + promote workflow consumes strategy maturity phases)
- **Cross-cutting**: `client_isolation_and_governance_master` (per-client isolation + share-class registry +
  jurisdiction restrictions affect strategy emit)

## Assigned active plans

_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## Assigned active plans

_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`defi_recursive_borrow_archetypes_2026_05_10`](../active/defi_recursive_borrow_archetypes_2026_05_10.md)

**status**: active · **estimate**: 42.3 cal AI-days (class: design)

### [`strategy_archetype_taxonomy_2026_05_12`](../archive/2026_05/strategy_archetype_taxonomy_2026_05_12.md)

**status**: ✅ ARCHIVED 2026-05-21 — 100% complete (0 open todos); taxonomy + share-class neutrality + recursive carry
rename shipped

### [`strategy_repo_consolidation_2026_05_19`](../archive/2026_05/strategy_repo_consolidation_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-11 done (3-repo merge + all cleanup); P2 StrategyDirectiveReloader
DEFERRED-POST-CUTOVER · **estimate**: 12 cal AI-days (class: infra)

## P1 — important; post-current-gate

### [`compute_optimization_mock_data_2026_05_13`](../active/compute_optimization_mock_data_2026_05_13.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: design)

### [`config_grid_archetype_extend_2026_05_20`](../archive/2026_05/config_grid_archetype_extend_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 3 items DEFERRED-OPERATOR-DECISION (critical mismatch between plan's proposed
dimension names and actual engine params; no operator response since 2026-05-20). · **estimate**: 2.4 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — post-cutover backlog:

- **Confirm per-archetype grid dimension names (P0, BLOCKED-OPERATOR-DECISION)**: Operator must align dims with actual
  engine params or add proposed params to engines first. `ARBITRAGE_CROSS_DOMAIN_EVENT` needs engine factory entry.
- **Implement grid branches + smoke tests (P0)**: Gate: operator decision above.

## P2 — useful; opportunistic

### [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`](../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)

**status**: active · **estimate**: 12 cal AI-days (class: design)

### [`defi_recursive_borrow_archetypes_post_cutover_2026_06_01`](../active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md)

**status**: scope-narrowed · **estimate**: 24 cal AI-days (class: brand-new)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Archived plans

### [`strategy_execution_contract_remediation_2026_05_20`](../archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-5+Q done: strategy manifest emission (`record_captured`/`record_failed`),
`resolve_bucket_name(kind="strategy-store")` bucket SSOT, preflight gate via `validate_config_can_run()`, error
classification (`ADAPTER_FETCH_FAILED`), QG ratchet, codex SSOT updated. · **estimate**: 3.0 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — P0 operator-decision:

- **4c. Per-AG → unified bucket migration**: CeFi bucket has 237 files (~19MB) dev backtest data (2025-01-01). All
  prod per-AG buckets are 0-byte. Operator choose: (a) abandon old dev data + delete per-AG buckets, OR (b) write
  migration script (old `strategy_instructions/<id>/<date>.parquet` → new `strategy_instructions/client_id=/.../`).
  BLOCKED-OPERATOR-DECISION. Ping filed slot-6 2026-05-23.
