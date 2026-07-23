---
name: DART Terminal vs. DART Research — Tile Split + Instrument-Type View Gating
status: active
owner: ikenna
created: 2026-04-28
locked_by: live-defi-rollout
locked_since: 2026-04-28
codex_ref: /codex/14-playbooks/dart/dart-terminal-vs-research.md
---

# DART Terminal vs. DART Research — Tile Split + Instrument-Type View Gating

## Context

DART today renders as a single dashboard tile with chip-level navigation. Research and Promote chips are
padlocked-visible for Signals-In users. Customer-facing framing has always been **DART Terminal** (Signals-In +
DART-Full) and **DART Research** (DART-Full only) as two distinct products. This plan splits DART into two top-level
dashboard tiles, adds dynamic instrument-type view gating across all trading sub-routes, surfaces the orphaned
`/services/research/signals` page, restores the deleted research-side allocator workbench (distinct from the operational
IM allocator), and ships a comprehensive Playwright matrix per persona.

User decisions:

- DART Research is a **separate top-level tile** padlocked for Signals-In with a feature-preview card.
- FOMO mode (catalogue Explore-tab teaser strategies expanding view-gating) is **default for non-DART-Full users**, not
  a third tier.
- Surface the orphan `/services/research/signals` page; verify each existing research page renders correctly.
- Restore the deleted allocator dashboard from `dfc8c5ba^` under DART Research → Allocate (research-time workbench,
  distinct from `/services/investment-management/allocator` which stays as the operational surface).
- Promote Feature ETL + Features prominently under Develop section.
- Strategy selection in DART Research uses **family → archetype → asset_group** hierarchy (research lens).

## Phased DAG

```
Phase A (codex SSOT + plan, READ-ONLY)  ─┐
                                          ├─→ Phase B (two-tile dashboard split) ─┐
Phase A.2 (orphan re-audit)             ─┘                                          │
                                                                                   ├─→ Phase F (Playwright matrix) ─→ Phase G (verify, no quickmerge)
Phase C (instrument-type lib + gate ext)─┐                                          │
                                          ├─→ Phase D (apply gates + surface orphans + restore allocator + restructure hierarchy) ─┘
Phase E (FOMO mode default-on)          ─┘
```

## Todos

### Phase A — Audit + SSOT (PM repo)

- [x] [HUMAN] P0. Codex SSOT written at `/codex/14-playbooks/dart/dart-terminal-vs-research.md` — full route inventory,
      tile ownership, persona × tile × view matrix, instrument-type derivation chain, FOMO mode behavior. Sourced from
      actual code, not 2026-03-21 wishlist.
- [x] [HUMAN] P0. Re-audit orphan list against actual code. **Result: 1 orphan** (`/services/research/signals`), not 14.
      The 2026-03-21 archived plan listed `/services/research/ml/experiments` etc. as wishlist items that never shipped.
- [x] [HUMAN] P0. Plan SSOT written at `plans/active/dart_terminal_research_split_2026_04_28.plan.md` (this file).

### Phase B — Two-tile dashboard split (UI repo)

- [ ] [AGENT] P0. Edit `lib/config/services.ts`:
  - Update `DashboardTileId` from `"dart" | ...` to `"dart-terminal" | "dart-research" | ...`
  - Replace single `dart` SERVICE_REGISTRY entry with `dart-terminal` (id, requiredEntitlements: `execution-basic` OR
    `execution-full`) and `dart-research` (requiredEntitlements: `strategy-full` AND `ml-full`).
  - Define DART Terminal sub-routes: Terminal, Observe, Strategy Catalogue, Signal Intake, Trading sub-domains.
  - Define DART Research sub-routes by lifecycle stage: Overview / Develop / Train / Validate / Allocate / Promote.
- [ ] [AGENT] P0. Edit `lib/auth/persona-dashboard-shape.ts`:
  - Update `PERSONA_TILE_SHAPES` for every persona — split `dart` → `dart-terminal` + `dart-research`.
  - Signals-In personas: `dart-terminal: visible`, `dart-research: padlocked-visible`.
  - DART Full personas + admin (`["*"]`): both `visible`.
  - Update `PERSONA_SUBROUTE_SHAPES` correspondingly.
- [ ] [AGENT] P0. Edit `components/shell/service-tabs.tsx`:
  - Split `BUILD_TABS` (research tabs) into `RESEARCH_TABS` with sub-sections (Develop / Train / Validate / Allocate /
    Promote).
  - Add new `TERMINAL_TABS` with Terminal-only chips (Terminal, Observe, Strategy Catalogue, Signal Intake).
  - Move Promote (`/services/research/strategy/{candidates,handoff}`) into RESEARCH_TABS Promote section.
  - Remove `RESEARCH_TABS = BUILD_TABS` alias at line 665 (clean break, no shim).
- [ ] [AGENT] P0. Render two tiles on dashboard at `app/(platform)/dashboard/page.tsx`:
  - Padlocked DART Research tile shows feature preview (3 sample research surfaces with locks) + "Upgrade to DART Full"
    CTA.
  - Reuse existing padlock styling from `padlocked-visible` chip pattern.
- [ ] [AGENT] P0. Update `__tests__/dashboard-subroute-chips.test.tsx`:
  - Cover both tiles for every persona.
  - Assert no fall-through to old `dart` key.
- [ ] [AGENT] P0. Commit + push.

### Phase C — Instrument-type derivation library + gate extension (UI repo)

- [ ] [AGENT] P0. Create `lib/architecture-v2/user-instrument-types.ts`:

  ```ts
  export type DerivationMode = "reality" | "fomo";
  export async function instrumentTypesForUser(
    user: AuthPersona,
    mode: DerivationMode = "reality"
  ): Promise<{ instrumentTypes: Set<string>; assetGroups: Set<StrategyCategory> }>;
  export async function assetGroupsForUser(
    user: AuthPersona,
    mode: DerivationMode = "reality"
  ): Promise<Set<StrategyCategory>>;
  export async function teaserStrategiesForUser(user: AuthPersona): Promise<readonly string[]>;
  ```

  - Admin (`entitlements.includes("*")`): early bypass — return ALL.
  - Reality: filter `strategy_instruments.json` slots by `user.assigned_strategies`.
  - FOMO: reality + teaser-strategy slots (deterministic stable subset matching Strategy Catalogue Explore tab).

- [ ] [AGENT] P0. Extend `components/platform/page-entitlement-gate.tsx`:
  - Add props `requiredInstrumentTypes?: string[]` and `requiredAssetGroups?: StrategyCategory[]` and
    `derivationMode?: DerivationMode`.
  - Async check: `instrumentTypesForUser(user, mode)`.
  - Empty intersection → frosted-glass FOMO overlay + upsell CTA.
  - Admin bypass already in place via `isAdmin()`.
- [ ] [AGENT] P0. Unit tests `__tests__/lib/architecture-v2/user-instrument-types.test.ts`:
  - admin → all instrument types.
  - desmond-dart-full reality → entitled-only.
  - desmond-dart-full + Signals-In tier-override → Signals-In subset.
  - elysium-defi-full → DEFI only.
  - elysium-defi → DEFI only (no ml/strategy-full).
  - FOMO mode → reality ∪ teaser instrument types.
- [ ] [AGENT] P0. Commit + push.

### Phase D — Apply gates + surface orphans + restore allocator + restructure hierarchy (UI repo)

- [ ] [AGENT] P0. Wrap each trading sub-domain page with `PageEntitlementGate`, `derivationMode="fomo"`:
  - `app/(platform)/services/trading/options/page.tsx` → `requiredInstrumentTypes: ["option", "future"]`
  - `app/(platform)/services/trading/sports/page.tsx` → `requiredAssetGroups: [SPORTS]`
  - `app/(platform)/services/trading/defi/{page,bundles,staking}.tsx` → `requiredAssetGroups: [DEFI]`
  - `app/(platform)/services/trading/predictions/page.tsx` → `requiredAssetGroups: [PREDICTION]`
  - Markets stays gated on `trading-common` only (instrument-agnostic).
- [ ] [AGENT] P0. Update trading sidebar `app/(platform)/services/trading/layout.tsx` (lines 50-65):
  - Auto-hide nav items whose `requiredInstrumentTypes` / `requiredAssetGroups` don't intersect
    `instrumentTypesForUser(user, "fomo")`.
  - Admin sees all (existing `isAdmin()` short-circuit).
- [ ] [AGENT] P0. Surface `/services/research/signals` (sole orphan) in RESEARCH_TABS Validate section. Verify the page
      renders correctly first.
- [ ] [AGENT] P0. Restore allocator dashboard under DART Research → Allocate (Research):
  - Recover `_components/allocator-dashboard.tsx` and `app/(platform)/services/research/strategy/allocator/page.tsx`
    from commit `dfc8c5ba^` via `git show dfc8c5ba^:<path>`.
  - New paths: `app/(platform)/services/research/allocate/page.tsx` and
    `app/(platform)/services/research/allocate/_components/allocator-research-dashboard.tsx` (renamed to disambiguate).
  - Wire to research-flavoured data: regime simulation runs, allocator-archetype backtests, shadow-vs-primary diff,
    directive history.
  - Gate via `PageEntitlementGate` requiring `strategy-full` + `ml-full`.
  - Do NOT modify `/services/investment-management/allocator/` or `/services/trading-platform/allocator/` — operational
    surfaces stay.
- [ ] [AGENT] P0. Promote Feature ETL + Features prominently in RESEARCH_TABS Develop section (already in BUILD_TABS
      today; move into Develop sub-section with appropriate icons).
- [ ] [AGENT] P0. Restructure DART Research strategy selection to **family → archetype → asset_group** hierarchy:
  - Affected: `/services/research/strategy/{families,catalog,overview}` + `/services/research/strategies`.
  - Top filter: family chip row (8 families from `STRATEGY_FAMILIES_V2`).
  - Within family: archetype list (from `ARCHETYPE_TO_FAMILY`).
  - Within archetype: asset_group filter chips (CEFI / DEFI / SPORTS / TRADFI / PREDICTION).
  - Within asset_group: instance list (per slot from `strategy_instruments.json`).
  - Add helper `instancesByFamilyArchetypeAssetGroup()` in `lib/architecture-v2/envelope-loader.ts` (extend, don't break
    existing exports).
  - Public catalogue `/services/strategy-catalogue` unchanged (asset_group-led).
- [ ] [AGENT] P0. Commit + push (one commit per restructure chunk).

### Phase E — FOMO mode default (UI repo)

- [ ] [AGENT] P0. Thread `derivationMode="fomo"` into trading-route gates by default; reality mode reserved for
      tile-level entitlement checks (Phase B).
- [ ] [AGENT] P1. Strategy Catalogue Explore tab teaser logic extracted into shared `teaserStrategiesForUser()` helper
      (Phase C.1) so view-gating uses the same source as the catalogue's existing Explore tab.
- [ ] [AGENT] P0. Commit + push.

### Phase F — Playwright + Vitest matrix (UI repo)

- [ ] [AGENT] P0. New spec `tests/e2e/playbooks/dart-tile-split.spec.ts` — for each persona (admin, internal-trader,
      im-desk-operator, admin-odum, desmond-dart-full, elysium-defi-full, elysium-defi, client-full, client-premium,
      client-data-only, prospect-dart-full, prospect-dart-signals-in, demo-signals-client, client-regulatory):
  - Sign in, land on `/dashboard`.
  - Assert presence/absence/padlock of DART Terminal + DART Research tiles per persona matrix.
  - Padlocked Research tile: feature-preview card + upgrade CTA, no clickable internal links.
  - Visible Research tile (DART Full + admin): clickable, leads to `/services/research/overview`.
- [ ] [AGENT] P0. New spec `tests/e2e/playbooks/instrument-type-view-gating.spec.ts`:
  - Per persona, navigate to each of `/services/trading/{options,sports,defi,predictions,markets}`.
  - Assert content vs FOMO overlay matches `instrumentTypesForUser()` derivation.
  - Cross-reference: elysium-defi-full sees DeFi but not Options. desmond-dart-full + Signals-In tier-override +
    carry-only assigned_strategies sees Markets but not Sports. Admin sees all.
- [ ] [AGENT] P0. New spec `tests/e2e/playbooks/tier-override-flip.spec.ts`:
  - Sign in as Desmond (default DART Full).
  - Trigger localStorage tier-override flip to Signals-In; reload — assert DART Research now padlocked, identity
    unchanged.
  - Repeat for Patrick (DeFi Full ↔ DeFi Base).
  - Verify FOMO behavior: Signals-In + teaser sports strategy unlocks Sports view.
- [ ] [AGENT] P0. Additional unit tests:
  - `__tests__/lib/auth/persona-dashboard-shape.test.ts` — every persona resolves to two distinct tile entries.
  - `__tests__/components/platform/page-entitlement-gate.test.tsx` — `requiredInstrumentTypes` honoured; admin bypasses.
- [ ] [AGENT] P0. Run full UI suite: `cd unified-trading-system-ui && CI=true npm test -- --run` and Playwright
      headless.
- [ ] [AGENT] P0. Commit + push (one commit per spec).

### Phase G — Verification (no quickmerge per user)

- [ ] [AGENT] P0. UI smoke build: `cd unified-trading-system-ui && npm run build`.
- [ ] [AGENT] P1. Manual Tier 0 smoke: `bash scripts/dev-tiers.sh --tier 0` — sign in as each persona via Firebase
      emulator, verify dashboard tile rendering, Research padlock state, trading sub-route gating, tier-override flip.
- [ ] [AGENT] P0. Quality gates Pass 1: `bash scripts/quality-gates.sh`.
- [ ] [HUMAN] P0. **No quickmerge** per user direction. Per-chunk pushes (already happening) replace quickmerge for this
      plan. UAT/prod deployment is a separate operator step.

## Critical files

### Modify

| File                                                                                                                                                                | Phase | Change                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------- |
| `unified-trading-system-ui/lib/config/services.ts`                                                                                                                  | B     | Split `dart` → `dart-terminal` + `dart-research` in DashboardTileId + SERVICE_REGISTRY      |
| `unified-trading-system-ui/lib/auth/persona-dashboard-shape.ts`                                                                                                     | B     | Update PERSONA_TILE_SHAPES + PERSONA_SUBROUTE_SHAPES                                        |
| `unified-trading-system-ui/components/shell/service-tabs.tsx`                                                                                                       | B     | Split BUILD_TABS → TERMINAL_TABS + RESEARCH_TABS; remove `RESEARCH_TABS = BUILD_TABS` alias |
| `unified-trading-system-ui/app/(platform)/dashboard/page.tsx`                                                                                                       | B     | Render two tiles; padlocked DART Research preview card                                      |
| `unified-trading-system-ui/components/platform/page-entitlement-gate.tsx`                                                                                           | C     | Add `requiredInstrumentTypes` + `requiredAssetGroups` + `derivationMode` props              |
| `unified-trading-system-ui/lib/architecture-v2/envelope-loader.ts`                                                                                                  | D     | Add `instancesByFamilyArchetypeAssetGroup()` helper                                         |
| `unified-trading-system-ui/app/(platform)/services/trading/{options,sports,defi/page,defi/bundles,defi/staking,predictions}/page.tsx`                               | D     | Wrap with `PageEntitlementGate`                                                             |
| `unified-trading-system-ui/app/(platform)/services/trading/layout.tsx`                                                                                              | D     | Auto-hide sidebar items                                                                     |
| `unified-trading-system-ui/app/(platform)/services/research/strategy/{families,catalog,overview}/page.tsx` + `app/(platform)/services/research/strategies/page.tsx` | D     | family → archetype → asset_group hierarchy                                                  |
| `unified-trading-system-ui/__tests__/dashboard-subroute-chips.test.tsx`                                                                                             | B     | Cover both tiles                                                                            |

### New

| File                                                                                                                            | Phase | Purpose                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------- |
| `unified-trading-system-ui/lib/architecture-v2/user-instrument-types.ts`                                                        | C     | `instrumentTypesForUser` + `assetGroupsForUser` + `teaserStrategiesForUser` |
| `unified-trading-system-ui/app/(platform)/services/research/allocate/page.tsx` + `_components/allocator-research-dashboard.tsx` | D     | Restored allocator workbench (research-side)                                |
| `unified-trading-system-ui/__tests__/lib/architecture-v2/user-instrument-types.test.ts`                                         | C+F   | Unit tests for derivation lib                                               |
| `unified-trading-system-ui/__tests__/lib/auth/persona-dashboard-shape.test.ts`                                                  | F     | Persona × tile coverage                                                     |
| `unified-trading-system-ui/__tests__/components/platform/page-entitlement-gate.test.tsx`                                        | F     | Gate component tests                                                        |
| `unified-trading-system-ui/tests/e2e/playbooks/dart-tile-split.spec.ts`                                                         | F     | Persona × tile Playwright matrix                                            |
| `unified-trading-system-ui/tests/e2e/playbooks/instrument-type-view-gating.spec.ts`                                             | F     | Persona × view gating Playwright                                            |
| `unified-trading-system-ui/tests/e2e/playbooks/tier-override-flip.spec.ts`                                                      | F     | Tier-override flip + FOMO unlock Playwright                                 |

### Do NOT modify

- `unified-trading-system-ui/app/(platform)/services/investment-management/allocator/` — operational allocator stays.
- `unified-trading-system-ui/app/(platform)/services/trading-platform/allocator/` — operational allocator stays.
- `unified-trading-system-ui/app/(platform)/services/strategy-catalogue/page.tsx` — public catalogue keeps asset_group →
  family → archetype hierarchy.
- `unified-trading-system-ui/app/api/catalogue/envelope/route.ts` — GCS proxy unchanged.

## Success criteria

1. Two tiles render on dashboard for every persona, with correct padlock state per the Phase 0 entitlement matrix.
2. `instrumentTypesForUser(user, "reality"/"fomo")` returns correct sets for all test personas.
3. Trading sub-routes (Options/Sports/DeFi/Predictions) gate correctly — render content for entitled instrument types,
   FOMO overlay otherwise.
4. `/services/research/signals` reachable from DART Research nav (DART Full + admin only).
5. Tier-override flip preserves identity (email/uid) and only flips entitlements + view-gating.
6. Admin (`entitlements: ["*"]`) sees every tile, every chip, every view, every research page — no overlays.
7. Operational allocator at `/services/investment-management/allocator` and `/services/trading-platform/allocator`
   continues to render unchanged for IM personas; restored research allocator at `/services/research/allocate` renders
   for DART Full + admin only.
8. Strategy selection in DART Research correctly renders family → archetype → asset_group hierarchy; public catalogue
   unchanged.
9. Playwright matrix green across all test personas × trading sub-routes × research pages.
10. UI smoke build green; quality-gates Pass 1 green.

## Cross-references

- SSOT codex doc: `/codex/14-playbooks/dart/dart-terminal-vs-research.md`
- Catalogue artefacts: `feedback_catalogue_gcs_artefacts.md` (memory)
- Public catalogue ordering rationale: `feedback_primary_category_first_class_axis.md` (memory)
- Allocator G2.10 split: commit `dfc8c5ba` in `unified-trading-system-ui`
