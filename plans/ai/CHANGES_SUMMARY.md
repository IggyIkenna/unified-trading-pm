# Service Standardization - Complete Changes Summary

## Repos Requiring Changes (17 total)

### Python Services (14) - FULL Refactoring
**CLI + Engine/Adapters + Quality Gates**

Each service gets:
- ✅ `--operation` and `--mode` flags (separated)
- ✅ `engine/` directory (mode-agnostic business logic)
- ✅ `adapters/` directory (thin wrappers <100 lines)
- ✅ Quality gates passing (including pre-existing issues)

1. instruments-service (pilot)
2. market-tick-data-handler
3. market-data-processing-service
4. pnl-attribution-service
5. features-calendar-service
6. features-delta-one-service
7. features-volatility-service
8. features-onchain-service
9. ml-training-service
10. ml-inference-service
11. strategy-service
12. execution-services
13. risk-and-exposure-service
14. position-balance-monitor-service

### Platform Libraries (1) - Code Changes

15. **unified-events-interface**
    - Add `observability/error_tracker.py` (ErrorWarningCounter)
    - Add `observability/memory_tracker.py` (DataFrame memory helpers)
    - ~200 lines of new code

### Deployment (1) - Configuration Updates

16. **unified-trading-deployment-v3**
    - Update `shard_builder.py` (add operation support)
    - Update 14 sharding YAML configs
    - Update 20+ Terraform files
    - Update UI preview component
    - Update tests
    - **~40 files affected**

### Documentation (1) - Standards Updates

17. **unified-trading-codex**
    - Add `cli-standards.md`
    - Update `batch-live-symmetry.md`
    - Update `coding-standards/README.md`
    - Add service structure refactoring guide
    - **~5 files affected**

---

## Repos NOT Requiring Changes (19 total)

### UI Repos (9) - Out of Scope
TypeScript/React, different quality gates (tsc, ESLint), no CLI

- backtest-ui
- batch-audit-ui
- client-reporting-ui
- live-health-monitor-ui
- logs-dashboard-ui
- ml-deployment-ui
- onboarding-ui
- settlement-ui
- trading-analytics-ui

### Platform Libraries (5) - No Changes Needed
Already library format, no CLI, no observability changes

- unified-cloud-services
- unified-config-interface
- unified-market-interface
- unified-trade-execution-interface
- unified-domain-services

### Deployment (1) - Documentation Only
- unified-trading-deployment-v3 (examples only)

### Utility (2) - No Changes
- execution-algo-library
- alerting-system

### Special Cases (2) - Ignored
- sports-betting-services
- one-time-scripts

---

## Summary by Change Type

| Change Type | Repos | Files Affected | Effort |
|-------------|-------|----------------|--------|
| **Full refactoring** (CLI + structure) | 14 services | ~500+ files | 7-9 days |
| **Code changes** (new features) | 1 library (UEI) | ~5 files | 1 day |
| **Config updates** (no code) | 1 deployment (v3) | ~40 files | 1 day |
| **Documentation** | 1 codex | ~5 files | 1 day |
| **No changes** | 19 repos | 0 files | 0 days |
| **Total** | **36 repos** | **~550 files** | **10-12 days** |

---

## Key Decisions

1. ✅ **Scripts/docs ignored** - No changes to one-time-scripts, presentations, temp folders
2. ✅ **Deployment v3 needs updates** - ~40 config/infrastructure files for CLI standardization
3. ✅ **Platform libraries mostly unchanged** - Only UEI gets new observability code
4. ✅ **UI repos out of scope** - Different tech stack, different quality gates
5. ✅ **Quality gates are blocking** - Must pass for each service before proceeding
