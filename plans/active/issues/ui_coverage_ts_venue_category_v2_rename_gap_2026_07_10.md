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
status: open
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
    committed) once the break was found — see that issue doc's Resolution section for the revert evidence.",
  ]
assigned_vm: NA
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by:
---

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
