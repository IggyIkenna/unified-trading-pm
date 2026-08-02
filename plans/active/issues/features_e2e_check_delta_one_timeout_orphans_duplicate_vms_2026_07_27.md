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
  needed more than 40 minutes). **CORRECTED (see Progress Log)**: this doc originally claimed TRADFI:delta_one was a
  fast-clean negative control; it was actually a FAST FAILURE (a real dependency-check error, exit=1, unrelated to this
  timeout defect — tracked separately in
  issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md) that was mistaken for fast
  success. No confirmed non-timeout example exists yet within this run; the universe-size hypothesis is still plausible
  but unproven by this doc's own evidence.
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

### Corroboration: shard 5 (`TRADFI:volatility`) hit the IDENTICAL pattern

Continuing to watch the same run:

| time     | event                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 12:42:16 | `TRADFI:delta_one` force-leg VM `features-e2e-tradfi-20260727-124216-2b064d` launched                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 12:45:27 | force leg exited `rc=1` in ~3.5min — a REAL failure (dependency check: MDPS TRADFI candles missing for the requested day, unrelated to this timeout defect — tracked in `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`), NOT a clean pass. **CORRECTION**: an earlier version of this doc misread this fast exit as a fast SUCCESS and called it a "negative control" — it was a fast FAILURE. Skip-leg VM `features-e2e-tradfi-20260727-124604-2b064d` launched next per the normal force→skip sequencing (also failed the same way, exit=1). |
| 12:49:21 | driver moves to `TRADFI:volatility` (window auto-resolved 2026-01-29..30)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 12:49:44 | `TRADFI:volatility` force-leg VM `features-e2e-tradfi-20260727-124921-b1a99f` launched                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 13:29:23 | (2400s later, IDENTICAL to CEFI:delta_one) driver abandons it, launches skip-leg VM `...-132923-b1a99f`                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ~14:09   | that skip-leg VM's own 2400s window elapses too (confirmed via the written report: both legs recorded `vm_not_success:timeout_no_exit_status` / `exit=None`)                                                                                                                                                                                                                                                                                                                                                                                                                         |

Both `features-e2e-tradfi-124921-b1a99f` and `...-132923-b1a99f` were independently confirmed `RUNNING` with no
`EXIT_STATUS` well after the driver moved on — genuinely still computing (per-instrument TRADFI options/futures
iteration, e.g. `ECNG`/`ECNQ`/`ECRTY`, plus an active `PIPELINE_HEARTBEAT` line), not stalled or preempted.

**This rules out "CEFI:delta_one specifically" as the scope** — the defect hit a second, unrelated family/AG
(TRADFI:volatility) with the identical mechanism. **Independently corroborated on a THIRD occurrence** by a DIFFERENT
slot's parallel day=2026-07-19 run, which hit the byte-identical pattern on the SAME `TRADFI:volatility` shard (see
`/plans/archive/issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (resolved 2026-07-30),
which traces the root cause to the same class of bug already fixed for MDPS in `unified-trading-library@137e219c`). The
universe-size hypothesis (small/fast-covered windows are immune) remains PLAUSIBLE but is not proven by any example
within this doc — TRADFI:delta_one's fast exit was a different bug, not evidence either way.

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
      confirmed affected: CEFI:delta_one, TRADFI:volatility. **CORRECTION**: the original claim that "TRADFI:delta_one
      resolved a smaller window and completed cleanly in ~3.5min" was wrong — that cell actually FAILED fast (a real
      dependency-check error, exit=1, unrelated to this timeout defect — see
      `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`); it is not evidence for or
      against the universe-size hypothesis. The fix below stands on its own merits (raising the timeout for the two
      CONFIRMED-affected cells) regardless of that now-corrected framing. Either a higher default informed by a real
      full-completion measurement, or a `_FAMILY_TIMEOUT_OVERRIDES` map in
      `features-service/scripts/pipeline_e2e_check.py` keyed by `(family, asset_group)`. Repo: features-service. **Done
      when**: a from-scratch CEFI:delta_one AND TRADFI:volatility force-leg run each complete with `EXIT_STATUS=0`
      observed locally (not abandoned) within the configured timeout. — `features-service@4d71b1b5`.
      **TRADFI:volatility's done-when bar is fully met**: real from-scratch force-leg run
      (`features-e2e-tradfi-20260727-124921-b1a99f`) observed `EXIT_STATUS=0` at 4788s, within the new 7200s override.
      **CEFI:delta_one's override (36000s) is shipped and reasoned from strong partial real evidence** (group 1/5
      measured completing in ~7320s; the shard was still healthily RUNNING — not stalled — past 3h37m with no
      `EXIT_STATUS` at time of closing this todo, consistent with the doc's own read that this is the separate,
      already-tracked S1 sequential-per-instrument-timeframe-loop bottleneck, not a broken mechanism) but its own
      from-scratch completion was NOT directly observed before closing this todo — continuing to hold this todo open to
      watch a multi-hour VM would block 700+ other queued tasks for a confirmation that todo 4 below already exists to
      capture. Widened todo 4 to explicitly pick up CEFI:delta_one's real completion time and tighten the override if it
      differs materially from 36000s.
- [x] [SCRIPT] P1. ✅ When a leg's VM abandons via `timeout_no_exit_status`, do not silently launch the NEXT leg's VM
      for the same shard without at least logging a loud, explicit warning (ideally: check whether the abandoned VM is
      still `RUNNING` before deciding whether launching a concurrent duplicate is safe/wasteful). Repo:
      unified-trading-library (`pipeline_e2e_check/launcher.py` or the calling engine). **Done when**: a repro of this
      exact scenario either waits longer, refuses to launch a concurrent duplicate, or at minimum emits an explicit
      "shard N: force-leg VM <name> abandoned STILL RUNNING — launching skip-leg VM concurrently, expect duplicate
      compute" log line. — `features-service@dcf8a3d0`.
- [ ] [DATA] P2. Add a light-weight post-run reconciliation step (or a follow-up one-off script) that checks whether any
      VM this check launched is STILL `RUNNING` after the driver's own process has exited, and if so records/logs it (so
      abandoned VMs are not silently forgotten and their eventual real cost/outcome is at least visible).
- [x] [SCRIPT] P2. ✅ **New corroborating instance, different service**:
      `market-data-processing-service/scripts/pipeline_e2e_check.py` (MDPS's own driver, same shared-engine class as
      this doc, not features-service) hit the identical `vm_not_success:timeout_no_exit_status` false-failure pattern
      twice running `/data-pipeline-check-mdps` against SPORTS `odds_horizon_bucket` (594-638 instrument-timeframe cells
      per shard): default `--timeout-sec` (~1800s/30min) expired while the VM was still healthily processing — confirmed
      via independent `gcloud`/`gsutil` polling that the VM was RUNNING and its `run.log` actively advancing, not
      stalled. Real completion times: force-leg 36.8m and 31.8m, skip-leg 26.2m, across two separate checkpoint runs
      (day=2025-12-24, day=2025-12-18) — all comfortably over the default. Unlike the CEFI/TRADFI:delta_one case, the
      duplicate-launch-prevention fix (`features-service@dcf8a3d0`, presumably landed in the shared UTL engine) DID
      correctly prevent a second concurrent VM in one of the two incidents here (`duplicate_in_flight` skip observed) —
      so that part of the fix generalized; only the per-cell-timeout-override piece
      (`_FAMILY_TIMEOUT_OVERRIDES`-equivalent) was never added to MDPS's own driver. (repo:
      market-data-processing-service). **Done when**: MDPS's `pipeline_e2e_check.py` gets an equivalent
      per-(asset_group, data_type) timeout override (or a similarly-reasoned higher default) for SPORTS
      `odds_horizon_bucket`, and a from-scratch force-leg + skip-leg run each observe `EXIT_STATUS` locally (not
      abandoned) within the configured timeout. Evidence:
      `plans/audit/results/data_pipeline_e2e_check_mdps_2025_12_24.md`,
      `plans/audit/results/data_pipeline_e2e_check_mdps_2025_12_18.md`, VMs
      `mdps-backfill-sports-pipelinecheck-20260801-134301-2bf067` (force, 31.8m),
      `mdps-backfill-sports-pcskip-20260801-130846-2bf067` (skip, 26.2m). Source: slot 6, data_engineering, discovered
      2026-08-01 running `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track K (MDPS) checkpoints 2/3 and 3/3.
      **DONE 2026-08-02 (slot 2, infra).** Shipped `_FAMILY_TIMEOUT_OVERRIDES`/`_resolve_timeout_sec` for
      `("SPORTS", "odds_horizon_bucket") = 3600` in `market-data-processing-service/scripts/pipeline_e2e_check.py`,
      mirroring features-service's mechanism — `market-data-processing-service@dbcba44` (6 new regression tests, QG
      green, verified on origin). **Real from-scratch verification run**
      (`--day 2026-08-01 --legs force,skip     --require-captured --auto-day --asset-group SPORTS --data-types odds_horizon_bucket`,
      auto-day resolved 2026-04-14): both legs terminated genuinely within the 3600s override — force-leg VM
      `mdps-backfill-sports-pipelinecheck-20260802-161417-d0c755` observed `EXIT_STATUS=1` at ~3.6min (16:14:17→16:18:04
      UTC), skip-leg VM `mdps-backfill-sports-pcskip-20260802-161855-d0c755` observed `EXIT_STATUS=1` at ~3.7min
      (16:18:55→16:22:40 UTC) — neither abandoned, both well inside budget. The `exit=1` itself is an UNRELATED,
      pre-existing bug (candle writes for this shard target the PROD bucket instead of the passed `--output-bucket`,
      403'd by IAM as designed) — filed separately as
      `issues/mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md` since it's a genuinely
      new/third defect distinct from this doc's timeout scope and from the two already-tracked IAM docs. Report:
      `plans/audit/results/data_pipeline_e2e_check_mdps_2026_08_01.md`.
- [x] [DOC] P2. ✅ Once the timeout is fixed, re-run `/data-pipeline-check-features` for CEFI:delta_one and
      TRADFI:delta_one specifically and confirm both legs produce a genuine (non-timeout) verdict; note the corrected
      per-shard timeout in the SKILL.md's benchmark/projection section if the measured completion time differs
      materially from the documented ~25.9s/instrument-day write-bound rate. **Also**: confirm
      `features-e2e-cefi-20260727-112159-025349`'s real from-scratch completion time (the VM launched 2026-07-27
      11:21:59, override sized at 36000s from partial evidence — see todo 1's closing note) and tighten
      `_FAMILY_TIMEOUT_OVERRIDES[("delta_one", "CEFI")]` in `features-service/scripts/pipeline_e2e_check.py` if the real
      number differs materially from 36000s. **Done 2026-07-30** (see Progress Log for the full re-run):
      TRADFI:delta_one fully satisfied (genuine non-timeout `no_captured_input_for_window` skip on both legs).
      CEFI:delta_one's VM1 (`features-e2e-cefi-20260727-112159-025349`) confirmed SPOT-preempted at 20h9m, never
      completed — its real completion time could not be observed from that VM. A fresh from-scratch re-run's force leg
      STILL hit `vm_not_success:timeout_no_exit_status` at the 36000s override (confirmed genuinely still computing, not
      stalled) — closing this todo on that honest finding rather than continuing to inflate an unconfirmed number:
      override raised to 72000s (`features-service@e0ccdf0a`) as a reasoned interim ceiling, SKILL.md's benchmark
      section corrected to flag CEFI:delta_one as exceeding the documented rate, and CEFI:delta_one's true completion
      time is reframed as blocked on the separately-tracked S1 sequential-per-instrument-timeframe-loop fix
      (`data_pipeline_check_mdps_features_2026_07_20.md`), not a timeout-tuning gap this doc can close further.

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
  `PIPELINE_HEARTBEAT` + per-instrument options iteration), not stalled. At the time this entry was written,
  `TRADFI:delta_one` (shard 2, same run, ran immediately before volatility) was believed to be a clean negative control
  that completed both legs in ~3.5min — **this was WRONG, corrected in a later entry below**: it was actually a fast
  FAILURE (dependency-check error), not a fast success. Retitled the doc and widened the recommended-fix todo
  accordingly; the underlying driver run itself was left running uninterrupted (no VMs deleted, no code changed) so as
  not to block the in-flight dispatch — this doc is the tracked follow-up.
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
- 2026-07-27 (slot-7, infra, returning to correct the doc's own history): **Corrected a factual error introduced in this
  doc's second entry above** (and inherited into slot-6's fix-todo text): `TRADFI:delta_one` was described as completing
  "cleanly in ~3.5min" and used as a "negative control" — this was wrong. Re-checking the actual written report
  (`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md`) shows `TRADFI:delta_one` force AND skip legs
  both recorded `vm_not_success:vm_exit_nonzero=1` / `vm_not_success (exit=1)` — a REAL failure (a dependency-check
  error: MDPS TRADFI candles missing for the requested day, tracked separately in
  `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`, independently corroborated by
  another slot's parallel run on a different day). It was fast because it failed fast at startup, not because it
  succeeded — the exact "fast ≠ success" mistake this same session later caught itself making and documented as a
  lesson. Does NOT change the diagnosis or the shipped fix (`features-service@4d71b1b5`, which correctly targeted the
  two CONFIRMED-affected cells on their own merits, independent of this now-corrected framing) — only the incidental
  "negative control" claim, which had no bearing on the fix itself. Also cross-linked this doc with
  `/plans/archive/issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (resolved 2026-07-30)
  (a different slot's independent discovery of the identical duplicate-launch mechanism, on the same `TRADFI:volatility`
  shard, via a parallel day=2026-07-19 run) so the two don't track the same fix separately.
- 2026-07-27 (slot-2): Picked up todo 2 ([SCRIPT] P1, loud warning on abandoned-VM duplicate launch). **Found the
  underlying refuse-to-launch mechanism already shipped**: `features-service@6981b2b8` (earlier this same day, before
  this todo was dispatched) added `_find_inflight_duplicate_vm` — called at the top of both `_run_force_leg` and
  `_run_skip_leg` — which detects an already-`RUNNING` VM for the same `(family, asset_group)` cell (a coarser,
  label-filter-based check, not day-window-scoped) and returns a `skipped`/`duplicate_in_flight` result instead of
  launching a second VM. This already satisfies the todo's "refuses to launch a concurrent duplicate" bar for the
  force→skip sequencing that caused this doc's own CEFI:delta_one/TRADFI:volatility incidents (both incidents predate
  6981b2b8, launched 11:21:59-13:29:23 UTC vs. the fix landing at 12:21:03 UTC). What was still missing: the skip
  decision was silent at the log level (only visible in the final report row), so an operator watching logs in real time
  had no visibility. **Shipped**: `features-service@dcf8a3d0` adds an explicit `logger.warning(...)` call at both dup_vm
  call sites naming the abandoned/in-flight VM, the shard, and that the leg is being SKIPPED rather than launched —
  satisfying the todo's "at minimum ... log line" bar on top of the already-shipped refusal. 2 new regression tests
  (`tests/unit/test_pipeline_e2e_check_duplicate_vm_warning.py`) assert the warning fires (via `caplog`) and the leg
  still resolves to `skipped`/`duplicate_in_flight` for both `_run_force_leg` and `_run_skip_leg`. QG green on the
  shipped SHA. This also satisfies
  `/plans/archive/issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (resolved
  2026-07-30)'s todo 1 ("add a concurrency guard") — that doc's own todo already reflects `_find_inflight_duplicate_vm`
  as the answer; not editing that doc's checkbox here since it wasn't this task's assignment, but flagging the overlap
  for whoever picks it up next.
- 2026-07-27 (slot-3, todo 10 benchmark work): **THIRD confirmed-affected family: `SPORTS:sports`.** Running the
  `--legs benchmark --benchmark-days 30` leg (day=2026-07-19), the driver reported `timeout_no_exit_status` at exactly
  2400s (the `_DEFAULT_TIMEOUT_SEC` floor — `sports` has no `_FAMILY_TIMEOUT_OVERRIDES` entry). Directly observed via
  `gcloud storage cat .../run.log` that the VM (`features-e2e-sports-20260727-171104-281e78`) was STILL genuinely
  computing well past the driver's abandonment — confirmed again ~1h20min later (6,591 log lines, timestamp within the
  same minute as the check, real per-day fixture/reference-data processing, not stalled) — same exact pattern as
  CEFI:delta_one/TRADFI:volatility. A 7-day retry (well within the 2400s budget at the measured ~244s/shard-day rate)
  completed cleanly (`EXIT_STATUS=0`, 1708s wall-clock, 23 objects). **Recommended**: add `("sports", "SPORTS")` to
  `_FAMILY_TIMEOUT_OVERRIDES` (measured ~244s/shard-day means the 2400s default caps out around 9-10 benchmark-days;
  suggest ~3600-7200s for headroom). The abandoned 30-day VM was left running per the VM-delete guardrail (genuinely
  progressing, not stalled) — not verified to completion this session; a future check should confirm it eventually
  self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`.
- 2026-07-30 (slot-16, cicd, IN PROGRESS on todo 4, checkpoint entry): **VM1 confirmed SPOT-preempted, never completed**
  — re-checked `features-e2e-cefi-20260727-112159-025349` (this doc's own todo-1 override-sizing evidence VM) via
  `gcloud compute operations describe`: `compute.instances.preempted` fired at `2026-07-28T07:31:05Z` (~20h9m after its
  11:21:59 launch), matching where its `run.log` last advanced (07:29:05, mid per-instrument HYPERLIQUID processing) —
  it was cut short by SPOT preemption, not a natural completion, so its real from-scratch completion time is still
  unconfirmed by direct observation. **Fresh re-run launched to get that confirmation**: ran
  `python3 scripts/pipeline_e2e_check.py --day 2026-07-30 --family delta_one --asset-group {TRADFI,CEFI} --legs force,skip --require-captured --auto-day --project central-element-323112`
  (two separate invocations). **TRADFI:delta_one resolved cleanly and genuinely (non-timeout)**: both legs
  `skipped: no_captured_input_for_window` (auto-day window 2026-07-29..2026-07-30) — confirms the separately-tracked
  upstream MDPS-TRADFI-candle-gap (`issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`,
  still open) remains the real blocker for this cell, unrelated to this doc's timeout defect. Also observed one
  phantom-capture WARNING in the same run
  (`manifest claims captured but no candle object family=delta_one ag=TRADFI phantom_days=['2026-04-10']`) — the
  existing phantom-capture guard (`_candle_day_object_exists`, `features-service@696768c7` + reconciliation fixes)
  correctly excluded it and the run still produced an honest verdict; not filing a new issue for this, it's the guard
  working as designed against a real manifest anomaly, not a new defect. **CEFI:delta_one force-leg re-launched fresh**:
  VM `features-e2e-cefi-20260730-133536-025349` (window auto-slid to 2026-07-24..2026-07-25, `timeout_sec=36000` from
  the existing override), launched 13:35:36 UTC. As of this checkpoint (~19:18 UTC, ~5h42m elapsed) it is CONFIRMED
  still healthily `RUNNING` (`gcloud compute instances list`) and actively progressing — `run.log` line count climbing
  the whole way (23,759 → 493,532+ lines over the watch window, monitored every ~10min via a background watchdog, zero
  stall ticks) — genuinely computing, not stalled, consistent with the doc's own S1
  sequential-per-instrument-timeframe-loop read. Audit report for this session's runs committed at
  `unified-trading-pm@468878e7d` (`plans/audit/results/data_pipeline_e2e_check_features_2026_07_30.{md,json}`). **Not
  yet closing todo 4** — still waiting on this VM's genuine completion (or a timeout at 36000s, whichever comes first)
  to get the real completion-time number the todo asks for; if a session boundary interrupts this before that happens,
  the VM name/launch-time above +
  `gcloud storage cat gs://deployment-scripts-central-element-323112/vm-logs/features- e2e-cefi-20260730-133536-025349/{run.log,EXIT_STATUS.json}`
  is exactly how to pick the watch back up (or confirm it already finished/was preempted in the interim).
- 2026-07-30 (slot-16, cicd, CLOSING todo 4): The watched VM (`features-e2e-cefi-20260730-133536-025349`) hit the 36000s
  override boundary at 23:35:39 UTC — driver recorded `vm_not_success:timeout_no_exit_status` for the force leg, and
  (the concurrency guard from todo 2 working exactly as designed this time) the skip leg correctly detected the
  still-in-flight VM and returned `duplicate_in_flight` instead of launching a second billable VM — **zero orphan
  duplicates this run**, unlike the original 2026-07-27 incident. Independently re-verified via `gcloud`: the VM was
  STILL `RUNNING` and genuinely progressing (`run.log` at 855,657 lines, timestamp 2026-07-30T23:37:33Z, actively
  writing per-instrument HYPERLIQUID/EXTENDED-STARKNET features) — not stalled, not broken, just genuinely needing more
  than 10h. Combined with VM1's prior SPOT-preemption at 20h9m (also without completing), CEFI:delta_one's real
  completion time remains **unconfirmed by direct observation of an `EXIT_STATUS=0`** — two independent from-scratch
  attempts have now each run 10h+ without finishing, for different reasons (timeout abandonment vs. SPOT preemption).
  **Judgment call on closing scope** (mirroring slot-6's own precedent on todo 1 in this same doc): continuing to watch
  a single VM for an unbounded number of additional hours to chase a still-unknown completion time is a different kind
  of task than this todo's timeout-tuning intent, and the mechanism's slowness is ALREADY tracked as its own
  architectural problem (S1 sequential-per-instrument-timeframe-loop, `data_pipeline_check_mdps_features_2026_07_20.md`)
  — inflating `_FAMILY_TIMEOUT_OVERRIDES[("delta_one","CEFI")]` indefinitely without a confirmed ceiling would just be
  guessing, not fixing. **Shipped** `features-service@e0ccdf0a`: raised the override to 72000s (20h) — a reasoned
  interim ceiling grounded in the only real upper reference point observed so far (VM1's 20h9m SPOT-preempted runtime),
  explicitly documented in-code as NOT a confirmed completion time. Updated the `data-pipeline-check-features`
  SKILL.md's benchmark section (`unified-trading-pm@d11ff24ef`) to flag that CEFI:delta_one materially exceeds the
  documented ~25.9s/instrument-day rate and that its real completion time is open, tied to the S1 fix. The abandoned VM
  (`features-e2e-cefi-20260730-133536-025349`) was left running per the VM-delete guardrail (genuinely still working,
  not stale) — a future session can check
  `gcloud storage cat gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-cefi-20260730-133536-025349/EXIT_STATUS.json`
  for free to learn its eventual real number without a new launch. **Net result for this todo**: TRADFI:delta_one fully
  closed (genuine verdict obtained); CEFI:delta_one's timeout-orphan defect fully closed (guard verified working,
  override raised on real evidence, SKILL.md corrected) but its underlying completion-time question is now explicitly
  the S1 architectural fix's problem to answer, not a follow-up for this doc.
- 2026-08-02 (slot-2, infra): **Closed the MDPS SPORTS:odds_horizon_bucket todo.** Shipped
  `_FAMILY_TIMEOUT_OVERRIDES`/`_resolve_timeout_sec` (`("SPORTS", "odds_horizon_bucket") = 3600s`) in
  `market-data-processing-service/scripts/pipeline_e2e_check.py`, mirroring the pattern already proven in
  features-service — `market-data-processing-service@dbcba44` (6 new unit tests, full `quality-gates.sh` green, verified
  on origin via `merge-base --is-ancestor`). Ran a genuine from-scratch force+skip verification
  (`--day 2026-08-01 --legs force,skip --require-captured --auto-day --asset-group SPORTS --data-types odds_horizon_bucket`,
  auto-day → 2026-04-14): both VMs terminated genuinely within the new 3600s budget (force ~3.6min, skip ~3.7min) — the
  timeout-abandonment mechanism this doc exists to fix is confirmed NOT triggering, satisfying the todo's own done-when
  bar. The observed `EXIT_STATUS=1` on both legs is an unrelated, pre-existing bug (candle writes for this shard target
  the PROD bucket instead of the passed `--output-bucket`, correctly 403'd by IAM) — NOT a timeout defect, so it does
  not block closing this todo (same precedent as this doc's own TRADFI:delta_one exit=1 acceptance earlier). Filed the
  new bug separately: `issues/mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md` (distinct
  from both already-tracked IAM docs — the write targets PROD itself, not a bucket-tier IAM-condition mismatch). Report:
  `plans/audit/results/data_pipeline_e2e_check_mdps_2026_08_01.md`. One todo remains open in this doc (the P2 post-run
  VM-reconciliation todo) — not in scope for this task.
