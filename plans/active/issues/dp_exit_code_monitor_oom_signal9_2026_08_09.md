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
assigned_vm: NA
execution_scope: local-only
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

- [ ] [SCRIPT] P1. Confirm via Cloud Logging history
      (`gcloud logging read 'resource.labels.job_name="uts-prod-dp-exit-code-monitor" AND textPayload:"signal 9"'`) how
      far back the OOM recurrence actually goes (single-session blip vs. sustained, like the meta-watchers timeout was).
- [ ] [SCRIPT] P1. Bump `cpu`/`memory` on `data_pipeline_exit_code_monitor_job` in
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf` (mirror the heartbeat-watcher's 8Gi/cpu2 → 16Gi/cpu4
      precedent in the same file — exit-code and heartbeat share the same "reads per-VM shards for the whole RUNNING
      fleet" load pattern per that file's own comments) — apply live via `gcloud run jobs update` first (mirrors this
      session's meta-watchers emergency-fix pattern) then backport to terraform, ship via `quality-gates.sh` →
      `quickmerge.sh --agent --files`.
- [ ] [SCRIPT] P2. Live-verify: watch `vm-census/exit-code-last-run.json` advance on schedule (every ~5 min) for at
      least 3 consecutive cycles post-fix, and confirm no further `"signal 9"` entries in Cloud Logging.
- [ ] [SCRIPT] P2. Cross-check `#data-pipeline-alerts` for `DP_CRON_DID_NOT_FIRE::vm-census/exit-code-last-run.json`
      during the stale window, confirming the meta-watchers' own cron-freshness detection correctly caught this (or, if
      it didn't, treat that as a second finding).

## Progress Log

- 2026-08-09: Filed as a side-discovery from the `dp-meta-watchers` DP_RUN_MOSTLY_EMPTY re-nag investigation. Not fixed
  in this session (out of scope) — this doc exists so the finding isn't lost as a chat aside.
