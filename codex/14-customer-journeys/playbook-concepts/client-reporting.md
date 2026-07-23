---
doc_type: codex-ssot
title: Client Reporting — the shared surface
summary:
  The /services/reports/* tree (12 pages) is the ONE shared client-reporting surface for both the IM (pb3b) and Reg
  Umbrella (pb3a) demos and real clients — same code, only the narrative framing differs; Pooled vs SMA changes the
  report shape via a fund-context switcher, not the surface.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [client-reporting, ui, reporting, fund, sma, page-triage]
related:
  [
    ../playbooks/03a-demo-reg-umbrella.md,
    ../playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
  ]
created: 2026-04-19
authoritative_for: [client-reporting UI surface (/services/reports/* shared IM+Reg)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/page-triage/triage-matrix.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Client Reporting — the shared surface

The `/services/reports/*` tree is the ONE client-reporting surface. It's used by BOTH the Investment Management playbook
(pb3b) AND the Regulatory Umbrella playbook (pb3a). Same features, same reporting, same code. Only the **narrative
framing** differs.

> User quote: "investment management (all the same as reg umbrella / coverage same features same reporting)"

> User quote: "SMA vs fund different for client reporting which is the demo playbook for investment management AND reg
> umbrella"

## Route tree

| Route                               | Purpose                                                                          |
| ----------------------------------- | -------------------------------------------------------------------------------- |
| `/services/reports/overview`        | Landing — high-level P&L + quick links                                           |
| `/services/reports/performance`     | Performance attribution (by strategy, by venue, by asset class)                  |
| `/services/reports/nav`             | NAV calculation, per share class                                                 |
| `/services/reports/invoices`        | Fee invoices (management fee, performance fee per high-water mark)               |
| `/services/reports/ibor`            | Investment book of record                                                        |
| `/services/reports/settlement`      | Settlement status, T+1 reconciliation                                            |
| `/services/reports/reconciliation`  | Position + cash reconciliation vs venue statements                               |
| `/services/reports/regulatory`      | MiFID II transaction reporting, best-execution reports, regulator-facing exports |
| `/services/reports/analytics`       | Performance analytics (Sharpe, Sortino, max drawdown, etc.)                      |
| `/services/reports/trades`          | Trade blotter (with filters)                                                     |
| `/services/reports/executive`       | Executive summary report (board-level KPIs)                                      |
| `/services/reports/fund-operations` | Fund ops dashboard (operational KPIs)                                            |

All 12 pages exist today but most are orphans from the audit — not linked from the landing or from nav. Phase 3 wires
them via a unified sub-tab pattern.

## Why shared across IM and Reg Umbrella

The underlying data shapes — NAV, P&L, positions, trades, regulatory filings — are structurally identical whether the
client is:

- Allocating capital to an Odum strategy (IM)
- Running their own activity under Odum's FCA umbrella (Reg Umbrella)

In both cases there's a **fund** with **positions** held for **clients**. Reporting derives from those three primitives.
The only difference is who owns the P&L (allocator in IM, umbrella-client in Reg Umbrella) — a metadata label, not a
structural difference.

## Structured by SMA vs Pooled

The Pooled-vs-SMA choice (see [sma-vs-pooled.md](sma-vs-pooled.md)) changes the reporting shape but not the surface:

| Report         | Pooled                                                         | SMA                                       |
| -------------- | -------------------------------------------------------------- | ----------------------------------------- |
| NAV            | ONE fund NAV + per-share-class allocation                      | Per-client NAV (each client has own fund) |
| Invoices       | Per share class (grouped by fund)                              | Per client (one fund each)                |
| Trade blotter  | Fund-level; attribution to share classes via allocation engine | Per-client; direct attribution            |
| Regulatory     | Fund-level transaction reporting                               | Per-client transaction reporting          |
| Reconciliation | Fund-level                                                     | Per-client                                |

UI handles the difference via a fund-context switcher — same pages, different filtered views.

## Demo narrative (pb3a vs pb3b)

Both demos walk the same screens. Framing differences captured in the playbook docs:

- [pb3a framing (Reg Umbrella)](../playbooks/03a-demo-reg-umbrella.md)
- [pb3b framing (IM)](../playbooks/03b-demo-im.md)

## Primary content sources

- Implementation plan:
  [client_lifecycle_platform_2026_04_05.plan.md](../../../plans/archive/client_lifecycle_platform_2026_04_05.plan.md)
- Share class architecture:
  [../../04-architecture/share-class-architecture.md](../../04-architecture/share-class-architecture.md)

## Orphan concerns

Per static audit, 9 of the 12 reports/\* pages have no direct inbound link — they're tab-only. Phase 3 wires them into a
sub-nav pattern similar to `PROMOTE_LIFECYCLE_NAV` — one config object drives tab rendering for every report sub-page.

## Related

- Playbook pb3a: [../playbooks/03a-demo-reg-umbrella.md](../playbooks/03a-demo-reg-umbrella.md)
- Playbook pb3b: [../playbooks/03b-demo-im.md](../playbooks/03b-demo-im.md)
- SMA vs Pooled: [sma-vs-pooled.md](sma-vs-pooled.md)
- Fund hierarchy: [fund-org-hierarchy.md](fund-org-hierarchy.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
