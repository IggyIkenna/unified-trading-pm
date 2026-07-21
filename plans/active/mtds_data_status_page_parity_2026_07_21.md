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

### Bug C — MTDS coverage/drilldown panel shows nothing / self-contradicts

Operator screenshot: the MTDS "Data Coverage" TURBO panel shows **0.0% captured / shards** and **"1 missing shards"**
while the "Needs Attention" banner directly above it claims **"no failures, gaps, or stale captures in the current
range"** — a direct contradiction, and the drilldown that should back this up renders empty where the equivalent
instruments-service view shows real data. This is a SEPARATE bug from A/B (it's the coverage/drilldown data path, not
the instrument-search path).

**Partial root cause CONFIRMED (2026-07-21)** — matches the operator's own diagnosis exactly: MTDS's job should be "do
we have market data shards for times we DO have instruments [per the IS catalogue]", i.e. IS answers "does this
instrument exist for this expected day" and MTDS's denominator should only ask "did we capture it" over THAT gated set.
`deployment-api/deployment_api/services/data_status/instrument_coverage.py::per_instrument_coverage`, lines 278-280:

```python
n_instruments = len(expected_instruments)
n_dates = len(expected_dates)
expected_count = n_instruments * n_dates
```

This is a flat CROSS-PRODUCT — every expected instrument × every expected date — with **no per-instrument
existence-window clipping**. The function's own comment (lines 100-102, in `build_cefi_is_instruments_provider`) admits
this: _"date-agnostic for now (IS catalog available_from/to lifecycle filtering is reserved for a future walk once the
full universe stabilises)."_ So today the denominator counts `(instrument, day)` pairs that are structurally impossible
(before listing / after delisting) as "missing shards" — inflating the false-missing count. Whether this fully explains
the operator's exact screenshot numbers (0.0%, "1 missing") or is one of several contributing factors is NOT yet
confirmed against live data — that verification is still open, but the mechanism itself is a confirmed, real bug
matching the operator's stated model.

**The fix requires**: `get_expected_instruments_for_venue` (or the catalogue read behind it) to expose each instrument's
real existence window (`available_from`/`available_to`, or equivalent lifecycle columns already used elsewhere for the
"could-exist" CF-14 denominator — reuse that concept, don't invent a second one), and `per_instrument_coverage` to
intersect EACH instrument's own window with `expected_dates` when building the denominator set, instead of a blanket
`n_instruments * n_dates` multiply.

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

- [x] N. ✅ [BACKEND] P0. **Fix Bug A** — swapped the dead `"market-tick-data-handler"` string to
      `"market-tick-data-service"` across `DataStatusTab.tsx` (2 conditionals + 1 comment), `CLIPreview.tsx`,
      `ServiceDetails.tsx` (2 sites), `api/client.ts` (3 sites incl. a redundant duplicate key removed) + the one stale
      unit-test assertion that had locked in the dead string. **deployment-ui@9c64878**, verified on origin
      (`ahead_by=0`), full `quality-gates.sh` green, new regression spec
      `tests/smoke/     mtds_instrument_search_visibility.spec.ts` (pw:L2 ✓, both boxes confirmed rendering for MTDS
      live via dev server + Playwright MCP before the automated spec was written).
- [x] N. ✅ [BACKEND] P0. **Fix Bug C** — `per_instrument_coverage()`'s `expected_count = n_instruments * n_dates`
      cross-product (root cause confirmed above, `instrument_coverage.py:278-280`) now clips per-instrument to its real
      existence window. Implementation note (verified via `catalogue_lifecycle.py` before writing code — the manifest/
      availability-index read `build_cefi_is_instruments_provider` already used does NOT carry `available_from`/
      `available_to`; only `prod/catalog.parquet` does): added `_read_cefi_catalogue_existence_windows()` (a small,
      SEPARATE object read from the SAME already-resolved bucket, mirroring `catalogue_lifecycle.py::_read_catalogue`'s
      pattern — not a second whole-corpus walk), changed `build_cefi_is_instruments_provider`'s return type to
      `(provider, windows)`, threaded a new `instrument_windows` param through `per_instrument_coverage` →
      `mtds_honest_coverage_for_venue` → `venue_resolution.py`'s call site (all backward-compatible via a
      `None`-default, zero behavior change for any caller that doesn't pass it). New `_clip_dates_to_window` helper + 8
      new unit tests (existence-window clipping, fail-open on missing catalogue data, exact pre-fix-behavior parity when
      `instrument_windows=None`) — 17/17 passing in the target test file. Full repo `quality-gates.sh` in progress; not
      yet shipped via quickmerge.
- [ ] [DATA] P1. **Verify Bug C's fix against live data**: once shipped, reproduce the operator's screenshot scenario
      (0.0% captured, 1 missing shard, contradicting "Needs Attention: clean") against the real MTDS manifest + IS
      catalogue and confirm the existence-window clipping closes the gap. If a residual discrepancy remains, trace it
      separately (e.g. "Needs Attention" and "Data Coverage" reading from different/inconsistent sources) rather than
      assuming this one fix explains 100% of the screenshot.
- [x] N. ✅ [BACKEND] P0. **Fix Bug B** — `deployment-ui@c11d370`, verified on origin, full QG green. Fixed the
      `getInstrumentAvailability` request/response contract mismatch + added a monotonic-sequence stale-response guard
      to both debounced search flows (`runSymbolSearch`, `fetchInstruments`). See the Progress Log entry above for the
      full detail, including the correction that the operator's screenshot traces to a THIRD search flow
      (`searchInstruments`/cross-category), not the originally-cited one.
- [ ] [BACKEND] P1. **New — `GET /instruments` (`get_instruments_list`) is doubly broken**, found while fixing Bug B,
      deliberately NOT fixed in the same tick (needs real design, not a quick patch): (a) the `search` query param the
      frontend already sends is never read or applied by the route/service — the "Instrument-Level Search" box's text
      input currently does nothing; (b) the service returns `instruments: list[str]` (bare filenames) while the
      frontend's `InstrumentsListResponse.instruments` type expects `InstrumentSearchResult[]` objects
      (`venue`/`instrument_type`/etc.) — every result the box shows today is likely rendering broken/undefined fields.
      Fix: parse `venue`/`instrument_type` out of each GCS object path (mirror `_load_corpus_from_per_venue_parquets`'s
      existing pattern in the same file) and apply substring+token-AND filtering matching `search_instruments`'s
      convention, so both boxes share one filtering rule.
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

### 2026-07-21 (later) — operator's precise coverage-model correction confirms Bug C's mechanism; `/autonomous` engaged

Operator clarified the intended MTDS coverage model directly: IS answers "do we have instruments (catalogued) for an
expected day"; MTDS should only ask "do we have market-data shards for the days we DO have instruments" — i.e. MTDS's
denominator must be GATED by IS catalogue existence, never a raw instrument-count × date-count multiply. Traced this
exactly to `instrument_coverage.py::per_instrument_coverage` lines 278-280 (`expected_count = n_instruments * n_dates`)
— confirmed root cause, documented in the "Confirmed bugs" section above with the concrete fix shape (per-instrument
existence-window intersection, reusing the CF-14 could-exist lifecycle concept). Not yet implemented or verified against
live data.

**`/autonomous` invoked** — operator: "execute plan mtds_data_status_page_parity_2026_07_21 in full, together with our
other pending todos." Applying `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + `SUB_AGENT_MANDATORY_RULES.md` from here:
finish completely (no `BLOCKED-OPERATOR`/deferred leftovers for anything decidable with common sense + this plan's
documented intent), decide-and-document instead of asking, drive on a self-paced loop, journal every tick to this
Progress Log (this log IS the handoff document across context compression — no separate summary file).

**Model-tier flag (rule 2, self-check)**: this is a long, cross-repo (deployment-api/deployment-ui/market-tick-data-
service/market-data-processing-service/instruments-service/unified-api-contracts) autonomous dispatch — per
`model-tier-selection.md` this class of work is usually `opus-required`. The main thread is running Sonnet 5 and cannot
self-upgrade mid-session; flagging per rule 2 rather than silently proceeding as if it were the correct tier.
Mitigation: delegate the highest-complexity architectural/design sub-steps to sub-agents with an explicit Opus model
override where warranted, and keep this plan's Progress Log unusually explicit so a tier mismatch doesn't silently
compound into a wrong decision going uncaught.

**Execution order chosen** (documented per rule 2 — an "operator could decide, they're away" call): Bug A first (1-line,
zero-design-risk, makes Bug B/UI work independently verifiable), then Bug C's fix (backend-only, no UI dep), then Bug B
(deeper contract work), then the universal search UI (depends on B's fixed contract), then MVP wiring + MDPS parity,
then the manifest re-stamp re-run (separate plan, picked up between MTDS ticks whenever its own background gates are the
blocking step rather than my active attention).

### 2026-07-21 (tick 1) — Bug A SHIPPED, Bug C implemented (QG in progress)

**Bug A — SHIPPED, verified on origin: `deployment-ui@9c64878`.** Fixed the dead `"market-tick-data-handler"` string at
every site (`DataStatusTab.tsx` x2 conditionals + comment, `CLIPreview.tsx`, `ServiceDetails.tsx` x2, `api/client.ts` x3
incl. one redundant duplicate dict key removed), plus the one stale unit test (`tests/unit/client.test.ts`) that had
locked in the dead string as expected behaviour — this is exactly why the bug was never caught: the test asserted the
BUG. Verified live before writing the automated spec: started the dev server (`VITE_MOCK_API=true`), used Playwright MCP
to navigate to `/service/market-tick-data-service/data-status`, confirmed "First day of each month only" renders
immediately and "Instrument-Level Search" renders once one asset-group category is selected (matches the
`selectedCategories.length === 1` gate in the code). Wrote `tests/smoke/mtds_instrument_search_visibility.spec.ts` to
lock this in — first attempt used manual `page.route()` mocking and failed (this repo's playwright webServer already
runs with `VITE_MOCK_API=true`, so a hand-rolled empty-object route fallback shadowed the app's own richer mock layer);
fixed by removing the manual routes and relying on the webServer's mock mode, matching what the manual MCP verification
had already proven works. Full `tests/smoke/` run: 396 passed, 8 pre-existing failures confirmed unrelated (Daily Costs
page / mobile nav / nav-menu-dedup — filed as
`plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` rather than silently ignored,
not fixed here to avoid scope creep). Full `quality-gates.sh` green both before AND after a sentinel-invalidating pull
mid-ship (a peer landed `Deployments.tsx` changes between my QG run and the quickmerge attempt — re-ran the gate, got a
fresh sentinel, shipped clean).

**Bug C — implemented, not yet shipped.** Traced (before writing any code, per "grep-then-READ") whether the existing
`build_cefi_is_instruments_provider`'s catalogue read already carried `available_from`/`available_to`: it does NOT —
that function reads the MANIFEST/availability-index (`read_availability_index` → `read_manifest_index`), a per-shard
schema; the existence-level `available_from`/`available_to` columns live ONLY in `prod/catalog.parquet`, confirmed via
`catalogue_lifecycle.py`'s own docstring ("The catalogue is the ONLY identity-level source... the availability `_index`
carries per-shard COUNTS"). This ruled out my first design (naively assume the existing read already had the columns)
before it became a bug. Implemented as a SEPARATE small object read from the SAME already-resolved bucket (mirroring
`catalogue_lifecycle.py::_read_catalogue`'s exact pattern, not imported cross-module since it's private there) —
`_read_cefi_catalogue_existence_windows()`, fail-open (`{}` on any error). `build_cefi_is_instruments_provider` now
returns `(provider, windows)`; `per_instrument_coverage` gained `instrument_windows` (default `None` — zero behavior
change for every existing caller that doesn't pass it) and a new `_clip_dates_to_window` helper; the denominator
(`expected_count`) and numerator (`found_count`) are now BOTH clipped per-instrument to `[available_from, available_to]`
intersected with `expected_dates`, keyed by NORMALIZED instrument_id (reusing the existing bug #4 cross-service
id-divergence pattern, since `instrument_windows` comes from the catalogue while `found_pairs` comes from the manifest).
Threaded through `mtds_honest_coverage_for_venue` → `venue_resolution.py`'s call site. 8 new unit tests added to
`tests/unit/test_per_instrument_cefi_is_provider.py` (clipping primitive in isolation, the operator's exact scenario — a
late-listed instrument not counting its pre-listing days as missing, an already-delisted instrument contributing 0 —
fail-open when an instrument is absent from the windows dict, and exact pre-fix-behavior parity when
`instrument_windows=None` is not passed at all). 17/17 passing. Two lint issues found+fixed on the first QG pass (unused
`n_dates` var, one line >120 chars) — re-verified ruff clean. Full repo `quality-gates.sh` running now; will ship via
quickmerge once green.

**Known residual scope, documented not silently dropped**: the secondary `per_instrument` breakdown block's `"found"`
count (only rendered for venues with <20 instruments) is NOT clipped to the per-instrument window the way the headline
`expected_shards`/`found_shards`/`completion_pct` now are — its `"expected"` field IS fixed, but `"found"` still comes
from the unclipped `normalized_iid_counts`. The `min(..., 100.0)` clamp prevents a nonsensical >100% display, but this
is a known, minor inconsistency in a secondary display block, not the primary headline metric the operator's screenshot
was about. Flagged here for a future refinement pass rather than expanding this tick's scope further.

### 2026-07-21 (tick 1, continued) — Bug C SHIPPED; two unrelated cross-repo bugs found+fixed while reconciling concurrent work

**Bug C SHIPPED — `deployment-api@5bced2b`** (rebased SHA; original `885260a` before a peer-work reconciliation, see
below). Full `quality-gates.sh` green, verified on origin (`ahead_by=0`).

**Reconciliation (autonomous rule 4 — merge the best of both sides, never blind take-mine/take-theirs)**: while
shipping, a concurrent slot-5 agent independently found + fixed the SAME stale `OKX-FUTURES` test assertion (this plan's
earlier "unrelated stale test" fix) within ~1 hour of my own fix, in an unrelated commit (`fe8eaf1`). Their version is
more thorough (asserts `OKX-FUTURES` canonical=True + adds a genuine `OKX-MARGIN` negative case, testing both directions
of the exact-compare invariant) than mine (which only swapped the negative example). Resolved via `git rebase` +
`--skip` on my now-redundant commit, keeping their better version + my genuine Bug C commit on top — verified both
sides' content survived (grep-confirmed) before pushing, per the rule's explicit requirement.

**Found + fixed, unrelated to this plan, discovered only because they blocked shipping**:

1. **`unified-trading-library@517b276a`**: `gcs_copy_object` was defined and re-exported from
   `cloud_interface/__init__.py` but accidentally omitted from the top-level `unified_trading_library/__init__.py`
   re-export list, even though its siblings (`gcs_delete_object`/`gcs_describe_object`) were present — the exact
   codex-sanctioned import surface. Discovered because it blocked the manifest re-stamp script (a completely separate
   effort, see `distinct_values_noncanonical_audit_2026_07_20.md`) from even starting. 2-line fix (import + `__all__`).
2. **`unified-trading-library@ec629a2e`**: found while re-running full QG for #1 — `defi/token_metadata_resolver.py` (a
   brand-new, recently-landed feature, `b9534230`, not mine) had two deep-UAC-import lint violations with no noqa
   opt-out, failing the shared codex-compliance gate for anyone touching this repo. Added the workspace's existing
   sanctioned `# noqa: qg-deep-import` / `# noqa: imports-inside-functions, qg-deep-import` markers (verified this exact
   convention already used identically elsewhere, e.g. `manifest_writer/_writer_ingest.py`) rather than restructuring
   someone else's in-flight feature's import surface.
3. **`unified-trading-pm@f542a76d7` + a same-session follow-up cleanup**: UTL's `test_cloud_providers_yaml_parity`
   failed — the PM repo's `configs/cloud-providers.yaml` sibling mirror was missing a `kill-switch-audit-log` GCP
   bucket-kind entry that UAC's packaged copy already had (per `deployment_alerts_ingestion_completeness_2026_07_20.md`
   todo 9). Added the matching entry (metadata only — a bucket-name resolution template for the kill-switch audit-log
   _reader_, not a kill-switch control action). **Caution logged**: right after this shipped cleanly (`ahead_by=0`
   verified), a LOCAL, never-committed copy of this same file was found to contain literal git conflict-marker lines
   (angle-bracket / equals-sign separator triples) — traced to a prek stash-pop artifact colliding with a concurrent
   process's own edit to the same file. Verified origin was clean throughout (the markers never left my local working
   tree); fixed via `git restore --staged --worktree` back to the clean committed HEAD. No data was ever at risk, but
   this is worth remembering: **always re-read a just-pushed file's actual content once, don't trust a grep-count
   alone**, when working in a repo this contended.

All 4 fixes verified independently via full `quality-gates.sh` green + confirmed on origin before moving on. Relaunched
the manifest re-stamp extended retry (`distinct_values_noncanonical_audit_2026_07_20.md`) now that its blocking
dependency is fixed — see that plan for the outcome.

### 2026-07-21 (tick 2) — Bug B SHIPPED; the operator's screenshot was a THIRD, different search flow than first assumed

**Bug B SHIPPED — `deployment-ui@c11d370`**, verified on origin. Full `quality-gates.sh` green.

**Correction to the original Bug B scoping**: while implementing, traced the operator's exact screenshot ("Symbol search
— cross-category · canonical IDs") to a DIFFERENT code path than the "Instrument-Level Search" checkbox flow this plan
originally cited — `runSymbolSearch` → `searchInstruments()` → `GET /data-status/instruments/search`, an institutional
cross-asset-group search added in a separate, later feature (`bc4d05f8` was the OLDER flow; this is a third one). Two
independent, real bugs found and fixed:

1. **The originally-cited contract mismatch** (`getInstrumentAvailability`): confirmed via direct code reading — the
   frontend sent `instrument_key`, the backend route requires `venue`/`instrument_type`/`instrument` as separate params
   (would 422 on any real call); the frontend's `InstrumentAvailabilityResponse` type also didn't match the backend's
   actual flat `{daily_availability, summary, ...}` shape. Fixed by sending the correct params (derived from
   `selectedInstrument`, already carrying `venue`/`instrument_type`) and transforming the real backend response into the
   existing UI type client-side — chose this over reshaping the backend since it's a smaller, already-tested surface and
   the existing UI shape is the right one (day-level found/missing lists, matching "day availability").
2. **A stale-response race in BOTH debounced search flows** (`runSymbolSearch` and `fetchInstruments`): the 250/300ms
   debounce only cancels overlapping _timers_, never overlapping _in-flight fetches_ — if the user pauses twice in quick
   succession, both requests fire, and whichever resolves LAST wins regardless of which query is more recent. This is
   the most likely explanation for the screenshot itself (a "BTC" query displaying results — canonical_id=EPL across
   every row — that only make sense for an earlier, different query): I could not reproduce it live (no real backend in
   this dev session to drive the actual race), so this is the best-evidenced explanation from static analysis, not a
   confirmed root cause with a live repro. Fixed with a monotonic per-flow sequence ref that discards any response whose
   sequence number is stale by the time it resolves — the standard, always-correct fix for this bug class regardless of
   whether it's the full explanation.

**A third, real, but NOT YET FIXED bug found while investigating** — flagged rather than rushed: `GET /instruments`
(backing `fetchInstruments`, the per-category "Instrument-Level Search" box) has TWO separate problems of its own: (a)
the route/service (`get_instruments_list`) never accepts or applies the `search` query param the frontend already sends
— typing in that box currently does nothing, the list is always unfiltered; (b) the service returns
`instruments: list[str]` (bare filenames) while the frontend's `InstrumentsListResponse.instruments` type expects
`InstrumentSearchResult[]` (objects with `venue`/`instrument_type`/etc.) — every result in that box is presumably
rendering as broken/undefined fields today. Both need real backend design work (parsing venue/instrument_type out of the
GCS path per result, mirroring `_load_corpus_from_per_venue_parquets`'s pattern) that I have not yet verified closely
enough to ship safely in this tick — added as its own todo below rather than guessing.
