---
doc_type: codex-ssot
title: Building-Block Packaging — Which Blocks Cluster into Which Packages
summary:
  Block × package matrix — how the thirteen rule-05 building blocks compose into six standard commercial packages (IM
  reporting-only, Reg Umbrella starter, Signals-only DART, Full DART, Full+Odum strategy, Combined), with sub-scoping
  (venue/chain/instrument/analytics packs) priced per unit.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, admin]
tags: [commercial-model, pricing, dart, building-blocks, packaging, im, reg-umbrella]
related:
  [
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
  ]
created: 2026-04-20
authoritative_for: [building-block to commercial-package composition matrix]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Building-Block Packaging — Which Blocks Cluster into Which Packages

> The thirteen rule-05 blocks compose into standard commercial packages. Not every engagement builds a custom block set
> from scratch; packages are the starting points. This doc tabulates the block × package matrix.

**Rule sources:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md),
[rule 05](../_ssot-rules/05-building-block-dimensions.md)

## Standard packages

Six named packages. Each has a typical block composition; real engagements deviate per negotiation but usually start
from one of these shapes.

| Package                                  | Composition summary                                                         | Typical buyer                                         |
| ---------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------- |
| **IM reporting-only**                    | Blocks 1 + 3 + optional 11                                                  | Family office, institutional allocator                |
| **Reg Umbrella starter**                 | Blocks 1 + 2 + 7 + 8 + 10 + optional 11                                     | Emerging manager, firm spinning up regulated activity |
| **Signals-only DART**                    | Blocks 1 + 4 + 5 + 7 + 8 + 9 + 10 + optional 11                             | DeFi-native fund, prop firm wanting downstream stack  |
| **Full DART**                            | Blocks 1 + 4 + 6 + 7 + 8 + 9 + 10 + 11                                      | Fund building on Odum top-to-bottom                   |
| **Full DART + Odum strategy**            | Blocks 1 + 4 + 6 + 7 + 8 + 9 + 10 + 11 + Odum-strategy premium              | Prop firm licensing Odum IP                           |
| **Combined Reg Umbrella + signals-only** | Union of Reg Umbrella starter + Signals-only DART with block 1 counted once | Emerging manager with own strategy + reg cover        |

## Block × package matrix

`✓` = standard inclusion. `○` = optional, per negotiation. `—` = not applicable.

| Block                                  | IM reporting-only | Reg Umbrella starter | Signals-only DART | Full DART | Full + Odum strategy | Reg + signals-only |
| -------------------------------------- | ----------------- | -------------------- | ----------------- | --------- | -------------------- | ------------------ |
| 1 — Reporting core                     | ✓                 | ✓                    | ✓                 | ✓         | ✓                    | ✓                  |
| 2 — Regulatory umbrella reporting      | —                 | ✓                    | —                 | —         | —                    | ✓                  |
| 3 — IM allocator reporting             | ✓                 | —                    | —                 | —         | —                    | —                  |
| 4 — Strategy-service entry             | —                 | ○                    | ✓                 | ✓         | ✓                    | ✓                  |
| 5 — Instructions integration           | —                 | ○                    | ✓                 | ○         | ○                    | ✓                  |
| 6 — Research / promote pipeline        | —                 | —                    | —                 | ✓         | ✓                    | —                  |
| 7 — Execution layer                    | —                 | ✓                    | ✓                 | ✓         | ✓                    | ✓                  |
| 8 — Venue packs                        | —                 | ✓                    | ✓                 | ✓         | ✓                    | ✓                  |
| 9 — Chain packs                        | —                 | ○                    | ✓ (DeFi scope)    | ○         | ○                    | ○                  |
| 10 — Instrument-type packs             | —                 | ✓                    | ✓                 | ✓         | ✓                    | ✓                  |
| 11 — Analytics packs                   | ○                 | ○                    | ○                 | ✓         | ✓                    | ○                  |
| 12 — Exclusivity / non-compete premium | ○                 | ○                    | ○                 | ○         | ✓                    | ○                  |
| 13 — Custom solution premium           | ○                 | ○                    | ○                 | ○         | ○                    | ○                  |

Notes on the matrix:

- **Block 1 is universal.** Every paying engagement includes reporting core. It is the shared component tree that
  enables rule 03's same-system claim.
- **Block 6 exclusion is load-bearing.** Signals-only engagements do NOT include research / promote pipeline. Clients
  wanting that upgrade to Full DART, not bolt research onto signals-only (rule 04 + rule 10 enforcement).
- **Block 2 and block 3 are mutually exclusive** per engagement (a single engagement is either Reg Umbrella or IM;
  combined is two engagements with one shared-infrastructure envelope).
- **Blocks 12 and 13 are Tier-B-only modifiers.** They do not appear without a Tier B base. See
  [`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md).

## Sub-scoping within a block

Some blocks have inherent sub-scoping (rule 05 sub-scoping rules). For pricing, each sub-scope is a separate unit.

- **Block 8 (venue packs).** One unit per venue or venue group. Binance-spot is one unit; a bundled "tier-2 DEX pack" is
  one unit. See [`../shared-core/venue-chain-instrument-scope.md`](../shared-core/venue-chain-instrument-scope.md).
- **Block 9 (chain packs).** One unit per chain. Ethereum L1 is one pack; Arbitrum is another; Base another.
- **Block 10 (instrument-type packs).** One unit per type. Options is one pack; perps another; spot another; prediction
  markets another; sports fixtures another.
- **Block 11 (analytics packs).** One unit per analytic family. Exposure analytics is one pack; factor-attribution
  another; regime classification another; liquidity analytics another.

A Signals-only DART engagement trading perps + spot on 2 CeFi venues + 1 DeFi chain buys: block 8 × 2, block 9 × 1,
block 10 × 2 — four sub-scope units inside three block identifiers. Pricing is per unit.

## Standard-package-to-commercial-path mapping

The packages map to the rule-04 commercial cells:

| Cell                       | Default package              |
| -------------------------- | ---------------------------- |
| `(Odum, reporting-only)`   | IM reporting-only            |
| `(Client, reporting-only)` | Reg Umbrella starter (often) |
| `(Client, downstream)`     | Signals-only DART            |
| `(Client, full-pipeline)`  | Full DART                    |
| `(Odum, full-pipeline)`    | Full DART + Odum strategy    |
| Hybrid (two cells)         | Combined package (union)     |

Rule 04 enforcement: `(Odum, downstream-only)` does not have a standard package because it usually collapses to
full-pipeline. If a prospect asks for Odum strategy exposure without the research surface, escalate rather than price.

## Adding a new package

Adding a fourteenth package requires the same deliberate process as adding a fourteenth block (rule 05 §Adding or
removing a block):

1. A case for why no existing package composes the needed block set.
2. Stage-3B registry update naming the new package identifier.
3. Pricing structure (TBD numbers per block) aligned in `pricing-building-blocks.md`.
4. Demo-restriction profile defined in `../demo-ops/demo-restriction-profiles.md`.
5. One-place update here (this doc), propagated to consumers.

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — per-block tier assignment
- [dart-entry-points.md](dart-entry-points.md) — the three commercial paths
- [pricing-building-blocks.md](pricing-building-blocks.md) — pricing numbers (TBD)
- [fixed-vs-variable-commercials.md](fixed-vs-variable-commercials.md) — Tier A vs Tier B
- [exclusivity-and-noncompete.md](exclusivity-and-noncompete.md) — Tier B modifiers
- [../shared-core/venue-chain-instrument-scope.md](../shared-core/venue-chain-instrument-scope.md) — sub-scoping
- [im-vs-reg-reporting-logic.md](im-vs-reg-reporting-logic.md) — IM vs Reg Umbrella commercial framings
