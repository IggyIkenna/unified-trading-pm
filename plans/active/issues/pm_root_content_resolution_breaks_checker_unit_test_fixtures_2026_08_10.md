---
doc_type: issue
title: >-
  QG red: 2 checker test suites break under 55a43797a4's content-based PM-root resolution — the synthetic
  `--workspace-root` fixture is ignored
summary: >-
  8 deterministic failures in unified-trading-pm `quality-gates.sh` after commit 55a43797a4 (2026-08-10) made PM-root
  resolution content-based. `scripts/quality_gates/_pm_root.py`'s `pm_root()` resolves the checkout root from `__file__`
  FIRST and unconditionally wins, so the `--workspace-root` value (a synthetic `tmp_path` fixture in these unit tests)
  is never used and the checkers read the REAL checkout instead. Affected:
  `test_only_fails_on_a_violating_plan_in_scope`, `test_only_with_multiple_paths_reports_every_violation_among_them`,
  `test_default_mode_regresses_on_a_new_uncovered_plan` (`scripts/quality_gates/test_check_finalize_plan_coverage.py`)
  and `test_missing_active_repo_fails`, `test_stale_archived_repo_listed_fails`, `test_unknown_repo_in_folders_fails`,
  `test_consolidated_repo_treated_as_inactive`, `test_missing_canonical_returns_2`
  (`tests/unit/test_check_workspace_code_workspace_drift.py`).
status: open
archive_exempt: true
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [qg, regression, unit-test, pm-root, workspace-drift, finalize-plan, ci-red]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
    /plans/archive/issues/safe_doc_push_isolation_rewrites_slot_commit_identity_2026_08_10.md,
  ]
created: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: unified-trading-pm@8a7b1860a0
context_scope:
  [
    scripts/quality_gates/_pm_root.py,
    scripts/quality_gates/test_check_finalize_plan_coverage.py,
    tests/unit/test_check_workspace_code_workspace_drift.py,
    /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
  ]
source: slot-17 quality-gates Pass-1 run on cross_cutting_satellite_ao_dispatch_batch6 todo 3 (2026-08-10)
---

# QG red: content-based PM-root resolution breaks 2 checker test suites

## What I found

A full `bash scripts/quality-gates.sh` on unified-trading-pm HEAD (`36fc569462`, which includes the upstream commit
`55a43797a4`) fails 8 tests deterministically (8 failed, 1911 passed, 17 skipped):

- `scripts/quality_gates/test_check_finalize_plan_coverage.py` (3): all three expect `rc == 1` for a synthetic violating
  plan, but the checker prints "0 violation(s)" and returns 0.
- `tests/unit/test_check_workspace_code_workspace_drift.py` (5): the four drift scenarios expect `rc == 1` and
  `test_missing_canonical_returns_2` expects `rc == 2`, but every one returns 0 with "✅ workspace .code-workspace
  clean: folders[] == 26 active+scaffolded repos".

Root cause is a single change, not eight independent bugs. `55a43797a4` introduced `scripts/quality_gates/_pm_root.py`
(operator-ruled 2026-08-10, pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md F7) and wired
`_pm_root_or_legacy()` into these checkers. Its `pm_root()` resolves the PM checkout by CONTENT from
`Path(__file__).parents[2]` first and returns it unconditionally when it "looks like PM root"; the explicit
`workspace_root` only matters as a FALLBACK when content resolution fails. Because the checker module is loaded from the
REAL checkout, content resolution always succeeds — so a test passing `--workspace-root <tmp fixture>` (or calling
`check(tmp_path)`) is silently ignored and the checker scans the real `plans/active/` corpus / real `.code-workspace`
instead of the fixture.

Verified this is pre-existing, not from my task: `git diff origin/live-defi-rollout..HEAD` shows only my 3 files
(scripts/validation/check-template-yaml.py, scripts/workflow-templates/rollout-workflow-templates.sh,
tests/unit/test_check_template_yaml.py); the 4 failing checker/test files are byte-identical to
origin/live-defi-rollout. The failures reproduce with my diff removed.

## Why it matters

- `quality-gates-v2` is the required CI gate on every repo. unified-trading-pm CI has been red since ~01:33 UTC today
  for several other causes (VERSION_SPLIT / check_na_corpus_ratchet / plan-discipline — covered by repo-blocker
  RB-5b82f02e + escalation agt-cced28); this 8-test regression is an ADDITIONAL, independent red cause that must also be
  fixed before PM CI can go green.
- The regression breaks the test contract: these suites are supposed to exercise the drift/coverage logic against
  controlled synthetic corpora. After this change they no longer test anything (they read the live repo and trivially
  pass) — so future drift/finalize regressions would ship silently.
- It blocks every PM-backed task under the green-tree rule (this slot's own cross_cutting_satellite_ao_dispatch_batch6
  todo 3 is stuck on it).

## Recommended decision

Fix on the TEST side, preserving the deliberate production behavior (`_pm_root.py`'s documented "Fallback order is
deliberate" comment). The tests should redirect `_pm_root_or_legacy` to their fixture PM root, which is standard
dependency-injection-via-monkeypatch and does not touch `_pm_root.py`:

- In `tests/unit/test_check_workspace_code_workspace_drift.py`: patch the loaded module
  (`MOD._pm_root_or_legacy = lambda root: Path(root) / "unified-trading-pm"`) before the `TestCheck` scenarios run.
- In `scripts/quality_gates/test_check_finalize_plan_coverage.py`: the module's `main()` resolves `_pm_root_or_legacy`
  as a module global at call time, so set
  `check_finalize_plan_coverage._pm_root_or_legacy = lambda root: Path(root) / "unified-trading-pm"` before the
  `main([...])` calls.

DO NOT flip `_pm_root.py` to prefer the legacy `<workspace_root>/unified-trading-pm` when it exists — that would
re-introduce the worktree-shadowing case F7 was built to fix (a stale main checkout can shadow the worktree's correct PM
root). That alternative is operator-gated if ever wanted.

## Fix todos

- [x] ✅ [SCRIPT] P1. Redirect `_pm_root_or_legacy` to the fixture PM root in the two broken test suites so they
      exercise the drift/coverage logic against their synthetic `tmp_path` corpus again (exact patch recipe in
      "Recommended decision" above; do not change `_pm_root.py` or the checkers). Done when: all 8 tests pass under
      `bash scripts/quality-gates.sh`. (repo: unified-trading-pm) — fixed by slot-17, unified-trading-pm@8a7b1860a0
      (2026-08-10)

## Progress Log

- **2026-08-10 (slot-17)**: Regression root-caused + fixed in the same pass that surfaced it. `55a43797a4`'s
  content-based `_pm_root.py` resolution made the checkers ignore the synthetic `--workspace-root` fixture; slot-17
  shipped the test-side `_pm_root_or_legacy` redirect (`unified-trading-pm@8a7b1860a0`, part of the same quickmerge as
  the batch6 todo 3 template-lint pre-flight) and verified all 8 tests pass under `quality-gates.sh`. Set
  `archive_exempt: true` (status stays `open` — a terminal `resolved` status demands archival, but this freshly-resolved
  regression record is cited as SSOT by two shipped test files
  (`tests/unit/test_check_workspace_code_workspace_drift.py`,
  `scripts/quality_gates/test_check_finalize_plan_coverage.py`); archiving it now would break those references and force
  a code change, so it is intentionally kept active for fleet-wide bulk archival later).
- **context-scout 2026-08-14**: populated context_scope (4 entries).
