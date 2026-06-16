---
title: "RB-INC-001 — SEV0 Incident Handling"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly game-day
verifier: PagerDuty escalation drill
last_executed: never
authoritative_for:
  - "RB-INC-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-INC-001 — SEV0 Incident Handling

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

SEV0 IncidentEnvelope emitted by the Incident Gateway (capital at risk, recovery unproven).

Category: **Core** · Runbook ID: **RB-INC-001**.

## First 60 seconds — acknowledge + scope

1. Acknowledge the PagerDuty page via app or 'pd-cli ack'.
2. Open DART Safety Ops tab → filter to the incident_key.
3. Read the LLM RecoveryAuditSignoff verdict if present (informational only).
4. Identify scope: service / strategy / venue / instrument from IncidentEnvelope.

## Diagnose

- Check `risk_state` field: safe / protected_mode / unknown / live_unresolved.
- Check `capital_at_risk` field: True = positions / orders exposed.
- Pull the latest AgentActionEvent rows for this incident_key from GCS audit store.
- Pull the relevant detector trigger (LiquidationEventDetector / kill-switch / circuit-breaker).

## Resolve

- If `recovery_confirmed=False` AND `risk_state` in {unknown, live_unresolved}: take ownership via Operational Ack
  button + investigate root cause before any action.
- If automation has SAFE_MODE_ACTIVE: verify scope is correct + verify positions reconcile.
- If LLM verdict=DISPUTE_AUTOMATED_ACTION: assume automated action was wrong; re-evaluate from upstream signal.
- When risk neutralised: transition to AUDIT_REPORT_GENERATED via gateway state machine.

## Rollback

If a Layer-0 action made things worse (rare): use Safety Ops tab to undo (e.g. UNDISABLE_VENUE) — typed-confirm-string
required.

## Escalate

Founder Twilio voice call after 30min unacked (CRITICAL SLA per `audit-acknowledgement-flow.md`).

## Success criteria

Incident reaches HUMAN_AUDIT_ACKED → RESOLVED → CLOSED with audit report in GCS.

## Post-incident

Post-incident retro within 48h; update closed-set thresholds if false-positive contributed.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
