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
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-api-contracts]
scope: [engineer, admin]
tags: [infra, ram, memory, shared-host, fleet-wide, quality-gates, qg-governor, blocking]
related:
  [
    /plans/active/issues/shared_host_tmp_tmpfs_full_2026_07_26.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: infrastructure_master
source: "slot-12, data_engineering, discovered while shipping prediction_satellite_ao_dispatch_batch1-003, 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

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

- [ ] [INFRA] P1. **Investigate whether the qg-governor's 5500MB RAM reservation is being violated by the OS/cgroup
      AFTER admission** — i.e., does the governor only gate entry, with no ongoing enforcement that admitted processes
      stay within their reservation as OTHER processes' demand grows post-admission? If so, either (a) tighten the
      governor to re-check/pause admitted-but-not-yet-CPU-heavy processes when fleet RAM drops below a floor, or (b)
      raise total host RAM / reduce max concurrent slots so admitted work can actually complete. Repo:
      unified-trading-pm (or wherever qg-governor lives — locate via `rg -l qg-governor`). **Done when**: a repro
      (concurrent QG runs at the same contention level this doc measured) completes without a silent kill, OR a
      documented capacity ceiling is set (e.g. "max N concurrent full QG runs fleet-wide") that the governor enforces
      globally, not per-invocation.
- [ ] [DOC] P2. **Add a one-line rule to `unified-trading-pm/agents/worker.md`'s Pass-1/Pass-2 QG section**: run
      `quality-gates.sh` AFTER committing (not before), so the written sentinel's recorded SHA matches HEAD on the first
      pass — avoids the extra QG-before-commit → commit → sentinel-SHA-mismatch → re-run cycle this session hit. (repo:
      unified-trading-pm, doc edit). **Done when**: the line is added and cross-referenced from RULES.md § 2 if that
      section also describes the ordering.
- [ ] [INFRA] P2. **Make a killed (not just failed) background QG run loud**: have `quality-gates.sh` (or its governor
      wrapper) write a partial-state marker file on SIGTERM/SIGKILL (via a trap, where signal-catchable) so a worker
      polling for completion can distinguish "silently killed" from "still legitimately running" without needing to
      infer it from `ps` disappearing. Repo: unified-trading-pm (wherever the governor/QG entrypoint lives). **Done
      when**: a deliberately-killed QG run leaves a marker distinguishable from a clean in-progress state.

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
