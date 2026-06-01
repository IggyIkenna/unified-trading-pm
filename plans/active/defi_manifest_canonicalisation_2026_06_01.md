---
title: "DeFi manifest + data-status canonicalisation (post 2026-06-01 coverage audit)"
created: 2026-06-01
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
status: active
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
source:
  - plans/audit/results/defi_master_audit_2026_06_01.md (the audit that surfaced all of this)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# DeFi Manifest + Data-Status Canonicalisation

> **Why this exists**: the 2026-06-01 DeFi coverage audit took many passes because the data is **not in canonical form**
> — scattered buckets, hyphen/underscore + VENUE-CHAIN + blank-chain duplicates, a phantom grid, a v4–v8 schema spread,
> and mislabeled reasons. The hard-to-find-ness IS the bug. This plan makes the **data, manifest, data-status tab, owner
> code, and docs** canonical so the next audit is trivial. Single-walk discipline applies — the multi-bucket sweep MUST
> be one bundled walk, not N ad-hoc walks.

## Status legend: ✅ shipped · ⏳ ready/in-flight · ☐ todo

## A. Owner code (writers) — make future writes canonical

- [x] ✅ A1. Pre-genesis empty-reason: oracle + evm-defi handlers classify via UAC `get_chain_genesis_date()` →
      `EXPECTED_PRE_GENESIS_CHAIN` not blanket `SOURCE_RETURNED_ZERO`. market-tick-data-service@840d85f1.
- [ ] ☐ A2. Pre-venue-launch empty-reason: young perp/LST venues (PACIFICA/ASTER/ETHERFI pre-launch) →
      `EXPECTED_PRE_VENUE_LAUNCH` via UAC `get_protocol_launch_date()` / venue_launch_dates, same pattern as A1.
      Handlers: `perp_funding_handler` / `lst_rates_handler` / solana+evm defi handlers.
- [ ] ☐ A3. data_type name SSOT at write: ensure every handler writes the **underscore** canonical (`lending_indices`
      not `lending-indices`, `dex_pools` not `dex-pools`, `dex_swaps` not `dex-swaps`, `lst_rates` not
      `staking_yields`). Grep `_DATA_TYPE =` + bucket `prefix` config; one canonical per type.
- [ ] ☐ A4. chain dimension always populated (no blank chain): Pyth/Solana writes already set `chain="SOLANA"` (current
      code OK — legacy rows are the issue, see C). Add a QG guard: DeFi `record_captured`/`record_empty` with blank
      `chain` for a chain-scoped data_type fails QG.
- [ ] ☐ A5. LIGHTER perp_funding: real adapter fix — `SOURCE_RETURNED_ZERO` across full post-launch life (zkSync
      endpoint returns nothing). Verify endpoint/auth.

## Architecture principle (codify — answers "manifest vs data-status job")

**Annotate honestly ONCE at write-time (manifest, via the `expected_coverage()` oracle); READ everywhere else. Never
re-derive the expected set in a consumer.**

- **Manifest = the canonical honest 4-state ledger.** Its job: apply the IS∩UAC / genesis / launch constraint ONCE, at
  write/consolidation time, materialising a row for **every expected cell** with one of: `captured` /
  `empty_confirmed[typed reason]` / `attempted_failed` / **`expected_unattempted`** (owed but never attempted). The
  typed empty reason (`EXPECTED_PRE_GENESIS_CHAIN`, `EXPECTED_PRE_VENUE_LAUNCH`, `EXPECTED_KNOWN_SOURCE_GAP`, …) **is**
  the IS/UAC annotation. Confirmed gap 2026-06-01: `expected_unattempted` is **never materialised** (0 source hits;
  oracle bucket has only the 3 attempted states; `expected=True` on every present row = useless for "what's missing"). A
  cell that SHOULD exist but was never enumerated has **no row** → invisible to every consumer.
- **Data-status summary + drilldown = VIEWS** over the manifest: group / aggregate / display. They must **read** the
  manifest's 4-state, not re-derive the expected set. Operator filter-chips narrow at request time (never expand). The
  drilldown's `_aggregate_counts` is **generic across all services** (one 3-tuple code path) — so materialising the 4th
  state + reading it fixes IS / MTDS / MDPS / features **in one place**.
- **Downstream preflight (strategy / features) = read the SAME 4-state.** "Can I run this archetype over this window?" =
  read manifest `capture_status`, no re-deriving genesis/launch/IS.
- **The benefit (the whole point of the manifest):** one canonical honest surface for preflight, instead of every
  consumer re-implementing IS/UAC/genesis/launch rules. The audit found the failure mode this prevents: three consumers
  (manifest-status ✅, coverage-summary self-referential ❌, drilldown 3-state ❌) re-derive "what should exist" three
  different ways and **disagree**. Root fix = materialise-once, read-everywhere.

## B. Data-status tab + API (owner code) — honest numbers by default

- [ ] ☐ B0. **ROOT FIX — materialise `expected_unattempted` in the manifest** (the `expected_coverage()` oracle already
      computes the expected set): at consolidation, emit an `expected_unattempted` row for every IS∩UAC-expected cell
      with no attempt. Then B1/B2/B3 collapse to "read the manifest 4-state" not re-derive. One fix → all services + all
      consumers honest. parent_epic: manifest_master.
- [ ] ☐ B1. `coverage-summary` (`data_status_service._build_coverage_for_cat`): replace `len(index)` self-referential
      denominator with the expected-dates oracle (`_mtds_expected_dates_cached`) + `is_expected()` scope gate; align
      with `manifest-status`. (audit Gap A/B/C)
- [ ] ☐ B2. **Drilldown** (`data_status_hierarchical.get_hierarchical_drilldown`): add the 4th bin —
      `expected_unattempted` / `MISSING_EXPECTED` — by enumerating IS∩UAC expected `(venue,chain,data_type,date)` and
      diffing vs manifest-present rows. Today it only counts the 3 manifest-present states, so genuinely-missing cells
      are invisible in the tree (the most useful "where's the missing data" view). (drilldown audit gap B/E)
- [ ] ☐ B3. Drilldown chain-genesis / venue-launch clipping: pre-genesis cells must render `out_of_scope`, not counted
      in the denominator (drilldown audit gap E/MED).
- [ ] ☐ B4. `data_status_rollup_worker.py`: verify it shares the expected-dates denominator (not manifest row count).
- [ ] ☐ B5. deployment-ui: surface the 4-state validity + per-chain split in the drilldown UI (composes with B2/B3).

## C. Data / manifest migration (single-walk, bundled) — fix existing rows

- [⏳] C1. **Oracle-prices index relabel + Pyth dedup** — script ready
  `plans/audit/results/defi_oracle_relabel_migration_2026_06_01.py` (dry-run confirmed: 728 pre-genesis relabel
  [CHAINLINK ARB/BASE/OPT blank + BASE 275 SRZ]; Pyth 1,185 chain `''`→`SOLANA` + drop 1,034 dup empties). Snapshots
  before write. **Apply once network/consolidator-safe** (index last rebuilt 2026-05-20, not live-rebuilt).
- [ ] ☐ C2. data_type alias dedup across buckets: `lending-indices`→`lending_indices`, `dex-pools`→`dex_pools`,
      `dex-swaps`→`dex_swaps`, `staking_yields`→`lst_rates` (rename rows; data exists). Bundle into ONE walk.
- [ ] ☐ C3. VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated `chain`. Same walk.
- [ ] ☐ C4. Schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk.
- [ ] ☐ C5. Phantom-grid delete: remove the cartesian `data_type × venue` empty grid in `market-data-tick-defi`
      (perp_funding on Uniswap/Lido/Aave etc.); point the data-status denominator at the dedicated indexes.
- [ ] ☐ C6. Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM after C1.
- [ ] ☐ C7. Pre-launch reason relabel for young venues (PACIFICA/ASTER/ETHERFI/LIDO/MARINADE pre-launch) — same walk as
      C2–C4.

## D. Docs / SSOT — record the canonical forms

- [ ] ☐ D1. `codex/02-data/defi-data-types-catalog.md`: state the underscore-canonical data_type names + dedicated
      bucket per type + that hyphen aliases are deprecated.
- [ ] ☐ D2. `codex/02-data/data-status-drilldown.md`: document the 4-state denominator + per-chain requirement (B2/B3).
- [ ] ☐ D3. `_defi_manifest.py` reason-labeling docstring (lines ~213-220 "future refinement" TODO) → mark done for
      pre-genesis (A1), note pre-venue-launch (A2) remaining.

## Verification (full-execution criterion)

Re-run `plans/audit/results/defi_strategy_coverage_query_2026_06_01.py` + the drilldown: every DeFi cell carries a
canonical data_type (underscore), flat venue + populated chain, v9 schema, and a typed reason; no hyphen/underscore
dupes, no blank chains, no phantom grid; coverage-summary == manifest-status == drilldown denominators; the next audit
needs one pass.
