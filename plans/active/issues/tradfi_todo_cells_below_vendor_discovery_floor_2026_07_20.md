---
doc_type: issue
title: "182,407 TRADFI todo cells sit below the vendor discovery floor and are permanently unfillable"
summary:
  182,407 TRADFI equity cells are counted `todo` on dates BEFORE the Databento venue discovery floor (XNAS.ITCH /
  XNYS.PILLAR carry nothing pre-2023-04-15). No launcher can ever fill them — the launchers already clamp START_FLOOR to
  that same UAC floor, correctly, so these cells are structurally unreachable rather than merely un-run. Counting them
  as `todo` overstates remaining work, permanently depresses the coverage %, and leaves dashboards showing a gap no run
  can ever close. They should be reclassified `expected_unattempted` / expected-absent so coverage reads honestly. The
  floor is already the SSOT in UAC (`VenueMapping.get_instrument_discovery_start`) — this is about making the
  DENOMINATOR agree with the clamp the launchers already apply.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-api, unified-trading-library]
scope: [engineer]
tags:
  [
    honest-coverage,
    expected-unattempted,
    discovery-floor,
    manifest,
    coverage-denominator,
    databento,
    backfill-readiness,
  ]
related:
  [
    tradfi_consolidated_closeout_2026_07_18,
    tradfi_captured_cells_zero_or_null_row_count_2026_07_20,
    tradfi_canonical_path_migration_design_2026_07_19,
  ]
created: 2026-07-20
priority: P2
parent_epic: tradfi_master
source: "Backfill-readiness manifest sweep, 2026-07-20"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# TradFi todo cells below the vendor discovery floor

## The measurement

**182,407** TRADFI cells are counted `todo` on dates strictly before their venue's Databento discovery floor:

| Venue  | Databento dataset | Discovery floor | Pre-floor data |
| ------ | ----------------- | --------------- | -------------- |
| NASDAQ | XNAS.ITCH         | 2023-04-15      | none exists    |
| NYSE   | XNYS.PILLAR       | 2023-04-15      | none exists    |

**RE-VERIFIED EXACTLY, 2026-07-20 (tick 26).** Independently re-derived on manifest snapshot T1 `2026-07-20T14:47:40Z`
and again at T2 `2026-07-20T15:09:03Z` (after the peer force-rebuild) — **182,407 on both**, so the figure is stable
across a full manifest rebuild. Per (venue, data_type), the breakdown the P1 todo below asks for is already available
from that run: **NASDAQ `ohlcv_1m` 97,475** (of 177,865 todo) · **NYSE `ohlcv_1m` 79,130** (of 143,947) · **CME
`ohlcv_1m` 5,802** (of 66,012, against the CME floor `2020-01-01`) · all other (venue, data_type) slices **0**. Total
todo 638,446 → **456,039 genuinely backfillable**. Note the CME 5,802 — the pre-floor class is NOT equity-only, so a
reclassification pass scoped to NASDAQ/NYSE alone would miss it.

**Interaction with the tick-26 ETA correction:** this 182,407 exclusion is unaffected by the `resolved[:cap]`
denominator-truncation fix. The truncation suppressed `expected_unattempted` rows for tickers ABOVE the cap on dates
AT-OR-AFTER the floor; the pre-floor cells counted here are a disjoint, correctly-enumerated set. Both corrections
therefore apply independently and are additive.

## Why they are permanently unfillable

The floor is already enforced end-to-end on the WRITE side, and correctly so:

- **UAC is the SSOT.** `VenueMapping.get_instrument_discovery_start(venue)` holds the earliest date a (venue, date)
  shard can produce records.
- **The launchers already clamp to it.** `ohlcv_clamp_floor_to_venue()` in
  `deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` raises `START_FLOOR` to the UAC floor (monotone max), so
  no sub-floor shard is ever launched.
- **That clamp exists because sub-floor VMs were measurably harmful, not merely wasteful.** VM
  `tradfi-bf-nyse-ohlcv-1m-2019-20260517-101526` ran 2 minutes, emitted 365 "No active venues" warnings, wrote 0
  parquets, self-deleted rc=0, and fired a false-CRITICAL `DP_VM_GONE_NO_CAPTURE` alert. The same bug bit the 2019 CME
  shards on 2026-07-16.

So the write path is right. The DENOMINATOR is what disagrees with it: these cells are counted as work-remaining that
the system is — correctly and permanently — never going to do.

## Why `todo` is the wrong state

`todo` means "not yet attempted, still fillable." These cells are "cannot exist at source." Conflating the two has three
concrete costs:

1. **Overstated remaining work.** 182,407 phantom cells inflate every remaining-work count and every backfill ETA
   derived from it — directly distorting the tradfi MVP-backfill critical-path planning these numbers feed.
2. **A permanently depressed coverage %.** The gap can never close, so tradfi coverage carries a fixed haircut that no
   amount of successful backfilling will ever lift.
3. **A standing false signal.** A dashboard gap that no launcher can close trains operators to ignore gaps — the exact
   alert-fatigue failure mode the workspace's actionable-only alerting rules exist to prevent.

`expected_unattempted` is the state the manifest model already has for precisely this: honest, materialised absence that
counts in the denominator as expected-absent rather than as outstanding work.

## Constraint on the fix

Per `codex/02-data/availability-manifest-and-data-status.md`, `expected_unattempted` is **materialised by the WRITER and
never re-derived** by readers. So the fix is a writer-side materialisation pass plus the enumerator learning the floor —
NOT a filter bolted onto the aggregator or the UI. A reader-side "just hide pre-floor cells" patch would violate the
shard-atom-identical-across-writer/manifest/status/gate/UI rule and would drift the moment another consumer reads the
manifest directly.

The floor must be read from UAC at runtime, never hardcoded per-venue — the launcher clamp already had to supersede
exactly such ad-hoc per-wrapper hardcodes.

## Todos

- [ ] [DATA] P1. **Re-measure and break down the 182,407** by (venue, data_type, year) so the reclass pass has an exact,
      verifiable worklist. Confirm each counted cell is genuinely strictly-before its UAC floor — an off-by-one at the
      boundary date would silently reclass a real, fillable day into expected-absent, which is the one dangerous failure
      mode of this change.
- [ ] [BACKEND] P1. **Teach the sentinel/enumerator path the discovery floor** so NEW pre-floor cells materialise as
      `expected_unattempted` at write time rather than as `todo`. Resolve the floor from UAC
      (`get_instrument_discovery_start`) at runtime; no hardcoded per-venue dates.
- [ ] [DATA] P1. **Run the corrective reclassification** over the existing 182,407 cells, writer-side. Verify the
      before/after counts and that tradfi coverage % moves by the expected amount and no more.
- [ ] [BACKEND] P2. **Assert the invariant in the aggregator's fairness checks** — no cell below a venue's UAC discovery
      floor may be in state `todo`. This is the regression guard that keeps the denominator and the launcher clamp from
      drifting apart again.
- [ ] [DATA] P2. **Sweep the other tradfi venues for the same class.** CBOE (2020-06-01) and CME (2020-01-01) have
      floors too; this measurement only counted the equity venues, so the real total is a floor, not a ceiling.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`; `expected_unattempted` is
  materialised by the WRITER, never re-derived.
- `codex/02-data/honest-coverage-model.md` — the two-layer coverage denominator this reclass corrects.
- `codex/02-data/tradfi-databento-sourcing-ssot.md` — § "Per-venue genesis / discovery-start floors".
- `codex/05-infrastructure/vm-launcher-runbook.md` — the launcher-side clamp this makes the denominator agree with.
