---
doc_type: issue
title:
  "pytest-timeout-under-contention bug class continues (3rd split — continued2 hit its 1000-line hard cap) —
  instruments-service#1069 (cicd agt-f90886), no code gap, promotion already merged before the escalating run finished"
summary: >-
  Continuation of `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` (966/1000
  lines with `agt-63a88d`'s entry already merged upstream when this split landed — a `git pull --rebase --autostash`
  conflict during this session's own push confirmed a SECOND concurrent write had landed there in the same window;
  appending this session's entry on top would have pushed it to ~1003 lines, over the hard cap, so this session resolved
  the conflict by keeping `continued2` exactly as `agt-63a88d` left it and split here instead, per the parent chain's
  own established practice). `cicd` escalation `agt-f90886` (`WALL_TYPE=ldr_qg_failure`, `REPO=instruments-service`,
  `pr_number=1069`, slot 8) hit the SAME xdist-channel/timeout-corruption signature this doc-chain has repeatedly
  documented — `pytest-timeout` fired `Failed: Timeout (>150.0s)` inside
  `tests/unit/test_sports_comprehensive.py::TestApiFootballAdapterEdgeCases::test_fetch_league_fixtures_error_returns_empty`,
  which pytest-xdist's worker-crash detector then reported as an `INTERNALERROR> AssertionError` on `<WorkerController
  gw0>`. A full local reproduction (isolated single-test run + the entire 110-test file under the exact CI `PARGS`)
  found zero failures and no plausible code-level mechanism for a genuine 150s+ hang, and the promotion PR had already
  merged 2 seconds before the escalating run even started — confirming, once again, this is pure runner-queue-depth host
  contention, not a code or test defect.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist, escalation-refire-waste]
related:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03T22:45Z
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "cicd-role escalation agt-f90886 (WALL_TYPE=ldr_qg_failure, REPO=instruments-service, slot 8) — split of continued2 at
  its line cap"
context_scope:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
    instruments-service/scripts/quality-gates.sh,
  ]
---

# pytest-timeout-under-contention: 3rd split (continued2 at hard cap) — instruments-service#1069

Parent doc `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` reached 966/1000
lines with `agt-63a88d`'s entry (the most recent addition) already committed upstream; appending this session's own
entry there would have exceeded the 1000-line hard cap, so this session split here instead. Read the parent (and its own
ancestors, `continued_2026_08_02.md` and the founding `2026_07_29.md`) for the full bug-class history; not repeated
here.

## Todos

- [ ] 1. [INFRA] P3. Root-cause fix is capacity-side, not another per-repo timeout raise — track landing of
      `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phase 2-3 (carried forward
      unchanged from the parent doc-chain; still open per `continued2`'s own last check — a brief runner-idle window was
      observed once but did not hold). Once landed AND sustained (not a momentary idle blip), re-test whether
      `main_ci_red`/`ldr_qg_failure` re-fires across this whole doc-chain stop recurring.
- [ ] 2. [OPERATOR] P2. Same operator-level gap flagged repeatedly across the whole doc-chain, now also observed for
      `instruments-service`: no cooldown/state-transition dedup guard exists on the `main_ci_red`/`ldr_qg_failure`
      escalation trigger, so an escalation can fire (and a worker be dispatched) for a state that self-resolved before
      the worker even started investigating (this session's PR merged 2 seconds before its own escalating run began).
      Recommend gating re-fire on either (a) a minimum cooldown since the last dispatch for the same repo with an
      unchanged target-branch HEAD, or (b) checking PR merge/HEAD-advancement state at dispatch time, not just at
      escalation-creation time. Operator decision, not something a one-shot wall-clearing session should self-implement.
- [ ] 3. [INFRA] P3. Once `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phases 2-3
      land and hold, re-check whether this entire doc-chain (4 docs now, 30+ occurrences across 8+ repos) self-resolves
      — if so, archive all four docs together rather than leaving them open indefinitely as "still waiting."

## Progress Log

- **2026-08-03 ~22:20-22:50Z (`cicd` escalation `agt-f90886`, slot 8, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=1069`) — new repo for this doc-chain; disposition: already resolved, no code action needed**: failing run
  `30843828387` (`QG slice (tests)` job) hit the SAME signature as every prior entry — `pytest-timeout` fired
  `Failed: Timeout (>150.0s)` inside
  `tests/unit/test_sports_comprehensive.py::TestApiFootballAdapterEdgeCases:: test_fetch_league_fixtures_error_returns_empty`,
  which pytest-xdist's worker-crash detector then reported as an
  `INTERNALERROR> AssertionError: (..., <WorkerController gw0>)` (the xdist+pytest-timeout SIGALRM interaction this
  doc-chain has repeatedly documented). Ran a full local reproduction before touching any code: the single test in
  isolation passed in 11.4s (dominated by import overhead, no hang); the entire 110-test file
  (`test_sports_comprehensive.py`, `-n 2 --timeout=150`, matching CI's exact `PARGS`) passed in 8.7s flat, 0 failures.
  Also read the adapter code (`instruments_service/.../adapters/sports/adapters/base.py` `_throttle`/`_get_with_retry`)
  to rule out a class-state-leak theory specific to this repo (the `TestApiFootballAdapterEdgeCases` class shares the
  real `ApiFootballAdapter` class — not an isolated per-test subclass like `test_sports_base_adapter.py` uses — so its
  class-level rate-limiter state, incl. a cached `asyncio.Lock`, does persist across the ~100+ other tests elsewhere in
  the suite that instantiate the same class): `_window_max_per_min`/`_window_max_per_day` default to `0` (uncapped) and
  no test anywhere calls `set_rate_budget_rpm`/`set_window_quota` on the real class, so the window-quota path never
  fires; the autouse `_no_retry_backoff` fixture patches `asyncio.sleep` module-wide (not a bound import), which covers
  every call site in `_throttle`/`_get_with_retry` regardless of which subclass/test triggers it. No credible code-level
  mechanism found for a genuine 150s+ wall-clock hang in this test — consistent with a pure scheduler/host contention
  flake, not a code defect. Checked the PR directly rather than trusting the escalation's staleness: `gh pr view 1069` →
  **already `MERGED`**, `mergedAt=19:00:25Z`, 2 seconds _before_ the escalating run (`30843828387`,
  `createdAt=19:00:27Z`) even started — the required check had already been satisfied by an earlier passing instance;
  this run's later failure arrived too late to matter and never blocked anything. LDR's own most recent
  `quality-gates-v2` (run at `21:26:01Z`, well after the incident) = `success`, confirming LDR is green now too.
  **Disposition: no code or workflow change made or needed** — the wall was already cleared by the time of
  investigation. Noted but explicitly OUT OF SCOPE for this escalation (not dispatched to me — `main`-push failures
  correctly skip the "Escalate LDR-QG failure to orchestrator (promotion PR only)" step): `main`'s own post-merge
  `quality-gates-v2` (run `30846147595`, headSha `0ac1b64b`, current `main` HEAD) is currently `failure` — its `tests`
  job was CREATED at `19:31:34Z` but did not actually START until `21:16:11Z` (~1h45m queued), direct evidence of the
  same runner-starvation class, then failed on a _different_ test/site
  (`test_process_write_fixtures_captured_guard.py::...::test_this_run_captured_league_still_excluded`,
  `pytest_socket.SocketConnectBlockedError` on `169.254.169.254`) — another previously-unlogged random hang/flake site,
  left for whoever next triages `instruments-service` `main`-push health (or the next `main_ci_red` escalation, if one
  fires). While pushing this doc's own commit, `git pull --rebase --autostash` on `unified-trading-pm` conflicted with a
  concurrent `agt-63a88d` commit that had ALSO just appended to `continued2` (a second `git pull` mid-push found it 1
  commit behind again) — resolved on the merits by keeping `continued2` exactly as `agt-63a88d` left it (966 lines) and
  splitting this new doc for my own entry rather than pushing `continued2` over its 1000-line hard cap, per this
  doc-chain's own established split practice. `AUTHORING_SLOT=ci` (sentinel, not a real numbered slot per `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping. Slot left clean (`instruments-service` on `live-defi-rollout`, 0
  commits ahead; no code changes made in that repo this session — only this doc + `continued2`'s conflict-resolution
  commit in `unified-trading-pm`).
