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

## Sequencing — canonical migration is a GATE before ANY backfill (HARD RULE, operator 2026-06-01)

> Operator: "pipeline mode needs to be in legacy which needs to be migrated — this is why we keep having mess before
> more backfills. Everything must be fully migrated into the right form (env splits etc) so that manifest AND data AND
> data-status are all in their right format."

**No backfill, no B0-run, no `expected_unattempted` generation until the in-scope buckets are in canonical form.**
Backfilling into the legacy layout (no `pipeline_mode`, `category=` not `asset_group=`, no env split, v4–v8, hyphen/
VENUE-CHAIN names) just manufactures more non-canonical data to re-migrate. So **C (migration) is a foundation gate**;
C6 (Pyth backfill) / D1 (features backfill) / E1 (cefi fetch) / B0 (run the chain) are **review-blocked until C is GREEN
for the affected bucket.** Composes with single-walk discipline + the pre-migration-drain HARD RULE (stop VMs + snapshot
before cutover).

### Canonical target form — what "right format" means (every in-scope object + manifest row)

| Dimension | Legacy (now) | Canonical (target) |
| --- | --- | --- |
| Bucket env split | `oracle-prices-{project}` (no env) | `oracle-prices-{env}-{project}` (`-prd`/`-test`) — or fold into `market-data-tick-defi-{env}` |
| Asset-group key | `category=defi` | `asset_group=defi` |
| Pipeline mode | absent in path | `pipeline_mode=` hive partition (value `batch` or `live`) |
| Schema version | v4–v8 spread | v9 |
| data_type name | hyphen / `staking_yields` | underscore canonical (`lst_rates`, `dex_pools`, …) |
| Venue / chain | `UNISWAPV3-ETHEREUM`, blank chain | flat `venue` + populated `chain` |
| Empty reason | blank / `SOURCE_RETURNED_ZERO` mislabel | typed (`EXPECTED_PRE_GENESIS_CHAIN`, …) |
| 4th state | absent | `expected_unattempted` materialised by the run (B0) |

All of the above land in **one bundled single-walk** per bucket (C2–C5 + C7 + C9 + env-split), then the consolidated
`_index` + data-status reflect the canonical form, then backfills run into the correct structure.

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
- [ ] [CODE] P1. A2 pre-venue-launch empty-reason → `EXPECTED_PRE_VENUE_LAUNCH`. **Scoped 2026-06-01**:
      `perp_funding_handler` ALREADY does this for Aster (L344-353) — replicate for PACIFICA (currently
      `SOURCE_RETURNED_ZERO` pre-2025-12). `lst_rates_handler` (L512-535) + `solana_defi_handler` (L344/1486/1876)
      blanket-write `SOURCE_RETURNED_ZERO`. **Blocker found**: `get_venue_launch_date('defi', …)` returns None for
      LIDO/ETHERFI/MARINADE/PACIFICA/ASTER (only ETHENA populated) → **A2a: populate `DEFI_VENUE_LAUNCH_DATES` in UAC
      `registry/venue_launch_dates.py`** (parent_epic: manifest_master) OR wire the empty site to the token-level
      `get_lst_token_genesis` via the handler's venue→token map (the captured path at lst_rates_handler:399-404 already
      does this — extend it to the empty branch). Then A2b: wire the 3 handlers. Two clean units; do A2a first.
- [x] ✅ [CODE] P1. A3 data_type name SSOT at write — **verify-done 2026-06-01**: every DeFi handler `_DATA_TYPE`
      constant + `data_type=` literal is underscore-canonical
      (`dex_pools`/`dex_swaps`/`lending_indices`/`lst_rates`/`oracle_prices`/ `perp_funding`/`dex_pool_state`); **zero
      hyphen literals written by any handler**. The hyphen variants (`lending-indices`/`dex-pools`/`dex-swaps`) +
      `staking_yields` in the corpus are purely LEGACY data → fixed by C2.
- [ ] [CODE] P2. A4 chain dimension always populated: QG guard fails a DeFi `record_captured`/`record_empty` with blank
      `chain` for a chain-scoped data_type.
- [ ] [CODE] P1. A5 LIGHTER perp_funding adapter fix: `SOURCE_RETURNED_ZERO` across full post-launch life (zkSync
      endpoint returns nothing) — verify endpoint/auth.
- [x] ✅ [CODE] P0. A6 `expected_unattempted` is ALREADY canonical in UAC (`honest_coverage.py`:
      `EXPECTED_UPSTREAM_EMPTY` + `EXPECTED_OUTSIDE_PROCESSING_SCOPE` reasons; shipped via
      `expected_unattempted_propagation_chain_2026_05_12.md` Phase 0). No new state to add — verified 2026-06-01.
- [~] [CODE] P0. A7 **fetch-failure swallow bug — record `attempted_failed` not `empty_confirmed`** (operator 2026-06-01).
      Systemic: a fetch helper does `except Exception: … return []`, swallowing a timeout/DNS/RPC error → caller sees
      zero-rows-no-error → `record_empty(SOURCE_RETURNED_ZERO)` = a silent lie that the data is genuinely empty.
      **Fixed (mtds, re-raise → caller `record_failed`)**: `lst_rates_handler` L697, `oracle_prices_handler` L820/L948.
      **OPEN**: `lending_indices_handler` L989 (nested Aave RPC fallback — caller-routing review) + **sweep EVERY adapter
      in instruments-service + MTDS + features-service doing external I/O**. Per-adapter audit codified in
      `defi_master`(aa)/`mtds_mdps`(i)/`instruments`(h)/`features_and_ml`(u). Needs QG green before LDR. parent_epic: mtds_mdps_master.

## B. Manifest consolidation + data-status (owner code) — honest by default

- [ ] [DATA] P0. B0 (CORRECTED — do NOT build a consolidator step) RUN the existing expected_unattempted chain for DeFi:
      confirm the DeFi MTDS batch orchestrator goes through the instruments-service pre-flight that calls
      `record_expected_unattempted` (wire the DeFi handlers onto it if not), then run a prod DeFi MTDS batch so the owed
      rows generate; validate the denominator. **GATED on C-GREEN** — the owed rows must land in the canonical structure
      (env-split/`pipeline_mode`/`asset_group=`), so migrate first. Closes deferred
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

> **C is the foundation gate** (see Sequencing). One bundled single-walk per bucket applies C0+C2+C3+C4+C5+C7+C9
> together (no N ad-hoc walks). Backfills (C6/D1/E1) + B0-run are blocked until C is GREEN for the affected bucket.

- [ ] [DATA] P0. C0 **path + bucket canonicalisation (the foundational migration)**: for each dedicated DeFi bucket,
      rewrite object paths to the canonical layout — `category=defi`→`asset_group=defi`, add the
      `pipeline_mode={batch|live}` hive partition, and move into the **env-split** bucket (`{kind}-prd-{project}`, or
      fold into `market-data-tick-defi-prd`). This is the keystone the operator flagged: without it, every backfill
      re-creates the mess. Bundle with C2–C5/C7/C9 in the single walk. parent_epic: manifest_master.
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
- [ ] [DATA] P2. C6 Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM. **GATED on C0/C-GREEN** (backfill
      into the canonical env-split/`pipeline_mode`/`asset_group=` structure, never the legacy layout).
- [~] [DATA] P2. C7 reason relabel. **Chain-genesis portion: script ready + proven** —
      `plans/audit/results/defi_chain_genesis_relabel_migration_2026_06_01.py` (snapshot-protected, idempotent,
      `get_chain_genesis_date`-driven). Dry-run across all dedicated buckets: oracle ✅ done (C1, 728 rows); **lst-rates 75
      rows (SOLANA pre-2020-03-16) pending** — apply kept failing on flaky LOCAL GCS DNS (lst-rates/lending-indices time
      out); lending/perp/dex already clean on chain-genesis. **Run this on a VM in asia-northeast1** (stable in-region
      network) to land lst-rates. **Pre-VENUE-launch portion** (PACIFICA/ASTER/ETHERFI/LIDO/MARINADE pre-launch) stays
      blocked on A2a (`DEFI_VENUE_LAUNCH_DATES` populated) — bundle into the C2–C4 walk.
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
      features backfill for the in-scope DeFi instruments over the captured window. **GATED on C-GREEN** (features must
      read canonical raw, else they inherit the mess). parent_epic: features_and_ml_master.

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
