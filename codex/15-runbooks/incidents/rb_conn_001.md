---
title: "RB-CONN-001 — Exchange WebSocket Degradation"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: scenario 01_cefi_venue_circuit_breaker_trip
last_executed: never
authoritative_for:
  - "RB-CONN-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-CONN-001 — Exchange WebSocket Degradation

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

CONNECTIVITY_GAP_DETECTED OR TICK_STALENESS on a venue.

Category: **Connectivity** · Runbook ID: **RB-CONN-001**.

## First 60 seconds — acknowledge + scope

1. Identify venue + duration.
2. Check whether circuit breaker has already disabled the venue.
3. Check backup feed health.

## Diagnose

- Disconnect duration vs expected_recovery_time from dependency_health_policy.
- Backup feed staleness — is it fresh enough to fall back to?
- Order book freshness.

## Resolve

- If recoverable: wait for venue WS to restore + monitor.
- If beyond hard threshold: fail over to backup feed via failover_feed Layer-0 OR Safety Ops manual.
- If both feeds down: disable_venue + cancel_open_orders.

## Rollback

Failover is reversible — failover back when primary recovers.

## Escalate

Both feeds down + recon impossible → SEV0 + DUAL_FAILURE_DETECTED.

## Success criteria

Tick freshness < staleness threshold + positions reconcile.

## Post-incident

If frequent: add to per-venue dependency_health_policy hard_escalation_seconds tuning queue.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
