---
title: "RB-ALERT-002 — Physical Siren/GSM Alarm Setup"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly device check
verifier: Monthly test trigger + audible-confirm
last_executed: never
authoritative_for:
  - "RB-ALERT-002 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-ALERT-002 — Physical Siren/GSM Alarm Setup

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

New siren device OR operator location move.

Category: **Alerting** · Runbook ID: **RB-ALERT-002**.

## First 60 seconds — acknowledge + scope

1. Identify vendor (Eshion / DAYTECH M5).
2. Identify SIM provider (third carrier).
3. Confirm wall-mount location near sleeping/working area.

## Diagnose

- SIM signal strength at install location.
- Power source (mains + battery backup).
- SMS-trigger format from vendor docs.

## Resolve

- Wire SMS-trigger via Twilio SMS path (alerting-service notifier).
- Configure SM secrets: alerting-physical-pager-\* set to GSM_SIREN.
- Test: send synthetic SEV0-no-ack from staging → confirm audible alarm.
- Document expected response time (5-15s for SMS).

## Rollback

If SMS path fails: device can also be wired via webhook OR satellite uplink.

## Escalate

If device doesn't fire when expected → ALERTING_PROVIDER_DEGRADED.

## Success criteria

Device alarms reliably on test trigger.

## Post-incident

Test monthly + log result in `last_executed` frontmatter of this runbook.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
