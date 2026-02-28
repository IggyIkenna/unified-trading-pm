# instruments-service: Complete File-by-File Refactoring Plan

**Related Documents**:
- Main plan: `.cursor/plans/service_structure_standardization_4a4b3ff3.plan.md`
- API keys process: `instruments-service/docs/API_KEYS_STANDARDIZED_PROCESS.md`
- Quality gate audit: `instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md`
- API keys plan: `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md`

**This document consolidates**:
- INSTRUMENTS_SERVICE_REFACTORING.md (deleted, merged here)
- File-by-file mapping for complete refactoring

**Related plans:**
- `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md` — API keys standardization, instrument reader consolidation, aggregated instruments ownership

---

## Current Structure (All Files)

```
instruments_service/
├── __init__.py (48 lines)
├── __main__.py (9 lines)
├── config.py (629 lines)                          # ⚠️ Should be package, not file
├── models.py (13 lines)
├── events.py (18 lines)
├── app/
│   ├── __init__.py
│   └── core/                                      # ❌ ENTIRE DIRECTORY MOVES
│       ├── adapter_loader.py (155 lines)
│       ├── batch_processor.py (273 lines)
│       ├── cloud_data_provider.py (298 lines)     # ❌ "cloud" in name
│       ├── cloud_instrument_storage.py (418 lines) # ❌ "cloud" in name
│       ├── dependency_checker.py (340 lines)
│       ├── instrument_processing_service.py (1228) # ❌ >1500 limit
│       ├── instruments_service.py (1195)          # ❌ >1500 limit
│       ├── selective_validation.py (133 lines)
│       └── processors/
│           ├── __init__.py
│           ├── canonical_key_generator.py (182)
│           ├── ccxt_manual_fallback.py (178)
│           ├── defi_processor.py (362)
│           ├── derived_fields_populator.py (235)
│           └── symbol_parser.py (364)
├── cli/                                           # ✅ KEEP (update handlers)
│   ├── __init__.py
│   ├── base_handler.py (73 lines)
│   ├── main.py (253 lines)
│   ├── parser.py (338 lines)
│   └── handlers/
│       ├── __init__.py
│       ├── corporate_actions_backfill_handler.py (558)  # ❌ DELETE (deprecated)
│       ├── corporate_actions_handler.py (535)           # ⚠️ KEEP or merge
│       ├── corporate_actions_production_handler.py (620) # ✅ KEEP (main)
│       ├── corporate_actions_update_handler.py (217)    # ❌ DELETE (deprecated)
│       ├── generate_date_views_handler.py (245)         # ❌ DELETE (deprecated)
│       ├── instrument_handler.py (426)                  # ✅ KEEP
│       └── live_mode_handler.py (319)                   # ✅ KEEP
├── config/                                        # ✅ KEEP (domain data)
│   ├── __init__.py
│   ├── api_keys.py (29 lines)
│   ├── data_type_config.py (70 lines)
│   ├── instrument_definitions.py (1126)           # ⚠️ Large but domain data
│   ├── service_config.py (252 lines)
│   ├── tradfi_exchange_mappings.py (171 lines)
│   └── venue_config.py (89 lines)
├── engine/operations/                             # ✅ NEW (operation-specific logic)
│   ├── instruments/                               # Instruments operation
│   │   └── (logic from app/core/instruments_service.py)
│   └── corporate_actions/                         # Corporate actions operation
│       ├── adapter.py (450 lines)                 # From corporate_actions/
│       ├── models.py (209 lines)                  # From corporate_actions/
│       └── utils.py                               # ✅ NEW (extracted from handlers)
├── data/                                          # ✅ KEEP (static domain data)
│   ├── sp500_tickers.json
│   └── tradfi_instruments.json
├── io/                                            # ❌ DELETE (merge into adapters/)
│   ├── __init__.py
│   └── writer.py (63 lines)                       # → adapters/storage_adapter.py
├── schemas/                                       # ✅ KEEP (service-owned schemas)
│   ├── __init__.py
│   ├── README.md
│   ├── output_schemas.py (488 lines)
│   └── parquet.py (598 lines)
└── utils/                                         # ⚠️ EVALUATE (may move to engine/)
    ├── __init__.py
    ├── ccxt_service.py (838 lines)                # ⚠️ Large, venue-specific
    └── special_instruments.py (324 lines)
```

---

## Target Structure (After Refactoring)

```
instruments_service/
├── __init__.py                                    # ✅ KEEP
├── __main__.py                                    # ✅ KEEP
├── config.py                                      # ✅ KEEP (top-level singleton)
├── models.py                                      # ✅ KEEP
├── events.py                                      # ✅ KEEP
├── engine/                                        # ✅ NEW (from app/core/)
│   ├── __init__.py
│   ├── orchestrator.py                            # Top-level orchestration (dispatches to operations)
│   ├── operations/                                # ✅ NEW (operation-specific logic)
│   │   ├── __init__.py
│   │   ├── instruments/                           # Instruments operation
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py                    # From instruments_service.py (instruments logic, ~600 lines)
│   │   │   ├── batch_orchestrator.py              # From batch_processor.py
│   │   │   └── processors/                        # Category processors
│   │   │       ├── cefi_processor.py              # Split from instrument_processing_service.py (~400)
│   │   │       ├── tradfi_processor.py            # Split from instrument_processing_service.py (~400)
│   │   │       └── defi_processor.py              # Split from instrument_processing_service.py (~400)
│   │   └── corporate_actions/                     # Corporate actions operation
│   │       ├── __init__.py
│   │       ├── adapter.py                         # From corporate_actions/adapter.py
│   │       ├── models.py                          # From corporate_actions/models.py
│   │       └── utils.py                           # ✅ NEW (extracted from handlers)
│   ├── processors/                                # Shared processors (used by both operations)
│   │   ├── __init__.py
│   │   ├── canonical_key_generator.py             # From app/core/processors/
│   │   ├── ccxt_manual_fallback.py                # From app/core/processors/
│   │   ├── derived_fields_populator.py            # From app/core/processors/
│   │   └── symbol_parser.py                       # From app/core/processors/
│   ├── validation/                                # ✅ NEW (standard validation)
│   │   ├── __init__.py
│   │   ├── dependency_checker.py                  # From app/core/ (STANDARDIZE)
│   │   └── selective_validator.py                 # From selective_validation.py
│   └── venues/                                    # ✅ NEW (venue-specific logic)
│       ├── __init__.py
│       ├── ccxt_service.py                        # From utils/
│       ├── special_instruments.py                 # From utils/
│       └── venue_adapter_loader.py                # From adapter_loader.py
├── adapters/                                      # ✅ NEW (thin wrappers)
│   ├── __init__.py
│   ├── storage_adapter.py                         # From cloud_instrument_storage.py (THIN <100 lines)
│   └── data_source_adapter.py                     # From cloud_data_provider.py + io/writer.py (THIN <100 lines)
├── cli/                                           # ✅ KEEP (update handlers)
│   ├── __init__.py
│   ├── base_handler.py
│   ├── main.py                                    # Update for --operation + --mode
│   ├── parser.py                                  # Update for --operation + --mode
│   └── handlers/
│       ├── __init__.py
│       ├── corporate_actions_handler.py           # ✅ KEEP (consolidated, use ConfigStore)
│       ├── instrument_handler.py                  # ✅ KEEP (use ConfigStore)
│       └── live_mode_handler.py                   # ✅ KEEP (use ConfigReloader)
├── config/                                        # ✅ KEEP (domain data package)
│   ├── __init__.py
│   ├── api_keys.py
│   ├── data_type_config.py
│   ├── instrument_definitions.py                  # Domain data (large OK)
│   ├── service_config.py
│   ├── tradfi_exchange_mappings.py
│   └── venue_config.py
├── corporate_actions/                             # ✅ KEEP (domain logic)
│   ├── __init__.py
│   ├── adapter.py
│   ├── models.py
│   └── utils.py                                   # ✅ NEW (extracted from handlers)
├── schemas/                                       # ✅ KEEP (service-owned schemas)
│   ├── __init__.py
│   ├── README.md
│   ├── output_schemas.py
│   └── parquet.py
└── utils/                                         # ⚠️ MOVE to engine/ (venue-specific logic)
    ├── __init__.py
    ├── ccxt_service.py                            # → engine/venues/ccxt_service.py
    └── special_instruments.py                     # → engine/venues/special_instruments.py
```

---

## File-by-File Changes

### Root Level Files

| File | Lines | Action | Reason |
|------|-------|--------|--------|
| `__init__.py` | 48 | ✅ KEEP | Package init |
| `__main__.py` | 9 | ✅ KEEP | Entry point |
| `config.py` | 629 | ✅ KEEP + UPDATE | Add ConfigStore usage, keep as singleton |
| `models.py` | 13 | ✅ KEEP | Domain models |
| `events.py` | 18 | ✅ KEEP | Event definitions |

**config.py changes**:
```python
# Current (inheritance only)
from unified_config_interface import UnifiedCloudConfig

class InstrumentsServiceConfig(UnifiedCloudConfig):
    service_name: str = "instruments-service"

instruments_config = InstrumentsServiceConfig()

# Target (full UCI usage)
from unified_config_interface import UnifiedCloudConfig, ConfigStore
from pydantic import Field

class InstrumentsServiceConfig(UnifiedCloudConfig):
    __config_schema_version__ = "1.0"
    service_name: str = "instruments-service"
    
    max_workers: int = Field(16, json_schema_extra={"hot_reloadable": True})
    venues: list[str] = Field(default_factory=list, json_schema_extra={"requires_restart": True})

# Singleton with ConfigStore
_config: InstrumentsServiceConfig | None = None
_config_store: ConfigStore | None = None

def get_config() -> InstrumentsServiceConfig:
    global _config, _config_store
    if _config is None:
        _config_store = ConfigStore(
            bucket_name=f"config-store-{project_id}",
            service_name="instruments-service",
            schema_version="1.0"
        )
        _config = _config_store.load_config(InstrumentsServiceConfig)
    return _config

instruments_config = get_config()  # Backward compat
```

---

### app/core/ → engine/ (Complete Restructure)

| Current File | Lines | Target Location | New Name | Changes |
|--------------|-------|-----------------|----------|---------|
| `adapter_loader.py` | 155 | `engine/` | `venue_adapter_loader.py` | Rename for clarity |
| `batch_processor.py` | 273 | `engine/` | `batch_orchestrator.py` | Rename for clarity |
| `cloud_data_provider.py` | 298 | `adapters/` | `data_source_adapter.py` | Remove "cloud", make THIN (<100 lines) |
| `cloud_instrument_storage.py` | 418 | `adapters/` | `storage_adapter.py` | Remove "cloud", make THIN (<100 lines) |
| `dependency_checker.py` | 340 | `engine/validation/` | `dependency_checker.py` | STANDARDIZE (same in all services) |
| `instrument_processing_service.py` | 1228 | SPLIT | `engine/processors/cefi_processor.py`, `tradfi_processor.py`, `defi_processor.py` | Split by category (<500 each) |
| `instruments_service.py` | 1195 | `engine/` | `orchestrator.py` | Orchestration only (~600 lines), remove ErrorWarningCounter |
| `selective_validation.py` | 133 | `engine/validation/` | `selective_validator.py` | Rename for clarity |

#### app/core/processors/ → engine/processors/

| Current File | Lines | Target | Changes |
|--------------|-------|--------|---------|
| `canonical_key_generator.py` | 182 | `engine/processors/` | ✅ KEEP (move as-is) |
| `ccxt_manual_fallback.py` | 178 | `engine/processors/` | ✅ KEEP (move as-is) |
| `defi_processor.py` | 362 | `engine/processors/` | ✅ KEEP (move as-is) |
| `derived_fields_populator.py` | 235 | `engine/processors/` | ✅ KEEP (move as-is) |
| `symbol_parser.py` | 364 | `engine/processors/` | ✅ KEEP (move as-is) |

---

### cli/ (Minimal Changes)

| File | Lines | Action | Changes |
|------|-------|--------|---------|
| `base_handler.py` | 73 | ✅ KEEP | No changes |
| `main.py` | 253 | ✅ UPDATE | Add --operation flag (instruments, corporate_actions, **aggregate**), update dispatch |
| `parser.py` | 338 | ✅ UPDATE | Add --operation arg, backward compat conversion |

**New operation: `aggregate`** — Daily batch job to produce aggregated instruments cache. See `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md` §3.

#### cli/handlers/ (Consolidate)

| Current File | Lines | Action | Changes |
|--------------|-------|--------|---------|
| `instrument_handler.py` | 426 | ✅ KEEP | Add ConfigStore/TimeSeriesConfigStore usage |
| `live_mode_handler.py` | 319 | ✅ KEEP | Add ConfigReloader usage |
| `corporate_actions_production_handler.py` | 620 | ✅ KEEP | Main handler, add ConfigStore |
| `corporate_actions_handler.py` | 535 | ⚠️ EVALUATE | Merge into production or keep for date-range queries? |
| `corporate_actions_backfill_handler.py` | 558 | ❌ DELETE | Deprecated, extract utils first |
| `corporate_actions_update_handler.py` | 217 | ❌ DELETE | Deprecated, extract utils first |
| `generate_date_views_handler.py` | 245 | ❌ DELETE | Deprecated, functionality in production handler |

**Consolidation**:
- Extract `_get_tickers_from_gcs()` to `corporate_actions/utils.py` (used by 4 handlers)
- Keep 1-2 handlers: production (main) + optional date-range handler
- Delete 3 deprecated handlers

---

### config/ Package (KEEP - Domain Data)

| File | Lines | Action | Reason |
|------|-------|--------|--------|
| `__init__.py` | - | ✅ KEEP | Package init |
| `api_keys.py` | 29 | ✅ KEEP | API key management |
| `data_type_config.py` | 70 | ✅ KEEP | Data type mappings |
| `instrument_definitions.py` | 1126 | ✅ KEEP | Domain data (large OK) |
| `service_config.py` | 252 | ✅ KEEP | Service-specific config |
| `tradfi_exchange_mappings.py` | 171 | ✅ KEEP | TradFi exchange mappings |
| `venue_config.py` | 89 | ✅ KEEP | Venue configurations |

**Why keep config/ package**:
- Domain-specific data (instrument definitions, exchange mappings)
- Not runtime config (that's in config.py singleton)
- Large files OK (domain data, not code)

**Relationship to config.py**:
- `config.py` = Runtime config singleton (uses ConfigStore)
- `config/` = Domain data package (static mappings, definitions)

---

### corporate_actions/ (KEEP + Add Utils)

| File | Lines | Action | Changes |
|------|-------|--------|---------|
| `__init__.py` | - | ✅ KEEP | Package init |
| `adapter.py` | 450 | ✅ KEEP | yfinance integration (domain logic) |
| `models.py` | 209 | ✅ KEEP | Corporate actions models |
| `utils.py` | - | ✅ NEW | Extract `_get_tickers_from_gcs()` from 4 handlers |

**New utils.py**:
```python
# corporate_actions/utils.py
from unified_trading_services import get_storage_client

def get_tickers_from_gcs(project_id: str, bucket: str, fallback_dates: list[str]) -> list[str]:
    """Load tickers from GCS instruments data.
    
    Extracted from 4 corporate actions handlers (200+ lines duplicated).
    """
    client = get_storage_client()
    # ... implementation from handlers ...
```

---

### io/ → adapters/ (Merge)

| Current File | Lines | Target | Changes |
|--------------|-------|--------|---------|
| `writer.py` | 63 | `adapters/storage_adapter.py` | Merge into storage adapter (thin) |

**Why merge**:
- `io/writer.py` is I/O logic (belongs in adapters)
- `adapters/storage_adapter.py` will be thin wrapper
- Combine write operations into single adapter

**Target adapter**:
```python
# adapters/storage_adapter.py (THIN <100 lines)
from unified_trading_services import get_storage_client

class StorageAdapter:
    """Thin wrapper - delegates to UCS."""
    
    def __init__(self, bucket: str):
        self.client = get_storage_client()
        self.bucket = bucket
    
    def write_parquet(self, df: pd.DataFrame, path: str) -> None:
        """Delegate to UCS."""
        self.client.write_parquet(df, self.bucket, path)
    
    def read_parquet(self, path: str) -> pd.DataFrame:
        """Delegate to UCS."""
        return self.client.read_parquet(self.bucket, path)
```

**What happens to io/ directory**:
- ❌ DELETE `io/` directory (merged into adapters)

---

### schemas/ (KEEP - Service-Owned)

| File | Lines | Action | Reason |
|------|-------|--------|--------|
| `__init__.py` | - | ✅ KEEP | Package init |
| `README.md` | - | ✅ KEEP | Schema documentation |
| `output_schemas.py` | 488 | ✅ KEEP | Service-owned output schemas |
| `parquet.py` | 598 | ✅ KEEP | Parquet schema definitions |

**Why keep**:
- Service-owned schemas (per codex)
- Schema validation logic (not I/O)
- Used by engine for validation

**No changes needed** - schemas stay as-is.

---

### utils/ → engine/venues/ (Move)

| Current File | Lines | Target | Changes |
|--------------|-------|--------|---------|
| `ccxt_service.py` | 838 | `engine/venues/ccxt_service.py` | Move to engine (venue-specific logic) |
| `special_instruments.py` | 324 | `engine/venues/special_instruments.py` | Move to engine (venue-specific data) |

**Why move to engine**:
- Venue-specific business logic (not I/O)
- Used by processors (engine code)
- Not utilities (they're domain logic)

**New location**:
```
engine/venues/
  __init__.py
  ccxt_service.py          # From utils/
  special_instruments.py   # From utils/
```

**What happens to utils/ directory**:
- ❌ DELETE `utils/` directory (moved to engine/venues)

---

### data/ Directory (Check Contents)

**Need to investigate**: What's in `instruments_service/data/`?

**Possible actions**:
- If test data → Move to `tests/fixtures/`
- If domain data → Move to `config/` or `engine/`
- If empty → DELETE

---

## Summary of Changes

### Directories

| Current | Target | Action |
|---------|--------|--------|
| `app/core/` | `engine/` | MOVE + RESTRUCTURE |
| `app/core/processors/` | `engine/processors/` | MOVE (shared processors) |
| - | `engine/operations/` | NEW (operation-specific logic) |
| - | `engine/operations/instruments/` | NEW (from app/core/instruments_service.py) |
| - | `engine/operations/corporate_actions/` | NEW (from corporate_actions/) |
| - | `engine/validation/` | NEW (from app/core/) |
| - | `engine/venues/` | NEW (from utils/) |
| - | `adapters/` | NEW (from app/core/cloud_*, io/) |
| `cli/` | `cli/` | KEEP + UPDATE |
| `cli/handlers/` | `cli/handlers/` | KEEP + CONSOLIDATE (7→3 handlers) |
| `config/` | `config/` | KEEP (domain data package) |
| `corporate_actions/` | `engine/operations/corporate_actions/` | MOVE to operations/ |
| `io/` | - | DELETE (merge into adapters/) |
| `schemas/` | `schemas/` | KEEP |
| `utils/` | - | DELETE (move to engine/venues/) |
| `data/` | ? | INVESTIGATE |

### Files by Action

**KEEP (no changes)**: 15 files
- Root: `__init__.py`, `__main__.py`, `models.py`, `events.py`
- config/: All 7 files (domain data)
- schemas/: All 4 files (service-owned schemas)
- corporate_actions/: `adapter.py`, `models.py`

**KEEP (update for library usage)**: 4 files
- `config.py` - Add ConfigStore
- `cli/handlers/instrument_handler.py` - Add ConfigStore/TimeSeriesConfigStore
- `cli/handlers/live_mode_handler.py` - Add ConfigReloader
- `cli/handlers/corporate_actions_production_handler.py` - Add ConfigStore

**KEEP (update for CLI)**: 2 files
- `cli/main.py` - Add --operation flag
- `cli/parser.py` - Add --operation arg

**MOVE + RENAME**: 10 files
- `app/core/adapter_loader.py` → `engine/venue_adapter_loader.py`
- `app/core/batch_processor.py` → `engine/batch_orchestrator.py`
- `app/core/dependency_checker.py` → `engine/validation/dependency_checker.py`
- `app/core/selective_validation.py` → `engine/validation/selective_validator.py`
- `app/core/processors/*` (5 files) → `engine/processors/*`
- `utils/ccxt_service.py` → `engine/venues/ccxt_service.py`
- `utils/special_instruments.py` → `engine/venues/special_instruments.py`

**SPLIT**: 2 files (>1500 lines)
- `app/core/instrument_processing_service.py` (1228) → `engine/processors/cefi_processor.py`, `tradfi_processor.py`, `defi_processor.py`
- `app/core/instruments_service.py` (1195) → `engine/orchestrator.py` (orchestration only, ~600 lines)

**EXTRACT + MAKE THIN**: 2 files
- `app/core/cloud_instrument_storage.py` (418) → `adapters/storage_adapter.py` (<100 lines, delegate to UCS)
- `app/core/cloud_data_provider.py` (298) → `adapters/data_source_adapter.py` (<100 lines, delegate to UCS)

**MERGE**: 1 file
- `io/writer.py` (63) → Merge into `adapters/storage_adapter.py`

**DELETE**: 3 files (deprecated handlers)
- `cli/handlers/corporate_actions_backfill_handler.py` (558)
- `cli/handlers/corporate_actions_update_handler.py` (217)
- `cli/handlers/generate_date_views_handler.py` (245)

**NEW**: 3 files
- `corporate_actions/utils.py` - Extract shared utilities
- `adapters/__init__.py` - Package init
- `engine/aggregation.py` - Instrument aggregation (moved from UTDv3 scripts)

---

## Aggregation Ownership (from UTDv3)

**See:** `.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md` for full plan.

| Component | Responsibility |
|-----------|----------------|
| **instruments-service** | Own aggregation. New `--operation aggregate` (batch, daily). Delta-only by default; `--full` for schema changes. |
| **unified-trading-services** | Expose `InstrumentsDomainClient.get_aggregated_instruments(category)` — reads latest `aggregated/aggregated_instruments_*.parquet` |
| **UTDv3** | Remove aggregation scripts; data-status uses UCS `get_aggregated_instruments`. |

**Target structure:**
```
engine/
  aggregation.py          # NEW: InstrumentAggregator (from UTDv3 scripts)
  ...
cli/handlers/
  aggregate_handler.py    # NEW: --operation aggregate
```

**Schedule:** Daily batch job after main instruments run. Delta (previous day only) by default; `--redo-all` for full rebuild on schema change.

---

## Impact on Current Directories

### config/ Package (NO CHANGES)

**Current purpose**: Domain data (instrument definitions, exchange mappings, venue configs)

**After refactoring**: SAME purpose

**Why keep as package**:
- Large domain data files (instrument_definitions.py = 1126 lines) - OK for data
- Static mappings (tradfi_exchange_mappings.py, venue_config.py)
- Not runtime config (that's config.py singleton with ConfigStore)

**Relationship**:
- `config.py` (root) = Runtime config singleton (ConfigStore, hot-reloadable)
- `config/` (package) = Domain data (static, large files OK)

---

### schemas/ (NO CHANGES)

**Current purpose**: Service-owned output schemas

**After refactoring**: SAME purpose

**Why keep**:
- Service-owned schemas (per codex)
- Used by engine for validation
- No I/O logic (pure schema definitions)

**Files stay**:
- `output_schemas.py` (488 lines) - Output schema definitions
- `parquet.py` (598 lines) - Parquet schema mappings

---

### io/ (DELETE - Merge into adapters/)

**Current purpose**: Write operations (writer.py = 63 lines)

**After refactoring**: Merged into `adapters/storage_adapter.py`

**Why delete**:
- Only 1 file (writer.py)
- I/O belongs in adapters (thin wrappers)
- No need for separate io/ directory

---

### utils/ (DELETE - Move to engine/venues/)

**Current purpose**: Venue-specific utilities

**After refactoring**: Moved to `engine/venues/`

**Why move**:
- `ccxt_service.py` (838 lines) - Venue-specific business logic (not I/O)
- `special_instruments.py` (324 lines) - Venue-specific data
- Used by engine processors (not utilities)
- Belongs in engine (domain logic)

**New location**: `engine/venues/`

---

### corporate_actions/ → engine/operations/corporate_actions/ (MOVE)

**Current purpose**: Corporate actions domain logic

**After refactoring**: Move to `engine/operations/corporate_actions/`

**Why move**:
- Operation-specific logic (one of two operations: instruments, corporate_actions)
- Aligns with CLI `--operation corporate_actions`
- Keeps all operation logic in `engine/operations/`
- Consistent with `cli/handlers/` which dispatch by operation

**New location**:
```
engine/operations/corporate_actions/
  __init__.py
  adapter.py          # yfinance integration
  models.py           # Corporate actions models
  utils.py            # ✅ NEW (extract _get_tickers_from_gcs from handlers)
```

---

## Quality Gate Impact

### Files >1500 Lines (MUST SPLIT)

Current violations:
- ❌ `instrument_processing_service.py` (1228 lines) - Close to limit
- ❌ `instruments_service.py` (1195 lines) - Close to limit

After refactoring:
- ✅ All files <1500 lines
- ✅ Most files <500 lines (target)

### Circular Imports (MUST FIX)

Current violations:
- ❌ 4 corporate actions handlers import `unified_trading_services` inside functions
- ❌ Whitelisted in `QUALITY_GATE_BYPASS_AUDIT.md`

After refactoring:
- ✅ Imports at top of file
- ✅ Zero quality gate bypasses
- ✅ Shared utilities extracted

### Adapter Size (NEW REQUIREMENT)

Current:
- `cloud_instrument_storage.py` (418 lines) - Too thick
- `cloud_data_provider.py` (298 lines) - Too thick

After refactoring:
- ✅ `adapters/storage_adapter.py` (<100 lines) - Thin, delegates to UCS
- ✅ `adapters/data_source_adapter.py` (<100 lines) - Thin, delegates to UCS

---

## Import Path Changes

### Example Import Updates

```python
# Before
from instruments_service.app.core.instruments_service import InstrumentsService
from instruments_service.app.core.dependency_checker import DependencyChecker
from instruments_service.app.core.cloud_instrument_storage import CloudInstrumentStorage
from instruments_service.utils.ccxt_service import CCXTService

# After
from instruments_service.engine.orchestrator import InstrumentsOrchestrator
from instruments_service.engine.validation.dependency_checker import DependencyChecker
from instruments_service.adapters.storage_adapter import StorageAdapter
from instruments_service.engine.venues.ccxt_service import CCXTService
```

### Automated Import Rewriting

```bash
# Script to update all imports
find instruments_service -name "*.py" -type f -exec sed -i '' \
  -e 's/from instruments_service\.app\.core\.instruments_service/from instruments_service.engine.orchestrator/g' \
  -e 's/from instruments_service\.app\.core\.dependency_checker/from instruments_service.engine.validation.dependency_checker/g' \
  -e 's/from instruments_service\.app\.core\.cloud_instrument_storage/from instruments_service.adapters.storage_adapter/g' \
  -e 's/from instruments_service\.app\.core\.cloud_data_provider/from instruments_service.adapters.data_source_adapter/g' \
  -e 's/from instruments_service\.utils\.ccxt_service/from instruments_service.engine.venues.ccxt_service/g' \
  -e 's/from instruments_service\.utils\.special_instruments/from instruments_service.engine.venues.special_instruments/g' \
  {} \;

# Update tests
find tests -name "*.py" -type f -exec sed -i '' \
  -e 's/from instruments_service\.app\.core/from instruments_service.engine/g' \
  -e 's/from instruments_service\.utils/from instruments_service.engine.venues/g' \
  {} \;
```

---

## Test Impact

### Test Files to Update

All test files importing from `app.core` or `utils` need import path updates:

```bash
# Find all test files with old imports
rg "from instruments_service\.app\.core|from instruments_service\.utils" tests/
```

**Expected**: ~50+ test files need import updates

**Automated**: Use sed script above to update all at once

---

## Final Structure Summary

### Before (Current)
```
instruments_service/
  app/core/          # ❌ Mixed concerns, large files
  cli/handlers/      # ⚠️ 7 handlers (4 deprecated)
  config/            # ✅ Domain data
  corporate_actions/ # ⚠️ Should be in engine/operations/
  io/                # ❌ Single file
  schemas/           # ✅ Service-owned
  utils/             # ❌ Misnamed (venue logic)
```

### After (Target)
```
instruments_service/
  engine/            # ✅ Mode-agnostic business logic
    orchestrator.py  # Top-level (dispatches to operations)
    operations/      # ✅ Operation-specific logic
      instruments/   # Instruments operation
      corporate_actions/  # Corporate actions operation
    processors/      # Shared processors
    validation/      # Standard validation (dependency_checker)
    venues/          # Venue-specific logic (from utils/)
  adapters/          # ✅ Thin wrappers (<100 lines)
    storage_adapter.py
    data_source_adapter.py
  cli/handlers/      # ✅ 3 handlers (4 deleted)
  config/            # ✅ Domain data (unchanged)
  schemas/           # ✅ Service-owned (unchanged)
```

### Key Improvements

1. ✅ **Clear separation**: engine (logic) vs adapters (I/O)
2. ✅ **Operation-based organization**: `engine/operations/instruments/`, `engine/operations/corporate_actions/`
3. ✅ **Cloud-agnostic naming**: No "cloud" in file names
4. ✅ **File size compliance**: All files <1500 lines
5. ✅ **Thin adapters**: <100 lines, delegate to UCS
6. ✅ **Standard patterns**: dependency_checker in validation/
7. ✅ **No duplication**: Shared utilities extracted
8. ✅ **Clear naming**: orchestrator, processor, adapter (not *_service)
9. ✅ **Aligned with CLI**: `--operation` maps to `engine/operations/`

---

## Execution Checklist

### Phase 0: Test Libraries (No Structure Changes)

- [ ] Add ErrorWarningCounter to UEI
- [ ] Test ErrorWarningCounter in instruments-service (use from UEI, no structure changes)
- [ ] Add ConfigStore usage to config.py (no structure changes)
- [ ] Test ConfigStore/TimeSeriesConfigStore/ConfigReloader
- [ ] All unit tests pass
- [ ] All integration tests pass

### Phase 1: Aggregation + API Keys (see INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md)

- [ ] Fix API key violations (test_batch_cost_comparison.py, find_subgraph_ids.py)
- [ ] Add `get_aggregated_instruments` to UCS InstrumentsDomainClient
- [ ] Add `engine/aggregation.py` + `aggregate_handler.py` to instruments-service
- [ ] Add `--operation aggregate` to CLI
- [ ] Update UTDv3 data-status to use UCS `get_aggregated_instruments`
- [ ] Deprecate UTDv3 aggregation scripts

### Phase 2: Refactor Structure

- [ ] Create `engine/`, `engine/processors/`, `engine/validation/`, `engine/venues/`, `adapters/`
- [ ] Move files (10 files)
- [ ] Rename files (8 files)
- [ ] Split large files (2 files → 5 files)
- [ ] Extract thin adapters (2 files)
- [ ] Delete deprecated handlers (3 files)
- [ ] Delete io/ and utils/ directories
- [ ] Update all imports (automated script)
- [ ] Update all tests (automated script)
- [ ] Run quality gates
- [ ] Fix ALL issues (including pre-existing)
- [ ] Quality gates pass (exit code 0)

### Phase 4: Corporate Actions Consolidation

- [ ] Extract `corporate_actions/utils.py`
- [ ] Update 4 handlers to use shared utils
- [ ] Delete 3 deprecated handlers
- [ ] Fix circular imports (move imports to top)
- [ ] Remove quality gate bypasses
- [ ] Quality gates pass (exit code 0)
