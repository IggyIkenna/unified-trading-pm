---
name: trading_agent_master
title: "Trading Agent Master"
type: epic
tier: L2
status: active
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/trading_agent_service_architecture_unlock_2026_05_22.md
---

# Trading Agent Master

**Owns**: trading-agent-service closed-loop allocator + AllocationDirective + PnL stream consumer

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Assigned active plans

_1 active plans declare `parent_epic: trading_agent_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

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
