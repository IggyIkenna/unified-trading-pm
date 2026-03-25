---
title: "UTL Import Consolidation — Services Import from UTL, Not Split Libraries"
created: 2026-03-25
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-25
priority: P0
---

# UTL Import Consolidation

## Context

Services are importing directly from split libraries (unified-config-interface, unified-cloud-interface,
unified-events-interface, etc.) instead of through unified-trading-library (UTL) which re-exports everything.
This created 100+ transitive dep declarations that were added to pyproject.toml files, undoing the original
refactor that consolidated imports through UTL.

## Architectural Rule

Services MUST import from these sources ONLY:
- `unified_trading_library` — the primary facade (re-exports config, cloud, events, domain, etc.)
- `unified_api_contracts` — external data normalization types (T0)
- `unified_internal_contracts` — internal domain types (T0)
- Domain-specific interfaces ONLY when the service implements the interface (not just consumes)

**EXCEPTION:** `deployment-service` has a documented bootstrap exception — it directly uses cloud/config for
infrastructure orchestration. Whitelisted in alignment scripts.

## What's Wrong Now

18 services have direct imports like:
```python
from unified_config_interface import UnifiedCloudConfig  # WRONG
from unified_cloud_interface import get_storage_client    # WRONG
from unified_events_interface import log_event            # WRONG
```

Should be:
```python
from unified_trading_library import UnifiedCloudConfig    # CORRECT (re-exported by UTL)
from unified_trading_library import get_storage_client    # CORRECT
from unified_trading_library import log_event             # CORRECT
```

## Execution Phases

### Phase 0 — Whitelist deployment-service (unblock alignment)
- [x] [AGENT] P0. Add deployment-service to tier exception list in alignment script
- [x] [AGENT] P0. Verify alignment passes with only deployment-service as exception

### Phase 1 — Audit UTL re-exports (what's missing?)
- [ ] [AGENT] P0. Scan all 18 services for direct split-library imports
- [ ] [AGENT] P0. Cross-reference with UTL __init__.py — find symbols imported from split libraries that UTL doesn't re-export
- [ ] [AGENT] P0. Add missing re-exports to UTL __init__.py

### Phase 2 — Change service imports (PARALLEL across all 18)
- [ ] [AGENT] P0. For each service: `from unified_config_interface import X` → `from unified_trading_library import X`
- [ ] [AGENT] P0. Same for unified_cloud_interface, unified_events_interface, unified_domain_client
- [ ] [AGENT] P0. Same for unified_features_interface, unified_feature_calculator_library, etc.
- [ ] [AGENT] P0. Run import smoke test after each service change

### Phase 3 — Remove transitive deps from pyproject.toml
- [ ] [AGENT] P0. Remove unified-config-interface, unified-cloud-interface, unified-events-interface, etc. from each service's [project.dependencies]
- [ ] [AGENT] P0. Remove corresponding [tool.uv.sources] entries
- [ ] [AGENT] P0. Keep ONLY: unified-trading-library + unified-api-contracts + unified-internal-contracts + domain-specific (where justified)

### Phase 4 — Update validate-import-deps.py
- [ ] [AGENT] P0. Change script to FLAG direct split-library imports as violations (not add them as deps)
- [ ] [AGENT] P0. Whitelist: deployment-service
- [ ] [AGENT] P0. Allowed direct deps: unified-trading-library, unified-api-contracts, unified-internal-contracts
- [ ] [AGENT] P0. Domain-specific exceptions per service (e.g. execution-service → unified-trade-execution-interface)

### Phase 5 — Strip transitive deps from manifest
- [ ] [AGENT] P0. Re-run manifest stripping (same as we did earlier)
- [ ] [AGENT] P0. Verify alignment passes clean

## Success Criteria

- All services import from UTL (except deployment-service)
- pyproject.toml has only UTL + UAC + UIC as internal deps (plus justified domain-specific)
- validate-import-deps.py flags direct split-library imports as violations
- Version alignment passes clean with 0 misalignments
- All services pass setup smoke test
