---
name: observability_master
title: "Observability Master"
type: epic
tier: L4
status: active
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md
  - ../active/alerting_service_live_rules_2026_05_07.md
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# Observability Master

**Owns**: alerting-service + monitoring + telemetry + 3am-auto-recovery agent

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Assigned active plans

_2 active plans declare `parent_epic: observability_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`alerting_service_live_rules_2026_05_07`](../active/alerting_service_live_rules_2026_05_07.md)

**status**: active · **estimate**: 13.2 cal AI-days (class: design)

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`alerting_runbook_and_operator_ux_post_cutover_2026_05_12`](../active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: design)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
