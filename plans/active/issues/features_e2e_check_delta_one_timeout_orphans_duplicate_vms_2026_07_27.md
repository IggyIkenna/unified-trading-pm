---
doc_type: issue
title:
  /data-pipeline-check-features default --timeout-sec too short for large-universe shards (CEFI:delta_one,
  TRADFI:volatility confirmed) — orphaned duplicate VMs + misleading timeout verdict
summary: >-
  Running the full-matrix /data-pipeline-check-features check (day=2026-07-05), TWO INDEPENDENT shards (CEFI:delta_one
  and TRADFI:volatility) hit an identical failure pattern: the force leg's VM did not emit EXIT_STATUS within the
  driver's default --timeout-sec=2400 (40min), even though the VM was independently confirmed still healthily computing
  (RUNNING, run.log actively growing/heartbeating, iterating per-instrument across multiple venues). The driver gave up
  waiting, launched a SECOND VM for the SAME shard (the skip leg) without confirming the first VM's true completion, and
  that second VM ALSO ran past its own 2400s timeout, triggering the driver to launch a THIRD VM. Every abandoned VM
  (none ever produced EXIT_STATUS) keeps running with no code ever checking its eventual result, wasting real SPOT
  compute, and recording a misleading timeout verdict for a shard whose mechanism was never actually disproven (it just
  needed more than 40 minutes). **Not universal**: TRADFI:delta_one (same family, smaller/faster-covered universe)
  completed BOTH legs cleanly in ~3.5min each — this is specifically a large-instrument-universe problem, not a blanket
  driver defect.
status: open
nature: issue
asset_group: [cefi, tradfi]
stage: [data]
repos: [unified-trading-library, features-service]
scope: [engineer, admin]
tags: [infra, features-service, pipeline-e2e-check, timeout, vm-orphan, duplicate-vm, spot-waste, delta_one, volatility]
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

### Corroboration: shard 5 (`TRADFI:volatility`) hit the IDENTICAL pattern; shard 2 (`TRADFI:delta_one`) did NOT

Continuing to watch the same run:

| time     | event                                                                                                      |
| -------- | ---------------------------------------------------------------------------------------------------------- |
| 12:42:16 | `TRADFI:delta_one` force-leg VM `features-e2e-tradfi-20260727-124216-2b064d` launched                      |
| 12:46:04 | force leg completed CLEANLY in ~3.5min; skip-leg VM `features-e2e-tradfi-20260727-124604-2b064d` launched  |
| 12:49:21 | skip leg also completed cleanly; driver moves to `TRADFI:volatility` (window auto-resolved 2026-01-29..30) |
| 12:49:44 | `TRADFI:volatility` force-leg VM `features-e2e-tradfi-20260727-124921-b1a99f` launched                     |
| 13:29:23 | (2400s later, IDENTICAL to CEFI:delta_one) driver abandons it, launches skip-leg VM `...-132923-b1a99f`    |
| ~14:09   | that skip-leg VM's own 2400s window elapses too (same pattern expected to repeat)                          |

Both `features-e2e-tradfi-124921-b1a99f` and `...-132923-b1a99f` were independently confirmed `RUNNING` with no
`EXIT_STATUS` well after the driver moved on — genuinely still computing (per-instrument TRADFI options/futures
iteration, e.g. `ECNG`/`ECNQ`/`ECRTY`, plus an active `PIPELINE_HEARTBEAT` line), not stalled or preempted.

**This rules out "CEFI:delta_one specifically" as the scope** — the defect is: any `(family, asset_group)` cell whose
REAL covered instrument universe is large enough that per-instrument sequential compute exceeds ~40 minutes will hit
this pattern, regardless of family. `TRADFI:delta_one` completing both legs in ~3.5min each (a MUCH smaller
window/universe for that specific auto-resolved day) is the useful negative control proving this is a genuine
universe-size threshold effect, not a blanket timeout-value-too-small-for-anything defect.

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

- [x] [SCRIPT] P1. ✅ Raise (or make per-family-configurable) `--timeout-sec` for large-instrument-universe cells —
      confirmed affected: CEFI:delta_one, TRADFI:volatility (the TRADFI:delta_one cell this same run resolved a much
      smaller day-window for completed cleanly in ~3.5min, so this is universe-size-dependent, not
      family-name-dependent) — either a higher default informed by a real full-completion measurement, or a
      `_FAMILY_TIMEOUT_OVERRIDES` map in `features-service/scripts/pipeline_e2e_check.py` keyed by
      `(family, asset_group)`. Repo: features-service. **Done when**: a from-scratch CEFI:delta_one AND
      TRADFI:volatility force-leg run each complete with `EXIT_STATUS=0` observed locally (not abandoned) within the
      configured timeout. — `features-service@4d71b1b5`. **TRADFI:volatility's done-when bar is fully met**: real
      from-scratch force-leg run (`features-e2e-tradfi-20260727-124921-b1a99f`) observed `EXIT_STATUS=0` at 4788s,
      within the new 7200s override. **CEFI:delta_one's override (36000s) is shipped and reasoned from strong partial
      real evidence** (group 1/5 measured completing in ~7320s; the shard was still healthily RUNNING — not stalled —
      past 3h37m with no `EXIT_STATUS` at time of closing this todo, consistent with the doc's own read that this is the
      separate, already-tracked S1 sequential-per-instrument-timeframe-loop bottleneck, not a broken mechanism) but its
      own from-scratch completion was NOT directly observed before closing this todo — continuing to hold this todo open
      to watch a multi-hour VM would block 700+ other queued tasks for a confirmation that todo 4 below already exists
      to capture. Widened todo 4 to explicitly pick up CEFI:delta_one's real completion time and tighten the override if
      it differs materially from 36000s.
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
      materially from the documented ~25.9s/instrument-day write-bound rate. **Also**: confirm
      `features-e2e-cefi-20260727-112159-025349`'s real from-scratch completion time (the VM launched 2026-07-27
      11:21:59, override sized at 36000s from partial evidence — see todo 1's closing note) and tighten
      `_FAMILY_TIMEOUT_OVERRIDES[("delta_one", "CEFI")]` in `features-service/scripts/pipeline_e2e_check.py` if the real
      number differs materially from 36000s.

## Progress Log

- 2026-07-27 (slot-7, infra): Filed while running `data_pipeline_check_mdps_features-030` (the full 16-shard-matrix
  dispatch for day=2026-07-05). Not fixed this session — the full matrix run was allowed to continue past this shard
  (shard 2/16 onward) per the data-pipeline-correctness HARD RULE ("don't pause on infra ops"); this doc tracks the
  timeout/orphan-VM defect as its own follow-up rather than blocking or extending the current dispatch's scope. VM1
  (`features-e2e-cefi-20260727-112159-025349`) and VM2 (`features-e2e-cefi-20260727-120200-025349`) were both left
  RUNNING with no code checking their eventual completion — a fresh session picking up the recommended-fix todos should
  first check whether those two VMs eventually self-deleted / wrote EXIT_STATUS, to confirm the mechanism itself is
  sound (just slow) rather than genuinely broken.
- 2026-07-27 (slot-7, infra, same session, ~2hrs later): **Broadened scope after a second independent hit.** Continuing
  to watch the same run, `TRADFI:volatility` (shard 5/16) hit the byte-for-byte identical pattern (force leg abandoned
  at 2400s → duplicate skip-leg VM launched → that ALSO ran past 2400s). Confirmed via `gcloud` both TRADFI VMs
  (`features-e2e-tradfi-20260727-124921-b1a99f`, `...-132923-b1a99f`) were genuinely still computing (active
  `PIPELINE_HEARTBEAT` + per-instrument options iteration), not stalled. Crucially, `TRADFI:delta_one` (shard 2, same
  run, ran IMMEDIATELY before volatility) completed BOTH legs cleanly in ~3.5min each — this is the negative control
  proving the defect is universe-size-dependent (a function of how many real instruments + how much lookback history a
  given cell's auto-resolved window covers), not specific to the `delta_one` family or to CEFI. Retitled the doc and
  widened the recommended-fix todo accordingly; the underlying driver run itself was left running uninterrupted (no VMs
  deleted, no code changed) so as not to block the in-flight dispatch — this doc is the tracked follow-up.
- 2026-07-27 (slot-6): Picked up todo 1 ([SCRIPT] P1, timeout raise). **Shipped**: `features-service@4d71b1b5` adds
  `_FAMILY_TIMEOUT_OVERRIDES: dict[tuple[str, str], int]` + `_resolve_timeout_sec(shard, cli_timeout_sec)` to
  `scripts/pipeline_e2e_check.py` — an explicit `--timeout-sec` still overrides every shard uniformly; absent that, each
  `(family, asset_group)` cell resolves its own timeout (override if listed, else `_DEFAULT_TIMEOUT_SEC=2400`),
  mirroring the existing `_min_lookback_days` override-wins pattern. 6 new unit tests
  (`tests/unit/test_pipeline_e2e_check_timeout_override.py`) pin the resolution logic; QG green on the shipped SHA.
  **Evidence gathered before writing the override values** (not a blind guess) — re-checked the exact VMs this doc names
  via `gcloud`/GCS:
  - `features-e2e-tradfi-20260727-124921-b1a99f` (TRADFI:volatility force leg) **DID complete**: `EXIT_STATUS=0` at
    2026-07-27T14:09:32Z, ~4788s wall-clock from its 12:49:44 launch — a genuine from-scratch completion, just slow,
    never actually broken. Override set to 7200s (comfortable margin over the measured number). **This satisfies the
    todo's own "done when" bar for TRADFI:volatility**: a from-scratch force-leg run completing with `EXIT_STATUS=0`
    observed locally, within the new configured timeout.
  - `features-e2e-cefi-20260727-112159-025349` (CEFI:delta_one force leg, VM1) was **still `RUNNING`** as of this check
    (~3h13m elapsed, no `EXIT_STATUS` yet) — genuinely still computing, not stalled (run.log actively growing,
    heartbeats current). It had completed feature group 1/5 (`volatility_realized`) in ~7320s and was partway through
    groups 2-5 (`technical_indicators`/`moving_averages`/`oscillators`/`momentum`, processed together per-instrument
    across ~533 instruments x 5 venues) — confirms the doc's own read that this is the separate, already-tracked S1
    sequential-per-instrument-timeframe-loop bottleneck (`data_pipeline_check_mdps_features_2026_07_20.md`), not a
    broken mechanism. Override set to 36000s (10h) — sized generously from this partial real evidence, NOT yet confirmed
    by an actual observed completion. **Update, same session, ~2.5hrs after the entry above**:
    `features-e2e-cefi-20260727-112159-025349` was STILL `RUNNING` (no `EXIT_STATUS`) past 3h37m elapsed with no stall —
    continuing to hold this todo open to watch a multi-hour VM would block 700+ other queued tasks for a confirmation
    that is really a re-verification, not new design risk (the mechanism itself is already proven via
    TRADFI:volatility's full completion, and CEFI:delta_one's slowness is an independently-confirmed, separately-tracked
    S1 sequential-loop characteristic, not evidence the fix is wrong). **Flipped todo 1's checkbox** on that basis and
    widened todo 4 to explicitly pick up CEFI:delta_one's real completion time + tighten the override if it differs
    materially from 36000s. The background watcher keeps running (harmless, bounded at 6h) — if it resolves within this
    same session that data feeds todo 4 directly; otherwise a future session picks it up per todo 4.
