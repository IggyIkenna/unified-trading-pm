---
doc_type: codex-ssot
title: Data Ownership Principles
summary:
  The five-layer data-ownership model (external schema / normalize fn / registry-static / config / domain-data) with
  owners, plus interface-vs-service role boundaries and the config-vs-registry-vs-schema-vs-data decision table.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service, market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [data-ownership, uac, schema, registry, config, normalization]
related: [/codex/04-architecture/asset-class-ownership.md, /codex/04-architecture/data-flow-map.md]
created: 2026-03-27
authoritative_for: [data-ownership five-layer model and interface-vs-service role boundaries]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Data Ownership Principles

> SSOT: This document. Referenced from `00-SSOT-INDEX.md`. Scope: All asset classes (TradFi, CeFi, DeFi, Sports,
> Crypto).

## 1. The Five Layers

Every piece of data in the system belongs to exactly ONE of these layers:

| Layer                      | Owner                                   | What lives here                                                                                                                                                                                             | Changes how often                                   |
| -------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **External schemas**       | UAC `external/{source}/schemas.py`      | Raw API response models per venue/source. Pydantic models matching the external API exactly.                                                                                                                | When venue changes their API                        |
| **Normalize functions**    | UAC `external/{source}/normalize.py`    | Translation rules: raw → canonical. One function per venue per concept (e.g., `normalize_betfair_fixture()`, `normalize_binance_instrument()`).                                                             | When venue schema changes or mapping logic improves |
| **Registry / static data** | UAC `registry/` + `canonical/domain/`   | Venue endpoints, IDs, league tables, team mappings, venue classification, error codes. Data that changes very rarely (new league, new venue, bookmaker name change). Not config — matter-of-fact reference. | Monthly or less                                     |
| **Config**                 | UCI `domain_configs.py` → cloud storage | Service-specific runtime parameters: enabled venues, polling intervals, MVP token filters, batch date ranges. Read from cloud storage via `ConfigStore`/`TimeSeriesConfigStore`.                            | Per-deployment or hot-reloaded                      |
| **Domain data**            | Services → DataSink/EventBus            | Dynamic data that services produce: fixtures for a date, instruments discovered, market ticks, features computed. Stored via UCI DataSink, shipped via UCI EventBus/PubSub. Never in code.                  | Continuously                                        |

### Key distinctions

- **Registry ≠ Config**: League IDs are registry (they exist whether or not you use them). Which leagues to process is
  config.
- **External schema ≠ Canonical schema**: Betfair's `MarketCatalogue` is an external schema. `CanonicalFixture` is the
  canonical schema. The normalize function bridges them.
- **UAC canonical ≠ UIC internal**: UAC canonical models define WHAT something IS (domain truth). UIC internal contracts
  define HOW it flows between services (storage columns, partitioning, nullable fields for incomplete data). Both are
  needed — they serve different consumers.

## 2. Interface Roles

| Interface                                                                                                                                | Owns                                                                                                                                           | Does NOT own                                                                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **instruments-service** (reference data — formerly unified-reference-data-interface, **Retired 2026 — merged into instruments-service**) | Connectivity to venue APIs. Auth management. Calling `normalize_*()` from UAC. Returning `InstrumentRecord`.                                   | Domain data storage. Scheduling. Venue schemas (those are in UAC).                                                                         |
| **instruments-service sports/** (sports reference — formerly USRI, **Retired 2026 — merged into instruments-service**)                   | Connectivity to sports data APIs (API Football, etc.). Calling `normalize_*()` from UAC. Returning `CanonicalFixture`, `CanonicalLeague`, etc. | Fixture storage. League classification logic. Team mapping data (that's UAC registry).                                                     |
| **UMI** (market data)                                                                                                                    | Connectivity to market data feeds (WebSocket, REST). Raw tick/OHLCV retrieval.                                                                 | Reference data (that's instruments-service). Instrument discovery (that's instruments-service). Processing/downsampling (that's services). |
| **UCI** (cloud)                                                                                                                          | Cloud-agnostic storage, messaging, config. DataSink, EventBus, ConfigStore.                                                                    | Domain logic. Venue connectivity. Schema definitions.                                                                                      |
| **UEI** (events)                                                                                                                         | Event schema definitions. `log_event()` + `setup_events()`.                                                                                    | Event routing (that's UCI PubSub). Event processing (that's services).                                                                     |

## 3. Service Roles

Services are the ONLY deployed, scheduled components. Interfaces are libraries — they don't trigger themselves.

| Service                            | Orchestrates                                                                                                                                                                                           | Stores                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| **instruments-service**            | Calls reference-data adapters (formerly unified-reference-data-interface/USRI, now in-service) to discover instruments for a date. Joins reference data (fixtures) with market instruments. Validates. | Instruments via DataSink (Parquet, by venue/date). |
| **market-tick-data-service**       | Calls UMI to fetch raw market data. Routes to correct adapter.                                                                                                                                         | Raw ticks via DataSink.                            |
| **market-data-processing-service** | Reads raw ticks, computes OHLCV, resamples.                                                                                                                                                            | Processed candles via DataSink.                    |
| **features-\*-service**            | Computes features from processed data.                                                                                                                                                                 | Feature vectors via DataSink.                      |
| **execution-service**              | Routes orders via UTEI/UDEI.                                                                                                                                                                           | Fills, PnL via DataSink.                           |

## 4. The Pattern (all asset classes)

```
Service (scheduled/triggered)
  → calls Interface (connectivity + auth)
    → Interface uses UAC (external schema → normalize → canonical schema)
    → returns canonical objects
  → Service applies domain logic (filtering, joining, validation)
  → Service stores via UCI DataSink
  → Service emits via UEI log_event()
```

No service should:

- Define its own normalize functions (use UAC's)
- Define its own external schemas (use UAC's)
- Hold static reference data that belongs in UAC registry
- Connect directly to external APIs (use the interface)

No interface should:

- Trigger itself on a schedule
- Store domain data
- Define schemas (use UAC's)

## 5. Config vs Registry vs Schema vs Data

| Question                                                            | Answer             | Lives in                                      |
| ------------------------------------------------------------------- | ------------------ | --------------------------------------------- |
| "What is Betfair's API endpoint?"                                   | Registry           | UAC `registry/endpoints.py`                   |
| "What does Betfair's MarketCatalogue response look like?"           | External schema    | UAC `external/betfair/schemas.py`             |
| "How do I convert Betfair's MarketCatalogue to a CanonicalFixture?" | Normalize function | UAC `external/betfair/normalize.py`           |
| "What does a canonical fixture look like?"                          | Canonical schema   | UAC `canonical/domain/sports/fixture.py`      |
| "How is a fixture stored internally between services?"              | Internal contract  | UIC `sports.py`                               |
| "Which leagues should I process today?"                             | Config             | UCI → cloud storage                           |
| "What are the fixtures for Arsenal vs Chelsea on Jan 5?"            | Domain data        | instruments-service → DataSink                |
| "What teams are in the EPL?"                                        | Registry (static)  | UAC `canonical/domain/sports/league_data.py`  |
| "What error codes does Betfair return?"                             | Error registry     | UAC `canonical/crosscutting/errors/sports.py` |
