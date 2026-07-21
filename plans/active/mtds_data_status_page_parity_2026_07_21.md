---
doc_type: plan
title: MTDS data-status page parity — catalogue explorer, MVP coverage split, per-instrument download-day granularity
summary: >-
  The instruments-service side of the shared DataStatusTab has an MVP/could-exist/all coverage-scope toggle
  (mvp_scope_catalogue_tagging_2026_06_08.md, shipped) and a Catalogue Explorer with search + CSV export
  (data_status_page_ux_and_canonicalisation_2026_07_16.md P6, shipped) — MTDS's side of the same shared component has
  neither: deployment-api's MTDS coverage service has no is_mvp wiring, and it's unconfirmed whether the existing
  per-instrument availability lookup already answers "was instrument X downloaded, and on which days" for MTDS or is
  IS-only. Bring MTDS to the same capability level, reusing the shipped IS patterns rather than rebuilding them.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [deployment-ui, deployment-api, mtds, data-status, mvp, catalogue-explorer, parity]
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
priority: P2
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  operator ask 2026-07-21 (mid-session, two messages): (1) "add mvp tick box so we can see mvp instruments coverage vs
  non mvp instruments for all AGs, done in a performant way, catalogue instruments give us MVP"; (2) "the mtds
  deployment ui and api need revamp to have the same level of class as the instrument services page, albeit less about
  catalogue exploration — we could have an explorer where we can see via similar search capability if an instrument is
  downloaded and for what days, if the drilldown section doesn't give us that info at that granularity". Operator
  confirmed: human plan (not AO-dispatched), both asks bucketed into this one plan.
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
- **Whether MTDS instrument availability-by-day works today is unconfirmed** (see todo 1) — this may already largely
  satisfy ask (2), or may need real backend work if `instrument_key`/`InstrumentAvailabilityResponse` assumes an IS
  catalogue shape that doesn't map onto MTDS's manifest rows.

## Todos

- [ ] [BACKEND] P0. **Trace, don't assume**: for a real MTDS venue/instrument, drive the existing `instrumentSearchMode`
      → `instrumentAvailability` flow end-to-end (UI or direct API call) with `service=market-tick-data-service`
      selected. Confirm/deny: (a) does instrument search return MTDS instruments at all; (b) does the availability
      response's `by_data_type`/`availability_window` reflect real MTDS manifest rows or empty/wrong data; (c) does it
      already show WHICH DAYS were captured, or only a window/count. Write the answer as a Progress Log entry before
      touching any other todo — it determines whether (2) below is a UI-only fix or needs new backend logic.
- [ ] [BACKEND] P1. Wire UAC `is_mvp` into `deployment_api/services/data_status/mtds.py` the same way
      `_live_coverage.py` does for instruments-service-backed asset_groups — MTDS coverage responses gain the same
      `scope=mvp|could_exist|all` param and the `VenueCoverageTable` pill toggle works when MTDS is the selected
      service. Reuse `_coverage_scope.py`'s `filter_to_mvp`, do not fork a parallel implementation.
- [ ] [DATA] P1. Precompute `mvp: bool` for sports + prediction catalogues the same way `_add_mvp_column` already does
      for cefi/defi/tradfi (`build_instrument_catalogue.py`), eliminating the live `df.apply(is_mvp_for_manifest_row)`
      fallback path — this is the "performant way" half of ask (1), and closes the one precompute gap in the shipped MVP
      feature.
- [ ] [BACKEND] P1. If todo 1 finds the availability flow does NOT already answer "downloaded on which days" for MTDS
      (e.g., it only returns a window/count, not a per-day list): design + ship a per-instrument day-level availability
      endpoint for MTDS, reusing the manifest's existing per-row `capture_status`/`date` columns (no new data model —
      this is a read/aggregation over rows that already exist) rather than a new corpus walk (single-walk discipline
      applies).
- [ ] [UI] P1. If todo 1 confirms the search+availability affordance works but is rough/IS-flavoured for MTDS: extend
      `DataStatusTab.tsx`'s instrument-search UI so results + the availability panel read correctly for MTDS instrument
      keys/venues (folder/instrument_type labels, venue axis, etc. — MTDS's shard atom differs from IS's). Do NOT build
      a parallel MTDS-only search component — same component, service-aware.
- [ ] [UI] P2. Once MVP-scope + availability-by-day are wired, confirm the MTDS view is genuinely at parity with the
      instruments-service view for: MVP toggle, catalogue/instrument search, per-instrument availability drilldown.
      `[UI]` + `pw:L2 ✓` + a regression spec per the playwright gate (per this workspace's UI-testing convention) — no
      tick without it.
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
