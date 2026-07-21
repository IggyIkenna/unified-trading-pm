---
doc_type: issue
title:
  dart_ui_strategy_filtering_and_onboarding — 21 genuinely-orphaned residual items (UAC capability-manifest never
  regenerated, catalogue formatting gaps, asset_class rename incomplete)
summary: >-
  Splitting the archived dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md's 67 residual items between its
  two candidate successor plans surfaced that a real chunk has NO successor at all: the original hypothesis that
  capability_wizard_and_manifest_2026_06_11.md owns Phase 9's archetype-capability-taxonomy work is WRONG — that plan
  claims zero of it (confirmed by grep for bespoke/admin_assignment/REPORTING_ONLY etc., all zero hits). Two parallel
  research agents classified all 99 open items across the archived plan's 12 phases; this doc bundles the 21 that came
  back GENUINELY_ORPHANED (real, still-relevant work, no current owner) into one tracked doc per findings-triage rules,
  rather than 21 separate issue docs.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-system-ui]
scope: [engineer]
tags: [plan-discipline, dart, strategy-catalogue, capability-manifest, asset-class-rename]
related:
  [
    plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md,
    plans/active/capability_wizard_and_manifest_2026_06_11.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [batch4_strategy_ui_archived_plan_residuals-006]
resolved_by:
locked_by:
depends_on: []
---

# What I found

Two parallel read-only research agents each classified half of the archived
`dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`'s 99 open items (Phases 0-8: onboarding/questionnaire/
FOMO; Phases 9-11 + backlog: archetype-capability taxonomy, instruments resolver, catalogue rendering). Full per-item
evidence lives in the two agents' reports (not reproduced here); this doc groups the **21 GENUINELY_ORPHANED** items by
theme.

## A. UAC capability-manifest was never regenerated after the Phase 9 enum expansion (the big one, ~7 items)

`StrategyArchetype`/`StrategyFamily` gained 19 VOL archetypes, 10 MARKET_MAKING archetypes, and the whole PORTFOLIO
family back in April 2026 (enum-level, confirmed shipped, docstrings cite this plan by name). But
`unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` — the actual capability-cell data
consumers read — was **never regenerated**: it still has only 23 legacy archetypes, one `VOL_TRADING_OPTIONS` cell, zero
PORTFOLIO cells. `scripts/enumerate_envelope.py`'s own docstring admits the splits/bespoke logic is "currently mocked in
this script — not yet in the UAC capability manifest," citing this now-archived plan as the reason. Confirmed:
`capability_wizard_and_manifest_2026_06_11.md` (the plan the parent issue doc assumed owned this) claims ZERO of it —
its `ARCHETYPE_CAPABILITY_REGISTRY` overlap is about extracting the EXISTING registry into the openapi/manifest
exporter, not adding new archetype cells.

- Regenerate `archetype_capability_manifest.json` with real cells for all 19 VOL / 10 MM / 4 PORTFOLIO archetypes.
- Add a `bespoke_capable: bool` field to `ArchetypeCapabilityClaim`/`ArchetypeCapabilityCell` (currently only a
  script-local `_BESPOKE_CAPABLE` set in `enumerate_envelope.py`).
- Simplify `enumerate_envelope.py` once the above lands (its mocking logic becomes dead code).

## B. Admin strategy-assignment model was never built (~3 items)

- `admin_assignment.py` (`AdminStrategyAssignment` model) doesn't exist anywhere in `unified-api-contracts`.
- `AdminStrategyAssignmentTable.tsx` + `app/(ops)/admin/strategy-assignments/page.tsx` don't exist in the UI repo.
- `lib/entitlements/strategy-route.ts`'s resolvers (`resolveSlotAccess`/`resolveArchetypeAccess`) are a UI-side
  entitlement APPROXIMATION per the file's own docstring — there's no real admin-assignment backing store to project
  from. `canEnterTerminal()` in that same file is defined but never called anywhere (dead code — the terminal-blocking /
  "Reports access only — upgrade for terminal" UX was never wired).

## C. `AssetClass` → `AssetGroup` rename never executed repo-wide (~4 items)

The rename direction is set (newer code — `envelope-loader.ts`, `EnvelopeBrowser.tsx`,
`lib/architecture-v2/ terminology.ts` — already uses `assetGroup`/`ASSET_GROUP`), but the actual sweep never ran:
`AssetClass` is still live in ~20 UAC Python files (`_instrument_enums.py`, `canonical/crosscutting/ledger/_enums.py`,
`internal/reference/instrument.py`, ...) and ~19+15 UI files/identifiers, plus "asset class" prose in marketing content.
Tied together: codex terminology sweep (P11.1.4) can't happen until the code-level rename does.

## D. Strategy-catalogue UI formatting gaps (~3 items, Phase 2)

`lib/strategy-display.ts`'s formatters (`formatFamily`/`formatArchetype`/`formatSlotLabel`) are NOT applied everywhere
the plan required:

- `StrategyCatalogueSurface.tsx`'s `AdminUniverseGrid` renders raw `{instance.family}` / `{instance.archetype}`
  unformatted (only `getArchetypePlanTier` is imported, not the display formatters).
- `components/signal-broadcast/signal-history-table.tsx` renders raw `{emission.slot_label}` (no `formatSlotLabel`).
- `app/(ops)/admin/strategy-universe/page.tsx`'s admin table shows raw `instance.instanceId`, no slot-label column at
  all.
- The phase's own success gate ("zero raw underscore identifiers visible to clients") is not met.

## E. Demo persona → instrument hydration built but never wired (~2 items, Phase 10)

`lib/auth/derive-persona-instruments.ts` implements exactly the spec'd `derivePersonaInstruments(persona)` and has a
real regression test (`tests/unit/lib/auth/demo-provider-instruments.test.ts`). But `personaToAuthUser()` in
`demo-provider.ts` is still synchronous and never calls it; `AuthUser` has no `instruments` field. The
`QUESTIONNAIRE_PRESEEDS` mock object the cleanup step was supposed to remove is still there (`demo-provider.ts: 90-143`,
unremoved).

## F. Other orphans (~2 items)

- `enumerate_envelope.py`/`enumerate_catalogue.py` aren't wired into `scripts/dev/dev-start.sh` (N1 from the archived
  plan's trailing backlog).
- Phase 3's `seedFiltersFromQuestionnaire()` has no `instrument_types` passthrough — `StrategyCatalogueFilter` has zero
  `instrumentType` dimension.

# Why it matters

Item A (the capability-manifest regeneration gap) is the highest-leverage one: it means the capability wizard, the
prospectus generator, and any consumer reading `archetype_capability_manifest.json` as the archetype-coverage SSOT are
all working off data that's 3 months stale relative to the actual enum surface — 29 of 52+ archetypes have NO capability
cell at all. Items B/C are real, scoped, still-wanted product work with zero current owner. Items D/E/F are smaller
UI-polish gaps.

# Recommended decision

File as a standalone P3 tracking doc (this one) rather than force-fitting into either successor plan, since neither
`marketing_site_three_route_consolidation` nor `capability_wizard_and_manifest` actually claims this scope. A future
plan-authoring pass can pull items A-C into a real "capability manifest v2 / admin assignment model" plan when someone
has bandwidth; items D-F are small enough to fold into whichever plan next touches `StrategyCatalogueSurface.tsx` /
`demo-provider.ts`.

## Todos

- [ ] [BACKEND] P2. Regenerate `archetype_capability_manifest.json` with real cells for the 19 VOL / 10 MM / 4 PORTFOLIO
      archetypes added in Phase 9 (currently only 23 legacy archetypes have cells); add `bespoke_capable: bool` to
      `ArchetypeCapabilityClaim`. (repo: unified-api-contracts)
- [ ] [BACKEND] P3. Build the `admin_assignment.py` (`AdminStrategyAssignment`) model + wire it as the real backing
      store for `lib/entitlements/strategy-route.ts`'s resolvers (currently a UI-side approximation with no backend).
      Build `AdminStrategyAssignmentTable.tsx` + `app/(ops)/admin/strategy-assignments/page.tsx`. Wire
      `canEnterTerminal()` (currently dead code) into the actual terminal entry path. (repo: unified-api-contracts,
      unified-trading-system-ui)
- [ ] BLOCKED-SUPERSEDED [CODE] P3. ~~Execute the `AssetClass` → `AssetGroup` rename repo-wide~~ — SUPERSEDED
      2026-07-21: the real blast radius is 9+ repos (not 2), touches a persisted-schema-adjacent field, and risks
      conflating two distinct `AssetClass` enums (domain vs. `LedgerAssetClass`). See
      `plans/active/issues/asset_class_to_asset_group_rename_scope_underestimated_2026_07_21.md` (the investigation) and
      `plans/active/asset_class_to_asset_group_rename_2026_07_21.md` (the dedicated 6-todo phased plan that owns this
      work now — human plan, `assigned_vm: NA`, pending operator dispatch decision). Non-dispatchable — do not execute
      this line as scoped. (repo: unified-api-contracts, unified-trading-system-ui)
- [ ] [CODE] P3. Apply `lib/strategy-display.ts` formatters (`formatFamily`/`formatArchetype`/`formatSlotLabel`) in
      `StrategyCatalogueSurface.tsx`'s `AdminUniverseGrid`, `signal-history-table.tsx`, and
      `admin/strategy-universe/page.tsx` — currently render raw underscore identifiers. (repo:
      unified-trading-system-ui)
- [ ] [CODE] P3. Wire `derivePersonaInstruments()` into `personaToAuthUser()` (make it async, populate a new
      `AuthUser.instruments` field); remove the now-redundant `QUESTIONNAIRE_PRESEEDS` mock once wired. (repo:
      unified-trading-system-ui)

## Codex SSOTs

`codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`,
`codex/06-coding-standards/ strategy-display-conventions.md`.
