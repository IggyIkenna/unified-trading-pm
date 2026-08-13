---
doc_type: issue
title:
  "sports manifest consolidator: rows_out static at 17090683 across >=5 consecutive real merges (23:49Z-00:49Z, 1h+)
  despite growing rows_in/dedup_dropped and confirmed live INJURIES VM writes — census reads may be stale"
summary: >-
  Cloud Logging shows `manifest-consolidator bucket=instruments-store-sports-prd-central-element-323112` genuine merge
  cycles (`error=-`, not the `error=locked` skip variant) reporting the EXACT SAME `rows_out=17090683` across 5
  consecutive real merges spanning `2026-08-09T23:49:05Z` -> `2026-08-10T00:49:04Z` (1h+), with `rows_in` climbing each
  cycle (17137532->17142139->17147899->17152507) and `dedup_dropped` climbing correspondingly
  (46849->51456->57216->61824) — i.e. every new input row is being deduplicated away as already-present, netting zero
  canonical growth. This overlaps a live INJURIES backfill VM (`af-backfill-20260809-222924`) actively writing NEW
  per-VM-shard content confirmed via both its own `[[VM_PROGRESS]] last_completed_date=...` log marker (monotonic real
  date advance, e.g. 2024-04-04->2024-09-13 in ~30min) and fresh per-VM-shard GCS object timestamps
  (`_index/per_vm/af-backfill-20260809-222924*`, latest update 01:21:19Z). A
  `census_all_af_entities_completion_2026_08_03.py` read taken across this window is essentially flat for INJURIES
  (needed=29,480, unchanged across 2 consecutive monitoring-loop ticks spanning ~50min) despite the VM's own progress
  marker showing substantial real advancement — **this pattern matches the already-RESOLVED
  `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` incident almost exactly (same symptom signature: static
  rows_out, growing dedup_dropped, live backfill VM confirmed writing) but that incident's root cause
  (check_shard_freshness's ODDS_API-sentinel collision silently skipping dates) was odds_api/date-freshness specific —
  this occurrence is for INJURIES (a different entity, different code path) so the same root cause is NOT assumed to
  apply without verification.** Additionally observed (secondary symptom, likely same underlying stall): in a 15-minute
  sample window (01:22:55Z-01:29:43Z) EVERY consolidator invocation attempt for this bucket returned `error=locked
  shards=0 rows_in=0 rows_out=0` — the lock was held continuously across that entire window before a new holder
  (`instance=1-c366fe97`) acquired a fresh lock at `01:30:54Z`; not confirmed whether this was a stale lock from a
  crashed holder or legitimate serialized contention, not investigated further (out of scope for the monitoring loop
  that found this).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [manifest, consolidator, data-correctness, sports, injuries, api-football, zero-growth, stale-read, P1]
related:
  [
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
created: 2026-08-10
author: claude-agent
last_updated: 2026-08-10
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  Found during the autonomous sports dual-fleet (INJURIES + odds_api) honest-coverage convergence monitoring loop
  (continuation of sports_all_vendor_honest_coverage_convergence_2026_08_07.md) while investigating why two consecutive
  INJURIES census reads were byte-identical despite confirmed live VM progress.
context_scope:
  [
    unified_trading_library/manifest_writer,
    instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py,
    plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
  ]
---

## What was found

Two consecutive `census_all_af_entities_completion_2026_08_03.py` runs, ~50 minutes apart, both reported identical
`manifest rows (post-floor, <=today): 16176107` and identical `INJURIES needed=29480` — despite the live INJURIES
backfill VM's own `[[VM_PROGRESS]]` marker confirming substantial real, monotonic forward progress in that same window
(2024-04-04 -> 2024-09-13). Cross-checked via Cloud Logging: the manifest consolidator for this bucket
(`instruments-store-sports-prd-central-element-323112`) genuinely ran multiple times in this window with
`success=True error=-` (real merges, not the `error=locked` skip path), but every one reported the exact same
`rows_out=17090683` while `rows_in` and `dedup_dropped` both climbed in lockstep — i.e. all newly-ingested input rows
are being deduplicated away as already-canonical, netting zero growth cycle over cycle.

## Why it matters

The `census_all_af_entities_completion_2026_08_03.py`/`census_fixture_stats_lineups_widening_volume_2026_07_31.py`
scripts (the ground-truth measurement tools for the whole sports AF-entity-completion campaign, including the INJURIES
backfill currently in flight) read the CANONICAL manifest index, not per-VM shards directly. If the consolidator is
stuck in this static-`rows_out` state, EVERY census reading taken during the stall window under-reports genuine progress
— a monitoring session trusting the census alone (without cross-checking the VM's own progress markers, as this session
did) would wrongly conclude the campaign has stalled when it has not.

## Precedent

`sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` documents the IDENTICAL symptom signature (static
`rows_out`, growing `dedup_dropped`, confirmed live backfill VM writing) for `odds_api` specifically, resolved
2026-07-30 by finding the consolidator itself was not at fault — the real cause was `check_shard_freshness`'s
ODDS_API-sentinel logic silently skipping already-"fresh" dates upstream of the consolidator, so the consolidator was
correctly deduplicating genuinely-duplicate content. **Whether the same root cause (or a structurally similar one, e.g.
an INJURIES-entity freshness-sentinel collision) applies here is NOT yet verified** — this doc only establishes that the
symptom recurred for a different entity; the investigation that distinguished "consolidator bug" from "upstream
freshness-skip bug" for the odds_api case has not been repeated for INJURIES.

## Root cause (2026-08-10, slot 14, data_engineering) — P1 todo

**Verdict: NOT the odds_api sentinel-collision bug class, and NOT a genuine new consolidator defect.** The static
`rows_out` window was a real (not stale) reflection of the canonical state during that window, and it self-resolved —
compounded by an unrelated, already-monitored rate-limit event on the same VM later in its run.

1. **Structurally, the ODDS_API-class collision cannot occur for INJURIES.** That bug depended on a foreign pipeline
   (MDPS) writing under the SAME `service_name` as the checking caller (MTDS) so a blind `venue`/`data_type` match
   collided across sources. INJURIES has exactly one producer fleet-wide — queried the current consolidated index
   (`_index/availability_index.parquet`, single read, not a new corpus walk) for every distinct
   `(service_name, source, venue)` combo with `data_type='INJURIES'`: **one row: `instruments-service` / `api_football`
   / `venue=''`, 955,848 rows.** No foreign `service_name` or `source` stamps this `data_type` anywhere in the bucket,
   so the collision precondition (two producers sharing a dedup-key match) is absent by construction.
2. **INJURIES never reaches the coarse `check_shard_freshness` path that had the odds_api bug anyway.** INJURIES is a
   member of `_SPORTS_PER_LEAGUE_ENTITIES`
   (`instruments-service/instruments_service/engine/orchestrator/process_preflight.py:178`) — the coarse date-only
   pre-flight is explicitly SKIPPED for it in favour of `_should_skip_date_for_per_league`
   (`instruments-service/instruments_service/engine/orchestrator/sports.py:416`), which scopes its freshness check to
   the EXACT `(service_name, date, data_type, league_id)` tuple — no blind venue/data_type OR-match, no cross-`source`
   blindness. This is the same exact-scoping shape the 2026-07-30 blast-radius audit already verified is safe for every
   other asset_group's non-sports callers.
3. **What actually explains the flat window**: Cloud Logging shows the "stall" was real but temporary — `rows_out` held
   at `17090683` for the 5 cycles cited (`23:49:05Z`->`00:49:04Z`), then genuinely GREW twice more: `17096317` at
   `02:31:30Z` (+5,634) and `17097852` at `03:03:35Z` (+1,535), before plateauing again through `04:53:19Z`. A
   static-forever stall would never recover on its own; a VM walking a wide date range that revisits
   already-fully-captured ground before crossing into a genuine gap produces exactly this on/off growth pattern.
   Corroborated directly: querying the same index for INJURIES `capture_status`, the entity is 97.7% `empty_confirmed`
   (935,223 of 955,848 rows) — i.e. almost every (date, league) combo genuinely has no injury data, so a wide sweep
   naturally re-confirms mountains of already-`empty_confirmed` rows (harmless, correctly deduped) while only rarely
   crossing a real gap.
4. **Separately, this specific VM (`af-backfill-20260809-222924`) hit an upstream rate limit and was already caught by
   existing monitoring** — Cloud Logging:
   `exit_code_fleet_monitor: af-backfill-20260809-222924 verdict=rate_limited exit_code=0 captured=0->0` at `04:26:10Z`,
   immediately followed by the VM's own shutdown sequence (`04:23:59Z` onward) and its disappearance from the live
   instance list. This verdict landed AFTER the cited stall window (23:49Z-00:49Z), so it explains the LATER plateau
   (03:19Z-04:53Z+), not the originally-reported one — but it confirms the fleet's existing `exit_code_fleet_monitor`
   already detects and terminates a rate-limited INJURIES backfill VM correctly; no new detection gap found.

**Conclusion for the doc's own premise ("census reads may be stale"): the census was NOT stale.** It accurately reported
zero canonical growth during a window where canonical growth was genuinely (if temporarily) zero. No code fix is needed
in `check_shard_freshness`, `_should_skip_date_for_per_league`, or the consolidator for INJURIES.

## P2 verdict (2026-08-10, slot 7, data_engineering) — the `error=locked` streak was a STALE lock, not contention

**Verdict: STALE lock from an ORPHANED holder.** The streak (01:22:55Z–01:29:43Z) was a stale `_index/consolidator.lock`
blob left by a Cloud Run consolidator execution (`6tx26`) that Cloud Run killed at its **1800s task timeout mid-merge**
— NOT legitimate serialized contention from concurrent live holders. The lock mechanism is **NOT defective** — the TTL
reclaim worked exactly as designed and the bucket self-healed. The recurring enabler is a **config mismatch** (task
timeout shorter than real merge duration) → tracked as a new P3.1 follow-up below.

### Evidence (Cloud Logging, `uts-prod-manifest-consolidator-instruments-sports`, asia-northeast1)

Lock config for this bucket: `CONSOLIDATOR_LOCK_TTL_SECONDS=2400`, `CONSOLIDATOR_STALL_ALERT_CYCLES=40`, job
`timeoutSeconds=1800` (verified live; tf value 1800 matches).

| time (UTC)            | execution     | event                                                                                                                                                                  |
| --------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 00:49:55              | `6tx26`       | `phase=lock_acquired` (lock blob `started_at=00:49:55`)                                                                                                                |
| 00:50:00              | `6tx26`       | `phase=duckdb_merge_start` (real merge 1)                                                                                                                              |
| 01:05:42              | `6tx26`       | `phase=duckdb_merge_done rows_out=17090954` — **real absorption** (+271 over prior 17090683)                                                                           |
| 01:05:55–57           | `6tx26`       | CAS-write retry re-reads canonical + shards, `duckdb_merge_start` again (merge 2)                                                                                      |
| 01:19:29              | `6tx26`       | `Terminating task because it has reached the maximum timeout of 1800 seconds` — **Cloud Run SIGKILL mid-merge-2; `finally: _release_lock` never runs → lock orphaned** |
| 01:20:20–32           | `6tx26` retry | `skipping cycle … fresh lock present` → `error=locked` → `exit(0)`                                                                                                     |
| **01:22:55–01:29:43** | every tick    | `error=locked` streak — lock age 1980s→2388s, all **< 2400s TTL** (still "fresh" from the orphan)                                                                      |
| 01:30:54.6            | `xzc5v`       | `clearing stale lock (age=2459.3s > TTL=2400.0s)` — TTL reclaim fires                                                                                                  |
| 01:30:54.8            | `xzc5v`       | `phase=lock_acquired` → real merge 01:31:02→01:51:35 (`rows_out=17091186`, +232) — **self-healed**                                                                     |
| 01:51:48–52           | `xzc5v`       | CAS retry → second `duckdb_merge_start`                                                                                                                                |
| 02:00:27              | `xzc5v`       | **`Terminating task … maximum timeout of 1800 seconds`** — SAME timeout-kill pattern repeats                                                                           |
| 02:10:57.9            | `86ghl`       | `clearing stale lock (age=2403.3s > TTL=2400.0s)` — repeats                                                                                                            |
| 02:10:58              | `86ghl`       | `phase=lock_acquired` → real merge 02:11:04 — repeats                                                                                                                  |

### Why it's the stale-lock branch, not contention

- Every streak tick hit the **same orphaned lock** (`started_at=00:49:55` from the dead `6tx26`). There was **no
  concurrent live holder** — `6tx26` was SIGKILLed at 01:19:29, ~3.5 min before the streak began, and no other execution
  acquired the lock between 00:49:55 and 01:30:54 (verified: lock_acquired events only at 00:49:55/01:30:54/ 02:10:58).
  This is the 2026-07-13 "lock-orphan blind spot" shape (SIGKILL bypasses `finally:`), here triggered by the **Cloud Run
  task-timeout kill** rather than OOM — the `phase=duckdb_merge_start` at 01:05:57 with no matching `merge_done` is the
  tell (a genuinely-finished merge always logs both).
- No OOM/SIGKILL/MemoryError logged on either execution — the kill was purely the platform's 1800s task timeout.
- The lock TTL (2400s) is deliberately > task timeout (1800s) per the tf design invariant ("a fresh lock can only belong
  to a still-legally-running execution"), and it worked: the orphan self-cleared at 01:30:54 (age 2459.3s > 2400s) and
  the next execution merged normally. The streak is just the _TTL−timeout = 600s_ window after a timeout-kill where the
  dead execution's lock still reads "fresh".

### Recurring enabler (this session: twice in ~1h)

`6tx26` (killed 01:19:29) and `xzc5v` (killed 02:00:27) BOTH died the same way: a single Cloud Run execution ran a real
merge (~15–20 min) **plus** a CAS-write retry re-merge, exceeding the 1800s task timeout, so Cloud Run killed a
legitimately-still-running merge and orphaned its lock. The 1800s timeout was sized for the bucket's 6–9 min merges (tf
comment) but this bucket now merges 72–75 shards / 17.3M rows_in in ~15–20 min per cycle. The consolidator lock logic is
correct; the fix is config (mirror defi's 3600s timeout + 4200s TTL). Filed as P3.1 below.

## Todos

- [x] ✅ [SCRIPT] P1. Determine whether INJURIES' `check_shard_freshness` path (or equivalent freshness-sentinel logic)
      has the same class of bug the odds_api investigation found (silently marking dates "fresh" that shouldn't be,
      causing the writer to re-emit rows identical to what's already canonical, which the consolidator then
      correctly-but-uselessly dedupes away) — or whether this is a genuinely new, INJURIES-specific consolidator issue.
      Repo: market-tick-data-service or instruments-service (wherever INJURIES' freshness-check path lives). —
      **RESOLVED, no code change**: neither. See "Root cause (2026-08-10)" above — structurally immune to the odds_api
      collision class (single producer, no foreign `service_name`/`source` collision possible), and the observed stall
      was a real, self-recovering artifact of a wide-range backfill VM re-scanning already-covered ground, compounded by
      an unrelated rate-limit termination the fleet monitor already caught correctly.
- [x] ✅ [SCRIPT] P2. Confirm whether the `error=locked` streak observed (01:22:55Z-01:29:43Z, every attempt in that
      window failed to acquire the lock) is a stale lock from a crashed/orphaned holder or legitimate serialized
      contention from concurrent consolidator invocations — check the lock file's held-since timestamp against the
      holder instance's actual liveness before assuming either. Repo: unified-trading-library (manifest_writer/
      consolidator lock logic). — **RESOLVED, stale lock from an ORPHANED holder; no UTL code change.** See "P2 verdict
      (2026-08-10)" above. Lock was `started_at=00:49:55` from execution `6tx26`, which Cloud Run SIGKILLed at 01:19:29
      at its 1800s task timeout mid-second-merge (CAS-retry), so `finally: _release_lock` never ran; the orphan stayed
      "fresh" (age < 2400s TTL) through the whole streak, and was TTL-reclaimed at 01:30:54 (age 2459.3s) — the next
      execution merged normally. No concurrent live holder existed during the window (only lock_acquired events 00:49:55
      / 01:30:54 / 02:10:58). Lock logic works as designed; the recurring enabler (task timeout 1800s < real merge+retry
      duration) is a deployment-service config issue → P3.1.
- **[DOCS] P3. CANCELLED 2026-08-12 (/plan-reconcile) — conditional premise did not hold.** Original text: "If confirmed
  as a genuine, recurring consolidator defect (not just an upstream freshness-skip bug each time), consider whether
  `census_all_af_entities_completion_2026_08_03.py` and `census_fixture_stats_lineups_widening_volume_2026_07_31.py`
  should cross-check a live VM's own progress marker (e.g. `[[VM_PROGRESS]]`) against the canonical read and warn when
  they diverge, rather than silently trusting a potentially-stale canonical snapshot." The trigger condition is this
  same doc's own todo 1, resolved above as **"RESOLVED, no code change"** — the root cause was confirmed NOT a genuine
  recurring consolidator defect (structurally immune to the odds_api collision class; a self-recovering artifact of a
  wide-range backfill VM re-scanning already-covered ground). Since the premise never held, the conditional census
  cross-check enhancement was never triggered. If the census-vs-VM-progress cross-check is still wanted as
  general-purpose defense-in-depth independent of this specific (now-closed) incident, that is a fresh, unconditional
  proposal for the operator to scope — not a re-opening of this todo.
- [ ] [SCRIPT] P3.1. Bump the `instruments-sports` manifest-consolidator Cloud Run task timeout from 1800s to 3600s AND
      its `CONSOLIDATOR_LOCK_TTL_SECONDS` from 2400s to 4200s (mirroring the `market-data-defi` per-bucket override
      pattern) so a legitimately-running merge + CAS-retry re-merge (~15–20 min/cycle at current 72–75-shard /
      17.3M-rows_in working set) can no longer hit the 1800s task timeout and get SIGKILLed mid-merge, orphaning the
      lock and blocking the bucket for the TTL window (observed TWICE in ~1h on 2026-08-10 — `6tx26` killed 01:19:29Z,
      `xzc5v` killed 02:00:27Z; both left stale locks reclaimed only at 2400s TTL). Keep the "TTL > task timeout"
      structural invariant. Repo: deployment-service (terraform/gcp/manifest_consolidator_scheduler.tf) — deploy the
      per-bucket override like `market-data-defi`'s, then verify via Cloud Logging that the next long merge logs no
      task-timeout termination.

## Progress Log

- **2026-08-10 (slot 7, data_engineering)**: Resolved P2 — the `error=locked` streak was a STALE lock from an ORPHANED
  holder (`6tx26`, killed by the 1800s Cloud Run task timeout at 01:19:29Z mid-CAS-retry-merge; `finally: _release_lock`
  never ran; orphan stayed fresh under the 2400s TTL through the whole 01:22:55Z–01:29:43Z window and was reclaimed at
  01:30:54Z). NOT serialized contention — no concurrent live holder. Lock logic (UTL `manifest_consolidator.py`
  `_is_lock_fresh`/`_acquire_lock`/TTL) verified correct. Recurring enabler (same timeout-kill orphan struck `xzc5v`
  again at 02:00:27Z, <1h later) filed as P3.1 (deployment-service task-timeout + TTL bump). No UTL code change shipped
  — the lock worked as designed; the fix is config. Evidence via Cloud Logging (executions `6tx26`/`xzc5v`/`86ghl`,
  `Terminating task … timeout of 1800` + `clearing stale lock age>2400s` events) + live job env
  (`CONSOLIDATOR_LOCK_TTL_SECONDS=2400`, timeoutSeconds=1800).
