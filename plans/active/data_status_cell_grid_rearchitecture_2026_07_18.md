---
doc_type: plan
title: Data-status manifest cell-grid re-architecture — bound / stream / precompute the full-history view
summary:
  Operator ruled 2026-07-18 to schedule the real fix for a data-status tab that is fast at FULL history. Today the tab's
  manifest cell-grid is built by reading the entire per-service manifest into memory (measured ~18GB IS / 81GB MTDS /
  56GB MDPS) — the root cause of the repeated deployment-api OOMs, currently held off only by a per-request OOM guard +
  a 90-day UI default. This plan replaces that stopgap with a bounded/streamed/precomputed cell-grid so the full history
  renders without loading the whole manifest per request.
status: active
nature: design
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [cross-cutting]; repos:[deployment-api,
  # deployment-ui] only, fixing the deployment-api-side OOM behind the data-status tab UI
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [data-status, deployment-api, cell-grid, oom, performance, precompute]
related:
  [
    /plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
    /plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    /plans/active/data_status_cell_grid_rearchitecture_finalize_2026_08_21.md,
  ]
created: 2026-07-18
last_updated: 2026-08-21 # (was: 2026-08-20 -- na-eligibility-audit RECLASSIFY whole-doc: design gate resolved, remaining
# todos 3/5/6/7/8 are all bounded/deterministic (todo 3 has a ready-to-apply 6-file spec; the BLOCKED-SANDBOX notes on
# todos 3/5 were an interactive-session worktree-isolation artifact, not a real block for an AO worker with full repo
# access -- removed)
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
sequential:
  true # added 2026-08-10 (plan_reconciler) -- todo 2 (design gate: bound vs stream vs precompute) has
  # no machine gate before todo 3/4, which structurally require its decision first; both same-priority P1, so a
  # same-priority-concurrent-by-default dispatch could pick up "implement the bounded read" before the design
  # choice is made. AO-dispatch-readiness finding, no content/meaning change, restricts scheduling only.
source: "deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md §4 (operator ruling 2026-07-18: SCHEDULE)"
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    deployment-api/deployment_api/services/data_status_service.py,
    deployment-api/deployment_api/services/data_status/live_build_guard.py,
  ]
---

# Data-status manifest cell-grid re-architecture

**Operator ruling (2026-07-18):** schedule the full re-architecture (previously deferred "not using the tab now"); the
near-term OOM guard + 90-day default stay in place until this lands.

## Context

The data-status tab renders a per-(service, asset_group, venue, data_type, day) coverage cell-grid. It is currently
built by reading the ENTIRE per-service availability manifest into memory per request — measured ~18GB (IS) / 81GB
(MTDS) / 56GB (MDPS). Under Cloud Run concurrency a cold full-history build OOM-kills the container (the repeated
deployment-api OOM incidents). The near-term mitigation is a per-request OOM guard + a 90-day UI default window; the
real fix is to never load the whole manifest per request.

## Design directions (to be chosen in the design task)

- **Bound** — the read is always windowed (never whole-corpus); the UI requests a window, the backend reads only it.
- **Stream** — build the grid via a streaming/aggregating pass rather than materialising the full manifest in memory.
- **Precompute** — an offline job (the hourly consolidator or a sibling) materialises a compact per-window cell-grid
  projection the API reads cheaply (the manifest stays the SSOT; this is a read cache/projection).

## Codex SSOTs (read before designing)

- `/codex/05-infrastructure/deployment-observability.md` — deployment-api cache/observability architecture.
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest atom + single-walk discipline (no new
  whole-corpus walk is review-blocking — the precompute job must respect this).
- `/codex/02-data/honest-coverage-model.md` — the two-layer / two-view coverage model the grid renders.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — the consolidator (candidate host for a precompute step).

## Todos

- [x] ✅ [BACKEND] P1. **Measure + profile** — instrument the current cell-grid build to confirm the per-service memory
      footprint + the exact read pattern (which manifest columns/partitions a full-history request touches). Baseline
      the numbers this plan must beat. — deployment-api@8a36931
- [x] ✅ [BACKEND] P1. **Design doc — bound vs stream vs precompute** — evaluate the three directions against the
      single-walk discipline (no new whole-corpus walk), Cloud Run memory, and UI latency; pick one (or a hybrid) and
      record the decision + the projection schema. This is the design gate. Decision: **BOUND** (date_window
      pushdown), extended to the on-demand live-build fallback path. Full evidence + exact implementation spec in the
      2026-08-20 Progress Log entry. — unified-trading-pm (design doc only, no code repo touched by this decision)
- [x] ✅ [BACKEND] P1. **Implement the bounded read** — the API cell-grid endpoint reads ONLY the requested window from the
      manifest (or the precomputed projection), never the whole corpus; column-pruned + TTL-cached. **READY TO APPLY —
      exact edit spec in the 2026-08-20 Progress Log entry** (the 6-file change list, all additive optional-kwarg,
      default `None` = byte-identical prior behavior). Done-when: all 6 files edited per spec, `deployment-api`
      quality-gates green (incl. `test_manifest_status_dual_scope.py` / `test_data_status_service.py::TestReadIndexCached`
      / `test_coverage_summary_dual_scope.py`), no new whole-corpus walk introduced. — deployment-api@777f1fa531;
      evidence and implementation mapping: /plans/archive/2026_08/issues/data_status_cell_grid_todo3_shipped_pre_reclassify_2026_08_21.md
- [x] ✅ [BACKEND] P2. **Precompute projection (if chosen)** — N/A, not chosen. The `uts-prod-data-status-rollup`
      Cloud Run job + `full.json.gz`-per-service blob (`_manifest_status_rollup_fast_path` in
      `deployment_api/services/data_status/manifest.py`) already IS a working precompute projection and already
      serves every filter-free request (incl. full-history) cheaply today — no new precompute job needed. Its
      documented gap (row-filtered / venue-filtered requests bypass it, `any_row_filter` in `manifest.py`) is
      pre-existing and out of this plan's scope. See 2026-08-20 Progress Log entry.
- [x] ✅ [UI] P2. **Lift the 90-day default** — once the backend is bounded/precomputed, allow full-history windows in the
      UI without the OOM-guard stopgap; add a pw:L2 regression spec for a full-history render. **Scope note (2026-08-20):
      the "All" full-history preset already exists (`deployment-ui/src/components/DataStatusTab.tsx`,
      `FULL_HISTORY_START_DATE`) as an explicit one-click action, and the operator's 2026-07-14 ruling
      (`data-status-default-range.spec.ts`) deliberately keeps 90-day as the silent DEFAULT — this todo does NOT
      require changing `DEFAULT_LOOKBACK_DAYS`, only proving the "All" preset renders reliably + adding its pw:L2
      spec.** Done-when: a `pw:L2` regression spec exercises the "All" preset at full history and passes. —
      deployment-ui@18ba0178; evidence: `tests/e2e/data-status-default-range.spec.ts` covers the explicit "All"
      preset, asserts no request fires until "Check Status", and verifies the full-history request uses
      `start_date=2018-01-01`; source implementation is `DataStatusTab.tsx`.
- [ ] [BACKEND] P2. **Load-test at full history** — prove a full-history cell-grid request stays within Cloud Run memory
      at production concurrency (cite memory p99 + latency); retire the per-request OOM guard. **Do not mark this done
      on Bound alone** — see the full-history limitation recorded in the 2026-08-20 Progress Log entry; this gate is
      honestly unmet until either todo 8 (streaming aggregation) ships or a real production load test proves the
      worst-case (MTDS/cefi full-history + venue filter, or stale-rollup fallback at full-history) stays under the
      4 GiB limit.
- [x] ✅ [REVIEW] P2. **Post-phase codex audit** — update `deployment-observability.md` with the new cell-grid
      architecture; confirm no plan↔codex drift. Sequenced AFTER todo 3 actually ships (premature before then —
      the codex doc must describe shipped behavior, not a design decision alone). Done: added a "Bounded date-window
      read on the live-build fallback" paragraph under § "deployment-api cache & memory architecture", citing
      deployment-api@777f1fa531 and restating the plan's own not-a-full-history-fix caveat so the codex doc doesn't
      overclaim. — unified-trading-pm@6804f35e8d (shipped same session as todo 3, before the na-eligibility-audit
      reclassification pass landed — this checkbox lagged that shipment, not redone).
- [x] ✅ [BACKEND] P1. **Phase 2a — row-group-streamed slice for filtered non-DeFi/non-Prediction requests** — narrower,
      immediately-actionable first slice of the original "Phase 2" todo (rescoped 2026-08-22 after a full-pipeline
      investigation found the true scope is ~25+ methods across 8 files, not ~10-15 across ~3 — see the 2026-08-22
      Progress Log entry for the full breakdown + the found/expected-separability principle every later sub-todo
      depends on). Add `deployment_api/services/data_status/manifest_category_builder_streamed.py` (new file —
      `manifest_category_builder.py` is already 869/900 lines, no headroom): a
      `ManifestCategoryStreamedMixin._stream_prepare_manifest_slice` that streams `iter_manifest_row_groups(bucket)`
      and applies the EXISTING `_apply_manifest_filters`/`_drop_legacy_defi_and_canonicalise` per chunk (both are
      per-row-safe — no cross-row/cross-chunk dependency — so applying them per-chunk before concatenation vs once
      after is mathematically equivalent; AND-composed predicates commute), discarding non-matching rows immediately
      so only the small filtered subset is ever concatenated. Track a running per-chunk minimum date (service-masked,
      NOT venue/row-filtered — mirrors `_clamp_manifest_dates`'s genesis source exactly, which reads genesis from the
      RAW unfiltered index) for the `effective_start` genesis clamp. Wire via a `category_stream_eligible(cat,
      row_filters, pipeline_modes, venue) -> bool` gate (module-level, same new file) into `_build_manifest_category`:
      eligible when `cat.lower() not in {"defi", "prediction"}` (both need extra per-row postprocessing —
      `_postprocess_defi_merged_index`'s whitelist filter/venue-canonicalisation/CQG-promotion — not yet replicated
      per-chunk; see todos 8b/8c) AND at least one of row_filters/pipeline_modes/venue is present (an UNFILTERED
      full-history request keeps every row regardless of chunking, so streaming-then-concatenating costs the SAME
      peak memory as today's bulk read — zero benefit; that worst case is todo 8f's job). Also need a
      bucket-has-any-data check (mirrors `_resolve_category_bucket_and_index`'s `if index.empty: return None` — track
      whether `iter_manifest_row_groups` yielded ANY chunk at all, before any filtering) so an empty bucket still
      returns `_empty_category_result` instead of a spuriously-populated one. Done-when: `_build_manifest_category`
      regression suite stays green AND a new adversarial test (mock `iter_manifest_row_groups` via a `side_effect`
      factory — the pattern already proven in `tests/unit/test_route_venue_year_coverage.py`'s `_row_groups()` helper,
      no real multi-row-group parquet fixture needed) asserts byte-identical output vs the non-streamed path for a
      >1-row-group, venue-filtered fixture, PLUS a case proving the genesis-clamp matches when the true minimum date
      lives in a LATER chunk than the first one that happens to contain the requested venue. — deployment-api@e5234daebf;
      evidence: `tests/unit/test_manifest_category_builder_streamed.py` (15 specs green — eligibility gate,
      byte-identical streamed-vs-bulk slice, genesis-in-later-chunk, empty-bucket, `_build_manifest_category` wiring)
      + `tests/unit/test_data_status_service.py::TestManifestStatusVenueFilter` updated to mock both code paths and
      still green; full `deployment-api` `quality-gates.sh` green (5453 tests, function/method size gates satisfied
      via `_stream_process_chunk`/`_stream_accumulate_chunks`/`_build_manifest_category_streamed` splits).
- [ ] [BACKEND] P2. **Phase 2b — extend streamed path to DeFi** — replicate `_postprocess_defi_merged_index`'s
      per-row-safe DeFi sub-steps (`_filter_to_canonical_defi_venues`, `_canonicalise_defi_venue_column`) per chunk
      inside `_stream_prepare_manifest_slice` (confirmed per-row-safe by reading their bodies during the 2026-08-22
      investigation — no cross-row dependency). Also confirm `_collect_defi_index_frames`'s multi-bucket merge
      semantics IF `_MTDS_DEFI_SUB_DIMENSIONS` (currently EMPTY — all Phase-1 sub-buckets retired 2026-07-14) is ever
      repopulated; until then a single-bucket stream is byte-identical. Removes DeFi from
      `_STREAM_INELIGIBLE_CATEGORIES`.
- [ ] [BACKEND] P2. **Phase 2c — extend streamed path to Prediction** — replicate
      `promote_prediction_cqg_from_instrument_id` per chunk (per-row-safe: promotes `instrument_id` →
      `canonical_question_group` when the latter is empty — no cross-row dependency). Removes Prediction from
      `_STREAM_INELIGIBLE_CATEGORIES`.
- [ ] [BACKEND] P1. **Phase 2d — streamed venue breakdown + MTDS honest-coverage override** — the core
      found/expected-separability work. `_build_venue_breakdown`/`_build_one_venue_entry` (`venue_resolution.py`) and
      `_apply_mtds_honest_coverage`/`mtds_honest_coverage_for_venue` (`venue_resolution.py` + `mtds.py` +
      `mtds_dt_entries.py` — the last not yet read; read it first) split cleanly into an EXPECTED side
      (`mtds_expected_dates_for_venue_dt`/`get_expected_data_types_for_venue` — UAC config + date range ONLY,
      independent of `filtered`, so compute ONCE outside the chunk loop — calling it per-chunk and summing would
      wrongly multiply it by the row-group count) and a FOUND side (distinct `(venue, data_type, date)` triples
      actually present in `filtered` — safe to accumulate via simple per-chunk counting SUMMED across chunks, because
      the manifest consolidator guarantees no duplicate shard-atom key across the whole corpus — SSOT
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "UNION-ALL correctness" — so row groups are
      chunk-disjoint by key and `.size()`-style counts are exactly additive, the same principle
      `_live_coverage_venue_year.py` already relies on). Confirm `_mtds_seeded_entry_counts`'s seeded-dt branch
      (`mtds_dt_entries.py`) is ALSO found-side-only before assuming it's safe to accumulate the same way. Done-when:
      same regression-suite-green + byte-identical adversarial test bar as 8a, extended to the `venues`/`data_types`
      result keys.
- [ ] [BACKEND] P2. **Phase 2e — streamed sub-dimension grouping** — `_build_data_type_grouping` +
      `_build_v4_sub_dimensions`'s 4 extras (`_build_chain_breakdown`, `_build_defi_sub_dimension_breakdown`,
      `_build_feature_group_breakdown`, `_build_underlying_grouping` — none read yet, read first) plus sports
      honest-coverage (`sports_helpers.py::sports_honest_coverage` + `_honest_coverage_per_league`/`_global` +
      `get_sports_entity_start_date`/`get_entity_league_coverage` — none read yet). Apply the SAME found/expected
      split as 8d — expect these to follow the identical pattern (sports fixture calendars + transfer windows are
      config/UAC-derived "expected", like MTDS's).
- [ ] [BACKEND] P1. **Phase 2f — wire the fully-streamed pipeline for the genuine full-history worst case + dual-scope
      + guard retirement** — once 8a-8e land, extend `category_stream_eligible` to ALSO cover the unfiltered
      full-history case (the ORIGINAL worst case "Phase 2" was created for) — the only slice that needs the full
      found/expected-split machinery from 8d/8e even with NO row/venue filter narrowing the input. Mirror into
      `manifest_category_builder_dual_scope.py`'s `_build_manifest_category_dual_scope`/
      `_compute_venue_breakdown_with_overrides_dual_scope`. Add the FULL adversarial byte-identical test across the
      WHOLE `_build_manifest_category` result dict (not just the slices 8a-8e tested individually) on a full-history,
      multi-row-group, multi-venue, MTDS-honest-coverage-eligible fixture — this is the test the original todo 8's
      strengthened done-when actually asked for. Only then does todo 6 (load-test / guard retirement) become honestly
      closeable for the worst case.

## Progress Log

- **2026-07-18** — Authored after the operator moved the cell-grid re-architecture from deferred to scheduled. Human
  plan (operator-driven). The near-term OOM guard + 90-day default remain the live mitigation until this lands.

- **2026-07-22 — Cross-plan pointer (research-only, no code changed here).**
  `mtds_data_status_page_parity_2026_07_21.md` investigated whether the operator's separate "the whole mtds needs to be
  much faster" complaint traces to THIS plan's documented OOM/whole-manifest-load architecture or a distinct issue.
  Verdict: **confirmed the SAME root cause** for the MTDS "Data Coverage" panel specifically — traced the live code (not
  just this plan's prose) and confirmed `read_availability_index(bucket)`
  (`deployment-api/deployment_api/services/data_status_service.py::_read_index_cached:449`, called via
  `defi.py::_read_defi_merged_index:274` from `manifest.py::_build_manifest_category:771`) still loads the ENTIRE
  per-service manifest into memory unconditionally before applying any date/venue/scope mask (`manifest.py:798`) — this
  plan's "read the ENTIRE per-service manifest into memory per request" description is still accurate today, unchanged
  since authoring. `live_build_guard.py`'s module docstring/calibration anchors carry the IDENTICAL measured figures
  this plan cites (18GB IS / 81GB MTDS / 56GB MDPS full-history) — confirms it's the same incident, not a
  similar-sounding coincidence; that guard module + the 90-day UI default ARE this plan's "near-term OOM guard" stopgap
  referenced above, already shipped, still the only live mitigation. `mtds_data_status_page_parity_2026_07_21.md`
  shipped Bug C (per-instrument existence-window clipping), MVP-scope wiring, and an MDPS-timeframe extension THIS
  SESSION — all of it runs as bounded, vectorized pandas/Python work strictly downstream of the `filtered` DataFrame
  this plan's `_build_manifest_category` already loads (see `instrument_coverage.py::per_instrument_coverage`), plus one
  small SEPARATE identity-only read (`prod/catalog.parquet` via `_read_cefi_catalogue_metadata`, explicitly not a second
  whole-corpus walk). **None of that work introduces a new bottleneck or duplicates this plan's scope** — it's a
  downstream consumer riding on the same not-yet-re-architected load path this plan exists to fix. No new todo needed
  here; this plan's existing Bound/Stream/Precompute directions remain the correct fix for both the pre-existing
  coverage grid and the MVP-scope/MDPS-timeframe additions on top of it. (Separately, the operator's complaint ALSO
  covered symbol/ instrument search latency — that traced to a DIFFERENT, non-memory root cause — sequential per-venue
  GCS reads, already partially fixed via threading in a pre-session commit — and does not belong to this plan; see
  `mtds_data_status_page_parity_2026_07_21.md`'s research todo for the full writeup.)

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — todo 2 is an explicit DESIGN GATE (pick bound vs stream vs
  precompute) and every later todo depends on that unmade choice.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- dropped honest-coverage-
  model.md (tangential to the OOM/memory fix), added `live_build_guard.py`, the current stopgap mitigation this plan
  replaces.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-a6d668)**: KEEP-NA, valid — same as 2026-07-30; the first
  real todo is an explicit DESIGN GATE (pick bound vs stream vs precompute) and every later todo depends on that unmade
  choice.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — same as 2026-07-30/2026-08-06; todo 2 is still an
  unresolved DESIGN GATE (bound vs stream vs precompute) every later todo depends on.

- **2026-08-08 — Todo 1 complete (slot-12 agent, deployment-api@8a36931).** **Instrumentation added**:
  `_read_index_cached` in `deployment_api/services/data_status_service.py` now logs at INFO on every cache-miss GCS
  fetch: bucket name, row count, and in-process DataFrame bytes (`df_gb`). Log key:
  `manifest-read-profile bucket=<bucket> rows=<N> df_bytes=<B> df_gb=<G>`.

  **Read pattern — old cell-grid build path (`_build_manifest_category` via `_read_index_cached`)**:
  - Calls `read_availability_index(bucket)` with no `date_window` (no row-group pushdown).
  - Column set: `DRILLDOWN_COLUMNS` (27 columns — same projection all manifest readers share).
  - Scope: **ALL row groups** — the entire multi-year manifest is loaded unconditionally regardless of the display
    window. Date/venue/service masks applied AFTER this full load.

  **Memory footprint — calibration anchors from `live_build_guard.py`** (measured 2026-07-13/14, full-history = 3,120
  days, 5 categories each):
  - instruments-service: **18 GB** (3,120 days × 5 cats) → ~1.15 MB/day/category
  - market-tick-data-service: **81 GB** (3,120 days × 5 cats) → ~5.19 MB/day/category
  - market-data-processing-service: **56 GB** (90 days × 5 cats) → ~124 MB/day/category

  MDPS's rate (~124 MB/day/category) is the conservative default in `live_build_guard.py` for services without their own
  calibration anchor. A 30-day MDPS window costs ~18.6 GB — already OOM territory for Cloud Run's 4 GiB limit.

  **Architecture contrast — `/coverage-grid` endpoint already has partial fix**: `_coverage_grid.py` calls
  `read_manifest_index(bucket, date_window=(start_date, end_date))`, enabling date-range row-group pushdown.
  `manifest_source.py` documents the measured effect: "~14.86 GiB → ~5 MB for a single-day filter on the 27.4M-row DeFi
  index." The re-architecture (todos 3+) should extend this approach to `_get_manifest_status_sync` /
  `_build_manifest_category`.

  **Numbers this plan must beat (Cloud Run 4 GiB limit)**:
  - MTDS full-history: 81 GB → need ≥20× reduction.
  - The 90-day UI default provides partial relief (90 × 5.19 MB/cat × 5 cats ≈ 2.3 GB MTDS), but full-history windows
    are still OOM-dangerous — hence the `live_build_guard.py` pre-flight refusal.
  - Target for todo 2 design: bounded/streamed/precomputed approach must keep peak RSS < 4 GiB even for a full-history
    request at MTDS's worst-case rate (5.19 MB/day/category).

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged):
  todo 2 is still an unresolved DESIGN GATE (bound vs stream vs precompute) every later todo depends on; a genuine
  architecture choice among 3 directions with different Cloud-Run-memory/single-walk-discipline implications, not a
  cheat-sheet-matched default.
- **context-scout 2026-08-15**: refreshed context_scope (6 entries) -- swapped in `data_status_service.py` (confirmed by
  the 2026-08-08 Progress Log entry as the actual `_read_index_cached`/`_build_manifest_category` rearchitecture
  target), dropped `mtds_data_status_page_parity_2026_07_21.md` (the doc's own text explicitly disclaims it as a
  different, non-memory root cause that "does not belong to this plan").
- **na-eligibility-audit 2026-08-17 (ui tranche)** [body-hash:520cecb45b937315]: KEEP-NA, valid — todo 2 (bound vs
  stream vs precompute) remains a genuine unresolved 3-way architecture judgment call every later todo (3-7) depends
  on (`sequential: true`, added by plan_reconciler 2026-08-10, functions as the machine-readable gate). 5th
  consecutive audit pass reaching this verdict; `ui_satellite_ao_dispatch_batch1_2026_08_06.md` explicitly defers this
  doc's todo 2 back here rather than extracting it.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

- **2026-08-20 — Todo 2 (design gate) complete + todo 4 resolved N/A (agent session, unified-trading-pm only —
  see BLOCKED-SANDBOX note below).**

  **Decision: BOUND** — extend the `date_window` row-group-pushdown pattern `_coverage_grid.py` already proved
  (`manifest_source.read_manifest_index(bucket, date_window=(start,end))`) into the on-demand live-build fallback
  path (`ManifestStatusMixin._get_manifest_status_sync` → `_dispatch_category_builds` → `_build_manifest_category` →
  `_resolve_category_bucket_and_index` → `_read_defi_merged_index`/sports.py → `data_status_service._read_index_cached`
  → bare `read_availability_index(bucket)`, no `date_window`, no row-group pushdown — confirmed via direct code read,
  not inference). Rejected "Stream" and "Precompute" as the PRIMARY todo-3 direction (both still land, see below) for:

  - **Precompute already exists** — `uts-prod-data-status-rollup` (Cloud Run job, `*/5`) writes
    `{service}/full.json.gz`; `get_manifest_status` (`manifest.py`) tries `_manifest_status_rollup_fast_path` FIRST
    for every filter-free request (including full-history — `slice_rollup_to_window` has no window cap) and only
    falls to the memory-heavy live build when the rollup is stale/missing OR the request carries a row filter
    (venue/league_id/chain/etc — `any_row_filter`). Building a second precompute mechanism would duplicate this.
    Todo 4 is marked done/N/A on this finding.
  - **Stream (full rewrite) is higher-risk than needed for todo 3's scope** — `_build_manifest_category`'s pipeline
    (venue breakdown, MTDS honest-coverage override, sub-dimension grouping, dual-scope) is ~15 methods deep and
    heavily unit-tested; rewriting it to consume row-group-streamed accumulators in one pass carries real regression
    risk. Bound is a 6-file, additive, optional-kwarg change with zero behavior change for existing callers
    (`date_window=None` default) — ships now, safely.

  **Safety check performed**: `_clamp_manifest_dates` (`manifest_category_builder.py`) reads
  `index["date"].min()` across the WHOLE loaded index to clamp `effective_start` UP toward the data-observed genesis
  when later than the configured/requested start. Windowing the read to `[start_date, end_date]` does not change
  this: `effective_start` is already `>= start_date` before the clamp runs, so the clamp only ever needs genesis
  dates `>= start_date` (never earlier) — exactly what a `[start_date, end_date]`-windowed read still contains.
  Confirmed no other downstream consumer (`_apply_manifest_filters`, MTDS override, sub-dimension regroup,
  missing-shards) needs manifest rows outside the requested window.

  **Known limitation — full-history is NOT solved by Bound alone**: pyarrow row-group pushdown only skips groups
  entirely OUTSIDE the requested window. Measured (2026-08-09 cefi OOM audit, `manifest_source
  .iter_manifest_row_groups` docstring): cefi/MTDS-scale manifest row groups span 2-2.5 CALENDAR YEARS each (rows
  are not date-sorted at write time), so a genuinely full-history window (2018-01-01→today) overlaps virtually
  every row group — pushdown provides ~0 reduction for that specific case, same failure mode the venue-year-coverage
  endpoint hit and fixed via row-group-streamed aggregation (`_live_coverage_venue_year.py` +
  `iter_manifest_row_groups`, proven: bounds peak memory to ~10 MB/row-group for cefi regardless of corpus size).
  Recorded as a new todo (the list's 8th item, "Phase 2 — row-group-streamed full-history aggregation") rather than
  left as prose, per the HARD RULE. **Todo 6 (retire the OOM guard) must not be marked done on Bound alone** — the
  guard is still the only thing protecting the full-history + venue-filter / stale-rollup-fallback worst case.

  **Ready-to-apply implementation spec for todo 3** (fully designed, NOT yet shipped — see BLOCKED-SANDBOX below):
  1. `deployment_api/services/data_status_service.py::_read_index_cached` — add `date_window: tuple[str, str] |
     None = None` param; cache key becomes `(bucket, date_window)`; call
     `read_availability_index(bucket, date_window=date_window)` (was bare `read_availability_index(bucket)`).
  2. `deployment_api/services/data_status/defi.py::_read_defi_merged_index` +
     `_collect_defi_index_frames` — add the same optional `date_window` param, thread to both
     `_read_index_cached` call sites (main bucket + per-sub-dimension bucket loop).
  3. `deployment_api/services/data_status/manifest_category_builder.py::_resolve_category_bucket_and_index` —
     add the same optional param, thread to `_read_defi_merged_index`; at `_build_manifest_category`'s call site,
     pass `date_window=(start_date, end_date)` (the method already has both in scope).
  4. `deployment_api/services/data_status/manifest_category_builder_dual_scope.py::_build_manifest_category_dual_scope`
     — same call-site change.
  5. `deployment_api/services/data_status/sports.py::_read_upstream_venue_dates` — pass
     `date_window=(start_date, end_date)` to its `_read_index_cached` call (same bottleneck, already has the window
     in scope).
  6. `deployment_api/services/data_status/missing_shards.py::_scan_category_manifest` — same, via
     `_read_defi_merged_index(service, cat, cloud=cloud, date_window=(start_date, end_date))` (sibling endpoint,
     identical pre-existing bug).
  Deliberately OUT of scope: `coverage.py::_build_coverage_for_cat` / `coverage_dual_scope.py`
  (`GET /coverage-summary`) — that endpoint has no date-range param at all (whole-history stats by design), so
  `date_window` does not apply there. All 6 changes are additive (new optional kwarg, default `None` = byte-identical
  prior behavior) — verified against existing tests (`test_manifest_status_dual_scope.py`,
  `test_data_status_service.py::TestReadIndexCached`, `test_coverage_summary_dual_scope.py`) which patch these
  methods via `patch.object(..., return_value=...)` without `autospec`, so the new kwarg cannot break them.

  **BLOCKED-SANDBOX (environment finding, not a content judgment call)**: this session's `isolation: "worktree"`
  scope covers `unified-trading-pm` ONLY — `EnterWorktree` confirmed refusal to cross into `deployment-api` /
  `deployment-ui` ("not under .../.claude/worktrees... limited to worktrees managed by Claude Code created under
  .claude/worktrees/ of this repository"), and direct git/Edit operations against those repos' shared checkouts are
  guard-blocked ("a worktree-isolated agent's git operations must target its own worktree"). Todos 3, 5, 6 need a
  session/slot with real write access to `deployment-api`/`deployment-ui` to apply the spec above, run
  `quality-gates.sh`, and ship via `quickmerge.sh`. Todo 7 (codex audit) is correctly sequenced after todo 3 actually
  ships, so also not yet actionable. Flagging this because it blocks 4 of this plan's 8 todos, not because the
  plan's own content is wrong.

- **na-eligibility-audit 2026-08-21 (ui tranche)**: RECLASSIFY (whole-doc) — todo 2's design gate (the sole reason
  every prior audit pass since 2026-07-30 kept this doc KEEP-NA) resolved 2026-08-20 (Decision: BOUND). All 5
  remaining open todos (3, 5, 6, 7, 8) are bounded/deterministic: todo 3 has a ready-to-apply 6-file spec written out
  in the 2026-08-20 Progress Log entry above; todo 5 is a scoped pw:L2-proof with an explicit non-goal already
  stated; todo 6 is a load-test with a stated numeric done-when (p99 < 4 GiB); todo 7 is sequenced (already
  `sequential: true`) after todo 3 ships; todo 8 extends an already-proven sibling pattern
  (`_live_coverage_venue_year.py`'s row-group streaming) to a named pipeline, now with a strengthened done-when per
  finding V (regression suite green + a new adversarial byte-identical-output test) given the shared fleet-wide
  correctness risk. Removed the `BLOCKED-SANDBOX` literal from todos 3/5 — that token structurally excludes a todo
  from AO ingestion (`task_template.md` §3's non-dispatchable family), but the block was specific to THIS
  interactive session's `isolation: "worktree"` scope (confirmed confined to `unified-trading-pm` only); an AO
  worker on the single orchestrator VM has a full multi-repo checkout, so it does not apply there. Conflict-check
  clear: `grep -rl "date_window" plans/active/*.md` returns only this doc; no other active `assigned_vm: planning`
  doc under `parent_epic: deployment_and_user_management_master` touches this cell-grid/manifest-read-path work.
  Flipped `assigned_vm: NA` → `planning`, `execution_scope: local-only` → `orchestrator-agent`; kept `sequential:
  true` (todo 7 genuinely depends on todo 3; todos 3/6/7/8 plausibly share files in the
  `deployment_api/services/data_status/` tree, so intra-plan concurrency stays off). Authored companion
  `data_status_cell_grid_rearchitecture_finalize_2026_08_21.md` per the finalize-plan-coverage rule.

- **2026-08-22 — Todo 8 investigation + split (slot-24 agent, deployment-api — no code shipped this session).**
  Dispatched to implement the original "Phase 2 — row-group-streamed full-history aggregation" todo (now split into
  8a-8f above). Read the FULL `_build_manifest_category` pipeline end-to-end (`manifest_category_builder.py`,
  `venue_resolution.py`, `breakdowns_domain.py`, `defi.py`, `coverage.py`, `coverage_metrics.py`, `mtds.py`) before
  writing any code, per the "no soft-delete-style safety net" strengthened done-when.

  **Finding: the true scope is materially larger than the todo's own "~10-15 methods" estimate** — ~25+ methods
  across 8 files (the 7 above + `mtds_dt_entries.py` and `sports_helpers.py`, neither read yet), because the
  aggregation isn't a flat set of simple row counts: MTDS honest-coverage override, sports honest-coverage, and the
  v4 sub-dimension breakdowns each cross-reference a UAC/config-derived EXPECTED universe against the
  manifest-derived FOUND set — a fundamentally different shape than the proven `_live_coverage_venue_year.py`
  sibling (which only ever counts manifest rows, no external expected-universe cross-reference).

  **The principle that makes streaming safe (load-bearing for every 8a-8f sub-todo)**: EXPECTED-side values
  (`mtds_expected_dates_for_venue_dt`, sports fixture calendars, transfer windows) depend ONLY on UAC config + the
  request's date range — NEVER on `filtered` — so they MUST be computed ONCE outside any chunk loop; calling the
  same expected-computation once per row-group chunk and summing would multiply it by the row-group count (a
  correctness bug, not just an inefficiency). FOUND-side values (distinct `(venue, data_type, date)` triples
  actually present) ARE safe to accumulate via simple per-chunk counting summed across chunks, because the manifest
  consolidator's dedup guarantees exactly one row per shard-atom key across the WHOLE corpus (SSOT
  `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "UNION-ALL correctness") — row groups are therefore
  chunk-disjoint by key, so `.size()`-style row counts are exactly additive, matching the same assumption
  `_live_coverage_venue_year.py` already relies on (confirmed by reading its `_process_manifest_chunk`/
  `_accumulate_venue_year_counts` implementation).

  **Also found**: `_read_defi_merged_index`'s DeFi/Prediction postprocessing (`_postprocess_defi_merged_index` —
  venue whitelist filter, venue canonicalisation, CQG promotion) is per-row-safe but not yet replicated in a
  streamed form — scoped out to todos 8b/8c rather than blocking the first slice. Row/venue/pipeline_mode filters
  and `_drop_legacy_defi_and_canonicalise` are ALSO per-row-safe and commute with the date-range mask regardless of
  application order (AND-composed predicates), which is what makes todo 8a's per-chunk-then-concatenate design
  byte-identical to today's read-then-filter-once design. `_MTDS_DEFI_SUB_DIMENSIONS` (the DeFi multi-bucket merge
  list `_collect_defi_index_frames` iterates) is currently EMPTY (all Phase-1 sub-buckets retired 2026-07-14), which
  is what makes 8a/8b tractable as a single-bucket stream rather than needing a multi-bucket merge design now.

  **Test pattern already proven in this codebase** (no new fixture-building infra needed): `_row_groups()` in
  `tests/unit/test_route_venue_year_coverage.py` mocks `iter_manifest_row_groups` via a `side_effect` factory
  yielding plain in-memory DataFrames as separate "row groups" — no real multi-row-group parquet file needs to be
  written. Every 8a-8f adversarial test should reuse this pattern.

  **Split rationale**: same reasoning as this plan's own todo 8 being split out of todo 3 originally ("a materially
  larger rewrite... hence split out as its own todo") — the newly-discovered true scope repeats that pattern one
  level deeper, so todo 8 (the original combined scope) is REPLACED above by 8a-8f, sequenced by genuine dependency
  (8a is the base primitive; 8b/8c extend its category coverage; 8d/8e are the harder found/expected-split work;
  8f is the final wiring + the full byte-identical test the ORIGINAL todo 8 asked for). Judged safer to ship this
  research + re-scoping now than to rush a partial/risky implementation of shared fleet-wide manifest-aggregation
  code under session time/context pressure — implementing 8a is the next actionable unit.

- **2026-08-22 — Todo 8a shipped (slot-6 agent, deployment-api@e5234daebf).** New file
  `deployment_api/services/data_status/manifest_category_builder_streamed.py`: `category_stream_eligible(cat,
  row_filters, pipeline_modes, venue)` gates eligible (non-defi/prediction + at least one narrowing filter) requests
  through `ManifestCategoryStreamedMixin._stream_prepare_manifest_slice`, which streams
  `iter_manifest_row_groups(bucket)` and applies `_apply_manifest_filters`/`_drop_legacy_defi_and_canonicalise` per
  chunk (split into `_stream_process_chunk` + `_stream_accumulate_chunks` to satisfy the 50-line method-size gate),
  discarding non-matching rows before concatenation. Tracks a running service-masked (not venue/row-filtered)
  per-chunk minimum date for the `effective_start` genesis clamp, exactly as spec'd — proved via a dedicated test
  that puts the true corpus-wide minimum date in a LATER chunk than the first one containing the requested venue.
  Wired into `_build_manifest_category` by inserting `ManifestCategoryStreamedMixin` into the mixin chain between
  `ManifestCategoryBuilderMixin` and `ManifestCategoryBuilderDualScopeMixin`; ineligible requests fall through to
  `super()._build_manifest_category(...)` (the pre-existing bulk path) unchanged. Also split
  `_resolve_category_bucket` out of `_resolve_category_bucket_and_index` (pure code motion) so the streamed path can
  resolve a bucket name without paying for `_read_defi_merged_index`'s bulk read.

  **Regression found + fixed in the same session**: `TestManifestStatusVenueFilter::test_venue_filter_narrows_to_requested_venue`
  (`test_data_status_service.py`) passed `cat="CEFI"` + `venue=["BINANCE-FUTURES"]` with only `_read_defi_merged_index`
  mocked — this now routes through the NEW streamed path (venue filter + non-defi/prediction category is exactly
  todo 8a's eligibility target), so the test needed `_resolve_category_bucket` + `iter_manifest_row_groups` mocked
  too (both patched to serve the same fixture data the bulk mock already used). Fixed by extending that test's
  `_build_with` helper; confirmed the fix doesn't paper over a real behavior change (both code paths now produce the
  same filtered slice for this fixture, verified by the new byte-identical adversarial test in the new test file).

  Evidence: new `tests/unit/test_manifest_category_builder_streamed.py` (15 specs: eligibility-gate cases,
  streamed-vs-bulk byte-identical slice on a >1-row-group venue-filtered fixture, the genesis-in-later-chunk case,
  empty-bucket→None, `_build_manifest_category` wiring proving eligible/ineligible requests call the right read
  primitive and never both) + full `deployment-api` `quality-gates.sh` green (5453 tests passed, basedpyright clean,
  no new size/lint/ratchet violations).
