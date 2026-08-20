---
doc_type: issue
title:
  "uts-prod-dp-exit-code-monitor OOM-crash-looping (signal 9) — new recurrence, exit-code fleet monitor blind for hours"
summary: >-
  Found 2026-08-09T15:51Z as a side-discovery while root-causing the DP_RUN_MOSTLY_EMPTY re-nag regression on the
  sibling `dp-meta-watchers` Cloud Run Job (see
  `plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` for the original renag-dedup fix,
  unrelated to this). Live `gcloud logging read` on `uts-prod-dp-exit-code-monitor` shows `"Container terminated on
  signal 9."` (OOM) recurring on multiple consecutive */5 cron cycles as of this writing; its freshness sentinel
  `gs://deployment-scripts-central-element-323112/vm-census/exit-code-last-run.json` was stale at
  `ts=2026-08-09T02:31:35Z` (~13h behind at time of finding), meaning `DP_VM_EXIT_NONZERO`/ `DP_VM_GONE_NO_CAPTURE`
  detection has been silently blind for that window — the exact failure class this monitor exists to catch.
  `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s own comment on `data_pipeline_exit_code_monitor_job`
  (memory bumped 2Gi→8Gi/cpu2 on 2026-06-23, after repeated OOM at 2Gi/4Gi) explicitly flags "re-bump it too if the same
  flapping pattern recurs there" — the pattern has recurred and the job was never re-bumped, even though its two
  siblings in the same file (heartbeat-watcher 8Gi→16Gi/cpu4 2026-08-02; meta-watchers 16Gi→32Gi/cpu8 2026-08-09, same
  day) both already got a second bump for the identical "fleet grew past the current ceiling" reason. NOT yet fixed —
  out of scope for the task that found it (a live-verified fix + quickmerge for the meta-watchers TIMEOUT regression, a
  completely different symptom on a sibling job).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [data-pipeline-monitors, oom, cloud-run-job, exit-code-monitor, dp-vm]
related:
  [
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
    /plans/archive/2026_08/infra_health_audit_findings_fix_2026_08_07.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
  ]
created: 2026-08-09
author: sub-agent (Claude Code session, dispatched to diagnose DP_RUN_MOSTLY_EMPTY re-nag cadence)
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
archive_exempt: true
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-20
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md,
    /plans/archive/2026_08/issues/dp_meta_watchers_oom_at_32gi_2026_08_13.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
source: >-
  Operator asked whether DP_RUN_MOSTLY_EMPTY (check_high_attempted_failed) genuinely re-fires on the same stale failure
  data despite the 2026-07-15 RenagTracker cooldown fix, or represents new information each time. While pulling live
  Cloud Logging history for the sibling `dp-meta-watchers` job to answer that (root cause: a Cloud Run Job task-timeout
  regression, fixed + shipped separately), the SAME `gcloud logging read` sweep incidentally surfaced
  `uts-prod-dp-exit-code-monitor` actively OOM-killing on signal 9 — a different job, different failure mode (memory,
  not timeout), same file/pattern-class. Captured here per the workspace's "capture every side-discovery as a plan todo
  immediately" rule rather than left as a chat aside; the archived `infra_health_audit_findings_fix_2026_08_07.md` plan
  (which previously fixed a DIFFERENT bug on this same job — a preemption-detection `targetLink` filter bug, see its
  Progress Log) is already fully closed/archived (16/16 done, verified live) so this is filed as a fresh issue rather
  than reopening it.
---

# uts-prod-dp-exit-code-monitor OOM-crash-looping (signal 9)

## What was found

While diagnosing the `dp-meta-watchers` DP_RUN_MOSTLY_EMPTY re-nag question (separate task, separate fix), a
`gcloud logging read` sweep against the sibling `uts-prod-dp-exit-code-monitor` Cloud Run Job turned up:

```
2026-08-09T15:51:17Z  WARNING  Container terminated on signal 9.
```

recurring on multiple consecutive `*/5` cron cycles. Corroborating evidence:

- `gs://deployment-scripts-central-element-323112/vm-census/exit-code-last-run.json` (the job's own end-of-sweep
  freshness sentinel, written only on a clean completed run) was stuck at
  `{"counts": {"non_clean": 1, "terminated": 1}, "mode": "exit-code", "ok": true, "ts": "2026-08-09T02:31:35Z"}` —
  roughly 13 hours stale at the time of the finding, despite the `*/5` cadence.
- `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `data_pipeline_exit_code_monitor_job` module carries an
  explicit comment from the 2026-06-23 fix (2Gi/cpu1 → 8Gi/cpu2, after repeated OOM at 2Gi and 4Gi): "exit-code stays
  8Gi/cpu2 (bumped 2026-06-23, no OOM observed there currently) — **re-bump it too if the same flapping pattern recurs
  there**." It has recurred; the job's config was never re-bumped.
- Both siblings in the same terraform file already needed a SECOND bump for the identical "corpus grew past the current
  ceiling" reason: `data_pipeline_heartbeat_watcher_job` 8Gi/cpu2 → 16Gi/cpu4 (2026-08-02, DP-WATCHER-002 escalation
  `agt-4cb519`), and `data_pipeline_meta_watchers_job` 16Gi/cpu4 → 32Gi/cpu8 (2026-08-09, same day as this finding — a
  live-vs-IaC drift backport). The exit-code monitor sharing the exact same per-VM-shard full-fleet read pattern as
  heartbeat (per that job's own terraform comment) makes it a strong prior that it needs the same treatment.

## Why this matters

A silently-OOMing exit-code monitor never reaches its sentinel write (`_gcs.write_monitor_last_run`), so:

1. `DP_VM_EXIT_NONZERO` / `DP_VM_GONE_NO_CAPTURE` detection is blind for the duration — a VM that exits non-zero or
   terminates without capturing data during this window pages nothing.
2. `DeploymentsRegistry().reap_stale()` (wired into the exit-code sweep, `cli.py`) doesn't run either, so stale
   `deployments/active/*.json` registrations for already-gone instances accumulate.
3. The meta sweep's own `check_monitor_crons_fired` (DP-WATCHER-002) should eventually catch the stale sentinel and page
   `DP_CRON_DID_NOT_FIRE` for `vm-census/exit-code-last-run.json` — worth confirming that alert actually fired in
   `#data-pipeline-alerts` during this window (it should have), as a cross-check that the meta-watchers' own
   cron-freshness detection is intact (separately verified healthy as of the `dp-meta-watchers` fix in the sibling
   task).

## Not yet done

- [x] ✅ [SCRIPT] P1. **CONFIRMED (2026-08-13, slot 18)** — via Cloud Logging history, the OOM/signal-9 premise for this
      job is **DISPROVEN**. 30-day `gcloud logging read` shows **ZERO** `signal 9` / `Container terminated` events
      attributed to `uts-prod-dp-exit-code-monitor`. The signal-9 events the original finding saw on 08-09
      (`14:54/16:09/16:10/23:34Z`) are attributed to `uts-shared-deployment-api-*` (revisions `-00490/-00491/-00499`), a
      DIFFERENT job. The exit-code monitor actually ran **288 successful ~1-minute sweeps on 08-09**
      (`gcloud run jobs executions list` — "Execution completed successfully in 1m.."), so it was NOT OOM-looping. Its
      real failure modes since: **sweep-overlap** (chronic inability to finish within the `*/5` interval — the
      structural root cause, already tracked separately in
      `/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md` with the P1 parallelize todo), then
      **task timeouts** (08-11 executions "The configured timeout was reached"), then the cron was **PAUSED** (last
      executions 08-11T15:40, "Cancelled by user"). Live job config today = 16Gi/4cpu/1800s (bumped live 2026-08-10 —
      drift vs terraform 8Gi/2/900); cron scheduler = **PAUSED** `0 * * * *` (drift vs terraform `*/5 * * * *`). The
      `exit-code-last-run.json` sentinel being stale since 08-10T05:41Z is because **the cron is paused**, not OOM.
      Repo: deployment-service.
- [x] ✅ [SCRIPT] P1. Backport the ALREADY-LIVE 16Gi/cpu4/1800s config on `data_pipeline_exit_code_monitor_job` into
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf` — deployment-service@a87831b5 (live job was bumped
      2026-08-10 as an emergency fix; terraform still reads 8Gi/cpu2/900 — pure IaC-vs-live drift). The OOM
      justification is DISPROVEN (see todo 1); the real fix for the sweep being unable to finish is the parallelization
      todo in `/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`. This drift backport is
      bookkeeping on the existing live config, not a new bump. Ship via `quality-gates.sh` →
      `quickmerge.sh --agent --files`. Repo: deployment-service.
- [x] ✅ [SCRIPT] P2. **RESULT: verification target NOT met — a fresh, fast OOM regression on the confirmed-latest
      post-fix image, cron re-paused for safety.** (2026-08-15, slot-14·infra) The gating condition cited (the sibling
      sweep-overlap doc's parallelize/backlog-checkpoint fix chain) is now fully shipped —
      `deployment-service@48f4e8e6aa` (2026-08-15T02:26Z) confirmed an ancestor of `origin/live-defi-rollout`, and
      content-verified present in the currently-running `deployment-api:latest` image (tag `973d7a6`, pushed
      2026-08-15T15:28:34Z — pulled + `docker cp`'d `exit_code_fleet_monitor.py` directly off that digest, confirmed
      `run_log_prefetch_candidates = list(terminated)`, the exact widened-fan-out marker). Found the cron itself
      **PAUSED** (last 8 hourly executions 07:00Z→14:00Z today all still hit `"The configured timeout was reached"` on
      an OLDER pre-widened-fix digest) — resumed it (`gcloud scheduler jobs resume`, reversible, and the sibling doc's
      "confirm deliberate before resuming" caution is now stale: the underlying blocker it was protecting is the exact
      chain that's since shipped + verified). Triggered one immediate manual execution (`kpxh6`,
      `gcloud run jobs execute`) rather than waiting a full hour for the next scheduled tick, to get a same-session data
      point. **Result: NOT a timeout this time — `kpxh6` OOM-killed FAST** (`"The configured memory limit was reached"`,
      signal 9, at 15:43:43Z — only ~103s after the job started at 15:42:03Z-ish, and only ~42s after the
      `run-log-prefetch` phase's own completion log line at 15:43:01Z). Phase logs before the kill: `running-census`
      (not separately timestamped in the tail read) → `terminated-base-signals phase took 306.1s (155 VMs, 16 workers)`
      → `run-log-prefetch phase took 39.6s (155 candidates, 16 workers)` — both FAST, confirming the widened-fan-out +
      2MiB tail-cap combination is not itself memory-heavy at face value (155 candidates × 2MiB cap ≈ 310MB worst case,
      well under the 16Gi limit) — then the sequential classify/route/emit phase started at 15:43:01Z and the container
      was killed at 15:43:43Z, only 42s later, well before any wall-clock timeout could explain it.
      `gcloud logging read` for this execution shows a HIGH rate of `download_bytes`/`download_bytes_range`
      30s-bounded-call stalls/timeouts across BOTH fanned-out phases (~50+ warnings in the 90s window before the kill) —
      each stalled call, per the sibling doc's own already-flagged (but never confirmed/fixed) "possibly-compounding
      contributor" note, leaves an abandoned daemon thread that "can never block process exit" and holds its own
      buffered/retry state for the rest of the process lifetime. This is the strongest live candidate for the fast OOM:
      thread-count/retry-state accumulation across two consecutive fanned-out phases hitting the SAME throttled
      `vm-logs/` prefix, not resident run.log blob size (which the tail-cap fix already bounds). **Re-paused the cron
      immediately after this result** (`gcloud scheduler jobs pause`) to avoid an hourly OOM storm recurring on schedule
      while this is unfixed — same reversible action, verified `state=PAUSED` after. Did not attempt a fix (infra craft
      scope is live-verify here, not a fresh investigate/fix — mirrors this doc's and the sibling doc's own established
      pattern of a NEW P1 investigate/fix todo for a NEW failure mode rather than absorbing unplanned scope). Filed the
      fix-needed finding as a new todo in `/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`
      (that doc's own established SSOT for this job's fix chain, `archive_exempt: true` precisely because it stays the
      live fix-chain home even though its own todos are all individually closed). Repo: deployment-service.
- [x] ✅ [SCRIPT] P2. **CONFIRMED (2026-08-14, slot 11)** — cross-checked `#data-pipeline-alerts`
      (`slack-read-channel.py data-pipeline-alerts 132`, 12,599 messages) for `DP_CRON_DID_NOT_FIRE` on
      `cron 'dp-exit-code-monitor'` / `vm-census/exit-code-last-run.json`. **Partial detection, with a real gap that
      confirms the note's own suspicion:** - **08-09 window** (the original OOM-suspected staleness, later disproven —
      todo 1): detection worked correctly end-to-end — 6 firing alerts 16:23Z→19:27Z (`last output` growing 831m→1011m
      ago) followed by a clean `:white_check_mark: RESOLVED — vm-census/exit-code-last-run.json recovered` at
      19:38:25Z. - **08-10/08-11 pause-window** (cron paused 08-11T15:40): detection ALSO fired correctly at first — 7
      more alerts from 08-10T20:55Z through 08-11T01:11Z (`last output` growing 914m→1170m ago) — confirming
      `check_monitor_crons_fired` was reaching this check and correctly flagging the paused cron. - **Then it went
      silent**: exactly ONE more alert at **08-12T19:05:30Z** (`last output 3683m ago` ≈ 61.4h stale), then **zero
      further `DP_CRON_DID_NOT_FIRE::exit-code` alerts** in the rest of the 132h window despite the cron remaining
      paused for at least another day (resumed by someone else sometime before slot 15's 08-14 check per this doc's own
      Progress Log — exact resume timestamp not captured by either session). **This IS the second finding**: the
      alerting gap from 08-12T19:06Z onward lines up exactly with
      `/plans/archive/2026_08/issues/dp_meta_watchers_oom_at_32gi_2026_08_13.md`'s live incident (meta-watchers
      OOM-killing every `*/15` run at 32Gi, confirmed ongoing through 2026-08-13, root-caused + fixed 2026-08-14 slot 14
      — `deployment-service@f425eb12b3`) — the meta sweep was dying before reaching `check_monitor_crons_fired`, so the
      cross-check silently stopped running for that whole window rather than the detection logic itself being broken.
      Folded this same finding into that doc's twin todo (its own todo 2) rather than filing a third issue doc — the
      root cause is already tracked + fixed there.

## Progress Log

- 2026-08-15 (slot-14, infra): Closed the final open todo (todo 3, live-verify sentinel post-fix). Full result in the
  todo itself: confirmed the sibling sweep-overlap doc's fix chain fully shipped + live (`48f4e8e6aa`, content-verified
  in the running `deployment-api:latest` image), resumed the previously-PAUSED cron, triggered one manual execution as
  an immediate data point — it OOM-killed FAST (42s after run-log-prefetch completed), a NEW regression distinct from
  both the original OOM-suspected premise (disproven, todo 1) and the wall-clock-timeout class the widened-prefetch fix
  was built to solve. Re-paused the cron for safety. Filed the fix-needed finding as a new todo in the sweep-overlap doc
  rather than attempting a fix myself (live-verify task scope). This doc's own todos are now all closed — leaving
  `status: open`/active per its own `archive_exempt`-adjacent situation: it remains referenced as the SOURCE doc by
  `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` (this same live-verify item) and the sweep-overlap doc's
  cross-reference; not archiving this session (checkbox reconciliation into the batch plan happens per that plan's own
  convention, and archival coordination across referencing docs is a `/plan-reconcile`-class action, not a single-worker
  flip — mirrors the sweep-overlap doc's own stated `archive_exempt` reasoning).

- 2026-08-14 (slot 15, infra): Todo 3 (live-verify sentinel after resume) — re-checked. The cron is now **ENABLED**
  (`gcloud scheduler jobs describe uts-prod-dp-exit-code-monitor-cron`: `state=ENABLED`, `schedule=0 * * * *` hourly) —
  resumed by someone else since slot 29's 08-13 check; not resumed by this session. The sibling doc's P1
  `ThreadPoolExecutor` parallelize fix (`deployment-service@069ced1412`) IS present at current HEAD (confirmed
  `grep -n ThreadPoolExecutor deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` → 3 hits, incl. the
  pool construction). Signal-9/OOM is confirmed genuinely absent: `gcloud logging read` for
  `resource.labels.job_name="uts-prod-dp-exit-code-monitor" AND textPayload:"signal 9"` over the last 6h returns ZERO
  hits. **But the verification target itself still FAILS**: `gcloud run jobs executions list` shows 3 consecutive full
  executions on 08-13 (21:27–21:57, 22:00–22:30, 23:00–23:30, all AFTER the parallelize fix shipped the same day) each
  hit `"The configured timeout was reached"` at the full 1800s — the identical failure mode as before the fix. A 4th
  execution (`8n77n`, started 00:00:05 on 08-14) was still running past the 15-min mark at last check, live logs showing
  per-VM classification lines spaced ~30-90s apart (not the tight clustering you'd expect from a genuinely effective
  32-worker thread pool), including a `download_bytes(...) exceeded the 30s bounded-call timeout` stall on one VM's
  run.log read. **Conclusion: the parallelize fix, though shipped and live, has NOT brought the sweep under its 1800s
  timeout in production — the sentinel is still not advancing cleanly.** Leaving this todo UNCHECKED (the
  ≥3-consecutive-clean-cycles target is not met) and did not further touch the cron/job config myself (investigation
  only, no infra state changed this session). Filed a follow-up todo + Progress Log entry in
  `/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md` (the sweep-duration SSOT) since its
  shipped P1 fix is now empirically disproven-insufficient — that's the right place for the next fix attempt, not this
  P2 verify-only todo.

- 2026-08-13 (slot 29): Todo 3 (live-verify sentinel after resume) — checked whether it's safe to resume yet. Live
  `gcloud scheduler jobs list --location=asia-northeast1` confirms `uts-prod-dp-exit-code-monitor-cron` is still
  **PAUSED**, schedule already edited to `0 * * * *` (hourly — the "reduce cadence" fallback from
  `dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`), but never resumed. `gcloud run jobs executions list` shows
  every execution in the run-up to the 08-11T15:40 pause hit **"The configured timeout was reached"** at the full 1800s
  (30 min) task timeout, even at the bumped 16Gi/4cpu — the sweep does not complete within 30 min. The sibling doc's P1
  `ThreadPoolExecutor` parallelize todo is still open and unshipped (confirmed:
  `grep -c ThreadPoolExecutor deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` = 0 on current
  HEAD). **Verdict: NOT safe to resume yet** — even at the reduced hourly cadence, a sweep that still needs >30 min will
  keep hitting the 1800s timeout every cycle and the freshness sentinel will never advance, failing this todo's own
  verification target before it even starts. Resuming now would not reproduce the original signal-9/overlap storm
  (hourly cadence caps concurrent executions to ~1), but it also would not produce the "sentinel advances ≥3 consecutive
  cycles" evidence this todo needs — that requires the sweep to actually finish, which requires the parallelize fix.
  Skipping this todo GATED on `/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`'s P1
  landing; re-attempt resume-verify only after that ships (or after a task-timeout bump well past the sweep's real
  duration, which is unmeasured since every observed run was killed at exactly 1800s).

- 2026-08-13 (slot 18, infra): Confirmed via Cloud Logging history (todo 1) that the exit-code monitor is **NOT**
  OOM-crash-looping — zero signal-9 events attributed to it in 30 days; 08-09 signal-9s were
  `uts-shared-deployment-api-*`; it ran 288 successful ~1-min sweeps on 08-09. Real failure modes: sweep-overlap
  (sibling doc, P1 parallelize todo), then timeouts, then cron **PAUSED** (08-11T15:40). Discovered the exit-code cron
  is currently PAUSED + drifted live config (16Gi/4/1800 vs tf 8Gi/2/900) + a separate LIVE incident: `dp-meta-watchers`
  OOM-killing every `*/15` run at 32Gi today — filed as `dp_meta_watchers_oom_at_32gi_2026_08_13.md`.

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-09: Filed as a side-discovery from the `dp-meta-watchers` DP_RUN_MOSTLY_EMPTY re-nag investigation. Not fixed
  in this session (out of scope) — this doc exists so the finding isn't lost as a chat aside.
- **context-scout 2026-08-14**: populated context_scope (4 entries).
- 2026-08-14 (slot 11, infra): Closed todo 4 (cross-check `#data-pipeline-alerts` for `DP_CRON_DID_NOT_FIRE::exit-code`
  during the stale/paused window). Read `#data-pipeline-alerts` via
  `scripts/dev/slack-read-channel.py data-pipeline-alerts 132` (132h window, 2026-08-08→2026-08-14, 12,599 messages),
  filtered for `exit-code`. Detection worked correctly for the 08-09 window (6 alerts + a clean RESOLVED at 19:38:25Z)
  and for the start of the 08-10/08-11 pause window (7 more alerts through 08-11T01:11Z), but went silent after one last
  alert at 08-12T19:05:30Z (3683m/61.4h stale) for the rest of the window despite the cron staying paused — a real gap,
  attributable to `/plans/archive/2026_08/issues/dp_meta_watchers_oom_at_32gi_2026_08_13.md`'s concurrent live OOM
  incident (the meta sweep was dying before reaching `check_monitor_crons_fired`, confirmed by that doc's own timeline:
  the incident was live through 08-13 and only root-caused + fixed 08-14 slot 14, `deployment-service@f425eb12b3`).
  Folded the same finding + evidence into that doc's twin todo 2 rather than filing a third issue doc — no code change
  needed here, the root cause is already tracked and fixed there. No repos touched by this session (findings-only
  cross-check).
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
