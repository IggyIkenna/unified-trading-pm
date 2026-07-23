---
doc_type: codex-ssot
title: Rule 10 — Strategy instruction schema principles
summary:
  "The (Client, downstream) signals-only fit-check — the eight required instruction-schema fields Odum execution needs,
  what Odum explicitly does NOT need (client IP stays upstream), the signals-only package boundary (no research/promote
  by default), and schema-depth as a block-5 pricing dimension."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin, sales]
tags: [customer-journey, sales, dart, strategy, execution]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
  ]
created: 2026-04-20
authoritative_for: [signals-only instruction-schema principles ((Client, downstream) fit-check)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 10 — Strategy instruction schema principles

> The fit-check layer for the `(Client, downstream)` DART path. Signals-only clients and Odum exchange a defined
> instruction schema. What Odum needs, what Odum does not need, and what package boundary follows from that — fixed
> before a demo, not re-litigated per engagement.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On DART commercial model (rule 04)" + 2026-04-19 user
directive to make the fit-check layer a first-class rule.

## Why this rule exists

Rule 04 resolves commercial engagements into three paths, one of which — `(Client, downstream)` — is the signals-only
DART path. The client keeps their strategy IP upstream; Odum operates the downstream stack (execution, trading,
reporting, observation). The boundary between "what the client sends in" and "what Odum runs" is the instruction schema.

That boundary has to be clear **before** a demo so the prospect self-sorts: either their signal surface fits the schema
or it does not. Without rule 10, signals-only demos drift into "can Odum accommodate your custom upstream logic"
negotiations, which collapse into custom-solution premiums (block 13) or failed engagements.

## What Odum execution needs (the required schema)

Every client instruction that comes in must express the following, at minimum:

1. **Instrument + venue context** — what the instrument is, on which venue or chain, in which instrument-type category.
   Unambiguous reference to an entry in Odum's instruments catalogue.
2. **Intended action** — buy / sell / hedge / close / roll / combination. Action must map onto a known execution
   primitive.
3. **Size / target exposure** — quantity, notional, or target portfolio exposure. Expressed in a unit Odum's risk and
   allocation services understand.
4. **Timeframe / urgency** — is this a market order, an over-a-window order, a passive limit, a scheduled execution?
   Maps onto the execution-algo library.
5. **Order constraints** — price limits, participation limits, slippage budget, venue restrictions, time-in-force. The
   minimum set that lets Odum select and parameterise the appropriate execution algo.
6. **Strategy / instruction id** — a client-stable identifier linking this instruction to the client's upstream strategy
   or signal. Required for reconciliation, P&L attribution back to client strategies, and lifecycle linkage.
7. **Lifecycle updates / replace / cancel behaviour** — how the client modifies, replaces, or cancels an open
   instruction. Must be explicit: does a new instruction supersede the old one, add to it, or sit alongside?
8. **Essential risk + allocation constraints** — per-instruction risk limits, per-client allocation caps, correlation
   limits the client wants Odum to respect.

These are the load-bearing fields. Absent any of them, Odum cannot cleanly execute; the client is either on the wrong
path (should be full DART) or the engagement is bespoke (rule 05 block 13 custom premium).

## What Odum does NOT need

Explicitly out of scope for the signals-only instruction surface:

- **Regime classification logic.** How the client decided "we're in a risk-on regime" — not Odum's concern. Odum
  receives the decision (size / direction / instrument), not the reasoning.
- **Raw model logic.** The client's predictive model internals. Odum does not need features, weights, code, or training
  process.
- **Signal-generation methodology.** How the client went from market data to trading signal. The signal itself comes in
  as an instruction; the generation is upstream.
- **Broader upstream IP.** Portfolio construction math, optimisation objective, capacity models — all upstream.

Rule 10's boundary is explicit: the client sends instructions; Odum operates on them. The client's IP stays on the
client's side of the fence.

## Package boundaries

A signals-only engagement unlocks a bounded set of building blocks (per rule 05):

**Included:**

- Reporting core (block 1).
- Strategy-service entry (block 4) — the runtime hosting the client's per-instruction execution, risk, and allocation
  wiring.
- Instructions integration (block 5) — the schema surface itself.
- Execution layer (block 7).
- Venue packs (block 8), chain packs (block 9), instrument-type packs (block 10) — scoped to the venues / chains /
  instrument types the client's instructions touch.
- Selected analytics packs (block 11) — execution quality, reconciliation, exposure analytics on the client's own flow.

**Not included by default:**

- Research / promote pipeline (block 6). Signals-only clients do not automatically get research, backtest, paper, or
  promotion capabilities.
- Analytics packs that would require derived research on underlying data beyond the client's own flow.

**Why the boundary matters:** a signals-only client buying Odum's research pipeline at signals-only pricing is
underpriced; Odum either upgrades them to full DART pricing or declines. Rule 04's enforcement rule "signals-only
clients don't get research/promote" is load-bearing.

### Upgrade path

A signals-only client can upgrade to full DART later. The transition adds block 6 (research/promote pipeline), expands
analytics packs, and shifts pricing. It is a deliberate commercial event, not an incremental bolt-on.

## Schema depth as a pricing dimension

Block 5 (instructions integration) is priced per-depth. Three indicative depths:

- **Minimal schema** — the eight required fields above, little more. Lowest onboarding cost. Thinnest instruction
  surface. Tier A viable.
- **Standard schema** — required fields + common extensions (strategy-family tags, parent-child instruction grouping,
  scheduling hints, reconciliation annotations). Tier A or B.
- **Rich schema** — bespoke fields negotiated per client (proprietary risk dimensions, custom execution directives,
  custom lifecycle states). Tier B, often with custom-solution premium (block 13).

Schema depth is an axis inside block 5. Different clients on the signals-only path sit at different depths; pricing
reflects depth.

## Pre-demo fit-check discipline

Before a signals-only demo, a fit-check runs:

1. **Does the prospect's current signal / instruction surface express the eight required fields?** If yes, proceed. If
   no, flag the gap.
2. **Where the gap exists, can the prospect adapt?** Most prospects can — adding a stable strategy id, expressing size
   in Odum-understood units, defining replace-cancel behaviour. Some can't — their upstream system is too rigid.
3. **If the prospect cannot adapt at the minimal depth, they are not a signals-only client.** Either they are a full
   DART client (Odum runs the upstream too) or they are a bespoke engagement (custom premium). Do not force-fit them
   into signals-only.
4. **The fit-check happens in pb2b (post-first-call DART briefing).** The briefing includes the required-fields table;
   the prospect's follow-up call includes a schema walk-through.

Enforcing this upstream saves two kinds of waste: demos that end in "we can't integrate", and engagements that ship and
then struggle because the schema didn't fit.

## Commercial quote enforcement

Every `(Client, downstream)` commercial quote references rule 10 explicitly:

- The quote line for block 5 (instructions integration) names the schema depth (minimal / standard / rich) and the tier
  (A or B).
- The quote excludes block 6 (research/promote pipeline) unless the engagement is full-DART.
- The quote flags any deviations from the minimal-schema defaults so pricing and scope are aligned.

Quotes that omit a schema depth, or that slip block 6 in at signals-only pricing, are rule-10 violations and get kicked
back.

## Interaction with the same-system principle

Rule 03 says one operating system, many views. Rule 10 specifies how a signals-only client's view is constructed:

- The client uses the same strategy-service runtime Odum uses internally — but entry is via the instructions integration
  API, not the full strategy-authoring surface.
- The client sees the same reporting surface Odum uses internally — entitlement-sliced to their own flow.
- The client does **not** see the research / promote / strategy-authoring surfaces (rule 06 LOCKED-VISIBLE), because
  their path does not include them.

Same system, partitioned view — the partition is precisely what rule 10 defines.

## Enforcement rules

1. **Required fields are non-negotiable.** A signals-only engagement without one of the eight required fields is not
   signals-only; either it is full-DART or bespoke.
2. **Out-of-scope items stay out of scope.** Odum does not ingest client regime logic, model internals, or signal
   generation methodology. Clients keep their IP upstream.
3. **Package boundary is explicit.** Signals-only = downstream stack; no research/promote by default. Exceptions upgrade
   to full-DART pricing, not bolt-on.
4. **Pre-demo fit-check.** pb2b briefing includes the required-fields table; the prospect self-sorts before a demo is
   scheduled.
5. **Commercial quote discipline.** Every signals-only quote names the schema depth and excludes research/promote
   explicitly.
6. **Upgrade path is formal.** Signals-only → full-DART is a commercial event, not a ticket. New scope, new quote, new
   blocks.

## Stage 2 implications

- `commercial-model/signals-only-schema.md` (new in Stage 2) tabulates the eight required fields, three indicative
  depths, and pricing treatment.
- pb2b briefing doc carries a one-page summary of rule 10 in rule-02 voice.
- `demo-ops/demo-restriction-profiles.md` for `(Client, downstream)` LOCKED-VISIBLE locks research/promote pipeline.
- Every signals-only quote template references rule 10 and names the schema depth.

## Stage 3 implications

- Stage 3B registry declares schema depth as a sub-dimension of block 5.
- Stage 3C derivation engine resolves signals-only entitlements to exclude block 6 by default.
- Instruction-schema validation is a runtime concern (instructions-service + UAC), not a rule 10 concern — rule 10 is
  about commercial + product boundary, not runtime validation.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On DART commercial model (rule 04)" + 2026-04-19 instruction
  schema directive
- [`04-dart-commercial-axes.md`](04-dart-commercial-axes.md) — rule 10 is the fit-check for the `(Client, downstream)`
  cell
- [`05-building-block-dimensions.md`](05-building-block-dimensions.md) — block 5 (instructions integration) is the
  scoped block; rule 10 defines its depth axis
- [`08-pricing-principles.md`](08-pricing-principles.md) — schema depth becomes a pricing dimension inside blocks 5 and
  7
- [`03-same-system-principle.md`](03-same-system-principle.md) — same-system partitioned-view framing underpins the
  boundary
- [`06-show-dont-show-discipline.md`](06-show-dont-show-discipline.md) — research/promote stays LOCKED-VISIBLE on
  signals-only demos
