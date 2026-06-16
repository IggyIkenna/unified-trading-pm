---
scope: [admin, engineer]
last_reviewed: 2026-05-23
authoritative_for: [incidents-runbook-index]
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
---

# Incident Runbooks Index

> Procedure-oriented runbooks per `plans/active/issues/disaster_recovery.md` §15.
>
> **Distinct from the per-AlertCode runbooks** under `codex/15-runbooks/alerting/` — those answer "what does this alert
> mean?"; these answer "how do I handle this kind of incident, regardless of which alert fired?". Both are linked from
> the `runbook_id` field on every IncidentEnvelope.

## 22 runbooks

### Core incident handling

- [RB-INC-001 SEV0 Incident Handling](rb_inc_001.md)
- [RB-INC-002 SEV1 Investigation Handling](rb_inc_002.md)
- [RB-INC-003 Audit Acknowledgement Handling](rb_inc_003.md)

### Reconciliation

- [RB-RECON-001 Position Reconciliation Lag](rb_recon_001.md)
- [RB-RECON-002 Open Order Uncertainty](rb_recon_002.md)
- [RB-RECON-003 Balance/Collateral Mismatch](rb_recon_003.md)

### Risk

- [RB-RISK-001 Strategy Drawdown Investigation](rb_risk_001.md)
- [RB-RISK-002 Liquidation Event](rb_risk_002.md)
- [RB-RISK-003 Liquidation Risk / Margin Danger](rb_risk_003.md)
- [RB-RISK-004 Strategy Safe Mode](rb_risk_004.md)

### Connectivity

- [RB-CONN-001 Exchange WebSocket Degradation](rb_conn_001.md)
- [RB-CONN-002 Exchange REST API Failure](rb_conn_002.md)
- [RB-CONN-003 Internal Messaging Lag](rb_conn_003.md)
- [RB-CONN-004 Database/Storage Degradation](rb_conn_004.md)
- [RB-CONN-005 Alert Provider Failure](rb_conn_005.md)

### Deployment + infrastructure

- [RB-DEPLOY-001 Production Rollback](rb_deploy_001.md)
- [RB-INFRA-001 OOM Recovery](rb_infra_001.md)
- [RB-INFRA-002 Machine/Node Failure](rb_infra_002.md)
- [RB-INFRA-003 Secret/Config Failure](rb_infra_003.md)

### Alerting hardware

- [RB-ALERT-001 Dedicated On-Call Phone Setup](rb_alert_001.md)
- [RB-ALERT-002 Physical Siren/GSM Alarm Setup](rb_alert_002.md)
- [RB-ALERT-003 Satellite / No-Signal Fallback](rb_alert_003.md)

## Governance fields

Every runbook MUST declare `owner` / `cadence` / `verifier` / `last_executed` in frontmatter per CLAUDE.md "Runbook
Execution-Owner SSOT" HARD RULE.

Updated 2026-05-23: initial 22 runbooks landed alongside the disaster-recovery target operating model implementation
(Tier-1-4 ship).
