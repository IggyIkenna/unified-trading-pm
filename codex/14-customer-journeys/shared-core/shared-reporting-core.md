---
doc_type: codex-ssot
title: Shared Reporting Core
summary:
  The one client-reporting surface (/services/reports/overview) that IM allocators, Reg Umbrella firms, and DART clients
  all render from the same component tree — entitlement-filtered per audience via API-key-set scope. Block 1 = generic
  panels; block 2 adds Reg panels; block 3 adds IM panels; no forked per-audience reporting products.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [same-system, ui, reporting, playbooks, sales]
related:
  [
    ../_ssot-rules/03-same-system-principle.md,
    ../playbook-concepts/client-reporting.md,
    /codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md,
    /codex/14-customer-journeys/shared-core/same-system-principle.md,
    /codex/14-customer-journeys/shared-core/client-reporting-demo-walkthrough.md,
  ]
created: 2026-04-20
authoritative_for: [shared client-reporting core surface (one component tree, entitlement-filtered)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/regulatory-demo.md,
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/shared-core/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Shared Reporting Core

> The one client-reporting surface that IM allocators, Reg Umbrella firms, and DART clients all use. Entitlement
> filtered per audience; component tree is the same. Cites [rule 03](../_ssot-rules/03-same-system-principle.md) +
> [rule 05](../_ssot-rules/05-building-block-dimensions.md) blocks 1-3.

**Engineering source** (authoritative):
[../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md). This doc re-frames the reporting
surface for the experience layer and the commercial model; it does not duplicate the engineering content.

## Why one surface

Rule 03 sub-claim (a): every paying audience renders reporting from the same component tree. The alternative — three
reporting products, one per audience — creates three maintenance surfaces, three drift vectors, and forces Odum to
re-explain the mechanism per audience. One surface with entitlement slicing is simpler to operate and more credible to
diligence. The experience playbooks make this claim in their key-message sections; this doc is the definitional anchor
they cite.

## What "shared" actually means

The reporting landing page lives at `/services/reports/overview` (or equivalent canonical route per the live UI). Every
audience lands there. The data they see is filtered by persona / entitlement; the components are not forked.

| Surface                                   | Component                    | Who sees it (filter)                                                            |
| ----------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------- |
| Positions table                           | `<PositionsTable>`           | IM: allocator's share class; Reg Umbrella: firm's activity; DART: client's flow |
| P&L attribution                           | `<PnlAttributionChart>`      | Same component; filter scoped to client API-key set                             |
| Exposure analytics                        | `<ExposureSummary>`          | Same component                                                                  |
| Reconciliation                            | `<ReconciliationPanel>`      | Same component; breaks filtered by client scope                                 |
| Audit trail                               | `<AuditTrail>`               | Same component                                                                  |
| Fee accrual (IM)                          | `<FeeAccrual>`               | Visible only on IM profile                                                      |
| Investor statements (IM)                  | `<InvestorStatementIndex>`   | Visible only on IM profile                                                      |
| Transaction reporting (Reg Umbrella)      | `<TransactionReport>`        | Visible only on Reg Umbrella profile                                            |
| Best-execution evidence (Reg Umbrella)    | `<BestExEvidence>`           | Visible only on Reg Umbrella profile                                            |
| Supervisory artifact index (Reg Umbrella) | `<SupervisoryArtifactIndex>` | Visible only on Reg Umbrella profile                                            |

The IM-specific and Reg-specific surfaces are rule-05 blocks 2 + 3 (regulatory umbrella reporting, IM allocator
reporting) — scoped as discrete entitlements, rendered as mounted panels on the same reporting surface.

## Commercial view

Block 1 (reporting core) covers the generic surfaces. Block 2 (regulatory umbrella reporting) adds the Reg Umbrella
panels. Block 3 (IM allocator reporting) adds the IM panels. Every paying client is on block 1; Reg Umbrella clients are
on 1 + 2; IM clients are on 1 + 3; a combined engagement (rare but supported) is on 1 + 2 + 3.

Pricing: see [../commercial-model/im-vs-reg-reporting-logic.md](../commercial-model/im-vs-reg-reporting-logic.md) — same
UI, different commercial framing, different pricing tier composition per audience.

## The entitlement filter in practice

The filter lives at the API-key-set level (see [`org-fund-client-entity-model.md`](org-fund-client-entity-model.md)).
Stage 3C's derivation engine computes `access_control(user, route, component, phase)`. On the reporting route, the same
component tree renders; the visibility of each panel is resolved against:

1. **The audience's block entitlements.** IM-specific panels mount only if block 3 is active.
2. **The data-scoping filter.** Every query filters by the user's `client_id` / `api_key_set_id`.
3. **The phase context.** Research-phase views of reporting bind to historical data; live-phase bind to live data.

## Demo walkthrough

The shared demo walkthrough lives in [`client-reporting-demo-walkthrough.md`](client-reporting-demo-walkthrough.md) —
the click-path that both pb3a (Reg Umbrella) and pb3b (IM) use, with narrative overlays for each audience's framing.

## The same-system claim, operationalised

When a sales person says "this is the same surface Odum uses internally", the claim is true because:

1. Odum's internal operations team views `/services/reports/overview` with admin entitlement, which renders all panels
   over all clients' data.
2. Every paying client views the same route, with their entitlement set reducing the data and panels to their slice.
3. No separate internal reporting UI exists. Internal / external reporting converge on one component tree.

**Violation signal:** any `internal-reporting-*` repo, any `/admin/reports/*` route tree that renders different
positions / P&L / attribution components than `/services/reports/*`. Resolve by consolidating under the shared surface
with admin entitlement.

## Relationship to investor relations

The investor-relations views (board presentations, allocator pitch decks, platform-level summaries) exist at
[../cross-cutting/investor-relations.md](../playbook-concepts/investor-relations.md). They are distinct from client
reporting: IR renders aggregates and narrative; client reporting renders operational detail. The two are different
surfaces but read from the same underlying reporting core for aggregates.

## Cross-references

- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks 1, 2, 3
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md) — entitlement slicing
- [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md) — engineering treatment
- [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md) — the filter mechanism
- [org-fund-client-entity-model.md](org-fund-client-entity-model.md) — where entitlement attaches
- [same-system-principle.md](same-system-principle.md) — the meta-claim
- [client-reporting-demo-walkthrough.md](client-reporting-demo-walkthrough.md) — the shared demo path
- [../commercial-model/im-vs-reg-reporting-logic.md](../commercial-model/im-vs-reg-reporting-logic.md) — pricing view
