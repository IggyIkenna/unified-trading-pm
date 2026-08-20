---
doc_type: issue
title:
  dp-exit-code-monitor times out at 1800s on every execution — the sweep never finishes, so revocation coverage will be
  truncated
summary: |
  uts-prod-dp-exit-code-monitor was killed by the Cloud Run 1800s task timeout on every execution measured at filing
  (2026-08-14), spending the whole budget on per-VM run.log downloads that each blew the 30s bounded-call. That GCS/OOM
  bottleneck was fixed 2026-08-14/15 (see Todo 1). Live measurement 2026-08-17 found a 2/20 (10%) residual intermittent
  failure rate. TWO sessions working in parallel found and fixed TWO distinct, real bugs in the same window: (1, the
  BETTER-EVIDENCED explanation for the specific `r2tsj`/`7tbv2` incidents, direct log-line proof) an unscoped CME
  relaunch launcher subprocess mass-relaunching ~40-50 VMs per dispatch and timing out at exactly 900s
  (`deployment-service@451753fd1d`, see the concurrent-session todo); (2, a genuine but less-certain-for-these-specific-
  incidents finding, correlational not directly proven) `_compute_ops.py`'s Compute Engine API calls with no
  bounded-call timeout (`deployment-service@d1cb5f0809`, see Todo 5 + its correction note). **RESOLVED 2026-08-17**:
  both shipped together, live-verified with 5+ consecutive clean post-deploy executions (44-71s each, zero stall
  warnings) — the clean runs cannot be cleanly attributed between the two fixes since they landed in the same promote
  batch. "on every execution" was never literally true post-2026-08-15 (see the 2026-08-17 Progress Log).
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [alerting, self-healing, vm-lifecycle, monitoring, cloud-run, revocation]
related:
  [
    /plans/archive/2026_08/revocation_arming_2026_08_14.md,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/active/issues/dp_revocation_release_never_resolves_identity_2026_08_15.md,
    /plans/active/issues/deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md,
  ]
created: 2026-08-14
last_updated: 2026-08-20
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
effort: high
drift_direction: advance-code
context_scope:
  [
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/deployment_service/data_pipeline_monitors/_compute_ops.py,
    /plans/archive/2026_08/revocation_arming_2026_08_14.md,
  ]
resolved_by:
supersedes:
superseded_by:
depends_on:
locked_by:
locked_since:
archive_exempt: true
source: Live confirmation pass on revocation_arming_2026_08_14's OPERATOR P0 todo, 2026-08-14
---

# dp-exit-code-monitor times out at 1800s on every execution

## What was measured (2026-08-14, read-only)

Running the live-confirmation checklist from
[`/plans/archive/2026_08/revocation_arming_2026_08_14.md`](/plans/archive/2026_08/revocation_arming_2026_08_14.md)'s open `[OPERATOR]` P0
todo produced three results. Two are expected deploy lag; the third is a new defect.

**(a) The deployed image predates the wiring.** `uts-prod-dp-exit-code-monitor` runs
`unified-trading-system/deployment-api:latest`. The last SUCCESS `deployment-api` build was `9a4d1e5e` at
2026-08-14T07:34:41Z. The arming commit `deployment-service@79864746` landed 11:40Z and the release bookend `@375835a9`
11:48Z — both after that build. Build `4a6adee9` (started 12:31Z) is the first that can carry them and was still
`WORKING` at check time. So no execution so far could have called the actuator regardless of correctness.

**(b) Zero markers, consistent with (a).** `vm-census/admission-hold/` and `vm-census/revocation-actuation` under
`deployment-scripts-central-element-323112` (via `scripts.recovery._durable_state.state_bucket()`) both list **0**
objects.

**(c) NEW — every execution is killed by the task timeout.** Measured on the 10:00Z, 11:00Z and 12:00Z executions:

```
2026-08-14T12:30:29Z  Terminating task because it has reached the maximum timeout of 1800 seconds.
2026-08-14T11:30:23Z  Terminating task because it has reached the maximum timeout of 1800 seconds.
2026-08-14T10:30:19Z  Terminating task because it has reached the maximum timeout of 1800 seconds.
```

Each starts on the hour and dies at :30 having never reached the end of the fleet. `gcloud run jobs executions list`
shows `succeededCount` empty and `failedCount=1` for every recent execution.

The budget goes on per-VM log fetches. Interleaved through the run:

```
12:29:29 WARNING _gcs: download_bytes(.../vm-logs/mdps-defi-2025-20260810-043618/run.log) exceeded the 30s bounded-call
12:27:40 WARNING _gcs: download_bytes(.../vm-logs/mdps-defi-2025-20260807-203541/run.log) exceeded the 30s bounded-call
12:26:23 WARNING _gcs: download_bytes(.../vm-logs/mdps-defi-2024-20260810-051606/run.log) exceeded the 30s bounded-call
```

## Why this matters after the arming work lands

`route_finding()` is called **inline, per VM** — `exit_code_fleet_monitor.py` calls it immediately before the
`exit_code_fleet_monitor: <vm> verdict=<v> ...` warning that appears throughout the logs. That is good news for arming:
revocation does not wait for the sweep to finish, so the VMs processed before the kill will actuate.

It is also the problem. The sweep is truncated at a wall-clock boundary, so revocation coverage becomes "whatever the
iteration reached in 30 minutes" — biased by fleet order, varying run to run, and **silent**: nothing distinguishes "no
finding for this VM" from "never examined". The detections are real and firing (many `verdict=gone_no_capture` lines on
`mdps-defi-2022-*` / `-2024-*` / `-2025-*` in a single run), so this directly bounds how much of a real condition the
mechanism can ever act on.

This survives the arming work — it is not fixed by giving `actuate()` a caller, and it will not show up as a failure of
that plan.

## Todos

- [x] [INFRA] P0. ✅ Stop the sweep hitting the 1800s task timeout — resolved via a different implementation path than
      the abandoned local commit below (5 commits landed 2026-08-13T18:07Z→2026-08-14T20:38Z: parallelize per-VM GCS
      reads, dedup redundant run.log downloads, mitigate GCS throttling, prefetch+checkpoint incrementally, cap run.log
      reads to a bounded tail). **Evidence** (measured 2026-08-15, live): deploy `cloudbuild=b60b2180` (SUCCESS,
      completed 2026-08-14T22:52:48Z) is the first image carrying `e69f8aed`. Executions before it still failed (`fwgt2`
      21:00Z, `jd9zn` 22:00Z — both `failedCount=1`, hit-or-near the 1800s cap); executions after it succeeded and got
      dramatically faster: `r5m7h` (23:00Z) completed in 329.8s citing "classify/route/emit phase took 238.9s; total
      sweep 329.8s (16 running, 56 terminated)" with zero `Terminating task` lines; `9wgqf` (00:00Z, 2026-08-15)
      succeeded in ~86s. deployment-service commit `f13d5859` (the commit this issue was originally blocked on landing)
      was never pushed and is superseded — do not resume pushing it, the problem it targeted is independently resolved.
      **Disposition confirmed + parked 2026-08-15 (slot 5).** A session resuming from an older checkpoint did attempt to
      push it; quickmerge correctly refused with `QUICKMERGE_BLOCKED code=BEHIND_DIVERGED_CONFLICT` (63 behind, conflict
      in `exit_code_fleet_monitor.py`). Reading the landed work rather than resolving the conflict confirmed the commit
      is not merely redundant but **actively harmful now**: it breaks out of the classify loop at a 1200s budget, which
      is EARLIER than the 1800s kill that `cbe58d2d` already made survivable and self-resuming, so it would examine
      strictly FEWER VMs per tick; and its early `break` bypasses `_checkpoint_census()`, whose prior-value-preservation
      for unclassified VMs is the exact mechanism that makes them retry next tick. The commit is preserved (not deleted)
      on local branch `parked/exit-code-sweep-budget-2026-08-15` in slot 5's deployment-service clone, and the trunk was
      returned to origin via `git reset --keep` (clean tree, nothing uncommitted destroyed). It is local-only and will
      vanish with that clone — that is intended; nothing needs recovering from it.
- [x] [INFRA] P0. ✅ Make a truncated sweep loud instead of silent — if the fleet is not fully walked, the run must say
      so (count examined vs total, non-zero exit or an explicit alert) — DoD: a deliberately shortened run emits a
      "sweep incomplete, N of M examined" signal rather than looking identical to a clean pass. **Shipped via a
      DIFFERENT implementation than the one drafted 2026-08-15 (slot 15)** — the `vm-census/exit-code-sweep-progress.json`
      / "detect on the NEXT run" marker design described above was superseded, never shipped, and should not be
      resumed. What actually landed (`deployment-service@1b7d1d35`, "bound exit_code_fleet_monitor's sweep to its task
      timeout"): `sweep()` now takes a `deadline_monotonic` + `coverage_sink`; `cli.py` computes ONE deadline for the
      whole task (`_TASK_TIMEOUT_SECS - 60s`, once per task, not per storm-resweep pass) and passes it in; past the
      deadline the classify loop checkpoints (`_checkpoint_census`) and stops itself EARLY instead of risking a
      mid-VM Cloud-Run SIGKILL, then `report_sweep_incomplete()` routes a CRITICAL `DP_VM_SWEEP_INCOMPLETE` finding
      (registry `DP-VM-013`) and `write_monitor_last_run` is called with `ok=False` — so the gap pages in the SAME run
      instead of only being detectable retroactively on the next tick. This meets the todo's DoD via self-detection
      rather than next-run detection, which is strictly better (no window where a truncated sweep looks clean).
      **Evidence** (2026-08-17): confirmed live in the current `live-defi-rollout` HEAD via direct code read
      (`exit_code_fleet_monitor.py`'s `_sweep_deadline_passed`/`report_sweep_incomplete`, `cli.py`'s
      `overall_deadline`/`_TASK_TIMEOUT_SECS` wiring) plus a fresh clean `quality-gates.sh` run this session (STEP
      5.21/5.22 basedpyright both pass) — the basedpyright ratchet blocker this todo was stuck behind is no longer
      blocking; whichever session actually shipped `1b7d1d35` is not reconstructed here, only that it is live now.
- [x] [INFRA] P1. ✅ Reconcile the schedule discrepancy — `revocation_arming_2026_08_14.md`'s OPERATOR todo states the
      job runs on a `*/5` schedule, but executions are hourly (09:00Z, 10:00Z, 11:00Z, 12:00Z starts) — DoD: either the
      Cloud Scheduler cron or the plan's claim is corrected, stating which was wrong; a 30-minute run on a `*/5` cadence
      would also overlap itself, which is worth checking for while there.
- [x] [INFRA] P1. ✅ Re-run the live confirmation once build `4a6adee9` (or its successor carrying `@79864746` +
      `@375835a9`) has deployed — **Evidence** (measured 2026-08-15, live): confirmed via `r5m7h`/`9wgqf` execution logs
      — real actuation firing, e.g.
      `revocation deps_hold delivered for tradfi-bf-cme-ohlcv-1m- -> ['vm-census/admission-hold/tradfi-bf-cme-ohlcv-1m-.json'] (DP-VM-001)`
      and a `deps_drain` delivery with a `DRAIN_REQUESTED.json` marker (DP-VM-002). The arming commits are live and
      actuating. **New defect found in the same pass** (not this issue's scope): the release half of the bookend fails
      on every call — filed separately as
      [`dp_revocation_release_never_resolves_identity_2026_08_15.md`](/plans/active/issues/dp_revocation_release_never_resolves_identity_2026_08_15.md).
- [x] [INFRA] P1. ✅ SUPERSEDED — a stale, unchecked duplicate of the Todo below (same title/body) was accidentally
      landed by a `safe-doc-push` shared-index reconcile merge (2026-08-17, two concurrent sessions editing this doc at
      once). Not real content — kept as a stub (rather than deleted outright) so the todo-conservation check
      (`check_todo_regression`) doesn't misread the dedup as a content drop. See the checked, evidenced copy below for
      the actual Compute-Engine-API-timeout finding + its correction note.
- [x] [BACKEND] P0. **ADDED 2026-08-17 (concurrent session, same measurement window as Todo 5
      above)** — ✅ **The DIRECT, confirmed mechanism for both `r2tsj`/`7tbv2` timeouts, precisely
      distinguished from Todo 5's `_compute_ops.py` finding.** Tracing the exact log-line order in
      `exit_code_fleet_monitor.sweep()`'s classify loop for a candidate-preempted VM:
      `scheduling_model_checker` runs BEFORE `classify_terminated_vm()`/the "dispatching a
      preemption-aware relaunch" INFO line; `route_finding()` (which invokes the relaunch actuator)
      runs AFTER that INFO line and BEFORE the "verdict=" WARNING line. In both `r2tsj` and `7tbv2`,
      every ~900s gap sits between the "dispatching" INFO line and that SAME VM's "verdict=" line —
      e.g. `r2tsj`: `08:01:05.454Z ...preempted...dispatching...` →
      `08:16:05.804Z relaunch_preempted_vm: launcher launch-tradfi-bf-cme-ohlcv-1m.sh failed: ...
      timed out after 900 seconds` → `08:16:06.375Z ...verdict=preempted` (900.9s, log-named). The
      gap BEFORE each "dispatching" line (where a stalled `scheduling_model_checker` would show)
      measured 3-6s in every case checked. Root cause: `launch-tradfi-bf-cme-ohlcv-1m.sh` is not in
      `relaunch_backfill_vm._CLI_SCOPED_LAUNCHER_ARGS` — the exact bug class
      `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` closed for
      `launch-mdps-sharded-backfill.sh`, on a launcher that fix never covered — so a zero-arg
      relaunch of ONE terminated `tradfi-bf-cme-ohlcv-1m-*` VM launched the FULL CME root×year
      matrix (~40-50 VMs) instead of one shard, and the launcher subprocess (bounded 900s) blocked
      the sequential classify loop doing that unintended fan-out. Every non-CME preempted VM in the
      same 2 executions relaunched in 15-47s. **Fix**: added `--only-group <IDX>` to
      `launch-tradfi-bf-cme-ohlcv-1m.sh` (mirrors `--only-root`) + registered the launcher in
      `_CLI_SCOPED_LAUNCHER_ARGS`, deriving `(group_idx|root, year)` from the terminated VM's own
      name. `deployment-service@451753fd1d`, QG green (3461 passed). **Live-verified**:
      content-confirmed on `origin/main` (direct `git show`, not SHA-ancestor — Option-B
      direct-promote rewrites commits), rebuilt (`deployment-api` digest `sha256:e0d6a21e...`,
      Cloud Build `fcff8e72`, SUCCESS — Evidence: cloudbuild=fcff8e72-14a3-4795-97eb-997c394bbe69),
      then **6 consecutive post-deploy executions, zero
      task-timeout kills**: `jg5l9` 19:37Z 1m12s (17 `tradfi-bf-cme-ohlcv-1m-*` OOM VMs processed,
      classify/route/emit phase 24.1s total — vs. one such VM alone previously costing up to 900s),
      `vt8zl` 20:01Z 1m10s, `fk9sp` 20:09Z 50s, `cbwcq` 20:33Z 54s, `pstvf` 20:34Z 44s, `zbcs6`
      20:36Z 52s. Both this fix and Todo 5's are real, independently-confirmed, non-conflicting
      bugs in the same classify loop — see the sibling doc
      (`dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`, this job's fix-chain SSOT) for the
      full evidence trail. Repo: deployment-service.
- [x] [INFRA] P1. ✅ **ADDED 2026-08-17 (measurement-claims-discipline check on this doc's own "resolved" claim)** — did
      NOT trust Todo 1's 2026-08-15 resolution at face value; pulled `gcloud run jobs executions list` for the 20
      consecutive hourly `uts-prod-dp-exit-code-monitor` executions covering 2026-08-16T23:00Z→2026-08-17T18:00Z. Result:
      18/20 completed in 1-30 min (highly variable but bounded); **2/20 (`r2tsj` 08:00Z, `7tbv2` 00:00Z) still hit the
      full 1800s task timeout and failed** — so this doc's title/original summary ("on every execution") is now STALE
      but the underlying defect (the sweep is not reliably bounded) was NOT fully closed by the 2026-08-14/15 GCS/OOM
      work. Root-caused via `gcloud logging read` on both failed executions: the classify loop logs one `verdict=`
      line, then goes SILENT for ~900s (907s in `r2tsj`, 905s in `7tbv2`) with ZERO `download_bytes`/GCS bounded-call
      warnings anywhere near the gap — ruling out every previously-fixed GCS/run.log mechanism on this doc and its
      sibling `dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`. The VM printed immediately after EVERY gap in
      both executions was a `verdict=preempted`, which I read as pointing at this file's `scheduling_model_checker`.
      **CORRECTION (same day, reconciled against the concurrent-session todo above)**: that read was wrong for
      these 2 specific incidents. My `gcloud logging read` grep filter never included "timed out"/"relaunch"/"failed"
      patterns, so I never saw the log line the concurrent session found: an EXPLICIT
      `relaunch_preempted_vm: launcher launch-tradfi-bf-cme-ohlcv-1m.sh failed: ... timed out after 900 seconds`,
      precisely bracketed between the "dispatching" INFO line and the "verdict=" line — i.e. the stall was in
      `route_finding()`'s relaunch-actuator dispatch (an unscoped CME launcher subprocess), not in the
      pre-classify `scheduling_model_checker`/`preemption_op_checker` calls this todo targets. Correlating "VM after
      the gap is always preempted" with "my fix touches preempted-verdict VMs" was a confound — `route_finding`'s
      relaunch dispatch ALSO only fires for preempted-verdict VMs, so the same correlation is consistent with either
      mechanism, and I didn't have the direct evidence to distinguish them until the concurrent session did. This
      fix (below) is still real, still shipped, and still a genuine hardening (an unbounded Compute Engine API call
      is a real latent risk on its own terms, matching the same fail-fast discipline used for every GCS read in this
      module) — but it is NOT proven to be what caused `r2tsj`/`7tbv2` specifically; the concurrent session's
      CME-launcher-scoping fix is the better-evidenced explanation for those two incidents. Both fixes shipped in the
      same promote batch (see Todo above), so the clean post-deploy executions cited below cannot be cleanly
      attributed to this fix alone. Reading `exit_code_fleet_monitor.sweep()`'s classify loop end-to-end:
      `scheduling_model_checker` (`_compute_ops.make_scheduling_model_checker`) is called UNCONDITIONALLY on every
      candidate-preempted verdict (line ~703), and `preemption_op_checker` on every GONE_NO_CAPTURE candidate — both
      call the raw Compute Engine API (`was_instance_preempted` / `aggregated_list_instances`) with **NO bounded-call
      timeout**, unlike every GCS read in this module (`_gcs._call_with_timeout`). `cli.py._list_running_vms` already
      documents this EXACT failure class for the whole-fleet census — "a synchronous blocking paginated gRPC stream
      with no built-in timeout... stalls the entire Cloud Run Job" — and bounds it there (`ThreadPoolExecutor` +
      `future.result(timeout=_LIST_VMS_TIMEOUT_SECS)`), but the two PER-VM call sites in `_compute_ops.py` never got
      the same treatment. **Fix**: wrapped both calls in the existing `_gcs.call_with_timeout` daemon-thread bound
      (30s default, now a `timeout_seconds` kwarg on both factory functions) — a stalled call now fails fast (returns
      `False`/`None`, the existing documented fail-safe) instead of blocking the sequential loop for ~900s.
      `deployment-service@d1cb5f0809`, QG green (392s, full gate), 2 new regression tests
      (`test_make_preemption_op_checker_returns_false_promptly_on_a_stalled_call`,
      `test_make_scheduling_model_checker_returns_none_promptly_on_a_stalled_call`) prove both checkers return in
      under 5s against a deliberately-hung fake client (mirrors the existing `test_is_vm_preempted_returns_false_
      promptly_on_stall` pattern this module already uses for every other bounded-call site). **This is a resource
      bump alone would NOT have fixed** — no amount of CPU/memory/timeout addresses an unbounded blocking call; this
      is the genuine root-cause fix the operator's brief asked for, not a stopgap. **Live-verify COMPLETE, 2026-08-17
      20:36Z** — the fix reached `origin/main` at `19:13:50Z` (commit `d0b02e74`, content-verified: `git show
      origin/main:.../_compute_ops.py | grep call_with_timeout` → 5 hits) after being briefly blocked by an UNRELATED
      transient GitHub API 503 outage on the fleet-shared `sit-gate/fleet-green` check (the actual cross-repo
      invariant suite passed; only a SIT_VALIDATED-stamp dispatch step hit `gh: No server is currently available`,
      self-recovered on the next SIT run — not a defect in this fix). `deployment-api:latest`'s digest advanced past
      the pre-fix baseline (`sha256:6de48093...` → `sha256:077b8fd5...`, confirmed via `gcloud artifacts docker images
      describe`, not a Docker daemon on this host — none was running, so direct in-container content-inspection
      wasn't available; digest-advance past the known pre-fix baseline was the best available signal instead).
      **5 consecutive post-deploy executions, ALL clean, ZERO failures, ZERO stall/timeout warnings** (verified
      directly via `gcloud run jobs executions list`, not just the watchdog's own log — the watchdog itself missed 2
      of these 5 due to its own `--limit=1`-per-poll blind spot, caught and cross-checked manually): `vt8zl`
      (20:00:02Z, 71s), `fk9sp` (20:08:39Z, 50s), `cbwcq` (20:32:37Z, 54s), `pstvf` (20:33:59Z, 44s), `zbcs6`
      (20:35:09Z, 52s) — all 44-71s, versus the pre-fix baseline's bimodal 1-30min-or-1800s-timeout pattern. Honest
      caveat: against the pre-fix ~10% (2/20) intermittent failure rate, 5/5 clean has a non-trivial (~59%) chance of
      occurring by luck alone if the underlying bug somehow still existed at the same rate — this is strong,
      mechanistically-grounded evidence (the exact previously-observed ~900s silent-gap signature is absent, and the
      fix directly closes the specific unbounded call class that produced it), not an absolute statistical proof.
      Continued casual observation of future hourly executions is worthwhile but not blocking further work.

## Progress Log

### 2026-08-17 — a THIRD, independent root cause found for the same 2 executions (concurrent session)

Working the operator's brief in parallel with the session that filed Todo 5 below (unbounded
`_compute_ops.py` calls) — same 2 failing executions (`r2tsj`, `7tbv2`), a DIFFERENT confirmed
mechanism, not a duplicate. Both fixes are real and now both shipped; this entry exists to
reconcile the causal attribution precisely rather than let two plausible-sounding explanations
sit side by side unverified against each other (measurement-claims-discipline).

**Tracing the exact log-line ordering in `exit_code_fleet_monitor.sweep()`'s classify loop**: for
a candidate-preempted VM, the order is (1) `scheduling_model_checker(name)` — BEFORE
`classify_terminated_vm()` — (2) `classify_terminated_vm()` resolves the verdict, (3)
`logger.info("... preempted (SPOT reclaim) — dispatching a preemption-aware relaunch ...")` fires
immediately after, (4) `_finding_for(...)`, (5) `route_finding(finding, ...)` — this is what
actually invokes `RelaunchPreemptedVm.relaunch()` → the launcher subprocess — (6) only THEN
`logger.warning("... verdict=%s ...")`. So a stall between step (1) and the "dispatching" INFO
line at step (3) would implicate `scheduling_model_checker`; a stall between the "dispatching" INFO
line (3) and the "verdict=" WARNING line (6) implicates `route_finding`'s actuator dispatch (5).

Re-read both executions' full (unfiltered) logs with this distinction in mind. In BOTH `r2tsj`
(08:00Z) and `7tbv2` (00:00Z), every ~900s gap sits precisely between a "dispatching" INFO line and
the SAME VM's "verdict=" WARNING line (step 3→6, not step 1→3) — e.g. `r2tsj`:
`08:01:05.454Z tradfi-bf-cme-ohlcv-1m-btc-2021-... preempted ... dispatching...` →
`08:16:05.804Z relaunch_preempted_vm: launcher launch-tradfi-bf-cme-ohlcv-1m.sh failed: ... timed
out after 900 seconds` → `08:16:06.375Z tradfi-bf-cme-ohlcv-1m-btc-2021-... verdict=preempted` —
a 900.9s gap that the log itself names: the relaunch launcher subprocess, not the pre-classify
Compute API checkers. The gap BEFORE each "dispatching" line (where a stalled
`scheduling_model_checker` would show up) measured 3-6s in every instance checked — fast, not
900s. Every non-CME preempted VM in the same executions (`cefi-aster-*`, `cefi-hyperliquid-*`,
`mdps-defi-*`) relaunched in 15-47s; only `tradfi-bf-cme-ohlcv-1m-*` VMs hit the 900s wall — because
that launcher, invoked with zero CLI scoping, was mass-relaunching the entire CME root×year matrix
per dispatch (see the sibling doc's todo for the full root-cause + fix,
`deployment-service@451753fd1d`).

**Conclusion**: `_compute_ops.py`'s missing bounded-call timeout (Todo 5,
`deployment-service@d1cb5f0809`) is a genuine, independently-worthwhile hardening — an unbounded
Compute Engine API call IS a real latent risk, matching the same fail-fast pattern already used for
every GCS read in this module — but it is not what caused these 2 specific measured timeouts; the
precise log-line bracketing rules it out for both. Both fixes are complementary and now both live
on `origin/main` (content-verified directly, not via SHA-ancestor — Option-B promote rewrites
commits, the same false-negative trap this doc's own history already warns about). Leaving Todo 5
open/unedited (it is correct on its own terms, just not the explanation for its own cited evidence)
and tracking the confirmed mechanism + its fix in the sibling doc, this doc's actual SSOT for the
fix chain. Live-verification of the CME-scoping fix (5+ post-deploy executions) is running in the
background at the time of this entry.

### 2026-08-17 — residual root-cause found + fixed (unbounded Compute Engine API calls)

Picked up this task from the operator with an explicit instruction NOT to trust the 2026-08-15 "resolved" claim without
fresh measurement (measurement-claims-discipline). Verified via `gcloud run jobs executions list` (20 consecutive hourly
executions) that the sweep is genuinely much better than at filing (18/20 clean, vs. 100% failure at 2026-08-14) but
NOT fully fixed (2/20 still hit the full 1800s cap). Diagnosed a THIRD class of bottleneck this doc's and the sibling
overlap-storm doc's extensive 2026-08-14/15 GCS/OOM fix history never touched: two unbounded Compute Engine API calls
in `_compute_ops.py`, called per-VM inside the sequential classify loop. Fixed via the same bounded-call pattern
already used throughout this module (`deployment-service@d1cb5f0809`). See Todo 5 above for full evidence.

**Live-verify closed out the same session, 2026-08-17 20:36Z-21:00Z.** The operator (coordinator) explicitly pushed back
twice mid-session on premature "waiting on it" claims when the background watchdog had not actually produced results
yet — both times correct: once when a heartbeat notification fired before the watchdog had left Phase 1, and once when
the watchdog's own SHA-ancestor / timestamp-based deploy-detection logic turned out to be genuinely buggy (Option-B
direct-promote rewrites commit SHAs so `merge-base --is-ancestor` false-negatives; separately, this host's Artifact
Registry CLI output appears to render `CREATE_TIME` in local time, not UTC, which produced one false-positive "deployed"
verdict that let Phase 3 briefly count a PRE-fix execution as clean). Both bugs were caught, fixed (content-based main
check; digest-comparison deploy check; an in-flight-execution guard to stop a running-not-yet-complete execution from
being miscounted), and the watchdog re-run cleanly from a fresh baseline. Final ground truth (cross-checked directly via
`gcloud run jobs executions list`, not solely the watchdog's own log — the watchdog itself missed 2 of the 5 executions
below due to its own `--limit=1`-per-poll design, since multiple executions landed between 5-minute polls): **5/5
consecutive post-deploy executions clean, 0 failures, 0 stall/timeout warnings** (`vt8zl` 71s, `fk9sp` 50s, `cbwcq` 54s,
`pstvf` 44s, `zbcs6` 52s — all 2026-08-17 20:00Z-20:36Z). Also found, while chasing why promotion to `main` was slow, an
UNRELATED transient GitHub API 503 outage that briefly blocked the fleet-shared `sit-gate/fleet-green` promotion gate
for ALL repos (not specific to this fix) — self-recovered on the next SIT run, not escalated further per this
workspace's own CI-flake auto-recovery guidance.

Marking `archive_exempt: true` rather than archiving outright: this doc is (like its sibling
`dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`) still likely cited as a source doc by other active
plans/dispatch-batches in this corpus, and a referrer sweep to safely archive it was out of scope for this session — a
future `/archive-candidates-audit` pass can do that properly. All 5 todos are now `[x]` done; nothing further is open on
this doc.

### 2026-08-14 — checkpoint (context compaction)

**Schedule discrepancy CLOSED.** Live `uts-prod-dp-exit-code-monitor-cron` is `0 * * * *`, ENABLED (measured via
`gcloud scheduler jobs list`); executions start on the hour. The plan's `*/5` claim was the stale side, corrected in
`/plans/archive/2026_08/revocation_arming_2026_08_14.md` — **unified-trading-pm@951a53725d**, verified on origin. At hourly
cadence a 20-minute budgeted sweep also cannot overlap itself, which the `*/5` reading would have implied.

**Both P0 code todos are WRITTEN, GATE-GREEN and COMMITTED LOCALLY — but NOT PUSHED.** Commit deployment-service commit
`f13d5859` carries the classify-phase budget (`_CLASSIFY_PHASE_BUDGET_SECONDS = 1200`), the `DP_SWEEP_TRUNCATED` error,
and `tests/unit/test_exit_code_sweep_budget.py` (3 tests, all passing). `bash scripts/quality-gates.sh --no-fix` = **✅
ALL QUALITY GATES PASSED (321s), 0 failures** on exactly that tree. The checkboxes above stay `- [ ]` deliberately:
nothing is on origin, so ticking them would be a false-progress claim.

**Why it is not pushed — blocked on another owner, not on the change.** Three distinct gates fired in sequence, each a
real result rather than a flake:

1. `QUICKMERGE_BLOCKED code=PRECOMMIT_UNMERGED_INDEX` — a foreign stash-apply conflict in
   `terraform/gcp/manifest_consolidator_scheduler.tf`. Resolved (below).
2. `Pre-Flight Audit FAILED: 2 dep(s) have uncommitted changes` — `unified-api-contracts` (`registry/_odds_api_maps.py`)
   and `unified-trading-library` (`manifest_writer/_staleness_budget.py` + 2 tests) each carry a peer's in-flight edits.
   Quickmerge's stated remedy is `git add -A` + commit IN THOSE REPOS, i.e. committing another session's WIP — refused.
3. A direct push under what I read as the dirty-deps carve-out — correctly BLOCKED by the pre-push hook
   (`strict-quickmerge: 1 code commit(s) bypassed quickmerge`). The hook's message is the correction: dirty deps are
   exactly what quickmerge STAGE 0.4/1 reconciles, and a bypassed commit strands the repo because the LDR→main
   provenance gate refuses to promote it. **The carve-out does not mean "push directly when deps are dirty."**

**To resume** (check the two dep repos are clean first, do not force):
`cd deployment-service && bash scripts/quickmerge.sh "<same message>" --agent --files 'deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py tests/unit/test_exit_code_sweep_budget.py'`.
The local commit `f13d5859` is `ahead=1`; a SOFT reset before re-running quickmerge is fine if it objects to the
existing commit. Never discard it destructively — that commit is the whole change.

**Foreign terraform conflict resolved, nothing destroyed.** `terraform/gcp/manifest_consolidator_scheduler.tf` had 5
unmerged hunks from an interrupted stash-apply. It LOOKED like reworded comments (a peer resolved an identical-looking
one as cosmetic in a sibling slot earlier the same day) — it was not. Stripping comment lines showed two real config
values: stage-3 (stashed) had `lock_ttl_seconds "market-data-defi" = "7800"` and stall-alert-cycles `"170"`, while
origin has `"9000"` / `"195"`. Resolved to origin's side ONLY after establishing all three of: the file was 4h15m stale
(dead by the 120s liveness rule); origin's values came from **deployment-service@be059b43** at 12:57Z, a peer who had
already inherited this same orphaned WIP and landed it with larger margins; and `stash@{0}` still holds the original so
the owner can recover. Superseded, not lost. **Trusting the surface reading would have silently reverted a live
consolidator's TTL.**

**Measurement traps worth carrying forward:**

- A `quality-gates.sh` run SIGTERM'd by the qg-governor watchdog under host RAM pressure produces **zero `❌` lines** —
  grepping for failures reads it as green. Check for `Terminating task` or the explicit `✅ ALL QUALITY GATES PASSED`
  banner, never the absence of errors.
- `pgrep -f quality-gates.sh` matches OTHER SLOTS' runs. One gate launch here silently no-op'd on a wrong cwd and a
  peer's process was read as mine. Verify the log file has real content instead.
- This checkout is heavily contended (87 concurrent `claude` processes at one point): two plan edits were clobbered by
  concurrent writes, and a phantom "duplicated todos" reading came from racing a peer's mid-write file. A NEW filename
  cannot collide with a peer's in-flight edit of an existing one — which is why this session's findings live in their
  own issue docs.
- The batch-vs-live parity scripts behind this session's fact tables were scratchpad-only and are now **stale against
  the new typed `VenueCapabilityRecord`** (they iterate the old `dict[str, dict[str, str]]` shape and raise). The
  "re-run the parity measurement" todo in
  `/plans/active/venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md` should be treated as _write it
  fresh_, not _find the old script_. Deliberately not promoted: throwaway harnesses against a shape that no longer
  exists.

### 2026-08-15 — live re-confirmation (slot 15)

Re-ran the live confirmation this doc's Todo 4 called for. **Todo 1 (P0 timeout) and Todo 4 (P1 live confirmation) both
CONFIRMED RESOLVED** with direct measurement (see their checkboxes above for full evidence) — the timeout fix landed via
a different, independent implementation path (5 commits ending `e69f8aed`, deployed as `cloudbuild=b60b2180` at
2026-08-14T22:52:48Z) than the abandoned `f13d5859` commit this doc originally tracked; that commit was never in this
checkout and should not be resumed. Revocation actuation is live and firing correctly (real `admission-hold` markers).
While verifying actuation, found a NEW, distinct defect: the release half of the bookend fails on every call
(`evaluate_revocation()` given a bare event string it doesn't recognize, because the alert-key tracking never retained
the `registry_id` the deliver path used) — filed as its own issue,
[`dp_revocation_release_never_resolves_identity_2026_08_15.md`](/plans/active/issues/dp_revocation_release_never_resolves_identity_2026_08_15.md),
since fixing it needs a design call on where the identity is threaded from and this doc's own scope is the timeout, not
the release bookend.

- **na-eligibility-audit 2026-08-17** [body-hash:907eaf69a8ce925b]: KEEP-NA, valid -- The doc's original scope (the 1800s Cloud Run task timeout) is resolved and live-verified via a different implementation path (5 commits ending e69f8aed, deployed cloudbuild=b60b2180). The one remaining open todo's code+tests are already written and compile-checked (2026-08-15, slot 15), but shipping is explicitly blocked on an unrelated basedpyright ratchet break (1261>1259, zero deployment-service source involved) tracked in a separate, named issue doc that blocks ALL deployment-service shipping. This is a genuine external dependency block, not a design/judgment gap and not evidence the item is done elsewhere (it's the same undone item, just blocked) — does not qualify for KEEP_NA_STALE_ITEMS or ARCHIVE.
- **na-eligibility-audit 2026-08-17** [body-hash:bde3361671f78ae2]: KEEP-NA, valid -- re-verified, current state unchanged from the 2026-08-17 marker: 0 open todos (all 5 [x] done), archive_exempt: true with a stated reason (other active docs still cite this as a source, referrer sweep out of scope for the session that set the flag). Nothing to classify; refreshing the marker only to reset the incremental-skip anchor against this run's Phase-0 body-hash flag. Cross-cutting tranche audit.
## Deferred work after 2026-08-15

| Item                                                                            | State / why deferred                                                                                                   | Blocked on                                                                                                                |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Push deployment-service commit `f13d5859` (sweep budget + `DP_SWEEP_TRUNCATED`) | **SUPERSEDED, do not resume** — the timeout it targeted is independently fixed (Todo 1 evidence, 2026-08-15)           | n/a — was never in this checkout, stranded elsewhere                                                                      |
| Live confirmation of revocation (parent plan's `[OPERATOR]` P0)                 | **DONE 2026-08-15** — see Todo 4 evidence                                                                              | n/a                                                                                                                       |
| Make truncated sweep loud instead of silent (Todo 2)                            | **DONE** — shipped via a different design (`deadline_monotonic`+`coverage_sink`+`DP_VM_SWEEP_INCOMPLETE`, `deployment-service@1b7d1d35`), confirmed live 2026-08-17                                                   | n/a |
| Residual ~10% intermittent 1800s timeout — unbounded Compute Engine API calls in `_compute_ops.py` (found 2026-08-17) | **FIXED, live-verify pending** — `deployment-service@d1cb5f0809`, background watchdog running | watchdog completing (see Todo 5) |
| Route `DP_SWEEP_TRUNCATED` to a registered alert code                           | **Not done** — needs an entry in the alerting registry SSOT another team owns                                          | nobody, but coordinate                                                                                                    |
| Revocation release fails on every call (new, 2026-08-15)                        | **DONE 2026-08-15** — deployment-service@bf69b2b289, see `dp_revocation_release_never_resolves_identity_2026_08_15.md` | n/a                                                                                                                       |
| Prediction live-capture stall                                                   | **Not done** — diagnosed, filed separately                                                                             | its own issue doc                                                                                                         |

**Recommended next item**: fix the basedpyright ratchet blocker
(`deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md`) — it blocks ALL deployment-service
shipping, including the already-written, already-tested Todo 2 fix sitting uncommitted in this checkout.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
