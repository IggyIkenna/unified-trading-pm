---
title: "RB-RECON-001 — Position Reconciliation Lag"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Quarterly game-day
verifier: scenario 11_handshake_integration
last_executed: never
authoritative_for:
  - "RB-RECON-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RECON-001 — Position Reconciliation Lag

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Position delta unreconciled > 15min (SEV1) OR > 30min OR immediate-SEV0 override (SEV0).

Category: **Reconciliation** · Runbook ID: **RB-RECON-001**.

## First 60 seconds — acknowledge + scope

1. Acknowledge the page.
2. Identify (strategy, venue, instrument) scope from IncidentEnvelope.
3. Check if RECON_FREEZE armed (execution-service preflight rejects new orders for scope).

## Diagnose

- Pull venue REST snapshot via execution-service /evidence/{incident_key}.
- Compare against internal ledger (`oldest_unreconciled_position_age_seconds`).
- Identify the unreconciled trade / order / fill / position.
- Apply buffer policy: which of the 7 ImmediateSev0Overrides apply?

## Resolve

- If lag is API/network: wait for venue to catch up.
- If unexplained: cancel open orders via Safety Ops → CANCEL*ALL*<venue> → wait for venue ack → re-reconcile.
- If still mismatched: flatten the affected scope manually via execution-service /admin endpoints.

## Rollback

Unfreeze RECON_FREEZE only after operator manually verifies internal == venue.

## Escalate

30min unresolved → SEV0; founder Twilio voice at 30min CRITICAL escalation window.

## Success criteria

Recon delta = 0 AND oldest_unreconciled_age_seconds < 60s. Operator unfreezes via Safety Ops.

## Post-incident

If the same (venue, instrument) shows repeated lag: add to per-venue override in alerting-service config.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
