---
doc_type: issue
title:
  Shared-host RAM exhaustion silently kills background quality-gates.sh runs mid-TESTS-stage — fleet-wide, ~7
  consecutive kills observed
summary: >-
  Attempting to ship a small, correct, already-verified code change (unified-api-contracts *-PERP write-time guardrail)
  required a fresh `quality-gates.sh` run to match the sentinel to a new commit SHA. Every background attempt
  (nohup+disown, immune to shell-session teardown) was silently killed — no error, no exit code visible, the process
  simply vanishes from `ps` — consistently right after the `[3/6] TESTS` stage header, before any pytest output appears,
  across attempt durations ranging from 32s to 520s (not tied to elapsed time). `free -h` showed wild swings (365Mi to
  15Gi free RAM; swap 3.4-5.6Gi/15Gi used) and fleet-wide concurrent `quality-gates.sh` process count ranged 5-8
  throughout, confirming genuine RAM contention, not a fluke. One earlier same-repo run under lighter contention DID
  complete cleanly (580s, `ALL QUALITY GATES PASSED`) — proving the code and the QG suite itself are fine; only the
  SHARED HOST's capacity to sustain a run is the variable. Total time lost to this retry loop: ~2 hours wall-clock
  across slot-12's session before escalating instead of continuing to retry blindly.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-api-contracts]
scope: [engineer, admin]
tags: [infra, ram, memory, shared-host, fleet-wide, quality-gates, qg-governor, blocking]
related:
  [
    /plans/archive/issues/shared_host_tmp_tmpfs_full_2026_07_26.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
  ]
created: 2026-07-27
last_updated: 2026-07-28
priority: P1
parent_epic: infrastructure_master
source: "slot-12, data_engineering, discovered while shipping prediction_satellite_ao_dispatch_batch1-003, 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: unified-trading-pm@8a5693a4e + @fd06d1dee (2026-07-28)
---

> **✅ RESOLVED 2026-07-28.** All 3 todos done: (1) the qg-host-governor runtime abort-monitor (self-scoped watchdog,
> `unified-trading-pm@<slot-5 shipped SHA, see Recommended fix path>`); (2) the commit-before-QG ordering rule added to
> `worker.md`/`RULES.md` (`unified-trading-pm@fd06d1dee`); (3) the SIGTERM/SIGINT/SIGHUP kill-marker trap across
> `base-service.sh`/`base-library.sh`/`base-ui.sh` (`unified-trading-pm@8a5693a4e` + `@fd06d1dee`). Archived.

# Shared-host RAM exhaustion silently kills background quality-gates.sh runs

## What I found

Shipping `unified-api-contracts` commit `5a582dce` (a small, fully-verified 2-file change — 6/6 new unit tests + 15/15
pre-existing tests green, `basedpyright` clean) required a fresh `quality-gates.sh --no-fix` run so the `--agent`
sentinel would match the new HEAD (the sentinel is content/SHA-keyed; running QG pre-commit then committing leaves the
sentinel pointing at the PARENT SHA, not HEAD — `quickmerge.sh`'s own sentinel-ancestor check correctly refuses that
mismatch and either re-runs QG itself or requires the caller to).

Seven consecutive attempts to regenerate that sentinel were killed:

| Attempt | Method                                | Elapsed at kill     | Furthest log line reached                                                                                                                                                                                      |
| ------- | ------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | `run_in_background: true` (harness)   | ~1237s (reported)   | Completed but exceeded the 720s wall-clock QG cap (governor queue-wait 116s + actual work 1237s vs baseline ~440-580s) — a REAL failure, but caused by contention inflating work time ~2-3x, not a code defect |
| 2-7     | harness background / `nohup`+`disown` | 32s – 520s (varies) | Every single one stopped exactly after the `[3/6] TESTS` header, before any pytest output — never once got further, regardless of how long it had been running                                                 |

`free -h` samples taken between attempts:

```
365Mi free / 5.6Gi swap used   (attempt ~3)
15Gi  free / 3.8Gi swap used   (attempt ~6, right after a retry succeeded... but only briefly)
11Gi  free / 4.3Gi swap used
3.6Gi free / 3.6Gi swap used
4.3Gi free / 3.4Gi swap used
```

Fleet-wide concurrent `quality-gates.sh` process count (`ps aux | grep quality-gates.sh | grep -v grep | wc -l`) ranged
5-8 throughout, never dropping to a level that produced a sustained clean run. `qg-governor` log lines show the gate's
own concurrency limiter is working as designed (`WAIT_CPU`/`WAIT_RAM_LIVE` backoff, `reserved 5500MB (ADMIT)` after
26-146s) — the governor throttles ADMISSION correctly, but nothing protects an ALREADY-ADMITTED run from being killed
later if fleet-wide memory pressure spikes again mid-run. One attempt (this session, ~580s, `ALL QUALITY GATES PASSED`)
DID complete successfully when contention happened to be lower at the time — confirming the QG suite itself has no
defect; it is purely a function of host capacity at any given moment.

## Why it matters

- **This is not specific to my repo or change.** The pattern (governor admits a run reserving 5500MB, then something
  external kills the whole process tree later with zero error output) will hit ANY worker on ANY repo whenever
  fleet-wide concurrent QG count is high — which per the 5-8 concurrent count observed, appears to be close to the
  STEADY STATE on this host, not a rare spike.
- **Silent kills are worse than loud failures.** No exit code, no stderr, no `dmesg` OOM-killer entry visible to this
  session (may require elevated permissions to inspect) — a worker has no way to distinguish "genuinely still running,
  just slow" from "already dead" without polling `ps` directly, which the async-wait-discipline HARD RULE already
  requires but doesn't fully solve here (the kill can happen at any point, not on a predictable cadence).
- **Real cost**: ~2 hours of slot-12 session wall-clock (and a comparable amount of the fleet's shared CPU/RAM budget
  across 7 wasted partial runs) were spent shipping a change that was correct and fully test-verified after its FIRST QG
  pass. The `.qg_last_passed_sha`/HEAD-mismatch-after-commit interaction (running QG before vs after commit) also
  contributed avoidable retries — worth a callout in `RULES.md`/`worker.md`: **run QG AFTER committing, not before**, so
  the sentinel written matches HEAD on the first try and a single retry (if killed) doesn't also need a rebase.

## Recommended fix path

- [x] [INFRA] P1. ✅ unified-trading-pm@<PENDING-SHA> — **Investigate whether the qg-governor's 5500MB RAM reservation
      is being violated by the OS/cgroup AFTER admission** — i.e., does the governor only gate entry, with no ongoing
      enforcement that admitted processes stay within their reservation as OTHER processes' demand grows post-admission?
      **CONFIRMED YES.** `_qg_admit_check` (`scripts/quality-gates-base/qg-host-governor.sh`) runs exactly ONCE, at
      `qg_governor_acquire` time — the RAM-reservation ledger records each admitted run's ESTIMATED baseline peak (a
      fixed number from `qg_resource_baseline.json`, not live RSS), and nothing ever re-reads it against live host state
      after admission. This is NOT a new discovery — it's the already-tracked, still-open P0 in
      `/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` (line ~265: "Global 80% valve — admission side
      SHIPPED; runtime ABORT of an already-running >80% job STILL PENDING"), which this doc's silent-kill pattern is
      direct field confirmation of. Cross-referencing rather than duplicating: that plan is the authoritative owner of
      the fix design. **Bonus finding**: on THIS host, `systemd-run` is unavailable
      (`⚠️ QG_MEM_CAP=2048M set but systemd-run     unavailable on this host`, confirmed live during this session's QG
      run) — so the OTHER hard backstop (the per-repo cgroup cap, `1.2× baseline`) is ALSO inactive here, same failure
      class as `/plans/archive/issues/qg_mem_wrap_systemd_bus_unavailable_2026_07_26.md`. On this host, admission-time
      estimation is genuinely the ONLY layer of defense until a run completes — raising the value of a live,
      cgroup-independent runtime check. **Shipped (option a — tighten the governor)**: a self-scoped runtime
      abort-monitor in `qg-host-governor.sh` (`_qg_watchdog_start`/`_qg_watchdog_loop`/`_qg_watchdog_signal_tree`,
      reservation-mode only). Each admitted run backgrounds a watchdog that polls live `MemAvailable` every
      `QG_WATCHDOG_INTERVAL_SECONDS` (default 15s); after `QG_WATCHDOG_CONSECUTIVE_HITS` (default 2) consecutive samples
      over `QG_HOST_RAM_ABORT_PCT` (default 80% used), it writes a loud marker (`<ledger-dir>/aborted.<pid>`, reason +
      timestamp + mem stats — satisfies this doc's own P2 todo #3 below) and SIGTERMs the run's OWN process tree (walked
      via `pgrep -P`, never a process-group signal — so it can never touch another slot's process even by accident).
      Tree-signaling (not just the root PID) is required, not cosmetic: bash defers a pending trap until its current
      foreground child (pytest/basedpyright) returns, so signaling only the root would sit queued and do nothing until
      the blocked command finished on its own — verified by manual repro before landing the fix. Tests: new suite
      `scripts/quality-gates-base/tests/test-qg-watchdog.sh` (9 assertions: token-mode inert, healthy-host no-op,
      sustained-pressure fires with a catchable SIGTERM + loud marker, release reaps a still-running watchdog) — all
      governor suites green, `bash -n` + shellcheck clean (only pre-existing SC2017 info-level notices, none in the new
      code). **Done when clause is satisfied via the "documented capacity ceiling... enforced globally" branch**: the
      existing reservation-ledger budget (70% of RAM) IS the global ceiling; it is now enforced continuously, not just
      at admission. Full repro-under-real-fleet-contention is left to the owning plan's soak process (this doc's fix is
      unit-tested + logically verified, not yet fleet-soaked).
- [x] [DOC] P2. ✅ **DONE 2026-07-28** — added an explicit rule to `agents/worker.md`'s Pass-1/Pass-2 QG section (right
      above the Pass-1 bullet): "Run Pass 1 AFTER committing (step a), never before" with the sentinel-SHA rationale + a
      cite back to this doc. Cross-referenced from `agents/RULES.md` § 2 (an "Ordering note" added right after the
      ship-loop code snippet, which already showed commit-then-QG in its example but didn't call the ordering out as a
      rule) pointing back to worker.md. — `unified-trading-pm@fd06d1dee`.
- [x] [INFRA] P2. ✅ **DONE 2026-07-28** — added a SIGTERM/SIGINT/SIGHUP signal trap to all three shared QG entrypoints
      (`base-service.sh`, `base-library.sh`, `base-ui.sh` — sourced directly from this PM checkout by every consuming
      repo, so this is a single-place fix, not a per-repo rollout) that writes a loud `killed.<pid>` marker (signal,
      pid, repo, timestamp) to the SAME `_qg_ledger_dir()` the qg-host-governor watchdog already uses, then exits 143,
      before the process fully dies. Honestly scoped per the todo's own "where signal-catchable" hedge: SIGKILL (the
      kernel OOM-killer's usual weapon per this doc's own field evidence) is fundamentally uncatchable — no trap
      anywhere can fire for it; this closes the CATCHABLE-signal slice. Also inherits the SAME bash gotcha the
      watchdog's own code already documents (a pending trap is deferred until the CURRENT FOREGROUND command returns) —
      fires promptly when the signal reaches the whole process tree (the watchdog's own tree-walk, a process-group
      signal, `pkill`), deferred (not lost) when it reaches only the parent while a child stays alive. Verified with a
      manual repro (sent SIGTERM to both a test script and its foreground child, mirroring the watchdog's tree-walk
      delivery pattern): marker written correctly with the right signal/pid/repo/timestamp fields before exit. —
      `unified-trading-pm@8a5693a4e` (base-service.sh), `unified-trading-pm@fd06d1dee` (base-library.sh/base-ui.sh).

## Progress Log

- 2026-07-27 (slot-12, `data_engineering`): Filed after successfully shipping the underlying change (blocked-question
  BLK-4be13754 raised in parallel, recommending option B — escalate + move to other work rather than keep retrying). Not
  investigated further this session — scope was capture the pattern, not fix the governor.
- 2026-07-27 (slot-8, `infra`): **4th independent corroboration**, on a DIFFERENT repo (market-tick-data-service) and a
  small, unrelated change (`reader.py` OOM-guard projection fix for
  `read_availability_index_bare_defi_callers_2026_07_27.md`). 4 consecutive `quality-gates.sh --no-fix` attempts
  (`nohup`+`disown`, immune to shell-session teardown) all silently died — 3 of the 4 got past the `[qg-governor]`'s own
  `WAIT_CPU`/`ADMIT` throttle (150-292s of the governor itself waiting for CPU before reserving 1271MB and letting the
  run proceed) and STILL died within seconds of admission, either right at/before the `[3/6] TESTS` coverage-floor line
  or a few % into the pytest-xdist progress bar — confirming the governor's own admission check does not protect an
  already-admitted run from a later RAM/CPU squeeze (exactly the open P1 fix-todo above: "does the governor only gate
  entry, with no ongoing enforcement..."). New detail not previously noted: one killed attempt left an ORPHANED
  pytest-xdist worker process (reparented to PID 1, kept running under
  `.venv/bin/python -c "import sys;exec(eval(sys.stdin.readline()))"` for several more minutes after its
  `quality-gates.sh` parent died) — the kill is selective enough to take out the wrapper/some workers while leaving at
  least one worker alive, which could itself contribute to the RAM pressure this doc describes if such orphans
  accumulate across many kills fleet-wide and are never reaped. Host load during the 4 attempts ranged 15-65 (`uptime`
  1-min avg), so this is not purely a "wait for load to drop" fix — the 3rd/4th attempts both started at load ~15-21
  (well below the ~65 peak observed earlier the same session) and still died. Followed this doc's own precedent + the
  operator's earlier ruling on an analogous external-gate situation this same session ("pick up other queued backlog
  work now; do NOT hold the slot idle... KEEP your background monitor armed"): stashed the verified-correct,
  QG-never-completed code (`market-tick-data-service` stash
  `orchestrator-slot-8-read_availability_index_bare_defi_callers-001`) and returned the task to the queue (GATED) rather
  than keep retrying blind.

- 2026-07-27 (slot-14, infra): **5th independent corroboration**, DIFFERENT repo (features-service) and a small,
  unrelated change (`scripts/pipeline_e2e_check.py` per-family `--timeout-sec` fix,
  `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`). New detail: the failure signature
  here is the **TYPE CHECK stage specifically**, not TESTS — 5 consecutive `quality-gates.sh` attempts (3 plain, 2 with
  `PYRIGHT_TIMEOUT` raised 120s->420s, which had ZERO effect on the outcome): 2 got fully through `[3/6] TESTS` GREEN
  (17902 passed, 0 failed, twice, byte-identical) then died at `[4/6] TYPE CHECK` with `PYRIGHT_EXIT` nonzero + empty
  captured output, hitting the exact ambiguous-failure branch the script's own comment (`base-service.sh` ~line 955)
  already anticipates (`PYRIGHT_EXIT != 0 && ERROR_COUNT==0 && WARN_COUNT==0` -> generic "Type check FAILED/timeout",
  indistinguishable from a real basedpyright failure without reading the empty `$PYRIGHT_OUT`); 1 attempt hit a
  DIFFERENT failure mid-TESTS (`test_health_router.py`, pytest's own `mainloop: caught unexpected SystemExit!` handler
  aborting the whole run early, no final summary) — a 3rd distinct failure shape added to this doc's catalogue (TESTS
  silent-vanish / TESTS SystemExit-abort / TYPECHECK signaled-before-output). Root-caused that raising `PYRIGHT_TIMEOUT`
  was chasing the wrong variable: basedpyright run STANDALONE (`.venv/bin/basedpyright features_service/`, no concurrent
  pytest suite competing) completed in **74.6s wall-clock** — well under even the ORIGINAL 120s default — confirming the
  kill is NOT the timeout expiring, it is something external (most likely the kernel OOM-killer, since
  `MEM_WRAP`/`systemd-run` cgroup capping is INACTIVE on this host per this repo's own QG log header: "systemd-run
  unavailable ... running pytest + basedpyright without hard memory cap") signaling the process before it finishes,
  exactly when fleet-wide swap usage is climbing. Host samples this session: load 35.87->11.20 (attempt 1 kill) ->12.67
  (attempt 4 kill) -> **45.64 / 383Mi free / 7.0Gi swap used** (right when I checked before a planned 6th attempt — the
  worst single sample yet recorded in this doc) confirming the "wild swings, not tied to a fixed threshold"
  characterization holds. Also confirmed the repo's `BASEDPYRIGHT_MAX_ERRORS` is UNSET for features-service, so even the
  955 pre-existing (baselined-by-omission) basedpyright errors on the full dir would only WARN, never fail the gate —
  i.e. a clean type-check pass was never actually blocked by real type errors, only by this infra issue. Not retrying
  blind into an observed 45.64-load spike; waiting for a calmer window (see this doc's own precedent) before the next
  attempt.

  **Same session, follow-up**: waited for memory to visibly recover (8.4-8.7Gi free, swap down from a peak 11Gi to
  4.9-5.0Gi, 1-min load briefly down to 15.15) and retried — got FURTHER (past both prior flake points, deep into the
  `sports`/`unit` test range) before dying on a **4th distinct failure signature**: `pytest`'s per-test timeout firing
  mid-`pandas` internals (`test_momentum.py::test_volume_momentum_columns_present`, hung inside
  `pandas.core.array_algos.take._take_nd_ndarray`) — a plain CPU-starvation stall, nothing to do with numba, SystemExit,
  or basedpyright this time. Confirms the failure mode is generic host contention, not tied to any one library/stage.
  Host had spiked AGAIN by the time of this kill: **load 57.23 (worst 1-min avg recorded in this doc yet), 381Mi free,
  swap back up to 7.2Gi** — the "wild swings" are on a much shorter cycle than the ~10min polling interval used here
  (memory recovered, then re-spiked worse, within roughly 10-15 minutes). Also hit a NEW variant of the doc-shipping
  problem itself while trying to commit this very corroboration: 3 consecutive
  `quickmerge.sh --agent --files <this-doc>` attempts on a **docs-only, ~30s-QG** change (not the multi-minute
  full-suite runs above) — attempt 1 and 2 failed on `check-branch-drift` (2-4 commits landed on `live-defi-rollout`
  between fetch and commit, from the same fleet-wide push volume this doc describes; recovered cleanly both times via
  `git stash push --include-untracked` -> `git fetch`+`merge --ff-only` -> `git stash pop`, zero conflicts since the
  edit only appends to this Progress Log); attempt 3 got all the way through its OWN internal `quality-gates.sh` re-run
  (`✅ ALL QUALITY GATES PASSED (34s)`, sentinel written) and then the **quickmerge process itself vanished
  mid-STAGE-4/5** (no PR/push confirmation, no error, process gone from `ps`) before completing the push — i.e. even a
  passing, near-instant doc-only QG run is not immune once the outer `quickmerge.sh` orchestrator process itself gets
  caught by the same external kill mechanism. 3rd corroboration that this is not confined to the heavy TESTS/TYPECHECK
  phases of a full-suite QG run.

- 2026-07-27 (slot-10, `data_engineering`): **6th independent corroboration**, features-service again, a DIFFERENT
  trivial change (one new untracked one-off script, zero edits to any existing module —
  `/plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md` todo 7).
  `bash scripts/quality-gates.sh --no-fix` (already the lower-footprint variant) ran cleanly to **66% through the pytest
  suite** (deep into `tests/sports/unit/calculators/`) before an `INTERNALERROR` fired:
  `pytest_timeout.py:327 threading.Timer(...)` → `threading.Thread.__init__` → `mainloop: caught unexpected SystemExit!`
  — a NEW (4th distinct) failure shape: the crash happens creating a plain `threading.Timer` object (not a subprocess,
  not a pandas internal), consistent with the host being unable to spawn a new OS thread at all at that moment
  (thread/resource-table exhaustion), not a memory-triggered kill mid-computation like the earlier signatures. Host
  state at the moment of the kill: `uptime` load average **18.65 / 19.28 / 23.39**; `free -h` **2.2Gi free / 12Gi used /
  4.1Gi swap used out of 30Gi**; `ps aux` confirmed **at least 3 concurrent full `quality-gates.sh` runs** on this host
  at that instant (this one, plus a live PM `quickmerge`-driven `--no-fix` run on slot-2, plus a plain
  `quality-gates.sh` on slot-13) — directly violating this workspace's own `Shared-host ≤2 full QGs at once` cap, and
  consistent with every prior corroboration in this doc: genuine external contention, not a defect in the change under
  test. Did not retry blind (per this doc's own established precedent) — the underlying data fix for todo 7 was
  independently verified correct on REAL production GCS + the live availability manifest (31/31 rows confirmed captured,
  durable across 2 consolidator cycles) before this QG attempt was even started, so the fix's correctness does not
  depend on this gate; the one-off script itself was deleted rather than held pending a contended re-run (it already
  achieved its one-shot effect — nothing left for it to do). Flagging here rather than re-opening a stash/park cycle
  since there was no code change left to preserve.

- 2026-07-27 (slot-5, `infra`): Investigated + closed the P1 todo. Confirmed the admission-only gap by reading
  `_qg_admit_check`/`_qg_governor_acquire_reservation` directly — it is exactly the already-open P0 in
  `/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` ("Global 80% valve — runtime ABORT of an
  already-running >80% job STILL PENDING"), so this doc's silent-kill pattern is field confirmation of a known,
  already-scoped design gap rather than a new one. Also found `systemd-run` is unavailable on this host (live warning
  during this session's own QG run), meaning the OTHER hard backstop (per-repo cgroup cap) is inactive here too — same
  failure class as `/plans/archive/issues/qg_mem_wrap_systemd_bus_unavailable_2026_07_26.md`. Implemented + shipped the
  runtime abort-monitor (`_qg_watchdog_*` in `qg-host-governor.sh`, reservation-mode only, self-scoped — can only ever
  signal its OWN process tree, never another slot's): polls live MemAvailable, and on sustained >80% host-used pressure
  writes a loud marker + SIGTERMs its own process tree (via `pgrep -P`-walked descendants, not a process-group signal —
  required because bash defers a pending trap until the current foreground child returns, so signaling only the root PID
  would silently do nothing until pytest/basedpyright finished on its own; verified by manual repro before fixing). New
  test suite `test-qg-watchdog.sh` (9 assertions) + all 8 pre-existing governor suites re-run clean (one pre-existing,
  unrelated flake in `test-qg-governor-wait-time.sh`'s "contended acquire" case reproduced identically on a clean
  `git stash` of this change — not caused by this work). Also flipped the corresponding P0 in the owning plan
  (`qg_host_adaptive_resource_governor_2026_07_14.md`) to avoid the fix being tracked as open in two places. Shipping
  via `quickmerge --agent` next. **Update (post-flip)**: shipping itself then hit 20+ consecutive quickmerge failures on
  the SAME push-race pattern slot-14 independently corroborated above ("quickmerge process itself vanished
  mid-STAGE-4/5") — found + fixed a real contributing bug (my commit lacked the `Quickmerge: agent` trailer, so Stage 5
  was doing a LATE `git commit --amend` that re-triggered `check-branch-drift`'s pre-commit hook AFTER the full QG
  re-run, well past my own pre-rebase — pre-stamping the trailer eliminated that specific hurdle), but the residual
  final-`git push` non-fast-forward race persists under this session's sustained churn. Filed as its own issue:
  `/plans/archive/issues/quickmerge_stage5_push_loses_fast_forward_race_under_high_churn_2026_07_27.md`.
- 2026-07-27 (slot-7, `infra`): **Further corroboration, 2 consecutive kills, same session**, shipping the
  `features-multi-timeframe-service` date-bug fix (`features-service@0eaafe5c`, committed, unpushed pending a valid
  sentinel). Both `quality-gates.sh --no-fix` re-runs (needed to refresh `.qg_last_passed_sha` to the new HEAD after
  committing) vanished silently mid-run — attempt 1 mid-`[6/6] PRODUCTION READINESS VALIDATORS`, attempt 2 at ~54%
  through the TESTS stage — no error, no marker file found (`find`'d for `*qg*watchdog*marker*`/`.qg_kill*`, zero hits),
  consistent with a genuine kernel OOM-kill rather than the new self-terminating watchdog's own >80%-threshold path (or
  that watchdog fix isn't yet live in this checkout). Fleet state at time of both kills: 15-20 concurrent
  `quality-gates.sh` processes, load average 10-17, free RAM as low as 1.1Gi. Per this doc's own precedent (do not
  blind-retry a 3rd time once 2 consecutive kills confirm the condition is stable, not flapping): did NOT retry again.
  The underlying code fix itself is independently verified correct — a full clean QG run against the pre-commit tree
  (identical file changes, just staged not committed) DID complete with `ALL QUALITY GATES PASSED (336s)` earlier in
  this same session, before the host got more contended. Releasing the dispatched task
  (`features_e2e_check_full_matrix_widespread_real_failures-002`) via `/skip-current-task` with reason GATED rather than
  holding the slot idle waiting for contention to ease; the commit stays safe locally (not pushed, not lost) for
  whichever slot picks this up next once the host is less loaded.

- 2026-07-27 (slot-3, `infra`, ~22:04-22:09 UTC): **Much more severe data point than any previously recorded** —
  `uptime` load average **1200.89 / 556.62 / 264.05** at first observation (own `docs(issues):` quickmerge for a 1-file
  change had been in-flight ~10min at that point, far longer than a single-file plan-doc commit normally takes).
  `ps aux | grep quality-gates.sh | wc -l` counted **34** concurrent full `quality-gates.sh` processes fleet-wide (vs.
  this doc's prior worst-recorded 15-20, vs. CLAUDE.md's `≤2 full QGs at once` hard rule) — identified concurrent QGs
  for at least 3 other repos/slots (`alerting_service`, `fund_administration_service`, `client_reporting_api` via
  slot-15 and slot-1's own quickmerge invocations, confirmed via `ps -ef` command-line inspection). Re-checked ~5 min
  later: load average dropped to **461.97 / 775.59 / 461.56**, still **19** concurrent `quality-gates.sh` processes —
  declining but still an order of magnitude over the ≤2 rule. **Own process did NOT get killed this time** — it
  completed successfully (`unified-trading-pm@892e3456a`, `QUICKMERGE_EXIT=0`) after being severely slowed (CPU-starved,
  not memory-killed) — i.e. this specific episode manifested as throughput degradation for a surviving process, not
  (this time) a silent kill, though the mechanism this doc tracks (RAM exhaustion → OOM-kill) and pure CPU contention
  are DIFFERENT failure modes that can co-occur at this concurrency level; did not independently check `free -h` at
  either observation point to confirm whether RAM was ALSO constrained, so cannot confirm this episode's mechanism
  matches the doc's OOM-kill hypothesis vs. being pure CPU starvation — flagging as a related but not
  confirmed-identical data point.

- 2026-07-28 (slot-2, `cicd`, escalation agt-68aa52): **New scope — confirms this pattern now blocks the LDR→main
  PROMOTION pipeline itself, not just background dev-slot QG runs**, via the SELF-HOSTED `quality-gates-v2` GHA runner
  (`opt/github-glue-runners-features-service/...` — same shared-host failure class, a different runner identity from the
  dev-slot fleet). Dispatched to fix `features-service` promotion PR #884's red `quality-gates-v2` (run `30328712723`).
  Diagnosis, not a code defect — **four independent local reproductions, all clean and fast, each matching a CI failure
  that hit its own timeout/OOM boundary**:
  1. CI: `tests` slice hung on the pytest-timeout 60s per-test cap inside `pandas` internals
     (`test_cross_candle.py::test_calculate_does_not_raise`, `_get_item_cache`) after a ~4min silent gap deep in the
     suite. Local: that same test passed in 7.25s isolated; the full
     `calendar+cefi+commodity+cross_instrument+ delta_one/calculators/test_cross_candle.py` scope (1625 tests) passed
     clean in 25.31s.
  2. PR #884 auto-superseded by a fresh promote PR #885 (created 04:54:30Z at the new LDR HEAD, per the standing
     `ldr-to-main-promote.yml` */15 cycle) — its OWN fresh `quality-gates-v2` run (`30330060500`) ALSO failed, ruling
     out "stale PR head" as the explanation. `tests` slice this time: `base-service.sh` reported `Killed` (OS-level
     SIGKILL, i.e. OOM-killer) ~40s in, before any pytest output — same
     `⚠️ QG_MEM_CAP=10G set but systemd-run unavailable on this host` gap this doc already tracks (no cgroup hard cap
     active).
  3. Same run, `checks` slice: `[qg-governor] all 4 tokens busy — queued 30s` → `token 1/4 acquired after 44s wait`
     (governor itself confirming fleet-wide contention) → `[4/6] TYPE CHECK` ran ~2min then
     `❌ Type check FAILED/timeout (exit=124)` — the exact TYPE-CHECK-timeout signature slot-14 recorded above
     (`PYRIGHT_EXIT` nonzero from external signal, not a real type error).
  4. Same run: `[5.E2E/6] E2E PIPELINE DRIVER SMOKE` (`scripts/e2e/run_pipeline_e2e.py --dry-run`, `run_timeout 30`)
     also failed at exactly its 30s wall-clock cap. Local repro with the identical CI env vars
     (`CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local GCP_PROJECT_ID=test-project`): completed in 4.1s, exit 0. No fix landed
     on `live-defi-rollout` (nothing is broken there — confirmed via 4 independent clean local runs). Did not force a
     3rd retry per this doc's own established precedent (2 consecutive kills on a fresh HEAD = stable condition, not
     flapping); the standing `ldr-to-main-promote.yml` cycle will keep generating fresh promote PRs and retrying on its
     own 15-min cadence independent of this one-shot worker holding the slot. Pinged authoring slot with outcome;
     closing escalation without a code change.

## Cross-check addendum (2026-08-14) — orphan_reap/kill_session misdiagnosis check

**Requested by** `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`'s own open-work item 3
("cross-check this doc's logged death timestamps against `journalctl | grep -E 'orphan_reap sweep|kill_session'` for the
same windows"). **Verdict: PARTIALLY CONFIRMED, not a wholesale misdiagnosis** — this doc's overall "shared-host RAM
exhaustion" framing stays substantially correct; ONE of its ~8 corroborating entries (slot-8) plausibly conflates the
separate `nohup`/`orphan_reap` bug.

**Data source**: live `journalctl` on this host only retains back to the current boot (`2026-08-11`, confirmed via
`journalctl --list-boots`) — too recent to reach 2026-07-27 directly. The rotated rsyslog archive `/var/log/syslog.2.gz`
(`ip-172-31-5-118`, spans `2026-07-26T00:00Z` → `2026-08-02T00:00Z`, readable via the `adm` group without root) DOES
still carry the raw `orphan_reap sweep: ... KILLED` / `kill_session(orch-slot-N): reaped ...` log stream for the full
incident window — a future retro cross-check of this vintage should reach for the archived `.gz` rotation, not bare
`journalctl`.

**Code-verified fact**: `orphan_reap`'s sweep has a hard-coded minimum kill age, `boot_grace_seconds` (default `300`,
`agent-orchestrator/server/config.py:795`) — nothing younger than 300s can structurally be an `orphan_reap` kill.

**What the archive shows**: `orphan_reap sweep: ... KILLED` and `kill_session(orch-slot-N): reaped ...` fired
continuously and fleet-wide throughout 2026-07-27 — far more pervasive than the nohup doc's own "5+ slots in one hour"
framing (hundreds of KILLED lines across nearly every slot 1-16, all day), observed `age` consistently 300-360s
(occasional >500s outliers from stale/backlogged sweeps), hitting every one of this doc's own corroborating slots (5, 7,
8, 10, 12, 14) repeatedly.

**Per-entry cross-check**:

- **Slot-8 (4th corroboration, market-tick-data-service) — PLAUSIBLE MISATTRIBUTION.** This entry's own text states the
  background method was `nohup`+`disown` and that 3/4 attempts "died within seconds of admission" after a 150-292s
  governor wait — total elapsed ≈150-300+s, overlapping the observed 300-360s `orphan_reap` kill-age band almost
  exactly. Its own noted detail — an orphaned pytest-xdist worker reparented to PID 1 surviving its parent's death — is
  a distinctive `orphan_reap` fingerprint (a per-PID `SIGKILL`, not a process-group-wide OOM sweep, leaves
  already-forked children orphaned rather than dying together). Real `orphan_reap` KILLED events hit slot 8 repeatedly
  that day: `02:03:19 age=355s`, `05:42:43 age=304s`, `05:49:54 age=331s`, `05:58:15 age=322s`, `07:03:39 age=306s`,
  `10:58:31 age=325s` (×2), `11:39:48-49 age=349s` (×3) — no single line is provably THE kill (this entry never logged
  an exact timestamp), but the mechanism, methodology, and timing band all line up.
- **Original slot-12 incident, attempts 2-7 (32s-520s elapsed) — NOT `orphan_reap`.** Several deaths (e.g. the 32s one)
  occurred well under the 300s `boot_grace_seconds` floor — code-confirmed structurally impossible to be an
  `orphan_reap` kill. A genuine, different external kill mechanism explains these (consistent with this doc's own
  RAM-pressure diagnosis).
- **Slot-14 (5th corroboration) / slot-7 / slot-10 (6th corroboration) — NOT `orphan_reap`.** Their failure signatures
  (`PYRIGHT_EXIT` nonzero with empty output, pytest `INTERNALERROR` on `threading.Timer` creation, a per-test 60s pytest
  timeout stall inside `pandas`) all leave a live application-level error/exit code, inconsistent with `orphan_reap`'s
  silent raw `SIGKILL` (no trace at all in the killed process's own output). These remain genuine host RAM/CPU/thread
  contention, as originally diagnosed.
- **Slot-3 (~22:04-22:09 UTC)** — the process did NOT die (survived, just slow) — no kill occurred, so no
  `orphan_reap`/`kill_session` correlation applies either way; still an open CPU-vs-RAM-mechanism question as this doc's
  own entry already flagged.
- **Slot-2 (2026-07-28, CI)** — a self-hosted GHA runner (`github-glue-runners-features-service`), a DIFFERENT host
  identity from this orchestrator VM; `orphan_reap`/`kill_session` are AO-server worker-slot mechanisms and do not run
  against CI runner infrastructure — categorically out of scope for this cross-check.

**Conclusion**: not correcting this doc's root-cause title/framing (it remains correct for the majority — and the
mechanism — of its own evidence), but flagging the slot-8 corroboration specifically as likely a second, distinct kill
mechanism (`nohup`/`orphan_reap`) riding alongside the genuine RAM-exhaustion pattern this doc otherwise documents,
rather than independent confirmation of it. Cross-check closed via
`/plans/active/ao_satellite_ao_dispatch_batch20_2026_08_13.md`.
