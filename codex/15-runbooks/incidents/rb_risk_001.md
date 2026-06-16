---
title: "RB-RISK-001 — Strategy Drawdown Investigation"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Per-incident
verifier: Drawdown investigation report writer test
last_executed: never
authoritative_for:
  - "RB-RISK-001 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-RISK-001 — Strategy Drawdown Investigation

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

PnL drawdown threshold breach (warning / investigation / human_escalation / auto_pause / auto_reduce / auto_close_all /
liquidation_risk).

Category: **Risk** · Runbook ID: **RB-RISK-001**.

## First 60 seconds — acknowledge + scope

1. Acknowledge.
2. Read the DrawdownInvestigationReport (17 fields).
3. Identify which threshold breached + the strategy's response_policy state.

## Diagnose

- Compare drawdown to expected_drawdown_model band (in-distribution vs out-of-distribution).
- Attribute realised vs unrealised PnL.
- Check exposure before/after the breach.
- Check market move context (was this a venue-wide event?).
- Check execution slippage + fees + funding + borrow costs.
- Check signal sanity (did the strategy see normal signals?).

## Resolve

- If breach is in-distribution + auto_pause already fired: monitor + decide resume per response_policy.
- If out-of-distribution: SEV0 — close all on affected scope via Safety Ops.
- If signal bug / data quality issue: pause strategy + escalate to strategy-service engineering.
- If venue-wide event: check other strategies on same venue + consider venue disable.

## Rollback

Auto-pause/reduce can be resumed via Safety Ops only when require_human_for_resume=True allows it.

## Escalate

auto_close_all threshold → founder Twilio voice + physical pager.

## Success criteria

Drawdown stabilised + operator-acked + strategy state explicit (paused / reduced / closed / resumed).

## Post-incident

If threshold was too tight (FP rate > 5%): retune in the next quietness-baseline cycle.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
