---
doc_type: plan
title:
  Rollup worker MVP/could-exist dual-scope parity — extend the existing scope=mvp|could_exist|all toggle to the
  deployment-api rollup layer, single-pass where the data shape allows it
summary:
  The scope=mvp|could_exist|all toggle already exists for on-demand data-status endpoints (mvp_scope_catalogue_tagging)
  but the rollup worker only ever computes could_exist — a live scope=mvp request against a fresh rollup is silently
  served could_exist data today. Extend dual-scope to the rollup, single-pass where mechanically free, without
  reintroducing the cefi/defi OOM class the container has already been fixed twice for.
status: active
nature: design
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api]
scope: [engineer, admin]
tags: [mvp, could-exist, honest-coverage, rollup, data-status, scope-filter, memory-safety]
related:
  [
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md,
    /plans/active/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md,
    /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md,
  ]
created: "2026-08-12"
last_updated: "2026-08-12"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
sequential: false
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md,
    deployment-api/deployment_api/routes/data_status/_coverage_scope.py,
    deployment-api/deployment_api/scripts/data_status_rollup_worker.py,
    deployment-api/deployment_api/services/data_status/rollup_cache.py,
    deployment-api/deployment_api/services/data_status/manifest.py,
    deployment-api/deployment_api/services/data_status/coverage.py,
    deployment-api/deployment_api/services/data_status/mtds.py,
    deployment-api/deployment_api/services/data_status/instrument_coverage.py,
  ]
source:
  [
    'operator 2026-08-12 (interactive session, slot 5): "in Honest Coverage can we have mvp and could exist results
    separation so duplicate everything with and without mvp which means the rollup script needs to be updated to handle
    that too? we have it already below for the drilldown" — followed by a scoping question on the MVP source of truth''s
    edit cost and whether a single-pass dual-accumulate design beats a literal 2x-build, per Explore-agent research (two
    rounds, see Progress Log).',
    "operator ruling 2026-08-12: full single-pass everywhere including the dispatch-mode restructure (not a 2x-build,
    not a mixed strategy deferring the restructure).",
  ]
---

# Rollup worker MVP/could-exist dual-scope parity

## Why this plan exists, not a new todo in `mvp_scope_catalogue_tagging_2026_06_08.md`

That plan (`locked_by: live-defi-rollout`, active) is the SSOT for the `scope=mvp|could_exist|all` toggle's design and
already shipped it end-to-end for the on-demand `venue-year-coverage` endpoint + UI toggle (`deployment-api@3390c98`,
`deployment-ui@2279e57`). It explicitly precedents extending the toggle to a NEW consumer as its **own** plan,
cross-linked rather than folded in — see its "Composes with" note on `mtds_data_status_page_parity_2026_07_21.md`. This
plan is that same pattern applied to the **rollup worker** (`data_status_rollup_worker.py` + `rollup_cache.py`), which
today has **zero** scope awareness — both worker calls omit `scope=` entirely, defaulting to `could_exist`, and
`_get_coverage_summary_sync` doesn't even have a `scope` parameter to pass. See both plans' "Composes with"/`related:`
for the bidirectional link (todo 0 below).

## The three-way cost split (verified by direct code reads, not guessed)

A literal "just call `scope=mvp` a second time" is not uniformly cheap. Three genuinely different engines, three
different verdicts:

1. **Tier-3 per-instrument path** (CEFI/MTDS honest-coverage categories, `instrument_coverage.py`) — near-free. The
   expensive part (`_compute_found_shards`, scanning captured data into a found-set) is already scope-independent;
   `_scoped_expected_instruments` only narrows the cheap `expected_instruments` list before the shared found-set is
   intersected against it. Running both scopes here means computing the expected-list twice against the SAME found-set —
   a localized change.
2. **The default venue-breakdown path** (most of the manifest-status engine, `manifest.py`) — `scope` today is a
   **build-dispatch-mode branch**, not a per-cell tag: `_pick_dispatch_mode`'s `multi_cat_no_filters` gate
   (`manifest.py:541-567`) requires `scope == "could_exist"` to use the fast process-pool/isolated-serial paths, so a
   naive `scope="mvp"` call today already falls back to a slower path. This is the genuinely invasive piece — it needs
   dispatch-mode selection restructured to stop branching on scope, plus `is_mvp` masking added to the default
   venue-breakdown loop.
3. **Coverage-summary engine** (`_get_coverage_summary_sync` → `_compute_capture_status_counts`, `coverage.py:530-569`)
   — mechanically the best fit (already one vectorized pandas pass, boolean-mask counting, no per-row Python loop) but
   has **zero** existing scope/MVP wiring — needs new code: an `is_mvp` boolean mask (reuse `filter_to_mvp`'s
   dedup-then-broadcast technique, not a naive per-row `.apply` — see the OOM history below for why that distinction is
   load-bearing) plus doubling the four `.sum()` calls and `_fold_cat_entry_into_totals`'s running totals.

## Memory-safety constraint (not optional — this container has OOM'd on this exact class of read twice)

`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` (open) reproduced a live `uts-shared-deployment-api` Cloud
Run OOM (16 GiB limit) on cefi's manifest reads, root-caused twice: once to an unbounded full-column fallback read (~8
GiB RSS, fixed in `unified-trading-library@609299ad`), and again to `_live_coverage_venue_year.py` materializing a full
`to_pandas()` DataFrame per date-window (cefi alone measured 9.94 GiB peak RSS unfiltered; defi extrapolates to ~80
GiB). The fix that actually held was switching to `iter_manifest_row_groups()` — a genuinely streamed,
row-group-at-a-time accumulation (`deployment-api@3d72470`), not a smaller window. **Any new dual-scope aggregation code
in this plan must follow the same streamed-accumulation shape, never a second full-DataFrame materialization "for the
MVP pass"** — that would reintroduce exactly the OOM class this container has already been fixed for twice.
`honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (open, a different honest-coverage compute path — a GCE VM
launcher, not this Cloud Run service) is further evidence this compute class is fleet-wide memory-constrained, not a
one-off.

## A latent correctness bug found during scoping, fixed here (not filed separately — same code, same change)

`manifest.py::get_manifest_status`'s rollup fast-path gate (`any_row_filter`, ~line 181-230) does not include `scope` in
its filter check. A live `GET /api/data-status/manifest?scope=mvp` request with no other filters takes the rollup fast
path today and is served **could_exist** rollup data silently — wrong regardless of whether the rollup ever gains an MVP
variant. Todo 1 fixes this as the first step (small, isolated, verifiable independent of everything else).

## Todos

- [x] [BACKEND] P0. Fix `manifest.py::get_manifest_status`'s fast-path gate to include `scope` in `any_row_filter` so a
      non-default `scope` bypasses the could_exist-only rollup fast path until todo 6 below makes that path scope-aware.
      Add a regression test asserting `scope=mvp` with no other filters does NOT return could_exist-tagged data (assert
      on a fixture where the two scopes provably differ). Done-when: new test fails on the pre-fix code, passes after;
      full `quality-gates.sh` green. — `deployment-api@af9025b784`. Extracted the gate into
      `_manifest_status_any_row_filter` (kept `get_manifest_status` under the 50-line method-size gate). Added
      `TestManifestStatusScopeFastPathGate` (3 tests: `scope=mvp` bypasses, `scope=all` bypasses, default `could_exist`
      still fast-paths) mirroring the existing `TestManifestStatusVenueFilter` pattern. `quality-gates.sh` full green.
- [x] [BACKEND] P1. Tier-3 per-instrument single-pass dual-accumulate — change `_scoped_expected_instruments` and its
      caller chain (`per_instrument_coverage` in `instrument_coverage.py`, the per-dt loop in `mtds.py`) to compute
      `expected_count`/`found_count` for BOTH `could_exist` and `mvp` in one pass against the same
      `_compute_found_shards` found-set, returning a `{could_exist: dt_entry, mvp: dt_entry}` pair instead of one
      `dt_entry`. Done-when: existing Tier-3 coverage tests pass unmodified for `could_exist`, new tests assert the
      `mvp` entry's expected_count is a subset consistent with `is_mvp` filtering, and a monotonicity test asserts
      `mvp_expected_count <= could_exist_expected_count` for every fixture case (mirrors the existing
      `mvp ≤ could_exist ≤ all` pattern from `test_route_venue_year_coverage_scope.py`). — `deployment-api@a79397b8ec`.
      Implemented as ADDITIVE functions (design decision, logged 2026-08-13 below): `per_instrument_coverage_dual_scope`
      (`instrument_coverage.py`, shares the found-set via a new `_build_tier3_entry` helper extracted verbatim from the
      existing single-scope function — zero behavior change to `per_instrument_coverage` itself) and
      `mtds_honest_coverage_for_venue_dual_scope` (`mtds.py`, via `_mtds_derived_entry_counts_dual_scope`).
      Tier-2/seeded dts (no per-instrument grain) share one computed entry across both scope keys via a defensive
      shallow-copy (never the same dict object — an aliasing bug caught + fixed before shipping). Regression tests:
      `test_per_instrument_cefi_is_provider.py::TestPerInstrumentCoverageDualScope` (could_exist-half parity, mvp
      monotonicity, found-set-computed-once via a `wraps=` spy) + `test_mtds_honest_coverage_dual_scope.py` (4 tests:
      parity, monotonicity, empty-dts, MDPS historical_coverage_gap). `quality-gates.sh` full green.
- [ ] [BACKEND] P1. Coverage-summary engine dual-scope — add an `is_mvp` boolean mask to
      `_compute_capture_status_counts` (`coverage.py`), built via `filter_to_mvp`'s dedup-then-broadcast technique
      (evaluate `is_mvp` once per distinct axis-combo, NOT a per-row `.apply` — the exact pattern `filter_to_mvp`'s own
      docstring says avoids an OOM on a 26M-row cefi manifest), and double the four `.sum()` calls (masked vs unmasked)
      plus `_fold_cat_entry_into_totals`'s running-totals dict to carry both scopes. Add `scope`-shaped output
      (`{could_exist: {...}, mvp: {...}}` per node) to `_get_coverage_summary_sync`'s return shape. Done-when: existing
      coverage-summary tests pass for the `could_exist` half of the output unmodified, new tests cover the `mvp` half +
      the mask-reuse (not a second full pass over the DataFrame — assert the source DataFrame is read/decoded once, e.g.
      via a call-count assertion on the row-group iterator), and a peak-RSS measurement against a cefi-scale fixture
      (mirroring `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`'s measurement methodology) shows no
      meaningful RSS increase over the current could_exist-only path.
- [ ] [BACKEND] P1. Dispatch-mode restructure — stop `_pick_dispatch_mode`'s `multi_cat_no_filters` gate
      (`manifest.py:541-567`) from branching on `scope == "could_exist"`; instead make the default venue-breakdown loop
      (`_build_venue_breakdown`/`_build_single_venue_entry` in `venue_resolution.py`/`breakdowns_core.py`, and Tier-2
      `_tier2_dt_entry`) carry an `is_mvp` per-cell tag the same shape as todo 2/3, so `scope="mvp"` gets the SAME fast
      dispatch path (process-pool/isolated-serial) as `could_exist` instead of falling back to a slower path. Done-when:
      a dispatch-mode unit test asserts `scope="mvp"` with no other filters selects the same dispatch mode as
      `scope="could_exist"` for an otherwise-identical request (currently they diverge); existing dispatch-mode tests
      for `could_exist`/`all` pass unmodified.
- [ ] [BACKEND] P1. Rollup worker dual-write — change `_build_one_service_rollup`/`_build_one_service_coverage`
      (`data_status_rollup_worker.py:243-274`) to consume the now-dual-scope-output builds from todos 2-4 in a SINGLE
      call each (not two separate `scope=` invocations — the single-pass output already carries both scopes), and write
      both scopes to the rollup blobs: extend the existing `full.json.gz`/`coverage.json.gz` schema with a top-level
      `{could_exist: {...}, mvp: {...}}` split (do not create separate blob files — keeps the existing
      `data_status_rollup_ml_service_full_blob_missing_2026_07_26.md` gap from getting a second variant to go missing
      independently). Done-when: a real rollup run against a test service writes both scopes' data into one blob,
      verified via a round-trip read; existing single-scope consumers of the old schema shape get a compat check (read
      `.get("could_exist", root)` fallback during the transition, tracked in todo 7).
- [ ] [BACKEND] P1. `rollup_cache.py` scope-aware reads — add a `scope: CoverageScope = "could_exist"` parameter to
      `read_coverage_rollup_if_fresh`/`_allow_stale`/`slice_rollup_to_window`/`slice_asset_group`/`slice_venue`/
      `filter_coverage_to_asset_groups`, defaulting to `could_exist` (backward-compatible for every existing caller) and
      selecting the matching sub-object from todo 5's dual-scope blob shape. Done-when: existing rollup-cache tests pass
      unmodified with the default, new tests cover `scope="mvp"` returning the MVP sub-object, and `manifest.py`'s
      rollup fast path (todo 1's fix) actually threads its `scope` param through to these readers instead of dropping
      it.
- [ ] [BACKEND] P2. Transition compat cleanup — once todo 6 ships and a fresh rollup run has produced the new dual-scope
      blob shape for every `_DEFAULT_SERVICES` entry (verify via a live GCS read, not an assumption), remove the
      `.get("could_exist", root)` fallback added in todo 5 and require the new shape unconditionally. Done-when:
      fallback code deleted, full test suite green, live GCS check cites the object generation/timestamp proving every
      service's blob was rewritten after todo 5 landed.
- [ ] [REVIEW] P2. End-to-end live verification — once todos 1-6 are deployed, re-run the 3-scope probe pattern from
      `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` (`could_exist`/`mvp`/`all`, `asset_groups=cefi`)
      against BOTH the on-demand endpoint (should already work) and a fresh rollup-backed response (the new capability),
      confirm no `Memory limit exceeded`/`terminated on signal 9` in Cloud Logging for either, and confirm the two paths
      agree (on-demand `scope=mvp` and rollup-fast-path `scope=mvp` return the same counts for a stable window). Repo:
      deployment-api. Done-when: fresh Cloud Logging evidence cited (timestamp + absence of OOM signal) + a diff showing
      on-demand vs rollup parity for at least cefi and one other asset_group.
- [ ] [DOCS] P3. Cross-link this plan into `mvp_scope_catalogue_tagging_2026_06_08.md`'s "Composes with" section
      (mirroring its existing `mtds_data_status_page_parity_2026_07_21.md` precedent) and confirm this plan's own
      `related:` already points back (it does, at authoring time — re-verify it wasn't edited away). Done-when: both
      docs show the bidirectional link.

## Progress Log

- **2026-08-12 (authoring)**: Two rounds of Explore-agent research established (1) the existing `CoverageScope`
  machinery and where it's already wired (drilldown, on-demand manifest/coverage-summary endpoints via
  `mvp_scope_catalogue_tagging_2026_06_08.md`), (2) the rollup worker's complete absence of scope-awareness, (3) the MVP
  source of truth (`unified-api-contracts`'s static `MVP_SCOPE` dict — cheap to call, a real release cycle to edit), and
  (4) the three-way cost split above via direct tracing of the counting loops. Operator ruled: full single-pass design
  (not a 2x-build, not deferring the dispatch-mode restructure) + human plan (not AO-dispatched). Pre-task conflict
  check surfaced the parent MVP-scope plan (this plan's `depends_on` was left `[]` since that plan's own shipped work is
  a prerequisite already satisfied, not in-flight work this plan waits on) and the still-open cefi/defi OOM issue, which
  is why the memory-safety constraint section above is load-bearing, not decorative.
- **2026-08-13 (`/autonomous` run, todo 1 shipped)**: `deployment-api@af9025b784`. Re-confirmed both source issues
  (`venue_year_coverage_cefi_oom_...`, `data_status_rollup_ml_service_full_blob_missing_...`) still `status: open` — the
  memory-safety constraint stays live. Reading `instrument_coverage.py`/`mtds.py`/`coverage.py` for todos 2-3 confirmed
  the plan's three-way cost-split analysis is accurate: `_compute_found_shards` (Tier-3) and the coverage-summary
  4-state tally (`_compute_capture_status_counts`) are both genuinely scope-independent today, and neither
  `mtds_honest_coverage_for_venue` nor `get_coverage_summary`'s wire shape currently carries a scope dimension.
  Continuing todo-by-todo; will design todos 2-3 as ADDITIVE dual-scope functions (new `*_dual_scope` entry points
  consumed only by the future rollup-worker wiring in todo 5) rather than reshaping `per_instrument_coverage`'s /
  `_compute_capture_status_counts`'s existing single-scope return contract in place — the existing on-demand
  `get_manifest_status`/`get_coverage_summary` HTTP responses are shipped, already-consumed wire contracts
  (deployment-ui parses today's flat shape) that this plan does not target; reshaping them in place would silently break
  that consumer. This satisfies each todo's own "existing tests pass unmodified" done-when criterion while still giving
  the rollup worker a genuine single-pass dual-scope compute path.
