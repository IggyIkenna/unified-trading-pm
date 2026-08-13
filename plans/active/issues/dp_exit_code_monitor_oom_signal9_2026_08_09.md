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
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-09
locked_since:
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
      `/plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md` with the P1 parallelize todo), then
      **task timeouts** (08-11 executions "The configured timeout was reached"), then the cron was **PAUSED** (last
      executions 08-11T15:40, "Cancelled by user"). Live job config today = 16Gi/4cpu/1800s (bumped live 2026-08-10 —
      drift vs terraform 8Gi/2/900); cron scheduler = **PAUSED** `0 * * * *` (drift vs terraform `*/5 * * * *`). The
      `exit-code-last-run.json` sentinel being stale since 08-10T05:41Z is because **the cron is paused**, not OOM.
      Repo: deployment-service.
- [ ] [SCRIPT] P1. Backport the ALREADY-LIVE 16Gi/cpu4/1800s config on `data_pipeline_exit_code_monitor_job` into
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf` (live job was bumped 2026-08-10 as an emergency fix;
      terraform still reads 8Gi/cpu2/900 — pure IaC-vs-live drift). The OOM justification is DISPROVEN (see todo 1); the
      real fix for the sweep being unable to finish is the parallelization todo in
      `/plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`. This drift backport is bookkeeping
      on the existing live config, not a new bump. Ship via `quality-gates.sh` → `quickmerge.sh --agent --files`. Repo:
      deployment-service.
- [ ] [SCRIPT] P2. **GATED on the cron being resumed** — live-verify the sentinel advances only once
      `uts-prod-dp-exit-code-monitor-cron` is re-ENABLED; it is currently **PAUSED** (last execution 08-11T15:40), so
      the sentinel is stale by definition of the cron not running. Verification target:
      `vm-census/exit-code-last-run.json` advances on schedule for ≥3 consecutive cycles after resume, with no
      `"signal     9"` entries. NOTE: before resuming, confirm the pause was deliberate (likely operator action to stop
      the 08-10 alert storm while the overlap fix lands) — do NOT resume blind. Repo: deployment-service.
- [ ] [SCRIPT] P2. Cross-check `#data-pipeline-alerts` for `DP_CRON_DID_NOT_FIRE::vm-census/exit-code-last-run.json`
      during the stale/paused window, confirming the meta-watchers' own cron-freshness detection correctly caught this
      (or, if it didn't, treat that as a second finding). **NOTE 2026-08-13**: meta-watchers is itself currently
      OOM-killing every `*/15` run at 32Gi (`dp_meta_watchers_oom_at_32gi_2026_08_13.md`) and may never reach
      `check_monitor_crons_fired` — so a missing `DP_CRON_DID_NOT_FIRE` may mean the cross-check never ran, not that the
      detection is broken.

## Progress Log

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
