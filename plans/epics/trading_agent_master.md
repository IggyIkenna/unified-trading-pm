---
name: trading_agent_master
type: epic
tier: L2
status: active
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
owner: ikenna
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
asset_group: cross-cutting
related_plans:
  - ../active/trading_agent_service_architecture_unlock_2026_05_22.md

---

# Trading Agent Master

**Owns**: trading-agent-service closed-loop allocator + AllocationDirective + PnL stream consumer

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Assigned active plans

_1 active plans declare `parent_epic: trading_agent_master` in their frontmatter. Workers pick up in priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`trading_agent_service_architecture_unlock_2026_05_22`](../active/trading_agent_service_architecture_unlock_2026_05_22.md)
**status**: in-progress · **estimate**: 3.2 cal AI-days (class: refactor)

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

_(no plans currently assigned at this priority)_

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

