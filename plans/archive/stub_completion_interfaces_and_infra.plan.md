---
doc_type: plan
title: stub-completion-interfaces-and-infra
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [client-reporting-api, deployment-api, deployment-service, execution-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-09
overview:
  Complete all raise NotImplementedError stubs and unimplemented TODOs across URDI, UMI, UTEI, UPI, UCI, and
  deployment-api not tracked by other active plans.
type: code
epic: epic-code-completion
archived: 2026-03-11
archive_reason:
  "All unblocked tracks complete (A-F, I, J, K, UAC — 35+ todos done). Blocked items migrated: UPI adapters (8) + UMI
  onchain (3) → api_keys_and_auth.md in plans/ai/; GH-BACKLOG items (5) → phase3_service_hardening_integration.md."
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - {
      repo: unified-reference-data-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-market-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-trade-execution-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-position-interface,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "Track G items (UPI venue impls) remain blocked on api_keys_and_auth phase-2 to phase-4. DR N/A: code-completion
        epic scope. BR N/A: no commercial sign-off required.",
    }
  - {
      repo: unified-cloud-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: deployment-api,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-api-contracts,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
depends_on: [api_keys_and_auth]
todos:
  - {
      id: upi-binance-impl,
      content:
        "[BLOCKED: api_keys_and_auth phase-2-http] Implement get_balance()+get_positions() in adapters/binance.py",
      status: blocked,
      note: "",
    }
  - {
      id: upi-bybit-impl,
      content: "[BLOCKED: api_keys_and_auth phase-2-http] Implement using Bybit V5 wallet-balance and position/list",
      status: blocked,
      note: "",
    }
  - {
      id: upi-deribit-impl,
      content: "[BLOCKED: api_keys_and_auth phase-2-http] Implement using Deribit private endpoints",
      status: blocked,
      note: "",
    }
  - {
      id: upi-okx-impl,
      content: "[BLOCKED: api_keys_and_auth phase-2-http] Implement using OKX account/balance and positions",
      status: blocked,
      note: "",
    }
  - {
      id: upi-hyperliquid-impl,
      content: "[BLOCKED: api_keys_and_auth phase-2-http] Implement using Hyperliquid REST /info",
      status: blocked,
      note: "",
    }
  - {
      id: upi-ccxt-impl,
      content: "[BLOCKED: api_keys_and_auth phase-2-http] Implement using ccxt.fetchBalance()+fetchPositions()",
      status: blocked,
      note: "",
    }
  - {
      id: upi-polymarket-impl,
      content: "[BLOCKED: api_keys_and_auth phase-3-keys] Implement using Polymarket CLOB REST API",
      status: blocked,
      note: "",
    }
  - {
      id: upi-betfair-impl,
      content: "[BLOCKED: api_keys_and_auth phase-4-blockers] Implement using Betfair Accounts API",
      status: blocked,
      note: "",
    }
  - {
      id: risk-batch-compute-unimplemented,
      content: "Implement _compute_batch_risk() in risk-and-exposure-service compute_handler.py:30",
      status: todo,
      note: "",
    }
  - {
      id: pre-trade-cash-reserve-check,
      content: "Wire _check_cash_reserves() to live position data in pre_trade_check_engine.py:420",
      status: completed,
      note:
        Implemented 2026-03-11 (commit 6ce535d). PositionMonitorClient has no live cash balance endpoint; used
        conservative proxy remaining_capacity=max_capital_deployed-new_capital. Fail-safe rejects when ceiling
        unconfigured. 5 unit tests added.,
    }
  - {
      id: gas-estimator-live-umi-feed,
      content: "Replace static gas price lookup with get_price() from UMI in gas_estimator.py:175",
      status: todo,
      note: "",
    }
isProject: false
---

## Deferred work — migrated to: `plans/active/issues/strategy_service_batch_risk_compute_unimplemented_2026_07_21.md` — successor:

strategy_service_batch_risk_compute_unimplemented_2026_07_21 (verified 2026-07-21, batch-5 archived-plan discipline
triage). Tracks G+H (UPI venue adapters, UMI onchain, 11 items) are MOOT — `unified-position-interface` was eliminated
2026-03-26 (merged into position-balance-monitor-service), which was itself eliminated 2026-05-20
(`plans/active/bucket_fold_portfolio_state_2026_07_17.md`); neither the target repo nor the target file paths exist
anymore. Of Track L's 5 GH-BACKLOG items: `risk-batch-compute-unimplemented` is the one genuinely still-open item —
migrated to the new issue doc above (this plan's own stated successor, `phase3_service_hardening_integration.plan.md`,
inherited it unchanged and was itself superseded without ever addressing it). `gas-estimator-live-umi-feed` is MOOT
(target file no longer exists, rebalancing rearchitected). `futures-roll-adjuster-calendar` and
`futures-basis-mark-price-features` are MOOT (both closed by named archived plans). `balancer-eth-venue-implementation`
is likely done (implemented in market-tick-data-service's DeFi adapters) — folded into the new issue doc as a
low-priority verify-or-close item since the original target repo isn't in this workspace checkout.

# Stub Completion — Interfaces & Infrastructure (Plan #32)

## Context

A workspace-wide scan (2026-03-09) found **187 `raise NotImplementedError` occurrences** and **57 `# TODO` comments** in
Python source files (excluding tests, archive, venvs). The majority cluster in interface adapter repos. This plan covers
only items **not specifically targeted by any other active plan**:

| Already covered elsewhere — do NOT duplicate                                                                                       |
| ---------------------------------------------------------------------------------------------------------------------------------- |
| IBKR adapters in UMI / UTEI / UPI / URDI → `ibkr_gateway_rollout.md`                                                               |
| API-key-blocked adapters (Betfair, Pinnacle, Kalshi, Coinbase, Smarkets, Betdaq) → `api_keys_and_auth.md`                          |
| T4 service stubs (execution, features-_, risk, strategy-validation, instruments, ml-_) → `phase3_service_hardening_integration.md` |
| T5 API stubs (execution-results-api) → `phase3_service_hardening_integration.md`                                                   |
| UDC athena/bq_external readers → `phase2_library_tier_hardening.md` (T3 code-rewrite)                                              |
| Trading-agent-service l3 placeholder → `tradfi_expansion.md`                                                                       |
| Test-failure root causes RC-1 to RC-13 → `unit_tests_and_test_failure_action.md`                                                   |
| UCI GCP concrete providers (archived complete) → `uci_cloud_abstraction_complete.md`                                               |

---

## Track A — URDI Venue Adapter Stubs

**Repo:** `unified-reference-data-interface` **File pattern:** `unified_reference_data_interface/adapters/<venue>.py`

These adapters raise `NotImplementedError` for `get_funding_rate()` and `get_ohlcv()`. None require API keys for the
public REST endpoints (public market data only).

### Todos

- [x] `urdi-binance-funding-ohlcv` — DONE 2026-03-09 commit `993f706`: `get_funding_rate()` via `/fapi/v1/premiumIndex`;
      `get_ohlcv()` via `/fapi/v1/klines`.

- [x] `urdi-bybit-funding-ohlcv` — DONE 2026-03-09 commit `993f706`: `get_funding_rate()` via
      `/v5/market/funding/history?limit=1`; `get_ohlcv()` via `/v5/market/kline` with interval mapping.

- [x] `urdi-ccxt-methods` — DONE 2026-03-09 commit `993f706`: all 6 stubs delegated to `ccxt.async_support`
      (`load_markets`, `fetch_funding_rate`, `fetch_ohlcv`); helpers extracted to stay within mccabe=7.

- [x] `urdi-coinbase-funding-ohlcv` — DONE 2026-03-09 commit `993f706`: funding rate raises `NotImplementedError` with
      domain explanation (no perpetuals); `get_ohlcv()` via `/api/v3/brokerage/products/{product_id}/candles`.

- [x] `urdi-deribit-methods` — DONE 2026-03-09 commit `993f706`: `get_funding_rate()` via
      `/public/get_funding_rate_history`; `get_ohlcv()` via `/public/get_tradingview_chart_data`.

- [x] `urdi-hyperliquid-methods` — DONE 2026-03-09 commit `993f706`: `get_funding_rate()` via
      `POST /info fundingHistory`; `get_ohlcv()` via `POST /info candleSnapshot`; options/expiry retain domain raises.

- [x] `urdi-okx-funding-ohlcv` — DONE 2026-03-09 commit `993f706`: `get_funding_rate()` via
      `/api/v5/public/funding-rate-history?limit=1`; `get_ohlcv()` via `/api/v5/market/history-candles`.

- [x] `urdi-polygon-methods` — DONE 2026-03-09 commit `993f706`: funding rate raises domain exception (equities);
      `get_ohlcv()` via `/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`.

- [x] `urdi-polymarket-methods` — DONE 2026-03-09 commit `993f706`: funding rate raises domain exception (no
      perpetuals); `get_ohlcv()` via CLOB `prices-history` synthetic OHLCV.

- [x] `urdi-tardis-methods` — DONE 2026-03-09 commit `993f706`: `get_funding_rate()` + `get_ohlcv()` via Tardis
      `/v1/data-feeds` NDJSON endpoint using `derivative_ticker` and `trade_bar_{interval}` channels.

---

## Track B — UMI TradFi Adapter Stubs

**Repo:** `unified-market-interface` **File pattern:** `unified_market_interface/adapters/tradfi/<name>_adapter.py`

These adapters are all open/free data sources (ECB, FRED, OFR are free public APIs; OpenBB, Barchart, Yahoo Finance have
free tiers). HTTP keys where needed are handled by `api_keys_and_auth.md § phase-2-http`; this plan covers only the stub
bodies.

### Todos

- [x] `umi-ecb-impl` — VERIFIED 2026-03-09: already fully implemented; `fetch_instruments`/`fetch_trades` raise
      `NotImplementedError` intentionally (rate/analytics adapter, no tradeable instruments).
- [x] `umi-fred-impl` — VERIFIED 2026-03-09: already fully implemented.
- [x] `umi-ofr-impl` — VERIFIED 2026-03-09: already fully implemented.
- [x] `umi-openbb-impl` — VERIFIED 2026-03-09: already fully implemented.
- [x] `umi-barchart-impl` — VERIFIED 2026-03-09: already fully implemented.
- [x] `umi-yahoo-impl` — VERIFIED 2026-03-09: already fully implemented.

---

## Track C — UMI DeFi + OnChain-Perps + Alt-Data Base Stubs

**Repo:** `unified-market-interface`

### Todos

- [x] `umi-defillama-impl` — VERIFIED 2026-03-09: already fully implemented; `get_instrument_metadata()` raises
      `NotImplementedError` intentionally (TVL/analytics adapter, no instrument definitions).
      `normalize_liquidity_pool()` and `normalize_chain_tvl()` are fully implemented via api-contracts Pydantic parsing.

- [x] `umi-instadapp-impl` — DONE 2026-03-09: Implemented `get_dsa_positions(account)` via The Graph free-tier subgraph
      (`https://api.thegraph.com/subgraphs/name/instadapp/dsa-v2`); returns canonical dicts with
      `venue/chain/account_id/version/authority/recent_casts/data_source/timestamp_utc`. `get_instrument_metadata` and
      `download_market_data` raise `NotImplementedError` with descriptive guidance (Instadapp is position aggregator
      only). Removed phantom fields (`type`/`collateralUsd`/etc.) from `_normalize_position` to match actual
      `InstadappPosition` schema. Three unit tests added: success path, empty accounts, custom subgraph URL. Commit:
      `f32938d` (unified-market-interface).

- [x] `umi-onchain-perps-base` — VERIFIED 2026-03-09: already fully implemented; `fetch_markets()` and `fetch_trades()`
      raise `NotImplementedError` with descriptive messages guiding concrete subclass implementors;
      `fetch_funding_rates()` has sensible default (logs warning, returns empty list).

- [x] `umi-alt-data-base` — VERIFIED 2026-03-09: already fully implemented; `normalize_record()` raises
      `NotImplementedError("Subclasses must implement normalize_record()")` — correct abstract base pattern.

---

## Track D — UMI Sports + Prediction Base Stubs

**Repo:** `unified-market-interface`

### Todos

- [x] `umi-sports-base` — VERIFIED 2026-03-09: already implemented; `normalize_odds()` is `@abstractmethod` overridden
      by all concrete sports adapters.
- [x] `umi-prediction-base` — VERIFIED 2026-03-09: already implemented; `normalize_market()` is `@abstractmethod`
      overridden by all concrete prediction adapters.

---

## Track E — UMI WebSocket + API Stubs

**Repo:** `unified-market-interface`

### Todos

- [x] `umi-api-stubs` — VERIFIED 2026-03-09: lines 70/155/220 are fallback error branches of fully implemented routing
      logic above them; no stub bodies present.
- [x] `umi-websocket-manager` — VERIFIED 2026-03-09: `connect()` is `@abstractmethod` in base;
      `BinanceWebSocketHandler.connect()` in `websocket/handlers/binance.py` is fully implemented.

---

## Track F — UTEI Order Feed WebSocket Stubs

**Repo:** `unified-trade-execution-interface` **File:** `unified_trade_execution_interface/ws_feeds.py`

The file has 3 × 2 = 6 stubs for order feed connections (connect + message handler for each venue). **IBKR** is covered
by `ibkr_gateway_rollout.md`. This covers Binance, Bybit, OKX.

### Todos

- [x] `utei-binance-order-feed` — DONE 2026-03-09 commit `e365bd6`: POST listenKey →
      `wss://stream.binance.com:9443/ws/{listenKey}`; `executionReport` → `CanonicalFill` / `CanonicalOrderRejection`.
- [x] `utei-bybit-order-feed` — DONE 2026-03-09 commit `e365bd6`: HMAC-SHA256 auth →
      `wss://stream.bybit.com/v5/private`; parses `Filled/Trade/Rejected/PartiallyFilledCanceled`.
- [x] `utei-okx-order-feed` — DONE 2026-03-09 commit `e365bd6`: HMAC-SHA256+base64 login →
      `wss://ws.okx.com:8443/ws/v5/private`; subscribes `orders instType=ANY`; 25s ping task.

---

## Track G — UPI Venue Adapter Stubs (BLOCKED — key-dependent)

**Repo:** `unified-position-interface` **File pattern:** `unified_position_interface/adapters/<venue>.py`

These adapters need authenticated REST calls to fetch balances and positions. Blocked until relevant API keys are in SM
via `api_keys_and_auth.md`. Grouped by blocker phase.

**Blocked on api_keys_and_auth Phase 2 (HTTP key setup):** _(agent hit usage quota 2026-03-09, re-run needed)_

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
      `ccxt.fetchPositions()`.

**Blocked on api_keys_and_auth Phase 3:**

- [ ] `upi-polymarket-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` Implement using Polymarket CLOB REST API.

**Blocked on api_keys_and_auth Phase 4:**

- [ ] `upi-betfair-impl` — `[BLOCKED: api_keys_and_auth phase-4-blockers]` Implement using Betfair Accounts API.

**REST fallback (no key dependency):**

- [x] `upi-upbit-impl` — DONE 2026-03-09: `UpbitPositionAdapter` fully implemented in `adapters/upbit.py`;
      `get_balances()` via `GET /v1/accounts` with JWT HS256 Bearer token; `get_positions()` returns `[]` (spot-only);
      credentials read via constructor args (called from factory with `api_key`/`api_secret`); 6 unit tests in
      `tests/unit/test_adapters.py` covering balance mapping, zero-total skip, positions empty, snapshot, auth header,
      and JWT structure — all passing.

---

## Track H — UMI OnChain Adapter Stubs (BLOCKED — key-dependent)

**Repo:** `unified-market-interface`

Blocked until keys are in SM via `api_keys_and_auth.md § phase-3-keys`.

- [ ] `umi-mev-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` VERIFIED 2026-03-09: correctly marked
      BLACKLISTED_NO_ACCESS; implement once MEV provider key in SM.
- [ ] `umi-glassnode-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` VERIFIED 2026-03-09: correctly marked
      BLACKLISTED_NO_ACCESS; implement once Glassnode key in SM.
- [ ] `umi-arkham-impl` — `[BLOCKED: api_keys_and_auth phase-3-keys]` VERIFIED 2026-03-09: correctly marked
      BLACKLISTED_NO_ACCESS; implement once Arkham key in SM.

---

## Track I — UCI Cloud Infrastructure Stubs

**Repo:** `unified-cloud-interface`

`uci_cloud_abstraction_complete.md` is archived as "all code complete" for GCP providers. These two remaining items were
not resolved:

### Todos

- [x] `uci-cloud-logging` — DONE 2026-03-09 commit `fb7c63b`: `AWSLoggingProvider` wired in `get_logging_client()`;
      `ValueError` for unknown provider (consistent with factory pattern).
- [x] `uci-aws-provider` — DONE 2026-03-09 commit `fb7c63b`: `S3StorageClient.bucket()` implemented via
      `S3BucketHandle` + `S3BlobHandle` wrapping boto3; matches GCP `GCSBucketHandle` pattern exactly.

---

## Track J — Deployment-API Stubs

**Repo:** `deployment-api` **Note:** `deployment-api` is NOT in phase3's T5 scope (T5 = execution-results-api,
market-data-api, client-reporting-api). These stubs are untracked.

### Todos

- [x] `deployment-api-cache` — DONE 2026-03-09 commit `07939d3`: 4 abstract stubs given descriptive
      `f"{self.__class__.__name__} does not implement <method>()"` messages; concrete subclasses (`InMemoryCache`,
      `RedisCache`, `GCSCache`) already fully implemented.
- [x] `deployment-api-prometheus` — DONE 2026-03-09 commit `07939d3`: `PrometheusMiddleware(BaseHTTPMiddleware)`
      implemented in `middleware.py` using existing `RECORDS_PROCESSED` + `PROCESSING_LATENCY` metrics; wired in
      `main.py`; TODO comment removed.

---

## Track K — Untracked TODO/FIXME Items (2026-03-09 Audit)

These items were found during the Section 13 audit scan and are not covered by any other active plan.

### Todos

- [x] `todo-client-reporting-prometheus` — DONE 2026-03-09 commit `5976dbc`: implemented local `PrometheusMiddleware` in
      `main.py` using `RECORDS_PROCESSED` + `PROCESSING_LATENCY` from `client_reporting_api.metrics`; wired via
      `app.add_middleware(PrometheusMiddleware, service_name="client-reporting-api")`; `/metrics` endpoint already
      exposed via `generate_latest()`; `prometheus-client>=0.20.0` confirmed in `pyproject.toml`; TODO comments removed.

- [x] `todo-deployment-api-uci-cloud-build` — DONE 2026-03-09: Added `CloudBuildClient` ABC to UCI abstractions,
      `GCPCloudBuildClient` implementation in `gcp_compute.py`, and `get_cloud_build_client()` factory with caching in
      `factory.py`. Exported from UCI `__init__`. In deployment-api: 5 `_cb.CloudBuildClient()` call-sites in
      `cloud_builds.py` replaced with `_get_gcp_build_client()` (which uses UCI factory); 1 call-site in
      `service_status_checkers.py` replaced with UCI-routed client. TODO comments removed. 17 new tests added (8
      factory, 9 GCPCloudBuildClient). UCI coverage: 80.79% → 84.34%. Commits: `2306747` (unified-cloud-interface),
      `6b940c9` (deployment-api).

- [x] `todo-deployment-service-league-config-import` — `deployment-service/scripts/sports/verify_league_config.py:348` —
      replace the inline workaround with an actual import from the league config module when that module is available. —
      DONE 2026-03-09 (commit `3ad6a92`): created `scripts/sports/league_config.py` shim that re-exports
      `LEAGUE_CLASSIFICATION_DATA` from `instruments_service.sports.league_data_classification`; updated `main()` in
      `verify_league_config.py` to import and use it instead of the empty-dict placeholder.

- [x] `todo-features-commodity-signal-composer` — `features-commodity-service/features_commodity_service/cli/main.py:93`
      — wire `engine.signal_composer.SignalComposer` per commodity asset class; currently the CLI exits without running
      signal composition. — DONE 2026-03-09: Added `_collect_factor_values()` helper and
      `_compute_signals_for_commodity()` function that iterates `enabled_factor_groups`, resolves each factor via
      `FACTOR_REGISTRY`/`get_factor()`, fetches data via `DATA_SOURCE_REGISTRY`/`get_source()`, computes `FactorValue`
      via `BaseCommodityFactor.compute()`, composes into a `CommoditySignal` via `SignalComposer` (defaulting regime to
      UNKNOWN for CLI pass), and publishes via `SignalPublisher`. Dry-run path skips publish but runs full factor
      computation. Ruff C901 complexity resolved by extracting the per-factor fetch/compute loop into
      `_collect_factor_values`.

- [x] `todo-features-delta-one-subscriber-orchestration` —
      `features-delta-one-service/features_delta_one_service/app/pubsub/subscriber.py:115` — parse incoming candle data,
      invoke the feature orchestration pipeline, and publish computed features to EventBus (referenced as Task 6.1.4). —
      DONE 2026-03-09: Implemented `_parse_candle_row()` to extract OHLCV fields from the message `data` dict into a
      Polars DataFrame; added `_run_pipeline()` that applies `NaNHandler.handle_nans()`/`replace_infinities()`, builds a
      feature record with per-column `to_list()` extraction (typed `list[object]` to satisfy basedpyright reportAny),
      and publishes to `{category_lower}-features-ready` via `get_event_bus()` from UCI. Messages with missing/empty
      candle data are acknowledged with status `skipped` (not hard-failed) for resilience. All 6 existing unit tests
      pass.

- [x] `todo-instruments-config-reloader-hook` — DONE 2026-03-09 commit `54c4268`: `_on_instruments_reload` now writes
      `_active_subscription_list` / `_active_enabled_venues` module-level snapshots and exposes
      `get_active_subscription_list()` / `get_active_enabled_venues()` for consumers; emits `CONFIG_RELOADED` event via
      `log_event` when events are set up.

- [x] `todo-instruments-gcs-upload-handlers` — DONE 2026-03-09 commit `54c4268`:
      `CorporateActionsBackfillHandler._upload_to_gcs()` walks `by_ticker_dir`, reads each CSV and writes via
      `get_data_sink(routing_key="tradfi")` partitioned by `{ticker}/{action_type}`;
      `GenerateDateViewsHandler._upload_to_gcs(by_date_dir)` walks date-partition dirs and writes Parquet via DataSink
      partitioned by `{day}/{action_type}`.

- [x] `todo-instruments-defi-adapter-explicit-imports` — DONE 2026-03-09 commit `4a42cf3`: all 15 inline
      `from unified_market_interface import ...` calls in `adapter_loader.py` replaced with a single consolidated
      top-level import block covering `TardisAdapter`, `DatabentoAdapter`, `HyperliquidAdapter`,
      `HyperliquidBaseClient`, `UniswapV2/V3/V4Adapter`, `AaveV3Adapter`, `CurveAdapter`, `BalancerAdapter`,
      `MorphoAdapter`, `EulerAdapter`, `FluidAdapter`, `LidoAdapter`, `EtherFiAdapter`, `EthenaAdapter`; all TODO
      comments removed; ruff clean.

- [x] `todo-ml-training-model-registry-explicit-imports` —
      `ml-training-service/ml_training_service/ml/model_registry.py:33,34` — replace inline import markers for
      `ModelMetadata` and `ModelVariantConfig` with explicit module paths once those symbols are exported from a stable
      UTL or UMI sub-module. — DONE 2026-03-09 commit `f3c4019`: reverted deep sub-module import
      (`from unified_ml_interface.models import`) to quality-gate-compliant top-level import
      (`from unified_ml_interface import ModelMetadata, ModelVariantConfig`); TODO comments removed.

- [x] `todo-execution-loader-explicit-import` — `execution-service/execution_service/utils/io/loader.py:10` — replace
      `from unified_trading_library import BaseGCSLoader` wildcard with an explicit sub-module import path once
      `BaseGCSLoader` is exported from a stable public UTL API. — DONE 2026-03-09 commit `0ffede59`: reverted deep
      sub-module import (`from unified_trading_library.io.base_loader import BaseGCSLoader`) to the
      quality-gate-compliant top-level import (`from unified_trading_library import BaseGCSLoader`); the
      check-import-patterns.py gate requires top-level imports for all unified external libraries.

- [x] `todo-risk-cli-client-list` — DONE 2026-03-09: VERIFIED already fully implemented; `run_batch_mode()` builds the
      client list as the union of `get_monitored_client_ids()` (reads `MONITORED_CLIENT_IDS` from
      `RiskAndExposureServiceConfig`) and `limits_client.list_client_ids()` (from `RiskLimitsClient`); de-duplicated,
      sorted, and iterated; empty-list path logs a warning and exits cleanly. No stub remaining.

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

api_keys_and_auth.md phases 2–4 ─UNBLOCKS──> Track G (UPI impls) + Track H (UMI onchain)
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
| IBKR adapters (UMI/UTEI/UPI/URDI)                     | `adapters/ibkr.py` × 4 repos                             | `ibkr_gateway_rollout.md`                                             |
| Betfair/Kalshi/Coinbase/Smarkets/Betdaq WS            | UTEI ws_feeds.py                                         | `api_keys_and_auth.md § phase-4`                                      |
| execution-service PostgreSQL persistence              | `engine/live/persistence/postgresql.py`                  | `phase3_service_hardening_integration.md`                             |
| execution-service config_reloaders TODOs              | `config_reloaders.py:54,72`                              | `phase3_service_hardening_integration.md`                             |
| features-delta-one futures_roll_adjuster              | `app/core/futures_roll_adjuster.py:341-346`              | `phase3_service_hardening_integration.md`                             |
| features-cross-instrument cli TODO                    | `cli/main.py:84-101`                                     | `phase3_service_hardening_integration.md`                             |
| features-multi-timeframe EventBus TODO                | `app/engine/orchestrator.py:210`                         | `phase3_service_hardening_integration.md`                             |
| risk-and-exposure compute_handler + cash reserve      | `compute_handler.py:30`, `pre_trade_check_engine.py:332` | `safety_and_risk_controls.md`                                         |
| strategy-validation-service validation logic          | `cli/main.py:107`                                        | `phase3_service_hardening_integration.md`                             |
| execution-results-api abstract services (24 stubs)    | `services/data_service_*.py` × 6 files                   | `phase3_service_hardening_integration.md`                             |
| ml-training cascade_meta_model_trainer                | `app/training/cascade_meta_model_trainer.py:44`          | `phase3_service_hardening_integration.md`                             |
| instruments-service barchart + defi_processor         | `adapter_loader.py:75,100`, `defi_processor.py:175`      | `phase3_service_hardening_integration.md`                             |
| trading-agent-service estimated_price placeholder     | `app/loops/l3_trade_decision.py`                         | `tradfi_expansion.md`                                                 |
| execution-service manual_instruction_api account_id   | `api/manual_instruction_api.py`                          | `phase3_service_hardening_integration.md`                             |
| UCI abstractions.py base class stubs                  | `abstractions.py:91-566`                                 | Abstract base pattern — concrete GCP impls complete per archived plan |
| UDC athena + bq_external readers                      | `readers/athena.py`, `readers/bq_external.py`            | `phase2_library_tier_hardening.md § t3-udc-code-rewrite`              |
| UMI footystats + soccer_football adapters             | `adapters/alt_data/footystats_adapter.py`                | `api_keys_and_auth.md § phase-3-keys`                                 |
| execution-service ADAPTIVE_TWAP / ALMGREN_CHRISS port | `scripts/migrate_to_library_algorithms.py:31-32`         | `phase2_library_tier_hardening.md § t0-code-rewrite` (EAL)            |

---

## Track G — UAC Orphaned Symbol Remediation (Section 14 audit fix)

**Repo:** `unified-api-contracts` **Added:** 2026-03-09

### Background

Audit Section 14 found 12 confirmed orphan symbols in `unified-api-contracts` — symbols defined but never imported by
any downstream repo. Remediation completed 2026-03-09:

- `domain_config.py` — 4 Protocol classes deleted (no import anywhere, only docstring mentions)
- `canonical_mappings.py` — 3 orphan functions deleted (`get_venues_for_data_source`, `get_canonical_venue_for_dataset`,
  `get_defi_venue`; superseded by UTL equivalents)
- `endpoint_registry.py` — 4 classes (`AccessMode`, `DataAvailability`, `ResponseFormat`, `EndpointSpec`) marked with
  `# orphan: kept because` comments; `ENDPOINT_REGISTRY` holds substantive per-venue documentation (auth details,
  deprecation dates) not yet wired to a consumer
- `vcr_endpoints.py` — `VCREndpoint` TypedDict marked with `# orphan: kept because` comment; it is used internally to
  type `VCR_ENDPOINTS` and the `_get`/`_post` helpers

### Todos

- [x] `uac-endpoint-registry-consumer` — DONE 2026-03-09 commit `2aa25d0`: `ENDPOINT_REGISTRY`, `AccessMode`,
      `DataAvailability`, `EndpointSpec`, `ResponseFormat` imported and added to `__all__` in
      `unified_api_contracts/__init__.py`; all `# orphan:` comments removed from `endpoint_registry.py`; basedpyright
      clean (0 errors).

---

## Track L — §13.2 Trading-Critical TODO Tracking (2026-03-11 Audit)

These items were found during the §13.2 audit scan (2026-03-11). All are GH-BACKLOG items formally tracked here.

### Todos

- [ ] `risk-batch-compute-unimplemented` — `risk-and-exposure-service/cli/handlers/compute_handler.py:30` — batch risk
      computation is unimplemented (GH-BACKLOG). Implement `_compute_batch_risk()` to calculate portfolio risk metrics
      for historical windows.

- [x] `pre-trade-cash-reserve-check` — DONE 2026-03-11 commit `6ce535d`: `_check_cash_reserves()` implemented with
      fail-safe proxy using remaining capacity (max_capital_deployed − new_capital). 5 new unit tests added.

- [ ] `balancer-eth-venue-implementation` — `unified-market-interface/models/venue_config.py:164,206` — BALANCER-ETH
      venue config stubs (2 commented-out blocks). Implement when Balancer v3 adapter is available (stream-d).

- [ ] `gas-estimator-live-umi-feed` — `strategy-service/engine/rebalancing/gas_estimator.py:175` — live UMI price feed
      not wired (stream-d phase). Replace static gas price lookup with `get_price()` from UMI.

- [ ] `futures-roll-adjuster-calendar` — `features-delta-one-service/app/core/futures_roll_adjuster.py:345` — roll
      calendar prices unimplemented (GH-BACKLOG). Fetch roll prices from reference data service.

- [ ] `futures-basis-mark-price-features` —
      `features-delta-one-service/features_service/app/calculators/futures_basis.py:70` — mark price features commented
      out (GH-BACKLOG). Implement mark_price-based basis calculations when live mark price feed available.

- [x] `mft-audit-remediation-plan-registered` — `mft_audit_full_remediation_2026_03_11.md` created and registered. All
      20 tasks tracked. Wave 1 complete. Wave 2 in progress.
