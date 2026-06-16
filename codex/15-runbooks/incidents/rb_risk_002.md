---
title: "RB-RISK-002 — Liquidation Event"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Per-incident
verifier: scenario 15_liquidation_proximity_auto_deleverage
last_executed: never
authoritative_for:
  - "RB-RISK-002 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RISK-002 — Liquidation Event

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

LIQUIDATION_EVENT_DETECTED fires (always SEV1 minimum).

Category: **Risk** · Runbook ID: **RB-RISK-002**.

## First 60 seconds — acknowledge + scope

1. Acknowledge IMMEDIATELY — liquidation = capital loss.
2. Read the LiquidationInvestigationReport (16 fields).
3. Identify the venue + account + instrument + liquidated quantity.

## Diagnose

- Check the 7 SEV0-escalation predicates (material / more-risk-remains / cause-unknown / strategy-still-trading /
  margin-uncertain / cross-account-affected / not-predicted).
- If any escalation predicate True → SEV0.
- Check whether close/reduce logic failed (was margin too low when reduce fired?).
- Check whether risk limits were in force + correctly evaluated.

## Resolve

- Freeze the affected strategy + venue immediately if SEV0 (Safety Ops → ENTER_SAFE_MODE).
- Investigate post-mortem: was this preventable?
- Document liquidation cause + remediation in the incident audit trail.

## Rollback

Liquidation is irreversible. No rollback. Only forward: recovery + prevention.

## Escalate

SEV0 always → founder + physical pager. Multi-account → CCFO involvement.

## Success criteria

Affected strategy in safe mode + remaining positions verified + LiquidationInvestigationReport complete.

## Post-incident

Within 48h: full incident retro + threshold update + close-all-script update if logic gap surfaced.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
