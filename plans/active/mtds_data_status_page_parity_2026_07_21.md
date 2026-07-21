---
doc_type: plan
title: MTDS data-status page parity — catalogue explorer, MVP coverage split, per-instrument download-day granularity
summary: >-
  The instruments-service side of the shared DataStatusTab has an MVP/could-exist/all coverage-scope toggle
  (mvp_scope_catalogue_tagging_2026_06_08.md, shipped) and a Catalogue Explorer with search + CSV export
  (data_status_page_ux_and_canonicalisation_2026_07_16.md P6, shipped) — MTDS's side of the same shared component has
  neither, and is CONFIRMED BROKEN (operator screenshots 2026-07-21): the MTDS instrument-search box is gated behind a
  dead pre-rename service-name string so it never renders, and the underlying search/availability API has an independent
  request/response contract mismatch that returns wrong-category results even when reached; the MTDS coverage/drilldown
  panel renders 0%/empty where the instruments-service equivalent shows real data. Scope: fix the confirmed bugs, wire
  MVP scope into MTDS coverage, build the operator's described universal MTDS search (fixtures / leagues / instruments,
  type-aware drill-through) additive to the existing macro asset-group drilldown, and bring MDPS's view (same
  bucket/manifest as MTDS) to the same fixed state.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-ui,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    unified-api-contracts,
  ]
scope: [engineer]
tags: [deployment-ui, deployment-api, mtds, mdps, data-status, mvp, catalogue-explorer, parity, search, bug]
related:
  [
    mvp_scope_catalogue_tagging_2026_06_08.md,
    data_status_page_ux_and_canonicalisation_2026_07_16.md,
    data_status_cell_grid_rearchitecture_2026_07_18.md,
    deployment_redesign_cherrypicks_2026_07_20.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  operator ask 2026-07-21, four mid-session messages: (1) "add mvp tick box so we can see mvp instruments coverage vs
  non mvp instruments for all AGs, done in a performant way, catalogue instruments give us MVP"; (2) "the mtds
  deployment ui and api need revamp to have the same level of class as the instrument services page, albeit less about
  catalogue exploration — we could have an explorer where we can see via similar search capability if an instrument is
  downloaded and for what days, if the drilldown section doesn't give us that info at that granularity"; (3) two
  screenshots + "search need[s] to work and the whole mtds need[s] to be much faster", "this mtds screenshot data status
  you'd wanna be able to click through and see what's there for sports league search should drop down to odds and day
  availability and for other instrument dropdown to drilldown day availability this is a universal search bar for mtds
  data for fixtures, leagues, instruments etc. doesn't cancel the drilldown below it which is macro view split per AG"
  and "this is also clearly just broken right the drilldown for mtds showing nothing where instrument service one does
  show"; (4) "mdp should look basically same shards as mtds in the mdps view, its same bucket and manifest as mtds but
  separate view should all the fixed same perpks views and mtds" + "all this and above should be inside documented plan
  we[']re making human plan existing [and] actions together". Operator confirmed: human plan (not AO-dispatched), all
  asks bucketed into this one plan.
locked_by:
locked_since:
supersedes:
superseded_by:
---

# MTDS data-status page parity

> **Don't rebuild what already shipped.** Before writing code against any todo below, re-read
> `mvp_scope_catalogue_tagging_2026_06_08.md` and `data_status_page_ux_and_canonicalisation_2026_07_16.md` P6 in full —
> both are LIVE, shipped, and this plan's job is to extend their pattern to MTDS, not reinvent an MVP predicate or a
> catalogue-explorer UI from scratch.

## What already exists (confirmed 2026-07-21, do not duplicate)

- **UAC `is_mvp(asset_group, venue, instrument_type, data_type, ...)`** — a pure rules predicate, versioned
  (`MVP_SCOPE_CONFIG_VERSION`), covers all 5 asset_groups.
  `unified-api-contracts/.../canonical/crosscutting/mvp_scope.py`
  - siblings. **This is "catalogue instruments give us MVP"** — reuse this predicate, do not invent a new one.
- **Precomputed `mvp: bool` catalogue column** for cefi/defi/tradfi —
  `instruments-service/scripts/ build_instrument_catalogue.py::_add_mvp_column`, baked into `prod/catalog.parquet` at
  rollup time (performant: no live per-row `is_mvp` evaluation for these 3 asset_groups). **Sports/prediction still fall
  back to a live `df.apply(is_mvp_for_manifest_row)`** per asset_group year-coverage request — the one confirmed
  live-performance gap.
- **`CoverageScope = "could_exist"|"mvp"|"all"`** toggle on the venue-year-coverage grid
  (`deployment-api/deployment_api/routes/data_status/_coverage_scope.py`, `_live_coverage.py`) + a pill toggle in
  `deployment-ui/src/components/VenueCoverageTable.tsx` (default `mvp`) — **shipped and live for the coverage grid**.
- **A second, independent "MVP only" checkbox** in the per-instrument catalogue modal/explorer (`DataStatusTab.tsx`
  state `mvpOnly`; backend `_tag_is_mvp` + `mvp_only` param) — also shipped.
- **Catalogue Explorer** (`deployment-ui/src/components/CatalogueExplorer.tsx`, backend
  `deployment-api/deployment_api/ routes/data_status/_catalogue.py` + `catalogue_lifecycle.py`) — search, MVP badge, CSV
  export (`/catalogue`, `/download-catalogue-csv`). Shipped per `data_status_page_ux_and_canonicalisation_2026_07_16.md`
  P6.
- **A per-instrument availability lookup already exists in the shared component**: `DataStatusTab.tsx` has
  `instrumentSearchMode`/`instrumentAvailability` state (`api.InstrumentAvailabilityResponse`, carrying
  `availability_window` + `by_data_type`) wired to an instrument-search-then-availability flow. **UNCONFIRMED whether
  this already works end-to-end for `market-tick-data-service` or is gated to `instruments-service` only** — todo 1
  below traces this before any new UI is designed.
- **`DataStatusTab.tsx` is ONE shared component across services**
  (`SERVICES = ["instruments-service", "market-tick-data-service", ...]`), not separate per-service pages — "the
  instruments-service page" the operator means is this component with IS selected; parity means the SAME component
  behaves as well with MTDS selected, not a new page.

## What's a confirmed real gap

- **`deployment-api/deployment_api/services/data_status/mtds.py` has no `is_mvp` wiring at all** — MTDS coverage
  responses carry no MVP/non-MVP split today.
- **Sports/prediction catalogue MVP column is not precomputed** (live `df.apply` fallback) — a performance gap in the
  existing IS-side feature, not an MTDS-specific one, but the operator's "done in a performant way" concern applies here
  too; fix while touching this area.

## Confirmed bugs (2026-07-21 — research pass + operator screenshots, root-caused, not yet fixed)

### Bug A — MTDS instrument-search box never renders (dead pre-rename gate)

`deployment-ui/src/components/DataStatusTab.tsx:2495-2496` gates the entire "Instrument-Level Search" block
(`instrumentSearchMode`/`instrumentSearchQuery`/`instrumentSearchResults`/`instrumentAvailability`, added in `bc4d05f8`
2026-06-12) on:

```tsx
["market-tick-data-handler", "market-data-processing-service"].includes(serviceName);
```

`"market-tick-data-handler"` is a **dead pre-rename name** — MTDS was renamed to `"market-tick-data-service"` on
2026-03-10 (`2c75696`), three months before this block was written, so the string was already stale at authoring time.
Because `serviceName` is never `"market-tick-data-handler"`, this condition is always false for MTDS and the whole
search block silently never mounts — no fetch, no error, just an absent search box. The same dead string also lingers in
`ServiceDetails.tsx:226/238`, `CLIPreview.tsx:194`, and `api/client.ts`'s `TURBO_MODE_SERVICES`/
`TURBO_SUB_DIMENSION_SERVICES` lists. Zero test coverage exists for this block for any service (`grep` across
`*.test.tsx` for `instrumentSearchMode`/`"Instrument-Level Search"`/`"market-tick-data-handler"` returns nothing) — why
it was never caught.

### Bug B — even once visible, the search/availability contract is broken independent of Bug A

Two separate, deeper mismatches sit underneath Bug A (fixing the gate alone will NOT make search work correctly):

1. **Wrong request shape.** Frontend `api/client.ts:3594-3604` sends `instrument_key` to
   `GET /data-status/instrument-availability`. The backend route
   (`deployment-api/deployment_api/routes/data_status/ _query_meta.py:130-139`) requires `venue`, `instrument_type`,
   `instrument` as separate REQUIRED params — confirmed by its only test coverage
   (`tests/unit/test_route_data_status_live.py:583-591`), which never passes `instrument_key`.
2. **Wrong response shape.** Even with matching params, the backend (`data_query_service.py:786-859`) returns
   `{venue, instrument_type, instrument, date_range, effective_range, data_types, daily_availability, summary}` — none
   of which matches the frontend's `InstrumentAvailabilityResponse` type (`availability_window`, `overall`,
   `by_data_type`, `parsed`, `bucket`). A repo-wide grep for the literal string `"availability_window"` in
   `deployment-api` returns **zero hits** — no backend code anywhere constructs that field.
3. **The search-as-you-type box itself is shape-mismatched too**: `getInstrumentsList`/`get_instruments_list`
   (`data_query_service.py:193-271`) is asset_group-driven (correct — reference data lives in IS regardless of caller)
   but returns `instruments: sorted(list[str])` (plain filenames), while the frontend expects `InstrumentSearchResult[]`
   objects with `.instrument_key`/`.venue`/etc. **This is almost certainly why the operator's screenshot shows a "BTC"
   query returning SPORTS/EPL bookmaker rows** (`API_FOOTBALL`, `BETFAIR`, `BETONLINEAG`, …, all tagged `odds`) — with
   no typed filtering on the response shape, the UI is very likely rendering an unfiltered or wrongly-matched list
   rather than a real cross-category "BTC" symbol match.

**Verdict**: Bug A is a 1-line, high-confidence, near-zero-risk fix (swap the dead string). Bug B is a real
backend/frontend contract gap requiring either a new MTDS-aware backend implementation matching
`InstrumentAvailabilityResponse` (day-level `by_data_type` per the operator's "day availability" ask), or reconciling
the frontend type down to what `data_query_service.py` already returns. Fix A first (cheap, makes the box visible for
verification), then B (the real work) — do not ship A alone and call it done, the box will render but still return wrong
results per the screenshot evidence until B lands.

### Bug C — MTDS coverage/drilldown panel shows nothing / self-contradicts (operator screenshot, root cause NOT yet traced)

Operator screenshot: the MTDS "Data Coverage" TURBO panel shows **0.0% captured / shards** and **"1 missing shards"**
while the "Needs Attention" banner directly above it claims **"no failures, gaps, or stale captures in the current
range"** — a direct contradiction, and the drilldown that should back this up renders empty where the equivalent
instruments-service view shows real data. This is a SEPARATE bug from A/B (it's the coverage/drilldown data path, not
the instrument-search path) and has **not yet been traced** — first todo below.

## Desired UX (operator's explicit description, 2026-07-21)

A **single universal search bar for MTDS data** — covering fixtures, leagues, and instruments in one box — with
type-aware click-through:

- A **sports/league hit** drops down to **odds + day-level availability** for that league.
- An **instrument hit** (cefi/defi/tradfi) drills down to **day-level availability** for that instrument.
- This search bar is **additive** — it must NOT replace or cancel the existing macro drilldown below it (the
  asset-group-split view, `HierarchicalShardDrilldown`/`DataStatusDrilldown`). Both coexist: the macro view for browsing
  by asset_group/venue/date, the search bar for jumping straight to a known fixture/league/instrument.

## MDPS parity (operator ask 2026-07-21)

`market-data-processing-service` (MDPS) reads/writes the **same GCS bucket and manifest as MTDS** — it is a separate
service view over the same underlying shards, not a separate data model. Once MTDS's coverage/drilldown/search bugs
above are fixed, **the same fix must apply to MDPS's view** (same shard-level presentation, same perp/instrument views)
rather than MDPS being fixed separately or left behind — trace whether MDPS already shares the relevant deployment-api
service code with MTDS (likely, given the shared bucket) or has its own parallel implementation that independently needs
the same fixes.

## Todos

- [ ] [BACKEND] P0. **Fix Bug A** — swap the dead `"market-tick-data-handler"` string to `"market-tick-data-service"` at
      `DataStatusTab.tsx:2495-2496` (and the same dead string at `:2471`, `ServiceDetails.tsx:226/238`,
      `CLIPreview.tsx:194`, `api/client.ts`'s turbo-mode lists) so the search box actually renders for MTDS. Cheap,
      scoped, near-zero risk — do this first so Bug B's fix is independently testable against a visible UI.
- [ ] [BACKEND] P0. **Trace Bug C**: for a real MTDS venue/asset_group combination reproducing the operator's screenshot
      (0.0% captured, 1 missing shard, contradicting "Needs Attention: clean"), find the root cause in
      `deployment_api/services/data_status/mtds.py` / the TURBO coverage path — is the denominator wrong, is the
      manifest read returning empty, is there a stale-cache issue, or is "Needs Attention" and "Data Coverage" reading
      from two different (and inconsistent) sources. Write the finding as a Progress Log entry before fixing.
- [ ] [BACKEND] P0. **Fix Bug B**: reconcile the instrument-search + per-instrument-availability contract between
      `DataStatusTab.tsx`/`api/client.ts` and `deployment-api`'s `/instruments`/`/instrument-availability` routes —
      either implement the `InstrumentAvailabilityResponse` shape (`availability_window`, `by_data_type` with per-day
      granularity) backend-side for MTDS, or correct the frontend type + request params to match what
      `data_query_service.py` actually serves. `get_instruments_list` must return typed, category-correct results (fixes
      the "BTC" → SPORTS/EPL screenshot bug).
- [ ] [UI] P1. **Build the universal MTDS search bar** per the "Desired UX" section above: one search box for
      fixtures/leagues/instruments, type-aware click-through (sports → league → odds + day availability; instrument →
      day availability drilldown), additive to (not replacing) the existing macro asset-group drilldown. Reuse Bug B's
      fixed backend contract — do not design a third parallel data path.
- [ ] [BACKEND] P1. Wire UAC `is_mvp` into `deployment_api/services/data_status/mtds.py` the same way
      `_live_coverage.py` does for instruments-service-backed asset_groups — MTDS coverage responses gain the same
      `scope=mvp|could_exist|all` param and the `VenueCoverageTable` pill toggle works when MTDS is the selected
      service. Reuse `_coverage_scope.py`'s `filter_to_mvp`, do not fork a parallel implementation.
- [ ] [DATA] P1. Precompute `mvp: bool` for sports + prediction catalogues the same way `_add_mvp_column` already does
      for cefi/defi/tradfi (`build_instrument_catalogue.py`), eliminating the live `df.apply(is_mvp_for_manifest_row)`
      fallback path — this is the "performant way" half of ask (1), and closes the one precompute gap in the shipped MVP
      feature.
- [ ] [BACKEND] P1. **MDPS parity**: trace whether `market-data-processing-service`'s data-status view shares
      deployment-api service code with MTDS or has its own parallel path; apply every fix above (Bug A/B/C, MVP wiring,
      universal search) to MDPS's view too, so it shows the same shards/state as MTDS rather than drifting behind it.
- [ ] [BACKEND] P2. Also investigate whether `data_status_cell_grid_rearchitecture_2026_07_18.md`'s known OOM/slowness
      (81GB for full-history MTDS manifest loads) is the SAME root cause as the operator's "the whole mtds needs to be
      much faster" complaint, or a distinct perf issue specific to this page's coverage/search paths — annotate that
      plan rather than duplicating its scope if it's the same issue.
- [ ] [UI] P2. Once Bugs A/B/C are fixed and MVP-scope + universal search are wired: confirm the MTDS (and MDPS) view is
      genuinely at parity with the instruments-service view. `[UI]` + `pw:L2 ✓` + a regression spec per the playwright
      gate (per this workspace's UI-testing convention) — no tick without it.
- [ ] [REVIEW] P2. Post-phase codex/plan audit: confirm this plan's "already shipped" section still matches
      `mvp_scope_catalogue_tagging_2026_06_08.md` (which has its own open Phase-2+ features/strategy/model items,
      unrelated to this plan — don't pull those in) and annotate that plan's "Composes with" section with a pointer back
      here so a future reader doesn't re-discover the MTDS gap from scratch.

## Codex SSOTs

- `codex/02-data/honest-coverage-model.md`, `codex/02-data/availability-manifest-and-data-status.md` — coverage/
  manifest model this plan reads from (no new data model introduced).
- `codex/06-coding-standards/ui-testing-layers.md` — playwright gate for the UI todos.

## Composes with

`mvp_scope_catalogue_tagging_2026_06_08.md` (the MVP predicate + toggle this plan extends to MTDS + sports/prediction
precompute) · `data_status_page_ux_and_canonicalisation_2026_07_16.md` P6 (the Catalogue Explorer pattern this plan
reuses, not forks) · `data_status_cell_grid_rearchitecture_2026_07_18.md` (the cell-grid perf work — relevant if MTDS's
coverage view hits the same OOM/perf class once MVP filtering is added) ·
`deployment_redesign_cherrypicks_2026_07_20.md` (sibling deployment-ui/api workstream, same epic).

## Progress Log

### 2026-07-21 — plan created

Operator raised both asks mid-session while unrelated manifest-restamp work was in flight. Research pass (Explore
agent + direct grep) found most of the MVP-toggle machinery already shipped under
`mvp_scope_catalogue_tagging_2026_06_08.md` and the Catalogue Explorer already shipped under
`data_status_page_ux_and_canonicalisation_2026_07_16.md` P6 — this plan's scope is narrowed to the confirmed real gaps
(MTDS `is_mvp` wiring, sports/prediction catalogue precompute, and the unconfirmed-but-promising existing
instrument-availability flow) rather than re-designing from zero.

### 2026-07-21 (later same session) — Bugs A/B root-caused; operator screenshots confirm Bug C + supply the UX spec

Operator sent two screenshots plus explicit UX requirements, confirming the search flow is genuinely broken (not just
untested) and surfacing a second, independent bug in the coverage/drilldown panel:

- **Bug A** (dead `"market-tick-data-handler"` gate) and **Bug B** (search/availability request+response contract
  mismatch: `instrument_key` vs `venue`/`instrument_type`/`instrument`; `InstrumentAvailabilityResponse` shape never
  constructed anywhere backend-side; `get_instruments_list` returns untyped filenames) root-caused via a dedicated
  Explore pass — see "Confirmed bugs" section above for exact file:line citations. Neither fix has been applied yet.
- **Screenshot 1** (symbol search, query "BTC" → results tagged `SPORTS`/`EPL`/`API_FOOTBALL`/`BETFAIR`/etc.) is
  independent, strong evidence for Bug B's hypothesis 3 (untyped/wrongly-filtered search results) — a crypto symbol
  query should never surface sports bookmakers.
- **Screenshot 2** (MTDS "Data Coverage" TURBO panel: 0.0% captured, "1 missing shards", while "Needs Attention"
  directly above claims clean) is a NEW bug (**Bug C**) in the coverage/drilldown path, distinct from Bugs A/B — not yet
  traced. Operator: "the drilldown for mtds showing nothing where instrument service one does show."
- **Operator supplied the UX spec directly** (see "Desired UX" section) rather than leaving search-bar design open: one
  universal search bar for MTDS fixtures/leagues/instruments, sports hits drop to odds+day-availability, instrument hits
  drill to day-availability, additive to (never replacing) the existing macro asset-group drilldown.
- **New ask folded in**: MDPS shares MTDS's bucket/manifest and should receive the same fixes/view, not be handled as a
  separate effort — added as its own todo rather than a new plan.
- Reprioritized: Bugs A/B/C promoted to P0 (confirmed, operator-blocking) ahead of the MVP-wiring/precompute work, which
  remains real but is P1 (a gap, not a broken feature).
