---
doc_type: codex-ssot
title: Rule 08 — Pricing principles
summary:
  "Pricing principles — two external tiers (A cost-plus variable / B fixed upfront+monthly), per-block mixable,
  twelve-month minimum, internal-cost column codex-private, exclusivity + custom premiums Tier-B-only; actual numbers
  live only in commercial-model/pricing-building-blocks.md."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin, sales]
tags: [customer-journey, sales, cost, dart, registry]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md,
  ]
created: 2026-04-19
authoritative_for: [pricing principles (two-tier building-block model)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/cash-deployment-plan.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 08 — Pricing principles

> Two external tiers, per-block mixable, twelve-month minimum. Internal cost is codex-private. Exclusivity premiums are
> Tier B only. Numbers are not in this file.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On pricing (rule 08)". Tier structure locked
2026-04-19.

## Principles

### Two external tiers

**Tier A — cost-plus (variable).**

- Underlying variable cost pass-through with a thin margin.
- No upfront fee.
- Low barrier to entry.
- Usage-linked billing where the underlying block has usage semantics (venue fees, analytics compute).
- Suitable for prospects who want to start small and ramp.

**Tier B — fixed (upfront + monthly).**

- Fixed upfront fee paid at engagement start.
- Fixed monthly fee thereafter, independent of usage.
- Predictable revenue for Odum; predictable cost for client.
- Unlocks exclusivity / non-compete and custom solution premiums (neither available on Tier A).
- Suitable for institutional prospects who need budget certainty and deeper commitment.

### Twelve-month minimum commitment

Both tiers carry a minimum twelve-month commitment. Shorter engagements are not a standard option.

Rationale: onboarding a DART or IM or Reg Umbrella client involves provisioning, legal review, compliance signoff, venue
setup, and per-client API-key issuance. The twelve-month floor recovers that fixed cost and aligns client time-horizon
with the operational reality of running a regulated infrastructure engagement.

### Internal cost column is codex-private

Every building block has three numbers internally:

1. **Internal monthly cost** — what it costs Odum to provide the block. Infrastructure + licensing + support + allocated
   operational overhead.
2. **Tier A price** — internal cost + thin margin. Passed through to client with usage overlay where applicable.
3. **Tier B price** — upfront + monthly, priced for predictability and client commitment rather than direct cost
   recovery.

The internal cost number **never** appears in any client-facing document, pricing sheet, commercial proposal, demo
environment, or public marketing asset. It lives only in:

- `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md` (Stage 2 output — codex-private by directory
  convention; not rendered in any client-facing UI).
- Odum finance analysis exports.
- Board/investor materials clearly marked internal.

A client-facing pricing doc, quote, demo script, or website page that surfaces internal cost is a rule-08 violation.
Audit for leakage before any external publication.

### Per-block tier mixability

Clients can buy different blocks on different tiers. A typical engagement might look like:

- Reporting core on Tier B (institutional-grade SLA matters — client wants certainty).
- Strategy-service entry on Tier B.
- Venue pack for primary venues on Tier B.
- Venue pack for marginal venues on Tier A (usage-variable; doesn't warrant upfront commitment).
- Analytics pack on Tier A (ramps with usage).

There is no "must be all Tier A" or "must be all Tier B" rule. Per-block selection is a commercial negotiation.

### Exclusivity and custom premiums — Tier B only

- **Exclusivity / non-compete premium** — client pays to restrict Odum from offering the same capability to direct
  competitors, usually scoped by asset class, venue set, or strategy family. Only negotiable on Tier B. Expressed as a
  percentage uplift on the Tier B fixed monthly.
- **Custom solution premium** — client pays for bespoke feature development or non-standard integrations. Upfront +
  uplift on monthly. Tier B only.

Tier A does not unlock either premium. Clients who want exclusivity must be on Tier B for the blocks that exclusivity
covers.

### No raw-data resale

Cross-reference rule 07 (`07-data-licensing-boundaries.md`). DART is sold as enriched platform services built on top of
underlying data sources. Pricing can reflect the fact that certain blocks require access to data-sensitive inputs
(licensing cost flows into internal cost), but client-facing pricing never frames the product as raw-data resale. A
"Tier A raw data feed" line item is a rule-07 and rule-08 violation.

### Numbers live in Stage 2

This rule file defines the structure and discipline. The actual numbers per block per tier are populated in Stage 2
`commercial-model/pricing-building-blocks.md` by Odum finance. Stage 2 ships with `TBD` stubs; finance populates
post-Stage-2 merge.

When numbers arrive:

- Follow the structure defined here (three columns: internal / Tier A / Tier B, with Tier B split upfront + monthly).
- Respect the codex-private column.
- Update Stage 3C's `cost(combo, tier)` derivation formula so it reads from the populated pricing doc.

## Building-block dimensions

Pricing structure spans the thirteen blocks from rule 05 (`05-building-block-dimensions.md`):

1. Reporting core
2. Regulatory umbrella reporting
3. IM allocator reporting
4. Strategy-service entry
5. Instructions integration
6. Research / promote pipeline
7. Execution layer
8. Venue packs
9. Chain packs
10. Instrument-type packs
11. Analytics packs
12. Exclusivity / non-compete premium
13. Custom solution premium

Blocks 12 and 13 are Tier-B-only premiums, not standalone blocks priced the same way as 1–11.

## Worked example — same prospect, two pricing shapes

**Prospect:** a DeFi-native fund with a working signals strategy (resolves to `(Client, downstream)` per rule 04).

Blocks they need:

- Reporting core
- Strategy-service entry
- Instructions integration
- Execution layer
- Venue packs × 3 (their 3 primary venues)
- Chain packs × 2 (their 2 primary chains)
- Instrument-type pack × 2 (perps + spot)
- Reconciliation depth (part of reporting core)

**Tier A pricing shape:**

- No upfront. Usage-variable monthly costs per block with thin margin pass-through.
- Total month-1 commitment: small fixed baseline (reporting core + strategy-service entry) + usage-scaled execution +
  venue + chain + analytics.
- Estimated year-1 outlay: scales with trading volume. Potentially very low if volume is low; can grow substantially at
  scale.

**Tier B pricing shape:**

- Upfront fee covering onboarding, venue + chain provisioning, reconciliation setup.
- Monthly fixed covering all selected blocks.
- No usage-scaling surprise.
- Exclusivity negotiable (e.g. "Odum will not offer this execution-layer + venue-pack combo to another stat-arb DeFi
  fund within 18 months").

**Hybrid (most common in practice):**

- Tier B on reporting core, strategy-service entry, instructions integration (the sticky long-term blocks).
- Tier A on venue packs × 3 (marginal, volume-variable).
- Tier A on analytics pack (low commitment, high value scaling).
- Result: predictable core, variable edge.

## Enforcement rules

1. **No internal cost leakage.** Audit every client-facing doc, quote, demo, and website page. Internal cost column
   never appears externally.
2. **12-month floor is non-negotiable.** Shorter engagements require explicit leadership override and a separate
   contract structure; treat as bespoke.
3. **Exclusivity requires Tier B.** Never offer exclusivity discounts to a Tier A client. Route the conversation to a
   Tier B upgrade for the covered blocks.
4. **Per-block tier is decided in commercial negotiation.** Don't force an all-A or all-B default. The mixability is the
   point.
5. **Raw data is never a Tier A block.** Any quote line that reads as data-resale violates rule 07; rewrite as
   enriched-analytics or venue-access framing.
6. **Numbers live in one place.** `commercial-model/pricing-building-blocks.md` is the single source. No shadow pricing
   sheets.
7. **Pricing logic feeds Stage 3C.** When numbers populate, update the derivation engine's `cost(combo, tier)` formula
   to read from the doc. Never hardcode prices in UI or services.

## Stage 3 implications

Rule 08 shapes three Stage-3 design decisions:

1. **Stage 3C derivation engine** — `cost(combo, tier)` has three output columns (internal, Tier A, Tier B
   upfront+monthly). Consumers access only the columns their audience warrants. The billing service gets the external
   columns; Odum finance dashboards get internal.
2. **Stage 3B registry** — building-block identifiers are stable across the pricing doc, demo restriction profiles, and
   production entitlements. Adding a block requires adding it in one place (the registry); pricing, demo, prod all pick
   it up.
3. **Stage 3E refactor plan** — "pricing engine service" is a G3 item. Reads the populated `pricing-building-blocks.md`,
   exposes `cost(combo, tier)` via internal API, enforces the codex-private column via access-control. Numbers populate
   from finance as a separate (non-codex) commit.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On pricing (rule 08)"
- [`05-building-block-dimensions.md`](05-building-block-dimensions.md) — the 13 blocks priced here
- [`07-data-licensing-boundaries.md`](07-data-licensing-boundaries.md) — raw-data guardrail
- [`04-dart-commercial-axes.md`](04-dart-commercial-axes.md) — axis resolution picks which blocks are in scope per cell
- [`10-strategy-instruction-schema-principles.md`](10-strategy-instruction-schema-principles.md) — instruction-schema
  fit depth becomes a pricing dimension inside blocks 5 and 7 (instructions integration + execution layer)
- [Stage 2 `commercial-model/pricing-building-blocks.md`](../../../plans/ai/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
  — numbers populate here
- [Stage 3 Phase 3C derivation engine](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md) —
  `cost(combo, tier)` formula
