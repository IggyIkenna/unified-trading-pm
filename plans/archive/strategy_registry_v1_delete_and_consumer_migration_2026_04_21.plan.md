---
doc_type: plan
title: strategy-registry-v1-delete-and-consumer-migration-2026-04-21
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
overview:
  Delete unified-trading-system-ui/lib/strategy-registry.ts (7780 LOC) + legacy-family-migration helpers. Migrate 18
  consumer files to v2-sourced data (lib/architecture-v2/coverage.ts + regenerated mock fixture derived from UAC
  STRATEGY_REGISTRY). Purge 3 Elysium rows from mock-data-seed.ts + positions-data-context.tsx + ui-reference-data.json.
type: refactor
epic: epic-code-completion
completion_gates: { code: C4, deployment: none, business: none }
repo_gates:
  - { repo: unified-trading-system-ui, code: C4, deployment: none, business: none }
depends_on: [ui_unification_v2_sanitisation_2026_04_20]
todos:
  - { id: p1-consumer-surface-audit, content: "- [x] [AGENT] P0. For each of the 18 consumer files in the Pre-Audit
        Manifest below, document (a) which v1 STRATEGIES field each consumer reads, (b) RICH vs LEAN mock data
        requirements, (c) proposed v2 source. Emit pre-audit manifest at
        plans/active/strategy_registry_v1_delete_consumer_audit.md.

        ", status: completed }
  - { id: p2-regenerate-mock-fixture, content: "- [x] [AGENT] P0. Regenerate
        unified-trading-system-ui/lib/mocks/fixtures/strategy-catalog-data.ts from UAC STRATEGY_REGISTRY (99 entries
        post Wave 6). Preserve only the shape consumers need per Phase 1 audit. Source:
        unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py. Drop 3 Elysium rows
        (retired). Add NFL/MLB value-bet + TLT/IEF stat-arb mappings (already present as representative slot labels in
        UAC manifest).

        ", status: completed }
  - { id: p3a-migrate-trading-strategy-detail, content: "- [x] [AGENT] P0. Migrate the 3 strategy-detail files under
        app/(platform)/services/trading/strategies/[id]/* from getStrategyById / STRATEGIES to v2 sources.
        Archetype/family from lib/architecture-v2/coverage.ts + enums.ts. Drop legacyFamilyToV2() calls.

        ", status: completed }
  - { id: p3b-migrate-widgets, content: "- [x] [AGENT] P0. Migrate 5 widget files —
        components/widgets/book/book-data-context.tsx +
        components/widgets/strategies/{strategies-catalogue-widget,strategies-data-context}.tsx +
        components/widgets/terminal/{order-entry-widget,use-terminal-page-data}.{tsx,ts}.

        ", status: completed }
  - { id: p3c-migrate-pnl-and-lib, content: "- [x] [AGENT] P0. Migrate components/trading/pnl-waterfall.tsx +
        lib/mocks/fixtures/trading-data.ts + lib/stores/scope-helpers.ts + lib/execution-mode-context.tsx +
        lib/taxonomy.ts + app/(platform)/services/research/strategy/families/_components/aggregation.ts.

        ", status: completed }
  - { id: p4-elysium-purge, content: "- [x] [AGENT] P0. Remove all ELYSIUM_ references from
        lib/mocks/fixtures/mock-data-seed.ts + components/widgets/positions/positions-data-context.tsx +
        lib/registry/ui-reference-data.json. Elysium is a retired venue (workspace CLAUDE.md); v1 rows are RETIRED by
        design. See /codex/09-strategy/architecture-v2/legacy-family-migration.md § 2.1 Wave 6.

        ", status: completed }
  - { id: p5-delete-v1-artefacts, content: '- [x] [AGENT] P0. After Phases 3 + 4 done AND `rg
        "from.*strategy-registry|legacyFamilyToV2" unified-trading-system-ui/{app,components,lib}` returns ZERO matches,
        delete unified-trading-system-ui/lib/strategy-registry.ts (7780 LOC) +
        unified-trading-system-ui/lib/architecture-v2/legacy-mapping.ts +
        unified-trading-system-ui/tests/unit/lib/strategy-registry.test.ts + any re-exports from
        lib/architecture-v2/index.ts. Delete dead type aliases (StrategyV1, LegacyFamilyString, etc.) if zero consumers
        remain.

        ', status: completed }
  - { id: p6-update-tests, content: '- [x] [AGENT] P0. Update tests/unit/lib/stores/scope-helpers.test.ts to use v2
        sources. Grep tests/e2e/** for
        `legacy.*family|strategy-registry\.ts|SPORTS_VALUE|ELYSIUM_|TRADFI_BOND_MEAN_REV_HUF_1D` and migrate any
        Playwright spec fixtures. Run `CI=true npm test -- --run` — all green modulo pre-existing coverage-floor
        baseline.

        ', status: completed }
  - { id: p7-final-qg, content: "- [x] [AGENT] P0. Run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` —
        all green. Coverage floor may still fail at the pre-existing baseline; that's OK if delta is non-negative.
        Update INDEX.md (remove this plan's entry + reference completion commit). Request human unlock of parent
        ui_unification_v2_sanitisation_2026_04_20.md. Archive both plans.

        ", status: completed }
---

### Wave 6 prerequisite closure (all DONE 2026-04-21)

- UAC `unified-api-contracts@b7c15d2` — slot labels added for sports value-bet + TradFi treasury-ETF stat-arb.
- PM `unified-trading-pm@533a732f` — codex decision docs (`value-betting-archetype-decision.md` +
  `tradfi-bond-instrument-type-decision.md`) + `legacy-family-migration.md` re-verdicted (0 gap / 53 equivalent / 3
  retired).
- UI `unified-trading-system-ui@27c1d71` — coverage.ts regenerated to mirror UAC manifest.
- Decision: NO new archetypes, NO new instrument types. Value-betting is an `EdgeMethod` axis on
  `ML_DIRECTIONAL_EVENT_SETTLED`; Treasury ETFs are spot equities. System-First.

### 18 consumers (from `rg "strategy-registry|STRATEGY_REGISTRY_V1|legacyFamilyToV2|LegacyFamily"`)

1. `app/(platform)/services/research/strategy/families/_components/aggregation.ts`
2. `app/(platform)/services/trading/strategies/[id]/strategy-detail-page-client.tsx`
3. `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-tab-panels.tsx`
4. `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-archetype-panel.tsx`
5. `components/trading/pnl-waterfall.tsx`
6. `components/widgets/book/book-data-context.tsx`
7. `components/widgets/strategies/strategies-catalogue-widget.tsx`
8. `components/widgets/strategies/strategies-data-context.tsx`
9. `components/widgets/terminal/order-entry-widget.tsx`
10. `components/widgets/terminal/use-terminal-page-data.ts`
11. `lib/architecture-v2/index.ts` (re-export — just remove)
12. `lib/architecture-v2/legacy-mapping.ts` (the `legacyFamilyToV2` helper)
13. `lib/execution-mode-context.tsx`
14. `lib/mocks/fixtures/trading-data.ts`
15. `lib/stores/scope-helpers.ts`
16. `lib/taxonomy.ts`
17. `tests/unit/lib/stores/scope-helpers.test.ts`
18. `tests/unit/lib/strategy-registry.test.ts` (self-test — delete entire file)

### Pre-Audit Manifest — Files to touch

| File                                                                   | Action                                      |
| ---------------------------------------------------------------------- | ------------------------------------------- |
| `lib/strategy-registry.ts`                                             | DELETE                                      |
| `lib/architecture-v2/legacy-mapping.ts`                                | DELETE                                      |
| `lib/architecture-v2/index.ts`                                         | Remove re-export                            |
| `lib/mocks/fixtures/strategy-catalog-data.ts`                          | REGENERATE from UAC STRATEGY_REGISTRY       |
| `lib/mocks/fixtures/mock-data-seed.ts`                                 | PURGE Elysium entries                       |
| `lib/mocks/fixtures/trading-data.ts`                                   | Migrate to v2                               |
| `lib/registry/ui-reference-data.json`                                  | Regen / purge Elysium + stale v1 archetypes |
| `lib/stores/scope-helpers.ts`                                          | Migrate                                     |
| `lib/execution-mode-context.tsx`                                       | Migrate                                     |
| `lib/taxonomy.ts`                                                      | Drop v1 StrategyArchetype types or archive  |
| `app/(platform)/services/trading/strategies/[id]/*` (3 files)          | Migrate to v2                               |
| `app/(platform)/services/research/strategy/families/_components/*` (1) | Migrate to v2                               |
| `components/trading/pnl-waterfall.tsx`                                 | Migrate                                     |
| `components/widgets/book/book-data-context.tsx`                        | Migrate                                     |
| `components/widgets/positions/positions-data-context.tsx`              | Purge Elysium                               |
| `components/widgets/strategies/*` (2)                                  | Migrate to v2                               |
| `components/widgets/terminal/*` (2)                                    | Migrate to v2                               |
| `tests/unit/lib/strategy-registry.test.ts`                             | DELETE                                      |
| `tests/unit/lib/stores/scope-helpers.test.ts`                          | Migrate fixtures                            |
| `tests/e2e/**`                                                         | Grep + migrate any v1 fixture refs          |

### Success Criteria

| Phase | Gate           | Validation                                                                                        |
| ----- | -------------- | ------------------------------------------------------------------------------------------------- |
| 1     | Audit complete | pre-audit manifest committed; every consumer has a documented v2 replacement                      |
| 2     | Mock fixture   | strategy-catalog-data.ts regenerated; shape v2-canonical                                          |
| 3     | Consumers      | 13 consumer files compile clean; `rg "from.*strategy-registry"` returns 0 from app/components/lib |
| 4     | Elysium        | `rg "ELYSIUM_" unified-trading-system-ui/{app,components,lib}` returns 0                          |
| 5     | Delete         | Files deleted; compile clean                                                                      |
| 6     | Tests          | vitest + Playwright green (modulo pre-existing baseline)                                          |
| 7     | Finalise       | QG green; INDEX updated; parent plan unlocked                                                     |

### Non-Goals

- Adding new archetypes or instrument types (Wave 6 decided against — see
  `codex/09-strategy/architecture-v2/{value-betting-archetype-decision.md,tradfi-bond-instrument-type-decision.md}`).
- Lifting UI coverage-floor baseline (42.75% → 70%). Unrelated.
- Deleting legacy `taxonomy.ts` types still used by lifecycle-nav / testing-stage UIs (audit will clarify).

### References

- Parent plan: `plans/active/ui_unification_v2_sanitisation_2026_04_20.md`
- Wave 6 migration report: `/codex/09-strategy/architecture-v2/legacy-family-migration.md` § 2.1
- UAC STRATEGY_REGISTRY: `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py`
- UI coverage SSOT: `unified-trading-system-ui/lib/architecture-v2/coverage.ts` (AUTO-GEN from UAC manifest)
