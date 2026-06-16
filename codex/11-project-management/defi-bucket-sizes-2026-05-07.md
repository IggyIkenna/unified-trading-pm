---
scope: [engineer, admin]
title: DeFi Bucket Sizes (point-in-time 2026-05-07)
status: planned
created: 2026-05-07
authoritative_for:
  Per-bucket size estimate (DeFi instruments, MTDS, MDPS, manifests) at a snapshot point 2026-05-07. Feeds the AWS S3
  cost projection + the cross-cloud migration time estimate (storage transfer hours).
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_07.md
related:
  - codex/05-infrastructure/cloud-agnostic-build-lineage.md
  - codex/02-data/availability-manifest-and-data-status.md
last_reviewed: 2026-05-17
---

# DeFi Bucket Sizes (2026-05-07)

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in
> with `gcloud storage du -s` output once the workspace runs the size audit.

## Purpose

Snapshot every DeFi-related bucket's total size + object count + age distribution as of 2026-05-07. This data drives two
decisions: (a) AWS S3 cost projection for the migration target, and (b) the storage-transfer time estimate for the
cutover plan.

## Scope

- DeFi instruments-service buckets (per-protocol catalogues + denorm).
- DeFi MTDS raw-tick buckets (per-chain partition).
- DeFi MDPS processed-tick buckets (per-chain partition).
- Manifest buckets (`_index/availability_index.parquet` + per-VM shards).
- Excluded: events buckets (handled separately under live-deployment-monitoring), CeFi/TradFi/Sports buckets (covered
  under their own asset-group bucket-size docs).

## Outline (planned sections)

1. **Audit methodology** — `gcloud storage du -s -h gs://<bucket>` per-bucket; iceberg of objects under hive partitions
   sampled rather than enumerated for very large prefixes.
2. **Bucket inventory** — full list of DeFi buckets with project + region.
3. **Size table** —
   `bucket_name, project, region, total_bytes, object_count, oldest_object_date, newest_object_date, est_growth_per_day_gb`.
4. **AWS S3 cost projection** — `total_bytes × $0.023/GB/month (Standard) + $0.0125/GB/month (IA)`; cross-region
   transfer-out estimate at cutover.
5. **Storage-transfer plan** — gsutil rsync vs Storage Transfer Service vs Snowball; time-to-transfer estimates.
6. **Lifecycle policy review** — current GCS lifecycle rules; equivalent AWS S3 lifecycle to apply post-migration.

## Cross-references

- **Plan(s) implementing this:**
  [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.md).
- **Related codex SSOTs:** [`cloud-agnostic-build-lineage`](../05-infrastructure/cloud-agnostic-build-lineage.md),
  [`availability-manifest-and-data-status`](../02-data/availability-manifest-and-data-status.md).
- **Code:** TBD audit helper — likely a `gcloud storage du` wrapper script that materialises the table.

## Open questions

- Do we migrate cold (>180 day) data via Snowball + hot data via online rsync, or one path for everything?
- Are there DeFi buckets we should not migrate (e.g. exploratory/sandbox data — leave on GCP, decommission)?
- What is the per-day growth rate for active backfill buckets — does the projection assume backfill complete?
- Do we keep GCS as the cold archive post-migration, or fully decommission?
