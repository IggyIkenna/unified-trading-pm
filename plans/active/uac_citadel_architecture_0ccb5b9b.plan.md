---
name: UAC Citadel Architecture
overview: |
  Citadel-grade architectural redesign of unified-api-contracts, unified-internal-contracts, and the interface/library ecosystem. Resolves structural mess in UAC (inconsistent external/, misplaced config, hard-to-navigate normalize/, scattered mappings). Establishes interface-domain-mirrored canonical organization, flat-per-source externals with co-located normalization, domain-capability registry, cross-cutting canonical layer, features stack (new interface + orchestration library), sports reference interface, and clean tier/dependency model. Subsumes good ideas from interfaces_capability_contract and internal_contract_replay_and_drift plans.
todos:
  - id: phase0-manifest-schema
    content: |
      Phase 0 -- Manifest schema evolution (prerequisite for all other phases): Split arch_tier into tier (integer 0-3) + role (string: contracts, primitive, library, interface, domain-client, service, api, ui, infrastructure, test). Add workspace_infrastructure.setup_repos: [unified-trading-pm, unified-trading-codex]. Add runtime_clients[] field to infrastructure repos (ibkr-gateway-infra). Fix tier violations: URDI 1->2, USEI 1->2, UCfgI 1->0. Remove UMI + UTEI from UTL dependencies (tier violation T1->T2). Remove direct UCI/UCfgI/UEI deps from interfaces (route through UTL at service level). Remove direct UCI/UCfgI deps from UDC (route through UTL). Simplify UFCL deps to UTL only. Regenerate topologicalOrder.levels via generate_workspace_dag.py. Update WORKSPACE_MANIFEST_DAG.svg with three edge types (code, tooling, runtime).
    status: pending
  - id: phase0-service-dep-cleanup
    content: |
      Phase 0b -- Service dependency cleanup: Remove explicit UCfgI + UCI + UEI deps from all ~30 services and APIs (they get these transitively through UTL). Each service keeps: UTL + domain interfaces + contracts (UAC/UIC) as needed. Feature services get: UTL + UFCL + UFOL. Update workspace-manifest.json for each service. Regenerate DAG. Verify edge count reduction (~180 -> ~130).
    status: pending
  - id: phase0-tier-gate-validator
    content: |
      Phase 0c -- Tier-gate validator update: Update tier-gate-check.sh to read integer tier field (not arch_tier string). Add validation: for each repo R with tier=N, every code dep D must have tier <= N. Add validation: workspace_infrastructure.setup_repos are not in any repo dependencies[]. Add validation: runtime_clients[] repos exist in manifest. Wire into quality-gates base scripts.
    status: pending
  - id: phase1-uac-foundations
    content: |
      Phase 1 -- UAC structural foundations (no import changes): Create normalize_utils/ with shared primitives (sides, symbols, timestamps, common). Move venue_manifest/ to registry/venue_manifest.py. Move venue_rate_limits.py to registry/. Delete orphan config/domain_config.py. Restructure external/cloud_sdks/ to external/aws/ and external/gcp/ (flatten one level).
    status: pending
  - id: phase2-canonical-reorg
    content: |
      Phase 2 -- Canonical domain reorganization (interface-mirrored): Reorganize canonical/domain/ into 8 interface-aligned sub-packages (market, reference, sports_reference, execution with base+trade/sports/defi, position, features, infrastructure, derivatives, onchain). Create canonical/crosscutting/ for errors, rate_limits, latency, connectivity. Move floating files (execution.py, odds.py, options.py, spread.py) into their domain directories. Move sports/canonical/ types to canonical/domain/sports_reference/.
    status: pending
  - id: phase3-normalize-colocation
    content: |
      Phase 3 -- Per-source normalization co-location: Extract venue-specific normalizers from canonical/normalize/*.py (22 modules, 338 symbols) into external/{source}/normalize.py. Each normalize.py imports from normalize_utils/. Keep canonical/normalize/__init__.py as temporary re-export facade. Move per-source mappings from canonical_mappings.py (465 lines) to external/{source}/mappings.py. Keep cross-venue lookups (DATA_SOURCE_TO_VENUES) in registry/.
    status: pending
  - id: phase4-flatten-external
    content: |
      Phase 4 -- Flatten non-standard external directories: mev/ -> flashbots/, mev_share/, mev_blocker/. onchain/ -> cryptoquant/. sports/sources/{provider}/ -> flat external/{provider}/. Delete empty shells after moves.
    status: pending
  - id: phase5-move-config-out
    content: |
      Phase 5 -- Move non-API-contract modules out of UAC: trading_validation.py -> unified-config-interface (config validation is its domain). log_level.py -> unified-trading-library (cross-cutting utility, 20 service consumers). quota_types.py -> SPLIT: AWS types to external/aws/, GCP to external/gcp/, canonical ComputeType to canonical/domain/infrastructure/. Delete shared/__init__.py and schemas/__init__.py facade modules.
    status: pending
  - id: phase6-import-surface
    content: |
      Phase 6 -- Import surface cleanup and enforcement: Update UAC __init__.py to export canonical domain + crosscutting + registry only. Update ALL interface adapter imports to new paths (40+ adapter files across 7 interfaces). Remove canonical/normalize/__init__.py facade (no dual paths). Add QG linter rule: services must not import from external/{source}/ (interfaces only).
    status: pending
  - id: phase7-registry-capability
    content: |
      Phase 7 -- Registry + domain-capability model: Build capability registry in registry/capability.py (from Plan 1 P0). Add domain-coverage dimension: per-source declaration of domains (market, reference, execution, position, features, infrastructure) and cross-cutting (errors, rate_limits, latency, connectivity). Backfill all current providers. Build coverage matrix generation script for gap visibility.
    status: pending
  - id: phase8-features-stack
    content: |
      Phase 8 -- Features stack (new repos): Create unified-features-interface (external feature/derived data IO via UAC). Create unified-feature-orchestration-library (pipeline routing, batch/live handlers, feature registry -- domain-specific UTL extension for feature services). Update workspace-manifest.json. Migrate feature-service UAC interactions.
    status: pending
  - id: phase9-sports-reference
    content: |
      Phase 9 -- Sports reference interface (new repo): Create unified-sports-reference-interface (fixtures, leagues, teams, players, bookmakers). Different refresh triggers/cadence from financial reference data. Update workspace-manifest.json. Migrate sports reference data consumption.
    status: pending
  - id: phase10-replay-drift
    content: |
      Phase 10 -- Replay and drift infrastructure (from Plan 2): UIC internal endpoint registry (R2). PM reusable replay workflow contract-replay.yml (R4). Nightly drift recording contract-drift-record.yml (R6). VCR capability assertions (Plan 1 P7). Lane metrics for smoke/replay/live/drift (R8). Least-privilege secrets for recorders (R7).
    status: pending
  - id: phase11-guardrails-adoption
    content: |
      Phase 11 -- Runtime guardrails and service adoption (from Plan 1): Fail-fast error classes in UTL (P2). Preflight capability checks in adapters (P2). Standard raw->validate->canonical pipeline in all adapters (P3). Remove duplicate mapping logic across interfaces (P3). Refactor services to canonical-only consumption (P4). SSOT docs in codex (P8). QG validators for capability coverage and duplicate detection (P8).
    status: pending
isProject: false
---

# Citadel-Grade UAC/UIC Architecture Redesign

Citadel-grade architectural redesign of the external contract, internal contract, and interface/library ecosystem. This
plan supersedes both `interfaces_capability_contract_unification` and `internal_contract_replay_and_drift_infra`,
incorporating their good ideas into a unified structural foundation.

---

## 1. Plan Conflict Audit (Superseded Plans)

### Plans being superseded

- **interfaces_capability_contract_unification_2026_03_14** (Plan 1): Capability registry, runtime guardrails,
  mode/env/auth checking, standardized raw->canonical flows, import surface enforcement.
- **internal_contract_replay_and_drift_infra_2026_03_14** (Plan 2): UAC/UIC boundary, replay gates, SIT, drift
  recording, cassette management.

### Compatible elements (no conflict)

- **Plan 1 P0 (capability registry in UAC)** vs **Plan 2 R2 (internal registry in UIC)**: Different repos, different
  purposes (external vs internal). Both incorporated. Design patterns aligned.
- **Plan 1 P6 (import surface enforcement)** and **Plan 2 R3 (UAC boundary cleanup)**: Complementary. Both drive toward
  a cleaner UAC with well-defined external-only scope. Combined into Phase 6.
- **Plan 1 P2 (error taxonomy in UTL)** and **Plan 2 R8 (observability metrics)**: Different concerns (error classes vs
  lane metrics). No overlap. Both incorporated into Phases 10-11.

### Coordination resolved (soft conflicts)

- **Plan 1 P7 (VCR alignment)** and **Plan 2 R4 (replay workflow)**: Both touch `testing/` and cassette validation.
  **Resolution:** VCR schema validation is the single mechanism. Plan 1 adds capability assertions as an extension. Plan
  2 adds replay workflow infrastructure around it. Combined into Phase 10.
- **Plan 1 P3 (normalize raw->validate->canonical)** and **Plan 2 R3 (remove internal endpoints from UAC)**:
  **Resolution:** Structural cleanup first (Phases 1-6), then normalization pipeline and boundary cleanup operate on
  clean foundation (Phases 7+).

### Execution order resolved

- Plan 2 depended on 7 other plans. Plan 1 had zero dependencies. Both assumed the current UAC structure and added
  features on top. **This plan fills the structural gap** as the prerequisite that both plans were missing. Phases 1-6
  are the restructure. Phases 7-11 incorporate Plan 1 and Plan 2 features on the clean foundation.

### Design gaps filled (not in either plan)

- Flat external sources with co-located normalization
- Canonical organized by interface domain (not ad-hoc)
- Cross-cutting canonical types (errors, rate limits, latency, connectivity) separated from domain
- Registry domain-capability model (which domains each source serves, coverage matrix)
- Features stack (unified-features-interface + unified-feature-orchestration-library)
- Sports reference interface (separate from financial reference data)
- Config ownership model (UAC/UIC have zero service config; services own their config.py)
- Cloud interface positioning (T0, no prod UAC dependency, UTL routes cloud operations)
- Coverage matrix / universe concept (canonical defines the universe, sources fill what they can)

---

## 2. Current State Problems

### a) Inconsistent `external/` directory

80+ subdirectories mixing five incompatible patterns:

| Pattern                     | Examples                                                               | Problem                                                                       |
| --------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Single-provider flat        | `binance/`, `bybit/`, `fred/`                                          | Correct pattern                                                               |
| Multi-provider domain group | `mev/` (Flashbots + MEV-Share + MEV Blocker), `onchain/` (CryptoQuant) | Hides individual sources behind domain grouping                               |
| Metadata registry           | `venue_manifest/`                                                      | Not a data source; belongs in `registry/`                                     |
| Cloud provider APIs         | `cloud_sdks/` (83 files, nested `aws/` + `gcp/`)                       | ARE external APIs but nested instead of flat `external/aws/`, `external/gcp/` |
| Nested canonical+sources    | `sports/` (has own `canonical/` + `sources/`)                          | UAC-within-UAC nesting; canonical types belong in `canonical/domain/`         |

### b) Misplaced `config/` directory

| File                                               | Problem                                                                                                                                                                                                 | Correct home                                                                                               |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `trading_validation.py`                            | Config validation constants (`CONFIG_SCHEMA`, `VALID_ALGORITHMS`, `INSTRUMENT_SCHEMA`), not external API schemas. 5 consumers. UCI already has `execution_config_schema.py` partially duplicating this. | unified-config-interface. Services own domain config in their own `config.py`.                             |
| `domain_config.py`                                 | Confirmed orphan -- file is a deprecation note. Zero consumers.                                                                                                                                         | DELETE                                                                                                     |
| `log_level.py`                                     | `LogLevel` StrEnum -- cross-cutting utility, not an API contract. 20 service consumers.                                                                                                                 | unified-trading-library                                                                                    |
| `quota_types.py`                                   | `GcpQuotaUsage`, `AwsServiceQuota`, `ComputeType`, `VmQuotaShape` -- cloud provider raw + canonical schemas.                                                                                            | SPLIT: AWS to `external/aws/`, GCP to `external/gcp/`, `ComputeType` to `canonical/domain/infrastructure/` |
| `venue_rate_limits.py`                             | Per-venue rate limit specs -- IS provider metadata, grouped with config instead of registry.                                                                                                            | `registry/venue_rate_limits.py`                                                                            |
| `provider_modes.py` + `provider_api_versions.yaml` | Provider mode resolution -- this IS external provider metadata.                                                                                                                                         | Stays in `config/`                                                                                         |

### c) Hard-to-navigate `canonical/normalize/`

- 22 submodules, 338 exported symbols, 728-line `__init__.py`
- Organized by OUTPUT domain (tickers, orderbooks, trades) not by INPUT source
- **But the functions ARE venue-specific**: `normalize_binance_ticker()`, `normalize_kraken_orderbook()`
- Developer working on Binance must search across `tickers.py`, `orderbooks.py`, `trades.py`, `cefi_extended.py`
- Small number of truly generic utilities (side normalization, symbol formatting) mixed with venue-specific code

### d) Scattered mappings

- `canonical_mappings.py` (465 lines): `DATA_SOURCE_TO_VENUES`, `SYMBOL_MAPPINGS` -- global mappings for some venues but
  not others
- Per-venue symbol mappings should live WITH the venue in `external/{source}/mappings.py`
- Cross-venue lookups ("which venues cover BTC-USDT?") are a registry concern

### e) Canonical not organized by interface domain

- `canonical/domain/` has 14+ files that don't map cleanly to the interface catalog
- Floating files at canonical root: `execution.py`, `odds.py`, `options.py`, `spread.py`
- Cross-cutting concerns (errors, rate limits, latency, connectivity) mixed with domain types
- An interface developer has no clear "go to this directory for your domain"

### f) No domain-capability bridge between external sources and canonical

- An interface developer doesn't know which Binance schemas are market-relevant vs execution-relevant
- No registry metadata declares "Binance provides market + execution + reference + position data"
- The "universe" of what is canonically expressible is implicit, not declared

---

## 3. Interface Catalog and Tier Architecture

### Tier model

```
T0: Primitives (no UAC dependency in production)
    unified-cloud-interface, unified-config-interface, unified-events-interface

T1: Core shared library
    unified-trading-library (wraps T0 with mode-aware routing; every service uses this)

T2: Interfaces (external data IO via UAC) + Domain libraries
    Interfaces: UMI, URDI, USRI, UTEI, USEI, UDEI, UPI, UFI
    Libraries: unified-feature-calculator-library, unified-feature-orchestration-library,
               execution-algo-library, matching-engine-library

T3: Services (use UTL for infrastructure, use T2 for domain data)
    All *-service repos

Contracts (consumed at all tiers):
    unified-api-contracts (external schemas + canonical)
    unified-internal-contracts (internal cross-service schemas)
```

### Interface catalog (9 interfaces)

| #   | Interface                                         | Domain                 | Data nature                                                                                   | Tier |
| --- | ------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------- | ---- |
| 1   | unified-market-interface (UMI)                    | Market/tick data       | Streaming: tickers, orderbooks, candles, funding rates; odds for sports; pool prices for DeFi | T2   |
| 2   | unified-reference-data-interface (URDI)           | Financial reference    | Slow-changing: instruments, fee schedules, venue metadata, expiry cycles                      | T2   |
| 3   | **unified-sports-reference-interface (USRI)** NEW | Sports reference       | Event-driven: fixtures, leagues, teams, players, bookmaker registry                           | T2   |
| 4   | unified-trade-execution-interface (UTEI)          | CeFi/TradFi execution  | Actionable: orders, fills, amendments                                                         | T2   |
| 5   | unified-sports-execution-interface (USEI)         | Sports execution       | Actionable: bet orders, back/lay fills                                                        | T2   |
| 6   | unified-defi-execution-interface (UDEI)           | DeFi execution         | Actionable: swaps, lend/borrow, stake/unstake                                                 | T2   |
| 7   | unified-position-interface (UPI)                  | Position/balance state | State: balances, exposure, liquidation-as-position-event                                      | T2   |
| 8   | **unified-features-interface (UFI)** NEW          | Features/derived data  | Processed: pre-computed indicators, feature vectors                                           | T2   |
| 9   | unified-cloud-interface (UCI)                     | Cloud infrastructure   | Operational: storage, pubsub, secrets, quota, compute                                         | T0   |

### Cloud interface positioning

UCI stays T0. Cloud SDK schemas in UAC (`external/aws/`, `external/gcp/`) are for contract validation and VCR testing --
same as all UAC schemas. UCI production code uses actual SDK libraries (boto3, google-cloud-\*) directly. No production
dependency on UAC. UCI tests CAN import from UAC for schema validation (test-only dependencies don't affect tier).

Services never import UCI directly. UTL adapter facade handles mode-aware routing: mock -> local emulator/filesystem;
real+GCP -> GCS/PubSub/BigQuery via UCI; real+AWS -> S3/SQS/DynamoDB via UCI; local -> local emulators. Services import
config and events directly from T0 (universal, no routing needed).

### Features stack

| Layer                 | Repo name                                         | Role                                                                                                  |
| --------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| External data IO      | **unified-features-interface** NEW                | Interface (T2): thin adapters to external feature/derived data sources via UAC schemas                |
| Pure calculators      | **unified-feature-calculator-library** (existing) | Library (T2): stateless pure calculation functions, shared across all feature services                |
| Feature orchestration | **unified-feature-orchestration-library** NEW     | Library (T2): pipeline routing, batch/live handlers, feature registry. Domain-specific UTL extension. |

Feature service dependency tree:

```
features-volatility-service (T3)
  -> unified-trading-library (T1)              # Infrastructure: config, events, cloud routing
  -> unified-features-interface (T2)            # External: derived data sources
  -> unified-feature-calculator-library (T2)    # Math: pure calculations
  -> unified-feature-orchestration-library (T2) # Glue: pipeline routing, handlers
  -> unified-internal-contracts                 # Schemas: cross-service contracts
  -> unified-api-contracts                      # Schemas: transitive via interface
```

---

## 4. Target Architecture

### 4a. UAC directory structure

```
unified_api_contracts/
+-- canonical/                             # Canonical domain output schemas
|   +-- domain/                            # Interface-domain-aligned
|   |   +-- market/                        # UMI: tickers, trades, orderbooks, candles, odds, spread
|   |   +-- reference/                     # URDI: instruments, fees, venue metadata
|   |   +-- sports_reference/              # USRI: fixtures, leagues, teams, players, bookmakers
|   |   +-- execution/                     # UTEI/USEI/UDEI
|   |   |   +-- base.py                    # CanonicalOrder, CanonicalFill, OrderStatus
|   |   |   +-- trade.py                   # CeFi/TradFi-specific execution types
|   |   |   +-- sports.py                  # BetOrder, BetExecution
|   |   |   +-- defi.py                    # SwapExecution, LendExecution
|   |   +-- position/                      # UPI: balances, exposure, position state
|   |   +-- features/                      # UFI: feature vectors, indicators
|   |   +-- infrastructure/                # UCI: quota, storage, compute (test schemas)
|   |   +-- derivatives/                   # Options, futures canonical types
|   |   +-- onchain/                       # On-chain analytics types
|   |
|   +-- crosscutting/                      # Cross-domain (used by ALL interfaces)
|       +-- errors/                        # Error classification + per-domain errors
|       |   +-- _canonical.py, _types.py, cefi.py, defi.py, sports.py, altdata.py
|       +-- rate_limits.py                 # VenueRateLimitSpec, HttpRateLimitHeaders
|       +-- latency.py                     # LatencyPercentile, SubMillisecondLatencyRecord
|       +-- connectivity.py                # WebSocket lifecycle events, health
|
+-- external/                              # FLAT: one directory per data source
|   +-- binance/                           # schemas.py, normalize.py, mappings.py, examples/, mocks/
|   +-- aws/                               # Cloud (was cloud_sdks/aws/): s3.py, ec2.py, ...
|   +-- gcp/                               # Cloud (was cloud_sdks/gcp/): bigquery.py, ...
|   +-- flashbots/                         # Was mev/; now flat
|   +-- cryptoquant/                       # Was onchain/; now flat
|   +-- oddsjam/                           # Was sports/sources/; now flat
|   +-- prime_broker/                      # Stays (cross-provider canonical)
|   +-- ... (every source flat, ~80+ dirs)
|
+-- normalize_utils/                       # ONLY truly shared normalization primitives
|   +-- sides.py, symbols.py, timestamps.py, common.py
|
+-- registry/                              # Provider metadata + capability
|   +-- capability.py                      # CapabilityRecord + domain-coverage declarations
|   +-- endpoint_registry.py               # EndpointSpec, ENDPOINT_REGISTRY
|   +-- venue_constants.py                 # Venue enums, AlphaProfile, etc.
|   +-- venue_manifest.py                  # VenueContract metadata (was external/venue_manifest/)
|   +-- venue_rate_limits.py               # Per-venue rate limits (was config/)
|   +-- endpoints.py                       # BASE_URLS, ENDPOINT_SCHEMA_MAP
|
+-- config/                                # ONLY external provider configuration
|   +-- provider_api_versions.yaml
|   +-- provider_modes.py
|
+-- testing/                               # VCR infrastructure
|   +-- vcr_endpoints.py, detect_cassette_drift.py, fault_injection.py,
|   +-- network_block_plugin.py, conftest_helper.py
|
+-- __init__.py                            # Clean public API: canonical + crosscutting + registry
```

### 4b. Canonical domain model

The canonical schemas define the **universe** of what is expressible. Each external source fills what it can. The
registry declares coverage. Where data does not exist for a source, it does not exist -- no stubs, no fake data.

**Domain types** (mirror interfaces):

| Canonical domain           | Interface(s)     | Key types                                                                                                                                       |
| -------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `domain/market/`           | UMI              | CanonicalTicker, CanonicalTrade, CanonicalOrderBook, CanonicalOHLCV, CanonicalFundingRate, CanonicalSpread, CanonicalOdds, CanonicalLiquidation |
| `domain/reference/`        | URDI             | CanonicalInstrument, FeeSchedule, VenueMetadata                                                                                                 |
| `domain/sports_reference/` | USRI             | CanonicalFixture, CanonicalLeague, CanonicalTeam, CanonicalPlayer, BookmakerRegistry                                                            |
| `domain/execution/`        | UTEI, USEI, UDEI | Shared base (CanonicalOrder, CanonicalFill) + trade/sports/defi extensions                                                                      |
| `domain/position/`         | UPI              | CanonicalPosition, CanonicalBalance, CanonicalAccountState, CanonicalMarginState                                                                |
| `domain/features/`         | UFI              | SportsFeatureVector, derived indicators                                                                                                         |
| `domain/infrastructure/`   | UCI (test)       | ComputeType, CanonicalQuotaUsage                                                                                                                |
| `domain/derivatives/`      | UMI/UTEI         | OptionChainSnapshot, NormalizedStrikeCoordinate                                                                                                 |
| `domain/onchain/`          | UMI              | On-chain analytics types                                                                                                                        |

**Cross-cutting types** (span ALL interfaces):

| Location                       | What                                                                                                | Used by                 |
| ------------------------------ | --------------------------------------------------------------------------------------------------- | ----------------------- |
| `crosscutting/errors/`         | CanonicalError, VenueErrorClassification, VENUE_ERROR_MAP, classify_venue_error + per-domain errors | Every interface adapter |
| `crosscutting/rate_limits.py`  | VenueRateLimitSpec, HttpRateLimitHeaders                                                            | Every interface adapter |
| `crosscutting/latency.py`      | LatencyPercentile, SubMillisecondLatencyRecord, NetworkJitterMetric                                 | Every interface adapter |
| `crosscutting/connectivity.py` | WebSocket lifecycle events (connect, disconnect, ping, pong, subscribe)                             | Streaming adapters      |

**Execution commonality**: Trade fills, bet fills, DeFi swaps share a common base in `domain/execution/base.py`. Domain
extensions live alongside. Services like risk-and-exposure can consume execution results generically via the base types.

### 4c. Registry domain-capability model

The registry bridges flat-per-source externals and domain-organized canonicals:

```yaml
binance:
  domains:
    market: [ticker, trade, orderbook, klines, funding_rate]
    execution: [order, fill, amendment]
    reference: [exchange_info, instruments]
    position: [account, balance, margin_state]
  crosscutting: [errors, rate_limits, latency, connectivity]
  supports_live: true
  supports_batch: true
  supports_testnet: true
  auth_scope: [read, trade, withdraw]

betfair:
  domains:
    market: [odds, live_match_state]
    execution: [bet_order, bet_fill]
    sports_reference: [fixtures, markets]
  crosscutting: [errors, rate_limits]
  supports_live: true
  supports_batch: false

fred:
  domains:
    reference: [interest_rates, economic_indicators]
  crosscutting: [errors, rate_limits]
  supports_live: false
  supports_batch: true
```

Enables: interface developers check registry for domain relevance; coverage matrix shows gaps; capability checks
validate mode/env/auth before network call.

### 4d. Config ownership model

| Config type                 | Owner                            | Rationale                                                     |
| --------------------------- | -------------------------------- | ------------------------------------------------------------- |
| External provider metadata  | **UAC** `config/`                | `provider_api_versions.yaml`, `provider_modes.py`             |
| Config validation constants | **unified-config-interface**     | `VALID_ALGORITHMS`, `CONFIG_SCHEMA`, etc.                     |
| Cross-service mode enums    | **UIC** `modes.py`               | DataMode, RuntimeMode, CloudProvider, PhaseMode, MockScenario |
| Canonical env var names     | **UIC** `env_canon.py`           | EnvVars class                                                 |
| Service-specific config     | **Each service** own `config.py` | Domain-specific config schemas                                |
| LogLevel enum               | **unified-trading-library**      | Cross-cutting utility (20 consumers)                          |

**Principle:** UAC and UIC have zero service-specific config schemas.

### 4e. What moves OUT of UAC

| Current location               | Destination                                                                                              | Rationale                                                                 |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `config/trading_validation.py` | unified-config-interface                                                                                 | Config validation constants; UCI already has `execution_config_schema.py` |
| `config/log_level.py`          | unified-trading-library                                                                                  | Cross-cutting utility (20 service consumers)                              |
| `config/quota_types.py`        | SPLIT: AWS to `external/aws/`, GCP to `external/gcp/`, ComputeType to `canonical/domain/infrastructure/` | Cloud provider raw/canonical types                                        |
| `config/domain_config.py`      | DELETE                                                                                                   | Confirmed orphan                                                          |
| `shared/__init__.py`           | DELETE                                                                                                   | Only re-exports                                                           |
| `schemas/__init__.py`          | DELETE                                                                                                   | Re-exports from canonical/domain                                          |
| `external/venue_manifest/`     | `registry/venue_manifest.py`                                                                             | Metadata, not a data source                                               |
| `external/sports/canonical/`   | `canonical/domain/sports_reference/`                                                                     | Canonical types belong in canonical                                       |

### 4f. What restructures WITHIN UAC

| Current                                                            | Target                                                                | Change                              |
| ------------------------------------------------------------------ | --------------------------------------------------------------------- | ----------------------------------- |
| `canonical/normalize/*.py` (22 modules, 338 symbols)               | `external/{source}/normalize.py` + `normalize_utils/`                 | Co-locate normalization with source |
| `canonical/canonical_mappings.py` (465 lines)                      | `external/{source}/mappings.py` + `registry/` cross-venue lookups     | Co-locate mappings with source      |
| `canonical/execution.py`, `odds.py`, `options.py`, `spread.py`     | Into `canonical/domain/{domain}/`                                     | No floating files at canonical root |
| `canonical/errors/`                                                | `canonical/crosscutting/errors/`                                      | Errors are cross-cutting            |
| `canonical/domain/rate_limits.py`, `latency.py`, `connectivity.py` | `canonical/crosscutting/`                                             | Cross-cutting types separated       |
| `external/cloud_sdks/{aws,gcp}/`                                   | `external/aws/`, `external/gcp/`                                      | Flatten one level                   |
| `external/mev/`                                                    | `external/flashbots/`, `external/mev_share/`, `external/mev_blocker/` | One source per directory            |
| `external/onchain/`                                                | `external/cryptoquant/`                                               | Flatten                             |
| `external/sports/sources/{provider}/`                              | `external/{provider}/`                                                | Flatten into main external          |

### 4g. Import patterns after restructure

```python
# Interface adapter (e.g., UMI Binance adapter):
from unified_api_contracts.external.binance.schemas import BinanceTicker, BinanceOrderBook
from unified_api_contracts.external.binance.normalize import normalize_binance_ticker
from unified_api_contracts.canonical.domain.market import CanonicalTicker
from unified_api_contracts.canonical.crosscutting.errors import classify_venue_error

# Service consuming canonical output (never touches external/):
from unified_api_contracts.canonical.domain.market import CanonicalTicker, CanonicalTrade
from unified_api_contracts.canonical.domain.execution import CanonicalOrder, CanonicalFill

# Capability check in adapter:
from unified_api_contracts.registry.capability import resolve_capability

# Cross-cutting types in any adapter:
from unified_api_contracts.canonical.crosscutting.rate_limits import VenueRateLimitSpec
from unified_api_contracts.canonical.crosscutting.latency import LatencyPercentile
```

### 4h. VCR / cassette story

Cassettes stay in `external/{source}/mocks/`. Drift detection walks `external/*/mocks/`. Replay workflow validates each
cassette against co-located `schemas.py`. Everything about a source is in one place: raw schemas, normalization,
mappings, examples, cassettes.

External replay validates against UAC schemas. Internal replay validates against UIC schemas. Drift recording creates
PRs with cassette/schema diff summary, labeled `schema-impact`, requiring manual approval. Never auto-merge
schema-affecting updates.

---

## 5. Migration Strategy

### Phase 1: UAC structural foundations (no import changes)

- Create `normalize_utils/` extracting shared primitives from `canonical/normalize/`
- Create `registry/venue_manifest.py` from `external/venue_manifest/`
- Move `config/venue_rate_limits.py` to `registry/`
- Delete orphan `config/domain_config.py`
- Restructure `external/cloud_sdks/` to `external/aws/` and `external/gcp/`

### Phase 2: Canonical domain reorganization

- Reorganize `canonical/domain/` into interface-aligned sub-packages: `market/`, `reference/`, `sports_reference/`,
  `execution/` (base + trade/sports/defi), `position/`, `features/`, `infrastructure/`, `derivatives/`, `onchain/`
- Create `canonical/crosscutting/` with `errors/`, `rate_limits.py`, `latency.py`, `connectivity.py`
- Move floating files: `execution.py` -> `domain/execution/base.py`, `odds.py` -> `domain/market/`, `options.py` ->
  `domain/derivatives/`, `spread.py` -> `domain/market/`
- Move `canonical/errors/` -> `canonical/crosscutting/errors/`
- Move `canonical/domain/rate_limits.py`, `latency.py`, `connectivity.py` -> `canonical/crosscutting/`
- Move `external/sports/canonical/` -> `canonical/domain/sports_reference/`

### Phase 3: Per-source normalization co-location

- Extract venue-specific normalizers from `canonical/normalize/*.py` into `external/{source}/normalize.py`
- Each `normalize.py` imports shared utilities from `normalize_utils/`
- Keep `canonical/normalize/__init__.py` as temporary re-export facade
- Move per-source mappings from `canonical_mappings.py` to `external/{source}/mappings.py`
- Keep cross-venue lookups in `registry/`

### Phase 4: Flatten non-standard external directories

- `external/mev/` -> `external/flashbots/`, `external/mev_share/`, `external/mev_blocker/`
- `external/onchain/` -> `external/cryptoquant/`
- `external/sports/sources/{provider}/` -> `external/{provider}/`
- Delete empty shells after moves

### Phase 5: Move non-API-contract modules out

- `config/trading_validation.py` -> unified-config-interface
- `config/log_level.py` -> unified-trading-library
- `config/quota_types.py` -> SPLIT: AWS to `external/aws/`, GCP to `external/gcp/`, ComputeType to
  `canonical/domain/infrastructure/`
- Delete `shared/__init__.py` and `schemas/__init__.py`

### Phase 6: Import surface cleanup and enforcement

- Update `__init__.py` to export canonical domain + crosscutting + registry only
- Update all interface adapter imports (~40+ files across 7 interfaces)
- Remove `canonical/normalize/__init__.py` facade
- Add QG linter rule: services must not import from `external/{source}/`

### Phase 7: Registry + domain-capability model

- Build capability registry in `registry/capability.py`
- Domain-coverage dimension: per-source domains + cross-cutting + mode/env/auth
- Backfill all current providers
- Coverage matrix generation script
- Integrate into adapter preflight checks

### Phase 8: Features stack (new repos)

- Create **unified-features-interface**: external feature/derived data IO via UAC
- Create **unified-feature-orchestration-library**: pipeline routing, handlers, feature registry
- Update workspace-manifest.json
- Migrate feature-service UAC interactions

### Phase 9: Sports reference interface (new repo)

- Create **unified-sports-reference-interface**: fixtures, leagues, teams, players, bookmakers
- Update workspace-manifest.json
- Migrate sports reference data consumption

### Phase 10: Replay and drift infrastructure (from Plan 2)

- UIC internal endpoint registry (Plan 2 R2)
- Remove internal endpoint ownership from UAC VCR registry (Plan 2 R3)
- PM reusable replay workflow `contract-replay.yml` (Plan 2 R4): external->UAC, internal->UIC, fail on mismatch
- Nightly drift recording `contract-drift-record.yml` (Plan 2 R6): staging only, approval-gated PRs
- VCR capability assertions (Plan 1 P7)
- Lane metrics for smoke/replay/live/drift (Plan 2 R8)
- Least-privilege secrets for recorder jobs (Plan 2 R7)

### Phase 11: Runtime guardrails and service adoption (from Plan 1)

- Fail-fast error classes in UTL: UnsupportedModeError, UnsupportedEnvironmentError, ApiKeyScopeMismatchError,
  UnsupportedOperationError, CapabilityResolutionError (Plan 1 P2)
- Preflight capability checks in all interface adapters before network calls (Plan 1 P2)
- Standard raw->validate->canonical pipeline: resolve capability -> validate mode/env/auth -> resolve endpoint ->
  execute -> validate raw -> map canonical -> return (Plan 1 P3)
- Detect and remove duplicate raw->canonical mapping logic across interfaces (Plan 1 P3)
- Refactor services to canonical-only consumption (Plan 1 P4)
- Publish SSOT docs in codex (Plan 1 P8)
- QG validators for capability coverage, unsupported-combo guardrails, duplicate detection (Plan 1 P8)
- Matrix tests for mode/env/auth compatibility (Plan 1 P7)

---

## 6. Key Architectural Decisions

- **Flat external, always**: Every external data source gets exactly one directory. No nesting, no domain grouping. The
  directory name IS the source identifier used in capability registry, cassette paths, and adapter resolution.
- **Normalization co-located with source**: `external/binance/normalize.py` is the single place to find all Binance
  normalization. Shared primitives live in `normalize_utils/`.
- **Canonical mirrors interfaces**: `canonical/domain/` sub-packages map to the interface catalog. An interface
  developer navigates by data domain. Cross-cutting types in `canonical/crosscutting/` are available to all interfaces.
- **The universe concept**: Canonical schemas define the full universe of what is expressible. Each external source
  fills what it can. The registry declares coverage. The coverage matrix makes gaps visible. This makes deduplication
  and missing-normalizer detection easy.
- **Execution commonality**: Trade fills, bet fills, DeFi swaps share a common base in `domain/execution/base.py`.
  Domain extensions live alongside. Services can consume generically via base types.
- **Cloud APIs are external APIs**: AWS and GCP follow the same raw->normalize->canonical pattern. They stay in UAC as
  `external/aws/` and `external/gcp/`. UCI is the thin T0 adapter with no production UAC dependency. UCI tests validate
  against UAC schemas.
- **UTL is the central router**: Services call UTL for infrastructure (storage, pubsub, secrets). UTL routes to UCI
  based on mode/provider. Services never import UCI directly. Config and events are the only T0 direct imports.
- **Config ownership**: UAC has zero service config. UIC has only cross-service mode enums. Config validation framework
  in unified-config-interface. Services own domain config in their own `config.py`.
- **Features stack**: Three layers (interface + calculator + orchestration) parallel the market data stack. All feature
  services also use UTL for infrastructure. Orchestration library is the domain-specific UTL extension, not a
  replacement.
- **Sports reference separated**: Sports reference data has fundamentally different triggers, cadence, and data shapes
  from financial reference data. Separate interface, shared canonical contract layer.
- **Registry bridges external and canonical**: Domain-capability model declares which canonical domains each source
  serves. Coverage matrix scripts make gaps visible.
- **No backward-compat shims**: Per `delete-deprecated.mdc`, old import paths get deleted, not aliased. Migration is
  atomic per phase. Safe rollback via git history.

---

## 7. Standard Execution Flow (Post-Restructure)

For any interface adapter making an external API call:

1. Resolve capability record from UAC registry (`registry/capability.py`)
2. Validate requested mode/env/auth against capability (fail-fast with explicit error)
3. Resolve endpoint from capability metadata
4. Execute API call in interface adapter
5. Validate raw payload against UAC raw schema (`external/{source}/schemas.py`)
6. Map raw payload to UAC canonical schema (`external/{source}/normalize.py`)
7. Return canonical object to caller/service

Services consume canonical types only. They never touch raw schemas or normalization.

---

## 8. Acceptance Criteria

- Every external source has one flat directory with co-located schemas, normalize, mappings, examples, mocks
- `canonical/domain/` sub-packages map to interface catalog
- `canonical/crosscutting/` contains errors, rate_limits, latency, connectivity only
- No floating `.py` files at `canonical/` root
- Registry capability model declares domain + cross-cutting coverage for all active sources
- Coverage matrix script generates gap report
- Every interface resolves provider endpoint via capability metadata
- Every interface rejects unsupported mode/env/auth pre-call with explicit error
- Services do not import from `external/{source}/` (QG enforced)
- No duplicate raw->canonical mapping logic across interfaces
- `config/` contains only `provider_api_versions.yaml` and `provider_modes.py`
- `shared/` and `schemas/` facades deleted
- VCR replay validates raw schema and canonical output invariants
- Drift recording creates approval-gated PRs for schema changes
- unified-features-interface, unified-feature-orchestration-library, unified-sports-reference-interface created
- Public import paths documented in codex and QG enforced

---

## 9. Non-Goals

- Backward-compatibility shims, legacy aliases, or try/except import fallbacks for old paths
- Dual old/new mapping paths or normalize paths retained after migration
- Service-level schema ownership that belongs in UAC/UIC
- Service config schemas in UAC or UIC (services own their own config.py)
- Auto-merging schema-affecting drift updates (always approval-gated)
- Monorepo consolidation (multi-repo architecture stays)
- Moving UCI to T2 or adding production UAC dependency to UCI (UCI stays T0)
- Services importing UCI directly (always route through UTL adapter facade)
- Replacing UTL with unified-feature-orchestration-library (orchestration is a domain extension, not a replacement)
- Merging URDI and USRI into one interface (different triggers, cadence, data shapes)
- Keeping domain-grouped external directories (mev/, onchain/, sports/sources/) after Phase 4
- Keeping normalization organized by output domain after Phase 3 (co-locate with source)
- Building new services as part of this plan (this is architecture/contract/library layer only)
- Auto-promoting any repo to v1.0.0 (requires human approval per semver rules)
- Changing UIC cross-service mode enums location (DataMode, RuntimeMode stay in UIC modes.py)
- Keeping venue_manifest/ or venue_rate_limits in their current locations
- Creating optional-dependencies groups in pyproject.toml for new repos (flat deps only)
- Implementing runtime features (circuit breakers, health endpoints) -- separate plans own those

---

## 10. Manifest Schema Evolution

### 10a. Split arch_tier into tier + role

Current arch_tier conflates conceptual layer with repo type. Split into two fields:

| Field                                 | Type              | Values                                                                                          | Purpose                                               |
| ------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| tier                                  | integer or null   | 0, 1, 2, 3, null (for infra/test)                                                               | Conceptual layer for humans + tier-gate validator     |
| role                                  | string            | contracts, primitive, library, interface, domain-client, service, api, ui, infrastructure, test | Repo kind for SVG styling, rollout template selection |
| Proposed assignments:                 |                   |                                                                                                 |                                                       |
| Repo                                  | Current arch_tier | New tier                                                                                        | New role                                              |
| ---                                   | ---               | ---                                                                                             | ---                                                   |
| unified-api-contracts                 | "0"               | 0                                                                                               | contracts                                             |
| unified-internal-contracts            | "0"               | 0                                                                                               | contracts                                             |
| unified-events-interface              | "0"               | 0                                                                                               | primitive                                             |
| unified-cloud-interface               | "0"               | 0                                                                                               | primitive                                             |
| unified-config-interface              | "1"               | 0                                                                                               | primitive                                             |
| unified-trading-library               | "1"               | 1                                                                                               | library                                               |
| unified-market-interface              | "2"               | 2                                                                                               | interface                                             |
| unified-reference-data-interface      | "1"               | 2                                                                                               | interface                                             |
| unified-sports-reference-interface    | NEW               | 2                                                                                               | interface                                             |
| unified-trade-execution-interface     | "2"               | 2                                                                                               | interface                                             |
| unified-sports-execution-interface    | "1"               | 2                                                                                               | interface                                             |
| unified-defi-execution-interface      | "2"               | 2                                                                                               | interface                                             |
| unified-position-interface            | "2"               | 2                                                                                               | interface                                             |
| unified-features-interface            | NEW               | 2                                                                                               | interface                                             |
| unified-ml-interface                  | "2"               | 2                                                                                               | interface                                             |
| execution-algo-library                | "0"               | 2                                                                                               | library                                               |
| matching-engine-library               | "0"               | 2                                                                                               | library                                               |
| unified-feature-calculator-library    | "2"               | 2                                                                                               | library                                               |
| unified-feature-orchestration-library | NEW               | 2                                                                                               | library                                               |
| unified-domain-client                 | "3"               | 3                                                                                               | domain-client                                         |
| unified-trading-ui-auth               | "ui"              | 3                                                                                               | library                                               |
| unified-trading-ui-kit                | "ui"              | 3                                                                                               | library                                               |
| All \*-service                        | "service"         | 3                                                                                               | service                                               |
| All \*-api                            | "api"             | 3                                                                                               | api                                                   |
| All \*-ui                             | "ui"              | 3                                                                                               | ui                                                    |
| unified-trading-pm                    | "devops"          | null                                                                                            | infrastructure                                        |
| unified-trading-codex                 | "infrastructure"  | null                                                                                            | infrastructure                                        |
| ibkr-gateway-infra                    | "infrastructure"  | null                                                                                            | infrastructure                                        |
| system-integration-tests              | "integration"     | null                                                                                            | test                                                  |

### 10b. Three relationship types

| Relationship          | Manifest field                       | Drives                                                    | Rendered in SVG                         |
| --------------------- | ------------------------------------ | --------------------------------------------------------- | --------------------------------------- |
| Code dependency       | dependencies[]                       | quickmerge cascade, topological build order, CI dep-clone | Solid arrow                             |
| Workspace tooling     | workspace_infrastructure.setup_repos | setup-workspace.sh, cursor rules propagation              | Dashed arrow from floating PM/Codex box |
| Runtime connection    | runtime_clients[] on infra repos     | Runtime topology docs, data-flow DAG, deployment ordering | Dotted arrow labeled "runtime"          |
| Add to manifest root: |                                      |                                                           |                                         |

```json
"workspace_infrastructure": {
  "setup_repos": ["unified-trading-pm", "unified-trading-codex"],
  "note": "Cloned by every repo via setup-workspace.sh for rules, scripts, standards. Not code deps."
}

Add to ibkr-gateway-infra:

"runtime_clients": [
  "unified-market-interface",
  "unified-reference-data-interface",
  "unified-trade-execution-interface"
]

### 10c. Dependency graph corrections
UTL (remove T2 deps -- tier violation): REMOVE: unified-market-interface, unified-trade-execution-interface KEEP: unified-cloud-interface, unified-config-interface, unified-events-interface, unified-internal-contracts

Interfaces (remove direct T0 primitive deps -- services get these via UTL): UMI REMOVE: unified-config-interface, unified-cloud-interface UTEI REMOVE: unified-config-interface, unified-sports-execution-interface URDI REMOVE: unified-cloud-interface UMLI REMOVE: unified-config-interface, unified-cloud-interface All interfaces KEEP: unified-api-contracts, unified-internal-contracts, unified-events-interface

UDC (remove direct T0 deps): REMOVE: unified-config-interface, unified-cloud-interface KEEP: unified-trading-library, unified-api-contracts, unified-internal-contracts, unified-ml-interface

UFCL (simplify): REMOVE: unified-config-interface, unified-events-interface KEEP: unified-trading-library

Service dependency template (replaces current per-service sprawl): Every service: unified-trading-library + domain interfaces as needed + UAC/UIC as needed Feature services: unified-trading-library + unified-feature-calculator-library + unified-feature-orchestration-library + UIC REMOVE from all services: explicit unified-config-interface, unified-cloud-interface, unified-events-interface

### 10d. Topological build order (derived, not stored)
After corrections, topologicalOrder.levels becomes: Level 0: UAC, UEI, EAL, MEL Level 1: UIC Level 2: UCI Level 3: UCfgI Level 4: UTL Level 5: UMI, URDI, USRI, UTEI, USEI, UDEI, UPI, UFI, UMLI Level 6: UFCL Level 7: UFOL Level 8: UDC Level 9: All services, APIs Level 10: UIs (those depending on APIs)

### 10e. Tier-gate invariant (enforced by validator)
For each repo R with tier=N (where N is not null): For each dep D in R.dependencies[]: D.tier must be <= N (or null for infra) Violation = QG failure

This catches: T1 depending on T2 (the UTL bug), T0 depending on T2, etc.

### 10f. SVG rendering rules
Group nodes by tier (0, 1, 2, 3) with labeled subgraphs
Contracts (tier=0, role=contracts) in own box at top
Infrastructure (tier=null) in own box at top alongside contracts
Solid arrows: code dependencies (from dependencies[])
Dashed arrows: workspace tooling (from workspace_infrastructure.setup_repos to all)
Dotted arrows: runtime connections (from runtime_clients[])
Node shape: rect for libraries/interfaces, rounded for services/APIs, hexagon for infra
Three new repos highlighted with border

---
```
