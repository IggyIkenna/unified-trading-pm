---
doc_type: issue
title: "Step 3 cross-data_type completeness capture (venue_data_types.yaml) is mis-scoped for a single AO dispatch"
summary: >-
  cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md's "Step 3 cross-data_type completeness capture per
  venue_data_types.yaml" todo (source: data_completion_to_100_all_ag_2026_06_21.md) was classified bounded/deterministic
  by the drafting audit, but direct investigation shows both halves of the work are genuinely open-ended: the
  MEASUREMENT mechanism already exists and is live (no code needed) but a real corpus-wide query already times out at 2
  minutes, and the actual CAPTURE ask (backfilling every non-trades data_type per venue across all 5 asset groups) is an
  unbounded, multi-AG, many-VM-hours operation — not a worker-determinable outcome for one ~1h dispatch.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, mis-scoped, data-completeness, venue_data_types, unbounded-read]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/issues/axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-15
author: claude-code (slot-5, infra craft, adopted backend_engineer scope for investigation)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: ["AO dispatch of cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md's Step 3 todo to slot 5, 2026-08-15"]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    market-tick-data-service/configs/venue_data_types.yaml,
    deployment-api/deployment_api/routes/batch_config_utils.py,
    deployment-api/deployment_api/routes/data_batch_processing.py,
    /plans/archive/issues/axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
drift_direction: advance-code
depends_on: []
---

# Step 3 cross-data_type completeness capture is mis-scoped for a single AO dispatch

## What I found

The batch13 todo reads: "Step 3 cross-data_type completeness capture the FULL expected data_type set per listed
instrument (not just `trades`), per `venue_data_types.yaml`" (source:
`plans/active/data_completion_to_100_all_ag_2026_06_21.md`). Investigated both halves of what "capture" requires:

**1. The measurement/completeness MECHANISM already exists and is live — no code change needed.**
`market-tick-data-service/configs/venue_data_types.yaml` (531 lines, spans CEFI/DEFI/TRADFI/SPORTS/PREDICTION, each
venue's declared `data_types` list) is already fully wired into the live dashboard completeness computation:
`deployment-api/deployment_api/routes/batch_config_utils.py::load_venue_data_types()` /
`get_expected_data_types_for_venue()` feed `data_batch_processing.py::get_data_status_turbo_impl()` (the "TURBO" data
status endpoint used by the real dashboard), which already compares actual captured data_types per venue against the
venue-specific expected set from this yaml — for `service="market-tick-data-handler"` (the raw-tick API alias), not just
the processed-candles service. This is NOT new/broken code; the "capture the full expected set, not just trades"
comparison the todo describes is already computed live, corpus-wide, per venue.

(Separately noted, NOT the same mechanism: `deployment-service/deployment_service/catalog.py` sets
`"use_venue_specific_data_types": True` only on the `market-data-processing-service` entry, not on
`market-tick-data-service` — but that flag has zero consumers anywhere in the repo (`grep` found only the one assignment
site). It's dead config on a separate, apparently-unused legacy CLI code path
(`deployment_service/cli/utils/data_status_checkers.py` reads a _different_ config, `venues.yaml`, TradFi-only) — not
the live mechanism the dashboard actually uses. Not worth fixing on its own; flagging so a future reader doesn't mistake
it for the real gap.)

**2. Actually querying the live mechanism for real numbers is itself unbounded/slow — confirms the class of gap a
sibling todo already filed today.** Attempted a direct in-process call to
`get_data_status_turbo_impl(service= "market-tick-data-handler", start_date="2026-07-16", end_date="2026-08-15", include_sub_dimensions=True, check_upstream_availability=False)`
(all 5 asset groups, no venue/data_type filter — the natural first measurement step) — it did not complete within a 120s
budget and was killed. This is the same failure class
`plans/archive/issues/axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md` already filed today for a sibling
MDPS-scoped axis-census call (that one root-caused to an unbounded full-bucket read + client-side filter where a
pushdown filter measured 8.6s for the same result). Did not further diagnose this specific call's root cause (would need
its own investigation of `query_specific_prefixes_for_asset_group`'s cost at `include_sub_dimensions=True` scale) —
filing as a follow-up rather than guessing.

**3. The actual "capture" ask, even once measured, is an unbounded multi-AG backfill — not a bounded worker task.** Even
with real gap numbers in hand, closing them means launching backfills for every non-`trades` data_type
(`book_snapshot_5`, `derivative_ticker`, `liquidations`, `options_chain`, `futures_chain`, etc.) per venue that declares
them, across all 5 asset groups — a many-VM, multi-day operation, not a single ~1h P2 dispatch. This contradicts the
AO-eligibility bar ("outcome DETERMINABLE by the worker alone, never an open-ended judgment/design call" —
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 / CLAUDE.md's plan-authoring rule) even
though the drafting audit classified it bounded/deterministic.

## Why it matters

Left as-is, this todo will keep getting re-dispatched, and every worker that picks it up either (a) times out on the
same unbounded measurement call and burns a turn re-discovering this, or (b) launches an ad-hoc partial backfill for
whichever venue/data_type it happens to pick first, with no cross-worker coordination — silent partial, uncoordinated
progress that no single plan tracks to completion.

## Recommended decision

1. Fix the `get_data_status_turbo_impl` / `query_specific_prefixes_for_asset_group` unbounded-read class once (tracked
   in `axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md`) so a real cross-AG completeness measurement is
   actually runnable.
2. Once runnable, run ONE bounded measurement pass per asset_group to produce real per-venue, per-data_type gap counts
   (not attempted here — blocked on step 1).
3. Turn genuine, non-trivial gaps into properly-sized, per-AG (or even per-venue) `assigned_vm: planning` backfill todos
   — each independently bounded/deterministic (launch VM X for venue Y / data_type Z, verify manifest counts) — rather
   than one umbrella "capture everything" todo.
4. This doc's own todo below (re-scope, do not re-attempt as-is) is `assigned_vm: NA` because steps 1-3 above are a
   judgment/sequencing call, not mechanical work.

## Todos

- [ ] [DATA] P2. Once `axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md`'s fix lands, re-run the
      `get_data_status_turbo_impl(service="market-tick-data-handler", include_sub_dimensions=True)` measurement above
      per asset_group and report real per-venue/per-data_type completeness gaps for non-`trades` data_types.
- [ ] [DATA] P3. From that report, draft per-AG (or per-venue) bounded `assigned_vm: planning` backfill todos for any
      genuine gaps found — do not re-open this todo's original umbrella scope.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:6b8c25824bd0d572]: KEEP-NA, valid -- Fresh issue explicitly filed to correct a prior drafting audit's mis-scoping of a batch13 AO todo. Both remaining todos are explicitly sequenced: todo 1 behind a sibling issue doc's unresolved fix (axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md's unbounded-read performance bug in get_data_status_turbo_impl), todo 2 behind todo 1's own output (a completeness report). The doc's own text states the umbrella capture ask is an unbounded, multi-AG, many-VM-hours operation, not a worker-determinable outcome.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 2 open todos, both explicitly sequenced: todo 1 behind a sibling issue doc's unresolved unbounded-read-performance fix (axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md), todo 2 behind todo 1's own future.
