---
title: "RB-CONN-005 — Alert Provider Failure"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Monthly
verifier: Provider health probe smoke
last_executed: never
authoritative_for:
  - "RB-CONN-005 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-CONN-005 — Alert Provider Failure

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

ALERTING_PROVIDER_DEGRADED fires (PagerDuty / Telegram probe failed).

Category: **Connectivity** · Runbook ID: **RB-CONN-005**.

## First 60 seconds — acknowledge + scope

1. Check the probe result in DART.
2. Confirm fallback_mode=True in the router.
3. Verify Twilio voice is reachable (test call).

## Diagnose

- PagerDuty API status page.
- Telegram bot status.
- Twilio account billing.
- SM credential validity.

## Resolve

- Wait for provider recovery + monitor.
- If billing issue: escalate to operator IMMEDIATELY.
- If credential rotated externally: re-sync from SM.

## Rollback

Fallback mode auto-resets after 3 consecutive successful probes.

## Escalate

All channels down during SEV0 → physical pager + in-person escalation.

## Success criteria

Probe returns 2 consecutive successes → fallback_mode=False.

## Post-incident

Document provider-outage duration in alerting health log.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
