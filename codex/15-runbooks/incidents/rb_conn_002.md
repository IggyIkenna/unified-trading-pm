---
title: "RB-CONN-002 — Exchange REST API Failure"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: scenario 01_cefi_venue_circuit_breaker_trip
last_executed: never
authoritative_for:
  - "RB-CONN-002 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-CONN-002 — Exchange REST API Failure

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Order cancellation cannot be confirmed via venue REST.

Category: **Connectivity** · Runbook ID: **RB-CONN-002**.

## First 60 seconds — acknowledge + scope

1. Identify venue.
2. Check rate limit headers + auth state.
3. Check whether the circuit breaker has fired.

## Diagnose

- Order placement: can we still place new orders? (If yes — partial outage only.)
- Order cancellation: can we cancel? (Critical — blocks risk management.)
- Authentication: API key valid + permissions OK.

## Resolve

- If cancel impossible: KILL_SWITCH_CANNOT_CONFIRM_CANCEL → SEV0; engage venue support.
- If placement only impacted: pause new orders + monitor.
- If rate limit: back off + retry.

## Rollback

None — venue-side issue.

## Escalate

Cancel confirmation impossible → SEV0 + venue support ticket.

## Success criteria

REST API responsive + cancel/place both work.

## Post-incident

Document API outage + duration in venue-stability log.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
