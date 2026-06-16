---
title: "RB-RISK-003 — Liquidation Risk / Margin Danger"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Per-incident
verifier: Liquidation pre-detector unit tests
last_executed: never
authoritative_for:
  - "RB-RISK-003 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RISK-003 — Liquidation Risk / Margin Danger

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

LIQUIDATION_RISK_IMMINENT (any of 6 pre-detection triggers).

Category: **Risk** · Runbook ID: **RB-RISK-003**.

## First 60 seconds — acknowledge + scope

1. Acknowledge.
2. Check which of the 6 triggers fired: margin ratio / liquidation distance / collateral transfer fail / ADL/insurance /
   venue API uncertainty / price gap.

## Diagnose

- Pull current margin ratio + HF + collateral balances from venue.
- Check whether auto-deleverage already fired (per response_policy.allow_auto_reduce).
- Check whether collateral transfer is feasible (gas / settlement window).

## Resolve

- Reduce position size if allow_auto_reduce=True + safe path exists.
- Or close all on affected scope if allow_auto_close_all=True.
- Or transfer collateral if path is live + not too costly.
- Or manually flatten via Safety Ops if no auto-path safe.

## Rollback

Once collateral transferred or position reduced, reversing requires fresh order at current prices.

## Escalate

If risk remains after first action → SEV0.

## Success criteria

Margin ratio above threshold + HF > 1.5 (LR margin recovered).

## Post-incident

Review threshold seeding: was the pre-detector fast enough?

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
