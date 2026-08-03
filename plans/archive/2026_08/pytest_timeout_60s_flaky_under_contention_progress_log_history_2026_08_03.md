---
doc_type: issue
title: Global QG pytest-timeout flaky-under-contention — Progress Log history (2026-07-29 through 2026-08-01 ~00:49Z)
summary:
  Line-cap remediation extraction from plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md's
  Progress Log — every corroboration/fix entry from the doc's founding (2026-07-29) through the 2026-08-01 ~00:49Z
  redispatch entry, moved verbatim so the live doc stays under the 1000-line hard cap. Fully superseded by the live
  doc's Todos/Evidence sections; read this only if a deeper citation on a specific historical corroboration entry is
  needed.
status: archived
nature: notes
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist, history, line-cap-remediation]
related: [/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md]
created: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-08-03
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source: [plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md, line-cap remediation 2026-08-03]
assigned_role: project_management
drift_direction: none
---

# Global QG pytest-timeout flaky-under-contention — Progress Log history

> Extracted verbatim 2026-08-03 (line-cap remediation, live doc was at 996/1000 lines) from
> `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md`'s Progress Log. This covers every entry
> from the doc's founding (2026-07-29) through the 2026-08-01 ~00:49Z redispatch entry. The live doc's Progress Log
> continues from the 2026-08-01 ~00:42Z client-reporting-api entry onward (kept in place — extraction boundary was
> chosen to preserve the most recent ~1/3 of corroborations in the live doc).

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
