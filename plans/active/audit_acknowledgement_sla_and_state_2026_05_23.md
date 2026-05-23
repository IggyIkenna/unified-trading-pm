---
title: "Audit-Acknowledgement SLA + State (6h default + per-severity override + secondary-human + founder fallback)"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  Design class — operator-judgment SLA values per severity + escalation ladder + operational-ack-vs-audit-ack
  distinction. Implementation is small (cron-style timer on incident state machine + DART buttons). Baseline 8 × 0.6
  design = 4.8 cal-days.
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on:
  - incident_gateway_and_state_machine_2026_05_23
  - ai_recovery_audit_signoff_agent_2026_05_23
gates:
  - master_to_live_defi_2026_05_23:Group-F
  - master_to_live_defi_2026_05_23:Group-G
related_plans:
  - incident_gateway_and_state_machine_2026_05_23.md
  - ai_recovery_audit_signoff_agent_2026_05_23.md
  - deployment_ui_safety_ops_tab_2026_05_23.md
---

# Audit-Acknowledgement SLA + State

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #7.** Closes §6 of the target
> model + operator's added requirement: "even if AI audit confirms automation was good result, human should be required
> to double check and ack within 6 hours or less or more depending on severity".

## Goal

Codify the 6h audit-ack SLA as the workspace default with per-severity override (SEV0 minutes, SEV1 < 2h, SEV2 < 6h,
SEV3 informational). Distinguish operational ack ("I'm investigating") from audit ack ("I've reviewed the report after
the system handled it"). Wire secondary-human escalation when primary on-call doesn't ack within window; founder
fallback if still unacked. Even APPROVED LLM-signoff verdict requires the human ack.

## Context

**Existing capability** (verified 2026-05-23):

- DART Active Alerts panel + Ack button (single-button — no distinction).
- PagerDuty escalation policy doc (`codex/15-runbooks/alerting/pagerduty-escalation-policy.md`).

**Missing for May-23**:

- No SLA timer enforcement.
- No operational-ack-vs-audit-ack distinction.
- No secondary-human auto-escalation when ack-window expires.
- No founder fallback.

## Pre-audit (blast radius)

- TOUCH: `incident_gateway_and_state_machine_2026_05_23.md` (already in flight) — `audit_ack_due_at` is the SLA-timer
  field. This plan adds the timer cron + escalation logic.
- NEW: `alerting-service/alerting_service/gateway/ack_escalation.py` — cron job runs every 30s, scans audit-ack queue,
  escalates breaches.
- TOUCH: `unified-trading-system-ui/components/widgets/alerts/ack-queue-widget.tsx` — surface countdown + secondary
  escalation status.
- NEW: `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — operator playbook.

## Phased execution DAG

### Phase 1 — SLA timer (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `unified_api_contracts/canonical/crosscutting/incident/sla.py`: - `AuditAckSLAPolicy` Pydantic —
      `severity: AlertSeverity, default_seconds: int, secondary_human_after_seconds:       int, founder_after_seconds: int`. -
      `LIVE_AUDIT_ACK_POLICIES: tuple[AuditAckSLAPolicy, ...]` — 4 entries: - CRITICAL: default=300 (5min),
      secondary_after=600 (10min), founder_after=1800 (30min). - HIGH: default=7200 (2h), secondary_after=10800 (3h),
      founder_after=21600 (6h). - WARN: default=21600 (6h), secondary_after=43200 (12h), founder_after=86400 (24h). -
      INFO: default=None (no enforcement).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Operator-tunable per-strategy / per-archetype overrides via `audit_ack_policy:` key in strategy
      config (operator approves stricter overrides).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. UAC sanity tests: closed set; defaults make sense; per-strategy override loads correctly.

### Phase 2 — Ack escalation cron (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.4. `alerting-service/alerting_service/gateway/ack_escalation.py` — runs every 30s: - Scan audit-ack
      queue for incidents with `audit_ack_due_at < now()` and not yet acked. - Per-incident: load SLA policy from
      severity; check elapsed time since due_at. - If `elapsed > secondary_human_after_seconds` and no secondary-page
      sent yet → trigger Layer-2 PagerDuty page to secondary on-call (Harsh if Ikenna is primary; vice versa). - If
      `elapsed > founder_after_seconds` and no founder-page sent yet → trigger Layer-3 Twilio voice call to
      founder/responsible-officer.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.5. Audit trail: each escalation step appends to `audit_ack_escalation_history` on the incident
      envelope.

### Phase 3 — Operational ack vs audit ack (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.6. UAC `IncidentEnvelope` extension —
      `operational_acked_by: str | None, operational_acked_at:     datetime | None, audit_acked_by: str | None, audit_acked_at: datetime | None`.
      Operational ack does NOT transition incident state (incident stays in its current state); audit ack transitions to
      `HUMAN_AUDIT_ACKED`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. `alerting-service` ack endpoints: `POST /incidents/{key}/operational-ack` (sets fields, no state
      transition); `POST /incidents/{key}/audit-ack` (sets fields + transitions to `HUMAN_AUDIT_ACKED`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.8. DART: `OperationalAckButton` + `AuditAckButton` as distinct components. Audit ack button is
      disabled until the AUDIT_REPORT_GENERATED state has been reached.

### Phase 4 — Even-APPROVED-requires-human-ack rule (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.9. `incident_gateway_and_state_machine` state machine: even when LLM RecoveryAuditSignoff
      verdict=APPROVED + recovery_confirmed=True, the audit-ack queue MUST hold the incident open until human audit-ack
      within the per-severity window. LLM verdict is informational; not a substitute for human ack.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.10. Integration test: simulate APPROVED LLM signoff on a SEV2 incident → assert incident remains open in
      audit-ack queue with 6h countdown; assert manual audit-ack closes it.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.11. Synthetic smoke: create a SEV2 incident → wait → at 6h+10min assert secondary-human PagerDuty page
      sent; at 24h assert founder Twilio voice call placed; manually ack → assert escalation stops.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.12. SEV0 smoke: at 10min unacked → secondary; at 30min → founder.

## Success criteria

- 4 SLA policies in UAC; per-strategy overrides load correctly.
- ack-escalation cron escalates within ±60s of due time.
- Operational ack vs audit ack distinct + tested.
- Even APPROVED LLM signoff requires human ack.
- Smoke green for both SEV0 + SEV2 escalation ladders.

## Anti-patterns + banned approaches

- ❌ Auto-closing incident on APPROVED LLM verdict — human ack always required (operator HARD RULE).
- ❌ Single Ack button — must be 2 distinct buttons.
- ❌ Escalation to non-rota humans — only primary → secondary → founder.

## Continuous verification

- Daily: query audit-ack queue + count incidents > SLA → should be 0.
- Per-incident: assert audit_ack_escalation_history rows match the timing expected by SLA.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 (IncidentEnvelope) +
`ai_recovery_audit_signoff_agent_2026_05_23` Phase 1 (SignoffVerdict).

**Blocks**: `deployment_ui_safety_ops_tab_2026_05_23` (Safety Ops tab shows ack-queue countdown).

## Codex SSOT updates

- NEW: `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — flow diagram + SLA matrix + escalation ladder.
- UPDATE: `codex/15-runbooks/alerting/pagerduty-escalation-policy.md` — add the secondary-after + founder-after
  thresholds per severity.
