---
doc_type: codex-ssot
title: Strategy Origin × Stack Depth — The DART Commercial Matrix
summary:
  Implementation reference for rule 04's 2×3 matrix (strategy-origin Odum/client × stack-depth
  reporting-only/downstream/ full-pipeline) — per-cell commercial resolution, the five actual 2026 engagements (CME S&P,
  India Options, Elysium, Desmond, BTC FoF) mapped to cells, and each cell's default demo-restriction profile.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin, sales]
tags: [dart, strategy, sales, defi, tradfi, cost]
related:
  [
    ../_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/shared-core/dart-pricing-axes.md,
    /codex/14-customer-journeys/shared-core/instruction-schema-fit-and-package-boundaries.md,
    /codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md,
    ../commercial-model/dart-entry-points.md,
  ]
created: 2026-04-20
authoritative_for: [DART commercial-matrix cell worked examples + demo-restriction-profile mapping]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Origin × Stack Depth — The DART Commercial Matrix

> Implementation reference for [rule 04](../_ssot-rules/04-dart-commercial-axes.md). Worked examples, per-cell
> commercial mapping, and the demo-restriction profile each cell resolves to.

**Rule source:** [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)

## The two axes, restated

Every DART engagement resolves on two independent axes. Every commercial conversation must resolve both axes before
pricing is discussed.

**Axis 1 — Strategy origin.** Whose strategy is being run?

- **Odum strategy** — Odum-developed, Odum-run systematic strategy. Odum owns the IP.
- **Client strategy** — Client-developed strategy. Client retains IP. Strategy generation (regime classification, signal
  generation, allocation logic) happens outside Odum.

**Axis 2 — Stack depth.** How much of the Odum operating stack is the client buying?

- **Reporting-only visibility** — reporting surface only. Closer to IM or Reg Umbrella than true DART.
- **Client strategy + downstream integration** — client keeps strategy generation upstream; Odum runs execution, trading
  terminal, position monitoring, reconciliation, and scoped analytics.
- **Full DART pipeline** — the deeper stack including research, backtest, promote, execute, trade, observe.

## The 2 × 3 matrix

```
                        │  Reporting-only     │  Client strategy +         │  Full DART pipeline
                        │  visibility         │  downstream integration    │
────────────────────────┼─────────────────────┼────────────────────────────┼───────────────────────────
Odum strategy origin    │ [IM / Reg Umbrella] │ [Rare]                     │ [DART + Odum exposure]
                        │                     │                            │
Client strategy origin  │ [Rare]              │ [DART signals-only]        │ [Full DART build/run]
```

## Cell-by-cell resolution

| Cell                       | Practical path                          | Commercial home                                                                                      |
| -------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `(Odum, reporting-only)`   | Route to IM or Reg Umbrella             | [pb2a](../experience/im-decision-journey.md) / [pb2c](../experience/regulatory-umbrella-briefing.md) |
| `(Odum, downstream-only)`  | Rare; collapses to full-pipeline        | Escalate to leadership; default route `(Odum, full)`                                                 |
| `(Odum, full-pipeline)`    | DART client with Odum strategy exposure | Full DART pricing + Odum strategy premium                                                            |
| `(Client, reporting-only)` | Rare; routes to Reg Umbrella            | Route to Reg Umbrella                                                                                |
| `(Client, downstream)`     | Signals-only DART                       | [pb2b](../experience/dart-briefing.md) signals-only path; rule 10 fit-check                          |
| `(Client, full-pipeline)`  | Full DART build-and-run                 | [pb2b](../experience/dart-briefing.md) full path                                                     |

## Three practical paths that sell

Collapsing the matrix to the three cells that produce engagements:

1. **Reporting-only visibility** → IM or Reg Umbrella entry points. Not DART commercially.
2. **`(Client, downstream)` = signals-only DART** — client keeps the edge upstream; Odum runs the downstream stack. Rule
   10 fit-check runs before any demo. Block composition: reporting core + strategy-service entry + instructions
   integration + execution layer + venue/chain/instrument-type packs + scoped analytics. No research/promote pipeline
   (block 6 excluded).
3. **Full DART pipeline** — `(Client, full)` or `(Odum, full)`. The richer engagement. Adds block 6 (research/promote
   pipeline). Odum strategy exposure lives here when present, priced as a premium.

## Worked examples

### Example 1 — DeFi stat-arb fund

**Situation:** Fund has a working stat-arb strategy on their own infrastructure. Hits operational limits: venue
onboarding, cross-chain treasury rebalancing, regulatory cover, monitoring fragility.

**Axis resolution:** Strategy origin = client; stack depth = downstream integration.

**Cell:** `(Client, downstream)` → signals-only DART.

**Blocks:** reporting core + strategy-service entry + instructions integration + execution layer + venue packs (their 3
primary venues) + chain packs (their 2 primary chains) + instrument-type packs (perps + spot). Analytics pack optional.

**Pricing shape:** Tier B on sticky blocks (reporting, strategy-service, instructions); Tier A on marginal venue packs.

### Example 2 — Family office wanting Odum-run exposure

**Situation:** Allocator evaluating Odum as a manager. Wants to allocate capital; not operate infrastructure.

**Axis resolution:** Strategy origin = Odum; stack depth = reporting-only.

**Cell:** `(Odum, reporting-only)` → route to IM, not DART.

**Commercial home:** IM briefing (pb2a) + IM demo (pb3b). DART pricing and demo profile do not apply.

### Example 3 — Emerging manager launching under regulated cover

**Situation:** Manager wants regulatory cover, execution infrastructure, and reporting. Retains some strategy
discretion.

**Axis resolution:** Strategy origin = client; stack depth = downstream integration (hybrid with reg cover).

**Cell:** `(Client, downstream)` + Reg Umbrella composition. Two commercial engagements with shared infrastructure.

**Blocks:** regulatory umbrella reporting + reporting core + strategy-service entry + instructions integration +
execution layer + relevant venue/instrument-type packs.

### Example 4 — Prop firm buying Odum strategy IP + running it themselves

**Situation:** Firm wants to run Odum-developed strategies on their own capital with Odum's infrastructure.

**Axis resolution:** Strategy origin = Odum; stack depth = full-pipeline.

**Cell:** `(Odum, full)` → Full DART + Odum strategy premium. This is NOT a lighter package; it's full DART pricing with
the Odum-strategy exposure priced on top.

### Example 5 — DAO wanting systematic yield rotation

**Situation:** DAO wants yield rotation across DeFi protocols plus reporting for members.

**Axis resolution:** Strategy origin = Odum (DAO is buying exposure); stack depth = reporting-only.

**Cell:** `(Odum, reporting-only)` → Route to IM with DeFi flavour.

## Worked examples — 2026 concrete client mix

These are the five actual 2026 engagements the commercial stack is built around. Each example names the cell, commercial
home, and cross-references the pricing mechanic for that engagement.

### Example — CME S&P (Sept 2026, `(Odum, full-pipeline)`, IM co-invest)

**Situation:** Odum trades its own S&P ML directional strategy on CME dated futures. The client allocates
$500k and
ramps toward $5M over year-1. Odum commits $50k skin-in-the-game alongside the client's capital. Because Odum
brings the strategy IP on an asymmetric basis, the commercial split is **70% of profits / 10% of losses** to Odum.

**Axis resolution:** Strategy origin = Odum; stack depth = full-pipeline. IM engagement, NOT DART.

**Cell:** `(Odum, full-pipeline)` → IM co-invest (asymmetric).

**Commercial home:**
[`../commercial-model/im-profit-share-structures.md`](../commercial-model/im-profit-share-structures.md) §CME
co-investment structure (asymmetric). Skin scaling resolves per engagement: S1 flat / S2 pro-rata / S3 reduced,
confirmed at contracting.

### Example — India Options (Oct 2026, `(Odum, full-pipeline)`)

**Situation:** Odum trades NSE options for deltas (not vol) for convex payouts.
$100k upfront onboarding covers the
new-venue integration (NSE options adapter, clearing, margin). Ongoing is standard 30-35% performance-share +
platform-fee client-choice, same framework as BTC ML. Allocation $5-10M
expected year-1. **Gated** on the S&P ML signal shipping first — India engagement does not unlock without the preceding
signal proving out.

**Axis resolution:** Strategy origin = Odum; stack depth = full-pipeline. IM engagement, NOT DART.

**Cell:** `(Odum, full-pipeline)` → standard IM pricing + $100k onboarding.

**Commercial home:**
[`../commercial-model/im-profit-share-structures.md`](../commercial-model/im-profit-share-structures.md) §India Options.

### Example — Elysium Phase A (Jun 2026, `(Client, downstream)` signals-only DART)

**Situation:** Elysium runs a DeFi staked-basis yield strategy on their own
$500k allocation. They bring the signals;
Odum runs the downstream stack (execution, terminal, monitoring, reconciliation, scoped analytics). Phase A is paid as a
conservative fixed-total onboarding package of ~$125k
covering signals-only DART block composition.

**Axis resolution:** Strategy origin = client; stack depth = downstream integration.

**Cell:** `(Client, downstream)` → signals-only DART.

**Phase B upsell:** once their own $5-10M client allocation is wired in, ongoing scales to ~$90k/yr recurring on their
Tier B block usage.

**Commercial home:** [`../commercial-model/dart-entry-points.md`](../commercial-model/dart-entry-points.md) +
[`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md).

### Example — Desmond (May 2026 earliest, `(Client, downstream)` + Reg Umbrella hybrid)

**Situation:** Desmond runs a perp-funding-arb strategy with his own signals (commodity alpha, no exclusivity premium).
Combined engagement: Reg Umbrella cover for his regulated activity **AND** DART signals-only for execution,
reconciliation, and reporting on the same underlying Odum infrastructure. Two commercial shapes, shared blocks.
Commercials: **£25-50k upfront** (worst / best case) + **~£22k/mo** ongoing (Reg Umbrella ~£12k/mo + DART signals-only
~£10k/mo).

**Axis resolution:** Strategy origin = client; stack depth = downstream integration. Paired with Reg Umbrella cover.

**Cell:** `(Client, downstream)` + Reg Umbrella composition (two-engagement hybrid per the edge-case rule at the top of
this doc).

**Commercial home:** [`../commercial-model/dart-entry-points.md`](../commercial-model/dart-entry-points.md) +
[`../experience/regulatory-umbrella-briefing.md`](../experience/regulatory-umbrella-briefing.md).

### Example — BTC FoF (external wrapper, NOT in the catalogue)

**Situation:** Odum allocates a BTC client's 50 BTC mandate to an external fund-of-funds vehicle that Odum does not
operate. Odum acts as allocator, not strategy operator. Revenue: 20% × 5% annualised × 50 BTC = **0.5 BTC/yr ≈
£2.3k/mo**. No Odum-system compute is consumed; no strategy catalogue cell applies.

**Axis resolution:** Does NOT resolve against the 2 × 3 matrix above — external wrapper, not an Odum-run strategy.

**Cell:** None. Surfaced only in `client-reporting` for the specific wrapper mandate.

**Commercial home:**
[`../commercial-model/im-profit-share-structures.md`](../commercial-model/im-profit-share-structures.md) §BTC Fund of
Funds wrapper. Rule 07 data-licensing does **not** apply (no Odum strategy IP involved).

## Mapping to demo restriction profiles

Each cell resolves to a default restriction profile (see
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md)).

| Cell                              | Default restriction profile                                                                               |
| --------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `(Odum, reporting-only)`          | IM default profile (pb3b) — catalogue of IM-available slots + reporting; research/promote HIDDEN-ENTIRELY |
| `(Client, downstream)`            | signals-only DART — execution + strategy-service + reporting unlocked; research/promote LOCKED-VISIBLE    |
| `(Client, full)` / `(Odum, full)` | full DART — everything unlocked (catalogue + research + promote + execution + reporting)                  |

Demo mode (broader-platform / turbo / deep-dive — see
[`../demo-ops/dart-demo-modes.md`](../demo-ops/dart-demo-modes.md)) layers on top; cell resolves the restriction, mode
resolves the breadth of walk-through.

## Edge cases

- **Hybrid engagements.** A prospect spans two cells (Reg Umbrella + signals-only DART). Handle as two commercial
  engagements with shared infrastructure; do not try to collapse.
- **Build-for-client.** Odum builds a strategy to client spec and runs it on the client's capital. Strategy origin =
  Odum (Odum built it); stack depth = full-pipeline. Sits in `(Odum, full)` with a build-engagement upfront premium.
- **Strategic partnership.** Genuine co-development. Doesn't fit the matrix cleanly; bespoke, leadership signoff.
- **Non-compete / exclusivity.** A modifier on Tier B blocks, not a separate cell (see rule 05 block 12, rule 08
  exclusivity principles).

## Relationship to rule 10 (signals-only schema)

`(Client, downstream)` is the cell rule 10 guards. The instruction-schema fit-check determines whether the prospect's
upstream can produce the eight required fields. If yes, they fit signals-only; if no, they are either full-DART (Odum
runs the upstream too) or bespoke (custom premium block 13). Rule 10 is the fit-check layer; this doc is the commercial
matrix underneath.

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — the blocks each cell composes
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — tier assignment per block
- [rule 10 — strategy instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md) — fit-check for
  `(Client, downstream)`
- [instruction-schema-fit-and-package-boundaries.md](instruction-schema-fit-and-package-boundaries.md) — rule 10
  implementation
- [../experience/dart-briefing.md](../experience/dart-briefing.md) — pb2b briefing that walks this matrix
- [../experience/dart-demo.md](../experience/dart-demo.md) — pb3c demo scoped per resolved cell
- [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md) — commercial-facing expansion
- [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md) — profile per cell
