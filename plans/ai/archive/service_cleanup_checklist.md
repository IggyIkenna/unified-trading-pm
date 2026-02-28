# Service Cleanup Checklist — Duplicate Implementation Removal

**Goal**: Every service is agnostic of storage, event, config, and API implementation details.
It orchestrates decisions; shared libraries own the how.

**Rule**: When a service owns its own storage wrapper, argparse CLI, raw `os.getenv`, or direct
third-party SDK imports, it has not fully migrated. Delete the duplicate — don't archive it.

**Audit date**: 2026-02-26
**Total service lines at audit**: ~313,000 (target: reduce by ~30–50k after cleanup)

---

## Status Key

- ✅ Complete
- 🔧 In progress
- ⬜ Pending
- 🔍 Review needed (domain-specific logic — may be acceptable)

---

## Services — Fully Complete

| Service | Lines | Storage | Events | Config | CLI | Status |
|---|---|---|---|---|---|---|
| ml-inference-service | ~3,761 | ✅ | ✅ | ✅ | ✅ | ✅ Done |
| risk-and-exposure-service | ~2,932 | ✅ | ✅ | ✅ | ✅ | ✅ Done |
| pnl-attribution-service | ~1,036 | ✅ | ✅ | ✅ | ✅ | ✅ Done |
| features-volatility-service | ~4,331 | ✅ | ✅ | ✅ | ✅ | ✅ Done |
| features-delta-one-service | ~12,628 | ✅ | ✅ | ✅ | ✅ | ✅ Done |
| execution-service | ~122,641 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| market-tick-data-handler | ~72,911 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| instruments-service | ~28,269 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| strategy-service | ~23,674 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| market-data-processing-service | ~18,320 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| ml-training-service | ~11,831 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| features-onchain-service | ~3,996 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| features-calendar-service | ~3,469 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |
| position-balance-monitor-service | ~3,650 | ✅ | ✅ | ✅ | ✅ | ✅ Done 2026-02-26 |

---

## Services — Cleanup Required

> All services completed 2026-02-26. Details below for reference.

### 1. execution-service (~122,641 lines) ✅ DONE 2026-02-26
**Priority: P0 — largest service, multiple duplicate implementations**

- [x] Deleted `cli/argument_parser.py` — orphaned (zero callers)
- [x] Removed `_find_credentials()` from `utils/gcs_service.py` — filesystem SA JSON scanner; ADC handles this
- [x] Removed all `GOOGLE_CLOUD_PROJECT` fallbacks
- [x] Fixed 3 hardcoded `central-element-323112` in scripts
- [x] `adapters/storage.py` confirmed thin correct pattern — kept
- Note: `utils/gcs_service.py` kept (10+ callers); internals cleaned

**Actual savings**: ~800 lines

---

### 2. market-tick-data-handler (~72,911 lines) ✅ DONE 2026-02-26

- [x] `config_utils.py` — removed redundant os.environ API key blocks; fail-loud raise instead
- [x] `config.py` — removed os.environ fallbacks; deleted `get_db_connection_string()` (no production callers)
- [x] `config_base.py` — removed `GOOGLE_CLOUD_PROJECT` AliasChoices and writes
- [x] `__main__.py` — removed `os.environ` feature flag; single unconditional `run_service_cli()` call
- [x] **Deleted `cli/parser.py`** (657 lines) — entire argparse module gone; ServiceCLI is sole entry point
- Result: 0 os.getenv calls outside tests, 0 argparse references outside tests

**Actual savings**: ~750 lines (657 from cli/parser.py alone)

---

### 3. instruments-service (~28,269 lines) ✅ DONE 2026-02-26

- [x] Removed `GOOGLE_CLOUD_PROJECT` fallbacks in `scripts/data_catalog.py`, `scripts/find_subgraph_ids.py`
- [x] `scripts/check_envio_config.py` — replaced os.environ block with `config.gcp_project_id`; moved lazy import to top
- [x] Argparse in `instruments_service/cli/parser.py` confirmed correct — feeds ServiceCLI/BaseModeHandler kwargs, not a parallel path

---

### 4. strategy-service (~23,674 lines) ✅ DONE 2026-02-26

- [x] `gcs_storage_service.py` KEPT — contains legitimate domain logic: schema validation, strategy partition paths, backtest result builders. Cloud storage correctly delegated to `get_storage_client()`
- [x] Deleted backward-compat aliases `GCSStorageService` and `get_gcs_storage_service`
- [x] Moved lazy `get_storage_client` import to top of file
- [x] Replaced 6 `Any` type annotations with specific types
- [x] Deleted dead code: `STRATEGY_BUCKET = _get_shared_bucket()` (unused in file)

---

### 5. market-data-processing-service (~18,320 lines) ✅ DONE 2026-02-26

- [x] Fixed `GOOGLE_CLOUD_PROJECT` → `GCP_PROJECT_ID` in `config.py` `is_vm` lambda
- [x] `batch_handler.py` — replaced `argparse.Namespace` with `types.SimpleNamespace` (no argparse dependency)

---

### 6. ml-training-service (~11,831 lines) ✅ DONE 2026-02-26

- [x] `scripts/e2e_mock_pipeline.py` — removed `GOOGLE_CLOUD_PROJECT` fallback from project ID chain

---

### 7. features-onchain-service (~3,996 lines) ✅ DONE 2026-02-26

- [x] `app/calculators/defillama_tvl.py` — migrated `requests.Session()` → `aiohttp.ClientSession` (fully async)
- [x] `app/calculators/fear_greed.py` — migrated `requests` → `aiohttp`
- [x] `fetch_data` abstract method made `async def` in `base.py`
- Note: `examples/` and `scripts/` retain requests (acceptable for non-production scripts)

---

### 8. features-calendar-service (~3,469 lines) ✅ DONE 2026-02-26

- [x] `economic_calendar_loader.py` — collapsed 15-line try/except+os.environ fallback to 3 lines using `config.fred_api_key` (backed by `get_secret_client`)

---

### 9. position-balance-monitor-service (~3,650 lines) ✅ DONE 2026-02-26

- [x] `position_store_gcs.py` KEPT — legitimate domain logic: account-key partitioning, position/reconciliation schemas, `_determine_account_type` classification. Cloud storage correctly delegated to `StandardizedDomainCloudService`.
- [x] Added domain adapter docstring documenting what it owns vs what it delegates

---

## Progress Tracker

| Service | Completed |
|---|---|
| execution-service | ✅ 2026-02-26 |
| market-tick-data-handler | ✅ 2026-02-26 |
| instruments-service | ✅ 2026-02-26 |
| strategy-service | ✅ 2026-02-26 |
| market-data-processing-service | ✅ 2026-02-26 |
| ml-training-service | ✅ 2026-02-26 |
| features-onchain-service | ✅ 2026-02-26 |
| features-calendar-service | ✅ 2026-02-26 |
| features-delta-one-service | ✅ pre-existing |
| features-volatility-service | ✅ pre-existing |
| ml-inference-service | ✅ pre-existing |
| risk-and-exposure-service | ✅ pre-existing |
| pnl-attribution-service | ✅ pre-existing |
| position-balance-monitor-service | ✅ 2026-02-26 |

**ALL 14 SERVICES COMPLETE**

---

## Key Deletions / What Was Actually Removed

| What | Lines | Service |
|---|---|---|
| `cli/parser.py` (pure argparse module) | 657 | market-tick-data-handler |
| `cli/argument_parser.py` (orphaned duplicate) | ~100 | execution-service |
| `_find_credentials()` SA-JSON scanner | ~80 | execution-service |
| All `GOOGLE_CLOUD_PROJECT` fallback chains | ~60 | multiple |
| 3 hardcoded `central-element-323112` blocks | ~30 | execution-service |
| Backward-compat aliases (GCSStorageService etc.) | ~20 | strategy-service |
| `get_db_connection_string()` (no callers) | ~40 | market-tick-data-handler |
| os.getenv API key blocks | ~80 | market-tick-data-handler |
| requests → aiohttp migration | ~20 | features-onchain-service |
| FRED API key os.environ block | ~12 | features-calendar-service |

**Total removed: ~1,100 lines of duplicate/deprecated code**

## Why the Count Is Lower Than 30k

The 30k+ estimate assumed complete duplication of storage, events, config infrastructure
in every service. The audit found services were MORE complete than expected — most shared
abstractions were already wired from prior work. The remaining issues were:
- Old fallback chains (GOOGLE_CLOUD_PROJECT) lingering alongside new patterns
- A few argparse modules not cleaned up after ServiceCLI was wired
- Direct os.environ API key reads not yet replaced with config fields
- requests not yet replaced with aiohttp

The REAL line-count savings will come when we reach the TESTING phase and eliminate test
duplication (conftest redundancy, fixture duplication across files) — that is a separate
effort tracked in the lobster workflow.

---

## Bloat Extraction Results (service_bloat_extraction_88f98116 — completed 2026-02-27)

A second, larger pass eliminated structural bloat (duplicate directories, library code
living inside services, embedded sub-services). Tracked in
`service_bloat_extraction_88f98116.plan.md`.

### market-tick-data-handler

| What removed | Lines |
|---|---|
| `app/` duplicate of `engine/` (identical copies) | ~16,522 |
| `cli/handlers/download_handler_original.py` (deprecated) | ~1,018 |
| Schemas moved to api-contracts (thin re-exports left) | ~1,500 net |
| Venue clients (barchart, yahoo_finance) → UMI | ~476 |
| **Total removed** | **~19,516** |

**Result**: ~30k → ~10k source lines (**~66% reduction**)

### execution-service

| What removed | Lines |
|---|---|
| `backtest/` → `engine/backtest/` migration + delete old | ~7,663 |
| `orders/` → UTEI | ~426 |
| `venues/` → UDEI/UMI | ~3,349 |
| Algorithm calculator extraction | ~374 |
| `visualizer-api/` → new repo (execution-results-api) | ~7,807 |
| Algo impl → execution-algo-library | ~14,267 |
| **Total removed** | **~33,886** |

### New Repos Created

| Repo | Lines | Contents |
|---|---|---|
| execution-results-api | ~7,807 | Extracted from execution-service visualizer-api/ |

### Libraries Enriched

- **UTEI** (unified-trade-execution-interface): order management primitives
- **UDEI** (unified-defi-execution-interface): DeFi venue adapters
- **UMI** (unified-market-interface): market data venue clients (barchart, yahoo_finance)
- **api-contracts**: databento, defi, nautilus raw provider schemas
- **execution-algo-library**: TWAP/VWAP/Almgren-Chriss algo implementations

### Test Fixes Applied (2026-02-27)

Fixed 13 test failures in execution-service caused by `signal→instruction` method renames
from the `backtest/ → engine/backtest/` migration:

| Test file | Failures fixed | Root cause |
|---|---|---|
| `test_backtest_signal_loading.py` | 7 | `_filter_signal_schedule_by_window` → `filter_instruction_schedule_by_window` (module fn); `_inject_signal_schedule_into_strategy_config` → `_inject_instruction_schedule_into_strategy_config`; `_convert_instructions_to_signals` → `InstructionLoader.convert_instructions_to_schedule`; `_load_signals_single_day` → `instruction_loader.load_instructions_single_day` |
| `test_battle_testing_regressions.py` | 2 | `_extract_instruction_benchmark_points` → `_extract_signal_benchmark_points` (in config_builder); `InstructionDrivenStrategyV3._resolve_entry_quantity` docstring → `InstructionDrivenV3Utils.resolve_entry_quantity` docstring |
| `test_order_tracker.py` | 2 | API changed: `get_instruction_orders("unknown")` and `is_instruction_complete("unknown")` now raise `KeyError` instead of returning `[]`/`False` |
| `test_preflight_checker.py` | 4 | `_generate_date_range` moved to module fn `generate_date_range` in `engine/validation/_utils.py`; `_load_venue_book_types` moved to `load_venue_book_types` in `engine/validation/_venue_book_types.py`; `check_data_configuration_compatibility` → `CatalogValidator.validate_data_config_compatibility` |

**Final result**: 33 passed, 0 failures across the 4 test files.
