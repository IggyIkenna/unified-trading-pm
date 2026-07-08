---
doc_type: plan
title: Cost Observability — unified breakdown table + resource-detail columns (UI)
summary:
  UI half of the cost-breakdown enrichment — merge the duplicated bars and table into one sortable table with an inline
  bar-in-cell, then surface the backend's new fields as columns (gross/credit/net, SKU dimension, bucket volume plus
  class split, idle-IP and orphaned-disk cost-waste, spot-vs-on-demand, VM machine specs), dimension-aware and applied
  to the leaf tables. Starts draft, released to active by the last task of
  cost_obs_backend_sku_usage_enrichment_2026_07_08 once the API contract exists. Every UI task carries a Playwright L2
  regression.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [billing, cost, observability, breakdown, ui, deployment-ui, playwright]
related: [cost_observability_ui_2026_07_08.md, cost_obs_backend_sku_usage_enrichment_2026_07_08.md]
created: "2026-07-08"
last_updated: "2026-07-08"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: ui-developer
drift_direction: advance-code
depends_on: [cost_obs_backend_sku_usage_enrichment_2026_07_08]
locked_by:
locked_since:
supersedes:
superseded_by:
source: cost_observability_ui_2026_07_08.md
---

# Cost Observability — unified breakdown table + resource-detail columns (UI)

> **AO-DISPATCHED UI plan — starts `draft` (NOT ingested).** Released to `active` by the LAST task of the backend plan
> **`cost_obs_backend_sku_usage_enrichment_2026_07_08.md`**, so this agent only starts once the new `BreakdownRow`
> fields (gross/credit, sku, bucket volume, waste flags, machine specs) actually exist in the API. Full design context
> is in the LOCAL parent plan **`cost_observability_ui_2026_07_08.md`** ("Resource-detail enrichment + unified
> breakdown" section — read it first).
>
> **UI gate (HARD):** no `[UI]` task ticks without `pw:L2 ✓` + a cited regression spec. TS strict; tsc / ESLint / Vitest
> / Playwright only (no Python tools). All cost work lives in `src/pages/CostObservability.tsx` (`BreakdownPanel` /
> `LeafPanel`) + `src/api/deploymentApi.ts` types + `src/lib/mock-api.ts`.

## Codex SSOTs (read before touching)

- `codex/06-coding-standards/ui-testing-layers.md` — the Playwright L2 gate.
- `codex/05-infrastructure/billing-cost-observability.md` — the API row contract the backend plan extends (net/gross/
  credit, sku, usage, bucket-volume, waste fields).

## Tasks

- [x] ✅ [UI] P0. **Merge the bars + table into one table** (foundation for every column below) —
      deployment-ui@`212acb6`. Collapsed `BreakdownPanel`'s left top-12 bar chart + right table into ONE scrollable,
      sortable table with an inline proportional **bar-in-cell that carries the cost value** (bar width = cost / max
      across the full dataset), dropping the separate bars column. Sticky header + 400px scroll region unchanged.
      tsc/ESLint/vitest (912 passed) all green. pw:L2 ✓ | regression: tests/smoke/cost-observability.spec.ts ("breakdown
      bars + table are merged into one table with an inline bar-in-cell" — asserts a single `cost-breakdown-table`, the
      top row's bar-in-cell renders at >90% width matching its max cost, and re-sorting ascending shrinks the bar,
      proving it's data-driven).
- [x] ✅ [UI] P1. **Gross / credit / net columns** — deployment-ui@`f27e40f`. Added `gross`+`credit` to
      `CostBreakdownRow` (mirrors the backend `BreakdownRow` bifurcation) and `mock-api.ts` fixtures (GCP rows carry
      ~20% credit, mirroring the existing summary mock). `BreakdownPanel` renders net as the primary Cost column with
      secondary Gross/Credit columns — shown only when a row in view carries a credit (dash for zero-credit rows;
      columns omitted entirely when nothing in view has credits, e.g. an AWS-only filter), mirroring the KPI band's
      per-cloud `GrossCredit` treatment down into the table. tsc/ESLint/vitest (914 passed, incl. 2 new cases) all
      green. pw:L2 ✓ | regression: tests/smoke/cost-observability.spec.ts ("breakdown table shows gross/credit columns
      only where a credit applies" — asserts the columns render + a dash + a credited row by default, then disappear
      entirely under an AWS-only filter).
- [x] ✅ [UI] P2. **SKU dimension in the control** — deployment-ui@`0d33ef0`. Added `"sku"` to `CostDimension` + the
      breakdown `Segmented` control ("By SKU", note "Google/AWS SKU"), backed by the already-shipped backend `_by_sku`
      grouping. `mock-api.ts` gets SKU fixtures mirroring the audit's #1 finding (Regional Coldline Class A Operations,
      the top cost driver hidden inside the Cloud Storage service rollup). Rebased onto the concurrently-landed
      bucket-columns commit (`034c89a`) touching the same files; both features kept. tsc/ESLint/ vitest (915 passed) all
      green; existing pw:L2 8/8 unaffected (no regression spec required for this task per the plan).
- [x] ✅ [UI] P2. **Bucket columns** (dimension = bucket): total GB, storage-class split,
      $/GB. Format GB (not bytes) —
      deployment-ui@`034c89a`. Added `storage_gb` / `storage_class_gb` / `cost_per_gb` to `CostBreakdownRow` (mirrors
      the backend bucket-only fields) + `mock-api.ts` fixtures (per-bucket GB + class split). `BreakdownPanel` renders
      three bucket-dimension-only columns — Storage (GB, thousands-separated, never bytes), Storage class (per-class GB
      split, largest first), $/GB
      — shown only when `dimension === "bucket"` (dash for a bucket row with no storage-volume usage this window).
      Reconciled onto the concurrently-landed gross/credit-columns commit (`f27e40f`) touching the same 4 files (stash +
      ff-pull + manual 3-way resolve, both features kept). tsc/ESLint/ vitest (914 passed) all green. pw:L2 ✓ |
      regression: tests/smoke/cost-observability.spec.ts ("By bucket shows
      storage/class-split/$-per-GB columns formatted in GB, not bytes" — asserts the Storage cell reads "18,500 GB" not
      a raw byte count, the class-split cell lists "Standard", the $/GB
      cell suffixes "/GB", and all three columns disappear under "By resource").
- [x] ✅ [UI] P2. **Resource / waste columns** (dimension = resource) — deployment-ui@`047494b`. Added
      `machine_type`/`vcpu`/`memory_gb` + `is_idle`/`waste_kind` to `CostBreakdownRow` (mirrors the backend's
      resource-dimension fields). `BreakdownPanel` renders, resource-dimension-only: a **Machine** column (e.g.
      "e2-highmem-8 · 8 vCPU · 64 GB", dash when unset — AWS has no machine-spec equivalent) and a **Waste** column
      badging idle-IP / orphaned-disk rows (amber "idle IP" / red "orphaned") with the row's own cost as the waste
      amount, dash for non-waste rows. `mock-api.ts` fixtures mirror the live audit's evidence resources
      (`harsh-static-ip`, `ikenna-windows-tokyo-restored`). tsc/ESLint/vitest (916 passed) all green. pw:L2 ✓ |
      regression: tests/smoke/cost-observability.spec.ts ("By resource shows machine specs + cost-waste badges" —
      asserts the machine-spec text renders, the orphaned-disk row carries an "orphaned" badge + its own $68.62 cost, a
      non-waste row dashes, and both columns disappear under "By bucket").
- [ ] [UI] P2. **Spot vs on-demand display.** A `purchase_option` column (or chip) on resource/service rows, from the
      backend field. vitest.
- [ ] [UI] P3. **Dimension-aware columns + leaf tables.** Show the right detail columns per dimension (VM cols under
      By-resource, bucket cols under By-bucket, SKU under By-SKU); apply the same detail columns to the `LeafPanel` "Top
      compute instances" / "Top storage buckets" tables. Detail columns scroll horizontally on narrow widths. pw:L2.
- [ ] [UI] P3. **Stale-during-refetch fix** (carried over from the parent plan). Gate the breakdown table body on
      `breakdown.dimension === dimension` (+ matching days), or skeleton the panel while `loadBreakdown` is in flight,
      so switching dimension/range never shows the prior fetch's rows under the new column header. pw:L2.
