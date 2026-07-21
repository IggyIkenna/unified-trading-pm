---
doc_type: plan
title: DART UI — Strategy Dimension Filtering, Permission Tiers, Client Onboarding & Codex Integration
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-24"
branch: live-defi-rollout
repos_affected: [unified-trading-system-ui, unified-api-contracts, unified-trading-pm]
superseded_by: marketing_site_three_route_consolidation_2026_04_26.md
superseded_on: 2026-04-26
current_readiness: C2
target_readiness: C5
---

## Deferred work — migrated to: `plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md` — successor:

batch4_strategy_ui_archived_plan_residuals (genuinely mixed domain — the frontmatter's
`marketing_site_three_route_consolidation_2026_04_26.plan.md` is real and owns the onboarding/questionnaire/FOMO-funnel
work streams (Phases 0-8), but this plan's Phase 9 (archetype-capability taxonomy: `bespoke_capable`, VOL/MARKET_MAKING
splits, admin-assignment) is a different domain owned by `plans/active/capability_wizard_and_manifest_2026_06_11.md`; a
single successor would misrepresent one half, so the split is tracked as a fresh audit todo there).

# DART UI — Strategy Dimension Filtering, Permission Tiers, Client Onboarding & Codex Integration

> **Status note (2026-04-26): SUPERSEDED.** Phases 1–3 of this plan (UAC restriction-profile axes, UI types,
> questionnaire form, seed mapper, catalogue hydration) shipped via the Funnel Coherence rollout — see
> `marketing_site_three_route_consolidation_2026_04_26.md` Workstream E (commits `029ab371` + `c132421d`, plus the
> seed-mapper extension that landed alongside this supersedure tag).
>
> Phase 4 (Desmond demo persona + email handoff) is operator-driven and tracked via the demo-ops profile YAMLs under
> `codex/14-playbooks/demo-ops/profiles/`.
>
> Phase 5 (DemoPlanToggle component), Phase 6 (FOMO tier badges + upgrade preview), Phase 7 (onboarding website polish —
> bulk absorbed into the funnel-coherence rollout), and Phase 8 (codex docs) remain open as smaller polish tasks. They
> do NOT block the funnel — documenting here so the work isn't lost. New work picks them up opportunistically.
>
> `[unlock-plan]` tag carried in the supersedure commit so this plan can be archived by plan agents.

## Context

Three interleaved work streams that were synthesised from Telegram conversations and session decisions.

### Work Stream A — Client onboarding architecture (end-to-end)

Canonical path: **Briefings → Questionnaire → Strategy Universe (FOMO/Explore tab) → Reporting → Demo → Production**.

The questionnaire captures client preferences. Those answers resolve to a pre-filtered strategy catalogue view in the
FOMO/Explore tab. The Explore tab is the **discovery and subscription surface only** — it does not duplicate returns/P&L
data (which belongs in the reporting service). Clicking "View returns →" on a FOMO card links to
`/services/reports/strategy/{instanceId}`.

This path is the **standard onboarding flow** for all future clients — not ad-hoc for Desmond.

**Desmond (`desmondhw@gmail.com`)** — first client using the full path. Funding rate arb, stable yield, market-neutral,
CeFi + DeFi, perp-only, all venues, low risk. Likely wants regulatory umbrella too. Staging demo must be ready within 48
hours of plan execution start.

**Admin catalogue management** (`admin-universe` + `admin-editor` view modes in `StrategyCatalogueSurface.tsx`) —
already built. Ikenna assigns strategies to organisations, sets maturity/routing, locks or unlocks instances. **Do not
rebuild this**.

### Work Stream B — Strategy catalogue UI enhancements

- Human-readable display names for all strategy identifiers (no raw `UNDERSCORE_IDS` to clients)
- Post-questionnaire filter seeding (Explore tab pre-populates from 11-axis response)
- DART Full vs Signals-In plan toggle in demo mode (visible switch in nav)
- FOMO tier badges (which strategies are available in which tier)
- Locked section preview (Research/Promote gated behind upgrade CTA for Signals-In)
- Catalogue enumeration script (output all 99+ representative instances for user review)

**Catalogue size note**: The 99 representative slot labels are the current declared instances. The actual combinatoric
space is much larger across venue tiers, market neutrality variants, and share class variants. The FOMO tab should
surface this expanding envelope — not just the 99 current instances.

### Work Stream C — Codex integration

All design decisions in this plan must be **woven into existing codex docs**, not bolted on as separate files. The eight
codex updates in Phase 8 are mandatory — a new engineer reading only the codex should be able to understand the full
system without reading this plan.

---

## Pre-Audit Manifest

### Files modified (by repo)

#### `unified-api-contracts`

| File                                                                     | Action                                                               | Lines affected |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------------- |
| `unified_api_contracts/internal/architecture_v2/restriction_profiles.py` | Add 5 new Literal type aliases + 5 fields to `QuestionnaireResponse` | ~107–184       |
| `scripts/enumerate_catalogue.py`                                         | NEW — one-off enumeration script                                     | new file       |

#### `unified-trading-system-ui`

| File                                                         | Action                                                                  | Lines affected        |
| ------------------------------------------------------------ | ----------------------------------------------------------------------- | --------------------- |
| `lib/questionnaire/types.ts`                                 | Add 5 new TS type aliases + fields to `QuestionnaireResponse` interface | ~100–141              |
| `lib/questionnaire/submit.ts`                                | Include 5 new axes in Firestore payload                                 | TBD                   |
| `app/(public)/questionnaire/page.tsx`                        | Add 5 new question steps                                                | TBD                   |
| `app/api/questionnaire/email/route.ts`                       | Include 5 new axes in notification email table                          | TBD                   |
| `lib/architecture-v2/catalogue-filter.ts`                    | Add `venue_category` + `coverage_status` filter dims                    | TBD                   |
| `lib/questionnaire/resolve-persona.ts`                       | Add `seedFiltersFromQuestionnaire()` with rules-based expansion         | TBD                   |
| `lib/strategy-display.ts`                                    | NEW — formatFamily, formatArchetype, formatSlotLabel, etc.              | new file              |
| `components/strategy-catalogue/StrategyCatalogueSurface.tsx` | Apply pretty-printing; FOMO tier banner                                 | TBD                   |
| `components/strategy-catalogue/FomoTearsheetCard.tsx`        | Add tier badge + "View returns →" → reporting link                      | TBD                   |
| `components/strategy-catalogue/RealityPositionCard.tsx`      | Apply pretty-printing                                                   | TBD                   |
| `components/architecture-v2/family-archetype-picker.tsx`     | Apply pretty-printing to dropdown labels                                | TBD                   |
| `lib/auth/personas.ts`                                       | Add `desmond-dart-full` + `desmond-signals-in` personas                 | end of PERSONAS array |
| `app/(platform)/layout.tsx`                                  | Mount `DemoPlanToggle` in nav                                           | TBD                   |
| `app/(platform)/services/strategy-catalogue/page.tsx`        | `from=questionnaire` banner + filter hydration                          | TBD                   |
| `app/(platform)/services/dart/locked/page.tsx`               | NEW — locked section placeholder page                                   | new file              |
| `app/(public)/briefings/page.tsx`                            | Add questionnaire CTAs per pillar                                       | TBD                   |
| `app/(public)/briefings/[slug]/page.tsx`                     | Comparison table + CTA on dart-full/dart-signals-in                     | TBD                   |
| `app/(public)/contact/page.tsx`                              | Verify `dart-signals-in` + `dart-full` pre-fill params                  | TBD                   |
| `components/demo/DemoPlanToggle.tsx`                         | NEW — plan tier switcher badge                                          | new file              |

#### `unified-trading-pm`

| File                                                                  | Action                                                                                         |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `codex/08-workflows/client-onboarding.md`                             | NEW — 7-step onboarding sequence                                                               |
| `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`       | Update sections (questionnaire seeding, Explore role, tier badges, admin catalogue management) |
| `codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md` | NEW — 11-axis → filter mapping SSOT                                                            |
| `codex/06-coding-standards/strategy-display-conventions.md`           | NEW — pretty-printing rules + bespoke names                                                    |
| `codex/14-playbooks/demo-ops/profiles/desmond-dart-full.yaml`         | NEW — Desmond DART Full profile                                                                |
| `codex/14-playbooks/demo-ops/profiles/desmond-signals-in.yaml`        | NEW — Desmond Signals-In profile                                                               |
| `codex/14-playbooks/demo-ops/staging-demo-setup.md`                   | Update: email-based demo login pattern                                                         |
| `codex/04-architecture/service-family-scope.md`                       | Update: Full vs Signals-In feature matrix, locked section design                               |
| `codex/02-data/questionnaire-axes.md`                                 | NEW or update: full 11-axis catalogue + Firestore schema                                       |

---

## Execution DAG

```
Phase 0 (Catalogue enumeration) ──────────── P0.3 user review GATE ──────────────────────────┐
                                                                                               │
Phase 1 (Questionnaire axes UAC)  ─── PARALLEL ─── Phase 2 (Pretty-printing utility) ────────┤
Phase 1 (Questionnaire axes UI)   ─── PARALLEL (after P1 UAC) ────────────────────────────────┤
                                                                                               │
                              Phase 3 (Universe seeding — depends on P1+P2) ──────────────────┤
                                                                                               │
         Phase 4 (Desmond personas — depends on P1 types, critical path 48h) ─────────────────┤
                  │                                                                            │
         Phase 5 (Plan toggle — depends on P4) ─────────────────────────────────────────────── ┤
                  │                                                                            │
         Phase 6 (FOMO badges — depends on P5) ─────────────────────────────────────────────── ┤
                                                                                               │
         Phase 7 (Website polish — depends on P1+P3+P4) ────────────────────────────────────── ┤
                                                                                               │
         Phase 8 (Codex integration — LAST, all phases done) ──────────────────────────────────┘
```

**Critical path for Desmond 48h deadline**: P0.1 → P1.1→P1.3 → P4.1 → P4.4 (send email to Desmond)

Phases 1-UAC and 2 are parallel. Phases 1-UI and 4 are parallel after 1-UAC completes.

---

## Phase 0 — Catalogue Enumeration (Prerequisite)

### - [ ] [SCRIPT] P0.1 — Verify manifest is current

```bash
cd unified-api-contracts
source ../.venv-workspace/bin/activate
python scripts/generate_archetype_capability_manifest.py --check
```

Expected: "Manifest is up-to-date (18 archetypes, 99 slot labels)"

### - [ ] [SCRIPT] P0.2 — Write and run catalogue enumeration script

Create `unified-api-contracts/scripts/enumerate_catalogue.py` that imports `STRATEGY_REGISTRY` and outputs a markdown
table grouped by family → archetype → instances, with columns: slot_label, category, coverage_status. Run:

```bash
python scripts/enumerate_catalogue.py 2>&1 | tee /tmp/catalogue_snapshot.md
```

### - [ ] [HUMAN] P0.3 — User reviews output

Ikenna reviews `/tmp/catalogue_snapshot.md` and provides:

- Bespoke display name corrections for 18 archetypes
- Logical grouping feedback
- Any instances to hide from clients
- Expansion envelope feedback (next venue tier additions)

**GATE**: Phase 2 bespoke archetype name finalisation requires P0.3 user review.

---

## Phase 1 — Questionnaire Axis Enhancements

### 5 new axes

| Axis                     | Python type                                 | TS type          | Values                               | Default |
| ------------------------ | ------------------------------------------- | ---------------- | ------------------------------------ | ------- |
| `market_neutral`         | `QuestionnaireMarketNeutrality \| None`     | same             | neutral/directional/both             | `None`  |
| `share_class_preference` | `QuestionnaireShareClassPreference \| None` | same             | btc_neutral/eth_neutral/usd_only/any | `None`  |
| `risk_profile`           | `QuestionnaireRiskProfile \| None`          | same             | low/medium/high                      | `None`  |
| `target_sharpe_min`      | `float \| None`                             | `number \| null` | ≥ 0                                  | `None`  |
| `leverage_preference`    | `QuestionnaireLeveragePreference \| None`   | same             | none/low/medium/any                  | `None`  |

### UAC changes (PARALLEL with Phase 2)

#### - [ ] [CODE] P1.1 — Add 4 Literal type aliases to `restriction_profiles.py`

After existing `QuestionnaireLicenceRegion`:

```python
QuestionnaireMarketNeutrality = Literal["neutral", "directional", "both"]
QuestionnaireShareClassPreference = Literal["btc_neutral", "eth_neutral", "usd_only", "any"]
QuestionnaireRiskProfile = Literal["low", "medium", "high"]
QuestionnaireLeveragePreference = Literal["none", "low", "medium", "any"]
```

#### - [ ] [CODE] P1.2 — Add 5 fields to `QuestionnaireResponse` model

After existing Reg-Umbrella axes:

```python
# ── Strategy-preference axes (optional; 2026-04-24) ─────────────────────
market_neutral: QuestionnaireMarketNeutrality | None = None
share_class_preference: QuestionnaireShareClassPreference | None = None
risk_profile: QuestionnaireRiskProfile | None = None
target_sharpe_min: float | None = None
leverage_preference: QuestionnaireLeveragePreference | None = None
```

#### - [ ] [CODE] P1.3 — Extend `_apply_questionnaire_override()` for new axes

Add new block after existing overlay logic:

- `market_neutral="neutral"` → add `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`,
  `RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED`, `EVENT_DRIVEN` to tile-level padlock list (mark
  their sub-tiles as padlocked)
- `leverage_preference="none"` → padlock `VOL_TRADING_OPTIONS` archetype tiles
- `risk_profile="low"` → padlock PARTIAL-status strategy tiles (catalogue filter; not tile-lock overlay — document as
  annotation only for now, actual filter happens in UI `seedFiltersFromQuestionnaire`)

#### - [ ] [QG] P1.4 — UAC quality gates

```bash
cd unified-api-contracts && bash scripts/quality-gates.sh
```

**Success gate**: `quality-gates.sh` passes. `QuestionnaireResponse` accepts 11 axes, all `None`-defaulted
backwards-compatible.

### UI changes (after P1 UAC passes QG)

#### - [ ] [CODE] P1.5 — Mirror in `lib/questionnaire/types.ts`

Add 4 new type aliases + 5 fields to `QuestionnaireResponse` interface. All optional.

#### - [ ] [CODE] P1.6 — Add 5 question steps to `app/(public)/questionnaire/page.tsx`

5 new card-select steps after `strategy_style`:

1. Market neutrality (3-way: neutral / directional / both)
2. Share class preference (4-way: usd_only / btc_neutral / eth_neutral / any)
3. Risk profile (3-way: low / medium / high)
4. Leverage preference (4-way: none / low / medium / any)
5. Target Sharpe minimum (number input with "Skip" button)

#### - [ ] [CODE] P1.7 — Update `lib/questionnaire/submit.ts`

Include 5 new axes in Firestore document payload.

#### - [ ] [CODE] P1.8 — Update `/api/questionnaire/email/route.ts`

Add 5 new axes to internal notification email HTML table.

#### - [ ] [QG] P1.9 — UI quality gates

```bash
cd unified-trading-system-ui && CI=true npm test -- --run
cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build
```

**Phase 1 success gate**: Questionnaire accepts all 11 axes. Internal email shows all axes.

---

## Phase 2 — Strategy Pretty-Printing Utility (PARALLEL with Phase 1 UAC)

### - [ ] [CODE] P2.1 — Create `unified-trading-system-ui/lib/strategy-display.ts`

Exports: `formatFamily`, `formatArchetype`, `formatVenueScope`, `formatInstrumentType`, `formatShareClass`,
`formatSlotLabel`, `getArchetypePlanTier`, `ARCHETYPE_PLAN_TIER`.

Bespoke archetype display names (subject to P0.3 review):

- `CARRY_BASIS_PERP` → "Basis Carry — Funding Rate (Perp)"
- `CARRY_BASIS_DATED` → "Basis Carry — Dated Futures"
- `ARBITRAGE_PRICE_DISPERSION` → "Price Dispersion Arbitrage"
- `STAT_ARB_PAIRS_FIXED` → "Statistical Arbitrage — Fixed Pairs"
- `STAT_ARB_CROSS_SECTIONAL` → "Statistical Arbitrage — Cross-Sectional"
- (full list in implementation)

FULL-only archetypes (require ML training, lock in Signals-In view): `ML_DIRECTIONAL_CONTINUOUS`,
`ML_DIRECTIONAL_EVENT_SETTLED`, `EVENT_DRIVEN`, `VOL_TRADING_OPTIONS`

Acronym preservation list: ML, BTC, ETH, SOL, USD, USDT, USDC, GBP, EUR, DeFi, CeFi, TradFi, LP, IV, DEX, CEX, OKX

### - [ ] [CODE] P2.2 — Apply formatters in catalogue components

- `StrategyCatalogueSurface.tsx` — column headers, filter chip labels
- `RealityPositionCard.tsx` — heading (family/archetype display)
- `FomoTearsheetCard.tsx` — card title
- `family-archetype-picker.tsx` — dropdown option labels

### - [ ] [CODE] P2.3 — Apply `formatSlotLabel` in admin table and signals dashboard

Admin universe table: pretty-printed primary label + monospace ID as hover/subtitle. Signals dashboard: slot label
column.

### - [ ] [QG] P2.4 — UI quality gates

**Phase 2 success gate**: Zero raw underscore identifiers visible to clients in catalogue UI.

---

## Phase 3 — Questionnaire → Strategy Universe Seeding

**Dependency**: Phase 1 complete (new axes in types) + Phase 2 (pretty-printing for filter chips)

### Architecture note: Explore tab role

FOMO cards show: pretty-printed strategy name, maturity badge, coverage status badge, tier badge, and teaser metric stub
(single-line approximate Sharpe range from manifest). CTA: "View returns →" links to
`/services/reports/strategy/{instanceId}` (reporting service). **No P&L charts in FOMO cards.**

### - [ ] [CODE] P3.1 — Extend `StrategyCatalogueFilter` in `catalogue-filter.ts`

Add:

- `venue_category?: VenueCategoryV2[]`
- `coverage_status?: CoverageStatus[]`

Extend `matchesFilter()`, `serialiseCatalogueFilter()`, `parseCatalogueFilter()` for both new dims.

### - [ ] [CODE] P3.2 — Implement `seedFiltersFromQuestionnaire()` in `resolve-persona.ts`

Full mapping with rules-based expansion:

- `categories` → `venue_category` (CeFi→CEFI, DeFi→DEFI, TradFi→TRADFI, Sports→SPORTS, Prediction→PREDICTION)
- `strategy_style` → `family` (carry→CARRY_AND_YIELD, arbitrage→ARBITRAGE_STRUCTURAL, stat_arb→STAT_ARB_PAIRS, etc.)
- Rules-based expansion: `carry` + `market_neutral=neutral` → also include `ARBITRAGE_STRUCTURAL` (structural arb is
  market-neutral by construction)
- `instrument_types` → `instrument_type` (direct pass-through)
- `market_neutral=neutral` (if family not set by strategy_style):
  `family = [CARRY_AND_YIELD, ARBITRAGE_STRUCTURAL, MARKET_MAKING, STAT_ARB_PAIRS]`
- `leverage_preference=none` → exclude `option` from instrument_type filter
- `risk_profile=low` → `coverage_status = [SUPPORTED]`; high → `[SUPPORTED, PARTIAL]`
- `share_class_preference=usd_only` → `share_class = [USDT, USDC, USD, GBP, EUR]`; `btc_neutral` → `[BTC]`;
  `eth_neutral` → `[ETH]`

### - [ ] [CODE] P3.3 — Post-questionnaire redirect in `questionnaire/page.tsx`

After submit: seed filter from response, serialise, redirect to
`/services/strategy-catalogue?tab=explore&from=questionnaire&{filter_params}`. If unauthenticated: store in
sessionStorage + redirect to login with `next` param.

### - [ ] [CODE] P3.4 — Banner + filter hydration in `strategy-catalogue/page.tsx`

On `?from=questionnaire`: hydrate Explore tab filter from URL params + show banner "Showing **N strategies** matching
your profile — [View all] [Edit filters]". No questionnaire + no filters: show soft CTA "Complete the questionnaire to
see your personalised universe →".

### - [ ] [CODE] P3.5 — Wire "View returns →" link in FOMO card

`FomoTearsheetCard.tsx`: "View returns →" links to `/services/reports/strategy/{instanceId}`. Do not render P&L charts
in the card.

### - [ ] [QG] P3.6 — UI quality gates

**Phase 3 success gate**: Post-questionnaire redirect works. FOMO tab shows correct strategies for Desmond's profile.
"View returns" links to reporting.

---

## Phase 4 — Demo Persona: Desmond (48-hour deadline)

**Dependency**: Phase 1 complete (new QuestionnaireResponse type available in UI)

### - [ ] [CODE] P4.1 — Add two personas to `lib/auth/personas.ts`

Add after existing `prospect-perp-funding` entry (which has fake email `ops@desmond-capital.example`). New entries use
his real email:

```typescript
{
  id: "desmond-dart-full",
  email: "desmondhw@gmail.com",
  password: "odum-demo-2026",
  displayName: "Desmond H-W",
  role: "client",
  org: { id: "desmond-capital", name: "Desmond Capital" },
  entitlements: [
    "investor-relations",
    "investor-platform",
    "data-pro",
    "execution-full",
    "ml-full",
    "strategy-full",
    "reporting",
  ],
  description: "Desmond — DART Full (funding rate arb, stable yield, market-neutral, CeFi+DeFi, perp).",
},
{
  id: "desmond-signals-in",
  email: "desmondhw@gmail.com",   // same email; getPersonaByEmail returns first match (dart-full)
  password: "odum-demo-2026",
  displayName: "Desmond H-W",
  role: "client",
  org: { id: "desmond-capital", name: "Desmond Capital" },
  entitlements: [
    "investor-relations",
    "investor-platform",
    "data-pro",
    "execution-full",
    "reporting",
    // no strategy-full / ml-full → Research/Promote gated
  ],
  description: "Desmond — Signals-In tier (execution + P&L only, no Research/Promote).",
},
```

### - [ ] [CODE] P4.2 — Pre-seed questionnaire on email login in `demo-provider.ts`

In `DemoAuthProvider.login()`, after a persona is resolved by email, check if `persona.id.startsWith("desmond-")`:

```typescript
// Pre-seed questionnaire response for demo personas that have one
const QUESTIONNAIRE_PRESEEDS: Record<string, QuestionnaireResponse> = {
  "desmond-dart-full": {
    categories: ["CeFi", "DeFi"],
    instrument_types: ["perp"],
    venue_scope: "all",
    strategy_style: ["carry", "arbitrage", "stat_arb"],
    service_family: "DART",
    fund_structure: "NA",
    market_neutral: "neutral",
    share_class_preference: "any",
    risk_profile: "low",
    leverage_preference: "low",
    target_sharpe_min: null,
  },
  "desmond-signals-in": {/* same */},
};

const preseed = QUESTIONNAIRE_PRESEEDS[persona.id];
if (preseed) {
  localStorage.setItem("questionnaire-response-v1", JSON.stringify(preseed));
}
```

### - [ ] [CODE] P4.3 — Verify `docker-build.env.uat` settings

Confirm `NEXT_PUBLIC_AUTH_PROVIDER=demo` and `NEXT_PUBLIC_SKIP_AUTH=false`. Do not change prod/firebase env.

### - [ ] [ACTION] P4.4 — Ikenna sends Desmond staging access email

Email content (use the template from CLAUDE plan — contains briefing URLs, questionnaire URL, staging credentials).
**Ikenna manual action — not automated.**

### - [ ] [QG] P4.5 — Manual staging smoke test

1. Navigate `https://uat.odum-research.com` → login `desmondhw@gmail.com` / `odum-demo-2026`
2. ✅ Lands as DART Full persona
3. ✅ Explore tab pre-filtered (carry/arb/stat_arb, CeFi+DeFi, perp)
4. ✅ Strategy names pretty-printed

**Phase 4 success gate**: Staging demo ready for Desmond within 48 hours.

---

## Phase 5 — DART Full vs Signals-In Plan Toggle

**Dependency**: Phase 4 (both personas exist)

### - [ ] [CODE] P5.1 — Create `components/demo/DemoPlanToggle.tsx`

Small badge in top nav. Shown only when `NEXT_PUBLIC_AUTH_PROVIDER === "demo"` and user is logged in. Clicking swaps
persona between `{baseId}-dart-full` and `{baseId}-signals-in` via `login(targetId)` (ID-based lookup, no password
needed). Shows toast on switch.

Derives `baseId` by stripping `-dart-full` or `-signals-in` suffix from `user.id`. Determines current tier from
`user.entitlements.includes("strategy-full")`.

### - [ ] [CODE] P5.2 — Wire `DemoPlanToggle` into `app/(platform)/layout.tsx`

Mount after user avatar in top nav.

### - [ ] [CODE] P5.3 — Verify locked chip state for Research + Promote sub-routes in `services.ts`

`requiredEntitlements: ["strategy-full", "ml-full"]` on Research and Promote sub-routes. When user lacks these, chip
renders locked (opacity-50, lock icon). Clicking locked chip → navigate to `/services/dart/locked?from=research` or
`?from=promote`.

### - [ ] [CODE] P5.4 — Create `app/(platform)/services/dart/locked/page.tsx`

Content varies by `from` param. Shows: title, bullet list of what the section unlocks, "Upgrade to DART Full" CTA →
`/contact?service=dart-full&action=upgrade`, and (demo mode only) "Switch to DART Full demo" button that calls
`login(baseId + "-dart-full")`.

### - [ ] [QG] P5.5 — UI quality gates + manual test

**Phase 5 success gate**: Toggle works. Signals-In → Research greyed → locked page loads → switch back → Research
active.

---

## Phase 6 — FOMO Tier Badges + Upgrade Preview

**Dependency**: Phase 5 (toggle exists; plan-aware rendering meaningful)

### Tier classification

4 Full-only archetypes (require ML training pipeline):

- `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`, `EVENT_DRIVEN`, `VOL_TRADING_OPTIONS`

14 archetypes available in both Signals-In and Full.

### - [ ] [CODE] P6.1 — `ARCHETYPE_PLAN_TIER` and `getArchetypePlanTier()` already in `lib/strategy-display.ts` (Phase 2)

No additional code needed — Phase 2 includes this.

### - [ ] [CODE] P6.2 — Add tier badge to `FomoTearsheetCard.tsx`

Green "Full + Signals-In" badge for `both` tier. Amber "DART Full only" badge for `full-only` tier (amber styling when
Signals-In active). Badge data comes from `getArchetypePlanTier(instance.archetype)`.

### - [ ] [CODE] P6.3 — Upgrade banner in `StrategyCatalogueSurface.tsx` Explore tab

When Signals-In persona active (lacks `strategy-full`): amber banner showing `signalsInCount / totalCount` +
`fullOnlyCount` + toggle CTA + upgrade CTA.

### - [ ] [QG] P6.4 — UI quality gates

**Phase 6 success gate**: FOMO cards in Signals-In mode show tier badges. Amber banner shows correct counts.

---

## Phase 7 — Onboarding & Website Polish

**Dependency**: Phases 1+3+4 done

### - [ ] [CODE] P7.1 — Post-questionnaire CTA in `questionnaire/page.tsx`

Success screen: "See your strategy universe →" button links to pre-filtered Explore tab.

### - [ ] [CODE] P7.2 — Questionnaire CTAs on briefing detail pages

`/briefings/dart-full` and `/briefings/dart-signals-in`: add "Get your personalised universe →" section linking to
`/questionnaire?service_family=DART`.

### - [ ] [CODE] P7.3 — Pre-fill `service_family` in questionnaire from URL param

Detect `?service_family=DART` → pre-select that axis on load.

### - [ ] [CODE] P7.4 — DART Full vs Signals-In comparison table on `/briefings/dart-signals-in`

Feature matrix table (8 rows × 2 columns): P&L dashboard ✓/✓, Positions ✓/✓, Observe ✓/✓, Signal intake ✓/—, ML
backtesting —/✓, Strategy customisation —/✓, Promote workflow —/✓, Feature engineering —/✓.

### - [ ] [CODE] P7.5 — Verify contact form pre-fill params

Confirm `?service=dart-signals-in` and `?service=dart-full` resolve correctly in `contact/page.tsx` service key map.

### - [ ] [CODE] P7.6 — Verify questionnaire email route includes all 11 axes

Check `/api/questionnaire/email/route.ts` renders all 11 axes in the internal notification HTML table.

### - [ ] [QG] P7.7 — UI quality gates + E2E manual test

**Phase 7 success gate**: Full path works: briefings → questionnaire → submit → pre-filtered Explore tab → "View
returns" links → reporting.

---

## Phase 8 — Codex Integration (LAST)

**Dependency**: All phases 1-7 complete

### - [ ] [DOC] P8.1 — Update `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`

Add/update sections: Explore tab role (discovery + subscription only; returns → reporting), questionnaire seeding,
expanding universe model (99 representative + expansion envelope), DART Full vs Signals-In universe distinction, admin
catalogue management (existing, do not rebuild), tier badge logic.

### - [ ] [DOC] P8.2 — Create `codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md`

SSOT for 11-axis → catalogue filter mapping. Full axis table + rules-based expansion layer + example (Desmond's answers
→ filter → what he sees).

### - [ ] [DOC] P8.3 — Create `codex/06-coding-standards/strategy-display-conventions.md`

Bespoke display name table for 18 archetypes + 8 families. Acronym list. 6-function API. File location. Rule: no raw
UNDERSCORE_IDs to clients.

### - [ ] [DOC] P8.4 — Update `codex/04-architecture/service-family-scope.md`

Add: DART Full vs Signals-In feature matrix, demo plan toggle design, locked section design.

### - [ ] [DOC] P8.5 — Create `codex/08-workflows/client-onboarding.md`

7-step onboarding sequence with Ikenna/client/system actions per step.

### - [ ] [DOC] P8.6 — Create `codex/14-playbooks/demo-ops/profiles/desmond-dart-full.yaml`

YAML profile following existing `prospect-dart.yaml` structure.

### - [ ] [DOC] P8.7 — Create `codex/14-playbooks/demo-ops/profiles/desmond-signals-in.yaml`

YAML profile — same tile base, Research/Promote tiles padlocked.

### - [ ] [DOC] P8.8 — Update `codex/14-playbooks/demo-ops/staging-demo-setup.md`

Add: email-based persona mapping mechanism, persona naming convention, how to onboard new demo client (checklist).

### - [ ] [DOC] P8.9 — Create or update `codex/02-data/questionnaire-axes.md`

Full 11-axis catalogue with Python type, TS type, allowed values, default, Firestore field path.

### - [ ] [QG] P8.10 — PM quality gates

```bash
cd unified-trading-pm && bash scripts/quality-gates.sh
```

**Phase 8 success gate**: All design decisions documented in codex. A new engineer reading only the codex can understand
and extend the full system.

---

## Success Criteria

### Code gates (C4)

- [ ] `cd unified-api-contracts && bash scripts/quality-gates.sh` passes
- [ ] `cd unified-trading-system-ui && CI=true npm test -- --run` passes
- [ ] `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` passes
- [ ] `cd unified-trading-pm && bash scripts/quality-gates.sh` passes

### Business gates (B6)

- [ ] Desmond can log in with his real email to staging and browse his pre-filtered strategy universe
- [ ] Toggle switches between DART Full and Signals-In views without page reload
- [ ] Questionnaire submission redirects to correctly pre-filtered FOMO tab
- [ ] All strategy names display without underscores in client-facing views
- [ ] "View returns →" on FOMO card links to reporting service, not a chart inline
- [ ] Briefings pages have questionnaire CTAs that work end-to-end

### Deployment gates (D1)

- [ ] Quickmerge complete for unified-api-contracts
- [ ] Quickmerge complete for unified-trading-system-ui
- [ ] Quickmerge complete for unified-trading-pm

---

## Quickmerge Protocol

1. `cd <repo> && bash scripts/quality-gates.sh` — pass before quickmerge
2. `bash scripts/quickmerge.sh "<description>" --agent` — never `--dep-branch`
3. Commit order: unified-api-contracts → unified-trading-system-ui → unified-trading-pm (codex last)
4. Never quickmerge when dep repos have uncommitted changes
5. Two-pass: Pass 1 = full QG; quickmerge = Pass 2 (lint/format/typecheck/codex only)

---

## Phase 9 — Full Combinatoric Envelope + Admin Locking & Routing (ADDENDUM 2026-04-24)

### Motivation

The 99-instance `STRATEGY_REGISTRY` is a curated representative slice. The real product surface — enumerated by
`unified-api-contracts/scripts/enumerate_envelope.py` into `catalogue_envelope.md` — is **1,609 single-share-class
instances + 28 bespoke-capable archetypes** (each representing ∞ per-client configurations) across 9 families:

- `ARBITRAGE_STRUCTURAL` (724), `CARRY_AND_YIELD` (355), `MARKET_MAKING` (186 + 7 bespoke), `ML_DIRECTIONAL` (105 + 2),
  `RULES_DIRECTIONAL` (75 + 2), `STAT_ARB_PAIRS` (70 + 2), `VOL_TRADING` (57 + 9), `EVENT_DRIVEN` (28 + 1), `PORTFOLIO`
  (9 + 4).

UI catalogue today exposes only the 99. We need:

1. **Envelope → UI as the backing store** with **progressive disclosure** so clients are not overwhelmed. Admin sees
   all; clients see what is unlocked for their org.
2. **VOL / MM / PORTFOLIO archetype splits** currently mocked in `enumerate_envelope.py` must be lifted into the UAC
   capability manifest (`archetype_capability.py`) so UI + downstream services all share the same SSOT.
3. **Admin locking & routing model**: lock by family, archetype, or individual instance. Route to **DART** surface
   (research/promote), **Reporting-only** surface (IM reporting, no research), or **locked entirely**. Attach
   assignments to an **organisation** (Odum, a client org, or a third-party manager org) — attachment must flow through
   from admin action to user surfacing.
4. **Family / archetype dropdown filter** already landed on IM reporting (performance, trades, portfolio-analytics) in
   this session (uncommitted, 2026-04-24). Wire the same cascade into DART signals dashboard + research surfaces.

### Pre-Audit Manifest

#### `unified-api-contracts`

| File                                                          | Action                                                                                                                                                                                                                           |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `internal/architecture_v2/archetype_capability.py`            | Add VOL archetype split (9), MM archetype split (7 including DEFI_LP sub-archetypes), PORTFOLIO family (4 canonical archetypes). Remove legacy `VOL_TRADING_OPTIONS`, `MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED`. |
| `internal/architecture_v2/archetype_capability_manifest.json` | Regenerate via `scripts/generate_archetype_capability_manifest.py` after Python change.                                                                                                                                          |
| `internal/architecture_v2/strategy_availability.py`           | Add `BespokeEligibility` flag + per-archetype `bespoke_capable: bool`.                                                                                                                                                           |
| `internal/architecture_v2/enums.py`                           | Add `STRATEGY_FAMILY` enum value `PORTFOLIO`; `StrategyArchetype` values for 20 new archetypes.                                                                                                                                  |
| `scripts/enumerate_envelope.py`                               | Remove mocked splits once manifest lifted; script becomes a thin wrapper over the manifest.                                                                                                                                      |
| `internal/architecture_v2/admin_assignment.py`                | NEW — `AdminStrategyAssignment` model. Fields: `assignment_id`, `scope` (`family` \| `archetype` \| `instance`), `scope_id`, `route` (`DART` \| `REPORTING_ONLY` \| `LOCKED`), `org_id`, `created_at`, `created_by`, `notes`.    |
| `internal/domain/client_reporting/StrategyInfo`               | Extend with `family: str`, `archetype: str`, `route: StrategyRoute` (already added optionally in UI fixture 2026-04-24; make authoritative).                                                                                     |

#### `unified-trading-system-ui`

| File                                                         | Action                                                                                                                                                                                                                            |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lib/architecture-v2/envelope.ts`                            | NEW — import the generated manifest JSON as the full envelope; typed accessors grouped by family / archetype / bespoke flag.                                                                                                      |
| `lib/architecture-v2/catalogue-filter.ts`                    | Add `bespoke?: boolean`, `route?: StrategyRoute` filter dims.                                                                                                                                                                     |
| `components/strategy-catalogue/StrategyCatalogueSurface.tsx` | Progressive-disclosure UX: Family accordion (9 rows) → Archetype accordion → representative instances (curated) + "Show all N combinations" drill-down button; bespoke row rendered separately with "Request custom build →" CTA. |
| `components/strategy-catalogue/FomoTearsheetCard.tsx`        | Bespoke variant — no metrics stub, "Start a conversation" CTA.                                                                                                                                                                    |
| `components/admin/AdminStrategyAssignmentTable.tsx`          | NEW — admin-only surface: scope selector (family / archetype / instance), route dropdown (DART / REPORTING_ONLY / LOCKED), org picker, assignment history.                                                                        |
| `app/(ops)/admin/strategy-assignments/page.tsx`              | NEW — admin page hosting the above table.                                                                                                                                                                                         |
| `lib/entitlements/strategy-route.ts`                         | NEW — `resolveStrategyRoute(user, instance, assignments): StrategyRoute \| "HIDDEN"`. Checks org attachments + route.                                                                                                             |
| `components/reports/performance-dashboard.tsx`               | **DONE 2026-04-24 (uncommitted)**: family/archetype cascading dropdowns.                                                                                                                                                          |
| `components/reports/trades-dashboard.tsx`                    | **DONE 2026-04-24 (uncommitted)**: family/archetype dropdowns + client-side strategy_id filter.                                                                                                                                   |
| `components/reports/portfolio-analytics.tsx`                 | **DONE 2026-04-24 (uncommitted)**: family/archetype dropdowns + cascade client filter.                                                                                                                                            |
| `components/strategy-catalogue/*` — DART signals dashboard   | Add same cascade. Scope: `app/(platform)/services/signals/dashboard/page.tsx` + research/promote pages.                                                                                                                           |

#### `unified-trading-pm`

| File                                                            | Action                                                                                                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md` | Document the three-layer model: curated representatives (99) → full envelope (1,609) → bespoke (∞). Document progressive-disclosure UX.                                              |
| `codex/09-strategy/architecture-v2/admin-locking-routing.md`    | NEW — SSOT for the `AdminStrategyAssignment` model. Covers: scope hierarchy (instance > archetype > family), route semantics, org-attachment flow-through, locking precedence rules. |
| `codex/09-strategy/architecture-v2/archetype-taxonomy.md`       | Update: 9 families, full archetype list including 9 VOL + 7 MM + 4 PORTFOLIO.                                                                                                        |

### Execution DAG

```
P9.1 (UAC manifest lift — VOL/MM/PORTFOLIO splits) ──────────────────────── QG ─┐
          │                                                                     │
          └─ P9.2 (enumerate_envelope.py becomes manifest-read) ────────────────┤
                                                                                │
P9.3 (UAC AdminStrategyAssignment model) ────────────────────────────── QG ────┤
                                                                                │
                     P9.4 (UI envelope.ts + catalogue-filter dims) ── PARALLEL ─┤
                     P9.5 (UI progressive disclosure in StrategyCatalogueSurface)┤
                     P9.6 (UI admin strategy-assignments page) ─── PARALLEL ────┤
                     P9.7 (UI DART signals/research/promote cascade) ─ PARALLEL ─┤
                                                                                │
                     P9.8 (Codex SSOT docs) ─────────────────────── LAST ───────┘
```

### Todos

#### UAC

- [ ] [CODE] P9.1.1 — Add 9 VOL archetype entries to `archetype_capability.py` (`VOL_ARB_RV_IV`,
      `VOL_SPREAD_STRUCTURES`, `VOL_CARRY`, `VOL_OVERLAY_COVERED_CALLS`, `VOL_OVERLAY_PROTECTIVE_PUT`, `VOL_STRADDLE`,
      `VOL_SYNTHETIC_DELTA`, `VOL_MARKET_MAKING`, `VOL_ML_LEAN`). Remove legacy `VOL_TRADING_OPTIONS`.
- [ ] [CODE] P9.1.2 — Split `MARKET_MAKING` into `MARKET_MAKING_PASSIVE_SPREAD`, `MARKET_MAKING_INVENTORY_SKEW`,
      `MARKET_MAKING_ML_LEAN`, `MARKET_MAKING_QUEUE_MICROSTRUCTURE`, `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`,
      `DEFI_LP_VAULT`. Remove legacy `MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED`.
- [ ] [CODE] P9.1.3 — Add `PORTFOLIO` family + 4 archetypes (`PORTFOLIO_MULTI_STRATEGY`, `PORTFOLIO_RISK_PARITY`,
      `PORTFOLIO_FACTOR_ALLOCATION`, `PORTFOLIO_TACTICAL_OVERLAY`).
- [ ] [CODE] P9.1.4 — Add `bespoke_capable: bool` field to `ArchetypeCapabilityClaim`. Flag 28 archetypes (full list in
      `enumerate_envelope.py::_BESPOKE_CAPABLE`).
- [ ] [SCRIPT] P9.1.5 — Regenerate `archetype_capability_manifest.json` via
      `scripts/generate_archetype_capability_manifest.py`.
- [ ] [CODE] P9.2.1 — Simplify `enumerate_envelope.py`: remove mocked splits, read everything from manifest.
- [ ] [CODE] P9.3.1 — Create `internal/architecture_v2/admin_assignment.py` with `AdminStrategyAssignment` model.
- [ ] [QG] P9.UAC — `cd unified-api-contracts && bash scripts/quality-gates.sh`.

#### UI

- [ ] [CODE] P9.4.1 — Create `lib/architecture-v2/envelope.ts` — typed envelope accessors.
- [ ] [CODE] P9.4.2 — Extend `catalogue-filter.ts` with `bespoke?: boolean`, `route?: StrategyRoute` dims.
- [ ] [CODE] P9.5.1 — Refactor `StrategyCatalogueSurface.tsx` to progressive-disclosure accordion (family → archetype →
      curated reps + "Show all N" drill).
- [ ] [CODE] P9.5.2 — Add bespoke row renderer + "Request custom build →" CTA in `FomoTearsheetCard.tsx`.
- [ ] [CODE] P9.6.1 — Create `components/admin/AdminStrategyAssignmentTable.tsx` +
      `app/(ops)/admin/strategy-assignments/page.tsx`.
- [ ] [CODE] P9.6.2 — Wire assignments through `lib/entitlements/strategy-route.ts`; consumers =
      StrategyCatalogueSurface + IM reporting dashboards.
- [ ] [CODE] P9.7.1 — Add family/archetype cascade to DART `signals/dashboard/page.tsx`.
- [ ] [CODE] P9.7.2 — Add family/archetype cascade to DART research + promote pages (scope TBD on audit).
- [ ] [QG] P9.UI — UI quality gates + `npm test -- --run`.

#### Codex (LAST)

- [ ] [DOC] P9.8.1 — Update `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md` with curated / envelope /
      bespoke three-layer model + progressive-disclosure UX.
- [ ] [DOC] P9.8.2 — Create `codex/09-strategy/architecture-v2/admin-locking-routing.md` (SSOT for
      AdminStrategyAssignment).
- [ ] [DOC] P9.8.3 — Update `codex/09-strategy/architecture-v2/archetype-taxonomy.md` with full 9-family / 32-archetype
      list.
- [ ] [QG] P9.DOC — `cd unified-trading-pm && bash scripts/quality-gates.sh`.

### Success Criteria (Phase 9)

- **Code**: All three QG groups pass.
- **Business**:
  - Admin can lock a family, archetype, or instance and route to DART / REPORTING_ONLY / LOCKED with an org attach;
    change surfaces immediately to affected users.
  - Client sees only routed-to-DART instances in DART, routed-to-REPORTING_ONLY in IM reports, never sees LOCKED ones.
  - Envelope view in StrategyCatalogueSurface renders 1,600+ instances progressively without performance degradation
    (virtualisation or pagination, not a flat 1.6k DOM).
  - Bespoke rows render with correct CTA and do not attempt metric stubs.
- **Docs**: Codex SSOT covers the full model; no ad-hoc documentation outside codex.

### Decisions confirmed 2026-04-24

1. **Archetype IDs**: names as proposed are final. Lift into UAC manifest unchanged.
2. **Default route** for new admin assignments: `DART`.
3. **Org-attach flow-through**: **batch refresh** (daily). Real-time not required.
4. **Progressive-disclosure UX**: **accordion or tree**. Implement accordion first; tree is a follow-up if the accordion
   becomes unwieldy at 5k+ rows.

### Primary-category axis + capability rules (2026-04-24)

The envelope now uses **primary category** (`CEFI` / `DEFI` / `TRADFI` / `SPORTS` / `PREDICTION` / `CROSS_CATEGORY`) as
the top-level axis:

1. User picks category first.
2. Then family (within that category only).
3. Then archetype.
4. Then instance (representative) or "Show all N combinations" drill-down.
5. Bespoke rows appear inline per (category × archetype) with a "Request custom build →" CTA.

**Category × archetype capability rules** are mocked in `scripts/enumerate_envelope.py::_ARCHETYPE_ALLOWED_CATEGORIES`.
These forbid nonsensical combinations — e.g. `CARRY_*` on SPORTS (no funding rates), `VOL_*` on SPORTS/PREDICTION (no
options), `DEFI_LP_*` on TRADFI, `MARKET_MAKING_QUEUE_MICROSTRUCTURE` on DEFI (no order-book queue on AMMs). These rules
must be lifted into the UAC manifest alongside the archetype split (Phase 9.1).

**Per-category venue universe** also mocked in `scripts/enumerate_envelope.py` — wider than the currently-integrated
`venue_ids` in the manifest. CEFI spot/perp uses a 10-venue list
(Binance/OKX/Bybit/Hyperliquid/Deribit/Coinbase/Bybit/Bitget/Gate/ KuCoin); DEFI expands per protocol × chain; TRADFI
covers IBKR/CME/ICE/CBOE/Saxo/LMAX/ Eurex/NYSE/NASDAQ; SPORTS covers
Unity/Betfair/Smarkets/Sporttrade/Sportradar/FanDuel/ DraftKings; PREDICTION covers Polymarket/Kalshi/Unity/Manifold.

Envelope output **2026-04-24**: **5,355 single-share-class instances + 51 bespoke archetype-rows** across 9 families × 6
categories. Breakdown:

| Category          | Instances | Bespoke |
| ----------------- | --------: | ------: |
| CEFI              |     1,175 |      19 |
| DEFI              |     3,501 |       8 |
| TRADFI            |       512 |      12 |
| SPORTS            |       112 |       4 |
| PREDICTION        |        46 |       4 |
| CROSS (Portfolio) |         9 |       4 |

### Admin-assignment multi-route rule (CRITICAL)

A single strategy (scope = family / archetype / instance) **may** be routed to both `DART` and `REPORTING_ONLY`
simultaneously, **only if the attached org is the same**. Route + org is a composite key:

- `(scope_id, org_A, DART) + (scope_id, org_A, REPORTING_ONLY)` — ✅ allowed. Same org sees the strategy on both
  surfaces.
- `(scope_id, org_A, DART) + (scope_id, org_B, REPORTING_ONLY)` — ❌ forbidden. Different orgs on different routes means
  two orgs are competing for the same strategy. The admin write must reject with `ORG_CONFLICT_ON_STRATEGY`.
- `(scope_id, org_A, LOCKED)` — exclusive. No other assignment on the same scope_id regardless of org.

Implementation: `admin_assignment.py::AdminStrategyAssignmentWriter.validate()` checks the existing assignment set on
write, rejects conflicts loud.

### Config version is an implicit locking axis

Every instance today runs on config `v1` (baseline parameters). As config groups evolve (thresholds, windows, sizing,
feature toggles), new versions emerge. Client org subscriptions lock in a specific version — changing version is a
deliberate admin action. Version-governance is the mechanism for bounding the otherwise-infinite config space.

This ties into the existing **Plan D version governance** work (strategy-lifecycle version_governance worker + UAC
subscription.py + UTL 7-event registration, shipped 2026-04-22). Phase 9's admin-assignment model should carry a
`config_version: str` field (default `"v1"`) alongside `scope`, `route`, `org_id`.

### Shipped 2026-04-24/25

UAC `9a9242d` (envelope script + curated snapshot script) on origin/live-defi-rollout. UI 5 files (IM reporting cascade
dropdowns + glossary fix) — quickmerge in flight 2026-04-25.

### Envelope artefacts (live)

Catalogue snapshot scripts now emit to GCS on every run:

| Artefact                                           | GCS path                                                                              | Console                                                                                                                                  |
| -------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Curated 99 (representative slot labels)            | `gs://strategy-store-cefi-central-element-323112/catalogue/snapshot.md` (next ship)   | —                                                                                                                                        |
| Full combinatoric envelope (6,063 + 75 bespoke)    | `gs://strategy-store-cefi-central-element-323112/catalogue/envelope.md`               | https://console.cloud.google.com/storage/browser/_details/strategy-store-cefi-central-element-323112/catalogue/envelope.md               |
| Strategy → instruments resolver (stub: venue-only) | `gs://strategy-store-cefi-central-element-323112/catalogue/strategy_instruments.json` | https://console.cloud.google.com/storage/browser/_details/strategy-store-cefi-central-element-323112/catalogue/strategy_instruments.json |

Run scripts via:

```
cd unified-api-contracts && source ../.venv-workspace/bin/activate
python scripts/enumerate_envelope.py --upload
python scripts/enumerate_strategy_instruments.py --upload
```

### Catalogue scope as of 2026-04-25

**6,063 single-share-class instances + 75 bespoke-capable archetypes** across 9 families × 6 categories:

| Category       | Instances | Bespoke |
| -------------- | --------: | ------: |
| CEFI           |     1,395 |      28 |
| DEFI           |     3,792 |      12 |
| TRADFI         |       620 |      21 |
| SPORTS         |       112 |       4 |
| PREDICTION     |        54 |       5 |
| CROSS_CATEGORY |        90 |       5 |

VOL family expanded to 18 archetypes including 0DTE (`VOL_0DTE_GAMMA_SCALPING`, `VOL_0DTE_PIN_RISK`), term-structure
(`VOL_TERM_STRUCTURE_ARB`, `VOL_TERM_STRUCTURE_SLOPE`, `VOL_DISPERSION`), variance swap, LEAPS convexity, cross-asset
spread (BTC vol vs ETH vol), and ratio-spread structures (1×2 / 2×3 / broken-wing). MEV split adds 4 DeFi-only
archetypes (sandwich, JIT liquidity, backrun, liquidation bundle). Cross-domain event arb covers Polymarket↔Betfair
same-event arb. Prediction-market MM is its own archetype.

---

## Phase 10 — Strategy → Instruments Resolver + UI Filter Hierarchy Fix

> **Status:** Refreshed against codebase 2026-04-25. **10 of 14 original todos shipped.** Remaining work is one
> architectural fix (P10.6.4) and two UI partials (P10.3.1 cascade, P10.4.1 terminal). Original blocker description for
> P10.6.x ("teammate needs to run real parquet resolver") is **stale** — the resolver shipped, the GCS artefact is fresh
> (`gs://strategy-store-cefi-central-element-323112/catalogue/strategy_instruments.json`, 17.8 MB, 943 slots with
> concrete instrument keys), and the Cloud Scheduler nightly job is terraformed. P10.6.x is unblocked.

### Motivation (2026-04-25)

The catalogue tells you _what shape_ of instrument is allowed (archetype × category × venue × instrument*type). The
instruments-service writes \_which concrete instruments exist right now* per-(category, day, venue) parquet rolls under
`gs://instruments-store-{category}-central-element-323112/instrument_availability/by_date/`. We need a resolver that
joins the two so UI surfaces (DART, terminal, IM reporting) can answer "which instruments can I trade for this strategy
slot today?"

Plus the DART filter hierarchy is wrong — was 2 levels (`strategy family` + `strategy`) with family value mislabelled
"DeFi/DeFi". The correct hierarchy per Phase 9 decisions is **`category → family → archetype → instance`** (4-level).
The DeFi/DeFi label has been fixed; cascade-to-4-levels in the catalogue surface is still partial.

### Pre-Audit Manifest (refreshed)

| File                                                                        | Action                                                                                                                                                                                                                                                                              | Status                                                                                                                     |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/scripts/enumerate_strategy_instruments.py`           | Real parquet read via `_resolve_instruments_real()` (L222–259), per-category bucket index `_build_bucket_venue_index()` (L166–200), `--with-real-instruments` flag (L349–352).                                                                                                      | ✅ DONE                                                                                                                    |
| `deployment-service/terraform/gcp/catalogue_regen_scheduler.tf`             | Cloud Scheduler nightly (`30 4 * * *` UTC) → Cloud Run job `catalogue-regen:run`. SA reads instrument-store buckets, writes strategy-store. Retry config + backoff.                                                                                                                 | ✅ DONE                                                                                                                    |
| `unified-trading-system-ui/lib/architecture-v2/envelope-loader.ts`          | (Plan called for `strategy-instruments.ts`; landed at `envelope-loader.ts` with same surface.) Exports `instrumentsForSlot()` (L301), `slotsForArchetype()`, `slotsForAssetGroup()` (asset_group rename per Phase 11). Cached fetch via `/api/catalogue/envelope?file=…` GCS proxy. | ✅ DONE (filename diverged — keep `envelope-loader.ts` as the canonical home; do NOT create a new strategy-instruments.ts) |
| `components/strategy-catalogue/StrategyCatalogueSurface.tsx`                | Cascade still 2-level (`FamilyArchetypePicker` at L255–259). No `category` or `instance` cascade level present. "DeFi/DeFi" literal grepped → not present (already fixed).                                                                                                          | 🟡 PARTIAL — needs category + instance levels added on top                                                                 |
| `components/terminal/order-entry-form.tsx`                                  | File does not exist. The terminal order-entry surface lives elsewhere (or hasn't been built). Needs scoping decision before implementing.                                                                                                                                           | 🟥 NOT BUILT                                                                                                               |
| `components/reports/{performance,trades,portfolio-analytics}-dashboard.tsx` | 3-level cascade shipped on `performance-dashboard.tsx` (L60–95) + `trades-dashboard.tsx` (L36–38, L65–84): `assetGroup → family → archetype`. `portfolio-analytics-dashboard.tsx` not found in the codebase — file deleted or renamed.                                              | ✅ DONE on the two surfaces that exist                                                                                     |
| `lib/config/auth.ts` (the actual home of `AuthPersona`)                     | `assigned_strategies?: readonly string[]` field on the interface (L107) with jsdoc explaining catalogue slot label semantics + locked-visible fallback. (Plan said `lib/auth/personas.ts` — type lives in `auth.ts`; values seeded in `personas.ts`.)                               | ✅ DONE                                                                                                                    |
| `lib/auth/personas.ts` Desmond + Patrick seeds                              | `desmond-dart-full` (L385) carries 11 slot labels (L409–421). `elysium-defi` (L250–265) carries 2; `elysium-defi-full` (L268–285) extends to 5 with CARRY_RECURSIVE_STAKED + YIELD_ROTATION_LENDING.                                                                                | ✅ DONE                                                                                                                    |
| `lib/auth/demo-provider.ts` runtime hydration                               | `personaToAuthUser()` (L9–25) copies entitlements ONLY. **`assigned_strategies` is read by neither `personaToAuthUser` nor `login()`. `instrumentsForSlot()` is never called at login**. Plan-named "P10.6.4" is the architectural debt — not done.                                 | 🟥 PENDING (architectural debt — see "Universal hydration" rewrite below)                                                  |
| `codex/09-strategy/architecture-v2/instruments-resolver-architecture.md`    | New SSOT shipped describing the catalogue ↔ instruments-service join, GCS layout, refresh cadence.                                                                                                                                                                                  | ✅ DONE                                                                                                                    |
| `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`             | Updated for 4-level filter hierarchy.                                                                                                                                                                                                                                               | ✅ DONE                                                                                                                    |

### Architectural rewrite — Universal persona instrument hydration (replaces narrow P10.6.4)

**User intent (2026-04-25):** ALL personas should resolve their concrete instrument lists from `instrumentsForSlot()` at
login time. The "Desmond + Patrick only" framing of the original P10.6.4 was too narrow — any future demo persona would
re-introduce the same hardcoded-list drift. **This must be a default behaviour at the demo-provider layer**, not
per-persona work.

**Mechanics:**

1. `lib/auth/demo-provider.ts` exports `derivePersonaInstruments(persona: AuthPersona): Promise<readonly string[]>` that
   maps over `persona.assigned_strategies` (when present) and concatenates the result of `instrumentsForSlot()` for each
   slot. Empty/absent `assigned_strategies` → empty list (consumer falls through to entitlements gating).
2. `personaToAuthUser()` becomes async, awaits `derivePersonaInstruments(persona)`, and writes the result onto a new
   `AuthUser.instruments?: readonly string[]` field.
3. Login flow on every demo provider call site uses the same hydration — no per-persona special-casing.
4. Hardcoded instrument lists currently scattered in `personas.ts` (the questionnaire-preseeded mock arrays in
   `demo-provider.ts:94–147`, plus any persona-local mock-data shims in service tabs) are deleted; consumers read
   `user.instruments` instead.
5. `instrumentsForSlot()` is server-side-friendly (it reads cached JSON via a relative API proxy), so the hydration
   works in client demo-provider without a separate fetch shim.

**Surface area of the cleanup:** ~4 personas with hardcoded `assigned_strategies` flow through the same path; an unknown
number of consumers currently bypass `assigned_strategies` and read mock lists directly. The cleanup pass is to rewire
those consumers to `user.instruments`.

### Execution DAG (refreshed)

```
P10.1 (✅ UAC parquet resolver + scheduler) ─── DONE ──┐
P10.2 (✅ envelope-loader.ts accessors) ─── DONE ──────┤
P10.3 (🟡 catalogue surface cascade)   ─── PARALLEL ───┤
P10.4 (🟥 terminal order-entry — file does not exist) ─┤  ← scope decision needed before any code
P10.5 (✅ reporting cascade) ─── DONE ─────────────────┤
P10.6 (🟥 universal persona hydration) ─── BLOCKER for FOMO/catalogue parity demos ───┤
P10.7 (✅ codex SSOTs) ─── DONE ───────────────────────┘
```

### Todos (refreshed — surviving work only)

#### UAC (resolver) — ✅ DONE

- [x] [CODE] P10.1.1 — Real parquet read shipped at
      `unified-api-contracts/scripts/enumerate_strategy_instruments.py:222`.
- [x] [CODE] P10.1.2 — Per-category bucket index + error handling shipped (L166–200).
- [x] [CODE] P10.1.3 — Cloud Scheduler nightly job shipped at
      `deployment-service/terraform/gcp/catalogue_regen_scheduler.tf`.
- [x] [QG] P10.1.UAC — quality-gates passed at ship time.

#### UI accessors + filter cascade

- [x] [CODE] P10.2.1 — `instrumentsForSlot()` + `slotsForArchetype()` + `slotsForAssetGroup()` shipped at
      `lib/architecture-v2/envelope-loader.ts:301`. Filename diverged from plan (`envelope-loader.ts` not
      `strategy-instruments.ts`); keep canonical at `envelope-loader.ts`.
- [x] [CODE] P10.3.1 — Refactor `StrategyCatalogueSurface.tsx` filter UI to 4-level cascade:
      `asset_group → family → archetype → instance`. **Done:** commit `0be7b2bc`. 2026-04-25.
- [x] [CODE] P10.3.2 — "DeFi/DeFi" mis-label fixed (literal not present in current source). `EnvelopeBrowser.tsx` now
      calls `formatFamily(row.family)`. 2026-04-25.
- [x] [CODE] P10.4.1 — **Re-scoped 2026-04-25.** Codebase scan (background agent) found **4 trade-booking surfaces** in
      DART: 1. `ManualTradingPanel` (`components/trading/manual/manual-trading-panel.tsx`) — already uses
      `useStrategyScopedInstruments`. Reference implementation. **Currently not mounted anywhere.** 2. **Terminal**
      (`components/widgets/terminal/order-entry-widget.tsx`) — emergency-only, audit-logged. Hardcoded
      `DEFAULT_INSTRUMENTS` mock. **Deferred** — low-value catalogue scoping for an emergency surface. 3. **Book Trade**
      (`components/widgets/book/book-order-entry-widget.tsx`) — full back-office form (Execute / Record-Only modes, OTC,
      compliance). Was freeform text input. **SHIPPED** — replaced freeform `<Input>` with a catalogue-scoped `<Select>`
      driven by `useStrategyScopedInstruments(strategyId, user.instruments)`. Falls back to freeform when
      `strategyId === "manual"` or scoping returns no instruments (so OTC + unusual tickers still work). "Custom
      symbol…" sentinel in the dropdown lets the user opt back into freeform mid-form. testids:
      `book-instrument-scoped-select`, `book-instrument-freeform-input`. 4 new tests cover the four render modes (manual
      / no-scope / scoped / freeform routing). 18/18 book-order-entry harness tests pass. 4. **Asset-group widgets**
      (DeFi swap/lending/staking, Sports fixtures, Predictions) — per-asset-group mock arrays tightly coupled to
      asset-group-specific data. **Deferred** to a separate plan once each asset-group-specific catalogue lands. Plus:
      `use-terminal-page-data.ts` watchlist scoping shipped via
      `useStrategyScopedInstruments(linkedStrategyId ?? "manual", instruments, (inst) => inst.instrumentKey)`. CeFi-only
      default when no strategy linked. 2026-04-25.
- [x] [CODE] P10.5.1 — 3-level cascade shipped on `performance-dashboard.tsx` + `trades-dashboard.tsx`. SelectItems use
      `ASSET_GROUP_LABELS`, `formatFamily()`, `formatArchetype()`. `portfolio-analytics-dashboard.tsx` no longer exists
      in the repo; drop from the manifest. 2026-04-25.
- [ ] [CODE] P10.4.2 — Mount `ManualTradingPanel` somewhere visible (likely as an overlay on
      `/services/trading/terminal/page.tsx` or as a tab on `/services/trading/orders`). Currently dormant — built but
      never rendered. Scope decision: which surface owns the manual-trading control panel UX?
- [ ] [QG] P10.UI — re-run after P10.4.2 + P10.6.4 land.

#### Universal persona hydration (replaces the narrow P10.6.4)

- [x] [CODE] P10.6.1 — `assigned_strategies?: readonly string[]` shipped on `AuthPersona` at `lib/config/auth.ts:107`.
- [x] [CODE] P10.6.2 — Desmond DART-Full seeded with 11 slots at `lib/auth/personas.ts:409`.
- [x] [CODE] P10.6.3 — Patrick (Elysium) base + full tiers seeded at `lib/auth/personas.ts:262,279`.
- [ ] [CODE] P10.6.4 — **Universal hydration in `demo-provider.ts`.** Add `derivePersonaInstruments(persona)` →
      `Promise<readonly string[]>` that calls `instrumentsForSlot(slot)` for each slot in `persona.assigned_strategies`.
      Make `personaToAuthUser()` async; await; expose `user.instruments` as a derived field on `AuthUser`. Applies to
      EVERY persona, not just Desmond + Patrick. Empty `assigned_strategies` → empty list (graceful).
- [ ] [CODE] P10.6.5 — **Cleanup pass.** Find every consumer that reads hardcoded mock instrument lists in service tabs
      (book/orders/positions widgets, `demo-provider.ts:94–147` mock arrays) and rewire to `user.instruments`. Delete
      hardcoded lists once consumers are migrated.
- [ ] [CODE] P10.6.6 — Add a Vitest spec asserting that `personaToAuthUser(desmondDartFull)` returns a non-empty
      `instruments` array, with at least one entry per `assigned_strategies` slot. Mock `instrumentsForSlot` to a
      deterministic stub.

#### Codex — ✅ DONE

- [x] [DOC] P10.7.1 — `codex/09-strategy/architecture-v2/instruments-resolver-architecture.md` (NEW) — describes the
      catalogue ↔ instruments-service join, GCS layout, refresh cadence. **Done:** commit `20c4532` by teammate.
      2026-04-25.
- [x] [DOC] P10.7.2 — `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md` updated with 4-level filter
      hierarchy decision (`asset_group → family → archetype → instance`). 2026-04-25.

### Success Criteria (Phase 10, refreshed)

- **Code**: P10.3.1 + P10.6.4 + P10.6.5 + P10.6.6 land. QGs pass on the touched files.
- **Business**:
  - DART catalogue surface filter shows 4 levels (category → family → archetype → instance), not 2.
  - **Every** demo persona's `user.instruments` field is non-empty when `assigned_strategies` is set, populated via
    `instrumentsForSlot()` at login. No hardcoded instrument lists survive in `personas.ts` or `demo-provider.ts`.
  - Adding a new demo persona by appending to `personas.ts` with an `assigned_strategies` field requires zero changes
    elsewhere — instruments materialise automatically.
- **Docs**: Existing codex SSOTs already cover the resolver join. Add a one-paragraph note to
  `instruments-resolver-architecture.md` describing the universal hydration path so future agents don't reintroduce
  per-persona hardcoding.

---

## Phase 11 — Full 5k+ Catalogue UI Rendering, Asset-Group Rename, Access-Aware Lock States (ADDENDUM 2026-04-25)

### Motivation

The 5k+ envelope already exists as data (`gs://strategy-store-cefi-central-element-323112/catalogue/envelope.md` +
`strategy_instruments.json`). The DART UI today only renders the curated 99 from `STRATEGY_REGISTRY`. Phase 11 wires the
full envelope into the catalogue UI with:

- Primary execution category as top-level filter (with "All" option for category-agnostic strategies)
- "asset class" → **"asset group"** terminology rename across ALL surfaces (constants, labels, types, codex)
- Access-aware rendering: locked-but-visible strategies, reports-only access vs terminal access split
- Progressive-disclosure accordion for 5k+ rows (virtualised)

### Pre-Audit Manifest

| File                                                                                   | Action                                                                                                                                                                     |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-system-ui/lib/architecture-v2/asset-group.ts`                         | NEW or rename from `asset-class.ts`. SSOT constant export `ASSET_GROUPS`, `AssetGroup` type, label map.                                                                    |
| `unified-trading-system-ui/lib/**/*.{ts,tsx}`                                          | Project-wide rename `asset_group` → `asset_group`, `assetClass` → `assetGroup`, `AssetClass` → `AssetGroup`, `"asset class"` → `"asset group"` in user-facing strings.     |
| `unified-api-contracts/.../enums.py`                                                   | If `AssetClass` enum exists, rename to `AssetGroup`. Update all consumers.                                                                                                 |
| `unified-trading-pm/codex/**/*.md`                                                     | Update terminology in codex SSOT docs.                                                                                                                                     |
| `unified-trading-system-ui/components/strategy-catalogue/StrategyCatalogueSurface.tsx` | Render full envelope (not just 99). Virtualised list (react-window or @tanstack/react-virtual) for 5k+ rows. Top-level category filter with "All" option.                  |
| `unified-trading-system-ui/lib/architecture-v2/envelope-loader.ts`                     | NEW. Fetches `envelope.md` + `strategy_instruments.json` from GCS (or proxied via Next.js API route). Cached with stale-while-revalidate.                                  |
| `unified-trading-system-ui/app/api/catalogue/envelope/route.ts`                        | NEW. Proxies GCS read so client doesn't need GCS auth. Returns envelope + instruments JSON.                                                                                |
| `unified-trading-system-ui/lib/entitlements/strategy-route.ts`                         | NEW (overlap with Phase 9). Computes user's per-strategy access state: `terminal-and-reports` / `reports-only` / `locked-visible` / `hidden`.                              |
| `unified-trading-system-ui/components/strategy-catalogue/StrategyCard.tsx`             | Render lock icon + access-state badge per strategy. Locked-visible cards greyed but interactive (hover shows "Available in Reports only" or "Upgrade to unlock terminal"). |
| `unified-trading-system-ui/app/(platform)/services/terminal/page.tsx`                  | Terminal entry blocks reports-only strategies; show "Reports access only — upgrade for terminal" inline.                                                                   |

### Constant SSOT for shared terms

To prevent drift like "DeFi/DeFi" or "asset class" vs "asset group", introduce typed constants:

```ts
// lib/architecture-v2/terminology.ts
export const TERMS = {
  ASSET_GROUP: "asset group",
  STRATEGY_FAMILY: "strategy family",
  STRATEGY_ARCHETYPE: "strategy archetype",
  STRATEGY_INSTANCE: "strategy instance",
  PRIMARY_CATEGORY: "primary execution category",
  // ...
} as const;
```

UI labels MUST reference `TERMS.*` rather than inline strings.

### Execution DAG

```
P11.1 (asset_group → asset_group rename — UAC + UI + codex) ── QG ──┐
                                                                     │
P11.2 (envelope-loader.ts + /api/catalogue/envelope route) ──────────┤
P11.3 (StrategyCatalogueSurface full-envelope rendering, virtualised)┤
P11.4 (Top-level category filter with "All" option) ── PARALLEL ─────┤
P11.5 (Access-aware lock states + reports-only/terminal split) ──────┤
P11.6 (Terminology constants TERMS.* across UI) ── PARALLEL ─────────┤
P11.7 (Codex SSOT — update terminology + lock-state spec) ── LAST ───┘
```

### Todos

#### Asset-group rename (P11.1)

- [ ] [CODE] P11.1.1 — UAC: rename any `AssetClass` enum/type to `AssetGroup`, update all imports.
- [ ] [CODE] P11.1.2 — UI: ripgrep `assetClass`, `AssetClass`, `asset_group`, `"asset class"`. Rename to `assetGroup` /
      `AssetGroup` / `asset_group` / `"asset group"`. Run typecheck after.
- [ ] [CODE] P11.1.3 — Create `lib/architecture-v2/terminology.ts` with `TERMS.*` constants. Replace inline strings.
- [ ] [DOC] P11.1.4 — Codex grep + replace.
- [ ] [QG] P11.1.QG — quality gates each repo.

#### Envelope rendering (P11.2-P11.4)

- [ ] [CODE] P11.2.1 — `app/api/catalogue/envelope/route.ts` — Next.js API route proxying GCS reads of `envelope.md` +
      `strategy_instruments.json`. Server-side ADC.
- [ ] [CODE] P11.2.2 — `lib/architecture-v2/envelope-loader.ts` — client-side fetcher (SWR / react-query). Returns typed
      `EnvelopeEntry[]` parsed from envelope.md grouped sections.
- [ ] [CODE] P11.3.1 — `StrategyCatalogueSurface.tsx` — switch from `STRATEGY_REGISTRY` (99) to envelope data source.
      Virtualise the table — `@tanstack/react-virtual`. Test 5k+ rows render < 200ms.
- [ ] [CODE] P11.3.2 — Progressive accordion: category → family → archetype → instances. Expand-all / collapse-all
      controls.
- [ ] [CODE] P11.4.1 — Top-level category dropdown with "All" option for category-agnostic browsing. Wire into
      `catalogue-filter.ts`.

#### Access-aware lock states (P11.5)

- [ ] [CODE] P11.5.1 — `lib/entitlements/strategy-route.ts` —
      `resolveStrategyAccess(user, slotLabel) → "terminal" | "reports-only" | "locked-visible" | "hidden"`.
- [ ] [CODE] P11.5.2 — `StrategyCard.tsx` — lock icon + access badge per state. Hover tooltip explains.
- [ ] [CODE] P11.5.3 — Reports surfaces include reports-only strategies; terminal blocks them with inline upgrade CTA.

#### Phase 11 success criteria

- [ ] User browses 5,000+ catalogue rows without performance degradation (virtualised, < 200ms initial render).
- [ ] "asset class" string nowhere in user-facing UI; `assetClass` identifier nowhere in TS/Python source.
- [ ] DART catalogue at `https://uat.odum-research.com/services/strategy-catalogue` shows lock icons per user's access;
      locked-visible cards remain interactive.
- [ ] Reports-only strategies appear in IM reporting surfaces but block terminal entry with explicit messaging.

---

## Open todos / nice-to-haves (2026-04-25 backlog)

These don't fit cleanly into a Phase but should land before the catalogue is "production-clean":

- [ ] [CODE] N1 — `enumerate_envelope.py` and `enumerate_strategy_instruments.py` should be wired into PM
      `scripts/dev/dev-start.sh` so local dev surfaces fresh GCS artefacts on every stack start.
- [ ] [SCRIPT] N2 — Cloud Scheduler nightly job for both scripts (overwrite GCS artefacts each night).
- [ ] [CODE] N3 — Lift VOL/MM/PORTFOLIO/MEV/cross-domain splits from `enumerate_envelope.py` mocks into the UAC
      `archetype_capability` manifest as the SSOT (currently script-mocked).
- [ ] [CODE] N4 — Add the 5 new questionnaire axes (already in UAC restriction_profiles) into questionnaire-axes codex
      doc.
- [ ] [CODE] N5 — Demo persona toggle (DART Full ↔ Signals-In) wire-up — landed `d7f4805c` but UAT smoke-test pending
      Desmond email send.
- [ ] [CODE] N6 — FOMO banner on `?from=questionnaire` (P3.4) — awaiting browser test.
- [ ] [CODE] N7 — Glossary `<Term>` wiring on questionnaire option labels — partially landed (strategy-family +
      strategy-archetype 2026-04-25); remaining: ml-directional, rules-directional, carry-yield, arbitrage,
      event-driven, perp, spot, sma, pooled, dart, im.
- [ ] [DOC] N8 — Phase 8 codex docs (9 files) still pending; Phase 9 + 10 + 11 will subsume some.
- [ ] [CODE] N9 — IM reporting cascade dropdowns landed 2026-04-25 (commit pending) at 2-level (family + archetype).
      Phase 11 extends this to 4-level with category top-level.
- [ ] [INFRA] N10 — Verify `strategy-store-{cefi,defi,tradfi}-central-*` buckets are accessible to the Next.js API
      route's service account when deployed (currently uses ADC for local dev).
- [ ] [DOC] N11 — Add `instruments-service` parquet schema to codex (currently only InstrumentDefinition Pydantic model
      is documented).
