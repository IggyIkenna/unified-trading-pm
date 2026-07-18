---
doc_type: issue
title:
  api_football enrichment backfill walks chronologically from coverage-floor and never reaches the pending tail within
  any survivable VM lifetime
summary:
  Found while dispatched to sports_p2_history_apifootball_2015_to_present-001's "Full-history enrichment phase" todo
  (already bounced 15-20+ times). Cross-checked per-VM manifest shards against the canonical index and found the
  af-backfill-* fleet walks strictly chronologically from the 2020-06-06 coverage floor, re-confirming already-resolved
  cells at ~2.2 dates/min (100% of one VM's 10,861 written rows already matched the canonical capture_status) — at that
  rate it would take ~16.7h/entity to ever reach the pending tail (~79% of which sits in 2026-06/07), which is the
  primary previously-undiagnosed reason this todo's many relaunches never closed the gate regardless of VM health. Filed
  an immediate-mitigation todo (narrow pending-cluster relaunch) and a systemic fix todo (manifest-aware date-jump in
  the backfill loop).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [api-football, backfill, efficiency, chronological-scan, manifest, sports, prune-dont-scan]
related:
  [
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
  ]
created: "2026-07-18"
parent_epic: sports_master
priority: P1
assigned_vm: planning
source: [sports_p2_history_apifootball_2015_to_present-001]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to `sports_p2_history_apifootball_2015_to_present-001` (Todo "Full-history enrichment phase"), the task's 20+
prior sessions (see that plan's Progress Log, entries from 2026-07-17T15:1xZ onward) have repeatedly relaunched the same
4-entity `af-backfill-*` fleet (FIXTURE_EVENTS/LINEUPS/STATS/PLAYER_STATS, `2020-06-06..2026-07-18`) and repeatedly
found the gate (`read_availability_index` → `expected_unattempted` pending count per data_type) essentially unchanged
across many hours and many relaunches — attributed so far to VM kills (zombie-watchdog false-positive, then a manually
agent-deleted fleet, both now fixed/guardrailed per `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`) and
to normal slow throughput.

**This dispatch found a third, distinct, and much more fundamental cause: the backfill walks every date in the window
STRICTLY CHRONOLOGICALLY from the coverage floor, re-verifying already-fully-resolved days at real cost, and would take
on the order of 16+ hours of uninterrupted runtime per entity to ever reach the genuinely-pending tail — far longer than
any relaunch has survived (or than any single dispatch session lasts).**

Evidence (this session, 2026-07-18 ~17:00-17:15Z):

1. The 4 VMs launched by slot-9 at 16:16-16:18Z (`af-backfill-20260718-16{1608,1641,1712,1740}`,
   FIXTURE_EVENTS/LINEUPS/STATS/PLAYER_STATS) were confirmed healthy and actively writing (`run.log` tails, fresh
   `PIPELINE_HEARTBEAT` timestamps) throughout this session — no kill occurred this time.
2. Ran the actual gate query (`read_availability_index`, `source==api_football`, per-entity coverage windows) twice, ~40
   min apart (17:03Z and 17:14Z, the second AFTER confirming a fresh consolidator merge had landed): **pending_fetch was
   byte-for-byte identical both times** — FIXTURE_EVENTS 1935, FIXTURE_LINEUPS 1925, FIXTURE_STATS 1893, PLAYER_STATS
   1172 — matching slot-8's original 07-17T15:20Z baseline and slot-11's 07-18T16:36Z read. Zero net movement despite
   ~50-60 minutes of 4 VMs actively writing rows.
3. Read the per-VM manifest shards directly (bypassing the consolidated index) for 2 of the 4 VMs:
   - `af-backfill-20260718-161608` (FIXTURE_EVENTS): 10,861 rows written since launch (~58 min in), covering
     **`date=2020-06-06` through `date=2020-10-10` only** — 127 distinct dates out of the ~2,225-day
     (2020-06-06..2026-07-18) window. Rate: ~2.2 days/minute.
   - `af-backfill-20260718-161740` (PLAYER_STATS): 9,108 rows, **`date=2020-06-06` through `date=2020-09-16`** — 103
     distinct dates. Same chronological-from-floor pattern, same order-of-magnitude rate.
4. Cross-checked all 10,861 FIXTURE_EVENTS rows this VM wrote against the (freshly-merged) canonical index by composite
   key (`date`, `league_id`, `venue`): **100% (10,861/10,861) already carried the IDENTICAL `capture_status`
   (`empty_confirmed` or `captured`) in the canonical index before this VM ever touched them.** Zero of this VM's writes
   this session resolved a previously-`expected_unattempted` cell. Every single row was a re-confirmation of
   already-done work.
5. At the observed ~2.2 days/minute chronological rate, closing the ~2,225-day window (to reach 2026-06/07, where slot-8
   already established ~79% of the FIXTURE_EVENTS pending mass actually sits) would take **~1,000 minutes (~16.7 hours)
   of uninterrupted per-VM runtime** — before the VM would even reach the first genuinely-pending date. No relaunch of
   this todo (across 6+ relaunches spanning 2 days) has survived anywhere near that long.

## Why it matters

This is the primary, previously-undiagnosed root cause of this specific todo's 15-20+ bounce cycle — NOT (only) VM
kills, NOT (only) slow API throughput, but the backfill's own date-iteration order. Every relaunch restarts from
`--start-date=2020-06-06` (the launcher's own coverage floor) and spends its ENTIRE runtime re-verifying years of
already-resolved history before it could ever reach the small, scattered pending tail — so no amount of "just relaunch
it again" will ever close this gate, regardless of how well the VM-kill issues (already fixed) are handled. This also
means every hour of the 4-VM fleet's compute (and a share of the shared `api_football` API-key daily quota) spent this
session, and in every prior relaunch, produced **zero** gate-relevant progress — a direct, large-scale violation of the
craft's efficiency north-star ("prune-don't-scan"; "treat every avoidable re-scan as a defect, not a detail").

Whatever "skip-if-exists" mechanism the per-day loop has (there is a `check_shard_freshness()` skip path referenced in
`instruments_service/cli/instruments_handler.py`) is not fast enough to matter here: each already-resolved day cost ~27
seconds of wall-clock (10,861 rows / ~127 dates ≈ 85 rows/date at the observed ~2.2 dates/min), the same order of
magnitude as doing real per-league work, not a cheap manifest lookup. The "skip" appears to avoid re-fetching from the
API but does NOT appear to fast-forward the date cursor across large already-done ranges.

This is likely NOT unique to this one todo — the exact same launcher (`launch-api-football-backfill-vm.sh`) and the same
per-day CLI loop are the standard mechanism for every api_football entity/history backfill in the sports pipeline, so
any other multi-year api_football backfill (past or future) is subject to the identical defect.

## Recommended decision

Two independent, non-conflicting fixes:

1. **Immediate mitigation (unblocks THIS todo without any code change)**: relaunch with a narrow `--start-date` computed
   from the actual pending-date distribution (e.g. from the gate query's per-date breakdown — slot-8 already showed
   FIXTURE_EVENTS pending concentrates ~79% in 2026-06/07 plus smaller 2024-12/2025-12 clusters) instead of the full
   `2020-06-06` coverage floor. A handful of narrow-window VMs targeting just the known pending clusters would close
   this gate in minutes, not hours. Not done in this dispatch — computing the exact per-entity pending-date list plus
   safely accounting for the shared `api_football` per-key rate budget across the ALREADY-running 4 wide-window VMs (the
   launcher's `allocate_rate_budget` split is computed per-launch-invocation from `--fleet-vms`, not dynamically shared
   across all currently-running VMs system-wide — adding more VMs without reducing the existing ones' share risks
   over-subscribing the shared daily/RPM cap) needs a moment of care by whoever picks this up next.
2. **Systemic fix (repo: instruments-service, prevents recurrence for every future api_football multi-year backfill)**:
   the per-day backfill loop (`instruments_service/cli/instruments_handler.py`, `check_shard_freshness()` skip path and
   whatever drives the outer day-by-day iteration) should read the manifest FIRST to compute the actual set/ranges of
   genuinely-pending dates within the requested window, and jump directly to those — not iterate every calendar day from
   `start_date` and rely on a per-day skip that still costs real wall-clock. This is the same "prune, don't scan"
   principle the manifest system is built around everywhere else.

- [ ] [DATA] P1. **Relaunch the 4-entity api_football enrichment fleet with narrow, pending-cluster-targeted date
      ranges** (not the full `2020-06-06` coverage floor) for `sports_p2_history_apifootball_2015_to_present-001`'s
      "Full-history enrichment phase" todo. Compute the exact pending-date list per entity from
      `read_availability_index` first; size `--fleet-vms`/rate split to account for any of the 4 wide-window VMs still
      running concurrently (or let those finish/be superseded — do not silently over-subscribe the shared api_football
      daily quota). (repo: instruments-service / deployment-service)
- [ ] [DATA] P2. **Make the api_football per-day backfill loop manifest-aware: jump across already-fully-resolved date
      ranges instead of iterating + skip-checking every calendar day** — root-cause fix in
      `instruments-service/instruments_service/cli/instruments_handler.py` (and/or wherever `check_shard_freshness()`'s
      caller drives the outer date loop). Add a regression test asserting that a backfill over a window where e.g. the
      first N-1 years are already fully resolved reaches the pending tail in O(pending days), not O(total window days).
      (repo: instruments-service)
- [ ] [DATA] P3. **Audit whether any OTHER long-window api_football (or other source) backfill in flight/recently-run
      has the same chronological-scan-never-reaches-tail shape** — this launcher/CLI pattern is shared, so any other
      multi-year single-entity backfill is a candidate. (repo: instruments-service)

## Evidence

- Gate reads: 17:03Z and 17:14Z, both `pending_fetch` = FIXTURE_EVENTS 1935 / FIXTURE_LINEUPS 1925 / FIXTURE_STATS 1893
  / PLAYER_STATS 1172 (identical).
- Per-VM shard reads:
  `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/af-backfill-20260718-161608.parquet` (10,861
  rows, dates 2020-06-06..2020-10-10) and `.../af-backfill-20260718-161740.parquet` (9,108 rows, dates
  2020-06-06..2020-09-16).
- Composite-key cross-check: 10,861/10,861 of the EVENTS VM's written keys already had the identical `capture_status` in
  the freshly-merged canonical index (0 net-new resolutions of previously-pending cells).
- `run.log` tails for all 4 VMs at 17:01-17:02Z: live, fresh `PIPELINE_HEARTBEAT`, zero Tracebacks — genuinely healthy,
  not stalled/killed.
