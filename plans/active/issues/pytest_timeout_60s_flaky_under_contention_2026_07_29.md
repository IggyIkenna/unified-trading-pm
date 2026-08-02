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
repos: [unified-trading-pm, unified-api-contracts, instruments-service, features-service]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related:
  [
    /plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-29
last_updated: 2026-08-02
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
- **2026-07-31** — 1st confirmed instance in a NEW repo (market-tick-data-service, previously only named as a
  `base-service.sh` consumer in this doc, never an actual occurrence): `cicd` escalation `agt-96b341`
  (`WALL_TYPE=ldr_qg_failure`), promotion PR #804 (LDR→main), failing run `30658462443` (`pull_request`-triggered,
  started `19:16:27Z`, head SHA `6bcc5154d22fb7a51ff991287c185886924eebdd`, `QG slice (tests)` job, self-hosted runner
  `glue-ip-172-31-5-118-1`). Failing test:
  `tests/unit/test_tardis_free_only_gate.py::test_free_only_allows_recent_rolling_window` —
  `Failed: Timeout (>150.0s) from pytest-timeout.` — `1 failed, 9778 passed, 25 skipped, 1 xpassed` in `3212.47s`
  (0:53:32). Read the test + its call path (`TickDataHandler.process()` → `_check_early_exit` → `is_tardis_free_date()`
  (pure date arithmetic, no I/O) → mocked `process_ticks`) — no plausible real-I/O or real-timer path for this specific
  test (unlike todo 4's `_throttle()` sleep or todo 5's un-mocked GCS probe; `_apply_freshness_skip` is also not
  reachable here since the fixture sets `h._bucket = ""`, short-circuiting before `check_shard_freshness`). Isolated
  re-run of the whole 5-test file: **2.58s** (all 5 pass), matching every prior entry's profile of a legitimately-fast
  test blown out by scheduling contention, not a real hang. Confirmed root-fact before treating it as resolved: PR #804
  `state=MERGED`, `mergedAt=2026-07-31T19:16:32Z` — 5s after the failing run even started, i.e. self-merged via an
  independent already-green check on the same head SHA before this slower `pull_request`-triggered run completed
  (identical mechanism to #1027/#1035/#1038/#1039 above).
  `git merge-base --is-ancestor 6bcc5154 origin/live-defi-rollout` confirmed true on current LDR HEAD; subsequent LDR
  `quality-gates-v2` runs (`30640305750`, `30644139336`, `30651592108`) all `success`. Zero open `/api/repo-blockers`
  entries for market-tick-data-service. Same "orphaned noise against an already-resolved wall" conclusion as every prior
  entry — no code or test change made. Slot left clean (0 commits ahead of `origin/live-defi-rollout`, nothing to
  commit).
- **2026-07-31 (cicd escalation `agt-02ea96`, slot 3)**: instruments-service promotion PR #1048 (LDR→main), failing run
  `30658448525` (`QG slice (tests)` job, started `19:16:13Z`, head SHA `aadd856c`). Identical "no-attributable-test"
  signature to the immediately-preceding entry (`agt-64f618`): `pytest_timeout.py:317 handler` fired INSIDE the xdist
  worker's own IPC flush (`execnet/gateway_base.py:577 to_io` → `write` → `outfile.flush()`),
  `Failed: Timeout (>150.0s)`, cascading into `worker_internal_error`/`AssertionError`, then the whole
  `quality-gates.sh` process SIGKILLed (`exit=137`) ~6min later (`19:39:00Z`) — no source-level test file/line
  attributable, confirming a scheduling artifact, not a per-test bug. Diff since the last confirmed-green run
  (`2b488f0e`, run `30651585942` success `17:32:49Z`) is one unrelated commit (`aadd856c`, +55 lines, a new
  bounded-wrapper script for an unrelated one-off DeFi-catalogue script — zero test/core-code changes), ruling out a
  code regression. PR #1048 already **MERGED** (`mergedAt=19:16:18Z`, 5s after the check run started — an independent
  already-green check satisfied the merge, same self-merge pattern as every prior entry). Zero open
  `/api/repo-blockers`, zero open PRs for instruments-service. New wrinkle: the standing recovery `workflow_dispatch`
  reruns (`30659447161` live-defi-rollout@`df9b6daa`, queued since `19:31:59Z`; `30664529775` main@`25e67740`, queued
  since `20:52:27Z`) were STILL queued with zero pickup after 2h+ at investigation time (`21:44Z`). Confirmed this is
  queue depth, not a dead runner: sibling repos on the same `i-0c9b283b31d6b5ca7` protected-6 box
  (market-tick-data-service, features-service) show jobs from the same ~19:16-19:32Z window actively completing (some
  taking 2h+ end-to-end) or still `in_progress` at investigation time — the box is grinding through a deep backlog, not
  wedged. Consistent with the standing operator ruling ("protected-6 stay self-hosted, accept recurring reds, resolve
  via retrigger", `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) — did not add a 3rd retrigger (2 already
  in flight) and did not attempt runner/host-level intervention (out of a cicd worker's scope;
  `ssm:DescribeInstanceInformation` also denied for the current IAM identity, confirming no ambient access to this box
  either way). No code/test action taken — same "orphaned noise against an already-resolved wall" conclusion as every
  prior entry in this doc. Slot left clean (0 commits ahead of `origin/live-defi-rollout` on instruments-service).
- **2026-07-31 (cicd escalation `agt-d404d8`, slot 7)**: the retry run the immediately-preceding entry left "STILL
  queued" (`30659447161`, live-defi-rollout@`df9b6daa`) eventually got a runner and completed — `failure`, `2h39m34s`
  total. This time a source-level test IS attributable (unlike the two immediately-preceding IPC-flush-only entries):
  `FAILED tests/unit/test_event_logging.py::test_required_lifecycle_events_importable - Failed: Timeout (>150.0s) from pytest-timeout.`
  — `1 failed, 5119 passed, 7 skipped, 11 warnings in 2470.61s (0:41:10)`. This is a NEW test for this doc (not
  `test_understat_adapter_coverage.py`/`test_orchestrator_sports_pipeline.py`/etc from prior entries). Read the test: a
  pure `ast.parse()` walk over ~a dozen small `.py` files in `instruments_service/engine/orchestrator/` — no I/O, no
  network, no real timer, no subprocess; isolated local re-run: **7.55s** (`1 passed`), a ~20x margin under the 150s
  budget, matching every prior entry's "legitimately fast, blown out by scheduling" profile even more starkly than most
  (an AST walk over small files has essentially no plausible slow path at all). Confirmed root-fact before concluding:
  `git log --oneline df9b6daa..origin/live-defi-rollout` shows 2 further commits landed since (`11169213` deps-pin
  refresh, `1bf5467c` docs-only) — current HEAD is `51f85d9c`. That HEAD's own `quality-gates-v2` run (`30669732609`,
  `workflow_dispatch`, created `22:22:23Z`) passed its `content sentinel` job (`success`, `22:22:38Z`) but its
  `QG slice (tests)`/`QG slice (checks)` jobs are themselves still `queued` (checked `22:33Z`, ~11min in queue) —
  consistent with the same self-hosted protected-6 backlog the immediately-preceding entry already diagnosed (not a dead
  runner; did not add a redundant retrigger). Zero open `/api/repo-blockers` entries for instruments-service
  (`{"open": []}`). No code/test action taken — same "orphaned noise / known flake class, tree not actually broken"
  conclusion as every prior entry in this doc; this occurrence's only new information is a 6th distinct
  attributable-test instance (this doc's list so far: bybit/ticker.yaml cassette, Dockerfile-parsing, 2x
  `test_understat_adapter_coverage.py` mechanisms, `test_orchestrator_sports_pipeline.py`,
  `test_tardis_free_only_gate.py`, now `test_event_logging.py::test_required_lifecycle_events_importable` — the breadth
  continues to point at genuine runner-level contention on `github-glue-runners-instruments-service`, not a per-test
  anti-pattern, since this latest one has no I/O/timer/subprocess surface at all to blame). Slot left clean (0 commits
  ahead of `origin/live-defi-rollout` on instruments-service, nothing to commit).
- **2026-07-31 ~22:34Z (cicd escalation `agt-29d892`, slot 11)**: `unified-api-contracts` promotion PR #821 (LDR→main,
  "Option-B direct"), failing run `30658448355` (`QG slice (tests)` job, databaseId `91248622261`, self-hosted runner
  `glue-ip-172-31-5-118-1` — confirmed via the job's own setup-log group, and the SAME exact runner named in the
  immediately-preceding market-tick-data-service PR#804 entry above; instruments-service PR#1048's failure two entries
  up also started in this same `~19:16-19:22Z` window, a 3rd repo hitting the box simultaneously). A quieter variant of
  this doc's signature: entered `── [3/6] TESTS ──` at `19:22:11Z`, then **zero output of any kind** (no per-test dots,
  no pytest-timeout SIGALRM traceback, nothing) until the wrapper shell's own `Killed` message at `19:31:27.89Z` —
  `exit=137` (SIGKILL), `9m16s` of complete silence, no source-level test attributable at all (not even the
  execnet-IPC-flush frame the two entries above captured) — consistent with a straight external OOM-kill of the whole
  process (SIGKILL gives no chance to flush pytest's buffered stdout), one step further along the same spectrum as the
  captured-traceback variants. Confirmed root facts before concluding: PR #821 `state=MERGED`, `mergedAt=19:16:17Z` — 5
  min BEFORE the failing run's own TESTS phase even started — self-merged via an independent already-green check on the
  same head SHA (`fb792b7a`), identical self-merge race to every prior entry. `live-defi-rollout` HEAD (`2b7454a8`)
  matches my slot clone exactly AND matches the head SHA of the very next `quality-gates-v2` run (`30659459010`,
  success, `19:32:10Z` — 5 min after the kill) — 8 consecutive green LDR runs since, sustained ~3h to investigation
  time. Zero open `/api/repo-blockers`, zero open PRs, for `unified-api-contracts`. Given CI itself already produced a
  green run on this exact commit, chose NOT to additionally burn a full local `quality-gates.sh` repro (the default
  `ldr_qg_failure` recipe) after checking host state first: my own slot host measured `load average: 27.20` on 16 vCPUs
  (~1.7x oversubscribed), `18Gi/47Gi` swap in active use, and **14 concurrent `quality-gates.sh --no-fix` processes**
  already running (`pgrep -af`) at investigation time — a 15th full pass would only have added to the exact contention
  this doc and `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` track, for strictly less information than
  the CI run already provided on the identical SHA. This live host snapshot is fresh, direct, first-hand corroboration
  for that sibling doc's still-open `[BACKEND] P1` "machine-enforced shared-host QG concurrency gate" todo (14 observed
  vs. its own `max(2, floor(cores/4))`-derived cap of ~4) — cross-referenced here, not duplicated as a new todo in
  either doc. No code/test action taken — same "orphaned noise against an already-resolved wall" conclusion as every
  prior entry in this doc. Slot left clean (`unified-api-contracts` already on `live-defi-rollout`, 0 commits ahead of
  `origin`, nothing to commit there).
- **2026-07-31 ~23:05Z (cicd escalation `agt-719421`, slot 7)**: instruments-service promotion PR #1049 (LDR→main),
  failing run `30669400970` (`QG slice (tests)` job, `pull_request`-triggered, head SHA `111692134aa3`, started
  `22:19:01Z`). Downloaded the raw job log (`gh api repos/.../actions/jobs/91283678626/logs`) — identical
  no-source-level-test-attributable signature to the two immediately-preceding entries: `pytest_timeout.py:317 handler`
  fired inside the xdist worker's own IPC flush path (`execnet/gateway_base.py:577 to_io` → `write` →
  `outfile.flush()`), `Failed: Timeout (>150.0s)`, cascading into `worker_internal_error`/`AssertionError` in
  `dsession.py`, `##[error]QG selector 'tests' FAILED (leg=tests, exit=1)` at `22:30:36Z`. A subsequent retry pass in
  the same job logged `1133 passed, 2 warnings in 277.79s` with no failures — consistent with the scheduling-artifact
  theory (the same suite content, re-run, passed clean). Confirmed root facts before concluding: PR #1049
  `state=MERGED`, `mergedAt=2026-07-31T22:16:09Z` — 3 minutes BEFORE the failing run's TESTS phase even started
  (`22:19:01Z` setup, `22:26:48Z` first test collection) — self-merged via an independent already-green check on the
  same head SHA, identical self-merge race to every prior entry in this doc.
  `git merge-base --is-ancestor 111692134aa3 origin/live-defi-rollout` confirmed true. Went further than the
  immediately-preceding two entries: the standard 15-min promotion cycle had already produced and MERGED the _next_
  promotion PR too (`#1050`, `promote/instruments-service/b0282cb1f0cf`, `mergedAt=23:00:04Z`), main-backmerge-to-ldr
  and Semver Agent both `success` on that push — i.e. the pipeline demonstrably kept advancing past this wall without
  any intervention. Zero open PRs (`gh pr list --state open` empty) and zero open `/api/repo-blockers` entries for
  instruments-service at investigation time. Same "orphaned noise against an already-resolved wall" conclusion as every
  prior entry in this doc — no live-defi-rollout code or test change made or needed. Slot left clean
  (instruments-service + unified-trading-pm both already on `live-defi-rollout`, 0 commits ahead of `origin`, nothing to
  commit).
- **2026-08-01 (cicd escalation `agt-8ac0d7`, slot 2)**: features-service `ldr_qg_failure` (no PR — direct push gate), 4
  consecutive `QG slice (tests)` failures across 2 SHAs on `tests/delta_one/unit/test_cross_timeframe_sanity.py`, ~8 min
  wall-clock timeout inside synchronous `pandas` code (no awaited timer — see todo 7 for the full mechanism + evidence,
  including live host contention corroboration: `load average 30.43`, 13 concurrent `quality-gates.sh` processes, 16Gi
  swap in use). Isolated local re-run of the entire failing test file: 8.98s, nothing over 0.63s. No code/test defect —
  both sides read clean. features-service's own `live-defi-rollout` HEAD (`d8d6b63d`) already has zero diff vs the
  failing SHAs and a fresh `quality-gates-v2` run already queued (30+ min, no self-hosted-runner pickup at investigation
  time — the runner-capacity crisis itself, not something this escalation can push a fix for). Did not force a
  speculative timeout bump beyond the already-raised 150s budget (todo 3 showed that game is whack-a-mole, not a fix)
  and did not touch features-service's tree (nothing to commit — QG is genuinely green on the merits). Filed as new todo
  7 (first non-async-timer instance) rather than reusing an existing todo, per this doc's own "each root-cause gets its
  own todo" convention. No further action from this escalation; pinged the authoring slot with the outcome and exited
  per the one-shot `cicd` role's bounded scope (fleet-wide runner capacity is
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s P0, not this wall-clearer's).
- **2026-08-01 ~00:15Z (cicd escalation `agt-6fd2a1`, slot 10)**: same underlying wall as the entry directly above, the
  promotion-PR variant — features-service PR #921 (LDR→main, "Option-B direct"), failing run `30668552631` (head SHA
  `8aa3796b`, same commit family). `QG slice (tests)` failed on the identical
  `tests/delta_one/unit/test_cross_timeframe_sanity.py::test_output_index_matches_input` pytest-timeout thread-dump,
  hung inside `_add_lagged_features`'s pandas boolean-column-mask indexing (`take_nd` → `return out`);
  `QG slice (checks)` separately failed on `Type check FAILED/timeout (exit=124)` (basedpyright hit the full 120s
  `PYRIGHT_TIMEOUT` — same signature class as the #918 entry earlier in this doc). Reproduced locally end-to-end on
  current LDR HEAD (`d8d6b63d`, contains PR #921's head as an ancestor): ran the full `bash scripts/quality-gates.sh`
  backgrounded — `test_cross_timeframe_sanity.py` passed all 35 cases cleanly (dots + skips, no hang) well before the
  run later got caught by the SAME host contention this doc documents (the tee'd log truncated mid-stream around 99%
  with no final summary, consistent with a `qg-governor-watchdog` RAM-pressure SIGTERM or OOM-kill — `free -h` showed
  18Gi/47Gi swap in active use at the time, and `ps aux` showed 5+ other slots' `quality-gates.sh` running concurrently
  on this same shared host). Confirmed root facts: PR #921 `state=MERGED`, `mergedAt=2026-07-31T22:01:08Z` (2s after the
  failing run's own trigger, self-merged via an independent already-green check on the same head SHA — identical race to
  every prior entry in this doc); `live-defi-rollout` HEAD (`d8d6b63d`) has zero diff vs the failing SHA.
  `GET /api/repo-blockers` → `{"open": []}`. LDR's own latest `quality-gates-v2` run (`30673928757`,
  `workflow_dispatch`) was still `queued` 48+ minutes at investigation time with no runner pickup — left alone per this
  doc's established "resolves once host contention clears" precedent (canceling a queued run on an already-saturated
  single-runner pool doesn't help and risks adding load). No code/test change made or needed; no repo push required —
  nothing to add to todo 7 beyond this corroboration (same mechanism, same commit family, now via the promotion-PR path
  instead of the direct-LDR-push path). Slot left clean (features-service 0 commits ahead of `origin/live-defi-rollout`,
  nothing to commit). Pinged the authoring slot with the outcome and exiting per the one-shot `cicd` role's bounded
  scope.
- **2026-08-01 ~00:42Z (cicd escalation `agt-e5401f`, slot 13)**: 1st confirmed instance in a NEW repo
  (client-reporting-api). `ldr_qg_failure` (no PR — direct `live-defi-rollout` push gate), failing run `30669712681`
  (`workflow_dispatch`, started `22:22:01Z`, head SHA `e02d2f520900fb3d75625a2af6f7e3756f9eb778` — a
  `chore(deps): refresh base-image digest pin` bot commit, zero application/test code touched). `QG slice (tests)` job:
  `FAILED tests/unit/test_attribution_routes.py::TestGetNav::test_internal_admin_can_read_any_client - Failed: Timeout (>150.0s) from pytest-timeout.`
  — `1 failed, 664 passed, 4 skipped` in `1107.73s` (0:18:27). Read the test (hits `GET /nav` as an internal-admin
  caller) and its route handler (`client_reporting_api/api/routes/attribution.py::get_client_nav`) — the real-I/O branch
  (`read_attribution_rows` → real GCS `list_blobs`/`download_bytes`) is gated behind `_cloud_cfg.is_mock_mode()`, which
  QG's `base-service.sh` forces true workspace-wide (`export CLOUD_MOCK_MODE="true"`) before pytest starts — no
  plausible real-network path for this specific test; matches this doc's established "legitimately fast, blown out by
  scheduling" profile. Did not attempt an isolated local re-run (unlike most prior entries) — this slot's own host
  measured `load average: 30.82` (16-32 vCPU class box), `21Gi/47Gi` swap in active use, and 13 concurrent
  `quality-gates.sh --no-fix` processes (`pgrep -af`) at investigation time, i.e. the identical fleet-wide capacity
  crisis snapshot this doc's todo 7 and several other entries already captured — spinning up even a single-file venv
  repro would add to, not diagnose past, that same contention, and the log evidence alone (isolated single failure among
  664 passes, zero real-I/O path, unrelated triggering commit) already meets this doc's evidentiary bar. Confirmed root
  facts: `git merge-base --is-ancestor e02d2f52 origin/live-defi-rollout` true, current LDR HEAD (`12702a2`) is 5
  commits ahead with zero code/test diff (2 promote/backmerge commits + 1 further digest-pin refresh);
  `GET /api/repo-blockers` → `{"open": []}` for client-reporting-api. The self-hosted runner (`glue-ip-172-31-5-118-1` —
  same runner name confirmed in this doc's market-tick-data-service and unified-api-contracts entries above, i.e. the
  same shared box) was `busy=true` (`gh api .../actions/runners`) with a fresh `workflow_dispatch` run at current HEAD
  (`30672687292`) already queued 1h16m+ with no pickup (`content sentinel` job succeeded — no matching green marker, so
  slices must actually run) at investigation time — left alone per this doc's established precedent (a queued run on an
  already-saturated single-runner pool resolves once the backlog clears; canceling/retriggering adds load, not signal).
  No code/test change made or needed — same "orphaned noise / known flake class, tree not actually broken" conclusion as
  every prior entry in this doc. Slot left clean (client-reporting-api already on `live-defi-rollout`, 0 commits ahead
  of `origin`, nothing to commit there). Pinged the authoring slot with the outcome and exiting per the one-shot `cicd`
  role's bounded scope.
- **2026-08-01 ~00:49Z (cicd redispatch of the SAME escalation id `agt-719421`, slot 7, re-triaging PR #1049)**: the
  `agt-719421`/slot-7 entry above (2026-07-31 ~23:05Z) already root-caused this exact wall; this redispatch
  independently re-verified from scratch rather than trusting it blind (the prior run evidently didn't reach `/done`).
  Confirmed unchanged: PR #1049 `state=MERGED`, `mergedAt=2026-07-31T22:16:09Z`;
  `git merge-base --is-ancestor 111692134aa3 origin/live-defi-rollout` true. Went further than the prior entry: current
  LDR HEAD (`d2c73500`) is now **15 commits** ahead of the failing SHA, all real feature/fix work (DeFi adapter routing,
  prediction Kalshi category fixes, catalogue retry hardening, LST/vault venue registration, etc.) — the pipeline has
  kept advancing substantially, not just ticked forward by promote/backmerge noise. Zero open PRs
  (`gh pr list --state open` empty), zero open `/api/repo-blockers` entries. Latest LDR `quality-gates-v2` run
  (`30675771282`, `workflow_dispatch`) was still queued 17+min with no runner pickup at investigation time; did not
  force a repro or retrigger — this slot's own host measured `load average: 31.20/30.94/30.75`, `22Gi/47Gi` swap in
  active use, and 17 concurrent `quality-gates.sh` processes (`pgrep -af`), the identical fleet-wide capacity-crisis
  snapshot this doc's todo 7 and several entries above already captured — a local repro would only add to that
  contention for no new signal given the log + merge evidence already meets this doc's evidentiary bar. Same "orphaned
  noise against an already-resolved wall" conclusion, now with stronger evidence (15 substantive commits, not 2
  mechanical ones). No live-defi-rollout code or test change made or needed. Slot left clean (instruments-service +
  unified-trading-pm both on `live-defi-rollout`, 0 commits ahead of `origin` besides this doc edit). Pinged the
  authoring slot with the outcome and exiting per the one-shot `cicd` role's bounded scope.
- **2026-08-01 ~02:15Z (cicd redispatch of the SAME escalation id `agt-6fd2a1`, slot 5, re-triaging PR #921)**: the
  `agt-6fd2a1`/slot-10 entry above (2026-08-01 ~00:15Z) already root-caused this exact wall (features-service PR #921,
  run `30668552631`, head SHA `8aa3796b`); this redispatch independently re-verified from scratch rather than trusting
  it blind (the prior run evidently didn't reach `/done` either). Confirmed unchanged: PR #921 `state=MERGED`,
  `mergedAt=2026-07-31T22:01:08Z` — over an hour BEFORE the failing `pull_request`-triggered run even started
  (`23:30:17Z`), i.e. the run was investigating an already-superseded state from the moment it began. Zero open PRs,
  zero open `/api/repo-blockers` entries for features-service. Went further than the prior entry on the diagnostic side:
  rather than relying on the prior pass's full-`quality-gates.sh` repro (which itself got caught mid-run by the same
  host contention this doc tracks, per its own account), ran two independent SCOPED diagnostics at an even newer HEAD
  (`a0d4e6e4`, 8 commits ahead of the failing SHA — 2 real onchain/defi fixes + 6 mechanical dep/promote/backmerge
  commits, zero touching `delta_one`/`features_service` core code or tests): (1)
  `pytest tests/delta_one/unit/test_cross_timeframe_sanity.py --timeout=20 --durations=20` — **102 passed, 17 skipped in
  8.76s**, slowest single case 0.56s, matching the prior pass's 8.98s finding almost exactly at a materially newer HEAD;
  (2) `basedpyright features_service` — **42.1s wall-clock** (964 pre-existing, already-tolerated `reportAny`/
  `reportUnknown*` warnings via the QG's own Any/Unknown-baseline mechanism, not new errors), comfortably under the 120s
  `PYRIGHT_TIMEOUT` that the CI run's `checks` leg hit at exit=124. Also started a full backgrounded
  `quality-gates.sh --no-fix` run for a third data point; stopped it myself (exact-PID `kill`, my own spawned PGID, no
  name-pattern pkill) at 16% progress with zero failures observed once the two scoped diagnostics already answered the
  only question that mattered (is there a code defect — no) and continuing would only have added a single-threaded
  (`-n 0`, no xdist) full suite's worth of load to an already-elevated host (`load average: 21.88/22.15/22.72` on 16
  vCPUs, 16Gi/47Gi swap in use, 1 sibling `quality-gates.sh` already running) for strictly less marginal signal than the
  targeted checks already gave — the same judgment call several entries above this one made explicitly. Same "orphaned
  noise against an already-resolved wall" conclusion, now corroborated a second time for this exact escalation with
  fresher evidence (newer HEAD, both failing components independently re-timed). No live-defi-rollout code or test
  change made or needed. Slot left clean (features-service already on `live-defi-rollout`, 0 commits ahead of `origin`
  besides this doc edit). Pinged the authoring slot with the outcome and exiting per the one-shot `cicd` role's bounded
  scope.
- **2026-08-01 ~02:25Z (cicd escalation `agt-2f35f6`, slot 9, re-triaging PR #922)**: 3rd independent redispatch of the
  SAME underlying wall the two entries directly above already root-caused (features-service,
  `test_cross_timeframe_sanity.py` family) — this time for promotion PR #922 (also `mergedAt=2026-07-31T23:28:20Z`, same
  self-merge race), failing run `30672970501` at head SHA `2532428d`. `QG slice (checks)`:
  `Type check FAILED/timeout (exit=124)` — identical signature to the `agt-6fd2a1` entry above. `QG slice (tests)`: same
  test/mechanism. Confirmed `live-defi-rollout` HEAD (`a0d4e6e4`) is the EXACT SAME HEAD the `agt-6fd2a1`/slot-5 entry
  above already scoped-diagnosed clean (8.76s test-file re-run, 42.1s basedpyright, both well under budget) — did not
  repeat that repro, no new HEAD to re-verify. New information this pass: (1) pulled `GET /repos/{repo}/actions/runners`
  directly — confirms exactly ONE registered runner for this repo (`glue-ip-172-31-5-118-1`, `busy` toggles true/false,
  never a 2nd registration), and per-job `started_at`/`completed_at` timestamps for both this run and the next LDR retry
  (`30673928757`) show the `checks`/ `tests` jobs running strictly SEQUENTIALLY on it (never overlapping) — ruling out
  same-run job-vs-job contention on one box as the direct mechanism; the slowdown is either queue-depth (one run's jobs
  waiting on a DIFFERENT run's jobs to finish) or in-job resource pressure from something outside GH Actions' own job
  scheduling (leaked child/zombie processes from a prior SIGALRM/SIGKILL-interrupted xdist run — `base-service.sh`
  already carries defensive "kill zombie basedpyright" logic, consistent with this having been anticipated). (2) The 5
  consecutive `workflow_dispatch` LDR failures since 13:36Z yesterday show job durations climbing monotonically across
  the day — `30m58s → 57m12s → 1h11m58s → 1h41m36s → 1h54m28s` — and the `30673928757` run specifically had a **1h21m
  gap** between `content sentinel` finishing (`23:50:01Z`) and `QG slice (tests)` actually starting (`01:11:51Z`), i.e.
  pure queue wait, not test execution time. Both observations are new, concrete evidence for a _worsening-over-the-day_
  backlog on this repo's one dedicated runner, not independent random flakes — worth the fleet-capacity doc's attention
  if it isn't already tracking per-runner queue depth. Zero open `/api/repo-blockers` for features-service. Retriggered
  a fresh `workflow_dispatch` (`30680074425`, picked up immediately — runner was idle at trigger time) rather than wait
  synchronously on a run that has historically taken 30min-2h; not holding the slot for it per this doc's own
  established precedent (queued/running CI is left to resolve on its own, monitored asynchronously, not babysat inline).
  No live-defi-rollout code or test change made or needed. Slot left clean (features-service already on
  `live-defi-rollout`, 0 commits ahead of `origin` besides this doc edit). Pinging the authoring slot with the outcome
  and exiting per the one-shot `cicd` role's bounded scope.
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
