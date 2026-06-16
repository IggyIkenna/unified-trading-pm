---
scope: [engineer, admin]
---

# Archived pre-v2 strategy docs

Everything in this directory was the pre-v2 (category-organised) strategy documentation. It has been superseded by
[`../architecture-v2/`](../architecture-v2/README.md), which organises by **family → archetype → instance → config**
rather than by venue category.

## Why this exists

Git history preserves everything, but an archive directory with pointers is kinder to readers who stumble into old
links. Every doc below maps 1:1 to a v2 placement via
[`../architecture-v2/MIGRATION.md`](../architecture-v2/MIGRATION.md) — that's the authoritative source for "where did my
doc go?"

## What's here

### Category docs — superseded by archetypes

| Archived path    | v2 replacement                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------- |
| `cefi/*.md`      | `../architecture-v2/archetypes/{ml,rules,market}-*-continuous.md`                              |
| `defi/*.md`      | `../architecture-v2/archetypes/{carry,yield,arbitrage,liquidation,market-making}-*.md`         |
| `sports/*.md`    | `../architecture-v2/archetypes/{ml,rules,market-making}-directional-event-settled.md` +        |
|                  | `arbitrage-price-dispersion.md`                                                                |
| `tradfi/*.md`    | `../architecture-v2/archetypes/{ml,rules}-directional-continuous.md`, `vol-trading-options.md` |
| `templates/*.md` | Folded into each archetype doc's standard sections                                             |

### Cross-cutting docs absorbed into v2 axes / cross-cutting

| Archived path                                    | v2 replacement                                                                                                      |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `cross-cutting/config-architecture.md`           | `../../06-coding-standards/strategy-identity-versioning.md` + `../../04-architecture/artifact-versioning.md`        |
| `cross-cutting/cost-modeling.md`                 | `../../04-architecture/execution-policy.md` + `../architecture-v2/cross-cutting/benchmark-fills.md`                 |
| `cross-cutting/latency-profiles.md`              | `../../04-architecture/execution-policy.md` + `../../02-venues/venue-registry-reference.md`                         |
| `cross-cutting/margin-health.md`                 | `../architecture-v2/cross-cutting/venue-account-coordination.md` + `../architecture-v2/cross-cutting/risk-gates.md` |
| `cross-cutting/ml-pipeline.md`                   | `../../04-architecture/backtest-groups.md` (Group A)                                                                |
| `cross-cutting/share-classes.md`                 | `../architecture-v2/axes/share-class.md`                                                                            |
| `cross-cutting/venue-collateral-and-wrapping.md` | `../../02-venues/venue-capability-registry.md` (structured data in UAC)                                             |

**Cross-cutting docs that were NOT archived** (still authoritative, not absorbed): see [`../README.md`](../README.md) §
"What's still in this directory".

### Top-level docs

| Archived path                                | v2 replacement                                                                                                                                                                   |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `strategy-registry.md`                       | UAC `StrategyInstanceDefinition` + `StrategyInstanceIdentity` (machine-readable registry)                                                                                        |
| `STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md` | [`../architecture-v2/MIGRATION.md`](../architecture-v2/MIGRATION.md)                                                                                                             |
| `execution-modes.md`                         | `../../04-architecture/backtest-groups.md` + `../architecture-v2/cross-cutting/benchmark-fills.md`                                                                               |
| `STRATEGY_CATALOG_pre_v2.md`                 | [`../README.md`](../README.md) (v2 index) + [`../architecture-v2/README.md`](../architecture-v2/README.md) — pre-v2 65+-strategy catalogue (preserved from main@03a37b6a1 audit) |

## Rules for this directory

- **Read-only.** Do not edit archived docs — changes won't flow to the v2 surface.
- **Use v2 first.** If you need to document something new, write it in `../architecture-v2/` and reference it from any
  v2 archetype or axis doc that needs it.
- **If you find a case not covered by v2**, flag it — that's a bug in the migration audit, not a reason to edit an
  archived doc. Update [`../architecture-v2/MIGRATION.md`](../architecture-v2/MIGRATION.md) § 14 (TBDs).
