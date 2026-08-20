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
  ]
created: 2026-07-18
last_updated: 2026-08-20 # (was: 2026-08-08 -- plan-reconcile 2026-08-18: bumped to match latest Progress Log entry, now through 2026-08-17)
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
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
- [ ] [BACKEND] P1. **Design doc — bound vs stream vs precompute** — evaluate the three directions against the
      single-walk discipline (no new whole-corpus walk), Cloud Run memory, and UI latency; pick one (or a hybrid) and
      record the decision + the projection schema. This is the design gate.
- [ ] [BACKEND] P1. **Implement the bounded read** — the API cell-grid endpoint reads ONLY the requested window from the
      manifest (or the precomputed projection), never the whole corpus; column-pruned + TTL-cached.
- [ ] [BACKEND] P2. **Precompute projection (if chosen)** — an offline job materialises the per-window cell-grid
      projection (respecting single-walk); the API reads it; manifest stays SSOT + fallback.
- [ ] [UI] P2. **Lift the 90-day default** — once the backend is bounded/precomputed, allow full-history windows in the
      UI without the OOM-guard stopgap; add a pw:L2 regression spec for a full-history render.
- [ ] [BACKEND] P2. **Load-test at full history** — prove a full-history cell-grid request stays within Cloud Run memory
      at production concurrency (cite memory p99 + latency); retire the per-request OOM guard.
- [ ] [REVIEW] P2. **Post-phase codex audit** — update `deployment-observability.md` with the new cell-grid
      architecture; confirm no plan↔codex drift.

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
