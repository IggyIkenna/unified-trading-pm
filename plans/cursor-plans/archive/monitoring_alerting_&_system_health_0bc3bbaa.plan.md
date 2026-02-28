---
name: Monitoring Alerting & System Health
overview: "Build institutional-grade (Citadel-level+) monitoring and alerting: Prometheus metrics across all services via unified-trading-services shared lib, standalone alerting-service fully built out (AlertRule engine, Slack blocks with Claude Code Slack integration that reads alerts and dispatches follow-up actions, PagerDuty), new market-data-api repo for order book SSE, latency/CPU/memory dashboards in trading-analytics-ui and live-health-monitor-ui, Grafana-export-compatible dashboard JSONs, deployment system refactor (split unified-trading-deployment-v3 backend from UI), ML deployment UI correctly scoped as ML analytics UI, prometheus-metrics codex doc. reportAny=error everywhere."
todos:
  - id: prometheus-client-add-to-uts
    content: "Add prometheus-client>=0.21.0 to unified-trading-services/pyproject.toml as a core dependency (not optional). Create unified_trading_services/observability/__init__.py and unified_trading_services/observability/metrics.py with ALL canonical Prometheus metrics defined as module-level globals (see Part 1). Create unified_trading_services/observability/metrics_handler.py with get_metrics_response() → fastapi.Response function. Create unified_trading_services/observability/middleware.py with PrometheusMiddleware (starlette BaseHTTPMiddleware) that auto-records API_REQUEST_LATENCY for every request. Export all from unified_trading_services/__init__.py. Run timeout 120 basedpyright unified_trading_services/ fix all errors. bash scripts/quickmerge.sh 'feat: add prometheus observability module'."
    status: done
    completed_at: "2026-02-27"
  - id: alert-rule-schemas-uic
    content: "Create unified_internal_contracts/alerting/__init__.py and unified_internal_contracts/alerting/rules.py. Schemas: AlertSeverity(StrEnum: DEBUG/INFO/WARNING/CRITICAL/FATAL), AlertChannel(StrEnum: SLACK/EMAIL/PAGERDUTY/UI), AlertRule(BaseContractModel: rule_id, name, metric_name, condition gt|lt|eq|ne, threshold float, severity AlertSeverity, channels list[AlertChannel], cooldown_seconds=300, strategy_id str|None, venue str|None), AlertEvent(BaseContractModel: alert_id, rule_id, severity, channels_notified, metric_value float, threshold float, strategy_id str|None, venue str|None, message str, triggered_at datetime, resolved_at datetime|None). Export all from top-level unified_internal_contracts/__init__.py. reportAny=error, no Any types. quickmerge unified-internal-contracts."
    status: done
    completed_at: "2026-02-27"
  - id: metrics-endpoint-fastapi-services
    content: "Add GET /metrics Prometheus endpoint to ALL FastAPI services that are user-facing or externally consumed. Services: execution-results-api, position-balance-monitor-service, execution-service (manual instruction API), alerting-service (when built out), client-reporting-api (new repo), market-data-api (new repo), unified-trading-deployment-v3. Pattern for each: (1) add sse-starlette and prometheus-client to pyproject.toml via uv add (already in unified-trading-services transitively, but explicit is better). (2) In api/main.py: app.add_middleware(PrometheusMiddleware) from unified_trading_services.observability.middleware. (3) Add @app.get('/metrics') route that returns get_metrics_response(). (4) Instrument service-specific metrics: execution-results-api instruments TRADE_EXECUTION_LATENCY on backtest completion, position-balance-monitor instruments POSITION_NOTIONAL and RECONCILIATION_DRIFT on each reconciliation. (5) quickmerge each repo. NOTE: risk-and-exposure-service FastAPI is being REMOVED (per service/UI separation rule) — do NOT add /metrics there; risk metrics published via unified-events-interface instead."
    status: done
    completed_at: "2026-02-27"
  - id: alerting-service-build-out
    content: "Build out alerting-service from near-empty skeleton (currently only config.py + main.py stubs). This is the central alerting hub — external-facing, runs as always-on FastAPI service. (1) Add to pyproject.toml: fastapi>=0.109, uvicorn[standard], sse-starlette>=1.6.1, aiohttp>=3.13, httpx>=0.28, pyyaml>=6.0, unified-internal-contracts, unified-trading-services, unified-events-interface, unified-config-interface, unified-cloud-interface, anthropic>=0.40 (for Claude Code Slack integration). (2) Build alerting_service/config.py: extend UnifiedCloudConfig, add slack_webhook_url, pagerduty_api_key, email_smtp_host, google_oauth_domain, alert_rules_gcs_path. (3) Build alerting_service/core/rule_engine.py: RuleEngine class — loads AlertRule list from alerting-service/config/default_rules.yaml, polls Prometheus /metrics endpoints from all services every 10s, evaluates each AlertRule condition, fires AlertEvent if threshold breached and cooldown not active, stores last_fired timestamps in memory. (4) Build alerting_service/core/slack_dispatcher.py: sends branded Odum Slack blocks (see Part 2 format), includes 'View in Dashboard' button, color-coded by severity. (5) Build alerting_service/core/claude_slack_agent.py: after sending alert to Slack, also triggers a Claude Code API call (using anthropic SDK) that reads the alert context and posts a follow-up Slack message with: analysis of what caused it, recommended action steps, link to relevant service logs. This gives AI-driven alert triage in Slack. (6) Build alerting_service/api/main.py: FastAPI app with Google OAuth middleware. GET /stream/alerts SSE endpoint (streams AlertEvent to live-health-monitor-ui). POST /alerts/test (ADMIN role, trigger test alert). GET /rules (list AlertRule). POST /rules (create/update AlertRule, ADMIN). GET /health. GET /metrics. (7) Build alerting_service/config/default_rules.yaml (see Part 2 table). (8) quickmerge alerting-service."
    status: done
    completed_at: "2026-02-27"
  - id: standard-alert-rules-config
    content: "Create alerting-service/config/default_rules.yaml with all 10 standard alert rules. Each rule: rule_id, name, metric_name (exact Prometheus metric name from metrics.py), condition, threshold, severity, channels list, cooldown_seconds. Rules: (1) recon-drift: reconciliation_drift_usd > 500 → CRITICAL → [SLACK, PAGERDUTY]. (2) circuit-breaker-open: circuit_breaker_state == 2 → FATAL → [SLACK, PAGERDUTY, EMAIL]. (3) position-limit-breach: position_notional_usd > (configured per strategy, use 1000000 default) → CRITICAL → [SLACK, UI]. (4) feature-staleness: feature_staleness_seconds > 300 → WARNING → [SLACK, UI]. (5) dlq-depth: dead_letter_queue_depth > 10 → WARNING → [SLACK]. (6) gcs-latency: gcs_write_latency_seconds > 30 → WARNING → [SLACK]. (7) fill-rate-low: order_fill_rate_pct < 0.80 → CRITICAL → [SLACK, PAGERDUTY]. (8) exec-latency: trade_execution_latency_seconds > 0.5 → WARNING → [SLACK, UI]. (9) pnl-drawdown: pnl_drawdown_pct < -0.05 → CRITICAL → [SLACK, PAGERDUTY, EMAIL]. (10) ibgw-disconnect: ibkr_gateway_connected == 0 → FATAL → [SLACK, PAGERDUTY, EMAIL, UI]. quickmerge alerting-service."
    status: done
    completed_at: "2026-02-27"
  - id: market-data-api-new-repo
    content: "Create NEW standalone repo market-data-api following new-repo-setup.mdc. Purpose: order book SSE delivery service. market-tick-data-handler publishes normalized L2 order book updates to Pub/Sub topic ORDERBOOK_UPDATES. market-data-api subscribes and exposes SSE endpoints. (1) gh repo create IggyIkenna/market-data-api --private --clone. Grant CosmicTrader + datado access. (2) Dependencies: fastapi>=0.109, uvicorn[standard], sse-starlette>=1.6.1, google-cloud-pubsub (via unified-cloud-interface), unified-internal-contracts, unified-trading-services, unified-config-interface, unified-events-interface, unified-cloud-interface, google-auth>=2.40. (3) Structure: market_data_api/api/main.py (FastAPI + Google OAuth), market_data_api/core/orderbook_subscriber.py (Pub/Sub subscriber, maintains per-symbol L2 book in memory as dict[str, OrderBookSnapshot]), market_data_api/api/routes/orderbook.py (GET /stream/orderbook?symbol=BTCUSDT&depth=20 SSE endpoint, GET /orderbook/{symbol}/snapshot REST), market_data_api/api/routes/health.py, market_data_api/config.py. (4) OrderBookSnapshot dataclass: symbol, bids list[tuple[float,float]], asks list[tuple[float,float]], timestamp, venue. (5) SSE format: {bids: [[price,qty],...], asks: [[price,qty],...], own_orders: {bid_orders: [{price,qty,order_id}], ask_orders: [...]}, timestamp, venue, spread_bps}. own_orders fetched from execution-service API. (6) Rate limiting: max 10 concurrent SSE subscribers per symbol. (7) GET /metrics Prometheus endpoint. (8) quickmerge market-data-api."
    status: done
    completed_at: "2026-02-27"
  - id: orderbook-viz-ui
    content: "Build /orderbook page in trading-analytics-ui. (1) OrderBookDepthChart component: recharts AreaChart (cumulative depth on Y, price on X). bids side: blue fill (#2563EB). asks side: red fill (#DC2626). Midpoint line: dashed gray with spread label in bps. own bid orders: green dots overlaid. own ask orders: orange dots overlaid. Update in real-time from SSE (EventSource to market-data-api GET /stream/orderbook?symbol={selectedSymbol}). (2) OrderBookTable component: top 10 bid/ask levels each side. Qty column shows our own order qty highlighted [MY ORDER] if order_id matches. Flash animation on price/qty change. (3) TradeTimeline component: scrolling tape of recent fills from execution-results-api GET /stream/fills SSE. Buy=green row, Sell=red row, own fill=bold + ★. Auto-scroll to newest. (4) Symbol selector dropdown: list of active instruments from instruments-service. (5) SpreadIndicator: live spread in bps, target <5bps warning >20bps. (6) npm run typecheck passes. quickmerge trading-analytics-ui."
    status: pending
  - id: latency-plots-ui
    content: "Build /latency page in trading-analytics-ui. All data from alerting-service GET /metrics?service=execution-service or Prometheus scrape. (1) ExecutionLatencyHistogram: recharts BarChart — buckets [<10ms, 10-50ms, 50-100ms, 100-500ms, >500ms], bars grouped by venue (OKX=blue, Binance=green, Bybit=orange). Threshold line at 500ms (WARNING level). (2) SlippageScatter: recharts ScatterChart — X=order_size_usd, Y=slippage_bps. Color by venue. Tooltip shows instrument, timestamp. Data: GET /api/v1/analysis/slippage from execution-results-api. (3) GatewayRoundtrip: recharts LineChart — IBKR TWS roundtrip latency over last 24h (1-min buckets). Red threshold at 100ms. Data: ibkr_roundtrip_latency_seconds Prometheus gauge. (4) P50/P95/P99 latency summary table above charts. (5) Time range selector: 1h, 6h, 24h, 7d. (6) npm run typecheck passes. quickmerge trading-analytics-ui."
    status: pending
  - id: system-health-page
    content: "Build /system-health page in live-health-monitor-ui. Pulls from metrics-aggregator-api (GET /api/system/metrics). (1) ServiceStatusGrid: grid of service cards (all 14+ services). Each card: service name, green/yellow/red status dot (green=heartbeat<30s, yellow=latency_high or warning alerts, red=down or CIRCUIT_BREAKER_OPEN), last heartbeat timestamp. Click → navigate to service detail. Data: alerting-service GET /health, supplemented by Prometheus up{job=service_name} scrape. (2) CPUMemoryTimeSeries: recharts LineChart — multi-line (one per service), selector for which services to show. Y-axis: % usage. Time window: 1h. Threshold lines: 85% RAM=warning, 90%=danger. (3) PubSubLagBars: recharts BarChart — one bar per Pub/Sub topic. Color: green<1s, yellow 1-5s, red>5s. Data: pubsub_message_lag_seconds Prometheus gauge. (4) DLQDepthBadges: grid of topic badges with count. Zero=green badge, any>0=red badge with integer count. Clicking badge shows DLQ messages. (5) GCSWriteThroughput: recharts LineChart — records/min per service. Helps detect stalled writes. (6) Active Alerts panel: SSE from alerting-service GET /stream/alerts — live scrolling AlertEvent list with severity color-coding. (7) npm run typecheck passes. quickmerge live-health-monitor-ui."
    status: pending
  - id: metrics-aggregator-api
    content: "Build metrics aggregator into live-health-monitor-ui's backend (or add to alerting-service — prefer alerting-service to keep UI backends thin). Add to alerting_service/api/routes/system_metrics.py: GET /api/system/metrics?service={service}&window={1h|6h|24h} endpoint. Implementation: use httpx.AsyncClient to fan-out GET /metrics to all service Prometheus endpoints (URLs from config: METRICS_ENDPOINTS dict in UnifiedCloudConfig). Parse Prometheus text format (use prometheus-client parse_known_metrics or simple regex). Aggregate into {service, cpu_pct, memory_mb, worker_count} time-series. Cache results in memory for 15s to avoid hammering services. Return JSON array of {timestamp, service, metric, value}. Add get_metrics_response() pattern consistent with other services. quickmerge alerting-service."
    status: pending
  - id: deployment-service-split
    content: "Refactor unified-trading-deployment-v3 to cleanly separate: backend API (already exists in api/), UI (already exists in ui/), and config service (extract from api/routes/config.py). (1) The existing unified-trading-deployment-v3/api/ + unified-trading-deployment-v3/ui/ structure is CORRECT — keep co-located (it is the deployment control plane, FastAPI serves the React UI). No repo split needed. (2) Extract config-related routes (StrategyConfig/ExecutionConfig CRUD) from api/routes/config.py into a dedicated api/routes/config_service.py and expose as /api/v1/configs/* routes. These routes are shared with execution-analytics-ui and onboarding-ui. (3) The existing ui/ (React 19, Radix UI, Tailwind, 7 tabs: Deploy, Data Status, Builds, Readiness, Status, Config, History) is the system deployment UI — keep as-is. This is NOT ml-training-ui. (4) ml-training-ui is ML Analytics & Deployment (separate — see ml-training-ui-scope-correct in config plan). (5) Add Google OAuth to unified-trading-deployment-v3 api/auth_middleware.py (already has auth_middleware.py — wire Google OAuth using shared middleware from unified-trading-services). (6) quickmerge unified-trading-deployment-v3."
    status: pending
  - id: grafana-export
    content: "Export Grafana-compatible dashboard JSONs (export-only, no live Grafana instance required yet). (1) Create unified-trading-deployment-v3/grafana/ directory. (2) Create grafana/dashboards/trading-overview.json: Grafana dashboard JSON with panels for: trade_execution_latency_seconds heatmap, position_notional_usd gauge per strategy, reconciliation_drift_usd time-series, circuit_breaker_state state timeline, pubsub_message_lag_seconds bar gauge. Use Prometheus data source (variable: ${prometheus_url}). (3) Create grafana/dashboards/system-health.json: CPU/memory time-series per service, GCS write latency, DLQ depth. (4) Create grafana/provisioning/datasources/prometheus.yaml: Grafana provisioning config pointing to ${PROMETHEUS_URL}. (5) Add GET /api/grafana/datasource to alerting-service: implements Grafana SimpleJSON protocol (GET / → capabilities, POST /query → metric values, POST /search → metric names). This allows adding alerting-service as a Grafana data source. (6) Document in unified-trading-codex/03-observability/prometheus-metrics.md. quickmerge unified-trading-deployment-v3 and alerting-service."
    status: pending
  - id: prometheus-codex
    content: "Create unified-trading-codex/03-observability/prometheus-metrics.md. Contents: (1) Canonical metric catalog: every metric name, type (Counter/Gauge/Histogram), labels, description, which service records it. (2) Alert rule catalog: all 10 standard rules from default_rules.yaml with threshold rationale. (3) Service → metrics endpoint mapping table: service_name → http://service:port/metrics. (4) Grafana dashboard JSON location: unified-trading-deployment-v3/grafana/dashboards/. (5) How to add a new metric: step-by-step (add to metrics.py, instrument in service, update this doc, add alert rule if needed). (6) Alert triage guide: for each CRITICAL/FATAL alert, what to check and what action to take. (7) Claude Code Slack integration description: how AI triage messages are generated and what they contain. quickmerge unified-trading-codex."
    status: pending
  - id: quality-gates-venv-fix
    content: "Fix quality-gates.sh venv logic across all repos"
    status: done
    completed_at: "2026-02-27"
  - id: e722-ruff-fix
    content: "Remove E722 from global ruff ignore in execution-service"
    status: done
    completed_at: "2026-02-27"
  - id: uv-lock-gitignore
    content: "Remove uv.lock from .gitignore in pnl-attribution-service and alerting-service"
    status: done
    completed_at: "2026-02-27"
  - id: thread-pool-bounded
    content: "Bound ThreadPoolExecutor in uniswap adapters"
    status: done
    completed_at: "2026-02-27"
  - id: lifecycle-events-canonical
    content: "Fix non-canonical lifecycle events UPLOAD_STARTED -> PERSISTENCE_STARTED"
    status: done
    completed_at: "2026-02-27"
isProject: false
---

# Monitoring, Alerting & System Health Plan

Cross-references:

- `end-to-end_completion_master_plan_(v2)_2ce484e2.plan.md` — P0-6 SSE endpoints, P1-19 circuit breaker schema
- `config,_reporting_&_ui_completion_2c43029e.plan.md` — trading-analytics-ui SSE, live-health-monitor-ui, Google OAuth, service/UI separation

**Updated:** 2026-02-27 — Incorporates: Google OAuth on alerting-service, Claude Code Slack AI triage integration, risk-and-exposure-service FastAPI removal (internal service), new market-data-api repo for order book SSE, deployment-service kept co-located (correct), ml-training-ui correctly scoped as ML analytics UI, reportAny=error mandate.

---

## Workspace Rules (Every Agent Must Follow)

```
- uv not pip
- bash scripts/quickmerge.sh "message" not git push
- timeout 120 basedpyright <source_dir>/ not basedpyright .
- from unified_events_interface import setup_events, log_event — no fallbacks
- No os.getenv() — use UnifiedCloudConfig
- No Any types — reportAny = "error" everywhere
- No try/except ImportError — fail loud
- Delete deprecated code — no parallel code paths
- Search unified libraries before implementing anything new
- typeCheckingMode = "strict" in pyrightconfig.json
```

---

## Actual Current State (Confirmed by Codebase Audit)


| Component                    | Status                              | Notes                                                                                                                |
| ---------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `alerting-service` repo       | EXISTS but SKELETON                 | Only config.py + main.py stubs. No actual alerting logic.                                                            |
| Slack integration            | EXISTS in risk-and-exposure-service | `alert_manager.py` + `alert_adapter.py` — sends to Slack + PagerDuty. Has rate limiting. Uses `aiohttp`.             |
| Alert schemas                | PARTIAL in UIC                      | `AlertMessage`, `AlertType` in `risk.py` — NOT `AlertRule`/`AlertEvent` (missing).                                   |
| Prometheus                   | **MISSING**                         | Zero `prometheus_client` usage anywhere in production code. `market-tick-data-handler` has it in optional deps only. |
| Order book visualization     | **MISSING**                         | No order book SSE endpoint. `market-tick-data-handler` is CLI-only.                                                  |
| Latency / CPU / memory plots | **MISSING**                         | No instrumentation.                                                                                                  |
| Grafana                      | **MISSING**                         | No dashboards, no datasource endpoint.                                                                               |
| FastAPI in risk service      | EXISTS but should be removed        | `risk_and_exposure_service/api/main.py` — pre-trade checks should be library import in execution-service, not HTTP. |


---

## Part 1 — Prometheus Metrics Library (unified-trading-services)

**Add to `unified-trading-services`** as core dependency — all services get metrics transitively.

```python
# unified_trading_services/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge, REGISTRY

TRADE_EXECUTION_LATENCY = Histogram(
    "trade_execution_latency_seconds",
    "Time from signal to order submission",
    labelnames=["venue", "strategy_id", "instrument_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
ORDER_SUBMISSION_COUNTER = Counter(
    "orders_submitted_total",
    "Total orders submitted",
    labelnames=["venue", "order_type", "side"],
)
ORDER_FILL_RATE = Gauge(
    "order_fill_rate_pct",
    "Ratio of filled to submitted orders (rolling 1h)",
    labelnames=["venue", "strategy_id"],
)
POSITION_NOTIONAL = Gauge(
    "position_notional_usd",
    "Current position notional in USD",
    labelnames=["strategy_id", "instrument_key"],
)
RECONCILIATION_DRIFT = Gauge(
    "reconciliation_drift_usd",
    "Difference between internal and exchange position (USD)",
    labelnames=["venue", "account_id"],
)
FEATURE_STALENESS_SECONDS = Gauge(
    "feature_staleness_seconds",
    "Age of most recent feature computation in seconds",
    labelnames=["feature_name", "service"],
)
GCS_WRITE_LATENCY = Histogram(
    "gcs_write_latency_seconds",
    "GCS write operation latency",
    labelnames=["bucket", "service"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
)
PUBSUB_LAG = Gauge(
    "pubsub_message_lag_seconds",
    "Lag from publish to consume",
    labelnames=["topic", "service"],
)
DEAD_LETTER_QUEUE_DEPTH = Gauge(
    "dead_letter_queue_depth",
    "Number of messages in DLQ",
    labelnames=["topic"],
)
API_REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "HTTP API endpoint latency",
    labelnames=["service", "endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=half-open, 2=open)",
    labelnames=["strategy_id", "trigger_type"],
)
PNL_DRAWDOWN_PCT = Gauge(
    "pnl_drawdown_pct",
    "Current drawdown from peak PnL (negative means drawdown)",
    labelnames=["strategy_id", "client_id"],
)
IBKR_GATEWAY_CONNECTED = Gauge(
    "ibkr_gateway_connected",
    "IB Gateway connection state (1=connected, 0=disconnected)",
    labelnames=["account_id"],
)
IBKR_ROUNDTRIP_LATENCY = Histogram(
    "ibkr_roundtrip_latency_seconds",
    "IB TWS roundtrip latency",
    labelnames=["account_id"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)
```

```python
# unified_trading_services/observability/metrics_handler.py
from fastapi import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def get_metrics_response() -> Response:
    """Standard /metrics endpoint handler for all FastAPI services."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

```python
# unified_trading_services/observability/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
from unified_trading_services.observability.metrics import API_REQUEST_LATENCY

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Auto-instrument all FastAPI endpoints with API_REQUEST_LATENCY."""

    def __init__(self, app, service_name: str) -> None:
        super().__init__(app)
        self._service = service_name

    async def dispatch(self, request: Request, call_next):  # type: ignore[override] — starlette typing
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        API_REQUEST_LATENCY.labels(
            service=self._service,
            endpoint=request.url.path,
            method=request.method,
        ).observe(duration)
        return response
```

Services that get `/metrics` endpoint added:


| Service                          | `/metrics`              | Specific metrics to instrument                                                            |
| -------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------- |
| execution-results-api            | ✅ Add                   | API_REQUEST_LATENCY (auto via middleware)                                                 |
| execution-service               | ✅ Add                   | TRADE_EXECUTION_LATENCY, ORDER_SUBMISSION_COUNTER, ORDER_FILL_RATE, CIRCUIT_BREAKER_STATE |
| position-balance-monitor-service | ✅ Add                   | POSITION_NOTIONAL, RECONCILIATION_DRIFT                                                   |
| alerting-service                  | ✅ Add                   | API_REQUEST_LATENCY                                                                       |
| client-reporting-api (new)   | ✅ Add                   | API_REQUEST_LATENCY                                                                       |
| market-data-api (new)            | ✅ Add                   | API_REQUEST_LATENCY                                                                       |
| unified-trading-deployment-v3    | ✅ Add                   | API_REQUEST_LATENCY                                                                       |
| pnl-attribution-service          | Add CLI metric emission | PNL_DRAWDOWN_PCT updated after each batch run                                             |
| features-* services              | Add CLI metric emission | FEATURE_STALENESS_SECONDS updated after each batch run                                    |
| market-tick-data-handler         | Add CLI metric emission | PUBSUB_LAG, DEAD_LETTER_QUEUE_DEPTH                                                       |
| risk-and-exposure-service        | ❌ FastAPI being removed | Emit metrics via unified-events-interface instead                                         |


---

## Part 2 — Alerting System: Full Build-Out

### Architecture

```
All services → Prometheus /metrics endpoints
    ↓ (polled every 10s)
alerting-service RuleEngine
    ↓ (evaluates AlertRule conditions)
    ├── Slack dispatcher (branded blocks + Claude AI triage message)
    ├── PagerDuty dispatcher (CRITICAL/FATAL only)
    ├── Email dispatcher (FATAL only)
    └── SSE /stream/alerts (live-health-monitor-ui)
```

### alerting-service structure (full)

```
alerting-service/
├── alerting_service/
│   ├── __init__.py
│   ├── config.py                        # UnifiedCloudConfig extension
│   ├── main.py                          # asyncio entrypoint
│   ├── api/
│   │   ├── main.py                      # FastAPI app + Google OAuth + /metrics
│   │   └── routes/
│   │       ├── alerts.py                # GET /stream/alerts SSE, POST /alerts/test
│   │       ├── rules.py                 # GET/POST /rules
│   │       ├── system_metrics.py        # GET /api/system/metrics aggregator
│   │       └── health.py
│   ├── core/
│   │   ├── rule_engine.py              # RuleEngine: polls /metrics, evaluates rules
│   │   ├── slack_dispatcher.py         # Branded Odum Slack blocks
│   │   ├── claude_slack_agent.py       # AI triage follow-up via anthropic SDK
│   │   ├── pagerduty_dispatcher.py     # PagerDuty Events API v2
│   │   ├── email_dispatcher.py         # SMTP email for FATAL alerts
│   │   └── alert_store.py             # In-memory cooldown tracking + recent events
│   └── config/
│       └── default_rules.yaml
├── tests/
├── pyproject.toml
└── scripts/quality-gates.sh
```

### alerting_service/config.py

```python
from unified_config_interface import UnifiedCloudConfig

class AlertingSystemConfig(UnifiedCloudConfig):
    service_name: str = "alerting-service"
    slack_webhook_url: str                          # required — fail if missing
    pagerduty_routing_key: str | None = None
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_to: list[str] = []
    google_oauth_domain: str = ""
    anthropic_api_key: str | None = None           # for Claude AI triage
    poll_interval_seconds: int = 10
    metrics_endpoints: dict[str, str] = {}         # service_name → http://host:port/metrics
    # Example:
    # execution-results-api: http://execution-results-api:8080/metrics
    # position-balance-monitor-service: http://position-balance-monitor:8080/metrics
```

### Slack message format (branded Odum blocks)

```python
# alerting_service/core/slack_dispatcher.py

SEVERITY_COLORS = {
    "DEBUG": "#808080",
    "INFO": "#0EA5E9",
    "WARNING": "#F59E0B",
    "CRITICAL": "#EF4444",
    "FATAL": "#7C3AED",
}

def build_slack_blocks(event: AlertEvent) -> dict:
    return {
        "attachments": [{
            "color": SEVERITY_COLORS[event.severity],
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"[{event.severity}] {event.message}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Rule:* {event.rule_id}"},
                        {"type": "mrkdwn", "text": f"*Value:* {event.metric_value:.4f}"},
                        {"type": "mrkdwn", "text": f"*Threshold:* {event.threshold}"},
                        {"type": "mrkdwn", "text": f"*Strategy:* {event.strategy_id or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Venue:* {event.venue or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Time:* {event.triggered_at.isoformat()}"},
                    ]
                },
                {
                    "type": "actions",
                    "elements": [{
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Dashboard"},
                        "url": f"{DASHBOARD_URL}/system-health",
                        "style": "primary",
                    }]
                }
            ]
        }]
    }
```

### Claude Code Slack AI Triage Integration

After each CRITICAL/FATAL alert is sent to Slack, `claude_slack_agent.py` makes an **anthropic API call** (claude-3-5-haiku-20241022 for speed) and posts a follow-up Slack thread message with AI-driven triage:

```python
# alerting_service/core/claude_slack_agent.py

TRIAGE_SYSTEM_PROMPT = """
You are an institutional trading system on-call engineer.
Analyze the alert and provide:
1. Root cause hypothesis (2-3 sentences)
2. Immediate action steps (numbered list, max 5)
3. Which service/log to check first
Be concise. This goes to Slack. Use bullet points.
"""

async def post_ai_triage(event: AlertEvent, slack_ts: str) -> None:
    """Post AI triage analysis as thread reply to the alert Slack message."""
    # Build context from event
    context = f"""
    Alert: {event.message}
    Severity: {event.severity}
    Metric: {event.rule_id} = {event.metric_value} (threshold: {event.threshold})
    Strategy: {event.strategy_id}
    Venue: {event.venue}
    Time: {event.triggered_at}
    """
    # Call Claude API
    response = anthropic_client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=400,
        system=TRIAGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    triage_text = response.content[0].text

    # Post as thread reply
    await post_slack_thread_reply(
        thread_ts=slack_ts,
        text=f"🤖 *AI Triage Analysis*\n{triage_text}",
    )
```

### Standard alert rules (default_rules.yaml)

```yaml
rules:
  - rule_id: recon-drift-critical
    name: "Reconciliation Drift > $500"
    metric_name: reconciliation_drift_usd
    condition: gt
    threshold: 500.0
    severity: CRITICAL
    channels: [SLACK, PAGERDUTY]
    cooldown_seconds: 300

  - rule_id: circuit-breaker-open
    name: "Circuit Breaker OPEN"
    metric_name: circuit_breaker_state
    condition: eq
    threshold: 2.0
    severity: FATAL
    channels: [SLACK, PAGERDUTY, EMAIL]
    cooldown_seconds: 60

  - rule_id: feature-staleness-warning
    name: "Feature Staleness > 5 min"
    metric_name: feature_staleness_seconds
    condition: gt
    threshold: 300.0
    severity: WARNING
    channels: [SLACK, UI]
    cooldown_seconds: 600

  - rule_id: dlq-depth-warning
    name: "DLQ Depth > 10 messages"
    metric_name: dead_letter_queue_depth
    condition: gt
    threshold: 10.0
    severity: WARNING
    channels: [SLACK]
    cooldown_seconds: 300

  - rule_id: gcs-latency-warning
    name: "GCS Write Latency > 30s"
    metric_name: gcs_write_latency_seconds
    condition: gt
    threshold: 30.0
    severity: WARNING
    channels: [SLACK]
    cooldown_seconds: 600

  - rule_id: fill-rate-low
    name: "Order Fill Rate < 80%"
    metric_name: order_fill_rate_pct
    condition: lt
    threshold: 0.80
    severity: CRITICAL
    channels: [SLACK, PAGERDUTY]
    cooldown_seconds: 300

  - rule_id: exec-latency-warning
    name: "Execution Latency > 500ms"
    metric_name: trade_execution_latency_seconds
    condition: gt
    threshold: 0.5
    severity: WARNING
    channels: [SLACK, UI]
    cooldown_seconds: 300

  - rule_id: pnl-drawdown-critical
    name: "PnL Drawdown > 5% Daily"
    metric_name: pnl_drawdown_pct
    condition: lt
    threshold: -0.05
    severity: CRITICAL
    channels: [SLACK, PAGERDUTY, EMAIL]
    cooldown_seconds: 3600

  - rule_id: ibgw-disconnect
    name: "IB Gateway Disconnected"
    metric_name: ibkr_gateway_connected
    condition: eq
    threshold: 0.0
    severity: FATAL
    channels: [SLACK, PAGERDUTY, EMAIL, UI]
    cooldown_seconds: 60

  - rule_id: position-notional-breach
    name: "Position Notional > $1M"
    metric_name: position_notional_usd
    condition: gt
    threshold: 1000000.0
    severity: CRITICAL
    channels: [SLACK, UI]
    cooldown_seconds: 300
```

---

## Part 3 — Order Book Visualization

### Architecture (confirmed design decision)

```
market-tick-data-handler (CLI batch + live, publishes to Pub/Sub)
    → Pub/Sub topic: ORDERBOOK_UPDATES (L2 normalized updates)
        → market-data-api (NEW standalone FastAPI repo)
            → maintains per-symbol OrderBookSnapshot in memory
            → GET /stream/orderbook?symbol=BTCUSDT&depth=20 SSE
            → GET /orderbook/{symbol}/snapshot REST
                → trading-analytics-ui /orderbook page
```

### market-data-api (new repo) — key details

Setup: `gh repo create IggyIkenna/market-data-api --private --clone`

```python
# market_data_api/core/orderbook_subscriber.py

@dataclass
class OrderBookSnapshot:
    symbol: str
    bids: list[tuple[float, float]]    # [(price, qty), ...] sorted desc
    asks: list[tuple[float, float]]    # [(price, qty), ...] sorted asc
    timestamp: datetime
    venue: str
    spread_bps: float

class OrderBookSubscriber:
    """Subscribes to ORDERBOOK_UPDATES Pub/Sub, maintains L2 book per symbol."""

    def __init__(self) -> None:
        self._books: dict[str, OrderBookSnapshot] = {}
        self._queues: dict[str, list[asyncio.Queue[OrderBookSnapshot]]] = {}

    async def start(self) -> None:
        """Start Pub/Sub subscription. Updates _books on each message."""
        queue_client = get_queue_client()   # unified-cloud-interface
        async for message in queue_client.subscribe("ORDERBOOK_UPDATES"):
            snapshot = OrderBookSnapshot(**message.data)
            self._books[snapshot.symbol] = snapshot
            for q in self._queues.get(snapshot.symbol, []):
                await q.put(snapshot)

    def subscribe(self, symbol: str) -> asyncio.Queue[OrderBookSnapshot]:
        q: asyncio.Queue[OrderBookSnapshot] = asyncio.Queue(maxsize=100)
        self._queues.setdefault(symbol, []).append(q)
        return q
```

```python
# market_data_api/api/routes/orderbook.py

@router.get("/stream/orderbook")
async def stream_orderbook(
    symbol: str,
    depth: int = 20,
    user: GoogleUser = Depends(get_current_user),
) -> EventSourceResponse:
    async def generator():
        q = subscriber.subscribe(symbol)
        while True:
            snapshot = await asyncio.wait_for(q.get(), timeout=30)
            bids = snapshot.bids[:depth]
            asks = snapshot.asks[:depth]
            payload = {
                "bids": bids,
                "asks": asks,
                "spread_bps": snapshot.spread_bps,
                "timestamp": snapshot.timestamp.isoformat(),
                "venue": snapshot.venue,
            }
            yield {"data": json.dumps(payload)}
    return EventSourceResponse(generator())
```

### UI visualization spec (trading-analytics-ui /orderbook)

```
OrderBook page: /orderbook

┌─────────────────────────────────────────────────────┐
│ Symbol: [BTCUSDT ▼]  Venue: [OKX ▼]  Spread: 2.3bps│
├────────────────┬────────────────────────────────────┤
│ Depth Chart                                          │
│ (recharts AreaChart, cumulative depth curve)         │
│ Bids=blue, Asks=red, Own bids=green dots             │
│ Own asks=orange dots                                 │
├────────────────┬────────────────────────────────────┤
│    BIDS        │    ASKS                             │
│ Price  Qty     │ Price  Qty                          │
│ 43210  1.5 ★  │ 43220  0.8                         │
│ 43200  2.1     │ 43225  1.2 [MY ORDER]              │
│ ...            │ ...                                 │
├────────────────────────────────────────────────────┤
│ Trade Tape (SSE from execution-results-api /stream/fills)│
│ 🟢 BUY  0.5 BTC @ 43215  14:23:01                  │
│ 🔴 SELL 1.0 BTC @ 43218  14:23:00  ★               │
└─────────────────────────────────────────────────────┘
```

---

## Part 4 — System Health Dashboard (live-health-monitor-ui)

### Data sources

```
GET /api/system/metrics?service={name}&window=1h
    ← alerting-service /api/system/metrics (aggregates Prometheus from all services)
GET /stream/alerts
    ← alerting-service /stream/alerts SSE (live AlertEvent stream)
GET /rules
    ← alerting-service /rules (list configured AlertRule)
```

### System Health page layout (/system-health)

```
┌─────────────────────────────── SYSTEM HEALTH ───────────────────────────────┐
│                                                                               │
│  Service Status Grid                                                          │
│  ● execution-results-api  HEALTHY  47ms    ● alerting-service  HEALTHY  12ms  │
│  ● position-balance-mon.  HEALTHY  23ms    ● client-reporting  HEALTHY  89ms │
│  ⚠ features-volatility    DEGRADED 892ms   ● market-data-api   HEALTHY  5ms  │
│  ● execution-service     HEALTHY  134ms   ● instruments-svc   HEALTHY  45ms │
│                                                                               │
│  CPU & Memory (1h)  [1h▼]                                                    │
│  [recharts LineChart, multi-service, threshold lines at 85%/90%]              │
│                                                                               │
│  PubSub Lag by Topic                                                          │
│  [recharts BarChart, green<1s yellow 1-5s red>5s]                            │
│                                                                               │
│  DLQ Depth                                                                    │
│  ORDERBOOK_UPDATES: 0  FILLS: 0  POSITIONS: 0  FEATURES: 3 🔴               │
│                                                                               │
│  Active Alerts (live SSE)                                                     │
│  🔴 14:25:01 CRITICAL  feature-staleness: features-volatility 892s > 300s   │
│  🟡 14:20:33 WARNING   gcs-latency: market-data-processing 35s > 30s        │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 5 — Deployment System (No Repo Split — Correct As-Is)

### Decision (updated from original plan)

`unified-trading-deployment-v3` co-locates `api/` (FastAPI backend) + `ui/` (React 19, Radix UI, Tailwind). This is **correct** — it is the deployment control plane where the UI and API are tightly coupled. No repo split.

**The existing ui/ already has 7 tabs**: Deploy, Data Status, Builds, Readiness, Status, Config, History. This is the system deployment UI. Keep it.

**ml-training-ui** is **NOT** the system deployment UI. It is the ML analytics and model deployment UI (experiments, metrics, promote model to inference service). See `config,_reporting_&_ui_completion` plan `ml-training-ui-scope-correct` todo.

### What IS needed

1. Add Google OAuth to `unified-trading-deployment-v3/api/auth_middleware.py` — it already has `auth_middleware.py`, wire to `GoogleOAuthMiddleware` from `unified-trading-services`.
2. Add `/metrics` Prometheus endpoint to `unified-trading-deployment-v3/api/main.py`.
3. Extract StrategyConfig/ExecutionConfig CRUD into `api/routes/config_service.py` with `/api/v1/configs/`* routes — shared with execution-analytics-ui and onboarding-ui.
4. Add Grafana dashboard JSONs to `unified-trading-deployment-v3/grafana/` directory.

---

## Part 6 — Grafana / Prometheus Codex

### Grafana dashboards (export-only, no live Grafana required)

Files to create in `unified-trading-deployment-v3/grafana/`:

```
grafana/
├── dashboards/
│   ├── trading-overview.json        # Execution latency, position notional, circuit breaker
│   └── system-health.json           # CPU/memory per service, GCS latency, DLQ depth
└── provisioning/
    └── datasources/
        └── prometheus.yaml          # Points to ${PROMETHEUS_URL}
```

### Codex doc

`unified-trading-codex/03-observability/prometheus-metrics.md`:

```markdown
# Prometheus Metrics Catalog

## Metric Definitions
| Metric | Type | Labels | Service | Description |
|--------|------|--------|---------|-------------|
| trade_execution_latency_seconds | Histogram | venue, strategy_id, instrument_type | execution-service | Signal to order |
| orders_submitted_total | Counter | venue, order_type, side | execution-service | Total orders |
| order_fill_rate_pct | Gauge | venue, strategy_id | execution-service | Rolling 1h fill rate |
| position_notional_usd | Gauge | strategy_id, instrument_key | position-balance-monitor | Current notional |
| reconciliation_drift_usd | Gauge | venue, account_id | position-balance-monitor | Internal vs exchange |
| feature_staleness_seconds | Gauge | feature_name, service | features-* | Age of latest compute |
| gcs_write_latency_seconds | Histogram | bucket, service | all | GCS write time |
| pubsub_message_lag_seconds | Gauge | topic, service | market-tick-data-handler | Pub/Sub lag |
| dead_letter_queue_depth | Gauge | topic | market-tick-data-handler | DLQ depth |
| api_request_latency_seconds | Histogram | service, endpoint, method | all FastAPI | HTTP latency |
| circuit_breaker_state | Gauge | strategy_id, trigger_type | execution-service | 0=closed,1=half,2=open |
| pnl_drawdown_pct | Gauge | strategy_id, client_id | pnl-attribution | Drawdown from peak |
| ibkr_gateway_connected | Gauge | account_id | execution-service | 1=connected |
| ibkr_roundtrip_latency_seconds | Histogram | account_id | execution-service | TWS roundtrip |

## Service → /metrics Endpoint Map
| Service | URL |
|---------|-----|
| execution-results-api | http://execution-results-api:8080/metrics |
| position-balance-monitor-service | http://position-balance-monitor:8080/metrics |
| execution-service | http://execution-service:8080/metrics |
| alerting-service | http://alerting-service:8080/metrics |
| client-reporting-api | http://client-reporting-api:8080/metrics |
| market-data-api | http://market-data-api:8080/metrics |
| unified-trading-deployment-v3 | http://deployment-api:8080/metrics |

## Alert Triage Guide
| Alert | First Check | Action |
|-------|------------|--------|
| circuit-breaker-open | execution-service logs | Check fill rejection rate, venue connectivity |
| recon-drift-critical | position-balance-monitor /reconciliation | Trigger manual reconciliation, check exchange balance |
| ibgw-disconnect | IB Gateway process | Restart IB Gateway, check TWS session |
| feature-staleness-warning | features-* service logs | Check GCS write, restart service if stalled |
| pnl-drawdown-critical | pnl-attribution-service logs | Notify trader, consider reducing position |
```

---

## Execution Order

**Wave 1 — Foundations (blocking everything)**:

1. `prometheus-client-add-to-uts` — all other metrics work depends on this
2. `alert-rule-schemas-uic` — blocking alerting-service build

**Wave 2 — Core Services**:
3. `alerting-service-build-out` — central hub
4. `standard-alert-rules-config`
5. `metrics-endpoint-fastapi-services`
6. `market-data-api-new-repo`
7. `metrics-aggregator-api`

**Wave 3 — UI + Codex**:
8. `orderbook-viz-ui`
9. `latency-plots-ui`
10. `system-health-page`
11. `deployment-service-split` (actually just additions, not split)
12. `grafana-export`
13. `prometheus-codex`
