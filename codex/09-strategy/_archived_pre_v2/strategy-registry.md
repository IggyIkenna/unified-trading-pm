---
scope: [engineer, admin]
---

# Strategy Registry — SSOT in UAC

## Location

`unified_api_contracts/internal/domain/strategy_service/registry.py`

Facade: `from unified_api_contracts.strategy import STRATEGY_REGISTRY`

## What It Contains

- 57 strategy definitions with: id, name, family, category, archetype, execution_mode
- Strategy families (18): BASIS_TRADE, MOMENTUM, MARKET_MAKING, LENDING, etc.
- Archetypes (13): directional, delta-neutral, yield, quoting, etc.
- Mode validation rules per category

## How It Syncs to UI

```
UAC (Python) -> generate_ui_reference_data.py -> ui-reference-data.json -> generated.ts -> UI
```

1. UAC defines `StrategyRegistry` with all strategies
2. PM script `generate_ui_reference_data.py` calls `STRATEGY_REGISTRY.to_dict()`
3. Output goes to UI's `lib/registry/ui-reference-data.json`
4. UI's `lib/registry/generated.ts` re-exports typed constants
5. UI components import from `@/lib/registry/generated`

The UI's `strategy-registry.ts` was previously hand-written. It should now be a thin wrapper over the generated data.

## Adding a New Strategy

1. Add `StrategyDefinition` to `_DEFAULT_STRATEGIES` in registry.py
2. Run `bash unified-trading-pm/scripts/openapi/generate-unified-openapi.sh`
3. UI picks up the new strategy automatically via `ui-reference-data.json`
