---
scope: [sales, admin]
---

# Pricing Building Blocks — Structure (Numbers TBD)

> Three columns × thirteen rows. **Numbers are `TBD` stubs** — Odum finance populates post-Stage-2 merge as a separate
> (non-codex) commit per [rule 08 §Numbers live in Stage 2](../_ssot-rules/08-pricing-principles.md). The structure is
> locked; the numbers are out of scope for this commit.

**Rule source:** [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)

## Discipline reminders (rule 08)

Before any number is populated, the following are non-negotiable:

- **Internal cost column is codex-private.** Never appears in client-facing docs, quote lines, demo surfaces, or the
  website. Stays in this codex dir only. Rule 08 enforcement rule 1.
- **Twelve-month minimum commitment** applies to Tier A and Tier B. Rule 08 enforcement rule 2.
- **Per-block tier mixability.** A client can be Tier B on some blocks and Tier A on others. Rule 08 enforcement rule 4.
- **Exclusivity premium (block 12) and custom solution premium (block 13) are Tier-B-only modifiers.** They do not
  appear without a Tier B base. Rule 08 enforcement rule 3.
- **No raw data on any tier.** Raw-data-framed line items are rule-07 + rule-08 violations.
- **Numbers live in one place.** This doc. No shadow pricing sheets. Rule 08 enforcement rule 6.

## The pricing table

Three columns, thirteen rows. Internal column stays codex-private; Tier A is cost-plus (variable); Tier B is fixed
upfront + fixed monthly.

| #   | Block                                  | Internal monthly cost | Tier A (cost-plus, variable)           | Tier B (fixed upfront + monthly)                         |
| --- | -------------------------------------- | --------------------- | -------------------------------------- | -------------------------------------------------------- |
| 1   | Reporting core                         | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 2   | Regulatory umbrella reporting          | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 3   | IM allocator reporting                 | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 4   | Strategy-service entry                 | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 5   | Instructions integration               | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 6   | Research / promote pipeline            | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 7   | Execution layer                        | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 8   | Venue packs (per venue or venue group) | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 9   | Chain packs (per chain)                | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 10  | Instrument-type packs (per type)       | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 11  | Analytics packs (per family)           | TBD — Odum finance    | TBD — Odum finance (cost-plus monthly) | TBD — Odum finance (upfront) + TBD (monthly)             |
| 12  | Exclusivity / non-compete premium      | n/a (modifier)        | Not available on Tier A                | TBD — Odum finance (percentage uplift on Tier B monthly) |
| 13  | Custom solution premium                | n/a (modifier)        | Not available on Tier A                | TBD — Odum finance (upfront) + TBD (monthly uplift)      |

### Licensing-constraint notes per block

Some blocks carry a licensing-constraint flag per [rule 07](../_ssot-rules/07-data-licensing-boundaries.md). The
licensing constraint shapes internal cost and the client-facing framing. Finance should note any upstream-licensing
tightness inline when populating internal cost.

| Block | Licensing constraint                                                                                 |
| ----- | ---------------------------------------------------------------------------------------------------- |
| 8     | Per-venue licensing terms govern redistribution of venue data. Odum-enriched output only.            |
| 9     | Chain-specific data providers' terms govern on-chain data redistribution. Odum-enriched output only. |
| 10    | Instrument-type-specific data sources may tighten (e.g., options chain licensing).                   |
| 11    | Analytics packs drawing on data-sensitive inputs inherit the upstream source's licensing terms.      |

Blocks 1, 2, 3, 4, 5, 6, 7, 12, 13 do not carry upstream-data-licensing constraints by default.

### Schema depth as a pricing dimension inside block 5 and block 7

Per [rule 10 §Schema depth as a pricing dimension](../_ssot-rules/10-strategy-instruction-schema-principles.md) and rule
05 block 5 description, instruction-schema depth (minimal / standard / rich) shapes the block 5 price. Three sub-lines
per tier:

| Block 5 depth | Internal           | Tier A             | Tier B                                                                    |
| ------------- | ------------------ | ------------------ | ------------------------------------------------------------------------- |
| Minimal       | TBD — Odum finance | TBD — Odum finance | TBD — Odum finance upfront + monthly                                      |
| Standard      | TBD — Odum finance | TBD — Odum finance | TBD — Odum finance upfront + monthly                                      |
| Rich          | TBD — Odum finance | TBD — Odum finance | TBD — Odum finance upfront + monthly (often with block 13 custom premium) |

## How numbers populate

Odum finance is responsible for populating the TBD values. The process:

1. **Finance-drafts pass.** Finance produces an initial set of numbers using internal cost analysis, market benchmarks,
   and the per-block commercial rationale documented in
   [`../_ssot-rules/08-pricing-principles.md`](../_ssot-rules/08-pricing-principles.md).
2. **Leadership review.** Finance's draft is reviewed against commercial strategy (where the firm wants to land across
   DART vs IM vs Reg Umbrella buyers; where exclusivity premiums should bite; the usage-variable shape on Tier A packs).
3. **Populated commit.** Numbers replace TBD in this table. The commit is explicitly a finance commit, separate from the
   Stage 2 doc commit. The commit message tags it as `chore(pricing): populate TBD numbers per finance 2026-MM-DD`.
4. **Stage 3C derivation update.** Once numbers populate, the Stage 3C `cost(combo, tier)` formula reads from this doc.
   See [`../infra-spec/stage-3c-derivation-engine.md`](../infra-spec/stage-3c-derivation-engine.md).

No numbers leak to client-facing surfaces in the interim. The commercial-model docs are codex-private; demo, quote, and
website surfaces do not reference this doc directly.

## What this doc does not do

- Does not express blended / bundled pricing. All pricing is per-block per-tier.
- Does not express discount structures. Discounts, if any, are captured in quote-specific commercial negotiation; this
  is the list-price SSOT.
- Does not express transaction volume tiers within a block. Block 7 (execution layer) on Tier A has usage-variable
  pricing; the structure of that variable function (per-fill, per-notional) is inside block 7's internal pricing model,
  noted by finance when they populate.

## Cross-references

- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — the discipline this doc enforces
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — the thirteen blocks
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — licensing constraint handling
- [rule 10 — instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md) — block 5 depth axis
- [building-block-packaging.md](building-block-packaging.md) — which blocks compose which packages
- [fixed-vs-variable-commercials.md](fixed-vs-variable-commercials.md) — Tier A vs Tier B decision
- [exclusivity-and-noncompete.md](exclusivity-and-noncompete.md) — block 12 modifier
- [../infra-spec/stage-3c-derivation-engine.md](../infra-spec/stage-3c-derivation-engine.md) — Stage 3C reads this doc
  once numbers populate
