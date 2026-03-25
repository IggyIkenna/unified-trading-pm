---
title: "UTL Import Consolidation — Services Import from UTL, Not Split Libraries"
created: 2026-03-25
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-25
priority: P0
---

# UTL Import Consolidation

## Context

Services are importing directly from split libraries (unified-config-interface, unified-cloud-interface,
unified-events-interface, etc.) instead of through unified-trading-library (UTL). This session's audit found
101 symbols across 18 services that are imported from split libraries but not re-exported by UTL.

The original refactor consolidated imports through UTL. Adding transitive deps back to pyproject.toml undid that.

## Architectural Rules

### Services MUST import from UTL for common infrastructure:
- Config: `from unified_trading_library import UnifiedCloudConfig, InstrumentDomainConfig, ...`
- Cloud: `from unified_trading_library import get_storage_client, get_data_sink, ...`
- Events: `from unified_trading_library import log_event, setup_events, ...`
- Domain: `from unified_trading_library import DomainConfigReloader, DataCompletionChecker, ...`

### Services MAY import directly from domain-specific interfaces they implement:
| Service | Allowed Direct Deps (beyond UTL/UAC/UIC) |
|---------|----------------------------------------|
| instruments-service | unified-reference-data-interface |
| market-tick-data-service | unified-market-interface |
| market-data-processing-service | unified-market-interface |
| features-sports-service | unified-market-interface, unified-sports-reference-interface, unified-feature-calculator-library, unified-features-interface, unified-feature-orchestration-library |
| features-*-service (all) | unified-feature-calculator-library, unified-features-interface |
| execution-service | unified-trade-execution-interface, unified-defi-execution-interface, unified-sports-execution-interface, execution-algo-library, matching-engine-library |
| ml-inference-service | unified-ml-interface |
| ml-training-service | unified-ml-interface, unified-feature-calculator-library |
| position-balance-monitor-service | unified-position-interface |
| strategy-service | unified-domain-client |
| deployment-service | ALL (exempt — bootstrap exception) |

### NEVER allowed as direct deps in services:
- `unified-config-interface` → use `from unified_trading_library import UnifiedCloudConfig, ...`
- `unified-cloud-interface` → use `from unified_trading_library import get_storage_client, ...`
- `unified-events-interface` → use `from unified_trading_library import log_event, setup_events, ...`
- `unified-domain-client` → use `from unified_trading_library import ...` (except strategy-service)

## Symbol Audit Results (2026-03-25)

### ~40 common symbols that UTL should re-export (services should NOT import directly):

**unified_config_interface** (13 missing from UTL):
UnifiedCloudConfig, InstrumentDomainConfig, StrategyDomainConfig, VenueDomainConfig,
AlertRuleDomainConfig, RateLimitDomainConfig, RiskDomainConfig, FeatureFlagDomainConfig,
ClientDomainConfig, MLTrainingConfig, TickerUniverseConfig, TimeSeriesConfigStore,
ConfigStoreError, INSTRUMENT_TYPE_FOLDER_MAP, VENUE_CATEGORY_MAP, CONFIG_SCHEMA,
validate_config_file

**unified_cloud_interface** (14 missing from UTL):
get_data_source, get_event_bus, get_pubsub_client, get_queue_client, get_analytics_client,
EventBus, PubSubClient, QueueClient, StorageBlob, BlobMetadata, StorageDataSource,
AnalyticsClient, PubSubSubscriberClient, PubSubReceivedMessage, CredentialsRegistry,
create_s2s_auth_dependency

**unified_events_interface** (36 missing — mostly event name constants):
All KILL_SWITCH_*, ORDER_*, POSITION_*, PORTFOLIO_*, BALANCE_*, DEVIATION_*, PNL_*,
CIRCUIT_BREAKER_*, REGIME_*, TRADE_REPORTED_MIFID, etc. + CoordinationEvent,
ComplianceEventPayload, JSONDict

### ~60 domain-specific symbols (remain as direct deps — NOT added to UTL):
Feature calculator math, ML types, position types, market adapters, execution adapters, URDI adapters

## Execution Phases

### Phase 0 — Whitelist deployment-service (DONE)
- [x] [AGENT] P0. Add deployment-service to TIER_EXEMPT_REPOS in fix-internal-dependency-alignment.py
- [x] [AGENT] P0. Plan filed with detailed symbol audit

### Phase 1 — Add ~40 common re-exports to UTL __init__.py
- [ ] [AGENT] P0. Add UnifiedCloudConfig, InstrumentDomainConfig, and all domain config classes
- [ ] [AGENT] P0. Add get_data_source, get_event_bus, get_pubsub_client, and all cloud clients
- [ ] [AGENT] P0. Add all event name constants (KILL_SWITCH_*, ORDER_*, etc.)
- [ ] [AGENT] P0. Add CoordinationEvent, ComplianceEventPayload, ConfigStoreError, etc.
- [ ] [AGENT] P0. Verify: `python3 -c "from unified_trading_library import UnifiedCloudConfig; print('OK')"`

### Phase 2 — Change service imports to UTL (PARALLEL across 18 services)
- [ ] [AGENT] P0. For each service: `from unified_config_interface import X` → `from unified_trading_library import X`
- [ ] [AGENT] P0. Same for unified_cloud_interface → UTL
- [ ] [AGENT] P0. Same for unified_events_interface → UTL (event constants + helpers)
- [ ] [AGENT] P0. Leave domain-specific imports as-is (URDI, UMI, UTEI, etc.)
- [ ] [AGENT] P0. Run import smoke test per service

### Phase 3 — Remove disallowed deps from pyproject.toml
- [ ] [AGENT] P0. Remove unified-config-interface from all services' [project.dependencies] + [tool.uv.sources]
- [ ] [AGENT] P0. Remove unified-cloud-interface from all services
- [ ] [AGENT] P0. Remove unified-events-interface from all services
- [ ] [AGENT] P0. Remove unified-domain-client from all services except strategy-service
- [ ] [AGENT] P0. Keep domain-specific deps only for services that need them (per table above)

### Phase 4 — Update validate-import-deps.py enforcement
- [ ] [AGENT] P0. Change script to FLAG direct imports from config/cloud/events as violations
- [ ] [AGENT] P0. Add per-service allowed direct dep whitelist (from table above)
- [ ] [AGENT] P0. deployment-service fully exempt

### Phase 5 — Strip manifest + verify alignment
- [ ] [AGENT] P0. Re-run manifest stripping of transitive deps
- [ ] [AGENT] P0. Run version alignment — should pass clean
- [ ] [AGENT] P0. Run run-all-setup.sh — all services pass import smoke test

## Success Criteria

- `from unified_config_interface import X` appears in ZERO services (except deployment-service)
- `from unified_cloud_interface import X` appears in ZERO services (except deployment-service)
- `from unified_events_interface import X` appears in ZERO services (except deployment-service)
- Each service's pyproject.toml has max 3-5 internal deps (UTL + UAC + UIC + domain-specific)
- Version alignment passes with 0 misalignments
- All services pass setup smoke test
