---
title: "UTL Import Consolidation — Services Import from UTL, Not Split Libraries"
created: 2026-03-25
status: done
locked_by: live-defi-rollout
locked_since: 2026-03-25
priority: P0
---

# UTL Import Consolidation

## Context

Services are importing directly from split libraries (unified-config-interface, unified-cloud-interface,
unified-events-interface, etc.) instead of through unified-trading-library (UTL). This session's audit found 101 symbols
across 18 services that are imported from split libraries but not re-exported by UTL.

The original refactor consolidated imports through UTL. Adding transitive deps back to pyproject.toml undid that.

## Architectural Rules

### Services MUST import from UTL for common infrastructure:

- Config: `from unified_trading_library import UnifiedCloudConfig, InstrumentDomainConfig, ...`
- Cloud: `from unified_trading_library import get_storage_client, get_data_sink, ...`
- Events: `from unified_trading_library import log_event, setup_events, ...`
- Domain: `from unified_trading_library import DomainConfigReloader, DataCompletionChecker, ...`

### Services MAY import directly from domain-specific interfaces they implement:

| Service                          | Allowed Direct Deps (beyond UTL/UAC/UIC)                                                                                                                                                                                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service              | unified-reference-data-interface                                                                                                                                                                                                                                              |
| market-tick-data-service         | unified-market-interface                                                                                                                                                                                                                                                      |
| market-data-processing-service   | unified-market-interface                                                                                                                                                                                                                                                      |
| features-sports-service          | unified-market-interface, unified-features-interface (NOTE: unified-sports-reference-interface merged into URDI sports/, unified-feature-calculator-library merged into UTL feature_calculator/, unified-feature-orchestration-library merged into UTL feature_service_base/) |
| features-\*-service (all)        | unified-features-interface (NOTE: unified-feature-calculator-library merged into UTL feature_calculator/)                                                                                                                                                                     |
| execution-service                | (NOTE: unified-trade-execution-interface, unified-defi-execution-interface, unified-sports-execution-interface, execution-algo-library, matching-engine-library all merged into execution-service as subpackages)                                                             |
| ml-inference-service             | (NOTE: unified-ml-interface merged into UTL ml/)                                                                                                                                                                                                                              |
| ml-training-service              | (NOTE: unified-ml-interface merged into UTL ml/, unified-feature-calculator-library merged into UTL feature_calculator/)                                                                                                                                                      |
| position-balance-monitor-service | (NOTE: unified-position-interface merged into position-balance-monitor-service as subpackage)                                                                                                                                                                                 |
| strategy-service                 | (NOTE: unified-domain-client merged into UTL domain_client/)                                                                                                                                                                                                                  |
| deployment-service               | ALL (exempt — bootstrap exception)                                                                                                                                                                                                                                            |

### NEVER allowed as direct deps in services:

- `unified-config-interface` → use `from unified_trading_library import UnifiedCloudConfig, ...`
- `unified-cloud-interface` → use `from unified_trading_library import get_storage_client, ...`
- `unified-events-interface` → use `from unified_trading_library import log_event, setup_events, ...`
- `unified-domain-client` (now merged into UTL domain_client/) → use `from unified_trading_library import ...`

## Symbol Audit Results (2026-03-25)

### ~40 common symbols that UTL should re-export (services should NOT import directly):

**unified_config_interface** (13 missing from UTL): UnifiedCloudConfig, InstrumentDomainConfig, StrategyDomainConfig,
VenueDomainConfig, AlertRuleDomainConfig, RateLimitDomainConfig, RiskDomainConfig, FeatureFlagDomainConfig,
ClientDomainConfig, MLTrainingConfig, TickerUniverseConfig, TimeSeriesConfigStore, ConfigStoreError,
INSTRUMENT_TYPE_FOLDER_MAP, VENUE_CATEGORY_MAP, CONFIG_SCHEMA, validate_config_file

**unified_cloud_interface** (14 missing from UTL): get_data_source, get_event_bus, get_pubsub_client, get_queue_client,
get_analytics_client, EventBus, PubSubClient, QueueClient, StorageBlob, BlobMetadata, StorageDataSource,
AnalyticsClient, PubSubSubscriberClient, PubSubReceivedMessage, CredentialsRegistry, create_s2s_auth_dependency

**unified_events_interface** (36 missing — mostly event name constants): All KILL*SWITCH*\_, ORDER\__, POSITION*\*,
PORTFOLIO*_, BALANCE\__, DEVIATION*\*, PNL*_, CIRCUIT*BREAKER*\_, REGIME\_\*, TRADE_REPORTED_MIFID, etc. +
CoordinationEvent, ComplianceEventPayload, JSONDict

### ~60 domain-specific symbols (remain as direct deps — NOT added to UTL):

Feature calculator math, ML types, position types, market adapters, execution adapters, URDI adapters

## Execution Phases

### Phase 0 — Whitelist deployment-service (DONE)

- [x] [AGENT] P0. Add deployment-service to TIER_EXEMPT_REPOS in fix-internal-dependency-alignment.py
- [x] [AGENT] P0. Plan filed with detailed symbol audit

### Phase 1 — Add ~40 common re-exports to UTL **init**.py (DONE)

- [x] [AGENT] P0. Add UnifiedCloudConfig, InstrumentDomainConfig, and all domain config classes
- [x] [AGENT] P0. Add get_data_source, get_event_bus, get_pubsub_client, and all cloud clients
- [x] [AGENT] P0. Add all event name constants (KILL*SWITCH*\_, ORDER\_\_, etc.)
- [x] [AGENT] P0. Add CoordinationEvent, ComplianceEventPayload, ConfigStoreError, etc.
- [x] [AGENT] P0. Verify: `python3 -c "from unified_trading_library import UnifiedCloudConfig; print('OK')"` — PASS

### Phase 2 — Change service imports to UTL (DONE — 638 import lines across 21 services + 2 APIs)

- [x] [AGENT] P0. For each service: `from unified_config_interface import X` → `from unified_trading_library import X`
- [x] [AGENT] P0. Same for unified_cloud_interface → UTL
- [x] [AGENT] P0. Same for unified_events_interface → UTL (event constants + helpers)
- [x] [AGENT] P0. Leave domain-specific imports as-is (URDI, UMI, UTEI, etc.)
- [x] [AGENT] P0. Run import smoke test per service

### Phase 3 — Remove disallowed deps from pyproject.toml (DONE)

- [x] [AGENT] P0. Remove unified-config-interface from all services' [project.dependencies] + [tool.uv.sources]
- [x] [AGENT] P0. Remove unified-cloud-interface from all services
- [x] [AGENT] P0. Remove unified-events-interface from all services
- [x] [AGENT] P0. Remove unified-domain-client from all services (now merged into UTL domain_client/)
- [x] [AGENT] P0. Keep domain-specific deps only for services that need them (per table above)

### Phase 4 — Update validate-import-deps.py enforcement (DONE)

- [x] [AGENT] P0. Change script to FLAG direct imports from config/cloud/events as violations
- [x] [AGENT] P0. Add per-service allowed direct dep whitelist (from table above)
- [x] [AGENT] P0. deployment-service fully exempt

### Phase 5 — Strip manifest + verify alignment (DONE)

- [x] [AGENT] P0. Re-run manifest stripping of transitive deps — only deployment-service needs additions (exempt)
- [x] [AGENT] P0. validate-import-deps.py passes clean
- [x] [AGENT] P0. Success criteria verified: 0 banned imports across all services

## Success Criteria

- `from unified_config_interface import X` appears in ZERO services (except deployment-service)
- `from unified_cloud_interface import X` appears in ZERO services (except deployment-service)
- `from unified_events_interface import X` appears in ZERO services (except deployment-service)
- Each service's pyproject.toml has max 3-5 internal deps (UTL + UAC + UIC + domain-specific)
- Version alignment passes with 0 misalignments
- All services pass setup smoke test
