---
doc_type: issue
title:
  "Cross-repo, cross-agent pytest flake: pathlib._local.PosixPath '_str'/'_drv' AttributeError inside
  unified_trading_library.cloud_interface.factory.get_data_sink under xdist-parallel test execution (Python 3.13.9)"
summary: >-
  Independently observed in TWO unrelated concurrent quality-gates.sh runs on 2026-07-16/17 — one against
  instruments-service's cefi instrument_type migration work (this plan's P9 Q2), one against a different concurrent
  agent's instruments-service DeFi work (different checkout, different repo state) — both hit the IDENTICAL
  AttributeError signature (`pathlib._local.PosixPath` object has no attribute `_str` / `_drv`) inside
  unified_trading_library/cloud_interface/factory.py's `get_data_sink`, surfaced via 3 completely unrelated sports/
  reference-data unit tests (test_orchestrator_boost.py::test_teams_and_standings_fetched_and_written,
  test_understat_adapter_coverage.py x2). Neither failing agent's diff touched factory.py, pathlib, or the sports code
  paths involved — this is a pre-existing, environment-level flake (most likely a pytest-xdist worker race on
  shared/cached PosixPath internal state under Python 3.13.9's pathlib._local implementation), not a regression from
  either agent's change. A retry of the SAME quality-gates.sh run (no code changes, same HEAD) on a quieter host passed
  cleanly, consistent with a non-deterministic race rather than a deterministic bug.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [pytest, flake, pathlib, xdist, python-3.13, ci, environment]
related: [/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-17
parent_epic: instruments_master
priority: P3
source:
  "Found as a byproduct of the P9 Q2 CeFi legacy-lowercase instrument_type migration
  (data_status_page_ux_and_canonicalisation_2026_07_16.md) — an unrelated quality-gates.sh run failed on 3
  sports/reference-data unit tests; cross-validated against a second, unrelated concurrent agent's QG log hitting the
  identical signature before concluding it is pre-existing/environment-level rather than a regression from either
  agent's change. Flagged as a follow-up per the workspace's big-finding triage rule, not actioned."
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
  "Reproduced the exact reported AttributeError signature deterministically (byte-for-byte traceback match) by forcing
  pytest-timeout's SIGALRM to interrupt mid-flight via an artificially short --timeout against
  test_orchestrator_boost.py::TestFetchSportsReferenceData::test_teams_and_standings_fetched_and_written; root-caused it
  to that test's missing _write_team_mapping/_write_fixture_mapping mocks (present everywhere else in the codebase, e.g.
  test_orchestrator_sports_pipeline.py) letting a truthy bucket='test-bucket' silently auto-upgrade
  unified_trading_library.get_data_sink's local→gcp backend and cold-import the full google-cloud SDK + resolve real ADC
  credentials — several seconds of genuine I/O that widened the timing window for pytest-timeout's SIGALRM to land
  inside CPython 3.13's pathlib._local lazy _str/_drv slot population. Fixed by adding the missing mocks
  (instruments-service@bc7936a9c75b353bd587b4e2e0d254d207cb7b80, tests/unit/test_orchestrator_boost.py) + a dedicated
  regression test; verified 8/8 clean re-runs at the exact --timeout value that reliably reproduced the bug beforehand.
  See Progress Log below for full reproduction methodology and the residual (unfixable-in-repo) general hazard this does
  NOT close."
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
last_updated: 2026-07-25
drift_direction: advance-code
depends_on: []
---

# pytest PosixPath `_str`/`_drv` AttributeError flake — cross-repo, cross-agent

> **✅ ARCHIVED 2026-07-25 — RESOLVED.** Reproduced deterministically, root-caused, and fixed
> (instruments-service@bc7936a9c75b353bd587b4e2e0d254d207cb7b80) per the Progress Log below; 8/8 clean re-runs at the
> exact `--timeout` value that reliably reproduced the bug beforehand, full `quality-gates.sh --no-fix` green. The
> residual general upstream hazard (CPython 3.13 `pathlib._local` + `pytest-timeout` SIGALRM interaction) is a
> documented, low-probability, unfixed-in-repo risk, not an open action item — monitor for recurrence per the Progress
> Log's closing note.

## Evidence

**Occurrence 1** (this plan's P9 Q2 CeFi migration work, instruments-service, 2026-07-16 ~14:00 UTC-ish local run,
`qg_run3.log`):

```
../pathlib/_local.py:231: in __str__
    return self._str
E   AttributeError: 'pathlib._local.PosixPath' object has no attribute '_str'

During handling of the above exception, another exception occurred:
../pathlib/_local.py:293: in drive
    return self._drv
E   AttributeError: 'pathlib._local.PosixPath' object has no attribute '_drv'

During handling of the above exception, another exception occurred:
tests/unit/test_orchestrator_boost.py:307: in test_teams_and_standings_fetched_and_written
    result = await _fetch_sports_reference_data(
instruments_service/engine/orchestrator/sports_reference.py:217: in _fetch_sports_reference_data
    _orch._write_team_mapping(bucket)
instruments_service/engine/orchestrator/sports_fixtures.py:705: in _write_team_mapping
    mapping_sink = _orch.get_data_sink(bucket=bucket, prefix="sports_reference/mappings")
../unified-trading-library/unified_trading_library/cloud_interface/factory.py:477: in get_data_sink
    sink = _build_data_sink(p, bucket, prefix, routing_key, protocol_config)
```

Full run result: `3 failed, 4384 passed, 3 skipped, 10 warnings in 764.29s` — the 3 failures were
`test_orchestrator_boost.py::TestFetchSportsReferenceData::test_teams_and_standings_fetched_and_written`,
`test_understat_adapter_coverage.py::TestUnderstatFetchErrorTracking::test_get_fixtures_all_leagues_404_sets_error_count_6`,
`test_understat_adapter_coverage.py::TestUnderstatFailedLeagueNameTracking::test_get_fixtures_all_leagues_404_records_all_names`.

**Occurrence 2** (a DIFFERENT concurrent agent's `quality-gates.sh` run, same 2026-07-16 window, logged to
`/tmp/qg_is_defi.log` — a separate instruments-service checkout working the sibling DeFi data_type migration, wholly
unrelated diff): the IDENTICAL `pathlib._local.py` `_str`/`_drv` `AttributeError` signature appears at the same source
lines.

**Retry**: re-running the exact same `quality-gates.sh --no-fix` at the same HEAD commit (`6f87a251`, no code changes)
on a quieter host (0 concurrent quality-gates.sh processes) passed cleanly — all tests green, sentinel written. This is
consistent with a non-deterministic race (most likely pytest-xdist worker parallelism, `gw0` in the traceback) rather
than a deterministic logic bug.

## Why this is worth tracking

- Both occurrences are cross-validated as **pre-existing and environment-level** — neither agent's diff touched
  `unified_trading_library/cloud_interface/factory.py`, `pathlib`, or the sports/reference-data code paths where it
  surfaced (`sports_reference.py`, `sports_fixtures.py`, `understat` adapter).
- It burns real agent time (both agents independently had to diagnose "is this my fault?" before concluding no) and,
  worse, **blocks the quickmerge two-pass sentinel gate** (`quality-gates.sh` must exit 0 to write
  `.qg_last_passed_sha`) — an unrelated flaky test failure fully blocks shipping unrelated, correct code until a lucky
  retry.
- Root cause is very likely a **pytest-xdist parallel-worker race** touching cached/shared internal state on a
  `PosixPath` instance under CPython 3.13.9's newer `pathlib._local` implementation (the `_str`/`_drv` private
  attributes are lazily-computed caches — a classic shape for a race if two workers construct/mutate the same
  interned/shared `Path`-like object concurrently). Not diagnosed further here — out of scope for the CeFi
  instrument_type migration this finding was found during.

## Suggested next step (not actioned by this issue doc)

Someone with bandwidth should: (a) try to reproduce deterministically (e.g. `pytest -n auto` repeated N times against
just the 3 affected tests, or the sports_reference/understat modules) to confirm the xdist-race hypothesis; (b) check
whether `unified_trading_library.cloud_interface.factory.get_data_sink` (or something it calls) holds a
class-level/module-level cached `Path` object that isn't safe under xdist's process-pool parallelism; (c) if confirmed,
either make the cache worker-local or pin affected tests off `-n auto` (`@pytest.mark.no_parallel`-style, if the
workspace has such a marker).

## Status

Not actioned — flagged per the workspace's "big finding" triage rule (cross-repo, affects CI reliability workspace-wide)
during the P9 Q2 CeFi legacy-lowercase `instrument_type` migration
(`data_status_page_ux_and_canonicalisation_2026_07_16.md`). No fix attempted; both affected quality-gates.sh runs this
issue documents already have a PASSING retry on record, so nothing is currently blocked.

## Progress Log — 2026-07-25 (repro + root-cause + fix)

**Repro attempts, in order:**

1. Ran the exact QG invocation
   (`pytest tests/unit/ --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket -n 2 --timeout=60 -q -r a --tb=short --no-header`,
   matching `base-service.sh`'s `PARGS`) 3× full-suite, sequentially — 4903 passed / 7 skipped each time, ~52-65s. No
   repro (consistent with the doc's own note that a quiet retry passes cleanly — the race needs specific timing, not
   just xdist parallelism per se).
2. Ran just the 3 named failing tests under `-n 2` repeated 15× — no repro (too few tests per worker for the real
   trigger, identified in step 4, to fire; see root cause).
3. Investigated `unified_trading_library/cloud_interface/factory.py` — `get_data_sink(bucket=..., ...)` auto-upgrades
   `local`→`gcp` when `bucket` is truthy (`_build_data_sink`, existing/intentional behavior, not itself a bug).
   `instruments-service`'s `sports_fixtures.py::_write_team_mapping`/`_write_fixture_mapping` call it unconditionally
   with a **real** `bucket="test-bucket"` from inside `test_orchestrator_boost.py::TestFetchSportsReferenceData`'s 3
   tests — none of which mock `_write_team_mapping`/`_write_fixture_mapping` (unlike EVERY call site in
   `test_orchestrator_sports_pipeline.py`, which consistently mocks both). Confirmed empirically: calling
   `get_data_sink(bucket="test-bucket", ...)` directly constructs a REAL `GCSStorageClient` (cold-imports the full
   google-cloud SDK: bigquery/logging/compute_v1/storage + `google.auth.default()` ADC resolution) — **3.3s** of genuine
   I/O on first call in a process, not mocked, not gated by any test marker.
4. **Deterministic repro achieved**: ran `test_teams_and_standings_fetched_and_written` alone with an artificially short
   `--timeout=N` (no `-n`, single process) to force pytest-timeout's SIGALRM to land inside that 3.3s window. At
   `--timeout=1` and `--timeout=4`, repeatedly got the **exact reported signature, byte-for-byte**:
   `pathlib/_local.py:231: in __str__ → AttributeError: ... '_str'` → "During handling..." →
   `pathlib/_local.py:293: in drive → AttributeError: ... '_drv'` → "During handling..." → the test call chain down
   through `sports_fixtures.py:770: get_data_sink` → `factory.py:477: _build_data_sink` → `get_storage_client` → the
   lazy `from .providers.gcp import GCSStorageClient` cold-import. Confirmed root cause reads straight off CPython
   3.13's `pathlib/_local.py`: `PurePath.__str__` (line 227-235) and `.drive` (line 289-296) are lazy `__slots__` caches
   populated via a bare `try: return self._str / except AttributeError: self._str = ...` — NOT signal-safe. A SIGALRM
   landing between the `try` and the assignment (inside the multi-second cold-import's own internal `Path` construction,
   e.g. `importlib.metadata`/namespace-package discovery touching unrelated installed packages' files — one repro hit a
   `PosixPath` pointing at a bundled `pandas/tests/.../conftest.py`) leaves that `_str`/`_drv` slot **permanently
   unset**; ANY later `str()`/`.drive` access on the same (process-cached) object re-triggers the identical chained
   AttributeError — explaining why unrelated later tests in the same worker (the 2 understat tests in the original
   evidence) tripped over it as pure collateral, without needing their own separate reproduction.
5. **Fix shipped** — `instruments-service@bc7936a9c75b353bd587b4e2e0d254d207cb7b80`
   (`tests/unit/test_orchestrator_boost.py`): added the missing `_write_team_mapping`/`_write_fixture_mapping` mocks to
   all 3 `TestFetchSportsReferenceData` call sites (matching the established pattern already used consistently in
   `test_orchestrator_sports_pipeline.py`), closing the multi- second unmocked real-I/O window. Added a new regression
   test, `test_teams_and_standings_never_reaches_real_data_sink`, that patches `get_data_sink`/`get_storage_client` with
   plain `MagicMock`s and asserts `.assert_not_called()` **after** the call — verified experimentally that a
   raising-`side_effect` tripwire is NOT sufficient here (`_write_team_mapping`/`_write_fixture_mapping` wrap their body
   in a broad `except Exception: classify_and_emit_error(...)` that silently swallows a raised tripwire, so the test
   would falsely pass) whereas post-hoc `assert_not_called()` has no such blind spot.
6. **Verified the fix closes the confirmed trigger**: re-ran the exact repro sweep from step 4 against the fixed test at
   `--timeout` values from 0.05s up to 4s — 8/8 clean at the exact `--timeout=1` value that reliably reproduced the
   AttributeError before the fix (now completes in ~0.83s, well under any of these timeouts, so the race window is
   closed for this specific call site). Full `tests/unit/test_orchestrator_boost.py` +
   `tests/unit/test_understat_adapter_coverage.py` under `-n 2 --timeout=60` (the real QG config): 74 passed. Full
   `quality-gates.sh --no-fix`: `ALL QUALITY GATES PASSED (111s)`.

**What this does NOT close (honest residual)**: the underlying CPython 3.13 `pathlib._local` + `pytest-timeout` SIGALRM
interaction is a genuine upstream hazard, not something any in-repo code change fully eliminates — ANY sufficiently slow
test anywhere in this dependency stack that happens to be lazily constructing/stringifying a `Path` when a signal-based
test timeout fires is theoretically exposed, at very low/rare probability (needs a slow-enough operation + host
contention pushing a test close to its timeout ceiling, as in the original doc's "concurrent agent" occurrence). The
only real upstream-level mitigations are (a) `--timeout-method=thread` instead of the default `signal` (pytest-timeout
`.venv/lib/python3.13/site-packages/pytest_timeout.py`) — but this changes failure semantics workspace-wide (a timeout
hard-kills the whole xdist worker via `os._exit(1)` + stack dump, instead of failing just the one test), which is a
bigger CI-behavior call than this P3 finding's scope, so it is NOT actioned here — flagging for an explicit operator
decision if this class of flake recurs elsewhere; or (b) upgrading past whatever CPython 3.13.x patch release (if any)
hardens `pathlib._local`'s lazy-cache population against async interrupts. Recommend: monitor for recurrence; if it
resurfaces in a DIFFERENT, already-mock-clean test (i.e. not another instance of "a unit test accidentally doing real
I/O"), that would indicate the general hazard is live at a meaningfully higher rate than observed here and would justify
escalating the `--timeout-method` question to the operator.

**Closing this issue** as resolved for the concrete, reproduced instance (root-caused + fixed + regression-tested); the
residual general hazard above is deliberately left as a documented, low-probability, unfixed-in-repo risk rather than a
fresh action item, per the honest-repro-reporting instruction for this task.
