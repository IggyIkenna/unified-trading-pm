---
title: "22 Incident Runbooks + Evidence Store + config_hash + code_version + runbook_version"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 8.4
estimate_calibration_note: |
  Design class — 22 procedure-oriented runbooks + evidence store schema + cross-linking discipline. Baseline 14 = ~0.6
  cal-day per runbook × 22 + 1 cal-day store. × 0.6 design = 8.4 cal-days.
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on:
  - incident_gateway_and_state_machine_2026_05_23
  - agent_recovery_controller_layer0_deterministic_2026_05_23
gates:
  - master_to_live_defi_2026_05_23:Group-F
related_plans:
  - incident_gateway_and_state_machine_2026_05_23.md
  - agent_recovery_controller_layer0_deterministic_2026_05_23.md
  - reconciliation_age_tracking_and_escalation_2026_05_23.md
  - drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md
  - connectivity_dependency_buffer_policy_2026_05_23.md
---

# 22 Incident Runbooks + Evidence Store

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #10.** Closes §15 + §17 of the
> target model. **Distinct from the 15 per-AlertCode runbooks** already shipped by Phase 6 of
> `alerting_service_live_rules_2026_05_07.md` — these are **procedure-oriented**: "how to handle a position
> reconciliation lag" not "how to handle a `KILL_SWITCH_VENUE_DISCONNECT` alert".

## Goal

Ship 22 incident runbooks per `disaster_recovery.md` §15. Ship a queryable evidence store where every material incident
links to: raw venue API snapshot, internal ledger snapshot, order/fill records, position records, balance records, logs,
metrics, traces, agent action logs, config_hash, code_version, runbook_version, human ack trail.

## Context

**Existing capability**:

- 15 per-AlertCode runbooks (`codex/15-runbooks/alerting/{kill_switch_*,defi_*,...}.md`).
- AlertDeliveryRecord persistence to GCS.
- `_template.md` for per-AlertCode runbook shape.

**Missing for May-23**:

- 22 procedure runbooks (RB-INC-001 .. RB-ALERT-003) per target §15.
- Evidence store: incident-keyed durable store linking the 14 evidence types.
- config_hash + code_version + runbook_version stamped on every IncidentEnvelope.

## Pre-audit (blast radius)

- NEW: `codex/15-runbooks/incidents/` directory — 22 markdown files.
- NEW: UAC `IncidentEvidence` Pydantic schema in `unified_api_contracts/canonical/crosscutting/incident/evidence.py`.
- NEW: `alerting-service/alerting_service/gateway/evidence_collector.py` — collects + persists evidence per incident.
- TOUCH: every Layer-0 recovery script (from `agent_recovery_controller_layer0_deterministic_2026_05_23`) — stamp
  config_hash + code_version + runbook_version on emitted AgentActionEvent.

## Phased execution DAG

### Phase 1 — UAC schema (0.5 cal-day)

- [ ] [SCRIPT] P0.1. `IncidentEvidence` Pydantic — 14 optional URL fields per target §17:
      `raw_venue_api_snapshot_url, internal_ledger_snapshot_url, order_fill_records_url, position_records_url,     balance_records_url, logs_url, metrics_url, traces_url, agent_action_logs_url, config_hash, code_version,     runbook_version, human_acknowledgement_trail_url, additional_evidence: dict[str, str]`.
- [ ] [SCRIPT] P0.2. Link from `IncidentEnvelope`: `evidence: IncidentEvidence | None` (lazy-collected post-RESOLVED).

### Phase 2 — Evidence collector (1.5 cal-day)

- [ ] [AGENT] P0.3. `alerting-service/alerting_service/gateway/evidence_collector.py` — on incident transition to
      AUDIT_REPORT_GENERATED: - Trigger per-service evidence-capture endpoints (each service exposes
      `/evidence/{incident_key}` which writes the snapshot to GCS at `incidents/{date}/{key}/evidence/<type>.json`). -
      Capture config_hash (= git rev-parse HEAD of unified-trading-pm + service repo at incident time; deterministic
      from deployment registry). - Capture code_version (= image_digest of running container OR git sha for VM-hosted
      services). - Capture runbook_version (= git sha of `codex/15-runbooks/incidents/<runbook_id>.md` at incident
      time).
- [ ] [AGENT] P0.4. Each service registers an evidence-capture callback: execution-service
      (orders/fills/positions/balances + venue REST snapshots), strategy-service (strategy state + signals),
      batch-live-reconciliation-service (recon deltas + age fields), risk-and-exposure-service (margin/HF/exposure).

### Phase 3 — 22 incident runbooks (3 cal-days, parallel across runbooks)

Each runbook lives at `codex/15-runbooks/incidents/<runbook_id>.md` with frontmatter
`owner, cadence, verifier, last_executed` per the existing runbook-governance HARD RULE. Each follows a canonical shape:
TL;DR + symptom + diagnosis steps (concrete commands) + 3 resolution paths (auto-recovery, manual intervention,
kill-switch) + rollback

- common false-positives + escalation criteria + success criteria + post-incident actions.

* [ ] [SCRIPT] P0.5. **RB-INC-001 SEV0 Incident Handling**: ack + check current risk + identify scope + confirm safe
      mode + escalate + close.
* [ ] [SCRIPT] P0.6. **RB-INC-002 SEV1 Investigation Handling**: review agent report + confirm protected mode + decide
      continue/pause/disable/close + document.
* [ ] [SCRIPT] P0.7. **RB-INC-003 Audit Acknowledgement Handling**: what counts as ack + what must be reviewed + sign
      off + escalate insufficient report.
* [ ] [SCRIPT] P0.8. **RB-RECON-001 Position Reconciliation Lag**: check venue + check ledger + check fills/orders +
      identify oldest + apply buffer + safe-mode-vs-continue.
* [ ] [SCRIPT] P0.9. **RB-RECON-002 Open Order Uncertainty**: pull open orders + attempt cancel + confirm + handle
      unknown + escalate if cancel unproven.
* [ ] [SCRIPT] P0.10. **RB-RECON-003 Balance/Collateral Mismatch**: pull balances + check transfers/funding/fees/
      borrow + check movements + check collateral/margin + escalate unexplained.
* [ ] [SCRIPT] P0.11. **RB-RISK-001 Strategy Drawdown Investigation**: determine threshold + compare to model +
      attribute PnL + check exposure/execution/slippage/fees/funding/data-quality + recommend.
* [ ] [SCRIPT] P0.12. **RB-RISK-002 Liquidation Event**: confirm details + remaining risk + freeze/reduce + report +
      escalate.
* [ ] [SCRIPT] P0.13. **RB-RISK-003 Liquidation Risk / Margin Danger**: check margin ratio + liquidation distance +
      collateral + reduce/close + SEV0 escalate.
* [ ] [SCRIPT] P0.14. **RB-RISK-004 Strategy Safe Mode**: define per-strategy + pause new + cancel-or-retain orders +
      confirm positions/hedges + human-resume-requirements.
* [ ] [SCRIPT] P0.15. **RB-CONN-001 Exchange WebSocket Degradation**: disconnect duration + backup feed +
      order-book-freshness + pause-decision.
* [ ] [SCRIPT] P0.16. **RB-CONN-002 Exchange REST API Failure**: order placement/cancel + rate limits + auth + escalate
      if cancel unconfirmable.
* [ ] [SCRIPT] P0.17. **RB-CONN-003 Internal Messaging Lag**: check PubSub/Kafka/Redis lag + check consumers + check
      DLQ + failover/scale.
* [ ] [SCRIPT] P0.18. **RB-CONN-004 Database/Storage Degradation**: ledger writes + read-only mode + replay/recovery +
      can-continue-trading.
* [ ] [SCRIPT] P0.19. **RB-CONN-005 Alert Provider Failure**: confirm provider status + trigger fallback + Twilio
      voice + create audit incident.
* [ ] [SCRIPT] P0.20. **RB-DEPLOY-001 Production Rollback**: identify version + roll back image + verify health + verify
      trading state + audit report.
* [ ] [SCRIPT] P0.21. **RB-INFRA-001 OOM Recovery**: capture memory profile + restart/resize + check repeated OOM +
      verify recon + audit report.
* [ ] [SCRIPT] P0.22. **RB-INFRA-002 Machine/Node Failure**: cordon + move workload + verify service + verify risk.
* [ ] [SCRIPT] P0.23. **RB-INFRA-003 Secret/Config Failure**: verify config registry + verify secret access + prevent
      unsafe default + escalate if production-config-unknown.
* [ ] [SCRIPT] P0.24. **RB-ALERT-001 Dedicated On-Call Phone Setup**: carrier + apps + DND bypass + charger/UPS + test
      schedule.
* [ ] [SCRIPT] P0.25. **RB-ALERT-002 Physical Siren/GSM Alarm Setup**: trigger path + SIM + power backup + test.
* [ ] [SCRIPT] P0.26. **RB-ALERT-003 Satellite / No-Signal Fallback**: when used + who carries + test + limitations.

### Phase 4 — Runbook governance (0.5 cal-day)

- [ ] [SCRIPT] P0.27. Every runbook has 4-field frontmatter (`owner, cadence, verifier, last_executed`). Cadence:
      RB-INC, RB-RECON, RB-RISK = quarterly game-day verification. RB-CONN, RB-DEPLOY, RB-INFRA = pre-cutover
      verification. RB-ALERT = monthly.
- [ ] [SCRIPT] P0.28. Hygiene script `unified-trading-pm/scripts/plan-hygiene/check_runbook_fields.py` flags missing
      fields. Wire into daily plan-hygiene cron.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [ ] [HUMAN] P0.29. Synthetic smoke: trigger a SEV1 incident → assert evidence_collector populates all 14 evidence URL
      fields → assert config_hash / code_version / runbook_version stamped on IncidentEnvelope.
- [ ] [HUMAN] P0.30. Per-runbook walkthrough on staging: operator runs each of 22 runbooks on a synthetic incident
      matching the runbook's scope; signs off in `last_executed:` frontmatter.

## Success criteria

- 22 incident runbooks land + governance fields valid.
- IncidentEvidence schema + collector ship.
- Every IncidentEnvelope stamped with config_hash + code_version + runbook_version.
- Evidence store URLs are queryable from DART (deep-link per incident).
- Smoke + per-runbook walkthrough green.

## Anti-patterns + banned approaches

- ❌ Runbook without owner/cadence/verifier/last_executed — fails plan-hygiene.
- ❌ Evidence captured lazily after incident closes — must be collected at AUDIT_REPORT_GENERATED state.
- ❌ Runbook merging into per-AlertCode runbooks — these are distinct (procedure-oriented vs alert-oriented).

## Continuous verification

- Quarterly: game-day per RB-INC/RECON/RISK runbook; update `last_executed`.
- Pre-cutover: walk RB-CONN/DEPLOY/INFRA.
- Monthly: walk RB-ALERT.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 +
`agent_recovery_controller_layer0_deterministic_2026_05_23` Phase 1.

**Blocks**: `audit_acknowledgement_sla_and_state_2026_05_23` (audit ack package requires the runbook + evidence links).

## Codex SSOT updates

- NEW: `codex/15-runbooks/incidents/README.md` — 22 runbooks index.
- NEW: 22 individual runbooks.
- UPDATE: existing `codex/15-runbooks/alerting/README.md` — point to incidents/ section for procedure-oriented runbooks.
