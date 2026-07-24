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
last_updated: "2026-07-24"
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
      gate). The "1M" framing is the old safety-cap slug — the real target is 63.9M. **Re-verify
      `spot_pair`/`spot_asset` counts against the CURRENT catalogue before applying** — the 63.9M figure (incl.
      `spot_pair` 143K) was measured 2026-07-10 against a catalogue snapshot that predates the 2026-07-16 SPOT_ASSET
      population backfill + the 2026-07-21 reference-only reclassification; live re-measurement 2026-07-24 shows
      catalogue SPOT_ASSET=1,390 (well-populated, 17 venues, 0 DRIFT) and catalogue SPOT_PAIR=56
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
- [ ] [INFRA] P2. **NEW 2026-07-24 — fix the `canonical-migration` `VM_TASK` mtds-hardcoded `cd` bug** found above
      (`setup-data-pipeline-vm.sh:1187`) — mirror the `VM_SERVICE`-keyed `cd "$WORKSPACE/instruments"` pattern other
      branches already use (e.g. `:1224`). (repo: deployment-service)
  - [x] `spot_asset`/`spot_pair` reconciliation investigated + resolved via live re-measurement (see the P0 item's
        footnote above) — both were stale/non-issues, not a coding task.
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
- [x] ✅ [DATA] P2. **Verified 2026-07-24 (GCS object-existence probe, 160 venue×data_type×sample-date combos + VM
      run.log/deployment-registry evidence — manifest download infeasible this session, ~100KB/s sandbox network).** OOM
      crash-loop did NOT recur post-fix — every VM that ran after `a5b07ff7e` ran clean (no `Killed`/`rc=137`) until
      independently TERMINATED by an explicit `v1.compute.instances.delete` (confirmed via audit log; not OOM, not SPOT
      preemption). Mixed result: `dex_pool_state` has real substantive coverage for all 4 protocols 2023→2026-03
      (UNISWAP_V4 correctly absent pre-2025-01-31 launch) but a real, patchy gap ~2026-03→today (the healthy
      `mtds-dex-pools-backfill` run was killed 2026-07-18 mid-backfill, never relaunched until this session).
      `dex_pool_swaps`: UNISWAP_V2/V4 partial-but-improving (currently-running sharded fleet
      `mtds-dex-swaps-backfill-{1,2,3}` actively filling recent dates); **TRADER_JOE_V2 = 0% ever captured** (persistent
      TheGraph subgraph schema-cascade failure, a code bug, NOT OOM-related); **VELODROME_V2 = near-zero (2/20 sampled
      dates)**. Found + fixed a real launcher bug along the way (`--protocols` comma-lists broke gcloud `--metadata`
      parsing — deployment-service commit, both dex-pools + dex-swaps launchers) and relaunched a scoped
      `mtds-dex-pools-backfill` (4 protocols, 2023-01-01→today) to close the pool_state gap — T+10min health-verified
      RUNNING + writing real rows. Full evidence + verdict table + 5 follow-up todos (trader_joe_v2 code fix,
      velodrome/trader_joe swaps historical backfill, lending-indices launcher preemptive fix, re-check, manifest
      cross-check): `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`. (repos: market-tick-data-service,
      deployment-service)
- [x] ✅ [BACKEND] P3. **Post-phase codex audit for the dex_pools/dex_swaps protocol dispatch list** — check whether
      `/codex/02-data/defi-canonical-naming-ssot.md` documents the MTDS `_DEFAULT_PROTOCOLS`/fallbacks dispatch set; it
      currently does not (only data_type/venue/bucket path-naming rules) — add it if the audit confirms no stale list
      exists elsewhere. (repos: unified-trading-pm) — audit confirmed `defi-canonical-naming-ssot.md` genuinely lacks
      it, but a STALE, incomplete version already existed in `/codex/02-data/defi-data-types-catalog.md` §1/§2
      ("Sources" fields, missing the 2026-07-14 zero-capture-fix protocols + the Solana route) — corrected in place
      rather than duplicated, verified against `market-tick-data-service` code (`dex_pools_handler._DEFAULT_PROTOCOLS`
      17 protocols, `_dex_swaps_queries._DEFAULT_PROTOCOLS` 12 protocols) 2026-07-24.

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
      slow I/O). ~~The 3 `service_config.py` knobs are a trivial, un-risky first step~~ — **CORRECTED 2026-07-24
      (sub-agent investigation): WRONG per this item's own cited source** —
      `plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md:617` states the knobs (none of the 3 exist
      yet — confirmed via grep) are "inert alone — 0% gain, 3 unread fields — ship knobs+fanout+executors as ONE commit
      or not at all." `plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` (open, locked_by:
      live-defi-rollout) already carries the correctly-bundled todo; nothing shipped standalone. **Separately**: the
      2-VM TheGraph canary is operator-owned ("ship code + I run the canary") — do not launch VMs for it. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Confirm the launcher + parallelization plan for the DeFi-MVP full-history MDPS candle backfill**
      (gate-audit §6, 2026-07-24 — gated on `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8).
      Determine which launcher runs it (single-VM vs. cross-VM sharded) and whether `max_workers` lets concurrent writes
      overlap GCS (~8x ETA impact suspected, unconfirmed). Definition of done: name the launcher + cite a measured
      write-concurrency figure. (repos: market-data-processing-service, deployment-service)
- [ ] [DATA] P1. **Run `/data-pipeline-check-is` and `/data-pipeline-check-mtds` 3x each across the defi backfill**
      (gate-audit §11: pre-backfill baseline, mid-backfill spot-check, post-backfill final gate per skill — 0 dated runs
      of either on record for defi today). Cite each run's report path + date. (repos: instruments-service,
      market-tick-data-service)

## MVP universe — proven-wired vs. merely-declared (gate-audit §14, 2026-07-24: no such section existed; Track 5 above is the closest source)

**Status: unresolved, mostly an open question.** Per Track 5's unpark note, defi's MVP backfill has not yet written
canonical rows against the per-instrument shard key (R3 is `RUNNING, partial`) — so **no DeFi MVP cell can yet be called
PROVEN wired backfill=paper=live**; every cell in scope today is only DECLARED in-scope via the catalogue/ registries +
the Track 7 culled-venue ruling.

- [ ] [DATA] P2. **Determine the real DeFi MVP universe once Track 5's backfill produces its first canonical rows** —
      enumerate which (venue, instrument_type, data_type) cells are PROVEN wired backfill=paper=live vs. still only
      declared in-scope. Definition of done: a verdict table (here or a linked issue doc), re-derived from the live
      catalogue/manifest at that time. (repos: instruments-service, market-tick-data-service)

## Track 6 — RENDER: data-status surface #4 + RESTORE the enumeration view · P1

- **Sources**: `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (HYPERLIQUID/ASTER 3.77M/1.07M invisible),
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`, the removed-feature archaeology
  (`deployment-api@47a7f67`/`953fa81`/`512180be` gated/suppressed/canonicalised-away the distinct-values view
  2026-07-16→18).
- **Close-out criterion**: data-status renders the canonical DeFi ids; the raw distinct-values audit view is live again;
  **AND** a fresh re-run of that census (`GET /api/data-status/distinct-values/defi`) returns **zero**
  `is_canonical=false` entries — not just the view being live (gate-audit §2, 2026-07-24; the Wave-D worklist it
  surfaced 2026-07-18 must be driven to 0 first).

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
      against it). **ADDITIONAL GATE (2026-07-23) — RESOLVED 2026-07-24 (gate-audit §13 fixed a broken citation +
      self-contradiction here).** `uts-prod-mtds-collect-solana-defi-cron` needed the Solana AMM symbol-collision fix
      before resuming — previously mis-cited as "the `[CODE] P1` todo above" (that todo lived in Track 1, forked out
      2026-07-24 to `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, so the pointer went stale on the fork).
      **The fix has since SHIPPED** (`market-tick-data-service@0d83a8a9`, ancestor of `origin/live-defi-rollout`; see
      "Open follow-ups" below) — so this specific pre-resume condition is now satisfied; the cron still waits on the
      Track-1/2 + migration-VM gates above like the rest. A 2026-07-23 GCS sample (every 3 days, both venues) had found
      ZERO `dex_pool_state` objects for ORCA/RAYDIUM, confirming the bug hadn't yet corrupted data before the fix
      landed. (repos: deployment-service, market-tick-data-service)
- [x] ✅ [BACKEND] P2. **Stale duplicate — RESOLVED elsewhere 2026-07-24, synced here.** Already answered in
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s "Second Solana writer" item:
      `_dex_pools_subgraph.py::_collect_solana_dex` keys its manifest row AND leaf filename off the pool **ADDRESS**,
      never a derived symbol — structurally immune to the token-pair collision this item worried about (addresses are
      inherently unique). No fix/retire decision needed on collision grounds; only gap is optional readability. (repo:
      market-tick-data-service)

## Open follow-ups (carried forward from the pre-2026-07-24 Progress Log's "Deferred work after 2026-07-22/23" tables)

> Full narrative + evidence for every row below lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md)
> ("Deferred work after 2026-07-22" / "…-07-23" sections) — condensed to actionable todos here so nothing genuinely open
> got silently archived. Items already marked DONE/SHIPPED/RESOLVED in that history are NOT repeated here.

- [ ] [SCRIPT] P3. **Root-cause `quickmerge.sh` silently resetting an unpushed commit** (observed 2026-07-22, 2
      hypotheses ruled out, cause not confirmed, non-reproducible on retry). Needs a `bash -x`/`set -x` trace the next
      time it recurs. (repo: unified-trading-pm)
- [ ] [BACKEND] P2. **Audit defi adapters for dead code, runtime-fallback masking, and duplicate implementations**
      (gate-audit §1, 2026-07-24) across instruments-service `.../adapters/defi/`, MTDS
      `market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/`, and execution-service
      `adapters/defi_adapter.py`, per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Definition of
      done: a written finding per module (kept/fixed/removed + reason). (repos: instruments-service,
      market-tick-data-service, execution-service)

> **🟢 IN-FLIGHT (2026-07-24, ~18:22 UTC onward) — a fresh dry-run report for this exact script is ALREADY RUNNING on VM
> `canonical-migration-defi-marker-cleanup-20260724-182226` (SPOT, `asia-northeast1-c`, launched via the new
> `defi-marker-cleanup` category on `launch-canonical-migration-vm.sh`, `deployment-service@b4d2305`). Full
> 2020-01-01..2026-07-24 corpus (356,391 markers); log streams to
> `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-marker-cleanup-20260724-182226/run.log`;
> resume-log checkpoints every 2 min to
> `gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/resume-seed/delete_migrated_defi_markers_2026_07_23.resume.jsonl`
> (safe to resume from if the VM is preempted). Steady-state ~5-6 markers/sec once past the cheap early-corpus portion →
> ETA ~15-16h from launch. **Do NOT launch another dry-run (local or VM) for this script while this is in flight** —
> check the VM/GCS log above for current status first. `--apply` stays human-executed-only regardless (see below) — this
> banner only concerns not duplicating the DRY-RUN. Remove this banner once the report is delivered to the operator and
> either superseded by a fresh run or acted on.**

- [ ] [OPERATOR] P1. **Run `delete_migrated_defi_markers_2026_07_23.py --apply`** — CODE-SHIP HALF DONE
      (`market-tick-data-service@a65117eb`, confirmed on `origin/live-defi-rollout` — the blocking flaky-test issue was
      worked around via the serial-pytest mitigation, not fixed at root; see
      `issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`, reopened 2026-07-24). Exact
      operator command:
      `cd market-tick-data-service && .venv/bin/python     scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py --apply`.
      **Still gated on 712 below** — re-verify 0 glued ids before running; the fix that stops NEW glued rows shipped
      (`f2e3ad41`) but the 12 pre-existing liquidations rows found 2026-07-23 have not yet been re-verified clean.
      Prod-bucket delete, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — an agent must
      never run `--apply` itself.
- [ ] [DATA] P2. **Remediate FLAGGED `_migrated_*` markers, not just delete the SAFE subset — operator ruling
      2026-07-24: cleanup should resolve everything, not defer FLAGGED cases indefinitely.** The dry-run above only
      deletes SAFE-classified markers; a FLAGGED marker is left untouched forever unless someone re-runs the actual
      split migration for that cell. Once the in-flight dry-run (banner above) completes and gives real counts, root-
      cause per disposition type before just re-running blind: `FLAGGED_NO_SIBLINGS_NO_BACKUP` is most likely a cell
      where `migrate_defi_batch_to_per_instrument.py` was interrupted before ever writing output (safe to just re-run
      for that cell); `FLAGGED_ROWCOUNT_SHORTFALL` means siblings exist but rows are missing — could be a genuine bug in
      the original migration silently dropping rows, so investigate before blindly re-running. Then re-run the split
      migration (`defi-per-instrument`/`defi-pi-range` category on `launch-canonical-migration-vm.sh`) targeted at the
      confirmed cells, and only after that re-run this dry-run once more to confirm 0 FLAGGED remain before any
      `--apply`.
- [ ] [DATA] P2. **21 glued-id rows found in the 2026-07-23 manifest rebuild — writer fix SHIPPED, re-verify pending.**
      9 ORCA/SOLANA `dex_pool_state` cells (2025-12-23..12-31) still need the higher-timeout/parallel-write migration
      retry (tracked in `issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md`'s addendum — root-caused
      as a genuine large fan-out, not a bug; safe to retry, source bundles left intact). The 12 `liquidations` bundles
      question is ANSWERED: root-caused + fixed 2026-07-24 (`market-tick-data-service@f2e3ad41` — a daily cron was
      writing timestamp-glued empty markers across 6 handlers; `70b9a81a` promoted the verify tool to
      `scripts/one_offs/verify_defi_glued_ids_2026_07_24.py`). **Remaining**: run the 9-cell ORCA retry + re-run the
      verify script for a fresh 0-glued-ids reading before todo 708's `--apply` proceeds.
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
- [ ] [BACKEND] P2. **Async fan-out + executor-offload for the DeFi write path — duplicate of the Track 5 item above**
      (same 4 upload sites, same design sketch, same 2026-07-24 correction re: the knobs NOT being a safe standalone
      step — see that item for full evidence). (repo: market-tick-data-service)
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
- [x] ✅ [BACKEND] P2. **`is_defi_force_include_pool` wiring** — `instruments-service@4e97a82e`. Cherry-picked ONLY the
      `filter_defi_instruments_by_relevance`/`_add_force_include`/orchestrator-namespace-import hunks out of `stash@{0}`
      (re-diff-confirmed against current HEAD, not just the 2026-07-22 claim): wired
      `is_defi_force_include_pool`/`DEFI_FORCE_INCLUDE_POOLS` into the IS DEX relevance filter (pool_address carve-out,
      `instruments_service/engine/orchestrator/defi.py`) and the catalogue `_add_force_include` column
      (`scripts/build_instrument_catalogue.py`), plus the orchestrator-package export
      (`instruments_service/engine/orchestrator/__init__.py`) so `_orch.is_defi_force_include_pool` resolves at runtime
      — so the 32 legacy-only high-TVL Raydium pools (incl. XMR/USDC ~$47M, BNB/USDC ~$18M) survive both the relevance
      filter and the catalogue force_include stamp. The REST of `stash@{0}` (Chainlink oracle + Solana-DEX
      venue/factory-adapter WIP, goldens, per-AG target counts) diff-confirmed fully superseded/redundant at HEAD —
      `git apply --check` fails on every remaining hunk, and HEAD's golden `defi.json` tuple_count (234, captured
      2026-07-22) and `_PER_AG_TARGET_COUNTS["DEFI"]` (96) are already strictly ahead of the stash's stale 227/93 — so
      only the 3 force-include hunks moved, nothing else cherry-picked. Added unit test coverage: 3 new tests in
      `tests/unit/test_new_orchestrator.py` (force-include keeps a high-TVL minor-asset pool, case- insensitive match,
      non-allowlisted minor-asset pool still rejected) + 1 new test in
      `tests/unit/scripts/test_build_instrument_catalogue.py` (`_add_force_include` flags a force-include pool by
      address, control pool stays False). `quality-gates.sh` green (sentinel `.qg_last_passed_sha` == HEAD `31d662e1`
      pre-ship), shipped via `quickmerge.sh --agent --files`. Stash cleanup: `stash@{0}` is now fully
      consumed/superseded (post-ship re-diff also fails to apply on every hunk) but `git stash drop` is BLOCKED by the
      orchestrator's destructive-command guardrail for autonomous workers — needs an operator/interactive-session
      `git stash drop stash@{0}` in `instruments-service` to actually clear it. `stash@{1}`
      (`stale-e527a0d7-dockerfile-wip-do-not-ship`) is unrelated/out-of-scope and was left untouched.
- [x] ✅ [DATA] P3. **Orphan-sweep VM monitoring** — `orphan-sweep-defi-20260723-043605` (6th attempt) reached
      ACCEPTANCE 2026-07-23 21:04:37 UTC: `orphan_class_E=15,865,384, unknown_prefixes=8` (full 24,890,959-object walk,
      16h25m). The 8 unknown-prefix objects were fully triaged (test-artifact leak, negligible scale, fixed with a
      general safety net) and the backfill is now in progress — see
      `plans/active/issues/estate_orphan_assessment_2026_07_21.md` todo 3c and
      `plans/active/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md` for full detail (the latter also
      documents a related cefi manifest row_count-inflation finding from the same defect class).
- [x] ✅ [DATA] P1. **Fake-history relabel-forward migration script** — checkbox was STALE, work already shipped +
      verified complete. `market-tick-data-service/scripts/relabel_solana_dex_pools_fake_history.py`
      (`market-tick-data-service@67524cbb`, 429-crash fix `@b48a0a4d`, sharding fix `@b9a8b76e`) relabels each of the
      241,281 legacy `data_type=dex_pools` rows (17 days x 2 venues: ORCA + RAYDIUM, 2025-01-01..17) forward to its TRUE
      date (from the row's own `timestamp`, not `available_at`) under canonical `data_type=dex_pool_state` +
      `pipeline_mode=live_onchain_subgraph`, `record_captured`s only the new path, and leaves the old object
      un-recorded + logged to `_index/audit/dex_pools_fake_history_pending_delete.parquet` for human delete review.
      **Full-scale run VERIFIED COMPLETE 2026-07-24 ~12:09 UTC** per
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 3 (all 4 ON_DEMAND VMs exited
      rc=0, sum of objects-processed = 241,281 exactly matching the measured population) — **independently re-confirmed
      2026-07-24** via a fresh `gcloud storage ls` count against the live `-prd-` bucket: `day=2026-05-04` = 14,104
      ORCA + 119 RAYDIUM, `day=2026-05-05` = 14,099 ORCA + 113 RAYDIUM, sum = 28,435, exactly matching the issue doc's
      cited final count. Pending-delete audit parquet confirmed present in GCS. No new script needed — this todo and the
      mirrored verification todo in `defi_track01_per_instrument_and_canon_id_2026_07_24.md` are both being flipped in
      this pass.
- [x] ✅ [DATA] P2. **Get TRUE final fake-history scope** — DONE 2026-07-23 per the issue doc todo 2, superseded by a
      faster independent targeted walk (not the `--source final` path) — proved 17 days x 2 venues (ORCA, RAYDIUM),
      2025-01-01..17, no gaps, nothing beyond this window. See
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` "Scope" section.
- [x] ✅ [DATA] P2. **cefi/prediction timestamp-provenance audit — DONE 2026-07-24.** Sampled prediction's core adapters
      (`kalshi_adapter.py`/`polymarket_adapter.py` — already correct, `available_at = max(tick_ts, market_created_at)`)
      and cefi's primary path (`ccxt_adapter.py` — already correct, derives from `compute_bar_close_boundary`) plus 3
      smaller cefi batch handlers for the exact DeFi-fix defect shape. Found 2 real gaps
      (`deribit_volatility_index_handler.py`, `book_microstructure_handler.py` — wall-clock `available_at` despite an
      already-computed deterministic timestamp in the same function) + 1 weaker dead-code candidate
      (`deribit_options_chain_handler.py`). Filed
      [`issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`](/plans/active/issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md)
      and routed the code-fix work into `cefi_consolidated_closeout_2026_07_18.md` Track 6 (owning plan — out of scope
      for this defi-plan audit todo). No code changed by this touch.
- [x] ✅ [BACKEND] P2. **Solana AMM symbol-collision code fix — SHIPPED 2026-07-24 (checkbox was stale — this todo's
      text describing the fix as "unwritten" was overtaken by events, never flipped).**
      `market-tick-data-service@0d83a8a9` wires the fee/tick-spacing discriminator into `solana_defi_handler.py`,
      confirmed ancestor of `origin/live-defi-rollout`. Full remaining scope (already-shipped fix,
      migration-of-existing-data check DONE clean, manifest-impact doc note, naming-doc update, and the SEPARATE cruder
      `dex_pools_handler.py` writer's own collision exposure) tracked in
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (§ "Per-instrument re-architecture", the Solana
      pool-symbol todo) — not duplicated here.
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

- **2026-07-24 (session 3, `/autonomous`, orchestration pass)** — pulled latest across all repos, re-read this plan +
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md` + `defi_lending_writer_retire_prerequisite_2026_07_20.md` in
  full, triaged all ~50 open todos across the three docs into actionable-now / launchable / genuinely-gated. Flipped 4
  stale checkboxes found DONE-but-never-flipped (verified via `git merge-base`/archived-issue-doc checks, not assumed):
  dex_pools/lending_indices legacy fold, Solana AMM symbol-collision fix (`mtds@0d83a8a9`), delete-marker script ship
  (`mtds@a65117eb`), legacy composite-venue investigation (issue filed). Fanned out 9 parallel background agents on
  independent actionable items; 3 hit transient ECONNRESET/network-stall failures mid-task and were resumed via
  SendMessage (2 of those 3 confirmed shipped: `unified-api-contracts@e893e5c9` EXPECTED_SUBGRAPH_DEINDEXED,
  `instruments-service@4e97a82e` is_defi_force_include_pool wiring). **Big finding**: the long-running defi orphan-sweep
  (`estate_orphan_assessment_2026_07_21.md` todo 3, 6th VM attempt) completed with **15,865,384 orphan_class_E rows** —
  larger than cefi+prediction+sports combined — with a caution flag that some fraction is likely leaked test-artifact
  data (`agent-sample-test-jupiter/` prefix sampled), not genuine production gaps; delegated scoped investigation +
  backfill to a background agent, full detail in that issue doc's 2026-07-24 update. **Session interrupted mid-flight**:
  operator is migrating this session to different infrastructure (bandwidth constraints) while 4-5 of the 9 background
  agents were still actively running (line-445 backfill-VM verification, line-761 cefi/prediction audit, the Solana
  symbol-collision closeout naming-doc/second-writer sub-items, the 9-cell ORCA glued-id retry, and the 15.87M-row
  orphan backfill) — their in-flight edits may or may not land depending on whether those background tasks survive the
  migration. Anyone resuming this plan should first `git fetch` + check each repo's recent log for commits past this
  entry's timestamp before assuming any of those 5 items are still open — they may have completed independently after
  this entry was written. If genuinely still open, re-check `gcloud compute instances list` for any
  `backfill-orphan-e-defi-*` / `canonical-migration-defi-pi-range-*` VMs before re-launching anything (avoid a duplicate
  concurrent run). The prod-bucket `_migrated_*` marker delete (`delete_migrated_defi_markers_2026_07_23.py --apply`,
  line ~708) was handed to the operator directly (human-planning VM) this session — check with them before assuming it's
  still pending.

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
- **2026-07-24** — cefi/prediction `available_at` timestamp-provenance audit (line-761 todo) executed. Checked whether
  prediction/cefi's write paths share DeFi's resolved "stamp a deterministic timestamp then discard it for wall-clock"
  bug class. Prediction (kalshi_adapter.py/polymarket_adapter.py) and cefi's primary path (ccxt_adapter.py) are already
  correct. Found 2 real gaps + 1 weaker candidate in smaller cefi batch handlers (`deribit_volatility_index_handler.py`,
  `book_microstructure_handler.py`, `deribit_options_chain_handler.py`). Filed
  `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`, cross-referenced into
  `cefi_consolidated_closeout_2026_07_18.md` Track 6 as the owning plan for the code fix (out of scope for this
  defi-plan audit todo). No production code touched this session.

## Aggregated source docs

> Moved verbatim to `/plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md` (2026-07-24 line-cap
> trim, 2nd pass — the umbrella:true exemption was removed same-day). Read that doc for the full discoverability index
> of every other defi-relevant plan/issue with its open-todo digest.

**Missing digest entry (gate-audit §12, 2026-07-24)**: `defi_track01_per_instrument_and_canon_id_2026_07_24.md` is
referenced 3x by "tracked under X below" prose in `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` but
never appears there as a linked entry — recorded here pending the fix below.

- **[`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)**
  — 18 open (6 P0, 7 P1, 5 P2); top P0s: legacy `dex_pools/`/`lending_indices/` fold-not-delete, glued-venue flat tree
  in `raw_tick_data/`.
- [ ] [DOC] P1. **Add the digest entry above into `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`** and
      fix its 3 dangling "tracked under X below" references to point at it (bold digest style, task_template.md finding
      H). (repo: unified-trading-pm)
