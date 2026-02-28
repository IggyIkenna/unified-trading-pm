# execution-service Structural Refactoring: Brainstorming

**Date**: 2026-02-24
**Goal**: Transform execution-service from 25% coverage to 50%+ by fixing structural issues
**Reference**: instruments-service as clean structure example

---

## 🎯 Core Problems Identified

### 1. God Classes (5 files > 1500 lines - BLOCKING quality gates!)
- BacktestEngine: 2,681 lines (should be < 800)
- GridConfigGenerator: 2,277 lines (should be < 1500)
- PreflightChecker: 2,108 lines (should be < 1500)
- ResultSerializer: 2,017 lines (should be < 1500)
- DataConfigBuilder: 1,873 lines (should be < 1500)

### 2. Hard Dependencies (Untestable)
- 10+ files with direct GCS usage (should use StorageAdapter)
- Top-level `execution_algo_library` import blocks test collection
- No abstraction for risk service, order adapters
- 150+ functions returning `None` (hard to assert)

### 3. DRY Violations
- 4 different instrument ID conversion implementations
- 4 duplicated UCS storage import patterns
- 4 different GCS upload implementations
- Scattered conversion helpers across 5+ files

### 4. Missing Abstractions
- No StorageAdapter (like instruments-service has)
- No RiskServiceClient abstraction
- No OrderAdapterFactory
- No mock factories in conftest

---

## 🏗️ Proposed Structure (Based on instruments-service)

### Current (Messy):
```
execution_service/
├── algorithms/          # 6,537 lines (moving to library)
├── backtest/            # 7,293 lines (god classes!)
├── data/                # 9,686 lines (mixed concerns)
├── matching/            # Moving to library
├── orchestration/       # Import issues
├── results/             # 3,482 lines (serializer god class)
├── services/            # Mixed
├── utils/               # Scattered helpers
└── venues/              # 3,689 lines (moving to library)
```

### Proposed (Clean):
```
execution_service/
├── adapters/            # Thin I/O adapters (< 100 lines each)
│   ├── storage.py       # GCS operations via UCS
│   ├── risk_service.py  # Risk check HTTP client
│   ├── order_adapter.py # Order execution via unified-trade-execution-interface
│   ├── matching.py      # Matching via matching-engine-library
│   ├── algorithms.py    # Algorithms via execution-algo-library
│   └── defi.py          # DeFi via unified-defi-execution-interface
│
├── engine/              # Core business logic (testable!)
│   ├── orchestration/
│   │   ├── orchestrator.py      # < 200 lines (delegates to components)
│   │   ├── order_tracker.py     # Order tracking only
│   │   ├── risk_checker.py      # Risk validation (calls adapter)
│   │   └── order_submitter.py   # Order submission (calls adapter)
│   │
│   ├── backtest/
│   │   ├── engine.py            # < 800 lines (orchestrates only)
│   │   ├── validator.py         # Preflight validation
│   │   ├── signal_loader.py     # Signal loading
│   │   ├── data_loader.py       # Data loading (calls adapter)
│   │   ├── node_builder.py      # Node configuration
│   │   └── result_extractor.py  # Result extraction
│   │
│   ├── routing/
│   │   ├── instruction_router.py
│   │   └── instruction_validator.py
│   │
│   └── processors/
│       ├── signal_processor.py
│       └── instruction_processor.py
│
├── utils/               # Shared utilities (pure functions)
│   ├── transformations.py       # All conversion helpers
│   ├── validation.py            # Common validators
│   ├── instrument_conversion.py # Single source for ID conversion
│   └── datetime_utils.py        # UTC datetime helpers
│
├── config/              # Configuration (extends UnifiedCloudConfig)
│   ├── service_config.py
│   └── grid_generator.py        # < 1500 lines (delegates to storage adapter)
│
├── cli/                 # CLI handlers
│   ├── handlers/
│   │   ├── backtest_handler.py
│   │   └── live_handler.py
│   └── main.py
│
└── schemas/             # Output schemas
    └── output_schemas.py
```

---

## 💡 Key Improvements from instruments-service Pattern

### 1. **Thin Adapters** (instruments-service/adapters/storage_adapter.py)

**Pattern**: 122 lines, pure I/O, delegates to `StandardizedDomainCloudService`

```python
class StorageAdapter:
    """Thin storage adapter - I/O only, NO business logic."""

    def __init__(self, cloud_target: CloudTarget | None = None):
        self.cloud_service = StandardizedDomainCloudService(
            domain="execution",
            cloud_target=cloud_target
        )

    def upload_batch(self, uploads: list[tuple[str, pd.DataFrame, str]]) -> list[dict]:
        """Upload via StandardizedDomainCloudService."""
        batch_uploads = [{"data": df, "gcs_path": path, "format": "parquet"}
                        for path, df, _ in uploads]
        return self.cloud_service.upload_to_gcs_batch(batch_uploads)
```

**Benefits**:
- ✅ Easy to mock (inject mock adapter)
- ✅ Cloud-agnostic (no direct GCS imports)
- ✅ Testable (pure I/O, no business logic)
- ✅ Single responsibility

### 2. **Orchestrator Pattern** (instruments-service has 371 lines max)

**Current**: LiveOrchestrator 450 lines, mixed concerns
**Target**: < 200 lines, delegates everything

```python
class LiveOrchestrator:
    """Orchestrates live execution - delegates to components."""

    def __init__(
        self,
        risk_checker: RiskChecker,           # Injected
        order_submitter: OrderSubmitter,     # Injected
        order_tracker: OrderTracker,         # Injected
        algo_factory: AlgorithmFactory,      # Injected
    ):
        self.risk_checker = risk_checker
        self.order_submitter = order_submitter
        self.order_tracker = order_tracker
        self.algo_factory = algo_factory

    async def execute_instruction(self, instruction: Instruction) -> ExecutionResult:
        """Orchestrate execution - delegates to components."""
        # 1. Risk check (delegates)
        risk_ok = await self.risk_checker.check(instruction)
        if not risk_ok:
            return ExecutionResult(status=ExecutionStatus.REJECTED_RISK)

        # 2. Select algorithm (delegates)
        algo = self.algo_factory.create(instruction.algorithm)

        # 3. Execute (delegates)
        result = await self.order_submitter.execute(instruction, algo)

        # 4. Track (delegates)
        self.order_tracker.track(instruction.instruction_id, result)

        return result
```

**Benefits**:
- ✅ Testable (inject mocks for all components)
- ✅ Clear responsibilities
- ✅ No direct external dependencies
- ✅ Easy to understand

### 3. **Separate Validation** (instruments-service/engine/validation/)

**Current**: Validation scattered across BacktestEngine, PreflightChecker
**Target**: Dedicated validator classes

```python
class BacktestValidator:
    """Validates backtest configuration and dependencies."""

    def __init__(self, storage: StorageAdapter, config: BacktestConfig):
        self.storage = storage
        self.config = config

    def validate_all(self) -> ValidationResult:
        """Run all validations."""
        results = [
            self.validate_catalog_bars(),
            self.validate_instructions(),
            self.validate_data_availability(),
        ]
        return ValidationResult.aggregate(results)
```

### 4. **Dependency Injection** (Not Global Singletons)

**Current**: Direct `get_storage_client()` calls everywhere
**Target**: Inject adapters

```python
# ❌ BAD (Hard to test)
class BacktestEngine:
    def __init__(self, config):
        self.storage = get_storage_client()  # Direct dependency!

    def load_data(self):
        self.storage.download_blob(...)  # Hard to mock

# ✅ GOOD (Easy to test)
class BacktestEngine:
    def __init__(self, config, storage: StorageAdapter):
        self.storage = storage  # Injected!

    def load_data(self):
        self.storage.download(...)  # Easy to mock
```

---

## 🔧 Specific Refactoring Actions

### Action 1: Create StorageAdapter (Like instruments-service)

**File**: `execution_service/adapters/storage.py`

**Responsibilities**:
- Build GCS paths (results, configs, data)
- Upload/download via `StandardizedDomainCloudService`
- Bucket selection
- NO business logic, validation, or transformation

**Replace**:
- `utils/gcs_service.py` (179 lines)
- `utils/execution_cloud_service.py` (GCS methods)
- Direct `get_storage_client()` calls in 10+ files

**Benefits**:
- Single source for GCS operations
- Easy to mock in tests
- Cloud-agnostic

### Action 2: Create RiskChecker (NOT HTTP Client!)

**File**: `execution_service/engine/risk/risk_checker.py`

**CRITICAL INSIGHT FROM USER**: Risk checks via HTTP are too slow. Instead, import `risk-and-exposure-service` as a **package dependency** and run calculations locally in a "light operational mode".

**Responsibilities**:
- Import risk calculation logic from risk-and-exposure-service
- Run risk checks locally (no HTTP)
- Use risk config to determine limits
- Return risk approval/rejection

**Pattern**:
```python
# execution_service/engine/risk/risk_checker.py
from risk_and_exposure_service.engine.calculators import RiskCalculator
from risk_and_exposure_service.config import RiskConfig

class RiskChecker:
    """Local risk checker - imports risk service as package."""

    def __init__(self, risk_config: RiskConfig):
        self.calculator = RiskCalculator(risk_config)

    def check_instruction(self, instruction: TradeInstruction) -> RiskCheckResult:
        """Check risk locally (no HTTP)."""
        # Use risk service's calculator
        exposure = self.calculator.calculate_exposure(instruction)

        if exposure > self.calculator.max_exposure:
            return RiskCheckResult(
                approved=False,
                reason=f"Exposure {exposure} exceeds limit {self.calculator.max_exposure}"
            )

        return RiskCheckResult(approved=True)
```

**Benefits**:
- ✅ Fast (no HTTP overhead)
- ✅ Reuses risk service logic (no duplication)
- ✅ Easy to test (inject mock calculator)
- ✅ Consistent risk rules (same code as risk service)

**Add to pyproject.toml**:
```toml
[tool.uv.sources]
risk-and-exposure-service = { path = "../risk-and-exposure-service" }
```

### Action 3: Fix Orchestration Import Issue

**Problem**: `orchestration/__init__.py` imports `LiveOrchestrator` → imports `execution_algo_library` → blocks test collection

**Solution 1** (Quick): Lazy import in LiveOrchestrator
```python
# orchestration/orchestrator.py
def _execute_twap(self, instruction):
    from execution_algo_library import TWAPAlgorithm  # Lazy import
    algo = TWAPAlgorithm(...)
```

**Solution 2** (Better): AlgorithmFactory with dependency injection
```python
# adapters/algorithms.py
class AlgorithmFactory:
    """Factory for creating algorithms from library."""

    def create(self, algo_type: str, config: dict):
        from execution_algo_library import (
            TWAPAlgorithm,
            VWAPAlgorithm,
            AdaptiveTWAPCalculator,
        )
        # Factory logic
```

**Solution 3** (Best): Split `orchestration/__init__.py`
```python
# orchestration/__init__.py
from execution_service.orchestration.order_tracker import OrderTracker

# Don't import LiveOrchestrator here
# Import it explicitly where needed
```

### Action 4: Break Up BacktestEngine (2,681 → < 800 lines)

**Extract these components**:

1. **BacktestValidator** (validation methods)
   - `_validate_catalog_bars`
   - `_validate_instructions`
   - `_validate_data_availability`
   - `_validate_instruction_data_availability`

2. **SignalLoader** (signal loading methods)
   - `_load_signals_single_day`
   - `_load_signals_multi_day`
   - `_load_signals`
   - `_convert_instructions_to_signals`
   - `_filter_signal_schedule_by_window`

3. **DataLoader** (data loading methods)
   - `_load_data_for_instrument`
   - `_build_data_configurations`
   - `_build_instruction_based_data_configs`

4. **NodeBuilder** (already exists, use it more)
   - `_build_node_configurations`

5. **ResultExtractor** (already exists, use it more)
   - `_extract_results`
   - `_calculate_instruction_alpha`

**Result**: BacktestEngine becomes pure orchestrator (< 800 lines)

### Action 5: Centralize Instrument ID Conversion

**Problem**: 4 different implementations

**Solution**: Single source in `utils/instrument_conversion.py`

```python
# utils/instrument_conversion.py
def to_gcs_format(instrument_id: str) -> str:
    """Convert instrument ID to GCS format (canonical)."""
    # Single implementation
    return instrument_id.replace("/", "-").replace(".", "-")

def from_gcs_format(gcs_id: str) -> tuple[str, str, str]:
    """Parse GCS format to components."""
    # Single implementation
    parts = gcs_id.split("-")
    return parts[0], parts[1], parts[2]

def to_nautilus_format(instrument_id: str) -> str:
    """Convert to NautilusTrader format."""
    # Single implementation
    pass
```

**Remove**:
- `data/checker._convert_instrument_id_to_gcs_format`
- Duplicates in other files

### Action 6: Create Mock Factories (Like api-contracts)

**File**: `tests/conftest.py` (expand significantly)

**Add mock factories**:

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from api_contracts.binance.schemas import BinanceOrder, BinanceTrade

@pytest.fixture
def mock_storage_adapter():
    """Mock storage adapter for GCS operations."""
    adapter = MagicMock()
    adapter.upload_batch.return_value = [{"success": True}]
    adapter.download.return_value = pd.DataFrame(...)
    return adapter

@pytest.fixture
def mock_risk_service():
    """Mock risk service client."""
    client = MagicMock()
    client.check_risk.return_value = {"approved": True}
    return client

@pytest.fixture
def mock_order_adapter():
    """Mock order adapter."""
    adapter = MagicMock()
    adapter.submit_order.return_value = BinanceOrder(...)
    return adapter

@pytest.fixture
def instruction_builder():
    """Builder for test instructions."""
    class InstructionBuilder:
        def trade(self, symbol="BTC-USDT", quantity=100):
            return TradeInstruction(...)

        def swap(self, token_in="USDT", token_out="ETH"):
            return SwapInstruction(...)

    return InstructionBuilder()
```

### Action 7: Use api-contracts for NautilusTrader Mocking

**Problem**: NautilusTrader is external dependency, hard to mock

**Solution**: Reverse engineer NautilusTrader types in api-contracts

**Add to api-contracts**:
```
api-contracts/
├── nautilus/
│   ├── __init__.py
│   ├── schemas.py           # Order, Position, Instrument, Fill, etc.
│   ├── cache.py             # Cache Protocol
│   ├── clock.py             # Clock Protocol
│   └── mocks.py             # Mock implementations
```

**Benefits**:
- ✅ Type-safe mocks (Pydantic schemas)
- ✅ No need for NautilusTrader in tests
- ✅ Control exact behavior in tests
- ✅ Faster test execution

**Use context7 + https://github.com/nautechsystems/nautilus_trader** to understand:
- Order model structure
- Position model structure
- Cache interface
- Clock interface
- Event types

### Action 8: Functions Returning Values (Not None)

**Problem**: 150+ functions return `None`, hard to assert

**Pattern 1**: Return Result objects
```python
# ❌ BAD
def process_order(order) -> None:
    # Do stuff
    logger.info("Processed")

# ✅ GOOD
def process_order(order) -> ProcessResult:
    # Do stuff
    return ProcessResult(
        success=True,
        order_id=order.id,
        fills=fills,
    )
```

**Pattern 2**: Return status codes
```python
# ❌ BAD
def validate(config) -> None:
    if not valid:
        raise ValueError("Invalid")

# ✅ GOOD
def validate(config) -> ValidationResult:
    if not valid:
        return ValidationResult(
            valid=False,
            errors=["Invalid config"],
        )
    return ValidationResult(valid=True)
```

---

## 🎯 Comparison: execution-service vs instruments-service

| Aspect | instruments-service ✅ | execution-service ❌ |
|--------|----------------------|---------------------|
| **Largest file** | 862 lines | 2,681 lines |
| **Adapters** | Yes (storage_adapter.py) | No (direct GCS) |
| **Config** | UnifiedCloudConfig | Mixed (some fallbacks) |
| **Event logging** | unified-events-interface | Mixed |
| **Structure** | engine/, adapters/, cli/, config/ | Flat, mixed concerns |
| **Test coverage** | ~50%+ | 25% |
| **Testability** | High (dependency injection) | Low (hard dependencies) |

---

## 🚀 Proposed Refactoring Phases

### Phase 1: Quick Wins (Unblock Tests) - This Week

**Goal**: Get tests running, reach 30-35% coverage

1. **Fix orchestration import** (lazy import or factory)
2. **Create StorageAdapter** (like instruments-service)
3. **Create RiskServiceClient** adapter
4. **Add mock factories** to conftest
5. **Centralize instrument conversion** (single source)

**Estimated Impact**: +5-10% coverage (25% → 30-35%)

### Phase 2: Break Up God Classes - 1-2 Weeks

**Goal**: Files < 1500 lines, reach 40-45% coverage

1. **BacktestEngine**: Extract validator, signal loader, data loader
2. **GridConfigGenerator**: Extract uploader, delegate to storage adapter
3. **PreflightChecker**: Split into smaller validators
4. **ResultSerializer**: Extract timeline builder, delegate to storage adapter
5. **DataConfigBuilder**: Extract cache manager, delegate to storage adapter

**Estimated Impact**: +10-15% coverage (35% → 45-50%)

### Phase 3: DRY Refactoring - 1 Week

**Goal**: Single source of truth, reach 50%+ coverage

1. **Centralize conversions** (utils/transformations.py)
2. **Single GCS upload** (via StorageAdapter)
3. **Remove duplicated validation**
4. **Extract common patterns**

**Estimated Impact**: +5% coverage (45% → 50%)

### Phase 4: Add NautilusTrader Mocks - 1 Week

**Goal**: Remove external dependency in tests

1. **Create api-contracts/nautilus/** (use context7 + GitHub)
2. **Mock Order, Position, Instrument, Cache, Clock**
3. **Replace NautilusTrader imports in tests**

**Estimated Impact**: +5% coverage (50% → 55%)

---

## 🤔 Open Questions for Brainstorming

### Q1: StorageAdapter Scope

**Option A**: Single StorageAdapter for all GCS operations
- Pro: Simple, single source
- Con: May become large

**Option B**: Multiple adapters (ResultsStorage, ConfigStorage, DataStorage)
- Pro: Separation of concerns
- Con: More files, more complexity

**Recommendation**: Start with single StorageAdapter (like instruments-service), split later if needed

### Q2: RiskServiceClient Location

**Option A**: `adapters/risk_service.py`
- Pro: Consistent with other adapters
- Con: HTTP client, not I/O adapter

**Option B**: `clients/risk_service.py`
- Pro: Clearer distinction (client vs adapter)
- Con: New directory

**Recommendation**: Use `adapters/` for consistency, rename to `clients/` later if needed

### Q3: AlgorithmFactory Pattern

**Option A**: Factory in adapters
```python
# adapters/algorithms.py
class AlgorithmFactory:
    def create(self, algo_type: str, config: dict):
        from execution_algo_library import ...
        # Factory logic
```

**Option B**: Registry pattern
```python
# adapters/algorithms.py
class AlgorithmRegistry:
    def __init__(self):
        self._algos = {}

    def register(self, name: str, algo_class):
        self._algos[name] = algo_class

    def create(self, name: str, config: dict):
        return self._algos[name](config)
```

**Recommendation**: Factory pattern (simpler, sufficient for now)

### Q4: NautilusTrader Mocking Strategy

**Option A**: Full reverse engineering in api-contracts
- Pro: Complete control, type-safe
- Con: Large effort, maintenance burden

**Option B**: Minimal Protocol types
- Pro: Faster, less maintenance
- Con: May miss edge cases

**Option C**: Use NautilusTrader's test utilities
- Pro: Official mocks
- Con: Still depends on NautilusTrader

**Recommendation**: Option B (Minimal Protocols) + expand as needed

### Q5: Functions Returning None

**Option A**: Return Result objects everywhere
- Pro: Explicit success/failure
- Con: More boilerplate

**Option B**: Return status codes/enums
- Pro: Simple
- Con: Less information

**Option C**: Mix (return values for queries, None for commands)
- Pro: Pragmatic
- Con: Inconsistent

**Recommendation**: Option A for critical paths, Option C elsewhere

### Q6: File Size Limits

**Current quality gate**: Files > 1500 lines fail

**Should we**:
- Keep 1500 line limit?
- Reduce to 1000 lines?
- Reduce to 800 lines (stricter)?

**Recommendation**: Keep 1500 for now, aim for < 800 in new code

---

## 📊 Expected Coverage Trajectory

| Phase | Coverage | Tests | Effort |
|-------|----------|-------|--------|
| **Current** | 25% | 586 | - |
| **After Phase 1** | 30-35% | ~450 | 1 week |
| **After Phase 2** | 40-45% | ~500 | 2 weeks |
| **After Phase 3** | 50%+ | ~550 | 1 week |
| **After Phase 4** | 55%+ | ~600 | 1 week |

**Total**: 5 weeks to reach 55% coverage with clean structure

---

## 💾 Line Count Savings Analysis

### Current State
- **Total lines**: 66,482 lines (excluding tests)
- **God classes**: 6,571 lines (10% of codebase!)
  - BacktestEngine: 2,681 lines
  - GridConfigGenerator: 2,277 lines
  - PreflightChecker: 2,108 lines
  - ResultSerializer: 2,017 lines
  - DataConfigBuilder: 1,873 lines

### Expected Savings

**Phase 1: Quick Wins** (-500 lines, -0.8%)
- Fix orchestration import: 0 lines (structural fix)
- Create StorageAdapter: +150 lines (new file)
- Create RiskChecker: +100 lines (new file)
- Centralize instrument conversion: -200 lines (remove 3 duplicates)
- Add mock factories: +50 lines (conftest)
- **Net**: -500 lines (remove duplicated conversions, GCS patterns)

**Phase 2: Break Up God Classes** (-3,000 lines, -4.5%)
- BacktestEngine (2,681 → 800): Extract 1,881 lines to:
  - BacktestValidator: 400 lines
  - SignalLoader: 600 lines
  - DataLoader: 500 lines
  - NodeBuilder: 200 lines (already exists, use more)
  - ResultExtractor: 181 lines (already exists, use more)
- GridConfigGenerator (2,277 → 1,200): Extract 1,077 lines to:
  - StorageAdapter usage: -400 lines (delegate to adapter)
  - Config validation: 300 lines (separate validator)
  - Grid builder: 377 lines (separate builder)
- PreflightChecker (2,108 → 800): Extract 1,308 lines to:
  - Multiple validators: 1,308 lines (split by concern)
- ResultSerializer (2,017 → 800): Extract 1,217 lines to:
  - TimelineBuilder: 500 lines
  - StorageAdapter usage: -400 lines (delegate)
  - Result formatter: 317 lines
- DataConfigBuilder (1,873 → 800): Extract 1,073 lines to:
  - CacheManager: 400 lines
  - StorageAdapter usage: -300 lines (delegate)
  - Config builder: 373 lines
- **Net**: -3,000 lines (extracted components are more focused, less duplication)

**Phase 3: DRY Refactoring** (-1,500 lines, -2.3%)
- Centralize transformations: -400 lines (4 duplicates → 1)
- Single GCS upload via StorageAdapter: -600 lines (4 implementations → 1)
- Remove duplicated validation: -300 lines
- Extract common patterns: -200 lines
- **Net**: -1,500 lines

**Phase 4: NautilusTrader Mocks** (+800 lines, +1.2%)
- Create api-contracts/nautilus/: +800 lines (new schemas/mocks)
- Remove NautilusTrader test dependencies: 0 lines (imports change)
- **Net**: +800 lines (but improves testability)

**Phase 5: Adapter Creation** (+400 lines, +0.6%)
- StorageAdapter: 150 lines
- RiskChecker: 100 lines
- OrderAdapter: 80 lines
- AlgorithmFactory: 70 lines
- **Net**: +400 lines (thin adapters)

### Total Savings

| Category | Lines Saved | % of Codebase |
|----------|-------------|---------------|
| **Quick Wins** | -500 | -0.8% |
| **God Class Breakup** | -3,000 | -4.5% |
| **DRY Refactoring** | -1,500 | -2.3% |
| **NautilusTrader Mocks** | +800 | +1.2% |
| **Adapter Creation** | +400 | +0.6% |
| **NET SAVINGS** | **-3,800 lines** | **-5.7%** |

### Final State
- **Current**: 66,482 lines
- **After refactoring**: ~62,682 lines
- **Reduction**: 3,800 lines (5.7%)

**But more importantly**:
- ✅ 5 god classes → 20+ focused components (< 800 lines each)
- ✅ 4 duplicate patterns → 1 canonical implementation
- ✅ Hard dependencies → Injected adapters (testable!)
- ✅ 150+ functions returning None → Result objects
- ✅ 25% coverage → 55% coverage

**Quality over quantity**: The 5.7% line reduction is less important than the **structural improvements** that enable testing and maintenance.

---

## 🎯 Immediate Next Steps (For Discussion)

1. **Agree on structure** (adapters/, engine/, utils/, config/, cli/)
2. **Agree on adapter scope** (single vs multiple storage adapters)
3. **Agree on NautilusTrader mocking** (full reverse engineering vs minimal protocols)
4. **Agree on function return types** (Result objects vs status codes)
5. **Start Phase 1** (quick wins to unblock tests)

---

## 📝 Notes

### instruments-service Lessons

**What works well**:
- ✅ Thin adapters (storage_adapter.py: 122 lines)
- ✅ Clear separation (engine/, adapters/, cli/, config/)
- ✅ Dependency injection (adapters injected into engine)
- ✅ No god classes (largest: 862 lines)
- ✅ StandardizedDomainCloudService usage

**Apply to execution-service**:
- Create similar adapter structure
- Break up god classes
- Use dependency injection
- Delegate to unified libraries

### api-contracts Lessons

**What works well**:
- ✅ Pydantic schemas for external APIs
- ✅ Type-safe mocks
- ✅ VCR for recording/replaying HTTP

**Apply to execution-service**:
- Create nautilus/ schemas in api-contracts
- Mock NautilusTrader types
- Use in tests instead of real NautilusTrader

### unified-trade-execution-interface Rename

**Note**: Should be renamed to `unified-trade-execution-interface` per plan
- Update all references
- Update imports
- Update documentation

---

## 💡 Key Tips from service_structure_standardization Plan

### 1. **Risk Checker as Package Dependency** (User Insight!)
- ❌ **DON'T**: HTTP client for risk checks (too slow)
- ✅ **DO**: Import risk-and-exposure-service as package, run calculations locally
- **Pattern**: Light operational mode, use risk config, no HTTP overhead

### 2. **Thin Adapters Pattern** (Critical!)
- **Size**: <100 lines MAX (<20 for simple, <50 for multiple ops)
- **Delegate to libraries**: UCS (storage), UCI (config), UEI (events), UMI (market data)
- **NO business logic**: No transformations, filtering, validation
- **Example**: StorageAdapter delegates to `StandardizedDomainCloudService`

### 3. **Operation-Based Organization**
```
engine/
  operations/          # Operation-specific logic
    backtest/
    live_execution/
  processors/          # Shared processors
  validation/          # Standard validation
```

### 4. **Dependency Injection Everywhere**
- ❌ **BAD**: `self.storage = get_storage_client()` (hard dependency)
- ✅ **GOOD**: `def __init__(self, storage: StorageAdapter)` (injected)
- **Benefits**: Easy to mock, testable, clear contracts

### 5. **StandardizedDomainCloudService Usage**
```python
# adapters/storage.py
from unified_domain_client.standardized_service import StandardizedDomainCloudService

class StorageAdapter:
    def __init__(self, cloud_target: CloudTarget):
        self.cloud_service = StandardizedDomainCloudService(
            domain="execution",
            cloud_target=cloud_target
        )

    def upload_batch(self, uploads: list[tuple[str, pd.DataFrame, str]]):
        batch_uploads = [{"data": df, "gcs_path": path, "format": "parquet"}
                        for path, df, _ in uploads]
        return self.cloud_service.upload_to_gcs_batch(batch_uploads)
```

### 6. **Quality Gate Checkpoints**
- **BLOCKING**: Each phase must pass quality gates before proceeding
- **Pilot first**: instruments-service passed, then replicate pattern
- **Fix ALL issues**: Including pre-existing (file size, circular imports, coverage)

### 7. **CLI Pattern** (--operation + --mode)
```python
# cli/main.py
def main():
    args = parse_arguments()

    # Dispatch by operation (WHAT)
    if args.operation == "backtest":
        handler = BacktestHandler(config, mode=args.mode)
    elif args.operation == "live_execution":
        handler = LiveExecutionHandler(config, mode=args.mode)

    # Execute by mode (HOW)
    if args.mode == "batch":
        result = handler.run_batch(start_date=args.start_date, end_date=args.end_date)
    else:  # live
        result = handler.run_live(interval=args.interval)
```

### 8. **Config Types** (Two Distinct Types!)
| Type | Purpose | Storage | UCI Feature |
|------|---------|---------|-------------|
| **Grid config** | Param optimization, many configs per run | Domain buckets (`execution-store`) | NOT ConfigStore |
| **Runtime config** | Service runtime params, slow-changing | `gs://config-store-{proj}/{service}/` | ConfigStore + TimeSeriesConfigStore |

**execution-service has BOTH**:
- Grid config: BacktestEngine parameter grids (keep in domain bucket)
- Runtime config: Service settings (migrate to ConfigStore)

### 9. **Mock Factories in conftest** (Critical for Testing!)
```python
# tests/conftest.py
@pytest.fixture
def mock_storage_adapter():
    adapter = MagicMock()
    adapter.upload_batch.return_value = [{"success": True}]
    return adapter

@pytest.fixture
def instruction_builder():
    class InstructionBuilder:
        def trade(self, symbol="BTC-USDT", quantity=100):
            return TradeInstruction(...)
    return InstructionBuilder()
```

### 10. **api-contracts for External Dependencies**
- **Problem**: NautilusTrader is external, hard to mock
- **Solution**: Reverse engineer types in `api-contracts/nautilus/`
- **Use**: context7 + https://github.com/nautechsystems/nautilus_trader
- **Create**: Order, Position, Instrument, Cache, Clock schemas

### 11. **File Size Limits** (Quality Gates)
- **Current**: >1500 lines FAILS quality gates
- **Target**: <800 lines for new code
- **God classes**: MUST split (BacktestEngine 2,681 → 800)

### 12. **Parallel Agent Strategy**
- **Cross-repo**: Always parallelize (zero conflict risk)
- **Same repo, different files**: Parallelize if no dependencies
- **Same file**: Sequential only
- **Max**: 4 concurrent agents

### 13. **instruments-service as Reference**
- **Largest file**: 862 lines (vs execution-service 2,681!)
- **Adapters**: Thin (storage_adapter.py: 122 lines)
- **Structure**: Clean (engine/, adapters/, cli/, config/)
- **Coverage**: ~50%+ (vs execution-service 25%)

---

## 🔍 Questions to Answer Before Proceeding

1. **Do you agree with the proposed structure?** (adapters/, engine/, utils/, config/, cli/)
2. **Should we create api-contracts/nautilus/ for mocking?** (use context7 + GitHub)
3. **Should we start with Phase 1 quick wins?** (StorageAdapter, RiskServiceClient, mock factories)
4. **Any specific concerns about breaking up god classes?** (BacktestEngine, GridConfigGenerator, etc.)
5. **Should functions return Result objects or keep returning None?**

**Your feedback will guide the implementation!**
