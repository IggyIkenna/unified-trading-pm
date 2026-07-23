---
doc_type: codex-ssot
title: Org / Fund / Client Entity Model
summary:
  The four-level entity hierarchy (organisation → fund [Pooled/SMA] → client [share class] → API-key set) that powers IM
  allocator reporting, Reg Umbrella registration, and DART provisioning. Block entitlements (rule 05) attach at the
  API-key-set level; external-wrapper mandates (BTC FoF) attach at client level without entering the strategy catalogue.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin, sales]
tags: [playbooks, sales, strategy, registry, ui]
related:
  [
    ../playbook-concepts/fund-org-hierarchy.md,
    ../playbook-concepts/sma-vs-pooled.md,
    /codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md,
    /codex/14-customer-journeys/shared-core/shared-reporting-core.md,
  ]
created: 2026-04-20
authoritative_for: [org/fund/client/api-key-set entity model for experience surfaces]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Org / Fund / Client Entity Model

> The entity hierarchy that underpins IM allocator reporting, Reg Umbrella registration, and DART client provisioning.
> Reference for experience docs (pb2a, pb3a, pb3b); definitional input for Stage 3B's entitlement registry. Cites
> [rule 03](../_ssot-rules/03-same-system-principle.md) + [rule 05](../_ssot-rules/05-building-block-dimensions.md).

**Existing engineering sources** (authoritative):
[../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md)

- [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md). This doc re-frames them for the experience
  layer without duplicating their content.

## The hierarchy

Every paying relationship maps onto a four-level entity hierarchy:

```
organisation
  ├── fund (Pooled or SMA)
  │     ├── client (share class in a Pooled fund, or the sole client in an SMA)
  │     │     └── API-key set (venue credentials scoped to client + entitlement)
  │     └── client
  └── fund
```

- **Organisation** — the legal entity that signs with Odum. For IM allocators, this is the allocator firm. For Reg
  Umbrella, the firm operating under Odum's permissions. For DART, the client fund or prop firm.
- **Fund** — a Pooled vehicle or Separately Managed Account. One organisation can have multiple funds. Each fund has its
  own structural properties (custodian, venue set, regulatory permissions).
- **Client** — the capital-holder. In a Pooled fund, one fund has multiple clients represented as share classes. In an
  SMA, one fund has exactly one client.
- **API-key set** — venue credentials and service entitlements scoped to a specific client within a specific fund. Two
  clients in the same Pooled fund may have different API-key sets if their entitlement scope differs (rare but
  modelable).

## Why Pooled vs SMA matters

See [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md) for the full engineering treatment. Short
version for experience-layer usage:

- **Pooled fund.** One set of positions, one set of venue accounts, multiple share classes. NAV is struck at the fund
  level; per-client P&L is derived from share-class proportion. Operationally simpler; cross-client isolation is
  accounting, not physical.
- **SMA (Separately Managed Account).** Each client gets their own fund structure, their own venue accounts, their own
  API keys. Full physical isolation. Operationally heavier; per-client everything is a separate fund-shape entity.

The structural choice is a real decision with real cost consequences. Most allocators default to SMA for isolation; some
to Pooled for operational simplicity. The choice is made at onboarding, not re-negotiated per quarter.

### Which structural choice fits which audience

| Audience                              | Typical structure | Rationale                                                                             |
| ------------------------------------- | ----------------- | ------------------------------------------------------------------------------------- |
| IM allocator — single mandate         | SMA               | Isolation; allocator's own legal entity                                               |
| IM allocator — multi-mandate sleeve   | Pooled            | Sleeves are share classes inside one fund; simpler operationally                      |
| IM fund-of-fund aggregating managers  | Pooled            | Aggregate sleeves into one vehicle                                                    |
| Reg Umbrella — one firm, one activity | SMA               | Firm's activity scoped to its own entity structure                                    |
| Reg Umbrella — firm with sub-desks    | Pooled-analogue   | Sub-desks as "share classes"; operational consolidation                               |
| DART — fund with own strategy         | SMA or Pooled     | Depends on whether the fund has its own investors (Pooled) or is single-capital (SMA) |

Decisions are made case-by-case; the table gives default starting points.

## How the hierarchy powers experience surfaces

### IM allocator (pb2a, pb3b)

The allocator is the `organisation`. Their `fund` is Pooled (share-class NAV) or SMA (single client). The pb3b demo
renders the structure the allocator has chosen — SMA shows a distinct fund entity; Pooled shows share classes inside a
single fund. The allocator's view is filtered to their own `client` scope.

### Reg Umbrella firm (pb2c, pb3a)

The firm is the `organisation`. They operate under Odum's permissions as designated representative. Their `fund`
structure mirrors their own operational model — single activity (SMA-analogue) or sub-desk aggregate (Pooled-analogue).
The pb3a demo renders transaction reporting and supervisory artifacts scoped to their `organisation` view.

### DART client (pb2b, pb3c)

The client is the `organisation`. Their `fund` carries their own strategy IP (full pipeline) or signals flow
(signals-only). API-key sets are scoped to the instruction flow's venue / chain / instrument-type scope. The pb3c demo
renders the catalogue, terminal, and reporting for their `client` scope.

## Entitlement scope lives at the API-key set

The building-block entitlements (rule 05) attach to the API-key set level, not the client or fund level. This is
load-bearing: the same client in the same fund can have one API-key set for the execution layer and a distinct set for
reporting-only access, if the commercial shape requires.

| Level        | What is scoped there                                                        |
| ------------ | --------------------------------------------------------------------------- |
| Organisation | Contract, legal agreements, compliance posture                              |
| Fund         | Custodian, venue accounts (physical), regulatory permissions                |
| Client       | Share-class identity, capital allocation, fee schedule                      |
| API-key set  | Block entitlements (rule 05), demo restriction profile, maturity visibility |

Stage 3B's entitlement registry reads from the API-key-set level; Stage 3C's derivation engine resolves
`(client, api_key_set, route, block)` → `visible | locked-visible | hidden`.

## External-wrapper mandates

Some mandates do not consume Odum-system compute — Odum acts as **allocator**, not strategy operator. The canonical
example is the BTC Fund of Funds wrapper: a BTC client's 50 BTC mandate where Odum allocates to an external
fund-of-funds vehicle Odum does not run. Odum keeps 20% of the client's profits (~0.5 BTC/yr) as pure-margin revenue
with no system compute cost.

External wrappers are modelled against this hierarchy as follows:

- **NOT in the strategy catalogue.** There is no `(archetype, instrument, venue)` cell for the wrapper. No strategy
  lock-state applies. No strategy-service tenant slot is consumed. Catalogue filters do not surface the wrapper to any
  audience.
- **Surfaced ONLY in `client-reporting`** for the specific wrapper mandate. The allocator's client view shows the
  mandate as a standalone reporting line — external fund name, allocation, periodic return, Odum share booked — with no
  linkage to the strategy catalogue.
- **Entitlement attaches at the client level** via a `wrapper_mandate` flag on the API-key set (rule 05 block
  entitlements still live at the API-key-set level — see table above). The flag turns on the wrapper reporting line and
  nothing else.
- **No data-licensing exposure.** Because no Odum strategy IP is involved, rule 07 data-licensing boundaries do not
  apply to the wrapper's pricing or exposure.

Net effect: wrapper mandates are low-surface-area legacy-style engagements that attach to the client entity without
polluting the strategy catalogue or the lock-state machinery. See
[`strategy-allocation-lock-matrix.md`](strategy-allocation-lock-matrix.md) §BTC Fund of Funds for the canonical
lock-matrix treatment and
[`../commercial-model/im-profit-share-structures.md`](../commercial-model/im-profit-share-structures.md) §BTC Fund of
Funds wrapper for the commercial mechanic.

## Provisioning flow

See
[../implementation-mapping/demo-email-and-provisioning-flow.md](../implementation-mapping/demo-email-and-provisioning-flow.md)
for the sales-to-provisioning flow. Short version: onboarding creates one `organisation`, one or more `fund` records,
one or more `client` records, and one or more `api_key_set` records. The user-management-ui (referenced in
[../../../plans/ai/user_management_merge_2026_03_23.plan.md](../../../plans/ai/user_management_merge_2026_03_23.plan.md))
is the operating surface for this; the experience playbooks describe the shape, the impl plan specifies the build.

## Cross-references

- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — entitlement slicing over one
  underlying system
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks attach at API-key-set
  level
- [../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md) — engineering treatment
- [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md) — structural decision detail
- [../experience/im-decision-journey.md](../experience/im-decision-journey.md) — pb2a uses this model
- [../experience/investment-management-demo.md](../experience/investment-management-demo.md) — pb3b renders
  structure-specific views
- [../experience/regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md) — pb2c uses this model
- [../experience/dart-briefing.md](../experience/dart-briefing.md) — pb2b uses this model
- [share-class architecture plan](../../../plans/archive/share_class_architecture_2026_04_01.plan.md)
- [user-management merge plan](../../../plans/ai/user_management_merge_2026_03_23.plan.md)
