---
doc_type: issue
title: strategy-service Verification-Debt Findings — Coverage-Gate CI Wiring Gap and ε=0 Negative-Control Gap
summary:
  Two findings from a read-only production-verification audit of already-shipped strategy-service commits (35547432,
  3e8162c6) — the clients.yaml coverage gate structurally skips in real CI regardless of violations, and the ε=0
  determinism claim for the ADV as_of_date wiring has no negative control proving a divergence is actually detected.
  venue_capabilities (c95473c3) and the 8c11e2fc shadow-SSOT collisions were also audited and found CORRECT — no todos
  needed for those two. No fixes applied during the audit; scoped here for AO dispatch.
status: open
nature: process
resolved_by:
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [audit, verification-debt, ci-gate, determinism, code-quality]
related:
  [
    /plans/active/issues/execution_service_verification_debt_findings_2026_08_15.md,
    /plans/active/issues/pm_archive_false_done_and_review_backlog_2026_08_15.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1
effort: medium
locked_by:
locked_since:
context_scope:
  [
    strategy-service/strategy_service/engine/strategies/v2/clients_yaml_coverage.py,
    strategy-service/tests/unit/engine/strategies/v2/test_clients_yaml_coverage_gate.py,
    strategy-service/.github/workflows/quality-gates-v2.yml,
    strategy-service/strategy_service/cli/handlers/paper_run_handler.py,
    strategy-service/strategy_service/cli/handlers/batch_rerun.py,
    strategy-service/tests/unit/cli/handlers/test_batch_rerun.py,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
supersedes:
superseded_by:
depends_on:
source: production_verification_debt_audit_2026_08_15
assigned_role: backend_engineer
drift_direction: advance-code
---

# strategy-service Verification-Debt Findings (2026-08-15 Audit)

> Read-only verification audit of production commits already shipped in strategy-service. No fixes were applied —
> findings are scoped below for AO dispatch to decide execution order. Small plan (3 todos); the archival step is folded
> into the final todo rather than spun into a separate companion finalize plan, per `task_template.md` §4's
> single-todo-scale exception (disproportionate overhead for this size).

## Findings → todos

- [x] ✅ [INFRA] P1. Add `deployment-service` to strategy-service's `.github/workflows/quality-gates-v2.yml` `dep_repos`
      list (currently `"unified-trading-library unified-api-contracts"`) so the clients.yaml coverage gate
      (`test_clients_yaml_coverage_gate.py`) stops unconditionally `pytest.skip`-ing in real CI. Today
      `_deployment_service_strategy_config_root()` in `clients_yaml_coverage.py` always resolves `None` in CI because
      the sibling checkout the reusable workflow clones never includes `deployment-service` — the test then skips
      regardless of how many archetypes are uncovered, so the gate's own hard-fail assertion logic (confirmed correct)
      never actually gets to run against real data. Repo: strategy-service. Done-when: a `quality-gates-v2` CI run's log
      shows the clients.yaml coverage test actually EXECUTED (not skipped) — cite the run URL/ID and the log line. —
      strategy-service@610fa77d + unified-trading-pm (`extra-dep-repos.txt`: `strategy-service: deployment-service`,
      re-rendered via `rollout-workflow-templates.sh`). Verified via `workflow_dispatch` run
      https://github.com/IggyIkenna/strategy-service/actions/runs/31897443696 (SUCCESS): log shows
      `Cloning deployment-service at live-defi-rollout HEAD` +
      `Installing test-only sibling dep not in pyproject: ../deployment-service` +
      ` + deployment-service==0.1.dev1+gaad3a3743`; final tally `6014 passed, 248 skipped` — the 11 distinct skip
      reasons printed (summing to exactly 248) do NOT include `test_clients_yaml_coverage_gate.py` or its
      `deployment-service not checked out` skip message, confirming the gate test ran for real (not skipped) and passed.

- [ ] [BACKEND] P2. Add a missing-entry test case to `test_clients_yaml_coverage_gate.py` that constructs a
      clients.yaml-shaped input with one archetype's entry deliberately removed and asserts `uncovered_archetypes()`
      returns it non-empty (i.e. the existing `assert not violations` line would actually fail on real bad data) — today
      the single test only exercises the clean, 0-violation path. Repo: strategy-service. Done-when: the new test is
      present, and manually stubbing `clients_yaml_coverage.py`'s detection logic to always return `[]` makes this new
      test fail (verify locally, do not ship the stub).

- [ ] [BACKEND] P1. Add a negative-control test proving `run_paper()`'s ε=0 reconciliation actually detects a divergence
      when `dynamic_universe_as_of_dates` mismatches between the paper and batch-rerun sides. Today `deterministic`
      (`batch_rerun.py`) is computed solely from `paper_fills`/`batch_fills` comparison — the field is never itself
      compared, so a broken `as_of_date` wiring (e.g. the `_FUNDING_ARCHETYPES` conditional in `paper_run_handler.py`
      silently not firing, or `get_resolved_carry_universe_as_of_date()` always returning `None`) would pass every
      existing test unnoticed. The code's own comment in `batch_rerun.py` already acknowledges this is "a real remaining
      gap, not one this pass-through closes." Repo: strategy-service. Done-when: a new test in
      `tests/unit/cli/handlers/test_batch_rerun.py` sets a deliberately mismatched `as_of_date` on one side and asserts
      the reconciliation surfaces it (either `deterministic=False` or an explicit new comparison field/warning); once
      all three todos above are `[x]`, run the standard archival ritual on this doc (git mv to `plans/archive/2026_08/`,
      corpus-wide referrer fixup) in the same commit that flips this checkbox.

## Progress Log

- **2026-08-15**: Filed from a read-only production-verification-debt audit (8-item priority list, this doc covers the 4
  strategy-service items). `venue_capabilities` typed migration (c95473c3/UAC@b6887df5) and the 8c11e2fc shadow-SSOT
  collision resolution were both independently verified CORRECT with no stragglers or dropped members — no todos filed
  for those two. Companion docs from the same audit: `execution_service_verification_debt_findings_2026_08_15.md`,
  `pm_archive_false_done_and_review_backlog_2026_08_15.md`.
