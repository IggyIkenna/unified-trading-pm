---
doc_type: issue
title:
  QG host governor caps INSTANCES but each instance fans out, so 5 slot-holders produce 155 runnable threads on 10 cores
summary: >-
  The total-instance cap (floor(cores x 3/4) = 7 on a 10-core Mac) treats one quality-gates.sh run as roughly one core
  of work. It is not — each run spawns bats -j 5, pytest workers, vitest/node AND its own LOCAL_DEPS child gates.
  Measured 2026-08-10: 5 held slots (2 FREE), 155 runnable threads, 0.0% idle, 53% sys, and an 80s-baseline gate taking
  2510s wall. No stale processes and no leaked slots — the cap simply does not model per-instance parallelism.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, concurrency, host-governor, capacity]
related:
  [
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-08-10
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: none
source: Measured while diagnosing repeated MAX_DURATION failures on a substantively-green PM tree, 2026-08-10.
depends_on: []
last_updated: 2026-08-20
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    scripts/quality-gates-base/qg-host-governor.sh,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
---

# The instance cap does not model per-instance fan-out

## Measured, 2026-08-10 ~20:50 (operator laptop, 10 physical cores)

| Signal                        | Value                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------- |
| Governor slots HELD / free    | **5 held, 2 FREE** (cap 7 = `floor(10 x 3/4)`)                                   |
| Runnable threads vs cores     | **155 vs 10**                                                                    |
| CPU                           | 47.6% user, **52.9% sys**, **0.0% idle**                                         |
| Fan-out from those 5 holders  | 2x `bats -j 5`, 6 pytest processes, 4 node/vitest                                |
| PM gate wall time vs baseline | **1195s then 2510s** vs an **80.2s** baseline                                    |
| Stale / orphaned QG processes | **none** (no `ppid=1`, oldest 24 min, all logs progressing)                      |
| Leaked governor slots         | **none possible** — slots are `flock` targets; the kernel releases them on death |

## Root cause

`_qg_total_default_cap()` returns `floor(cores x 3/4)`, i.e. it budgets **one core per QG instance**. But one instance
is not one core of work:

- `bats -j 5` — five parallel shell-test jobs
- pytest with `PYTEST_WORKERS = max(1, cores/4)` workers
- dashboard `vitest` / node
- **plus its own `LOCAL_DEPS` child gates**, which each fan out again

So 5 instances legitimately produce ~155 runnable threads. The machine then spends more than half its CPU in the kernel
(context-switch thrash, 52.9% sys), and every gate on the host — including gates that would otherwise take 80 seconds —
misses its own `MAX_DURATION`. The cap is not being violated; it is being honoured, and it is the wrong quantity to cap.

Note the two FREE slots: the governor was NOT the binding constraint at the moment of measurement. Raising or lowering
the instance number alone will not fix this.

## Why this matters beyond slowness

`MAX_DURATION` is meant to catch a gate that has become pathologically slow — a real regression signal. Under this
contention it measures the HOST, not the change, and it fails a substantively-green tree. An agent that does not
diagnose it will do one of two harmful things: retry forever, or "fix" it by raising the budget and permanently blinding
the regression signal.

## Candidate fixes (not applied — see below)

1. **Budget threads, not instances**: cap on `sum(per-instance fan-out)` against cores rather than a raw count.
2. **Force nested dependency gates to `-j 1` / `PYTEST_WORKERS=1`**: a child dep-gate inherits the parent's slot and
   should not re-fan-out.
3. **Make `MAX_DURATION` contention-aware**: it already subtracts governor queue-wait (measured 0s here); it could
   likewise discount time when runnable-threads/cores exceeds a threshold, so the gate keeps its regression-detecting
   power without failing on neighbours' load.

## Deliberately NOT hot-patched

Concurrency infra shared by every repo and host, with three live Claude sessions mid-gate on it at the time of
measurement. CLAUDE.md carries an explicit blast-radius rule for exactly this, added after re-enabling a gate broke
every repo at once. A wrong change here converts "slow" into "every session deadlocked", so this is written up for a
deliberate decision rather than changed mid-session.

- [ ] [INFRA] P2. **Cap on aggregate fan-out rather than instance count, and stop nested dependency gates from
      re-fanning-out.** Use the measurements above as the before-state. **Done when**: a repeat of the same
      5-concurrent-gate scenario keeps runnable-threads within ~2x cores, and PM's gate completes inside `MAX_DURATION`
      with 5 neighbours running.
- [ ] [INFRA] P3. **Stop `MAX_DURATION` failing a green tree purely on neighbour load** — it already subtracts governor
      queue-wait; extend that to CPU-starvation, or report duration as a WARN plus a separate hard ceiling. **Done
      when**: a gate that is green on every substantive check is not blocked by a host-load artifact, and a
      genuinely-slow gate still fails.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **2026-08-14 (slot 15, corroborating downstream symptom)**: while shipping an unrelated 1-line
  `market-tick-data-service` fix (`infra_satellite_ao_dispatch_batch16_2026_08_13.md`), hit 12 consecutive
  `bash scripts/quality-gates.sh` invocations (background-mode, this AWS host — not the laptop this doc's original
  measurement was taken on) all terminated externally (`status: killed`, no traceback in the captured log) before
  completing, under confirmed heavy fleet-wide QG concurrency (15-19 concurrent `quality-gates.sh` processes,
  `load average` 5-7 on a shared host). Ruled out via direct investigation: (a) NOT a governor logic bug — `bash -x`
  tracing confirmed the per-repo `flock`-based token wait (`_qg_try_repo_token`,
  `~/unified-trading-system-repos/.benchmarks/qg-governor-total/repo/<repo>/slot.N`) works correctly and was
  legitimately serializing against another slot's concurrent MTDS run; (b) NOT host-wide OOM — `free -h` consistently
  showed 20+Gi "available" throughout; (c) NOT a background-task silence-timeout — a heartbeat-wrapped attempt printing
  output every 20s still died within ~20s of launch. One attempt did survive ~19min (reaching the governor's own
  periodic "queued Ns" print) before also eventually dying. Net: still unresolved which exact mechanism kills the
  process (a cgroup CPU/mem-pressure eviction under the 0%-idle/high-sys-CPU thrashing this doc's root cause already
  documents is the leading hypothesis, given it fits the "instance cap doesn't model fan-out" mechanism above without
  needing a new root cause) — flagging as a probable DOWNSTREAM SYMPTOM of the same root cause rather than opening a
  separate issue, since the fix candidates above (cap on aggregate fan-out) would likely also resolve this. Not actioned
  (same "deliberately not hot-patched" blast-radius reasoning applies); MTDS fix left committed locally (`d6ca0a67`)
  pending a successful QG run, tracked as a follow-up in `infra_satellite_ao_dispatch_batch16_2026_08_13.md`.
- **2026-08-14 (operator root-cause lead, via BLK-cec1d239 answer)**: `orchestrator.service` on this host restarted at
  `2026-08-14T23:45:18Z` — roughly 1 minute before the blocked question above was filed — and `systemctl status` for
  that cgroup showed peak memory 23.0G / peak swap 20.0G. This matches the exact incident class RULES.md § "Bound memory
  BEFORE running any heavy script" already documents (3 prior same-shape outages where a heavy subprocess's memory
  footprint got a background QG/analysis run externally killed on this shared host) even though this session's own
  point-in-time `free -h` snapshots looked clear throughout — a transient spike during/around a service restart would
  not show up in a later snapshot taken after the spike subsided. This more directly explains the "silent external kill,
  no traceback" signature than the CPU-thrash hypothesis above (both may be contributing factors under the same root
  umbrella of "the instance cap doesn't model real resource cost"). Operator noted it's worth checking whether other
  slots hit the same kill pattern in the same window — not verified in this pass.
- **2026-08-15 06:26-06:32 (slot 2, third corroborating downstream symptom, same AWS host)**: while shipping the AAVE_V3
  rewards-capture task (`uac_data_type_validity_combinator_fragmentation_2026_07_07.md` item, repo
  `market-tick-data-service`), a `bash scripts/quality-gates.sh --no-fix` run (PID `3857681`) was correctly tracked via
  a `run_in_background` blocking `kill -0` watchdog loop. It queued behind the host-wide governor for the expected
  `[qg-governor] ... queued Ns` cadence through 300s, then the PID vanished with no further log output whatsoever — no
  phase markers past the queue lines, no exit code, no traceback — matching the exact "silent external kill" signature
  from the 2026-08-14 slot-15 entry above. At the moment of death: `uptime` showed load average 11.73/12.74/14.22,
  `ps aux | grep -c quality-gates.sh` = 20 concurrent instances host-wide, `free -h` showed 20Gi "available" (so a
  point-in-time snapshot looked clear, same false-negative pattern already noted above). Ruled out as a
  content/lint/test failure in the diff itself: an earlier, more complete run on the same 2-file diff
  (`/tmp/qg_run7.log`) had already reached `10799 passed, 28 skipped` through `[3/6] TESTS`. Treating this as further
  corroboration of the existing root cause, not a new issue; not actioned per the same deliberately-not-hot-patched
  blast-radius reasoning. Retrying.
- **2026-08-15 06:32-06:39 (slot 2, retry of the entry above, IDENTICAL failure)**: the retry (PID `14840`, same
  `--no-fix` invocation, same repo) reproduced the exact same signature — queued behind the host-wide governor through
  `queued 300s` (final governor line), then the PID vanished with zero further log output, no exit code, no traceback.
  Host state at time of death: load average 11.02/11.15/12.84, 19 concurrent `quality-gates.sh` processes host-wide. Per
  the workspace's "two identical consecutive failures = stop blind-retrying" rule, did NOT launch a third immediate
  attempt. Instead armed a single `run_in_background` watchdog (`/tmp/qg_retry10_watchdog.sh`) that polls `uptime` every
  60s (cap 15 checks / 15min) and only launches the next attempt once load drops below 6 (or the cap is hit), then
  tracks that attempt to completion the same way. This is a load-gated retry, not a blind one — the condition being
  waited on (host contention) is external and measurable, not a coin-flip re-run.
- **2026-08-15 06:54-07:16 (slot 2, load-gated retry result — partial success, then a fourth silent kill much deeper
  into the gate)**: the load-gated watchdog's cap-fallback fired at 06:54:40 (load never dropped below 6 in its 15-check
  window) and launched attempt 3 (PID `1069852`) anyway. This attempt broke clean through the governor queue (unlike the
  two prior identical `queued 300s` deaths) and ran real content for over 20 minutes, progressing through TESTS (pytest
  visibly at 82-91%, all passing bar 2 skips) and on into the `[5.x/6]` DATA-PIPELINE SELF-MONITORING / ratchet checks,
  reaching **5.95/6** (792 log lines, last write 07:16:18) — by far the deepest any attempt has reached. It then died
  the same way as the first two: PID vanished, log stopped mid-stream with **no exit code, no traceback, no phase-6
  banner**, right after a `5.95 PASS:` line. At death: `uptime` 5.26/7.42/9.15 (host load had already eased from the
  peak), `free -h` showed 20Gi "available" (same clean-snapshot-hides-the-spike pattern already noted above). Checked
  `dmesg`/`journalctl` for an OOM/cgroup-eviction signature around 07:16:18 — no kernel OOM lines found (dmesg
  unreadable without privilege; journalctl had only unrelated substring hits) — inconclusive, does not rule out the
  memory-pressure hypothesis from the 2026-08-14 operator entry above. **Reframing**: this is not a fixed "dies at 300s"
  signature — the kill point is not a fixed offset, and forward progress is real and increasing each retry
  (governor-queue-only → governor-queue-only → 91% through tests and past 5.95/6 checks). Treating this as continued
  corroboration of the same root cause (a per-instance resource cost the governor doesn't model), now with evidence the
  failure mode is a moving contention threshold rather than a deterministic timeout. Retrying a 4th time immediately
  (load already favorable, no load-gate wait needed this time).
- **2026-08-15 07:21-07:25 (slot 2, 4th attempt result — reverted to the pure-queue death pattern)**: attempt 4 (PID
  `2183466`) tracked via the same `kill -0` background watchdog, this time did NOT break through the governor queue at
  all — it died with the log showing only the `[qg-governor] ... queued Ns` cadence through **`queued 330s`** and
  nothing else (no phase content, no exit code, no traceback), i.e. the same signature as attempts 1-2, not attempt 3's
  "broke through to 5.95/6 then died" pattern. At death: `uptime` 2.26/4.12/6.89 (already trending down from the peak),
  and `ps` showed at least 3 other concurrently-running `quality-gates.sh` instances from other slots (one, PID
  `2363722`/`2363761`, had a `pytest` worker actively running at 60.6% CPU) — confirming real host-wide contention was
  still the binding constraint, not a fluke. This reinforces that forward progress is NOT monotonic across retries
  (attempt 3 reached 5.95/6, attempt 4 reached 0/6) — the moving-contention-threshold framing holds, but it moves in
  both directions depending on which neighbours are mid-fanout at any given moment, not a steadily improving trend.
  Retrying a 5th time immediately given the 1-min load average (2.26) is already low and trending down.
- **2026-08-15 08:57-09:11 (slot 8, further corroboration — worsening storm, ~10 attempts, one clean SIGTERM
  captured)**: picked up the same AAVE_V3 rewards-capture task from slot-2's checkpoint (fixed a genuine reserve-
  discovery bug in the code itself — separate from this issue). Hit the identical signature repeatedly while shipping:
  `market-tick-data-service --no-fix` attempts died silently (no exit code, no traceback) across ~10 consecutive
  launches over ~15 minutes, while host-wide `ps aux | grep -c quality-gates.sh` climbed from 10 → 13 → 16 → 19 → 21
  concurrent instances and `uptime` load stayed pinned at 10-15. One attempt DID capture the governor's own kill marker
  cleanly (`❌ [quality-gates] received SIGTERM — wrote kill marker .../.benchmarks/qg-governor/killed.<pid>`)
  confirming the SIGTERM is external, not a script crash. `free -h` fluctuated wildly between attempts (865Mi available
  at one low point, up to 20Gi a few checks later) — same clean-snapshot-hides-the-spike unreliability already noted
  above; not a stable OOM signal on its own. **New observation, not previously logged**: two of my own lightweight
  `run_in_background` watchdog scripts (trivial `sleep`-poll loops doing near-zero CPU/memory work, meant to gate the
  next QG launch on load easing) were themselves reported `killed` by the harness after ~90-180s despite doing nothing
  but sleeping — this doesn't fit the CPU-thrash/OOM hypothesis (a near-idle process is an unlikely eviction target) and
  may point at a THIRD contributing mechanism (pane/session-liveness pressure under the same host-wide load) rather than
  confirm the two already documented; flagging as an open question, not a new root-cause claim. **Self-correction worth
  recording**: one observed "failure" during this session was NOT a governor kill at all — a stale `cd` from an
  unrelated dirty-file check earlier in the session left the shell's cwd pointed at `features-service-clean-check`, so
  one QG invocation silently validated the wrong repo (surfaced its own pre-existing red `STEP 5.5 broad-except` gate,
  unrelated to this task) before erroring — worth noting as a distinct human/agent-error failure mode that can
  masquerade as this issue's signature if the log isn't checked for which repo actually ran. Not actioned (same
  deliberately-not-hot-patched blast-radius reasoning); backing off from immediate retries given every relaunch appears
  to add to an already-severe fleet-wide storm (21 concurrent instances at last check) rather than help it clear.

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:2660ad0b240e84dc]: KEEP-NA, valid — doc's own "Deliberately NOT hot-patched" section covers both open todos — changes touch concurrency infra shared by every repo/host, needing a deliberate decision per CLAUDE.md's blast-radius rule.
