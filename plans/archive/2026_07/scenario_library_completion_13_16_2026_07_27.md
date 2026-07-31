---
doc_type: plan
title: Scenario library completion — execution_slippage_spike + lst_unstake_queue_blowup
summary:
  Implement the 2 orphaned Day-1 scenario designs (plans/active/scratch_scenarios_day1/13 and 16) into the UAC
  ScenarioOverlay registry + UTL applier, per operator decision (2026-07-27 pre-June-1 stale-plans audit) — the other 16
  of 18 Day-1 scenarios were all consumed one way or another; these 2 were designed 2026-05-12 and never picked up
  anywhere.
status: complete # (was: active) 2026-07-31 — all 3 todos [x] w/ verified commit evidence (unified-api-contracts@15ab5a48), archived
nature: process
asset_group:
  [defi] # corrected 2026-07-29 (/ag-closeout-audit defi, Phase 0.3 Orthogonality HARD CHECK) -- was
  # [defi, cross-cutting], a genuine mistag: parent_epic is defi_master (not one of the 5 cross-cutting DATA_EPICS), and
  # 1 of 2 implementation todos (lst_unstake_queue_blowup, an LST/restaking concept) is unambiguously DeFi-only; the tag
  # never functionally registered as cross-cutting membership anyway (parent_epic gate fails, doc was never cited by the
  # cross-cutting closeout), so this was vestigial, not a real dual-scope marker.
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [scenario-injection, uac, defi, execution, lst, game-day]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-07-27
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source:
  [
    plans/active/scratch_scenarios_day1/13_execution_slippage_spike.md,
    plans/active/scratch_scenarios_day1/16_lst_unstake_queue_blowup.md,
  ]
assigned_role: backend_engineer
drift_direction: none
---

# Scenario library completion — execution_slippage_spike + lst_unstake_queue_blowup

> **ARCHIVED (2026-07-31) — all 3 todos shipped.** Both `ScenarioOverlay` entries landed
> (`unified-api-contracts@15ab5a48`) and are verified consumable by the UTL applier with zero applier-code changes.
> Gated finalize twin `scenario_library_completion_13_16_finalize_2026_07_30.md` archived alongside this doc.

## Context

16 of the 18 `plans/active/scratch_scenarios_day1/*.md` Day-1 scenario designs (2026-05-11/12) were consumed somewhere —
the `unified-api-contracts` `ScenarioOverlay` registry (`registry/scenarios/{cefi,defi,cross_asset}.py`), a smoke test,
a runbook verifier, or an alerting-service subscriber. 2 were not: `13_execution_slippage_spike.md` and
`16_lst_unstake_queue_blowup.md` have zero downstream consumption anywhere. The registry pattern is established (see
e.g. `DEFI_CHAIN_RPC_OUTAGE_SOLANA` in `registry/scenarios/defi.py:44-70` — a `ScenarioOverlay` with `scenario_id`,
`category`, `layer`, `asset_groups`, `applies_to` filter, `mutation_spec`, and `expected_outcomes` assertions).

## Todos

- [x] ✅ [CODE] P2. **DONE 2026-07-31 — `unified-api-contracts@15ab5a48`.** Implemented `execution_slippage_spike` as a
      `ScenarioOverlay` in `unified_api_contracts/registry/scenarios/cross_asset.py` (asset_groups span both cefi+defi
      per the source doc, matching `CROSS_ASSET_FLASH_CRASH`'s exact home-file precedent). `BookSpoof` mutation
      (existing type — covers both the DEX pool-drain and CeFi book-thinning variants' shared depth-withdrawal
      mechanism). Closest-fit substitutions documented in the registry file's own module docstring: `VENUE_OUTAGE`
      category + `SPREAD_BLOWOUT_BPS` breaker (the source fragment's `EXECUTION_QUALITY`/`LIQUIDITY_DRAIN`/
      `BOOK_THINNING` categories and `EXECUTION_SLIPPAGE_EXCEEDED`/`CEFI_BOOK_THIN` alert codes don't exist in UAC yet).
      `Drift`/`Hyperliquid-spot` DEX protocols from the source fragment omitted (not registered adapter keys anywhere in
      the workspace — confirmed via MTDS's `VENUE_REGISTRY`/`PLANNED_VENUES`) rather than invented; only Uniswap
      V3/Curve/Balancer declared. 3 expected_outcomes (carry_staked_basis/ARBITRAGE_PRICE_DISPERSION/
      LEVERAGED_FUNDING_ARB) per the source doc's targeted archetypes. Full `quality-gates.sh` green (281s, 2 dedicated
      shape tests + all pre-existing registry-invariant tests updated for the new count).
- [x] ✅ [CODE] P2. **DONE 2026-07-31 — `unified-api-contracts@15ab5a48`.** Implemented `lst_unstake_queue_blowup` as
      `DEFI_LST_UNSTAKE_QUEUE_BLOWUP` (`scenario_id="defi_lst_unstake_queue_blowup"`, `defi_`-prefixed per this registry
      file's own naming convention) in `unified_api_contracts/registry/scenarios/defi.py`, next to
      `DEFI_LST_DEPEG_STETH_5PCT` as scoped. `LatencyInject` mutation (existing type — represents the added redemption
      delay; same type `defi_mempool_congestion_inclusion_delay` already uses for an analogous "added delay to a
      settlement pipeline" mechanism) since the source fragment's own PRIMARY mechanism (a per-LST
      `unstake_days_remaining` feature) needs a `LST_WITHDRAWAL_THROUGHPUT_BASELINES` registry the fragment itself marks
      `DEFERRED-TO-PHASE-2-IMPL`. `LENDING_POOL_UNAVAILABLE_SECONDS` substitutes for the undefined queue-lockup breaker
      (same "prevented from acting on this position" shape as its existing Aave/Morpho use). Only the 12 LST/LRT tokens
      confirmed in UAC's real `LST_TOKEN_TO_PROTOCOL_ASSET` registry declared — the source fragment's frxETH/sfrxETH
      (Frax)/Sanctum/LBTC (Lombard) aren't onboarded there, so omitted rather than invented. The fragment's
      `secondary_market_depeg` sub-variant is not separately modeled (composes with, and is mechanically covered by,
      `execution_slippage_spike`'s pool-drain mechanism per the fragment's own "Composes with" section). Full
      `quality-gates.sh` green (same run as above, 1 dedicated shape test added).
- [x] ✅ [VALIDATE] P3. **DONE 2026-07-31.** Verified `unified-trading-library`'s `ScenarioOverlayApplier` picks up both
      new entries with ZERO applier code changes needed — both scenarios reuse EXISTING mutation types (`BookSpoof`,
      `LatencyInject`) whose `apply()` dispatch (`unified_trading_library/scenario/applier.py`) is already generic on
      `mutation_type`. Confirmed via the pre-existing parametrized smoke test
      `tests/unit/scenario/test_applier.py::test_every_registry_scenario_applies_without_error` — ran green against all
      13 registry scenarios (up from 11), including both new ones, with no test or applier-code edits required. Full
      `unified-trading-library` scenario suite (`tests/unit/scenario/`) green, 64/64. Updated the source design
      fragments (`13_execution_slippage_spike.md`, `16_lst_unstake_queue_blowup.md`) with a `🟢 SHIPPED` banner noting
      the registry entry + commit SHA each now backs, per this todo's own instruction (no such banner pattern actually
      existed on scenarios 01-10 despite this todo's claim — confirmed via grep before writing the note, so a new
      minimal banner convention was used instead of a nonexistent one).

## Progress Log

- **2026-07-31 (slot 7, backend_engineer)**: All 3 todos DONE — `unified-api-contracts@15ab5a48` (both
  ScenarioOverlays + registry tests, full `quality-gates.sh` green) + verified zero-code-change consumption via
  `unified-trading-library`'s existing applier smoke test. Plan is fully complete + unlocked (`locked_by:` empty) —
  archiving in a separate follow-up commit per the checkbox-flip-then-git-mv discipline
  (`quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`'s sibling incident on combining flips with
  archival in one commit).

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - implement 2 already-DESIGNED scenarios into the UAC
  ScenarioOverlay registry against an established pattern; design is done, only the build remains

- 2026-07-27: Plan created per operator decision (pre-June-1 stale-plans audit) — implement both, don't drop.
