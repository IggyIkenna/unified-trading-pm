---
doc_type: codex-ssot
title: Cloud-Agnostic Migration
summary:
  All cloud I/O (storage/secrets/queues) goes through unified-cloud-interface Tier-0 factories
  (get_storage_client/get_secret_client/get_queue_client); CLOUD_PROVIDER switches gcp/aws/local at runtime; Cloud*
  naming rule, before/after migration examples, and the Phase-0 direct-import ban.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [cloud-agnostic, uci, storage, secrets, migration, gcp, aws]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/07-security/secrets-management.md,
    /codex/06-coding-standards/pre-sprint-baseline.md,
  ]
created: 2026-03-27
authoritative_for: [cloud-agnostic application-code migration to UCI factories]
referenced_by:
  [
    /codex/04-architecture/seamless-cloud-switch.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/05-infrastructure/README.md,
    /codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md,
    /plans/epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md,
  ]
owner:
last_reviewed: 2026-08-11
code_refs:
---

# Cloud-Agnostic Migration

## TL;DR

All cloud I/O (storage, secrets, queues) must go through the abstraction layer provided by `unified-cloud-interface`
(UCI, Tier 0). Direct imports of `google.cloud.*` or `boto3` in application source code are a Phase 0 violation. The
`CLOUD_PROVIDER` environment variable switches the active provider at runtime without code changes.

**Naming rule:** Public-facing protocols and interface class names use the `Cloud*` prefix. Provider implementations
inside `providers/gcp.py` and `providers/aws.py` may use cloud-specific prefixes (`GCSStorageClient`,
`S3StorageClient`), but these must never appear in public re-exports or abstract class names.

See also: `04-architecture/tier-and-import-architecture.md` § Naming Conventions (lines 91–96) for the canonical
one-liner statement of this rule.

---

## The Abstraction Layer

> **⛔ REPO + CLASS NAMES CORRECTED 2026-07-30.** The `unified-cloud-interface` (UCI) repo no longer exists — the
> cloud-agnostic layer folded into **unified-trading-library (UTL)** at `unified_trading_library/cloud_interface/`. The
> protocol classes were also renamed: they carry **no `Cloud*` prefix**. The factory functions and the `CLOUD_PROVIDER`
> env-var contract are unchanged and still correct.

UTL's `cloud_interface` is the Tier-0 cloud-agnostic layer. It exposes factory functions that return cloud-agnostic
abstract implementations (`unified_trading_library/cloud_interface/abstractions.py`):

| Factory function       | Returns (actual class) | What it does                                               |
| ---------------------- | ---------------------- | ---------------------------------------------------------- |
| `get_storage_client()` | `StorageClient`        | Read/write blobs (GCS bucket or S3)                        |
| `get_secret_client()`  | `SecretClient`         | Access secrets (GCP Secret Manager or AWS Secrets Manager) |
| `get_queue_client()`   | `QueueClient`          | Publish/subscribe (Pub/Sub or SQS/SNS)                     |

Also present in the same module: `AsyncStorageClient`, `CachingSecretClient`, `PubSubClient`, `AnalyticsClient`.

```python
from unified_trading_library import get_storage_client, get_secret_client
```

All service code must import from `unified_trading_library`. No other import path for cloud I/O is acceptable in
non-provider source files — direct `google.cloud` / `boto3` imports are a QG-enforced ban.

---

## CLOUD_PROVIDER Environment Variable

The `CLOUD_PROVIDER` env var controls which provider implementation is instantiated:

| Value   | Storage backend              | Secrets backend       |
| ------- | ---------------------------- | --------------------- |
| `gcp`   | GCS (`google.cloud.storage`) | GCP Secret Manager    |
| `aws`   | S3 (`boto3`)                 | AWS Secrets Manager   |
| `local` | Local filesystem             | Environment variables |

`CLOUD_PROVIDER` is read once at process start. GCP is the primary production provider; AWS is secondary. The `local`
provider is for development and unit tests only.

**DeFi services (`features-service`, `execution-service`, `strategy-service`) — GCP cutover complete, 2026-08-10.**
These three ran as live AWS ECS Fargate tasks (`uts-defi-prod`, `ap-northeast-1`) even though their real data always
lived in GCS (`central-element-323112`) — the AWS S3 counterparts were empty, driving ongoing cross-cloud egress cost.
This superseded the mid-2026-05 "DeFi client mandate on AWS" placement
(`/plans/archive/2026_05/aws_migration_defi_first_2026_05_07.md`), whose data-and-compute-co-located-on-AWS premise was
never completed. All 3 services are now deployed to GCP Cloud Run (`asia-northeast1`), confirmed healthy against the
real, populated GCS buckets; AWS ECS compute for all 3 is scaled to `desiredCount=0` (`uts-strategy-service-prod`'s ECS
service definition additionally deleted). Full AWS `uts-defi-prod` cluster teardown is pending a multi-day post-cutover
stability window, not yet executed as of this note. See `/plans/active/defi_compute_gcp_migration_2026_08_08.md` for the
full cutover record and current decommission status.

This env var is the **only** acceptable way to inject cloud provider choice. Never branch on
`os.getenv("CLOUD_PROVIDER")` in application code — the factory functions handle this.

---

## Naming Convention

### Protocols and Abstract Classes

> **⛔ Superseded 2026-07-30 — the `Cloud*` prefix is NOT the shipped convention.** The real protocol/ABC names in
> `unified_trading_library/cloud_interface/abstractions.py` are unprefixed (`StorageClient`, `SecretClient`,
> `QueueClient`, `PubSubClient`, `AnalyticsClient`, `StorageBucket`, `StorageBlob`). The example below shows the
> ORIGINALLY-PROPOSED naming and is retained only to explain the provider-vs-protocol split that follows; do not name
> new classes `Cloud*` to match it.

```python
# Illustrative only — the shipped class is `StorageClient`, without the Cloud* prefix.
class CloudStorageClient(Protocol):
    def read(self, path: str) -> bytes: ...
    def write(self, path: str, data: bytes) -> None: ...

class CloudModelArtifactStore(Protocol):
    def save(self, model: object, path: str) -> None: ...
    def load(self, path: str) -> object: ...

class CloudEventSink(Protocol):
    def emit(self, event: str, metadata: dict[str, str]) -> None: ...
```

### Provider Implementations — cloud-specific prefix in `providers/` only

```python
# CORRECT — implementation in providers/gcp.py uses GCS* prefix
class GCSStorageClient:
    def read(self, path: str) -> bytes: ...

# CORRECT — implementation in providers/aws.py uses S3* prefix
class S3StorageClient:
    def read(self, path: str) -> bytes: ...
```

### Forbidden in public re-exports and abstract classes

```python
# WRONG — cloud-specific prefix in protocol
class GCSModelArtifactStore(Protocol): ...   # rename to CloudModelArtifactStore

# WRONG — cloud-specific prefix in __init__.py re-export
from .providers.gcp import GCSStorageClient as StorageClient  # do not re-export as public API
```

---

## Migration Guide — Before / After

### Storage reads and writes

```python
# BEFORE (direct GCS import — Phase 0 violation)
from google.cloud import storage
client = storage.Client(project="my-project")
bucket = client.bucket("my-bucket")
blob = bucket.blob("path/to/file.parquet")
blob.upload_from_string(data)

# AFTER (cloud-agnostic via UCI)
from unified_cloud_interface import get_storage_client
storage_client = get_storage_client()
storage_client.write("gs://my-bucket/path/to/file.parquet", data)
```

### Secret access

```python
# BEFORE (direct GCP Secret Manager import — Phase 0 violation)
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project}/secrets/{secret_name}/versions/latest"
response = client.access_secret_version(name=name)
api_key = response.payload.data.decode("utf-8")

# AFTER (cloud-agnostic via UCI)
from unified_cloud_interface import get_secret_client
api_key = get_secret_client().access_secret("tardis-api-key")
```

### Pub/Sub message publishing

```python
# BEFORE (direct Pub/Sub import — Phase 0 violation)
from google.cloud import pubsub_v1
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)
publisher.publish(topic_path, data=message_bytes)

# AFTER (cloud-agnostic via UCI or UTL GCSEventSink/PubSubEventSink)
from unified_trading_library import PubSubEventSink
sink = PubSubEventSink(project_id=config.gcp_project_id, topic=config.events_topic)
sink.emit("DATA_BROADCAST", metadata={"messages_published": 100})
```

---

## ModelArtifactStore — T0 Protocol, T3 Concrete Implementation

`ModelArtifactStore` is a pure abstract protocol living at Tier 0. The concrete implementation `CloudModelArtifactStore`
lives in `unified-domain-client` (T3) and uses `get_storage_client()` from UCI (T0). ML services (T4) import the T0
protocol only; the concrete implementation is injected at startup via dependency injection.

```python
# ML service (T4) — imports T0 protocol only
from unified_api_contracts.internal import ModelArtifactStore

class MyInferenceService:
    def __init__(self, artifact_store: ModelArtifactStore) -> None:
        self._store = artifact_store

# CLI entrypoint — injects T3 concrete implementation
from unified_domain_client import CloudModelArtifactStore
service = MyInferenceService(artifact_store=CloudModelArtifactStore(...))
```

---

## Phase 0 Detection

The Phase 0 baseline check (see `06-coding-standards/pre-sprint-baseline.md`) flags direct cloud imports with:

```bash
rg "from google\.cloud|import boto3" --type py \
  --glob '!.venv*' --glob '!providers' <source_dir>/
```

Zero results are required to pass Phase 0. The `--glob '!providers'` exclusion permits cloud imports inside
`providers/gcp.py` and `providers/aws.py` — nowhere else.

---

## Related

- Tier architecture and `Cloud*` naming rule: `04-architecture/tier-and-import-architecture.md` § Naming Conventions
- Secrets management detail: `07-security/secrets-management.md`
- Cursor rule: `.cursor/rules/core/cloud-agnostic.mdc`
- Phase 0 baseline: `06-coding-standards/pre-sprint-baseline.md`
