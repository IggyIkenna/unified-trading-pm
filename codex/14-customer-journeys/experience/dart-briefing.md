---
doc_type: codex-ssot
title: DART — Post-First-Call Briefing
summary:
  pb2b DART post-first-call briefing — lets the prospect self-sort along the signals-only (Client, downstream) vs
  full-pipeline (Client, full-pipeline) axis via the 8-field instruction-schema fit-check; block-6 research/promote is
  full-DART only, 12-month minimum, pricing deferred to call 2.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [dart, briefing, prospect, sales, instruction-schema, signals-only, ui]
related:
  [
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    ../commercial-model/dart-entry-points.md,
    ../_ssot-rules/04-dart-commercial-axes.md,
    ../shared-core/strategy-origin-vs-stack-depth.md,
  ]
created: 2026-04-20
authoritative_for: [pb2b DART post-first-call briefing experience]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts]
---

# DART — Post-First-Call Briefing

> Experience playbook for pb2b. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md),
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md), and
> [rule 10 (strategy instruction schema principles)](../_ssot-rules/10-strategy-instruction-schema-principles.md).

**Internal label:** pb2b (post-first-call DART briefing) **Status:** Stage 2 draft **Owner:** DART sales

## Audience

A fund, prop firm, or single-strategy manager with a working trading operation that is running into infrastructure
limits — venue onboarding, execution quality, treasury rebalancing, regulatory cover, reconciliation fragility — and is
evaluating DART as either the downstream stack (signals-only) or the full research-to-execute pipeline.

## Moment in journey

Post-first-call. The prospect has had a thirty-minute intro with Odum leadership, signed a light-auth briefing code, and
is reading the DART briefing between the intro and the second call. The intro resolved that the path is DART, not IM or
Reg Umbrella. What the intro did not resolve is the axis within DART — signals-only `(Client, downstream)` or full
pipeline `(Client, full-pipeline)` per [rule 04](../_ssot-rules/04-dart-commercial-axes.md). The briefing's first job is
to let the prospect self-sort along that axis; the second is to show what each path actually looks like.

## What Odum must prove

- DART runs on the same services Odum operates internally (see
  [same-system-principle.md](../shared-core/same-system-principle.md)).
- The prospect's situation lands on one of three practical paths
  ([strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md)).
- Signals-only integration has a fixed, published schema. The prospect's upstream either fits it or does not.
- Research, promote, paper, and live are phase views of one system, not separate products.
- Pricing and demo scope follow from the resolved path.

## Experience goal

The prospect finishes the briefing with a resolved DART path (signals-only or full pipeline), a clear answer to the
instruction-schema fit-check, and a specific reason to book the second call — to walk the build surface they intend to
use, not to re-explore the shape.

## Walkthrough

The briefing opens with the DART rule-09 expansion. Full expansion and path definitions live in
[`../commercial-model/dart-entry-points.md`](../commercial-model/dart-entry-points.md). Inline summary: DART is Odum's
internal operating system for strategy, execution, and monitoring, packaged for client use — signals-only clients plug
upstream signals into the downstream stack; full-pipeline clients use research and promote on the same components.

The second section is the fit-check. See "Does DART fit you?" below — four sub-sections that let the prospect self-sort
before a demo is scheduled.

The third section is the strategy catalogue. One row per slot, with maturity, phase, and venue metadata. Research,
paper, and live are phase toggles over one catalogue (see
[`../shared-core/same-system-principle.md`](../shared-core/same-system-principle.md)). Pre-BACKTESTED maturity is hidden
externally.

The fourth section is the research, promote, and execution loop. Full-pipeline clients use all three. Signals-only
clients use execution, reporting, and reconciliation only — block 6 (research / promote) is excluded per rule 04.

The fifth section is commitment and structure. Twelve-month minimum engagement. Venue, chain, and instrument-type packs
scope per client. Pricing per block, tier-mixable. Numbers land on the second call.

The briefing closes with the second-call hook: a forty-five-minute session with DART sales, agenda set by the resolved
path.

### Does DART fit you?

Before the demo, the prospect decides whether their situation fits DART, and if so, which path. The fit-check has four
parts. Read them; answer the questions; come to the second call with a resolved answer or a specific question for Odum.

#### Schema explainer (one paragraph)

Odum's execution runs on a defined instruction schema. A client-side strategy or signal generator sends structured
instructions in; Odum's downstream stack (execution, risk, allocation, reporting) operates on them. The schema is fixed
in the sense that Odum needs certain fields to run cleanly; it is flexible in the sense that the fields are
straightforward for any working systematic operation to produce. The schema is published; the fit-check is whether the
prospect's upstream can produce it.

#### What Odum needs from you

Eight fields, required on every instruction:

- Instrument and venue context — the instrument, the venue or chain, the instrument-type category.
- Intended action — buy, sell, hedge, close, roll, or a combination that maps to a known execution primitive.
- Size or target exposure — quantity, notional, or target exposure in a unit Odum's risk and allocation services
  understand.
- Timeframe or urgency — market, scheduled, over-window, passive limit. Maps onto Odum's execution-algo library.
- Order constraints — price limits, participation limits, slippage budget, venue restrictions, time-in-force.
- Strategy or instruction identifier — a client-stable identifier linking the instruction to the client's upstream
  strategy for reconciliation and lifecycle linkage.
- Lifecycle behaviour — how the client modifies, replaces, or cancels an open instruction. Explicit supersede / add /
  alongside semantics.
- Essential risk and allocation constraints — per-instruction risk limits, per-client allocation caps, correlation
  limits the client wants Odum to respect.

A prospect whose upstream already produces these — or can be adapted to produce them — fits signals-only.

#### What Odum does not need from you

Explicitly out of scope:

- Regime classification logic. How the client decided "we're in a risk-on regime" is not Odum's concern. The decision
  comes in as an instruction; the reasoning stays upstream.
- Raw model logic. Features, weights, code, training process. All upstream.
- Signal-generation methodology. How market data became a trading signal. Upstream.
- Broader upstream IP. Portfolio construction math, optimisation objective, capacity models. Upstream.

The client's strategic edge stays on the client's side of the fence. Signals-only DART is downstream only.

#### Signals-only versus full DART

The full signals-only-vs-full-DART comparison matrix lives in
[`../shared-core/strategy-origin-vs-stack-depth.md § Three practical paths`](../shared-core/strategy-origin-vs-stack-depth.md#three-practical-paths).
Headline differences:

- **Research / promote pipeline (block 6):** full DART only. Signals-only is excluded per rule 04.
- **Execution, reporting, reconciliation:** both paths.
- **Pricing model:** signals-only is scope-fixed Tier B, block-based. Full DART adds per-backtest metering and IP-power
  exclusivity tiers.
- **Cross-strategy research analytics:** full DART only.

Pricing detail: [`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md).

The upgrade from signals-only to full DART is a commercial event (rule 04), not a bolt-on. Prospects expecting research
access should resolve to full DART now.

## Key messages

1. DART is the set of services Odum uses to build, research, promote, execute, and monitor its own strategies — packaged
   for client use.
2. Two paths within DART — signals-only or full pipeline. The instruction-schema fit-check resolves which one fits.
3. Research, paper, and live are phase views of the same system. Catalogue rows carry phase tags; there is one
   catalogue, not three.
4. Signals-only clients send instructions in and use execution, reporting, and reconciliation. They do not receive the
   research and promote pipeline — that is the full-DART block boundary.
5. Twelve-month minimum engagement. Venue, chain, and instrument-type packs scope per client. Pricing is per block,
   mixable across tiers.

## What not to show

- Internal cost column from the pricing registry — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
  Internal cost is codex-private; client-facing surfaces carry Tier A and Tier B only, and neither appears in the
  briefing.
- Specific client integrations, client names, or client-specific strategy detail —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY. Anonymised aggregates only.
- Pre-BACKTESTED maturity slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) +
  [strategy-availability](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md),
  HIDDEN-ENTIRELY. CODE_NOT_WRITTEN and CODE_WRITTEN do not appear on external surfaces.
- For signals-only prospects: the research, backtest, and promote-pipeline surfaces —
  [rule 04](../_ssot-rules/04-dart-commercial-axes.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  LOCKED-VISIBLE. The surfaces appear in the catalogue navigation with a lock and the message "available in full DART";
  they are not demonstrated in the briefing or the pb3c demo.
- Raw data feeds, tick-feed subscriptions, on-chain data dumps —
  [rule 07](../_ssot-rules/07-data-licensing-boundaries.md), HIDDEN-ENTIRELY. DART is enriched services; raw data is not
  on the table.
- Other clients' CLIENT_EXCLUSIVE strategy slots —
  [strategy-availability](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md),
  HIDDEN-ENTIRELY.
- Strategies in the catalogue with `INVESTMENT_MANAGEMENT_RESERVED` lock state — these are strategies Odum is running
  for its own IM mandates (BTC ML, CME S&P, India Options delta trading, sports ML, and the forward-plan archetype cells
  per [`../shared-core/strategy-allocation-lock-matrix.md`](../shared-core/strategy-allocation-lock-matrix.md)).
  HIDDEN-ENTIRELY from DART prospects. Rule 03 + rule 06 enforcement.
- Internal engineering architecture or component diagrams beyond the rule-03 same-system framing —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY for standard briefings. Technical-diligence
  sessions run a different playbook.
- Tier A / Tier B numbers — reserved for the second call. Briefing is scope and discipline, not pricing.

## Desired next step

Book the forty-five-minute DART sales session, with the fit-check resolved.

## Internal handoff

DART sales picks up the prospect once the session is booked. The CRM record updates with the briefing-read event, the
fit-check resolution (signals-only, full-pipeline, or unresolved), and any section-skip or dwell signals from the
briefing view. DART sales prepares the session against the resolved path — signals-only sessions walk the
instruction-schema contract against the prospect's upstream (see
[`../shared-core/instruction-schema-fit-and-package-boundaries.md`](../shared-core/instruction-schema-fit-and-package-boundaries.md));
full-pipeline sessions walk the research surface. If the session produces alignment, the prospect transitions to pb3c —
the warm-prospect DART demo on staging — with a demo user provisioned to the resolved restriction profile from
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md).

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — research, paper, live as phases of one
  system
- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — the axis resolution the fit-check serves
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks the DART paths compose
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md) — exclusion set for DART
  briefings
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — enriched-services framing
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — twelve-month minimum, internal cost private
- [rule 10 — strategy instruction schema principles](../_ssot-rules/10-strategy-instruction-schema-principles.md) — the
  schema this briefing's fit-check section implements
- Impl-layer: [../playbooks/02b-research-dart.md](../playbooks/02b-research-dart.md)
- Downstream demo: [dart-demo.md](dart-demo.md)
- Instruction-schema implementation map:
  [../shared-core/instruction-schema-fit-and-package-boundaries.md](../shared-core/instruction-schema-fit-and-package-boundaries.md)
- Strategy origin × stack depth matrix:
  [../shared-core/strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md)
- DART entry points: [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md)
- Demo restriction profile for `(Client, downstream)`:
  [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (DART persona)
