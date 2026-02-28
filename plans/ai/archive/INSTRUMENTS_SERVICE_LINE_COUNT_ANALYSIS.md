# instruments-service: Line Count Analysis

## Current State (Before Refactoring)

### Source Code (excluding tests)
**Total**: ~14,500 lines of Python code

**Breakdown by directory**:
- `app/core/`: ~5,000 lines (2 files >1500 lines)
- `cli/`: ~3,500 lines (7 handlers, 3 deprecated)
- `config/`: ~2,000 lines (domain data)
- `corporate_actions/`: ~700 lines
- `schemas/`: ~1,100 lines
- `utils/`: ~1,200 lines
- `io/`: ~65 lines
- `data/`: 2 JSON files (not counted)
- Root files: ~700 lines

### Test Code
**Total**: ~2,500 lines

---

## Target State (After Refactoring)

### Expected Line Count Changes

| Change Type | Current Lines | Target Lines | Delta | Reason |
|-------------|---------------|--------------|-------|--------|
| **Split large files** | 2,423 (2 files) | 2,423 (5 files) | 0 | Same code, better organized |
| **Delete deprecated handlers** | 1,020 (3 files) | 0 | -1,020 | Remove deprecated code |
| **Extract shared utils** | 200 (duplicated) | 200 (1 file) | 0 | DRY (no duplication) |
| **Make adapters thin** | 716 (2 files) | 150 (2 files) | -566 | Delegate to UCS (remove reimplemented logic) |
| **Remove ErrorWarningCounter** | 20 | 0 | -20 | Use from UEI |
| **Add ConfigStore usage** | 0 | 100 | +100 | New feature adoption |
| **Other files** | 9,621 | 9,621 | 0 | Move/rename only |

**Total Source Code After Refactoring**: ~13,000 lines (-1,500 lines or -10%)

### Line Reduction Breakdown

1. **Delete deprecated code**: -1,020 lines
   - corporate_actions_backfill_handler.py (558)
   - corporate_actions_update_handler.py (217)
   - generate_date_views_handler.py (245)

2. **Thin adapters** (remove DRY violations): -566 lines
   - cloud_instrument_storage.py: 418 → 80 lines (remove UCS reimplementation)
   - cloud_data_provider.py: 298 → 70 lines (remove UCS reimplementation)

3. **Remove ErrorWarningCounter**: -20 lines (use from UEI)

4. **Add ConfigStore**: +100 lines (new feature)

**Net reduction**: ~1,500 lines (-10%)

---

## Directory-by-Directory Target

### engine/ (NEW - ~7,500 lines)

```
engine/
  orchestrator.py                    (~200 lines) - Top-level dispatch
  operations/
    instruments/
      orchestrator.py                (~600 lines) - From instruments_service.py (orchestration only)
      batch_orchestrator.py          (~270 lines) - From batch_processor.py
      processors/
        cefi_processor.py            (~400 lines) - Split from instrument_processing_service.py
        tradfi_processor.py          (~400 lines) - Split from instrument_processing_service.py
        defi_processor.py            (~400 lines) - Split from instrument_processing_service.py
    corporate_actions/
      adapter.py                     (~450 lines) - From corporate_actions/
      models.py                      (~210 lines) - From corporate_actions/
      utils.py                       (~200 lines) - Extracted from 4 handlers
  processors/                        # Shared processors
    canonical_key_generator.py       (~180 lines)
    ccxt_manual_fallback.py          (~180 lines)
    derived_fields_populator.py      (~235 lines)
    symbol_parser.py                 (~365 lines)
  validation/
    dependency_checker.py            (~340 lines) - STANDARDIZE
    selective_validator.py           (~133 lines)
  venues/
    ccxt_service.py                  (~840 lines) - From utils/
    special_instruments.py           (~325 lines) - From utils/
    venue_adapter_loader.py          (~155 lines) - From adapter_loader.py

Total: ~7,500 lines
```

### adapters/ (NEW - ~150 lines)

```
adapters/
  storage_adapter.py                 (~80 lines) - THIN (from cloud_instrument_storage.py + io/writer.py)
  data_source_adapter.py             (~70 lines) - THIN (from cloud_data_provider.py)

Total: ~150 lines (down from 716 lines - 79% reduction)
```

### cli/ (KEEP - ~2,500 lines)

```
cli/
  base_handler.py                    (~75 lines)
  main.py                            (~260 lines) - Update for --operation
  parser.py                          (~350 lines) - Update for --operation
  handlers/
    instrument_handler.py            (~430 lines) - Add ConfigStore
    corporate_actions_handler.py     (~550 lines) - Consolidated (from 620 + utils)
    live_mode_handler.py             (~320 lines) - Add ConfigReloader

Total: ~2,500 lines (down from 3,500 - 3 handlers deleted)
```

### config/ (KEEP - ~2,000 lines)

```
config/
  api_keys.py                        (~30 lines)
  data_type_config.py                (~70 lines)
  instrument_definitions.py          (~1,130 lines) - Domain data (large OK)
  service_config.py                  (~250 lines)
  tradfi_exchange_mappings.py        (~170 lines)
  venue_config.py                    (~90 lines)

Total: ~2,000 lines (unchanged - domain data)
```

### schemas/ (KEEP - ~1,100 lines)

```
schemas/
  output_schemas.py                  (~490 lines)
  parquet.py                         (~600 lines)

Total: ~1,100 lines (unchanged)
```

### data/ (KEEP - Static JSON)

```
data/
  sp500_tickers.json                 (Static data)
  tradfi_instruments.json            (Static data)

Total: 2 JSON files (not counted in line count)
```

### Root files (KEEP - ~700 lines)

```
__init__.py                          (~50 lines)
__main__.py                          (~10 lines)
config.py                            (~630 lines) - Add ConfigStore usage (~100 lines added)
models.py                            (~15 lines)
events.py                            (~20 lines)

Total: ~800 lines (up from 700 - ConfigStore added)
```

### Deleted Directories

- ❌ `app/` - Entire directory deleted (moved to engine/)
- ❌ `io/` - Merged into adapters/
- ❌ `utils/` - Moved to engine/venues/
- ❌ `corporate_actions/` - Moved to engine/operations/corporate_actions/

---

## Final Structure with Line Counts

```
instruments_service/                           TOTAL: ~13,000 lines (-1,500 from current)
├── __init__.py                                (~50)
├── __main__.py                                (~10)
├── config.py                                  (~730) +100 for ConfigStore
├── models.py                                  (~15)
├── events.py                                  (~20)
├── engine/                                    (~7,500)
│   ├── orchestrator.py                        (~200)
│   ├── operations/                            (~2,130)
│   │   ├── instruments/                       (~1,670)
│   │   └── corporate_actions/                 (~860)
│   ├── processors/                            (~960)
│   ├── validation/                            (~473)
│   └── venues/                                (~1,320)
├── adapters/                                  (~150) -566 from current
│   ├── storage_adapter.py                     (~80)
│   └── data_source_adapter.py                 (~70)
├── cli/                                       (~2,500) -1,000 from current
│   ├── main.py, parser.py, base_handler.py    (~685)
│   └── handlers/                              (~1,800) 3 handlers (4 deleted)
├── config/                                    (~2,000) unchanged
├── schemas/                                   (~1,100) unchanged
└── data/                                      (2 JSON files)
```

---

## Where data/ and io/ End Up

### data/ Directory
**Current**: `instruments_service/data/`
- sp500_tickers.json
- tradfi_instruments.json

**After refactoring**: ✅ **STAYS** at `instruments_service/data/`
- Static domain data (not code)
- Used by corporate_actions operation
- No changes needed

### io/ Directory
**Current**: `instruments_service/io/`
- writer.py (63 lines) - Extends BaseGCSWriter from UCS

**After refactoring**: ❌ **DELETED** (merged into adapters/)
- `io/writer.py` → `adapters/storage_adapter.py`
- InstrumentWriter class becomes part of StorageAdapter
- Only 1 file, no need for separate directory

**Merged code**:
```python
# adapters/storage_adapter.py (~80 lines total)
from unified_trading_services.io import BaseGCSWriter

class StorageAdapter(BaseGCSWriter):
    """Thin wrapper - extends UCS BaseGCSWriter.
    
    Combines functionality from:
    - cloud_instrument_storage.py (I/O operations)
    - io/writer.py (path building)
    """
    
    def __init__(self, category: str, dry_run: bool = False):
        # Delegate to UCS
        super().__init__(bucket_name=bucket, schema=INSTRUMENTS_SCHEMA, ...)
    
    def build_path(self, **kwargs) -> str:
        # From io/writer.py
        return f"by_date/day={date}/instrument_id={id}.parquet"
```

---

## Summary

### Line Count
- **Before**: ~14,500 lines
- **After**: ~13,000 lines
- **Reduction**: -1,500 lines (-10%)

### Where Everything Goes

| Current Directory | Target Directory | Action | Lines |
|-------------------|------------------|--------|-------|
| `app/core/` | `engine/` | MOVE + RESTRUCTURE | ~5,000 |
| `app/core/processors/` | `engine/processors/` | MOVE | ~960 |
| `corporate_actions/` | `engine/operations/corporate_actions/` | MOVE | ~860 |
| `utils/` | `engine/venues/` | MOVE | ~1,320 |
| `io/` | `adapters/` | MERGE | 63 → 80 |
| `cli/` | `cli/` | KEEP + UPDATE | ~2,500 |
| `config/` | `config/` | KEEP | ~2,000 |
| `schemas/` | `schemas/` | KEEP | ~1,100 |
| `data/` | `data/` | KEEP | 2 JSON files |

### Key Points

1. ✅ **data/ stays** - Static domain data (JSON files)
2. ❌ **io/ deleted** - Merged into adapters/ (only 1 file)
3. ✅ **10% code reduction** - Delete deprecated, thin adapters, DRY
4. ✅ **Better organized** - Clear hierarchy (engine/operations/, engine/processors/, etc.)
5. ✅ **All files <1500 lines** - Quality gates will pass
