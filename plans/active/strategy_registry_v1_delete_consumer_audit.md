# v1 strategy-registry consumer audit (Wave 7 pre-audit manifest)

**Status:** Completed 2026-04-21 as Phase 1 of
`plans/active/strategy_registry_v1_delete_and_consumer_migration_2026_04_21.plan.md`.

## Shape summary

The v1 `Strategy` interface (declared in `lib/strategy-registry.ts`) carries 30+ fields per strategy —
`id / name / description / strategyIdPattern / clientId / assetClass / strategyType / archetype / executionMode / status / version / deployedAt / instruments[] / featuresConsumed[] / dataArchitecture / sorEnabled / sorConfig / pnlAttribution / riskProfile / latencyProfile / riskSubscriptions[] / testingStatus[] / configParams[] / crossAssetLink? / venues[] / performance / sparklineData[] / references? / instructionTypes[] / kellySizing?`.

The v2 `StrategyRegistry` (UAC `unified_api_contracts.internal.domain.strategy_service.registry`) stores only the
canonical fields needed for routing + resolution —
`strategy_id (slot label) / name / family / category / archetype / coverage_status` (6 fields, 99 entries post Wave 6).

Consumers fall into two groups:

- **LEAN consumers** — only need {id, name, family, category, archetype, clientId, status, venues, assetClass,
  performance}. These migrate to the v2 shape directly + derive the rest from the slot label.
- **RICH consumers** — the 3 strategy-detail pages under `app/(platform)/services/trading/strategies/[id]/` lean on
  `instruments / pnlAttribution / riskProfile / latencyProfile / configParams / testingStatus / dataArchitecture`. For
  these we regenerate a v2-canonical mock fixture (`lib/mocks/fixtures/strategy-instances.ts`) that wraps the 99 UAC
  entries with per-slot mock-data. The v1 `Strategy` type is renamed `StrategyInstance` and relocated there.

## Consumer-by-consumer audit

| #   | File                                                                                             | v1 fields read                                                                                                | Shape bucket     | v2 source                                                                                                                 |
| --- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1   | `app/(platform)/services/research/strategy/families/_components/aggregation.ts`                  | `STRATEGY_CATALOG.family` (free-text)                                                                         | LEAN             | Regenerated `strategy-catalog-data.ts`; `family` is already v2-canonical after Phase 2 so `legacyFamilyToV2()` is deleted |
| 2   | `app/(platform)/services/trading/strategies/[id]/strategy-detail-page-client.tsx`                | `STRATEGIES, getStrategyById, generatePnLBreakdown, generatePositionsForStrategy, Strategy, PnLBreakdownData` | RICH             | New `lib/mocks/fixtures/strategy-instances.ts` re-exports all these (StrategyInstance shape preserved)                    |
| 3   | `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-tab-panels.tsx`      | `type {PnLBreakdownData, Strategy}`                                                                           | RICH             | Same — types re-exported from `strategy-instances.ts`                                                                     |
| 4   | `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-archetype-panel.tsx` | `type Strategy`                                                                                               | RICH             | Same                                                                                                                      |
| 5   | `components/trading/pnl-waterfall.tsx`                                                           | `type PnLBreakdownData`                                                                                       | LEAN (type-only) | `strategy-instances.ts`                                                                                                   |
| 6   | `components/widgets/book/book-data-context.tsx`                                                  | `STRATEGIES as REGISTRY_STRATEGIES` (used as dropdown source)                                                 | LEAN             | `strategy-instances.ts` STRATEGY_INSTANCES                                                                                |
| 7   | `components/widgets/strategies/strategies-catalogue-widget.tsx`                                  | `type Strategy`                                                                                               | RICH (UI only)   | `strategy-instances.ts` StrategyInstance type                                                                             |
| 8   | `components/widgets/strategies/strategies-data-context.tsx`                                      | `STRATEGIES, getTotalAUM, getTotalMTDPnL, getTotalPnL, Strategy`                                              | RICH             | `strategy-instances.ts`                                                                                                   |
| 9   | `components/widgets/terminal/order-entry-widget.tsx`                                             | `STRATEGIES`                                                                                                  | LEAN             | `strategy-instances.ts`                                                                                                   |
| 10  | `components/widgets/terminal/use-terminal-page-data.ts`                                          | `STRATEGIES, Strategy`                                                                                        | LEAN             | `strategy-instances.ts`                                                                                                   |
| 11  | `lib/architecture-v2/index.ts`                                                                   | re-exports `legacy-mapping.ts`                                                                                | DELETE           | Remove export                                                                                                             |
| 12  | `lib/architecture-v2/legacy-mapping.ts`                                                          | `legacyFamilyToV2` helper                                                                                     | DELETE           | No longer needed — `strategy-catalog-data.ts` emits v2 families directly                                                  |
| 13  | `lib/execution-mode-context.tsx`                                                                 | `ExecutionMode, EXECUTION_MODES`                                                                              | LEAN             | Inline (local definition — execution mode is UI-runtime, not system-design)                                               |
| 14  | `lib/mocks/fixtures/trading-data.ts`                                                             | `STRATEGIES as REGISTRY_STRATEGIES, type Strategy as RegistryStrategy`                                        | LEAN             | `strategy-instances.ts`                                                                                                   |
| 15  | `lib/stores/scope-helpers.ts`                                                                    | `STRATEGIES`                                                                                                  | LEAN             | `strategy-instances.ts`                                                                                                   |
| 16  | `lib/taxonomy.ts`                                                                                | (no import) — is IMPORTED BY strategy-registry.ts for types                                                   | NONE             | Keep as-is; taxonomy is independent of strategy-registry                                                                  |
| 17  | `tests/unit/lib/stores/scope-helpers.test.ts`                                                    | `STRATEGIES`                                                                                                  | LEAN             | `strategy-instances.ts`                                                                                                   |
| 18  | `tests/unit/lib/strategy-registry.test.ts`                                                       | self-test of deleted file                                                                                     | DELETE           | Replaced by coverage of the new `strategy-instances.ts` helpers if needed                                                 |

## Non-consumer surface changes

- `lib/mocks/fixtures/strategy-catalog-data.ts` — regenerated from UAC STRATEGY_REGISTRY, 99 entries (53 → 99).
  Categories re-bucketed (DEFI / CEFI / TRADFI / SPORTS / PREDICTION unchanged). Family strings now return v2 enum names
  directly (`ML_DIRECTIONAL`, `CARRY_AND_YIELD`, etc.). 3 Elysium legacy entries dropped. NFL/MLB value-bet + TLT/IEF
  stat-arb + 4 other Wave-6 slots included.

- `lib/mocks/fixtures/mock-data-seed.ts` — purge 3 ELYSIUM\_\* seed rows (+ their position / order siblings = 3
  positions, 4 orders).

- `components/widgets/positions/positions-data-context.tsx` — purge 5 DeFi mock position records (2 Elysium basis, 2
  recursive-staked, 1 lending).

- `lib/registry/ui-reference-data.json` — re-emit from UAC (downstream of the UAC `generate_ui_reference_data.py`
  pipeline). Drops SPORTS*VALUE family entries, 3 ELYSIUM*\* strategies, TRADFI_BOND_MEAN_REV_HUF_1D slot,
  SPORTS_VALUE_BET risk-budget-scope reference. patrick-elysium client kept (it is Organisation-Client lineage and not
  tied to strategy-registry; but will be dropped in a follow-up when client seed regenerates).

## Delete list (Phase 5)

- `lib/strategy-registry.ts` (7780 LOC)
- `lib/architecture-v2/legacy-mapping.ts` (61 LOC)
- `tests/unit/lib/strategy-registry.test.ts` (145 LOC)
- `lib/architecture-v2/index.ts` — remove `export * from "./legacy-mapping";`

Total surface shrink: **7986 LOC deleted + legacy-family-migration helper gone + fixture consolidated to the v2
slot-label axis**.

## Ring-2 / transitive audit

- `MODEL_STRATEGY_MAP` in `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-constants.ts`
  keyed on v1 `strategyIdPattern` — regenerate to slot labels (or keep as-is since slot labels ARE the new pattern
  post-Phase 2; `strategy.strategyIdPattern === strategy.id` in the new shape).
- `components/widgets/strategies/strategies-kpi-strip.md` and `components/widgets/strategies/strategies-widgets.md` —
  docs only; update path references to `strategy-instances.ts`.
- `docs/widget-certification/order-entry.json` + `book-hierarchy-bar.json` — doc / widget certification fixtures; path
  references to `lib/strategy-registry` → `lib/mocks/fixtures/strategy-instances`.
