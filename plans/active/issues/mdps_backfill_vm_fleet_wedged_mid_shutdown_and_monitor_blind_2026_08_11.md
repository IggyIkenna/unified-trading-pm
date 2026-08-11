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

## Follow-ups

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
      neither live nor wedged and were left alone.
