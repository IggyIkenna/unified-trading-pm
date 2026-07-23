---
doc_type: issue
title: >-
  UAC's codex↔registry archetype-parity tests resolve the PM codex checkout via a STALE global
  `UNIFIED_TRADING_WORKSPACE_ROOT` env var, not the live per-slot worktree — 3 false failures on every local
  full-workspace `quality-gates.sh` run, invisible to CI
summary: >-
  Discovered as a side effect of a sports Part-1 (1.3) UAC change
  (`sports_shard_enumeration_cartesian_blowup_2026_07_20.md`), unrelated to it. UAC's
  `tests/internal/unit/test_archetype_capability_manifest_parity.py`
  (`test_codex_markdown_has_section_for_every_registered_archetype`,
  `test_codex_markdown_family_groupings_match_uac_family_enum`,
  `test_codex_markdown_archetype_appears_under_correct_family_section`) resolve the PM's
  `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` via `_find_codex_markdown()`, which checks
  `$UNIFIED_TRADING_WORKSPACE_ROOT` FIRST before falling back to an ancestor-directory walk from `__file__`. On this dev
  box `UNIFIED_TRADING_WORKSPACE_ROOT=/Users/ikennaigboaka/Code/unified-trading-system-repos` — the
  pre-per-slot-worktree ROOT checkout, not any `.tabs/N/` slot clone — and that root `unified-trading-pm` checkout is
  pinned at commit `017940b1` (2026-07-06), 16 days stale versus `origin/live-defi-rollout` (`4780c40f`, 2026-07-22) and
  every live slot checkout. The root checkout's codex doc has 8 `## Family N:` sections (no `## Family 9: Portfolio`)
  and is missing ~29 `### N. \`ARCHETYPE\`` headers (all `VOL_*`, `MARKET_MAKING_*`, `PORTFOLIO_*`, `DEFI_LP_*`
  additions that landed on `origin` since 2026-07-06), so any local full-workspace `quality-gates.sh` run on ANY slot on
  this machine reproduces the same 3 failures — deterministically, not flakily — because they all share the one stale
  env var, not because of anything in the diff being gated. CI never catches this: `_find_codex_markdown()` returns
  `None` (skip) in an ephemeral CI container with no PM checkout, so this parity check is effectively
  local-workspace-only and has apparently never been exercised against a fresh checkout since the per-slot-worktree
  migration.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [tooling, ci-blind-spot, stale-checkout, workspace-root, archetype, codex-parity, false-failure]
related: [/plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md]
created: 2026-07-22
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data-pipeline
drift_direction: advance-code
depends_on: []
resolved_by: uac@68c4c371dfeab875ee8d78b1b6882d631614c570
locked_by:
source:
  [
    "surfaced running `unified-api-contracts` full `quality-gates.sh` while shipping
    sports_shard_enumeration_cartesian_blowup_2026_07_20.md step 1.3 (2026-07-22); confirmed unrelated to that change by
    inspecting `_find_codex_markdown()` resolution order and comparing the root checkout's commit SHA against
    origin/live-defi-rollout",
  ]
---

# UAC archetype↔codex parity tests read a stale root checkout, not the live slot worktree

## Root cause

`unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py::_find_codex_markdown()` checks
`os.environ["UNIFIED_TRADING_WORKSPACE_ROOT"]` **before** falling back to an ancestor-walk from `__file__`. On this dev
box that env var is set to the workspace root (`/Users/ikennaigboaka/Code/unified-trading-system-repos`), which predates
the per-slot-worktree model (`/codex/05-infrastructure/per-tab-worktrees.md`) and is not kept in sync with any
`.tabs/N/` slot clone. Its `unified-trading-pm` copy is pinned at `017940b1` (2026-07-06); the live slot checkouts and
`origin/live-defi-rollout` are at `4780c40f` (2026-07-22, 16 days / ~30 archetypes ahead).

## Measured effect

Any agent running `unified-api-contracts`'s full `bash scripts/quality-gates.sh` (or `--no-fix`) in **any** slot
reproduces 3 deterministic failures, independent of what they changed:

- `test_codex_markdown_has_section_for_every_registered_archetype` — 29 archetypes missing from the stale copy's headers
  (`DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT`, `MARKET_MAKING_INVENTORY_SKEW`, `MARKET_MAKING_ML_LEAN`,
  `MARKET_MAKING_PASSIVE_SPREAD`, `MARKET_MAKING_PREDICTION`, `MARKET_MAKING_QUEUE_MICROSTRUCTURE`,
  `PORTFOLIO_FACTOR_ALLOCATION`, `PORTFOLIO_MULTI_STRATEGY`, `PORTFOLIO_RISK_PARITY`, `PORTFOLIO_TACTICAL_OVERLAY`, 17x
  `VOL_*`).
- `test_codex_markdown_family_groupings_match_uac_family_enum` — stale copy has 8 `## Family N:` sections, registry now
  declares 9 (`StrategyFamily.PORTFOLIO` missing).
- `test_codex_markdown_archetype_appears_under_correct_family_section` — first archetype lookup that misses
  (`VOL_ARB_RV_IV`) fails the same way.

**Verified NOT caused by**: the sports UAC change these tests were incidentally run alongside
(`is_bookmaker_league_covered_exact`, registry export) — neither touches
`unified_api_contracts/internal/architecture_v2/*` or the codex file. **Verified NOT a race** with a concurrent sibling
agent editing the same slot-3 checkout at the time (their diff was scoped to `market_data_categories.py` /
`test_sports_prediction_contracts.py`, also unrelated). **Verified pre-existing**: `origin/live-defi-rollout`'s own
`quality-gates-v2` CI has been green through 2026-07-22T00:30Z — because `_find_codex_markdown()` returns `None` (no PM
checkout in the ephemeral CI container) and the tests self-skip there. The live slot-3 `unified-trading-pm` checkout
(`.tabs/3/unified-trading-pm`, `4780c40f`) already has all 9 families / all archetypes documented — only the stale root
checkout is behind.

## Recommended next step (not done here — out of scope for the sports Part-1 task this surfaced under)

Two independent fixes, either sufficient alone:

1. **Update the stale root checkout**
   (`cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm && git pull --ff-only origin live-defi-rollout`)
   — fixes it today, but will drift stale again since nothing keeps that root copy current post-migration.
2. **Fix `_find_codex_markdown()`'s resolution order** to prefer the ancestor-walk (which finds the caller's OWN live
   slot checkout) over the global env var, or drop `UNIFIED_TRADING_WORKSPACE_ROOT` reliance entirely now that per-slot
   worktrees are the standing model — the env var made sense pre-migration when there was one shared checkout, not N.

No manifest/GCS/prod data involved; this is a pure local dev-environment / test-harness fix.

## Resolution (2026-07-22, independently hit by slot-1, same root cause)

Implemented fix #2 (`_find_codex_markdown()`'s resolution order) rather than #1 — a stale-checkout `git pull` only fixes
this machine's outer root copy once and drifts again, since nothing keeps it current; the resolution-order fix is
permanent and applies to every slot/machine that ever has this env var pointed above the per-slot worktree root.

**Change**:
`unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py::_find_codex_markdown()` now
tries the ancestor-directory walk from `__file__` FIRST (always resolves to the CALLER's own live, synced slot checkout
under the per-slot-worktree model) and falls back to `$UNIFIED_TRADING_WORKSPACE_ROOT` only if that walk finds nothing
(e.g. a genuinely isolated CI container with no sibling PM checkout at all — the one case the env var fallback still
legitimately covers). Verified: all 17 tests in the file pass locally post-fix, including the 3 that were failing
(`test_codex_markdown_has_section_for_every_registered_archetype`,
`test_codex_markdown_family_groupings_match_uac_family_enum`,
`test_codex_markdown_archetype_appears_under_correct_family_section`) — confirming the live slot-1 checkout already had
all 9 families / 53 archetypes documented (matching this doc's own note that slot-3's checkout was already current), it
was purely a resolution-order bug, zero doc content was ever missing or needed writing.

Did NOT touch the stale outer-root `unified-trading-pm` checkout itself (left as-is — orphaned pre-Path-B debris, out of
scope for this fix and not blocking anything now that the test no longer reads it first).
