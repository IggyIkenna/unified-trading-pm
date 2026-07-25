---
doc_type: epic
title: Trading Agent Master
summary: >-
  L2 everlasting epic owning trading-agent-service: the closed-loop allocator, AllocationDirective pipeline, and
  StrategyPnlStreamEvent consumer. Architecture-unlock (directive pipeline + event contracts + UAC schema + codex SSOT)
  shipped 2026-05-23; P3 backlog covers real allocator logic, ML/LLM subscribers, and performance_features passthrough.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [trading-agent-service]
scope: [engineer, admin]
tags: [trading-agent, strategy, execution, orchestrator, reconciliation, ml]
related: [../archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md] # was: ../active/trading_agent_service_architecture_unlock_2026_05_22.md -- corrected 2026-07-14, verify-rerun-2 finding 230: plan archived 2026-05-23, path never existed under active/ post-archival, body (line ~50) already used the correct archive path
created: 2026-05-21
name: trading_agent_master
tier: L2
priority: P0
assigned_vm: planning # corrected 2026-07-21 (plan-reconcile) — legacy multi-VM host id, deprecated 2026-06-27
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: []
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Trading Agent Master

**Owns**: trading-agent-service closed-loop allocator + AllocationDirective + PnL stream consumer

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Assigned active plans

_(no active plans currently declare `parent_epic: trading_agent_master`. Audit-pool wrapper plans for this epic land
here as they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_

## P3 — backlog (recovered 2026-07-25; completes a migration declared but never applied)

> The frontmatter summary's "P3 backlog" claim was previously untracked anywhere in this file's body — this section
> completes the migration `plans/archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md` explicitly
> declared ("MIGRATED FROM: this plan → `plans/epics/trading_agent_master.md` P3") but that never actually landed here.
> No active plan currently carries these items — they are backlog prose only, not yet forked into a dispatchable plan.

- **Real allocator logic** (post-cutover successor to the May-23 no-op directive emission, Phase 6) — was tracked in the
  now-`SUPERSEDED` `plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md` Phase 10.7; needs a live successor
  plan/epic before this is dispatchable.
- **ML/LLM subscribers** — real derivations replacing the May-23 STUB subscribers (Phase 6); was tracked at epic Phase
  10.7 + an `ml_repo_consolidation` plan (status not re-verified in this pass).
- **`performance_features` passthrough** — real rolling sharpe/drawdown/attribution replacing the May-23 passthrough
  stub (Phase 3), scoped to the Allocator service post-cutover. Note: `plans/epics/features_and_ml_master.md`'s archived
  `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19` records its own Phase-H "`performance_features`
  passthrough... complete" — that is the features-service COMPUTE side; whether it also satisfies this
  trading-agent-service CONSUME-side item was not re-verified in this pass.
