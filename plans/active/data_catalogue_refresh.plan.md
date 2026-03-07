---
name: Data Catalogue Refresh
overview: |
  Recheck the data catalogue for availability and MVP readiness. Split availability audit
  across GCP and AWS (dual-cloud). Automate YAML catalogue updates when schemas or instruments
  change. Replace static file-reading with a smarter metadata catalogue backed by a queryable
  store for speed and consistency.

  Scope:
    1. Availability audit — which datasets are actually available in GCP vs AWS
    2. MVP split — identify the minimum datasets needed for first live trading (CEFI, TradFi, DeFi, Sports)
    3. Auto-update — catalogue YAML updates automatically when instruments-service writes new schemas
    4. Smarter metadata store — replace slow filesystem reads with a cached queryable catalogue

todos:
  - id: dc-availability-audit-gcp
    content: |
      GCP DATA AVAILABILITY AUDIT: For each dataset declared in data-catalogue.*.yaml, verify
      that the GCS bucket + prefix actually contains data for the expected date range.

      Run a script that checks:
        - Bucket exists + accessible with service account
        - At least one partition present (year=YYYY/month=MM/day=DD/)
        - Parquet file is readable + schema matches declared schema
        - Row count > 0 for at least one recent date (last 30 days)

      Output: data-catalogue-gcp-availability-report.yaml with status: available|empty|missing|schema_mismatch
      per dataset. Score PASS if >= 80% of declared datasets are available.
    status: pending
    activeForm: "Auditing GCP data availability against declared catalogue"

  - id: dc-availability-audit-aws
    content: |
      AWS DATA AVAILABILITY AUDIT: Same check as dc-availability-audit-gcp but against S3 buckets.
      Run only after aws_migration phase 1 (S3 buckets provisioned).

      Output: data-catalogue-aws-availability-report.yaml with same schema as GCP report.
      Cross-reference with GCP report to identify datasets present in one cloud but not the other.
    status: pending
    activeForm: "Auditing AWS S3 data availability against declared catalogue"

  - id: dc-mvp-split
    content: |
      MVP DATASET IDENTIFICATION: Define the minimum dataset set needed for first live batch trading
      across all four categories. Output as data-catalogue-mvp.yaml.

      CEFI MVP:
        - instruments (all T0 exchanges: binance, deribit, coinbase)
        - OHLCV candles (1m, 5m, 1h) for top-20 instruments per exchange, 90 days
        - Order book snapshots not required for MVP

      TradFi MVP:
        - instruments (equities: top-500 by volume; FX: major pairs)
        - OHLCV candles (1d, 1h) for top-100 instruments, 2 years

      DeFi MVP:
        - instruments (top-50 by TVL from thegraph)
        - onchain OHLCV (1h) for top-50, 180 days

      Sports MVP:
        - fixtures (EPL + Bundesliga, last 3 seasons)
        - odds snapshots (pinnacle + odds_api, last season)

      Mark each dataset as: mvp_required | mvp_optional | post_mvp.
    status: pending
    activeForm: "Defining MVP dataset requirements per trading category"

  - id: dc-auto-update-yaml
    content: |
      AUTO-UPDATE CATALOGUE YAML: When instruments-service writes a new batch of instruments or
      when a new partition appears in GCS/S3, automatically update data-catalogue.*.yaml.

      Implementation options:
        (a) GCS Object Notification → Pub/Sub → instruments-service listener → catalogue update
        (b) instruments-service post-batch hook → directly updates catalogue YAML via ConfigStore

      Preferred: option (b) — instruments-service owns instrument data, so it should update
      the catalogue when it writes.

      Changes needed:
        - instruments-service: after each successful batch write, call catalogue_updater.update()
        - catalogue_updater.py (new): reads existing YAML, updates last_updated + row_count + partitions
        - Write updated YAML back via get_storage_client() + notify via event bus
        - Add test: mock write → verify catalogue YAML updated with correct metadata
    status: pending
    activeForm: "Implementing automatic data catalogue YAML updates on instrument writes"

  - id: dc-metadata-store
    content: |
      SMARTER METADATA CATALOGUE: Replace slow filesystem reads (reading YAML files for each
      catalogue query) with a queryable metadata store.

      Options evaluated:
        (a) BigQuery external table over YAML files in GCS — SQL queryable, auto-updated
        (b) Firestore/DynamoDB document store — fast key-value lookups, real-time updates
        (c) In-memory cache in instruments-service — fastest, but no cross-service queries

      Recommended approach:
        - Primary store: BigQuery external table over GCS JSON catalogue files (GCP)
          / Athena external table over S3 JSON catalogue files (AWS)
        - Cache: instruments-service maintains in-memory catalogue snapshot, refreshed on
          CONFIG_CHANGED event
        - UCI: add get_metadata_client() → MetadataClient ABC with query(dataset, filters) method
          backed by BigQuery/Athena externally or in-memory locally

      Add MetadataClient to UCI with:
        - list_datasets(category=None, status=None) → list[DatasetMeta]
        - get_dataset(dataset_id) → DatasetMeta
        - query_partitions(dataset_id, since=None, until=None) → list[PartitionMeta]
    status: pending
    activeForm: "Designing and implementing smarter metadata catalogue store"

  - id: dc-catalogue-format-standard
    content: |
      CATALOGUE FORMAT STANDARDISATION: Define canonical schema for data-catalogue-*.yaml files
      in unified-trading-codex/06-coding-standards/data-catalogue-schema.md.

      Required fields per dataset entry:
        dataset_id: instruments_cefi_binance
        category: cefi | tradfi | defi | sports
        service_owner: instruments-service
        schema_ref: unified_internal_contracts.domain.instruments.InstrumentsSchema
        gcp_path: gs://instruments-cefi-batch/instrument_availability/
        aws_path: s3://instruments-cefi-batch/instrument_availability/
        partition_keys: [year, month, day]
        format: parquet
        retention_days: 90
        last_updated: <iso>
        row_count_last_batch: <int>
        status: available | empty | missing | deprecated

      Update all existing data-catalogue-*.yaml files to conform to this schema.
    status: pending
    activeForm: "Standardising data catalogue YAML schema and updating existing files"
isProject: false
---

# Data Catalogue Refresh

**Scope:** All datasets declared across CEFI, TradFi, DeFi, and Sports trading categories **Blocks:** First deployment
(L2 infra verify checks catalogue availability) **Owner:** instruments-service team

---

## Problem

The data catalogue exists as static YAML files that:

1. Are not verified against actual data availability
2. Require filesystem reads (slow for queries)
3. Are not automatically updated when new data arrives
4. Have no dual-cloud (GCP + AWS) availability split

---

## Target State

- Availability reports per cloud (GCP + AWS) with PASS/FAIL per dataset
- MVP dataset list defined — clear scope for first live trading
- Catalogue YAML auto-updates when instruments-service writes new batches
- MetadataClient in UCI replaces filesystem reads with queryable store
- Canonical catalogue YAML schema enforced in codex
