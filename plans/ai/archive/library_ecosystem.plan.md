---
name: "Plan 2 — Library Ecosystem: New Libraries + Stage 2 Split"
overview: "Create new libraries, complete interface coverage across all trading domains, split unified-trading-services into unified-cloud-interface (Tier 0) + unified-trading-services (Tier 1, renamed), update all SSOT docs, align all service pyproject.toml files. REFACTOR-ONLY: This plan makes structural code and dependency changes only. Do NOT run full test suites mid-refactor. Full testing runs ONLY after this plan's structural work is complete (see Plan 3 Testing Phase). Bottom-up ordering: UCLI created first, then Tier 2 libs migrate to UCLI, then services aligned, then rename. AWS implementations are NEVER removed — cloud-agnostic is the target. Absorbs: ucs_quickmerge_unblock Stage 2 (PRs E–G), io_interface_architecture ALL phases, architecture_finalization SSOT items. Starts only after Plan 1 (Library Foundation) fully merges. THREE-PHASE EXECUTION: Phase 1 = ALL code changes (no commits, no quickmerge, no tests — runs in parallel with Plan 1 Phase 1 where possible). Phase 2 = Commit phase: quickmerge bottom-up by tier after ALL repos are code-complete, max 6 parallel. Phase 3 = Testing in Plan 3. ADDITIONAL SCOPE (2026-02-26): unified-domain-client renamed to unified-domain-client (it is a data access client library, not a service). New Phase 4 todos added: udc-path-registry (centralized PathRegistry for all 14 datasets, fixes P0 hardcoded project ID violations), udc-readers-writers (cloud-agnostic readers/writers via UCLI), udc-external-tables (BigQuery external tables + AWS Athena, opt-in, non-breaking)."
todos:
  - id: pr-e-ucli-create
    content: "PR E — Create unified-cloud-interface repo: NOTE — Plan 1 PR B3 completes the AWS plumbing in UCS first. PR E MOVES (not rebuilds) the following from UCS to UCLI: StorageClient(ABC) + StorageBucket(ABC) + StorageBlob(ABC) + BlobMetadata + GCSStorageClient + S3StorageClient (both full implementations exist in UCS after Plan 1 merges); SecretClient(ABC) + SecretMetadata + CachingSecretClient + GCPSecretClient + AWSSecretClient (all fully implemented after Plan 1 PR B3); QueueClient(ABC) + PubSubQueueClient + SQSQueueClient (new in Plan 1 PR B3); factory functions get_storage_client(), get_secret_client(), get_queue_client() (already exist in client_factory.py, move to factory.py in UCLI). NEW in UCLI (not in UCS): LoggingProvider ABC + GCPLoggingProvider + AWSCloudWatchProvider; LocalStorageProvider (pathlib-based, for tests/local dev without cloud creds); LocalSecretProvider (env var-backed); CacheProvider ABC + RedisProvider implementation (re-implement from redis_cache.py/redis_secret_manager.py that a pre-plan agent wrote to UCS — now deleted; re-implement in UCLI); AuthProvider ABC + GoogleOIDCAuth (re-implement from auth/oidc_auth.py — now deleted; OIDC auth is a cloud SDK wrapper, correct home is UCLI). Zero inter-library dependencies. Add cloudbuild.yaml, scripts/quickmerge.sh, pyrightconfig.json. Publish to Artifact Registry. Bump version 0.0.0 → 1.0.0."
    status: completed
  - id: batch1-api-schemas
    content: "Batch 1 Agent 2a — api-contracts Phase 1 schema expansion. See completed_notes."
    status: completed
    completed_notes: "COMPLETED AHEAD OF PLAN (audit 2026-02-26): api-contracts is already at v1.2.0 (ae8f28d). The schema expansion was done as part of Plan 1 work: derivatives schemas (FundingRate, Liquidation, SettlementPrice, OptionsChain, OptionGreeks), DeFi schemas (Swap, LiquidityPool, OraclePrice, StakingRate, LendingRate), error schemas (DatabentoError with retry_safe/reconnect classification), WebSocket schemas added. VCR cassettes not confirmed — verify if vcr/ directory exists. Order/Position schemas for Coinbase may still be missing — verify with `ls api-contracts/api_contracts/schemas/` before marking fully closed."
  - id: batch1-upi-create
    content: "Batch 1 Agent 2b — Create unified-position-interface repo (Phase 3): CanonicalBalance, CanonicalPosition, CanonicalAccountSnapshot, CanonicalSettlement schemas; BasePositionAdapter ABC; adapters for Binance, Bybit, OKX, Deribit, Hyperliquid, Upbit, IBKR, CCXT; factory.py; pyproject.toml (depends on api-contracts + unified-cloud-interface); cloudbuild.yaml, quickmerge.sh, pyrightconfig.json. NOTE: UDEI (unified-defi-execution-interface) stays separate — position-balance-monitor-service will depend on BOTH UPI (CeFi) AND UDEI (DeFi). Bump version 0.0.0 → 1.0.0."
    status: completed
    content: "Batch 1 Agent 2b — Create unified-position-interface repo (Phase 3): CanonicalBalance, CanonicalPosition, CanonicalAccountSnapshot, CanonicalSettlement schemas; BasePositionAdapter ABC; adapters for Binance, Bybit, OKX, Deribit, Hyperliquid, Upbit, IBKR, CCXT; factory.py; pyproject.toml (depends on api-contracts + unified-cloud-interface); cloudbuild.yaml, quickmerge.sh, pyrightconfig.json. NOTE: UDEI (unified-defi-execution-interface) stays separate — position-balance-monitor-service will depend on BOTH UPI (CeFi) AND UDEI (DeFi). Bump version 0.0.0 → 1.0.0."
    status: pending
  - id: batch1-umi-utei
    content: "Batch 1 Agent 3 — UMI + UTEI interface completion (parallel): Phase 2: UMI add CanonicalFundingRate, CanonicalLiquidation, CanonicalSwap, CanonicalLiquidityPool, CanonicalOraclePrice, CanonicalStakingRate, CanonicalOptionsChain schemas; add WebSocket handlers (subscribe, reconnect, backfill, dispatch) for Bybit, Coinbase, Deribit, OKX; complete Aster onchain_perps adapter. Phase 4: UTEI add WebSocket order update feeds for Binance, Bybit, OKX, Deribit, Hyperliquid with reconnect + state recovery; add CanonicalPartialFill, CanonicalOrderRejection (retry_safe), CanonicalOrderAmendment schemas; map api-contracts error schemas to retry_safe/reconnect actions per venue."
    status: pending
  - id: batch1-ssot
    content: "Batch 1 Agent 4 — SSOT + Codex alignment (parallel): (1) workspace-manifest.json: add arch_tier field (0/1/2/service/ui) to every repo entry; add tier_rules section; bump lastUpdated; (2) Create unified-trading-codex/05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md with canonical tier diagram, tier rules, allowed-imports-per-tier table, QG enforcement reference, diamond-dep note for UCLI; (3) Rewrite dependency-matrix.md: rename 'Migration Priority Tiers' → 'Service Adoption Priority', add 'Library Architecture Tiers' section at top with tier diagram and allowed deps per tier; update library descriptions for UDS (api-contracts + UCLI only), UCS (v2.2.0, no domain exports, UTS service runtime API); (4) Update codex/06-coding-standards/dependency-management.md: add 'Architecture Tier Rules' section with FORBIDDEN_IMPORT_PATTERNS; (5) Update codex Phase 6-7: fix 'unified-order-interface' → 'unified-trade-execution-interface' naming throughout; add position-interface.md; update workspace-manifest.json UPI status from future to active."
    status: pending
  - id: pr-f-tier2-migration
    content: "PR F — Tier 2 lib migration (4 parallel agents, after PR E merges): For each of UDS, UMI, UTEI, UML, UFC: switch pyproject.toml from unified-trading-services → unified-cloud-interface for raw cloud I/O; update [tool.uv.sources] to point to ../unified-cloud-interface; update source code to replace 'from unified_trading_services import get_storage_client' with 'from unified_cloud_interface import get_storage_client' etc. UCS remains as a transitive dep of UTS (services continue to use UCS until PR G rename). Bump each library minor version."
    status: completed
  - id: pr-f-service-enforcement
    content: "PR F Service Enforcement (parallel with PR F, io_interface Phase 6): MTDH: remove app/venues/ and engine/venues/; wire all venue adapters through unified_market_interface; execution-services: delete legacy adapters/venues/ ExternalVenueAdapter code; verify all order execution routes through UTEI; position-balance-monitor-service: add unified-position-interface dependency; replace direct venue calls with BasePositionAdapter (UPI); keep UDEI dependency alongside UPI (ADR: two separate adapters for CeFi + DeFi)."
    status: pending
  - id: pr-f-feature-calc-fix
    content: "PR F Feature Calc Fix (parallel): unified-feature-calculator-library: migrate Poetry to uv (rewrite pyproject.toml, run uv lock, delete poetry.lock); fix Python version 3.11 → 3.13; declare unified-cloud-interface as dep (not unified-trading-services); add quickmerge.sh (library template); add pyrightconfig.json; ensure quality gates pass."
    status: completed
  - id: pr-f-service-pytoml
    content: "PR F Service pyproject.toml Alignment (parallel with PR F Tier 2 migration): Audit and align all 14 service pyproject.toml files against the canonical dependency matrix. Each service must: (1) declare unified-trading-services (after rename) OR unified-trading-services>=2.2.0 as the Tier 1 dep; (2) declare unified-domain-client if it reads domain data; (3) declare unified-market-interface if it processes market data; (4) declare unified-trade-execution-interface if it submits orders; (5) declare unified-events-interface (UTS re-exports are fine for production, but direct dep needed for type stubs); (6) declare unified-config-interface; (7) REMOVE any direct google-cloud-* deps that are now routed through unified-cloud-interface/unified-trading-services; (8) REMOVE any direct boto3 deps — these route through UTS/UCLI; (9) run uv lock after every pyproject.toml change; (10) verify no import statements in service source use direct cloud SDK imports (rg 'from google.cloud import' --type py should return zero in service source, not tests). Services: instruments-service, market-tick-data-handler, market-data-processing-service, strategy-service, ml-training-service, ml-inference-service, execution-services, pnl-attribution-service, risk-and-exposure-service, position-balance-monitor-service, features-delta-one-service, features-calendar-service, features-onchain-service, features-volatility-service. Run 4 parallel agents (3-4 services each)."
    status: pending
  - id: pr-f-ucs-internal-migration
    content: "UCS Internal Migration (Phase 1 code change, no commit yet): Delete the 10 UCLI-destined files from UCS core/ (gcp_clients.py, async_gcp_clients.py, aws_clients.py, secret_manager.py, queue_abstraction.py, storage_abstraction.py, cloud_constants.py, cloud_auth_factory.py, client_factory.py, cloud_config.py) and update UCS __init__.py to import from unified-cloud-interface instead. Delete UCS domain/ package (8 files: domain_service_base.py, factories.py, async_service_adapter.py, standardized_service.py, validation.py, data_source_mapping.py, typed_standardized_service.py, __init__.py). Remove domain exports from UCS __init__.py (StandardizedDomainCloudService, DomainValidationConfig, DomainValidationService, create_domain_cloud_service). Add unified-cloud-interface>=1.0.0,<2.0.0 to UCS pyproject.toml [project.dependencies]. Run uv lock. After this, UCS core/ should have ≤15 modules: __init__.py, cloud_config.py (timeout config), config.py (UnifiedCloudConfig re-export shim), date_utils.py, dependency_checker.py, error_classification.py, error_decorators.py, error_models.py, error_service.py, gcsfuse_helper.py, logging.py, parquet_schema_enforcer.py, provider.py, run_async.py, signal_handler.py, unified_monitor.py."
    status: pending
  - id: pr-g-rename
    content: "PR G — Rename unified-trading-services → unified-trading-services (after PR F merges): Step 1: Add unified_trading_services/ package directory in the repo that re-exports everything from unified_trading_services (backward compat alias); publish both package names from same repo; update pyproject.toml to include unified-trading-services as an additional package name; update workspace-manifest.json repo metadata. Step 2 (separate PR 2 weeks later): Update all 14 services' pyproject.toml and imports to use unified_trading_services; remove the alias; rename GitHub repo. IMPORTANT — also update redirect error messages: Plan 1 PR A added error messages like 'Use unified_trading_services.get_secret_client() instead' in UCI base_config.py, secrets.py, loaders.py — after this rename these messages must be updated to say unified_trading_services instead. Also update event-logging.mdc, instruments-domain-and-api-keys.mdc, and any codex docs that say 'from unified_trading_services import' in examples. ALSO: Rename unified-domain-client → unified-domain-client: same PR window as UCS rename. Step 1: Add unified_domain_client/ package directory in the repo that re-exports everything from unified_domain_client (backward compat alias). Update pyproject.toml to publish as both package names. Update workspace-manifest.json entry. Step 2 (2 weeks later): update all 14 services and Tier 2 libs to import from unified_domain_client. Remove alias. Rename GitHub repo. The name 'unified-domain-client' was a misnomer — it is a read-only data access client library, not a running service. 'unified-domain-client' is accurate."
    status: pending
  - id: pr-g-urdi
    content: "URDI Creation (can run in parallel with PR G, io_interface Phase 8): Create unified-reference-data-interface repo v1.0.0 — REST-only reference/static data: instrument definitions, options chains, expiry calendars, corporate actions; REST adapters for major venues; pyproject.toml (depends on api-contracts + unified-cloud-interface); cloudbuild.yaml, quickmerge.sh. Wire instruments-service to use URDI (Phase 8 migration of instruments-service off direct exchange REST calls)."
    status: pending
  - id: udc-path-registry
    content: "UDC Phase 1 — PathRegistry: Central SSOT for all dataset paths (no service changes yet). In unified-domain-client/ (or unified-domain-client/ after rename): create unified_domain_client/paths/ subpackage with: (1) registry.py — DataSetSpec dataclass (bucket_template, path_template, partition_keys, file_format, bq_table_template, athena_table_template) + PATH_REGISTRY dict mapping dataset name → DataSetSpec for ALL 14 datasets: market_tick, processed_candles, instruments, instrument_availability, corporate_actions, features_delta_one, features_calendar, features_onchain, features_volatility, strategy_orders, strategy_instructions, execution_records, positions, ml_models, ml_predictions, ml_training_artifacts, ml_configs. Bucket template convention: '{prefix}-{category}-{project_id}' where category=cefi|defi|tradfi and project_id comes from config — NEVER hardcoded. (2) Per-domain files (instruments.py, market_data.py, features.py, strategy.py, execution.py, positions.py, ml.py) that define typed build_path(**kwargs) and build_bucket(**kwargs) functions wrapping the registry. Fixes P0 violations: execution-services/backtest.py gs://execution-store-central-element-323112/ and features-volatility-service/conftest.py central-element-323112 bucket names must be deleted and replaced with PathRegistry calls. No service code changes in this phase."
    status: pending
  - id: udc-readers-writers
    content: "UDC Phase 2 — Readers + Writers: cloud-agnostic I/O using PathRegistry. In unified-domain-client/: create unified_domain_client/readers/ and unified_domain_client/writers/ subpackages. readers/: base.py (BaseDataReader Protocol: read(**partition_kwargs) -> pd.DataFrame), direct.py (DirectReader: builds path from PathRegistry, reads Parquet via unified_cloud_interface StorageClient — works on GCS and S3 transparently), factory.py (get_reader(dataset_name, mode=ReadMode.AUTO) -> BaseDataReader). writers/: base.py (BaseDataWriter Protocol: write(df, **partition_kwargs) -> None), direct.py (DirectWriter: builds path from PathRegistry, writes Parquet via UCLI StorageClient, triggers catalog update if enabled), factory.py (get_writer(dataset_name) -> BaseDataWriter). ReadMode enum: DIRECT (always Parquet via UCLI, operational default), MANAGED (BigQuery external table on GCP, Athena on AWS — for analytics/backtesting), AUTO (DIRECT unless BQ_EXTERNAL_TABLES=true or ATHENA_ENABLED=true env var). Migration of instruments-service and market-data-processing-service to use get_reader/get_writer in this phase (remove their gcs_path_utils.py)."
    status: pending
  - id: udc-external-tables
    content: "UDC Phase 3 — External Table Catalog (opt-in, non-breaking): catalog/ subpackage for BigQuery external tables (GCP) and AWS Athena (AWS). bq_catalog.py: generate_external_table_ddl(dataset_name, project_id, category) -> str — produces CREATE OR REPLACE EXTERNAL TABLE DDL using Hive partitioning URI prefix matching PathRegistry bucket+path; register_partition(dataset_name, partition_kwargs) -> None — no-op since BQ auto-discovers Hive partitions on external tables; ensure_external_table(dataset_name, ...) — idempotent create-or-replace. glue_catalog.py: ensure_athena_table(dataset_name, ...) — creates Glue Catalog table using Athena DDL; register_partition(dataset_name, partition_kwargs) -> None — calls MSCK REPAIR TABLE or ADD PARTITION for the specific partition. Both triggered automatically by DirectWriter after each write IF CATALOG_ENABLED=true env var. No service code changes required — services write via get_writer() and catalog registration is transparent. External tables use Hive-compatible paths (key=value/) which ALL services already use — zero path migration needed. Services can then read via get_reader(mode=ReadMode.MANAGED) for SQL analytics, backtesting, or cross-service ad-hoc queries without loading data into native BQ storage."
    status: pending
  - id: ucs-service-framework
    content: "UCS Service Framework — P0: Add shared service infrastructure to unified-trading-services to eliminate ~8,000 lines of duplicated code across 14 services. (1) ServiceCLI base class: standard argparse setup for all services with common args: --mode batch|live|incremental, --start-date YYYY-MM-DD, --end-date YYYY-MM-DD, --venue (multi), --category cefi|defi|tradfi, --max-workers INT, --dry-run, --env dev|prod, --project-id. Services extend ServiceCLI and add their own args. Replaces ~3,500 lines of parser boilerplate. (2) BaseModeHandler ABC: abstract base with run(), cleanup(), validate_config() abstract methods; concrete subclasses BatchModeHandler and LiveModeHandler; get_handler(mode) factory. Replaces 8 independent ModeHandler/BatchHandler ABCs across instruments-service, market-tick-data-handler, market-data-processing-service, features-delta-one, features-onchain, features-volatility, ml-inference, strategy. (3) BatchOrchestrator base: abstract class with date_loop(start_date, end_date) that handles missing-date detection, parallel execution via max_workers, progress logging, error collection; services implement _process_single_date(date). Replaces 8 custom orchestrators. (4) @with_retry decorator: sync + async, configurable max_attempts (default 3), backoff=exponential|linear|fixed, retry_on errors (default retryable HTTP errors from error_classification.py), jitter. Replaces ad-hoc retry loops in instruments-service, market-tick-data-handler, ml-inference, position-balance-monitor, and any service calling external APIs. (5) GracefulShutdownHandler is already in UCS — ensure all 14 services use it (currently only ml-training, ml-inference, execution use it). NOTE: Rate limiting does NOT go in UCS — see umi-connectivity-framework."
    status: pending
  - id: udc-data-completion
    content: "UDC DataCompletionChecker — P1: Add to unified-domain-client a DataCompletionChecker class that replaces per-service 'skip already processed dates' logic (~400 lines across 4 services). class DataCompletionChecker: __init__(dataset_name, project_id, cloud_provider, category) takes a PATH_REGISTRY dataset name; get_missing_dates(start_date, end_date, **partition_kwargs) -> list[str] — lists all expected blobs for date range using PathRegistry path template, calls UCLI StorageClient.list_blobs() to get existing blobs, returns dates where expected blob(s) are missing; get_completed_dates(start_date, end_date, **partition_kwargs) -> list[str] — inverse. Also port the 'available start/end date' detection from unified-trading-deployment-v3 (the RateLimiter/availability check logic there): get_available_date_range(dataset_name, **partition_kwargs) -> tuple[str, str] — discovers earliest and latest available date for a dataset by listing blobs. This replaces custom _check_existing_outputs, _check_file_exists_cached, _blob_exists wrappers in market-data-processing-service, market-tick-data-handler, features-calendar-service, execution-services."
    status: pending
  - id: umi-connectivity-framework
    content: "UMI Connectivity Framework — P1: Add shared connectivity infrastructure to unified-market-interface. (1) BaseWebSocketClient ABC: abstract base for all venue WebSocket clients with connect(), disconnect(), reconnect(), subscribe(channels), unsubscribe(channels), heartbeat loop (send ping every N seconds), resubscribe on reconnect, max_reconnect_attempts, reconnect_backoff_seconds. Concrete venue clients (Deribit, OKX, Binance, etc.) extend this. Currently execution-services/venues/deribit.py has a full WebSocket implementation (200+ lines) that should be the reference implementation moved to UMI. (2) VenueRateLimiter: token bucket rate limiter per venue, configurable requests_per_second and burst_size. Rate limiting is a CONNECTIVITY concern — it belongs in the interface library, not in services. Move from: instruments-service corporate_actions adapter (_rate_limit() method), market-tick-data-handler (rate_limit_delay). The existing DatabentoIPRateLimiter in UMI is the right pattern — generalise it to VenueRateLimiter(venue, requests_per_second) and make all venue clients use it. (3) BaseVenueRestClient: shared base for REST API clients with VenueRateLimiter built in, @with_retry from UCS, connection pooling via aiohttp.ClientSession. instruments-service and market-tick-data-handler MUST NOT implement their own retry, rate limiting, or hold API keys — they are orchestrators that call library adapters and receive canonical domain objects. The adapter (in UMI or URDI) owns the full API call lifecycle: authentication, rate limiting, retry, and response mapping."
    status: pending
  - id: utei-order-management
    content: "UTEI Order Management — P2: Move core order management protocols and base implementations from execution-services into unified-trade-execution-interface. execution-services owns 661 Python files — much of the OMS infrastructure is reusable. Move to UTEI: (1) OrderState enum and state machine (PENDING→OPEN→PARTIAL→FILLED→CANCELLED/REJECTED), (2) UnifiedOrderManager protocols and base impl (~177 lines from orders/oms.py), (3) OrderTracker base protocol (~50 lines from orders/tracker.py), (4) OrderPersistenceAdapter Protocol (from engine/live/persistence/protocols.py — PostgreSQL + in-memory impls stay in execution-services as concrete impls), (5) SmartOrderRouter Protocol + base routing logic (~100 lines from algorithms/sor.py). execution-services keeps: venue-specific adapters (Binance, OKX, Deribit order submission), NautilusTrader integration, backtest engine, live execution engine. After migration: any new execution service or strategy engine can import OMS protocols from UTEI without depending on execution-services."
    status: pending
  - id: ufc-feature-service-base
    content: "UFC Feature Service Base — P1: Unify the feature calculation pattern across all 4 feature services (delta-one, calendar, onchain, volatility) in unified-feature-calculator-library. Currently: delta-one and volatility use UFC base; calendar has its own ABC; onchain uses if/elif dispatch. Add to UFC: (1) FeatureCalculatorRegistry: standard dict[str, type[FeatureCalculator]] with register(group_name)(cls) decorator; get_calculator(group_name) factory; list_groups() for CLI validation. All 4 services should use this registry — eliminates if/elif dispatch in onchain and divergent ABCs in calendar. (2) BaseFeatureService ABC: abstract class with process_feature_group(group, date, **kwargs) abstract method; run_batch(start_date, end_date, feature_groups, max_workers) implementation using BatchOrchestrator from UCS; validate_feature_groups(groups) that checks against registry. (3) FeatureModeHandler: concrete BatchModeHandler subclass for feature services; handles standard feature service CLI args (--feature-groups, --timeframes). (4) Migrate features-calendar-service: currently has its own FeatureCalculator ABC — delete and use UFC's. Migrate features-onchain-service: replace if/elif dispatch with CALCULATOR_REGISTRY. After migration: new feature service = implement FeatureCalculator subclasses + register them + call BaseFeatureService. No custom orchestrator needed."
    status: pending
  - id: urdi-create-full
    content: "URDI Full Creation — unified-reference-data-interface: Create unified-reference-data-interface repo (repo already in workspace, previously cursor-ignored, now accessible). This is the connectivity layer for reference/static data that instruments-service currently handles itself. instruments-service should NOT do connectivity (venue REST calls, rate limiting, retries) — it should call URDI. (1) Package: unified_reference_data_interface/. (2) Adapters (REST-only, no WebSocket): CcxtReferenceAdapter (symbol lists, instrument metadata from 70+ venues via ccxt), BinanceReferenceAdapter, BybitReferenceAdapter, OkxReferenceAdapter, DeribitReferenceAdapter, CoinbaseReferenceAdapter, IbkrReferenceAdapter (tradfi), TardisReferenceAdapter, DatabentoReferenceAdapter. Each inherits from BaseReferenceAdapter with get_instruments(venue, instrument_type) -> list[CanonicalInstrument] from api-contracts. (3) API keys: each adapter calls get_secret_client(project_id, secret_name, fallback_env_var) from UCS INSIDE the adapter __init__ or fetch method — the secret never surfaces to the service layer. (4) Rate limiting via UMI VenueRateLimiter (URDI depends on UMI for connectivity primitives). (5) Retry via UCS @with_retry. (6) Factory: get_reference_adapter(venue) -> BaseReferenceAdapter. (7) pyproject.toml: depends on api-contracts, unified-cloud-interface, unified-market-interface (for VenueRateLimiter). (8) instruments-service migration: replace its engine/operations/ venue REST calls with get_reference_adapter(venue).get_instruments(); keep only the GCS write logic and domain orchestration. Removes ~3,000 lines of venue connectivity from instruments-service. NOTE: repo is already cursor-visible (line 17 of .cursorignore). Add quickmerge.sh, pyrightconfig.json, README, Dockerfile following codex library standards."
    status: pending
  - id: udei-rate-limiting
    content: "UDEI Rate Limiting — P2: unified-defi-execution-interface should follow the same pattern as UTEI for rate limiting. DeFi venue rate limiting (The Graph API limits, onchain RPC rate limits, DEX API limits) belongs in UDEI as VenueRateLimiter instances, not in individual services. features-onchain-service currently has no rate limiting — add it via UDEI rate limiter for onchain data sources. onchain protocol adapters (Alchemy, The Graph, Uniswap) should have built-in rate limiting in UDEI."
    status: pending
isProject: true
---

# Plan 2 — Library Ecosystem: New Libraries + Stage 2 Split

> **Execute SECOND.** Starts only after Plan 1 (Library Foundation) fully merges to main.
> **Absorbs**: `ucs_quickmerge_unblock_8bf08dc3` Stage 2 (PRs E–G), `io_interface_architecture_4c0c9336` ALL phases, `architecture_finalization_47c7e2e7` SSOT items.

---

## ⚠️ REFACTOR-ONLY RULE (Applies to All PRs in This Plan)

Same rule as Plan 1: **DO NOT run full test suites during any PR in this plan.** Tests will break because Tier 2 libs and services are changing their import sources simultaneously. Fixing tests mid-refactor is wasted effort.

**Full testing runs ONLY after this plan's structural work is complete.** See Plan 3 "Testing Phase."

---

## 🌐 AWS CLOUD-AGNOSTIC RULE

**All AWS implementations moved from UCS to UCLI must be moved intact and complete.** Do not downgrade, stub, or remove any AWS implementation during the migration. UCLI must support `CLOUD_PROVIDER=aws` fully on day 1. We have no AWS SA currently, so: unit tests mock boto3 (required), integration tests skip without AWS creds (expected). The code must be production-ready.

---

## UCLI Module Map: Exact Target Layout (9 source files)

> This is the authoritative structure for `unified-cloud-interface`. Do not add modules without justification. Do not merge files that exceed ~600 lines.

```
unified-cloud-interface/
├── unified_cloud_interface/
│   ├── __init__.py             # all public exports (ABCs + factory fns + data models)
│   ├── abstractions.py         # StorageClient, SecretClient, QueueClient, LoggingProvider,
│   │                           #   CacheProvider, AuthProvider ABCs (Protocol-based)
│   │                           #   + data models: BlobMetadata, SecretMetadata, StorageBlob
│   ├── factory.py              # get_storage_client(), get_secret_client(), get_queue_client(),
│   │                           #   get_logging_client(), get_cache_client()
│   │                           #   Routes via CLOUD_PROVIDER env var: gcp | aws | local
│   ├── constants.py            # CloudProvider StrEnum (GCP, AWS, LOCAL), get_cloud_provider()
│   │                           #   Merged from UCS core/provider.py + core/cloud_constants.py
│   ├── auth.py                 # AuthProvider ABC + GoogleOIDCAuth
│   │                           #   Moved from UCS auth/oidc_auth.py (Plan 1 PR B transitional home)
│   ├── cache.py                # CacheProvider ABC + RedisProvider
│   │                           #   Re-implemented from deleted UCS redis_cache.py
│   └── providers/
│       ├── __init__.py         # re-exports all provider classes
│       ├── gcp.py              # GCSStorageClient, GCPSecretClient, PubSubQueueClient,
│       │                       #   GCPLoggingProvider + async GCS variants
│       │                       #   Merged from UCS: gcp_clients.py + async_gcp_clients.py + secret_manager.py
│       ├── aws.py              # S3StorageClient, AWSSecretClient, SQSQueueClient,
│       │                       #   AWSCloudWatchProvider
│       │                       #   Moved intact from UCS aws_clients.py — DO NOT MODIFY AWS IMPLS
│       └── local.py            # LocalStorageProvider (pathlib), LocalSecretProvider (env vars),
│                               #   LocalQueueProvider (asyncio.Queue) — for tests + local dev
├── tests/unit/
│   ├── test_gcp_providers.py   # Mock google-cloud-* SDKs; test all GCP implementations
│   ├── test_aws_providers.py   # Mock boto3 fully; test ALL AWS implementations; NEVER skip
│   └── test_local_providers.py # No mocking needed; test LocalStorage/Secret/Queue
├── pyproject.toml              # zero inter-library deps; cloud SDKs as optional extras:
│                               #   google-cloud-storage, google-cloud-secret-manager,
│                               #   google-cloud-pubsub as optional [gcp] extra
│                               #   boto3 as optional [aws] extra
│                               #   redis as optional [cache] extra
├── cloudbuild.yaml
├── scripts/quickmerge.sh
└── pyrightconfig.json
```

**Total: 9 source files + 2 `__init__.py` files = 11 total Python files at v1.0.0.**
**UCS after UCLI split (UTS core/): 14 source files + `__init__.py` = 15 modules max.**

---

## Final Target Architecture (this plan delivers)

```mermaid
flowchart TD
    subgraph t0 [Tier 0 — All pure leaves after this plan]
        UCI["unified-config-interface\nBaseConfig, UnifiedCloudConfig\nPure Pydantic + env loading"]
        UEI["unified-events-interface\nEventSink Protocol\nsetup_events(sink=), log_event"]
        API["api-contracts\nVenue schemas + constants\nFull schema coverage"]
        UCLI["unified-cloud-interface NEW\nStorageProvider, SecretProvider\nQueueProvider, LoggingProvider\nGCP + AWS + Local impls\nZero inter-library deps"]
        UPI["unified-position-interface NEW\nCanonicalPosition, CanonicalBalance\nBasePositionAdapter + venue adapters"]
        URDI["unified-reference-data-interface\nInstrument defs, options chains\ncorporate actions"]
    end

    subgraph t1 [Tier 1 — Service Runtime]
        UTS["unified-trading-services\n(renamed from unified-trading-services)\nConfigStore, ConfigReloader\nGCSEventSink, PubSubEventSink\nUnifiedCloudConfig re-export\nlog_event re-export\nsetup_service() wrapper\nBaseDomainCloudService\nerror decorators"]
    end

    subgraph t2 [Tier 2 — Domain libs, Tier 0 deps only]
        UDS["unified-domain-client v1.1.0\nImports: api-contracts + UCLI only"]
        UMI["unified-market-interface\nFull WebSocket coverage\nImports: api-contracts + UCLI only"]
        UTEI["unified-trade-execution-interface\nFull WebSocket + error handling\nImports: api-contracts + UCLI only"]
        UML["unified-ml-interface\nImports: UCLI only"]
        UFC["unified-feature-calculator-library\nImports: UCLI only"]
    end

    subgraph svc [Services]
        SVC["from unified_trading_services import\n    UnifiedCloudConfig, ConfigStore\n    GCSEventSink, setup_service, log_event\nfrom unified_domain_client import\n    InstrumentsDomainClient\nfrom unified_position_interface import\n    BasePositionAdapter  (PBMS, risk)"]
    end

    UCI --> UCLI
    UEI --> UTS
    UCI --> UTS
    UCLI --> UTS
    API --> UDS
    API --> UMI
    API --> UTEI
    UCLI --> UDS
    UCLI --> UMI
    UCLI --> UTEI
    UCLI --> UML
    UCLI --> UFC
    UTS --> SVC
    UDS --> SVC
    UMI --> SVC
    UTEI --> SVC
    UPI --> SVC
```

> **Diamond dep note**: Both UTS (Tier 1) and Tier 2 libs import UCLI (Tier 0). This is safe — Python loads modules once and caches in `sys.modules`. A shared leaf dependency creates zero coupling between its dependents. The only problem would be a cycle (UCLI → UTS or UCLI → UDS), which is impossible since UCLI is a pure leaf with no inter-library imports.

---

## Batch 1 — Fully Parallel (all 4 agents start simultaneously after Plan 1 merges)

### Agent 1 — Create `unified-cloud-interface` (new repo)

**Repo layout**:

```
unified-cloud-interface/
├── unified_cloud_interface/
│   ├── __init__.py          # exports all ABCs + factory functions
│   ├── base.py              # Protocol ABCs (no ABC inheritance, just Protocol)
│   ├── factory.py           # get_storage_client(), get_secret_client(), etc.
│   └── providers/
│       ├── gcp.py           # GCPStorageProvider, GCPSecretProvider, GCPQueueProvider, GCPLoggingProvider
│       ├── aws.py           # AWSStorageProvider, AWSSecretProvider, AWSQueueProvider, AWSLoggingProvider
│       └── local.py         # LocalStorageProvider (pathlib), LocalSecretProvider (env), LocalQueueProvider (asyncio.Queue)
├── tests/unit/
├── pyproject.toml           # zero inter-library deps; cloud SDKs as optional extras
├── cloudbuild.yaml
├── scripts/quickmerge.sh    # library template
└── pyrightconfig.json
```

**Provider ABCs** (all take primitive params — never Pydantic config objects):

```python
# unified_cloud_interface/base.py
from typing import Callable, Protocol

class StorageProvider(Protocol):
    async def upload_bytes(self, bucket: str, path: str, data: bytes) -> None: ...
    async def download_bytes(self, bucket: str, path: str) -> bytes: ...
    async def list_blobs(self, bucket: str, prefix: str) -> list[str]: ...
    async def delete_blob(self, bucket: str, path: str) -> None: ...

class SecretProvider(Protocol):
    async def get_secret(self, name: str, project_id: str, version: str = "latest") -> str: ...

class QueueProvider(Protocol):
    async def publish(self, topic: str, data: bytes, attributes: dict[str, str] | None = None) -> str: ...
    async def subscribe(self, subscription: str, callback: Callable[[bytes, dict[str, str]], None]) -> None: ...

class LoggingProvider(Protocol):
    """Routes Python stdlib log records to cloud structured logging.
    Distinct from EventSink (unified-events-interface) — that is for lifecycle events."""
    def emit(self, severity: str, message: str, labels: dict[str, str] | None = None) -> None: ...
```

**Factory**:

```python
# unified_cloud_interface/factory.py
import os

def get_storage_client(provider: str | None = None) -> StorageProvider:
    p = provider or os.environ.get("CLOUD_PROVIDER", "gcp")
    match p:
        case "gcp":   return _gcp_storage()
        case "aws":   return _aws_storage()
        case "local": return _local_storage()
        case _: raise ValueError(f"Unknown CLOUD_PROVIDER: {p!r}. Valid: gcp, aws, local")
```

Same pattern for `get_secret_client()`, `get_queue_client()`, `get_logging_client()`.

**UCS delegation** (after UCLI is published, UCS delegates raw ops to it):

```python
# unified_trading_services/factory.py — updated to delegate
from unified_cloud_interface import get_storage_client as _ucli_storage

def get_storage_client(provider: str | None = None):
    """Backward-compat: delegates to unified-cloud-interface."""
    return _ucli_storage(provider)
```

### Agent 2 — api-contracts schema expansion + UPI creation

**api-contracts Phase 1** — add to `api_contracts/`:
- `schemas/derivatives.py`: FundingRate, Liquidation, SettlementPrice, OptionsChain, OptionGreeks
- `schemas/defi.py`: Swap, LiquidityPool, OraclePrice, StakingRate, LendingRate
- `schemas/errors.py`: DatabentoError, ErrorClassification (retry_safe/reconnect per venue)
- `schemas/websocket.py`: SubscribeRequest, UnsubscribeRequest, HeartbeatMessage per venue
- `vcr/coinbase/`, `vcr/deribit/`, `vcr/okx/`: Add VCR cassettes

**UPI creation (Phase 3)**:

```
unified-position-interface/
├── unified_position_interface/
│   ├── schemas.py           # CanonicalBalance, CanonicalPosition, CanonicalAccountSnapshot, CanonicalSettlement
│   ├── base.py              # BasePositionAdapter ABC
│   ├── adapters/
│   │   ├── binance.py, bybit.py, okx.py, deribit.py
│   │   ├── hyperliquid.py, upbit.py, ibkr.py, ccxt.py
│   └── factory.py
├── pyproject.toml           # deps: api-contracts + unified-cloud-interface
└── ...
```

ADR: `position-balance-monitor-service` depends on BOTH UPI (CeFi) AND `unified-defi-execution-interface` (DeFi) — two separate adapters, not one merged interface.

### Agent 3 — UMI + UTEI completion

**UMI Phase 2** — add to `unified_market_interface/`:
- `schemas.py`: `CanonicalFundingRate`, `CanonicalLiquidation`, `CanonicalSwap`, `CanonicalLiquidityPool`, `CanonicalOraclePrice`, `CanonicalStakingRate`
- `adapters/bybit_ws.py`, `adapters/coinbase_ws.py`, `adapters/deribit_ws.py`, `adapters/okx_ws.py`: WebSocket handlers with subscribe/reconnect/backfill/dispatch
- Complete Aster onchain_perps adapter

**UTEI Phase 4** — add to `unified_trade_execution_interface/`:
- `ws_feeds/`: WebSocket order update feeds for Binance, Bybit, OKX, Deribit, Hyperliquid with reconnect + state recovery
- `schemas.py`: `CanonicalPartialFill`, `CanonicalOrderRejection` (with `retry_safe: bool`), `CanonicalOrderAmendment`
- `error_map.py`: venue → error_code → `(retry_safe, reconnect)` action mapping using api-contracts error schemas

**Note**: MDPS UMI dependency is schema-only in live mode (ADR-2026-02-26-B). MDPS imports `CanonicalTrade`, `CanonicalCandle` for type annotations only; it does NOT instantiate WS handlers. Live data arrives via co-deployed MTDH. Do NOT add WS handler instantiation in MDPS.

### Agent 4 — SSOT + Codex alignment

**workspace-manifest.json additions**:

```json
"tier_rules": {
  "0": { "allowed_from": [], "description": "Pure leaf — no inter-library imports" },
  "1": { "allowed_from": [0], "description": "Service runtime — imports Tier 0 only" },
  "2": { "allowed_from": [0], "description": "Domain libs — imports Tier 0 only, no Tier 1" },
  "service": { "allowed_from": [0, 1, 2], "description": "Services import from all tiers" },
  "ui": { "allowed_from": [], "description": "TypeScript — separate QG rules" }
}
```

Add `"arch_tier"` to each repo:
- `api-contracts`, `unified-config-interface`, `unified-events-interface`, `unified-cloud-interface`, `execution-algo-library`, `matching-engine-library`, `unified-defi-execution-interface` → `"arch_tier": 0`
- `unified-trading-services` (and future `unified-trading-services`) → `"arch_tier": 1`
- `unified-domain-client`, `unified-market-interface`, `unified-trade-execution-interface`, `unified-ml-interface`, `unified-feature-calculator-library`, `unified-position-interface`, `unified-reference-data-interface` → `"arch_tier": 2`
- All 14 services → `"arch_tier": "service"`
- All UI repos → `"arch_tier": "ui"`

**Create `TIER-ARCHITECTURE.md`** at `unified-trading-codex/05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md`:
- Canonical tier diagram (same as final architecture above)
- Tier rules table (what each tier can import from)
- Allowed import patterns per tier with code examples
- Forbidden patterns (Tier 2 importing from Tier 1, intra-tier imports)
- Diamond dependency explanation (UCLI shared between Tier 1 and Tier 2 is safe)
- Reference to QG enforcement (STEP 5.6 in quality-gates-service-template.sh)

**Rewrite dependency-matrix.md** sections:
- Rename "Migration Priority Tiers" section → "Service Adoption Priority" (to avoid confusion with arch tiers)
- Add new top section "Library Architecture Tiers" with the tier diagram and tier rules
- Update library descriptions: UDS (api-contracts + UCLI only), UCS v2.2.0 (no domain exports, UTS service runtime API), new UCLI entry, new UPI entry, new URDI entry

---

## Batch 2 — Sequential (after Batch 1 merges)

### PR F — Tier 2 lib migration

4 parallel agents, each handles a set of libraries:

```
Agent A: UDS — switch pyproject.toml dep from unified-trading-services → unified-cloud-interface
Agent B: UMI — same pyproject switch
Agent C: UTEI + UML — same pyproject switch
Agent D: UFC + any remaining libs — same pyproject switch
```

Per-library changes:
```toml
# pyproject.toml
# REMOVE:
"unified-trading-services>=2.2.0,<3.0.0",
# ADD:
"unified-cloud-interface>=1.0.0,<2.0.0",
```

Source code: replace `from unified_trading_services import get_storage_client` with `from unified_cloud_interface import get_storage_client` in all Tier 2 lib source (not tests).

**Service enforcement** (parallel with PR F, io_interface Phase 6):
- MTDH: remove `app/venues/` and `engine/venues/`; wire all venue adapters through `unified_market_interface`
- execution-services: delete `legacy/adapters/venues/` ExternalVenueAdapter; verify all orders route through UTEI
- PBMS: add `unified-position-interface` + keep `unified-defi-execution-interface`; replace direct venue calls with BasePositionAdapter

**feature-calculator-library fix** (parallel):
- Migrate from Poetry → uv (`pyproject.toml` rewrite, `uv lock`, delete `poetry.lock`)
- Fix `requires-python = ">=3.11"` → `">=3.13,<3.14"`
- Declare `unified-cloud-interface` dep (not UCS)
- Add `scripts/quickmerge.sh` (library template)
- Add `pyrightconfig.json`

### PR G — UCS rename → unified-trading-services

**Step 1** (this PR): Add alias package:
```python
# unified_trading_services/__init__.py
"""unified-trading-services — service runtime orchestration layer.

This package is unified-trading-services renamed.
During migration window, both package names are available.
"""
from unified_trading_services import *  # backward compat alias
from unified_trading_services import __all__ as __all__  # re-export __all__
```

Add `unified-trading-services` to `pyproject.toml` as an installable package name.

Update workspace-manifest.json: add `unified-trading-services` entry, mark `unified-trading-services` as deprecated alias.

**Step 2** (separate PR, ~2 weeks later): Migrate all 14 services to use `unified_trading_services` imports; remove the alias; rename GitHub repo.

### URDI Creation (parallel with PR G)

```
unified-reference-data-interface/
├── unified_reference_data_interface/
│   ├── schemas.py           # InstrumentDefinition, OptionsChain, ExpiryCalendar, CorporateAction
│   ├── base.py              # BaseReferenceDataAdapter ABC
│   ├── adapters/            # venue-specific REST adapters
│   └── factory.py
├── pyproject.toml           # deps: api-contracts + unified-cloud-interface
└── ...
```

Wire instruments-service to URDI: replace direct exchange REST calls with URDI adapters.

---

## Execution Order Summary

> **REFACTOR-ONLY. NO TEST SUITES.** Ordering is strictly bottom-up in the dependency chain.
> UCLI (Tier 0) must exist and be published BEFORE Tier 2 libs or services can reference it.
> Tier 2 migration (PR F) cannot start until UCLI (PR E) is published to Artifact Registry.
> Service pyproject.toml alignment (pr-f-service-pytoml) runs parallel with Tier 2 migration.
> Full testing deferred to Plan 3 Testing Phase.

```
AUDIT STATUS (2026-02-26 — UPDATED):

--- PHASE 1: CODE CHANGES (no commits, no quickmerge, no tests) ---

BATCH 1 — ALL DONE (ran in parallel after Plan 1 Phase 1):
  Agent 1: UCLI repo creation          ✅ DONE — unified-cloud-interface v1.0.0 EXISTS
             Files: __init__.py, abstractions.py, auth.py, cache.py, constants.py,
                    factory.py, providers/__init__.py, providers/gcp.py, providers/aws.py,
                    providers/local.py
             Tests: test_abstractions.py, test_aws_providers.py, test_factory.py,
                    test_gcp_providers.py, test_local_providers.py
             quickmerge.sh present. Zero inter-library deps.
  Agent 2: UPI creation                ✅ DONE — unified-position-interface v1.0.0 EXISTS
             Files: __init__.py, adapters/, base.py, factory.py, schemas.py
             No forbidden Tier 1 deps.
  Agent 3: UMI + UTEI WebSocket        ✅ DONE
             UMI: latest commit adds CanonicalFundingRate/Liquidation/Swap schemas + WS handlers
             UTEI: latest commit adds CanonicalPartialFill/OrderRejection/OrderAmendment + ws_feeds.py
             Both use unified-cloud-interface dep only.
  Agent 4: SSOT + codex alignment      ⏳ NOT DONE — batch1-ssot still pending

STEP 2 — Tier 2 lib pyproject.toml deps:
  PR F tier2 migration:                ✅ DONE
    - UDS v1.1.2: api-contracts only (no Tier 1 deps) ✅
    - UMI: unified-cloud-interface>=1.0.0 ✅
    - UTEI: unified-cloud-interface>=1.0.0 ✅
    - UML (unified-ml-interface): unified-cloud-interface>=1.0.0 ✅
    - UFC (feature-calculator-library): unified-cloud-interface>=1.0.0, Python 3.13 ✅

  PR F Service pyproject.toml:         ⏳ PARTIALLY DONE
    CLEAN (no direct cloud deps):
      ml-inference-service, risk-and-exposure-service, features-calendar-service (3 clean)
    STILL HAS DIRECT CLOUD DEPS IN PYPROJECT.TOML:
      instruments-service (boto3), market-tick-data-handler (google-cloud-* + boto3),
      market-data-processing-service (google-cloud-storage + boto3),
      strategy-service (boto3), ml-training-service (boto3),
      execution-services (google-cloud-*),
      position-balance-monitor-service (google-cloud-pubsub),
      features-delta-one-service (google-cloud-storage),
      features-onchain-service (google-cloud-storage),
      features-volatility-service (google-cloud-storage)
    GOOD NEWS: None of these services import from google.cloud or boto3 in their
    source code — only pyproject.toml needs cleanup. Mechanical change only.

  PR F Feature Calc Fix:               ✅ DONE (Python 3.13, setuptools, UCLI dep)

  PR F Service enforcement (MTDH, exec, PBMS): ⏳ CHECK PENDING
    market-tick-data-handler has direct google-cloud-* in pyproject.toml (see above);
    pending verification that all source imports are routed through UCLI/UTS.

UCS INTERNAL MIGRATION (NEW — not in original todos):
  The 10 UCLI-destined files are STILL IN UCS core/:
    gcp_clients.py, async_gcp_clients.py, aws_clients.py, secret_manager.py,
    queue_abstraction.py, storage_abstraction.py, cloud_constants.py,
    cloud_auth_factory.py, client_factory.py, cloud_config.py
  AND UCS still has domain/ package (8 files) + domain exports in __init__.py.
  UCS currently has 26 core modules (target ≤15 after this migration).
  This migration must happen BEFORE pr-g-rename:
    → Delete UCLI-destined files from UCS core/
    → Update UCS __init__.py to import from UCLI instead
    → Delete UCS domain/ package (or keep for backward compat until pr-g)
    → Remove UCS domain exports: StandardizedDomainCloudService, DomainValidationConfig,
      DomainValidationService (also tracked in Plan 1 Step 5a)
  Add new todo: pr-f-ucs-internal-migration

STEP 3 — PR G rename:
  pr-g-rename: unified_trading_services alias package    ⏳ NOT STARTED
  pr-g-urdi: URDI creation                               ⏳ NOT STARTED

--- PHASE 2: COMMIT (quickmerge bottom-up, max 6 parallel) ---
GATE: ALL Phase 1 code changes complete (Plans 1 AND 2) before any quickmerge.
Order: UCLI → UPI → api-contracts → UCI → UEI → UCS (after internal migration) →
       UDS → UMI/UTEI/UML/UFC (parallel) → 14 services → UTS rename alias

--- PHASE 3: TESTING (see Plan 3) ---
After all quickmerges green. T0 → T1 → T2 → instruments-service ONLY.
```
