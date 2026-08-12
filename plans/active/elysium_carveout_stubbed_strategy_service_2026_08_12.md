---
doc_type: plan
title: >-
  Elysium full carve-out — a partly stubbed strategy-service where the orchestration is real and everything beneath it
  is not
summary: >-
  Specification for the full carve-out, which is a POST-EXPANSION task and must not start before the strategy-service
  expansion lands. The organising principle, per operator ruling 2026-08-12: the substantive deliverable is the
  ORCHESTRATION that decides, for the client's strategy types, what can be done — the decision layer and the
  instructions it emits are real, and everything beneath the strategy-decision boundary is static, mock or inert. The
  ten typed interfaces in contracts-platform are KEPT as the disclosed contract with static implementations behind them
  (operator confirmed), so the seam already documented in carveout-engineering.html §04 stands and needs reframing
  rather than rewriting. Withheld as IP: the universe registries and general resolution functions behind UAC, the
  multi-step capital-movement reconciliation across Copper/Ceffu/venues, the execution adapters and algorithms, and the
  capability-wizard restriction graph. All carved artefacts are NEW repositories — no production code is removed or
  stubbed.
status: draft
nature: process
asset_group: [defi]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [elysium, carve-out, disclosure, stubs, commercial-model, capability-wizard]
related:
  [
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
    /codex/14-customer-journeys/commercial-model/carveout-engineering.html,
    /codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md,
    /codex/04-architecture/transfer-architecture.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: client_isolation_and_governance_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role:
drift_direction: none
depends_on: [strategy_service_expansion_overlays_config_and_wizard_2026_08_12]
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12. Operator rulings — UAC cannot be in the carve-out in final form, so its functions
  return statically what the configured Elysium strategies need; the client does not need the post-decision-layer
  dynamics (multi-step capital movement, execution adapters and algorithms); the reconciliation smarts across
  Copper/Ceffu/venues are IP; the ten typed interfaces are KEPT as the disclosed contract with static implementations
  behind them; the substantive deliverable is the orchestration that decides for their strategy types what can be done;
  all of it is NEW repositories with production untouched.
---

# Full carve-out — stubbed beneath the decision layer

> **THIS IS HAPPENING** (operator, 2026-08-12): _"we'll show them the carve-out code. That's happening anyway, so that's
> got to be part of the plan."_ It is a commitment, not a contingency. `status: draft` and `depends_on` the expansion
> plan reflect **sequencing only** — the three real archetypes must be carved from post-expansion behaviour, or their
> static implementations freeze the wrong reality and need redoing. Flip to `active` when the expansion lands.

> **All carved artefacts are NEW repositories.** No production code is removed, stubbed or altered. This plan describes
> what gets _built for transfer_, never a change to the running system.

**The organising principle (operator ruling 2026-08-12).** The carve-out is a **partly stubbed strategy-service**. The
line is the **strategy-decision boundary**:

- **REAL** — the orchestration that decides, for the client's strategy types, what can be done: archetype engines for
  the contracted strategies, the configuration surface that constrains them, the decision logic, and the
  `StrategyInstructionEnvelope` instructions it emits.
- **STATIC, MOCK or INERT** — everything beneath that boundary: how an instruction becomes capital movement, which rail
  it takes, how custody mirroring reconciles, how attribution closes.

The client sees **what is decided and what is emitted**. They do not see **how it is executed or reconciled**.

**Codex SSOTs:** [carveout-engineering.html](/codex/14-customer-journeys/commercial-model/carveout-engineering.html)
§§02–04 · [transfer-architecture](/codex/04-architecture/transfer-architecture.md) ·
[capability-wizard](/codex/09-strategy/architecture-v2/capability-wizard.md) ·
[tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md)

## A. The seam stands — §04 is a REFRAME, not a rewrite

Checked 2026-08-12: `carveout-engineering.html` §04 already states each of the ten interfaces "resolves to a local,
static or mock implementation", that "**no implementation transfers** — contracts, schemas and mocks only; nothing
behind them", and that "static universe and frozen configuration satisfy the universe and config contracts". **That is
already the operator's ruling.** The ten interfaces are KEPT (operator confirmed), so what §04 needs is precision about
_what sits behind each_, not a new structure.

Per-interface resolution to specify. `FeatureProvider` · `PricingService` · `ReferenceDataProvider` · `ExecutionService`
· `PortfolioRiskService` · `TreasuryService` · `ReconciliationService` · `AttributionService` · `ConfigVersionService` ·
`UniverseService`.

- [ ] [AGENT] P1. **Write the per-interface resolution table**: for each of the ten, state exactly what ships in
      Resolution A — a static return, a mock, a documented-inert stub, or a real local reader — and what the client must
      supply or source themselves. **Vagueness here is the whole risk**: a CTO reading §04 will ask what
      `UniverseService` returns, and the honest answer is "the resolved universe for your configured strategies, frozen
      at hand-over" — not the ranking functions that produced it.
- [ ] [AGENT] P1. **Specify `UniverseService` as a frozen resolved universe.** It returns the coin/venue/instrument set
      the configured Elysium strategies resolve to at hand-over date. **Withheld:** `rank_top_n_by_adv`, the ADV corpus
      reader, the candidate pools, and the eligibility filters that produced it. They get the answer, not the resolver.
- [ ] [AGENT] P1. **Specify `ConfigVersionService` as frozen configuration** — the instance configs as configured, with
      the param schema for those archetypes only. **Withheld:** `PARAM_SCHEMA_REGISTRY` for the other archetypes and the
      capability-manifest restriction graph.
- [ ] [AGENT] P1. **Specify `TreasuryService` and `ReconciliationService` as inert with documented extension points.**
      This is where the newest IP sits: the Copper/Ceffu mirrored-custody model, the per-client funding-route graph and
      the persisted multi-hop `TransferRoute` (see
      [transfer-architecture](/codex/04-architecture/transfer-architecture.md) rulings 1–4). `request_transfer()`
      accepts and acknowledges; it does not route.
- [ ] [AGENT] P2. **Specify `ExecutionService` as basic routing only.** The carved package's `execution-basic` and
      `adapters-lite` give order placement against a venue API. **Withheld:** execution algorithms, SOR, the
      venue-capability registry and the transfer rails.
- [ ] [AGENT] P2. **Specify `PortfolioRiskService` local guard-rails vs withheld platform risk.** `risk-guards-local`
      gives the local circuit breakers the strategy needs to be safe standalone; cross-client portfolio risk and
      governance stay platform-side.

## A2. Archetype scope — THREE real, the rest shipped as stubs (operator ruling 2026-08-12)

**Only the DeFi-relevant archetypes carry real implementations**, plus dispersion so the client can see how an expanded
strategy correlates against the contracted pair:

| Archetype                  | In the carve-out                                                       | Why                                                                                                         |
| -------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `CARRY_BASIS_PERP`         | **REAL**                                                               | Contracted                                                                                                  |
| `CARRY_STAKED_BASIS`       | **REAL**                                                               | Contracted                                                                                                  |
| `CARRY_FUNDING_DISPERSION` | **REAL**                                                               | Shown deliberately so they can see how an expanded, cross-sectional strategy relates to the contracted pair |
| **All other enum members** | **STUB** — signature, docstring, archetype identity; no decision logic | The **universe of archetypes is disclosed; the mechanisms are not**                                         |

**This is a disclosure design, not a shortcut.** Shipping the full enum as stubs shows the client the real breadth of
the platform — every family, every archetype name — while the alpha logic transfers for three only. Breadth is visible;
mechanism is withheld. It also happens to align with the existing estate: **28 of 60 archetypes are already unreachable
in production** (Elysium plan § H.12), so stubbing the remainder is continuing a pattern rather than inventing one.

- [ ] [AGENT] P1. **Define one stub shape and apply it uniformly.** Each stub carries its archetype identity, family,
      param schema reference and docstring, and raises or returns inert on tick. **It must be unmistakably a stub** — a
      stub that looks like a thin implementation invites a bug report or, worse, an assumption that the strategy is
      runnable.
- [ ] [AGENT] P1. **Stub the internal code the non-carved archetypes depend on**, not just the engines: their
      target-universe builders, rank allocators, catalogue entries and archetype-specific helpers. The import closure
      must still resolve — `contracts-platform` is derived as an import closure over the tier graph, so a dangling
      reference breaks the package build rather than degrading gracefully.
- [ ] [AGENT] P2. **Keep the enum whole.** Do NOT narrow `StrategyArchetype` to the three — the full enum with stubs is
      the point. This supersedes the earlier instinct in § B to narrow it; the correct fix for "don't hit `KeyError` on
      an advertised name" is a stub that fails informatively, saying this archetype is not part of this package.
- [ ] [AGENT] P2. **Verify the three real archetypes' dependency closure is genuinely carvable** — they pull the rank
      allocators, the collateral eligibility filters and the ADV universe resolver, and § A withholds the last of those.
      Confirm the frozen-universe substitution actually satisfies all three engines before committing to the package
      boundary.

## B. What the expansion adds, and therefore what the carve-out must account for

The expansion plan changes what "real" means at the decision boundary, so the carve-out inherits it.

- [ ] [AGENT] P1. **Decide the resolution for each of the four book-level overlays.** Rank-buffer is archetype-layer so
      it carves with the engine. **Beta-hedge, vol-target and the no-trade band are cross-archetype book-level** — so
      either they carve (and the client gets a working risk overlay) or they are `PortfolioRiskService` stubs (and the
      carved strategy runs un-overlaid, materially different risk). **This is the single most consequential carve-out
      decision** and it must be explicit, because the overlays are what make the research risk profile real.
- [ ] [AGENT] P2. **Stub the capability wizard.** It lives in strategy-service, and its backing restriction graph is
      exactly the reconciliation IP withheld. Carve the _resolved_ config, not the form that generates it.
- [ ] [AGENT] P2. **Account for archetype reachability.** Only the contracted archetypes carve. The other 50-odd enum
      members must not appear as dead names — either the carved enum is narrowed to what ships, or the unreachable ones
      are visibly marked, so the client's engineer does not hit `KeyError` on a name the code advertises.

## C. Artefact alignment — reality, present tense, no roadmap voice

Operator instruction: the artefacts are the **union of code and codex**, describe **post-plan reality in the present
tense**, carry **no "will be"**, and are **not salesy**. State what the full picture contains and what a carve-out
stubs; the client draws their own conclusion about the middle.

**The framing target, stated precisely because it is easy to get wrong** (operator, 2026-08-12): the artefact should
leave the client understanding that _"it probably doesn't make sense to take the carve-out because of the reduced
implementations"_ — **and it must reach that conclusion through completeness, not advocacy.** The distinction that keeps
it honest:

- **Do** state, per capability, what the hosted form runs and what the carved form resolves to. Ten interfaces resolving
  to static returns and inert stubs, three archetypes real out of the full enum, no execution algorithms, no transfer
  routing — laid out plainly, that speaks for itself.
- **Do NOT** write a recommendation, a comparison verdict, a "you would be giving up…", or any sentence whose subject is
  the client's decision. **The moment we argue for a conclusion, a reader starts discounting the facts** — and rev 1.0
  of `carveout-engineering.html` was rejected for exactly that register.

The reduced implementation is a fact about the package. Let the fact do the work.

- [ ] [AGENT] P1. **Reframe `carveout-engineering.html` §04** with the per-interface resolution table from § A. Keep the
      seam, the ship-form taxonomy and the reversibility property — they are accurate and they are what make the
      document useful to a CTO.
- [ ] [AGENT] P1. **Ensure the full-picture surface is represented across all three artefacts** so the client can see
      what the hosted form contains: the mirrored-custody routing, the funding-route graph, the capability wizard and
      restriction graph, the ADV-ranked dynamic universe, the rank-allocator weighting layer, the book-level overlays,
      venue and instrument capabilities. **Woven into the relevant sections, never stacked in one "what you don't get"
      block** — a loss-list invites argument, a described capability invites integration planning. That framing already
      fixed rev 1.0 of this document.
- [ ] [AGENT] P2. **No performance figure anywhere until the overlays land.** The research Sharpe belongs to the
      8-overlay book; production runs 2 (Elysium plan § H.16). This is the one hard prohibition on the artefacts.
- [ ] [AGENT] P2. **Cross-check the five older Elysium docs** in `commercial-model/` that this session never reviewed —
      `ODUM_Elysium_Phase2_Update_2026-07-24.html`, `elysium-remaining-work-appendix-2026-07-24.md`,
      `elysium-delay-letter-2026-07-20.md`, `elysium-account-trajectory-2026-05-14.md`,
      `elysium-managed-sla-2026-05-14.md` — against everything established since. Any of them may contradict the
      two-custodian model, the archetype counts or the carve-out scope.

## Progress Log

- **2026-08-12** — Authored on operator instruction, `status: draft` and `depends_on` the expansion plan because
  assembling a carve-out from pre-expansion behaviour would freeze the wrong reality into the static implementations.
  **Useful finding while specifying it: §04 does not need rewriting.** It already states that the ten interfaces resolve
  to local/static/mock implementations and that no implementation transfers — the operator's ruling was already the
  documented design, so the work is precision about what sits behind each interface, not a new structure. Operator
  confirmed the ten interfaces are KEPT as the disclosed contract. Recorded the strategy-decision boundary as the
  organising line: the orchestration that decides what can be done for the client's strategy types is real; everything
  beneath it is static, mock or inert. Flagged the book-level-overlay resolution as the most consequential open
  decision, since it determines whether the carved strategy has a working risk profile or an un-overlaid one.
