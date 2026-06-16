---
title: "RB-INC-002 — SEV1 Investigation Handling"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly game-day
verifier: PagerDuty escalation drill
last_executed: never
authoritative_for:
  - "RB-INC-002 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-INC-002 — SEV1 Investigation Handling

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

SEV1 IncidentEnvelope — material trading event OR unresolved degradation; system in protected mode.

Category: **Core** · Runbook ID: **RB-INC-002**.

## First 60 seconds — acknowledge + scope

1. Acknowledge the PagerDuty page.
2. Read the agent investigation report linked from the incident (drawdown / liquidation / recon).
3. Identify which closed-set predicate triggered the SEV1 (15-min recon / drawdown_human_escalation / etc).

## Diagnose

- Read the LLM RecoveryAuditSignoff narrative.
- Check whether the affected scope (strategy / venue / symbol) is correctly identified.
- Verify protected mode is functioning (preflight rejects orders for the scope).

## Resolve

- Decide: continue / pause / disable-venue / close-all.
- Use DART Safety Ops manual buttons for the decision; typed-confirm required.
- Document the decision in the incident audit trail.

## Rollback

If continue → escalate to SEV0 via gateway if conditions worsen.

## Escalate

Secondary on-call after 2h unacked (HIGH SLA); founder after 3h.

## Success criteria

Incident closes with audit ack + clear action documented.

## Post-incident

Threshold review if false-positive frequency rising.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
