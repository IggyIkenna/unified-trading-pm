---
doc_type: plan
title: Client Vehicle Type (SMA vs Pooled Fund) — Finalize
summary:
  Gated finalize plan for client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20 — reconciles evidence and runs
  the 6-step archival ritual once every todo in the source plan is done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, fund-administration-service, unified-api-contracts]
scope: [engineer]
tags: [vehicle-eligibility, sma, fund-administration, finalize, archival]
related: [/plans/active/client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: companion finalize plan per task_template.md §4 STRICT rule, 2026-08-20
context_scope:
  [
    /plans/active/client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Client Vehicle Type (SMA vs Pooled Fund) — Finalize

**Why this doc exists**: `task_template.md`'s STRICT rule requires a gated finalize companion for every
`assigned_vm: planning` plan — this reconciles the source plan's evidence and runs the archival ritual so the source
plan doesn't sit `active` with zero open todos.

## Todos

- [ ] [REVIEW] P1. Reconcile every completed todo in `client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md`
  against its cited evidence (commit SHA, test name) — re-verify each cited commit actually exists and contains the
  claimed change. Done-when: every `[x]` todo's evidence is independently re-confirmed, or a discrepancy is logged
  and routed back to a new todo.

- [ ] [REVIEW] P1. Confirm todo 1's `ClientConfig` home decision (strategy_service's `ClientConfigRegistry` vs a
  fund-administration-service-local copy) didn't leave the OTHER `ClientConfig` type
  (`unified_api_contracts/internal/reporting/client_config.py`) silently out of sync — if `client-reporting-api`'s
  registry needs `vehicle_type` too for its own NAV/reporting views, spin that into a new tracked todo rather than
  leaving a second client-config surface without the field.

- [ ] [DOC] P2. Run the 6-step archival ritual on
  `client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md` once every one of its todos is `[x]` and unlocked:
  dated archive folder move, exact-successor banner, corpus-wide referrer-path fixup. Done-when: `git mv` lands the
  source plan into `plans/archive/2026_08/` and `run_hygiene_sweep.sh` shows zero broken referrers to its old path.

## Progress Log

- **2026-08-20**: Finalize plan authored alongside its source plan per the STRICT companion-finalize-plan rule.
