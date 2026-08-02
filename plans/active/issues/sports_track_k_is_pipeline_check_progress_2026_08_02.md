---
doc_type: issue
title: "Sports Track K (IS) pipeline_e2e_check progress tracker -- baseline checkpoint (2025-12-20) mid-run"
summary: >-
  Progress tracker for `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track K (IS) todo
  (`sports_consolidated_native_ao_extract-029`). The parent plan is exactly at its 1000-line hard cap
  (`check_line_caps.sh`), so a growing multi-checkpoint progress log lives here instead of inline in the plan -- this
  doc is the durable resume-state; the plan's own todo text is unchanged.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-pipeline-check-is, pipeline-e2e-check, progress-tracker, line-cap]
related: [/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md]
created: "2026-08-02"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
drift_direction: advance-code
assigned_role: data_engineering
depends_on: []
locked_by:
resolved_by:
source: "sports_consolidated_native_ao_extract-029, context-limit checkpoint (slot 11, 2026-08-02T19:20Z)"
---

# Sports Track K (IS) pipeline check -- progress tracker

## What this is

`sports_consolidated_native_ao_extract_2026_07_25.md`'s Track K (IS) todo asks for 3 dated checkpoints (baseline
`2025-12-20`, mid `2025-12-24`, final `2025-12-18`) of
`instruments-service/scripts/pipeline_e2e_check.py --asset-group SPORTS --day <D> --legs force,skip,live` across 7
sports venues (API_FOOTBALL, BETFAIR, FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT, UNDERSTAT) -- 21
force/skip/live legs per checkpoint, 63 total. Each leg launches its own VM and can take 10-15+ minutes (API_FOOTBALL
alone rate-limits at ~1 req/min per fixture endpoint across hundreds of fixtures). This is a genuinely multi-hour todo;
this doc tracks cross-session resume state so it isn't re-derived from scratch on every dispatch.

## Baseline checkpoint (2025-12-20) -- ORIGINAL status as of 2026-08-02T19:20Z (SUPERSEDED, see correction below)

Launched via
`GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/pipeline_e2e_check.py --asset-group SPORTS --day 2025-12-20 --legs force,skip,live --report-dir ../unified-trading-pm/plans/audit/results`
as a harness-tracked `run_in_background` process (not `nohup`) from `instruments-service/` in this slot's worktree.
Driver PID 3466458 on this host.

**Shard 1/7 (API_FOOTBALL)**:

- `force`: **PASSED** (917.8s, `Shard completeness OK: 8/1 venues written for date=2025-12-20`, wrote 26,877 records
  across 390 venues per the manifest writer's own summary line).
- `skip`: **FAILED** (`reason=skip_signal_not_found`, 867.1s) -- **ROOT-CAUSED 2026-08-02 (slot 9)**: read the skip-leg
  VM's `run.log` directly
  (`gs://deployment-scripts-central-element-323112/vm-logs/instr-backfill-sports-pchk-0802183841-s-a2a5-api-football/run.log`,
  227,944 chars). **This is a checker false-negative, NOT a real skip-logic regression** -- and NOT the raw->canonical
  instrument-id migration class this doc originally hypothesized. The actual mechanism: `run.log:23` logs
  `"date=2025-12-20: deferring pre-flight to per-league entity handlers (sports per-league mode; expected=[...])"`, and
  `instruments_service/engine/orchestrator/process_preflight.py:578-590` shows why --
  `_has_sports_per_league_in_scope = bool(set(expected) & _SPORTS_PER_LEAGUE_ENTITIES)` is true for API_FOOTBALL's
  `expected` set (FIXTURES_SCHEDULE/TEAMS/STANDINGS/etc., all in `_SPORTS_PER_LEAGUE_ENTITIES`), which unconditionally
  sets `is_fresh = False` at the coarse level and defers the real freshness decision to each entity handler's own
  `_should_skip_date_for_per_league` call -- so the top-level
  `"SKIP date=%s: all %d venues/entities already fresh in manifest"` line `pipeline_e2e_check.py`'s
  `contains_skip_signal` greps for (`pattern = f"SKIP date={day}: all "`) can **structurally never appear** in a
  per-league-mode sports run's log, regardless of whether skip actually worked. The per-league skip logic demonstrably
  DID work correctly this run: `run.log:915` logs
  `"Per-fixture pre-fetch skip: 499 (entity, fixture_id) pairs already in existing per-league parquets — skipping api_football calls (pass --force to re-fetch regardless)"`
  -- i.e. the skip-leg correctly avoided re-fetching the 499 pairs the force-leg had just captured, and only queued
  genuinely-new work (1603 - 499 = 1104 calls). **Since `_SPORTS_PER_LEAGUE_ENTITIES` covers ~15 entity types spanning
  nearly every sports data_type** (FIXTURES_SCHEDULE, PREDICTIONS, MATCHES, STANDINGS, TEAMS, INJURIES, FIXTURE_STATS,
  FIXTURE_EVENTS, FIXTURE_LINEUPS, PLAYER_STATS, XG, PLAYER_VALUES, SFI_PROGRESSIVE_STATS, WEATHER,
  ODDS_HORIZON_BUCKET), **this false-negative is NOT API_FOOTBALL-specific — expect `skip_signal_not_found` on the
  remaining 6 venues' skip legs too** (BETFAIR, FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT, UNDERSTAT),
  since each provider's `expected` set for SPORTS necessarily includes at least one per-league entity. **Do not spend
  time re-investigating this same symptom on other venues in this checkpoint matrix** -- cite this root-cause instead
  and move on; a real checker fix is tracked as its own todo below (properly scoped -- the fix needs per-provider-aware
  secondary signals, which is more than this investigation's scope and risks a worse failure mode, a false-POSITIVE skip
  verification, if rushed).
- `live`: **IN PROGRESS** at checkpoint time. VM `instr-backfill-sports-pchk-0802183841-l-a2a5-api-football`, launched
  `2026-08-02T19:08:52Z`, healthy (fresh heartbeat, log growing normally through the same
  teams/standings/stats/events/lineups/player-stats phase sequence the force-leg went through).

**Remaining for this checkpoint**: 6 venues (BETFAIR, FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT,
UNDERSTAT) x 3 legs each, not yet started.

## Baseline checkpoint (2025-12-20) -- CORRECTED status as of 2026-08-02T19:45Z (slot 13, [REVIEW] verification)

**The "6 venues not yet started" claim above (from the 19:20Z checkpoint) was STALE the moment it was written -- a
COMPLETE 21-leg report already existed on disk at that point**, produced by a DIFFERENT, earlier driver run
(`Started: 2026-08-02T13:33:14Z`, `Finished: 2026-08-02T15:35:00Z`, committed `unified-trading-pm@48ae74001` at
`2026-08-02T16:03:49Z` -- over 3 hours before the 19:20Z checkpoint above was written). The 19:20Z checkpoint's own
driver (PID 3466458, launched after 16:03) appears to have been a REDUNDANT re-run of an already-complete checkpoint,
launched without first checking for an existing report -- exactly the failure mode the updated Resume instructions below
now guard against. **The real, complete, already-shipped report is**:
`plans/audit/results/data_pipeline_e2e_check_is_2025_12_20.md` (`status: partial`, `total=21 passed=12 failed=9`).

Verified breakdown of the 9 failures (all 7 venues x 3 legs ARE accounted for in this report -- checkpoint 1's data
collection is DONE; only failure triage is incomplete):

- **6x `skip_signal_not_found`** (API_FOOTBALL, TRANSFERMARKT, SOCCER_FOOTBALL_INFO, UNDERSTAT, FOOTYSTATS skip legs) --
  root-caused in the Todos section below: checker false-negative (SPORTS per-league mode structurally never emits the
  coarse `SKIP date=...` line the checker greps for), NOT a real skip-logic regression. **KNOWN, already investigated --
  do not re-investigate.**
- **3x BETFAIR (force/skip/live, ALL legs)**: `no_parquet_at:.../venue=BETFAIR/` +
  `manifest_status_invalid:no_matching_row`. **This matches BETFAIR's ALREADY-DOCUMENTED
  `BLOCKED-CREDENTIALS`/zero-PROD-rows state** (see the parent plan's own progress log, slot-14 2026-08-01: "BETFAIR ...
  failed separately on `manifest_status_invalid:manifest_empty` -- consistent with its known
  BLOCKED-CREDENTIALS/zero-PROD-rows state"). **KNOWN, pre-existing gap, NOT a new finding -- do not re-investigate as
  part of this checkpoint's scope.**
- **1x OPEN_METEO skip**: `vm_run_not_successful:launcher_script_nonzero_rc=1` -- **NEW, UNEXPLAINED failure mode**,
  distinct from both the per-league false-negative class and the BETFAIR credentials gap (OPEN_METEO's force+live legs
  both PASSED normally, only its skip leg's launcher script itself exited non-zero). Not yet investigated -- new todo
  filed below.

**Currently-running duplicate VMs** (found live at 2026-08-02T19:40Z via
`gcloud compute instances list --filter="name~instr-backfill-sports-pchk"`):
`instr-backfill-sports-pchk-0802193055-f-a2a5-api-football` and
`instr-backfill-sports-pchk-0802193411-f-cab3-api-football` -- both API_FOOTBALL **force**-leg launches, i.e. BOTH
re-running a leg that ALREADY PASSED in the complete report above. This looks like a further round of the same
redundant-relaunch pattern (a later slot likely picked up the "complete the baseline" todo without checking for the
existing report first). Flagging here rather than unilaterally killing another slot's in-flight VM without full context
on who launched it or why -- whoever next touches this todo should check the existing report FIRST and terminate these
if confirmed redundant (SPOT VM billing waste -- `/vm-preemption-billing-waste-audit` territory).

**Net for baseline (2025-12-20): checkpoint's data-collection IS complete (21/21 legs ran, real report exists). Its 9
failures are FULLY accounted for except the 1 new OPEN_METEO `vm_run_not_successful` case.** This checkpoint should NOT
be re-run again -- only the OPEN_METEO investigation remains open for it.

## Mid (2025-12-24) and final (2025-12-18) checkpoints

**Confirmed NOT started** (verified 2026-08-02T19:45Z, slot 13): no `data_pipeline_e2e_check_is_2025_12_24.{md,json}` or
`data_pipeline_e2e_check_is_2025_12_18.{md,json}` exist anywhere under `plans/audit/results/`. This is the real
remaining work gating the parent plan's `-029` checkbox -- 2 of 3 checkpoints (42 of the 63 total legs) have not been
attempted at all.

## Resume instructions

1. **STOP -- before launching ANY VM for this todo, check for an existing report AND for already-running VMs first**
   (this exact step was skipped at least twice already, producing the redundant re-runs documented above):
   - `ls plans/audit/results/data_pipeline_e2e_check_is_<date>.md` for the target date -- if it exists with `status`
     other than a stub, READ IT before relaunching; a complete report means that checkpoint's data collection is DONE
     and only unresolved failure triage (if any) remains.
   - `gcloud compute instances list --filter="name~instr-backfill-sports-pchk"` -- if a VM matching your target day is
     already RUNNING, do not launch a duplicate; wait for it or investigate why it's slow instead.
2. As of 2026-08-02T19:45Z: baseline (`2025-12-20`) is DONE (report exists, complete 21/21 legs) -- do NOT re-run it.
   Only remaining baseline work is the OPEN_METEO skip investigation (todo below). Mid (`2025-12-24`) and final
   (`2025-12-18`) have NOT been run at all -- that is the real remaining work.
3. If a report exists but you still suspect it's stale/wrong, verify its `generated_at`/`Finished` timestamp against the
   most recent commit touching it (`git log -- plans/audit/results/<file>.md`) before trusting or discarding it.
4. Once mid + final are both run (with reports committed) and the OPEN_METEO investigation is resolved (or explicitly
   documented as out-of-scope, same as BETFAIR/the skip false-negative class), move to the flip step.
5. Once all 3 checkpoints are done, flip `sports_consolidated_native_ao_extract-029`'s checkbox in the parent plan
   citing all 3 report paths, and mark this doc `status: resolved`. **NOT DONE YET as of 2026-08-02T19:45Z (slot 13) --
   2 of 3 checkpoints have not been run; the flip todo below was picked up prematurely and is being returned to the
   queue rather than falsely flipped.**

## Todos

- [x] ✅ [DATA] P1. Investigate the `skip_signal_not_found` finding on API_FOOTBALL's skip-leg (real regression vs.
      known raw->canonical false-negative class) -- read the skip-leg VM's `run.log` directly, per the
      `data-pipeline-check-is` skill's own "read run.log as ground truth" guidance. (repo: instruments-service) --
      unified-trading-pm@(this commit), see "Baseline checkpoint" section above for full root-cause + evidence: checker
      false-negative (SPORTS per-league mode structurally never emits the coarse `SKIP date=...` line the checker greps
      for), NOT a real skip-logic regression; expect the same symptom on all remaining 6 venues.
- [ ] [DATA] P2. Fix `pipeline_e2e_check.py`'s skip-leg verification to recognize SPORTS per-league mode: any run whose
      `expected` entities intersect `process_preflight.py`'s `_SPORTS_PER_LEAGUE_ENTITIES` frozenset defers the coarse
      freshness check (`is_fresh = False` unconditionally at `process_preflight.py:583`), so the
      `f"SKIP date={day}: all "` pattern `contains_skip_signal` greps for (`pipeline_e2e_check.py:592`) can never match
      for these runs regardless of whether skip actually worked -- this makes `skip_signal_not_found` a permanent
      false-negative for the ENTIRE SPORTS asset_group's skip leg (not just API_FOOTBALL), since nearly every sports
      data_type is in that frozenset. Needs a per-provider-aware secondary signal (each entity handler logs its own
      "already captured, skipping" line with different wording -- e.g. API_FOOTBALL's
      `"Per-fixture pre-fetch skip: %d ... pairs already in existing per-league parquets"` -- footystats.py/sfi.py/
      transfermarkt.py each have their own call sites around `_should_skip_date_for_per_league` with their own log
      phrasing, not yet surveyed) before the checker can distinguish a genuine skip regression from expected
      per-league-mode behavior. Out of scope for the investigation above (root-causing ≠ safely fixing -- a rushed fix
      risks a false-POSITIVE skip verification, which is worse for data-correctness than today's honest fail-closed
      state). (repo: instruments-service)
- [x] ✅ [REVIEW] P2. Verify baseline (2025-12-20) checkpoint's true status before further dispatch -- **CORRECTED
      2026-08-02 (slot 13)**: the "6 venues remaining" claim was stale; a complete 21-leg report already existed
      (`plans/audit/results/data_pipeline_e2e_check_is_2025_12_20.md`, 12/21 passed). Baseline data-collection is DONE;
      see "CORRECTED status" section above for the full failure breakdown. (repo: unified-trading-pm)
- [ ] [DATA] P2. Investigate the OPEN_METEO skip leg's NEW `vm_run_not_successful:launcher_script_nonzero_rc=1` failure
      (baseline day=2025-12-20) -- distinct from both the known per-league skip-signal false-negative class and
      BETFAIR's known BLOCKED-CREDENTIALS gap (OPEN_METEO's force+live legs both passed). Read the skip-leg VM's
      launcher/run.log to find why the launcher script itself exited non-zero. (repo: instruments-service)
- [ ] [DATA] P3. Check the 2 currently-running duplicate VMs
      (`instr-backfill-sports-pchk-0802193055-f-a2a5-api-football`,
      `instr-backfill-sports-pchk-0802193411-f-cab3-api-football`, both API_FOOTBALL force-leg re-runs of an
      already-passed leg) -- confirm they're redundant against the existing complete baseline report and terminate if
      so, to stop further SPOT VM billing waste. (repo: instruments-service, operator/infra -- VM lifecycle)
- [ ] [DATA] P1. Run the mid (2025-12-24) checkpoint, same 7-venue force/skip/live matrix -- confirmed NOT STARTED
      (verified 2026-08-02, slot 13: no report file exists). (repo: instruments-service, skill-driven)
- [ ] [DATA] P1. Run the final (2025-12-18) checkpoint, same 7-venue force/skip/live matrix -- confirmed NOT STARTED
      (verified 2026-08-02, slot 13: no report file exists). (repo: instruments-service, skill-driven)
- [ ] [REVIEW] P2. Once all 3 checkpoints are done, flip `sports_consolidated_native_ao_extract-029` in
      `/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` citing all 3 report paths, and mark this doc
      `status: resolved`. **NOT YET ELIGIBLE (verified 2026-08-02, slot 13): mid + final checkpoints have not been
      run.** (repo: unified-trading-pm)

## Progress Log

- 2026-08-02T19:45Z (slot 13, [REVIEW] task `sports_track_k_is_pipeline_check_progress-005`, dispatched to flip the
  parent `-029` checkbox): verified ground truth before flipping anything, per this task's own craft (evidence-backed
  completion, never trust a self-report). Findings: (1) the 19:20Z checkpoint's "6 venues remaining" claim was ALREADY
  STALE when written -- a complete 21-leg baseline report existed 3+ hours earlier (`unified-trading-pm@48ae74001`,
  finished 15:35Z); the 19:20Z driver (PID 3466458) was a redundant re-run that didn't check for the existing report
  first. (2) Of the baseline's 9 failures, 6 are the known skip-signal false-negative (already root-caused) and 3
  (BETFAIR, all legs) are the already-documented BLOCKED-CREDENTIALS gap -- but 1 (OPEN_METEO skip,
  `vm_run_not_successful:launcher_script_nonzero_rc=1`) is NEW and unexplained; filed as its own todo. (3) Found 2
  CURRENTLY RUNNING duplicate VMs re-launching the already-passed API_FOOTBALL force leg -- flagged as likely billing
  waste, filed as its own todo rather than unilaterally killing another slot's VM without full context. (4) Confirmed
  mid (2025-12-24) and final (2025-12-18) checkpoints have NOT been run at all -- no report files exist for either.
  **Did NOT flip `sports_consolidated_native_ao_extract-029`'s checkbox in the parent plan** -- this task's own
  precondition ("once all 3 checkpoints are done") is false (2 of 3 never run), so flipping it now would be a false
  completion claim. Corrected the stale "Baseline checkpoint" / "Resume instructions" sections above so future pickers
  don't repeat the redundant-relaunch mistake. Returning the flip-todo to the queue via `/skip-current-task` rather than
  falsely completing it.
- 2026-08-02T19:20Z (slot 11, data_engineering): filed this tracker as a context-limit checkpoint mid-baseline-run; see
  "Baseline checkpoint" section above for full state. Background VM continues independently of this session.
- 2026-08-02 (slot 9, data_engineering): root-caused the `skip_signal_not_found` finding on API_FOOTBALL's skip-leg by
  fetching the skip-leg VM's `run.log` directly from
  `gs://deployment-scripts-central-element-323112/vm-logs/instr-backfill-sports-pchk-0802183841-s-a2a5-api-football/run.log`
  (via `unified_trading_library.download_from_storage`, not `gsutil` -- the interactive shell's `gsutil` creds were
  invalid on this host; the UTL client used the ambient service-account credential successfully). Verdict: checker
  false-negative, not a real regression -- see "Baseline checkpoint" section for the full mechanism (SPORTS per-league
  mode in `process_preflight.py` structurally defers the coarse freshness check for any run touching
  `_SPORTS_PER_LEAGUE_ENTITIES`, so `pipeline_e2e_check.py`'s `"SKIP date=... all "` grep can never match). No code
  changed this session (the actual checker fix is correctly out of scope for a root-cause investigation and is now
  tracked as its own P2 todo above, since a rushed fix risks a worse failure mode). Flipped this todo's checkbox
  accordingly. Did NOT touch the remaining checkpoint work (6 venues baseline, mid/final checkpoints, or the live-leg
  VM's current status) -- out of scope for this task.
