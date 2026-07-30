---
doc_type: plan
title: E2E coverage gaps (alerting/deployment/trading-agent) — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md, reclassified `assigned_vm: NA ->
  planning` by the na-eligibility-audit infra-tranche run 2026-07-30 (retroactive-reclassification shape, codex
  ao-dispatch-batch-naming-and-conflict-check.md §1(b)). Once the source doc's 3 E2E-harness-build todos
  (alerting-service, deployment-service, trading-agent-service) are done, verifies each harness actually exercises the
  itemized coverage the source doc's own Context section names, then checks archival eligibility.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [alerting-service, deployment-service, trading-agent-service]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md,
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

# E2E coverage gaps (alerting/deployment/trading-agent) — finalize

> **Machine-gated on `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue this plan's todo until the parent's 3 todos are done.

## Todos

- [ ] [DOC] P2. **Verify each of the 3 new E2E harnesses against the parent doc's own itemized coverage list, then check
      archival eligibility.** Once all 3 service-specific harness todos are `[x]`: (1) for each of alerting-service
      (subscriber→rules→notifiers, alert lifecycle, api/routes query, multi-venue aggregation), deployment-service, and
      trading-agent-service, confirm the shipped test actually exercises every item the parent doc's own Context section
      named for that service — re-run the suite and cite the real pass output, not a summary. (2) Grep the parent doc's
      remaining `- [ ]` items; if zero remain, run the standard 6-step archival ritual on it + this finalize plan.
      **Done when**: all 3 harnesses are verified against their doc's own stated coverage lists with a real test-run
      citation, and both this finalize plan + its parent are archived if the parent has zero open todos left.
