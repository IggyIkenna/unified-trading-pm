---
doc_type: issue
title: "quality-gates.sh's TESTS phase never runs scripts/quality_gates/test_*.py — checker self-tests are dead weight"
summary: >
  pyproject.toml's `[tool.pytest.ini_options] testpaths = ["tests"]` means `bash scripts/quality-gates.sh`'s TESTS phase
  only collects tests under `tests/` — it never executes the unit tests that already live next to several QG checker
  scripts (e.g. `scripts/quality_gates/test_check_no_empty_string_fallback.py`, 17 tests, verified passing only via a
  manual `pytest` invocation while shipping the git-diff-detection fix for that checker). Pre-existing, not introduced
  by this session's work — filed per the findings-triage rule ("pre-existing is not a triage criterion").
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, pytest, testpaths, tooling-gap]
related: [plans/active/issues/instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md]
created: "2026-07-14"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
source: [pyproject.toml, scripts/quality_gates/test_check_no_empty_string_fallback.py]
---

# quality-gates.sh's TESTS phase never runs scripts/quality_gates/test_*.py

## What I found

While shipping the git-diff-based over-baseline-reporting fix for `check_no_empty_string_fallback.py`
(`instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md` todo 2), I added 9 unit tests to the existing
`scripts/quality_gates/test_check_no_empty_string_fallback.py` (17 total) and verified them directly via
`.venv/bin/python -m pytest scripts/quality_gates/test_check_no_empty_string_fallback.py -q` — 17 passed.

Running the real `bash scripts/quality-gates.sh` afterward, the TESTS phase output showed:

```
collected 6 items
tests/integration/test_pm_scripts_integration.py ......                  [100%]
6 passed in 0.11s
```

Only 6 items, all from `tests/integration/`. `pyproject.toml`'s pytest config is `testpaths = ["tests"]` — the TESTS
phase never looks under `scripts/quality_gates/`, so `test_check_no_empty_string_fallback.py`'s tests (mine and the 8
pre-existing ones) are never actually executed by CI or by any agent's routine `quality-gates.sh` run. They only run if
someone thinks to invoke pytest against that path directly, as I did here.

## Why it matters

Any checker script under `scripts/quality_gates/` that ships its own `test_*.py` file (a real, established convention in
this dir) currently gets **zero** automatic regression coverage from the gate that's supposed to guarantee it. A future
edit to `check_no_empty_string_fallback.py` (or any sibling checker with tests) could break its own test suite silently
— QG would stay green, because the tests that would catch it never run.

## Recommended decision

Two options, not mutually exclusive:

1. Add `"scripts/quality_gates"` (or a narrower `"scripts/quality_gates/test_*.py"` collection root) to `testpaths` in
   `pyproject.toml`. **Caution**: audit first — there may be OTHER `test_*.py` files scattered under `scripts/` (not
   just `quality_gates/`) that have never run and could be currently failing/stale; a blind `testpaths` widening could
   turn QG red fleet-wide on the next run. Scope the audit before flipping the switch.
2. Alternatively, wire a dedicated QG step that explicitly runs `pytest scripts/quality_gates/` (mirroring how other
   checker-adjacent tooling gets its own STEP), keeping the main `tests/` TESTS phase untouched and lower-risk.

Did not implement either option in this dispatch — this is a P2 checker-content fix, not a QG-pipeline-wide change, and
the audit implied by option 1 is out of scope for that task.

## Todos

- [ ] [SCRIPT] P3. Audit `scripts/**/test_*.py` for files outside `tests/` that `testpaths` currently skips; for each,
      confirm it currently passes if run directly. (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. Wire `scripts/quality_gates/test_*.py` (and any other confirmed-passing orphaned test files from the
      audit above) into `quality-gates.sh`'s TESTS phase — either via `testpaths` widening or a dedicated step — so
      checker self-tests actually run on every gate invocation. (repo: unified-trading-pm)

## Progress Log

**2026-07-14, slot 10 (infra)**: discovered while shipping the git-diff-detection fix for
`check_no_empty_string_fallback.py`. Verified the finding via a real `quality-gates.sh` run
(`unified-trading-pm@dc5ebe3cb`) showing only 6 collected items, all under `tests/integration/`. Filed this doc per the
findings-triage rule rather than silently absorb or ignore. Did not fix — out of this task's scope.
