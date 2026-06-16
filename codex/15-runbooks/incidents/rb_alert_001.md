---
title: "RB-ALERT-001 — Dedicated On-Call Phone Setup"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly device check
verifier: Monthly test alert + device-ack proof
last_executed: never
authoritative_for:
  - "RB-ALERT-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-ALERT-001 — Dedicated On-Call Phone Setup

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

New operator joins on-call OR device replaced.

Category: **Alerting** · Runbook ID: **RB-ALERT-001**.

## First 60 seconds — acknowledge + scope

1. Identify carrier (different from operator primary).
2. Identify model (Nokia 2660 Flip recommended).
3. Check SIM activation.

## Diagnose

- Carrier coverage in operator location.
- Battery + charger state (always-plugged).
- Ringtone volume + DND-bypass configured.

## Resolve

- Install PagerDuty app + Telegram on the device.
- Configure DND-bypass for Twilio number + PagerDuty contact.
- Test: send synthetic alert from staging environment.
- Disable battery optimisation.
- Keep device near bed/desk.

## Rollback

If device fails: revert to primary phone temporarily + ship replacement.

## Escalate

Device unreliable → physical pager (RB-ALERT-002) + Twilio voice.

## Success criteria

Device ack'd a test alert + operator confirms audible.

## Post-incident

Add device serial to inventory + next test date.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
