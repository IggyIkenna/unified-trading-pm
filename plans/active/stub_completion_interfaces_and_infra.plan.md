---
name: stub_completion_interfaces_and_infra
overview: >
  Complete all `raise NotImplementedError` stubs and unimplemented TODO placeholders across interface adapter repos
  (URDI, UMI, UTEI, UPI), cloud infrastructure (UCI factory + AWS provider), and deployment-api that are not
  specifically tracked in any other active plan. Key-blocked items (API keys not yet in SM) are included but marked
  BLOCKED pending api_keys_and_auth.plan.md resolution.
status: active
created: 2026-03-09
---

# Stub Completion — Interfaces & Infrastructure (Plan #32)

## Context

A workspace-wide scan (2026-03-09) found **187 `raise NotImplementedError` occurrences** and **57 `# TODO` comments** in
Python source files (excluding tests, archive, venvs). The majority cluster in interface adapter repos. This plan covers
only items **not specifically targeted by any other active plan**:

| Already covered elsewhere — do NOT duplicate                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------------- |
| IBKR adapters in UMI / UTEI / UPI / URDI → `ibkr_gateway_rollout.plan.md`                                                               |
| API-key-blocked adapters (Betfair, Pinnacle, Kalshi, Coinbase, Smarkets, Betdaq) → `api_keys_and_auth.plan.md`                          |
| T4 service stubs (execution, features-_, risk, strategy-validation, instruments, ml-_) → `phase3_service_hardening_integration.plan.md` |
| T5 API stubs (execution-results-api) → `phase3_service_hardening_integration.plan.md`                                                   |
| UDC athena/bq_external readers → `phase2_library_tier_hardening.plan.md` (T3 code-rewrite)                                              |
| Trading-agent-service l3 placeholder → `tradfi_expansion.plan.md`                                                                       |
| Test-failure root causes RC-1 to RC-13 → `unit_tests_and_test_failure_action.plan.md`                                                   |
| UCI GCP concrete providers (archived complete) → `uci_cloud_abstraction_complete.plan.md`                                               |

---

## Track A — URDI Venue Adapter Stubs

**Repo:** `unified-reference-data-interface` **File pattern:** `unified_reference_data_interface/adapters/<venue>.py`

These adapters raise `NotImplementedError` for `get_funding_rate()` and `get_ohlcv()`. None require API keys for the
public REST endpoints (public market data only).

### Todos

- [ ] `urdi-binance-funding-ohlcv` — Implement `get_funding_rate()` + `get_ohlcv()` in `adapters/binance.py` using the
      Binance public REST endpoints (`/fapi/v1/fundingRate`, `/fapi/v1/klines`). Return `CanonicalFundingRate` /
      `CanonicalOHLCV` from UAC schemas.

- [ ] `urdi-bybit-funding-ohlcv` — Implement `get_funding_rate()` + `get_ohlcv()` in `adapters/bybit.py` using Bybit V5
      public endpoints (`/v5/market/funding/history`, `/v5/market/kline`).

- [ ] `urdi-ccxt-methods` — Implement the 6 stub methods in `adapters/ccxt_adapter.py` (funding rate fetch, OHLCV fetch,
      and any other `raise NotImplementedError` present). Delegate to `ccxt` unified API methods
      (`fetch_funding_rate_history`, `fetch_ohlcv`).

- [ ] `urdi-coinbase-funding-ohlcv` — `adapters/coinbase.py` raises `NotImplementedError` for funding rates (Coinbase
      Advanced does not support perpetuals — return `UnsupportedVenueCapabilityError`) and OHLCV (implement via
      `/api/v3/brokerage/products/{product_id}/candles`). Options stubs may raise `UnsupportedVenueCapabilityError` with
      clear message.

- [ ] `urdi-deribit-methods` — Implement `get_funding_rate()` + `get_ohlcv()` in `adapters/deribit.py` via public REST
      (`/public/get_funding_rate_history`, `/public/get_tradingview_chart_data`).

- [ ] `urdi-hyperliquid-methods` — `adapters/hyperliquid.py` has 4 stubs: options not supported (return
      `UnsupportedVenueCapabilityError`), expiry calendar (`NotImplementedError`), funding rates (`/info` endpoint
      `fundingHistory`), OHLCV (`/info` candleSnapshot).

- [ ] `urdi-okx-funding-ohlcv` — Implement `get_funding_rate()` (`/api/v5/public/funding-rate-history`) and
      `get_ohlcv()` (`/api/v5/market/history-candles`) in `adapters/okx.py`.

- [ ] `urdi-polygon-methods` — `adapters/polygon.py`: funding rates not applicable for equities/options (return
      `UnsupportedVenueCapabilityError`); implement OHLCV via Polygon Aggregates API
      (`/v2/aggs/ticker/{ticker}/range/...`).

- [ ] `urdi-polymarket-methods` — `adapters/polymarket.py` has 4 stubs. Prediction market has no perpetual funding
      (return `UnsupportedVenueCapabilityError`). Implement remaining methods via CLOB API.

- [ ] `urdi-tardis-methods` — Implement `get_funding_rate()` + `get_ohlcv()` in `adapters/tardis.py` via the Tardis
      Machine REST replay API or their datasets endpoint. **Note:** Tardis VCR cassette setup is tracked in
      `api_keys_and_auth.plan.md § phase-1`; this todo only concerns the stub implementation.

---

## Track B — UMI TradFi Adapter Stubs

**Repo:** `unified-market-interface` **File pattern:** `unified_market_interface/adapters/tradfi/<name>_adapter.py`

These adapters are all open/free data sources (ECB, FRED, OFR are free public APIs; OpenBB, Barchart, Yahoo Finance have
free tiers). HTTP keys where needed are handled by `api_keys_and_auth.plan.md § phase-2-http`; this plan covers only the
stub bodies.

### Todos

- [ ] `umi-ecb-impl` — Implement `adapters/tradfi/ecb_adapter.py` stubs. ECB Data Portal is a public API
      (`https://data-api.ecb.europa.eu`); no key required. Return `CanonicalMarketData` records.

- [ ] `umi-fred-impl` — Implement `adapters/tradfi/fred_adapter.py`. FRED API key in SM is tracked in
      `api_keys_and_auth.plan.md § phase-2-http` (openbb-fmp/fred group). Stub implementation should read key from
      `UnifiedCloudConfig` and call `https://api.stlouisfed.org/fred/series/observations`.

- [ ] `umi-ofr-impl` — Implement `adapters/tradfi/ofr_adapter.py`. OFR (Office of Financial Research) has a public REST
      API at `https://data.financialresearch.gov`. No key required.

- [ ] `umi-openbb-impl` — Implement `adapters/tradfi/openbb_adapter.py`. OpenBB-FMP key is tracked in
      `api_keys_and_auth.plan.md § phase-2-http`. Read key from `UnifiedCloudConfig`; use openbb-core installed package.

- [ ] `umi-barchart-impl` — Implement `adapters/tradfi/barchart_adapter.py` lines 353 and 364. Also unblocks
      `instruments-service/app/core/adapter_loader.py` line 75 and
      `instruments_service/engine/venues/venue_adapter_loader.py` line 75 which raise `NotImplementedError` when
      Barchart adapter is requested.

- [ ] `umi-yahoo-impl` — Implement `adapters/tradfi/yahoo_finance_adapter.py` stub. Use `yfinance` or direct Yahoo
      Finance v8 API (no key required for basic OHLCV/quote data).

---

## Track C — UMI DeFi + OnChain-Perps + Alt-Data Base Stubs

**Repo:** `unified-market-interface`

### Todos

- [ ] `umi-defillama-impl` — Implement stub in `adapters/defi/defillama_adapter.py` line 96. DefiLlama is a free public
      API (`https://api.llama.fi`); no key required.

- [ ] `umi-instadapp-impl` — `adapters/defi/instadapp_adapter.py` (2 stubs): InstaApp is an aggregator without a
      canonical REST API. Implement using on-chain read (Ethereum RPC) or the InstaApp subgraph. Document
      `UnsupportedVenueCapabilityError` for position data if aggregation-only.

- [ ] `umi-onchain-perps-base` — Implement `adapters/onchain_perps/base_onchain_perp_adapter.py` abstract methods
      `fetch_markets()` and `fetch_trades()`. These are the base class stubs that concrete adapters (GMX, dYdX,
      Synthetix, etc.) should override. Define correct return types using UAC schemas; add docstrings explaining what
      each concrete adapter must implement.

- [ ] `umi-alt-data-base` — Implement `adapters/alt_data/base_alt_data_adapter.py` line 65 `normalize_record()`. This is
      the base class hook; concrete adapters override it. Define the signature and return type (`CanonicalAltDataRecord`
      or similar) and raise `NotImplementedError` with a useful message guiding implementors.

---

## Track D — UMI Sports + Prediction Base Stubs

**Repo:** `unified-market-interface`

### Todos

- [ ] `umi-sports-base` — Implement `adapters/sports/base_sports_adapter.py` line 70 `normalize_odds()`. Define abstract
      signature returning `CanonicalOdds` (from UAC). Concrete adapters that inherit this (Betfair, Pinnacle, etc.) are
      tracked in `sports_migration_combined.plan.md` and `api_keys_and_auth.plan.md`.

- [ ] `umi-prediction-base` — Implement `adapters/prediction/base_prediction_adapter.py` `normalize_market()`. Define
      abstract return type and docstring consistent with `CanonicalPredictionMarket` (or create the schema in UAC if it
      does not exist).

---

## Track E — UMI WebSocket + API Stubs

**Repo:** `unified-market-interface`

### Todos

- [ ] `umi-api-stubs` — Implement 3 stub methods in `api.py` (lines 70, 155, 220). Identify what each method is supposed
      to do from context (likely `get_market_data`, `subscribe`, and `unsubscribe` or similar) and implement the body
      wiring to the appropriate adapter.

- [ ] `umi-websocket-manager` — Implement `websocket/manager.py` line 69 `connect()` method. This is the WebSocket
      connection manager entry point. Should establish connection using the venue-specific WS adapter and register
      message handlers.

---

## Track F — UTEI Order Feed WebSocket Stubs

**Repo:** `unified-trade-execution-interface` **File:** `unified_trade_execution_interface/ws_feeds.py`

The file has 3 × 2 = 6 stubs for order feed connections (connect + message handler for each venue). **IBKR** is covered
by `ibkr_gateway_rollout.plan.md`. This covers Binance, Bybit, OKX.

### Todos

- [ ] `utei-binance-order-feed` — Implement `ws_feeds.py` lines 47 and 52: Binance order update WebSocket feed. Use
      Binance User Data Stream (`wss://stream.binance.com:9443/ws/<listenKey>`). Key setup is tracked in
      `api_keys_and_auth.plan.md § phase-2-ws`.

- [ ] `utei-bybit-order-feed` — Implement lines 71 and 76: Bybit private order stream
      (`wss://stream.bybit.com/v5/private`). Authentication via HMAC-SHA256.

- [ ] `utei-okx-order-feed` — Implement lines 95 and 100: OKX private orders channel
      (`wss://ws.okx.com:8443/ws/v5/private`, channel `orders`).

---

## Track G — UPI Venue Adapter Stubs (BLOCKED — key-dependent)

**Repo:** `unified-position-interface` **File pattern:** `unified_position_interface/adapters/<venue>.py`

These adapters need authenticated REST calls to fetch balances and positions. Blocked until relevant API keys are in SM
via `api_keys_and_auth.plan.md`. Grouped by blocker phase.

**Blocked on api_keys_and_auth Phase 2 (HTTP key setup):**

- [ ] `upi-binance-impl` — `[BLOCKED: api_keys_and_auth phase-2-http]` Implement `get_balance()` + `get_positions()` in
      `adapters/binance.py` using `/sapi/v1/asset/wallet/balance` and `/fapi/v2/positionRisk`.

- [ ] `upi-bybit-impl` — `[BLOCKED: api_keys_and_auth phase-2-http]` Implement using Bybit V5
      `/v5/account/wallet-balance` and `/v5/position/list`.

- [ ] `upi-deribit-impl` — `[BLOCKED: api_keys_and_auth phase-2-http]` Implement using Deribit
      `/private/get_account_summary` and `/private/get_positions`.

- [ ] `upi-okx-impl` — `[BLOCKED: api_keys_and_auth phase-2-http]` Implement using OKX `/api/v5/account/balance` and
      `/api/v5/account/positions`.

- [ ] `upi-hyperliquid-impl` — `[BLOCKED: api_keys_and_auth phase-2-http]` Implement using Hyperliquid REST `/info`
      (clearinghouse state + perpetuals position).

- [ ] `upi-ccxt-impl` — `[BLOCKED: api_keys_and_auth phase-2-http]` Implement using `ccxt.fetchBalance()` and
      `ccxt.fetchPositions()` for the ccxt adapter.

**Blocked on api_keys_and_auth Phase 3:**

- [ ] `upi-polymarket-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` Implement using Polymarket CLOB REST API;
      requires Polymarket credentials.

**Blocked on api_keys_and_auth Phase 4:**

- [ ] `upi-betfair-impl` — `[BLOCKED: api_keys_and_auth phase-4-blockers]` Implement using Betfair Accounts API;
      requires partner key.

**REST fallback (no key dependency):**

- [ ] `upi-upbit-impl` — `adapters/upbit.py` comment says "not yet implemented — use REST API". Upbit has authenticated
      REST endpoints; key is standard exchange key. Implement `/v1/accounts` for balance and `/v1/positions` for
      positions.

---

## Track H — UMI OnChain Adapter Stubs (BLOCKED — key-dependent)

**Repo:** `unified-market-interface`

Blocked until keys are in SM via `api_keys_and_auth.plan.md § phase-3-keys`.

- [ ] `umi-mev-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` Implement `adapters/onchain/mev_adapter.py` lines 60,
      71, 87 once MEV provider key is available.

- [ ] `umi-glassnode-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` Implement
      `adapters/onchain/glassnode_adapter.py` lines 59, 69, 84 once Glassnode key is in SM.

- [ ] `umi-arkham-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` Implement `adapters/onchain/arkham_adapter.py`
      lines 54, 64, 79 once Arkham Intelligence key is in SM.

---

## Track I — UCI Cloud Infrastructure Stubs

**Repo:** `unified-cloud-interface`

`uci_cloud_abstraction_complete.plan.md` is archived as "all code complete" for GCP providers. These two remaining items
were not resolved:

### Todos

- [ ] `uci-cloud-logging` — `unified_cloud_interface/factory.py` line 333: cloud logging provider is not yet
      implemented. Identify what cloud logging provider type is expected (GCP Cloud Logging via `google.cloud.logging`?
      Structured JSON stdout adapter?), implement the concrete provider, and register it in the factory dispatch.

- [ ] `uci-aws-provider` — `unified_cloud_interface/providers/aws.py` line 106: one method is explicitly marked "not
      implemented". Identify the method from context, implement it using `boto3` (via UCI's `_aws_client()` helper —
      never call `boto3` directly in services), and add a VCR or moto test.

---

## Track J — Deployment-API Stubs

**Repo:** `deployment-api` **Note:** `deployment-api` is NOT in phase3's T5 scope (T5 = execution-results-api,
market-data-api, client-reporting-api). These stubs are untracked.

### Todos

- [ ] `deployment-api-cache` — `deployment_api/utils/cache.py` lines 78, 81, 84, 87: 4 abstract cache methods not
      implemented. Identify the cache strategy in use (Redis? In-memory LRU? GCS-backed?), implement the concrete class,
      and wire it into the DI container.

- [ ] `deployment-api-prometheus` — `deployment_api/main.py` line 64: `PrometheusMiddleware` is disabled with
      `# TODO GH-BACKLOG`. Re-enable it. Verify `prometheus-client` is in `pyproject.toml`; ensure the `/metrics`
      endpoint is exposed. This is a prerequisite for `observability_and_health_endpoints.plan.md` coverage of
      deployment-api.

---

## Track K — Untracked TODO/FIXME Items (2026-03-09 Audit)

These items were found during the Section 13 audit scan and are not covered by any other active plan.

### Todos

- [ ] `todo-client-reporting-prometheus` — `client-reporting-api/client_reporting_api/api/main.py:12,44` —
      PrometheusMiddleware and `get_metrics_response` are not yet implemented in UTL; re-enable once available. Verify
      `prometheus-client` in `pyproject.toml` and expose `/metrics` endpoint.

- [ ] `todo-deployment-api-uci-cloud-build` — `deployment-api/deployment_api/routes/cloud_builds.py:42` and
      `deployment_api/routes/service_status_checkers.py:355` — migrate direct GCP CloudBuild calls to UCI
      `CloudBuildClient` abstraction once that client is available in `unified-cloud-interface`.

- [ ] `todo-deployment-service-league-config-import` — `deployment-service/scripts/sports/verify_league_config.py:348` —
      replace the inline workaround with an actual import from the league config module when that module is available.

- [ ] `todo-features-commodity-signal-composer` — `features-commodity-service/features_commodity_service/cli/main.py:93`
      — wire `engine.signal_composer.SignalComposer` per commodity asset class; currently the CLI exits without running
      signal composition.

- [ ] `todo-features-delta-one-subscriber-orchestration` —
      `features-delta-one-service/features_delta_one_service/app/pubsub/subscriber.py:115` — parse incoming candle data,
      invoke the feature orchestration pipeline, and publish computed features to EventBus (referenced as Task 6.1.4).

- [ ] `todo-instruments-config-reloader-hook` — `instruments-service/instruments_service/config_reloaders.py:22` — hook
      the config reloader into `InstrumentsService` subscription list so live reload triggers a real subscription update
      instead of a no-op.

- [ ] `todo-instruments-gcs-upload-handlers` —
      `instruments-service/instruments_service/cli/handlers/corporate_actions_backfill_handler.py:572` and
      `instruments_service/cli/handlers/generate_date_views_handler.py:242` — implement optional GCS upload using
      `DataSink.upload()` from UCI when `--upload` flag is passed.

- [ ] `todo-instruments-defi-adapter-explicit-imports` —
      `instruments-service/instruments_service/app/core/adapter_loader.py:82,120-164` — replace wildcard
      `from unified_market_interface import <Adapter>` inline imports with explicit top-level imports so basedpyright
      can resolve types. Covers HyperliquidAdapter, UniswapV2/V3/V4, AaveV3, Curve, Balancer, Morpho, Euler, Fluid,
      Lido, EtherFi, Ethena adapters.

- [ ] `todo-ml-training-model-registry-explicit-imports` —
      `ml-training-service/ml_training_service/ml/model_registry.py:33,34` — replace inline import markers for
      `ModelMetadata` and `ModelVariantConfig` with explicit module paths once those symbols are exported from a stable
      UTL or UMI sub-module.

- [ ] `todo-execution-loader-explicit-import` — `execution-service/execution_service/utils/io/loader.py:10` — replace
      `from unified_trading_library import BaseGCSLoader` wildcard with an explicit sub-module import path once
      `BaseGCSLoader` is exported from a stable public UTL API.

- [ ] `todo-risk-cli-client-list` — `risk-and-exposure-service/risk_and_exposure_service/cli/main.py:94` — implement
      retrieval of the full client list from `UnifiedCloudConfig` or a config database; currently the `--all-clients`
      CLI flag is a no-op stub.

---

## Cross-Repo Sequencing

```
Track A (URDI stubs) ──────────────────────────────────> [ urdi-* todos ]
Track B (UMI TradFi stubs) ────────────────────────────> [ umi-ecb/fred/ofr/openbb/barchart/yahoo ]
Track C (UMI DeFi + base stubs) ───────────────────────> [ umi-defillama/instadapp/onchain-base/alt-data-base ]
Track D (UMI Sports + Prediction base) ────────────────> [ umi-sports-base / umi-prediction-base ]
Track E (UMI WS + API) ────────────────────────────────> [ umi-api-stubs / umi-websocket-manager ]
Track F (UTEI WS feeds) ───────────────────────────────> [ utei-binance/bybit/okx-order-feed ]
Track I (UCI infra) ───────────────────────────────────> [ uci-cloud-logging / uci-aws-provider ]
Track J (deployment-api) ──────────────────────────────> [ deployment-api-cache / deployment-api-prometheus ]
Track K (untracked audit TODOs) ───────────────────────> [ todo-client-reporting-prometheus / todo-deployment-api-uci-cloud-build /
                                                           todo-features-commodity-signal-composer / todo-features-delta-one-subscriber-orchestration /
                                                           todo-instruments-config-reloader-hook / todo-instruments-gcs-upload-handlers /
                                                           todo-instruments-defi-adapter-explicit-imports / todo-ml-training-model-registry-explicit-imports /
                                                           todo-execution-loader-explicit-import / todo-risk-cli-client-list ]

api_keys_and_auth.plan.md phases 2–4 ─UNBLOCKS──> Track G (UPI impls) + Track H (UMI onchain)
```

Tracks A–F, I, J have no external blockers and can start immediately in any order.

---

## Quality Gate Requirements

Each completed todo must satisfy:

1. `basedpyright unified_*/` — zero new errors introduced
2. `ruff check <file> --fix && ruff format <file>` — clean
3. Test coverage: add at least one unit test using VCR cassette or `pytest-mock` per new adapter method; coverage must
   not drop below the repo's `MIN_COVERAGE` threshold
4. No `os.getenv()` — use `UnifiedCloudConfig`
5. No `try/except ImportError` — fail loud
6. Commit per-repo with `bash scripts/quickmerge.sh "feat: implement <stub-name>"` (or `--to-staging` if method is a
   breaking interface change)

---

## Appendix — Deferred Items (covered by other plans)

| Stub / TODO                                           | Location                                                 | Covered by                                                            |
| ----------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- |
| IBKR adapters (UMI/UTEI/UPI/URDI)                     | `adapters/ibkr.py` × 4 repos                             | `ibkr_gateway_rollout.plan.md`                                        |
| Betfair/Kalshi/Coinbase/Smarkets/Betdaq WS            | UTEI ws_feeds.py                                         | `api_keys_and_auth.plan.md § phase-4`                                 |
| execution-service PostgreSQL persistence              | `engine/live/persistence/postgresql.py`                  | `phase3_service_hardening_integration.plan.md`                        |
| execution-service config_reloaders TODOs              | `config_reloaders.py:54,72`                              | `phase3_service_hardening_integration.plan.md`                        |
| features-delta-one futures_roll_adjuster              | `app/core/futures_roll_adjuster.py:341-346`              | `phase3_service_hardening_integration.plan.md`                        |
| features-cross-instrument cli TODO                    | `cli/main.py:84-101`                                     | `phase3_service_hardening_integration.plan.md`                        |
| features-multi-timeframe EventBus TODO                | `app/engine/orchestrator.py:210`                         | `phase3_service_hardening_integration.plan.md`                        |
| risk-and-exposure compute_handler + cash reserve      | `compute_handler.py:30`, `pre_trade_check_engine.py:332` | `safety_and_risk_controls.plan.md`                                    |
| strategy-validation-service validation logic          | `cli/main.py:107`                                        | `phase3_service_hardening_integration.plan.md`                        |
| execution-results-api abstract services (24 stubs)    | `services/data_service_*.py` × 6 files                   | `phase3_service_hardening_integration.plan.md`                        |
| ml-training cascade_meta_model_trainer                | `app/training/cascade_meta_model_trainer.py:44`          | `phase3_service_hardening_integration.plan.md`                        |
| instruments-service barchart + defi_processor         | `adapter_loader.py:75,100`, `defi_processor.py:175`      | `phase3_service_hardening_integration.plan.md`                        |
| trading-agent-service estimated_price placeholder     | `app/loops/l3_trade_decision.py`                         | `tradfi_expansion.plan.md`                                            |
| execution-service manual_instruction_api account_id   | `api/manual_instruction_api.py`                          | `phase3_service_hardening_integration.plan.md`                        |
| UCI abstractions.py base class stubs                  | `abstractions.py:91-566`                                 | Abstract base pattern — concrete GCP impls complete per archived plan |
| UDC athena + bq_external readers                      | `readers/athena.py`, `readers/bq_external.py`            | `phase2_library_tier_hardening.plan.md § t3-udc-code-rewrite`         |
| UMI footystats + soccer_football adapters             | `adapters/alt_data/footystats_adapter.py`                | `api_keys_and_auth.plan.md § phase-3-keys`                            |
| execution-service ADAPTIVE_TWAP / ALMGREN_CHRISS port | `scripts/migrate_to_library_algorithms.py:31-32`         | `phase2_library_tier_hardening.plan.md § t0-code-rewrite` (EAL)       |
