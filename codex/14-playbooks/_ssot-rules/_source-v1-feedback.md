---
scope: [engineer, admin, sales]
---

# Source: v1 agent feedback on the playbook SSOT (2026-04-19)

This file captures the structural decisions from the "Client Experience Playbooks — Polished v1" feedback session, with
additions from the 2026-04-19 research↔live unification directive. It is the stable citation target for every
`_ssot-rules/*.md` file.

The full prose version of v1 (tone commentary, per-playbook narrative drafts, Axis/POD benchmarks, and the agent's
structural critique) was provided in the 2026-04-19 conversation. The Stage 1 agent executing
`plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md` Phase 1.0 should append the full verbatim text below the
**`## Full v1 prose (appendix)`** marker at the end of this file.

## Key structural claims (authoritative summary)

### On tone + posture

- Calm, specific, credible, lightly guided, never desperate.
- Restrained institutional posture. Benchmarks: [axis.to](https://www.axis.to/) and [podlabs.xyz](https://podlabs.xyz/).
- What to borrow from those benchmarks: restrained headlines; a few concrete proof points; clear explanation of how the
  operating model works; sparse navigation; low-drama trust markers.
- What **not** to borrow: waitlist-first posture, unfinished-page energy, retail-facing vocabulary, forward-tense
  language that implies the product isn't live today.
- Explicit anti-goal: do not sound AI-generated. Written by people who have run trading businesses.

### On document grammar (rule 01)

Every experience playbook has these 9 sections, in order:

1. Audience
2. Moment in journey
3. What Odum must prove
4. Experience goal
5. Walkthrough
6. Key messages
7. What not to show
8. Desired next step
9. Internal handoff

### On the same-system principle (rule 03)

Five sub-claims, locked 2026-04-19:

- **(a)** DART, IM, and Regulatory Umbrella client surfaces are **partitioned views of the same internal Odum operating
  system**, not three separate products.
- **(b)** **Research infrastructure ≡ live infrastructure.** Any metric generated during research is generated in live
  trading via the same underlying component.
- **(c)** The trading terminal is a **live/batch toggle over the same component tree.** Same numbers, same tables, same
  charts — the data source binds differently.
- **(d)** The strategy catalogue carries **phase tags** (research / paper / live) on a single row; the UI does not fork
  into separate catalogue products per phase.
- **(e)** Paper trading has the **same look and feel** as live. Paper is not a separate product.

**Phase (research/paper/live) is orthogonal to maturity (CODE_NOT_WRITTEN → LIVE_ALLOCATED).** A `LIVE_ALLOCATED` slot
can still be viewed in research phase when a researcher re-runs it over historical data. Phase is an execution-context
dimension; maturity is a promotion-stage dimension.

### On DART commercial model (rule 04)

**Two axes:**

- **Strategy origin** — Odum strategy vs client strategy
- **Stack depth** — reporting-only visibility / client-strategy+downstream-integration / full-DART-pipeline

**Three practical commercial paths** collapse out of those axes:

1. Reporting-only visibility — closer to reporting or regulatory visibility than true DART.
2. Client strategy + downstream integration — client keeps strategy generation outside Odum, sends instructions in, uses
   execution / trading / selected analytics / monitoring.
3. Full DART pipeline — client buys into enriched data services, research, backtesting, promotion, execution, trading,
   observation.

If a client wants Odum strategy exposure inside DART, they sit in path 3, not path 1 or 2.

### On data licensing boundary (rule 07)

DART is sold as **enriched platform and research services built on top of underlying data sources**, subject to
licensing and commercial constraints. DART is **not** a direct raw-data resale product.

Internal pricing can use data-sensitive building blocks; external positioning always frames the product as enriched
services.

### On building-block dimensions (rule 05)

Thirteen internal building blocks:

1. Reporting core
2. Regulatory umbrella reporting
3. IM allocator reporting
4. Strategy-service entry
5. Instructions integration
6. Research / promote pipeline
7. Execution layer
8. Venue packs (per venue or venue group)
9. Chain packs (per chain)
10. Instrument-type packs (per type: options / perps / futures / spot / sports-fixture / prediction-market / ...)
11. Analytics packs
12. Exclusivity / non-compete premium
13. Custom solution premium

These dimensions drive: (a) client-facing packaging in Stage 2's `commercial-model/pricing-building-blocks.md`, (b)
demo-restriction-profile construction in Stage 2's `demo-ops/`, (c) UAC combo rules in Stage 3B, (d) the
one-registry-four-derivations engine in Stage 3C.

### On pricing (rule 08)

Two external tiers:

- **Tier A — cost-plus.** Variable cost pass-through with a thin margin. Low barrier. No upfront. Per-block; client can
  buy some blocks on Tier A.
- **Tier B — fixed.** Upfront plus fixed monthly. Predictable. Unlocks exclusivity and custom premiums.

Twelve-month minimum commitment on both tiers. Internal cost column is codex-private — never appears in any
client-facing document. Clients can mix tiers per block (Tier A on marginal venues + Tier B on core reporting, for
example). Exclusivity and custom solution premiums are Tier B only.

Numbers are populated by Odum finance in Stage 2 outputs; this rule file is principles-only.

### On internal commercial one-liners (rule 09)

User voice, 2026-04-19:

- **DART** — "an accelerator for strategy, research, execution, and control — the same system Odum uses internally."
- **IM** — "allocate capital to Odum-managed strategies; reporting is built in because it is the same reporting system
  Odum uses itself."
- **Reg Umbrella** — "operate your regulated activity under Odum's FCA permissions; onboarding, compliance, MLRO,
  supervision, and reporting included."

These are internal sales shorthand. Every public-facing doc expands each into a calm, institutional paragraph using the
rule 02 tone; internal docs can use them directly.

### On the layered directory structure

```
codex/14-playbooks/
├── _ssot-rules/       (rules governing every experience doc — this dir)
├── experience/        (narrative playbooks, sales-owned)
├── shared-core/       (product truths reused across layers)
├── commercial-model/  (packaging, tiers, pricing — structure only; numbers from finance)
├── demo-ops/          (demo controls + sales ops — consolidated)
├── implementation-mapping/  (routes, personas, QA coverage)
├── playbooks/         (IMPL LAYER — engineering-grade, pre-existing)
├── authentication/    (IMPL LAYER)
├── environments/      (IMPL LAYER)
├── cross-cutting/     (IMPL LAYER)
├── page-triage/       (pre-existing — 177-page classification)
├── testing/           (pre-existing — Playwright coverage)
├── roadmap/           (superseded by infra-spec/stage-3e-refactor-plan.md on Stage 3 merge)
├── infra-spec/        (Stage 3 outputs — audit, combo rules, derivation engine, refactor plan)
└── presentations/     (Stage 3D target-experience slide deck with mermaid + screenshots)
```

### On demo mode vs commercial path vs production restriction

Three independent axes. Stage 3 specs the infra that lets all three derive from the same UAC combo registry:

- **Demo mode** — broader platform OR turbo; chosen per prospect, configurable toggle for comparison.
- **Commercial path** — reporting-only visibility / client-strategy+downstream / full-pipeline (DART); or IM /
  Reg-Umbrella path.
- **Production restriction** — what the paying client actually gets gated to.

### On sales ops orchestration

Every prospect generates an **account-intelligence record** (not just a lead tag) covering: organisation, service
interests, markets, commercial path, call notes, objections, inferred gaps, next-meeting hypothesis. Each demo session
appends back so later calls are cumulative. Stage 2 `demo-ops/` specifies structure; Stage 3E refactor plan specs the
CRM implementation.

Explicit orchestration rules: 7-day stall trigger, post-step follow-up asset per stage, qualification criteria per stage
transition.

## Full v1 prose (appendix)

> The verbatim v1 prose below was captured from the 2026-04-19 conversation by the master planner. It preserves the
> narrative drafts, tone commentary, and structural recommendations in the original voice. For authoritative summary of
> structural claims, see the top of this file.

### What changes across the 9 playbooks

The client-experience playbook layer is nine documents. What is no longer limited to nine is the wider documentation
system around them: those nine sit alongside separate directories for the shared product model, commercial model, demo
controls, sales ops, registry and entitlements, and implementation mapping. So: nine playbooks, more than nine docs
overall.

These playbooks should read as client-experience operating documents, not just route maps.

### Tone and posture

These should not feel pushy, needy, or overly sales-led. The buyer is often skeptical, commercially aware, and used to
filtering out exaggerated claims.

The right posture: calm · specific · credible · lightly guided · never desperate.

The goal is not to force conversion. The goal is to help the prospect recognise fit, see what is already solved, and
understand what they may still be underestimating. That means the experience should create confidence without sounding
like it is trying too hard. A good benchmark is the restrained style used by firms that lead with a simple proposition,
clear trust markers, and a low-drama explanation of how the system works, rather than aggressive CTA stacking.

For Odum specifically: avoid writing that sounds AI-generated, generic, or over-optimised. The experience should feel
like it was written by people who actually understand how trading businesses are built and where they usually break.

A useful internal benchmark is the restrained posture seen on certain modern capital-markets and fund-infrastructure
sites: simple proposition, sparse navigation, a few hard proof points, a calm explanation of how the system works. What
is worth borrowing is the restraint. What is not worth borrowing: vague waitlist energy, unfinished-page energy, or
language that feels more promotional than operational.

Across all nine, the writing consistently answers:

- who this buyer is
- what they care about right now
- what Odum must prove in this moment
- what we show first
- what we do not show unless asked
- what the next commitment is

Use the same document grammar everywhere (the nine sections from rule 01).

### Playbook 1 — Marketing, pre-first-call

- **Audience:** anonymous visitor with little or no prior context on Odum.
- **Moment:** very top of funnel; deciding whether Odum is relevant enough for a first conversation.
- **What Odum must prove:** credible; institutional; does three clear things; there is an obvious next step.
- **Experience goal:** move visitor from curiosity to informed self-selection among IM / Platform / Regulatory Umbrella.
  A softer win also counts: spends time on deeper pages, requests more information, leaves with a clearer understanding
  of where Odum may fit.
- **Walkthrough:** homepage with one institutional message — one firm, three commercial entry points, one underlying
  operating platform. From there, into one of three service pages (IM / DART / Regulatory Umbrella). Firm page supports
  trust, not the conversion burden. Contact page removes friction.
- **Key messages:** Odum is a regulated institutional operator, not a generic software vendor. Clients can allocate,
  build and run, or operate under coverage. Same underlying infrastructure supports all three.
- **What to show first:** three commercial options; institutional trust markers; breadth of markets + coverage; one
  strong CTA per service.
- **What not to show unless asked:** deep product taxonomy; internal service decomposition; orphan pages; technical
  route language.
- **Desired next step:** book a first call, request a demo, submit an enquiry with a tagged service preference, or
  intentionally continue deeper.
- **Internal handoff:** qualified lead moves into the briefing flow with a tagged service interest. Becomes an
  account-intelligence record — not a simple lead tag — capturing org name, service interests, markets of interest,
  likely commercial path, call notes, objections raised, inferred gaps in their current setup, next meeting hypothesis.

### Playbook 2 — Research & Documentation hub

- **Audience:** prospect who has already had a first call and now wants deeper material before committing to a live
  demo.
- **Moment:** middle of funnel; validating fit, seriousness, commercial relevance.
- **What Odum must prove:** proposition is real + structured; Odum understands the client's use case; credible next step
  into the product exists.
- **Experience goal:** give the prospect enough depth to become demo-ready without overwhelming them. Should feel like a
  thoughtful layer of material that helps a serious buyer pressure-test their own readiness — not a pitch deck in
  disguise.
- **Walkthrough:** briefings hub — curated, not encyclopedic; access gate reinforces guided commercial posture. Three
  briefing paths: IM / DART / Regulatory Umbrella. Each tile answers one question fast: why would someone like me click
  this?
- **Key messages:** these are briefing materials, not the full platform; each path corresponds to a real commercial
  engagement; the next step after reading is a focused product demo.
- **What to show first:** who each pillar is for; what outcome each pillar enables; what the prospect will understand by
  the end.
- **What not to show unless asked:** excessive cross-linking into internal codex; implementation language; feature lists
  without business meaning.
- **Desired next step:** progress to one of the flavour-specific demos, or schedule a follow-up call around open
  questions.
- **Internal handoff:** sales should know which pillar was accessed, how long the prospect engaged, and whether they are
  ready for pb3.

### Playbook 2a — Investment Management briefing

- **Audience:** allocator or mandate prospect considering giving capital to Odum-managed strategies.
- **Moment:** understand the category; deciding whether Odum is credible, differentiated, operationally mature.
- **What Odum must prove:** Odum runs its own strategies within a regulated framework; the operating model is real;
  reporting + entity structure are institutional; allocator experience is clear from day one; the client is seeing the
  same reporting setup Odum uses internally — not a separate lightweight client layer.
- **Experience goal:** turn a general IM conversation into confidence that Odum can be evaluated seriously as a manager.
- **Walkthrough:** open with what Odum IM is in plain language — clients allocate capital to Odum-managed systematic
  strategies run on Odum's own infrastructure. That same infrastructure includes the reporting setup Odum uses itself.
  The IM client is not being shown a separate reporting product. They are being shown the same core client-reporting
  structure, organised around organisations, funds, and one or more clients. In pooled structures, external client sees
  own share of fund performance rather than combined picture. Internally Odum can still view combined across all
  clients. IM path also includes strategy choice. Then move through: what Odum manages → how Odum is structured → what
  the allocator receives → what the allocator does next. The four catalogues support credibility but don't dominate.
- **Key messages:** Odum is not just signals or tooling; it is a manager running its own stack. Pooled and SMA both
  supported. Client reporting is allocator-grade because it is built on the same reporting core Odum uses itself.
  Organisations, funds, and one or more clients can be configured within the same structure. Pooled-client visibility
  restricted to that client's share while Odum retains combined internal view. Strategy selection is part of the IM
  commercial path. Next step is a guided reporting-led demo.
- **What to show first:** manager proposition; regulated operating framework; allocator reporting experience;
  same-system reporting credibility; structure choice SMA vs pooled.
- **What not to show unless asked:** too much raw architecture detail; internal catalogue jargon without explanation;
  any page that feels like an engineer's reference manual.
- **Desired next step:** book an IM-flavoured demo focused on reporting, fund structure, allocator visibility, strategy
  selection.
- **Internal handoff:** tag as IM, record likely structure preference, note allocator diligence questions.

### Playbook 2b — DART briefing

- **Audience:** prospect who wants to build, run, or commission strategies on Odum infrastructure.
- **Moment:** deciding whether DART is real platform leverage or just dressed-up consulting.
- **What Odum must prove:** DART is the same production-grade operating system Odum uses internally for proprietary
  trading and IM; distinct commercial entry points exist (not just one monolithic package); the research-to-trading flow
  is unified where the client buys into the deeper pipeline; the system can be partitioned cleanly by client relevance
  without fragmenting the underlying product; observability and control are serious.
- **Experience goal:** create conviction that Odum can support a client's strategy lifecycle from data through live
  operation. The key: do NOT present DART as a separate client shell loosely inspired by Odum's internal stack. The
  point is that it IS the same command-and-control system, with access restricted and curated based on what the client
  actually cares about. Many DART prospects arrive believing they are already largely built; the briefing should help
  them recognise — without feeling cornered — that execution readiness, exchange onboarding, treasury workflows,
  rebalancing, venue coverage, regulatory setup, ongoing operational control are often much less complete than they
  first assume.
- **Walkthrough:** lead with a clear sentence: DART is Odum's platform for data, analytics, research, execution, and
  live operation. More specifically, it is the same underlying system Odum uses to trade, monitor, and control its own
  proprietary and IM activity. The client experience is not a different product; it is a partitioned view of the same
  product, restricted to domains / venues / instruments / strategy families / workflow surfaces most relevant to the
  prospect. Then four commercial anchors: which entry point fits them; how ideas move from research to production where
  relevant; how IP is handled; what the live operating surface looks like. The four catalogues matter more here than in
  IM but should still be framed as decision tools, not inventories. Partitioning by common components plus specific
  domains: category (CeFi/DeFi), strategy family (arb, MM, ML-directional), strategy archetype (continuous /
  event-settled), venue scope, instrument-type scope. Commercially, DART = three practical paths: reporting-only
  visibility (closer to regulatory visibility than true DART); client strategy + downstream integration (client keeps
  strategy generation outside Odum, sends instructions in, uses execution/trading/selected analytics/operating
  surfaces); full DART pipeline (deeper enriched data + research + backtesting + promotion + execution + trading +
  observation). If client wants Odum strategy exposure inside DART, that generally sits inside the fuller DART path. A
  key commercial boundary: DART is not framed as direct raw-data resale — client is buying enriched services built on
  top of underlying data sources, subject to licensing.
- **Key messages:** one platform, not disconnected tools; same core system Odum uses internally, not a diluted
  client-only surface; different DART entry points depending on where client enters the stack and how much of the
  operating model they want Odum to own; client IP and Odum IP distinct and enforceable; research / promotion /
  execution / observation connected where the client buys into that layer; DART sold as enriched platform capability,
  not direct raw-data resale; next step is a live DART demo on staging.
- **What to show first:** platform promise in business terms; same-system credibility (this is how Odum itself runs and
  controls trading operations); four catalogues as usable coverage, not abstract taxonomy; research-to-trading
  lifecycle; operational observability.
- **What not to show unless asked:** excessive internal state names; technical acronyms without immediate explanation;
  pages that imply the platform is unfinished unless there is a clear reason to show them.
- **Desired next step:** book a DART-flavoured demo matching the likely commercial path — reporting-only visibility /
  client strategy + downstream integration / full DART pipeline. Internal commercial note: for the right prospect,
  especially one already working on a live or near-live strategy, sweet spot may be positioning DART as a practical 3–6
  month path to market with a 1-year commercial commitment as the natural minimum structure. (For internal sales
  handling only — not public copy.)
- **Internal handoff:** capture which use case applies: reporting-only visibility; client strategy + downstream
  integration; full DART pipeline; build-for-client; hybrid; or broader strategic partnership. Before the demo the team
  should be able to define a restriction profile from call notes and strategy documentation — not to hide the breadth of
  Odum's capabilities but to stop the demo from becoming noisy. Capture: strategy live-ness (live / partially built /
  conceptual); whether client wants to keep strategy generation outside Odum; whether they're asking for Odum strategy
  exposure and therefore likely belong in the fuller DART path; execution readiness; exchange onboarding status;
  treasury and collateral workflows; rebalancing logic + venue transfer needs; monitoring and operational control gaps;
  regulatory path needed to go live. Let the prospect gradually recognise what is still missing, rather than feeling
  cross-examined.

### Playbook 2c — Regulatory Umbrella briefing

- **Audience:** prospect who wants regulated coverage without pursuing direct authorisation on their own timeline.
- **Moment:** weighing speed, credibility, scope, supervision risk.
- **What Odum must prove:** the umbrella is real and bounded; Odum understands what is and is not covered; supervision
  is meaningful; reporting and control are institutionally credible; the client is plugging into the same reporting
  setup Odum uses itself, not a parallel simplified layer.
- **Experience goal:** give the prospect enough clarity to take the umbrella route seriously as an operating model, not
  just a shortcut.
- **Walkthrough:** open with the commercial truth — Odum provides a regulated framework that lets the client operate
  within defined scope under Odum's permissions and oversight. That framework plugs into the same client-reporting setup
  Odum uses itself; umbrella prospect enters a real operating structure built around orgs / funds / clients. Post-demo,
  client can choose between pooled and SMA; that choice affects their own client accounting and reporting. Then through:
  what the umbrella is / what is covered and what is not / what Odum provides operationally / what the reporting and
  audit experience looks like. Should feel sober and concrete.
- **Key messages:** coverage is specific, not vague; compliance, MLRO, and supervision are part of the operating model;
  the same reporting infrastructure supports regulatory and investor outcomes (same core setup as Odum uses internally);
  orgs / funds / clients structure; pooled vs SMA is a real operating choice; next step is a reporting-led demo framed
  around regulated operation.
- **What to show first:** scope clarity; supervision model; client reporting and audit trail; same-system reporting
  credibility; structure choice where relevant.
- **What not to show unless asked:** wording that sounds casual or overly promotional; unnecessary product sprawl;
  unbounded permissions claims.
- **Desired next step:** book a regulatory demo focused on reporting, structure, scope, oversight, and the
  pooled-versus-SMA decision.
- **Internal handoff:** record target activity, likely operating model, urgency, scope edge cases for compliance review.

### Playbook 3 — Warm-prospect demo on staging

- **Audience:** prospect who has had multiple conversations, consumed the briefings, ready to see the product in action.
- **Moment:** late middle of funnel; testing whether the product experience matches the commercial narrative.
- **What Odum must prove:** the product is real; the product is controlled; the demo is a restriction profile over the
  same underlying system Odum uses internally; the product can be sliced to their use case without feeling fragmented;
  the demo feels intentional, not improvised.
- **Experience goal:** deliver a guided, confidence-building demo that shows exactly what matters for this prospect and
  nothing distracting. By this stage the aim is not to overwhelm; it is to confirm the suspicion that Odum can fill the
  parts of the operating stack the prospect has not fully solved, while making the overall setup feel tangible, visible,
  and achievable.
- **Walkthrough:** staging experience should feel provisioned, curated, purposeful. Three demo flavours: Reg Umbrella /
  IM / DART. Reg Umbrella and IM = one shared reporting-led product family with two narrative lenses; both on same
  client-reporting setup + same org/fund/client structure; main difference is what the external client is meant to see
  and decide. DART is not a separate product — same underlying operating system seen through a different restriction
  profile and different set of relevant surfaces. Within DART, separate commercial path from demo mode. Commercial paths
  (3): reporting-only visibility / client strategy + downstream integration / full DART pipeline. On top, two high-level
  demo anchor modes: broader-platform demo (full platform except for extra restrictions already judged irrelevant after
  sales call); turbo demo (narrower visible surface to what client can realistically interact with without building into
  Odum's infrastructure). Used well, these modes can be shown side by side or via user toggle.
- **Key messages:** this is not a sandbox free-for-all; experience deliberately sliced to client's likely commercial
  path and interests; the client is seeing a partitioned version of the same system Odum uses internally; for IM/Reg the
  same reporting core + entity structure as Odum uses itself; for DART, commercial path + demo mode + production
  restrictions should be chosen deliberately rather than conflated; what is locked still supports the commercial story
  if presented properly; the goal is commitment, not exploration for its own sake.
- **What to show first:** relevant unlocked surface; clear service scope; credible lock states where other services
  exist but are not part of today's package.
- **What not to show unless asked:** admin clutter; unfinished routes; internal implementation logic;
  hidden-versus-locked inconsistency.
- **Desired next step:** commit to paid onboarding; request a narrower follow-up demo with adjusted entitlements; or
  request a comparison between the base visible package and the next layer of capability.
- **Internal handoff:** provisioning, entitlement setup, welcome email, post-demo follow-up attached to the playbook
  rather than handled ad hoc. Restriction profiles configurable from pre-demo call feedback, strategy documents, and
  expressed domains of interest. Each demo prospect carries a live account brief covering what they say is already
  built; what likely still is not; strategy style + family + archetype; venue / instrument needs; treasury / rebalancing
  pain; regulatory needs; objections; non-compete; fit for reporting-only vs signals-only vs full pipeline; fit for
  broader-platform vs turbo demo mode; what the next demo should prove.

### Playbook 3a — Regulatory Umbrella demo

- **Audience:** warm prospect considering operating under Odum's regulated umbrella.
- **Moment:** wants proof of regulatory seriousness, reporting quality, operational structure.
- **What Odum must prove:** umbrella is operationally real; reporting robust enough for regulatory + investor needs;
  structure choices understood; Odum can supervise without creating chaos; prospect is plugging into the same reporting
  setup + entity structure Odum uses itself.
- **Experience goal:** make prospect feel Odum has already built the reporting and governance spine they would otherwise
  assemble themselves. Key nuance: this is not a polished demo shell — it is the same reporting-led structure Odum uses
  internally, shown through the lens of a regulated client relationship.
- **Walkthrough:** lead into a dashboard where Reports is the primary unlocked service and the rest of the platform is
  visible but clearly not part of today's package. From the start, make clear the reporting path is built on the same
  org / fund / client structure Odum uses itself. One or more clients can sit within that structure. In Reg Umbrella,
  demo shows available structure options while the actual pooled-vs-SMA choice is a post-demo operating decision. Guide
  through: reporting overview → available structure options → fund setup → client setup → key reporting tabs →
  regulatory and audit views.
- **Key messages:** the plumbing already exists; built for regulated operation, not just performance display; pooled vs
  SMA is a real operating choice made after the demo; that choice changes downstream client accounting / splits /
  reporting control; Odum provides the oversight layer; entity and reporting setup is the same core structure Odum uses
  internally.
- **What to show first:** reports surface; regulatory reporting tabs; audit + reconciliation confidence points;
  same-system reporting credibility.
- **What not to show unless asked:** broader DART surfaces; speculative platform upsell too early; any route that makes
  the umbrella experience feel secondary.
- **Desired next step:** progress to commercial scoping, compliance fit review, production onboarding.
- **Internal handoff:** compliance + sales jointly review scope, structure, any extra surfaces requested during the
  demo.

### Playbook 3b — Investment Management demo

- **Audience:** warm allocator or mandate prospect considering allocating capital to Odum-managed strategies.
- **Moment:** wants to see what the allocator experience actually looks like.
- **What Odum must prove:** reporting experience is institutional; operating model is mature; structure choice clear;
  Odum feels like a manager, not a software experiment; allocator is seeing the same reporting setup + entity structure
  Odum uses itself.
- **Experience goal:** make the allocator feel Odum can support a serious capital relationship with clear reporting,
  structure, operational discipline. The allocator should feel the reporting path is part of a real operating system
  already used by Odum, not a separate investor-facing layer built only for presentation.
- **Walkthrough:** same product path as Reg Umbrella, but framed through allocator visibility, governance, and manager
  reporting. Same org / fund / client structure with one or more clients. In IM the important distinction is not just
  pooled vs SMA but what each client is allowed to see — in pooled structures, client view restricted to that client's
  share; Odum retains combined internal view. IM path also shows strategy choice is part of the setup. Guide through:
  reporting overview → strategy selection and structure logic → fund setup → client or allocation setup → performance /
  NAV / reconciliation / executive reporting.
- **Key messages:** your allocator window into Odum-managed capital; reporting is part of the core operating model;
  structure affects visibility, economics, operational handling; in pooled structures client sees own share while Odum
  retains combined internal view; strategy selection is part of the IM path; same infrastructure that runs the
  strategies supports the allocator experience; entity + reporting setup same core as Odum's internal.
- **What to show first:** performance + overview tabs; NAV + reconciliation trust markers; executive + investor-facing
  reporting outputs; same-system reporting credibility.
- **What not to show unless asked:** overemphasis on compliance framing (belongs to regulatory lens); broader platform
  surfaces unless commercially relevant.
- **Desired next step:** diligence, mandate structuring, strategy selection, production onboarding path.
- **Internal handoff:** log likely allocation structure, diligence concerns, whether the client needs extra reporting
  depth before commitment.

### Playbook 3c — DART demo

- **Audience:** warm prospect evaluating Odum as the operating platform for their own strategies or for a build-and-run
  engagement.
- **Moment:** wants to see whether the product is a real integrated platform and whether Odum can support serious
  workflows.
- **What Odum must prove:** platform is coherent; coverage broad enough to matter; client can move from idea to
  production inside one operating model; real-time control and observation exist; visible scope is a precise restriction
  of a broader production system, not a stitched-together demo layer.
- **Experience goal:** create the feeling that DART is a serious decision-making and operating environment, not a set of
  disconnected modules. Prospect should understand they are seeing the same command-and-control environment Odum uses
  internally, narrowed to what matters for their likely mandate, strategy set, and operating constraints. For
  DeFi-native prospects especially, the demo should quietly answer the war wounds they already carry — liquidity risk,
  rebalancing risk, moving assets across venues, operational fragility, venue access, treasury control, regulatory
  cover. The prospect should come away feeling Odum can both plug the gaps and make the setup visible without requiring
  a heavy bespoke engineering effort before they can even start.
- **Walkthrough:** DART supports two high-level demo anchor points. Broader-platform demo = full platform except extra
  restrictions already judged irrelevant after initial sales call. Turbo demo = narrower visible surface to what the
  client can realistically interact with without actually building their code into Odum's infrastructure. On top sit
  three practical commercial paths (reporting-only visibility / client strategy + downstream integration / full DART
  pipeline). Demo follows a clean narrative order: data coverage → strategy coverage → model coverage → execution
  coverage → research workflow → promotion workflow → live trading surface → observability. That order tells one story:
  from raw inputs to controlled live operation. Within that story, visible material restricted using same strategy
  taxonomy Odum uses internally — filterable by common components + more specific slices (family, archetype, venue set,
  instrument scope). Pre-demo call notes + strategy documentation are detailed enough to support a tailored restriction
  profile rather than generic presets. In some cases useful to let the client toggle between two user views — base
  package + next layer above — creating healthy sense of what is available without overwhelming. Especially useful when
  client may begin on reporting-only or signals-only but could grow into full pipeline once they see extra operating
  depth.
- **Key messages:** four catalogues = operating inventory; research / promotion / trading / observation connected; same
  core system Odum uses internally for command and control; clients who don't want to give Odum their code can still
  access meaningful parts, especially through reporting-led or downstream-integration paths; clients wanting Odum
  strategy exposure or deeper research/data usage should usually be framed into fuller DART path; DART exposure framed
  as enriched services and workflow capability, NOT direct raw-data resale; IP boundaries explicit; what is visible in
  demo is deliberately selected for trust and clarity, not because the rest does not exist.
- **What to show first:** clean unlocked service surface; commercial path best matching the client; either
  broader-platform or turbo mode (whichever matches); one strong example from each catalogue relevant to prospect's
  expressed interests; research-to-live continuity; real-time observation and control.
- **What not to show unless asked:** broken TCA or obviously incomplete routes; placeholder states that undermine trust;
  too much taxonomy without commercial meaning.
- **Desired next step:** progress to the right DART path (reporting-only visibility / client-strategy downstream / full
  pipeline); scoped pilot; build engagement; follow-up session comparing client's base path against next layer of
  capability.
- **Internal handoff:** capture requested asset classes, required venues, likely entitlement package, any additional
  catalogue visibility needed. Restriction profile is a first-class sales + product artifact — reflects what prospect
  said they care about, what team infers they will need, what is best shown now vs saved for later. For DART
  specifically decide both: commercial path (reporting-only / client-strategy+downstream / full-pipeline); demo mode
  (broader-platform / turbo / both with controlled toggle). For DeFi-native prospects note: liquidity sensitivities;
  rebalancing + treasury pain points; bridge or transfer friction between venues; regulatory cover needs; whether they
  want to keep code outside Odum while still using parts of the platform; whether minimum viable DART path is really a
  client-strategy downstream integration rather than a fuller research-and-data engagement; whether client is actually
  asking for raw data access vs enriched services built on top of licensed inputs; what parts of the stack they believe
  are solved vs what the demo suggests still needs work. The curated demo should be built to answer those points
  indirectly through the product, not by stating them back too bluntly.

### Recommended structural simplification

Nine documents, but they do not all require equal independence.

**Keep distinct:** pb1, pb2, pb2a, pb2b, pb2c, pb3.

**Keep separate in narrative, but not as separate products:** pb3c.

**Treat as shared-core with lens overlays:** pb3a, pb3b. Both sit on the same client-reporting setup Odum uses
internally, with the same underlying org / fund / client structure. Main difference is what the external client is meant
to see and decide.

Operationally maintain: one shared reporting-led demo core; one shared IM/Reg entity-and-reporting structure based on
orgs / funds / clients; one regulatory narrative overlay; one IM narrative overlay; one DART restriction-profile
framework over the same underlying system; three DART commercial paths; two DART demo anchor modes; one internal
building-block pricing model that can drive demo scope, commercial proposals, and production restrictions from the same
underlying registries.

Operationally, the same registries and catalogues should support three separate decisions: what the client is shown in
demo; what the client is sold commercially; what the client is actually restricted to in production. That allows one
infrastructure, one backend, one frontend to support different interaction models without breaking the integrity of the
core system.

### DART commercial structure — clarified

Separate two questions:

1. **Whose strategy is it?** Odum strategy vs client strategy.
2. **How much of the stack are they buying?** Reporting / downstream operating exposure only · Full
   upstream-to-downstream pipeline.

Practical commercial paths:

- **Reporting-only visibility** — really closer to reporting or regulatory visibility than true DART.
- **Client strategy + downstream integration** — client keeps strategy generation outside Odum, sends instructions in,
  uses execution / trading / selected analytics / monitoring to the extent supported.
- **Full DART pipeline** — richer upstream-to-downstream: enriched data services, research, backtesting, promotion,
  execution, trading, observation.

If client wants Odum strategy exposure inside DART, that generally sits inside the full DART pipeline rather than a
separate light package. Internally, different workflow states may still be tracked, but commercially the simpler split
is stronger. The real distinction is not whether an Odum strategy is already inside Odum's system (if it is, it is
inside either way) — it is whether the client is buying only downstream managed operating exposure, or the richer
research / backtest / promote layer as part of the engagement.

### Building-block dimensions for pricing, demo scope, and production restrictions

Same underlying registries support all three: what the client sees in demo; what the client is sold commercially; what
the client is restricted to in production.

Useful internal building-block dimensions: reporting core; regulatory umbrella reporting; IM allocator reporting;
strategy-service entry; instructions integration; research / promote pipeline; execution layer; venue packs; chain
packs; **instrument-type packs** (options, perps, futures, spot); analytics packs; exclusivity / non-compete premium;
custom solution premium.

Instrument types matter as a first-class dimension because they can materially constrain: which strategy families are
relevant; which archetypes are possible; which venues matter; which analytics and attribution surfaces are useful; which
operational and risk workflows need to be shown. Venue, chain, and instrument type should all shape both commercial
packaging and the visible demo restriction profile.

A key commercial boundary: DART is not framed as direct raw-data resale. The client is buying enriched platform and
research services built on top of underlying data sources, subject to licensing and commercial constraints.

### Recommended document and directory separation

(Note: nested under `codex/14-playbooks/` in Stage 2 decisions, not as parallel top-level dirs.)

- **`/experience-playbooks/`** — narrative journey docs for sales, product, leadership, demo owners.
- **`/shared-product-model/`** — core truths reused across experience, commercial packaging, demo, and production
  (shared reporting core, org-fund-client entity model, same-system principle, strategy origin vs stack depth, venue /
  chain / instrument scope, data licensing boundaries).
- **`/commercial-model/`** — how the business is packaged and sold (DART entry points, IM vs Reg reporting logic,
  building-block packaging, pricing philosophy, fixed vs variable commercials, exclusivity and non-compete).
- **`/demo-controls/`** — how demo scope is decided and configured (restriction profiles, DART demo modes, upsell
  overlays, demo toggle patterns, pre-demo curation rules).
- **`/sales-ops/`** — how prospect context is captured and reused (account-intelligence record, pre-demo discovery
  framework, demo decision matrix, meeting history and interest tracking).
- **`/registry-and-entitlements/`** — registry-driven rules that can later be scriptable (demo visibility rules,
  commercial selection to package mapping, production entitlements, pricing input dimensions, restriction profile
  schema).
- **`/implementation-mapping/`** — bridges between narrative docs and actual product behaviour (route mapping, persona
  and user prototype mapping, demo email and provisioning flow, playbook to QA coverage).

### Operating principle across all directories

Still one infrastructure, one backend, one frontend, one internal monitoring and control layer. The separation is only
about documentation and decision layers, not about splitting the product into separate systems.

### What to fix first

1. Rewrite all intros so they describe the buyer and the commercial moment more clearly.
2. Add "what Odum must prove" to every doc.
3. Add "what not to show unless asked" to every doc.
4. Split narrative playbook language from implementation-only notes.
5. Collapse duplicated pb3a and pb3b UI logic into one shared core and two framing layers.
6. Tighten pb2 and pb2b so they read less like internal architecture notes and more like guided commercial material.
7. Make every playbook end with a single explicit next commitment.

### Suggested naming improvement

Visible document titles should be more human:

- Marketing Journey · Briefings Hub · Investment Management Briefing · DART Briefing · Regulatory Umbrella Briefing ·
  Staging Demo Journey · Regulatory Demo · Investment Management Demo · DART Demo.

That instantly makes the set feel less like engineering inventory and more like a real client-experience system.

### Tone cues from Axis and POD

**Worth borrowing:** restrained headlines instead of shouting; a few concrete proof points rather than too many claims;
clear explanation of how the operating model works; visible trust markers used calmly; navigation that helps a serious
buyer self-sort quickly.

**Not worth borrowing:** waitlist-first posture; copy aimed at a broader or more retail audience than Odum's target;
unfinished or placeholder sections that weaken trust; language that implies the product is more future-facing than
present-tense.

For Odum: serious, understated, specific, and obviously written by people who understand the operational reality of
launching and running trading businesses.
