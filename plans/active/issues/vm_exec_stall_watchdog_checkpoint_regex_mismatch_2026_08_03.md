---
doc_type: issue
title:
  "vm-exec-with-gcs-tee.sh's STALL_PROGRESS_REGEX=checkpoint self-kills every real run of
  backfill_defi_dex_pool_swaps_source_correction.py — CORRECTS the root-cause claim in
  reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md (the flagged VM was self-killed by this watchdog, not
  reaped by reap-zombies.sh); relaunched VM is currently minutes from hitting the same kill"
summary: >-
  Auditing reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md's todo 2 (were other healthy VMs killed by
  reap-zombies.sh?) turned up direct evidence that the ORIGINAL flagged VM (backfill-defi-dex-swaps-20260803-092530) was
  NOT killed by reap-zombies.sh at all: its own run.log (read at the correct vm-logs/ path) shows `[vm-exec]
  DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=3639 threshold=3600`
  immediately followed by `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete` — a SELF-inflicted kill by
  vm-exec-with-gcs-tee.sh's own stall watchdog, triggered because the launcher's STALL_PROGRESS_REGEX=checkpoint never
  matches during normal operation (the underlying script only logs "checkpoint" every 20th day, not per-day). This is a
  distinct, deterministic bug that will keep self-killing every real run of this tool — the reap-zombies.sh log-path fix
  (already shipped, deployment-service@60d9f7e) was a real, worthwhile fix but did NOT cause and does NOT fix this
  incident. STALL_PROGRESS_REGEX in the launcher has been corrected in this session (deployment-service, pending ship)
  to "day=" (the tool's actual per-day log marker). The RELAUNCHED VM (backfill-defi-dex-swaps-20260803-103749, launched
  10:37:55Z) is running the OLD (pre-fix) metadata and is on track to hit the same stall-kill around 11:38-11:43Z.
status: open
nature: issue
asset_group: [defi, cross-cutting]
stage: [data, meta]
repos: [deployment-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, vm-lifecycle, stall-watchdog, false-positive, big-finding, data-pipeline, root-cause-correction, defi]
related:
  [
    /plans/active/issues/reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
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
  Surfaced 2026-08-03 (slot 6, infra) while executing reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md's todo
  2 (audit for other reap-zombies.sh false-positive kills).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md,
    /deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
    /market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py,
  ]
depends_on: []
---

# vm-exec's STALL_PROGRESS_REGEX=checkpoint self-kills every real dex-swaps source-correction run — corrects the reap-zombies.sh root-cause claim

## What I found

While executing `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md`'s todo 2 ("audit whether reap-zombies.sh
has ever been invoked against prod in a way that could have silently killed other healthy VMs"), I first confirmed via
`gcloud logging read` (30-day window, `v1.compute.instances.delete`, 20,691 total events project-wide) that the
gcloud-CLI/`from-script/True` signature matching the flagged incident's actor
(`uts-prd-sa@central-element-323112.iam.gserviceaccount.com`) accounts for 202 delete events (101 unique instances) over
the audited window — but EVERY sampled instance's own `vm-logs/<instance>/run.log` (a 12-instance random sample, checked
at the CORRECT canonical path) shows a clean, self-contained
`[vm-exec] ... VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete` sequence immediately after a genuine terminal
state (`DEPLOYMENT_COMPLETED`/`DEPLOYMENT_FAILED` with a real `exit_code`) — i.e. the documented, intentional
`VM_SHUTDOWN_ON_COMPLETION=true` self-delete convention (`deployment-service/scripts/vm/lib/launcher_common.sh` +
`vm-exec-with-gcs-tee.sh`), not an external reap-zombies.sh invocation. The caller-IP reuse across unrelated VMs (e.g.
one IP touching 7 different, temporally-scattered instance names over 2 days) is consistent with Cloud NAT IP-pool
sharing across many independent self-deletes, not a single centralized actor. **No evidence was found of
reap-zombies.sh's actual list+delete-loop pattern running against prod in the 30-day window.**

**Then I checked the ORIGINAL flagged VM's own log the same way** — and it directly contradicts the parent issue's
root-cause claim. `backfill-defi-dex-swaps-20260803-092530`'s `run.log` (read at
`gs://deployment-scripts-central-element-323112/vm-logs/backfill-defi-dex-swaps-20260803-092530/run.log`, the CORRECT
canonical path) ends with:

```
[vm-exec] WORKER_STALLED (no-progress-marker): no progress in 3639s (threshold=3600s) — killing CMD_PID=...
...
[vm-exec] DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=3639 threshold=3600
[vm-exec] VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete of backfill-defi-dex-swaps-20260803-092530 in asia-northeast1-c
```

This is `vm-exec-with-gcs-tee.sh`'s OWN internal stall watchdog (a documented, pre-existing mechanism — see its
extensive comments on two PRIOR false-positive-kill root causes, both already fixed: a SIGPIPE/ `tail`/`grep -q` race
and a byte-boundary line-splitting bug) deciding, entirely from WITHIN the VM using its own attached service account,
that the workload had produced no progress-marker match for `STALL_TIMEOUT_SEC=3600s`, then killing the workload and
self-deleting. The `gcloud compute instances delete` calls in the audit log (`10:30:57Z` and `10:31:48Z`, both from
`callerIp=136.110.126.79`) are this SAME self-delete firing (confirmed: that IP is the VM's own network egress,
consistent with the log's own narrated sequence) — NOT reap-zombies.sh reading an empty `logs/` path and reaping on
creation-time alone. The parent issue's own evidence for ruling out `vm_zombie_watchdog.py` (gcloud-CLI signature, not
the Python client) is real, but it missed this THIRD possibility — the VM's own `VM_SHUTDOWN_ON_COMPLETION` self-delete
ALSO uses gcloud CLI, non-interactively, under `uts-prd-sa` — identical signature to reap-zombies.sh.

**Root cause of the STALL false-positive**:
`deployment-service/scripts/vm/launch-backfill-defi-dex-swaps-source-correction-vm.sh` set
`STALL_PROGRESS_REGEX=checkpoint` (pre-fix), with a comment claiming `"checkpoint"` "recurs throughout a full --apply
run". This is wrong for this specific tool:
`market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py::run_remediate` only emits a
line containing `"checkpoint"` every 20th day
(`if i % 20 == 0: _write_checkpoint(...); logger.info("  checkpoint: %d/%d days done...")`) — the per-day summary line
itself (`"  day=%s: already_covered=%d needs_copy=%d ..."`) contains NO "checkpoint" substring. Fetched
`WATCHDOG_TRACE.log` for the flagged VM directly confirms this: **all 58 watchdog iterations across ~60 minutes show
`progress=0`**, even though `size=` (the on-VM log's byte count) grew monotonically the entire time (2147 → 86470 bytes)
— i.e. the VM was genuinely, continuously producing real output, but none of it ever matched
`STALL_PROGRESS_REGEX=checkpoint`. At the tool's observed per-day rate (~2-7 min/day, per the parent issue's own
monitoring), reaching day 20 takes 40-140 minutes — routinely exceeding `STALL_TIMEOUT_SEC=3600s` (60 min) before the
first checkpoint is ever written. **This makes the self-kill deterministic, not a rare race** — essentially every real,
uninterrupted `--apply` run of this tool will be killed by its own watchdog before completing its first checkpoint
cycle, unless a future run happens to process 20 days in under an hour.

**Fixed in this session** (deployment-service, not yet shipped as of this writing): `STALL_PROGRESS_REGEX=checkpoint` →
`STALL_PROGRESS_REGEX=day=`, matching the tool's actual per-day log marker (`"  day=%s: ..."`) — the same convention
every OTHER launcher in this fleet uses (a token that recurs on every processed item, not a periodic batch-checkpoint
token). See the updated comment at `launch-backfill-defi-dex-swaps-source-correction-vm.sh` for the full reasoning.

**Time-sensitive**: the RELAUNCHED VM from the original incident, `backfill-defi-dex-swaps-20260803-103749` (created
`2026-08-03T10:37:55Z`, confirmed `RUNNING` as of `11:25:45Z` in this session), was launched BEFORE this session's fix
and is running with the OLD `STALL_PROGRESS_REGEX=checkpoint` metadata baked in at boot (metadata is read once into a
shell env var at VM startup — a live `gcloud compute instances add-metadata` on the running instance will NOT reach the
already-running watchdog process). Its own `WATCHDOG_TRACE.log` shows the identical `progress=0` pattern across 42+
iterations as of this writing. **It is on track to self-kill via the same `WORKER_STALLED`/`no-progress-marker` path
around 11:38-11:43Z** — i.e., likely already dead or imminently about to die by the time this doc is picked up. No data
loss is expected (idempotent copy-based writes, per the parent issue's own analysis), but it will waste the elapsed
wall-clock time and needs a prompt relaunch WITH this session's launcher fix once it dies (todo 3 below).

## Why it matters

- **Directly corrects a shipped P0 fix's stated root cause.**
  `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md` todo 1 (deployment-service@60d9f7e, already shipped)
  fixed a REAL bug in `reap-zombies.sh` — the wrong log path is a genuine landmine and the fix should stay — but it did
  NOT cause, and does not prevent recurrence of, the incident that prompted the doc. Anyone relying on that doc's
  root-cause narrative (e.g. to argue "reap-zombies.sh is now safe, the fleet-wide false-positive-reap risk is closed")
  would be wrong on the specific incident that motivated it, even though the reap-zombies.sh fix is independently
  correct.
- **Deterministic, currently-recurring bug**: unlike a rare race, this will kill EVERY future run of
  `backfill_defi_dex_pool_swaps_source_correction.py --apply` (uninterrupted) under the pre-fix
  `STALL_PROGRESS_REGEX=checkpoint` config — confirmed actively in-progress on the relaunched VM as this doc is being
  written.
- **Same failure class as the reap-zombies.sh incident** (`data_engineering.md` VM-delete guardrail /
  `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`) but via a THIRD, previously-unaudited mechanism (the
  generic `STALL_PROGRESS_REGEX` stall watchdog, misconfigured for one specific launcher) — worth a broader sanity check
  (todo 2) of whether any OTHER launcher's `STALL_PROGRESS_REGEX` choice has the same "keyed to a periodic/rare token
  instead of a per-item token" mismatch, now that this failure mode is known.

## Recommended decision

- [x] ✅ [INFRA] P0. **Fix `STALL_PROGRESS_REGEX` in `launch-backfill-defi-dex-swaps-source-correction-vm.sh`** from
      `checkpoint` to `day=` (the tool's actual per-day log marker), and correct the stale comment that claimed
      `"checkpoint"` recurs throughout a run. (repo: deployment-service) — `deployment-service@b38130d`,
      `quality-gates.sh` green, quickmerge landed on `live-defi-rollout`, SHA verified ancestor of origin.
- [ ] [INFRA] P1. **Sanity-sweep every other launcher's `STALL_PROGRESS_REGEX` against its target script's actual log
      cadence** — for each of the ~12 launchers setting `STALL_PROGRESS_REGEX` (grep `deployment-service/scripts/vm/`
      for the metadata key), confirm the chosen token appears on essentially every processed item/day/shard, not just at
      a periodic checkpoint or a one-time startup line. Cross-reference against each target script's actual logging code
      (not just the launcher's own comment, which was WRONG in this exact case). File any additional mismatches found as
      follow-up todos in this doc. (repo: deployment-service)
- [ ] [INFRA] P0. **Monitor `backfill-defi-dex-swaps-20260803-103749` and relaunch promptly once it self-kills**
      (expected ~11:38-11:43Z per this doc's analysis, may have already happened by the time this todo is picked up) —
      verify via `gcloud compute instances describe ... --format='value(status)'` or its absence (self-delete removes
      the instance entirely), confirm the terminal state was `WORKER_STALLED` (not a genuine failure) via its
      `run.log`/`WATCHDOG_TRACE.log`, then relaunch via `launch-backfill-defi-dex-swaps-source-correction-vm.sh` (now
      carrying the `STALL_PROGRESS_REGEX=day=` fix from todo 1) to resume the
      `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` campaign without a third false-kill. (repo:
      deployment-service, market-data-processing-service)
- [ ] [DATA] P2. **Cross-link this doc's finding into `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md`'s
      remaining open todos (2-4)** — todo 2 there ("audit whether reap-zombies.sh has silently killed other healthy
      VMs") is effectively answered NO by this doc's audit (see "What I found" above); its todo 4 ("make the day-level
      checkpoint durable against an early kill") remains independently valid but is now understood to be a SEPARATE
      hardening improvement, not the fix for why the original VM died. Update that doc's Progress Log to reference this
      correction (this doc's own filing already cross-references it via `related:`; this todo is a light consistency
      pass, not new investigation). (repo: unified-trading-pm)

## Progress Log

- **2026-08-03T~11:30Z** (AO dispatch, slot 6, `infra`) — Filed while executing
  `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md` todo 2. Confirmed via direct GCS log reads (both the
  flagged VM's `run.log` + `WATCHDOG_TRACE.log`, and a 12-instance random sample of the broader `uts-prd-sa` delete
  population from a 30-day `gcloud logging read`) that the flagged incident was a self-inflicted `WORKER_STALLED` kill,
  not a reap-zombies.sh reap. Fixed the `STALL_PROGRESS_REGEX` misconfiguration in
  `launch-backfill-defi-dex-swaps-source-correction-vm.sh` (not yet shipped as of this Progress Log entry — see this
  doc's own commit). Flagged the currently-running relaunched VM as time-sensitive (todo 3). No GCS deletes/mutations
  performed — read-only investigation (log/audit-log reads, `gcloud compute instances describe`) plus the one
  launcher-script edit.
- **2026-08-03T11:42Z** (AO dispatch, slot 5, `infra`, todo 3) — Checked `backfill-defi-dex-swaps-20260803-103749`:
  status `RUNNING`, `run.log` actively advancing (`day=2023-04-05` as of 11:41:44Z, ~10-13s/day at the current point in
  the range vs. the ~2-7min/day this doc's estimate assumed), `WATCHDOG_TRACE.log` shows the (old, pre-fix)
  `STALL_PROGRESS_REGEX=checkpoint` token DID match twice recently (iter=54 at 11:36:42Z, iter=57 at ~11:39:55Z,
  `progress=1`) — the per-20-day checkpoint cadence is landing well inside the 3600s stall window at this run's actual
  pace, so the predicted ~11:38-11:43Z self-kill did **not** occur on this VM. Prediction was directionally correct (the
  bug is real and deterministic at the ~2-7min/day pace originally observed) but this run's per-day rate turned out
  faster than that estimate, so it may complete or hit further checkpoints without ever stalling — not yet provably safe
  for the FULL remaining ~1,300-day range if the per-day rate slows again later (e.g. denser days). Armed a bounded (6h,
  5min-poll) background watchdog (`dex_swaps_watchdog.sh`, this session) that detects a genuine self-delete,
  distinguishes `DEPLOYMENT_COMPLETED` (no action) from a stall/preemption kill (auto-relaunches via the now-fixed
  launcher and keeps tracking the new VM name). No GCS deletes/mutations performed this entry — read-only checks + one
  background monitoring process armed.
