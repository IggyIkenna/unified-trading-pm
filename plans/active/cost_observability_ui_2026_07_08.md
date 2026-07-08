---
doc_type: plan
title: Cost Observability UI — comprehensive GCP + AWS billing breakdown on /ops/costs
summary:
  Replace the narrow self-reported VM cost_summary pipeline behind /ops/costs with a comprehensive cost-monitoring tool
  driven by the real billing exports — GCP BigQuery billing_export and AWS CUR→Athena (aws_billing.cur_uts_cost_usage).
  High-level total → per-cloud → per-service → per-day → per-resource/bucket, on data we fully have today. GitHub
  renders dummy data until a billing PAT lands; business-context (asset_group/archetype) is a tracked fast-follow.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-trading-library]
scope: [engineer]
tags: [billing, cost, observability, bigquery, athena, cur, deployment-ui, cockpit]
related: [billing-cost-observability.md]
created: "2026-07-08"
last_updated: "2026-07-08"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
assigned_role: ui-developer
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Cost Observability UI — comprehensive GCP + AWS billing breakdown on /ops/costs

> **LOCAL / human plan** (`assigned_vm: NA`) — driven hands-on in a slot-4 interactive session, not AO-dispatched.
> Operator decisions captured 2026-07-08: (1) human plan; (2) build GCP + AWS live now, GitHub renders **dummy data**
> until a billing PAT + permission land, then swap to real APIs; (3) **pure infra-billing for v1** — business-context
> (spend-by-asset_group / strategy archetype) is a tracked fast-follow, not v1.

## Context — what exists, what's ready, what's being replaced

**The page already exists but is narrow.** `/ops/costs` → `deployment-ui/src/pages/DailyCosts.tsx`, backed by
`deployment-api/deployment_api/routes/cost_daily.py` (`GET /api/costs/daily`). That route reads **self-reported**
`cost_summary` JSONL blobs that our own VM launch scripts write to `gs://{pid}-deployment-events/cost_summary/{date}/`.
Limitations that motivate this rebuild: single date only · GCP VMs only (no AWS, no storage/build/other services, no
buckets) · the numbers are a launch-script **estimate**, not real billing · no per-service, per-region, or time-series
view. Per operator direction this narrow pipeline is **removed**, not extended.

**Both real backends are provisioned and verified** (see the codex SSOT — do not duplicate its IAM/provisioning detail
here):

- **GCP** — BigQuery billing export,
  `central-element-323112.billing_export.gcp_billing_export_resource_v1_016B25_109840_AF2ACB` (resource-level: has
  `resource.name` for per-VM / per-bucket). Verified live: per-day × service × sku × resource × region × credits. Query
  cost is fractions of a cent (1 TiB/mo free). **Gotcha:** ingestion-time partitioned on `_PARTITIONTIME`, NOT
  `usage_start_time` — filter on BOTH or partition pruning doesn't happen (~4× bytes). Last ~2 days are **provisional**
  (Google reconciles credits/CUD for ~2 days after usage).
- **AWS** — CUR→S3→Athena. Workgroup `uts-billing`, db `aws_billing`, table `cur_uts_cost_usage` (146 cols;
  `line_item_resource_id` gives per-EC2-instance / per-S3-bucket). Verified live via `harsh-worker`: per-service/day,
  per-resource, per-bucket all return real numbers. Athena has **no free tier** (billed per byte from query 1) — so
  avoiding per-page-load re-queries matters more here than on GCP. Current-month rows are estimates; AWS re-trues on the
  6th–7th of the following month.

**Sanctioned integration points already in the codebase** (reuse, don't reinvent):

- GCP BigQuery — deployment-api already queries BQ in `deployment_api/services/data_status_drilldown/` +
  `routes/data_status/_downloads.py`; UTL BQ plumbing in `unified_trading_library/io/connection_pool.py`. First backend
  task confirms the exact read helper.
- AWS Athena/Glue — UTL `unified_trading_library/cloud_interface/providers/aws.py:744` `AWSAnalyticsClient`
  (`_boto3_client("athena")` / `"glue"`, StartQueryExecution → `s3://{bucket}/athena-results/`) + exported
  `AthenaDataSink`. **Use this, never raw boto3** (QG ban). `get_athena_output_bucket()` must reconcile with the
  `uts-billing` workgroup's output location — verify / fix in the AWS reader task.
- Deployed AWS credentials — keyless GCP→AWS WIF precedent in `deployment_api/routes/_code_builds_aws.py`
  (`assume_role_with_web_identity` vs `AWS_CODEBUILD_READER_ROLE_ARN`). Local dev uses the ambient `harsh-worker`
  profile / gcloud ADC; the deployed cutover is a fast-follow (see Deferred), not a v1 blocker per the local-first goal.
- UI entry point — the Cockpit tile is **already** `Billing (GitHub+GCP+AWS)` → `/ops/costs` (`Cockpit.tsx:191`).
  recharts precedent: `deployment-ui/src/components/DeploymentFrequencyChart.tsx`.

## Design decisions (recommendations — challenge before building)

1. **Daily-refreshed server-side cache, not live-query-per-load.** Cost data is inherently ~daily-lagged (GCP ~2-day
   reconciliation, AWS ≤3×/day), so live-querying on every page load adds latency + Athena cost with **zero** freshness
   benefit. Cache normalized results with a short TTL + an explicit "Refresh" that forces a re-query. This is the single
   most important structural choice — it makes the Athena-no-free-tier economics a non-issue.
2. **One normalized cross-cloud cost record** —
   `{cloud, service, day, resource_id, resource_kind, region, cost_usd, credit_usd, is_provisional, is_placeholder}` —
   with a per-cloud adapter mapping native schema → this shape. The UI stays cloud-agnostic; adding GitHub (or a 4th
   cloud) is a provider swap, not a UI change.
3. **Layout: high-level first, then drill.** Top = KPI band (total for range, per-cloud split donut, trend area chart,
   top-N movers, provisional badge). Middle = dimension-switchable breakdown (by service / resource / bucket / region /
   day) with a per-cloud filter and service→resource drill. Bottom = granular leaf tables (per-VM, per-bucket). A global
   time-range selector (presets + custom) drives every panel — replacing today's single-date input.
4. **GitHub = dummy data now, honestly labeled.** Same normalized shape, `is_placeholder=true`, a visible "placeholder —
   real billing pending GitHub PAT" banner. Swapping to the real Enhanced Billing API later touches only the provider.
5. **Provisional-data honesty** (mirrors the data-correctness honesty rule): visibly flag GCP's last ~2 days and AWS's
   current month as estimates rather than presenting them as final.

## Available query dimensions (what the data actually supports)

Both exports support, per day: **service**, **resource_id** (VM / bucket / other), **resource_kind**, **region/zone**,
**credits/discounts**, **effective-vs-list price**. GCP additionally carries `labels` / `system_labels` /
`project.labels` and AWS carries `line_item_resource_id` + ~70 `product_*` descriptor columns — the raw material for the
business-context fast-follow (asset_group via labels/tags), deliberately out of v1 scope.

## Codex SSOTs (read before touching the relevant task — plan references, does not duplicate)

- `codex/05-infrastructure/billing-cost-observability.md` — GCP BQ export + AWS CUR/Athena backends, table names,
  workgroup, and the read-only IAM grants. **Authoritative for the backends.** Post-Phase-C audit updates it with the UI
  consumer + endpoint contract.
- `codex/06-coding-standards/ui-testing-layers.md` — the Playwright L2 gate (no `[UI]` tick without `pw:L2 ✓` + a cited
  regression spec).
- `codex/06-coding-standards/` — no raw `boto3` / `google.cloud` (use UTL wrappers), no `os.getenv`, UTC datetimes.

---

## Phase A — Backend data + API foundation

- [x] [BACKEND] P0. GCP cost reader — query the resource-level billing export for per-day × service × sku × resource ×
      region × credits; filter on BOTH `_PARTITIONTIME` and `usage_start_time` (partition-prune); flag last ~2 days
      `is_provisional`. Follow the existing BQ read pattern in `data_status_drilldown/` (confirm the exact helper).
- [x] [BACKEND] P0. AWS cost reader via UTL `AWSAnalyticsClient` (`cloud_interface/providers/aws.py:744`) against
      workgroup `uts-billing` / db `aws_billing` / table `cur_uts_cost_usage` — per-day × service ×
      `line_item_resource_id` × region, `line_item_line_item_type IN ('Usage','DiscountedUsage')`. Reconcile
      `get_athena_output_bucket()` with the `uts-billing` output location (fix if mismatched). No raw boto3.
- [x] [BACKEND] P0. Normalized cross-cloud cost record + per-cloud adapters (GCP, AWS) mapping native → the common shape
      (`cloud, service, day, resource_id, resource_kind, region, cost_usd, credit_usd, is_provisional, is_placeholder`).
- [x] [BACKEND] P0. Retire the narrow pipeline — delete `routes/cost_daily.py` (`/costs/daily` + the GCS `cost_summary`
      reads) and drop it from `main.py`; migrate nothing the new `/breakdown` doesn't already cover. No shims (delete
      deprecated code).
- [x] [BACKEND] P1. Daily-refreshed server-side cache (short TTL + explicit force-refresh) wrapping both readers — the
      Design-Decision-1 rationale; avoids per-load Athena/BQ scans.
- [x] [BACKEND] P1. New `/api/costs` routes with Pydantic models: `/summary` (KPIs + per-cloud totals + trend),
      `/breakdown` (`dimension=service|resource|bucket|region|day`, `cloud=`, `from=`, `to=`), `/timeseries` (daily
      series per cloud/service). Rate-limited like the existing cost route.
- [x] [BACKEND] P2. GitHub dummy-data provider emitting the normalized shape with `is_placeholder=true` so the UI
      renders a third cloud immediately (swap-to-real is a later provider change only).

## Phase B — Frontend rebuild of /ops/costs

- [x] [UI] P1. `deploymentApi.ts` — client funcs + types for `/api/costs/{summary,breakdown,timeseries}`; remove
      `fetchDailyCosts` + `DailyCost*` types.
- [x] [UI] P1. High-level overview band — total spend for range, per-cloud split donut, spend trend (recharts area;
      follow `DeploymentFrequencyChart.tsx`), top-N movers, a provisional-data badge.
- [x] [UI] P1. Global time-range selector (7 / 30 / 90d presets + custom range) replacing the single-date input; wire it
      to every panel.
- [x] [UI] P1. Dimension-switchable breakdown — by service / resource / bucket / region / day, with a per-cloud filter
      and a service→resource drilldown; sortable + searchable tables.
- [x] [UI] P2. Granular leaf tables — per-VM (GCE + EC2) and per-bucket (GCS + S3), cost desc, searchable.
- [x] [UI] P2. GitHub section rendering the dummy provider behind a visible "placeholder — real billing pending GitHub
      PAT" banner.
- [x] [UI] P2. Rebuild `DailyCosts.tsx` → a `CostObservability` page composing the above — loading / error / empty
      states, responsive, theme-aware; keep the `/ops/costs` route + the existing Cockpit tile.

## Phase C — Tests, verify, docs

- [x] [BACKEND] P1. pytest for the readers + normalization + cache (mock BQ / Athena responses; assert provisional
      flags, dimension aggregation, cache hit/refresh).
- [x] [UI] P1. Vitest for the new components + client, and a **Playwright L2** regression spec driving the page against
      the mock API (UI gate: `pw:L2 ✓` + cite the spec path on the tick).
- [x] [REVIEW] P2. Verify end-to-end locally against REAL data (page on :5183; confirm GCP + AWS totals match direct
      `bq` / Athena queries; screenshot). Then the post-phase codex audit — update `billing-cost-observability.md` with
      the UI consumer + `/api/costs` contract.

## Deferred / fast-follow (tracked — not v1)

- [ ] [BACKEND] P3. _(fast-follow, operator-deferred 2026-07-08)_ Business-context enrichment — derive asset_group /
      archetype from GCP `labels`/`system_labels` + AWS resource tags → a spend-by-strategy view (restores and
      generalizes what the retired narrow page showed).
- [ ] [BACKEND] P3. `BLOCKED-CREDENTIALS` GitHub real billing — replace the dummy provider with the Enhanced Billing API
      (`GET /organizations/{org}/settings/billing/usage` or the user endpoint) once a **classic PAT with `user` scope**
      exists. Unblocks the moment the token lands.
- [ ] [BACKEND] P3. Deployed AWS-credential cutover — wire the Athena reader to the keyless WIF role
      (`_code_builds_aws.py` precedent) so the Cloud Run deployment reaches Athena without a static key. Local dev uses
      the ambient profile; this is only needed at deploy time.

## Progress Log

_(Session findings go here — agent memory writes are BANNED. Append dated notes as work proceeds.)_

- 2026-07-08 — Plan authored (slot 4). Backends verified live earlier this session: GCP BQ resource-level export + AWS
  CUR/Athena (`cur_uts_cost_usage` created via a manual crawler run, real per-service/resource/bucket queries returned
  as `harsh-worker`). `harsh-worker` IAM confirmed sufficient for Athena/Glue/S3; `harshkantariya@odum-research.com`
  reaches the GCP export via project `editor`/`viewer` → `projectReaders`. Tab-4 repos confirmed at LDR head before
  authoring.
- 2026-07-08 — **Phase A/B/C SHIPPED (first pass).** Both code repos landed on `live-defi-rollout` via quickmerge, each
  from a `quality-gates.sh`-green tree:
  - **deployment-api@`bdf6c81`** — `services/cost_observability/` (models/queries/providers/cache/service) +
    `routes/costs.py` (`/api/costs/{summary,breakdown,timeseries}`); retired `cost_daily.py`; migrated the
    health-overview cost tile to `summarize(days=1)`. Reads both exports via UTL `get_analytics_client` +
    `AWSAnalyticsClient(us-east-1, CUR bucket)`. Tests: `test_cost_observability.py` 11/11. Full backend QG green.
  - **deployment-ui@`cd5d33b`** — `pages/CostObservability.tsx` (KPI band, recharts trend + donut, dimension breakdown,
    per-VM/per-bucket leaf tables, GitHub dummy) + range/cloud filters + sortable tables; `deploymentApi.ts` client;
    mock-api handlers; replaced `DailyCosts`. Tests: vitest 4/4 + Playwright L2 `cost-observability.spec.ts` 4/4. Full
    UI QG green.
  - **e2e verified** against REAL data on `:5183` (both themes, 0 console errors): GCP Cloud Run/Compute/Storage, AWS
    EC2/EKS, real VM ids + bucket names, GitHub dummy flagged.
  - Codex SSOT `billing-cost-observability.md` updated with the consumer + `/api/costs` contract (post-Phase-C audit).
  - Gate-surfaced coding-standard fixes (not bypassed): schema-provenance `# CORRECT-LOCAL` on `CostRecord`; bandit B608
    `# nosec` on the SQL builders; DTZ `date.today()`→`datetime.now(UTC).date()` (ratchet 12→11); de-hardcoded mock
    project id.
  - **Still open (Deferred, intentional):** business-context enrichment; GitHub real billing (`BLOCKED-CREDENTIALS` —
    needs a classic PAT `user` scope); deployed-AWS keyless-WIF credential cutover.
