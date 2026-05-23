---
name: execution_master
title: "Execution Master"
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
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# Execution Master

**Owns**: execution-service: handlers + transfers + treasury coordinator + custody integration + flash loan + matching
engine

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## P0 — must complete before next foundation gate

### [`workspace_qg_sweep_2026_05_23`](../active/workspace_qg_sweep_2026_05_23.md) — execution-service cluster

**status**: 🟠 ACTIVE — QG sweep for execution-service (20 ruff errors) + trading-agent-service (ruff clean). Run
`bash scripts/quality-gates.sh` exit 0 in each. PREREQ: UTL QG green. [vm: vm-trading-core]

## Assigned active plans

_(no other active plans currently declare `parent_epic: execution_master`. Audit-pool wrapper plans for this epic land
here as they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_
