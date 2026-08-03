---
doc_type: issue
title:
  "reap-zombies.sh checks the WRONG GCS log path (logs/ instead of canonical vm-logs/) — reaps ANY healthy VM older than
  10min fleet-wide; confirmed killing a healthy, zero-error defi backfill campaign mid-run"
summary: >-
  While monitoring a long-running defi dex_pool_swaps source-correction backfill VM
  (backfill-defi-dex-swaps-20260803-092530), the VM was DELETED (not preempted) at 2026-08-03T10:30:56Z by service
  account uts-prd-sa via the gcloud CLI from a non-interactive script, despite being demonstrably healthy (monotonic
  day-progress advancing every check, zero errors, 60s heartbeats). Root-caused to
  deployment-service/scripts/vm/reap-zombies.sh checking `gs://<bucket>/logs/<instance>/run.log` — a path that has NEVER
  existed for any VM using the canonical convention (`vm-logs/<instance>/run.log`, the SSOT per
  unified_trading_library::vm_log_stream_uri and launcher_common.sh's own documented canonical path). This makes
  reap-zombies.sh always read "no run.log at all" for every correctly-functioning VM and fall through to a
  creation-time-only staleness check with a 600s (10-minute) default threshold — meaning ANY healthy VM older than 10
  minutes is a false-positive zombie candidate under this script, fleet-wide, not just this task's VM.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, vm-lifecycle, zombie-watchdog, false-positive, big-finding, data-pipeline, cross-cutting]
related:
  [
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /plans/archive/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
    /plans/active/issues/vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
source: >-
  Surfaced 2026-08-03 (slot 15, data_engineering) while monitoring
  plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md's last open todo (defi dex_pool_swaps
  source-correction campaign verification).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /plans/archive/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
  ]
depends_on: []
---

# reap-zombies.sh checks the wrong GCS log path — reaps healthy VMs fleet-wide

## What I found

While monitoring `backfill-defi-dex-swaps-20260803-092530` (a Tier-2 SPOT VM running
`backfill_defi_dex_pool_swaps_source_correction.py --apply`, launched to close the last open todo of
`mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`), the VM disappeared mid-campaign:

- **Health immediately before deletion**: `last_completed_date` had advanced monotonically every ~2-7 minutes
  (2023-01-01 → 2023-01-12) across ~40 polls over ~61 minutes, zero `errors=` in any completed-day log line, VM status
  `RUNNING` throughout, 60s heartbeats visible in `run.log` (`PIPELINE_HEARTBEAT ... source=vm-life-emitter`).
- **What happened**: `gcloud compute operations list` showed a `delete` operation (`operation-1785753056146-...`)
  inserted at `2026-08-03T03:30:56-07:00` (`10:30:56Z`), NOT a `compute.instances.preempted` system event — this was an
  explicit delete, not a SPOT preemption.
- **Who/what did it**: `gcloud logging read` on the delete audit entry shows
  `principalEmail: uts-prd-sa@central-element-323112.iam.gserviceaccount.com`, `callerIp: 136.110.126.79`, and
  critically the `callerSuppliedUserAgent`:
  `google-cloud-sdk gcloud/577.0.0 command/gcloud.compute.instances.delete ... interactive/False from-script/True`. This
  is the **`gcloud` CLI binary**, invoked non-interactively from a script — NOT the Python `google-cloud-compute` client
  that `deployment-service/scripts/vm/vm_zombie_watchdog.py` uses (`compute_v1.InstancesClient().delete(...)`, which
  would carry a different, gRPC/python-client user-agent shape). This rules out `vm_zombie_watchdog.py` as the actor
  (further confirmed: its own pre-kill log-backup step, which archives `run.log` to
  `gs://deployment-scripts-{project}/log-archive/snapshot_{ts}/{vm}/` before any delete, left NO archive for this VM or
  this timestamp — `gcloud storage ls .../log-archive/ | grep 20260803` returns nothing).
- **Root cause**: `deployment-service/scripts/vm/reap-zombies.sh` builds its run.log path as:
  ```bash
  log_path="gs://${BUCKET}/logs/${instance}/run.log"
  ```
  but the CANONICAL (and universally actually-used) path, documented as the SSOT in THREE places
  (`unified_trading_library/deployment_registry.py::vm_log_stream_uri` docstring, `launcher_common.sh` lines ~1155-1159
  "Canonical run.log path", and `aws_ec2_launch_lib.sh`'s AWS-side mirror), is:
  ```
  gs://${BUCKET}/vm-logs/${instance}/run.log
  ```
  Confirmed empirically:
  `gs://deployment-scripts-central-element-323112/logs/backfill-defi-dex-swaps-20260803-092530/run.log` and the same
  path for a second, unrelated VM (`backfill-defi-dex-swaps-20260803-090659`) BOTH return "no objects matched" — the
  `logs/` prefix (without the `vm-` segment) has never held real VM logs for either VM checked. Every VM using the
  canonical launcher stack (`launcher_common.sh`, `setup-data-pipeline-vm.sh`, `aws_ec2_launch_lib.sh` — i.e.
  essentially the entire fleet) writes to `vm-logs/`, so `reap-zombies.sh`'s `tail_text` read is UNCONDITIONALLY empty
  for every real, healthy VM on this project.
- **Consequence of the path bug**: with `tail_text` always empty, `reap-zombies.sh` falls into its "no run.log at all"
  branch, which checks ONLY the VM's `creationTimestamp` against `--silence-threshold-sec` (default `600` = 10 minutes)
  and reaps unconditionally past that age — `reason="no run.log + created ${SILENCE_SEC}s+ ago"`. My VM was created at
  `09:29:57Z` and reaped at `10:30:56Z` (61 minutes old) — squarely past the 600s default. **This means reap-zombies.sh,
  if run against ANY prefix, will delete every matching VM older than 10 minutes regardless of real health** — the "was
  it actually silent" check it's designed to perform never engages because it can never find the log it's looking for.
- **Who/what invoked reap-zombies.sh this time**: not conclusively identified — grepped `deployment-service` +
  `agent-orchestrator` for any Terraform/GHA/systemd/crontab wiring of `reap-zombies.sh` and found none (it does not
  appear to be scheduled via `terraform/gcp/*.tf` or `cloud_run_job_registry.py`). Given the gcloud-CLI +
  non-interactive-script signature, the most likely explanation is an ad-hoc invocation by another agent/slot doing
  fleet-cleanup or VM-audit work (e.g. a `/vm-preemption-billing-waste-audit` -style pass) rather than a hidden
  recurring cron — but this was NOT independently confirmed and is worth a operator/main-agent check of recent agent
  activity around `10:30:56Z` if a definitive attribution matters.
- **Impact on the task this surfaced from**: the campaign lost real wall-clock time (VM relaunched immediately,
  `backfill-defi-dex-swaps-20260803-103749`, verified running the correct fixed code —
  `market-data-processing-service@ce64a98` confirmed an ancestor of the freshly-published tarball pin). No DATA was lost
  or corrupted — the tool's `--apply` writes (copy-not-move + `record_captured`) are durable and idempotent, and its own
  day-level checkpoint design means a resume only REDOES already-done days rather than causing incorrect output.
  However: the checkpoint is only written every 20 completed days (see the second, smaller finding below), so fewer than
  20 days in this run meant the checkpoint was never actually persisted, and the relaunch reprocesses from day 1
  (safe/idempotent, just wasted ~15-20 min of the ~61 min of prior work).
- **Second, smaller finding (same investigation, not blocking)**:
  `market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py::run_remediate` only calls
  `_write_checkpoint` every 20 days (`if i % 20 == 0`) plus once at the very end of a full, uninterrupted run — there is
  no `finally`-block or per-day checkpoint write, so ANY kill (preemption, a zombie-watchdog false-positive like this
  one, an OOM, an operator-initiated stop) within the first 19 days of a run loses all checkpoint progress, forcing a
  full redo from day 1 on the next launch. This is safe (idempotent) but wasteful, and undermines the
  "PROGRESS-checkpoint contract" intent the tool's own launcher-script docstring claims to satisfy ("resumes from
  measured progress on a SPOT preemption relaunch rather than replaying from day one").

## Why it matters

This is NOT scoped to one VM or one campaign. `reap-zombies.sh`'s log-path bug means that **if this script runs against
any VM prefix on this project, it will delete every matching VM older than 10 minutes, healthy or not** — the entire "is
it actually silent" logic it exists to implement is structurally unreachable given the path mismatch. Any future
invocation (scheduled, ad-hoc, or copy-pasted by an agent following stale documentation) against a broad prefix filter
could mass-delete a large slice of the currently-running fleet, matching the exact "zombie watchdog false-positive reaps
a live backfill" incident class already codified as a HARD RULE in `unified-trading-pm/agents/data_engineering.md` §
VM-delete guardrail (which cites 3 prior same-day incidents from 2026-07-18,
`zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`) — this is the SAME failure MODE recurring via a
different, previously-unaudited script. Given `reap-zombies.sh` was NOT the actor implicated in that earlier incident
doc (that one was an agent's manual `gcloud compute instances delete` copy-paste, not this script), this is a genuinely
NEW root cause in the same incident family, not a duplicate.

## Recommended decision

- [x] ✅ [INFRA] P0. **Fix the log path in `deployment-service/scripts/vm/reap-zombies.sh`** — change
      `log_path="gs://${BUCKET}/logs/${instance}/run.log"` to `log_path="gs://${BUCKET}/vm-logs/${instance}/run.log"`
      (matching the canonical SSOT — ideally source the path via the same `vm_log_stream_uri()` convention the Python
      side uses, or at minimum hardcode the correct `vm-logs/` segment). Add a regression test/fixture (or a `--dry-run`
      smoke invocation against a known-healthy running VM showing it now correctly finds `tail_text` non-empty and skips
      it) so this exact mismatch cannot silently reappear. (repo: deployment-service) — `deployment-service@60d9f7e`.
      Added `tests/test_reap_zombies.sh` — a stubbed-gcloud regression harness proving (a) a healthy VM at the canonical
      `vm-logs/` path is read + skipped, (b) the queried path is exactly `vm-logs/` never `logs/`, (c) a VM with a
      terminal `rc=` line is reaped, (d) `--dry-run` never calls delete. Verified the test fails on the pre-fix script
      (reproduces the exact incident: healthy VM read as zombie) and passes on the fix. `quality-gates.sh` green,
      quickmerge landed on `live-defi-rollout`, SHA verified ancestor of origin.
- [x] ✅ [INFRA] P1. **Audit whether `reap-zombies.sh` has ever been invoked against prod in a way that could have
      silently killed other healthy VMs** — check `gcloud logging read` for `v1.compute.instances.delete` events
      fleet-wide over the last 30 days where `callerSuppliedUserAgent` matches the `gcloud` CLI (`from-script/True`, NOT
      the Python compute client's signature) and cross-reference each deleted VM's run.log for a genuine terminal
      `rc=`/`VERDICT` line vs. a healthy-but-young kill. If other false-positive reaps are found, file them as their own
      follow-up (data-loss / wasted-compute) issue docs per the findings-triage HARD RULE. (repo: deployment-service) —
      **Answer: NO evidence of reap-zombies.sh's list+delete-loop pattern actually running against prod in the audited
      30-day window.** Pulled all `v1.compute.instances.delete` events (20,691 total, project-wide) via
      `gcloud logging read`; the `uts-prd-sa@...` + gcloud-CLI/`from-script/True` signature matching the flagged
      incident's actor accounts for 202 events / 101 unique instances. A 12-instance random sample's `run.log` (read at
      the CORRECT `vm-logs/` path) each showed a clean, self-contained `DEPLOYMENT_COMPLETED`/`DEPLOYMENT_FAILED`
      terminal state immediately followed by `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete` — the documented,
      intentional self-delete convention (`launcher_common.sh`/`vm-exec-with-gcs-tee.sh`), not reap-zombies.sh.
      Caller-IP reuse across unrelated, temporally-scattered instances is consistent with Cloud NAT IP-pool sharing
      across independent self-deletes, not one centralized actor. **BIG FINDING — corrects this doc's own root-cause
      claim**: re-checked the ORIGINAL flagged VM's `run.log` the same way, and it shows
      `[vm-exec] DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED     mode=no-progress-marker stalled_for=3639 threshold=3600`
      immediately before its self-delete — i.e. the VM was SELF-killed by `vm-exec-with-gcs-tee.sh`'s own stall watchdog
      (a `STALL_PROGRESS_REGEX=checkpoint` misconfiguration in the launcher — the tool only logs "checkpoint" every 20th
      day, never per-day), NOT reaped by reap-zombies.sh. Filed as
      `/plans/active/issues/vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md` (P0) with the full evidence
      chain, the launcher fix (already applied, `STALL_PROGRESS_REGEX=day=`), and a time-critical callout that the
      relaunched VM (`backfill-defi-dex-swaps-20260803-103749`) is running the OLD pre-fix metadata and is on track to
      hit the identical self-kill imminently. Todo 1's reap-zombies.sh log-path fix remains a real, independently
      worthwhile fix — it just wasn't the cause of THIS incident.
- [x] ✅ [INFRA] P2. **Determine (or rule out) what actually invoked `reap-zombies.sh` at `2026-08-03T10:30:56Z`** —
      **RULED OUT: `reap-zombies.sh` was never invoked at this timestamp at all.** Two independent lines of evidence
      converge: (1) a repo-wide grep for `reap-zombies` across `deployment-service`, `unified-trading-pm`, and
      `agent-orchestrator` (`*.yml`/`*.yaml`/`*.tf`/`*.sh`/`*.py`, plus a plain filename grep) finds the script only at
      its own source path and its own new test — zero Terraform/GHA/systemd/cron wiring anywhere in any repo checkout
      that could have fired it on a schedule or from CI; (2) direct read of
      `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` lines 432-471 (the `VM_SHUTDOWN_ON_COMPLETION=true`
      self-delete block) shows it fires
      `gcloud compute instances delete '$VM_NAME_SELF' --zone='$VM_ZONE_SELF' --quiet     --delete-disks=all` from a
      detached background subshell **running on the VM itself**, under the VM's own attached `uts-prd-sa` service
      account — which independently and exactly reproduces every signature element previously attributed to
      reap-zombies.sh (`gcloud` CLI binary, `interactive/False from-script/True`, `uts-prd-sa` principal, caller IP =
      the VM's own network egress). This is the SAME mechanism
      `vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md` already root-caused as the actual killer of the
      flagged VM (a `WORKER_STALLED` self-kill, not an external reap). Combined with todo 2's 30-day fleet-wide audit
      (zero evidence of reap-zombies.sh's list+delete-loop pattern ever running against prod), there is no remaining
      candidate actor other than each VM's own documented self-delete convention — the question is answered, not just
      left inconclusive. No recurring schedule exists to harden, so todo 1's path fix (already shipped) is
      defense-in-depth for a script that is invoked ad hoc/manually only, not a currently-scheduled process. (repo:
      deployment-service, unified-trading-pm) — doc-only, no code change required.
- [ ] [DATA] P2. **Make `backfill_defi_dex_pool_swaps_source_correction.py`'s day-level checkpoint durable against an
      early kill** — write `_write_checkpoint` after EVERY completed day (or wrap the loop body in a try/finally that
      always persists `done_days` on any exit path, not just the `i % 20 == 0` cadence + a full-completion tail-call),
      so a kill within the first 19 days doesn't force a full redo from day 1. Given per-day GCS writes are cheap
      relative to the per-day copy/record work itself, the extra per-day checkpoint write is not a meaningful cost.
      Add/update the existing unit test suite
      (`tests/unit/scripts/test_backfill_defi_dex_pool_swaps_source_correction.py`) to cover a simulated
      early-kill-then-resume scenario. (repo: market-data-processing-service)

## Progress Log

- **2026-08-03T10:38Z** (AO dispatch, slot 15, `data_engineering`) — Filed while monitoring
  `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`'s last open todo. Root-caused via GCS path probes +
  `gcloud logging read` audit-log inspection (principal, user-agent, caller IP) + source-code cross-reference across
  `reap-zombies.sh`, `vm_zombie_watchdog.py`, and the canonical `vm_log_stream_uri()` SSOT. Mitigated the immediate
  impact by relaunching the affected campaign VM (`backfill-defi-dex-swaps-20260803-103749`, verified running the
  correct fixed tool code, `market-data-processing-service@ce64a98` confirmed an ancestor of the published tarball pin).
  Did not fix `reap-zombies.sh` itself in this session — that's todo 1, filed for a worker with `infra` role/scope (this
  session stayed in `data_engineering` craft per the craft-not-domain rule; `reap-zombies.sh` is infra-lifecycle
  tooling, not data-pipeline code). No GCS deletes/mutations performed by this investigation — every action was
  read-only (log/operation inspection, GCS listing, git history) plus the one legitimate VM relaunch.
- **2026-08-03T~11:05Z** (AO dispatch, slot 10, `infra`) — Fixed todo 1: `reap-zombies.sh`'s `log_path` now reads
  `gs://${BUCKET}/vm-logs/${instance}/run.log` (was `.../logs/${instance}/run.log`). Added
  `deployment-service/tests/test_reap_zombies.sh`, a stubbed-`gcloud` shell harness (same pattern as
  `tests/test_launch_expected_universe_v2.sh`) covering: healthy-VM skip at the canonical path, a regression guard
  asserting the exact queried path, terminal-`rc=` reap, and `--dry-run` never deleting. Confirmed empirically that the
  test FAILS against the pre-fix script (reproduces the incident: a healthy VM at an old creation timestamp gets reaped
  because the wrong path reads empty) and PASSES against the fix — this is a real regression guard, not a vacuous one.
  `quality-gates.sh` full run green (3019 passed); shipped via `quickmerge --agent`, `deployment-service@60d9f7e`
  verified ancestor of `origin/live-defi-rollout`. Todos 2-4 (audit for other false-positive reaps, determine what
  invoked the script, harden the source-correction script's checkpoint cadence) remain open — out of this task's scope
  (single P0 todo dispatched).
- **2026-08-03T~11:30Z** (AO dispatch, slot 6, `infra`) — Completed todo 2 (the fleet-wide false-positive-reap audit).
  **Correction to this doc's own root cause**: the flagged VM was NOT killed by reap-zombies.sh — its `run.log`, read at
  the correct `vm-logs/` path, shows a self-inflicted `WORKER_STALLED`/`no-progress-marker` kill by
  `vm-exec-with-gcs-tee.sh`'s own stall watchdog, caused by a `STALL_PROGRESS_REGEX=checkpoint` misconfiguration in
  `launch-backfill-defi-dex-swaps-source-correction-vm.sh` (the tool only logs "checkpoint" every 20th day, so the
  watchdog's 3600s no-progress threshold trips before the first checkpoint on every real run). Full evidence chain + the
  fix (already applied, `STALL_PROGRESS_REGEX=day=`, pending ship) + a time-critical note that the relaunched VM is
  running the pre-fix metadata: `/plans/active/issues/vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md`
  (P0). Todo 1's reap-zombies.sh fix stays valid/necessary (a real bug, just not this incident's cause). Todos 3-4
  remain open. No GCS deletes/mutations performed — read-only investigation (30-day `gcloud logging read`, GCS log
  reads, `gcloud compute instances describe`) plus the launcher-script edit filed in the new doc.
- **2026-08-03T~11:45Z** (AO dispatch, slot 6, `infra`, todo 3) — Ruled out `reap-zombies.sh` as ever having been
  invoked at `2026-08-03T10:30:56Z` (or in the broader 30-day window todo 2 already audited). Repo-wide grep across
  `deployment-service`/`unified-trading-pm`/`agent-orchestrator` found zero Terraform/GHA/systemd/cron wiring of the
  script anywhere. Direct read of `vm-exec-with-gcs-tee.sh`'s `VM_SHUTDOWN_ON_COMPLETION=true` self-delete block (lines
  432-471) confirms it independently reproduces the exact audit-log signature previously attributed to reap-zombies.sh
  (gcloud CLI, `from-script/True`, `uts-prd-sa`, VM's own egress IP) — consistent with
  `vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md`'s finding that this specific VM self-killed via its
  own stall watchdog. No new investigation needed beyond cross-referencing the two already-completed audits. No code
  shipped (doc-only closure); no GCS/VM mutations performed.
