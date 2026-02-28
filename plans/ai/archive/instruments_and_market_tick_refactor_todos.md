# Detailed To-Dos: Instruments-Service Finish + Market-Tick-Data-Handler Refactor

**References:**
- Service structure: [service_structure_standardization_4a4b3ff3.plan.md](service_structure_standardization_4a4b3ff3.plan.md)
- Library refactor (assumed complete): [fix_7_unified_libraries_quality_gates.plan.md](fix_7_unified_libraries_quality_gates.plan.md)
- Dependency matrix: `unified-trading-codex/05-infrastructure/unified-libraries/dependency-matrix.md`

**Import rules (post library refactor):**
- **Config:** `from unified_config_interface import UnifiedCloudConfig, BaseConfig, VenueMapping, InstrumentType, DataTypeConfig, ExchangeInstrumentConfig` (not UCS).
- **Events:** `from unified_events_interface import setup_events, log_event, ErrorWarningCounter` (not UCS).
- **Domain clients / date validation:** `from unified_domain_client import InstrumentsDomainClient, StandardizedDomainCloudService, should_skip_date, get_earliest_valid_date, get_validator, validate_timestamp_date_alignment, InstrumentKey` (not `unified_trading_services.domain`).
- **Market / adapters / API clients:** `from unified_market_interface import DataSourceMapping`; `from unified_market_interface.clients import TardisBaseClient, ...`; `from unified_market_interface.adapters.defi import ...` (UMI canonical).
- **UCS (cloud-only):** `from unified_trading_services import get_storage_client, get_secret_client, get_secret_client, CloudTarget, upload_to_storage, download_from_storage, get_instruments_bucket_for_category, get_bucket_for_category, determine_market_category, get_date_range, parse_date, generate_date_range, split_into_batches, ParquetSchemaEnforcer, GracefulShutdownHandler` (from `core.signal_handler`). No `UnifiedCloudServicesConfig`, no `setup_cloud_logging`, no domain clients, no `StandardizedDomainCloudService` from UCS once UDS is canonical for that.
- **Note:** If `StandardizedDomainCloudService` remains in UCS for a transition period, prefer migrating to UDS usage where the dependency matrix says "Domain clients canonical" (UDS). Check dependency-matrix.md for current canonical home.

---

## Part A: Finishing Instruments-Service

### A.1 Align imports with library refactor (assumed done)

- [ ] **A.1.1** Replace any `UnifiedCloudServicesConfig` / `unified_config` from UCS with `UnifiedCloudConfig` from `unified_config_interface` in [config/service_config.py](instruments-service/instruments_service/config/service_config.py) and [config/__init__.py](instruments-service/instruments_service/config/__init__.py). Config must extend UCI only.
- [ ] **A.1.2** Ensure all event usage is from UEI: `setup_events`, `log_event`, `ErrorWarningCounter` from `unified_events_interface` (already so in main.py, events.py, orchestrator; verify no `setup_cloud_logging` or UCS event re-exports).
- [ ] **A.1.3** Domain clients and date validation: use `unified_domain_client` for `InstrumentsDomainClient`, `StandardizedDomainCloudService`, `should_skip_date`, `get_earliest_valid_date`, `get_validator`, `validate_timestamp_date_alignment`. Update [adapters/data_source_adapter.py](instruments-service/instruments_service/adapters/data_source_adapter.py), [adapters/storage_adapter.py](instruments-service/instruments_service/adapters/storage_adapter.py), [engine/validation/dependency_checker.py](instruments-service/instruments_service/engine/validation/dependency_checker.py), [engine/operations/corporate_actions/utils.py](instruments-service/instruments_service/engine/operations/corporate_actions/utils.py), [cli/parser.py](instruments-service/instruments_service/cli/parser.py), [cli/handlers/corporate_actions_handler.py](instruments-service/instruments_service/cli/handlers/corporate_actions_handler.py) if they still import `StandardizedDomainCloudService` or domain helpers from UCS.
- [ ] **A.1.4** Cloud-only from UCS: keep `get_storage_client`, `get_secret_client`, `CloudTarget`, `get_instruments_bucket_for_category`, `get_bucket_for_category`, `determine_market_category`, `get_date_range`, `parse_date`, `generate_date_range`, `split_into_batches`, `upload_to_storage`; remove or replace any import of config/events/domain from UCS with UCI/UEI/UDS.
- [ ] **A.1.5** Replace `unified_trading_services.core.cloud_data_provider.InstrumentsDataProvider` in [instrument_handler.py](instruments-service/instruments_service/cli/handlers/instrument_handler.py) with UDS-based or engine-level data source if that type moves out of UCS; otherwise keep and document.

### A.2 Phase 2 quality gates (instruments-service)

- [ ] **A.2.1** Run `bash scripts/quality-gates.sh --no-fix` in instruments-service and fix all remaining failures (lazy imports, type bypasses, tests).
- [ ] **A.2.2** Ensure no file under `instruments_service/` exceeds 1,500 lines; split or trim any that do (QUALITY_GATE_BYPASS_AUDIT.md and SPLIT_SUMMARY.md already reflect instrument_processing_service split).
- [ ] **A.2.3** Update [QUALITY_GATE_BYPASS_AUDIT.md](instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md) to remove or update any bypasses that are obsolete after import alignment.

### A.3 CLI and handlers (optional / Phase 1)

- [ ] **A.3.1** When Phase 1 is executed: add `--operation` (instruments | aggregate | corporate_actions | corporate_actions_production) and `--mode` (batch | live) to [cli/parser.py](instruments-service/instruments_service/cli/parser.py); keep backward compatibility for existing `--mode` usage if needed.
- [ ] **A.3.2** Register or remove [live_mode_handler.py](instruments-service/instruments_service/cli/handlers/live_mode_handler.py): either register for `--mode live` or delete if obsolete; update [handlers/__init__.py](instruments-service/instruments_service/cli/handlers/__init__.py) accordingly.

### A.4 Plan doc and status

- [ ] **A.4.1** Update the "Current Implementation Status" table in [service_structure_standardization_4a4b3ff3.plan.md](service_structure_standardization_4a4b3ff3.plan.md) (around line 1571): set instruments-service to engine/adapters done, quality gates in progress (not "Needs refactor").

---

## Part B: Market-Tick-Data-Handler Refactor

Assume library refactor is complete: UCI (config), UEI (events), UDS (domain clients), UMI (DataSourceMapping, API clients), UCS (cloud-only).

### B.1 Imports aligned to new library structure

- [ ] **B.1.1** Config: use only `unified_config_interface` for `UnifiedCloudConfig`, `VenueMapping`, etc. In [config.py](market-tick-data-handler/market_data_tick_handler/config.py) ensure no `UnifiedCloudServicesConfig` from UCS; extend UCI `UnifiedCloudConfig`.
- [ ] **B.1.2** Events: use only `unified_events_interface` for `setup_events`, `log_event`, `ErrorWarningCounter`. In [cli/main.py](market-tick-data-handler/market_data_tick_handler/cli/main.py), [download_handler.py](market-tick-data-handler/market_data_tick_handler/cli/handlers/download_handler.py) ensure no event imports from UCS.
- [ ] **B.1.3** Domain: use only `unified_domain_client` for `InstrumentsDomainClient`, `StandardizedDomainCloudService`, `should_skip_date`, `get_earliest_valid_date`, `get_validator`, `validate_timestamp_date_alignment`. Update [download_handler.py](market-tick-data-handler/market_data_tick_handler/cli/handlers/download_handler.py), [data_orchestration_service.py](market-tick-data-handler/market_data_tick_handler/app/core/data_orchestration_service.py), [validated_uploader.py](market-tick-data-handler/market_data_tick_handler/app/core/uploaders/validated_uploader.py), and any other file importing domain/date from UCS.
- [ ] **B.1.4** Market: keep `DataSourceMapping` and API clients from `unified_market_interface` only. In [selective_validation.py](market-tick-data-handler/market_data_tick_handler/app/core/selective_validation.py) use `from unified_market_interface import DataSourceMapping` (already so). Ensure all DeFi/onchain adapters and Tardis/Databento clients import from UMI (already in data_orchestration_service, adapter_loader, venues).
- [ ] **B.1.5** UCS: use only for storage, secrets, cloud helpers: `get_storage_client`, `get_secret_client`, `CloudTarget`, `determine_market_category`, `ParquetSchemaEnforcer`, `GracefulShutdownHandler`, etc. Remove any import of config, events, or domain clients from UCS. Replace `unified_trading_services.models.*` with UMI or local schemas if those models move to another library per fix_7 plan.
- [ ] **B.1.6** [models.py](market-tick-data-handler/market_data_tick_handler/models.py): if UCS sheds `models.error`, `models.observability`, `models.schemas`, `models.validation`, update to import from the canonical library (codex/dependency-matrix) or keep local types.

### B.2 Create engine/ and move logic

- [ ] **B.2.1** Add `market_data_tick_handler/engine/` with `__init__.py`, `orchestrator.py` (top-level fetch dispatcher).
- [ ] **B.2.2** Add `engine/operations/fetch/` and move fetch orchestration entry from [data_orchestration_service.py](market-tick-data-handler/market_data_tick_handler/app/core/data_orchestration_service.py) (split file first if needed).
- [ ] **B.2.3** Move `app/core/orchestrators/*` to `engine/orchestrators/` (day, equities, external, futures, options, parallel_download); update internal imports to use engine and adapters (no direct GCS/API in engine core).
- [ ] **B.2.4** Move `app/core/validation_service.py`, `dependency_checker.py`, `selective_validation.py` to `engine/validation/`; update imports.
- [ ] **B.2.5** Move `app/core/transforms/*` (business logic only) to `engine/transforms/`; keep schema/validation usage but delegate I/O to adapters.
- [ ] **B.2.6** Move `app/venues/*` to `engine/venues/` (or keep under engine as venue-specific logic); ensure they use adapters or UMI clients for HTTP/storage only.

### B.3 Split data_orchestration_service.py and add adapters

- [ ] **B.3.1** Split [data_orchestration_service.py](market-tick-data-handler/market_data_tick_handler/app/core/data_orchestration_service.py) (2,193 lines) into modules under `engine/operations/fetch/` or `engine/orchestrators/` so no file exceeds 1,500 lines.
- [ ] **B.3.2** Add `market_data_tick_handler/adapters/` with `__init__.py`, `data_source.py` (thin: instruments/config reads via UDS/UCS), `data_sink.py` (thin: GCS write via UCS + schema validation).
- [ ] **B.3.3** Refactor engine code to use `adapters.data_source` and `adapters.data_sink` for all I/O; no direct `get_storage_client` or domain client calls inside engine orchestration (only inside adapters).

### B.4 CLI and handler

- [ ] **B.4.1** Add `--operation fetch` and `--mode batch|live` to [cli/parser.py](market-tick-data-handler/market_data_tick_handler/cli/parser.py); keep `--mode download` as alias for `--operation fetch --mode batch` during migration if desired.
- [ ] **B.4.2** Refactor [download_handler.py](market-tick-data-handler/market_data_tick_handler/cli/handlers/download_handler.py) to delegate to `engine.orchestrator` (or engine/operations/fetch) instead of calling `DataOrchestrationService` directly.
- [ ] **B.4.3** Deprecate or remove direct use of `app.core.data_orchestration_service` from the CLI path once engine is the single entry point; leave a thin compat wrapper if needed for tests or scripts.

### B.5 Tests and quality gates

- [ ] **B.5.1** Update all tests that import from `app.core` or `app.venues` to use new paths (`engine/`, `adapters/`).
- [ ] **B.5.2** Run `bash scripts/quality-gates.sh --no-fix` in market-tick-data-handler; fix file size, imports, type errors, and test failures.
- [ ] **B.5.3** Update pyproject.toml dependencies to match dependency matrix: UCS, UEI, UCI, UDS, UMI (no extra UCS re-exports relied on).

### B.6 Deployment and docs

- [ ] **B.6.1** If UTDv2/UTDv3 or scripts invoke the handler with `--mode download`, add a note or alias so `--operation fetch --mode batch` works; update deployment config when ready.
- [ ] **B.6.2** Update service README or .cursorrules to describe engine/adapters layout and import rules (UCI, UEI, UDS, UMI, UCS as above).

---

## Execution order

1. **Part A** (instruments-service): A.1.x import alignment, then A.2.x quality gates, then A.3.x/A.4.x as needed.
2. **Part B** (market-tick-data-handler): B.1.x imports first (so refactor uses correct libraries), then B.2.x/B.3.x structure and split, then B.4.x CLI, B.5.x tests and quality gates, B.6.x deployment/docs.
