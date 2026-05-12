---
scope: [engineer, admin]
last_verified: 2026-05-12
---

# Data Catalogue Schema

**SSOT for:** canonical schema for `unified-trading-pm/configs/data-catalogue.{service}.yaml` files (symlinked into
`deployment-service/configs/`).

All `data-catalogue.*.yaml` files must conform to this schema. Validated by
`data_catalogue_refresh.plan.md#dc-catalogue-format-standard`.

> ## Two distinct manifests — do NOT confuse them (clarified 2026-05-12)
>
> This document covers the **data-catalogue manifest** — a per-service inventory + freshness ledger written to
> `gs://data-catalogue-{project_id}/{service}/day={date}/manifest.parquet` via
> `deployment_service.data_status.manifest_writer.ManifestWriter`. It is for **catalogue-completeness reporting**
> (which datasets exist, when they were last written, row counts at the dataset level).
>
> The **availability manifest** (used everywhere else in this codex) is a different artifact at
> `gs://{kind}-{asset_group}-{env}-{project_id}/_index/availability_index.parquet` written via the canonical
> `unified_trading_library.manifest_writer.ManifestWriter` (`record_captured` / `record_empty` / `record_failed` /
> `record_expected_unattempted` API). It is for **per-shard data-status drilldown** (capture_status × error_reason
> taxonomy). See [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md).
>
> The two SSOT classes happen to share the name `ManifestWriter` — they live in different modules and have
> different APIs. When in doubt, the **availability manifest** is the May-23 cutover artifact; the **data-catalogue
> manifest** is the operator-facing inventory ledger.

---

## Required Fields Per Dataset Entry

```yaml
datasets:
  - dataset_id: instruments_cefi_binance # snake_case, globally unique
    category: cefi # cefi | tradfi | defi | sports | altdata | prediction
    service_owner: instruments-service # repo name that writes this dataset
    schema_ref: unified_api_contracts.internal.domain.instruments.InstrumentsSchema
    gcp_path: gs://instruments-cefi-batch/instrument_availability/
    aws_path: s3://instruments-cefi-batch/instrument_availability/
    partition_keys: [year, month, day] # Hive partition columns
    format: parquet # parquet | json | csv
    retention_days: 90
    last_updated: "2026-03-07T00:00:00Z" # ISO 8601 UTC; updated by service post-batch hook
    row_count_last_batch: 1234 # integer; updated by service post-batch hook
    status: available # available | empty | missing | deprecated
    mvp_tier: mvp_required # mvp_required | mvp_optional | post_mvp
```

---

## Field Rules

| Field                  | Type         | Rule                                                                                              |
| ---------------------- | ------------ | ------------------------------------------------------------------------------------------------- |
| `dataset_id`           | string       | `{entity}_{category}_{source}` — globally unique across all catalogues                            |
| `category`             | enum         | `cefi \| tradfi \| defi \| sports \| altdata \| prediction`                                       |
| `service_owner`        | string       | Must match a repo name in `workspace-manifest.json`                                               |
| `schema_ref`           | string       | Fully-qualified Python import path to the UIC schema class or constant                            |
| `gcp_path`             | string       | Must start with `gs://`                                                                           |
| `aws_path`             | string       | Must start with `s3://`                                                                           |
| `partition_keys`       | list[str]    | Hive partition columns; minimum `[year, month, day]` for time-series                              |
| `format`               | enum         | `parquet \| json \| csv`; prefer parquet                                                          |
| `retention_days`       | int          | Must match GCS/S3 lifecycle rule in deployment-service Terraform                                  |
| `last_updated`         | ISO datetime | Auto-updated by `catalogue_updater.py` after each successful batch write                          |
| `row_count_last_batch` | int          | Auto-updated by `catalogue_updater.py`                                                            |
| `status`               | enum         | `available \| empty \| missing \| deprecated`                                                     |
| `mvp_tier`             | enum         | `mvp_required \| mvp_optional \| post_mvp` — set by `data_catalogue_refresh.plan.md#dc-mvp-split` |

---

## Optional Fields

| Field                 | Type      | Description                                                 |
| --------------------- | --------- | ----------------------------------------------------------- |
| `description`         | string    | Human-readable summary of the dataset                       |
| `tags`                | list[str] | Free-form tags for discovery, e.g. `[ohlcv, candles, cefi]` |
| `sla_freshness_hours` | int       | Maximum acceptable staleness in hours before alerting       |
| `depends_on`          | list[str] | Upstream `dataset_id` values this dataset depends on        |

---

## Manifest-Based Data Catalogue (Current)

The catalogue now uses per-service Parquet manifests written after each batch run, replacing the old YAML-patching
`catalogue_updater` approach. Two components handle write and read:

### ManifestWriter

After each successful batch write, the owning service calls `ManifestWriter` to append a row to the service's manifest
partition:

```python
from deployment_service.data_status.manifest_writer import ManifestWriter

writer = ManifestWriter(project_id="my-project")
writer.write(
    service_name="instruments-service",
    dataset_id="instruments_cefi_binance",
    category="cefi",
    venue="binance",
    date="2026-03-21",
    row_count=1234,
    file_count=3,
    total_bytes=524288,
    gcs_bucket="instruments-cefi-batch",
    gcs_prefix="instrument_availability/year=2026/month=03/day=21/",
    scenario="default",
    grid_id="",
    schema_version="1.0",
    bucket_env="development",
    duration_seconds=12.5,
)
```

Output path: `gs://data-catalogue-{project_id}/{service}/day={date}/manifest.parquet`

### ManifestReader

Queries manifests via DuckDB for fast freshness and completion checks without scanning GCS blobs:

```python
from deployment_service.data_status.manifest_reader import ManifestReader

reader = ManifestReader(project_id="my-project")
results = reader.query_freshness("instruments-service", start_date="2026-03-01", end_date="2026-03-21")
completion = reader.query_completion("instruments-service", start_date="2026-03-01", end_date="2026-03-21")
```

### Manifest Parquet Schema

| Field              | Type     | Description                                     |
| ------------------ | -------- | ----------------------------------------------- |
| `service_name`     | string   | Repo name of the owning service                 |
| `dataset_id`       | string   | Globally unique dataset identifier              |
| `category`         | string   | cefi, tradfi, defi, sports, altdata, prediction |
| `venue`            | string   | Venue name (e.g. binance, deribit)              |
| `date`             | string   | Partition date (YYYY-MM-DD)                     |
| `row_count`        | int64    | Rows written in this batch                      |
| `file_count`       | int32    | Number of Parquet files written                 |
| `total_bytes`      | int64    | Total bytes written                             |
| `gcs_bucket`       | string   | Target GCS bucket name                          |
| `gcs_prefix`       | string   | GCS prefix path for the partition               |
| `scenario`         | string   | Scenario label (default, backtest, etc.)        |
| `grid_id`          | string   | Grid identifier for parameterized runs          |
| `schema_version`   | string   | Manifest schema version                         |
| `bucket_env`       | string   | Environment (development, staging, production)  |
| `duration_seconds` | float64  | Wall-clock seconds for the batch write          |
| `written_at`       | datetime | UTC timestamp when the manifest row was written |

### Partitioning

```
gs://data-catalogue-{project_id}/
  {service}/
    day={YYYY-MM-DD}/
      manifest.parquet
```

Each service gets its own top-level prefix. Daily partitions enable efficient date-range scans.

### DuckDB Query Examples

Freshness check (most recent write per service):

```sql
SELECT service_name, venue, MAX(written_at) AS last_write, MAX(date) AS latest_date
FROM read_parquet('gs://data-catalogue-*/instruments-service/day=*/manifest.parquet')
GROUP BY service_name, venue
ORDER BY last_write DESC;
```

Completion check (dates with data in a range):

```sql
SELECT date, COUNT(DISTINCT venue) AS venues, SUM(row_count) AS total_rows
FROM read_parquet('gs://data-catalogue-*/instruments-service/day=*/manifest.parquet')
WHERE date BETWEEN '2026-03-01' AND '2026-03-21'
GROUP BY date
ORDER BY date;

---

## Availability Audit Reports

Availability audits produce reports in:

- `deployment-service/configs/data-catalogue-gcp-availability-report.yaml`
- `deployment-service/configs/data-catalogue-aws-availability-report.yaml`

PASS threshold: >= 80% of declared datasets have `status: available`.

---

## References

- `data_catalogue_refresh.plan.md` — implementation plan (availability audit, MVP split, auto-update, metadata store)
- `unified-trading-pm/configs/data-catalogue.*.yaml` — per-service catalogue files (canonical data; symlinked into
  `deployment-service/configs/`)
- `00-SSOT-INDEX.md` — SSOT registry entry for data catalogue
```
