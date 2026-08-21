---
doc_type: issue
title: CBOE venue-level discovery floor blocks the Yahoo Treasury-INDEX series' real pre-2020 history
summary: >-
  `is_venue_available()` (market-tick-data-service `engine/orchestrator/__init__.py`) checks discovery-floor
  availability at (venue, date) granularity only — never (venue, data_type, date). CBOE is a MIXED venue: the registered
  floor is the Databento VX-FUTURE genesis (~2020-06-01), but the Yahoo Treasury yield-curve INDEX (ohlcv_24h) has real
  Yahoo daily history back to 2000-01-03 for 4 of 5 tenors (US3M/US5Y/US10Y/US30Y — ^IRX/^FVX/^TNX/^TYX) and 2018-08-13
  for the 5th (US2Y — 2YY=F). Every CBOE ohlcv_24h date before ~2020-06-01 is silently classified `HONEST_ABSENCE ...
  EXPECTED_PRE_SOURCE_COVERAGE_START` and no manifest row is written — a structurally correct honest-absence signal for
  the WRONG floor, so real, fetchable Yahoo data is never attempted for that whole multi-year window.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, cboe, discovery-floor, honest-absence, yahoo, data-correctness]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/archive/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-08-09
author: claude-code (data_engineering worker, slot 17, tradfi_satellite_ao_dispatch_batch10 todo 1)
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: >-
  Found while verifying/launching the CBOE Treasury yield-curve INDEX backfill for
  `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1. After fixing the separate
  `_resolve_source` --source-required gate bug (CBOE ohlcv_24h missing from the Yahoo-routed venue exemption —
  market-tick-data-service@af2c53ce), a `--start-floor 2000-01-01` relaunch of the CBOE Treasury-INDEX launcher still
  wrote ZERO real rows for years 2000-2019 (all dates logged `HONEST_ABSENCE: 1 venue(s) below UAC discovery floor ...
  EXPECTED_PRE_SOURCE_COVERAGE_START: ['CBOE']`), while years 2020+ wrote real captured rows correctly
  (`CBOE:INDEX:US3M/US5Y/US10Y/US30Y-USD` for 2021-01-04 onward, confirmed via run.log). The CBOE Treasury-INDEX
  launcher's own header comment already documents the intent this bug defeats: "this launcher deliberately does NOT
  apply the UAC venue-discovery-floor clamp — that floor (VenueMapping "CBOE") is the DATABENTO VX-futures genesis
  (~2020-06-01), which is WRONG for the Yahoo Treasury series" — but that comment only describes the LAUNCHER script's
  own `START_FLOOR` handling; it does not (and structurally cannot) prevent the orchestrator's independent
  `is_venue_available()` preflight gate from re-applying the venue-wide floor downstream.
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py,
  ]
drift_direction: advance-code
depends_on: []
---

# CBOE venue-level discovery floor blocks the Yahoo Treasury-INDEX series' real pre-2020 history

## What I found

`market_tick_data_service/engine/orchestrator/__init__.py::is_venue_available(venue, date)` delegates to
`_VENUE_MAPPING.is_venue_available_on_date(venue, date)` — a single floor date PER VENUE, with no data_type dimension.
`_build_active_venues_for_date()` calls this to strip below-floor venues into `pre_coverage_skipped`
(`preflight.py::_log_pre_coverage_honest_absence`), which correctly writes NO manifest row (by honest-absence design —
an `expected_unattempted` or `empty_confirmed` row there would be a numerator-credited fabrication of a fetch that never
ran).

CBOE is registered with a SINGLE floor (~2020-06-01, the Databento VX-FUTURE genesis via `XCBF.PITCH`). But CBOE also
serves a second, entirely separate data_type/source pairing: the Yahoo Finance daily Treasury yield-curve INDEX
(`ohlcv_24h`, `route_yahoo_tradfi("CBOE", ...)` in `_umi_yahoo.py`, gated to
`_CBOE_YAHOO_TREASURY_DATA_TYPES = {"ohlcv_24h"}`), whose REAL Yahoo history starts far earlier:

- US3M/US5Y/US10Y/US30Y (`^IRX`/`^FVX`/`^TNX`/`^TYX`): 2000-01-03
- US2Y (`2YY=F`): 2018-08-13

Because `is_venue_available()` has no data_type awareness, EVERY CBOE ohlcv_24h date before the Databento-genesis floor
(~2020-06-01) is treated as `EXPECTED_PRE_SOURCE_COVERAGE_START` and silently skipped — even though real, fetchable
Yahoo data exists for ~20 years of that window for 4 of the 5 tenors.

**Live evidence (2026-08-09, same-day verification during this task):**

- `tradfi-bf-cboe-idx-ohlcv-24h-2000-...` run.log: every date in Jan/Feb 2000 logs
  `HONEST_ABSENCE: 1 venue(s) below UAC discovery floor for date=2000-02-XX — out-of-window (EXPECTED_PRE_SOURCE_COVERAGE_START) ... no manifest row written: ['CBOE']`.
- `tradfi-bf-cboe-idx-ohlcv-24h-2021-...` run.log: same date range logic, but 2021-01-04 onward writes real
  `StreamingParquetWriter` uploads for `CBOE:INDEX:US3M/US5Y/US10Y/US30Y-USD`.
- Manifest query (`read_availability_index_safe`, venue=CBOE, data_type=ohlcv_24h) before any fix: 2230 rows, 100%
  `empty_confirmed` with BLANK `instrument_id` — the OLD bug (separate, already-fixed `_resolve_source` issue). After
  the `_resolve_source` fix + this floor gate, years 2020+ now write real per-instrument `captured` rows; years
  2000-2019 still write NOTHING (correct honest-absence behavior for the WRONG floor, not a crash).

## Why it matters

The CBOE Treasury-INDEX launcher's own design intent (per its header comment, and the operator ruling in
`tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` which explicitly calls for `--start-floor 2000-01-01` "for the
full ^TNX/^TYX/^IRX/^FVX history") cannot be satisfied by the launcher alone — the floor is enforced a second time,
independently, downstream in the orchestrator, using the wrong (Databento) genesis date for a Yahoo-routed data_type.
This is the same venue-conflates-two-sources problem the codebase already has a proven pattern for
(`_CBOE_YAHOO_TREASURY_DATA_TYPES` in `_umi_yahoo.py`; `_CBOE_YAHOO_ONLY_DATA_TYPES` added to
`tick_data_handler.py::_resolve_source` in this same session, `market-tick-data-service@af2c53ce`) — but
`is_venue_available()` was never updated to the same data-type-aware discrimination.

## Recommended decision

Make the discovery-floor check data-type-aware for CBOE specifically (mirroring the two existing CBOE
data-type-discrimination sites), rather than a blanket per-venue floor change (which would incorrectly widen the floor
for CBOE's real Databento VX-futures leg too). Concretely:

- `is_venue_available()` needs an optional `data_types` (or `data_type`) parameter; when the venue is CBOE and the
  requested data_types are a subset of the Yahoo-only set, resolve against a Yahoo-specific floor (2000-01-03, or a
  documented per-tenor table if exactness matters) instead of the registered VenueMapping floor.
- The registered VenueMapping floor doesn't need to change — the VX-futures Databento leg's own floor is correct and
  should stay untouched (the same reasoning as `_CBOE_YAHOO_ONLY_DATA_TYPES`'s guard against a blanket exemption).
- `_build_active_venues_for_date()` and its callers would need to thread `data_types` through to `is_venue_available()`.

This is a real cross-cutting orchestrator change (not confined to one file/handler), so it is intentionally NOT bundled
into the `_resolve_source` fix already shipped this session (`market-tick-data-service@af2c53ce`) — that fix closed a
hard failure (every CBOE ohlcv_24h payload erroring); this floor gap is a silent-but-honest under-coverage, lower
urgency, and warrants its own scoped implementation + test pass.

## Todos

- [x] ✅ [DATA] P2. **DONE — flipped 2026-08-12 (/plan-reconcile), sha's independently verified to exist.** Shipped via
      `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` todo 1: `UAC@a65c2fa9` (`_data_type_floor_overrides` field in
      `VenueMapping`), `MTDS@fe000178` (`data_type` param on `is_venue_available()` wrapper). Add data-type-aware floor
      resolution for CBOE to `is_venue_available()` (`market_tick_data_service/engine/orchestrator/__init__.py`) so CBOE
      ohlcv_24h (Yahoo Treasury INDEX) dates from 2000-01-03 (or the correct per-tenor floor) are attempted instead of
      auto-skipped via the Databento VX-futures genesis (~2020-06-01). Thread `data_types` through
      `_build_active_venues_for_date()` and its callers. Add regression tests confirming (a) CBOE Databento VX-futures
      dates before ~2020-06 still correctly skip as honest-absence, (b) CBOE Yahoo ohlcv_24h dates from 2000-2020-06 now
      attempt a real fetch. Repo: market-tick-data-service. **(na-eligibility-audit 2026-08-10, tradfi tranche, dispatch
      agt-a70469): KEEP-NA-STALE (already-duplicated) — this item is extracted verbatim into
      `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` todo 1 (status: draft,
      `Source: issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md todo 1`), drafted by
      an earlier same-day `/ag-closeout-audit tradfi` pass. Not reclassifying `assigned_vm` here — that would risk a
      double-dispatch once batch12 flips `active`. Fix is citation-only; leaving `assigned_vm: NA`.)**
- [ ] [DATA] P3. Once the floor fix ships, relaunch the CBOE Treasury-INDEX launcher
      (`launch-tradfi-bf-cboe-indices-ohlcv-24h.sh`) with `--start-floor 2000-01-01` to backfill the 2000-2020-06 window
      that this bug currently blocks, and verify real captured coverage in the manifest for all 4 pre-2018 tenors. Repo:
      market-tick-data-service / deployment-service. **(na-eligibility-audit 2026-08-10, tradfi tranche, dispatch
      agt-a70469): KEEP-NA-STALE (already-duplicated) — extracted verbatim into
      `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` todo 2 (status: draft, same Source citation as above, todo
      2). Same reasoning — citation-only, `assigned_vm: NA` unchanged.)**

## Progress Log

- 2026-08-09: doc created during `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1
  (data_engineering worker, slot 17). Root-cause `_resolve_source` bug (separate, already fixed —
  `market-tick-data-service@af2c53ce`) confirmed working for post-floor (~2020-06+) CBOE dates; this floor-granularity
  gap is the reason full 2000-history coverage isn't achievable yet even with that fix shipped.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:300c26b85b568267]:
  **KEEP-NA-STALE (already-duplicated), first audit pass.** Both open todos (Phase-1 classifier initially flagged as a
  clean whole-doc RECLASSIFY candidate — no `[OPERATOR]` tag, no gate, a definitive already-decided implementation
  approach) are independently confirmed extracted verbatim into `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md`
  (status: draft, its own `Source:` citations name this doc's todo 1/todo 2 exactly), drafted by an earlier same-day
  `/ag-closeout-audit tradfi` pass -- see the per-checkbox citations above. Declining to flip `assigned_vm` to avoid a
  double-dispatch once batch12 activates; fix is citation-only.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA-STALE (already-duplicated),
  re-confirmed.** Both todos' citations to `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` remain accurate (now
  `status: active`; its todo 1 is `[x]` done, todo 2 still open). **Noted, not edited**: batch12's todo 2 text now
  carries a 2026-08-10 operator decision narrowing the relaunch scope to `--start-floor 2018-01-01` ("2018 onward is
  sufficient"), tighter than this doc's own todo 2 text (`--start-floor 2000-01-01`) — the batch doc is the live
  dispatch vehicle and its narrower text controls; this doc's stale wording is citation-only pointer text, not
  independently executed, so left as-is rather than editing a doc whose content isn't the dispatch source of truth.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) — added `engine/orchestrator/__init__.py`
  (market-tick-data-service), the file the doc's own body names as `is_venue_available()`'s home and the actual fix
  target of the still-open P3 relaunch todo; the 2 codex entries re-verified, unchanged.
- **na-eligibility-audit 2026-08-21**: KEEP-NA-STALE (already-duplicated), reaffirmed. Sole open todo's citation to
  `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` todo 2 remains current (status: active, operator-narrowed to
  `--start-floor 2018-01-01`). `assigned_vm` unchanged.
