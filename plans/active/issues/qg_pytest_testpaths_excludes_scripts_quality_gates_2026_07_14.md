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

- [x] ✅ [SCRIPT] P3. Audit `scripts/**/test_*.py` for files outside `tests/` that `testpaths` currently skips; for
      each, confirm it currently passes if run directly. (repo: unified-trading-pm) — **AUDITED, slot 10 (infra),
      2026-07-14.** Found 19 orphaned `test_*.py` files under `scripts/**` (18 under `scripts/quality_gates/` +
      `scripts/quality_gates/tests/`, 1 under `scripts/cicd/`, 1 under `scripts/docs/` ×2, 1 under
      `scripts/prediction/`). Ran each directly via `.venv/bin/python -m pytest <file>`:

  **17/19 files fully clean (241 tests, 0 failures)**: `test_promotion_lag_monitor_etag.py` (20), `test_docspec.py`
  (21), `test_gen_doc_index.py` (3), `test_check_asyncio_manifest_explicit_drain.py` (10),
  `test_check_bar_edge_open_ingestion.py` (9), `test_check_canonical_futures_construction.py` (7),
  `test_check_canonical_model_regressions.py` (11), `test_check_chain_set_inclusion.py` (3),
  `test_check_imports_inside_functions.py` (18), `test_check_inline_bucket_uri.py` (16),
  `test_check_manifest_writer_missing_write_before_return.py` (13), `test_check_mdps_bar_available_at_stamping.py` (13),
  `test_check_no_empty_string_fallback.py` (17, incl. this session's own 9 new ones),
  `test_check_pipeline_mode_explicit_at_record_calls.py` (11), `test_check_removed_symbols.py` (18),
  `test_detect_template_drift.py` (21), `tests/test_check_mdps_bar_boundary_compliance.py` (12).

  **2/19 files have real issues — excluded from todo 2's wiring scope, filed as their own todos below:**
  - `scripts/quality_gates/test_check_banned_placeholder_methods.py`: 27/28 pass; ONE failure —
    `test_load_baseline_real_workspace_baseline` asserts `len(baseline) >= 1`, but
    `banned_placeholder_methods_baseline.yaml` is now **legitimately empty** (its own `entries_postscript` field
    confirms: "all originally-baselined banned-placeholder occurrences fully removed 2026-05-17. New occurrences will
    fail CI."). The baseline is correct; the test's assertion is stale from before the ratchet fully cleared.
  - `scripts/prediction/test_prediction_pipeline_e2e.py`: not a real pytest suite — functions take non-fixture
    parameters (`condition_ids`, `instruments`) meant to be threaded by a manual driver, so pytest's fixture injection
    fails on 2 of them (`ERROR ... fixture 'condition_ids' not found`). Of the 3 that DO run standalone:
    `test_urdi_instruments` fails with `ModuleNotFoundError: No module named 'instruments_service'` (cross-repo import,
    needs a different PYTHONPATH context than a bare PM checkout) and `test_mappings` fails a real assertion —
    `get_canonical_league_for_polymarket_series("ucl-2025")` returns `None`, not `"UCL"`. Traced this to
    `unified-api-contracts/unified_api_contracts/external/polymarket/sports_mappings.py`'s `POLYMARKET_SERIES_TO_LEAGUE`
    dict: it has 40+ domestic-league entries but **zero** UEFA Champions League/UCL entry at all — a genuine
    data-completeness gap (Champions League is a major, high-volume Polymarket market), not a stale test. Filed as its
    own data-craft todo below rather than fixed here (out of infra-craft/this-repo scope; needs
    `unified-api-contracts`).

- [ ] [SCRIPT] P3. Wire `scripts/quality_gates/test_*.py` (and any other confirmed-passing orphaned test files from the
      audit above) into `quality-gates.sh`'s TESTS phase — either via `testpaths` widening or a dedicated step — so
      checker self-tests actually run on every gate invocation. Scope: the 17 confirmed-clean files above (241 tests)
      only — do NOT include `test_check_banned_placeholder_methods.py` or `test_prediction_pipeline_e2e.py` until their
      own todos below are resolved (wiring them as-is would turn QG red immediately). (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. Fix `test_load_baseline_real_workspace_baseline`'s stale `len(baseline) >= 1` assertion in
      `scripts/quality_gates/test_check_banned_placeholder_methods.py` — the real baseline is correctly empty (ratchet
      fully cleared 2026-05-17 per its own `entries_postscript`); the test should assert the baseline parses cleanly
      (e.g. `isinstance(baseline, dict)`) without requiring non-empty content, or assert `len(baseline) >= 0` as a
      structural sanity check only. (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. Decide `scripts/prediction/test_prediction_pipeline_e2e.py`'s disposition — it is a manual e2e driver
      script, not a real pytest suite (2 functions take non-fixture args pytest can't inject). Either rename away from
      the `test_*` prefix (so pytest stops trying to collect it as a unit test) or restructure it into a real
      fixture-based suite. Out of scope for todo 2's wiring either way. (repo: unified-trading-pm)
- [ ] [DATA] P3. Add a UEFA Champions League entry to `POLYMARKET_SERIES_TO_LEAGUE`
      (`unified_api_contracts/external/polymarket/sports_mappings.py`) — currently has 40+ domestic-league entries but
      zero UCL/Champions-League mapping, so `get_canonical_league_for_polymarket_series("ucl-2025")` (and any other UCL
      series-slug variant Polymarket actually uses — verify the real slug, "ucl-2025" was this audit's test-file
      assumption, not independently confirmed against live Polymarket data) returns `None` instead of a real league ID.
      Discovered via `scripts/prediction/test_prediction_pipeline_e2e.py::test_mappings`'s failing assertion while
      auditing orphaned test files (unrelated task) — a real data-completeness gap, not a test bug. (repo:
      unified-api-contracts)

## Progress Log

**2026-07-14, slot 10 (infra)**: discovered while shipping the git-diff-detection fix for
`check_no_empty_string_fallback.py`. Verified the finding via a real `quality-gates.sh` run
(`unified-trading-pm@dc5ebe3cb`) showing only 6 collected items, all under `tests/integration/`. Filed this doc per the
findings-triage rule rather than silently absorb or ignore. Did not fix — out of this task's scope.

**2026-07-14, slot 10 (infra), todo 1 audit**: ran all 19 orphaned `scripts/**/test_*.py` files directly. 17 fully clean
(241 tests). 2 have real issues (one stale test assertion, one genuine data-mapping gap in a sibling repo) — both
excluded from todo 2's wiring scope and filed as their own todos rather than blocking the audit or silently fixing
out-of-scope repos/files under a P3 audit dispatch.
