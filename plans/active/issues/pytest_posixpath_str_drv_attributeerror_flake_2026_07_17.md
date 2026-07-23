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
status: open
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
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
last_updated: 2026-07-17
drift_direction: advance-code
depends_on: []
---

# pytest PosixPath `_str`/`_drv` AttributeError flake — cross-repo, cross-agent

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
