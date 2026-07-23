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
status: complete
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [billing, cost, observability, breakdown, ui, deployment-ui, playwright]
related:
  [
    /plans/archive/2026_07/cost_observability_ui_2026_07_08.md,
    /plans/archive/2026_07/cost_obs_backend_sku_usage_enrichment_2026_07_08.md,
  ]
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

> **✅ ARCHIVED 2026-07-10 — COMPLETE.** Every todo shipped (see the Progress Log below). Codex aligned
> (`/codex/05-infrastructure/billing-cost-observability.md`: label dimension + real GitHub provider). Moved to
> `plans/archive/2026_07/`.

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

- `/codex/06-coding-standards/ui-testing-layers.md` — the Playwright L2 gate.
- `/codex/05-infrastructure/billing-cost-observability.md` — the API row contract the backend plan extends (net/gross/
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
      storage/class-split/$-per-GB
      columns formatted in GB, not bytes" — asserts the Storage cell reads "18,500 GB" not a raw byte count, the
      class-split cell lists "Standard", the $/GB
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
- [x] ✅ [UI] P2. **Spot vs on-demand display.** — deployment-ui@`5b99519`. Added `purchase_option` to
      `CostBreakdownRow` (mirrors the backend's resource/service-dimension field). `BreakdownPanel` renders a
      **Purchase** column, resource/service-dimension-only: a green "spot" badge, plain "on-demand" text, or a dash for
      "other"/non-compute rows. `mock-api.ts` fixtures give the backfill VMs "spot" (mirrors the workspace's
      spot-by-default backfill rule, `/codex/05-infrastructure/spot-vms-for-backfill.md`) and the AWS EC2 instance
      "on-demand". tsc/ESLint/vitest (85 tests) all green — 2 new vitest cases (chip on service rows, on-demand +
      column-omitted-on-other-dimensions on resource rows) per the plan's "vitest" spec for this task (no pw:L2 cited).
      Reconciled 2x onto concurrently-landed resource/waste-columns (`047494b`) and stale-during-refetch (`0b396a8`)
      commits touching the same 4 files; full QG green on each merge.
- [x] ✅ [UI] P3. **Dimension-aware columns + leaf tables.** — deployment-ui@`88c4b70`. The breakdown table's
      resource/bucket dimension columns were already dimension-gated from the P2 tasks above; this task's gap was the
      `LeafPanel` "Top compute instances" / "Top storage buckets" tables, which only rendered Name/Type/Cost. Added a
      `kind: "vm" | "bucket"` prop to `LeafPanel` and applied the SAME detail columns (same helpers, same data-testids)
      as the breakdown table: Machine + Waste (via a new shared `WasteCell`) for vm rows, Storage / Storage class /
      $-per-GB for bucket rows. Detail-column `<td>`s now render `whitespace-nowrap` (in both the breakdown table and
      the leaf tables) so narrow viewports genuinely scroll horizontally instead of wrapping; added `role="region"` +
      `tabIndex={0}` to the scroll wrappers to keep them keyboard-reachable (axe `scrollable-region-focusable` — a real
      a11y regression the new overflow caught, fixed in the same commit). Also fixed a mock-fixture gap: `mock-api.ts`
      only populated bucket `storage_gb`/`storage_class_gb` for the `dimension=bucket` query, not `dimension=resource`
      (which feeds the leaf tables) — keyed off `resource_kind` instead, matching the real backend's `_by_resource`.
      Reconciled onto the concurrently-landed resource/waste-columns (`047494b`), spot/on-demand (`5b99519`), and
      stale-during-refetch (`0b396a8`) commits touching the same file (rebase + manual merge, all four features kept).
      tsc/ESLint/vitest (919 passed, incl. 2 new cases) all green. pw:L2 ✓ (20/20, incl. the a11y suite) | regression:
      tests/smoke/cost-observability.spec.ts ("leaf tables carry the same dimension-aware detail columns as the
      breakdown table" + "leaf table detail columns scroll horizontally instead of overflowing on narrow widths").
- [x] ✅ [UI] P3. **Stale-during-refetch fix** (carried over from the parent plan). Gate the breakdown table body on
      `breakdown.dimension === dimension` (+ matching days), or skeleton the panel while `loadBreakdown` is in flight,
      so switching dimension/range never shows the prior fetch's rows under the new column header —
      deployment-ui@`0b396a8`. Two-part fix: (1) a request-token guard in `loadBreakdown()` so a slower, now-stale
      response can never resolve after a newer one and clobber fresher state; (2) a render-time freshness gate
      (`breakdown.dimension/cloud/days === current state`) — the table body renders a loading placeholder instead of the
      prior fetch's rows whenever `breakdown` hasn't caught up to the currently-selected filters. Added a
      `__mockBreakdownDelayMs` test hook to `mock-api.ts` so a spec can deterministically slow one dimension's response
      to reproduce the out-of-order-response race. Reconciled onto two concurrently-landed column commits (`0d33ef0` SKU
      dimension, `047494b` resource/waste columns) touching the same files. tsc/ESLint/vitest (916 passed) all green.
      pw:L2 ✓ | regression: tests/smoke/cost-observability.spec.ts — two new cases: "switching dimension never shows the
      prior fetch's rows under the new header (loading gate during refetch)" (asserts the loading gate appears + old
      rows never show under the new header while a slowed fetch is in flight) and "a stale slower response never
      clobbers a fresher one after a rapid dimension switch" (asserts a late-resolving stale response never overwrites a
      fresher one). Both verified to FAIL without the fix before being kept.
- [x] ✅ [UI] P3. **Per-column dropdown filters + larger resize grip** (operator request 2026-07-10, follow-up to the
      single search box, which only matched the pre-aggregated rows already shipped). Replaced the one search `<input>`
      with a per-column filter row in the table header: one `<select>` per categorical column (Label/dimension, Detail,
      Purchase, Storage class, Machine), each populated with the DISTINCT values PRESENT in the fetched rows (dynamic,
      not a fixed list) via the same `sortValue` accessor the header sorts by — so a single ordered column model is the
      SSOT for the header row, the filter row, and the colSpan maths (they can't drift). Filters AND-combine, gate on
      `!stale` (no stale options leak during refetch), auto-drop a selection that no longer exists after a dimension
      switch, and a "Clear filters (N)" button appears only when any are active. Also enlarged the breakdown resize grip
      (6px→12px scoped `::-webkit-scrollbar` + a painted diagonal `::-webkit-resizer`, cyan-on-hover with a light-theme
      override) so the drag handle is easy to see and grab — deployment-ui@`1b6531d`. tsc/ESLint/vitest (917 passed; 4
      assertions tightened to `tbody`-scope now that distinct values also render as dropdown options) all green. pw:L2 ✓
      (17/17) | regression: tests/smoke/cost-observability.spec.ts "By-label dimension: label-key selector + per-column
      filter + pagination + resizable container" (selects a value in the dynamic Label dropdown → table narrows to the
      matching row → Clear filters restores the paginated set). NOTE: this is client-side filtering of the cached,
      pre-aggregated rows; richer server-side faceted filtering over a fuller cached fact set is entangled with the
      deployment-api-wide caching redesign (Redis/DuckDB) and deferred to a dedicated session.
- [x] ✅ [BACKEND] P3. **GitHub billing number-check** (operator "verify the github billing is actually correct",
      2026-07-10). Reconciled `fetch_github_billing()` output against the raw GitHub Enhanced Billing API for the live
      30-day window (same Secret-Manager token, never printed): records 1,469 == 1,469; **NET $1,332.55 == $1,332.55**;
      gross $1,430.97 == $1,430.97; credit −$98.42 == −$98.42 — exact to the cent. Confirms the mapping (`cost`=gross,
      `credit`=net−gross, net=cost+credit) and the `[start,end)` window slice. Context: June full-month net
      $1,441,
      July-to-date $221. The displayed GitHub figure is verified correct — no code change (provider already
      shipped).
- [x] ✅ [UI] P3. **Cost page layout refresh + help guide** (operator review session 2026-07-10). Five folded UI
      refinements on `/ops/costs`: (1) the breakdown header is now ONE row — title + dimension tabs + dimension note +
      stats share a line (was two), reclaiming vertical space; (2) the per-column filter dropdowns moved INTO each
      categorical column header, beside the sort label (was a separate row that covered data on vertical scroll) —
      compact `<select>`s with `stopPropagation` so filtering never triggers the sort; (3) the "Cloud share" donut is
      folded into the Total-spend card (its standalone panel removed) via a size-parameterised `CloudDonut`; (4) the top
      is now 2 columns — a bigger daily chart on the left, all 4 KPI cards (total + 3 sources) stacked on the right —
      and the per-card sparklines are dropped (the left chart already carries that trend; `Sparkline`/`mergeDaily`
      deleted); (5) a **help-guide dialog** (`?` button in the top bar, reuses `ui/dialog`) with a short term→definition
      guide to the page, every KPI, and every breakdown column — and the "recent days are provisional" note moved OUT of
      the standing page banner INTO this guide. deployment-ui@`a9795f32`. tsc/ESLint/vitest (coverage 75.83%) + build
      all green. pw:L2 ✓ (18/18) | regression: tests/smoke/cost-observability.spec.ts "help guide: opens from the top
      bar, carries the moved provisional note, closes on Escape" (+ the existing per-column-filter case still green
      against the relocated header dropdowns).
