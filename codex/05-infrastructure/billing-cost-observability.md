---
doc_type: codex-ssot
title: Billing & Cost Observability — GCP + AWS export backends for the deployment UI
summary:
  Provisioned cost-observability backends for the deployment-UI cost tab — GCP BigQuery billing export (billing_export
  dataset; standard + resource-level tables) and an AWS CUR→S3→Athena stack (aws_billing.cur_uts_cost_usage, workgroup
  uts-billing), plus the read-only BigQuery/IAM grants to the deployment-api service identities.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, deployment-api]
scope: [engineer, admin]
tags: [billing, cost, observability, bigquery, athena, cur, gcp, aws, deployment-ui, iam]
related: [spot-vms-for-backfill.md, aws-cloudtrail-cost-optimization-2026-06-20.md, aws-iam-matrix.md]
created: 2026-06-27
authoritative_for:
  [deployment-UI billing/cost-observability backends (GCP BQ export + AWS CUR/Athena) and their read-only access grants]
referenced_by: []
owner:
last_reviewed: 2026-06-27
code_refs:
type: infrastructure
execution:
  owner: "deployment-platform"
  cadence: "per billing-export/permission change; verify AWS table after first CUR delivery"
  verifier:
    "bq query on billing_export.gcp_billing_export_v1_* ; Athena query on aws_billing.cur_uts_cost_usage (after ~24h
    first delivery)"
  last_executed: "2026-06-27 (AWS CUR stack stood up)"
---

# Billing & Cost Observability — GCP + AWS export backends

The deployment-UI cost tab reads **granular (per-day / per-service / per-resource / per-bucket) cost** from two
provider-native billing exports — **not** the native Billing APIs (which only do service-level and cost money per
request). Both are provisioned; the frontend just queries them.

|               | GCP                                             | AWS                                                              |
| ------------- | ----------------------------------------------- | ---------------------------------------------------------------- |
| Backend       | BigQuery **Billing Export**                     | **CUR → S3 → Athena**                                            |
| Granularity   | per-day / per-service / **per-bucket / per-VM** | per-day / per-service / **per-resource (EC2) / per-bucket (S3)** |
| Query surface | `bq` / BigQuery API                             | Athena (workgroup `uts-billing`)                                 |
| First data    | live (enabled 2026-06-20)                       | **~24h after 2026-06-27** (crawler builds the table)             |

> Native `billing.viewer` (GCP) / the Cost Explorer console **resource-level toggle** (AWS) are **not** required — the
> exports give strictly more, at query cost near zero. The CE console toggle is redundant given the CUR.

## GCP backend (BigQuery)

- Project `central-element-323112`, dataset **`billing_export`** (US), linked billing account `016B25-109840-AF2ACB`.
- Tables: `gcp_billing_export_v1_016B25_109840_AF2ACB` (standard: service/SKU/project/day) and
  `gcp_billing_export_resource_v1_016B25_109840_AF2ACB` (**resource-level**: per-bucket, per-VM). Enabled via Billing
  console → Billing export (standard + detailed). **Not retroactive** — data from 2026-06-20 forward (GCP backfilled Apr
  1–May 20 on enablement; a gap May 21–Jun 19 may persist — use the console Reports CSV for that window).
- Credits: the `credits` array carries `type=PROMOTION` etc. **Promo credits exhausted ~2026-06-20** (see
  [`spot-vms-for-backfill.md`](spot-vms-for-backfill.md)).

```sql
-- per-service per-day (net of credits)
SELECT FORMAT_DATE('%Y-%m-%d', DATE(usage_start_time)) AS day, service.description AS service,
       ROUND(SUM(cost) + SUM((SELECT IFNULL(SUM(c.amount),0) FROM UNNEST(credits) c)),2) AS net_cost
FROM `central-element-323112.billing_export.gcp_billing_export_v1_016B25_109840_AF2ACB`
GROUP BY 1,2 ORDER BY 1 DESC,3 DESC;
-- per-bucket / per-VM: use the *_resource_v1 table, GROUP BY resource.name
```

## AWS backend (CUR → Athena), payer account `427895769566`, region `us-east-1`

Stood up 2026-06-27 (all via CLI — no console toggle needed):

| Component                                                                             | Name                                 |
| ------------------------------------------------------------------------------------- | ------------------------------------ |
| S3 delivery bucket (public-access blocked; billing-service write policy)              | `uts-billing-cur-427895769566`       |
| CUR report (DAILY, Parquet, `AdditionalSchemaElements=[RESOURCES]`, OVERWRITE_REPORT) | `uts-cost-usage` → prefix `cur/`     |
| Glue database                                                                         | `aws_billing`                        |
| Glue crawler (daily `cron(0 8 * * ? *)`, combines schema → one table)                 | `uts-cur-crawler`                    |
| Athena workgroup (results → `s3://uts-billing-cur-427895769566/athena-results/`)      | `uts-billing`                        |
| Table (created by crawler after first delivery)                                       | **`aws_billing.cur_uts_cost_usage`** |

First CUR file lands within ~24h of creation; the crawler then creates/refreshes the table. Column names are
crawler-detected — `DESCRIBE cur_uts_cost_usage` for the exact set.

```sql
-- per-service per-day
SELECT date(line_item_usage_start_date) AS day, product_product_name AS service,
       round(sum(line_item_unblended_cost),2) AS cost
FROM aws_billing.cur_uts_cost_usage
WHERE line_item_line_item_type IN ('Usage','DiscountedUsage')
GROUP BY 1,2 ORDER BY 1 DESC,3 DESC;
-- per-resource (EC2/VM): GROUP BY line_item_resource_id
-- per-S3-bucket:         WHERE product_servicecode='AmazonS3' GROUP BY line_item_resource_id
-- credits / net:         line_item_net_unblended_cost, or line_item_line_item_type='Credit'
```

Service-level cost is **also** available with zero setup via the Cost Explorer API (`aws ce get-cost-and-usage`) — use
it for the AWS tab until the CUR table lands, or for live forecasts.

### Not covered

- AWS S3 **bucket-level** cost needs the CUR `RESOURCES` element (present) — the CE console resource toggle does **not**
  cover S3. Cost-allocation tags are an alternative but the CUR route is already complete.

## Permissions granted for the deployment UI (2026-06-27)

The UI backend (`deployment-api`) service identities were granted read-only billing access:

- **GCP** — SA `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (runs Cloud Run
  `uts-shared-deployment-api`): dataset **READER** on `billing_export` + project `roles/bigquery.jobUser`.
- **AWS** — managed policy **`uts-billing-readonly`** (Athena on wg `uts-billing` + Glue read on `aws_billing` + S3 read
  on the CUR bucket + `ce:*` read) attached to roles **`uts-deployment-api-{prod,dev,staging}`**.

**If the UI is served by a different identity** (e.g. the dashboard Cloud Run compute SA `1060025368044-compute@…`, or a
new AWS task role), grant it the same: GCP dataset-READER + `bigquery.jobUser`; AWS attach `uts-billing-readonly`. The
frontend's own principal additionally needs `athena:StartQueryExecution/GetQueryResults`, `glue:GetTable/GetPartitions`,
and `s3:GetObject` on the CUR + `athena-results/` prefixes (all included in `uts-billing-readonly`).

## Cost of the exports themselves

Negligible: GCP BQ export storage a few cents/mo; AWS CUR = a few Parquet files/day in one S3 bucket + a daily Glue
crawler (about $0.44/crawler-hour, minutes/day) + Athena at $5/TB scanned (a cost dashboard scans MB). Far cheaper than
`GetCostAndUsageWithResources` at $0.01/request for a polling UI.

## Related

- [`spot-vms-for-backfill.md`](spot-vms-for-backfill.md) ·
  [`aws-cloudtrail-cost-optimization-2026-06-20.md`](aws-cloudtrail-cost-optimization-2026-06-20.md) — the cost work
  these exports made measurable.
- [`aws-iam-matrix.md`](aws-iam-matrix.md) — AWS IAM principals.
