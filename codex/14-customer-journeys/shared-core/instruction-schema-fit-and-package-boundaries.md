---
doc_type: codex-ssot
title: Instruction Schema Fit + Package Boundaries
summary:
  Rule-10 implementation map — the eight required signals-only instruction fields, three schema depths
  (minimal/standard/ rich as block-5 pricing axis), venue×instrument×mode compatibility matrix, lifecycle semantics, and
  the load-bearing package boundary — what signals-only enables downstream vs what requires upgrading to full DART
  (block 6).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service]
scope: [engineer, admin, sales]
tags: [dart, execution, instruments, strategy, cost, sales]
related:
  [
    ../_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/shared-core/strategy-origin-vs-stack-depth.md,
    /codex/14-customer-journeys/shared-core/dart-pricing-axes.md,
    ../../16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
  ]
created: 2026-04-20
authoritative_for: [signals-only 8-field instruction-schema fit + package boundary/upgrade path]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/shared-core/README.md,
    /codex/14-customer-journeys/shared-core/dart-pricing-axes.md,
    /codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Instruction Schema Fit + Package Boundaries

> Implementation map for [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md). The eight required
> fields, the three schema depths, the compatibility matrix, the lifecycle semantics, the downstream enablement map
> (what signals-only unlocks and what it does not), and the upgrade path to full DART.

**Rule source:**
[rule 10 — strategy instruction schema principles](../_ssot-rules/10-strategy-instruction-schema-principles.md) **Stage
3 contract:**
[`../infra-spec/stage-3b-instruction-schema-contract.md`](../../16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md)

## Why this doc exists

Rule 10 defines the commercial and product boundary between signals-only clients and Odum's downstream stack. This doc
makes the boundary concrete: the fields, the depths, the compatibility matrix, and — critically — what signals-only
integration actually enables downstream (and what it does not). The pb2b briefing's fit-check reads from here; the pb3c
demo's gate reads from here; Stage 3B's schema contract is the runtime enforcement of what is defined here.

## (a) The eight required fields

Every signals-only instruction must express these. Absent any one, the engagement is not signals-only — it is either
full-DART (Odum runs the upstream too) or bespoke (rule 05 block 13 custom premium).

| #   | Field                                   | What it expresses                                                             | Runtime consumer                        |
| --- | --------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------- |
| 1   | Instrument + venue context              | `instrument_id` + venue / chain + instrument-type category                    | instruments-service + execution-service |
| 2   | Intended action                         | buy / sell / hedge / close / roll / combination mapped to execution primitive | execution-service algo selector         |
| 3   | Size / target exposure                  | quantity / notional / target portfolio exposure in known unit                 | risk + allocation services              |
| 4   | Timeframe / urgency                     | market / window / passive limit / scheduled mapped to execution algo          | execution-service algo library          |
| 5   | Order constraints                       | price limits, participation limits, slippage budget, venue restrictions, TIF  | execution-service algo parameterisation |
| 6   | Strategy / instruction id               | client-stable identifier for reconciliation and lifecycle                     | reconciliation + reporting attribution  |
| 7   | Lifecycle behaviour                     | supersede / add / alongside semantics for updates / replaces / cancels        | instructions-service lifecycle handler  |
| 8   | Essential risk + allocation constraints | per-instruction risk limits, per-client caps, correlation limits              | risk service + allocation service       |

## (b) Venue × instrument × execution-mode compatibility

Schema depth is compatible across most but not all combinations. Known incompatibilities:

| Venue / scope                           | Instrument type      | Execution mode            | Compatible? | Notes                                                                                     |
| --------------------------------------- | -------------------- | ------------------------- | ----------- | ----------------------------------------------------------------------------------------- |
| Any CeFi venue in `../../02-venues/`    | Spot / perps / dated | Market / limit / schedule | Yes         | Minimal schema sufficient                                                                 |
| Any CeFi venue                          | Options              | Multi-leg structure       | Depends     | Multi-leg order capability is a venue-pack sub-dimension; some venues support, some don't |
| DeFi chain in UAC `CHAIN_RPC_TEMPLATES` | Spot (DEX)           | Flash-loan / swap         | Yes         | Standard schema + DeFi-specific order constraints (slippage in bps)                       |
| DeFi chain                              | Perps (on-chain)     | Venue-native              | Depends     | Per protocol; documented in instrument-type pack                                          |
| DeFi chain                              | Options              | n/a                       | No          | BLOCKED — no DeFi options protocol integrated today                                       |
| DeFi chain                              | Dated futures        | n/a                       | No          | BLOCKED — no DeFi dated future protocol                                                   |
| Polymarket / Kalshi                     | Prediction markets   | Limit / taker             | Yes         | Standard schema; sports-specific lifecycle (event-settled)                                |
| Sports venues                           | Sports fixtures      | Pre-match / in-play       | Yes         | Rich schema with event-lifecycle fields                                                   |

For the full compatibility matrix including blocker predicates, see
[`../infra-spec/stage-3b-uac-combo-rules.md`](../../16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md) (Stage
3B).

## (c) Lifecycle behaviour — replace / cancel / amend semantics

The lifecycle field (field 7) must pick one of the following semantics per instruction:

- **Supersede.** New instruction replaces the prior one. Open quantity on the prior is cancelled; new instruction's
  parameters apply from acknowledgement.
- **Add.** New instruction sits alongside the prior. Both active, both tracked independently, reconciled to the same
  `strategy_id` for attribution.
- **Cancel.** Instruction-level cancel. Semantics: attempt to cancel open quantity on all fills belonging to this
  instruction id; prior already-filled quantity is not unwound (that would be a new counter-instruction).

Amend within an active instruction (e.g. changing a price limit on an unfilled working portion) is a lifecycle update
event on the same instruction id; it is not a new instruction. Execution-service handles the venue-side protocol (some
venues support amend; some require cancel-and-replace).

Lifecycle behaviour at the client boundary is distinct from venue-side behaviour: the client sends one semantic; Odum's
execution layer translates to the venue protocol that produces the equivalent outcome.

## (d) What signals-only integration enables downstream

A signals-only client who sends well-formed instructions against the fit-check schema gets:

| Downstream capability                            | Enabled by signals-only?                                                         |
| ------------------------------------------------ | -------------------------------------------------------------------------------- |
| Execution (algo selection, venue routing, fills) | Yes — block 7                                                                    |
| Reconciliation (instruction ↔ fills)             | Yes — part of block 1 / block 4                                                  |
| Position tracking                                | Yes — block 1 reporting core                                                     |
| P&L attribution to the client's strategy id      | Yes — but only to the client's declared `strategy_id`, not to upstream sub-logic |
| Exposure analytics on the client's flow          | Yes — block 11 analytics pack (scoped)                                           |
| Execution quality / TCA on the client's flow     | Yes — block 11 analytics pack                                                    |
| Reporting surface (positions, P&L, recon, audit) | Yes — block 1 reporting core                                                     |

## (e) What signals-only integration does NOT enable

The package boundary is load-bearing. Signals-only clients do NOT get the following without upgrading to full DART:

| Downstream capability                                                           | Enabled by signals-only?                                    |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Backtest / research surface over historical data                                | No — block 6 excluded                                       |
| Promotion pipeline (shadow → paper → live-tiny → allocated)                     | No — block 6 excluded                                       |
| Live-vs-backtest P&L comparison that requires Odum-side backtest lineage        | No — the client's upstream is not in Odum's research system |
| Full P&L attribution that traces back to upstream signal-generation features    | No — upstream stays upstream                                |
| Cross-strategy research analytics drawing on data beyond the client's own flow  | No — block 11 analytics is scoped per client                |
| Regime classification analytics (the client's own regime logic is out of scope) | No                                                          |

Why the boundary matters: if a signals-only client buys block 6 at signals-only pricing, they are underpriced. Rule 10
enforcement rule: no research / promote bolted on at signals-only pricing. The upgrade is a commercial event.

## (f) Package boundary — signals-only upgrade path to full DART

A signals-only client can upgrade. The transition:

1. **Adds block 6** (research / promote pipeline) to the engagement.
2. **Expands block 11** (analytics packs) to include cross-strategy research analytics.
3. **Shifts pricing** to full-DART tier shape.
4. **Requires schema depth reassessment.** The client may stay on the same schema depth (they keep sending instructions)
   but the research-layer gains context through their uploaded or declared strategy-logic scope.

The transition is a formal commercial event, not a bolt-on. Rule 10 enforcement rule: `signals-only → full DART` is a
new quote, new scope, new blocks — not an incremental upgrade.

## Schema depth as a pricing dimension

Block 5 (instructions integration) prices per-depth. Three indicative depths:

| Depth    | Field set                                                                                                                | Onboarding cost | Tier viability                             |
| -------- | ------------------------------------------------------------------------------------------------------------------------ | --------------- | ------------------------------------------ |
| Minimal  | The eight required fields, nothing more                                                                                  | Lowest          | Tier A viable                              |
| Standard | Required + common extensions (strategy-family tag, parent-child grouping, scheduling hints, recon annotations)           | Moderate        | Tier A or B                                |
| Rich     | Bespoke fields negotiated per client (proprietary risk dimensions, custom execution directives, custom lifecycle states) | Higher          | Tier B, often with block 13 custom premium |

Schema depth is an axis inside block 5 pricing, not a separate block.

## Pre-demo fit-check discipline

The pb2b briefing ([`../experience/dart-briefing.md`](../experience/dart-briefing.md)) includes the fit-check as the
"Does DART fit you?" section. The prospect self-sorts before a demo is scheduled. If the prospect cannot adapt to the
minimal schema, they are routed to:

- full DART (Odum runs the upstream too), or
- bespoke engagement with a custom premium (rule 05 block 13), or
- declined — the engagement doesn't fit.

## Cross-references

- [rule 10 — strategy instruction schema principles](../_ssot-rules/10-strategy-instruction-schema-principles.md)
- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — the `(Client, downstream)` cell this
  schema guards
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — block 5 (instructions
  integration), block 6 (research / promote excluded from signals-only), block 13 (custom premium for non-fit)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — schema depth as block-5 pricing dimension
- [`../infra-spec/stage-3b-instruction-schema-contract.md`](../../16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md)
  — Stage 3B runtime contract
- [`../infra-spec/stage-3b-uac-combo-rules.md`](../../16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md) —
  compatibility predicates
- [strategy-origin-vs-stack-depth.md](strategy-origin-vs-stack-depth.md) — the cell this fit-check resolves
- [../experience/dart-briefing.md](../experience/dart-briefing.md) — pb2b briefing that runs the fit-check
- [../experience/dart-demo.md](../experience/dart-demo.md) — pb3c demo gated on fit-check resolution
- [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md) — commercial framing
