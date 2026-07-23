---
doc_type: codex-ssot
title: Tier + Import Architecture — 5-Tier Dependency Model + Cross-Tier Protocol Injection
summary:
  The 5-tier (T0–T4) integer-tagged dependency model plus the cross-tier protocol-injection contract — higher tiers
  import same/lower only, no service-to-service imports, services declare WHAT + MODE while topology injects HOW via the
  UCI factory, enforced by QG STEP 5.10/5.11 and check-no-service-deps.py.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    execution-service,
    ibkr-gateway-infra,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [tier, refactor, uac, ssot, quality-gates, protocol-injection, imports, architecture]
related:
  [
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/04-architecture/commercial-service-families.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/cloud-agnostic-migration.md,
  ]
created: 2026-03-27
authoritative_for: [5-tier dependency model + cross-tier protocol-injection contract]
referenced_by:
  [
    /codex/02-data/contracts-scope-and-layout.md,
    /codex/04-architecture/TOPOLOGY-DAG.md,
    /codex/04-architecture/cloud-agnostic-migration.md,
    /codex/04-architecture/commercial-service-families.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/04-architecture/service-control-surface.md,
    /codex/04-architecture/service-framework.md,
  ]
owner:
last_reviewed: 2026-06-25
code_refs:
---

# Tier + Import Architecture — 5-Tier Dependency Model + Cross-Tier Protocol Injection

> **Created 2026-05-08** (Phase E.1 of `plans/active/codex_refactor_2026_05_08.md`) by merging two prior docs into one
> SSOT for the import-tier surface:
>
> - `TIER-ARCHITECTURE.md` (5-tier dependency model, per-repo tier assignments, integer tier values, T0 sub-tier model,
>   tier-violation tracking, naming conventions).
> - `PROTOCOL-INJECTION.md` (cross-tier protocol injection contract, `CLOUD_PROVIDER` / `SERVICE_MODE` / `PROTOCOL_*`
>   env-var conventions, factory functions, live vs batch wiring, service-side anti-patterns + QG enforcement).
>
> The two docs always read as one — the tier model is what tells you WHICH library belongs WHERE; the protocol-injection
> contract is what tells you HOW the lower tiers reach intent-level factory functions without leaking cloud SDK
> knowledge into services. Runtime + deployment topology (cluster shapes, container co-location, message-flow diagrams)
> is in [`runtime-deployment-topology.md`](runtime-deployment-topology.md); commercial / UX service-family scoping is in
> [`commercial-service-families.md`](commercial-service-families.md).

**Last updated:** 2026-05-08

---

# Import-Tier Rules (TL;DR)

1. **5 tiers, integer-tagged** in `workspace-manifest.json` (`arch_tier: 0|1|2|3|4`). Higher tiers may import from SAME
   or LOWER tiers ONLY. Tier 0 must NEVER import from Tier 1+.
2. **No service ↔ service imports.** Services (T4) consume libraries (T0–T3) only. Cross-service contracts ride through
   `unified_api_contracts.internal` messaging schemas, never through Python imports.
3. **No circular imports.** UAC canonical/external (`T0-base`) MUST NOT import from UAC internal (`T0-consumer`); the
   internal layer depends on canonical, not the reverse. The single permitted intra-T0 import is UAC-internal → UAC
   canonical. Anything that breaks this direction is a build-order violation.
4. **Cloud-protocol injection is layered.** Services declare WHAT (data schema) + MODE (live/batch). Topology declares
   HOW (which provider, which bucket, which topic). Libraries resolve the rest via `unified_cloud_interface.factory`.
   Services NEVER import `google.cloud.*` / `boto3`, NEVER read `CLOUD_PROVIDER` / bucket names / topic names directly,
   NEVER instantiate `CloudTarget` (deleted) or carry `gcs_bucket` field names.
5. **Quality gates enforce both halves.** STEP 5.10 hard-fails any direct cloud SDK import in service code; STEP 5.11
   hard-fails any `CloudTarget` / `gcs_bucket` / `bigquery_dataset` field name. Tier-violation detection is integer
   `arch_tier <= N` comparison in `workspace-manifest.json`-driven CI checks.

---

# Part 1 — 5-Tier Dependency Model

```
TIER 0 — Pure Leaves (no cloud I/O, no trading state, zero inter-lib deps)

  NOTE: T0 has two sub-levels due to a single permitted inter-T0 import (UIC may import UAC):
    T0-L2a (true leaves, no workspace imports):
      unified-api-contracts (UAC)             Canonical schemas, Pydantic v2 models, VCR cassettes, external raw schemas
                                              stdlib + pydantic ONLY — zero unified-* imports, not even in tests.
                                              SSOT for all external API schemas and canonical normalization outputs.
      unified-cloud-interface (UCLI)          StorageClient, SecretClient, QueueClient, GCP+AWS+Local providers
      unified-trading-library (UEI)          EventSink Protocol, setup_events, log_event, MockEventSink
      execution-algo-library (EAL)            TWAP, VWAP, pure compute algorithms, zero inter-lib deps
      ibkr-gateway-infra                      Deploys and manages the IB Gateway Java process (long-lived). All IBKR
                                              connectivity routes through this — UMI + execution-service + position-balance-
                                              monitor-service + instruments-service adapters use it (formerly the UMI/UTEI/UPI/unified-reference-data-interface
                                              interfaces; **Retired 2026** — merged into their respective services). No
                                              unified-* imports. TWS uses proprietary socket protocol; mock at ib_insync
                                              layer for tests (not HTTP VCR).

    T0-L2b (UAC canonical-dependent; builds after L2a):
      unified_api_contracts.internal (UAC-internal)
                                              MessagingTopic, EventEnvelope, PubSub topics, req/resp/error schemas,
                                              internal/domain/<service-name>/ output schemas for all services.
                                              May import from UAC canonical (normalization canonicals re-exported for messaging).
                                              UAC canonical/external MUST NOT import from UAC internal — this direction is a CIRCULAR violation.
                                              Build order: UAC canonical (L2a) → UAC internal (L2b). merge_level in workspace-manifest: UAC=2.

  ModelArtifactStore — A pure abstract protocol for model artifact storage (save/load ML models). Lives at T0 (in `unified-cloud-interface` or `unified_api_contracts.internal`) because it has no cloud I/O or trading logic — just an abstract interface. Concrete implementation `CloudModelArtifactStore` lives in UDC (T3) using `get_storage_client()` from UCI (T0). ML services (T4) import the T0 protocol only — the concrete impl is injected at startup via dependency injection. UML (T2) may re-export the protocol for convenience.

TIER 1 — Shared Infrastructure (trading-aware cloud services)
  unified-config-interface (UCI)          BaseConfig, UnifiedCloudConfig, venue constants (imports UEI for CONFIG_LOADED event)
  matching-engine-library (MEL)           Pure order matching logic, imports schemas from unified_api_contracts.internal (OrderRecord, FeeResult, SwapResult, MatchResult). Pool impls (UniswapV2/3/4) remain local.
  unified-trading-library (UTL)           [renamed from unified-trading-services; alias package: unified_trading_services still works]
  Note: `unified-trading-services` is being renamed to `unified-trading-library` (UTL) per Phase 2 plan (`lib-phase2-uts-rename-step1`). Codex will be updated after rename is complete. Until then, both names refer to the same T1 library.
    get_storage_client, get_secret_client, handle_api_errors, handle_storage_errors
    ConfigStore, BaseCloudWriter, BaseCloudLoader, generate_date_range
    BaseDependencyChecker, GCSEventSink, PubSubEventSink, CompositeEventSink
    ServiceCLI, BaseModeHandler, BatchOrchestrator, @with_retry   ← service framework
    GracefulShutdownHandler

TIER 2 — Domain/Market Interfaces (protocols + schemas + connectivity, no cloud storage I/O)
  market-tick-data-service/market_tick_data_service/market_interface (UMI)              market data schemas + venue WS adapters + BaseWebSocketClient + VenueRateLimiter
  unified-ml-interface (UML)                  ML model protocols + prediction schemas
  unified-trading-library (UFC)    feature schemas + FeatureCalculatorRegistry + BaseFeatureService

  NOTE: The following T2 interface repos have been merged into their respective services (no longer exist as standalone repos):
  - unified-trade-execution-interface (UTEI) → execution-service (CeFi order/fill adapters, OMS, OrderTracker, SmartOrderRouter)
  - unified-defi-execution-interface (UDEI) → execution-service (BaseAMMAdapter, Uniswap/Curve/DeFi pool adapters)
  - unified-sports-execution-interface (USEI) → execution-service (BaseSportsAdapter, Betfair/Smarkets adapters)
  - unified-position-interface (UPI) → position-balance-monitor-service (position/account schemas + CCXT/OKX/IBKR adapters)
  - unified-reference-data-interface (retired) → instruments-service (REST venue adapters, API key resolution, IBKR corp actions)
  Do NOT import from or reference these eliminated repos.

TIER 3 — Domain Data Client (cloud storage I/O, uses UCLI + UTS)
  unified-domain-client / unified-domain-client (UDC)
    paths/         PATH_REGISTRY (20 datasets), DataSetSpec, build_bucket, build_path, build_full_uri
    clients/       14 typed domain clients
    readers/       DirectReader, BigQueryExternalReader, AthenaReader, get_reader()
    writers/       DirectWriter, get_writer()
    catalog/       BigQueryCatalog, GlueCatalog
    DataCompletionChecker, get_available_date_range
    CloudModelArtifactStore — concrete impl of ModelArtifactStore T0 protocol; uses get_storage_client() from UCI (T0); does NOT import T2
  UDC provides `CloudModelArtifactStore` implementing the `ModelArtifactStore` T0 protocol. Imports T0 for the protocol + `get_storage_client()`. Does NOT import T2.

TIER 4 — Services (uses Tier 0–3; never import from another service repo)
  14 service repos — all use ServiceCLI, BaseModeHandler/BatchOrchestrator
```

## Topology-Driven Protocol Selection

Services declare WHAT data they produce and which MODE (batch/live) they run in. The runtime topology defines HOW —
messaging transport, storage backend, and deployment target — read from
`unified-trading-pm/configs/runtime-topology.yaml` (the SSOT).

| Concern             | Declared by | Source of truth                      | Read via                                                                         |
| ------------------- | ----------- | ------------------------------------ | -------------------------------------------------------------------------------- |
| Data schema         | Service     | `unified_api_contracts.internal`     | import at build time                                                             |
| Service mode        | Service     | `PROTOCOL_SERVICE_MODE` env var      | `get_service_mode()` from `unified_cloud_interface.factory`                      |
| Messaging transport | Topology    | `protocols.messaging.{mode}.default` | `get_messaging_protocol(mode)` from `unified_config_interface.topology_reader`   |
| Storage backend     | Topology    | `protocols.storage.{mode}.default`   | `get_storage_protocol(mode)` from `unified_config_interface.topology_reader`     |
| Deployment target   | Topology    | `protocols.deployment.{service}`     | `get_deployment_target(service)` from `unified_config_interface.topology_reader` |

The `unified_config_interface.topology_reader` module is the canonical read layer for topology decisions. Libraries and
deployment-service import from it; services receive injected protocol config via UCI factory (`get_data_sink`,
`get_event_bus`, etc.).

## Import Rules

1. Higher tiers may import from SAME or LOWER tiers only.
2. Tier 0 must NEVER import from Tier 1+.
3. Tier 2 may import from Tier 0 and Tier 1.
4. Tier 3 (UDC) imports from Tier 0 (UCLI) and Tier 1 (UCI, UTL).
5. Services (Tier 4) import from Tier 0–3 only. Never from another service.
6. UIs import from service APIs only (never directly from libraries).

## Import Routing Map

| Symbol                                               | Import from                                          |
| ---------------------------------------------------- | ---------------------------------------------------- |
| StorageClient, get_storage_client                    | unified_cloud_interface                              |
| SecretClient, get_secret_client                      | unified_cloud_interface                              |
| CloudProvider, BlobMetadata                          | unified_cloud_interface                              |
| UnifiedCloudConfig, BaseConfig                       | unified_config_interface                             |
| setup_events, log_event, MockEventSink               | unified_trading_library.events                       |
| get_secret_client, handle_api_errors                 | unified_trading_services (→ unified_trading_library) |
| GCSEventSink, setup_service                          | unified_trading_services (→ unified_trading_library) |
| ServiceCLI, BatchOrchestrator, with_retry            | unified_trading_services (→ unified_trading_library) |
| InstrumentsDomainClient, DataCompletionChecker       | unified_domain_client                                |
| PATH_REGISTRY, get_reader, get_writer                | unified_domain_client                                |
| CanonicalTick, BaseWebSocketClient, VenueRateLimiter | unified_market_interface                             |
| UnifiedOrderManager, OrderTracker                    | unified_trade_execution_interface                    |
| FeatureCalculatorRegistry, BaseFeatureService        | unified_feature_calculator (UFC repo)                |
| get_reference_adapter, BaseReferenceAdapter          | unified_reference_data_interface                     |

## Topology / Level Map

**L10 — system-integration-tests** (standalone repo, created in Phase 1 Stream B UTD V3 four-way split)

- Zero cross-service Python imports — interacts via HTTP, GCS, PubSub only
- Discovers live services via `deployment-api GET /services`
- Contains Layer 3a smoke tests (`@pytest.mark.smoke`, <5 min) and Layer 3b full E2E (`@pytest.mark.full_e2e`, 15–30
  min)
- Depends on: `unified-api-contracts` (canonical schema validation + internal message schemas)

## T0 Sub-Tier Model (Corrected — Supersedes Outdated Audit Spec)

The T0 tier contains two sub-tiers due to a single permitted intra-UAC import direction:

- **T0-base (true leaves, no workspace imports):** `unified-api-contracts` canonical/external surface — zero internal
  workspace dependencies; pure external contract schemas, Pydantic v2 models, VCR cassettes. stdlib + pydantic ONLY.
- **T0-consumer (canonical-dependent):** `unified_api_contracts.internal` — may depend on
  `unified_api_contracts.canonical` only (internal schemas that reference external contract types). The
  canonical/external surface MUST NOT import from `internal` — this direction is a CIRCULAR violation. Build order: UAC
  canonical (T0-base) → UAC internal (T0-consumer); both within the same `unified-api-contracts` repo.

**T1 sub-ordering:**

- **T1a:** `unified-config-interface` — BaseConfig, UnifiedCloudConfig, topology reader; imports UEI (T0) for
  CONFIG_LOADED event. This is T1, NOT T0. Any audit spec listing it as T0 is outdated.
- **T1b:** `unified-trading-library` — may depend on T1a (unified-config-interface) and T0 libraries.
- **T1c:** `unified-reference-data-interface` (ELIMINATED 2026-03-26) — REST venue adapters, API key resolution. Merged
  into `instruments-service` (T4 service). Reference data adapters now live inside the service, not as a standalone
  library.

> Note: `unified-config-interface` is T1, not T0. The audit spec listing it as T0 was outdated and has been corrected
> here. The canonical tier assignment is: UAC=T0-base, UIC=T0-consumer, UCI=T1a, UTL=T1b.
> unified-reference-data-interface/T1c eliminated.

**T2, T3:** unchanged — see the 5-Tier Dependency Model section above.

## Integer Tier Assignments (workspace-manifest.json)

The `arch_tier` field in `workspace-manifest.json` uses integer values (0, 1, 2, 3, 4) rather than string labels. This
was formalized as part of the UAC Citadel Architecture to enable programmatic tier validation in quality gates and CI.
The mapping is:

| Integer | Tier label | Description                     |
| ------- | ---------- | ------------------------------- |
| 0       | T0         | Pure leaves (no inter-lib deps) |
| 1       | T1         | Shared infrastructure           |
| 2       | T2         | Domain/market interfaces        |
| 3       | T3         | Domain data client (cloud I/O)  |
| 4       | T4         | Services                        |

Quality gates and the version cascade use integer comparison (`arch_tier <= N`) to enforce the tier import invariant.
String `arch_tier` values (e.g., `"T0"`, `"tier-0"`) are deprecated; all repos should use the integer form.

## No Service ↔ Service Imports — Enforcement + Layer-1.5 Test Shape

**HARD RULE:** A deployable service (T4) may declare as a cross-repo dependency ONLY shared libraries (UTL / UAC / the
`unified-*-interface` packages, T0–T3) — **never another service**. This means:

- No `[tool.uv.sources]` path dep on a peer service in `pyproject.toml`.
- No `import other_service` in source OR in tests.

Services integrate by **API contract + data transfer** (HTTP / events / GCS), with schemas held in UAC/UTL as the SSOT.

### Layer-1.5 Integration Test Shape

An integration test that spans two services asserts against the UAC/UTL contract + mocks — it does **not** import the
peer service. The concrete layers:

- **Layer-1.5 (per-component / contract test):** assert against `unified_api_contracts.internal` schemas + mocks; zero
  cross-service Python imports; credential-free, `--block-network`. This is what local `quality-gates.sh` runs.
- **Layer-3 / SIT (cross-service interaction):** HTTP / PubSub / GCS only; fires at the staging promotion boundary on a
  real breaking public-surface change, NOT on every dev push. See
  `/codex/06-coding-standards/integration-testing-layers.md` § "When Each Layer Runs".

### check-no-service-deps.py — Live Enforcement (2026-06-11)

`check-no-service-deps.py` is wired in `base-service.sh` at `scripts/validation/check-no-service-deps.py`. It:

- **Exits 1** on any cross-service Python import in source or tests (blocking merge).
- Classifies repo types as `service` / `api-service` / `batch-service` / `api` to scope its checks correctly.

Any remaining live violations are tracked in `plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md` §
"Service-dependency violations".

## Known Tier Violations

**Known T2→T3 violation:** `market-tick-data-service/market_tick_data_service/market_interface` (UMI, T2) currently
imports from `unified-domain-client` (UDC, T3). Task: `cohesion-umi-udc-dep-violation` in
`phase2_library_tier_hardening.plan.md`. Resolution: move whatever UMI imports from UDC into a T1 library or a shared T0
protocol. This violation must be fixed in Phase 2 T2 hardening step before Phase 3 begins.

## Naming Conventions

**Cloud-agnostic naming rule for protocols/interfaces:**

- Public-facing protocol and interface class names MUST use `Cloud*` prefix: `CloudStorageClient`,
  `CloudModelArtifactStore`, `CloudEventSink`
- Provider implementations MAY use cloud-specific prefixes: `GCSStorageClient`, `S3StorageClient` (in
  `providers/gcp.py`, `providers/aws.py`)
- NEVER use `GCS*`, `S3*`, or `GCP*` in public-facing protocol or abstract class names
- Rationale: protocols are cloud-agnostic; provider implementations are not

## Repo Rename Status (in progress)

- unified-trading-services → unified-trading-library (alias package: unified_trading_services still works during
  transition)
- unified-domain-client → unified-domain-client (alias package: unified_domain_client)

Use new package names in all new code. Alias packages ensure backward compat during transition.

---

# Part 2 — N-Tier Protocol Injection Contract

**SSOT for:** How libraries know which cloud protocol to use at runtime. **Related:**
`unified-trading-pm/TOPOLOGY-DAG.md` · `deployment-service/configs/runtime-topology.yaml` **Implementation:**
`unified-cloud-interface/unified_cloud_interface/factory.py`

## The Core Invariant

```
Services declare WHAT they want to do + which MODE they run in.
Deployment injects HOW (which provider, which bucket/topic).
Libraries resolve the rest.
Services never read CLOUD_PROVIDER, bucket names, or topic names directly.
```

This invariant is enforced by `quality-gates.sh` STEP 5.10 (no direct cloud SDK imports) and STEP 5.11 (no
`CloudTarget`, `gcs_bucket`, `bigquery_dataset` field names in services).

## Injection Stack

```
workspace-manifest.json (PM)
  └── TOPOLOGY-DAG.md (PM) — tier map, which libraries belong where
        └── runtime-topology.yaml (deployment-service/configs/)
              └── Deployment injects env vars per service instance:
                    CLOUD_PROVIDER=gcp|aws|local
                    SERVICE_MODE=live|batch
                    PROTOCOL_DATA_SINK_BUCKET_{ROUTING_KEY_UPPER}=<bucket-name>
                    PROTOCOL_EVENT_BUS_TOPIC_{ROUTING_KEY_UPPER}=<topic-name>
                      └── UCI factory.py (T0 — unified-cloud-interface)
                            └── Resolves: StorageClient | DataSink | EventBus | QueueClient
                                  └── Service calls:
                                        get_data_sink(routing_key="features")
                                        get_event_bus(routing_key="orders")
                                        get_storage_client()
                                        get_secret_client()
                                          └── Zero cloud SDK knowledge in service code
```

## Tier Injection Points

| Tier               | Library                    | Injection role                                                                                                                                   |
| ------------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| T0                 | `unified-cloud-interface`  | Defines all client ABCs + factory functions. Reads `CLOUD_PROVIDER` via `UnifiedCloudConfig`. Zero `os.getenv`. No service-specific knowledge.   |
| T1                 | `unified-config-interface` | `UnifiedCloudConfig` resolves env vars. All config values from here. Zero `os.getenv` in production source.                                      |
| T1                 | `unified-trading-library`  | Service runtime helpers (`BatchOrchestrator`, `StateStore`). Uses UCI factory. Never reads `CLOUD_PROVIDER` or `PROTOCOL_*` directly.            |
| T2/T3 (interfaces) | UMI, UTEI, UDC, etc.       | Use `get_data_sink(routing_key=...)` / `get_storage_client()` / `get_secret_client()`. Never instantiate providers. No `gcs_bucket` field names. |
| Services (T4)      | All services               | Call intent-level factory functions only. Declare `SERVICE_MODE`. Never import `google.cloud.*` or `boto3`.                                      |
| Deployment         | runtime-topology.yaml      | Sets all env vars per service deployment. Services are blind to GCP vs AWS.                                                                      |

## Factory Functions (UCI T0)

All live in `unified_cloud_interface.factory`:

```python
# Cloud-agnostic storage
get_storage_client(project_id=None) -> StorageClient
get_secret_client() -> SecretClient
get_queue_client() -> QueueClient

# Mode-agnostic data I/O (reads PROTOCOL_* env vars for bucket/topic routing)
get_data_sink(routing_key: str) -> DataSink
get_data_source(routing_key: str) -> DataSource
get_event_bus(routing_key: str) -> EventBus

# Compute/cache
get_analytics_client() -> AnalyticsClient
get_compute_client() -> ComputeClient
get_async_cache_client() -> AsyncCacheClient

# Mode
get_service_mode() -> ServiceMode  # live | batch
```

`CLOUD_PROVIDER` selects `gcp | aws | local`. `SERVICE_MODE` selects `live | batch` transport strategy.

## Env Var Naming Convention

```
CLOUD_PROVIDER=gcp|aws|local
SERVICE_MODE=live|batch

# Per routing key (set in runtime-topology.yaml per service):
PROTOCOL_DATA_SINK_BUCKET_FEATURES=features-store-cefi
PROTOCOL_DATA_SINK_BUCKET_INSTRUMENTS=instruments-store-cefi
PROTOCOL_DATA_SINK_BUCKET_EXECUTION=execution-results
PROTOCOL_DATA_SINK_BUCKET_ML_MODELS=ml-models-store

PROTOCOL_EVENT_BUS_TOPIC_ORDERS=projects/{project}/topics/orders
PROTOCOL_EVENT_BUS_TOPIC_FILLS=projects/{project}/topics/execution-fills
```

Routing key is the snake_case domain name (lowercase). Env var is `ROUTING_KEY.upper()`.

## Live vs Batch Wiring

| `SERVICE_MODE` | `DataSink` transport                     | `EventBus` transport                         |
| -------------- | ---------------------------------------- | -------------------------------------------- |
| `live`         | Object storage streaming writes (GCS/S3) | Message queue (PubSub/SQS)                   |
| `batch`        | Object storage bulk writes (GCS/S3)      | In-process (no queue — direct function call) |

The `runtime-topology.yaml` `co_location_rules` can override to `in_memory` for collocated services.

## What Services Must NOT Do

```python
# VIOLATION — never in service code
import os
bucket = os.getenv("GCS_BUCKET")  # banned
from google.cloud import storage   # banned outside UCI providers
import boto3                        # banned outside UCI providers

ct = CloudTarget(gcs_bucket="x")  # deleted from UDC/UTL
```

```python
# CORRECT — service code pattern
from unified_cloud_interface.factory import get_data_sink, get_storage_client

sink = get_data_sink(routing_key="features")
await sink.write(df, path="features/2024-01-01/data.parquet")

client = get_storage_client()
raw = client.download_bytes(bucket, path)  # bucket from config
```

## Enforcement

Quality gate STEP 5.10 (hard-fail): `rg "from google.cloud|import boto3|import botocore" --type py` Quality gate STEP
5.11 (hard-fail): `rg "CloudTarget|gcs_bucket|bigquery_dataset" --type py`

Both are in `quality-gates.sh`. Any violation blocks merge. Exceptions: `unified-cloud-interface/providers/` and
`deployment-service/terraform/` are exempt.

## Cross-References

- `unified-trading-pm/TOPOLOGY-DAG.md` — tier diagram (human-readable DAG)
- `deployment-service/configs/runtime-topology.yaml` — per-service env var wiring
- `unified-cloud-interface/unified_cloud_interface/factory.py` — implementation
- `unified-cloud-interface/unified_cloud_interface/protocol.py` — DataSink/DataSource/EventBus ABCs
- `unified-trading-pm/plans/archive/service_protocol_abstraction.plan.md` — plan defining this architecture
- `unified-trading-pm/plans/archive/topology_dag_pm_ssot.plan.md` — plan that created this doc
- [`runtime-deployment-topology.md`](runtime-deployment-topology.md) — runtime cluster shapes + deployment topology
- [`commercial-service-families.md`](commercial-service-families.md) — commercial / UX service-family scoping
