---
title: "RB-CONN-003 — Internal Messaging Lag"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: Pub/Sub lag synthetic smoke
last_executed: never
authoritative_for:
  - "RB-CONN-003 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-CONN-003 — Internal Messaging Lag

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

PubSub / Kafka / Redis lag exceeds dependency_health_policy threshold.

Category: **Connectivity** · Runbook ID: **RB-CONN-003**.

## First 60 seconds — acknowledge + scope

1. Identify topic / queue / stream.
2. Check current lag vs threshold.
3. Check consumer group health.

## Diagnose

- Producer rate vs consumer rate.
- Dead-letter queue accumulation.
- Consumer instance count + resource usage.

## Resolve

- Scale consumers if CPU-bound.
- Replay DLQ if recoverable.
- Fail over to backup messaging layer if available.

## Rollback

Consumer scale-out is reversible.

## Escalate

If live-trading topics blocked → SEV1 → SEV0.

## Success criteria

Lag below threshold + DLQ < 10 entries.

## Post-incident

Capacity-plan if recurring.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
