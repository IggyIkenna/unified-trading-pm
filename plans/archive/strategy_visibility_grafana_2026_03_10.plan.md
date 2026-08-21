---
doc_type: plan
title: strategy-visibility-grafana-2026-03-10
summary: Deploy Grafana on Cloud Run, add Prometheus metrics to strategy/execution/PnL services, create 5 dashboards (strategy
  performance, market data health, execution quality, system health, DeFi), and embed Grafana panels into unified-admin-ui.
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, execution-service, strategy-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: code
epic: epic-code-completion
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: strategy-service, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: execution-service, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: pnl-attribution-service, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-trading-library, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-admin-ui, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: Grafana infrastructure config files in PM are provisioning artifacts — cloud deployment readiness tracked at plan completion_gates level (D3). BR N/A: no commercial sign-off required for a code plan.'}
- {repo: strategy-analysis-ui, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: [phase3-service-hardening-integration, data-availability-live-expectations-2026-03-10, recon-rebalancing-order-recovery-2026-03-10]
isProject: false
---

# Plan: Strategy Visibility — Grafana Integration

status: superseded superseded_by: cicd_code_rollout_master_2026_03_13 superseded_date: 2026-03-13

> ⚠️ **M4 SEQUENCING NOTE (2026-03-11):** This plan depends on `recon_rebalancing_order_recovery_2026_03_10` being
> committed to `strategy-service` first. Grafana dashboards reference `DEFI_VAULT_REBALANCED` and other events/metrics
> from the recon_rebalancing plan. Do not begin Grafana integration (Phase 2+) until recon_rebalancing strategy-service
> changes are merged.

## Context

alerting-service exposes Prometheus metrics (RECORDS_PROCESSED, PROCESSING_LATENCY). strategy-service has
`signal_publisher.py`. pnl-attribution-service has `execution_alpha/calculator.py` producing 6-dimension PnL breakdown.
execution-service/benchmark/ has regime analysis and ranking. None of this is visible in a real-time dashboard.
unified-admin-ui has per-service pages but no time-series visualization. Grafana on Cloud Run with Prometheus + BigQuery
data sources delivers this at minimal cost (~$20/month). User requirement: deploy Grafana embedded/integrated into
existing UIs, replacing custom chart code with Grafana panels for time-series data.

---

## Phase 1: Infrastructure

### P1.1 — Grafana Cloud Run deployment

File: `unified-trading-pm/infrastructure/grafana/cloud-run-grafana.yaml`

Deploy Grafana to dev project first, promote to prod after dashboards validated.

Dev: `https://grafana.unified-trading-dev.run.app` Prod: `https://grafana.unified-trading.run.app`

Config:

- Auth proxy enabled: deployment-api JWT → `X-Grafana-User` header → Grafana trusts it
- Anonymous access disabled
- Persistent storage: Cloud SQL Postgres (Grafana state: dashboards, users, alerts)
- Resource: 0.5 vCPU, 512MB RAM (sufficient for <10 concurrent users)

### P1.2 — Prometheus data source

File: `unified-trading-pm/infrastructure/grafana/provisioning/datasources/prometheus.yaml`

Two options (select based on what's deployed):

1. alerting-service Prometheus endpoint (`:9090/metrics`) — if self-hosted Prometheus
2. GCP Cloud Monitoring → Prometheus bridge — preferred (managed)

### P1.3 — BigQuery data source

Configure Grafana BigQuery plugin:

- SA key: `unified-trading-grafana@unified-trading-prod.iam.gserviceaccount.com`
- Materialized views (create in BigQuery):
  - `unified_trading.daily_pnl_by_strategy` — daily PnL × 6 dimensions
  - `unified_trading.monthly_sharpe_by_strategy` — rolling 30d Sharpe
  - `unified_trading.order_latency_histogram` — hourly p50/p95/p99

### P1.4 — Docker Compose for local dev

File: `unified-trading-pm/infrastructure/grafana/docker-compose.dev.yaml`

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes:
      - ./provisioning:/etc/grafana/provisioning
      - ./dashboards:/var/lib/grafana/dashboards
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true" # dev only
      GF_SECURITY_ADMIN_PASSWORD: "dev"
```

---

## Phase 2: Prometheus metrics expansion

### P2.1 — Strategy-service metrics

File: `strategy-service/strategy_service/engine/core/signal_publisher.py` (extend)

```python
from prometheus_client import Gauge, Counter, Histogram

SIGNAL_SCORE = Gauge(
    "strategy_signal_score", "Current signal score [-1, 1]",
    ["strategy", "asset", "timeframe"]
)
SIGNAL_COUNT = Counter(
    "strategy_signals_total", "Signals generated",
    ["strategy", "direction"]  # direction: long|short|flat
)
MARKET_REGIME = Gauge(
    "strategy_market_regime", "Current regime (0=bear, 0.5=neutral, 1=bull)",
    ["strategy"]
)
SIGNAL_LATENCY = Histogram(
    "strategy_signal_generation_ms", "Signal generation latency",
    ["strategy"], buckets=[50, 100, 200, 500, 1000, 2000]
)
```

### P2.2 — Execution-service metrics

File: `execution-service/execution_service/metrics.py` (new)

```python
ORDER_LATENCY_MS = Histogram(
    "execution_order_latency_ms", "Order submission latency",
    ["venue", "order_type"], buckets=[50, 100, 200, 500, 1000]
)
FILL_RATE = Gauge("execution_fill_rate_pct", "Fill rate %", ["venue"])
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state", "0=closed/half-open, 1=open", ["venue"]
)
ORDERS_SUBMITTED = Counter("execution_orders_total", "Orders submitted", ["venue", "side"])
SLIPPAGE_BPS = Histogram(
    "execution_slippage_bps", "Execution slippage in basis points",
    ["venue"], buckets=[0, 1, 2, 5, 10, 20, 50]
)
```

### P2.3 — PnL-attribution metrics

File: `pnl-attribution-service/pnl_attribution_service/metrics.py` (new)

```python
PNL_RUNNING_USD = Gauge(
    "pnl_running_usd", "Running PnL USD",
    ["strategy", "dimension"]  # dimensions: alpha, beta, carry, vol_premium, timing, tx_cost
)
SHARPE_ROLLING_30D = Gauge("pnl_sharpe_rolling_30d", "Rolling 30d Sharpe", ["strategy"])
DRAWDOWN_CURRENT_PCT = Gauge("pnl_drawdown_current_pct", "Current drawdown %", ["strategy"])
WIN_RATE = Gauge("pnl_win_rate_pct", "Win rate %", ["strategy"])
```

### P2.4 — Feature pipeline metrics

File: `unified-trading-library/unified_trading_library/monitors/feature_metrics.py` (new)

```python
FEATURE_LAG_SECONDS = Gauge(
    "feature_lag_seconds", "Feature pipeline lag",
    ["service", "asset_group"]
)
FEATURE_COVERAGE_PCT = Gauge(
    "feature_coverage_pct", "% of expected features present",
    ["service"]
)
```

Wire `feature_metrics.py` into each of the 8 features services.

---

## Phase 3: Grafana dashboards

All dashboard JSON files go in: `unified-trading-pm/infrastructure/grafana/dashboards/` Provision via
`unified-trading-pm/infrastructure/grafana/provisioning/dashboards/default.yaml`

### P3.1 — Strategy performance dashboard

File: `dashboards/strategy_performance.json`

Panels:

- **Signal scores** (time series, 24h window): per strategy × top 5 assets, score [-1, 1]
- **PnL 6-dim breakdown** (stacked area): alpha/beta/carry/vol_premium/timing/tx_cost daily
- **30d rolling Sharpe** (time series): per strategy, target line at 1.0
- **Win rate + expectancy** (stat panels): current values
- **Active positions** (table): asset, side, size, entry price, unrealized PnL, age

### P3.2 — Market data health dashboard

File: `dashboards/market_data_health.json`

Panels:

- **Data freshness heatmap** (heatmap): venue × hour-of-day, color = staleness
- **Tick rate per venue** (time series): ticks/second
- **Feature pipeline lag** (bar chart): per service, target line
- **Feed health events** (table): last 20 FEED_UNHEALTHY events

### P3.3 — Execution quality dashboard

File: `dashboards/execution_quality.json`

Panels:

- **Order latency** (time series): p50/p95/p99 per venue
- **Fill rates** (gauge): per venue, green/yellow/red thresholds
- **Circuit breaker states** (state timeline): open/closed history per venue
- **Slippage distribution** (histogram): bps per venue

### P3.4 — System health dashboard

File: `dashboards/system_health.json`

Panels:

- **CPU/memory** (time series): per Cloud Run service
- **Error rates** (time series): errors/minute per service
- **Event throughput** (time series): UEI events/second per type
- **Circuit breaker open events** (event annotations): on all charts

### P3.5 — DeFi dashboard

File: `dashboards/defi_strategies.json`

Panels:

- **Protocol yields** (bar chart, refreshed 5m): Aave/Curve/Uniswap/Lido/Morpho APY
- **Vault allocation** (pie chart): current distribution across protocols
- **ETH gas price** (time series): fast/standard/safe
- **Rebalance history** (table): last 20 DEFI_VAULT_REBALANCED events

---

## Phase 4: UI integration

### P4.1 — GrafanaPanel component

File: `unified-admin-ui/packages/grafana-integration/src/GrafanaPanel.tsx` (new package)

```typescript
interface GrafanaPanelProps {
  dashboardUid: string;
  panelId: number;
  height?: number;
  timeRange?: { from: string; to: string };  // e.g. "now-24h", "now"
  theme?: "light" | "dark";
}

export const GrafanaPanel: React.FC<GrafanaPanelProps> = ({
  dashboardUid, panelId, height = 300, timeRange, theme = "light"
}) => {
  const grafanaUrl = useGrafanaBaseUrl();  // from env config
  const params = new URLSearchParams({
    panelId: String(panelId),
    theme,
    ...(timeRange ? { from: timeRange.from, to: timeRange.to } : {}),
  });
  return (
    <iframe
      src={`${grafanaUrl}/d-solo/${dashboardUid}?${params}`}
      width="100%"
      height={height}
      frameBorder="0"
      title={`Grafana panel ${panelId}`}
    />
  );
};
```

### P4.2 — Replace charts in strategy-analysis-ui

Identify existing custom chart components in `strategy-analysis-ui` that are time-series:

- Signal score charts → replace with `GrafanaPanel` (strategy_performance, panel: signal_scores)
- PnL history → replace with `GrafanaPanel` (strategy_performance, panel: pnl_breakdown)
- Keep: data tables, non-time-series gauges, custom interactive components

### P4.3 — Add Grafana links to admin UI nav

Add "Dashboards" section to unified-admin-ui sidebar:

- Strategy Performance → links to full Grafana dashboard (new tab)
- Market Data Health → links to health dashboard
- Execution Quality → links to execution dashboard
- System Health → links to system dashboard

---

## Phase 5: Strategy development workflow

### P5.1 — Strategy scoring breakdown view

New Grafana dashboard per strategy (templated with `$strategy` variable):

- Per-signal-component score breakdown (what's contributing to the signal)
- Regime state timeline and its weight impact
- Feature values driving each component (last 24h)
- Annotations: actual trades placed

### P5.2 — Strategy comparison view

Grafana dashboard with `$strategy_a` and `$strategy_b` variables:

- Side-by-side: Sharpe, max drawdown, win rate, avg trade duration
- Correlation heatmap of signals across strategies

---

## Verification Gates

- [ ] Grafana deployed to dev Cloud Run: `curl https://grafana.unified-trading-dev.run.app/api/health` →
      `{"database":"ok"}`
- [ ] All 5 dashboards load with real data (no "No data" panels)
- [ ] `GrafanaPanel` component renders in unified-admin-ui strategy page
- [ ] Auth proxy: accessing Grafana without JWT → 401; with valid JWT → dashboard loads
- [ ] Prometheus metrics from strategy-service, execution-service, pnl-attribution-service visible in Prometheus data
      source

## Files Created / Modified

- `unified-trading-pm/infrastructure/grafana/` (new directory, all YAML + JSON files)
- `strategy-service/engine/core/signal_publisher.py` (extend with Prometheus metrics)
- `execution-service/execution_service/metrics.py` (new)
- `pnl-attribution-service/pnl_attribution_service/metrics.py` (new)
- `unified-trading-library/monitors/feature_metrics.py` (new)
- `unified-admin-ui/packages/grafana-integration/` (new package)
- `unified-admin-ui/packages/grafana-integration/src/GrafanaPanel.tsx` (new)

## Dependencies

- `phase3_service_hardening_integration` (services must be deployed with Prometheus endpoints)
- `data_availability_live_expectations_2026_03_10` (DATA_STALE events used in health dashboard)
- `recon_rebalancing_order_recovery_2026_03_10` (DEFI_VAULT_REBALANCED events in DeFi dashboard)
