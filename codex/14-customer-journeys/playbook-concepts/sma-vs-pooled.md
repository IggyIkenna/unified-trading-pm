---
doc_type: codex-ssot
title: SMA vs Pooled
summary:
  "Fund-level structural choice: Pooled (one fund, clients as share classes, allocation-engine NAV) vs SMA (one fund per
  client, own API keys, NAV=actual P&L); surfaces in pb3a/pb3b demos, catalogue-agnostic, irreversible without
  redemption + new-fund creation."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, fund-structure, sma-pooled, reporting, demo, share-class]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
    /codex/14-customer-journeys/playbook-concepts/client-reporting.md,
    ../playbooks/03a-demo-reg-umbrella.md,
    ../../04-architecture/share-class-architecture.md,
    ../../04-architecture/capital-flow-model.md,
  ]
created: 2026-04-19
authoritative_for: [SMA vs Pooled fund-structure decision (customer-journey framing)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/client-reporting.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
  ]
owner:
last_reviewed:
code_refs:
---

# SMA vs Pooled

The structural decision at fund level. Surfaces in pb3a (Reg Umbrella demo) AND pb3b (IM demo) as the first choice the
prospect makes after signing in to the services portal.

## Definitions

### Pooled

One fund holds multiple clients. Each client is a **share class** of the fund. The fund has:

- ONE set of positions
- ONE market data feed
- ONE set of API keys (sort of — sometimes mirrored to sub-accounts per venue)
- Per-share-class NAV allocation (allocations computed via allocation engine)

### SMA (Separately Managed Account)

EACH client has their OWN fund. Each SMA fund runs independently:

- Per-client positions
- Per-client API keys (always; no sharing)
- Per-client NAV = actual P&L
- No allocation engine needed

## Decision tree

| Factor                      | Pooled                          | SMA                          |
| --------------------------- | ------------------------------- | ---------------------------- |
| Number of clients           | Many (scale economy)            | Few (bespoke)                |
| Client wealth               | Retail/mid                      | HNW/institutional            |
| Investment mandate          | Standardised                    | Bespoke per client           |
| Operational cost per client | Low                             | High                         |
| Isolation                   | Logical (via allocation engine) | Physical (separate accounts) |
| Regulatory reporting        | Fund-level                      | Per-client                   |
| Fee structure               | Share-class tiers               | Per-client negotiated        |

## Applies to BOTH IM and Reg Umbrella

Per user directive, SMA vs Pooled is a structural decision applicable to both:

- IM clients deciding how they're allocated to
- Reg Umbrella clients deciding how their activity is structured

The UI presents the choice identically in both pb3a and pb3b.

## Demo locking logic

In pb3 demos, the admin can:

- Show BOTH choices (prospect makes their own selection — educational demo)
- LOCK one choice (force the other — targeted demo for a prospect whose structure is known)
- Show only one (pretend the other doesn't apply — simplified demo)

Lock state passed via demo-user entitlement flag (gap — entitlement extension tracked in
[../roadmap/next-waves.md](../roadmap/next-waves.md)).

## UI surface

The picker lives either:

- On the services portal landing (`/dashboard`) as a first-time modal, OR
- Inside `/services/reports/overview` as a "switch fund structure" control (TBD — decision in Phase 3 nav-config)

After picking:

- Pooled: fund creation flow presents share-class setup
- SMA: fund creation flow presents one-client-per-fund setup

Subsequent provisioning (funds, clients, API keys) diverges accordingly.

## Data model impact

All four catalogues are agnostic to SMA vs Pooled — strategies, ML models, data, execution algos work the same either
way. The difference is at reporting/NAV layer. See [client-reporting.md](client-reporting.md).

## Migration between structures

Once a fund is Pooled, clients cannot migrate to SMA (or vice versa) without a structural change — redemption +
new-fund-creation. The UI presents this as irreversible for the demo to make that clear. Production: only admin can
change (with deep ops involvement).

## Related plans

- [share_class_architecture_2026_04_01.plan.md](../../../plans/archive/share_class_architecture_2026_04_01.plan.md) —
  the detailed implementation

## Related codex

- Share class architecture:
  [../../04-architecture/share-class-architecture.md](../../04-architecture/share-class-architecture.md)
- Capital flow: [../../04-architecture/capital-flow-model.md](../../04-architecture/capital-flow-model.md)
- Fund/org hierarchy: [fund-org-hierarchy.md](fund-org-hierarchy.md)
- Client reporting: [client-reporting.md](client-reporting.md)
