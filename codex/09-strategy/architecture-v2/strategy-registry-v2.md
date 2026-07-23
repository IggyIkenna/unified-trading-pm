---
doc_type: codex-ssot
title: Strategy Registry (v2)
summary:
  Post-v1-delete SSOT for the v2 StrategyRegistry that resolves strategy_id→(name, family, category, archetype), derived
  from the archetype capability manifest; documents the to_dict() shape change, the Category vs VenueCategoryV2 seam,
  and slot-label-grammar fallback resolution. Concrete counts are the 2026-04-21 baseline (UAC enums are canonical).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    e2e-testing,
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [strategy, registry, uac, refactor, canonicalisation]
related:
  [
    /codex/09-strategy/architecture-v2/naming-convention.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
  ]
created: 2026-04-21
authoritative_for: [v2 strategy registry derivation (strategy_id resolution)]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/MIGRATION.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
    /codex/09-strategy/architecture-v2/naming-convention.md,
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/09-strategy/architecture-v2/tradfi-bond-instrument-type-decision.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Registry (v2)

> **PARTIALLY SUPERSEDED 2026-04-25 by Phase 9 — counts below are the 2026-04-21 baseline; UAC enums are canonical.**
> Concrete numbers in this doc (`18 archetypes`, `96 entries`, `8 families`) reflect the 2026-04-21 registry snapshot.
> Per the `enum-wins` governance rule (`strategy-summary.md:27`), the canonical counts are: 9 families / 57 archetypes /
> 14 InstructionActionV2 actions (per UAC `StrategyFamily` / `StrategyArchetype` / `InstructionActionV2`). The flatten
> arithmetic still holds at the cell-level (each cell's `representative_slot_labels` flatten to N entries) — the total
> entry count grew with the Phase 9 + recursive-staked-split additions but the mechanism is unchanged. Refresh trigger:
> `codex_audit_strategy_2026_05_12.md` ST-1/ST-2 audit.

> **SSOT:** `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py` backed by
> `unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`.

This document records the post-v1-delete shape of the strategy registry — the **one** place in Python that resolves
`strategy_id → (name, family, category, archetype)` for downstream consumers. v1 `StrategyFamily` (17 values), v1
`StrategyArchetype` (13 values), the 55-entry `_DEFAULT_STRATEGIES` catalogue and the `StrategyDefinition` dataclass in
its old shape were deleted on 2026-04-21 per `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` todo
`p1-kill-v1-strategyfamily-uac`. The v2 replacement is described here.

## Where the data comes from

The v2 registry is **derived** (not hand-maintained) from the v2 archetype capability matrix:

```
archetype_capability_manifest.json
  → archetypes: [{ archetype_id, family, cells: [{ category, instrument_type,
                                                    status, venue_ids,
                                                    representative_slot_labels, ... }, ...] }, ...]
```

Each `cell.representative_slot_labels[i]` becomes one `StrategyDefinition` row in the registry. Slot labels follow the
canonical grammar `ARCHETYPE@venue-asset-instrument-period-quote-env` (e.g.
`ML_DIRECTIONAL_CONTINUOUS@binance-btc-usdt-5m-usdt-prod`). `status == BLOCKED` cells are excluded — they have no
representative strategies by definition.

At module import time (`UAC StrategyRegistry.__init__`) the registry flattens 18 archetypes × their cells'
representative slot labels into 96 entries (count as of 2026-04-21).

## Public API (preserved v1 signatures)

Consumers migrate from v1 to v2 **without touching call sites**. The only churn is the strategy IDs themselves — v1 flat
IDs like `DEFI_ETH_BASIS_HUF_1H` are gone; v2 uses the slot-label grammar.

```python
from unified_api_contracts.strategy import STRATEGY_REGISTRY

# Resolution helpers (unchanged signatures)
STRATEGY_REGISTRY.resolve_name("ML_DIRECTIONAL_CONTINUOUS@binance-btc-usdt-5m-usdt-prod")
#   → "Ml Directional Continuous — binance-btc-usdt-5m-usdt-prod"
STRATEGY_REGISTRY.resolve_family("ML_DIRECTIONAL_CONTINUOUS@synthetic-slot-not-registered")
#   → "ML_DIRECTIONAL"   (falls back to ARCHETYPE@... prefix parse)
STRATEGY_REGISTRY.resolve_category("CARRY_BASIS_PERP@binance-btc-usdt-prod")
#   → "CEFI"

# to_dict() — shape CHANGED (see § Shape Change)
STRATEGY_REGISTRY.to_dict()
#   → {"strategies": [...], "families": {...}, "categories": [...],
#       "archetypes": [...], "coverage_statuses": [...]}
```

## Shape Change: `to_dict()`

v1 → v2 field drift in `strategies[i]`:

| Field               | v1                                         | v2 (2026-04-21)                                                                     |
| ------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------- |
| `strategy_id`       | Flat ID (e.g. `DEFI_ETH_BASIS_HUF_1H`)     | Slot label (`ARCHETYPE@...`)                                                        |
| `name`              | Hand-authored display name                 | Humanised slot label                                                                |
| `family`            | v1 StrategyFamily value (17 possibilities) | v2 StrategyFamily value (8 possibilities)                                           |
| `category`          | Category enum value                        | Same (CEFI/DEFI/TRADFI/SPORTS/PREDICTION)                                           |
| `archetype`         | v1 StrategyArchetype value (13)            | v2 StrategyArchetype value (18)                                                     |
| `execution_mode`    | `HUF` / `SCE` / `EVT`                      | **Removed** — was v1-only, mode selection is now archetype-derived via `HoldPolicy` |
| `strategy_type`     | Human-readable type label                  | **Removed** — redundant with archetype                                              |
| `default_timeframe` | `"1H"` / `"4H"` / …                        | **Removed** — now encoded in the slot label body                                    |
| `version`           | Config version int                         | **Removed** — per-slot config version lives in `strategy_service.ConfigRegistry`    |
| `description`       | Free-form                                  | **Removed** — codex is the description surface                                      |
| `client_id`         | Default client association                 | **Removed** — client binding is now `StrategyAvailabilityEntry.exclusive_client_id` |
| `coverage_status`   | (not present)                              | **New** — `SUPPORTED` / `PARTIAL`                                                   |

All v1-only fields above are gone **without a deprecation shim** (Citadel rule 3 — clean break). Consumers that relied
on v1-only fields have been updated in lockstep (see § Consumers).

## Category vs VenueCategoryV2

The registry exposes **two** category types for now:

- `Category` (in `unified_api_contracts.strategy`) — the engine-side enum used by strategy-service mode validation
  (`validate_mode_for_category`). Same upper-case values as `VenueCategoryV2`, kept to avoid breaking existing engine
  code.
- `VenueCategoryV2` (in `unified_api_contracts.internal.architecture_v2.enums`) — the canonical v2 axis enum used by
  `ArchetypeCapability`, derivation formulas, pricing, and everything downstream.

New code should import `VenueCategoryV2`. The `_category_from_v2()` helper in `registry.py` converts between them at the
one seam — keep it auditable.

## Consumers

All migrated in the same wave (UAC `e6f7c6d` + `92104ab` + downstream commits on 2026-04-21):

| Repo                             | File                                                    | Change                                                                    |
| -------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------- |
| unified-api-contracts            | `internal/domain/strategy_service/registry.py`          | Rewrite — v2 from ARCHETYPE_CAPABILITY                                    |
| unified-api-contracts            | `internal/architecture_v2/enums.py` + `__init__.py` + … | Drop V2 suffix on family/archetype enums                                  |
| unified-api-contracts            | `openapi/ui-reference-data.json`                        | Regenerated — now 96 slot-labelled entries                                |
| unified-trading-library          | `utils/record_enricher.py`                              | Zero source change (API preserved)                                        |
| unified-trading-library          | `tests/unit/test_utils_record_enricher.py`              | Fixtures migrated to slot-label IDs                                       |
| unified-trading-api              | `routes/trading_analytics.py`                           | Zero change — `to_dict()` field overlap covers it                         |
| unified-trading-pm               | `scripts/openapi/generate_ui_reference_data.py`         | Zero source change (counter-agnostic)                                     |
| strategy-service                 | 54 files across `engine/strategies/v2/` + tests         | Drop V2 suffix — bulk rename                                              |
| risk-and-exposure-service        | `v2/orchestrator.py` + `v2/preflight.py` + tests        | Drop V2 suffix                                                            |
| execution-service                | `tests/unit/v2/` + `tests/unit/backtest_v2/`            | Drop V2 suffix                                                            |
| position-balance-monitor-service | `tests/unit/v2/`                                        | Drop V2 suffix                                                            |
| e2e-testing                      | `tests/integration/test_architecture_v2_roundtrip.py`   | Drop V2 suffix                                                            |
| unified-trading-system-ui        | `lib/architecture-v2/enums.ts` + `coverage.ts`          | Drop V2 suffix on `StrategyFamilyV2` / `StrategyArchetypeV2` type aliases |

## ClientRegistry

Separate from the strategy registry, `CLIENT_REGISTRY` (in
`unified_api_contracts.internal.domain.strategy_service.client_registry`) is **unchanged** — the client identity axis is
orthogonal to v1/v2 strategy taxonomy. 3 default entries: `patrick-elysium` / `acme-fund` / `internal-prop`. Extending
the client list is a follow-up wave tracked separately (plan file TBD — not blocking this refactor).

## Fallback behaviour

`resolve_family(strategy_id)` supports a **slot-label grammar fallback**: if the full `strategy_id` isn't registered but
parses as `ARCHETYPE@...` with a known `StrategyArchetype`, the family is resolved via `ARCHETYPE_CAPABILITY_REGISTRY`.
This keeps legacy records (created before they were registered) routable.

`resolve_category(strategy_id)` has **no** prefix fallback (v1 had `"CEFI_UNKNOWN" → "CEFI"`; v2 removed this because
the slot-label grammar doesn't carry category in the ARCHETYPE token).

## Who owns this

Registry ownership follows the `unified-api-contracts` Citadel convention:

- **Schema / code SSOT**: `unified-api-contracts` (this document lives here as its codex dossier).
- **Data SSOT**:
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`. Humans edit
  that JSON via the flow documented in `/codex/09-strategy/architecture-v2/category-instrument-coverage.md`; the UI
  mirror `coverage.ts` is auto-generated from it.
- **Test parity**: `unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py` — any drift
  between the manifest and the in-memory registry fails loud.

## Follow-ups

- UI type alias `StrategyFamilyV2` (in `lib/architecture-v2/enums.ts`) renamed to `StrategyFamily` in the same wave.
  Consumers across `components/architecture-v2/` migrated in lockstep. If any UI surface imports the old name it will
  fail at `tsc` time.
- `ClientRegistry` v2 expansion (more than 3 seed entries; Firebase-backed admin surface) is tracked separately.
- The `Category` engine-side enum is a temporary retention — once strategy-service engine code drops its uses and
  migrates to `VenueCategoryV2` directly, `Category` can be deleted. Tracked under architecture-v2 Stage 3E follow-ups.
