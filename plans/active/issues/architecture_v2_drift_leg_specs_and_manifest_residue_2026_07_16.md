---
doc_type: issue
title:
  architecture_v2 strategy-archetype subsystem still has live DRIFT venue references (leg specs, capability manifest,
  backtest scenarios) — the Solana perp-DEX cull did not reach it
summary:
  'While closing the "orphaned UAC Drift domain types" loose end (operator ruling 2026-07-16, Solana perp DEX cull),
  found that `unified-api-contracts/unified_api_contracts/internal/architecture_v2/` still has ~20 files with LIVE
  (non-comment) "drift" venue references — `archetype_capability_manifest.json` (8 occurrences incl. a
  `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` strategy-slot label + a prose note naming Drift as a staked-basis
  leg venue), `archetype_leg_spec_seeds.py` (8 occurrences incl. `venues = (..., "drift", ...)` tuples that build real
  `ArchetypeLegStructure` leg definitions for STAT_ARB_CROSS_SECTIONAL/CARRY_STAKED_BASIS/etc — not decorative strings),
  plus `perp_hedge_sizer.py`, `capability_manifest.py`, `archetype_config.py`, `backtest_scenarios.py`,
  `benchmark_fill_pricing.py`, `algo_compatibility.py`, `collateral_registry.py`, `leveraged_legs.py`,
  `restaking_rewards.py`, `archetype_leg_spec.py`, `archetype_capability.py` and others flagged by `rg -l -i
  ''drift|pacifica'' unified_api_contracts/internal/architecture_v2/` (not all individually confirmed
  live-vs-false-positive — needs a full pass). This is UNLIKE every other UAC registry (venue_constants.py,
  defi_venues.py, venue_mapping.py, venue_collateral.py, expected_coverage.py, etc.) which already carry clean "removed
  2026-07-16 (operator ruling)" comment markers — architecture_v2 was structurally missed by that sweep, likely because
  it''s strategy-definition code (leg specs / manifests / backtest scenarios) rather than venue/instrument registries,
  so it wasn''t in the grep surface the original cull used. Downstream —
  `unified-trading-system-ui/lib/registry/ui-reference-data.json`''s `venue_set_variants` (live-read by
  `lib/architecture-v2/lifecycle.ts`) and `archetype_capability_registry` sections mirror this — they still list "drift"
  as a SUPPORTED venue in 13+ strategy-tier variants (e.g. "CARRY_BASIS_PERP — CEFI+DEFI (9 venues)" literally counts
  Drift). NOT fixed as part of this session — fixing the UI copy without fixing the UAC source first would just regress
  on the next regen, and the UAC fix itself needs strategy-domain judgment (leg specs / backtest scenarios / benchmark
  pricing may have Drift-specific numeric assumptions, not just a venue string to delete) that was out of scope for a
  UI-registry cleanup task. UPDATE 2026-07-16: the UAC-source portion was resolved by a follow-up dispatch — see the
  "UPDATE" section in the body below.'
status: open
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [drift-solana-cull, architecture-v2, leg-specs, strategy-archetype, venue-residue, ui-reference-data]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: 2026-07-16
author: unknown
last_updated: 2026-08-20
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Drift orphan-cleanup task, 2026-07-16 — discovered via `rg -n -i 'drift|pacifica'
  unified_api_contracts/internal/architecture_v2/` while tracing why UI's `venue_set_variants` still lists Drift.
resolved_by:
context_scope: [/plans/active/defi_consolidated_closeout_2026_07_18.md, /plans/archive/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md, unified-api-contracts/unified_api_contracts/internal/architecture_v2/, unified-trading-system-ui/lib/registry/ui-reference-data.json, unified-api-contracts/scripts/generate_ui_reference_data.py, unified-trading-system-ui/lib/architecture-v2/lifecycle.ts]
---

# architecture_v2 strategy-archetype subsystem still has live DRIFT venue references

## Facts

1. `unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` lines 113, 367, 640, 675, 690,
   697, 918, 1720, 1834 — live `"drift"` venue entries in capability-cell venue lists, a
   `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` strategy-slot label (line 690), and a prose `notes` field
   (line 697) naming Drift as the Solana leg of a 3-leg atomic staked-basis strategy.
2. `unified_api_contracts/internal/architecture_v2/archetype_leg_spec_seeds.py` lines 72, 81, 228, 297, 575, 993, 1210 —
   `venues = (..., "drift", ...)` tuples feeding `ArchetypeLegStructure` leg definitions (real strategy-leg construction
   code, e.g. `STAT_ARB_CROSS_SECTIONAL`'s
   `venues = ("binance", "hyperliquid", "bybit", "gmx_v2", "drift", "ibkr", "nasdaq", "nyse")` at line 993) plus prose
   docstrings.
3. `rg -l -i 'drift|pacifica' unified_api_contracts/internal/architecture_v2/` additionally flags:
   `perp_hedge_sizer.py`, `simulation_assumptions.py`, `capability_manifest.py`, `jurisdiction_overlay.py`,
   `order_semantics.py`, `archetype_config.py`, `backtest_scenarios.py`, `venue_tokens.py`, `flash_loan_receiver.py`,
   `algo_compatibility.py`, `collateral_registry.py`, `liquidation_bonus_schedule.py`, `leveraged_legs.py`,
   `benchmark_fill_pricing.py`, `archetype_leg_spec.py`, `restaking_rewards.py`, `archetype_capability.py`. Each needs
   individual triage (some may be false positives — "drift" as in numerical/schema drift — same as elsewhere in the
   codebase; not all confirmed live venue refs in this pass).
4. Contrast: every OTHER UAC registry touched by the 2026-07-16 Solana-perp-DEX cull (`venue_constants.py`,
   `defi_venues.py`, `venue_mapping.py`, `venue_collateral.py`, `expected_coverage.py`, `venue_adapter_keys.py`,
   `cefi_perp_venue_endpoints.py`, capability_declarations/*.py) carries a clean
   `# DRIFT/PACIFICA (Solana) removed 2026-07-16 (operator ruling: ...)` comment marker in place of the dead entry —
   architecture_v2 has none of these markers, confirming it was structurally outside the original cull's grep surface.
5. Downstream in `unified-trading-system-ui`: `lib/registry/ui-reference-data.json`'s `venue_set_variants` (68 entries,
   live-read by `lib/architecture-v2/lifecycle.ts:241` as `rawVariants`) lists "drift" as a venue in 13 variants across
   6 archetypes (ML_DIRECTIONAL_CONTINUOUS, RULES_DIRECTIONAL_CONTINUOUS, CARRY_BASIS_PERP, CARRY_STAKED_BASIS,
   ARBITRAGE_PRICE_DISPERSION, STAT_ARB_PAIRS_FIXED, STAT_ARB_CROSS_SECTIONAL) — each variant's `label` field literally
   counts venues (e.g. `"CARRY_BASIS_PERP — CEFI+DEFI (9 venues)"` includes Drift in the 9). The
   `archetype_capability_registry` section (cell-level `venue_ids` arrays, `representative_slot_labels`) has the same
   residue, plus the `strategy_instance_catalogue.instances` entry itself for
   `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` (a named strategy instance, not just a capability cell).

## Why not fixed in this session

This session's task was narrowly scoped to the orphaned UAC `Drift*` Pydantic/StrEnum TYPES (`solana.py` +
`internal/__init__.py` + `internal/domain/defi/__init__.py` re-exports) and their DIRECT generated-JSON copies in
`unified-trading-system-ui` (the `uic_enums.DriftMarketType`/`DriftOrderSide` entries) — both fixed this session. The
`architecture_v2` residue is a different, larger surface: real strategy-leg-construction code and a capability manifest,
not orphaned type definitions. Hand-deleting "drift" from `venues` tuples in `archetype_leg_spec_seeds.py` without
strategy-domain review risks silently changing archetype eligibility/backtest assumptions in ways a UI-registry cleanup
task shouldn't decide unilaterally. Fixing the UI's `venue_set_variants`/`archetype_capability_registry` copy ahead of
the UAC source would also just regress on the next `generate_ui_reference_data.py` regen (which doesn't even touch these
sections currently — see Finding below) or a manual resync.

## UPDATE 2026-07-16 (later dispatch) — UAC-source portion RESOLVED

A follow-up session, dispatched specifically to close the "UPPERCASE-biased closing grep missed lowercase venue ids" gap
workspace-wide (`unified-api-contracts` + `unified-trading-library`, case-insensitive, venue-context patterns only — not
the blanket `drift_|_drift` pattern that produced 233/351 bogus hits earlier), fixed every item in Fact #1/#2 above:

- `archetype_capability_manifest.json` — venue_ids (lines 113, 367, 640, 675, 918, 1720, 1834) + the
  `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` slot label (line 690) + the prose `notes` field (line 697, now
  reads "...Kamino + CeFi-perp hedge — native Solana perp DEX hedge leg (Drift) removed 2026-07-16...") all fixed.
  Verified round-trip clean: `python scripts/generate_archetype_capability_manifest.py` →
  `archetype_capability_manifest.json is up-to-date`.
- `archetype_leg_spec_seeds.py` — all 7 occurrences fixed (lines 72, 81, 228, 297, 575, 993, 1210): the
  `_STAKED_HEDGE_VENUES` tuple, the `CARRY_BASIS_PERP` perp-leg tuple, `ARBITRAGE_PRICE_DISPERSION`'s `venues` tuple,
  `STAT_ARB_CROSS_SECTIONAL`'s `venues` tuple, `_directional_seeds()`'s `continuous_venues` tuple, and the two
  slot-label doc-comments (re-pointed to the surviving `jito-kamino-bybit-sol-usdt-prod` label, not just deleted).
- Also fixed (found by the venue-context sweep, not in this doc's original Fact list): `collateral_registry.py` (the
  full `CollateralPolicy(venue_id="drift", ...)` block, lines 533-554, removed — this is what made
  `tests/unit/test_collateral_registry_backfill.py::test_drift_accepts_solana_lsts` pass on dead-venue behaviour; see
  below), `simulation_assumptions.py` (`_CLOB_PERP_VENUES`), `jurisdiction_overlay.py` (`KNOWN_VENUE_IDS` + 4
  `_allow`/`_block`/`_unknown` policy rows), `order_semantics.py` (the full `VenueOrderSemantics(venue_id="drift", ...)`
  block), `venue_tokens.py` (`_DEFI_PERP_TOKENS`), and `archetype_leg_spec.py` (a docstring example tuple).
- Vacuous-test trap avoided per the operator's explicit guidance (same pattern as strategy-service's F-09 fix, see
  `solana_perp_dex_cull_drift_pacifica_2026_07_16.md`):
  `test_collateral_registry_backfill.py::test_drift_accepts_solana_lsts` was DELETED (not silently left) with an
  explanatory comment — verified the scenario is genuinely unreachable (Drift was the only PERP venue ever accepting
  Solana LSTs as margin; the surviving Solana-LST acceptor is Kamino, a LENDING venue, already covered by
  `test_kamino_partial_ltv_none_but_haircut_sourced`, so real coverage is not lost).
  `test_jurisdiction_overlay_backfill.py::test_retail_restricted_blocks_derivative_venues` had "drift" dropped from its
  assertion list with a comment explaining WHY: keeping it would have asserted "not in allowed" off the absence-default
  for a now-nonexistent venue, not off a real RETAIL_RESTRICTED `_block` row.
- `unified-api-contracts` full `quality-gates.sh` + `unified-trading-library` full `quality-gates.sh` both run green
  post-fix; both shipped via scoped `quickmerge.sh --agent --files`. See this repo's commit history / the dispatching
  session's final report for exact shas.
- **Third instance of the stale-bundle class also found and filed** (not hand-patched):
  `unified-api-contracts/openapi/capability-manifest.json` / `capability-verdict-matrix.json` /
  `capability-unlock-report.json` — same "committed generated bundle, no in-repo generator" situation as this issue's
  sibling doc `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` already tracks for 2 other bundles;
  appended there as "Third instance" rather than hand-edited.

**Still open (unchanged from the original Facts above — out of the UAC/UTL-scoped dispatch)**:
`unified-trading-system-ui/lib/registry/ui-reference-data.json`'s `venue_set_variants` / `archetype_capability_registry`
sections and `unified-trading-system-ui/tests/e2e/_shared/strategy-registry.ts`'s `CARRY_STAKED_BASIS.instanceIds` entry
still reference the now-dead `drift` venue / the now-removed `jito-kamino-drift-sol-usdc-prod` slot label — these are
downstream UI mirrors of the UAC source fixed above and need their own resync (see "Secondary finding" below on why a
blind full regen is itself unsafe right now) or a scoped hand-fix once that generator/UI-shape mismatch is resolved.

## Secondary finding: the UI/UAC registry-sync generator is itself stale

Running `unified-api-contracts/scripts/generate_ui_reference_data.py --output <tmp>` and diffing against
`unified-trading-system-ui`'s committed `lib/registry/ui-reference-data.json` (HEAD, last regenerated at `a4ec4985`)
shows a MASSIVE unrelated structural diff — different top-level metadata fields (`generated_by`/`ssot_doc` vs
`version`/`generator`/`registry_count`) and a completely restructured `archetype_capability_registry` (current generator
emits only per-archetype counts, not the `venue_ids`/`cells` detail the committed copy — and
`lifecycle.ts`/`platform-stats.ts` — currently depend on). This means: (a) a full regen right now would silently DROP
fields the live UI TypeScript reads, breaking rendering, not just remove Drift; (b) the UI copy has been drifting from
the generator's actual current output shape for a while, independent of the Drift cull. Worth its own investigation —
tag `assigned_role: engineer`, likely a `unified-trading-system-ui` + `unified-api-contracts` coordinated fix.

## Additional pointer found during the UI sweep

`unified-trading-system-ui/tests/e2e/_shared/strategy-registry.ts` line 158 lists
`"CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod"` in `CARRY_STAKED_BASIS.instanceIds` — an E2E fixture pinned to
the same strategy-instance ID as `archetype_capability_manifest.json` line 690. Left untouched this session for the same
reason: whether it's deleted or re-legged onto Jupiter is a strategy-domain call that should follow the UAC-side
decision, not precede it (an E2E fixture referencing an ID the backend still serves is not itself a bug).

## UPDATE 2026-07-26 — full triage of the remaining 9 never-individually-confirmed files (RESOLVED — all false positive)

The 9 files listed in Fact #3 but never individually re-confirmed by the 2026-07-16 follow-up dispatch —
`perp_hedge_sizer.py`, `capability_manifest.py`, `archetype_config.py`, `backtest_scenarios.py`,
`flash_loan_receiver.py`, `algo_compatibility.py`, `liquidation_bonus_schedule.py`, `benchmark_fill_pricing.py`,
`archetype_capability.py` — were each individually re-run through `rg -n -i 'drift|pacifica'` scoped to that file.
Verdict: **all false positive, zero code changes needed.**

- `perp_hedge_sizer.py` (3 hits) — `DRIFT_BAND_BREACH` enum member + "Drift within/as fraction of band" docstrings:
  position-exposure drift (deviation from target) within a rebalance band, unrelated to the Drift DEX venue.
- `capability_manifest.py` (2 hits) — "JSON drift detection" / "deterministic serialisation for drift detection":
  schema/content drift (change-tracking), not a venue reference.
- `archetype_config.py` (1 hit) — "cross-venue delta-drift risk surfaces" (line 286, `CARRY_BASIS_PERP_INV` comment): a
  risk-surface description of hedge-ratio delta drift across venues generically, not a Drift-venue mention — the venue
  actually named nearby is Bybit (perp hedge venue), not Drift.
- `flash_loan_receiver.py` (1 hit), `algo_compatibility.py` (1 hit), `liquidation_bonus_schedule.py` (1 hit),
  `benchmark_fill_pricing.py` (1 hit), `archetype_capability.py` (1 hit) — each a single generic "config/behavioral
  drift" mention (e.g. "flash-loan borrow if drift detected", "no drift" between registries, "backtest engine could
  drift from live", "cannot drift between batch and paper", "push catches drift") — none reference a venue at all.
- **Zero `pacifica` hits** in any of the 9 files (checked separately, case-insensitive).

No comment markers were added since there was no dead venue entry to mark — the standard
`# DRIFT/PACIFICA (Solana) removed 2026-07-16 (operator ruling: ...)` pattern applies only where a genuine live venue
reference existed to replace, which none of these 9 files had. No `unified-api-contracts` code changed, so no QG run was
needed for this sub-task. This closes out Fact #3's "not all individually confirmed" gap — combined with the 2026-07-16
UPDATE above (which resolved the genuine-hit files), **all files originally flagged by the `rg -l -i 'drift|pacifica'`
sweep are now individually triaged** (either fixed with a marker, or confirmed false-positive).

Still open (unchanged): the UI resync (`venue_set_variants`/`archetype_capability_registry`/
`strategy_instance_catalogue`), the `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` delete-vs-re-leg strategy call,
and the generator/UI structural-skew investigation — see "Recommended next steps" below, items 2-4.

## Recommended next steps

1. Triage each `architecture_v2` file flagged above for genuine Drift-venue residue vs false positive (schema/numeric
   drift), following the same pattern as the rest of the 2026-07-16 cull (comment-marker the dead entries, don't
   silently vanish them).
2. Decide whether `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` gets deleted outright or re-legged onto a
   remaining Solana venue (Jupiter) — a strategy-domain call, not a registry-cleanup call.
3. Once UAC's architecture_v2 source is clean, regenerate (or hand-sync, scoped) the UI's `venue_set_variants` /
   `archetype_capability_registry` / `strategy_instance_catalogue` sections to match.
4. Separately: investigate the generator/UI structural skew (see Secondary finding) — likely needs its own plan before
   any full regen is safe.

## Todos

- [ ] [ENGINEER] P1. **Fix the E2E fixture + the generator/UI structural skew** (STRUCK the ui-reference-data.json
      resync sub-claim 2026-08-17, na-eligibility-audit — STALE, already shipped: commits `80bb6a9c` (2026-07-26) +
      `88422902` (2026-08-16) removed all drift-venue residue from that file; live-verified 2026-08-17, zero matches
      remain). Two sub-parts genuinely still open: (1) `tests/e2e/_shared/strategy-registry.ts:158` still has the dead
      `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` instance ID (grep-confirmed, no fixing commit in that
      file's history); (2) the sync generator/UI structural-skew investigation (see "Recommended next steps" items 2-4
      above) — unverified either way (re-running `generate_ui_reference_data.py` to check needs the repo `.venv`,
      ambient `python3` lacks `pydantic`).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - bundles a strategy-domain delete-vs-re-leg decision with a
  generator/UI structural-skew investigation the doc says likely needs its own plan
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries — corrects the 2026-08-01 marker's stale count, the
  list itself already carried 6) — all still resolve; covers the still-open UI-resync todo's exact source targets
  (`ui-reference-data.json`, `generate_ui_reference_data.py`, `lifecycle.ts`).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  the sole todo still bundles a strategy-domain delete-vs-re-leg judgment call with an open-ended generator/UI
  structural-skew investigation the doc itself says likely needs its own plan. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-04 audit (context-scout metadata only, per git log). Sole open todo still bundles a strategy-domain
  delete-vs-re-leg judgment call (`CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod`) with an open-ended UI/generator
  structural-skew investigation the doc's own "Secondary finding" says likely needs its own plan. Doc stays
  `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 1 open checkbox (`[ENGINEER] P1`) bundling 3
  sub-parts: an undecided strategy-domain judgment call (delete vs re-leg
  `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod`), a mechanical UI resync gated on that decision landing first,
  and a separate generator item. Doc's own words: "a strategy-domain call, not a registry-cleanup call." Doc stays
  `assigned_vm: NA`.
- **2026-08-16 (slot 4, data_engineering, task `meta_plan_corpus_hygiene_ao_dispatch_batch1-ca0c6558e40b`) — retagged
  `asset_group: [defi] → [ui]` per `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` todo 6.** The
  UAC-source portion of this issue (architecture_v2 leg specs / capability manifest) was already RESOLVED by the
  2026-07-16 follow-up dispatch (see "UPDATE 2026-07-16" above) and the 9-file false-positive triage (see "UPDATE
  2026-07-26" above) — the sole remaining open todo (`[ENGINEER] P1`) is exclusively the UI-side resync:
  `unified-trading-system-ui/lib/registry/ui-reference-data.json`'s `venue_set_variants` /
  `archetype_capability_registry` / `strategy_instance_catalogue`, the `generate_ui_reference_data.py` generator/UI
  structural-skew fix, and the `tests/e2e/_shared/strategy-registry.ts` fixture — all `unified-trading-system-ui`
  content, not defi-domain. `[ui]` fits better than `[cross-cutting]`: the remaining work is single-repo-primary
  (UI registry + its generator), not genuinely multi-domain. Added
  `related: [/plans/active/ui_consolidated_closeout_2026_07_30.md]` alongside the existing defi-closeout link so the
  doc has a path into its new tranche's closeout family (`check_ag_closeout_linkage.py` convention).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17 (ui tranche)** [body-hash:0d2984d35c34a8d6]: KEEP-NA, stale item closed — the
  bundled todo's ui-reference-data.json resync sub-claim was STALE (already shipped via `80bb6a9c`/`88422902`,
  live-verified 2026-08-17: zero drift-venue-residue matches remain) and has been struck from the todo text. Doc stays
  NA: 2 genuinely open sub-parts remain (the e2e-fixture fix, live-confirmed still-present; the generator/UI
  structural-skew investigation, unverified either way).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
