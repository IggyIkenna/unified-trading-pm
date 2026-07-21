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
