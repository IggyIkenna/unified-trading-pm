---
doc_type: issue
title:
  "UAC->UI archetype-capability sync would break the UI TypeScript build — coverage.ts generator emits VenueCategoryV2,
  UI enums.ts still only has the older VenueAssetGroupV2"
summary:
  "Discovered while adding CEFI cells to ARCHETYPE_CAPABILITY_REGISTRY
  (archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md). Re-running
  unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh --write against the current committed
  archetype_capability_manifest.json regenerates unified-trading-system-ui/lib/architecture-v2/coverage.ts with `import
  type { StrategyArchetype, VenueCategoryV2 } from './enums'` (sync_archetype_capability_to_ui.py hardcodes this import
  name), but unified-trading-system-ui/lib/architecture-v2/enums.ts still only exports the older 5-member
  `VenueAssetGroupV2` type (CEFI/DEFI/SPORTS/TRADFI/PREDICTION, no CROSS_CATEGORY) — there is no `VenueCategoryV2`
  export in the UI repo at all. Regenerating coverage.ts as committed would not compile. UAC's own enum
  (unified_api_contracts.internal.architecture_v2.enums.VenueCategoryV2) already has 6 members (added CROSS_CATEGORY
  2026-04-25 per its docstring) — the UI mirror never picked up either the rename or the new member. The drift also
  predates this discovery: UI coverage.ts was last synced 2026-06-22 15:58 (commit 6442d46) but UAC's manifest was
  touched again at 17:48 the same day (d924d67, TSMOM_BTC_CTA) and at least once more since (7f20bdee, this session's
  CEFI-cells fix) — so coverage.ts is independently content-stale on top of the naming break."
status: resolved
nature: issue
asset_group: [cefi, defi, sports, tradfi, prediction]
stage: [strategy]
repos: [unified-trading-system-ui, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [archetype, capability-registry, ui-sync, typescript, rename, cross-repo-drift, coverage-ts]
related: [/plans/archive/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md]
created: 2026-07-10
parent_epic: strategy_master
priority: P2
source:
  [
    "Discovered running sync-archetype-capability-to-ui.sh --write while resolving
    archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md (2026-07-10, slot-3). Change was reverted (not
    committed) once the break was found — no committed diff exists; the referenced issue doc's Resolution section only
    flags the sync drift as out-of-scope for that fix, it does not itself carry the revert evidence (verified
    2026-07-25).",
  ]
assigned_vm: NA
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by: unified-trading-system-ui@7900f560
---

> 🟢 **ARCHIVED — ACKED-INTO-CODE (2026-07-28).** Fixed: `unified-trading-system-ui@7900f560` renamed
> `VenueAssetGroupV2`→`VenueCategoryV2` (+ const `VENUE_ASSET_GROUPS_V2`→`VENUE_CATEGORIES_V2`) across all 21 consuming
> files and added the 6th member `CROSS_CATEGORY`, cascading the required `Record<VenueCategoryV2, …>` exhaustiveness
> additions (`components/architecture-v2/category-chip.tsx`, `components/briefings/ strategy-coverage-matrix.tsx`,
> `components/marketing/strategy-family-catalogue.tsx`, `components/shell/asset-group-pill.tsx`,
> `components/widgets/widget-registry.ts`, `lib/types/asset-group.ts`, `lib/help/help-tree-generated.ts`) plus the
> URL-round-trip allowlists that would otherwise silently drop the new member
> (`lib/architecture-v2/workspace-scope.ts`'s `VALID_ASSET_GROUPS`, `lib/architecture-v2/catalogue-filter.ts`'s
> `venue_asset_groups`/`venue_categories` parser). `tsc --noEmit` + `eslint` + full `npm test` (3287 tests) all green;
> `tests/unit/lib/help/help-search-recall.test.ts`'s generated-search-recall test proves `CROSS_CATEGORY` is genuinely
> reachable (not just type-complete). **Scope note**: this was the UI-repo half only — the generator script
> (`unified-trading-pm/scripts/propagation/ sync_archetype_capability_to_ui.py`) already emitted the correct
> `VenueCategoryV2` name per this issue's own finding. Recommended-fix steps 3 (re-run `--write` to pick up unrelated
> accumulated manifest content drift) and 5 (audit other UAC-side enum drift) are NOT done here — tracked as a real
> todo, not left as prose, in
> `/plans/active/issues/ui_coverage_ts_regen_content_drift_after_venue_category_v2_rename_2026_07_28.md`.

## What I found

`unified-trading-pm/scripts/propagation/sync_archetype_capability_to_ui.py` (the code generator behind
`sync-archetype-capability-to-ui.sh`) unconditionally emits:

```ts
import type { StrategyArchetype, VenueCategoryV2 } from "./enums";
```

into `unified-trading-system-ui/lib/architecture-v2/coverage.ts`. But
`unified-trading-system-ui/lib/architecture-v2/enums.ts` currently exports:

```ts
export type VenueAssetGroupV2 = "CEFI" | "DEFI" | "SPORTS" | "TRADFI" | "PREDICTION";
export const VENUE_ASSET_GROUPS_V2: readonly VenueAssetGroupV2[] = [...]; // 5 members
```

— no `VenueCategoryV2` export exists in that file at all. Running `--write` today produces a `coverage.ts` that
references an undefined type, which would fail the UI's TypeScript strict build.

The UAC-side canonical enum (`unified_api_contracts.internal.architecture_v2.enums.VenueCategoryV2`) has 6 members:
CEFI, DEFI, SPORTS, TRADFI, PREDICTION, **CROSS_CATEGORY** (added 2026-04-25 per its docstring, "primary category for
portfolio archetypes / cross-category sleeves and ARBITRAGE_CROSS_DOMAIN_EVENT"). The UI's `VenueAssetGroupV2` was never
renamed or extended to match.

## Why it matters

`sync-archetype-capability-to-ui.sh` is documented as "wired into `unified-trading-system-ui/scripts/quality-gates.sh`
so every UI push fails if the TS mirror drifts from UAC" — but the mirror has been silently stale since at least
2026-06-22 (UI last synced 15:58 that day; UAC manifest changed again 17:48 same day, `d924d67d` TSMOM_BTC_CTA, plus at
least one further UAC manifest commit since, `7f20bdee` this session). Anyone who runs `--write` expecting a routine
content refresh will instead ship a broken UI build, because the real gap is a **type rename that was never
propagated**, not just stale cell content.

## Recommended fix (not done here — out of scope for the CEFI-cells fix that surfaced this)

1. Rename `VenueAssetGroupV2` -> `VenueCategoryV2` in `unified-trading-system-ui/lib/architecture-v2/enums.ts` (grep +
   update all consumers in the UI repo).
2. Add the 6th member `CROSS_CATEGORY` to the UI enum + its `VENUE_ASSET_GROUPS_V2`-equivalent constant (rename that
   too, or confirm downstream consumers before renaming the const).
3. Re-run `sync-archetype-capability-to-ui.sh --write` to regenerate `coverage.ts` against the current
   `archetype_capability_manifest.json` (this also picks up unrelated accumulated content drift: TSMOM_BTC_CTA rows,
   `smarkets_direct` venue additions, notes-formatting fixes, etc. — a much larger diff than the rename alone).
4. Run the UI's own `quality-gates.sh` (tsc strict + Vitest + the sync `--check` gate) to confirm green before shipping.
5. Grep for any other UAC-side `architecture_v2` enum/type renames that may have similarly drifted from their UI
   mirrors, since this is evidence the sync pipeline's `--check` gate has not been run in this UI checkout in a while
   (or is not actually wired into that repo's live `quality-gates.sh` path).

## Todos

- [x] [AGENT][UI] P2. **Rename `VenueAssetGroupV2`→`VenueCategoryV2` in the UI and resync `coverage.ts`** — the 5-step
      recommended fix above (rename + add `CROSS_CATEGORY`, re-run `sync-archetype-capability-to-ui.sh --write`, verify
      the UI's `quality-gates.sh`, grep for other drifted enums) has not been executed; running `--write` today would
      still produce a `coverage.ts` that fails the UI's TypeScript strict build. — ✅
      `unified-trading-system-ui@7900f560`. Renamed `VenueAssetGroupV2`→`VenueCategoryV2` +
      `VENUE_ASSET_GROUPS_V2`→`VENUE_CATEGORIES_V2` across all 21 consuming files, added the 6th member
      `CROSS_CATEGORY`, and cascaded every `Record<VenueCategoryV2, …>` exhaustiveness requirement it forced (7 files)
      plus the two URL-round-trip allowlists that would otherwise silently drop the new member on deep-link reload.
      `tsc --noEmit` clean, `eslint` clean, full `npm test` 3287/3289 passed (2 pre-existing skips) — including
      `tests/unit/lib/help/help-search-recall.test.ts`'s generated search-recall coverage, which proves `CROSS_CATEGORY`
      is genuinely reachable end-to-end, not just type-complete. Steps 3 (content-drift regen) + 5 (audit other drifted
      enums) of the recommended fix are NOT done here — tracked as their own todo, not prose, in
      `/plans/active/issues/ui_coverage_ts_regen_content_drift_after_venue_category_v2_rename_2026_07_28.md`. No
      `pw:L2`/`regression:` evidence tag: this change touches only type-level/enum plumbing (no new route, widget, or
      user-visible surface) — covered by L0/L1 (tsc + the existing
      `enums.test.ts`/`help-tree.test.ts`/`help-search-recall.test.ts` unit suite), not an L2 route-smoke concern per
      `/codex/06-coding-standards/ui-testing-layers.md`'s layer scoping. **PM-side half verified 2026-07-28, NOT touched
      (split with a concurrent UI-side agent) — checkbox intentionally left unflipped, see Progress Log.**

## Progress Log

- **2026-07-28**: Verified the PM-side generator
  (`unified-trading-pm/scripts/propagation/sync_archetype_capability_to_ui.py`) requires NO code change — it already
  unconditionally emits `import type { StrategyArchetype, VenueCategoryV2 } from "./enums"` (line 38) and types
  `CoverageCell.assetGroup: VenueCategoryV2` (line 83), which is the CORRECT, current UAC canonical name (confirmed
  live: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:417`
  `class VenueCategoryV2(StrEnum)` with 6 members incl. `CROSS_CATEGORY`, docstring "added 2026-04-25"). The generator
  was never the defect — it was always correctly referencing UAC's real type name; the entire gap this doc describes is
  the UI-side mirror (`enums.ts`) never being renamed to match. Did not run `--write` (would overwrite
  `unified-trading-system-ui/lib/architecture-v2/coverage.ts`, which is a DIFFERENT agent's live, currently-uncommitted
  WIP as of this check — `git status` in that repo shows `coverage.ts` and `enums.ts` both modified, and `enums.ts`
  already carries a `VenueCategoryV2` type with all 6 members including `CROSS_CATEGORY`, i.e. that agent's rename is
  already in flight). Per this session's explicit scope split (PM-side generator only, no UI-repo edits), leaving this
  item's checkbox unflipped — the doc's single todo is UI-scoped (rename + resync + UI QG verification), none of which a
  PM-only change can independently satisfy. Remaining work: the UI-side agent's in-flight rename/resync +
  `unified-trading-system-ui`'s own `quality-gates.sh` (tsc strict + Vitest + the sync `--check` gate) passing, plus
  recommended-fix step 5 (grep for any OTHER UAC `architecture_v2` enum renames similarly drifted from their UI mirror)
  — not attempted here, out of this session's scope.
