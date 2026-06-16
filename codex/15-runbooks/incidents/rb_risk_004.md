---
title: "RB-RISK-004 — Strategy Safe Mode"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Per-incident
verifier: scenario 04_defi_oracle_deviation_30sigma
last_executed: never
authoritative_for:
  - "RB-RISK-004 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RISK-004 — Strategy Safe Mode

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Strategy entered safe mode via Layer-0 enter_safe_mode or LLM DISPUTE.

Category: **Risk** · Runbook ID: **RB-RISK-004**.

## First 60 seconds — acknowledge + scope

1. Acknowledge.
2. Identify which strategy + scope is in safe mode.
3. Read the trigger reason from IncidentEnvelope.

## Diagnose

- Verify safe-mode behaviour: new orders paused, existing orders per policy (cancel or retain), positions still tracked.
- Check whether response_policy.require_human_for_resume=True (auto-resume blocked).
- Check what condition needs to clear for safe resume.

## Resolve

- Wait for trigger condition to clear (e.g. oracle deviation back below threshold).
- Verify positions reconcile and hedges are intact.
- Use Safety Ops EXIT_SAFE_MODE only after manual verification.

## Rollback

Safe mode → resume requires explicit operator action when require_human_for_resume=True.

## Escalate

Operator unable to verify safe-mode state → SEV0.

## Success criteria

Strategy resumed normal operation + audit ack.

## Post-incident

Document the safe-mode duration + cause + resume rationale.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
