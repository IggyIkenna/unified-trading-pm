> **ARCHIVED (2026-07-27) — genuine coverage gap found.** Blank template. alerting-service's own
> `tests/e2e/test_mock_replay_e2e.py` (178 lines) never actually imports `alerting_service.*` — it re-implements ad-hoc
> assertions over VCR cassette data, not the real rule/notifier pipeline. This is a real, unaddressed E2E gap. Coverage
> gap found (2026-07-27): the file's own template was blank/never-executed. Real E2E coverage does not yet exist for
> this service — tracked as a new gap in
> `plans/archive/2026_07/e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md` (archived 2026-07-30, all 3
> todos done — a real harness now exists, see that doc).

---

title: "E2E Test: alerting-service" service: alerting-service date: 2026-03-22 status: pending
---

# E2E Test: alerting-service

Follows `procedure.md`. Pipeline position: L6 monitoring (cross-cutting, one-to-many).

## Service Characteristics

**Cross-cutting service.** Unlike pipeline services that process data in sequence, alerting-service subscribes to PubSub
alert topics from multiple upstream services and can issue circuit breaker commands that downstream services MUST honor.

- **NOT ServiceCLI-based** -- uses argparse directly with `--mode batch/live`
- **No `--operation`** -- single responsibility (subscribe + route alerts)
- **No `--asset-group`** -- processes all alerts regardless of category
- **Modes:** `batch`, `live`
- **Mock mode:** `CLOUD_MOCK_MODE=true` triggers `run_mock_pipeline()` before argparse (early exit)

## Upstream Dependencies

| Source service                   | PubSub subscription                    | Event types                                     |
| -------------------------------- | -------------------------------------- | ----------------------------------------------- |
| risk-and-exposure-service        | `risk_alerts_circuit_breaker_triggers` | Risk threshold breaches, CB triggers            |
| position-balance-monitor-service | `balance_discrepancy_alerts`           | Balance drift, reconciliation failures          |
| execution-service                | `order_rejection_spikes`               | Order rejection rate spikes                     |
| execution-service (coordination) | (inline events)                        | `KILL_SWITCH_ACTIVATED`, `CIRCUIT_BREAKER_OPEN` |

## Downstream Commands

| Target service    | Channel                         | Command type           |
| ----------------- | ------------------------------- | ---------------------- |
| execution-service | `circuit_breaker_commands`      | Halt order submission  |
| strategy-service  | `circuit_breaker_commands`      | Halt signal generation |
| deployment-api    | `service_stop_restart_triggers` | Service stop/restart   |

## Alert Routing Rules (config-driven)

Routing is fnmatch glob-based, first match wins (from `AlertingSystemConfig.routing_rules`):

| Pattern                       | Channels             | Severity |
| ----------------------------- | -------------------- | -------- |
| `KILL_SWITCH_*`               | PagerDuty + Telegram | critical |
| `CIRCUIT_BREAKER_OPEN`        | PagerDuty + Telegram | critical |
| `DEFI_HEALTH_FACTOR_CRITICAL` | PagerDuty + Telegram | critical |
| `DEFI_WEETH_DEPEG`            | PagerDuty + Telegram | critical |
| `DEFI_AAVE_UTILIZATION_SPIKE` | Telegram             | --       |
| `DEFI_FUNDING_RATE_FLIP`      | Telegram             | --       |
| `DEFI_FEATURE_STALE`          | Telegram             | --       |
| `PREFLIGHT_FAILED`            | Telegram             | --       |
| `SERVICE_DEGRADED`            | Telegram             | --       |
| `*` (catch-all)               | Telegram             | --       |

## Alert Lifecycle

`created` (PubSub message received) -> `acknowledged` (operator action) -> `escalated` (PagerDuty) -> `resolved`

## Frontend API Surface

| Endpoint                        | Method | What it feeds                     |
| ------------------------------- | ------ | --------------------------------- |
| `GET /alerts/active`            | GET    | Active alerts list (live + batch) |
| `POST /alerts/{id}/acknowledge` | POST   | Mark alert as acknowledged        |
| `POST /alerts/{id}/escalate`    | POST   | Escalate alert to PagerDuty       |
| Notification bell count         | GET    | Unacknowledged alert count        |
| Alert severity breakdown        | GET    | Pie chart by severity             |
| Alerts tab in Observe service   | --     | Full alert management UI          |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                          | Status |
| --- | ------------------------------------------------------------------------------- | --------------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                                |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK (mock pipeline runs)           |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                                |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED         |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED         |        |
| 1.6 | `LOG_LEVEL=INVALID`                                                             | SystemExit with valid values list |        |

Note: alerting-service does NOT use ServiceRuntime. Startup validation is limited to `LOG_LEVEL` enum check and
`AlertingSystemConfig()` Pydantic validation. Test 1.4/1.5 only apply if `UnifiedCloudConfig` validates these.

### Phase 2: Dry-Run

Alerting-service has no `--dry-run` flag. It is an event router, not a pipeline writer. The closest equivalent is
running in mock mode (`CLOUD_MOCK_MODE=true`) which skips notification delivery.

| #   | Mode  | Mock mode | Expected                                                                                                          | Status |
| --- | ----- | --------- | ----------------------------------------------------------------------------------------------------------------- | ------ |
| 2.1 | batch | true      | Mock pipeline runs, loads risk metrics from seed, writes alerts to `.local-dev-cache/mock-seed/alerting-service/` |        |
| 2.2 | live  | true      | Mock pipeline runs (same behavior -- mock exits before mode check)                                                |        |
| 2.3 | batch | false     | Starts PubSubEventSink, AlertSubscriber, waits for messages                                                       |        |

### Phase 3: Real Writes (dev environment)

Not applicable in the traditional sense. Alerting-service writes to:

- GCS alert history (via `AlertStorageStore.write_alert_history()`)
- GCS config snapshots (via `AlertStorageStore.write_config_snapshot()`)
- PagerDuty / Telegram / Slack (external delivery)

| #   | Test                                                           | Expected                                                | Status |
| --- | -------------------------------------------------------------- | ------------------------------------------------------- | ------ |
| 3.1 | Publish test message to `risk_alerts_circuit_breaker_triggers` | Alert received, routed to Telegram, GCS history written |        |
| 3.2 | Publish `KILL_SWITCH_ACTIVATED` event                          | Routed to PagerDuty (critical) + Telegram               |        |
| 3.3 | Publish `CIRCUIT_BREAKER_OPEN` event                           | Routed to PagerDuty (critical) + Telegram               |        |
| 3.4 | Publish duplicate event within 60s                             | Deduplicated (suppressed by `AlertDeduplicator`)        |        |
| 3.5 | Verify GCS alert history blob                                  | `write_alert_history()` persisted delivery record       |        |
| 3.6 | Verify GCS config snapshot                                     | `write_config_snapshot()` persisted routing rules       |        |

### Phase 4: Category Sweep

**Not applicable.** Alerting-service does not use `--asset-group`. It processes all alerts regardless of domain origin.
The routing is event-name-based (fnmatch), not category-based.

However, verify that alerts from ALL categories are routed correctly:

| #   | Alert origin category | Event name                    | Expected routing      | Status |
| --- | --------------------- | ----------------------------- | --------------------- | ------ |
| 4.1 | CEFI                  | `CIRCUIT_BREAKER_OPEN`        | PagerDuty + Telegram  |        |
| 4.2 | DEFI                  | `DEFI_HEALTH_FACTOR_CRITICAL` | PagerDuty + Telegram  |        |
| 4.3 | DEFI                  | `DEFI_AAVE_UTILIZATION_SPIKE` | Telegram only         |        |
| 4.4 | TRADFI                | `SERVICE_DEGRADED`            | Telegram only         |        |
| 4.5 | SPORTS                | (arbitrary event)             | Catch-all -> Telegram |        |
| 4.6 | PREDICTION            | (arbitrary event)             | Catch-all -> Telegram |        |

### Phase 5: Live Mode

Live mode is the PRIMARY mode for alerting-service. It runs an async subscriber loop polling PubSub subscriptions.

| #   | What                       | Expected                                               | Status |
| --- | -------------------------- | ------------------------------------------------------ | ------ |
| 5.1 | `--mode live` startup      | PubSubEventSink created, AlertSubscriber initialized   |        |
| 5.2 | Subscription polling       | Round-robin poll across 3 subscriptions                |        |
| 5.3 | Message processing         | Deserialized, enriched with correlation_id, routed     |        |
| 5.4 | Graceful shutdown (Ctrl-C) | `GracefulShutdownHandler` stops subscriber, clean exit |        |
| 5.5 | Malformed message          | `MALFORMED_EVENT` logged, subscriber loop continues    |        |
| 5.6 | PubSub unavailable         | Error logged, subscriber retries (no crash)            |        |
| 5.7 | Prometheus metrics         | `RECORDS_PROCESSED` and `PROCESSING_LATENCY` recorded  |        |

#### Phase 5b: Mock/Real A/B

| #    | Configuration                        | Expected behavior                                         | Status |
| ---- | ------------------------------------ | --------------------------------------------------------- | ------ |
| 5b.1 | `CLOUD_MOCK_MODE=true --mode live`   | Mock pipeline runs, writes to `.local-dev-cache/`, exits  |        |
| 5b.2 | `CLOUD_MOCK_MODE=false --mode live`  | Real PubSub subscriber starts, polls indefinitely         |        |
| 5b.3 | `CLOUD_MOCK_MODE=true --mode batch`  | Mock pipeline runs (identical to 5b.1)                    |        |
| 5b.4 | `CLOUD_MOCK_MODE=false --mode batch` | Real PubSub subscriber starts (batch = historical replay) |        |

### Phase 6: Mock Mode (scenario testing)

Mock mode loads risk metrics from upstream `risk-and-exposure-service` seed data, runs REAL threshold evaluation via
`evaluate_risk_thresholds()`, and writes alert records to `.local-dev-cache/mock-seed/alerting-service/alerts/`.

| #   | Scenario                       | What it tests                       | Expected                                            | Status |
| --- | ------------------------------ | ----------------------------------- | --------------------------------------------------- | ------ |
| 6.1 | Upstream seed present          | Risk metrics loaded from seed       | Alerts generated from real threshold evaluation     |        |
| 6.2 | Upstream seed missing          | Fallback risk metrics used          | Fallback values (leverage=8.5, etc.) trigger alerts |        |
| 6.3 | Seed already exists            | Idempotent re-run                   | "Seed data already present" log, skip generation    |        |
| 6.4 | Verify alert content           | Threshold evaluation correctness    | Alert severity, metric_name, metric_value correct   |        |
| 6.5 | Verify `.seed-complete` marker | Pipeline completion marker          | JSON with service name, layer=7, alert_count        |        |
| 6.6 | No notification delivery       | Mock skips PagerDuty/Telegram/Slack | No HTTP calls to external APIs                      |        |

### Phase 7: Observability

| #   | Check                            | Expected                                                        | Status |
| --- | -------------------------------- | --------------------------------------------------------------- | ------ |
| 7.1 | UEI lifecycle events             | STARTED, STOPPED/FAILED with correlation_id                     |        |
| 7.2 | ALERT_RECEIVED events            | Logged per message with subscription + correlation_id           |        |
| 7.3 | ALERT_ROUTED events              | Logged per routed event                                         |        |
| 7.4 | ALERT_SENT / ALERT_FAILED events | Logged per delivery attempt                                     |        |
| 7.5 | Prometheus metrics               | `RECORDS_PROCESSED{status=success/error}`, `PROCESSING_LATENCY` |        |
| 7.6 | Memory watchdog                  | `setup_service_observability(memory_threshold_pct=85.0)` active |        |
| 7.7 | Transport protocol logged        | "transport: X, storage: Y" line at startup                      |        |
| 7.8 | Deduplication logging            | "Duplicate alert suppressed" on repeated events                 |        |

## Known Issues Audit

Before running tests, check for these patterns known from prior services:

| Pattern                      | What to check                                                                    | Applies?                 |
| ---------------------------- | -------------------------------------------------------------------------------- | ------------------------ |
| `load_dotenv(override=True)` | `.env` overrides shell env vars silently                                         | Check                    |
| No ServiceRuntime            | Service uses raw argparse, not ServiceCLI/ServiceRuntime                         | Yes -- by design         |
| Mock mode early exit         | `config.is_mock_mode()` checked before argparse -- `--mode` never parsed in mock | Check if problematic     |
| PubSub emulator in tests     | `PUBSUB_EMULATOR_HOST` needed for local testing                                  | Check                    |
| GCS writes in router         | `AlertStorageStore` writes alert history + config snapshots                      | Verify bucket resolution |
| Telegram/Slack fallback      | If Telegram not configured, falls back to deprecated Slack                       | Note in findings         |
| `cast(str, args.mode)`       | argparse returns str but typed as Any -- cast is correct                         | OK                       |

## AWS Testing

Alerting-service is GCP-native (PubSub subscriber, GCS alert history). AWS equivalent would require:

- SQS subscriptions instead of PubSub
- S3 for alert history instead of GCS
- SNS for outbound notifications

| #   | Test                                       | Expected                            | Status |
| --- | ------------------------------------------ | ----------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`  | Mock pipeline runs (no cloud calls) |        |
| A.2 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=false` | UCI routes to SQS/S3 if wired       |        |

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |

## Next Service

After alerting-service passes all phases -> proceed to `021_batch_live_reconciliation_service.md`
