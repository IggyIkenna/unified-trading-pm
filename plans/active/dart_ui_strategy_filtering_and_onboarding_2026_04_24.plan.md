---
title: DART UI — Strategy Dimension Filtering, Permission Tiers, Client Onboarding & Codex Integration
branch: live-defi-rollout
locked_by: live-defi-rollout
locked_since: 2026-04-24
repos_affected:
  - unified-trading-system-ui
  - unified-api-contracts
  - unified-trading-pm
status: in_progress
current_readiness: C0
target_readiness: C5
---

# DART UI — Strategy Dimension Filtering, Permission Tiers, Client Onboarding & Codex Integration

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
  "desmond-signals-in": {
    /* same */
  },
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
