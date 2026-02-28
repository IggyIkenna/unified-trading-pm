# execution-service: MASTER REFACTORING PLAN

**Created**: 2026-02-24
**Status**: Ready for execution
**Context**: Full session consolidated - structural refactoring + library extraction + hardening

---

## 🎯 KEY CLARIFICATIONS (User Feedback)

### 1. **Terminology: Instructions (NOT Signals)**
- ✅ **Instruction**: Generic term for all action types (trade, swap, lend, stake, etc.)
- ❌ **Signal**: Old ML-specific term, implies machine learning signal
- **Source**: strategy-service produces instructions
- **Mock**: execution-service has local mock for testing in isolation (writes to same bucket as prod for now)
- **Action**: Rename `signal` → `instruction` everywhere in codebase

### 2. **Results: Separate Library (Batch AND Live)**
- **Scope**: Messaging + persistence layer for execution data output
- **Modes**: Works for BOTH batch and live (not backtest-heavy!)
- **Batch**: Enriched with extra details, process one day at a time
- **Live**: Continuous, same core analytics
- **Decision**: Extract to separate library (NOT separate service - avoid latency)
- **Purpose**: Unified results handling for both modes

### 3. **Node Builder: NautilusTrader Configuration**
- **Purpose**: Builds `BacktestNode` configuration for NautilusTrader engine
- **Components**: `BacktestEngineConfig`, `BacktestRunConfig`, `BacktestVenueConfig`
- **NOT**: Frontend/backend distinction
- **IS**: Configuration builder for NautilusTrader backtest infrastructure
- **Location**: `execution_service/backtest/node_builder.py`

### 4. **Risk Checker: Package Dependency (NOT HTTP)**
- **Problem**: HTTP calls are too slow
- **Solution**: Import risk-and-exposure-service as package dependency
- **Mode**: Light operational mode - run calculations locally
- **Benefits**: Fast, no HTTP overhead, reuses risk service logic

---

## 📋 COMPLETE TODO LIST (Consolidated from Entire Session)

### ✅ COMPLETED (8 items)

1. ✅ **Deep Discovery** (Phase -1): Order state, algorithms, exchange interactions
2. ✅ **Regression Tests** (Phase 0.5): 212 tests added (order state, algorithms, exchange, V4, battle-testing, performance)
3. ✅ **Alignment Fixes** (Phase 0): CI/CD (basedpyright, pytest -n auto), Uniswap V4 full implementation, lazy imports removed, batch operations added
4. ✅ **Library Extraction** (Phase 1): matching-engine-library (80%), unified-defi-execution-interface (85%), execution-algo-library (78%), unified-trade-execution-interface (71%)
5. ✅ **Hardening** (Phase 1.5): All 4 libraries hardened (basedpyright, 300s timeout, no Any, TypedDict)
6. ✅ **Structural Analysis**: God classes identified, DRY violations found, hard dependencies mapped
7. ✅ **Brainstorming**: Complete refactoring strategy documented
8. ✅ **Terminology Clarification**: Instructions vs signals, results library scope, node builder purpose

### 🔄 IN PROGRESS (1 item)

9. 🔄 **Master Plan Consolidation**: This document!

### ⏳ PENDING - STRUCTURAL REFACTORING (13 items)

#### Phase 1: Quick Wins (1 week → 30-35% coverage)

10. ⏳ **Create StorageAdapter** (like instruments-service)
    - Thin wrapper (~150 lines)
    - Delegates to `StandardizedDomainCloudService`
    - Replaces direct GCS usage in 10+ files

11. ⏳ **Create RiskChecker** (package dependency, NOT HTTP)
    - Import risk-and-exposure-service as package
    - Light operational mode (local calculations)
    - Use risk config for limits
    - Add to pyproject.toml path dependencies

12. ⏳ **Add Mock Factories** (conftest.py)
    - `mock_storage_adapter()`
    - `mock_risk_checker()`
    - `mock_order_adapter()`
    - `instruction_builder()` (test helper)

13. ⏳ **Centralize Instrument Conversion** (utils/instrument_conversion.py)
    - Single source for ID conversions
    - Remove 4 duplicate implementations
    - `to_gcs_format()`, `from_gcs_format()`, `to_nautilus_format()`

14. ⏳ **Fix Orchestration Import** (lazy import or factory)
    - Unblock test collection
    - Remove top-level `execution_algo_library` import

#### Phase 2: Break Up God Classes (1-2 weeks → 40-45% coverage)

15. ⏳ **BacktestEngine** (2,681 → 800 lines)
    - Extract: BacktestValidator (400 lines)
    - Extract: SignalLoader → **InstructionLoader** (600 lines)
    - Extract: DataLoader (500 lines)
    - Use existing: NodeBuilder, ResultExtractor

16. ⏳ **GridConfigGenerator** (2,277 → 1,200 lines)
    - Delegate to StorageAdapter (-400 lines)
    - Extract: ConfigValidator (300 lines)
    - Extract: GridBuilder (377 lines)

17. ⏳ **PreflightChecker** (2,108 → 800 lines)
    - Split into multiple validators (1,308 lines total)
    - Each validator < 400 lines

18. ⏳ **ResultSerializer** (2,017 → 800 lines)
    - Extract: TimelineBuilder (500 lines)
    - Delegate to StorageAdapter (-400 lines)
    - Extract: ResultFormatter (317 lines)

19. ⏳ **DataConfigBuilder** (1,873 → 800 lines)
    - Extract: CacheManager (400 lines)
    - Delegate to StorageAdapter (-300 lines)
    - Extract: ConfigBuilder (373 lines)

#### Phase 3: DRY Refactoring (1 week → 50% coverage)

20. ⏳ **Centralize Transformations** (utils/transformations.py)
    - Remove 4 duplicate implementations
    - Single source for all conversions

21. ⏳ **Single GCS Upload** (via StorageAdapter)
    - Remove 4 duplicate implementations
    - Delegate to StandardizedDomainCloudService

22. ⏳ **Remove Duplicated Validation**
    - Consolidate validation logic
    - Use shared validators

#### Phase 4: NautilusTrader Mocks (1 week → 55% coverage)

23. ⏳ **Create api-contracts/nautilus/**
    - Use context7 + https://github.com/nautechsystems/nautilus_trader
    - Mock: Order, Position, Instrument, Cache, Clock
    - Pydantic schemas + mock implementations

#### Phase 5: Results Library (Separate Library)

24. ⏳ **Decide Results Library Scope**
    - Messaging + persistence for batch AND live
    - NOT separate service (avoid latency)
    - Unified results handling

25. ⏳ **Extract Results Library**
    - Create `execution-results-library/`
    - Move: ResultSerializer, ResultExtractor, result models
    - Works for both batch and live modes

#### Phase 6: Terminology & Config (execution-service)

26. ⏳ **Rename Signal → Instruction**
    - Update all files, classes, functions, variables
    - `SignalLoader` → `InstructionLoader`
    - `signal_processor` → `instruction_processor`
    - Update tests, docs, comments

27. ⏳ **Refactor Config** (extend UnifiedCloudConfig)
    - Remove fallbacks
    - Use ConfigStore for runtime config
    - Keep grid config in domain bucket

28. ⏳ **Create Thin Adapters** (<100 lines each)
    - StorageAdapter (150 lines)
    - RiskChecker (100 lines)
    - OrderAdapter (80 lines)
    - AlgorithmFactory (70 lines)

29. ⏳ **Add Event Logging** (unified-events-interface)
    - All 11 lifecycle events
    - Progress tracking (dates, instruments)
    - Error/warning tracking

30. ⏳ **Update CLI Structure** (--operation, --mode)
    - `--operation execute` (or `backtest`, `live_execution`)
    - `--mode batch|live`
    - Dispatch by operation, execute by mode

#### Phase 7: Final Cleanup

31. ⏳ **Remove Duplicate Code** (switch to library imports)
    - Use matching-engine-library
    - Use unified-defi-execution-interface
    - Use execution-algo-library
    - Use unified-trade-execution-interface

32. ⏳ **Verify Quality Gates** (all 6 repos)
    - execution-service
    - matching-engine-library
    - unified-defi-execution-interface
    - execution-algo-library
    - unified-trade-execution-interface
    - execution-results-library (new)

33. ⏳ **Commit All Changes** (don't push)
    - Run quality gates on all repos
    - Commit to feature branches
    - Create PRs (don't merge yet)

---

## 📊 EXPECTED OUTCOMES

### Line Count Savings
- **Current**: 66,482 lines
- **After refactoring**: ~62,682 lines
- **Reduction**: 3,800 lines (5.7%)

### Structural Improvements (More Important!)
- ✅ 5 god classes → 20+ focused components (< 800 lines each)
- ✅ 4 duplicate patterns → 1 canonical implementation
- ✅ Hard dependencies → Injected adapters (testable!)
- ✅ 150+ functions returning None → Result objects
- ✅ 25% coverage → 55% coverage

### Quality Metrics
- **Coverage**: 25% → 55% (+30%)
- **Testability**: Low → High (dependency injection)
- **Maintainability**: Low → High (focused components)
- **DRY**: Violations → Single source of truth

---

## 🏗️ TARGET STRUCTURE

```
execution-service/
├── adapters/                    # Thin I/O adapters (<100 lines each)
│   ├── storage.py              # GCS via StandardizedDomainCloudService
│   ├── risk_checker.py         # Risk via package dependency (NOT HTTP)
│   ├── order_adapter.py        # Orders via unified-trade-execution-interface
│   └── algorithms.py           # Algorithms via execution-algo-library
│
├── engine/                      # Core business logic (testable!)
│   ├── orchestration/          # Orchestrators (<200 lines each)
│   │   ├── orchestrator.py
│   │   ├── order_tracker.py
│   │   └── order_submitter.py
│   │
│   ├── backtest/               # Backtest components
│   │   ├── engine.py           # < 800 lines (orchestrates only)
│   │   ├── validator.py        # Preflight validation
│   │   ├── instruction_loader.py  # Instruction loading (was SignalLoader)
│   │   ├── data_loader.py      # Data loading
│   │   └── node_builder.py     # NautilusTrader config
│   │
│   ├── routing/                # Instruction routing
│   │   ├── instruction_router.py
│   │   └── instruction_validator.py
│   │
│   ├── processors/             # Instruction processors
│   │   └── instruction_processor.py  # (was signal_processor)
│   │
│   ├── risk/                   # Risk checking
│   │   └── risk_checker.py     # Uses risk-and-exposure-service package
│   │
│   └── validation/             # Validation
│       └── dependency_checker.py
│
├── utils/                       # Shared utilities (pure functions)
│   ├── transformations.py      # All conversion helpers
│   ├── instrument_conversion.py # Single source for ID conversion
│   └── validation.py           # Common validators
│
├── config/                      # Configuration
│   ├── service_config.py       # Extends UnifiedCloudConfig
│   └── grid_generator.py       # < 1200 lines (delegates to storage)
│
├── cli/                         # CLI handlers
│   ├── handlers/
│   │   ├── backtest_handler.py
│   │   └── live_handler.py
│   └── main.py                 # --operation, --mode
│
└── schemas/                     # Output schemas
    └── output_schemas.py
```

---

## 🔧 EXECUTION STRATEGY

### Parallel Agents (Fast Model)
- **Phase 1**: 1 agent (quick wins, sequential dependencies)
- **Phase 2**: 5 agents (one per god class, parallel)
- **Phase 3**: 3 agents (transformations, GCS, validation, parallel)
- **Phase 4**: 1 agent (NautilusTrader mocks, GitHub + context7)
- **Phase 5-7**: 1 agent (sequential, dependencies)

### Quality Gate Checkpoints (BLOCKING)
- After each phase: Run `bash scripts/quality-gates.sh --no-fix`
- Must pass before proceeding to next phase
- Fix ALL issues (including pre-existing)

### Local Testing Only
- NO commits until Master CI/CD Plan is ready
- Run quality gates locally
- Verify with `pytest` after each change

---

## 📚 RELATED DOCUMENTS

1. **Brainstorming**: `.cursor/plans/execution_service_structural_refactoring_brainstorm.md`
2. **Plan**: `.cursor/plans/execution_service_refactoring_0c597f7f.plan.md`
3. **Service Structure**: `.cursor/plans/service_structure_standardization_4a4b3ff3.plan.md`
4. **Structural Analysis**: Previous agent report (agent-xxx)
5. **Reference**: `instruments-service/` (clean structure example)
6. **Codex**: `unified-trading-codex/06-coding-standards/`

---

## 🚀 READY TO EXECUTE

**Master orchestrator** (this agent): Maintains high-level context, delegates to sub-agents

**Next step**: Launch Phase 1 Quick Wins with fast sub-agent

**User approval needed**: Confirm ready to proceed with Phase 1?
