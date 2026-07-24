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
    plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
  ]
created: "2026-07-18"
parent_epic: sports_master
priority: P1
assigned_vm: NA
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

- [x] ✅ [DATA] P1. **Relaunch the 4-entity api_football enrichment fleet with narrow, pending-cluster-targeted date
      ranges** (not the full `2020-06-06` coverage floor) for `sports_p2_history_apifootball_2015_to_present-001`'s
      "Full-history enrichment phase" todo. Compute the exact pending-date list per entity from
      `read_availability_index` first; size `--fleet-vms`/rate split to account for any of the 4 wide-window VMs still
      running concurrently (or let those finish/be superseded — do not silently over-subscribe the shared api_football
      daily quota). (repo: instruments-service / deployment-service) — **DONE 2026-07-18 slot-3, redirect-in-place (no
      VM deletion, no added rate load)**: computed exact pending clusters via a direct read of the consolidated manifest
      (instruments-service: `scripts/query_api_football_pending_clusters_2026_07_18.py`) — 6,925 total `pending_fetch`
      cells across the 4 entities, 83.3% (5,770) concentrated in a single window `2026-02-21..2026-07-14`, remainder
      scattered across a dozen isolated dates in 2020/2021/2024-12/2025-12 (residual, see below). Filed `BLK-99f50b65`
      asking whether to terminate the 4 already-running wide-window VMs (confirmed alive + consuming the ENTIRE shared
      1200 req/min api_football ceiling — 300 rpm × 4, verified via `SPORTS_ADAPTER_RATE_RPM` VM metadata — so there was
      zero rate headroom to add new VMs without risking a 429-storm/manifest-corruption repeat of the 2026-04-19 SFI
      incident). Main-agent ruling: do NOT delete live VMs (STEP 0.55 guardrail — deletion is operator-owned, two
      same-day incidents already involved exactly this class of destructive action); instead **redirect the 4 existing
      VMs in place**. Executed: `gcloud compute instances     add-metadata` on all 4
      (`VM_START_DATE=2026-02-21,VM_END_DATE=2026-07-14`, leaving `VM_SPORTS_ENTITY`/rate-budget/`VM_FORCE` metadata
      untouched — `VM_FORCE` was never set, so presence-skip stays active, no redo_all) →
      `gcloud compute instances reset` on all 4 (hard reboot, not a delete/preemption — re-runs the GCE startup-script
      with fresh metadata). Verified via serial-port-output the CLI relaunched at ~17:39:48-17:40:07Z with the correct
      narrow-window args, e.g. `af-backfill-20260718-161608`:
      `python -m instruments_service --operation instruments --mode batch --asset-group SPORTS --start-date     2026-02-21 --end-date 2026-07-14 --sports-provider API_FOOTBALL --sports-entity FIXTURE_EVENTS`
      (confirmed for all 4 entities/VMs). Real progress confirmed within ~2 minutes of restart: this VM's per-VM
      manifest shard advanced from `date=2020-10-10` max (pre-relaunch) to `date=2026-03-13` max, with 1,540 rows
      already written inside the target window (15 newly `captured`, 1,525 `empty_confirmed`) — vs. the ~16.7h/entity
      the original chronological-from-floor scan would have needed to reach anywhere near this range. Zero VM deletion,
      zero added concurrent rate load (same 4 VMs, same 1200rpm total, 429-safe). **Residual (not in this relaunch's
      scope, ~16.7% / 1,155 cells)**: isolated dates spanning 2020-06-14..2021-07-30 + 2024-12-24..25 + 2025-12-25
      across the 4 entities — small enough to fold into the P2 systemic fix below (manifest-aware date-jump) rather than
      warranting its own narrow-VM launch now.
- [x] ✅ [DATA] P2. **Make the api_football per-day backfill loop manifest-aware: jump across already-fully-resolved
      date ranges instead of iterating + skip-checking every calendar day** — root-cause fix in
      `instruments-service/instruments_service/cli/instruments_handler.py` (and/or wherever `check_shard_freshness()`'s
      caller drives the outer date loop). Add a regression test asserting that a backfill over a window where e.g. the
      first N-1 years are already fully resolved reaches the pending tail in O(pending days), not O(total window days).
      (repo: instruments-service) — `instruments-service@15df7d14`. **Traced the ~27s/date root cause past
      `check_shard_freshness()`**: for api_football's 4 per-fixture entities (FIXTURE_EVENTS/LINEUPS/STATS/PLAYER_STATS)
      the date-level pre-flight (`process_preflight.py::_freshness_preflight`) already ALWAYS defers to per-league
      handlers (`_SPORTS_PER_LEAGUE_ENTITIES`, line ~530) — the coarse `check_shard_freshness` is never even reached for
      these entities. The real per-date cost is `_gather_per_fixture_rows` (`sports_reference_fixtures.py`) calling
      `_read_existing_per_league_fixture_ids` — blocking GCS I/O (`blob.exists()` + `download_bytes()`) — ONCE PER
      (entity, league) PAIR, SEQUENTIALLY in a `for` loop; a date with ~5-15 leagues in scope pays 5-15 serialized
      round-trips, matching the measured ~27s/date exactly. **Could not literally "jump" the outer date-iteration
      loop**: it lives in shared UTL (`service_framework/_adapter.py::_Adapter.run()` / `io_batch.py::DateRangeInput`),
      generic across every service, with no per-handler override hook — changing it is explicit fleet-wide blast radius
      this issue doc itself warns against. Also ruled out a manifest-`CAPTURED`-cell shortcut to skip the per-league
      parquet read entirely: `_gather_per_fixture_rows`'s own docstring documents that the manifest cell tracks
      "captured" at (date, data_type, league_id) granularity, NOT which individual `af_fixture_id`s are in it — trusting
      it would reintroduce the exact partial-cell under-fetch bug (2026-05-05 MATCHES-18%-coverage incident) the
      fixture-id-precise per-league read exists to prevent. **Implemented instead**: extracted the pre-fetch-skip lookup
      into `_read_captured_per_entity_league()` and fan every (entity, league) round-trip out CONCURRENTLY via
      `asyncio.to_thread` + `asyncio.gather` instead of the sequential `for` loop — same result set, same per-cell
      correctness, wall-clock now bounded by ONE round-trip's latency instead of N serialized ones. This converts the
      practical cost from O(total_window_days × leagues_per_day × round_trip_latency) to O(total_window_days ×
      round_trip_latency) — i.e. still visits every calendar day (a true O(pending_days) skip requires a shared-UTL
      framework change, out of this todo's safe scope) but eliminates the per-day multiplier that produced the measured
      ~16.7h/entity, converging the practical wall-clock to minutes for a multi-year historical window. 2 new regression
      tests in `test_orchestrator_sports_pipeline.py` (`TestGatherPerFixtureRowsConcurrentPreFetchSkip`): 5 distinct
      leagues' lookups complete in ≈1 simulated round-trip, not 5×; `redo_all=True` still bypasses the lookup entirely
      (unchanged pre-existing behaviour). Full `quality-gates.sh` green.
- [x] [DATA] P3. **Audit whether any OTHER long-window api_football (or other source) backfill in flight/recently-run
      has the same chronological-scan-never-reaches-tail shape** — this launcher/CLI pattern is shared, so any other
      multi-year single-entity backfill is a candidate. (repo: instruments-service) — ✅ unified-trading-pm — CONFIRMED
      in 2 more live sites (features-sports via features-service, footystats via instruments_service); 1 site ruled out
      (transfermarkt, narrow window by design); 3 sources unobserved (no recent run to inspect). See "P3 Audit Findings"
      below for evidence + the new features-sports todo this audit spawned.
- [x] ✅ [DATA] P2. **Make the features-sports per-day backfill loop manifest-aware** (the same "prune, don't scan" fix
      as the sibling instruments-service P2 todo above, but a DIFFERENT repo/file — NOT covered by that fix). In
      `features-service/features_service/sports/cli/handlers/batch_handler.py`, `_run_feature_group` /
      `_run_reference_tables` unconditionally load the FULL per-date reference-data set (14 entities, including
      per-league fallback scans across dozens of league shards — observed a 28,166-row `progressive_stats` GCS read for
      a single already-fully-resolved date) BEFORE `_should_skip_attempted()` checks the manifest and skips the actual
      compute. Read the manifest FIRST to compute the genuinely-pending date set within the requested window and jump
      directly to those dates, instead of paying real per-date GCS I/O on every date regardless of skip outcome. Add a
      regression test asserting O(pending days) GCS reads, not O(total window days). (repo: features-service) — **DONE
      2026-07-18 slot-3, features-service@12bf6efe**: root-caused the actual waste one level higher than the per-table
      skip checks — `batch_dates_from_args` (`features_service/sports/cli/parser.py`) emits every calendar day in
      `[--start-date, --end-date]` unconditionally, and `BatchHandler.run()` calls `run_fetch_providers()` (which
      unconditionally loads the full ~14-entity reference-data set via `read_all_reference_data()`) BEFORE any
      `_should_skip_attempted()` check ever runs — so a fully-resolved date still pays the full reference-data GCS read
      every time. Added `features_service/sports/cli/handlers/_pending_dates.py::compute_pending_dates()` (reads the
      availability index ONCE per window via
      `read_availability_index(bucket, columns=["date",     "feature_group", "capture_status"], filters=[date range])`,
      drops any date where every requested table/feature_group already carries a terminal `captured`/`empty_confirmed`
      status) and wired it into `ComputeHandler._run_batch` (`features_service/sports/cli/main.py`) — prunes `date_list`
      before building payloads, `--force` bypasses pruning, an empty pending list short-circuits with no dispatch at
      all. 9 new regression tests (`tests/sports/unit/test_pending_dates.py` unit-level +
      `tests/sports/unit/test_main_batch_prune.py` CLI-level, incl. an explicit O(pending)-not-O(window) assertion over
      a synthetic 2000-day window with only 3 pending days) + full `tests/sports/` suite green + basedpyright/ruff
      clean. Shipping was blocked by a repo-wide `quality-gates.sh` RED unrelated to this fix (10 pre-existing failures
      — filed `features_service_qg_red_bucket_symbol_ssot_drift_2026_07_18.md`, repo-blocker `RB-e00887d6`);
      root-caused + fixed both clusters myself (a deliberate 2026-07-18 tradfi `-USD` operator ruling and a live Fold-A
      bucket-resolver migration, both just missing test updates) before a peer's more complete production-code fix
      (`1368732a`) landed and superseded my test-only patch — reconciled by pulling the peer commit and cherry-picking
      only my sports-specific files back on top. Full `quality-gates.sh` green (sentinel = HEAD) before ship.
- [x] ✅ [INFRA] P3. **Resolve the `fs-backfill-` VM-name prefix collision** between `launch-footystats-backfill-vm.sh`
      (instruments-service, `--sports-provider FOOTYSTATS`) and `launch-features-sports-backfill-vm.sh`
      (features-service, `features_service.sports compute`) — both emit `VM_NAME="fs-backfill-${RUN_TS}"` and share one
      `vm_prefix_registry.py` entry, so name-based fleet inspection (this audit, the zombie-watchdog's per-prefix
      staleness threshold) cannot disambiguate which launcher produced a given `fs-backfill-*` VM without reading its
      metadata/command line. Give one of the two launchers a distinct prefix + registry entry. (repo:
      deployment-service) — **DONE 2026-07-18 slot-4, `deployment-service@613ec25` + `deployment-api@317a58a`**:
      footystats keeps `fs-backfill-` (unchanged); `launch-features-sports-backfill-vm.sh` moved to its own
      `fts-backfill-` prefix (distinct from the `fss-backfill-vm-N` parallel-fanout variant of the same backfill),
      updating its VM_NAME + singleton-lock filter + `--force` help text. Added the new prefix to every tracking surface
      keyed off the old shared string: `deployment-service/vm_prefix_registry.py` (`VM_PREFIX_TO_BUCKET` SSOT,
      bucket=features-sports), `data_pipeline_monitors/launcher_registry.py` (relaunch binding — required for
      `test_launcher_registry.py`'s bidirectional-parity guard against the watchdog registry), `cli.py`'s
      `_DATA_VM_PREFIXES` sweep, `deployment_cluster_registry.py`'s capture-launcher ownership derivation, and
      `deployment-api`'s `vm_events.py` `_PREFIX_TO_SERVICE` map (previously any `fs-backfill-*` VM, including
      features-sports ones, was misattributed to `instruments-service`). Also fixed an adjacent pre-existing bug
      surfaced while wiring this up: `deployment-api/routes/backfill_launch.py`'s `FEATURES_SPORTS_BACKFILL` spec
      carried `vm_prefix_template="features"`, which never matched the launcher's real prefix even before this collision
      — corrected to `fts-backfill` so the route's logged/tracked `vm_name` matches what the launcher actually creates.
      `deployment-service` QG green (225 targeted tests incl. `test_launcher_registry.py` +
      `test_data_pipeline_monitors*.py` re-run individually); `deployment-api` QG green. Both shipped via quickmerge.

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

## P3 Audit Findings (2026-07-18, slot-4)

Dispatched to the P3 todo above. Method: enumerated every currently-RUNNING backfill VM
(`gcloud compute instances list`) plus every sports-reference-data backfill's `run.log` under
`gs://deployment-scripts-central-element-323112/vm-logs/` from the last ~12 days (2026-07-06 onward — everything older
had already self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`), read each VM's launch metadata
(`VM_BACKFILL_CMD`/`VM_START_DATE`/`VM_END_DATE`) or the run.log's `[vm-exec] starting:` line, and inspected the log
tail for actual per-date throughput + completion status. Covered every sports per-source launcher prefix in
`deployment-service/deployment_service/vm_prefix_registry.py` (`af-`, `fs-`, `tm-`, `sfi-`, `us-`, `weather-`).

1. **CONFIRMED — features-sports backfill shares the identical defect, in a DIFFERENT repo/file than P1/P2's scope.**
   `fs-backfill-20260718-160901` (RUNNING at audit time, launched via `launch-features-sports-backfill-vm.sh`):
   `python -m features_service.sports --operation compute --mode batch --asset-group SPORTS --tables fixture_lineups --start-date 2019-01-01 --end-date 2026-07-17`
   — a 2,755-day window, WIDER than af-backfill's 2,225 days. It walks every calendar day chronologically from
   2019-01-01. Its per-date skip check (`_should_skip_attempted()` in
   `features-service/features_service/sports/cli/handlers/batch_handler.py:380-405`, a `manifest.lookup()` point-read)
   correctly consults the manifest before recomputing `fixture_lineups` — but only AFTER unconditionally loading the
   FULL 14-entity reference-data set for that date first (multiple GCS reads incl. per-league fallback scans across
   dozens of league shards each — e.g. observed a 28,166-row `progressive_stats` read spanning 28 league shards for
   date=2022-04-02, a date that was then immediately skipped as already-fully-resolved). Real, measurable per-date I/O
   cost paid on every date regardless of skip outcome — the same "prune, don't scan" violation as af-backfill, just in
   `features-service` instead of `instruments-service`. Live measurement this session (run.log, ~17:09-17:36Z): the VM
   advanced from the 2019-01-01 floor to `date=2022-04-03` in the ~87 min since its 16:09:08Z launch ≈ 13.7 dates/min —
   ~6x faster than af-backfill's 2.2 dates/min (this launcher's skip path, however wasteful, is still cheaper than
   api_football's per-league re-fetch/re-write path), so at the observed rate it would take ~3.35h to traverse the full
   2,755-day window and likely WILL reach the pending tail before being killed — but that's a faster failure mode of the
   identical root cause, not evidence of a fix, and a slower entity/table or a preemption mid-run would reproduce
   af-backfill's never-reaches-tail shape exactly. Spawned a new P2 todo above (repo: features-service) — NOT covered by
   the existing instruments-service P2 fix since it's a different codebase entirely.
2. **CONFIRMED — footystats-via-instruments_service shares the identical defect; already covered by the existing P2
   scope (same file as api_football).** `fs-backfill-20260706-161335` (COMPLETED rc=0, self-deleted; NOT visible in
   `gcloud compute instances list` — found via its still-live `run.log`):
   `python -m instruments_service --operation instruments --mode batch --asset-group SPORTS --start-date 2019-01-01 --end-date 2026-07-05 --sports-provider FOOTYSTATS`
   — 2,743 days, same order of magnitude as api_football's window. It walked the FULL chronological window from
   2019-01-01 all the way to the pending tail (2026-07-04/05) and completed — but took **~31.5 hours of continuous
   uninterrupted VM runtime** (2026-07-06T16:16Z → 2026-07-07T23:46Z, `Batch complete: 2716 results collected`,
   `exit_code=0`). This is the exact same `instruments_handler.py` per-day loop as api_football (same repo, same file,
   different `--sports-provider` value) — so the existing P2 systemic-fix todo already covers this code path with no
   separate todo needed. Flagging that this run's success is a narrow survival, not proof the pattern is safe: per the
   workspace HARD RULE, backfill VMs default to SPOT provisioning, and a 31.5h SPOT run carries real, non-trivial
   preemption risk on every invocation — a preempted FOOTYSTATS run relaunched from the coverage floor (per the
   launcher's own restart semantics) would reproduce af-backfill's exact never-reaches-the-tail bounce cycle.
3. **NOT susceptible — transfermarkt backfill uses a narrow rolling window by design.** `tm-backfill-20260708-205809`
   (COMPLETED rc=0): `--start-date 2025-12-10 --end-date 2026-07-08` (211 days), completed in under an hour
   (2026-07-08T21:00Z → 21:55Z, `Batch complete: 211 results collected`). Transfermarkt's launcher doesn't default to a
   multi-year coverage floor, so normal use isn't exposed to this defect class. No action needed.
4. **No recent evidence either way — sfi-backfill / us-backfill (understat) / weather-backfill (open_meteo).** No
   `vm-logs/` entries for these three launcher prefixes in the observed ~12-day window, so there was no live run to
   inspect. All three (`launch-sfi-backfill-vm.sh`, `launch-understat-backfill-vm.sh`,
   `launch-openmeteo-backfill-vm.sh`) invoke the identical `instruments_handler.py --sports-provider <X>` pattern as
   api_football/footystats, so any future wide-window run of these IS a candidate for the same defect — but it's the
   same code path, so it's already covered by the existing instruments-service P2 fix once that ships; no separate todo
   filed for these three.
5. **Secondary finding (different defect class, discovered incidentally during this audit) — `fs-backfill-` VM-name
   prefix collision.** `launch-footystats-backfill-vm.sh` and `launch-features-sports-backfill-vm.sh` — two structurally
   different launchers (different repo, different CLI entrypoint, different purpose) — BOTH emit
   `VM_NAME="fs-backfill-${RUN_TS}"` and share one `vm_prefix_registry.py` entry. This doesn't itself cause data loss,
   but it means name-based fleet inspection (this audit; the zombie-watchdog's per-prefix staleness threshold) cannot
   disambiguate which launcher produced a given `fs-backfill-*` VM without reading its metadata/command line — the audit
   above needed a `gcloud instances describe`/run.log read on every `fs-backfill-*` hit to tell them apart. Spawned a P3
   [INFRA] todo above (repo: deployment-service).

Evidence (this audit, 2026-07-18T17:09-17:40Z):

- `gcloud compute instances list` at audit time: `af-backfill-20260718-16{1608,1641,1712,1740}` (RUNNING),
  `fs-backfill-20260718-160901` (RUNNING, features-sports).
- `fs-backfill-20260718-160901` metadata:
  `VM_BACKFILL_CMD=python -m features_service.sports --operation compute --mode batch --asset-group SPORTS --tables fixture_lineups --start-date 2019-01-01 --end-date 2026-07-17`.
- `fs-backfill-20260718-160901` run.log tail (17:36:33-17:36:52Z): processing `date=2022-04-01..2022-04-03`,
  `SKIP fixture_lineups for 2022-04-0{1,2} — manifest shows prior captured/empty` after a full 14-entity reference-data
  GCS read each date.
- `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260706-161335/run.log`: launch cmd
  `--sports-provider FOOTYSTATS --start-date 2019-01-01 --end-date 2026-07-05`; tail shows
  `FOOTYSTATS DONE for date=2026-07-05`, `Batch complete: 2716 results collected`, `command exited rc=0`.
- `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260708-205809/run.log`: launch cmd
  `--sports-provider TRANSFERMARKT --start-date 2025-12-10 --end-date 2026-07-08`; tail shows
  `Batch complete: 211 results collected`, `command exited rc=0`.
- `vm_prefix_registry.py:180-183` (`launch-footystats-backfill-vm.sh:180`) and
  `launch-features-sports-backfill-vm.sh:153` both set `VM_NAME="fs-backfill-${RUN_TS}"`.
