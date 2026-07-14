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
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: [../archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md] # was: ../active/trading_agent_service_architecture_unlock_2026_05_22.md -- corrected 2026-07-14, verify-rerun-2 finding 230, same dangling-ref fix as `related:` above
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

_0 active plans declare `parent_epic: trading_agent_master` in their frontmatter (was: stale auto-gen count of "1" — the
only plan declaring it, `trading_agent_service_architecture_unlock_2026_05_22`, is `status: complete` /
`✅ ARCHIVED 2026-05-23`, see P0 below). Workers pick up in priority order (P0 first) once a new child plan is filed.
Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`. **Sync 2026-07-12** (finding 334, §A2 B-queue
ruling): corrected the count so a dispatcher scanning epic summaries doesn't read "1 active" as live work when the epic
currently has zero._

## P0 — must complete before next foundation gate

### [`trading_agent_service_architecture_unlock_2026_05_22`](../archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-8 complete: directive pipeline + event contracts + UAC schema + codex SSOT
shipped. Phase 7 CI wired locally (GH_PAT rotation BLOCKED-OPERATOR). · **estimate**: 3.2 cal AI-days (class: refactor)

**Deferred (MIGRATED FROM archived plan)** — P3 backlog, post-cutover:

- No-op directive emission (Phase 6): real allocator logic; previously pointed at SUPERSEDED epic Phase 10.7
- STUB ML/LLM subscribers (Phase 6): real derivations → `ml_repo_consolidation` + Allocator service
- `performance_features` passthrough (Phase 3): rolling sharpe/drawdown/attribution → Allocator service
- Phase 7 CI (GH_PAT rotation): `BLOCKED-OPERATOR` — unit tests + scaffold ship; CI triggers on PAT rotation

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

_(no plans currently assigned at this priority)_

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
