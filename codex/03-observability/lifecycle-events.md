---
doc_type: codex-ssot
title: Lifecycle Events
summary:
  "Lifecycle-event taxonomy: batch services emit 11 mandatory ordered events (STARTED→…→STOPPED/FAILED), live mode adds
  DATA_BROADCAST (12); required envelope fields + per-event extras; conditional event families (instruments-live,
  live-pipeline, ML, strategy hot-reload, kill-switch bus); ServiceBootstrap auto-emits STARTED/STOPPED/FAILED (QG STEP
  5.61). Machine SSOT = UAC internal/events.py."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, instruments-service, strategy-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [lifecycle-events, observability, pipeline, monitoring, data-quality, live-trading]
related:
  [
    /codex/03-observability/coordination-events.md,
    /codex/03-observability/alerting.md,
    /codex/04-architecture/data-flow-map.md,
    /codex/07-security/audit-logging.md,
  ]
created: 2026-03-27
authoritative_for: [lifecycle-event taxonomy, mandatory lifecycle event sequence]
referenced_by:
  [
    /codex/03-observability/alerting.md,
    /codex/03-observability/coordination-events.md,
    /codex/03-observability/slos.md,
    /codex/04-architecture/opentelemetry.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/06-coding-standards/correlation-id.md,
    /codex/07-security/audit-logging.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Lifecycle Events

## TL;DR

Every service must emit a structured sequence of lifecycle events via `log_event()` from
`unified_trading_library.events`. Batch services require **11 mandatory events**; live services require **12 mandatory
events** (batch set plus `DATA_BROADCAST`). UTD v2 parses these events for real-time progress tracking, alerting, and
cost attribution.

**Machine-readable SSOT:** `unified-api-contracts/unified_api_contracts/internal/events.py` — `LifecycleEventType` enum
and `REQUIRED_EVENT_FIELDS` dict.

---

## Mandatory Events — Batch Mode (11)

Emit in this order. Skipping or reordering events is a violation.

| #   | Event                      | When to Emit                                      | Required Extra Fields           |
| --- | -------------------------- | ------------------------------------------------- | ------------------------------- |
| 1   | `STARTED`                  | Immediately after config is loaded at CLI entry   | —                               |
| 2   | `VALIDATION_STARTED`       | Before dependency / preflight checks begin        | —                               |
| 3   | `VALIDATION_COMPLETED`     | After all preflight checks pass                   | `duration_ms`                   |
| 4   | `DATA_INGESTION_STARTED`   | Before reading source data (GCS, API, BQ, etc.)   | —                               |
| 5   | `DATA_INGESTION_COMPLETED` | After all source data is loaded into memory       | `duration_ms`, `rows_loaded`    |
| 6   | `PROCESSING_STARTED`       | Before domain computation / transformation begins | —                               |
| 7   | `PROCESSING_COMPLETED`     | After domain computation finishes                 | `duration_ms`, `rows`           |
| 8   | `PERSISTENCE_STARTED`      | Before writing output to GCS / BQ                 | `bucket`, `path`                |
| 9   | `PERSISTENCE_COMPLETED`    | After all output files are written                | `duration_ms`, `files_written`  |
| 10  | `STOPPED`                  | On clean, successful exit                         | `total_duration_ms`             |
| 11  | `FAILED`                   | On any unrecovered error before `STOPPED`         | `stack_trace`, `error_category` |

`FAILED` is terminal — a service that emits `FAILED` must not emit `STOPPED`. A service that emits `STOPPED` must not
have emitted `FAILED`.

---

## Mandatory Events — Live Mode (12)

Live mode adds `DATA_BROADCAST` between `PROCESSING_COMPLETED` and `PERSISTENCE_STARTED`. The remaining 11 events are
identical to batch mode.

| #   | Event                      | When to Emit                                            |
| --- | -------------------------- | ------------------------------------------------------- |
| 1   | `STARTED`                  | Same as batch                                           |
| 2   | `VALIDATION_STARTED`       | Same as batch                                           |
| 3   | `VALIDATION_COMPLETED`     | Same as batch                                           |
| 4   | `DATA_INGESTION_STARTED`   | Same as batch (or per tick-batch in streaming context)  |
| 5   | `DATA_INGESTION_COMPLETED` | Same as batch                                           |
| 6   | `PROCESSING_STARTED`       | Same as batch                                           |
| 7   | `PROCESSING_COMPLETED`     | Same as batch                                           |
| 8   | `DATA_BROADCAST`           | After processing; before writing — Pub/Sub publish step |
| 9   | `PERSISTENCE_STARTED`      | Same as batch                                           |
| 10  | `PERSISTENCE_COMPLETED`    | Same as batch                                           |
| 11  | `STOPPED`                  | Same as batch                                           |
| 12  | `FAILED`                   | Same as batch                                           |

`CONNECTION_ESTABLISHED` is a **service-specific domain event**, not a lifecycle event. It is documented in
`03-observability/live/per-service/` for the services that use it.

---

## Required Fields on Every Event

These fields are required on all events regardless of type (from `REQUIRED_EVENT_FIELDS["ALL"]` in
`unified-api-contracts/unified_api_contracts/internal/events.py`):

| Field             | Type       | Description                                                |
| ----------------- | ---------- | ---------------------------------------------------------- |
| `service_name`    | `str`      | Canonical service name (e.g. `instruments-service`)        |
| `event_type`      | `str`      | One of the `LifecycleEventType` string values              |
| `timestamp`       | `datetime` | UTC timestamp of the event                                 |
| `correlation_id`  | `str`      | UUID linking all events in one service run / shard         |
| `service_version` | `str`      | Semver string from `pyproject.toml`                        |
| `local_timestamp` | `datetime` | Wall-clock time on the host (may differ from UTC on drift) |

Additionally, per-event required fields (from `REQUIRED_EVENT_FIELDS` per event key):

| Event pattern | Extra required fields                                        |
| ------------- | ------------------------------------------------------------ |
| `FAILED`      | `stack_trace`, `error_category`                              |
| `*_COMPLETED` | `duration_ms`                                                |
| `MARKET_DATA` | `exchange_timestamp`, `local_timestamp`, `sequence_number`   |
| `EXECUTION`   | `client_order_id`, `exchange_timestamp`, `venue_response_id` |

---

## Conditional event types (live-pipeline / instruments-live / ML / strategy)

Beyond the 12 mandatory per-run lifecycle events, the workspace defines event TYPES that fire conditionally during a
service's run. They share the
`service_name / event_type / timestamp / correlation_id / service_version / local_timestamp` envelope and add typed
`metadata.details` per event.

### Instruments-live (7 codes)

Per
[`/codex/04-architecture/instruments-live-architecture.md`](/codex/04-architecture/instruments-live-architecture.md) +
[`instruments-preflight-chain.md`](/codex/04-architecture/instruments-preflight-chain.md):

| Event                                   | When                                                              |
| --------------------------------------- | ----------------------------------------------------------------- |
| `INSTRUMENTS_LIVE_TRIGGER_FIRED`        | A scheduled trigger started a refresh                             |
| `INSTRUMENTS_LIVE_TRIGGER_FAILED`       | A trigger errored                                                 |
| `INSTRUMENTS_LIVE_SOURCE_DEGRADED`      | Primary source returned degraded data; auto-switch to secondary   |
| `INSTRUMENTS_LIVE_SCHEMA_DRIFT`         | Adapter output schema diverged from canonical; circuit-broken     |
| `INSTRUMENTS_LIVE_T1_AUDIT_DISCREPANCY` | T+1 audit detected live≠batch beyond tolerance                    |
| `INSTRUMENTS_LIVE_PREFLIGHT_FAILED`     | Pre-flight detected stale upstream; trigger skipped, alert paged  |
| `INSTRUMENTS_LIVE_UPSTREAM_STALE`       | Upstream-staleness monitor early warning (no downstream fire yet) |

`PREFLIGHT_FAILED` payload:
`{asset_group, trigger_name, missing_dependencies: [{entity_type, expected_max_age, actual_age, last_seen_at}], correlation_id}`
— the `missing_dependencies` list is what the alerting rule routes on so the operator sees the named upstream blocking
the trigger.

### Live-pipeline (4 codes)

Per [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md) +
[`/codex/04-architecture/alerting-batch-live.md`](/codex/04-architecture/alerting-batch-live.md):

| Event                                 | When                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------- |
| `LIVE_PIPELINE_CANDLE_NOT_COMPUTED`   | Candle boundary fired but the downstream calculator did not produce a row |
| `LIVE_PIPELINE_REPLAY_HANDOFF_FAILED` | Replay-to-live handoff did not validate state continuity                  |
| `LIVE_PIPELINE_HOT_RELOAD_REJECTED`   | Cache-delta hot-reload found unsafe diff and refused                      |
| `LIVE_PIPELINE_UTC_MIDNIGHT_DRIFT`    | A service crossed UTC midnight without alignment                          |

### ML lifecycle (5 codes)

Per [`/codex/04-architecture/ml-experiment-lifecycle.md`](/codex/04-architecture/ml-experiment-lifecycle.md):

| Event                      | When                                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| `ML_TRAINING_FAILED`       | Training run errored; ML manifest row flipped to retired             |
| `ML_VALIDATION_FAILED`     | Out-of-sample backtest failed target metrics                         |
| `ML_MODEL_STALENESS`       | Champion model older than per-family threshold                       |
| `ML_INFERENCE_LATENCY`     | Inference path exceeded SLO                                          |
| `ML_FEATURE_INPUT_MISSING` | Required feature not available; inference falls through to safe-mode |

### Strategy hot-reload (1 code)

Per
[`/codex/04-architecture/live-strategy-config-hot-reload.md`](/codex/04-architecture/live-strategy-config-hot-reload.md):

| Event                      | When                                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| `STRATEGY_CONFIG_RELOADED` | `StrategyConfigReloader` applied a config delta; payload is the diff |

### Kill-switch bus (alerting → execution, Pub/Sub)

When alerting-service fires a `KILL_SWITCH_*` alert code, it publishes a typed `KillSwitchEvent` to the
`kill-switch-bus` Pub/Sub topic. This is a **domain event** (not a `log_event()` lifecycle event) — it does not appear
in the lifecycle event stream. Execution-service and strategy-service subscribe to this topic and auto-halt without
operator intervention.

`KillSwitchEvent` payload: `{code: AlertCode, scope: KillSwitchScope, triggered_at, correlation_id}`.

`KillSwitchScope` values: `GLOBAL` (halt all strategies), `VENUE` (halt named venue adapters only), `ARCHETYPE` (halt
named strategy archetype only). Per-code scope is validated at `AlertRule` construction time — `KILL_SWITCH_*` codes
require non-None scope; all other codes must have `kill_switch_scope=None`.

SSOTs:

- alerting-service Phase 1.C: `alerting-service/alerting_service/notifiers/router.py` (`_publish_kill_switch_event`
  helper, post-channel-dispatch wire). alerting-service@`8eda37c`.
- UAC: `unified_api_contracts.canonical.crosscutting.alerting.codes.KillSwitchScope` (enum).
- Tests: `alerting-service/tests/integration/test_kill_switch_publisher_hook.py` (5 integration tests).
- Per-code scope mapping: `/codex/15-runbooks/alerting/alert-code-taxonomy.md` § "Kill-switch family".

### Per-instrument progress (silent-success-with-zero-output detector)

Adapters that fan out across instruments MUST emit per-instrument progress events with row counts so a clean
`STARTED → STOPPED` pair with no intermediate `INSTRUMENT_PROCESSED` events surfaces as broken. Reference incident
2026-05-05: 21 MDPS VMs emitted clean lifecycle but produced 1440 NaN OHLC bars/day for years — absence of intermediate
progress events with row counts was the silent-success signal that should have caught it.

---

## State Machine — Valid Transitions

```
                     ┌─────────────────────────────────┐
                     │            FAILED (terminal)     │
                     └──────────────┬──────────────────┘
                                    │ (any state may transition here)
                                    │
[START] ──► STARTED
               │
               ▼
        VALIDATION_STARTED
               │
               ▼
        VALIDATION_COMPLETED
               │
               ▼
        DATA_INGESTION_STARTED
               │
               ▼
        DATA_INGESTION_COMPLETED
               │
               ▼
        PROCESSING_STARTED
               │
               ▼
        PROCESSING_COMPLETED
               │
               ├──► (live only) DATA_BROADCAST
               │                     │
               │                     ▼
               └──────────► PERSISTENCE_STARTED
                                     │
                                     ▼
                            PERSISTENCE_COMPLETED
                                     │
                                     ▼
                               STOPPED (terminal)
```

Any state may transition directly to `FAILED`. No other backward or skip transitions are valid.

---

## setup_events() Requirement

`setup_events()` (or the `setup_service()` wrapper from `unified_trading_services`) **must be called at the CLI
entrypoint** before the first `log_event()` call. It registers the event sink (GCS, Pub/Sub, or mock) and binds the
`service_name` and `mode` for the process lifetime.

Calling `log_event()` before `setup_events()` raises a runtime error in non-test environments.

---

## Code Example

```python
from unified_trading_library.events import setup_events, log_event

# At CLI entrypoint (before any log_event calls):
setup_events(service_name="instruments-service", mode="batch")

# --- batch run lifecycle ---
log_event("STARTED", metadata={"correlation_id": run_id, "service_version": "1.4.0"})
log_event("VALIDATION_STARTED", metadata={"correlation_id": run_id})
log_event("VALIDATION_COMPLETED", metadata={"correlation_id": run_id, "duration_ms": 120.5})
log_event("DATA_INGESTION_STARTED", metadata={"correlation_id": run_id, "source": "tardis-gcs"})
log_event("DATA_INGESTION_COMPLETED", metadata={"correlation_id": run_id, "duration_ms": 4200.0, "rows_loaded": 950000})
log_event("PROCESSING_STARTED", metadata={"correlation_id": run_id})
log_event("PROCESSING_COMPLETED", metadata={"correlation_id": run_id, "duration_ms": 8100.0, "rows": 950000})
log_event("PERSISTENCE_STARTED", metadata={"correlation_id": run_id, "bucket": "uts-features", "path": "cefi/2026-03-04/"})
log_event("PERSISTENCE_COMPLETED", metadata={"correlation_id": run_id, "duration_ms": 320.0, "files_written": 12})
log_event("STOPPED", metadata={"correlation_id": run_id, "total_duration_ms": 13000.0})

# On any unhandled error (instead of STOPPED):
import traceback
log_event("FAILED", metadata={
    "correlation_id": run_id,
    "stack_trace": traceback.format_exc(),
    "error_category": "NETWORK",
})
```

### UTS v2.2.0+ pattern (with GCSEventSink):

```python
from unified_trading_services import GCSEventSink, setup_service, log_event

setup_service(
    service_name="instruments-service",
    mode="batch",
    sink=GCSEventSink(
        project_id=config.gcp_project_id,
        bucket=config.events_bucket,
        service_name="instruments-service",
    ),
)
# log_event() calls are identical to the example above
```

---

## GCS Event Storage Path

Events written by `GCSEventSink` are stored at:

```
events/{service_name}/{YYYY-MM-DD}/events.jsonl
```

Each line is a JSON object conforming to `LifecycleEventEnvelope` from
`unified-api-contracts/unified_api_contracts/internal/events.py`.

---

## UI Auth Events (codex-canonical, v0.2.26+)

These events are emitted by browser clients via `unified-trading-ui-auth` `emitAuthEvent()` and relay to `log_event()`
through the backend `POST /events` endpoint (`make_events_relay_router()` in UTL). They are **not subject to lifecycle
ordering rules** and are never required by QG checks.

| Event Name        | When to Emit                                                      | Severity |
| ----------------- | ----------------------------------------------------------------- | -------- |
| `LOGIN_INITIATED` | OAuth redirect started (user clicked login)                       | INFO     |
| `LOGIN_SUCCESS`   | OAuth callback completed, token stored                            | INFO     |
| `LOGIN_FAILURE`   | OAuth callback error or token validation failed (UI-side only)    | WARNING  |
| `LOGOUT`          | User-initiated logout                                             | INFO     |
| `SESSION_EXPIRED` | Token TTL exceeded; detected via sessionStorage sentinel on mount | WARNING  |

> `LOGIN_FAILURE` is distinct from `AUTH_FAILURE`: `AUTH_FAILURE` covers server-side API key validation failures;
> `LOGIN_FAILURE` covers UI-side OAuth errors.

---

## API Request Audit Events (codex-canonical, v0.2.26+)

Emitted by `RequestAuditMiddleware` from `unified-trading-library[api]`. Add to FastAPI apps with
`app.add_middleware(RequestAuditMiddleware)`. Infrastructure paths are excluded from audit (`/health`, `/readiness`,
`/metrics`, `/docs`, `/openapi.json`, `/favicon.ico`, `/redoc`).

| Event Name             | When to Emit                        | Severity              | Key Details                                   |
| ---------------------- | ----------------------------------- | --------------------- | --------------------------------------------- |
| `API_REQUEST_RECEIVED` | On ingress, before handler executes | INFO                  | `method`, `path`, propagated correlation_id   |
| `API_RESPONSE_SENT`    | On egress, after handler completes  | INFO (>=400: WARNING) | `method`, `path`, `status_code`, `latency_ms` |

---

## Security / Audit Events

`AUTH_FAILURE`, `SECRET_ACCESSED`, and `CONFIG_CHANGED` are also members of `LifecycleEventType` but are **security
audit events**, not lifecycle events. They are documented in `07-security/audit-logging.md` and may be emitted at any
point in the lifecycle (not subject to the ordering rules above).

---

## Security / Resource Monitoring Events

These events are codex-canonical and may be emitted outside the normal lifecycle sequence. They cover runtime health,
security anomalies, and infrastructure boundary conditions.

| Event Name                 | When to Emit                                              | Severity |
| -------------------------- | --------------------------------------------------------- | -------- |
| `MEMORY_THRESHOLD_REACHED` | Process memory exceeds configured threshold (default 85%) | WARNING  |
| `DISK_THRESHOLD_REACHED`   | Disk usage exceeds configured threshold                   | WARNING  |
| `CPU_THRESHOLD_REACHED`    | CPU usage exceeds configured threshold                    | WARNING  |
| `AUTHENTICATION_FAILED`    | Service-to-service auth check failed                      | ERROR    |
| `AUTHORISATION_DENIED`     | Principal lacks required permissions                      | ERROR    |
| `RATE_LIMIT_EXCEEDED`      | Inbound or outbound rate limit hit                        | WARNING  |
| `CIRCUIT_OPEN`             | Circuit breaker tripped after repeated failures           | ERROR    |
| `CIRCUIT_HALF_OPEN`        | Circuit breaker entering probe phase after cooldown       | WARNING  |
| `CIRCUIT_CLOSED`           | Circuit breaker recovered                                 | INFO     |
| `DEPENDENCY_UNAVAILABLE`   | Required upstream service/resource unreachable            | ERROR    |
| `SECURITY_ALERT`           | Generic security anomaly detected                         | CRITICAL |

> All events in this table are codex-canonical and enforced by QG rg-checks. Use `log_event(event_name, ...)` from
> `unified_trading_library.events`.

---

## Lifecycle Event QG Enforcement

Every deployable entrypoint **must** emit `STARTED`, `STOPPED`, and `FAILED`.

- `STARTED` — emitted immediately after config is loaded, before any work begins.
- `STOPPED` — emitted on clean, successful exit (mutually exclusive with `FAILED`).
- `FAILED` — emitted on any unrecovered error; must not be followed by `STOPPED`.

**UTL ServiceBootstrap handles these automatically.** Services using `ServiceBootstrap` (which is all of them — enforced
by QG STEP 5.61) do NOT emit these manually. The QG check verifies `ServiceBootstrap(` usage in the service source, not
the presence of individual `log_event("STARTED")` calls.

UIs emit browser telemetry separately (via the frontend observability pipeline) and are not subject to this QG check.

---

## Related

- Machine-readable schema: `unified-api-contracts/unified_api_contracts/internal/events.py`
- Security audit events: `07-security/audit-logging.md`
- Alerting rules derived from lifecycle events: `03-observability/alerting.md`
- Coordination events (service-to-service): `03-observability/coordination-events.md`
- Data flow map: `04-architecture/data-flow-map.md`
- Cursor rule: `.cursor/rules/core/event-logging.mdc`
- Observability compliance fields: `.cursor/rules/misc/observability-compliance.mdc`
