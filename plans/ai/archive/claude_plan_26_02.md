Follow all workspace cursor rules in .cursorrules.
No commits. No quickmerge. No git operations. No PRs. No test suites. No quality-gates.sh.
No summary docs, no _SUMMARY.md, no _COMPLETE.md files.
uv not pip. Delete deprecated code — do not archive.
WORKSPACE: /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

╔══════════════════════════════════════════════════════════════╗
║  ⛔ NO TESTING UNTIL SECTION 8 — THIS IS NON-NEGOTIABLE      ║
║                                                              ║
║  DO NOT run at any point before Section 8:                   ║
║    ✗ pytest / python -m pytest                               ║
║    ✗ bash scripts/quality-gates.sh                           ║
║    ✗ ruff check / ruff format                                ║
║    ✗ basedpyright                                            ║
║    ✗ uv pip install -e ".[dev]" (full dev install)           ║
║    ✗ Any CI/CD pipeline or GitHub Actions trigger            ║
║                                                              ║
║  The ONLY allowed mid-phase check is:                        ║
║    python -c "import <module>; print('OK')"                  ║
║  This verifies imports are not broken — nothing more.        ║
║  If an import fails: FIX IT. Do not run tests to debug.      ║
║                                                              ║
║  ALL testing (pytest, quality-gates, ruff, basedpyright)     ║
║  happens ONLY in SECTION 8 after all 4 phases are done.      ║
╚══════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
SECTION 1 — CURRENT STATE (audit 2026-02-26)
═══════════════════════════════════════════════════════════════

✅ CONFIRMED DONE:
  - UCI v1.2.0: abstractions.py, auth.py, cache.py, constants.py, factory.py, providers/gcp.py, aws.py, local.py
  - UPI v1.0.0: schemas.py, base.py, adapters/, factory.py
  - api-contracts v1.2.0
  - UCS v2.2.0: GCSEventSink exported, PubSubEventSink exported, CompositeEventSink exported
  - UEI v2.0.0: circular dep fixed
  - UDS v1.1.2: api-contracts only dep declared in pyproject.toml
  - UMI + UTEI WebSocket batch: CanonicalFundingRate and WS handlers complete
  - UFC: Poetry→uv migrated, Python 3.13, UCLI dep added
  - Tier 2 pyproject.toml deps: switched to unified-cloud-interface
  - workspace-manifest.json: arch_tier on all entries
  - Codex QG templates: REPO_ARCH_TIER + STEP 5.5/5.6 added
  - PR D: 13/14 services have GCSEventSink wired

❌ BROKEN — must fix in Phase 0 before anything else:
  - UCS __all__ stale symbols: create_domain_cloud_service, create_backtesting_cloud_service,
    create_features_cloud_service, create_instruments_cloud_service,
    create_market_data_cloud_service, create_strategy_cloud_service,
    create_portfolio_cloud_service — all reference deleted domain/ code → AttributeError
  - UDS broken imports: unified_trading_services.domain.standardized_service,
    unified_trading_services.domain.factories, unified_trading_services.core.config,
    unified_trading_services.core.market_category — all raise ImportError
  - post-D domain export cleanup: remove StandardizedDomainCloudService,
    DomainValidationConfig, DomainValidationService from UCS __init__.py __all__
    (those are now owned by UDS; UCS should not re-export them)
  - Tier 2 source imports incomplete: UMI ~25 `from unified_trading_services import` remain,
    UTEI ~1 remain, UML ~2 remain — must become `from unified_cloud_interface import`
  - pnl-attribution-service: directory exists with files but branch main has ZERO commits,
    all files are untracked — the repo is in an uninitialised state

⏳ REMAINING BUILD (Phases 1–3):
  - UDS PathRegistry (20 datasets), domain clients (14), readers/writers/catalog,
    DataCompletionChecker, get_available_date_range port
  - UCS Service Framework: ServiceCLI, BaseModeHandler, BatchOrchestrator, @with_retry
  - UMI Connectivity Framework: BaseWebSocketClient, VenueRateLimiter
  - UTEI Order Management: OMS protocols, OrderTracker, SmartOrderRouter
  - UFC Feature Service Base: FeatureCalculatorRegistry, BaseFeatureService
  - URDI: new repo unified-reference-data-interface
  - Codex TIER-ARCHITECTURE.md
  - UCS internal migration: 10 UCLI-destined files still in UCS core/ (see Phase 1 Agent 1)
  - 10 services have direct google-cloud-* or boto3 in pyproject.toml (mechanical remove)
  - Repo renames: UCS→UTS, UDS→UDC (Phase 2)
  - Service hardening: all 14 services (Phase 3)

═══════════════════════════════════════════════════════════════
SECTION 2 — TARGET ARCHITECTURE (5-TIER)
═══════════════════════════════════════════════════════════════

TIER 0 — Cloud Primitives (no trading logic)
  unified-cloud-interface (UCLI)
    StorageClient, SecretClient, QueueClient, CloudProvider enum
    BlobMetadata, SecretMetadata, get_cloud_provider()
    providers/: gcp.py, aws.py, local.py

TIER 1 — Shared Infrastructure (trading-aware cloud services)
  unified-trading-services (UTS) [renamed from unified-trading-services]
    get_storage_client, get_secret_client, handle_api_errors, handle_storage_errors
    ConfigStore, BaseCloudWriter, BaseCloudLoader, generate_date_range, ColumnSchema
    BaseDependencyChecker, GCSEventSink, PubSubEventSink, CompositeEventSink
    ServiceCLI, BaseModeHandler, BatchOrchestrator, @with_retry  ← NEW
  unified-config-interface (UCI)         BaseConfig, UnifiedCloudConfig
  unified-events-interface (UEI)         setup_events, log_event, MockEventSink

TIER 2 — Domain/Market Interfaces (pure protocols + schemas, no cloud I/O)
  unified-market-interface (UMI)         market data schemas + venue WS adapters + BaseWebSocketClient + VenueRateLimiter
  unified-trade-execution-interface (UTEI) order/fill schemas + OMS protocols + OrderTracker + SmartOrderRouter
  unified-ml-interface (UML)             ML model protocols + prediction schemas
  unified-feature-interface (UFC)        feature schemas + FeatureCalculatorRegistry + BaseFeatureService
  unified-position-interface (UPI)       position/account schemas
  unified-reference-data-interface (URDI) ← NEW: REST venue adapters (CCXT + exchange-specific)

TIER 3 — Domain Data Client (cloud I/O, uses UCLI + UTS)
  unified-domain-client (UDC) [renamed from unified-domain-client]
    paths/         PATH_REGISTRY (20 datasets), DataSetSpec, build_bucket/path/uri
    clients/       14 typed domain clients (instruments, market_data, features ×4, ml ×2,
                   strategy, execution, positions, pnl, risk)
    readers/       DirectReader, BigQueryExternalReader, AthenaReader, factory
    writers/       DirectWriter, factory
    catalog/       BigQueryCatalog, GlueCatalog
    DataCompletionChecker, get_available_date_range

TIER 4 — Services (uses Tier 0–3)
  14 service repos — all use ServiceCLI, BaseModeHandler, BatchOrchestrator
  instruments-service       → delegates to URDI (no direct exchange SDK imports)
  market-tick-data-handler  → delegates to UMI (no direct Databento SDK in service)
  market-data-processing-service
  features-delta-one-service
  features-calendar-service    (bug fix: day-{date} path corrected)
  features-onchain-service
  features-volatility-service
  ml-training-service
  ml-inference-service         (bug fix: predictions path corrected)
  strategy-service
  execution-services
  risk-service
  position-balance-monitor
  pnl-attribution-service

ASCII DEPENDENCY GRAPH (simplified):
  UCLI ←── UTS ←── UDC ←── Services
  UCLI ←── UCI ←── UTS
  UEI  ←── UTS ←── Services
  UMI  ←── UTS ←── Services
  UTEI ←── UTS ←── Services
  URDI ←── Services (instruments-service, market-tick-data-handler only)

═══════════════════════════════════════════════════════════════
SECTION 3 — DATASET REGISTRY (20 datasets, canonical spec)
═══════════════════════════════════════════════════════════════

Bucket naming rules:
  category   = cefi | defi | tradfi (from config, never hardcoded)
  project_id = config.gcp_project_id (GCP) or config.aws_account_id (AWS)
  Category-scoped:  {prefix}-{category}-{project_id}
  Cross-category:   {prefix}-{project_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1. raw_tick_data
    bucket:     market-data-tick-{category}-{project_id}
    path:       raw_tick_data/by_date/day={date}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/
    partitions: [date, data_type, instrument_type, venue]
    file:       {instrument_key}.parquet

 2. processed_candles
    bucket:     market-data-tick-{category}-{project_id}
    path:       processed_candles/by_date/day={date}/timeframe={timeframe}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/
    partitions: [date, timeframe, data_type, instrument_type, venue]
    file:       {instrument_id}.parquet

 3. instruments
    bucket:     instruments-store-{category}-{project_id}
    path:       instrument_availability/by_date/day={date}/venue={venue}/
    partitions: [date, venue]
    file:       instruments.parquet

 4. corporate_actions
    bucket:     instruments-store-tradfi-{project_id}   ← tradfi ONLY, no {category}
    path:       corporate_actions/by_date/day={date}/
    partitions: [date]
    files:      dividends.parquet, splits.parquet, earnings.parquet

 5. delta_one_features
    bucket:     features-delta-one-{category}-{project_id}
    path:       by_date/day={date}/feature_group={feature_group}/timeframe={timeframe}/
    partitions: [date, feature_group, timeframe]
    file:       {instrument_id}.parquet

 6. calendar_features
    bucket:     features-calendar-{project_id}          ← no {category}
    path:       calendar/{category}/by_date/day={date}/
    partitions: [category, date]
    file:       features.parquet
    BUG FIX NOTE: features-calendar-service currently writes day-{date} (HYPHEN).
                  PathRegistry and service MUST use day={date} (EQUALS sign).

 7. onchain_features
    bucket:     features-onchain-{project_id}
    path:       by_date/day={date}/feature_group={feature_group}/
    partitions: [date, feature_group]
    file:       features.parquet

 8. volatility_features
    bucket:     features-volatility-{category}-{project_id}
    path:       by_date/day={date}/feature_group={feature_group}/
    partitions: [date, feature_group]
    file:       {underlying}.parquet

 9. ml_models
    bucket:     ml-models-store-{project_id}
    path:       models/{model_id}/training-period={training_period}/
    partitions: [model_id, training_period]
    file:       model.joblib

10. ml_model_metadata
    bucket:     ml-models-store-{project_id}
    path:       model_registry/metadata/{model_id}/training-period={training_period}/
    partitions: [model_id, training_period]
    file:       metadata.json

11. ml_predictions
    bucket:     ml-predictions-store-{project_id}
    path:       predictions/by_date/day={date}/mode={mode}/
    partitions: [date, mode]
    files:      {event_id}.json, batch_{timestamp}.parquet
    BUG FIX NOTE: ml-inference-service currently writes YYYY/MM/DD (no partition key).
                  PathRegistry and service MUST use day={date}/mode={mode}/.

12. ml_training_artifacts
    bucket:     ml-training-artifacts-{project_id}
    path:       stage1-preselection/model-{model_id}/training-period={training_period}/
    partitions: [model_id, training_period]
    file:       (model-specific artifacts)

13. strategy_orders
    bucket:     strategy-store-{project_id}
    path:       strategy_orders/by_date/day={date}/strategy_id={strategy_id}/
    partitions: [date, strategy_id]
    file:       orders.parquet

14. strategy_instructions
    bucket:     strategy-store-{project_id}
    path:       strategy_instructions/strategy_id={strategy_id}/day={date}/
    partitions: [strategy_id, date]
    file:       instructions.parquet

15. backtest_results
    bucket:     strategy-store-{project_id}
    path:       backtest_results/strategy_id={strategy_id}/run_id={run_id}/
    partitions: [strategy_id, run_id]
    files:      instructions.parquet, positions.parquet, pnl_attribution.parquet, summary.json

16. execution_fills
    bucket:     execution-store-{category}-{project_id}
    path:       execution/by_date/day={date}/
    partitions: [date]
    files:      fills.parquet, orders.parquet

17. positions
    bucket:     positions-store-{project_id}
    path:       by_date/day={date}/account={account_key}/snapshot_type={snapshot_type}/
    partitions: [date, account_key, snapshot_type]
    file:       positions.parquet

18. pnl_attribution
    bucket:     pnl-attribution-store-{project_id}
    path:       by_date/day={date}/strategy_id={strategy_id}/
    partitions: [date, strategy_id]
    file:       pnl_attribution.parquet

19. risk_metrics
    bucket:     risk-metrics-store-{project_id}
    path:       by_date/day={date}/risk_type={risk_type}/
    partitions: [date, risk_type]
    file:       risk_metrics.parquet

20. nautilus_catalog
    bucket:     execution-store-{category}-{project_id}
    path:       nautilus-catalog-cache/data/trade_tick/{instrument_id}/
    partitions: [instrument_id]
    file:       (NautilusTrader catalog format)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

═══════════════════════════════════════════════════════════════
SECTION 4 — DOMAIN CLIENT SPEC (14 clients)
═══════════════════════════════════════════════════════════════

All clients: __init__(self, storage_client: StorageClient, config: UnifiedCloudConfig)
All clients: use paths/ registry to resolve bucket + path; never hardcode paths.
All clients: return typed DataFrames or Pydantic models — never dict[str, Any].

InstrumentsDomainClient (clients/instruments.py) — migrated from clients.py
  get_instruments(date, venue, category) -> pd.DataFrame
  get_available_dates(venue, category) -> list[str]
  get_venues(category) -> list[str]

MarketTickDomainClient (clients/market_data.py)
  get_tick_data(date, venue, instrument_key, data_type, instrument_type, category) -> pd.DataFrame
  get_available_dates(venue, category) -> list[str]

MarketCandleDomainClient (clients/market_data.py)
  get_candles(date, venue, instrument_id, timeframe, data_type, instrument_type, category) -> pd.DataFrame
  get_available_timeframes(venue, category) -> list[str]

FeaturesDeltaOneDomainClient (clients/features.py)
  get_features(date, instrument_id, feature_group, timeframe, category) -> pd.DataFrame
  get_available_feature_groups(category) -> list[str]

FeaturesCalendarDomainClient (clients/features.py)
  get_features(date, category) -> pd.DataFrame
  get_available_dates(category) -> list[str]

FeaturesOnchainDomainClient (clients/features.py)
  get_features(date, feature_group) -> pd.DataFrame
  get_available_feature_groups() -> list[str]

FeaturesVolatilityDomainClient (clients/features.py)
  get_features(date, underlying, feature_group, category) -> pd.DataFrame
  get_available_underlyings(category) -> list[str]

MLModelsDomainClient (clients/ml.py)
  get_model(model_id, training_period) -> bytes
  get_metadata(model_id, training_period) -> dict[str, str | int | float]
  list_models() -> list[str]

MLPredictionsDomainClient (clients/ml.py)
  get_predictions(date, mode) -> pd.DataFrame
  get_available_dates(mode) -> list[str]

StrategyDomainClient (clients/strategy.py)
  get_orders(date, strategy_id) -> pd.DataFrame
  get_instructions(strategy_id, date) -> pd.DataFrame
  get_backtest_results(strategy_id, run_id) -> dict[str, pd.DataFrame]

ExecutionDomainClient (clients/execution.py) — migrated from clients.py
  get_fills(date, category) -> pd.DataFrame
  get_orders(date, category) -> pd.DataFrame
  get_nautilus_catalog_path(instrument_id, category) -> str

PositionsDomainClient (clients/positions.py)
  get_positions(date, account_key, snapshot_type) -> pd.DataFrame
  get_available_accounts() -> list[str]

PnLDomainClient (clients/pnl.py)
  get_pnl_attribution(date, strategy_id) -> pd.DataFrame
  get_available_strategies() -> list[str]

RiskDomainClient (clients/risk.py)
  get_risk_metrics(date, risk_type) -> pd.DataFrame
  get_available_risk_types() -> list[str]

═══════════════════════════════════════════════════════════════
SECTION 5 — IMPORT ROUTING MAP (for migration agents)
═══════════════════════════════════════════════════════════════

Move FROM unified_trading_services TO unified_cloud_interface:
  get_storage_client, get_secret_client, get_queue_client
  StorageClient, SecretClient, QueueClient
  BlobMetadata, SecretMetadata
  CloudProvider, get_cloud_provider

Stay in unified_trading_services (will become unified_trading_services after rename):
  get_secret_client, handle_api_errors, handle_storage_errors
  ConfigStore, BaseCloudWriter, BaseCloudLoader
  generate_date_range, ColumnSchema, BaseDependencyChecker
  GCSEventSink, PubSubEventSink, CompositeEventSink, setup_service

Stay in unified_config_interface:
  UnifiedCloudConfig, BaseConfig

Stay in unified_events_interface:
  setup_events, log_event, MockEventSink

Stay in unified_domain_client (will become unified_domain_client after rename):
  InstrumentsDomainClient, ExecutionDomainClient (all 14 new clients)
  PATH_REGISTRY, DataSetSpec, get_reader, get_writer
  validate_timestamp_date_alignment, DataCompletionChecker, get_available_date_range

═══════════════════════════════════════════════════════════════
SECTION 6 — REPO RENAME PLAN
═══════════════════════════════════════════════════════════════

RENAME A: unified-trading-services → unified-trading-services
  Package: unified_trading_services → unified_trading_services
  Step 1: Inside unified-trading-services/ run:
            gh repo rename unified-trading-services
            git remote set-url origin git@github.com:IggyIkenna/unified-trading-services.git
  Step 2: Create unified_trading_services/__init__.py that re-exports everything:
            from unified_trading_services import *  # noqa: F401, F403
            __all__ = [...]  # explicit list matching unified_trading_services.__all__
  Step 3: Add "unified_trading_services" to pyproject.toml [tool.setuptools.packages.find]
          or packages list under [project] packages declaration.
  Step 4: In ALL repos — pyproject.toml [tool.uv.sources]:
            unified-trading-services → unified-trading-services
          In ALL repos — pyproject.toml [project.dependencies]:
            "unified-trading-services @ ..." → "unified-trading-services @ ..."
  Step 5: In ALL 14 service source files + all Tier 2 lib source files:
            from unified_trading_services import X → from unified_trading_services import X
            (Exception: within unified-trading-services repo itself, keep internal imports)
  Step 6: In ALL cloudbuild.yaml files referencing the repo name — update.
  Step 7: workspace-manifest.json: rename the entry key + folder_name.
  Step 8: Update cursor rules:
            .cursor/rules/event-logging.mdc — update all UCS package name references
            .cursor/rules/instruments-domain-and-api-keys.mdc — update all UCS references
            .cursorrules — update anti-patterns table and import routing map

RENAME B: unified-domain-client → unified-domain-client
  Package: unified_domain_client → unified_domain_client
  Step 1: Inside unified-domain-client/ run:
            gh repo rename unified-domain-client
            git remote set-url origin git@github.com:IggyIkenna/unified-domain-client.git
  Step 2: Create unified_domain_client/__init__.py that re-exports everything:
            from unified_domain_client import *  # noqa: F401, F403
            __all__ = [...]
  Step 3: Add "unified_domain_client" to pyproject.toml packages list.
  Step 4: In ALL repos — update [tool.uv.sources] and dependencies:
            unified-domain-client → unified-domain-client
  Step 5: In ALL service source files:
            from unified_domain_client import X → from unified_domain_client import X
  Step 6: workspace-manifest.json: rename the entry.
  Step 7: Update cursor rules:
            .cursor/rules/instruments-domain-and-api-keys.mdc
            .cursor/rules/search-before-implementing.mdc
            .cursorrules — all references to unified-domain-client / unified_domain_client

NOTE ON EXISTING PACKAGES/IMAGES:
  User confirmed: do NOT worry about existing Artifact Registry packages or Docker images
  having old names. Only update source code imports, pyproject.toml deps/sources,
  cloudbuild.yaml repo references, cursor rules, and codex docs.

═══════════════════════════════════════════════════════════════
SECTION 7 — AGENT ASSIGNMENTS
═══════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0 — FIX BROKEN STATE (run FIRST; all other phases block on this)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⛔ DO NOT START Phase 1 until both Phase 0 agents are complete.

────────────────────────────────────────────────────────────────
AGENT 0-A — Fix UCS __all__, UDS broken imports, post-D cleanup, Tier 2 migrations
Touches: unified-trading-services/, unified-domain-client/, unified-market-interface/,
         unified-trade-execution-interface/, unified-ml-interface/
────────────────────────────────────────────────────────────────

Step 1 — UCS __all__ stale symbol removal
  File: unified-trading-services/unified_trading_services/__init__.py
  Remove these symbols from __all__ (they reference deleted domain/ code):
    create_domain_cloud_service
    create_backtesting_cloud_service
    create_features_cloud_service
    create_instruments_cloud_service
    create_market_data_cloud_service
    create_strategy_cloud_service
    create_portfolio_cloud_service
  If any of these are defined (not just listed in __all__) inside __init__.py or any
  remaining module, delete those definitions entirely. Do not archive.

Step 2 — UCS post-D domain export cleanup
  File: unified-trading-services/unified_trading_services/__init__.py
  Remove from __all__ (these are now owned by UDS only, UCS must not re-export):
    StandardizedDomainCloudService
    DomainValidationConfig
    DomainValidationService
  If they are imported into __init__.py from any local submodule, delete those import lines.

Step 3 — UDS broken import fix
  Read unified-domain-client/unified_domain_client/__init__.py
  Read unified-domain-client/unified_domain_client/standardized_service.py (if it exists)
  Read unified-domain-client/unified_domain_client/factories.py (if it exists)
  For every import that references:
    unified_trading_services.domain.standardized_service  → delete or rewrite against UCS v2.2.0 exports
    unified_trading_services.domain.factories             → delete or rewrite
    unified_trading_services.core.config                  → replace with: from unified_config_interface import UnifiedCloudConfig
    unified_trading_services.core.market_category         → replace with: from api_contracts import MarketCategory (or equivalent api_contracts symbol)
  Files to fix: __init__.py, standardized_service.py, factories.py, cloud_data_provider.py
  If standardized_service.py and factories.py cannot be fixed without recreating the deleted
  UCS domain/ logic, DELETE them entirely (they will be superseded by clients/ subpackage
  built by Agent 3 in Phase 1). Update __init__.py imports accordingly.
  Quick sanity (python -c only): python -c "from unified_domain_client import InstrumentsDomainClient"
  If it raises: fix the import. Do NOT run pytest.

Step 4 — UMI Tier 2 source import migration (~25 occurrences)
  Run: grep -rn "from unified_trading_services import" unified-market-interface/unified_market_interface/
  For each hit: determine if the symbol belongs in unified_cloud_interface per IMPORT ROUTING MAP
  If yes: change to `from unified_cloud_interface import <symbol>`
  If no (UTS-tier symbol): leave as unified_trading_services for now (Phase 2 rename will handle)
  Symbols that must move to unified_cloud_interface: StorageClient, get_storage_client,
    SecretClient, get_secret_client, CloudProvider, BlobMetadata, get_cloud_provider

Step 5 — UTEI Tier 2 source import migration (~1 occurrence)
  Same procedure as Step 4 for unified-trade-execution-interface/unified_trade_execution_interface/

Step 6 — UML Tier 2 source import migration (~2 occurrences)
  Same procedure as Step 4 for unified-ml-interface/unified_ml_interface/

Step 7 — Quick import sanity (python -c ONLY — not pytest, not quality-gates)
  python -c "from unified_trading_services import GCSEventSink, handle_api_errors, ConfigStore"
  python -c "from unified_domain_client import InstrumentsDomainClient"
  python -c "from unified_market_interface import CanonicalFundingRate"
  python -c "from unified_trade_execution_interface import UnifiedOrderFill"
  If any raise: fix the import. Then continue. Do NOT run pytest or quality-gates.

────────────────────────────────────────────────────────────────
AGENT 0-B — pnl-attribution-service git init + scaffold
Touches: pnl-attribution-service/ (currently untracked, zero commits)
────────────────────────────────────────────────────────────────

Step 1 — Verify state
  cd pnl-attribution-service && git log --oneline  (expect: fatal: not a git repo, OR 0 commits)
  ls -la  (list what files already exist)

Step 2 — Wire GCSEventSink (same as the 13 other services that already have it)
  Read existing pnl-attribution-service source to find the setup_events call.
  If it uses the legacy pattern (setup_events without GCSEventSink):
    from unified_trading_services import GCSEventSink, setup_service
    Remove: from unified_events_interface import setup_events
    Add setup_service(..., sink=GCSEventSink(project_id=config.gcp_project_id,
                                              bucket=config.events_bucket,
                                              service_name="pnl-attribution-service"))
  If GCSEventSink is already wired, skip.

Step 3 — Ensure pyproject.toml has correct deps
  Required deps: unified-trading-services, unified-config-interface, unified-events-interface,
    unified-domain-client, api-contracts
  Required dev deps: ruff==0.15.0, pytest>=9.0.1, pytest-cov>=7.0.0, pytest-asyncio>=0.25.0,
    basedpyright
  Python: requires-python = ">=3.13,<3.14"
  No direct google-cloud-* or boto3 in deps.

Step 4 — Ensure minimum required files exist
  Required files (create stubs if missing):
    pnl_attribution_service/__init__.py
    pnl_attribution_service/config.py  ← class PnLAttributionConfig(UnifiedCloudConfig)
    tests/__init__.py
    tests/unit/__init__.py
    tests/unit/test_event_logging.py  ← standard event logging test (see UEI pattern)
    .env.example
    pyrightconfig.json  ← {"pythonVersion": "3.13", "strict": true, "include": ["pnl_attribution_service"]}

Step 5 — git init + initial commit structure (FILES ONLY — do NOT run git commands)
  List what files need to exist so the user can do: git init && git add -A && git commit
  Print the list of files that would be in the initial commit.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — LIBRARY BUILD (run AFTER Phase 0 complete; all 6 agents fully parallel)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⛔ DO NOT START Phase 1 until Phase 0 is complete (0-A and 0-B both done).
✅ Agents 1–6 have ZERO file overlap — run all in parallel.

────────────────────────────────────────────────────────────────
AGENT 1 — UCS Internal Migration + UCS Service Framework
Touches: unified-trading-services/ only
────────────────────────────────────────────────────────────────

Part A: UCS Internal Migration — move 10 UCLI-destined files out of UCS core/
  The following files in unified-trading-services/unified_trading_services/core/ should be
  replaced by UCLI equivalents. For each file:
    (a) Check if UCLI already exports the equivalent (it should for all 10).
    (b) Remove the file from UCS core/.
    (c) Update any internal UCS imports that referenced the deleted file to use UCLI instead.

  Files to migrate/delete from UCS core/:
    gcp_clients.py          → unified_cloud_interface.providers.gcp
    async_gcp_clients.py    → unified_cloud_interface.providers.gcp (async variant)
    aws_clients.py          → unified_cloud_interface.providers.aws
    secret_manager.py       → unified_cloud_interface (SecretClient, get_secret_client)
    queue_abstraction.py    → unified_cloud_interface (QueueClient, get_queue_client)
    storage_abstraction.py  → unified_cloud_interface (StorageClient, get_storage_client)
    cloud_constants.py      → unified_cloud_interface.constants
    cloud_auth_factory.py   → unified_cloud_interface.auth
    client_factory.py       → unified_cloud_interface.factory
    cloud_config.py         → unified_config_interface (UnifiedCloudConfig)

  For each file: read it first, confirm the UCLI equivalent exists, update internal usages,
  then delete the file. Never leave a deleted-file import dangling in UCS __init__.py.

  Update UCS pyproject.toml [project.dependencies] if UCLI is not already listed:
    "unified-cloud-interface @ {path to ucli}"
  Update UCS [tool.uv.sources] accordingly.

Part B: UCS Service Framework — add 4 new abstractions to UCS
  Create: unified-trading-services/unified_trading_services/service_framework/
    __init__.py
    cli.py          ← ServiceCLI: argparse base class with --mode batch|live, --date, --env,
                       --venues, --dry-run flags; parse_args() -> ServiceArgs dataclass
    handlers.py     ← BaseModeHandler(ABC): abstract run_batch(args) / run_live(args);
                       BatchOrchestrator(BaseModeHandler): date-range loop with
                       ThreadPoolExecutor(max_workers=config.max_workers), RAM adaptive
                       (reduce at 85%, shutdown at 90% via psutil)
    retry.py        ← @with_retry(max_retries=3, backoff_factor=2.0, exceptions=(Exception,)):
                       decorator using exponential backoff; log_event("RETRY_ATTEMPT", ...) each retry
    __init__.py exports: ServiceCLI, ServiceArgs, BaseModeHandler, BatchOrchestrator, with_retry

  Add to UCS unified_trading_services/__init__.py __all__:
    ServiceCLI, ServiceArgs, BaseModeHandler, BatchOrchestrator, with_retry

────────────────────────────────────────────────────────────────
AGENT 2 — UDC PathRegistry
Touches: unified-domain-client/ → paths/ subpackage only
────────────────────────────────────────────────────────────────

Create unified-domain-client/unified_domain_client/paths/:

  __init__.py — exports: PATH_REGISTRY, DataSetSpec, ReadMode, get_spec,
                          build_bucket, build_path, build_full_uri

  registry.py — DataSetSpec dataclass:
    @dataclass
    class DataSetSpec:
        name: str
        bucket_template: str      # e.g. "market-data-tick-{category}-{project_id}"
        path_template: str        # e.g. "raw_tick_data/by_date/day={date}/..."
        partition_keys: list[str]
        file_template: str        # e.g. "{instrument_key}.parquet"
        multi_file: bool = False  # True when dataset has multiple files (e.g. corporate_actions)
        extra_files: list[str] = field(default_factory=list)

    PATH_REGISTRY: dict[str, DataSetSpec] = {
        "raw_tick_data": DataSetSpec(...),  # all 20 entries per Section 3 above
        ... (all 20 datasets)
    }

    def get_spec(name: str) -> DataSetSpec:
        if name not in PATH_REGISTRY:
            raise KeyError(f"Dataset '{name}' not in PATH_REGISTRY. Known: {list(PATH_REGISTRY)}")
        return PATH_REGISTRY[name]

    def build_bucket(name: str, *, project_id: str, category: str = "") -> str:
        spec = get_spec(name)
        return spec.bucket_template.format(project_id=project_id, category=category)

    def build_path(name: str, **partition_values: str) -> str:
        spec = get_spec(name)
        return spec.path_template.format(**partition_values)

    def build_full_uri(name: str, *, project_id: str, category: str = "", **partition_values: str) -> str:
        bucket = build_bucket(name, project_id=project_id, category=category)
        path = build_path(name, **partition_values)
        return f"gs://{bucket}/{path}"  # or s3:// based on CloudProvider

  class ReadMode(str, Enum):
      AUTO = "auto"        # UCLI StorageClient direct
      BQ_EXTERNAL = "bq"   # BigQuery external table
      ATHENA = "athena"    # AWS Athena

  market_data.py — class MarketDataPaths with typed helper methods delegating to registry
  instruments.py — class InstrumentsPaths with typed helpers
  features.py    — class FeaturesPaths (delta_one, calendar, onchain, volatility)
  ml.py          — class MLPaths (models, metadata, predictions, training_artifacts)
  strategy.py    — class StrategyPaths
  execution.py   — class ExecutionPaths
  positions.py   — class PositionsPaths
  pnl.py         — class PnLPaths
  risk.py        — class RiskPaths

  Add paths to UDS __init__.py:
    from unified_domain_client.paths import PATH_REGISTRY, DataSetSpec, ReadMode, get_spec,
        build_bucket, build_path, build_full_uri

────────────────────────────────────────────────────────────────
AGENT 3 — UDC Domain Clients (clients/ subpackage)
Touches: unified-domain-client/ → clients/ subpackage only
────────────────────────────────────────────────────────────────

Create unified-domain-client/unified_domain_client/clients/:

  __init__.py — exports all 14 clients

  base.py — BaseDataClient(ABC):
    def __init__(self, storage_client: StorageClient, config: UnifiedCloudConfig) -> None
    def _read_parquet(self, bucket: str, path: str) -> pd.DataFrame
    def _list_blobs(self, bucket: str, prefix: str) -> list[str]
    Use get_storage_client() from unified_cloud_interface to get StorageClient.

  instruments.py — InstrumentsDomainClient(BaseDataClient):
    Migrate the existing InstrumentsDomainClient from unified_domain_client/clients.py
    (the current monolithic file). Keep existing method signatures if they work.
    Add: get_available_dates(venue, category) -> list[str]
    Use PATH_REGISTRY["instruments"] for all path construction.

  market_data.py — MarketTickDomainClient(BaseDataClient) + MarketCandleDomainClient(BaseDataClient)
    See Domain Client Spec in Section 4.

  features.py — FeaturesDeltaOneDomainClient, FeaturesCalendarDomainClient,
                 FeaturesOnchainDomainClient, FeaturesVolatilityDomainClient
    All use PATH_REGISTRY for path construction.
    FeaturesCalendarDomainClient.get_features uses day={date} NOT day-{date}.

  ml.py — MLModelsDomainClient + MLPredictionsDomainClient
    MLPredictionsDomainClient uses PATH_REGISTRY["ml_predictions"] which has
    day={date}/mode={mode}/ — never the legacy YYYY/MM/DD format.

  strategy.py  — StrategyDomainClient (orders, instructions, backtest_results)
  execution.py — ExecutionDomainClient migrated from existing clients.py
  positions.py — PositionsDomainClient (scaffold; reads positions dataset)
  pnl.py       — PnLDomainClient (scaffold; reads pnl_attribution dataset)
  risk.py      — RiskDomainClient (scaffold; reads risk_metrics dataset)

  Update UDS __init__.py to export all 14 clients from clients/ subpackage.
  Keep backward compat for InstrumentsDomainClient and ExecutionDomainClient
  (they were already exported from the old clients.py — do not break existing imports).
  Delete the old monolithic unified_domain_client/clients.py once migrated.

────────────────────────────────────────────────────────────────
AGENT 4 — UDC Readers, Writers, Catalog, DataCompletionChecker
Touches: unified-domain-client/ → readers/, writers/, catalog/, completion.py
────────────────────────────────────────────────────────────────

Create unified-domain-client/unified_domain_client/readers/:
  __init__.py   — exports: get_reader, ReadMode, BaseDataReader
  base.py       — BaseDataReader(Protocol):
                    def read(self, bucket: str, path: str) -> pd.DataFrame
                    def list_available(self, bucket: str, prefix: str) -> list[str]
  direct.py     — DirectReader(BaseDataReader):
                    Uses StorageClient from unified_cloud_interface.
                    read() → download blob → pd.read_parquet(BytesIO(...))
                    list_available() → storage_client.list_blobs(bucket, prefix=prefix)
  bq_external.py — BigQueryExternalReader(BaseDataReader):
                    Uses BigQuery client (via UCLI providers/gcp).
                    Executes SELECT * FROM external_table WHERE partition filters.
  athena.py     — AthenaReader(BaseDataReader):
                    Uses boto3 Athena client (via UCLI providers/aws).
  factory.py    — get_reader(dataset_name: str, mode: ReadMode = ReadMode.AUTO) -> BaseDataReader:
                    AUTO → DirectReader
                    BQ_EXTERNAL → BigQueryExternalReader
                    ATHENA → AthenaReader

Create unified-domain-client/unified_domain_client/writers/:
  __init__.py   — exports: get_writer, BaseDataWriter
  base.py       — BaseDataWriter(Protocol):
                    def write(self, df: pd.DataFrame, bucket: str, path: str) -> None
                    def write_json(self, data: dict[str, object], bucket: str, path: str) -> None
  direct.py     — DirectWriter(BaseDataWriter):
                    df → BytesIO → parquet → storage_client.upload_blob(bucket, path, data)
                    Calls validate_timestamp_date_alignment(df, date=date) BEFORE every write.
  factory.py    — get_writer(dataset_name: str) -> BaseDataWriter:
                    Returns DirectWriter(storage_client) for now (Athena write TBD).

Create unified-domain-client/unified_domain_client/catalog/:
  __init__.py      — exports: BigQueryCatalog, GlueCatalog
  bq_catalog.py    — BigQueryCatalog:
                       create_external_table(dataset_name, project_id, category, bq_dataset)
                       Generates DDL for Hive-partitioned external tables over GCS.
  glue_catalog.py  — GlueCatalog:
                       create_table(dataset_name, account_id, category)
                       Generates Glue table definition for Athena.

Create unified-domain-client/unified_domain_client/completion.py:
  class DataCompletionChecker:
    def __init__(self, storage_client: StorageClient, config: UnifiedCloudConfig) -> None
    def is_complete(self, dataset_name: str, date: str, *, category: str = "",
                    **partition_values: str) -> bool:
      Checks whether the expected output blobs exist in GCS/S3.
      Uses PATH_REGISTRY to resolve bucket + path.
      Returns True only if ALL expected files for the dataset exist.
    def get_missing_dates(self, dataset_name: str, start_date: str, end_date: str,
                          *, category: str = "", **partition_values: str) -> list[str]:
      Returns list of dates where data is missing.
    def get_available_date_range(self, dataset_name: str, *, category: str = "",
                                 **partition_values: str) -> tuple[str, str] | None:
      Ported from unified-trading-deployment-v3 (find the equivalent function there first;
      if it lists blobs and parses day= partitions, replicate that logic here).
      Returns (earliest_date, latest_date) or None if no data.

  Add to UDS __init__.py:
    from unified_domain_client.completion import DataCompletionChecker
    from unified_domain_client.readers import get_reader, ReadMode
    from unified_domain_client.writers import get_writer

────────────────────────────────────────────────────────────────
AGENT 5 — URDI Creation + UMI Connectivity Framework
Touches: NEW unified-reference-data-interface/ repo + unified-market-interface/ WS framework
────────────────────────────────────────────────────────────────

Part A: Create unified-reference-data-interface/ repo
  (This is a Tier 2 library — no cloud I/O; REST clients + schema parsing only)

  Repo structure:
    unified_reference_data_interface/
      __init__.py           ← exports: get_reference_adapter, BaseReferenceAdapter, venue adapters
      base.py               ← BaseReferenceAdapter(ABC):
                                 get_instruments(venue: str) -> list[InstrumentRef]
                                 get_funding_rate(venue: str, symbol: str) -> FundingRateRef
                                 get_ohlcv(venue: str, symbol: str, timeframe: str, limit: int) -> list[OHLCVRef]
      schemas.py            ← InstrumentRef(BaseModel), FundingRateRef(BaseModel), OHLCVRef(BaseModel)
                               All Pydantic v2 models. No Any types.
      adapters/
        __init__.py
        ccxt_adapter.py     ← CCXTAdapter(BaseReferenceAdapter): uses ccxt library
        binance.py          ← BinanceAdapter (direct REST, no CCXT)
        bybit.py            ← BybitAdapter
        okx.py              ← OKXAdapter
        deribit.py          ← DeribitAdapter
        coinbase.py         ← CoinbaseAdapter
        ibkr.py             ← IBKRAdapter (Interactive Brokers)
        tardis.py           ← TardisAdapter (metadata / instrument list via REST)
        databento.py        ← DatabentoAdapter (symbol reference via REST)
      factory.py            ← get_reference_adapter(venue: str, config: UnifiedCloudConfig)
                                → resolve API key via get_secret_client()
                                → return correct adapter instance
    pyproject.toml          ← name="unified-reference-data-interface", version="1.0.0",
                               python>=3.13,<3.14, deps: api-contracts, unified-config-interface,
                               unified-trading-services (for get_secret_client), aiohttp, ccxt
                               dev deps: ruff==0.15.0, pytest>=9.0.1, basedpyright
    pyrightconfig.json      ← strict mode, include: ["unified_reference_data_interface"]
    scripts/quickmerge.sh   ← copy template from any existing service
    .env.example
    README.md               ← ONE LINE: "REST reference data adapters for all supported venues."

  HARD BOUNDARY: No cloud storage I/O (no GCS/S3 reads/writes). REST only.
  API keys: resolved exclusively via get_secret_client() — never os.environ directly.

Part B: UMI Connectivity Framework additions
  Add to unified-market-interface/unified_market_interface/connectivity/:
    __init__.py
    base_ws.py  ← BaseWebSocketClient(ABC):
                    def __init__(self, url: str, venue: str, config: UnifiedCloudConfig)
                    async def connect(self) -> None
                    async def disconnect(self) -> None
                    async def subscribe(self, channels: list[str]) -> None
                    @abstractmethod
                    async def on_message(self, msg: dict[str, object]) -> None
                    Reconnect logic with exponential backoff (uses @with_retry from UTS).
    rate_limiter.py ← VenueRateLimiter:
                    Token bucket implementation.
                    __init__(self, requests_per_second: float, burst: int = 10)
                    async def acquire(self) -> None  ← awaitable; blocks until token available
                    Singleton cache: get_rate_limiter(venue: str) -> VenueRateLimiter

  Add to UMI unified_market_interface/__init__.py:
    from unified_market_interface.connectivity import BaseWebSocketClient, VenueRateLimiter

────────────────────────────────────────────────────────────────
AGENT 6 — UFC Feature Base + UTEI OMS + Codex TIER-ARCHITECTURE + pyproject.toml cleanup
Touches: unified-feature-interface/, unified-trade-execution-interface/, unified-trading-codex/,
         10 service pyproject.toml files
────────────────────────────────────────────────────────────────

Part A: UFC Feature Service Base
  Add to unified-feature-interface/unified_feature_interface/service_base/:
    __init__.py
    registry.py ← FeatureCalculatorRegistry:
                    _calculators: dict[str, type[BaseFeatureCalculator]] = {}
                    @classmethod
                    def register(cls, name: str) -> Callable[[type], type]  # decorator
                    @classmethod
                    def get(cls, name: str) -> type[BaseFeatureCalculator]
                    @classmethod
                    def list_calculators() -> list[str]
    base.py     ← BaseFeatureCalculator(ABC):
                    @abstractmethod
                    def calculate(self, df: pd.DataFrame, **params: object) -> pd.DataFrame
                    @abstractmethod
                    def get_output_schema(self) -> list[ColumnSchema]
               ← BaseFeatureService(ABC):
                    @abstractmethod
                    def run_batch(self, date: str, instruments: pd.DataFrame) -> pd.DataFrame
                    @abstractmethod
                    def run_live(self, tick: object) -> pd.DataFrame
    handlers.py ← FeatureModeHandler(BaseModeHandler from UTS):
                    Wires feature service into BatchOrchestrator; handles batch date loops.

  Add to UFC __init__.py:
    FeatureCalculatorRegistry, BaseFeatureCalculator, BaseFeatureService, FeatureModeHandler

Part B: UTEI Order Management — move OMS protocols here
  If UnifiedOrderManager, OrderTracker, SmartOrderRouter currently live in execution-services/
  (service repo) rather than the UTEI library:
    Read execution-services to confirm where they are defined.
    Create unified-trade-execution-interface/unified_trade_execution_interface/oms/:
      __init__.py
      protocols.py    ← UnifiedOrderManager(Protocol): submit_order, cancel_order, amend_order
      tracker.py      ← OrderTracker: in-memory order state machine (NEW/PENDING/FILLED/CANCELLED)
      router.py       ← SmartOrderRouter(Protocol): route_order(order) -> VenueTarget
    Delete originals from execution-services/ once UTEI versions are added.
    Add to UTEI __init__.py: UnifiedOrderManager, OrderTracker, SmartOrderRouter

Part C: Codex TIER-ARCHITECTURE.md
  Create unified-trading-codex/04-architecture/TIER-ARCHITECTURE.md
  Content:
    - 5-tier diagram (ASCII) matching Section 2 of this plan
    - Per-tier: repo name, package name, purpose, what it imports, what imports it
    - Import routing table (mirrors Section 5 of this plan)
    - Rule: never import across tiers in reverse (Tier 0 must not know about Tier 3+)
    - Rule: services (Tier 4) import from Tier 0-3 only; never from other service repos
    - Repo rename status section (UCS→UTS, UDS→UDC in progress)

Part D: Service pyproject.toml cleanup — remove direct cloud provider deps
  10 services still have direct google-cloud-storage, google-cloud-pubsub, google-cloud-secret-manager,
  or boto3 in [project.dependencies]. These must be removed (services use UCLI/UCS abstractions).
  Identify the 10 services by running:
    grep -rl "google-cloud-storage\|google-cloud-pubsub\|google-cloud-secret-manager\|boto3" \
      */pyproject.toml
  For each hit: remove the direct cloud dep from [project.dependencies].
  Do NOT remove from any library's pyproject.toml (UCLI, UCS, UDS own those deps legitimately).
  Do NOT change any source code imports — only pyproject.toml cleanup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — REPO RENAMES (run AFTER Phase 1 complete; both agents fully parallel)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⛔ DO NOT START Phase 2 until Phase 1 is complete (Agents 1–6 all done).
✅ Agents 7 and 8 have ZERO file overlap — run in parallel.

────────────────────────────────────────────────────────────────
AGENT 7 — UCS → UTS Rename (unified-trading-services → unified-trading-services)
Touches: unified-trading-services/ + ALL 30+ repos (pyproject.toml + source imports)
────────────────────────────────────────────────────────────────

Step 1 — GitHub rename + remote update
  cd unified-trading-services
  gh repo rename unified-trading-services
  git remote set-url origin git@github.com:IggyIkenna/unified-trading-services.git

Step 2 — Add alias package in unified-trading-services/
  Create unified-trading-services/unified_trading_services/__init__.py:
    """Backward-compat alias: unified_trading_services → unified_trading_services."""
    from unified_trading_services import *  # noqa: F401, F403
    from unified_trading_services import __all__  # re-export __all__
  Add "unified_trading_services" to pyproject.toml packages list.

Step 3 — Update pyproject.toml for ALL repos
  For every repo that has [tool.uv.sources] with "unified-trading-services":
    Change key: unified-trading-services → unified-trading-services
  For every repo that has "unified-trading-services" in [project.dependencies]:
    Change to "unified-trading-services @ ..."
  Repos to check: all 14 services + all Tier 2 libs (UMI, UTEI, UML, UFC, UPI, URDI) +
    UDS (unified-domain-client) + any utility repos.

Step 4 — Update source imports in ALL service source files
  Run: grep -rln "from unified_trading_services import" */
  For each file found outside unified-trading-services/ itself:
    Replace: from unified_trading_services import → from unified_trading_services import
  Exclusion: do NOT change imports inside unified-trading-services/unified_trading_services/
    (internal imports stay as-is).

Step 5 — Update cloudbuild.yaml references
  Run: grep -rln "unified-trading-services" */cloudbuild.yaml
  For each hit: replace repo name references (not package import strings).

Step 6 — Update workspace-manifest.json
  Change entry key and folder_name from "unified-trading-services" to "unified-trading-services".

Step 7 — Update cursor rules
  .cursor/rules/event-logging.mdc:
    Replace all "unified_trading_services" package name references with "unified_trading_services"
  .cursor/rules/instruments-domain-and-api-keys.mdc:
    Same replacement.
  .cursorrules (workspace root):
    Update the IMPORT ROUTING MAP section, anti-patterns table, and any explicit package name refs.

────────────────────────────────────────────────────────────────
AGENT 8 — UDS → UDC Rename (unified-domain-client → unified-domain-client)
Touches: unified-domain-client/ + ALL 30+ repos (pyproject.toml + source imports)
────────────────────────────────────────────────────────────────

Step 1 — GitHub rename + remote update
  cd unified-domain-client
  gh repo rename unified-domain-client
  git remote set-url origin git@github.com:IggyIkenna/unified-domain-client.git

Step 2 — Add alias package in unified-domain-client/
  Create unified-domain-client/unified_domain_client/__init__.py:
    """Backward-compat alias: unified_domain_client → unified_domain_client."""
    from unified_domain_client import *  # noqa: F401, F403
    from unified_domain_client import __all__
  Add "unified_domain_client" to pyproject.toml packages list.

Step 3 — Update pyproject.toml for ALL repos
  Change all occurrences of "unified-domain-client" in [tool.uv.sources] and
  [project.dependencies] to "unified-domain-client".

Step 4 — Update source imports in ALL service source files
  Run: grep -rln "from unified_domain_client import" */
  For each file found outside unified-domain-client/ itself:
    Replace: from unified_domain_client import → from unified_domain_client import
  Exclusion: do NOT change imports inside unified-domain-client/unified_domain_client/
    (internal imports stay as-is).

Step 5 — Update workspace-manifest.json
  Change entry key and folder_name to "unified-domain-client".

Step 6 — Update cursor rules
  .cursor/rules/instruments-domain-and-api-keys.mdc:
    Replace all "unified_domain_client" import examples with "unified_domain_client".
  .cursor/rules/search-before-implementing.mdc:
    Update the "unified-domain-client" entry to "unified-domain-client".
  .cursorrules (workspace root):
    Update all references to unified-domain-client / unified_domain_client.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — SERVICE HARDENING (run AFTER Phase 2 complete; all 4 agents fully parallel)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⛔ DO NOT START Phase 3 until Phase 2 is complete (Agents 7 and 8 both done).
✅ Agents 9–12 have ZERO file overlap (each covers distinct service repos) — run all in parallel.

────────────────────────────────────────────────────────────────
AGENT 9 — instruments-service hardening
Touches: instruments-service/ only
────────────────────────────────────────────────────────────────

HARD BOUNDARY (non-negotiable):
  instruments-service MUST NOT contain:
    ✗ Direct exchange REST API keys or SDK calls (ccxt, binance-connector, deribit-py, etc.)
    ✗ Rate limiting logic (use VenueRateLimiter from UMI)
    ✗ Any `from ccxt import` or `import requests` for exchange data
  All venue REST calls → delegate to unified_reference_data_interface via URDI adapters.

Step 1 — Audit current service
  Read instruments_service/ source tree. List all files.
  Identify: venue REST call files, rate limiting logic, direct exchange SDK imports.

Step 2 — Delete venue REST logic
  Files that do direct exchange REST calls: delete them.
  Replace with: adapter = get_reference_adapter(venue, config); instruments = adapter.get_instruments(venue)

Step 3 — Wire ServiceCLI + BatchOrchestrator
  Replace existing argparse/main.py with ServiceCLI-based entrypoint.
  BaseModeHandler subclass: InstrumentsModeHandler(BatchOrchestrator)
    run_batch(args): for each date in date_range, call DataCompletionChecker.is_complete();
                      skip if complete, else fetch + write via get_writer("instruments").

Step 4 — Wire DataCompletionChecker
  from unified_domain_client import DataCompletionChecker
  checker = DataCompletionChecker(storage_client, config)
  Skip dates already present in GCS.

Step 5 — Wire get_writer("instruments")
  from unified_domain_client import get_writer
  writer = get_writer("instruments")
  writer.write(df, bucket, path)  ← path from PATH_REGISTRY["instruments"]

Step 6 — Update pyproject.toml
  Add deps: unified-reference-data-interface, unified-domain-client, unified-trading-services
  Remove: any direct exchange SDK deps (ccxt, etc.) — those belong in URDI only.

────────────────────────────────────────────────────────────────
AGENT 10 — market-tick-data-handler + market-data-processing-service hardening
Touches: market-tick-data-handler/ and market-data-processing-service/ only
────────────────────────────────────────────────────────────────

HARD BOUNDARY for market-tick-data-handler:
  market-tick-data-handler MUST NOT contain:
    ✗ Direct Databento SDK imports in service logic (no `import databento` in service code)
    ✗ Direct API key reads via os.environ
    ✗ Rate limiting logic
  All Databento calls → UMI adapters via unified_market_interface.
  Rate limiting → VenueRateLimiter from UMI.
  API keys → get_secret_client() called inside UMI adapter only.

market-tick-data-handler:
  Step 1 — Identify Databento SDK usage in service source (grep for `import databento`).
  Step 2 — Delete any direct databento imports/calls from service code.
           Replace with: UMI adapter calls (DatabentoAdapter or equivalent WS handler).
  Step 3 — Wire ServiceCLI, BatchOrchestrator, DataCompletionChecker.
  Step 4 — Wire get_writer("raw_tick_data") from UDC.
  Step 5 — Delete gcs_path_utils.py (superseded by PATH_REGISTRY).
           Fix any imports that referenced gcs_path_utils.py.
  Step 6 — Update pyproject.toml: add unified-market-interface, unified-domain-client.

market-data-processing-service:
  Step 1 — Read the main orchestrator file. It is reportedly ~1256 lines.
           Confirm the file path (likely orchestrator.py or main.py).
  Step 2 — Extract the date-loop logic out of the orchestrator and replace with BatchOrchestrator.
           The processing engine (candle building, resampling logic) stays; only the outer
           orchestration loop is replaced.
  Step 3 — Wire DataCompletionChecker to skip already-processed dates.
  Step 4 — Wire get_writer("processed_candles") from UDC.
  Step 5 — Update pyproject.toml: add unified-domain-client, unified-trading-services.

────────────────────────────────────────────────────────────────
AGENT 11 — All 4 features services + both ML services hardening
Touches: features-delta-one-service/, features-calendar-service/,
         features-onchain-service/, features-volatility-service/,
         ml-training-service/, ml-inference-service/
────────────────────────────────────────────────────────────────

For ALL 4 features services:
  Step 1 — Wire FeatureCalculatorRegistry, BaseFeatureService, FeatureModeHandler from UFC.
  Step 2 — Wire ServiceCLI + BatchOrchestrator (via FeatureModeHandler).
  Step 3 — Wire DataCompletionChecker from UDC.
  Step 4 — Wire get_writer("delta_one_features") / ("calendar_features") / etc. from UDC.

features-calendar-service ADDITIONAL (path bug fix):
  Step 5 — Find every place where the path is constructed with day-{date} (hyphen).
           Replace ALL occurrences with day={date} (equals sign).
           This includes: GCS write paths, any file listing/reading logic, docs.
           After fix: verify the full path matches PATH_REGISTRY["calendar_features"].path_template.

For BOTH ML services:
  Step 1 — Wire ServiceCLI, BatchOrchestrator, @with_retry (from UTS service framework).
  Step 2 — Wire DataCompletionChecker from UDC.

ml-training-service:
  Step 3 — Wire get_reader("delta_one_features"), get_reader("instruments") for input data.
  Step 4 — Wire get_writer("ml_models"), get_writer("ml_model_metadata") for output.

ml-inference-service ADDITIONAL (predictions path bug fix):
  Step 3 — Find every place where ml predictions are written to YYYY/MM/DD format.
           Replace ALL occurrences with day={date}/mode={mode}/ per PATH_REGISTRY["ml_predictions"].
  Step 4 — Wire get_writer("ml_predictions") from UDC.
  Step 5 — Wire get_reader("ml_models") to load the model.

────────────────────────────────────────────────────────────────
AGENT 12 — strategy/risk/position/pnl hardening + execution-services P1 + cross-cutting rollouts
Touches: strategy-service/, risk-service/, position-balance-monitor/, pnl-attribution-service/,
         execution-services/; PLUS GracefulShutdownHandler + BaseDependencyChecker rollout to
         any services still missing them
────────────────────────────────────────────────────────────────

strategy-service:
  Step 1 — Wire ServiceCLI, BaseModeHandler (batch + live modes).
  Step 2 — Wire get_reader("instruments"), get_reader("delta_one_features"),
           get_reader("ml_predictions") for inputs.
  Step 3 — Wire get_writer("strategy_orders"), get_writer("strategy_instructions") for outputs.
  Step 4 — Wire DataCompletionChecker.

risk-service:
  Step 1 — Wire ServiceCLI, BatchOrchestrator.
  Step 2 — Wire get_reader("positions"), get_reader("execution_fills") for inputs.
  Step 3 — Wire get_writer("risk_metrics") for output.
  Step 4 — Wire DataCompletionChecker.

position-balance-monitor:
  Step 1 — Wire ServiceCLI, BaseModeHandler (live mode primary).
  Step 2 — Wire get_writer("positions") for snapshots.
  Step 3 — Wire DataCompletionChecker for gap detection.

pnl-attribution-service:
  Step 1 — Wire ServiceCLI, BatchOrchestrator.
  Step 2 — Wire get_reader("execution_fills"), get_reader("positions"),
           get_reader("strategy_instructions") for inputs.
  Step 3 — Wire get_writer("pnl_attribution") for output.
  Step 4 — Wire DataCompletionChecker.

execution-services Phase 1:
  Step 1 — Fix P0 hardcoded project ID: find any `"central-element-323112"` in source.
           Replace with config.gcp_project_id.
  Step 2 — Wire ServiceCLI, BaseModeHandler (live mode).
  Step 3 — OMS protocols: ensure execution-services imports UnifiedOrderManager, OrderTracker,
           SmartOrderRouter from unified_trade_execution_interface (Agent 6 built these).
           Delete any local duplicates.

Cross-cutting rollout (check ALL services, apply to those missing):
  GracefulShutdownHandler:
    grep -rln "GracefulShutdownHandler" */
    For each service NOT in the results: add shutdown handler wiring in main.py / entrypoint.
    Pattern: signal.signal(SIGTERM, handler.handle_shutdown); signal.signal(SIGINT, handler.handle_shutdown)
  BaseDependencyChecker:
    grep -rln "BaseDependencyChecker" */
    For each service NOT in the results: add pre-flight check in entrypoint.
    Pattern: checker = BaseDependencyChecker(config); checker.check_all()  # raises on failure

═══════════════════════════════════════════════════════════════
SECTION 8 — FINAL SMOKE CHECK
(This is the FIRST AND ONLY point where any verification runs.
 Still no pytest. Still no quality-gates.sh. Still no commits.
 Only python -c import checks and assertions.)
═══════════════════════════════════════════════════════════════

⛔ GATE: Do NOT reach this section until Phases 0, 1, 2, and 3 are ALL complete.

After all phases complete, run these checks. Each python -c must print OK with no exception.
If any fail: go back and fix the code. Do NOT try to fix by running tests.

  python -c "from unified_cloud_interface import StorageClient, get_storage_client, CloudProvider"
  python -c "from unified_config_interface import UnifiedCloudConfig, BaseConfig"
  python -c "from unified_events_interface import setup_events, log_event, MockEventSink"
  python -c "from unified_trading_services import GCSEventSink, handle_api_errors, ServiceCLI, BatchOrchestrator"
  python -c "from unified_trading_services import with_retry, BaseModeHandler"
  python -c "from unified_domain_client import InstrumentsDomainClient, DataCompletionChecker"
  python -c "from unified_domain_client import PATH_REGISTRY, get_reader, get_writer, ReadMode"
  python -c "from unified_domain_client import MLModelsDomainClient, StrategyDomainClient"
  python -c "from unified_market_interface import CanonicalFundingRate, BaseWebSocketClient, VenueRateLimiter"
  python -c "from unified_trade_execution_interface import UnifiedOrderManager, OrderTracker"
  python -c "from unified_feature_interface import FeatureCalculatorRegistry, BaseFeatureService"
  python -c "from unified_reference_data_interface import get_reference_adapter, BaseReferenceAdapter"

Verify PATH_REGISTRY contains all 20 datasets:
  python -c "
  from unified_domain_client import PATH_REGISTRY
  expected = {
    'raw_tick_data','processed_candles','instruments','corporate_actions',
    'delta_one_features','calendar_features','onchain_features','volatility_features',
    'ml_models','ml_model_metadata','ml_predictions','ml_training_artifacts',
    'strategy_orders','strategy_instructions','backtest_results','execution_fills',
    'positions','pnl_attribution','risk_metrics','nautilus_catalog'
  }
  missing = expected - set(PATH_REGISTRY.keys())
  assert not missing, f'Missing datasets: {missing}'
  print('PATH_REGISTRY OK — all 20 datasets present')
  "

Verify calendar path bug is fixed:
  python -c "
  from unified_domain_client import PATH_REGISTRY
  spec = PATH_REGISTRY['calendar_features']
  assert 'day={date}' in spec.path_template, 'BUG: calendar path still uses hyphen'
  assert 'day-' not in spec.path_template, 'BUG: calendar path still uses hyphen'
  print('calendar_features path OK — uses day={date}')
  "

Verify ml_predictions path bug is fixed:
  python -c "
  from unified_domain_client import PATH_REGISTRY
  spec = PATH_REGISTRY['ml_predictions']
  assert 'day={date}' in spec.path_template, 'BUG: ml_predictions path missing day= partition'
  print('ml_predictions path OK')
  "

Verify no stale domain symbols in UTS (formerly UCS):
  python -c "
  import unified_trading_services as uts
  stale = [s for s in ['create_domain_cloud_service','create_instruments_cloud_service',
                        'StandardizedDomainCloudService','DomainValidationConfig']
           if s in dir(uts)]
  assert not stale, f'Stale symbols still exported: {stale}'
  print('UTS __all__ clean — no stale domain symbols')
  "
