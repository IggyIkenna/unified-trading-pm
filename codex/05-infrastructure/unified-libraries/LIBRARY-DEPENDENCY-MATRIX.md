---
doc_type: codex-ssot
title: Library Dependency Matrix
summary: >-
  Library-layer (T0–T3) dependency quick-reference — per-tier library exports, the tier import rules, the full
  service×library dependency matrix, and library usage counts; explicitly NOT the tier SSOT (that is
  `tier-and-import-architecture.md`) and NOT the machine-readable SSOT (`workspace-manifest.json`).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [infrastructure, refactor, uac]
related:
  [
    /codex/05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md,
    /codex/05-infrastructure/unified-libraries/dependency-matrix.md,
    ../../04-architecture/tier-and-import-architecture.md,
  ]
created: 2026-03-27
authoritative_for: [library dependency matrix (per-library table view)]
referenced_by:
  [
    /codex/05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md,
    /codex/05-infrastructure/unified-libraries/dependency-matrix.md,
  ]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# Library Dependency Matrix

> **Supersedes:** `archive/dependency-matrix.md` (2026-02-26). unified-api-contracts version table moved to
> `02-data/unified-api-contracts-chain.md`.

> **⚠️ Migration note (2026-05-20)**: `risk-and-exposure-service`, `position-balance-monitor-service`, and
> `pnl-attribution-service` are now sub-packages of `strategy-service` (`strategy_service/{risk,position,pnl}/`).
> Dependency matrix rows for those 3 repos are superseded by the single `strategy-service` row.

> ⚠️ **THIS IS NOT THE TIER SSOT.**
>
> **Authoritative tier model:**
> [`04-architecture/tier-and-import-architecture.md`](../../04-architecture/tier-and-import-architecture.md) — defines
> the full 5-tier system (T0 pure leaves → T1 service runtime → T2 domain interfaces → T3 domain data client →
> T4/service)
>
> **Machine-readable SSOT:**
> [`unified-trading-pm/workspace-manifest.json`](../../../../unified-trading-pm/workspace-manifest.json) — canonical
> `arch_tier`, `dependencies`, `completion_paths`, `tier_rules` per repo
>
> This document covers the **library layer only** (T0–T3) — which library imports which, and why. For services and UIs,
> see `04-architecture/tier-and-import-architecture.md`.

**Last updated:** 2026-02-28

---

## Library Tier Diagram (T0–T3 only)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  TIER 0 — Pure Leaves (zero unified-* imports; stdlib + external packages only)  │
│                                                                                  │
│  unified-api-contracts (AC + AC_INT)         unified-cloud-interface (UCLI)               │
│  AC_INT = unified_api_contracts.internal   unified-config-interface (UCI)                │
│  unified-trading-library (UEI)    execution-algo-library (EAL)                  │
│  matching-engine-library (MEL)                                                    │
│  NOTE: unified-reference-data-interface (retired) merged into instruments-service   │
└──────────────────────────────────────┬───────────────────────────────────────────┘
                                       │ T0 imports only
┌──────────────────────────────────────▼───────────────────────────────────────────┐
│  TIER 1 — Shared Cloud Runtime (imports T0 only)                                 │
│  unified-trading-services (UTL)                                                  │
│  ConfigStore · GCSEventSink · PubSubEventSink · ServiceCLI · BatchOrchestrator   │
│  setup_service · @with_retry · StateStore · GracefulShutdownHandler              │
└────────────┬──────────────────────────────────────────────────────┬──────────────┘
             │ T0+T1 imports                                        │ T0+T1 imports
┌────────────▼──────────────────┐   ┌──────────────────────────────▼──────────────┐
│  TIER 3 — Domain Data Client  │   │  TIER 2 — Domain/Market Interfaces           │
│                               │   │                                              │
│  unified-domain-client (UDC)  │   │  market-tick-data-service/market_tick_data_service/market_interface (UMI)              │
│  PATH_REGISTRY · 20 datasets  │   │  unified-ml-interface (UML)                  │
│  14 typed domain clients      │   │  unified-trading-library (UFC)    │
│  DirectReader/Writer          │   │                                              │
│  BigQueryCatalog · GlueCatalog│   │  MERGED INTO SERVICES (2026-03-26):          │
│  DataCompletionChecker        │   │  UTEI+UDEI+USEI → execution-service          │
│                               │   │  UPI → position-balance-monitor-service      │
└───────────────────────────────┘   └─────────────────────────────────────────────┘
             │                                        │
             └─────────────────┬──────────────────────┘
                               │ T0–T3 imports (never cross-tier, never service→service)
            ┌──────────────────▼──────────────────────────────────────────────┐
            │  TIER 4 / SERVICES — 17+ service repos                          │
            │  instruments-service · market-tick-data-service                 │
            │  market-data-processing-service · features-* · ml-*             │
            │  strategy-service · execution-service · pnl-attribution-service│
            │  position-balance-monitor-service · risk-and-exposure-service   │
            │  alerting-service                                               │
            └─────────────────────────────────────────────────────────────────┘
```

---

## Import Rules

| Tier    | May import from                 | Violation check                                           |
| ------- | ------------------------------- | --------------------------------------------------------- |
| 0       | stdlib + external packages only | Zero `from unified_` imports                              |
| 1       | Tier 0 only                     | No T2/T3 imports                                          |
| 2       | Tier 0 + Tier 1                 | No `from unified_domain_client` (T3); no other T2 imports |
| 3       | Tier 0 + Tier 1                 | No T2 imports                                             |
| service | T0 + T1 + T2 + T3               | Never imports another service                             |
| api/ui  | T0 only (no internal libs)      | Call services via REST/SSE only                           |

> ⚠️ **Known violation:** `market-tick-data-service/market_tick_data_service/market_interface` currently imports
> `unified-domain-client` (T2→T3 lateral). Must be removed — tracked as `cohesion-umi-udc-dep-violation` in consolidated
> plan.

---

## Diamond Pattern (safe — Python sys.modules cache)

```
Services → UTS (T1) → UCLI (T0)
Services → UDC (T3) → UCLI (T0)
Services → UMI (T2) → UCLI (T0)
```

All three paths converge on T0 libs. Python loads each package once.

---

## Tier 0 Library Quick-Reference

| Library                  | Package                          | Key exports                                                                                                                               | External deps               |
| ------------------------ | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| unified-api-contracts    | `unified_api_contracts`          | Pydantic v2 schemas, VCR cassettes, `unified_api_contracts.external`, `unified_api_contracts.canonical`, `unified_api_contracts.internal` | pydantic, aiohttp           |
| _(internal subpackage)_  | `unified_api_contracts.internal` | `MessagingTopic`, `EventEnvelope`, PubSub topic names, req/resp/error envelopes (part of unified-api-contracts)                           | pydantic                    |
| unified-config-interface | `unified_config_interface`       | `UnifiedCloudConfig`, `BaseConfig`, env loading, venue constants                                                                          | pydantic, pyyaml            |
| unified-trading-library  | `unified_trading_library.events` | `EventSink` Protocol, `setup_events`, `log_event`, `MockEventSink`                                                                        | pydantic                    |
| unified-cloud-interface  | `unified_cloud_interface`        | `StorageClient`, `SecretClient`, `QueueClient`; GCP/AWS/Local providers                                                                   | google-cloud-storage, boto3 |
| execution-algo-library   | `execution_algo_library`         | TWAP, VWAP, Iceberg — pure compute, zero inter-lib deps                                                                                   | pydantic, python-dateutil   |
| matching-engine-library  | `matching_engine_library`        | Pure order matching logic, zero inter-lib deps                                                                                            | pydantic                    |

## Tier 1 Library Quick-Reference

| Library                  | Package                    | Key exports                                                                                                                                                                                                                                 | Imports (T0)            |
| ------------------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| unified-trading-services | `unified_trading_services` | `get_secret_client`, `handle_api_errors`, `GCSEventSink`, `PubSubEventSink`, `QueueEventSink`, `ConfigStore`, `ServiceCLI`, `BatchOrchestrator`, `setup_service`, `@with_retry`, `StateStore`, `BaseCloudWriter`, `GracefulShutdownHandler` | UCLI, UCI, UEI, UIC_INT |

## Tier 2 Library Quick-Reference

| Library                                                            | Package                              | Key exports                                                                                                                         | Imports (T0+T1)                              |
| ------------------------------------------------------------------ | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| market-tick-data-service/market_tick_data_service/market_interface | `unified_market_interface`           | `CanonicalTick`, `BaseWebSocketClient`, `VenueRateLimiter`, venue WS adapters (Binance, OKX, Deribit, Bybit, Hyperliquid, Coinbase) | UTS, UCI, AC ⚠️ also imports UDC (violation) |
| unified-ml-interface                                               | `unified_ml_interface`               | ML model protocols, `CrossValidationResult`, `ModelDegradationAlert`, prediction schemas                                            | UTS, UCI                                     |
| unified-trading-library                                            | `unified_feature_calculator_library` | `FeatureCalculatorRegistry`, `BaseFeatureService`, `FeatureStalenessConfig`                                                         | UTS, UCI                                     |

NOTE: The following T2 repos have been merged into services (no longer standalone libraries):

- unified-trade-execution-interface (UTEI) → execution-service
- unified-defi-execution-interface (UDEI) → execution-service
- unified-sports-execution-interface (USEI) → execution-service
- unified-position-interface (UPI) → position-balance-monitor-service

## Tier 3 Library Quick-Reference

| Library               | Package                 | Key exports                                                                                                                                                                                                     | Imports (T0+T1) |
| --------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| unified-domain-client | `unified_domain_client` | `PATH_REGISTRY` (20 datasets), 14 typed domain clients, `DirectReader`, `DirectWriter`, `BigQueryCatalog`, `GlueCatalog`, `DataCompletionChecker`, `get_available_date_range`, `StandardizedDomainCloudService` | UTS, UCLI, UCI  |

---

## Full Service → Library Dependency Matrix

All 17 active/scaffolded services × all 16 libraries. `●` = direct dependency. `○` = not required. `⟪f⟫` =
future/scaffolded service.

| Service                                  | UTS | UCI | UEI | UCLI | AC  | UIC | ref-if | EAL | MEL | UMI | UTEI | UDEI | USEI | UML | UFC | UPI | UDC |
| ---------------------------------------- | :-: | :-: | :-: | :--: | :-: | :-: | :----: | :-: | :-: | :-: | :--: | :--: | :--: | :-: | :-: | :-: | :-: |
| **instruments-service**                  |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ●    |  ○  |  ○  |  ●  |  ○   |  ○   |  ○   |  ○  |  ○  |  ○  |  ●  |
| **market-tick-data-service**             |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ●  |  ○   |  ○   |  ○   |  ○  |  ○  |  ○  |  ●  |
| **market-data-processing-service**       |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ●  |  ○   |  ○   |  ○   |  ○  |  ○  |  ○  |  ●  |
| **features-service (calendar family)**   |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ○  |  ●  |  ○  |  ○  |
| **features-service (delta-one family)**  |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ●  |  ○   |  ○   |  ○   |  ○  |  ●  |  ○  |  ●  |
| **features-service (volatility family)** |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ●  |  ○   |  ○   |  ○   |  ○  |  ●  |  ○  |  ●  |
| **features-service (onchain family)**    |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ●   |  ○   |  ○  |  ●  |  ○  |  ●  |
| **features-service (sports family)** ⟪f⟫ |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ●   |  ○  |  ●  |  ○  |  ●  |
| **ml-training-service**                  |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ●  |  ○  |  ○  |  ●  |
| **ml-inference-service**                 |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ●  |  ○  |  ○  |  ●  |
| **strategy-service**                     |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ●  |  ○   |  ○   |  ○   |  ●  |  ○  |  ○  |  ●  |
| **execution-service**                    |  ●  |  ●  |  ●  |  ○   |  ●  |  ○  |   ○    |  ●  |  ●  |  ●  |  ●   |  ○   |  ○   |  ○  |  ○  |  ○  |  ●  |
| **pnl-attribution-service**              |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ○  |  ○  |  ○  |  ●  |
| **position-balance-monitor-service**     |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ○  |  ○  |  ●  |  ●  |
| **risk-and-exposure-service**            |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ○  |  ○  |  ○  |  ●  |
| **alerting-service**                     |  ●  |  ●  |  ●  |  ○   |  ○  |  ○  |   ○    |  ○  |  ○  |  ○  |  ○   |  ○   |  ○   |  ○  |  ○  |  ○  |  ○  |

**Column key:** UTS=unified-trading-services, UCI=unified-config-interface, UEI=unified-trading-library,
UCLI=unified-cloud-interface, AC=unified-api-contracts (incl. AC_INT=unified_api_contracts.internal subpackage),
UIC=unified-internal-contracts (ELIMINATED — merged into UAC internal/), ref-if=unified-reference-data-interface
(ELIMINATED — merged into instruments-service), EAL=execution-algo-library, MEL=matching-engine-library,
UMI=market-tick-data-service/market_tick_data_service/market_interface, UTEI=unified-trade-execution-interface
(ELIMINATED — merged into execution-service), UDEI=unified-defi-execution-interface (ELIMINATED — merged into
execution-service), USEI=unified-sports-execution-interface (ELIMINATED — merged into execution-service),
UML=unified-ml-interface, UFC=unified-trading-library, UPI=unified-position-interface (ELIMINATED — merged into
position-balance-monitor-service), UDC=unified-domain-client

---

## Library Usage Count (by consumer count)

| Library                                                                      | Services using | Service list                                                                           |
| ---------------------------------------------------------------------------- | :------------: | -------------------------------------------------------------------------------------- |
| **UTS** (unified-trading-services)                                           |       17       | All                                                                                    |
| **UCI** (unified-config-interface)                                           |       17       | All                                                                                    |
| **UEI** (unified-trading-library)                                            |       17       | All (via UTS re-export)                                                                |
| **UDC** (unified-domain-client)                                              |       13       | instruments, MTDH, MDPS, FDS, FVS, FOS, FSS, MLTR, MLIN, STR, EXEC, PNL, PBM, RAE, SVS |
| **UMI** (market-tick-data-service/market_tick_data_service/market_interface) |       5        | instruments, MTDH, MDPS, FDS, FVS, STR, EXEC                                           |
| **UFC** (unified-trading-library)                                            |       5        | FCS, FDS, FVS, FOS, FSS                                                                |
| **UML** (unified-ml-interface)                                               |       3        | MLTR, MLIN, STR                                                                        |
| **EAL** (execution-algo-library)                                             |       1        | execution-service                                                                      |
| **MEL** (matching-engine-library)                                            |       1        | execution-service                                                                      |
| **AC** (unified-api-contracts)                                               |       1        | execution-service (direct); others via UMI transitively                                |
| ~~UTEI~~ (ELIMINATED)                                                        |       —        | Merged into execution-service                                                          |
| ~~UDEI~~ (ELIMINATED)                                                        |       —        | Merged into execution-service                                                          |
| ~~USEI~~ (ELIMINATED)                                                        |       —        | Merged into execution-service                                                          |
| ~~unified-reference-data-interface~~ (ELIMINATED)                            |       —        | Merged into instruments-service                                                        |
| ~~UPI~~ (ELIMINATED)                                                         |       —        | Merged into position-balance-monitor-service                                           |
| **UCLI** (unified-cloud-interface)                                           |    0 direct    | All get via UTS transitively                                                           |
| **AC_INT** (unified_api_contracts.internal)                                  |    0 direct    | Via UTS transitively (part of unified-api-contracts)                                   |

---

## QG Tier Enforcement

Quality gate step checks:

- `STEP 5.5`: no direct `google.cloud` or `boto3` imports in library source (use UCLI)
- `STEP 5.6`: tier compliance via `REPO_ARCH_TIER` env variable
  - Tier 0: zero `from unified_` imports anywhere in source
  - Tier 2: no `from unified_domain_client` imports (T2 must not import T3)
  - Services: no `from <other_service>` imports
- `STEP 5.7`: `unified-api-contracts` version alignment for T2 consumers (UMI — UTEI/UDEI/USEI eliminated, merged into
  execution-service)
