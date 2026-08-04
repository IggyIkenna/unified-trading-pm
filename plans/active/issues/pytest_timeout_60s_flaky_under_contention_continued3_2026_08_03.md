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
repos: [unified-trading-pm, instruments-service, market-data-processing-service, features-service]
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
last_updated: 2026-08-04T04:23Z
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
  its line cap; also agt-edf42f (WALL_TYPE=ldr_qg_failure, REPO=features-service, slot 4)"
context_scope:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
    instruments-service/scripts/quality-gates.sh,
    features-service/scripts/quality-gates.sh,
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

- **2026-08-03 ~22:34-22:57Z (`cicd` escalation `agt-9c7994`, slot 4, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=1068`) — THIRD occurrence for this same repo+file within the same day; disposition: already resolved, no
  code action needed**: failing run `30839360878` (`QG slice (tests)` job `91772398050`) hit the identical signature yet
  again — `pytest-timeout` fired `Failed: Timeout (>150.0s)` on
  `tests/unit/test_sports_comprehensive.py::TestCompetitionPhaseAdditional::test_whitespace_handling` (a synchronous,
  fixture-free, one-line call into `classify_competition_phase` — pure string logic, no I/O, no sleep, no regex; read
  the function directly, `instruments_service/reference_data/adapters/sports/competition_phase.py`, to rule out a
  catastrophic-backtracking or similar code-level mechanism — none exists), which pytest-xdist's worker-crash detector
  reported as `INTERNALERROR> AssertionError: (..., <WorkerController gw1>)`. Ran a full local reproduction BEFORE
  touching any code: the entire 110-test file under CI's exact `PARGS`
  (`-n auto --timeout=150 -q -r a --tb=short --no-header --durations=25`,
  `--allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket`) passed 110/110 in 13.9s flat — no hang, no failure.
  Checked the PR directly: `gh pr view 1068` → **already `MERGED`**, `mergedAt=2026-08-03T18:01:13Z`, 2 seconds _after_
  the escalating run was created (`createdAt=18:01:11Z`) — same "run started right as/after the PR that would have
  satisfied it already merged" pattern as this doc-chain's prior two `instruments-service` entries. LDR's own most
  recent completed `quality-gates-v2` (run `30854606507`, `headSha=d79b9d74`, `21:26:01Z`) = `success`, and a fresh run
  (`30858477952`) was already in progress for LDR's current HEAD (`df83fdcd`) at investigation time — not blocked on
  waiting for it given the local reproduction already independently confirms no defect. Checked `GET /api/repo-blockers`
  — none open for `instruments-service` to fast-path. **Disposition: no code or workflow change made or needed.** Noted,
  out of scope for this escalation (a separate `main`-branch symptom, not `live-defi-rollout`): `main`'s own post-merge
  `quality-gates-v2` (run `30846147595`, `headSha=0ac1b64b`) remains `failure` as of this session too (same run already
  logged in this doc-chain's immediately-prior entry above, on a different test/site — `main`-push failures correctly do
  not dispatch to `cicd` per the workflow's own escalation gating, so left for whoever next triages
  `instruments-service` `main` health). This is now a **3rd same-day, same-repo, same-file** occurrence
  (`test_sports_comprehensive.py`, escalations `agt-f90886`→PR#1069 above and now `agt-9c7994`→PR#1068) — worth flagging
  to whoever picks up todo 1/3 above that `instruments-service`'s sports-adapter test file specifically may be
  disproportionately represented in this bug class (large xdist worker-group, or simply this repo's heaviest-hit file)
  even though the mechanism remains generic host contention, not anything specific to the file's own content. Slot left
  clean (`instruments-service` on `live-defi-rollout`, 0 commits ahead; no code changes made in that repo this session —
  only this doc in `unified-trading-pm`). `AUTHORING_SLOT=ci` (sentinel) — skipped the authoring-slot ping per
  `cicd.md`'s `^[0-9]+$` check.

- **2026-08-03 ~23:00-23:12Z (`cicd` escalation `agt-681f6e`, slot 6, `market-data-processing-service`,
  `wall_type=main_ci_red`) — new repo + first `main_ci_red` (not `ldr_qg_failure`) occurrence for this doc-chain;
  disposition: already resolved via re-fire, no code action needed**: `main`'s post-promote `quality-gates-v2` (run
  `30859621125`, headSha `37aea56` — the `chore(promote): LDR → main (Option-B direct)` push, PR#573 already `MERGED`)
  was `failure` on its `QG slice (tests)` job. The escalation's own framing assumed LDR was green and the fix "already
  exists" there — checked live state instead of trusting that: `live-defi-rollout`'s own most recent `quality-gates-v2`
  `workflow_dispatch` runs were ALSO failing (`30858480894` etc., same `tests`-leg pattern, hours of alternating
  pass/fail all day) — same bug-class, not a main-specific regression, so the (A) promotion-stuck / (B)
  stale-workflow-on-main classification in `cicd.md` didn't apply; this is a 3rd distinct failure _signature_ variant of
  the same host-contention class: `main`'s narrowed-file run (`TEST_IMPACT_GATE` →
  `tests/unit/scripts/test_restamp_sports_candle_venue.py` only) produced no test failure output at all — just a silent
  ~5m20s gap then `exit=1`; LDR's own concurrent full-suite run (narrowed set empty → fell through to full suite) showed
  the mechanism directly: `PluggyTeardownRaisedWarning` / `OSError: cannot send (already closed?)` in
  `pytest_sessionfinish` on TWO xdist workers before the runner reported `exit=1` — an xdist inter-process channel dying
  under host contention during teardown, not a real test failure (no `FAILED`/`AssertionError` anywhere, coverage
  combine warned `No data was collected` — consistent with the run completing but the reporting channel being severed).
  Ran a full local reproduction before touching any code: the narrowed file (6 tests) passed clean, `6 passed in 0.44s`,
  no hang, no failure — ruling out a code/test defect for `main`'s specific failure. Re-triggered `quality-gates-v2` on
  `main`'s current HEAD (`gh workflow run quality-gates-v2.yml --ref main`) rather than declare done via
  local-repro-only, since `main_ci_red` (unlike the PR-scoped `ldr_qg_failure` cases in prior entries) means the actual
  required-check state on `main` stays red until something re-runs it: the re-fire (run `30861199746`) went green in 45s
  via the content-hash green-marker fast path (tree hash matched an already-verified state, short-circuiting past the
  flaky `tests` slice entirely) — confirms the tree content was never the problem. `main` is now `success`/green
  (verified via `gh run list`). `live-defi-rollout` itself remains red on its own most recent `workflow_dispatch` runs
  as of this session — noted, explicitly out of scope for a `main_ci_red` wall (this doc-chain's todo 1 capacity-side
  fix is the actual owner of that). No open `repo-blockers` for `market-data-processing-service` to fast-path.
  Incidental `uv.lock` rewrite from the local `uv run pytest` repro (dependency-graph resolution-marker/version drift,
  unrelated to any real dep change) was reverted (`git checkout -- uv.lock`) before leaving the slot.
  `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered slot) — skipped the authoring-slot ping per `cicd.md`'s
  `^[0-9]+$` check. Slot left clean (`market-data-processing-service` + `unified-trading-pm` both on
  `live-defi-rollout`, no code changes, only this doc entry).

- **2026-08-04 ~04:03-04:26Z (`cicd` escalation `agt-edf42f`, slot 4, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0`) — new repo for this doc-chain (4th); disposition: already resolved via re-fire, no code action
  needed**: failing run `30873653061` (`QG slice (tests)` job, 49m14s) hit the same signature class again —
  `pytest-timeout` fired inside
  `tests/delta_one/unit/test_feature_groups/test_technical_indicators.py:: TestTechnicalIndicatorsCalculate::test_bollinger_bands_columns`
  mid-`pd.concat`/`shift` on a 50-row synthetic candle fixture
  (`Insufficient data for reliable features. Has 50 candles...` warning immediately preceding the stack dump), then
  reported `QG selector 'tests' FAILED (leg=tests, exit=1)`. Ran a full local reproduction BEFORE touching any code:
  `bash scripts/quality-gates.sh` (backgrounded per `cicd.md`'s mandatory pattern) on unchanged `live-defi-rollout` HEAD
  (`383d8548`) passed the ENTIRE suite — `18245 passed, 209 skipped` in 263.7s, zero failures; the specific CI-flagged
  test in isolation passed in `0.70s` (`1 passed in 0.70s`). The gate's own TYPE CHECK step separately hit `exit=143` at
  its already-raised `PYRIGHT_TIMEOUT=300` local default in this same repro run (host load average was 16.6 on 16 cores
  from 3+ concurrent slot QG runs at the time) — considered raising `PYRIGHT_TIMEOUT` further (this repo's own
  `quality-gates.sh` comments cite that exact philosophy, and other repos run 900-1200s), but a bare unwrapped
  `basedpyright features_service/` timed independently at `29s` once host contention eased, and this doc-chain's own
  todo 1 already rules a per-repo timeout raise out as the wrong fix for this bug class (capacity-side, not per-repo) —
  so no timeout change made. Checked the actual CI failure signature directly (`gh run view --log-failed` / `--log`)
  rather than trusting a local-only repro: confirmed `qg_red_reason: "pytest"` (the `tests` slice, matching the local
  finding), not `typecheck`. Checked runner state: `gh api repos/IggyIkenna/features-service/actions/runners` showed 2
  self-hosted `glue` runners, one ( `glue-ip-172-31-3-59-1`) idle (`busy=false`) at investigation time. Re-triggered
  `quality-gates-v2` on unchanged LDR HEAD (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`, run
  `30877012874`) rather than declare done via local-repro-only, per this doc-chain's established
  `main_ci_red`/`ldr_qg_failure` practice — the re-fire went **green in 20m7s** (`success`), confirming the tree content
  was never the problem. Checked `GET /api/repo-blockers` — none open for `features-service` to fast-path.
  **Disposition: no code or workflow change made or needed.** `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real
  numbered slot per `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping. Slot left clean (`features-service`
  on `live-defi-rollout`, 0 commits ahead, no code changes made).
