---
doc_type: issue
title: >-
  strategy-service: a GLOBAL pytest collection hook silently SKIPS every test whose path contains "backtest" when the
  data/ dir is absent — darkening all of tests/unit/engine/backtest/ (runner, benchmark_fills, paper_run) in local AND
  Cloud Build, so a green quality-gates run does NOT mean the paper/benchmark-fill settlement engine was tested
summary: >-
  `strategy-service/tests/e2e/conftest.py::pytest_collection_modifyitems` is a GLOBAL pytest hook — pytest hands a
  `conftest.py` hook the FULL collected item list, not just items under its own directory — and it skips ANY item whose
  path contains the substring "backtest" whenever the `data/` directory is absent. Because `tests/unit/engine/backtest/`
  contains that substring, the ENTIRE unit backtest suite is silently skipped: `test_runner.py` (GroupBRunner),
  `test_benchmark_fills.py`, and the `test_paper_run_*` suites. These cover the deterministic benchmark-fill settlement
  path — i.e. the engine that produces paper/backtest fills and the `paper(W)==batch-rerun(W)` epsilon-0 guarantee. The
  skip is silent (reported only as a skip count), so `quality-gates.sh` exits 0 and CI is green while those tests never
  execute. MEASURED 2026-07-20: adding a new 3-venue paper-proof test under `tests/unit/engine/backtest/` produced 5089
  passed / 356 skipped (the new test SKIPPED — proving nothing); re-homing the identical test to
  `tests/unit/engine/strategies/v2/` produced 5091 passed / 354 skipped (it runs). The +2/-2 delta is exactly that test
  moving from silently-skipped to actually-passing. Discovered while adding the prediction 3-venue paper-arb proof — the
  proof would have been a false green.
status: open
nature: issue
asset_group: [crosscutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [testing, ci-integrity, pytest, silent-skip, backtest, benchmark-fills, false-green]
related: [prediction_consolidated_closeout_2026_07_18.md, prediction_arb_live_execution_bridge_2026_07_20.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: strategy
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  [
    "discovered 2026-07-20 while adding the prediction 3-venue paper-arb proof test (autonomous run); the proof was
    silently skipped by this hook until re-homed, which would have made the 'climbing metric' a false green",
  ]
---

# A global pytest hook is silently darkening the whole unit backtest suite

## The mechanism (why a directory-scoped conftest has global reach)

`pytest_collection_modifyitems` declared in ANY `conftest.py` is invoked once with the **entire** collected item list —
it is NOT scoped to that conftest's directory. `strategy-service/tests/e2e/conftest.py` implements it and skips items by
a **path substring match on "backtest"**, gated on the presence of a `data/` directory. So an e2e-scoped
data-availability guard reaches out and skips unit tests it was never meant to touch.

## Blast radius (what is silently NOT running)

Everything under `tests/unit/engine/backtest/` — the path contains "backtest":

- `test_runner.py` — `GroupBRunner`, the paper/backtest tick runtime.
- `test_benchmark_fills.py` — `BenchmarkFillEngine` / `compute_benchmark_fill` / `_compute_atomic_fill`, the
  deterministic settlement that produces paper fills + P&L.
- `test_paper_run_*` — the paper-run suites.

That is precisely the machinery behind the **batch=live determinism spine** (`paper(W) == batch-rerun(W)`, epsilon 0). A
regression there is currently invisible to `quality-gates.sh` and to Cloud Build.

## Why it matters beyond a skipped test

A green gate is being read as "the paper settlement engine is verified" when those tests did not run. Any new test
placed under that path is a **false green** — which is exactly what happened to the 3-venue paper-arb proof on
2026-07-20 (it asserted a fired instruction + 2 fills, was skipped, and still reported green).

## Fix options (operator-scoped — deliberately NOT auto-applied)

1. **Narrow the hook to its own subtree** (preferred): have the e2e hook only skip items whose path is under
   `tests/e2e/`, e.g. compare against the conftest's own directory rather than a bare `"backtest" in str(item.path)`
   substring test.
2. **Replace path-substring with an explicit marker**: mark the genuinely data-dependent tests
   (`@pytest.mark.requires_data`) and skip on the marker, so the guard is intentional per-test rather than incidental
   per-path.

**Why this was not fixed autonomously:** un-skipping those suites may legitimately RED-en tests that really do need the
absent `data/` fixtures. Turning them back on needs a scoped triage pass (which of the ~N newly-collected tests actually
require data, and how to provide or mark them) — a small plan of its own, not a drive-by edit inside an unrelated
feature run. Doing it blind risks a red gate for every slot on the shared branch.

## Interim mitigation already applied

The 3-venue paper-arb proof was **re-homed** to
`tests/unit/engine/strategies/v2/test_prediction_arb_3venue_paper_proof.py` so it actually executes (verified: it runs
and passes, and drove the passed count 5089 → 5091). No behaviour was changed and the hook was left untouched.
