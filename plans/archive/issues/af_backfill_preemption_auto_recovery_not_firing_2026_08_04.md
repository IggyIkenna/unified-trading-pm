---
doc_type: issue
title: af-backfill-* SPOT preemption auto-recovery not firing within its 5-min cadence — 2x same-day recurrence
summary: >-
  Confirmed twice in one day (2026-08-03/04): the FIXTURE_STATS `af-backfill-*` VM was SPOT-preempted and no successor
  VM was auto-launched by `exit_code_fleet_monitor`'s PREEMPTED `auto_recover` actuator
  (`relaunch_backfill_vm.RelaunchPreemptedVm`) within multiple ticks of its 5-minute Cloud Scheduler cadence
  (`dp_exit_code_monitor_cron`, `*/5 * * * *`). Both times a human/agent had to manually relaunch. The wiring LOOKS
  correct on inspection (`af-backfill-` prefix registered in `launcher_registry.py`, `lc_write_launch_params` persists
  resume env, PREEMPTED relaunch budget is 48/day — nowhere near exhausted by 1-2 events), so this reads as a genuine
  runtime gap, not a missing-config issue. Root cause NOT YET DIAGNOSED — filing so it is tracked instead of silently
  re-discovered a third time (the gating doc below already flagged this twice as "out of scope, not chased further").
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-preemption, billing-waste, auto-recovery, sports, api-football, big-finding]
related:
  [
    /plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
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
resolved_by: deployment-service@16938c1
source:
  [
    "sports_af_full_entity_completion-003 (slot 6), 2026-08-04 — found while re-verifying the FIXTURE_LINEUPS launch
    gate",
  ]
drift_direction: advance-code
context_scope:
  [
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    deployment-service/terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf,
    deployment-service/scripts/vm/launch-api-football-backfill-vm.sh,
  ]
---

# af-backfill-* SPOT preemption auto-recovery not firing

## What I found

Working `sports_af_full_entity_completion-003` (launch FIXTURE_LINEUPS after FIXTURE_STATS converges), re-verified the
gate before launching (per the recurring-risk note already in the gating doc): FIXTURE_STATS had not converged
(125/68,409 non-MVP shards captured — essentially flat). Checked why: the FIXTURE_STATS VM slot 4 had relaunched ~6
hours earlier (`af-backfill-20260804-001203`, launched 2026-08-04T00:12:03Z) was **gone entirely** —
`gcloud compute instances list` shows no trace of it at all (not even TERMINATED — the launcher sets
`--instance-termination-action=DELETE`, so a preempted instance self-deletes rather than parking).

Confirmed via audit log:

```
gcloud logging read 'protoPayload.methodName="compute.instances.preempted" ...'
2026-08-04T00:18:31Z  .../instances/af-backfill-20260804-001203
2026-08-04T00:18:20Z  .../instances/af-backfill-20260804-001203
```

So this VM ran only ~6 minutes before being preempted. By the time I checked (~2026-08-04T00:25-00:30Z, i.e. 1-2 ticks
past the `*/5 * * * *` `dp_exit_code_monitor_cron` schedule), **no successor VM had been launched.** This is the
**second** occurrence of the exact same shape for the exact same entity in under 24h — the gating doc's own Progress Log
(`sports_af_full_entity_completion_2026_08_03.md`) already records a first instance: `af-backfill-20260803-233053`
preempted 2026-08-03T23:47-48Z, also never auto-recovered, manually relaunched by a worker ~25 min later
(2026-08-04T00:12Z, itself now also preempted per above).

**Ruled out as the cause** (so a future investigator doesn't re-check these):

- **Registry wiring**: `launcher_registry.py:301` — `"af-backfill-": "launch-api-football-backfill-vm.sh"` is present
  and correct.
- **Relaunch budget**: PREEMPTED relaunches use `_MAX_PREEMPTION_RELAUNCHES_PER_DAY = 48` (`relaunch_backfill_vm.py`) —
  nowhere near exhausted by 1-2 events/day. (Not the separate, much stricter OOM budget of 2/day — different namespace,
  confirmed by reading the code.)
- **Resume-env persistence**: `launch-api-football-backfill-vm.sh:502-517` calls `lc_write_launch_params` with
  `RESUME_ENTITY`/`RESUME_START_DATE`/`RESUME_END_DATE` on every launch, so the relaunch actuator has what it needs to
  replay a resume.
- **Scheduler cadence**: `data_pipeline_fleet_monitor_scheduler.tf:216` — `dp_exit_code_monitor_cron` runs
  `*/5 * * * *`. 1-2 ticks elapsed with no action.

**Not yet checked** (genuinely unknown, needs the next investigator):

1. Whether `dp_exit_code_monitor_cron`'s Cloud Run Job invocations are actually succeeding (vs silently erroring — the
   monitor's own docstring notes a "never-raises" broad-except pattern around its GCS/compute I/O, flagged separately in
   `QUALITY_GATE_BYPASS_AUDIT.md` §2.19 — worth checking Cloud Run job execution logs/history for this specific job
   around 2026-08-03T23:50Z and 2026-08-04T00:20Z for silent failures).
2. Whether the PREEMPTED durable signal blob (written by the VM's own `shutdown-script` in the ~30s GCE preemption
   warning window) is actually landing in GCS before `--instance-termination-action=DELETE` tears the VM down — a race
   between the shutdown-script write and the delete could mean the monitor's census-diff never sees a `PREEMPTED` marker
   at all, silently falling through to a different (or no) classification branch.
3. Whether the monitor's per-tick census snapshot happened to run in the ~6min window the VM was alive, or whether a VM
   that lives <5min (one scheduler tick) is invisible to the prior-tick/this-tick diff entirely
   (`af-backfill-20260804-001203` ran ~6 min — right at the edge of one 5-min tick, plausible that it was never captured
   as "RUNNING" in a prior census snapshot before it was already gone, in which case the "present in PRIOR census but
   GONE this tick" diff condition the monitor relies on never fires).

Hypothesis (3) is the most promising thread — a VM whose full lifetime is shorter than the monitor's poll cadence would
be structurally invisible to a diff-based detector, which would explain BOTH occurrences (both VMs died in ~6-17
minutes, well under or barely past one 5-min tick).

## ✅ RESOLVED 2026-08-04 — root cause: `af-backfill-`/`af-audit-` missing from `_DATA_VM_PREFIXES`

Checked (1) directly first (`gcloud run jobs executions list --job=uts-prod-dp-exit-code-monitor`): every 5-min tick
since 22:00Z **succeeded** (`SUCCEEDED_COUNT=1`, no failures) — the job runs fine, ruling out a silent Cloud Run
execution failure.

Read the actual `dp-fleet-monitor` logs for the ticks bracketing the 00:18:20-31Z preemption
(`gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-dp-exit-code-monitor" ...'`
— required switching the active gcloud identity from `github-deploy@...` to `unified-trading-sa@...`, which had the
missing log-viewer capability; both are ambient worker identities per RULES.md §5, no new grant needed). The 00:20
tick's `exit-code sweep: 10 terminated, 9 non-clean (...)` line **never mentions `af-backfill-20260804-001203` at all**
— it's entirely absent from the sweep's classified-VM list. The ONLY mention of that VM anywhere in the monitor's logs
is:

```
2026-08-04T00:25:47Z  reap_stale: archived ee6027ce-... (vm=af-backfill-20260804-001203, reason=vm_not_running)
```

— a completely SEPARATE code path (`DeploymentsRegistry.reap_stale()`, `cli.py:653`, wired to the UNFILTERED
`all_running_vms` census) that only archives the stale deployment-registration JSON and has **zero relaunch logic**. The
same pattern held for the first preemption (`af-backfill-20260803-233053` → `reap_stale` only, at 23:55:45Z).

**Root cause found in `cli.py`**: `exit_code_fleet_monitor.sweep()` — the ONLY code path that can classify a VM
`verdict=preempted` and trigger `RelaunchPreemptedVm` — is called with
`running_vms=[vm for vm in all_running_vms if _is_data_vm(vm[0])]` (`cli.py:610`), a FILTERED subset. `_is_data_vm()`
requires either an asset_group substring match (`_asset_group_for_vm`, checks for
`cefi`/`defi`/`tradfi`/`sports`/`prediction` as a substring) OR a listed prefix in `_DATA_VM_PREFIXES`.
**`af-backfill-*`/`af-audit-*` VM names contain neither** — no asset_group substring (the name is just
`af-backfill-<timestamp>`) and the prefix list was missing `"af-backfill-"`/`"af-audit-"` entirely. So these VMs were
**structurally invisible** to the classifier from day one — this had nothing to do with VM lifetime/tick-cadence timing
(hypothesis 3 above); every single af-backfill-_/af-audit-_ preemption, ever, would have hit this same silent gap.

**Fixed**: added `"af-backfill-"` and `"af-audit-"` to `_DATA_VM_PREFIXES`
(`deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`), with a unit-test regression
(`test_is_data_vm_filters_infra`) covering both prefixes. Full QG green, shipped via quickmerge.

## Why it matters

- **Billing waste**: every preempted VM that silently dies burns SPOT compute for zero net progress until a human
  happens to notice and relaunch.
- **Business-goal-critical**: the operator's explicit ask (`sports_af_full_entity_completion_2026_08_03.md`) is full AF
  entity completion so the API-Football subscription tier can be downgraded — a stalled-and-unnoticed campaign directly
  delays that. FIXTURE_STATS has now lost ~25-30+ min of runway twice in one day to this gap alone.
- **Pattern repeats across asset groups**: `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` documents the
  same failure shape (SPOT VM preempted, wrote no checkpoint, sat dead ~2 days) for a different launcher family — this
  may not be an af-backfill-specific bug but a shared gap in the exit-code/preemption monitor's detection window.

## Recommended decision

Someone with Cloud Run Jobs execution-log access should check hypothesis (1) and (2)/(3) above directly (execution
history for `dp_exit_code_monitor_cron` around the two preemption timestamps, and the raw GCS object listing under
`vm-logs/af-backfill-20260803-233053/` and `vm-logs/af-backfill-20260804-001203/` for whether a `PREEMPTED` blob was
ever written) before attempting a code fix — the three "not yet checked" items above are diagnostic reads, not code
changes, and should resolve which of them is the real cause.

## Todos

- [x] ✅ [SCRIPT] P1. ~~Check Cloud Run Jobs execution history for `dp_exit_code_monitor_cron`~~ — DONE 2026-08-04:
      every 5-min tick since 22:00Z succeeded (`gcloud run jobs executions list`, `SUCCEEDED_COUNT=1` throughout, no
      failures) — ruled out a silent execution failure. See "RESOLVED" section above.
- [x] ✅ [SCRIPT] P1. ~~Read the raw GCS objects for a PREEMPTED signal blob~~ — SUPERSEDED 2026-08-04: root cause found
      via a more direct path (the monitor's own logs) before this check was needed — the VMs were never even reaching
      the classification step that would read that blob. See "RESOLVED" section above.
- [x] ✅ [SCRIPT] P1. **Root cause found + fixed 2026-08-04** — NOT hypothesis (3) (tick-timing); actual cause:
      `af-backfill-`/`af-audit-` missing entirely from `_DATA_VM_PREFIXES` (`cli.py`), so `_is_data_vm()` excluded these
      VMs from `exit_code_fleet_monitor.sweep()`'s classification universe — structurally invisible to
      `verdict=preempted`, regardless of timing. Fixed: `deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`
      (added both prefixes + regression test `test_is_data_vm_filters_infra`). QG green, shipped via quickmerge,
      verified on origin. See "RESOLVED" section above.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-04 (slot 12)** — `deployment-service@16938c1`. Cross-referenced EVERY
      `launcher_registry.LAUNCHER_FOR_VM_PREFIX` entry with a real (non-None) relaunch launcher — i.e. every genuinely
      auto-relaunchable data VM — against `cli._is_data_vm()` (ASSET_GROUPS substring OR `_DATA_VM_PREFIXES`
      membership). Found **29 more prefixes with the identical gap**: a real launcher, but a VM name carrying no
      cefi/defi/tradfi/sports/prediction substring and not in `_DATA_VM_PREFIXES` — af-recover-, aster-fwd-,
      blank-reason-recon-, deribit-opts-fwd-, dvol-deribit-, expected-universe-v2-, feat-orph- (covers feat-orph-bf- by
      prefix), features- (covers features-xc-), fill-missing-player-stats-, footystats-fwd-, fss-backfill-vm-,
      governance-backfill-, instr-backfill-pred, jito-solana-backfill-, marinade-backfill-, ml-orph-, opt-cboe-,
      opt-cme-, opt-deribit-, opt-okx-, pyth-lst-backfill-, replay-, scenario-matrix-, sfi-backfill-, sfi-fwd-,
      strat-orph-, tm-forward-poll-, us-backfill-, us-forward-poll-. Verified each against the actual launcher script's
      `VM_NAME=` construction (not just the registered prefix string) for the ambiguous cases — `feat-orph-`/
      `feat-orph-bf-` was the sharpest example of why prefix-membership can't be inferred from "usually contains the
      asset group": their VM names embed `ASSET_GROUP_ABBREV`, which passes cefi/defi/sports through literally but
      remaps tradfi->tfi, prediction->pred, and no `--asset-group` at all -> `gl`, so only 3 of 5 asset-group cells
      accidentally matched via substring — the other 2 (+ the global family) were silently invisible regardless of the
      `_DATA_VM_PREFIXES` fix.

      Cross-referenced `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` per this todo's own pointer: that
                          incident is a **different root cause**, not this one — `cefi-queue-*` VM names already contain `cefi` and were
                          always visible to `_is_data_vm()`; that doc's chain of preemptions instead traced to missing `PROGRESS.json`
                          checkpoint emission + a `VM_TASK` collision + a `WORKER_STALLED` watchdog kill. Same failure SHAPE
                          (preempted/killed, no auto-recovery), genuinely different mechanism — noting this here so a future investigator
                          doesn't assume they're the same bug.

                          **Fix**: added all 29 prefixes to `_DATA_VM_PREFIXES`, split into a new `vm_classification.py` module (the
                          addition pushed `cli.py` to 975 lines, over the repo's 930-line `MAX_FILE_LINES` gate — extracted
                          `_asset_group_for_vm`/`_is_data_vm`/`_DATA_VM_PREFIXES` following the same precedent as `meta_targets.py`'s
                          2026-07-13 split; `cli.py` re-imports them aliased to their original names so every existing call site, incl.
                          tests, is unchanged). Added a permanent regression guard,
                          `test_data_vm_prefixes_cover_every_relaunchable_launcher`, asserting every CURRENT AND FUTURE
                          `LAUNCHER_FOR_VM_PREFIX` entry with a real launcher resolves `True` through `_is_data_vm()` — closes this bug
                          class going forward, not just today's 31 instances. Full `deployment-service` `quality-gates.sh` green (230s,
                          sentinel matches `16938c1`), 313/313 unit tests pass. Shipped via quickmerge, verified on origin.

## Progress Log

- **2026-08-04 (slot 6)** — Filed while working `sports_af_full_entity_completion-003`. Manually relaunched
  FIXTURE_STATS as `af-backfill-20260804-002608` (safe idempotent resume, no `--force`) to keep the sports campaign
  moving; did NOT chase the auto-recovery root cause further in that task (out of its scope) — filed here instead so
  it's tracked rather than re-discovered a third time.
- **2026-08-04 (slot 6)** — Dispatched todo 1 of this doc. Root-caused and fixed in the same turn (see "RESOLVED"
  section above): `af-backfill-`/`af-audit-` were entirely missing from `_DATA_VM_PREFIXES`, making these VMs invisible
  to the exit-code sweep's classification regardless of timing — not the tick-timing hypothesis originally suspected.
  Shipped `deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`. Only the P2 cross-check todo (other
  VM_PREFIX_TO_BUCKET families) remains open; this doc is not yet fully closed pending that.
- **2026-08-04 (slot 8)** — Answered todo #2's literal question directly (the checkbox was already flipped SUPERSEDED by
  slot 6 before this read ran, so it stays flipped — this is the corroborating evidence, not a re-flip). Listed both
  `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/` prefixes: **NO `PREEMPTED` blob was ever written for
  either VM** — each prefix holds only `LAUNCH_PARAMS.json` / `PROGRESS.json` / `WATCHDOG_TRACE.log` / `run.log`.
  Confirmed the shutdown-script (`lc_write_preemption_signal_file`, `scripts/vm/lib/launcher_common.sh`) targets exactly
  that path (`vm-logs/${VM_NAME}/PREEMPTED` in `deployment-scripts-${PROJECT}`), so the absence is genuine, not a
  wrong-path lookup. Timestamps (relative to the delete/preempt audit-log op): `af-backfill-20260803-233053` last GCS
  write 23:46:56Z → `compute.instances.preempted` op first=23:47:54.18Z / last=23:48:03.90Z (~58s gap);
  `af-backfill-20260804-001203` last GCS write 00:17:56Z → op first=00:18:20.42Z / last=00:18:31.71Z (~24s gap). This is
  DISTINCT from (and does not contradict) the `_DATA_VM_PREFIXES` root cause: even now that the classifier fix lets
  these VMs be swept, their verdict will lack the clean `PREEMPTED` blob signal and must lean on the op-checker /
  `PARTIAL_UNCONFIRMED` fallback. The marker is absent **2/2 even after** the 2026-07-26 switch to the hardened
  `lc_write_preemption_signal_file` helper, so that hardening did not close the grace-period race. Not filing a new todo
  — this is already the open P3 audit in
  `/plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` ("Audit whether the `PREEMPTED`
  marker's shutdown-script grace period is survivable in practice"); appended these two datapoints as evidence to that
  doc's Progress Log for the auditor.
