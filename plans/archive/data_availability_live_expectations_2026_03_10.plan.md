---
doc_type: plan
title: data-availability-live-expectations-2026-03-10
summary: Add per-source freshness contracts, FreshnessMonitor base class in UTL, per-service freshness gates in strategy/execution,
  alerting integration, and daily completeness check — so stale data is detected within 60 second in live mode.
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, market-data-processing-service, market-tick-data-service, strategy-service, system-integration-tests]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: code
epic: epic-code-completion
superseded_by: defi_keys_data_integration_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-internal-contracts, code: C1, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-trading-library, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-events-interface, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: strategy-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: execution-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: alerting-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: system-integration-tests, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: [uei_pending_event_additions]
todos:
- {id: phase-0-freshness-contracts, content: Add DataFreshnessContract model + all 30 source definitions to unified-internal-contracts/reference/data_freshness.py., status: done, note: All 30 data sources have DataFreshnessContract entries (gate checkbox checked).}
- {id: phase-1-freshness-monitor-utl, content: Write FreshnessMonitor base class in unified-trading-library/monitors/freshness_monitor.py with async monitor() and check_once()., status: todo, note: ''}
- {id: phase-1-wire-services, content: 'Wire FreshnessMonitor in all 10 data-producing services: market-tick-data-service, market-data-processing-service, all 8 features-* services, ml-inference-api.', status: todo, note: ''}
- {id: phase-1-consuming-gates, content: Add assert_feature_fresh() to strategy-service and assert_market_data_fresh() to execution-service., status: todo, note: ''}
- {id: phase-2-uei-events, content: 'Add DATA_STALE, DATA_AVAILABILITY_RESTORED, DATA_GAP_DETECTED, FEED_UNHEALTHY, DATA_COMPLETENESS_CHECK to unified-events-interface/schemas.py via uei_pending_event_additions plan.', status: todo, note: Blocked — must batch with other UEI event additions via uei_pending_event_additions.md.}
- {id: phase-3-alerting, content: Write alerting-service/rules/data_freshness_rules.py with FEED_UNHEALTHY (PagerDuty + Telegram) and DATA_STALE (Telegram) alert rules., status: todo, note: ''}
- {id: phase-4-completeness-check, content: Write unified-trading-pm/scripts/ops/check-data-completeness.sh and system-integration-tests/tests/integration/test_data_freshness.py., status: todo, note: ''}
isProject: false
---

# Plan: Data Availability vs Expectations (Live Monitoring)

## Context

`unified-internal-contracts` has staleness thresholds for onchain data per blockchain (`onchain_freshness.py`). Nothing
equivalent exists for market tick data per venue, feature pipeline outputs, ML model artifacts, or instruments metadata.
In live mode, a stale data feed is indistinguishable from a healthy one unless a service explicitly checks. An
undetected stale feed produces bad signals and incorrect orders. Goal: every data-producing service monitors its own
output freshness; every data-consuming service rejects inputs beyond freshness SLA; alerting-service escalates
`FEED_UNHEALTHY` events within 60 seconds of threshold breach. No production data quality surprise.

---

## Phase 0: Freshness contracts for all data sources

### P0.1 — Expand unified-internal-contracts

File: `unified-internal-contracts/unified_internal_contracts/reference/data_freshness.py` (new)

Extends `onchain_freshness.py` pattern to all sources:

```python
class DataFreshnessContract(BaseModel):
    source: str
    asset_group: str  # "crypto_cefi"|"crypto_defi"|"tradfi"|"onchain"|"sports"|"feature"|"ml"
    max_age_seconds: int       # FEED_UNHEALTHY threshold
    warn_age_seconds: int      # DATA_STALE threshold (warning)
    expected_cadence_seconds: int  # how often data should arrive
    criticality: str           # "critical"|"important"|"informational"
```

Contract definitions — all sources:

**Market tick data:** | Source | max_age_s | warn_age_s | cadence_s | criticality | |---|---|---|---|---| | binance,
bybit, okx, coinbase, hyperliquid | 5 | 2 | 1 | critical | | deribit | 10 | 3 | 1 | critical | | uniswap_v3, aave_v3,
curve, balancer | 15 | 6 | 12 | critical | | databento (intraday) | 60 | 30 | 60 | important | | databento (EOD),
yahoo_finance | 86400 | 43200 | 86400 | important | | openbb, fred, ecb, ofr | 86400 | 43200 | 86400 | informational | |
pinnacle, odds_api | 300 | 60 | 30 | important | | betfair | 60 | 15 | 5 | important | | glassnode, coinglass | 3600 |
1800 | 3600 | important | | arkham | 3600 | 1800 | 3600 | informational |

**Feature pipeline:** | Service | max_age_s | warn_age_s | cadence_s | criticality | |---|---|---|---|---| |
features-delta-one-service | 120 | 60 | 60 | critical | | features-volatility-service | 300 | 150 | 60 | critical | |
features-onchain-service | 600 | 300 | 300 | important | | features-calendar-service | 86400 | 43200 | 3600 |
informational | | features-commodity-service | 3600 | 1800 | 3600 | informational | | features-cross-instrument-service
| 300 | 150 | 60 | important | | features-multi-timeframe-service | 300 | 150 | 60 | critical | |
features-sports-service | 300 | 60 | 60 | important |

**ML outputs:** | Service | max_age_s | warn_age_s | cadence_s | criticality | |---|---|---|---|---| | ml-inference-api
| 120 | 60 | 60 | critical | | ml-training-api (artifacts) | 604800 (7d) | 259200 (3d) | 86400 | informational |

---

## Phase 1: FreshnessMonitor base class

### P1.1 — Shared base class in UTL

File: `unified-trading-library/unified_trading_library/monitors/freshness_monitor.py` (new)

```python
class FreshnessMonitor:
    """
    Instantiated per data-producing service with its DataFreshnessContract.
    Background coroutine; checks last_update_timestamp every check_interval_seconds.
    On warn breach: emits DATA_STALE. On max breach: emits FEED_UNHEALTHY.
    On recovery: emits DATA_AVAILABILITY_RESTORED.
    """
    def __init__(self, contract: DataFreshnessContract, check_interval_seconds: int = 10) -> None: ...

    async def monitor(self, get_last_update_fn: Callable[[], datetime]) -> None:
        """Run as asyncio.create_task() in service startup."""

    async def check_once(self) -> FreshnessStatus: ...
```

### P1.2 — Wire FreshnessMonitor in each data-producing service

Services to update (add `FreshnessMonitor` in `live_mode_handler.py`):

- `market-tick-data-service` — per-venue freshness (last tick timestamp per venue)
- `market-data-processing-service` — per-symbol
- `features-delta-one-service`, `features-volatility-service`, `features-onchain-service`, `features-calendar-service`,
  `features-commodity-service`, `features-cross-instrument-service`, `features-multi-timeframe-service`,
  `features-sports-service` (all 8)
- `ml-inference-api` — per-model inference freshness

### P1.3 — Freshness gate in consuming services

**strategy-service** — before using a feature vector:

```python
def assert_feature_fresh(feature_ts: datetime, service: str) -> None:
    contract = FEATURE_FRESHNESS[service]
    age = (datetime.utcnow() - feature_ts).total_seconds()
    if age > contract.max_age_seconds:
        raise DataStalenessError(f"{service} features are {age:.0f}s old, max {contract.max_age_seconds}s")
    if age > contract.warn_age_seconds:
        log_event(DATA_STALE, source=service, age_seconds=age)
```

**execution-service** — before submitting an order:

```python
def assert_market_data_fresh(venue: str, last_tick_ts: datetime) -> None:
    contract = MARKET_TICK_FRESHNESS[venue]
    age = (datetime.utcnow() - last_tick_ts).total_seconds()
    if age > contract.max_age_seconds:
        raise DataStalenessError(f"{venue} market data is {age:.0f}s old — order blocked")
```

---

## Phase 2: New UEI events

> ⚠️ **H1 CONSOLIDATION NOTE (2026-03-11):** These 5 UEI events are tracked in the consolidated plan
> `uei_pending_event_additions.md` along with events from recon_rebalancing and position_precision_pnl. All UEI event
> additions must be batched into a single PR to avoid merge conflicts on schemas.py. Do not add these events
> independently — coordinate via the consolidated plan.

### P2.1 — Add to unified-events-interface/schemas.py

```python
DATA_STALE = "DATA_STALE"                           # warn threshold breached
DATA_AVAILABILITY_RESTORED = "DATA_AVAILABILITY_RESTORED"
DATA_GAP_DETECTED = "DATA_GAP_DETECTED"             # gap in time series
FEED_UNHEALTHY = "FEED_UNHEALTHY"                   # max threshold breached
DATA_COMPLETENESS_CHECK = "DATA_COMPLETENESS_CHECK" # scheduled completeness report
```

Payload schema for `DATA_STALE` / `FEED_UNHEALTHY`: `source`, `age_seconds`, `max_age_seconds`, `asset_group`,
`criticality`, `timestamp`

---

## Phase 3: Alerting integration

### P3.1 — Freshness alert rules

File: `alerting-service/alerting_service/rules/data_freshness_rules.py` (new)

| Event               | Criticality   | Alert Channel                  | SLA         |
| ------------------- | ------------- | ------------------------------ | ----------- |
| `FEED_UNHEALTHY`    | critical      | PagerDuty + Telegram           | immediate   |
| `DATA_STALE`        | critical      | Telegram                       | within 60s  |
| `DATA_STALE`        | important     | Telegram                       | within 300s |
| `DATA_GAP_DETECTED` | any           | Telegram (if gap > 2× cadence) | within 300s |
| `FEED_UNHEALTHY`    | informational | log only                       | —           |

---

## Phase 4: Daily completeness check

### P4.1 — Completeness check script

File: `unified-trading-pm/scripts/ops/check-data-completeness.sh` Runs daily at 08:00 UTC via Cloud Scheduler. For each
service:

- Counts rows in GCS/BigQuery for yesterday
- Compares vs expected count: `trading_hours × (3600 / cadence_seconds) × venue_count`
- Emits `DATA_COMPLETENESS_CHECK` event with `pass=True/False`, `coverage_pct`
- Generates: `unified-trading-pm/reports/data_completeness_YYYY-MM-DD.md`

### P4.2 — SIT test

File: `system-integration-tests/tests/integration/test_data_freshness.py`

- For each monitored service: inject artificially old timestamp → verify `FEED_UNHEALTHY` fires
- Verify consuming service (`strategy-service`) raises `DataStalenessError` on stale features
- Verify `DATA_AVAILABILITY_RESTORED` fires after fresh data arrives
- Verify execution-service blocks order on stale market data

---

## Verification Gates

- [x] All 30 data sources have `DataFreshnessContract` entries
- [ ] `FreshnessMonitor` wired in all 10 data-producing services
- [ ] `strategy-service` and `execution-service` have freshness gates blocking stale data
- [ ] SIT freshness test green
- [ ] Daily completeness check script runs and reports >95% coverage

## Files Modified / Created

- `unified-internal-contracts/reference/data_freshness.py` (new)
- `unified-events-interface/schemas.py` (5 new events)
- `unified-trading-library/monitors/freshness_monitor.py` (new)
- `market-tick-data-service/monitors/freshness_monitor.py` (wire)
- `features-*/cli/handlers/live_mode_handler.py` (wire, all 8)
- `ml-inference-api/monitors/freshness_monitor.py` (wire)
- `strategy-service/engine/core/feature_validator.py` (new freshness gate)
- `execution-service/engine/market_data_validator.py` (new freshness gate)
- `alerting-service/rules/data_freshness_rules.py` (new)
- `unified-trading-pm/scripts/ops/check-data-completeness.sh` (new)
- `system-integration-tests/tests/integration/test_data_freshness.py` (new)

## Dependencies

- `error_normalisation_unknown_exchanges_2026_03_10.md` (`DataStalenessError` follows canonical pattern)
- `strategy_visibility_grafana_2026_03_10.md` (data freshness heatmap dashboard)
- `live_batch_protocol_completeness_2026_03_10.md` (freshness monitoring is live-mode only)
