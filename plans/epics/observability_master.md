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
last_updated: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md
  - ../archive/2026_05/alerting_service_live_rules_2026_05_07.md
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
  - ../active/incident_gateway_and_state_machine_2026_05_23.md
  - ../active/agent_recovery_controller_layer0_deterministic_2026_05_23.md
  - ../active/ai_recovery_audit_signoff_agent_2026_05_23.md
  - ../active/reconciliation_age_tracking_and_escalation_2026_05_23.md
  - ../active/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md
  - ../active/connectivity_dependency_buffer_policy_2026_05_23.md
  - ../active/audit_acknowledgement_sla_and_state_2026_05_23.md
  - ../active/independent_fallback_twilio_voice_2026_05_23.md
  - ../active/physical_pager_research_and_webhook_prototype_2026_05_23.md
  - ../active/incident_runbooks_and_evidence_store_2026_05_23.md
  - ../active/deployment_ui_safety_ops_tab_2026_05_23.md
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

| Doc                                                         | Owns                                                                                                                          |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `codex/05-infrastructure/live-deployment-monitoring.md`     | Per-archetype heartbeat thresholds; STARTED/progress/STOPPED/FAILED event cadence; cross-cloud event-stream parity            |
| `codex/03-observability/alerting.md`                        | AlertSeverity enum (CRITICAL/HIGH/WARN/INFO) → PagerDuty P-tier → routing channels                                            |
| `codex/04-architecture/kill-switch-circuit-breaker.md`      | Kill-switch alerting; circuit-breaker trigger → auto-STOPPED event; alert escalation on arm                                   |
| `codex/04-architecture/autonomous-recovery-matrix.md`       | Decision tree — every failure scenario × every recovery action                                                                |
| `codex/04-architecture/incident-gateway-state-machine.md`   | **NEW 2026-05-23** — 13-state incident lifecycle (DETECTED → … → CLOSED); audit-ack queue; dedup-key                          |
| `codex/04-architecture/recovery-defence-in-depth-layers.md` | **NEW 2026-05-23** — 5-layer model: L0 Python → L1 LLM audit → L2 PagerDuty → L3 Twilio voice → L4 pager → L5 human audit ack |
| `codex/05-infrastructure/disaster-recovery.md`              | RTO/RPO targets, Tier 0-3 recovery, restore from manifest (existing — extended 2026-05-23)                                    |
| `codex/05-infrastructure/physical-pager-layer.md`           | **NEW 2026-05-23** — Pager device comparison, webhook prototype, Twilio voice bridge                                          |
| `codex/15-runbooks/alerting/pagerduty-escalation-policy.md` | Ikenna 14:30–02:30 UK / Harsh 02:30–14:30 UK; PagerDuty escalation ladder                                                     |
| `codex/15-runbooks/alerting/audit-acknowledgement-flow.md`  | **NEW 2026-05-23** — 6h audit-ack SLA + secondary-human + founder fallback                                                    |
| `codex/05-infrastructure/manifest-consolidator-ssot.md`     | Manifest consolidator freshness alerts; silence > 120s → CRITICAL                                                             |
| `codex/02-data/data-pipeline-correctness-hard-rule.md`      | Layer freeze on RED data audit; slot-reassignment trigger                                                                     |

## Assigned active plans

_13 active plans declare `parent_epic: observability_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate (May-23 cutover)

### [`alerting_service_live_rules_2026_05_07`](../archive/2026_05/alerting_service_live_rules_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-9 complete: AlertCode taxonomy + LIVE_ALERT_RULES + DART Active Alerts panel + 15 per-AlertCode runbooks + Phase 7 quietness baseline VM running. Phase 8 rehearsal + Telegram token rotation + PagerDuty setup BLOCKED-OPERATOR. · **estimate**: 13.2 cal AI-days (class: design)

### [`incident_gateway_and_state_machine_2026_05_23`](../active/incident_gateway_and_state_machine_2026_05_23.md)

**status**: active · **estimate**: 10.8 cal AI-days (class: design) · **NEW 2026-05-23** — 13-state machine (DETECTED →
… → CLOSED), audit-ack queue, dedup-key, `AUTO_ACTION_SUCCEEDED ≠ RESOLVED` invariant.

### [`agent_recovery_controller_layer0_deterministic_2026_05_23`](../active/agent_recovery_controller_layer0_deterministic_2026_05_23.md)

**status**: active · **estimate**: 14.0 cal AI-days (class: brand-new) · **NEW 2026-05-23** — 10 closed-set
deterministic recovery scripts (restart/redeploy/resize/failover/pause/cancel/disable-venue/safe-mode/readonly-recon)

- structured AgentActionEvent.

### [`ai_recovery_audit_signoff_agent_2026_05_23`](../active/ai_recovery_audit_signoff_agent_2026_05_23.md)

**status**: active · **estimate**: 12.0 cal AI-days (class: brand-new) · **NEW 2026-05-23** — agent-orchestrator
custom-role agent that audits every AgentActionEvent, writes signoff doc, can DISPUTE, acts as Layer-1.5 backup actuator
when Layer-0 fails.

### [`reconciliation_age_tracking_and_escalation_2026_05_23`](../active/reconciliation_age_tracking_and_escalation_2026_05_23.md)

**status**: active · **estimate**: 4.0 cal AI-days (class: refactor) · **NEW 2026-05-23** — age fields + 12-dimension
separation + 15-min SEV1 + 30-min SEV0 + 7 immediate-SEV0 overrides + freeze-on-recon-risk.

### [`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`](../active/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md)

**status**: active · **estimate**: 9.6 cal AI-days (class: design) · **NEW 2026-05-23** — per-strategy 7-threshold
closed set + expected_drawdown_model + response_policy + drawdown investigation report + idempotent close-all script
contract + liquidation event + liquidation-risk pre-detection.

### [`connectivity_dependency_buffer_policy_2026_05_23`](../active/connectivity_dependency_buffer_policy_2026_05_23.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: design) · **NEW 2026-05-23** — 5-class dependency taxonomy

- per-dependency YAML policy + expected_time + buffer escalation rule.

### [`audit_acknowledgement_sla_and_state_2026_05_23`](../active/audit_acknowledgement_sla_and_state_2026_05_23.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: design) · **NEW 2026-05-23** — 6h default SLA + per- severity
override + secondary-human + founder fallback + operational-ack-vs-audit-ack distinction.

### [`independent_fallback_twilio_voice_2026_05_23`](../active/independent_fallback_twilio_voice_2026_05_23.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: infra) · **NEW 2026-05-23** — Twilio voice/SMS as independent
fallback for primary-provider-down + SEV0-no-ack + continuous primary-provider health probe.

### [`physical_pager_research_and_webhook_prototype_2026_05_23`](../active/physical_pager_research_and_webhook_prototype_2026_05_23.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: research) · **NEW 2026-05-23** — comparison matrix (4-6
candidates) + webhook prototype + Twilio voice bridge as permanent fallback.

### [`incident_runbooks_and_evidence_store_2026_05_23`](../active/incident_runbooks_and_evidence_store_2026_05_23.md)

**status**: active · **estimate**: 8.4 cal AI-days (class: design) · **NEW 2026-05-23** — 22 incident-level runbooks
(RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT) + evidence store schema + config_hash + code_version + runbook_version
linked per incident.

### [`deployment_ui_safety_ops_tab_2026_05_23`](../active/deployment_ui_safety_ops_tab_2026_05_23.md)

**status**: active · **estimate**: 8.0 cal AI-days (class: brand-new) · **NEW 2026-05-23** — Safety Ops tab in
deployment-ui/DART surfacing every Layer-0 + Layer-1 action as manual buttons with typed-confirm pattern; manual actions
also flow through the incident state machine.

## P1 — important; post-current-gate

_(no plans currently assigned at this priority. Post-cutover audits will spawn P1 items here.)_

## P2 — useful; opportunistic

### [`alerting_runbook_and_operator_ux_post_cutover_2026_05_12`](../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)

**status**: in archive (status: active in frontmatter — needs archival sweep; link corrected 2026-05-22) · **estimate**:
2.4 cal AI-days (class: design)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Archived plans

### [`alerting_service_live_rules_2026_05_07`](../archive/2026_05/alerting_service_live_rules_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-9 complete. Phase 7 quietness baseline VM running until ~2026-05-24 08:32 UTC.

**Deferred (migrated):**
- **Phase 4 — CRITICAL: rotate Telegram bot token (OPERATOR ACTION)**: Token leaked in Tab L httpx log. Rotate via @BotFather + re-push to GCP SM + AWS SM.
- **Phase 4 — PagerDuty + Slack credential push**: DEFERRED-PER-DECISION; operator triages post-Phase 7 baseline.
- **Phase 7 — 48h baseline FP analysis (OPERATOR ACTION)**: VM `alerting-quietness-20260522-083225` runs until ~2026-05-24. If FP > 10%/24h, file threshold-adjustment task.
- **Phase 8 rehearsal (OPERATOR ACTION)**: Run `inject_synthetic_alert.py` for all 15 alert codes + fill sign-off doc `REHEARSAL_2026_05_23.md`.
- **Phase 9 — 7-day soak daily review (OPERATOR ACTION)**: Monitor FP rate post-cutover; threshold re-tune if needed.
