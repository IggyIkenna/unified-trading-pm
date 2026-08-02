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
- `skip`: **FAILED** (`reason=skip_signal_not_found`, 867.1s) -- **not yet root-caused**. The skip-if-fresh signal did
  not fire against the force-leg's own just-written test-bucket data. Per the `data-pipeline-check-is` skill's own
  caution ("read the VM run.log as ground truth, not the report verdict" -- the raw->canonical instrument-id migration
  can produce false-negative verdicts), this needs a direct read of the skip-leg VM's `run.log` for the actual
  freshness-check log line before concluding this is a genuine regression vs. a known false-negative class. NOT
  investigated yet this session.
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

- [ ] [DATA] P1. Investigate the `skip_signal_not_found` finding on API_FOOTBALL's skip-leg (real regression vs. known
      raw->canonical false-negative class) -- read the skip-leg VM's `run.log` directly, per the
      `data-pipeline-check-is` skill's own "read run.log as ground truth" guidance. (repo: instruments-service)
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
