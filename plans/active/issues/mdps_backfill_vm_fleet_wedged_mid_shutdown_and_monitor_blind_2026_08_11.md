---
doc_type: issue
title:
  651 running VMs — 398 wedged mid-shutdown since 06:00-07:00 UTC while the exit-code fleet monitor times out at 1800 s
  and only ever observes 18 of them
summary: >-
  Measured 2026-08-11: the project had 651 RUNNING GCE instances against a launcher designed for ~28 (one per
  asset_group x year). 398 of them had hung part-way through an orderly shutdown — every one's last serial-console line
  is `Stopping rsyslog.service` / `Stopping polkit.service` / `Stopping multipathd.service`, all between 06:05 and 06:53
  UTC — yet GCE still reports them RUNNING, so they bill CPU and a 250 GB boot disk each while doing nothing. The
  `uts-prod-dp-exit-code-monitor` Cloud Run job that should catch this is itself broken: it hits its 1800 s task timeout
  every execution, so in six hours it emitted verdicts for only 18 distinct VMs, NONE of them in the live fleet, and its
  */5 executions overlap — the exact empty-budget-per-container condition `relaunch_backfill_vm.py` documents as the
  cause of the 2026-08-09 relaunch storm. 393 wedged backfill VMs were deleted under operator authorisation; 4 wedged
  LIVE producers were deliberately excluded and need a restart, not a delete.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [vm-fleet, billing-waste, monitoring, relaunch-actuator, spot, P1]
related:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    deployment-service/scripts/vm/reap_vms.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
  ]
created: "2026-08-11"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Interactive session 2026-08-11 slot 1, found while checking whether the liquidations re-drive prerequisite had
  cleared. Every number below is from `gcloud compute instances list`, per-VM serial-console reads, and `gcloud logging
  read` on the monitor job — not inferred.
---

# The backfill VM fleet wedged, and the monitor that should have caught it is blind

## What was measured (2026-08-11, 14:30-15:30 UTC)

| Signal                                               | Value                                                          |
| ---------------------------------------------------- | -------------------------------------------------------------- |
| RUNNING instances in `central-element-323112`        | **651** (639 SPOT, 12 STANDARD)                                |
| Design intent for the sharded launcher               | ~28 (one VM per asset_group x year)                            |
| Duplicates per year-shard                            | up to **36** (`mdps-cefi-2022`), ~50 counting deleted siblings |
| Wedged mid-shutdown                                  | **398**                                                        |
| Wedge window                                         | 06:05-06:53 UTC, a single hour, across every family            |
| Guest-alive (serial output within the minute)        | 214                                                            |
| Probe inconclusive                                   | 39                                                             |
| Instances launched since 2026-08-09                  | 623, none self-deleted                                         |
| Monitor executions                                   | every 5 min, **every one hits the 1800 s task timeout**        |
| Distinct VMs the monitor emitted a verdict for (6 h) | **18** — and **zero** of them were in the running fleet        |

## Why the wedge is the expensive part

`VM_SHUTDOWN_ON_COMPLETION=true` is supposed to make a finished backfill VM disappear. These VMs began an orderly
shutdown and never finished it: the last serial line is a `Stopping <unit>` from the shutdown sequence, and GCE has
reported them RUNNING for ~9 hours since. A VM in that state bills CPU + its 250 GB boot disk and produces nothing.

Order-of-magnitude cost while it lasted (list pricing, NOT billing data — re-measure before quoting it anywhere):
~$45/hr compute across 640 spot instances, plus ~160 TB of attached boot disk at roughly $500/day. The disk, not the
CPU, is the dominant term.

## Why the monitor could not catch it

`uts-prod-dp-exit-code-monitor` iterates the fleet serially at roughly 10 s per VM. At 651 VMs that is ~1.8 hours of
work against a **1800 s task timeout**, so every execution is killed part-way through the same early portion of the
list. Consequences, all measured:

1. **It never reaches the live fleet at all.** Six hours of logs contain verdicts for 18 distinct VMs, every one of them
   an already-deleted `20260810-*` instance. The 651 running VMs are invisible to it.
2. **Executions overlap.** A */5 schedule against a 30-minute run means ~6 containers alive at once — precisely the
   condition `relaunch_backfill_vm.py`'s own comment blames for the 2026-08-09 relaunch storm ("several containers were
   each retrying with their own empty budget").
3. **The feedback loop is self-reinforcing.** More VMs → slower sweep → more overlap → more relaunches → more VMs.

The `_MAX_RELAUNCHES_PER_DAY = 2` budget cannot hold under (2): `vm_prefix()` longest-prefix-matches
`VM_PREFIX_TO_BUCKET`, so every `mdps-cefi-*` year shares one budget key and the cap should be 2/day for the whole
family. Observed: ~50 launches per year-shard over two days. Whether the GCS-backed `_ShardedState` fix
(`_STATE_ROOT_BUDGET = "vm-census/relaunch-budget"`, shipped in deployment-service@0c38c00d) has actually reached the
deployed image is NOT yet verified — the job runs `deployment-api:latest` and the image build time was not checked.

## Remediation done under operator authorisation (2026-08-11)

**393 wedged backfill VMs deleted.** Selection was evidence-based, not name-based: a VM qualified only if its last
serial-console line predated 14:00 UTC (i.e. it was not merely quiet — it had stopped logging hours earlier), and the
tail was spot-checked on five singletons plus three family representatives to confirm a `Stopping <unit>` shutdown
sequence rather than in-progress work. Zero overlap with the guest-alive set was asserted before any delete. Backfills
are idempotent and resume from their progress checkpoint, so deleting a hung one loses no work — and a VM hung
mid-shutdown could not have resumed anyway. The name list is preserved for audit.

**Method note worth keeping**: serial-console recency is a proxy for GUEST liveness, not for backfill progress — the
"alive" VMs' recent output is only the `snap.google-cloud-cli.gcloud-*.scope` heartbeat cycling every ~10 s. It proves
the box is up. It does not prove MDPS is doing anything. The wedge verdict is solid because a `Stopping <unit>` line is
unambiguous; the liveness verdict is not, and was deliberately not used to justify any delete.

## The deletion triggered a relaunch burst — cause attribution (2026-08-11 15:44-15:51 UTC)

**Deleting the 393 wedged VMs made the monitor relaunch them.** A deleted VM reads to `exit_code_fleet_monitor` as
`terminated with NO durable exit marker but captured climbed` — the `PARTIAL_UNCONFIRMED` verdict, which `_classify.py`
deliberately auto-recover-routes "via the SAME resume-from-checkpoint relaunch as PREEMPTED" so a genuine partial run
self-heals. That routing is correct in its intended case; it simply cannot distinguish "preempted mid-run" from "an
operator reaped a corpse". Measured effect: the fleet went **250 → 364 in about six minutes**, in whole-launcher
fan-outs (several VMs sharing one timestamp suffix, e.g. `...-154435` across every year, i.e.
`launch-mdps-sharded-backfill.sh` invoked wholesale rather than a per-VM relaunch). The `_MAX_RELAUNCHES_PER_DAY = 2`
budget did not stop it, which is further evidence the deployed image's budget is not actually durable.

Stopped in three steps, each verified: schedule `*/5` → `0 * * * *` (15:44Z), scheduler **PAUSED** (15:46Z), then all
six in-flight executions **cancelled** (15:50-15:51Z) — pausing alone was not enough because an execution runs up to its
1800 s timeout and keeps relaunching the whole time. Last launch 15:51:07Z; zero launches after that, confirmed at
15:53Z. Fleet settled at ~358.

The sibling `uts-prod-dp-heartbeat-watcher` was checked and deliberately **left running**: it reports
`heartbeat sweep: 272 running, 0 stalled` and exits 0 in seconds. It is healthy and is not a relaunch source.

**⚠️ STANDING STATE — the exit-code monitor is PAUSED.** Genuine spot-preemption recovery is therefore OFF fleet-wide.
This is a deliberate hold, not a fix, and it must be reversed as part of the bounded-sweep work below.

**Operator ruling 2026-08-11 (recorded in this doc): KEEP IT PAUSED** until the classifier can tell a deliberate delete
from a partial run. Rationale accepted at decision time: backfills resume from their progress checkpoint on the next
launch regardless, so a paused preemption-recovery loop delays recovery rather than losing work — whereas unpausing now
would resume relaunching the 393 deleted VMs against a per-prefix budget whose durability in the deployed image is still
unverified. The unpause is gated on the P0 below, not on elapsed time.

## Second remediation — duplicate-year-shard prune (2026-08-11, continuation session)

**Operator ruling: "prune the duplicates, wasting money" — executed same session.** Found while checking the
liquidations P0 re-derive prerequisite (`/plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`): the
fleet had grown BACK to 485 total / 467 RUNNING instances (up from the ~358 this doc's first remediation settled at),
confirming the wedge/duplication pattern recurred rather than the fleet self-healing.

**Verified safe before touching anything**:
`gcloud scheduler jobs describe uts-prod-dp-exit-code-monitor-cron --location=asia-northeast1` returned
`state=PAUSED, schedule="0 * * * *"` — the standing hold from the first remediation is still in effect, so a delete
cannot trigger the same relaunch-storm this session (the monitor isn't consuming terminate events at all right now).

**Selection, evidence-based (grouped, not name-based)**: grouped all RUNNING instances by name with the trailing
`-YYYYMMDD-HHMMSS` run-ts stripped (47 distinct groups: `mdps-{cefi,tradfi,defi,sports}-{year}` × several years each,
plus a handful of genuinely-singleton jobs with no duplication). Per group with N>1, kept the MOST RECENTLY CREATED
instance (maximizes the chance it's running current code, e.g. the `contract_size` fix that landed hours earlier) and
reaped the rest — **411 duplicate VMs across the 47 groups**, up to 42 duplicates in a single group (`mdps-cefi-2019`).
Spot-checked 2 of the 47 kept VMs' serial console: both showed a live guest heartbeat (not wedged) — confirms the "keep"
pick, per the FIRST remediation's own caveat, is a liveness check not a progress check, and that's what was verified.
Explicitly excluded (never touched): 8 `-live-` producer VMs, 1 `vm-zombie-watchdog`, 1 `af-backfill-*` — different
action class per this doc's existing P1 (live producers need restart, not delete).

**Executed via the sanctioned tool, not a raw delete**:
`deployment-service/scripts/vm/reap_vms.py --vms-file <411 names> --zone asia-northeast1-c` (tombstone-then-delete, the
exact mechanism this doc's first P0 shipped to close the relaunch bug — `GCP_PROJECT_ID` had to be exported for the run,
the script doesn't read it from `gcloud config`). Result: **tombstoned 411/411**, deleted in 14 batches of ≤30. One
batch logged a non-zero exit despite every instance in it actually deleting (confirmed by content — the "FAILED" line's
own body was a list of successful `Deleted [...]` lines) — a script-quality nit, not a real failure; verified by
re-listing the live fleet afterward and finding **zero** of the 411 targeted names still present. **Fleet: 485 total /
467 RUNNING → 69 total / 51 RUNNING.** 5 of the 47 "kept" VMs were also gone on the post-check, but NOT because this
reap touched them — they were absent entirely (not merely `TERMINATED`), consistent with
`VM_SHUTDOWN_ON_COMPLETION=true` self-deleting on a genuine finish in the few minutes between the pre- and post-
snapshots (e.g. `betfair-egress-probe`, single-symbol `tradfi-bf-cme-ohlcv-1m-*` jobs — small, fast jobs finishing
mid-operation is plausible). Full name list:
`/plans/active/issues/vm_reap_lists/reaped_duplicate_year_shards_2026_08_11.txt`.

**Not done as part of this pass** (scope was explicitly "prune duplicates", not the open P0/P1s below): the monitor
stays PAUSED, the wedge root cause is still unknown, and the 47 "keep" VMs were not verified for backfill PROGRESS (only
guest liveness on 2 samples) — a future check should confirm they're actually advancing, not merely alive.

## Follow-ups

- [x] ✅ [SCRIPT] P0. **Taught the recovery path the difference between a preempted VM and a reaped one** —
      deployment-service@ecd6d2bd90. `vm-logs/{vm}/REAPED` tombstone + `is_vm_reaped` (mirrors the existing `PREEMPTED`
      marker: bounded `blob_exists`, never raises, fails toward not-reaped so a read error costs a spurious relaunch
      rather than silently suppressing recovery for a genuinely preempted VM); a `REAPED` verdict checked FIRST, ahead
      of `preempted`, because a reaped spot VM can still carry a stale `PREEMPTED` blob and PREEMPTED relaunches;
      `_finding_for` returns `None`, which is what withholds the relaunch since the escalation tier rides on the
      finding. `scripts/vm/reap_vms.py` writes the tombstone BEFORE deleting (order is load-bearing — the reverse leaves
      the relaunch window open) with `--tombstone-only` for VMs already deleted. 5 tests including a negative control
      asserting the SAME VM shape without a tombstone still classifies `PARTIAL_UNCONFIRMED`, so the positive test
      cannot pass for the wrong reason. Evidence: gate green, 3,322 passed, basedpyright 1259/1259 (ratchet held, not
      raised); `_gcs.py` 982 → 939 via the `_vm_markers` leaf split rather than raising the 960-line cap.
- [ ] [SCRIPT] P0. **UNPAUSE `uts-prod-dp-exit-code-monitor-cron` — BLOCKED on deploy + tombstone backfill, in that
      order.** The code is on LDR but landing on `main` deploys nothing: the monitor runs `deployment-api:latest` via
      Cloud Build, so (1) wait for the image to carry `ecd6d2bd90`, (2) run
      `reap_vms.py --tombstone-only --vms-file /plans/active/issues/vm_reap_lists/reaped_vms_2026_08_11.txt` (the exact
      393 names, committed alongside this doc so the list outlives the session that produced it) — they were deleted
      before the tool existed and still have no tombstones, so unpausing first would replay the exact burst — then (3)
      unpause. Doing these out of order re-creates the incident.
- [ ] [SCRIPT] P1. Make `exit_code_fleet_monitor` bounded and complete: it must either finish a full fleet sweep inside
      its task timeout (parallelise the per-VM probe, or page the fleet across executions with a durable cursor) or
      loudly report that it did NOT complete. A monitor that silently covers 3% of the fleet is worse than none — it
      reports green by omission. Evidence: 18 distinct VMs verdicted in 6 h against 651 running.
- [ ] [SCRIPT] P1. Stop `*/5` executions overlapping — set the Cloud Run job's concurrency to 1 (or take a lease), so
      the relaunch budget is consulted by ONE container at a time. The empty-budget-per-container race is already
      documented in `relaunch_backfill_vm.py`; the schedule still permits it.
- [ ] [SCRIPT] P1. Find why ~398 VMs hung mid-shutdown inside one hour (06:05-06:53 UTC 2026-08-11). A mass simultaneous
      wedge across every asset_group points at a shared trigger — a coordinated spot-preemption wave, a metadata/agent
      update, or the shutdown script itself blocking. Until this is understood the deletion is treatment, not cure.
- [ ] [SCRIPT] P1. Make a VM that has begun shutting down actually go away: the shutdown path must end in an instance
      DELETE (or a watchdog must reap instances whose guest has been in shutdown for more than N minutes), so a hung
      unit can never leave a billing instance behind.
- [ ] [OPERATOR] P1. Four LIVE producers are wedged and were deliberately NOT deleted — `mdps-features-live-cefi` and
      `mdps-features-live-defi` (last serial output **2026-08-09T00:00**, so ~2.5 days dead),
      `mtds-live-cefi-consolidated` and `mtds-live-tradfi-cme-trades` (2026-08-11T06:xx). These need a restart and an
      investigation of what live data was missed, not a delete. Restarting a live producer is a different action class
      from reaping a backfill.
- [ ] [SCRIPT] P2. Verify whether deployment-service@0c38c00d's GCS-backed relaunch budget is in the deployed
      `deployment-api:latest` image the monitor job runs. The fix is on the branch; the image build time was never
      checked, so the cap may still be reading an empty per-container tempdir in production.
- [ ] [SCRIPT] P2. Re-probe the 39 VMs whose serial-console read returned no parseable timestamp — they are classified
      neither live nor wedged and were left alone. Tool: `deployment-service/scripts/vm/probe_vm_serial_liveness.sh`
      (promoted from this incident's diagnostic session, read its header before trusting a fresh timestamp as more than
      guest-alive).

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (5 entries).

- **data_pipeline_failure escalation `agt-68d94a` (2026-08-12, slot 5)**: dispatched via `rb_infra_relaunch.md` with
  `CONTEXT=CRITICAL DP_VM_EXIT_NONZERO (DP-VM-001) — VM mdps-cefi-2019-20260810-023141 terminated with exit_code=1 ... RELAUNCH`.
  Did **NOT** relaunch — this VM (and this exact shard, `mdps-cefi-2019`/CeFi) is the SAME pattern this doc already
  tracks, confirmed still live 2 days later:
  - `DeploymentsRegistry.list_recent_archive(days=3)` shows **76 archived `mdps-cefi-2019-*` deployments, ALL
    `status=failed exit_code=125`**, spanning 2026-08-10T04:38Z-23:16Z (deployment_ids `a9a06d5d`..`f9ac35c7`, full list
    in registry, not reproduced here) — i.e. the relaunch-storm this doc documents for the fleet generally is STILL
    producing dozens of same-shard failures for this specific prefix, not merely the 2026-08-11 06:05-06:53Z wedge
    window this doc's "measured" table covers.
  - `DeploymentsRegistry.list_active()` shows **3 concurrently RUNNING `mdps-cefi-2019-*` VMs right now**
    (`mdps-cefi-2019-20260811-212851` started 21:31Z 08-11, `mdps-cefi-2019-20260811-222436` started 22:26Z 08-11,
    `mdps-cefi-2019-20260812-012210` started ~01:22Z 08-12) — confirmed via serial-console read that the first two are
    running the byte-identical command (`--start-date 2019-01-01 --end-date 2019-12-31`, `MDPS_ASSET_GROUP=CEFI`), i.e.
    genuine duplicate/redundant compute on the same shard, consistent with this doc's "Second remediation" section
    (mdps-cefi-2019 had up to 42 duplicates pruned 2026-08-11) — the duplication has regrown since that prune.
  - `gcloud scheduler jobs describe uts-prod-dp-exit-code-monitor-cron` confirms **still `state=PAUSED`** (the standing
    hold from this doc's first remediation) — so this specific relaunch dispatch did not originate from the paused cron;
    it reads as either a queued/delayed escalation from before the pause, or a separate actuator path
    (`RelaunchBackfillVm`) not covered by the cron pause. Not chased further — out of scope for a one-shot relaunch
    worker and orthogonal to the "should I relaunch" decision.
  - Per `rb_infra_relaunch.md`'s own bound ("if the registry archive shows ≥2 relaunches of this prefix today, do NOT
    relaunch again; page the operator") and this doc's own operator ruling ("prune the duplicates, wasting money"),
    launching a 4th VM for this shard would be the exact anti-pattern this doc exists to stop, not a fix. Precedent:
    `/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md` — a prior DP-VM-001 worker
    also found its target VM already superseded by a supervising loop and correctly declined to relaunch.
  - Did NOT attempt to fix `exit_code=125`'s root cause (out of scope/too large for a one-shot dispatch; the run.log
    tail for a sampled failure, `mdps-cefi-2019-20260810-231350`, ends mid-candle-aggregation with no
    `=== VM EXIT rc=... ===` trap line ever written, suggesting a hard SIGKILL/preemption rather than an
    application-level error — consistent with, not yet proof of, this doc's open P1 "why ~398 VMs hung" investigation)
    and did NOT kill either duplicate VM (no destructive action without a clearer instruction than "relaunch," and
    reaping is already this doc's own tracked P0/P1 territory). No code shipped this session; this Progress Log entry is
    the only change. `/done` posted with `one_shot_complete: true`.
