---
doc_type: codex-ssot
title: DART Pricing Axes — Signals-Only vs Full DART
summary:
  Pricing dimensional model splitting signals-only DART (scope-fixed Tier-B block pricing) from full DART (adds
  usage-metered research consumption + IP-power exclusivity uplift tiers + venue/server cost pass-through), with worked
  examples per commercial cell.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin, sales]
tags: [cost, dart, defi, strategy, sales, features]
related:
  [
    ../_ssot-rules/04-dart-commercial-axes.md,
    ../_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/shared-core/strategy-origin-vs-stack-depth.md,
    /codex/14-customer-journeys/shared-core/instruction-schema-fit-and-package-boundaries.md,
    ../commercial-model/pricing-building-blocks.md,
  ]
created: 2026-04-20
authoritative_for: [DART pricing dimensional model (signals-only vs full-DART metering axes)]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/shared-core/instruction-schema-fit-and-package-boundaries.md,
    /codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md,
    /codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md,
    /codex/14-customer-journeys/shared-core/strategy-origin-vs-stack-depth.md,
  ]
owner:
last_reviewed:
code_refs:
---

# DART Pricing Axes — Signals-Only vs Full DART

> Implementation map for the pricing dimensional model that distinguishes signals-only DART from full-pipeline DART.
> Signals-only is fixed-scope block pricing. Full DART adds per-backtest metering + IP-power exclusivity tiers +
> venue/server cost pass-through.

**Rule sources:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md) (commercial axes),
[rule 05](../_ssot-rules/05-building-block-dimensions.md) (13 blocks),
[rule 08](../_ssot-rules/08-pricing-principles.md) (tier structure),
[rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md) (signals-only fit-check).

## Why this doc exists

Earlier Stage 2 passes treated signals-only and full DART with a common block framework but didn't properly
differentiate the metering axes. In practice, signals-only engagements are scope-bounded (client's venue + instrument

- strategy list is known at contracting) while full DART engagements have variable research consumption that can't be
  priced flat. This doc captures the dimensional split.

## Three pricing dimensions

### Dimension 1 — Fixed-access layer

Block 1 (reporting core), 4 (strategy-service entry), 7 (execution layer), 8/9/10 (venue / chain / instrument-type
packs). Always Tier A/B fixed-monthly. Applies to BOTH signals-only and full DART.

### Dimension 2 — Usage-metered research consumption

**Unique to full DART** (Block 6 research / promote pipeline):

- Backtest runtime compute (BQ queries + feature-service CPU + simulated fill runtime in strategy-service matching
  engine).
- Shadow-evaluation + paper runtime per-strategy-month.
- Promote-pipeline evaluation + capital-allocation governance.
- Feature-compute for custom feature sets.

### Dimension 3 — IP-power modifiers

**Unique to full DART + optionally signals-only with specific strategies**:

- Exclusivity (block 12) scaled by strategy IP power / scarcity.
- Custom solution premium (block 13) for bespoke feature builds.

## Signals-only DART pricing model

Client keeps strategy IP upstream. Sends instructions in (rule 10 schema). Pricing is **scope-fixed, Tier B default**:

| Block                      | Tier               | £/month pricing shape                     | Upfront £      |
| -------------------------- | ------------------ | ----------------------------------------- | -------------- |
| 1 Reporting core           | B fixed            | 3-5k                                      | 10-20k         |
| 4 Strategy-service entry   | B per-tenant-slot  | 0.4-0.8k per strategy                     | 5-10k          |
| 5 Instructions integration | B per-schema-depth | minimal 2-4k / standard 4-8k / rich 8-20k | 5-15k          |
| 7 Execution layer          | B fixed            | 3-6k                                      | 10-20k         |
| 8 Venue packs              | B fixed per venue  | 1-2k per primary; 0.5-1k per marginal     | 3-8k per venue |
| 9 Chain packs              | B fixed per chain  | 0.5-1.5k per                              | 2-5k per chain |
| 10 Instrument-type packs   | B fixed per type   | 1-3k per type                             | 3-6k per type  |
| 11 Analytics packs         | A or B             | 0.5-3k per pack                           | 2-5k per pack  |

**Does NOT include** block 6 (research / promote). Rule 04 boundary.

**Worked example — Elysium Phase A (DeFi staked-basis, 4 chains scope):**

Block composition: 1 + 4 × 1 strategy + 5 (std depth) + 7 + 8 × 0 (DEX-only) + 9 × 4 (Eth / Arb / Base / Solana) + 10 ×
2 (spot + perp) + 11 × 1 (execution quality analytics).

Conservative Tier B: £4k + £0.6k + £5k + £4k + £5k (4 chains × £1.25k) + £4k (2 types × £2k) + £1.5k = **~£24k/mo**.

Actual Elysium engagement: profit-share model (30% of their fees/returns) replaces the block pricing for the post-
go-live phase. Onboarding was $125k total fixed. See
[`../commercial-model/im-profit-share-structures.md`](../commercial-model/im-profit-share-structures.md) for the
profit-share structure applied to DART clients that prefer upside-aligned terms over Tier B fixed.

## Full-DART pricing model

Client uses Odum's research + promote + execute + report. Fixed-access layer + metered research consumption + IP-power
modifiers.

### Fixed-access layer (same as signals-only)

Blocks 1, 4, 7, 8, 9, 10 at Tier B fixed. Same shape as signals-only above.

### Metered research consumption layer (new)

| Research driver             | Metering unit                                                       | Tier B pricing                                 |
| --------------------------- | ------------------------------------------------------------------- | ---------------------------------------------- |
| Baseline backtest           | Per run: 1 archetype × 1 instrument × 1 year history                | £50-£200 per run                               |
| Complex backtest            | Per run: multi-instrument portfolio × 5-yr history × regime slicing | £500-£2,000 per run                            |
| Full-matrix sweep           | One-time full-combinatoric proof run                                | £10k-£30k (rare; most clients don't need this) |
| Shadow-evaluation runtime   | Per strategy × month in shadow phase                                | £300-£1,000 per strategy-month                 |
| Paper-trading runtime       | Per strategy × month in paper phase                                 | £300-£1,000 per strategy-month                 |
| Promote pipeline evaluation | Per promoted strategy (one-time)                                    | £500-£2,000 per promotion                      |
| Custom feature compute      | Per feature-job compute hour                                        | £20-£50/hr metered                             |

**Commercial packaging options:**

- **Pay-as-you-go**: pure metering against actual usage.
- **Bundled credits**: e.g. "100 baseline backtests + 10 complex + 5 paper-months for £5k flat, overage metered".
- **Hybrid**: Tier B floor + usage overage.

Bundled credits is the most common for clients who want budget certainty.

### IP-power exclusivity tiers (block 12)

Rule 08 specifies exclusivity is Tier-B-only. Scaled by strategy scarcity:

| IP-power category                          | Example                                                     | Uplift on Tier B monthly |
| ------------------------------------------ | ----------------------------------------------------------- | ------------------------ |
| Commodity archetype                        | ML directional on liquid CeFi perps; perp-funding arb       | 20-30%                   |
| Specialised venue + archetype combo        | Hyperliquid market-making; drift carry-basis                | 50-80%                   |
| Scarce venue access (hard-to-integrate)    | Indian options NSE delta trading; Kalshi prediction markets | 80-120%                  |
| Uniquely differentiated multi-leg strategy | Custom DeFi stat-arb; novel event-driven multi-leg          | 120-200%                 |

Pricing logic: Odum's estimated revenue forgone from NOT selling the same scope to a direct competitor, over the
exclusivity term, times a margin multiplier. Document the specific forgone-revenue estimate in each quote's exclusivity
line.

### Custom solution premium (block 13)

Tier B only. Covers bespoke feature development or non-standard integrations. Priced as:

- **Build fee**: estimate engineering hours × loaded cost × margin (usually 1.5-2×). Paid upfront before work starts.
- **Monthly uplift**: ongoing maintenance of the custom capability. Typically 10-25% of the build fee annualised.

## Venue + server cost pass-through (Tier A)

For full-DART clients running heavy custom workloads, offer a Tier A cost-plus line on compute + venue data:

- GCP usage attributable to their workspace (tagged resources or isolated project): actual cost + 25% margin.
- Venue / chain / sport data licensing share (Tardis, Graph, Alchemy, API-Football): pro-rata by the client's venue /
  chain / sport scope, baked into the venue-pack pricing already but surfaced as a line item if the client asks.
- RPC provider calls for DeFi clients: metered pass-through + margin.

This keeps cost-sensitive clients on rule-08 Tier A alignment instead of forcing flat Tier B on high-variance workloads.

## Full-DART worked example

Hypothetical DART client wanting full pipeline on crypto perps across 3 venues + 2 chains, running 5 strategies, wanting
exclusivity on one specialised multi-leg archetype (say, a custom DeFi stat-arb), Tier B throughout:

| Component                                                                                       | Monthly £              | Upfront £         |
| ----------------------------------------------------------------------------------------------- | ---------------------- | ----------------- |
| Block 1 reporting core                                                                          | 4                      | 15                |
| Block 4 strategy-svc × 5 tenants                                                                | 5 × 0.6 = 3            | 10                |
| Block 6 research bundle (100 baseline backtests + 10 paper-months)                              | 5                      | 15                |
| Block 6 overage metered                                                                         | 0-3                    | —                 |
| Block 7 execution layer                                                                         | 4                      | 15                |
| Block 8 venue packs × 3 primary CeFi                                                            | 4.5                    | 15                |
| Block 9 chain packs × 2 DeFi                                                                    | 2                      | 6                 |
| Block 10 instrument-type packs (perp + spot)                                                    | 3                      | 6                 |
| Block 11 analytics × 2 (exec quality + exposure)                                                | 2                      | 5                 |
| Block 12 exclusivity — uniquely differentiated multi-leg (120% uplift on sticky £10k of Tier B) | 12                     | —                 |
| **Full-DART total**                                                                             | **~£40k/mo + metered** | **~£87k upfront** |

That's an ~£500k/yr Tier B engagement. At ~£3-5k/month Odum incremental cost to serve (multi-tenant sharing), ~85% gross
margin.

## Commercial-path resolution → pricing model selection

Per rule 04 matrix:

| Cell                                | Pricing model                                                                                              |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `(Odum, reporting-only)`            | IM engagement — perf-share + platform-fee choice. See `../commercial-model/im-profit-share-structures.md`. |
| `(Client, downstream)` signals-only | Signals-only pricing above.                                                                                |
| `(Client, full-pipeline)` full DART | Full-DART pricing above.                                                                                   |
| `(Odum, full-pipeline)`             | Full DART + Odum strategy premium. Often negotiated as profit-share rather than Tier B fixed.              |

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)
- [rule 10 — strategy instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md)
- [strategy-origin-vs-stack-depth.md](strategy-origin-vs-stack-depth.md) — axis resolution
- [instruction-schema-fit-and-package-boundaries.md](instruction-schema-fit-and-package-boundaries.md) — rule 10
- [../commercial-model/pricing-building-blocks.md](../commercial-model/pricing-building-blocks.md) — full 13-row pricing
  SSOT
- [../commercial-model/im-profit-share-structures.md](../commercial-model/im-profit-share-structures.md) — IM mechanics
- [../commercial-model/exclusivity-and-noncompete.md](../commercial-model/exclusivity-and-noncompete.md) — block 12
- [../experience/dart-briefing.md](../experience/dart-briefing.md) — pb2b uses this pricing model
- [../experience/dart-demo.md](../experience/dart-demo.md) — pb3c demo scoping
