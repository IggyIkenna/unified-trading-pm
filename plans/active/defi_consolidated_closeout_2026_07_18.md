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
umbrella: true
asset_group: [defi]
stage: [meta]
repos:
  [
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
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md,
    /plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    /plans/archive/2026_07/mtds_defi_dex_zero_capture_protocols_2026_07_14.md,
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
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
    issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md,
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
  ]
created: 2026-07-18
last_updated: 2026-07-23
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
depends_on:
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
> `/plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 11: "Extract Strategy/PnL index + 1800-line
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
>
> **Open-todo counts per child (2026-07-24, so a fresh session doesn't have to open each one to see what's live)**:
>
> - `defi_strategy_pnl_axis_index_2026_07_24.md` — **0 own top-level todos** (it's an entry-point index that references
>   other plans rather than carrying its own checkboxes; most of what it points to is already indexed in this doc's
>   "Aggregated source docs" § Strategy/PnL/backtest axis below).
> - `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — **18 open** (6 P0, 7 P1, 5 P2). Top P0s: (1) legacy
>   `dex_pools/`/`lending_indices/` = PARTIAL-OVERLAP, fold-not-delete — 32 legacy-only high-TVL Raydium pools are
>   absent from canon and must be union-merged in before any delete; (2) a legacy GLUED-VENUE flat tree still lives
>   inside `raw_tick_data/` that R3 (per-instrument discovery) never sees — first determine if it's superseded
>   `_migrated_` leftovers or an un-split source.
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

| type                                    | grammar                                                                                                        | example                                                                         |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `SPOT_ASSET`                            | `VENUE-CHAIN:SPOT_ASSET:SYM`                                                                                   | `UNISWAP_V3-ETHEREUM:SPOT_ASSET:WETH`                                           |
| `POOL`                                  | `VENUE-CHAIN:POOL:TOKEN0-TOKEN1[-FEE_BPS]` — **3-segment, fee INSIDE the symbol (operator ruling 2026-07-18)** | `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`                                        |
| `A_TOKEN` / `DEBT_TOKEN`                | supply / borrow leg (isolated markets append `marketId[:8]`)                                                   | `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC` · `MORPHO-BASE:A_TOKEN:AUSDC-EURC-<marketId8>` |
| `LST` / `YIELD_BEARING` / `STAKING`     | staking token / vault share                                                                                    | `LIDO-ETHEREUM:LST:stETH` · `ETHENA-ETHEREUM:YIELD_BEARING:sUSDe`               |
| `PERPETUAL` (on-chain, DeFi lane = GMX) | `VENUE:PERPETUAL:SYM` — **NO chain suffix** (routes cefi-simple branch)                                        | `GMX:PERPETUAL:BTC-USD`                                                         |
| `SOLANA_AMM_POOL` / `SOLANA_LENDING`    | Solana grains                                                                                                  | `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC`                                          |

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
  `issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`,
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
> `issues/defi_dex_pools_delete_order_stale_2026_07_20.md`.

- [x] ✅ [DATA] P0. **Pin the flat canonical path shape (code portion) + kill the second dexpool writer path.** ~~DELETE
      the dead top-level Solana `dex_pools/`+`lending_indices/` prefixes (frozen 2026-04-14, "Shape-B")~~ **← DELETE
      CLAUSE SUPERSEDED — see the ⛔ correction banner directly above.**

      **2026-07-22 findings + fix.** The historical bare-`0x<address>.parquet` batch writer suspected by
                                                                                                                                                                                      `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md` was already fixed 2026-07-09
                                                                                                                                                                                      (`mtds@0713c01a`/`0ce28623`) — confirmed dead via a narrow live-GCS read (`day=2026-07-18` CURVE
                                                                                                                                                                                      `dex_pool_state` objects are real `TOKEN0-TOKEN1.parquet` symbol names, not addresses). The ACTUAL live
                                                                                                                                                                                      second writer: `market_tick_data_service.live.websocket_runner.live_tick_blob_path` (`mtds@3043f2dc1`,
                                                                                                                                                                                      2026-06-26) spliced `chain=` BEFORE `venue=` for every non-cefi asset_group — the reverse of the canonical
                                                                                                                                                                                      batch order (`unified_api_contracts.build_defi_partition_path`: `venue={V}/chain={C}/...`) — for the SAME
                                                                                                                                                                                      (asset_group=defi, venue, chain, data_type, day) shard. Undetected for ~1 month because
                                                                                                                                                                                      `canonical_path_violations` parsed partition segments into a `key→value` dict and never validated ORDER
                                                                                                                                                                                      (only presence/values) — proven empirically (a hand-built reversed-order path returned the identical
                                                                                                                                                                                      violation list as the correct order).

                                                                                                                                                                                      **Shipped**: `market-tick-data-service@0fcfa803` — reordered `live_tick_blob_path` to venue-before-chain +
                                                                                                                                                                                      pinned the `_PER_AG_SHARD_COUNTS["DEFI"]` regression test (2673→2592, drifted by the unrelated concurrent
                                                                                                                                                                                      METEORA/LIFINITY/PHOENIX phase-downgrade commit `uac@9a047a31`) + a new live/batch path-order regression
                                                                                                                                                                                      test. Full `quality-gates.sh` green (6814 passed), pushed to `live-defi-rollout`.

                                                                                                                                                                                      **UAC half SHIPPED `unified-api-contracts@1cd27478` (2026-07-23)**: the paired defi-scoped structural check
                                                                                                                                                                                      added to `unified_api_contracts.canonical_path_violations` (venue-before-chain, lowercase
                                                                                                                                                                                      `instrument_type`, `pipeline_mode=` position) so this drift class fails loud going forward — proven safe
                                                                                                                                                                                      against the real writer (its template is unconditional/fixed; verified zero violations across every
                                                                                                                                                                                      pipeline_mode × instrument_type × data_type combination + the fixed live path) and covered by 4 new
                                                                                                                                                                                      regression tests (126 total passing). The blocking pre-existing defect
                                                                                                                                                                                      (`tests/internal/unit/test_archetype_capability_manifest_parity.py`, 3 false failures) was ALREADY
                                                                                                                                                                                      resolved by unrelated concurrent work by the time this shipped — `uac@68c4c371` fixed the parity test's
                                                                                                                                                                                      root-cause path resolution (it resolved via ancestor walk before `UNIFIED_TRADING_WORKSPACE_ROOT`,
                                                                                                                                                                                      which had been reading a stale outer-root PM checkout — the codex markdown sections were never
                                                                                                                                                                                      actually missing, the test was just looking in the wrong place); no codex-doc content edit was needed.
                                                                                                                                                                                      Verified: `bash scripts/quality-gates.sh --no-fix` full green (`.qg_last_passed_sha` == HEAD
                                                                                                                                                                                      `824b1b7d` pre-ship), all 17 archetype-parity tests + all 89 `test_partition_path_is_canonical.py`
                                                                                                                                                                                      tests passing, shipped via `quickmerge.sh --agent --files 'unified_api_contracts/canonical/partition_paths.py
                                                                                                                                                                                      tests/unit/test_partition_path_is_canonical.py'`. (repos: market-tick-data-service, unified-api-contracts)

- [x] ✅ [INFRA] P1. **Correct the STALE codex path docs — checklist item was itself stale; both docs were ALREADY fixed
      (verified 2026-07-21).** Re-read both target docs in full + re-derived from this plan's own "Path template
      (operator-locked...)" section + a fresh live GCS listing
      (`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-04-14/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=AAVE_V3/chain=ARBITRUM/`
      — venue segment confirmed BEFORE chain). **Finding: both docs already state venue-before-chain + carry
      `pipeline_mode=` left of `asset_group=`, and neither contains any "Shape-B" text** — grepped
      `market-tick-data-service/docs/` for `Shape-B` (0 hits). The underlying fix landed same-day this bullet was
      authored (`58a6a54edb` @ 2026-07-18 14:14), just ~2.5h before the checklist text could reflect it:
      **`unified-trading-pm@709274a5c`** (2026-07-18 16:50, "…venue-before-chain…", corrected the DEFI row in
      `per-asset-group-bucket-layouts.md` to `venue={v}/chain={chain}` + added `pipeline_mode={mode}_{source}` left of
      `asset_group=`) and **`market-tick-data-service@5f498858`+`@e9764b38`** (2026-07-18 16:46 / 2026-07-19 05:02, same
      "venue-before-chain path" DEFI-align pass to `docs/GCS_PATHS.md`, which already showed
      `venue={PROTOCOL}/chain={CHAIN}` with an explicit "(venue BEFORE chain)" comment and never referenced Shape-B).
      **No further doc edit required** — this bullet was simply never flipped after the fix shipped; flipping it now
      closes the gap. (repos: unified-trading-pm, market-tick-data-service)
- [ ] [INFRA] P1. **Delete the lending-indices legacy bucket (C0f)** + resolve TF estate drift
      (`market_data_defi_lending_indices_prd` still declared) + the bare `features-onchain` vs asset-group bucket. All
      GCS/bucket DELETEs are snapshot-first. (repos: deployment-service, market-tick-data-service)

## Track 3 — DENOM: empty_confirmed / denominator honesty · P1

- **Sources**: `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (measured 63.9M via the v2 enumerator),
  `issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md`, `defi-completeness-oracle.md`,
  `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`,
  `issues/defi_catalogue_available_to_false_delisting_2026_07_20.md`.
- **Close-out criterion**: fresh single-walk yields zero silent-`M` rows; denominator honest.

- [ ] [DATA] P0. **PURGE first, then seed.** Purge the 1.79M duplicate + ~219.5K phantom rows (re-verify the 219,529
      detected vs 219,632 flipped delta), THEN apply the ~63.9M `expected_unattempted` seed (operator write-volume
      gate). The "1M" framing is the old safety-cap slug — the real target is 63.9M. (repos: market-tick-data-service)
- [ ] [BACKEND] P1. **Add the `EXPECTED_SUBGRAPH_DEINDEXED` reason** to reclassify the 952 false Curve/Optimism
      `attempted_failed` → honest-empty; reconcile `spot_asset` absence from the enumerated catalogue (the v2 corpus
      predates SPOT_ASSET population; `spot_pair` 143K is partly the culled DRIFT SPOT leak). (repos:
      unified-api-contracts, instruments-service)
- [x] ✅ [DATA] P1. **DeFi catalogue `available_to` false-delisting — DONE (2026-07-20).** Root fix SHIPPED + VERIFIED
      `instruments-service@13c4f68a` (Option A: defi drop-outs never last-seen-delist, gated `asset_group=="defi"`, both
      full + incremental paths; truth-gate `delisted_at`/`expiry` preserved for a future probe) — PROVEN on real prod
      data: 947 clustered false-delistings (06-26/07-06/07-08 across TRADER_JOE_V2/PANCAKESWAP_V3/AAVE_V3/MORPHO) → 0.
      **(a) prod catalogue CORRECTED + VERIFIED**: `--mode full` regen (monotonic guard ACCEPT, `CATALOGUE_PROMOTED`) +
      a targeted frozen-tail purge (`purge_defi_false_available_to_2026_07_20.py`) — non-blank `available_to` 2,349 →
      **105**, **0** on the 3 false-cluster dates. **(b) historical manifest un-delist DONE + VERIFIED**
      (`undelist_defi_false_postdelist_eu_2026_07_20.py`, instrument_type-agnostic, the inverse of
      `reclassify_defi_postdelist_eu_2026_06_24.py`) — `EXPECTED_INSTRUMENT_DELISTED` **219,738 → 3,874** across 45.8M
      manifest rows. **(c) Option B (on-chain removal probe) SHIPPED** `instruments-service@13c4f68a` +
      `deployment-service@9a36478` (daily Cloud Run job, `defi-removal-probe`, 00:30 UTC) — conservative by
      construction, runtime-verified against prod (0/30 live targets confirmed gone — correct for a healthy universe).
      CI green both repos. SSOT + full evidence: `issues/defi_catalogue_available_to_false_delisting_2026_07_20.md`.
      **Residual, tracked separately**: the 215,864 un-delisted cells are honest-pending, not yet terminal — see the
      next item. (repos: instruments-service, deployment-service)
- [x] ✅ [DECISION] P1. **DeFi non-POOL per-instrument EU has NO reconciliation path — DECISION resolved + shipped
      (2026-07-21), generalization work still open.** (surfaced by the un-delist above). The catalogue-residual →
      typed-empty machinery is DEX-POOL-ONLY at all three layers, and SPOT_ASSET/A_TOKEN/DEBT_TOKEN are reference-only
      holdings with no per-day capture path. **Resolved: Option B — a NEW in-denominator terminal reason** (never
      `EXPECTED_NOT_ENOUGH_TVL`, which would reproduce the `EXPECTED_INSTRUMENT_DELISTED` clipped-from-denominator
      exclusion), decided via `AskUserQuestion` 2026-07-20/21. **Shipped**: `unified-api-contracts@d4d85854`
      (`EmptyConfirmedReason.EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH`, deliberately NOT in
      `OUT_OF_COVERAGE_WINDOW_REASONS`), `instruments-service@a516bd01` (prospective enumerator seeding,
      `_enumerate_v2_defi`), `instruments-service@2967cf5f` (retroactive reconciliation script),
      `deployment-api@8691f29`/`@ea56fff` + `deployment-ui@183cfc3` (dashboard parity). **Measured 2026-07-21**: the
      215,864-cell instrument-level estimate did NOT hold at cell grain by measurement time (3 independent pyarrow
      queries against the live `_index`, 52.3M rows: zero EU cells carry a reference-only `instrument_type`; 166,641
      reference-only rows exist but are 100% already `captured`) — the retroactive script is a correct no-op today and
      stays as a self-cleaning safety net. Full evidence:
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`. **Still open** (real capability
      work, not a decision gap): generalise `catalogue_pool_ids_for_shard` beyond `instrument_type=='pool'` + add a
      per-instrument residual emitter to the capturable non-POOL handlers (lending_indices/risk_params/lst_rates/
      evm_defi) — tracked as that issue doc's own `[ ]` follow-on items. (repos: market-tick-data-service,
      instruments-service, unified-api-contracts)

## Track 4 — CAP: zero-capture protocols · P2

- **Sources**: `mtds_defi_dex_zero_capture_protocols_2026_07_14.md` (folded in + archived 2026-07-21, consolidation pass
  — all 6 wiring todos shipped incl. an 8/8-shard-combo smoke test; 2 residual todos folded below),
  `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`,
  `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`.
- **Close-out criterion**: every MVP protocol/data_type captures or is honestly `empty_confirmed`.

- [ ] [BACKEND] P2. **Wire the remaining zero-capture protocols** (uniswap_v2/v4, trader_joe_v2, velodrome_v2 DONE —
      wired + smoke-tested 2026-07-14; Morpho lending indices; Solana ORCA/RAYDIUM swap indexer as a new capability —
      both still open per the two sibling issues above). (repos: market-tick-data-service)
- [ ] [DATA] P2. **Verify the mtds-dex-pools/dex-swaps backfill VMs (uniswap_v2/v4, trader_joe_v2, velodrome_v2,
      launched 2026-07-14 for 2023-01-01→today) actually produced real historical rows** — spot-check row counts +
      manifest `capture_status=captured` for a sample of dates for each of the 4 protocols, both `dex_pool_state` and
      `dex_pool_swaps`. **Known risk**: these exact VM names (`mtds-dex-pools-backfill`, `mtds-dex-swaps-backfill`) hit
      the `issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` OOM SIGKILL crash-loop the SAME day they were
      launched; the eventual fix (`unified-trading-library@a5b07ff7e` + follow-ons) was only production-verified on
      short smoke windows (a 3-day uniswap_v2 dex_pools run, a 108-day Morpho lending_indices run) — NOT on this
      specific full-range, 4-protocol launch. A relaunch may be required if the original run predates the fix landing.
      (repos: market-tick-data-service, deployment-service)
- [ ] [BACKEND] P3. **Post-phase codex audit for the dex_pools/dex_swaps protocol dispatch list** — check whether
      `/codex/02-data/defi-canonical-naming-ssot.md` documents the MTDS `_DEFAULT_PROTOCOLS`/fallbacks dispatch set; it
      currently does not (only data_type/venue/bucket path-naming rules) — add it if the audit confirms no stale list
      exists elsewhere. (repos: unified-trading-pm)

## Track 5 — COVERAGE: backfill → MVP-100% (largest open track) · P1 (C-GREEN gated on T1→T3)

- **Sources**: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (G2 final verify),
  `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` (Phase-D carry tracer — prior ✅ was gate-only, data was
  10/10 SKIP → RE-RUN), `defi_onchain_derivable_values_and_date_drift_2026_06_20.md` (2 P1).
- **Close-out criterion**: manifest-counted canonical rows for every MVP cell; carry tracer green on real data.

> **mvp-defi backlog unpark condition — re-pointed here 2026-07-20 (`ao_dispatch_cooldown_and_park_2026_07_20` todo
> 4).** The agent-orchestrator backlog task `mvp_backfill_defi_onchain_v10-001` carries a durable park (`priority: 999`
> / `priority_override: true`) gated on the named prerequisite
> `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (condition currently `false`).
>
> Its original owner, `data_completion_defi_2026_07_15.md` (todos B0/C0, seed-then-backfill framing), is dead under the
> per-instrument re-architecture above — that plan never re-derives the condition and its seed-chain premise no longer
> matches how backfill actually runs (shard key = symbolic `canonical_instrument_id`, not the old seed-chain).
>
> **Flip instruction**: set `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` **true**
> (`POST /api/prerequisites/defi_onchain_v10_universe_v2_seed_or_backfill_progressed {"value": true, "set_by": "<you>"}`)
> the first time the todo below shows REAL manifest-counted progress on the per-instrument shard key — i.e. once R1→R3
> above have landed (writer + denominator + historical migration) and this track's backfill has actually started writing
> canonical rows, not merely been unblocked to start.
>
> Until then the park is intentional, not stale: Track 5 is explicitly gated C-GREEN on T1→T3, and R3 (the historical
> migration this backfill depends on) is still `RUNNING, partial` as of this writing. No park exists without a named
> LIVE flipper — this note + this track ARE that flipper; if Track 5 is ever archived/superseded before flipping the
> condition, migrate this note to whatever supersedes it rather than letting the park go silent again.

- [ ] [DATA] P1. **Run the DeFi MVP backfill to 100%** on the canonical/migrated corpus (SPOT VMs; the DRIFT/Velocity
      historical grind is now CULL residue — DRIFT is out of target, so its gap is dropped not filled); re-run the
      Phase-D historical carry tracer on real data; resolve the 2 derivable-values P1s. On first real progress, flip
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` true per the unpark note above — that is what releases
      the parked `mvp_backfill_defi_onchain_v10-001` backlog task back to the fleet. (repos: deployment-service,
      market-tick-data-service, features-service)
- [ ] [BACKEND] P2. **Async fan-out + executor-offload for the MTDS DeFi collectors** (recovered from the pre-2026-07-24
      historical Progress Log's deferred-work table — genuinely correctness-sensitive, deliberately not squeezed into a
      sub-agent turn). The sequential loops needing fan-out are `solana_defi_handler.py::_run_solana_protocol_loop` +
      `dex_pools_handler.py::_run_process`, with the actual blocking `_upload_parquet`/`storage.upload_bytes` calls two
      files deeper in `_dex_pools_subgraph.py::_collect_protocol_chain`/`::_collect_solana_dex`. Design sketch: fan out
      fetch+upload via UTL `ParallelPerSymbolRunner` with `manifest_writer=None`, then apply
      `record_captured`/`record_zero_rows`/`record_failed` + the heartbeat SEQUENTIALLY over the gathered results in
      original iteration order (preserves today's manifest-write/heartbeat semantics exactly while parallelizing the
      slow I/O). The 3 `service_config.py` knobs (`defi_max_concurrent_fetches`/`defi_max_inflight_tasks`/
      `defi_max_concurrent_uploads`, mirroring the Tardis 3-knob block) are a trivial, un-risky first step.
      **Separately**: the 2-VM TheGraph canary is operator-owned ("ship code + I run the canary") — do not launch VMs
      for it. (repo: market-tick-data-service)

## Track 6 — RENDER: data-status surface #4 + RESTORE the enumeration view · P1

- **Sources**: `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (HYPERLIQUID/ASTER 3.77M/1.07M invisible),
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`, the removed-feature archaeology
  (`deployment-api@47a7f67`/`953fa81`/`512180be` gated/suppressed/canonicalised-away the distinct-values view
  2026-07-16→18).
- **Close-out criterion**: data-status renders the canonical DeFi ids; the raw distinct-values audit view is live again.

- [x] ✅ [BACKEND] P1. **SHIPPED + LIVE (operator ask 2026-07-18): `instruments-service@64a58cc1` (by_chain projection +
      `chain` read-col) + `deployment-api@0d2f6e6` (endpoint) + `deployment-ui@4afcfd8` (panel, `pw:L2 ✓`
      `data-status-distinct-values.spec.ts`).** `GET /api/data-status/distinct-values/{asset_group}` returns per-axis
      distinct values (venues/instrument_types/data_types/**chains**) each with `is_canonical` (exact UAC-SSOT-set
      membership: `VENUES_BY_ASSET_GROUP`/`InstrumentType`/`DATA_TYPES_BY_ASSET_GROUP`/`MAINNET_CHAIN_IDS`), sourced
      from the nightly `coverage.json` rollup keys (single bounded blob read — NO new corpus walk), values NOT
      collapsed. **It immediately surfaces the Wave-D worklist** (real defi drift measured: 76 venues incl.
      AAVE/AAVEV3/AAVE_V3 + COMPOUND/COMPOUND_V3 dupes; 17 itypes, 11 non-canonical case/alias drift; 36 dtypes, 10
      non-canonical incl. `dex_pools`→`dex_pool_state`; 24 chains, 3 non-canonical: HYPERLIQUID→HYPERLIQUID_L1 +
      KALSHI_PERP/POLYMARKET_PERP leaking). **Process findings (see Progress Log)**: (a) `@0d2f6e6` was DIRECT-PUSHED
      (no `Quickmerge:` trailer) via the REMOVED git-commit skill — a git-discipline violation; code is green (6 unit
      tests + lint) so accepted, flagged for operator; (b) it also fixed a pre-existing cross-repo drift
      `deployment-api@593327a` (R2c's new `EXPECTED_ACQUISITION_PENDING` hadn't been mirrored into
      `coverage_metrics.py::EMPTY_REASON_KEYS` → tree-break on LDR — via quickmerge). (repos: deployment-api,
      deployment-ui, instruments-service)
- [x] ✅ [BACKEND] P2. **SHIPPED 2026-07-21: `deployment-api@427ede5` (turbo-API fix) + `deployment-ui@83ec561`
      (capability-bundle DRIFT residue prune).** **Root cause (turbo-API)**: `_read_defi_merged_index`'s DEFI-venue
      whitelist (`_allowed_defi_venue_chain_pairs`) is sourced purely from UAC `ALL_DEFI_VENUES` +
      `LEGACY_DEFI_VENUE_ALIASES`; HYPERLIQUID and ASTER are CEFI-registered hybrid on-chain-CLOB venues never declared
      in UAC's DEFI registry, so their real, currently-captured chain-side rows under `asset_group=defi` (confirmed live
      2026-07-10: 3.77M `(HYPERLIQUID, HYPERLIQUID)` rows 2023-11-01→2026-05-31, 1.07M `(ASTER, BSC)` rows
      2024-04-03→2026-05-31) were silently dropped BEFORE the aggregator ever saw them — not a stale cache, not a naming
      mismatch, a pure registry-completeness gap in the whitelist filter. **Fix**: added a deployment-api-local
      supplemental whitelist (`_CEFI_DEFI_HYBRID_VENUE_CHAIN_PAIRS`, `defi.py`) admitting these two confirmed
      `(venue, chain)` pairs — NOT a double-counting risk since this whitelist only gates DEFI-category bucket reads,
      completely separate from CEFI's own coverage computation (matches the operator-confirmed hybrid architecture,
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` Update §3: CEFI holds instrument
      definitions, DEFI holds chain-level settlement data). Traced the downstream `dates_expected`/`venue_start`
      resolution (`venue_resolution.py`) to confirm it gracefully falls back to observed-date-range for undeclared
      venues (no crash, no stale-cache dependency). Durable fix still belongs in UAC's `ALL_DEFI_VENUES` (out of this
      dispatch's deployment-api/deployment-ui scope) — this is the documented stopgap, flagged in the code comment +
      `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. 2 new regression tests
      (`TestCefiDefiHybridVenueWhitelist`, `test_data_status_service.py`), full `quality-gates.sh` green. Shipped via
      the **dirty-deps carve-out** (direct push, `Quickmerge: agent` trailer) — quickmerge's pre-flight audit was
      blocked by foreign concurrent-agent WIP in unified-trading-library (`defi/` module) and deployment-service
      (`launch-canonical-migration-vm.sh`), neither touched. **Live re-verification attempt**: inconclusive — the real
      GCS DEFI manifest (`_index/availability_index.parquet`, ~1.9GB) is being actively rewritten by the manifest
      consolidator several times per minute right now (confirmed generation churn across repeated read attempts, all
      raced to 404), so a fresh full-file read couldn't complete; the fix rests on the 2026-07-10 live-verified evidence
      above + the code-path trace + passing regression tests, not a fresh live pull. **Capability bundle (Track 6 + the
      sibling issue doc's DRIFT-residue finding)**: no generator for
      `capability-manifest.json`/`capability-verdict-matrix.json` exists anywhere in this workspace (confirmed — no
      committed script in deployment-ui or UAC; the verdict-matrix's own reasons cite a `config_space_fuzzer` module
      that doesn't exist either), so per the issue doc's own fallback guidance this was a surgical,
      referential-integrity-verified prune rather than a blind full regen: removed the `venue:drift`/`collateral:drift`
      nodes + their 21 edges from the manifest (574→572 nodes, 2433→2412 edges; zero NEW dangling edge references — the
      pre-existing `venue:ibkr` dangling ref and the pre-existing duplicate `EVENT_DRIVEN` node are untouched, out of
      scope), one stale free-text "Kamino + Drift" mention fixed in a `CARRY_STAKED_BASIS` edge reason, and removed the
      66 `venue=drift` cells from the verdict-matrix with recomputed per-archetype + top-level summary counts (verified
      formula: `available_count=Σlen(available_algos)`, `blocked_count=Σlen(blocked_algos)`, `cell_count`=their sum; new
      summary total=20,544, available=12,122, blocked=7,974, not_registered=448 unchanged). `generated_from_commit` left
      unchanged (still 1000+ commits stale) since this is a documented delta on top of the stale base, not a full regen
      — the durable fix is still recovering/ building the real generator, tracked in the sibling issue doc.
      **Verification**: `tsc`/`eslint`/`vitest` (1038 passed) all clean; updated the 2 hardcoded stale-count assertions
      in `tests/smoke/capability_tab.spec.ts` (574/2433 → 572/2412; summary 21,600/12,977/8,175 → 20,544/12,122/7,974)
      and re-ran — **`pw:L2 ✓` all 9 tests green**, incl. a real browser render of the Capability tab confirming DRIFT
      no longer shown. (repos: deployment-api, deployment-ui)

## Track 7 — CULL: purge the removed venues everywhere (dead-only, snapshot-first) · P1

> **Operator ruling 2026-07-18**: remove the CULLED venues ENTIRELY — UAC + manifest + GCS data + MVP catalogue + docs —
> to avoid confusion. **KEEP** `KALSHI-PERP`/`POLYMARKET-PERP` (roadmap — will be added), `LIGHTER-ZKSYNC`
> (blocked-credentials MVP scaffold — external-data-always-available rule), `EXTENDED-STARKNET` (live MVP). **All
> GCS-data deletes are snapshot-first** (irreversible). NOTE: LIGHTER/EXTENDED/(culled) PACIFICA are CeFi-classified —
> the cefi purge is passed to `cefi_consolidated_closeout_2026_07_18.md`; this track owns the DeFi-side residue.

- **Sources**: `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`,
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`,
  `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`, `/codex/02-data/mvp-scope-canonical.md`
  (STALE — still bolds `PACIFICA-SOLANA` as MVP; code culled it).
- **Close-out criterion**: zero references to culled venues in UAC / manifest / GCS / catalogue / docs; a snapshot
  exists before any delete.

- [x] ✅ [DATA] P1. **Purge the culled Solana-perp venues' DeFi-side residue — checklist item was itself stale; nearly
      all of it was ALREADY DONE (verified 2026-07-21).** Fresh live case-insensitive grep of unified-api-contracts +
      market-tick-data-service for DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN, with every hit read in
      context (not grep-and-conclude): - **architecture_v2 leg specs — already dropped, NOT ~20 files still pending.**
      The `d996e4fe` UAC commit (2026-07-16, cited in
      `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`'s own "UPDATE" section) already
      removed every live DRIFT reference from `archetype_capability_manifest.json`, `archetype_leg_spec.py`,
      `archetype_leg_spec_seeds.py`, `collateral_registry.py`, `jurisdiction_overlay.py`, `order_semantics.py`,
      `simulation_assumptions.py`, `venue_tokens.py` (+5 test files) — re-verified live: the ONLY residual "Drift"
      mention in `architecture_v2/` is one properly-formatted historical note in `archetype_capability_manifest.json`
      line 692 ("...CeFi-perp hedge leg (Drift) removed 2026-07-16, operator ruling..."), matching this cull's own
      comment-marker convention. Zero MANGO/ZETA/PACIFICA hits in `architecture_v2/` at all. **Nothing left to drop.** -
      **`mvp-scope-canonical.md` — already fixed**, `unified-trading-pm@709274a5c` (2026-07-18): grepped the live file,
      zero PACIFICA/DRIFT hits remain; DeFi section now reads "MVP-tag-all today" with no per-venue bolding. **No doc
      edit needed.** - **SOLAYER/PICASSO/CAMBRIAN — record-correction, not part of this ruling.** These were removed
      **2026-06-02** (a DIFFERENT, EARLIER, unrelated operator decision — "no usable/decodable data source" per
      `issues/issue_docs_remediation_sweep_2026_06_02.md`), NOT the 2026-07-16 Solana-perp-DEX-onto-Jupiter ruling this
      todo's own wording implied. Confirmed live: only historical comment markers remain in
      `unified_api_contracts/{testing/vcr_endpoints.py, registry/venue_adapter_keys.py,       registry/capability_declarations/{_defi.py,_defi_chain_data.py}}`
      — no live registry entries, nothing to purge, already at the correct end-state. - **market-tick-data-service — one
      genuine residue item found + removed**:
      `market_tick_data_service/scripts/purge_drift_pacifica_solana_perp_2026_07_16.py`, the (already-executed)
      DATA/STATE purge script itself, which carried its own lifecycle marker ("DELETE this file once the kill is
      verified + journaled"). The kill IS fully verified + journaled
      (`issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` COMPLETION RECORD: 0 residual across
      manifest/catalogue/GCS/per-VM-shards, both asset groups, 3+ post-resume consolidator cycles watched clean). No
      other lingering MTDS handler branches found (`drift_v2_historical_handler.py` / `drift_v2_onchain_decoder.py` /
      any pacifica-named handler were already deleted in `market-tick-data-service@2e674d1f`, "55 files, -11,178
      lines"). Deleted: **`market-tick-data-service@f6176e8b`** (dirty-deps carve-out direct push — quickmerge's
      pre-flight blocked on foreign concurrent WIP in unified-trading-library + unified-api-contracts, confirmed
      unrelated canonical-id/fail-hard-enforcement work, neither touched; `quality-gates.sh --no-fix` green,
      `.qg_last_passed_sha` sentinel matched HEAD before the commit). **unified-api-contracts required NO commit**
      (nothing dead left to remove — see below). - **Confirmed LOAD-BEARING, deliberately left alone (not residue)**:
      (a) `unified_api_contracts/registry/venue_adapter_keys.py::DECOMMISSIONED_VENUE_BASES` — an ACTIVE frozenset
      (`{"DRIFT","PACIFICA","MANGO","ZETA","FLASH"}`) that deployment-api's data-status drilldown reads to
      base-prefix-exclude legacy manifest rows; removing it would REGRESS that filter. (b)
      `unified_api_contracts/canonical/quarantine.py::QUARANTINE_REGISTRY` — a NEW (2026-07-20/21,
      `fail_hard_canonical_enforcement_design_2026_07_20.md`) fail-hard-enforcement mechanism whose ONE seed member is
      `PACIFICA-SOLANA` (265 permanently-honest-raw objects, evidenced, expires 2027-07-21) — deliberately references
      the culled venue so these legacy rows verdict `quarantined` (PASS) instead of `non_canonical` (FAIL) once Stage-3
      read-enforcement wires in; NOT dead code. (c) `DRIFT` as a TOKEN TICKER (not venue) in
      `unified_api_contracts/registry/{defi_major_assets.py,cefi_instrument_universe.py}` — the Drift-protocol
      governance token trades live on non-culled venues (Binance/Bybit/etc, ~40,693 manifest rows per the original
      cull's own scope-guard); this is a different entity from the culled DEX venue and must stay. (d) a
      `_PERP_DEFAULT_CHAIN` DRIFT/PACIFICA chain-default mapping in MTDS's `scripts/migrate_defi_full_v9_canonical.py`
      and a `_RENAMED_VENUES = {"PACIFICA": "PACIFICA-SOLANA"}` mapping in
      `scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — both are historical-data migration utilities (the
      latter has its own `Delete-when:` gated on a DIFFERENT plan's Todo 9, unrelated to this cull) whose correctness
      for any future re-run of already-written legacy rows depends on these mappings; left untouched as
      out-of-scope-for-this-cull rather than risk miscategorising historical data. - **instruments-service +
      deployment-service** were explicitly OUT of this dispatch's repo scope (narrowed to avoid a live file-collision
      with two other concurrently-running agents in those exact repos) — per
      `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`'s own COMPLETION RECORD these already shipped
      (`instruments-service@4d65d468`+`b37e9d82`+`ee19f6f3`, `deployment-service@9b13679`+`194deeb`, all confirmed on
      `origin` as of the 2026-07-18 closing pass) — not re-verified this session, cited as already-closed evidence
      rather than re-audited. (repos: market-tick-data-service, unified-api-contracts, unified-trading-pm —
      instruments-service/deployment-service closed by a prior session, cited above)

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

- [ ] [INFRA] P1. **Resume the paused DeFi crons** (precisely: 4 collect + 3 forward = 7 schedulers currently paused,
      see the correction above — NOT 11+3) AFTER Track-1/2 land so they write the canonical shape; fix the consolidator
      duplicate-race + SIGKILL (**both already CLOSED, see correction above** — only the honest-coverage nightly
      right-size + codex-drift-doc sub-clauses remain). **Because live=batch, no live-only DeFi data_type needs separate
      reconciliation** — the forward writer is already canonical (Half-A done); the open work is Half-B (migrate the
      historical corpus) then resume forward. Do not resume before the currently-running per-instrument migration VM
      finishes (it is actively migrating exactly the 4 paused collectors' data types — resuming now races live writes
      against it). **ADDITIONAL GATE (2026-07-23)**: `uts-prod-mtds-collect-solana-defi-cron` specifically must also
      wait for the Solana AMM symbol-collision fix (the `[CODE] P1` todo above, "writer emits the wrapped filename").
      Confirmed via live check
      (`gcloud scheduler jobs describe uts-prod-mtds-collect-solana-defi-cron     --location=asia-northeast1`,
      `state: PAUSED`) + a systematic GCS sample (every 3 days, 2026-06-05 through 2026-07-23, both venues, correct
      derived `pipeline_mode=batch_onchain_subgraph`) finding ZERO `data_type=dex_pool_state` objects for ORCA/RAYDIUM
      anywhere in that window — the collector has not written a single canonical-shape shard since before the pause, so
      the collision bug has NOT corrupted any production data yet. It WILL start doing so on day one of resume if the
      symbol fix hasn't landed first — add it as an explicit pre-resume checklist item for solana-defi specifically, not
      just "after Track-1/2". (repos: deployment-service, market-tick-data-service)
- [ ] [BACKEND] P2. **`dex_pools_handler.py` (CLI op `collect-dex-pools`, cron `uts-prod-mtds-collect-dex-pools-cron`,
      currently PAUSED — confirmed still registered, not retired, zero immediate risk while paused) shares Track 1's
      Solana-AMM-pool symbol-collision gap in a MORE severe form** (`_dex_pools_subgraph.py::_collect_solana_dex` never
      attempts symbol resolution at all, always falls back to the bare pool address) and is **NOT covered by
      `market-tick-data-service@0d83a8a9`** (that fix only touches `_solana_row_symbol`, which this handler never
      calls). Needs its own fix, or an explicit retire decision, before its cron is safe to resume too. (repo:
      market-tick-data-service)

## Open follow-ups (carried forward from the pre-2026-07-24 Progress Log's "Deferred work after 2026-07-22/23" tables)

> Full narrative + evidence for every row below lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md)
> ("Deferred work after 2026-07-22" / "…-07-23" sections) — condensed to actionable todos here so nothing genuinely open
> got silently archived. Items already marked DONE/SHIPPED/RESOLVED in that history are NOT repeated here.

- [ ] [SCRIPT] P3. **Root-cause `quickmerge.sh` silently resetting an unpushed commit** (observed 2026-07-22, 2
      hypotheses ruled out, cause not confirmed, non-reproducible on retry). Needs a `bash -x`/`set -x` trace the next
      time it recurs. (repo: unified-trading-pm)
- [ ] [OPERATOR] P1. **Run `delete_migrated_defi_markers_2026_07_23.py --apply`** once pushed (blocked on
      `issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`, or pull the local
      `market-tick-data-service` commit directly) — prod-bucket delete, human-gated per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`.
- [ ] [DATA] P2. **21 glued-id rows found in the 2026-07-23 manifest rebuild**: 9 ORCA/SOLANA `dex_pool_state` cells
      (2025-12-23..12-31) need the higher-timeout/parallel-write migration retry (tracked in
      `issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md`'s addendum); 12 fresh `liquidations`
      bundles (`20260723_013349`, AAVE_V3/COMPOUND_V3/GMX/FLUID/SPARK × 8 chains) suggest that handler's forward-write
      path may still use the pre-R1 bundled convention — confirm whether it needs the same per-instrument fix
      `write_defi_rows()` already got.
- [ ] [DATA] P1. **~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN migration** — gated on lending-writer-retire todos 7/8/10/11
      (per-data_type target mapping + atomic 3-repo wave + runtime proof), see
      `defi_lending_writer_retire_prerequisite_2026_07_20.md`.
- [ ] [DATA] P1. **Residual canon walk C2-C12 + instrument_type case/venue-spelling unify** — 6 items SCOPED not
      executed (C2/C3/C4/C9/C11/C12), code-side verified GREEN for C2/C3/C9/C12; ALL SIX need a data-side read of the
      live `_index` once the 2 canonical-migration VMs reach a terminal state, then
      `audit_canonical_form.py --probe-paths` against the single consolidated bucket. Also surfaced but not filed:
      `staking_yields_handler.py`'s `collect-staking-yields` CLI op has zero Cloud Scheduler jobs (dead code?);
      `lst_rates_handler.py` writes to a non-canonical, non-hive path.
- [ ] [DATA] P2. **Purge 1.79M dup + ~219.5K phantom + seed ~63.9M `expected_unattempted`** (incl. 812,055
      solana-pool-vocab rows, 215,864 non-POOL EU rows) — large data op, sequence AFTER the glued-id manifest rebuild
      (both touch the same consolidated index).
- [ ] [BACKEND] P2. **Async fan-out + executor-offload for the DeFi write path** (`solana_defi_handler.py`,
      `dex_pools_handler.py`, `_dex_pools_subgraph.py` — 4 upload sites total) — investigated, correctness-sensitive
      (shard isolation, `record_captured` grain, heartbeat monotonicity all load-bearing), needs a dedicated focused
      session, not a squeezed turn. Design sketch (UTL `ParallelPerSymbolRunner` with `manifest_writer=None`, then
      sequential `record_captured`/heartbeat over gathered results) recorded in the history doc. The 3
      `service_config.py` knobs (`defi_max_concurrent_fetches`/`defi_max_inflight_tasks`/`defi_max_concurrent_uploads`)
      are a trivial, un-risky first step.
- [ ] [OPERATOR] P2. **2-VM TheGraph canary** — code-only so far per the original session's instructions; launching the
      canary VMs is operator-owned (Q3 ruling: "ship code + I run the canary").
- [ ] [DATA] P1. **Resume paused DeFi crons** (4 collect + 3 forward = 7 schedulers) + fix the honest-coverage-nightly
      right-size + codex-drift doc — gated on Track 1 (LENDING migration + canon walk above) + Track 2 (path-shape-pin
      code half) + the currently-running per-instrument migration VM finishing first (resuming now would race live
      writes against the exact data types it's mid-migrating).
- [ ] [DATA] P1. **DeFi MVP backfill to 100%** — C-GREEN gated on Track 1 (LENDING migration + canon walk, above) +
      Track 2 (path-shape-pin) + Track 3 (`catalogue_pool_ids_for_shard` generalization, execution work not a decision).
      Backlog task `mvp_backfill_defi_onchain_v10-001` stays parked (`priority: 999`) until
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` flips true.
- [ ] [BACKEND] P2. **`is_defi_force_include_pool` wiring** — the UAC-side predicate
      (`unified_api_contracts.registry.defi_major_assets.is_defi_force_include_pool`, `DEFI_FORCE_INCLUDE_POOLS`) exists
      and is exported but is called from nowhere in current instruments-service (0 hits). High-TVL Raydium pool
      force-include behavior (32 legacy-only pools incl. XMR/USDC $47M, BNB/USDC $18M). Genuine unshipped work sitting
      in instruments-service `stash@{0}` (diff-confirmed 2026-07-22, NOT fully redundant with current HEAD) —
      cherry-pick ONLY the `filter_defi_instruments_by_relevance`/`_add_force_include`/factory-import hunks.
- [ ] [DATA] P3. **Cannot-be-done-yet monitoring**: orphan-sweep VM (`orphan-sweep-defi-20260723-043605`) reaching
      ACCEPTANCE — just monitor via `gcloud compute instances list --filter="name~orphan-sweep-defi"`, do not poll
      tightly.
- [ ] [DATA] P1. **Fake-history relabel-forward migration script** — operator ruled on disposition (relabel to true date
      via `available_at`), script not yet written. Bounded scope (17 known days/2 venues), not gated on the orphan-sweep
      finishing. See `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`.
- [ ] [DATA] P2. **Get TRUE final fake-history scope** — needs `--source final` against
      `instruments-service/scripts/scope_defi_dex_pools_fake_history.py` once the orphan-sweep VM's final report is in.
- [ ] [DATA] P2. **cefi/prediction timestamp-provenance audit** — cefi/prediction backfills were only sampled for
      canonical-SHAPE, not this specific `available_at` timestamp mismatch class.
- [ ] [BACKEND] P2. **Solana AMM symbol-collision code fix** — verified CLEAN (zero shards corrupted, collector paused
      since before the rename), added as an explicit pre-resume gate on `collect-solana-defi`, but the actual fix (wire
      the fee/tick-spacing discriminator into `_solana_row_symbol`/`write_defi_rows`) is unwritten — genuinely
      correctness-sensitive live-write-path code, do as its own focused pass (same caution as the async-fan-out item
      above). Rejected approach (don't retry): MTDS calling instruments-service's `build_pool_identity` directly at
      write time — violates the T4 tier-import rule.
- [ ] [BACKEND] P3. **`dex_pools_handler.py`'s parallel Solana writer — still scheduled?** Unverified whether this
      second, cruder (always-bare-address) writer is still actively cron'd alongside `solana_defi_handler.py` — needs a
      quick read of `main.py`'s CLI dispatch table.

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

> **The full tick-by-tick history was NOT deleted** — it lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md)
> (contradiction-resolution audit + the complete 2026-07-18→2026-07-23 Progress Log, including the full "Deferred work
> after 2026-07-22/23" tables this section condenses above). Every genuinely-open item from those tables now has a
> canonical todo under "Open follow-ups" above or the relevant Track — nothing was silently archived.

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

## Aggregated source docs (referenced, not duplicated — every other active defi + defi-touching plan/issue)

> **Format**: each bullet is a real repo-root-relative link followed by a condensed digest of its currently-OPEN
> top-level todos (unchecked `- [ ]` only — `[x]` and `[~]` excluded). `+N more` means P2/P3 items exist beyond the ones
> listed — open the file for the rest. Digests condensed 2026-07-24 so an AO worker can triage from this doc alone.

- **Strategy/PnL/backtest axis**:
  - [`plans/active/defi_strategy_pnl_axis_index_2026_07_24.md`](/plans/active/defi_strategy_pnl_axis_index_2026_07_24.md)
    — 0 own top-level todos (active entry-point index, not closed/archived — it references other plans instead of
    carrying its own checkboxes). Most of what it points to is already indexed elsewhere in this section
    (`lst_rate_honest_coverage_2026_07_21.md`,
    `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`,
    `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
    `issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
    `issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`); two of its links are NOT tracked elsewhere
    here: `plans/active/distinct_values_noncanonical_audit_2026_07_20.md` (`asset_group: [cross-cutting]`, 4 open todos,
    out of this plan's defi-primary scope) and `plans/active/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md`
    (`asset_group: [infrastructure]`, explicitly "not defi-scoped itself" per its own doc).

- **Bucket / storage / migration**:
  - [`plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md`](/plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md)
    - **[SCRIPT] P2.** 3 diagnostic/migration scripts (MTDS + strategy-service) still hardcode dead flat bucket-name
      templates for dex-pools/lst-rates/perp-funding — need the same
      `resolve_bucket_name(kind="tick-data", asset_group="defi")` repoint already shipped elsewhere.
    - **[CHORE] P3.** Housekeeping cluster (low-risk): delete a script past its own `Delete-when`, fix a stale
      `OPERATIONS` bucket_type dict, audit ~8 `Lifecycle: campaign` scripts with dead bucket names, fix stale comments.
  - [`plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`](/plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md)
    - **[SCRIPT] P0.** Final defi MVP verification — all 6 data_types `attempted_failed=0` AND `expected_unattempted=0`
      post-genesis; subgraph-zero-on-alive-day cells typed honest, never silent.
  - [`plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md`](/plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/active/candle_canonical_path_migration_execution_2026_07_24.md)
    (16 open, all P0/P1 — this is the cefi-authored candle-namespace migration epic; defi is sequenced FIRST in its
    per-AG apply order)
    - **[DATA] P0.** Rebuild code tarballs for the 4 already-shipped repos so canonical-shape changes are live on VM
      images.
    - **[DATA] P0.** VERIFY on `-test-` via `/data-pipeline-check-mdps` that the writer emits the canonical shape — GATE
      before any prod-data executor.
    - **[DATA] P0.** VERIFY readers dual-read correctly against both canonical and legacy-flat prefixes.
    - **[SCRIPT] P0.** Run the sanctioned Tier-2 spot-VM single-walk census for a precise per-AG object count before
      sizing the migration fleet.
    - **[SCRIPT] P0.** Build the migration executor — idempotent, sharded, `--apply`-gated, PROGRESS.json checkpointed.
    - **[SCRIPT] P0.** Implement the path transform (backward-add `instrument_type=`, keep SOURCE `data_type`).
    - **[SCRIPT] P0.** Implement DEDUP for the split-brain candle layout (~2x inflation on cefi/tradfi/prediction).
    - **[SCRIPT] P0.** Implement PURGE of empty-stem objects (~0.6-0.8% defect rate).
    - **[SCRIPT] P0.** Implement QUARANTINE for unresolvable legacy TradFi leaf ids — never guess.
    - **[SCRIPT] P0.** Wire manifest re-record to the SOURCE-keyed row into the executor for correct post-migration
      skip-if-fresh.
    - **[SCRIPT] P0.** Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum.
    - **[DATA] P0.** Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch.
    - **[DATA] P1.** P6 drain+snapshot: coordinate with the running cefi raw_tick VMs before the candle migration
      writes.
    - **[DATA] P0.** P7 per-AG SPOT migration apply, order defi→prediction→cefi→tradfi.
    - **[DATA] P0.** P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle to
      `processed_candles/`.
    - **[DATA] P1.** Root-cause + close the candle object↔manifest disconnect so skip-if-fresh can be trusted at scale.

- **Coverage / honest-coverage / manifest**:
  - [`plans/active/data_completion_defi_2026_07_15.md`](/plans/active/data_completion_defi_2026_07_15.md) (25 open: 10
    P0, 9 P1, 6 P2 — P0/P1 listed in full, P2 capped)
    - **[DATA] P0.** B0 — RUN the existing `expected_unattempted` chain for DeFi (wire the MTDS batch orchestrator
      through IS pre-flight → `record_expected_unattempted`, run a prod batch, validate the denominator). GATED on
      C-GREEN.
    - **[DATA] P0.** C0 — path + bucket canonicalisation (the foundational migration), RUN ON A VM. C0a-C0e DONE; C0f
      (delete legacy originals) remains: 2 of 14 legacy buckets (`lending-indices`) still deferred pending a live VM
      finishing.
    - **[DATA] P0.** C11 — deeper phantom audit: are the POST-launch dex `captured` rows actually object-backed? Re-run
      the captured-vs-objects walk after C12 lands, without read-path normalisation.
    - **[DATA] P0.** D1 — features-onchain-defi is near-empty (3 rows); features-delta-one-defi +
      features-volatility-defi have no index. Run the features backfill. GATED on C-GREEN.
    - **[DATA] P0.** E1 — CeFi `derivative_ticker` funding-carrier fetch failures: ASTER partially resolved, OKX-FUTURES
      still unverified — re-check independently.
    - **[DATA] P0.** G1 — Launch the full 2024-06-01→2026-06-01 backfill VM (Drift V2 historical + Solana spot DEX
      state). Operator-launched.
    - **[DATA] P0.** G2 — Launch live-mode snapshotters via `--live --continuous` (Drift funding hourly + Solana DEX
      pool state 1-min). GATED on G1+C-GREEN.
    - **[PLAY] P0.** G3 — Run 24h paper trade via `run-paper.sh --strategy SOL_BASIS`. GATED on G2.
    - **[HUMAN] P0.** G4 — Promote to live wallet — HUMAN-ONLY hard-stop. GATED on G3.
    - **[DATA] P0.** `instruments-store-defi` reference-surface canonical-form walk — same
      v9/`asset_group=`/`pipeline_mode=`/`source` target as the MTDS C0 walk; re-run CF-1…CF-12 before any DeFi
      instruments writer relaunch.
    - **[DATA] P1.** C2 — data_type alias dedup across buckets (hyphen→underscore; pool/swap collapse to
      `dex_pool_state`/`dex_pool_swaps`). Rides the C0 walk.
    - **[DATA] P1.** C3 — VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated
      `chain`. Same walk.
    - **[DATA] P1.** C4 — schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk.
    - **[DATA] P1.** C5 — phantom-grid delete: remove the cartesian `data_type × venue` empty grid in
      `market-data-tick-defi`.
    - **[DATA] P1.** C8 — fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only
      a fraction (lst 14/22, lending 6/21, perp 5/8); genuine absentees DRIFT-SOLANA/FRAX/MORPHO/FLUID.
    - **[DATA] P1.** C9 — legacy DeFi bucket object paths are pre-canonical (`category=` not `asset_group=`, no
      `pipeline_mode=`); normalise in the same single-walk as C2-C4.
    - **[DATA] P1.** D2 — MDPS swaps_ohlcv reprocess for the stale chain-column `attempted_failed` rows (28,634
      UNISWAP_V3-ETHEREUM + companion venues). GATED on C-GREEN.
    - **[CODE] P1.** G5 — Phoenix radix-slab decode (top-of-book bid+ask+size); not gated on G1-G4.
    - **[DATA] P1.** BLOCKED-CREDENTIALS — gas-fees MANTLE paid RPC (free public RPC 429-throttles `eth_feeHistory`);
      unblock = a paid MANTLE RPC key in Secret Manager.
    - +6 more (P2: C6 Pyth backfill, G6 Jupiter historical reconstruction, G7 Orca tick-array decode, G8 Raydium second
      pool, FLAG2 `_BUCKET_CATEGORY_OVERRIDES` DeFi scope, sub-bucket blank-chain phantom audit) — see file for the
      rest.
  - [`plans/active/lst_rate_honest_coverage_2026_07_21.md`](/plans/active/lst_rate_honest_coverage_2026_07_21.md) (7
    open)
    - **[MTDS] P2.** #1 CEX-spot contiguity backfill — full-history Tardis backfill over `*-SPOT` LST venues (9 real
      (venue,symbol) cells across 3 venues; BYBIT structurally absent). Blocked twice on VM OOM; filed as its own P0
      bug, not relaunching blind.
    - **[FEATURES] P2.** #4 `lst_yields` backfill — Solana-LST sub-fix (DefiLlama historical-ratio fallback) SHIPPED;
      genesis dates validated + corrected for 7 tokens (Sanctum INF was 2.3 years too late); ezETH/rsETH historical MTDS
      collector backfill still held pending real-infra caution.
    - **[MTDS] P3.** #2 DEX fill — deep-backfill `dex_pool_swaps`; endpoint + price column now live, LAUNCHED
      (operator-acked) — verify completion.
    - **[STRATEGY] P2.** A2 staking leg — wire `carry_staked_basis` STAKING_REWARD/CARRY to the `lst_yields` index
      ratio; explicit-zero the Aave-lending mismodel; ship to LDR.
    - **[STRATEGY] P3.** Recursive-staking borrow leg — wire the `aave_borrow_index` cost leg once the Aave oracle
      (collateral) lands.
    - **[MTDS] P3.** Solana `lst_rates` `pipeline_mode` mislabels which tier supplied each row (Tier-4 DefiLlama
      market-proxy rows stamped as if on-chain/subgraph) — fix `pipeline_mode_for_source` to key off the real per-row
      `method`.
    - **[MTDS] P3.** Prove force + skip per surface on `-test-` — BLOCKED-CREDENTIALS (the `-test-` bucket doesn't exist
      / SA lacks `storage.buckets.get`+`create`).
  - [`plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`](/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md)
    (9 open: 1 P0, 6 P1, 1 P2, 1 P3 — P0/P1 listed in full, P2/P3 capped)
    - **[OPERATOR] P0.** BLOCKED-OPERATOR-DECISION — coordinate a maintenance window with the operator for the
      prediction + tradfi consolidator crons before pausing either.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — snapshot the prediction canonical manifest index + pause its
      consolidator cron. Snapshot half DONE 2026-07-14; cron-pause half not done (no operator go-ahead).
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — apply `rebuild_prediction_manifest.py` (full date range),
      force-consolidate, re-run the fill-rate audit.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — resume the prediction consolidator cron; record before/after fill-rate
      evidence.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — snapshot the tradfi canonical manifest index + pause its consolidator
      cron. Snapshot half DONE 2026-07-14; cron-pause half not done.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — apply `rebuild_tradfi_manifest.py` (full date range),
      force-consolidate, verify fill rate + guardrail + row count.
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — resume the tradfi consolidator cron; record evidence.
    - +2 more (P2 present-the-defi-audit-for-go/no-go decision, P3 stretch implement-if-GO) — see file for the rest.
  - [`plans/active/data_pipeline_check_mdps_features_2026_07_20.md`](/plans/active/data_pipeline_check_mdps_features_2026_07_20.md)
    (≈27 open: 14 P0, 8 P1, 5 P2 — P0/P1 listed in full, P2 capped)
    - **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-mdps` e2e across all AGs × venues × data_types × timeframes.
    - **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-features` e2e across all families × valid AGs.
    - **[DATA] P0.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + migrate existing data to zero
      orphans.
    - **[DATA] P0.** Produce a concrete ETA to backfill all remaining DeFi MVP (benchmark × remaining-shard count ×
      throughput × fleet width × $ cost).
    - **[DATA] P0.** Verify whether MDPS `max_workers` actually overlaps GCS writes — measured evidence implies SERIAL;
      up to ~8x ETA impact if fixed.
    - **[DATA] P0.** Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe) — drives which AGs
      to run + the ETA denominator.
    - **[DATA] P0.** Run `/data-pipeline-check-mdps` across all relevant AGs not already in candles.
    - **[DATA] P0.** Run `/data-pipeline-check-features` across all shards (8 families × valid AGs).
    - **[DATA] P0.** VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win — the biggest
      unknown in the ETA.
    - **[SCRIPT] P0.** Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`), with the
      1.4M-row perf guard.
    - **[DATA] P0.** Audit every `read_availability_index` caller on defi for a missing column/filter projection (1.58
      GB index, OOM risk).
    - **[SCRIPT] P0.** Fix the shared seed context (per-call immutable value object + collision-proof cache key) + a
      regression test — prerequisite for raising in-process concurrency.
    - **[SCRIPT] P0.** Implement R1 (concurrent date-subprocesses) — the months→weeks throughput lever, safe today.
    - **[DATA] P0.** Real-VM re-measure of end-to-end per-instrument-day rate against a PROD-sized index after the
      read-path fix lands.
    - **[DATA] P1.** Steady-state benchmark VMs (250GB disk) per representative shard-type; project full-history time +
      SPOT cost + parallelization headroom.
    - **[SCRIPT] P1.** Backfill-processing path optimized learning from cefi (within-VM multiproc, faster libs,
      fleet-wide).
    - **[DATA] P1.** Full DeFi-MVP candle backfill on real infra — GATED on
      `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8.
    - **[SCRIPT] P1.** Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps` (+ features twin)
      as a distinct `content_check=` verdict.
    - **[DOC] P1.** Correct `/codex/05-infrastructure/spot-vms-for-backfill.md` — preemption signal is now installed by
      `setup-data-pipeline-vm.sh` as a systemd unit, not via `launcher_common.sh`.
    - **[SCRIPT] P1.** Close residual risk 1 — make arg-required launchers relaunchable (features especially).
    - **[DATA] P1.** Blast radius: did any past prod MDPS run use `max_workers>1` over a heterogeneous list? Affected
      shards may need seed re-derivation.
    - **[SCRIPT] P1.** Implement R1 bounded-concurrent `_run_date_as_subprocess` dispatch. Gated on the seed-context
      fix.
    - +5 more (P2: ship/quickmerge housekeeping, codex promotion of the two-signal table, correct performance-targets.md
      compute-vs-IO classification, vectorize `_calculate_volume_clock_features`, write-batching for per-timeframe
      parquet writes) — see file for the rest.
  - [`plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`](/plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md)
    (14 open: 8 P1, 4 P2, 2 P3 — P1 listed in full, P2/P3 capped)
    - **[DESIGN] P1.** Fix the mockup's leaf model everywhere it still needs it — re-verify SPORTS/PREDICTION don't have
      an analogous mistake once the operator's review reaches those tabs.
    - **[DESIGN] P1.** Design the CEFI instrument-definition parquet resharding to (date, venue, instrument_type), one
      file per shard — design only, operator-gated before actual resharding.
    - **[CODE] P1.** Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM — same blank-`instrument_type` bug hits
      DRIFT/KAMINO/MARGINFI/MARINADE/ORCA/RAYDIUM/SOLEND-SOLANA + CURVE-OPTIMISM.
    - **[CODE] P1.** Pull the real per-instrument_type breakdown for DERIBIT live and confirm OPTION coverage is
      actually healthy.
    - **[CODE] P1.** Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries (deployment-api + deployment-ui).
    - **[CODE] P1.** Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis onto the
      `reference_scope`-based model.
    - **[VERIFY] P1.** Raw-parquet spot-check 5 additional CeFi venues (OKX-FUTURES, bare BYBIT, BINANCE-FUTURES,
      KRAKEN-FUTURES, BINANCE-DELIVERY) for the same multi-type blank-collapse.
    - **[CODE] P1.** Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split (pre-fix
      rows still blended+blank).
    - +6 more (P2: remove phantom OPTION on bare OKX, retire DERIBIT-COMBO as its own venue key, extend CLOB-on-chain
      classification to HYPERLIQUID/ASTER, audit MTDS/reference-data conflation elsewhere; P3: update a UI tooltip,
      clarify the venue-detail link naming) — see file for the rest.
  - [`plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`](/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md)
    (6 open)
    - **[CODE] P1.** Add a falsifier test that fails CI when a venue/source key present in both coverage registries
      disagrees on its date — the permanent backstop against re-divergence.
    - **[DATA] P1.** Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT,
      DERIBIT, OKX, BINANCE, BYBIT, HYPERLIQUID) against measured manifest reality.
    - **[DATA] P2.** Resolve the CME mismatch — probe the manifest to confirm 2020-01-01, drop the `# TODO verify`
      marker.
    - **[DATA] P2.** Resolve the POLYMARKET mismatch (CLOB-launch vs first-actual-instrument, ~2.3-year gap).
    - **[DATA] P3.** Resolve the small 1-21 day DeFi protocol drifts (CURVE, UNISWAP_V2/V4, BALANCER, LIDO) + the
      AAVE_V3 chain-axis question.
    - **[DATA] P3.** Publish an explicit key-mapping table between the two registries' key schemes — prerequisite for
      the P1 falsifier todo.
  - [`plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
    (3 open)
    - **[DATA] P0.** VERIFY the prod projection before sizing the win — is `_publish_emission_check` actually firing on
      prod MDPS backfills?
    - **[DATA] P0.** The 1.58 GB defi-prd index is its own P0 — audit every `read_availability_index` caller for a
      missing column/filter projection (OOM risk).
    - **[DOC] P2.** Record in codex that the per-VM manifest flush is already debounced, so the "flush is O(n²)"
      hypothesis isn't re-derived.
  - [`plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
    (2 open)
    - **[DATA] P1.** Prove the fixed writers green on one real day, then migrate the historical flat
      `instrument_availability`/`market_lifecycle`/`futures_contracts` objects up into full hive. Deferred to Round 2
      (likely VM-scale).
    - **[REVIEW] P1.** On writer ship, record the full-hive cutover date in
      `/codex/02-data/canonical-cutover-register.md` + flip the non-canonical-path-inventory row #16 to EXECUTED.
  - [`plans/active/issues/estate_orphan_assessment_2026_07_21.md`](/plans/active/issues/estate_orphan_assessment_2026_07_21.md)
    (4 open)
    - **[INFRA] P1.** Run the orphan sweep for defi/cefi/tradfi/prediction on a VM — cefi + prediction COMPLETE (real
      measured `E_orphan_real` counts); defi IN PROGRESS (3rd attempt, now resume-capable after 2 SPOT preemptions).
    - **[CODE] P2.** Make the manifest load resumable/streamed in `migration_orphan_sweep.py` — folded into
      `migration_orphan_sweep_performance_decay_2026_07_22.md`, don't duplicate investigation here.
    - **[CODE] P3.** `GcsEventSink` never `.shutdown()`s its background `ThreadPoolExecutor` — costs ~11.5 real SPOT-VM
      minutes per batch script using this pattern.
    - **[CODE] P2.** Give `backfill_orphan_class_e.py --apply` a batched-incremental `record_cells()` call
      (cell-boundary-safe) so a SPOT preemption doesn't lose 100% of progress.
  - [`plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`](/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/phantom_captures_defi_2026_06_28.md`](/plans/active/issues/phantom_captures_defi_2026_06_28.md)
    (3 open)
    - **[SCRIPT] P1.** Diagnose defi phantom root cause: uniform ~25,400 counts across 7 `swaps_ohlcv_*` granularities
      suggest a single batch writer failure.
    - **[SCRIPT] P1.** Apply defi phantom reconciliation (219,529 rows → `attempted_failed`) BEFORE defi backfill G0.
    - **[SCRIPT] P2.** After reconcile + backfill: confirm defi OHLCV writers are fixed so new writes don't re-create
      the phantom pattern.

- **DeFi-specific canonicalisation residuals**:
  - [`plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md`](/plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md)
    (2 open)
    - **[HUMAN-AGENT] P1.** Pyth Hermes coverage SSOT + jitoSOL pre-2023-10 backtest scope — operator go/no-go on
      Pythnet replay vs clipping the backtest window (default: clip).
    - **[SCRIPT] P1.** Latent Bug-class-3 local fallback drift sweep — find any local fallback overriding a UAC value
      without an explicit comment.
  - [`plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`](/plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md)
    (5 open — ⛔ GATES Track 1's LENDING retire)
    - **[CODE] P0.** Ship the retire atomically across UAC+MTDS+UTL in ONE wave — a partial wave IS the outage (the
      documented meta-lesson of the earlier reversal).
    - **[DATA] P0.** Runtime green proof — run it, don't read it: real one-day run for each of the 8 writers,
      manifest-verified `captured` + zero `attempted_failed`.
    - **[DATA] P0.** Three-surface agreement check on the shards from the runtime proof — GCS path · parquet column ·
      manifest row. Any disagreement is a hard fail.
    - **[DATA] P1.** Grain regression check — confirm the type change didn't disturb the per-market `record_captured`
      grain that converts `expected_unattempted`.
    - **[PM] P1.** Flip the gate + hand off — record evidence, flip the migration plan's banner from BLOCKED to CLEARED,
      notify the operator the ~16.7M-row migration may begin.
  - [`plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md`](/plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md)
    (3 open)
    - **[VERIFY] P0.** Phase-D gate — full Stage-4 historical carry tracer over 2022-01-01..today across all 7
      archetypes. REOPENED 2026-07-12 (prior ✅ covered gate LOGIC only; the 2022→today data outcome was 10/10
      SKIP_NO_DATA).
    - **[SCRIPT] P1.** Re-run `phase_d_gate.py` against real 2022→today data once the DeFi backfill reaches full
      coverage.
    - **[AGENT] P2.** `SolidlyCLForkPool` historical golden-swap validation — ≥20 Velodrome + ≥20 Aerodrome real
      on-chain fixtures within 5 bps.
  - [`plans/active/issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md`](/plans/active/issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md)
    (2 open)
    - **[BACKEND] P2.** Trace `backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`'s POOL code path — does it
      enforce the "pool or not" invariant, or is this a docstring-only defect?
    - **[BACKEND] P2.** Apply the operator's ruling (default A: test wins, fix the docstring), reconcile the losing
      side, pin a test naming the authoritative policy.
  - [`plans/active/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`](/plans/active/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`](/plans/active/issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md)
    (3 open)
    - **[BACKEND] P1.** Generalise `catalogue_pool_ids_for_shard` beyond `instrument_type=='pool'` — the prerequisite
      for any non-pool residual reconciliation.
    - **[BACKEND] P1.** Add a per-instrument residual emitter to the capturable non-POOL handlers
      (`lending_indices_handler`, `risk_params_handler`, `lst_rates_handler`, `evm_defi_collectors`).
    - **[DATA] P2.** Check whether affected (venue, chain) pairs are in UAC `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` or
      `PROTOCOL_PAUSE_WINDOWS` — superseded by the enumerator's priority ordering, may no longer be decision-relevant.
  - [`plans/active/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`](/plans/active/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`](/plans/active/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md)
    — 0 open todos (closed/archived/record-only) — its still-open relabel-forward verification is tracked as its own
    todo under `defi_track01_per_instrument_and_canon_id_2026_07_24.md` below.
  - [`plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`](/plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md)
    (1 open)
    - **[DESIGN] P3.** Author the dedicated implementation plan when this becomes a priority — not urgent, a 2-venue gap
      on a data_type with non-zero coverage elsewhere.
  - [`plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`](/plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md`](/plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`](/plans/active/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md`](/plans/active/issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`](/plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md)
    (1 open)
    - **[SCRIPT] P2.** Re-run `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s G2 gate for `lending_indices` after the
      backfill completes.
  - [`plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`](/plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md)
    — 0 open todos (closed/archived/record-only) — its follow-up capture work is tracked under
    `defi_track01_per_instrument_and_canon_id_2026_07_24.md` below.
  - [`plans/active/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`](/plans/active/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`](/plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md)
    (1 open)
    - **[DESIGN] P1.** GATED on parity results — decide whether to demote `perp_funding` from a captured raw type to a
      DERIVED interval view now that `derivative_ticker` is the canonical raw funding home for all perps.
  - [`plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`](/plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`](/plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md)
    (3 open)
    - **[VERIFY] P2.** Confirm whether adding a data_type to `DATA_TYPES_BY_ASSET_GROUP["defi"]` actually changes
      `expected_unattempted`/`completeness_pct`, or is scoped independently.
    - **[CODE] P2.** Gated on the verify above — if inert, register `perp_daily_ctx` as its own canonical data_type +
      SchemaContract; backfill manifest rows for existing shards.
    - **[OPERATOR-DECISION] P3.** Whether/when to execute the perp_funding-demotion todo, and whether
      `perp_daily_ctx`/mark-price should fold into that same decision.
  - [`plans/active/issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`](/plans/active/issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md)
    (5 open)
    - **1. [DATA] P2.** Confirm the stale-row hypothesis — compare the desynced row's `attempted_at`/`available_at`
      against the handler's git-blame introduction date.
    - **2. [DATA] P2.** Measure blast radius beyond the single sampled row — scan for any row where `pipeline_mode`
      implies a different vendor than the `source` column names.
    - **3. [CODE] P2.** Fix `vault_share_price_handler.py` to pass an explicit `source=` on every
      `record_captured`/`record_failed`/`record_zero_rows` call.
    - **4. [DECISION] P2.** If todo 1 confirms stale legacy rows, rule on remediation — accepted historical artifact vs
      targeted manifest correction.
    - **5. [DATA] P3.** Append F10 to the reconciliation register per the audit's own maintenance-contract note.
  - [`plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md`](/plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md)
    (4 open)
    - **[VERIFY] P2.** Confirm the exact `completeness_pct` before/after impact of adding an exclusion guard vs adding
      the 7 keys without one — answers whether Path A is safe directly.
    - **[CODE] P2.** Gated on the verify above — execute Path A: add the defi-scoped exclusion guard + the 7
      `swaps_ohlcv_*` keys to `DATA_TYPES_BY_ASSET_GROUP['defi']`.
    - **[CODE] P3.** Alternatively execute Path B (accepted-exception stopgap) if Path A isn't prioritized soon.
    - **[VERIFY] P3.** Reconcile the `swaps_ohlcv_4h` timeframe discrepancy before either path ships.
  - [`plans/active/issues/defi_five_never_captured_venues_fix_2026_07_22.md`](/plans/active/issues/defi_five_never_captured_venues_fix_2026_07_22.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md`](/plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md)
    (3 open)
    - **[SCRIPT] P0.** Both DeFi launchers MISS the SPOT preemption contract (zero
      `lc_write_preemption_signal_file`/`lc_write_launch_params` calls) — must land before any wide SPOT wave.
    - **[DATA] P0.** `available_at` clobbered by wall-clock `now()` — BIG FINDING, breaks batch==live ε=0; needs an
      operator ruling on intended semantics.
    - **[SCRIPT] P1.** Knobs + async fan-out + executor-offload, together — the 3 concurrency knobs are inert alone;
      bundle with `ParallelPerSymbolRunner` fan-out + dedicated ThreadPoolExecutor. CANARY at 2 VMs before any wide
      wave.
  - [`plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md`](/plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`](/plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md)
    (3 open)
    - **[BACKEND] P2.** `RecursiveLoopOrchestrator` exists + is substantially complete in execution-service, but
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY`/`CARRY_BASIS_PERP_INV` need NEW strategy-side decision logic (not plumbing)
      — correctly NOT AO-dispatchable, parked pending an operator design session.
    - **[BACKEND] P2.** Phase 5 — LIQUIDATION_CAPTURE: new on-chain liquidation-cascade feed + `health_factor_trigger`.
    - **[DOCS] P3.** Explicitly document
      `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`/`ARBITRAGE_MEV_JIT_LIQUIDITY`/`ARBITRAGE_MEV_BACKRUN` as OUT of the
      tick-builder-wiring scope (opportunistic/mempool-driven, no catalog-declared universe).
  - [`plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`](/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md)
    — 0 open todos (closed/archived/record-only) — its P0 finding (6 of 9 archetypes checked can't execute a real trade
    in ANY environment) blocks further orphaned-archetype work; read before touching that thread.
  - [`plans/active/issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`](/plans/active/issues/defi_upstream_instruments_catalog_stale_2026_07_15.md)
    (4 open)
    - **[DATA] P1.** Execute the re-collect commands (or launch as a monitored backfill) once scoped; verify
      before/after counts — clears the `DP_RUN_MOSTLY_EMPTY` alert.
    - **[DEPLOY] P1.** Redeploy the DeFi backfill VM tarball/image with `420221b4` so the next re-walk records honest
      `empty_confirmed` instead of recurring `attempted_failed`.
    - **[SCRIPT] P3.** Thread `mode=` into `assert_defi_catalog_fresh(...)` for the 9 handlers that still omit it —
      orthogonal to the pre-genesis classification fix.
    - **[DESIGN] P3.** IS-DeFi-catalogue-completion-signal retry-sweep — re-scoped, valid only for the genuine
      post-genesis catalogue-behind class now.
  - [`plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`](/plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md)
    (5 open)
    - **[CODE] P1.** `EULER_V2-ARBITRUM`'s `defi_venues.py` phase-dict comment is still factually wrong — correct it to
      state the real reason (adapter is Ethereum-only), not a stale no-subgraph-id claim.
    - **[CODE] P2.** Three concrete gaps to actually wire EULER_V2 capture: `mtds_operations` capability mismatch,
      capability-gate entries with zero rows ever captured, and a ~38-day-stalled upstream subgraph to re-verify before
      wiring.
    - **[VERIFY] P3.** Resolve which "Plasma" chain UAC's `FLUID-PLASMA`/`AAVE-PLASMA` placeholders refer to before
      touching those entries.
    - **[CODE] P1.** HYPERLIQUID/ASTER durable fix — declare them in UAC's own `ALL_DEFI_VENUES` +
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (a deployment-api-local stopgap already unblocks the dashboard).
    - **[OPS] P1.** Restart/fix the `uts-prod-data-status-rollup` Cloud Run Job — Cloud Scheduler has been firing into
      `UNAVAILABLE` since at least 2026-07-05.
  - [`plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`](/plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`](/plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`](/plans/active/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`](/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`](/plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`](/plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md)
    (1 open)
    - **[DATA] P2.** `lst_yields` sparse coverage (~15 days) — file the coverage extension with features-onchain/MTDS;
      STAKING_REWARD honestly books zero (visible log) outside that window until then.
  - [`plans/active/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md`](/plans/active/issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md)
    — 0 open todos (closed/archived/record-only) — operator ruling needed (rewrite vs delete vs gate-hardening) before
    this becomes a real todo.
  - [`plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`](/plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`](/plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md)
    — 0 open todos (closed/archived/record-only) — its scope (legacy `dex_pools/`/`lending_indices/` fold + the
    glued-venue flat tree inside `raw_tick_data/`) is tracked as live todos under
    `defi_track01_per_instrument_and_canon_id_2026_07_24.md` below.

- **Cross-AG / infra / process**:
  - [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md)
    (9 open: 3 P1, 3 P2, 3 P3 — P1 listed in full, P2/P3 capped)
    - **[DATA] P1.** Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string to
      `build_canonical_instrument_id(...)`. Do NOT start until the TYPE-token question below is resolved.
    - **[DATA] P1.** Resolve the non-canonical TYPE-token question before retrofitting —
      `VAULT`/`SUPPLY`/`BORROW`/`LENDING_MARKET`/`GOVERNANCE_TOKEN`/`SPOT`/`PERP` aren't real `InstrumentType` enum
      values.
    - **[DATA] P1.** Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters (Kalshi + Polymarket
      store the bare raw provider id).
    - +6 more (P2: VERIFY morpho.py's current code against finding 6, ship each retrofit batch via quickmerge, resolve
      the FI_-vs-FF_ Kraken-Futures collision; P3: cross-reference the TradFi combo-leg fix, refactor `ccxt_adapter.py`,
      upgrade MTDS's already-correct callers) — see file for the rest.
  - [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md)
    (2 open)
    - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols) — code is already correct, only the
      catalog rows predate it; re-run instrument discovery and rewrite in place.
    - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (ASTER/PACIFICA/LIGHTER-ZKSYNC)
      before the illustrative targets become real implementation targets.
  - [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
    (3 open)
    - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
      when an IS adapter's stamped `instrument_type` changes.
    - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers (DERIBIT live-vs-batch,
      HUOBI-SPOT venue-universe gap).
    - **[DECISION] P2.** Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
      findings.
  - [`plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`](/plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md)
    (2 open)
    - **[DATA] P1.** Re-fetch/backfill the ~3,116 undocumented api_football `attempted_failed` rows; investigate the 461
      blank-data_type failures first.
    - **[DATA] P2.** Remove/relabel 2 rows mis-filed in the sports manifest under `source=api_football` (a
      defi/UNISWAP_V3-BASE row + a cefi row) — same wrong-non-blank-value bug class.
  - [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
    (6 open)
    - **1. [DATA] P1.** instruments-service: canonicalise the `instrument_availability` write using the sink PREFIX
      mechanism, not the partition dict (the UTL sink sorts keys alphabetically).
    - **2. [DATA] P1.** market-tick-data-service: rule on + fix the cefi chain tail — W1 emits a bare `underlying=` path
      while W2 emits the canonical v6 tail.
    - **3. [DOCS] P2.** Correct 3 in-repo comments asserting the IS live writer emits the hive layout.
    - **4. [SCRIPT] P2.** Add a Phase-0 `-test-` assertion on the resolved WRITE bucket to
      `data-pipeline-check-mdps`/`-features`.
    - **5. [DOCS] P2.** Add an explicit "never pass `--allow-live-prod-writes`" prohibition to the MTDS check skill doc.
    - **6. [DATA] P3.** Decide whether `market_lifecycle`/`futures_contracts` are in the canonical shard grammar's
      scope.
  - [`plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`](/plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md)
    (4 open)
    - **[SERVICE] P1.** Add a write-time canonical-path guard to the Tardis cefi lane (currently has none) — DEFAULT
      all-class `canonical_path_violations`.
    - **[SERVICE] P1.** Fix `tardis_shared.py:671` to escape `/` in the stem; migrate the 48+ KRAKEN-SPOT corrupt
      objects.
    - **[SERVICE] P1.** Turn `validate=True` on the two `tardis_cefi_shards.py` write sites and make violations FATAL,
      not advisory.
    - **[DATA] P1.** Migrate/restate the 1,697 historical non-canonical live colon_wire cefi objects as part of the
      surface-A re-run.
  - [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
    (8 open — cefi/cross-AG-primary, defi has none of the empty-stem class)
    - **2. [DATA] P1.** Corpus-wide count of zero-length-stem candle objects; purge or repair — census done, repair
      pending P7 `--apply`.
    - **3. [DATA] P1.** Canonicalise TradFi candle leaf ids (`E1AF0_*_migrated_*` → `VENUE:TYPE:SYMBOL`) — 93% of the
      TradFi corpus is quarantined, unresolved as of P8; needs a real leaf-id resolution pass or an operator won't-fix
      ruling.
    - **7. [DATA] P0.** Root-cause the candle object↔manifest disconnect — confirmed cross-AG (defi 0 rows despite 1.1M
      live candle objects; cefi/tradfi/prediction all similarly degenerate); skip-if-fresh is moot fleet-wide until
      fixed.
    - **9. [DATA] P1.** Split-brain candle layout — quantify the corpus-wide split and fold into the A/B/C migration;
      pending P5 executor.
    - **13. [DATA] P3.** `ProvisionalTargetIndex` keys lack a bucket component — the split-brain COUNT can be inflated
      by cross-AG path coincidences.
    - **15. [DOC] P3.** Update `build_canonical_candle_path()`'s docstring example to match the 2026-07-21 correction.
    - **16. [SCRIPT] P3.** Investigate a DERIBIT trades:24h force-leg `off_template` classification mismatch —
      non-blocking.
    - **19. [SCRIPT] P2.** Fix `_copy_verify_delete()`'s retry-idempotency gap — a verification-FAILED destination is
      never re-copied on a subsequent run; source data was never at risk.
  - [`plans/active/issues/canonical_closeout_open_questions_2026_07_18.md`](/plans/active/issues/canonical_closeout_open_questions_2026_07_18.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](/plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)
    (2 open)
    - **2. [DATA] P0.** Make a run whose every write failed EXIT NON-ZERO (fix the "N success / 0 failed" summary to
      count written, not processed).
    - **3. [DATA] P1.** Sweep the other candle data_types (trades, book_snapshot_5, liquidations, options_chain,
      futures_chain, the DeFi set) for the same contract-drift class before the backfill.
  - [`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`](/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md)
    (8 open)
    - **1. [SCRIPT] P2.** S1-a — `launch-prediction-features-vm.sh` is BROKEN; superseded by
      `launch-features-vm.sh --feature-family cross_instrument`. DELETE + repoint registry (pending operator).
    - **2. [SCRIPT] P2.** S1-b — `launch-mdps-features-live.sh` is non-runnable but still registered (5 rows) — DELETE
      or finish the dispatcher branch (pending operator).
    - **3. [SCRIPT] P1.** S1-c — `mdps-sports-<year>-<ts>` emitted but registered in NEITHER registry → invisible to the
      zombie watchdog; add it or drop sports from the sharded launcher default set.
    - **4. [SCRIPT] P3.** S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (unreachable dead body).
    - **5. [SCRIPT] P3.** S2-b — delete 8 stale `features_*_service`/`ml_*_service` SERVICE_TARBALLS keys.
    - **6. [SCRIPT] P3.** S3-a — delete MDPS one-offs past their `Delete-when` after verifying each condition.
    - **7. [SCRIPT] P3.** S3-c — repoint `smoke_matrix.py` SSOT citations to `launch-features-vm.sh` + the codex
      smoke-matrix doc.
    - **8. [SCRIPT] P3.** S3-b — sports dual entrypoint needs an operator/design adjudication; do NOT silently delete
      (breaks live sports backfills).
  - [`plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
    (1 open)
    - **3. [DATA] P1.** Assess blast radius on existing candle data — any past MDPS run with `max_workers>1` over a
      heterogeneous file list may carry wrong leading-bin seeds.
  - [`plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`](/plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`](/plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md)
    (4 open)
    - **[DECISION] P1.** Decide the fix mechanism for 338 empty-string-fallback call sites — bulk-annotate safe ones,
      rewrite unsafe ones fail-fast, or add a baseline-ratchet file.
    - **[SCRIPT] P1.** Once decided, execute it and get `quality-gates.sh` exiting 0 on MTDS's `live-defi-rollout` tip.
    - **[SCRIPT] P3.** Ratchet 5 baselines DOWN (`--update-baseline` per repo) — pure hygiene, unbanked headroom is how
      `agent-orchestrator` reached 26.
    - **[SCRIPT] P2.** Stamp a `commit:` anchor into the `agent-orchestrator` baseline row so an over-baseline failure
      can git-diff against a known-good point instead of a positional tail-slice guess.
  - [`plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`](/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md)
    (3 open)
    - **[VERIFY] P1.** FLUID `lending_indices` silently returns 0 rows for ~18 months (2024-06-01→2025-11-26) — the
      resolver contract wasn't deployed until 2025-11-26; needs an alternate historical read path.
    - **[VERIFY] P1.** Root-cause the 273 mistagged DERIBIT/COMBO rows — not attempted this session.
    - **[CODE] P2.** Update both drilldown mockups — not attempted this session; ~12 remaining P2/P3 items
      low-value/deferred.
  - [`plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md`](/plans/active/issues/mtds_perp_funding_backfill_hang_2026_07_14.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md`](/plans/active/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`](/plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md)
    (5 open)
    - **[INFRA] P2.** HYPERLIQUID trades backfill re-run — parser fix is code-correct but no re-run has happened since;
      ~12,179 stale rows persist. Force/overwrite, monitored (not fire-and-forget).
    - **[FIX] P3.** HYPERLIQUID k-prefix coin case-sensitivity — `kPEPE`/`kBONK`/`kSHIB` requests drop real fills due to
      a case mismatch between catalogue and fill-matching.
    - **[CODE] P3.** Delete the retired perp_funding DeFi-routing residue (stale HL/ASTER/LIGHTER entries) so a re-run
      can never re-stamp DeFi HL/ASTER perp_funding.
    - **[INFRA] P3.** BLOCKED-OPERATOR-DECISION — reconcile 916 HL + 642 ASTER `defi/perp_funding` legacy rows
      (redundant with cefi `derivative_ticker.funding_rate`); delete-vs-re-home decision needed.
    - **[FIX] P3.** BLOCKED-OPERATOR-DECISION — extending the live-probe mechanism to cefi CEX venues contradicts a
      deliberate RULE 11 invariant; needs an explicit operator ruling.
  - [`plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
    (1 open)
    - **[INFRA] P1.** Decide + implement a default-to-yesterday date bridge for MTDS's batch CLI — needs an owner
      decision between a local fix (MTDS) and a shared UTL fix before coding.
  - [`plans/active/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/active/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    (2 open — sports/prediction-primary, tracked here for cross-AG catalogue overlap)
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run promotes successfully and
      `prod/catalog.parquet` row count is `>= 27,216`.
    - **[INFRA] P3.** Grant the catalogue-regen SA `storage.objects.create` on the events-sink bucket so structured
      events stop silently 403ing.
  - [`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`](/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`](/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md`](/plans/active/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`](/plans/active/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md)
    (5 open)
    - **1. [REVIEW] P1.** Confirm whether MTDS call-site updates for the UAC colon-strictness change were intended to
      land in the same wave — cross-link if already in flight.
    - **2. [DATA] P1.** Fix `canonical_write.py::write_defi_rows` (the `WETH:USDC` POOL case) — resolve the symbol
      before calling `build_instrument_id`, or route through UAC quarantine.
    - **3. [DATA] P1.** Fix `tardis_shared.py::derive_row_instrument_id`'s disabled-by-default fallback (the
      `ADAF0:USTF0` case) the same way.
    - **4. [REVIEW] P2.** Re-check `test_slash_id_never_forges_a_path_segment` — confirm whether it's the same fix as
      todo 2 or a separate defi-oracle-price naming gap.
    - **5. [REVIEW] P2.** Once 2-4 ship, re-run MTDS's full `quality-gates.sh` to confirm no other UAC-contract-change
      fallout.
  - [`plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`](/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md)
    (4 open)
    - **[CODE] P2.** `_L5_VENUES` cefi part RESOLVED-BY-DELETION; still open — audit
      `_SOURCE_COVERAGE_START`/`_PROTOCOL_TO_DATA_TYPE` (onchain) for the same read-from-UAC fix.
    - **[CODE] P2.** Add missing `book_snapshot`/`market_metadata`/`fills` declarations to
      `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]`; retire deployment-api's parallel registry.
    - **[SCRIPT] P3.** Delete confirmed-dead code (`MVP_VENUE_DATA_TYPES`, DeFi's emptied `DEFI_VENUE_AXIS_OVERRIDES`,
      Prediction's inert matrix row) — not touched this pass, `defi_venues.py` was live-being-edited concurrently.
    - **[DESIGN] P2.** 31 DeFi (venue, data_type) pairs declare a genesis start-date with zero real captured rows (100%
      `empty_confirmed`) — needs an operator/data-owner decision per (protocol, data_type).
  - [`plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md`](/plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md`](/plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md)
    (3 open)
    - **6. [DATA] P1.** PROVE the fixed delta_one + volatility writers green on one real day, then migrate historical
      objects up into the `by_date/day=` tree.
    - **7. [DATA] P1.** Re-sync the availability manifest + data-status render for the migrated features cells so all
      four canonical surfaces agree.
    - **8. [REVIEW] P1.** On writer ship, record the cutover date in the canonical-cutover-register + flip the
      non-canonical-path-inventory row #17 to EXECUTED.
  - [`plans/active/issues/migration_orphan_sweep_performance_decay_2026_07_22.md`](/plans/active/issues/migration_orphan_sweep_performance_decay_2026_07_22.md)
    (1 open)
    - **7. [CODE] P3.** Genuinely stream `_load_manifested_cells()`'s parquet read instead of relying on a bigger
      machine type — today's fix works but doesn't scale as cefi's index keeps growing.

- **Cross-AG-touching cefi plans referenced here for their defi overlap** (primary tracking:
  [`plans/active/cefi_consolidated_closeout_2026_07_18.md`](/plans/active/cefi_consolidated_closeout_2026_07_18.md)):
  - [`plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md`](/plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)
    (2 open) — [ ] [SCRIPT] P2. Spot-check 3 random days of DERIBIT options greeks/IVs. [ ] [SCRIPT] P2. Spot-check 1
    day of BINANCE-FUTURES funding + open_interest.
  - [`plans/active/cefi_ml_directional_continuous_live_2026_06_20.md`](/plans/active/cefi_ml_directional_continuous_live_2026_06_20.md)
    (3 open) — [ ] [AGENT] P0. Continuous ML signal live ≥7 days across OKX+Binance+Bybit — GATED on
    wallet-key/kill-switch operator hard-stops. [ ] [VERIFY] P0. 2-year config-grid backtest fidelity run — architecture
    verified, grid run pending operator VM scheduling. [ ] [RESEARCH] P2. Not currently scheduled (2026-07-24: reworded
    off the bare DEFERRED-then-dash marker, which is reserved for whole-plan migrations per the plan-discipline gate —
    this is a single low-priority research idea, not a plan-level deferral, and has no successor plan to banner): volume
    as a first-class feature for the cs/ext ML models.
  - [`plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`](/plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md)
    (22 open — a genuinely large tradfi/cefi crypto-venue-equity-perp build; top items only) — [ ] [SCRIPT] P0.
    Propagation ops (B1/B3/B4) — run the IS→catalogue→enumerator→MTDS chain on real infra to completion; IN PROGRESS. [
    ] [UAC] P0. Map index perps (SPXUSDT/NAS100/SPYUSDT/XAUUSDT) to their CME/Databento canonical + contract multiplier.
    [ ] [DESIGN] P0. execution-service — IBKR equities execution adapter is the gating unlock for the winning
    single-stock basis archetype. [ ] [DESIGN] P0. strategy-service+UAC — replace the fixed net-profitable-12 with a
    broad dynamic live-net-carry universe. — see file for the remaining 18 (mostly P1/P2 strategy-design + data-sourcing
    items).

- **Newly discovered (completeness-check addition, 2026-07-24)**:
  - [`plans/active/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`](/plans/active/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md)
    (`asset_group: [defi, cefi]`, `status: open` — the DRIFT + all-other-Solana-perp-DEX kill ruling's DATA/STATE half;
    not previously named in this section) (1 open)
    - **[DATA] P2.** Once the sibling's UAC venue removal + IS adapter removal are fully on `origin`, re-run
      `build_instrument_catalogue.py --asset-group defi` (and `cefi`) as a confirmation pass — pre-conditions now
      satisfied, `instruments-service@ee19f6f3` already hardens the catalogue script to structurally exclude the killed
      venues.
