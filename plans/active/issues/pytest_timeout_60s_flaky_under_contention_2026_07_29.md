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
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    instruments-service,
    features-service,
    market-tick-data-service,
    client-reporting-api,
    unified-trading-api,
    market-data-processing-service,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related:
  [
    /plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-29
last_updated: 2026-08-02T22:20Z
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
- [x] ✅ 7. [INFRA] P3. **NEW 2026-08-01.** First occurrence of this bug class on a **synchronous, non-async, purely
      CPU-bound test** (every prior entry in this doc involves an awaited real/mocked timer — todo 4/5/6's core argument
      was that CPU-bound work "can only slow down proportionally to contention, not get woken 100x late").
      features-service `ldr_qg_failure` escalation `agt-8ac0d7` (slot 2, no PR — direct `live-defi-rollout` push gate,
      not a promotion PR), run `30668432435` (`QG slice (tests)` job, head SHA `8aa3796b`, and 3 repeat failures on the
      prior SHA `97351fef` across runs `30663077898`/`30659440157`/`30655029889`): pytest-timeout fired on
      `tests/delta_one/unit/test_cross_timeframe_sanity.py::test_output_index_matches_input` after ~8 min wall-clock
      (well past this repo's already-raised 150s `PYTEST_TIMEOUT` budget), stack-dumped inside
      `FeatureCalculator._add_lagged_features`'s `pandas` boolean-column-mask indexing. Isolated local re-run: the
      ENTIRE test file (119 parametrized cases across all 4 test functions in the file) completed in **8.98s**, no test
      over 0.63s (`--durations=20`), with a deliberately tighter `--timeout=20` override — zero slowness reproduced at
      any contention level achievable locally. The same run's `QG slice (checks)` job also failed (`exit code 1`) with
      NO attributable failing gate — every individual check (`ADAPTER CONTRACT-CALL REGRESSION`, `FORMULA-HASH DRIFT`,
      `NO-LOOK-AHEAD PATTERN`, `ASSET-GROUP PARITY`, main `features_service` basedpyright typecheck) printed PASS/✅
      immediately before the exit; the only warning-level anomaly was a pre-existing, explicitly non-blocking peripheral
      `e2e-testing/scripts/features/` basedpyright WARN (`|| log_warn`, `reportAny` on `argparse.Namespace` attributes —
      a real but cosmetic e2e-testing typing gap, unrelated to this wall and out of scope here). Confirmed HEAD
      (`d8d6b63d`, a dep-only commit, is a descendant of both failing SHAs with zero code/test diff since) had a fresh
      `quality-gates-v2` run queued for **30+ minutes with no self-hosted runner pickup** at investigation time —
      corroborated by a live snapshot of THIS shared host at the same moment: `load average: 30.43` (on the same class
      of 16-vCPU box these docs already track), `16Gi/47Gi` swap in active use, and **13 concurrent `quality-gates.sh`
      processes** running across other slots (`pgrep -af`) — matching
      `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`'s still-open `[BACKEND] P1` shared-host QG
      concurrency-gate gap, not proof of the GH-hosted `glue` runner pool specifically (separate host), but consistent
      first-hand corroboration that the whole workspace is currently oversubscribed. **No code or test action taken** —
      both sides are provably correct (clean, fast local repro); this is the capacity crisis, not a regression. Widens
      the doc's own scope: the flake class is NOT confined to awaited-timer tests — sufficiently severe host contention
      can also starve a plain synchronous pandas operation for minutes. **Done when**: (a) the currently-queued run
      completes (green confirms pure noise, consistent with local repro; red on a clean tree would need fresh
      investigation) — not blocked on here, out of this one-shot wall-clearer's scope — or (b) a THIRD non-async
      recurrence surfaces, which would justify promoting "CPU-bound tests are also exposed" from a hypothesis to a
      confirmed mechanism. — **(b) CONFIRMED 2026-08-02 (`cicd` escalation `agt-f4cc24`,
      market-data-processing-service)**: a further non-async, purely-CPU-bound recurrence — TWO
      `pandas`/`pandas.groupby` tests in the same run, no I/O, no awaited timer, real measured durations of
      1043.94s/701.45s — with the same host independently corroborating severe contention
      (`load average 48.95/54.83/53.70`, 32 concurrent `quality-gates.sh` processes). "CPU-bound tests are also exposed"
      is now a confirmed mechanism, not just this doc's original hypothesis. Closing todo 7 on this evidence.
- [x] ✅ 8. [INFRA] P2. **NEW 2026-08-01, `cicd` escalation `WALL_TYPE=main_ci_red`.** First confirmed instance of this
      doc's flake class escalating past "slow-but-completing" into a genuine multi-hour WEDGE — a `quality-gates-v2` run
      stuck `queued`/`in_progress` producing zero step progress for 3+ hours (vs. every prior entry's
      tens-of-minutes-to- ~2.5h "slow but terminal" profile), on BOTH the LDR `workflow_dispatch` run (`30685179092`,
      queued 3h+) and the `main` push-triggered run (`30684455584`, in_progress 3h+, same
      `promote/features-service/b457ee437f2c` head) simultaneously. **Cancelling and re-triggering worked** — this
      directly REFUTES the assumption several entries above made explicitly (e.g. the 2026-08-01 ~00:15Z/00:49Z entries:
      "canceling a queued run on an already-saturated single-runner pool doesn't help and risks adding load"):
      `gh run cancel` on both wedged runs, then a fresh `gh workflow run quality-gates-v2.yml --ref live-defi-rollout`,
      produced a run whose `content sentinel` + `QG slice     (tests)` jobs completed normally (9m37s to a real
      pytest-timeout verdict — same `test_cross_timeframe_sanity.py` test todo 7 already tracks) instead of wedging
      again. **Done when**: (a) confirm this holds on a second wedge instance (not yet a proven general fix, N=1), and
      (b) decide whether a wedge past some threshold (e.g. 60-90min with zero step progress) should be auto-detected +
      auto-cancelled+retriggered (candidate home: the same watchdog class as `ci-failure-watcher --auto-recover`) rather
      than requiring a human/agent to notice and intervene per occurrence. — **(a) CONFIRMED 2026-08-02 (`cicd`
      escalation `agt-f4cc24`, market-data-processing-service)**: a 2nd independent wedge instance — `main`
      push-triggered `quality-gates-v2` run `30749594379` stuck `queued` 3h30m+ with `content sentinel` green but both
      `QG slice` jobs never leaving `queued` — same zero-progress signature as the features-service case. Same fix
      applied (`gh run cancel` + `gh workflow run quality-gates-v2.yml --ref main`) and it worked again: the fresh run
      (`30757463906`) picked up immediately. N is now 2/2 for cancel+retrigger clearing a wedge. (b) Per slot-6's
      2026-08-02 assessment (still N=1 at the time) recommending AGAINST new automation — that recommendation stands
      even at N=2: 2 successful manual interventions is still far short of the bar the existing
      `auto_recover_stuck_prs`-class automation needed before it was built, and auto-cancelling a possibly-legitimate
      long-running CI job carries real risk a human/agent judgment call doesn't. Closing todo 8 — both "Done when"
      criteria are now addressed (confirmed generalizes + a considered automation-vs-manual decision on record); reopen
      with a new todo only if a 3rd wedge needs a materially different disposition (e.g. cancel+retrigger stops working,
      or wedge frequency alone justifies revisiting (b)).

## Progress Log

> **2026-08-03 line-cap remediation**: every 2026-07-29 through 2026-08-01 ~00:49Z corroboration/fix entry extracted
> verbatim to `/plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_progress_log_history_2026_08_03.md` (doc
> was at 996/1000 lines). New entries append below this note going forward.

- **2026-08-01 ~08:07-08:35Z (`cicd` escalation, `WALL_TYPE=main_ci_red`, slot 14, `AUTHORING_SLOT=ci-reconcile`)**:
  dispatched off a wall brief assuming a binary "(A) promotion stuck" / "(B) main-only stale workflow" split with
  `live-defi-rollout` already green — **that premise was false**. Found LDR itself has failed EVERY `quality-gates-v2`
  run since the last real success (`30647714046`, 2026-07-31T16:35:09Z) — 6 straight failures climbing
  30m→57m→1h11m→1h41m→1h54m→2h20m (the same monotonic-climb pattern the `agt-2f35f6`/slot-9 entry above already
  flagged), then a 7th run (`30685179092`) that didn't even fail — it sat `queued` for 3h+ with zero step progress,
  while the `main` push-triggered run from the last successful promotion (`30684455584`, PR #923, merged 04:41:59Z) sat
  `in_progress` for 3h+ identically. Confirmed via `ldr_to_main_fleet_promote.sh:475-479`'s Tier-A gate
  (`if [ "$CI_STATUS" = "FAILING" ]... GATE BLOCK`) that this is why no new promote PR had opened in 3h+ despite LDR
  being **387 commits ahead of `main`** — the fleet-promote workflow itself ran cleanly every ~15min the whole time
  (`ldr-to-main-promote-fleet` runs all `success`) and silently skipped features-service each tick, exactly as designed;
  not a broken promotion mechanism, a correctly-refusing gate reacting to a genuinely-red LDR. Root cause: same flake
  class this doc already tracks — `test_cross_timeframe_sanity.py`'s pytest-timeout hit repeatedly across the failing
  runs (confirmed via `gh api .../jobs/<id>/logs` on run `30680074425`), consistent with host contention
  (`load average 16-50` on the shared 16-vCPU box this session runs on, `13-17Gi/47Gi` swap in active use, 6-13
  concurrent `quality-gates.sh` processes from other slots observed throughout). What was NEW and worth the todo 8
  entry: the two wedged runs weren't just slow-and-eventually-failing like every prior entry — they were producing
  literally zero progress for 3h+, a qualitatively worse failure mode. Cancelled both (`gh run cancel`) and re-triggered
  fresh (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout` → run `30691249715`) rather than leave them
  wedged indefinitely (GH's own default 6h job timeout was the only thing that would eventually have cleared them). The
  fresh run did NOT wedge — `content sentinel` passed in 8s, `QG slice (tests)` reached a real verdict in 9m37s (failed
  again, same test, same mechanism — the underlying contention hadn't cleared, but the run itself behaved normally
  instead of hanging), refuting the "canceling doesn't help" assumption two entries above made. Did not hold the slot
  for the `checks` leg / full run conclusion (still `in_progress` at ~24min, consistent with this doc's own established
  precedent of not babysitting a queued/running CI pass synchronously) — the wedge is cleared and the Tier-A gate will
  re-evaluate `ci_status` live on the next `ldr-to-main-promote-fleet` tick (~15min cadence) once any run does go green;
  no further action needed from this escalation. No `live-defi-rollout` code or test change made or needed (the code is
  clean — same conclusion every prior entry in this doc reached for this and other tests). Filed as new todo 8 (the
  wedge-and-cancel finding is a distinct, actionable observation from the underlying flake class itself). Pinged the
  authoring slot with the outcome. **Note on dispatch chain**: this escalation (`agt-0cadd0`) was already worked twice
  before reaching this slot — slot 4 (02:35-07:38Z) diagnosed the identical run and explicitly chose NOT to
  cancel/retrigger ("a queued run doesn't benefit from retriggering"), then hit the known `/done` 400
  AgentRow-archived-mid-session bug (see `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`),
  causing this redispatch; a further immediate redispatch (`agt-45c03c`, slot 2, ~07:52Z) observed the same run finally
  flip `queued`→`in_progress` and also chose not to intervene. This entry is the first to actually test the
  cancel-and-retrigger action, which is why the conclusion differs (unwedged it) — see both sessions' own corroboration
  entries in `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (lines ~914-963) for the full prior chain.
  Also per `agt-45c03c`'s finding, did NOT attempt an `AUTHORING_SLOT=ci-reconcile` ping — confirmed `422` (non-integer
  `slot_id`) in that entry, a known dead end.
- **slot-6 2026-08-02**: dispatched todo 8 (backlog task `pytest_timeout_60s_flaky_under_contention-006`). Checked the
  "Done when" criteria: (a) requires a SECOND confirmed multi-hour wedge instance before this is "a proven general fix"
  (currently N=1, per todo 8's own text) — not something a worker can produce on demand, only observe; (b) requires
  deciding whether to build an auto-detect + auto-cancel + auto-retrigger watchdog for a wedged `quality-gates-v2` run.
  Surveyed the existing watcher (`scripts/repo-management/ci_failure_watcher.py`, 2001 lines) for a natural home:
  `detect_stuck_prs`/`auto_recover_stuck_prs` (close+reopen recovery) is scoped specifically to wedged PROMOTION PRs,
  and `detect_glue_starvation` is scoped specifically to QUEUED self-hosted glue jobs in the PM dispatch repo — neither
  covers todo 8's actual shape (a GH-hosted, non-PR `workflow_dispatch`/`push`-triggered `quality-gates-v2` run stuck
  with ZERO step progress for 3h+). Recommend AGAINST building new automation yet: (1) todo 8's own text explicitly
  frames this as N=1, not yet a confirmed general mechanism; (2) auto-cancelling an in-progress CI run carries real risk
  (masking a genuinely slow-but-real hang, interrupting a legitimate long-running job) that a one-off manual
  `gh run cancel` + re-trigger doesn't — building it now would be automation for an unconfirmed pattern; (3) the
  existing `auto_recover_stuck_prs` precedent already bounds its own retries and only acts on a well-understood,
  narrower failure shape (PR-level), which took multiple confirmed occurrences to earn that automation — todo 8 should
  earn the same bar before a general workflow-run-level watchdog gets built. No code change made. Checkbox intentionally
  stays `[ ]` — per this doc's own established precedent (todos 3/5/7), a "wait for a second occurrence" disposition is
  not a completion; this is a genuine "not yet actionable" state, not a discipline gap. Releasing the task via
  `/skip-current-task` rather than `/done` (a `/done` call with no checkbox flip would 409 under the M3 plan-flip gate,
  correctly — see `ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md` for a related M3 finding
  from this same session).
- **2026-08-02 ~16:25Z (`cicd` escalation `agt-60a920`, slot 8) — 1st confirmed instance in a NEW repo
  (unified-trading-api)**: promotion PR #495 (LDR→main, "Option-B direct"), failing run
  [30748526804](https://github.com/IggyIkenna/unified-trading-api/actions/runs/30748526804) (`QG slice (tests)` job,
  `pull_request`-triggered, head SHA `751483305fe5`, started `12:46:23Z`). 6 tests across 5 unrelated files all hit
  `Failed: Timeout (>150.0s) from pytest-timeout`:
  `test_defi_lp.py::TestDefiLpRebalanceHistory:: test_get_rebalance_history_returns_200`,
  `test_strategy_performance.py:: TestPerformanceEndpointMissingViewFallback::test_single_view_request_returns_only_that_view`,
  `test_routes.py::TestInstrumentRoutes::test_get_instruments_with_filter`,
  `test_event_logging.py::TestAuthEventLogging::test_auth_disabled_skips_key_validation`,
  `test_routes_extra.py::TestReportingRoutes::test_get_pnl_attribution`, and
  `test_routes_extra.py::TestDerivativesRoutes::test_get_options_chain` —
  `6 failed, 435 passed, 8 warnings in 3096.45s (0:51:36)`. No shared code path across these 5 files
  (defi/strategy/instruments/auth/reporting/derivatives) — the breadth itself is this doc's established signature for
  genuine scheduler-level contention rather than a per-test anti-pattern (todo 6's argument). Isolated local re-run of
  exactly these 6 test ids together (`uv sync --frozen` + targeted `pytest --timeout=60`): **6 passed, 2 warnings in
  14.90s**, slowest single case 0.52s setup + 0.47s call — a >300x margin under even a tightened 60s budget. Confirmed
  root fact: PR #495 `state=MERGED`, `mergedAt=2026-08-02T12:46:24Z` — **1 second** after the failing run's own
  `createdAt` (`12:46:23Z`), the tightest self-merge race yet recorded in this doc — self-merged via an independent
  already-green check on the same head SHA before this `pull_request`-triggered run had even finished its setup step.
  (`git merge-base --is-ancestor` doesn't directly apply since the promote-merge squashes to a new SHA — confirmed
  equivalence instead via `main` HEAD `68e276b7`'s own commit message/timestamp exactly matching PR #495's
  title/`mergedAt`.) Zero open PRs, zero open `/api/repo-blockers` entries for unified-trading-api. Live host
  corroboration gathered during this exact investigation: load average climbed **38→54** (16-vCPU box) and concurrent
  `quality-gates.sh --no-fix` processes climbed **27→33** (`pgrep -af`) over the ~15min of this investigation alone,
  19Gi/47Gi swap in active use — confirms the fleet-wide capacity crisis
  (`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) is still live and worsening in real time, 2 days past
  that doc's last dated entry. Further corroboration: a `workflow_dispatch` re-test of the CURRENT `live-defi-rollout`
  HEAD (`990187dd5`, run `30750131924`) had its `checks` slice queued **2h43m** (`13:32:00Z`→`16:15:31Z`) before a
  self-hosted runner picked it up, then passed; its `tests` slice was still `in_progress` at investigation time —
  direct, same-repo evidence that queue depth, not code, is the bottleneck. Same "orphaned noise against an
  already-resolved wall" conclusion as every prior entry in this doc — no `live-defi-rollout` code or test change made
  or needed. Widens this doc's confirmed-repo list to 7 (unified-api-contracts, deployment-api, instruments-service,
  features-service, market-tick-data-service, client-reporting-api, now unified-trading-api). Slot left clean
  (unified-trading-api already on `live-defi-rollout`, 0 commits ahead of `origin`, nothing to commit). Pinged the
  authoring slot (`AUTHORING_SLOT=ci`) with the outcome — likely a 400/422 given the non-numeric slot id, per this doc's
  own already-documented dead end for non-integer `AUTHORING_SLOT` values, not retried further.
- **2026-08-02 ~16:35Z (`cicd` escalation `agt-f4cc24`, slot 3) — 8th confirmed repo (market-data-processing-service),
  and 2nd confirmed multi-hour WEDGE (todo 8)**: promotion PR #567 (LDR→main), failing run
  [30747993571](https://github.com/IggyIkenna/market-data-processing-service/actions/runs/30747993571)
  (`QG slice (tests)` job, `pull_request`-triggered, head SHA `ef8b693c7862`, started `12:36Z`). Two purely synchronous,
  CPU-bound `pandas`/`pandas.groupby` tests (no I/O, no awaited timer at all — the strongest form of todo 7's "CPU-bound
  tests are also exposed" claim) both hit `Failed: Timeout (>150.0s)` with real measured `call` durations of 1043.94s
  and 701.45s:
  `test_writer_schema_preservation.py::TestTradesWriterSchemaPreservation::test_aggregation_15s_to_1m_preserves_ohlcv`
  and
  `test_orchestration_scanner_venue_scoped_listing.py::TestCefiVenueScopedListing::test_no_category_falls_back_to_whole_day_scan`
  — `1 failed` reported (xdist crash cascaded from the first) after `1h42m17s` total job time. Read both call paths
  (`_calculate_volume_clock_features`→`grouped.apply`→`_calc_interval_volume_clock`; `_list_instrument_files`→a mocked
  `list_blobs`) — no algorithmic defect, no unbounded loop, nothing plausibly O(n²) at test-fixture scale. This is
  another confirmed non-async, purely-CPU-bound recurrence of the class todo 7 first flagged (a different repo, a
  different pandas code path, TWO tests in the same run this time) — strong enough additional evidence to close todo 7's
  hypothesis-vs-confirmed-mechanism question (see todo 7). Confirmed root fact: PR #567 `state=MERGED`,
  `mergedAt=2026-08-02T12:31:22Z` — 5 minutes BEFORE the failing run even started (`12:36Z`) — self-merged via an
  independent already-green check, the same race as every prior entry. Zero open `/api/repo-blockers`. Live host
  corroboration at investigation time: `load average: 48.95/54.83/53.70` (16-vCPU class box) and 32 concurrent
  `quality-gates.sh` processes (`pgrep -af`) — worse than the unified-trading-api entry directly above (38→54, 27→33)
  taken ~20min earlier, confirming the fleet-wide capacity crisis is still actively worsening. Found the actionable
  part: a `main` push-triggered `quality-gates-v2` run (`30749594379`, "records MAIN_GREEN post-merge", not gating
  anything since the PR already merged) was stuck `queued` 3h30m+ with `content sentinel` green but both `QG slice` jobs
  never leaving `queued` — the exact zero-progress WEDGE signature todo 8 tracks, this time on a 2nd repo. Applied todo
  8's playbook: `gh run cancel 30749594379` then `gh workflow run quality-gates-v2.yml --ref main` — the fresh run
  (`30757463906`) picked up immediately instead of wedging again, confirming the fix generalizes (see todo 8, now closed
  on this evidence). No market-data-processing-service code or test change made or needed — same "orphaned noise against
  an already-resolved wall" conclusion as every prior entry in this doc. Slot left clean (0 commits ahead of
  `origin/live-defi-rollout` besides this doc edit). Pinged the authoring slot (`ci`) with the outcome.
- **2026-08-02 ~18:35Z (`cicd` escalation `agt-537de5`, slot 9, `WALL_TYPE=ldr_qg_failure`, `PR_NUMBER=0`)**: direct LDR
  push-gate red for unified-trading-api — this is the run the `agt-60a920`/slot-8 entry above already flagged as "in
  progress" while investigating a DIFFERENT run (`30748526804`, promotion PR #495): `workflow_dispatch` run
  [30750131924](https://github.com/IggyIkenna/unified-trading-api/actions/runs/30750131924) on LDR HEAD `990187dd5`
  (started `13:32:00Z`) finished `failure` after **4h50m36s** — its `checks` slice queued 2h43m before pickup then
  passed; its `tests` slice ran ~2h and hit `Failed: Timeout (>150.0s)` on **12 tests across 10+ unrelated files**
  (defi/basis, events/news, defi/lending, registry/lifecycle, defi/lp, catalogue, instrument routes, auth-middleware,
  reporting, service-status) — the widest single-run spread yet recorded in this doc, matching its established "genuine
  scheduler contention, not a per-test anti-pattern" signature even more starkly than prior entries. Every captured
  stack trace is the same shape as this doc's earlier `test_understat_...`/`test_tardis_...` entries: `TestClient.get()`
  → `anyio.from_thread.py:334 call` → `concurrent.futures._base.py:451 result` → `threading.py:359 wait` — genuinely
  blocked waiting on the ASGI app's response via the anyio portal thread, not inside any handler-specific code path.
  Reproduced locally end-to-end on current LDR HEAD (`990187dd5`, confirmed `HEAD == origin/live-defi-rollout`, zero
  diff): backgrounded full `bash scripts/quality-gates.sh` per this role's mandatory non-blocking pattern — **ALL
  QUALITY GATES PASSED in 111s, 441 passed, 0 failures, 0 timeouts** — a clean repro with zero contention-induced
  slowness locally, consistent with every prior entry's "legitimately fast, blown out by CI-side scheduling" conclusion.
  `GET /api/repo-blockers` → `{"open": []}`; `gh pr list --state open` → empty for unified-trading-api. Since this is a
  direct-LDR push gate (no PR to self-merge past the flake, unlike most prior entries in this doc), triggered a fresh
  `workflow_dispatch` re-verification
  ([30761689446](https://github.com/IggyIkenna/unified-trading-api/actions/runs/30761689446)) on the same HEAD rather
  than relying solely on the local repro — `content sentinel` passed in 5s, `QG slice (tests)`/`QG slice (checks)` still
  running at investigation time; per this doc's own established precedent, not holding the slot to babysit it
  synchronously (queued/running CI resolves asynchronously; the fleet-wide capacity crisis is the actionable item,
  already tracked in `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`, not something a single wall-clearer
  can fix). No `live-defi-rollout` code or test change made or needed — same "orphaned noise / known flake class, tree
  not actually broken" conclusion as every prior entry in this doc. Widens the confirmed-repo list's evidence for
  unified-trading-api specifically (2nd occurrence within ~2h, `agt-60a920`'s PR #495 case and this direct-push case)
  without adding a new repo to the list (already added by `agt-60a920`). Slot left clean (unified-trading-api on
  `live-defi-rollout`, 0 commits ahead of `origin` besides this doc edit). Pinged the authoring slot (`ci-reconcile`)
  with the outcome.
- **2026-08-02 ~20:30Z (`cicd` escalation `agt-4385f0`, slot 8) — 9th confirmed repo (deployment-service)**: promotion
  PR #673 (LDR→main), failing run `30752878298` (`QG slice (tests)`, `pull_request`-triggered, head SHA `24e0878d65e6`).
  `tests/unit/test_cluster_materialisation.py::TestLoadSubscription::test_missing_raises_file_not_found` (pure tmp_path
  `FileNotFoundError` check, no I/O) hit `Failed: Timeout (>150.0s)` → xdist `worker_internal_error`/`AssertionError` in
  `dsession.py` — `1 failed, 597 passed, 10 skipped, 56 errors in 7217.43s (2:00:17)`. Isolated local re-run of the
  whole file on current LDR HEAD (`e8963ec`, contains `24e0878d65e6` as ancestor): **9 passed in 14.67s** — same
  "legitimately fast, blown out by scheduling" profile as every prior entry. PR #673 `state=MERGED`
  (`mergedAt=14:47:16Z`, 3s after `createdAt`) — self-merged via an independent already-green check, same race as every
  prior entry. Zero open PRs, zero open `/api/repo-blockers` for deployment-service. Current LDR `quality-gates-v2`
  (`30765433226`) is `in_progress` (not wedged — `tests` job actively running since `20:24:42Z`), left to resolve
  asynchronously per this doc's precedent. No `live-defi-rollout` code or test change made or needed. Added
  `deployment-service` to this doc's `repos:` frontmatter. Slot left clean. Pinging authoring slot (`ci`) with the
  outcome.
- **2026-08-02 ~22:20Z (`cicd` escalation `agt-eb1cc8`, slot 5) — 3rd occurrence, unified-trading-api (direct LDR push
  gate, `PR_NUMBER=0`)**: run `30761689446` — 10 tests across 9 unrelated files (defi_basis/events/defi_lending/
  reporting_blrs_proxy/defi_lp/catalogue/routes/routes_extra x2/middleware) hit `Failed: Timeout (>150.0s)`,
  `10 failed, 431 passed in 5704.25s`. Current LDR HEAD (`990187dd5`) byte-identical to the failing SHA (zero drift).
  Reproduced locally on this exact HEAD: backgrounded `quality-gates.sh` — **ALL QUALITY GATES PASSED in 85s, 441
  passed, 0 failures** (441 = CI's 431+10, same total). Host corroboration: `load avg 40.85/43.48/41.50`, `24Gi/47Gi`
  swap in use, 22 concurrent `quality-gates.sh` processes — worse than every prior snapshot in this doc. Zero open
  PRs/`/api/repo-blockers`. A 3rd `workflow_dispatch` re-verification (`30767355814`) already in flight (checks green,
  tests in_progress) — left to resolve asynchronously, not babysat. No code/test change made or needed — same "orphaned
  noise, fleet-capacity-crisis flake class" conclusion as every prior entry. Doc now near its 1000-line hard cap (~989
  lines) — future entries should stay terse or a split/archive pass may be warranted. Slot left clean. Pinging authoring
  slot (`ci-reconcile`) with the outcome.
- **2026-08-02 ~22:30Z (`cicd` `agt-57f191`, slot 5)**: recurrence of this doc's OWN founding case —
  unified-api-contracts `ldr_qg_failure`, run `30765447372`, `test_vcr_cassette_interactions_is_list[bybit/ticker.yaml]`
  timeout, commit `7450e744` (self-contained new test file, unrelated). Isolated re-run: 0.01s. Host: `load avg 32-36`,
  26Gi swap, 20 concurrent QG procs. Zero open PRs/blockers. Retry `30769856300` already in flight (tests running) —
  left async. No code fix needed/made.
- **2026-08-02 ~22:36Z (`cicd agt-17bfd9`, slot 12) — 4th unified-trading-api occurrence**: run `30767355814` (LDR push,
  HEAD `990187dd5`), 10 tests / 9 unrelated files, same >150s timeout signature. Local repro: 441 passed/0 failed in
  50.47s. Load avg 32-36, 25 QG procs. Zero blockers/PRs. Retriggered `30770482343`, left async. No fix needed. **Doc at
  hard cap (992→now) — next occurrence MUST split/archive, not append.**
- **2026-08-03 ~01:32Z (`cicd` escalation `agt-dbfcd7`, slot 5, `WALL_TYPE=main_ci_red`)**: dispatched off a wall brief
  assuming a binary "(A) promotion stuck" / "(B) main-only stale workflow" split with `live-defi-rollout` GREEN — same
  false premise as the 2026-08-01 ~08:07Z entry above. Found `main` HEAD (`0f775529`, PR #568, already the full LDR
  promotion tip) failing on run `30757463906` — this is the SAME run the 2026-08-02 ~16:35Z (`agt-f4cc24`) entry above
  already picked up via cancel+retrigger to clear a queue-wedge; it then ran 6h30m and genuinely failed with the
  `OSError: cannot send (already closed?)` / `PluggyTeardownRaisedWarning` xdist-crash signature after 14 min of total
  silence post-`Coverage floor`, zero attributable test/traceback. Checked `live-defi-rollout` itself before assuming it
  was clean per the brief: it is NOT — 3 of the last 4 `quality-gates-v2` runs on LDR are also `failure`
  (`30774747037`/`30772053085`/`30758737872`), and `30774747037` (LDR HEAD `beb9fed6`) shows the IDENTICAL
  `OSError: cannot send`/`PluggyTeardownRaisedWarning` signature at the identical `── [3/6] TESTS ──` → 28min-silence →
  crash shape — confirms this is the fleet-wide contention class, not a main-vs-LDR code divergence (no code fix exists
  on LDR to "not re-apply" here). Live host corroboration: `load average 48.08/40.22/36.74` (16-vCPU class box),
  20Gi/47Gi swap in use, 35 live `Runner.Listener` processes, 32 concurrent `quality-gates.sh` processes — matches/
  exceeds every prior severe-contention snapshot in this doc. Did not run a local full-suite repro (would add a 33rd
  process to an already-saturated host for no new signal, per this doc's established judgment call). Zero open PRs
  (`gh pr list --state main` — only merged history), zero open `/api/repo-blockers` for market-data-processing-service.
  Triggered a fresh `workflow_dispatch` re-verification on `main` (`30777098334`) — picked up immediately (not wedged),
  left running asynchronously, not babysat synchronously per this doc's established precedent. No
  market-data-processing-service code or `live-defi-rollout` change made or needed — same "fleet-wide capacity crisis,
  tree not actually broken" conclusion as every prior entry in this doc. **Doc line-cap remediated this same turn**
  (996→trimmed; see the pointer note above the Progress Log heading) before this entry was appended, so the doc stays
  under its 1000-line hard cap. Slot left clean (market-data-processing-service already on `live-defi-rollout`, 0
  commits ahead of `origin`; only this doc + the new archive file touched, both in `unified-trading-pm`). Pinging the
  authoring slot (`ci-reconcile`) with the outcome.
