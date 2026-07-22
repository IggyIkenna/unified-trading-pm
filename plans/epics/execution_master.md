---
doc_type: epic
title: Execution Master
summary:
  L2 epic owning execution-service — order/transfer handlers, treasury coordinator, custody integration, flash loans,
  the matching engine, MEV protection, and per-incident recon-freeze signal emission consumed by alerting-service.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, trading-agent-service]
scope: [engineer, admin]
tags: [execution, defi, quality-gates, escalation, live-trading]
related:
  [
    ../active/execution_fidelity_tiers_uac_governed_2026_06_28.md,
    ../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../active/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md,
  ]
created: 2026-05-21
name: execution_master
tier: L2
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: []
last_updated: 2026-07-12 # was 2026-05-21 (stale vs 2026-07-12 body edits, line 57) — see body "Assigned active plans" note
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Execution Master

> **🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation** (guardrails phase:
> [`utl_reuse_phase0_guardrails_2026_07_13`](../archive/2026_07/utl_reuse_phase0_guardrails_2026_07_13.md); compose
> phases: `utl_reuse_phase1_strategy_risk_hwm_2026_07_13` (strategy risk/HWM),
> `utl_reuse_phase3_ml_model_registry_2026_07_13` (ml ModelRegistry),
> `utl_reuse_phase4_features_builder_registry_2026_07_13` (features builder_registry)). Concurrent slots: do not
> re-touch the strategy risk-eval, ml-registry, or features-builder-registry surfaces until those phase plans land —
> check them first.

**Owns**: execution-service: handlers + transfers + treasury coordinator + custody integration + flash loan + matching
engine

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## P0 — must complete before next foundation gate

### [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — execution-service cluster

**status**: 🟠 ACTIVE — QG sweep for execution-service (20 ruff errors) + trading-agent-service (ruff clean). Run
`bash scripts/quality-gates.sh` exit 0 in each. PREREQ: UTL QG green. [vm: vm-trading-core]

- [ ] [CODE] P1. **G12 (execution-side) — emit per-incident recon-freeze signals** that the alerting-service publisher
      (owned in `observability_master`) consumes: symbol-scoped for symbol breaks, account-wide for account-level SEV0s.
      In-scope for May-23. Repo: execution-service. From
      `archive/issues/recon_freeze_armed_never_published_2026_05_27.md`. **Escalated P2→P0 2026-07-12 by operator
      ruling** (plan-reconciliation Q&A finding 367): subscriber code confirmed absent in execution-service; live orders
      currently NEVER blocked by recon-freeze state — safety gap on the passed May-23 critical path; alerting-service
      twin already shipped P0. See plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2.

## P2 — opportunistic / post-cutover (slot 7 dispatch 2026-06-01)

- [ ] [CODE] P2. **F-32 — size-based MEV auto-escalation (post-cutover).** Operator decision 2026-06-01: MEV mode is
      **directive-driven** for May-23 (F-32 closed for the cutover). Post-cutover, add size-based auto-escalation of MEV
      protection. Repo: execution-service. From `archive/issues/audit03_ikenna_review_routing_2026_05_22.md`.
- G12 escalated to P0 2026-07-12 (see P0 section).

## Assigned active plans

_(no active plans currently declare `parent_epic: execution_master`. Audit-pool wrapper plans for this epic land here as
they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_
