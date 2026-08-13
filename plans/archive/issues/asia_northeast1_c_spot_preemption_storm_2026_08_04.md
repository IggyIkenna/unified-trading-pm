---
doc_type: issue
title: asia-northeast1-c SPOT preemption storm — 151 preemptions/5h across sports/tradfi/cefi, ongoing
summary: >-
  Found while working `sports_af_full_entity_completion-003` (launch FIXTURE_LINEUPS after FIXTURE_STATS converges):
  relaunched FIXTURE_STATS (`af-backfill-20260804-004955`) and it was SPOT-preempted after only ~1.5 min
  (2026-08-04T00:51:21-32Z) — the THIRD preemption of this same entity's backfill in <24h, each one dying faster than
  the last (17min -> 6min -> ~1.5min). Checking the audit log for the broader picture: this is NOT an af-backfill-
  specific problem. `asia-northeast1-c` is in an active, sustained SPOT preemption storm — 151
  `compute.instances.preempted` events over the 2026-08-03T19:54Z..2026-08-04T00:54Z window (5h), hitting at least 3
  asset groups concurrently (sports `af-backfill-*`/`expected-universe-v2-sports-*`, tradfi
  `tradfi-bf-{nyse,nasdaq,cme,cboe}-ohlcv-1m-*`, cefi `cefi-aster-2026`), still firing as of the last check (3 events in
  the most recent 10-minute window). This is fleet-wide billing waste happening right now, not isolated to this campaign
  — flagging per the CLAUDE.md "regularly check every running VM for preemption ... billing waste" rule and the "big
  finding" escalation bar (affects 3+ asset groups' active backfills simultaneously).
status: resolved
nature: issue
asset_group: [sports, tradfi, cefi, prediction]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-preemption, billing-waste, spot-capacity, cross-cutting, big-finding]
related:
  [
    /plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md,
    /plans/archive/issues/af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-08-04
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  deployment-service@7a2b28f (sub-tick census fix), deployment-service@1861cbe (residual expected-universe-v2-sports
  preemption backoff)
source:
  [
    "sports_af_full_entity_completion-003 (slot 5), 2026-08-04 — found while re-verifying the FIXTURE_LINEUPS launch
    gate",
  ]
drift_direction: advance-code
context_scope:
  [
    deployment-service/scripts/vm/launch-api-football-backfill-vm.sh,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
  ]
---

# asia-northeast1-c SPOT preemption storm

## What I found

Working `sports_af_full_entity_completion-003`. Re-verified the FIXTURE_LINEUPS launch gate per the standing risk note
in the gating doc: singleton lock was free (no `af-backfill-*`/`af-audit-*` VM RUNNING), but FIXTURE_STATS still had not
converged (125/68,409 non-MVP shards captured via `census_fixture_stats_lineups_widening_volume_2026_07_31.py` —
essentially flat vs. slot 6's last check). Relaunched FIXTURE_STATS as `af-backfill-20260804-004955`
(`--entity FIXTURE_STATS 2020-06-06 2026-08-04`, safe idempotent resume, no `--force`) to keep the campaign moving,
matching the pattern already used twice by slots 4 and 6.

This VM was preempted almost immediately:

```
gcloud logging read 'protoPayload.methodName="compute.instances.preempted" AND protoPayload.resourceName:"af-backfill-20260804-004955"'
2026-08-04T00:51:32Z  .../instances/af-backfill-20260804-004955
2026-08-04T00:51:21Z  .../instances/af-backfill-20260804-004955
```

Launched at 00:49:55Z, preempted at 00:51:21Z — a ~1.5 minute lifetime. This is the **third** preemption of the SAME
entity's backfill in under 24h (`af-backfill-20260803-233053` lived ~16min, `af-backfill-20260804-001203` lived ~6min,
`af-backfill-20260804-002608` — status unconfirmed but also gone by this check, `af-backfill-20260804-004955` lived
~1.5min), each one dying faster than the last.

Checked whether this is af-backfill-specific (as the two prior slots suspected) or something broader — it's broader.
Full audit-log sweep of `compute.instances.preempted` in `asia-northeast1-c`:

- **Last 10 min**: 3 preemption events (storm is ONGOING as of this check, 2026-08-04T00:54Z)
- **Last 3h**: preemption counts by VM-name family — `expected-universe-v2-sports` (10), `af-backfill` (10), then 2 each
  for ~20 distinct `tradfi-bf-{nyse,nasdaq,cme,cboe}-ohlcv-1m-*` shards, plus `cefi-aster-2026` (2)
- **Last 6h** (2026-08-03T19:54Z..2026-08-04T00:54Z): **151 total preemption events**

This spans at least 3 asset groups' active backfills (sports, tradfi, cefi) concurrently, all in the same zone, over a
sustained 5-hour window that is still active. This reads as a genuine SPOT capacity crunch specific to
`asia-northeast1-c` right now, not a bug in any one launcher — every affected campaign is bleeding SPOT compute-minutes
to preemption with proportionally little forward progress while it lasts.

**Distinct from, but adjacent to,** `af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md` (already root-caused

- fixed: `af-backfill-`/`af-audit-` were missing from `_DATA_VM_PREFIXES`, so those VMs' preemptions were invisible to
  the auto-relaunch actuator). That fix addresses "preempted but never re-launched" — it does NOT address "gets
  re-preempted within ~2 minutes of every relaunch," which is what's actually blocking FIXTURE_STATS convergence right
  now. Even with working auto-recovery, a relaunch loop against an active capacity storm will keep failing
  near-instantly.

**Not yet checked** (out of this task's scope, flagging for the next investigator):

1. Whether the `af-backfill-`/`af-audit-` prefix fix (`deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`) is
   actually live in the deployed `uts-prod-dp-exit-code-monitor` Cloud Run job image yet (image tag is a floating
   `:latest`; did not confirm the image was rebuilt from a commit at-or-after that SHA) — if not yet deployed,
   af-backfill preemptions during this storm are STILL invisible to auto-recovery on top of the storm itself.
2. Whether this is a known/expected SPOT market condition for this zone/time-of-day (transient, will clear on its own)
   or a genuine anomaly worth a support ticket / zone-diversification response.
3. Whether other campaigns' launchers (tradfi/cefi) have working auto-recovery that IS successfully relaunching them
   through this storm (making the same near-instant-repreemption tradeoff, just less visibly since a fix already covers
   their prefix) — if so, af-backfill riding it out via the now-fixed auto-recovery (once confirmed deployed) may be the
   right posture rather than a code change.

## Why it matters

- **Active billing waste, right now**: 151 preemption events in 5h across 3 asset groups means each affected campaign is
  burning SPOT minutes with minimal net throughput for as long as the storm continues.
- **Business-goal-critical for sports**: the operator's explicit ask (`sports_af_full_entity_completion_2026_08_03.md`)
  is full AF entity completion to downgrade the API-Football subscription — FIXTURE_STATS (gating FIXTURE_LINEUPS and
  the eventual re-census) has now made ~0 net progress across 4 launch attempts and ~3 preemptions in <24h, entirely
  attributable to this storm once the auto-recovery gap is factored out.
- **Cross-cutting**: not fixable by continuing to patch the sports/af-backfill launcher alone — tradfi and cefi
  campaigns are hitting the identical capacity wall in the same zone at the same time.

## Recommended decision

1. Someone with Cloud Build access should confirm whether `uts-prod-dp-exit-code-monitor`'s deployed image already
   includes `c3594db647c25ae2656ba020e15d3f55a42bd179` (rebuild timestamp vs. commit timestamp) — if not, expedite that
   redeploy so auto-recovery is genuinely live for af-backfill/af-audit before the storm clears.
2. Re-check the preemption rate in a few hours — if it has genuinely subsided, no further action needed beyond the
   redeploy-confirmation above (transient SPOT market condition). If it is still elevated after a full day, this
   deserves a proper capacity/zone-diversification decision (e.g., an alternate zone for backfill VMs, or a scoped
   on-demand exception for entities on a hard business deadline) — that tradeoff is an operator call, not a worker
   unilateral decision, given the HARD RULE that backfill VMs default to SPOT.
3. Do NOT keep blind-relaunching FIXTURE_STATS on a tight loop while the storm is this active — each attempt is
   consuming real compute for ~1-2 minutes of useful work. The sports campaign issue doc's Progress Log will track when
   it's safe to try again.

## Todos

- [x] ✅ [SCRIPT] P1. ~~Confirm whether `uts-prod-dp-exit-code-monitor`'s deployed Cloud Run image includes
      `deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`~~ — **CONFIRMED DEPLOYED 2026-08-04**:
      `gcloud artifacts docker images list` shows a genuinely new `deployment-api` image digest (`sha256:1ba77ac3...`,
      distinct from the prior `sha256:bc0bc256...` build) created **2026-08-04T00:50:50Z** — AFTER the fix commits
      landed (`c301076` at 00:34:58Z, `c3594db` at 00:40:13Z). The job's `observedGeneration` bumped 121→122 in the same
      window, and `uts-prod-dp-exit-code-monitor-f27xh` (execution at 00:55:01Z) ran `EXECUTION_SUCCEEDED` on the new
      revision. The af-backfill/af-audit prefix fix is genuinely live. See "Additional finding" below for a SEPARATE,
      still-open gap this uncovered.
- [x] ✅ [SCRIPT] P2. ~~Once (1) is confirmed deployed, verify a real af-backfill preemption during this storm actually
      triggers `RelaunchPreemptedVm` end-to-end~~ — **PARTIALLY CONFIRMED, NEW GAP FOUND 2026-08-04**: a real
      af-backfill preemption occurred post-deploy (`af-backfill-20260804-004955`, preempted 00:51:21-32Z, ~10 min after
      the fix went live) but STILL did not trigger `RelaunchPreemptedVm` — not because of the prefix bug (that's fixed),
      but because the VM's ~1.5min lifetime never appeared in the monitor's OWN prior-tick census at all (see
      "Additional finding" below). Converted into a new todo below rather than re-opening this one, since the prefix fix
      itself IS verified working.
- [x] ✅ [SCRIPT] P2. ~~Re-check `compute.instances.preempted` volume in `asia-northeast1-c` after several hours —
      confirm whether the storm has subsided; note the outcome in this doc's Progress Log~~ — **RESOLVED
      2026-08-04T05:16Z (slot 5)**: the original CROSS-CUTTING storm (sports+tradfi+cefi simultaneously, 151 events/5h)
      HAS SUBSIDED — tradfi zero events for 94+ min (last 03:42:43Z), cefi zero for ~7h (last 22:07:17Z Aug-03),
      af-backfill/af-audit zero for ~3.9h (last 01:21:48Z). A SEPARATE, narrower pattern remains: the
      `expected-universe-v2-sports-*` VM family (sports asset-group's expected-universe backfill launcher) continues
      taking isolated preemption hits at a low steady rate (~1 every 2-25 min, still ongoing as of 05:16Z) — every
      single preemption event since 03:42:44Z has been this one VM family, none from tradfi/cefi/af-backfill. Read as a
      persistent, narrow SPOT capacity/ auto-relaunch-collision issue specific to that machine type, not a continuation
      of the zone-wide storm this doc was filed about — see Progress Log for the live-monitored evidence trail and a
      filed follow-up for the residual pattern (repo: deployment-service, none needed — informational finding, no code
      change required by this todo).
- [x] ✅ [SCRIPT] P2. ~~**NEW 2026-08-04** — `exit_code_fleet_monitor.sweep()`'s
      `terminated = [name for name in prior if     name not in running]` diff (`exit_code_fleet_monitor.py:565`)
      requires a VM to have appeared in a PRIOR tick's `running` census before its disappearance can ever be detected. A
      VM whose entire lifetime (launch → preemption) falls inside one ~5-min `dp_exit_code_monitor_cron` tick window is
      structurally invisible — it never enters `prior`, so it can never show up as `terminated` on any later tick
      either. Confirmed live: `af-backfill-20260804-004955` (launched 00:49:55Z, preempted 00:51:21-32Z, i.e. ~1.5min
      total) appears in ZERO monitor log lines across the 00:50:42 and 00:55:50 ticks that bracket its lifetime — not
      `verdict=`, not `reap_stale`, nothing. During an active preemption storm where VMs are dying in 1-2 minutes
      (faster than the 5-min tick), this makes the tick-based census structurally blind to a growing share of
      preemptions regardless of the prefix fix. Consider either (a) a shorter poll cadence during a detected storm, or
      (b) driving `running_vms` from a source that captures sub-tick churn (e.g. a Pub/Sub `compute.instances.preempted`
      audit-log sink instead of a periodic list-and-diff) (repo: deployment-service).~~ — **FIXED 2026-08-04**: went
      with (a), implemented as a bounded in-process re-sweep rather than a Cloud Scheduler cadence edit (the latter is
      an infra change outside this todo's scope). `cli.py`'s exit-code mode now re-sweeps at a 60s interval, still
      inside the SAME Cloud Run Job invocation, whenever a pass observes ≥2 PREEMPTED verdicts (storm evidence) — capped
      at 4 extra passes so the worst case stays under the 5-min gap to the next scheduled tick and the job's 900s
      timeout. A VM captured RUNNING on an intra-loop pass becomes visible as `terminated` on the NEXT pass even if it
      dies before the next external tick. Never triggers in `--dry-run`. 3 new unit tests cover storm-triggers-
      resweep-then-caps, below-threshold-sweeps-once, and dry-run-never-resweeps —
      `deployment-service@7a2b28f92bc6d1f684d6c4d715d21da3a68d3c0a`.
- [x] ✅ [SCRIPT] P3. ~~**NEW 2026-08-04** — investigate the residual `expected-universe-v2-sports-*` SPOT preemption
      pattern in `asia-northeast1-c` discovered while resolving the recheck todo above: distinct from the (now resolved)
      cross-cutting storm, this ONE VM family has taken isolated preemption hits at a low, non-zero, ongoing rate (~1
      every 2-25 min, ~11+ hits observed 03:47Z-05:16Z) while tradfi/cefi/af-backfill have all gone completely quiet in
      the same zone over the same window. Determine whether this is (a) a persistent machine-type-specific SPOT capacity
      constraint the launcher's auto-relaunch loop keeps colliding with (would argue for a relaunch backoff or alternate
      zone/machine-type for this launcher specifically), or (b) expected/ acceptable background churn not worth acting
      on. Check `expected-universe-v2-sports` launcher config (machine type, relaunch cadence) and whether it has
      working auto-recovery already absorbing this at acceptable cost (repo: deployment-service). **CORRECTION
      2026-08-04T06:03Z** (sports campaign monitoring loop): the "af-backfill completely quiet" premise no longer holds
      cleanly — relaunched `af-backfill-20260804-063845` at 05:38Z on the strength of 4+ hours of af-backfill quiet, and
      it was preempted at 05:41:34Z (~2 min lifetime) while the `expected-universe-v2-sports` pattern was still actively
      firing nearby (steady hits through 05:52:59Z). One data point, not conclusive, but it suggests the residual
      capacity pressure may not be perfectly isolated to the `expected-universe-v2-sports` name/launcher — worth
      checking machine type overlap (is af-backfill also `e2-standard-8`, same as this family?) as part of the
      investigation above, not just the launcher config. Full detail: `sports_af_full_entity_completion_2026_08_03.md`'s
      06:03Z entry.~~ — **RESOLVED 2026-08-04 (slot 5) — verdict (a), fixed**: confirmed via
      `gcloud compute instances list --filter='name~"^expected-universe-v2-sports-"'` — 48
      `expected-universe-v2-sports-*` VMs launched 2026-08-03T23:07Z-2026-08-04T06:30Z (one still `RUNNING` at check
      time), the large majority TERMINATED within 1-3min of creation, matching the doc's "isolated hit" pattern exactly.
      Root cause: this VM family comes from `launch-expected-universe-v2-historical-backfill-vm.sh` (the GATED one-time
      sports historical `expected_unattempted` backfill, floor 2020-06-06 — NOT the daily Cloud Run Job scheduler in
      `expected_universe_v2_scheduler.tf`, which can't be SPOT-preempted at all) — its sequential per-chunk retry loop
      retried a CONFIRMED preemption (`_was_preempted`) with **zero backoff**, `continue`-ing straight back into another
      launch on the same `e2-standard-4`/`asia-northeast1-c` SPOT pool it had just been reclaimed from. That answers the
      06:03Z correction too: `launch-api-football-backfill-vm.sh` (af-backfill) computes a dynamic default machine type
      that falls back to `e2-standard-4` (same as this family) when unset — real overlap, not two independent capacity
      pools, so the two launchers WERE colliding on the same constrained SPOT tier. Fixed by adding
      `PREEMPTION_BACKOFF_BASE_SECONDS`/`PREEMPTION_BACKOFF_MAX_SECONDS` (default 60s/600s, doubling per consecutive
      confirmed preemption of the same chunk, resetting once a launch reaches the enumerator — halt-safety
      `EXIT_STATUS=5` retries stay immediate, that's real progress hitting a write cap, not a capacity collision). 2
      new/updated shell-test cases cover the backoff message and the growth-then-cap behavior (17/17 pass).
      `deployment-service@1861cbe`, verified on `origin/live-defi-rollout`.

## Progress Log

- **2026-08-04 (slot 5)** — Filed while working `sports_af_full_entity_completion-003`. Confirmed the storm is broader
  than af-backfill (151 preemptions/5h across sports/tradfi/cefi, still ongoing). Did not attempt a further
  FIXTURE_STATS relaunch given the active storm — `skip-current-task`'d the sports campaign todo so it requeues once
  conditions improve.
- **2026-08-04 (slot 5, continued)** — Dispatched todo 1 of this doc. Confirmed the af-backfill/af-audit prefix fix
  (`c3594db647c25ae2656ba020e15d3f55a42bd179`) IS deployed to `uts-prod-dp-exit-code-monitor` (new image digest built
  00:50:50Z, job generation 121→122, execution succeeded at 00:55:01Z — all after the fix commits at 00:34-00:40Z).
  However, checking the monitor's actual logs across the tick before/after `af-backfill-20260804-004955`'s preemption
  (00:50:42 and 00:55:50) found it in ZERO log lines — the prefix fix alone did not make this specific preemption
  visible. Root-caused why: `exit_code_fleet_monitor.sweep()`'s
  `terminated = [name for name in prior if name not in running]` diff can only detect a VM that was captured as
  `running` in some earlier tick's persisted census (`load_census`/`write_census` via `CENSUS_BLOB`) — a VM whose full
  lifetime (this one: ~1.5min, 00:49:55→00:51:21Z) fits entirely inside one ~5-min tick window never gets recorded as
  `prior` before it's already gone, so it can never be diffed as `terminated` on any subsequent tick either. This is a
  genuine, SEPARATE gap from the already-fixed prefix bug — filed as a new P2 todo above. Given the active storm is
  producing VMs with 1-2 min lifetimes (faster than the 5-min tick), this gap is likely affecting more than just
  af-backfill right now. Flipped todos 1 and 2 above (prefix fix confirmed deployed; the "verify end-to-end" check
  surfaced this new gap instead of a clean pass).
- **2026-08-04 (slot 8)** — Working `sports_af_full_entity_completion-003` (6th dispatch). Quick datapoint, not the "few
  hours" recheck (too soon, todo below stays open): `af-backfill-20260804-015704` (FIXTURE_STATS) was preempted at
  01:04:30-41Z after a ~6.2min lifetime — storm confirmed still active as of this timestamp, no material change from the
  151-events/5h baseline. Did not attempt a further FIXTURE_STATS relaunch (5 attempts today, zero net progress).
- **2026-08-04 (slot 13)** — Working `sports_af_full_entity_completion-003` (7th dispatch). Bucketed
  `compute.instances.preempted` in `asia-northeast1-c` over the trailing 90 min into 10-min buckets: 1, 16, 32, 7, 7, 1,
  3, 6 — a genuine peak-then-taper shape (peak 32/10min at 00:10-00:20Z, down to 1-6/10min by 00:40-01:10Z), plus an
  11-min clean gap (01:06:55Z→01:18:08Z) immediately before I checked. Read this as real evidence of subsidence (not
  just a lull inside an ongoing storm) and, with the singleton lock free and FIXTURE_STATS still at 125/68,284 non-MVP
  shards (0.18%, unchanged), relaunched it as `af-backfill-20260804-011911` (safe idempotent resume, no `--force`) —
  **this was the wrong call**: preempted again at 01:21:36-48Z, ~2.5min lifetime, the **7th FIXTURE_STATS preemption
  today**. The zone-wide rate check immediately after (last 20 min: only 2 log lines, both this one VM's own
  preempt-start/preempt-end pair) shows the broader storm genuinely IS much calmer than the 00:10-00:20 peak — so this
  reads as one unlucky `e2-standard-8` capacity hit rather than a resumed broad storm, but it's still enough to keep
  FIXTURE_STATS from converging. **Revised recommendation for the next dispatch**: the zone-wide aggregate rate is not
  by itself sufficient evidence to green-light a relaunch of THIS specific machine type/entity — either wait for a
  longer clean window (this attempt only had ~11 min of quiet before I acted) or check `e2-standard-8`-specific SPOT
  capacity signals if that's exposed anywhere, before trying again. Did NOT attempt an 8th relaunch this session.
  `af-backfill-20260804-011911` never got far enough to write a `run.log` (confirmed via `gsutil stat` — no object
  exists), so nothing to add on the "does auto-recovery fire" question beyond what todo 2 above already found.
  FIXTURE_LINEUPS gate remains unmet; `skip-current-task`'d the sports campaign todo again.
- **2026-08-04T01:52Z (slot 11)** — First DIRECT dispatch of this todo itself
  (`asia_northeast1_c_spot_preemption_storm-002`) — all 3 prior touches (slots 5/8/13) reached this doc as a side-effect
  of the sports `FIXTURE_LINEUPS` task, not a dispatch of this specific recheck todo. **This todo's own bar is NOT yet
  met**: the doc was filed ~00:54Z, "several hours" means a recheck due no earlier than ~03:54-04:54Z — only ~58 min
  have elapsed. Ran the fuller analysis anyway (bucketed the ENTIRE storm timeline 23:00Z→01:50Z into 10-min buckets,
  not just a trailing-90-min window): `1,1,2,4, 16,32,7,7,1,3,6,·,2,2,2` (23:00→01:40, `·`=zero events at 01:10) —
  confirms the same peak-then-taper shape (peak 32/10min at 00:10-00:20Z) slot 13 already found, but extends it ~40 min
  further: the post-peak rate has settled to a **low but NONZERO** steady background of ~2/10min for the last 30 min
  checked (01:20, 01:30, 01:40 each = 2 events), not the extended clean gap that would support "genuinely subsided."
  Read as: the PEAK has clearly passed, but the zone has NOT returned to the pre-storm baseline (quiet) — this is
  exactly the ambiguous middle ground slot 13's own "revised recommendation" already flagged (zone-wide aggregate rate
  alone isn't sufficient to green-light a relaunch). **Checkbox stays UNFLIPPED** — the todo's own "after several hours"
  bar isn't met yet, and even the fuller data I do have doesn't cleanly support "subsided" either way.
  `skip-current-task`'d (reason_code=GATED, estimated_unblock_minutes≈120) rather than force a premature verdict;
  recommend the next dispatch of this specific todo not fire before ~03:54Z, and pull the FULL trailing window (not just
  since my 23:00Z start point) at that time.
- **2026-08-04T03:29Z** — Checked ~25min early (working the sports campaign's own monitoring loop, not a fresh dispatch
  of this todo) since my prior `gcloud logging read` query syntax was broken (`jsonPayload.event_subtype=...` returned 0
  results even over a 6h window with known events in range) — found the working filter other slots used
  (`protoPayload.methodName="compute.instances.preempted"`) cited in this doc's own earlier entry and re-ran it
  properly. **Finding: the storm did NOT taper toward subsidence — it had a fresh, SHARPER spike.** Minute-by-minute
  breakdown of the trailing 3h: quiet 00:30-03:06 (0-3 events/min, consistent with slot-11's "low background ~2/10min"
  read), then a sudden burst 03:07-03:20 (9, 1, 1, **20**, 2, 2, 6, 5, 1 events per minute — peak of 20 in the single
  minute 03:10, i.e. **more concentrated and higher-peak than the original 00:10-00:20Z storm's 32-events-over-10min**),
  then tapering to 2, 2 events at 03:22 and 03:28 (last event 03:28:45Z, ~30s before this check at 03:29:15Z — still not
  a clean window). 94 total preemption events in the trailing 3h. Did **not** attempt a FIXTURE_STATS relaunch — this is
  stronger evidence against subsidence than before, not weaker. **Recommendation**: treat 03:10Z as a new reference
  point for the "genuinely clean window" bar, not the original ~00:54Z filing time or the ~01:52Z low-background reading
  — a recheck immediately at the nominal ~03:52-04:54Z window would be measuring from pre-spike data if done using only
  the older entries above. Whoever does the next recheck should pull the FULL trailing window fresh (not rely on this
  entry's numbers going stale) and confirm at least 30-60 clean minutes measured forward from whatever the actual latest
  event turns out to be at check time.
- **2026-08-04 (slot 6)** — Direct dispatch of todo 3 (the sub-tick census-blindness gap). Read
  `exit_code_fleet_monitor.sweep()` + its `cli.py` call site: `running_vms` is populated once per tick from
  `_list_running_vms()` (Compute API `aggregated_list_instances`, RUNNING-only) and diffed against the persisted prior
  census — a VM whose entire lifetime fits inside one tick literally never gets a chance to be recorded. Considered
  driving detection from the Compute Operations API's `compute.instances.preempted` log instead (option b, already used
  per-VM by `preemption_op_checker`) but a fleet-wide time-windowed query needs GCP filter/ordering semantics I couldn't
  verify live within this task's scope, so implemented option (a) instead — NOT as a Cloud Scheduler cadence edit (infra
  change, out of scope for a `[SCRIPT]` todo) but as a bounded in-process re-sweep loop inside `cli.py`'s existing
  exit-code mode: on a pass with ≥2 PREEMPTED verdicts, re-sweep every 60s (cap 4 extra passes) within the SAME Cloud
  Run Job invocation, so a VM captured RUNNING on an intra-loop pass is visible as `terminated` on the next pass even if
  it dies before the next external 5-min tick. Hit the file's 930-line QG cap on first pass (931L) — trimmed the added
  comment block, landed at 920L. 3 new unit tests (storm resweeps-then-caps at `_STORM_MAX_RESWEEPS`, below- threshold
  sweeps once, `--dry-run` never resweeps); full `quality-gates.sh` green, sentinel verified against the commit SHA (ran
  QG before committing the first time — wrong order per RULES.md — recommitted then re-ran QG on the correct HEAD).
  Shipped `deployment-service@7a2b28f92bc6d1f684d6c4d715d21da3a68d3c0a`, verified on `origin/live-defi-rollout`. Todo
  flipped above. Did not touch todos 1-2 (already resolved) or the still-open recheck todo (separate,
  operator-judgment-timing scoped).
- **2026-08-04T04:14Z (slot 6)** — Direct dispatch of the recheck todo (`asia_northeast1_c_spot_preemption_storm-002`),
  auto-chained after todo 3 above. Per the 03:29Z entry's own recommendation, pulled the FULL trailing window fresh
  (`gcloud logging read 'protoPayload.methodName="compute.instances.preempted" AND resource.labels.zone="asia-northeast1-c"' --freshness=75m`)
  rather than trusting stale numbers: 03:04→04:14Z, 80 total events. Minute buckets: burst 03:07-03:20
  (9,1,1,**20**,2,·,·,·,2,6,5,1,8,1 — matches the 03:29Z entry's spike), tapering 03:22-03:32 (2,·,·,·,·,2,·,1,1,5), a
  genuine 9-min clean gap (03:33-03:41), 4 events at 03:42, a 4-min clean gap, 1 event at 03:47, then a **24-min clean
  window (03:48-04:11)** that looked like real subsidence — until, at the exact moment of this recheck, TWO fresh
  preemptions landed: `expected-universe-v2-sports-20260804-041142` (55s lifetime, preempted 04:12:37Z) and
  `expected-universe-v2-sports-20260804-041305` (68s lifetime, preempted 04:14:13Z) — both freshly-launched VMs
  preempted within ~1 minute of insert, i.e. live confirmation of the exact sub-tick pattern todo 3's fix above targets.
  **Verdict: still NOT subsided** — the storm is now intermittent (long-ish clean gaps broken by fresh isolated hits)
  rather than sustained-dense, but "confirm 30-60 clean minutes measured forward from the actual latest event" (the
  03:29Z entry's own bar) cannot be satisfied by a point-in-time check — the latest event is effectively "now."
  **Checkbox stays UNFLIPPED.** Clock reset to 04:14Z above (superseding the 03:10Z reference). `skip-current-task`'d
  (reason_code=GATED, estimated_unblock_minutes≈45) rather than force a premature verdict — recommend the next dispatch
  pull the full window fresh again no earlier than ~05:00Z and specifically check whether the clean-gap-to-isolated-hit
  pattern seen here (vs. the earlier sustained-dense bursts) continues to lengthen, which would be the actual subsidence
  signal.
- **2026-08-04T04:33Z** — Checked ~27min early (sports campaign monitoring loop) since the isolated-hit pattern slot 6
  flagged is cheap to re-sample. Directly answers slot 6's "does the gap lengthen" question: **no, not yet** — events at
  04:16, 04:24, 04:28, 04:32 (gaps of 8, 4, 4 min respectively), the last one just ~1 min before this check. Density is
  genuinely down an order of magnitude from the 03:07-03:20 burst (single isolated events vs. 20/min), but the gap
  length is bouncing around 2-8 min, not trending upward — still no clean window by the "measure forward from the latest
  event" bar. Did not attempt a relaunch. Not treating this as the due ~05:00Z recheck (too early, no todo flip) — just
  a cheap interim datapoint since it directly resolves the open question from the last entry.
- **2026-08-04T04:44Z-05:16Z (slot 5)** — Direct dispatch of the recheck todo itself. First pulled the full trailing
  window fresh (`--freshness=105m`, no `--order=asc` this time — an earlier attempt combining `--order=asc` with
  `--freshness` silently ignored the freshness bound and returned data from far outside the window, truncated
  misleadingly by my own `tail -200`; the correct call is default desc order + `--freshness`, 85 real events in the
  window). Minute-bucketed 03:04Z→04:33Z: confirms the 03:07-03:22 burst (peak 20/min at 03:10, matching the 03:29Z
  entry), taper 03:28-03:47, then isolated single-VM hits every few minutes 04:12-04:33 (matching the 04:14Z/04:33Z
  entries). Rather than defer again (this todo has now bounced through 5+ dispatches without a verdict), actively
  watched live via a bounded poll (checking for new `compute.instances.preempted` events every 5 min, target: 40 clean
  minutes since the latest event or a new event resetting the clock) from 04:44Z to 05:16Z (32 min of live observation).
  Result: **no clean 40-min window was reached** — new isolated events kept landing (04:56:46Z, 04:58:25Z, 05:01:32Z,
  05:03:26Z, 05:12:47Z), gaps between them ranging ~2-25 min, still bouncing rather than lengthening. BUT
  cross-referencing VM names resolved the real question the prior 4 entries couldn't: **every single preemption event
  since 03:42:44Z — with zero exceptions — has been `expected-universe-v2-sports-*`.** Zero tradfi events since
  03:42:43Z (94+ min clean at time of writing), zero cefi events since 22:07:17Z Aug-03 (~7h clean), zero
  af-backfill/af-audit events since 01:21:48Z (~3.9h clean). **Verdict: the original cross-cutting storm (the thing this
  doc was actually filed about — 3 asset groups hit simultaneously) HAS subsided.** What's continuing is a separate,
  narrower phenomenon confined to one VM family, which does not meet this doc's own definition of "the storm"
  (multi-asset-group, zone-wide). Flipped the recheck todo above on this basis and filed a new P3 follow-up todo for the
  residual `expected-universe-v2-sports` pattern rather than leaving it as an unflipped ambiguous checkbox or a separate
  issue doc (adjacent finding, same investigation, cheaper to track in this already-open doc). Good news for the sports
  campaign specifically: af-backfill (the FIXTURE_STATS entity blocking `sports_af_full_ entity_completion-003`'s
  FIXTURE_LINEUPS gate) has been preemption-free for ~3.9h — the original blocking condition for that campaign looks
  clear now, though a relaunch attempt is outside this todo's scope to make.
- **2026-08-04T06:07-06:10Z (slot 6)** — Side-effect finding while running
  `/data-pipeline-check-is --asset-group prediction --day 2026-08-02`
  (`prediction_consolidated_native_ao_extract_2026_07_25.md` todo 2, unrelated task). Extends the residual-pattern scope
  found beyond `expected-universe-v2-sports`: both KALSHI check-VMs
  (`instr-backfill-pred-pchk-0804060413-{f,s}-6969-kalshi`, `e2-standard-4` — a DIFFERENT machine type than the
  `expected-universe-v2-sports`/af-backfill family) were preempted before writing any `run.log`/`EXIT_STATUS` —
  force-leg at 06:07:32-44Z (launched 06:04:22Z, ~3.2min lifetime), skip-leg at 06:09:33-47Z (launched 06:08:15Z,
  ~1.3min lifetime) — confirmed via
  `gcloud compute operations list --filter="targetLink~<vm> AND operationType=compute.instances.preempted"` (both
  DONE/"Instance was preempted."), not a code defect. A concurrent POLYMARKET skip-leg VM
  (`instr-backfill-pred-pchk-0804060413-s-6969-polymarket`) also shows a `compute.instances. preempted` event
  (06:08:02-17Z) but its result stands as genuinely `passed` — the preemption landed after the VM had already written
  its manifest row + parquet (verified via the check's own GCS-artifact read, duration 221.5s matching a normal
  completion), consistent with `VM_SHUTDOWN_ON_COMPLETION=true` racing a preemption notice on an already-done VM rather
  than an in-progress kill. Trailing-30min zone-wide sample at 06:10Z: 5 events across 4 distinct VM families
  (`expected-universe-v2-sports` x2, `tradfi-bf-cme-ohlcv-1m-*` x2, `instr-backfill-pred-pchk-*` x4) — roughly 1
  event/6min, matching the doc's already-documented "low, ongoing, non-zero" residual rate, now confirmed to span at
  least 3 VM families / 2 machine types (not just `e2-standard-8` sports/af-backfill) and a 4th asset group
  (prediction). Retried the KALSHI force+skip pair once (single retry, per this doc's "do not blind-loop" guidance,
  given this is a P2 baseline-checkpoint task with no hard deadline, not a business-critical backfill) — outcome logged
  separately in the consuming task's own plan.
- **2026-08-04 (slot 5)** — Direct dispatch of the residual-pattern todo.
  `gcloud compute instances list --filter='name~"^expected-universe-v2-sports-"'` showed 48 VMs launched
  2026-08-03T23:07Z-2026-08-04T06:30Z (1 still `RUNNING`), the large majority `TERMINATED` within 1-3min — this VM
  family is `launch-expected-universe-v2-historical-backfill-vm.sh` (the gated one-time sports historical
  `expected_unattempted` backfill; NOT the daily Cloud Run Job scheduler, which can't be SPOT-preempted). Read its
  sequential per-chunk retry loop: the confirmed-preemption branch (`_was_preempted` → true) retried with ZERO delay,
  `continue`-ing straight back into another launch on the same `e2-standard-4`/`asia-northeast1-c` SPOT pool it had just
  been reclaimed from — verdict (a) from the todo's own framing, not (b). This also resolves the 06:03Z correction's
  open question: `launch-api-football-backfill-vm.sh` (af-backfill) computes a DEFAULT machine type that falls back to
  `e2-standard-4` too (same as this family) when unset — genuine overlap on one constrained SPOT tier, not two
  independent pools. Fix: `PREEMPTION_BACKOFF_BASE_SECONDS`/`PREEMPTION_BACKOFF_MAX_SECONDS` (60s/600s default, doubling
  per consecutive confirmed preemption of the SAME chunk, resetting once a launch reaches the enumerator — halt-safety
  `EXIT_STATUS=5` stays immediate-retry since that's real progress, not a capacity collision). 2 new/updated shell-test
  cases (17/17 pass, ~6s). Shipped `deployment-service@1861cbe`, verified on `origin/live-defi-rollout`. Added the
  general pattern (a launcher's own in-process retry loop needs backoff on confirmed preemption, distinct from the
  fleet-wide `RelaunchPreemptedVm` auto-recovery) to `/codex/05-infrastructure/spot-vms-for-backfill.md` so other
  launcher authors don't repeat the zero-backoff mistake. Every todo in this doc is now checked with no lock — archiving
  per the plan-completion-and-archival-discipline HARD RULE (6-step ritual: referrer paths updated corpus-wide, see this
  commit's sibling commits touching the 5 referring docs).
