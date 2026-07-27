---
doc_type: issue
title:
  /data-pipeline-check-features default --timeout-sec too short for delta_one CEFI/TRADFI — orphaned duplicate VMs +
  misleading timeout verdict
summary: >-
  Running the full-matrix /data-pipeline-check-features check (day=2026-07-05) against CEFI:delta_one, the force leg's
  VM did not emit EXIT_STATUS within the driver's default --timeout-sec=2400 (40min), even though the VM was
  independently confirmed still healthily computing (RUNNING, run.log actively growing, iterating per-instrument candle
  history across multiple venues). The driver gave up waiting, launched a SECOND VM for the SAME shard (the skip leg)
  without confirming the first VM's true completion, and that second VM ALSO ran past its own 2400s timeout. The driver
  then abandoned BOTH VMs (neither ever produced EXIT_STATUS) and moved on to shard 2/16 (TRADFI:delta_one) — leaving
  two orphaned VMs still running with no code ever checking their eventual result, wasting real SPOT compute, and
  recording a misleading timeout verdict for a shard whose mechanism was never actually disproven (it just needed more
  than 40 minutes).
status: open
nature: issue
asset_group: [cefi, tradfi]
stage: [data]
repos: [unified-trading-library, features-service]
scope: [engineer, admin]
tags: [infra, features-service, pipeline-e2e-check, timeout, vm-orphan, duplicate-vm, spot-waste]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: infrastructure_master
source:
  "slot-7, infra, discovered while running data_pipeline_check_mdps_features-030 (full-matrix
  /data-pipeline-check-features, day=2026-07-05), 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# /data-pipeline-check-features default timeout too short for delta_one CEFI/TRADFI — orphaned duplicate VMs

## What I found

Running
`python3 scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day --project central-element-323112`
(the full 16-shard matrix, all 8 families x valid asset_groups, no `--family`/ `--asset-group` filter), shard 1/16
(`CEFI:delta_one`, auto-day resolved window `2026-06-28..2026-06-29`) played out as follows (all times UTC):

| time     | event                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------ |
| 11:21:59 | force-leg VM `features-e2e-cefi-20260727-112159-025349` launched, confirmed present                                |
| 12:02:00 | (2400s later) driver launches a SECOND VM `features-e2e-cefi-20260727-120200-025349` for the SAME shard (skip leg) |
| 12:42:08 | (2400s after the 2nd launch) driver moves to shard 2/16 (`TRADFI:delta_one`) — no verdict/completion line logged   |

At no point did the local driver log an explicit "timed out" message for either VM (the
`reason="timeout_no_exit_status"` path in `launch_vm_and_wait` is not itself logged at INFO). Independently verified via
`gcloud`:

- **VM1** (`features-e2e-cefi-20260727-112159-025349`): confirmed `RUNNING` and actively progressing (run.log line count
  climbing steadily: 12,813 -> 23,157 -> 27,829+ lines over the ~40min the driver waited) — genuinely computing, not
  stalled or preempted. Iterating sequentially per-instrument across BITFINEX-FUTURES, COINBASE-SPOT, HYPERLIQUID, etc.,
  scanning multi-month candle history per instrument (the known S1 sequential-per-instrument-timeframe-loop bottleneck
  documented elsewhere in `data_pipeline_check_mdps_features_2026_07_20.md`).
- **VM2** (`features-e2e-cefi-20260727-120200-025349`): same pattern — `RUNNING`, no `EXIT_STATUS` object, launched
  immediately after VM1's timeout with the identical shard params (no `FORCE` env visible in argv since it's env-based,
  but timing/order strongly indicates this is the skip leg for the same shard).
- **After the driver moved to shard 2** (past 12:42:08), BOTH VM1 and VM2 were re-checked and were STILL `RUNNING` with
  no `EXIT_STATUS` object present — i.e. the driver abandoned both without ever learning their true outcome, and nothing
  in the check flow re-polls or reconciles an abandoned VM's eventual result.

## Why it matters

1. **Wasted SPOT compute, unbounded**: two VMs are left running indefinitely (until their own internal work finishes and
   they self-delete, or some external timeout/budget catches them) with zero code path checking their eventual
   completion or writing that result anywhere. Every delta_one-heavy shard (CEFI has ~589 CEFI perpetuals/futures per
   the universe-filter fix in `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`) is a
   candidate for the same pattern.
2. **Misleading verdict**: the shard's report entry will show `timeout_no_exit_status` for force and/or skip, which
   reads as "the mechanism doesn't work" — it is actually "the mechanism needs more than 2400s for this instrument
   count/lookback combination." This is the OPPOSITE of the honest-absence principle (CLAUDE.md § "Data pipeline
   correctness is the heartbeat") if left unqualified in the final report.
3. **Invalidated skip-proof**: the skip leg is only a meaningful proof if a PRIOR successful force run exists to skip
   against. Since the force leg never actually completed within the timeout, the skip leg's VM has no valid completed
   state to detect — it is really just a duplicate, unproven force attempt, not a genuine skip-if-fresh demonstration.
4. **No VM-abandonment safeguard**: per the infra craft's own VM-delete guardrail (`agents/infra.md` STEP 0.65), neither
   VM should be force-deleted since both are genuinely still working (not stale) — but there is also no mechanism to let
   the driver WAIT LONGER, check back later, or at minimum log a loud warning that it is abandoning a live VM. The check
   silently proceeds as if the shard is done.

## Recommended fix path

- [ ] [SCRIPT] P1. Raise (or make per-family-configurable) `--timeout-sec` for instrument-heavy families/asset_groups
      (delta_one on CEFI/TRADFI in particular) — either a higher default informed by a real full-completion measurement,
      or a `_FAMILY_TIMEOUT_OVERRIDES` map in `features-service/scripts/pipeline_e2e_check.py` keyed by
      `(family, asset_group)`. Repo: features-service. **Done when**: a from-scratch CEFI:delta_one force-leg run
      completes with `EXIT_STATUS=0` observed locally (not abandoned) within the configured timeout.
- [ ] [SCRIPT] P1. When a leg's VM abandons via `timeout_no_exit_status`, do not silently launch the NEXT leg's VM for
      the same shard without at least logging a loud, explicit warning (ideally: check whether the abandoned VM is still
      `RUNNING` before deciding whether launching a concurrent duplicate is safe/wasteful). Repo:
      unified-trading-library (`pipeline_e2e_check/launcher.py` or the calling engine). **Done when**: a repro of this
      exact scenario either waits longer, refuses to launch a concurrent duplicate, or at minimum emits an explicit
      "shard N: force-leg VM <name> abandoned STILL RUNNING — launching skip-leg VM concurrently, expect duplicate
      compute" log line.
- [ ] [DATA] P2. Add a light-weight post-run reconciliation step (or a follow-up one-off script) that checks whether any
      VM this check launched is STILL `RUNNING` after the driver's own process has exited, and if so records/logs it (so
      abandoned VMs are not silently forgotten and their eventual real cost/outcome is at least visible).
- [ ] [DOC] P2. Once the timeout is fixed, re-run `/data-pipeline-check-features` for CEFI:delta_one and
      TRADFI:delta_one specifically and confirm both legs produce a genuine (non-timeout) verdict; note the corrected
      per-shard timeout in the SKILL.md's benchmark/projection section if the measured completion time differs
      materially from the documented ~25.9s/instrument-day write-bound rate.

## Progress Log

- 2026-07-27 (slot-7, infra): Filed while running `data_pipeline_check_mdps_features-030` (the full 16-shard-matrix
  dispatch for day=2026-07-05). Not fixed this session — the full matrix run was allowed to continue past this shard
  (shard 2/16 onward) per the data-pipeline-correctness HARD RULE ("don't pause on infra ops"); this doc tracks the
  timeout/orphan-VM defect as its own follow-up rather than blocking or extending the current dispatch's scope. VM1
  (`features-e2e-cefi-20260727-112159-025349`) and VM2 (`features-e2e-cefi-20260727-120200-025349`) were both left
  RUNNING with no code checking their eventual completion — a fresh session picking up the recommended-fix todos should
  first check whether those two VMs eventually self-deleted / wrote EXIT_STATUS, to confirm the mechanism itself is
  sound (just slow) rather than genuinely broken.
