---
doc_type: plan
title: Cost Observability UI — comprehensive GCP + AWS billing breakdown on /ops/costs
summary:
  Replace the narrow self-reported VM cost_summary pipeline behind /ops/costs with a comprehensive cost-monitoring tool
  driven by the real billing exports — GCP BigQuery billing_export and AWS CUR→Athena (aws_billing.cur_uts_cost_usage).
  High-level total → per-cloud → per-service → per-day → per-resource/bucket, on data we fully have today. GitHub
  renders dummy data until a billing PAT lands; business-context (asset_group/archetype) is a tracked fast-follow.
status: superseded
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-trading-library]
scope: [engineer]
tags: [billing, cost, observability, bigquery, athena, cur, deployment-ui, cockpit]
related:
  [
    /codex/05-infrastructure/billing-cost-observability.md,
    /plans/archive/2026_07/cost_obs_backend_sku_usage_enrichment_2026_07_08.md,
    /plans/archive/2026_07/cost_obs_ui_unified_breakdown_2026_07_08.md,
  ]
created: "2026-07-08"
last_updated: "2026-07-09"
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
superseded_by: [cost_obs_backend_sku_usage_enrichment_2026_07_08.md, cost_obs_ui_unified_breakdown_2026_07_08.md]
source:
---

# Cost Observability UI — comprehensive GCP + AWS billing breakdown on /ops/costs

> **📦 ARCHIVED 2026-07-10.** Superseded (see below); all 7 deferred follow-ups migrated to
> `plans/active/issues/cost_observability_deferred_followups_2026_07_10.md` (0 open todos remain here). Moved to
> `plans/archive/2026_07/`.

> **⏩ SUPERSEDED 2026-07-08 — the remaining build is now two AO-dispatched plans:**
> **`cost_obs_backend_sku_usage_enrichment_2026_07_08.md`** (backend-engineer, active) +
> **`cost_obs_ui_unified_breakdown_2026_07_08.md`** (ui-developer, draft-gated on the backend). **RETAINED as the
> verification checkpoint** — when the workers finish we reconcile their output against the design + evidence here (the
> audit findings, the live `bq` probes, the enrichment spec) and fix any residual gaps in the code. **NOT carried by the
> AO plans (still live here):** the GitHub real-billing PAT (BLOCKED-CREDENTIALS), the AWS WIF deploy-time cutover, and
> the business-context / asset_group fast-follow — re-home these to a new plan when picked up. Everything already
> shipped below (Phase A/B/C + the net-of-credits P1 fix) stays done.

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

- `/codex/05-infrastructure/billing-cost-observability.md` — GCP BQ export + AWS CUR/Athena backends, table names,
  workgroup, and the read-only IAM grants. **Authoritative for the backends.** Post-Phase-C audit updates it with the UI
  consumer + endpoint contract.
- `/codex/06-coding-standards/ui-testing-layers.md` — the Playwright L2 gate (no `[UI]` tick without `pw:L2 ✓` + a cited
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
- [x] [UI] P1. High-level overview band — total spend for range, per-cloud split donut, spend trend (custom SVG
      stacked-area with crosshair + tooltip), top-N movers, a provisional-data badge.
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

> **🔄 SUPERSEDED + RECONCILED 2026-07-10 (cross-plan audit).** `status: superseded` →
> `[cost_obs_backend_sku_usage_enrichment_2026_07_08, cost_obs_ui_unified_breakdown_2026_07_08]` (both COMPLETE). This
> doc had **20 open** todos while the work had already shipped in the successors — a false-progress hazard. **11 were
> verified done + flipped** above with the successor sha. The **8 boxes still open** are the genuine residual, and
> split:
>
> - **Real-but-deferred (3):** `183` business-context spend-by-strategy view · `191` AWS-credential WIF cutover
>   (deploy-time only) · `288` AWS Athena CUR historical backfill (P2 investigation).
> - **Low-value nice-to-haves (5):** `221` AWS provisional-flag month-aware · `232` credits-first-class-view
>   (gross/credit/net already shipped; only the effective-discount-rate residual) · `234` usage quantity+unit · `240`
>   cheaper standard table (explicitly "revisit only if needed") · `243` "other resources" leaf.
>
> **Open question for the operator:** migrate the 3 real ones to a small `plans/active/issues/` fast-follow doc (and
> drop the 5 nice-to-haves), or leave them parked here under this banner? Not decided unilaterally — where residual work
> lives is your call.

## Deferred / fast-follow (tracked — not v1)

- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [BACKEND] P3. _(fast-follow,
  operator-deferred 2026-07-08)_ Business-context enrichment — derive asset_group / archetype from GCP
  `labels`/`system_labels` + AWS resource tags → a spend-by-strategy view (restores and generalizes what the retired
  narrow page showed).
- [x] ✅ [BACKEND] P3. GitHub real billing — **NOW LIVE** (see the done `[BACKEND+UI] P1` in the "GitHub real billing"
      subsection below, deployment-api@29a18c088/@c4549daa; token in Secret Manager). Superseded the dummy provider with
      the Enhanced Billing API (`GET /organizations/{org}/settings/billing/usage` or the user endpoint) once a **classic
      PAT with `user` scope** exists. Unblocks the moment the token lands. → **2026-07-10** — re-tracked as a P1 in the
      "GitHub real billing & GCP Pacific-day alignment" subsection below; the token in hand is a fine-grained PAT
      **without** billing/`Plan` scope (403 on every billing endpoint), so still credential-blocked pending a
      Plan-scoped token.
- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [BACKEND] P3. Deployed
  AWS-credential cutover — wire the Athena reader to the keyless WIF role (`_code_builds_aws.py` precedent) so the Cloud
  Run deployment reaches Athena without a static key. Local dev uses the ambient profile; this is only needed at deploy
  time.
- [x] ✅ [UI] P3. _(found 2026-07-08 during the row-cap fix)_ Breakdown stale-during-refetch — _(SHIPPED →
      cost_obs_ui_unified_breakdown, stale-during-refetch fix)_ switching dimension+range quickly on the slow real
      backend briefly renders the previous fetch's rows under the new column header (e.g. service rows under a "Day"
      header). Gate the table body on `breakdown.dimension === dimension` (+ matching days), or skeleton the panel while
      `loadBreakdown` is in flight. Pre-existing; cosmetic-only (self-corrects on fetch completion).

## Data-fidelity audit findings (2026-07-08) — UI vs BigQuery/Athena source

Operator-requested audit: what the exports actually contain vs what `/ops/costs` surfaces. Evidence = live `bq` probes
on the resource table + the running backend endpoints (last-30d window).

### Correctness (the displayed numbers are wrong today)

- [x] ✅ [BACKEND+UI] P1. **GCP showed GROSS, not NET of credits — FIXED.** `credit` was fetched into `CostRecord`
      (`providers.py:96`) but **never read** — every aggregation summed `r.cost`. Live proof (resource table, last 30d):
      gross **$15,134.51** − credits **$2,541.19** = net
      **$12,593.32** → page had **overstated GCP ~17%**; credits are
      mostly **active PROMOTION** (−$2,487/30d), so
      the codex "promo exhausted ~2026-06-20" note was stale. Fix: `_net(r)=cost+credit` summed across summary /
      breakdown / timeseries; `SummaryResponse`+`CloudSummary` expose `gross`+`credit`; the KPI band leads with net + a
      "(gross − credits)" derivation (GCP tiles + grand; AWS/GitHub have none). Corrected the codex note.
      **deployment-api@`f10b0914`** + **deployment-ui@`0f653068`** — both full QGs green (backend pytest incl. a
      credit-netting test; vitest 911 + a pw:L2 derivation regression); live `:5183` net
      **$12,593.31** reconciles to the bq probe **$12,593.32**.
- [x] ✅ [BACKEND] P2. **AWS shows unblended usage-only, not net / not invoice-total.** _(SHIPPED →
      **deployment-api@`f914cc4`** — AWS now reports net-of-credits with Tax/Fee/Credit line-items. NB the earlier
      `301ccfc` net_unblended_cost + invoice-reconciliation attempt was **REVERTED** — that column is absent from this
      CUR's crawler schema and silently zeroed the AWS tab; `f914cc4` is the live fix)_ `aws_facts_sql` sums
      `line_item_unblended_cost` and filters `line_item_type IN ('Usage','DiscountedUsage')` — excludes Tax / Credit /
      Fee / RIFee / SavingsPlan\* and ignores `line_item_net_unblended_cost`. So the AWS total
      (~$213/30d) is usage
      spend, not the AWS invoice. Decide net-of-discounts (`net_unblended_cost`) + a tax/fee line so it reconciles; at
      minimum label it "usage spend". (AWS is ~1.4% of total, so lower $
      impact than the GCP item.)
- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [BACKEND] P3. **Provisional
  flag is trailing-2-days for BOTH clouds**, but AWS re-trues the whole current month (6th–7th). Early-current-month AWS
  days render as final though they aren't — make the AWS cutoff month-aware.

### Granularity we HAVE but don't surface (near-zero extra query cost)

- [x] ✅ [UI+BACKEND] P2. **SKU (GCP) / usage_type (AWS) breakdown dimension** _(SHIPPED → backend@9b4e59d +
      UI@0d33ef0)_ — highest-value add. The #1 GCP line item is "Regional Coldline Class A Operations **$2,870/30d**",
      invisible today inside "Cloud Storage"; SKU is the "why is this service expensive" axis. Resource table already
      carries `sku.description`; AWS has `line_item_usage_type`. Add as a 6th breakdown dimension.
- [x] ✅ [UI+BACKEND] P2. **Spot vs On-Demand (purchase option) split** _(SHIPPED → backend@947a48b + UI@5b99519)_ — GCP
      SKU exposes "Spot Preemptible E2…"; AWS has `pricing_purchase_option`. Directly validates the
      SPOT-VMs-for-backfill HARD RULE + quantifies the savings.
- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [UI+BACKEND] P3.
  **Credits/discounts as a first-class view** — we already fetch GCP credits; surface gross → credits → net + the
  effective discount rate (how much promo/CUD/SUD is saving).
- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [BACKEND] P3. **Usage
  quantity + unit** (GCP `usage.amount/unit`; AWS `line_item_usage_amount/pricing_unit`) → unit economics
  ($/GB-month,
  $/vCPU-hour), and GB-stored vs GB-egress for buckets.
- [x] ✅ [BACKEND] P3. **Zone (GCP `location.zone`) / AZ (AWS `line_item_availability_zone`)** _(SHIPPED →
      backend@537af3d — zone dimension)_ — finer than region.

### Structural

- [x] 🚫 [BACKEND] P3. **CLOSED — won't-do (operator, 2026-07-10).** Wire the cheaper **standard table**
      (`gcp_billing_export_v1_*`, SKU/project). Its only driver was **per-project**, which is now moot: multi-account /
      multi-org = **separate deployments per account** (the 2026-07-10 decision), NOT an in-app per-project view. SKU is
      already reachable off the resource table (SKU dimension shipped), so the resource table stays the sole source and
      the standard table is not needed.
- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [UI] P3. No **"other
  resources" leaf** — Cloud Run Jobs is ~$2.9k/30d (CPU $2,047 + Mem $882), bigger than any single VM, but only
  vm+bucket leaf tables exist; it surfaces only in the "By resource" breakdown.

### Currency, AWS history & timezone reconciliation (2026-07-09) — UI vs operator-downloaded GCP/AWS console CSVs

Operator (Harsh) reconciled `/ops/costs` against console CSVs pulled direct from the clouds
(`odum_gcp_acc_Reports, 2026-07-03 — 2026-07-09.csv`, GBP; `aws_gross_usage_by_service_jan_jun_2026.csv`, USD). The UI
faithfully mirrors its sources — every GCP per-service figure matches the `bq` probe to the penny — so the gaps are
**source-level, not UI math**. Evidence = live `bq` probes on the resource table + `SHOW COLUMNS`/Athena probes on the
CUR (2026-07-09). Operator decisions captured inline.

- [x] ✅ [BACKEND+UI] P1. **GCP is billed in GBP but the UI prints `$` — convert to USD everywhere.** The BQ export's
      `currency` column = **`GBP`** on all 1.79M rows (last 60d); the pipeline selects `cost` raw with no FX and the
      frontend `usd()` hardcodes `$`, so every GCP figure is a **pound value wearing a dollar sign** (the "GCP
      $12,593/30d" is really £12,593). Proven 3 independent ways: (a) `currency='GBP'`, zero USD rows; (b)
      `currency_conversion_rate` = **0.7413–0.756** (≠ 1.0 ⇒ non-USD account); (c) currency-blind — Coldline Iowa unit
      cost £0.002956 vs GCP's public USD list $0.004
      = ratio 0.739, matching the rate column. AWS is USD (`line_item_currency_code=USD`; 157 CUR columns, **none** a
      conversion rate), so today's cross-cloud grand total **sums GBP + USD under one `$`** = invalid. **FIX — convert
      GCP→USD at query time using GCP's OWN embedded per-day rate (no external FX feed):** in `gcp_facts_sql`,
      `cost`→`SUM(SAFE_DIVIDE(cost,     currency_conversion_rate))`and the credit line divides the`UNNEST(credits)`sum
      by the same outer-row`currency_conversion_rate`; usage amounts untouched; AWS/GitHub paths unchanged. Verified:
      Jul3–9 gross £2,708.12 → **$3,581.93** (rate 0.756), flows     per-service (Cloud Run £1,264.84→$1,672.96). Whole
      page becomes genuinely USD → the `$`label +`usd()`become correct and the cross-cloud total valid. Add a unit test
      asserting the`/rate`split; update `/codex/05-infrastructure/billing-cost-observability.md` (GCP GBP-native, USD at
      query time). NB reports the **USD list-equivalent** (comparable to AWS), NOT the GBP invoice cash figure. - ✅
      **2026-07-10 — deployment-api@`782c988`.** `gcp_facts_sql` now divides both `cost` and each row's credit sum by
      `IFNULL(NULLIF(currency_conversion_rate, 0), 1)` (per-source-row, guarded no-op for a USD account); usage
      untouched. Verified vs live BQ for the current window to the penny: backend GCP gross
      **$2,978.18** =
        `SUM(cost/rate)`, credit **−$1,719.36**, net
      **$1,258.82** (usd_per_gbp = 1.3227). Unit test
        `test_gcp_facts_sql_converts_gbp_to_usd_via_conversion_rate` added; 52/52 cost-obs tests + full backend QG green.
        Codex `billing-cost-observability.md` updated (Currency bullet). No UI change needed — the existing `usd()`/`$`
      is now correct. GBP tally view is the next todo (P2).
- [x] ✅ [UI] P2. **GBP view option for GCP (tally against the £ invoice).** Primary display stays USD everywhere; add
      an option to also read GCP figures in **native GBP** so the operator can tie out to the GBP console/invoice. AWS
      can't be GBP (no AWS-supplied rate — external FX only), so the GBP view is GCP-only-meaningful: thread
      `currency` + the native amount through the cost model and surface GCP's £ in a tooltip / secondary line (or a
      USD⇄GBP control that only re-denominates GCP while AWS stays USD-labelled). Confirm exact UX at build time. - ✅
      **2026-07-10 — operator chose Option A (a USD⇄GBP toggle).** Backend threads native GBP end-to-end:
      `gcp_facts_sql` also selects the raw pre-conversion `cost_native`/`credit_native` + `currency`; a `_NativeAcc`
      DRYs the per-group native accumulation across every breakdown builder; `CloudSummary`/`BreakdownRow` expose
      `currency` + `*_native` (mixed cross-cloud keys → USD so a by-day row never mislabels).
      **deployment-api@`033967a`** (threading, +`test_native_currency_threads_gbp_for_gcp_tally`) + **@`a40f18a`**
      (mixed-currency guard). Verified vs live BQ: GCP `gross_native` £2,251.65 (rate 0.756), AWS mirrors (rate 1.0).
      UI: a header `USD/GBP` `Segmented` re-denominates GBP-native rows (GCP) to £ across KPI tiles + breakdown table
      (incl. Other/Unattributed residual + the fraction hint) + leaf tables ($/GB and bucket component split
      re-denominated at the row's own rate); AWS/ GitHub + cross-cloud aggregates (grand total, trend/donut) stay USD,
      since no GBP figure exists. **deployment-ui@`6bc9139`** — 14 vitest + 16 pw (`USD⇄GBP toggle …` regression) + full
      UI QG green. Codex `billing-cost-observability.md` Currency bullet updated.
- ➡️ **Migrated 2026-07-10 → issues/cost_observability_deferred_followups_2026_07_10.md** — [BACKEND/INFRA] P2. **AWS
  Athena holds July-2026 only — investigate a CUR historical backfill.** Per-month probe:
  `aws_billing.cur_uts_cost_usage` contains ONLY `2026-07` (gross
  $792.89) — the CUR delivery started in July, so
  `/ops/costs` structurally cannot show any pre-July AWS spend. The operator's AWS CSV is Jan–Jun (Cost Explorer, ~14mo
  retention; $8,584
  gross), **zero temporal overlap** with the CUR. Also: AWS is **fully credited** — every July day gross≈−credit → **net
  $0** (~$98/day gross visible). **Investigate** a backfill: CUR "include historical data" on report re-creation, or a
  one-off Cost Explorer `GetCostAndUsage` import into a side table. If feasible → backfill full-year AWS history; else
  document the AWS tab as **July-2026-onward** (operator: acceptable). Not a code bug — a data-source coverage gap.
- [x] ✅ [UI] P3. **Top-of-page tooltip: GCP console = Pacific day boundary, export = UTC.** Not a bug — it's why a
      console CSV won't tie to the penny. Same Jul3–9 window/currency: console gross £2,509.38 vs export(UTC) £2,708.12;
      re-windowing the export on Pacific midnight (07:00 UTC) → £2,549.07, within £40 (1.6%) of console (residual =
      late-arriving recent-day data). Add a one-line tooltip so operators don't chase the ~8% phantom gap. - ✅
      **2026-07-10 — deployment-ui@`95370af`.** Header `InfoTip` (`data-testid="cost-currency-tz-note"`) covering both
      the new currency behaviour (USD everywhere; GCP GBP→USD at Google's daily rate; AWS native USD) and the
      UTC-vs-Pacific day-boundary caveat. pw:L2 regression added to `cost-observability.spec.ts` (hover reveals both the
      "converted at Google's own daily rate" and "US Pacific time" lines) — 15/15 pw + full UI QG green.

### GitHub real billing & GCP Pacific-day alignment (2026-07-10 — operator)

Two focused items this pass; the multi-account/multi-org idea is **explicitly out** (decision recorded below).

- [x] ✅ [BACKEND] P1. **GCP Pacific-day bucketing (GCP-only) — make BigQuery match the console.** The day mismatch was
      **GCP only**: `gcp_facts_sql` bucketed by `DATE(usage_start_time)` = UTC, but the GCP billing console groups by
      **US Pacific**. AWS needs no change (CUR + Cost Explorer are both UTC). Fix: group + filter GCP on
      `DATE(usage_start_time, 'America/Los_Angeles')` (pruning still on `_PARTITIONTIME`). - ✅ **2026-07-10 —
      deployment-api@`29a18c088`** + **deployment-ui@`4e14b450`** (tooltip). Verified vs live BQ: Pacific brings the
      Jul3-9 window gross **£2,959.65 → £2,800.60** (−5.4%, toward the console's Pacific convention; exact tie-out
      drifts as both the export and the CSV keep accruing late rows). Unit tests:
      `..._buckets_and_windows_in_us_pacific` + `test_aws_facts_sql_stays_utc_no_timezone_conversion`; header `InfoTip`
      reworded (GCP Pacific-matched, AWS UTC-matched) with a pw:L2 assertion (`cost-observability.spec.ts` 16/16). Full
      backend + UI QG green.
- [x] ✅ [BACKEND+UI] P1. **GitHub real billing — LIVE.** `github_billing.py` calls the Enhanced Billing usage report
      (`GET /users|organizations/{acct}/settings/billing/usage`), token from Secret Manager via `get_secret_client`,
      mapped per-day x product x repo x SKU to `CostRecord` (cost=gross, credit=net−gross); `github_facts` tries real →
      falls back to the labelled dummy on any failure (non-regressive). - ✅ **2026-07-10 — deployment-api@`29a18c088`**
      (provider) + **@`c4549daa`** (real-token wiring + product prettify) + **deployment-ui@`89d5b276`** (dummy note /
      footer gate on `is_placeholder`). Operator (Ikenna) minted a fine-grained PAT (**Account → Plan → Read-only**,
      owner `IggyIkenna`), stored it as Secret Manager `github-billing-token` in `central-element-323112` with read for
      `github-token-sa`; config default now points there. **Live-verified end-to-end:** real usage flows (30d **gross
      $1,415.98 / credit −$98.29 / net $1,317.69**, GitHub Actions across 832 paid line items, `placeholder=False`, HTTP
      200 on both month queries). Field names + `net=cost+credit` mapping confirmed against the live response; lowercase
      products prettified (`actions`→`Actions`); RFC3339 `date` → day. UI: the "Dummy data" note becomes a "Live" note +
      the source footer reads "GitHub — Enhanced Billing" for real data (both gate on `is_placeholder`, so the mock/pw
      path keeps the dummy — 16/16). 10 unit tests + full backend & UI QG green.

**DECISION — multi-account / multi-org is NOT an in-app selector (2026-07-10, operator).** New AWS/GCP accounts for
Odum-Research (opened to harvest fresh cloud credits) will be **entirely separate** — separate org, project, BigQuery
tables, **and** separate secrets / env vars / JWT tokens / gcloud CLI identities. That is far heavier than swapping a
query table, so an in-app account/project dropdown is the wrong tool. **Chosen architecture: run the SAME code as a
separate deployment (its own backend + VM + UI) per account/org** — simpler to operate and less error-prone. Therefore
the earlier Tier-1 selector / Tier-2 multi-source-config / AWS cost-allocation-tag ideas are **dropped** (not built now
or in the near future). The current shared-account tenant split (Odum vs the account owner in `427895769566`) is moot —
Odum migrates to its own fresh accounts rather than splitting the legacy one.

**Codex SSOTs:** `/codex/05-infrastructure/billing-cost-observability.md` (exports + GitHub provider contract — update
when the real provider lands), `/codex/06-coding-standards/ui-testing-layers.md` (Playwright L2 gate),
`codex/06-coding-standards/` (no `os.getenv` — GitHub token via config).

## Resource-detail enrichment + unified breakdown (operator-requested 2026-07-08)

Operator wants a cleaner breakdown and richer per-resource detail. The table-merge (1) creates the columns the rest
(2–5) fill. All target `deployment-ui/src/pages/CostObservability.tsx` (`BreakdownPanel` / `LeafPanel`) + new backend
fields on `BreakdownRow`. **Key decision (operator, verified via live `bq` probe): the detail is all
BigQuery/Athena-native — pull `sku.description` + `usage.amount_in_pricing_units` (the SKU + usage fields the query
currently drops; same enrichment as the audit's "SKU dimension" finding) and group by `resource.name`. NO Cloud
Monitoring / CloudWatch (extra API cost + an IAM grant we don't have); anything not in the billing export is dropped,
not sourced elsewhere.** Confirm exact field/label names at implementation time (grep-then-read).

- [x] ✅ [UI] P2. **Merge the breakdown bars + table into one table.** _(SHIPPED → cost_obs_ui_unified_breakdown@88c4b70
      et al.)_ Today `BreakdownPanel` renders the same rows twice — a top-12 bar chart (left) and a sortable table
      (right), duplicating label + cost. Collapse to ONE scrollable, sortable table with an inline proportional
      **bar-in-cell that carries the cost value** (bar width = cost / max), dropping the separate bars column. Keep the
      sticky header + 400px scroll region; this frees horizontal space for the detail columns below and removes the
      duplication.
- [x] ✅ [BACKEND+UI] P2. **Gross / credits / net split per breakdown row (bifurcation).** _(SHIPPED → backend@a6bd1f8 +
      UI@f27e40f)_ Answers the operator Q — yes, the data supports it: `credit` is per-`CostRecord` at (day, service,
      resource, region) granularity, _finer_ than any breakdown group, so gross = Σcost, credit = Σcredit, net =
      Σ(cost+credit) reconcile for every dimension. Add `gross` + `credit` to `BreakdownRow` (currently net-only) and
      populate in `_grouped` / `_by_resource` / `_by_day`; render net as primary with gross + credit columns, shown only
      where credit ≠ 0 (GCP). Pushes the KPI-band treatment down into the table.
- [x] ✅ [BACKEND+UI] P2. **Bucket detail columns** _(SHIPPED → backend@171a61c + UI)_ (dimension = bucket): total
      stored **GB** + a **storage-class split** (Standard / Nearline / Coldline / Archive) + derived **$/GB** per bucket
      — **all from the billing export itself, no Cloud Monitoring / CloudWatch** (operator: don't pay to query stats we
      already have). Pull `sku.description` + `usage.amount_in_pricing_units` (unit `gibibyte month`) on the storage
      SKUs, group by `resource.name`, convert GiB-month → avg GB over the window; show **GB, not raw bytes**. AWS analog
      = CUR `line_item_usage_amount` on the S3 storage usage-types. **Dropped (not billable → absent from BQ/Athena, per
      operator's "if not in BQ, drop it"): the soft-delete / noncurrent split (verified — no soft-delete SKU in the
      export) + object count (only Class-A/B _operations_ counts are billed, not object totals).**
- [x] ✅ [BACKEND+UI] P2. **Resource detail + waste flags** _(SHIPPED → backend@8d8802f idle-IP/orphaned-disk
      cost-waste + UI@047494b)_ (dimension = resource): machine type (e.g. `e2-highmem-16` → **16 vCPU · 128 GB**) per
      VM from the billing `system_labels` (`compute.googleapis.com/machine_spec`, + `cores` / `memory`) — no Compute
      API. Plus the **cost-waste the operator actually wants** (their case: a static IP billed unused for ~4 months):
      **idle static-IP cost** — the `Static Ip Charge` SKU is a reserved IP billed while NOT attached (distinct from
      `External IP Charge on a Standard VM` = in-use), keyed by `resource.name` (verified live: `harsh-static-ip`
      $5.95,
      `deployment-dashboard-ip` $3.35, `grafana`
      $2.24 …); and **orphaned-disk cost** — `… PD Capacity` SKUs keyed by
      disk `resource.name`, flag disks with no matching running VM (verified: `ikenna-windows-tokyo-restored` SSD
      **$68.62/30d**).
      AWS analog = idle Elastic-IP + unattached-EBS usage-types in the CUR. **All billing-native.** (Dropped, per
      operator: the live IP _address_ / current disk from the Compute API — they want the _cost of idle resources_, not
      network config, and not running-VM detail.)
- [x] ✅ [UI] P3. **Dimension-aware columns + leaf tables.** _(SHIPPED → UI@88c4b70)_ Merged table = label · [bar+cost]
      · net (· gross · credit) · share by default; add bucket columns when `dimension=bucket` / VM columns when
      `dimension=resource` (vm rows). Apply the same detail columns to the `LeafPanel` "Top compute instances" / "Top
      storage buckets" tables (their natural home too). Detail columns scroll horizontally on narrow widths. `[UI]`
      gate: `pw:L2` + a cited spec.

**Codex SSOTs:** `/codex/05-infrastructure/billing-cost-observability.md` (exports + net/gross/credit contract),
`/codex/06-coding-standards/ui-testing-layers.md` (Playwright L2 gate).

### Breakdown UX: By-label dimension, per-tab filter, pagination & resizable table (2026-07-10 — operator)

Operator asked to make the breakdown tabs navigable (resource/bucket have 300+ rows) + a business-context "By label"
view. Built + shipped on the running local stack for fast feedback.

- [x] ✅ [BACKEND+UI] P2. **"By label" breakdown dimension (GCP business labels).** `gcp_facts_sql` extracts the
      resource-level `labels` (purpose/category/venue/asset_group) → `CostRecord.labels`; a `label` dimension groups by
      a `label_key` route param (GCP-only; AWS/GitHub → "(unlabeled)"). UI: a "By label" dimension + a
      purpose/category/venue/asset_group sub-selector. **Coverage caveat (live probe): `asset_group` tags only ~0.16% of
      spend; `purpose` (49%) + `category` (24%, layer×asset-group) are the useful axes now.** - ✅
      **deployment-api@`9a6b5d2c`** + **deployment-ui@`881a4880`**. Live-verified: purpose → manifest-consolidator
      $3.7k, market-data-raw $945, … category → instruments-defi / market-data-tradfi / execution-defi splits.
- [x] ✅ [UI] P2. **Per-tab search filter.** A search box filters the already-loaded breakdown rows client-side (label +
      detail substring, no re-query) — makes the 300+-row resource/bucket tabs navigable; roll-up rows hide while
      filtering; a "No X match" empty state. deployment-ui@`881a4880`.
- [x] ✅ [UI+BACKEND] P2. **Pagination (100/page).** Backend `_BREAKDOWN_LIMIT` 100→1000 so all groups return
      (bucket=338); UI paginates 100/page with Prev/Next + "showing X–Y of Z". "Other"/"Unattributed" roll-ups render
      only on the last page. Cap test updated to exceed the new limit. deployment-api@`9a6b5d2c` +
      deployment-ui@`881a4880`.
- [x] ✅ [UI] P2. **Resizable breakdown container.** `resize-y` handle — drag the bottom edge to make the table taller /
      shorter (420px default, min 160, max 85vh). deployment-ui@`881a4880`.

**Sort mechanism (operator Q — answered, no change):** sorting is **100% client-side** (`useSort` re-orders the loaded
rows in a `useMemo`; no API call). BigQuery/Athena are queried at most **once per date-window** (in-memory cache), so
switching dimensions + sorting all derive from that cache — a "Refresh" is the only re-query.

**Deferred (operator to evaluate first):** `asset_group` / launcher-labeling enrichment for full business-context
coverage — only if the By-label view proves valuable. Probe: labels already in the export (`purpose` 56k rows, `venue`
23k, `managed-by` 19k, `category`), but `asset_group` is ~unpopulated.

**Codex SSOTs:** `/codex/05-infrastructure/billing-cost-observability.md`,
`/codex/06-coding-standards/ui-testing-layers.md`.

## Progress Log

_(Session findings go here — agent memory writes are BANNED. Append dated notes as work proceeds.)_

- 2026-07-10 — **Reconciled against the successors (cross-plan audit).** This `superseded` plan showed 20 open todos
  while its successors (`cost_obs_backend_sku_usage_enrichment` 11/0, `cost_obs_ui_unified_breakdown` 8/0) had already
  shipped the work. Verified each open todo against the successor done-items and **flipped 11 with the successor sha**
  (SKU dimension, spot/on-demand, gross/credit/net bifurcation, bucket detail, resource+waste incl.
  idle-IP/orphaned-disk cost, zone, AWS net/invoice, merge-bars-table, dimension-aware leaf tables, stale-refetch fix,
  GitHub billing → LIVE). **Open 20 → 8**, all genuine residual (3 real-deferred + 5 nice-to-have — see the banner above
  the Deferred section). No work lost; the tracker made honest. Residual home = an open operator question (issue-doc vs
  park here).

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
- 2026-07-08 — **UI redesign to mockup fidelity (follow-up).** Operator feedback on the first pass: "nowhere close to
  the mock in terms of UI." Rebuilt `pages/CostObservability.tsx` on the real deployment-ui tokens to match the
  reference mockup — non-sticky page header (gradient icon tile + `/ops/costs` subtitle; no duplicate site-chrome or
  theme-toggle since the app `<Header/>` owns those), corner-sparkline KPI cards (**anchored to a
  $0 baseline** so a
  near-flat series like GitHub reads flat instead of a full-height zig-zag), a **custom SVG** stacked-area (gridded,
  crisp via `ResizeObserver`, crosshair + per-cloud+total tooltip, faint amber **provisional band** over the trailing
  unreconciled day so today's not-yet-reported `$0`reads as "pending", not "crashed") + custom SVG donut, tighter`Panel`density, refined bars + sortable tables, a two-column GitHub placeholder, and a source-attribution footer (BigQuery / Athena table names + last-updated). **recharts dropped on this page** (chart-theme.ts stays for other pages). Every`data-testid` + button label preserved, so vitest + Playwright stayed green with only the recharts mock removed. **deployment-ui@`8a56b6b`** — tsc + ESLint + vitest 4/4 + Playwright L2 4/4 + full UI QG green; re-verified on `:5183`in **both themes** (0 console errors; real total`$15,367.85`).
  Mockup HTML kept untracked — delete once the page fully supersedes it.
- 2026-07-08 — **Segmented-control boundaries (operator feedback).** "7d/30d/90d buttons are not separated properly … no
  clear boundaries." The shared `Segmented` (range / cloud-filter / breakdown-dimension) now renders a bordered
  container with **`border-emphasis` dividers between every cell** + a filled active cell, so options read as distinct
  buttons, not one run-together word. Verified both themes. **deployment-ui@`b0eacaf`** — full UI QG green. Audit of the
  rest of deployment-ui: RepoCi "sort:" + Deployments status-chips/umbrella-tabs already give each button its own
  `rounded border` (fine); the app-wide **`ui/tabs.tsx` pill variant** (cockpit / landing / service-details / capability
  / deployment-details) shares the defect — extending the same bordered-cell + divider treatment there next.
- 2026-07-08 — **App-wide pill-tab boundaries (same feedback, shared component).** `ui/tabs.tsx` pill variant now
  renders a bordered frame + `border-emphasis` divider between every trigger (`[&>*]:rounded-none` squares the shared
  `TabsTrigger` inside the frame; the active cell fills edge-to-edge). One change fixes every pill tab bar — cockpit
  (grid-cols-12), service views, landing, capability, deployment-details. `underline` variant untouched.
  **deployment-ui@`6377437`** — tsc + ESLint + **full vitest 910/910** + full UI QG (incl. build) green; screenshotted
  the cockpit + a service tab bar in dark (0 page errors, clean dividers, active cell filled, no layout breakage).
- 2026-07-08 — **Last custom tab group (DeployConsole).** Full sweep of `role="tab"`/`aria-selected` groups:
  LiveDeployments panel tabs + LaunchTab pane tabs already carry per-button `border` (fine); `FeatureFamilyFilter` is a
  dropdown (n/a). Only `cockpit/DeployConsole.tsx` deploy-view tabs were bare text — gave them the same bordered-frame +
  divider treatment. **deployment-ui@`aaed6647`** — tsc + ESLint + full vitest 910/910 + full UI QG green. All
  segmented/pill tab groups in deployment-ui now have clear cell boundaries; `underline` Radix tabs deliberately left
  (different idiom).
- 2026-07-08 — **Matched the design mock (course-correction).** Operator compared the mock vs the shipped controls
  side-by-side: the hard-divider look diverged from the mock. Reverted to the **mock's exact aesthetic** — padded
  rounded pills with a gap between them + a filled accent (cyan `accent-dim`) active pill; the separation comes from
  padding + the active pill, not dividers. Applied uniformly: cost-page `Segmented`, the shared `ui/tabs.tsx` pill
  variant (active override is pill-scoped via `[&>[data-state=active]]:…!` so the `underline` variant — Monitor /
  DataStatus tabs — is untouched), and `cockpit/DeployConsole` view tabs. **deployment-ui@`4c65cfb`** — tsc + ESLint +
  full vitest 910/910 + full UI QG (incl. production build, which validates the arbitrary important selector) green;
  screenshotted the cost range/dimension controls + cockpit + service tab bars in dark — pills match the mock, active
  cell is a cyan pill, 0 page errors. **Note (app-wide active-colour change):** pill tab bars now show the active tab as
  a cyan pill (was a dark inset pill) — consistent with the mock + the sidebar nav's own active style; flagged for
  operator review.
- 2026-07-08 — **Root cause found + fixed: the CSS reset was zeroing ALL Tailwind spacing app-wide (one commit).** After
  the mock-match pass the controls still ran together (`All clouds` then `GCPAWSGitHub`) and, per operator, stacked
  cards had no vertical separation (horizontal only). Diagnosed via computed styles: every Tailwind `p-*`/`px-*`/`py-*`
  AND `m-*`/`space-y-*` resolved to `0` — the unlayered `* { margin:0; padding:0 }` reset in `index.css` outranks
  Tailwind v4's _layered_ utilities (layer-vs-unlayered cascade), silently killing all Tailwind margin + padding. This —
  not the gap — was the real source of the app-wide "cramped/ugly" look; the earlier divider/gap passes were treating a
  symptom (removing the gap fully collapsed the zero-padding buttons).
  - **Fix (one place):** moved the reset into `@layer base` (`* { box-sizing }` stays unlayered;
    `@layer base { * { margin:0; padding:0 } }`) so `@layer utilities` wins. Un-utility'd elements still get 0;
    hand-written unlayered rules (`.card-content`, `select`, …) still win; the only 2 negative-margin utilities
    (edge-bleed separators) are benign. Measured: seg-button padding 0→11px, cost sections 0→14px vertical gap
    (bounding-box; Tailwind v4 `space-y` applies logical `margin-block-start`, so a naive `.marginTop` read shows 0 —
    the rendered gap is the truth).
  - **Controls onto the mock spec (padding restored → flush pills read correctly):** shared `ui/tabs.tsx` pill (drop
    `gap-1`, `p-1`→`p-0.5`, pill-scoped inactive-hover — fixes 6 pages), cost `Segmented` (exact `px-[11px] py-[5px]`,
    no hover box), `DeployConsole`; **converted** `LaunchTab` (bordered card-tabs → segmented pill) + `LiveDeployments`
    events/logs (also fixed a **dark-mode bug**: hardcoded `bg-blue-50`/`text-blue-700` light colours on the dark theme
    → `accent-dim`/`accent` tokens). Cloud filter kept segmented (now readable; mock's dropdown is an optional tweak).
  - **deployment-ui@`f4c59e7`** — `quality-gates.sh --no-fix`-green (tsc + ESLint + orphan-audit + **vitest 911
    passed** + UI codex + production build) → quickmerge to `live-defi-rollout`; screenshotted 6 pages (cost / cockpit /
    landing / deployments / research / safety-ops) in dark — controls match the mock, vertical rhythm restored, **0
    breakage**. Both CSS root-cause fixes (margin + padding) now live in one `@layer base` block.
- 2026-07-08 — **Breakdown table only ever showed the top 15 rows of every dimension (operator-reported).** "In By day
  - 90d I still see only some of them … same for other breakdowns — 40 items, only some shown." Root cause: the
    breakdown **table** rendered `sorted.slice(0, 15)`, a hard cap independent of dimension. Verified the data path is
    honest end-to-end first: `_by_day` returns **all** N days uncapped (`service.py:211`), `_grouped`/`_by_resource`
    return up to `_BREAKDOWN_LIMIT=50`, and the client passes no limit — so the backend was handing over up to 90 (day)
    / 50 (grouped) rows and the UI discarded everything past the 15th.
  * **Fix (frontend-only):** the table now maps **every** `sorted` row inside a `max-h-[400px] overflow-auto` container
    with a **sticky header** (opaque panel-bg `<th>`, opt-in via a new `sticky` prop on `SortHead`/`PlainHead` so the
    LeafPanel tables stay unaffected). Footprint stays ~the old 15-row height but all rows are reachable by scroll; the
    panel-header hint gains a live row count (`· 90 rows`). Left-side bars stay a top-12 "biggest items" chart (a 90-bar
    stack is unreadable) — chart = top spenders, table = full ledger.
  * **deployment-ui@`ec88032`** — full UI QG green (tsc + ESLint + orphan-audit + **vitest 911 passed** + UI codex +
    production build) → quickmerge to `live-defi-rollout`. Added a **pw:L2** regression (`By day @90d` lists >30 rows in
    an overflowing scroll region) — Playwright smoke **5/5**. Screenshotted the mock (**90 rows**, container clamped
    400px / scrollHeight 2636px) and real `:5183` (40 rows, same clamp) — all rows present, page stays compact.
  * **Note (adjacent, NOT fixed — flagged):** switching dimension+range quickly on the slow real backend briefly shows
    the previous fetch's rows under the new column header (stale-during-refetch). Pre-existing and orthogonal to this
    cap fix; follow-up would gate the table on `breakdown.dimension === dimension` or skeleton the panel while
    refetching. Tracked below.
- 2026-07-08 — **NET-of-credits (audit finding P1) — the page was overstating GCP spend ~17%.** Operator: "add this so
  we have the actual cost we have to pay, but show all 3 — actual $ then in bracket (gross − credit)." Root cause (from
  the data-fidelity audit): `CostRecord.credit` was fetched but **never read**, so every view summed pre-credit gross.
  - **Backend
    (`deployment-api@`f10b0914`):** `_net(r)=cost+credit`now summed across summary / breakdown / timeseries (net is canonical everywhere, so trend / donut / tables all reconcile to the headline);`SummaryResponse`+`CloudSummary`gained`gross`+`credit`.
    GCP populates credit; AWS/GitHub carry 0 (net==gross). New pytest asserts net = gross + credit end-to-end. Existing
    tests unaffected (their fixtures have credit 0).
  - **Frontend
    (`deployment-ui@`0f653068`):** KPI band leads with **net** (what you pay) and, when credits apply, shows the derivation **"(gross − credits)"** — grand total + GCP tiles; AWS/GitHub (no credits) render no line. Credits in green. `deploymentApi.ts`
    types + the frontend mock (GCP ~20% promo credit) updated; vitest + a **pw:L2** regression assert the split renders
    (and is absent without credits).
  - **Verify:** both full QGs green (backend 71s; UI tsc+ESLint+vitest 911+build); Playwright cost smoke **6/6**. Live
    `:5183` net **$12,593.31** matches the bq probe **$12,593.32** (1-cent rounding) — the fix is correct against the
    source. Corrected the codex's stale "promo exhausted ~2026-06-20" note (promo is **active**, ~$2.5k/30d). The other
    audit findings (SKU dim, spot-vs-on-demand, AWS net/invoice, usage units) remain tracked P2/P3.
- 2026-07-09 — **Post-completion review of the AO fleet's work + 4 robustness fixes (checkpoint reconciliation).** The
  two AO plans (`cost_obs_backend_sku_usage_enrichment` + `cost_obs_ui_unified_breakdown`) shipped all 19 tasks with
  both QGs green + Playwright 14/14. Reviewed each independently against **real billing data** (not just the checkboxes)
  — most is genuinely good (merged table, gross/credit bifurcation, SKU dim surfacing the hidden Coldline #1 driver,
  bucket volume + class split, VM machine specs, spot/on-demand). But 3 features were **green-in-tests yet broken on
  real GCP data** — the fixtures used mock SKU strings that don't match the live regional naming. Fixed all, verified
  live:
  - **Waste detection flagged 0 rows → now 8.** (a) Matchers were exact/`endswith` but real SKUs carry a regional suffix
    (`Static Ip Charge in Japan`) → substring match. (b) Waste is cheap by nature, so the top-N-by-cost cap hid it →
    flagged rows now bypass the cap (resource rows 50→58). (c) Orphaned-disk used a disk-name==VM-name heuristic
    (false-positived data disks) → now the disk's real Compute `users` attachment via new
    `vm_utils.list_unattached_disk_names`. **deployment-api@`5739728`**.
  - **Bucket `$/GB` read total(ops-dominated)/GB → `$733/GB` nonsense; now storage-SKU cost / stored GB** (real
    ~$0.006/GB). Same commit.
  - **"Top storage buckets" leaf was blank** (storage only computed for the By-bucket dimension, but the leaf is fed by
    the resource dimension) → storage now computed for bucket-KIND rows in any dimension. Same commit.
  - **Waste amount showed the credit-masked net (`$-0.0`) → now gross** (the honest cost of the idle resource / what
    you'll pay when the promo ends). **deployment-ui@`9a8d567`**.
  - **Verify:** full backend QG (76s, incl. new regional-SKU / cap-bypass /
    storage-cost-$/GB / leaf / real-attachment
    tests) + full UI QG green; vitest 12/12; Playwright cost **14/14**. Live `:8004`: waste **0→8** flags (7 idle IPs
    incl. the regional ones + 1 orphaned disk), `$/GB`
    **25.50→0.0061**, resource-dim bucket storage **0→10** populated. Root-cause pattern for the reviewer's log: **green
    tests ≠ works on real data** when fixtures don't mirror the live SKU naming — every fix here is now covered by a
    test asserting the real regional strings.
- 2026-07-09 — **AWS showed $0 — root-caused to a fully-credited account + 2 bugs (operator: "AWS 0 doesn't sound
  right").**
  - **The truth:** AWS is genuinely fully credited — usage ~$752/30d, offset by ~-$752 in AWS promotional credits →
    **net ~$0**. The page showed $0 for the _wrong_ reasons and never surfaced the credited gross.
  - **Bug 1 — deployment-api@`f914cc47`:** task 301ccfc's `line_item_net_unblended_cost` does not exist in this CUR's
    crawler schema (verified `SHOW COLUMNS`) → Athena errored → per-cloud isolation silently zeroed AWS. Reverted to
    `line_item_unblended_cost`, then made AWS mirror GCP's cost/credit split — the query pulls gross
    (Usage/DiscountedUsage/Tax/Fee) + credit (`Credit` line-items) via conditional aggregation and `aws_facts` populates
    `CostRecord.credit`.
  - **Bug 2 — unified-trading-library@`999383e`:** `AWSAnalyticsClient.execute_query` fetched only the first Athena
    `GetQueryResults` page (no `NextToken`) → truncated at ~~1000 rows; the new usage_type+zone columns pushed the query
    to 4266 groups → 999 returned (~~$48 of ~$752). Now paginates via `paginate_athena_result_rows` (extracted to
    `_aws_sdk_protocols.py` to keep `aws.py` <900L, per that module's role). Unit test covers 2-page accumulation + the
    `NextToken` pass-through.
  - **Verify:** backend QG + full UTL QG green; live via the real service path (paginated): AWS **net
    $0.00 / gross
    $752.29 / credit -$752.29**. AWS now reads **$0 net** WITH the ($752.29 gross − $752.29 credits)
    split — honest "fully credited", plus a heads-up that the real AWS bill lands when those credits run out. Corrected
    the AWS-net task's stale `net_unblended_cost` premise.
  - **Note (pre-existing, FLAGGED not fixed):** `test_event_sink_factory::TestGcpEventSink` is order-fragile under
    pytest-xdist — a stale `GCP_PROJECT_ID=test-project` leaks through a cache `clear_client_caches()` misses, so it
    intermittently reads the wrong project. Surfaced (not caused) by the extra AWS test shifting the xdist distribution;
    passed on the shipping run. A real UTL test-isolation bug worth a separate fix.
- 2026-07-09 — **Reconciliation vs operator console CSVs + GCP currency root-cause (slot 4, interactive).** Reconciled
  `/ops/costs` against the operator's GCP (£, Jul3–9) + AWS
  ($, Jan–Jun) console CSVs. Confirmed the UI == its billing
  sources to the penny (GCP per-service matches `bq`). Root-caused 3 source-level facts, logged as the "Currency, AWS
  history & timezone reconciliation (2026-07-09)" findings above: (1) GCP export is GBP mislabelled `$`(3 independent proofs) → fix = in-query`/currency_conversion_rate`
  USD conversion using GCP's own rate, no external FX; (2) AWS CUR is July-only (Cost Explorer has Jan–Jun, zero
  overlap; AWS fully credited → net $0); (3) console(Pacific) vs export(UTC) day-boundary explains the residual ~8%
  gross gap (→ £40 / 1.6% once Pacific-aligned). Operator decisions: **USD everywhere + a GBP option for GCP**;
  **investigate AWS CUR backfill** (else July-onward is fine); **TZ note in a top tooltip**. Findings + plan only — no
  code shipped this step.
- 2026-07-09 (EOD) — **All slot-4 repos pushed to LDR** (operator: "make sure everything is pushed").
  - **deployment-ui@`f9d0a00`** — bold the `/` in the `N/total` breakdown-rows fraction (legibility); via quickmerge, UI
    QG green.
  - **deployment-api@`33d5afe`** — the top-100 breakdown-cap checkpoint (`_finalize_rows` Other/Unattributed roll-ups +
    `cost_by_component`), **direct-pushed under the dirty-deps carve-out** (operator-authorized): backend QG is red ONLY
    on the 3 UAC-drift `data_status_drilldown::TestGetSchemaForShard::test_uppercase_*` tests — verified this run **4364
    passed / 3 failed, all UAC** (`assert 'symbol' == 'pool_address'/'pool_id'`, from unified-api-contracts@9ec7dde6);
    cost-obs code + tests clean. strict-quickmerge WARNed (no `Quickmerge:` trailer), push succeeded. **NB the commit
    BODY still reads "held, NOT pushed" — stale; it IS on LDR now** (amend aborted by the identity hook; won't
    force-push a shared branch for cosmetic text). Author label reads `[main·harsh_pc]` not `[slot-4·]` (same reason,
    pre-existing). The P1 GCP→USD conversion resumes tomorrow AM on top of this.
  - **unified-trading-pm@`eadf1c173`** — the currency / AWS-history / TZ plan follow-ups (added earlier this session).
- 2026-07-10 — **Multi-account/project + GitHub-token + Pacific-TZ scoping → operator narrowed it (slot 4,
  interactive).** Initial scoping read the whole cost-obs backend + probed CUR metadata: (1) the aggregation layer is
  already account-agnostic (an in-app selector would be Tier-1 small); (2) **AWS can't separate the two tenants in one
  account** — 159 CUR cols, **zero** cost-allocation-tag / cost-category cols; (3) **Pacific-vs-UTC is GCP-only** (AWS
  CUR + Cost Explorer are both UTC); (4) GitHub real-billing needs a billing-scoped token. **Operator decisions
  2026-07-10:** (1) fix GCP→Pacific now; (2/3) **drop the in-app multi-account/multi-org selector entirely** — future
  Odum-Research accounts are wholly separate (org/project/BQ tables + secrets/env/JWT/gcloud identities), so each gets
  its **own separate deployment (backend + VM + UI)** rather than a dropdown; stripped the Tier-1/Tier-2/tag items from
  the plan; (4) **this pass = GitHub real billing + the GCP Pacific fix.** GitHub probe (verified): `IggyIkenna` is a
  **User** in no orgs, and the token we hold is a **fine-grained PAT without the `Plan` permission** → **403** on every
  billing endpoint — real GitHub $ needs a Plan-scoped token (operator credential ask). Code for GCP-Pacific + the
  GitHub provider scaffold follows in this session; GitHub live-verify pends the token.
- 2026-07-10 — **SHIPPED: GCP Pacific-day bucketing + real GitHub billing provider (slot 4, batched per operator).**
  Operator asked to batch the work + push once at the end rather than per-item git rituals. Both backend items built,
  gated, and quickmerged.
  - **GCP Pacific TZ — deployment-api@`29a18c088` + deployment-ui@`4e14b450`.** `gcp_facts_sql` buckets + windows on
    `DATE(usage_start_time, 'America/Los_Angeles')`; AWS untouched (both sides UTC). Verified vs live BQ (Jul3-9 gross
    £2,959.65 UTC → £2,800.60 Pacific, −5.4% toward the console). Header `InfoTip` reworded; pw:L2 16/16.
  - **GitHub real billing — deployment-api@`29a18c088` (same commit).** New
    `services/cost_observability/github_billing.py` (Enhanced Billing usage report → CostRecord; token via
    `get_secret_client`, `GH_BILLING_PAT`→`GH_PAT`); `github_facts` real-or-dummy orchestrator (non-regressive
    fallback). 8 new unit tests (mapping/window/403/no-token/fallback/degrade)
    - standalone smoke. **Live data BLOCKED-CREDENTIALS** — the in-hand fine-grained PAT lacks the `Plan` scope (403),
      so the page still renders the dummy; provisioning a Plan-scoped `GH_BILLING_PAT` secret flips it to real with zero
      code.
  - Both full QGs green (backend 123s / UI 18s); `strict-quickmerge` clean on both. **Deferred to next pass:** GitHub
    live-verify (operator provisions the Plan-scoped token) + the AWS CUR historical backfill go/no-go.
- 2026-07-10 — **GitHub real billing is LIVE (token landed, verified end-to-end).** Operator (Ikenna) minted the
  Plan-scoped fine-grained PAT (Account → Plan → Read-only, owner `IggyIkenna`), stored it as Secret Manager
  `github-billing-token` in `central-element-323112` and granted read to `github-token-sa`. Pointed the config default
  at that secret; live-verified the whole path: `github_facts` now returns **real** usage — 30d **gross
  $1,415.98,
  credit −$98.29, net $1,317.69** (GitHub Actions, 832 paid line items across the repos,
  `placeholder=False`, HTTP 200 on both month queries). The live response confirmed the field names + `net=cost+credit`
  mapping; prettified lowercase products (`actions`→`Actions`); RFC3339 `date`→day. UI dummy-note + source-footer now
  gate on `is_placeholder` (mock/pw stays dummy → 16/16 green; real data shows a "Live" note + "GitHub — Enhanced
  Billing" footer). Shipped deployment-api@`c4549daa` + deployment-ui@`89d5b276`; both full QGs green. **Only AWS CUR
  backfill go/no-go remains open on this plan.**
- 2026-07-10 — **Verified the parallel-agent reconcile of this superseded plan (operator asked "check it was done
  properly").** Another agent's `169b44b74` flipped this checkpoint 19→8 open (11 done items, each SHA-cited) and the
  deployment `expansion` parent 35→11. Audited the 11 cost flips against the LIVE code + the children's evidence: 10 are
  correct (SKU dim, spot/on-demand, zone, merged table, gross/credit split, bucket detail, resource+waste, dimension
  columns, GitHub-live, stale-during-refetch — the last confirmed by the real `breakdown.dimension===dimension` gate at
  `CostObservability.tsx:1645`; all cited SHAs resolve to real feature commits). **One defect fixed:** the AWS-not-net
  flip cited `301ccfc` (the net_unblended_cost attempt that was **reverted** — that column is absent from the CUR and
  zeroed the tab); repointed the evidence to the live fix `deployment-api@f914cc4` (net-of-credits + Tax/Fee/Credit).
  The 8 remaining open items are all genuinely open (P3 + the P2 AWS backfill). My currency/GitHub/Pacific subsections
  survived the parallel edit intact. Net: the cost reconcile is now correct. (The `expansion` reconcile + its
  still-`active` status are the deployment cluster — operator is routing the overlap notes to that agent.)
- 2026-07-10 — **Breakdown UX shipped: By-label dimension + filter + pagination + resizable table (local-first, batched
  per operator).** Operator wanted navigable breakdown tabs + a business-context view; ran the slot-4 local stack (api
  :8004 + ui :5183, `DISABLE_AUTH=true`, real data) for fast feedback, built all four, gated, quickmerged.
  **deployment-api@`9a6b5d2c`** (label dimension: extract purpose/category/venue/asset_group labels →
  `CostRecord.labels` → `label` dim + `label_key` param; `_BREAKDOWN_LIMIT` 100→1000 for pagination; 3 tests) +
  **deployment-ui@`881a4880`** (By-label dim + label-key sub-selector, per-tab client-side filter, 100/page pagination,
  `resize-y` container; pw:L2 regression 17/17; mock >100-row label fixture; vitest labelKey-arg fixes). Both full QGs
  green (backend 129s / UI 21s); UI quickmerge auto-reconciled a parallel `launched_by` push cleanly. Live-verified via
  the UI proxy: By-label/purpose → manifest-consolidator $3.7k etc., bucket dim now returns all 338 rows. Answered the
  operator's sort Q (client-side, no BQ/Athena re-query). **`asset_group` enrichment parked** — operator evaluating the
  By-label view's value first.
