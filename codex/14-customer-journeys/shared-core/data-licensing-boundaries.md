---
doc_type: codex-ssot
title: Data Licensing Boundaries — Expanded Reference
summary:
  Rule-07 expansion — the enriched-vs-raw inventory of what DART sells (analytics, positions/P&L, TCA, reconciliation)
  vs never sells (raw ticks, reference dumps, fixture lists). The test — client pays for what Odum did to the data, not
  the data itself. Includes copy-audit checklist + upstream-licence pre-ship audit.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [data-licensing, sales, cost, dart, audit, data-quality]
related:
  [
    ../_ssot-rules/07-data-licensing-boundaries.md,
    ../_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/shared-core/venue-chain-instrument-scope.md,
    ../commercial-model/pricing-building-blocks.md,
  ]
created: 2026-04-20
authoritative_for: [data-licensing enriched-vs-raw inventory (rule 07 expansion)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/shared-core/README.md,
    /codex/14-customer-journeys/shared-core/competitive-landscape.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Data Licensing Boundaries — Expanded Reference

> Full version of [rule 07](../_ssot-rules/07-data-licensing-boundaries.md). Enumerates what DART sells (enriched
> platform services) and what DART does not sell (raw data). Notes where internal pricing may reflect data-sensitive
> inputs without leaking into client-facing framing.

**Rule source:** [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md)

## The boundary

Odum sells enriched platform services. Odum does not resell raw data. The internal cost model may include data-licensing
inputs; the external framing never does.

This doc expands rule 07 into two concrete inventories — what counts as enriched vs raw — and names the pricing /
proposal language discipline that keeps the boundary intact.

## What DART sells (enriched services)

Every line on every client-facing quote or proposal must frame the product as one of the following. Each is an enriched
service; none is raw data.

| Enriched output                                   | What the client gets                                                 |
| ------------------------------------------------- | -------------------------------------------------------------------- |
| Analytics derived from underlying data            | Factor exposures, regime classifications, execution-quality measures |
| Positions + P&L from client's own fills           | Through Odum's execution + reconciliation stack                      |
| Backtested strategy performance                   | From historical data under Odum's research licence                   |
| Reconciliation outputs                            | Venue-side data reconciled with client instructions                  |
| Research-surface workflows                        | Interrogate data through Odum's enriched models                      |
| Monitoring + reporting surfaces                   | Built on top of Odum's processed data                                |
| Execution algorithms + TCA                        | Algo selection + measurement, not a raw fill feed                    |
| Cross-client anonymised aggregates (with consent) | Odum-enriched derivative products                                    |

## What DART does NOT sell (raw)

No quote, proposal, demo script, or website page frames any of the following as a product. Internal engineering may
ingest and process these; the commercial surface never names them as line items.

| Raw output                                                           | Why it's not sold                                |
| -------------------------------------------------------------------- | ------------------------------------------------ |
| Stream of venue ticks passed through Odum's pipes with no enrichment | Redistribution — most upstream licences prohibit |
| Exchange reference-data dumps                                        | Redistribution rights rarely permit              |
| On-chain transaction-level dumps without derived analytics           | Publicly available from nodes; Odum adds nothing |
| Fixture lists as standalone product                                  | Licensing + commercial model don't fit           |
| Any product whose primary value is access to the underlying source   | Makes Odum a data vendor — Odum is not           |

The test: does the client pay for the data, or for what Odum did to the data? If "the data itself", rule 07 violation.

## Internal cost inputs vs external framing

Rule 07 is consistent with rule 08's private internal-cost column. Internal pricing may reflect:

- Licensing costs Odum pays for market-data access on venue packs (block 8).
- Licensing costs for on-chain data providers on chain packs (block 9).
- Licensing costs for feature / analytics data sources on analytics packs (block 11).

These costs flow into the internal cost column (rule 08, codex-private), which then sets Tier A cost-plus pricing. The
client sees Tier A / Tier B numbers framed as the enriched block price; never as "$X for data access".

The discipline: Stage 2's `commercial-model/pricing-building-blocks.md` carries a `licensing-constraint` note per block
where upstream licensing tightens the client-facing framing. Stage 3B's registry declares the `licensing_constraint`
flag per block; Stage 3C surfaces a warning when a proposed combination would require redistribution rights Odum doesn't
hold.

## Client-owned data is distinct

Rule 07 governs Odum's access to third-party data. It does NOT govern Odum's handling of client-originated data — their
positions, trades, exposures, P&L. That data belongs to the client; Odum processes and surfaces it back to them. Rule 06
visibility slicing plus the security controls in [`../../07-security/`](../../07-security/) govern client-data handling.
Rule 07 is third-party upstream; client data is client-owned.

## Cross-client aggregates

Odum may publish cross-client aggregates (anonymised, not attributable) as Odum-enriched products — inside the rule 07
boundary on the enriched side. Publishing requires consent at the contract level; default is no publication without
explicit written consent.

## Demo-mode constraint

Rule 07 hardens a specific rule 06 exclusion: demo prospects never see surfaces that would, in production, expose
underlying data sources directly. Demo data is Odum-enriched or synthetic. This preserves the enriched-service framing
through every walkthrough — see [`client-reporting-demo-walkthrough.md`](client-reporting-demo-walkthrough.md) for what
demo data looks like in practice.

## Upstream-licence audit — before a new venue / chain ships

Before a new venue pack or chain pack goes live:

1. Confirm the redistribution terms of the upstream source permit the enriched output Odum plans to expose.
2. Scope the pack to those terms. If the source's terms prohibit certain derivations, those derivations are not part of
   the pack.
3. Register the licensing constraint flag on the pack in the Stage 3B registry.
4. Audit every client-facing copy touchpoint for raw-data framing leakage.

## Copy-audit checklist

Every external copy surface (website page, proposal, demo script, quote line item) is scanned before ship for rule-07
violations:

- [ ] No "data subscription" framing
- [ ] No "tick feed" framing
- [ ] No "exchange data access fee" as a line item
- [ ] No "raw on-chain stream" framing
- [ ] No "data vendor" or "data reseller" descriptors
- [ ] Every line item references an enriched block (venue pack, chain pack, analytics pack, etc.)
- [ ] Questions about data provenance answered honestly about sources without reframing the product as a data
      subscription

## Cross-references

- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks 8, 9, 10, 11 carry
  data-sensitive inputs
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md) — demo-mode constraint
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — internal-cost column privacy
- [../../07-security/compliance.md](../../07-security/compliance.md) — compliance escalation path
- [venue-chain-instrument-scope.md](venue-chain-instrument-scope.md) — scope dimensions where licensing flags attach
- [../commercial-model/pricing-building-blocks.md](../commercial-model/pricing-building-blocks.md) —
  licensing-constraint notes per block
