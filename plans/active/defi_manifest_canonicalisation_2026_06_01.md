---
title: "DeFi manifest + data-status canonicalisation (post 2026-06-01 coverage audit)"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-05-21
source:
  - plans/audit/results/defi_master_audit_2026_06_01.md (the audit that surfaced all of this)
  - plans/audit/instructions/defi_master_audit_instructions.md (items o–y)
---

# DeFi Manifest + Data-Status Canonicalisation

> **Why this exists**: the 2026-06-01 DeFi coverage audit took many passes because the data is **not in canonical form**
> — scattered buckets, hyphen/underscore + VENUE-CHAIN + blank-chain duplicates, a phantom grid, a v4–v8 schema spread,
> mislabeled empty reasons, and (the keystone) **no materialised `expected_unattempted` state**. The hard-to-find-ness
> IS the bug. This plan makes the **data, manifest, data-status tab/UI, owner code, and docs** canonical so the next
> audit is one pass. Single-walk discipline applies — the multi-bucket sweep MUST be one bundled walk, not N ad-hoc
> walks.

## Architecture principle (the governing contract)

**Annotate honestly ONCE at write/consolidation-time (manifest, via the `expected_coverage()` oracle); READ everywhere
else. Never re-derive the expected set in a consumer.**

- **Manifest = canonical honest 4-state ledger.** Every IS∩UAC-expected cell carries one of: `captured` /
  `empty_confirmed[typed reason]` / `attempted_failed` / **`expected_unattempted`** (IS-listed + post-genesis +
  post-launch + in source-coverage, but no data yet). The typed empty reason IS the IS/UAC annotation.
- **Data-status summary + drilldown = VIEWS**: group/aggregate/display by READING `capture_status`; never re-derive.
  Operator filter-chips narrow at request time (never expand). The drilldown `_aggregate_counts` is generic → one fix
  serves IS/MTDS/MDPS/features.
- **Strategy/features preflight = read the SAME 4-state.** No re-deriving genesis/launch/IS rules per consumer.
- **CORRECTION 2026-06-01 (system-first save)**: `expected_unattempted` is **already canonical + the propagation chain
  is already shipped** — archived plan `expected_unattempted_propagation_chain_2026_05_12.md` (Phase 0 UAC reasons
  `EXPECTED_UPSTREAM_EMPTY`/`EXPECTED_OUTSIDE_PROCESSING_SCOPE` ✅; Phase 1 MTDS instruments-service pre-flight →
  `record_expected_unattempted` ✅; Phase 2 MDPS ✅). It is **writer/orchestrator-driven** (MTDS pre-flight reads the IS
  manifest and records owed cells on skip), **NOT** consolidator-driven. The DeFi manifest shows **0**
  expected_unattempted rows for ONE reason (deferred Phase 6,
  `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`): **no prod MTDS batch has RUN on the
  post-Phase-1+2 code yet** (defi 1.6M rows, 0 owed). So the fix is **run the existing chain + validate**, NOT build a
  parallel consolidator mechanism. (The earlier "never materialised / 0 source hits" reading was wrong — the handlers
  don't reference it because the pre-flight lives in the batch orchestrator, not per-handler.)

## `expected_unattempted` — the mechanism exists; RUN it for DeFi (corrected B0)

**Do NOT build a consolidator step (rejected — would duplicate the shipped chain).** The propagation chain already
exists (`expected_unattempted_propagation_chain_2026_05_12.md`, archived, Phases 0–2 shipped): the MTDS batch
orchestrator does an instruments-service **pre-flight** — it reads the IS manifest, and for every instrument the IS
lists that the batch will NOT attempt (outside scope / upstream empty), it calls `record_expected_unattempted(...)` with
reason `EXPECTED_OUTSIDE_PROCESSING_SCOPE` / `EXPECTED_UPSTREAM_EMPTY`. MDPS + features propagate it downstream. The
owed rows are written by the **writer**, at shard grain, gated by the **IS manifest** (which already encodes "this
instrument should exist") — exactly the operator's intent (`we have the instrument + it's post-genesis, but no data`).

**Why DeFi shows 0**: no prod MTDS batch has run on the post-Phase-1+2 code for the DeFi buckets since 2026-05-19. So
the remaining work is to **RUN the existing chain for the DeFi handlers + validate** (the deferred Phase 6), NOT
re-implement.

What to verify/wire (B0 corrected scope):

- Confirm the DeFi MTDS batch orchestrator path (oracle / perp / lst / lending / dex handlers) goes through the same
  instruments-service pre-flight that records `expected_unattempted` (Phase 1 wired CeFi/TradFi; confirm DeFi handlers
  are on that path — they may need wiring since DeFi uses dedicated buckets + a different orchestration).
- Run a DeFi MTDS dry-run on a sample date → confirm `expected_unattempted` rows generate with correct reasons.
- Then the denominator is honest automatically: `% = captured / (captured + empty + failed + expected_unattempted)` —
  consumers just read it (B1/B2/B3).
- Composes with `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md` (the deferred validation).

## Status legend: ✅ shipped · ⏳ ready/in-flight · ☐ todo · canonical todos below feed the orchestrator backlog

## A. Owner code (writers) — canonical writes

- [x] ✅ [CODE] P0. A1 pre-genesis empty-reason: oracle + evm-defi handlers classify via UAC `get_chain_genesis_date()`
      → `EXPECTED_PRE_GENESIS_CHAIN`. market-tick-data-service@840d85f1.
- [ ] [CODE] P1. A2 pre-venue-launch empty-reason: young perp/LST venues (PACIFICA/ASTER/ETHERFI pre-launch) →
      `EXPECTED_PRE_VENUE_LAUNCH` via UAC `get_protocol_launch_date()`/venue_launch_dates, same pattern as A1. Handlers:
      perp_funding + lst_rates + solana/evm defi.
- [ ] [CODE] P1. A3 data_type name SSOT at write: every handler writes the underscore canonical (`lending_indices` not
      `lending-indices`, `dex_pools` not `dex-pools`, `dex_swaps` not `dex-swaps`, `lst_rates` not `staking_yields`).
- [ ] [CODE] P2. A4 chain dimension always populated: QG guard fails a DeFi `record_captured`/`record_empty` with blank
      `chain` for a chain-scoped data_type.
- [ ] [CODE] P1. A5 LIGHTER perp_funding adapter fix: `SOURCE_RETURNED_ZERO` across full post-launch life (zkSync
      endpoint returns nothing) — verify endpoint/auth.
- [x] ✅ [CODE] P0. A6 `expected_unattempted` is ALREADY canonical in UAC (`honest_coverage.py`:
      `EXPECTED_UPSTREAM_EMPTY` + `EXPECTED_OUTSIDE_PROCESSING_SCOPE` reasons; shipped via
      `expected_unattempted_propagation_chain_2026_05_12.md` Phase 0). No new state to add — verified 2026-06-01.

## B. Manifest consolidation + data-status (owner code) — honest by default

- [ ] [DATA] P0. B0 (CORRECTED — do NOT build a consolidator step) RUN the existing expected_unattempted chain for DeFi:
      confirm the DeFi MTDS batch orchestrator goes through the instruments-service pre-flight that calls
      `record_expected_unattempted` (wire the DeFi handlers onto it if not), then run a prod DeFi MTDS batch so the owed
      rows generate; validate the denominator. Closes deferred
      `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`. parent_epic: manifest_master.
- [ ] [CODE] P1. B1 `coverage-summary` (`data_status_service._build_coverage_for_cat`): drop the `len(index)`
      self-referential denominator; read the 4-state (or expected-dates oracle) + `is_expected()` gate; align with
      `manifest-status`.
- [ ] [CODE] P0. B2 drilldown (`data_status_hierarchical._aggregate_counts`): count the 4th bin `expected_unattempted`
      so genuinely-missing cells appear in the tree (the most useful "where's the missing data" view). Generic path →
      fixes IS/MTDS/MDPS/features at once.
- [ ] [CODE] P1. B3 drilldown denominator: `% = captured / (captured+empty+failed+expected_unattempted)`;
      pre-genesis/launch render out_of_scope (already excluded by the oracle once B0 lands).
- [ ] [CODE] P2. B4 `data_status_rollup_worker.py`: read the 4-state, not manifest row count.
- [ ] [UI] P1. B5 deployment-ui drilldown: render the 4-state (esp. `expected_unattempted`) + per-chain split; badge
      legend. (playwright gate applies)

## C. Data / manifest migration (single-walk, bundled) — fix existing rows

- [x] ✅ [DATA] P0. C1 oracle-prices index relabel + Pyth dedup — **APPLIED 2026-06-01** via
      `plans/audit/results/defi_oracle_relabel_migration_2026_06_01.py --apply`: 728 pre-genesis relabel →
      `EXPECTED_PRE_GENESIS_CHAIN`; Pyth 1,185 chain `''`→`SOLANA` + dropped 1,034 dup empties; 9,717→8,683 rows; PYTH
      now all `chain=SOLANA` (1,447 = 1,185 captured + 262 owed). Original snapshotted →
      `_index/snapshots/pre_relabel_2026_06_01.parquet`. Fixes the consolidated index; durable until a full consolidator
      rebuild (which needs the source rows fixed too — the bundled C2–C7 walk). Writer A1 makes future writes correct.
- [ ] [DATA] P1. C2 data_type alias dedup across buckets: `lending-indices`→`lending_indices`, `dex-pools`→`dex_pools`,
      `dex-swaps`→`dex_swaps`, `staking_yields`→`lst_rates` (rename rows; data exists). ONE walk.
- [ ] [DATA] P1. C3 VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated `chain`. Same
      walk.
- [ ] [DATA] P1. C4 schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk. parent_epic:
      manifest_master.
- [ ] [DATA] P1. C5 phantom-grid delete: remove the cartesian `data_type × venue` empty grid in `market-data-tick-defi`;
      point data-status at the dedicated indexes.
- [ ] [DATA] P2. C6 Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM after C1.
- [ ] [DATA] P2. C7 pre-launch reason relabel for young venues (PACIFICA/ASTER/ETHERFI/LIDO/MARINADE pre-launch) — same
      walk as C2–C4.
- [ ] [DATA] P1. C8 fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only lst
      14/22, lending 6/21, perp 5/8; genuine absentees DRIFT-SOLANA (Solana MVP), FRAX, MORPHO, FLUID. parent_epic:
      defi_master.
- [ ] [DATA] P1. C9 legacy DeFi bucket object paths are pre-canonical —
      `day=/category=defi/venue=/chain=/instrument_type=/data_type=/file.parquet`: **`category=` not `asset_group=`**
      AND **no `pipeline_mode=` partition** (canonical raw_tick_data layout is
      `…/day=/pipeline_mode={mode}/asset_group={ag}/…`). The manifest ROWS carry pipeline_mode (handlers pass it); the
      object PATHS don't. Normalise the dedicated DeFi bucket paths in the same single-walk as C2–C4. parent_epic:
      manifest_master.

## D. Features propagation (L3) — coverage must reach features-service

- [ ] [DATA] P0. D1 features-onchain-defi is near-empty (3 rows); features-delta-one-defi + features-volatility-defi
      have NO index → derived features (staking*apy_bps/funding_rate_apy_bps/basis_bps/realized_vol*\*) absent. Run the
      features backfill for the in-scope DeFi instruments over the captured window. parent_epic: features_and_ml_master.

## E. CeFi perp leg (hybrid hedge) — fix-fetch

- [ ] [DATA] P0. E1 CeFi `derivative_ticker` (funding carrier) fetch failures: OKX-FUTURES + ASTER 100%
      attempted_failed; refresh to current (stale ~3–5 weeks). parent_epic: cefi_master.

## F. Docs / SSOT — record canonical forms

- [ ] [DOCS] P1. F1 `codex/02-data/defi-data-types-catalog.md`: underscore-canonical data_type names + dedicated bucket
      per type + hyphen aliases deprecated.
- [ ] [DOCS] P1. F2 `codex/02-data/availability-manifest-and-data-status.md` + `data-status-drilldown.md`: document the
      materialised `expected_unattempted` 4-state + the manifest-annotates-once/consumers-read principle + per-chain
      requirement.
- [ ] [DOCS] P2. F3 `_defi_manifest.py` reason-labeling docstring (~L213-220 "future refinement" TODO) → mark
      pre-genesis done (A1); note pre-launch (A2).
- [ ] [DOCS] P2. F4 CLAUDE.md "Manifest + honest absence" note: `expected_unattempted` is materialised at consolidation
      from the oracle; consumers read, never re-derive.

## Verification (full-execution criterion)

Re-run `plans/audit/results/defi_strategy_coverage_query_2026_06_01.py` + the drilldown: every DeFi cell carries a
canonical data_type (underscore), flat venue + populated chain, v9 schema, a typed reason; `expected_unattempted`
materialised so `% captured = captured / (captured+empty+failed+expected_unattempted)`; coverage-summary == drilldown ==
manifest-status denominators; features-onchain-defi populated for the in-scope window; the next audit needs one pass.
