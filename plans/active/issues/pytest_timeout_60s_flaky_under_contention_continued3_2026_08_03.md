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
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-data-processing-service,
    features-service,
    alerting-service,
    deployment-service,
  ]
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
author: unknown
last_updated: 2026-08-04T13:00Z
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
  its line cap; also agt-edf42f (WALL_TYPE=ldr_qg_failure, REPO=features-service, slot 4); also agt-933d8f
  (WALL_TYPE=main_ci_red, REPO=alerting-service, slot 8); also agt-1efedf (WALL_TYPE=ldr_qg_failure,
  REPO=features-service, pr_number=936, slot 4)"
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
- [x] ✅ 2. [SCRIPT] P2. **RESOLVED 2026-08-06 — same ruling as the parent doc-chain's decision, do not duplicate
      here.** `[SCRIPT]` tag (was `[OPERATOR]`) — option (a), minimum cooldown since last dispatch with unchanged HEAD.
      Same operator-level gap flagged repeatedly across the whole doc-chain, now also observed for
      `instruments-service`: no cooldown/state-transition dedup guard exists on the `main_ci_red`/`ldr_qg_failure`
      escalation trigger, so an escalation can fire (and a worker be dispatched) for a state that self-resolved before
      the worker even started investigating (this session's PR merged 2 seconds before its own escalating run began).
      Recommend gating re-fire on either (a) a minimum cooldown since the last dispatch for the same repo with an
      unchanged target-branch HEAD, or (b) checking PR merge/HEAD-advancement state at dispatch time, not just at
      escalation-creation time. Operator decision, not something a one-shot wall-clearing session should self-implement.
      — **DONE 2026-08-08, agent-orchestrator@a351d0d** (same fix as the parent doc's todo 3 — see
      `pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` todo 3 and
      `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 6; not re-implemented separately here). Note: option (b)'s
      PR-merge/HEAD-advancement-at-dispatch-time refinement was not built — option (a) alone was operator-ruled; not a
      gap left open by this fix.
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

- **2026-08-04 ~04:07-04:55Z (`cicd` escalation `agt-933d8f`, slot 8, `alerting-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — new repo for this doc-chain (5th); disposition: already resolved via re-fire, no code action needed,
  but surfaced a second distinct root cause underneath the same symptom (single-runner queue starvation, not just the
  flaky-timeout signature itself)**: `main`'s post-promote `quality-gates-v2` (run `30865808444`, headSha `0fbf9adb` —
  the `chore(promote): LDR → main (Option-B direct)` push, PR#328 already `MERGED` at `00:30:39Z`) was `failure` on its
  `QG slice (tests)` job — `pytest-timeout` fired `Failed: Timeout (>150.0s)` on
  `tests/unit/test_main.py::test_main_runs_successfully` (`1 failed, 909 passed` in `1060.30s`), the same signature
  class as every prior entry in this doc-chain. The escalation's own framing ("LDR is green, fix already exists there")
  checked out: `main`'s content is byte-identical to LDR at that promote point (a direct promote, no intervening
  commits), so there was no code difference to hunt for. Ran a local repro before touching anything: `uv sync --frozen`
  then `tests/unit/test_main.py` in isolation — `7 passed in 0.63s`, no hang, confirming no code-level defect (the
  test's own mocking of `AlertSubscriber`/`GracefulShutdownHandler`/ `_run_subscriber_until_shutdown` is correct;
  nothing in the happy path can plausibly block for 150s). Re-triggered `quality-gates-v2` on `main`'s unchanged HEAD
  (`gh workflow run quality-gates-v2.yml --ref main`, run `30876446174`) per this doc-chain's established `main_ci_red`
  practice — but unlike prior entries (45s–20m fast green), this one sat `queued` for 9+ minutes before even starting a
  job. Investigated rather than just waiting blindly: `gh api .../actions/runners` showed **alerting-service has exactly
  ONE self-hosted runner** (`glue-ip-172-31-5-118-1`, `busy=true`), and a SEPARATE, older `quality-gates-v2` run
  (`30865864841`, `workflow_dispatch` on LDR) had its own `tests` job `in_progress` since `00:31:52Z` — 3.5h+ elapsed at
  investigation time, holding the repo's only runner and blocking my re-fire from even starting. Before treating this as
  a stuck/ runaway process (which the workspace rules permit killing after confirmation), checked the QG host-governor
  first (`qg-host-governor.sh --status` → zero live reservations, capacity free — ruling out the reservation-governor as
  the blocker) and then inspected the actual runner process tree directly on the shared host
  (`/opt/github-glue-runners-alerting-service/glue-1/`): the job was in its POST `actions/cache/v4` save step
  (`tar ... --use-compress-program zstdmt` of the venv/uv cache), not hung — confirmed via `/proc/<pid>/io` showing
  `wchar` actively increasing (~260MB/8s) across two samples, i.e. genuine forward I/O progress on an unusually large
  cache under shared-host disk contention, not a stall. Correctly did NOT kill it (RULES.md's kill-permission requires
  confirming genuine runaway/stalled state first, which this explicitly was not). Waited it out: the old run completed
  `success` after the cache-save finished (its own LDR `quality-gates-v2` genuinely green, corroborating the
  escalation's premise), the runner freed up, and my re-fire (`30876446174`) then ran cleanly — `tests` **passed**
  (confirming the original timeout was the same host-contention flake this whole doc-chain documents) and `checks`
  passed, run **`success`** in 52m16s wall-clock (mostly queue-wait, not execution). `main` is now green
  (`gh run list --branch main` confirms `quality-gates-v2 success` at headSha `0fbf9adb`). **Disposition: no code or
  workflow change made or needed.** New angle worth flagging to whoever next touches todo 1 (capacity-side root-cause
  fix): this occurrence shows the fleet-wide contention manifests in at least TWO distinct ways — (a) the
  already-documented xdist-worker/pytest-timeout false-failure signature itself, AND (b) a single-runner-per-repo
  topology turning one slow-but-legitimate job (a large cache save under I/O contention) into a 30+ minute
  queue-starvation for anything else targeting that repo's CI, including a re-fire meant to clear a wall. (b) is a
  capacity/topology question (more runners per repo, or a smaller/streamed cache), not a code defect either — out of
  scope for a one-shot wall-clearing session to fix, noted here for the capacity-side owner. No open `repo-blockers` for
  `alerting-service` to fast-path. `git status` clean throughout (no `uv.lock` drift from the local `uv sync`/pytest
  repro this time). `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered slot per `cicd.md`'s `^[0-9]+$` check)
  — skipped the authoring-slot ping. Slot left clean (`alerting-service` on `live-defi-rollout`, 0 commits ahead, no
  code changes made; only this doc entry in `unified-trading-pm`).

- **2026-08-04 ~06:55-07:10Z (`cicd` escalation `agt-88658c`, slot 8, `deployment-service`, `wall_type=ldr_qg_failure`,
  `pr_number=679`) — `deployment-service` added to this doc's own `repos:` frontmatter (previously only cited in
  `continued2`); already self-resolved before investigation, no code action needed**: escalation cited failing run
  `30843983859` (`QG slice (tests)` job `91787698183`, created `2026-08-03T20:08Z`) — `pytest-timeout` fired
  `Failed: Timeout (>300.0s)` on
  `tests/unit/test_vm_launcher_scripts.py::TestApiFootballLauncherHardenedPreemptionSignal::test_shutdown_script_syntax_and_shellcheck_clean`
  (`1 failed, 2888 passed, 17 skipped, 8 warnings in 2084.68s`) — the SAME test class already logged 3× for this exact
  repo in `continued2` above (different individual tests each time — `_writes_launch_params_...`,
  `_expected_instrument_types_cefi_deribit` — a random subset of the class, not a fixed hang site), and `PYTEST_TIMEOUT`
  already sits at the sanctioned `300` ceiling in `deployment-service/scripts/quality-gates.sh` (unchanged, confirmed on
  current HEAD `1861cbe`) — did NOT raise it a further time, per this doc-chain's established todo-1 practice. Checked
  the PR directly rather than trusting the escalation's staleness: `gh pr view 679` → already **`MERGED`**,
  `mergedAt=2026-08-03T19:02:26Z`, ~52 minutes _before_ the escalating run even started (`20:08Z`) — the required check
  had already been satisfied by an earlier passing instance (the familiar self-merge-before-confirmatory-check-completes
  pattern this doc-chain documents repeatedly); this run's later timeout arrived too late to matter and never blocked
  anything. Confirmed live gate state directly instead of stopping at the PR check: `deployment-service`'s own most
  recent COMPLETED `quality-gates-v2` on `live-defi-rollout` (`30879550487`, headSha `7a2b28f9`, `05:04:29Z`) =
  `success`, several commits ahead of the failing run's tree; a fresh run against the true current HEAD (`30885643491`,
  headSha `1861cbe`) was already `queued` at investigation time (no redispatch needed). `main`'s own most recent
  completed `quality-gates-v2` (`ddad18ed`, `00:46:23Z`) = `success` too, and a newer LDR→main promote (`c22f471`,
  `chore(promote): LDR → main (Option-B direct)`) had already landed and had its own `quality-gates-v2` `in_progress` at
  investigation end — i.e. the promotion this escalation was originally raised about has since been superseded by a
  later, already-green promotion. Ran a local isolation repro before declaring done rather than relying on the
  doc-chain's prior same-class findings alone: the entire `TestApiFootballLauncherHardenedPreemptionSignal` class (6
  tests, incl. the exact CI-flagged `test_shutdown_script_syntax_and_shellcheck_clean`) — **6 passed in 66.23s, zero
  hang, zero shellcheck/syntax failures** — decisive, no code/test defect. `GET /api/repo-blockers` → open list
  contained only `RB-e7d79260` (`market-tick-data-service`, unrelated CVE gate) — nothing to fast-path for
  `deployment-service`. **Disposition: no code or workflow change made or needed** — the wall was already fully cleared
  (PR merged, LDR green at a later HEAD, main green with a newer promotion in flight) before this investigation began;
  the already-queued `30885643491` is left to complete on its own. `AUTHORING_SLOT=ci` (sentinel, fails `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left
  clean (`deployment-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond
  this doc's own commit; no branch changes in either repo). This is now the **4th same-repo occurrence** for
  `deployment-service`/`TestApiFootballLauncherHardenedPreemptionSignal` across the doc-chain (3 in `continued2`, this
  one) — further corroborates todo 1 (capacity-side root cause, not a per-repo timeout raise) and todo 2's
  operator-flagged missing cooldown/dedup guard (this escalation fired ~52min after the PR that would have satisfied it
  had already merged).

- **2026-08-04 ~07:03-07:15Z (`cicd` escalation `agt-5ea4c7`, slot 6, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=934`) — 6th same-doc-chain occurrence for `features-service` (2nd for this repo — see `agt-edf42f` above);
  already self-resolved before investigation, no code action needed**: escalation cited failing run `30840835293`
  (`QG slice (tests)` job `91777237040`) — `pytest-timeout` (thread-dumper, `timeout_method="thread"`) fired mid
  `tests/delta_one/unit/test_cli_parser.py`, dumping MainThread's stack inside `_pytest/skipping.py`'s
  `evaluate_xfail_marks`/`iter_markers` (a call path with no plausible multi-minute hang mechanism — plain marker lookup
  on a fixture-free argparse test file, no I/O/sleep/regex), then `QG selector 'tests' FAILED (leg=tests, exit=1)`. Read
  the flagged file (`tests/delta_one/unit/test_cli_parser.py`, 29 tests) and the module under test
  (`features_service/delta_one/cli/parser.py`) end-to-end before touching anything — pure argparse/dataclass validation
  logic, no fixtures, no subprocess, no blocking call anywhere in either file; ruled out a code-level hang mechanism by
  inspection rather than local repro alone. Checked the PR directly rather than trusting the escalation's staleness:
  `gh pr view 934` → already **`MERGED`**, `mergedAt=2026-08-03T18:20:32Z`; the escalating run's own `createdAt` =
  `2026-08-03T18:20:35Z` — **3 seconds after** the merge — the exact "run started right as/after the PR that would have
  satisfied it already merged" pattern this doc-chain documents repeatedly (this run was the PR's own confirmatory
  check, which then took ~3h wall-clock under contention and failed too late to matter — mergedAt precedes it, so
  something else already satisfied the required check). Verified the merge commit (`e6dfb41f`) is an ancestor of current
  `origin/live-defi-rollout` (`git merge-base --is-ancestor` → yes) — nothing outstanding to ship for PR#934. Checked
  live gate state instead of stopping at the PR check:
  `gh run list --workflow quality-gates-v2.yml --branch live-defi-rollout` shows the familiar alternating
  success/failure/cancelled pattern all day, but the most recent COMPLETED run (`30877012874`, `04:12:57Z`, 20m7s) =
  `success` — already the `agt-edf42f` re-fire logged immediately above this entry — with a fresh `workflow_dispatch`
  run (`30885649017`) already `in_progress` at investigation time against current HEAD; not blocked on waiting for it
  given the PR-merge + local-inspection findings already independently confirm no defect, and a same-repo re-fire
  already went green 3h ago. Host state at investigation time: `uptime` load average 22.8 (vs.
  `qg-host-governor.sh --status` showing zero live reservations) — the same governor-blind-to-actual-load signature
  `ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md` flagged, corroborating todo 1 rather than adding a new angle.
  `GET /api/repo-blockers` → only `RB-e7d79260` open (`market-tick-data-service`, unrelated CVE gate) — nothing to
  fast-path for `features-service`. **Disposition: no code or workflow change made or needed** — the wall was already
  fully cleared (PR merged before its own confirmatory check even started, LDR green at a later HEAD via the
  immediately-preceding entry's re-fire, a further re-fire already in flight). `AUTHORING_SLOT` was not supplied in this
  escalation's boot vars — treated as a non-numbered sentinel per `cicd.md`'s `^[0-9]+$` check, skipped the
  authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean (`features-service` and
  `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead beyond this doc's own commit; no code changes made).
  This is now the **2nd occurrence for `features-service`** and **6th for the whole doc-chain** — further corroborates
  todo 1 (capacity-side root cause) and todo 2 (missing dispatch-time merge/HEAD-advancement check, this escalation
  fired ~7h after `agt-edf42f` already re-fired the identical repo's identical wall class green).

- **2026-08-04 ~09:45-10:05Z (`cicd` escalation `agt-58f46b`, slot 4, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=935`) — 3rd occurrence for `features-service` (7th for the whole doc-chain), SAME test file as
  `agt-5ea4c7`'s PR#934 entry immediately above; already self-resolved before investigation, no code action needed**:
  escalation cited failing run `30858945592` (`QG slice (tests)` job `91836443052`) — `pytest-timeout` (thread-dumper)
  fired mid `tests/delta_one/unit/test_cli_parser.py`, dumping MainThread's stack inside `_pytest/skipping.py`'s
  `evaluate_xfail_marks` → `stash.get()` — the IDENTICAL call path, identical file, identical
  no-plausible-hang-mechanism signature `agt-5ea4c7` already root-caused for this repo 2.5h earlier, then
  `QG selector 'tests' FAILED (leg=tests, exit=1)`. Independently re-read both the test file (29 tests, pure argparse)
  and `features_service/delta_one/cli/parser.py` (the module under test — `valid_date`/`add_delta_one_extra_args`/
  `validate_args`, zero I/O, zero blocking calls, zero fixtures) before touching anything — confirms `agt-5ea4c7`'s
  finding rather than assuming it: no credible code-level hang mechanism in either file. Checked the PR directly rather
  than trusting the escalation's staleness: `gh pr view 935` → already **`MERGED`**, `mergedAt=2026-08-03T22:31:08Z`;
  the escalating run's own `createdAt` = `2026-08-03T22:31:05Z` — **3 seconds BEFORE** the merge, the same
  "confirmatory-check-still-running-when-PR-self-merges" pattern this doc-chain documents repeatedly. Went one step
  further than a bare merge-timestamp check: found the run that actually SATISFIED the required check —
  `gh run list --workflow quality-gates-v2.yml` for the same headSha (`5275fef1d6ed`) shows an EARLIER completed run
  (`30857768146`, `createdAt=22:12:34Z`, `conclusion=success`) that finished ~19 minutes before the later,
  escalation-flagged run (`30858945592`, `createdAt=22:31:05Z`) even started — i.e. two `quality-gates-v2` runs fired
  for the identical commit (ordinary `pull_request`-sync trigger + a later re-check/supersede trigger), the first went
  green and gated the merge, the second is the redundant one that hit host contention and failed ~16 minutes AFTER the
  PR had already merged on the first green run. Verified the merge commit (`aa175f1d`) is an ancestor of BOTH
  `origin/main` and `origin/live-defi-rollout` (`git merge-base --is-ancestor` → yes/yes) — nothing outstanding to ship
  for PR#935. Checked live gate state instead of stopping at the PR check: current LDR HEAD (`85e72625`) is many commits
  past this merge; a `workflow_dispatch` run already `in_progress` against that exact current HEAD (`30897598328`,
  `QG slice (tests)` job running since `10:58:21Z`, ~52min elapsed at investigation time) — did NOT re-trigger a
  duplicate, one is already in flight against the true current tree. Checked runner state before concluding this was
  "just waiting": `gh api .../actions/runners` shows `features-service` has exactly ONE self-hosted runner
  (`glue-ip-172-31-3-59-1`, `busy=true`) — the same single-runner-per-repo topology `agt-88658c`'s `deployment-service`
  entry flagged as a second, distinct contributing mechanism (queue-starvation, not just the xdist/timeout signature
  itself). Host `uptime` at investigation time: load average 19.73/19.64/18.96 — `qg-host-governor.sh` is not present in
  this repo's `scripts/quality-gates-base/` (a per-repo layout difference, not investigated further — out of scope for a
  one-shot wall-clearing session), so could not directly reproduce the governor-blind-to-load check other entries ran,
  but the load level itself is consistent with the same contention class. `GET /api/repo-blockers` → `{"open": []}` —
  nothing to fast-path for `features-service`. **Disposition: no code or workflow change made or needed** — the wall was
  already fully cleared (PR merged via an earlier green run of the same commit, LDR green-in-flight at a much later
  HEAD, no repo-blocker). `AUTHORING_SLOT=ci` (sentinel, fails `cicd.md`'s `^[0-9]+$` check) — skipped the
  authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean (`features-service` and
  `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no code
  changes made in either repo). This is now the **3rd occurrence for `features-service`** (all three:
  `test_cli_parser.py` ×2, `test_technical_indicators.py` ×1) and **7th for the whole doc-chain** — further corroborates
  todo 1 (capacity-side root cause, not a per-repo timeout raise) and the new single-runner-topology angle `agt-88658c`
  first surfaced (now observed on a SECOND repo).

- **2026-08-04 ~12:39-12:50Z (`cicd` escalation `agt-1efedf`, slot 4, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=936`) — 4th occurrence for `features-service` (8th for the whole doc-chain), SAME test file as
  `agt-5ea4c7`/`agt-58f46b`'s two entries above; already self-resolved before investigation, no code action needed**:
  escalation cited failing run `30866617062` (`QG slice (tests)` job `91859800925`) — `pytest-timeout`
  (`timeout_method="thread"`) fired mid `tests/delta_one/unit/test_cli_parser.py`, dumping MainThread's stack inside
  `_pytest/skipping.py`'s `evaluate_xfail_marks` → `stash.get()` — the IDENTICAL call path/file/signature this doc-chain
  has now root-caused 3 separate times for this exact file. Checked the PR directly rather than trusting the
  escalation's staleness: `gh pr view 936` → already **`MERGED`**, `mergedAt=2026-08-04T00:46:11Z`; the escalating run's
  own `createdAt` = `00:46:07Z` — **4 seconds BEFORE** the merge, the same
  "confirmatory-check-still-running-when-PR-self-merges" pattern this doc-chain documents repeatedly. Verified nothing
  outstanding to ship: PR#936's merge commit (`612a3947`) is an ancestor of `origin/main`, and its head content
  (`02360ee5`) is an ancestor of `origin/live-defi-rollout` (both `git merge-base --is-ancestor` → yes) — the LDR
  backmerge already carries this content. Ran a local isolation repro before declaring done rather than relying on the
  doc-chain's prior same-file findings alone: `tests/delta_one/unit/test_cli_parser.py` (29 tests, pure argparse, zero
  I/O/fixtures) — **29 passed in 2.73s, zero hang** (hit an unrelated tooling snag first — `uv run pytest <file>` on its
  own raised `ImportError: No module named 'tests._native_lib_early_preimport'`, a `-p` plugin-resolution quirk when
  invoking a single-file path directly rather than via `scripts/quality-gates.sh`'s own invocation, not a repo defect;
  resolved with `PYTHONPATH=.`). Checked live gate state: current LDR HEAD (`2f27addc`) already has a fresh
  `quality-gates-v2` `workflow_dispatch` run `queued` (`30910052434`) at investigation time — did not trigger a
  duplicate. Host `uptime` load average at investigation time: `25.59/21.94/20.05` on a shared multi-slot host —
  consistent with the same contention class every prior entry documents. Noted, out of scope for this `ldr_qg_failure`
  wall (a separate `main_ci_red` symptom, per this doc-chain's established scoping): current `main` HEAD (`6a1460f0`, a
  LATER LDR→main promote than PR#936's own merge) has its own most-recent completed `quality-gates-v2` (`30892320551`,
  `08:31:35Z`) = `failure` — left for whoever next triages `features-service` `main` health or the next `main_ci_red`
  escalation. `GET /api/repo-blockers` → `{"open": []}` — nothing to fast-path for `features-service`. **Disposition: no
  code or workflow change made or needed** — the wall was already fully cleared (PR merged 4s after its own confirmatory
  check started, LDR green-in-flight via an already-queued run, local repro clean). `AUTHORING_SLOT=ci` (sentinel, fails
  `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the
  FYI). Slot left clean (`features-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of
  origin beyond this doc's own commit; no code changes made in either repo). This is now the **4th occurrence for
  `features-service`** (`test_cli_parser.py` ×3, `test_technical_indicators.py` ×1) and **8th for the whole doc-chain**
  — further corroborates todo 1 (capacity-side root cause) and todo 2 (missing dispatch-time merge/HEAD-advancement
  check — this is the THIRD `features-service` occurrence where the escalating run's `createdAt` sits within
  single-digit seconds of the PR's own `mergedAt`).

- **2026-08-04 ~12:47-13:00Z (`cicd` escalation `agt-43f424`, slot 7, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=1072`) — 4th occurrence for `instruments-service` (9th for the whole doc-chain), but a NEW signature within
  the family: `checks`/`typecheck` (basedpyright) timeout, not `tests`/`pytest-timeout`; already self-resolved before
  investigation, no code action needed**: escalation cited failing run `30868240796` (`QG slice (checks)` job
  `91864635465`) — NOT the pytest-xdist signature every prior entry in this doc-chain documents. The `[4/6] TYPE CHECK`
  phase itself timed out: `qg-governor` held the job in `WAIT_CPU` for 884s before admitting it
  (`reserved 3657MB (ADMIT) after 884s`), then basedpyright ran from admission to
  `❌ Type check FAILED/timeout (exit=124)` in exactly ~120.5s — i.e. it hit `PYRIGHT_TIMEOUT`'s 120s default budget
  under live host contention, not a code-level type error (no basedpyright diagnostic output precedes the timeout line).
  Checked the PR directly rather than trusting the escalation's staleness: `gh pr view 1072` → already **`MERGED`**,
  `mergedAt=2026-08-04T01:16:25Z`; the escalating run's own `createdAt` = `01:16:26Z` — **1 second AFTER** the merge,
  the tightest margin logged in this doc-chain yet (the confirmatory check was still queued/running when the PR
  self-merged on an earlier signal). Verified nothing outstanding to ship: PR#1072's merge commit (`ebebd2e1`) is an
  ancestor of BOTH `origin/main` and `origin/live-defi-rollout` (`git merge-base --is-ancestor` → yes/yes). Checked live
  gate state instead of stopping at the PR check: LDR's own next completed `quality-gates-v2` (`30873658868`,
  `03:04:09Z`, ~1h48m after the incident) = `success`; a later `workflow_dispatch` run against current LDR HEAD
  (`96ea6c4b`) was `in_progress` at investigation time (`30906285537`, started `11:47:34Z`) with its `QG slice (checks)`
  job (the exact job class that failed originally) already completed **`success` in 14m48s** — direct evidence the
  typecheck leg passes fine on the current tree once actually scheduled; its `QG slice (tests)` job was still running at
  ~60min elapsed (long but not itself a failure). Host state at investigation time: `uptime` load average
  20.19/21.42/20.10 on an 8-core host, while `qg-host-governor.sh --status` showed `running heavy phases: 0` /
  `live reservations: none` — the same governor-blind-to-actual-load signature todo 1 already flagged, now corroborated
  for the `checks`/typecheck selector in addition to the `tests` selector every other entry covers (the governor's own
  ledger and real host load diverge regardless of which QG leg is asking). `GET /api/repo-blockers` → `{"open": []}` —
  nothing to fast-path for `instruments-service`. **Disposition: no code or workflow change made or needed** — the wall
  was already fully cleared (PR merged 1s before its own confirmatory check began, LDR green ~1h48m later, current-HEAD
  checks-leg green again now). `AUTHORING_SLOT=ci` (sentinel, fails `cicd.md`'s `^[0-9]+$` check) — skipped the
  authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean (`instruments-service` and
  `unified-trading-pm` both on `live-defi-rollout`, no code changes made in either repo — only this doc's own commit).
  This is now the **4th occurrence for `instruments-service`** (3× `tests`/pytest-timeout, 1× `checks`/typecheck-timeout
  — same capacity-side root cause, different QG selector) and **9th for the whole doc-chain**; extends todo 1's scope
  (`PYRIGHT_TIMEOUT`, not just `pytest --timeout`, is exposed to the same governor-admission-vs-real-load gap) and
  further corroborates todo 2 (single-digit-second merge/escalation race, now observed at 1s — the tightest yet).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous, first pass): **KEEP-NA, valid.** This is the 3rd
installment of a running `cicd`-role incident log (founding → continued → continued2 → this doc), each split purely
because the prior doc hit its 1000-line hard cap. All 3 open todos fail the worker-determinable-outcome bar: todo 2 is
explicitly `[OPERATOR]`-tagged ("operator decision, not something a one-shot wall-clearing session should
self-implement"), unresolved identically across every predecessor doc in the chain; todos 1 and 3 require ongoing
interpretive judgment over a live, evolving incident signal (the residual root cause, per this doc's own entries, is
runner-pool starvation — a capacity/topology question, i.e. an operator-gated spend decision, not a code defect). No
duplicate extraction found in any active `assigned_vm: planning` doc. Consistent with continued2's independent same-day
verdict and the `fleet_wide_qg_self_hosted_runner_capacity_crisis`/`_continues_day2` sibling docs' established KEEP-NA
logic for the same root-cause family. No RECLASSIFY, no ARCHIVE. **Note**: this chain's `continued2` doc sits at
997/1000 lines (its own self-imposed hard cap) — too close to the cap to safely receive an incremental-skip marker this
pass without risking `check_line_caps.sh`'s HARD gate (the small-marker-append exception only forgives docs already OVER
cap, not ones a marker would push over); flagged for a future pass rather than risking the gate.

- **2026-08-05 (interactive session) — 4 MORE test files confirmed hit by this exact class, found via an unrelated
  re-run of the test-impact-selector backtest**
  (`/plans/active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`). Re-ran `test_impact_backtest.py`
  against `features-service` now that the CI-runner fleet split
  (`/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`) has meaningfully reduced (not
  eliminated) fleet contention — got a usable sample for the first time (5, up from 0) and all 5 flagged as "selector
  divergences" (narrowed test set missed the actual failing test). Investigated each one's real CI log directly rather
  than trusting the backtest's naive attribution: **all 5 show the identical `pytest-timeout` `+++++ Timeout +++++`
  marker this doc-chain already tracks** — `test_numba_kernels.py`, `test_feature_touchup.py`, `test_momentum.py`,
  `test_cross_timeframe_sanity.py` (the doc-chain's already-named test), and `test_anomaly.py` (all under
  `features-service`, 2026-08-03/04). **This is NOT a selector safety bug** — the selector correctly narrowed the test
  set based on the diff's actual content; these tests then separately, coincidentally timed out under load, unrelated to
  what the diff touched. It IS new evidence that this flakiness class isn't confined to `test_cross_timeframe_sanity.py`
  specifically — under sufficient contention it can fire on essentially any test that happens to be running when the
  60/150s per-test timeout elapses, expanding the known blast radius. No new todo filed here (same root cause, same
  `[OPERATOR]`-gated capacity question already tracked) — noted for whoever next re-derives the residual-contention
  baseline.
- **context-scout 2026-08-06**: populated context_scope (6 entries) — none previously recorded via a marker.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — OPERATOR dedup decision, incident log chain, prior verdict stands

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — re-verified all 3 open
items; prior verdict stands (2026-08-04 audit: "all 3 open todos fail the worker-determinable-outcome bar"). Todo 1
still open per `continued2`'s own last check (a brief runner-idle window observed once, did not hold); todo 2 is the
`[OPERATOR]`-tagged cooldown-guard item; todo 3 gated on todo 1. No RE-TRIAGE section, no prose-only work outside the 3
checkboxes. No `assigned_vm` change.

- **2026-08-09 ~02:20-03:15Z (slot 22, data_engineering, task
  `defi_dex_pool_swaps_733_row_indexer_health_findings-c4893c5446f8`)**: another corroborating occurrence,
  `market-tick-data-service` (no `PYRIGHT_TIMEOUT` override — consistent with the established "don't pre-emptively raise
  it" practice above). A local `quality-gates.sh` run repeatedly died with no visible error until the log tail was
  checked directly: `❌ Type check FAILED/timeout (exit=143)` — `[4/6] TYPE CHECK` hitting the bare 120s
  `PYRIGHT_TIMEOUT` default under this session's measured heavy host contention (9+ concurrent `quality-gates.sh`
  processes host-wide at points, `free -h` showing 5.7-8.4GiB swapped throughout, `qg-host-governor.sh --status`
  reporting only 4 physical cores on this box). Worked around with a one-shot `PYRIGHT_TIMEOUT=600` env override for
  this session's own runs only — did NOT add a permanent repo override, per this doc's established precedent that MTDS's
  occurrence rate doesn't yet warrant one. No new todo — same root cause, same `[OPERATOR]`-gated capacity question
  already tracked by todo 1.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:39bc9a22662d6f04]: KEEP-NA,
valid — both open items (track the ledger-coordination fork Phase 2-3; re-check the 4-doc chain once landed) remain
gated on that external plan, consistent with the doc-chain family's established verdict. No `assigned_vm` change.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:3d63d998f3f9b402]: KEEP-NA,
valid — 3rd split of the same doc-chain (continued2 hit its 1000-line cap); 2 open checkboxes (matches phase0=2 and my
grep; todo 2 already [x] RESOLVED 2026-08-08, same fix as the chain, correctly not re-implemented here). Todos 1 and 3
are near-verbatim copies of continued2's todos 1/3 (same P3 items, same gate on
qg_governor_glue_runner_ledger_coordination_2026_08_03.md Phase 2-3 landing AND holding) -- same analysis applies:
independently verified that doc is archived/status: complete (direct grep), but this doc's OWN final Progress Log entry
(2026-08-09 ~02:20-03:15Z, market-tick-data-service, a fresh corroborating pytest-timeout/typecheck-timeout occurrence
under measured heavy host contention -- 9+ concurrent quality-gates.sh processes, 5.7-8.4GiB swap, 4-physical-core host
per qg-host-governor.sh) is itself direct evidence recurrence continued PAST the fix landing -- the archive-gate ('o...

- **slot-2 2026-08-11 ~15:45Z (post-fix monitoring, task `pytest_timeout_60s_flaky_under_contention-472dc502ba82`, 29th
  pass of the founding doc's monitoring-window todo — appended here per that doc's own 2026-08-11 hard-cap-split
  note)**: surveyed latest 3 `quality-gates-v2` runs across all 10 primary repos tracked by the founding doc (runs
  spanning ~04:30Z–15:22Z 2026-08-11). 9 service repos: 26/27 terminal runs `conclusion=success`; 3 failures
  job-level-verified NOT the tracked flake: instruments-service `31469102636` (4 `FAILED`,
  `AttributeError: module '...' has no attribute 'storage'` — unrelated code defect, not timeout);
  market-data-processing-service `31433128155` (2 `FAILED`, `AssertionError: assert 'continuous_future' == 'FUTURE'` —
  same tradfi-casing class slot-26 already flagged in the founding doc); market-tick-data-service `31472876767` (`ERROR`
  at setup, `ImportError: cannot import name '_resolve_chain_bundle_manifest_id'` — unrelated import defect).
  unified-trading-pm: 2 success + 1 failure (`31496502920`, `checks`-slice only, `tests`-slice unaffected — known
  ratchet class). Zero `Timeout (>150s)` / pytest-timeout recurrence anywhere. Window NOT yet closed (day ~7 of ~14,
  closes ~2026-08-20); releasing via skip-current-task with `reason_code: "GATED"`, `estimated_unblock_minutes: 180` per
  the founding doc's slot-32 precedent.
