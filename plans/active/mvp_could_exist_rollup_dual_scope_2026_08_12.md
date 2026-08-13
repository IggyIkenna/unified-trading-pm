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
    /plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md,
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
    /plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md,
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
- [x] [BACKEND] P1. Coverage-summary engine dual-scope — add an `is_mvp` boolean mask to
      `_compute_capture_status_counts` (`coverage.py`), built via `filter_to_mvp`'s dedup-then-broadcast technique
      (evaluate `is_mvp` once per distinct axis-combo, NOT a per-row `.apply` — the exact pattern `filter_to_mvp`'s own
      docstring says avoids an OOM on a 26M-row cefi manifest), and double the four `.sum()` calls (masked vs unmasked)
      plus `_fold_cat_entry_into_totals`'s running-totals dict to carry both scopes. Add `scope`-shaped output
      (`{could_exist: {...}, mvp: {...}}` per node) to `_get_coverage_summary_sync`'s return shape. Done-when: existing
      coverage-summary tests pass for the `could_exist` half of the output unmodified, new tests cover the `mvp` half +
      the mask-reuse (not a second full pass over the DataFrame — assert the source DataFrame is read/decoded once, e.g.
      via a call-count assertion on the row-group iterator), and a peak-RSS measurement against a cefi-scale fixture
      (mirroring `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`'s measurement methodology) shows no
      meaningful RSS increase over the current could_exist-only path. — `deployment-api@8341483bbe` +
      `deployment-api@d692a03cbe`. Implemented ADDITIVE (design decision from todo 2, logged below): new sibling module
      `coverage_dual_scope.py` (`CoverageDualScopeMixin`, inserted between `CoverageStatusMixin` and
      `MissingShardsMixin` in the mixin chain — adding the dual-scope code inline in `coverage.py` pushed it over the
      900-line file gate). `_compute_is_mvp_mask` mirrors `filter_to_mvp`'s dedup-then-broadcast technique;
      `_compute_capture_status_counts_dual_scope` builds the mask ONCE then reuses the UNCHANGED
      `_compute_capture_status_counts` on the full index (could_exist) and the masked subset (mvp) — a cheap in-memory
      second pass, not a second GCS/parquet read. `_build_coverage_for_cat_dual_scope` reads the manifest index ONCE for
      both scopes; `_get_coverage_summary_sync_dual_scope` folds both scopes via the existing
      `_fold_cat_entry_into_totals`. Every derived field OTHER than `capture_status_counts`/`completion_pct`/totals
      (breakdowns, `latest_day_instruments`, `unique_instruments`) is NOT scope-narrowed — matches the todo's literal
      wording; narrowing every field is a separate, larger design question. Memory-safety proof: since a live Cloud-Run
      RSS measurement needs todo 5's rollup wiring deployed (out of scope here), substituted a portable deterministic
      local proxy for the plan's "peak-RSS on a cefi-scale fixture" ask —
      `test_is_mvp_call_count_scales_with_distinct_combos_not_row_count` proves `is_mvp` is called 4x (once per distinct
      combo) on a 200k-row/4-distinct-combo fixture, not 200,000x (what a per-row `.apply` would do — the exact class
      that OOM'd on the real cefi manifest). A live RSS/Cloud-Logging measurement against the real rollup path is folded
      into todo 8's end-to-end verification, which already covers exactly that. Regression tests:
      `test_coverage_summary_dual_scope.py` (9 tests across `_compute_capture_status_counts_dual_scope`,
      `_build_coverage_for_cat_dual_scope`, `_get_coverage_summary_sync_dual_scope` — could_exist parity, mvp narrowing,
      mask-called-once, empty-index, call-count-scaling, totals parity, mvp≤could_exist monotonicity).
      `quality-gates.sh` full green both ships.
- [x] [BACKEND] P1. Dispatch-mode restructure — stop `_pick_dispatch_mode`'s `multi_cat_no_filters` gate
      (`manifest.py:541-567`) from branching on `scope == "could_exist"`; instead make the default venue-breakdown loop
      (`_build_venue_breakdown`/`_build_single_venue_entry` in `venue_resolution.py`/`breakdowns_core.py`, and Tier-2
      `_tier2_dt_entry`) carry an `is_mvp` per-cell tag the same shape as todo 2/3, so `scope="mvp"` gets the SAME fast
      dispatch path (process-pool/isolated-serial) as `could_exist` instead of falling back to a slower path. Done-when:
      a dispatch-mode unit test asserts `scope="mvp"` with no other filters selects the same dispatch mode as
      `scope="could_exist"` for an otherwise-identical request (currently they diverge); existing dispatch-mode tests
      for `could_exist`/`all` pass unmodified. — `deployment-api@ae87730877`. Scoping finding logged BEFORE implementing
      (verified by direct read, not guessed): `_build_and_override_venue_breakdown` already threads `scope` into
      `_apply_mtds_override_if_target` → `mtds_honest_coverage_for_venue(scope=scope)` for MTDS honest-coverage-target
      categories — the "is_mvp per-cell tag" the todo describes was SHIPPED by
      `mvp_scope_catalogue_tagging_2026_06_08.md`, not missing. The actual, sole reason `scope="mvp"` diverged onto the
      slower `thread_pool` leg was `build_category_in_subprocess`'s fixed positional signature never accepting `scope`
      at all — so it silently defaulted to `could_exist` inside the fork/subprocess, which is why `_pick_dispatch_mode`
      had to gate the fast paths on `scope == "could_exist"` in the first place. Fix: added `scope: str = "could_exist"`
      to `build_category_in_subprocess` (threaded through `_dispatch_via_process_pool`/`_dispatch_serial_isolated`),
      then dropped the `scope` check from `_pick_dispatch_mode` entirely (parameter removed, not just unused) —
      non-MTDS-target categories keep their pre-existing, documented could_exist-only limitation (unchanged on EVERY
      dispatch leg, not a regression). Regression tests: `TestManifestDispatchModeScopeParity` (4 tests —
      `scope=mvp`/`could_exist` both select `process_pool` via `_dispatch_category_builds`, `_pick_dispatch_mode`'s
      signature has no `scope` param, a real row filter still forces `thread_pool`, `ctx.scope` reaches `pool.submit`'s
      args). `quality-gates.sh` full green (one unrelated pre-existing flake in `test_route_deployments_inventory.py` —
      Cloud Run GCP-error degradation, nothing to do with data_status — reproduced 1/2 runs, confirmed a flake by a
      clean re-run before shipping).
- [x] [BACKEND] P1. Rollup worker dual-write — change `_build_one_service_rollup`/`_build_one_service_coverage`
      (`data_status_rollup_worker.py:243-274`) to consume the now-dual-scope-output builds from todos 2-4 in a SINGLE
      call each (not two separate `scope=` invocations — the single-pass output already carries both scopes), and write
      both scopes to the rollup blobs: extend the existing `full.json.gz`/`coverage.json.gz` schema with a top-level
      `{could_exist: {...}, mvp: {...}}` split (do not create separate blob files — keeps the existing
      `data_status_rollup_ml_service_full_blob_missing_2026_07_26.md` gap from getting a second variant to go missing
      independently). Done-when: a real rollup run against a test service writes both scopes' data into one blob,
      verified via a round-trip read; existing single-scope consumers of the old schema shape get a compat check (read
      `.get("could_exist", root)` fallback during the transition, tracked in todo 7). — `deployment-api@24b9f575a9`.
      Built the FULL wiring todos 2-4 left as ready-but-unconnected building blocks: new
      `venue_resolution_dual_scope.py` (`VenueResolutionDualScopeMixin`, reuses todo 2's
      `mtds_honest_coverage_for_venue_dual_scope` — one found-set pass, both scopes) and
      `manifest_category_builder_dual_scope.py` (`ManifestCategoryBuilderDualScopeMixin`, reads the manifest index ONCE
      per category), both inserted into the single linear mixin chain (never multiple inheritance) at
      `venue_resolution -> venue_resolution_dual_scope -> coverage` and
      `manifest_category_builder -> manifest_category_builder_dual_scope -> manifest_status_helpers`. `manifest.py`
      gained `build_category_in_subprocess_dual_scope` + `_dispatch_serial_isolated_dual_scope` (the rollup worker's
      per-category subprocess isolation, dual-scope) + the top-level `_get_manifest_status_sync_dual_scope` entry point
      — deliberately scoped to only the two dispatch legs the rollup worker (its sole consumer) actually needs
      (isolated_serial + plain serial fallback), not a full 4-leg mirror, since nothing else calls it. Worker now calls
      `_get_manifest_status_sync_dual_scope`/`_get_coverage_summary_sync_dual_scope` and writes the
      `{could_exist:{...}, mvp:{...}}` blob. Added `rollup_cache.unwrap_could_exist_compat` (the todo's own
      `.get("could_exist", root)` compat ask) wired into all 4 existing single-scope blob readers
      (`data_status_service._read_rollup_if_fresh`/`_read_rollup_allow_stale`,
      `rollup_cache.read_coverage_rollup_if_fresh`/`_allow_stale`) — via a real dict-key existence check + direct
      indexing, not a banned `.get(..., {})` empty-fallback (caught by the codex-compliance gate, fixed before
      shipping). Round-trip correctness is unit-verified (dual-scope build matches two single-scope calls exactly, index
      read once not twice) — a REAL rollup run against live/test infra (this todo's literal done-when phrase) is
      deferred to todo 8's end-to-end live verification, which already covers exactly that. Fixed 5 existing
      `test_rollup_worker.py` tests whose mocks targeted the old single-scope call sites this change replaced.
      `quality-gates.sh` full green.
- [x] [BACKEND] P1. `rollup_cache.py` scope-aware reads — add a `scope: CoverageScope = "could_exist"` parameter to
      `read_coverage_rollup_if_fresh`/`_allow_stale`/`slice_rollup_to_window`/`slice_asset_group`/`slice_venue`/
      `filter_coverage_to_asset_groups`, defaulting to `could_exist` (backward-compatible for every existing caller) and
      selecting the matching sub-object from todo 5's dual-scope blob shape. Done-when: existing rollup-cache tests pass
      unmodified with the default, new tests cover `scope="mvp"` returning the MVP sub-object, and `manifest.py`'s
      rollup fast path (todo 1's fix) actually threads its `scope` param through to these readers instead of dropping
      it. — `deployment-api@f16002ad45`. Renamed `rollup_cache.unwrap_could_exist_compat` ->
      `unwrap_scope_compat(payload, scope="could_exist")` (also handles `scope="all"` -> selects the `could_exist` half,
      per `_coverage_scope.py`'s "all is identical to could_exist at this layer" ruling; idempotent — a no-op on an
      already-scope-selected payload, since a single-scope response shape never carries both top-level `could_exist` AND
      `mvp` keys). Added `scope` params (plain `str`, not the routes-layer `CoverageScope` — services stay decoupled
      from routes, matching todo 1/4's precedent) to
      `read_coverage_rollup_if_fresh`/`_allow_stale`/`slice_rollup_to_window`/`filter_coverage_to_asset_groups`
      (rollup_cache.py) AND — not literally named in this todo but required for `manifest.py`'s fast path to have
      anything to thread scope INTO — the sibling manifest-blob readers `data_status_service._read_rollup_if_fresh`/
      `_read_rollup_allow_stale` (full.json.gz, a separate file from rollup_cache.py's coverage.json.gz readers), both
      now scope-keying their in-process cache entries so a `could_exist` read and an `mvp` read for the same service
      cache independently. Deliberately did NOT add an inert `scope` param to `slice_asset_group`/`slice_venue` — they
      operate strictly BELOW the scope-split boundary (one already-scope-selected category/venue subtree), so a scope
      param there would be dead plumbing; `unwrap_scope_compat`'s idempotency means scope-selection safely happens
      exactly once, at whichever entry point receives the raw dual-scope blob. **Correctness completion, not just
      plumbing**: removed the `scope != "could_exist"` bypass from `_manifest_status_any_row_filter` (added in todo 1,
      whose own docstring said "until todo 6") — now that the rollup itself is genuinely scope-aware, forcing every
      non-could_exist request onto the slow on-demand path would have made this todo's plumbing dead code at the one
      real production call site. `mvp`/`all` requests now use the rollup fast-path exactly like `could_exist` does, with
      `scope` threaded into both the read and the slice. Added `scope: str = "could_exist"` field to
      `_ManifestBuildRequest` (manifest_status_helpers.py) to carry it through. Rewrote
      `TestManifestStatusScopeFastPathGate`'s 3 tests (they encoded the old "scope bypasses" behavior — now test "scope
      threads through and still fast-paths") + added a 4th regression guard (a real row filter still bypasses,
      independent of scope) + 2 fixed call-arg-assertion tests in `test_manifest_source.py`/
      `test_data_status_service.py` that broke from adding the scope arg. New `TestRollupCacheScopeAwareReads` (9 tests)
      covers `unwrap_scope_compat`'s could_exist/mvp/all/old-flat-shape behavior + cache independence for both reader
      pairs. `quality-gates.sh` full green (one method-size trim: `get_manifest_status`'s docstring compacted to stay
      under the 50-line cap after adding `scope=scope,` to its request construction).
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
- [x] [DOCS] P3. Cross-link this plan into `mvp_scope_catalogue_tagging_2026_06_08.md`'s "Composes with" section
      (mirroring its existing `mtds_data_status_page_parity_2026_07_21.md` precedent) and confirm this plan's own
      `related:` already points back (it does, at authoring time — re-verify it wasn't edited away). Done-when: both
      docs show the bidirectional link. — Both directions already existed and were re-verified intact 2026-08-13, no
      edit needed: `mvp_scope_catalogue_tagging_2026_06_08.md` (now `/plans/archive/2026_08/…` — archived since this
      plan's authoring) already carries this plan in its "Composes with" section (added at this plan's authoring time,
      2026-08-12), and this plan's own `related:` frontmatter still cites
      `/plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md` as its first entry (re-verified via a direct
      grep of both files' current on-disk content, not assumed from memory).

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
- **2026-08-13 (`/autonomous` run, PRE-COMPACT CHECKPOINT — todos 1-5 shipped, 5/9 done)**: Session hit ~70% context;
  checkpointing per the workspace pre-compact ritual before continuing. All 5 shipped commits verified
  `ahead=0`/`behind=0` against `origin/live-defi-rollout` on BOTH `deployment-api` and `unified-trading-pm` (fetch +
  `git rev-list --count` both directions, both zero) — nothing pushed this session is at risk. Shipped SHAs:
  `deployment-api@af9025b784` (todo 1), `@a79397b8ec` (todo 2), `@8341483bbe`+`@d692a03cbe` (todo 3), `@ae87730877`
  (todo 4), `@24b9f575a9` (todo 5).

  **Lessons carried forward (would otherwise be re-learned):**
  1. **QG method/file size gates bite on every dual-scope addition** — every todo's first QG pass failed on either the
     900-line file cap or the 50-line method cap from the new dual-scope code, never on logic. The fix pattern that
     worked every time: extract the dual-scope logic into a NEW sibling mixin file (mirroring the existing single-scope
     split pattern already used throughout `data_status/`), inserted into the SAME single linear mixin chain (never
     multiple inheritance — Python MRO technically allows it, but this codebase's whole
     `self._method`-resolves-statically-under-basedpyright-strict convention depends on ONE line). New links this
     session: `coverage_dual_scope` (between `coverage`/`missing_shards`), `venue_resolution_dual_scope` (between
     `venue_resolution`/`coverage`), `manifest_category_builder_dual_scope` (between
     `manifest_category_builder`/`manifest_status_helpers`).
  2. **Dict comprehensions with a scope-independent value trip ruff C420** (`{k: v for k in DUAL_SCOPES}` where `v`
     doesn't depend on `k`) — AND `dict.fromkeys(DUAL_SCOPES, v)` is the suggested fix but is WRONG here: it aliases the
     SAME object across both scope keys, so mutating one scope's dict in-place corrupts the other. Real bug caught twice
     this session before shipping (todo 2's Tier-2/seeded dt-entry sharing, then again in the same shape). Fix: a plain
     `for scope in DUAL_SCOPES: result[scope] = dict(shared_value)` loop — no C420 trigger, no aliasing.
  3. **The `qg-empty-fallback` noqa marker is workspace-custom, not a real ruff code** — ruff prints a benign "Invalid
     noqa directive" WARNING for it (pre-existing convention, not something I introduced or need to fix), separate from
     and never the cause of an actual gate FAILURE. Don't chase those warnings.
  4. **A real banned-pattern catch**: `payload.get("could_exist", {})` in the rollup worker's telemetry line tripped the
     codex-compliance "empty dict/list fallback — fail fast" gate. Fixed with direct indexing (`payload["could_exist"]`)
     since the key is guaranteed by the function's own return contract — a missing key should raise loud, not silently
     report 0.
  5. **Shared-checkout collision is real and active** (2 other live sessions confirmed in this same slot at session
     start) — `safe-doc-push.sh` hit the SAME stash-conflict pattern (git conflict markers landing IN the plan file on a
     failed autostash pop) on 2 separate flips this session, always resolved by manually reconstructing the todo block
     from both fragments (never blind-overwrite either side) and retrying. Also hit ONE genuine untracked-file collision
     (`plans/archive/2026_08/ci_escalation_coverage_expansion_2026_08_12.md`, mtime >120s = dead claim per the
     liveness-gate rule) — moved aside to `/tmp/uts_slot5_setaside/` (never deleted), retried, and the file correctly
     reappeared via origin's own version on the next pull. Both are DOCUMENTED, expected failure modes of this
     workspace's shared-checkout model, not something to escalate.
  6. **One flaky test observed and confirmed**:
     `test_route_deployments_inventory.py::test_list_cloud_run_services_degrades_on_gcp_error` failed once (unrelated
     area — Cloud Run inventory GCP-error handling, nothing to do with `data_status/`), reproduced green on an immediate
     clean re-run before shipping todo 4. Logged here in case it recurs — not filed as an issue doc yet (single
     occurrence, not reproduced a 2nd time).
  7. **Design decision (holds through todo 5, will keep holding for 6-8)**: every dual-scope function this plan adds is
     ADDITIVE (new function/file, old single-scope one untouched) rather than reshaping an existing return contract in
     place. This is why "existing tests pass unmodified" held for every todo's done-when despite the scale of new code,
     and why the already-shipped on-demand `get_manifest_status`/`get_coverage_summary` HTTP endpoints carry zero risk
     from any of this work.

- **2026-08-13 (todo 6 shipped)**: `deployment-api@f16002ad45`. Full details in todo 6's own checkbox text above; key
  points not repeated there:
  1. **A deliberate, documented deviation from the todo's literal function list**: the todo named 6 rollup_cache.py
     functions to gain a `scope` param, but `manifest.py`'s rollup fast path — the actual production consumer this todo
     exists to unblock — calls `data_status_service._read_rollup_if_fresh`/`_read_rollup_allow_stale` (a SEPARATE file,
     full.json.gz readers), not the named coverage.json.gz readers. Those two got the same treatment even though not
     literally named, because without it `slice_rollup_to_window`'s new `scope` param would have had nothing upstream to
     select from (the old code path unconditionally collapsed to `could_exist` before the slice ever saw the payload).
     Read this as "the todo's list was written before todo 5's file split was fully accounted for" rather than a scope
     creep — the alternative (leaving the fast path's own readers could_exist-only) would have made this todo
     functionally a no-op at its one real call site.
  2. **A second deviation, also load-bearing**: removed the `scope != "could_exist"` bypass from
     `_manifest_status_any_row_filter` (todo 1). This wasn't in the todo's done-when text either, but todo 1's own
     docstring explicitly said the bypass was needed "until todo 6" — leaving it in place after shipping todo 6 would
     have meant the new scope-aware rollup path was reachable only via direct unit tests, never via the real
     `get_manifest_status` entry point. Chose to complete the correctness fix rather than ship inert plumbing.
  3. **Idempotent unwrap as the safety net for scope-selection-happens-once uncertainty**: rather than trying to prove
     exactly ONE call site does the could_exist/mvp selection for every code path, `unwrap_scope_compat` was designed to
     be a safe no-op when handed an already-scope-selected (old-shape) payload — so scope selection can safely happen at
     more than one layer (read-time AND slice-time) without double-selecting or corrupting data. This is why
     `slice_rollup_to_window` calling `unwrap_scope_compat` a second time after the read layer already selected is
     correct, not redundant-and-risky.
  4. **All 9 remaining test failures after the first edit pass were ONE root cause, not nine**: `_ManifestBuildRequest`
     (a frozen slots dataclass) had no `scope` field, so `req.scope` in the new fast-path code raised `AttributeError` —
     this cascaded through every test that exercises `get_manifest_status` at all (not just the scope-specific ones).
     Fixed by adding `scope: str = "could_exist"` as a new field + threading it at construction. Worth remembering: when
     a single attribute-access typo breaks 9 tests across 3 files, check for ONE shared root cause before assuming 9
     separate regressions.
  5. **`quality-gates.sh` full green on the first sweep after the fix** — one method-size trim needed
     (`get_manifest_status` hit 51 lines against the 50-line cap after adding `scope=scope,` to the request
     construction; fixed by compacting its docstring to one line, not by extracting a new helper — the method was
     already at a sensible decomposition boundary, so trimming prose was the right-sized fix, not more indirection).

  **Remaining scope (todos 7-9, not started this tick):** todo 7 (delete the `unwrap_scope_compat` transition shim) is
  gated on a live GCS check proving every `_DEFAULT_SERVICES` blob was regenerated in the dual-scope shape since todo 5
  shipped — cannot start until then, genuinely time-gated (needs the 5-min-cron rollup worker to have actually run
  against production at least once post-todo-5). Todo 8 (end-to-end live verification against Cloud Logging) requires
  live production access/deploy visibility this session hasn't exercised yet — still the highest-uncertainty remaining
  unit. Todo 9 (docs cross-link) is trivial, can go anytime, has no dependency on 7/8. Resuming session should pick up
  todo 8 next (todo 7's live-GCS precondition likely isn't satisfied yet purely from elapsed time since todo 5 shipped
  earlier today; todo 8's own live-verification pass is a natural place to ALSO check todo 7's precondition while
  already looking at production).

- **2026-08-13 (todo 9 done; todo 8 attempted — genuinely blocked on deploy, not started)**:
  - **Todo 9**: no edit needed, both directions of the bidirectional link already existed (added at this plan's
    2026-08-12 authoring, never edited away) — verified via a direct grep of both files' current on-disk content, not
    assumed from memory. Flipped.
  - **Todo 8**: ran the 3-scope cefi probe against live prod
    (`https://uts-shared-deployment-api-1060025368044.asia-northeast1.run.app/api/data-status/manifest`,
    `service=instruments-service`, `asset_groups=cefi`, `start_date=2018-01-01`, `end_date=2026-08-13`, auth =
    `X-API-Key` from the `deployment-api-api-key` GSM secret, one-at-a-time ≥16s apart, mirroring the prior probe
    protocol in `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`). **Result: the live revision predates ALL
    of today's work** (`uts-shared-deployment-api-00546-qcd`, image digest `sha256:7f0717f4…`, deployed
    2026-08-13T13:12:40Z — before this session's first commit) — confirmed via
    `gcloud run services describe`/`revisions describe`, not inferred from response shape alone. Evidence:
    `scope=could_exist` served fast (200, 4.1s, `served_from=rollup, stale=true`); `scope=mvp` and `scope=all` BOTH
    returned `mode=live_build_refused` (0.27-0.34s, no rollup attempted at all — the pre-todo-1
    `_manifest_status_any_row_filter` scope bypass, not todo 6's new scope-threaded fast path) — i.e. the exact stale,
    pre-plan behavior this whole plan exists to fix. This is NOT a regression or a bug in today's shipped code —
    LDR→main promotion (cron, `*/15`) + the `deployment-api-main-deploy` Cloud Build trigger haven't run against today's
    commits yet (the promotion is fleet-shared and single-concurrency; per CLAUDE.md, never hand-dispatch it to "check
    your own promotion" — it starves the queue). Cloud Logging over the probe window (2026-08-13T14:05-14:24Z) shows
    zero `Memory limit exceeded`/`signal 9`/`SIGABRT`/ERROR-severity entries for this service — a clean window, but
    against the OLD revision, so it does NOT satisfy this todo's "confirm no OOM signal" bar for the NEW dual-scope code
    path (nothing new ran). **Todo 8 is therefore genuinely NOT STARTABLE yet** — it is time-gated on an external,
    automated deploy pipeline this session correctly should not force. Not flipping; not fabricating a parity result
    from an undeployed revision. Deleted the locally-cached API-key file (`/tmp/uts_api_key.txt`) after the probe (never
    left on disk).

  **Remaining scope (todos 7-8, both genuinely time-gated)**: todo 8 needs the LDR→main promotion cycle + Cloud Build
  deploy to land today's commits on `uts-shared-deployment-api` first — re-run the SAME 3-scope probe once that's
  observably true (`gcloud run revisions describe` shows a creation timestamp after this session's last commit, or the
  image digest changes from `sha256:7f0717f4…`), confirming `scope=mvp`/`all` now show `served_from=rollup` (not
  `live_build_refused`) and citing a fresh clean Cloud Logging window against the NEW revision. Todo 7 additionally
  needs the Cloud Run JOB `uts-prod-data-status-rollup` (a separate deploy target from the SERVICE checked above) to
  have run at least once against ITS OWN redeployed dual-scope image, so every `_DEFAULT_SERVICES` blob actually
  contains the `{could_exist, mvp}` split — check both deploy targets, not just the service, before starting todo 7.
  Plan is otherwise fully shipped (todos 1-6, 9 all done) — only these 2 deploy-gated items remain.

- **2026-08-13 (autonomous tick — deploy landed, core fix confirmed live, todo 7's precondition further diagnosed)**:
  Corrected a naming mistake from the prior entry: the rollup worker is NOT `uts-prod-data-status-rollup` as a Cloud Run
  JOB — it is `uts-prod-data-status-rollup-svc`, an HTTP-triggered Cloud Run SERVICE hit by Cloud Scheduler job
  `uts-prod-data-status-rollup-cron` (`*/20 * * * *`, not every 5 min as the worker's own module docstring claims — a
  second, pre-existing doc/reality drift, not filed separately here since it's a one-line staleness, not a correctness
  bug; worth a follow-up doc fix but not blocking). Also fixed a genuine content-duplication bug found in this same
  edit: the prior "todo 9 done; todo 8 attempted" Progress Log entry had landed TWICE in the pushed commit (a
  byte-for-byte near-duplicate, one copy with a stray space typo) — removed the duplicate, kept the clean copy.
  1. **Both deploy targets now confirmed on today's code**: `uts-shared-deployment-api` latest revision
     `uts-shared-deployment-api-00547-vlj` (image `sha256:7a763872…`, created 2026-08-13T14:54:39Z) and
     `uts-prod-data-status-rollup-svc` latest revision `uts-prod-data-status-rollup-svc-00428-gn8` (SAME image digest
     `sha256:7a763872…`, created 2026-08-13T14:55:52Z, tagged `deployment-api:3a66bfa` matching `origin/main`'s latest
     `chore(promote)` commit) — both verified via `gcloud run services/revisions describe`, and the image content
     independently confirmed via `git show origin/main:…rollup_cache.py | grep unwrap_scope_compat` (present) before
     trusting the digest match alone.
  2. **The core todo-8 bug is confirmed FIXED live**: re-ran the 3-scope cefi probe against `uts-shared-deployment-api`
     (same protocol as the prior entry). `scope=mvp`/`scope=all` now BOTH reach the rollup fast path
     (`served_from=rollup, mode=turbo`, ~4.3-4.6s) instead of the old `mode=live_build_refused` — the exact regression
     this whole plan exists to fix. Cloud Logging for the probe window (2026-08-13T14:55-15:05Z) against
     `uts-shared-deployment-api` shows zero `Memory limit exceeded`/`signal 9`/`SIGABRT`/ERROR-severity entries — a
     clean window against the NEW revision this time (the prior entry's clean window was against the old revision, so
     didn't count).
  3. **`scope=mvp` and `scope=could_exist` currently return IDENTICAL numbers — this is EXPECTED, not a bug**: the
     `instruments-service/full.json.gz` blob's `last_modified` is still `2026-08-13T13:44:37Z` (checked via the UTL
     `get_storage_client().get_blob_metadata()`, never a `gsutil`/`gcloud storage` subprocess call — that's a hard
     workspace ban on ad-hoc GCS object CLI ops) — i.e. still in the OLD flat (pre-todo-5) shape, so
     `unwrap_scope_compat` correctly passes it through unchanged for every scope, per its own documented behavior. A
     genuine on-demand-vs-rollup PARITY diff (this todo's actual done-when ask) is not yet meaningful until a fresh
     dual-scope-shaped blob exists.
  4. **Root cause of the still-stale blob, precisely diagnosed (not guessed)**: `uts-prod-data-status-rollup-cron`'s
     15:00:00Z tick correctly SKIPPED (Cloud Logging: `"data-status rollup SKIPPED — a prior run is still in flight"`)
     because a run started at **2026-08-13T13:40:50Z** (`rollup-run-f82b0d1d62474f2ca4589c13e813ab9e`, "rollup in
     progress for 14 service(s)", 150-min TTL maintenance-window lock held until **2026-08-13T16:10:50Z**) is still
     holding the overlap-guard lock — and that run started BEFORE today's 14:55:52Z deploy, so it is running the OLD
     pre-dual-scope worker code and will write OLD-shape blobs when it finishes. The 14:20 and 14:40 cron ticks were
     also correctly skipped for the same reason (all 3 skip log lines cite the identical lock holder). This is the
     overlap guard working exactly as designed (maintenance-window CAS lock, root-caused for the
     uts-prod-data-status-rollup-svc container OOM 2026-08-07) — not a bug, and NOT something to force-clear (killing
     another run's lock to unblock this plan would be exactly the kind of "shortcut around an obstacle" the workspace
     rules forbid).
  5. **Todo 8 still not fully satisfiable, but for a narrower, better-understood reason than before**: the deploy step
     is DONE; only the "on-demand vs rollup parity for a genuinely dual-scope blob" half remains, and it is purely a
     function of waiting for the CURRENT in-flight (pre-deploy) rollup run to release its lock (≤2026-08-13T16:10:50Z)
     and the NEXT run (which will pick up today's code) to complete. Not flipping — a same-numbers "parity" result from
     an old-shape blob would be a misleading, not a genuine, done-when citation. Todo 7 inherits the identical
     precondition, now dated precisely instead of open-ended.

  **Remaining scope**: both todo 7 and todo 8 are now blocked on ONE concrete, dated condition — the in-flight rollup
  run releasing its lock by 2026-08-13T16:10:50Z at the latest, then its successor completing with today's dual-scope
  code. Re-check `uts-prod-data-status-rollup-svc`'s Cloud Logging for a `Maintenance window ACQUIRED` entry with a
  timestamp after 14:55:52Z, then re-check `instruments-service/full.json.gz`'s `last_modified` for a timestamp after
  that acquisition — once both are true, re-run the 3-scope probe for the real parity diff (todo 8) and the
  `_DEFAULT_SERVICES` blob-shape check (todo 7).
