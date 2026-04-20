---
scope: [sales, admin]
---

# Pricing Building Blocks — 13-Row Anchor Ranges

> Three columns × thirteen rows, populated with **anchor ranges** aligned to the signals-only pricing table in
> [`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md). Ranges, not point values — these are
> sales anchors, not finance-signed-off specifics.
>
> **Internal-cost column: codex-private per
> [rule 08](../_ssot-rules/08-pricing-principles.md) §Internal cost column is codex-private. Numbers TBD pending Odum
> finance review.** Cost-column entries stay empty in this doc and never appear in any client-facing quote or demo.

**Rule source:** [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)

## Discipline reminders (rule 08)

Before any number is committed in a quote, the following are non-negotiable:

- **Internal cost column is codex-private.** Never appears in client-facing docs, quote lines, demo surfaces, or the
  website. Stays in this codex dir only. Rule 08 enforcement rule 1.
- **Twelve-month minimum commitment** applies to Tier A and Tier B. Rule 08 enforcement rule 2.
- **Per-block tier mixability.** A client can be Tier B on some blocks and Tier A on others. Rule 08 enforcement rule 4.
- **Exclusivity premium (block 12) and custom solution premium (block 13) are Tier-B-only modifiers.** They do not
  appear without a Tier B base. Rule 08 enforcement rule 3.
- **No raw data on any tier.** Raw-data-framed line items are rule-07 + rule-08 violations.
- **Numbers live in one place.** This doc (for DART blocks) plus
  [`im-profit-share-structures.md`](im-profit-share-structures.md) (for IM mechanics). No shadow pricing sheets.
  Rule 08 enforcement rule 6.

## The pricing table

Three columns, thirteen rows. Internal column stays codex-private; Tier A is cost-plus (variable); Tier B is fixed
upfront + fixed monthly. Ranges mirror the signals-only anchor table in
[`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md).

| #   | Block                                  | Internal monthly cost   | Tier A (cost-plus, variable)    | Tier B fixed monthly      | Tier B upfront         |
| --- | -------------------------------------- | ----------------------- | ------------------------------- | ------------------------- | ---------------------- |
| 1   | Reporting core                         | codex-private (TBD)     | cost-plus monthly               | £3-5k/mo                  | £10-20k                |
| 2   | Regulatory umbrella reporting          | codex-private (TBD)     | cost-plus monthly               | £8-15k/mo                 | £20-40k                |
| 3   | IM allocator reporting                 | codex-private (TBD)     | cost-plus monthly               | £3-6k/mo                  | £10-20k                |
| 4   | Strategy-service entry                 | codex-private (TBD)     | cost-plus per-tenant-slot       | £0.4-0.8k per strategy/mo | £5-10k                 |
| 5   | Instructions integration (see depth)   | codex-private (TBD)     | cost-plus per-depth             | £2-20k/mo (by depth)      | £5-15k                 |
| 6   | Research / promote pipeline            | codex-private (TBD)     | not available on Tier A         | £5-15k/mo bundled credits | £15-30k                |
| 7   | Execution layer                        | codex-private (TBD)     | cost-plus usage-variable        | £3-6k/mo                  | £10-20k                |
| 8   | Venue packs (per venue)                | codex-private (TBD)     | cost-plus per venue             | £1-2k per primary / £0.5-1k per marginal | £3-8k per venue |
| 9   | Chain packs (per chain)                | codex-private (TBD)     | cost-plus per chain             | £0.5-1.5k per chain/mo    | £2-5k per chain        |
| 10  | Instrument-type packs (per type)       | codex-private (TBD)     | cost-plus per type              | £1-3k per type/mo         | £3-6k per type         |
| 11  | Analytics packs (per family)           | codex-private (TBD)     | cost-plus per pack              | £0.5-3k per pack/mo       | £2-5k per pack         |
| 12  | Exclusivity / non-compete premium      | n/a (modifier)          | Not available on Tier A         | 20-200% uplift on Tier B monthly (by IP-power tier) | — |
| 13  | Custom solution premium                | n/a (modifier)          | Not available on Tier A         | 10-25% of build fee annualised | engineering-hours × loaded cost × 1.5-2× margin |

### Licensing-constraint notes per block

Some blocks carry a licensing-constraint flag per [rule 07](../_ssot-rules/07-data-licensing-boundaries.md). The
licensing constraint shapes internal cost and the client-facing framing. Finance should note any upstream-licensing
tightness inline when finalising internal cost.

| Block | Licensing constraint                                                                                 |
| ----- | ---------------------------------------------------------------------------------------------------- |
| 8     | Per-venue licensing terms govern redistribution of venue data. Odum-enriched output only.            |
| 9     | Chain-specific data providers' terms govern on-chain data redistribution. Odum-enriched output only. |
| 10    | Instrument-type-specific data sources may tighten (e.g., options chain licensing).                   |
| 11    | Analytics packs drawing on data-sensitive inputs inherit the upstream source's licensing terms.      |

Blocks 1, 2, 3, 4, 5, 6, 7, 12, 13 do not carry upstream-data-licensing constraints by default.

### Schema depth as a pricing dimension inside block 5

Per [rule 10 §Schema depth as a pricing dimension](../_ssot-rules/10-strategy-instruction-schema-principles.md) and rule
05 block 5 description, instruction-schema depth (minimal / standard / rich) shapes the block 5 price. Three sub-lines
per tier:

| Block 5 depth | Internal            | Tier A                   | Tier B monthly        | Tier B upfront                                            |
| ------------- | ------------------- | ------------------------ | --------------------- | --------------------------------------------------------- |
| Minimal       | codex-private (TBD) | cost-plus                | £2-4k/mo              | £5-10k                                                    |
| Standard      | codex-private (TBD) | cost-plus                | £4-8k/mo              | £8-15k                                                    |
| Rich          | codex-private (TBD) | cost-plus                | £8-20k/mo             | £10-15k (often with block 13 custom premium layered over) |

### Block 12 — exclusivity uplift by IP-power tier

Scaled by strategy scarcity. See
[`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md) §IP-power tier anchors for full definitions and worked
examples.

| IP-power tier                              | Example strategy                                            | Uplift on Tier B monthly |
| ------------------------------------------ | ----------------------------------------------------------- | ------------------------ |
| Commodity archetype                        | ML directional on liquid CeFi perps; perp-funding arb       | 20-30%                   |
| Specialised venue + archetype combo        | Hyperliquid market-making; Drift carry-basis                | 50-80%                   |
| Scarce venue access                        | Indian options NSE delta trading; Kalshi prediction markets | 80-120%                  |
| Uniquely differentiated multi-leg strategy | Custom DeFi stat-arb; novel event-driven multi-leg          | 120-200%                 |

Each exclusivity quote still computes a specific revenue-forgone × margin multiplier; the percentage above is an anchor,
not a fixed mark-up. See [`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md) §Premium structure.

## Row 14 — Signal leasing (separate commercial path)

Signal leasing sits **outside the DART 2×3 matrix** as a fourth commercial path (see
[`signal-leasing.md`](signal-leasing.md)). It is not a DART block row and should not be bundled into block-composition
quotes. Captured here for cross-reference because signal-leasing counterparties still buy against the Tier B floor
concept.

**Recommended pricing model: hybrid (Option 4 in [`signal-leasing.md`](signal-leasing.md)).**

| Component                  | Tier B range                                                     |
| -------------------------- | ---------------------------------------------------------------- |
| Floor monthly licence      | £10-20k/mo per counterparty                                      |
| Per-signal uplift          | £25-100 per signal (high-freq) / £200-500 per signal (sparse)    |
| Optional P&L share upsell  | 5% of counterparty's signal-attributable P&L (with audit rights) |

Alternative models — flat monthly licence, per-signal-only metering, pure rev-share — are documented in
[`signal-leasing.md`](signal-leasing.md) but the hybrid is recommended as the default commercial offering.

## Special-structure engagement notes

Some engagements do not compose cleanly from the 13-block Tier A/B grid. These deviations are documented below with
pointers to the canonical mechanic doc.

### IM engagement (Odum IM on own strategies) — NOT a block quote

IM is a `(Odum, *)` rule-04 cell; mechanics live in
[`im-profit-share-structures.md`](im-profit-share-structures.md).

- **No management fee** on allocated capital.
- **30-35% performance-share band** (30% commoditised, 35% specialised).
- **Platform-fee client choice** at mandate signing: Option A (+5% perf-share uplift) OR Option B ($500/mo flat
  platform-access fee).
- Block 1 (reporting core) + block 3 (IM allocator reporting) entitlements are bundled into the IM operating envelope;
  the client does not see a block-by-block quote.
- See [`im-profit-share-structures.md`](im-profit-share-structures.md) for full worked examples.

### CME co-invest special structure (asymmetric 70/10)

Unique mechanic — not covered by any Tier A/B row. Applies to the CME S&P ML mandate only.

- **$50k skin-in-the-game** from Odum alongside client allocation (initial $500k, ramping to $5M+).
- **70% of profits / 10% of losses** to Odum. Rationale: Odum brings the strategy IP; client brings most of the capital.
- Skin-scaling (flat $50k vs pro-rata) confirmed as **flat $50k year-1** default; see
  [`im-profit-share-structures.md`](im-profit-share-structures.md) §Scaling the skin-in-the-game.
- Fallback if client rejects the 70/10 asymmetry in negotiation: flat 10%-pari-passu (Odum share drops 70→10%).
  Document in contracting notes.

### India Options special structure ($100k onboarding + standard perf-share)

Applies to the India Options `(Odum, full-pipeline)` IM engagement.

- **$100k upfront onboarding** — new-venue (NSE options) integration + clearing + margin + options-specific
  infrastructure. Framed commercially as **block 13 custom premium** for the new-venue integration; amortised over three
  months at contracting.
- **Ongoing**: standard 30-35% performance-share + platform-fee client choice (same framework as BTC ML).
- The $100k covers the new-venue cost premium, so no higher perf-share band applies. See
  [`im-profit-share-structures.md`](im-profit-share-structures.md) §India Options.

### Elysium engagement — profit-share replaces block pricing post go-live

- Onboarding phase: **$125k fixed** (already paid + remaining $35k as of April 2026).
- Post go-live: **30% of Elysium's fees/returns** from the DeFi staked-basis strategy they operate via our stack.
- Replaces the block-composition Tier B quote that would otherwise apply to a signals-only DART engagement. Client
  prefers upside-aligned mechanics over flat Tier B monthly.
- **2026 revenue target**: $125k conservative / $200-230k aspirational with MEV + Solana + recursive-staking upsells.
- Block composition baseline (before the profit-share replaces it) is the Elysium Phase A worked example in
  [`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md) §Signals-only DART pricing model
  (~£24k/mo Tier B equivalent).

### Signal leasing — separate commercial path

See row 14 above and [`signal-leasing.md`](signal-leasing.md). Not a DART block row. Treat as a **fourth commercial
path** alongside DART, IM, Reg Umbrella.

## How numbers populate (finance process)

Odum finance owns the internal cost column and is responsible for tightening the Tier A/B external-facing ranges where
required. The process:

1. **Finance-drafts pass.** Finance produces internal cost numbers using cost analysis, market benchmarks, and the
   per-block commercial rationale documented in
   [`../_ssot-rules/08-pricing-principles.md`](../_ssot-rules/08-pricing-principles.md).
2. **Leadership review.** Finance's draft is reviewed against commercial strategy (where the firm wants to land across
   DART vs IM vs Reg Umbrella buyers; where exclusivity premiums should bite; the usage-variable shape on Tier A packs).
3. **Populated commit.** Internal cost numbers replace `codex-private (TBD)` entries; range tighteners (if any) replace
   the wide anchor ranges. Commit is finance-tagged: `chore(pricing): populate numbers per finance 2026-MM-DD`.
4. **Stage 3C derivation update.** Once numbers populate, the Stage 3C `cost(combo, tier)` formula reads from this doc.
   See [`../infra-spec/stage-3c-derivation-engine.md`](../infra-spec/stage-3c-derivation-engine.md).

No internal cost numbers leak to client-facing surfaces in the interim. The commercial-model docs are codex-private;
demo, quote, and website surfaces do not reference internal cost.

## What this doc does not do

- Does not express blended / bundled pricing. All pricing is per-block per-tier.
- Does not express discount structures. Discounts, if any, are captured in quote-specific commercial negotiation; this
  is the list-price SSOT.
- Does not express transaction volume tiers within a block. Block 7 (execution layer) on Tier A has usage-variable
  pricing; the structure of that variable function (per-fill, per-notional) is inside block 7's internal pricing model,
  noted by finance when they populate.
- Does not duplicate IM profit-share mechanics. IM lives in
  [`im-profit-share-structures.md`](im-profit-share-structures.md); block rows 1/3 above cover only the reporting
  entitlement portion of IM, not the perf-share side.

## Cross-references

- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — the discipline this doc enforces
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — the thirteen blocks
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — licensing constraint handling
- [rule 10 — instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md) — block 5 depth axis
- [../shared-core/dart-pricing-axes.md](../shared-core/dart-pricing-axes.md) — signals-only + full-DART anchor tables
- [im-profit-share-structures.md](im-profit-share-structures.md) — IM mechanics (perf-share, platform-fee choice, CME
  asymmetric, India Options, mean-rev migration, BTC FoF wrapper)
- [signal-leasing.md](signal-leasing.md) — fourth commercial path, hybrid pricing recommended
- [building-block-packaging.md](building-block-packaging.md) — which blocks compose which packages
- [fixed-vs-variable-commercials.md](fixed-vs-variable-commercials.md) — Tier A vs Tier B decision
- [exclusivity-and-noncompete.md](exclusivity-and-noncompete.md) — block 12 modifier, IP-power tier anchors
- [../infra-spec/stage-3c-derivation-engine.md](../infra-spec/stage-3c-derivation-engine.md) — Stage 3C reads this doc
  once numbers populate
