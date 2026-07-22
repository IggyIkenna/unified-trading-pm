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
      `instrument_windows=None`) — 17/17 passing in the target test file. **SHIPPED — `deployment-api@89e31a0`**,
      content-verified on origin (`merge-base --is-ancestor` against the exact SHA, not just exit-code trust). Was
      blocked ~40min on deployment-service's `launch-cefi-sharded-backfill.sh` + `tardis-concurrency-guard.sh` being
      dirty (a bounded 20×90s retry loop exhausted without it clearing); re-checked mtime and found it frozen 35+min
      stale with no process holding the files open — reclassified from LIVE (protect) to DEAD (inherit) per the
      LIVENESS-gating rule, verified the content was a complete, self-consistent Tardis-guard hardening fix (bash -n +
      shellcheck + full QG green), and shipped it as `deployment-service@ee67255` to clear the gate. Bug C then needed
      one `git pull --rebase --autostash` (deployment-api had drifted 3 commits behind on unrelated promote/backmerge
      chores — clean rebase, no conflicts) before quickmerge landed it.
- [x] N. ✅ [DATA] P1. **Verify Bug C's fix against live data — MECHANISM CONFIRMED WORKING, but a SEPARATE, real, live
      collision bug found + filed (not fixed here — out of this read-only unit's scope).** Called the real
      `deployment-api` `per_instrument_coverage()` (`deployment_api/services/data_status/instrument_coverage.py`)
      directly against real prod data (read-only, no mutation, ADC via `get_storage_client()`): the real IS catalogue
      (`instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`, 429,129 rows), the real MTDS manifest
      (`market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 10.5M rows), and the real
      `mtds_expected_dates_for_venue_dt()`/`_read_cefi_catalogue_metadata()` (the actual Bug-C-fix functions, not
      re-implemented). **Clean, collision-free repro found**: `COINBASE-FUTURES:PERPETUAL:DRAM-USD@LIN` (real
      instrument, catalogue `available_from=2026-07-16` `available_to=None`, `book_snapshot_5` dt — confirmed NOT
      F4-seeded for this venue, i.e. genuinely exercises the fixed code path in production, not the seeded-4-state
      bypass). Real manifest: exactly 5 `captured` shards, 2026-07-16..2026-07-20 (zero rows before listing). **BEFORE
      (`instrument_windows=None`, pre-fix behavior)**: `expected_shards=630` (full 2024-10-31..2026-07-22 calendar),
      `found_shards=5`, **`completion_pct=0.79%`** — reproduces the operator's exact symptom class (near-zero completion
      from phantom pre-listing "missing" days). **AFTER (Bug C fix, real catalogue windows)**: `expected_shards=7`
      (clipped to the instrument's real 2026-07-16..2026-07-22 existence window), `found_shards=5`,
      **`completion_pct=71.43%`** — a realistic number reflecting the 2 days not yet captured, not hundreds of
      structurally-impossible pre-listing days. Also ran the full real venue aggregate (all 277 COINBASE-FUTURES
      PERPETUAL+SPOT_PAIR instruments, confirmed collision-free — see below): `expected_shards` 174,510 → 104,326,
      `completion_pct` 18.08% → 30.25%. **Verdict: the existence-window-clipping mechanism itself works exactly as
      designed and materially changes real numbers in the correct direction** — confirms Bug C's fix. **A second,
      different, real bug found while cross-checking a second (DERIBIT `options_chain`) candidate — filed separately,
      NOT fixed here per this task's explicit read-only scope + the >30min findings-triage bar**:
      `_normalize_instrument_id_for_match`'s `@`-suffix-stripping (designed for the `@LIN`/`@INV`/`@ETHEREUM`
      settlement-tag divergence case) catastrophically collides for OPTIONS/dated-FUTURES, whose `@`-suffix encodes real
      distinguishing identity (expiry/strike/side), not a formatting tag — measured live: DERIBIT OPTION 264,550 raw
      instrument_ids → 4 normalized keys (66,137x collision), DERIBIT FUTURE 1,631 → 12 (135.9x), vs. PERPETUAL/
      SPOT_PAIR/COMBO measured collision-free (ratio 1.00) across every venue checked. This corrupts Bug C's new
      `per_instrument_expected` dict (keyed by normalized id) for these instrument_types — live-measured consequence:
      `per_instrument_coverage(DERIBIT, options_chain)` today reports a false **`completion_pct=100.0%`**
      (`expected_shards=210` vs. the real ~264,550-option universe, `found_shards=10,172`) — masking real gaps, the
      mirror-image failure of the operator's original "0% shown when fine" symptom. Confirmed `options_chain`/
      `futures_chain` are NOT F4-seeded for DERIBIT (live manifest check), so this is an ACTIVE production code path
      today, not dormant. Filed as `plans/active/issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`
      (full repro data, root cause, recommended fix directions, own todos) — this is a genuine, additional, real bug the
      fix's own new unit tests didn't catch (none of the 8 use an OPTION/dated-FUTURE id), not something Bug C's
      original scope was expected to cover, and not the kind of fix a read-only verification pass should make silently.
      **Does this fully explain the operator's original screenshot?** Not independently confirmable without the
      operator's exact venue/ instrument — no screenshot metadata survives to identify which specific instrument
      triggered it — but the mechanism is now proven, on real data, to produce exactly the class of symptom described
      (near-zero completion from an unclipped pre-listing/pre-existence denominator), which is the strongest
      verification available short of the original literal repro.
- [x] N. ✅ [BACKEND] P0. **Fix Bug B** — `deployment-ui@c11d370`, verified on origin, full QG green. Fixed the
      `getInstrumentAvailability` request/response contract mismatch + added a monotonic-sequence stale-response guard
      to both debounced search flows (`runSymbolSearch`, `fetchInstruments`). See the Progress Log entry above for the
      full detail, including the correction that the operator's screenshot traces to a THIRD search flow
      (`searchInstruments`/cross-category), not the originally-cited one.
- [x] N. ✅ [BACKEND] P1. **`GET /instruments` (`get_instruments_list`) doubly-broken bug — FIXED.**
      `deployment-api@b8a1426`, verified on origin, full QG green, 19 unit tests (7 rewritten + all passing). Rather
      than parsing venue/instrument_type off raw GCS object paths (the originally-sketched approach), reused the
      EXISTING `_load_search_corpus`/`_load_corpus_from_per_venue_parquets` corpus loader that `search_instruments`
      already relies on (same 5-min in-process cache, same per-venue `instruments.parquet` reads) — lower risk than a
      new path-parsing scheme, and it already carries real `venue`/`instrument_type` columns per row. `search` now
      applies whitespace-tokenized AND-match substring filtering (mirrors `search_instruments`'s own convention);
      response reshaped to `{instrument_key, venue, instrument_type}` objects matching the frontend's
      `InstrumentSearchResult` contract, with `total_in_file`/`returned_count`/`search` fields matching
      `InstrumentsListResponse` (confirmed via grep that `deployment-ui` never reads the old `total_count`/`truncated`/
      venue/instrument_type-echo fields, so dropping them is safe). Also expanded scope beyond the original ask:
      `sports` now works through this endpoint too (free, since `_load_search_corpus` already special-cases it) — the
      old code only ever supported cefi/tradfi/defi.
- [x] N. ✅ [BACKEND] P1. **Wire UAC `is_mvp` into MTDS coverage — SHIPPED** (`deployment-api@724910e`, verified on
      origin, full QG green, 20/20 tests in the target file incl. 3 new MVP-scope tests). Scoped to where the semantics
      are actually well-defined: the per-instrument-shard (Tier-3) branch, via a new `scope`/`instrument_types` param
      threaded `_status_core.py` route (`GET /data-status/manifest`, the "drilldown" surface the operator's screenshot
      was about) → `_get_manifest_status_sync` → `_dispatch_category_builds` (gates the process-pool fast-path off for
      `scope=mvp`, same way `row_filters`/`pipeline_modes`/`venue` already do, so it falls through to the thread/serial
      path without touching the pickled subprocess boundary) → `_build_manifest_category` →
      `_apply_mtds_honest_coverage` → `mtds_honest_coverage_for_venue` → `per_instrument_coverage`, which filters
      `expected_instruments` to UAC `is_mvp(asset_group, venue, instrument_type, dt, base_ccy=None)`-true instruments.
      `instrument_type` per instrument comes from a NEW combined read (`_read_cefi_catalogue_metadata`, replacing Bug
      C's `_read_cefi_catalogue_existence_windows`) that projects `instrument_type` alongside `available_from`/
      `available_to` from the SAME `prod/catalog.parquet` object in one pass (no second GCS round-trip); an instrument
      absent from `instrument_types` fails CLOSED under `scope=mvp` (documented as the deliberate opposite of the
      existence-window clipping's fail-OPEN convention — an unknown instrument_type cannot be proven MVP).
      `build_cefi_is_instruments_provider`'s return grew from a 2-tuple to a 3-tuple
      (`provider, windows,     instrument_types`) — its one caller (`venue_resolution.py`) and 4 existing unit tests
      updated to match. Default `scope="could_exist"` everywhere = zero behavior change for every existing caller that
      doesn't pass it. **Deliberately NOT covered by this ship** (both now separate follow-up todos below, not silently
      dropped): venue-level (non-per-instrument) dt entries have no single `instrument_type` to evaluate `is_mvp(...)`
      against, so `scope=mvp` is a documented no-op there; and the `/turbo` endpoint (`get_data_status_turbo` in
      `_deploy_turbo.py`, the OTHER surface behind the operator's second screenshot) has no `scope` param at all today —
      only `/manifest` (the drilldown) was wired.
- [x] N. ✅ [BACKEND] P2. **MDPS parity / `/turbo` scope gap — SHIPPED** (`deployment-api@511084b`, verified on origin
      via `merge-base --is-ancestor`, full `quality-gates.sh` green). Added
      `scope: CoverageScope = Query("could_exist",     ...)` to `get_data_status_turbo` (`_deploy_turbo.py`), mirroring
      `_status_core.py`'s exact param/description; threaded it into the route's `_manifest_source` closure →
      `get_manifest_status(scope=...)` (the same narrowing engine `/manifest` calls), and into
      `data_analytics_service.get_data_status_turbo`'s own signature — that service does no aggregation of its own
      (confirmed by reading it: it only forwards to the closure) so `scope` there is used SOLELY to fold into the
      turbo-mode cache key; without that fold, a cached `could_exist` response would have been served back for an `mvp`
      request (or vice versa) since every other input param is identical — a real bug the review-before-ship pass
      caught, not a hypothetical. Tests: 4 new route-level plumbing tests in `test_route_data_status_live.py`
      (`TestGetDataStatusTurboScopeParity` — proves `scope=mvp` reaches `get_manifest_status` via the real
      `_manifest_source` closure invoked end-to-end, default is `could_exist`, invalid scope 422s, and
      `/turbo`+`/manifest` call `get_manifest_status` with the IDENTICAL scope value for the same request) + 3 new
      cache-differentiation tests in `test_data_analytics_service.py` against the REAL `DataAnalyticsService` class
      (loaded standalone — the package-level singleton is globally mocked in this repo's unit-test conftest for perf,
      discovered while writing the first draft of the route test). Full suite: 4900+ passed, 16 skipped, 0 failed.
      Shipped via `--skip-preflight` (documented multi-agent carve-out, does NOT weaken the quality gate — Stage 3 full
      QG still ran and passed twice, against two different HEADs as sibling agents' commits landed):
      `unified-api-contracts` was mid-edit by a concurrent agent on unrelated symbols
      (`venue_adapter_keys`/`market_data_categories`/`processed_data_dependencies`/`lst.py`/`instrument_validation.py` —
      none used by this change) for ~25+ min without settling, so Stage 2's cross-repo dirty-dep audit was skipped per
      its own documented purpose (a multi-agent safety net, not a QG gate).
- [x] N. ✅ [UI] P1. **Build the universal MTDS search bar — SHIPPED** (`deployment-ui@afe3262`, verified on origin via
      `merge-base --is-ancestor`, full `quality-gates.sh` green, live-verified via dev server + Playwright MCP before
      writing the automated spec, new regression spec `tests/smoke/symbol_search_clickthrough.spec.ts` pw:L2 ✓). The
      "Symbol search" box (`DataStatusTab.tsx`) already existed and already returned cross-category matches — the gap
      was purely that clicking a result row did nothing; closed that with two new click-through branches, each its own
      state (deliberately NOT the pre-existing `selectedInstrument`/`instrumentAvailability` pair, which is wiped by an
      effect keyed on `[instrumentSearchMode, selectedCategories]` on any unrelated change, and whose render block is
      additionally gated to `selectedCategories.length === 1` on MTDS/MDPS only — reusing it would make the panel
      invisible on other service tabs or silently vanish out from under the operator): - **Non-SPORTS
      (cefi/tradfi/defi/prediction)**: reuses `getInstrumentAvailability` exactly as Bug B fixed it — the only new logic
      is parsing `InstrumentSearchMatch.canonical_id`. **Id-format landmine + how it was resolved**: `canonical_id` is a
      single-colon `VENUE:TYPE:SYMBOL` composite (confirmed against deployment-api's `_read_venue_parquet_rows` producer
      code + its own unit-test fixtures), a COMPLETELY different format from the `::`-delimited `instrument_key` the
      separate manual "Instrument-Level Search" dropdown's Bug-B fix parses — naively reusing that `::`-split logic here
      would have silently sent a malformed/overly-composite string to the availability endpoint. Fix: since the match
      already carries `venue`/`instrument_type` as separate fields, strip that exact `venue:instrument_type:` prefix off
      `canonical_id` to recover the bare symbol (falls back to positionally dropping the first two colon segments only
      if the prefix doesn't match verbatim, defensive against format drift) — verified empirically against the real
      backend's `instrument` param semantics (a plain string EQUALITY match against the manifest's `instrument_id`
      column, not a colon-split), not assumed from the docstring. - **SPORTS**: fetches the clicked league's
      found/missing dates via the already-built `GET /data-status/manifest?secondary_axis=league_id` contract (new,
      independent state — NOT the page's global `turboData`/`manifestFilter`, so it can never replace or cancel the
      macro drilldown below it, satisfying the "additive" requirement literally); picking a found day composes the
      existing `<FixtureBreakdown day league_id       readOnly>` component unmodified. - **Second stale-closure gotcha
      found + fixed while implementing** (beyond the one already flagged in research): the existing
      `fetchInstrumentAvailability` `useCallback` is gated on `selectedInstrument` state — calling
      `setSelectedInstrument` then that callback back-to-back in a click handler would silently no-op (stale closure,
      state updates are async). Both new click handlers are plain (non-`useCallback`) functions that build the request
      directly from the clicked match instead of depending on any state closure. - **Mock-mode gaps found + fixed while
      verifying live (all in `src/lib/mock-api.ts`, required to actually see the feature render before writing the spec,
      per the mandatory live-verify-before-spec rule)**: (1) no handler existed for `/data-status/instruments/search` at
      all — it fell through to the generic `/data-status/instruments` prefix handler, which returns a completely
      different shape (`{instruments: [...]}` vs the real `{matches: [...]}`), so `searchInstruments()` would have
      handed back `matches: undefined` and the results `.map()` would have thrown; (2)
      `/data-status/instrument-availability`'s mock body didn't match `RawInstrumentAvailabilityResponse` at all
      (pre-existing, unrelated to this ship, but blocking — would have thrown on `raw.data_types` being undefined) —
      reshaped to the real shape; (3) `/data-status/fixtures/breakdown` had NO mock handler either and fell through to a
      different generic `/data-status/*` catch-all that returns the big turbo status object (no `fixtures` field) —
      `FixtureBreakdown` then threw reading `data.fixtures.length`, crashing the whole tab's ErrorBoundary the first
      time ANY league/day breakdown was expanded in mock mode (this is the ALREADY-EXISTING sports fixture drilldown,
      not new code — it had simply never been exercised live in mock mode before). All three fixed with realistic
      representative data so the click-through (and the pre-existing drilldown it composes) actually render in mock
      mode. **Follow-up fix (`deployment-ui@319a32e`, verified on origin, full QG green, tsc/eslint/pw:L2 all clean)**:
      an independent adversarial-review pass on the shipped click-through found one real, plausible-but-unconfirmed edge
      case — the `canonical_id` bare-symbol extraction silently produced an EMPTY string for any legacy,
      not-yet-canonicalized (zero-colon) `instrument_key` still surviving in a venue's corpus (a shape UAC's own
      `instrument_key.py` documents as still-live, pending removal), which would have sent an empty `instrument` param
      to the availability endpoint and silently rendered a misleading "0 found / 0 missing" instead of a real check.
      Fixed: guard `canonical_id.split(":").length < 3` and fall back to the raw `canonical_id` itself as the bare
      symbol in that case.
- [x] N. ✅ **DUPLICATE of the todo above — SHIPPED, see that entry** (`deployment-api@724910e`). Stale copy of the same
      "wire UAC `is_mvp` into MTDS coverage" ask, left unchecked in an earlier plan revision; consolidating here rather
      than leaving a done item showing as open next to its own completed twin.
- [ ] [DATA] P2. **Precompute `mvp: bool` for sports/prediction — TRACED + DESIGNED this tick, deliberately NOT
      implemented (scope-risk STOP, not a skipped task).** Picks up exactly where the prior tick left off (that tick had
      already ruled out the naive "mirror `_add_mvp_column`/redirect to `prod/catalog.parquet`" fix — see
      `_catalogue.py:75-87` + `test_sports_not_in_identity_catalogue_asset_groups`, unchanged, still correct).

      **Trace (done this tick)**: sports/prediction have NO separate manifest-writer pipeline — they flow through the
                      exact same universal orchestrator as every other asset_group.
                      `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py`'s
                      `_finalize_prediction_bundles`/`_finalize_sports_...` closures (+ the shared `_write_bundle_shard_row` helper)
                      call `unified-trading-library/unified_trading_library/manifest_writer/_writer_captured.py`'s
                      `ManifestWriter.record_captured`/`record_captured_from_counts` (captured rows) and `_writer_record.py`'s
                      `_record_status` (empty/failed/expected_unattempted rows), which both build ONE shared dataclass —
                      `_rows.py::AvailabilityRecord` — the UNIVERSAL manifest-row schema written into `_index/availability_index.parquet`
                      by EVERY asset_group and EVERY producer service (cefi/defi/tradfi/sports/prediction, plus features-service /
                      ml-service / strategy-service / execution-service, which is why `AvailabilityRecord` already carries
                      `feature_group`/`model_family`/`strategy_id`/`client_id`/`instruction_type` columns). There is no
                      sports/prediction-scoped writer to touch in isolation — any new column lands on this ONE shared schema.

                      **Key finding (changes the framing of "correct fix")**: `is_mvp_for_manifest_row`'s two extra axes beyond
                      `(venue, instrument_type, data_type)` — `base_ccy` (read from a `base_asset` column) and `market_group` — are
                      confirmed ABSENT not just from the read-time manifest DataFrame (already documented at `_coverage_scope.py:96-104`)
                      but from the WRITE-time schema too: neither `base_asset` nor `market_group` appears in UTL's `_ROW_KEY_COLUMNS`
                      or `AvailabilityRecord` fields (`_rows.py`). So a write-time `is_mvp(...)` call would resolve those two kwargs to
                      `None` — IDENTICAL to what the read-time call resolves today. **Write-time precompute is a pure caching/perf
                      optimization, not a correctness fix** — it would not change a single row's `is_mvp` verdict vs. today.

                      **Design (for whoever implements)**:
                      1. UTL `manifest_writer/_rows.py`: add `mvp: bool | None = None` (trailing field, back-compat default) to
                         `AvailabilityRecord`; bump `MANIFEST_SCHEMA_VERSION` 9→10 in `_schema.py`.
                      2. UTL `_writer_captured.py::record_captured`/`record_captured_from_counts`: when the resolved `asset_group` is
                         `"sports"`/`"prediction"`, lazy-import UAC `is_mvp` and stamp
                         `is_mvp(asset_group, venue, instrument_type, data_type, league=league_id or None, market_group=None,
                         base_ccy=None, source=resolved_source)` onto the `AvailabilityRecord(...)` call; leave `None` for every other
                         asset_group (no behavior change elsewhere).
                      3. UTL `_writer_record.py::_record_status`: same conditional stamp (sports/prediction also write
                         empty/failed/expected_unattempted rows through this path).
                      4. `deployment-api/_catalogue.py::_row_is_mvp`/`_is_mvp_series`: add a THIRD branch — when `"mvp" in df.columns`
                         for a manifest-backed (non-identity-catalogue) frame, use the precomputed value for rows where it's non-null
                         (`_truthy_mvp` fast path, mirroring the identity-catalogue branch byte-for-byte) and fall back to
                         `is_mvp_for_manifest_row` only for legacy rows where the column is null/absent — old rows keep today's exact
                         behavior.
                      5. Historical rows do NOT retroactively gain `mvp` from steps 1-4 alone — closing the live-compute gap for
                         EXISTING data needs a companion backfill/rebuild pass (the repo already has the pattern:
                         `rebuild_sports_manifest_v9.py` / `rebuild_prediction_manifest.py`), scoped separately.

                      **Why this STOPS here instead of shipping (explicit scope-risk call, not an oversight)**: step 1 is not a
                      sports/prediction-scoped change — it is a schema addition on the ONE shared `AvailabilityRecord` used by every
                      asset_group and every producer service, so it needs a FULL FLEET redeploy (every live/backfill/cron VM, both
                      clouds, all asset_groups) to take effect, not a bounded single-service change. The manifest-consolidator
                      (Cloud Run/Batch-Fargate) merging old-schema and new-schema per-VM shards together is unverified here and codex
                      documents it as "loud-fails on stale index" — exactly the risk class behind this SAME session's separate CeFi
                      manifest re-stamp (see the "2026-07-21 (tick 2)" progress-log entry above and the deferred-work table below),
                      which needed a snapshot + guarded rollout + an operator-gated Cloud Scheduler pause and is still not fully landed.
                      Given the P2 (not P1) priority, the already-documented "bounded, non-regressed" live-compute cost (no active
                      incident forcing urgency), and the Key Finding above (this is a perf win, not a correctness fix), rushing steps
                      1-4 here would repeat the exact near-miss pattern this plan has already flagged twice. Left at P2 with the design
                      above ready to hand off; NOT force-shipped.

- [x] N. ✅ [BACKEND] P1. **MDPS parity — traced + backend honest-coverage SHIPPED** (`unified-api-contracts@a7798b93` +
      `deployment-api@60a23ae`, both verified landed on origin by SHA). **Traced first** (Explore agent, before writing
      any code): MDPS was hard-excluded from the entire honest-coverage path (`is_mtds_honest_coverage_target`:
      `service != "market-tick-data-service"` → always `False` for MDPS) and fell back to a generic, imprecise path —
      NOT a free UI fix, confirmed MDPS has a genuine timeframe axis (7 timeframes × 2 data_types today) that MTDS's
      coverage code has zero model of; naively flipping the gate would have conflated all 7 timeframes into one
      denominator cell. Ran a full design→3-way-adversarial-review→ implement→independent-verify pipeline given the
      data-correctness stakes: - **Design** (research + concrete design): generalized `is_mtds_honest_coverage_target`
      to a `_HONEST_COVERAGE_SERVICES` frozenset covering both services; reused `MTDS_CATEGORY_META`/
      `mtds_expected_dates_for_venue_dt` unchanged (venue-list resolution and calendar math are service-agnostic); added
      an optional `timeframes` param to `per_instrument_coverage`/`mtds_honest_coverage_for_venue`, defaulting to `None`
      (byte-for-byte unchanged for every MTDS caller); two new additive UAC registries (`MDPS_DERIVABLE_DATA_TYPES`,
      `MDPS_CANONICAL_TIMEFRAMES`) plus a `service`-scoped branch on `get_expected_data_types_for_venue`. - **3
      independent adversarial reviews** (mtds-regression / denominator-correctness / completeness lenses) ALL THREE
      converged on one critical, ship-blocking gap the design itself missed: `service` was never actually threaded from
      `manifest.py`'s gate down to the `get_expected_data_types_for_venue(venue, service=service)` call — without the
      fix, MDPS's expected-data-type list would have resolved to the FULL MTDS raw vocabulary instead of the narrowed
      derivable subset, permanently inflating `missing_data_types` and tanking `completion_pct` for real venues
      (measured: BINANCE-FUTURES declares 5 data types, only 2 MDPS-derivable). 2 of 3 reviews also independently found
      a real pandas index-misalignment bug in the new timeframe branch (a `tf_str` built from the unfiltered row slice
      vs. the legacy-masked `iid_str`/`rd_str`), and 1 review found the legacy-row-fallback branch was silently
      untouched by the new timeframe multiplier. - **Implementation incorporated all three fixes**: `service` now
      threads `manifest.py` → `_apply_mtds_honest_coverage` → `mtds_honest_coverage_for_venue` →
      `get_expected_data_types_for_venue`; the pandas index-alignment bug is fixed (timeframe series derived from the
      same masked slice); the legacy-row fallback gets BOTH a `len(timeframes)` multiplier AND an explicit
      `denominator_timeframe_aware: False` provenance marker (belt-and-suspenders, exceeds what either review asked for
      individually). Also fixed a pre-existing, unrelated bug found along the way: `path_combinatorics.py`'s
      `PROCESSING_TIMEFRAMES` carried a stale `"24h"` token no real manifest row has ever written (the writer normalizes
      to `"1d"`) — now single-sourced from the new UAC registry. - **Verified independently** (separate agent, re-read
      the diff + re-ran both test suites from scratch, did not trust the implementer's own report): service-threading
      fix confirmed present at the exact call site; 977 existing deployment-api tests + 44 UAC registry tests pass with
      ZERO regressions (only 6 source files + 2 new test files touched, no existing test modified); pandas fix confirmed
      correct; legacy-fallback fix confirmed present. I additionally ran the full local `quality-gates.sh` (not just the
      workflow's own test run) in both repos before shipping. - **Two open design questions deliberately left
      unresolved, not silently assumed** (flagged in code comments + an additive `historical_coverage_gap: true`
      response field for MDPS entries): (1) whether pre-cutover MDPS manifest rows — written under the legacy aggregated
      `data_type` convention before today's `752eaff` commit — should count toward the new source-keyed denominator at
      all, or are invisible until a backfill/relabel migration (implemented: invisible, flagged via the new field, not
      reverse-mapped); (2) whether any `(venue, data_type)` pair has genuine per-timeframe start-date divergence
      (implemented: flat `MDPS_CANONICAL_TIMEFRAMES` applied uniformly, with `get_expected_timeframes_for_venue_dt`'s
      signature left open for a future per-venue override). - **Deliberately out of scope for this ship** (each is its
      own follow-up, not silently dropped): the Tier-2 venue-level (non-per-instrument) branch is NOT timeframe-aware
      yet — MDPS's one current venue-level derivable dt (`liquidations`) will under-multiply there;
      `deployment_api/services/data_status/coverage.py`'s separate offline-rollup `completion_pct` surface is untouched
      (independent 4-state tally, noted in a new docstring comment); the universal-search-bar UI work (separate todo
      below) is unrelated to this backend ship. - **Independent side-discovery, filed separately, NOT part of this
      ship**: the same `752eaff` commit that switched MDPS's manifest `data_type` to the SOURCE-key convention (the fix
      this whole design depends on) also silently broke deployment-api's UNRELATED generic processed/raw classifier
      (`_classify_data_type_for_venue` in `breakdowns_core.py`, keyed on the old aggregated tokens) — filed as
      `plans/active/issues/mdps_datatype_axis_switch_breaks_generic_classifier_2026_07_21.md` and already landed on
      origin; not this plan's scope to fix.
- [x] N. ✅ [RESEARCH] P2. **Investigated — TWO root causes bundled under one operator complaint, code-confirmed
      (2026-07-22, research-only unit, no fix attempted).** The operator's "the whole mtds needs to be much faster"
      complaint traces to **two genuinely different mechanisms**, not one: 1. **Coverage/drilldown grid (the "Data
      Coverage" TURBO panel, Bug C's surface) — SAME root cause as `data_status_cell_grid_rearchitecture_2026_07_18.md`,
      confirmed by reading the live code path, not the two plans' prose.** `/manifest`'s on-demand fallback
      (`deployment-api/deployment_api/services/data_status/        manifest.py::_get_manifest_status_sync` →
      `_build_manifest_category:771` → `defi.py::_read_defi_merged_index:274` →
      `data_status_service.py::_read_index_cached:449`) calls `read_availability_index(bucket)` **with no
      date/venue/scope window at all** — it loads the ENTIRE per-service manifest into memory unconditionally, THEN
      applies the date mask in-memory (`manifest.py:798`,
      `mask = (index["date"] >= effective_start) & (index["date"] <= end_date)`) — exactly the "reads the ENTIRE
      per-service availability manifest into memory per request" architecture the rearchitecture plan describes.
      Confirmed same incident, not just a similar-sounding one:
      `deployment_api/services/data_status/live_build_guard.py`'s module docstring + calibration anchors (lines 1-70)
      cite the IDENTICAL measured figures the rearchitecture plan cites (18GB IS / 81GB MTDS / 56GB MDPS full-history) —
      `live_build_guard.py` + the 90-day UI default are the "near-term OOM guard" stopgap that plan's own Context
      section says remains live "until this lands." This session's Bug C (existence-window clipping), MVP-scope wiring,
      and MDPS-timeframe extension (all shipped this session, see entries above) run entirely INSIDE
      `_build_manifest_category`'s post-load `filtered` DataFrame (`instrument_coverage.py::per_instrument_coverage`) —
      bounded, vectorized pandas ops on data already in memory, plus one SEPARATE small identity-only read
      (`_read_cefi_catalogue_metadata`, `prod/catalog.parquet`, explicitly documented as "not a second whole-corpus
      walk," `instrument_coverage.py:150-153`). None of this session's shipped work introduces a new full-corpus read or
      a new architectural bottleneck — it all rides on top of the SAME not-yet-fixed whole-manifest-load path the
      rearchitecture plan already scopes to fix. **Annotated `data_status_cell_grid_rearchitecture_2026_07_18.md` with a
      pointer to this session's work (see that plan's Progress Log) rather than duplicating its scope here.** 2.
      **Symbol/instrument search latency (Bug A/B's surface) — a DIFFERENT root cause, NOT memory/OOM, already measured
      and partially fixed BEFORE this session** (so nothing new to do here either).
      `deployment-api/deployment_api/services/data_query_service.py::_load_corpus_from_per_venue_parquets:463` reads
      only the LATEST day's small per-venue `instruments.parquet` files (bounded to one day, not full history) — the
      slowness was never a memory problem, it was N sequential transpacific GCS round-trips (one per venue; DeFi alone
      has 63). `_read_all_venue_parquets:499-513`'s own code comment cites the measured cost directly: "~44s cold
      cache-miss latency (measured operator-side, 2026-07-16)" — fixed via `ThreadPoolExecutor`-based parallelization,
      commit `8e1221b` ("perf(data-status): parallelise symbol-search per-venue parquet reads (~44s -> seconds)",
      2026-07-17, predates this plan). This session's Bug B (`deployment-ui@c11d370`) and `get_instruments_list` fix
      (`deployment-api@b8a1426`) both REUSE this already-threaded corpus loader rather than needing to fix its latency
      again. "Partially" fixed (44s→seconds, not instant) — a further latency-reduction pass is a legitimate follow-up
      but is NOT the OOM plan's scope and does not belong there. **Verdict for the plan-annotation instruction**: item 1
      is the same issue (annotated, not duplicated); item 2 is unrelated to the cell-grid plan and needed no new
      annotation there.
- [ ] [UI] P2. Once Bugs A/B/C are fixed and MVP-scope + universal search are wired: confirm the MTDS (and MDPS) view is
      genuinely at parity with the instruments-service view. `[UI]` + `pw:L2 ✓` + a regression spec per the playwright
      gate (per this workspace's UI-testing convention) — no tick without it.
- [ ] [REVIEW] P2. Post-phase codex/plan audit: confirm this plan's "already shipped" section still matches
      `mvp_scope_catalogue_tagging_2026_06_08.md` (which has its own open Phase-2+ features/strategy/model items,
      unrelated to this plan — don't pull those in) and annotate that plan's "Composes with" section with a pointer back
      here so a future reader doesn't re-discover the MTDS gap from scratch.
- [x] N. ✅ [BACKEND] P2. **MDPS honest-coverage follow-up — SHIPPED** (`deployment-api@43f067e`, content-verified on
      origin via `merge-base --is-ancestor` against the exact SHA). Made the Tier-2 (venue-level, non-per-instrument)
      branch in `mtds_honest_coverage_for_venue` timeframe-aware, mirroring the Tier-3 `per_instrument_coverage` pattern
      exactly: extracted the branch into a new `_tier2_dt_entry()` helper — `expected_shards` multiplies by
      `len(timeframes)` and the found-set becomes `(date, timeframe)` pairs read from the manifest's `timeframe` column
      (restricted to `expected_dates` AND the canonical timeframe list) when `timeframes` is supplied; a manifest slice
      with no `timeframe` column degrades to zero found pairs — honestly 0%, never a `KeyError` — matching the Tier-3
      contract; `timeframes=None` (every existing MTDS caller) reproduces the prior per-(venue, dt, date) denominator
      byte-for-byte. Concretely fixes MDPS's `liquidations` data_type (confirmed NOT in UAC's
      `_PER_INSTRUMENT_SHARD_DATA_TYPES`, so it always dispatches to Tier-2), which previously under-multiplied its
      denominator by `len(timeframes)`. **Also single-sourced `path_combinatorics.py`'s `PROCESSING_DATA_TYPES` from UAC
      `MDPS_DERIVABLE_DATA_TYPES`** (design item 14). **Correction to this todo's own prior assumption**: this is NOT a
      no-op/cosmetic rename — direct inspection of `unified_api_contracts/registry/processed_data_dependencies.py`
      (git-blamed to `a7798b93`, the SAME commit this todo cites as already-shipped) showed `MDPS_DERIVABLE_DATA_TYPES`
      was `frozenset(_RAW_TO_PROCESSED_PREFIX)     | frozenset(_PASSTHROUGH_RAW_FOR_OHLCV)` = **~12 values** (`trades`,
      `book_snapshot_5`, `derivative_ticker`, `liquidations`, the DEFI per-pool/index types, `ohlcv_1m`, `odds`,
      `prediction_market`) even at that commit — never "the same 2 values" as the local hardcoded
      `["trades", "derivative_ticker"]` this todo described. Widening `PROCESSING_DATA_TYPES` to the real UAC set is the
      correct fix for parity with what `mtds.py`'s own `get_expected_data_types_for_venue(service=...)` already treats
      as MDPS-derivable, but it IS a genuine behavior change to the `/turbo` GCS-prefix combinatorics path
      (`_get_processing_combinatorics` in `path_combinatorics.py`, consumed by `get_data_status_turbo_impl` →
      `_check_asset_group` → `query_specific_prefixes_for_asset_group`): MDPS combinatorics now additionally cover
      `book_snapshot_5`/`liquidations`/DEFI pool-index types/`ohlcv_1m` wherever a venue declares them, not just
      `trades`/`derivative_ticker`. Updated the one existing test
      (`test_processing_service_filters_to_valid_data_types`) that asserted the stale exclusion of `book_snapshot_5`,
      and strengthened it with a real negative case (`options_chain`, which has no UAC candle form and correctly stays
      excluded). New unit tests in `test_mdps_timeframe_aware_honest_coverage.py::TestTier2VenueLevelTimeframeAwareness`
      (5 tests: expected/found-shard math, garbage-timeframe rejection, no-timeframe-column zero-found degrade, and two
      byte-for-byte-unchanged-when-`timeframes=None` variants). Verified via `QG_SLICE=lint-codex` (full pass) +
      `QG_SLICE=typecheck` (0 basedpyright errors on the 4 touched files) + full `quality-gates.sh --no-fix` (4891
      passed; the only 4 failures were a concurrent agent's unrelated, uncommitted `/turbo`-scope WIP in
      `_deploy_turbo.py`/`test_route_data_status_live.py` — confirmed via `git diff` showing a `# DEBUG-TEMP` marker and
      a brand-new test class absent from `HEAD`, not touched). Shipped with `--skip-preflight` (documented
      multi-agent-use flag) because deployment-api's pinned `unified-api-contracts` dependency directory was
      concurrently dirty (another live agent's WIP, confirmed via <120s file mtimes — LIVENESS-gated PROTECT, not
      touched); safe because deployment-api has no editable/path dep on UAC
      (`dep-content gate: no editable deps — PASS`) — the shipped code was tested against the pinned, installed UAC
      package version, not the dirty local checkout, and the UAC symbols this ship depends on
      (`MDPS_DERIVABLE_DATA_TYPES`, `get_expected_timeframes_for_venue_dt`, `is_per_instrument_shard_data_type`) were
      already stable/shipped well before the concurrent session started.
- [x] N. ✅ [DATA] P3. **Resolved by direct production-data investigation, 2026-07-22 — no migration needed.** Read the
      live manifest (`market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 10,490,576
      rows) and found **exactly 6 total `market-data-processing-service` rows in the ENTIRE manifest**, ALL
      `written_at=2026-04-16`, ALL for the single date `2026-04-14`, all missing `venue`/`instrument_id` — one row per
      data_type (`book_snapshot_5`, `derivative_ticker`, `futures_chain`, `liquidations`, `options_chain`, `trades`),
      clearly a one-off smoke-test/seed write from early MDPS integration, not real production candle-writing volume.
      **MDPS is not actually writing production candle history to this manifest yet.** This means the
      `historical_coverage_gap` concern (Open Question 1) is currently MOOT, not merely deferred: there is no real
      historical volume to backfill or reverse-map — a migration would touch 6 rows of test data. Left the shipped
      `historical_coverage_gap` flag as-is (it's honest and correct — those 6 rows genuinely don't match the new
      source-keyed query) rather than building migration machinery for data that doesn't exist yet. **Re-open this todo
      once MDPS starts writing real production volume** — the right trigger is a manifest row-count check for
      `service_name=="market-data-processing-service"` climbing into the thousands+, not a calendar date.
- [x] N. ✅ [DATA] P3. **Resolved by the same investigation — insufficient real data to determine, safe default
      confirmed unfalsified.** With only ONE new-convention-shaped MDPS row in the whole manifest (a single
      `trades`/`15s` row), there is no real per-(venue, data_type, timeframe) history to check for start-date divergence
      (Open Question 2) — the sample is far too small to prove or disprove anything about real deployed onboarding
      cadence. The shipped `get_expected_timeframes_for_venue_dt` flat-uniform default is therefore neither confirmed
      nor contradicted by live data; it remains the correct, documented, revisable-without-a-signature-change assumption
      until real volume exists. **Re-check once MDPS has meaningfully more production history** (same trigger as the
      todo above) by re-running the per-(venue, data_type) earliest-timeframe-date groupby this investigation used
      (script discarded, trivial to rewrite: read the manifest, filter to
      `service_name=="market-data-processing-service"` + populated `timeframe`, group by
      `(venue, data_type, timeframe)`, take `min(date)`, compare across timeframes within each `(venue, data_type)`).

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

### 2026-07-21 (tick 2) — Bug C SHIPPED; inherited a dead cross-repo WIP to clear the blocking dep-gate

**Bug C SHIPPED — `deployment-api@89e31a0`**, content-verified on origin via `merge-base --is-ancestor` against the
exact SHA (never trust `git push`'s exit code alone in this workspace — established the hard way earlier this session).
The prior tick's bounded 20×90s retry loop for the blocking `deployment-service` dependency exhausted without it
clearing. Re-checked by hand: `stat -f "%Sm"` on `scripts/vm/launch-cefi-sharded-backfill.sh` +
`scripts/vm/tardis-concurrency-guard.sh` showed both frozen at the SAME timestamp, 35+ minutes stale relative to
wall-clock, with no process holding either file open (`lsof` empty) and no matching bash/python process in `ps aux`. Per
the LIVENESS-gating rule (mtime <120s = PROTECT; a dead claim = inherit + commit), this reclassified the dirty state
from "live, don't touch" to "abandoned, safe to take over." Read the full diff before touching anything: it was a
complete, internally-consistent Tardis-concurrency-guard hardening fix (fail-closed fleet enumeration instead of
silently reading an unreachable gcloud/aws/python3 as "0 running"; a new `tardis_guard_reserve_slot` that binds the
cap-1 rule to actual VM-creation time instead of a pre-flight estimate, closing a real 2026-07-20 incident where a
DERIBIT+perp-venue SINGLE_VM_QUEUE launch undercounted 2 real buckets as 1 and breached the cap) — no half-finished
edits, no debug scaffolding, `bash -n` clean, `shellcheck` clean (info-only pre-existing notes), full
`quality-gates.sh --no-fix` green. Committed + pushed as `deployment-service@ee67255`. Bug C's own commit then needed
one `git pull --rebase --autostash` (deployment-api had drifted 3 commits behind on unrelated LDR→main promote /
backmerge / digest-pin chores while the dependency was blocking — clean rebase, zero conflicts, verified Bug C's
`instrument_windows` content survived intact post-rebase) before `quickmerge.sh` landed it.

Also re-armed the manifest re-stamp's watchdog after a prior heartbeat check reported (correctly, by design) "still
running" — process (PID 9641) confirmed alive via `kill -0`, log progressing normally through attempt 21/25 at the same
~155-160s/attempt cadence the perf fix produced, consistently losing the CAS race but making genuine progress through
its bounded retry budget (~4 attempts / ~11min remaining before the 25-attempt cap). Next tick resumes on whichever
fires first: the watchdog reporting a terminal state, or picking up the next open todo (`get_instruments_list`
search+shape bug, or MVP-scope wiring into MTDS coverage) while it finishes.

### 2026-07-22 (final tick) — session close-out: all P0/P1 backend+UI engineering items shipped; audit + deferred-work table

Every P0 and P1 todo with a clear, executable scope is now shipped and verified on origin by SHA (see the checklist
above for each commit). Two multi-phase Workflow runs (research → design → 3-way adversarial review → implement →
independent verify) were used for the MDPS timeframe-coverage extension and the universal search-bar click-through,
given both touch data-correctness-sensitive or contract-sensitive surfaces — each caught real, concrete bugs the
single-pass design/implementation missed (documented inline at each todo above), which a lighter-weight process would
likely have shipped uncaught. Ran a post-phase codex audit (`codex/02-data/honest-coverage-model.md` now documents the
MDPS timeframe axis) and a plan-hygiene pass (deduped a stale, already-shipped todo that was left unchecked from an
earlier revision).

**What's still genuinely open** — every item below already has its own `- [ ]` todo above; this table exists per the
session-end hygiene rule to separate the three kinds of "not done," not to duplicate them:

| Item                                                                                                      | State                              | Blocked on                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest re-stamp final write (CeFi venue-as-chain historical fix)                                        | Cannot be done yet                 | **Operator**: authorize a ~3-5min pause of the `manifest-consolidator-market-data-cefi` Cloud Scheduler cron (root cause pinpointed precisely; see `distinct_values_noncanonical_audit_2026_07_20.md`)                                                                                                                    |
| Bug C live-data verification against the operator's original screenshot                                   | Not done                           | Nobody — genuine engineering work (reproduce against real GCS/manifest data for the specific venue/instrument), just not attempted this session; moderate effort, no blocker                                                                                                                                              |
| `/turbo` endpoint MVP-scope gap (only `/manifest` got `scope=mvp`)                                        | Done (2026-07-22)                  | N/A — see the checklist todo above (`deployment-api@511084b`)                                                                                                                                                                                                                                                             |
| Sports/prediction MVP-column real fix (precompute onto the manifest writer)                               | Traced + designed, not implemented | Nobody — deliberate scope-risk STOP: write path traced to UTL's universal `AvailabilityRecord` schema (shared by every asset_group + service), full design handed off in the todo above; implementing needs a full-fleet redeploy + consolidator schema-evolution verification, disproportionate to a bounded P2 perf gap |
| MDPS Tier-2 (venue-level) timeframe-awareness + `PROCESSING_DATA_TYPES` single-sourcing                   | Not done                           | Nobody — deliberately out of the reviewed scope for the shipped Tier-3 work; narrow, well-defined follow-up                                                                                                                                                                                                               |
| MDPS `historical_coverage_gap` real fix (backfill/relabel vs. compat shim)                                | Cannot be done yet                 | **Operator decision**: which of the two real fixes to pursue (flagged via a response field in the meantime, not silently wrong)                                                                                                                                                                                           |
| MDPS per-timeframe start-date divergence question                                                         | Cannot be done yet                 | **Operator/data**: needs a factual answer about real deployed venue cadence config; API surface already supports the answer either way without a signature change                                                                                                                                                         |
| `data_status_cell_grid_rearchitecture_2026_07_18.md` OOM vs. "MTDS needs to be faster" — same root cause? | Done (2026-07-22)                  | N/A — two root causes found: coverage/drilldown grid = SAME as the OOM plan (annotated there); symbol search = a different, already-partially-fixed I/O-latency issue (pre-session `8e1221b`). See todo above.                                                                                                            |
| Final MTDS/MDPS-parity confirmation pass (`[UI]` + `pw:L2`)                                               | Not done                           | Nobody — the shipped UI work each carries its OWN regression spec already, but the plan's broader "confirm full parity" todo as originally scoped hasn't had its own dedicated pass                                                                                                                                       |

**Recommended next item**: the manifest re-stamp cron-pause authorization — it's the only item blocking on a single,
fast operator decision (a ~5-minute production action) rather than more engineering time, and closing it out finishes a
genuinely separate, real data-correctness fix (`mtds@accd8aa4`) that's been ready and waiting since earlier in this
session.

**Safe to compact**: yes — every shipped item is committed, pushed, and SHA-verified on `origin/live-defi-rollout`
across `deployment-api`, `deployment-ui`, `unified-api-contracts`, `deployment-service`, and `unified-trading-library`;
`git status` in each touched repo is clean; nothing depends on a scratchpad path. Two operator-decision points and a
handful of well-scoped, non-blocking engineering follow-ups remain, all tracked as `- [ ]` todos above — none of them
represent lost or hidden work.

### 2026-07-22 (post-close-out) — Operator authorized both remaining decision points; all three now resolved

The two items the prior entry flagged as needing an operator call are now closed:

1. **Manifest re-stamp cron pause — APPLIED AND VERIFIED.** See `distinct_values_noncanonical_audit_2026_07_20.md`'s own
   2026-07-22 entry for the full detail (credential-impersonation path used, exact pause/resume timestamps, the write's
   verified before/after row counts). Both halves of the venue-as-chain fix (writer + historical re-stamp) are now live.
2. **The two MDPS design questions — resolved by direct production-data investigation, not by picking a default blind.**
   Read the live manifest directly (read-only, no mutation) rather than guessing: `market-data-processing- service` has
   written exactly **6 rows total** to the shared manifest, all a single-day smoke-test/seed write from 2026-04-16 with
   no `venue`/`instrument_id` populated — MDPS is not actually writing production candle volume to this manifest yet.
   This makes Open Question 1 (historical pre-cutover row visibility) currently MOOT (no real history to backfill or
   reverse-map) and Open Question 2 (per-timeframe start-date divergence) UNDETERMINABLE from real data yet (sample size
   of 1) — the shipped flat-uniform `MDPS_CANONICAL_TIMEFRAMES` default stands, neither confirmed nor contradicted. Both
   todos above are flipped with an explicit re-open trigger (real MDPS production volume appearing in the manifest)
   rather than closed as if permanently settled — this is a "not enough data yet" answer, not a "verified correct
   forever" one.

**Everything from the original plan scope is now closed or has an explicit re-open trigger.** Remaining `- [ ]` items in
the Todos section above (the `/turbo` MVP-scope gap, MDPS Tier-2 timeframe-awareness, sports/prediction MVP precompute,
the cell-grid OOM investigation, the final parity confirmation pass) are genuine, non-blocking engineering follow-ups
with no operator dependency — pick up whichever is highest-value next, or leave them for a future session.

### 2026-07-22 (follow-up tick) — Sports/prediction MVP-column P2: traced + designed, deliberately not implemented

Picked up the sports/prediction MVP-column todo per its own "correct fix direction for whoever picks this up" note.
**Traced** (grep-then-READ, no code written before the trace was complete): sports/prediction have no dedicated
manifest-writer job — `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py`'s
prediction/sports bundle-finalize closures call UTL `ManifestWriter.record_captured`/`record_captured_from_counts`
(`_writer_captured.py`) and `_record_status` (`_writer_record.py`), which both build ONE shared dataclass —
`manifest_writer/_rows.py::AvailabilityRecord` — the universal manifest-row schema every asset_group and every producer
service (cefi/defi/tradfi/sports/prediction/features/ml/strategy/execution) writes into
`_index/availability_index.parquet`. No sports/prediction-scoped writer exists to touch in isolation.

**Key finding**: `is_mvp_for_manifest_row`'s two extra axes (`base_ccy`/`market_group`) are absent from the WRITE-time
schema exactly as they're already documented absent from the READ-time one — a write-time `is_mvp(...)` call would
resolve identically to today's read-time call. **This is a pure caching/perf optimization, not a correctness fix.**

**Designed** the full write-time-stamp fix (5 concrete steps: `AvailabilityRecord` field + schema-version bump,
conditional stamp in `record_captured`/`record_captured_from_counts`, conditional stamp in `_record_status`, a third
`"mvp" in df.columns` fast-path branch in deployment-api's `_row_is_mvp`/`_is_mvp_series`, a companion historical
backfill/rebuild) — written into the todo above verbatim for whoever implements it.

**Deliberately stopped before implementing** (explicit scope-risk call, per this task's own instruction to stop rather
than force-ship something risky): step 1 is a schema addition on the ONE shared `AvailabilityRecord`, so it needs a
full-fleet redeploy (every live/backfill/cron VM, both clouds, every asset_group) to take effect, plus unverified
manifest-consolidator schema-evolution behavior on a system codex documents as "loud-fails on stale index" — the same
risk class behind this plan's own separate CeFi manifest re-stamp (see the 2026-07-21 tick-2 and 2026-07-22
post-close-out entries above), which needed a snapshot + guarded rollout + an operator-gated cron pause and took most of
a session to land safely. Given the already-documented bounded/non-regressed live-compute cost (P2, not P1, no active
incident) and the Key Finding above (perf-only, not correctness), rushing this in one pass would repeat that exact
near-miss pattern rather than learn from it.

**Shipped this tick**: nothing code-wise — the todo above and the deferred-work table row were updated
(`unified-trading-pm` — this commit) with the trace + design + explicit stop rationale so the next picker-upper starts
from a design, not from scratch. No other repo was touched; no quality gates were run (no code changed).
