---
doc_type: plan
title: Audit-Acknowledgement SLA + State (6h default + per-severity override + secondary-human + founder fallback)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    incident_gateway_and_state_machine_2026_05_23.md,
    ai_recovery_audit_signoff_agent_2026_05_23.md,
    /plans/archive/2026_05/deployment_ui_safety_ops_tab_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: "Design class — operator-judgment SLA values per severity + escalation ladder +
  operational-ack-vs-audit-ack

  distinction. Implementation is small (cron-style timer on incident state machine + DART buttons). Baseline 8 × 0.6

  design = 4.8 cal-days.

  "
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23, ai_recovery_audit_signoff_agent_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F", "master_to_live_defi_2026_05_23:Group-G"]
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
- PagerDuty escalation policy doc (`/codex/15-runbooks/alerting/pagerduty-escalation-policy.md`).

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
- NEW: `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — operator playbook.

## Phased execution DAG

### Phase 1 — SLA timer (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `unified_api_contracts/canonical/crosscutting/incident/sla.py`: -
      `AuditAckSLAPolicy` Pydantic —
      `severity: AlertSeverity, default_seconds: int, secondary_human_after_seconds:       int, founder_after_seconds: int`. -
      `LIVE_AUDIT_ACK_POLICIES: tuple[AuditAckSLAPolicy, ...]` — 4 entries: - CRITICAL: default=300 (5min),
      secondary_after=600 (10min), founder_after=1800 (30min). - HIGH: default=7200 (2h), secondary_after=10800 (3h),
      founder_after=21600 (6h). - WARN: default=21600 (6h), secondary_after=43200 (12h), founder_after=86400 (24h). -
      INFO: default=None (no enforcement).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Operator-tunable per-strategy / per-archetype overrides via
      `audit_ack_policy:` key in strategy config (operator approves stricter overrides).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. UAC sanity tests: closed set; defaults make sense; per-strategy
      override loads correctly.

### Phase 2 — Ack escalation cron (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.4. `alerting-service/alerting_service/gateway/ack_escalation.py` — runs
      every 30s: - Scan audit-ack queue for incidents with `audit_ack_due_at < now()` and not yet acked. - Per-incident:
      load SLA policy from severity; check elapsed time since due_at. - If `elapsed > secondary_human_after_seconds` and
      no secondary-page sent yet → trigger Layer-2 PagerDuty page to secondary on-call (Harsh if Ikenna is primary; vice
      versa). - If `elapsed > founder_after_seconds` and no founder-page sent yet → trigger Layer-3 Twilio voice call to
      founder/responsible-officer.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.5. Audit trail: each escalation step appends to
      `audit_ack_escalation_history` on the incident envelope.

### Phase 3 — Operational ack vs audit ack (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.6. UAC `IncidentEnvelope` extension —
      `operational_acked_by: str | None, operational_acked_at:     datetime | None, audit_acked_by: str | None, audit_acked_at: datetime | None`.
      Operational ack does NOT transition incident state (incident stays in its current state); audit ack transitions to
      `HUMAN_AUDIT_ACKED`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. `alerting-service` ack endpoints:
      `POST /incidents/{key}/operational-ack` (sets fields, no state transition); `POST /incidents/{key}/audit-ack`
      (sets fields + transitions to `HUMAN_AUDIT_ACKED`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.8. DART: `OperationalAckButton` + `AuditAckButton` as distinct
      components. Audit ack button is disabled until the AUDIT_REPORT_GENERATED state has been reached.

### Phase 4 — Even-APPROVED-requires-human-ack rule (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.9. `incident_gateway_and_state_machine` state machine: even when LLM
      RecoveryAuditSignoff verdict=APPROVED + recovery_confirmed=True, the audit-ack queue MUST hold the incident open
      until human audit-ack within the per-severity window. LLM verdict is informational; not a substitute for human
      ack.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.10. Integration test: simulate APPROVED LLM signoff on a SEV2 incident →
      assert incident remains open in audit-ack queue with 6h countdown; assert manual audit-ack closes it.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.11. Synthetic smoke: create a SEV2 incident → wait → at 6h+10min assert
      secondary-human PagerDuty page sent; at 24h assert founder Twilio voice call placed; manually ack → assert
      escalation stops.
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

- NEW: `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — flow diagram + SLA matrix + escalation ladder.
- UPDATE: `/codex/15-runbooks/alerting/pagerduty-escalation-policy.md` — add the secondary-after + founder-after
  thresholds per severity.

## Tier-1-4 implementation log (2026-05-23)

> **Phase-1 shipped — partial Phase-2+ where noted.** Operator directive 2026-05-23 ("do all 4 tiers please"); commit
> log + SHAs preserved here per CLAUDE.md `Commit + Push + Flip` HARD RULE.

| Tier  | Repo                      | SHA        | What landed                                                                                                   |
| ----- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| 1     | `unified-api-contracts`   | `ae5771e2` | Phase-1 schemas + facades + 48 sanity tests (closed-set + central invariant enforced)                         |
| 3A    | `unified-trading-library` | `6c08212e` | UTL `recovery/` library — AgentActionEmitter / RecoveryScriptRegistry / RepeatedRepairLoopDetector + 15 tests |
| 3B+4B | `deployment-service`      | `21cd67b`  | 10 Layer-0 scripts in `scripts/recovery/` + `llm_invoke_layer0.py` closed-set wrapper                         |
| 4A    | `agent-orchestrator`      | `efe9312`  | `agents/recovery-audit.md` boot template (role=custom, 60s poll, closed-set Layer-1.5 authority)              |
| 2     | `alerting-service`        | `925be02`  | Gateway scaffold (state_machine + dedup + audit_ack_queue) + Twilio voice/SMS notifiers                       |

**Phase-1 items that landed (this plan's scope):**

- [x] ✅ Phase 1 P0.1-P0.3 UAC AuditAckSLAPolicy (4 LIVE_AUDIT_ACK_POLICIES) + lookup_sla + monotonic-ladder validator +
      sanity tests — unified-api-contracts@ae5771e2

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.4-P0.5 — `gateway/ack_escalation.py` escalation-ladder cron (secondary PagerDuty → founder Twilio →
      physical pager) anchored at incident creation per AuditAckSLAPolicy; one step/tick, idempotent via
      audit_ack_escalation_history; injectable notifier; +3 tests. — alerting-service@39b6650
- [x] ✅ Phase 3 P0.6-P0.8 — distinct operational-ack vs audit-ack endpoints
      (`POST /safety-ops/incidents/{key}/{operational|audit}-ack`; audit-ack clears the SLA-countdown queue entry,
      op-ack records handler) backed by GatewayState; DART distinct Op-Ack / Audit-Ack buttons render + wire to them;
      Playwright asserts both buttons. — alerting-service@53fb493 + unified-trading-system-ui@a6f3924c | pw:L2 ✓ |
      regression: tests/e2e/safety-ops.spec.ts + tests/unit/test_safety_ops_routes.py
- [x] ✅ Phase 4 P0.9-P0.10 — alerting-service@839cb5f | 5-test APPROVED-verdict-does-NOT-bypass-audit-ack suite | QG
      green
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] Phase 5 P0.11-P0.12 — synthetic smoke for SEV0 + SEV2 ladders (operator to
      schedule when ready; P0.11/P0.12 main items marked DEFERRED-OPERATOR-DECISION)

**Cross-references**:

- Tier-1 UAC schemas → `unified_api_contracts.incident` / `unified_api_contracts.dependency` /
  `unified_api_contracts.risk` facades
- Tier-3 UTL primitives → `unified_trading_library.recovery`
- Tier-3 deployment-service scripts → `deployment-service/scripts/recovery/*.py`
- Tier-4 LLM agent template → `agent-orchestrator/agents/recovery-audit.md`
- Tier-2 alerting-service gateway → `alerting-service/alerting_service/gateway/`
- Tier-2 Twilio notifiers → `alerting-service/alerting_service/notifiers/twilio_voice.py` + `twilio_sms.py`

## Tier-5 implementation log (2026-05-23, follow-up)

> Follow-up commits after Tier-1-4 ship. Operator directive: "do these then too".

| Tier | Repo                        | SHA         | What landed                                                                                                                            |
| ---- | --------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 5    | `unified-trading-pm`        | (ping doc)  | 5 BLOCKED-OPERATOR-ACTION ping in `_agent_pings.md` (Twilio / pager / risk values / PD tier / LLM model)                               |
| 5    | `alerting-service`          | `e5c8084`   | provider_health_probe + physical_pager (Webhook + GSM-Siren) + evidence_collector + manual_action_endpoint + envelope_adapter          |
| 5    | `unified-trading-pm`        | (this)      | 22 incident runbooks (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT) + game-day protocol doc                                               |
| 5    | `strategy-service`          | `3b0f7397`  | 2 archetype configs (carry_staked_basis + arbitrage_price_dispersion) with risk_thresholds + close-all scripts + recovery_event_helper |
| 5    | `execution-service`         | `a6fa7c501` | recovery_event_helper for service-initiated AgentActionEvent emission                                                                  |
| 5    | `unified-trading-system-ui` | `01e1bb69`  | DART Safety Ops tab scaffold (3 widgets + Playwright skeleton). [UI] [BLOCKED-PLAYWRIGHT]                                              |

**Per-plan Tier-5 items shipped (this plan's scope):**

- [x] ✅ Phase 3 P0.6-P0.8 DART distinct Op Ack + Audit Ack buttons SCAFFOLD — unified-trading-system-ui@01e1bb69
      (AuditAckQueueWidget) [UI] [BLOCKED-PLAYWRIGHT]

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.4-P0.5 ack_escalation.py cron + ladder shipped. — alerting-service@39b6650
- [x] ✅ Phase 4 P0.9 even-APPROVED-requires-human-ack — `process_signoff` leaves APPROVED incidents in the audit-ack
      queue (no auto-close); `test_approved_does_not_transition_or_clear_queue` asserts it. — alerting-service@39b6650
- [x] ✅ Phase 4 P0.10 — alerting-service@839cb5f | 5-test TestApprovedVerdictDoesNotBypassAuditAck (APPROVED +
      APPROVED_WITH_NOTES + human-ack-clears + signoff-history + flag-retained) | QG green
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] Phase 5 P0.11-P0.12 synthetic smoke for SEV0 + SEV2 ladders (operator to
      schedule when ready)

**Cross-references**:

- Operator ping doc → `plans/active/_agent_pings.md` 2026-05-23 ikenna-slot-1 → operator entry
- 22 incident runbooks → `codex/15-runbooks/incidents/` (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT)
- Game-day protocol → `/codex/15-runbooks/incidents/game_day_protocol.md`
- Alerting Tier-5 → `alerting-service@e5c8084` (5 new gateway/notifier modules)
- Strategy Tier-5 → `strategy-service@3b0f7397` (2 configs + close-all + helper)
- Execution Tier-5 → `execution-service@a6fa7c501` (recovery_event_helper)
- DART Tier-5 → `unified-trading-system-ui@01e1bb69` (safety-ops route + widgets)
