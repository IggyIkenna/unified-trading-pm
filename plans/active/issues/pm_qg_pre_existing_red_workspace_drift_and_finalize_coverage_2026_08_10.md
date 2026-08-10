---
doc_type: issue
title: >-
  PM quality-gates.sh red on 8 pre-existing live-corpus tests (check_workspace_code_workspace_drift +
  check_finalize_plan_coverage) on the shared orchestrator VM — blocks every slot's PM QG sentinel
summary: >-
  Discovered 2026-08-10 while shipping the safe_doc_push_isolation_rewrites_slot_commit_identity fix: PM
  `quality-gates.sh` fails on 8 tests that depend on LIVE workspace/plan-corpus state, independently of any agent's
  change. Verified PRE-EXISTING: the same 8 tests fail byte-identically at `origin/live-defi-rollout` (HEAD
  `5d7019869b`, no local commit) on the shared VM. The two defect families: (1) 5 tests in
  `tests/unit/test_check_workspace_code_workspace_drift.py` expect `check_workspace_code_workspace_drift.py` to flag
  drift against a canonical `.code-workspace` repo list that has since evolved (check returns 0/clean, tests assert
  1/violation); (2) 3 tests in `scripts/quality_gates/test_check_finalize_plan_coverage.py` scan the LIVE
  `plans/active/` corpus and assert specific violation counts the current churning corpus no longer yields. Effect:
  every slot's PM `quality-gates.sh` is red on the shared host (no `.qg_last_passed_sha` sentinel), so quickmerge
  refuses PM code ships until a fix lands.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, test-isolation, pre-existing-red, workspace-drift, plan-coverage, infra]
related:
  - /plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md
created: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - slot-29, 2026-08-10, blocking ship of safe_doc_push_isolation_rewrites_slot_commit_identity
---

# PM quality-gates.sh red on 8 pre-existing live-corpus tests

## What I found

Running `bash scripts/quality-gates.sh` on `unified-trading-pm` (slot 29, 2026-08-10) failed with 8 test failures, none
touched by the change being shipped (`scripts/dev/safe-doc-push.sh` + a new `.bats` test):

```
FAILED tests/unit/test_check_workspace_code_workspace_drift.py::TestCheck::test_missing_active_repo_fails
FAILED tests/unit/test_check_workspace_code_workspace_drift.py::TestCheck::test_stale_archived_repo_listed_fails
FAILED tests/unit/test_check_workspace_code_workspace_drift.py::TestCheck::test_unknown_repo_in_folders_fails
FAILED tests/unit/test_check_workspace_code_workspace_drift.py::TestCheck::test_consolidated_repo_treated_as_inactive
FAILED tests/unit/test_check_workspace_code_workspace_drift.py::TestCheck::test_missing_canonical_returns_2
FAILED scripts/quality_gates/test_check_finalize_plan_coverage.py::test_only_fails_on_a_violating_plan_in_scope
FAILED scripts/quality_gates/test_check_finalize_plan_coverage.py::test_only_with_multiple_paths_reports_every_violation_among_them
FAILED scripts/quality_gates/test_check_finalize_plan_coverage.py::test_default_mode_regresses_on_a_new_uncovered_plan
```

**Verified PRE-EXISTING** (2026-08-10): created a `git worktree` at `origin/live-defi-rollout` (HEAD `5d7019869b`, which
does NOT contain the in-flight commit) and ran the 8 tests standalone — **byte-identical failures**
(`8 failed, 8 passed`). The red is not caused by any slot's in-flight change.

Root cause per family:

1. **Workspace-drift tests (5)** — `check_workspace_code_workspace_drift.py` compares a workspace's `.code-workspace`
   `folders[]` against the canonical `cursor-configs/unified-trading-system-repos.code-workspace` repo list. The tests
   assert a violation (rc=1) for e.g. a missing active repo, but the checker now reports
   `✅ workspace .code-workspace clean: folders[] == 26 active+scaffolded repos (no drift)` — the canonical list has
   evolved (26 repos) past what the test fixtures assume, so the tests' expected-drifty fixtures read as clean.
2. **Finalize-plan-coverage tests (3)** — `check_finalize_plan_coverage.py` scans the LIVE `plans/active/` corpus
   (`Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — 0 violation(s)`) and asserts
   specific violation counts. On the shared VM the plan corpus churns continuously (concurrent slots
   flipping/archiving), so the live-state scan yields 0 where the test expects 1. These are live-corpus-dependent tests
   that cannot be stable on the shared host.

## Why it matters

- PM `quality-gates.sh` is RED on the shared orchestrator VM for EVERY slot (not just this one) until a fix lands — no
  `.qg_last_passed_sha` sentinel is written, so `quickmerge --agent` refuses all PM code ships.
- The 8 failures are non-deterministic w.r.t. the live workspace/plan corpus: a test result that depends on concurrent
  slots' activity is a false signal — sometimes green, sometimes red, never meaningful.
- Blocking this: the `safe_doc_push_isolation_rewrites_slot_commit_identity` fix (already implemented + verified on
  slot-29) cannot reach the fleet until PM QG is green again.

## Recommended decision

Fix the two test families so PM QG is deterministic on the shared host:

- Make the workspace-drift tests assert against a FIXED fixture `.code-workspace` + canonical repo list (not the live
  `cursor-configs/unified-trading-system-repos.code-workspace`), OR update the fixtures to the current 26-repo canonical
  list.
- Make the finalize-plan-coverage tests run against a FIXED fixture plan corpus (tmp dir), not the live `plans/active/`.

## Todos

- [ ] [INFRA] P1. **Fix `check_workspace_code_workspace_drift.py` test fixtures to match the current canonical repo
      list** (repo: unified-trading-pm). The 5 failing `TestCheck` tests in
      `tests/unit/test_check_workspace_code_workspace_drift.py` assert drift the checker no longer finds because the
      canonical `.code-workspace` (26 repos) has evolved past the test fixtures. Fix by pointing the tests at a FIXED
      fixture `.code-workspace` (or updating the fixtures to the current 26-repo list) so they don't depend on the live
      canonical file. Done when: the 5 tests pass deterministically on the shared VM at `origin/live-defi-rollout`.
- [ ] [INFRA] P1. **Make `check_finalize_plan_coverage.py` tests use a fixed fixture corpus, not the live
      `plans/active/`** (repo: unified-trading-pm). The 3 failing tests in
      `scripts/quality_gates/test_check_finalize_plan_coverage.py` scan the live plan corpus and assert violation counts
      the churning corpus no longer yields. Fix by running them against a fixed tmp fixture corpus. Done when: the 3
      tests pass deterministically on the shared VM regardless of concurrent plan activity.

## Progress Log

- **2026-08-10 (slot-29, infra)**: Found while shipping `safe_doc_push_isolation_rewrites_slot_commit_identity`.
  Verified pre-existing via a base-HEAD worktree (`origin/live-defi-rollout`, HEAD `5d7019869b`) — identical 8 failures
  with no local commit. Declared PM `qg_red` repo-blocker RB-… (backend now owns the wait). Filed this doc with 2 fix
  todos.
