---
doc_type: issue
title:
  PM BATS tmux-fixture tests spin at ~90% CPU and leak sessions, wedging the shared 4-slot host (load 283) and making
  every repo's quality gate untrustworthy
summary: >-
  The `test_slot_git_status_claim*` BATS suite in unified-trading-pm spawns real `tmux new-session` / `kill-session` /
  `has-session` commands as test fixtures. Under a loaded shared host these commands never return: measured 2026-08-10
  with 19 stuck tmux clients, EIGHT of them spinning at 75-94% CPU each (~7 of the box's 10 cores) and one leaked
  fixture session 29 HOURS old. Because three slots run the same suite concurrently (`-j 5` each), the spin is
  self-reinforcing: killing the clients only frees CPU until the next fixture spawns. Host load reached 283 on a 10-core
  / 24 GiB box and MemAvailable fell to 6 GiB, which in turn produced FALSE RED quality gates in unrelated repos
  (pytest-timeout kills) and starved the QG governor's RAM budget so new gates could not be admitted at all.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, bats, tmux, shared-host, flaky, contention, P1]
related:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Interactive session 2026-08-10 slot 1, found while waiting on a stalled unified-trading-pm quality gate during the
  data-pipeline alert-storm batch. Diagnosed from `ps`/`uptime`/`lsof` on the live host, not inferred.
---

# PM BATS tmux fixtures wedge the shared host

## What was measured (2026-08-10, ~21:20 local, slot 1)

| Signal                                | Value                                                     |
| ------------------------------------- | --------------------------------------------------------- |
| Host load average (10 physical cores) | **283** (1-min), 278 (5-min)                              |
| `MemAvailable`                        | **6 GiB** of 24 GiB (QG RAM budget is 17.2 GiB)           |
| Stuck `tmux` client processes         | **19**                                                    |
| …of which spinning                    | **8**, at 75–94% CPU each (~7 cores)                      |
| Oldest leaked fixture                 | `bats-claim-hb-test-60732-…`, **29 hours** elapsed        |
| Leaked tmux SESSIONS still registered | 7 (`tmux ls`, which itself took >120 s to answer)         |
| Slots running the suite concurrently  | **3** (`.tabs/1`, `.tabs/2`, `.tabs/3`), each `bats -j 5` |

The stuck commands are all fixture plumbing, not product code: `tmux new-session -d -s bats-claim-hb-test-<pid>-<n>`,
`tmux kill-session -t =bats-claim-hb-test-…`, `tmux has-session -t =no-such-session-…`.

## Why this is worse than a slow test

1. **It manufactures false RED gates in OTHER repos.** With the box this loaded, `pytest-timeout` (wall-clock) fires on
   tests that are merely slow, not broken: `unified-api-contracts` failed 5 tests whose terminal cause was
   `Failed: Timeout (>150.0s) from pytest-timeout`, and `agent-orchestrator` failed 9 that PASS on a clean tree
   (verified by stashing the change and re-running). An agent that trusts a red gate will "fix" code that was never
   broken.
2. **It starves the QG governor.** With MemAvailable at 6 GiB against a 17.2 GiB budget, new gates sit in
   `WAIT_RAM_LIVE` indefinitely — the governor is behaving correctly, but no work can be admitted.
3. **`SIGTERM` does not clear it and `SIGKILL` is only briefly effective.** The spinners survived SIGTERM; SIGKILL
   reaped them, and fresh ones appeared within seconds because the suites kept running. Whack-a-mole on the clients
   cannot fix it — only stopping the suite does.
4. **It leaks across sessions.** A 29-hour-old fixture proves this is not purely a today-under-load artifact: fixtures
   leak in normal operation and simply accumulate until something notices.

## Root cause (hypothesis, needs confirming in the suite)

The fixtures shell out to a REAL tmux server. `tmux new-session` with no server running forks one; under heavy load the
client can spin waiting on the server socket rather than blocking, and the suite's `-j 5` parallelism multiplies that by
three slots. Nothing in the fixture path bounds the call with a timeout, and nothing guarantees teardown when the test
is killed — hence both the spin and the leak.

## Suggested fix (owner's call — do NOT just delete the tests)

- [ ] [SCRIPT] P1. Bound every fixture tmux call with a `timeout` (a fixture that cannot get a tmux server in a few
      seconds should FAIL the test loudly, never spin), and give the suite a `teardown_file` that kills its own
      `bats-claim-hb-test-*` sessions unconditionally, including on abort.
- [ ] [SCRIPT] P1. Use a DEDICATED tmux socket per suite run (`tmux -L bats-<runid>`) instead of the user's default
      server, so a wedged/slow fixture server can never contend with the operator's real sessions and the whole socket
      can be torn down in one call.
- [ ] [SCRIPT] P2. Make the claim/heartbeat behaviour under test injectable so the common cases can be covered WITHOUT a
      real tmux server at all, leaving only a small number of genuine integration cases behind a marker.
- [ ] [OPERATOR] P2. Sweep the host for pre-existing leaked `bats-claim-hb-test-*` sessions (7 registered at the time of
      writing, oldest 29 h) — they hold a tmux server alive for no reason.
- [ ] [SCRIPT] P2. Consider whether the QG host governor should account for load average / MemAvailable, not just its
      own reservations: at the time of measurement it reported `reserved: 0MB` and `running heavy phases: 0` while the
      box was at load 283, because the load came from processes it had never admitted.

## Non-goals

Deleting or skipping the tmux tests. They cover the slot-claim heartbeat, which is real multi-agent-safety behaviour;
the defect is the fixture plumbing (unbounded, un-torn-down, shared-socket), not the coverage.
