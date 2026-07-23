---
doc_type: codex-ssot
title: Client Reporting Demo Walkthrough — Shared
summary:
  The single five-stop reporting click-path (landing → positions/P&L → reconciliation → audience panel → audit trail)
  shared by pb3a (Reg Umbrella) and pb3b (IM) demos, with per-audience narrative overlays over one component tree.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [playbooks, ui, reconciliation, reporting, same-system, demo]
related:
  [
    /codex/14-customer-journeys/shared-core/shared-reporting-core.md,
    /codex/14-customer-journeys/shared-core/same-system-principle.md,
    ../experience/regulatory-demo.md,
    ../experience/investment-management-demo.md,
  ]
created: 2026-04-20
authoritative_for: [shared client-reporting demo click-path (pb3a/pb3b)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/regulatory-demo.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/shared-core/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Client Reporting Demo Walkthrough — Shared

> The shared click-path used by pb3a (Reg Umbrella demo) and pb3b (IM demo). One walkthrough, two narrative overlays.
> Avoids drift between the two demos because both render the same reporting components — rule 03 same- system principle
> applied at the demo layer.

**Consumed by:** [`../experience/regulatory-demo.md`](../experience/regulatory-demo.md) (pb3a),
[`../experience/investment-management-demo.md`](../experience/investment-management-demo.md) (pb3b) **Grounded in:**
[`shared-reporting-core.md`](shared-reporting-core.md), [rule 03](../_ssot-rules/03-same-system-principle.md),
[rule 06](../_ssot-rules/06-show-dont-show-discipline.md)

## Why one walkthrough

Per user directive 2026-04-19: pb3a and pb3b use the same reporting surface. Writing two separate walkthroughs creates
drift. This doc is the single click-path; pb3a and pb3b overlay narrative framing on top without forking the path.

The pb3a overlay frames the walkthrough as a regulated-activity view (transaction reporting, best-execution, supervisory
artifacts take the foreground). The pb3b overlay frames the walkthrough as an allocator view (positions, P&L, NAV, fee
accrual, investor statements take the foreground). The underlying components are identical; the framing differs.

## Pre-conditions

Before opening the walkthrough, confirm:

- The prospect is logged into staging (`odum-research.co.uk`) with a demo user provisioned to the correct restriction
  profile (IM or Reg Umbrella).
- The demo firm's synthetic data has been seeded (see
  [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) for seeding expectations).
- The sales person has the account-intelligence record open in a side panel (see
  [`../demo-ops/account-intelligence-record.md`](../demo-ops/account-intelligence-record.md)).

## The click-path

Five stops. Each stop names the route, the component, and the narrative anchor. The sales person's pb3a or pb3b overlay
supplies the audience-specific framing.

### Stop 1 — Reporting landing

**Route:** `/services/reports/overview`

**Components rendered:** `<PositionsSummary>`, `<PnlSummary>`, `<ExposureOverview>`, `<ReconciliationHealth>`, plus the
audience-specific panels (IM: `<FeeAccrual>`, `<InvestorStatementIndex>`; Reg Umbrella: `<TransactionReport>`,
`<BestExEvidence>`, `<SupervisoryArtifactIndex>`).

**Narrative anchor (both audiences):** "This is the landing page Odum uses internally. Your view is filtered to your
scope by entitlement; the components are the same." Sales person says rule-02 framing:
[rule 09](../_ssot-rules/09-internal-commercial-oneliners.md) expansion for the service.

**Data-source check:** Verify the page renders the demo firm's synthetic data, not an empty state or another demo firm's
data. Entitlement slicing is the proof point; if slicing failed, stop and fix before proceeding.

### Stop 2 — Positions and P&L

**Route:** `/services/trading/positions` + `/services/trading/pnl`

**Components rendered:** `<PositionsTable>`, `<PnlAttributionChart>`, `<ExposureSummary>` across instrument types.

**Click sequence:**

1. Open positions table. Filter by instrument type. Narrate: "Every position, live. Reconciled against venue records via
   the reconciliation pipeline — that's the next stop."
2. Open a single position drill-down. Show the fills that produced it, the current exposure, the attributed P&L.
3. Switch to P&L attribution. Narrate: "This is the same component Odum uses to monitor its own positions."

**Audience overlay:**

- **pb3b (IM):** name the allocator-share-class scope. "What you see is your allocation. Other allocators do not
  appear."
- **pb3a (Reg Umbrella):** name the regulated-activity scope. "Positions filtered to your firm's regulated activity."

### Stop 3 — Reconciliation

**Route:** `/services/reports/reconciliation` (or the corresponding route on the live UI)

**Components:** `<ReconciliationPanel>`, break-resolution view.

**Click sequence:**

1. Open reconciliation summary. Show the count of clean fills vs breaks in the demo data.
2. Open one break. Show the diff (instruction vs venue fills). Narrate: "Breaks are surfaced, investigated, resolved.
   Every break is traceable to the instruction and the venue record."

**Audience overlay:** both audiences get the same framing. Reconciliation is operational credibility; it is the same
process whether the client is IM or Reg Umbrella.

### Stop 4 — Audience-specific panel

Audience overlay takes foreground. This is the stop that differs in emphasis between pb3a and pb3b; the component
rendering is still shared.

**pb3a (Reg Umbrella):**

1. Open `/services/regulatory/transaction-reporting` (or equivalent). Filter transactions by instrument and venue.
2. Drill into a transaction. Show the best-execution evidence that ties the transaction to the MIFID best-ex claim.
3. Switch to the supervisory-artifact index. Show the shape of artifacts (quarterly compliance reports, MLRO summaries,
   attestations).

**pb3b (IM):**

1. Open `/services/investment-management/nav` (or equivalent). Show share-class NAV across time for a Pooled structure,
   or the SMA's NAV for an SMA.
2. Show fee accrual — management fee, performance fee if applicable.
3. Open the investor-statement generation path. Show the artifact a statement looks like without generating a real one.

### Stop 5 — Audit trail

**Route:** `/services/reports/audit-trail`

**Components:** `<AuditTrail>` with filter by instruction / fill / user action.

**Click sequence:**

1. Open the audit trail. Filter to a specific instruction id.
2. Show every event — instruction received, algo selected, order sent, fills arrived, reconciliation, reporting update.
3. Narrate: "This is the trail a diligence visit would walk. The shape of the artifact is what you see today."

**Audience overlay:** both audiences see the same audit trail. It closes the walkthrough.

## What not to show during this walkthrough

Per [rule 06](../_ssot-rules/06-show-dont-show-discipline.md). Every one of the following stays off the walkthrough; the
specific exclusions for pb3a and pb3b appear in those playbooks' §7.

- Internal ops routes (`/admin/*`, `/ops/*`, `/config/*`, `/devops/*`) — HIDDEN-ENTIRELY.
- Internal compliance SOPs or MLRO workbooks — HIDDEN-ENTIRELY.
- Other clients' data — HIDDEN-ENTIRELY (entitlement slicing enforces).
- DART research / promote / strategy-authoring surfaces — HIDDEN-ENTIRELY for IM, LOCKED-VISIBLE with upgrade message
  for Reg Umbrella combined with DART engagement.
- Pre-BACKTESTED maturity strategy slots — HIDDEN-ENTIRELY.
- Internal cost / Tier A / Tier B pricing — HIDDEN-ENTIRELY.
- Raw data feeds — HIDDEN-ENTIRELY per [rule 07](../_ssot-rules/07-data-licensing-boundaries.md).

## Session close

The walkthrough closes with a named next commitment:

- **pb3b (IM):** agree the mandate signing date.
- **pb3a (Reg Umbrella):** agree the onboarding kickoff date.

If the prospect surfaces a reservation, capture verbatim in the account-intelligence record. If they commit, the record
transitions to onboarding ownership.

## Playwright spec

The walkthrough is covered by `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` with persona
overlays for IM and Reg Umbrella. See
[`../implementation-mapping/playbook-to-qa-coverage.md`](../implementation-mapping/playbook-to-qa-coverage.md) for the
coverage mapping.

## Cross-references

- [shared-reporting-core.md](shared-reporting-core.md) — definition of the shared surface
- [same-system-principle.md](same-system-principle.md) — rule 03 implementation
- [../experience/regulatory-demo.md](../experience/regulatory-demo.md) — pb3a overlay
- [../experience/investment-management-demo.md](../experience/investment-management-demo.md) — pb3b overlay
- [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md) — profiles that seed demo data
- [../demo-ops/account-intelligence-record.md](../demo-ops/account-intelligence-record.md) — session-close capture
- [rule 03](../_ssot-rules/03-same-system-principle.md)
- [rule 06](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 07](../_ssot-rules/07-data-licensing-boundaries.md)
