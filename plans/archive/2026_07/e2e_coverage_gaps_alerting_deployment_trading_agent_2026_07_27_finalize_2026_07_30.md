---
doc_type: plan
title: E2E coverage gaps (alerting/deployment/trading-agent) — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md, reclassified `assigned_vm: NA ->
  planning` by the na-eligibility-audit infra-tranche run 2026-07-30 (retroactive-reclassification shape, codex
  ao-dispatch-batch-naming-and-conflict-check.md §1(b)). Once the source doc's 3 E2E-harness-build todos
  (alerting-service, deployment-service, trading-agent-service) are done, verifies each harness actually exercises the
  itemized coverage the source doc's own Context section names, then checks archival eligibility.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [alerting-service, deployment-service, trading-agent-service]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/archive/2026_07/e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
depends_on: [e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit infra tranche, dispatch agt-30721a, 2026-07-30 — retroactive reclassification of an
  already-owned assigned_vm:NA doc. Conflict-check: no active assigned_vm:planning doc in parent_epic
  plan_hygiene_master claims this content; zero overlap found in the infra tranche's consolidated-closeout digest.
---

> **🗄️ ARCHIVED 2026-07-30** — status=complete, 0 open todos (1/1 done). Archived per
> /codex/12-agent-workflow/plan-completion-and-archival-discipline.md.

# E2E coverage gaps (alerting/deployment/trading-agent) — finalize

> **Machine-gated on `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue this plan's todo until the parent's 3 todos are done.

## Todos

- [x] ✅ [DOC] P2. **Verify each of the 3 new E2E harnesses against the parent doc's own itemized coverage list, then
      check archival eligibility.** — unified-trading-pm@(this commit). All 3 parent todos were already `[x]`. Verified
      each service by (a) reading the actual e2e test file and confirming a real test class exists for every claimed
      coverage item, and (b) re-running the full suite via `bash scripts/quality-gates.sh --test --no-fix` (never pytest
      directly) and citing the real pass output: - **alerting-service**: 4/4 items confirmed as real test classes in
      `tests/e2e/test_mock_replay_e2e.py` — `TestSubscriberRulesNotifiersPipeline` (subscriber→rules→notifiers),
      `TestAlertLifecycleViaPersistence` (alert lifecycle), `TestDeliveryStatusApiAfterInjectedTrigger` (api/routes
      query), `TestMultiServiceHealthAggregation` (multi-venue aggregation). Suite run: **907 passed, 8 warnings in
      10.92s**. - **deployment-service**: 4/4 items confirmed in `tests/e2e/test_deployment_e2e.py` —
      `TestCatalogAggregationRealShardSet`, `TestDependencyGraphExecution`, `TestVmLaunchConfigResolution`,
      `TestClusterBootstrapCliMockedBackend`. Suite run: **2968 passed, 5 skipped, 8 warnings in 104.39s**. -
      **trading-agent-service**: 4/4 items confirmed in `tests/e2e/test_trading_agent_e2e.py` —
      `TestMockDrivenLoopToLedgerFill`, `TestL2SignalLoopTickDrivenExecution`, `TestReplayFixtureDeterministicOutput`,
      `TestCliMainOneFullCycleSmoke`. Suite run: **146 passed in 13.15s** (matches the parent doc's own original
      citation exactly). Grepped the parent doc for `^- \[ \]`: **zero remaining**. Codex-alignment check:
      `codex/06-coding-standards/     integration-testing-layers.md` is a general layer-strategy SSOT, not a per-service
      coverage tracker — no update needed (no new contract established, just filling an existing gap). Ran the standard
      6-step archival ritual on both this plan and its parent — see both docs' archived banners + Progress Logs.

## Progress Log

- **2026-07-30 (slot 16, backend_engineer)** — Dispatched this plan's single todo. No deferred items found to migrate
  (step 1). Verified all 3 harnesses per the todo above; all pass with real per-service suite runs. Archived both this
  plan and its parent per the 6-step ritual: added archived banners + `status: complete`; codex-alignment check found no
  contract update needed; fixed the 3 archived source docs (`e2e_testing_020/022/023_..._2026_03_22.md`) that
  forward-referenced the parent doc's now-stale `plans/active/...` path to the new `plans/archive/2026_07/...` path;
  `plans/active/INDEX.md` is auto-generated (never hand-edited) — regenerated it via
  `scripts/plans/regenerate_active_plan_index.py` to drop both entries;
  `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` is also auto-regenerated (twice-daily Cloud
  Scheduler), left untouched; `plans/active/issues/plan_reconcile_autonomous_sweep_2026_07_30.md` is a dated
  point-in-time sweep snapshot using bare slugs (not paths), left untouched as historical record. Moved both docs to
  `plans/archive/2026_07/`.
