---
name: "Plan 4 — Service Hardening: Adopt Shared Abstractions, Eliminate Duplication"
overview: "Migrate all 14 services to adopt the shared service framework from Plans 1-3 library work. Eliminates ~100,000+ lines of duplicated boilerplate across services by: (1) replacing 14 custom CLI parsers with ServiceCLI, (2) replacing 8+ custom ModeHandler ABCs with BaseModeHandler, (3) replacing 8+ custom orchestrators with BatchOrchestrator, (4) replacing per-service retry/rate-limiting with @with_retry + VenueRateLimiter from UMI, (5) replacing per-service 'already processed' checks with DataCompletionChecker, (6) replacing instruments-service connectivity code with URDI, (7) unifying 4 feature services under BaseFeatureService + FeatureCalculatorRegistry. EXECUTION: REFACTOR-ONLY. No commits until ALL service code changes are done across all 14 services. Then quickmerge bottom-up: libraries first (UCS framework additions, UFC, UMI, URDI, UTEI, UDC), then services. Services have no cross-service file conflicts — can parallelize all 14 simultaneously. GATE: Plans 1+2+3 library framework todos (ucs-service-framework, udc-data-completion, umi-connectivity-framework, ufc-feature-service-base, utei-order-management, urdi-create-full) MUST be code-complete before any service migration starts."
todos:
  - id: p4-preflight
    content: "Plan 4 Pre-flight: Verify all library framework todos from Plan 2 are code-complete before starting service migration. Check: (1) UCS has ServiceCLI, BaseModeHandler, BatchOrchestrator, @with_retry exported from unified_trading_services; (2) UMI has BaseWebSocketClient, VenueRateLimiter; (3) UDC has DataCompletionChecker, get_available_date_range; (4) UFC has FeatureCalculatorRegistry, BaseFeatureService; (5) URDI exists with BaseReferenceAdapter + venue adapters. Run: cd unified-trading-services && python -c 'from unified_trading_services import ServiceCLI, BaseModeHandler, BatchOrchestrator, with_retry; print(OK)'. If any fail, stop and complete the library work first."
    status: pending

  - id: p4-instruments-service
    content: "HARD BOUNDARY — instruments-service MUST NOT: hold API keys, import ccxt/databento/exchange SDKs, make HTTP/WebSocket calls to 3rd party APIs, or implement rate limiting. API key retrieval (get_secret_client) is done INSIDE URDI adapters, not in the service. instruments-service calls get_reference_adapter(venue).get_instruments() and receives CanonicalInstrument objects. It is blind to authentication, transport, and rate limiting. instruments-service Hardening — P0 (highest value): (1) CONNECTIVITY EXTRACTION: Replace all direct venue REST calls (engine/operations/ venue processors) with get_reference_adapter(venue).get_instruments() from unified_reference_data_interface. Delete: engine/operations/instruments/processors/cefi_processor.py, tradfi_processor.py, defi_processor.py venue REST logic — keep only the GCS write + domain orchestration. Delete: local _rate_limit() method and retry loops (these move to URDI via VenueRateLimiter + @with_retry). (2) CLI: Replace cli/parser.py (~356 lines) with ServiceCLI subclass (~30 lines). (3) ModeHandler: Replace any ModeHandler subclasses with BaseModeHandler subclass. (4) Orchestrator: Replace engine/operations/instruments/orchestrator.py (~301 lines) with BatchOrchestrator subclass. (5) DataCompletion: Replace corporate_actions_handler.py 'already processed' checks with DataCompletionChecker('instruments', ...).get_missing_dates(). (6) Domain writes: Use get_writer('instruments') from unified_domain_client.writers instead of inline GCS path construction. Target: instruments-service shrinks from 159 Python files to ~80 by delegating connectivity to URDI and framework to UCS."
    status: pending

  - id: p4-market-tick-data-handler
    content: "HARD BOUNDARY — market-tick-data-handler MUST NOT: hold API keys, import databento SDK directly in service code, make HTTP calls to Databento/Tardis/exchange REST endpoints, or implement rate limiting. API keys and all HTTP transport live inside UMI adapters. market-tick-data-handler calls get_market_data_adapter(venue, instrument_type).fetch_ticks(date, instruments) and receives CanonicalTick objects. It is blind to authentication, transport, and rate limiting. market-tick-data-handler Hardening — P0: (1) Rate limiting: Delete local rate_limit_delay + _rate_limit_request implementations; replace with VenueRateLimiter from UMI (already uses DatabentoIPRateLimiter — generalise). (2) Retry: Replace databento_client.py retry loop (~90 lines) with @with_retry from UCS. (3) CLI: Replace cli/main.py parser (~243 lines) with ServiceCLI subclass. (4) Orchestrator: Replace parallel_download_orchestrator.py + options_orchestrator.py with BatchOrchestrator subclass (handles date loop + asyncio.Semaphore concurrency). (5) DataCompletion: Replace _check_file_exists_cached (~50 lines) with DataCompletionChecker('raw_tick_data', ...).get_missing_dates(). (6) Domain writes: Replace gcs_path_utils.py path construction with get_writer('raw_tick_data') from UDC. Delete gcs_path_utils.py after migration. (7) Dependency checker: Extend BaseDependencyChecker (currently has own DependencyChecker). Target: shrink from 181 files toward ~100."
    status: pending

  - id: p4-market-data-processing
    content: "market-data-processing-service Hardening — P1: (1) CLI: Replace cli/parser.py (~236 lines) with ServiceCLI subclass. (2) Orchestrator: Replace app/core/orchestration_service.py (~1,256 lines) with BatchOrchestrator subclass — the date loop, _check_existing_outputs, parallel execution are all boilerplate that BatchOrchestrator handles. Service keeps only candle_processing_service.py core logic. (3) DataCompletion: _check_existing_outputs uses DataCompletionChecker. (4) Domain writes: Replace cloud_candle_storage.py + writer.py path construction with get_writer('processed_candles'). Delete local gcs_path_utils.py. (5) Domain reads: Replace cloud_data_provider.py with MarketTickDomainClient + InstrumentsDomainClient from UDC. (6) ModeHandler: live_mode_handler.py extends LiveModeHandler from UCS. Target: shrink from 125 files toward ~60."
    status: pending

  - id: p4-strategy-service
    content: "strategy-service Hardening — P1: (1) CLI: Replace cli/main.py parser (~241 lines) with ServiceCLI subclass. (2) ModeHandler: BatchHandler (~38 lines) extends BatchModeHandler from UCS. (3) Domain writes: Replace cloud_strategy_storage.py + gcs_storage_service.py path construction with get_writer('strategy_orders'), get_writer('strategy_instructions'), get_writer('backtest_results') from UDC. (4) Domain reads: strategy-service reads ml_predictions, delta_one_features, instruments — replace with MLPredictionsDomainClient, FeaturesDeltaOneDomainClient, InstrumentsDomainClient from UDC. (5) No WebSocket, no connectivity — keep as-is. Target: strategy-service focuses purely on signal logic."
    status: pending

  - id: p4-ml-services
    content: "ML Services Hardening (ml-training-service + ml-inference-service) — P1: ml-training-service: (1) Replace pd.date_range feature date loops with get_date_range from UCS. (2) Replace ThreadPoolExecutor(max_workers) + GCS feature reading (gcs_feature_reader.py, ~133 lines + parallelism) with BatchOrchestrator + get_reader('delta_one_features') from UDC. (3) Replace cli/main.py (~263 lines) with ServiceCLI. (4) Replace rolling/ewm mock feature logic with unified_feature_calculator library. (5) Align app/core/config_loader.py (~445 lines) — replace custom GCS config loading with ConfigStore from UCS. ml-inference-service: (1) Replace fixed 60s sleep retry in live_inference.py with @with_retry from UCS. (2) Replace cli/data_catalog.py custom logic with MLModelsDomainClient from UDC. (3) Replace ThreadPoolExecutor in orchestrator.py with BatchOrchestrator. (4) Fix ml predictions path from YYYY/MM/DD to day={date} Hive format (already tracked in library_ecosystem plan). Both: add GracefulShutdownHandler if not present."
    status: pending

  - id: p4-execution-services
    content: "execution-services Hardening — P2 (largest service, 661 files): Phase 1 (move OMS to UTEI): After utei-order-management todo in Plan 2 completes, update execution-services to import UnifiedOrderManager, OrderTracker, SmartOrderRouter from unified_trade_execution_interface instead of defining them locally. Phase 2 (WebSocket to UMI): venues/deribit.py WebSocket implementation → extend BaseWebSocketClient from UMI; delete local WebSocket boilerplate. Repeat for OKX, Binance WS venues once UMI base is ready. Phase 3 (path/domain cleanup): Replace backtest.py hardcoded gs://execution-store-central-element-323112 (P0 violation) with get_writer('execution_fills') from UDC. Replace preflight.py (~2,262 lines) where it does GCS checks with DataCompletionChecker + InstrumentsDomainClient. Phase 4 (rate limiting): Replace klines.py and async_klines.py rate_limit_delay implementations with VenueRateLimiter from UMI. Phase 5 (CLI): Replace argument_parser.py with ServiceCLI subclass. NOTE: execution-services is the most complex service — do in phases, not all at once. Phase 1 is gated on UTEI order management work completing."
    status: pending

  - id: p4-features-services
    content: "Features Services Hardening (delta-one + calendar + onchain + volatility) — P1: Run 4 parallel agents, one per service. Common pattern for ALL 4: (1) FeatureCalculatorRegistry: each service registers its calculators with @CALCULATOR_REGISTRY.register('group_name')(cls). Delete local CALCULATOR_REGISTRY dicts and replace with UFC shared registry. (2) BaseFeatureService: each service's orchestrator extends BaseFeatureService from UFC. Delete local orchestration service (delta-one ~420 lines, volatility ~463 lines, calendar ~310 lines, onchain ~150 lines). (3) FeatureModeHandler: CLI mode handling extends FeatureModeHandler from UFC. (4) DataCompletion: get_missing_dates() for which feature dates need processing. (5) Domain writes: use get_writer('delta_one_features') etc. instead of local writer.py path construction. (6) Domain reads: use MarketCandleDomainClient / InstrumentsDomainClient from UDC. Service-specific differences that are FINE to keep: timeframe handling (delta-one only), onchain protocol types (macro_sentiment vs lending_rates etc.), volatility options underlying logic. features-calendar: delete local FeatureCalculator ABC, use UFC's. features-onchain: replace if/elif dispatch with registry. NOTE: features-calendar uses day-{date} path bug — fixed in library_ecosystem plan udc-path-registry todo, must land first."
    status: pending

  - id: p4-risk-position-pnl
    content: "Risk + Position + PnL Services Hardening — P2: risk-and-exposure-service: (1) CLI parser.py (~68 lines) → ServiceCLI. (2) Batch/live mode → BaseModeHandler. (3) Add @with_retry for external API calls. (4) Domain writes: use get_writer('risk_metrics') from UDC once pnl-attribution and risk write paths are defined. (5) Alert rate limiting (alert_rate_limit_seconds) — this is an alerting concern, keep locally. position-balance-monitor-service: (1) CLI → ServiceCLI. (2) ModeHandler → BaseModeHandler. (3) fill_event_consumer.py asyncio.sleep(1) backoff → @with_retry from UCS. (4) position_store_gcs.py path construction → get_writer('positions') from UDC. (5) Add unified-position-interface as dep (already tracked in Plan 2 pr-f-service-enforcement). pnl-attribution-service: (1) Implement PnL computation logic (currently TODO stubs). (2) Use get_writer('pnl_attribution') from UDC for output. (3) Use ExecutionDomainClient for fills input, StrategyDomainClient for strategy outputs. (4) CLI → ServiceCLI. (5) Initial git commit (repo has zero commits — must happen before Phase 2 quickmerge)."
    status: pending

  - id: p4-dependency-checker-rollout
    content: "BaseDependencyChecker Rollout — P1: unified-trading-services already has BaseDependencyChecker (449 lines). Only market-data-processing-service uses it. Migrate the other 3 custom dependency checkers: (1) market-tick-data-handler/engine/validation/dependency_checker.py (302 lines) → extend BaseDependencyChecker. (2) features-onchain-service/app/core/dependency_checker.py (324 lines) → extend BaseDependencyChecker. (3) execution-services preflight check GCS dependency logic (subset of 2,262-line preflight.py) → extend BaseDependencyChecker for the data availability checks. Execution-services startup checks (exchange connectivity, API keys, instrument availability) remain custom — they are execution-specific. BaseDependencyChecker handles: GCS bucket accessibility, required blobs present for date range, secret manager key availability."
    status: pending

  - id: p4-graceful-shutdown-rollout
    content: "GracefulShutdownHandler Rollout — P2: UCS provides GracefulShutdownHandler. Currently only ml-training, ml-inference, execution-services use it. Add to ALL 14 services: import and call setup_graceful_shutdown() in every cli/main.py or cli/parser.py entry point. This is a 1-2 line change per service. Verify: rg 'GracefulShutdownHandler|setup_graceful_shutdown' --include='*.py' across all 14 service repos — any service without it needs the 1-line add."
    status: pending

isProject: true
---

# Plan 4 — Service Hardening: Adopt Shared Abstractions

> **Execute FOURTH.** Starts only after Plan 2 library framework todos
> (ucs-service-framework, udc-data-completion, umi-connectivity-framework,
> ufc-feature-service-base, utei-order-management, urdi-create-full) are code-complete.
> All 14 services can be refactored in parallel — no cross-service file conflicts.

---

## Architecture Principle

Services are **orchestration and domain logic only**. They do NOT own:
- Venue connectivity (REST, WebSocket, rate limiting) → UMI / UTEI / URDI
- Cloud I/O primitives (GCS paths, bucket names) → UDC PathRegistry
- CLI parsing boilerplate → UCS ServiceCLI
- Retry/backoff logic → UCS @with_retry
- Mode handling boilerplate → UCS BaseModeHandler
- Batch orchestration boilerplate → UCS BatchOrchestrator
- Missing data detection → UDC DataCompletionChecker

Each service should be **thin** — it delegates everything structural to libraries
and contains only the domain-specific computation that makes it unique.

---

## Estimated Impact

| Abstraction | Lines eliminated across 14 services |
|---|---|
| ServiceCLI (CLI parsers) | ~3,500 |
| BaseModeHandler / BatchModeHandler | ~500 |
| BatchOrchestrator (date loops) | ~4,000 |
| @with_retry (retry/backoff) | ~300 |
| DataCompletionChecker | ~400 |
| UDC path/bucket construction | ~2,000 |
| FeatureCalculatorRegistry + BaseFeatureService | ~1,500 |
| URDI (instruments connectivity) | ~3,000 |
| OMS → UTEI | ~400 |
| WebSocket → UMI | ~300 |
| BaseDependencyChecker rollout | ~600 |
| **Total** | **~16,500 service lines** |

With library implementations (~2,000 lines total), **net reduction ≈ 14,500 lines**.
Maintenance burden drops proportionally — a change to retry behaviour updates 1 library,
not 14 services.

---

## Ordering Within Plan 4

```
Phase 0: p4-preflight (verify library todos complete)

Phase 1 (all in parallel — zero conflicts):
  p4-instruments-service      ← highest value, URDI connectivity extraction
  p4-market-tick-data-handler ← rate limiting + gcs_path_utils removal
  p4-market-data-processing   ← orchestrator largest target (1,256 lines)
  p4-features-services        ← 4 services, 4 parallel agents
  p4-ml-services              ← 2 services, 2 parallel agents
  p4-dependency-checker-rollout ← low-risk 1:1 replacements
  p4-graceful-shutdown-rollout  ← trivial 1-line adds

Phase 2 (after Phase 1 done):
  p4-strategy-service
  p4-risk-position-pnl

Phase 3 (gated on UTEI + UMI framework complete):
  p4-execution-services       ← most complex, phased execution
```
