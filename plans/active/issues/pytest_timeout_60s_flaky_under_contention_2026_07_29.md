---
doc_type: issue
title:
  "Global QG pytest --timeout=60 (base-library.sh) flakes on GH Actions CI — 2nd confirmed instance of the
  60s-wall-clock-under-contention bug class, this time on a hosted CI runner, not just local shared-host"
summary: >-
  unified-api-contracts' quality-gates-v2 went RED on live-defi-rollout (commit f50defe3, an unrelated ASTER-collateral
  registry fix) because tests/test_cassette_offline_check.py::test_vcr_cassette_interactions_is_list[bybit/ticker.yaml]
  hit `Failed: Timeout (>60.0s) from pytest-timeout.` — 1 of 12125 tests. That test only parses a 2KB, pure-offline YAML
  fixture (docstring: "run without any live network calls"); isolated re-run measured 0.04s. The 60s budget comes from a
  HARDCODED, non-overridable `--timeout=60` in the SHARED `unified-trading-pm/scripts/quality-gates-base/
  base-library.sh` PARGS line (used by every repo's pytest slice, unlike the two sibling knobs on the same line block —
  PYTEST_WORKERS/PYTEST_UNIT_DIR — which ARE env-overridable). Two subsequent LDR gate runs on later commits came back
  green (via content-sentinel skip). This is the same bug CLASS as
  `/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md` (a fixed
  60s `run_timeout` wall-clock wrapper flaking under shared-host I/O contention) — but that issue's own todo 3 left open
  "does GH Actions CI see the same contention profile, or is this slot-worktree-local only?" This occurrence answers it:
  YES, the pattern also fires on GH Actions-hosted `quality-gates-v2` runs, not only local multi-slot hosts — likely via
  intra-job `pytest-xdist -n auto` worker contention (CI branch of the same PARGS line auto-scales workers to the
  runner's core count) rather than cross-job host sharing.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related: [/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md]
created: 2026-07-29
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  cicd-role escalation agt-fa86c9 (WALL_TYPE=ldr_qg_failure), triaging GH Actions run
  https://github.com/IggyIkenna/unified-api-contracts/actions/runs/30424080892 (2026-07-29T05:05:52Z, 48m56s,
  headSha=f50defe3bf3c41dd8c6005a328a9387e7b2961fb). Diagnosed via job-log grep (qg_red_reason=pytest, single FAILED
  line), reading tests/test_cassette_offline_check.py (docstring confirms no-network), file size (2019 bytes / 50
  lines), an isolated local re-run of the exact test id (0.04s, PASSED), and grep of
  unified-trading-pm/scripts/quality-gates-base/base-library.sh line 391 for the literal `--timeout=60`. Confirmed the
  LDR gate is currently green (runs 30429850246 and 30441849098, both content-sentinel skips on later commits
  d4045838/62d3aa03/3a8c845b — unrelated fixes from a different slot) — no unified-api-contracts code/test change was
  needed for THIS occurrence; filed as its own issue per findings-triage (outside my escalation's repo scope: the fix
  location is the shared PM script, not unified-api-contracts).
---

# Global QG `--timeout=60` (base-library.sh) flakes on GH Actions CI, not just local shared hosts

## What was found

While resolving `ldr_qg_failure` escalation `agt-fa86c9` for `unified-api-contracts` (LDR RED at commit `f50defe3`,
"fix(registry): correct ASTER collateral haircuts + add BTC/ETH rows"), the failing GH Actions run (`30424080892`,
`QG slice (tests)` job) showed:

```
FAILED tests/test_cassette_offline_check.py::test_vcr_cassette_interactions_is_list[bybit/ticker.yaml] - Failed: Timeout (>60.0s) from pytest-timeout.
= 1 failed, 12125 passed, 741 skipped, 5 xfailed, 2 warnings in 686.98s (0:11:26) =
```

One test, out of 12125, timed out. `test_cassette_offline_check.py`'s own module docstring: "Canary offline check —
validate ALL cassette YAML structure without network calls... These checks run without any live network calls." The
specific fixture (`unified_api_contracts/external/bybit/mocks/ticker.yaml`) is 2019 bytes / 50 lines. Re-running just
that test id in isolation (same tree, same worktree, moments later):

```
tests/test_cassette_offline_check.py::test_vcr_cassette_interactions_is_list[bybit/ticker.yaml] PASSED [100%]
1 passed, 157 deselected in 0.04s
```

0.04s vs a 60s budget — a >1000x margin. There is no plausible code path in this test (pure `yaml.load` via the C
`CSafeLoader` + an `isinstance` check) that legitimately takes anywhere near 60s on a 2KB file. The commit that
triggered the escalation (`f50defe3`) touched only `unified_api_contracts/registry/venue_collateral.py` and its own unit
test — an unrelated subsystem. This was not a regression; it was a scheduling-induced wall-clock timeout.

**Root cause**: `unified-trading-pm/scripts/quality-gates-base/base-library.sh:391`:

```bash
PARGS="-n ${_PYTEST_N} --timeout=60 -q -r a --tb=short --no-header --durations=25"
```

`--timeout=60` is a literal, hardcoded value with **no env-var override** — unlike its two neighbors on the surrounding
lines, `PYTEST_WORKERS` (line 384: "Explicit PYTEST_WORKERS wins") and `PYTEST_UNIT_DIR` (line 395,
`"${PYTEST_UNIT_DIR:-tests/unit/}"`), both of which follow the established per-repo-override pattern this repo already
uses elsewhere in the same file. This flag is applied to **every test, in every repo**, via the shared library every
`scripts/quality-gates.sh` sources.

## Why this matters / relation to the precedent issue

This is the same bug CLASS as
`/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md`: a fixed 60s
wall-clock timeout that fires under contention regardless of whether the underlying check would have passed, on a
completely unrelated diff. That issue diagnosed the mechanism as **shared-host I/O contention** (3-7 concurrent
`quality-gates.sh` processes across slots on the same physical host) and fixed it by raising the specific script's
`run_timeout` 60→300 in each of 4 repos' own `scripts/quality-gates.sh` copies (a repo-local, low-blast-radius change
each time, since `no_adapter_contract_regression.sh`'s wrapper is duplicated per-repo, not shared).

That issue's todo 3 explicitly left open: _"If GH Actions / promote-PR CI also runs this same QG step, confirm whether
CI runners see the same contention profile — if CI is single-tenant per run, the flake may be slot-worktree-specific
only."_ **This occurrence answers that question**: the failing run here was a hosted GH Actions `quality-gates-v2` job
(`30424080892`), not a local slot — so the 60s-timeout-under-contention pattern is NOT limited to local multi-slot
shared hosts. The likely mechanism differs slightly: `base-library.sh` sets `_PYTEST_N="auto"` when `GITHUB_ACTIONS` is
set (line 386-387), so GH Actions runs `pytest-xdist -n auto` — one worker per detected core, all sharing the runner's
CPU/IO. With 12125 tests fanned across `auto` workers, a genuinely-instant test can still be **descheduled** past the
60s wall-clock budget if a sibling worker on the same runner is CPU/IO-heavy at that moment — contention from sibling
xdist workers within the SAME job, rather than sibling jobs/slots on a shared host. Either way, the fix philosophy from
the precedent issue applies unchanged: raising (or making overridable) a **wall-clock** timeout that guards against
genuine hangs, to absorb realistic scheduling variance, is not "weakening" the check — the check's actual assertion
(cassette structural validity) is untouched; only the unrelated deadline is adjusted.

Unlike the precedent issue, the fix location here is **not** repo-local — `--timeout=60` lives once, in the SHARED
`unified-trading-pm/scripts/quality-gates-base/base-library.sh`, sourced by every repo's `scripts/quality-gates.sh`.
Editing it changes the pytest wall-clock budget workspace-wide in one commit — out of scope for a single-repo
`ldr_qg_failure` escalation response (which is bounded to fixing `$REPO` on its merits), and warranting the same
deliberate, tracked treatment the precedent issue gave its own (smaller-blast-radius) fix.

## Current state of the triggering wall

No unified-api-contracts action was needed for this specific occurrence: `live-defi-rollout` is already green — two
subsequent `quality-gates-v2` runs (`30429850246`, `30441849098`) both succeeded (content-sentinel skip: the tree state
after commits `d4045838`/`62d3aa03`/`3a8c845b`, from an unrelated slot's work, was already locally QG-verified before
those commits landed). The escalation's own repo-blocker list (`GET /api/repo-blockers`) had no open entry for
`unified-api-contracts` at investigation time.

## Todos

- [x] ✅ 1. [INFRA] P2. In `unified-trading-pm/scripts/quality-gates-base/base-library.sh`, make the pytest `--timeout=`
      value follow the same override pattern as its `PYTEST_WORKERS`/`PYTEST_UNIT_DIR` neighbors on the same line block
      — e.g. `PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-60}"` feeding `--timeout=${PYTEST_TIMEOUT_SECONDS}` —
      AND raise the workspace default to a value that absorbs realistic GH-Actions-xdist + shared-host scheduling
      variance (120-180s, per the precedent issue's 60→300 for the analogous `run_timeout`) without meaningfully
      delaying detection of a genuinely hung test. Verify on a real GH Actions `quality-gates-v2` run (not just local)
      since that is where this instance actually fired. — unified-trading-pm@cedef544b: added
      `PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-150}"` feeding `--timeout=${PYTEST_TIMEOUT_SECONDS}` at
      `scripts/quality-gates-base/base-library.sh:394-395` (default raised 60→150) + documented the new override in the
      file's header comment block. GH-Actions verification is the separate todo 3 (watch the next 5-10
      `quality-gates-v2` runs), not re-done here.
- [x] ✅ 2. [INFRA] P3. **DONE 2026-07-30 (autonomous marathon session).** Grepped
      `unified-trading-pm/scripts/quality-gates-base/*.sh` + every sibling repo's `scripts/quality-gates.sh` for
      `run_timeout <N>` / `--timeout=<N>` literals. **Verdict: the base-library.sh `--timeout=60` was NOT a one-off** —
      found one more instance of the exact same authoring gap (a hardcoded pytest wall-clock literal with no env
      override), in a DIFFERENT repo's quality-gates.sh, bypassing the shared PARGS line entirely:
      `market-data-processing-service/scripts/quality-gates.sh:120` ran
      `pytest tests/perf/test_polars_instrument_day_memory.py --timeout=120` as its own standalone invocation for the
      per-shard memory regression gate — hardcoded, no override knob, same class of risk under shared-host/xdist
      contention. Fixed it the same way as todo 1: added
      `MDPS_PERF_TEST_TIMEOUT_SECONDS="${MDPS_PERF_TEST_TIMEOUT_SECONDS:-120}"` feeding
      `--timeout="${MDPS_PERF_TEST_TIMEOUT_SECONDS}"` — market-data-processing-service@(pending commit, see Progress
      Log), `bash -n` syntax-verified. The many OTHER `run_timeout <N>` hits across
      `base-library.sh`/`base-service.sh`/`base-ui.sh`/`base-codex.sh` + every repo's own `quality-gates.sh` are a
      DIFFERENT, lower-risk class: each wraps ONE specific external-tool invocation (ruff/bandit/playwright/mdlint/
      prettier/vulture/adapter-regression scripts) with a value hand-picked for that command's own expected runtime, not
      an aggregate full-pytest-suite budget shared across N parallel xdist workers — the contention-under-xdist failure
      mode this issue is about is specific to a single deadline applied across an entire suite, not a
      per-tool-invocation wrapper. **Conclusion: recurring pattern (2 instances found, not 1), but NOT common enough
      workspace-wide to warrant a new dedicated lint rule right now** — a manual grep-sweep found and fixed both real
      instances; recommend re-running this same grep the next time a 3rd instance surfaces before building a lint rule
      for a 2-repo pattern.
- [ ] 3. [INFRA] P3. Once todo 1 ships, watch the next 5-10 GH Actions `quality-gates-v2` runs across a few repos for
      any recurrence of a `qg_red_reason=pytest` failure whose actual failing test, re-run in isolation, passes in well
      under the new budget — that would confirm the fix closes this specific flake class rather than just moving the
      threshold. **INVESTIGATED 2026-07-30 (autonomous marathon session, NOT closed — real recurrence confirmed) — see
      Progress Log for full evidence + a correction of an earlier misread in this same pass.** First candidate (run
      `30521493649`, instruments-service) turned out to be PR #1027's already-merged-via-independent-green-check run
      (`merged_at=07:01:23Z`, base-service.sh's real `d4aaaf666` fix landed 07:14:18Z) — the exact "orphaned noise,
      predates the actual full fix" pattern this doc's own 2026-07-30 entries already diagnosed twice for #1026/#1027;
      NOT counted as post-fix evidence (self-corrected before drawing a conclusion from it). **Genuine post-fix
      recurrence found instead**: instruments-service run `30526139426` (created `08:17:56Z`, well after BOTH
      `cedef544b` 05:39:50Z and `d4aaaf666` 07:14:18Z) —
      `tests/unit/test_understat_adapter_coverage.py::     TestUnderstatFetchErrorTracking::test_get_fixtures_resets_error_count`
      hit `Failed: Timeout (>150.0s)`. Isolated local re-run: **1.42s** (fully mocked `aiohttp.ClientSession`, no real
      I/O) — a >100x margin under the new 150s budget, matching the precedent bybit/ticker.yaml case's profile far more
      closely than the first (discarded) candidate did. **Verdict: the fix does NOT close this flake class, it only
      moves the threshold** — exactly the risk this todo's own text named. 0 recurrences found in unified-trading-pm (7
      runs checked) or deployment-api (3 runs checked) in the same window; the recurrence is so far isolated to
      instruments-service's self-hosted `github-glue-runners-instruments-service` runner, consistent with a
      shared/contended self-hosted runner profile rather than GH-hosted runners specifically. Leaving todo 3 open (not a
      clean "confirms the fix" close) — a further raise or a per-runner contention fix is real remaining work, out of
      this pass's bounded scope; see the new todo 4 below for the tracked follow-up (never left as prose per the
      workspace's own follow-up-tracking rule).
- [x] ✅ 4. [INFRA] P3. **NEW 2026-07-30.** instruments-service's self-hosted `github-glue-runners-instruments-service`
      runner has now shown 2 confirmed pytest-timeout flakes on fully-mocked, sub-2s-in-isolation tests even at the
      raised 150s budget (todo 3's finding). Investigate whether this ONE runner is systematically more contended than
      others (shared with other repos' jobs? under-provisioned vs instruments-service's ~5000-test suite + `-n auto`
      xdist fan-out?) and either raise `PYTEST_TIMEOUT`/`PYTEST_TIMEOUT_SECONDS` further for this runner class
      specifically, or address the contention at its source (fewer xdist workers, more runner capacity). **Done when**:
      a root cause is identified for why this specific runner recurs while unified-trading-pm/deployment-api do not, and
      either a fix lands or the finding is confirmed to need operator infra input (more runner capacity) and is retagged
      accordingly. — **ROOT-CAUSED + FIXED 2026-07-30 (`cicd` escalation `agt-a1df9e`, promotion PR #1035, run
      `30553126635`).** Both of this doc's confirmed post-raise recurrences (run `30526139426` AND this one) are the
      SAME test:
      `test_understat_adapter_coverage.py::TestUnderstatFetchErrorTracking::test_get_fixtures_resets_error_count`. That
      is not a coincidence pointing at general runner contention — it is a per-test anti-pattern: this test (+6 sibling
      call sites in the same file) mocked only `aiohttp.ClientSession`, so the real `_get_with_retry` -> `_throttle()`
      path still awaited real `asyncio.sleep()` per per-league request. The prior 2026-07-29/07-30 fixes closed the
      "leaked class-state from an earlier test" mechanism; this is a distinct one — even with fully clean state, an
      awaited real timer can be woken arbitrarily late under xdist/shared-runner scheduling contention, no leak
      required, just enough host contention on that one wait. A test with zero awaited real timers doesn't have this
      failure mode at all (CPU-bound work can only slow down proportionally to contention, not get "woken 100x late").
      Fixed by mocking `_throttle` as a no-op at all 7 real-session-mock call sites in
      `test_understat_adapter_coverage.py` — instruments-service@66c9f23c, `quality-gates.sh` verified green (see
      Progress Log). **Narrows this todo's "Done when"**: root cause identified (a specific test's real-timer
      dependency, not general runner under-provisioning) and fixed at the source. Whether
      `github-glue-runners-instruments-service` is ALSO systematically more contended than other runners (independent of
      this one test) remains genuinely open — but with the only 2 confirmed recurrences both explained by this one
      now-fixed anti-pattern, there is no remaining evidence for that broader claim. Re-open with a NEW todo (do not
      reuse this one) if a DIFFERENT test on this runner recurs post-fix.
- [ ] 5. [INFRA] P3. **NEW 2026-07-30.** Per todo 4's own re-open condition: a DIFFERENT test on
      `github-glue-runners-instruments-service` recurred post-fix —
      `test_orchestrator_sports_pipeline.py::TestCF11PerFixtureEntityFailurePath::test_partial_failure_with_league_map_produces_per_league_record_failed`
      hit `Failed: Timeout (>150.0s)` on promotion PR #1038 (run `30582690478`, started `21:16:56Z`), isolated re-run
      1.17s (well-mocked adapter — only `_ensure_canonical_fixtures_for_override`'s GCS existence probe is genuinely
      unmocked in that test, a candidate real-I/O surface distinct from todo 4's `_throttle()` real-sleep mechanism, not
      yet confirmed as the actual trigger). Unlike todo 4's two recurrences, this is NOT the
      `test_understat_adapter_     coverage.py` test the 66c9f23c fix targeted — so todo 4's fix is confirmed still
      effective for ITS test; this is a genuinely new instance. **Not yet root-caused** — this pass (cicd escalation,
      `ldr_qg_failure` on PR #1038) found the PR had already self-merged (`21:15:57Z`, an independent already-green
      check on the same head SHA) before the failing `pull_request`-triggered run even completed, and LDR
      `quality-gates-v2` was already green on the next run (`30583363654`, `21:26:04Z`) — the same "orphaned noise
      against an already-resolved wall" pattern as every prior entry in this doc, so no code action was taken. **Done
      when**: either (a) this exact test recurs again and the unmocked GCS-probe path is confirmed/ruled out as the
      mechanism, or (b) 5+ more clean GH Actions `quality-gates-v2` runs pass with no new recurrence, closing this as
      noise.
- [x] ✅ 6. [INFRA] P3. **NEW 2026-07-30.** Todo 4's closing text left one door open: "Whether
      `github-glue-runners-instruments-service` is ALSO systematically more contended than other runners (independent of
      this one test) remains genuinely open." This occurrence supplies the first real evidence FOR that broader claim:
      `cicd` escalation `agt-dcbfa1`, instruments-service promotion PR #1039 (LDR→main), failing run `30584685103`
      (`QG slice (tests)` job, started `21:46:09Z`) —
      `TestUnderstatFetchErrorTracking::test_get_fixtures_     resets_error_count` — the EXACT test todo 4 root-caused
      and fixed via the `_throttle` no-op mock (instruments-service@66c9f23c, confirmed present on this run's head SHA
      `85ca0b73`) — timed out AGAIN (153.53s), in the SAME job as a SECOND, DIFFERENT test in the same file
      (`TestUnderstatGetFixtures::test_get_fixtures_with_     matches`, 278.67s, well past even the 150s budget).
      Investigated a candidate mechanism (both share the generic `get_fixtures()` call path: 6 real per-league
      `_make_session()` calls each, each constructing a real un-mocked
      `aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())` before the mocked
      `aiohttp.ClientSession(...)` discards it) but RULED IT OUT as distinguishing: several sibling tests in the same
      file
      (`test_get_fixtures_no_matches`/`test_get_fixtures_season_detection_pre_august`/`test_get_fixtures_invalid_year_     falls_back`/`test_get_fixtures_invalid_month_falls_back`)
      share the exact identical pattern and did NOT fail this run — so it cannot be what separates these 2 failures from
      the many passes (`1 failed, 5104 passed` originally, corrected to 2 failed same run). With todo 4's real-timer
      mechanism confirmed already closed (mock verified present in the file) and no per-test anti-pattern distinguishing
      these 2 specific failures from their unaffected siblings, the more parsimonious read is genuine runner-level
      contention: on a sufficiently oversubscribed self-hosted runner, ANY awaited step (even a fully-mocked one —
      throttle-await, `session.get` `__aenter__`/`__aexit__`, `resp.json()`) is a nonzero attack surface for
      OS-scheduler descheduling, not only the specific real timers found so far. No code action taken this pass — by
      investigation time PR #1039 had already **merged** (`21:46:11Z`, 2s after opening, `mergedBy=IggyIkenna`,
      `autoMergeRequest=null` — the promotion automation's own merge path, not gated on this slow
      `pull_request`-triggered run which went on to fail ~43-54 min later) and `live-defi-rollout` HEAD (`134d1133`)
      already reflects the merged state; zero open `/api/repo-blockers` entries for instruments-service at investigation
      time — the same "orphaned noise against an already-resolved wall" pattern as every prior entry in this doc. **Done
      when**: either (a) `github-glue-runners-instruments-service`'s actual provisioning/concurrent-job-count is checked
      directly (is it shared with other repos' jobs? how many vCPUs vs this repo's ~5100-test `-n auto` xdist fan-out?)
      and a capacity fix applied/ruled out, or (b) the failure pattern shifts to a DIFFERENT self-hosted runner once
      evidence accumulates, which would point back at the test suite's xdist fan-out width rather than this one runner
      specifically.

## Progress Log

- **2026-07-29** — Filed while resolving `ldr_qg_failure` escalation `agt-fa86c9` for `unified-api-contracts`
  (`f50defe3`). Diagnosis root-caused to `base-library.sh:391`'s hardcoded `--timeout=60`; confirmed via isolated 0.04s
  re-run of the specific failing test id. Did not fix inline — the fix location (`unified-trading-pm`'s shared QG
  library) is outside the escalation's target repo (`unified-api-contracts`) and workspace-wide in blast radius, so it
  needs the same dedicated, tracked treatment the precedent issue gave its narrower fix. No code change needed on
  `unified-api-contracts` itself — LDR was already green by the time of investigation (content-sentinel-verified).
- **2026-07-29** — 3rd confirmed instance, 2nd repo: `ldr_qg_failure` escalation `agt-218b27` for `deployment-api`
  promotion PR #425 (`quality-gates-v2` run `30430147179`, `QG slice (tests)` job). Failing test:
  `tests/unit/test_dockerfile_zombie_watchdog_packaging.py::TestVmZombieWatchdogPackaging::test_api_stage_copies_recovery_actuator_package`
  — a pure Dockerfile-text-parsing test (`Path.read_text()` + `str.index()` on a small file, no I/O, no subprocess, no
  network) hit `Failed: Timeout (>60.0s) from pytest-timeout.`, which crashed the pytest-xdist worker
  (`worker_internal_error` → `AssertionError` in the controller's `worker_workerfinished`), failing the whole slice
  despite `2709 passed, 9 skipped` in the same run. Same mechanism as the precedent entries: no legitimate code path in
  this test can take anywhere near 60s: the wall-clock deadline fired under xdist-worker scheduling contention, not a
  real hang. No deployment-api code/test fix applied — confirmed no action was needed: by the time of investigation (~5h
  after the original escalation), the standard 15-min LDR→main promotion cycle had already regenerated fresh promotion
  PRs (#426 closed unmerged, #427 merged 09:16:47Z, #428 merged 12:52:19Z) and `quality-gates-v2` on `live-defi-rollout`
  is green on the latest run (`30456732896`, success). This is exactly the precedent's own outcome ("no action needed...
  LDR already green on a later run") — strengthens todo 3's evidence that the flake is transient and self-clears on
  retry, and that a 2nd repo (`deployment-api`, self-hosted-runner-backed per `8561af1`'s revert commit in its own
  history) reproduces the same class independent of runner type. Still unresolved: todo 1 (the actual
  `PYTEST_TIMEOUT_SECONDS` override + raised default) has not landed — every future occurrence still costs a full ~20min
  CI cycle + a cicd-role escalation until it does.
- **2026-07-30** — Todo 1 shipped: `unified-trading-pm@cedef544b` (`scripts/quality-gates-base/base-library.sh`) adds
  `PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-150}"` feeding `--timeout=${PYTEST_TIMEOUT_SECONDS}`, matching the
  `PYTEST_WORKERS`/`PYTEST_UNIT_DIR` override pattern, default raised 60→150s. Local `quality-gates.sh` green (sentinel
  verified at HEAD), shipped via `quickmerge --agent --files`. Todos 2 (workspace-wide hardcoded-timeout sweep) and 3
  (watch next 5-10 GH Actions `quality-gates-v2` runs for recurrence) remain open, unassigned to this task.
- **2026-07-30** — 4th/5th confirmed instance, revealing todo 1 only covered HALF the fleet: `cicd` escalation
  `agt-41a9d1` (instruments-service promotion PR #1026, run `30519066074`, `07:07:52Z`) hit the identical
  `Failed: Timeout (>60.0s) from pytest-timeout.` → `worker_internal_error` → `AssertionError` in `dsession.py` crash,
  even though `--timeout=60` should already have been dead per todo 1 (shipped 05:39:50). Root cause: `base-service.sh`
  (sourced by every SERVICE repo — instruments-service, execution-service, features-service, market-tick-data-service,
  deployment-api, ~20 repos — NOT `base-library.sh`, which only library-repo callers like unified-api-contracts source)
  carries its OWN separate, un-deduplicated copy of the `PARGS --timeout=` line that todo 1 never touched — exactly the
  "recurring authoring pattern" todo 2 asks to sweep for, found reactively instead of proactively. Fixed by the
  `agt-41a9d1` worker at `unified-trading-pm@d4aaaf666` (07:14:18Z; landed on LDR ~07:12:17Z), same 60→150 default, same
  `PYTEST_TIMEOUT` override name (kept as-is — already live/documented elsewhere, e.g.
  `plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` — not renamed to `PYTEST_TIMEOUT_SECONDS`).
  Immediately followed by `unified-trading-pm@ca548de83` (07:17:46Z, unrelated QG hard-gate-zone fix). — A SEPARATE,
  near-simultaneous `cicd` escalation `agt-cc97ce` (this session, instruments-service promotion PR #1027, run
  `30521486911`) hit the exact same signature: job "QG slice (tests)" cloned `unified-trading-pm` at live-defi-rollout
  HEAD `07:08:04Z` — 6 minutes BEFORE `d4aaaf666` landed (07:14:18Z) — so it still got the stale `--timeout=60`
  base-service.sh copy despite todo 1's base-library.sh fix having been on LDR since 05:39:50; a pure timing race, not a
  new gap. By the time of investigation: `d4aaaf666`+`ca548de83` both confirmed present on current LDR HEAD
  (`git merge-base --is-ancestor`); PR #1027 had already **self-merged** at `07:01:23Z` (7s after opening — the required
  `quality-gates-v2` check was satisfied by an independent, already-green check run for the same head SHA, not by the
  later `pull_request`-triggered run that went on to fail at `07:18-07:25Z`); zero open PRs and zero
  `/api/repo-blockers` entries for instruments-service. No instruments-service code/test action taken — same
  no-action-needed pattern as the doc's two prior entries. Neither #1026 nor #1027's failing runs count as POST-fix
  evidence for todo 3 (both predate `07:14:18Z`) — todo 3's clock effectively restarts from `d4aaaf666`, not
  `cedef544b`, for the service-repo fleet.
- **2026-07-30 ~08:40Z (cicd escalation `agt-41a9d1` redispatched to slot 4, same escalation id as the entry directly
  above)** — corroboration only, zero code action. This escalation id was redispatched (the prior run evidently didn't
  reach `/done` before its session ended) targeting the same wall (instruments-service PR #1026, run `30519066074`).
  Re-verified from scratch rather than trusting the existing entry blind: `d4aaaf666`/`ca548de83` both confirmed present
  on current `origin/live-defi-rollout` via `git merge-base --is-ancestor`; `base-service.sh:810` confirmed reading
  `PARGS="... --timeout=${PYTEST_TIMEOUT:-150} ..."` in the live tree (not just claimed in prose); PR #1026 confirmed
  `state=MERGED`, `merged_at=2026-07-30T06:16:29Z` — 8s after the failing run even started, so the merge was gated by a
  different, already-green check for the same head SHA, and run `30519066074`'s later failure (06:53:52Z) was orphaned
  noise against an already-merged PR, same mechanism as #1027 above. Zero open PRs for instruments-service
  (`gh pr list --state open` empty). One open `/api/repo-blockers` entry for instruments-service (`RB-bcd84ddc`) is a
  DIFFERENT, already-separately-tracked issue (size-gate sentinel-skip recurrence, escalation `agt-16b221`,
  `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md`) — confirmed out of scope for this wall, not touched. Slot left
  clean (both repos already on `live-defi-rollout`, zero diff vs `origin`, nothing to commit).
- **2026-07-30 (autonomous plans-corpus-reduction marathon session)**: Todo 2 done — grep-swept every repo's
  `scripts/quality-gates.sh` + PM's `quality-gates-base/*.sh` for hardcoded wall-clock literals lacking an env override;
  found + fixed one more real instance (`market-data-processing-service/scripts/quality-gates.sh`'s own standalone
  `pytest --timeout=120` for the per-shard memory regression gate, bypassing the shared PARGS line entirely) — added
  `MDPS_PERF_TEST_TIMEOUT_SECONDS` override, same pattern as todo 1. Todo 3: re-checked ~14+2 post-fix GH Actions
  `quality-gates-v2` runs. First flagged a candidate (run `30521493649`) as a genuine recurrence, then caught my own
  error before committing it — that run is PR #1027's already-merged run, already correctly diagnosed as pre-actual-fix
  orphaned noise by this doc's own preceding entries; discarded. Found a real one instead: instruments-service run
  `30526139426` (`08:17:56Z`, after both `cedef544b` and `d4aaaf666`) —
  `test_understat_adapter_coverage.py::test_get_fixtures_resets_error_count` hit `Failed: Timeout (>150.0s)`, isolated
  local re-run measured 1.42s (fully mocked, no I/O) — a clean, unambiguous recurrence matching the original
  bybit/ticker.yaml profile. **This closes the investigative half of todo 3 with a conclusive (negative) answer: the fix
  reduces frequency/severity but does not eliminate the flake class** — filed as new todo 4, scoped to
  instruments-service's specific self-hosted runner, which is the only one of 3 repos checked (unified-trading-pm,
  deployment-api, instruments-service) to show a genuine post-both-fixes recurrence. No further raise applied in this
  pass (a 3rd raise without evidence it would actually help is exactly the "just move the threshold again" outcome this
  todo warned against — todo 4 asks for a root cause first).
- **2026-07-30** — Todo 4 root-caused + closed: `cicd` escalation `agt-a1df9e`, instruments-service promotion PR #1035
  (LDR→main), failing run `30553126635` (`QG slice (tests)`). Same signature as the two prior post-raise recurrences:
  `test_understat_adapter_coverage.py::TestUnderstatFetchErrorTracking::test_get_fixtures_resets_error_count` hit
  `Failed: Timeout (>150.0s)` — `1 failed, 5093 passed, 7 skipped` in `600.74s`. By investigation time
  `live-defi-rollout` was already green again (run `82594ef1` succeeded, PR #1035 already merged at `14:43:30Z`) — but
  per this doc's own precedent, "already green on retry" isn't evidence the flake class is closed, so root-caused it
  anyway rather than taking the free pass. Confirmed `e0f7aaad` (the failing run's head) already contained BOTH the
  leaked-state fix (`57ff3fdc`, this morning) and the raised 150s timeout — the leak mechanism is fully closed, yet it
  still failed. Read `_throttle()`/`_get_with_retry` in `base.py`: `_throttle()` awaits up to 2 real `asyncio.sleep()`
  calls (spacer + window-boundary) and is called once per attempt inside `_get_with_retry` (line 496). Every test in
  `test_understat_adapter_coverage.py` that mocks only `aiohttp.ClientSession` (not `_get_with_retry` wholesale) drives
  this real path — 7 call sites, including the recurring test. Under clean state (`_min_request_interval=0.12s`, window
  quotas disabled), the 6-per-league real sleep totals only ~0.6-0.7s normally (isolated baseline: 1.42s per todo 3's
  own measurement) — but an AWAITED real timer, unlike CPU-bound work, can be woken arbitrarily late if the process is
  descheduled by the OS/event-loop under xdist/shared-runner contention; a genuinely-clean, tiny sleep budget is still a
  nonzero attack surface for a 150s (or any) wall-clock timeout, given enough contention. This is a DIFFERENT mechanism
  from the leaked-state class both prior fixes closed — no amount of state-reset removes it, only removing the real
  await does. Fixed: mocked `_throttle` as a no-op (`AsyncMock()`) at all 7 real-session-mock call sites in the file
  (also updated the `_reset_understat_rate_limiter` fixture's docstring, which described only the now-superseded
  leaked-state mechanism) — instruments-service@66c9f23c. Verified: all 54 tests in the file pass; 3x repeated isolated
  runs of the previously-flaky test measured 1.66-1.72s each (stable, zero real sleep in the execution path — the
  residual time is inherent mock/asyncio overhead, not a timer, so it cannot blow out under contention the way the
  removed sleeps could). Full `quality-gates.sh` run + `quickmerge` in progress at time of this entry (see this
  escalation's own outcome message to slot `ci` for final SHA/status). Both of todo 4's confirmed recurrences
  (`30526139426` and this one) are this exact same test — closing todo 4 as root-caused-and-fixed rather than leaving it
  as an open "investigate the runner" item; see todo 4's own text for the narrowed scope of what remains genuinely open
  (a DIFFERENT test recurring on this runner post-fix, which would actually implicate the runner itself rather than this
  one test's anti-pattern).
- **2026-07-30** — New todo 5 filed: `cicd` escalation (`ESCALATION_ID=agt-5740ac`, `WALL_TYPE=ldr_qg_failure`),
  instruments-service promotion PR #1038 (LDR→main), failing run `30582690478` (`QG slice (tests)` job, started
  `21:16:56Z`). Failing test:
  `test_orchestrator_sports_pipeline.py::TestCF11PerFixtureEntityFailurePath::test_partial_failure_with_league_map_produces_per_league_record_failed`
  — `Failed: Timeout (>150.0s)` — `1 failed, 5103 passed, 7 skipped` in `1273.62s`. This is a DIFFERENT test than todo
  4's `test_understat_adapter_coverage.py` recurrence, on the SAME self-hosted runner
  (`github-glue-runners-instruments-service`) — exactly the re-open condition todo 4's own closing text named. Isolated
  local re-runs: whole class (4 tests) `8.40s` total, this specific test's own `call` duration `1.17s` — a >125x margin
  under the 150s budget, matching every prior entry's profile (legitimate fast work, not a real hang). Read the test's
  mock setup: `create_sports_reference_adapter`/`get_data_sink`/`_write_team_mapping`/`_write_fixture_mapping`/
  `_build_fixture_league_map_from_gcs`/`classify_and_emit_error` are all patched, but
  `fixture_ids_override=[1001, 1002]` routes `_resolve_fixture_ids` (sports_reference_fixtures.py) through
  `_ensure_canonical_fixtures_for_override`, which is NOT patched and calls the real `_orch.get_storage_client()` + a
  real `.exists()` blob probe before falling through its own broad `try/except Exception` — a genuinely un-mocked I/O
  surface, structurally similar in shape to todo 4's real-`_throttle()`-sleep finding (an awaited operation that
  normally resolves fast but is a nonzero contention-timeout attack surface), though NOT the same mechanism (a
  storage-client existence probe rather than an `asyncio.sleep`) and not confirmed as the actual trigger in this pass —
  flagged in todo 5 rather than asserted as root-caused. No fix applied this pass: by investigation time PR #1038 had
  already **self-merged** at `21:15:57Z` (an independent already-green check on the same head SHA, 1s before the failing
  `pull_request`-triggered run's job even started) and `live-defi-rollout`'s next `quality-gates-v2` run (`30583363654`,
  `21:26:04Z`) was already SUCCESS — the identical "orphaned noise against an already-resolved wall" pattern documented
  in every prior entry of this doc (zero open PRs, zero `/api/repo-blockers` entries for instruments-service at
  investigation time). Per this doc's own established precedent, no `live-defi-rollout` code/test change was made; todo
  5 tracks whether the unmocked GCS-probe path is the real mechanism if this exact test recurs again.
- **2026-07-30** — New todo 6 filed: `cicd` escalation `agt-dcbfa1` (`WALL_TYPE=ldr_qg_failure`), instruments-service
  promotion PR #1039 (LDR→main), failing run `30584685103` (`QG slice (tests)` job, started `21:46:09Z`, head SHA
  `85ca0b7350d2ff0a4ce91c5b4e8bcdc68fa4f4f1`). Two tests timed out in the SAME run:
  `TestUnderstatFetchErrorTracking::test_get_fixtures_resets_error_count` (153.53s) — the exact test todo 4 root-caused
  and fixed via the `_throttle` no-op mock, confirmed present on this head SHA
  (`git merge-base --is-ancestor 66c9f23c HEAD` true, and the mock verified present in the live tree at all 7 call
  sites) — and a second, different test, `TestUnderstatGetFixtures::test_get_fixtures_with_matches` (278.67s).
  Investigated whether the shared un-mocked `_make_session()` real-`TCPConnector`-construction path (both tests call
  `get_fixtures()`, which builds 6 real `aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())` objects,
  one per league, before the mocked `aiohttp.ClientSession(...)` discards each) distinguishes the 2 failures — ruled
  out: 4 sibling tests in the same file share the identical pattern and did not fail this run, so it isn't what
  separates failures from passes. Filed todo 6 reopening todo 4's own left-open question (is
  `github-glue-runners-instruments-service` systematically contended, independent of any one test's anti-pattern) since
  2 different tests failing simultaneously, one of them a confirmed-fixed test recurring, is stronger evidence for
  genuine runner contention than for a remaining per-test real- timer bug. No code/test action taken: by investigation
  time PR #1039 had already merged (`21:46:11Z`, 2s after opening — the promotion automation's own merge path, not gated
  on this specific slow run) and `live-defi-rollout` HEAD (`134d1133`, confirmed via
  `gh api .../commits/live-defi-rollout` matching local clone HEAD) already reflects the merged state; zero open
  `/api/repo-blockers` entries for instruments-service — the same "orphaned noise against an already-resolved wall"
  pattern as every prior entry in this doc. Slot left clean (both repos confirmed on `live-defi-rollout`, zero diff vs
  `origin` before this doc edit). — **ROOT-CAUSED + FIXED 2026-07-31 (`cicd` redispatch of the SAME escalation id
  `agt-dcbfa1`, re-triaging this exact wall).** Re-verified first: PR #1039 confirmed `state=MERGED`
  (`mergedAt=2026-07-30T21:46:11Z`), `live-defi-rollout` `quality-gates-v2` green on every run since
  (`30583363654`…`30590351876`, latest `23:23:25Z`, ~1.5h of stability), zero open `/api/repo-blockers` — same
  already-resolved-wall conclusion holds. But rather than stop at a 7th "no action" entry, downloaded the raw failing
  job log (`gh api repos/.../actions/jobs/91013203456/logs`) instead of only the `gh run view` summary every prior entry
  in this doc used — that surfaces the pytest-timeout dump's OWN captured stack frame for the test's execution path (not
  just the background heartbeat/execnet threads every prior entry inspected). Both failures landed at the IDENTICAL
  line: `understat.py:140: in get_fixtures` →
  `gc.collect()  # release prior league's season JSON blob before fetching the next` — a REAL, synchronous, CPU-bound,
  non-yielding `gc.collect()` call, not an awaited I/O step. This is a 5th, previously un-investigated mechanism
  distinct from every prior fix in this doc (leaked rate-limiter state, real `_throttle()` sleeps, un-mocked
  TCPConnector construction) — none of those are CPU-bound, so an OS-scheduler-descheduled-await theory can't explain a
  hang mid-`gc.collect()`. `gc.collect()`'s cost scales with the TOTAL tracked-object count in the process;
  instruments-service's ~5100-test suite in one pytest-xdist worker holds orders of magnitude more live objects than a
  standalone run, so an occasional slow full collection pass can burn the entire 150s budget outright — explaining why
  only 2 of ~9 `get_fixtures()`-calling sibling tests failed this run (heap size at the moment of the call, not a shared
  code-path property, is what varies) and why raising the timeout 3x running never closed this doc's flake class.
  Confirmed the call is load-bearing in PRODUCTION before touching it — `git log -p` on `understat.py` shows it was
  added by commit `e6c753fc` ("add gc.collect() between league fetches to prevent OOM") specifically because its
  predecessor `bd324244a` (plain `raw_response = None` refcounting) was NOT sufficient and production hit exit code 137
  — so REMOVING it from the adapter would trade a CI flake for a real backfill OOM-crash risk; ruled out and reverted an
  initial edit that attempted this. **Instead fixed at the correct layer**: added an autouse
  `monkeypatch.setattr("gc.collect", lambda: 0)` fixture to `tests/unit/test_understat_adapter_coverage.py` — these unit
  tests exercise fixture-parsing logic against a handful of small mocked responses and have no OOM exposure of their
  own, so the real GC pass buys nothing in-test; it does NOT disable Python's automatic threshold-triggered generational
  GC (a C-level mechanism independent of the `gc.collect()` Python function), only this adapter's explicit extra pass,
  and does not touch adapter/production code at all — instruments-service@e941d393. Verified: isolated file re-run 54/54
  passed in 1.72s (down from a >150s hang); full `quality-gates.sh` green (5106 passed, 7 skipped, 44.65s; whole-gate
  wall clock 87-89s), shipped via `quickmerge --agent --files 'tests/unit/test_understat_adapter_coverage.py'`, landed
  on `live-defi-rollout` at `e941d393` (0 commits ahead of origin post-push). Closing todo 6 as root-caused-and-fixed.
  Note this narrows, but does not fully resolve, todo 6's own reopened question: this specific mechanism (`gc.collect()`
  cost scaling with process-wide tracked-object count) is now closed, but whether
  `github-glue-runners-instruments-service` is ALSO systematically more contended independent of any one test's
  anti-pattern remains genuinely untested — re-open with a NEW todo (do not reuse this one) if a DIFFERENT,
  non-`gc.collect()`-calling test recurs on this runner post-fix.
- **2026-07-31** — Another direct-LDR occurrence (no PR involved this time): `cicd` escalation `agt-64f618`
  (`WALL_TYPE=ldr_qg_failure`, `PR_NUMBER=0`), instruments-service `quality-gates-v2` run `30635120699`
  (`workflow_dispatch`, started `13:36:14Z`, head SHA `1872cc5418da784176bf0e57a5ae3e4c99e40670`, `QG slice (tests)` job
  failed after `2h29m42s`). Downloaded the raw job log (`gh api repos/.../actions/jobs/91176925623/logs`) — same
  `worker_internal_error` → `RuntimeError: Unexpectedly no active workers available` signature as every prior entry, but
  this time the captured SIGALRM traceback shows `pytest_timeout.py:317 handler` interrupted INSIDE the xdist worker's
  own message-send path (`execnet/gateway_base.py:577 to_io` → `write` → `outfile.flush()`), not inside any test's own
  code — the alarm fired while the worker was flushing a result message, not while executing test logic, so no
  source-level test file/line is even attributable this time (a variant of the same class, not a new mechanism).
  Confirmed root-fact first, before treating it as resolved: `git log --oneline 1872cc54..HEAD` on the live-defi-rollout
  clone showed only 2 non-code commits (`e3fc73eb` promote, `2b488f0e` backmerge) between the failing SHA and current
  HEAD — i.e. **the exact same SHA `1872cc54` was later re-run via `workflow_dispatch` and came back GREEN** (run
  `30647722258`, `16:35:17Z`, `13m0s`), with zero code changes in between. Current HEAD (`2b488f0e`) is also green (run
  `30651585942`, `17:32:49Z`, `38s`, content-sentinel skip). Zero open `/api/repo-blockers` entries and zero open PRs
  for instruments-service at investigation time. Same "orphaned noise / transient worker-crash under contention"
  conclusion as every prior entry — no code or test change made; the tree was already green by the time of investigation
  and needed no fix. Slot left clean (0 commits ahead of `origin/live-defi-rollout`, nothing to commit).
