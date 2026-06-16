---
title: "RB-INFRA-001 — OOM Recovery"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: resize_machine_after_oom --dry-run
last_executed: never
authoritative_for:
  - "RB-INFRA-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-INFRA-001 — OOM Recovery

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Service OOM detected.

Category: **Infrastructure** · Runbook ID: **RB-INFRA-001**.

## First 60 seconds — acknowledge + scope

1. Acknowledge.
2. Check whether Layer-0 already resize+restarted.
3. Check for repeated OOM (loop detection).

## Diagnose

- Memory profile if captured.
- Recent deploys / config changes.
- Workload spike?

## Resolve

- If single OOM with clean recovery: SEV2 + audit ack.
- If repeated: investigate root cause before further restarts.

## Rollback

If new deploy caused the OOM: REDEPLOY to previous known-good revision.

## Escalate

Repeated OOM with order/position state uncertain → SEV0.

## Success criteria

Service stable + memory < 80% + no OOM in last 1h.

## Post-incident

Update VM size in deployment-service if pattern recurring.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
