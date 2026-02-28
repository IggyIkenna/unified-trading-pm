# execution-services Refactoring Plan

**Plan ID**: 0c597f7f
**Created**: 2026-02-24
**Status**: In Progress
**Related**: execution_services_structural_refactoring_brainstorm.md

---

## Current Status

**Last Updated**: 2026-02-24

### Phase -1: Deep Discovery ✅ COMPLETED
- ✅ Order state management discovery (agent-1c0f5e0c)
- ✅ Algorithm execution discovery (agent-1c0f5e0c)
- ✅ Exchange/protocol interactions discovery (agent-1c0f5e0c)

### Phase 0.5: Add Regression Tests ✅ COMPLETED
- ✅ Order state tests (58 tests, agent-d0e6f4e7)
- ✅ Algorithm tests (45 tests, agent-d0e6f4e7)
- ✅ Exchange/protocol tests (82 tests, agent-d0e6f4e7)
- ✅ Uniswap V4 tests (16 tests, agent-d0e6f4e7)
- ✅ Battle-testing regressions (6 tests, agent-d0e6f4e7)
- ✅ Performance regressions (5 tests, agent-d0e6f4e7)
- **Total**: 212 new regression tests added

### Phase 0: Alignment Fixes ✅ COMPLETED
- ✅ CI/CD alignment (basedpyright, pytest -n auto, path deps)
- ✅ Uniswap V4 full implementation (hooks, custom curves)
- ✅ Lazy imports removed (codex compliance)
- ✅ Batch operations added (GCS performance)

### Phase 1: Library Extraction/Enhancement ✅ COMPLETED
- ✅ matching-engine-library created (130 tests, 80% coverage)
- ✅ unified-defi-execution-interface created (46 tests, 85% coverage)
- ✅ execution-algo-library enhanced (67 tests, 78% coverage)
- ✅ unified-trade-execution-interface enhanced (71% coverage)

### Phase 1.5: Hardening ✅ COMPLETED
- ✅ unified-trade-execution-interface hardened (71% coverage, basedpyright, 300s timeout)
- ✅ matching-engine-library hardened (basedpyright, 300s timeout, no Any)
- ✅ unified-defi-execution-interface hardened (basedpyright, 300s timeout, TypedDict)
- ✅ execution-algo-library hardened (basedpyright, 300s timeout, TypedDict)

### Phase 1.6: Structural Analysis 🔄 IN PROGRESS
- ✅ Structural analysis completed (agent-xxx)
- 🔄 Brainstorming refactoring strategy (see: execution_services_structural_refactoring_brainstorm.md)
- **Key Findings**:
  - 5 god classes (> 1500 lines, BLOCKING quality gates!)
  - Hard dependencies (direct GCS, no adapters)
  - DRY violations (4 duplicate patterns)
  - Missing abstractions (StorageAdapter, RiskServiceClient, mock factories)
  - 150+ functions returning None (hard to test)
- **Proposed Solution**: Adopt instruments-service structure (adapters/, engine/, utils/, config/, cli/)

---

## Structural Refactoring Roadmap

### Phase 2.0: Quick Wins (Unblock Tests) - 1 Week
**Goal**: Get tests running, reach 30-35% coverage

1. ✅ Fix orchestration import (lazy import or factory)
2. 🔄 Create StorageAdapter (like instruments-service)
3. 🔄 Create RiskServiceClient adapter
4. 🔄 Add mock factories to conftest
5. 🔄 Centralize instrument conversion (single source)

**Estimated Impact**: +5-10% coverage (25% → 30-35%)

### Phase 2.1: Break Up God Classes - 1-2 Weeks
**Goal**: Files < 1500 lines, reach 40-45% coverage

1. 🔄 BacktestEngine: Extract validator, signal loader, data loader
2. 🔄 GridConfigGenerator: Extract uploader, delegate to storage adapter
3. 🔄 PreflightChecker: Split into smaller validators
4. 🔄 ResultSerializer: Extract timeline builder, delegate to storage adapter
5. 🔄 DataConfigBuilder: Extract cache manager, delegate to storage adapter

**Estimated Impact**: +10-15% coverage (35% → 45-50%)

### Phase 2.2: DRY Refactoring - 1 Week
**Goal**: Single source of truth, reach 50%+ coverage

1. 🔄 Centralize conversions (utils/transformations.py)
2. 🔄 Single GCS upload (via StorageAdapter)
3. 🔄 Remove duplicated validation
4. 🔄 Extract common patterns

**Estimated Impact**: +5% coverage (45% → 50%)

### Phase 2.3: Add NautilusTrader Mocks - 1 Week
**Goal**: Remove external dependency in tests

1. 🔄 Create api-contracts/nautilus/ (use context7 + GitHub)
2. 🔄 Mock Order, Position, Instrument, Cache, Clock
3. 🔄 Replace NautilusTrader imports in tests

**Estimated Impact**: +5% coverage (50% → 55%)

---

## Open Questions (Awaiting User Input)

### Q1: Structure Agreement
**Do you agree with the proposed structure?**
- adapters/ (StorageAdapter, RiskServiceClient, OrderAdapter, etc.)
- engine/ (orchestration/, backtest/, routing/, processors/)
- utils/ (transformations.py, validation.py, instrument_conversion.py)
- config/ (service_config.py, grid_generator.py)
- cli/ (handlers/, main.py)

### Q2: NautilusTrader Mocking
**Should we create api-contracts/nautilus/ for mocking?**
- Use context7 + https://github.com/nautechsystems/nautilus_trader
- Reverse engineer Order, Position, Instrument, Cache, Clock types
- Create Pydantic schemas and mock implementations

### Q3: Phase Priority
**Should we start with Phase 2.0 quick wins?**
- StorageAdapter creation
- RiskServiceClient creation
- Mock factories in conftest
- Centralized instrument conversion

### Q4: God Class Breakup
**Any specific concerns about breaking up god classes?**
- BacktestEngine (2,681 lines → < 800 lines)
- GridConfigGenerator (2,277 lines → < 1500 lines)
- PreflightChecker (2,108 lines → < 1500 lines)
- ResultSerializer (2,017 lines → < 1500 lines)
- DataConfigBuilder (1,873 lines → < 1500 lines)

### Q5: Function Return Types
**Should functions return Result objects or keep returning None?**
- Option A: Return Result objects everywhere (explicit success/failure)
- Option B: Return status codes/enums (simple)
- Option C: Mix (return values for queries, None for commands)

---

## Next Steps (Awaiting User Approval)

1. **Review brainstorming doc**: execution_services_structural_refactoring_brainstorm.md
2. **Discuss open questions** (Q1-Q5 above)
3. **Agree on approach** (Phase 2.0 quick wins vs full restructure)
4. **Launch implementation** (fast sub-agents for heavy work)

---

## Related Documents

- **Brainstorming**: `.cursor/plans/execution_services_structural_refactoring_brainstorm.md`
- **Structural Analysis**: Previous agent report (agent-xxx)
- **Reference Structure**: `instruments-service/` (clean example)
- **API Contracts**: `api-contracts/` (for NautilusTrader mocking)
- **Codex**: `unified-trading-codex/06-coding-standards/`
