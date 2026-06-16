---
title: "RB-DEPLOY-001 — Production Rollback"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: redeploy_known_good --dry-run
last_executed: never
authoritative_for:
  - "RB-DEPLOY-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-DEPLOY-001 — Production Rollback

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Operator decides to roll back a service to a known-good revision.

Category: **Deployment** · Runbook ID: **RB-DEPLOY-001**.

## First 60 seconds — acknowledge + scope

1. Identify the service.
2. Identify the target revision (from Cloud Run history or workspace manifest).

## Diagnose

- Why are we rolling back? (Bug / regression / config issue.)
- Is the target revision verified?

## Resolve

- Use Safety Ops → REDEPLOY*<service>\_to*<revision> with typed confirm.
- Verify health checks on the rolled-back revision.
- Verify trading state reconciles.

## Rollback

Rollback IS the rollback. To un-rollback, deploy forward to a different revision.

## Escalate

Health checks fail after rollback → SEV0.

## Success criteria

Service serving traffic on target revision + positions reconcile.

## Post-incident

File bug for the regression that triggered the rollback.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
