---
title: "RB-RECON-002 — Open Order Uncertainty"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly game-day
verifier: scenario 01_cefi_venue_circuit_breaker_trip
last_executed: never
authoritative_for:
  - "RB-RECON-002 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RECON-002 — Open Order Uncertainty

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Open orders cannot be confirmed via venue REST (OPEN_ORDERS_UNCONFIRMABLE immediate-SEV0).

Category: **Reconciliation** · Runbook ID: **RB-RECON-002**.

## First 60 seconds — acknowledge + scope

1. Acknowledge.
2. Identify the venue.
3. Check circuit breaker state — is the venue already disabled?

## Diagnose

- Try venue REST GET /orders/open from execution-service /admin endpoint.
- If 5xx: this is the cause; wait for venue OR fail over.
- If 200 but mismatched: pull each known internal order_id + try GET /order/{id}.

## Resolve

- Cancel each ambiguous order via Safety Ops → CANCEL*ALL*<venue>.
- If cancel returns partial-success: KILL_SWITCH_CANNOT_CONFIRM_CANCEL fires → SEV0 escalation.
- Once cancellation confirmed: re-reconcile internal ledger.

## Rollback

Cancel actions are NOT idempotent — once cancelled, can't be un-cancelled. Re-submit fresh orders if needed.

## Escalate

SEV0 if cancel confirmation impossible — founder Twilio + physical pager.

## Success criteria

All previously-open orders either confirmed-cancelled OR confirmed-still-active in internal ledger.

## Post-incident

If venue REST regularly flakes: add per-venue circuit-breaker override or upgrade to backup feed.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
