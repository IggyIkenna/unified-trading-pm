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

## Codex SSOTs

| Doc                                                         | Owns                                                                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `codex/05-infrastructure/live-deployment-monitoring.md`     | Per-archetype heartbeat thresholds; STARTED/progress/STOPPED/FAILED event cadence; cross-cloud event-stream parity |
| `codex/03-observability/alerting.md`                        | AlertSeverity enum (CRITICAL/HIGH/WARN/INFO) → PagerDuty P-tier → routing channels                                 |
| `codex/04-architecture/kill-switch-circuit-breaker.md`      | Kill-switch alerting; circuit-breaker trigger → auto-STOPPED event; alert escalation on arm                        |
| `codex/15-runbooks/alerting/pagerduty-escalation-policy.md` | Ikenna 14:30–02:30 UK / Harsh 02:30–14:30 UK; PagerDuty escalation ladder                                          |
| `codex/05-infrastructure/manifest-consolidator-ssot.md`     | Manifest consolidator freshness alerts; silence > 120s → CRITICAL                                                  |
| `codex/02-data/data-pipeline-correctness-hard-rule.md`      | Layer freeze on RED data audit; slot-reassignment trigger                                                          |

## Assigned active plans

_2 active plans declare `parent_epic: observability_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`alerting_service_live_rules_2026_05_07`](../active/alerting_service_live_rules_2026_05_07.md)

**status**: active · **estimate**: 13.2 cal AI-days (class: design)

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`alerting_runbook_and_operator_ux_post_cutover_2026_05_12`](../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)

**status**: in archive (status: active in frontmatter — needs archival sweep; link corrected 2026-05-22) · **estimate**: 2.4 cal AI-days (class: design)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
