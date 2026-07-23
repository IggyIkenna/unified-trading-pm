---
doc_type: codex-ssot
title: Pricing Building Blocks — 13-Row Anchor Ranges
summary:
  The 13-block DART pricing anchor table (internal-cost / Tier A cost-plus / Tier B fixed monthly + upfront) with the
  codex-private internal-cost column allocated from the ~£34k/mo base burn; also block-5 depth pricing, block-12
  exclusivity uplift, signal-leasing row 14, and IM/CME/India/Elysium special structures.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, admin]
tags: [commercial-model, pricing, dart, building-blocks, tier-a-tier-b, exclusivity, cost]
related:
  [
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
    ../shared-core/dart-pricing-axes.md,
  ]
created: 2026-04-20
authoritative_for: [DART 13-block pricing anchor table (Tier A/B ranges + codex-private internal-cost column)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/cash-deployment-plan.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
  ]
owner:
last_reviewed:
code_refs: [unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation_cost.py]
---

# Pricing Building Blocks — 13-Row Anchor Ranges

> **Three columns × thirteen rows** of sales anchor ranges, aligned to
> [`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md). Ranges are locked as sales anchors.
> Point values resolve per engagement.
>
> **Internal-cost column is codex-private** per [rule 08](../_ssot-rules/08-pricing-principles.md) §Internal cost column
> is codex-private. Populated 2026-04-20 from the ~£34k/mo base burn in
> [`revenue-projection-2026-monthly.md`](revenue-projection-2026-monthly.md) §Monthly cost decomposition using the
> allocation methodology below. These cost-column entries never appear in any client-facing quote, demo, or website
> surface — they live only here and in the Stage 3C `cost()` derivation read path for callers with
> `pricing.read_internal` capability. The public-facing structure (Tier A / Tier B / modifier blocks) is locked.

**Rule source:** [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)

## Discipline reminders (rule 08)

Non-negotiable before any number commits to a quote:

- **Internal cost column stays codex-private.** Never in client-facing docs, quote lines, demo surfaces, or the website.
  Lives in this codex dir only. Rule 08 enforcement rule 1.
- **Twelve-month minimum commitment** on both Tier A and Tier B. Rule 08 enforcement rule 2.
- **Per-block tier mixability.** A client runs Tier B on some blocks and Tier A on others within the same contract. Rule
  08 enforcement rule 4.
- **Block 12 (exclusivity premium) and block 13 (custom solution premium) are Tier-B-only modifiers.** They never appear
  without a Tier B base. Rule 08 enforcement rule 3.
- **No raw data on any tier.** Raw-data-framed line items violate rules 07 and 08.
- **Numbers live in one place.** This doc (DART blocks) plus
  [`im-profit-share-structures.md`](im-profit-share-structures.md) (IM mechanics). No shadow pricing sheets. Rule 08
  enforcement rule 6.

## The pricing table

Three columns, thirteen rows. Internal column stays codex-private; Tier A is cost-plus (variable); Tier B is fixed
upfront + fixed monthly. Ranges mirror the signals-only anchor table in
[`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md).

**Internal-cost column populated 2026-04-20** from the base-burn line items in
[`revenue-projection-2026-monthly.md`](revenue-projection-2026-monthly.md) §Monthly cost decomposition (~£34k/mo base
burn across 2.5 FTE engineering + data + cloud + corporate overhead). Allocation methodology is documented under
[Internal-cost allocation methodology](#internal-cost-allocation-methodology) below. Numbers are anchors — per-deal
cost-plus quotes pull the specific venue/chain/data licence figures in play. These entries stay codex-private per rule
08 and never appear in client-facing quotes, demos, or the website.

| #   | Block                                | Internal monthly cost | Tier A (cost-plus, variable) | Tier B fixed monthly                                | Tier B upfront                                  |
| --- | ------------------------------------ | --------------------- | ---------------------------- | --------------------------------------------------- | ----------------------------------------------- |
| 1   | Reporting core                       | £1.8-2.5k             | cost-plus monthly            | £3-5k/mo                                            | £10-20k                                         |
| 2   | Regulatory umbrella reporting        | £4-6k                 | cost-plus monthly            | £8-15k/mo                                           | £20-40k                                         |
| 3   | IM allocator reporting               | £1.2-2k               | cost-plus monthly            | £3-6k/mo                                            | £10-20k                                         |
| 4   | Strategy-service entry               | £0.2-0.4k per slot    | cost-plus per-tenant-slot    | £0.4-0.8k per strategy/mo                           | £5-10k                                          |
| 5   | Instructions integration (see depth) | £1-10k (by depth)     | cost-plus per-depth          | £2-20k/mo (by depth)                                | £5-15k                                          |
| 6   | Research / promote pipeline          | £3-6k                 | not available on Tier A      | £5-15k/mo bundled credits                           | £15-30k                                         |
| 7   | Execution layer                      | £1.5-3k               | cost-plus usage-variable     | £3-6k/mo                                            | £10-20k                                         |
| 8   | Venue packs (per venue)              | £0.3-0.8k per venue   | cost-plus per venue          | £1-2k per primary / £0.5-1k per marginal            | £3-8k per venue                                 |
| 9   | Chain packs (per chain)              | £0.2-0.5k per chain   | cost-plus per chain          | £0.5-1.5k per chain/mo                              | £2-5k per chain                                 |
| 10  | Instrument-type packs (per type)     | £0.3-1k per type      | cost-plus per type           | £1-3k per type/mo                                   | £3-6k per type                                  |
| 11  | Analytics packs (per family)         | £0.2-1k per pack      | cost-plus per pack           | £0.5-3k per pack/mo                                 | £2-5k per pack                                  |
| 12  | Exclusivity / non-compete premium    | n/a (modifier)        | Not available on Tier A      | 20-200% uplift on Tier B monthly (by IP-power tier) | —                                               |
| 13  | Custom solution premium              | n/a (modifier)        | Not available on Tier A      | 10-25% of build fee annualised                      | engineering-hours × loaded cost × 1.5-2× margin |

### Internal-cost allocation methodology

Base burn of **~£34k/mo** (from [`revenue-projection-2026-monthly.md`](revenue-projection-2026-monthly.md)) breaks down
into three layers:

**Layer 1 — shared corporate overhead (~£6-7k/mo, not block-allocated):** FCA (£0.83), audit (£1.67), registrar (£0.33),
banking (£0.05), AML (£1.0), SaaS (£2.0), agentic AI (£2.0). Spread across all active client contracts. Not a per-block
line — shows up inside the Tier B "whole-contract" monthly.

**Layer 2 — data + licence costs (~£4.67k/mo, allocated to blocks 8/9/10/11):** Tardis (£0.67), DeFi data Graph+Alchemy
(£1.0), Sports data API-Football+weather (£1.0), TradFi data (£2.0). Allocated by domain — venue packs get roughly
one-third, chain packs one-fifth, instrument-type packs one-third, analytics packs the remainder.

**Layer 3 — engineering + cloud (~£21k/mo, allocated to blocks 1-7):** Engineering 2.5 FTE (£16.0) + GCP cloud (£5.0) =
£21k/mo. Weighted by implementation+maintenance load:

- Block 1 (reporting core): 10% → ~£2.1k
- Block 2 (reg umbrella): 20% (FCA + reg workflow is engineering-heavy) → ~£5k (incl. regulatory-eng uplift)
- Block 3 (IM reporting): 8% → ~£1.7k
- Block 4 (strategy slot): variable; ~£0.3k/slot at steady-state
- Block 5 (instructions integration): 10-50% depending on depth (minimal → rich)
- Block 6 (research/promote): 18% → ~£3.8k
- Block 7 (execution layer): 10% → ~£2.1k

Block 12 and 13 are modifiers with no direct internal cost — margin on engineering hours (block 13) and revenue-forgone
× margin (block 12) drive the external price.

**Review cadence**: finance revisits the allocation every quarter or on any ±15% change in base burn (e.g. an additional
FTE, new data vendor). Re-allocation commit message:
`chore(pricing): re-populate internal-cost column per finance YYYY-MM-DD`.

### Block 5 — internal cost by instruction-schema depth

Per rule 10 schema-depth pricing dimension:

| Block 5 depth | Internal | Tier A    | Tier B monthly | Tier B upfront                                            |
| ------------- | -------- | --------- | -------------- | --------------------------------------------------------- |
| Minimal       | £1-2k    | cost-plus | £2-4k/mo       | £5-10k                                                    |
| Standard      | £2-4k    | cost-plus | £4-8k/mo       | £8-15k                                                    |
| Rich          | £4-10k   | cost-plus | £8-20k/mo      | £10-15k (often with block 13 custom premium layered over) |

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

Block 5's depth-table is rendered inside the main pricing table above (see §Block 5 — internal cost by
instruction-schema depth). Per
[rule 10 §Schema depth as a pricing dimension](../_ssot-rules/10-strategy-instruction-schema-principles.md) and rule 05
block 5 description, instruction-schema depth (minimal / standard / rich) shapes the block 5 price.

### Block 12 — exclusivity uplift by IP-power tier

Scaled by strategy scarcity. See [`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md) §IP-power tier anchors
for full definitions and worked examples.

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

| Component                 | Tier B range                                                     |
| ------------------------- | ---------------------------------------------------------------- |
| Floor monthly licence     | £10-20k/mo per counterparty                                      |
| Per-signal uplift         | £25-100 per signal (high-freq) / £200-500 per signal (sparse)    |
| Optional P&L share upsell | 5% of counterparty's signal-attributable P&L (with audit rights) |

Alternative models — flat monthly licence, per-signal-only metering, pure rev-share — are documented in
[`signal-leasing.md`](signal-leasing.md) but the hybrid is recommended as the default commercial offering.

## Special-structure engagement notes

Some engagements do not compose cleanly from the 13-block Tier A/B grid. These deviations are documented below with
pointers to the canonical mechanic doc.

### IM engagement (Odum IM on own strategies) — NOT a block quote

IM is a `(Odum, *)` rule-04 cell; mechanics live in [`im-profit-share-structures.md`](im-profit-share-structures.md).

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
- Fallback if client rejects the 70/10 asymmetry in negotiation: flat 10%-pari-passu (Odum share drops 70→10%). Document
  in contracting notes.

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
required.

**Status (2026-04-20):** internal-cost column populated from the
[`revenue-projection-2026-monthly.md`](revenue-projection-2026-monthly.md) base-burn line items using the allocation
methodology in §The pricing table. Tier A/B external ranges remain at their anchored values from commercial strategy.

**Re-populate trigger:** finance re-runs the allocation whenever base burn moves ±15% or a new data vendor / engineering
hire lands. Re-allocation commit is tagged `chore(pricing): re-populate internal-cost column per finance YYYY-MM-DD` and
includes a line in the PR body pointing at the specific revenue-projection-2026-monthly.md revision.

**Stage 3C derivation read path:** the Stage 3C `cost(combo, tier)` formula reads this doc's internal-cost column when
the caller carries the `pricing.read_internal` capability claim; callers without the claim get an
`InternalCostLeakageError` + compliance event (rule 08 enforcement, wired in UAC
`internal/architecture_v2/derivation_cost.py`). See
[`../infra-spec/stage-3c-derivation-engine.md`](../../16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md)
and [`../infra-spec/stage-3e-g2-env-split.md`](../../16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md) §5.

No internal cost numbers leak to client-facing surfaces. The commercial-model docs are codex-private; demo, quote, and
website surfaces do not reference internal cost.

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
- [../infra-spec/stage-3c-derivation-engine.md](../../16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md) —
  Stage 3C reads this doc once numbers populate
