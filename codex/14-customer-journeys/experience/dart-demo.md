---
doc_type: codex-ssot
title: DART — Warm-Prospect Demo
summary:
  pb3c warm-prospect DART demo on staging — signals-only walks 4 surfaces (catalogue, strategy-service,
  execution+reconciliation, reporting); full-pipeline adds research/promote/paper; research surfaces stay LOCKED-VISIBLE
  for signals-only; IM_RESERVED and CLIENT_EXCLUSIVE slots HIDDEN-ENTIRELY.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [sales, prospect]
tags: [dart, demo, prospect, sales, strategy, warm-prospect, ui]
related:
  [
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    ../demo-ops/demo-restriction-profiles.md,
    ../shared-core/same-system-principle.md,
    ../shared-core/strategy-allocation-lock-matrix.md,
  ]
created: 2026-04-20
authoritative_for: [pb3c DART warm-prospect demo experience]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts]
---

# DART — Warm-Prospect Demo

> Experience playbook for pb3c. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md),
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md), and
> [rule 10 (strategy instruction schema principles)](../_ssot-rules/10-strategy-instruction-schema-principles.md).

**Internal label:** pb3c (warm-prospect DART demo) **Status:** Stage 2 draft **Owner:** DART sales

## Audience

A fund or prop-firm operator who has completed the pb2b DART briefing, resolved the instruction-schema fit-check,
attended the second call with DART sales, and is now viewing the staging environment scoped to the resolved DART path —
signals-only `(Client, downstream)` or full pipeline `(Client, full-pipeline)`.

## Moment in journey

Warm-prospect demo. The rule-10 fit-check is resolved (signals-only or full DART) before scheduling, or the demo reads
the prospect's declared schema shape against Odum's required fields to force resolution. The demo does not interrogate
the prospect's upstream. Research, backtest, and promote surfaces stay LOCKED-VISIBLE for unresolved or signals-only
prospects per [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md).

The prospect is logged into staging with a demo user scoped to the resolved restriction profile.

## What Odum must prove

- Staging is the production UI with the prospect's restriction profile applied (see
  [`../shared-core/same-system-principle.md`](../shared-core/same-system-principle.md)).
- Signals-only path delivers a coherent downstream operating surface; research / promote remain LOCKED-VISIBLE with the
  upgrade path named.
- Full-pipeline path: research, promote, paper, live all operate on one catalogue and one component tree — phase tag is
  the only axis that changes per view.
- Demo data mirrors the prospect's declared venues, chains, and instrument types — not generic equities.
- Entitlement slicing is real: no visibility into other clients' data or `CLIENT_EXCLUSIVE` slots.

## Experience goal

The prospect leaves the demo with a named next commitment — onboarding kickoff (if the path is signals-only or full DART
and commercials are agreed), a commercial follow-up (if structure is resolved but numbers pending), or a specific scope
question to close before onboarding. Exploratory "let's see more" outcomes are a demo-design failure.

## Walkthrough

DART sales opens by confirming the demo context: prospect firm name, resolved path, restriction profile applied, demo
mode (broader / turbo / deep-dive), agenda. The agenda differs by path.

### Signals-only walkthrough — 4 surfaces

1. **Strategy catalogue** — filtered to slots the prospect's instructions will touch; maturity ≥ BACKTESTED per rule 06;
   research / promote columns LOCKED-VISIBLE.
2. **Strategy-service entry** — the runtime that hosts the prospect's instruction flow as one tenant.
3. **Execution + reconciliation** — end-to-end walk of a rule-10 instruction: algo selection → venue routing → fills →
   TCA → reconciliation breaks + resolutions.
4. **Reporting surface** — positions, P&L attribution, exposure, audit; scoped to the prospect's synthetic flow.

### Full-pipeline walkthrough — 6 surfaces

The signals-only 4 surfaces plus three that are only unlocked for full DART:

- **Research** — historical backtest of a strategy matching the prospect's mandate shape; phase tag flips to `research`;
  tables, charts, attribution identical to live view.
- **Promote** — promotion-decision ledger for a slot (shadow → paper → live-tiny → live-allocated); prospect sees the
  ladder, criteria, current state. Same artifact Odum operates internally.
- **Paper** — live-data paper-trading view; same UI as live, different phase tag, different data-source binding.

The last three surfaces (strategy-service entry, execution, reporting) are identical across both paths — that identity
is the point. See [`../shared-core/same-system-principle.md`](../shared-core/same-system-principle.md).

### Session close

DART sales closes on the next commitment — onboarding kickoff or commercial close meeting. Reservations are captured
verbatim and routed to demo-decision-matrix review.

## Key messages

1. Staging is the production UI, filtered to your resolved path.
2. Signals-only: the downstream stack is what you buy. Research and promote are locked with the upgrade-path message —
   not hidden.
3. Full pipeline: research, paper, live are phase tags on one catalogue; same components, different data bindings.
4. Your flow runs on the same components Odum uses internally (see
   [`../shared-core/same-system-principle.md`](../shared-core/same-system-principle.md)).
5. The next step is onboarding kickoff or a specific commercial close. We do not demo twice.

## What not to show

- Research, backtest, and promote surfaces for unresolved or signals-only prospects —
  [rule 04](../_ssot-rules/04-dart-commercial-axes.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) +
  [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md), LOCKED-VISIBLE with the "available in full
  DART" message. Visible in nav, locked on click. Hidden entirely would break the upgrade-path conversation.
- Pre-BACKTESTED maturity slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Other clients' CLIENT_EXCLUSIVE slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- **IM_RESERVED strategies (HIDDEN-ENTIRELY per rule 06):**
  - `ML_DIRECTIONAL_CONTINUOUS` × BTC perp/spot on Binance/Coinbase/Hyperliquid (Odum IM — BTC ML directional for 10
    clients)
  - `ML_DIRECTIONAL_CONTINUOUS` × S&P futures on CME (Odum IM — CME co-invest)
  - `VOL_TRADING_OPTIONS` × NSE options (Odum IM — India Options)
  - `ML_DIRECTIONAL_EVENT_SETTLED` × sports fixtures (Odum IM — Sports ML)
  - `STAT_ARB_PAIRS_FIXED` × crypto pairs (Odum IM — mean reversion, but ALSO PUBLIC per rule; only shown as IM in this
    filter for IM prospects)
  - All other archetype × instrument × venue cells per
    [`../shared-core/strategy-allocation-lock-matrix.md`](../shared-core/strategy-allocation-lock-matrix.md)
    forward-plan list.

  Cross-ref the matrix so the list stays maintainable — the matrix is the SSOT; this bullet mirrors its current
  snapshot.

- Other clients' positions, instructions, or reporting data —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) + [rule 07](../_ssot-rules/07-data-licensing-boundaries.md),
  HIDDEN-ENTIRELY. Entitlement slicing enforces this.
- Odum-run IM strategy internals beyond the peer-visible aggregate —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Raw venue data feeds, on-chain transaction dumps, or any surface that would read as raw-data resale —
  [rule 07](../_ssot-rules/07-data-licensing-boundaries.md), HIDDEN-ENTIRELY. Demo data is Odum-enriched or synthetic.
- Internal cost column from the pricing registry — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
- Internal ops, admin, devops, or config routes — HIDDEN-ENTIRELY.
- Client regime logic, model internals, or signal generation methodology —
  [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md), OUT-OF-SCOPE. Odum does not ingest client IP;
  the demo does not frame them as input surfaces.
- Tier A / Tier B numbers — reserved for the commercial follow-up.

## Desired next step

Agree the onboarding kickoff date or the commercial close meeting.

## Internal handoff

DART sales captures the session outcome in the account-intelligence record — surfaces covered, resolved path confirmed
(or unresolved flagged), execution-quality reactions, reporting reactions, reservations raised, named next commitment.
Signals-only prospects transitioning to onboarding: the workstreams are instruction-schema contract, venue provisioning
(from the declared venue scope), chain provisioning, reconciliation setup, and reporting entitlement. Full-pipeline
prospects transitioning to onboarding: the same, plus research surface provisioning and promote-pipeline configuration.
If the prospect surfaces a scope gap or commercial reservation, the post-demo follow-up orchestration triggers per
[`../demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md). If the prospect
has combined DART + IM or DART + Reg Umbrella intent, the companion demo is scheduled per
[`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md).

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — research, paper, live as phases over
  one system
- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks the DART paths compose
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — demo data is enriched or
  synthetic
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — no numbers in the demo
- [rule 10 — strategy instruction schema principles](../_ssot-rules/10-strategy-instruction-schema-principles.md) — the
  pre-qualification layer this demo sits on top of
- Impl-layer: [../playbooks/03c-demo-dart.md](../playbooks/03c-demo-dart.md)
- Upstream briefing: [dart-briefing.md](dart-briefing.md)
- Instruction-schema implementation map:
  [../shared-core/instruction-schema-fit-and-package-boundaries.md](../shared-core/instruction-schema-fit-and-package-boundaries.md)
- Strategy origin × stack depth matrix:
  [../shared-core/strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md)
- Demo restriction profiles: [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md)
- Demo modes: [../demo-ops/dart-demo-modes.md](../demo-ops/dart-demo-modes.md)
- DeFi demo specifics:
  [../../../plans/archive/defi_demo_e2e_workflow_2026_03_30.plan.md](../../../plans/archive/defi_demo_e2e_workflow_2026_03_30.plan.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (DART persona)
