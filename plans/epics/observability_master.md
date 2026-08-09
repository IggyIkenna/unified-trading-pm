---
doc_type: epic
title: Observability Master
summary:
  L4 cross-cutting epic owning alerting-service + monitoring/telemetry + the Incident Gateway 13-state machine + the
  5-layer recovery defence-in-depth (L0 Python scripts → L1 LLM audit → L2 PagerDuty → L3 Twilio voice → L4 pager → L5
  human ack) + kill-switch/drawdown alerting + the deployment-UI Safety Ops manual-override tab + runbook governance.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-ui]
scope: [engineer, admin]
tags: [observability, monitoring, escalation, self-healing, slack, runbook, live-trading, ui]
related:
  [
    ../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md,
    ../archive/2026_05/alerting_service_live_rules_2026_05_07.md,
    ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../archive/incident_gateway_and_state_machine_2026_05_23.plan.md,
    ../archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
    ../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md,
    ../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md,
    ../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md,
    ../archive/2026_05/connectivity_dependency_buffer_policy_2026_05_23.md,
    ../archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md,
    ../archive/independent_fallback_twilio_voice_2026_05_23.plan.md,
    ../archive/2026_05/physical_pager_research_and_webhook_prototype_2026_05_23.md,
    ../archive/2026_05/incident_runbooks_and_evidence_store_2026_05_23.md,
    ../archive/2026_05/deployment_ui_safety_ops_tab_2026_05_23.md,
    ../active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md,
  ]
created: 2026-05-21
name: observability_master
tier: L4
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/artifact_pipeline_observability_2026_07_17.md
  - ../active/consolidator_throughput_backlog_monitor_2026_07_09.md
  - ../active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md
  - ../active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md
  - ../active/data_pipeline_alert_substrate_residual_2026_07_24.md
  - ../active/data_pipeline_alerts_batch_remediation_2026_07_15.md
  - ../archive/2026_07/data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md
  - /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md
  - ../active/data_pipeline_self_healing_completion_residual_2026_07_24.md
  - ../active/deployment_registry_firestore_migration_2026_07_14.md
  - ../active/deployment_registry_firestore_p0_unblock_2026_07_14.md
  - ../active/deployment_registry_firestore_p3_cutover_2026_07_14.md
  - ../active/deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md
  - ../active/monitoring_control_plane_master_2026_06_10.md
  - ../active/orchestrator_vm_e2e_hardening_2026_07_24.md
last_updated: 2026-06-19
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Observability Master

**Owns**: alerting-service + monitoring + telemetry + **Incident Gateway state machine** + **Agent Recovery Controller
(Layer-0 deterministic scripts)** + **LLM recovery-audit-signoff agent (Layer-1)** + **reconciliation age tracking** +
**drawdown + liquidation policy + strategy risk config** + **connectivity dependency buffers** + **alert-provider
health + Twilio voice fallback (Layer-3)** + **physical pager layer (Layer-4)** + **audit acknowledgement SLA
(Layer-5)** + **deployment-UI Safety Ops tab (manual override)** + 3am-auto-recovery agent + QG snapshot cron + runbook
governance.

**Status**: P0-expanded 2026-05-23 — 11 new active plans landed from
[`../audit/results/observability_disaster_recovery_audit_2026_05_23.md`](../audit/results/observability_disaster_recovery_audit_2026_05_23.md)
(gap analysis vs target model in [`../active/issues/disaster_recovery.md`](../active/issues/disaster_recovery.md)).
Total ~86 cal AI-days dispatched across slots for May-23 cutover.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                          | Owns                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/codex/05-infrastructure/live-deployment-monitoring.md`     | Per-archetype heartbeat thresholds; STARTED/progress/STOPPED/FAILED event cadence; cross-cloud event-stream parity                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `/codex/03-observability/alerting.md`                        | AlertSeverity enum (CRITICAL/HIGH/WARN/INFO) → PagerDuty P-tier → routing channels                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `/codex/04-architecture/kill-switch-circuit-breaker.md`      | Kill-switch alerting; circuit-breaker trigger → auto-STOPPED event; alert escalation on arm                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `/codex/04-architecture/autonomous-recovery-matrix.md`       | Decision tree — every failure scenario × every recovery action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `/codex/04-architecture/incident-gateway-state-machine.md`   | **NEW 2026-05-23** — 13-state incident lifecycle (DETECTED → … → CLOSED); audit-ack queue; dedup-key                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `/codex/04-architecture/recovery-defence-in-depth-layers.md` | **NEW 2026-05-23** — 5-layer model: L0 Python → L1 LLM audit → L2 PagerDuty → L3 Twilio voice → L4 pager → L5 human audit ack                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `/codex/05-infrastructure/disaster-recovery.md`              | RTO/RPO targets, Tier 0-3 recovery, restore from manifest (existing — extended 2026-05-23)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `/codex/15-runbooks/physical-pager-layer.md`                 | **NEW 2026-05-23** — Pager device comparison, webhook prototype, Twilio voice bridge                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `/codex/15-runbooks/alerting/pagerduty-escalation-policy.md` | Ikenna 14:30–02:30 UK / Harsh 02:30–14:30 UK; PagerDuty escalation ladder                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md`  | **NEW 2026-05-23** — 6h audit-ack SLA + secondary-human + founder fallback                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `/codex/05-infrastructure/manifest-consolidator-ssot.md`     | Manifest consolidator freshness alerts; silence > 120s → CRITICAL — **[doc-reconciliation 2026-07-12, finding 205, §A2 B-queue ruling] STALE AS A UNIVERSAL RULE** (was: blanket 120s with no exception noted): `active/consolidator_throughput_backlog_monitor_2026_07_09.md` item 5 (`[x]`, shipped `deployment-api@90ace9f`, confirmed on `live-defi-rollout` via `git log`/`git branch --contains` in this pass) proved 120s false-degrades cefi (a daily-batch AG) and introduced a per-AG `_AG_STALENESS_BUDGET_SEC`/`_budget_for` (cefi=86400s, others default 120s). **(was: "Re-read the codex doc in this pass — it still states only the blanket 120s rule (no per-AG exception); the plan's own `[DOCS]` codex-update todo for this exact doc is still unchecked" — that claim was stale/incorrect: the plan's `[DOCS]` P2 item (`consolidator_throughput_backlog_monitor_2026_07_09.md:197`) is `[x]` DONE 2026-07-11, and the codex doc's own "Cockpit data-correctness signals..." section [WS-3, 2026-07-11] already documents the exact per-AG exception, plus a further "Corrected 2026-07-12 (finding 205)" note with `_AG_STALENESS_BUDGET_SEC={"cefi": 86400}` — both verified present. [finding 181, synced 2026-07-14])** |
| `/codex/02-data/data-pipeline-correctness-hard-rule.md`      | Layer freeze on RED data audit; slot-reassignment trigger                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

## Assigned active plans

_15 active plans declare `parent_epic: observability_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`data_pipeline_alerts_batch_remediation_2026_07_15`](../active/data_pipeline_alerts_batch_remediation_2026_07_15.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: Data-pipeline alerts batch remediation —
drive #data-pipeline-alerts to a clean/accurate state

### [`deployment_registry_firestore_migration_2026_07_14`](../active/deployment_registry_firestore_migration_2026_07_14.md)

**status**: active · **estimate**: 13 cal AI-days (class: infra) **title**: Deployment registry — migrate from
GCS-object-per-VM to Firestore (queryable, scalable, AWS-ready) — OVERVIEW

### [`deployment_registry_firestore_p0_unblock_2026_07_14`](../active/deployment_registry_firestore_p0_unblock_2026_07_14.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: Deployment registry Firestore migration —
Phase 0 — unblock prod (schedule reaper + graceful complete)

## P1 — important; post-current-gate

### [`data_feed_sla_registry_and_active_self_healing_2026_06_19`](../active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md)

**status**: active · **estimate**: 3.0 cal AI-days (class: design) **title**: Data-feed SLA registry (single SSOT) +
active feed self-healing

### [`deployment_registry_firestore_p3_cutover_2026_07_14`](../active/deployment_registry_firestore_p3_cutover_2026_07_14.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Deployment registry Firestore migration —
Phase 3 — cutover to Firestore-only + decommission the GCS registry

### [`monitoring_control_plane_master_2026_06_10`](../active/monitoring_control_plane_master_2026_06_10.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: design) **title**: Monitoring control-plane master — CI
dashboard (deployment-ui) + fleet git-health (orchestrator)

### [`orchestrator_vm_e2e_hardening_2026_07_24`](../active/orchestrator_vm_e2e_hardening_2026_07_24.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: design) **title**: Orchestrator e2e control-plane
validation + VM-from-scratch hardening

## P2 — useful; opportunistic

### [`artifact_pipeline_observability_2026_07_17`](../active/artifact_pipeline_observability_2026_07_17.md)

**status**: active · **estimate**: 10 cal AI-days (class: infra) **title**: Artifact pipeline observability — build →
artifact → deploy lineage across both clouds

### [`consolidator_throughput_backlog_monitor_2026_07_09`](../active/consolidator_throughput_backlog_monitor_2026_07_09.md)

**status**: active · **estimate**: 1.8 cal AI-days (class: design) **title**: Consolidators tab — per-AG backlog +
consolidation throughput monitor

### [`data_pipeline_ag_residual_backfill_decisions_2026_07_24`](../active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: Data-Pipeline AG Residual Backfill
Decisions — TradFi + DeFi (forked from the hardening/self-monitoring plan)

### [`data_pipeline_alert_substrate_residual_2026_07_24`](../active/data_pipeline_alert_substrate_residual_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Data-Pipeline Alert Substrate — Residual
Hardening (forked from the hardening/self-monitoring plan)

### [`data_pipeline_hardening_self_monitoring_2026_06_22`](/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md)

**status**: active · **estimate**: 18 cal AI-days (class: infra) **title**: Data-Pipeline Hardening + Self-Monitoring
(anti silent-misclassification)

### [`data_pipeline_self_healing_completion_residual_2026_07_24`](../active/data_pipeline_self_healing_completion_residual_2026_07_24.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data-Pipeline Self-Healing Completion —
Residual Actuator Wiring (forked from the hardening/self-monitoring plan)

### [`deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17`](../active/deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md)

**status**: active · **estimate**: 0.8 cal AI-days (class: refactor) **title**: deployment-ui — one URL scheme — plain
routes, retire `?tab=`

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [REVIEW] P3. WS-4 (verify): re-pull a 24–48 h `#ci-failures` window post-rollout and confirm the volume drop
      (promotion-lag re-reminds ~2 h not hourly, no green all-clears, QG failures dedup per-branch); drop the evidence
      jsonl in `alerts_audit/`. (Pure observation window — same 24–48 h wait as AO WS-E.) (FOLDED IN from
      ci_failures_channel_cleanup_2026_07_13, 2026-07-15, plan-reconcile §6 operator ruling)

## Folded-in scope 2026-07-21 (plan-reconcile consolidation pass)

- [ ] [BACKEND] P3. **LIVE/PAPER `stalled` signals — DEFERRED (scope decision 2026-07-10, needs new subsystems)**.
      Discovered while wiring the BATCH row (deployment-api@29f3be5): LIVE `stalled` needs an expected-active-window
      calendar (market-hours-aware, so an idle-but-healthy off-hours window never misfires); PAPER needs a `work_delta`
      (rows-out-delta) tracker (the D.1 rolling window @970bcdc samples `/proc` cpu/mem/disk, NOT `rows_out`, so it
      would have to be extended to carry the counter history first). **Decision**: both are genuinely NEW subsystems — a
      market calendar and a counter-history tracker — disproportionate to build for a P3 `stalled` refinement, so they
      are DEFERRED to a future phase. The current **honest-`"unknown"` degradation is confirmed correct** as the v1:
      `_composite_health_status` returns `"unknown"` for LIVE/PAPER `stalled` rather than guessing from a proxy (WS-D.0
      principle 2), and the oom-risk/`stalled` alert wiring (deployment-api@5e25dce) only fires on a REAL state, so
      nothing misfires while these stay unknown. BATCH — the one umbrella with a real signal (`object_delta`) — is
      wired + shipped. This item stays open (not a fake `[x]`) as an explicit, tracked deferral. No sibling plan under
      this epic owns VM/job work-health signals or a market-hours calendar today (checked
      `consolidator_throughput_backlog_monitor_2026_07_09.md` — different surface, backlog/throughput not
      liveness-stalled detection). (FOLDED IN from deployment_observability_expansion_2026_07_08.md, originally from
      deployment_obs_backend_kinds_health_2026_07_09, via 2026-07-15 plan-reconcile §6 operator ruling — second-hop fold
      2026-07-21, source plan archived)

## Archived plans

### [`data_pipeline_alerts_batch_remediation_closeout_2026_07_24`](../archive/2026_07/data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md)

**status**: ✅ ARCHIVED 2026-07-24 — closeout & historical narrative for
[`data_pipeline_alerts_batch_remediation_2026_07_15`](../active/data_pipeline_alerts_batch_remediation_2026_07_15.md);
all 14 todos it carried are `[x]`, 0 open. Moved from `plans/active/` to `plans/archive/2026_07/` the same day it was
extracted (plan line-cap remediation) since it was already fully-closed history, not just an over-cap trim.

### [`alerting_service_live_rules_2026_05_07`](../archive/2026_05/alerting_service_live_rules_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-9 complete. Deferred operator tasks migrated to P3 above.

### [`incident_gateway_and_state_machine_2026_05_23`](../archive/incident_gateway_and_state_machine_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped.

### [`ai_recovery_audit_signoff_agent_2026_05_23`](../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All implementable phases shipped. Operator-action items in P3.

### [`reconciliation_age_tracking_and_escalation_2026_05_23`](../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Operator smoke in P3.

### [`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`](../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Operator smoke in P3.

### [`independent_fallback_twilio_voice_2026_05_23`](../archive/independent_fallback_twilio_voice_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — Code shipped. Twilio account creation + creds in P3.
