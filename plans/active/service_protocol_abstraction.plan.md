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

### P0 — ABCs + ServiceMode in UCI (abstractions.py + protocol.py)

- [ ] `p0-service-mode` — Add `ServiceMode` enum to `unified_cloud_interface/protocol.py` (new file)
- [ ] `p0-data-sink-abc` — Add `DataSink` ABC with `write()` + `write_batch()`
- [ ] `p0-data-source-abc` — Add `DataSource` ABC with `read()` + `list_partitions()`
- [ ] `p0-event-bus-abc` — Add `EventBus` ABC (sync + async publish)
- [ ] `p0-protocol-config` — Add `ProtocolConfig` dataclass that reads PROTOCOL\_\* env vars
- [ ] `p0-init-exports` — Export all new ABCs from `__init__.py`

### P1 — Concrete Implementations in UCI providers

- [ ] `p1-gcs-data-sink` — `GCSDataSink(DataSink)` backed by `GCSStorageClient`; writes parquet/json/csv to configured bucket+prefix
- [ ] `p1-s3-data-sink` — `S3DataSink(DataSink)` backed by `S3StorageClient`
- [ ] `p1-bq-data-sink` — `BigQueryDataSink(DataSink)` backed by `GCPAnalyticsClient`; for live streaming inserts
- [ ] `p1-athena-data-sink` — `AthenaDataSink(DataSink)` backed by `AWSAnalyticsClient`
- [ ] `p1-local-data-sink` — `LocalDataSink(DataSink)` backed by `LocalStorageProvider`
- [ ] `p1-pubsub-event-bus` — `PubSubEventBus(EventBus)` backed by `PubSubQueueClient`
- [ ] `p1-sqs-event-bus` — `SQSEventBus(EventBus)` backed by `SQSQueueClient`
- [ ] `p1-local-event-bus` — `LocalEventBus(EventBus)` backed by `LocalQueueProvider`

### P2 — Factory Integration (factory.py)

- [ ] `p2-get-service-mode` — `get_service_mode()` reads `SERVICE_MODE` env var; fails loud if missing
- [ ] `p2-get-data-sink` — `get_data_sink()` reads `PROTOCOL_DATA_SINK_BACKEND` → routes to correct impl
- [ ] `p2-get-data-source` — `get_data_source()` symmetric to data sink
- [ ] `p2-get-event-bus` — `get_event_bus()` reads `PROTOCOL_EVENT_BUS_BACKEND` → routes to correct impl
- [ ] `p2-protocol-cache` — cache protocol client instances (same as storage/secret caches)

### P3 — Deployment Config Generation (deployment-service)

- [ ] `p3-config-schema` — Define `protocol-config-schema.yaml` in deployment-service/configs/; documents all PROTOCOL\_\* keys per service
- [ ] `p3-gen-batch-configs` — Generate `configs/services/<svc>/batch.env` with PROTOCOL\_\* vars for all batch services
- [ ] `p3-gen-live-configs` — Generate `configs/services/<svc>/live.env` with PROTOCOL\_\* vars for all live services
- [ ] `p3-bootstrap-injects` — Deployment bootstrap scripts inject SERVICE*MODE + PROTOCOL*\* vars when provisioning Cloud Run / ECS services
- [ ] `p3-terraform-vars` — Terraform modules receive PROTOCOL\_\* vars as input vars; pass to service container env

### P4 — Service Refactors (high priority: services with worst violations)

- [ ] `p4-instruments-service` — Refactor `cloud_instrument_storage.py`: replace `CloudTarget` + `upload_to_gcs_batch` with `get_data_sink()`
- [ ] `p4-market-data-service` — Refactor any `CloudTarget`/`StandardizedDomainCloudService` usage
- [ ] `p4-features-service` — Refactor feature storage to use `get_data_sink()` for batch feature writes
- [ ] `p4-ml-training` — Refactor `etl_gcs_to_bigquery.py` to use `get_data_sink()` + `get_data_source()`
- [ ] `p4-deployment-api` — Verify deployment-api/cache.py is fully via UCI (done in #2a); verify event bus
- [ ] `p4-utl-cloud-layer` — Remove `StandardizedDomainCloudService`, `CloudTarget` from UTL public API; replace with `get_data_sink()` facade
- [ ] `p4-all-services` — Audit all remaining services: grep for `CloudTarget|gcs_bucket|bigquery_dataset|upload_to_gcs`

### P5 — Quality Gate

- [ ] `p5-quality-gate` — Add STEP 5.11 to quality-gates-service-template.sh:
  ```bash
  # Block protocol-leaking symbols in service code
  if rg -l "CloudTarget|upload_to_gcs|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
      --type py --glob '!.venv*' --glob '!tests' .; then
    echo "FAIL: Service contains protocol-specific symbols. Use get_data_sink() / get_event_bus() instead."
    exit 1
  fi
  ```
- [ ] `p5-codex-update` — Document intent-level API pattern in `unified-trading-codex/06-coding-standards/`

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
