---
scope: [sales, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# `commercial-model/` — Blocks-to-packages-to-tiers

How the thirteen rule-05 building blocks compose into commercial packages, how rule-08 tiers apply, and where
exclusivity and custom premiums attach. Stage 2 ships the structure; pricing numbers are populated by Odum finance as a
separate commit after Stage 2 merges (see [`pricing-building-blocks.md`](pricing-building-blocks.md)'s TBD stubs).

## Three-step commercial resolution

Every commercial conversation runs three steps:

1. **Resolve the commercial path.** Strategy-origin × stack-depth per
   [rule 04](../_ssot-rules/04-dart-commercial-axes.md). Routes to IM, Reg Umbrella, signals-only DART, or full DART.
   See [`dart-entry-points.md`](dart-entry-points.md) +
   [`../shared-core/strategy-origin-vs-stack-depth.md`](../shared-core/strategy-origin-vs-stack-depth.md).
2. **Compose the block set.** Which of the thirteen rule-05 blocks apply, with sub-scoping (venue / chain /
   instrument-type). See [`building-block-packaging.md`](building-block-packaging.md).
3. **Assign the tier per block.** Tier A (cost-plus variable) or Tier B (fixed upfront + monthly). Per-block mixable.
   See [`fixed-vs-variable-commercials.md`](fixed-vs-variable-commercials.md) and
   [`pricing-building-blocks.md`](pricing-building-blocks.md).

Exclusivity (block 12) and custom-solution premium (block 13) attach only to Tier B blocks — see
[`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md).

## Contents

| File                                                                 | Purpose                                                                |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [dart-entry-points.md](dart-entry-points.md)                         | Three practical DART commercial paths + who buys what                  |
| [im-vs-reg-reporting-logic.md](im-vs-reg-reporting-logic.md)         | Same UI, two commercial framings (IM vs Reg Umbrella)                  |
| [building-block-packaging.md](building-block-packaging.md)           | 13 blocks × 6 package matrix                                           |
| [pricing-building-blocks.md](pricing-building-blocks.md)             | 3 cols × 13 rows pricing structure (TBD stubs; Odum finance populates) |
| [fixed-vs-variable-commercials.md](fixed-vs-variable-commercials.md) | Tier A vs Tier B decision tree                                         |
| [exclusivity-and-noncompete.md](exclusivity-and-noncompete.md)       | What exclusivity means, who gets it, legal framing                     |

## Stage 3 relationship

Stage 3B's UAC combo registry declares the thirteen blocks as the entitlement dimension. Stage 3C's derivation engine
resolves `(path, blocks, tier)` into `demo_universe`, `prod_restrictions`, `pricing_quote`, and `codex_scope`. Pricing
numbers in [`pricing-building-blocks.md`](pricing-building-blocks.md) feed Stage 3C's `cost(combo, tier)` formula once
populated.

## Cross-references

- [`../_ssot-rules/`](../_ssot-rules/) — rules 04, 05, 07, 08, 10
- [`../shared-core/`](../shared-core/) — shared concepts
- [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) — profiles per path
- [`../infra-spec/`](../infra-spec/) — Stage 3 registry and derivation
