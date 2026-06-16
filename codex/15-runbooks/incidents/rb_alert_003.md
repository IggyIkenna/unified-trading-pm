---
title: "RB-ALERT-003 — Satellite / No-Signal Fallback"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-travel
verifier: Pre-travel test call
last_executed: never
authoritative_for:
  - "RB-ALERT-003 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-ALERT-003 — Satellite / No-Signal Fallback

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Operator travelling to no-signal area OR primary devices unreachable.

Category: **Alerting** · Runbook ID: **RB-ALERT-003**.

## First 60 seconds — acknowledge + scope

1. Confirm satellite device on hand (Garmin inReach Mini 2 recommended).
2. Check Iridium subscription active.
3. Pre-configure webhook → alerting-service.

## Diagnose

- Satellite uplink test from current location.
- Battery charge.
- Backup human rota set up?

## Resolve

- Notify alerting-service to route SEV0 to satellite endpoint while operator is travelling.
- Engage backup human (Harsh) for primary on-call rota during travel.
- Test end-to-end before departure.

## Rollback

Resume primary device on return.

## Escalate

Satellite + cellular both down → human-only fallback (call founder).

## Success criteria

Test alert routed via satellite + acked.

## Post-incident

Log travel dates + device usage in alerting health log.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
