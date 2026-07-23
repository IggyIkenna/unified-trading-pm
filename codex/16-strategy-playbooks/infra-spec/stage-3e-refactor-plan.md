---
doc_type: codex-ssot
title: Stage 3E — Refactor plan (supersedes roadmap/next-waves.md)
summary: >-
  Authoritative 31-item post-Stage-3 refactor backlog (G1 now ×14 / G2 next ×11 / G3 later ×6) with per-item current →
  target state, blast radius, blockers, dependency graph, and proposed follow-up plan filename; supersedes
  roadmap/next-waves.md. DELTA 2026-05-22: G1 is post-May-23-cutover scope, none shipped yet.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [deployment-api, execution-service, features-service, instruments-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [refactor, ui, uac, strategy, migration, docspec]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/09-strategy/architecture-v2/uac-registry-gaps.md,
  ]
created: 2026-04-20
authoritative_for:
  [Stage 3E post-Stage-3 refactor backlog (G1/G2/G3 items + dependency graph, supersedes roadmap/next-waves.md)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
    /codex/14-customer-journeys/roadmap/next-waves.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Stage 3E — Refactor plan (supersedes roadmap/next-waves.md)

> **Purpose.** The authoritative post-Stage-3 refactor backlog. Every gap surfaced in
> [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) has a refactor item here. Every item names enough
> context that a future author (human or agent) can spawn a follow-up `plans/active/*.md` against it without re-doing
> the Stage 3 analysis.
>
> **Parent plan:**
> [`plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md)
> § Phase 3E.
>
> **Supersedes:** [`../roadmap/next-waves.md`](../../14-customer-journeys/roadmap/next-waves.md) (pointer-only; content
> preserved).
>
> **Reads:**
>
> - [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) — 13 building-block gap table, UAC gap audit,
>   entitlement audit, demo-provisioning audit
> - [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) — 15 dimensions + 22 blocker predicates that each
>   refactor item composes against
> - [`stage-3c-derivation-engine.md`](stage-3c-derivation-engine.md) — 4 formulas the G1 items implement
> - All 10 rules under [`../_ssot-rules/`](../_ssot-rules/)
> - [`../page-triage/`](../page-triage/) — broken-links, duplicate-clusters, triage-matrix

---

## 0. Reading guide

Three execution groups:

- **G1 — now.** Blocks Stage 2 playbook content from being operationally true. Prospects cannot be demoed safely or
  priced correctly until G1 ships.
- **G2 — next.** Unblocks scale and multi-client operations — JWT claims, per-client API keys, catalogue parity. Without
  G2 the platform works for demos but not for growth.
- **G3 — later.** Polish, automation, CRM integration, content CMS. Run without G3 indefinitely.

Each item below has:

| Field                       | Meaning                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------- |
| **Name**                    | Short identifier                                                                        |
| **Current state**           | 1–2 lines — what exists today                                                           |
| **Target state**            | 1–2 lines — what ships                                                                  |
| **Blast radius**            | Services / UI / UAC affected                                                            |
| **Blockers**                | Hard prereqs (must ship before this can)                                                |
| **Group**                   | G1 / G2 / G3                                                                            |
| **Owner**                   | Primary team / service                                                                  |
| **Proposed follow-up plan** | Filename the future `plans/active/<name>.md` will take                                  |
| **Unlocks playbooks**       | Experience playbooks this item enables (per [`../experience/`](../experience/) targets) |

---

## 1. G1 — post-cutover (originally "4–6 weeks from 2026-04-19")

> **[DELTA 2026-05-22]** **Current state:** The G1 items below were written 2026-04-19 with a "4–6 week" target (implied
> ~2026-05-30). As of 2026-05-22 the May-23 DeFi live gate takes precedence; none of the G1 items have shipped yet.
> **Planned delta:** G1 items are post-cutover scope. The derivation engine (Stage 3C) and phase-unification UI refactor
> (1.1) are tracked under `plans/epics/deployment_and_user_management_master.md` (UI) and
> `plans/epics/strategy_master.md` (backend). **Target:** G1 items schedulable once May-23 live DeFi is running ≥7 days.

### 1.1 Phase-unification refactor — no forked research/paper/live UIs

- **Current state.** Separate `/services/research/*`, `/services/trading/terminal`, and `/services/observe/*` surfaces
  render different component trees for the same conceptual data. Lifecycle-route-mappings declare research-only routes
  (`/services/research/ml/overview`, etc.) that duplicate canonical catalogue pages. Five of these are broken
  ([`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) §2.2). No `<PhaseToggle>` component exists; no
  route accepts a `?phase=` query parameter.
- **Target state.** One component tree per concept (catalogue, terminal, positions, reports). Each accepts a
  `phase ∈ {research, paper, live}` prop. Phase rebinds the data source (research → historical binding via
  research-service; paper → live market data + simulated fills via execution-service matching engine; live → live
  fills). No `/research/*` or `/paper/*` top-level route prefixes. `<PhaseToggle>` chip in the app header lets entitled
  users flip phases on the current route. Rule 03 sub-claims (b–e) become mechanically enforced.
- **Blast radius.** 13 UI pages (`/services/trading/terminal`, `/services/reports/*` × 6,
  `/services/strategy-catalogue/*` × 4, `/services/observe/health` × 2) + 3 backend services (strategy-service
  data-binding layer, reports-service, execution-service matching-engine mode flag) + 5 broken hrefs retired (§2.2 of
  3a).
- **Blockers.** `access_control(..., phase)` from [`stage-3c-derivation-engine.md`](stage-3c-derivation-engine.md) §1.5
  must ship first (same G1). No UAC work required — phase is a dimension already declared in
  [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §1.12.
- **Group.** G1
- **Owner.** UI + strategy-service + execution-service
- **Proposed follow-up plan.** `phase_unification_no_forked_uis_2026_05.plan.md`
- **Unlocks playbooks.** pb3b `investment-management-demo.md` (reporting phase=live), pb3c `dart-demo.md` (terminal
  phase toggle demo), pb2b briefing's walkthrough section.

### 1.2 Instruction-schema validation service

- **Current state.** No service validates inbound client instructions against a declared schema. `execution-service`
  accepts whatever shape arrives and fails at execution time. No mapping from rule 10's 8 required fields to a runtime
  validation layer. No rejection codes per
  [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md) §4.
- **Target state.** A service (`instructions-service` extension or new `instruction-validator`) accepts inbound client
  instructions, validates against the
  [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md) schema (8 required fields,
  optional Standard + Rich extensions, venue × instrument × mode compat matrix §6), rejects non-compliant shapes with
  actionable errors (`SCHEMA_VALIDATION_FAILED`, `SCHEMA_OUT_OF_PACKAGE`, `LIFECYCLE_INVALID_TRANSITION`, etc.), and
  emits accepted instructions to execution-service. Feeds pricing-engine with integration-depth signal
  (`basic_instruction_integration` / `richer_execution_constraints` / `custom_allocator_handling`) per rule 10 ×
  rule 08.
- **Blast radius.** 1 new service (or 1 sub-package in `execution-service`), UAC `ClientInstructionSchema` types,
  billing-signal emitter. ~3 UI routes get a new validation-status display (`/services/execution/*`).
- **Blockers.** UAC `ClientInstructionSchema` (new — not in the declared 12 UAC gaps; introduced by rule 10 + Stage 3B
  instruction schema contract). Stage 3B instruction-schema-contract.md (shipped ✅). Stage 3C derivation engine
  (shipped ✅).
- **Group.** G1
- **Owner.** instructions-service / execution-service
- **Proposed follow-up plan.** `instruction_schema_validation_service_2026_05.plan.md`
- **Unlocks playbooks.** pb2b `dart-briefing.md` (signals-only fit-check discipline), pb3c `dart-demo.md` (demo
  walkthrough of the validation surface).

### 1.3 LOCKED-VISIBLE UI service-tile mode

- **Current state.** `isItemAccessible` cascade in
  [`components/shell/lifecycle-nav.tsx:102-113`](../../../../unified-trading-system-ui/components/shell/lifecycle-nav.tsx#L102-L113)
  hides inaccessible routes entirely. No LOCKED-VISIBLE rendering. Demo prospects cannot see surfaces they don't have
  without persona switching. Rule 06 §"LOCKED-VISIBLE vs HIDDEN-ENTIRELY" cannot be honoured.
- **Target state.** `<ServiceTile variant="locked" upgradeHint="...">` component that renders the nav item with a
  padlock chip + tooltip (e.g. "Available in full DART — contact sales"). `access_control(...)` status `locked_visible`
  triggers this rendering instead of hiding. Clicking a locked tile shows a modal with the upgrade path (rule 06
  §"LOCKED-VISIBLE" semantics). Nav layouts updated in `components/shell/lifecycle-nav.tsx`,
  `components/shell/service-tabs.tsx`, `components/shell/spaces-nav-sections.tsx`.
- **Blast radius.** 3 nav components, 1 new `<ServiceTile>` primitive, 1 new `<LockedTileModal>`, 1 new chip primitive
  (extend `components/architecture-v2/`).
- **Blockers.** `access_control(...)` service (same G1 ships). Stage 3C derivation engine (shipped ✅).
- **Group.** G1
- **Owner.** UI
- **Proposed follow-up plan.** `locked_visible_service_tile_2026_05.plan.md`
- **Unlocks playbooks.** pb3c `dart-demo.md` (shows research/promote as locked-visible), pb3a `regulatory-demo.md`
  (shows DART as locked-visible).

### 1.4 Prospect-DART + Prospect-Reg personas

- **Current state.** 5 personas in [`lib/auth/personas.ts`](../../../../unified-trading-system-ui/lib/auth/personas.ts):
  `admin` / `internal-trader` / `client-full` / `client-data-only` / `prospect-im`. No `prospect-dart` for warm-prospect
  DART demos. No `prospect-reg` for Reg Umbrella demos. pb3a + pb3c cannot be Playwright-tested; sales cannot demo
  either path without persona-switching.
- **Target state.** Two new personas:
  - `prospect-dart` — Demo DART Prospect, `org: "demo-dart"`, entitlements scoped to `(Client, downstream)` default
    restriction profile (blocks 1/4/5/7/8/9/10/11, block 6 LOCKED-VISIBLE).
  - `prospect-reg` — Demo Reg Umbrella Prospect, `org: "demo-reg"`, entitlements scoped to Reg Umbrella default (blocks
    1/2/7/8/10).
  - Both added to `lib/auth/personas.ts` and `tests/e2e/playbooks/seed-persona.ts`.
- **Blast radius.** 2 files in UI repo. 0 backend changes (mock-auth-only; real Firebase staging is G2).
- **Blockers.** None — additive.
- **Group.** G1
- **Owner.** UI
- **Proposed follow-up plan.** `demo_personas_prospect_dart_reg_2026_05.plan.md`
- **Unlocks playbooks.** pb3a `regulatory-demo.md`, pb3c `dart-demo.md`, the `warm-prospect-demo.spec.ts` +
  `visibility-slicing.spec.ts` Playwright coverage.

### 1.5 Broken-href probable-5 cleanup (ML Model Catalogue routes)

- **Current state.** 5 hrefs referenced by
  [`lib/lifecycle-route-mappings.ts`](../../../../unified-trading-system-ui/lib/lifecycle-route-mappings.ts) have no
  `page.tsx`:
  - `/services/research/ml/overview`
  - `/services/research/ml/experiments`
  - `/services/research/ml/features`
  - `/services/research/ml/validation`
  - `/services/research/ml/deploy`
- **Target state.** Two paths depending on 1.6 (ML Catalogue refactor): if 1.6 is G2, ship stubs matching the pattern of
  the Phase-3 `/services/execution/tca` stub (landing page + "catalogue refactor pending" notice + deep-link to existing
  partial ML pages). If 1.6 lands G1, these routes are folded into the new canonical ML catalogue structure.
- **Blast radius.** 5 new `page.tsx` files (stub-form) or 5 route renamings (canonical-form, depends on 1.6 timing).
- **Blockers.** Decision on 1.6 timing (G1 vs G2).
- **Group.** G1 (stubs) or G2 (folded into full refactor)
- **Owner.** UI
- **Proposed follow-up plan.** `ml_catalogue_broken_hrefs_cleanup_2026_05.plan.md`
- **Unlocks playbooks.** pb3c `dart-demo.md` (ML research walkthrough is demo-able without 404s).

### 1.6 Derivation engine — ship to `strategy-service/availability/`

- **Current state.** `strategy-service/availability/` has `store.py`, `watchdog.py`, `audience_filters.py`, `events.py`
  (Phase 10.5 shipped 2026-04-19). No `combo.py`, no `pricing/`, no `demo_universe.py`, no `prod_restrictions.py`, no
  `access_control.py`. The four derivation formulas are specified in
  [`stage-3c-derivation-engine.md`](stage-3c-derivation-engine.md) but unimplemented.
- **Target state.** Ship the four sub-modules into `strategy-service/availability/` per the layout in
  [`stage-3c-derivation-engine.md`](stage-3c-derivation-engine.md) §5 (pricing/, combo, demo_universe,
  prod_restrictions, access_control). Expose HTTP surface via new `strategy-service/api/restriction_profile_router.py`.
  Capability-gate `cost(..., tier=internal)`. Cachable (§6 of 3C).
- **Blast radius.** `strategy-service` (1 repo, 1 sub-package), UI `lib/architecture-v2/` gets a client hook, UAC gets a
  `combo_registry.py` loader for the Stage 3B YAML schema.
- **Blockers.** Stage 3B schema landed ✅. Stage 3C spec landed ✅. UAC `ArchetypeCapabilityV2` (UAC gap #1) must be
  shipped for `combo()` to read archetype metadata from UAC instead of hardcoding it.
- **Group.** G1
- **Owner.** strategy-service + UAC
- **Proposed follow-up plan.** `derivation_engine_ship_to_strategy_availability_2026_05.plan.md`
- **Unlocks playbooks.** All playbooks — this is the plumbing for 1.1 / 1.2 / 1.3.

### 1.7 Restriction-profile engine — demo-profile registry + persona overlays

- **Current state.** Demo restriction profiles are described in Stage 2 `demo-ops/demo-restriction-profiles.md` but
  exist only as prose. No runtime registry. UI defaults to hiding anything not in the persona's entitlement array.
- **Target state.** `demo_profile_registry.yaml` fixture shipped to UAC; loaded by
  `strategy-service/availability/demo_universe.py`. Each persona in `personas.ts` gets a `demo_profile_id`;
  `demo_universe(persona, flavour)` reads the profile, overlays flavour adjustments, returns the visibility slice. 3
  flavour values (broader_platform / turbo / deep_dive) declared.
- **Blast radius.** UAC fixture file, strategy-service sub-module, UI demo-context provider.
- **Blockers.** 1.6 (derivation engine ships first), Stage 2 `demo-ops/demo-restriction-profiles.md` (partially in
  flight via Agent D).
- **Group.** G1
- **Owner.** strategy-service + UAC + UI
- **Proposed follow-up plan.** `restriction_profile_engine_demo_registry_2026_05.plan.md`
- **Unlocks playbooks.** pb3a / pb3b / pb3c — the three demo walkthroughs.

### 1.8 UAC `ArchetypeCapabilityV2` (UAC gap #1)

- **Current state.** Archetype metadata (valid_pairs, supported_venues, supported_signal_variants, instrument_schema_fit
  eligibility) is encoded across 18 Python files under `strategy-service/engine/strategies/v2/*.py`. No UAC registry;
  other services cannot read it. Stage 3B's blockers cite the Python files directly.
- **Target state.** `unified_api_contracts.internal.architecture_v2.archetype_capability.ArchetypeCapabilityV2` shipped.
  18 archetype records declared. strategy-service reads its own truth from UAC (not vice-versa). Stage 3C derivation
  engine's `combo()` reads `ArchetypeCapabilityV2` for archetype-to-pair mapping.
- **Blast radius.** UAC (1 new module), strategy-service (18 files lose their inline constants, import from UAC).
- **Blockers.** None — additive.
- **Group.** G1
- **Owner.** UAC + strategy-service
- **Proposed follow-up plan.** `uac_archetype_capability_v2_2026_05.plan.md` (tracks UAC gap #1 from
  [`uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md)).
- **Unlocks playbooks.** Indirectly all — the derivation engine depends on it.

### 1.9 Codex scope registry — per-audience documentation surface

- **Current state.** `codex/` is read-all / write-all to internal readers. No mechanism to surface a subset to external
  audiences. Stage 3B rule 07 requires enriched-service framing externally; today the internal cost column leaks if a
  client-facing doc references codex directly.
- **Target state.** `codex_scope(audience)` derivation: per-audience allow-list of codex paths. External audiences see
  only doc paths tagged `audience: external` in frontmatter. Internal cost leaks blocked via allow-list enforcement.
  Each playbook in `codex/14-customer-journeys/` gets an explicit audience tag.
- **Blast radius.** codex doc build pipeline (adds audience-filtering); no runtime service.
- **Blockers.** None — additive tagging.
- **Group.** G1
- **Owner.** codex / docs pipeline
- **Proposed follow-up plan.** `codex_scope_per_audience_tagging_2026_05.plan.md`
- **Unlocks playbooks.** pb1 `marketing-journey.md` (external codex links in anonymous marketing), pb2b
  `dart-briefing.md` (post-light-auth links into internal-ish codex sections).

### 1.10 Questionnaire-to-configuration flow (2026-04-20 amendment)

- **Current state.** No prospect-facing questionnaire. Sales / ops manually map a prospect's stated interest onto a
  persona. No audit trail, no Firestore record, no `_apply_questionnaire_override` overlay feeding the
  restriction-profile engine. Resolution of a `QuestionnaireResponse` → `RestrictionProfile` happens only in sales
  heads.
- **Target state.** Public `/questionnaire` route in `unified-trading-system-ui` with a 6-axis form (categories,
  instrument_types, venue_scope, strategy_style, service_family [4-value prospect-facing enum], fund_structure). Submit
  writes to Firestore + localStorage fallback. Admin playback surface in `user-management-ui` at `/questionnaires`. UAC
  `QuestionnaireResponse` pydantic schema. Strategy-service endpoint
  `POST /internal/restriction-profile/{persona_id}/resolve` accepts the response body and returns a resolved
  `RestrictionProfile` via `_apply_questionnaire_override` overlay composed on top of `prod_restrictions` (G1.7).
- **Blast radius.** UAC (1 new schema), strategy-service (1 new router + resolve endpoint), unified-trading-system-ui (1
  new public route + form), user-management-ui (1 new admin route + Firestore reader), Firestore security rules
  (questionnaire collection; follow-up plan).
- **Blockers.** G1.7 restriction-profile engine (consumer of resolved profile). G1.11 service-family scope rules
  (constrains the 4-value picker).
- **Group.** G1
- **Owner.** UAC + strategy-service + UI + user-management-ui
- **Proposed follow-up plan.**
  [`refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md`](../../../plans/archive/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md)
  — **SHIPPED 2026-04-20** (UAC `e4a9e72`, strategy-service `429ff53`, ui `ce53f4d`, user-management-ui `93f7a76`).
- **Unlocks playbooks.** pb3a / pb3b / pb3c (questionnaire becomes the entry point to each demo walkthrough); feeds
  account-intelligence-record CRM (G2.11).

### 1.11 Service-family scope rules (rule 12) (2026-04-20 amendment)

- **Current state.** Service-family constraints (which audiences can observe / report / research / promote /
  admin-catalogue) exist as prose in Stage 2 docs. No rule file, no YAML, no UAC function. `access_control()` pre-check
  does not consult scope rules — scope is implicit in persona-level entitlement arrays.
- **Target state.** Rule 12 at `codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.{md,yaml}`
  codifies: observe ∈ {DART}; reporting ∈ {IM, DART-reporting-only, Reg Umbrella}; research / promote ∈ {full-DART};
  strategy-catalogue-admin ∈ {admin, IM-desk}. New UAC function
  `check_service_family_scope(audience, service_family, activity) -> ScopeDecision` consumed as a pre-check inside
  `access_control()` (G1.6). 6-value internal `ServiceFamily` enum
  (`IM | RegUmbrella | DART | DART_reporting_only | admin | IM_desk`) vs 4-value prospect-facing enum
  (`IM | DART | RegUmbrella | combo`) both declared in UAC.
- **Blast radius.** UAC (1 new function + 1 new enum + YAML loader), codex (1 new rule + YAML), strategy-service
  (access_control pre-check wire-in), user-management-ui (picker uses prospect-facing enum), unified-trading-system-ui
  (questionnaire picker).
- **Blockers.** G1.6 derivation engine (access_control is the consumer). G1.9 rule-registry slot 11 already taken by
  codex scope registry → scope rules shipped as rule 12.
- **Group.** G1
- **Owner.** UAC + codex + strategy-service + UI
- **Proposed follow-up plan.**
  [`refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md`](../../../plans/archive/refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md)
  — **SHIPPED 2026-04-20**.
- **Unlocks playbooks.** pb3a / pb3c (hard scope on DART vs Reg Umbrella route access); validates G1.4 persona matrix.

### 1.12 Public-site IA + briefings polish (2026-04-20 amendment)

- **Current state.** 9 public pages (`/`, `/investment-management`, `/platform`, `/regulatory`, `/firm`, `/contact`,
  `/demo`, `/signup`, `/login`) each render different headers. Briefings pages use ad-hoc hero formatting. Information
  architecture drift — rule 02 tone and rule 06 LOCKED-VISIBLE guidance not surfaced consistently.
- **Target state.** Single `<SiteHeader>` component adopted across all 9 public pages. New `<BriefingHero>` component
  applies cut-through-noise formatting to `/briefings/*` sub-pages. UI-only refactor; no auth/routing changes. Follows
  rule 02 tone + rule 06 visibility without touching entitlements or data.
- **Blast radius.** 9 public page components, 2 new shared components (`<SiteHeader>`, `<BriefingHero>`), briefings
  hub + sub-pages.
- **Blockers.** None — UI-only, additive.
- **Group.** G1
- **Owner.** UI
- **Proposed follow-up plan.**
  [`refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md`](../../../plans/archive/refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md)
  — **SHIPPED 2026-04-20**.
- **Unlocks playbooks.** pb1 `marketing-journey.md` (consistent public-site framing), pb2b `dart-briefing.md` +
  `regulatory-umbrella-briefing.md` (briefing hero polish).

### 1.13 Demo upsell-overlay tempt-logic (2026-04-20 amendment)

- **Current state.** Demo-ops docs reference "upsell overlay" and "tempt logic" in prose, but no runtime transform
  widens the demo universe to tease adjacent-tier content. Sales must manually switch persona to showcase upgrade paths.
- **Target state.** Per-axis widening rules in `codex/14-customer-journeys/demo-ops/upsell-overlay-hierarchy.yaml` +
  `apply_tempt_logic(response, env) -> QuestionnaireResponse` transform in
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/tempt_logic.py`. Chained into `resolve_profile`
  BEFORE the questionnaire-overlay step. DEMO env only (`env.is_demo=True`); production is a no-op. Never widens
  `service_family` or `fund_structure` axes (rule-12 scope is absolute, not teasable).
- **Blast radius.** UAC (1 new module), demo-ops (1 new YAML), strategy-service (resolve endpoint reads tempt output).
- **Blockers.** G1.7 restriction-profile engine (consumer), G1.10 questionnaire (input source).
- **Group.** G1
- **Owner.** UAC + strategy-service + demo-ops
- **Proposed follow-up plan.**
  [`refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.plan.md`](../../../plans/archive/refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.plan.md)
  — **SHIPPED 2026-04-20** (commit `147c773`).
- **Unlocks playbooks.** pb3c `dart-demo.md` (upsell path tease), pb3b `investment-management-demo.md` (flavour
  widening).

### 1.14 Presentation deck refresh + HTML stretch (2026-04-20 amendment)

- **Current state.** `/codex/14-customer-journeys/presentations/target-experience-post-refactor.md` drafted against the
  9-item G1 enumeration; missing slides for items 1.10-1.14 and the 2026-04-20 amendment's cross-cutting lessons (MCP
  Playwright discipline, dev/staging parity). No HTML reveal.js wrapper.
- **Target state.** Markdown deck refreshed for the 14-item G1 surface + 7 new slides (G1.10 questionnaire, G1.11 scope
  rules, G1.12 public-site IA, G1.13 tempt-logic, G1.4 persona matrix, MCP Playwright discipline, dev/staging parity).
  Optional reveal.js HTML wrapper at `target-experience-post-refactor.html` — HTML stretch depends on G1.4 personas
  screenshots landing first.
- **Blast radius.** 1 markdown refresh, 1 new HTML wrapper (stretch), 0 code.
- **Blockers.** G1.4 persona combinatorial expansion (screenshots for stretch only).
- **Group.** G1 (markdown); G1 stretch (HTML, after G1.4).
- **Owner.** codex / presentations
- **Proposed follow-up plan.**
  [`refactor_g1_14_presentation_deck_refresh_2026_04_20.plan.md`](../../../plans/archive/refactor_g1_14_presentation_deck_refresh_2026_04_20.plan.md)
  — **SHIPPED 2026-04-20** (markdown + HTML stretch both landed post-G1.4).
- **Unlocks playbooks.** Operator-level communication of the Stage-3E roadmap to stakeholders.

---

## 2. G2 — next (ships in months 2–4)

### 2.1 Org-scoped JWT claims

- **Current state.** JWT carries `uid`, `email`, `email_verified`, Firebase custom claims. No `org_id`, `fund_id`,
  `client_id`, `business_unit`, `api_key_scopes`, `audience` claims. Personas have `org: { id, name }` client-side only.
  See [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) §8.
- **Target state.** Firebase custom claims emit `{org_id, client_id, fund_id, business_unit, audience, api_key_scopes}`
  at provisioning time. `unified-trading-system-ui/lib/auth/*` reads claims from the ID token. `access_control(...)`
  middleware derives `UserContext` from claims verbatim (no client-side persona lookup). user-management-ui's
  provisioning flow populates these at account creation.
- **Blast radius.** user-management-api (claim emitter), unified-trading-system-ui (claim reader), all backend services
  (JWT middleware consumers).
- **Blockers.** Staging Firebase project (2.5).
- **Group.** G2
- **Owner.** user-management-api + UI
- **Proposed follow-up plan.** `org_scoped_jwt_claims_2026_06.plan.md` (folds existing
  [user_management_merge_2026_03_23.plan.md](../../../plans/ai/user_management_merge_2026_03_23.plan.md) scope).
- **Unlocks playbooks.** All playbooks requiring non-demo-fixture auth.

### 2.2 Per-client API key issuance

- **Current state.** No per-client API keys. All calls are Firebase-session-token; no API developer surface. No UAC
  declaration of API-key scopes.
- **Target state.** `unified-api-keys-service` (new) or user-management-api extension issues per-client API keys scoped
  to `(client_id, api_key_scopes)`. Keys rotatable via admin console. Rate-limited per-org via deployment-api. UAC
  declares `ApiKeyScope` enum: `read_data`, `read_reporting`, `execute_trades`, `execute_defi`,
  `admin_override_coverage`.
- **Blast radius.** 1 new service OR user-management-api extension, deployment-api rate-limiter, UAC ApiKeyScope enum,
  admin UI for rotation.
- **Blockers.** 2.1 (JWT claims carry `api_key_scopes`).
- **Group.** G2
- **Owner.** user-management-api + deployment-api
- **Proposed follow-up plan.** `per_client_api_key_issuance_2026_06.plan.md`
- **Unlocks playbooks.** pb3c `dart-demo.md` (developer-portal walkthrough), pb2b `dart-briefing.md` (API key
  description).

### 2.3 Four-catalogue parity — Data Catalogue refactor

- **Current state.** `/services/data/*` is 13 routes of ad-hoc lists (instruments, venues, coverage, completeness, gaps,
  missing, events, logs, processing, raw, valuation, markets). Three concept-duplicates (completeness + missing + gaps).
  No queryable master matrix. No archetype × instrument × venue × chain dimension navigation like Strategy Catalogue. No
  codex deep-link.
- **Target state.** `/services/data-catalogue/*` matching the Strategy Catalogue pattern — master matrix, filter facets,
  per-instrument detail, admin availability axis, codex GitHub deep-link to
  [`/codex/02-data/availability-manifest-and-data-status.md`](../../02-data/availability-manifest-and-data-status.md).
  Three concept-duplicates consolidated into `/services/data-catalogue/coverage/gaps` with tabs.
- **Blast radius.** 13 → 7 UI routes, 1 new lib module mirroring coverage; strategy-service/availability data
  sub-surface.
- **Blockers.** Derivation engine (1.6) so data-status reads from the shared registry.
- **Group.** G2
- **Owner.** UI + strategy-service
- **Proposed follow-up plan.** `data_catalogue_parity_refactor_2026_06.plan.md`
- **Unlocks playbooks.** pb3c `dart-demo.md` (data-exploration walkthrough).

### 2.4 Four-catalogue parity — ML Model Catalogue refactor

- **Current state.** `/services/research/ml/*` is 9 routes + 5 broken. Fragmented (config + grid-config + registry +
  training all partially overlapping). No model-family taxonomy in UAC. No per-model-family lock/maturity registry (only
  strategy availability exists). Biggest single pending UI surface per
  [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) §4.3.
- **Target state.** `/services/ml-model-catalogue/*` matching Strategy Catalogue. `ModelFamilyRegistry` in UAC declaring
  families (xgboost_1h, lstm_5m, transformer_event, poisson_xg, logit_eloprobs, ...). Per-model-family lock state +
  maturity (reusing `LockState` + `StrategyMaturity` from Phase 10.5). Per-family detail pages. Cross-links from
  Strategy Catalogue's `ml_family_ref` field.
- **Blast radius.** UI (13 new routes, 9 old retired), UAC (new ModelFamilyRegistry), strategy-service reads
  `ml_family_ref` correctly.
- **Blockers.** 1.6 (derivation engine), 2.3 structural pattern reused.
- **Group.** G2
- **Owner.** UI + UAC + strategy-service
- **Proposed follow-up plan.** `ml_model_catalogue_parity_refactor_2026_06.plan.md`
- **Unlocks playbooks.** pb3c `dart-demo.md` (ML research walkthrough), pb3b `investment-management-demo.md` (reporting
  on ML-backed strategies).

### 2.5 Four-catalogue parity — Execution Algo Catalogue refactor

- **Current state.** `/services/execution/*` is 7 sub-routes (algos, benchmarks, candidates, handoff, overview, tca,
  venues) + `[executionId]`. `algos` is flat list; no TWAP/VWAP/POV/iceberg/SOR archetype hierarchy. `venues` duplicates
  `/services/data/venues` conceptually. TCA stub shipped but placeholder. `candidates` + `handoff` arguably belong in
  Strategy Catalogue.
- **Target state.** `/services/execution-algo-catalogue/*` matching Strategy Catalogue. Execution algo archetype
  hierarchy: TWAP / VWAP / POV / iceberg / SOR / sniper / liquidation-bot / flash-loan-bundle / calendar-spread-combo /
  limit-passive / market / leader-hedge. Per-algo detail pages. `candidates` + `handoff` relocated into Strategy
  Catalogue's promotion-ledger flow. `venues` consolidated with `data/venues` into one source.
- **Blast radius.** UI (1 new catalogue + deletions), UAC (`ExecutionAlgoCatalogV2`), execution-service exposes algo
  metadata endpoint.
- **Blockers.** 1.6. UAC gap #7 (`MultiLegOrderCapability`) + gap #10 (`CrossVenueRoutingPolicy`) required for a
  complete algo catalogue.
- **Group.** G2
- **Owner.** UI + UAC + execution-service
- **Proposed follow-up plan.** `execution_algo_catalogue_parity_refactor_2026_06.plan.md`
- **Unlocks playbooks.** pb3c `dart-demo.md` (execution-algo walkthrough).

### 2.6 Staging Firebase provisioning

- **Current state.** No staging Firebase project. Demo personas work localhost-only. Warm-prospect demos on
  odum-research.co.uk (staging domain) cannot provision real Firebase credentials. Tracked as five_space_ia ticket #12
  per memory.
- **Target state.** Staging Firebase project provisioned at `odum-staging` (or similar). Demo personas provisioned with
  real accounts + JWT custom claims (from 2.1). Warm-prospect demo URLs hand out staging-only credentials. Admin console
  rotates credentials between demos.
- **Blast radius.** Firebase console, `VITE_FIREBASE_*` env vars for staging, deployment-api, user-management-api.
- **Blockers.** 2.1 (JWT claim issuer).
- **Group.** G2
- **Owner.** ops + user-management-api
- **Proposed follow-up plan.** `staging_firebase_provisioning_2026_06.plan.md` (tracks five_space_ia #12).
- **Unlocks playbooks.** pb3a / pb3b / pb3c — the three warm-prospect demos against staging.

### 2.7 Demo-provisioning automation

- **Current state.** Demo credentials are seeded by hand for each prospect. No persona-factory. No automatic expiry. No
  per-prospect isolation (two prospects sharing a persona see each other's session state).
- **Target state.** Admin console emits a per-prospect demo credential (1-day TTL) via user-management-api. The
  `demo_profile_id` attaches from a dropdown (DART / IM / Reg Umbrella × flavour). Credentials rotate automatically.
  Each prospect gets their own org_id (e.g. `demo-prospect-<uuid>`) so visibility slicing is enforceable per-prospect.
- **Blast radius.** user-management-api (new endpoint), admin UI (new modal), demo-context provider (reads expiry).
- **Blockers.** 2.1, 2.6, 1.7 (restriction-profile engine).
- **Group.** G2
- **Owner.** user-management-api + UI
- **Proposed follow-up plan.** `demo_provisioning_automation_2026_06.plan.md`
- **Unlocks playbooks.** All pb3 warm-prospect demos — makes them scalable.

### 2.8 Fund + business_unit + reserving_business_unit_id registry

- **Current state.** `StrategyAvailabilityRegistry` takes `business_unit ∈ {saas, im_desk, admin}` but no registry
  declares which `business_unit` owns which `reserving_business_unit_id`. IM has multiple funds (Reg Umbrella + IM
  pooled + per-client SMAs). Per [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) §3.2
  adjacent-missing #2.
- **Target state.** UAC `FundBusinessUnitRegistry` declares: `fund_id → business_unit → reserving_business_unit_id`.
  Each IM pooled fund + Reg Umbrella fund + SMA has a record. Allocator reads this registry instead of free-form
  strings.
- **Blast radius.** UAC (new module), strategy-service allocator reads it, IM allocator-reporting UI consumes it.
- **Blockers.** Phase 10.7 (allocator split — also G2 per below).
- **Group.** G2
- **Owner.** UAC + strategy-service
- **Proposed follow-up plan.** `fund_business_unit_registry_2026_07.plan.md` (folds existing
  [share_class_architecture_2026_04_01.plan.md](../../../plans/archive/share_class_architecture_2026_04_01.plan.md)
  scope).
- **Unlocks playbooks.** pb3b `investment-management-demo.md` (per-fund reporting), pb3a `regulatory-demo.md` (per-firm
  reporting).

### 2.9 UAC capability declarations — remaining 10 gaps (#2–#11)

- **Current state.** 11 of 12 UAC gaps from
  [`uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md) open. Only #12
  (StrategyAvailabilityRegistry) shipped. Specifically missing: #1 ArchetypeCapabilityV2 (see 1.8 — G1), #2
  supported_signal_variants on VenueCapV2, #3 FlashLoanReceiverRegistry, #4 LiquidationBonusScheduleV2, #5
  EventCalendarSourceCapability, #6 IvSurfaceFidelity, #7 MultiLegOrderCapability, #8 PricingFidelity on DeFi, #9
  LaySideExecutionSemantics, #10 CrossVenueRoutingPolicy, #11 RepresentativeFutureRegistry.
- **Target state.** All 11 declared + consumers updated. Each declaration is a separate UAC PR (one gap, one PR).
  Typically 5–15 LoC per gap in UAC + 1–3 consumer services updated.
- **Blast radius.** UAC (11 new modules across `capability_declarations/*.py` + `internal/architecture_v2/*.py`),
  instruments-service, execution-service, features-service, sports-service consumers per gap.
- **Blockers.** None — additive. Some gaps depend on others (#7 unblocks algo catalogue 2.5).
- **Group.** G2 (10 items; #1 is G1)
- **Owner.** UAC + relevant consumers
- **Proposed follow-up plan.** `uac_registry_gaps_2_to_11_2026_07.plan.md` (one umbrella plan with 10 sub-phases).
- **Unlocks playbooks.** pb3c `dart-demo.md` (full catalogue breadth), pb3a `regulatory-demo.md` (LaySide / multi-leg
  for Reg Umbrella clients).

### 2.10 Phase 10.7 — portfolio-allocator UI split (IM-side vs trading-platform-side)

- **Current state.** `/services/research/strategy/allocator` is a single surface serving both IM-desk and
  trading-platform-subscriber audiences. Phase 10.6 consumer-surface split shipped; 10.7 deferred per memory.
- **Target state.** Two distinct surfaces on the same `portfolio_allocator` core:
  - `/services/investment-management/allocator` — IM-desk, careful, human-approved, emits proposals then allocator
    applies on approval.
  - `/services/trading-platform/allocator` — trading-platform-subscriber, auto-apply on client's own infra.
  - Research-side allocator page DELETED (rule 03: allocator is not research, it's a commercial surface).
- **Blast radius.** 2 new UI routes, 1 deleted, 2 backend variants on same `portfolio_allocator` core
  (instance-configuration not code-fork).
- **Blockers.** 2.1 (JWT audience claim), 2.8 (fund registry).
- **Group.** G2
- **Owner.** UI + strategy-service
- **Proposed follow-up plan.** `phase_10_7_allocator_split_2026_07.plan.md` (folds existing
  [platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md](../../../plans/ai/platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md)).
- **Unlocks playbooks.** pb3b `investment-management-demo.md` (IM allocator surface), pb3c `dart-demo.md`
  (trading-platform allocator surface).

### 2.11 Account-intelligence-record CRM base

- **Current state.** No structured per-prospect CRM. Demo deviations, talking points, not-show log entries, follow-up
  tasks sit in sales-person heads or ad-hoc docs. Rule 09 `09-internal-commercial-oneliners.md` implies this exists;
  rule 06 §"Enforcement rules" #5 references "account-intelligence record".
- **Target state.** Minimal CRM table (per-prospect):
  `{prospect_id, org_id, commercial_path, resolved_cell, demo_history, not_show_deviations, upcoming_actions, next_playbook}`.
  Admin console surface at `/admin/prospects/[id]`. Hooks into user-management-api for persona assignment.
- **Blast radius.** 1 new table in user-management-api, 1 new admin UI surface, 0 public surface.
- **Blockers.** 2.7 (demo provisioning automation populates it), 2.1 (JWT claims).
- **Group.** G2 (on G2/G3 border — can slide to G3 if bandwidth is tight)
- **Owner.** user-management-api + admin UI
- **Proposed follow-up plan.** `account_intelligence_record_crm_2026_07.plan.md`
- **Unlocks playbooks.** pb1 → pb2 → pb3 handoff (rule 01 §9 Internal-handoff section assumes this exists).

---

## 3. G3 — later (ships month 4+)

### 3.1 Pricing-engine service

- **Current state.** `commercial-model/pricing-building-blocks.md` (Stage 2) declares the 13-row × 3-column structure;
  sales anchor ranges are locked. Cost numbers remain codex-private pending finance population (§ 3.2). No runtime
  service; quotes built by hand. Billing service does not reconcile against a programmatic `cost(combo, tier)` source.
- **Target state.** `pricing-engine-service` (new) OR `strategy-service/availability/pricing/` (extension per §5 of
  [`stage-3c-derivation-engine.md`](stage-3c-derivation-engine.md)). Reads populated numbers from
  `commercial-model/pricing-building-blocks.md` (once finance populates). Exposes
  `GET /api/pricing/quote?combo=&tier=&depth=` (capability-gated for `tier=internal`). Billing reconciles monthly
  against this.
- **Blast radius.** 1 new sub-service, billing-service reader, internal admin UI at `/admin/pricing/quote-builder`.
- **Blockers.** 1.6 (derivation engine), 3.2 (numbers populated).
- **Group.** G3
- **Owner.** strategy-service + billing
- **Proposed follow-up plan.** `pricing_engine_service_2026_08.plan.md`
- **Unlocks playbooks.** pb2a/b/c proposal generation, commercial-ops automation.

### 3.2 Pricing-numbers populated from Odum finance

- **Current state.** `commercial-model/pricing-building-blocks.md` (Stage 2) publishes sales anchor ranges; internal
  cost / Tier A / Tier B point values sit only in Odum finance dashboards and leadership decks. The structure is locked;
  the numbers land via finance workflow.
- **Target state.** Finance populates numbers via a non-codex workflow (finance Google Sheet → export → commit). Update
  frequency: quarterly. Internal-column leakage guard per rule 08 ensures only finance-authorised commits land on
  `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md`.
- **Blast radius.** 1 doc populated; no code.
- **Blockers.** None — organisational.
- **Group.** G3 (non-codex, depends on finance)
- **Owner.** Odum finance
- **Proposed follow-up plan.** `pricing_numbers_population_from_finance_2026_08.plan.md` (mostly ops process doc, not
  engineering).
- **Unlocks playbooks.** pb2a/b/c proposal generation with real numbers.

### 3.3 Briefings-content CMS migration

- **Current state.** pb2 briefing docs (`briefings-hub.md`, `dart-briefing.md`, `regulatory-umbrella-briefing.md`,
  `im-decision-journey.md`) live as markdown in `codex/14-customer-journeys/experience/`. Updates require PR + merge +
  deploy. Sales cannot iterate briefing content without engineering.
- **Target state.** Briefing content lives in a headless CMS (Contentful / Sanity / Notion API); UI renders from CMS.
  Markdown in codex becomes the canonical draft + audit source; CMS mirrors it with managed-revision workflow for sales.
- **Blast radius.** New `briefings-content-service` (thin CMS wrapper), UI `/briefings/*` routes read from it,
  codex-sync agent ensures parity.
- **Blockers.** None — additive layer.
- **Group.** G3
- **Owner.** ops + UI
- **Proposed follow-up plan.** `briefings_content_cms_migration_2026_09.plan.md`
- **Unlocks playbooks.** Sales ability to iterate briefing content without engineering roundtrip.

### 3.4 DART marketing-copy rebrand + trademark check

- **Current state.** "Platform" label replaced with "DART" in UI nav (`components/shell/nav-copy.ts` — Phase 3 shipped).
  Marketing copy in static pages + website + briefings still uses "Platform" in places.
- **Target state.** Full DART branding across marketing-static pages, SEO metadata, open-graph tags, briefing docs,
  proposal templates. Trademark check filed (per memory note 2026-04-19 HSBC DART is non-competing; still file search at
  UKIPO / USPTO). Domain `dart.odum.com` registered + redirect configured.
- **Blast radius.** marketing-static pages, SEO config, briefing templates, external website.
- **Blockers.** None — organisational.
- **Group.** G3
- **Owner.** marketing + ops
- **Proposed follow-up plan.** `dart_marketing_rebrand_2026_09.plan.md`
- **Unlocks playbooks.** pb1 `marketing-journey.md` (full DART framing).

### 3.5 Codex-sync + playbook consistency agents

- **Current state.** `codex/14-customer-journeys/` is hand-maintained. When rules change, 40+ docs may drift. No
  automated parity checker between `_ssot-rules/` and downstream docs.
- **Target state.** `playbook-consistency-agent` (part of `plan_health-agent` family) runs on merges to
  `codex/14-customer-journeys/` — verifies rule citations still point to live sections, verifies experience playbook
  grammar (9 sections per rule 01), verifies demo-restriction-profile references are valid.
- **Blast radius.** Agents repo (existing infrastructure), GHA workflow.
- **Blockers.** None — additive.
- **Group.** G3
- **Owner.** agents / plan_health team
- **Proposed follow-up plan.** `playbook_consistency_agent_2026_10.plan.md`
- **Unlocks playbooks.** Long-term maintenance of the `14-customer-journeys/` SSOT.

### 3.6 Visibility-slicing — e2e coverage expansion

- **Current state.**
  [`visibility-slicing.spec.ts`](../../../../unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing.spec.ts)
  covers 4 personas × 5-or-so routes. No LOCKED-VISIBLE coverage (1.3 ships that); no prospect-dart / prospect-reg
  coverage (1.4 adds them).
- **Target state.** Playwright spec covers: 7 personas (adding prospect-dart + prospect-reg) × 3 flavours × full route
  surface (~25 routes). LOCKED-VISIBLE padlock rendering asserted. Phase toggle restrictions asserted (1.1 integration
  test).
- **Blast radius.** 1 spec file (`visibility-slicing.spec.ts`) expanded.
- **Blockers.** 1.1, 1.3, 1.4.
- **Group.** G3 (tests follow features)
- **Owner.** UI
- **Proposed follow-up plan.** `visibility_slicing_e2e_expansion_2026_10.plan.md`
- **Unlocks playbooks.** Long-term safety net for all pb3 surfaces.

---

## 4. Group totals

| Group     | Item count | Primary unlock                                                                                                                                                                                                                                                                                 |
| --------- | :--------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1        |     14     | Stage 3C derivation engine + phase unification + instruction-schema validation + LOCKED-VISIBLE + 2 new personas + 5 broken hrefs fixed + UAC ArchetypeCapabilityV2 + codex scope tagging + questionnaire flow + service-family scope rules + public-site IA + tempt-logic + presentation deck |
| G2        |     11     | JWT claims + API keys + 3 catalogue refactors (Data + ML + Execution Algo) + staging Firebase + demo automation + fund registry + 10 UAC gaps + allocator split + CRM base                                                                                                                     |
| G3        |     6      | Pricing engine + pricing numbers + CMS migration + DART rebrand + consistency agents + e2e expansion                                                                                                                                                                                           |
| **Total** |   **31**   | Full G1 + G2 + G3 roadmap to a shippable SSOT end state                                                                                                                                                                                                                                        |

(The plan calls for ≥ 15; 31 is the complete enumerable backlog after the 2026-04-20 amendment added G1 items 1.10-1.14.
Trim G3 items if scope compression is needed.)

---

## 5. Dependency graph

```
G1 — now
 │
 ├── 1.8 UAC ArchetypeCapabilityV2 ────────────────┐
 ├── 1.9 Codex scope tagging                       │
 │                                                 ▼
 ├── 1.6 Derivation engine ships ◄─────── (uses ArchetypeCapabilityV2)
 │        │
 │        ├─▶ 1.7 Restriction-profile engine (demo registry)
 │        │       │
 │        │       ├─▶ 1.10 Questionnaire-to-configuration flow
 │        │       │       │
 │        │       │       ├─▶ 1.4 Persona combinatorial expansion
 │        │       │       └─▶ 1.13 Demo upsell-overlay tempt-logic
 │        │       │
 │        │       └─▶ 1.11 Service-family scope rules (rule 12) ◄─── (access_control pre-check)
 │        │
 │        ├─▶ 1.1 Phase-unification refactor
 │        ├─▶ 1.2 Instruction-schema validation service
 │        └─▶ 1.3 LOCKED-VISIBLE UI mode
 │
 ├── 1.4 prospect-dart + prospect-reg personas (independent base; expanded via 1.10)
 ├── 1.5 Broken-href probable-5 cleanup (stubs, independent)
 ├── 1.12 Public-site IA + briefings polish (UI-only, independent)
 └── 1.14 Presentation deck refresh (markdown independent; HTML stretch after 1.4)

G2 — next (blocks on G1 completion)
 │
 ├── 2.1 Org-scoped JWT claims ────────────┐
 ├── 2.6 Staging Firebase ◄───────────────┤
 │                                         ▼
 ├── 2.2 Per-client API keys ◄─── (uses JWT)
 ├── 2.7 Demo provisioning automation ◄─── (uses JWT + Firebase + restriction-profile)
 ├── 2.8 Fund + business_unit registry
 ├── 2.9 UAC gaps #2–#11 (per-gap parallelism)
 ├── 2.3 Data Catalogue refactor   ◄─── (uses derivation engine)
 ├── 2.4 ML Model Catalogue refactor ◄─── (uses derivation + UAC #1)
 ├── 2.5 Execution Algo Catalogue ◄──── (uses UAC #7, #10)
 ├── 2.10 Phase 10.7 allocator split ◄── (uses fund registry + JWT)
 └── 2.11 Account-intelligence-record CRM ◄── (G2/G3 border)

G3 — later (polish + automation)
 │
 ├── 3.1 Pricing-engine service ◄── (uses derivation + 3.2 numbers)
 ├── 3.2 Pricing-numbers populated from finance (organisational)
 ├── 3.3 Briefings-content CMS migration
 ├── 3.4 DART marketing-copy rebrand + trademark check
 ├── 3.5 Playbook-consistency agent
 └── 3.6 Visibility-slicing e2e expansion (after 1.1 + 1.3 + 1.4)
```

---

## 6. Cross-links to existing `plans/active/*.md`

Some G1/G2 items fold existing active plans. Those plans either become sub-phases of new umbrella plans (per "Proposed
follow-up plan" column) or are retired once their scope is absorbed.

| Existing plan                                                                                                                                     | Status after Stage 3E                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| [user_management_merge_2026_03_23.plan.md](../../../plans/ai/user_management_merge_2026_03_23.plan.md)                                            | Folded into 2.1 (JWT claims) + 2.2 (API keys)          |
| [share_class_architecture_2026_04_01.plan.md](../../../plans/archive/share_class_architecture_2026_04_01.plan.md)                                 | Folded into 2.8 (fund/business_unit registry)          |
| [deployment_topology_and_client_isolation_2026_04_17.plan.md](../../../plans/archive/deployment_topology_and_client_isolation_2026_04_17.plan.md) | Referenced by 2.6 (staging Firebase)                   |
| [defi_demo_e2e_workflow_2026_03_30.plan.md](../../../plans/archive/defi_demo_e2e_workflow_2026_03_30.plan.md)                                     | Referenced by 1.4 + 2.7 (demo personas + provisioning) |
| [platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md](../../../plans/ai/platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md)  | Folded into 2.10 (Phase 10.7 allocator split)          |
| [five_space_ia_execution_child_plan_2026_04_17.md](../../../plans/ai/five_space_ia_execution_child_plan_2026_04_17.md)                            | Referenced by 2.6 (ticket #12 is staging Firebase)     |
| [coverage_ratchet_policy_2026_04_19.plan.md](../../../plans/archive/coverage_ratchet_policy_2026_04_19.plan.md)                                   | Independent — runs in parallel                         |
| [coverage_uplift_bottom5_2026_04_19.plan.md](../../../plans/ai/coverage_uplift_bottom5_2026_04_19.plan.md)                                        | Independent — runs in parallel                         |

---

## 7. What supersedes what

- This document **supersedes** [`../roadmap/next-waves.md`](../../14-customer-journeys/roadmap/next-waves.md). Content
  preserved in that file with a top-line `> Superseded by ...` pointer.
- This document **does NOT supersede** the 10 duplicate-cluster decisions in
  [`../page-triage/duplicate-clusters.md`](../../14-customer-journeys/page-triage/duplicate-clusters.md) — those are
  tactical merge decisions already resolved within Phase 10.
- This document **does NOT supersede**
  [`../../09-strategy/architecture-v2/uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md) —
  that is the canonical UAC gap tracker; Stage 3E § 1.8 + § 2.9 cite it as the source of truth for UAC work sequencing.

---

## 8. Reporting + success criteria

Per-G progression is tracked in `plans/active/<proposed-follow-up-plan-name>.md` Phase sections. Stage 3E itself is
complete when:

- All 14 G1 items have a tracked follow-up plan spawned or explicitly deferred with reason.
- All 11 G2 items have a tracked follow-up plan spawned or explicitly deferred with reason.
- `roadmap/next-waves.md` superseded header is merged.
- Each experience playbook in `experience/` has a "G-item dependencies" subsection naming which refactor items it
  depends on for its walkthrough to be operational.

(The "Unlocks playbooks" field in each item row makes the reverse mapping trivial to assemble per-playbook.)

---

## 9. Cross-references

- [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) — gap source for every G1/G2 item
- [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) — 15 dimensions + 22 blockers the engine enforces
- [`stage-3c-derivation-engine.md`](stage-3c-derivation-engine.md) — 4 formulas G1 ships
- [`../_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md) —
  no-forked-UIs rule driving 1.1
- [`../_ssot-rules/06-show-dont-show-discipline.md`](../../14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md)
  — LOCKED-VISIBLE semantics for 1.3
- [`../_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
  — rule driving 1.2 + integration-depth pricing in 3.1
- [`../../09-strategy/architecture-v2/uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md) —
  UAC gap tracker referenced by 1.8 + 2.9
