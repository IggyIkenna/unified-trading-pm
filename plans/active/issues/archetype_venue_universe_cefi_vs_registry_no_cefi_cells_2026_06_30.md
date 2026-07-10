---
doc_type: issue
title: Carry archetypes list CEFI venues in venue_universe but ARCHETYPE_CAPABILITY_REGISTRY has no CEFI cells
summary:
  Two carry archetype codex docs declare CEFI venues (BYBIT/OKX/DERIBIT) in their venue_universe frontmatter while
  ARCHETYPE_CAPABILITY_REGISTRY has no CEFI capability cells for them — a codex↔registry contradiction the two-sided
  audit flags. Surfaced (not introduced) by the 2026-06-30 frontmatter canonicalization, which reflowed a block-list
  venue_universe to the inline form the audit parser can read.
status: resolved
nature: notes
asset_group: [cefi, defi]
stage: [strategy]
repos: [strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [archetype, venue-universe, capability-registry, two-sided-audit, data-correctness]
related: [../../archive/2026_06/frontmatter_full_corpus_coverage_2026_06_30.md]
created: 2026-06-30
parent_epic: strategy_master
priority: P2
source:
  [
    two-sided prospectus-vs-codex audit (scripts/openapi/audit_prospectus_vs_codex.py) — venue-category contradictions,
    surfaced by frontmatter canonicalization in frontmatter_full_corpus_coverage_2026_06_30 (codex@0b019a8b4),
  ]
assigned_vm: NA
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by: "unified-api-contracts@7f20bdee63903e4d30736ad59229a392dc33958a — see Resolution section below"
---

## What I found

The two-sided audit (`check_two_sided_audit.py`) reports two **venue-category contradictions**:

| archetype              | codex `venue_universe` (CEFI venues)                  | registry says                                                |
| ---------------------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| `CARRY_BASIS_PERP_INV` | AAVE, MORPHO, HYPERLIQUID, **BYBIT**                  | `ARCHETYPE_CAPABILITY_REGISTRY` has no CEFI capability cells |
| `CARRY_STAKED_BASIS`   | LIDO, …, **DERIBIT, BYBIT, OKX**, UNISWAP_V3, JUPITER | `ARCHETYPE_CAPABILITY_REGISTRY` has no CEFI capability cells |

`CARRY_BASIS_PERP_INV` was already visible (baseline = 1). `CARRY_STAKED_BASIS` is the **new** one (baseline 1 → 2): its
`venue_universe` was a YAML **block list**, which the audit's frontmatter parser does not read; the 2026-06-30
frontmatter canonicalization reflowed it to the inline `[...]` form, so the audit can now see the venues. **The
contradiction is real and pre-existing — it was masked by formatting, not caused by the reflow.**

## Why it matters

A staked-basis / inverse-perp carry strategy legitimately stakes on DeFi and hedges basis on **CEFI perps/options**
(BYBIT/OKX/DERIBIT) — so the CEFI venues in `venue_universe` look correct. The likely defect is the **registry side**:
`ARCHETYPE_CAPABILITY_REGISTRY` has no CEFI capability cells modelling the CEFI hedge leg for these archetypes. Either
the registry is missing those cells, or the `venue_universe` overstates the universe. Resolving it is a **strategy /
capability-registry domain decision**, not a frontmatter change.

## Recommended decision (strategy owner)

1. Decide the SSOT: should `CARRY_STAKED_BASIS` / `CARRY_BASIS_PERP_INV` have CEFI capability cells in
   `ARCHETYPE_CAPABILITY_REGISTRY` (add them) — or should the codex `venue_universe` drop the CEFI venues (correct the
   doc)? Then the two-sided audit baseline drops back toward 0.
2. Until then this is tracked debt; the two-sided audit baseline was set to 2 (2026-06-30) to reflect the now-visible
   pre-existing contradiction (NOT new debt introduced by code) — see `two_sided_audit_baseline.yaml`.

## Resolution (2026-07-10)

Operator decision (2026-07-10 instruments-audit dispatch, decision #7): **registry catches up to the codex claim** — add
the missing CEFI cells rather than pruning `venue_universe`.

Real registry location:
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/ archetype_capability_manifest.json` (loaded into
`ARCHETYPE_CAPABILITY_REGISTRY` at import by `archetype_capability.py`; hand-edit the committed JSON, then
`scripts/generate_archetype_capability_manifest.py --write` canonicalises formatting/validates via the Pydantic schema
round-trip).

Added, matching the shape of the sibling `CARRY_BASIS_PERP` / `CARRY_STAKED_BASIS_DATED` CEFI cells:

- `CARRY_BASIS_PERP_INV` — new `CEFI` / `perp` cell, `venue_ids: [hyperliquid, bybit]` (matches the codex doc's "CeFi
  PRIMARY: Hyperliquid; BACKUP: Bybit ≤50% notional cap" hedge-leg description).
- `CARRY_STAKED_BASIS` — new `CEFI` / `perp` cell, `venue_ids: [deribit, bybit, okx]` (matches the codex venue matrix:
  Deribit + Bybit UTA have live catalog slots; OKX wstETH acceptance is confirmed in `venue_collateral.py` with catalog
  slot generation pending — noted in the cell's `notes`).

Verified real (not smoke-tested):

- `check_two_sided_audit.py` contradiction count: **2 → 0** (re-baselined; `two_sided_audit_baseline.yaml` updated).
- New regression test `test_carry_staked_basis_and_perp_inv_have_cefi_cells` in
  `unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py` — 17/17 tests in that module
  pass; sibling `tests/unit/test_archetype_capability_may_23_coverage.py` (46/46) unaffected.
- `generate_archetype_capability_manifest.py` (no `--write` needed — hand-edit was already canonical) confirms
  byte-identical round-trip through the Pydantic schema.
- ruff + basedpyright clean on both touched files.

Shipped: `unified-api-contracts@7f20bdee63903e4d30736ad59229a392dc33958a` (quickmerge, scoped to the manifest + test
file only — landed on `live-defi-rollout`).

**Discovered but explicitly OUT OF SCOPE for this fix** — do not conflate with the above: the UAC→UI capability-matrix
sync (`unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh --write`) is independently drifted and
regenerating `unified-trading-system-ui/lib/architecture-v2/coverage.ts` right now would **break the UI TypeScript
build** — the sync script emits `import type { ... VenueCategoryV2 } from "./enums"` but the UI's
`lib/architecture-v2/enums.ts` still only exports the older 5-member `VenueAssetGroupV2` (no `CROSS_CATEGORY`). This
predates this fix (UI `coverage.ts` last synced 2026-06-22 15:58 vs UAC manifest commits after that, e.g. `d924d67d` at
17:48 same day) — a separate cross-repo rename gap, not touched here. Needs its own issue/plan (rename
`VenueAssetGroupV2` → `VenueCategoryV2` in UI enums.ts + add `CROSS_CATEGORY` + re-sync coverage.ts + UI typecheck)
before the sync script can be safely re-run.
