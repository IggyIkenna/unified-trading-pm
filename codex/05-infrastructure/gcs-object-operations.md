---
scope: [engineer, admin]
---

# GCS Object Operations — Canonical Pattern

**SSOT for per-object copy / delete / describe in migration and batch scripts.**

## Rule

Use `unified_trading_library.cloud_interface.gcs_copy_object` / `gcs_delete_object` / `gcs_describe_object` instead of
spawning `gcloud` or `gsutil` subprocesses for GCS object-level operations.

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

`gcloud`/`gsutil` CLI spawns cost **~500ms per call** (subprocess + Python interpreter startup + GCP auth). At
workers=32 in a `ThreadPoolExecutor`, 5 subprocess calls per parquet limits throughput to **~34 parquets/min**.

The UTL helpers use the `google-cloud-storage` REST API (~50–200ms per call) and release the Python GIL (IO-bound), so
threads run in true parallel. Measured throughput: **~8 500 parquets/min** at workers=32 — a **250× improvement**.

| Approach                                             | Time/call             | Parquets/min (workers=32) |
| ---------------------------------------------------- | --------------------- | ------------------------- |
| `gcloud storage cp` + `gcloud storage ls` subprocess | ~500ms each × 5 calls | ~34                       |
| UTL `gcs_copy_object` + `gcs_describe_object`        | ~50–200ms via REST    | ~8 500                    |

## Functions

### `gcs_copy_object(src_uri, dst_uri)`

Server-side rewrite via GCS API — no data egress within the same region. GCS guarantees CRC32C integrity on the server
side; no client-side verification needed for the copy itself.

### `gcs_delete_object(uri)`

Deletes the object. Returns `None`. Raises `google.cloud.exceptions.NotFound` if the object does not exist.

### `gcs_describe_object(uri) -> BlobMetadata | None`

Returns `BlobMetadata` (fields: `name`, `bucket`, `size`, `content_type`, `etag`, `crc32c`, `last_modified`). Returns
`None` if the object does not exist. Internally calls `blob.reload()` to populate all fields.

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

## Migration-script performance contract (HARD RULE — codified 2026-06-01)

**Every whole-corpus GCS migration / backfill / reconciler script MUST be parallel + observable + shardable from day
one.** This is the cross-service SSOT for the contract (the per-AG + per-service canonicalisation plans —
`{defi,cefi,tradfi,sports,prediction}_manifest_canonicalisation_2026_06_01.md` + `instruments_…` +
`downstream_services_…` — all reference it). A script that walks a bucket MUST satisfy all six:

1. **Parallelise the object walk** with `ThreadPoolExecutor(max_workers=workers)` — GCS read/write **release the GIL**,
   so I/O-bound walks overlap for 5–10× (dominant cost is GCS round-trips, not CPU). A bare `for obj in objs:` loop over
   a remote bucket is **review-blocking**. (CPU-bound _serialize_ is GIL-capped → escalate to `ProcessPoolExecutor` only
   if profiling shows serialize-bound; threads first for pure I/O.)
2. **Wire the knobs — no dead args.** `--workers` actually sizes the pool; `--start-date`/`--end-date` actually filter
   the walk → the job is **date-shardable across many VMs** (the real horizontal-scale lever). A parsed-but-unused arg
   is a latent perf/scope bug.
3. **Path-only move ⇒ `gcs_copy_object` (server-side, ~250×); content/column transform ⇒ download+transform+upload
   (unavoidable) but parallelised.** Never download+reupload when only the path changes. Idempotent: re-running on
   already-canonical objects is a no-op (skip).
4. **Observability**: log a progress counter every N objects (≈1000) AND run under `python -u` / `PYTHONUNBUFFERED=1` —
   block-buffered stdout hides all progress until exit and is indistinguishable from a hang.
5. **Per-object failure isolation** — `try/except … continue` per object (log + skip), never `raise` inside the walk
   (composes with shard-level failure isolation). The run completes; the verify step catches any gaps.
6. **Tune for the bottleneck**: I/O-bound → more workers + GCS client connection-pool headroom (gcsfs/aiohttp default
   ~100 conns covers workers ≤ ~64); CPU/bandwidth-bound → bigger VM or shard across VMs by date. GCS has **no
   client-side warm cache** — concurrency (in-flight requests), not "warming", is the throughput lever.

### Measured sizing (2026-06-01 DeFi C0, in-region e2-standard-8) + the <1h recipe

Empirical: at `--workers 32` the in-region C0 walk ran at **load avg ~1.46 on 8 cores (~18% CPU)** — every worker thread
blocked on GCS round-trips, i.e. **I/O-bound with large CPU + bandwidth headroom**. So for a content-transform walk
(download→transform→upload, can't use server-side copy):

- **Default to `--workers 64`** (was 16/32), and go to **96** when the corpus is large and the VM is I/O-bound (verify
  with `uptime` load « ncores). One VM's gcsfs/aiohttp pool tops out ~100 concurrent conns, so **>~96 workers on a
  single VM hits diminishing returns** — past that, scale _horizontally_, don't just raise workers.
- **Bump the gcsfs connection pool when workers > ~64**: the default ~100-conn aiohttp connector becomes the cap; size
  it ≳ workers so threads aren't queuing on connections.
- **Horizontal scale is THE lever for a <1h target on a large (100K+ object) corpus**: shard the walk across VMs by
  `--start-date`/`--end-date` (now functional) **and/or one VM per bucket** (`--buckets <one>`), each at workers≈64–96
  with its own connection pool. A single sequential-bucket VM cannot beat its one pool; N VMs give ~N× (each its own
  pool + bandwidth). Example: a 191K-object bucket at ~1.8K/min·32w ≈ hours on one VM → ~3 date-shard VMs at 96w ≈ ~½h.
- Re-running is safe (idempotent overwrite), so it's fine to kill an under-provisioned run and relaunch sharded/higher-
  worker once a quick comparison confirms throughput scales.

## Migration completeness + uniform-schema + legacy-deletion contract (HARD RULE — codified 2026-06-01)

**Why migrations kept failing (operator post-mortem 2026-06-01).** The canonical TARGET layout moved several times (defi
e.g. `{data_type}/{venue}/{chain}/date=` → `day=/category=defi/` → `raw_tick_data/by_date/day=/asset_group=/`), and
**each move wrote a NEW layout WITHOUT deleting the old**. So a single source bucket silently accumulated 2–3
**overlapping representations of the same cells** in different schemas + partial coverage. Migrations then (a) assumed
one layout and **missed the other 90%**, and (b) **never deleted** the old buckets/paths → dual/triple SSOT →
data-status can't show true missing data → "audit + migrate" again → the loop repeats. Every whole-corpus migration MUST
break it:

1. **Discover ALL historical layouts — never assume today's target shape.** Mandatory pre-flight: bucket-wide list of
   distinct top-level prefixes/trees. An unrecognised tree is **review-blocking, never silently skipped**. (defi: a
   `day=`-prefix listing that ignored `dex_pools/` + `raw_tick_data/` caught only ~10%.)
2. **Normalize every layout to ONE canonical cell key + dedup overlaps** (freshest schema → most-complete → latest
   write). The union migrates once; no duplicate object per canonical cell, no cell dropped.
3. **Uniform output schema (KEY).** Every output object is conformed to the SINGLE canonical schema for its data_type
   (UAC contract): identical column set (`schema_version=v9` + `asset_group`/`pipeline_mode`/`source`/`available_at` +
   canonical `venue`/`chain`/`data_type` + the data_type's data columns) **and** identical path layout — regardless of
   which source layout the cell came from. A `dex_pools/`-sourced cell and a `raw_tick_data/`-sourced cell come out
   byte-structurally identical. Non-uniform output just recreates the mess in the new bucket.
4. **End by DELETING all legacy buckets + paths** — but ONLY after the completeness+uniformity gate: canonical
   distinct-cells ≥ union of every source layout's distinct cells, CF-1…CF-12 GREEN, and one schema per data_type across
   all output objects. **A migration that leaves the old layout in place is NOT done** — it re-creates the dual-SSOT.
   Done-definition: **exactly one canonical v9 SSOT remains**, verifiable by data-status showing a single source.

SSOT for the concrete unified-migration spec: `plans/active/defi_manifest_canonicalisation_2026_06_01.md` §C0-RD1…RD5.

## Incident history

**2026-06-01**: the DeFi C0 tool (`migrate_defi_full_v9_canonical.py`) walked ~40–50K objects **single-threaded** (~26%
CPU of an 8-vCPU VM, projected **hours**), with `--workers`/`--start-date`/`--end-date` parsed but **never wired** (dead
args). Fixed at mtds@92b8d25b (ThreadPoolExecutor + wired date-shard knobs). Codified the six-point contract above; all
per-AG + per-service canonicalisation walks inherit it.

**2026-05-19**: Phase 3 GCS migration fleet relaunched after discovering 140-hour ETA caused by 5 subprocess spawns per
parquet (`gcloud storage cp` + 2× `gcloud storage objects describe` + `gcloud storage rm`). Switching to UTL
`gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object` reduced runtime from 140h to ~45 minutes for the full
corpus. PM@e108cb090 + follow-up codex PR.

## Source

Implemented: `unified_trading_library/cloud_interface/gcs_blob_ops.py` Exported:
`unified_trading_library.cloud_interface` Plan: `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 7
— Codex updates
