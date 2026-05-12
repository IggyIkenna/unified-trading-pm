---
title: Live Deployment Monitoring
status: planned
created: 2026-05-07
authoritative_for:
  Per-archetype event cadence + heartbeat thresholds + cross-cloud event-stream parity expectations for live (non-batch)
  trading deployments. Defines the contract between a running VM/Cloud Run service and the unified-events-interface so
  silent stalls are visible within minutes.
referenced_by:
  - plans/active/master_to_live_defi_2026_05_23.md
related:
  - codex/05-infrastructure/vm-tarball-deployment.md
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/04-architecture/service-infrastructure-requirements.md
---

# Live Deployment Monitoring

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in as
> the work shipped by the referencing plan progresses.
>
> **CUTOVER DEADLINE 2026-05-12** — per the "Master Plan Continuous-Verification Column" HARD RULE, this doc MUST ship
> body content (or explicit move to `codex/16-future-work/`) before the May-23 cutover. As of 2026-05-12, still a stub.
> **Owner**: alerting-service + governance. **Action**: either (a) spawn an active plan to fill the 4 stub sections
> (Lifecycle Events / Heartbeat Thresholds / Cross-Cloud Parity / Stall Detection) before May-23, or (b) move to
> `codex/16-future-work/` and remove the `referenced_by: master_to_live_defi_2026_05_23.md` reference. Today the stub
> anchors a forward-reference that doesn't actually exist.

## Purpose

SSOT for "what does a healthy live deployment look like in the event stream?" Codifies STARTED/PROCESSING/STOPPED
cadence per archetype, heartbeat thresholds, and the cross-cloud parity expectation (GCP and AWS both emit the same
events to the same downstream consumers via the unified-events-interface).

## Scope

- Lifecycle events every live service emits (`STARTED`, `PROCESSING`, `STOPPED`, `FAILED`, `PREFLIGHT_SKIPPED`).
- Heartbeat thresholds per archetype (`carry_staked_basis`, `leveraged_funding_arb`, future archetypes).
- Cross-cloud parity — GCP Pub/Sub vs AWS SNS/SQS event delivery; consumers must see equivalent streams.
- Stall detection — when does "no events in N minutes" trigger an alert? Per-archetype tuning.
- Event UI consumption — `unified-events-interface` Cloud Run service.

## Outline (planned sections)

1. **Event taxonomy** — full list of events live services emit, with severity + expected cadence.
2. **Per-archetype heartbeat matrix** — `(archetype, expected_event, max_gap_seconds)`. e.g. `carry_staked_basis` emits
   `LST_YIELD_REFRESHED` every 60s; gap > 300s = stall.
3. **Cross-cloud delivery** — both clouds write to the same event bucket pattern. Consumer reads via `setup_events()`
   from UTL with cloud-agnostic routing.
4. **Stall-detection alerting** — alerting-service rules consume the event stream and emit AlertCode on heartbeat-miss.
5. **Pre-launch verification protocol** — per the workspace "no fire-and-forget VM launches" rule; covered also under
   live-deployment monitoring runbook.
6. **Cross-cloud parity verification** — once both clouds are live, periodic reconciliation of "did GCP and AWS see the
   same events for the same correlation_id?".

## Cross-references

- **Plan(s) implementing this:**
  [`master_to_live_defi_2026_05_23`](../../plans/active/master_to_live_defi_2026_05_23.md) work-stream B.
- **Related codex SSOTs:** [`vm-tarball-deployment`](./vm-tarball-deployment.md),
  [`alerting/operator-playbook`](../15-runbooks/alerting/operator-playbook.md).
- **Code:** `unified-trading-library/events/`, deployment-UI events tab (UEI archived per CLAUDE.md "System-First
  Architecture"; UI consumption shifted to deployment-UI events tab per `pagerduty-escalation-policy.md:129`;
  AL-19 PRE_CUTOVER 2026-05-12 refresh), alerting-service (TBD).

## Open questions

- What is the canonical heartbeat event for each strategy archetype? (need product-level decision)
- How do we surface event-stream parity-failure (GCP saw event X, AWS didn't) without false-positives during failover?
- Should heartbeat thresholds live in UAC `LIVE_HEARTBEAT_THRESHOLDS` dict or per-service config?
- When a VM is intentionally idle (e.g. between trading windows), how do we distinguish "alive but quiet" from
  "stalled"?
