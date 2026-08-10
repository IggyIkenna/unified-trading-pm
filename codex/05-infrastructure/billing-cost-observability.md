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
related:
  [
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/aws-cloudtrail-cost-optimization-2026-06-20.md,
    /codex/05-infrastructure/aws-iam-matrix.md,
    /plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
  ]
created: 2026-06-27
authoritative_for:
  [
    deployment-UI billing/cost-observability backends (GCP BQ export + AWS CUR/Athena) and their read-only access grants,
    the DuckDB-over-GCS-parquet cost snapshot read path,
  ]
referenced_by: []
owner:
last_reviewed: 2026-07-24
code_refs:
  [
    deployment-api/deployment_api/scripts/cost_snapshot_worker.py,
    deployment-api/deployment_api/services/cost_observability/snapshot.py,
    deployment-api/deployment_api/services/cost_observability/service.py,
    deployment-api/deployment_api/services/cost_observability/aws_wif.py,
  ]
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
- Credits: the `credits` array carries `type=PROMOTION` / `DISCOUNT` (CUD/SUD/free-tier) as negative amounts. **Net =
  `SUM(cost) + SUM(credits)`** and is what's actually invoiced. Promo credits are **still active** (~$2.5k/30d as of
  2026-07-08, mostly `PROMOTION`) — an earlier "exhausted ~2026-06-20" note was **wrong**; `cost` is the pre-credit
  usage/list cost, net is real spend. The `/api/costs` consumer sums **net** (`_net(r)=cost+credit`) across every view
  and surfaces `gross`+`credit` on the summary for the "you pay = gross - credits" headline.
- **Currency: this account bills in GBP** (the export's `currency` column = `GBP` on every row — verified 2026-07-09:
  1.79M rows, zero USD, `currency_conversion_rate` 0.74–0.76). So `cost`/`credits` are **pound** amounts. The
  `/api/costs` consumer **converts to USD at query time**: `gcp_facts_sql` divides both `cost` and each row's credit sum
  by `currency_conversion_rate` (the USD→account-currency rate GCP billed at), guarded `IFNULL(NULLIF(rate,0),1)` so a
  USD account / missing rate is a 1.0 no-op, applied **per source row** so each day's exact rate is used
  (`amount / rate` = USD-equivalent list price, verified to the penny vs the live export). This makes `/ops/costs`
  single-currency **USD**, matching the native-USD AWS CUR, so the cross-cloud total is dimensionally valid. NB the page
  reports the **USD list-equivalent** (comparable to AWS), NOT the GBP invoice cash figure. For the invoice tally, the
  summary + breakdown responses ALSO carry `currency` + `*_native` figures (`cost_native`/`gross_native`/`credit_native`
  — the raw pre-conversion GBP for GCP; == the USD values for USD-native clouds), powering the UI's **USD⇄GBP toggle**
  (GCP → native £; AWS stays USD, since its CUR is native USD — `line_item_currency_code=USD`, no conversion column, so
  GBP is not obtainable there without an external FX rate).

```sql
-- per-service per-day (net of credits). NB cost/credits are GBP here — the /api/costs consumer
-- divides each by currency_conversion_rate for USD (see the Currency bullet above).
SELECT FORMAT_DATE('%Y-%m-%d', DATE(usage_start_time)) AS day, service.description AS service,
       ROUND(SUM(cost) + SUM((SELECT IFNULL(SUM(c.amount),0) FROM UNNEST(credits) c)),2) AS net_cost_gbp
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
  on the CUR bucket) attached to roles **`uts-deployment-api-{prod,dev,staging}`**. **`ce:*` DRIFT (verified
  2026-07-08):** `ce:GetCostAndUsage` was **DENIED** for the checked `ikenna-worker` identity, despite the earlier note
  here that the policy includes it. Non-blocking — the `/api/costs` code path is **Athena-only** and never calls Cost
  Explorer (CE was only ever the zero-setup fallback until the CUR landed, which it has). Grant `ce:*` only if a live
  spend-forecast tile is built.

**If the UI is served by a different identity** (e.g. the dashboard Cloud Run compute SA `1060025368044-compute@…`, or a
new AWS task role), grant it the same: GCP dataset-READER + `bigquery.jobUser`; AWS attach `uts-billing-readonly`. The
frontend's own principal additionally needs `athena:StartQueryExecution/GetQueryResults`, `glue:GetTable/GetPartitions`,
and `s3:GetObject` on the CUR + `athena-results/` prefixes (all included in `uts-billing-readonly`).

## Cost of the exports themselves

Negligible: GCP BQ export storage a few cents/mo; AWS CUR = a few Parquet files/day in one S3 bucket + a daily Glue
crawler (about $0.44/crawler-hour, minutes/day) + Athena at $5/TB scanned (a cost dashboard scans MB). Far cheaper than
`GetCostAndUsageWithResources` at $0.01/request for a polling UI.

## Consumer — deployment-api `/api/costs` + the `/ops/costs` UI (2026-07-08)

The exports are consumed by the **cost-observability service** in `deployment-api`
(`deployment_api/services/cost_observability/`), which reads both through the UTL analytics wrappers — **never raw
`boto3`/`google.cloud`**:

- GCP: `get_analytics_client(provider="gcp").execute_query(...)` (returns typed rows).
- AWS: `AWSAnalyticsClient(region="us-east-1", output_bucket="uts-billing-cur-427895769566")` — the CUR/Athena live in
  **us-east-1**, not the app default region; pin both explicitly (the factory's `get_athena_output_bucket()` needs
  `ATHENA_OUTPUT_BUCKET` set, so pass it directly). Athena returns every value as a **string** — costs are coerced to
  float.

Both native schemas are normalized into one `CostRecord`
(`cloud, day, service, resource_id, resource_kind, region, cost, credit, sku, usage_amount, usage_unit, zone, purchase_option, machine_type, vcpu, memory_gb, is_provisional, is_placeholder`).
Per-cloud failure is isolated (one cloud down ≠ blank page). Source table/db/region/bucket are config
(`GCP_BILLING_DATASET/RESOURCE_TABLE`, `AWS_CUR_DATABASE/TABLE/REGION`, `AWS_ATHENA_OUTPUT_BUCKET`), defaulting to the
values above.

**⚠️ SUPERSEDED (2026-07-14) — read path is now snapshot-first, not per-request BQ/Athena.** The line above used to read
"every view derives from a daily-refresh-cached window fetch" — that in-process cache called BigQuery/Athena directly on
every cache-miss, which is what drove `/ops/costs` to +1.9GB RSS / 55–65s cold (98,542 full-grain BQ rows materialized
as Python `CostRecord` objects per window). See § "Cost snapshot — DuckDB over GCS parquet" below for the replacement
architecture and § "AWS Athena credential — WIF, not a stale deploy" for the AWS-side fix shipped in the same pass.

## Cost snapshot — DuckDB over GCS parquet (2026-07-14)

Root cause + option analysis: `deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` § 4b. Chosen design
(Option B over a coarse-BQ-query alternative) — reuses two patterns already proven elsewhere in this repo rather than
inventing a third: DuckDB (`unified-trading-library/manifest_consolidator.py`) and the worker→GCS-snapshot shape
(`deployment_api/scripts/data_status_rollup_worker.py`).

- **Snapshot worker** (`deployment-api@d7c0356`, `deployment_api/scripts/cost_snapshot_worker.py`, Cloud Run Job on a
  **~12h** Cloud Scheduler cadence) — for each cloud (GCP/AWS/GitHub) scans the billing export ONCE over the full
  available window (only ~90 days exist in the export; ~168K aggregated rows ≈ ~20–40MB), normalizes to `CostRecord` via
  the same provider adapters the live path used, and writes one parquet per cloud to
  `gs://unified-deployment-state-{project}/cost-snapshots/{cloud}.parquet` (deployment-api's existing state bucket — no
  dedicated cost bucket). Per-cloud isolation: one cloud's snapshot failing (e.g. AWS pending its perms fix, below)
  never blocks another cloud's write.
- **Read path** (`CostObservabilityService._load_window_table`, `services/cost_observability/service.py`) —
  **snapshot-first, live-fallback**: `_snapshot_table()` downloads the small per-cloud parquet(s) via
  `CostSnapshotStore` (`services/cost_observability/snapshot.py`), refreshing them from GCS if stale
  (`store.ensure_fresh()`), and answers the request via a **DuckDB** `GROUP BY` over the in-memory Arrow table — no
  BigQuery/Athena scan, no Python row materialization, a ~3MB local read instead of a 55–64s remote query. Falls through
  to the live BQ/Athena providers only when no snapshot is present yet (fresh deploy, unprovisioned bucket, or any
  snapshot/DuckDB read error — degrades to live, never a 5xx) or in `is_mock_mode()`. This is why the summary /
  breakdown / timeseries endpoints below stayed unchanged — the swap is entirely inside `_load_window_table`, every view
  still calls the same `_window_table()` → DuckDB `aggregate_arrow()` shape it always did, just over a snapshot-backed
  table instead of a live-query-backed one.
- **Why this fixes the memory number**: the 1.9GB RSS was **6 overlapping day-windows** (7/30/90 × current+prior) each
  separately materialized as ~2KB-class Python `CostRecord` objects (6 × ~168K rows × ~2KB ≈ ~2GB). One ~30MB parquet,
  queried per-window via DuckCB `GROUP BY`, never materializes the raw rows in Python at all — every window is a cheap
  re-filter of the same in-memory table.

## AWS Athena credential — WIF, not a stale deploy (2026-07-14)

AWS cost data showed correctly when queried locally but returned nothing from the deployed service ("1 cloud" on the
health tile). **Root-caused precisely, not assumed**: `AWSAnalyticsClient._boto3_client` (`unified-trading-library`)
used a bare `boto3.Session()` — there is no ambient AWS credential source in a GCP Cloud Run container at all, so every
Athena call failed silently in prod regardless of IAM grants or deploy freshness.

Fixed (`deployment-api@d8add54` + `fc53899`) by mirroring the already-proven keyless GCP→AWS WIF pattern this repo uses
for the CodeBuild reader (`_code_builds_aws.py::_assume_codebuild_reader_role`) —
`deployment_api/services/cost_observability/aws_wif.py`, config field `aws_athena_reader_role_arn` / env
`AWS_ATHENA_READER_ROLE_ARN`, threaded through `aws_facts(...)` into the Athena client. A new scoped AWS IAM role was
provisioned to receive it: `arn:aws:iam::427895769566:role/gcp-cloudrun-athena-cost-reader` (read-only; trusts the same
`unified-trading-sa` GCP SA the CodeBuild reader already trusts; scoped to exactly the CUR data + `uts-billing`
workgroup + results bucket). Wired into the Cloud Run deploy env via `cloudbuild.yaml`'s
`--update-env-vars WORKERS=2,AWS_ATHENA_READER_ROLE_ARN=...`.

`sku` / `usage_amount` / `usage_unit` come straight from each export — GCP `sku.description` +
`usage.amount_in_pricing_units` + `usage.pricing_unit`; AWS `line_item_usage_type` (as `sku`) +
`SUM(line_item_usage_amount)` (AWS has no separate pricing-unit column, so `usage_unit` is `""` for AWS records). A
`sku` breakdown dimension groups by `(cloud, service, sku)` — this surfaces the actual top cost driver inside a service
(e.g. GCS Coldline Class-A ops) that the service-level rollup hides. **Unit economics (2026-08-10, batch2):**
sku-dimension rows now additionally carry `cost_per_unit` (`net / summed usage_amount`, populated only where the group
bills in ONE unit — e.g. `$/GB-month`, `$/vCPU-hour`) for the sortable "Usage + $/unit" columns in the UI. Buckets were
already covered by `storage_gb`/`cost_per_gb` + `cost_by_component` (GB-stored vs GB-egress).

**Endpoints** (`routes/costs.py`, mounted `/api`, auth + rate-limited):

| Endpoint                    | Params                                                                                                                                                                               | Returns                                                                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `GET /api/costs/summary`    | `days`, `refresh`                                                                                                                                                                    | **net** total (+ `gross`/`credit`/`discount_rate_pct`) + per-cloud net/gross/credit/deltas/daily sparkline + `provisional_days` |
| `GET /api/costs/breakdown`  | `dimension=service\|resource\|bucket\|region\|day\|sku\|zone\|label`, `cloud`, `days`, `refresh`, `label_key` (`purpose\|category\|venue\|asset_group`, only when `dimension=label`) | grouped rows — full field set above                                                                                             |
| `GET /api/costs/timeseries` | `days`, `cloud`, `refresh`                                                                                                                                                           | daily per-cloud series (stacked trend)                                                                                          |

`cost_obs_backend_sku_usage_enrichment_2026_07_08.md` is now fully shipped — every field below has landed; the sibling
UI plan (`cost_obs_ui_unified_breakdown_2026_07_08.md`) builds the breakdown-table UI against this contract.

**`BreakdownRow` — full field set** (`services/cost_observability/models.py`): every row carries `label`, `cloud`,
`cost` (**net** — primary, matches the summary net total), `gross` (Σcost before credits), `credit` (Σcredit, ≤ 0;
`cost == gross + credit`), `detail`, `resource_kind`, `share_pct`, `is_provisional`. Plus, populated where the axis
applies (`None`/`""`/`0` when it doesn't):

- `is_idle` + `waste_kind` (`""` | `idle_static_ip` | `orphaned_disk` | `idle_elastic_ip`) — cost-waste flags, resource
  dimension only, from `services/cost_observability/waste.py`. GCP `Static Ip Charge` SKU = idle (distinct SKU from
  in-use `External IP Charge on a Standard VM`, so no cross-ref needed); GCP `… PD Capacity` disk SKUs are
  cross-referenced against the live running-VM fleet (`vm_utils.list_running_vm_names`) — a disk with no matching
  running VM is `orphaned_disk`. AWS `…ElasticIP:IdleAddress` usage-type = `idle_elastic_ip`. AWS orphaned-EBS is
  **not** flagged (no AWS instance/volume-attachment API integration to cross-ref against — dropped, not fabricated).
- `storage_gb` / `storage_class_gb` (`{"Standard"|"Nearline"|"Coldline"|"Archive": gb}`) / `cost_per_gb` — `bucket`
  dimension rows only, derived from the storage-volume SKUs' `usage_amount` (GiB/GB-month → average GB over the window).
  **GB only, never raw bytes**; no object count or soft-delete split (not billable, absent from the export).
- `usage_amount` / `usage_unit` / `cost_per_unit` — `sku` dimension rows only (2026-08-10, batch2): the summed
  usage-quantity + its billing unit + net-per-unit (`$/GB-month`, `$/vCPU-hour`), backing the sortable Usage + $/unit
  columns in the UI. Populated only where the group bills in ONE unit; `None`/`""`/`0` otherwise.
- `purchase_option` (`spot` | `on-demand` | `other`) — derived from the GCP SKU text (`Spot Preemptible …`) / AWS
  purchase-option marker, not a billed-export column; `other` covers non-compute SKUs where the axis doesn't apply.
- `machine_type` / `vcpu` / `memory_gb` — VM rows only, parsed from the GCP billing `system_labels`
  (`compute.googleapis.com/machine_spec` / `cores` / `memory`, the latter MiB → GB) via `ANY_VALUE(...)` in
  `gcp_facts_sql` — **no Compute API call**. AWS has no machine-spec system_labels equivalent — left unset.
- `labels` (`dict[str, str]`) — the business-label subset (`purpose`/`category`/`venue`/`asset_group`) extracted from
  the GCP `labels` REPEATED field via `_label_col()` in `gcp_facts_sql`; backs the `label` breakdown dimension (grouped
  by `labels[label_key]`, `"(unlabeled)"` when the key is absent). AWS/GitHub rows carry no business labels today.

**AWS net + invoice reconciliation**: `aws_facts_sql` sums `line_item_net_unblended_cost` (net of RI/SP discounts, not
list-price `line_item_unblended_cost`) and the line-item-type filter is now `('Usage', 'DiscountedUsage', 'Tax', 'Fee')`
(was `Usage`/`DiscountedUsage`-only) so the AWS total tracks the invoice including tax/fee lines.

A `zone` breakdown dimension slices by GCP `location.zone` / AWS `line_item_availability_zone` — finer than `region`.

A `label` breakdown dimension groups by a chosen business label (`label_key` ∈ `purpose|category|venue|asset_group`) off
the GCP `labels` map — spend by purpose / venue / asset_group; rows with no such label roll into `"(unlabeled)"`. Today
`purpose` (~49%) and `category` (~24%) have useful coverage; `asset_group` is ~0.16% until launchers stamp it.

- **UI**: `deployment-ui/src/pages/CostObservability.tsx` at route **`/ops/costs`** (Cockpit tile "Billing
  (GitHub+GCP+AWS)") — a 2-column top (bigger daily trend chart on the left; the total-spend card with the cloud-share
  donut folded in + the 3 per-cloud cards on the right), then the dimension breakdown table (per-column header-filter
  dropdowns, click-to-sort, 100/page pagination, drag-resize), then per-VM/per-bucket/**Other-resources** leaf tables
  (2026-08-10, batch2: the third leaf pins `resource_kind=other` — Cloud Run Jobs, build workers, … — which was only
  surfacing inside the "By resource" rollup before). A `?` help button opens a quick-guide dialog. Recent days flagged
  **provisional** — GCP ~2-day reconcile (trailing-2-days provisional, unchanged); **AWS provisional cutoff is the FIRST
  of the current month** (AWS re-trues the whole current month on the 6th–7th, so early-current-month AWS days are
  provisional until then; made cloud-aware 2026-08-10, batch2). The note now lives in the help guide (no standing page
  banner). The per-cloud cards render an "≈ X% off" chip — `discount_rate_pct` = |credit|/gross on
  `CloudSummary`/`SummaryResponse`, surface of the gross → credits → net derivation.
- **GitHub**: **real** provider — `fetch_github_billing()` (`services/cost_observability/github_billing.py`) reads the
  Enhanced Billing usage API (`GET /users|organizations/{account}/settings/billing/usage`) with a **Plan-scoped** token
  from Secret Manager (`github_billing_secret`, default `github-billing-token`, then the shared `GH_PAT`); each usage
  line item → `CostRecord` (`cost`=gross, `credit`=net−gross, so net=cost+credit). Falls back to the labelled **dummy**
  (`is_placeholder=true`) only when no Plan-scoped token is reachable (every billing endpoint 403s without the `Plan`
  permission). Verified 2026-07-10: backend net reconciles to the raw GitHub-API net to the cent ($1,332.55 / 30d).
- The narrow self-reported `cost_summary`-blob pipeline (`routes/cost_daily.py`, `/api/costs/daily`) that previously
  backed this page is **retired/deleted**; the health-overview cost tile now reads `summarize(days=1)`.

## Related

- [`spot-vms-for-backfill.md`](spot-vms-for-backfill.md) ·
  [`aws-cloudtrail-cost-optimization-2026-06-20.md`](aws-cloudtrail-cost-optimization-2026-06-20.md) — the cost work
  these exports made measurable.
- [`aws-iam-matrix.md`](aws-iam-matrix.md) — AWS IAM principals.
