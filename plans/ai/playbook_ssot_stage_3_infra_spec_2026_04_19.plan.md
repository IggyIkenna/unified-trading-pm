---
title:
  "Playbook SSOT — Stage 3: infra spec (audit → UAC combo rules → derivation engine → target presentation → refactor
  plan)"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-19
depends_on:
  - playbook_ssot_stage_1_rules
  # Parallelisable with Stage 2; soft-depends on Stage 2 commercial-model structure for Stage 3C inputs.
# Sibling plans:
#   plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md
#   plans/active/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md
supersedes_on_completion:
  - /codex/14-playbooks/roadmap/next-waves.md (Stage 3E becomes the authoritative refactor doc)
---

# Stage 3 — Playbook SSOT infra spec

## Context

Stage 1 locks the rules. Stage 2 rewrites the 40 docs. Stage 3 specs the **infrastructure that makes those docs
operationally true**. Every commitment in the experience playbooks (restriction profiles per persona, building-block
pricing, catalogue parity across 4 dimensions, same-system principle, demo provisioning automation, sales-ops
orchestration) needs corresponding infra. Stage 3's job is to surface exactly what that infra must be — as specs, not as
built code.

Stage 3 is deliberately structured to end with **deliverables a user can SEE** (target-experience presentation with
mermaid diagrams + Playwright-generated UI screenshots) and **ACT on** (concrete refactor plan per building-block gap).

> User directive 2026-04-19: "compare vs audit of the current infra ... finalise with clear refactor doc and target
> experience doc with visuals via a presentation so i can see what the end product post-refactor looks like for the
> building blocks. on the low level details we need UAC registry info for all possible combinations and blockers so that
> we can formulaically derive the costing and the demo universe and the restrictions / access controls across the user
> journey possibilities."

**Scope discipline:** Stage 3 is a spec, not an implementation. It produces: audit docs, registry schemas (YAML
sketches, not the actual UAC PRs), derivation rule docs, a mermaid+screenshot presentation, and a prioritised refactor
plan. The actual building of the restriction-profile engine, pricing engine, catalogue refactors, etc. are separate
follow-up plans that Stage 3E enumerates.

## Decisions locked with user (2026-04-19)

| Decision                                                 | Chosen                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Rationale                                                                                                                           |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Stage 3 has 5 sub-phases                                 | 3A audit / 3B UAC combo rules / 3C derivation engine / 3D target presentation / 3E refactor plan                                                                                                                                                                                                                                                                                                                                                                                                                                                              | User directive; each phase has distinct deliverable                                                                                 |
| UAC combo rules are formulaic, not enumerative           | Dimension tables + blocker predicates + derivation formulas, not explicit full cartesian product                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Combo space is thousands; formulas stay maintainable                                                                                |
| Blocker rules derived from strategy-service code         | Each archetype in `strategy-service/engine/strategies/v2/` already declares (category, instrument_type) valid pairs; Stage 3B surfaces these as declarative UAC rules                                                                                                                                                                                                                                                                                                                                                                                         | Nothing invented; extracted from production code                                                                                    |
| One registry, four derivations                           | The same UAC combo registry drives: (a) `cost(combo)`, (b) `demo_universe(persona, flavour)`, (c) `prod_restrictions(client, package)`, (d) `access_control(user, route, item)`                                                                                                                                                                                                                                                                                                                                                                               | Architectural payoff of Stage 3C — one source feeds 4 outputs                                                                       |
| Visual presentation format                               | Mermaid + Playwright-generated UI screenshots (option 2 from prior scoping)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Mermaid covers flow/registry/cost diagrams; Playwright covers real UI state comparisons. HTML reveal.js deck is out of scope for v1 |
| Refactor plan supersedes roadmap/next-waves.md           | Stage 3E is authoritative post-completion; old roadmap file gets marked superseded                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Avoids dual SSOT                                                                                                                    |
| Audit extension                                          | Re-use the static audit from the foamy-mango plan (177 pages, 4 broken hrefs, nav-config bottlenecks, 10 duplicate clusters) and EXTEND with UAC registry gaps + service-SSOT catalogue gaps + entitlement/auth audit + demo-provisioning audit                                                                                                                                                                                                                                                                                                               | Don't redo work; augment                                                                                                            |
| Internal cost info                                       | Pricing-engine spec lists internal cost dimension but does NOT populate numbers; numbers remain codex-private and flow in from Odum finance outside this plan                                                                                                                                                                                                                                                                                                                                                                                                 | Matches Stage 2 pricing doc treatment                                                                                               |
| Pricing spec owns the 2-tier commercial logic            | Tier A cost-plus (variable, thin margin, 12mo min, no upfront) + Tier B fixed upfront+monthly. Per-block tier is client-mixable. Exclusivity/custom premiums Tier B only                                                                                                                                                                                                                                                                                                                                                                                      | User directive 2026-04-19                                                                                                           |
| Strategy-code as hard taxonomy source                    | strategy-service `engine/strategies/v2/` source is authoritative for valid (category × instrument_type × venue) combos. Stage 3B reads the code; UAC combo-rules doc extracts it.                                                                                                                                                                                                                                                                                                                                                                             | User directive 2026-04-19                                                                                                           |
| **Lifecycle phase as orthogonal dimension (2026-04-19)** | Same-system principle (rule 03) expanded: research / paper / live are a **phase** dimension distinct from maturity. A LIVE_ALLOCATED slot can be viewed in any phase — same UI components, same metric-generation infra, different data-source bindings. Stage 3B adds `lifecycle_phase ∈ {research, paper, live}` as a named dimension; Stage 3C access-control formula becomes `access_control(user, route, item, phase)`; Stage 3E refactor plan includes item "no forked backtest / paper / live UIs — terminal + catalogue + observe are phase-toggled". | Flows from rule 03 sub-claims (b)–(e)                                                                                               |
| **Raw-data resale boundary (cite rule 07)**              | DART is enriched platform services, NOT direct raw-data resale. Stage 3B data-license-tier dimension respects this; Stage 3C pricing derivation uses data-sensitive blocks internally but never exposes raw feeds as a sellable tier. Cross-ref: rule 07 and Stage 2 `shared-core/data-licensing-boundaries.md`.                                                                                                                                                                                                                                              | Commercial/legal guardrail; missed from initial decisions table, added 2026-04-19                                                   |

## Cross-references

- **Stage 1**
  [plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md](playbook_ssot_stage_1_rules_2026_04_19.plan.md) — hard
  dep. Stage 3 uses rules 03 (same-system), 04 (DART commercial axes), 05 (building-blocks), 07 (data licensing), 08
  (pricing principles) extensively.
- **Stage 2**
  [plans/active/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md](playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
  — soft dep. Stage 3C derivation engine reads `commercial-model/pricing-building-blocks.md` structure; Stage 3D
  presentation references experience playbooks. 3A and 3B can run before Stage 2 completes.
- **Parent SSOT work**: [plans/archive/00-MASTER-CICD-PLAN.md](../archive/00-MASTER-CICD-PLAN.md) — static audit lineage
  outputs (177 pages, broken hrefs, duplicate clusters) are Stage 3A's starting material.
- **Existing active plans that will become sub-plans of Stage 3E refactor**:
  - [user_management_merge_2026_03_23.plan.md](user_management_merge_2026_03_23.plan.md) — fund/client/API-key
    provisioning
  - [share_class_architecture_2026_04_01.plan.md](share_class_architecture_2026_04_01.plan.md) — SMA vs Pooled
  - [deployment_topology_and_client_isolation_2026_04_17.plan.md](deployment_topology_and_client_isolation_2026_04_17.plan.md)
    — runtime profiles
  - [defi_demo_e2e_workflow_2026_03_30.plan.md](defi_demo_e2e_workflow_2026_03_30.plan.md) — DART demo workflows
  - [platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md](platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md)
    — strategy family IA
  - [five_space_ia_execution_child_plan_2026_04_17.md](five_space_ia_execution_child_plan_2026_04_17.md) — briefings
    hub, staging Firebase (ticket #12)

## Mandatory read-set

**Stage 1 + 2 outputs:**

1. All 9 files in `codex/14-playbooks/_ssot-rules/`
2. `codex/14-playbooks/experience/` — all 9 experience playbooks (if Stage 2 done; otherwise read Stage 2's plan to
   understand target)
3. `/codex/14-playbooks/shared-core/strategy-origin-vs-stack-depth.md`
4. `/codex/14-playbooks/commercial-model/pricing-building-blocks.md`
5. `/codex/14-playbooks/demo-ops/demo-restriction-profiles.md`

**Hard taxonomy sources — MUST read ALL of these for Stage 3B:** 6. `/codex/09-strategy/README.md` 7.
`/codex/09-strategy/architecture-v2/README.md` 8. `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` —
the existing coverage matrix with 10 block-list groups, primary source for blocker rules 9.
`/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — 12 known UAC gaps 10.
`/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md` 11.
`/codex/09-strategy/architecture-v2/cross-cutting/futures-roll-and-combos.md` 12.
`/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md` 13. `codex/09-strategy/_archived_pre_v2/` — READ FOR HISTORICAL
CONTEXT ONLY; never cite as authoritative 14. `codex/02-venues/` — venue registry, capability matrix, Unity/IBKR
integration specs

**Strategy-service source (authoritative for blocker rules):** 15. `strategy-service/engine/strategies/v2/*.py` — each
archetype's valid-pair declarations 16. `strategy-service/engine/strategies/v2/archetype_build_registry.py` 17.
`strategy-service/availability/` — availability registry

**UAC registries:** 18. `unified-api-contracts/unified_api_contracts/registry/capability_declarations/` — per-venue
capability 19. `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py` —
CHAIN_RPC_TEMPLATES 20. `unified-api-contracts/unified_api_contracts/strategy_availability/` — Phase 10.5 strategy
availability 21. `unified-api-contracts/unified_api_contracts/canonical/domain/` — canonical schemas 22.
`unified-api-contracts/unified_api_contracts/external/{source}/` — per-source normalisers

**Current UI (for audit + screenshots):** 23. `unified-trading-system-ui/lib/config/auth.ts` — entitlement
definitions 24. `unified-trading-system-ui/lib/auth/personas.ts` — 8 demo personas 25.
`unified-trading-system-ui/components/shell/lifecycle-nav.tsx` — entitlement-to-route gate 26.
`unified-trading-system-ui/components/shell/service-tabs.tsx` + `spaces-nav-sections.tsx` — nav SSOT

**Project rules:** 27. `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` 28.
`unified-trading-pm/plans/PLAN_FORMAT.md`

## Out of scope (explicit)

- Actually building the restriction-profile engine, pricing engine, or catalogue refactors — Stage 3 specs them;
  separate follow-up plans build them.
- Real cost numbers (internal or external) — Stage 3 spec'd the structure; numbers flow from Odum finance outside this
  plan.
- Touching UAC code — Stage 3B writes a YAML schema sketch that the actual UAC PR will implement. The UAC PR is a
  separate follow-up.
- Implementing the HTML slide deck via reveal.js — v1 uses markdown + mermaid + Playwright screenshots only.
- Any `plans/active/` archival — Stage 3E supersedes `roadmap/next-waves.md`, but archival is manual post-completion.

## Phase breakdown

### Phase 3A — Current-infra audit (extends the static audit)

Starting material: the static audit from the foamy-mango plan. Extend with UAC + service SSOT + entitlement +
demo-provisioning gaps.

- [ ] [AGENT] P0. Create `codex/14-playbooks/infra-spec/` dir.
- [ ] [AGENT] P0. `infra-spec/stage-3a-current-infra-audit.md` — compile current state across: UI page triage (reuse
      from `page-triage/triage-matrix.md`), nav-config state, broken hrefs (now 4 shipped, 5 probable — verify with
      grep), 4 catalogue surfaces (Strategy ✅, Data partial, ML partial, Exec fragmented), UAC registry gaps (cite
      `uac-registry-gaps.md` 12 items), entitlement gate (lifecycle-nav.tsx hardcoded map), demo-provisioning state (no
      staging Firebase, demo provider only, 5+3 personas), per-client API key state (not issued today), org-scoped JWT
      claims (org_id only, no fund_id/client_id).
- [ ] [AGENT] P0. Audit each building-block dimension from rule 05 against current state: does it exist in UAC? In a
      service? In the UI? For each of 13 blocks, produce a 3-column table (Exists-in / Gap / Blocker).
- [ ] [AGENT] P0. Run
      `grep -rE 'href=["\x27]/[^"\x27]*["\x27]' unified-trading-system-ui/app unified-trading-system-ui/components unified-trading-system-ui/lib` +
      cross-ref against `app/**/page.tsx` registry to re-verify broken-href list. Compare against
      `page-triage/broken-links.md`.

### Phase 3B — UAC combo rules (formulaic)

- [ ] [AGENT] P0. `infra-spec/stage-3b-uac-combo-rules.md` — declarative rule doc covering:
  - Dimension tables (one per building-block dim): category (CEFI / TRADFI / DEFI / SPORTS / PREDICTION), venue (from
    `02-venues/`), chain (from UAC CHAIN_RPC_TEMPLATES), instrument_type (spot / perp / dated-future / option /
    sports-fixture / prediction-market / ...), strategy_archetype (18 from v2), feature_group, model_family, exec_algo,
    entitlement, lock_state (PUBLIC/IM_RESERVED/CLIENT_EXCLUSIVE/RETIRED), maturity (8 stages: CODE_NOT_WRITTEN →
    LIVE_ALLOCATED), **lifecycle_phase (research / paper / live — orthogonal to maturity, per rule 03)**, org_scope,
    fund_structure (Pooled/SMA), data_license_tier (retail-ok / institutional-only / odum-proprietary),
    **instruction_schema_fit (signals-only / client-strategy+downstream / full-pipeline — per rule 10)**
  - Blocker predicates: read `strategy-service/engine/strategies/v2/*.py` for each archetype's valid_pairs; extend
    `category-instrument-coverage.md`'s 10 block-list groups into a full predicate list. Each blocker has: name,
    predicate (pseudo-code), reason (licensing / venue-unsupported / regulatory / technical), evidence (cite source
    file + line)
  - Valid-combo derivation formula (pseudo-code):
    ```
    valid_strategies(venue, instrument_type) =
      { archetype : (venue.category, instrument_type) ∈ archetype.valid_pairs
                  ∧ venue ∈ archetype.supported_venues
                  ∧ ¬ blocked(archetype, venue, instrument_type) }
    ```
- [ ] [AGENT] P0. `infra-spec/stage-3b-combo-rules-schema.yaml` — YAML sketch of the registry structure the actual UAC
      PR will implement. Dimensions + predicates + derivations + example rows. This is the spec the Stage 3E follow-up
      plan "UAC combo registry" builds.
- [ ] [AGENT] P0. Cross-reference: every blocker rule in 3b doc cites either a strategy-service file path OR
      `category-instrument-coverage.md` section OR `02-venues/` capability constraint.
- [ ] [AGENT] P0. `infra-spec/stage-3b-instruction-schema-contract.md` — **ADDED 2026-04-19** per rule 10. Define the
      external-facing instruction-schema contract that a `(Client, downstream-integration)` prospect integrates against:
      required fields, optional fields, unsupported shapes, validation rules (what Odum execution rejects), lifecycle
      semantics (replace/cancel/amend), compatibility rules by venue / instrument_type / execution_mode (some venues
      don't support some instruction shapes — surface the mapping). This is the spec the Stage 3E "instruction-schema
      validation service" follow-up plan implements.
- [ ] [AGENT] P0. `infra-spec/stage-3b-downstream-analytics-capability-matrix.md` — **ADDED 2026-04-19**. Matrix:
      analytics capability × instruction_schema_fit. Rows = analytics (P&L attribution depth, execution alpha
      measurement, regime-conditional reporting, strategy-health metrics, promote-pipeline readiness metrics,
      research-vs-live delta, etc.). Columns = integration modes (signals-only / client-strategy+downstream /
      full-pipeline). Cell = supported / partial / not-available, with a 1-line reason citing why (e.g. "not available:
      requires upstream research lineage that signals-only integration does not provide"). This matrix drives the pb2b
      fit-check content AND the signals-only client's realistic feature expectations.

### Phase 3C — Derivation engine (one registry → four outputs)

- [ ] [AGENT] P0. `infra-spec/stage-3c-derivation-engine.md` — four formulas, one registry:
  ```
  combo(dimensions)               = {d : d ∈ dimensions ∧ ¬ blocked(d)}
  cost(combo, tier)               = Σ block_price(d, tier) + premium(combo)   # tier ∈ {internal, tier-A cost-plus, tier-B fixed}
  demo_universe(persona, flavour) = combos ∩ demo_restriction_profile(persona, flavour)
  prod_restrictions(client, pkg)  = combos ∩ paid_entitlements(client, pkg)
  access_control(user, route, x, phase)
                                   = visible(user, combo(x)) ∧ phase ∈ allowed_phases(user.entitlements)
                                                                                 # from rule 03 same-system (phase orthogonal to maturity) + rule 06 show/don't-show
  ```
  Note the **phase-aware** access control: the same `combo(x)` is visible or not depending on whether the user is
  entitled to see it in research / paper / live context. A LIVE_ALLOCATED strategy is visible in research phase to a
  researcher persona, in paper phase to a QA persona, and in live phase to a trader persona — same underlying combo,
  phase-gated view. For each formula: inputs, outputs, worked example, which service owns the computation (backend
  service name + endpoint), UI consumption pattern.
- [ ] [AGENT] P0. Identify the single service that should own the derivation engine. Candidates: extend
      `strategy-service/availability/`, or a new `restriction-profile-service`. Pro/con per option + recommendation.
- [ ] [AGENT] P0. Define the 3 input feeds (dimensions + blocker rules from 3B, building-block prices from Stage 2
      `pricing-building-blocks.md`, demo restriction profiles from Stage 2 `demo-ops/demo-restriction-profiles.md`) and
      the 4 output consumers (billing, demo-provisioning, production entitlement gate, UI visibility filter).
- [ ] [AGENT] P0. **Instruction-integration-depth pricing dimension (per rule 10).** Extend `cost(combo, tier)` to treat
      integration depth as a modifier inside building-blocks 5 (instructions integration) and 7 (execution layer).
      Define depth levels: basic-instruction-integration / richer-execution-constraints / custom-allocator-handling.
      Each level uplifts the block price per rule 08. Cross-ref: rule 10, rule 08 §Building-block dimensions. Write into
      `stage-3c-derivation-engine.md` as a named extension to the cost formula.

### Phase 3D — Target-experience presentation (visuals)

Two artefact types: mermaid diagrams (lives in markdown) + Playwright-generated screenshots (generated by a new ad-hoc
test).

- [ ] [AGENT] P0. Create `codex/14-playbooks/presentations/` dir.
- [ ] [AGENT] P0. `presentations/target-experience-post-refactor.md` — markdown slide-deck structure:
  - Slide 1: cover + user-directive quote
  - Slide 2: the layered architecture (mermaid graph — rules → experience → shared-core → commercial → demo-ops → infra)
  - Slide 3: the 4-catalogue parity model (mermaid)
  - Slide 4: DART 2-axis commercial model (mermaid matrix)
  - Slide 5: building-block dimensions (mermaid)
  - Slide 6: the 1-registry-4-derivations engine (mermaid flow)
  - Slide 7: cost composition worked example per tier (mermaid stacked)
  - Slide 8: demo restriction profile per persona (mermaid — prospect-reg / prospect-im / prospect-dart / admin)
  - Slide 9: same-system partitioning (mermaid)
  - Slide 10: before/after page-triage counts (mermaid bar)
  - Slides 11–14: Playwright screenshots — homepage (pb1), briefings-hub (pb2), services-portal per prospect persona
    (pb3a, pb3b, pb3c)
  - Slide 15: the 3 internal one-liners + one-paragraph expansions (from Stage 1 rule 09)
  - Slide 16: next-steps — which Stage 3E refactor items unlock which experience playbook
- [ ] [AGENT] P0. Generate Playwright screenshots via a dedicated ad-hoc test under
      `unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts`. For each persona (admin / client-full /
      client-data-only / prospect-im + any others available), screenshot:
  - `/` (anonymous)
  - `/briefings` (post-briefings-auth)
  - `/dashboard` (signed-in per persona)
  - `/services/strategy-catalogue` (signed-in admin)
  - `/services/reports/overview` (signed-in prospect-im) Save to
    `codex/14-playbooks/presentations/screenshots/<persona>-<route>.png` with 1280×720 viewport.
- [ ] [AGENT] P1. Optional: emit an HTML slide-deck via marked.js / reveal.js under
      `presentations/target-experience.html` for easier sharing. Only if time permits — v1 scope is markdown + images.

### Phase 3E — Refactor plan (supersedes roadmap/next-waves.md)

- [ ] [AGENT] P0. `infra-spec/stage-3e-refactor-plan.md` — for each gap from 3A audit, write a refactor item with:
  - Name
  - Current state (1–2 lines)
  - Target state (1–2 lines, cites experience playbook or infra spec doc)
  - Blast radius (services / UI components / UAC registries affected)
  - Blockers (what must happen first)
  - Sequence group (G1 now / G2 next / G3 later)
  - Owner (UI / UAC / user-management-api / strategy-service / ops)
  - Proposed follow-up plan name (so each refactor item becomes its own `plans/active/*.plan.md`) Expected items:
    restriction-profile service/engine (G1), LOCKED-VISIBLE UI service-tile mode (G1), prospect-reg + prospect-dart
    personas (G1), broken-href probable-5 cleanup (G1), **phase-unification refactor — no forked backtest / paper / live
    UIs; terminal + catalogue + observe are phase-toggled over the same component tree (rule 03 sub-claims b–e)** (G1),
    **instruction-schema validation service — external-facing contract from Stage 3B instruction-schema-contract.md;
    validates inbound client instructions against schema + venue/instrument compatibility + licensing; rejects
    non-compliant shapes with actionable errors; feeds pricing-engine with integration-depth signal (rule 10)** (G1),
    fund_id+client_id JWT claims (G2), per-client API key issuance (G2), 4-catalogue parity refactor: Data (G2), ML
    (G2), Execution-Algo (G2) w/ TCA page, staging Firebase provisioning (G2 — already tracked in five_space_ia #12),
    demo-provisioning automation (G2), account-intelligence-record CRM (G3), pricing-engine service (G3),
    pricing-numbers population from finance (G3 — non-codex), briefings-content CMS migration (G3).
- [ ] [AGENT] P0. Mark `/codex/14-playbooks/roadmap/next-waves.md` with a superseded-by header pointing to
      `stage-3e-refactor-plan.md`. Do NOT delete.
- [ ] [AGENT] P0. Cross-link every refactor item in 3E to the experience playbook(s) it unblocks (e.g. "prospect-reg
      persona unblocks pb3a demo test coverage").

### Phase 3F — Verification + commit

- [ ] [AGENT] P0. Verify all 3A/3B/3C/3E docs exist and are internally consistent.
- [ ] [AGENT] P0. Verify 3D presentation has all 16 slides + 5+ Playwright screenshots.
- [ ] [AGENT] P0. Every refactor item in 3E has: name, current, target, blast, blockers, group, owner,
      follow-up-plan-name.
- [ ] [AGENT] P0. Every blocker rule in 3B cites a source file.
- [ ] [AGENT] P0. Commit via
      `bash scripts/quickmerge.sh "docs(codex/playbooks): Stage 3 — infra spec (audit + UAC combo + derivation engine + presentation + refactor plan)" --agent --files "codex/14-playbooks/infra-spec/ codex/14-playbooks/presentations/ /codex/14-playbooks/roadmap/next-waves.md unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts"`.

## Critical files

**New (in PM repo):**

- `codex/14-playbooks/infra-spec/` — 4 docs (3a audit, 3b combo rules + YAML schema, 3c derivation engine, 3e refactor
  plan)
- `/codex/14-playbooks/presentations/target-experience-post-refactor.md`
- `codex/14-playbooks/presentations/screenshots/*.png` (5–8 images)

**New (in UI repo):**

- `unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts` — ad-hoc test that generates the screenshots

**Modified:**

- `/codex/14-playbooks/roadmap/next-waves.md` — superseded-by header only

## Execution DAG

```
Stage 1 ✅ + Stage 2 (partial — pricing structure locked) ──┐
                                                            ▼
Phase 3A (audit) ──┐
                   ├──▶ Phase 3B (UAC combo rules) ──┐
                   │                                 ├──▶ Phase 3C (derivation engine) ──┐
                   └─────────────────────────────────┘                                    │
                                                                                          ▼
                                                                                   Phase 3D (presentation)
                                                                                          │
                                                                                          ▼
                                                                                   Phase 3E (refactor plan)
                                                                                          │
                                                                                          ▼
                                                                                   Phase 3F (verify + commit)
                                                                                          │
                                                                                          ▼
                                                             Follow-up plans per refactor item (separate)
```

3A and 3B can start in parallel. 3C blocks on both. 3D can partially start (mermaid diagrams) in parallel with 3C once
dimensions are locked. 3E blocks on 3A + 3B + 3C.

## Verification

1. **Audit completeness**: 3A doc covers all 13 building blocks with Exists/Gap/Blocker columns.
2. **Blocker coverage**: 3B has ≥ 20 blocker rules (10 from category-instrument-coverage + at least 10 more from
   strategy-service code inspection); each cites a source.
3. **Derivation soundness**: 3C's 4 formulas read the same registry; worked examples compile correctly against sample
   combos.
4. **Presentation completeness**: 3D has all 16 slides; Playwright screenshots render at 1280×720; mermaid diagrams
   parse clean.
5. **Refactor plan actionability**: 3E has ≥ 15 items grouped G1/G2/G3; each names a follow-up plan file.
6. **roadmap/next-waves.md superseded**: first line reads `> Superseded by [stage-3e-refactor-plan.md](...)` — content
   preserved but redirect clear.
7. **Cross-link integrity**: every experience playbook referenced in 3D exists post-Stage-2; every follow-up plan name
   in 3E is a valid future filename.

## Handoff

Stage 3 doesn't have a sibling "Stage 4". Its outputs feed:

- Ops + finance (pricing numbers flow into Stage 2's pricing doc from Odum finance post-Stage-2)
- Engineering (each Stage 3E refactor item spawns its own `plans/active/*.plan.md` follow-up with its own agent prompt)
- Sales + leadership (Stage 3D presentation is the end-product-post-refactor view; use for internal alignment + investor
  briefings)

Post-Stage-3, the `14-playbooks/` SSOT is complete. Further work is implementation of the items 3E enumerates.

---

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Stage 3. Can run in PARALLEL with Stage 2
(phases 3A + 3B only); 3C+ blocks on Stage 2 commercial-model/pricing-building-blocks.md structure.**

---

You are executing **Stage 3 of the Playbook SSOT restructure** for the Unified Trading System at Odum Research. Stage 3
is the infra spec — it specifies what engineering must build (or refactor) to make the experience playbooks
operationally true.

### Pre-flight check

Verify Stage 1 merged:

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git log origin/live-defi-rollout --oneline -30 | grep "Stage 1"
ls codex/14-playbooks/_ssot-rules/
```

Stage 2 status check:

```
ls /codex/14-playbooks/commercial-model/pricing-building-blocks.md 2>&1 || echo "Stage 2 not done — you can still run 3A + 3B, but 3C onwards must wait"
```

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 3A through 3F of this plan:
`plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md`

### Read-set (mandatory — all of these for Stage 3B blocker extraction)

1. This plan file
2. Stage 1 + 2 plans (for context)
3. All 9 `_ssot-rules/*.md`
4. Stage 2 outputs if available: `experience/`, `shared-core/strategy-origin-vs-stack-depth.md`,
   `commercial-model/pricing-building-blocks.md`, `demo-ops/demo-restriction-profiles.md`
5. **Hard taxonomy**: all 9 files in `codex/09-strategy/architecture-v2/` (especially `category-instrument-coverage.md`
   and `uac-registry-gaps.md`)
6. `codex/09-strategy/_archived_pre_v2/` — historical only
7. `codex/02-venues/` — all venue capability files
8. `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
9. **strategy-service source**: `strategy-service/engine/strategies/v2/` — grep each `.py` file for valid-pair
   declarations, archetype allowlists, venue allowlists. This is authoritative for Phase 3B blocker rules.
10. `strategy-service/availability/` — Phase 10.5 availability registry
11. **UAC**: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/` +
    `strategy_availability/` + `canonical/domain/`
12. **UI state for audit**: `unified-trading-system-ui/lib/config/auth.ts`, `lib/auth/personas.ts`,
    `components/shell/lifecycle-nav.tsx`, `components/shell/service-tabs.tsx`, `spaces-nav-sections.tsx`,
    `lib/lifecycle-route-mappings.ts`
13. **Existing audit material**: `/codex/14-playbooks/page-triage/triage-matrix.md` + `broken-links.md` +
    `duplicate-clusters.md`
14. **Existing plans that become Stage 3E sub-plans**: user_management_merge, share_class_architecture,
    deployment_topology, defi_demo_e2e, platform_strategy_families, five_space_ia_execution_child_plan

### Deliverables

**New in PM repo:**

- `/codex/14-playbooks/infra-spec/stage-3a-current-infra-audit.md`
- `/codex/14-playbooks/infra-spec/stage-3b-uac-combo-rules.md`
- `codex/14-playbooks/infra-spec/stage-3b-combo-rules-schema.yaml`
- `/codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md`
- `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md`
- `/codex/14-playbooks/presentations/target-experience-post-refactor.md`
- `codex/14-playbooks/presentations/screenshots/*.png` (5+ images)

**New in UI repo:**

- `unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts`

**Modified:**

- `/codex/14-playbooks/roadmap/next-waves.md` (add superseded-by header)

### Commit strategy

Two commits — one per repo.

PM repo:

```
cd unified-trading-pm
bash scripts/quickmerge.sh "docs(codex/playbooks): Stage 3 — infra spec (audit + UAC combo + derivation engine + presentation + refactor plan)" \
  --agent \
  --files "codex/14-playbooks/infra-spec/ codex/14-playbooks/presentations/ /codex/14-playbooks/roadmap/next-waves.md"
```

UI repo:

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "test(playbooks): screenshots spec for presentation assets" \
  --agent \
  --files "tests/e2e/playbooks/screenshots.spec.ts"
```

Run the screenshot spec locally FIRST to generate `*.png` files, then stage those into the PM repo commit. Don't commit
png into UI repo (keep UI repo clean of codex assets).

Playwright invocation:

```
cd unified-trading-system-ui
bash scripts/dev-tiers.sh --tier 0   # ensure UI running at port 3100
npx playwright test tests/e2e/playbooks/screenshots.spec.ts --project=chromium
# copy generated screenshots:
cp test-results/**/*.png ../unified-trading-pm/codex/14-playbooks/presentations/screenshots/
```

Fallback to manual git commit if quickmerge is blocked by unrelated WIP.

### Success criteria

1. ✅ Stage 3A audit covers all 13 building blocks (paste the Exists/Gap/Blocker table in report)
2. ✅ Stage 3B has ≥ 20 blocker rules with source citations (list 5 examples with file:line refs)
3. ✅ Stage 3B YAML schema parses as valid YAML (run
   `python -c "import yaml; yaml.safe_load(open('codex/14-playbooks/infra-spec/stage-3b-combo-rules-schema.yaml'))"`)
4. ✅ Stage 3C's 4 formulas compile against ≥ 3 worked examples each
5. ✅ Stage 3D presentation has 16 slides + ≥ 5 screenshots; paste mermaid diagram syntax for 3 key slides
6. ✅ Stage 3E has ≥ 15 refactor items in G1/G2/G3 grouping
7. ✅ `roadmap/next-waves.md` has superseded-by header
8. ✅ Commit SHAs pushed to `origin/live-defi-rollout` (both repos)

### What NOT to do

- Do NOT actually build the restriction-profile engine, pricing engine, or catalogue refactors. Spec only.
- Do NOT write real cost numbers.
- Do NOT modify UAC code — YAML schema sketch only.
- Do NOT modify `strategy-service/engine/strategies/v2/*.py` — read-only.
- Do NOT delete `roadmap/next-waves.md` — supersede only.
- Do NOT touch any file on `live-defi-rollout` you haven't explicitly created/modified.
- Do NOT use `--dep-branch`.
- Do NOT skip reading `category-instrument-coverage.md` before writing 3B — it's the single richest source for blocker
  rules.

### Report back

- File list per phase with line counts
- Stage 3A's Exists/Gap/Blocker table (13 rows)
- 5 example blocker rules with file:line citations from strategy-service code
- Mermaid syntax for 3 key presentation slides
- Playwright screenshot list (file paths)
- Stage 3E refactor item count per G-group
- 2 commit SHAs (PM + UI) pushed to live-defi-rollout
- Any blockers or gaps flagged for the user
