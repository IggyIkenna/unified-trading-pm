---
title: "RB-RECON-003 — Balance/Collateral Mismatch"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly game-day
verifier: Scenario 14_borrow_rate_spike
last_executed: never
authoritative_for:
  - "RB-RECON-003 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RECON-003 — Balance/Collateral Mismatch

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

VENUE_INTERNAL_BALANCE_MISMATCH OR MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED immediate-SEV0.

Category: **Reconciliation** · Runbook ID: **RB-RECON-003**.

## First 60 seconds — acknowledge + scope

1. Acknowledge.
2. Pull venue balance snapshot + internal balance snapshot.
3. Compute delta (venue - internal).

## Diagnose

- Check transfers, funding, fees, borrowing rows for the time window.
- Check for unexpected on-chain transactions (DeFi).
- Check for liquidation events that weren't captured by detectors.
- Check collateral movements + margin mode changes.

## Resolve

- If delta is explained by missing row in internal: backfill the row (e.g. funding payment that arrived late).
- If delta is unexplained > $1k: SEV0 — kill switch on the affected scope.
- Document each balance movement attribution in the incident audit trail.

## Rollback

Balance ledger writes are append-only — corrections are new rows, not edits.

## Escalate

Unexplained > threshold → founder + on-chain analytics team.

## Success criteria

abs(venue - internal) < $100 for the (account, asset) scope.

## Post-incident

If repeated mismatches on one venue: add per-venue threshold override + escalate to venue support.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
