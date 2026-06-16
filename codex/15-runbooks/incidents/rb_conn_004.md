---
title: "RB-CONN-004 — Database/Storage Degradation"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: Database failover smoke
last_executed: never
authoritative_for:
  - "RB-CONN-004 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-CONN-004 — Database/Storage Degradation

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Database write errors / read latency spike / connection pool exhaustion.

Category: **Connectivity** · Runbook ID: **RB-CONN-004**.

## First 60 seconds — acknowledge + scope

1. Identify the affected DB (Cloud SQL / Firestore / Redis / etc).
2. Check current state (read-only mode? full outage?).
3. Check whether services have fallen back to caches.

## Diagnose

- Read vs write impact.
- Replay / recovery capability.
- Per-service degraded-mode status.

## Resolve

- If transient: wait + monitor.
- If sustained: enter_readonly_recon_mode on affected services.
- If catastrophic: trigger DR restore per disaster-recovery.md.

## Rollback

Read-only mode is reversible.

## Escalate

Ledger writes failing → SEV0.

## Success criteria

DB responsive + per-service health checks green.

## Post-incident

DR test results updated.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
