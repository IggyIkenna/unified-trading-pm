---
title: "RB-INFRA-002 — Machine/Node Failure"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: Manual cordon+drain test
last_executed: never
authoritative_for:
  - "RB-INFRA-002 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-INFRA-002 — Machine/Node Failure

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

GCE node unresponsive / VM disk full / cluster node NotReady.

Category: **Infrastructure** · Runbook ID: **RB-INFRA-002**.

## First 60 seconds — acknowledge + scope

1. Identify the node + affected workloads.
2. Check whether workloads have auto-migrated.

## Diagnose

- VM health checks.
- Disk utilisation.
- Network connectivity.

## Resolve

- Cordon the node + drain workloads.
- Replace the VM if necessary (new launch from tarball).
- Verify all workloads running on new infra.

## Rollback

Old VM can be drained back if needed.

## Escalate

Multiple nodes failing → SEV0 + cluster-wide investigation.

## Success criteria

All affected workloads running on healthy infra + positions reconcile.

## Post-incident

Update VM zombie watchdog if VM was zombie.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
