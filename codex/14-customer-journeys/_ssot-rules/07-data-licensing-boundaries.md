---
doc_type: codex-ssot
title: Rule 07 — Data licensing boundaries
summary:
  "Data-licensing boundary — Odum sells enriched services, never raw-data resale — with the enriched-vs-raw test,
  internal-vs-external framing, the client-own-data carve-out, and the audit + compliance-escalation enforcement for
  raw-data framing leaks."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [customer-journey, sales, data-licensing, cost, compliance]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
  ]
created: 2026-04-20
authoritative_for: [data-licensing boundary (enriched-services-not-raw-resale)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 07 — Data licensing boundaries

> DART is enriched platform and research services built on top of underlying data sources. It is not direct raw-data
> resale. Internal pricing may use data-sensitive inputs; external framing always frames the product as enriched
> services.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On data licensing boundary (rule 07)".

## The boundary

Odum's data posture toward the outside world has one rule: **what Odum sells is an enriched service, never a raw feed.**

This has two sides:

1. **Internal side.** Odum ingests market data, on-chain data, reference data, fixture data, and news / event data under
   commercial and licensing agreements with the underlying sources. Those agreements vary: some permit derived analytics
   redistribution, some permit aggregated redistribution only, some permit internal-use-only. Odum's internal systems
   respect all of them.
2. **External side.** Every Odum client-facing product (DART, IM, Reg Umbrella) is framed and priced as enriched
   platform services. Clients pay for analytics, signals, execution integration, reporting — not for a raw tick feed.

## Why this matters

Three reasons:

- **Licensing compliance.** Most upstream data licences prohibit redistribution as raw data. Framing and selling Odum
  output as anything that looks like a raw feed creates licensing exposure.
- **Legal framing.** If Odum is in the business of reselling data, it is a data vendor, with data-vendor obligations
  (warranties, indemnities, exchange redistribution agreements). Odum is not in that business.
- **Pricing model integrity.** The two-tier building-block pricing in rule 08 works because blocks are enriched
  services. "Tier A raw data feed" collapses the structure.

## What counts as enriched vs raw

**Enriched (OK to sell):**

- Analytics derived from underlying data (factor exposures, regime classifications, execution-quality measures).
- Positions and P&L derived from the client's own fills through Odum's execution and reconciliation stack.
- Backtested strategy performance derived from historical data under Odum's research licence.
- Reconciliation outputs combining venue-side data with client instructions.
- Research-surface workflows that let a client interrogate data through Odum's enriched models.
- Monitoring + reporting surfaces built on top of Odum's processed data.

**Raw (not OK to sell):**

- A stream of venue ticks passed through Odum's pipes with no enrichment.
- Exchange reference-data dumps.
- On-chain transaction-level dumps without derived analytics.
- Fixture lists as a standalone product.
- Any product whose primary value is access to the underlying source rather than Odum's processing.

The line is sometimes blurry. The test: **does the client pay for the data, or for what Odum did to the data?** If the
answer is "the data itself", it's a rule-07 violation.

## Internal vs external framing

Rule 08 (pricing) and rule 05 (building blocks) operate internally with data-sensitive cost components. That is fine:

- Internal cost calculations for venue packs reflect the underlying data licensing costs Odum pays.
- Internal cost calculations for analytics packs reflect any underlying data-licence-driven inputs.
- The internal cost column stays codex-private (rule 08).

Externally, clients see:

- Tier A and Tier B prices for the enriched blocks.
- Framing that describes what the block does, not what underlying data it draws on.
- No line items that read as "raw data access fee" or "tick feed subscription".

When clients ask "where does this data come from", answer honestly about the data sources; do not answer by framing the
product as a data subscription. ("Venue pack includes reconciliation against Binance's post-trade feed. We're a DART
client of Binance data under their licence." — not: "Your Tier A fee includes a Binance data subscription.")

## Client-data reporting — distinct from rule 07

Reporting on a client's own data (their positions, their trades, their exposures, their P&L) is not rule-07-constrained.
That data belongs to the client; Odum is processing and surfacing it back. Rule 07 applies to Odum's access to
third-party data sources, not to Odum's handling of client-originated data.

Client data does have its own constraints: segregation, entitlement-scoped visibility (rule 06), and the security
controls in [../../07-security/](../../07-security/). Those are not rule 07.

## Cross-client aggregates

If Odum publishes cross-client aggregates — anonymised, aggregated, not attributable — those are Odum-enriched products
and sit on the enriched side of rule 07. Publishing must respect whichever client contracts govern the use of their data
for aggregate derivation. Default: no cross-client aggregate publication without explicit written consent at the
contract level.

## Demo-mode constraint

Rule 07 hardens a specific not-show item for rule 06: **demo prospects do not see surfaces that would, in production,
expose underlying data sources directly.** The demo data they see is Odum-enriched or synthetic. This preserves the
enriched-service framing even in walk-throughs.

## Enforcement rules

1. **Audit external copy for raw-data framing.** Every client-facing pricing doc, website page, demo script, and
   proposal deck is scanned for phrases that read as raw-data resale. Examples: "data subscription", "tick feed",
   "exchange data access fee", "raw on-chain stream". Rewrite as enriched services.
2. **Line items never reference raw data.** Quote line items describe Odum-enriched blocks: venue packs, chain packs,
   analytics packs. Never "Binance data feed — $X/mo" or similar.
3. **Upstream-licence audit before a new venue / chain / data source ships.** Before a new venue pack goes live, confirm
   the redistribution terms permit the enriched output Odum plans to expose to clients. If the terms are tighter than
   the default, scope the pack accordingly.
4. **Data-sensitive blocks get an internal licensing flag.** The block registry (rule 05 + Stage 3B) carries a
   licensing-constraint flag per block, so the derivation engine and pricing can honour upstream constraints without
   hardcoding per-block logic.
5. **No "Tier A raw data" combinations.** If a Tier A quote line reads as a raw-data pass-through, it's a joint rule-07
   and rule-08 violation. Rewrite.
6. **Rule 07 violations log to compliance.** Rule-07 breaches are compliance-adjacent. Log suspected breaches into the
   compliance audit trail (see [../../07-security/compliance.md](../../07-security/compliance.md)) rather than quietly
   fixing copy; pattern-level issues need to surface.

## Stage 2 implications

- `commercial-model/pricing-building-blocks.md` carries a licensing-constraint note per block where upstream licences
  tighten the client-facing framing.
- `commercial-model/dart-entry-points.md` expands rule 09's DART one-liner in rule-07-respecting language.
- `demo-ops/demo-restriction-profiles.md` encodes the rule-07 demo-mode constraint as a default exclusion.

## Stage 3 implications

Stage 3B's block registry carries licensing-constraint metadata per block. Stage 3C's derivation engine surfaces a
licensing-constraint warning when a proposed combination would require redistribution rights Odum doesn't hold.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On data licensing boundary (rule 07)"
- [`05-building-block-dimensions.md`](05-building-block-dimensions.md) — blocks 8/9/10/11 carry data-sensitive inputs
- [`06-show-dont-show-discipline.md`](06-show-dont-show-discipline.md) — rule 07 hardens not-show items about data
- [`08-pricing-principles.md`](08-pricing-principles.md) — no raw-data line items, enriched framing only
- [`../../07-security/compliance.md`](../../07-security/compliance.md) — compliance escalation path for suspected
  breaches
