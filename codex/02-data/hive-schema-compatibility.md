---
doc_type: codex-ssot
title: Hive Schema Compatibility
summary: >-
  Migration strategy + rationale for GCS-native Parquet with Hive-style partitioning replacing BigQuery storage (40-60%
  lower storage cost; self-describing day=/venue=/data_type= keys queryable as BigQuery external tables +
  Presto/Athena); the BigQuery dual-write/reader phases are now legacy (migration completed 2026-05-22, BQ writers
  removed) — per-asset-group path templates + shard atoms live in per-asset-group-bucket-layouts.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, market-data-processing-service, strategy-service]
scope: [engineer, admin]
tags: [migration, cost, data-pipeline, infrastructure, canonicalisation, polars]
related:
  [
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    ../../plans/epics/mtds_mdps_master.md,
  ]
created: 2026-03-27
authoritative_for: [GCS parquet hive-partitioning cost/rationale + BigQuery-to-GCS migration]
referenced_by: [/codex/02-data/instrument-pipeline-defi.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Hive Schema Compatibility

## Overview

This document defines the migration strategy from BigQuery schemas to Hive-compatible schemas for cost-optimized data
storage and analytics. The goal is to store data on GCS in Parquet format with Hive-style partitioning, query via
Hive/Presto/Athena, and migrate services incrementally with short-term dual schema support.

---

## Why Hive Compatibility

### Cost Optimization: GCS Storage + Hive Queries

**Problem:** BigQuery storage costs scale with data volume

- BigQuery active storage: **$0.02/GB/month**
- BigQuery long-term storage: **$0.01/GB/month** (data not modified for 90 days)
- **Total cost for 10TB:** $100-$200/month

**Solution:** Store data on GCS, query via Hive

- GCS Standard storage: **$0.023/GB/month**
- GCS Nearline storage: **$0.010/GB/month** (accessed <1x/month)
- **Hive/Presto/Athena queries:** Scan GCS directly, no storage markup
- **Total cost for 10TB:** $100/month (Nearline) + query compute costs

**Savings:** 40-60% reduction in storage costs for long-term data

### External Analytics Tools

**Use case:** Run Spark, Presto, Athena queries on trading data

- **Spark:** Large-scale analytics, ML feature engineering
- **Presto:** Interactive queries, dashboards
- **Athena:** Serverless queries on S3 (AWS dual-cloud readiness)

**Requirement:** Hive-compatible schema and partitioning

---

## Data Format: Parquet

### Why Parquet

**Advantages:**

1. **Columnar storage:** Efficient for analytics (read only needed columns)
2. **Compression:** 5-10x smaller than CSV
3. **Schema evolution:** Supports adding/removing columns
4. **Hive-native:** Standard format for Hive tables
5. **Interoperable:** Works with BigQuery, Spark, Presto, Athena

**Comparison:**

| Format  | Size     | Query Speed | Hive Support | BigQuery Support |
| ------- | -------- | ----------- | ------------ | ---------------- |
| CSV     | 1.0x     | Slow        | Yes          | Yes              |
| Parquet | 0.1-0.2x | Fast        | Yes          | Yes              |
| ORC     | 0.1-0.2x | Fast        | Yes (native) | No               |
| Avro    | 0.3-0.5x | Medium      | Yes          | Yes              |

**Decision:** Parquet for best balance of compression, speed, and compatibility

---

## Partitioning Strategy

> **SSOT pointer**: canonical per-asset-group path templates + hive-key vocabulary (`asset_group=` canonical vs
> `category=` legacy) + reader fallback discipline live in
> [`per-asset-group-bucket-layouts.md`](./per-asset-group-bucket-layouts.md). This section retains only the parquet+BQ
> rationale specific to hive-compatible partitioning; for the per-service path templates and shard-atom shapes per
> asset_group, consult the per-asset-group-bucket-layouts SSOT.

### Why hive-style partitioning (parquet + BigQuery rationale)

The workspace standardised on hive-style partition keys (`day=YYYY-MM-DD`, `venue=BINANCE`, `data_type=trades`) over
positional partitioning (`/2024/02/12/...`) because hive-style is self-describing in the path AND is the partition
syntax BigQuery's external-table reader expects without further configuration. The same parquet files on GCS are
queryable as BigQuery external tables (cost-optimised — pay GCS storage rates instead of BQ storage rates) precisely
because the partition key/value pairs are encoded in the directory names.

- **Metadata visibility:** Partition keys are self-describing.
- **Easier queries:** `SELECT * FROM table WHERE day='2024-02-12' AND venue='BINANCE'`.
- **External-tool standard:** Expected by Hive, Presto, Athena, BigQuery external tables.
- **Pruning:** Query engines skip partitions that don't match the WHERE clause without reading parquet footers.

**Trade-off:**

- **More partitions → Faster queries** (scan fewer files).
- **More partitions → Slower writes** (more directories to manage).
- **Recommendation:** Use the per-asset-group shard-atom shapes documented in
  [`per-asset-group-bucket-layouts.md`](./per-asset-group-bucket-layouts.md); they encode the workspace's chosen
  partition cardinality per asset_group + data_type.

---

## Schema Evolution Strategy

> **[DELTA 2026-05-22]** **Current state:** The workspace completed the migration to GCS-native Parquet (hive-style) as
> the primary storage format. BigQuery dual-write has been removed; all production data now lands in GCS Parquet via
> `resolve_bucket_name(...)`. The BigQuery migration phases below are legacy documentation from the original design
> (2026-Q1/Q2). **Planned delta:** `plans/epics/mtds_mdps_master.md` tracks ongoing GCS path canonicalisation and
> single-walk bundle migration (`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`). **Target
> architecture:** All services read/write GCS Parquet via canonical hive paths — BigQuery is external-table access only
> for ad-hoc analytics.

### Migration Approach: Short-Term Dual Support

**Key insight:** Not long-term backwards compatibility—just during migration

#### Phase 1: Add Hive Schema Writers (Dual Write)

**Timeline:** Q2 2026 (COMPLETED — GCS is now primary write path)

**Approach:**

1. Keep existing BigQuery writers (current data flow)
2. Add new GCS Parquet writers (Hive-compatible)
3. **Write to both destinations** during migration
4. New data flows to both BigQuery and GCS

**Example:**

```python
# Current: Write to BigQuery only
await bigquery_client.insert_rows(table, rows)

# Migration: Dual write
await bigquery_client.insert_rows(table, rows)  # Keep existing
await parquet_writer.write_to_gcs(bucket, path, rows)  # Add new
```

#### Phase 2: Migrate Readers to GCS (Incremental)

**Timeline:** Q2-Q3 2026

**Approach:**

1. Migrate downstream services one-by-one to read from GCS Parquet
2. Test each service independently
3. **Keep BigQuery readers as fallback** during migration

**Example services to migrate:**

- `ml-training-service`: Read historical data from GCS instead of BigQuery
- `features-service (volatility family)`: Read tick data from GCS
- `strategy-service`: Read backtest data from GCS

**Migration order:**

1. Batch analytics services (low risk, read-only)
2. ML training services (can revert easily)
3. Strategy backtesting (validate Parquet data matches BigQuery)
4. Last: Live data consumers (highest risk)

#### Phase 3: Remove BigQuery Writers (Complete Migration)

**Timeline:** Q4 2026

**Approach:**

1. Once all readers migrated, stop dual writes
2. Remove BigQuery writer code
3. **Migrate historical BigQuery data to GCS** (backfill)

**Backfill process:**

```python
# Export historical BigQuery data to GCS Parquet
bq_table = "unified-trading.market_data.tick_data"
gcs_path = "gs://unified-trading-market-data/tick_data/"

# BigQuery export to Parquet
job = bigquery_client.extract_table(
    bq_table,
    gcs_path + "year=*/month=*/day=*/*.parquet",
    job_config=bigquery.ExtractJobConfig(
        destination_format="PARQUET",
        compression="SNAPPY"
    )
)
job.result()  # Wait for completion
```

#### Phase 4: Clean Up Dual Support Code

**Timeline:** Q1 2027

**Approach:**

1. Remove BigQuery fallback readers
2. Remove dual-write logic
3. Archive BigQuery data (for audit trail)

**Mark migration as complete when:**

- All services read from GCS Parquet
- No BigQuery writes for 30+ days
- Historical data backfilled to GCS

---

## Schema Definition

### Centralized Schema Ownership

**Pattern:** Service-owned output schemas + unified-trading-services cross-cutting schemas

#### Service-Owned Schemas

**Each service defines its output schema:**

```python
# market-data-processing-service/schemas/output_schemas.py
from pydantic import BaseModel
from datetime import datetime

class TickDataSchema(BaseModel):
    timestamp: datetime
    instrument: str
    venue: str
    price: float
    quantity: float
    side: str  # "BUY" | "SELL"
```

**Parquet schema (auto-generated from Pydantic):**

```python
import pyarrow as pa
from pyarrow import parquet as pq

# Convert Pydantic schema to PyArrow schema
schema = pa.schema([
    ("timestamp", pa.timestamp("us")),
    ("instrument", pa.string()),
    ("venue", pa.string()),
    ("price", pa.float64()),
    ("quantity", pa.float64()),
    ("side", pa.string()),
])
```

#### Cross-Cutting Schemas (unified-trading-services)

**Owned by `unified-trading-services`:**

- Event logging schema (lifecycle events)
- Configuration schema (service configs)
- Observability schema (metrics, traces)

---

## Data Validation

### Pre-Upload Validation (Required)

**From `02-data/schema-governance.md`:**

Every service must call `validate_timestamp_date_alignment()` before GCS write

**Purpose:**

- Ensure data written to correct partition (e.g., `2024-02-12` data goes to `/year=2024/month=02/day=12/`)
- Detect clock skew, timezone issues
- **Prevent data loss** from writing to wrong partition

**Implementation:**

```python
from unified_trading_services.validators import validate_timestamp_date_alignment

# Before writing to GCS
data = [
    {"timestamp": datetime(2024, 2, 12, 10, 30, 0), "price": 50000.0, ...},
    {"timestamp": datetime(2024, 2, 12, 10, 31, 0), "price": 50001.0, ...},
]

# Validate all timestamps match partition date
target_partition = "year=2024/month=02/day=12"
validate_timestamp_date_alignment(data, target_partition)

# Write to GCS
await parquet_writer.write_to_gcs(bucket, target_partition, data)
```

**Validation checks:**

- All timestamps fall within partition date range (00:00:00 - 23:59:59 UTC)
- No timezone mismatches (all timestamps are UTC)
- No future dates (detect clock skew)

---

## Migration Tools

### BigQuery to GCS Parquet Converter

**Tool:** `unified-trading-services/scripts/bigquery_to_parquet.py`

**Usage:**

```bash
python scripts/bigquery_to_parquet.py \
  --bq-table "unified-trading.market_data.tick_data" \
  --gcs-bucket "unified-trading-market-data" \
  --gcs-prefix "tick_data/" \
  --date-range "2024-01-01:2024-12-31" \
  --partition-by "instrument,year,month,day"
```

**Features:**

- Incremental export (only new partitions)
- Schema translation (BigQuery → Parquet)
- Validation (compare row counts, checksums)
- Parallel export (multiple workers)

### Schema Migration Script

**Tool:** `unified-trading-services/scripts/migrate_schema.py`

**Purpose:** Update existing Parquet files to new schema version (add/remove columns)

**Usage:**

```bash
python scripts/migrate_schema.py \
  --gcs-bucket "unified-trading-market-data" \
  --gcs-prefix "tick_data/" \
  --old-schema "schemas/tick_data_v1.json" \
  --new-schema "schemas/tick_data_v2.json" \
  --backfill-column "new_column=default_value"
```

---

## Query Layer

### Hive/Presto/Athena Configuration

#### Hive Table Definition

```sql
CREATE EXTERNAL TABLE tick_data (
    timestamp TIMESTAMP,
    price DOUBLE,
    quantity DOUBLE,
    side STRING
)
PARTITIONED BY (
    instrument STRING,
    year INT,
    month INT,
    day INT
)
STORED AS PARQUET
LOCATION 'gs://unified-trading-market-data/tick_data/';

-- Add partitions (one-time or automated)
MSCK REPAIR TABLE tick_data;
```

#### Presto Query Example

```sql
-- Query specific partition (fast)
SELECT
    timestamp,
    price,
    quantity
FROM tick_data
WHERE
    instrument = 'BTC-PERP'
    AND year = 2024
    AND month = 2
    AND day = 12
ORDER BY timestamp;
```

#### Athena Query Example (AWS Dual-Cloud)

```sql
-- Same query, different execution engine
SELECT
    AVG(price) AS avg_price,
    COUNT(*) AS trade_count
FROM tick_data
WHERE
    instrument = 'BTC-PERP'
    AND year = 2024
    AND month = 2
GROUP BY instrument, year, month, day;
```

---

## Backwards Compatibility During Migration

### Dual Schema Support (Temporary)

**Goal:** Allow services to read from either BigQuery or GCS during migration

#### Data Layer Abstraction

```python
# unified-trading-services/data_readers.py
from enum import Enum

class DataSource(Enum):
    BIGQUERY = "bigquery"
    GCS_PARQUET = "gcs_parquet"

async def read_tick_data(
    instrument: str,
    start_date: str,
    end_date: str,
    source: DataSource = DataSource.GCS_PARQUET  # Default to new source
):
    if source == DataSource.BIGQUERY:
        return await read_from_bigquery(instrument, start_date, end_date)
    elif source == DataSource.GCS_PARQUET:
        return await read_from_gcs_parquet(instrument, start_date, end_date)
    else:
        raise ValueError(f"Unknown data source: {source}")
```

**Migration process:**

1. **Week 1:** Services default to BigQuery, opt-in to GCS
2. **Week 2-8:** Services migrate one-by-one, flip default to GCS
3. **Week 9+:** Remove BigQuery support

**Feature flag:**

```yaml
# service config.yaml
data_source:
  default: gcs_parquet # "bigquery" | "gcs_parquet"
  fallback: bigquery # Fallback if GCS read fails
```

---

## Cost Analysis

### Storage Cost Comparison

**Assumptions:**

- 10TB data (market data, features, backtest results)
- 6 years history

| Storage             | BigQuery | GCS Standard        | GCS Nearline         | Savings  |
| ------------------- | -------- | ------------------- | -------------------- | -------- |
| Cost/GB/month       | $0.02    | $0.023              | $0.010               | -        |
| **10TB cost/month** | **$200** | **$230**            | **$100**             | **50%**  |
| Query cost          | Included | Hive/Presto compute | Athena $5/TB scanned | Variable |

**Recommendation:** GCS Nearline for historical data (>30 days), GCS Standard for recent data

### Query Cost Comparison

**BigQuery:**

- $6.25 per TB scanned (on-demand pricing)
- **Example:** 1TB scan = $6.25

**Presto (self-hosted):**

- Compute cost only (VM instances)
- **Example:** n2-standard-8 (8 vCPU) = $0.40/hour
- 1TB scan ~1 hour = $0.40

**Athena (AWS):**

- $5 per TB scanned
- **Example:** 1TB scan = $5

**Savings:** Presto self-hosted is 10-15x cheaper than BigQuery for large scans

---

## Implementation Checklist

### Service Migration Template

**For each service migrating to Hive schema:**

1. ✅ **Add Parquet writer** (dual write to GCS + BigQuery)
2. ✅ **Validate data** (compare GCS vs BigQuery row counts)
3. ✅ **Update readers** (read from GCS, fallback to BigQuery)
4. ✅ **Test queries** (validate Parquet data matches BigQuery)
5. ✅ **Monitor metrics** (track read latency, error rate)
6. ✅ **Remove BigQuery writer** (after 30 days of stable GCS reads)
7. ✅ **Backfill historical data** (export BigQuery to GCS)
8. ✅ **Remove BigQuery fallback** (GCS-only reads)

---

## Configuration Example

```yaml
hive_schema:
  storage:
    bucket: unified-trading-market-data
    format: parquet
    compression: snappy

  partitioning:
    style: hive # "/year=2024/month=02/day=12/"
    dimensions:
      - date # year, month, day
      - instrument # Optional per dataset
      - venue # Optional per dataset

  migration:
    dual_write_enabled: true # Write to both BigQuery and GCS
    default_source: gcs_parquet # Read from GCS by default
    fallback_source: bigquery # Fallback if GCS fails

  validation:
    pre_upload: true # Call validate_timestamp_date_alignment()
    post_upload: true # Compare row counts

  query_engine:
    default: presto # "bigquery" | "presto" | "athena"
    presto_endpoint: http://presto.internal:8080
    athena_workgroup: unified-trading-analytics
```

---

## References

- **Schema Governance:** `02-data/schema-governance.md`
- **GCS Bucket Structure:** `sports-betting-services/docs/local_gcs_folder_structure/GCS_BUCKET_STRUCTURE.md`
- **BigQuery to GCS Migration:** `unified-trading-services/scripts/bigquery_to_parquet.py` (to be created)

---

## Implementation Phases

### Phase 1: Dual Write Setup (Q2 2026)

- Add Parquet writers to all pipeline services
- Write to both BigQuery and GCS (dual write)
- Validate data consistency (row counts, checksums)

### Phase 2: Reader Migration (Q2-Q3 2026)

- Migrate batch analytics services (ML training, backtesting)
- Update configuration to read from GCS by default
- Keep BigQuery fallback during migration

### Phase 3: Backfill Historical Data (Q3 2026)

- Export historical BigQuery data to GCS Parquet
- Validate backfilled data (sample queries, row counts)
- Archive BigQuery data for audit trail

### Phase 4: Remove Dual Support (Q4 2026)

- Stop writing to BigQuery
- Remove BigQuery fallback readers
- Mark migration complete
