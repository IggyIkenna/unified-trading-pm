---
doc_type: issue
title:
  "uts-prod-dp-meta-watchers OOM-killing every */15 run AT 32Gi/8cpu (2026-08-13 live) — the 08-09 32Gi bump did NOT fix
  it"
summary: >-
  Found 2026-08-13 while confirming the sibling `dp_exit_code_monitor_oom_signal9_2026_08_09.md` todo 1 (which that
  investigation DISPROVED for the exit-code job). `gcloud run jobs executions list --job uts-prod-dp-meta-watchers`
  shows the last 4+ executions (13:00/13:15/13:30/13:45Z) ALL failing with `"The configured memory limit was reached"`
  (OOM, signal 9) at the CURRENT live config of 32Gi/8cpu/900s — the config the 2026-08-09 fix bumped TO (16Gi→32Gi,
  same-day as this doc's sibling), explicitly to stop this exact failure class. The bump did not take. Cloud Logging
  `textPayload:"signal 9"` confirms `uts-prod-dp-meta-watchers` is the dominant signal-9 producer today (every ~15 min
  since at least 09:05Z). Because the meta sweep never reaches end-of-sweep, `check_monitor_crons_fired` (DP-WATCHER-002
  cron-freshness) may also never run — meaning the exit-code cron's pause + stale sentinel may NOT be paging
  `DP_CRON_DID_NOT_FIRE`, a second blind-spot compounding this one. This is a separate live incident from the exit-code
  OOM premise (disproven) and from the overlap-storm doc (which asserted meta-watchers was "OOM-safe at 32Gi" — that
  claim is now FALSE).
status: closed
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [data-pipeline-monitors, meta-watchers, oom, signal-9, cloud-run-job, dp-vm]
related:
  - /plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md
  - /plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md
  - /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md
  - /codex/05-infrastructure/data-pipeline-alerts.md
created: 2026-08-13
author: slot 18 (infra worker, dispatched to confirm exit-code OOM history)
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-13
locked_since:
context_scope:
  [
    /plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md,
    /plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md,
    deployment-service/deployment_service/data_pipeline_monitors/_attempted_failed_index.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
source: >-
  Side-discovery during the 2026-08-13 slot-18 confirmation of
  `/plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md` todo 1. That task's Cloud Logging history sweep
  (`textPayload:"signal 9"`, 30d) surfaced that the ONLY job still OOM-crash-looping on signal 9 today is
  `uts-prod-dp-meta-watchers`, not the exit-code monitor. Executions list + live job describe confirm the OOM is
  happening at the post-fix 32Gi/8cpu config. The 08-10 overlap-storm doc's claim that meta-watchers was "still OOM-safe
  at 32Gi" is contradicted by live evidence.
---

# uts-prod-dp-meta-watchers OOM at 32Gi/8cpu (live, 2026-08-13)

> **ARCHIVED 2026-08-14** — all 3 todos done. Todo 1's `deployment-service@f425eb12b3` fix (filter to
> `RELEVANT_CAPTURE_STATUSES` before `.to_pandas()`) is live-verified: 3 consecutive `*/15` cycles (04:45/05:00/05:15Z)
> completed clean with zero `"memory limit was reached"` failures, `vm-census/meta-last-run.json` advanced each cycle,
> and `RenagTracker`/`MissTracker` persist blobs advanced at matching timestamps — see Progress Log. Durable
> memory-sizing lesson migrated to `/codex/05-infrastructure/data-pipeline-alerts.md` § "Fleet-monitor job memory
> sizing" before archival.

## What was found

While running the 30-day Cloud Logging signal-9 history sweep for the exit-code monitor (todo 1 of
`dp_exit_code_monitor_oom_signal9_2026_08_09.md`), the sweep showed the overwhelming majority of current `signal 9`
events belong to `uts-prod-dp-meta-watchers`, not the exit-code job:

- `gcloud run jobs executions list --job uts-prod-dp-meta-watchers` — last 4 executions all
  `Task ...-task0 failed with exit code: 0 and message: The configured memory limit was reached.` at
  13:00/13:15/13:30/13:45Z (2026-08-13).
- Live config: `spec.template.spec.template.spec.containers[0].resources.limits = {cpu: 8, memory: 32Gi}`,
  `timeoutSeconds: 900` — i.e. the 08-09 fix's target config (16Gi/4cpu → 32Gi/8cpu, shipped same-day per
  `data_pipeline_fleet_monitor_scheduler.tf`) is LIVE and STILL OOMing.
- Cloud Logging `textPayload:"signal 9"` (30d): `uts-prod-dp-meta-watchers` fires roughly every 15 min today (09:05Z →
  13:49Z, ~20 events); the only other signal-9 today is a single `uts-prod-instruments-service-sports-fixtures` (12:09Z)
  and on 08-09 the events were `uts-shared-deployment-api-*` (all DIFFERENT jobs, none the exit-code monitor).

## Why this matters

1. **The 08-09 32Gi fix failed.** The `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` re-nag fix and the 08-09
   32Gi bump were supposed to make the meta sweep complete; instead it still OOMs every run. Every `*/15` sweep dies
   before `.persist()` of `RenagTracker`/`MissTracker`, so the DP_RUN_MOSTLY_EMPTY re-nag dedup and the DP-LIVE-003
   miss-tracking may both regress to re-firing on every sweep (the exact duplicate-alert symptom the 2026-07-15 fix was
   built to prevent).
2. **Cron-freshness cross-check may be blind too.** `check_monitor_crons_fired` (DP-WATCHER-002) lives late in the meta
   sweep. If the sweep OOMs before reaching it, the stale exit-code sentinel (cron paused since 08-11) may NOT page
   `DP_CRON_DID_NOT_FIRE` — meaning the meta-watchers' own safety net for the OTHER monitors is down exactly when one of
   them (exit-code) is genuinely paused.
3. This contradicts the 08-10 overlap-storm doc's assertion that meta-watchers was "still OOM-safe at 32Gi" — that claim
   must be corrected (see Related doc; it's the same "fleet grew past the ceiling" class, now at 32Gi).

## Not yet done

- [x] [BACKEND] P1. ✅ Root-cause the live OOM at 32Gi/8cpu: profile the meta sweep's memory peak (which checker/read
      dominates — likely `check_high_attempted_failed`'s full-corpus manifest read, or the DP-LIVE-003 AWS-census /
      per-prefix VM list, or a multi-day Cloud-Run execution history). Fix the memory hog rather than bumping the
      ceiling a 4th time; candidates: stream/chunk the manifest read (precedent: the 08-10 defi-index streaming read),
      or cap the per-sweep retained working set. Repo: deployment-service. — deployment-service@f425eb12b3 (see Progress
      Log for the measured root cause + fix).
- [x] ✅ [SCRIPT] P2. **CONFIRMED (2026-08-14, slot 20)** — After the fix, live-verify: `uts-prod-dp-meta-watchers`
      executions complete (no `"memory limit was reached"`) for ≥3 consecutive `*/15` cycles AND
      `vm-census/meta-last-run.json` advances each cycle AND `RenagTracker`/`MissTracker` persist lands (end-of-sweep).
      3 consecutive clean executions confirmed via `gcloud run jobs executions list`: `kd4x6` (04:45:06→04:52:25Z,
      7m18.77s), `rcn57` (05:00:06→05:06:53Z, 6m47.39s), `9xrhn` (05:15:04→05:21:08Z, 6m3.72s) — all "Execution
      completed successfully", zero `"memory limit was reached"` (the prior 4+ executions 02:15-04:35Z all failed with
      that exact message, confirming the fix is what changed the outcome). Sentinel `vm-census/meta-last-run.json` read
      via `_gcs.read_monitor_last_run` advanced each cycle: `ts=2026-08-14T05:06:48Z` (after rcn57) →
      `ts=2026-08-14T05:21:02Z` (after 9xrhn), both `ok=True`. `RenagTracker`/`MissTracker` persist blobs
      (`vm-census/dp-renag-timestamps.json`, `vm-census/dp-miss-counters.json`) confirmed advancing at matching
      timestamps each cycle (05:06:48/05:06:47 and 05:21:02/05:21:01) via `list_files_with_metadata` — proves both
      trackers reach their end-of-sweep `.persist()` call rather than the sweep dying first. Repo: deployment-service
      (read-only verification, no code change).
- [x] ✅ [SCRIPT] P2. **CONFIRMED (2026-08-14, slot 11)** — answered from the exit-code doc's twin todo 4 (full evidence
      there, `dp_exit_code_monitor_oom_signal9_2026_08_09.md`). Summary: `DP_CRON_DID_NOT_FIRE::exit-code` DID fire
      correctly through 08-11T01:11Z, then went silent after one last alert at **08-12T19:05:30Z** (3683m/61.4h stale) —
      a real detection gap, but attributable to THIS doc's own OOM incident (meta sweep dying before reaching
      `check_monitor_crons_fired`) rather than a separate bug. No further action needed here beyond this doc's own
      already-shipped fix (`deployment-service@f425eb12b3`, todo 1) + its live-verify todo 2 above (which will also
      re-confirm `check_monitor_crons_fired` reaches completion again). Repo: deployment-service.

## Progress Log

- 2026-08-14 (slot 20): Closed todo 2 (live-verify) — full evidence in the todo itself above. 3 consecutive clean `*/15`
  cycles (04:45/05:00/05:15Z start times) with sentinel + RenagTracker/MissTracker persist all advancing. Every todo in
  this doc is now done and unlocked — archiving per the 6-step ritual
  (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): migrated the durable memory-sizing lesson
  (`.to_pandas()` full-materialization anti-pattern + current live resource configs for all 3 fleet-monitor jobs) into
  `/codex/05-infrastructure/data-pipeline-alerts.md` (§ "Fleet-monitor job memory sizing" + an Anti-patterns bullet)
  BEFORE archival so the fact doesn't become archived-doc-only; corpus-grepped for referrers — only
  `dp_exit_code_monitor_oom_signal9_2026_08_09.md` cites this doc's path (in its `related`/frontmatter list; no specific
  fact/number cited from this doc there, so no further migration needed for that referrer). `git mv` to
  `plans/archive/2026_08/issues/` in this same commit (single-repo/mode-1 case — plan-of-record lives in this worker's
  own worktree — sanctioned per the archival SSOT's 2026-08-10 narrowing).
- 2026-08-13: Filed from the slot-18 exit-code confirmation sweep. Live evidence captured above; config 32Gi/8cpu/900s
  confirmed live via `gcloud run jobs describe`.
- 2026-08-14 (slot 14): Root-caused + fixed todo 1. **The 08-10 streaming-index fix (`_make_streaming_index_reader`,
  `cli.py`) was NOT the OOM driver — it was already live and does correctly stream/project columns.** The actual driver,
  confirmed by direct measurement against the live buckets (real `pq.ParquetFile` metadata + a bounded controlled read,
  not modeled): `check_high_attempted_failed` → `read_attempted_failed_cells` (`_attempted_failed_index.py`) calls
  `.to_pandas()` on the FULL unfiltered row count for every asset_group, and `.to_pandas()` materializes every projected
  string column as an individual Python `str` object regardless of relevance. Measured on the defi index specifically
  (159,036,875 rows / 6.8 GiB as of today, up from ~134M/~6GiB on 08-10): the Arrow table pre-`.to_pandas()` is ~14.3
  GiB, but the pandas conversion peaks ~40.9 GiB (257.3 bytes/row deep memory across 4 object-dtype columns), with the
  two co-resident during the conversion call plausibly peaking ~55 GiB total — comfortably over the 32Gi/8cpu ceiling on
  this ONE checker's ONE target (defi is 2nd of 5 AGs in `ASSET_GROUPS`, so the sweep reliably dies early, consistent
  with the observed every-run OOM). The `.astype(str)` calls downstream were investigated as the original hypothesis
  (per this doc's own "candidates" wording) and disproven by measurement — they're a near-no-op on already-object-dtype
  columns; `.to_pandas()` itself is the cost. Separately measured the `capture_status` distribution for defi
  (single-column pyarrow read, footer+data, ~3.1 GiB peak): of 159,036,875 rows, only 32,089,371 (`captured`) +
  7,874,973 (`attempted_failed`) = 39,964,344 (25.1%) are ever consumed by this checker's logic — the other 74.9%
  (`empty_confirmed` 78,597,415 + `expected_unattempted` 40,475,116) contribute to zero `AttemptedFailedCell` field and
  were being fully materialized for nothing. **Fix** (deployment-service@f425eb12b3): filter to
  `RELEVANT_CAPTURE_STATUSES = ("captured", "attempted_failed")` BEFORE the pandas conversion in both
  `read_attempted_failed_cells` read paths — inside pyarrow (`table.filter(...)`, pre-`.to_pandas()`) for the streaming
  path, and via a pandas `.isin()` mask right after `pd.read_parquet(...)` for the full-download fallback path. Cuts the
  row count ~4x with NO change to any computed `AttemptedFailedCell` field for a cell with real
  captured/attempted_failed activity — the filtered-out rows contributed nothing to `captured`, `attempted_failed`,
  `ratio`, `high`, `max_attempted_at`, or `stale_days` either before or after this fix. The one observable behavior
  change: a `data_type` with ONLY irrelevant-status rows (zero captured, zero attempted_failed) no longer appears in the
  returned cell list at all (previously appeared as a permanent zero-cell) — provably inconsequential since such a cell
  could never cross either HIGH threshold regardless (both require `attempted_failed >= 50`). Also investigated as
  ruled-out alternate hypotheses (kept here so a future OOM recurrence doesn't re-walk the same dead ends): the Cloud
  Run execution-history fan-out (`cloud_run_job_failure_watcher`/`consolidator_oom_watcher`/`check_cron_fired`, ~3
  separate unbounded `list_executions()` walks across ~60+ registered jobs, confirmed via live
  `gcloud run jobs executions list` — high-frequency jobs retain ~2000 executions each) is real and plausibly a genuine
  WALL-CLOCK/RPC-volume risk (matches the terraform comment's separately-documented 900s timeout history) but is NOT
  primarily a memory driver — Execution proto objects are modest and the reader only retains one scalar per job, not
  accumulated lists; DP-LIVE-003 (`missing_live_producer_watcher`) uses a bounded single-instance `describe_instances`
  lookup, not an unbounded AWS fleet census (the unbounded `list_ec2_census`/`list_batch_census`/etc in `aws_census.py`
  are NOT called by the meta sweep at all). Todos 2/3 (live-verify + the exit-code cron-freshness cross-check) are
  separate follow-on todos below, now unblocked by this fix. Tests:
  `test_high_attempted_failed_irrelevant_capture_statuses_excluded` (fallback path),
  `test_streaming_index_reader_filters_capture_status_before_pandas` (streaming path) — both new, both green under
  `quality-gates.sh`. Evidence: deployment-service@f425eb12b3, `.qg_last_passed_sha` verified, ancestry verified on
  `origin/live-defi-rollout`.
- **context-scout 2026-08-14**: populated context_scope (4 entries).
- 2026-08-14 (slot 11, infra): Todo "confirm DP_CRON_DID_NOT_FIRE::exit-code during the pause window" — answered (full
  evidence in the twin todo on `dp_exit_code_monitor_oom_signal9_2026_08_09.md`, not duplicated here). Read
  `#data-pipeline-alerts` via `scripts/dev/slack-read-channel.py data-pipeline-alerts 132` (132h window,
  2026-08-08→2026-08-14, 12,599 messages) and filtered for `exit-code`. Detection worked correctly through 08-11T01:11Z
  (7 alerts, `last output` growing 914m→1170m), fired once more at 08-12T19:05:30Z (3683m/61.4h stale), then went silent
  for the remainder of the window despite the cron staying paused — the gap starts right in the middle of THIS doc's own
  live OOM incident, confirming the suspected mechanism (meta sweep dying before reaching `check_monitor_crons_fired`)
  rather than a distinct detection bug. No new issue doc filed.
