---
title: "MDPS-tradfi 4-VM silent partial drain (no STOPPED event, mid-processing exit)"
created: 2026-05-08
author: vm-ops-tab (Tab 4)
source:
  - plans/active/work_split_2026_05_08_harsh.md § "TAB 4 — Per-asset_group VM ops" (TradFi MDPS post-drain ES.OPT
    validation)
  - plans/epics/tradfi_master_2026_05_07.md § "Tab 4 finding 2026-05-08" (annotation in plan body)
  - GCE event stream
    gs://central-element-323112-events/events/market-data-processing-service/2026-05-07/mdps-tradfi-{2021..2024}-20260506-125828/
  - CLAUDE.md § "No fire-and-forget VM launches (CRITICAL — production observability)"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# MDPS-tradfi 4-VM silent partial drain

> **Severity**: P0 — workspace silent-exit policy violation; data correctness for tradfi asset_group; blocks tradfi
> ML-pipeline-on-representative-sample readiness (master plan G-group floor). **Blast radius**: tradfi asset_group only
> — 4 of 5 mdps-tradfi-{year} year-shard VMs drained partial-window without emitting `STOPPED` events. mdps-tradfi-2025
> still running (different launch batch, may not be affected). **Suggested owner**: tradfi_master plan owner + Ikenna
> Tab 5 (master plan G-group readiness aggregator). Tab 4 (vm-ops-tab) is the discoverer; downstream relaunches +
> cluster-validation rerun are scoped here once the partial-drain root cause is fixed.

## What I found

Probed at 2026-05-08 11:25 UTC during Tab 4 ES.OPT 11-cluster validation kickoff. The 5 mdps-tradfi VMs are split across
two launch batches:

- **Batch 1** (`mdps-tradfi-{2021,2022,2023,2024}-20260506-125828`): created 2026-05-06 12:58 UTC, all 4 exited
  2026-05-07 ~14:00 UTC after ~25h runtime. **None emitted a `STOPPED` or `FAILED` event.** GCE instance records are
  fully deleted (`gcloud compute instances describe` returns 404). Last events per VM:

  | VM               | last event           | last event ts (UTC)   | last `details.date`  | partial-window state   |
  | ---------------- | -------------------- | --------------------- | -------------------- | ---------------------- |
  | mdps-tradfi-2021 | VALIDATION_STARTED   | 2026-05-07T14:00:17.6 | 2021-08-13           | 8 of 12 months (67%)   |
  | mdps-tradfi-2022 | PROCESSING_STARTED   | 2026-05-07T14:00:17.8 | (not in details)     | unknown month progress |
  | mdps-tradfi-2023 | PROCESSING_COMPLETED | 2026-05-07T13:57:10.3 | (not in details)     | unknown month progress |
  | mdps-tradfi-2024 | PERSISTENCE_STARTED  | 2026-05-07T14:00:19.9 | 2024-05-31 (parquet) | 5 of 12 months (42%)   |

  The 4 VMs died within a 3-minute window, while in MID-PROCESSING (different stages: validation / processing-started /
  processing-completed / persistence-started). Strong signal of **external force-kill**, not natural drain.

- **Batch 2** (`mdps-tradfi-2025-20260507-135207`): created 2026-05-07 05:52 UTC, still RUNNING at probe time (T+29h+).
  Different launch batch, possibly different config. Not yet exited; cannot infer same root cause.

## 2026-05-08 11:54 UTC follow-up — wall-clock-cap hypothesis DISPROVEN

`mdps-tradfi-2025` STILL RUNNING at T+30h (created 2026-05-07 05:52 UTC, current 2026-05-08 11:54 UTC). It crossed the
25h mark at ~2026-05-08 06:52 UTC and did NOT exit. **This rules out a clean wall-clock cap as the root cause of Batch
1's coordinated 14:00 UTC exit.** Updated hypothesis ranking:

1. **External force-kill at exactly 14:00 UTC** — consistent with `vm_zombie_watchdog` batched cull cycle, host
   maintenance window, or coordinated operator action. The 3-min coordinated exit timing is the strongest signal; a
   per-VM resource cap would scatter the exit times.
2. **Workload-specific OOM** — Batch 1's 4 VMs may have been processing heavier date ranges than Batch 2's 2025
   single-year shard. Less likely given the coordinated 14:00 UTC timing (OOM doesn't synchronise across VMs).
3. **Preemption** — possible but a 4-of-4 simultaneous preemption is rare for non-spot instances; would need to verify
   preemptible flag in launcher.
4. **Scheduled job kill** — cron/scheduler running at 14:00 UTC daily that culls stale-looking VMs. Worth grepping for
   `13:5*` / `14:00` cron entries in deployment-service.

Diagnosis priority: pull `vm_zombie_watchdog` event stream for 2026-05-07 13:55-14:05 UTC + grep deployment-service for
any 14:00 UTC scheduled job. mdps-tradfi-2025 acts as a control case (different launch batch, ~17h offset from Batch 1's
launch); its eventual exit pattern will further constrain the hypothesis.

## Why it matters

1. **Workspace `No fire-and-forget VM launches` rule violated** (CLAUDE.md HARD RULE): every VM launch MUST emit
   `STARTED` → `PROCESSING_*` → `STOPPED`/`FAILED` per the rule. Silent exit (last event = mid-step verb, then VM
   deleted) is exactly the failure mode the rule warns against.

2. **TradFi data is incomplete vs intent**. Per the year-shard naming (`mdps-tradfi-2021` = "process all of 2021"), each
   VM had a full-year intent. Partial windows (8/12 months for 2021; 5/12 for 2024) mean significant missing-data ranges
   in the MDPS-derived `processed_candles/` output. Master plan G-group floor "ML pipeline running on representative
   sample by 2026-05-23" risks being over-reported on TradFi readiness.

3. **Tab 4 ES.OPT 11-cluster validation rerun is moot until data is filled**. Cluster-coverage gate against an
   incomplete window can't distinguish "missing because not-yet-processed" from "missing because cluster validation
   missed it". Re-running validation post-relaunch is the right sequence.

4. **Coordinated 14:00 UTC exit pattern** is suspicious — points to external infra cause (wall-clock cap, watchdog kill,
   preemptible eviction, host maintenance) rather than per-VM resource exhaustion. Worth root-causing because if it's a
   launcher / watchdog / wall-clock-cap issue, mdps-tradfi-2025 is also vulnerable.

## Possible root causes (need operator/Ikenna eyes)

- **Wall-clock cap in launcher**: some launchers have `--max-run-time` or per-VM `idle-shutdown` config; ~25h is inside
  the typical 24-48h band. Need to inspect the launcher script for tradfi MDPS.
- **`vm_zombie_watchdog` kill**: the watchdog kills VMs that fail liveness checks; if it interpreted the in-flight VMs
  as zombie (no progress event for >Xmin per its config), it'd terminate them. Coordinated 3-min window matches watchdog
  batched kill cycle.
- **Preemptible / spot VM eviction**: if launched as preemptible, GCP can evict on host-resource pressure; 4 in 3
  minutes is plausible for shared-zone preemption.
- **GCE host maintenance**: less likely (would normally trigger live-migrate, not delete), but possible.

## Recommended decision

1. **Diagnose root cause**: inspect launcher script for tradfi MDPS (find via
   `find deployment-service/scripts/vm/ -name 'launch*tradfi*'`), check whether VMs were preemptible (no longer
   queryable post-delete; possibly recorded in the launcher script), pull `vm_zombie_watchdog` event stream for
   2026-05-07 13:55-14:05 UTC window.
2. **Relaunch the missing windows**: if the partial-drain was unintentional, relaunch year-shard VMs scoped to the
   missing month-ranges (e.g. `mdps-tradfi-2021-Aug-Dec`, `mdps-tradfi-2024-Jun-Dec`). Apply the per-VM-shard
   isolation + watchdog-prefix conventions from CLAUDE.md.
3. **Watch mdps-tradfi-2025**: if Batch-2's 2025 VM also exits silently around 2026-05-08 ~07:00 UTC (the 25h mark from
   its 2026-05-07 05:52 UTC launch), that confirms the wall-clock-cap hypothesis — and also confirms the pattern is
   reproducible / fixable in the launcher.
4. **Re-run cluster validation AFTER relaunch + drain**: the original Tab 4 ES.OPT 11-cluster validation work-split task
   is a downstream check; the precondition (full-window MDPS-tradfi data on disk) must be met first.
5. **Update tradfi_master plan body**: this finding annotation already lives under "Tab 4 finding 2026-05-08" in
   `plans/epics/tradfi_master_2026_05_07.md`. After diagnosis, fold the relaunch + validation steps into the plan's
   actionable todo list.

## Pre-existing relationship to other in-flight work

- **Tab 1 (instruments-live)**: Phase C is "tradfi" Cloud Scheduler + audit job + UI tab. The audit job design should
  ingest this kind of partial-drain detection automatically (so future regressions are caught at the scheduler audit
  cycle rather than by hand). Cross-reference for the instruments-live Phase C todo body.
- **Tab 5 (mechanical refactors)**: `hard_schema_enforcement_2026_05_08` plan is BLOCKED on tradfi_master per Tab 5's
  STARTED ping — the partial-drain finding may further sequence that block (cluster-validation rerun feeds back into the
  schema-enforcement assumptions).
- **Ikenna Tab 5 (master plan refresh)**: TradFi G-group readiness needs to reflect partial-drain reality, not
  optimistic assumed-coverage.
