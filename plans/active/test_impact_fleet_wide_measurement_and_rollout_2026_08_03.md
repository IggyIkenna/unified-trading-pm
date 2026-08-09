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
    /plans/archive/issues/test_impact_selective_execution_design_2026_08_03.md,
    /plans/archive/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
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
effort: high
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
context_scope:
  [
    /plans/archive/issues/test_impact_selective_execution_design_2026_08_03.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    scripts/quality_gates/test_impact_selector.py,
    scripts/quality_gates/import_graph_walker.py,
    market-data-processing-service/scripts/quality-gates.sh,
  ]
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
- [x] ✅ [REVIEW] P1. **Single-repo shadow-mode trial — SUPERSEDED 2026-08-03 by direct promotion to a real gate (see
      the new todo below) before the 2-week window completed.** `market-data-processing-service@1c8588c` shipped the
      original shadow-mode infrastructure (purely additive logging, verified via a real local run — 2332 passed/2
      skipped, exit 0 — and dry-run-validated against 3 real historical commits). The trial's own done-when (zero
      divergences over a full 2-week window) was never met by elapsed time — the operator instead directly authorized
      promotion (see Progress Log) before the window ran, so this todo closes as superseded, not as satisfied. The
      divergence-analysis tool (next todo) is still unbuilt and still has no urgency driver now that MDPS runs a real
      gate instead of a shadow trial.
- [ ] [SCRIPT] P2. **Build the shadow-trial divergence-analysis tool — DEPRIORITIZED, no longer load-bearing.**
      Originally meant to read the shadow-mode trial's logs; MDPS no longer runs in shadow mode (see above), so this
      tool's original purpose (measuring divergence during a trial before promoting) no longer applies to MDPS. Retained
      as a P2 for a genuinely useful purpose: retroactively checking whether ANY narrowed real gate run (post-promotion)
      ever missed a real failure — i.e. this becomes a POST-PROMOTION safety check, not a pre-promotion trial tool.
      Done-when: run against MDPS's real `TEST_IMPACT_GATE:` CI logs and produce a clean per-run divergence table.
- [x] ✅ [SCRIPT] P1. **Accelerate validation via a historical-commit backtest — DONE, but did NOT clear the evidence
      bar (see Progress Log for the full report).** `scripts/quality_gates/test_impact_backtest.py` +
      `test_test_impact_backtest.py` (unified-trading-pm) built and run for real against `execution-service`,
      `features-service`, `instruments-service`, `market-data-processing-service` (last 40 `quality-gates-v2` runs
      each). **Finding: historical CI data is queryable (`gh run list`/`gh run view --log`), but the current fleet is
      mid an already-tracked resource-contention crisis
      (`/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`, status open) that makes
      almost every recent "failure" run an infra-level SIGINT/OSError kill or a known contention-induced pytest-timeout
      (`/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` + `..._continued_2026_08_02.md`,
      both open, both already naming the exact test this backtest also hit) — NOT a genuine content-level test failure
      attributable to a specific diff.** Usable backtest sample size: `execution-service` 0/1, `instruments-service`
      0/5, `market-data-processing-service` 0/11 (100% unattributable infra kills in all three, even at a 40-run
      window); `features-service` showed 1 nominally-attributable failure that turned out to be the SAME already-tracked
      `test_cross_timeframe_sanity.py` contention-timeout (confirmed by cross-referencing 4 other unrelated commits with
      the identical signature) firing on a commit that only touched unrelated `commodity/` files — explained
      pre-existing flakiness, not a selector divergence, so NOT filed as a new issue (already tracked). **Net result: 0
      usable samples, 0 genuine divergences, but also 0 evidence — the backtest cannot currently produce the accelerated
      evidence the operator asked for, because the fleet's own CI health (not the selector) is the limiting factor.**
      This does NOT mean promote, and does NOT mean the selector is unsafe — it means the live single-repo trial (below,
      clock to 2026-08-17) remains the only viable evidence path until the capacity crisis resolves enough to produce
      clean historical samples.
- [ ] [REVIEW] P2. **Fleet-wide shadow-mode trial / evidence sufficiency — STILL BLOCKED overall, but real progress
      2026-08-05. UNAFFECTED by the MDPS-only promotion below** (that was a scoped, single-repo operator override, not
      fleet-wide evidence clearing the bar this todo actually gates). Gated on EITHER the live single-repo trial
      (`market-data-processing-service`, done-when 2026-08-17 — moot now that MDPS runs a real gate instead of a shadow
      trial; re-derive fleet-wide evidence from the post-promotion divergence-analysis tool instead, see above) OR the
      historical backtest clearing with zero divergences over a sample the reviewer judges large enough to trust.
      **Re-ran the backtest 2026-08-05** now that
      `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` has meaningfully (not fully)
      reduced fleet contention: `execution-service`/`instruments-service`/ `market-data-processing-service` still 0
      usable (100% unattributable infra kills — contention reduced, not eliminated), but `features-service` produced a
      real usable sample for the first time — **5/5, and investigated each one directly rather than trusting the raw
      tool output**: all 5 are the SAME already-tracked pytest-timeout-under-contention flakiness
      (`/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md`, identical
      `+++ Timeout +++` signature), NOT genuine selector divergences — the selector's narrowing was correct in every
      case; the tests separately timed out under load, unrelated to the diffs. **Net: 0 genuine divergences found in the
      first real usable sample (n=5, one repo)** — real, if still modest, positive evidence, not yet "large enough to
      trust" fleet-wide on its own. This plan's `sequential: true` only encodes file-order, not this OR; a
      human/reviewing-worker must read both todos' actual state and decide which (if either) satisfies the bar, not just
      check that the prior todo in file order is `[x]`. Done-when: zero observed divergences fleet-wide, from whichever
      evidence source actually satisfies the reviewer — re-run the backtest again once contention drops further (e.g.
      after the pending AO-box downsize, still on operator hold) to grow the sample across more repos.
- [x] ✅ [REVIEW] P2. **Promotion decision — RESOLVED for MDPS ONLY, 2026-08-03, direct operator override; fleet-wide
      promotion remains exactly as blocked as the todo above states.** Operator directly instructed promotion ("pls
      implement /autonomous") after being shown the corrected evidence picture in-conversation (backtest inconclusive —
      0 usable samples in 3/4 repos, confounded by the fleet-wide CI capacity crisis; live trial had zero elapsed signal
      at promotion time) — explicitly chose **"Promote now, no extra safety net"** over the offered alternative of
      adding a post-promotion nightly full-suite canary. This is a genuine, informed risk-accept by the operator, not
      evidence claiming to satisfy the bar — the fleet-wide evidence-sufficiency todo above is UNCHANGED and still gates
      any repo beyond MDPS. See Progress Log for the full implementation record (including a real architectural blocker
      discovered and fixed: the per-repo coverage floor cannot be satisfied by a narrowed test run, so
      `COV_FAIL_UNDER_OVERRIDE` was added as a new opt-in `base-service.sh` hook).

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
- **2026-08-03 (same session) — Phase 2.4 shadow-mode trial STARTED (not complete)**:
  `market-data-processing-service@ 1c8588c`. Investigated that repo's real CI first — its test execution runs through
  the SHARED, fleet-wide `base-service.sh` (sourced from unified-trading-pm), so a naive addition there would have
  silently gone fleet-wide before Phase 2.5 was supposed to happen. Instead added the shadow-mode block to that repo's
  OWN per-repo `scripts/quality-gates.sh` wrapper (the file's documented per-repo customization point — same pattern its
  existing `[6.X]`/`[6.Y]` custom sections already use), keeping this genuinely single-repo-scoped and zero-blast-radius
  (purely additive logging, never gates or skips). Dry-run-validated against 3 real historical commits before touching
  live CI, then verified with a full real local `quality-gates.sh` run (2332 passed/2 skipped, exit 0, correct verdict
  against the actual diff) before shipping. Added a new todo for the divergence-analysis tool (buildable now, but reads
  back CI history so has nothing meaningful to analyze until real runs accumulate). **The 2-week real-time clock starts
  today, 2026-08-03** — the trial's own done-when (zero divergences) is a genuine physical-time requirement no amount of
  engineering effort in this session can compress; re-check ~2026-08-17.
- **2026-08-03 (session pause point)**: Phase 1 (all 3 todos) and Phase 2 todos 1-3 are fully shipped, tested, and
  verified. Phase 2 todo 4 (single-repo shadow trial) has its infrastructure shipped and the real trial clock running,
  per above — genuinely not completable sooner regardless of further effort. Todos 5 (fleet-wide trial) and 6 (promotion
  decision, explicitly an operator call per its own text) are correctly blocked behind it via `sequential: true`.
  Nothing else in this plan is actionable right now without either the 2-week window elapsing or the divergence-analysis
  tool existing to read it.
- **2026-08-03 (operator decision, same session) — accelerate via historical backtest, do NOT skip validation.**
  Operator asked to get the fleet-wide savings immediately rather than wait ~2 weeks. Presented 3 options: (a) keep the
  live trial as designed, (b) accelerate via a historical-commit backtest — same zero-divergence evidence bar,
  compressed timeline, since past commits' real outcomes are already known, (c) skip validation and promote fleet-wide
  now, accepting the risk of a silent under-tested regression reaching execution-critical repos (`execution-service`
  directly touches live trading) with no CI signal at all. **Operator chose (b).** New todo added above (between the
  single-repo trial and the fleet-wide trial): build the backtest, gated on first confirming historical CI pass/fail +
  failing-test data is actually queryable (not assumed) — if it isn't, the todo's done-when is reporting that finding,
  not forcing a smaller sample to look complete. The live single-repo trial keeps running unchanged alongside it
  (zero-cost, doesn't conflict). The fleet-wide trial and promotion todos were reworded to accept EITHER evidence source
  clearing (live trial OR backtest) — `sequential: true` only enforces file-order, so a human/worker must actually read
  both todos' state, not just check the immediately-prior checkbox, before deciding the bar is met. **Per explicit
  operator instruction, this update is DOC-ONLY** — the backtest itself is scoped as a todo for a future (fresh-context)
  session/agent to execute, not started here.
- **2026-08-03 (same session) — Backtest EXECUTED, full honest report.** `unified-trading-pm` —
  `scripts/quality_gates/test_impact_backtest.py` (+ `test_test_impact_backtest.py`, 5 unit tests covering the two real
  attribution shapes + the unattributable case). Methodology: `gh run list --workflow quality-gates-v2.yml` per repo
  (last 40 runs), filter to `conclusion=failure`, fetch each run's full log (`gh run view --log`), try to attribute the
  failure to a specific test file (pattern 1: a clean pytest `FAILED <nodeid>` + short-summary section; pattern 2
  fallback: a Timeout/crash mid-test — the last traceback frame naming a `tests/` file is where execution was stuck),
  then replay `test_impact_selector.py` against that commit's real diff (this workspace's own local clones) and check
  whether the real failing test falls inside the narrowed set.
  - **`execution-service`**: 40 runs listed, 1 failure, unattributable (infra kill) → 0 usable.
  - **`instruments-service`**: 40 runs listed, 5 failures, all 5 unattributable → 0 usable.
  - **`market-data-processing-service`**: 40 runs listed, 11 failures, all 11 unattributable (same SIGINT →
    `graceful shutdown` → `OSError: cannot send (already closed?)` signature every time) → 0 usable.
  - **`features-service`**: 15 runs listed (didn't need 40 — plenty of failures already), 6 failures, all 6 attributed
    to `tests/delta_one/unit/test_cross_timeframe_sanity.py` (pytest-timeout), across only 4 distinct commits (one
    retried 3× via `workflow_dispatch` — a manual re-trigger pattern, consistent with someone hoping the flake would
    clear). 5 of 6 showed literally no `.py` diff (the retries landed on later, unrelated doc-only HEAD commits — the
    flake fires independent of what's even in the diff). The 1 with a real diff (commit `d387ba7f78`, "fix(commodity):
    scope weather_delta to NG...") touched only `commodity/` files — completely unrelated to `delta_one` — yet still hit
    the identical timeout signature, confirming this is diff-independent flakiness, not a regression this specific
    commit introduced. Cross-referenced against 4 OTHER commits with the same signature (unrelated diffs, same test,
    same timeout) to confirm — this is not a one-off coincidence.
  - **Root cause, already tracked, not new**:
    `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (status open) — ~20+ repos'
    self-hosted QG runners colocated on ONE oversubscribed 16-vCPU/64GB EC2 instance, causing exactly this class of
    hung/SIGINT-killed run and contention-induced timeouts;
    `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` + `..._continued_2026_08_02.md` (both
    open) already name `test_cross_timeframe_sanity.py` by name as a known recurring casualty. Neither issue needed a
    new doc — this backtest is corroborating evidence of their ongoing impact, not a new discovery, so no duplicate
    filed.
  - **Bottom line for the operator's acceleration ask**: the backtest mechanism works exactly as designed (real gh CLI
    data, real selector replay, real cross-referencing to rule out a false-positive) — but the fleet's CURRENT CI health
    is the limiting factor, not the selector. 0 usable samples across 3 repos and 1 explained-away false-positive in the
    4th is not "clean, zero divergences" — it's "no evidence either way." **The backtest does NOT accelerate anything
    right now; the live single-repo trial (clock to 2026-08-17) remains the only real evidence path**, unless the
    capacity crisis resolves and a re-run produces a genuinely large, clean sample.

- **2026-08-03 (same session) — MDPS PROMOTED to a real gate, direct operator override.** Operator asked (in-chat)
  whether the test-impact selector's "reduction in testing length" had actually been implemented, and separately invoked
  `/autonomous` to implement it. Before touching anything, corrected the operator's premise in-conversation: the
  backtest above did NOT clear the evidence bar (0 usable samples in 3/4 repos, confounded by the fleet-wide CI capacity
  crisis — see above) and the live trial had zero elapsed signal — "we backtested that" was not the same as "the
  backtest validated it." Presented three options (promote + nightly canary / promote with no extra safety net / hold
  for real evidence); **operator explicitly chose "Promote now, no extra safety net."**
  - **Architectural blocker discovered and fixed**: MDPS's `pyproject.toml` sets
    `[tool.coverage.report] fail_under = 85`. A narrowed pytest invocation (only the selector's chosen subset of test
    files) computes coverage against the WHOLE `$SOURCE_DIR` regardless of how few tests ran — verified empirically that
    a single-file narrowed run reports ~15% coverage, which would fail the 85% floor on every narrowed run, a spurious
    failure the original shadow-mode design never had to confront (shadow mode always ran the real full suite
    underneath). Fixed by adding a new, OPT-IN `COV_FAIL_UNDER_OVERRIDE` hook to `base-service.sh` (unified-trading-pm)
    — empty/unset for every repo by default (verified: no other repo sets it, zero behavior change fleet-wide), only
    MDPS's own wrapper sets it to `0` when its gate narrows, relaxing the floor for that one invocation. Full-suite runs
    (every escape-hatch case, the overwhelming majority) are completely unaffected.
  - **Implementation**: moved the test-impact-selector invocation in MDPS's `scripts/quality-gates.sh` from AFTER
    `source base-service.sh` (the old shadow-mode position, where it could only log, never gate) to BEFORE it, so its
    verdict can set `PYTEST_UNIT_DIR` (narrowed file list, using the SAME pre-source override hook per-family layouts
    already use) and the new `COV_FAIL_UNDER_OVERRIDE`. Every existing fail-closed escape hatch is untouched (high-level
    conftest, cross-cutting manifest, verified/unverified dynamic-dispatch, unparseable file, shared-dependency repo,
    no-diff, selector-process-error all still resolve to `RUN_FULL_SUITE=true`, unchanged). Removed the now-superseded
    post-source shadow-mode block (would have been redundant duplicate logging, not a second gate).
  - **Verification performed** (not just reasoning): (1) synthetic 5-scenario bash logic test of the new parsing
    (full-suite/narrowed/empty-narrowed-falls-through/selector-error/stray-stdout-line, all correct); (2) confirmed
    unquoted `PYTEST_UNIT_DIR` word-splits into separate pytest args under REAL bash (caught that my first test ran
    under the tool shell's zsh, which does NOT word-split by default — re-verified via explicit `bash -c`); (3) a REAL
    end-to-end run against MDPS with `PYTEST_UNIT_DIR` narrowed to one file and NO override — confirmed it genuinely
    fails (`Total coverage: 15.05%` vs `fail_under=85`), proving the blocker is real, not theoretical; (4) the SAME
    narrowed run WITH `COV_FAIL_UNDER_OVERRIDE=0` — confirmed `✅ QG_SLICE=tests PASSED`, only the narrowed file's 21
    tests ran; (5) an isolated integration run of the real pre-source block against the REAL `test_impact_selector.py`
    with an actual test file as the changed input — confirmed correct wiring end to end; (6) a new permanent bash
    self-test, `unified-trading-pm/scripts/quality-gates-base/tests/test-qg-cov-fail-under-override.sh` (mirrors the
    existing `test-qg-governor-slice-gating.sh` replica-matcher convention, since `base-service.sh` isn't sourceable in
    isolation), 5/5 cases pass; (7) `shellcheck` clean on all 3 touched files; (8) full `quality-gates.sh --no-fix`
    green on both `unified-trading-pm` (base-service.sh edit) and `market-data-processing-service` (default/no-diff
    path, confirming the common case is completely unaffected).
  - **Scope, explicitly**: MDPS ONLY. The fleet-wide evidence-sufficiency todo above is UNCHANGED — this was a scoped
    operator risk-accept for one repo, not fleet-wide evidence clearing the bar. No other repo's `quality-gates.sh` was
    touched; `base-service.sh`'s new hook is inert everywhere it isn't explicitly opted into.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA, valid — first audit pass (filed
today). All 4 open items re-verified: the calendar-gated shadow-trial item (re-visit ~2026-08-17); the promotion
decision (explicitly self-described as "itself an operator call, not a worker todo"); the fleet-wide evidence
sufficiency item (explicit human/reviewer judgment call). The `[SCRIPT]`-tagged divergence-analysis tool item is
individually bounded/deterministic-shaped on its own and would read as a strong RECLASSIFY candidate in isolation — NOT
recommending RECLASSIFY on it: this doc's own frontmatter `source:` and Progress Log both carry an explicit, dated
operator instruction that the intended next action is flipping the WHOLE plan to `assigned_vm: planning` once the
operator completes their own `/pre-compact` checkpoint, not a partial/cherry-picked dispatch; the plan also sets
`sequential: true` at the plan level, so a partial RECLASSIFY of one item isn't structurally consistent with how it's
built today. No ARCHIVE. Confirmed zero active `assigned_vm: planning` siblings in
`parent_epic: deployment_and_user_management_master` overlapping this content (one apparent grep hit was a false
positive — a different plan's `parent_epic`). **Flag for the orchestrating agent/operator** (informational only, not an
audit action): whether the operator's own `/pre-compact` checkpoint — the doc's stated flip-trigger — has already
happened this session is a timing question outside na-eligibility-audit's mechanism; if it has, this doc may already be
due for its own pre-authorized next action independent of this audit.

- **context-scout 2026-08-03**: populated context_scope (6 entries).
- **context-scout 2026-08-03 (re-scout)**: re-verified context_scope (6 entries) -- all paths resolve
  (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`, already correctly dated); no change needed.
- **2026-08-05 (interactive session)**: re-ran the historical backtest after completing
  `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` (fleet contention measurably down,
  load average ~65 peak → ~29 on the new dedicated VM, not fully resolved). `features-service` finally produced a usable
  sample (5, up from 0) — investigated each divergence directly against the raw CI logs rather than trusting the tool's
  summary, and all 5 turned out to be the same already-tracked pytest-timeout-under-contention flakiness, not genuine
  selector bugs (cross-linked into `pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md`). Net: first
  real, if modest, positive evidence point (0/5 genuine divergences) — updated the fleet-wide evidence-sufficiency todo
  above accordingly. The other 3 backtested repos remain at 0 usable sample; re-run again once contention drops further.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator-directed human plan, sequential judgment-gated items

**na-eligibility-audit 2026-08-07** (tranche `ci`): KEEP-NA, valid — confirms the established verdict. Both open items
unchanged: the `[SCRIPT] P2` divergence-analysis tool remains individually bounded-looking but stays correctly NA per
the 2026-08-03 pass's own reasoning (`sequential: true` at the plan level + the doc's stated whole-plan
`assigned_vm: planning` flip-trigger, not a partial dispatch) — not re-litigating that citation; the `[REVIEW] P2`
fleet-wide evidence-sufficiency item remains an explicit human/reviewer judgment call. No new RECLASSIFY or ARCHIVE
signal.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:e82da2dcd15f1683]: KEEP-NA,
valid — confirms the 2026-08-07 verdict, unchanged. The `[SCRIPT] P2` divergence-analysis tool item stays correctly NA
under the plan-level `sequential: true` + whole-plan `assigned_vm: planning` flip-trigger (not a partial dispatch); the
`[REVIEW] P2` fleet-wide evidence-sufficiency item remains an explicit human/reviewer judgment call. No `assigned_vm`
change.
