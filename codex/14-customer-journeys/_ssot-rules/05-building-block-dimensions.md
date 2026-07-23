---
doc_type: codex-ssot
title: Rule 05 — Building-block dimensions
summary:
  "The thirteen pricing/entitlement building blocks (11 standalone: reporting core, reg + IM reporting, strategy-service
  entry, instructions integration, research/promote, execution, venue/chain/instrument-type/ analytics packs + 2 Tier-B
  premium modifiers) — the atomic unit all pricing, demos, and entitlements compose from."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin, sales]
tags: [customer-journey, sales, cost, dart, registry]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
  ]
created: 2026-04-20
authoritative_for: [thirteen commercial building-block dimensions]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 05 — Building-block dimensions

> Thirteen building blocks. Every commercial engagement, demo restriction profile, and production entitlement composes
> from these blocks. Adding a block is a deliberate act; blocks do not multiply.

## Block legend (at a glance)

| #   | Block                                               | Pricing detail SSOT                                                                                                        |
| --- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1   | Reporting core                                      | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 1                   |
| 2   | Regulatory umbrella reporting                       | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 2                   |
| 3   | IM allocator reporting                              | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 3                   |
| 4   | Strategy-service entry                              | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 4                   |
| 5   | Instructions integration                            | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 5 (depth sub-table) |
| 6   | Research / promote pipeline                         | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 6                   |
| 7   | Execution layer                                     | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 7                   |
| 8   | Venue packs                                         | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 8                   |
| 9   | Chain packs                                         | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 9                   |
| 10  | Instrument-type packs                               | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 10                  |
| 11  | Analytics packs                                     | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 11                  |
| 12  | Exclusivity / non-compete premium (Tier-B modifier) | [`../commercial-model/exclusivity-and-noncompete.md`](../commercial-model/exclusivity-and-noncompete.md)                   |
| 13  | Custom solution premium (Tier-B modifier)           | [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) row 13                  |

Rule 05 defines the blocks. Pricing numbers live in the cited files only. No block lives elsewhere.

## The thirteen blocks

Eleven standalone blocks (1–11) and two premium modifiers (12–13).

### Standalone blocks

1. **Reporting core** — the shared client-reporting surface. One surface serves IM allocators, Reg Umbrella firms, and
   DART clients. Includes positions, P&L, exposures, reconciliation, audit. Reuses the same component tree Odum uses
   internally (rule 03).
2. **Regulatory umbrella reporting** — regulatory-filing-grade reporting under Odum's FCA permissions. Transaction
   reporting, best-execution evidence, MIFID surfaces, supervisory artifacts. Gated to Reg Umbrella clients.
3. **IM allocator reporting** — allocator-side reporting for IM clients: capital allocations, share-class NAV, fees,
   investor-statement generation. Distinct from reporting core by audience; shares the underlying component tree.
4. **Strategy-service entry** — per-client access to the strategy-service runtime for running strategies on Odum
   infrastructure. Includes risk bindings, allocation wiring, event plumbing.
5. **Instructions integration** — the signals-in / instructions-in API surface. Used by `(Client, downstream)` DART
   clients (see rule 04). Depth of schema support is a pricing dimension — see rule 10.
6. **Research / promote pipeline** — the deeper research, backtest, paper-trade, promote-to-live stack. Gated to full
   DART clients (rule 04). Signals-only clients do not receive this block.
7. **Execution layer** — the execution-service runtime, matching engine for historical backtests, algo library, TCA,
   smart routing. Scoped per venue/chain/instrument-type.
8. **Venue packs** — per-venue or per-venue-group capability. Each venue pack includes connectivity, credentials
   handling, reference-data coverage, execution integration, reconciliation adapters.
9. **Chain packs** — per-chain DeFi capability. RPC connectivity, wallet custody patterns, chain-specific instrument
   metadata, gas management. Per chain, priced independently.
10. **Instrument-type packs** — per-instrument-type capability: options, perps, dated futures, spot, lending, staking,
    yield, prediction markets, sports fixtures. Each pack carries the capability to handle that instrument type across
    research, promote, execution, reporting.
11. **Analytics packs** — analytics capability that slots onto reporting core: execution quality analytics, exposure
    analytics, factor attribution, regime classification, liquidity analytics. Each pack is a distinct scope.

### Premium modifiers (Tier B only per rule 08)

12. **Exclusivity / non-compete premium** — client pays Odum not to offer the same capability (venue pack + strategy
    family + instrument type combo) to direct competitors for a bounded scope and term. Expressed as a percentage uplift
    on Tier B monthly.
13. **Custom solution premium** — bespoke feature development or non-standard integrations specific to one client.
    Upfront plus monthly uplift. Tier B only.

## What each block delivers

| #   | Block                         | What a client on this block gets                                         | Who needs it                |
| --- | ----------------------------- | ------------------------------------------------------------------------ | --------------------------- |
| 1   | Reporting core                | P&L + positions + reconciliation + audit on the shared reporting surface | Every paying client         |
| 2   | Regulatory umbrella reporting | MIFID / FCA filing surfaces, best-ex evidence, transaction reporting     | Reg Umbrella clients        |
| 3   | IM allocator reporting        | Allocator-side NAV, fees, investor statements                            | IM clients                  |
| 4   | Strategy-service entry        | Per-client strategy runtime, risk + allocation wiring                    | DART clients (both paths)   |
| 5   | Instructions integration      | Signals-in API depth (see rule 10)                                       | `(Client, downstream)` DART |
| 6   | Research / promote pipeline   | Backtest + paper + promote + capital-alloc flow                          | Full-DART clients only      |
| 7   | Execution layer               | Execution-service + algos + TCA for the client's scope                   | Any client that trades      |
| 8   | Venue packs                   | Connectivity + reference data + recon per venue                          | Per-venue, scoped           |
| 9   | Chain packs                   | DeFi chain connectivity + custody + gas                                  | DeFi clients, per chain     |
| 10  | Instrument-type packs         | Handling depth for options / perps / futures / spot / etc.               | Per instrument type         |
| 11  | Analytics packs               | Analytics overlays on reporting core                                     | Optional per-client         |
| 12  | Exclusivity premium           | Restriction on Odum offering matched scope elsewhere                     | Tier B optional modifier    |
| 13  | Custom solution premium       | Bespoke build / integration                                              | Tier B optional modifier    |

## Composition rules

### A commercial path composes from blocks

From rule 04 axis resolution, each commercial path selects a subset of blocks:

- **`(Odum, reporting-only)` → IM.** Default blocks: 1 (reporting core) + 3 (IM allocator reporting); optional 11
  (analytics packs).
- **`(Client, downstream)` → signals-only DART.** Default blocks: 1 (reporting core) + 4 (strategy-service entry) + 5
  (instructions integration) + 7 (execution layer) + 8 (venue packs) + 9 (chain packs, where applicable) + 10
  (instrument-type packs). Block 6 (research / promote pipeline) is excluded.
- **`(Client, full-pipeline)` → full DART.** The signals-only set plus block 6; block 11 optional.
- **Reg Umbrella engagement.** Default blocks: 1 (reporting core) + 2 (regulatory umbrella reporting) + 7 (execution
  layer) + 8 (venue packs) + 10 (instrument-type packs).

### Blocks are atomic to pricing

Each block has three numbers (internal cost / Tier A price / Tier B upfront+monthly — see rule 08). Clients can mix
tiers per block. A client buying reporting core on Tier B and a marginal venue pack on Tier A is a normal engagement
shape.

### Blocks are atomic to visibility

The demo restriction profiles (Stage 2 `demo-ops/`) compose from the same block identifiers. Locking "research/promote
pipeline" in a signals-only demo is one profile toggle, not twenty individual screen toggles.

### Production entitlements compose from the same blocks

The entitlement registry in Stage 3B
([Stage 3 infra spec](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md)) uses the same thirteen
identifiers. One list of blocks, four derivations (pricing / demo / prod / codex).

## Adding or removing a block

Adding a fourteenth block is a deliberate act requiring:

1. A case for why no existing block subsumes the new capability.
2. Pricing numbers (internal cost / Tier A / Tier B) populated in Stage 2 `commercial-model/pricing-building-blocks.md`.
3. Demo-profile treatment defined in Stage 2 `demo-ops/demo-restriction-profiles.md`.
4. Entitlement-registry update in Stage 3B.
5. One-place update of rule 05 (this file), propagated automatically to rule 08 and downstream.

Removing a block is similarly deliberate — retire across pricing, demo profiles, entitlements, and this rule in one
pass.

## Sub-scoping within a block

Some blocks have inherent sub-scoping:

- **Venue packs** scope per venue or venue group. A Binance-spot pack is one item; a "tier-2 DEX pack" bundling five
  small-cap DEXs is one item. Sub-scope is recorded in the registry alongside the block identifier.
- **Chain packs** scope per chain. Ethereum L1 is one pack; Arbitrum is another.
- **Instrument-type packs** scope per type. Options is one pack; perps another. A client trading options + perps buys
  two packs.
- **Analytics packs** scope per analytic family. Exposure analytics is one pack; factor-attribution is another.

Sub-scope does not mean sub-block — these are still single blocks in rule 05 terms; they carry a scope tag in pricing
and entitlement storage.

## Enforcement rules

1. **Blocks are the atomic pricing unit.** Don't quote a client a price that doesn't map to one or more blocks. If it
   doesn't map, either a block is missing (add it via the process above) or the quote is non-standard (bespoke,
   leadership signoff).
2. **Demo restrictions compose from blocks.** Don't build ad-hoc demo restriction toggles; lock blocks.
3. **Production entitlements compose from blocks.** No custom-per-client entitlement flags that don't map to a block.
4. **Premium modifiers never appear without a Tier B base.** Exclusivity and custom premiums ride on Tier B blocks.
5. **No silent block splits.** If a block's scope changes (e.g. venue pack splits into "connectivity" and
   "reconciliation"), update rule 05 and propagate.

## Stage 2 implications

Stage 2 builds `commercial-model/pricing-building-blocks.md` with the thirteen rows + three columns (internal / Tier A /
Tier B) + TBD stubs for numbers. Finance populates post-merge. Stage 2 also builds
`demo-ops/demo-restriction-profiles.md` using the same thirteen identifiers and
`implementation-mapping/entitlement-registry.md` as the production link.

## Stage 3 implications

Stage 3B's UAC combo registry declares the thirteen blocks as the entitlement dimension. Stage 3C's derivation engine
resolves `(path, blocks, tier)` into `demo_universe`, `prod_restrictions`, `pricing_quote`, and `codex_scope` from a
single registry read — the "one registry, four derivations" pattern.

## Cross-references

- [`04-dart-commercial-axes.md`](04-dart-commercial-axes.md) — axis resolution selects which blocks are in scope per
  cell
- [`08-pricing-principles.md`](08-pricing-principles.md) — per-block tier structure applied to these thirteen
- [`10-strategy-instruction-schema-principles.md`](10-strategy-instruction-schema-principles.md) — block 5 (instructions
  integration) depth dimension
- [`../commercial-model/pricing-building-blocks.md`](../commercial-model/pricing-building-blocks.md) — anchor ranges per
  block
- Stage 3B UAC combo registry declares these thirteen as the entitlement dimension
