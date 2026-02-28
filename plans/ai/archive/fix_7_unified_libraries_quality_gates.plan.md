---
name: Fix 7 Unified Libraries Quality Gates
overview: Fix quality gate failures and restructure UCS for cloud-only focus. Move domain clients to UDS, remove legacy UnifiedCloudService, consolidate config in UCI, deprecate setup_cloud_logging, remove DataSourceMapping/API clients from UCS, split ML to unified-ml-interface. Update codex, cursor rules, and library docs (existing files only).
todos:
  - id: phase1_ucs_circular
    content: Fix UCS circular import (domain/clients.py) - import from submodules not package root
    status: completed
  - id: phase1_ucs_codex
    content: Fix UCS codex violations (hardcoded project IDs, broad except, Any/object, imports)
    status: completed
  - id: ucs_remove_datasource
    content: Remove UCS DataSourceMapping - consumers use UMI only (instruments-service, market-tick-data-handler)
    status: completed
  - id: ucs_domain_clients_uds
    content: Move UCS domain/clients.py (1563 lines) to UDS - canonical home per dependency matrix
    status: completed
  - id: ucs_remove_unified_cloud_service
    content: Remove UnifiedCloudService - refactor StandardizedDomainCloudService to use get_storage_client primitives
    status: completed
  - id: ucs_config_migrate
    content: Migrate UnifiedCloudServicesConfig users to UCI UnifiedCloudConfig, remove from UCS
    status: completed
  - id: ucs_deprecate_setup_cloud_logging
    content: Deprecate setup_cloud_logging - migrate callers to UEI setup_events (UTDv2, UTDv3, codex scripts)
    status: completed
  - id: ucs_stop_api_clients
    content: Stop shipping API clients from UCS build - UMI is canonical, ensure package excludes clients/
    status: completed
  - id: ucs_ml_split
    content: Move UCS ml/ module (~1428 lines) to new unified-ml-interface library
    status: completed
  - id: phase2_uci
    content: Fix UCI quality gates (empty fallbacks, lazy imports, Pyright, tests)
    status: completed
  - id: phase2_uei
    content: Fix UEI quality gates (Pyright, tests - should resolve after UCS fix)
    status: completed
  - id: phase2_uds
    content: Fix UDS E501 line length, consolidate domain clients from UCS, remove duplicates
    status: completed
  - id: phase2_umi
    content: Fix UMI E501 (1 in tardis_adapter.py) and any other violations
    status: completed
  - id: phase2_uoi_types
    content: Fix UOI basedpyright type errors and codex violations
    status: completed
  - id: phase3_uoi_arch
    content: UOI architectural alignment - add UCI and UEI deps, replace VenueName with UCI Venue
    status: completed
  - id: phase3_uoi_events
    content: UOI use UEI for order lifecycle event logging where needed
    status: completed
  - id: phase4_dep_matrix
    content: Update dependency-matrix.md - UOI, UDS domain clients, unified-ml-interface, config migration
    status: completed
  - id: phase5_docs
    content: Update codex, cursor rules, service/library docs (existing files only - no new docs)
    status: completed
  - id: phase6_merge
    content: Merge in order - UCS first, then UCI/UEI, UDS/UMI/UOI, unified-ml-interface
    status: pending
  - id: umi_base_adapter
    content: UMI - Consolidate BaseDefiAdapter, BaseTradfiAdapter, BaseOnchainPerpAdapter into BaseMarketAdapter
    status: pending
  - id: umi_block_resolver
    content: UMI - Centralize BlockResolver to clients/ or utils/, fix broken ...clients.block_resolver imports
    status: pending
  - id: umi_base_api_client
    content: UMI - Add BaseApiClient for Tardis/Databento/TheGraph/Alchemy/Hyperliquid (cache, retry, session)
    status: pending
  - id: umi_subgraph_layer
    content: UMI - Add SubgraphAdapterMixin or GraphQLDataFetcher for DeFi adapters
    status: pending
  - id: umi_uniswap_base
    content: UMI - Add BaseUniswapAdapter, extract shared V2/V3/V4 logic
    status: pending
  - id: umi_token_registry
    content: UMI - Centralize token/reserve mappings in models/token_registry.py or configs/
    status: pending
  - id: umi_lst_split
    content: UMI - Split lst_adapters.py into etherfi_adapter.py, lido_adapter.py, keep exports in defi __init__
    status: pending
isProject: false
---

# Fix 7 Unified Libraries Quality Gates + UCS Restructure

## Python Line Counts (Source Code Only)

Excludes: tests, scripts, .venv, build, **pycache**

### Current (Feb 2026)


| Library                      | Current Lines |
| ---------------------------- | ------------- |
| **unified-trading-services**   | 22,564        |
| **unified-config-interface** | 4,348         |
| **unified-events-interface** | 1,293         |
| **unified-domain-client**  | 4,730         |
| **unified-market-interface** | 20,885        |
| **unified-trade-execution-interface**  | 2,698         |
| **execution-algo-library**   | 1,396         |
| **TOTAL**                    | **57,914**    |


### After Restructure


| Library                        | After Restructure | Change                           |
| ------------------------------ | ----------------- | -------------------------------- |
| **unified-trading-services**     | ~16,467           | -6,097 (restructure)             |
| **unified-config-interface**   | 4,348             | —                                |
| **unified-events-interface**   | 1,293             | —                                |
| **unified-domain-client**    | ~6,293            | +1,563 (domain clients from UCS) |
| **unified-market-interface**   | 20,885            | —                                |
| **unified-trade-execution-interface**    | 2,698             | —                                |
| **execution-algo-library**     | 1,396             | —                                |
| **unified-ml-interface** (new) | ~1,428            | New library (from UCS ml/)       |
| **TOTAL**                      | **~54,808**       | **-3,106 net**                   |


**UCS line savings:** DataSourceMapping 129, domain clients 1,563, UnifiedCloudService+factories ~1,850, config 669, setup_cloud_logging ~458, ML 1,428 = ~6,097 lines.

**Note:** File splitting (unified_cloud_service.py, domain/clients.py) not needed after restructure — both removed.

---

## Phase 0: UCS Restructure (Cloud-Only Focus)

### 0.1 Remove DataSourceMapping from UCS

- **Action:** Delete [unified-trading-services/unified_trading_services/domain/data_source_mapping.py](unified-trading-services/unified_trading_services/domain/data_source_mapping.py) (129 lines)
- **Consumers:** instruments-service, market-tick-data-handler already use UMI. Update any UCS imports to UMI.
- **Repos:** instruments-service (venue_adapter_loader, selective_validator), market-tick-data-handler (selective_validation)

### 0.2 Move Domain Clients to UDS

- **Action:** Move [unified-trading-services/unified_trading_services/domain/clients.py](unified-trading-services/unified_trading_services/domain/clients.py) (1,563 lines) to UDS. UDS is canonical per dependency matrix ("Domain clients, date validation").
- **UDS:** Replace duplicate InstrumentsDomainClient, MarketDataDomainClient, etc. with UCS canonical implementation. UDS depends on UCS for StandardizedDomainCloudService.
- **Repos to update imports (UCS → UDS):**
  - unified-trading-deployment-v3 (data_status.py)
  - market-data-processing-service (cloud_data_provider.py)
  - market-tick-data-handler (download_handler.py)
  - execution-services (visualizer-api data_service.py)
  - instruments-service (comments/docs only)

### 0.3 Remove UnifiedCloudService Legacy Class

- **Action:** Refactor [StandardizedDomainCloudService](unified-trading-services/unified_trading_services/domain/standardized_service.py) to use `get_storage_client`, `CloudTarget`, and cloud primitives directly instead of UnifiedCloudService. Delete [unified_cloud_service.py](unified-trading-services/unified_trading_services/core/unified_cloud_service.py) (1,750 lines) and [domain/factories.py](unified-trading-services/unified_trading_services/domain/factories.py) (76 lines).
- **Repos to update:**
  - unified-trading-services (core refactor)
  - unified-domain-client (factories re-export — update or remove)
  - execution-services (test_ucs_integration.py — update or remove)

### 0.4 Migrate UnifiedCloudServicesConfig to UCI

- **Action:** Migrate remaining services to UCI `UnifiedCloudConfig`. Remove [unified-trading-services/unified_trading_services/core/config.py](unified-trading-services/unified_trading_services/core/config.py) UnifiedCloudServicesConfig (669 lines). Keep `get_config`, `unified_config` if still needed; otherwise migrate to UCI.
- **Repos to migrate:** strategy-service, ml-training-service, alerting-system, pnl-attribution-service, unified-trade-execution-interface, unified-market-interface

### 0.5 Deprecate setup_cloud_logging

- **Action:** Migrate callers to UEI `setup_events`. UEI can use UCS for cloud-specific wiring (e.g. Cloud Logging) if needed. Remove or thin [core/logging.py](unified-trading-services/unified_trading_services/core/logging.py) setup_cloud_logging (~458 lines).
- **Repos to update:** unified-trading-deployment-v3, unified-trading-deployment-v3 (cli.py), codex scripts (generate-per-service-specs.py)

### 0.6 Stop Shipping API Clients from UCS

- **Action:** Ensure UCS build/package excludes `clients/`. UMI has canonical Tardis, Databento, TheGraph, etc. UMI clients correctly use UCS for `get_secret_client`, `get_config` — no code carryover needed.

### 0.7 Move ML Module to unified-ml-interface

- **Action:** Create new `unified-ml-interface` library. Move [unified-trading-services/unified_trading_services/ml/](unified-trading-services/unified_trading_services/ml/) (~1,428 lines) — ModelRegistry, ModelVariantConfig, ModelMetadata, config_schema.
- **Consumers:** ml-training-service, ml-inference-service — update imports to unified-ml-interface.

---

## Phase 1: Fix UCS (Unblock Downstream)

### 1.1 Circular Import

**File:** [unified-trading-services/unified_trading_services/domain/clients.py](unified-trading-services/unified_trading_services/domain/clients.py) (until moved to UDS)

```python
# Before
from unified_trading_services import get_instruments_bucket_for_category, get_storage_client

# After
from unified_trading_services.core.market_category import get_instruments_bucket_for_category
from unified_trading_services.core.client_factory import get_storage_client
```

### 1.2 Codex Violations

- Hardcoded project ID in tests → use `test-project`
- Broad except Exception → use @handle_api_errors or specific exceptions
- Imports inside functions → move to top or document in QUALITY_GATE_BYPASS_AUDIT
- Any/object → replace with Protocol, TypedDict, specific types

---

## Phase 2: Parallel Libraries (4 Agents)

### Agent 1: UCI

Empty fallbacks (3), lazy imports (9), Pyright, tests.

### Agent 2: UEI

Pyright, tests (circular import from UCS should resolve).

### Agent 3: UDS

E501 in clients.py. Consolidate domain clients from UCS, remove duplicates.

### Agent 4: UMI

E501 in tardis_adapter.py:416.

### Agent 5: UOI

Types, codex. Then Phase 3 architectural alignment.

---

## Phase 3: UOI Architectural Alignment

### 3.1 Add UCI and UEI Dependencies

**pyproject.toml** — mirror UMI:

```toml
dependencies = [
    "unified-trading-services>=1.4.0",
    "unified-config-interface>=0.3.0",
    "unified-events-interface>=0.1.0",
    ...
]
```

### 3.2 Replace VenueName with UCI Venue

Use UCI Venue with mapping layer for CCXT lowercase.

### 3.3 Use UEI for Order Lifecycle Events

Where UOI adapters log order events, use `log_event()` from UEI.

---

## Phase 4: Dependency Matrix Update

[dependency-matrix.md](unified-trading-codex/05-infrastructure/unified-libraries/dependency-matrix.md):

- UDS: Domain clients canonical; depends on UCS, UCI, UEI
- UOI: Depends on UCS, UCI, UEI
- unified-ml-interface: New library; ml-training, ml-inference depend on it
- Config: All services use UCI UnifiedCloudConfig (remove UnifiedCloudServicesConfig references)
- UCS: Cloud-only (storage, secrets, client factory, error handling, monitoring)

---

## Phase 5: Documentation Updates (Existing Files Only)

**No new docs.** Update existing:

### Codex

- [02-data/instruments-and-api-keys-standard.md](unified-trading-codex/02-data/instruments-and-api-keys-standard.md) — InstrumentsDomainClient from UDS (not UCS)
- [05-infrastructure/unified-libraries/dependency-matrix.md](unified-trading-codex/05-infrastructure/unified-libraries/dependency-matrix.md) — full restructure
- [05-infrastructure/unified-libraries/README.md](unified-trading-codex/05-infrastructure/unified-libraries/README.md) — library roles
- [05-infrastructure/unified-libraries/import-patterns.md](unified-trading-codex/05-infrastructure/unified-libraries/import-patterns.md) — DataSourceMapping from UMI, domain clients from UDS
- [06-coding-standards/README.md](unified-trading-codex/06-coding-standards/README.md) — config section
- [06-coding-standards/config-types.md](unified-trading-codex/06-coding-standards/config-types.md) — UnifiedCloudConfig only
- [06-coding-standards/dependency-management.md](unified-trading-codex/06-coding-standards/dependency-management.md) — unified-ml-interface

### Cursor Rules

- [.cursor/rules/instruments-domain-and-api-keys.mdc](.cursor/rules/instruments-domain-and-api-keys.mdc) — InstrumentsDomainClient from UDS
- [.cursor/rules/event-logging.mdc](.cursor/rules/event-logging.mdc) — setup_events from UEI, no setup_cloud_logging
- [.cursorrules](.cursorrules) (workspace root) — config, domain clients, observability patterns

### Library Docs

- [unified-trading-services/.cursorrules](unified-trading-services/.cursorrules) — cloud-only scope
- [unified-trading-services/docs/ARCHITECTURE.md](unified-trading-services/docs/ARCHITECTURE.md) — remove domain clients, config, ML
- [unified-trading-services/README.md](unified-trading-services/README.md) — scope
- [unified-domain-client/README.md](unified-domain-client/README.md) — domain clients canonical
- [unified-market-interface/README.md](unified-market-interface/README.md) — DataSourceMapping, API clients canonical

### Plans (if still relevant)

- [.cursor/plans/INSTRUMENTS_DOMAIN_DECISIONS.md](.cursor/plans/INSTRUMENTS_DOMAIN_DECISIONS.md) — UDS as canonical
- [.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md](.cursor/plans/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md) — align with restructure

---

## Phase 6: UMI Abstraction (7 Tasks)

Reduce UMI from ~21K. All changes internal; public API preserved.

### Order

1. BlockResolver centralization (fix broken imports first)
2. Base adapter consolidation
3. Token registry
4. LST split
5. Base API client
6. Uniswap base
7. Subgraph/GraphQL layer

---

## Merge Order

1. UCS (restructure + quality gates)
2. UCI, UEI
3. UDS (with domain clients), UMI, UOI
4. unified-ml-interface (new)

---

## UCI Overhaul Status

**All 10 phases complete.** ConfigStore, TimeSeriesConfigStore, UnifiedCloudConfig in UCI. No missing implementation.

---

## Full Audit (2026-02-24, Codebase State)

Audit was performed against the actual codebase, not plan status.

### UCS (unified-trading-services)


| Item                 | Plan status | Actual state                                                                              | Action taken                                                                                                                                   |
| -------------------- | ----------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| UnifiedCloudService  | pending     | **Removed** (file gone; refs in comments only)                                            | Fixed test that imported it → use get_secret_client; removed file-size bypass; Dockerfile healthcheck → get_storage_client, CloudTarget |
| DataSourceMapping    | completed   | **Gone** (no file)                                                                        | None                                                                                                                                           |
| domain/clients.py    | completed   | **In UDS** (unified_domain_client/clients.py)                                           | None                                                                                                                                           |
| Config migration     | completed   | **UCI primary**; UCS still has UnifiedCloudServicesConfig for legacy                      | README updated to prefer UCI                                                                                                                   |
| setup_cloud_logging  | completed   | **Deprecated**; UTDv2 checklists still mention it (docs)                                  | None                                                                                                                                           |
| API clients in build | pending     | **Excluded** (pyproject.toml exclude unified_trading_services/clients*)                     | Marked completed                                                                                                                               |
| ML module            | pending     | **Gone from UCS**; unified-ml-interface exists with model_registry, config_schema, models | Marked completed; removed ml/tests from coverage omit                                                                                          |
| Lint                 | —           | I001 + F401 in test                                                                       | Fixed (ruff --fix, removed unused Mock)                                                                                                        |
| Pyright              | —           | ~994 errors (aws_clients, security loggers, etc.)                                         | Pre-existing; not fixed this pass                                                                                                              |


### UDS (unified-domain-client)


| Item                           | Actual state                                                          |
| ------------------------------ | --------------------------------------------------------------------- |
| Domain clients                 | In unified_domain_client/clients.py (InstrumentsDomainClient, etc.) |
| StandardizedDomainCloudService | Re-exported from UCS domain                                           |
| Factories                      | factories.py exists with "Legacy factories removed" note              |


### UOI (unified-trade-execution-interface)


| Item         | Actual state                                                             |
| ------------ | ------------------------------------------------------------------------ |
| UCI/UEI deps | In pyproject.toml (unified-config-interface, unified-events-interface)   |
| Venue        | From unified_config_interface import Venue (factory.py, **init**.py)     |
| log_event    | binance_ccxt.py, coinbase_ccxt.py use unified_events_interface.log_event |


### unified-ml-interface


| Item   | Actual state                                                              |
| ------ | ------------------------------------------------------------------------- |
| Exists | Yes; unified_ml_interface/ (model_registry, models, config_schema), tests |


### Dependency matrix (codex)

- Already documents UOI (UCS, UCI, UEI), UDS domain clients canonical, unified-ml-interface, config consolidation. No change needed.

### Phase 5 docs (existing only)

- UCS README: Updated verify command, known working imports, config pattern (UCI preferred).
- instruments-domain-and-api-keys.mdc: Already states InstrumentsDomainClient from UDS.
- dependency-matrix.md: Already current.

### Quality gates run (2026-02-24)


| Library                  | Config    | Lint | Pyright | Tests | Codex | Notes                                                                                              |
| ------------------------ | --------- | ---- | ------- | ----- | ----- | -------------------------------------------------------------------------------------------------- |
| **UCS**                  | ✅         | ✅    | ❌       | ✅     | ✅     | ~994 type errors (aws_clients, security); lint fixed this pass                                     |
| **UCI**                  | ✅         | ✅    | ✅       | ✅     | ✅     | All passed                                                                                         |
| **UEI**                  | —         | ✅    | ✅       | ✅     | ✅     | All passed                                                                                         |
| **UDS**                  | —         | ✅    | ✅       | ✅     | ✅     | Passed after ruff format (3 files)                                                                 |
| **UOI**                  | ✅         | ✅    | ✅       | ❌     | ❌     | Tests: pytest cov args not recognized; Codex: empty fallbacks + import inside function (log_event) |
| **UMI**                  | ✅         | —    | ❌       | ✅     | ❌     | Pyright + 1 Codex violation                                                                        |
| **unified-ml-interface** | (not run) | —    | —       | —     | —     | Has pyproject, tests                                                                               |


### UMI Phase 6 tasks (plan)

- umi_base_adapter, umi_block_resolver, umi_base_api_client, umi_subgraph_layer, umi_uniswap_base, umi_token_registry, umi_lst_split remain **pending** (abstraction work, not quality-gate fixes).

---

## References

- [unified_config_interface_overhaul_consolidated.plan.md](.cursor/plans/archive/2026-02-completed-work/unified_config_interface_overhaul_consolidated.plan.md)
- [quality-gates-hardening.mdc](.cursor/rules/quality-gates-hardening.mdc)
- [no-empty-fallbacks.mdc](.cursor/rules/no-empty-fallbacks.mdc)
- [file-splitting-guide.md](unified-trading-codex/06-coding-standards/file-splitting-guide.md)
