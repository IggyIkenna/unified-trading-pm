# GCS Object Operations — Canonical Pattern

**SSOT for per-object copy / delete / describe in migration and batch scripts.**

## Rule

Use `unified_trading_library.cloud_interface.gcs_copy_object` / `gcs_delete_object` / `gcs_describe_object`
instead of spawning `gcloud` or `gsutil` subprocesses for GCS object-level operations.

```python
from unified_trading_library.cloud_interface import (
    gcs_copy_object,
    gcs_delete_object,
    gcs_describe_object,
)

gcs_copy_object("gs://src-bucket/path/file.parquet", "gs://dst-bucket/new/path.parquet")
gcs_delete_object("gs://src-bucket/path/old.parquet")
meta = gcs_describe_object("gs://bucket/path/file.parquet")  # BlobMetadata | None
if meta:
    print(meta.size, meta.crc32c)
```

## Why

`gcloud`/`gsutil` CLI spawns cost **~500ms per call** (subprocess + Python interpreter startup + GCP auth).
At workers=32 in a `ThreadPoolExecutor`, 5 subprocess calls per parquet limits throughput to **~34 parquets/min**.

The UTL helpers use the `google-cloud-storage` REST API (~50–200ms per call) and release the Python GIL
(IO-bound), so threads run in true parallel. Measured throughput: **~8 500 parquets/min** at workers=32 —
a **250× improvement**.

| Approach | Time/call | Parquets/min (workers=32) |
|---|---|---|
| `gcloud storage cp` + `gcloud storage ls` subprocess | ~500ms each × 5 calls | ~34 |
| UTL `gcs_copy_object` + `gcs_describe_object` | ~50–200ms via REST | ~8 500 |

## Functions

### `gcs_copy_object(src_uri, dst_uri)`
Server-side rewrite via GCS API — no data egress within the same region. GCS guarantees CRC32C integrity
on the server side; no client-side verification needed for the copy itself.

### `gcs_delete_object(uri)`
Deletes the object. Returns `None`. Raises `google.cloud.exceptions.NotFound` if the object does not exist.

### `gcs_describe_object(uri) -> BlobMetadata | None`
Returns `BlobMetadata` (fields: `name`, `bucket`, `size`, `content_type`, `etag`, `crc32c`, `last_modified`).
Returns `None` if the object does not exist. Internally calls `blob.reload()` to populate all fields.

## Requirements

- `CLOUD_PROVIDER=gcp` (or equivalent runtime config) must be set — same as all other UTL cloud operations.
- On GCE VMs with Application Default Credentials (ADC), this works automatically.
- `google-cloud-storage>=3.8.0` is bundled in UTL's dependencies.

## Anti-patterns (do NOT use)

```python
# ❌ subprocess — 500ms startup per call, no GIL release
subprocess.run(["gcloud", "storage", "cp", src, dst], check=True)
subprocess.run(["gsutil", "cp", src, dst], check=True)

# ❌ direct google.cloud.storage client in scripts — bypasses UTL abstraction
from google.cloud import storage
client = storage.Client()
client.bucket(b).copy_blob(...)

# ❌ subprocess describe for metadata
subprocess.run(["gcloud", "storage", "objects", "describe", uri], ...)
```

## Incident history

**2026-05-19**: Phase 3 GCS migration fleet relaunched after discovering 140-hour ETA caused by 5 subprocess
spawns per parquet (`gcloud storage cp` + 2× `gcloud storage objects describe` + `gcloud storage rm`).
Switching to UTL `gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object` reduced runtime from 140h to
~45 minutes for the full corpus. PM@e108cb090 + follow-up codex PR.

## Source

Implemented: `unified_trading_library/cloud_interface/gcs_blob_ops.py`
Exported: `unified_trading_library.cloud_interface`
Plan: `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 7 — Codex updates
