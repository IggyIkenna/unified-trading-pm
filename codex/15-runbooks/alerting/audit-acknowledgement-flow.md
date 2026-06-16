---
scope: [engineer, admin]
last_reviewed: 2026-05-23
authoritative_for: [audit-ack-sla, escalation-ladder, operational-vs-audit-ack]
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - codex/15-runbooks/alerting/pagerduty-escalation-policy.md
  - plans/active/audit_acknowledgement_sla_and_state_2026_05_23.md
---

# Audit Acknowledgement Flow

> SSOT for the audit-ack SLA + escalation ladder. Codifies operator HARD RULE 2026-05-23: "even if AI audit confirms
> automation was good result, human should be required to double check and ack within 6 hours or less or more depending
> on severity".

## Two distinct ack types

| Ack type            | What it means                                                                   | When required                                                                                                                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operational ack** | "I'm investigating this now — I have ownership."                                | SEV0 always; SEV1 when unresolved; any incident in SAFE_MODE / degraded mode                                                                                                                                                      |
| **Audit ack**       | "I've reviewed the report AFTER the system handled it. I sign off the outcome." | Material auto-action; production redeploy; OOM resize; venue disablement; strategy pause/resume; auto-order-cancel; auto-close-all; liquidation; PnL drawdown investigation; recon breach; connectivity degradation beyond buffer |

The two are timestamped separately on `IncidentEnvelope`:

- `operational_acked_by` + `operational_acked_at` — operational ack does NOT transition incident state.
- `audit_acked_by` + `audit_acked_at` — audit ack transitions to `HUMAN_AUDIT_ACKED`.

Operational ack should be fast — measured in minutes for SEV0. Audit ack happens after the dust settles — measured in
hours per the SLA matrix below.

## SLA matrix

Default policy (`AuditAckSLAPolicy` registered in `unified_api_contracts/canonical/crosscutting/incident/sla.py`):

| Severity     | Default ack window | Secondary-human after | Founder after | Physical pager after         |
| ------------ | ------------------ | --------------------- | ------------- | ---------------------------- |
| **CRITICAL** | 300s (5min)        | 600s (10min)          | 1800s (30min) | (alongside founder)          |
| **HIGH**     | 7200s (2h)         | 10800s (3h)           | 21600s (6h)   | 21600s (6h)                  |
| **WARN**     | 21600s (6h)        | 43200s (12h)          | 86400s (24h)  | (n/a — no physical for WARN) |
| **INFO**     | None               | n/a                   | n/a           | n/a                          |

Per-strategy / per-archetype override via `audit_ack_policy:` key in strategy config. Operator approves stricter
overrides.

## Escalation ladder (the cascade)

```
T+0: incident transitions to AUDIT_REPORT_GENERATED
        ↓
T+default_window: if not acked → secondary on-call PagerDuty page
        ↓
T+secondary_after: if still not acked → founder PagerDuty page + Twilio voice call to founder
        ↓
T+founder_after: if still not acked → physical pager fires (or Twilio bridge twice if device not configured)
        ↓
incident remains open in audit-ack queue until acked
```

Each step appends to `audit_ack_escalation_history` array on the IncidentEnvelope, JSON shape per step:

```json
{
  "timestamp": "2026-05-23T18:00:00Z",
  "escalation_step": "secondary_human_pagerduty",
  "target": "harsh@odum-research.com",
  "channel": "PAGERDUTY",
  "delivery_status": "succeeded"
}
```

## Even-APPROVED-requires-human-ack rule (operator HARD RULE)

When the LLM recovery-audit-signoff agent posts `verdict=APPROVED` or `verdict=APPROVED_WITH_NOTES`, the incident
remains in the audit-ack queue with countdown active. The LLM verdict is INFORMATIONAL — it informs the operator's ack
decision, but does NOT substitute for the human ack.

Rationale (operator 2026-05-23): "ai/lmm needs to be able to use scripts to drive things like restarts in case
automation fails. AI audit every risk and recovery related event and sign off. ... even if AI audit confirms automation
was good result, human should be required to double check and ack within 6 hours or less or more depending on the
severity."

This composes with: `Plans Run To Actual Completion, Not Smoke-Test Green` (CLAUDE.md HARD RULE) — APPROVED LLM verdict
on an incident is not "the work is shipped"; the work is shipped when the operator audit-acks.

## DART surface

`unified-trading-system-ui/components/widgets/alerts/`:

- `ack-queue-widget.tsx` — list of incidents requiring `human_audit_ack_required=True + status≠HUMAN_AUDIT_ACKED`.
  Sortable by due-soon-first. Each row shows: incident_key, severity, problem_type, LLM verdict (if any), countdown to
  `audit_ack_due_at`, escalation status.
- `operational-ack-button.tsx` — sets `operational_acked_by` + `operational_acked_at`; no state transition.
- `audit-ack-button.tsx` — disabled until incident reaches `AUDIT_REPORT_GENERATED` state; on click, transitions to
  `HUMAN_AUDIT_ACKED`.

Operator HARD RULE 2026-05-23: "deployment ui should have the ui oversight in one of its tabs that allows us to perform
all the circuit break and disaster recovery stuff manually". The Safety Ops tab in deployment-ui mirrors these widgets
(per `plans/active/deployment_ui_safety_ops_tab_2026_05_23.md`).

## Ack-escalation cron

`alerting-service/alerting_service/gateway/ack_escalation.py` runs every 30s:

1. Scan audit-ack queue for incidents with `audit_ack_due_at < now()` and `audit_acked_at IS NULL`.
2. Per-incident: load SLA policy from severity; check elapsed time since due_at.
3. If `elapsed > secondary_human_after_seconds` and no secondary-page sent yet → trigger secondary PagerDuty page;
   append to escalation history.
4. If `elapsed > founder_after_seconds` and no founder-page sent yet → trigger founder Twilio voice call; append.
5. If `elapsed > physical_pager_after_seconds` (where defined) → trigger PhysicalPagerNotifier; append.
6. Continue running until acked.

## Audit trail durability

`audit_ack_escalation_history` is persisted to GCS via `incident_persister.py` at
`gs://<kill-switch-audit>/incidents/{date}/{key}/escalation_history.jsonl` — append-only, JSONL, 1-year retention.
Regulatory-grade trail of who was paged when.

## Related

- `04-architecture/incident-gateway-state-machine.md` — 13-state machine + audit-ack queue.
- `04-architecture/recovery-defence-in-depth-layers.md` — Layer-5 is this flow.
- `15-runbooks/alerting/pagerduty-escalation-policy.md` — Ikenna 14:30-02:30 UK / Harsh 02:30-14:30 UK rotation.
- `plans/active/audit_acknowledgement_sla_and_state_2026_05_23.md` — implementation plan.
