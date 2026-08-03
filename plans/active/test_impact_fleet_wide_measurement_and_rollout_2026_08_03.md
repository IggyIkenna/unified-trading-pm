---
doc_type: plan
title: Test-impact / selective execution — fleet-wide eligibility measurement, then staged rollout
summary: >-
  Extends a 4-repo commit-classification sample (execution-service, features-service, instruments-service,
  market-data-processing-service) to all ~23 Python fleet repos, to turn the selective-test-execution design's savings
  estimate from a guess into a real, per-repo measured number — then stages the design's own already-scoped
  implementation rollout (walker, allowlists, golden-set tests, single-repo shadow trial, fleet trial, promotion) —
  design REVIEWED AND APPROVED by the operator 2026-08-03, so both phases are now unblocked (dispatch timing is still a
  separate operator action, post-`/pre-compact`). Every todo across both phases has a real dependency on its predecessor
  (`sequential: true`).
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, execution-service, features-service, instruments-service, market-data-processing-service]
scope: [engineer]
tags: [ci-cd, testing, pytest, selective-execution, test-impact-analysis, cost, measurement]
related:
  [
    /plans/active/issues/test_impact_selective_execution_design_2026_08_03.md,
    /plans/active/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
sequential: true
depends_on: []
source:
  "Interactive session: after publishing the selective-test-execution design doc, the operator asked for a rough
  minutes-saved estimate; a 4-repo commit sample was run live to ground it instead of guessing. Operator then asked to
  extend that sample to the full fleet and track it as a human plan, to be dispatched (assigned_vm flipped to planning)
  after a session /pre-compact checkpoint."
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Test-impact / selective execution — fleet-wide eligibility measurement, then staged rollout

## Why this plan exists

`test_impact_selective_execution_design_2026_08_03.md` designed a conservative, escape-hatch-heavy selector for running
only the pytest files a diff can plausibly affect. Its own follow-up gates all implementation on an operator review.
Before that review, the operator asked how many minutes this would actually save — the honest answer needed real data,
not an industry-average guess, because this codebase's dynamic-dispatch adapter/family patterns (found live in
`execution-service` and `features-service`) are exactly the kind of thing that defeats a naive estimate.

**A live 4-repo sample (last 50 commits / 30 days each, classified against the design's actual escape-hatch rules)
already found real, repo-specific variance**:

| Repo                             | `.py`-touching commits sampled | Hit the dynamic-dispatch escape hatch | Narrow-eligible |
| -------------------------------- | ------------------------------ | ------------------------------------- | --------------- |
| `execution-service`              | 17                             | 11 (65%)                              | **35%**         |
| `features-service`               | 35                             | 2 (6%)                                | **94%**         |
| `instruments-service`            | 36                             | 5 (14%)                               | **86%**         |
| `market-data-processing-service` | 26                             | 1 (4%)                                | **96%**         |

Blended against a ~9 min baseline `QG slice (tests)` leg (measured earlier on `features-service`) and an assumed 20-40%
narrowed-runtime reduction (industry-typical, NOT measured here), this gave a rough **~4-6 min/run saved on the three
high-eligibility repos, ~2-3 min/run on `execution-service`** — directionally useful, but only 4 of ~23 Python repos
were sampled, and the dynamic-dispatch classifier was a rough regex proxy, not a verified allowlist. This plan closes
both gaps before anyone trusts the number for a real rollout decision.

## Phase 1 — Fleet-wide measurement (COMPLETE 2026-08-03)

- [x] ✅ [SCRIPT] P1. **Extend the commit-classification sample to every remaining Python fleet repo.** Done — see the
      full 22-repo table below and the Progress Log entry for methodology + per-repo commit SHAs.
- [x] ✅ [SCRIPT] P1. **Turn the full 22-repo table into a real fleet-wide minutes-saved estimate.** Done — see
      "Fleet-wide estimate" below, MEASURED vs ASSUMED inputs labeled, derivation shown.
- [x] ✅ [SCRIPT] P2. **Replace the regex dynamic-dispatch heuristic with a real, verified allowlist.** Done — see
      "Verified dynamic-dispatch allowlist" below; the eligibility table already reflects the verified numbers, not the
      raw regex proxy.

### Full 22-repo eligibility table (verified allowlist applied)

| Repo                                | `.py`-touching commits sampled | Escape-hatch-hit (verified)               | Narrow-eligible                                                                                                                                | Total commits (30d) |
| ----------------------------------- | ------------------------------ | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `execution-service`                 | 17                             | 6 (35.3%)                                 | **64.7%** (was 35% under raw regex)                                                                                                            | NM                  |
| `features-service`                  | 35                             | 0 (0%)                                    | **100%** (was 94%)                                                                                                                             | NM                  |
| `instruments-service`               | 36                             | 3 (8.3%)                                  | **91.7%** (was 86%)                                                                                                                            | NM                  |
| `market-data-processing-service`    | 28                             | 0 (0%)                                    | **100%** (was 96%)                                                                                                                             | NM                  |
| `unified-api-contracts`             | 32                             | 0 (0%)                                    | 100%                                                                                                                                           | 810                 |
| `unified-trading-library`           | 26                             | 0 (0%)                                    | 100%                                                                                                                                           | 633                 |
| `agent-orchestrator`                | 25                             | 0 (0%)                                    | 100%                                                                                                                                           | 870                 |
| `e2e-testing`                       | 25                             | 2 (8%)                                    | 92%                                                                                                                                            | 233                 |
| `strategy-service`                  | 14                             | 0 (0%)                                    | 100%                                                                                                                                           | 372                 |
| `deployment-api`                    | 18                             | 0 (0%)                                    | **100%** (was 83.3% under raw regex — the 1 flagged file, `deployment_api/main.py`, is a directory-name-suffix coincidence, not real dispatch) | 750                 |
| `deployment-service`                | 11                             | 0 (0%)                                    | 100%                                                                                                                                           | 1168                |
| `ml-service`                        | 8                              | 0 (0%)                                    | 100%                                                                                                                                           | 281                 |
| `unified-trading-api`               | 6                              | 1 (16.7%)                                 | 83.3% (via `pyproject.toml` touch, unrelated to dynamic-dispatch)                                                                              | 96                  |
| `system-integration-tests`          | 4                              | 0 (0%)                                    | 100%                                                                                                                                           | 136                 |
| `batch-live-reconciliation-service` | 2                              | 0 (0%)                                    | 100%                                                                                                                                           | 267                 |
| `trading-agent-service`             | 2                              | 0 (0%)                                    | 100%                                                                                                                                           | 200                 |
| `alerting-service`                  | 0                              | N/A (no `.py`-touching commits in window) | N/A                                                                                                                                            | 295                 |
| `client-reporting-api`              | 0                              | N/A                                       | N/A                                                                                                                                            | 260                 |
| `fund-administration-service`       | 0                              | N/A                                       | N/A                                                                                                                                            | 210                 |
| `greeks-service`                    | 0                              | N/A                                       | N/A                                                                                                                                            | 228                 |
| `ibkr-gateway-infra`                | 0                              | N/A                                       | N/A                                                                                                                                            | 80                  |
| `unified-trading-pm`                | 0                              | N/A                                       | N/A                                                                                                                                            | 13425               |

**Methodology**: last 50 commits or all commits in the last 30 days (whichever smaller), per repo, classified against 3
escape hatches — conftest.py touch, manifest/config touch (`*manifest*.json/.yaml`, `/config(s)/`, `pyproject.toml`),
verified dynamic-dispatch touch (below). 6 of 22 repos had zero `.py`-touching commits in their sampled window (recent
history dominated by Dockerfile digest bumps, CI YAML, docs/plans churn, or LDR→main promote merges) — narrow-eligible
is undefined (N/A) for these, not 0% or 100%; excluded from the fleet-wide estimate's denominator below. The original
4-repo table and this session's re-verification pass ran at different moments, so "last 30 days" windows differ slightly
(`market-data-processing-service`'s `.py`-touching count moved 26→28) — a known, unavoidable sampling-window drift, not
a methodology error.

### Verified dynamic-dispatch allowlist (replaces the raw regex proxy)

The 4-repo sample's proxy (`trade_execution/`, `/adapters?/`, `_adapter.py$`, `api/main.py$`) over-matches — any
directory literally named `adapter(s)` was flagged regardless of whether it does real dynamic dispatch. Read every
flagged file directly (`grep -n "importlib\.import_module\|__getattr__\|__import__("`) across all 5 repos that had a
non-trivial dynamic-dispatch-regex hit rate (the 4 original + `deployment-api`, the one new hit from the 18-repo pass):

**Genuine dynamic dispatch (verified file:line — the real allowlist)**:

- `execution-service/execution_service/trade_execution/__init__.py:252` (`__getattr__`) `:257`
  (`importlib.import_module(module_path)`) — dispatches TradFi adapter classes from `_TRADFI_ADAPTER_MAP`. Escape-hatch
  scope: any file under `execution_service/trade_execution/`.
- `features-service/features_service/api/main.py:64` (`importlib.import_module(f"features_service.{family}.api.main")`
  looped over `_FAMILY_NAMES`) — escape-hatch scope: `features_service/api/main.py` plus each family's own
  `features_service/<family>/api/main.py` target.
- `instruments-service/instruments_service/reference_data/adapters/cefi/tardis/_pkg_ref.py:33` (`__getattr__`),
  `.../tradfi/databento/_pkg_ref.py:34`, `.../prediction/polymarket/_pkg_ref.py:34` — three independent lazy-shim
  modules (optional heavy SDK imports). Escape-hatch scope: files under these 3 specific subdirectories only.

**Confirmed false positives (regex matched, no genuine dispatch found — narrower than the raw proxy assumed)**:

- `execution-service`: `sports_execution/adapters/**`, `execution_service/adapters/algorithm_factory.py` — plain static
  imports.
- `features-service`: `calendar/adapters/**`, `volatility/.../vol_greeks_surface_adapter.py`, `commodity/adapters/**`.
- `instruments-service`: `reference_data/adapters/sports/**`, `reference_data/adapters/tradfi/massive.py`, and
  `reference_data/factory.py` itself — confirmed to statically `from .adapters.<x>.<y> import <Z>Adapter` every one of
  its ~50+ adapter classes by name; zero dynamic dispatch anywhere in the factory.
- `market-data-processing-service`: `app/adapters/**` (`base_adapter.py`, `book_snapshot_adapter.py`) — zero dynamic
  dispatch found; the original 1-commit (4%) hit was a pure regex false positive.
- `deployment-api`: `deployment_api/main.py` — zero dynamic dispatch found; `api/main.py$` matched only because the
  package directory `deployment_api` happens to end in the substring `api`, not because it's a real `api/` dir with a
  dispatcher.

### Fleet-wide estimate

**Baseline**: ~9 min `QG slice (tests)` leg (MEASURED, `features-service`, carried over from the original sample — NOT
independently re-measured per repo here). **Reduction**: 20–40% (ASSUMED — industry-typical, not measured in this
codebase). **Eligibility %**: MEASURED per the verified-allowlist table above.

Per-run savings = `narrow_eligible_pct × 9 min × [0.20, 0.40]`. For the 4 highest-eligibility original repos (94–100%
verified) this is **1.7–3.6 min/run**; for `execution-service` (64.7% verified, up from 35%) it's **1.2–2.6 min/run**.

For the 12 repos with both a verified eligibility % and 30-day commit-frequency data (the other 10 either lack frequency
data — the original 4 — or have an undefined eligibility % — the 6 zero-`.py`-touching repos), weekly `.py`-touching
volume is estimated as `(py_touching / commits_sampled) × (total_commits_30d / 30 × 7)` — this ratio extrapolation is
ASSUMED, not measured, since the 50-commit sample window is shorter than 30 days for every high-churn repo in this set.
Weekly fleet savings = `Σ (weekly_py_touching × per-run-savings)`:

**≈ 884–1,768 minutes/week (≈ 14.7–29.5 hours/week) of local `quality-gates.sh` wall-clock time**, across these 12 repos
alone — excludes the 4 original repos (no frequency data) and the 6 zero-denominator repos. This is a LOCAL
`quality-gates.sh` figure; the same eligibility numbers apply to self-hosted CI, but CI runs less often per-engineer
than local QG, so CI's fleet-wide aggregate is smaller than this by whatever ratio (CI runs) : (local QG runs) turns out
to be per repo — not measured here, out of this todo's scope.

## Phase 2 — Implementation (unblocked 2026-08-03 — operator reviewed and approved the design)

> **Unblocked 2026-08-03**: the "Operator review of this design" todo in
> `test_impact_selective_execution_design_2026_08_03.md` is now `[x]` — operator approved the safety model interactively
> ("im fine with the design unblock Phase 2"). The `BLOCKED-OPERATOR-DECISION` tags below are cleared. These todos are
> STRICTLY sequential — the walker must exist before allowlists can wire into it, the golden-set tests need the wired
> walker to test against, and the shadow trials need the tested selector — see `sequential: true` in this plan's
> frontmatter, which serializes the whole plan (Phase 1's own todos have the same real dependency shape, so this is
> correct for both phases, not just Phase 2).

- [x] ✅ [INFRA] P1. **Build the workspace-wide import-graph walker** — `scripts/quality_gates/import_graph_walker.py`
      (unified-trading-pm), extending `check_removed_symbols.py`'s `iter_python_files()` + `ast.walk()`-over-
      `Import`/`ImportFrom` pattern into a `file → {imported files}` edge table (absolute + relative imports,
      package-vs-module resolution, and — a real bug caught by the golden-set tests below — every ANCESTOR package's
      `__init__.py` along a dotted path, since real Python import semantics execute each one before the leaf import
      completes; the first draft only recorded the leaf, which under-narrows), inverted via `invert_edges()` to
      `file → {direct importers}`, with `transitive_importers()` (BFS) and `affected_test_files()` on top. Caching:
      `compute_content_sentinel()` mirrors `.qg_content_sentinel`'s (path, size, mtime) hash pattern. Verified against a
      real repo (`market-data-processing-service`, 253 files, 489 edges) — `book_snapshot_adapter.py`'s direct import of
      `base_adapter.py` and `test_book_snapshot_column_normalization.py`'s transitive dependency on it both
      cross-checked against `grep -n "^import\|^from"` and matched. 10 unit tests in
      `scripts/quality_gates/test_import_graph_walker.py` (synthetic fixture repo: absolute/relative imports, package
      `__init__.py` targets, unparseable-file fallback, BFS correctness, content-sentinel stability). A SECOND real bug
      surfaced by the golden-set tests below (todo 3): `_is_test_file()`'s original heuristic ("`tests` in the path OR
      `test_`-prefixed name") flagged `conftest.py` itself as a test file merely for living under a `tests/` directory —
      pytest never collects `conftest.py` as a test module, so this wrongly injected `conftest.py` into a narrowed set.
      Fixed to filename-prefix-only (`test_*.py`), the actual pytest discovery convention. Full `quality-gates.sh` green
      (1678 passed/11 skipped, 0 failed). SHA stamped in the Progress Log below once shipped.
- [x] ✅ [INFRA] P1. **Wire the Phase-1 verified allowlists (dynamic-dispatch, conftest tree, config/data artifacts)
      into the walker as escape-hatch checks** — `scripts/quality_gates/test_impact_selector.py` +
      `scripts/quality_gates/test_impact_allowlist.yaml` (unified-trading-pm). The allowlist is a hand-curated,
      file:line-cited YAML manifest (matching `removed_symbols_manifest.yaml`'s convention) holding the 3 verified
      dynamic-dispatch entries from Phase 1 todo 3 (`execution-service/trade_execution/`,
      `features-service/api/main.py`, instruments-service's 3 `_pkg_ref.py`-guarded subdirectories) plus the 2
      cross-cutting manifests. `classify_diff()` implements the design's fallback rule literally: shared-dependency repo
      (UTL/UAC) → always full suite; high-level `conftest.py` (repo-root or top-level `tests/`) → full suite; leaf-level
      `conftest.py` → narrows to its own subtree (not full suite — the design's actual rule, more precise than "any
      conftest touch = everything"); cross-cutting manifest → full suite; verified dynamic-dispatch path → full suite;
      **a changed file containing an UNALLOWLISTED dynamic-dispatch call site → full suite too** (fail- closed on a new
      pattern the allowlist hasn't been told about yet, not just the known ones); unparseable file → full suite;
      anything else → narrowed via the walker. Selector's own process errors fail-open to full suite
      (`except Exception`, deliberate per the design's explicit fail-open requirement).
- [x] ✅ [REVIEW] P1. **Build the golden-set selector regression tests** (design doc layer 1) —
      `scripts/quality_gates/test_test_impact_selector.py`, a fixture repo with a known import graph, a verified
      dynamic-dispatch mechanism (mirrors the real `trade_execution/__init__.py` `__getattr__` shape), a multi-level
      `conftest.py` tree (repo-root-equivalent `tests/conftest.py` + leaf `tests/family_a/conftest.py`), and a
      cross-cutting manifest — 9 tests asserting the selector's exact expected output for the safe case AND every
      escape-hatch category (high-level conftest, leaf conftest, cross-cutting manifest, verified dynamic-dispatch,
      UNVERIFIED/unallowlisted dynamic-dispatch fail-closed, unparseable file, shared-dependency repo, no-changed-
      files). This suite is wired into unified-trading-pm's own `quality-gates.sh` (same repo, same gate as every other
      code regression) — caught the 2 real bugs documented in todo 1's writeup. Full `quality-gates.sh` green (1687
      passed/11 skipped, 0 failed).
- [ ] [REVIEW] P1. **Single-repo shadow-mode trial**, on the highest-eligibility repo from the Phase-1 measurement
      (candidates per the 4-repo sample: `market-data-processing-service` or `features-service`, ~94-96% eligible) — run
      the selector in parallel with the real full suite for 2 weeks, always actually executing the full suite, logging
      any divergence. Done-when: zero observed divergences over the full 2-week window; a single divergence resets the
      trial and is filed as its own issue doc (a design bug, not noise).
- [ ] [REVIEW] P2. **Fleet-wide shadow-mode trial**, only after the single-repo trial passes clean — same methodology, 2
      weeks, across every repo from the Phase-1 table with the current allowlists. Done-when: zero observed divergences
      fleet-wide over the full window.
- [ ] [REVIEW] P2. **Promotion decision** — once the fleet shadow trial is clean, decide whether to let the selector
      actually skip real test execution (vs. keep it shadow-only indefinitely), plus stand up the post-promotion nightly
      full-suite canary the design specifies. This is itself an operator call, not a worker todo — state the
      shadow-trial evidence and ask.

## Progress Log

- **2026-08-03**: Plan authored as a LOCAL/human plan (`assigned_vm: NA`) per operator instruction — ready to dispatch
  (flip to `assigned_vm: planning`) once the operator does so after their own `/pre-compact` checkpoint.
- **2026-08-03 (same session)**: Operator reviewed and approved the design interactively — Phase 2's
  `BLOCKED-OPERATOR-DECISION` tags cleared, `sequential: true` added to frontmatter (every todo across both phases has a
  real dependency on its predecessor). `assigned_vm` is still `NA` — dispatch timing is unchanged, still the operator's
  own action post-`/pre-compact`.
- **2026-08-03 (same session) — Phase 1 shipped in full**: extended the 4-repo sample to all 18 remaining Python fleet
  repos (3 parallel Explore sub-agents, 6 repos each, same last-50-commits/30-days methodology, full raw output logged
  per-agent). Then re-verified the dynamic-dispatch escape hatch directly
  (`grep -n "importlib\.import_module\|__getattr__\|__import__("` against every flagged file across the 5 repos with a
  non-trivial hit rate) instead of trusting the raw regex proxy — found genuine dispatch in only 3 places
  (`execution-service/trade_execution/__init__.py:252,257`, `features-service/api/main.py:64`, and 3 `_pkg_ref.py`
  lazy-shim files in `instruments-service`), and confirmed the regex over-matched everywhere else it fired
  (`sports_execution/adapters/`, `algorithm_factory.py`, `calendar/adapters/`, `commodity/adapters/`,
  `vol_greeks_surface_adapter.py`, `reference_data/adapters/sports/`, `reference_data/adapters/tradfi/massive.py`,
  `reference_data/factory.py` itself, `market-data-processing-service/app/adapters/`, and
  `deployment-api/deployment_api/main.py`). Verified eligibility moved substantially upward for `execution-service` (35%
  → 64.7%) and `deployment-api` (83.3% → 100%), modestly for the others. Full 22-repo table, verified allowlist, and
  fleet-wide estimate (≈884–1,768 min/week, MEASURED eligibility × ASSUMED 20-40% reduction, derivation shown) are now
  in this doc above — all 3 Phase-1 todos flipped `[x]`. Phase 2 (implementation) starts next, per `sequential: true`.
- **2026-08-03 (same session) — Phase 2 todos 1-3 shipped**: `unified-trading-pm@1452d5da1` — import-graph walker
  (`import_graph_walker.py`), the escape-hatch-wired selector (`test_impact_selector.py` +
  `test_impact_allowlist.yaml`), and the golden-set regression suite (`test_test_impact_selector.py`, 9 tests) all
  landed together. 19 new tests total across the 2 new test files; full `quality-gates.sh` green (1687 passed/11
  skipped, 0 failed). 2 real bugs caught by the tests themselves before shipping: (1) the walker's first draft only
  recorded the leaf of a dotted import path, missing every ANCESTOR package's `__init__.py` — real Python import
  semantics execute each one, so this under-narrowed; (2) `_is_test_file()`'s original heuristic flagged `conftest.py`
  as a test file merely for living under a `tests/` directory, when pytest never collects it as a test module — fixed to
  the actual `test_*.py` filename convention. Both fixed before ship, not after.
