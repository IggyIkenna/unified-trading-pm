---
doc_type: plan
title: DeFi strategy/PnL/backtest axis index — entry point for the strategy-service track
summary:
  Entry-point index for the DeFi strategy/PnL/backtest-engine axis (`strategy-service`), extracted from
  defi_consolidated_closeout_2026_07_18.md's "Strategy/PnL/backtest-side DeFi tracking" section (folded in there
  2026-07-23, "no orphans") so that plan could come back under the 1000-line hard cap. This doc REFERENCES the source
  docs; it does not duplicate them — same pattern as the parent data/canonicalization close-out.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos:
  [
    strategy-service,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [defi, strategy, pnl, backtest, strategy-service, index, entry-point]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    /plans/archive/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md,
    /plans/archive/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: none
archive_exempt: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Extracted 2026-07-24 from defi_consolidated_closeout_2026_07_18.md per
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md (bucket-(c) split #11: "Extract Strategy/PnL index +
  1800-line historical log"). Content moved verbatim, no rewrite — see the parent's Progress Log / this remediation
  job's evidence for the split rationale.
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py,
  ]
---

# DeFi strategy/PnL/backtest axis index — entry point for the strategy-service track

> **Purpose.** This is the entry point for the DeFi **strategy/PnL/backtest engine** axis (`strategy-service`) — a
> genuinely different set of tracks from
> [`defi_consolidated_closeout_2026_07_18.md`](defi_consolidated_closeout_2026_07_18.md)'s **data/canonicalization**
> axis (IS/MTDS-touching). Both plans are parallel, not sequential — read both so a fresh session can pick up fully.
> This doc references, does not duplicate; each linked doc below carries its own full detail + Progress Log.

## Strategy/PnL/backtest-side DeFi tracking (SECOND axis, folded in 2026-07-23 — operator: "no orphans")

> This doc's original scope (above + Tracks R1-R8/T1-T8 below) is the DeFi **data/canonicalization** axis
> (IS/MTDS-touching). Operator asked (2026-07-23) that ALL DeFi-related work — without exception — be discoverable from
> THIS one plan, so a fresh session can pick up fully from here + the docs it points to. This section is the entry point
> for the **strategy/PnL/backtest engine** axis (`strategy-service`), a genuinely different set of tracks that emerged
> in the same session as the data-side "Deferred work after 2026-07-23" table further down — READ BOTH, they are
> parallel, not sequential. This section references, does not duplicate; each linked doc carries its own full detail +
> Progress Log.

- **[[lst_rate_honest_coverage_2026_07_21]]** — the 4 LST exchange-rate surfaces (CEX spot / DEX pool / Aave oracle /
  protocol redemption) honest-coverage plan. `lst_rates` backfill VM completed clean (exit_code=0, full range);
  `dex_pool_swaps` backfill is a 3-VM date-sharded on-demand fleet, IN FLIGHT, targeting ~20-30h; 4-rate code-trace
  audit CONFIRMED EVM LSTs (stETH etc.) are genuine historical protocol-redemption (#4) every day, Solana LSTs are a
  DefiLlama market-proxy historically (not #4, moot today — no Solana LST is perp-eligible). See its own RESUME POINT
  section for the full deferred-work table + lessons.
- **[[distinct_values_noncanonical_audit_2026_07_20]]** — distinct-values/non-canonical audit, D1-D6 shipped this
  session.
- **[[pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21]]** (`issues/`) — DeFi interest PnL correctness.
  E1 (FUNDING leg, real `derivative_ticker.funding_rate`) SHIPPED `strategy-service@aa1fcdc7`. STAKING leg (real
  `lst_yields` index-ratio, replacing the banned `bps/365` form) SHIPPED `strategy-service@e93902d8`. Still open:
  `LENDING_INTEREST` mismodeling correction for `carry_staked_basis` (E4 already ruled the row-set should drop it
  entirely — implementation not started); `recursive_staking`'s real Aave `borrow_index` leg (E3) — SHIPPED
  `strategy-service@23bd8b76` (as "Phase 2" of the orphaned-archetype build below).
- **[[defi_catalog_engine_config_key_contract_drift_2026_07_23]]** (`issues/`, **P0**) — while wiring the
  orphaned-archetype tick builders below, a cheap mechanical pre-check (catalog-emitted config keys vs what each
  engine's `on_tick` actually reads) found **6 of the first 9 DeFi archetypes checked cannot execute a single real trade
  in ANY environment today** (paper, batch, OR live — same catalogs/engines the live path uses): 1 crashes at
  registration, 2 silently no-op forever on a catalog/engine key mismatch, 2 are intentional stubs pending an unwired
  execution-service integration, 1 fires but silently ignores the catalog's per-row economic tuning. None of this is
  caught by any test or gate. Read this doc before touching ANY more of the orphaned-archetype phases below — several
  phases are blocked or need re-scoping because of exactly this class of bug.
- **[[defi_archetype_universe_no_curtailment_mechanism_2026_07_23]]** (`issues/`) — full 19-archetype DeFi universe map
  (base currency/underlying, staking venues, lending venues, trading venues, data_type/instrument_type reqs per
  archetype) + the operator-specified **3-layer universe-constraint architecture** (Layer 1: dynamic ADV-ranked
  candidate discovery from features-service, reusing the existing `cross_instrument/app/calculators/adv.py`; Layer 2:
  archetype-level allow/block-list on currency/venue/instrument_type/data_type, generalizing `catalog_staked_basis.py`'s
  ad-hoc collateral gate; Layer 3: per-strategy-instance config filter, scoped to client/axis/version) + the **5-phase
  plan to wire the 12 currently-orphaned (engine_tick_builder_unwired) archetypes** (Phase 1 CARRY_STAKED_BASIS_DATED in
  flight; Phase 2 = E3 above; Phases 3-5 dated-basis/yield/ liquidation-capture) + 2 unreconciled-registry / dead-code
  side findings. This doc's own RESUME POINT section is the durable source of truth for this whole thread — read it in
  full before resuming.
- **[[e2e_testing_collateral_validation_dead_import_2026_07_23]]** (`issues/`) — `e2e-testing`'s
  `test_collateral_validation.py` has imported a module deleted 2026-05-01 for ~2.5 months, 9/9 scenarios dead, zero CI
  signal; underlying safety property still holds in prod via a newer v2 mechanism. Operator ruling needed: rewrite vs
  delete vs gate-hardening.
- **`/plans/archive/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md`** (archived 2026-07-30, all 9 todos done;
  not defi-scoped itself but directly affected the `dex_pool_swaps` fleet above) —
  `launch-mtds-dex-swaps-backfill-vm.sh` was missing the same SPOT-preemption auto-recovery wiring
  (`lc_write_preemption_signal_file`) as 13+ other launchers; fixed + shipped `deployment-service@db5d3c7`.

**Recommended next action (strategy/PnL axis)**: Phase 1 of the orphaned-archetype build (CARRY_STAKED_BASIS_DATED) is
running in a background agent as of this addendum — check its result first, then continue Phase 2 (E3, the Aave
borrow-index leg, shared across 3 archetypes) sequentially per the phased plan (phases touch shared files, run them one
at a time, never in parallel). The `LENDING_INTEREST` mismodeling correction (E4-ruled, unimplemented) is a small,
independently-startable item any session can pick up without waiting on the phased build.

## Todos

- [x] [BACKEND] P2. ✅ **`LENDING_INTEREST` mismodeling correction for `carry_staked_basis`** — E4 already ruled the
      row-set should drop it entirely; **SHIPPED `strategy-service@a90e85eb`** (per
      `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`'s own `[x]` todo, quickmerge landed,
      `quality-gates.sh --no-fix` green, 5407 tests) — `emit_lending_leg=False` wired for `CARRY_STAKED_BASIS`, dropping
      LENDING_INTEREST/BASIS rows entirely (not left on the old formula) from both the passive and attribution
      producers; every other archetype's default row-shape confirmed unchanged. This doc's own text was stale — it
      claimed "implementation has not started" (citation corrected 2026-08-03, /na-eligibility-audit reclassify-pass).
      Separately, `issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`'s rewrite-vs-delete-vs-gate-
      hardening choice was **RULED 2026-07-29 (operator direct answer): Option A, rewrite against the current v2
      mechanism** — that half is no longer pending (citation corrected 2026-07-30, /na-eligibility-audit defi).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA-STALE: its todo says the e2e_testing_collateral_validation
  rewrite-vs-delete choice 'still needs an operator ruling' — that ruling landed 2026-07-29 (Option A). Citation
  corrected; doc stays NA (index/entry-point doc, nature: process, drift_direction: none)
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — archive_exempt standing reference hub, 0 open
  checkboxes, re-confirmed unchanged.
- **na-eligibility-audit 2026-08-03 (reclassify pass)**: KEEP-NA-STALE -> checkbox closed. The sole open todo
  (`LENDING_INTEREST` mismodeling correction for `carry_staked_basis`) was already shipped in the linked sibling doc
  (`issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`, `strategy-service@a90e85eb`) — this
  doc's own text had not been updated to reflect it. Flipped `[x]` with citation; doc has zero remaining open scope
  (index/entry-point doc, `assigned_vm` unchanged).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **archive_candidates_content_verification 2026-08-06 (slot 9, review)**: `archive_exempt: true` — this is an
  index/entry-point doc (`nature: process`) serving as a standing reference hub for the DeFi strategy/PnL/backtest
  engine axis. All 1/1 native checkboxes are done; the doc's purpose is to aggregate pointers to the strategy-service
  track's source docs, not to carry its own executable work. Archiving it would orphan the entry-point reference for the
  strategy/PnL axis.
- **context-scout 2026-08-07**: refreshed context_scope (5 -> 6 entries) — all prior 5 re-verified and still resolve
  (unchanged after the 2026-08-06 archive-exempt classification note); added
  `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py`, the source file the
  "Recommended next action" (orphaned-archetype build Phase 1) directly targets for generalization — this doc's own body
  names it but no prior scout pass had added a source path (this is an index/pointer-hub doc, but its own "Recommended
  next action" section points at real code, not just other docs). ~~Note for the record: this doc's `repos:`
  frontmatter list is missing `strategy-service`~~ — **fixed 2026-08-17** (plan_reconciler `plan_reconciler_findings_defi_2026_08_17.md`
  Hygiene fixes #1): `strategy-service` is now the first entry in `repos:` above. This note was stale for a day
  before being caught (plan_reconciler 2026-08-18).
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
