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
- 2026-07-08 — **UI redesign to mockup fidelity (follow-up).** Operator feedback on the first pass: "nowhere close to
  the mock in terms of UI." Rebuilt `pages/CostObservability.tsx` on the real deployment-ui tokens to match the
  reference mockup — non-sticky page header (gradient icon tile + `/ops/costs` subtitle; no duplicate site-chrome or
  theme-toggle since the app `<Header/>` owns those), corner-sparkline KPI cards (**anchored to a $0 baseline** so a
  near-flat series like GitHub reads flat instead of a full-height zig-zag), a **custom SVG** stacked-area (gridded,
  crisp via `ResizeObserver`, crosshair + per-cloud+total tooltip, faint amber **provisional band** over the trailing
  unreconciled day so today's not-yet-reported `$0` reads as "pending", not "crashed") + custom SVG donut, tighter
  `Panel` density, refined bars + sortable tables, a two-column GitHub placeholder, and a source-attribution footer
  (BigQuery / Athena table names + last-updated). **recharts dropped on this page** (chart-theme.ts stays for other
  pages). Every `data-testid` + button label preserved, so vitest + Playwright stayed green with only the recharts mock
  removed. **deployment-ui@`8a56b6b`** — tsc + ESLint + vitest 4/4 + Playwright L2 4/4 + full UI QG green; re-verified
  on `:5183` in **both themes** (0 console errors; real total `$15,367.85`). Mockup HTML kept untracked — delete once
  the page fully supersedes it.
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
