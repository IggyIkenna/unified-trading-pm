---
doc_type: plan
title:
  DeFi consolidated close-out — one ordered pass (canonical target → residual canon walk → denominator → coverage →
  forward) mirroring the cefi/tradfi close-outs
summary:
  Single coordination plan that AGGREGATES (references, does NOT duplicate) every open defi + defi-touching IS/MTDS
  plan/issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md /
  tradfi_consolidated_closeout_2026_07_18.md. Authored 2026-07-18 from a 6-agent audit (7 active defi plans + ~35 issues
  + live GCS bucket audit + live manifest distinct-values query) plus direct operator rulings. UNLIKE cefi/tradfi the
  DeFi FOUNDATIONAL migration already ran (canonical-migration-defi-20260618-180603 → v9 + asset_group=defi +
  pipeline_mode + source; dedicated→shared bucket consolidation done) — so what remains is a RESIDUAL canon walk, a
  now-RESOLVED POOL-id policy, a large genuinely-open coverage/denominator effort, a culled-venue purge, and restoring
  the removed data-status enumeration view. The operator-decided canonical target (id grammar, SPOT_ASSET vs SPOT_PAIR
  vs POOL, the two-id model, empty_confirmed vs out-of-scope) is captured here as the target; the actual code+data
  changes are THIS plan's scope (cefi/tradfi findings are passed to their sibling plans).
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    defi,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    pool,
    lending,
    spot-asset,
    manifest,
    empty-confirmed,
    denominator,
    coverage,
    backfill,
    bucket,
    enumeration,
    venue-purge,
  ]
related:
  [
    /plans/archive/defi_consolidated_closeout_history_2026_07_25.md,
    /plans/active/defi_strategy_pnl_axis_index_2026_07_24.md,
    /plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
    /plans/archive/2026_07/defi_gmx_venue_removal_finalize_2026_07_25.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md,
    /plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    /plans/archive/2026_07/mtds_defi_dex_zero_capture_protocols_2026_07_14.md,
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/ao_dispatch_cooldown_and_park_2026_07_20.md,
    issues/estate_orphan_assessment_2026_07_21.md,
    issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md,
    issues/defi_five_never_captured_venues_fix_2026_07_22.md,
    issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md,
    issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md,
    issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md,
    issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md,
    issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
    issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    issues/lst_exchange_rate_data_availability_2026_07_21.md,
    issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/archive/issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md,
    issues/mtds_perp_funding_backfill_hang_2026_07_14.md,
    issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md,
    issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
    issues/phantom_captures_defi_2026_06_28.md,
    issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md,
    issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: 2026-07-18
last_updated: 2026-06-27
  2026-06-27 2026-06-27 "2026-07-25" # AO-readiness pass: related: reachability (6 new docs), 2 stale line-number
  # cross-refs -> content refs, defi.2 resume-crons split (operator ruling, task_template.md finding P),
  # write_defi_rows DoD, Split-notice table +2 rows, 2nd extraction pass into the history doc -- was:
  # "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
depends_on: [defi_track01_per_instrument_and_canon_id_2026_07_24, defi_lending_writer_retire_prerequisite_2026_07_20]
gate_on_depends:
  true # Tracks 5/8 and the "Resume paused DeFi crons" items are repeatedly gated in prose on "Track 1"
  # (R1-R8, now forked out to defi_track01_per_instrument_and_canon_id_2026_07_24) and on the LENDING migration
  # prerequisite in defi_lending_writer_retire_prerequisite_2026_07_20 — real, un-machine-enforced cross-plan gates
  # found by the 2026-07-24 AO-flip-safety audit; encoded here so a future `assigned_vm: planning` flip can't dispatch
  # gated tracks before their real prerequisites land.
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  Operator, 2026-07-18 — after directing the cefi + tradfi consolidated close-outs, asked for the same one-pass DeFi
  close-out that aggregates ALL defi IS/MTDS plans+issues, audits the GCS buckets for the canonical path, states the
  canonical target (paths, instrument uids) from buckets+UAC+code+plans, defines the empty_confirmed vs out-of-scope
  basis, and reconciles SPOT_ASSET vs SPOT_PAIR vs POOL — reconciled in code AND backfilled data AND forward data.
  Authored + ground-truth-verified from a 6-agent audit (slot-4, 2026-07-18) with live GCS reads + operator rulings.
---

# DeFi consolidated close-out — one pass to canonical, honestly-covered, forward-clean

> **Purpose.** ONE place that aggregates every open defi + defi-touching IS/MTDS plan/issue into a single ordered pass.
> This plan **references** the source docs; it does not duplicate them. Close a track by closing its source doc(s), then
> tick it here. Mirrors the cefi/tradfi consolidated close-outs. **Ownership (operator 2026-07-18)**: THIS plan is the
> target for the actual DeFi code + data changes; the audit's cefi/tradfi findings + operator decisions are passed to
> the two sibling plans.

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 3447 lines and forked 3 ways**, per the operator-approved split in
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 11: "Extract Strategy/PnL index + 1800-line
> historical log") plus an additional fork (Track 1) needed to actually land the doc under 1000 lines. Every todo and
> every Progress Log line was moved **verbatim** to its destination — nothing was summarized, rewritten, or silently
> dropped; every still-open item surfaced by the historical Progress Log's two "Deferred work after ..." tables was
> converted into a proper todo under "Open follow-ups" below rather than archived away.
>
> | Child doc                                                                                                                                                    | Carries                                                                                                                                                                                |
> | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | [`defi_strategy_pnl_axis_index_2026_07_24.md`](/plans/active/defi_strategy_pnl_axis_index_2026_07_24.md)                                                     | The **strategy/PnL/backtest-engine axis** (`strategy-service`) — a genuinely different set of tracks from this doc's data/canonicalization axis; entry point for that whole thread.    |
> | [`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)                             | The **per-instrument re-architecture (R1-R8)** + **Track 1 residual canon walk** — the single largest, most gating body of work (⛔ gates Half-B historical canonicalisation).         |
> | [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md) (archived, `status: complete`) | The 2026-07-18 canonical-target **contradiction-resolution audit** (75 findings, verbatim) + the full **chronological Progress Log** (2026-07-18 → 2026-07-23, ~2090 lines, verbatim). |
> | [`defi_track5_coverage_mvp_backfill_2026_07_24.md`](/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md)                                           | **Track 5 (COVERAGE)** — backfill to MVP-100%, incl. the MVP-universe gap-audit + the mvp-defi backlog unpark flipper note; C-GREEN gated on Track 1 → Track 3.                        |
> | [`defi_consolidated_closeout_aggregated_sources_2026_07_24.md`](/plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md)                   | The **discoverability index** of every other defi-relevant plan/issue with its open-todo digest — read this to find a doc not directly linked from this plan.                          |
> | [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md) (`status: complete`)                   | **Track 6 (RENDER) + Track 7 (CULL)**, plus (2nd pass, 2026-07-25) every closed item from Tracks 2/3/4/8 + Open-follow-ups + the full 2026-07-24→2026-07-25 session Progress Log tail. |
>
> **Open-todo counts per child (2026-07-24, so a fresh session doesn't have to open each one to see what's live)**:
>
> - `defi_strategy_pnl_axis_index_2026_07_24.md` — **0 own top-level todos** (it's an entry-point index that references
>   other plans rather than carrying its own checkboxes; most of what it points to is already indexed in this doc's
>   "Aggregated source docs" § Strategy/PnL/backtest axis below).
> - `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — **13 open** (5 P0, 3 P1, 5 P2 — 11 plain-open + 2 `[~]`
>   partial; re-verified LIVE 2026-07-25 via `grep -c '^- \[ \]'` + the 2 partials, corrects the earlier stale "18 open
>   (6 P0, 7 P1, 5 P2)" count, which pre-dated several checkbox flips incl. both of that count's own cited "Top P0s" —
>   the legacy `dex_pools/`/`lending_indices/` fold and the legacy GLUED-VENUE flat-tree investigation are now BOTH
>   `[x]` done). Top P0s as of 2026-07-25: (1) the R3-run full-corpus per-instrument migration VM is still applying
>   (2022+ years + `rebuild_defi_manifest` remain, ~8-12h); (2) the catalogue-venue gap fix is SHIPPED but its
>   re-enum/re-rollup is DEPLOY-GATED, not yet run; (3) the ~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN Wave-D migration (code
>   done, data migration open); (4) the residual canon walk C2-C12 (6 sub-items, data-side read pending); (5)
>   eliminating the address/UUID fallback in `canonical_instrument_id` for POOL/LENDING (operator ruling 2026-07-21).
> - `defi_consolidated_closeout_history_2026_07_18.md` (archived) — **0 open todos**, confirmed via `grep -c '^- \[ \]'`
>   — it is a `status: complete` record doc (audit findings + historical Progress Log), not a live work tracker.
>
> **Retained here**: the Canonical target spec + Operator rulings (foundational context every fork depends on), Tracks
> 2-8 (the remaining open work), the "Open follow-ups" list (every still-open item recovered from the historical
> Progress Log's deferred-work tables), the aggregated source-doc index, and a condensed pointer replacing the full
> tick-by-tick Progress Log (see the archive doc for full historical detail).

## Headline verdict — how DeFi differs from cefi/tradfi

- **The DeFi FOUNDATIONAL migration already ran.** `canonical-migration-defi-20260618-180603` (C0d in
  `data_completion_defi_2026_07_15.md`) took every DeFi object to v9 + `asset_group=defi` + `pipeline_mode=` + a
  `source` column; the dedicated→shared bucket consolidation (`defi_dedicated_bucket_shared_migration_2026_07_13.md`) is
  done (all kinds resolve `kind="tick-data"` on the single `market-data-tick-defi-prd-central-element-323112`). So the
  cefi/tradfi "0% canonical, migrate everything" starting point does NOT apply.
- **What remains is different in kind:** (1) a RESIDUAL canon walk the big migration didn't finish (C2–C12); (2) a
  now-RESOLVED POOL-id policy contradiction; (3) a culled-venue purge; (4) a large genuinely-open coverage/denominator
  effort (the ~63.9M `expected_unattempted` seed, the DRIFT/Velocity backfill, Morpho never wired, a dead Curve/Optimism
  subgraph); (5) restoring the removed data-status "what exists" enumeration view. DeFi's biggest open track is
  **coverage**, not id-canonicalisation.

## Strategy/PnL/backtest-side DeFi tracking — SECOND axis, moved out 2026-07-24

> This doc's scope (below) is the DeFi **data/canonicalization** axis (IS/MTDS-touching) only. The **strategy/PnL/
> backtest engine** axis (`strategy-service`) — a genuinely different set of tracks (LST rate coverage, DeFi interest
> PnL correctness, the orphaned-archetype tick-builder wiring program, collateral-validation dead-import) — now has its
> own entry-point index:
> **[`defi_strategy_pnl_axis_index_2026_07_24.md`](/plans/active/defi_strategy_pnl_axis_index_2026_07_24.md)**. Both
> plans are parallel, not sequential — a fresh session should read both to pick up all open DeFi work.

## Per-instrument re-architecture + Track 1 — CANON (instrument-ID canonicalization)

> **Forked out 2026-07-24** (line-cap remediation) to
> [`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)
> — the single largest, most gating body of work in this close-out (⛔ gates Half-B historical canonicalisation). Read
> that plan for the R1-R8 per-instrument writer re-architecture + the full Track 1 residual canon walk. The Canonical
> target spec + Operator decisions immediately below are the shared context both this fork and Tracks 2-8 depend on.

## Canonical target (operator-decided 2026-07-18 — the thing we converge all four surfaces on)

The four surfaces that must agree post-migration: **(1) GCS parquet path**, **(2) parquet
`instrument_id`/`canonical_instrument_id` columns**, **(3) manifest `_index` key**, **(4) data-status render**. For DeFi
**TARGET (operator 2026-07-18): DeFi is FLAT-PER-INSTRUMENT** — one parquet per instrument, filename = the symbolic
canonical id (`filename == instrument_id == manifest key`), exactly like cefi/tradfi. The old multi-instrument
capture-batch (`{venue}_{CHAIN}_{capture_ts}.parquet`) model is **RETIRED** — see the "Per-instrument re-architecture"
section above. The address stays a content column + the IS-definition/join key.

### Path template (operator-locked; forward writer already emits it)

```
gs://market-data-tick-defi-{prd|test}-central-element-323112/raw_tick_data/by_date/day={YYYY-MM-DD}/
  pipeline_mode={mode}_{source}/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/
  instrument_type={itype_lower}/data_type={dt}/{leaf}.parquet
```

Segment order is **venue BEFORE chain** (locked in `/codex/02-data/defi-canonical-naming-ssot.md`; the code + live GCS
confirm it — `per-asset-group-bucket-layouts.md` and `GCS_PATHS.md` are STALE the other way and must be corrected).
`instrument_type` in the PATH is lowercase.

### Instrument-uid grammar per DeFi type (real `build_canonical_instrument_id` output; UPPER type-segment, case-PRESERVED symbol)

Base = `VENUE-CHAIN:TYPE:SYMBOL` (DeFi is the only AG whose venue segment carries a `-CHAIN` suffix; on-chain token case
is preserved — `aUSDC`, `stETH`).

| type                                                                                                                                                     | grammar                                                                                                        | example                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `SPOT_ASSET`                                                                                                                                             | `VENUE-CHAIN:SPOT_ASSET:SYM`                                                                                   | `UNISWAP_V3-ETHEREUM:SPOT_ASSET:WETH`                                           |
| `POOL`                                                                                                                                                   | `VENUE-CHAIN:POOL:TOKEN0-TOKEN1[-FEE_BPS]` — **3-segment, fee INSIDE the symbol (operator ruling 2026-07-18)** | `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`                                        |
| `A_TOKEN` / `DEBT_TOKEN`                                                                                                                                 | supply / borrow leg (isolated markets append `marketId[:8]`)                                                   | `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC` · `MORPHO-BASE:A_TOKEN:AUSDC-EURC-<marketId8>` |
| `LST` / `YIELD_BEARING` / `STAKING`                                                                                                                      | staking token / vault share                                                                                    | `LIDO-ETHEREUM:LST:stETH` · `ETHENA-ETHEREUM:YIELD_BEARING:sUSDe`               |
| `PERPETUAL` (on-chain, DeFi lane — GMX was the example venue, **REMOVED 2026-07-25**, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) | `VENUE:PERPETUAL:SYM` — **NO chain suffix** (routes cefi-simple branch)                                        | `GMX:PERPETUAL:BTC-USD` (historical example; venue removed)                     |
| `SOLANA_AMM_POOL` / `SOLANA_LENDING`                                                                                                                     | Solana grains                                                                                                  | `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC`                                          |

### The two-id model (operator ruling 2026-07-18 — "that's fine as long as downstream uses what it needs the right way")

Every address-identified DeFi row carries TWO ids and this is INTENTIONAL — **do NOT mass-rewrite the 22.3M
address-keyed rows**:

- **`canonical_instrument_id` (the canonical/human id)** = the symbolic `VENUE-CHAIN:TYPE:SYMBOL` above. Carries the
  instrument_type; carries NO raw addresses. This is the operator's "type-in-id, symbol-in-id, addresses live in the
  definition" ruling.
- **`instrument_id` (the machine/operational key)** = the address-anchored form (POOL→`pool_address.lower()`,
  SPOT_ASSET→`spot_asset:{chain}:{token_addr}`). Used as the manifest join key + MTDS content-join. The pool/token
  CONTRACT ADDRESS lives HERE and in the instrument DEFINITION (catalogue) — NEVER inside the canonical id.
- **POOL-id policy = Option A (test wins)**: POOL rows legitimately DIVERGE (`instrument_id`=address,
  `canonical_instrument_id`=symbolic key). For SPOT_ASSET the two CONVERGE by construction. Fix the backfill-script
  docstring that wrongly asserts convergence "pool or not"; ensure every consumer reads the RIGHT one (join→address,
  display/canonical→symbolic).

### SPOT_ASSET vs SPOT_PAIR vs POOL — the decision rule

1. CeFi order-book two-token quoted market (or any two-token quoted price) → **`SPOT_PAIR`** (asset_group=cefi, no
   chain).
2. A single on-chain token you want oracle-price / transfers / gas / bridge / gov / MEV data for → **`SPOT_ASSET`**
   (defi, address-keyed; `canonical_instrument_id := instrument_id` so the two CONVERGE). Carries the
   `DEFI_SPOT_ASSET_*` data_types.
3. An AMM/DEX liquidity-pool contract (two legs + fee + pool address) → **`POOL`** (defi, pool-address-keyed; DIVERGE).
   Its two legs are each individually a `SPOT_ASSET`; the pool is a distinct instrument. Solana spot-DEX
   orderbook/quote/per-swap shards use **`DEX_POOL`**/`SOLANA_AMM_POOL`.

### Lending — ONE SSOT (operator ruling 2026-07-18)

`A_TOKEN` (supply) + `DEBT_TOKEN` (borrow) IS the canonical split (net_value = supply − borrow needs both legs). The
legacy flat **`LENDING`** type is retired: its ~16.7M enumerated rows migrate to the split, and the split is baked into
`build_instrument_catalogue.py` row-construction (not a catalog-only patch a `--mode full` rebuild reverts). The
enumeration audit's stray "fold a_token→lending" is BACKWARD — a_token/debt_token are canonical; `lending` migrates.

### empty_confirmed vs out-of-scope (the denominator basis)

Discriminator = **does a manifest row exist**.

- **`empty_confirmed`** — a cell INSIDE the could-exist universe, attempted, source PROVABLY returned 0 rows (typed
  `EmptyConfirmedReason` + `FetchEvidence` or UTL hard-raises `UnprovenHonestAbsenceError`). A materialized row
  (`row_count=0`, blank id). **EXCLUDED from `reachable_coverage`, RETAINED in `all_shards`.** Stays visible. DeFi-legit
  reasons only: `EXPECTED_PRE_GENESIS_CHAIN`, `EXPECTED_PRE_VENUE_LAUNCH`, `EXPECTED_PROTOCOL_PAUSED`,
  `EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED`, `SOURCE_RETURNED_ZERO`, proposed `EXPECTED_SUBGRAPH_DEINDEXED`
  (Curve/Optimism). An instrument-day source-zero on an ALIVE day = `attempted_failed`, NOT silent empty.
- **out-of-scope** — a `(venue, itype, data_type)` tuple that should NEVER generate → **NO manifest row**
  (`ExpectedState.NOT_IN_SCOPE` / `is_valid_shard_key=False` / `is_mvp()=False`). **Clipped from BOTH numerator and
  denominator.** Removed venues leave the registries entirely.
- **The trap (why the denominator lies today):** ~63.9M could-exist cells were never materialized as
  `expected_unattempted` by the writer → no row → they silently masquerade as out-of-scope and UNDERSTATE the
  denominator. Honest only after a fresh single-walk seeds them (gated on the phantom+duplicate purge first).

## Operator decisions applied (2026-07-18)

- **POOL canonical key = 3-segment, fee inside symbol** (`UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`) — the
  `canonical_id_builder` SSOT form, not the 4-segment `DefiPoolIdentity.glued_pair_id` (`…:POOL:USDC-WETH:500`). The
  4-segment form is retired.
- **Two-id model kept** (Option A) — no mass address→symbol rewrite; ensure symbolic `canonical_instrument_id` coexists
  on every row + downstream reads the right id.
- **Retire legacy `LENDING`** → migrate ~16.7M rows to the A_TOKEN/DEBT_TOKEN split + bake into the catalogue builder.
- **instrument_type case**: **⛔ corrected 2026-07-20, operator ruling D1 — ~~"lowercase in the PATH + manifest COLUMN
  (writer grain), UPPER stays only in the id SEGMENT"~~.** Three separate legs: manifest **COLUMN → UPPERCASE**
  (catalogue wins, ruling D1) · GCS **path segment → lowercase** (unchanged) · **id middle segment → UPPER**
  (unchanged). Do not bundle path and column into one case. SSOT: `/codex/02-data/cross-asset-canonical-target-ssot.md`
  §7.
- **Culled-venue purge = dead-only, snapshot-first, keep LIGHTER + EXTENDED** (see Track 7).
- **Combos = leg-aware signed-weight spec** (cross-AG) — see Track 1 + the cefi/tradfi hand-offs.
- **Restore the removed data-status enumeration** (raw distinct-values audit view) — Track 6.

---

## Track 2 — STORE: path authority + bucket hygiene (⛔ flat-vs-hive must be pinned) · P0

- **Sources**: `defi_dedicated_bucket_shared_migration_2026_07_13.md` (2 open P2/P3 + C0f),
  `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`,
  `issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`,
  `issues/features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15.md`,
  `/plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`,
  `issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md`.
- **Close-out criterion**: one pinned path shape; zero dedicated-bucket refs; TF state matches live estate;
  lending-indices legacy bucket deleted (snapshot-first).

> **⛔ corrected 2026-07-20 — the DELETE clause in the first todo below is STALE and executing it DESTROYS DATA.
> Disposition is now FOLD-not-delete.** The "dead prefixes" premise was **overturned by R5 in this same plan**
> (`:254-262`) — content-verify found PARTIAL-OVERLAP, not duplication: legacy=98 pools, canon=99, **intersection only
> 66**, with **32 legacy-only high-TVL raydium pools ABSENT from canon** (XMR/USDC $47M, BNB/USDC $18M, USD1/USDC
> $9.9M, ZEC/USDC $7.5M). A live GCS probe on 2026-07-20 corroborates and sharpens this: on `day=2026-04-14` the
> canonical twin **does** exist for ORCA (14,094 objs) / RAYDIUM (100 objs) / KAMINO lending_indices (47 objs) under
> `instrument_type=solana_amm_pool`, but **KAMINO `dex_pool_state` = 0 and SOLEND = 0** — for those two cells the legacy
> objects are the **only copy in existence**. A snapshot-first delete is NOT adequate protection. **Required order: (1)
> content-UNION the 32 legacy-only pools + the 2 twin-less cells into canon; (2) repoint
> `execution-service/execution_service/providers/solana_amm_depth_provider.py:41` — which STILL READS this legacy shape
> at runtime — to the canonical `data_type=dex_pool_state` path AND fix its broken `resolve_bucket_name` call at
> `:248-254` (`kind="market-data-tick-defi"` is a bucket-name FRAGMENT with no yaml key, and `env=`/`project_id=` are
> not parameters, so it RAISES uncaught); (3) ONLY THEN consider the delete.** Full evidence + resolution criteria:
> `/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`.

> **2 closed items extracted 2026-07-25** (line-cap remediation, 2nd pass) — the path-shape-pin code fix (dexpool
> writer-order bug) + the stale-codex-docs correction, both done; full text verbatim in
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

- [ ] [OPERATOR] P1. **Delete the lending-indices legacy bucket (C0f)** + resolve TF estate drift
      (`market_data_defi_lending_indices_prd` still declared) + the bare `features-onchain` vs asset-group bucket. All
      GCS/bucket DELETEs are snapshot-first, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
      — an agent must never run the delete itself. (repos: deployment-service, market-tick-data-service)
- [ ] [BACKEND] P0. **NEW 2026-07-24 — `write_defi_rows()` writes the bare SYMBOL as the filename leaf, not the ruled
      canonical_instrument_id, AND DeFi batch capture is actively writing (NOT stopped as the codex/plan text assumes) —
      so this is a growing defect, not frozen residue.** 13/13 sampled objects fail the UAC id-form oracle
      (`canonical_path_violations`, `_ID_FORM_CHECKED_ASSET_GROUPS={cefi,defi}`); `canonical-cutover-register.md` §5 +
      `defi-canonical-naming-ssot.md`'s WRITE-MODEL banner both incorrectly state capture is fully stopped — measured
      new objects with `time_created=2026-07-24` (same day as probe). Full evidence + repro:
      `/plans/active/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`. **Done
      when** a fresh `canonical_path_violations()` id-form sample against `write_defi_rows()` output across a multi-day
      window returns 0 violations. (repos: market-tick-data-service, unified-api-contracts, unified-trading-pm)

## Track 3 — DENOM: empty_confirmed / denominator honesty · P1

- **Sources**: `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (measured 63.9M via the v2 enumerator),
  `issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md`, `defi-completeness-oracle.md`,
  `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`,
  `issues/defi_catalogue_available_to_false_delisting_2026_07_20.md`.
- **Close-out criterion**: fresh single-walk yields zero silent-`M` rows; denominator honest.

- [ ] [DATA] P0. **PURGE first, then seed.** Purge the 1.79M duplicate + ~219.5K phantom rows (re-verify the 219,529
      detected vs 219,632 flipped delta), THEN apply the ~63.9M `expected_unattempted` seed (operator write-volume gate;
      incl. 812,055 solana-pool-vocab rows + 215,864 non-POOL EU rows). The "1M" framing is the old safety-cap slug —
      the real target is 63.9M. **Sequence AFTER the glued-id manifest rebuild** (both touch the same consolidated
      index). **Re-verify `spot_pair`/`spot_asset` counts against the CURRENT catalogue before applying** — the 63.9M
      figure (incl. `spot_pair` 143K) was measured 2026-07-10 against a catalogue snapshot that predates the 2026-07-16
      SPOT_ASSET population backfill + the 2026-07-21 reference-only reclassification; live re-measurement 2026-07-24
      shows catalogue SPOT_ASSET=1,390 (well-populated, 17 venues, 0 DRIFT) and catalogue SPOT_PAIR=56
      (CHAINLINK/PYTH/EIGENLAYER only, 0 DRIFT) with 0 `spot_pair` rows in the live consolidated manifest index — the
      143K figure is stale/never-applied, not a live target. (repos: market-tick-data-service)
- [ ] [BACKEND] P1. **Add the `EXPECTED_SUBGRAPH_DEINDEXED` reason** to reclassify the 952 false Curve/Optimism
      `attempted_failed` → honest-empty; reconcile `spot_asset` absence from the enumerated catalogue (the v2 corpus
      predates SPOT_ASSET population; `spot_pair` 143K is partly the culled DRIFT SPOT leak). **Parent stays open — the
      `--apply` sub-item below is genuinely pending; the other 3 are DONE.** (repos: unified-api-contracts,
      instruments-service)
  - [x] Reason SHIPPED `unified-api-contracts@e893e5c9`.
  - [x] Reclassification script SHIPPED `instruments-service@73100d4e`
        (`scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`), dry-run verified against live prod
        — found **144** matching rows today, not 952 (count shrank over the 9 intervening days of pipeline activity). A
        bug in the first script version (matching the full 45-char subgraph id) initially found 0 because the manifest's
        `error_reason` column truncates at 80 chars; fixed to match the untruncated message prefix, then confirmed
        against an independent raw pandas count of the same 144 rows.
  - [ ] `--apply` NOT YET RUN — 2 VM-launch attempts 2026-07-24 both FAILED differently; stopped (stall-safety) rather
        than blind-retry a 3rd time. **Attempt 1** rc=2 file-not-found — root cause: `setup-data-pipeline-vm.sh`'s
        `canonical-migration` branch (`:1187`) hardcodes `cd "$WORKSPACE/mtds"` regardless of `VM_SERVICE`, so this
        instruments-service script can't be found; a real launcher bug (new follow-up below), not user error. **Attempt
        2** (workaround: `bash -c 'cd .../instruments && python ...'`): `run.log` never got created at all — likely the
        nested quoting breaking the startup script's own `python`→venv-python substitution. Population still tiny (144
        rows) and low-growth — safe to leave open. Full detail:
        `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`.
- [ ] [INFRA] P2. **NEW 2026-07-24 — fix the `canonical-migration` `VM_TASK` mtds-hardcoded `cd` bug** found above (the
      canonical-migration `VM_TASK` case branch's hardcoded `cd` path in `setup-data-pipeline-vm.sh`) — mirror the
      `VM_SERVICE`-keyed instruments branch other cases already use. (repo: deployment-service)
  - [x] `spot_asset`/`spot_pair` reconciliation investigated + resolved via live re-measurement (see the P0 item's
        footnote above) — both were stale/non-issues, not a coding task.

> **2 closed items extracted 2026-07-25** (line-cap remediation, 2nd pass) — the `available_to` false-delisting fix
>
> - the non-POOL EU terminal-state decision, both done; full text verbatim in
>   [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

## Track 4 — CAP: zero-capture protocols · P2

- **Sources**: `mtds_defi_dex_zero_capture_protocols_2026_07_14.md` (folded in + archived 2026-07-21, consolidation pass
  — all 6 wiring todos shipped incl. an 8/8-shard-combo smoke test; 2 residual todos folded below),
  `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`,
  `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`.
- **Close-out criterion**: every MVP protocol/data_type captures or is honestly `empty_confirmed`.

- [ ] [BACKEND] P2. **Wire the remaining zero-capture protocols** (uniswap_v2/v4, trader_joe_v2, velodrome_v2 DONE —
      wired + smoke-tested 2026-07-14; Morpho lending indices; Solana ORCA/RAYDIUM swap indexer as a new capability —
      both still open per the two sibling issues above). (repos: market-tick-data-service)

> **2 closed items extracted 2026-07-25** (line-cap remediation, 2nd pass) — the OOM-crash-loop-fixed coverage
> verification + the protocol-dispatch-list codex audit, both done; full text verbatim in
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

## Track 5 — COVERAGE: backfill → MVP-100% — FORKED 2026-07-24

**Forked verbatim to
[`defi_track5_coverage_mvp_backfill_2026_07_24.md`](/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md)**
(the prose-only "C-GREEN gated on T1→T3" dependency is now a real `depends_on` + `gate_on_depends: true` on that child,
per task_template.md finding I — the SAME edit that forked this section). Includes the MVP-universe §14 gap-audit
sub-section and the mvp-defi backlog unpark flipper note, moved there unedited. Track this track's progress in that
file, not here.

## Track 6 — RENDER: data-status surface #4 + RESTORE the enumeration view · P1 — CLOSED, extracted 2026-07-25

> **Both todos in this track are done, extracted verbatim (line-cap remediation) to**
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md):
> (1) `instruments-service@64a58cc1`+`deployment-api@0d2f6e6`+`deployment-ui@4afcfd8` — restored the
> `GET /api/data-status/distinct-values/{asset_group}` enumeration view; (2) `deployment-api@427ede5`+
> `deployment-ui@83ec561` — fixed the turbo-API HYPERLIQUID/ASTER hide bug + pruned the capability-bundle DRIFT residue.
> **Close-out criterion note (kept live here, not archived)**: the doc's own criterion is NOT fully met yet — a fresh
> distinct-values census must return zero `is_canonical=false` entries; that drive-to-0 work is tracked in
> `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, not as its own todo here or in the history child.

## Track 7 — CULL: purge the removed venues everywhere (dead-only, snapshot-first) · P1 — CLOSED, extracted 2026-07-25

> **The 1 todo in this track is done, extracted verbatim (line-cap remediation) to**
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md)
> — `market-tick-data-service@f6176e8b` purged the culled Solana-perp venues' DeFi-side residue (architecture_v2 leg
> specs already dropped, `mvp-scope-canonical.md` already fixed, one genuine residue script deleted); the operator
> ruling (KEEP `KALSHI-PERP`/`POLYMARKET-PERP`/`LIGHTER-ZKSYNC`/`EXTENDED-STARKNET`, cull everything else, GCS deletes
> snapshot-first) and the load-bearing exclusions (`DECOMMISSIONED_VENUE_BASES`, `QUARANTINE_REGISTRY`, the DRIFT
> token-ticker, 2 historical migration-utility mappings) are preserved verbatim in the history child, not repeated here.

## Track 8 — INFRA / forward-data: resume steady-state (⛔ for forward honesty) · P1

- **Sources**: `issues/defi_scheduled_collection_outage_paused_crons_2026_07_16.md` (11 collect + 3 fwd crons paused
  since 2026-06-08), `issues/defi_consolidator_cron_left_paused_2026_07_15.md`,
  `issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`,
  `issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`,
  `issues/defi_code_codex_drift_2026_05_27.md`.
- **Close-out criterion**: forward crons running; consolidator race/pause fixed; codex↔code drift closed.

> **⛔ correction 2026-07-22 (scoping-only sub-agent, read-only `gcloud scheduler jobs list/describe`
> `central-element-323112`/`asia-northeast1`, nothing written/resumed) — the "11 collect + 3 forward, all paused"
> framing below is IMPRECISE.** Actual live state: only **4 of the 11** `uts-prod-mtds-collect-*` daily-batch crons are
> PAUSED (`dex-pools`, `oracle-prices`, `evm-defi`, `solana-defi` — all 4
> `userUpdateTime=2026-07-18T19:15:2[6-9|31|34|36]Z`, one coordinated action matching the "re-armed 2026-07-18"
> per-instrument-refactor banner above, `:114-121`, even though that banner's prose names only 2 of the 4). The other
> **7 are ENABLED and running today** (`perp-funding`, `gas-fees`, `dex-swaps`, `lending-indices`, `lst-rates`,
> `liquidations`, `eigenlayer-rewards`) — safe, because the forward per-instrument writer fix (R1, `mtds@4ca2640d`)
> already shards every one of them by real `instrument_id` (0 new glued objects across 8 consecutive live days — see the
> deferred-work table's "Forward write-path fix" row). All **3** `defi-fwd-*` live-poll crons remain PAUSED. **Net: 7
> schedulers paused, not 14** — a scoped pause on exactly the data types (dex_pools/oracle_prices/evm_defi/solana_defi)
> the still-RUNNING `canonical-migration-defi-per-instrument-*` VM is migrating, not a blanket outage. The manifest
> consolidator (`uts-prod-manifest-consolidator-market-data-defi-cron` + `instruments-defi`/`features-defi`) is ENABLED,
> running every 1 minute, unaffected. Of this todo's own close-out criterion: **consolidator duplicate-race is CLOSED
> (2026-07-10)** and **scheduler SIGKILL is RESOLVED (2026-07-14/15)** — both archived
> (`plans/archive/issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md`,
> `plans/archive/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`); only "right-size the
> honest-coverage nightly" and the codex↔code drift doc remain open (both `status: open` as of this check). Full
> derivation: this plan's Progress Log, 2026-07-22 sub-agent entry.

- [ ] [INFRA] P1. **Resume the paused DeFi crons NOT scoped to `dex_pool_state`** (oracle-prices, evm-defi, solana-defi
      collectors + their forward-poll counterparts — of the 4 collect + 3 forward = 7 schedulers currently paused per
      the correction above, this is every one EXCEPT the dex-pools-scoped collect + forward-poll pair split into the
      next todo) AFTER Track-1/2 land so they write the canonical shape; fix the consolidator duplicate-race + SIGKILL
      (**both already CLOSED, see correction above** — only the honest-coverage nightly right-size + codex-drift-doc
      sub-clauses remain). **Because live=batch, no live-only DeFi data_type needs separate reconciliation** — the
      forward writer is already canonical (Half-A done); the open work is Half-B (migrate the historical corpus) then
      resume forward. Do not resume before the currently-running per-instrument migration VM finishes (it is actively
      migrating exactly the 4 paused collectors' data types — resuming now races live writes against it).
      `uts-prod-mtds-collect-solana-defi-cron` needed the Solana AMM symbol-collision fix before resuming — **the fix
      has since SHIPPED** (`market-tick-data-service@0d83a8a9`, ancestor of `origin/live-defi-rollout`; see the
      Solana-symbol-collision item above), so this specific pre-resume condition is now satisfied; the cron still waits
      on the Track-1/2 + migration-VM gates above like the rest. (repos: deployment-service, market-tick-data-service)
- [ ] [INFRA] P1. **Resume the `dex_pool_state` collect + forward-poll schedulers ONLY AFTER
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` lands** (operator ruling 2026-07-25, task_template.md
      finding P) — these serve TRADER_JOE_V2/VELODROME_V2/CURVE, the exact venues that plan's
      subgraph-query-missing-`inputTokens{symbol}` fix targets; resuming before it ships would resume writing the same
      symbol-less rows that plan exists to stop. Same Track-1/2 + migration-VM gates as the item above ALSO apply here —
      this is an additional gate, not a replacement. A 2026-07-23 GCS sample (every 3 days, both venues) had found ZERO
      `dex_pool_state` objects for ORCA/RAYDIUM, confirming the (separate, already-fixed) Solana symbol-collision bug
      hadn't yet corrupted data before ITS fix landed. (repos: deployment-service, market-tick-data-service)

## Open follow-ups (carried forward from the pre-2026-07-24 Progress Log's "Deferred work after 2026-07-22/23" tables)

> Full narrative + evidence for every row below lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md)
> ("Deferred work after 2026-07-22" / "…-07-23" sections) — condensed to actionable todos here so nothing genuinely open
> got silently archived. Items already marked DONE/SHIPPED/RESOLVED in that history are NOT repeated here.

> **6 more closed items extracted 2026-07-25** (line-cap remediation, 2nd pass): the stale-duplicate Solana-writer note,
> the `is_defi_force_include_pool` wiring, orphan-sweep VM monitoring, the fake-history relabel + TRUE-final-scope pair,
> the cefi/prediction timestamp-provenance audit, and the `dex_pools_handler.py` parallel-writer resolution — all done;
> full text verbatim in
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).
> The FLAGGED-marker remediation decision record and the Solana AMM symbol-collision fix stayed here (also done) because
> open todos below point at them directly.

- [ ] [SCRIPT] P3. **Root-cause `quickmerge.sh` silently resetting an unpushed commit** (observed 2026-07-22, 2
      hypotheses ruled out, cause not confirmed, non-reproducible on retry). Needs a `bash -x`/`set -x` trace the next
      time it recurs. (repo: unified-trading-pm)
- [ ] [BACKEND] P2. **Audit defi adapters for dead code, runtime-fallback masking, and duplicate implementations**
      (gate-audit §1, 2026-07-24) across instruments-service `.../adapters/defi/`, MTDS
      `market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/`, and execution-service
      `adapters/defi_adapter.py`, per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Definition of
      done: a written finding per module (kept/fixed/removed + reason). (repos: instruments-service,
      market-tick-data-service, execution-service)

> **VM status** (full narrative archived 2026-07-25, 2nd extraction pass — see
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md)):
> check
> `gcloud compute instances describe canonical-migration-defi-marker-cleanup-20260724-182226 --zone=asia-northeast1-c` —
> SPOT + shutdown-on-completion, so TERMINATED/absent likely means done; the resume-logs at
> `gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/resume-seed/` are the proof
> either way, they don't need the VM alive to read.

- [ ] [OPERATOR] P1. **Run `delete_migrated_defi_markers_2026_07_23.py --apply`** — CODE-SHIP HALF DONE
      (`market-tick-data-service@a65117eb`, confirmed on `origin/live-defi-rollout` — the blocking flaky-test issue was
      worked around via the serial-pytest mitigation, not fixed at root; see
      `issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`, reopened 2026-07-24). Exact
      operator command:
      `cd market-tick-data-service && .venv/bin/python     scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py --apply`.
      **Gated on the "21 glued-id rows" todo below** — re-verify 0 glued ids before running; the fix that stops NEW
      glued rows shipped (`f2e3ad41`) but the 12 pre-existing liquidations rows found 2026-07-23 have not yet been
      re-verified clean. Prod-bucket delete, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
      — an agent must never run `--apply` itself.
- [x] 1. ✅ [DATA] P1. **Remediate FLAGGED `_migrated_*` markers — ROOT-CAUSED + DECIDED 2026-07-25.** Full analysis in
      `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` (live parquet inspection, not guessed).
      Operator decided all three clusters same day; execution now tracked in two dedicated plans (not here, to keep this
      plan from re-growing): - **GMX perp_funding** (~1,896 markers) — confirmed via direct parquet inspection across
      the FULL 2022-2023 range that every single row is a synthetic OI-imbalance proxy
      (`funding_rate_long == -funding_rate_short` exactly, `market="all"`), not real captured funding data — the native
      subgraph query never worked for this venue's whole history. Combined with GMX's narrow/unverified usage in
      strategy-service (`staked_basis.py`'s own "GMX-V2 rows pending verification" comment), **operator decided: remove
      GMX entirely** — `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`'s all 8 todos SHIPPED
      (2026-07-25/26): `unified-api-contracts@18d53d63`, `market-tick-data-service@68407ae5`,
      `instruments-service@0214bb3c` (+`2de3418e` residual cleanup), `execution-service@09a828ed`,
      `strategy-service@ca818ff8`, `unified-trading-library@f22e516f`, the `[OPERATOR]`-run prod-bucket GCS+manifest
      purge (5,374 `venue=GMX` manifest rows dropped, zero objects remain), and the docs update
      (`unified-trading-pm@bfda5df5b`). - **TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state** (~944+ markers) —
      root-caused to a real, ACTIVE code bug: `dex_pools_handler.py`'s `messari_basic` subgraph query never requests
      `inputTokens { symbol }` (verified byte-for-byte against the working sibling query), starving symbol resolution
      for these venues even in CURRENT/live captures (see
      `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`). **Operator decided: delete the bad
      data, fix the query, re-backfill** — `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (5 todos, sequential:
      fix → live-test recoverability → backfill → purge superseded data). - **lst_rates** (COINBASE/MAKER/SWELL/ETHENA)
      — root-caused: legitimate single-row/day snapshots, re-derivable on demand from the current canonical RPC-based
      `lst_rates_handler.py` (queries a historical block number directly, so nothing is actually lost by deleting the
      old copy); MAKER/ETHENA additionally obsolete (sDAI/sUSDe already reclassified out of `lst_rates` by a 2026-07-23
      fix). **Operator decided: purge as orphaned artifacts** — folded into
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s first todo. Evidence: `unified-trading-pm@83c31fc87`
      (refined root-cause), `@184387872` (GMX removal plan), `@781b98eea` (fix+backfill+purge plan). The underlying
      dry-run (banner above) continues independently — once it completes, re-run it to confirm these clusters clear per
      the two plans' own done-when criteria, before any `--apply`.
- [ ] [DATA] P2. **21 glued-id rows found in the 2026-07-23 manifest rebuild — writer fix SHIPPED, re-verify pending.**
      9 ORCA/SOLANA `dex_pool_state` cells (2025-12-23..12-31) still need the higher-timeout/parallel-write migration
      retry (tracked in `issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md`'s addendum — root-caused
      as a genuine large fan-out, not a bug; safe to retry, source bundles left intact). The 12 `liquidations` bundles
      question is ANSWERED: root-caused + fixed 2026-07-24 (`market-tick-data-service@f2e3ad41` — a daily cron was
      writing timestamp-glued empty markers across 6 handlers; `70b9a81a` promoted the verify tool to
      `scripts/one_offs/verify_defi_glued_ids_2026_07_24.py`). **Remaining**: run the 9-cell ORCA retry + re-run the
      verify script for a fresh 0-glued-ids reading before the marker-delete `--apply` todo above proceeds.
- [ ] [DATA] P1. **~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN migration** — gated on lending-writer-retire todos 7/8/10/11
      (per-data_type target mapping + atomic 3-repo wave + runtime proof), see
      `defi_lending_writer_retire_prerequisite_2026_07_20.md`.
- [ ] [DATA] P1. **Residual canon walk C2-C12 — corrected 2026-07-25, the bundled title was stale-drift.** 6 items still
      SCOPED not executed (C2/C3/C4/C9/C11/C12), code-side verified GREEN for C2/C3/C9/C12; ALL SIX need a data-side
      read of the live `_index` once the 2 canonical-migration VMs reach a terminal state, then
      `audit_canonical_form.py --probe-paths` against the single consolidated bucket. Same open item, tracked verbatim
      at `defi_track01_per_instrument_and_canon_id_2026_07_24.md:310` — avoid duplicating the work across both docs.
      **Two stale-drift corrections**: (1) the old title's "+ instrument_type case/venue-spelling unify" bundling is now
      WRONG — that half is a SEPARATE item that RESOLVED 2026-07-24 as its own todo
      (`defi_track01_per_instrument_and_canon_id_2026_07_24.md:316`, live census found zero case or spelling drift
      anywhere in the manifest, a clean no-op — not part of the still-open C2-C12 walk). (2) "Also surfaced but not
      filed: `staking_yields_handler.py`'s `collect-staking-yields` CLI op has zero Cloud Scheduler jobs (dead code?);
      `lst_rates_handler.py` writes to a non-canonical, non-hive path" is also stale — it HAS since been filed as its
      own open todo (`defi_track01_per_instrument_and_canon_id_2026_07_24.md:744`, `[DATA] P2`), not left un-filed.
- [ ] [BACKEND] P2. **Async fan-out + executor-offload for the DeFi write path — duplicate of the Track 5 item above**
      (same 4 upload sites, same design sketch, same 2026-07-24 correction re: the knobs NOT being a safe standalone
      step — see that item for full evidence). (repo: market-tick-data-service)
- [ ] [OPERATOR] P2. **2-VM TheGraph canary** — code-only so far per the original session's instructions; launching the
      canary VMs is operator-owned (Q3 ruling: "ship code + I run the canary").
- [ ] [DATA] P1. **Resume paused DeFi crons NOT scoped to `dex_pool_state`** + fix the honest-coverage-nightly
      right-size + codex-drift doc — gated on Track 1 (LENDING migration + canon walk above) + Track 2 (path-shape-pin
      code half) + the currently-running per-instrument migration VM finishing first (resuming now would race live
      writes against the exact data types it's mid-migrating). **Duplicate of the Track 8 resume-crons item above** —
      same split, same gates; the `dex_pool_state` (TRADER_JOE_V2/VELODROME_V2/CURVE) half stays gated on
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` too (operator ruling 2026-07-25, task_template.md finding
      P).
- [ ] [DATA] P1. **DeFi MVP backfill to 100%** — C-GREEN gated on Track 1 (LENDING migration + canon walk, above) +
      Track 2 (path-shape-pin) + Track 3 (`catalogue_pool_ids_for_shard` generalization, execution work not a decision).
      Backlog task `mvp_backfill_defi_onchain_v10-001` stays parked (`priority: 999`) until
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` flips true.
- [x] ✅ [BACKEND] P2. **Solana AMM symbol-collision code fix — SHIPPED 2026-07-24 (checkbox was stale — this todo's
      text describing the fix as "unwritten" was overtaken by events, never flipped).**
      `market-tick-data-service@0d83a8a9` wires the fee/tick-spacing discriminator into `solana_defi_handler.py`,
      confirmed ancestor of `origin/live-defi-rollout`. Full remaining scope (already-shipped fix,
      migration-of-existing-data check DONE clean, manifest-impact doc note, naming-doc update, and the SEPARATE cruder
      `dex_pools_handler.py` writer's own collision exposure) tracked in
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (§ "Per-instrument re-architecture", the Solana
      pool-symbol todo) — not duplicated here.

## Contradiction resolution (pre-SSOT) — archived, 95% closed

> The 2026-07-18 canonical-target audit's 75-finding contradiction-resolution log (1 blocking · 35 high · 31 medium · 8
> low; 53 doc · 17 code · 5 plan) lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md).
> **95% closed** (7 of 9 tracked todos shipped); the 2 still-open findings were relocated live into Track 1 above (the
> "Cross-AG — PREDICTION canonicalisation" subsection + the UTL `_derive_instrument_id.py` dispatch-key decision note)
> rather than left stranded in the archive.

## Codex SSOTs (read before touching a track)

`/codex/02-data/defi-canonical-naming-ssot.md`, `/codex/02-data/defi-data-pipeline.md`,
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/honest-coverage-model.md`,
`/codex/02-data/honest-absence-downstream-handling.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/02-data/defi-completeness-oracle.md`, `/codex/05-infrastructure/manifest-consolidator-ssot.md`,
`/codex/05-infrastructure/vm-launcher-runbook.md`, `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`.

## Progress Log — condensed (2026-07-24, replaces the pre-split ~2145-line tick-by-tick log)

- **2026-07-24 (session 3, `/autonomous`, orchestration pass)** — triaged ~50 open todos across 3 docs, flipped 4
  stale-done checkboxes, fanned out 9 parallel background agents; found the 15.87M-row defi orphan-sweep completed
  (largest of any AG, likely-test-artifact-leak caveat); session interrupted mid-flight by an infra migration. Full
  session narrative extracted 2026-07-25 (2nd pass) to
  [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

> **The full tick-by-tick history was NOT deleted.** The 2026-07-18→2026-07-23 detail (contradiction-resolution audit
>
> - the complete Progress Log + the "Deferred work after 2026-07-22/23" tables) lives verbatim in
>   [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md).
>   The 2026-07-24 session-3 → 2026-07-25 8h-mark-checkpoint detail (both full session write-ups condensed in this log,
>   the deferred-work table, lessons, and the interim cluster-breakdown report) lives verbatim in
>   [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md)
>   (2nd extraction pass, 2026-07-25). Every genuinely-open item from every deferred-work table now has a canonical todo
>   under "Open follow-ups" above or the relevant Track — nothing was silently archived.

- **2026-07-18** — Plan authored from a 6-agent audit + live GCS/manifest reads; operator-decided canonical target set
  (id grammar, SPOT_ASSET/SPOT_PAIR/POOL, two-id model); Tracks 1-8 scoped.
- **2026-07-18/19** — Per-instrument re-architecture superseded the batch-model tracks (DeFi capture stopped, migrated
  to per-instrument writers); the 75-finding contradiction-resolution audit run + mostly closed (see the archived
  section above).
- **2026-07-20/21** — Non-POOL EU terminal-state decision + oracle dead-venue handling shipped; `available_at` broader
  ~20-handler fix shipped; path-shape-pin (code portion) + second dexpool writer kill shipped both halves (MTDS + UAC).
- **2026-07-22** — SPOT preemption contract shipped for DeFi backfill launchers; residual canon walk C2-C12 scoped (not
  executed, gated on 2 running migration VMs); checker collect-* fleet-wide real-VM-launch verification DONE.
- **2026-07-23** — Glued-id manifest rebuild verify + `_migrated_` marker delete tooling shipped (dry-run default, human
  `--apply`-gated); 6th orphan-sweep VM launched; dex_pools fake-history recurrence found + disposition ruled
  (relabel-forward, script not yet written); a live Solana AMM symbol-collision bug verified clean (paused, gated); a
  documentation gap closed (22 open defi plans/issues + this plan's own related-doc list made mutually discoverable —
  the seed of this 2026-07-24 line-cap remediation).
- **2026-07-24** — Plan line-cap remediation: `defi_strategy_pnl_axis_index_2026_07_24.md` extracted (Strategy/PnL
  axis), full history + 75-finding audit extracted to `defi_consolidated_closeout_history_2026_07_18.md` (archived),
  Progress Log condensed to this summary, every still-open "Deferred work" item converted to a canonical todo above, and
  the Aggregated source docs index (below) enriched to cover every active defi + defi-touching plan/issue.
- **2026-07-24** — cefi/prediction `available_at` timestamp-provenance audit (line-761 todo) executed. Checked whether
  prediction/cefi's write paths share DeFi's resolved "stamp a deterministic timestamp then discard it for wall-clock"
  bug class. Prediction (kalshi_adapter.py/polymarket_adapter.py) and cefi's primary path (ccxt_adapter.py) are already
  correct. Found 2 real gaps + 1 weaker candidate in smaller cefi batch handlers (`deribit_volatility_index_handler.py`,
  `book_microstructure_handler.py`, `deribit_options_chain_handler.py`). Filed
  `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`, cross-referenced into
  `cefi_consolidated_closeout_2026_07_18.md` Track 6 as the owning plan for the code fix (out of scope for this
  defi-plan audit todo). No production code touched this session.
- **2026-07-25 (`/autonomous`, operator stepped away for ~8h)** — ran the `delete_migrated_defi_markers_2026_07_23.py`
  dry-run on 2 parallel VM shards (~6 markers/sec combined); root-caused the FLAGGED-marker clusters via direct parquet
  inspection (not guessed) — GMX (removed entirely), TRADER_JOE_V2/VELODROME_V2/CURVE (real subgraph query bug),
  lst_rates (orphaned) — see the FLAGGED-marker remediation item above for the operator-decided disposition of each.
  `--apply` stays human-only, queued regardless of report cleanliness. Full session narrative + the 8h-mark interim
  report extracted 2026-07-25 (2nd pass) to
  [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

> Moved verbatim to `/plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md` (2026-07-24 line-cap
> trim, 2nd pass — the umbrella:true exemption was removed same-day). Read that doc for the full discoverability index
> of every other defi-relevant plan/issue with its open-todo digest.

**Missing digest entry (gate-audit §12, 2026-07-24)**: `defi_track01_per_instrument_and_canon_id_2026_07_24.md` is
referenced 3x by "tracked under X below" prose in `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` but
never appears there as a linked entry — recorded here pending the fix below.

- **[`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)**
  — 13 open (5 P0, 3 P1, 5 P2 — 11 plain-open + 2 `[~]` partial; re-verified LIVE 2026-07-25, corrects the stale "18
  open" count above); top P0s: R3-run full-corpus migration VM still applying, catalogue-venue-gap re-enum/re-rollup
  deploy-gated, ~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN Wave-D migration, residual canon walk C2-C12, address/UUID
  fallback elimination in `canonical_instrument_id`.
- [ ] [DOC] P1. **Add the digest entry above into `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`** and
      fix its 3 dangling "tracked under X below" references to point at it (bold digest style, task_template.md finding
      H). (repo: unified-trading-pm)
