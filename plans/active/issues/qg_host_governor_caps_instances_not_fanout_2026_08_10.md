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
parent_epic: infrastructure_master
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
last_updated: 2026-08-10
locked_by:
locked_since:
resolved_by:
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
