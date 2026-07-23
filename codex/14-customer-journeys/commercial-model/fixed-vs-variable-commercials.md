---
doc_type: codex-ssot
title: Fixed vs Variable Commercials — Tier A vs Tier B Decision Tree
summary:
  Tier A (cost-plus variable, no upfront, no exclusivity) vs Tier B (fixed upfront + monthly, unlocks block-12/13
  premiums) decision tree — five per-block questions, per-block default-tier table, and the per-block mixability rule;
  both carry a twelve-month minimum commitment.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [sales, admin]
tags: [commercial-model, pricing, dart, tier-a-tier-b, building-blocks]
related:
  [
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
  ]
created: 2026-04-20
authoritative_for: [Tier A vs Tier B commercial-tier decision tree]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Fixed vs Variable Commercials — Tier A vs Tier B Decision Tree

> Tier A is cost-plus variable (no upfront, usage-linked). Tier B is fixed (upfront + fixed monthly, unlocks exclusivity
> and custom premiums). Per-block mixability means one engagement can mix tiers. This doc is the decision tree for which
> tier fits which block for which prospect.

**Rule source:** [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)

## The two tiers, restated

**Tier A — cost-plus (variable).**

- Underlying variable cost passed through with a thin margin.
- No upfront fee.
- Low barrier to entry.
- Usage-linked billing where the block has usage semantics (venue fees, analytics compute, execution volume).
- Suitable for prospects who want to start small and ramp.
- Does NOT unlock exclusivity (block 12) or custom solution (block 13) premiums.

**Tier B — fixed (upfront + monthly).**

- Fixed upfront fee at engagement start.
- Fixed monthly fee thereafter, independent of usage.
- Predictable revenue for Odum; predictable cost for client.
- Unlocks exclusivity / non-compete and custom solution premiums.
- Suitable for institutional prospects who need budget certainty and deeper commitment.

Both carry a **twelve-month minimum commitment.**

## Decision tree per block

Five questions per block. The answers push toward Tier A or Tier B.

1. **Is usage volume predictable?** High predictability → Tier B is defensible. Low predictability → Tier A may fit
   better. Tier A works when the client's ramp is slow and Tier A's variable billing aligns with their growth.
2. **Does the client want budget certainty?** Budget-certainty requirement → Tier B. Tier A's variable billing defeats
   certainty.
3. **Is this a sticky / core block for the engagement?** Core blocks (reporting core, strategy-service entry,
   instructions integration) that the client will use every day for the duration → Tier B preferred.
4. **Is this a marginal block?** Low-volume venue pack, experimental instrument type, early-stage analytics adoption →
   Tier A fits because usage grows slowly.
5. **Does the client want exclusivity or custom features on this block?** If yes, Tier B is required — Tier A does not
   unlock those premiums.

## Per-block tier preference

Defaults, based on typical prospect shapes. Real engagements negotiate per the above decision tree.

| Block                                   | Typical default tier | Rationale                                                                                       |
| --------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------- |
| 1 — Reporting core                      | Tier B               | Sticky core; allocators want SLA certainty; predictable                                         |
| 2 — Regulatory umbrella reporting       | Tier B               | Regulatory cover is high-certainty need                                                         |
| 3 — IM allocator reporting              | Tier B               | Fixed monthly aligns with allocator fund operation                                              |
| 4 — Strategy-service entry              | Tier B               | Core per-client runtime; daily use                                                              |
| 5 — Instructions integration            | Tier A or B          | Tier B if the client's signals flow is predictable; Tier A if ramp is slow                      |
| 6 — Research / promote pipeline         | Tier B               | Full DART clients commit to the research surface; high-use                                      |
| 7 — Execution layer                     | Tier A often         | Usage-variable (volume); Tier A aligns with actual execution cost; Tier B if volume predictable |
| 8 — Venue packs (primary)               | Tier B               | Primary venues are sticky                                                                       |
| 8 — Venue packs (marginal)              | Tier A               | Low-volume venues; usage-variable; Tier A margin reflects actual usage                          |
| 9 — Chain packs                         | Tier A or B          | Depends on chain volume; primary chains → Tier B, marginal → Tier A                             |
| 10 — Instrument-type packs              | Tier A or B          | Depends on volume per type                                                                      |
| 11 — Analytics packs                    | Tier A               | Often ramps with usage; Tier A aligns with value scaling                                        |
| 12 — Exclusivity premium (modifier)     | Tier B required      | Not available on Tier A                                                                         |
| 13 — Custom solution premium (modifier) | Tier B required      | Not available on Tier A                                                                         |

## Worked examples

### Example 1 — Conservative institutional

Large allocator. Wants budget certainty. Low tolerance for variable billing. Regulatory posture non-negotiable.

**Tier preference:** Tier B across all core blocks. Tier A only on marginal analytics packs where usage ramp matters.

### Example 2 — DeFi-native fund, mid-stage

Working signals flow. Ramping execution volume across venues and chains. Uncertain how two of their three primary venues
will perform over the engagement.

**Tier preference:**

- Tier B on reporting core, strategy-service entry, instructions integration (sticky, high-use).
- Tier B on one primary CeFi venue pack (the venue they're certain of).
- Tier A on two uncertain venue packs (let usage reveal the shape).
- Tier A on one chain pack (volume-variable), Tier B on one (primary, high-use).
- Tier A on analytics pack.

This is the hybrid shape from rule 08 §Per-block tier mixability — the most common in practice.

### Example 3 — Prop firm licensing Odum IP

Wants exclusivity on the Odum strategy IP for their scope. Predictable high-volume execution.

**Tier preference:** Tier B everywhere. Exclusivity premium (block 12) attached. Custom-solution premium (block 13) if
any bespoke integration is negotiated.

## When to push Tier B vs Tier A

Sales-conversation guidance:

- **Push Tier B when** the engagement is load-bearing for Odum's revenue predictability, the prospect is the type who
  values budget certainty, or exclusivity / custom features are in play.
- **Offer Tier A when** the prospect wants to start small, when the block is usage-variable by nature, or when the
  prospect's uncertainty about volume is genuine (not a negotiating posture).
- **Do not mix tiers on one block's sub-scope.** Per venue pack, the venue is Tier A or Tier B — not both. Different
  venue packs can carry different tiers; the same venue pack cannot.
- **Do not compromise on the twelve-month floor.** Shorter engagements require leadership override and a separate
  contract structure.

## Per-block tier mixability in practice

Rule 08 allows mixing across blocks. A typical shape (reporting Tier B + venue packs mostly Tier B + marginal venue
packs Tier A + analytics Tier A) is a normal engagement, not a concession. Don't force all-A or all-B.

## What Tier A does not unlock

- Block 12 (exclusivity / non-compete premium). Exclusivity is always Tier B.
- Block 13 (custom solution premium). Bespoke features are always Tier B.
- Any commercial posture that requires Odum to commit capacity or feature exclusivity. Those need the Tier B monthly
  guarantee.

If a Tier A prospect requests exclusivity, the conversation is: "exclusivity is a Tier B feature; what would it look
like to move these specific blocks to Tier B?" Not: "we can make exclusivity work on Tier A for this one time."

## Cross-references

- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — per-block semantics
- [pricing-building-blocks.md](pricing-building-blocks.md) — the 13-row pricing table
- [building-block-packaging.md](building-block-packaging.md) — standard packages + their typical tier shapes
- [exclusivity-and-noncompete.md](exclusivity-and-noncompete.md) — block 12 detail
- [dart-entry-points.md](dart-entry-points.md) — the three paths map to tier preferences
