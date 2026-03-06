# Plan: Service Protocol Abstraction (Intent-Level APIs)

**ID:** service_protocol_abstraction
**Status:** active
**Day:** 2–4 (runs alongside #2a)
**Scope:** UCI (T0), UTL (T1), all services
**Prerequisite:** uci_cloud_abstraction_complete.plan.md (P0–P1 must be done first)

---

## Problem

Services know too much about cloud protocols. `cloud_instrument_storage.py` is the canonical example:

- Directly names `gcs_bucket`, `bigquery_dataset`, `bigquery_location`
- Calls `upload_to_gcs_batch()` — GCS-specific
- Constructs `CloudTarget` — GCP-specific dataclass
- Has conditional logic: "batch = GCS, live = BigQuery"

This means changing cloud provider (or even just resource names) requires touching every service.
The same problem exists in every service that stores, publishes, or queries data.

## Target Architecture

```
Service code:       data_sink.write(df, partition={"day": date_str})
                    event_bus.publish("instruments.updated", payload)
                    ← mode fixed at startup from SERVICE_MODE env var
                    ← zero knowledge of GCS/S3/BigQuery/PubSub/SQS

Protocol Router:    reads PROTOCOL_DATA_SINK_BACKEND, PROTOCOL_DATA_SINK_BUCKET, etc.
                    maps (service_id, mode, intent) → (UCI client + resource params)
                    ← all config injected by deployment service

UCI (T0):           returns concrete GCS/S3/BigQuery/local clients
                    ← driven by CLOUD_PROVIDER env var

Deployment:         generates per-service PROTOCOL_* + SERVICE_MODE env vars per environment
                    ← single source of truth for all protocol decisions
```

**The invariant:** A service file must never contain any of these words: `gcs`, `gcp`, `bigquery`, `s3`,
`pubsub`, `redis`, `cloudtarget`, `bucket`, `dataset`, `upload_to_gcs`. Those words exist only in UCI
providers, the protocol router, and deployment config.

---

## Design Details

### ServiceMode

```python
class ServiceMode(str, Enum):
    LIVE = "live"    # real-time pipeline: low-latency, streaming protocols
    BATCH = "batch"  # batch pipeline: high-throughput, bulk storage protocols
```

Injected once per service deployment: `SERVICE_MODE=live` or `SERVICE_MODE=batch`.
A service is NEVER running both simultaneously — this is a deployment-level hard constraint.

### Intent ABCs

```python
class DataSink(Protocol):
    """Write structured data (DataFrame, bytes, dict)."""
    def write(self, data: pd.DataFrame | bytes | dict[str, object],
              partition: dict[str, str] | None = None) -> str: ...
    def write_batch(self, items: list[tuple[dict[str, str], pd.DataFrame | bytes]]) -> list[str]: ...

class DataSource(Protocol):
    """Read structured data."""
    def read(self, partition: dict[str, str] | None = None) -> pd.DataFrame: ...
    def list_partitions(self) -> list[dict[str, str]]: ...

class EventBus(Protocol):
    """Publish events / messages."""
    def publish(self, event_type: str, payload: bytes) -> None: ...
    async def publish_async(self, event_type: str, payload: bytes) -> None: ...

class ConfigStore(Protocol):
    """Load / save service configuration and secrets."""
    def get(self, key: str) -> str: ...
    def set(self, key: str, value: str) -> None: ...

# ⚠️ IMPORTANT: ConfigStore is NOT added to unified-cloud-interface (UCI).
# Per cursor-rules/config/config-store-usage.mdc, ConfigStore lives in
# unified_trading_services (UTL T1). Import as:
#   from unified_trading_services import ConfigStore
# NEVER: from unified_cloud_interface import ConfigStore
```

### Deployment-Injected Config Schema

Per-service env vars injected by deployment-service:

```bash
# Mode (live or batch) — hardened per deployment
SERVICE_MODE=batch

# Data sink backend for this service in this mode
PROTOCOL_DATA_SINK_BACKEND=gcs         # gcs | s3 | bigquery | local
PROTOCOL_DATA_SINK_BUCKET=instruments-cefi-batch
PROTOCOL_DATA_SINK_PATH_PREFIX=instrument_availability/by_date
PROTOCOL_DATA_SINK_FORMAT=parquet      # parquet | json | csv

# Event bus backend
PROTOCOL_EVENT_BUS_BACKEND=pubsub      # pubsub | sqs | local
PROTOCOL_EVENT_BUS_TOPIC_PREFIX=instruments

# Config store backend (inherits from UCI SECRET_PROVIDER by default)
PROTOCOL_CONFIG_STORE_BACKEND=secretmanager  # secretmanager | ssm | local
```

### Factory Functions (extend UCI factory.py)

```python
def get_data_sink(name: str | None = None) -> DataSink:
    """Return DataSink backed by PROTOCOL_DATA_SINK_BACKEND config."""

def get_data_source(name: str | None = None) -> DataSource:
    """Return DataSource backed by PROTOCOL_DATA_SINK_BACKEND config."""

def get_event_bus(name: str | None = None) -> EventBus:
    """Return EventBus backed by PROTOCOL_EVENT_BUS_BACKEND config."""

def get_service_mode() -> ServiceMode:
    """Read SERVICE_MODE env var. Raises if not set (services must always declare mode)."""
```

---

## Todos

### Completed (Session 3, 2026-03-05)

All P0 and P2 todos are done. P1 concrete implementations are partially done — cloud-agnostic
`StorageDataSink`/`StorageDataSource` cover GCS+S3 (unified, not split by provider); `QueueEventBus`
covers PubSub+SQS; `LocalDataSink`, `LocalDataSource`, `LocalEventBus` are implemented. Analytics-backed
sinks (`BigQueryDataSink`, `AthenaDataSink`) remain pending in P1.

Key implementation note: the plan named `GCSDataSink`/`S3DataSink` separately, but the implementation
correctly uses a single cloud-agnostic `StorageDataSink(storage: StorageClient, ...)` — the `StorageClient`
backend (GCS vs S3) is injected by the factory. Same pattern for `QueueEventBus`.

### P0 — ABCs + ServiceMode in UCI (abstractions.py + protocol.py)

- [x] `p0-service-mode` — Add `ServiceMode` enum to `unified_cloud_interface/protocol.py` (new file)
- [x] `p0-data-sink-abc` — Add `DataSink` ABC with `write()` + `write_batch()`
- [x] `p0-data-source-abc` — Add `DataSource` ABC with `read()` + `list_partitions()`
- [x] `p0-event-bus-abc` — Add `EventBus` ABC (sync + async publish)
- [x] `p0-protocol-config` — Add `ProtocolConfig` dataclass that reads PROTOCOL\_\* env vars
- [x] `p0-init-exports` — Export all new ABCs from `__init__.py`

### P1 — Concrete Implementations in UCI providers

- [x] `p1-gcs-data-sink` — Implemented as `StorageDataSink(DataSink)` in `providers/protocol_impls.py`; cloud-agnostic, backed by any `StorageClient` (GCS or S3); writes parquet/json/bytes to configured bucket+prefix
- [x] `p1-s3-data-sink` — Covered by `StorageDataSink` (same class, S3StorageClient injected by factory)
- [x] `p1-bq-data-sink` — `BigQueryDataSink(DataSink)` in `providers/protocol_impls.py`; backed by `AnalyticsClient.insert_rows()` (implemented in `GCPAnalyticsClient`); `PROTOCOL_DATA_SINK_BACKEND=bigquery` routes factory here; `PROTOCOL_ANALYTICS_DATASET` + `PROTOCOL_DATA_SINK_TABLE_PREFIX` configure target table
- [x] `p1-athena-data-sink` — `AthenaDataSink(DataSink)` in `providers/protocol_impls.py`; backed by any `StorageClient` (S3); writes Glue-compatible parquet; `PROTOCOL_DATA_SINK_BACKEND=athena` routes factory here
- [x] `p1-local-data-sink` — `LocalDataSink(DataSink)` implemented in `providers/protocol_impls.py`
- [x] `p1-pubsub-event-bus` — Implemented as `QueueEventBus(EventBus)` backed by `QueueClient`; covers PubSub and SQS
- [x] `p1-sqs-event-bus` — Covered by `QueueEventBus` (same class, SQSQueueClient injected by factory)
- [x] `p1-local-event-bus` — `LocalEventBus(EventBus)` implemented in `providers/protocol_impls.py`

### P2 — Factory Integration (factory.py)

- [x] `p2-get-service-mode` — `get_service_mode()` reads `SERVICE_MODE` env var; fails loud if missing
- [x] `p2-get-data-sink` — `get_data_sink()` reads `PROTOCOL_DATA_SINK_BACKEND` → routes to correct impl
- [x] `p2-get-data-source` — `get_data_source()` symmetric to data sink
- [x] `p2-get-event-bus` — `get_event_bus()` reads `PROTOCOL_EVENT_BUS_BACKEND` → routes to correct impl
- [x] `p2-protocol-cache` — `_data_sink_cache`, `_data_source_cache`, `_event_bus_cache` added to `factory.py` with `Lock` guards; `use_cache=True` param on all three factory functions; `clear_client_caches()` updated to include protocol caches

### P3 — Deployment Config Generation (deployment-service)

- [x] `p3-config-schema` — `deployment-service/configs/protocol-config-schema.yaml` — documents all PROTOCOL_* keys including new `PROTOCOL_DATA_SINK_TABLE_PREFIX` (for BigQueryDataSink) and `athena` backend value; per-service matrix section lists which vars each service uses
- [x] `p3-gen-batch-configs` — `configs/services/<svc>/batch.env` exist for all 11 batch services (instruments, features-*, market-data-processing, ml-training, strategy, pnl, position-balance-monitor); new files added for features-volatility-service, features-delta-one-service, features-cross-instrument-service
- [ ] `p3-gen-live-configs` — live.env files not yet created for live services (market-tick-data, execution, ml-inference, risk)
- [ ] `p3-bootstrap-injects` — Deployment bootstrap scripts need updating to inject SERVICE_MODE + PROTOCOL_* vars when provisioning Cloud Run / ECS
- [ ] `p3-terraform-vars` — Terraform modules receive PROTOCOL\_\* vars as input vars; pass to service container env

### P4 — Service Refactors (high priority: services with worst violations)

- [x] `p4-instruments-service` — `cloud_data_provider.py` uses `get_data_source(routing_key=category.lower())` (done in prior session); `cloud_instrument_storage.py` still present but deprecated; main read/write path is UCI
- [ ] `p4-market-data-service` — `CloudTarget`/`StandardizedDomainCloudService` usage still present; P4 backlog
- [x] `p4-features-service` — features-volatility, features-delta-one, features-onchain: refactored to `get_data_sink(routing_key=category.lower())` / `get_data_source()` / UCI `StorageClient`; `get_output_gcs_buckets()` / `get_gcs_buckets()` removed; `from google.cloud.storage import Blob` removed from features-cross-instrument-service
- [ ] `p4-ml-training` — `etl_gcs_to_bigquery.py` still uses BigQuery directly; P4 backlog
- [x] `p4-deployment-api` — `cache.py` fully UCI (session #2a); event bus uses `get_queue_client()` via UCI
- [ ] `p4-utl-cloud-layer` — `StandardizedDomainCloudService` in UTL has deprecation warnings; removal pending; `CloudTarget` still referenced by many services; P4 backlog
- [ ] `p4-all-services` — Remaining services (execution, market-data-processing, risk, strategy) still have `CloudTarget|gcs_bucket` references; P5 quality gate will catch them

### P5 — Quality Gate

- [x] `p5-quality-gate` — STEP 5.11 (blocks `CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService`) already added as hard-fail in prior sessions to `quality-gates-service-template.sh`, `quality-gates-codex-compliance-snippet.sh`, `quality-gates-template.sh`; STEP 5.12 also added (see session 3 notes). Remaining service violations are tracked in P4.
- [x] `p5-codex-update` — Document intent-level API pattern in `unified-trading-codex/06-coding-standards/` (how to use `get_data_sink`, `get_event_bus`, routing_key convention); `intent-level-api-pattern.md` created and `README.md` updated in this session.

---

## Acceptance Criteria

1. `grep -r "gcs_bucket\|bigquery_dataset\|CloudTarget\|upload_to_gcs\|StandardizedDomainCloudService" --include="*.py" services/` → 0 results
2. `instruments-service` stores parquet via `get_data_sink().write(df)` — zero GCS knowledge
3. Setting `PROTOCOL_DATA_SINK_BACKEND=s3` + `CLOUD_PROVIDER=aws` routes ALL data writes to S3 with no code changes
4. Setting `PROTOCOL_DATA_SINK_BACKEND=local` routes ALL writes to local filesystem (test mode)
5. All PROTOCOL\_\* env vars documented in `deployment-service/configs/protocol-config-schema.yaml`
6. Quality gate STEP 5.11 blocks protocol-leaking symbols in service CI

---

## Notes

- `get_service_mode()` is **the only** ENV READ allowed in service startup (besides UCI factory bootstrap reads)
- Mode is a deployment-time decision: batch jobs always BATCH, streaming services always LIVE
- The `DataSink` format (parquet/json/csv) is config-driven, NOT hardcoded in service
- Path/key structure (partition layout) IS defined by service code: service knows its domain structure
- For multi-bucket scenarios (instruments-service routes by `market_category`), service passes a `routing_key` param; deployment config maps routing_key → bucket name
