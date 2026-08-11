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

- [x] ✅ [SCRIPT] P1. Bound every fixture tmux call with a `timeout` (a fixture that cannot get a tmux server in a few
      seconds should FAIL the test loudly, never spin), and kill the suite's own `bats-claim-hb-test-*` sessions
      unconditionally, including on abort — unified-trading-pm@3895be718f. `_tmux()` wraps every call
      (`timeout`/`gtimeout` portable fallback, unbounded only if neither exists). The unconditional half is done in
      `teardown()` rather than a `teardown_file`: bats runs `teardown` after EVERY test including a failed assertion,
      which is exactly the path that leaked. Root cause found in the process: `teardown` only ever killed
      `${TMUX_SESSION}`, while the `-longer-suffix` session was killed on the LAST LINE of its own test body — every one
      of the 41 sessions leaked on the AO VM was a `*-longer-suffix`. Evidence: 5/5 tests pass, 0 sessions left on the
      default socket, 0 leftover socket dirs.
- [x] ✅ [SCRIPT] P1. Use a DEDICATED tmux socket per suite run instead of the user's default server, so a wedged/slow
      fixture server can never contend with the operator's real sessions and the whole socket can be torn down in one
      call — unified-trading-pm@3895be718f. Implemented via an exported per-test `TMUX_TMPDIR` rather than `tmux -L`:
      the script under test is a subprocess of `_heartbeat` and inherits the env, so both sides resolve the same socket
      with NO test-only flag in production code. `teardown` also `kill-server`s the whole socket. **Non-obvious
      constraint worth keeping**: the socket dir must be SHORT and NOT nested under `BATS_TEST_TMPDIR` —
      `sockaddr_un.sun_path` caps a unix socket path at ~104 B and macOS `BATS_TEST_TMPDIR` is already ~90, so the
      obvious nesting fails every session with `error connecting to ... (File name too long)`.
- [ ] [SCRIPT] P2. Make the claim/heartbeat behaviour under test injectable so the common cases can be covered WITHOUT a
      real tmux server at all, leaving only a small number of genuine integration cases behind a marker.
- [x] ✅ [OPERATOR] P2. Sweep the host for pre-existing leaked `bats-claim-hb-test-*` sessions — done 2026-08-10 on the
      ORCHESTRATOR VM (the laptop is a separate sweep; see the AO-VM section above). **41 reaped, not 7** — the count
      had grown 25 → 41 during the diagnosing session itself (~1 new leak / 4 min). Swept surgically: only names
      matching `bats-claim-hb-test-*`, with the `orch-slot-*` count asserted before AND after (21 → 21, none touched).
      Note the sweep alone did NOT restore the box — `/tmp` stayed 100% full afterwards, because the dominant consumer
      was a separate one (a banned subprocess GCS listing streaming multi-GiB parquet through the tmpfs). Recurrence is
      now handled by `tmpfs-disk-cleanup.timer` (30-min sweep, installed + verified running on the AO VM), so this todo
      should not need a human again.
- [ ] [SCRIPT] P2. Consider whether the QG host governor should account for load average / MemAvailable, not just its
      own reservations: at the time of measurement it reported `reserved: 0MB` and `running heavy phases: 0` while the
      box was at load 283, because the load came from processes it had never admitted.

## Second site, worse blast radius — the ORCHESTRATOR VM (2026-08-10, slot 3)

This doc's measurements are from the operator's 10-core laptop, where the symptom was false-red quality gates. The same
leak is also on the **orchestrator VM**, where it does something considerably worse.

Measured there 2026-08-10 (read-only via SSM, then remediated):

- **41 leaked `bats-claim-hb-test-*` sessions** — not 7. Oldest from Aug 9; the count grew 25 → 41 _during_ the session
  that was diagnosing it, i.e. ~1 new leak every 4 minutes.
- **Every single one ended in `-longer-suffix`.** That is the tell, and it identifies the defect exactly: the
  `exact-match target` test creates `${TMUX_SESSION}-longer-suffix` and kills it on the **last line of its own test
  body**, while `teardown()` only ever killed `${TMUX_SESSION}`. Any assertion failure above that line — which is
  precisely what a loaded host causes — skips the kill and leaks the session permanently.
- `/tmp` on that box is an **8 GiB tmpfs** and it reached **100% (15 MiB free)**. The leaked sessions were a contributor
  alongside a much larger one (an agent's ad-hoc `gsutil ls -r` streaming multi-GiB parquet through `/tmp` — banned, now
  blocked at the PreToolUse hook).
- Consequence: `tmux_spawn.spawn` fails with `[Errno 28] No space left on device`, so **every escalation dispatch died
  and re-queued**. Four dispatches failed that way at 16:41-16:44; the `unified-trading-pm` SIT walls reached 190+
  attempts on the resulting re-escalation treadmill. This is a fleet-wide CI-recovery outage, not a slow test.

Fixed at source in this session (see the Progress Log): `teardown()` now owns BOTH session names — the property that
matters is that bats runs teardown unconditionally, including after a failed assertion; every fixture tmux call is
`timeout`-bounded (portable `timeout`/`gtimeout` fallback); and each test gets its own `TMUX_TMPDIR` socket so a leak
can never again land on the default socket beside the real `orch-slot-*` sessions. One non-obvious constraint worth
recording: the isolated socket dir must be SHORT and must **not** be nested under `BATS_TEST_TMPDIR` — a unix socket
path is capped at ~104 bytes by `sockaddr_un.sun_path`, and on macOS `BATS_TEST_TMPDIR` is already ~90, so the obvious
nesting fails every session with `error connecting to ... (File name too long)`.

## Non-goals

Deleting or skipping the tmux tests. They cover the slot-claim heartbeat, which is real multi-agent-safety behaviour;
the defect is the fixture plumbing (unbounded, un-torn-down, shared-socket), not the coverage.
