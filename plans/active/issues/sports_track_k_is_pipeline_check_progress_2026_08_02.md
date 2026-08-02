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

## Baseline checkpoint (2025-12-20) -- status as of 2026-08-02T19:20Z

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

## Mid (2025-12-24) and final (2025-12-18) checkpoints

Not yet started.

## Resume instructions

1. Check for a still-running VM from this exact run before relaunching (avoid a duplicate/write-race):
   `gcloud compute instances list --filter="name~instr-backfill-sports-pchk-0802183841"` (or the current run's own
   timestamp-tagged prefix if a fresh run was launched since).
2. If the baseline run's driver process has exited, check whether it wrote the final report:
   `plans/audit/results/data_pipeline_e2e_check_is_2025-12-20.md` (+ sibling `.json`). If present, read it for the full
   21-leg verdict table (per the skill's own reporting step, the script prints the full report to stdout too -- check
   the driver log for that if the file write path was interrupted).
3. If no report exists and no VM is running, the driver process died mid-run -- relaunch the SAME command (idempotent
   per already-completed shard/leg is NOT automatic in this script; it does not skip already-passed legs on a fresh
   invocation, so a full relaunch re-runs shard 1's force+skip+live again -- accept this cost rather than hand-rolling a
   partial-resume flag that doesn't exist in the script).
4. Investigate the `skip_signal_not_found` finding (real bug vs. false-negative) before citing this checkpoint as fully
   green, regardless of how the remaining venues turn out.
5. Once baseline is fully green (or its gaps are documented), move to mid (`2025-12-24`) then final (`2025-12-18`) the
   same way.
6. Once all 3 checkpoints are done, flip `sports_consolidated_native_ao_extract-029`'s checkbox in the parent plan
   citing all 3 report paths, and mark this doc `status: resolved`.

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
- [ ] [DATA] P1. Complete the baseline (2025-12-20) checkpoint: 6 remaining venues x 3 legs, then write/finalize the
      report at `plans/audit/results/data_pipeline_e2e_check_is_2025-12-20.md`. (repo: instruments-service,
      skill-driven)
- [ ] [DATA] P1. Run the mid (2025-12-24) checkpoint, same 7-venue force/skip/live matrix. (repo: instruments-service,
      skill-driven)
- [ ] [DATA] P1. Run the final (2025-12-18) checkpoint, same 7-venue force/skip/live matrix. (repo: instruments-service,
      skill-driven)
- [ ] [REVIEW] P2. Once all 3 checkpoints are done, flip `sports_consolidated_native_ao_extract-029` in
      `/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` citing all 3 report paths, and mark this doc
      `status: resolved`. (repo: unified-trading-pm)

## Progress Log

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
