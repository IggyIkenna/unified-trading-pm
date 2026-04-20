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

Warm-prospect demo. This demo assumes the prospect has already self-sorted through the rule-10 fit-check in the pb2b
briefing. Before the demo is scheduled, either the fit-check is resolved — signals-only or full DART — or the demo
itself is designed to surface the resolution by reading the prospect's declared schema shape against Odum's required
fields. The demo does not interrogate the prospect about their upstream; it either works against a resolved path or uses
the surfaces under scope to make the path obvious to the prospect. Under no circumstances are research, backtest, or
promote surfaces shown to an unresolved or signals-only prospect — those surfaces stay LOCKED-VISIBLE with the
"available in full DART" message until full-DART is resolved. See
[rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md) for the underlying discipline.

The prospect is logged into staging with a demo user scoped to the resolved DART restriction profile.

## What Odum must prove

- The staging environment is the production UI. Same catalogue, same terminal, same reporting, same execution surfaces —
  with the prospect's restriction profile applied ([rule 03](../_ssot-rules/03-same-system-principle.md)).
- For signals-only prospects: the downstream stack (strategy-service entry, instructions integration, execution layer,
  reporting) is a coherent operating surface, and the research / promote pipeline is visible but locked with the upgrade
  path named.
- For full-pipeline prospects: research, promote, paper, and live operate on the same catalogue and the same components
  — the phase tag on a slot is the only thing that changes across views.
- Execution quality, reconciliation, and reporting render with demo data that mirrors the prospect's declared flow —
  venues, chains, instrument types — not generic equities.
- Entitlement slicing is real: the prospect does not see other clients' data or their CLIENT_EXCLUSIVE slots.

## Experience goal

The prospect leaves the demo with a named next commitment — onboarding kickoff (if the path is signals-only or full DART
and commercials are agreed), a commercial follow-up (if structure is resolved but numbers pending), or a specific scope
question to close before onboarding. Exploratory "let's see more" outcomes are a demo-design failure.

## Walkthrough

DART sales opens the session by confirming the demo context — prospect firm name, resolved path (signals-only vs full
pipeline), the restriction profile applied, the demo mode (broader platform for first-look; turbo or deep-dive if the
prospect wants depth on a specific surface), and the session agenda. The agenda differs by path.

### Signals-only walkthrough

Four surfaces, in order.

The first is the strategy catalogue, filtered to the slots the prospect's declared instruction flow will touch. Each row
shows maturity (BACKTESTED and later only, per [rule 06](../_ssot-rules/06-show-dont-show-discipline.md)), phase (live),
and scope. The research and promote columns on the catalogue are LOCKED-VISIBLE with the "available in full DART"
message.

The second is strategy-service entry. The prospect sees the runtime surface that will host their per-instruction
execution, risk, and allocation wiring. The narrative names the fact that this is the same runtime Odum uses for its own
strategies, with the prospect's flow as one tenant — same system, partitioned view per
[rule 03](../_ssot-rules/03-same-system-principle.md).

The third is execution and reconciliation. The demo walks an end-to-end flow: an incoming instruction with all eight
required fields (see [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md)), execution algo selection,
venue routing, fills, reconciliation. The prospect sees TCA, execution-quality metrics, reconciliation breaks and
resolutions. The narrative emphasises that the instruction schema is fixed and published; what the prospect sends in is
operated on here.

The fourth is the reporting surface. Positions, P&L attribution, exposure analytics, audit trail — scoped to the
prospect's synthetic flow. The reporting surface is the same one IM and Reg Umbrella clients use
([rule 03](../_ssot-rules/03-same-system-principle.md)).

### Full-pipeline walkthrough

Six surfaces, in order. First three are research, promote, and paper — the signals-only gating is lifted. The fourth
through sixth are strategy-service entry, execution, and reporting, identical to the signals-only walkthrough but
presented on top of a research-originated flow rather than an incoming-instruction flow.

The research surface shows a historical-window backtest of a strategy the prospect's mandate shape fits. Phase tag on
the catalogue row flips to `research` while the rest of the UI — tables, charts, attribution — is identical to the live
view ([rule 03](../_ssot-rules/03-same-system-principle.md) sub-claim b and c).

The promote surface shows the promotion-decision ledger for a slot — shadow-evaluated → paper → live-tiny →
live-allocated. The prospect sees the ladder, the criteria, and the current state. The narrative names the fact that the
ladder is the same one Odum operates internally; the prospect is looking at the actual operating artifact.

The paper surface shows a live-data paper-trading view. Same UI as live; different phase tag; different data-source
binding ([rule 03](../_ssot-rules/03-same-system-principle.md) sub-claim e).

Strategy-service entry, execution, reconciliation, and reporting mirror the signals-only walkthrough. The last three
surfaces are identical across the two paths; that is the point.

### Session close

DART sales closes with the resolved next commitment. Signals-only prospects: onboarding kickoff or commercial follow-up.
Full-pipeline prospects: the same, with research-surface onboarding included. If the prospect surfaces a reservation, it
is captured verbatim and routed to the demo-decision-matrix review.

## Key messages

1. Staging is the production UI. What you see is the system, filtered to your resolved path.
2. For signals-only: the downstream stack is what you buy. Research and promote are locked with the upgrade-path message
   — not hidden, not fudged.
3. For full pipeline: research, paper, and live are phase tags on one catalogue. Same components, different data
   bindings.
4. Your instruction flow (or strategy flow) runs on the same components Odum uses for its own strategies. One system,
   partitioned view.
5. The next step is onboarding kickoff or a specific commercial close. We do not demo twice.

## What not to show

- Research, backtest, and promote surfaces for unresolved or signals-only prospects —
  [rule 04](../_ssot-rules/04-dart-commercial-axes.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) +
  [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md), LOCKED-VISIBLE with the "available in full
  DART" message. Visible in nav, locked on click. Hidden entirely would break the upgrade-path conversation.
- Pre-BACKTESTED maturity slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Other clients' CLIENT_EXCLUSIVE slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
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
  [../../../plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md](../../../plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (DART persona)
