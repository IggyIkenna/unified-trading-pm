---
doc_type: issue
title: "quality-gates.sh's TESTS phase never runs scripts/quality_gates/test_*.py — checker self-tests are dead weight"
summary: >
  pyproject.toml's `[tool.pytest.ini_options] testpaths = ["tests"]` means `bash scripts/quality-gates.sh`'s TESTS phase
  only collects tests under `tests/` — it never executes the unit tests that already live next to several QG checker
  scripts (e.g. `scripts/quality_gates/test_check_no_empty_string_fallback.py`, 17 tests, verified passing only via a
  manual `pytest` invocation while shipping the git-diff-detection fix for that checker). Pre-existing, not introduced
  by this session's work — filed per the findings-triage rule ("pre-existing is not a triage criterion").
status: resolved
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
resolved_by: unified-trading-pm@297695d47 (+ 190636c04) — all 5 todos code-verified 2026-07-16
source: [pyproject.toml, scripts/quality_gates/test_check_no_empty_string_fallback.py]
---

# quality-gates.sh's TESTS phase never runs scripts/quality*gates/test*\*.py

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

- [x] ✅ [SCRIPT] P3. Wire `scripts/quality_gates/test_*.py` (and any other confirmed-passing orphaned test files from
      the audit above) into `quality-gates.sh`'s TESTS phase — either via `testpaths` widening or a dedicated step — so
      checker self-tests actually run on every gate invocation. Scope: the 17 confirmed-clean files above (241 tests)
      only — do NOT include `test_check_banned_placeholder_methods.py` or `test_prediction_pipeline_e2e.py` until their
      own todos below are resolved (wiring them as-is would turn QG red immediately). (repo: unified-trading-pm) —
      **WIRED, slot 13 (infra), 2026-07-14**: plain `testpaths` widening (option 1) does NOT work with this repo's
      invocation — `base-service.sh`'s TESTS phase always passes explicit `${PYTEST_UNIT_DIR}` path args to pytest, and
      pytest CLI paths override `[tool.pytest.ini_options] testpaths`, so testpaths is never consulted regardless of its
      value. Used the documented `PYTEST_UNIT_DIR` per-repo override point instead (space-separated dirs, word-split
      into pytest positional args) in `scripts/quality-gates.sh`:
      `PYTEST_UNIT_DIR="tests/unit/ scripts/quality_gates/ scripts/cicd/ scripts/docs/"`. Scope ended up wider than the
      17-file/241-test floor: by the time this shipped, both blocking todos below (banned-placeholder-methods assertion,
      prediction-e2e rename) were already resolved, so all 18 current orphaned files (254 tests: the 17 + the now-fixed
      `test_check_banned_placeholder_methods.py`, 28/28) are wired — verified collecting + passing together with no
      module-name collisions before wiring
      (`.venv/bin/python -m pytest scripts/quality_gates/ scripts/cicd/     scripts/docs/ -q` → 254 passed). Full
      `bash scripts/quality-gates.sh` green post-wiring: TESTS phase now runs 1247 passed + 8 skipped (was 6,
      `tests/integration/` only) at 72.85% coverage (floor 69%). `unified-trading-pm@297695d47`, PR #1015 (auto-merge
      enabled).
- [x] ✅ [SCRIPT] P3. Fix `test_load_baseline_real_workspace_baseline`'s stale `len(baseline) >= 1` assertion in
      `scripts/quality_gates/test_check_banned_placeholder_methods.py` — the real baseline is correctly empty (ratchet
      fully cleared 2026-05-17 per its own `entries_postscript`); the test should assert the baseline parses cleanly
      (e.g. `isinstance(baseline, dict)`) without requiring non-empty content, or assert `len(baseline) >= 0` as a
      structural sanity check only. (repo: unified-trading-pm) — **FIXED, slot 4 (infra), 2026-07-14**: replaced
      `assert len(baseline) >= 1` with `assert isinstance(baseline, dict)`, matching the todo's own recommended fix
      exactly — the remaining structural assertions (all entries `pending_removal`, 3-tuple keys, non-empty
      `default_successor`) are unaffected and still hold vacuously true on the now-empty dict. 28/28 tests pass (was
      27/28).
- [x] ✅ [SCRIPT] P3. Decide `scripts/prediction/test_prediction_pipeline_e2e.py`'s disposition — it is a manual e2e
      driver script, not a real pytest suite (2 functions take non-fixture args pytest can't inject). Either rename away
      from the `test_*` prefix (so pytest stops trying to collect it as a unit test) or restructure it into a real
      fixture-based suite. Out of scope for todo 2's wiring either way. (repo: unified-trading-pm) — **RENAMED, slot 4
      (infra), 2026-07-14**: `scripts/prediction/test_prediction_pipeline_e2e.py` →
      `scripts/prediction/prediction_pipeline_e2e_check.py` (matches the established `pipeline_e2e_check.py` naming
      already used in instruments-service/market-tick-data-service for the same "manual e2e driver, not a pytest suite"
      pattern). `python_files = ["test_*.py"]` in `pyproject.toml` means the rename alone fully removes it from pytest
      collection — no fixture-restructure needed for a script that legitimately hits live external APIs + writes real
      GCS data by design. Also renamed the 5 internal `test_*` functions to `check_*` (honest naming, no lingering
      `test_`-prefixed callables) and updated the module docstring's usage examples + the 5
      `!**/test_prediction_pipeline_e2e.py` exclusion-glob references in `scripts/quality-gates.sh` (the QG
      empty-string/dict-fallback checker exemptions this manual driver legitimately needs) to the new filename.
- [x] ✅ [DATA] P3. Add a UEFA Champions League entry to `POLYMARKET_SERIES_TO_LEAGUE`
      (`unified_api_contracts/external/polymarket/sports_mappings.py`) — currently has 40+ domestic-league entries but
      zero UCL/Champions-League mapping, so `get_canonical_league_for_polymarket_series("ucl-2025")` (and any other UCL
      series-slug variant Polymarket actually uses — verify the real slug, "ucl-2025" was this audit's test-file
      assumption, not independently confirmed against live Polymarket data) returns `None` instead of a real league ID.
      Discovered via `scripts/prediction/test_prediction_pipeline_e2e.py::test_mappings`'s failing assertion while
      auditing orphaned test files (unrelated task) — a real data-completeness gap, not a test bug. (repo:
      unified-api-contracts) — **FIXED, slot 13 (data_engineering), 2026-07-14**: the canonical `UCL` league_id already
      existed in `LEAGUE_REGISTRY` (`league_data_other.py`, tier=0/Reference) — added both `"champions-league-2025"`
      (follows the established tag+year slug convention already present in `POLYMARKET_SPORTS_TAG_SLUGS`) and
      `"ucl-2025"` (the slug this audit's test assumed) as aliases → `UCL` in `POLYMARKET_SERIES_TO_LEAGUE`, plus 4 new
      unit tests in `tests/unit/test_polymarket_sports_mappings.py`. Full `quality-gates.sh` green.
      `unified-api-contracts@aaa07df4045c7a021b2e79f2329585b7a96b18b7`. Note: NOT added to
      `POLYMARKET_PREDICTION_LEAGUES` (that frozenset's "9 days of Polymarket data" verification claim wasn't
      re-confirmed for UCL — left for a future audit, out of this todo's scope). Also filed
      `quickmerge_agent_already_committed_fastpath_skips_trailer_2026_07_14.md` — the documented `--agent` ship flow
      (commit → QG Pass 1 → quickmerge --agent) hit the local strict-quickmerge pre-push hook because quickmerge's
      already-committed fast path never stamps the `Quickmerge:` trailer; worked around via non-agent quickmerge for
      this ship rather than patching the shared script mid-task.

## Progress Log

**2026-07-14, slot 10 (infra)**: discovered while shipping the git-diff-detection fix for
`check_no_empty_string_fallback.py`. Verified the finding via a real `quality-gates.sh` run
(`unified-trading-pm@dc5ebe3cb`) showing only 6 collected items, all under `tests/integration/`. Filed this doc per the
findings-triage rule rather than silently absorb or ignore. Did not fix — out of this task's scope.

**2026-07-14, slot 10 (infra), todo 1 audit**: ran all 19 orphaned `scripts/**/test_*.py` files directly. 17 fully clean
(241 tests). 2 have real issues (one stale test assertion, one genuine data-mapping gap in a sibling repo) — both
excluded from todo 2's wiring scope and filed as their own todos rather than blocking the audit or silently fixing
out-of-scope repos/files under a P3 audit dispatch.

**2026-07-14, slot 13 (data_engineering), UCL mapping todo**: added `UCL` to `POLYMARKET_SERIES_TO_LEAGUE`
(`unified-api-contracts@aaa07df4`). The canonical `UCL` league_id already existed in `LEAGUE_REGISTRY`
(tier=0/Reference) — this was purely the Polymarket series-slug↔league_id mapping gap. Hit a separate, unrelated tooling
gap while shipping (the `--agent` fast path skipping the `Quickmerge:` trailer stamp) — filed as its own doc rather than
patch the shared `quickmerge.sh` unilaterally mid-task; see
`quickmerge_agent_already_committed_fastpath_skips_trailer_2026_07_14.md`.

**2026-07-14, slot 13 (infra), todo 2 wiring**: confirmed `testpaths` widening (recommended option 1) is a dead end for
this repo — `base-service.sh` always calls pytest with explicit `${PYTEST_UNIT_DIR}` path args, which take precedence
over `[tool.pytest.ini_options] testpaths` in pytest's own resolution order, so touching `pyproject.toml` alone would
have changed nothing (worth flagging back to the "Recommended decision" section above — its option 1 caution undersold
this). Used the `PYTEST_UNIT_DIR` override base-service.sh already documents for exactly this per-repo-layout case.
Spent real effort chasing a false alarm mid-task: the first full `quality-gates.sh` run appeared to only collect 6 tests
post-change, but that was the separate, always-unredirected `PM integration test` sub-step's own terminal output (6
items, `tests/integration/test_pm_scripts_integration.py`) — the actual widened TESTS run succeeds silently on a clean
pass (output only goes to a temp log, `cat`'d to terminal on failure only) and was genuinely green the whole time
(confirmed via temporary debug instrumentation in `base-service.sh`, fully reverted before shipping — `git diff` on that
file is clean). `unified-trading-pm@297695d47`, PR #1015.

## Reconciliation 2026-07-16 — status field was wrong; doc is done

Independently re-verified every todo against code during the AO issue-doc reconciliation sweep (all 5 `- [x]` claims
checked, not trusted): `PYTEST_UNIT_DIR="tests/unit/ scripts/quality_gates/ scripts/cicd/ scripts/docs/"`
(`scripts/quality-gates.sh:23`, `unified-trading-pm@297695d47`); the stale assertion is now
`assert isinstance(baseline, dict)` (`scripts/quality_gates/test_check_banned_placeholder_methods.py:76`); the e2e
driver rename landed (`scripts/prediction/prediction_pipeline_e2e_check.py` exists, `test_prediction_pipeline_e2e.py`
gone, `unified-trading-pm@190636c04`); the UCL mapping is present
(`unified_api_contracts/external/polymarket/sports_mappings.py:153-154`). Live re-run of the wired suite: **255 passed**
(doc claimed 254 — one test added since). Both cited SHAs are real commits.

**The doc was `status: open` with 0 open todos** — a false-open claim, the mirror of the false-resolved class this sweep
exists to catch. Flipped to `resolved` and archived. No code change was needed; the work was already done.
